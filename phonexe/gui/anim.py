"""
Motion helpers — intentional, easing-based animations for the Qt UI.

Applies the same animation philosophy as good web motion (ease-out curves,
~200-300 ms durations, subtle fade/slide) using QPropertyAnimation so views
feel alive instead of snapping into place.
"""

from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


def fade_in(widget: QWidget, ms: int = 220) -> None:
    """Fade *widget* from transparent to opaque with an ease-out curve."""
    if widget is None or not widget.isVisible():
        return  # skip when not on screen (e.g. headless tests)
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    # drop the effect when done so child effects (glow, shadows) are restored
    anim.finished.connect(lambda: widget.setGraphicsEffect(None))
    anim.start()
    widget._fade_anim = anim  # keep a reference alive


def slide_fade_in(widget: QWidget, ms: int = 260, dy: int = 16) -> None:
    """Fade in while gently sliding up — a livelier entrance for panels."""
    if widget is None or not widget.isVisible():
        return  # skip when not on screen (e.g. headless tests)
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    fade = QPropertyAnimation(eff, b"opacity", widget)
    fade.setDuration(ms)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.Type.OutCubic)

    start_pos = widget.pos()
    move = QPropertyAnimation(widget, b"pos", widget)
    move.setDuration(ms)
    move.setStartValue(QPoint(start_pos.x(), start_pos.y() + dy))
    move.setEndValue(start_pos)
    move.setEasingCurve(QEasingCurve.Type.OutCubic)

    group = QParallelAnimationGroup(widget)
    group.addAnimation(fade)
    group.addAnimation(move)
    group.finished.connect(lambda: widget.setGraphicsEffect(None))
    group.start()
    widget._enter_anim = group
