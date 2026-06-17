"""Recover deleted records from an iOS backup's key SQLite databases."""

from __future__ import annotations

from ..apps.social import KNOWN_APPS
from ..backup import IOSBackup
from ..forensics.sqlite_recover import recover_deleted

ARTIFACT = "deleted"

# (friendly label, domain, relative path) for the databases worth carving.
_TARGETS = [
    ("Messages (SMS/iMessage)", "HomeDomain", "Library/SMS/sms.db"),
    ("Contacts", "HomeDomain", "Library/AddressBook/AddressBook.sqlitedb"),
    ("Call History", "HomeDomain",
     "Library/CallHistoryDB/CallHistory.storedata"),
    ("WhatsApp", "AppDomainGroup-group.net.whatsapp.WhatsApp.shared",
     "ChatStorage.sqlite"),
]


def extract(backup: IOSBackup) -> dict:
    records = []

    for label, domain, rel in _TARGETS:
        db = backup.find_one(domain, rel)
        if db:
            for frag in recover_deleted(db):
                records.append({"source": label, **frag})

    # social/chat app databases (Instagram, Snapchat, Discord, ...)
    for f in backup.iter_files():
        if not f.is_file or not f.relative_path.lower().endswith(
            (".db", ".sqlite", ".sqlitedb")
        ):
            continue
        app = next(
            (a for a in KNOWN_APPS
             if any(m in f.domain for m in a.domain_markers)),
            None,
        )
        if not app:
            continue
        payload = backup.resolve(f)
        if payload:
            for frag in recover_deleted(payload):
                records.append({"source": app.name, **frag})

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
