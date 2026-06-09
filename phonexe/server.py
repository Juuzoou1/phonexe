"""
Local JSON API server for the Electron/React desktop frontend.

Exposes the Python forensic engine over HTTP on localhost so the React UI can
consume structured data. Uses only the standard library (no extra deps), and
reuses the Qt-free analysis + datasource layers.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__, analyze
from .gui import datasource as ds


class _State:
    report: dict | None = None
    lock = threading.Lock()


def _section_payload(report, key):
    cols, rows, note = ds.section_table(report, key)
    return {"columns": cols, "rows": rows, "note": note}


def _overview(report):
    return {
        "device": report.get("device", {}),
        "meta": report.get("meta", {}),
        "stats": [{"key": k, "value": v} for k, v in ds.overview_stats(report)],
        "sections": {
            s: ds.section_count(report, s)
            for s in (
                "sec_apps", "sec_installed", "sec_messages", "sec_media",
                "sec_location", "sec_calls", "sec_voicemail", "sec_contacts",
                "sec_browser", "sec_calendar", "sec_notes", "sec_files",
                "sec_deleted",
            )
        },
        "apps": ds.chat_apps(report),
    }


def make_handler(state: _State):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):  # silence default logging
            pass

        def _send(self, obj, status=200):
            body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):  # noqa: N802 (CORS preflight)
            self._send({}, 200)

        def do_GET(self):  # noqa: N802
            u = urlparse(self.path)
            path = u.path.rstrip("/")
            q = parse_qs(u.query)
            report = state.report

            if path == "/api/health":
                return self._send({"ok": True, "version": __version__,
                                   "has_report": report is not None})
            if report is None:
                return self._send({"error": "no_report"}, 404)
            if path == "/api/report":
                return self._send(report)
            if path == "/api/overview":
                return self._send(_overview(report))
            if path == "/api/section":
                key = (q.get("key") or [""])[0]
                return self._send(_section_payload(report, key))
            if path == "/api/app":
                key = (q.get("key") or [""])[0]
                return self._send({"conversations": ds.conversations(report, key)})
            if path == "/api/timeline":
                return self._send({"events": ds.timeline(report)})
            if path == "/api/links":
                return self._send({"links": ds.link_analysis(report)})
            if path == "/api/identities":
                return self._send({"identities": ds.unified_contacts(report)})
            if path == "/api/map":
                return self._send({"markers": ds.location_markers(report)})
            if path == "/api/keywords":
                return self._send({"keywords": ds.keywords(report)})
            if path == "/api/search":
                query = (q.get("q") or [""])[0]
                return self._send({"hits": ds.global_search(report, query)})
            return self._send({"error": "not_found"}, 404)

        def do_POST(self):  # noqa: N802
            u = urlparse(self.path)
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw or b"{}")
            except Exception:
                data = {}
            if u.path.rstrip("/") == "/api/analyze":
                path = data.get("path", "")
                try:
                    report = analyze.analyze(path)
                except Exception as e:
                    return self._send({"error": str(e)}, 400)
                with state.lock:
                    state.report = report
                return self._send(_overview(report))
            return self._send({"error": "not_found"}, 404)

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8765,
          report: dict | None = None) -> ThreadingHTTPServer:
    state = _State()
    state.report = report
    httpd = ThreadingHTTPServer((host, port), make_handler(state))
    httpd.state = state  # type: ignore[attr-defined]
    return httpd


def run(host: str = "127.0.0.1", port: int = 8765) -> int:
    httpd = serve(host, port)
    print(f"[phonexe] API server on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0
