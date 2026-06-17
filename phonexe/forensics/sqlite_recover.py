"""
Best-effort recovery of deleted records from SQLite databases.

When a row is deleted, SQLite marks its cell as a *freeblock* and may release
whole pages onto the *freelist*, but the original bytes are not wiped. This
module locates those unallocated regions (freeblocks, never-reused gaps, and
free pages) and carves readable text fragments out of them — the standard
"unallocated space" forensic technique. It deliberately excludes bytes that
belong to live cells, so recovered fragments represent deleted/old content.

This is a recovery aid, not a guarantee: fragments may be partial, and rows
whose space was overwritten by new data are unrecoverable.
"""

from __future__ import annotations

import re
from pathlib import Path

_MAGIC = b"SQLite format 3\x00"
# Only scan databases up to this size to keep carving responsive.
_MAX_BYTES = 256 * 1024 * 1024
# Printable run (Arabic + Latin + punctuation), excluding control chars.
_TEXT_RE = re.compile(r"[^\x00-\x1f\x7f]{4,}")
_MIN_LEN = 4


def _varint(buf: bytes, off: int) -> tuple[int, int]:
    """Decode a SQLite varint; return (value, next_offset)."""
    result = 0
    for i in range(9):
        if off + i >= len(buf):
            return result, off + i
        byte = buf[off + i]
        if i == 8:
            result = (result << 8) | byte
            return result, off + 9
        result = (result << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            return result, off + i + 1
    return result, off + 9


def _freelist_pages(raw: bytes, page_size: int) -> set[int]:
    """Return 0-based indexes of pages currently on the freelist."""
    pages: set[int] = set()
    first_trunk = int.from_bytes(raw[32:36], "big")
    total = int.from_bytes(raw[36:40], "big")
    trunk = first_trunk
    guard = 0
    while trunk and guard <= total + 1:
        guard += 1
        base = (trunk - 1) * page_size
        if base < 0 or base + 8 > len(raw):
            break
        next_trunk = int.from_bytes(raw[base:base + 4], "big")
        n_leaf = int.from_bytes(raw[base + 4:base + 8], "big")
        pages.add(trunk - 1)
        for i in range(n_leaf):
            off = base + 8 + i * 4
            if off + 4 > len(raw):
                break
            leaf = int.from_bytes(raw[off:off + 4], "big")
            if leaf:
                pages.add(leaf - 1)
        trunk = next_trunk
    return pages


def _text_runs(span: bytes) -> list[str]:
    text = span.decode("utf-8", "ignore")
    out = []
    for m in _TEXT_RE.finditer(text):
        frag = m.group().strip()
        if len(frag) >= _MIN_LEN and any(c.isalpha() for c in frag):
            out.append(frag)
    return out


def recover_deleted(path: str | Path) -> list[dict]:
    """Carve deleted text fragments from a SQLite file.

    Returns a list of {"page": int, "text": str} records.
    """
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError:
        return []
    if raw[:16] != _MAGIC or len(raw) > _MAX_BYTES:
        return []

    page_size = int.from_bytes(raw[16:18], "big")
    if page_size == 1:
        page_size = 65536
    if page_size < 512 or page_size & (page_size - 1):
        return []
    n_pages = len(raw) // page_size

    # active[b] == 1  -> live or structural byte (do not carve)
    active = bytearray(len(raw))
    free_pages = _freelist_pages(raw, page_size)

    def mark(a: int, b: int):
        a = max(0, a)
        b = min(len(raw), b)
        if b > a:
            active[a:b] = b"\x01" * (b - a)

    for i in range(n_pages):
        base = i * page_size
        if i in free_pages:
            continue  # whole free page is carvable
        hdr = base + (100 if i == 0 else 0)
        ptype = raw[hdr] if hdr < len(raw) else 0

        if ptype not in (2, 5, 10, 13):
            mark(base, base + page_size)  # non-btree page: skip carving
            continue

        is_leaf = ptype in (10, 13)
        hlen = 8 if is_leaf else 12
        ncells = int.from_bytes(raw[hdr + 3:hdr + 5], "big")
        ptr_array_end = hdr + hlen + 2 * ncells
        mark(base, ptr_array_end)  # page header + cell pointer array

        if ptype == 13:  # table leaf: mark each live cell's bytes
            for c in range(ncells):
                po = hdr + hlen + 2 * c
                cp = int.from_bytes(raw[po:po + 2], "big")
                cell_off = base + cp
                if cell_off >= base + page_size:
                    continue
                plen, o1 = _varint(raw, cell_off)
                _rowid, o2 = _varint(raw, o1)
                cell_len = (o2 - cell_off) + plen
                mark(cell_off, cell_off + cell_len)
        else:
            # interior/index pages: don't attempt structured carving
            content = int.from_bytes(raw[hdr + 5:hdr + 7], "big") or page_size
            mark(base + content, base + page_size)

    # scan unmarked spans for text
    results: list[dict] = []
    seen: set[str] = set()
    i, N = 0, len(raw)
    while i < N:
        if active[i] == 0:
            j = i
            while j < N and active[j] == 0:
                j += 1
            for frag in _text_runs(raw[i:j]):
                if frag not in seen:
                    seen.add(frag)
                    results.append({"page": i // page_size + 1, "text": frag})
            i = j
        else:
            i += 1
    return results
