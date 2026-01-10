# -*- coding: utf-8 -*-
import sys
import time
import os
from typing import Dict

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget

from config import CONCEPTOS, APP_BG
from gemini_eval import EvalWorker
from screens import (
    Presentacion, DatosParticipante, BienvenidaParticipante, ConceptoView, ChatLeccion,
    TurnoParticipante, PreguntaView, ProcesandoView, FeedbackView,
    FinView, HintView, PaseConceptoView, DescansoView
)

# ================== EXTRA: WEBSOCKET PARA EMOCIONES ==================
import json
import io
import threading
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

WS_HOST = '0.0.0.0'
WS_PORT = 9000
ARM_DELAY_MS = 3000  # margen antes de START (ms)

ws_clients = []
web_ready = False
t0_ms = None


def ws_broadcast(obj: dict):
    """Envía un mensaje JSON a todos los clientes conectados (navegador)."""
    payload = json.dumps(obj)
    for c in list(ws_clients):
        try:
            c.sendMessage(payload)
        except Exception as e:
            print("[WS] Error enviando:", e)


class SyncServer(WebSocket):
    """
    Servidor WS minimal para sincronizar con el navegador (face-api.js).

    Mensajes manejados:
      - HELLO {role:'web'} -> ACK
      - READY -> marcar navegador listo
      - CSV_DATA -> guardar emociones en resultados/emociones_sujetoX.csv
    """
    def handleMessage(self):
        global web_ready

        try:
            msg = json.loads(self.data)
        except Exception:
            msg = {}

        # HELLO handshake
        if msg.get('type') == 'HELLO' and msg.get('role') == 'web':
            print("[WEB] HELLO recibido")
            self.sendMessage(json.dumps({
                "type": "ACK",
                "role": "python-server"
            }))
            return

        # READY del navegador (modelos cargados + video listo)
        if msg.get('type') == 'READY':
            web_ready = True
            print("[WEB] READY recibido (navegador preparado)")
            return

        # CSV de emociones desde el navegador
        if msg.get('type') == 'CSV_DATA':
            sujeto_id = msg.get('sujeto_id', 'NA')
            csv_text = msg.get('csv_text', '')

            folder = "resultados"
            try:
                os.makedirs(folder, exist_ok=True)
                csv_path = os.path.join(folder, f"emociones_sujeto{sujeto_id}.csv")
                with io.open(csv_path, "w", encoding="utf-8") as f:
                    f.write(csv_text)
                print("[WS] CSV de emociones guardado:", csv_path)
            except Exception as e:
                print("[WS] Error guardando CSV emociones:", e)
            return

        print("[WS] Mensaje desconocido:", msg)

    def handleConnected(self):
        print("[WS] Cliente conectado:", self.address)
        ws_clients.append(self)

    def handleClose(self):
        print("[WS] Cliente desconectado:", self.address)
        try:
            ws_clients.remove(self)
        except Exception:
            pass


def run_ws_server():
    """Levanta el servidor WebSocket en un hilo separado."""
    server = SimpleWebSocketServer(WS_HOST, WS_PORT, SyncServer)
    print(f"[SYNC] Servidor WS en ws://{WS_HOST}:{WS_PORT}")
    server.serveforever()


def send_arm_and_start(arm_delay_ms=ARM_DELAY_MS):
    """
    Envía ARM (t0 en el futuro) y luego START en ese t0.
    El navegador comienza a loguear emociones desde START.
    """
    global t0_ms
    now_ms = int(time.time() * 1000)
    t0_ms = now_ms + int(arm_delay_ms)
    t0_hora = time.strftime('%H:%M:%S', time.localtime(t0_ms / 1000.0))

    print("[SYNC] ARM -> t0 =", t0_ms, "(", t0_hora, ")")
    ws_broadcast({"type": "ARM", "t0": t0_ms})

    time.sleep(arm_delay_ms / 1000.0)

    ws_broadcast({"type": "START", "t0": t0_ms})
    print("[SYNC] START enviado en", t0_hora)


# ================== VENTANA PRINCIPAL PYQT (GRUPO CONTROL) ==================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Intervenciones cognitivas | Grupo Control — Actividad")
        self.setStyleSheet(f"background:{APP_BG};")

        self.last_eval_correct = None

        self.idx = 0
        self.user_text = ""
        self.eval_result: Dict = {}
        self.num_sujeto = ""
        self.participant_name = ""
        self.last_question_text = ""   # última pregunta mostrada en pantalla

        # estado del flujo
        self.stage = "concepto"           # "concepto" o "ejemplo"
        self.concept_attempt = 0
        self.example_attempt = 0
        self.current_eval_stage = None    # qué se está evaluando ahora
        self.after_feedback_action = None # "show_pase_msg", "next_concept"
        self.hint_mode = None             # "concepto" o "ejemplo"

        # tiempos
        self.question_start_time = None       # tiempo desde que aparece la pregunta
        self.timeline_start_time = None       # inicio global de la intervención
        self.timeline_file_path = None        # ruta del txt de timeline

        self._pending_timeline = None  

        # resultados por concepto
        self.results_per_concept = []

        self.stack = QStackedWidget(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.stack)

        # Pantallas
        self.present = Presentacion()        # 0
        self.datos   = DatosParticipante()   # 1
        self.bienvenida = BienvenidaParticipante() # 2
        self.concepto = ConceptoView()        # 3
        self.chat    = ChatLeccion()         # 4
        self.turno   = TurnoParticipante()   # 5
        self.preg    = PreguntaView()        # 6
        self.proc    = ProcesandoView()      # 7
        self.fb       = FeedbackView()        # 8
        self.fin      = FinView()             # 9
        self.hint     = HintView()            # 10
        self.pase     = PaseConceptoView()    # 11
        self.descanso = DescansoView()        # 12

        self.stack.addWidget(self.present)
        self.stack.addWidget(self.datos)
        self.stack.addWidget(self.bienvenida)
        self.stack.addWidget(self.concepto)
        self.stack.addWidget(self.chat)
        self.stack.addWidget(self.turno)
        self.stack.addWidget(self.preg)
        self.stack.addWidget(self.proc)
        self.stack.addWidget(self.fb)
        self.stack.addWidget(self.fin)
        self.stack.addWidget(self.hint)
        self.stack.addWidget(self.pase)
        self.stack.addWidget(self.descanso)

        # Conexiones
        self.present.go.connect(self._go_datos)
        self.datos.submitted.connect(self._on_datos)
        self.bienvenida.cont.connect(self._go_concepto)
        self.concepto.done.connect(self._go_chat)
        self.chat.done.connect(self._go_turno)
        self.turno.cont.connect(self._go_preg)
        self.preg.send.connect(self._go_proc)
        self.descanso.cont.connect(self._advance_concept)
        self.hint.proceed.connect(self._hint_proceed)
        self.pase.cont.connect(self._pase_next)

        self.stack.setCurrentIndex(0)
        self.showMaximized()

    # -------- helpers internos --------
    def _current_concept(self) -> dict:
        return CONCEPTOS[self.idx]

    def _replace_participante(self, texto: str) -> str:
        return texto.replace("[participante]", self.participant_name)

    def _get_concept_question_text(self, intento: int) -> str:
        pe = self._current_concept()["parte_experimentacion"]
        if intento == 1:
            base = pe["pregunta_concepto"]
        else:
            base = pe["repeticion_pregunta_concepto"]
        base = base.split("|")[0].strip()
        return self._replace_participante(base)

    def _get_concept_question_after_hint(self) -> str:
        pe = self._current_concept()["parte_experimentacion"]
        base = pe["pregunta_concepto"]
        base = base.split("|")[0].strip()
        return self._replace_participante(base)

    def _get_example_question_text(self, intento: int) -> str:
        pe = self._current_concept()["parte_experimentacion"]
        base = pe["pedir_ejemplo"]
        base = base.split("|")[0].strip()
        return self._replace_participante(base)

    def _get_example_question_after_hint(self) -> str:
        pe = self._current_concept()["parte_experimentacion"]
        base = pe.get(
            "pedir_ejemplo_tras_ayuda",
            "Dame un ejemplo distinto al que tu compañero mencionó."
        )
        base = base.split("|")[0].strip()
        return self._replace_participante(base)

    # -------- TIMELINE --------
    def _init_timeline(self):
        folder = "resultados"
        os.makedirs(folder, exist_ok=True)

        filename = f"registro_{self.num_sujeto}_timeline.txt"
        self.timeline_file_path = os.path.join(folder, filename)

        with open(self.timeline_file_path, "w", encoding="utf-8") as f:
            f.write(
                f"Timeline de intervención - {self.num_sujeto} ({self.participant_name})\n\n"
            )

        self.timeline_start_time = time.perf_counter()
        self._timeline_log("Cronometro iniciado")

    def _timeline_log(self, message: str):
        if not self.timeline_file_path or self.timeline_start_time is None:
            return

        elapsed = time.perf_counter() - self.timeline_start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"

        with open(self.timeline_file_path, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {message}\n")

    def _log_response_time(self):
        """
        Calcula el tiempo de respuesta de la pregunta actual y lo devuelve.
        (OJO: no escribe Correcto/Incorrecto aquí, porque Gemini responde después.)
        """
        if self.question_start_time is None:
            return None
        elapsed_rt = time.perf_counter() - self.question_start_time
        self.question_start_time = None
        return elapsed_rt

    # -------- RESUMEN DE PUNTUACIONES --------
    def _write_results_summary(self):
        if not self.results_per_concept:
            return

        folder = "resultados"
        os.makedirs(folder, exist_ok=True)

        filename = os.path.join(
            folder,
            f"registro_sujeto{self.num_sujeto}_puntuaciones.txt"
        )

        total_concept = 0
        total_example = 0

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Actividad de intervencion - Sujeto {self.num_sujeto}:\n\n")

            for info in self.results_per_concept:
                f.write(f"Concepto {info['concepto']}:\n")
                f.write(
                    f"Concepto: {'Correcto' if info['concept_correct'] else 'Incorrecto'}\n"
                )
                f.write(
                    f"Ejemplo: {'Correcto' if info['example_correct'] else 'Incorrecto'}\n\n"
                )

                if info["concept_correct"]:
                    total_concept += 1
                if info["example_correct"]:
                    total_example += 1

            f.write("Total:\n")
            f.write(
                f"Respondio correctamente a {total_concept} preguntas de concepto\n"
            )
            f.write(
                f"Respondio correctamente a {total_example} ejemplos\n"
            )

    # -------- SYNC CON SISTEMA DE EMOCIONES --------
    def _sync_with_emotion_system(self):
        if web_ready:
            print("[SYNC] Navegador listo. Enviando ARM -> START…")
            threading.Thread(target=send_arm_and_start, daemon=True).start()
            self._timeline_log("[SYNC] START sincronizado (emociones)")
            return
        QTimer.singleShot(200, self._sync_with_emotion_system)

    # -------- transiciones de pantallas --------
    def _go_datos(self):
        self.stack.setCurrentIndex(1)

    def _on_datos(self, num_sujeto: str, nombre: str):
        self.num_sujeto = num_sujeto
        self.participant_name = nombre

        self.turno.set_participant_name(self.participant_name)
        self.bienvenida.set_participant_name(self.participant_name)
        self.fin.set_participant_name(self.participant_name)

        self._init_timeline()
        self._timeline_log("Pantalla de bienvenida mostrada")

        ws_broadcast({"type": "META", "sujeto_id": self.num_sujeto})
        print("[SYNC] META enviado con sujeto_id:", self.num_sujeto)

        self._sync_with_emotion_system()
        self.stack.setCurrentIndex(2)

    def _go_concepto(self):
        concepto = self._current_concept()
        numero_concepto = self.idx + 1
        self.stage = "concepto"
        self.concept_attempt = 0
        self.example_attempt = 0
        self.last_question_text = ""

        if len(self.results_per_concept) < self.idx + 1:
            self.results_per_concept.append({
                "concepto": numero_concepto,
                "concept_correct": False,
                "example_correct": False,
            })

        self._timeline_log(f"Concepto {numero_concepto}: {concepto['titulo']}")
        self.stack.setCurrentIndex(3)
        self.concepto.mostrar_concepto(numero_concepto, concepto["titulo"])

    def _go_chat(self):
        self._timeline_log("Fase observacion")
        self.stack.setCurrentIndex(4)
        self.chat.start_sequence(self._current_concept())

    def _go_turno(self):
        self.stage = "concepto"
        self.concept_attempt = 0
        self.example_attempt = 0
        self.last_question_text = ""
        self._timeline_log("Fase experimental")

        self.stack.setCurrentIndex(5)
        QTimer.singleShot(5000, self.turno.cont.emit)

    def _show_result_then_descanso(self, texto: str, positivo: bool):
        self.fb.show_final(texto, positivo=positivo)
        self.stack.setCurrentWidget(self.fb)
        QTimer.singleShot(4000, self._show_descanso)

    def _show_descanso(self):
        title, duration_secs, btn_text = self._get_descanso_info()
        self.descanso.set_info(title, duration_secs, btn_text)
        self.stack.setCurrentWidget(self.descanso)

    def _get_descanso_info(self):
        total = len(CONCEPTOS)
        midpoint = total // 2
        is_midpoint = midpoint > 0 and (self.idx + 1) == midpoint
        title = "Descanso" if is_midpoint else "Breve descanso"
        duration_secs = 240 if is_midpoint else 15
        btn_text = "Siguiente" if self.idx == total - 1 else "Siguiente concepto ➜"
        return title, duration_secs, btn_text

    def _go_preg(self):
        self.stack.setCurrentIndex(6)
        if self.stage == "concepto":
            intento = self.concept_attempt + 1
            texto = self._get_concept_question_text(intento)
        else:
            intento = self.example_attempt + 1
            texto = self._get_example_question_text(intento)
        self.last_question_text = texto
        self.preg.set_question(texto)

        self.question_start_time = time.perf_counter()

    def _go_proc(self, texto: str):
        self.user_text = texto
        self.stack.setCurrentIndex(7)

        # attempt del intento ACTUAL (antes de incrementar counters)
        if self.stage == "concepto":
            attempt = self.concept_attempt + 1
        else:
            attempt = self.example_attempt + 1

        # medir RT aquí (solo tiempo)
        rt = self._log_response_time()

        # guardar lo que luego se escribirá cuando llegue Gemini
        self._pending_timeline = {
            "stage": self.stage,
            "attempt": attempt,
            "rt": rt,
        }

        base = self._current_concept()
        pe = base["parte_experimentacion"]
        obs = base["parte_observacion"]

        if self.stage == "concepto":
            explicacion = obs["profesor_explica"]
            pregunta = self.last_question_text or self._get_concept_question_text(self.concept_attempt + 1)
            concepto_eval = {
                "titulo": base.get("titulo", "Concepto"),
                "explicacion": explicacion,
                "pregunta": pregunta
            }
        else:
            modelo = pe["respuesta_modelo"]
            pregunta = self.last_question_text or self._get_example_question_text(self.example_attempt + 1)
            concepto_eval = {
                "titulo": base.get("titulo", "Concepto") + " (ejemplo)",
                "explicacion": modelo,
                "pregunta": pregunta
            }

        self.current_eval_stage = self.stage
        self.worker = EvalWorker(self.user_text, concepto_eval)
        self.worker.finished.connect(self._got_eval)
        self.worker.start()

    def _got_eval(self, res: dict):
        print("[DEBUG] Resultado recibido desde Gemini en main:", res)

        self.eval_result = res
        self.last_eval_correct = bool(res.get("correct", False))

        # Escribir timeline AQUÍ, ya con el resultado real
        pending = self._pending_timeline or {}
        stage = pending.get("stage", self.current_eval_stage)
        attempt = pending.get("attempt", "?")
        rt = pending.get("rt", None)

        label = "Concepto" if stage == "concepto" else "Ejemplo"
        estado = "Correcto" if self.last_eval_correct else "Incorrecto"

        if rt is not None:
            self._timeline_log(f"{label} | Intento: {attempt} | Resultado: {estado} - duración: {rt:.2f} s")
        else:
            self._timeline_log(f"{label} | Intento: {attempt} | Resultado: {estado}")

        # limpiar pending (por si acaso)
        self._pending_timeline = None

        # continuar flujo normal
        if self.current_eval_stage == "concepto":
            self._handle_concept_eval(res)
        else:
            self._handle_example_eval(res)

    # -------- manejo evaluación de concepto --------
    def _handle_concept_eval(self, res: dict):
        self.concept_attempt += 1
        pe = self._current_concept()["parte_experimentacion"]

        if res.get("correct"):
            if self.idx < len(self.results_per_concept):
                self.results_per_concept[self.idx]["concept_correct"] = True
            self.stage = "ejemplo"
            self._start_example_stage()
        else:
            if self.concept_attempt == 1:
                self._go_preg()
            elif self.concept_attempt == 2:
                hint_text = self._replace_participante(pe["respuesta_concepto_modelo"])
                self.hint_mode = "concepto"
                self.hint.set_text(hint_text)
                self.stack.setCurrentIndex(10)
            else:
                neg_text = self._replace_participante(pe["retroalimentacion_negativa"])
                self._show_result_then_descanso(neg_text, positivo=False)

    def _start_example_stage(self):
        self.example_attempt = 0
        self.stage = "ejemplo"
        self.last_question_text = ""
        self._go_preg()

    # -------- manejo evaluación de ejemplo --------
    def _handle_example_eval(self, res: dict):
        self.example_attempt += 1
        pe = self._current_concept()["parte_experimentacion"]

        if res.get("correct"):
            if self.idx < len(self.results_per_concept):
                self.results_per_concept[self.idx]["example_correct"] = True

            pos_text = self._replace_participante(pe["retroalimentacion_positiva"])
            self._show_result_then_descanso(pos_text, positivo=True)
        else:
            if self.example_attempt == 1:
                hint_text = self._replace_participante(pe["respuesta_modelo"])
                self.hint_mode = "ejemplo"
                self.hint.set_text(hint_text)
                self.stack.setCurrentIndex(10)
            else:
                neg_text = self._replace_participante(pe["retroalimentacion_negativa"])
                self._show_result_then_descanso(neg_text, positivo=False)

    # -------- tras pantalla de pista --------
    def _hint_proceed(self):
        if self.hint_mode == "concepto":
            texto = self._get_concept_question_after_hint()
            self.last_question_text = texto
            self.stack.setCurrentIndex(6)
            self.preg.set_question(texto)
            self.question_start_time = time.perf_counter()
        elif self.hint_mode == "ejemplo":
            self.stage = "ejemplo"
            texto = self._get_example_question_after_hint()
            self.last_question_text = texto
            self.stack.setCurrentIndex(6)
            self.preg.set_question(texto)
            self.question_start_time = time.perf_counter()
        else:
            self._go_preg()

    # -------- mensaje de pase a otro concepto --------
    def _pase_next(self):
        self._advance_concept()

    # -------- acción tras feedback --------
    def _next_or_finish(self):
        if self.after_feedback_action == "show_pase_msg":
            pe = self._current_concept()["parte_experimentacion"]
            texto = self._replace_participante(pe["pase_otro_concepto"])
            self.pase.set_text(texto)
            self.stack.setCurrentIndex(11)
            self.after_feedback_action = None
        elif self.after_feedback_action == "next_concept":
            self.after_feedback_action = None
            self._advance_concept()
        else:
            self._advance_concept()

    def _advance_concept(self):
        self.idx += 1
        if self.idx >= len(CONCEPTOS):
            self.stack.setCurrentIndex(9)
            self._timeline_log("Fin de la intervención")
            self._write_results_summary()

            ws_broadcast({"type": "FIN"})
            print("[SYNC] Señal FIN enviada al navegador para guardar CSV de emociones")
        else:
            self._go_concepto()


def main():
    if not CONCEPTOS:
        print("No se cargaron conceptos desde actividades.json. Revisa el archivo.", file=sys.stderr)

    ws_thread = threading.Thread(target=run_ws_server, daemon=True)
    ws_thread.start()

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
