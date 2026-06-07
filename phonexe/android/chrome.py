"""Extract Chrome browsing history from an Android extraction."""

from __future__ import annotations

from ..extractors.chrome import parse_history
from .extraction import AndroidExtraction

ARTIFACT = "chrome_history"
_PACKAGE = "com.android.chrome"


def extract(ext: AndroidExtraction) -> dict:
    records = []
    for p in ext.path.rglob("History"):
        if _PACKAGE in str(p) and p.is_file():
            records.extend(parse_history(p))
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
