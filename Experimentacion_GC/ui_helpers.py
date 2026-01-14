from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QFontMetrics, QGuiApplication
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QWidget,
    QFrame,
    QMessageBox,
)

from config import (
    FG1, FG2, PRIMARY,
    LEFT_BG, RIGHT_BG, LEFT_FG, RIGHT_FG,
    APP_BG,
)


def scaled_pixmap(
    path: str,
    width: int,
    height: int,
    aspect: Qt.AspectRatioMode = Qt.AspectRatioMode.KeepAspectRatio,
    transform: Qt.TransformationMode = Qt.TransformationMode.SmoothTransformation,
) -> QPixmap:
    pix = QPixmap(path)
    if pix.isNull():
        return pix
    screen = QGuiApplication.primaryScreen()
    dpr = screen.devicePixelRatio() if screen else 1.0
    target_w = max(1, int(width * dpr))
    target_h = max(1, int(height * dpr))
    pix = pix.scaled(target_w, target_h, aspect, transform)
    pix.setDevicePixelRatio(dpr)
    return pix


def make_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{FG1};")
    lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    lbl.setWordWrap(True)
    lbl.setFont(QFont("Arial", 22, QFont.Weight.Bold))
    return lbl


def make_body(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{FG2};")
    lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    lbl.setWordWrap(True)
    lbl.setFont(QFont("Arial", 14))
    return lbl


def make_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    # Tamaño estándar para todos los botones creados con este helper
    b.setFixedWidth(400)
    b.setFixedHeight(70)
    b.setStyleSheet(f"""
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
        QPushButton:disabled {{
            background:#334155;
            color:#9aa6b2;
        }}
    """)
    return b

def show_info(parent: QWidget, title: str, text: str) -> None:
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Information)

    # Forzar fondo blanco en absolutamente todos los widgets internos
    msg.setStyleSheet("""
        QMessageBox {
            background: white;
        }
        QMessageBox QLabel {
            background: white;
            color: black;
            font: 22pt "Arial";
        }
        QMessageBox QWidget {
            background: white;
        }
        QPushButton {
            background-color: #d1d5db;
            color: black;
            padding: 10px 24px;
            border-radius: 8px;
            font: 16pt "Arial";
        }
        QPushButton:hover {
            background-color: #9ca3af;
        }
    """)

    msg.exec()

class Bubble(QWidget):
    """Globo de chat (solo el globo)"""

    def __init__(self, text: str, left: bool = True,
                 bg: str = LEFT_BG, fg: str = LEFT_FG, parent=None):
        super().__init__(parent)
        self.left = left

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.box = QFrame()
        self.box.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border-radius: 16px;
                padding: 4px 3px;
            }}
            QLabel {{
                color: {fg};
                font: 18pt "Arial";
            }}
        """)
        self.box.setSizePolicy(
            QSizePolicy.Policy.Maximum,
            QSizePolicy.Policy.Preferred
        )

        vbox = QVBoxLayout(self.box)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(0)

        self.lbl = QLabel(text)
        self.lbl.setWordWrap(True)
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.lbl.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.lbl.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred
        )

        vbox.addWidget(self.lbl)

        if left:
            layout.addWidget(self.box, 0, Qt.AlignmentFlag.AlignLeft)
        else:
            layout.addWidget(self.box, 0, Qt.AlignmentFlag.AlignRight)

        QTimer.singleShot(0, self._recalc_height)

    def _recalc_height(self):
        """Ajusta la altura del bubble en función del texto."""
        container = self.window() or self.parentWidget()
        if container:
            max_width = int(container.width() * 0.55)
            fm = QFontMetrics(self.lbl.font())
            lines = self.lbl.text().splitlines() or [""]
            longest = max(fm.horizontalAdvance(line) for line in lines)
            padding = 32  # margen interno + padding del layout
            desired = min(max_width, longest + padding)
            label_width = max(1, desired - padding)
            for w in (self.lbl, self.box, self):
                w.setMinimumWidth(desired)
                w.setMaximumWidth(desired)
            self.lbl.setMinimumWidth(label_width)
            self.lbl.setMaximumWidth(label_width)

        self.lbl.adjustSize()
        h = self.lbl.sizeHint().height() + 25
        self.setFixedHeight(h)

    def resizeEvent(self, event):
        self._recalc_height()
        return super().resizeEvent(event)


class ChatMessageRow(QWidget):
    """Fila completa: avatar + nombre debajo + burbuja"""

    def __init__(self, author: str, text: str, left: bool,
                 avatar_path: str, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        avatar_col = QVBoxLayout()
        avatar_col.setContentsMargins(0, 0, 0, 0)
        avatar_col.setSpacing(2)

        avatar_lbl = QLabel()
        avatar_lbl.setFixedSize(105, 105)
        pix = scaled_pixmap(
            avatar_path,
            105,
            105,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        )
        if not pix.isNull():
            avatar_lbl.setPixmap(pix)
        avatar_lbl.setStyleSheet("""
            QLabel {
                border-radius: 39px;
                background-color: transparent;
            }
        """)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_lbl = QLabel(author)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        name_lbl.setStyleSheet(
            "color:#cbd5e1; font: 15pt 'Arial'; font-weight: bold;"
        )

        avatar_col.addWidget(avatar_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        avatar_col.addWidget(name_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

        bg, fg = (LEFT_BG, LEFT_FG) if left else (RIGHT_BG, RIGHT_FG)
        bubble = Bubble(text, left=left, bg=bg, fg=fg, parent=self)

        if left:
            layout.addLayout(avatar_col, 0)
            layout.setAlignment(avatar_col, Qt.AlignmentFlag.AlignTop)
            layout.addWidget(bubble, 1)
            layout.addStretch()
        else:
            layout.addStretch()
            layout.addWidget(bubble, 1)
            layout.addLayout(avatar_col, 0)
            layout.setAlignment(avatar_col, Qt.AlignmentFlag.AlignTop)
