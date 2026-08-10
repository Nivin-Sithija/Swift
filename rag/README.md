# rag/ — RAG ingestion + retrieval pipeline

```text
rag/
  config.py                     Settings: Groq/Gemini keys, DATABASE_URL, embedding model
  sources/
    raw/                        Original source documents as fetched (HTML today; pdf/docx/
                                 pptx/txt loaders are ready for when new formats arrive)
    rag_source_manifest.csv     One row per source: id, category, language, url, owner,
                                 approval_status, version, local_path, cleaned_path, checksum
  ingestion/
    loaders/                    Per-format text extraction — html.py, pdf.py, text.py, office.py
                                 — plus manifest.py (reads rag_source_manifest.csv, filters to
                                 approval_status == approved)
    chunking/
      splitter.py                Structure-aware chunker: splits on Markdown-style headings
                                  (loaders re-emit HTML headings as '#'..'######') and paragraph
                                  boundaries, never fixed character counts. Tracks section_path
                                  and char_start/char_end into the parsed body.
    processor.py                 Orchestrates: manifest -> loader -> chunker -> embed -> upsert
                                  into Postgres (kb_articles / kb_chunks). Run directly:
                                  `python -m ingestion.processor`
  services/
    retrieval/
      embedding.py                Local multilingual embeddings (BGE-M3, 1024-dim; falls back to
                                   multilingual-e5-large, also 1024-dim, so it never breaks the
                                   fixed-width pgvector column)
      pgvector_service.py         Async SQLAlchemy engine, schema bootstrap (CREATE EXTENSION
                                   vector + kb_articles/kb_chunks + HNSW index), retrieve()/widen()
                                   — the small-to-big vector retrieval pattern
      ranking_service.py          FlashRank local cross-encoder reranking of retrieval hits
```

## Pipeline stage

Ingestion (loaders → chunking → embedding → pgvector) and retrieval are implemented and
importable — run `pytest`-free smoke checks by importing `ingestion.loaders`,
`ingestion.chunking`, `services.retrieval` directly. `processor.py`'s DB writes and
`embedding.py`'s model load are **not exercised in CI here** — they need a reachable
`DATABASE_URL` (Postgres + `pgvector` extension) and a local download of the embedding
model, neither of which is provisioned in this workspace yet.

This pipeline runs ahead of the FastAPI backend described in
[`context/architecture.md`](../context/architecture.md): it owns creating `kb_articles`/
`kb_chunks` for now (`pgvector_service.ensure_schema`), matching the exact schema documented
there, so it can hand off to `api/`'s alembic migration without a data model change once that
backend exists. Generation (`api/pipeline/rag.py`, the LLM answer draft) is still not built.

Run everything with `rag/` as the working directory (its own `.venv`) — packages import bare,
e.g. `from ingestion.chunking import chunk_document`, matching the `ml/swiftbench` convention
elsewhere in this repo rather than being prefixed with `rag.`.

## Adding a new source

1. Save the raw document to `sources/raw/<category>_<owner>_<slug>.<ext>`.
2. Add a row to `rag_source_manifest.csv` (`source_id`, `title`, `category`,
   `language`, `source_url`, `owner`, `approval_status`, `version`,
   `last_reviewed`, `local_path`) — leave `cleaned_path`/`checksum` blank
   until the ingestion pipeline fills them in.

Only `approved` sources should be treated as eligible for retrieval —
`pending_internal_review` sources are staged, not live.
