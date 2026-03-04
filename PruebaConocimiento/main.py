import os
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
)

from config import cargar_preguntas_desde_json, RUTA_PREGUNTAS_JSON
from lm_chat import LMValidatorThread
from views import WelcomeView, QuestionView, ProcessingView, FinalScoreView, DniView


# ============================
#  CARPETA RESULTADOS
# ============================

def asegurar_carpeta_resultados() -> str:
    carpeta = "resultados"
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    return carpeta


# ============================
#  VENTANA PRINCIPAL
# ============================

class MainWindow(QWidget):
    def __init__(self, preguntas):
        super().__init__()
        self.setWindowTitle("Prueba de Conocimientos de IA")

        self.preguntas = preguntas
        self.num_preguntas = len(preguntas)

        # Estado del quiz
        self.current_index = 0
        self.score = 0
        self.current_thread: LMValidatorThread | None = None
        self.dni_participante: str = ""

        # Stack
        self.stack = QStackedWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)

        # Vistas
        self.welcome_view = WelcomeView(self.show_dni_view)
        self.stack.addWidget(self.welcome_view)

        self.dni_view = DniView(self.start_quiz)
        self.stack.addWidget(self.dni_view)

        self.question_view = QuestionView(self.submit_answer)
        self.stack.addWidget(self.question_view)

        self.processing_view = ProcessingView()
        self.stack.addWidget(self.processing_view)

        self.stack.setCurrentWidget(self.welcome_view)

    # -------------------------
    #  FLUJO PRINCIPAL
    # -------------------------

    def show_dni_view(self):
        self.stack.setCurrentWidget(self.dni_view)

    def start_quiz(self, dni: str):
        self.dni_participante = dni.strip()
        self.current_index = 0
        self.score = 0

        carpeta = asegurar_carpeta_resultados()
        self.ruta = os.path.join(
            carpeta, f"{self.dni_participante}.txt"
        )

        try:
            with open(self.ruta, "w", encoding="utf-8") as f:
                f.write("Seguimiento de la prueba\n")
                f.write(f"DNI: {self.dni_participante}\n\n")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"No se pudo crear el archivo del participante:\n{e}",
            )

        self.show_next_question()

    def show_next_question(self):
        if self.current_index >= self.num_preguntas:
            self.show_final_score()
            return

        question_text = self.preguntas[self.current_index]
        self.question_view.set_question(
            question_text,
            self.current_index + 1,
            self.num_preguntas,
        )
        self.stack.setCurrentWidget(self.question_view)

    def submit_answer(self, question_text: str, user_answer: str):
        self.stack.setCurrentWidget(self.processing_view)

        self.current_thread = LMValidatorThread(question_text, user_answer)
        self.current_thread.finished_eval.connect(self.on_evaluation_finished)
        self.current_thread.start()

    def on_evaluation_finished(self, correcto: bool, mensaje: str, pregunta: str, respuesta: str):
        self.current_thread = None
        es_error = mensaje.startswith("ERROR")

        try:
            with open(self.ruta, "a", encoding="utf-8") as f:
                n = self.current_index + 1
                if es_error:
                    f.write(
                        f"Pregunta {n}: {pregunta}\n"
                        f"Respuesta: {respuesta}\n"
                        f"Resultado: ERROR (no evaluado)\n"
                        f"Detalle: {mensaje}\n\n"
                    )
                else:
                    f.write(
                        f"Pregunta {n}: {pregunta}\n"
                        f"Respuesta: {respuesta}\n"
                        f"Resultado: {'Correcto' if correcto else 'Incorrecto'}\n\n"
                    )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error al escribir detalle",
                f"No se pudo guardar la respuesta:\n{e}",
            )

        if not es_error and mensaje == "si" and correcto:
            self.score += 1

        self.current_index += 1
        self.show_next_question()

    def show_final_score(self):
        # Guardar resumen final EN EL MISMO ARCHIVO del DNI
        try:
            with open(self.ruta, "a", encoding="utf-8") as f:
                f.write("=====================================\n")
                f.write("Resumen Final\n")
                f.write(f"Puntaje: {self.score}/{self.num_preguntas}\n")
                f.write("=====================================\n\n")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error final",
                f"No se pudo guardar el resumen final:\n{e}",
            )

        # Mostrar vista final
        final_view = FinalScoreView(self.score, self.num_preguntas, self.close)
        self.stack.addWidget(final_view)
        self.stack.setCurrentWidget(final_view)


# ============================
#  MAIN
# ============================

def main():
    try:
        preguntas = cargar_preguntas_desde_json(RUTA_PREGUNTAS_JSON)
    except Exception as e:
        print(f"Error al cargar preguntas: {e}")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MainWindow(preguntas)
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()