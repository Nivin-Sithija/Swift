from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

SOURCES_DIR = Path(__file__).resolve().parents[2] / "sources"
MANIFEST_PATH = SOURCES_DIR / "rag_source_manifest.csv"


@dataclass
class SourceRow:
    source_id: str
    title: str
    category: str
    language: str
    approval_status: str
    local_path: Path


def load_manifest(manifest_path: Path = MANIFEST_PATH) -> list[dict[str, str]]:
    with manifest_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_approved_sources(
    manifest_path: Path = MANIFEST_PATH, sources_dir: Path = SOURCES_DIR
) -> list[SourceRow]:
    return [
        SourceRow(
            source_id=row["source_id"],
            title=row["title"],
            category=row["category"],
            language=row["language"],
            approval_status=row["approval_status"],
            local_path=sources_dir / row["local_path"],
        )
        for row in load_manifest(manifest_path)
        if row.get("approval_status") == "approved"
    ]
