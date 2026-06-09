"""
iOS backup structure parser.

A modern (iOS 10+) backup is a directory containing:

    Manifest.db    -- SQLite DB mapping each backed-up file to its domain
                      and relative path. Actual file payloads are stored
                      under two-hex-char subfolders, named by their fileID
                      (SHA-1 of "<domain>-<relativePath>").
    Manifest.plist -- backup-level metadata (incl. IsEncrypted flag).
    Info.plist     -- device metadata (name, model, iOS version, IMEI...).
    Status.plist   -- snapshot/state metadata.

This module exposes the device info and lets callers resolve a logical
file (by domain + relative path) to its on-disk payload.
"""

from __future__ import annotations

import plistlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


class BackupError(Exception):
    pass


@dataclass
class BackupFile:
    file_id: str
    domain: str
    relative_path: str
    flags: int

    @property
    def is_file(self) -> bool:
        # flag 1 == regular file, 2 == directory, 4 == symlink
        return self.flags == 1


@dataclass
class DeviceInfo:
    device_name: Optional[str] = None
    product_name: Optional[str] = None
    product_type: Optional[str] = None
    product_version: Optional[str] = None
    build_version: Optional[str] = None
    serial_number: Optional[str] = None
    imei: Optional[str] = None
    phone_number: Optional[str] = None
    unique_identifier: Optional[str] = None
    last_backup_date: Optional[str] = None

    def as_dict(self) -> dict:
        return self.__dict__.copy()


class IOSBackup:
    """Read-only accessor for an extracted iOS backup directory."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.is_dir():
            raise BackupError(f"Backup path is not a directory: {self.path}")

        self.manifest_db = self.path / "Manifest.db"
        if not self.manifest_db.exists():
            raise BackupError(
                "Manifest.db not found. This does not look like an iOS 10+ "
                "backup (or the backup is encrypted and not yet decrypted)."
            )

        self._check_encryption()
        self.device = self._load_device_info()

    # ----------------------------------------------------------------- info
    def _check_encryption(self) -> None:
        manifest_plist = self.path / "Manifest.plist"
        if not manifest_plist.exists():
            return
        try:
            data = plistlib.loads(manifest_plist.read_bytes())
        except Exception:
            return
        if data.get("IsEncrypted"):
            raise BackupError(
                "This backup is ENCRYPTED. phonexe analyzes decrypted "
                "backups only. Decrypt it first using the backup password "
                "you are lawfully authorized to use (e.g. via Finder/iTunes "
                "with 'Encrypt local backup' settings), then re-run."
            )

    def _load_device_info(self) -> DeviceInfo:
        info = DeviceInfo()
        info_plist = self.path / "Info.plist"
        if info_plist.exists():
            try:
                d = plistlib.loads(info_plist.read_bytes())
            except Exception:
                d = {}
            info.device_name = d.get("Device Name")
            info.product_name = d.get("Product Name")
            info.product_type = d.get("Product Type")
            info.product_version = d.get("Product Version")
            info.build_version = d.get("Build Version")
            info.serial_number = d.get("Serial Number")
            info.imei = d.get("IMEI")
            info.phone_number = d.get("Phone Number")
            info.unique_identifier = d.get("Unique Identifier") or d.get(
                "Target Identifier"
            )
            ldb = d.get("Last Backup Date")
            info.last_backup_date = ldb.isoformat() if ldb else None
        return info

    # ----------------------------------------------------------------- files
    def iter_files(
        self, domain: Optional[str] = None, path_like: Optional[str] = None
    ) -> Iterator[BackupFile]:
        """Yield BackupFile rows, optionally filtered by domain / path glob.

        *path_like* is a SQL LIKE pattern matched against relativePath.
        """
        query = "SELECT fileID, domain, relativePath, flags FROM Files"
        clauses, params = [], []
        if domain:
            clauses.append("domain = ?")
            params.append(domain)
        if path_like:
            clauses.append("relativePath LIKE ?")
            params.append(path_like)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        # as_uri() percent-encodes '#'/'%' in the path (legal on Windows) so
        # SQLite opens the real Manifest.db instead of an empty anonymous DB.
        uri = f"{self.manifest_db.resolve().as_uri()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as con:
            for row in con.execute(query, params):
                yield BackupFile(
                    file_id=row[0],
                    domain=row[1],
                    relative_path=row[2] or "",
                    flags=row[3] or 0,
                )

    def resolve(self, file: BackupFile) -> Optional[Path]:
        """Return the on-disk payload path for a BackupFile, if it exists."""
        candidate = self.path / file.file_id[:2] / file.file_id
        if candidate.exists():
            return candidate
        # Some very old backups stored payloads flat in the root.
        flat = self.path / file.file_id
        return flat if flat.exists() else None

    def find_one(self, domain: str, relative_path: str) -> Optional[Path]:
        """Resolve a single known file by exact domain + relative path."""
        for f in self.iter_files(domain=domain):
            if f.relative_path == relative_path:
                return self.resolve(f)
        return None
