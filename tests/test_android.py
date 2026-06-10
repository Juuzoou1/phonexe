"""Tests for the Android extraction pipeline."""

from __future__ import annotations

import json

import pytest

from phonexe.android import calls, contacts, messages, social, whatsapp
from phonexe.android.adb import parse_content_rows
from phonexe.android.extraction import AndroidExtraction, ExtractionError
from phonexe.cli import main
from tests.make_sample_android import build


@pytest.fixture
def ext(tmp_path) -> AndroidExtraction:
    build(tmp_path / "android")
    return AndroidExtraction(tmp_path / "android")


def test_device_info(ext):
    assert ext.device.manufacturer == "Samsung"
    assert ext.device.model == "SM-G991B"
    assert ext.device.android_version == "13"


def test_contacts(ext):
    out = contacts.extract(ext)
    assert out["count"] == 1
    rec = out["records"][0]
    assert rec["name"] == "Khalid Noor"
    assert "+966500000002" in rec["phones"]
    assert "khalid@example.com" in rec["emails"]


def test_messages(ext):
    out = messages.extract(ext)
    assert out["count"] == 2
    assert out["records"][0]["text"] == "android sms hi"
    assert out["records"][0]["direction"] == "received"
    assert out["records"][1]["direction"] == "sent"


def test_calls(ext):
    out = calls.extract(ext)
    assert out["count"] == 1
    assert out["records"][0]["number"] == "+966500000002"
    assert out["records"][0]["type"] == "outgoing"


def test_whatsapp(ext):
    out = whatsapp.extract(ext)
    assert out["count"] == 1
    assert out["records"][0]["text"] == "wa android"


def test_social_detects_instagram(ext):
    out = social.extract(ext)
    assert "instagram" in out["apps"]


def test_social_detects_additional_apps(ext):
    # Viber is one of the newly-supported messengers; the sample ships a
    # Viber database so detection of the expanded app list is exercised.
    out = social.extract(ext)
    assert "viber" in out["apps"]
    assert out["apps"]["viber"]["name"] == "Viber"


def test_social_recovers_deleted_messages(ext):
    out = social.extract(ext)
    assert out["deleted_count"] >= 1
    fragments = [
        frag["text"]
        for db in out["apps"]["viber"]["databases"]
        for frag in db["deleted"]
    ]
    assert any("docks at midnight" in t for t in fragments)


def test_missing_directory():
    with pytest.raises(ExtractionError):
        AndroidExtraction("/no/such/path/here")


def test_parse_content_rows():
    sample = (
        "Row: 0 _id=1, address=+966500000002, body=hello, date=1685620800000\n"
        "Row: 1 _id=2, address=NULL, body=world, date=1685620860000\n"
    )
    rows = parse_content_rows(sample)
    assert len(rows) == 2
    assert rows[0]["address"] == "+966500000002"
    assert rows[0]["body"] == "hello"
    assert rows[1]["address"] is None


def test_parse_content_rows_comma_in_value():
    # An SMS body containing ", " must not be chopped into extra fields.
    sample = "Row: 0 _id=1, address=+1, body=hey, are you there, date=1685620800000\n"
    rows = parse_content_rows(sample)
    assert len(rows) == 1
    assert rows[0]["body"] == "hey, are you there"
    assert rows[0]["date"] == "1685620800000"
    assert rows[0]["address"] == "+1"


def test_fetch_adb_extracts_from_zip(tmp_path):
    import io
    import zipfile
    from phonexe.android import fetch_adb

    # Synthetic platform-tools zip (no network): the wanted Windows files plus
    # an unrelated file that must be ignored.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("platform-tools/adb.exe", b"MZ-fake-adb")
        zf.writestr("platform-tools/AdbWinApi.dll", b"dll1")
        zf.writestr("platform-tools/AdbWinUsbApi.dll", b"dll2")
        zf.writestr("platform-tools/NOTICE.txt", b"license")

    written = fetch_adb.extract_from_zip(buf.getvalue(), tmp_path, key="windows")
    names = {p.name for p in written}
    assert names == {"adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"}
    assert (tmp_path / "adb.exe").read_bytes() == b"MZ-fake-adb"
    assert not (tmp_path / "NOTICE.txt").exists()
    assert fetch_adb.is_present(tmp_path) is True

    # Linux variant keeps only the bare `adb` binary and marks it executable.
    buf2 = io.BytesIO()
    with zipfile.ZipFile(buf2, "w") as zf:
        zf.writestr("platform-tools/adb", b"\x7fELF-fake")
    written2 = fetch_adb.extract_from_zip(buf2.getvalue(), tmp_path / "lx",
                                          key="linux")
    assert {p.name for p in written2} == {"adb"}


def test_cli_end_to_end(tmp_path):
    build(tmp_path / "android")
    out_dir = tmp_path / "report"
    rc = main(["android", str(tmp_path / "android"), "-o", str(out_dir)])
    assert rc == 0
    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert report["meta"]["platform"] == "android"
    assert report["artifacts"]["messages"]["count"] == 2
    assert (out_dir / "report.html").exists()
