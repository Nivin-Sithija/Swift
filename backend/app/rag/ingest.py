"""Ingest the existing approved-source manifest and structure-aware cleaned Markdown."""

import argparse
import asyncio
import csv
import hashlib
import re
import uuid
from pathlib import Path

from sqlalchemy import text

from app.core.db import SessionLocal
from app.rag.models import BGEM3Embedder

HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
OFFICIAL_DOMAINS = ("combank.lk", "peoplesbank.lk", "cbsl.gov.lk")


def chunk_markdown(document: str, *, max_chars: int = 1800) -> list[tuple[str, str]]:
    """Keep heading context and tables/lists together where practical."""
    matches = list(HEADING.finditer(document))
    chunks: list[tuple[str, str]] = []
    headings: list[str] = []
    for index, match in enumerate(matches):
        level, title = len(match.group(1)), match.group(2).strip()
        headings = headings[: level - 1] + [title]
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(document)
        body = document[match.end():body_end].strip()
        section = " > ".join(headings)
        paragraphs = re.split(r"\n\s*\n", body)
        current = f"{match.group(0)}\n"
        for paragraph in paragraphs:
            if len(current) + len(paragraph) > max_chars and len(current) > len(match.group(0)) + 2:
                chunks.append((section, current.strip()))
                current = f"{match.group(0)}\n{paragraph}\n"
            else:
                current += paragraph + "\n\n"
        if current.strip() != match.group(0):
            chunks.append((section, current.strip()))
    return chunks


def validate_source(row: dict[str, str]) -> None:
    if row["approval_status"] != "approved":
        raise ValueError(f"{row['source_id']} is not approved")
    if not any(domain in row["source_url"] for domain in OFFICIAL_DOMAINS):
        raise ValueError(f"{row['source_id']} is not an allow-listed official source")


async def ingest(manifest: Path, root: Path) -> int:
    embedder = BGEM3Embedder()
    rows = list(csv.DictReader(manifest.open(encoding="utf-8")))
    ingested = 0
    async with SessionLocal() as db:
        for row in rows:
            validate_source(row)
            path = root / row["cleaned_path"]
            raw_path = root / row["local_path"]
            content = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            if checksum != row["checksum"]:
                raise ValueError(f"Checksum mismatch for {row['source_id']}")
            article_id = uuid.uuid5(uuid.NAMESPACE_URL, row["source_id"])
            authority = "cbsl_official" if "cbsl.gov.lk" in row["source_url"] else "bank_official"
            await db.execute(text("""INSERT INTO knowledge_articles
                (id,source_id,title,source_url,institution,category,language,source_authority,version,review_date,approval_status,checksum)
                VALUES (:id,:source_id,:title,:source_url,:institution,:category,:language,:authority,:version,:review_date,'approved',:checksum)
                ON CONFLICT (source_id) DO UPDATE SET title=EXCLUDED.title, source_url=EXCLUDED.source_url,
                institution=EXCLUDED.institution, category=EXCLUDED.category, language=EXCLUDED.language,
                source_authority=EXCLUDED.source_authority, version=EXCLUDED.version, review_date=EXCLUDED.review_date,
                approval_status=EXCLUDED.approval_status, checksum=EXCLUDED.checksum, updated_at=now()"""), {
                    "id": article_id, "source_id": row["source_id"], "title": row["title"],
                    "source_url": row["source_url"], "institution": row["owner"], "category": row["category"],
                    "language": row["language"], "authority": authority, "version": row["version"],
                    "review_date": row["last_reviewed"], "checksum": checksum,
                })
            await db.execute(text("DELETE FROM knowledge_chunks WHERE article_id=:id"), {"id": article_id})
            for index, (section, chunk) in enumerate(chunk_markdown(content)):
                vector = await embedder.embed_query(chunk)
                await db.execute(text("""INSERT INTO knowledge_chunks
                    (id,article_id,chunk_index,section_path,content,embedding)
                    VALUES (:id,:article_id,:chunk_index,:section,:content,CAST(:embedding AS vector))"""), {
                        "id": uuid.uuid4(), "article_id": article_id, "chunk_index": index,
                        "section": section, "content": chunk, "embedding": str(vector),
                    })
            ingested += 1
        await db.commit()
    return ingested


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("../docs/rag_sources/rag_source_manifest.csv"))
    parser.add_argument("--root", type=Path, default=Path("../docs/rag_sources"))
    args = parser.parse_args()
    print(f"Ingested {asyncio.run(ingest(args.manifest, args.root))} approved articles")
