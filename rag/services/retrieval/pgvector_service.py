from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings

_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    async with _session_factory() as session:
        yield session


async def ensure_schema(session: AsyncSession) -> None:
    """Create the pgvector extension and kb_articles/kb_chunks if they don't exist yet.

    kb_articles/kb_chunks are the eventual FastAPI backend's tables (see
    context/architecture.md); this pipeline runs ahead of api/ existing, so it
    owns creating them until the alembic migration for api/ takes over.
    """
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS kb_articles (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                title text NOT NULL,
                body text NOT NULL,
                language text NOT NULL,
                source text NOT NULL,
                status text NOT NULL DEFAULT 'pending',
                created_at timestamptz NOT NULL DEFAULT now(),
                updated_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
    )
    await session.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS kb_chunks (
                id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                article_id uuid NOT NULL REFERENCES kb_articles(id) ON DELETE CASCADE,
                content text NOT NULL,
                chunk_index int NOT NULL,
                char_start int NOT NULL,
                char_end int NOT NULL,
                section_path text,
                embedding vector({settings.EMBEDDING_DIM}) NOT NULL,
                created_at timestamptz NOT NULL DEFAULT now(),
                UNIQUE (article_id, chunk_index)
            )
            """
        )
    )
    await session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS kb_chunks_embedding_hnsw "
            "ON kb_chunks USING hnsw (embedding vector_cosine_ops)"
        )
    )
    await session.commit()


async def retrieve(session: AsyncSession, query_vec: list[float], k: int = 5):
    """Top-k chunks by cosine distance — the locators (see Vector Retrieval Pattern in architecture.md)."""
    rows = await session.execute(
        text(
            """
            SELECT id, article_id, content, chunk_index,
                   char_start, char_end, section_path,
                   1 - (embedding <=> (:qv)::vector) AS score
            FROM kb_chunks
            ORDER BY embedding <=> (:qv)::vector
            LIMIT :k
            """
        ),
        {"qv": str(query_vec), "k": k},
    )
    return rows.mappings().all()


async def widen(session: AsyncSession, hits, mode: str = "article"):
    """Locators → generation context. mode='article' widens to kb_articles.body; dedupes by article."""
    if mode != "article":
        raise NotImplementedError(f"widen mode '{mode}' not implemented")

    article_ids = list({hit["article_id"] for hit in hits})
    if not article_ids:
        return []

    rows = await session.execute(
        text("SELECT id, title, body FROM kb_articles WHERE id = ANY(:ids)"),
        {"ids": article_ids},
    )
    return rows.mappings().all()
