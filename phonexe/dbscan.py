"""
Heuristic SQLite scanning shared by iOS and Android collectors.

App schemas drift constantly, so rather than hard-code queries we detect
tables that look like message/event logs (a text-ish column next to a
timestamp-ish column) and dump them defensibly.
"""

from __future__ import annotations

import sqlite3

from .sqlite_util import columns, safe_query

# Column-name hints used to recognise message-like tables.
TEXT_HINTS = ("text", "body", "message", "content", "caption", "comment", "data")
TIME_HINTS = ("date", "time", "timestamp", "created", "sent", "ts")

# Cap rows per table so a chat-heavy device can't blow up memory / report size.
MAX_ROWS = 5000


def message_tables(con: sqlite3.Connection) -> list[str]:
    """Return names of tables that look like message/event logs."""
    tables = [
        r["name"]
        for r in safe_query(
            con, "SELECT name FROM sqlite_master WHERE type='table'"
        )
    ]
    hits = []
    for t in tables:
        cols = {c.lower() for c in columns(con, t)}
        has_text = any(any(h in c for h in TEXT_HINTS) for c in cols)
        has_time = any(any(h in c for h in TIME_HINTS) for c in cols)
        if has_text and has_time:
            hits.append(t)
    return hits


def dump_table(con: sqlite3.Connection, table: str, limit: int = MAX_ROWS) -> list[dict]:
    """Dump up to *limit* rows of *table*, rendering blobs as placeholders."""
    rows = safe_query(con, f'SELECT * FROM "{table}" LIMIT {limit}')
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


# Cap carved deleted fragments per app database so a heavily-churned chat DB
# can't bloat the report.
MAX_DELETED = 500


def deleted_fragments(db_path, limit: int = MAX_DELETED) -> list[dict]:
    """Carve deleted text fragments from an app's SQLite file.

    Thin wrapper over the forensic carver so both the iOS and Android social
    collectors recover the same way. Returns [] on any failure (the carver is
    best-effort and must never abort an examination).
    """
    # Imported lazily to avoid a heavy import for callers that never carve.
    from .forensics.sqlite_recover import recover_deleted

    try:
        return recover_deleted(db_path)[:limit]
    except Exception:
        return []
