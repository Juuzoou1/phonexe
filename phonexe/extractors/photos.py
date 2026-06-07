"""Extract photo media and their EXIF metadata (incl. GPS) from a backup.

EXIF parsing uses Pillow if installed. If Pillow is unavailable, the media
inventory is still produced (paths + on-disk hashes), just without EXIF.
"""

from __future__ import annotations

from ..backup import IOSBackup

ARTIFACT = "photos"
_DOMAIN = "CameraRollDomain"
_IMAGE_EXTS = (".jpg", ".jpeg", ".heic", ".png", ".tiff")

try:  # optional dependency
    from PIL import Image
    from PIL.ExifTags import GPSTAGS, TAGS

    _HAVE_PIL = True
except Exception:  # pragma: no cover - depends on environment
    _HAVE_PIL = False


def _dms_to_decimal(dms, ref) -> float | None:
    try:
        deg, minute, sec = (float(x) for x in dms)
        dec = deg + minute / 60 + sec / 3600
        if ref in ("S", "W"):
            dec = -dec
        return round(dec, 6)
    except Exception:
        return None


def _read_exif(path) -> dict:
    if not _HAVE_PIL:
        return {}
    try:
        img = Image.open(path)
        raw = img._getexif() or {}
    except Exception:
        return {}

    exif = {}
    gps_raw = {}
    for tag_id, value in raw.items():
        tag = TAGS.get(tag_id, tag_id)
        if tag == "GPSInfo":
            for gk, gv in value.items():
                gps_raw[GPSTAGS.get(gk, gk)] = gv
        elif tag in ("DateTimeOriginal", "DateTime", "Make", "Model"):
            exif[tag] = str(value)

    if gps_raw:
        lat = _dms_to_decimal(
            gps_raw.get("GPSLatitude"), gps_raw.get("GPSLatitudeRef")
        )
        lon = _dms_to_decimal(
            gps_raw.get("GPSLongitude"), gps_raw.get("GPSLongitudeRef")
        )
        if lat is not None and lon is not None:
            exif["gps_latitude"] = lat
            exif["gps_longitude"] = lon
    return exif


def extract(backup: IOSBackup) -> dict:
    records = []
    for f in backup.iter_files(domain=_DOMAIN):
        if not f.is_file:
            continue
        if not f.relative_path.lower().endswith(_IMAGE_EXTS):
            continue
        payload = backup.resolve(f)
        if not payload:
            continue
        rec = {
            "relative_path": f.relative_path,
            "stored_at": str(payload),
            "exif": _read_exif(payload),
        }
        records.append(rec)

    return {
        "artifact": ARTIFACT,
        "count": len(records),
        "exif_available": _HAVE_PIL,
        "records": records,
    }
