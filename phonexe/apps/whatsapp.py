"""Parse WhatsApp chat artifacts (ChatStorage.sqlite)."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import columns, open_ro, safe_query, table_exists
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
        cols = columns(con, "ZWAMESSAGE")
        has_geo = {"ZLATITUDE", "ZLONGITUDE"} <= cols
        has_media = table_exists(con, "ZWAMEDIAITEM")

        select = [
            "m.ZTEXT AS text",
            "m.ZMESSAGEDATE AS date",
            "m.ZISFROMME AS is_from_me",
            "m.ZFROMJID AS from_jid",
            "m.ZTOJID AS to_jid",
            "s.ZPARTNERNAME AS partner",
        ]
        if has_geo:
            select += ["m.ZLATITUDE AS lat", "m.ZLONGITUDE AS lon"]
        joins = "LEFT JOIN ZWACHATSESSION s ON m.ZCHATSESSION = s.Z_PK"
        if has_media:
            select.append("md.ZMEDIALOCALPATH AS media")
            joins += " LEFT JOIN ZWAMEDIAITEM md ON m.ZMEDIAITEM = md.Z_PK"

        rows = safe_query(
            con,
            f"SELECT {', '.join(select)} FROM ZWAMESSAGE m {joins} "
            "ORDER BY m.ZMESSAGEDATE ASC",
        )
        for r in rows:
            keys = set(r.keys())
            rec = {
                "timestamp": cocoa_to_iso(r["date"]),
                "direction": "sent" if r["is_from_me"] else "received",
                "partner": r["partner"],
                "from": r["from_jid"],
                "to": r["to_jid"],
                "text": r["text"],
            }
            if "lat" in keys and r["lat"]:
                rec["latitude"] = r["lat"]
                rec["longitude"] = r["lon"]
            if "media" in keys and r["media"]:
                rec["media"] = r["media"]
            records.append(rec)

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
