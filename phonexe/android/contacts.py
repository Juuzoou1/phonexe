"""Extract Android contacts from contacts2.db."""

from __future__ import annotations

from ..sqlite_util import open_ro, safe_query
from .extraction import AndroidExtraction

ARTIFACT = "contacts"
_PACKAGE = "com.android.providers.contacts"
_DB = "contacts2.db"

_NAME_MIME = "vnd.android.cursor.item/name"
_PHONE_MIME = "vnd.android.cursor.item/phone_v2"
_EMAIL_MIME = "vnd.android.cursor.item/email_v2"


def extract(ext: AndroidExtraction) -> dict:
    db = ext.find_db(_PACKAGE, _DB)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    people: dict[int, dict] = {}
    with open_ro(db) as con:
        rows = safe_query(
            con,
            """
            SELECT d.raw_contact_id AS rid, m.mimetype AS mime, d.data1 AS v
            FROM data d
            JOIN mimetypes m ON d.mimetype_id = m._id
            """,
        )
        for r in rows:
            rid = r["rid"]
            rec = people.setdefault(
                rid, {"name": None, "phones": [], "emails": []}
            )
            if r["mime"] == _NAME_MIME and r["v"]:
                rec["name"] = r["v"]
            elif r["mime"] == _PHONE_MIME and r["v"]:
                rec["phones"].append(r["v"])
            elif r["mime"] == _EMAIL_MIME and r["v"]:
                rec["emails"].append(r["v"])

    records = list(people.values())
    return {"artifact": ARTIFACT, "count": len(records), "records": records}
