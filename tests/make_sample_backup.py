"""
Generate a synthetic (fake) iOS backup for testing phonexe.

This fabricates the same on-disk structure a real iOS 10+ backup uses
(Manifest.db + hashed payload files) but with entirely made-up data, so the
extraction pipeline can be exercised without any real device evidence.
"""

from __future__ import annotations

import hashlib
import plistlib
import sqlite3
from pathlib import Path

# Mac Absolute Time for 2023-06-01T12:00:00Z (seconds since 2001-01-01).
_T = 707400000


def _file_id(domain: str, relative_path: str) -> str:
    return hashlib.sha1(f"{domain}-{relative_path}".encode()).hexdigest()


def _store_payload(root: Path, file_id: str, data: bytes) -> None:
    sub = root / file_id[:2]
    sub.mkdir(parents=True, exist_ok=True)
    (sub / file_id).write_bytes(data)


def _sqlite_bytes(builder) -> bytes:
    """Run *builder* against a temp on-disk DB and return its raw bytes."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        path = Path(tmp.name)
    con = sqlite3.connect(path)
    builder(con)
    con.commit()
    con.close()
    data = path.read_bytes()
    path.unlink()
    return data


def _build_addressbook(con):
    con.execute(
        "CREATE TABLE ABPerson(ROWID INTEGER PRIMARY KEY, First, Last, "
        "Organization, Note, CreationDate, ModificationDate)"
    )
    con.execute(
        "CREATE TABLE ABMultiValue(record_id INTEGER, property INTEGER, value)"
    )
    con.execute(
        "INSERT INTO ABPerson VALUES(1,'Sara','Ahmed','ACME','vip',?,?)",
        (_T, _T),
    )
    con.execute("INSERT INTO ABMultiValue VALUES(1,3,'+966500000001')")
    con.execute("INSERT INTO ABMultiValue VALUES(1,4,'sara@example.com')")


def _build_sms(con):
    con.execute("CREATE TABLE handle(ROWID INTEGER PRIMARY KEY, id)")
    con.execute(
        "CREATE TABLE message(ROWID INTEGER PRIMARY KEY, text, date, "
        "is_from_me, service, handle_id)"
    )
    con.execute("CREATE TABLE chat(ROWID INTEGER PRIMARY KEY, display_name, "
                "chat_identifier)")
    con.execute("CREATE TABLE chat_message_join(chat_id, message_id)")
    con.execute("INSERT INTO handle VALUES(1,'+966500000001')")
    con.execute("INSERT INTO chat VALUES(1,'Sara','+966500000001')")
    con.execute(
        "INSERT INTO message VALUES(1,'Hello from the suspect',?,0,'iMessage',1)",
        (_T * 1_000_000_000,),
    )
    con.execute(
        "INSERT INTO message VALUES(2,'Reply text',?,1,'SMS',1)",
        ((_T + 60) * 1_000_000_000,),
    )
    con.execute("INSERT INTO chat_message_join VALUES(1,1)")
    con.execute("INSERT INTO chat_message_join VALUES(1,2)")


def _build_calls(con):
    con.execute(
        "CREATE TABLE ZCALLRECORD(Z_PK INTEGER PRIMARY KEY, ZADDRESS, ZDATE, "
        "ZDURATION, ZORIGINATED, ZCALLTYPE, ZSERVICE_PROVIDER)"
    )
    con.execute(
        "INSERT INTO ZCALLRECORD VALUES(1,?,?,42,1,1,'com.apple.Telephony')",
        (b"+966500000001", _T),
    )


def _make_whatsapp_builder(image_path: str):
    def _build_whatsapp(con):
        con.execute(
            "CREATE TABLE ZWACHATSESSION(Z_PK INTEGER PRIMARY KEY, ZCONTACTJID, "
            "ZPARTNERNAME)"
        )
        con.execute(
            "CREATE TABLE ZWAMEDIAITEM(Z_PK INTEGER PRIMARY KEY, ZMEDIALOCALPATH)"
        )
        con.execute(
            "CREATE TABLE ZWAMESSAGE(Z_PK INTEGER PRIMARY KEY, ZTEXT, "
            "ZMESSAGEDATE, ZISFROMME, ZFROMJID, ZTOJID, ZCHATSESSION, "
            "ZLATITUDE, ZLONGITUDE, ZMEDIAITEM)"
        )
        con.execute(
            "INSERT INTO ZWACHATSESSION VALUES(1,'1@s.whatsapp.net','Sara')"
        )
        con.execute("INSERT INTO ZWAMEDIAITEM VALUES(1,?)", (image_path,))
        # text, location, image, reply
        con.execute(
            "INSERT INTO ZWAMESSAGE VALUES(1,'مرحبا، وين نتقابل؟',?,0,"
            "'1@s.whatsapp.net','me',1,NULL,NULL,NULL)", (_T,))
        con.execute(
            "INSERT INTO ZWAMESSAGE VALUES(2,'موقعي الحين',?,0,"
            "'1@s.whatsapp.net','me',1,24.7136,46.6753,NULL)", (_T + 60,))
        con.execute(
            "INSERT INTO ZWAMESSAGE VALUES(3,'شوف الصورة',?,1,'me',"
            "'1@s.whatsapp.net',1,NULL,NULL,1)", (_T + 120,))
        con.execute(
            "INSERT INTO ZWAMESSAGE VALUES(4,'تمام، جاي',?,1,'me',"
            "'1@s.whatsapp.net',1,NULL,NULL,NULL)", (_T + 180,))
    return _build_whatsapp


def _build_instagram(con):
    # Mimic a generic message-like table the social collector should detect,
    # including an in-chat shared location.
    con.execute(
        "CREATE TABLE direct_messages(pk INTEGER PRIMARY KEY, text, "
        "timestamp, sender, latitude, longitude)"
    )
    con.execute(
        "INSERT INTO direct_messages VALUES"
        "(1,'ig dm hello',1685620800,'sara',NULL,NULL)"
    )
    con.execute(
        "INSERT INTO direct_messages VALUES"
        "(2,'هنا الكافيه',1685620900,'sara',21.4225,39.8262)"
    )


def _write_sample_image(path: Path) -> None:
    """Write a tiny placeholder image used as a chat media attachment."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image

        Image.new("RGB", (240, 160), (34, 211, 238)).save(path)
    except Exception:
        # 1x1 PNG fallback if Pillow is unavailable
        png = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108020000"
            "00907753de0000000c4944415408d763f8cfc0f01f00050001ff"
            "a3d4e60000000049454e44ae426082"
        )
        path.write_bytes(png)


def build(root: str | Path) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)

    # Create a real media file so the chat viewer can display it inline.
    media = root / "media" / "wa_photo.png"
    _write_sample_image(media)

    files = [
        ("HomeDomain", "Library/AddressBook/AddressBook.sqlitedb",
         _sqlite_bytes(_build_addressbook)),
        ("HomeDomain", "Library/SMS/sms.db", _sqlite_bytes(_build_sms)),
        ("HomeDomain", "Library/CallHistoryDB/CallHistory.storedata",
         _sqlite_bytes(_build_calls)),
        ("AppDomainGroup-group.net.whatsapp.WhatsApp.shared",
         "ChatStorage.sqlite",
         _sqlite_bytes(_make_whatsapp_builder(str(media.resolve())))),
        ("AppDomain-com.burbn.instagram", "Documents/direct.db",
         _sqlite_bytes(_build_instagram)),
    ]

    # Build Manifest.db.
    manifest = root / "Manifest.db"
    if manifest.exists():
        manifest.unlink()
    con = sqlite3.connect(manifest)
    con.execute(
        "CREATE TABLE Files(fileID TEXT PRIMARY KEY, domain TEXT, "
        "relativePath TEXT, flags INTEGER, file BLOB)"
    )
    for domain, rel, data in files:
        fid = _file_id(domain, rel)
        con.execute(
            "INSERT INTO Files VALUES(?,?,?,1,NULL)", (fid, domain, rel)
        )
        _store_payload(root, fid, data)
    con.commit()
    con.close()

    # Info.plist / Manifest.plist.
    (root / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "Device Name": "Suspect iPhone",
                "Product Type": "iPhone14,2",
                "Product Version": "16.5",
                "Serial Number": "F2LXXSAMPLE",
                "IMEI": "350000000000001",
                "Phone Number": "+966500000000",
            }
        )
    )
    (root / "Manifest.plist").write_bytes(
        plistlib.dumps({"IsEncrypted": False})
    )
    return root


if __name__ == "__main__":
    import sys

    dest = sys.argv[1] if len(sys.argv) > 1 else "sample/backup"
    print("Sample backup created at:", build(dest))
