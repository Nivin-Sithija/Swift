"""Approved knowledge metadata, PostgreSQL FTS, and pgvector HNSW retrieval."""

from alembic import op

revision = "0006_consumer_rag"
down_revision = "0005_repair_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
        CREATE TABLE knowledge_articles (
            id uuid PRIMARY KEY, source_id varchar(80) NOT NULL UNIQUE,
            title text NOT NULL, source_url text NOT NULL, institution varchar(200) NOT NULL,
            category varchar(100) NOT NULL, language varchar(30) NOT NULL,
            source_authority varchar(30) NOT NULL CHECK (source_authority IN ('bank_official','cbsl_official')),
            version varchar(50) NOT NULL, review_date date NOT NULL,
            approval_status varchar(30) NOT NULL CHECK (approval_status IN ('pending','approved','rejected','expired')),
            checksum varchar(64) NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE knowledge_chunks (
            id uuid PRIMARY KEY, article_id uuid NOT NULL REFERENCES knowledge_articles(id) ON DELETE CASCADE,
            chunk_index integer NOT NULL, section_path text NOT NULL, content text NOT NULL,
            embedding vector(1024) NOT NULL,
            search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
            UNIQUE(article_id, chunk_index)
        )
    """)
    op.execute("CREATE INDEX ix_kb_article_scope ON knowledge_articles (institution, category, language, approval_status)")
    op.execute("CREATE INDEX ix_kb_chunk_fts ON knowledge_chunks USING gin (search_vector)")
    op.execute("CREATE INDEX ix_kb_chunk_embedding_hnsw ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_chunks")
    op.execute("DROP TABLE IF EXISTS knowledge_articles")
