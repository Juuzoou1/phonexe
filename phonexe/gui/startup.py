"""
Case setup / startup wizard.

Shown before the main window: collects the examiner name and case number,
then guides connecting the device (or opening an existing backup/extraction)
and detects the device details that seed the examination's chain of custody.

Styled in an Apple-inspired dark aesthetic: near-black canvas, centered
content, soft rounded fields, San-Francisco-like typography (IBM Plex Sans
Arabic) and the Apple system-blue call to action.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .i18n import tr

# ----------------------------------------------------------------- palette
# Apple dark-mode system colours.
_BG = "#000000"
_CARD = "#1C1C1E"
_CARD2 = "#2C2C2E"
_BORDER = "#38383A"
_TXT = "#F5F5F7"
_TXT2 = "#86868B"
_TXT3 = "#AEAEB2"
_BLUE = "#0A84FF"

_QSS = f"""
QDialog#caseSetup, QWidget#page {{ background:{_BG}; }}
QFrame#headerBar {{ background:{_BG}; border-bottom:1px solid #1C1C1E; }}

QLabel {{ color:{_TXT}; background:transparent; }}
QLabel#wordmark {{ color:{_TXT}; font-size:17px; font-weight:600;
                   letter-spacing:0.3px; }}
QLabel#pageTitle {{ color:{_TXT}; font-size:27px; font-weight:600;
                    letter-spacing:0.2px; }}
QLabel#pageSub {{ color:{_TXT2}; font-size:14px; }}
QLabel#fieldLabel {{ color:{_TXT2}; font-size:12px; font-weight:600; }}
QLabel#stepsLabel {{ color:{_TXT3}; font-size:13px; }}
QLabel#detTitle {{ color:{_TXT2}; font-size:11px; font-weight:700;
                   letter-spacing:0.4px; }}
QLabel#detBody {{ color:{_TXT}; font-size:13px; }}

QLineEdit {{
    background:{_CARD}; border:1px solid {_BORDER}; border-radius:10px;
    padding:0 14px; min-height:42px; color:{_TXT}; font-size:15px;
    selection-background-color:{_BLUE};
}}
QLineEdit:focus {{ border:1px solid {_BLUE}; background:#222224; }}

QPushButton#primary {{
    background:{_BLUE}; color:#FFFFFF; border:none; border-radius:12px;
    min-height:46px; font-size:16px; font-weight:600;
}}
QPushButton#primary:hover {{ background:#3395FF; }}
QPushButton#primary:pressed {{ background:#0060DF; }}
QPushButton#primary:disabled {{ background:{_CARD2}; color:#6E6E73; }}

QPushButton#secondary {{
    background:{_CARD}; color:{_TXT}; border:1px solid {_BORDER};
    border-radius:12px; min-height:42px; font-size:15px; font-weight:500;
}}
QPushButton#secondary:hover {{ background:{_CARD2}; }}

QFrame#deviceCard {{ background:{_CARD}; border:1px solid {_BORDER};
                     border-radius:14px; }}
"""


class CaseSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("caseSetup")
        self.setWindowTitle("phonexe")
        self.resize(760, 640)
        self.setStyleSheet(_QSS)
        self.source: tuple[str, str] | None = None  # ("path"|"acquire", value)
        self.device_info: dict = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(62)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(26, 0, 26, 0)
        logo = QLabel("phonexe")
        logo.setObjectName("wordmark")
        hl.addWidget(logo)
        hl.addStretch(1)
        outer.addWidget(header)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_case())     # 0
        self.stack.addWidget(self._page_connect())  # 1
        outer.addWidget(self.stack, 1)

        self._retranslate()

    # -------------------------------------------------------- small helpers
    def _field(self, lbl: QLabel, edit: QLineEdit, col: QVBoxLayout):
        lbl.setObjectName("fieldLabel")
        edit.setClearButtonEnabled(False)
        col.addWidget(lbl)
        col.addSpacing(6)
        col.addWidget(edit)
        col.addSpacing(16)

    # ----------------------------------------------------------- page 1
    def _page_case(self) -> QWidget:
        w = QWidget()
        w.setObjectName("page")
        row = QHBoxLayout(w)
        row.setContentsMargins(40, 0, 40, 0)
        row.addStretch(1)

        col = QVBoxLayout()
        col.setSpacing(0)
        center = QWidget()
        center.setObjectName("page")
        center.setFixedWidth(400)
        center.setLayout(col)

        col.addStretch(3)
        self.p1_title = QLabel()
        self.p1_title.setObjectName("pageTitle")
        self.p1_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.p1_sub = QLabel()
        self.p1_sub.setObjectName("pageSub")
        self.p1_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.p1_sub.setWordWrap(True)
        col.addWidget(self.p1_title)
        col.addSpacing(8)
        col.addWidget(self.p1_sub)
        col.addSpacing(34)

        self.examiner_lbl = QLabel()
        self.examiner_edit = QLineEdit()
        self.case_lbl = QLabel()
        self.case_edit = QLineEdit()
        self.org_lbl = QLabel()
        self.org_edit = QLineEdit()
        self._field(self.examiner_lbl, self.examiner_edit, col)
        self._field(self.case_lbl, self.case_edit, col)
        self._field(self.org_lbl, self.org_edit, col)

        col.addSpacing(12)
        self.next_btn = QPushButton()
        self.next_btn.setObjectName("primary")
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self._go_connect)
        col.addWidget(self.next_btn)
        col.addStretch(4)

        row.addWidget(center)
        row.addStretch(1)
        return w

    # ----------------------------------------------------------- page 2
    def _page_connect(self) -> QWidget:
        from .widgets import NeonPhone
        w = QWidget()
        w.setObjectName("page")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40, 28, 40, 28)
        lay.setSpacing(18)

        self.p2_title = QLabel()
        self.p2_title.setObjectName("pageTitle")
        lay.addWidget(self.p2_title)

        body = QHBoxLayout()
        body.setSpacing(22)

        # large card with the glowing line-art phone
        square = QFrame()
        square.setObjectName("deviceCard")
        square.setFixedSize(300, 360)
        sq = QVBoxLayout(square)
        sq.setContentsMargins(8, 8, 8, 8)
        sq.addWidget(NeonPhone())
        body.addWidget(square, 0)

        # instructions + actions + detected device
        side = QVBoxLayout()
        side.setSpacing(12)
        self.steps_lbl = QLabel()
        self.steps_lbl.setObjectName("stepsLabel")
        self.steps_lbl.setWordWrap(True)
        side.addWidget(self.steps_lbl)

        self.detect_btn = QPushButton()
        self.detect_btn.setObjectName("primary")
        self.detect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.detect_btn.clicked.connect(self._detect)
        self.open_btn = QPushButton()
        self.open_btn.setObjectName("secondary")
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.clicked.connect(self._open_source)
        side.addWidget(self.detect_btn)
        side.addWidget(self.open_btn)

        self.device_card = QFrame()
        self.device_card.setObjectName("deviceCard")
        dcl = QVBoxLayout(self.device_card)
        dcl.setContentsMargins(16, 14, 16, 14)
        self.detected_title = QLabel()
        self.detected_title.setObjectName("detTitle")
        self.detected_lbl = QLabel("—")
        self.detected_lbl.setObjectName("detBody")
        self.detected_lbl.setWordWrap(True)
        dcl.addWidget(self.detected_title)
        dcl.addWidget(self.detected_lbl)
        side.addWidget(self.device_card)
        side.addStretch(1)
        body.addLayout(side, 1)
        lay.addLayout(body, 1)

        nav = QHBoxLayout()
        self.back_btn = QPushButton()
        self.back_btn.setObjectName("secondary")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.start_btn = QPushButton()
        self.start_btn.setObjectName("primary")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.accept)
        nav.addWidget(self.back_btn)
        nav.addStretch(1)
        nav.addWidget(self.start_btn)
        lay.addLayout(nav)
        return w

    # ----------------------------------------------------------- actions
    def _go_connect(self):
        if not self.examiner_edit.text().strip() or \
                not self.case_edit.text().strip():
            from .fluent import notify
            notify(self, tr("welcome_title"),
                   f"{tr('f_examiner')} / {tr('f_case')}", success=False)
            return
        self.stack.setCurrentIndex(1)
        self._retranslate()

    def _detect(self):
        """Auto-detect a connected device (iPhone or Android) — no manual pick."""
        # 1) iPhone via Apple's backup protocol
        try:
            from .. import ios_acquire
            devices = ios_acquire.list_devices()
        except Exception:
            devices = []
        if devices:
            info = ios_acquire.device_info(devices[0])
            self.source = ("acquire", devices[0])
            self.device_info = {
                "platform": "iPhone (iOS)",
                "name": info.get("DeviceName"),
                "model": info.get("ProductType"),
                "os": info.get("ProductVersion"),
                "imei": info.get("InternationalMobileEquipmentIdentity"),
                "serial": info.get("SerialNumber") or devices[0],
            }
            self._show_device()
            return
        # 2) Android via ADB
        try:
            from ..android import adb
            if adb.adb_available():
                ad = adb.list_devices()
                if ad:
                    info = adb.device_info(ad[0])
                    self.source = ("adb", ad[0])
                    self.device_info = {
                        "platform": "Android",
                        "name": info.get("model"),
                        "model": f"{info.get('manufacturer','')} "
                                 f"{info.get('model','')}".strip(),
                        "os": f"Android {info.get('android_version','')}".strip(),
                        "serial": info.get("serial") or ad[0],
                    }
                    self._show_device()
                    return
        except Exception:
            pass
        # nothing detected — explain clearly what is needed
        self.detected_lbl.setText(tr("no_device_found"))
        try:
            from .. import ios_acquire
            ready = ios_acquire.check().get("ready")
        except Exception:
            ready = False
        from .fluent import notify
        if not ready:
            notify(self, tr("detect_device"),
                   "لم يُعثر على جهاز. ثبّت تطبيق \"Apple Devices\" (تعريف USB) "
                   "للآيفون، أو استخدم \"فتح مصدر / استخراج\" لتحليل نسخة "
                   "احتياطية جاهزة.", success=False)
        else:
            notify(self, tr("detect_device"),
                   "لم يُعثر على جهاز متصل. تأكد أن الجهاز مفتوح وموثوق "
                   "(\"الثقة بهذا الكمبيوتر\")، أو استخدم \"فتح مصدر\".",
                   success=False)

    def _open_source(self):
        path = QFileDialog.getExistingDirectory(self, tr("open_source"))
        if not path:
            return
        self.source = ("path", path)
        self.device_info = self._read_device_info(path)
        self._show_device()

    def _read_device_info(self, path: str) -> dict:
        try:
            from ..analyze import detect_platform
            plat = detect_platform(path)
            if plat == "ios":
                from ..backup import IOSBackup
                d = IOSBackup(path).device
                return {"platform": "iPhone (iOS)",
                        "name": d.device_name, "model": d.product_type,
                        "os": f"iOS {d.product_version or ''}".strip(),
                        "imei": d.imei, "serial": d.serial_number}
            if plat == "android":
                from ..android.extraction import AndroidExtraction
                d = AndroidExtraction(path).device
                return {"platform": "Android",
                        "name": d.model, "model": d.model,
                        "os": f"Android {d.android_version or ''}".strip(),
                        "imei": None, "serial": d.serial}
        except Exception:
            pass
        return {"name": path}

    def _show_device(self):
        d = self.device_info
        lines = []
        if d.get("platform"):
            lines.append(f"النوع: {d['platform']}")
        for key, label in (("name", tr("f_name")), ("model", tr("f_model")),
                           ("os", tr("f_os")), ("imei", "IMEI"),
                           ("serial", tr("f_serial"))):
            if d.get(key):
                lines.append(f"{label}: {d[key]}")
        self.detected_lbl.setText("\n".join(lines) or "—")
        self.start_btn.setEnabled(bool(self.source))

    # ----------------------------------------------------------- i18n
    def _retranslate(self):
        self.p1_title.setText(tr("welcome_title"))
        self.p1_sub.setText(tr("welcome_sub"))
        self.examiner_lbl.setText(tr("f_examiner"))
        self.case_lbl.setText(tr("f_case"))
        self.org_lbl.setText(tr("f_org"))
        self.next_btn.setText(tr("next"))
        self.p2_title.setText(tr("connect_title"))
        self.steps_lbl.setText(tr("connect_steps"))
        self.detect_btn.setText(tr("detect_device"))
        self.open_btn.setText(tr("open_source"))
        self.detected_title.setText(tr("detected_device"))
        self.back_btn.setText(tr("back"))
        self.start_btn.setText(tr("start_exam"))

    # ----------------------------------------------------------- result
    def result_data(self) -> dict:
        return {
            "examiner": self.examiner_edit.text().strip(),
            "case_id": self.case_edit.text().strip(),
            "organization": self.org_edit.text().strip(),
            "source": self.source,
            "device_info": self.device_info,
        }
