"""Inventory installed applications listed in the backup's Info.plist."""

from __future__ import annotations

import plistlib

from ..backup import IOSBackup

ARTIFACT = "installed_apps"


def extract(backup: IOSBackup) -> dict:
    info = backup.path / "Info.plist"
    records = []
    if info.exists():
        try:
            data = plistlib.loads(info.read_bytes())
        except Exception:
            data = {}
        bundles = data.get("Installed Applications") or []
        apps = data.get("Applications") or {}
        for bid in bundles:
            meta = apps.get(bid, {}) if isinstance(apps, dict) else {}
            records.append({
                "bundle_id": bid,
                "name": meta.get("CFBundleDisplayName")
                or meta.get("CFBundleName"),
                "version": meta.get("CFBundleShortVersionString"),
            })
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
