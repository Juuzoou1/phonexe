"""Forensic report generation (JSON + self-contained HTML)."""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from .. import __version__


def _json_default(o):
    if isinstance(o, (bytes, bytearray)):
        return f"<blob {len(o)} bytes>"
    return str(o)


def write_json(report: dict, out_path: str | Path) -> Path:
    p = Path(out_path)
    p.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    return p


def _section(title: str, body_html: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2>{body_html}</section>"


def _kv_table(d: dict) -> str:
    rows = "".join(
        f"<tr><th>{html.escape(str(k))}</th>"
        f"<td>{html.escape(str(v))}</td></tr>"
        for k, v in d.items()
        if v is not None
    )
    return f"<table class='kv'>{rows}</table>"


def _records_table(records: list[dict], limit: int = 500) -> str:
    if not records:
        return "<p class='empty'>No records.</p>"
    cols: list[str] = []
    for r in records[:limit]:
        for k in r:
            if k not in cols:
                cols.append(k)
    head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    body_rows = []
    for r in records[:limit]:
        cells = "".join(
            f"<td>{html.escape(str(r.get(c, '')))}</td>" for c in cols
        )
        body_rows.append(f"<tr>{cells}</tr>")
    extra = (
        f"<p class='note'>Showing first {limit} of {len(records)} records.</p>"
        if len(records) > limit
        else ""
    )
    return (
        f"<table class='data'><thead><tr>{head}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody></table>{extra}"
    )


_CSS = """
body{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0;
color:#1d2330;background:#f5f6f8}
header{background:#11203a;color:#fff;padding:24px 32px}
header h1{margin:0 0 4px;font-size:22px}
header .sub{opacity:.8;font-size:13px}
main{padding:24px 32px;max-width:1200px;margin:0 auto}
section{background:#fff;border:1px solid #e2e5ea;border-radius:10px;
padding:18px 20px;margin-bottom:20px}
h2{margin:0 0 12px;font-size:17px;color:#11203a;
border-bottom:2px solid #eef0f3;padding-bottom:8px}
table{border-collapse:collapse;width:100%;font-size:13px}
table.kv th{text-align:left;width:200px;color:#555;font-weight:600;
padding:4px 8px;vertical-align:top}
table.kv td{padding:4px 8px}
table.data th{background:#f0f2f5;text-align:left;padding:6px 8px;
position:sticky;top:0}
table.data td{padding:5px 8px;border-top:1px solid #eef0f3;
max-width:420px;overflow-wrap:anywhere}
table.data tbody tr:nth-child(even){background:#fafbfc}
.empty,.note{color:#888;font-size:12px}
.badge{display:inline-block;background:#e8eefc;color:#1c4ed8;
border-radius:20px;padding:2px 10px;font-size:12px;margin-left:8px}
.scope{background:#fff7e6;border:1px solid #ffe1a8;border-radius:8px;
padding:10px 14px;font-size:12px;color:#7a5a00;margin-bottom:20px}
footer{padding:20px 32px;color:#888;font-size:12px;text-align:center}
"""


def write_html(report: dict, out_path: str | Path) -> Path:
    p = Path(out_path)
    device = report.get("device", {})
    artifacts = report.get("artifacts", {})

    parts = [
        "<div class='scope'>This report covers <b>local artifacts</b> from a "
        "lawfully acquired backup. It contains no passcode-bypass or remote "
        "account data. Handle according to your jurisdiction's evidence "
        "procedures.</div>",
        _section("Device", _kv_table(device)),
        _section("Examination", _kv_table(report.get("meta", {}))),
    ]

    for name, data in artifacts.items():
        count = data.get("count", 0)
        title = f"{name}"
        body = ""
        if "records" in data:
            body = _records_table(data["records"])
        elif "apps" in data:
            blocks = []
            for app in data["apps"].values():
                blocks.append(f"<h3>{html.escape(app['name'])}</h3>")
                for db in app["databases"]:
                    location = db.get("relative_path") or db.get("path", "")
                    blocks.append(
                        f"<p class='note'>{html.escape(str(location))}</p>"
                    )
                    for t in db.get("tables", []):
                        blocks.append(
                            f"<h4>{html.escape(t['table'])} "
                            f"({t['count']})</h4>"
                        )
                        blocks.append(_records_table(t["records"]))
                    if db.get("error"):
                        blocks.append(
                            f"<p class='empty'>{html.escape(db['error'])}</p>"
                        )
            body = "".join(blocks) or "<p class='empty'>No records.</p>"
        section_html = (
            f"<h2>{html.escape(title)}"
            f"<span class='badge'>{count}</span></h2>{body}"
        )
        parts.append(f"<section>{section_html}</section>")

    generated = datetime.now(timezone.utc).isoformat()
    doc = f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1">
<title>phonexe forensic report</title><style>{_CSS}</style></head>
<body><header><h1>phonexe — iOS Backup Forensic Report</h1>
<div class="sub">Generated {html.escape(generated)} ·
phonexe v{__version__}</div></header>
<main>{''.join(parts)}</main>
<footer>Generated by phonexe · for authorized forensic use only</footer>
</body></html>"""
    p.write_text(doc, encoding="utf-8")
    return p
