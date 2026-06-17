"""
License / activation gate.

Requires a secret activation code before the program can be used. Once the
correct code is entered it is remembered (a hash is stored locally) so it is
not asked again on the same machine.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout

from . import theme
from .fluent import LineEdit, PrimaryPushButton, notify

# The secret activation code required to use phonexe.
_CODE = "2002"
_DIR = Path.home() / ".phonexe"
_FILE = _DIR / "activation.json"


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def check_code(code: str) -> bool:
    return code.strip() == _CODE


def is_activated() -> bool:
    try:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
        return data.get("code_hash") == _hash(_CODE)
    except Exception:
        return False


def activate() -> None:
    try:
        _DIR.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(
            json.dumps({"activated": True, "code_hash": _hash(_CODE)}),
            encoding="utf-8")
    except Exception:
        pass


class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("phonexe")
        self.setFixedSize(420, 260)
        self.setStyleSheet(f"background:{theme.BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(34, 28, 34, 28)
        lay.setSpacing(14)

        lock = QLabel("\U0001F512")
        lock.setStyleSheet(f"font-size:34px;color:{theme.ACCENT};")
        lock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("تفعيل phonexe")
        title.setStyleSheet(
            f"color:{theme.TEXT};font-size:18px;font-weight:700;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("أدخل الرقم السري للتفعيل")
        sub.setStyleSheet(f"color:{theme.TEXT_DIM};font-size:12px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lock)
        lay.addWidget(title)
        lay.addWidget(sub)

        self.code_edit = LineEdit()
        self.code_edit.setEchoMode(LineEdit.EchoMode.Password)
        self.code_edit.setPlaceholderText("الرقم السري")
        self.code_edit.returnPressed.connect(self._try)
        lay.addWidget(self.code_edit)

        self.btn = PrimaryPushButton("تفعيل")
        self.btn.setMinimumHeight(40)
        self.btn.clicked.connect(self._try)
        lay.addWidget(self.btn)

    def _try(self):
        if check_code(self.code_edit.text()):
            activate()
            self.accept()
        else:
            self.code_edit.clear()
            notify(self, "phonexe", "رقم سري غير صحيح", success=False)


def ensure_activated(parent=None) -> bool:
    """Return True if activated (prompting for the code if needed)."""
    if is_activated():
        return True
    dlg = LicenseDialog(parent)
    return dlg.exec() == QDialog.DialogCode.Accepted
