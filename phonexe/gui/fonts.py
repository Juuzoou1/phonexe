"""Load the bundled Cairo font (OFL) so the UI uses it regardless of the OS."""

from __future__ import annotations

from PyQt6.QtGui import QFontDatabase

try:
    from importlib.resources import files as _res_files
except Exception:  # pragma: no cover
    _res_files = None

_loaded = False


def load_fonts() -> None:
    """Register the bundled Cairo TTF with Qt (idempotent)."""
    global _loaded
    if _loaded:
        return
    _loaded = True
    try:
        if _res_files is not None:
            data = (
                _res_files("phonexe.gui")
                .joinpath("assets/fonts/Cairo.ttf")
                .read_bytes()
            )
        else:  # pragma: no cover
            from pathlib import Path
            data = (Path(__file__).parent / "assets" / "fonts"
                    / "Cairo.ttf").read_bytes()
        QFontDatabase.addApplicationFontFromData(data)
    except Exception:
        pass  # fall back to the CSS font stack
