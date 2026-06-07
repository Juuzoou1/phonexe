"""
Generic social / chat application collector for Android extractions.

Mirrors the iOS social collector: for each known package, scan its SQLite
databases and surface message-like tables heuristically.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ..dbscan import dump_table, message_tables
from ..sqlite_util import open_ro
from .extraction import AndroidExtraction

ARTIFACT = "social_apps"


@dataclass(frozen=True)
class AppDef:
    key: str
    name: str
    package: str


KNOWN_APPS: tuple[AppDef, ...] = (
    AppDef("instagram", "Instagram", "com.instagram.android"),
    AppDef("snapchat", "Snapchat", "com.snapchat.android"),
    AppDef("discord", "Discord", "com.discord"),
    AppDef("telegram", "Telegram", "org.telegram.messenger"),
    AppDef("signal", "Signal", "org.thoughtcrime.securesms"),
    AppDef("messenger", "Facebook Messenger", "com.facebook.orca"),
    AppDef("tiktok", "TikTok", "com.zhiliaoapp.musically"),
)


def extract(ext: AndroidExtraction) -> dict:
    found: dict[str, dict] = {}

    for app in KNOWN_APPS:
        databases = []
        for db_path in ext.iter_app_databases(app.package):
            db_entry = {"path": str(db_path), "tables": []}
            try:
                with open_ro(db_path) as con:
                    for table in message_tables(con):
                        records = dump_table(con, table)
                        if records:
                            db_entry["tables"].append(
                                {
                                    "table": table,
                                    "count": len(records),
                                    "records": records,
                                }
                            )
            except sqlite3.Error:
                db_entry["error"] = "unreadable (locked/corrupt/encrypted)"
            if db_entry["tables"] or db_entry.get("error"):
                databases.append(db_entry)
        if databases:
            found[app.key] = {"name": app.name, "databases": databases}

    total = sum(
        len(t["records"])
        for app in found.values()
        for db in app["databases"]
        for t in db["tables"]
    )
    return {"artifact": ARTIFACT, "count": total, "apps": found}
