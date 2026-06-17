"""Load the bundled Cairo font (OFL) so the UI uses it regardless of the OS."""

from __future__ import annotations

from PyQt6.QtGui import QFontDatabase

try:
    from importlib.resources import files as _res_files
except Exception:  # pragma: no cover
    _res_files = None

_loaded = False

# Loaded in order; IBM Plex Sans Arabic is the design's primary font.
_FONT_FILES = [
    "IBMPlexSansArabic-Light.ttf",
    "IBMPlexSansArabic-Regular.ttf",
    "IBMPlexSansArabic-Medium.ttf",
    "IBMPlexSansArabic-SemiBold.ttf",
    "IBMPlexSansArabic-Bold.ttf",
    "Cairo.ttf",
]


def _read(rel: str) -> bytes:
    if _res_files is not None:
        return _res_files("phonexe.gui").joinpath(rel).read_bytes()
    from pathlib import Path  # pragma: no cover
    return (Path(__file__).parent / rel.replace("/", "/")).read_bytes()


def load_fonts() -> None:
    """Register the bundled UI fonts with Qt (idempotent)."""
    global _loaded
    if _loaded:
        return
    _loaded = True
    for name in _FONT_FILES:
        try:
            QFontDatabase.addApplicationFontFromData(
                _read(f"assets/fonts/{name}")
            )
        except Exception:
            pass  # fall back to the CSS font stack
