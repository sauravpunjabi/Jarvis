import sys
import os
import psutil

# Prevent circular import because the script is named hud.py inside a folder named hud.
# We remove the script's directory from sys.path and add the project root.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if current_dir in sys.path:
    sys.path.remove(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from hud.widgets import StatusPill, LiveTranscriptWidget, SystemStatsWidget
from hud.animations import ArcReactor

# Colors
BG_COLOR = "#020d1a"
ACCENT_COLOR = "#00e5ff"
WARN_COLOR = "#ff9f00"
SUCCESS_COLOR = "#00ff88"

class SystemStatsThread(QThread):
    """Runs in a separate thread to fetch system stats without blocking the GUI."""
    stats_updated = pyqtSignal(float, float, str)

    def run(self):
        while True:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            
            try:
                battery_info = psutil.sensors_battery()
                battery = f"{battery_info.percent}%" if battery_info else "N/A"
            except Exception:
                battery = "N/A"
                
            self.stats_updated.emit(cpu, ram, battery)
            self.msleep(1000) # Wait 1 second before next fetch to respect the 2s timer effectively (1s interval + sleep)


class JarvisHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configure Frameless, Transparent, Always-on-Top Window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Set geometry (Top Right Corner of the screen, leaving some margin)
        self.setGeometry(100, 100, 400, 500)
        
        # Central Widget & Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        # --- TOP SECTION: Arc Reactor & Status Pills ---
        self.top_layout = QHBoxLayout()
        
        # Arc Reactor Animation
        self.arc_reactor = ArcReactor()
        self.top_layout.addWidget(self.arc_reactor)
        
        # Spacer
        self.top_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Status Pills Layout (Vertical stacking of pills)
        self.status_layout = QVBoxLayout()
        
        self.status_idle = StatusPill("IDLE", "rgba(0, 229, 255, 50)")
        self.status_listening = StatusPill("LISTENING", "rgba(255, 159, 0, 50)")
        self.status_thinking = StatusPill("THINKING", "rgba(0, 255, 136, 50)")
        self.status_speaking = StatusPill("SPEAKING", "rgba(0, 229, 255, 150)")
        
        # Hide all except idle initially
        self.status_listening.hide()
        self.status_thinking.hide()
        self.status_speaking.hide()
        
        self.status_layout.addWidget(self.status_idle)
        self.status_layout.addWidget(self.status_listening)
        self.status_layout.addWidget(self.status_thinking)
        self.status_layout.addWidget(self.status_speaking)
        
        self.top_layout.addLayout(self.status_layout)
        self.main_layout.addLayout(self.top_layout)
        
        # --- MIDDLE SECTION: Live Transcript ---
        self.transcript_widget = LiveTranscriptWidget()
        self.main_layout.addWidget(self.transcript_widget)
        
        # --- BOTTOM SECTION: System Stats ---
        self.stats_widget = SystemStatsWidget()
        self.main_layout.addWidget(self.stats_widget)
        
        # --- INITIALIZATION ---
        self.init_threads()
        
        print("[HUD] Iron Man HUD initialized and running.")
        
    def init_threads(self):
        """Starts the QThread for system monitoring."""
        self.stats_thread = SystemStatsThread()
        self.stats_thread.stats_updated.connect(self.stats_widget.update_stats)
        self.stats_thread.start()
        
    def set_status(self, status: str):
        """Updates the active status pill."""
        self.status_idle.hide()
        self.status_listening.hide()
        self.status_thinking.hide()
        self.status_speaking.hide()
        
        status = status.upper()
        if status == "LISTENING":
            self.status_listening.show()
        elif status == "THINKING":
            self.status_thinking.show()
        elif status == "SPEAKING":
            self.status_speaking.show()
        else:
            self.status_idle.show()
            
    def update_transcript(self, speaker: str, text: str):
        self.transcript_widget.add_transcript(speaker, text)

# Allows running the HUD independently for testing
def main():
    app = QApplication(sys.argv)
    
    # Get screen geometry to place HUD in top right
    screen = app.primaryScreen().geometry()
    hud = JarvisHUD()
    
    # Position: Top Right with 20px padding
    x_pos = screen.width() - hud.width() - 20
    y_pos = 20
    hud.move(x_pos, y_pos)
    
    hud.show()
    
    # Test script: Update transcript and status over time
    QTimer.singleShot(2000, lambda: hud.set_status("LISTENING"))
    QTimer.singleShot(2000, lambda: hud.update_transcript("User", "Hey JARVIS, what is the system status?"))
    QTimer.singleShot(4000, lambda: hud.set_status("THINKING"))
    QTimer.singleShot(6000, lambda: hud.set_status("SPEAKING"))
    QTimer.singleShot(6000, lambda: hud.update_transcript("JARVIS", "All systems are operating at optimal levels, sir."))
    QTimer.singleShot(9000, lambda: hud.set_status("IDLE"))
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
