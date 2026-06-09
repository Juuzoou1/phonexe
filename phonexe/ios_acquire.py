"""
iOS acquisition — pull a backup directly from a connected, authorized iPhone.

Uses Apple's own backup protocol via either backend, in priority order:

1. libimobiledevice CLI tools (idevice_id / ideviceinfo / idevicebackup2),
   looked up first in the bundled ``gui/assets/tools`` folder, then on PATH.
2. pymobiledevice3 (pure-Python), bundled into the executable.

This performs NO jailbreak, exploit, or passcode bypass. It only works on a
device that is unlocked and has trusted this computer ("Trust This Computer"),
ideally in airplane mode for evidence isolation. On Windows the Apple USB
driver (Apple Mobile Device Support, from the free "Apple Devices" app) is
required — as it is for any tool, including iTunes.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_ASSET_TOOLS = Path(__file__).parent / "gui" / "assets" / "tools"


class AcquireError(Exception):
    pass


def _tool(name: str) -> str | None:
    """Locate a CLI tool: bundled assets first, then system PATH."""
    for cand in (_ASSET_TOOLS / f"{name}.exe", _ASSET_TOOLS / name):
        if cand.exists():
            return str(cand)
    return shutil.which(name)


def has_libimobiledevice() -> bool:
    return bool(_tool("idevicebackup2") and _tool("idevice_id"))


def has_pymobiledevice3() -> bool:
    try:
        import pymobiledevice3  # noqa: F401
        return True
    except Exception:
        return False


def check() -> dict:
    """Report which acquisition backends are available."""
    li = has_libimobiledevice()
    pm = has_pymobiledevice3()
    return {
        "libimobiledevice": li,
        "pymobiledevice3": pm,
        "ready": li or pm,
        "backend": "libimobiledevice" if li else ("pymobiledevice3" if pm
                                                  else None),
    }


def list_devices() -> list[str]:
    """Return UDIDs of connected, reachable devices."""
    tool = _tool("idevice_id")
    if tool:
        try:
            out = subprocess.run([tool, "-l"], capture_output=True,
                                 text=True, timeout=20)
            return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
        except Exception:
            pass
    if has_pymobiledevice3():
        try:
            import asyncio

            # pymobiledevice3 >= 2.30 makes usbmux.list_devices a coroutine.
            from pymobiledevice3.usbmux import list_devices as _ld
            return [d.serial for d in asyncio.run(_ld())]
        except Exception:
            pass
    return []


def device_info(udid: str | None = None) -> dict:
    """Read device properties via ideviceinfo when available."""
    tool = _tool("ideviceinfo")
    info: dict[str, str] = {}
    if tool:
        args = [tool] + (["-u", udid] if udid else [])
        try:
            out = subprocess.run(args, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace",
                                 timeout=20).stdout
            for line in out.splitlines():
                if ": " in line:
                    k, v = line.split(": ", 1)
                    info[k.strip()] = v.strip()
        except Exception:
            pass
    return info


def _find_backup_dir(dest: Path, udid: str | None) -> Path:
    """Both backends write the backup under dest/<udid>/; locate that folder."""
    candidates = []
    if udid:
        candidates.append(dest / udid)
    try:
        candidates += [c for c in dest.iterdir() if c.is_dir()]
    except OSError:
        pass
    for c in candidates:
        if (c / "Manifest.db").exists() or (c / "Manifest.plist").exists():
            return c
    return dest


def _backup_cmd(dest: Path, udid: str | None) -> list[str]:
    """Build the backup command, preferring bundled libimobiledevice, then
    pymobiledevice3 (pure-Python). Both speak Apple's own mobilebackup2
    protocol over USB — no jailbreak, root, or passcode bypass."""
    li = _tool("idevicebackup2")
    if li:
        return [li] + (["-u", udid] if udid else []) + \
            ["backup", "--full", str(dest)]
    if has_pymobiledevice3():
        return [sys.executable, "-m", "pymobiledevice3", "backup2", "backup",
                "--full"] + (["--udid", udid] if udid else []) + [str(dest)]
    raise AcquireError(
        "No acquisition backend found. Run `phonexe fetch-adb` is for Android; "
        "for iOS install pymobiledevice3 (`pip install pymobiledevice3`) or "
        "bundle libimobiledevice in gui/assets/tools.")


def acquire(dest: str | Path, udid: str | None = None, progress=None) -> Path:
    """Back up the connected iPhone into *dest*; return the backup directory.

    Drives Apple's mobilebackup2 protocol via libimobiledevice or
    pymobiledevice3. The device must be unlocked and have trusted this
    computer. *progress* is an optional callable invoked with each output line.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    cmd = _backup_cmd(dest, udid)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace")
    assert proc.stdout is not None
    for line in proc.stdout:
        if progress and line.strip():
            progress(line.rstrip())
    proc.wait()
    if proc.returncode != 0:
        raise AcquireError(
            "Backup failed. Make sure the iPhone is unlocked, has tapped "
            "'Trust This Computer', stays connected throughout, and that the "
            "iTunes/Finder backup password (encryption) is turned OFF.")
    return _find_backup_dir(dest, udid)
