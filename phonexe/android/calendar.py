"""Extract Android calendar events from the calendar provider."""

from __future__ import annotations

from ..sqlite_util import open_ro, safe_query
from ..timeutil import unix_to_iso
from .extraction import AndroidExtraction

ARTIFACT = "calendar"
_PACKAGE = "com.android.providers.calendar"
_DB = "calendar.db"


def extract(ext: AndroidExtraction) -> dict:
    db = ext.find_db(_PACKAGE, _DB)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            "SELECT title, dtstart, dtend, eventLocation, description "
            "FROM Events ORDER BY dtstart ASC",
        )
        for r in rows:
            records.append({
                "title": r["title"],
                "start": unix_to_iso(r["dtstart"], millis=True),
                "end": unix_to_iso(r["dtend"], millis=True),
                "location": r["eventLocation"],
            })
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
