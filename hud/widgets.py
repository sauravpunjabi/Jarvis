# Panel widgets for GLACIER MK3 HUD
# Each panel paints its own dark background + coloured border via paintEvent

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QPushButton,
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QLinearGradient, QFont

# ── Colour palette (oklch approximations) ────────────────────────────────────
CYAN   = "#8CE1FF"    # oklch(0.88 0.10 215)
CYAN_S = "#5BB8D7"    # oklch(0.72 0.08 215) soft
CYAN_D = "#3A8FAF"    # oklch(0.55 0.06 215) dim
AMBER  = "#D4A34B"    # oklch(0.80 0.16 70)
GREEN  = "#4DCC7A"    # oklch(0.82 0.20 145)
RED    = "#CC4444"    # oklch(0.68 0.22 25)
PAPER  = "#EEF5FA"    # oklch(0.96 0.02 220)
BG     = "#050B14"

MONO    = "'Consolas', monospace"
DISPLAY = "'Segoe UI', Arial, sans-serif"

# QColor versions for paintEvent drawing
_QCYAN    = QColor(140, 225, 255)
_QAMBER   = QColor(212, 163, 75)
_QGREEN   = QColor(77,  204, 122)
_QPANEL   = QColor(10,  22,  36,  160)
_QRULE    = QColor(140, 225, 255, 140)


# ── Base panel ────────────────────────────────────────────────────────────────

class MK3Panel(QWidget):
    """
    Dark translucent panel with a 3 px accent border.
    accent='cyan'  → 3 px left border (cyan)
    accent='amber' → 3 px right border (amber)
    All background and border drawing is in paintEvent for reliability.
    """

    def __init__(self, title: str, accent: str = 'cyan', parent=None):
        super().__init__(parent)
        self._accent     = accent
        self._accent_col = _QAMBER if accent == 'amber' else _QCYAN
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        align = Qt.AlignmentFlag.AlignRight if accent == 'amber' else Qt.AlignmentFlag.AlignLeft
        accent_hex = AMBER if accent == 'amber' else CYAN

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(6)

        self._head = QLabel(title)
        self._head.setAlignment(align)
        self._head.setStyleSheet(
            f"color: {accent_hex}; font-family: {MONO}; font-size: 10px;"
            "letter-spacing: 3px; background: transparent; border: none; padding: 0;"
        )
        root.addWidget(self._head)

        self._body = QWidget()
        self._body.setStyleSheet("background: transparent; border: none;")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(4)
        root.addWidget(self._body)

    def body(self) -> QVBoxLayout:
        return self._body_layout

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()

        # Dark semi-transparent fill
        p.fillRect(0, 0, w, h, _QPANEL)

        # Outer 1 px rule
        p.setPen(QPen(_QRULE, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(0, 0, w - 1, h - 1)

        # Thick accent border
        if self._accent == 'amber':
            p.fillRect(w - 3, 0, 3, h, _QAMBER)
        else:
            p.fillRect(0, 0, 3, h, _QCYAN)

        p.end()


# ── Identity panel ────────────────────────────────────────────────────────────

class IdentityPanel(MK3Panel):
    def __init__(self, parent=None):
        super().__init__("identity_matrix", parent=parent)

        self._name = QLabel("SAURAV")
        self._name.setStyleSheet(
            f"color: {PAPER}; font-family: {DISPLAY}; font-size: 20px;"
            "font-weight: 500; background: transparent; border: none; margin: 4px 0 6px;"
        )
        self.body().addWidget(self._name)

        self._loc      = self._dl_row("LOC:",       "DHULE, IN")
        self._sessions = self._dl_row("SESSIONS:",  "0")
        self._clear    = self._dl_row("CLEARANCE:", "LEVEL 7", val_color=AMBER)
        for row in (self._loc, self._sessions, self._clear):
            self.body().addWidget(row)

    @staticmethod
    def _dl_row(key: str, val: str, val_color: str = PAPER) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: transparent; border: none;")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        k = QLabel(key)
        k.setStyleSheet(f"color: {CYAN_S}; font-family: {MONO}; font-size: 11px; background: transparent; border: none;")
        v = QLabel(val)
        v.setStyleSheet(f"color: {val_color}; font-family: {MONO}; font-size: 11px; background: transparent; border: none;")
        v.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(k)
        lay.addStretch()
        lay.addWidget(v)
        return row

    def update_identity(self, name: str, city: str, sessions: int):
        self._name.setText((name or "UNKNOWN").upper())
        loc_lbl = self._loc.findChildren(QLabel)[1]
        ses_lbl = self._sessions.findChildren(QLabel)[1]
        loc_lbl.setText(f"{(city or 'UNKNOWN').upper()}")
        ses_lbl.setText(f"{sessions:,}")


# ── Comm log panel ────────────────────────────────────────────────────────────

class CommLogPanel(MK3Panel):
    def __init__(self, parent=None):
        super().__init__("▶  comm_log", parent=parent)

        lbl_ss = (
            f"color: {CYAN_S}; font-family: {MONO}; font-size: 9px;"
            "letter-spacing: 3px; background: transparent; border: none;"
        )
        self._user_head = QLabel("LAST USER COMMAND")
        self._user_head.setStyleSheet(lbl_ss)
        self.body().addWidget(self._user_head)

        self._user_box = QLabel('"Awaiting input."')
        self._user_box.setWordWrap(True)
        self._user_box.setStyleSheet(
            f"color: {CYAN}; font-family: {MONO}; font-size: 11px; line-height: 1.4;"
            "background: rgba(140,225,255,10); border: 1px solid rgba(140,225,255,89);"
            "padding: 6px 8px;"
        )
        self.body().addWidget(self._user_box)

        self._jarvis_head = QLabel("JARVIS RESPONSE")
        self._jarvis_head.setStyleSheet(lbl_ss + "margin-top: 6px;")
        self.body().addWidget(self._jarvis_head)

        self._jarvis_box = QLabel('"Standing by, sir."')
        self._jarvis_box.setWordWrap(True)
        self._jarvis_box.setStyleSheet(
            f"color: {GREEN}; font-family: {MONO}; font-size: 11px; line-height: 1.4;"
            "background: rgba(77,204,122,10); border: 1px solid rgba(77,204,122,89);"
            "padding: 6px 8px;"
        )
        self.body().addWidget(self._jarvis_box)

    def set_exchange(self, user_text: str, jarvis_text: str):
        self._user_box.setText(f'"{user_text}"' if user_text else '"Awaiting input."')
        self._jarvis_box.setText(f'"{jarvis_text}"' if jarvis_text else '"Standing by, sir."')


# ── Stat bar helper ───────────────────────────────────────────────────────────

class _TrackWidget(QWidget):
    """4 px filled progress track painted with QPainter."""

    _COLORS = {
        'cyan':  QColor(140, 225, 255),
        'amber': QColor(212, 163, 75),
        'green': QColor(77,  204, 122),
    }

    def __init__(self, color: str = 'cyan', parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self._pct   = 0.0
        self._color = self._COLORS.get(color, self._COLORS['cyan'])

    def set_pct(self, pct: float):
        self._pct = max(0.0, min(1.0, pct))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(140, 225, 255, 26))
        fw = int(w * self._pct)
        if fw > 0:
            p.fillRect(0, 0, fw, h, self._color)
        p.end()


class _StatBar(QWidget):
    def __init__(self, label: str, unit: str, color: str, parent=None):
        super().__init__(parent)
        self._unit  = unit
        self.setStyleSheet("background: transparent; border: none;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 3, 0, 3)
        lay.setSpacing(2)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"color: {CYAN_S}; font-family: {MONO}; font-size: 10px; background: transparent; border: none;")
        self._val = QLabel(f"0{unit}")
        self._val.setStyleSheet(f"color: {PAPER}; font-family: {MONO}; font-size: 10px; background: transparent; border: none;")
        row.addWidget(self._lbl)
        row.addStretch()
        row.addWidget(self._val)
        lay.addLayout(row)

        self._track = _TrackWidget(color)
        lay.addWidget(self._track)

    def set_value(self, value: float, pct: float | None = None):
        self._val.setText(f"{value:.0f}{self._unit}")
        p = pct if pct is not None else min(100.0, value)
        self._track.set_pct(p / 100.0)


class SystemStatPanel(MK3Panel):
    def __init__(self, parent=None):
        super().__init__("system_psutil", parent=parent)
        self._cpu  = _StatBar("CPU_LOAD",  '%',  'cyan')
        self._ram  = _StatBar("RAM_USAGE", 'GB', 'amber')
        self._temp = _StatBar("GPU_TEMP",  '°C', 'cyan')
        self._bat  = _StatBar("BATTERY",   '%',  'green')
        for bar in (self._cpu, self._ram, self._temp, self._bat):
            self.body().addWidget(bar)

    def update_stats(self, cpu: float, ram_pct: float, battery: str, temp: float = 55.0):
        self._cpu.set_value(cpu)
        ram_gb = ram_pct / 100.0 * 16.0
        self._ram.set_value(ram_gb, pct=ram_pct)
        self._temp.set_value(temp, pct=temp / 90.0 * 100.0)
        try:
            bat_val = float(battery.replace('%', '').strip())
        except (ValueError, AttributeError):
            bat_val = 0.0
        self._bat.set_value(bat_val)


# ── Conflict panel ────────────────────────────────────────────────────────────

_CONFLICTS_SHORT = [
    ("EASTERN",  "RED ALERT",  RED),
    ("HORN",     "UNSTABLE",   AMBER),
    ("LEVANT",   "UNSTABLE",   AMBER),
]


class ConflictPanel(MK3Panel):
    def __init__(self, parent=None):
        super().__init__("conflict_scope", accent='amber', parent=parent)
        align_r = Qt.AlignmentFlag.AlignRight

        self._risk_head = QLabel("RISK_LEVEL")
        self._risk_head.setAlignment(align_r)
        self._risk_head.setStyleSheet(
            f"color: {CYAN_S}; font-family: {MONO}; font-size: 9px;"
            "letter-spacing: 3px; background: transparent; border: none;"
        )

        self._risk_lbl = QLabel("ELEVATED (HIGH)")
        self._risk_lbl.setAlignment(align_r)
        self._risk_lbl.setStyleSheet(
            f"color: {AMBER}; font-family: {DISPLAY}; font-size: 17px;"
            "font-weight: 500; background: transparent; border: none; letter-spacing: 1px;"
        )

        self._hot_head = QLabel("GLOBAL HOTSPOTS")
        self._hot_head.setAlignment(align_r)
        self._hot_head.setStyleSheet(self._risk_head.styleSheet() + "margin-top: 6px;")

        for w in (self._risk_head, self._risk_lbl, self._hot_head):
            self.body().addWidget(w)

        for region, label, color in _CONFLICTS_SHORT:
            row = QLabel(
                f"{region}-1:  "
                f"<span style='color:{color};font-weight:600'>{label}</span>"
            )
            row.setTextFormat(Qt.TextFormat.RichText)
            row.setAlignment(align_r)
            row.setStyleSheet(
                f"color: {PAPER}; font-family: {MONO}; font-size: 10px;"
                "background: transparent; border: none; letter-spacing: 1px;"
            )
            self.body().addWidget(row)


# ── Market panel ──────────────────────────────────────────────────────────────

class MarketPanel(MK3Panel):
    def __init__(self, parent=None):
        super().__init__("market_commodities", parent=parent)

        outer = QHBoxLayout()
        outer.setSpacing(12)

        for lbl_text, val, delta in [
            ("BRENT_CRUDE",  "$78.42",    "+1.24%"),
            ("GOLD_SPOT",    "$2,042.10", "+0.80%"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            h = QLabel(lbl_text)
            h.setStyleSheet(f"color: {CYAN_S}; font-family: {MONO}; font-size: 9px; letter-spacing: 2px; background: transparent; border: none;")
            v = QLabel(val)
            v.setStyleSheet(f"color: {GREEN}; font-family: {DISPLAY}; font-size: 18px; font-weight: 500; background: transparent; border: none;")
            d = QLabel(delta)
            d.setStyleSheet(f"color: {GREEN}; font-family: {MONO}; font-size: 10px; background: transparent; border: none;")
            for w in (h, v, d):
                col.addWidget(w)
            outer.addLayout(col)

        wrap = QWidget()
        wrap.setStyleSheet("background: transparent; border: none;")
        wrap.setLayout(outer)
        self.body().addWidget(wrap)


# ── Geo panel ─────────────────────────────────────────────────────────────────

class GeoPanel(MK3Panel):
    def __init__(self, parent=None):
        super().__init__("geo_positional", parent=parent)

        head = QLabel("ALTITUDE")
        head.setStyleSheet(
            f"color: {CYAN_S}; font-family: {MONO}; font-size: 9px;"
            "letter-spacing: 3px; background: transparent; border: none;"
        )
        self._alt = QLabel("12,000 FT")
        self._alt.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._alt.setStyleSheet(
            f"color: {PAPER}; font-family: {DISPLAY}; font-size: 24px;"
            "font-weight: 500; background: transparent; border: none;"
        )
        coord = QLabel("LAT:  21.1458° N\nLONG: 79.0882° E")
        coord.setStyleSheet(
            f"color: {PAPER}; font-family: {MONO}; font-size: 10px;"
            "background: transparent; border: none; letter-spacing: 1px; margin-top: 6px;"
        )
        for w in (head, self._alt, coord):
            self.body().addWidget(w)


# ── Legacy aliases — kept so old imports don't break ──────────────────────────

class StatusPill(QWidget):
    def __init__(self, text: str, color: str, parent=None):
        super().__init__(parent)

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    def set_speaking(self, _: bool):
        pass

class SystemStatsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    def update_stats(self, *_):
        pass

class MemoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    def update_memory(self, *_):
        pass
