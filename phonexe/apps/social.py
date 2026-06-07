"""
Generic social / chat application artifact collector.

Apps such as Instagram, Snapchat, Discord and Telegram change their local
storage schemas frequently, so hard-coded queries rot quickly. Instead, for
each known app we locate its SQLite databases inside the backup, then
heuristically surface the tables that look like message/event logs (i.e.
they contain a text-ish column alongside a timestamp-ish column).

This produces a defensible inventory of recoverable local artifacts without
pretending to perfectly normalize every app's private schema.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ..backup import IOSBackup
from ..dbscan import dump_table, message_tables
from ..sqlite_util import open_ro

ARTIFACT = "social_apps"


@dataclass(frozen=True)
class AppDef:
    key: str
    name: str
    # domain prefixes whose files belong to this app
    domain_markers: tuple[str, ...]


# Known apps of interest. Matching is by substring against the file domain,
# so both AppDomain-<bundle> and AppDomainGroup-group.<bundle> are covered.
KNOWN_APPS: tuple[AppDef, ...] = (
    AppDef("instagram", "Instagram", ("com.burbn.instagram",)),
    AppDef("snapchat", "Snapchat", ("com.toyopagroup.picaboo",)),
    AppDef("discord", "Discord", ("com.hammerandchisel.discord",)),
    AppDef("telegram", "Telegram", ("ph.telegra.Telegraph", "org.telegram")),
    AppDef("signal", "Signal", ("org.whispersystems.signal",)),
    AppDef("messenger", "Facebook Messenger", ("com.facebook.Messenger",)),
    AppDef("tiktok", "TikTok", ("com.zhiliaoapp.musically", "com.ss.iphone")),
)

_DB_SUFFIXES = (".sqlite", ".db", ".sqlitedb", ".sql")


def _is_db(relative_path: str) -> bool:
    return relative_path.lower().endswith(_DB_SUFFIXES)


def _match_app(domain: str) -> AppDef | None:
    for app in KNOWN_APPS:
        if any(marker in domain for marker in app.domain_markers):
            return app
    return None


def extract(backup: IOSBackup) -> dict:
    # app key -> {name, databases: [...]}
    found: dict[str, dict] = {}

    for f in backup.iter_files():
        if not f.is_file or not _is_db(f.relative_path):
            continue
        app = _match_app(f.domain)
        if not app:
            continue
        payload = backup.resolve(f)
        if not payload:
            continue

        db_entry = {
            "relative_path": f.relative_path,
            "stored_at": str(payload),
            "tables": [],
        }
        try:
            with open_ro(payload) as con:
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

        bucket = found.setdefault(
            app.key, {"name": app.name, "databases": []}
        )
        bucket["databases"].append(db_entry)

    total = sum(
        len(t["records"])
        for app in found.values()
        for db in app["databases"]
        for t in db["tables"]
    )
    return {"artifact": ARTIFACT, "count": total, "apps": found}
