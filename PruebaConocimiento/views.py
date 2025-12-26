from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTextEdit, QHBoxLayout, QFrame, QSizePolicy,
    QLineEdit
)


def crear_card(parent: QWidget) -> QFrame:
    """
    Crea un QFrame tipo 'card' con fondo blanco y bordes redondeados,
    centrado dentro del layout del parent.
    """
    root_layout = QVBoxLayout(parent)
    root_layout.setContentsMargins(160, 80, 160, 80)
    root_layout.setSpacing(0)
    root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    card = QFrame()
    card.setObjectName("card")
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    root_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

    card.setStyleSheet("""
        QFrame#card {
            background-color: #ffffff;
            border-radius: 18px;
        }
    """)
    return card


class WelcomeView(QWidget):
    def __init__(self, on_start_callback, parent=None):
        super().__init__(parent)

        self.setStyleSheet("""
            QWidget#WelcomeRoot {
                background-color: #0f172a;
                font-family: 'Segoe UI', Arial;
            }
        """)
        self.setObjectName("WelcomeRoot")

        card = crear_card(self)
        card.setFixedWidth(1080)
        card.setFixedHeight(720)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(60, 40, 60, 40)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Prueba de conocimientos en Inteligencia Artificial")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 50pt; font-weight: 700; color: #111827;")

        subtitle = QLabel("Actividad de evaluación de conceptos")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 30pt; color: #6b7280;")

        desc = QLabel(
            "Responde 6 preguntas sobre conceptos de IA.\n"
            "Escribe con tus propias palabras. Al finalizar verás el siguiente paso."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 20pt; color: #111827;")

        btn = QPushButton("Continuar")
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
        card_layout.addSpacing(40)
        card_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)


class DniView(QWidget):
    """
    Vista para ingresar el número de DNI antes de iniciar el test.
    on_start_callback(dni: str)
    """
    def __init__(self, on_start_callback, parent=None):
        super().__init__(parent)
        self.on_start_callback = on_start_callback

        self.setObjectName("DniRoot")
        self.setStyleSheet("""
            QWidget#DniRoot {
                background-color: #0f172a;
                font-family: 'Segoe UI', Arial;
            }
        """)

        card = crear_card(self)
        card.setFixedWidth(800)
        card.setFixedHeight(500)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Datos del participante")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 40pt; font-weight: 700; color: #111827;")

        subtitle = QLabel("Ingrese su número de DNI para continuar.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 22pt; color: #4b5563;")

        self.txt_dni = QLineEdit()
        self.txt_dni.setPlaceholderText("Número de DNI")
        self.txt_dni.setMaxLength(12)
        self.txt_dni.setFixedHeight(70)
        self.txt_dni.setStyleSheet("""
            QLineEdit {
                font-size: 26pt;
                padding: 10px 16px;
                border-radius: 14px;
                border: 2px solid #d1d5db;
                background-color: #f9fafb;
            }
        """)

        btn = QPushButton("Comenzar el test")
        btn.setFixedHeight(70)
        btn.setFixedWidth(320)
        btn.setStyleSheet("""
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
        btn.clicked.connect(self._on_start_clicked)

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(self.txt_dni)
        layout.addSpacing(30)
        layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)

    def _on_start_clicked(self):
        dni = self.txt_dni.text().strip()
        if not dni:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "DNI vacío",
                "Por favor, ingrese su número de DNI para continuar."
            )
            return
        self.on_start_callback(dni)


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
            from PyQt6.QtWidgets import QMessageBox
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
        """)

        card = crear_card(self)
        card.setFixedWidth(800)
        card.setFixedHeight(500)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Lógica de mensaje según puntaje:
        # score >= 4 -> Gracias por su participación
        # score < 4  -> Continuemos con la siguiente intervención. Llame al investigador/a.
        if score >= 4:
            message = "Fin de la experimentación"
        else:
            message = "Continuemos con la siguiente experimentación"

        lbl_title = QLabel(message)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 40pt; font-weight: 700; color: #111827;")
        lbl_title.setWordWrap(True)

        lbl_message = QLabel("Llame al investigador/a")
        lbl_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_message.setWordWrap(True)
        lbl_message.setStyleSheet("font-size: 24pt; color: #6b7280;")

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
        layout.addWidget(lbl_message)
        layout.addSpacing(35)
        layout.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignCenter)
