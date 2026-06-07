"""
PDF report generation.

Renders a clean, RTL-aware forensic report to PDF using Qt's QPdfWriter +
QTextDocument — no external engine or network required. PyQt6 must be
available (it is whenever the GUI is used).
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

from .. import __version__


def _esc(v) -> str:
    return html.escape("" if v is None else str(v))


def _kv(d: dict) -> str:
    rows = "".join(
        f"<tr><td class='k'>{_esc(k)}</td><td>{_esc(v)}</td></tr>"
        for k, v in d.items() if v is not None
    )
    return f"<table class='kv'>{rows}</table>"


def _records_table(records: list[dict], limit: int = 300) -> str:
    if not records:
        return "<p class='dim'>لا توجد سجلات.</p>"
    cols: list[str] = []
    for r in records[:limit]:
        for k in r:
            if k not in cols:
                cols.append(k)
    head = "".join(f"<th>{_esc(c)}</th>" for c in cols)
    body = []
    for r in records[:limit]:
        body.append("<tr>" + "".join(
            f"<td>{_esc(r.get(c, ''))}</td>" for c in cols) + "</tr>")
    extra = (f"<p class='dim'>عرض أول {limit} من {len(records)} سجل.</p>"
             if len(records) > limit else "")
    return (f"<table class='data'><tr>{head}</tr>{''.join(body)}</table>"
            f"{extra}")


def _report_html(report: dict) -> str:
    device = report.get("device", {}) or {}
    meta = report.get("meta", {}) or {}
    artifacts = report.get("artifacts", {}) or {}
    generated = datetime.now(timezone.utc).isoformat()

    sections = [
        "<h1>تقرير فحص جنائي رقمي — phonexe</h1>",
        f"<p class='dim'>تم الإنشاء: {_esc(generated)} · phonexe v{__version__}</p>",
        "<div class='scope'>تقرير لأدلة محلية من نسخة/استخراج قانوني — بدون كسر "
        "أقفال أو تشفير.</div>",
        "<h2>معلومات الجهاز</h2>", _kv(device),
        "<h2>بيانات الفحص</h2>",
        _kv({k: v for k, v in meta.items() if k != "evidence_hashes"}),
    ]
    for name, data in artifacts.items():
        count = data.get("count", 0)
        sections.append(f"<h2>{_esc(name)} ({count})</h2>")
        if "records" in data:
            sections.append(_records_table(data["records"]))
        elif "apps" in data:
            for app in data["apps"].values():
                sections.append(f"<h3>{_esc(app.get('name'))}</h3>")
                for db in app.get("databases", []):
                    for t in db.get("tables", []):
                        sections.append(_records_table(t.get("records", [])))

    hashes = meta.get("evidence_hashes")
    if hashes:
        sections.append("<h2>بصمات سلامة الأدلة (Chain of Custody)</h2>")
        sections.append(_records_table(
            [{"path": h["path"], "sha256": h["sha256"]} for h in hashes], 1000))

    css = """
    body{font-family:'IBM Plex Sans Arabic','Cairo',Arial;color:#10202e;}
    h1{font-size:20pt;color:#0b2a3a;}
    h2{font-size:14pt;color:#0b2a3a;border-bottom:1px solid #ccc;
       padding-bottom:3px;margin-top:16px;}
    h3{font-size:12pt;color:#155;}
    .dim{color:#888;font-size:9pt;}
    .scope{background:#fff7e6;border:1px solid #ffe1a8;padding:6px;
           font-size:9pt;color:#7a5a00;}
    table{border-collapse:collapse;width:100%;font-size:8.5pt;}
    table.kv td{padding:3px 6px;border:1px solid #ddd;}
    table.kv td.k{color:#555;width:30%;}
    table.data th{background:#eef2f5;border:1px solid #ccc;padding:3px;}
    table.data td{border:1px solid #ddd;padding:3px;}
    """
    return (f"<html dir='rtl'><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>{''.join(sections)}</body></html>")


def write_pdf(report: dict, out_path: str | Path) -> Path:
    """Render *report* to a PDF file at *out_path*."""
    from PyQt6.QtGui import QPdfWriter, QPageSize, QTextDocument

    p = Path(out_path)
    writer = QPdfWriter(str(p))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setResolution(150)
    doc = QTextDocument()
    doc.setHtml(_report_html(report))
    doc.print_(writer)
    return p
