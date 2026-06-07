"""
Android filesystem-extraction accessor.

Wraps a directory tree copied from an Android device's /data partition and
locates app databases by package + filename. Dumps vary in layout (some root
at /, some at /data, some at the raw partition), so lookups search the tree
rather than assuming a fixed prefix.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ExtractionError(Exception):
    pass


@dataclass
class AndroidDeviceInfo:
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    brand: Optional[str] = None
    android_version: Optional[str] = None
    sdk: Optional[str] = None
    fingerprint: Optional[str] = None
    serial: Optional[str] = None

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def _parse_build_prop(text: str) -> AndroidDeviceInfo:
    props: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        props[k.strip()] = v.strip()
    return AndroidDeviceInfo(
        manufacturer=props.get("ro.product.manufacturer"),
        model=props.get("ro.product.model"),
        brand=props.get("ro.product.brand"),
        android_version=props.get("ro.build.version.release"),
        sdk=props.get("ro.build.version.sdk"),
        fingerprint=props.get("ro.build.fingerprint"),
        serial=props.get("ro.serialno"),
    )


class AndroidExtraction:
    """Read-only accessor for an extracted Android /data tree."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.is_dir():
            raise ExtractionError(f"Not a directory: {self.path}")
        self.device = self._load_device_info()

    # ----------------------------------------------------------------- info
    def _load_device_info(self) -> AndroidDeviceInfo:
        for name in ("build.prop", "system/build.prop", "default.prop"):
            candidates = list(self.path.rglob(name))
            if candidates:
                try:
                    return _parse_build_prop(
                        candidates[0].read_text(errors="replace")
                    )
                except Exception:
                    pass
        return AndroidDeviceInfo()

    # ----------------------------------------------------------------- files
    def find_db(self, package: str, db_name: str) -> Optional[Path]:
        """Locate <package>'s database file *db_name* anywhere in the tree."""
        for p in self.path.rglob(db_name):
            # Require the package name to appear in the path so we don't grab
            # an unrelated app's identically named database.
            if package in str(p):
                return p
        # Fall back to the conventional location if present.
        conventional = (
            self.path / "data" / "data" / package / "databases" / db_name
        )
        return conventional if conventional.exists() else None

    def iter_app_databases(self, package: str):
        """Yield every *.db file belonging to *package*."""
        seen = set()
        for pattern in ("*.db", "*.sqlite", "*.sqlitedb"):
            for p in self.path.rglob(pattern):
                if package in str(p) and p not in seen and p.is_file():
                    seen.add(p)
                    yield p
