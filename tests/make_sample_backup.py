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
    # Keep deleted bytes on disk (as on most real devices) so they remain
    # carvable; SQLite is otherwise sometimes built with secure_delete on.
    con.execute("PRAGMA secure_delete=OFF")
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
    # Insert two messages and then delete them so the carver can recover
    # their contents from the resulting SQLite freeblocks.
    con.execute(
        "INSERT INTO message VALUES(3,"
        "'DELETED secret meeting at the port tonight',?,1,'SMS',1)",
        ((_T + 120) * 1_000_000_000,),
    )
    con.execute(
        "INSERT INTO message VALUES(4,'DELETED please erase this chat',?,1,"
        "'SMS',1)",
        ((_T + 180) * 1_000_000_000,),
    )
    # Commit so the rows are written to disk pages, then delete them in a
    # second transaction — this leaves the original bytes in freeblocks,
    # exactly like a real deletion the carver can recover.
    con.commit()
    con.execute("DELETE FROM message WHERE ROWID IN (3,4)")


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
        sessions = [
            (1, "Sara"), (2, "أحمد"), (3, "سالم الحربي"),
            (4, "فهد"), (5, "نورة"), (6, "خالد العتيبي"),
        ]
        for pk, name in sessions:
            con.execute("INSERT INTO ZWACHATSESSION VALUES(?,?,?)",
                        (pk, f"{pk}@s.whatsapp.net", name))
        con.execute("INSERT INTO ZWAMEDIAITEM VALUES(1,?)", (image_path,))

        rows = [
            # (text, from_me, session, lat, lon, media)
            ("مرحبا، وين نتقابل؟", 0, 1, None, None, None),
            ("موقعي الحين", 0, 1, 25.2854, 51.5310, None),
            ("شوف الصورة", 1, 1, None, None, 1),
            ("تمام، جاي", 1, 1, None, None, None),
            ("وصلت الجهاز اللي تبيه؟", 0, 2, None, None, None),
            ("إي وصل، شكراً", 1, 2, None, None, None),
            ("تواصل معي بكرة الصبح", 0, 3, None, None, None),
            ("الاجتماع الساعة ٥", 0, 4, None, None, None),
            ("اوكي ثانكس", 1, 4, None, None, None),
            ("ارسلت لك الملفات", 0, 5, None, None, None),
            ("استلمتها", 1, 5, None, None, None),
            ("نشوفك في المكتب", 0, 6, None, None, None),
        ]
        for i, (text, fm, sess, lat, lon, media) in enumerate(rows, start=1):
            jid = f"{sess}@s.whatsapp.net"
            frm = "me" if fm else jid
            to = jid if fm else "me"
            con.execute(
                "INSERT INTO ZWAMESSAGE VALUES(?,?,?,?,?,?,?,?,?,?)",
                (i, text, _T + i * 60, fm, frm, to, sess, lat, lon, media))
    return _build_whatsapp


def _make_instagram_builder(image_path: str):
    def _build_instagram(con):
        # Generic message-like table the social collector detects, including
        # an in-chat shared location and an image (used for the Stories strip).
        con.execute(
            "CREATE TABLE direct_messages(pk INTEGER PRIMARY KEY, text, "
            "timestamp, sender, latitude, longitude, image)"
        )
        con.execute(
            "INSERT INTO direct_messages VALUES"
            "(1,'ig dm hello',1685620800,'sara',NULL,NULL,NULL)"
        )
        con.execute(
            "INSERT INTO direct_messages VALUES"
            "(2,'هنا الكافيه',1685620900,'sara',25.2760,51.5200,NULL)"
        )
        con.execute(
            "INSERT INTO direct_messages VALUES"
            "(3,'شوف ستوري',1685621000,'noor',NULL,NULL,?)", (image_path,)
        )
    return _build_instagram


def _build_bookmarks(con):
    con.execute(
        "CREATE TABLE bookmarks(id INTEGER PRIMARY KEY, title, url)"
    )
    con.execute(
        "INSERT INTO bookmarks VALUES(1,'Example Site','https://example.com')"
    )
    con.execute(
        "INSERT INTO bookmarks VALUES(2,'Folder',NULL)"
    )


def _build_chrome(con):
    con.execute(
        "CREATE TABLE urls(id INTEGER PRIMARY KEY, url, title, visit_count, "
        "last_visit_time)"
    )
    # Chrome time = (unix + 11644473600) * 1e6
    chrome_ts = int((1685620800 + 11644473600) * 1_000_000)
    con.execute(
        "INSERT INTO urls VALUES(1,'https://example.com','Example',5,?)",
        (chrome_ts,),
    )


def _build_calendar(con):
    con.execute(
        "CREATE TABLE CalendarItem(ROWID INTEGER PRIMARY KEY, summary, "
        "start_date, end_date, location)"
    )
    con.execute(
        "INSERT INTO CalendarItem VALUES(1,'اجتماع المشروع',?,?,'الدوحة')",
        (_T, _T + 3600),
    )


def _build_notes(con):
    con.execute("CREATE TABLE ZNOTEBODY(Z_PK INTEGER PRIMARY KEY, ZCONTENT)")
    con.execute(
        "INSERT INTO ZNOTEBODY VALUES(1,'<div>كلمة سر الحساب: 1234</div>')"
    )


def _make_chat_builder(rows):
    """Generic builder: a 'messages' table the social collector detects."""
    def _build(con):
        con.execute(
            "CREATE TABLE messages(pk INTEGER PRIMARY KEY, text, timestamp, "
            "sender)"
        )
        for i, (text, sender) in enumerate(rows, start=1):
            con.execute("INSERT INTO messages VALUES(?,?,?,?)",
                        (i, text, 1685620800 + i * 60, sender))
    return _build


def _write_skyline(path: Path) -> None:
    """Draw a simple city-skyline image for the Instagram featured post."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw
        import random

        w, h = 320, 200
        img = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(img)
        # sky gradient (dusk)
        for y in range(h):
            t = y / h
            draw.line([(0, y), (w, y)],
                      fill=(int(20 + 40 * t), int(24 + 30 * t),
                            int(60 + 50 * t)))
        random.seed(7)
        x = 0
        while x < w:
            bw = random.randint(18, 36)
            bh = random.randint(60, 150)
            draw.rectangle([x, h - bh, x + bw, h],
                           fill=(12, 18, 30))
            for wy in range(h - bh + 6, h - 6, 12):
                for wx in range(x + 4, x + bw - 4, 8):
                    if random.random() > 0.4:
                        draw.rectangle([wx, wy, wx + 3, wy + 5],
                                       fill=(255, 214, 120))
            x += bw + random.randint(2, 8)
        img.save(path)
    except Exception:
        _write_sample_image(path)


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

    # Create real media files so the chat viewer can display them inline.
    media = root / "media" / "wa_photo.png"
    _write_sample_image(media)
    ig_media = root / "media" / "ig_story.png"
    _write_skyline(ig_media)

    files = [
        ("HomeDomain", "Library/AddressBook/AddressBook.sqlitedb",
         _sqlite_bytes(_build_addressbook)),
        ("HomeDomain", "Library/SMS/sms.db", _sqlite_bytes(_build_sms)),
        ("HomeDomain", "Library/CallHistoryDB/CallHistory.storedata",
         _sqlite_bytes(_build_calls)),
        ("HomeDomain", "Library/Calendar/Calendar.sqlitedb",
         _sqlite_bytes(_build_calendar)),
        ("HomeDomain", "Library/Notes/notes.sqlite",
         _sqlite_bytes(_build_notes)),
        ("AppDomain-com.google.chrome.ios",
         "Library/Application Support/Google/Chrome/Default/History",
         _sqlite_bytes(_build_chrome)),
        ("AppDomainGroup-group.com.apple.safari", "Library/Safari/Bookmarks.db",
         _sqlite_bytes(_build_bookmarks)),
        ("AppDomainGroup-group.net.whatsapp.WhatsApp.shared",
         "ChatStorage.sqlite",
         _sqlite_bytes(_make_whatsapp_builder(str(media.resolve())))),
        ("AppDomain-com.burbn.instagram", "Documents/direct.db",
         _sqlite_bytes(_make_instagram_builder(str(ig_media.resolve())))),
        ("AppDomain-org.telegram.Telegraph", "telegram.sqlite",
         _sqlite_bytes(_make_chat_builder([
             ("هلا بك", "تليجرام"), ("تم الإرسال", "me")]))),
        ("AppDomain-com.toyopagroup.picaboo", "snap.db",
         _sqlite_bytes(_make_chat_builder([
             ("👻 سناب", "snap_user"), ("شفت الستوري؟", "noor")]))),
        ("AppDomain-com.zhiliaoapp.musically", "tiktok.db",
         _sqlite_bytes(_make_chat_builder([
             ("شوف الفيديو", "tiktok_fan")]))),
        ("AppDomain-com.hammerandchisel.discord", "discord.db",
         _sqlite_bytes(_make_chat_builder([
             ("gg", "gamer"), ("join the call", "me")]))),
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
                "Installed Applications": [
                    "net.whatsapp.WhatsApp", "com.burbn.instagram",
                    "com.toyopagroup.picaboo", "org.telegram.messenger",
                    "com.zhiliaoapp.musically", "com.hammerandchisel.discord",
                    "com.apple.mobilesafari", "com.google.chrome.ios",
                ],
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
