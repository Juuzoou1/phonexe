"""Extract Chrome browsing history (iOS) from the Chrome History database."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query
from ..timeutil import chrome_to_iso

ARTIFACT = "chrome_history"


def parse_history(db_path) -> list[dict]:
    records = []
    with open_ro(db_path) as con:
        rows = safe_query(
            con,
            "SELECT url, title, visit_count, last_visit_time "
            "FROM urls ORDER BY last_visit_time ASC",
        )
        for r in rows:
            records.append({
                "url": r["url"],
                "title": r["title"],
                "visit_count": r["visit_count"],
                "timestamp": chrome_to_iso(r["last_visit_time"]),
            })
    return records


def extract(backup: IOSBackup) -> dict:
    records = []
    for f in backup.iter_files():
        if not f.is_file or "chrome" not in f.domain.lower():
            continue
        if not f.relative_path.endswith("History"):
            continue
        payload = backup.resolve(f)
        if payload:
            records.extend(parse_history(payload))
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
