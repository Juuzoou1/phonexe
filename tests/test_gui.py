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
    assert stats["stat_contacts"] == 1
    # messages = SMS/iMessage (2) + WhatsApp (4) + Instagram social (2)
    assert stats["stat_messages"] == 8
    assert stats["stat_apps"] >= 1


def test_device_summary(ios_report):
    summ = device_summary(ios_report)
    assert summ["name"] == "Suspect iPhone"
    assert summ["os"].startswith("iOS")


def test_section_table_messages(ios_report):
    cols, rows, _ = section_table(ios_report, "sec_messages")
    assert "text" in cols and "source" in cols
    # merged stream: 2 SMS/iMessage + 4 WhatsApp + 2 Instagram = 8
    assert len(rows) == 8


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
