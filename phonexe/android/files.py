"""Inventory files in an Android filesystem extraction."""

from __future__ import annotations

from .extraction import AndroidExtraction

ARTIFACT = "files"
_MAX = 5000


def extract(ext: AndroidExtraction) -> dict:
    records = []
    root = ext.path
    for p in root.rglob("*"):
        if p.is_file():
            records.append({"path": str(p.relative_to(root))})
            if len(records) >= _MAX:
                break
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
