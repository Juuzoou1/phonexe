"""Inventory the files contained in an iOS backup (from the manifest)."""

from __future__ import annotations

from ..backup import IOSBackup

ARTIFACT = "files"
_MAX = 5000


def extract(backup: IOSBackup) -> dict:
    records = []
    for f in backup.iter_files():
        if not f.is_file:
            continue
        records.append({
            "domain": f.domain,
            "path": f.relative_path,
        })
        if len(records) >= _MAX:
            break
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
