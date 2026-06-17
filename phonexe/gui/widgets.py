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


class NeonPhone(QWidget):
    """A geometric line-art phone whose strokes glow white neon."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(220, 360)

    def paintEvent(self, _e):  # noqa: N802
        from PyQt6.QtCore import QPointF, QRectF
        from PyQt6.QtGui import QPainterPath

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        side = min(w, h - 20)
        bw = side * 0.52
        bh = side * 0.96
        x = (w - bw) / 2
        y = (h - bh) / 2
        body = QRectF(x, y, bw, bh)
        r = bw * 0.16

        def neon(draw):
            """Render a draw-callable 3x: wide soft halo -> crisp white core."""
            for width, alpha in ((9, 26), (4.5, 70), (1.6, 255)):
                pen = QPen(QColor(255, 255, 255, alpha), width)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                draw()

        # phone body outline
        neon(lambda: p.drawRoundedRect(body, r, r))
        # dynamic island
        island = QRectF(x + bw / 2 - bw * 0.16, y + bh * 0.04,
                        bw * 0.32, bh * 0.022)
        neon(lambda: p.drawRoundedRect(island, island.height() / 2,
                                       island.height() / 2))

        # inner geometric "scan / circuit" motif
        cx = x + bw / 2
        gx0, gx1 = x + bw * 0.16, x + bw * 0.84
        # horizontal scan lines
        for fy in (0.30, 0.46, 0.62, 0.78):
            yy = y + bh * fy
            neon(lambda yy=yy: p.drawLine(QPointF(gx0, yy), QPointF(gx1, yy)))
        # vertical spine
        neon(lambda: p.drawLine(QPointF(cx, y + bh * 0.16),
                                QPointF(cx, y + bh * 0.86)))
        # node dots along the spine
        for fy in (0.30, 0.46, 0.62, 0.78):
            yy = y + bh * fy
            for nx in (gx0, cx, gx1):
                for rad, alpha in ((6, 40), (2.4, 255)):
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(255, 255, 255, alpha))
                    p.drawEllipse(QPointF(nx, yy), rad, rad)
        # home indicator
        ind = QRectF(cx - bw * 0.12, y + bh * 0.93, bw * 0.24, bh * 0.012)
        neon(lambda: p.drawRoundedRect(ind, ind.height() / 2, ind.height() / 2))
        p.end()


class PhoneOutline(QWidget):
    """A near-realistic, screen-lit smartphone with a tiny live home screen."""

    _ICON_COLORS = ["#25D366", "#E1306C", "#229ED9", "#FFCC00", "#FF5B5B",
                    "#34DA50", "#5865F2", "#1DA1F2", "#0084FF", "#FE2C55",
                    "#21D07A", "#9b59ff"]

    def __init__(self, glow: str = None):
        super().__init__()
        self.setFixedSize(104, 204)

    def paintEvent(self, _e):  # noqa: N802
        from PyQt6.QtCore import QPointF, QRectF
        from PyQt6.QtGui import QLinearGradient, QRadialGradient

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen)
        body = QRectF(16, 10, w - 32, h - 22)
        radius = 20

        # contact shadow under the device
        for sw, alpha in ((18, 50), (10, 70)):
            sc = QColor(0, 0, 0, alpha)
            p.setBrush(sc)
            p.drawRoundedRect(QRectF(body.x() + 4, body.bottom() - 6 + sw / 4,
                                     body.width() - 8, 14), 10, 10)

        # ambient screen glow
        glow = QRadialGradient(QPointF(w / 2, h * 0.45), w * 0.75)
        gc = QColor("#7fd8ff")
        gc.setAlpha(60)
        glow.setColorAt(0.0, gc)
        glow.setColorAt(1.0, QColor(127, 216, 255, 0))
        p.setBrush(glow)
        p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # titanium rail
        rail = QLinearGradient(body.x(), 0, body.right(), 0)
        for stop, col in ((0.0, "#6c7276"), (0.08, "#b9c0c4"), (0.18, "#454a4e"),
                          (0.5, "#23272a"), (0.82, "#454a4e"),
                          (0.92, "#b9c0c4"), (1.0, "#5a6064")):
            rail.setColorAt(stop, QColor(col))
        p.setBrush(rail)
        p.drawRoundedRect(body, radius, radius)

        # side buttons
        p.setBrush(QColor("#202427"))
        p.drawRoundedRect(QRectF(body.x() - 1.5, body.y() + 42, 2.2, 14), 1, 1)
        p.drawRoundedRect(QRectF(body.x() - 1.5, body.y() + 64, 2.2, 26), 1, 1)
        p.drawRoundedRect(QRectF(body.right() - 0.7, body.y() + 58, 2.2, 30), 1, 1)

        # black bezel
        bezel = QRectF(body.x() + 3.5, body.y() + 3.5,
                       body.width() - 7, body.height() - 7)
        p.setBrush(QColor("#050608"))
        p.drawRoundedRect(bezel, radius - 3, radius - 3)

        # lit wallpaper
        screen = QRectF(bezel.x() + 2, bezel.y() + 2,
                        bezel.width() - 4, bezel.height() - 4)
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(screen, radius - 5, radius - 5)
        p.setClipPath(clip)
        wp = QLinearGradient(screen.x(), screen.y(),
                             screen.right(), screen.bottom())
        wp.setColorAt(0.0, QColor("#0b2a4a"))
        wp.setColorAt(0.5, QColor("#123a78"))
        wp.setColorAt(1.0, QColor("#3a1d6e"))
        p.fillRect(screen, wp)

        # mini home-screen app grid
        cols, rows = 4, 5
        pad = 8
        gx0 = screen.x() + pad
        gw = (screen.width() - 2 * pad)
        cell = gw / cols
        icon = cell * 0.66
        top = screen.y() + 18
        idx = 0
        for r in range(rows):
            for c in range(cols):
                cx = gx0 + c * cell + (cell - icon) / 2
                cy = top + r * cell
                p.setBrush(QColor(self._ICON_COLORS[idx % len(self._ICON_COLORS)]))
                p.drawRoundedRect(QRectF(cx, cy, icon, icon),
                                  icon * 0.28, icon * 0.28)
                idx += 1
        # dock
        dock = QRectF(screen.x() + 6, screen.bottom() - cell - 4,
                      screen.width() - 12, cell)
        p.setBrush(QColor(255, 255, 255, 35))
        p.drawRoundedRect(dock, 12, 12)
        for c in range(cols):
            cx = dock.x() + 6 + c * ((dock.width() - 12) / cols) + \
                (((dock.width() - 12) / cols) - icon) / 2
            cy = dock.y() + (dock.height() - icon) / 2
            p.setBrush(QColor(self._ICON_COLORS[(idx + c) % len(self._ICON_COLORS)]))
            p.drawRoundedRect(QRectF(cx, cy, icon, icon),
                              icon * 0.28, icon * 0.28)

        # diagonal glass reflection
        refl = QLinearGradient(screen.x(), screen.y(),
                               screen.right(), screen.bottom())
        refl.setColorAt(0.0, QColor(255, 255, 255, 60))
        refl.setColorAt(0.25, QColor(255, 255, 255, 0))
        p.fillRect(screen, refl)
        p.restore()

        # dynamic island
        island = QRectF(w / 2 - 14, screen.y() + 6, 28, 8)
        p.setBrush(QColor("#000000"))
        p.drawRoundedRect(island, 4, 4)
        p.setBrush(QColor("#16323f"))
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
