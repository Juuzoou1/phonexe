"""
Adapts a phonexe report dict into the shapes the GUI renders:
overview stat cards, device-info fields, and per-section tables.
"""

from __future__ import annotations

from .i18n import tr


def _art(report: dict, key: str) -> dict:
    return (report.get("artifacts") or {}).get(key, {}) or {}


def _records(report: dict, key: str) -> list[dict]:
    return _art(report, key).get("records", []) or []


def _count(report: dict, key: str) -> int:
    return int(_art(report, key).get("count", 0) or 0)


def _social_total(report: dict) -> int:
    return _count(report, "social_apps")


def _social_app_count(report: dict) -> int:
    apps = _art(report, "social_apps").get("apps", {}) or {}
    n = len(apps)
    if _count(report, "whatsapp") > 0:
        n += 1
    return n


def overview_stats(report: dict) -> list[tuple[str, int]]:
    """Return (label_key, value) pairs for the six stat cards."""
    messages = _count(report, "messages") + _count(report, "whatsapp") + _social_total(report)
    files = sum(
        _count(report, k)
        for k in ("contacts", "messages", "calls", "safari_history",
                  "whatsapp", "social_apps", "photos")
    )
    return [
        ("stat_apps", _social_app_count(report)),
        ("stat_messages", messages),
        ("stat_photos", _count(report, "photos")),
        ("stat_videos", 0),
        ("stat_files", files),
        ("stat_deleted", _count(report, "deleted")),
    ]


def device_summary(report: dict) -> dict:
    """Short device descriptor for the connected-device card."""
    d = report.get("device", {}) or {}
    platform = (report.get("meta", {}) or {}).get("platform", "")
    if platform == "ios":
        name = d.get("device_name") or d.get("product_type") or "iOS device"
        os_ = f"iOS {d.get('product_version', '')}".strip()
        ident = d.get("unique_identifier") or d.get("serial_number") or ""
    else:
        name = " ".join(
            x for x in (d.get("manufacturer"), d.get("model")) if x
        ) or "Android device"
        os_ = f"Android {d.get('android_version', '')}".strip()
        ident = d.get("serial") or ""
    return {"name": name, "os": os_, "ident": ident}


def device_fields(report: dict) -> list[tuple[str, str]]:
    """(label_key, value) rows for the device-info panel."""
    d = report.get("device", {}) or {}
    platform = (report.get("meta", {}) or {}).get("platform", "")
    rows: list[tuple[str, str]] = []

    def add(key, val):
        if val:
            rows.append((key, str(val)))

    if platform == "ios":
        add("f_name", d.get("device_name"))
        add("f_model", d.get("product_type"))
        add("f_os", f"iOS {d.get('product_version', '')}".strip())
        add("f_serial", d.get("serial_number"))
        add("f_imei", d.get("imei"))
        add("f_phone", d.get("phone_number"))
        rows.append(("f_encryption", tr("f_enc_off")))
    else:
        add("f_name", d.get("model"))
        add("f_model", f"{d.get('manufacturer', '')} {d.get('model', '')}".strip())
        add("f_os", f"Android {d.get('android_version', '')}".strip())
        add("f_serial", d.get("serial"))
    return rows


# ---------------------------------------------------------------- tables

def _to_table(records: list[dict], preferred: list[str] | None = None
              ) -> tuple[list[str], list[list[str]]]:
    """Turn a list of dicts into (columns, rows)."""
    if not records:
        return [], []
    cols: list[str] = list(preferred) if preferred else []
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    rows = []
    for r in records:
        rows.append(["" if r.get(c) is None else str(r.get(c, "")) for c in cols])
    return cols, rows


def _chat_records(report: dict) -> list[dict]:
    """Merge SMS/iMessage, WhatsApp and social messages into one stream."""
    out: list[dict] = []
    for r in _records(report, "messages"):
        out.append({
            "source": r.get("service") or "SMS",
            "timestamp": r.get("timestamp"),
            "direction": r.get("direction"),
            "counterpart": r.get("counterpart") or r.get("chat") or r.get("address"),
            "text": r.get("text"),
        })
    for r in _records(report, "whatsapp"):
        out.append({
            "source": "WhatsApp",
            "timestamp": r.get("timestamp"),
            "direction": r.get("direction"),
            "counterpart": r.get("partner") or r.get("chat"),
            "text": r.get("text"),
        })
    apps = _art(report, "social_apps").get("apps", {}) or {}
    for app in apps.values():
        for db in app.get("databases", []):
            for t in db.get("tables", []):
                for rec in t.get("records", []):
                    text = rec.get("text") or rec.get("body") or rec.get("content")
                    out.append({
                        "source": app.get("name"),
                        "timestamp": rec.get("timestamp") or rec.get("date"),
                        "direction": "",
                        "counterpart": rec.get("sender") or rec.get("user_id") or "",
                        "text": text,
                    })
    return out


def _app_inventory(report: dict) -> list[dict]:
    rows = []
    if _count(report, "whatsapp") > 0:
        rows.append({"app": "WhatsApp", "messages": _count(report, "whatsapp")})
    apps = _art(report, "social_apps").get("apps", {}) or {}
    for app in apps.values():
        total = sum(
            t.get("count", 0)
            for db in app.get("databases", [])
            for t in db.get("tables", [])
        )
        rows.append({"app": app.get("name"), "messages": total})
    return rows


def _location_records(report: dict) -> list[dict]:
    rows = []
    for r in _records(report, "photos"):
        exif = r.get("exif") or {}
        if "gps_latitude" in exif and "gps_longitude" in exif:
            rows.append({
                "latitude": exif["gps_latitude"],
                "longitude": exif["gps_longitude"],
                "timestamp": exif.get("DateTimeOriginal"),
                "source": r.get("relative_path"),
            })
    return rows


def _photo_records(report: dict) -> list[dict]:
    rows = []
    for r in _records(report, "photos"):
        exif = r.get("exif") or {}
        rows.append({
            "path": r.get("relative_path"),
            "taken": exif.get("DateTimeOriginal"),
            "make": exif.get("Make"),
            "model": exif.get("Model"),
            "gps": "yes" if "gps_latitude" in exif else "",
        })
    return rows


def _pick(rec: dict, *names, default=None):
    for n in names:
        if n in rec and rec[n] not in (None, ""):
            return rec[n]
    return default


def _msg_from_record(rec: dict) -> dict:
    """Normalize an arbitrary app message row into a chat message dict."""
    direction = _pick(rec, "direction")
    from_me = False
    if direction is not None:
        from_me = str(direction).lower() == "sent"
    else:
        fm = _pick(rec, "from_me", "is_from_me", "key_from_me")
        from_me = bool(fm) if fm is not None else False
    lat = _pick(rec, "latitude", "lat", "gps_latitude")
    lon = _pick(rec, "longitude", "lon", "gps_longitude")
    ts = _pick(rec, "timestamp", "date", "time")
    if _is_num(ts):
        from ..timeutil import unix_to_iso
        v = float(ts)
        ts = unix_to_iso(v, millis=v > 1e12) or unix_to_iso(v) or str(ts)
    return {
        "from_me": from_me,
        "text": _pick(rec, "text", "body", "content", "data", "caption"),
        "timestamp": ts,
        "sender": _pick(rec, "sender", "user_id", "from", "partner"),
        "image": _pick(rec, "image", "media", "media_path"),
        "lat": float(lat) if _is_num(lat) else None,
        "lon": float(lon) if _is_num(lon) else None,
    }


def _is_num(v) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def _group(records, key_fn, default_title):
    convos: dict[str, list] = {}
    for rec in records:
        title = key_fn(rec) or default_title
        convos.setdefault(str(title), []).append(_msg_from_record(rec))
    return [{"title": t, "messages": m} for t, m in convos.items()]


def chat_apps(report: dict) -> list[dict]:
    """List apps that have viewable conversations, in display order."""
    apps = []
    if _count(report, "messages") > 0:
        apps.append({"key": "messages", "name": "Messages"})
    if _count(report, "whatsapp") > 0:
        apps.append({"key": "whatsapp", "name": "WhatsApp"})
    social = _art(report, "social_apps").get("apps", {}) or {}
    for key, app in social.items():
        apps.append({"key": key, "name": app.get("name", key.title())})
    return apps


_IG_THREAD_KEYS = ("thread_id", "thread_key", "conversation_id",
                   "conversation_pk", "chat_id", "thread_pk")
_IG_NAME_KEYS = ("thread_title", "title", "participants", "username",
                 "sender", "user_id", "user_name")


def _instagram_conversations(records: list[dict]) -> list[dict]:
    """Dedicated Instagram DM grouping.

    Groups messages by their thread/conversation id when present (so a real
    Instagram Direct database splits into the correct threads), names each
    thread by its title/participants, and links any media column. Falls back
    to grouping by sender when no thread id exists.
    """
    def thread_key(r: dict):
        for k in _IG_THREAD_KEYS:
            if r.get(k) not in (None, ""):
                return str(r[k])
        return None

    def thread_name(r: dict):
        for k in _IG_NAME_KEYS:
            v = r.get(k)
            if v not in (None, ""):
                return str(v)
        return "Instagram"

    grouped: dict[str, dict] = {}
    for r in records:
        key = thread_key(r) or thread_name(r)
        bucket = grouped.setdefault(
            key, {"title": thread_name(r), "messages": []})
        # prefer a human title over a numeric thread id
        if bucket["title"] in (key, "Instagram"):
            bucket["title"] = thread_name(r)
        bucket["messages"].append(_msg_from_record(r))

    convos = list(grouped.values())
    for c in convos:
        c["messages"].sort(key=lambda m: str(m.get("timestamp") or ""))
    return convos


def conversations(report: dict, app_key: str) -> list[dict]:
    """Build per-conversation message threads for *app_key*."""
    if app_key == "messages":
        return _group(
            _records(report, "messages"),
            lambda r: r.get("chat") or r.get("counterpart"),
            "Unknown",
        )
    if app_key == "whatsapp":
        return _group(
            _records(report, "whatsapp"),
            lambda r: r.get("partner") or r.get("from") or r.get("to"),
            "WhatsApp",
        )
    # social app: flatten its tables
    app = (_art(report, "social_apps").get("apps", {}) or {}).get(app_key, {})
    recs = [
        rec
        for db in app.get("databases", [])
        for t in db.get("tables", [])
        for rec in t.get("records", [])
    ]
    if app_key == "instagram":
        return _instagram_conversations(recs)
    return _group(recs, lambda r: r.get("sender") or r.get("user_id"),
                  app.get("name", app_key.title()))


def location_markers(report: dict) -> list[dict]:
    """All geolocation points (photos GPS + in-chat locations)."""
    markers = []
    for r in _location_records(report):
        markers.append({
            "lat": r["latitude"], "lon": r["longitude"],
            "label": (r.get("source") or "")[-24:],
        })
    # in-chat locations (whatsapp + social)
    for app in chat_apps(report):
        for conv in conversations(report, app["key"]):
            for m in conv["messages"]:
                if m.get("lat") is not None and m.get("lon") is not None:
                    markers.append({
                        "lat": m["lat"], "lon": m["lon"],
                        "label": f"{app['name']}: {conv['title']}"[:28],
                    })
    return markers


def _ts_key(value) -> str:
    """Best-effort sort key: ISO strings sort directly; epochs are converted."""
    if value is None:
        return ""
    if _is_num(value):
        from ..timeutil import unix_to_iso
        v = float(value)
        iso = unix_to_iso(v, millis=v > 1e12) or unix_to_iso(v)
        return iso or ""
    return str(value)


def timeline(report: dict) -> list[dict]:
    """Aggregate every dated event into one chronologically sorted stream."""
    events: list[dict] = []

    def add(ts, etype, source, detail):
        events.append({
            "timestamp": _ts_key(ts) or (str(ts) if ts else ""),
            "type": etype, "source": source,
            "detail": (detail or "")[:120],
        })

    for r in _records(report, "messages"):
        add(r.get("timestamp"), "Message", r.get("service") or "SMS",
            f"{r.get('counterpart','')}: {r.get('text','')}")
    for r in _records(report, "whatsapp"):
        add(r.get("timestamp"), "Message", "WhatsApp",
            f"{r.get('partner','')}: {r.get('text','')}")
    for r in _records(report, "calls"):
        add(r.get("timestamp"), "Call", r.get("provider") or "Phone",
            f"{r.get('direction','')} {r.get('number','')}")
    for r in _records(report, "safari_history"):
        add(r.get("timestamp"), "Web", "Safari",
            f"{r.get('title','')} {r.get('url','')}")
    for r in _records(report, "chrome_history"):
        add(r.get("timestamp"), "Web", "Chrome",
            f"{r.get('title','')} {r.get('url','')}")
    for r in _records(report, "photos"):
        exif = r.get("exif") or {}
        if exif.get("DateTimeOriginal"):
            add(exif.get("DateTimeOriginal"), "Photo", "Camera",
                r.get("relative_path"))
    apps = _art(report, "social_apps").get("apps", {}) or {}
    for app in apps.values():
        for db in app.get("databases", []):
            for t in db.get("tables", []):
                for rec in t.get("records", []):
                    m = _msg_from_record(rec)
                    if m["timestamp"]:
                        add(m["timestamp"], "Message", app.get("name"),
                            f"{m.get('sender') or ''}: {m.get('text') or ''}")
    events.sort(key=lambda e: e["timestamp"])
    return events


def instagram_posts(report: dict) -> list[dict]:
    """Feed posts for the Instagram view: shared images + device photos."""
    posts = []
    for conv in conversations(report, "instagram"):
        for m in conv["messages"]:
            if m.get("image"):
                posts.append({
                    "username": m.get("sender") or conv["title"],
                    "image": m["image"],
                    "caption": m.get("text"),
                    "time": m.get("timestamp"),
                    "likes": 1204,
                })
    for r in _records(report, "photos"):
        if r.get("stored_at"):
            posts.append({
                "username": "camera",
                "image": r["stored_at"],
                "caption": None,
                "time": (r.get("exif") or {}).get("DateTimeOriginal"),
                "likes": 0,
            })
    return posts


def stories(report: dict, app_key: str) -> list[dict]:
    """Image highlights ('stories') for an app: its in-chat media items."""
    out = []
    for conv in conversations(report, app_key):
        for m in conv["messages"]:
            if m.get("image"):
                out.append({"title": m.get("sender") or conv["title"],
                            "image": m["image"]})
    return out


_STOPWORDS = {
    "the", "and", "you", "for", "this", "that", "with", "have", "are", "was",
    "في", "من", "على", "الى", "إلى", "عن", "مع", "هذا", "هذه", "اللي", "وش",
    "يا", "ما", "لا", "ان", "أن", "هو", "هي", "كان", "تم", "الذي",
}


def keywords(report: dict, top: int = 12) -> list[tuple[str, int]]:
    """Most frequent meaningful words across all message text."""
    import re
    from collections import Counter

    counter: Counter = Counter()
    texts: list[str] = []
    for app in chat_apps(report):
        for conv in conversations(report, app["key"]):
            for m in conv["messages"]:
                if m.get("text"):
                    texts.append(str(m["text"]))
    for t in texts:
        for w in re.findall(r"[^\W\d_]{3,}", t, flags=re.UNICODE):
            wl = w.lower()
            if wl not in _STOPWORDS:
                counter[w] += 1
    return counter.most_common(top)


def activity_by_source(report: dict) -> list[tuple[str, int]]:
    """Message volume per source/app, for the activity bar chart."""
    out: list[tuple[str, int]] = []
    n = _count(report, "messages")
    if n:
        out.append(("SMS/iMessage", n))
    if _count(report, "whatsapp"):
        out.append(("WhatsApp", _count(report, "whatsapp")))
    apps = _art(report, "social_apps").get("apps", {}) or {}
    for app in apps.values():
        total = sum(
            t.get("count", 0)
            for db in app.get("databases", [])
            for t in db.get("tables", [])
        )
        if total:
            out.append((app.get("name", "App"), total))
    return out


_SEARCH_SECTIONS = [
    "sec_messages", "sec_calls", "sec_contacts", "sec_media",
    "sec_browser", "sec_calendar", "sec_notes", "sec_files",
    "sec_accounts", "sec_deleted",
]


def global_search(report: dict, query: str, limit: int = 500) -> list[dict]:
    """Search every section's rows for *query*; return match rows."""
    q = (query or "").strip().lower()
    if not q:
        return []
    from .i18n import tr
    results: list[dict] = []
    for sec in _SEARCH_SECTIONS:
        cols, rows, _ = section_table(report, sec)
        label = tr(sec)
        for row in rows:
            joined = "  ·  ".join(c for c in row if c)
            if q in joined.lower():
                results.append({"section": label, "match": joined[:160]})
                if len(results) >= limit:
                    return results
    return results


def link_analysis(report: dict) -> list[dict]:
    """Communication graph: who the device owner interacted with, ranked."""
    from collections import Counter
    edges: Counter = Counter()
    for app in chat_apps(report):
        name = app["name"]
        for conv in conversations(report, app["key"]):
            edges[(conv["title"] or "?", name)] += len(conv["messages"])
    for c in _records(report, "calls"):
        if c.get("number"):
            edges[(c["number"], "Calls")] += 1
    rows = [{"counterpart": k[0], "app": k[1], "interactions": v}
            for k, v in edges.items()]
    rows.sort(key=lambda r: -r["interactions"])
    return rows


def unified_contacts(report: dict) -> list[dict]:
    """Merge identities across contacts, chat apps and calls.

    Groups by a normalized name (with a contains-match pass so e.g. a chat
    titled "Sara" folds into the contact "Sara Ahmed"), tracking every app the
    identity appears in and total interactions.
    """
    identities: dict[str, dict] = {}

    def get(name: str) -> dict:
        key = name.lower().strip()
        # fold into an existing identity if one name contains the other
        for k, v in identities.items():
            if key and (key in k or k in key):
                return v
        return identities.setdefault(
            key, {"name": name, "phones": set(), "emails": set(),
                  "apps": set(), "interactions": 0})

    for c in _records(report, "contacts"):
        name = c.get("name") or ((c.get("phones") or [""])[0])
        if not name:
            continue
        idt = get(name)
        if len(name) > len(idt["name"]):
            idt["name"] = name        # prefer the fuller name
        for p in c.get("phones", []) or []:
            idt["phones"].add(p)
        for e in c.get("emails", []) or []:
            idt["emails"].add(e)
        idt["apps"].add("Contacts")

    for app in chat_apps(report):
        for conv in conversations(report, app["key"]):
            if conv["title"]:
                idt = get(conv["title"])
                idt["apps"].add(app["name"])
                idt["interactions"] += len(conv["messages"])

    for c in _records(report, "calls"):
        if c.get("number"):
            idt = get(c["number"])
            idt["apps"].add("Calls")
            idt["interactions"] += 1

    out = [{
        "identity": v["name"],
        "phones": ", ".join(sorted(v["phones"])),
        "apps": ", ".join(sorted(v["apps"])),
        "interactions": v["interactions"],
    } for v in identities.values()]
    out.sort(key=lambda x: -x["interactions"])
    return out


def section_table(report: dict, section: str
                  ) -> tuple[list[str], list[list[str]], str]:
    """Return (columns, rows, note) for a sidebar section."""
    note = ""
    if section == "sec_messages":
        cols, rows = _to_table(
            _chat_records(report),
            ["source", "timestamp", "direction", "counterpart", "text"],
        )
    elif section == "sec_apps":
        cols, rows = _to_table(_app_inventory(report), ["app", "messages"])
    elif section == "sec_calls":
        cols, rows = _to_table(_records(report, "calls"))
    elif section == "sec_contacts":
        cols, rows = _to_table(_records(report, "contacts"))
    elif section == "sec_media":
        cols, rows = _to_table(_photo_records(report),
                               ["path", "taken", "make", "model", "gps"])
    elif section == "sec_location":
        cols, rows = _to_table(_location_records(report),
                               ["latitude", "longitude", "timestamp", "source"])
    elif section == "sec_browser":
        merged = []
        for r in _records(report, "safari_history"):
            merged.append({"browser": "Safari", "url": r.get("url"),
                           "title": r.get("title"),
                           "timestamp": r.get("timestamp")})
        for r in _records(report, "chrome_history"):
            merged.append({"browser": "Chrome", "url": r.get("url"),
                           "title": r.get("title"),
                           "timestamp": r.get("timestamp")})
        cols, rows = _to_table(merged,
                               ["browser", "title", "url", "timestamp"])
    elif section == "sec_accounts":
        emails = []
        for c in _records(report, "contacts"):
            for e in c.get("emails", []) or []:
                emails.append({"account": e, "type": "email", "source": "contacts"})
        cols, rows = _to_table(emails, ["account", "type", "source"])
        note = tr("accounts_note")
    elif section == "sec_deleted":
        cols, rows = _to_table(_records(report, "deleted"),
                               ["source", "page", "text"])
        note = tr("deleted_note")
    elif section == "sec_timeline":
        cols, rows = _to_table(timeline(report),
                               ["timestamp", "type", "source", "detail"])
    elif section == "sec_calendar":
        cols, rows = _to_table(_records(report, "calendar"),
                               ["title", "start", "end", "location"])
    elif section == "sec_notes":
        cols, rows = _to_table(_records(report, "notes"), ["title", "content"])
    elif section == "sec_files":
        cols, rows = _to_table(_records(report, "files"), ["domain", "path"])
    elif section == "sec_links":
        cols, rows = _to_table(link_analysis(report),
                               ["counterpart", "app", "interactions"])
    elif section == "sec_identities":
        cols, rows = _to_table(unified_contacts(report),
                               ["identity", "phones", "apps", "interactions"])
    else:
        cols, rows = [], []
    return cols, rows, note
