"""Entry point that launches the phonexe desktop GUI."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from . import theme
from .mainwindow import MainWindow


def run(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("phonexe")
    from .fonts import load_fonts
    load_fonts()
    # Fluent Design theming (used by the qfluentwidgets components)
    try:
        from qfluentwidgets import Theme, setTheme, setThemeColor
        setTheme(Theme.DARK)
        setThemeColor(theme.ACCENT)
    except Exception:
        pass
    app.setStyleSheet(theme.stylesheet())
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
