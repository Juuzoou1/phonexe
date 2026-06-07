"""Tests for the GUI data layer (and an optional headless Qt smoke test)."""

from __future__ import annotations

import os

import pytest

from phonexe.analyze import analyze, detect_platform
from phonexe.gui.datasource import (
    chat_apps,
    conversations,
    device_summary,
    location_markers,
    overview_stats,
    section_table,
    stories,
)
from tests.make_sample_android import build as build_android
from tests.make_sample_backup import build as build_ios


@pytest.fixture
def ios_report(tmp_path) -> dict:
    build_ios(tmp_path / "backup")
    return analyze(tmp_path / "backup")


def test_detect_platform(tmp_path):
    build_ios(tmp_path / "ios")
    build_android(tmp_path / "android")
    assert detect_platform(tmp_path / "ios") == "ios"
    assert detect_platform(tmp_path / "android") == "android"
    empty = tmp_path / "empty"
    empty.mkdir()
    assert detect_platform(empty) is None


def test_overview_stats(ios_report):
    stats = dict(overview_stats(ios_report))
    # six brief-defined cards
    assert {"stat_apps", "stat_messages", "stat_photos", "stat_videos",
            "stat_files", "stat_deleted"} == set(stats)
    # messages = SMS/iMessage (2) + WhatsApp (12) + social apps (10)
    assert stats["stat_messages"] == 24
    assert stats["stat_apps"] >= 1
    assert stats["stat_deleted"] >= 2


def test_device_summary(ios_report):
    summ = device_summary(ios_report)
    assert summ["name"] == "Suspect iPhone"
    assert summ["os"].startswith("iOS")


def test_section_table_messages(ios_report):
    cols, rows, _ = section_table(ios_report, "sec_messages")
    assert "text" in cols and "source" in cols
    # merged stream: 2 SMS/iMessage + 12 WhatsApp + 10 social = 24
    assert len(rows) == 24


def test_section_table_contacts(ios_report):
    cols, rows, _ = section_table(ios_report, "sec_contacts")
    assert len(rows) == 1
    assert any("Sara" in str(c) for c in rows[0])


def test_section_accounts_has_note(ios_report):
    _, _, note = section_table(ios_report, "sec_accounts")
    assert note  # accounts section carries an explanatory note


def test_chat_apps_and_conversations(ios_report):
    keys = {a["key"] for a in chat_apps(ios_report)}
    assert {"messages", "whatsapp", "instagram"} <= keys

    wa = conversations(ios_report, "whatsapp")
    assert wa and wa[0]["title"] == "Sara"
    msgs = wa[0]["messages"]
    assert len(msgs) == 4
    assert any(m["lat"] is not None for m in msgs)      # shared location
    assert any(m["image"] for m in msgs)                # media attachment


def test_location_markers(ios_report):
    markers = location_markers(ios_report)
    # WhatsApp (Riyadh) + Instagram (Jeddah) shared locations
    assert len(markers) >= 2
    assert all("lat" in m and "lon" in m for m in markers)


def test_deleted_recovery(ios_report):
    deleted = ios_report["artifacts"]["deleted"]
    assert deleted["count"] >= 2
    texts = " ".join(r["text"] for r in deleted["records"])
    assert "secret meeting" in texts
    cols, rows, note = section_table(ios_report, "sec_deleted")
    assert "text" in cols and len(rows) >= 2 and note


def test_timeline_sorted(ios_report):
    cols, rows, _ = section_table(ios_report, "sec_timeline")
    assert {"timestamp", "type", "source", "detail"} <= set(cols)
    times = [r[cols.index("timestamp")] for r in rows if r[cols.index("timestamp")]]
    assert times == sorted(times)
    types = {r[cols.index("type")] for r in rows}
    assert "Message" in types and "Call" in types


def test_stories(ios_report):
    items = stories(ios_report, "instagram")
    assert items and all("image" in s for s in items)


def test_instagram_thread_grouping():
    from phonexe.gui.datasource import _instagram_conversations
    recs = [
        {"thread_id": "A", "thread_title": "نورة", "text": "hi", "timestamp": 2},
        {"thread_id": "A", "thread_title": "نورة", "text": "hello", "timestamp": 1},
        {"thread_id": "B", "thread_title": "سارة", "text": "yo", "timestamp": 3,
         "image": "/x.png"},
    ]
    convos = _instagram_conversations(recs)
    assert len(convos) == 2  # two distinct threads
    a = next(c for c in convos if c["title"] == "نورة")
    # sorted by timestamp within the thread
    assert [m["text"] for m in a["messages"]] == ["hello", "hi"]
    b = next(c for c in convos if c["title"] == "سارة")
    assert b["messages"][0]["image"] == "/x.png"


def test_offline_map_asset_loads():
    pytest.importorskip("PyQt6.QtWidgets")
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PyQt6.QtWidgets import QApplication
        from phonexe.gui.mapview import OfflineMap
    except Exception:
        pytest.skip("Qt unavailable")
    _ = QApplication.instance() or QApplication([])
    m = OfflineMap()
    assert len(m._land) > 50  # bundled world polygons loaded


def test_qt_smoke(tmp_path):
    """Construct the main window headlessly if PyQt6 + offscreen are usable."""
    pytest.importorskip("PyQt6.QtWidgets")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PyQt6.QtWidgets import QApplication

        from phonexe.gui.mainwindow import MainWindow
    except Exception:
        pytest.skip("Qt platform libraries unavailable")

    app = QApplication.instance() or QApplication([])
    build_ios(tmp_path / "backup")
    win = MainWindow()
    win.report = analyze(tmp_path / "backup")
    win.refresh_views()
    assert win.table.rowCount() >= 0
    win.select_section("sec_contacts")
    assert win.table.rowCount() == 1
    app.processEvents()


def test_global_search(ios_report):
    from phonexe.gui.datasource import global_search
    hits = global_search(ios_report, "Sara")
    assert hits and all("section" in h and "match" in h for h in hits)
    assert global_search(ios_report, "") == []


def test_new_sections(ios_report):
    for sec in ("sec_calendar", "sec_notes", "sec_files"):
        cols, rows, _ = section_table(ios_report, sec)
        assert cols  # has columns


def test_link_analysis(ios_report):
    from phonexe.gui.datasource import link_analysis
    rows = link_analysis(ios_report)
    assert rows and rows[0]["interactions"] >= rows[-1]["interactions"]
    assert {"counterpart", "app", "interactions"} <= set(rows[0])


def test_unified_contacts(ios_report):
    from phonexe.gui.datasource import unified_contacts
    ids = unified_contacts(ios_report)
    # "Sara" chat folds into contact "Sara Ahmed"
    sara = next((i for i in ids if "Sara" in i["identity"]), None)
    assert sara and "Contacts" in sara["apps"] and "WhatsApp" in sara["apps"]


def test_audit_log():
    from phonexe.audit import AuditLog
    a = AuditLog("examiner1")
    a.record("test_action", "detail")
    rows = a.as_rows()
    assert rows[0]["action"] == "examination_started"
    assert any(r["action"] == "test_action" for r in rows)
    assert all("timestamp" in r for r in rows)


def test_multi_device(tmp_path):
    pytest.importorskip("PyQt6.QtWidgets")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PyQt6.QtWidgets import QApplication
        from phonexe.gui.mainwindow import MainWindow
    except Exception:
        pytest.skip("Qt unavailable")
    app = QApplication.instance() or QApplication([])
    build_ios(tmp_path / "b1")
    build_ios(tmp_path / "b2")
    win = MainWindow()
    win._add_device(analyze(tmp_path / "b1"))
    win._add_device(analyze(tmp_path / "b2"))
    assert len(win.devices) == 2
    assert win.device_combo.count() == 2
    win._switch_device(0)
    assert win.report is win.devices[0]["report"]
    app.processEvents()
