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
from .android import calendar as a_calendar
from .android import calls as a_calls
from .android import contacts as a_contacts
from .android import deleted as a_deleted
from .android import files as a_files
from .android import messages as a_messages
from .android import social as a_social
from .android import whatsapp as a_whatsapp
from .android.extraction import AndroidExtraction, ExtractionError
from .apps import social, whatsapp
from .backup import BackupError, IOSBackup
from .extractors import (
    calendar,
    calls,
    contacts,
    deleted,
    files,
    messages,
    notes,
    photos,
    safari,
)
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
    calendar,
    notes,
    files,
    deleted,
]

# Android filesystem-extraction pipeline.
_ANDROID_EXTRACTORS = [
    a_contacts,
    a_messages,
    a_calls,
    a_whatsapp,
    a_social,
    a_calendar,
    a_files,
    a_deleted,
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

    extractors = list(_CORE_EXTRACTORS)
    if not args.no_photos:
        extractors.append(photos)

    artifacts = _run_pipeline(backup, extractors)

    meta = {
        "tool": f"phonexe v{__version__}",
        "platform": "ios",
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
    _write_reports(report, Path(args.output or "phonexe_report"))
    return 0


def _run_pipeline(source, extractors) -> dict:
    """Run a list of extractor modules against *source*, printing progress."""
    artifacts: dict[str, dict] = {}
    for mod in extractors:
        name = getattr(mod, "ARTIFACT", mod.__name__)
        print(f"[*] Extracting {name} ...", end=" ", flush=True)
        try:
            result = mod.extract(source)
        except Exception as e:  # never let one artifact kill the run
            print(f"FAILED ({e})")
            artifacts[name] = {"artifact": name, "error": str(e), "count": 0}
            continue
        print(f"{result.get('count', 0)} records")
        artifacts[name] = result
    return artifacts


def _write_reports(report: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = reporting.write_json(report, out_dir / "report.json")
    html_path = reporting.write_html(report, out_dir / "report.html")
    print(f"\n[+] JSON report : {json_path}")
    print(f"[+] HTML report : {html_path}")
    print("[+] Done.")


def _cmd_android_info(args) -> int:
    try:
        ext = AndroidExtraction(args.extraction_dir)
    except ExtractionError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 2
    print(BANNER)
    print("[i] Android device information:\n")
    any_info = False
    for k, v in ext.device.as_dict().items():
        if v is not None:
            any_info = True
            print(f"    {k:20} : {v}")
    if not any_info:
        print("    (no build.prop found in extraction)")
    return 0


def _cmd_android(args) -> int:
    try:
        ext = AndroidExtraction(args.extraction_dir)
    except ExtractionError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 2

    print(BANNER)
    print(f"[i] Analyzing Android extraction: {ext.path}")
    if ext.device.model:
        print(f"[i] Device: {ext.device.manufacturer} {ext.device.model} "
              f"(Android {ext.device.android_version})")

    artifacts = _run_pipeline(ext, _ANDROID_EXTRACTORS)

    meta = {
        "tool": f"phonexe v{__version__}",
        "platform": "android",
        "examined_at": datetime.now(timezone.utc).isoformat(),
        "extraction_path": str(ext.path),
        "examiner": args.examiner,
        "case_id": args.case_id,
    }
    if args.hash:
        print("[*] Hashing extraction tree for chain-of-custody ...", end=" ",
              flush=True)
        hashes = [h.as_dict() for h in hash_tree(ext.path)]
        print(f"{len(hashes)} files")
        meta["evidence_hashes"] = hashes

    report = {
        "meta": meta,
        "device": ext.device.as_dict(),
        "artifacts": artifacts,
    }
    _write_reports(report, Path(args.output or "phonexe_report"))
    return 0


def _cmd_android_adb(args) -> int:
    from .android import adb

    if not adb.adb_available():
        print("[!] `adb` not found on PATH. Install Android platform-tools.",
              file=sys.stderr)
        return 2
    try:
        devices = adb.list_devices()
    except adb.ADBError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 2
    if not devices:
        print("[!] No authorized device connected. Enable USB debugging and "
              "accept the prompt on the device.", file=sys.stderr)
        return 2

    serial = args.serial or devices[0]
    print(BANNER)
    print(f"[i] Live ADB logical extraction from: {serial}")
    info = adb.device_info(serial)
    if info.get("model"):
        print(f"[i] Device: {info.get('manufacturer')} {info.get('model')} "
              f"(Android {info.get('android_version')})")

    print("[*] Pulling contacts / SMS / call log via content providers ...")
    artifacts = adb.logical_extract(serial)
    for name, data in artifacts.items():
        print(f"    {name}: {data.get('count', 0)} records")

    report = {
        "meta": {
            "tool": f"phonexe v{__version__}",
            "platform": "android",
            "acquisition": "adb-logical",
            "examined_at": datetime.now(timezone.utc).isoformat(),
            "device_serial": serial,
            "examiner": args.examiner,
            "case_id": args.case_id,
        },
        "device": info,
        "artifacts": artifacts,
    }
    _write_reports(report, Path(args.output or "phonexe_report"))
    return 0


def _cmd_acquire_ios(args) -> int:
    from . import ios_acquire

    print(BANNER)
    status = ios_acquire.check()
    if args.check or not status["ready"]:
        print("[i] iOS acquisition readiness:\n")
        print(f"    libimobiledevice : {'yes' if status['libimobiledevice'] else 'no'}")
        print(f"    pymobiledevice3  : {'yes' if status['pymobiledevice3'] else 'no'}")
        print(f"    ready            : {'YES' if status['ready'] else 'NO'}")
        if not status["ready"]:
            print("\n[!] No acquisition backend available.")
            print("    - Windows: install the free 'Apple Devices' app (Apple")
            print("      Mobile Device Support USB driver), then bundle")
            print("      libimobiledevice tools or install pymobiledevice3.")
            return 0 if args.check else 2
        if args.check:
            return 0

    devices = ios_acquire.list_devices()
    if not devices:
        print("[!] No device detected. Connect an UNLOCKED, trusted iPhone "
              "(tap 'Trust This Computer'), ideally in airplane mode.",
              file=sys.stderr)
        return 2
    udid = args.serial or devices[0]
    info = ios_acquire.device_info(udid)
    name = info.get("DeviceName", "iPhone")
    print(f"[i] Device: {name} (iOS {info.get('ProductVersion', '?')}) "
          f"UDID {udid}")

    out_root = Path(args.output or "ios_acquisition")
    print(f"[*] Acquiring backup into {out_root} (this can take a while) ...")
    try:
        backup_dir = ios_acquire.acquire(out_root, udid,
                                         progress=lambda ln: print("   ", ln))
    except ios_acquire.AcquireError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 2

    print(f"[+] Acquired. Analyzing {backup_dir} ...")
    args.backup_dir = str(backup_dir)
    args.no_photos = False
    args.hash = True
    return _cmd_analyze(args)


def _cmd_gui(args) -> int:
    try:
        from .gui.app import run as run_gui
    except ImportError:
        print("[!] PyQt6 is required for the GUI. Install it with: "
              "pip install PyQt6", file=sys.stderr)
        return 2
    return run_gui([sys.argv[0]])


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

    # ---- Android: filesystem extraction ----
    p_ainfo = sub.add_parser("android-info",
                             help="show device info from an Android extraction")
    p_ainfo.add_argument("extraction_dir",
                         help="path to the extracted /data tree")
    p_ainfo.set_defaults(func=_cmd_android_info)

    p_and = sub.add_parser("android",
                           help="analyze an Android filesystem extraction")
    p_and.add_argument("extraction_dir",
                       help="path to the extracted /data tree")
    p_and.add_argument("-o", "--output", help="output directory for reports")
    p_and.add_argument("--hash", action="store_true",
                       help="hash every file for chain-of-custody")
    p_and.add_argument("--examiner", help="examiner name (recorded in report)")
    p_and.add_argument("--case-id", help="case identifier (recorded in report)")
    p_and.set_defaults(func=_cmd_android)

    # ---- Android: live ADB logical acquisition ----
    p_adb = sub.add_parser(
        "android-adb",
        help="live logical extraction from an authorized USB-debugging device",
    )
    p_adb.add_argument("-s", "--serial", help="target device serial (adb -s)")
    p_adb.add_argument("-o", "--output", help="output directory for reports")
    p_adb.add_argument("--examiner", help="examiner name (recorded in report)")
    p_adb.add_argument("--case-id", help="case identifier (recorded in report)")
    p_adb.set_defaults(func=_cmd_android_adb)

    # ---- iOS direct acquisition ----
    p_acq = sub.add_parser(
        "acquire-ios",
        help="pull a backup from a connected, authorized iPhone and analyze it",
    )
    p_acq.add_argument("--check", action="store_true",
                       help="only report acquisition readiness")
    p_acq.add_argument("-s", "--serial", help="target device UDID")
    p_acq.add_argument("-o", "--output", help="output directory")
    p_acq.add_argument("--examiner", help="examiner name (recorded in report)")
    p_acq.add_argument("--case-id", help="case identifier (recorded in report)")
    p_acq.set_defaults(func=_cmd_acquire_ios)

    # ---- desktop GUI ----
    p_gui = sub.add_parser("gui", help="launch the desktop GUI (PyQt6)")
    p_gui.set_defaults(func=_cmd_gui)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
