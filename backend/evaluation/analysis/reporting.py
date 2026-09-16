"""Shared report output for the analysis harness.

Reports must be written as explicit UTF-8. Redirected stdout on Windows falls back to
the locale codepage (cp1252), which cannot encode Sinhala or Tamil -- and every
diagnostic in this workstream carries non-Latin evidence text, so writing through
stdout silently truncates exactly the multilingual cases the analysis is about.

Per-run JSON lands in `backend/evaluation/reports/`, which is gitignored; only the
aggregated findings under `docs/rag_error_analysis/` are committed.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parents[1] / "reports"


def git_sha() -> str:
    """Stamp every report with the commit it measured, so no comparison mixes versions."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[3],
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def write_report(name: str, report: dict[str, Any], *, out: Path | None = None) -> Path:
    destination = out or REPORT_DIR / f"{name}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    stamped = {
        "git_sha": git_sha(),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        **report,
    }
    destination.write_text(
        json.dumps(stamped, indent=2, sort_keys=False, ensure_ascii=False), encoding="utf-8"
    )
    return destination


def load_report(name: str) -> dict[str, Any]:
    path = REPORT_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))
