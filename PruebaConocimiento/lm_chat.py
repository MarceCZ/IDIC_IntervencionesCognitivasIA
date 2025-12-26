from PyQt6.QtCore import QThread, pyqtSignal
from config import API_KEY, procesar_GPT

class LMValidatorThread(QThread):
    """
    Hilo que llama a la API de Gemini para evaluar la respuesta.
    Emite:
        finished_eval(correcto: bool, mensaje: str, pregunta: str, respuesta: str)

    - Si hay error con Gemini:
        correcto = False
        mensaje = "ERROR: <detalle>"
    - Si Gemini responde bien:
        mensaje = "si" o "no"
        correcto = (mensaje == "si")
    """
    finished_eval = pyqtSignal(bool, str, str, str)

    def __init__(self, question: str, answer: str, parent=None):
        super().__init__(parent)
        self.question = question
        self.answer = answer

    def run(self):
        try:
            if not API_KEY:
                error_msg = "ERROR: No se encontró GOOGLE_API_KEY / GEMINI_API_KEY. No se pudo evaluar con Gemini."
                self.finished_eval.emit(False, error_msg, self.question, self.answer)
                return

            prompt = (
                "Actúas como un evaluador experto en Inteligencia Artificial y Machine Learning.\n"
                "Tu tarea es determinar si la respuesta del estudiante es conceptualmente correcta\n"
                "respecto al concepto preguntado.\n\n"

                "CRITERIOS DE EVALUACIÓN (FLEXIBLES PERO PRECISOS):\n"
                "1. Acepta respuestas correctas aunque estén explicadas con lenguaje simple y no técnico.\n"
                "2. Usa un criterio robusto para las respuestas cortas, generalmente no refleja la definición del concepto. Evalua si es correcto la definicion del concepto\n"
                "3. Marca como incorrecta solo si:\n"
                "   - La respuesta está en un dominio diferente a IA/ML.\n"
                "   - Contiene errores conceptuales graves.\n"
                "   - Es demasiado vaga y no se entiende la idea central.\n"
                "   - Contradice lo que realmente significa el concepto.\n"
                "   - Describe algo que no tiene relación con modelos, datos, aprendizaje o predicción.\n"
                "4. No seas extremadamente estricto con tecnicismos ni palabras exactas.\n"
                "   Evalúa la intención general y la coherencia.\n\n"

                "FORMATO DE RESPUESTA:\n"
                "- Responde solo con 'si' o 'no' en minúsculas.\n"
                "- No añadas explicaciones ni texto adicional.\n\n"

                f"Pregunta: {self.question}\n"
                f"Respuesta del estudiante: {self.answer}\n"
            )

            resp = procesar_GPT(prompt)
            resp = (resp or "").strip().lower()

            print("RESPUESTA LM:", repr(resp))
            tokens = resp.split()
            primer_token = tokens[0] if tokens else ""

            if primer_token in ("sí", "si", "si.", "sí.", "si,", "sí,"):
                resp_normalizada = "si"
            elif primer_token in ("no", "no.", "no,", "no\n"):
                resp_normalizada = "no"
            else:
                error_msg = f"ERROR: LM devolvió un formato inesperado: '{resp}'"
                self.finished_eval.emit(False, error_msg, self.question, self.answer)
                return

            correcto = (resp_normalizada == "si")
            self.finished_eval.emit(correcto, resp_normalizada, self.question, self.answer)

        except Exception as e:
            error_msg = f"ERROR: Error en la evaluación con LM: {e}"
            self.finished_eval.emit(False, error_msg, self.question, self.answer)
