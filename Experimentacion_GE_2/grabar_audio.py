# -*- coding: utf-8 -*-
# Función: grabar audio en el NAO y detener cuando haya silencio sostenido
#          usando umbral adaptativo. Lee energía de micrófonos vía ALAudioDevice
#          y opcionalmente usa ALSoundDetection como respaldo.

from naoqi import ALProxy
import time
import math

# Sensibilidad por defecto
DEFAULT_PARAMS = dict(
    silence_secs=5.0, # tiempo
    calib_secs=2.0,
    poll=0.05,
    margin_db=1.5,
    gain_factor=1.1,
    min_margin_db=1.0,
    ema_alpha=0.02,
    auto_relax_start=4.0,
    relax_db=1.0,
    debug=True,
    channels=[0,0,1,0],   # mic frontal
    sample_rate=16000,
    use_sound_fallback=True,
    sound_sensitivity=0.5
)

EPS = 1e-12

def _db(x):
    return 10.0 * math.log10(max(float(x), EPS))

def _read_max_energy_via_device(adev):
    emax = 0.0
    for getter in ("getFrontMicEnergy", "getRearMicEnergy",
                   "getLeftMicEnergy", "getRightMicEnergy"):
        try:
            v = float(getattr(adev, getter)())
            if v > emax:
                emax = v
        except:
            pass
    return emax

def _calibrate_noise_floor_via_device(adev, secs=2.0, poll=0.05):
    vals = []
    t0 = time.time()
    while time.time() - t0 < secs:
        vals.append(_read_max_energy_via_device(adev))
        time.sleep(poll)
    if not vals:
        return 1e-6, _db(1e-6)
    vals.sort()
    n = len(vals)
    med = vals[n//2]
    abs_dev = [abs(v - med) for v in vals]
    mad = abs_dev[n//2]
    noise_lin = max(med + 1.5 * mad, 1e-6)
    return noise_lin, _db(noise_lin)

def record_until_silence(ip, port, out_wav, stop_event=None, **params):
    """
    NUEVO:
      - stop_event: threading.Event() opcional.
        Si stop_event.is_set() => detiene grabación inmediatamente.
    Devuelve:
      - first_start_rel: instante relativo (s) del primer inicio de voz o None
    """
    # Mezclar defaults con overrides
    cfg = DEFAULT_PARAMS.copy()
    cfg.update(params)

    audio_rec = ALProxy("ALAudioRecorder", ip, port)
    adev = ALProxy("ALAudioDevice", ip, port)
    memory = ALProxy("ALMemory", ip, port)
    leds = ALProxy("ALLeds", ip, port)

    # Validar canales
    channels = cfg["channels"]
    if not (isinstance(channels, (list, tuple)) and len(channels) == 4):
        raise ValueError("channels debe ser lista/tupla de 4 enteros 0/1")
    channels = [1 if int(x) else 0 for x in channels]

    # Fallback ALSoundDetection
    sound_det = None
    if cfg["use_sound_fallback"]:
        try:
            sound_det = ALProxy("ALSoundDetection", ip, port)
            sound_det.setParameter("Sensitivity", float(cfg["sound_sensitivity"]))
            sound_det.subscribe("vad_helper")
        except Exception as e:
            sound_det = None
            if cfg["debug"]:
                print("[WARN] No se pudo activar ALSoundDetection: {}".format(e))

    # Calibración
    noise_lin, noise_db = _calibrate_noise_floor_via_device(
        adev, secs=cfg["calib_secs"], poll=cfg["poll"]
    )
    margen_db = max(cfg["margin_db"], cfg["min_margin_db"])

    # Iniciar grabación
    audio_rec.startMicrophonesRecording(out_wav, "wav", cfg["sample_rate"], channels)
    if cfg["debug"]:
        print("[INFO] Grabando en: {}".format(out_wav))
        print("[INFO] Ruido (lin): {:.6e} | Ruido (dB): {:.2f} dB".format(noise_lin, noise_db))
        print("[INFO] Umbral inicial: +{:.1f} dB | x{:.2f} (lineal)".format(margen_db, cfg["gain_factor"]))
        try:
            leds.fadeRGB("FaceLeds", "cyan", 0.4)
        except:
            pass

    t_start = time.time()
    last_voice_t = t_start
    last_debug_t = 0.0
    first_voice_detected = False

    # timeline
    first_voice_logged = False
    first_start_rel = None

    try:
        while True:
            # ✅ DETENER MANUAL
            if stop_event is not None and stop_event.is_set():
                if cfg["debug"]:
                    print("[INFO] Detención manual solicitada: deteniendo grabación")
                break

            e_lin = _read_max_energy_via_device(adev)
            e_db  = _db(e_lin)

            thr_db  = noise_db + margen_db
            thr_lin = max(noise_lin * cfg["gain_factor"], 10.0 ** (thr_db / 10.0))

            is_voice = (e_db > thr_db) or (e_lin > thr_lin)

            if not is_voice:
                noise_lin = (1.0 - cfg["ema_alpha"]) * noise_lin + cfg["ema_alpha"] * e_lin
                noise_db  = _db(noise_lin)
            else:
                first_voice_detected = True
                last_voice_t = time.time()

            if cfg["use_sound_fallback"] and sound_det is not None:
                try:
                    ev = memory.getData("ALSoundDetection/SoundDetected")
                    heard = False
                    if isinstance(ev, list) and ev and isinstance(ev[0], list):
                        heard = bool(ev[0][0])
                    elif isinstance(ev, (int, float, bool)):
                        heard = bool(ev)
                    if heard:
                        is_voice = True
                        last_voice_t = time.time()
                        first_voice_detected = True
                except:
                    pass

            # primera transición silencio → voz
            if is_voice and (not first_voice_logged):
                first_voice_logged = True
                first_start_rel = max(0.0, time.time() - t_start)

            if (not first_voice_detected) and ((time.time() - t_start) > cfg["auto_relax_start"]):
                old_margin = margen_db
                margen_db = max(cfg["min_margin_db"], cfg["min_margin_db"]) if cfg["relax_db"] <= 0 else max(cfg["min_margin_db"], margen_db - cfg["relax_db"])
                if cfg["debug"] and margen_db != old_margin:
                    print("[INFO] Sin voz tras {:.1f}s: relajando margen de {:.1f} dB a {:.1f} dB"
                          .format(time.time() - t_start, old_margin, margen_db))

            if cfg["debug"] and (time.time() - last_debug_t) >= 0.2:
                last_debug_t = time.time()
                print("E={:.2e} ({:.2f} dB) | ruido={:.2e} ({:.2f} dB) | thr≈max(x{:.2f}, +{:.1f} dB) | {}"
                      .format(e_lin, e_db, noise_lin, noise_db, cfg["gain_factor"], margen_db,
                              "VOZ" if is_voice else "silencio"))

            # Parada por silencio sostenido largo
            if (time.time() - last_voice_t) >= cfg["silence_secs"]:
                if cfg["debug"]:
                    print("[INFO] Silencio {:.1f}s: deteniendo grabación".format(cfg["silence_secs"]))
                break

            time.sleep(cfg["poll"])

    finally:
        try:
            audio_rec.stopMicrophonesRecording()
        except:
            pass
        if cfg["use_sound_fallback"] and sound_det is not None:
            try:
                sound_det.unsubscribe("vad_helper")
            except:
                pass
        try:
            leds.fadeRGB("FaceLeds", "white", 0.4)
        except:
            pass
        dur = time.time() - t_start
        print("[OK] Archivo guardado. Duración aprox: {:.2f} s".format(dur))
        return first_start_rel
