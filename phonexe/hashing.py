"""
Evidence integrity & chain-of-custody hashing.

Computing cryptographic hashes of every artifact lets an examiner prove the
evidence has not been altered between acquisition and presentation.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Read in 1 MiB chunks so we can hash arbitrarily large files without
# loading them fully into memory.
_CHUNK = 1024 * 1024


@dataclass
class FileHash:
    path: str
    size: int
    md5: str
    sha1: str
    sha256: str
    hashed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "size": self.size,
            "md5": self.md5,
            "sha1": self.sha1,
            "sha256": self.sha256,
            "hashed_at": self.hashed_at,
        }


def hash_file(path: str | os.PathLike) -> FileHash:
    """Compute MD5/SHA-1/SHA-256 for a single file in one pass."""
    p = Path(path)
    md5, sha1, sha256 = hashlib.md5(), hashlib.sha1(), hashlib.sha256()
    size = 0
    with p.open("rb") as fh:
        while chunk := fh.read(_CHUNK):
            size += len(chunk)
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
    return FileHash(
        path=str(p),
        size=size,
        md5=md5.hexdigest(),
        sha1=sha1.hexdigest(),
        sha256=sha256.hexdigest(),
    )


def hash_tree(root: str | os.PathLike) -> list[FileHash]:
    """Recursively hash every file under *root* (depth-first, sorted)."""
    root = Path(root)
    results: list[FileHash] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            results.append(hash_file(path))
    return results
