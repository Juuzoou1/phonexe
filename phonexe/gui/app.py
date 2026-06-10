"""Entry point that launches the phonexe desktop GUI."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from . import theme
from .mainwindow import MainWindow


def run(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("phonexe")
    # Window / taskbar icon (committed asset; silently skipped if absent).
    try:
        from pathlib import Path
        from PyQt6.QtGui import QIcon
        icon = Path(__file__).resolve().parent / "assets" / "appicon.ico"
        if icon.exists():
            app.setWindowIcon(QIcon(str(icon)))
    except Exception:
        pass
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

    # activation gate: require the secret code before anything else
    from .license import ensure_activated
    if not ensure_activated():
        return 0

    # case-setup wizard first: examiner + case number, then connect/open
    from PyQt6.QtWidgets import QDialog
    from .startup import CaseSetupDialog
    wizard = CaseSetupDialog()
    if wizard.exec() != QDialog.DialogCode.Accepted:
        return 0
    data = wizard.result_data()

    window = MainWindow(examiner=data["examiner"], case_id=data["case_id"],
                        organization=data["organization"])
    window.show()
    window.start_source(data["source"])
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
