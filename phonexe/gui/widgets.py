"""Reusable custom widgets for the phonexe GUI."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from . import theme

_AVATAR_COLORS = ["#22d3ee", "#34d399", "#a78bfa", "#f472b6", "#fbbf24",
                  "#f87171", "#60a5fa", "#fb923c"]


def avatar_pixmap(text: str, size: int = 40) -> QPixmap:
    """Circular avatar with the first letter of *text* on a stable color."""
    letter = (text.strip()[:1] or "?").upper()
    color = _AVATAR_COLORS[sum(map(ord, text)) % len(_AVATAR_COLORS)] if text \
        else _AVATAR_COLORS[0]
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    p.drawEllipse(0, 0, size, size)
    p.setPen(QColor("#0a0e1a"))
    f = QFont("Arial", int(size * 0.42))
    f.setBold(True)
    p.setFont(f)
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, letter)
    p.end()
    return pix


class StatCard(QFrame):
    """A single dashboard metric card: big value + label, accent colored."""

    def __init__(self, value: str, label: str, color: str):
        super().__init__()
        self.setObjectName("statCard")
        self.setMinimumHeight(92)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("statValue")
        self.value_lbl.setStyleSheet(f"color: {color};")

        self.label_lbl = QLabel(label)
        self.label_lbl.setObjectName("statLabel")

        lay.addWidget(self.value_lbl)
        lay.addWidget(self.label_lbl)

    def set_value(self, value: str, label: str) -> None:
        self.value_lbl.setText(value)
        self.label_lbl.setText(label)


class Donut(QWidget):
    """A simple painted progress ring with a percentage label."""

    def __init__(self, percent: int = 0, caption: str = ""):
        super().__init__()
        self._percent = percent
        self._caption = caption
        self.setMinimumSize(150, 150)

    def set_percent(self, percent: int, caption: str = "") -> None:
        self._percent = max(0, min(100, percent))
        self._caption = caption
        self.update()

    def paintEvent(self, _event):  # noqa: N802 (Qt naming)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 16
        x = (self.width() - side) // 2
        y = (self.height() - side) // 2
        thickness = 12

        # track
        pen = QPen(QColor(theme.BORDER), thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(x, y, side, side, 0, 360 * 16)

        # progress + cyan glow
        span = int(360 * 16 * self._percent / 100)
        glow = QColor(theme.ACCENT)
        for gw, alpha in ((thickness + 10, 40), (thickness + 5, 70)):
            glow.setAlpha(alpha)
            gpen = QPen(glow, gw)
            gpen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(gpen)
            p.drawArc(x, y, side, side, 90 * 16, -span)
        pen.setColor(QColor(theme.ACCENT))
        p.setPen(pen)
        p.drawArc(x, y, side, side, 90 * 16, -span)

        # center text
        p.setPen(QColor(theme.TEXT))
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._percent}%")
        p.end()


class BarChart(QWidget):
    """Simple horizontal bar chart: list of (label, value)."""

    def __init__(self, data: list[tuple[str, int]] | None = None):
        super().__init__()
        self._data = data or []
        self.setMinimumHeight(150)

    def set_data(self, data: list[tuple[str, int]]):
        self._data = data
        self.update()

    def paintEvent(self, _e):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._data:
            p.end()
            return
        rtl = self.layoutDirection() == Qt.LayoutDirection.RightToLeft
        peak = max(v for _, v in self._data) or 1
        n = len(self._data)
        gap = 10
        bw = (self.width() - gap * (n + 1)) / n
        base_y = self.height() - 22
        max_h = base_y - 10
        p.setFont(QFont("Arial", 8))
        for i, (label, val) in enumerate(self._data):
            x = gap + i * (bw + gap)
            h = max_h * val / peak
            y = base_y - h
            grad = QLinearGradient(0, y, 0, base_y)
            grad.setColorAt(0, QColor(theme.ACCENT))
            grad.setColorAt(1, QColor(theme.ACCENT_DIM))
            path = QPainterPath()
            path.addRoundedRect(QRectF(x, y, bw, h), 5, 5)
            p.fillPath(path, QBrush(grad))
            p.setPen(QColor(theme.TEXT))
            p.drawText(QRectF(x - gap / 2, y - 16, bw + gap, 14),
                       Qt.AlignmentFlag.AlignCenter, f"{val:,}")
            p.setPen(QColor(theme.TEXT_DIM))
            p.drawText(QRectF(x - gap / 2, base_y + 4, bw + gap, 16),
                       Qt.AlignmentFlag.AlignCenter, label[:12])
        p.end()


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {theme.BORDER}; background: {theme.BORDER};")
    line.setFixedHeight(1)
    return line
