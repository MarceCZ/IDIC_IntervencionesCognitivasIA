import os
import json
from typing import List
# import google.generativeai as genai
import requests

# Utiliza la variable de entorno GEMINI_API_KEY para la clave de API
# API_KEY = "TU_API_KEY" (Gemini, ejemplo)
API_KEY = "" #Reemplaza con la URL de tu servidor http://XXX.XXX.XXX.XXX:1234/v1/chat/completions 

'''
Desbloquear el codigo para utilizar Gemini
if API_KEY:
    genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME) if API_KEY else None
'''
# Ruta al JSON con las preguntas
RUTA_PREGUNTAS_JSON = "conceptos.json"


def procesar_GPT(prompt: str) -> str:
    '''
    Desbloquear el codigo para utilizar Gemini
    
    Envía un prompt a Gemini y devuelve el texto de respuesta.
    Lanza excepción si algo falla (la maneja el hilo que llama).
    
    if model is None:
        raise RuntimeError("No hay API KEY configurada para Gemini.")
    resp = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.4,
        }
    )
    return (resp.text or "").strip()
    '''
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "stream": False
    }

    response = requests.post(API_KEY, json=payload)

    # Mostrar la respuesta
    if response.status_code == 200:
        try:
            data = response.json()
            # Intentar extraer el contenido si existe
            content = data['choices'][0]['message']['content']
            return content

        except KeyError:
            print("ERROR del servidor: Intente de nuevo.")
    else:
        print("Error: No se pudo conectar al servidor.")
    return "Lo siento, no pude procesar la solicitud."

def cargar_preguntas_desde_json(ruta: str) -> List[str]:
    """
    Lee un archivo JSON y devuelve una lista de preguntas (strings).
    Formato esperado:
    {
      "preguntas": ["pregunta 1", "pregunta 2", ...]
    }
    o simplemente:
    ["pregunta 1", "pregunta 2", ...]
    """
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "preguntas" in data:
        preguntas = data["preguntas"]
    elif isinstance(data, list):
        preguntas = data
    else:
        raise ValueError("El JSON debe ser un objeto con clave 'preguntas' o una lista de strings.")

    preguntas_limpias = [str(p).strip() for p in preguntas if str(p).strip()]
    if not preguntas_limpias:
        raise ValueError("No se encontraron preguntas válidas en el JSON.")

    return preguntas_limpias
