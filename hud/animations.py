# Radar sweep widget and waveform bars for GLACIER MK3 HUD
# All drawing is done with QPainter — no SVG or HTML involved

import math
import random

from PyQt6.QtWidgets import QWidget, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPainterPath,
    QFont, QFontMetrics, QLinearGradient,
)

# Sweep: full 360° in 4500 ms → degrees added per 55 ms tick
_SWEEP_STEP = 360.0 / 4500.0 * 55.0      # ≈ 4.4°/tick

# Center-pulse period varies by status (ms)
_PULSE_MS = {'SPEAKING': 700, 'THINKING': 1200, 'LISTENING': 2200, 'IDLE': 3500}

_STATUS_SUB = {
    'LISTENING': 'WAKE WORD ARMED',
    'THINKING':  'PROCESSING REQUEST',
    'SPEAKING':  'VOICE SYNTHESIS LIVE',
    'IDLE':      'STANDBY — READY',
}


class RadarWidget(QWidget):
    """
    Full radar scope drawn via QPainter.
    Features: concentric rings, crosshair, decorative arcs, rotating sweep
    wedge, tick marks, cardinal labels N/E/S/W, pulsing center circle,
    four floating info chips, large status word overlay.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(280, 280)

        self._sweep   = 0.0   # current sweep angle, degrees CW from north
        self._tick_ms = 0     # accumulated ms — drives pulse phase
        self._status  = 'IDLE'

        # Large status word rendered as a transparent QLabel on top of the canvas
        self._status_lbl = QLabel(self)
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        self._status_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._sub_lbl = QLabel(self)
        self._sub_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self._sub_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Four corner info chips
        self._chips: dict[str, QLabel] = {}
        for pos, key, val in [
            ('tl', 'HDG',    '000°'),
            ('tr', 'PING',   '142ms'),
            ('bl', 'FLUX',   '3.142 GW'),
            ('br', 'UPLINK', 'OK'),
        ]:
            lbl = QLabel(f"{key}  {val}", self)
            lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self._chips[pos] = lbl

        self._apply_styles()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(55)

    # ── Public ─────────────────────────────────────────────────────────────

    def set_status(self, status: str):
        self._status = status.upper()
        self._status_lbl.setText(self._status)
        self._sub_lbl.setText(_STATUS_SUB.get(self._status, 'STANDBY — READY'))

    # ── Internal ────────────────────────────────────────────────────────────

    def _apply_styles(self):
        self.set_status(self._status)
        self._status_lbl.setStyleSheet(
            "background: transparent; color: #8CE1FF;"
            "font-family: 'Segoe UI', Arial, sans-serif;"
            "font-size: 52px; font-weight: 300; letter-spacing: 6px;"
        )
        self._sub_lbl.setStyleSheet(
            "background: transparent; color: #5BB8D7;"
            "font-family: 'Consolas', monospace; font-size: 9px; letter-spacing: 4px;"
        )
        chip_ss = (
            "background: rgba(8,18,30,180); color: #5BB8D7;"
            "font-family: 'Consolas', monospace; font-size: 9px; letter-spacing: 3px;"
            "padding: 2px 8px; border: 1px solid rgba(140,225,255,56);"
        )
        for lbl in self._chips.values():
            lbl.setStyleSheet(chip_ss)
            lbl.adjustSize()

    def _tick(self):
        self._sweep    = (self._sweep + _SWEEP_STEP) % 360.0
        self._tick_ms += 55
        hdg = int(self._sweep * 3) % 360
        self._chips['tl'].setText(f"HDG  {hdg:03d}°")
        self._chips['tl'].adjustSize()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        lw = int(w * 0.72)
        self._status_lbl.setFixedWidth(lw)
        self._status_lbl.setFixedHeight(70)
        self._status_lbl.move((w - lw) // 2, cy - 74)

        self._sub_lbl.setFixedWidth(lw)
        self._sub_lbl.setFixedHeight(20)
        self._sub_lbl.move((w - lw) // 2, cy + 6)

        mx = max(8, int(w * 0.04))
        my = max(4, int(h * 0.06))
        for pos, lbl in self._chips.items():
            lbl.adjustSize()
            cw = lbl.sizeHint().width() + 16
            lbl.setFixedSize(cw, 22)
            if   pos == 'tl': lbl.move(mx,          my)
            elif pos == 'tr': lbl.move(w - cw - mx, my)
            elif pos == 'bl': lbl.move(mx,          h - 22 - my)
            elif pos == 'br': lbl.move(w - cw - mx, h - 22 - my)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h   = self.width(), self.height()
        sz     = min(w, h)
        cx, cy = w / 2.0, h / 2.0
        sc     = sz / 600.0            # design SVG is 600×600

        p.translate(cx, cy)            # work in centre-origin coords

        r_outer = sc * 260
        radii   = [r_outer, sc * 200, sc * 150, sc * 100]

        # Concentric rings
        ring_cfg = [(64, None), (46, [6.0, 8.0]), (89, None), (46, [2.0, 6.0])]
        for r, (alpha, dash) in zip(radii, ring_cfg):
            pen = QPen(QColor(140, 225, 255, alpha), 1)
            if dash:
                pen.setStyle(Qt.PenStyle.CustomDashLine)
                pen.setDashPattern(dash)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(0, 0), r, r)

        # Decorative arcs top and bottom
        ar = sc * 170
        p.setPen(QPen(QColor(140, 225, 255, 217), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRectF(-ar, -ar, ar * 2, ar * 2)
        p.drawArc(arc_rect, int(55 * 16),  int(70 * 16))
        p.drawArc(arc_rect, int(235 * 16), int(70 * 16))

        # Crosshair lines (extend to widget edges, gap at outer ring)
        p.setPen(QPen(QColor(140, 225, 255, 102), 1))
        p.drawLine(QPointF(-cx,     0), QPointF(-r_outer, 0))
        p.drawLine(QPointF(r_outer, 0), QPointF(cx,       0))
        p.drawLine(QPointF(0, -cy),     QPointF(0, -r_outer))
        p.drawLine(QPointF(0, r_outer), QPointF(0,  cy))

        # Rotating sweep wedge — rotate painter CW, draw fixed northward wedge
        p.save()
        p.rotate(self._sweep)
        span  = 52.0
        n_pts = 26
        path  = QPainterPath()
        path.moveTo(0, 0)
        pts = [
            QPointF(r_outer * math.sin(math.radians(i / n_pts * span)),
                    -r_outer * math.cos(math.radians(i / n_pts * span)))
            for i in range(n_pts + 1)
        ]
        path.lineTo(pts[0])
        for pt in pts[1:]:
            path.lineTo(pt)
        path.closeSubpath()
        # Gradient: opaque at leading edge → transparent at trailing edge
        grad = QLinearGradient(pts[-1], pts[0])
        grad.setColorAt(0.0, QColor(140, 225, 255, 145))
        grad.setColorAt(0.5, QColor(140, 225, 255, 55))
        grad.setColorAt(1.0, QColor(140, 225, 255, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(path, QBrush(grad))
        p.restore()

        # Tick marks around outer ring (72 marks every 5°)
        p.setPen(QPen(QColor(140, 225, 255, 115), 0.7))
        for i in range(72):
            θ       = math.radians(i * 5)
            inner_r = r_outer - sc * (10 if i % 9 == 0 else 5)
            p.drawLine(
                QPointF(r_outer * math.sin(θ), -r_outer * math.cos(θ)),
                QPointF(inner_r * math.sin(θ), -inner_r * math.cos(θ)),
            )

        # Cardinal labels N / E / S / W
        font_c  = QFont('Consolas', max(9, int(sc * 13)))
        fm      = QFontMetrics(font_c)
        label_r = r_outer + sc * 18
        p.setFont(font_c)
        p.setPen(QPen(QColor(140, 225, 255, 179)))
        for text, deg in [('N', 0), ('E', 90), ('S', 180), ('W', 270)]:
            θ = math.radians(deg)
            lx = label_r * math.sin(θ)
            ly = -label_r * math.cos(θ)
            p.drawText(
                QPointF(lx - fm.horizontalAdvance(text) / 2, ly + fm.ascent() / 2),
                text,
            )

        # Pulsing center circle — speed driven by status
        period   = _PULSE_MS.get(self._status, 2200)
        sin_v    = math.sin((self._tick_ms % period) / period * math.pi)
        r_pulse  = sc * 60 * (0.85 + sin_v * 0.20)
        a_ring   = int(255 * (0.40 + sin_v * 0.60) * 0.65)
        p.setBrush(QBrush(QColor(140, 225, 255, 15)))
        p.setPen(QPen(QColor(140, 225, 255, a_ring), 1))
        p.drawEllipse(QPointF(0, 0), r_pulse, r_pulse)

        p.end()


class WaveformBarsWidget(QWidget):
    """
    72 bars whose amplitude is driven by JARVIS status.
    Algorithm mirrors shared.jsx useWaveform() exactly.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self._status = 'IDLE'
        self._levels = [0.05] * 72
        self._phase  = 0.0

        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(55)

    def set_status(self, status: str):
        self._status = status.upper()

    def _tick(self):
        self._phase += 0.18
        n  = 72
        c  = n / 2.0
        lvl = []
        for i in range(n):
            env = math.cos(abs(i - c) / c * math.pi * 0.5)
            s   = self._status
            if s == 'SPEAKING':
                a = ((math.sin(self._phase + i * 0.4) * 0.5 + 0.5) * env * 0.9
                     + (math.sin(self._phase * 2.1 + i * 0.7) * 0.5 + 0.5) * env * 0.3
                     + random.random() * 0.1)
                a = min(1.0, a * 0.85)
            elif s == 'LISTENING':
                a = 0.08 + random.random() * 0.25 + math.sin(self._phase * 0.4 + i * 0.2) * 0.04
            elif s == 'THINKING':
                pulse = (self._phase * 0.5) % n
                d = min(abs(i - pulse), abs(i - pulse + n), abs(i - pulse - n))
                a = math.exp(-d * d / 8) * 0.7 + 0.06
            else:
                a = 0.05 + math.sin(self._phase * 0.2 + i * 0.3) * 0.02 + random.random() * 0.02
            lvl.append(max(0.03, min(1.0, a)))
        self._levels = lvl
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h    = self.width(), self.height()
        n       = len(self._levels)
        gap     = 2.0
        bar_w   = max(1.0, (w - gap * (n - 1)) / n)
        avail_h = h - 8

        p.setPen(QPen(QColor(140, 225, 255, 56), 1))
        p.drawLine(QPointF(0, 3),     QPointF(w, 3))
        p.drawLine(QPointF(0, h - 4), QPointF(w, h - 4))

        grad = QLinearGradient(0, 0, 0, avail_h)
        grad.setColorAt(0, QColor(140, 225, 255, 220))
        grad.setColorAt(1, QColor(91,  184, 215, 160))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)

        for i, level in enumerate(self._levels):
            bh = max(2.0, level * avail_h)
            p.drawRect(QRectF(i * (bar_w + gap), 4 + avail_h - bh, bar_w, bh))
        p.end()


# Kept for import compatibility — not used in MK3
class ArcReactor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
