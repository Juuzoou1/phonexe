"""
Offline vector app-logo painter.

Draws simplified, recognizable brand logos (WhatsApp, Telegram, Instagram,
Snapchat, TikTok, Discord, Signal, Messenger, Facebook, X/Twitter, Messages)
with QPainter — no bundled image files or network needed. Each logo is a
rounded-square badge in the brand color with a white emblem, which reads as
the app at dashboard icon sizes.
"""

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
    QPolygonF,
)

BRAND = {
    "whatsapp": "#25D366",
    "messages": "#34DA50",
    "telegram": "#2AABEE",
    "instagram": "#E1306C",
    "snapchat": "#FFFC00",
    "discord": "#5865F2",
    "signal": "#3A76F0",
    "messenger": "#0084FF",
    "facebook": "#1877F2",
    "twitter": "#1DA1F2",
    "tiktok": "#000000",
}


def _badge(p: QPainter, s: int, color, gradient=None):
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, s, s), s * 0.24, s * 0.24)
    if gradient is not None:
        p.fillPath(path, QBrush(gradient))
    else:
        p.fillPath(path, QColor(color))
    return path


def _white(p: QPainter):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("white"))


def _whatsapp(p, s):
    _badge(p, s, BRAND["whatsapp"])
    _white(p)
    c = s * 0.5
    r = s * 0.27
    p.drawEllipse(QPointF(c, c), r, r)
    # speech tail
    tail = QPolygonF([QPointF(s*0.30, s*0.70), QPointF(s*0.40, s*0.62),
                      QPointF(s*0.34, s*0.78)])
    p.drawPolygon(tail)
    # green handset
    p.setBrush(QColor(BRAND["whatsapp"]))
    p.setFont(QFont("Arial", int(s*0.26)))
    p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "☎")


def _messages(p, s):
    _badge(p, s, BRAND["messages"])
    _white(p)
    path = QPainterPath()
    path.addRoundedRect(QRectF(s*0.18, s*0.20, s*0.64, s*0.46),
                        s*0.16, s*0.16)
    p.drawPath(path)
    tail = QPolygonF([QPointF(s*0.30, s*0.62), QPointF(s*0.30, s*0.80),
                      QPointF(s*0.46, s*0.62)])
    p.drawPolygon(tail)


def _telegram(p, s):
    grad = QLinearGradient(0, 0, 0, s)
    grad.setColorAt(0, QColor("#37BBFE"))
    grad.setColorAt(1, QColor("#007DBB"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawEllipse(QRectF(0, 0, s, s))
    _white(p)
    plane = QPolygonF([
        QPointF(s*0.22, s*0.50), QPointF(s*0.80, s*0.28),
        QPointF(s*0.66, s*0.74), QPointF(s*0.52, s*0.58),
        QPointF(s*0.40, s*0.68),
    ])
    p.drawPolygon(plane)


def _instagram(p, s):
    grad = QLinearGradient(0, s, s, 0)
    grad.setColorAt(0, QColor("#FEDA75"))
    grad.setColorAt(0.4, QColor("#FA7E1E"))
    grad.setColorAt(0.7, QColor("#D62976"))
    grad.setColorAt(1, QColor("#4F5BD5"))
    _badge(p, s, None, grad)
    pen = QPen(QColor("white"), max(2.0, s*0.06))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(s*0.24, s*0.24, s*0.52, s*0.52), s*0.16, s*0.16)
    p.drawEllipse(QRectF(s*0.36, s*0.36, s*0.28, s*0.28))
    p.setBrush(QColor("white"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(s*0.64, s*0.28, s*0.07, s*0.07))


def _snapchat(p, s):
    _badge(p, s, BRAND["snapchat"])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("white"))
    ghost = QPainterPath()
    ghost.moveTo(s*0.5, s*0.18)
    ghost.cubicTo(s*0.72, s*0.18, s*0.72, s*0.42, s*0.72, s*0.58)
    ghost.lineTo(s*0.78, s*0.66)
    ghost.lineTo(s*0.5, s*0.74)
    ghost.lineTo(s*0.22, s*0.66)
    ghost.lineTo(s*0.28, s*0.58)
    ghost.cubicTo(s*0.28, s*0.42, s*0.28, s*0.18, s*0.5, s*0.18)
    p.drawPath(ghost)


def _tiktok(p, s):
    _badge(p, s, BRAND["tiktok"])
    # cyan + red offset notes, white on top
    for color, dx in (("#25F4EE", -s*0.03), ("#FE2C55", s*0.03), ("white", 0)):
        p.setPen(QPen(QColor(color), max(2.0, s*0.07)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(s*0.30+dx, s*0.46, s*0.22, s*0.22), 0, 360*16)
        p.drawLine(QPointF(s*0.52+dx, s*0.57), QPointF(s*0.52+dx, s*0.28))
        p.drawLine(QPointF(s*0.52+dx, s*0.28), QPointF(s*0.66+dx, s*0.34))


def _discord(p, s):
    _badge(p, s, BRAND["discord"])
    _white(p)
    # rounded mascot face
    face = QPainterPath()
    face.addRoundedRect(QRectF(s*0.24, s*0.30, s*0.52, s*0.40),
                        s*0.20, s*0.20)
    p.drawPath(face)
    # two blurple eyes
    p.setBrush(QColor(BRAND["discord"]))
    p.drawEllipse(QRectF(s*0.36, s*0.44, s*0.10, s*0.13))
    p.drawEllipse(QRectF(s*0.54, s*0.44, s*0.10, s*0.13))


def _simple_letter(color, letter):
    def fn(p, s):
        _badge(p, s, color)
        p.setPen(QColor("white"))
        f = QFont("Arial", int(s*0.5))
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, letter)
    return fn


def _bubble_badge(color):
    def fn(p, s):
        _badge(p, s, color)
        _white(p)
        path = QPainterPath()
        path.addEllipse(QRectF(s*0.22, s*0.22, s*0.56, s*0.50))
        p.drawPath(path)
        tail = QPolygonF([QPointF(s*0.34, s*0.66), QPointF(s*0.34, s*0.82),
                          QPointF(s*0.50, s*0.66)])
        p.drawPolygon(tail)
    return fn


_PAINTERS = {
    "whatsapp": _whatsapp,
    "messages": _messages,
    "telegram": _telegram,
    "instagram": _instagram,
    "snapchat": _snapchat,
    "tiktok": _tiktok,
    "discord": _discord,
    "signal": _bubble_badge(BRAND["signal"]),
    "messenger": _bubble_badge(BRAND["messenger"]),
    "facebook": _simple_letter(BRAND["facebook"], "f"),
    "twitter": _simple_letter(BRAND["twitter"], "X"),
}


def app_pixmap(key: str, size: int = 48) -> QPixmap:
    """Return a QPixmap logo for *key* (falls back to a lettered badge)."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter = _PAINTERS.get(key)
    if painter is None:
        _simple_letter("#334155", (key[:1] or "?").upper())(p, size)
    else:
        painter(p, size)
    p.end()
    return pix
