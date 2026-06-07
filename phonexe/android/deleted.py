"""Recover deleted records from an Android extraction's SQLite databases."""

from __future__ import annotations

from ..forensics.sqlite_recover import recover_deleted
from .extraction import AndroidExtraction
from .social import KNOWN_APPS

ARTIFACT = "deleted"

# (friendly label, package, db filename)
_TARGETS = [
    ("Messages (SMS/MMS)", "com.android.providers.telephony", "mmssms.db"),
    ("Contacts", "com.android.providers.contacts", "contacts2.db"),
    ("WhatsApp", "com.whatsapp", "msgstore.db"),
]


def extract(ext: AndroidExtraction) -> dict:
    records = []

    for label, package, db_name in _TARGETS:
        db = ext.find_db(package, db_name)
        if db:
            for frag in recover_deleted(db):
                records.append({"source": label, **frag})

    for app in KNOWN_APPS:
        for db_path in ext.iter_app_databases(app.package):
            for frag in recover_deleted(db_path):
                records.append({"source": app.name, **frag})

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
