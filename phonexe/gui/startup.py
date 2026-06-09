"""
Case setup / startup wizard.

Shown before the main window: collects the examiner name and case number,
then guides connecting the device (or opening an existing backup/extraction)
and detects the device details that seed the examination's chain of custody.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .fluent import LineEdit, PrimaryPushButton, PushButton
from .i18n import tr


class CaseSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("phonexe")
        self.resize(720, 600)
        self.source: tuple[str, str] | None = None  # ("path"|"acquire", value)
        self.device_info: dict = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(f"background:{theme.PANEL};")
        header.setFixedHeight(84)
        hl = QVBoxLayout(header)
        hl.setContentsMargins(28, 16, 28, 16)
        logo = QLabel("\U0001F6E1  phonexe")
        logo.setStyleSheet(
            f"color:{theme.ACCENT};font-size:20px;font-weight:700;")
        self.h_title = QLabel()
        self.h_title.setStyleSheet(f"color:{theme.TEXT_DIM};font-size:12px;")
        hl.addWidget(logo)
        hl.addWidget(self.h_title)
        outer.addWidget(header)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_case())     # 0
        self.stack.addWidget(self._page_connect())  # 1
        outer.addWidget(self.stack, 1)

        self._retranslate()

    # ----------------------------------------------------------- page 1
    def _page_case(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(40, 30, 40, 30)
        lay.setSpacing(14)

        self.p1_title = QLabel()
        self.p1_title.setStyleSheet(
            f"color:{theme.TEXT};font-size:18px;font-weight:700;")
        self.p1_sub = QLabel()
        self.p1_sub.setStyleSheet(f"color:{theme.TEXT_DIM};font-size:12px;")
        lay.addWidget(self.p1_title)
        lay.addWidget(self.p1_sub)
        lay.addSpacing(10)

        self.examiner_lbl = QLabel()
        self.examiner_edit = LineEdit()
        self.case_lbl = QLabel()
        self.case_edit = LineEdit()
        self.org_lbl = QLabel()
        self.org_edit = LineEdit()
        for lbl, ed in ((self.examiner_lbl, self.examiner_edit),
                        (self.case_lbl, self.case_edit),
                        (self.org_lbl, self.org_edit)):
            lbl.setStyleSheet(f"color:{theme.TEXT_DIM};font-size:12px;")
            lay.addWidget(lbl)
            lay.addWidget(ed)
        lay.addStretch(1)

        self.next_btn = PrimaryPushButton()
        self.next_btn.setMinimumHeight(40)
        self.next_btn.clicked.connect(self._go_connect)
        lay.addWidget(self.next_btn)
        return w

    # ----------------------------------------------------------- page 2
    def _page_connect(self) -> QWidget:
        from .widgets import NeonPhone
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(34, 24, 34, 24)
        lay.setSpacing(16)

        self.p2_title = QLabel()
        self.p2_title.setStyleSheet(
            f"color:{theme.TEXT};font-size:18px;font-weight:700;")
        lay.addWidget(self.p2_title)

        body = QHBoxLayout()
        body.setSpacing(20)

        # big square card with the glowing neon line-art phone
        square = QFrame()
        square.setObjectName("deviceCard")
        square.setFixedSize(300, 360)
        square.setStyleSheet(
            f"#deviceCard{{background:{theme.LEVEL2};border:1px solid "
            f"{theme.BORDER};border-radius:12px;}}")
        sq = QVBoxLayout(square)
        sq.setContentsMargins(8, 8, 8, 8)
        sq.addWidget(NeonPhone())
        body.addWidget(square, 0)

        # instructions + actions + detected device
        side = QVBoxLayout()
        side.setSpacing(12)
        self.steps_lbl = QLabel()
        self.steps_lbl.setWordWrap(True)
        self.steps_lbl.setStyleSheet(
            f"color:{theme.TEXT_DIM};font-size:13px;line-height:1.7;")
        side.addWidget(self.steps_lbl)

        self.detect_btn = PrimaryPushButton()
        self.detect_btn.setMinimumHeight(42)
        self.detect_btn.clicked.connect(self._detect)
        self.open_btn = PushButton()
        self.open_btn.setMinimumHeight(38)
        self.open_btn.clicked.connect(self._open_source)
        side.addWidget(self.detect_btn)
        side.addWidget(self.open_btn)

        self.device_card = QFrame()
        self.device_card.setObjectName("deviceCard")
        self.device_card.setStyleSheet(
            f"#deviceCard{{background:{theme.LEVEL2};border:1px solid "
            f"{theme.BORDER};border-radius:12px;}}")
        dcl = QVBoxLayout(self.device_card)
        dcl.setContentsMargins(14, 12, 14, 12)
        self.detected_title = QLabel()
        self.detected_title.setStyleSheet(
            f"color:{theme.TEXT_DIM};font-size:11px;font-weight:600;")
        self.detected_lbl = QLabel("—")
        self.detected_lbl.setWordWrap(True)
        self.detected_lbl.setStyleSheet(f"color:{theme.TEXT};font-size:13px;")
        dcl.addWidget(self.detected_title)
        dcl.addWidget(self.detected_lbl)
        side.addWidget(self.device_card)
        side.addStretch(1)
        body.addLayout(side, 1)
        lay.addLayout(body, 1)

        nav = QHBoxLayout()
        self.back_btn = PushButton()
        self.back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.start_btn = PrimaryPushButton()
        self.start_btn.setMinimumHeight(40)
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
        self.h_title.setText(tr("welcome_sub"))
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
