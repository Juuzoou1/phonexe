"""
Build a standalone Windows executable (phonexe.exe) with PyInstaller.

Run on Windows (or under Wine) with:

    pip install pyinstaller pillow
    python build_exe.py

The result is dist/phonexe.exe — a single file you can run on a machine
without Python installed:

    phonexe.exe analyze "C:\\path\\to\\Backup\\<udid>" -o report --hash

Note: a PyInstaller build must be produced on the target OS. To get a
Windows .exe you must run this script on Windows; running it on Linux
produces a Linux binary instead.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ICON = Path(__file__).resolve().parent / "phonexe" / "gui" / "assets" / "appicon.ico"


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed. Run: pip install pyinstaller")
        return 1

    # Regenerate the brand icon if it is missing (committed, so usually present).
    if not _ICON.exists():
        try:
            from phonexe.gui.assets.make_icon import build as build_icon
            build_icon()
        except Exception as e:  # pragma: no cover - Pillow/build-host dependent
            print(f"note: could not generate app icon ({e}); building without "
                  "a custom icon.")

    # Best-effort: bundle Google's adb so Android acquisition works out of the
    # box in the packaged EXE. Falls back gracefully if offline.
    try:
        from phonexe.android import fetch_adb
        if not fetch_adb.is_present():
            print("Fetching Android platform-tools (adb) to bundle ...")
            fetch_adb.fetch()
    except Exception as e:  # pragma: no cover - network/build-host dependent
        print(f"note: could not bundle adb ({e}); Android live-extract will "
              "need adb on PATH at runtime.")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "phonexe",
        "--console",
        # collect optional Pillow plugins (HEIC/JPEG) when present
        "--collect-submodules",
        "PIL",
        # ensure lazily-imported phonexe modules (e.g. android.adb, gui) bundle
        "--collect-submodules",
        "phonexe",
        # bundle the PyQt6 desktop GUI and its Qt plugins
        "--collect-all",
        "PyQt6",
        # bundle the offline world-map data used by the geolocation view
        "--collect-data",
        "phonexe",
    ]

    # bundle the pure-Python iOS acquisition backend only if it is installed
    try:
        import pymobiledevice3  # noqa: F401
        # collect-all (not just submodules): pymobiledevice3 ships data files
        # (device lists, plist templates) the backup2 backend needs at runtime.
        cmd += ["--collect-all", "pymobiledevice3"]
    except ImportError:
        print("note: pymobiledevice3 not installed — acquire-ios will rely on "
              "bundled/system libimobiledevice instead.")

    # bundle the Fluent widget library (and its data) when installed
    try:
        import qfluentwidgets  # noqa: F401
        cmd += ["--collect-all", "qfluentwidgets"]
    except ImportError:
        print("note: PyQt6-Fluent-Widgets not installed — UI falls back to "
              "plain Qt widgets.")

    # Brand the executable with the phonexe app icon when available.
    if _ICON.exists():
        cmd += ["--icon", str(_ICON)]

    cmd.append("run.py")
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
