# -*- coding: utf-8 -*-
from naoqi import ALProxy
import time
import socket
import paramiko
import json
import io  # <- para escribir UTF-8 sin errores
import threading
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from grabar_audio import record_until_silence

FRASE_PAUSA = "Ahora tómate un momento para pensar en el concepto que acabas de aprender"
FRASE_PAUSA_LARGA = "Ahora haremos un breve descanso. Intenta relajar tu cuerpo y tu mente."

# ============== MONOTONIC (antes de usar START_TS) ==============
try:
    from monotonic import monotonic as _mono_now
except Exception:
    _mono_now = time.time

# ================== CONFIG WEBSOCKET (SERVIDOR) ==================
WS_HOST = 'localhost'   
WS_PORT = 9000          
ARM_DELAY_MS = 3000     # margen antes de START

# ================== ESTADO GLOBAL SYNC ==================
ws_clients = []
web_ready = False
t0_ms = None            # epoch ms de inicio compartido
START_TS = None         # ancla monotónica local (para _elapsed)
current_sujeto_id = None  # numero de dni del sujeto

# ================== CONFIG NAO / TCP RESPUESTA ==================
NAO1_IP = "192.168.137.22"
NAO2_IP = "192.168.137.46"
NAO_PORT = 9559                    

RUTA_AUDIO = "/home/nao/respuesta.wav"  
RUTA_LOCAL = "./respuesta.wav"          

HOST_RESP = 'localhost'           # servidor local que procesa respuesta
PORT_SOCKET = 12345               # puerto de ese servidor

# ================== DIRECTORIO DE RESULTADOS ==================
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "resultados")
try:
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
except Exception as e:
    print("[RESULTS_DIR] WARNING al crear carpeta:", e)

def build_csv_filename(sujeto_id):
    """Nombre canonico para el CSV de emociones."""
    return "emociones_sujeto{}.csv".format(sujeto_id)

# ================== CRONÓMETRO / LOG ==================
def _elapsed():
    if START_TS is None:
        return 0.0
    return max(0.0, _mono_now() - START_TS)

def _fmt_mmss(seconds):
    total = int(round(seconds))
    mm = total // 60
    ss = total % 60
    return u"{:02d}:{:02d}".format(mm, ss)

def log_event(logfile, message):
    # asegurar unicode en Py2
    try:
        is_unicode = isinstance(message, unicode)
    except NameError:
        is_unicode = isinstance(message, str)

    if not is_unicode:
        try:
            message = message.decode("utf-8")
        except Exception:
            message = unicode(message, errors="ignore")

    line = u"[{}] {}\n".format(_fmt_mmss(_elapsed()), message)
    try:
        with io.open(logfile, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print("[log_event] WARNING:", e)

# ================== SERVIDOR WS ==================
class SyncServer(WebSocket):
    def handleMessage(self):
        global web_ready, current_sujeto_id
        try:
            msg = json.loads(self.data)
        except Exception:
            msg = {}

        # HELLO handshake
        if msg.get('type') == 'HELLO' and msg.get('role') == 'web':
            print("[WEB] HELLO recibido")
            self.sendMessage(json.dumps({"type": "ACK", "role": "python-server"}))
            if current_sujeto_id:
                self.sendMessage(json.dumps({
                    "type": "META",
                    "sujeto_id": current_sujeto_id,
                    "csv_filename": build_csv_filename(current_sujeto_id)
                }))
            return

        # READY del navegador
        if msg.get('type') == 'READY':
            web_ready = True
            print("[WEB] READY recibido (navegador preparado)")
            return

        # CSV recibido desde el navegador -> guardar en ./resultados
        if msg.get('type') == 'CSV_DATA':
            sujeto_id = current_sujeto_id or msg.get('sujeto_id', 'NA')
            csv_text = msg.get('csv_text', '')
            try:
                if not os.path.isdir(RESULTS_DIR):
                    os.makedirs(RESULTS_DIR)
                csv_filename = build_csv_filename(sujeto_id)
                csv_path = os.path.join(RESULTS_DIR, csv_filename)
                with io.open(csv_path, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                print("[WS] CSV guardado:", csv_path)
                self.sendMessage(json.dumps({
                    "type": "CSV_SAVED",
                    "sujeto_id": sujeto_id,
                    "csv_filename": csv_filename
                }))
            except Exception as e:
                print("[WS] Error guardando CSV:", e)
            return

        print("[WS] Mensaje desconocido:", msg)

    def handleConnected(self):
        print("[WS] Cliente conectado:", self.address)
        ws_clients.append(self)

    def handleClose(self):
        print("[WS] Cliente desconectado:", self.address)
        try:
            ws_clients.remove(self)
        except Exception:
            pass

def ws_broadcast(obj):
    payload = json.dumps(obj)
    for c in list(ws_clients):
        try:
            c.sendMessage(payload)
        except Exception as e:
            print("[WS] Error enviando:", e)

def run_ws_server():
    server = SimpleWebSocketServer(WS_HOST, WS_PORT, SyncServer)
    print("[SYNC] Servidor WS en ws://%s:%d" % (WS_HOST, WS_PORT))
    server.serveforever()

def send_arm_and_start(arm_delay_ms=ARM_DELAY_MS):
    """ARM (t0 futuro) -> START en t0 y alinear START_TS."""
    global t0_ms, START_TS
    now_ms = int(time.time() * 1000)
    t0_ms = now_ms + int(arm_delay_ms)
    t0_hora = time.strftime('%H:%M:%S', time.localtime(t0_ms / 1000.0))

    print("[SYNC] ARM -> t0 =", t0_ms, "(", t0_hora, ")")
    ws_broadcast({"type": "ARM", "t0": t0_ms})

    time.sleep(arm_delay_ms / 1000.0)

    ws_broadcast({"type": "START", "t0": t0_ms})
    print("[SYNC] START enviado en", t0_hora)

    # Alinear cronómetro local: (_mono_now() - START_TS) ≈ (time.time() - t0)
    t0_secs = t0_ms / 1000.0
    START_TS = _mono_now() + (t0_secs - time.time())

def preparar_robot(ip):
    """Desactiva AutonomousLife, despierta y pone de pie."""
    life = ALProxy("ALAutonomousLife", ip, NAO_PORT)
    motion = ALProxy("ALMotion", ip, NAO_PORT)
    animated_speech = ALProxy("ALAnimatedSpeech", ip, NAO_PORT)
    leds = ALProxy("ALLeds", ip, NAO_PORT)
    audio_recorder = ALProxy("ALAudioRecorder", ip, NAO_PORT)

    life.setState("disabled")
    motion.wakeUp()

    return {
        "motion": motion,
        "animated_speech": animated_speech,
        "leds": leds,
        "audio_recorder": audio_recorder,
    }

def hablar_con_gestos(animated_speech, texto):
    animated_speech.setBodyLanguageModeFromStr("random")
    animated_speech.say(texto)
    return texto

def procesar_respuesta(texto):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST_RESP, PORT_SOCKET))
    # asegurar bytes utf-8 para el socket en Py2
    try:
        unicode  # Py2
        is_unicode = isinstance(texto, unicode)
    except NameError:
        is_unicode = isinstance(texto, str)
    if is_unicode:
        data_out = texto.encode("utf-8")
    else:
        data_out = texto
    try:
        try:
            print(texto)
        except Exception:
            print(data_out)
        s.sendall(data_out)
        data = s.recv(4096)
    finally:
        s.close()
    return data

def descargar_audio():
    USERNAME = "nao"
    PASSWORD = "nao"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(NAO1_IP, username=USERNAME, password=PASSWORD)
    sftp = ssh.open_sftp()
    sftp.get(RUTA_AUDIO, RUTA_LOCAL)
    sftp.close()
    ssh.close()

# ===== SOLO medir la grabación humana =====
def respuesta_alumno_humano(robot, contexto, log_timeline_filename=None, etiqueta=u"concepto", definicion_concepto=None):
    """
    Mide SOLO la duración de GRABACIÓN (record_until_silence).
    etiqueta: 'concepto' | 'concepto_repetido' | 'concepto_post_modelo' | 'ejemplo' | 'ejemplo_post_modelo'

    AHORA:
    - Si definicion_concepto no es None, se envía por socket:
        "pregunta|tipo|definicion_concepto"
      (en gemini_server.py se parsea con split('|')).
    """
    if log_timeline_filename:
        print('\n')
        log_event(log_timeline_filename, u"[HUMANO] INICIO grabación ({})".format(etiqueta))

    t0 = _elapsed()
    first_start_human_voice = record_until_silence(ip=NAO1_IP, port=NAO_PORT, out_wav=RUTA_AUDIO)  # bloqueante hasta silencio
    t1 = _elapsed()

    dur = max(0.0, t1 - t0)
    if log_timeline_filename:
        log_event(log_timeline_filename, u"[HUMANO] FIN grabación ({}) — duración: {} ({} s)"
                  .format(etiqueta, _fmt_mmss(dur), int(round(dur))))

        if first_start_human_voice is not None:
            log_event(log_timeline_filename, u"INICIO voz sujeto ({:.3f}s)".format(float(first_start_human_voice)))
        else:
            log_event(log_timeline_filename, u"No respondió")

    descargar_audio()

    # =========================
    # Construir contexto enriquecido
    # =========================
    contexto_socket = contexto
    if definicion_concepto:
        try:
            # contexto viene de actividades.json (str) y definicion_concepto también.
            contexto_socket = "{}|{}".format(contexto, definicion_concepto)
        except Exception:
            # fallback muy defensivo
            try:
                contexto_socket = u"{}|{}".format(
                    contexto.decode("utf-8") if isinstance(contexto, bytes) else contexto,
                    definicion_concepto.decode("utf-8") if isinstance(definicion_concepto, bytes) else definicion_concepto
                )
            except Exception:
                pass

    respuesta = procesar_respuesta(contexto_socket)
    try:
        print(u"Respuesta del modelo: {}".format(respuesta))
    except Exception:
        print("Respuesta del modelo: {}".format(respuesta))
    return respuesta


# ===== Fase de observación =====
def fase_observacion(robot1_proxies, robot2_proxies, texto, log_timeline_filename=None):
    motion1 = robot1_proxies["motion"]
    motion2 = robot2_proxies["motion"]

    motion1.setAngles(["HeadYaw", "HeadPitch"], [-0.6, 0.1], 0.1) # mirar al alumno robot
    motion2.setAngles(["HeadYaw", "HeadPitch"], [0.6, 0.1], 0.1)  # mirar al profesor robot

    if log_timeline_filename:
        log_event(log_timeline_filename, u"=== INICIO Fase de Observación ===")
        log_event(log_timeline_filename, u"[ROBOT PROFESOR] Explicación concepto")
    hablar_con_gestos(robot1_proxies["animated_speech"], "\\vct=95\\\\rspd=90\\" + texto["profesor_explica"])
    time.sleep(2)

    if log_timeline_filename:
        log_event(log_timeline_filename, u"[ROBOT ALUMNO] Respuesta parcialmente correcta")
    hablar_con_gestos(robot2_proxies["animated_speech"], "\\vct=95\\\\rspd=90\\" + texto["alumno_respuesta_parcialmente_incorrecta"])
    time.sleep(2)

    if log_timeline_filename:
        log_event(log_timeline_filename, u"[ROBOT PROFESOR] Aclaración del concepto")
    hablar_con_gestos(robot1_proxies["animated_speech"], "\\vct=95\\\\rspd=90\\" + texto["profesor_corrige"])
    time.sleep(2)

    if log_timeline_filename:
        log_event(log_timeline_filename, u"[ROBOT ALUMNO] Ejemplo correcto")
    hablar_con_gestos(robot2_proxies["animated_speech"], "\\vct=95\\\\rspd=90\\" + texto["alumno_ejemplo_correcto"])
    time.sleep(2)

    if log_timeline_filename:
        log_event(log_timeline_filename, u"[ROBOT PROFESOR] Retroalimentación")
    hablar_con_gestos(robot1_proxies["animated_speech"], "\\vct=95\\\\rspd=90\\" + texto["profesor_valida"])
    time.sleep(1)

def preguntar_y_validar(robot,texto,log_timeline_filename=None,etiqueta=u"concepto",log_line_for_question=None,definicion_concepto=None):
    """
    - 'texto' sigue siendo lo que tienes en actividades.json (ej: '¿Qué es X?|concepto').
    - 'definicion_concepto' es el texto de profesor_corrige que se manda al servidor
      para que Gemini lo use como referencia.
    """
    if log_timeline_filename and log_line_for_question:
        log_event(log_timeline_filename, log_line_for_question)

    text_temp = "\\vct=95\\\\rspd=90\\" + texto.split('|', 1)[0].strip()
    hablar_con_gestos(robot["animated_speech"], text_temp)

    respuesta = respuesta_alumno_humano(
        robot,
        texto,
        log_timeline_filename=log_timeline_filename,
        etiqueta=etiqueta,
        definicion_concepto=definicion_concepto,
    )
    return respuesta

def hacer_pausa(robot_proxies, log_timeline_filename, pausa_larga=False):
    if pausa_larga:
        log_event(log_timeline_filename, u"[PAUSA mitad de conceptos: 4 minutos]")
        hablar_con_gestos(robot_proxies["animated_speech"], FRASE_PAUSA_LARGA)
        time.sleep(240)
    else:
        log_event(log_timeline_filename, u"[PAUSA 15 segundos]")
        hablar_con_gestos(robot_proxies["animated_speech"], FRASE_PAUSA)
        time.sleep(15)



def fase_experimental(robot1_proxies, robot2_proxies, texto, definicion_concepto, log_timeline_filename=None, pausa_larga=False):
    if log_timeline_filename:
        log_event(log_timeline_filename, u"=== INICIO Fase Experimental ===")

    pregunta_concepto = texto["pregunta_concepto"]
    repeticion_pregunta_concepto = texto["repeticion_pregunta_concepto"]
    pedir_ejemplo = texto["pedir_ejemplo"]
    respuesta_modelo = texto["respuesta_modelo"]

    concepto_ok = 0
    ejemplo_ok = 0

    # 1) Concepto
    respuesta = preguntar_y_validar(
        robot1_proxies,
        pregunta_concepto,
        log_timeline_filename=log_timeline_filename,
        etiqueta=u"concepto",
        log_line_for_question=u"[ROBOT PROFESOR] Pregunta concepto",
        definicion_concepto=definicion_concepto,
    )

    if respuesta != "si":
        if log_timeline_filename:
            log_event(log_timeline_filename, u"[RESULTADO] Concepto = Incorrecto")

        # 1b) repetición
        respuesta = preguntar_y_validar(
            robot1_proxies,
            repeticion_pregunta_concepto,
            log_timeline_filename=log_timeline_filename,
            etiqueta=u"concepto",
            log_line_for_question=u"[ROBOT PROFESOR] concepto repetido",
            definicion_concepto=definicion_concepto,
        )

        if respuesta != "si":
            if log_timeline_filename:
                log_event(log_timeline_filename, u"[RESULTADO] Concepto = Incorrecto")

            # 1c) respuesta modelo (concepto)
            if log_timeline_filename:
                log_event(log_timeline_filename, u"[ROBOT ALUMNO] Respuesta modelo (concepto)")
            hablar_con_gestos(robot2_proxies["animated_speech"], texto["respuesta_concepto_modelo"])

            # 1d) post-modelo: humano responde
            respuesta = respuesta_alumno_humano(
                robot1_proxies,
                pregunta_concepto,
                log_timeline_filename=log_timeline_filename,
                etiqueta=u"concepto_post_modelo",
                definicion_concepto=definicion_concepto,
            )

            if respuesta != "si":
                log_event(log_timeline_filename, u"[ROBOT PROFESOR] Retroalimentación (negativa)")
                hablar_con_gestos(robot1_proxies["animated_speech"], texto["retroalimentacion_negativa"])

                time.sleep(1)
                hacer_pausa(robot1_proxies, log_timeline_filename, pausa_larga=pausa_larga)

                log_event(log_timeline_filename, u"[ROBOT PROFESOR] Pase a otro concepto")
                hablar_con_gestos(robot1_proxies["animated_speech"], texto["pase_otro_concepto"])
                time.sleep(2)
                return (concepto_ok, ejemplo_ok)

    # concepto correcto
    concepto_ok = 1
    if log_timeline_filename:
        log_event(log_timeline_filename, u"[RESULTADO] Concepto = Correcto")

    # Ejemplo
    respuesta = preguntar_y_validar(
        robot1_proxies,
        pedir_ejemplo,
        log_timeline_filename=log_timeline_filename,
        etiqueta=u"ejemplo",
        log_line_for_question=u"[PREGUNTA] ejemplo",
        definicion_concepto=definicion_concepto,
    )
    if respuesta != "si":
        if log_timeline_filename:
            log_event(log_timeline_filename, u"[RESULTADO] Ejemplo = Incorrecto")

        if log_timeline_filename:
            log_event(log_timeline_filename, u"[ROBOT ALUMNO] Respuesta modelo (ejemplo)")
        hablar_con_gestos(robot2_proxies["animated_speech"], respuesta_modelo)

        respuesta = respuesta_alumno_humano(
            robot1_proxies,
            pedir_ejemplo,
            log_timeline_filename=log_timeline_filename,
            etiqueta=u"ejemplo_post_modelo",
            definicion_concepto=definicion_concepto,
        )

        if respuesta == "si":
            ejemplo_ok = 1
            hablar_con_gestos(robot1_proxies["animated_speech"], texto["retroalimentacion_positiva"])
            if log_timeline_filename:
                log_event(log_timeline_filename, u"[ROBOT PROFESOR] Retroalimentación (positiva)")
        else:
            ejemplo_ok = 0
            hablar_con_gestos(robot1_proxies["animated_speech"], texto["retroalimentacion_negativa"])
            if log_timeline_filename:
                log_event(log_timeline_filename, u"[ROBOT PROFESOR] Retroalimentación (negativa)")
    else:
        ejemplo_ok = 1
        hablar_con_gestos(robot1_proxies["animated_speech"], texto["retroalimentacion_positiva"])
        if log_timeline_filename:
            log_event(log_timeline_filename, u"[ROBOT PROFESOR] Retroalimentación (positiva)")

    time.sleep(1)
    hacer_pausa(robot1_proxies, log_timeline_filename, pausa_larga=pausa_larga)
    
    if log_timeline_filename:
        log_event(log_timeline_filename, u"[ROBOT PROFESOR] Pase a otro concepto")
    hablar_con_gestos(robot1_proxies["animated_speech"], texto["pase_otro_concepto"])
    time.sleep(2)
    return (concepto_ok, ejemplo_ok)

def posicion_inicial(motion_robot1, motion_robot2):
    motion_robot1.setAngles(["HeadYaw", "HeadPitch"], [0.0, 0.0], 0.1)
    motion_robot2.setAngles(["HeadYaw", "HeadPitch"], [0.0, 0.0], 0.1)

def guardar_registro(resultados, sujeto_id, log_filename):
    total_concepto = sum(1 for c,e in resultados if c == 1)
    total_ejemplo  = sum(1 for c,e in resultados if e == 1)

    lineas = []
    lineas.append(u"Actividad de intervencion - Sujeto {0}:\n".format(sujeto_id))

    for indice, (concepto, ejemplo) in enumerate(resultados, start = 1):
        lineas.append(u"\nTema {0}:\n".format(indice))
        lineas.append(u"Concepto: {0}\n".format("Correcto" if concepto == 1 else "Incorrecto"))
        lineas.append(u"Ejemplo: {0}\n".format("Correcto" if ejemplo == 1 else "Incorrecto"))

    lineas.append(u"\n\nTotal:\n")
    lineas.append(u"Respondio correctamente a {0} preguntas de concepto\n".format(total_concepto))
    lineas.append(u"Respondio correctamente a {0} ejemplos\n".format(total_ejemplo))

    with io.open(log_filename, "w", encoding="utf-8") as log_file:
        log_file.writelines(lineas)

def json_to_utf8(data):
    """Convierte recursivamente todos los unicode del JSON a str UTF-8 (para Python 2.7)."""
    if isinstance(data, dict):
        return {json_to_utf8(key): json_to_utf8(value) for key, value in data.iteritems()}
    elif isinstance(data, list):
        return [json_to_utf8(element) for element in data]
    elif isinstance(data, unicode):
        return data.encode("utf-8")
    else:
        return data

def pedir_sujeto_gui():
    """Ventana para ingresar número de sujeto y nombre."""
    try:
        import Tkinter as tk
        import tkMessageBox
    except Exception:
        sujeto = raw_input("Ingrese el numero de sujeto: ").strip()
        nombre = raw_input("Ingrese el nombre del participante: ").strip()
        return sujeto, nombre

    datos = {"sujeto": None, "nombre": None}

    def on_continuar():
        s_val = entry_sujeto.get().strip()
        n_val = entry_nombre.get().strip()

        if not s_val:
            tkMessageBox.showwarning("Campo vacío", "Ingrese el número de sujeto.")
            return
        if not s_val.isdigit():
            tkMessageBox.showwarning("Valor inválido", "Use solo dígitos en número de sujeto (ej. 1, 2, 3).")
            return
        if not n_val:
            tkMessageBox.showwarning("Campo vacío", "Ingrese el nombre del participante.")
            return

        datos["sujeto"] = s_val
        datos["nombre"] = n_val
        root.destroy()

    def on_enter_key(event):
        on_continuar()

    root = tk.Tk()
    root.title("Intervenciones cognitivas")
    root.resizable(False, False)

    frame = tk.Frame(root, padx=24, pady=24)
    frame.pack()

    lbl1 = tk.Label(frame, text=u"Ingrese el DNI del sujeto:", font=("Arial", 14))
    lbl1.pack(anchor="w", pady=(0, 6))
    entry_sujeto = tk.Entry(frame, width=30, font=("Arial", 14))
    entry_sujeto.pack(fill="x", pady=(0, 12))
    entry_sujeto.focus_set()

    lbl2 = tk.Label(frame, text=u"Ingrese el nombre del participante:", font=("Arial", 14))
    lbl2.pack(anchor="w", pady=(0, 6))
    entry_nombre = tk.Entry(frame, width=30, font=("Arial", 14))
    entry_nombre.pack(fill="x", pady=(0, 12))

    entry_nombre.bind("<Return>", on_enter_key)
    entry_sujeto.bind("<Return>", on_enter_key)

    btn = tk.Button(frame, text="Continuar", font=("Arial", 13), width=12, command=on_continuar)
    btn.pack(pady=(8, 0))

    root.update_idletasks()
    w = 360
    h = 250
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry("{}x{}+{}+{}".format(w, h, x, y))

    root.mainloop()
    if datos["sujeto"] is None:
        import sys
        sys.exit(0)
    return datos["sujeto"], datos["nombre"]

def colocar_nombre_participante(data, nombre):
    """Reemplaza [participante] por el nombre en todo el árbol (dict/list/str)."""
    try:
        basestring  # Py2
    except NameError:
        basestring = str

    if isinstance(data, dict):
        return {k: colocar_nombre_participante(v, nombre) for k, v in data.iteritems()}
    elif isinstance(data, list):
        return [colocar_nombre_participante(x, nombre) for x in data]
    elif isinstance(data, basestring):
        return data.replace("[participante]", nombre)
    else:
        return data

def main():
    global current_sujeto_id
    # 1) WS server
    t = threading.Thread(target=run_ws_server)
    t.daemon = True
    t.start()

    # 2) Robots
    robot1_proxies = preparar_robot(NAO1_IP)
    robot2_proxies = preparar_robot(NAO2_IP)

    # 3) GUI sujeto+nombre
    sujeto_id, nombre = pedir_sujeto_gui()
    current_sujeto_id = sujeto_id

    # 4) Rutas de logs/textos
    log_filename = os.path.join(RESULTS_DIR, "registro_{0}.txt".format(sujeto_id))
    log_timeline_filename = os.path.join(RESULTS_DIR, "registro_{0}_timeline.txt".format(sujeto_id))

    # 5) Cargar actividades y personalizar
    with open("actividades.json", "r") as file:
        actividades = json.load(file)
    actividades = json_to_utf8(actividades)
    actividades = colocar_nombre_participante(actividades, nombre)

    # 6) Informar al navegador el sujeto_id
    ws_broadcast({
        "type": "META",
        "sujeto_id": sujeto_id,
        "csv_filename": build_csv_filename(sujeto_id)
    })

    # 7) Esperar READY del navegador -> ARM/START
    print("[SYNC] Esperando READY del navegador")
    while not web_ready:
        time.sleep(0.1)
    print("[SYNC] Navegador listo. Enviando ARM -> START…")
    send_arm_and_start(ARM_DELAY_MS)

    # 8) Cabecera timeline
    try:
        with io.open(log_timeline_filename, "w", encoding="utf-8") as f:
            f.write(u"Timeline de intervención - Sujeto {} ({})\n".format(sujeto_id, nombre))
    except Exception as e:
        print("[timeline init] WARNING:", e)
    log_event(log_timeline_filename, u"Cronómetro iniciado")
    log_event(log_timeline_filename, u"[SYNC] START sincronizado")

    resultados = []

    # 9) Bienvenida inicial del profesor
    log_event(log_timeline_filename, u"[ROBOT PROFESOR] Bienvenida inicial")
    texto_bienvenida = "Hola, [participante]. Bienvenido a la sesion de hoy. Estamos muy contentos de tenerte aqui. En esta actividad vamos a explorar juntos algunos conceptos fundamentales sobre inteligencia artificial. Para ello, cuento con la ayuda de mi compañero NAO, quien también estará participando en esta sesión. Ambos estaremos aqui para acompañarte, guiarte y responder a tus preguntas durante todo el proceso. Esperamos que disfrutes la experiencia y que aprendas mucho. Asi que, comencemos"
    texto_bienvenida = colocar_nombre_participante(texto_bienvenida, nombre)
    hablar_con_gestos(robot1_proxies["animated_speech"], texto_bienvenida)

    time.sleep(2)

    # 10) Loop de actividades

    total_actividades = len(actividades)
    indice_mitad = total_actividades // 2
    print(indice_mitad)

    for idx, actividad in enumerate(actividades, start=1):
        hablar_con_gestos(robot1_proxies["animated_speech"], "\\vct=95\\\\rspd=90\\" + actividad["tema"])
        log_event(log_timeline_filename, actividad["tema"])
        time.sleep(1)

        # Fase de observación
        fase_observacion(
            robot1_proxies, robot2_proxies, actividad["parte_observacion"],
            log_timeline_filename=log_timeline_filename
        )
        posicion_inicial(robot1_proxies["motion"], robot2_proxies["motion"])

        time.sleep(2)
        pausa_larga = (idx == indice_mitad)

        concepto_ok, ejemplo_ok = fase_experimental(
            robot1_proxies,
            robot2_proxies,
            actividad["parte_experimentacion"],
            actividad["parte_observacion"]["profesor_corrige"], 
            log_timeline_filename=log_timeline_filename,
            pausa_larga = pausa_larga
        )
        resultados.append((concepto_ok, ejemplo_ok))

        posicion_inicial(robot1_proxies["motion"], robot2_proxies["motion"])
        log_event(log_timeline_filename, u"--- Siguiente concepto ---")

    # 11) Despedida final
    log_event(log_timeline_filename, u"[ROBOT PROFESOR] Cierre de la sesión")
    texto_cierre = "Hemos llegado al final de la sesión de hoy. Gracias por tu tiempo, tu atención y tu participación, [participante]. Esperamos que los conceptos que revisamos te hayan resultado claros y útiles, y que esta experiencia haya sido tan enriquecedora para ti como lo fue para nosotros. Hasta pronto, [participante], y que tengas un excelente día."
    texto_cierre = colocar_nombre_participante(texto_cierre, nombre)
    hablar_con_gestos(robot1_proxies["animated_speech"], texto_cierre)
    time.sleep(1)

    # 12) Guardar resumen por sujeto
    guardar_registro(resultados, sujeto_id, log_filename)

    ws_broadcast({
        "type": "FIN",
        "sujeto_id": sujeto_id,
        "csv_filename": build_csv_filename(sujeto_id)
    })
    print("[SYNC] Señal FIN enviada al navegador para guardar CSV")
    time.sleep(1.0)

    procesar_respuesta("salir")

if __name__ == "__main__":
    main()
