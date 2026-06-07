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

_AVATAR_COLORS = ["#4FE3E0", "#24A8FF", "#21D07A", "#F7B731", "#FF5B5B",
                  "#a78bfa", "#60a5fa", "#fb923c"]


def apply_glow(widget, color: str = None, blur: int = 24, alpha: int = 60):
    """Attach a soft cyan glow (drop shadow, no offset) to a widget."""
    from PyQt6.QtWidgets import QGraphicsDropShadowEffect

    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(blur)
    eff.setOffset(0, 0)
    c = QColor(color or theme.ACCENT)
    c.setAlpha(alpha)
    eff.setColor(c)
    widget.setGraphicsEffect(eff)


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


class PhoneOutline(QWidget):
    """A realistic, screen-lit smartphone mockup (titanium frame + glow)."""

    def __init__(self, glow: str = None):
        super().__init__()
        self.setFixedSize(86, 168)

    def paintEvent(self, _e):  # noqa: N802
        from PyQt6.QtCore import QPointF, QRectF
        from PyQt6.QtGui import QLinearGradient, QRadialGradient

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        body = QRectF(14, 8, w - 28, h - 16)
        radius = 17

        # soft ambient glow behind the lit phone (neutral cyan-white)
        glow = QRadialGradient(QPointF(w / 2, h / 2), w * 0.7)
        gc = QColor("#9fe9ff")
        gc.setAlpha(70)
        glow.setColorAt(0.0, gc)
        gc2 = QColor("#9fe9ff")
        gc2.setAlpha(0)
        glow.setColorAt(1.0, gc2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow)
        p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # titanium frame (metallic vertical gradient)
        frame = QLinearGradient(body.x(), 0, body.right(), 0)
        frame.setColorAt(0.0, QColor("#5b6166"))
        frame.setColorAt(0.12, QColor("#9aa1a6"))
        frame.setColorAt(0.5, QColor("#2b2f33"))
        frame.setColorAt(0.88, QColor("#9aa1a6"))
        frame.setColorAt(1.0, QColor("#41464a"))
        p.setBrush(frame)
        p.drawRoundedRect(body, radius, radius)

        # side buttons
        p.setBrush(QColor("#2b2f33"))
        p.drawRoundedRect(QRectF(body.x() - 1.5, body.y() + 34, 2, 16), 1, 1)
        p.drawRoundedRect(QRectF(body.x() - 1.5, body.y() + 54, 2, 22), 1, 1)
        p.drawRoundedRect(QRectF(body.right() - 0.5, body.y() + 46, 2, 26), 1, 1)

        # lit screen (wallpaper gradient)
        screen = QRectF(body.x() + 4, body.y() + 4,
                        body.width() - 8, body.height() - 8)
        wp = QLinearGradient(screen.x(), screen.y(),
                             screen.right(), screen.bottom())
        wp.setColorAt(0.0, QColor("#2bd6ff"))
        wp.setColorAt(0.45, QColor("#3a7bff"))
        wp.setColorAt(1.0, QColor("#6f3cff"))
        p.setBrush(wp)
        p.drawRoundedRect(screen, radius - 4, radius - 4)

        # glossy highlight on the screen
        gloss = QLinearGradient(screen.x(), screen.y(),
                                screen.x(), screen.center().y())
        hc = QColor("#ffffff")
        hc.setAlpha(70)
        gloss.setColorAt(0.0, hc)
        hc2 = QColor("#ffffff")
        hc2.setAlpha(0)
        gloss.setColorAt(1.0, hc2)
        p.setBrush(gloss)
        p.drawRoundedRect(QRectF(screen.x(), screen.y(),
                                 screen.width(), screen.height() * 0.5),
                          radius - 4, radius - 4)

        # dynamic island with camera dot
        island = QRectF(w / 2 - 13, screen.y() + 7, 26, 8)
        p.setBrush(QColor("#000000"))
        p.drawRoundedRect(island, 4, 4)
        p.setBrush(QColor("#0c2330"))
        p.drawEllipse(QPointF(island.right() - 4, island.center().y()), 2, 2)
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
