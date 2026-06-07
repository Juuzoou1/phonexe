"""Main application window for the phonexe desktop GUI."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import __version__, analyze
from ..reporting import report as reporting
from . import theme
from .datasource import (
    device_fields,
    device_summary,
    overview_stats,
    section_table,
)
from .i18n import Lang, tr
from .widgets import Donut, StatCard, hline

# (section key, glyph) for the left sidebar.
_SECTIONS = [
    ("sec_overview", "⌂"),
    ("sec_apps", "▦"),
    ("sec_messages", "✉"),
    ("sec_media", "▣"),
    ("sec_location", "◎"),
    ("sec_calls", "☎"),
    ("sec_contacts", "☰"),
    ("sec_browser", "◐"),
    ("sec_accounts", "⚿"),
    ("sec_deleted", "✗"),
]

_NAV = ["nav_dashboard", "nav_extract", "nav_analyze", "nav_reports", "nav_tools"]


class AnalyzeWorker(QThread):
    progress = pyqtSignal(str)
    done = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, path: str):
        super().__init__()
        self._path = path

    def run(self):
        try:
            report = analyze.analyze(self._path, progress=self.progress.emit)
            self.done.emit(report)
        except Exception as e:  # surfaced to the user
            self.failed.emit(str(e))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.report: dict | None = None
        self.current_section = "sec_overview"
        self._worker: AnalyzeWorker | None = None

        self.setWindowTitle("phonexe")
        self.resize(1360, 860)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        body = QHBoxLayout()
        body.setContentsMargins(14, 14, 14, 14)
        body.setSpacing(14)
        body.addWidget(self._build_sidebar(), 0)
        body.addWidget(self._build_center(), 1)
        body.addWidget(self._build_right(), 0)
        body_w = QWidget()
        body_w.setLayout(body)
        root.addWidget(body_w, 1)

        self._start_clock()
        self.retranslate()
        self.select_section("sec_overview")
        self.refresh_views()

    # ------------------------------------------------------------ top bar
    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topbar")
        bar.setFixedHeight(64)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(16)

        logo = QLabel("\U0001F6E1")
        logo.setStyleSheet(f"font-size: 26px; color: {theme.ACCENT};")
        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("appTitle")
        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setObjectName("appSubtitle")
        titles.addWidget(self.title_lbl)
        titles.addWidget(self.subtitle_lbl)
        lay.addWidget(logo)
        lay.addLayout(titles)
        lay.addSpacing(20)

        # nav buttons
        self.nav_btns: dict[str, QPushButton] = {}
        for key in _NAV:
            b = QPushButton()
            b.setObjectName("navBtn")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, k=key: self.on_nav(k))
            self.nav_btns[key] = b
            lay.addWidget(b)
        self.nav_btns["nav_dashboard"].setChecked(True)

        lay.addStretch(1)

        clock_box = QVBoxLayout()
        clock_box.setSpacing(0)
        self.clock_lbl = QLabel()
        self.clock_lbl.setObjectName("clock")
        self.clock_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.date_lbl = QLabel()
        self.date_lbl.setObjectName("clockDate")
        self.date_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        clock_box.addWidget(self.clock_lbl)
        clock_box.addWidget(self.date_lbl)
        lay.addLayout(clock_box)

        self.lang_btn = QPushButton()
        self.lang_btn.setObjectName("ghost")
        self.lang_btn.clicked.connect(self.toggle_language)
        lay.addWidget(self.lang_btn)
        return bar

    # ------------------------------------------------------------ sidebar
    def _build_sidebar(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(258)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        self.connected_lbl = QLabel()
        self.connected_lbl.setObjectName("sectionHeader")
        lay.addWidget(self.connected_lbl)

        # device card
        self.device_card = QFrame()
        self.device_card.setObjectName("deviceCard")
        dc = QVBoxLayout(self.device_card)
        dc.setContentsMargins(12, 12, 12, 12)
        dc.setSpacing(2)
        self.dev_name_lbl = QLabel()
        self.dev_name_lbl.setObjectName("deviceName")
        self.dev_os_lbl = QLabel()
        self.dev_os_lbl.setObjectName("deviceMeta")
        self.dev_id_lbl = QLabel()
        self.dev_id_lbl.setObjectName("deviceMeta")
        self.dev_id_lbl.setWordWrap(True)
        self.dev_status_lbl = QLabel()
        self.dev_status_lbl.setObjectName("statusOk")
        dc.addWidget(self.dev_name_lbl)
        dc.addWidget(self.dev_os_lbl)
        dc.addWidget(self.dev_id_lbl)
        dc.addWidget(self.dev_status_lbl)
        lay.addWidget(self.device_card)

        # open buttons
        self.open_ios_btn = QPushButton()
        self.open_ios_btn.setObjectName("primary")
        self.open_ios_btn.clicked.connect(lambda: self.open_dir("ios"))
        self.open_android_btn = QPushButton()
        self.open_android_btn.setObjectName("ghost")
        self.open_android_btn.clicked.connect(lambda: self.open_dir("android"))
        self.open_report_btn = QPushButton()
        self.open_report_btn.setObjectName("ghost")
        self.open_report_btn.clicked.connect(self.open_report_file)
        lay.addWidget(self.open_ios_btn)
        lay.addWidget(self.open_android_btn)
        lay.addWidget(self.open_report_btn)

        lay.addWidget(hline())
        self.sections_lbl = QLabel()
        self.sections_lbl.setObjectName("sectionHeader")
        lay.addWidget(self.sections_lbl)

        self.section_btns: dict[str, QPushButton] = {}
        for key, glyph in _SECTIONS:
            b = QPushButton()
            b.setObjectName("sectionBtn")
            b.setCheckable(True)
            b.setProperty("glyph", glyph)
            b.clicked.connect(lambda _=False, k=key: self.select_section(k))
            self.section_btns[key] = b
            lay.addWidget(b)

        lay.addStretch(1)
        self.end_btn = QPushButton()
        self.end_btn.setObjectName("danger")
        self.end_btn.clicked.connect(self.end_examination)
        lay.addWidget(self.end_btn)
        return panel

    # ------------------------------------------------------------ center
    def _build_center(self) -> QWidget:
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        # stats header
        stats_panel = QFrame()
        stats_panel.setObjectName("panel")
        sp = QVBoxLayout(stats_panel)
        sp.setContentsMargins(16, 14, 16, 16)
        head = QHBoxLayout()
        self.stats_title_lbl = QLabel()
        self.stats_title_lbl.setObjectName("panelTitle")
        self.refresh_btn = QPushButton()
        self.refresh_btn.setObjectName("ghost")
        self.refresh_btn.clicked.connect(self.refresh_views)
        head.addWidget(self.stats_title_lbl)
        head.addStretch(1)
        head.addWidget(self.refresh_btn)
        sp.addLayout(head)

        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(12)
        self.stat_cards: list[StatCard] = []
        for i in range(6):
            card = StatCard("0", "", theme.STAT_COLORS[i])
            self.stat_cards.append(card)
            self.stats_grid.addWidget(card, 0, i)
        sp.addLayout(self.stats_grid)
        lay.addWidget(stats_panel)

        # content panel (section title + search + table)
        content = QFrame()
        content.setObjectName("panel")
        cp = QVBoxLayout(content)
        cp.setContentsMargins(16, 14, 16, 16)
        chead = QHBoxLayout()
        self.section_title_lbl = QLabel()
        self.section_title_lbl.setObjectName("panelTitle")
        self.search_box = QLineEdit()
        self.search_box.setFixedWidth(240)
        self.search_box.textChanged.connect(self._apply_filter)
        chead.addWidget(self.section_title_lbl)
        chead.addStretch(1)
        chead.addWidget(self.search_box)
        cp.addLayout(chead)

        self.note_lbl = QLabel()
        self.note_lbl.setObjectName("noteLabel")
        self.note_lbl.setWordWrap(True)
        cp.addWidget(self.note_lbl)

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        cp.addWidget(self.table, 1)
        lay.addWidget(content, 1)
        return wrap

    # ------------------------------------------------------------ right
    def _build_right(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(300)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(12)

        self.devinfo_title = QLabel()
        self.devinfo_title.setObjectName("panelTitle")
        outer.addWidget(self.devinfo_title)
        self.devinfo_box = QVBoxLayout()
        self.devinfo_box.setSpacing(6)
        outer.addLayout(self.devinfo_box)

        outer.addWidget(hline())
        self.extract_title = QLabel()
        self.extract_title.setObjectName("panelTitle")
        outer.addWidget(self.extract_title)
        self.donut = Donut(0, "")
        outer.addWidget(self.donut, 0, Qt.AlignmentFlag.AlignHCenter)
        self.extract_state_lbl = QLabel()
        self.extract_state_lbl.setObjectName("noteLabel")
        self.extract_state_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        outer.addWidget(self.extract_state_lbl)

        outer.addWidget(hline())
        self.events_title = QLabel()
        self.events_title.setObjectName("panelTitle")
        outer.addWidget(self.events_title)
        self.events_scroll = QScrollArea()
        self.events_scroll.setWidgetResizable(True)
        self.events_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.events_scroll.setStyleSheet("background: transparent; border: none;")
        self.events_scroll.viewport().setStyleSheet(
            f"background: {theme.PANEL};"
        )
        self.events_inner = QWidget()
        self.events_inner.setStyleSheet(f"background: {theme.PANEL};")
        self.events_layout = QVBoxLayout(self.events_inner)
        self.events_layout.setContentsMargins(0, 0, 0, 0)
        self.events_layout.setSpacing(4)
        self.events_layout.addStretch(1)
        self.events_scroll.setWidget(self.events_inner)
        outer.addWidget(self.events_scroll, 1)
        return panel

    # ------------------------------------------------------------ clock
    def _start_clock(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

    def _tick(self):
        now = datetime.now()
        self.clock_lbl.setText(now.strftime("%H:%M:%S"))
        self.date_lbl.setText(now.strftime("%Y-%m-%d"))

    # ------------------------------------------------------------ i18n
    def retranslate(self):
        rtl = Lang.is_rtl()
        QApplication.instance().setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if rtl
            else Qt.LayoutDirection.LeftToRight
        )
        self.title_lbl.setText(tr("app_title"))
        self.subtitle_lbl.setText(f"{tr('app_subtitle')}   v{__version__}")
        for key, btn in self.nav_btns.items():
            btn.setText(tr(key))
        self.lang_btn.setText(tr("language"))
        self.connected_lbl.setText(tr("connected_device"))
        self.dev_status_lbl.setText("● " + tr("connected"))
        self.open_ios_btn.setText(tr("open_ios"))
        self.open_android_btn.setText(tr("open_android"))
        self.open_report_btn.setText(tr("open_report"))
        self.sections_lbl.setText(tr("main_sections"))
        for key, btn in self.section_btns.items():
            glyph = btn.property("glyph")
            btn.setText(f"  {glyph}   {tr(key)}")
        self.end_btn.setText(tr("end_exam"))
        self.stats_title_lbl.setText(tr("stats_title"))
        self.refresh_btn.setText(tr("refresh"))
        self.search_box.setPlaceholderText(tr("search"))
        self.devinfo_title.setText(tr("device_info"))
        self.extract_title.setText(tr("extraction_status"))
        self.events_title.setText(tr("recent_events"))
        self.section_title_lbl.setText(tr(self.current_section))
        self.refresh_views()

    def toggle_language(self):
        Lang.toggle()
        self.retranslate()

    # ------------------------------------------------------------ nav
    def on_nav(self, key: str):
        for k, b in self.nav_btns.items():
            b.setChecked(k == key)
        if key == "nav_reports":
            self.export_report()
            self.nav_btns["nav_dashboard"].setChecked(True)
            self.nav_btns["nav_reports"].setChecked(False)
        elif key == "nav_extract":
            self.open_dir("ios")
            self.nav_btns["nav_dashboard"].setChecked(True)
            self.nav_btns["nav_extract"].setChecked(False)
        elif key == "nav_tools":
            self.show_about()
            self.nav_btns["nav_dashboard"].setChecked(True)
            self.nav_btns["nav_tools"].setChecked(False)

    def select_section(self, key: str):
        self.current_section = key
        for k, b in self.section_btns.items():
            b.setChecked(k == key)
        self.section_title_lbl.setText(tr(key))
        self.refresh_views()

    # ------------------------------------------------------------ loading
    def open_dir(self, _platform_hint: str):
        path = QFileDialog.getExistingDirectory(self, tr("open_ios"))
        if path:
            self.load_path(path)

    def open_report_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("open_report"), "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            self.report = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            QMessageBox.critical(self, "phonexe", str(e))
            return
        self.add_event(tr("completed"))
        self.donut.set_percent(100)
        self.refresh_views()

    def load_path(self, path: str):
        self.add_event(tr("loading"))
        self.donut.set_percent(5)
        self._worker = AnalyzeWorker(path)
        self._worker.progress.connect(self._on_progress)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, name: str):
        self.add_event(name)
        cur = min(95, self.donut._percent + 12)
        self.donut.set_percent(cur)

    def _on_done(self, report: dict):
        self.report = report
        self.donut.set_percent(100)
        self.add_event(tr("completed"))
        self.refresh_views()

    def _on_failed(self, msg: str):
        self.donut.set_percent(0)
        QMessageBox.critical(self, "phonexe", msg)

    # ------------------------------------------------------------ events
    def add_event(self, text: str):
        lbl = QLabel(f"{datetime.now().strftime('%H:%M:%S')}  ·  {text}")
        lbl.setObjectName("noteLabel")
        lbl.setWordWrap(True)
        self.events_layout.insertWidget(0, lbl)

    # ------------------------------------------------------------ views
    def refresh_views(self):
        report = self.report or {"artifacts": {}, "device": {}, "meta": {}}

        # stats
        for card, (label_key, value) in zip(
            self.stat_cards, overview_stats(report)
        ):
            card.set_value(f"{value:,}", tr(label_key))

        # device card
        summ = device_summary(report)
        self.dev_name_lbl.setText(summ["name"] if self.report else tr("no_device"))
        self.dev_os_lbl.setText(summ["os"])
        self.dev_id_lbl.setText(summ["ident"])
        self.dev_status_lbl.setVisible(bool(self.report))

        # device info panel
        while self.devinfo_box.count():
            item = self.devinfo_box.takeAt(0)
            if item.widget():
                # remove synchronously so rebuilt rows never overlap stale ones
                item.widget().setParent(None)
        for key, val in device_fields(report):
            row = QHBoxLayout()
            k = QLabel(tr(key))
            k.setObjectName("noteLabel")
            v = QLabel(val)
            v.setWordWrap(True)
            row.addWidget(k)
            row.addStretch(1)
            row.addWidget(v)
            holder = QWidget()
            holder.setLayout(row)
            self.devinfo_box.addWidget(holder)

        # extraction state
        self.extract_state_lbl.setText(
            tr("completed") if self.report else tr("no_data")
        )

        self._populate_table()

    def _populate_table(self):
        report = self.report or {"artifacts": {}}
        if self.current_section == "sec_overview":
            cols, rows, note = section_table(report, "sec_messages")
        else:
            cols, rows, note = section_table(report, self.current_section)
        self.note_lbl.setText(note)
        self.note_lbl.setVisible(bool(note))

        self._all_rows = rows
        self.table.clear()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self._fill_rows(rows)

    def _fill_rows(self, rows: list[list[str]]):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(val))
        self.table.resizeColumnsToContents()

    def _apply_filter(self, text: str):
        text = text.strip().lower()
        if not hasattr(self, "_all_rows"):
            return
        if not text:
            self._fill_rows(self._all_rows)
            return
        filtered = [
            row for row in self._all_rows
            if any(text in str(cell).lower() for cell in row)
        ]
        self._fill_rows(filtered)

    # ------------------------------------------------------------ actions
    def export_report(self):
        if not self.report:
            QMessageBox.information(self, "phonexe", tr("no_data"))
            return
        out = QFileDialog.getExistingDirectory(self, tr("export_report"))
        if not out:
            return
        out_dir = Path(out)
        reporting.write_json(self.report, out_dir / "report.json")
        html_path = reporting.write_html(self.report, out_dir / "report.html")
        QMessageBox.information(self, "phonexe", str(html_path))

    def end_examination(self):
        self.report = None
        self.donut.set_percent(0)
        self.select_section("sec_overview")
        self.refresh_views()

    def show_about(self):
        QMessageBox.information(
            self, "phonexe",
            f"phonexe v{__version__}\n\n{tr('scope_note')}",
        )
