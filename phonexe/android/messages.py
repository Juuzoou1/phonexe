"""Extract Android SMS/MMS from the telephony provider (mmssms.db)."""

from __future__ import annotations

from ..sqlite_util import open_ro, safe_query
from ..timeutil import unix_to_iso
from .extraction import AndroidExtraction

ARTIFACT = "messages"
_PACKAGE = "com.android.providers.telephony"
_DB = "mmssms.db"

# SMS type codes (android.provider.Telephony.Sms):
# 1 = inbox (received), 2 = sent, 3 = draft, 4 = outbox, 5 = failed, 6 = queued
_DIRECTION = {1: "received", 2: "sent", 3: "draft", 4: "outbox",
              5: "failed", 6: "queued"}


def extract(ext: AndroidExtraction) -> dict:
    db = ext.find_db(_PACKAGE, _DB)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            "SELECT address, body, date, type, read FROM sms ORDER BY date ASC",
        )
        for r in rows:
            records.append(
                {
                    "address": r["address"],
                    "timestamp": unix_to_iso(r["date"], millis=True),
                    "direction": _DIRECTION.get(r["type"], str(r["type"])),
                    "read": bool(r["read"]) if r["read"] is not None else None,
                    "text": r["body"],
                }
            )

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
