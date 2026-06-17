"""Inventory video media from a backup as its own artifact category.

Kept separate from ``photos`` so the examiner can review, select and export
images and videos independently. Videos don't carry EXIF the way JPEGs do, so
we record the on-disk path, size and (when available) the file's modification
time — enough to list, hash and offload them.
"""

from __future__ import annotations

from pathlib import Path

from ..backup import IOSBackup

ARTIFACT = "videos"
_DOMAIN = "CameraRollDomain"
_VIDEO_EXTS = (".mov", ".mp4", ".m4v", ".avi", ".3gp", ".hevc")


def extract(backup: IOSBackup) -> dict:
    records = []
    for f in backup.iter_files(domain=_DOMAIN):
        if not f.is_file:
            continue
        if not f.relative_path.lower().endswith(_VIDEO_EXTS):
            continue
        payload = backup.resolve(f)
        if not payload:
            continue
        try:
            size = Path(payload).stat().st_size
        except OSError:
            size = None
        records.append({
            "relative_path": f.relative_path,
            "stored_at": str(payload),
            "size_bytes": size,
        })

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
