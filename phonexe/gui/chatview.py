"""
App-faithful chat viewer.

Renders extracted conversations the way the original messaging app looks:
a conversation list beside a bubble thread, with per-app theming (WhatsApp
green, Telegram blue, iMessage, etc.), inline images, and tappable location
bubbles that open the offline map.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from . import theme


@dataclass
class AppTheme:
    name: str
    header: str          # header / accent bar color
    sent_bubble: str     # outgoing bubble color
    sent_text: str
    recv_bubble: str     # incoming bubble color
    recv_text: str
    chat_bg: str
    glyph: str = "▣"


APP_THEMES: dict[str, AppTheme] = {
    "whatsapp": AppTheme("WhatsApp", "#075E54", "#005C4B", "#e9edef",
                         "#202c33", "#e9edef", "#0b141a", "✆"),
    "messages": AppTheme("Messages", "#1f6feb", "#0b81ff", "#ffffff",
                         "#26282b", "#e6ebf5", "#0c0f14", "✉"),
    "telegram": AppTheme("Telegram", "#517da2", "#2b5278", "#ffffff",
                         "#182533", "#e6ebf5", "#0e1621", "✈"),
    "instagram": AppTheme("Instagram", "#c13584", "#3797f0", "#ffffff",
                          "#262626", "#fafafa", "#000000", "◉"),
    "discord": AppTheme("Discord", "#5865F2", "#5865F2", "#ffffff",
                        "#2b2d31", "#dbdee1", "#313338", "✦"),
    "snapchat": AppTheme("Snapchat", "#000000", "#0fadff", "#ffffff",
                         "#1b1b1b", "#fffc00", "#101010", "☂"),
    "signal": AppTheme("Signal", "#3A76F0", "#2c6bed", "#ffffff",
                       "#2a2a2a", "#e6ebf5", "#121212", "▲"),
    "messenger": AppTheme("Messenger", "#0084FF", "#0084ff", "#ffffff",
                          "#303030", "#e6ebf5", "#0b0b0b", "◈"),
    "tiktok": AppTheme("TikTok", "#010101", "#fe2c55", "#ffffff",
                       "#1f1f1f", "#e6ebf5", "#101010", "♪"),
}


def theme_for(key: str) -> AppTheme:
    return APP_THEMES.get(key, AppTheme(
        key.title(), theme.ACCENT_DIM, theme.ACCENT_DIM, "#ffffff",
        theme.PANEL_ALT, theme.TEXT, theme.BG, "▣"))


@dataclass
class ChatMessage:
    from_me: bool
    text: str | None = None
    timestamp: str | None = None
    sender: str | None = None
    image: str | None = None
    lat: float | None = None
    lon: float | None = None


@dataclass
class Conversation:
    title: str
    messages: list[ChatMessage] = field(default_factory=list)


class _Bubble(QFrame):
    location_clicked = pyqtSignal(float, float, str)

    def __init__(self, msg: ChatMessage, th: AppTheme):
        super().__init__()
        bubble = msg.from_me
        bg = th.sent_bubble if bubble else th.recv_bubble
        fg = th.sent_text if bubble else th.recv_text
        self.setStyleSheet(
            f"background: {bg}; border-radius: 10px;"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 7, 10, 5)
        lay.setSpacing(3)

        if msg.sender and not msg.from_me:
            s = QLabel(msg.sender)
            s.setStyleSheet(f"color: {th.header}; font-weight: 600; font-size: 11px;")
            lay.addWidget(s)

        # location bubble
        if msg.lat is not None and msg.lon is not None:
            btn = QPushButton(f"📍  {msg.lat:.5f}, {msg.lon:.5f}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"text-align:left; border:1px solid {th.header};"
                f"border-radius:8px; padding:8px; color:{fg};"
                f"background: rgba(0,0,0,0.15);"
            )
            label = msg.text or "Shared location"
            btn.clicked.connect(
                lambda: self.location_clicked.emit(msg.lat, msg.lon, label)
            )
            lay.addWidget(btn)

        # image
        if msg.image:
            img_lbl = QLabel()
            p = Path(msg.image)
            if p.exists():
                pix = QPixmap(str(p))
                if not pix.isNull():
                    img_lbl.setPixmap(
                        pix.scaledToWidth(220, Qt.TransformationMode.SmoothTransformation)
                    )
                else:
                    img_lbl.setText("🖼  image")
            else:
                img_lbl.setText("🖼  image (not in extraction)")
            img_lbl.setStyleSheet(f"color: {fg};")
            lay.addWidget(img_lbl)

        # text
        if msg.text and msg.lat is None:
            t = QLabel(msg.text)
            t.setWordWrap(True)
            t.setStyleSheet(f"color: {fg}; font-size: 13px;")
            lay.addWidget(t)

        if msg.timestamp:
            ts = QLabel(msg.timestamp.replace("T", " ")[:19])
            ts.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 9px;")
            ts.setAlignment(Qt.AlignmentFlag.AlignRight)
            lay.addWidget(ts)

        self.setMaximumWidth(380)


class ChatView(QWidget):
    """Two-pane app-styled chat browser."""

    location_clicked = pyqtSignal(float, float, str)

    def __init__(self, app_key: str, conversations: list[Conversation]):
        super().__init__()
        self.theme = theme_for(app_key)
        self.conversations = conversations

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # app header bar
        header = QFrame()
        header.setStyleSheet(f"background: {self.theme.header};")
        header.setFixedHeight(46)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 14, 0)
        title = QLabel(f"{self.theme.glyph}   {self.theme.name}")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: 700;")
        hl.addWidget(title)
        hl.addStretch(1)
        root.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # conversation list
        self.list = QListWidget()
        self.list.setFixedWidth(230)
        self.list.setStyleSheet(
            f"QListWidget{{background:{theme.PANEL_ALT};border:none;}}"
            f"QListWidget::item{{padding:12px 14px;border-bottom:1px solid {theme.BORDER};}}"
            f"QListWidget::item:selected{{background:{theme.PANEL};color:{theme.ACCENT};}}"
        )
        for conv in conversations:
            QListWidgetItem(conv.title or "(unknown)", self.list)
        self.list.currentRowChanged.connect(self._show_conversation)
        body.addWidget(self.list)

        # message thread
        self.thread_scroll = QScrollArea()
        self.thread_scroll.setWidgetResizable(True)
        self.thread_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.thread_scroll.setStyleSheet(
            f"background:{self.theme.chat_bg};border:none;"
        )
        self.thread_inner = QWidget()
        self.thread_inner.setStyleSheet(f"background:{self.theme.chat_bg};")
        self.thread_layout = QVBoxLayout(self.thread_inner)
        self.thread_layout.setContentsMargins(16, 12, 16, 12)
        self.thread_layout.setSpacing(8)
        self.thread_layout.addStretch(1)
        self.thread_scroll.setWidget(self.thread_inner)
        body.addWidget(self.thread_scroll, 1)

        root.addLayout(body, 1)

        if conversations:
            self.list.setCurrentRow(0)

    def _clear_thread(self):
        while self.thread_layout.count():
            item = self.thread_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    def _show_conversation(self, row: int):
        self._clear_thread()
        if row < 0 or row >= len(self.conversations):
            self.thread_layout.addStretch(1)
            return
        conv = self.conversations[row]
        for msg in conv.messages:
            bubble = _Bubble(msg, self.theme)
            bubble.location_clicked.connect(self.location_clicked)
            row_lay = QHBoxLayout()
            row_lay.setContentsMargins(0, 0, 0, 0)
            if msg.from_me:
                row_lay.addStretch(1)
                row_lay.addWidget(bubble)
            else:
                row_lay.addWidget(bubble)
                row_lay.addStretch(1)
            holder = QWidget()
            holder.setLayout(row_lay)
            self.thread_layout.addWidget(holder)
        self.thread_layout.addStretch(1)
