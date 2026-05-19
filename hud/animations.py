from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QRadialGradient
from PyQt6.QtCore import Qt, QTimer

class ArcReactor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self._pulse_radius = 20.0
        self._opacity = 1.0
        
        # QTimer for continuous pulse animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_pulse)
        self.timer.start(50) # 50 ms tick
        
        self.growing = True

    def update_pulse(self):
        if self.growing:
            self._pulse_radius += 1.0
            self._opacity -= 0.05
            if self._pulse_radius > 45.0:
                self.growing = False
        else:
            self._pulse_radius -= 1.0
            self._opacity += 0.05
            if self._pulse_radius < 20.0:
                self.growing = True
                
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Center coordinates
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        # Base ring
        pen = QPen(QColor("#00e5ff"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(int(center_x - 30), int(center_y - 30), 60, 60)
        
        # Pulsing ring
        pulse_color = QColor("#00e5ff")
        pulse_color.setAlphaF(max(0.0, min(1.0, self._opacity)))
        pen.setColor(pulse_color)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawEllipse(int(center_x - self._pulse_radius), 
                            int(center_y - self._pulse_radius), 
                            int(self._pulse_radius * 2), 
                            int(self._pulse_radius * 2))
                            
        # Core
        gradient = QRadialGradient(center_x, center_y, 15)
        gradient.setColorAt(0, QColor("#ffffff"))
        gradient.setColorAt(1, QColor("#00e5ff"))
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(center_x - 15), int(center_y - 15), 30, 30)
