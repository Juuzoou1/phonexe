"""Extract the device address book (contacts)."""

from __future__ import annotations

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query
from ..timeutil import cocoa_to_iso

ARTIFACT = "contacts"
_DOMAIN = "HomeDomain"
_PATH = "Library/AddressBook/AddressBook.sqlitedb"


def extract(backup: IOSBackup) -> dict:
    db = backup.find_one(_DOMAIN, _PATH)
    if not db:
        return {"artifact": ARTIFACT, "count": 0, "records": []}

    records = []
    with open_ro(db) as con:
        people = safe_query(
            con,
            """
            SELECT ROWID, First, Last, Organization, Note,
                   CreationDate, ModificationDate
            FROM ABPerson
            """,
        )
        for p in people:
            values = safe_query(
                con,
                "SELECT property, value FROM ABMultiValue WHERE record_id = ?",
                (p["ROWID"],),
            )
            phones = [v["value"] for v in values if v["property"] == 3]
            emails = [v["value"] for v in values if v["property"] == 4]
            name = " ".join(
                x for x in (p["First"], p["Last"]) if x
            ).strip()
            records.append(
                {
                    "name": name or None,
                    "organization": p["Organization"],
                    "phones": phones,
                    "emails": emails,
                    "note": p["Note"],
                    "created": cocoa_to_iso(p["CreationDate"]),
                    "modified": cocoa_to_iso(p["ModificationDate"]),
                }
            )

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
