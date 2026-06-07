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
from ..sqlite_util import columns, open_ro, safe_query

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

# Column-name hints used to recognise message-like tables.
_TEXT_HINTS = ("text", "body", "message", "content", "caption", "comment")
_TIME_HINTS = ("date", "time", "timestamp", "created", "sent", "ts")
_DB_SUFFIXES = (".sqlite", ".db", ".sqlitedb", ".sql")

# Cap rows per table so a chat-heavy device can't blow up memory / report size.
_MAX_ROWS = 5000


def _is_db(relative_path: str) -> bool:
    return relative_path.lower().endswith(_DB_SUFFIXES)


def _message_tables(con: sqlite3.Connection) -> list[str]:
    tables = [
        r["name"]
        for r in safe_query(
            con,
            "SELECT name FROM sqlite_master WHERE type='table'",
        )
    ]
    hits = []
    for t in tables:
        cols = {c.lower() for c in columns(con, t)}
        has_text = any(any(h in c for h in _TEXT_HINTS) for c in cols)
        has_time = any(any(h in c for h in _TIME_HINTS) for c in cols)
        if has_text and has_time:
            hits.append(t)
    return hits


def _dump_table(con: sqlite3.Connection, table: str) -> list[dict]:
    rows = safe_query(con, f'SELECT * FROM "{table}" LIMIT {_MAX_ROWS}')
    out = []
    for r in rows:
        rec = {}
        for k in r.keys():
            v = r[k]
            if isinstance(v, (bytes, bytearray)):
                v = f"<blob {len(v)} bytes>"
            rec[k] = v
        out.append(rec)
    return out


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
                for table in _message_tables(con):
                    records = _dump_table(con, table)
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
