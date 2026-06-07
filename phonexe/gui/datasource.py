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
