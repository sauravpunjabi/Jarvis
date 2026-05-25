import random
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit, QFrame
from PyQt6.QtCore import Qt, QTimer


class StatusPill(QWidget):
    def __init__(self, text: str, color: str):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.label.setStyleSheet(f"""
            QLabel {{
                color: #ffffff;
                background-color: {color};
                border-radius: 12px;
                padding: 4px 12px;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                font-size: 10px;
            }}
        """)


class WaveformWidget(QWidget):
    """25 animated bars that pulse when JARVIS is speaking."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._speaking = False
        self._bars = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        for _ in range(25):
            bar = QFrame(self)
            bar.setFixedWidth(7)
            bar.setFixedHeight(4)
            bar.setStyleSheet("background-color: #00e5ff; border-radius: 3px;")
            layout.addWidget(bar)
            self._bars.append(bar)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(80)

    def set_speaking(self, speaking: bool):
        self._speaking = speaking

    def _animate(self):
        for bar in self._bars:
            h = random.randint(6, 42) if self._speaking else 4
            bar.setFixedHeight(h)


class LiveTranscriptWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setFrameStyle(0)
        self.text_box.setFixedHeight(110)
        self.text_box.setStyleSheet("""
            QTextEdit {
                background-color: rgba(2, 13, 26, 180);
                color: #00e5ff;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                border: 1px solid rgba(0, 229, 255, 50);
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout.addWidget(self.text_box)
        self.setLayout(layout)

    def add_transcript(self, speaker: str, text: str):
        color = "#ffffff" if speaker.lower() == "user" else "#00e5ff"
        self.text_box.append(
            f"<span style='color:{color};'><b>{speaker.upper()}:</b> {text}</span>"
        )

    def set_exchange(self, user_text: str, jarvis_text: str):
        """Replaces transcript with the latest user↔JARVIS exchange."""
        self.text_box.clear()
        self.add_transcript("You", user_text)
        self.add_transcript("JARVIS", jarvis_text)


class SystemStatsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.stats_label = QLabel("Initializing system stats...")
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background-color: rgba(2, 13, 26, 150);
                font-family: 'Consolas', monospace;
                font-size: 11px;
                padding: 8px;
                border-left: 2px solid #ff9f00;
            }
        """)

        layout.addWidget(self.stats_label)
        self.setLayout(layout)

    def update_stats(self, cpu: float, ram: float, battery: str):
        self.stats_label.setText(f"CPU  {cpu:.0f}%   RAM  {ram:.0f}%   BAT  {battery}")


class MemoryPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Loading memory...")
        self.label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                background-color: rgba(2, 13, 26, 150);
                font-family: 'Consolas', monospace;
                font-size: 10px;
                padding: 6px 8px;
                border-left: 2px solid #00ff88;
            }
        """)

        layout.addWidget(self.label)
        self.setLayout(layout)

    def update_memory(self, name: str, city: str, sessions: int):
        name_str  = name    or "Unknown"
        city_str  = city    or "Unknown"
        self.label.setText(f"USER  {name_str}   CITY  {city_str}   SESSIONS  {sessions}")
