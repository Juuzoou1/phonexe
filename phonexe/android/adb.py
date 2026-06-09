"""
Live ADB logical acquisition for *authorized* Android devices.

Requires the `adb` binary on PATH and a connected device that has USB
debugging enabled and is authorized (the on-device "Allow USB debugging?"
prompt must be accepted by the device owner). This performs *logical*
extraction via Android content providers and per-app database pulls — it does
not root the device, bypass the lock screen, or defeat any security control.

Where possible, pulling the raw database files (via `run-as`, for debuggable
apps, or with root you already have) is preferred over content-provider
queries, whose text output cannot perfectly escape values that contain
commas.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import Optional

from ..timeutil import unix_to_iso

_ROW_RE = re.compile(r"^Row:\s*\d+\s*(.*)$")


class ADBError(Exception):
    pass


def _adb_path() -> Optional[str]:
    """Locate adb: bundled in gui/assets/tools first, then system PATH."""
    from pathlib import Path
    tools = Path(__file__).resolve().parent.parent / "gui" / "assets" / "tools"
    for cand in (tools / "adb.exe", tools / "adb"):
        if cand.exists():
            return str(cand)
    return shutil.which("adb")


def adb_available() -> bool:
    return _adb_path() is not None


def _run(args: list[str], serial: Optional[str] = None, timeout: int = 60) -> str:
    adb = _adb_path()
    if not adb:
        raise ADBError("`adb` not found. Install Android platform-tools "
                       "or bundle adb.exe in gui/assets/tools.")
    cmd = [adb]
    if serial:
        cmd += ["-s", serial]
    cmd += args
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout
    )
    if proc.returncode != 0:
        raise ADBError(proc.stderr.strip() or f"adb {' '.join(args)} failed")
    return proc.stdout


def list_devices() -> list[str]:
    """Return serials of devices in the 'device' (authorized) state."""
    out = _run(["devices"])
    serials = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def device_info(serial: Optional[str] = None) -> dict:
    props = {
        "manufacturer": "ro.product.manufacturer",
        "model": "ro.product.model",
        "brand": "ro.product.brand",
        "android_version": "ro.build.version.release",
        "sdk": "ro.build.version.sdk",
        "serial": "ro.serialno",
    }
    info = {}
    for key, prop in props.items():
        try:
            info[key] = _run(["shell", "getprop", prop], serial).strip() or None
        except ADBError:
            info[key] = None
    return info


def parse_content_rows(output: str) -> list[dict]:
    """Parse `adb shell content query` output into row dicts.

    Output lines look like:  Row: 0 _id=1, address=+123, body=hi, date=168...
    Values containing ", " are a known ambiguity of this format; pulling the
    raw DB is preferred when exact fidelity matters.
    """
    rows = []
    for line in output.splitlines():
        m = _ROW_RE.match(line.strip())
        if not m:
            continue
        body = m.group(1)
        rec: dict[str, Optional[str]] = {}
        for pair in body.split(", "):
            if "=" not in pair:
                continue
            k, _, v = pair.partition("=")
            rec[k.strip()] = None if v == "NULL" else v
        rows.append(rec)
    return rows


def query_provider(
    uri: str, projection: Optional[list[str]] = None, serial: Optional[str] = None
) -> list[dict]:
    args = ["shell", "content", "query", "--uri", uri]
    if projection:
        args += ["--projection", ":".join(projection)]
    return parse_content_rows(_run(args, serial))


def logical_extract(serial: Optional[str] = None) -> dict:
    """Pull contacts, SMS and call log via content providers."""
    artifacts: dict[str, dict] = {}

    # Contacts (phone numbers).
    contacts = query_provider(
        "content://com.android.contacts/data/phones",
        ["display_name", "data1"],
        serial,
    )
    artifacts["contacts"] = {
        "artifact": "contacts",
        "count": len(contacts),
        "records": [
            {"name": c.get("display_name"), "phone": c.get("data1")}
            for c in contacts
        ],
    }

    # SMS.
    sms = query_provider(
        "content://sms", ["address", "body", "date", "type"], serial
    )
    artifacts["messages"] = {
        "artifact": "messages",
        "count": len(sms),
        "records": [
            {
                "address": s.get("address"),
                "text": s.get("body"),
                "timestamp": unix_to_iso(s.get("date"), millis=True),
                "type": s.get("type"),
            }
            for s in sms
        ],
    }

    # Call log.
    calls = query_provider(
        "content://call_log/calls",
        ["number", "date", "duration", "type"],
        serial,
    )
    artifacts["calls"] = {
        "artifact": "calls",
        "count": len(calls),
        "records": [
            {
                "number": c.get("number"),
                "timestamp": unix_to_iso(c.get("date"), millis=True),
                "duration_seconds": c.get("duration"),
                "type": c.get("type"),
            }
            for c in calls
        ],
    }

    return artifacts
