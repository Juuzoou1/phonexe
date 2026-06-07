"""
Safe, read-only SQLite access for forensic artifacts.

Artifact schemas drift between iOS / app versions, so queries must tolerate
missing tables and columns rather than crashing a whole examination.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


@contextmanager
def open_ro(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open a SQLite database read-only (never mutates the evidence)."""
    con = sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def columns(con: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {r["name"] for r in con.execute(f'PRAGMA table_info("{table}")')}
    except sqlite3.Error:
        return set()


def safe_query(
    con: sqlite3.Connection, sql: str, params: tuple = ()
) -> list[sqlite3.Row]:
    """Run a query; return [] instead of raising on schema mismatches."""
    try:
        return con.execute(sql, params).fetchall()
    except sqlite3.Error:
        return []


def pick(row: sqlite3.Row, *names: str) -> Optional[object]:
    """Return the first present, non-null value among candidate column names."""
    keys = set(row.keys())
    for n in names:
        if n in keys and row[n] is not None:
            return row[n]
    return None
