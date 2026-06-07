"""
phonexe command-line interface.

Usage:
    phonexe analyze <backup_dir> [-o OUTPUT_DIR] [--no-photos] [--hash]
    phonexe info <backup_dir>
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .apps import social, whatsapp
from .backup import BackupError, IOSBackup
from .extractors import calls, contacts, messages, photos, safari
from .hashing import hash_tree
from .reporting import report as reporting

BANNER = r"""
        _
  _ __ | |__   ___  _ __   _____  _____
 | '_ \| '_ \ / _ \| '_ \ / _ \ \/ / _ \
 | |_) | | | | (_) | | | |  __/>  <  __/
 | .__/|_| |_|\___/|_| |_|\___/_/\_\___|
 |_|   iOS Backup Forensic Analyzer  v%s
""" % __version__

# Default extractor pipeline. Order controls report section order.
_CORE_EXTRACTORS = [
    contacts,
    messages,
    calls,
    safari,
    whatsapp,
    social,
]


def _cmd_info(args) -> int:
    try:
        backup = IOSBackup(args.backup_dir)
    except BackupError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 2
    print(BANNER)
    print("[i] Device information:\n")
    for k, v in backup.device.as_dict().items():
        if v is not None:
            print(f"    {k:20} : {v}")
    return 0


def _cmd_analyze(args) -> int:
    try:
        backup = IOSBackup(args.backup_dir)
    except BackupError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 2

    print(BANNER)
    print(f"[i] Analyzing backup: {backup.path}")
    if backup.device.device_name:
        print(f"[i] Device: {backup.device.device_name} "
              f"({backup.device.product_type}, iOS {backup.device.product_version})")

    out_dir = Path(args.output or "phonexe_report")
    out_dir.mkdir(parents=True, exist_ok=True)

    extractors = list(_CORE_EXTRACTORS)
    if not args.no_photos:
        extractors.append(photos)

    artifacts: dict[str, dict] = {}
    for mod in extractors:
        name = getattr(mod, "ARTIFACT", mod.__name__)
        print(f"[*] Extracting {name} ...", end=" ", flush=True)
        try:
            result = mod.extract(backup)
        except Exception as e:  # never let one artifact kill the run
            print(f"FAILED ({e})")
            artifacts[name] = {"artifact": name, "error": str(e), "count": 0}
            continue
        print(f"{result.get('count', 0)} records")
        artifacts[name] = result

    meta = {
        "tool": f"phonexe v{__version__}",
        "examined_at": datetime.now(timezone.utc).isoformat(),
        "backup_path": str(backup.path),
        "examiner": args.examiner,
        "case_id": args.case_id,
    }

    if args.hash:
        print("[*] Hashing backup tree for chain-of-custody ...", end=" ",
              flush=True)
        hashes = [h.as_dict() for h in hash_tree(backup.path)]
        print(f"{len(hashes)} files")
        meta["evidence_hashes"] = hashes

    report = {
        "meta": meta,
        "device": backup.device.as_dict(),
        "artifacts": artifacts,
    }

    json_path = reporting.write_json(report, out_dir / "report.json")
    html_path = reporting.write_html(report, out_dir / "report.html")
    print(f"\n[+] JSON report : {json_path}")
    print(f"[+] HTML report : {html_path}")
    print("[+] Done.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phonexe",
        description="iOS backup forensic analyzer (authorized use only).",
    )
    parser.add_argument("--version", action="version",
                        version=f"phonexe {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info", help="show device info from a backup")
    p_info.add_argument("backup_dir", help="path to the iOS backup directory")
    p_info.set_defaults(func=_cmd_info)

    p_an = sub.add_parser("analyze", help="run full forensic extraction")
    p_an.add_argument("backup_dir", help="path to the iOS backup directory")
    p_an.add_argument("-o", "--output", help="output directory for reports")
    p_an.add_argument("--no-photos", action="store_true",
                      help="skip photo/EXIF extraction (faster)")
    p_an.add_argument("--hash", action="store_true",
                      help="hash every backup file for chain-of-custody")
    p_an.add_argument("--examiner", help="examiner name (recorded in report)")
    p_an.add_argument("--case-id", help="case identifier (recorded in report)")
    p_an.set_defaults(func=_cmd_analyze)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
