"""
Evidence offload: dump the actual photos and chat conversations out of a
backup/extraction into a browsable folder tree.

Analysis produces a report *describing* what's on the device; this module
*offloads* the evidence itself — copying the real image files (with an EXIF/GPS
index) and rendering every conversation as a self-contained, app-themed HTML
page plus a CSV. Everything is read-only against the source; we only ever copy
out, never write back to the evidence.

Qt-free on purpose (only depends on the analysis report + the Qt-free
datasource), so the CLI and the API server can both call it.
"""

from __future__ import annotations

import csv
import html
import json
import re
import shutil
from pathlib import Path

from .gui import datasource as ds

# Per-app bubble palette, mirroring the GUI clones (gui/chatview.py APP_THEMES)
# and the React appThemes.ts. Kept here as a plain dict so this module stays
# free of any Qt / frontend dependency.
_APP_COLORS: dict[str, tuple[str, str, str, str]] = {
    # key: (header, sent_bubble, recv_bubble, chat_bg)
    "whatsapp": ("#202c33", "#005c4b", "#202c33", "#0b141a"),
    "messages": ("#1c1c1e", "#0b84ff", "#26282b", "#000000"),
    "telegram": ("#17212b", "#2b5278", "#182533", "#0e1621"),
    "instagram": ("#262626", "#3797f0", "#262626", "#000000"),
    "discord": ("#1e1f22", "#5865f2", "#2b2d31", "#313338"),
    "snapchat": ("#222222", "#0fadff", "#2a2a2a", "#1b1b1b"),
    "signal": ("#1b1b1b", "#2c6bed", "#2a2a2a", "#121212"),
    "messenger": ("#000000", "#0084ff", "#303030", "#0b0b0b"),
    "tiktok": ("#121212", "#fe2c55", "#1f1f1f", "#101010"),
    "viber": ("#1f1a2e", "#7360f2", "#2a2440", "#16121f"),
    "line": ("#1c1c1c", "#06c755", "#2a2a2a", "#101010"),
    "kik": ("#1f2933", "#82bc23", "#2b2b2b", "#111417"),
    "wechat": ("#111111", "#07c160", "#2c2c2c", "#101010"),
    "threema": ("#0f1b14", "#2c7d40", "#23282b", "#0c1410"),
}
_DEFAULT_COLORS = ("#0D1724", "#1d6f70", "#112132", "#050B12")

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(text: str, fallback: str = "item") -> str:
    s = _SAFE.sub("_", str(text or "")).strip("_")
    return s[:80] or fallback


def _unique(dest_dir: Path, name: str) -> Path:
    """Return a non-colliding path inside *dest_dir* for *name*."""
    target = dest_dir / name
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    i = 1
    while True:
        cand = dest_dir / f"{stem}_{i}{suffix}"
        if not cand.exists():
            return cand
        i += 1


# --------------------------------------------------------------------- media
def export_media(report: dict, dest: str | Path) -> dict:
    """Copy every recovered photo into ``<dest>/media`` + write an EXIF index."""
    dest = Path(dest)
    media_dir = dest / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    photos = (report.get("artifacts", {}).get("photos", {}) or {})
    records = photos.get("records", []) or []

    index_rows: list[list[str]] = []
    copied = with_gps = 0
    for rec in records:
        src = rec.get("stored_at")
        if not src or not Path(src).is_file():
            continue
        base = _slug(Path(rec.get("relative_path") or src).name, "photo")
        out = _unique(media_dir, base)
        try:
            shutil.copy2(src, out)
        except OSError:
            continue
        copied += 1
        exif = rec.get("exif", {}) or {}
        lat = exif.get("gps_latitude")
        lon = exif.get("gps_longitude")
        if lat is not None and lon is not None:
            with_gps += 1
        index_rows.append([
            rec.get("relative_path", ""),
            out.name,
            str(exif.get("DateTimeOriginal") or exif.get("DateTime") or ""),
            str(exif.get("Make") or ""),
            str(exif.get("Model") or ""),
            "" if lat is None else str(lat),
            "" if lon is None else str(lon),
        ])

    with (dest / "media_index.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["original_path", "exported_as", "taken", "make", "model",
                    "gps_lat", "gps_lon"])
        w.writerows(index_rows)

    return {"count": copied, "with_gps": with_gps, "dir": str(media_dir)}


def export_videos(report: dict, dest: str | Path) -> dict:
    """Copy every recovered video into ``<dest>/videos`` + write an index."""
    dest = Path(dest)
    vid_dir = dest / "videos"
    vid_dir.mkdir(parents=True, exist_ok=True)

    videos = (report.get("artifacts", {}).get("videos", {}) or {})
    records = videos.get("records", []) or []

    index_rows: list[list[str]] = []
    copied = 0
    for rec in records:
        src = rec.get("stored_at")
        if not src or not Path(src).is_file():
            continue
        base = _slug(Path(rec.get("relative_path") or src).name, "video")
        out = _unique(vid_dir, base)
        try:
            shutil.copy2(src, out)
        except OSError:
            continue
        copied += 1
        size = rec.get("size_bytes")
        index_rows.append([
            rec.get("relative_path", ""), out.name,
            "" if size is None else str(size),
        ])

    with (dest / "video_index.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["original_path", "exported_as", "size_bytes"])
        w.writerows(index_rows)

    return {"count": copied, "dir": str(vid_dir)}


# ------------------------------------------------------------- conversations
def _bubble_html(m: dict, sent_c: str, recv_c: str) -> str:
    mine = bool(m.get("from_me"))
    color = sent_c if mine else recv_c
    align = "flex-start" if mine else "flex-end"
    parts: list[str] = []
    if m.get("text"):
        parts.append(html.escape(str(m["text"])).replace("\n", "<br>"))
    if m.get("image"):
        parts.append('<i>📎 media attachment</i>')
    lat, lon = m.get("lat"), m.get("lon")
    if lat is not None and lon is not None:
        parts.append(
            f'<a href="https://www.openstreetmap.org/?mlat={lat}&mlon={lon}" '
            f'style="color:#ffd479">📍 {lat:.4f}, {lon:.4f}</a>'
        )
    ts = html.escape(str(m.get("timestamp") or "").replace("T", " ")[:19])
    body = "<br>".join(parts) if parts else "<i>(empty)</i>"
    return (
        f'<div style="align-self:{align};max-width:72%;background:{color};'
        f'color:#fff;border-radius:14px;padding:8px 12px;margin:3px 0;'
        f'font-size:13px;word-break:break-word">{body}'
        f'<div style="font-size:9px;opacity:.6;margin-top:3px">{ts}</div></div>'
    )


def _app_page_html(app_name: str, convos: list[dict], colors) -> str:
    header, sent_c, recv_c, bg = colors
    blocks = []
    for c in convos:
        bubbles = "".join(_bubble_html(m, sent_c, recv_c)
                          for m in c.get("messages", []))
        blocks.append(
            f'<section style="margin:0 0 26px">'
            f'<h2 style="background:{header};color:#fff;padding:8px 12px;'
            f'border-radius:8px;font-size:15px">{html.escape(c.get("title","")) }'
            f' <span style="opacity:.6;font-size:12px">'
            f'({len(c.get("messages", []))})</span></h2>'
            f'<div style="display:flex;flex-direction:column;padding:8px">'
            f'{bubbles}</div></section>'
        )
    return (
        f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">'
        f'<title>{html.escape(app_name)}</title></head>'
        f'<body style="background:{bg};font-family:Segoe UI,Arial,sans-serif;'
        f'margin:0;padding:18px">'
        f'<h1 style="color:#4FE3E0">{html.escape(app_name)}</h1>'
        f'{"".join(blocks) or "<p style=color:#889>No conversations.</p>"}'
        f'</body></html>'
    )


def export_conversations(report: dict, dest: str | Path) -> dict:
    """Render every chat app's threads to ``<dest>/conversations`` (HTML + CSV)."""
    dest = Path(dest)
    conv_dir = dest / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)

    apps_done: list[dict] = []
    total_msgs = 0
    csv_rows: list[list[str]] = []

    for app in ds.chat_apps(report):
        key, name = app["key"], app["name"]
        convos = ds.conversations(report, key)
        if not convos:
            continue
        colors = _APP_COLORS.get(key, _DEFAULT_COLORS)
        (conv_dir / f"{_slug(key, key)}.html").write_text(
            _app_page_html(name, convos, colors), encoding="utf-8")
        msgs = sum(len(c.get("messages", [])) for c in convos)
        total_msgs += msgs
        apps_done.append({"key": key, "name": name,
                          "threads": len(convos), "messages": msgs})
        for c in convos:
            for m in c.get("messages", []):
                csv_rows.append([
                    name, c.get("title", ""),
                    "sent" if m.get("from_me") else "received",
                    str(m.get("timestamp") or ""),
                    str(m.get("text") or ""),
                    "yes" if m.get("image") else "",
                    "" if m.get("lat") is None else str(m.get("lat")),
                    "" if m.get("lon") is None else str(m.get("lon")),
                ])

    with (dest / "conversations.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["app", "thread", "direction", "timestamp", "text",
                    "has_media", "lat", "lon"])
        w.writerows(csv_rows)

    # An index linking every app page.
    links = "".join(
        f'<li><a href="conversations/{_slug(a["key"], a["key"])}.html">'
        f'{html.escape(a["name"])}</a> — {a["threads"]} threads, '
        f'{a["messages"]} messages</li>'
        for a in apps_done
    )
    (dest / "conversations.html").write_text(
        f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">'
        f'<title>Conversations</title></head><body '
        f'style="background:#050B12;color:#e6f1ff;font-family:Segoe UI,Arial">'
        f'<h1 style="color:#4FE3E0">Conversations</h1><ul>{links or "<li>none</li>"}'
        f'</ul></body></html>', encoding="utf-8")

    return {"apps": apps_done, "messages": total_msgs, "dir": str(conv_dir)}


# ----------------------------------------------------------------- orchestrate
def export_all(report: dict, dest: str | Path) -> dict:
    """Offload both media and conversations; write a manifest.json."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    media = export_media(report, dest)
    videos = export_videos(report, dest)
    convos = export_conversations(report, dest)
    manifest = {
        "tool": report.get("meta", {}).get("tool", "phonexe"),
        "device": report.get("device", {}),
        "media": media,
        "videos": videos,
        "conversations": convos,
    }
    (dest / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    return manifest


# ------------------------------------------------------------------ selection
def _photo_records(report: dict) -> list[dict]:
    return (report.get("artifacts", {}).get("photos", {}) or {}).get("records", []) or []


def _video_records(report: dict) -> list[dict]:
    return (report.get("artifacts", {}).get("videos", {}) or {}).get("records", []) or []


def _matches(rec: dict, selection) -> bool:
    """True if *rec* is named by *selection* (by relative_path or basename)."""
    rp = rec.get("relative_path") or ""
    return rp in selection or Path(rp).name in selection


def export_selection(report: dict, dest: str | Path, *,
                     photos=None, videos=None) -> dict:
    """Build a report containing ONLY the selected photos/videos.

    *photos* / *videos* are iterables of identifiers (each item's
    ``relative_path`` or just its file name). Only matching items are copied
    out and listed in ``selected_report.html`` — the evidentiary subset the
    examiner chose, nothing else.
    """
    dest = Path(dest)
    media_dir = dest / "selected_media"
    vid_dir = dest / "selected_videos"
    media_dir.mkdir(parents=True, exist_ok=True)
    vid_dir.mkdir(parents=True, exist_ok=True)

    photos = set(photos or [])
    videos = set(videos or [])
    chosen_photos: list[dict] = []
    chosen_videos: list[dict] = []

    for rec in _photo_records(report):
        if not _matches(rec, photos):
            continue
        src = rec.get("stored_at")
        if not src or not Path(src).is_file():
            continue
        out = _unique(media_dir, _slug(Path(rec.get("relative_path") or src).name,
                                       "photo"))
        try:
            shutil.copy2(src, out)
        except OSError:
            continue
        exif = rec.get("exif", {}) or {}
        chosen_photos.append({
            "relative_path": rec.get("relative_path", ""),
            "exported_as": out.name,
            "lat": exif.get("gps_latitude"),
            "lon": exif.get("gps_longitude"),
            "taken": exif.get("DateTimeOriginal") or exif.get("DateTime"),
        })

    for rec in _video_records(report):
        if not _matches(rec, videos):
            continue
        src = rec.get("stored_at")
        if not src or not Path(src).is_file():
            continue
        out = _unique(vid_dir, _slug(Path(rec.get("relative_path") or src).name,
                                     "video"))
        try:
            shutil.copy2(src, out)
        except OSError:
            continue
        chosen_videos.append({
            "relative_path": rec.get("relative_path", ""),
            "exported_as": out.name,
            "size_bytes": rec.get("size_bytes"),
        })

    _write_selection_report(dest, report, chosen_photos, chosen_videos)
    summary = {
        "photos": len(chosen_photos),
        "videos": len(chosen_videos),
        "report": str(dest / "selected_report.html"),
    }
    (dest / "selection.json").write_text(
        json.dumps({"device": report.get("device", {}),
                    "photos": chosen_photos, "videos": chosen_videos},
                   ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    return summary


def _write_selection_report(dest: Path, report: dict,
                            photos: list[dict], videos: list[dict]) -> None:
    dev = report.get("device", {}) or {}
    dev_name = html.escape(str(dev.get("device_name")
                               or dev.get("name") or "Device"))

    def gps_link(p):
        if p.get("lat") is not None and p.get("lon") is not None:
            return (f'<a href="https://www.openstreetmap.org/?mlat={p["lat"]}'
                    f'&mlon={p["lon"]}" style="color:#ffd479">📍 GPS</a>')
        return ""

    photo_cards = "".join(
        f'<figure style="margin:0;background:#0D1724;border:1px solid #14304A;'
        f'border-radius:10px;padding:8px;width:200px">'
        f'<img src="selected_media/{html.escape(p["exported_as"])}" '
        f'style="width:100%;height:140px;object-fit:cover;border-radius:6px">'
        f'<figcaption style="font-size:11px;color:#bcd;margin-top:6px">'
        f'{html.escape(p["relative_path"])}<br>'
        f'{html.escape(str(p.get("taken") or ""))} {gps_link(p)}</figcaption>'
        f'</figure>'
        for p in photos
    )
    video_rows = "".join(
        f'<li><a href="selected_videos/{html.escape(v["exported_as"])}" '
        f'style="color:#4FE3E0">{html.escape(v["relative_path"])}</a></li>'
        for v in videos
    )
    (dest / "selected_report.html").write_text(
        f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">'
        f'<title>تقرير الأدلة المحددة</title></head>'
        f'<body style="background:#050B12;color:#e6f1ff;'
        f'font-family:Segoe UI,Arial;margin:0;padding:22px">'
        f'<h1 style="color:#4FE3E0">تقرير الأدلة المحددة</h1>'
        f'<p style="color:#90A6BC">الجهاز: {dev_name} · '
        f'الصور: {len(photos)} · الفيديو: {len(videos)}</p>'
        f'<h2 style="color:#24A8FF">الصور المحددة</h2>'
        f'<div style="display:flex;flex-wrap:wrap;gap:12px">'
        f'{photo_cards or "<p style=color:#889>لا توجد صور محددة.</p>"}</div>'
        f'<h2 style="color:#24A8FF;margin-top:24px">الفيديوهات المحددة</h2>'
        f'<ul>{video_rows or "<li style=color:#889>لا توجد فيديوهات محددة.</li>"}'
        f'</ul></body></html>', encoding="utf-8")
