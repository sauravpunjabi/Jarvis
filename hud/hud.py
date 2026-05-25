# GLACIER MK3 — full-screen JARVIS HUD built with PyQt6
# Layout: top bar (64px) | 3-column main (left rail / radar center / right rail) | bottom bar (80px)

import sys
import os
import queue
from datetime import datetime, timezone

import psutil

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QFont,
)

from hud.animations import RadarWidget, WaveformBarsWidget
from hud.widgets import (
    IdentityPanel, CommLogPanel, SystemStatPanel,
    ConflictPanel, MarketPanel, GeoPanel,
    CYAN, CYAN_S, CYAN_D, AMBER, GREEN, PAPER, MONO, DISPLAY,
)

# ── System stats thread ───────────────────────────────────────────────────────

class SystemStatsThread(QThread):
    # Emits (cpu%, ram%, battery_str, gpu_temp_placeholder)
    stats_updated = pyqtSignal(float, float, str, float)

    def run(self):
        while True:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            try:
                b   = psutil.sensors_battery()
                bat = f"{b.percent:.0f}%" if b else "N/A"
            except Exception:
                bat = "N/A"
            self.stats_updated.emit(cpu, ram, bat, 55.0)
            self.msleep(1000)


# ── Background canvas ─────────────────────────────────────────────────────────

class _BackgroundCanvas(QWidget):
    """Paints the MK3 dark blue background + radial glow + subtle 60px grid."""

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()

        # Solid base
        p.fillRect(0, 0, w, h, QColor(5, 11, 20))

        # Centre-right radial glow
        rg = QRadialGradient(QPointF(w * 0.5, h * 0.6), min(w, h) * 0.65)
        rg.setColorAt(0, QColor(30, 100, 160, 46))
        rg.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, w, h, rg)

        # Bottom-left corner glow
        rg2 = QRadialGradient(QPointF(0, h), min(w, h) * 0.5)
        rg2.setColorAt(0, QColor(20, 50, 90, 76))
        rg2.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, w, h, rg2)

        # 60 px grid overlay
        p.setPen(QPen(QColor(140, 225, 255, 10), 1))
        step = 60
        for x in range(0, w, step):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            p.drawLine(0, y, w, y)

        p.end()


# ── Top bar ───────────────────────────────────────────────────────────────────

class _TopBar(QWidget):
    """64 px top bar: wordmark + UTC clock | clickable status pills | meta + logo | window controls."""

    _STATES = ['LISTENING', 'THINKING', 'SPEAKING', 'IDLE']

    # Signals emitted when the user clicks the window-control buttons
    close_clicked    = pyqtSignal()
    minimize_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)

        root = QHBoxLayout(self)
        root.setContentsMargins(28, 0, 28, 0)
        root.setSpacing(0)

        # Brand: wordmark + system stamp with live clock
        brand = QVBoxLayout()
        brand.setSpacing(2)
        brand.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._wordmark = QLabel()
        self._wordmark.setTextFormat(Qt.TextFormat.RichText)
        self._wordmark.setText(
            f"<span style='color:{CYAN};font-family:Segoe UI,Arial;font-size:28px;"
            f"font-weight:600;letter-spacing:2px;'>JARVIS"
            f"<span style='color:{CYAN_D};'>-</span>MK3</span>"
        )
        self._wordmark.setStyleSheet("background: transparent; border: none;")

        self._stamp = QLabel()
        self._stamp.setStyleSheet(
            f"color: {CYAN_S}; font-family: {MONO}; font-size: 10px;"
            "letter-spacing: 3px; background: transparent; border: none;"
        )
        brand.addWidget(self._wordmark)
        brand.addWidget(self._stamp)
        root.addLayout(brand)
        root.addStretch()

        # Status pills
        pills_wrap = QWidget()
        pills_wrap.setStyleSheet("background: transparent; border: none;")
        pills_lay = QHBoxLayout(pills_wrap)
        pills_lay.setContentsMargins(0, 0, 0, 0)
        pills_lay.setSpacing(6)
        self._pills: dict[str, QPushButton] = {}
        for s in self._STATES:
            btn = QPushButton(s)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, st=s: self._pill_clicked(st))
            self._pills[s] = btn
            pills_lay.addWidget(btn)
        root.addWidget(pills_wrap)
        root.addStretch()

        # Meta labels
        meta = QVBoxLayout()
        meta.setSpacing(2)
        meta.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        for key, val in [("BIO-SIGNATURE:", "STABLE"), ("ENCRYPTION:", "256-BIT AES")]:
            row = QHBoxLayout()
            k = QLabel(key)
            v = QLabel(val)
            k.setStyleSheet(f"color:{CYAN_S};font-family:{MONO};font-size:10px;letter-spacing:2px;background:transparent;border:none;")
            v.setStyleSheet(f"color:{PAPER};font-family:{MONO};font-size:10px;letter-spacing:2px;font-weight:500;background:transparent;border:none;")
            row.addWidget(k)
            row.addSpacing(6)
            row.addWidget(v)
            row.addStretch()
            meta.addLayout(row)
        root.addLayout(meta)
        root.addSpacing(18)

        # Logo (hexagonal node)
        logo = QLabel("⬡")
        logo.setStyleSheet(f"color:{CYAN};font-size:30px;background:transparent;border:none;")
        root.addWidget(logo)

        # Window control buttons — minimize and close
        root.addSpacing(20)
        _wc_ss = (
            "QPushButton{{"
            "color:{fg};background:transparent;border:1px solid {border};"
            "font-family:{mono};font-size:13px;font-weight:600;"
            "min-width:28px;max-width:28px;min-height:28px;max-height:28px;"
            "border-radius:14px;}}"
            "QPushButton:hover{{background:{hover};border-color:{fg};}}"
        )
        btn_min = QPushButton("─")
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setToolTip("Minimise")
        btn_min.setStyleSheet(
            _wc_ss.format(fg=CYAN_S, border="rgba(140,225,255,56)",
                          hover="rgba(140,225,255,20)", mono=MONO)
        )
        btn_min.clicked.connect(self.minimize_clicked.emit)
        root.addWidget(btn_min)

        root.addSpacing(6)
        btn_cls = QPushButton("✕")
        btn_cls.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cls.setToolTip("Close")
        btn_cls.setStyleSheet(
            _wc_ss.format(fg="#CC4444", border="rgba(204,68,68,56)",
                          hover="rgba(204,68,68,25)", mono=MONO)
        )
        btn_cls.clicked.connect(self.close_clicked.emit)
        root.addWidget(btn_cls)

        # Bottom rule
        self._rule = QWidget(self)
        self._rule.setStyleSheet(f"background: rgba(140,225,255,56);")
        self._rule.setFixedHeight(1)

        # Clock
        self._clock = QTimer(self)
        self._clock.timeout.connect(self._tick_clock)
        self._clock.start(1000)
        self._tick_clock()

        self._set_active('IDLE')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rule.setGeometry(0, self.height() - 1, self.width(), 1)

    def _tick_clock(self):
        t = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self._stamp.setText(f"SYSTEM: STARK-7.2.4  ·  {t} UTC")

    def _pill_style(self, active: bool) -> str:
        if active:
            return (
                f"QPushButton{{color:{GREEN};background:transparent;"
                f"border:1px solid {GREEN};"
                f"font-family:{MONO};font-size:10px;letter-spacing:3px;"
                "padding:6px 14px;border-radius:999px;}}"
            )
        return (
            f"QPushButton{{color:{CYAN_S};background:transparent;"
            "border:1px solid rgba(140,225,255,56);"
            f"font-family:{MONO};font-size:10px;letter-spacing:3px;"
            "padding:6px 14px;border-radius:999px;}}"
            f"QPushButton:hover{{color:{PAPER};border-color:{CYAN};}}"
        )

    def _set_active(self, status: str):
        for s, btn in self._pills.items():
            btn.setStyleSheet(self._pill_style(s == status))

    def _pill_clicked(self, status: str):
        self._set_active(status)

    def set_status(self, status: str):
        self._set_active(status.upper())


# ── Bottom action bar ─────────────────────────────────────────────────────────

class _BottomBar(QWidget):
    """80 px action bar: ANALYZE · DEFENSE · [MIC] · NETWORK · OVERRIDE."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)

        # Top rule
        self._rule = QWidget(self)
        self._rule.setStyleSheet("background: rgba(140,225,255,56);")
        self._rule.setFixedHeight(1)
        self._rule.move(0, 0)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 1, 0, 0)
        root.setSpacing(0)
        root.addStretch()

        actions = [
            ("ANALYZE",  "⟁",  CYAN,  False),
            ("DEFENSE",  "⛨",  CYAN,  False),
            (None,       "🎤", CYAN,  True),    # circular mic
            ("NETWORK",  "⊕",  CYAN,  False),
            ("OVERRIDE", "⚠",  AMBER, False),
        ]
        for label, icon, color, is_mic in actions:
            if is_mic:
                btn = QPushButton(icon)
                btn.setFixedSize(56, 56)
                btn.setStyleSheet(
                    f"QPushButton{{color:{color};background:rgba(140,225,255,20);"
                    f"border:1px solid {color};border-radius:28px;font-size:20px;}}"
                    f"QPushButton:hover{{background:rgba(140,225,255,40);}}"
                )
            else:
                btn = QPushButton(f"{icon}\n{label}")
                btn.setFixedSize(68, 56)
                btn.setStyleSheet(
                    f"QPushButton{{color:{color};background:transparent;border:none;"
                    f"font-family:{MONO};font-size:10px;letter-spacing:3px;}}"
                    f"QPushButton:hover{{color:{PAPER};}}"
                )
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            root.addWidget(btn)
            root.addSpacing(36)

        root.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rule.setFixedWidth(self.width())


# ── Main HUD window ───────────────────────────────────────────────────────────

class JarvisHUD(QMainWindow):
    """
    GLACIER MK3 full-screen HUD.
    Public API (same contract as the old side-panel HUD):
        set_status(status)
        set_transcript(user_text, jarvis_text)
        update_memory(name, city, sessions)
    All three are thread-safe — they enqueue and are applied on the Qt main thread.
    """

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # Solid dark background — no need for translucency on a full-screen HUD
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Thread-safe command queue drained every 50 ms on the main thread
        self._queue = queue.Queue()
        self._poll  = QTimer(self)
        self._poll.timeout.connect(self._drain_queue)
        self._poll.start(50)

        # ── Root widget ───────────────────────────────────────────────────
        canvas = _BackgroundCanvas()
        self.setCentralWidget(canvas)

        root = QVBoxLayout(canvas)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        self._topbar = _TopBar()
        self._topbar.close_clicked.connect(self.close)
        self._topbar.minimize_clicked.connect(self.showMinimized)
        root.addWidget(self._topbar)

        # Main 3-column section
        main_w = QWidget()
        main_w.setStyleSheet("background: transparent;")
        main_lay = QHBoxLayout(main_w)
        main_lay.setContentsMargins(24, 16, 24, 16)
        main_lay.setSpacing(20)
        root.addWidget(main_w, 1)

        # Left rail (fixed 280 px)
        left = QWidget()
        left.setFixedWidth(280)
        left.setStyleSheet("background: transparent;")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(14)
        self._identity = IdentityPanel()
        self._commlog  = CommLogPanel()
        self._sysstat  = SystemStatPanel()
        for w in (self._identity, self._commlog, self._sysstat):
            left_lay.addWidget(w)
        left_lay.addStretch()
        main_lay.addWidget(left)

        # Centre column (radar + waveform + audio meta label)
        centre = QWidget()
        centre.setStyleSheet("background: transparent;")
        centre_lay = QVBoxLayout(centre)
        centre_lay.setContentsMargins(0, 0, 0, 0)
        centre_lay.setSpacing(4)
        self._radar    = RadarWidget()
        self._waveform = WaveformBarsWidget()
        self._audio_meta = QLabel(
            "AUDIO · IDLE   |   48 kHz · 24-bit · −24 dB   |   EN-GB / MALE · brian.v2"
        )
        self._audio_meta.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._audio_meta.setStyleSheet(
            f"color:{CYAN_S};font-family:{MONO};font-size:9px;"
            "letter-spacing:3px;background:transparent;"
        )
        centre_lay.addWidget(self._radar, 1)
        centre_lay.addWidget(self._waveform)
        centre_lay.addWidget(self._audio_meta)
        main_lay.addWidget(centre, 1)

        # Right rail (fixed 280 px)
        right = QWidget()
        right.setFixedWidth(280)
        right.setStyleSheet("background: transparent;")
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(14)
        self._conflict = ConflictPanel()
        self._market   = MarketPanel()
        self._geo      = GeoPanel()
        for w in (self._conflict, self._market, self._geo):
            right_lay.addWidget(w)
        right_lay.addStretch()
        main_lay.addWidget(right)

        # Bottom bar
        self._bottombar = _BottomBar()
        root.addWidget(self._bottombar)

        # System stats thread (real CPU / RAM / battery)
        self._stats_thread = SystemStatsThread()
        self._stats_thread.stats_updated.connect(self._sysstat.update_stats)
        self._stats_thread.start()

        print("[HUD] GLACIER MK3 online.")

    # ── Thread-safe public API ────────────────────────────────────────────────

    def set_status(self, status: str):
        self._queue.put(("status", status))

    def set_transcript(self, user_text: str, jarvis_text: str):
        self._queue.put(("transcript", (user_text, jarvis_text)))

    def update_memory(self, name: str, city: str, sessions: int):
        self._queue.put(("memory", (name, city, sessions)))

    # Backward-compatible alias used by older code paths
    def update_transcript(self, speaker: str, text: str):
        pass

    # ── Queue drain (main thread) ─────────────────────────────────────────────

    def _drain_queue(self):
        while not self._queue.empty():
            try:
                action, payload = self._queue.get_nowait()
                if action == "status":
                    self._apply_status(payload)
                elif action == "transcript":
                    self._commlog.set_exchange(payload[0], payload[1])
                elif action == "memory":
                    self._identity.update_identity(payload[0], payload[1], payload[2])
            except Exception:
                pass

    def _apply_status(self, status: str):
        s = status.upper()
        self._topbar.set_status(s)
        self._radar.set_status(s)
        self._waveform.set_status(s)
        direction = 'OUT' if s == 'SPEAKING' else 'IN' if s == 'LISTENING' else 'IDLE'
        self._audio_meta.setText(
            f"AUDIO · {direction}   |   48 kHz · 24-bit · −24 dB   |   EN-GB / MALE · brian.v2"
        )


# ── Standalone test ───────────────────────────────────────────────────────────

def main():
    app    = QApplication(sys.argv)
    screen = app.primaryScreen().geometry()
    hud    = JarvisHUD()
    hud.setGeometry(0, 0, screen.width(), screen.height())
    hud.update_memory("Saurav", "Dhule", 42)
    hud.set_status("LISTENING")
    hud.show()

    QTimer.singleShot(2000, lambda: hud.set_transcript(
        "Hey JARVIS, what's the weather?", ""))
    QTimer.singleShot(3000, lambda: hud.set_status("THINKING"))
    QTimer.singleShot(5200, lambda: hud.set_status("SPEAKING"))
    QTimer.singleShot(5300, lambda: hud.set_transcript(
        "Hey JARVIS, what's the weather?",
        "Currently 31° and clear skies over Dhule, sir."))
    QTimer.singleShot(9000, lambda: hud.set_status("IDLE"))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
