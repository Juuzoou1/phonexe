"""End-to-end tests for the phonexe extraction pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from phonexe.apps import social, whatsapp
from phonexe.backup import BackupError, IOSBackup
from phonexe.cli import main
from phonexe.extractors import calls, contacts, messages
from phonexe.timeutil import cocoa_to_iso, unix_to_iso
from tests.make_sample_backup import build


@pytest.fixture
def backup(tmp_path) -> IOSBackup:
    build(tmp_path / "backup")
    return IOSBackup(tmp_path / "backup")


def test_device_info(backup):
    assert backup.device.device_name == "Suspect iPhone"
    assert backup.device.product_version == "16.5"


def test_contacts(backup):
    out = contacts.extract(backup)
    assert out["count"] == 1
    rec = out["records"][0]
    assert rec["name"] == "Sara Ahmed"
    assert "+966500000001" in rec["phones"]
    assert "sara@example.com" in rec["emails"]


def test_messages(backup):
    out = messages.extract(backup)
    assert out["count"] == 2
    assert out["records"][0]["text"] == "Hello from the suspect"
    assert out["records"][0]["timestamp"] is not None


def test_calls(backup):
    out = calls.extract(backup)
    assert out["count"] == 1
    assert out["records"][0]["number"] == "+966500000001"
    assert out["records"][0]["direction"] == "outgoing"


def test_whatsapp(backup):
    out = whatsapp.extract(backup)
    assert out["count"] == 12
    assert out["records"][0]["partner"] == "Sara"
    # one message carries a shared location, another references media
    assert any("latitude" in r for r in out["records"])
    assert any("media" in r for r in out["records"])


def test_social_detects_instagram(backup):
    out = social.extract(backup)
    assert "instagram" in out["apps"]
    tables = out["apps"]["instagram"]["databases"][0]["tables"]
    assert any(t["table"] == "direct_messages" for t in tables)


def test_encrypted_backup_rejected(tmp_path):
    build(tmp_path / "backup")
    import plistlib

    (tmp_path / "backup" / "Manifest.plist").write_bytes(
        plistlib.dumps({"IsEncrypted": True})
    )
    with pytest.raises(BackupError, match="ENCRYPTED"):
        IOSBackup(tmp_path / "backup")


def test_timeutil():
    assert cocoa_to_iso(0) is None
    assert cocoa_to_iso(None) is None
    assert cocoa_to_iso(707400000).startswith("2023-")
    # nanosecond magnitude is auto-detected
    assert cocoa_to_iso(707400000 * 1_000_000_000).startswith("2023-")
    assert unix_to_iso(1685620800).startswith("2023-")


def test_cli_end_to_end(tmp_path):
    build(tmp_path / "backup")
    out_dir = tmp_path / "report"
    rc = main(["analyze", str(tmp_path / "backup"), "-o", str(out_dir)])
    assert rc == 0
    report = json.loads((out_dir / "report.json").read_text())
    assert report["device"]["device_name"] == "Suspect iPhone"
    assert report["artifacts"]["messages"]["count"] == 2
    assert (out_dir / "report.html").exists()


def test_ios_acquire_check():
    from phonexe import ios_acquire
    status = ios_acquire.check()
    assert set(status) >= {"libimobiledevice", "pymobiledevice3", "ready",
                           "backend"}
    assert isinstance(status["ready"], bool)
    # graceful when no device / backend present
    assert ios_acquire.list_devices() == [] or isinstance(
        ios_acquire.list_devices(), list)


def test_calendar_notes_files(backup):
    from phonexe.extractors import calendar, notes, files
    assert calendar.extract(backup)["count"] == 1
    assert notes.extract(backup)["count"] == 1
    assert "كلمة سر" in notes.extract(backup)["records"][0]["content"]
    assert files.extract(backup)["count"] > 0
