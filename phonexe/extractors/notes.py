"""Extract notes (best-effort) from legacy notes.sqlite and modern NoteStore."""

from __future__ import annotations

import re

from ..backup import IOSBackup
from ..sqlite_util import open_ro, safe_query, table_exists

ARTIFACT = "notes"


def _strip_html(text) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", str(text)).strip()


def extract(backup: IOSBackup) -> dict:
    records = []

    # Legacy notes.sqlite (HTML body).
    legacy = backup.find_one("HomeDomain", "Library/Notes/notes.sqlite")
    if legacy:
        with open_ro(legacy) as con:
            if table_exists(con, "ZNOTEBODY"):
                for r in safe_query(con, "SELECT ZCONTENT FROM ZNOTEBODY"):
                    body = _strip_html(r["ZCONTENT"])
                    if body:
                        records.append({"title": body[:40], "content": body})

    # Modern NoteStore.sqlite (titles only — bodies are gzipped protobuf).
    store = backup.find_one(
        "AppDomainGroup-group.com.apple.notes", "NoteStore.sqlite")
    if store:
        with open_ro(store) as con:
            for r in safe_query(
                con,
                "SELECT ZTITLE1, ZSNIPPET FROM ZICCLOUDSYNCINGOBJECT "
                "WHERE ZTITLE1 IS NOT NULL",
            ):
                records.append({
                    "title": r["ZTITLE1"],
                    "content": r["ZSNIPPET"] or "",
                })

    return {"artifact": ARTIFACT, "count": len(records), "records": records}
