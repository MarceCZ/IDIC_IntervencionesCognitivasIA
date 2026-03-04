import socket
import speech_recognition as sr
import requests
import os
import json

# =========================
# CONFIG
# =========================
HOST = "localhost"
PORT_SOCKET = 12345

# OJO: en tu código lo usas como URL endpoint, no como key.
# Debe ser algo tipo: http://localhost:8000/v1/chat/completions
API_ENDPOINT = "http://10.143.67.89:1234/v1/chat/completions"

RUTA = "./respuesta.wav"  # audio descargado desde NAO (por tu script Py2)

# =========================
# STT
# =========================
def speech_to_text():
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(RUTA)

    with audio_file as source:
        audio_data = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio_data, language="es-ES")
    except sr.UnknownValueError:
        print("[STT] No se pudo entender el audio.")
        return "No respondió"
    except Exception as e:
        print("[STT] Error:", e)
        return "No respondió"

# =========================
# LLM CALL
# =========================
def procesar_GPT(prompt):
    if not API_ENDPOINT:
        print("[ERROR] Falta API_GPT_MODEL (endpoint URL).")
        return "no"

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "stream": False,
    }

    try:
        r = requests.post(API_ENDPOINT, json=payload, timeout=60)
    except Exception as e:
        print("[HTTP] Error conectando:", e)
        return "no"

    if r.status_code != 200:
        print("[HTTP] Status:", r.status_code, "Body:", r.text[:200])
        return "no"

    try:
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print("[PARSE] Error leyendo respuesta:", e)
        return "no"

def normalize_verdict(txt):
    if not txt:
        return "no"
    t = txt.replace("*", "").strip().lower()

    # Robusto: si el modelo se sale del formato
    if t.startswith("si"):
        return "si"
    if t.startswith("no"):
        return "no"

    # Si aparece "si" sin "no", tomamos si
    if ("si" in t) and ("no" not in t):
        return "si"
    return "no"

# =========================
# MAIN SERVER
# =========================
def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT_SOCKET))
    s.listen(1)

    print("[GPT_SERVER] Escuchando en {}:{}".format(HOST, PORT_SOCKET))

    while True:
        conn, addr = s.accept()
        try:
            raw = conn.recv(4096)
            data = raw.decode("utf-8", errors="ignore").strip()

            if data.lower() == "salir":
                print("[GPT_SERVER] Cierre solicitado por cliente.")
                conn.close()
                break

            # ===========================
            # Parsear: pregunta | tipo | definicion
            # ===========================
            pregunta = data
            tipo = ""
            definicion = ""

            parts = data.split("|")
            if len(parts) >= 2:
                pregunta = parts[0].strip()
                tipo = parts[1].strip()
                if len(parts) >= 3:
                    definicion = "|".join(parts[2:]).strip()

            print("[GPT_SERVER] Pregunta:", pregunta)
    
            # 1) transcribir
            respuesta_estudiante = speech_to_text()
            print("[GPT_SERVER] Respuesta estudiante:", respuesta_estudiante)

            # 2) bloque guía (definición)
            bloque_def = ""
            if definicion:
                bloque_def = (
                    "Definición de referencia del concepto (proporcionada por el profesor):\n"
                    "\"{}\"\n\n"
                    "Usa esta definición solo como guía para juzgar si la respuesta del estudiante expresa "
                    "la idea central del concepto. No la repitas literalmente en tu respuesta.\n\n"
                ).format(definicion)

            # 3) prompt
            if tipo.lower() == "concepto":
                prompt = (
                    "Evalúa la respuesta del estudiante respecto al concepto preguntado.\n"
                    "Tu criterio debe ser el siguiente:\n"
                    "- Responde 'si' SOLO si la respuesta expresa la IDEA CENTRAL del concepto, aunque use otras palabras o sea más breve.\n"
                    "- La respuesta debe mencionar al menos los elementos esenciales del concepto o ideas estrechamente relacionadas, "
                    "no solo palabras sueltas.\n"
                    "- Si la respuesta es muy vaga, general, irrelevante, solo repite parte de la pregunta o contiene un error fuerte "
                    "sobre el concepto, responde 'no'.\n"
                    "- Si el estudiante dice que no sabe, no responde o da una frase sin relación, responde 'no'.\n"
                    "No expliques tu razonamiento.\n"
                    "Responde SOLO con 'si' o 'no' en minúsculas.\n\n"
                    + bloque_def +
                    "Pregunta (concepto): " + pregunta + "\n"
                    "Respuesta del estudiante: " + respuesta_estudiante + "\n"
                )
            else:
                prompt = (
                    "Evalúa si el ejemplo del estudiante es coherente con el concepto enseñado.\n"
                    "Tu criterio debe ser el siguiente:\n"
                    "- Responde 'si' SOLO si el ejemplo representa claramente el concepto, aunque no sea perfecto.\n"
                    "- El ejemplo debe ser específico y mostrar cómo se aplica el concepto en una situación concreta.\n"
                    "- Si el ejemplo es muy vago, genérico, no tiene relación clara con el concepto o contiene un error fuerte, responde 'no'.\n"
                    "- Si el estudiante dice que no sabe, no responde o da algo sin sentido, responde 'no'.\n"
                    "No expliques tu razonamiento.\n"
                    "Responde SOLO con 'si' o 'no' en minúsculas.\n\n"
                    + bloque_def +
                    "Concepto (pregunta): " + pregunta + "\n"
                    "Ejemplo del estudiante: " + respuesta_estudiante + "\n"
                )

            # 4) evaluar con LLM
            raw_model = procesar_GPT(prompt)
            verdict = normalize_verdict(raw_model)

            # 5) responder JSON (para que Py2 pueda abrir GUI manual)
            payload_out = {
                "verdict": verdict,
                "transcript": respuesta_estudiante
            }

            out_txt = json.dumps(payload_out, ensure_ascii=False)
            print("[GPT_SERVER] Enviando:", out_txt)

            conn.sendall(out_txt.encode("utf-8"))

        finally:
            try:
                conn.close()
            except:
                pass

    s.close()

if __name__ == "__main__":
    main()
