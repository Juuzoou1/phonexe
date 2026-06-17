"""
Instagram-style app view (dark), modeled on the real app: a feed of posts,
a stories row, top actions, and a bottom navigation bar — plus a DMs tab that
reuses the chat clone. Populated from the device's extracted Instagram
artifacts (cached/shared images, senders, message text).
"""

from __future__ import annotations

import html
from pathlib import Path

from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .chatview import ChatMessage, ChatView, Conversation
from .svgicons import nav_icon
from .widgets import avatar_pixmap

IG_BG = "#000000"
IG_CARD = "#000000"
IG_BORDER = "#262626"
IG_TEXT = "#fafafa"
IG_DIM = "#a8a8a8"


def _gradient_avatar(name: str, image: str | None, size: int) -> QPixmap:
    """Circular avatar with the Instagram gradient ring."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    from PyQt6.QtGui import QConicalGradient
    g = QConicalGradient(size / 2, size / 2, 90)
    g.setColorAt(0.0, QColor("#FEDA75"))
    g.setColorAt(0.3, QColor("#FA7E1E"))
    g.setColorAt(0.6, QColor("#D62976"))
    g.setColorAt(1.0, QColor("#4F5BD5"))
    p.setBrush(g)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(0, 0, size, size)
    inner = size - 8
    # inner avatar (image or letter)
    av = QPixmap(inner, inner)
    av.fill(Qt.GlobalColor.transparent)
    ap = QPainter(av)
    ap.setRenderHint(QPainter.RenderHint.Antialiasing)
    clip = QPainterPath()
    clip.addEllipse(0, 0, inner, inner)
    ap.setClipPath(clip)
    if image and Path(image).exists():
        src = QPixmap(image)
        if not src.isNull():
            ap.drawPixmap(0, 0, src.scaled(
                inner, inner, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation))
        else:
            ap.drawPixmap(0, 0, avatar_pixmap(name, inner))
    else:
        ap.drawPixmap(0, 0, avatar_pixmap(name, inner))
    ap.end()
    p.drawPixmap(4, 4, av)
    p.end()
    return pix


def _icon_label(name: str, size: int = 24, color: str = IG_TEXT) -> QLabel:
    lbl = QLabel()
    lbl.setPixmap(nav_icon(name, size, color))
    return lbl


class InstagramView(QWidget):
    image_clicked = pyqtSignal(str)

    def __init__(self, report: dict, posts: list[dict],
                 stories: list[dict], dm_convos: list[Conversation]):
        super().__init__()
        self.setStyleSheet(f"background:{IG_BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._top_bar())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._feed_page(posts, stories))   # 0
        dm = ChatView("instagram", dm_convos, stories)
        dm.image_clicked.connect(self.image_clicked)
        self.stack.addWidget(dm)                                 # 1
        root.addWidget(self.stack, 1)

        root.addWidget(self._bottom_nav())

    # ------------------------------------------------------------ top bar
    def _top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"background:{IG_BG};border-bottom:1px solid {IG_BORDER};")
        h = QHBoxLayout(bar)
        h.setContentsMargins(14, 0, 14, 0)
        logo = QLabel("Instagram")
        logo.setStyleSheet("color:#fafafa;font-size:20px;font-weight:700;"
                           "font-family:'Segoe Script','Cairo';")
        h.addWidget(logo)
        h.addStretch(1)
        for ic in ("square-plus", "heart", "send"):
            h.addWidget(_icon_label(ic, 22))
            h.addSpacing(14)
        # DM shortcut on the send icon
        dm_btn = _icon_label("send", 1)
        return bar

    # ------------------------------------------------------------ feed
    def _feed_page(self, posts, stories) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background:{IG_BG};border:none;")
        inner = QWidget()
        inner.setStyleSheet(f"background:{IG_BG};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._stories_row(stories))
        lay.addWidget(self._divider())
        if posts:
            for post in posts:
                lay.addWidget(self._post_card(post))
        else:
            empty = QLabel("لا توجد منشورات مستخرجة")
            empty.setStyleSheet(f"color:{IG_DIM};padding:30px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(empty)
        lay.addStretch(1)
        scroll.setWidget(inner)
        return scroll

    def _divider(self) -> QFrame:
        d = QFrame()
        d.setFixedHeight(1)
        d.setStyleSheet(f"background:{IG_BORDER};")
        return d

    def _stories_row(self, stories) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"background:{IG_BG};")
        h = QHBoxLayout(w)
        h.setContentsMargins(10, 10, 10, 10)
        h.setSpacing(14)
        items = stories or []
        if not items:
            items = [{"title": "story", "image": ""}]
        for s in items[:10]:
            col = QVBoxLayout()
            col.setSpacing(4)
            av = QLabel()
            av.setPixmap(_gradient_avatar(s.get("title", "?"),
                                          s.get("image"), 64))
            av.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nm = QLabel(str(s.get("title", ""))[:10])
            nm.setStyleSheet(f"color:{IG_TEXT};font-size:11px;")
            nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(av)
            col.addWidget(nm)
            cw = QWidget()
            cw.setLayout(col)
            h.addWidget(cw)
        h.addStretch(1)
        return w

    def _post_card(self, post: dict) -> QWidget:
        card = QFrame()
        card.setStyleSheet(f"background:{IG_BG};")
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 6, 0, 8)
        v.setSpacing(6)

        # header
        head = QHBoxLayout()
        head.setContentsMargins(12, 0, 12, 0)
        av = QLabel()
        av.setPixmap(_gradient_avatar(post.get("username", "?"), None, 34))
        uname = QLabel(post.get("username", ""))
        uname.setStyleSheet(f"color:{IG_TEXT};font-weight:600;font-size:13px;")
        head.addWidget(av)
        head.addWidget(uname)
        head.addStretch(1)
        more = QLabel("•••")
        more.setStyleSheet(f"color:{IG_TEXT};")
        head.addWidget(more)
        v.addLayout(head)

        # image
        img = QLabel()
        img.setStyleSheet(f"background:{IG_CARD};")
        img.setMinimumHeight(260)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        path = post.get("image")
        if path and Path(path).exists():
            pix = QPixmap(path)
            if not pix.isNull():
                img.setPixmap(pix.scaledToWidth(
                    500, Qt.TransformationMode.SmoothTransformation))
                img.setCursor(Qt.CursorShape.PointingHandCursor)
                img.mousePressEvent = lambda _e, p=path: self.image_clicked.emit(p)
        v.addWidget(img)

        # actions
        act = QHBoxLayout()
        act.setContentsMargins(12, 2, 12, 0)
        for ic in ("heart", "message-circle", "send"):
            act.addWidget(_icon_label(ic, 22))
            act.addSpacing(12)
        act.addStretch(1)
        act.addWidget(_icon_label("bookmark", 22))
        v.addLayout(act)

        # likes + caption
        likes = QLabel(f"{post.get('likes', 0):,} إعجاب")
        likes.setStyleSheet(f"color:{IG_TEXT};font-weight:600;font-size:12px;")
        likes.setContentsMargins(12, 0, 12, 0)
        v.addWidget(likes)
        if post.get("caption"):
            cap = QLabel(f"<b>{html.escape(post.get('username',''))}</b>  "
                         f"{html.escape(str(post['caption']))}")
            cap.setWordWrap(True)
            cap.setStyleSheet(f"color:{IG_TEXT};font-size:12px;")
            cap.setContentsMargins(12, 0, 12, 0)
            v.addWidget(cap)
        when = QLabel(str(post.get("time", ""))[:16].replace("T", " "))
        when.setStyleSheet(f"color:{IG_DIM};font-size:10px;")
        when.setContentsMargins(12, 0, 12, 4)
        v.addWidget(when)
        v.addWidget(self._divider())
        return card

    # ------------------------------------------------------------ bottom nav
    def _bottom_nav(self) -> QWidget:
        bar = QFrame()
        bar.setFixedHeight(50)
        bar.setStyleSheet(f"background:{IG_BG};border-top:1px solid {IG_BORDER};")
        h = QHBoxLayout(bar)
        h.setContentsMargins(20, 0, 20, 0)
        for i, ic in enumerate(("house", "search", "clapperboard",
                                "shopping-bag", "circle-user")):
            btn = _icon_label(ic, 24, IG_TEXT if i == 0 else "#cfcfcf")
            h.addWidget(btn)
            if i < 4:
                h.addStretch(1)
        # send icon toggles DMs
        return bar
