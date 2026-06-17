"""Extract SMS / iMessage conversations from sms.db."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query
from ..timeutil import cocoa_to_iso

ARTIFACT = "messages"
_DOMAIN = "HomeDomain"
_PATH = "Library/SMS/sms.db"


def extract(backup: IOSBackup) -> dict:
    db = backup.find_one(_DOMAIN, _PATH)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            """
            SELECT
                m.ROWID            AS id,
                m.text             AS text,
                m.date             AS date,
                m.is_from_me       AS is_from_me,
                m.service          AS service,
                h.id               AS handle,
                c.display_name     AS chat_name,
                c.chat_identifier  AS chat_identifier
            FROM message m
            LEFT JOIN handle h            ON m.handle_id = h.ROWID
            LEFT JOIN chat_message_join j ON m.ROWID = j.message_id
            LEFT JOIN chat c              ON j.chat_id = c.ROWID
            ORDER BY m.date ASC
            """,
        )
        for r in rows:
            records.append(
                {
                    "id": r["id"],
                    "timestamp": cocoa_to_iso(r["date"]),
                    "direction": "sent" if r["is_from_me"] else "received",
                    "service": r["service"],
                    "counterpart": r["handle"],
                    "chat": r["chat_name"] or r["chat_identifier"],
                    "text": r["text"],
                }
            )

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
