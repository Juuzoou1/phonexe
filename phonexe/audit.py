"""
Examination audit trail.

Records every significant examiner action with a UTC timestamp, so the
examination is reproducible and defensible in court. The log can be embedded
in the report and exported alongside the evidence.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class AuditLog:
    def __init__(self, examiner: str | None = None):
        self.examiner = examiner
        self.entries: list[dict] = []
        self.record("examination_started", examiner or "")

    def record(self, action: str, detail: str = "") -> None:
        self.entries.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "detail": str(detail)[:300],
            "examiner": self.examiner or "",
        })

    def as_rows(self) -> list[dict]:
        return list(self.entries)

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(json.dumps(self.entries, indent=2, ensure_ascii=False),
                     encoding="utf-8")
        return p
