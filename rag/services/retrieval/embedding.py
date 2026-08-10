from __future__ import annotations

from config import settings

_model = None


def _load_model():
    from sentence_transformers import SentenceTransformer

    try:
        return SentenceTransformer(settings.EMBEDDING_MODEL)
    except Exception:
        return SentenceTransformer(settings.EMBEDDING_FALLBACK_MODEL)


def _get_model():
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def embed_query(query: str) -> list[float]:
    return _get_model().encode(query, normalize_embeddings=True).tolist()


def embed_texts(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    embeddings = _get_model().encode(
        texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False
    )
    return embeddings.tolist()
