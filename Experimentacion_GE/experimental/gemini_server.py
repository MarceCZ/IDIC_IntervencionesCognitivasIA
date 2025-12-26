import socket
import speech_recognition as sr
import os
import google.generativeai as genai

# Configuración de la API de Google Gemini mediante la variable de entorno o configurar directamente
API_KEY = "TU_API_KEY_AQUI"  # Reemplaza con tu clave de API de Google Gemini
genai.configure(api_key=API_KEY)
model_name = "gemini-2.5-flash"
model = genai.GenerativeModel(model_name)

# Datos
HOST = 'localhost'        # Cambiar si el servidor está en otra máquina
PORT_SOCKET = 12345       # Debe coincidir con el del servidor
RUTA = "./respuesta.wav"  # Ruta local del audio descargado

def speech_to_text():
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(RUTA)

    with audio_file as source:
        audio_data = recognizer.record(source)
    try:
        data = recognizer.recognize_google(audio_data, language="es-ES")
        
        return data
    except sr.UnknownValueError:
        return "No respondió"
    
def procesar_GPT(prompt):
    try:
        resp = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.4,
            }
        )
        return resp.text.strip()
    except Exception as e:
        print("Error llamando a Gemini:", e)
        return "no"

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT_SOCKET))
    s.listen(1)  # Esperar conexión del cliente
    print(f"Servidor escuchando en {HOST}:{PORT_SOCKET}")
    print("Esperando conexión del cliente...")

    while True:
        conn, addr = s.accept()
        data = conn.recv(4096).decode('utf-8').strip()
        print("Contexto recibido bruto:", data)

        if data.lower() == "salir":
            print("Conexión cerrada por el cliente.")
            conn.close()
            break

        # ===========================
        # Parsear: pregunta | tipo | definicion
        # ===========================
        pregunta = data
        tipo = ""
        definicion = ""

        parts = data.split('|')
        if len(parts) >= 2:
            pregunta = parts[0].strip()
            tipo = parts[1].strip()
            if len(parts) >= 3:
                definicion = '|'.join(parts[2:]).strip()

        print("Pregunta:", pregunta)
        print("Tipo:", tipo)
        if definicion:
            print("Definición de referencia (profesor_corrige):", definicion)

        respuesta_estudiante = speech_to_text()
        print("Respuesta del estudiante:", respuesta_estudiante)

        # Bloque de definición para el prompt
        bloque_def = ""
        if definicion:
            bloque_def = (
                "Definición de referencia del concepto (proporcionada por el profesor):\n"
                "\"" + definicion + "\"\n\n"
                "Usa esta definición solo como guía para juzgar si la respuesta del estudiante expresa "
                "la idea central del concepto. No la repitas literalmente en tu respuesta.\n\n"
            )

        # Construir prompt según tipo
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

        respuesta_modelo = procesar_GPT(prompt)
        respuesta_modelo = respuesta_modelo.replace("*", "")
        print("Respuesta generada por Gemini:", respuesta_modelo)
        conn.sendall(respuesta_modelo.encode('utf-8'))

    s.close()


if __name__ == "__main__":
    main()