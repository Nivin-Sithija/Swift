"""Offline and live diagnostics for the consumer RAG pipeline.

This package is analysis instrumentation, not production code. It lives outside
`app/` deliberately: the workstream measures the pipeline as it stands, so nothing
here may be imported by `app/`, and the CI lint/type gates (`ruff check app tests`,
`mypy app`) do not cover it.

Every component is exercised through the real production seams -- `consumer_rag_service`,
`PostgresHybridRetriever`, and the `Embedder`/`Reranker`/`LLMProvider` protocols -- so
that measurements describe the shipped system rather than a reimplementation of it.
"""
