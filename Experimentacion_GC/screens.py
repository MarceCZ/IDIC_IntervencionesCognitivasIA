from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIntValidator
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QFrame, QProgressBar,
    QSizePolicy, QLineEdit, QApplication
)

from config import (
    APP_BG, FG1, FG2, PRIMARY,
    PROFESOR, PEPITO,
    PROFESORA_AVATAR, ALUMNO_AVATAR,
    PROFESORA, ALUMNO, BIENVENIDA,
    LEFT_BG, RIGHT_BG, LEFT_FG, RIGHT_FG,
)
from ui_helpers import (
    make_title,
    make_body,
    make_btn,
    show_info,
    scaled_pixmap,
)

# tiempo por mensaje
PROF_BASE_MS = 2_000
PROF_PER_CHAR_MS = 35
PROF_MAX_MS = 20_000

PEPITO_BASE_MS = 1_500
PEPITO_PER_CHAR_MS = 30
PEPITO_MAX_MS = 15_000
PEPITO_EXTRA_MS = 2_000

HINT_PER_CHAR_MS = 35
HINT_EXTRA_MS = 2_000
HINT_MAX_MS = 25_000


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
        self.txt_num.setValidator(QIntValidator(0, 99999999, self.txt_num))
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
            show_info(self, "Aviso", "Completa el nÇ§mero de sujeto y tu nombre.")
            return

        self.submitted.emit(num, nom)


class BienvenidaParticipante(QWidget):
    cont = pyqtSignal()   # seÇñal para continuar

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
        self.img_lbl.setFixedSize(520, 320)
        pix = scaled_pixmap(
            BIENVENIDA,
            520,
            320,
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        if not pix.isNull():
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

        # BotÇün continuar
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


class ConceptoView(QWidget):
    done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(12)

        self.lbl_concepto = QLabel("")
        self.lbl_concepto.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.lbl_concepto.setStyleSheet(f"color:{FG1};")
        self.lbl_concepto.setFont(QFont("Arial", 70, QFont.Weight.Bold))

        self.lbl_titulo = QLabel("")
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.lbl_titulo.setStyleSheet(f"color:{FG1};")
        self.lbl_titulo.setFont(QFont("Arial", 58, QFont.Weight.Bold))

        main.addWidget(self.lbl_concepto)
        main.addWidget(self.lbl_titulo)

    def mostrar_concepto(self, numero: int, titulo: str):
        self.lbl_concepto.setText(f"Concepto {numero}:")
        self.lbl_titulo.setText(titulo)
        QTimer.singleShot(4000, self.done.emit)


class ChatLeccion(QWidget):
    done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        self._token = 0
        self._pasos = []
        self._step_index = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(20)

        stage = QWidget()
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.setSpacing(0)
        stage_layout.addStretch(1)

        self.left_row = QWidget()
        left_layout = QHBoxLayout(self.left_row)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(24)

        self.left_avatar = QLabel()
        self.left_avatar.setFixedSize(300, 300)
        self.left_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.left_avatar, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        self.left_bubble = QFrame()
        self.left_bubble.setStyleSheet(f"""
            QFrame {{
                background:{LEFT_BG};
                border-radius:24px;
            }}
            QLabel {{
                color:{LEFT_FG};
                font: 28pt "Arial";
            }}
        """)
        left_bubble_layout = QVBoxLayout(self.left_bubble)
        left_bubble_layout.setContentsMargins(28, 20, 28, 20)
        left_bubble_layout.setSpacing(0)

        self.left_text = QLabel("")
        self.left_text.setWordWrap(True)
        self.left_text.setAlignment(Qt.AlignmentFlag.AlignJustify | Qt.AlignmentFlag.AlignTop)
        left_bubble_layout.addWidget(self.left_text)

        left_layout.addWidget(self.left_bubble, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        left_layout.addStretch(1)
        stage_layout.addWidget(self.left_row)

        self.right_row = QWidget()
        right_layout = QHBoxLayout(self.right_row)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(24)

        self.right_bubble = QFrame()
        self.right_bubble.setStyleSheet(f"""
            QFrame {{
                background:{RIGHT_BG};
                border-radius:24px;
            }}
            QLabel {{
                color:{RIGHT_FG};
                font: 28pt "Arial";
            }}
        """)
        right_bubble_layout = QVBoxLayout(self.right_bubble)
        right_bubble_layout.setContentsMargins(28, 20, 28, 20)
        right_bubble_layout.setSpacing(0)

        self.right_text = QLabel("")
        self.right_text.setWordWrap(True)
        self.right_text.setAlignment(Qt.AlignmentFlag.AlignJustify | Qt.AlignmentFlag.AlignTop)
        right_bubble_layout.addWidget(self.right_text)

        self.right_avatar = QLabel()
        self.right_avatar.setFixedSize(300, 300)
        self.right_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_layout.addStretch(1)
        right_layout.addWidget(self.right_bubble, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        right_layout.addWidget(self.right_avatar, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        stage_layout.addWidget(self.right_row)
        stage_layout.addStretch(1)

        root.addWidget(stage)

        self._clear_message()
        QTimer.singleShot(0, self._update_bubble_widths)

    def clear(self):
        self._clear_message()

    def add_msg(self, author: str, text: str, left: bool):
        self._show_message(author, text, left)

    def start_sequence(self, concepto: dict):
        self.clear()
        self._token += 1
        token = self._token

        obs = concepto["parte_observacion"]
        self._pasos = [
            (PROFESOR, obs["profesor_explica"], True),
            (PEPITO,   obs["alumno_respuesta_parcialmente_incorrecta"], False),
            (PROFESOR, obs["profesor_corrige"], True),
            (PEPITO,   obs["alumno_ejemplo_correcto"], False),
            (PROFESOR, obs["profesor_valida"], True),
        ]
        self._step_index = 0
        self._show_step(token)

    def _calc_delay_ms(self, author: str, text: str) -> int:
        text_len = len(text.strip())
        if author == PROFESOR:
            delay = PROF_BASE_MS + (text_len * PROF_PER_CHAR_MS)
            return min(delay, PROF_MAX_MS)
        delay = PEPITO_BASE_MS + (text_len * PEPITO_PER_CHAR_MS) + PEPITO_EXTRA_MS
        return min(delay, PEPITO_MAX_MS)

    def _show_step(self, token: int):
        if token != self._token:
            return
        if self._step_index >= len(self._pasos):
            self.done.emit()
            return

        author, text, left = self._pasos[self._step_index]
        self._step_index += 1
        self.add_msg(author, text, left)

        delay = self._calc_delay_ms(author, text)
        QTimer.singleShot(delay, lambda: self._hide_then_advance(token))

    def _hide_then_advance(self, token: int):
        if token != self._token:
            return
        self._clear_message()
        QTimer.singleShot(250, lambda: self._show_step(token))

    def _show_message(self, author: str, text: str, left: bool):
        if left:
            self.left_text.setText(text)
            pix = scaled_pixmap(
                PROFESORA_AVATAR,
                300,
                300,
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            if not pix.isNull():
                self.left_avatar.setPixmap(pix)
            self.left_row.show()
            self.right_row.hide()
        else:
            self.right_text.setText(text)
            pix = scaled_pixmap(
                ALUMNO_AVATAR,
                300,
                300,
                Qt.AspectRatioMode.KeepAspectRatio,
            )
            if not pix.isNull():
                self.right_avatar.setPixmap(pix)
            self.right_row.show()
            self.left_row.hide()
        self._update_bubble_widths()

    def _clear_message(self):
        self.left_row.hide()
        self.right_row.hide()
        self.left_text.setText("")
        self.right_text.setText("")

    def _update_bubble_widths(self):
        max_width = max(420, int(self.width() * 0.55))
        text_width = max(260, max_width - 56)
        for frame, label in (
            (self.left_bubble, self.left_text),
            (self.right_bubble, self.right_text),
        ):
            frame.setMinimumWidth(max_width)
            frame.setMaximumWidth(max_width)
            label.setMinimumWidth(text_width)
            label.setMaximumWidth(text_width)

    def resizeEvent(self, event):
        self._update_bubble_widths()
        return super().resizeEvent(event)


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
        self.img_lbl.setFixedSize(400, 400)

        pix = scaled_pixmap(
            PROFESORA,
            400,
            400,
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        if not pix.isNull():
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
    no_response = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        self._submitted = False
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(9500)
        self._idle_timer.timeout.connect(self._auto_send)

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
        self.txt.textChanged.connect(self._on_text_changed)

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
        self._submitted = False
        self.btn.setEnabled(True)
        self._start_idle_timer()

    def _enviar(self):
        if self._submitted:
            return
        texto = self.txt.toPlainText().strip()
        if not texto:
            # <<< AVISO CON TEXTO VISIBLE >>>
            show_info(self, "Aviso", "Por favor, escribe una respuesta.")
            return
        self._submitted = True
        self._idle_timer.stop()
        self.send.emit(texto)

    def _start_idle_timer(self):
        if self._submitted:
            return
        self._idle_timer.stop()
        self._idle_timer.start()

    def _on_text_changed(self):
        if self._submitted:
            return
        self._start_idle_timer()

    def _auto_send(self):
        if self._submitted:
            return
        self._submitted = True
        self.btn.setEnabled(False)
        texto = self.txt.toPlainText().strip()
        if texto:
            self.send.emit(texto)
        else:
            self.no_response.emit()


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
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(22)

        self.t = make_title("Resultado")
        self.t.setFont(QFont("Arial", 46, QFont.Weight.Bold))
        self.t.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )
        self.t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main.addWidget(self.t, 0, Qt.AlignmentFlag.AlignHCenter)

        self.estado = QLabel("")
        self.estado.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.estado.setStyleSheet("color:#ffffff; font: 80pt 'Arial';")
        self.estado.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
        main.addWidget(self.estado, 0, Qt.AlignmentFlag.AlignHCenter)

        self.fb = make_body("")
        self.fb.setFont(QFont("Arial", 28))
        self.fb.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main.addWidget(self.fb, 0, Qt.AlignmentFlag.AlignHCenter)

        QTimer.singleShot(0, self._update_label_widths)

    def show_final(self, texto: str, positivo: bool):
        self.t.setText("Resultado")
        self.estado.setText("✅" if positivo else "❌")
        self.fb.setText(texto)

    def _update_label_widths(self):
        w = int(self.width() * 0.80)
        if w > 0:
            self.fb.setMinimumWidth(w)
            self.fb.setMaximumWidth(w)

    def resizeEvent(self, event):
        self._update_label_widths()
        return super().resizeEvent(event)


class HintView(QWidget):
    """Ventana de pista / respuesta modelo con botİn para continuar a responder."""
    proceed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        self._token = 0
        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(30)

        self.img = QLabel()
        self.img.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.img.setFixedSize(400, 400)
        pix = scaled_pixmap(
            ALUMNO,
            400,
            400,
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        if not pix.isNull():
            self.img.setPixmap(pix)
        main.addWidget(self.img, 0, Qt.AlignmentFlag.AlignHCenter)

        self.body = make_body("")
        self.body.setFont(QFont("Arial", 32))
        main.addWidget(self.body, 0, Qt.AlignmentFlag.AlignHCenter)

        self.btn = make_btn("Responder ahora")
        self.btn.clicked.connect(self.proceed.emit)
        self.btn.setVisible(False)
        main.addWidget(self.btn, 0, Qt.AlignmentFlag.AlignHCenter)

        QTimer.singleShot(0, self._update_label_widths)

    def set_text(self, texto: str):
        self.body.setText(texto)
        self._token += 1
        token = self._token
        delay = self._calc_hint_delay_ms(texto)
        QTimer.singleShot(delay, lambda: self._auto_proceed(token))

    def _auto_proceed(self, token: int):
        if token != self._token:
            return
        self.proceed.emit()

    def _calc_hint_delay_ms(self, texto: str) -> int:
        text_len = len(texto.strip())
        delay = (text_len * HINT_PER_CHAR_MS) + HINT_EXTRA_MS
        return min(delay, HINT_MAX_MS)

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

        self.btn = make_btn("Siguiente concepto ƒzo")
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


class DescansoView(QWidget):
    cont = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background:{APP_BG};")
        self._token = 0

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.setSpacing(28)

        self.img = QLabel()
        self.img.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.img.setFixedSize(400, 400)
        pix = scaled_pixmap(
            PROFESORA_AVATAR,
            400,
            400,
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        if not pix.isNull():
            self.img.setPixmap(pix)
        main.addWidget(self.img, 0, Qt.AlignmentFlag.AlignHCenter)

        self.title = make_title("Breve descanso")
        self.title.setFont(QFont("Arial", 60, QFont.Weight.Bold))
        self.title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main.addWidget(self.title, 0, Qt.AlignmentFlag.AlignHCenter)

        self.body = make_body("")
        self.body.setFont(QFont("Arial", 30))
        self.body.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.body.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred
        )
        main.addWidget(self.body, 0, Qt.AlignmentFlag.AlignHCenter)

        main.addSpacing(30)

        duration_container = QWidget()
        duration_row = QHBoxLayout(duration_container)
        duration_row.setContentsMargins(0, 0, 0, 0)
        duration_row.setSpacing(10)

        self.duration_icon = QLabel("⏳")
        self.duration_icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.duration_icon.setStyleSheet(f"color:{FG2};")
        self.duration_icon.setFont(QFont("Arial", 30))
        duration_row.addWidget(self.duration_icon)

        self.duration = make_body("")
        self.duration.setFont(QFont("Arial", 34))
        self.duration.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.duration.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )
        self.duration.setWordWrap(False)
        duration_row.addWidget(self.duration)

        duration_container.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )
        main.addWidget(duration_container, 0, Qt.AlignmentFlag.AlignHCenter)

        QTimer.singleShot(0, self._update_label_widths)

    def set_info(self, title: str, duration_secs: int, btn_text: str):
        self._token += 1
        token = self._token
        self.title.setText(title)
        if title == "Breve descanso":
            self.body.setText("Tómate un momento para pensar en el concepto que acabas de aprender.")
        else:
            self.body.setText("Intenta relajar tu cuerpo y tu mente.")
        show_duration = title != "Breve descanso"
        self.duration_icon.setVisible(show_duration)
        self.duration.setVisible(show_duration)
        self.duration.setText(self._format_duration(duration_secs))

        QTimer.singleShot(duration_secs * 1000, lambda: self._auto_advance(token))

    def _auto_advance(self, token: int):
        if token != self._token:
            return
        self.cont.emit()

    def _format_duration(self, duration_secs: int) -> str:
        if duration_secs >= 60 and duration_secs % 60 == 0:
            minutes = duration_secs // 60
            label = "minuto" if minutes == 1 else "minutos"
            return f"Duración: {minutes} {label}"
        if duration_secs == 1:
            return "Duración: 1 segundo"
        return f"Duración: {duration_secs} segundos"

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
           "Hemos llegado al final de la sesión de hoy. Gracias por tu tiempo, tu atención y tu participación, [participante]. Esperamos que los conceptos que revisamos te hayan resultado claros y útiles, y que esta experiencia haya sido tan enriquecedora para ti como lo fue para nosotros. Hasta pronto, [participante], y que tengas un excelente día."
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
