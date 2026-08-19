from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import Db
from app.core.config import Settings, get_settings
from app.rag.models import FlashRankReranker, build_embedder
from app.rag.providers import FallbackProvider, GeminiProvider, GroqProvider
from app.rag.retrieval import PostgresHybridRetriever
from app.rag.service import ConsumerRAGService
from app.rag.types import Embedder


@lru_cache
def model_components() -> tuple[Embedder, FlashRankReranker]:
    settings = get_settings()
    return build_embedder(
        provider=settings.rag_embedding_provider,
        model_name=settings.rag_embedding_model,
        dimensions=settings.rag_embedding_dimensions,
        timeout=settings.rag_request_timeout_seconds,
        huggingface_token=settings.huggingface_token,
        huggingface_provider=settings.huggingface_provider,
        huggingface_endpoint_url=settings.huggingface_endpoint_url,
    ), FlashRankReranker()


def provider(settings: Settings) -> FallbackProvider:
    if not settings.groq_api_key:
        raise HTTPException(503, "RAG generation is not configured")
    primary = GroqProvider(settings.groq_api_key, settings.groq_model, settings.rag_request_timeout_seconds)
    fallback = GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.rag_request_timeout_seconds) if settings.gemini_api_key else None
    return FallbackProvider(primary, fallback)


def consumer_rag_service(db: AsyncSession, settings: Settings) -> ConsumerRAGService:
    try:
        embedder, reranker = model_components()
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    retriever = PostgresHybridRetriever(db, embedder, reranker,
        candidate_limit=settings.rag_candidate_limit, final_limit=settings.rag_final_limit,
        min_confidence=settings.rag_min_confidence,
        review_max_age_days=settings.rag_review_max_age_days)
    return ConsumerRAGService(retriever, provider(settings))


def get_consumer_rag_service(db: Db) -> ConsumerRAGService:
    return consumer_rag_service(db, get_settings())


ConsumerRAG = Annotated[ConsumerRAGService, Depends(get_consumer_rag_service)]
