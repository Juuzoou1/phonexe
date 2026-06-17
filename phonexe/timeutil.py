"""
Apple timestamp conversion helpers.

Apple stores time in several formats. The two most common in SQLite
artifacts are:

* Mac Absolute Time  -- seconds since 2001-01-01 00:00:00 UTC
                        (Core Data / Cocoa). Newer iMessage rows use
                        *nanoseconds* since the same epoch.
* Unix epoch         -- seconds since 1970-01-01 00:00:00 UTC.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

# Offset between the Cocoa epoch (2001) and the Unix epoch (1970).
_COCOA_EPOCH_OFFSET = 978307200  # seconds


def cocoa_to_iso(value: Optional[float]) -> Optional[str]:
    """Convert a Mac Absolute Time value to an ISO-8601 UTC string.

    Handles both second- and nanosecond-precision values (iMessage switched
    to nanoseconds around iOS 11); we detect the latter by magnitude.
    """
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v == 0:
        return None
    # Nanosecond timestamps are ~1e18; second timestamps are ~5e8.
    if abs(v) > 1e11:
        v = v / 1_000_000_000
    try:
        dt = datetime(2001, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=v)
        return dt.isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def chrome_to_iso(value: Optional[float]) -> Optional[str]:
    """Convert a Chrome/WebKit timestamp (microseconds since 1601) to ISO-8601."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v == 0:
        return None
    # microseconds since 1601-01-01 -> Unix seconds
    unix = v / 1_000_000 - 11644473600
    try:
        return datetime.fromtimestamp(unix, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def unix_to_iso(value: Optional[float], millis: bool = False) -> Optional[str]:
    """Convert a Unix timestamp (seconds, or milliseconds) to ISO-8601 UTC."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v == 0:
        return None
    if millis:
        v = v / 1000
    try:
        return datetime.fromtimestamp(v, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None
