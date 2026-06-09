"""Extract voicemail messages from voicemail.db.

iOS stores visual-voicemail metadata in HomeDomain at
``Library/Voicemail/voicemail.db``. The audio (.amr) lives next to it but is
not required to recover the forensically interesting fields: who left the
voicemail, when, how long it was, and whether it was deleted (trashed).
"""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, pick, safe_query
from ..timeutil import unix_to_iso

ARTIFACT = "voicemail"
_DOMAIN = "HomeDomain"
_PATH = "Library/Voicemail/voicemail.db"


def extract(backup: IOSBackup) -> dict:
    db = backup.find_one(_DOMAIN, _PATH)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        # `date` is a unix epoch (seconds); `trashed_date` is non-zero once the
        # voicemail has been moved to the Deleted folder.
        rows = safe_query(
            con,
            """
            SELECT ROWID, sender, callback_num, date, duration, trashed_date
            FROM voicemail
            WHERE sender IS NOT NULL OR duration IS NOT NULL
            ORDER BY date ASC
            """,
        )
        for r in rows:
            trashed = pick(r, "trashed_date")
            records.append({
                "sender": pick(r, "sender", "callback_num"),
                "timestamp": unix_to_iso(r["date"]),
                "duration_seconds": r["duration"],
                "deleted": bool(trashed),
            })
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
