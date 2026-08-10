from __future__ import annotations

from flashrank import Ranker, RerankRequest

_ranker: Ranker | None = None


def _get_ranker() -> Ranker:
    """FlashRank's local ONNX cross-encoder (ms-marco-MiniLM-L-6-v2) — lazy so import cost is paid once, on first use."""
    global _ranker
    if _ranker is None:
        _ranker = Ranker()
    return _ranker


def rerank_documents(query: str, documents: list[str], top_n: int = 5) -> list[str]:
    """Cross-encoder re-score of vector-search hits — cosine similarity is fast but fuzzy; this is slower but precise."""
    if not documents:
        return []

    passages = [{"id": i, "text": doc} for i, doc in enumerate(documents)]
    results = _get_ranker().rerank(RerankRequest(query=query, passages=passages))
    return [r["text"] for r in results[:top_n]]
