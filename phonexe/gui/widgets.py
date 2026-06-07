"""Reusable custom widgets for the phonexe GUI."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from . import theme


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

        # progress
        pen.setColor(QColor(theme.ACCENT))
        p.setPen(pen)
        span = int(360 * 16 * self._percent / 100)
        p.drawArc(x, y, side, side, 90 * 16, -span)

        # center text
        p.setPen(QColor(theme.TEXT))
        f = QFont()
        f.setPointSize(20)
        f.setBold(True)
        p.setFont(f)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._percent}%")
        p.end()


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {theme.BORDER}; background: {theme.BORDER};")
    line.setFixedHeight(1)
    return line
