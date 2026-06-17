"""
SVG icon rendering for brand logos (Simple Icons, CC0) and UI icons
(Lucide, ISC). Rendered offline with QtSvg; no network at runtime.

Brand badges = rounded square in the brand color + the white official glyph.
Nav icons = recolored Lucide stroke glyphs.
"""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PyQt6.QtSvg import QSvgRenderer

from . import theme

try:
    from importlib.resources import files as _res_files
except Exception:  # pragma: no cover
    _res_files = None

# our app key -> Simple Icons file name
_APP_FILE = {
    "whatsapp": "whatsapp", "instagram": "instagram", "telegram": "telegram",
    "snapchat": "snapchat", "tiktok": "tiktok", "discord": "discord",
    "signal": "signal", "messenger": "messenger", "facebook": "facebook",
    "twitter": "x", "messages": "imessage", "gmail": "gmail",
    "chrome": "googlechrome", "drive": "googledrive",
}

# badge background color per app
_APP_BG = {
    "whatsapp": "#25D366", "telegram": "#229ED9", "snapchat": "#FFFC00",
    "tiktok": "#000000", "discord": "#5865F2", "signal": "#3A76F0",
    "messenger": "#0084FF", "facebook": "#1877F2", "twitter": "#000000",
    "messages": "#34DA50", "gmail": "#FFFFFF", "chrome": "#FFFFFF",
    "drive": "#FFFFFF", "instagram": "#E1306C",
}
# glyph color override (default white)
_APP_GLYPH = {
    "snapchat": "#000000", "gmail": "#EA4335", "chrome": None, "drive": None,
}
_GRADIENT = {"instagram", "messenger"}


def _read(rel: str) -> bytes | None:
    try:
        if _res_files is not None:
            return _res_files("phonexe.gui").joinpath(rel).read_bytes()
        from pathlib import Path  # pragma: no cover
        return (__import__("pathlib").Path(__file__).parent / rel).read_bytes()
    except Exception:
        return None


def _recolor(svg: bytes, *, fill: str | None = None,
             stroke: str | None = None) -> QByteArray:
    text = svg.decode("utf-8", "ignore")
    if fill is not None:
        text = text.replace("<path", f'<path fill="{fill}"')
        text = text.replace('fill="none"', 'fill="none"')
    if stroke is not None:
        text = text.replace("currentColor", stroke)
    return QByteArray(text.encode("utf-8"))


def _badge_path(s: int) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, s, s), s * 0.24, s * 0.24)
    return path


def app_icon(key: str, size: int = 48) -> QPixmap | None:
    """Brand badge with the official white glyph; None if asset missing."""
    fname = _APP_FILE.get(key)
    if not fname:
        return None
    svg = _read(f"assets/appicons/{fname}.svg")
    if not svg:
        return None

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # badge background
    path = _badge_path(size)
    if key == "instagram":
        g = QLinearGradient(0, size, size, 0)
        g.setColorAt(0, QColor("#FEDA75"))
        g.setColorAt(0.4, QColor("#FA7E1E"))
        g.setColorAt(0.7, QColor("#D62976"))
        g.setColorAt(1, QColor("#4F5BD5"))
        p.fillPath(path, g)
    elif key == "messenger":
        g = QLinearGradient(0, size, size, 0)
        g.setColorAt(0, QColor("#00B2FF"))
        g.setColorAt(1, QColor("#006AFF"))
        p.fillPath(path, g)
    else:
        p.fillPath(path, QColor(_APP_BG.get(key, "#222")))

    # glyph
    glyph = _APP_GLYPH.get(key, "#FFFFFF") if key in _APP_GLYPH else "#FFFFFF"
    data = svg if glyph is None else bytes(_recolor(svg, fill=glyph).data())
    renderer = QSvgRenderer(QByteArray(data))
    m = size * 0.26
    renderer.render(p, QRectF(m, m, size - 2 * m, size - 2 * m))
    p.end()
    return pix


def nav_icon(name: str, size: int = 18, color: str | None = None) -> QPixmap:
    """Render a Lucide UI icon recolored to *color* (default #BFD5E6)."""
    color = color or "#BFD5E6"
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    svg = _read(f"assets/navicons/{name}.svg")
    if svg:
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        QSvgRenderer(_recolor(svg, stroke=color)).render(
            p, QRectF(0, 0, size, size))
        p.end()
    return pix
