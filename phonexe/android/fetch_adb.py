"""
Fetch Google's official ``adb`` (Android platform-tools) so live Android
acquisition works out of the box, without asking the examiner to install the
Android SDK separately.

The binaries are downloaded from Google's public platform-tools endpoint and
placed in ``phonexe/gui/assets/tools/`` — the same directory ``android.adb``
already searches before falling back to PATH. Platform-tools are distributed
by Google under the Apache 2.0 license (redistribution permitted).

This downloads a normal developer tool; it performs no jailbreak/root and
nothing device-specific. Logical extraction still requires an authorized,
USB-debugging-enabled device.
"""

from __future__ import annotations

import io
import os
import stat
import sys
import urllib.request
import zipfile
from pathlib import Path

_URL = "https://dl.google.com/android/repository/platform-tools-latest-{key}.zip"

# Files we keep from the platform-tools/ folder inside the zip, per OS. On
# Windows adb needs its two USB driver DLLs alongside the exe.
_WANTED = {
    "windows": ("adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"),
    "linux": ("adb",),
    "darwin": ("adb",),
}


def platform_key() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "darwin"
    return "linux"


def tools_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "gui" / "assets" / "tools"


def adb_name(key: str | None = None) -> str:
    return "adb.exe" if (key or platform_key()) == "windows" else "adb"


def is_present(dest: Path | None = None) -> bool:
    dest = dest or tools_dir()
    return (dest / adb_name()).exists()


def extract_from_zip(data: bytes, dest: Path, key: str | None = None) -> list[Path]:
    """Extract the wanted platform-tools files from an in-memory zip.

    Separated from the network download so it can be unit-tested with a
    synthetic archive.
    """
    key = key or platform_key()
    wanted = _WANTED[key]
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.endswith("/"):
                continue
            base = name.rsplit("/", 1)[-1]
            if base not in wanted:
                continue
            target = dest / base
            target.write_bytes(zf.read(name))
            if not base.lower().endswith((".dll", ".exe")):
                # make the unix adb binary executable
                target.chmod(target.stat().st_mode | stat.S_IXUSR
                             | stat.S_IXGRP | stat.S_IXOTH)
            written.append(target)
    return written


def fetch(dest: Path | None = None, force: bool = False,
          timeout: int = 180) -> Path:
    """Download and unpack platform-tools; return the path to the adb binary."""
    dest = dest or tools_dir()
    key = platform_key()
    adb = dest / adb_name(key)
    if adb.exists() and not force:
        return adb
    url = _URL.format(key=key)
    req = urllib.request.Request(url, headers={"User-Agent": "phonexe"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    written = extract_from_zip(data, dest, key)
    if not (dest / adb_name(key)).exists():
        raise RuntimeError(
            f"platform-tools archive did not contain {adb_name(key)} "
            f"(extracted: {[p.name for p in written]})")
    return adb


if __name__ == "__main__":  # pragma: no cover
    out = fetch(force="--force" in sys.argv)
    print(f"adb ready at: {out}")
