"""Parse WhatsApp for Android (msgstore.db)."""

from __future__ import annotations

from ..sqlite_util import open_ro, safe_query, table_exists
from ..timeutil import unix_to_iso
from .extraction import AndroidExtraction

ARTIFACT = "whatsapp"
_PACKAGE = "com.whatsapp"
_DB = "msgstore.db"


def extract(ext: AndroidExtraction) -> dict:
    db = ext.find_db(_PACKAGE, _DB)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        if table_exists(con, "messages"):
            # Classic schema.
            rows = safe_query(
                con,
                """
                SELECT key_remote_jid AS jid, key_from_me AS from_me,
                       data AS text, timestamp AS ts
                FROM messages ORDER BY timestamp ASC
                """,
            )
            for r in rows:
                records.append(
                    {
                        "timestamp": unix_to_iso(r["ts"], millis=True),
                        "direction": "sent" if r["from_me"] else "received",
                        "chat": r["jid"],
                        "text": r["text"],
                    }
                )
        elif table_exists(con, "message"):
            # Newer schema (text in message.text_data).
            rows = safe_query(
                con,
                """
                SELECT from_me, text_data AS text, timestamp AS ts
                FROM message ORDER BY timestamp ASC
                """,
            )
            for r in rows:
                records.append(
                    {
                        "timestamp": unix_to_iso(r["ts"], millis=True),
                        "direction": "sent" if r["from_me"] else "received",
                        "text": r["text"],
                    }
                )

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
