"""
Digit Span Task - Versión 2.0 con PyQt6
Tarea de Amplitud de Dígitos con diseño moderno y responsive
"""

import sys
import random
import time
import csv
import os
from datetime import datetime
from typing import List

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QFrame,
    QGridLayout, QLineEdit, QSizePolicy
)

# =============== CONFIGURACIÓN DE COLORES ===============
APP_BG = "#0f172a"      # Fondo oscuro principal
CARD_BG = "#ffffff"     # Fondo de cards (blanco)
PRIMARY = "#2563eb"     # Azul primario para botones
PRIMARY_HOVER = "#1d4ed8"  # Azul más oscuro para hover
TEXT_DARK = "#111827"   # Texto oscuro en cards
TEXT_LIGHT = "#e5e7eb"  # Texto claro en fondo oscuro
TEXT_GRAY = "#6b7280"   # Texto gris secundario
SUCCESS = "#10b981"     # Verde para correcto
ERROR = "#ef4444"       # Rojo para error


class DigitSpanTask(QWidget):
    def __init__(self):
        super().__init__()
        
        # Variables de la tarea
        self.participant_id = ""
        self.span_levels = [2, 2, 3, 4, 5, 6, 7, 8]
        self.level_index = 0
        self.current_span = self.span_levels[self.level_index]
        self.span_counter = 0  # Contador de intentos (máximo 2)
        self.span_correct = 0  # Si acertó al menos 1 de los 2 intentos
        self.best_span = 1
        self.digit_span = 0
        
        # Datos para guardar
        self.trial_data = []
        self.all_response_times = []
        
        # Variables de secuencia
        self.digit_sequence = []
        self.user_sequence = []
        self.response_start_time = None
        self.current_digit_index = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar la interfaz principal"""
        self.setWindowTitle("Digit Span Task")
        self.setStyleSheet(f"background-color: {APP_BG};")
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack para diferentes pantallas
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # Crear todas las vistas
        self.welcome_view = self.create_welcome_view()
        self.participant_view = self.create_participant_view()
        self.instructions_view = self.create_instructions_view()
        self.digit_display_view = self.create_digit_display_view()
        self.response_view = self.create_response_view()
        self.feedback_view = self.create_feedback_view()
        self.results_view = self.create_results_view()
        
        # Agregar vistas al stack
        self.stack.addWidget(self.welcome_view)
        self.stack.addWidget(self.participant_view)
        self.stack.addWidget(self.instructions_view)
        self.stack.addWidget(self.digit_display_view)
        self.stack.addWidget(self.response_view)
        self.stack.addWidget(self.feedback_view)
        self.stack.addWidget(self.results_view)
        
        # Mostrar pantalla de bienvenida
        self.stack.setCurrentWidget(self.welcome_view)
        
    def create_card(self, parent=None) -> QFrame:
        """Crear un card estilo moderno"""
        card = QFrame(parent)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 18px;
            }}
        """)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return card
        
    def create_welcome_view(self) -> QWidget:
        """Pantalla de bienvenida"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {APP_BG};")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(80, 40, 80, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Card central
        card = self.create_card()
        card.setMaximumWidth(1200)
        card.setMinimumWidth(600)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(20)
        
        # Título
        title = QLabel("🧠 Digit Span Task")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 48pt; font-weight: 700; color: {TEXT_DARK};")
        card_layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("Tarea de Amplitud de Dígitos")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"font-size: 26pt; color: {TEXT_GRAY};")
        card_layout.addWidget(subtitle)
        
        card_layout.addSpacing(15)
        
        # Descripción
        desc = QLabel("Evaluación de memoria de trabajo a corto plazo")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 18pt; color: {TEXT_DARK};")
        card_layout.addWidget(desc)
        
        card_layout.addSpacing(25)
        
        # Botón comenzar
        btn = QPushButton("Comenzar")
        btn.setMinimumHeight(60)
        btn.setMaximumWidth(300)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border-radius: 30px;
                font-size: 24pt;
                font-weight: 700;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
        """)
        btn.clicked.connect(self.show_participant_input)
        card_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        
        return widget
        
    def create_participant_view(self) -> QWidget:
        """Pantalla para ingresar datos del participante"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {APP_BG};")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(80, 40, 80, 40)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Card central
        card = self.create_card()
        card.setMaximumWidth(900)
        card.setMinimumWidth(500)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(25)
        
        # Título
        title = QLabel("Datos del participante")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 40pt; font-weight: 700; color: {TEXT_DARK};")
        card_layout.addWidget(title)
        
        card_layout.addSpacing(20)
        
        # Label
        label = QLabel("Código de participante:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(f"font-size: 20pt; color: {TEXT_DARK};")
        card_layout.addWidget(label)
        
        # Input
        self.participant_input = QLineEdit()
        self.participant_input.setMaximumWidth(500)
        self.participant_input.setMinimumHeight(50)
        self.participant_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.participant_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #f3f4f6;
                color: {TEXT_DARK};
                border: 2px solid #d1d5db;
                border-radius: 12px;
                padding: 10px 20px;
                font-size: 20pt;
            }}
            QLineEdit:focus {{
                border: 2px solid {PRIMARY};
            }}
        """)
        self.participant_input.returnPressed.connect(self.submit_participant)
        
        input_layout = QHBoxLayout()
        input_layout.addStretch()
        input_layout.addWidget(self.participant_input)
        input_layout.addStretch()
        card_layout.addLayout(input_layout)
        
        card_layout.addSpacing(20)
        
        # Botón continuar
        btn = QPushButton("Continuar")
        btn.setMinimumHeight(55)
        btn.setMaximumWidth(280)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border-radius: 30px;
                font-size: 22pt;
                font-weight: 700;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
        """)
        btn.clicked.connect(self.submit_participant)
        card_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        
        return widget
        
    def create_instructions_view(self) -> QWidget:
        """Pantalla de instrucciones (una sola página)"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {APP_BG};")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(60, 30, 60, 30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Card central
        card = self.create_card()
        card.setMaximumWidth(1200)
        card.setMinimumWidth(600)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setSpacing(12)
        
        # Título
        title = QLabel("Instrucciones")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 40pt; font-weight: 700; color: {TEXT_DARK};")
        card_layout.addWidget(title)
        
        card_layout.addSpacing(10)
        
        # Instrucciones
        instructions = [
            "1️⃣  Se te mostrarán secuencias de números que debes memorizar",
            "2️⃣  Deberás repetir la secuencia EN ORDEN INVERSO (de atrás hacia adelante)",
        ]
        
        for inst in instructions:
            lbl = QLabel(inst)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"font-size: 18pt; color: {TEXT_DARK}; padding: 4px;")
            card_layout.addWidget(lbl)
            
        card_layout.addSpacing(12)
        
        # Cómo responder
        how_label = QLabel("📝 Cómo responder:")
        how_label.setWordWrap(True)
        how_label.setStyleSheet(f"font-size: 22pt; font-weight: 700; color: {TEXT_DARK};")
        card_layout.addWidget(how_label)
        
        how_text = QLabel(
            "• Usa el teclado numérico en pantalla (clic en los números)\n"
            "• Ingresa los dígitos en ORDEN INVERSO\n"
            "• Ejemplo: Si ves 3-7-2, debes ingresar 2-7-3\n"
            "• Presiona 'Continuar' para enviar tu respuesta\n"
            "• Presiona 'Borrar' para eliminar el último dígito"
        )
        how_text.setWordWrap(True)
        how_text.setStyleSheet(f"font-size: 16pt; color: {TEXT_DARK}; padding: 4px;")
        card_layout.addWidget(how_text)
        
        card_layout.addSpacing(15)
        
        # Botón empezar
        btn = QPushButton("¡Empezar la tarea!")
        btn.setMinimumHeight(60)
        btn.setMaximumWidth(350)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border-radius: 30px;
                font-size: 22pt;
                font-weight: 700;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
        """)
        btn.clicked.connect(self.start_trial)
        card_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        
        return widget
        
    def create_digit_display_view(self) -> QWidget:
        """Pantalla para mostrar los dígitos"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {APP_BG};")
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label para mostrar dígitos o mensajes
        self.digit_label = QLabel("")
        self.digit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.digit_label.setStyleSheet(f"font-size: 120pt; font-weight: 700; color: {TEXT_LIGHT};")
        layout.addWidget(self.digit_label)
        
        return widget
        
    def create_response_view(self) -> QWidget:
        """Pantalla para ingresar la respuesta"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {APP_BG};")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        
        # Card para la respuesta
        card = self.create_card()
        card.setMaximumWidth(1100)
        card.setMinimumWidth(550)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(15)
        
        # Título
        title = QLabel("Ingresa la secuencia")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 32pt; font-weight: 700; color: {TEXT_DARK};")
        card_layout.addWidget(title)
        
        # Instrucción de orden inverso
        instruction = QLabel("(En orden inverso)")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet(f"font-size: 20pt; color: {TEXT_GRAY}; font-style: italic;")
        card_layout.addWidget(instruction)
        
        # Mostrar secuencia ingresada
        self.sequence_display = QLabel("Tu secuencia: ")
        self.sequence_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sequence_display.setWordWrap(True)
        self.sequence_display.setStyleSheet(f"font-size: 24pt; color: {PRIMARY}; font-weight: 600;")
        card_layout.addWidget(self.sequence_display)
        
        card_layout.addSpacing(5)
        
        # Teclado numérico
        keypad_layout = QGridLayout()
        keypad_layout.setSpacing(10)
        keypad_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.digit_buttons = {}
        positions = [
            (1, 0, 0), (2, 1, 0), (3, 2, 0),
            (4, 0, 1), (5, 1, 1), (6, 2, 1),
            (7, 0, 2), (8, 1, 2), (9, 2, 2)
        ]
        
        for digit, col, row in positions:
            btn = QPushButton(str(digit))
            btn.setMinimumSize(80, 70)
            btn.setMaximumSize(140, 110)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #f3f4f6;
                    color: {TEXT_DARK};
                    border: 2px solid #d1d5db;
                    border-radius: 12px;
                    font-size: 32pt;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: #e5e7eb;
                    border-color: {PRIMARY};
                }}
                QPushButton:pressed {{
                    background-color: {PRIMARY};
                    color: white;
                }}
            """)
            btn.clicked.connect(lambda checked, d=digit: self.add_digit_to_sequence(d))
            keypad_layout.addWidget(btn, row, col)
            self.digit_buttons[digit] = btn
            
        card_layout.addLayout(keypad_layout)
        
        card_layout.addSpacing(10)
        
        # Botones de control
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Botón borrar
        clear_btn = QPushButton("Borrar")
        clear_btn.setMinimumHeight(55)
        clear_btn.setMaximumWidth(200)
        clear_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ERROR};
                color: white;
                border-radius: 30px;
                font-size: 20pt;
                font-weight: 700;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #dc2626;
            }}
        """)
        clear_btn.clicked.connect(self.clear_last_digit)
        control_layout.addWidget(clear_btn)
        
        # Botón continuar
        continue_btn = QPushButton("Continuar")
        continue_btn.setMinimumHeight(55)
        continue_btn.setMaximumWidth(200)
        continue_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SUCCESS};
                color: white;
                border-radius: 30px;
                font-size: 20pt;
                font-weight: 700;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #059669;
            }}
        """)
        continue_btn.clicked.connect(self.submit_response)
        control_layout.addWidget(continue_btn)
        
        card_layout.addLayout(control_layout)
        
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        
        return widget
        
    def create_feedback_view(self) -> QWidget:
        """Pantalla de feedback"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {APP_BG};")
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setStyleSheet(f"font-size: 80pt; font-weight: 700;")
        layout.addWidget(self.feedback_label)
        
        return widget
        
    def create_results_view(self) -> QWidget:
        """Pantalla de resultados finales"""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {APP_BG};")
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(60, 30, 60, 30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Card de resultados
        card = self.create_card()
        card.setMaximumWidth(1100)
        card.setMinimumWidth(600)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 30, 40, 30)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(20)
        
        # Título
        title = QLabel("¡Tarea Completada!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 44pt; font-weight: 700; color: {TEXT_DARK};")
        card_layout.addWidget(title)
        
        card_layout.addSpacing(15)
        
        # Resultados
        self.results_text = QLabel("")
        self.results_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_text.setWordWrap(True)
        self.results_text.setStyleSheet(f"font-size: 20pt; color: {TEXT_DARK}; line-height: 1.6;")
        card_layout.addWidget(self.results_text)
        
        card_layout.addSpacing(20)
        
        # Botón cerrar
        btn = QPushButton("Cerrar")
        btn.setMinimumHeight(60)
        btn.setMaximumWidth(280)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: white;
                border-radius: 30px;
                font-size: 24pt;
                font-weight: 700;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER};
            }}
        """)
        btn.clicked.connect(self.close_application)
        card_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)
        
        return widget
        
    # =============== LÓGICA DE LA TAREA ===============
    
    def show_participant_input(self):
        """Mostrar pantalla de ingreso de participante"""
        self.stack.setCurrentWidget(self.participant_view)
        self.participant_input.setFocus()
        
    def submit_participant(self):
        """Guardar ID del participante y mostrar instrucciones"""
        participant_id = self.participant_input.text().strip()
        if not participant_id:
            return
        self.participant_id = participant_id
        self.stack.setCurrentWidget(self.instructions_view)
        
    def start_trial(self):
        """Iniciar un nuevo intento"""
        # Generar secuencia aleatoria SIN REPETIR DÍGITOS (solo 1-9)
        available_digits = list(range(1, 10))  # 1-9
        self.digit_sequence = random.sample(available_digits, self.current_span)
        self.user_sequence = []
        self.current_digit_index = 0
        
        # Cambiar a vista de dígitos
        self.stack.setCurrentWidget(self.digit_display_view)
        
        # Mostrar "Memoriza los dígitos"
        self.digit_label.setText("Memoriza los dígitos")
        self.digit_label.setStyleSheet(f"font-size: 64pt; font-weight: 700; color: {TEXT_LIGHT};")
        QTimer.singleShot(1800, self.show_get_ready)
        
    def show_get_ready(self):
        """Mostrar mensaje de preparación"""
        self.digit_label.setText("¡Prepárate!")
        self.digit_label.setStyleSheet(f"font-size: 80pt; font-weight: 700; color: {TEXT_LIGHT};")
        QTimer.singleShot(1500, self.show_digit_sequence)
        
    def show_digit_sequence(self):
        """Mostrar secuencia de dígitos"""
        self.show_next_digit()
        
    def show_next_digit(self):
        """Mostrar el siguiente dígito"""
        if self.current_digit_index < len(self.digit_sequence):
            digit = self.digit_sequence[self.current_digit_index]
            self.digit_label.setText(str(digit))
            self.digit_label.setStyleSheet(f"font-size: 140pt; font-weight: 700; color: {TEXT_LIGHT};")
            QTimer.singleShot(600, self.show_blank)
        else:
            self.start_response_phase()
            
    def show_blank(self):
        """Mostrar pantalla en blanco entre dígitos"""
        self.digit_label.setText("")
        self.current_digit_index += 1
        QTimer.singleShot(200, self.show_next_digit)
        
    def start_response_phase(self):
        """Iniciar fase de respuesta"""
        self.response_start_time = time.time()
        self.update_sequence_display()
        self.update_button_states()  # Habilitar todos los botones al inicio
        self.stack.setCurrentWidget(self.response_view)
        self.response_view.setFocus()
        
    def add_digit_to_sequence(self, digit: int):
        """Agregar dígito a la secuencia del usuario"""
        # Solo permitir si no está ya en la secuencia y no se ha completado
        if len(self.user_sequence) < len(self.digit_sequence) and digit not in self.user_sequence:
            self.user_sequence.append(digit)
            self.update_sequence_display()
            self.update_button_states()
            
    def clear_last_digit(self):
        """Borrar el último dígito ingresado"""
        if self.user_sequence:
            self.user_sequence.pop()
            self.update_sequence_display()
            self.update_button_states()
            
    def update_button_states(self):
        """Actualizar estado de los botones (deshabilitar los ya usados)"""
        for digit, btn in self.digit_buttons.items():
            if digit in self.user_sequence:
                btn.setEnabled(False)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #d1d5db;
                        color: #9ca3af;
                        border: 2px solid #d1d5db;
                        border-radius: 12px;
                        font-size: 32pt;
                        font-weight: 700;
                    }}
                """)
            else:
                btn.setEnabled(True)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #f3f4f6;
                        color: {TEXT_DARK};
                        border: 2px solid #d1d5db;
                        border-radius: 12px;
                        font-size: 32pt;
                        font-weight: 700;
                    }}
                    QPushButton:hover {{
                        background-color: #e5e7eb;
                        border-color: {PRIMARY};
                    }}
                    QPushButton:pressed {{
                        background-color: {PRIMARY};
                        color: white;
                    }}
                """)
            
    def update_sequence_display(self):
        """Actualizar visualización de la secuencia"""
        if self.user_sequence:
            sequence_text = f"Tu secuencia: {' '.join(map(str, self.user_sequence))}"
        else:
            sequence_text = "Tu secuencia: "
        self.sequence_display.setText(sequence_text)
        
    def submit_response(self):
        """Enviar respuesta"""
        if not self.user_sequence:
            return
            
        # Calcular tiempo de respuesta
        response_time = time.time() - self.response_start_time
        self.all_response_times.append(response_time)
        
        # Evaluar respuesta - DEBE SER EN ORDEN INVERSO
        reversed_sequence = list(reversed(self.digit_sequence))
        is_correct = self.user_sequence == reversed_sequence
        
        # Guardar datos del intento
        trial_info = {
            'participant_id': self.participant_id,
            'trial_number': len(self.trial_data) + 1,
            'span_length': self.current_span,
            'span_attempt': self.span_counter + 1,
            'digit_sequence': self.digit_sequence.copy(),
            'user_sequence': self.user_sequence.copy(),
            'is_correct': is_correct,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        }
        self.trial_data.append(trial_info)
        
        # Mostrar feedback
        self.show_feedback(is_correct)
        
    def show_feedback(self, is_correct: bool):
        """Mostrar feedback de la respuesta"""
        self.stack.setCurrentWidget(self.feedback_view)
        
        if is_correct:
            self.feedback_label.setText("¡CORRECTO! ✓")
            self.feedback_label.setStyleSheet(f"font-size: 80pt; font-weight: 700; color: {SUCCESS};")
            self.span_correct = 1  # Marcamos que acertó al menos uno
        else:
            self.feedback_label.setText("INCORRECTO ✗")
            self.feedback_label.setStyleSheet(f"font-size: 80pt; font-weight: 700; color: {ERROR};")
            
        self.span_counter += 1
        
        QTimer.singleShot(2000, self.check_span_completion)
        
    def check_span_completion(self):
        """Verificar si completó los 2 intentos del span"""
        # Si ya completó los 2 intentos
        if self.span_counter >= 2:
            # Si acertó AL MENOS UNO de los 2 intentos
            if self.span_correct >= 1:
                self.best_span = max(self.best_span, self.current_span)
                self.level_index += 1
                self.span_counter = 0
                self.span_correct = 0

                if self.level_index >= len(self.span_levels):
                    self.end_task()
                    return

                self.current_span = self.span_levels[self.level_index]
                self.show_span_completed()
            else:
                # Falló ambos intentos
                self.end_task()
        else:
            # Aún falta el segundo intento
            self.start_trial()
            
    def show_span_completed(self):
        """Mostrar mensaje de nivel completado"""
        self.stack.setCurrentWidget(self.digit_display_view)
        level_num = self.level_index + 1
        self.digit_label.setText(
            f"¡Excelente!\n\nNivel {level_num}: {self.current_span} dígitos"
        )
        self.digit_label.setStyleSheet(f"font-size: 56pt; font-weight: 700; color: {SUCCESS};")
        QTimer.singleShot(2500, self.start_trial)
        
    def end_task(self):
        """Finalizar la tarea"""
        self.digit_span = self.best_span
        
        # Calcular estadísticas
        total_trials = len(self.trial_data)
        correct_trials = sum(1 for t in self.trial_data if t['is_correct'])
        accuracy = (correct_trials / total_trials * 100) if total_trials > 0 else 0
        avg_rt = sum(self.all_response_times) / len(self.all_response_times) if self.all_response_times else 0
        
        # Guardar datos
        self.save_data()
        
        # Mostrar resultados
        results_html = f"""
        <p style='font-size: 26pt; margin-bottom: 20px;'>
            <strong style='color: {PRIMARY};'>Tu Digit Span: {self.digit_span} dígitos</strong>
        </p>
        
        <p style='font-size: 18pt; line-height: 1.7;'>
            <strong>Estadísticas:</strong><br/>
            • Intentos totales: {total_trials}<br/>
            • Respuestas correctas: {correct_trials}<br/>
            • Precisión: {accuracy:.1f}%<br/>
            • Tiempo promedio: {avg_rt:.2f} segundos
        </p>
        
        <p style='font-size: 16pt; margin-top: 20px; color: {TEXT_GRAY};'>
            Los datos se han guardado exitosamente.
        </p>
        """
        
        self.results_text.setText(results_html)
        self.stack.setCurrentWidget(self.results_view)
        
    def save_data(self):
        """Guardar datos en CSV"""
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Archivo detallado
        detailed_file = f"{data_dir}/digitspan_detailed_{self.participant_id}_{timestamp}.csv"
        with open(detailed_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['participant_id', 'trial_number', 'span_length', 'span_attempt',
                         'digit_sequence', 'user_sequence', 'is_correct', 'response_time', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for trial in self.trial_data:
                trial_copy = trial.copy()
                trial_copy['digit_sequence'] = ' '.join(map(str, trial['digit_sequence']))
                trial_copy['user_sequence'] = ' '.join(map(str, trial['user_sequence']))
                writer.writerow(trial_copy)
                
        # Archivo resumen
        summary_file = f"{data_dir}/digitspan_summary_{self.participant_id}_{timestamp}.csv"
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Participant_ID', 'Digit_Span', 'Total_Trials', 'Correct_Trials',
                           'Accuracy_Percent', 'Average_Response_Time', 'Best_Span', 'Date'])
            
            total_trials = len(self.trial_data)
            correct_trials = sum(1 for t in self.trial_data if t['is_correct'])
            accuracy = (correct_trials / total_trials * 100) if total_trials > 0 else 0
            avg_rt = sum(self.all_response_times) / len(self.all_response_times) if self.all_response_times else 0
            
            writer.writerow([
                self.participant_id,
                self.digit_span,
                total_trials,
                correct_trials,
                f"{accuracy:.2f}",
                f"{avg_rt:.3f}",
                self.best_span,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
            
        print(f"Datos guardados:\n- {detailed_file}\n- {summary_file}")
        
    def close_application(self):
        """Cerrar la aplicación"""
        self.close()
        

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    
    # Configurar fuente por defecto
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = DigitSpanTask()
    window.showMaximized()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
