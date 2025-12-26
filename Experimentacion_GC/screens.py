from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIntValidator, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QFrame, QProgressBar,
    QSizePolicy, QLineEdit, QApplication
)

from config import (
    APP_BG, FG1, FG2, PRIMARY,
    PROFESOR, PEPITO,
    PROFESORA_AVATAR, PEPITO_AVATAR,
    PROFESORA, ALUMNO,
)
from ui_helpers import make_title, make_body, make_btn, ChatMessageRow, show_info

# tiempo por mensaje
PROF_DELAY_MS = 12_000   
PEPITO_DELAY_MS = 4_000 


# =============== PANTALLAS ===============
class Presentacion(QWidget):
    go = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(32)

        title = QLabel("🧠 Bienvenid@")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet(f"color:{FG1};")
        title.setFont(QFont("Arial", 70, QFont.Weight.Bold))
        main.addWidget(title)

        b = QPushButton("Comenzar")
        b.setFixedWidth(240)
        b.setFixedHeight(60)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{
                background:{PRIMARY};
                color:white;
                font: 25pt "Arial";
                padding: 14px 24px;
                border-radius:12px;
                font-weight:600;
            }}
            QPushButton:hover {{
                background:#1d4ed8;
            }}
        """)
        b.clicked.connect(self.go.emit)
        main.addWidget(b, 0, Qt.AlignmentFlag.AlignHCenter)


class DatosParticipante(QWidget):
    submitted = pyqtSignal(str, str)  # (num_sujeto, nombre)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(10)

        center_box = QVBoxLayout()
        center_box.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        center_box.setSpacing(10)

        titulo = QLabel("Datos del participante")
        titulo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        titulo.setStyleSheet(f"color:{FG1};")
        titulo.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        center_box.addWidget(titulo)

        center_box.addSpacing(45)

        lbl_num = QLabel("Ingrese su número de DNI:")
        lbl_num.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_num.setStyleSheet(f"color:{FG1};")
        lbl_num.setFont(QFont("Arial", 18))
        center_box.addWidget(lbl_num)

        self.txt_num = QLineEdit()
        self.txt_num.setMaxLength(8)
        self.txt_num.setInputMask("99999999")
        self.txt_num.setFixedWidth(360)
        self.txt_num.setFixedHeight(42)
        self.txt_num.setStyleSheet("""
            QLineEdit {
                background:#0b1220;
                color:#e5e7eb;
                border:1px solid #1e293b;
                border-radius:10px;
                padding:10px 12px;
                font: 16pt "Arial";
            }
        """)
        center_box.addWidget(self.txt_num, 0, Qt.AlignmentFlag.AlignHCenter)

        center_box.addSpacing(25)

        lbl_nom = QLabel("Tu nombre:")
        lbl_nom.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lbl_nom.setStyleSheet(f"color:{FG1};")
        lbl_nom.setFont(QFont("Arial", 18))
        center_box.addWidget(lbl_nom)

        self.txt_nom = QLineEdit()
        self.txt_nom.setFixedWidth(360)
        self.txt_nom.setFixedHeight(42)
        self.txt_nom.setStyleSheet("""
            QLineEdit {
                background:#0b1220;
                color:#e5e7eb;
                border:1px solid #1e293b;
                border-radius:10px;
                padding:10px 12px;
                font: 16pt "Arial";
            }
        """)
        center_box.addWidget(self.txt_nom, 0, Qt.AlignmentFlag.AlignHCenter)

        center_box.addSpacing(40)

        btn = make_btn("Continuar")
        btn.clicked.connect(self._enviar)
        center_box.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)

        main.addLayout(center_box)

    def _enviar(self):
        num = self.txt_num.text().strip()
        nom = self.txt_nom.text().strip()

        if not num or not nom:
            # <<< AVISO >>>
            show_info(self, "Aviso", "Completa el número de sujeto y tu nombre.")
            return

        self.submitted.emit(num, nom)

class BienvenidaParticipante(QWidget):
    cont = pyqtSignal()   # señal para continuar

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        self.text_template = (
            "Hola, [participante]. Bienvenido a la sesión de hoy. "
            "Estamos muy contentos de tenerte aquí. En esta actividad vamos a explorar juntos "
            "algunos conceptos fundamentales sobre inteligencia artificial. Para ello, cuento con la ayuda "
            "de mi compañero Pepito, quien también estará participando en esta sesión. Ambos estaremos aquí "
            "para acompañarte, guiarte y responder a tus preguntas durante todo el proceso. "
            "Esperamos que disfrutes la experiencia y que aprendas mucho. Así que, comencemos."
        )

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setContentsMargins(60, 40, 60, 40)
        main.setSpacing(30)

        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(320, 320)
        pix = QPixmap(PROFESORA)
        if not pix.isNull():
            pix = pix.scaled(
                320, 320,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.img_lbl.setPixmap(pix)
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.img_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

        # Texto de bienvenida
        self.lbl_texto = QLabel(self.text_template)
        self.lbl_texto.setStyleSheet(f"color:{FG1};")
        self.lbl_texto.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.lbl_texto.setWordWrap(True)
        self.lbl_texto.setFont(QFont("Arial", 24))
        self.lbl_texto.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        main.addWidget(self.lbl_texto, 0, Qt.AlignmentFlag.AlignHCenter)
        main.setSpacing(40)

        # Botón continuar
        self.btn = make_btn("Continuar")
        self.btn.clicked.connect(self.cont.emit)
        main.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignHCenter)

        QTimer.singleShot(0, self._update_label_width)

    def set_participant_name(self, nombre: str):
        texto = self.text_template.replace("[participante]", nombre)
        self.lbl_texto.setText(texto)

    def _update_label_width(self):
        w = int(self.width() * 0.75)
        if w > 0:
            self.lbl_texto.setMinimumWidth(w)
            self.lbl_texto.setMaximumWidth(w)

    def resizeEvent(self, event):
        self._update_label_width()
        return super().resizeEvent(event)


class TemaView(QWidget):
    done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(12)

        self.lbl_tema = QLabel("")
        self.lbl_tema.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.lbl_tema.setStyleSheet(f"color:{FG1};")
        self.lbl_tema.setFont(QFont("Arial", 70, QFont.Weight.Bold))

        self.lbl_titulo = QLabel("")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.lbl_titulo.setStyleSheet(f"color:{FG1};")
        self.lbl_titulo.setFont(QFont("Arial", 58, QFont.Weight.Bold))

        main.addWidget(self.lbl_tema)
        main.addWidget(self.lbl_titulo)

    def mostrar_tema(self, numero: int, titulo: str):
        self.lbl_tema.setText(f"Tema {numero}:")
        self.lbl_titulo.setText(titulo)
        QTimer.singleShot(4000, self.done.emit)


class ChatLeccion(QWidget):
    done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = make_title("Observación")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet(f"color:{FG1};")
        title.setFont(QFont("Arial", 58, QFont.Weight.Bold))
        root.addWidget(title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"background:{APP_BG}; border:none;")
        root.addWidget(self.scroll)

        self.content = QWidget()
        self.content.setStyleSheet(f"background:{APP_BG};")
        self.v = QVBoxLayout(self.content)
        self.v.setContentsMargins(8, 8, 8, 8)
        self.v.setSpacing(4)
        self.v.addStretch(1)

        self.scroll.setWidget(self.content)

        self.btn_next = QPushButton("Siguiente ➜")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setFixedWidth(360)
        self.btn_next.setFixedHeight(70)
        self.btn_next.setStyleSheet(f"""
            QPushButton {{
                background:{PRIMARY};
                color:white;
                border:none;
                padding:14px 24px;
                border-radius:12px;
                font: 25pt "Arial";
                font-weight:600;
            }}
            QPushButton:hover {{
                background:#1d4ed8;
            }}
        """)
        self.btn_next.clicked.connect(self.done.emit)
        self.btn_next.hide()
        root.addWidget(self.btn_next, 0, Qt.AlignmentFlag.AlignHCenter)

    def clear(self):
        while self.v.count() > 1:
            item = self.v.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def add_msg(self, author: str, text: str, left: bool):
        avatar = PROFESORA_AVATAR if author == PROFESOR else PEPITO_AVATAR
        row = ChatMessageRow(author, text, left, avatar, parent=self.content)
        self.v.insertWidget(self.v.count()-1, row, 0)

        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def start_sequence(self, concepto: dict):
        self.clear()
        self.btn_next.hide()  # botón Siguiente oculto al inicio

        obs = concepto["parte_observacion"]
        pasos = [
            (PROFESOR, obs["profesor_explica"], True),
            (PEPITO,   obs["alumno_respuesta_parcialmente_incorrecta"], False),
            (PROFESOR, obs["profesor_corrige"], True),
            (PEPITO,   obs["alumno_ejemplo_correcto"], False),
            (PROFESOR, obs["profesor_valida"], True),
        ]

        t = 0  # tiempo acumulado

        for author, text, left in pasos:
            QTimer.singleShot(
                t,
                lambda a=author, tx=text, l=left: self.add_msg(a, tx, l)
            )

            # delay según quién habla
            if author == PROFESOR:
                t += PROF_DELAY_MS
            else:
                t += PEPITO_DELAY_MS

        QTimer.singleShot(t + 300, self.btn_next.show)

class TurnoParticipante(QWidget):
    cont = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(20)

        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(320, 320)

        pix = QPixmap(PROFESORA)
        if not pix.isNull():
            pix = pix.scaled(
                320, 320,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.img_lbl.setPixmap(pix)
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main.addWidget(self.img_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

        self.title = QLabel("Ahora es tu turno.")
        self.title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.title.setStyleSheet(f"color:{FG1};")
        self.title.setWordWrap(True)
        self.title.setFont(QFont("Arial", 65, QFont.Weight.Bold))
        main.addWidget(self.title, 0, Qt.AlignmentFlag.AlignHCenter)

    def set_participant_name(self, nombre: str):
        self.title.setText(f"Ahora es tu turno, {nombre}.")


class PreguntaView(QWidget):
    send = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(35)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pregunta_box = QHBoxLayout()
        pregunta_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_preg = QLabel("")
        self.lbl_preg.setWordWrap(True)
        self.lbl_preg.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.lbl_preg.setStyleSheet(f"color:{FG1};")
        self.lbl_preg.setFont(QFont("Arial", 58, QFont.Weight.Bold))
        self.lbl_preg.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        main.setSpacing(20)

        pregunta_box.addWidget(self.lbl_preg)
        main.addLayout(pregunta_box)

        from PyQt6.QtWidgets import QTextEdit
        self.txt = QTextEdit()
        self.txt.setPlaceholderText("Escribe tu respuesta con tus propias palabras...")
        self.txt.setFixedHeight(200)
        self.txt.setFixedWidth(1000)
        self.txt.setStyleSheet("""
            QTextEdit {
                background:#ffffff;
                color:#000000;
                border:none;
                padding:20px;
                font: 28pt "Arial";
                border-radius:12px;
            }
        """)
        self.txt.setAlignment(Qt.AlignmentFlag.AlignLeft)

        main.setSpacing(50)

        self.btn = make_btn("Enviar respuesta")
        self.btn.clicked.connect(self._enviar)

        main.addWidget(self.txt, 0, Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignCenter)

        QTimer.singleShot(0, self._update_label_width)

    def _update_label_width(self):
        w = int(self.width() * 0.70)
        if w > 0:
            self.lbl_preg.setMinimumWidth(w)
            self.lbl_preg.setMaximumWidth(w)

    def resizeEvent(self, event):
        self._update_label_width()
        return super().resizeEvent(event)

    def set_question(self, texto: str):
        self.lbl_preg.setText(texto)
        self.txt.clear()
        self.txt.setFocus()

    def _enviar(self):
        texto = self.txt.toPlainText().strip()
        if not texto:
            # <<< AVISO CON TEXTO VISIBLE >>>
            show_info(self, "Aviso", "Por favor, escribe una respuesta.")
            return
        self.send.emit(texto)
class ProcesandoView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(20)

        self.titulo = make_title("⚙️ Evaluando tu respuesta…")
        self.titulo.setFont(QFont("Arial", 60, QFont.Weight.Bold))
        self.titulo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        main.addWidget(self.titulo, 0, Qt.AlignmentFlag.AlignHCenter)

        self.sub = make_body("Esto tomará un momento.")
        self.sub.setFont(QFont("Arial", 40))
        self.sub.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        main.addWidget(self.sub, 0, Qt.AlignmentFlag.AlignHCenter)

        bar_container = QHBoxLayout()
        bar_container.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.bar = QProgressBar()
        self.bar.setRange(0, 0)
        self.bar.setFixedWidth(600)
        self.bar.setStyleSheet("""
            QProgressBar {
                background:#0b1220;
                border:1px solid #0b1220;
                border-radius:12px;
                height:28px;
            }
            QProgressBar::chunk {
                background:#3b82f6;
                border-radius:12px;
            }
        """)

        bar_container.addWidget(self.bar)
        main.addLayout(bar_container)

        QTimer.singleShot(0, self._update_label_width)

    def _update_label_width(self):
        w = int(self.width() * 0.8)
        if w > 0:
            for lbl in (self.titulo, self.sub):
                lbl.setMinimumWidth(w)
                lbl.setMaximumWidth(w)

    def resizeEvent(self, event):
        self._update_label_width()
        return super().resizeEvent(event)


class FeedbackView(QWidget):
    next = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(24)

        # CABECERA: "Resultado" + icono ✅ / ❌
        self.t = make_title("Resultado")
        self.t.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.t.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )

        self.estado = QLabel("")  # aquí va ✅ o ❌
        self.estado.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.estado.setStyleSheet("color:#ffffff; font: 40pt 'Arial';")
        self.estado.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )

        header = QHBoxLayout()
        header.setSpacing(12)
        header.addStretch(1)
        header.addWidget(self.t, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.estado, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addStretch(1)

        main.addLayout(header)

        # FEEDBACK
        self.fb = make_body("")
        self.fb.setFont(QFont("Arial", 28))
        main.addWidget(self.fb, 0, Qt.AlignmentFlag.AlignHCenter)

        # BOTÓN
        main.setSpacing(50)
        self.btn = make_btn("Siguiente concepto ➜")
        self.btn.clicked.connect(self.next.emit)
        main.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignHCenter)

        QTimer.singleShot(0, self._update_label_widths)

    def set_result(self, res: dict):
        ok = res.get("correct")
        self.estado.setText("✅" if ok else "❌")
        self.fb.setText("")

    def show_final(self, texto: str, positivo: bool,
                   btn_text: str = "Siguiente concepto ➜"):
        self.t.setText("Resultado")
        self.estado.setText("✅" if positivo else "❌")
        self.fb.setText(texto)
        self.btn.setText(btn_text)

    def _update_label_widths(self):
        w = int(self.width() * 0.80)
        if w > 0:
            self.fb.setMinimumWidth(w)
            self.fb.setMaximumWidth(w)

    def resizeEvent(self, event):
        self._update_label_widths()
        return super().resizeEvent(event)


class HintView(QWidget):
    """Ventana de pista / respuesta modelo con botón para continuar a responder."""
    proceed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(30)

        self.img = QLabel()
        self.img.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.img.setFixedSize(320, 320)
        pix = QPixmap(ALUMNO)
        if not pix.isNull():
            pix = pix.scaled(
                320, 320,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.img.setPixmap(pix)
        main.addWidget(self.img, 0, Qt.AlignmentFlag.AlignHCenter)

        self.body = make_body("")
        self.body.setFont(QFont("Arial", 32))
        main.addWidget(self.body, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btn = make_btn("Responder ahora")
        self.btn.clicked.connect(self.proceed.emit)
        main.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignHCenter)

        QTimer.singleShot(0, self._update_label_widths)

    def set_text(self, texto: str):
        self.body.setText(texto)

    def _update_label_widths(self):
        w = int(self.width() * 0.80)
        if w > 0:
            self.body.setMinimumWidth(w)
            self.body.setMaximumWidth(w)

    def resizeEvent(self, event):
        self._update_label_widths()
        return super().resizeEvent(event)


class PaseConceptoView(QWidget):
    """Ventana para mensaje de 'pase a otro concepto'."""
    cont = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(30)

        self.title = make_title("Continuemos")
        self.title.setFont(QFont("Arial", 50, QFont.Weight.Bold))
        main.addWidget(self.title, 0, Qt.AlignmentFlag.AlignHCenter)

        self.body = make_body("")
        self.body.setFont(QFont("Arial", 32))
        main.addWidget(self.body, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btn = make_btn("Siguiente concepto ➜")
        self.btn.clicked.connect(self.cont.emit)
        main.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignHCenter)

        QTimer.singleShot(0, self._update_label_widths)

    def set_text(self, texto: str):
        self.body.setText(texto)

    def _update_label_widths(self):
        w = int(self.width() * 0.80)
        if w > 0:
            self.body.setMinimumWidth(w)
            self.body.setMaximumWidth(w)

    def resizeEvent(self, event):
        self._update_label_widths()
        return super().resizeEvent(event)


class FinView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        self.text_template = (
            "Hemos llegado al final de la sesión de hoy. Gracias por tu tiempo, tu atención y tu participación, "
            "[participante]. Esperamos que los conceptos que revisamos te hayan resultado claros y útiles, y que "
            "esta experiencia haya sido tan enriquecedora para ti como lo fue para nosotros. Si tienes preguntas "
            "o quieres seguir aprendiendo, estaremos encantados de ayudarte en futuras sesiones. Hasta pronto, "
            "[participante], y que tengas un excelente día."
        )

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(30)

        self.title = make_title("🎉 ¡Has terminado todos los conceptos!")
        self.title.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main.addWidget(self.title, 0, Qt.AlignmentFlag.AlignHCenter)

        self.body = make_body(self.text_template)
        self.body.setFont(QFont("Arial", 25))
        self.body.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main.addWidget(self.body, 0, Qt.AlignmentFlag.AlignHCenter)

        main.addSpacing(40)

        self.btn_close = QPushButton("CERRAR")
        self.btn_close.setFixedWidth(360)
        self.btn_close.setFixedHeight(70)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background:#dc2626;
                color:white;
                border:none;
                padding:14px 24px;
                border-radius:14px;
                font: 30pt "Arial";
                font-weight:600;
            }
            QPushButton:hover {
                background:#b91c1c;
            }
        """)
        self.btn_close.clicked.connect(self._cerrar_app)
        main.addWidget(self.btn_close, 0, Qt.AlignmentFlag.AlignHCenter)

        QTimer.singleShot(0, self._update_label_widths)

    def set_participant_name(self, nombre: str):
        texto = self.text_template.replace("[participante]", nombre)
        self.body.setText(texto)

    def _update_label_widths(self):
        w = int(self.width() * 0.80)
        if w > 0:
            for lbl in (self.title, self.body):
                lbl.setMinimumWidth(w)
                lbl.setMaximumWidth(w)

    def resizeEvent(self, event):
        self._update_label_widths()
        return super().resizeEvent(event)

    def _cerrar_app(self):
        app = QApplication.instance()
        if app is not None:
            app.quit()

