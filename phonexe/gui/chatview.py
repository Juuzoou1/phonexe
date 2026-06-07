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


class ClickableLabel(QLabel):
    """A QLabel that emits its associated path string when clicked."""

    clicked = pyqtSignal(str)

    def __init__(self, path: str = ""):
        super().__init__()
        self._path = path
        if path:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, _e):  # noqa: N802
        if self._path:
            self.clicked.emit(self._path)


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
    image_clicked = pyqtSignal(str)

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

        # image (click to preview full size)
        if msg.image:
            p = Path(msg.image)
            img_lbl = ClickableLabel(str(p) if p.exists() else "")
            if p.exists():
                pix = QPixmap(str(p))
                if not pix.isNull():
                    img_lbl.setPixmap(
                        pix.scaledToWidth(220, Qt.TransformationMode.SmoothTransformation)
                    )
                    img_lbl.clicked.connect(self.image_clicked)
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
            ts = QLabel(str(msg.timestamp).replace("T", " ")[:19])
            ts.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 9px;")
            ts.setAlignment(Qt.AlignmentFlag.AlignRight)
            lay.addWidget(ts)

        self.setMaximumWidth(380)


class ChatView(QWidget):
    """Two-pane app-styled chat browser."""

    location_clicked = pyqtSignal(float, float, str)
    image_clicked = pyqtSignal(str)

    def __init__(self, app_key: str, conversations: list[Conversation],
                 stories: list[dict] | None = None):
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

        # stories strip (Instagram / Snapchat style)
        if stories:
            root.addWidget(self._build_stories(stories))

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

    def _build_stories(self, stories: list[dict]) -> QWidget:
        from PyQt6.QtGui import QBrush, QPainter, QPainterPath

        strip = QFrame()
        strip.setStyleSheet(f"background: {theme.PANEL_ALT};")
        strip.setFixedHeight(96)
        lay = QHBoxLayout(strip)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(12)
        for st in stories[:12]:
            col = QVBoxLayout()
            col.setSpacing(2)
            avatar = ClickableLabel(st.get("image", ""))
            avatar.setFixedSize(58, 58)
            pix = QPixmap(st["image"]) if Path(st.get("image", "")).exists() else QPixmap()
            if not pix.isNull():
                # circular crop with an accent ring
                size = 58
                circ = QPixmap(size, size)
                circ.fill(Qt.GlobalColor.transparent)
                painter = QPainter(circ)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(2, 2, size - 4, size - 4)
                painter.setClipPath(path)
                painter.drawPixmap(
                    2, 2, pix.scaled(size - 4, size - 4,
                                     Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                     Qt.TransformationMode.SmoothTransformation))
                painter.setClipping(False)
                from PyQt6.QtGui import QPen
                from PyQt6.QtGui import QColor
                painter.setPen(QPen(QColor(self.theme.header), 3))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawEllipse(2, 2, size - 4, size - 4)
                painter.end()
                avatar.setPixmap(circ)
                avatar.clicked.connect(self.image_clicked)
            else:
                avatar.setStyleSheet(
                    f"border:3px solid {self.theme.header};border-radius:29px;"
                    f"background:{theme.PANEL};")
            name = QLabel(str(st.get("title", ""))[:10])
            name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            name.setStyleSheet(f"color:{theme.TEXT_DIM};font-size:10px;")
            col.addWidget(avatar, 0, Qt.AlignmentFlag.AlignHCenter)
            col.addWidget(name)
            holder = QWidget()
            holder.setLayout(col)
            lay.addWidget(holder)
        lay.addStretch(1)
        return strip

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
            bubble.image_clicked.connect(self.image_clicked)
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
