"""
Generate a synthetic (fake) Android /data extraction for testing.

Recreates the conventional /data/data/<package>/databases/<db> layout with
entirely fabricated data so the Android pipeline can be exercised without any
real device evidence.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# Unix epoch milliseconds for 2023-06-01T12:00:00Z.
_T_MS = 1685620800000


def _db(path: Path, builder) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    builder(con)
    con.commit()
    con.close()


def _build_contacts(con):
    con.execute("CREATE TABLE mimetypes(_id INTEGER PRIMARY KEY, mimetype)")
    con.execute(
        "CREATE TABLE data(_id INTEGER PRIMARY KEY, raw_contact_id, "
        "mimetype_id, data1)"
    )
    con.execute("CREATE TABLE calls(_id INTEGER PRIMARY KEY, number, date, "
                "duration, type)")
    con.execute("INSERT INTO mimetypes VALUES(1,'vnd.android.cursor.item/name')")
    con.execute(
        "INSERT INTO mimetypes VALUES(2,'vnd.android.cursor.item/phone_v2')"
    )
    con.execute(
        "INSERT INTO mimetypes VALUES(3,'vnd.android.cursor.item/email_v2')"
    )
    con.execute("INSERT INTO data VALUES(1,1,1,'Khalid Noor')")
    con.execute("INSERT INTO data VALUES(2,1,2,'+966500000002')")
    con.execute("INSERT INTO data VALUES(3,1,3,'khalid@example.com')")
    con.execute(
        "INSERT INTO calls VALUES(1,'+966500000002',?,33,2)", (_T_MS,)
    )


def _build_telephony(con):
    con.execute(
        "CREATE TABLE sms(_id INTEGER PRIMARY KEY, address, body, date, "
        "type, read)"
    )
    con.execute(
        "INSERT INTO sms VALUES(1,'+966500000002','android sms hi',?,1,1)",
        (_T_MS,),
    )
    con.execute(
        "INSERT INTO sms VALUES(2,'+966500000002','reply',?,2,1)",
        (_T_MS + 60000,),
    )


def _build_whatsapp(con):
    con.execute(
        "CREATE TABLE messages(_id INTEGER PRIMARY KEY, key_remote_jid, "
        "key_from_me, data, timestamp)"
    )
    con.execute(
        "INSERT INTO messages VALUES(1,'2@s.whatsapp.net',0,'wa android',?)",
        (_T_MS,),
    )


def _build_instagram(con):
    con.execute(
        "CREATE TABLE messages(pk INTEGER PRIMARY KEY, text, timestamp, "
        "user_id)"
    )
    con.execute(
        "INSERT INTO messages VALUES(1,'ig android dm',?,'khalid')", (_T_MS,)
    )


def build(root: str | Path) -> Path:
    root = Path(root)
    base = root / "data" / "data"

    _db(base / "com.android.providers.contacts" / "databases" / "contacts2.db",
        _build_contacts)
    _db(base / "com.android.providers.telephony" / "databases" / "mmssms.db",
        _build_telephony)
    _db(base / "com.whatsapp" / "databases" / "msgstore.db", _build_whatsapp)
    _db(base / "com.instagram.android" / "databases" / "direct.db",
        _build_instagram)

    # Minimal build.prop for device info.
    sysdir = root / "system"
    sysdir.mkdir(parents=True, exist_ok=True)
    (sysdir / "build.prop").write_text(
        "ro.product.manufacturer=Samsung\n"
        "ro.product.model=SM-G991B\n"
        "ro.product.brand=samsung\n"
        "ro.build.version.release=13\n"
        "ro.build.version.sdk=33\n"
        "ro.serialno=R5SAMPLE123\n"
    )
    return root


if __name__ == "__main__":
    import sys

    dest = sys.argv[1] if len(sys.argv) > 1 else "sample/android"
    print("Sample Android extraction created at:", build(dest))
