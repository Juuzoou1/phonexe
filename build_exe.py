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


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed. Run: pip install pyinstaller")
        return 1

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
        cmd += ["--collect-submodules", "pymobiledevice3"]
    except ImportError:
        print("note: pymobiledevice3 not installed — acquire-ios will rely on "
              "bundled/system libimobiledevice instead.")

    cmd.append("run.py")
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
