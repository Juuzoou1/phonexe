"""
Rich Overview dashboard, reproducing the reference mockup: Instagram and
WhatsApp preview panels, an installed-apps grid, contacts, an activity bar
chart, and keyword analysis.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from . import theme
from .appicons import BRAND, app_pixmap
from .chatview import theme_for
from .datasource import (
    activity_by_source,
    chat_apps,
    conversations,
    keywords,
    stories,
)
from .datasource import _records  # noqa: internal helper reuse
from .widgets import BarChart, avatar_pixmap


def _circular(path: str, size: int) -> QPixmap | None:
    if not path or not Path(path).exists():
        return None
    src = QPixmap(path)
    if src.isNull():
        return None
    out = QPixmap(size, size)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    clip = QPainterPath()
    clip.addEllipse(0, 0, size, size)
    p.setClipPath(clip)
    p.drawPixmap(0, 0, src.scaled(
        size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation))
    p.end()
    return out


def _panel(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("panel")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(14, 12, 14, 14)
    lay.setSpacing(10)
    if title:
        head = QLabel(title)
        head.setObjectName("panelTitle")
        lay.addWidget(head)
    return frame, lay


def _instagram_panel(report, on_open, on_image) -> QFrame:
    frame, lay = _panel("")
    # header
    head = QHBoxLayout()
    ic = QLabel()
    ic.setPixmap(app_pixmap("instagram", 26))
    name = QLabel("Instagram")
    name.setStyleSheet("font-size:14px;font-weight:700;")
    head.addWidget(ic)
    head.addWidget(name)
    head.addStretch(1)
    heart = QLabel("♡   ✈   ⊕")
    heart.setStyleSheet(f"color:{theme.TEXT_DIM};font-size:14px;")
    head.addWidget(heart)
    lay.addLayout(head)

    # stories strip
    st = stories(report, "instagram")
    senders = [c["title"] for c in conversations(report, "instagram")]
    items = st or [{"title": s, "image": ""} for s in senders][:6]
    strip = QHBoxLayout()
    strip.setSpacing(10)
    for s in items[:6]:
        col = QVBoxLayout()
        col.setSpacing(2)
        av = QLabel()
        pix = _circular(s.get("image", ""), 50)
        av.setPixmap(pix if pix else avatar_pixmap(s.get("title", "?"), 50))
        av.setStyleSheet("border:2px solid #E1306C;border-radius:27px;")
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nm = QLabel(str(s.get("title", ""))[:8])
        nm.setStyleSheet(f"color:{theme.TEXT_DIM};font-size:10px;")
        nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(av, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(nm)
        h = QWidget()
        h.setLayout(col)
        strip.addWidget(h)
    strip.addStretch(1)
    lay.addLayout(strip)

    # featured post (first instagram image)
    post_img = None
    for s in st:
        if s.get("image"):
            post_img = s["image"]
            break
    photo = QLabel()
    photo.setMinimumHeight(150)
    photo.setStyleSheet(
        f"background:{theme.PANEL_ALT};border-radius:10px;")
    photo.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if post_img and Path(post_img).exists():
        pix = QPixmap(post_img)
        if not pix.isNull():
            photo.setPixmap(pix.scaledToWidth(
                300, Qt.TransformationMode.SmoothTransformation))
            photo.setCursor(Qt.CursorShape.PointingHandCursor)
            photo.mousePressEvent = lambda _e, p=post_img: on_image(p)
    else:
        photo.setText("📷")
    lay.addWidget(photo)
    loc = QLabel("📍 الدوحة، قطر    ·    ❤ 1,204    💬 89")
    loc.setObjectName("noteLabel")
    lay.addWidget(loc)
    lay.addStretch(1)

    frame.setCursor(Qt.CursorShape.PointingHandCursor)
    name.mousePressEvent = lambda _e: on_open("instagram")
    ic.mousePressEvent = lambda _e: on_open("instagram")
    return frame


def _whatsapp_panel(report, on_open) -> QFrame:
    frame = QFrame()
    frame.setObjectName("panel")
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    # green header with tabs
    header = QFrame()
    header.setStyleSheet(
        "background:#075E54;border-top-left-radius:12px;"
        "border-top-right-radius:12px;")
    hl = QVBoxLayout(header)
    hl.setContentsMargins(14, 10, 14, 0)
    top = QHBoxLayout()
    ic = QLabel()
    ic.setPixmap(app_pixmap("whatsapp", 24))
    title = QLabel("WhatsApp")
    title.setStyleSheet("color:white;font-size:14px;font-weight:700;")
    top.addWidget(ic)
    top.addWidget(title)
    top.addStretch(1)
    hl.addLayout(top)
    tabs = QHBoxLayout()
    for i, t in enumerate(("الدردشات", "الحالة", "المكالمات")):
        lb = QLabel(t)
        active = i == 0
        lb.setStyleSheet(
            f"color:{'white' if active else 'rgba(255,255,255,0.6)'};"
            f"padding:8px 4px;font-size:12px;"
            f"{'border-bottom:2px solid white;' if active else ''}")
        tabs.addWidget(lb)
    tabs.addStretch(1)
    hl.addLayout(tabs)
    outer.addWidget(header)

    body = QVBoxLayout()
    body.setContentsMargins(8, 6, 8, 10)
    body.setSpacing(2)
    convos = conversations(report, "whatsapp")
    for idx, conv in enumerate(convos[:6]):
        row = QHBoxLayout()
        row.setContentsMargins(6, 6, 6, 6)
        av = QLabel()
        av.setPixmap(avatar_pixmap(conv["title"], 40))
        col = QVBoxLayout()
        col.setSpacing(1)
        nm = QLabel(conv["title"])
        nm.setStyleSheet("font-weight:600;font-size:13px;")
        last = conv["messages"][-1] if conv["messages"] else {}
        preview = (last.get("text") or "🎤 رسالة صوتية") if last else ""
        pv = QLabel(str(preview)[:34])
        pv.setObjectName("noteLabel")
        col.addWidget(nm)
        col.addWidget(pv)
        meta = QVBoxLayout()
        meta.setSpacing(2)
        tm = QLabel(str(last.get("timestamp", ""))[11:16] if last else "")
        tm.setObjectName("noteLabel")
        tm.setAlignment(Qt.AlignmentFlag.AlignRight)
        unread = (idx + 1) % 3
        badge = QLabel(str(unread) if unread else "")
        if unread:
            badge.setStyleSheet(
                "background:#25D366;color:#0a0e1a;border-radius:9px;"
                "min-width:18px;max-width:18px;min-height:18px;"
                "max-height:18px;font-size:11px;font-weight:700;")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        meta.addWidget(tm)
        meta.addWidget(badge, 0, Qt.AlignmentFlag.AlignRight)
        row.addWidget(av)
        cw = QWidget()
        cw.setLayout(col)
        row.addWidget(cw, 1)
        mw = QWidget()
        mw.setLayout(meta)
        row.addWidget(mw)
        rw = QFrame()
        rw.setLayout(row)
        rw.setStyleSheet(
            f"QFrame:hover{{background:{theme.PANEL_ALT};border-radius:8px;}}")
        rw.setCursor(Qt.CursorShape.PointingHandCursor)
        rw.mousePressEvent = lambda _e: on_open("whatsapp")
        body.addWidget(rw)
    body.addStretch(1)
    outer.addLayout(body, 1)
    return frame


def _apps_panel(report, on_open) -> QFrame:
    frame, lay = _panel("التطبيقات المثبتة")
    grid = QGridLayout()
    grid.setSpacing(10)
    apps = chat_apps(report)
    for i, app in enumerate(apps):
        card = QFrame()
        card.setObjectName("appCard")
        card.setFixedHeight(96)
        brand = BRAND.get(app["key"], theme.ACCENT)
        card.setStyleSheet(
            f"QFrame#appCard{{background:{theme.PANEL_ALT};"
            f"border:1px solid {theme.BORDER};border-radius:14px;}}"
            f"QFrame#appCard:hover{{border:2px solid {brand};}}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(6, 10, 6, 8)
        cl.setSpacing(4)
        icon = QLabel()
        icon.setPixmap(app_pixmap(app["key"], 40))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nm = QLabel(app["name"])
        nm.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nm.setStyleSheet("font-size:11px;font-weight:600;")
        cl.addWidget(icon)
        cl.addWidget(nm)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda _e, k=app["key"]: on_open(k)
        grid.addWidget(card, i // 4, i % 4)
    grid.setColumnStretch(4, 1)
    holder = QWidget()
    holder.setLayout(grid)
    lay.addWidget(holder)
    lay.addStretch(1)
    return frame


def _contacts_panel(report) -> QFrame:
    frame, lay = _panel("جهات الاتصال")
    for c in _records(report, "contacts")[:8]:
        row = QHBoxLayout()
        av = QLabel()
        av.setPixmap(avatar_pixmap(c.get("name") or "?", 36))
        col = QVBoxLayout()
        col.setSpacing(0)
        nm = QLabel(c.get("name") or "—")
        nm.setStyleSheet("font-size:13px;font-weight:600;")
        ph = QLabel((c.get("phones") or [""])[0] if c.get("phones") else "")
        ph.setObjectName("noteLabel")
        col.addWidget(nm)
        col.addWidget(ph)
        row.addWidget(av)
        cw = QWidget()
        cw.setLayout(col)
        row.addWidget(cw, 1)
        rw = QWidget()
        rw.setLayout(row)
        lay.addWidget(rw)
    lay.addStretch(1)
    return frame


def _activity_panel(report) -> QFrame:
    frame, lay = _panel("إحصائيات النشاط")
    chart = BarChart(activity_by_source(report))
    lay.addWidget(chart)
    return frame


def _keyword_panel(report) -> QFrame:
    frame, lay = _panel("تحليل الكلمات المفتاحية")
    flow = QHBoxLayout()
    flow.setSpacing(8)
    kws = keywords(report)
    rows = QVBoxLayout()
    rows.setSpacing(8)
    line = QHBoxLayout()
    line.setSpacing(8)
    count = 0
    for word, freq in kws:
        tag = QLabel(f"{word}  {freq}")
        tag.setStyleSheet(
            f"background:rgba(34,211,238,0.12);color:{theme.ACCENT};"
            f"border:1px solid {theme.ACCENT_DIM};border-radius:14px;"
            f"padding:5px 12px;font-size:12px;")
        line.addWidget(tag)
        count += 1
        if count % 3 == 0:
            line.addStretch(1)
            w = QWidget()
            w.setLayout(line)
            rows.addWidget(w)
            line = QHBoxLayout()
            line.setSpacing(8)
    if line.count():
        line.addStretch(1)
        w = QWidget()
        w.setLayout(line)
        rows.addWidget(w)
    rows.addStretch(1)
    holder = QWidget()
    holder.setLayout(rows)
    lay.addWidget(holder)
    return frame


def build_dashboard(report, on_open_app, on_open_image) -> QWidget:
    """Return a scrollable Overview dashboard widget."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet("background:transparent;border:none;")

    inner = QWidget()
    grid = QGridLayout(inner)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setSpacing(14)
    grid.addWidget(_instagram_panel(report, on_open_app, on_open_image), 0, 0)
    grid.addWidget(_whatsapp_panel(report, on_open_app), 0, 1)
    grid.addWidget(_apps_panel(report, on_open_app), 1, 0)
    grid.addWidget(_contacts_panel(report), 1, 1)
    grid.addWidget(_activity_panel(report), 2, 0)
    grid.addWidget(_keyword_panel(report), 2, 1)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    scroll.setWidget(inner)
    return scroll
