import sys
import json
from typing import List
import os
import google.generativeai as genai

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QStackedWidget, QMessageBox, QHBoxLayout,
    QFrame, QSizePolicy
)

# ============================
#  CONFIG: GEMINI + JSON
# ============================

# Soporta GOOGLE_API_KEY o GEMINI_API_KEY
API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME) if API_KEY else None

RUTA_PREGUNTAS_JSON = "conceptos.json"


def procesar_GPT(prompt: str) -> str:
    """
    Envía un prompt a Gemini y devuelve el texto de respuesta.
    Lanza excepción si algo falla (la maneja luego el hilo).
    """
    if model is None:
        raise RuntimeError("No hay API KEY configurada para Gemini.")
    resp = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.2,
        }
    )
    return (resp.text or "").strip()


# ============================
#  FUNCIÓN: CARGAR PREGUNTAS JSON
# ============================

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


# ============================
#  WORKER PARA GEMINI (QThread)
# ============================

class GeminiValidatorThread(QThread):
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
                "Eres un evaluador experto en Inteligencia Artificial y Machine Learning.\n"
                "Debes decidir si la respuesta del estudiante es conceptualmente CORRECTA\n"
                "respecto al concepto de IA/ML que se está preguntando.\n\n"

                "REGLAS OBLIGATORIAS:\n"
                "1. Evalúa EXCLUSIVAMENTE en el dominio de IA y Machine Learning.\n"
                "2. Si la respuesta describe el concepto en otro contexto (ejemplo: modelo de moda,\n"
                "   clasificación legal, desempeño laboral, sobreajuste de ropa, etc.), responde 'no'.\n"
                "3. Si la respuesta es vaga, muy corta, o no menciona nada relacionado con IA/ML\n"
                "   (como datos, algoritmos, aprendizaje, patrones, predicción, modelos matemáticos), responde 'no'.\n"
                "4. Solo responde 'si' si la definición es clara, coherente y pertenece al dominio de IA/ML.\n\n"

                "FORMATO DE RESPUESTA:\n"
                "- Responde SOLO con 'si' o 'no' en minúsculas.\n"
                "- No añadas explicaciones, razones, ni texto adicional.\n\n"

                f"Pregunta: {self.question}\n"
                f"Respuesta del estudiante: {self.answer}\n"
            )

            resp = procesar_GPT(prompt)
            resp = resp.strip().lower()

            print("RESPUESTA GEMINI:", repr(resp))  # Para depuración opcional

            # Tomar solo la primera palabra por si devuelve "si, es correcto"
            tokens = resp.split()
            primer_token = tokens[0] if tokens else ""

            if primer_token in ("sí", "si", "si.", "sí.", "si,", "sí,"):
                resp_normalizada = "si"
            elif primer_token in ("no", "no.", "no,", "no\n"):
                resp_normalizada = "no"
            else:
                error_msg = f"ERROR: Gemini devolvió un formato inesperado: '{resp}'"
                self.finished_eval.emit(False, error_msg, self.question, self.answer)
                return

            correcto = (resp_normalizada == "si")
            self.finished_eval.emit(correcto, resp_normalizada, self.question, self.answer)

        except Exception as e:
            error_msg = f"ERROR: Error en la evaluación con Gemini: {e}"
            self.finished_eval.emit(False, error_msg, self.question, self.answer)


# ============================
#  HELPERS DE UI
# ============================

def crear_card(parent: QWidget) -> QFrame:
    """
    Crea un QFrame tipo 'card' con fondo blanco y bordes redondeados,
    centrado dentro del layout del parent.
    - Ocupa buena parte de la ventana (con márgenes amplios).
    - Se adapta cuando la ventana está maximizada.
    """
    root_layout = QVBoxLayout(parent)
    # Márgenes algo grandes para que el card crezca bastante
    root_layout.setContentsMargins(160, 80, 160, 80)
    root_layout.setSpacing(0)
    root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    card = QFrame()
    card.setObjectName("card")
    # Deja que crezca tanto como pueda dentro de esos márgenes
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    root_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

    card.setStyleSheet("""
        QFrame#card {
            background-color: #ffffff;
            border-radius: 18px;
        }
    """)

    return card


# ============================
#  VISTAS
# ============================

class WelcomeView(QWidget):
    def __init__(self, on_start_callback, parent=None):
        super().__init__(parent)

        # Fondo oscuro
        self.setStyleSheet("""
            QWidget#WelcomeRoot {
                background-color: #0f172a;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 10px;
                padding: 10px 26px;
                font-size: 15pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.setObjectName("WelcomeRoot")

        card = crear_card(self)
        card.setFixedWidth(1440)
        card.setFixedHeight(960)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(60, 40, 60, 40)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Prueba de conocimientos en Inteligencia Artificial")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 50pt; font-weight: 700; color: #111827;")
        

        subtitle = QLabel("Actividad de evaluación rápida")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 30pt; color: #6b7280;")

        desc = QLabel(
            "Responde 8 preguntas sobre conceptos básicos de IA y aprendizaje automático.\n"
            "Escribe tus respuestas con tus propias palabras. Al finalizar verás tu puntuación total."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 20pt; color: #111827;")

        btn = QPushButton("Comenzar el test")
        btn.setFixedHeight(80)
        btn.setFixedWidth(300)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 30px;       
                font-size: 20pt;           
                font-weight: 700;         
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn.clicked.connect(on_start_callback)

        card_layout.addWidget(title)
        card_layout.addSpacing(50)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(8)
        card_layout.addWidget(desc)
        card_layout.addSpacing(8)
        card_layout.addSpacing(40)
        card_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)


class QuestionView(QWidget):
    def __init__(self, on_submit_callback, parent=None):
        """
        on_submit_callback(question_text: str, user_answer: str)
        """
        super().__init__(parent)
        self.on_submit_callback = on_submit_callback

        self.setObjectName("QuestionRoot")
        self.setStyleSheet("""
            QWidget#QuestionRoot {
                background-color: #0f172a;
                font-family: 'Segoe UI', Arial;
            }
            QTextEdit {
                border-radius: 10px;
                border: 1px solid #d1d5db;
                padding: 8px 10px;
                font-size: 12pt;
            }
            QTextEdit:focus {
                border: 1px solid #2563eb;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 10px;
                padding: 8px 24px;
                font-size: 13pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

        card = crear_card(self)
        card.setFixedWidth(1200)
        card.setFixedHeight(500)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        self.lbl_progress = QLabel("Pregunta 1 de N")
        self.lbl_progress.setStyleSheet("font-size: 20pt; color: #6b7280;")
        header_layout.addWidget(self.lbl_progress)
        header_layout.addStretch()

        self.lbl_question = QLabel("Pregunta...")
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setStyleSheet("font-size: 36pt; font-weight: 700; color: #111827;")

        self.txt_answer = QTextEdit()
        self.txt_answer.setPlaceholderText("Escribe aquí tu respuesta...")
        self.txt_answer.setMinimumHeight(180)
        self.txt_answer.setStyleSheet("font-size: 25pt;")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_submit = QPushButton("Enviar respuesta")
        self.btn_submit.setFixedHeight(70)     
        self.btn_submit.setFixedWidth(300)
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 30px;
                font-size: 24pt;            
                font-weight: 700;           
                padding: 14px 30px;   
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.btn_submit.clicked.connect(self._on_submit_clicked)
        btn_layout.addWidget(self.btn_submit)

        layout.addLayout(header_layout)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_question)
        layout.addSpacing(10)
        layout.addWidget(self.txt_answer)
        layout.addSpacing(10)
        layout.addLayout(btn_layout)

    def set_question(self, question_text: str, idx: int, total: int):
        self.lbl_question.setText(question_text)
        self.lbl_progress.setText(f"Pregunta {idx} de {total}")
        self.txt_answer.clear()
        self.txt_answer.setFocus()

    def _on_submit_clicked(self):
        answer = self.txt_answer.toPlainText().strip()
        if not answer:
            QMessageBox.warning(self, "Respuesta vacía", "Por favor, escribe una respuesta antes de continuar.")
            return

        self.on_submit_callback(self.lbl_question.text(), answer)


class ProcessingView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProcessingRoot")
        self.setStyleSheet("""
            QWidget#ProcessingRoot {
                background-color: #0f172a;
                font-family: 'Segoe UI', Arial;
            }
        """)

        card = crear_card(self)
        card.setFixedWidth(1000)
        card.setFixedHeight(400)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel("Evaluando tu respuesta…")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 40pt; font-weight: 700; color: #111827;")

        lbl = QLabel("Por favor, espera unos segundos mientras se analiza tu respuesta.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 30pt; color: #4b5563;")

        layout.addWidget(lbl_title)
        layout.addSpacing(15)
        layout.addWidget(lbl)


class FinalScoreView(QWidget):
    def __init__(self, score: int, total: int, on_close_callback, parent=None):
        super().__init__(parent)
        self.setObjectName("FinalRoot")
        self.setStyleSheet("""
            QWidget#FinalRoot {
                background-color: #0f172a;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border-radius: 10px;
                padding: 10px 30px;
                font-size: 15pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

        card = crear_card(self)
        card.setFixedWidth(800)
        card.setFixedHeight(500)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel("Puntuación final")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 45pt; font-weight: 700; color: #111827;")

        lbl_score = QLabel(f"{score} / {total}")
        lbl_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_score.setStyleSheet("font-size: 80pt; font-weight: 800; color: #2563eb;")

        btn_close = QPushButton("Cerrar")
        btn_close.setFixedHeight(70)
        btn_close.setFixedWidth(250)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;     
                color: white;
                border-radius: 30px;
                font-size: 26pt;
                font-weight: 600;
                padding: 12px 30px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        btn_close.clicked.connect(on_close_callback)

        layout.addWidget(lbl_title)
        layout.addSpacing(20)
        layout.addWidget(lbl_score)
        layout.addSpacing(35)
        layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignCenter)


# ============================
#  VENTANA PRINCIPAL
# ============================

class MainWindow(QWidget):
    def __init__(self, preguntas: List[str]):
        super().__init__()
        self.setWindowTitle("Prueba de Conocimientos de IA")

        self.preguntas = preguntas
        self.num_preguntas = len(preguntas)

        self.stack = QStackedWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)

        # Estado
        self.current_index = 0
        self.score = 0
        self.current_thread: GeminiValidatorThread | None = None

        # Vistas
        self.welcome_view = WelcomeView(self.start_quiz)
        self.stack.addWidget(self.welcome_view)

        self.question_view = QuestionView(self.submit_answer)
        self.stack.addWidget(self.question_view)

        self.processing_view = ProcessingView()
        self.stack.addWidget(self.processing_view)

        # Mostrar bienvenida
        self.stack.setCurrentWidget(self.welcome_view)

    # ---- Flujo ----

    def start_quiz(self):
        self.current_index = 0
        self.score = 0

        # Reiniciar archivo de seguimiento detallado y escribir encabezado
        try:
            with open("detalle_respuestas_quiz_ia.txt", "w", encoding="utf-8") as f:
                f.write("Seguimiento general de resultados:\n\n")
        except Exception as e:
            QMessageBox.warning(self, "Error al iniciar seguimiento",
                                f"No se pudo crear el archivo de seguimiento:\n{e}")

        self.show_next_question()

    def show_next_question(self):
        if self.current_index >= self.num_preguntas:
            self.show_final_score()
            return

        question_text = self.preguntas[self.current_index]
        self.question_view.set_question(question_text, self.current_index + 1, self.num_preguntas)
        self.stack.setCurrentWidget(self.question_view)

    def submit_answer(self, question_text: str, user_answer: str):
        # Cambiar a vista de "procesando"
        self.stack.setCurrentWidget(self.processing_view)

        # Lanzar hilo que llama a Gemini
        self.current_thread = GeminiValidatorThread(question_text, user_answer)
        self.current_thread.finished_eval.connect(self.on_evaluation_finished)
        self.current_thread.start()

    def on_evaluation_finished(self, correcto: bool, mensaje: str, pregunta: str, respuesta: str):
        # Limpia referencia al hilo
        self.current_thread = None

        es_error = mensaje.startswith("ERROR:")

        # Guardar detalle en formato de seguimiento general
        try:
            with open("detalle_respuestas_quiz_ia.txt", "a", encoding="utf-8") as f:
                n = self.current_index + 1
                if es_error:
                    f.write(
                        f"Pregunta {n}: {pregunta}\n"
                        f"Respuesta: {respuesta}\n"
                        f"Resultado: No evaluado (error en la evaluación automática)\n"
                        f"Detalle error: {mensaje}\n\n"
                    )
                else:
                    f.write(
                        f"Pregunta {n}: {pregunta}\n"
                        f"Respuesta: {respuesta}\n"
                        f"Resultado: {'Correcto' if correcto else 'Incorrecto'}\n\n"
                    )
        except Exception as e:
            QMessageBox.warning(self, "Error al guardar detalle",
                                f"No se pudo guardar el detalle:\n{e}")

        # Manejo de error Gemini: mostrar alerta y NO sumar score
        if es_error:
            QMessageBox.critical(
                self,
                "Error en la evaluación",
                f"Ocurrió un problema al evaluar la respuesta con Gemini:\n\n{mensaje}"
            )
        else:
            if mensaje == "si" and correcto:
                self.score += 1

        # Avanzar a la siguiente pregunta
        self.current_index += 1
        self.show_next_question()

    def show_final_score(self):
        # Crear vista de resultado final
        final_view = FinalScoreView(self.score, self.num_preguntas, self.close)
        self.stack.addWidget(final_view)
        self.stack.setCurrentWidget(final_view)

        # Guardar resultado en TXT (solo puntuación final)
        try:
            with open("resultados_quiz_ia.txt", "a", encoding="utf-8") as f:
                f.write(f"{self.score}/{self.num_preguntas}\n")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error al guardar resultado",
                f"No se pudo guardar el resultado en TXT:\n{e}"
            )


# ============================
#  MAIN
# ============================

def main():
    # Cargar preguntas desde JSON ANTES de crear la ventana
    try:
        preguntas = cargar_preguntas_desde_json(RUTA_PREGUNTAS_JSON)
    except Exception as e:
        print(f"Error al cargar preguntas desde {RUTA_PREGUNTAS_JSON}: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MainWindow(preguntas)
    # Ventana maximizada
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
