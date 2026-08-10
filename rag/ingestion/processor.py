from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion.chunking import Chunk, chunk_document
from ingestion.loaders import SourceRow, load_approved_sources, parse_html, parse_office, parse_pdf, parse_text
from services.retrieval import embed_texts, ensure_schema, get_session

_PARSERS = {
    "html": parse_html,
    "htm": parse_html,
    "pdf": parse_pdf,
    "txt": parse_text,
    "docx": parse_office,
    "pptx": parse_office,
}

# kb_articles.language is a short code (si/en/ta/mixed) — the manifest spells it out.
_LANGUAGE_CODES = {"english": "en", "sinhala": "si", "tamil": "ta"}


def parse_source(row: SourceRow) -> str:
    ext = row.local_path.suffix.lstrip(".").lower()
    parser = _PARSERS.get(ext)
    if parser is None:
        raise ValueError(f"No loader for extension '.{ext}' ({row.local_path.name})")
    return parser(str(row.local_path))


async def upsert_article(session: AsyncSession, row: SourceRow, body: str) -> str:
    existing = await session.execute(
        text("SELECT id FROM kb_articles WHERE title = :title"), {"title": row.title}
    )
    article = existing.mappings().first()
    if article:
        await session.execute(
            text("UPDATE kb_articles SET body = :body, updated_at = now() WHERE id = :id"),
            {"body": body, "id": article["id"]},
        )
        return article["id"]

    language = _LANGUAGE_CODES.get(row.language, row.language)
    inserted = await session.execute(
        text(
            """
            INSERT INTO kb_articles (title, body, language, source, status)
            VALUES (:title, :body, :language, 'manifest', 'indexed')
            RETURNING id
            """
        ),
        {"title": row.title, "body": body, "language": language},
    )
    return inserted.mappings().first()["id"]


async def upsert_chunks(
    session: AsyncSession, article_id: str, chunks: list[Chunk], vectors: list[list[float]]
) -> None:
    await session.execute(text("DELETE FROM kb_chunks WHERE article_id = :article_id"), {"article_id": article_id})
    for chunk, vector in zip(chunks, vectors):
        await session.execute(
            text(
                """
                INSERT INTO kb_chunks
                    (article_id, content, chunk_index, char_start, char_end, section_path, embedding)
                VALUES
                    (:article_id, :content, :chunk_index, :char_start, :char_end, :section_path, (:embedding)::vector)
                """
            ),
            {
                "article_id": article_id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "section_path": chunk.section_path or None,
                "embedding": str(vector),
            },
        )


async def ingest_source(session: AsyncSession, row: SourceRow) -> int:
    """Parse → chunk → embed → upsert one manifest source. Returns chunks written."""
    body = parse_source(row)
    if not body.strip():
        return 0

    chunks = chunk_document(body, source_id=row.source_id)
    if not chunks:
        return 0

    article_id = await upsert_article(session, row, body)
    vectors = embed_texts([c.content for c in chunks])
    await upsert_chunks(session, article_id, chunks, vectors)
    return len(chunks)


async def run_ingestion() -> None:
    async with get_session() as session:
        await ensure_schema(session)
        total = 0
        for row in load_approved_sources():
            total += await ingest_source(session, row)
        await session.commit()
        print(f"Ingested {total} chunks from approved sources.")


if __name__ == "__main__":
    asyncio.run(run_ingestion())
