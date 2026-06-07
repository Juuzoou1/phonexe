"""Parse WhatsApp chat artifacts (ChatStorage.sqlite)."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query
from ..timeutil import cocoa_to_iso

ARTIFACT = "whatsapp"
_DOMAIN = "AppDomainGroup-group.net.whatsapp.WhatsApp.shared"
_PATH = "ChatStorage.sqlite"


def extract(backup: IOSBackup) -> dict:
    db = backup.find_one(_DOMAIN, _PATH)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            """
            SELECT m.ZTEXT        AS text,
                   m.ZMESSAGEDATE AS date,
                   m.ZISFROMME    AS is_from_me,
                   m.ZFROMJID     AS from_jid,
                   m.ZTOJID       AS to_jid,
                   s.ZPARTNERNAME AS partner
            FROM ZWAMESSAGE m
            LEFT JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK
            ORDER BY m.ZMESSAGEDATE ASC
            """,
        )
        for r in rows:
            records.append(
                {
                    "timestamp": cocoa_to_iso(r["date"]),
                    "direction": "sent" if r["is_from_me"] else "received",
                    "partner": r["partner"],
                    "from": r["from_jid"],
                    "to": r["to_jid"],
                    "text": r["text"],
                }
            )

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
