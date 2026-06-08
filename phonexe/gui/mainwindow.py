"""Main application window for the phonexe desktop GUI."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
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
from ..audit import AuditLog
from ..reporting import report as reporting
from . import theme
from .chatview import ChatMessage, ChatView, Conversation, theme_for
from .datasource import (
    chat_apps,
    conversations,
    device_fields,
    device_summary,
    location_markers,
    overview_stats,
    section_table,
    stories,
)
from .fluent import (
    ComboBox,
    FluentIcon,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    SearchLineEdit,
    TableWidget,
    notify,
)
from .i18n import Lang, tr
from .mapview import MapMarker, OfflineMap
from .widgets import Donut, PhoneOutline, StatCard, apply_glow, hline

# (section key, Lucide icon name) for the left sidebar.
_SECTIONS = [
    ("sec_overview", "layout-dashboard"),
    ("sec_apps", "layout-grid"),
    ("sec_installed", "layout-grid"),
    ("sec_messages", "message-circle"),
    ("sec_media", "image"),
    ("sec_location", "map-pin"),
    ("sec_calls", "phone"),
    ("sec_contacts", "users"),
    ("sec_browser", "globe"),
    ("sec_calendar", "calendar"),
    ("sec_notes", "file-text"),
    ("sec_files", "file"),
    ("sec_timeline", "clock"),
    ("sec_links", "share-2"),
    ("sec_identities", "contact-round"),
    ("sec_accounts", "key-round"),
    ("sec_deleted", "trash-2"),
    ("sec_bookmarks", "bookmark"),
    ("sec_audit", "history"),
]

_NAV = ["nav_dashboard", "nav_extract", "nav_analyze", "nav_reports", "nav_tools"]
_NAV_ICON = {
    "nav_dashboard": "layout-dashboard", "nav_extract": "download",
    "nav_analyze": "search", "nav_reports": "file-text", "nav_tools": "settings",
}


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


class AcquireWorker(QThread):
    """Pull a backup straight from a connected iPhone, then analyze it."""
    progress = pyqtSignal(str)
    done = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, serial: str):
        super().__init__()
        self._serial = serial

    def run(self):
        try:
            import tempfile
            from .. import ios_acquire
            dest = tempfile.mkdtemp(prefix="phonexe_acq_")
            self.progress.emit("acquiring backup…")
            backup_dir = ios_acquire.acquire(dest, self._serial,
                                             progress=self.progress.emit)
            report = analyze.analyze(str(backup_dir),
                                     progress=self.progress.emit)
            self.done.emit(report)
        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QWidget):
    def __init__(self, examiner: str | None = None, case_id: str | None = None,
                 organization: str | None = None):
        super().__init__()
        self.setObjectName("root")
        self.report: dict | None = None
        self.examiner = examiner
        self.case_id = case_id
        self.organization = organization
        self.current_section = "sec_overview"
        self._chat_return = "sec_apps"
        self._chat_size_mode = "full"
        self.bookmarks: list[dict] = []
        self._current_cols: list[str] = []
        self._search_results: list[dict] = []
        self.audit = AuditLog(examiner)
        if case_id:
            self.audit.record("case_opened", case_id)
        self.devices: list[dict] = []   # multi-device case: {label, report}
        self._switching = False
        self._worker: AnalyzeWorker | None = None
        self._acq_worker = None

        self.setWindowTitle("phonexe")
        self.resize(1360, 860)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_topbar())

        body = QHBoxLayout()
        body.setContentsMargins(14, 14, 14, 14)
        body.setSpacing(14)
        # Order matches the reference: device-info column on one side, the
        # section-navigation sidebar on the other (in RTL the first-added
        # widget renders right-most, so info goes right, nav goes left).
        body.addWidget(self._build_right(), 0)
        body.addWidget(self._build_center(), 1)
        body.addWidget(self._build_sidebar(), 0)
        body_w = QWidget()
        body_w.setLayout(body)
        root.addWidget(body_w, 1)

        self._start_clock()
        self.retranslate()
        self.select_section("sec_overview")
        self.refresh_views()

    # ------------------------------------------------------------ background
    def paintEvent(self, _e):  # noqa: N802
        """Dark base with soft ambient cyan/blue glows behind the panels."""
        from PyQt6.QtGui import QColor, QPainter, QRadialGradient

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(theme.BG))

        def glow(cx, cy, radius, hex_color, alpha):
            g = QRadialGradient(cx, cy, radius)
            c = QColor(hex_color)
            c.setAlpha(alpha)
            g.setColorAt(0.0, c)
            c2 = QColor(hex_color)
            c2.setAlpha(0)
            g.setColorAt(1.0, c2)
            p.fillRect(self.rect(), g)

        # cyan aura top-right, blue aura bottom-left, faint center lift
        glow(w * 0.82, h * 0.04, w * 0.55, theme.ACCENT, 46)
        glow(w * 0.10, h * 0.96, w * 0.55, theme.ACCENT2, 38)
        glow(w * 0.5, h * 0.45, w * 0.6, theme.ACCENT, 12)
        p.end()

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

        # global search across all sections
        self.global_search_box = SearchLineEdit()
        self.global_search_box.setFixedWidth(240)
        self.global_search_box.returnPressed.connect(self._run_global_search)
        lay.addWidget(self.global_search_box)

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

        # multi-device selector (visible once >1 device is loaded)
        self.device_combo = ComboBox()
        self.device_combo.setStyleSheet(
            f"QComboBox{{background:{theme.CARD};color:{theme.TEXT};"
            f"border:1px solid {theme.BORDER};border-radius:8px;padding:6px;}}")
        self.device_combo.currentIndexChanged.connect(self._switch_device)
        self.device_combo.hide()
        lay.addWidget(self.device_combo)

        # device card: phone outline mockup + details
        self.device_card = QFrame()
        self.device_card.setObjectName("deviceCard")
        dc = QHBoxLayout(self.device_card)
        dc.setContentsMargins(12, 12, 12, 12)
        dc.setSpacing(12)
        self.phone_outline = PhoneOutline()
        dc.addWidget(self.phone_outline, 0, Qt.AlignmentFlag.AlignTop)

        details = QVBoxLayout()
        details.setSpacing(2)
        self.dev_name_lbl = QLabel()
        self.dev_name_lbl.setObjectName("deviceName")
        self.dev_os_lbl = QLabel()
        self.dev_os_lbl.setObjectName("deviceMeta")
        self.dev_storage_lbl = QLabel()
        self.dev_storage_lbl.setObjectName("deviceMeta")
        self.dev_id_lbl = QLabel()
        self.dev_id_lbl.setObjectName("deviceMeta")
        self.dev_id_lbl.setWordWrap(True)
        self.dev_status_lbl = QLabel()
        self.dev_status_lbl.setObjectName("statusOk")
        details.addWidget(self.dev_name_lbl)
        details.addWidget(self.dev_os_lbl)
        details.addWidget(self.dev_storage_lbl)
        details.addWidget(self.dev_id_lbl)
        details.addWidget(self.dev_status_lbl)
        details.addStretch(1)
        dc.addLayout(details, 1)
        lay.addWidget(self.device_card)

        # device info button
        self.device_info_btn = PushButton()
        self.device_info_btn.setObjectName("ghost")
        self.device_info_btn.clicked.connect(self._show_device_info)
        lay.addWidget(self.device_info_btn)

        # open buttons
        self.open_ios_btn = PrimaryPushButton()
        self.open_ios_btn.setObjectName("primary")
        self.open_ios_btn.clicked.connect(lambda: self.open_dir("ios"))
        self.open_android_btn = PushButton()
        self.open_android_btn.setObjectName("ghost")
        self.open_android_btn.clicked.connect(lambda: self.open_dir("android"))
        self.open_report_btn = PushButton()
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
        self.section_icons: dict[str, str] = {}
        for key, icon_name in _SECTIONS:
            b = QPushButton()
            b.setObjectName("sectionBtn")
            b.setCheckable(True)
            b.setIconSize(QSize(18, 18))
            self.section_icons[key] = icon_name
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
            apply_glow(card, blur=20, alpha=30)
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
        self.search_box = SearchLineEdit()
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

        # content stack: table / offline map / apps grid
        self.content_stack = QStackedWidget()

        self.table = TableWidget()
        if hasattr(self.table, "setBorderRadius"):
            self.table.setBorderRadius(8)
            self.table.setBorderVisible(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellDoubleClicked.connect(self._bookmark_row)
        self.content_stack.addWidget(self.table)          # index 0

        self.map_view = OfflineMap()
        self.content_stack.addWidget(self.map_view)        # index 1

        self.apps_scroll = QScrollArea()
        self.apps_scroll.setWidgetResizable(True)
        self.apps_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.apps_scroll.setStyleSheet("background: transparent; border: none;")
        self.apps_scroll.viewport().setStyleSheet(f"background: {theme.PANEL};")
        self.apps_inner = QWidget()
        self.apps_inner.setStyleSheet(f"background: {theme.PANEL};")
        self.apps_grid = QGridLayout(self.apps_inner)
        self.apps_grid.setContentsMargins(4, 4, 4, 4)
        self.apps_grid.setSpacing(12)
        self.apps_scroll.setWidget(self.apps_inner)
        self.content_stack.addWidget(self.apps_scroll)     # index 2

        self.dash_holder = QWidget()
        self.dash_layout = QVBoxLayout(self.dash_holder)
        self.dash_layout.setContentsMargins(0, 0, 0, 0)
        self.content_stack.addWidget(self.dash_holder)     # index 3

        # inline app-clone page (opens "beside" the grid like the real app)
        self.chat_holder = QWidget()
        chat_v = QVBoxLayout(self.chat_holder)
        chat_v.setContentsMargins(0, 0, 0, 0)
        chat_v.setSpacing(8)
        back_bar = QHBoxLayout()
        self.chat_back_btn = QPushButton("‹  رجوع للتطبيقات")
        self.chat_back_btn.setObjectName("ghost")
        self.chat_back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chat_back_btn.clicked.connect(self._close_app_chat)
        back_bar.addWidget(self.chat_back_btn)
        back_bar.addStretch(1)
        self.size_phone_btn = QPushButton("📱  جوال")
        self.size_full_btn = QPushButton("🖥  كمبيوتر")
        for b, mode in ((self.size_phone_btn, "phone"),
                        (self.size_full_btn, "full")):
            b.setObjectName("ghost")
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, m=mode: self._set_chat_size(m))
            back_bar.addWidget(b)
        self.size_full_btn.setChecked(True)
        chat_v.addLayout(back_bar)
        self.chat_container = QVBoxLayout()
        self.chat_container.setContentsMargins(0, 0, 0, 0)
        cc = QWidget()
        cc.setLayout(self.chat_container)
        chat_v.addWidget(cc, 1)
        self.content_stack.addWidget(self.chat_holder)     # index 4

        # top-nav pages (reports / tools / extraction)
        self.nav_holder = QScrollArea()
        self.nav_holder.setWidgetResizable(True)
        self.nav_holder.setFrameShape(QFrame.Shape.NoFrame)
        self.nav_holder.setStyleSheet("background:transparent;border:none;")
        self.nav_inner = QWidget()
        self.nav_page_layout = QVBoxLayout(self.nav_inner)
        self.nav_page_layout.setContentsMargins(4, 4, 4, 4)
        self.nav_page_layout.setSpacing(12)
        self.nav_holder.setWidget(self.nav_inner)
        self.content_stack.addWidget(self.nav_holder)      # index 5

        cp.addWidget(self.content_stack, 1)
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
        from .svgicons import nav_icon
        for key, btn in self.nav_btns.items():
            btn.setText("  " + tr(key))
            btn.setIcon(QIcon(nav_icon(_NAV_ICON[key], 18)))
            btn.setIconSize(QSize(18, 18))
        self.lang_btn.setText(tr("language"))
        self.connected_lbl.setText(tr("connected_device"))
        self.dev_status_lbl.setText("● " + tr("connected"))
        self.device_info_btn.setText(tr("device_info"))
        self.open_ios_btn.setText(tr("open_ios"))
        self.open_android_btn.setText(tr("open_android"))
        self.open_report_btn.setText(tr("open_report"))
        if FluentIcon is not None:
            try:
                self.open_ios_btn.setIcon(FluentIcon.PHONE)
                self.open_android_btn.setIcon(FluentIcon.PHONE)
                self.open_report_btn.setIcon(FluentIcon.DOCUMENT)
                self.device_info_btn.setIcon(FluentIcon.INFO)
            except Exception:
                pass
        self.sections_lbl.setText(tr("main_sections"))
        for key, btn in self.section_btns.items():
            btn.setText("   " + tr(key))
        self._refresh_section_icons()
        self.end_btn.setText(tr("end_exam"))
        self.stats_title_lbl.setText(tr("stats_title"))
        self.refresh_btn.setText(tr("refresh"))
        self.search_box.setPlaceholderText(tr("search"))
        self.global_search_box.setPlaceholderText(tr("global_search"))
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
        if key in ("nav_dashboard", "nav_analyze"):
            self.select_section("sec_overview")
            return
        # build the corresponding top-nav page
        while self.nav_page_layout.count():
            item = self.nav_page_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        if key == "nav_reports":
            self._build_reports_page()
        elif key == "nav_extract":
            self._build_extraction_page()
        elif key == "nav_tools":
            self._build_tools_page()
        self.section_title_lbl.setVisible(False)
        self.search_box.setVisible(False)
        self.note_lbl.setVisible(False)
        self.content_stack.setCurrentIndex(5)

    def _nav_panel(self, title: str) -> QVBoxLayout:
        panel = QFrame()
        panel.setObjectName("panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(18, 16, 18, 18)
        lay.setSpacing(12)
        h = QLabel(title)
        h.setObjectName("panelTitle")
        lay.addWidget(h)
        self.nav_page_layout.addWidget(panel)
        return lay

    def _big_btn(self, text: str, slot, primary=True) -> QPushButton:
        b = (PrimaryPushButton(text) if primary else PushButton(text))
        b.setMinimumHeight(40)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.clicked.connect(slot)
        return b

    def _build_reports_page(self):
        lay = self._nav_panel(tr("reports_title"))
        lay.addWidget(self._big_btn(tr("export_pdf"),
                                    lambda: self.export_report("pdf")))
        lay.addWidget(self._big_btn(tr("export_html"),
                                    lambda: self.export_report("html"), False))
        lay.addWidget(self._big_btn(tr("export_json"),
                                    lambda: self.export_report("json"), False))
        note = QLabel(tr("scope_note"))
        note.setObjectName("noteLabel")
        note.setWordWrap(True)
        lay.addWidget(note)
        self.nav_page_layout.addStretch(1)

    def _build_extraction_page(self):
        lay = self._nav_panel(tr("extract_title"))
        lay.addWidget(self._big_btn(tr("open_ios"),
                                    lambda: self.open_dir("ios")))
        lay.addWidget(self._big_btn(tr("open_android"),
                                    lambda: self.open_dir("android"), False))
        lay.addWidget(self._big_btn(tr("open_report"),
                                    self.open_report_file, False))
        note = QLabel(tr("scope_note"))
        note.setObjectName("noteLabel")
        note.setWordWrap(True)
        lay.addWidget(note)
        self.nav_page_layout.addStretch(1)

    def _build_tools_page(self):
        lay = self._nav_panel(tr("tools_title"))
        lay.addWidget(self._big_btn(tr("save_case"), self.save_case))
        lay.addWidget(self._big_btn(tr("language"), self.toggle_language, False))
        about = QLabel(f"phonexe v{__version__}\n\n{tr('scope_note')}")
        about.setObjectName("noteLabel")
        about.setWordWrap(True)
        lay.addWidget(about)
        self.nav_page_layout.addStretch(1)

    def _refresh_section_icons(self):
        from .svgicons import nav_icon
        for key, btn in self.section_btns.items():
            color = theme.ACCENT if key == self.current_section else "#BFD5E6"
            btn.setIcon(QIcon(nav_icon(self.section_icons[key], 18, color)))

    def select_section(self, key: str):
        self.current_section = key
        for k, b in self.section_btns.items():
            b.setChecked(k == key)
        self._refresh_section_icons()
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
            report = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            QMessageBox.critical(self, "phonexe", str(e))
            return
        self.add_event(tr("completed"))
        self.donut.set_percent(100)
        self._add_device(report)

    def load_path(self, path: str):
        self.add_event(tr("loading"))
        self.donut.set_percent(5)
        self._worker = AnalyzeWorker(path)
        self._worker.progress.connect(self._on_progress)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def start_source(self, source: tuple[str, str] | None):
        """Begin the examination from the wizard's chosen source."""
        if not source:
            return
        kind, value = source
        if kind == "path":
            self.load_path(value)
        elif kind == "acquire":
            self.add_event(tr("loading"))
            self.donut.set_percent(5)
            self.audit.record("acquisition_started", value)
            self._acq_worker = AcquireWorker(value)
            self._acq_worker.progress.connect(self._on_progress)
            self._acq_worker.done.connect(self._on_done)
            self._acq_worker.failed.connect(self._on_failed)
            self._acq_worker.start()

    def _on_progress(self, name: str):
        self.add_event(name)
        cur = min(95, self.donut._percent + 12)
        self.donut.set_percent(cur)

    def _on_done(self, report: dict):
        self.donut.set_percent(100)
        self.add_event(tr("completed"))
        self._add_device(report)

    def _add_device(self, report: dict):
        from .datasource import device_summary
        # stamp the examination metadata onto the report
        meta = report.setdefault("meta", {})
        meta["examiner"] = self.examiner
        meta["case_id"] = self.case_id
        meta["organization"] = self.organization
        label = device_summary(report).get("name") or f"Device {len(self.devices)+1}"
        self.devices.append({"label": label, "report": report})
        src = (report.get("meta", {}) or {}).get("source_path", "")
        self.audit.record("evidence_loaded", f"{label} — {src}")
        # refresh the selector
        self._switching = True
        self.device_combo.clear()
        self.device_combo.addItems([d["label"] for d in self.devices])
        self.device_combo.setVisible(len(self.devices) > 1)
        self.device_combo.setCurrentIndex(len(self.devices) - 1)
        self._switching = False
        self.report = report
        self.refresh_views()

    def _switch_device(self, index: int):
        if self._switching or index < 0 or index >= len(self.devices):
            return
        self.report = self.devices[index]["report"]
        self.audit.record("device_switched", self.devices[index]["label"])
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
        storage = ""
        for key, val in device_fields(report):
            if key in ("f_storage", "f_capacity"):
                storage = val
        self.dev_storage_lbl.setText(storage)
        self.dev_storage_lbl.setVisible(bool(storage))
        # shorten very long UDIDs for the compact card
        ident = summ["ident"]
        self.dev_id_lbl.setText(f"UDID: {ident}" if ident else "")
        self.dev_status_lbl.setVisible(bool(self.report))
        self.phone_outline.setVisible(bool(self.report))
        self.device_info_btn.setVisible(bool(self.report))

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
        section = self.current_section

        # rich overview dashboard
        if section == "sec_overview":
            self.note_lbl.setVisible(False)
            self.search_box.setVisible(False)
            self.section_title_lbl.setVisible(False)
            self._build_overview(report)
            self.content_stack.setCurrentIndex(3)
            return
        self.section_title_lbl.setVisible(True)

        # apps grid
        if section == "sec_apps":
            self.note_lbl.setVisible(False)
            self.search_box.setVisible(False)
            self._build_apps_grid(report)
            self.content_stack.setCurrentIndex(2)
            return

        # offline map
        if section == "sec_location":
            self.note_lbl.setText(tr("scope_note"))
            self.note_lbl.setVisible(True)
            self.search_box.setVisible(False)
            markers = [
                MapMarker(m["lat"], m["lon"], m.get("label", ""))
                for m in location_markers(report)
            ]
            self.map_view.set_markers(markers)
            self.content_stack.setCurrentIndex(1)
            return

        # bookmarks
        if section == "sec_bookmarks":
            self.search_box.setVisible(False)
            self.note_lbl.setText(tr("bookmark_hint"))
            self.note_lbl.setVisible(True)
            cols = ["section", "data"]
            rows = [[b["section"], b["data"]] for b in self.bookmarks]
            self._current_cols = cols
            self._all_rows = rows
            self.table.clear()
            self.table.setColumnCount(len(cols))
            self.table.setHorizontalHeaderLabels(cols)
            self._fill_rows(rows)
            self.content_stack.setCurrentIndex(0)
            return

        # audit log
        if section == "sec_audit":
            self.search_box.setVisible(False)
            self.note_lbl.setVisible(False)
            cols = ["timestamp", "action", "detail"]
            rows = [[e["timestamp"], e["action"], e["detail"]]
                    for e in self.audit.as_rows()]
            self._current_cols = cols
            self._all_rows = rows
            self.table.clear()
            self.table.setColumnCount(len(cols))
            self.table.setHorizontalHeaderLabels(cols)
            self._fill_rows(rows)
            self.content_stack.setCurrentIndex(0)
            return

        # global search results
        if section == "sec_search":
            self.search_box.setVisible(False)
            self.note_lbl.setVisible(False)
            cols = ["section", "match"]
            rows = [[r["section"], r["match"]] for r in self._search_results]
            self._current_cols = cols
            self._all_rows = rows
            self.table.clear()
            self.table.setColumnCount(len(cols))
            self.table.setHorizontalHeaderLabels(cols)
            self._fill_rows(rows)
            self.content_stack.setCurrentIndex(0)
            return

        # default: table
        self.search_box.setVisible(True)
        table_section = "sec_messages" if section == "sec_overview" else section
        cols, rows, note = section_table(report, table_section)
        self.note_lbl.setText(note)
        self.note_lbl.setVisible(bool(note))
        self._current_cols = cols
        self._all_rows = rows
        self.table.clear()
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self._fill_rows(rows)
        self.content_stack.setCurrentIndex(0)

    def _run_global_search(self):
        q = self.global_search_box.text().strip()
        if not q or not self.report:
            return
        from .datasource import global_search
        self._search_results = global_search(self.report, q)
        self.audit.record("search", q)
        self.current_section = "sec_search"
        for b in self.section_btns.values():
            b.setChecked(False)
        self.section_title_lbl.setVisible(True)
        self.section_title_lbl.setText(
            f"{tr('search_results')} — {q} ({len(self._search_results)})")
        self.refresh_views()

    def _bookmark_row(self, r: int, _c: int):
        if self.current_section in ("sec_bookmarks", "sec_search"):
            return
        if r < 0 or r >= len(getattr(self, "_all_rows", [])):
            return
        data = "  ·  ".join(x for x in self._all_rows[r] if x)[:200]
        self.bookmarks.append({"section": tr(self.current_section),
                               "data": data})
        self.audit.record("bookmark_added", data[:80])
        notify(self, tr("sec_bookmarks"), data[:60], success=True)

    def _build_overview(self, report: dict):
        from .dashboard import build_dashboard

        while self.dash_layout.count():
            item = self.dash_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        dash = build_dashboard(
            report, self.open_app_chat, self.open_image_dialog
        )
        self.dash_layout.addWidget(dash)

    def _build_apps_grid(self, report: dict):
        while self.apps_grid.count():
            item = self.apps_grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        apps = chat_apps(report)
        if not apps:
            lbl = QLabel(tr("no_data"))
            lbl.setObjectName("noteLabel")
            self.apps_grid.addWidget(lbl, 0, 0)
            return
        from .appicons import BRAND, app_pixmap
        for i, app in enumerate(apps):
            n_msgs = sum(len(c["messages"]) for c in conversations(report, app["key"]))
            card = QFrame()
            card.setObjectName("appCard")
            card.setFixedHeight(150)
            card.setMinimumWidth(150)
            brand = BRAND.get(app["key"], theme.ACCENT)
            card.setStyleSheet(
                f"QFrame#appCard{{background:{theme.PANEL_ALT};"
                f"border:1px solid {theme.BORDER};border-radius:16px;}}"
                f"QFrame#appCard:hover{{border:2px solid {brand};}}"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 14, 10, 12)
            cl.setSpacing(6)
            icon = QLabel()
            icon.setPixmap(app_pixmap(app["key"], 56))
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name = QLabel(app["name"])
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name.setStyleSheet("font-size:13px;font-weight:600;")
            cnt = QLabel(f"{n_msgs:,} {tr('records')}")
            cnt.setObjectName("noteLabel")
            cnt.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(icon)
            cl.addWidget(name)
            cl.addWidget(cnt)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.mousePressEvent = (
                lambda _e, k=app["key"]: self.open_app_chat(k)
            )
            self.apps_grid.addWidget(card, i // 4, i % 4,
                                     Qt.AlignmentFlag.AlignTop)
        rows = (len(apps) + 3) // 4
        self.apps_grid.setRowStretch(rows, 1)
        self.apps_grid.setColumnStretch(4, 1)

    def open_app_chat(self, app_key: str):
        """Open the app's clone view inline, beside the grid (like the app)."""
        if not self.report:
            return
        convos = []
        for c in conversations(self.report, app_key):
            msgs = [ChatMessage(**m) for m in c["messages"]]
            convos.append(Conversation(title=c["title"], messages=msgs))
        story_items = stories(self.report, app_key) \
            if app_key in ("instagram", "snapchat") else None
        if app_key == "instagram":
            from .datasource import instagram_posts
            from .instaview import InstagramView
            view = InstagramView(self.report, instagram_posts(self.report),
                                 story_items, convos)
            view.image_clicked.connect(self.open_image_dialog)
        else:
            view = ChatView(app_key, convos, story_items)
            view.location_clicked.connect(self.open_map_dialog)
            view.image_clicked.connect(self.open_image_dialog)

        # swap into the inline chat page, wrapped so it can be sized like a
        # phone (centered, narrow) or fill the computer screen.
        while self.chat_container.count():
            item = self.chat_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        self._chat_view = view
        holder = QWidget()
        hb = QHBoxLayout(holder)
        hb.setContentsMargins(0, 0, 0, 0)
        hb.addStretch(0)        # index 0: left spacer
        hb.addWidget(view)      # index 1: the app view
        hb.addStretch(0)        # index 2: right spacer
        self._chat_hb = hb
        self.chat_container.addWidget(holder)
        self._set_chat_size(getattr(self, "_chat_size_mode", "full"))
        # remember where to return (apps grid by default)
        if self.current_section != "sec_apps":
            self._chat_return = self.current_section
        self.note_lbl.setVisible(False)
        self.search_box.setVisible(False)
        self.section_title_lbl.setVisible(True)
        self.section_title_lbl.setText(theme_for(app_key).name)
        self.content_stack.setCurrentIndex(4)

    def _set_chat_size(self, mode: str):
        self._chat_size_mode = mode
        self.size_phone_btn.setChecked(mode == "phone")
        self.size_full_btn.setChecked(mode == "full")
        view = getattr(self, "_chat_view", None)
        hb = getattr(self, "_chat_hb", None)
        if view is None or hb is None:
            return
        if mode == "phone":
            # narrow, phone-sized, centered between two spacers
            view.setFixedWidth(440)
            hb.setStretch(0, 1)
            hb.setStretch(1, 0)
            hb.setStretch(2, 1)
        else:
            # fill the whole computer screen
            view.setMinimumWidth(0)
            view.setMaximumWidth(16777215)
            hb.setStretch(0, 0)
            hb.setStretch(1, 1)
            hb.setStretch(2, 0)

    def _close_app_chat(self):
        self.select_section(getattr(self, "_chat_return", "sec_apps")
                            or "sec_apps")
        self._chat_return = "sec_apps"

    def open_image_dialog(self, path: str):
        # routes images, video and audio to the right preview
        from .mediaview import open_media
        self.audit.record("media_previewed", Path(path).name)
        open_media(self, path)

    def open_map_dialog(self, lat: float, lon: float, label: str):
        dlg = QDialog(self)
        dlg.setWindowTitle(label or "Location")
        dlg.resize(720, 520)
        lay = QVBoxLayout(dlg)
        m = OfflineMap()
        m.set_markers([MapMarker(lat, lon, label)])
        lay.addWidget(m)
        dlg.exec()

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
    def export_report(self, fmt: str = "html"):
        if not self.report:
            QMessageBox.information(self, "phonexe", tr("no_data"))
            return
        out = QFileDialog.getExistingDirectory(self, tr("export_report"))
        if not out:
            return
        out_dir = Path(out)
        try:
            if fmt == "json":
                path = reporting.write_json(self.report, out_dir / "report.json")
            elif fmt == "pdf":
                from ..reporting import pdf
                path = pdf.write_pdf(self.report, out_dir / "report.pdf")
            else:
                path = reporting.write_html(self.report, out_dir / "report.html")
        except Exception as e:
            QMessageBox.critical(self, "phonexe", str(e))
            return
        self.audit.record("report_exported", f"{fmt}: {path}")
        notify(self, tr("reports_title"), str(path), success=True)

    def save_case(self):
        if not self.report:
            QMessageBox.information(self, "phonexe", tr("no_data"))
            return
        out = QFileDialog.getExistingDirectory(self, tr("save_case"))
        if not out:
            return
        out_dir = Path(out)
        case = dict(self.report)
        case["bookmarks"] = self.bookmarks
        case.setdefault("meta", {})["audit"] = self.audit.as_rows()
        reporting.write_json(case, out_dir / "case.phonexe.json")
        self.audit.save(out_dir / "audit.json")
        self.audit.record("case_saved", str(out_dir))
        notify(self, tr("save_case"), str(out_dir / "case.phonexe.json"),
               success=True)

    def end_examination(self):
        self.report = None
        self.devices = []
        self._switching = True
        self.device_combo.clear()
        self.device_combo.hide()
        self._switching = False
        self.audit.record("examination_ended")
        self.donut.set_percent(0)
        self.select_section("sec_overview")
        self.refresh_views()

    def _show_device_info(self):
        if not self.report:
            return
        lines = [f"{tr(k)}: {v}" for k, v in device_fields(self.report)]
        QMessageBox.information(self, tr("device_info"),
                               "\n".join(lines) or tr("no_data"))

    def show_about(self):
        QMessageBox.information(
            self, "phonexe",
            f"phonexe v{__version__}\n\n{tr('scope_note')}",
        )
