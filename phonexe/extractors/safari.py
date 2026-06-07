"""Extract Safari browsing history and bookmarks."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query
from ..timeutil import cocoa_to_iso

ARTIFACT = "safari_history"
_DOMAIN = "AppDomainGroup-group.com.apple.safari"
_HISTORY = "Library/Safari/History.db"


def extract(backup: IOSBackup) -> dict:
    db = backup.find_one(_DOMAIN, _HISTORY)
    if not db:
        # Older iOS kept Safari history under HomeDomain.
        db = backup.find_one("HomeDomain", "Library/Safari/History.db")
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            """
            SELECT i.url        AS url,
                   i.visit_count AS visit_count,
                   v.title      AS title,
                   v.visit_time AS visit_time
            FROM history_visits v
            JOIN history_items i ON v.history_item = i.id
            ORDER BY v.visit_time ASC
            """,
        )
        for r in rows:
            records.append(
                {
                    "url": r["url"],
                    "title": r["title"],
                    "visit_count": r["visit_count"],
                    # Safari visit_time is Mac Absolute Time (seconds).
                    "timestamp": cocoa_to_iso(r["visit_time"]),
                }
            )

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
