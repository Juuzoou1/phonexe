"""
Programmatic (non-CLI) analysis API used by the GUI and other callers.

Mirrors the CLI pipeline but returns the report dict quietly instead of
printing progress.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .android import calls as a_calls
from .android import contacts as a_contacts
from .android import deleted as a_deleted
from .android import messages as a_messages
from .android import social as a_social
from .android import whatsapp as a_whatsapp
from .android.extraction import AndroidExtraction
from .apps import social, whatsapp
from .backup import IOSBackup
from .extractors import calls, contacts, deleted, messages, photos, safari

_IOS_EXTRACTORS = [contacts, messages, calls, safari, whatsapp, social, photos,
                   deleted]
_ANDROID_EXTRACTORS = [a_contacts, a_messages, a_calls, a_whatsapp, a_social,
                       a_deleted]


def detect_platform(path: str | Path) -> str | None:
    """Return 'ios', 'android', or None for the given directory."""
    p = Path(path)
    if not p.is_dir():
        return None
    if (p / "Manifest.db").exists():
        return "ios"
    # Android filesystem extraction heuristics.
    if (p / "data" / "data").is_dir() or list(p.rglob("build.prop"))[:1]:
        return "android"
    if list(p.rglob("contacts2.db"))[:1] or list(p.rglob("mmssms.db"))[:1]:
        return "android"
    return None


def _run(source, extractors, progress=None) -> dict:
    artifacts: dict[str, dict] = {}
    for mod in extractors:
        name = getattr(mod, "ARTIFACT", mod.__name__)
        if progress:
            progress(name)
        try:
            artifacts[name] = mod.extract(source)
        except Exception as e:  # never let one artifact kill the run
            artifacts[name] = {"artifact": name, "error": str(e), "count": 0}
    return artifacts


def analyze(path: str | Path, progress=None) -> dict:
    """Auto-detect platform and produce a full report dict.

    *progress* is an optional callable invoked with each artifact name.
    """
    platform = detect_platform(path)
    if platform == "ios":
        return analyze_ios(path, progress)
    if platform == "android":
        return analyze_android(path, progress)
    raise ValueError(
        "Could not detect an iOS backup or Android extraction at this path."
    )


def analyze_ios(path: str | Path, progress=None) -> dict:
    backup = IOSBackup(path)
    artifacts = _run(backup, _IOS_EXTRACTORS, progress)
    return {
        "meta": {
            "tool": f"phonexe v{__version__}",
            "platform": "ios",
            "examined_at": datetime.now(timezone.utc).isoformat(),
            "source_path": str(backup.path),
        },
        "device": backup.device.as_dict(),
        "artifacts": artifacts,
    }


def analyze_android(path: str | Path, progress=None) -> dict:
    ext = AndroidExtraction(path)
    artifacts = _run(ext, _ANDROID_EXTRACTORS, progress)
    return {
        "meta": {
            "tool": f"phonexe v{__version__}",
            "platform": "android",
            "examined_at": datetime.now(timezone.utc).isoformat(),
            "source_path": str(ext.path),
        },
        "device": ext.device.as_dict(),
        "artifacts": artifacts,
    }
