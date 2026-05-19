import sys
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt6.QtCore import Qt

class StatusPill(QWidget):
    def __init__(self, text: str, color: str):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        
        # Styles
        self.bg_color = color
        self.label.setStyleSheet(f"""
            QLabel {{
                color: #ffffff;
                background-color: {self.bg_color};
                border-radius: 12px;
                padding: 4px 12px;
                font-family: 'Inter', sans-serif;
                font-weight: bold;
                font-size: 10px;
            }}
        """)

class LiveTranscriptWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_box = QTextEdit()
        self.text_box.setReadOnly(True)
        self.text_box.setFrameStyle(0) # No border
        self.text_box.setStyleSheet("""
            QTextEdit {
                background-color: rgba(2, 13, 26, 180);
                color: #00e5ff;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                border: 1px solid rgba(0, 229, 255, 50);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout.addWidget(self.text_box)
        self.setLayout(layout)

    def add_transcript(self, speaker: str, text: str):
        """Adds a line to the transcript"""
        color = "#ffffff" if speaker.lower() == "user" else "#00e5ff"
        formatted_text = f"<span style='color: {color};'><b>{speaker.upper()}:</b> {text}</span>"
        self.text_box.append(formatted_text)

class SystemStatsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stats_label = QLabel("Initializing System Stats...")
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
        self.stats_label.setText(f"CPU: {cpu}% | RAM: {ram}% | BAT: {battery}")
