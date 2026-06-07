"""Extract calendar events from Calendar.sqlitedb."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query
from ..timeutil import cocoa_to_iso

ARTIFACT = "calendar"
_DOMAIN = "HomeDomain"
_PATH = "Library/Calendar/Calendar.sqlitedb"


def extract(backup: IOSBackup) -> dict:
    db = backup.find_one(_DOMAIN, _PATH)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            """
            SELECT summary, start_date, end_date, location
            FROM CalendarItem ORDER BY start_date ASC
            """,
        )
        for r in rows:
            records.append({
                "title": r["summary"],
                "start": cocoa_to_iso(r["start_date"]),
                "end": cocoa_to_iso(r["end_date"]),
                "location": r["location"],
            })
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
