"""
Thin compatibility layer over PyQt-Fluent-Widgets.

Exposes Fluent components when the library is installed, and falls back to the
plain Qt equivalents otherwise, so phonexe runs either way.
"""

from __future__ import annotations

try:
    from qfluentwidgets import (  # type: ignore
        ComboBox,
        InfoBar,
        InfoBarPosition,
        LineEdit,
        PrimaryPushButton,
        PushButton,
        SearchLineEdit,
        TableWidget,
    )
    HAVE_FLUENT = True
except Exception:  # pragma: no cover - lib optional
    from PyQt6.QtWidgets import (
        QComboBox as ComboBox,
        QLineEdit as LineEdit,
        QLineEdit as SearchLineEdit,
        QPushButton as PrimaryPushButton,
        QPushButton as PushButton,
        QTableWidget as TableWidget,
    )
    InfoBar = None
    InfoBarPosition = None
    HAVE_FLUENT = False


def notify(parent, title: str, content: str = "", success: bool = True) -> None:
    """Show a transient Fluent InfoBar (or a message box as a fallback)."""
    if HAVE_FLUENT and InfoBar is not None and parent is not None:
        try:
            maker = InfoBar.success if success else InfoBar.error
            maker(title=title, content=content, parent=parent,
                  position=InfoBarPosition.TOP_RIGHT, duration=3000,
                  isClosable=True)
            return
        except Exception:
            pass
    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.information(parent, title, f"{title}\n{content}".strip())
