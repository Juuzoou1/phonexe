"""Inventory installed packages from an Android /data extraction."""

from __future__ import annotations

from .extraction import AndroidExtraction

ARTIFACT = "installed_apps"


def extract(ext: AndroidExtraction) -> dict:
    records = []
    base = ext.path / "data" / "data"
    if base.is_dir():
        for d in sorted(base.iterdir()):
            if d.is_dir():
                records.append({"bundle_id": d.name, "name": None,
                                "version": None})
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
