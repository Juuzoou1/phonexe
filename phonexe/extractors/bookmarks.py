"""Extract Safari bookmarks from Bookmarks.db."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query

ARTIFACT = "safari_bookmarks"
_DOMAIN = "AppDomainGroup-group.com.apple.safari"
_PATH = "Library/Safari/Bookmarks.db"


def extract(backup: IOSBackup) -> dict:
    db = backup.find_one(_DOMAIN, _PATH)
    if not db:
        db = backup.find_one("HomeDomain", "Library/Safari/Bookmarks.db")
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            "SELECT title, url FROM bookmarks WHERE url IS NOT NULL "
            "AND url <> ''",
        )
        for r in rows:
            records.append({"title": r["title"], "url": r["url"]})
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
