"""Extract Android call log from the contacts provider (calls table)."""

from __future__ import annotations

from ..sqlite_util import open_ro, safe_query
from ..timeutil import unix_to_iso
from .extraction import AndroidExtraction

ARTIFACT = "calls"
_PACKAGE = "com.android.providers.contacts"
_DB = "contacts2.db"

# CallLog.Calls type codes:
# 1 = incoming, 2 = outgoing, 3 = missed, 4 = voicemail, 5 = rejected, 6 = blocked
_TYPE = {1: "incoming", 2: "outgoing", 3: "missed", 4: "voicemail",
         5: "rejected", 6: "blocked"}


def extract(ext: AndroidExtraction) -> dict:
    db = ext.find_db(_PACKAGE, _DB)
    if not db:
        # Some devices keep the call log in a dedicated calls.db.
        db = ext.find_db(_PACKAGE, "calls.db")
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            "SELECT number, date, duration, type FROM calls ORDER BY date ASC",
        )
        for r in rows:
            records.append(
                {
                    "number": r["number"],
                    "timestamp": unix_to_iso(r["date"], millis=True),
                    "duration_seconds": r["duration"],
                    "type": _TYPE.get(r["type"], str(r["type"])),
                }
            )

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
