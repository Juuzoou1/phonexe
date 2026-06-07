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
        ("stat_calls", _count(report, "calls")),
        ("stat_contacts", _count(report, "contacts")),
        ("stat_files", files),
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
    return {
        "from_me": from_me,
        "text": _pick(rec, "text", "body", "content", "data", "caption"),
        "timestamp": _pick(rec, "timestamp", "date", "time"),
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
    # social app: flatten its tables and group by sender if any
    app = (_art(report, "social_apps").get("apps", {}) or {}).get(app_key, {})
    recs = [
        rec
        for db in app.get("databases", [])
        for t in db.get("tables", [])
        for rec in t.get("records", [])
    ]
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
        cols, rows = _to_table(_records(report, "safari_history"))
    elif section == "sec_accounts":
        emails = []
        for c in _records(report, "contacts"):
            for e in c.get("emails", []) or []:
                emails.append({"account": e, "type": "email", "source": "contacts"})
        cols, rows = _to_table(emails, ["account", "type", "source"])
        note = tr("accounts_note")
    elif section == "sec_deleted":
        cols, rows = [], []
        note = tr("deleted_note")
    else:
        cols, rows = [], []
    return cols, rows, note
