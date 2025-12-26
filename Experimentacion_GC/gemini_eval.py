import sys
import json
from typing import Dict

from PyQt6.QtCore import QThread, pyqtSignal

from config import API_KEY, MODEL


def evaluar_con_gemini(respuesta_usuario: str, concepto_eval: Dict) -> Dict:
    """
    concepto_eval debe tener:
      - 'titulo'      : str
      - 'explicacion' : str  (para concepto: profesor_explica; para ejemplo: respuesta_modelo)
      - 'pregunta'    : str  (texto de la pregunta que se le hizo al estudiante)

    Retorna: {'correct': bool}
    """
    try:
        import google.generativeai as genai

        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(MODEL)

        titulo      = concepto_eval.get("titulo", "Concepto")
        explicacion = concepto_eval.get("explicacion", "")
        pregunta    = concepto_eval.get("pregunta", "")

        prompt = f"""
            Eres un evaluador pedagógico. Tu tarea es decidir si la respuesta del estudiante
            demuestra que entiende la IDEA CENTRAL del concepto, usando la explicación oficial
            como referencia.

            CRITERIOS:

            - Marca "correct": true si:
            - La respuesta expresa con sus propias palabras la idea central de la EXPLICACION_OFICIAL.
            - Puede omitir detalles secundarios, ejemplos o formulaciones exactas.
            - Puede tener errores menores, pero la idea principal está bien capturada.
            - Cuando tengas duda, da prioridad a considerar correcta la respuesta si la idea central está presente.

            - Marca "correct": false si:
            - La respuesta no contiene la idea central del concepto.
            - La respuesta es demasiado vaga o genérica (por ejemplo, frases que podrían aplicarse a casi cualquier cosa).
            - La respuesta contradice de forma clara la EXPLICACION_OFICIAL.
            - La respuesta es muy corta y no permite inferir que comprende el concepto.

            Devuelve SOLO este JSON, sin texto extra, sin explicaciones:

            {{
            "correct": true
            }}

            o

            {{
            "correct": false
            }}

            CONCEPTO_TITULO: {titulo}
            EXPLICACION_OFICIAL: {explicacion}
            PREGUNTA_REALIZADA: {pregunta}
            RESPUESTA_DEL_ESTUDIANTE: {respuesta_usuario}
            """.strip()

        result = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
            }
        )
        texto = (result.text or "").strip()

        try:
            data = json.loads(texto)
        except Exception:
            i, j = texto.find("{"), texto.rfind("}")
            data = json.loads(texto[i:j+1]) if i != -1 and j != -1 else None

        if not isinstance(data, dict) or "correct" not in data:
            return {"correct": False}

        return {"correct": bool(data["correct"])}

    except Exception as e:
        print(f"Error al llamar a Gemini: {e}", file=sys.stderr)
        return {"correct": False}


class EvalWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, texto: str, concepto_eval: Dict):
        super().__init__()
        self.texto = texto
        self.concepto_eval = concepto_eval

    def run(self):
        res = evaluar_con_gemini(self.texto, self.concepto_eval)
        print(res)
        self.finished.emit(res)
