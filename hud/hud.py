import sys
import os
import queue
import psutil
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)
if current_dir in sys.path:
    sys.path.remove(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from hud.widgets import StatusPill, WaveformWidget, LiveTranscriptWidget, SystemStatsWidget, MemoryPanel
from hud.animations import ArcReactor

BG      = "#020d1a"
CYAN    = "#00e5ff"
AMBER   = "#ff9f00"
GREEN   = "#00ff88"


class SystemStatsThread(QThread):
    stats_updated = pyqtSignal(float, float, str)

    def run(self):
        while True:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            try:
                b = psutil.sensors_battery()
                bat = f"{b.percent:.0f}%" if b else "N/A"
            except Exception:
                bat = "N/A"
            self.stats_updated.emit(cpu, ram, bat)
            self.msleep(1000)


class JarvisHUD(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(420)

        # Thread-safe update queue — voice thread posts here, QTimer applies on main thread
        self._queue = queue.Queue()
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._process_queue)
        self._poll_timer.start(50)

        # Central widget
        central = QWidget()
        central.setStyleSheet(f"background-color: rgba(2, 13, 26, 220); border-radius: 12px;")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── 1. Header: title + live clock ────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("J.A.R.V.I.S")
        title.setStyleSheet(f"color: {CYAN}; font-family: 'Consolas'; font-size: 16px; font-weight: bold; letter-spacing: 4px;")
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(f"color: {AMBER}; font-family: 'Consolas'; font-size: 12px;")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.clock_label)
        root.addLayout(header)

        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {CYAN}; opacity: 0.3;")
        root.addWidget(divider)

        # ── 2. Arc reactor + status pills ────────────────────────────────────
        top = QHBoxLayout()

        self.arc_reactor = ArcReactor()
        top.addWidget(self.arc_reactor)
        top.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        pills = QVBoxLayout()
        self._pill_idle      = StatusPill("IDLE",      f"rgba(0, 229, 255, 60)")
        self._pill_listening = StatusPill("LISTENING", f"rgba(255, 159, 0, 140)")
        self._pill_thinking  = StatusPill("THINKING",  f"rgba(0, 255, 136, 140)")
        self._pill_speaking  = StatusPill("SPEAKING",  f"rgba(0, 229, 255, 180)")
        for p in (self._pill_idle, self._pill_listening, self._pill_thinking, self._pill_speaking):
            pills.addWidget(p)
        self._pill_listening.hide()
        self._pill_thinking.hide()
        self._pill_speaking.hide()
        top.addLayout(pills)
        root.addLayout(top)

        # ── 3. Waveform ───────────────────────────────────────────────────────
        self.waveform = WaveformWidget()
        root.addWidget(self.waveform)

        # ── 4. Transcript ─────────────────────────────────────────────────────
        self.transcript = LiveTranscriptWidget()
        root.addWidget(self.transcript)

        # ── 5. System stats ───────────────────────────────────────────────────
        self.stats = SystemStatsWidget()
        root.addWidget(self.stats)

        # ── 6. Memory panel ───────────────────────────────────────────────────
        self.memory_panel = MemoryPanel()
        root.addWidget(self.memory_panel)

        # ── Timers ────────────────────────────────────────────────────────────
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        self._stats_thread = SystemStatsThread()
        self._stats_thread.stats_updated.connect(self.stats.update_stats)
        self._stats_thread.start()

        print("[HUD] Iron Man HUD initialized.")

    # ── Clock ─────────────────────────────────────────────────────────────────

    def _update_clock(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))

    # ── Thread-safe queue ─────────────────────────────────────────────────────

    def _process_queue(self):
        while not self._queue.empty():
            try:
                action, args = self._queue.get_nowait()
                if action == "status":
                    self._apply_status(args[0])
                elif action == "transcript":
                    self.transcript.set_exchange(args[0], args[1])
                elif action == "memory":
                    self.memory_panel.update_memory(args[0], args[1], args[2])
            except Exception:
                pass

    def enqueue_status(self, status: str):
        """Call from any thread to update the status pill."""
        self._queue.put(("status", (status,)))

    def enqueue_transcript(self, user_text: str, jarvis_text: str):
        """Call from any thread to update the transcript panel."""
        self._queue.put(("transcript", (user_text, jarvis_text)))

    def enqueue_memory(self, name: str, city: str, sessions: int):
        """Call from any thread to update the memory panel."""
        self._queue.put(("memory", (name, city, sessions)))

    # ── Direct setters (main-thread only) ────────────────────────────────────

    def _apply_status(self, status: str):
        for p in (self._pill_idle, self._pill_listening, self._pill_thinking, self._pill_speaking):
            p.hide()
        s = status.upper()
        if   s == "LISTENING": self._pill_listening.show()
        elif s == "THINKING":  self._pill_thinking.show()
        elif s == "SPEAKING":
            self._pill_speaking.show()
            self.waveform.set_speaking(True)
            return
        else:
            self._pill_idle.show()
        self.waveform.set_speaking(False)

    def set_status(self, status: str):
        """Thread-safe: enqueues status update."""
        self.enqueue_status(status)

    def set_transcript(self, user_text: str, jarvis_text: str):
        """Thread-safe: enqueues transcript update."""
        self.enqueue_transcript(user_text, jarvis_text)

    def update_memory(self, name: str, city: str, sessions: int):
        """Thread-safe: enqueues memory panel update."""
        self.enqueue_memory(name, city, sessions)

    # Backward-compatible alias
    def update_transcript(self, speaker: str, text: str):
        self.transcript.add_transcript(speaker, text)


def main():
    app = QApplication(sys.argv)
    screen = app.primaryScreen().geometry()
    hud = JarvisHUD()
    hud.setFixedHeight(screen.height())
    hud.move(screen.width() - hud.width() - 0, 0)
    hud.show()

    # Demo sequence
    QTimer.singleShot(1000, lambda: hud.set_status("LISTENING"))
    QTimer.singleShot(2500, lambda: hud.set_transcript("Hey JARVIS, what's the weather?", ""))
    QTimer.singleShot(3000, lambda: hud.set_status("THINKING"))
    QTimer.singleShot(5000, lambda: hud.set_status("SPEAKING"))
    QTimer.singleShot(5100, lambda: hud.set_transcript(
        "Hey JARVIS, what's the weather?",
        "It is currently 31 degrees and clear skies in Nagpur, sir."
    ))
    QTimer.singleShot(8000, lambda: hud.set_status("IDLE"))
    QTimer.singleShot(1500, lambda: hud.update_memory("Saurav", "Nagpur", 42))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
