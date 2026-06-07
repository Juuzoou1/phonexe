"""Extract call history from CallHistory.storedata."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query
from ..timeutil import cocoa_to_iso

ARTIFACT = "calls"
_DOMAIN = "HomeDomain"
_PATH = "Library/CallHistoryDB/CallHistory.storedata"


def extract(backup: IOSBackup) -> dict:
    db = backup.find_one(_DOMAIN, _PATH)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        rows = safe_query(
            con,
            """
            SELECT ZADDRESS, ZDATE, ZDURATION, ZORIGINATED,
                   ZCALLTYPE, ZSERVICE_PROVIDER
            FROM ZCALLRECORD
            ORDER BY ZDATE ASC
            """,
        )
        for r in rows:
            addr = r["ZADDRESS"]
            if isinstance(addr, (bytes, bytearray)):
                addr = addr.decode("utf-8", "replace")
            records.append(
                {
                    "number": addr,
                    "timestamp": cocoa_to_iso(r["ZDATE"]),
                    "duration_seconds": r["ZDURATION"],
                    "direction": "outgoing" if r["ZORIGINATED"] else "incoming",
                    "provider": r["ZSERVICE_PROVIDER"],
                }
            )

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
