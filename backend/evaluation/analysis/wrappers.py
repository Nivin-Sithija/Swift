"""Phase 3 -- timing and recording wrappers, plus configuration ablations.

No production code is modified. Every seam used here already exists:

  * `consumer_rag_service` takes a `Settings` object, so a configuration sweep is a
    `settings.model_copy(update=...)` (dependencies.py:40).
  * `PostgresHybridRetriever.__init__` takes the embedder and reranker as arguments
    (retrieval.py:29), so the harness builds its own retriever from wrapped components
    rather than mutating the `@lru_cache`d singletons in `model_components()`.
  * `Embedder`, `Reranker` and `LLMProvider` are structural Protocols (types.py:76-86),
    so a wrapper only needs matching methods.

Latency decomposition
---------------------
`embed`, `rerank` and `generate` are measured directly. The remaining retrieval cost --
SQL, reciprocal-rank fusion and neighbour expansion -- is *derived* as
`retrieve_total - embed - rerank`, and is reported as derived rather than measured.
Wrapper timing also excludes FastAPI middleware and connection-pool acquisition, so
these numbers are a floor on real request latency, not the whole of it.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from app.core.config import Settings
from app.rag.dependencies import model_components, provider
from app.rag.retrieval import PostgresHybridRetriever
from app.rag.service import ConsumerRAGService
from app.rag.types import Embedder, Evidence, LLMProvider, QueryContext, Reranker, RetrievalResult


class StageTimer:
    """Collects per-stage durations for a single probe."""

    def __init__(self) -> None:
        self.stages: dict[str, float] = {}
        self.retrieval: RetrievalResult | None = None
        self.embedding_dimensions: int | None = None
        # The reranker's output is the only place the *ranked* evidence is visible.
        # RetrievalResult.evidence is emptied when confidence < min_confidence
        # (retrieval.py:91), so reading only that conflates "retrieval never found the
        # document" with "the gate discarded it" -- two different failures with two
        # different fixes.
        self.ranked: list[Evidence] = []
        self.final_limit: int = 5

    def record(self, stage: str, seconds: float) -> None:
        self.stages[stage] = self.stages.get(stage, 0.0) + seconds * 1000

    def derived(self) -> dict[str, float]:
        retrieve = self.stages.get("retrieve_total", 0.0)
        embed = self.stages.get("embed", 0.0)
        rerank = self.stages.get("rerank", 0.0)
        out = dict(self.stages)
        # Derived, not measured: SQL + fusion + neighbour expansion.
        out["sql_fusion_neighbours_derived"] = round(max(0.0, retrieve - embed - rerank), 3)
        return {key: round(value, 3) for key, value in out.items()}

    def reset(self) -> None:
        self.stages = {}
        self.retrieval = None
        self.ranked = []

    def selected(self) -> list[Evidence]:
        """The evidence retrieval actually chose, before the confidence gate."""
        return self.ranked[: self.final_limit]


class TimedEmbedder:
    def __init__(self, inner: Embedder, timer: StageTimer) -> None:
        self.inner, self.timer = inner, timer

    async def embed_query(self, text: str) -> list[float]:
        started = time.perf_counter()
        try:
            vector = await self.inner.embed_query(text)
        finally:
            self.timer.record("embed", time.perf_counter() - started)
        self.timer.embedding_dimensions = len(vector)
        return vector


class CachingEmbedder:
    """Reuses vectors across configurations so ablations do not re-pay the API cost.

    The query set is identical in every configuration, and the embedding call is ~85% of
    end-to-end latency, so without this a sweep spends almost all its time re-computing
    the same vectors. The first configuration runs cold and therefore carries the honest
    latency numbers; later ones hit the cache, so their timings are understated and are
    reported as such. Retrieval *quality* is unaffected -- the vector is identical.
    """

    _cache: dict[tuple[str, str], list[float]] = {}

    def __init__(self, inner: Embedder, timer: StageTimer, model: str) -> None:
        self.inner, self.timer, self.model = inner, timer, model

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

    @property
    def hit_count(self) -> int:
        return len(self._cache)

    async def embed_query(self, text: str) -> list[float]:
        key = (self.model, text)
        cached = self._cache.get(key)
        if cached is not None:
            self.timer.record("embed", 0.0)
            self.timer.embedding_dimensions = len(cached)
            return cached
        started = time.perf_counter()
        try:
            vector = await self.inner.embed_query(text)
        finally:
            self.timer.record("embed", time.perf_counter() - started)
        self._cache[key] = vector
        self.timer.embedding_dimensions = len(vector)
        return vector


class FailingEmbedder:
    """Ablation: forces the production lexical-only fallback at retrieval.py:49-55.

    RuntimeError is the exact exception that path catches, so this exercises the real
    degradation rather than simulating it.
    """

    def __init__(self, timer: StageTimer) -> None:
        self.timer = timer

    async def embed_query(self, text: str) -> list[float]:
        self.timer.record("embed", 0.0)
        raise RuntimeError("embedding provider disabled for ablation")


class TimedReranker:
    def __init__(self, inner: Reranker, timer: StageTimer) -> None:
        self.inner, self.timer = inner, timer

    async def rerank(self, query: str, evidence: list[Evidence]) -> list[Evidence]:
        started = time.perf_counter()
        try:
            ranked = await self.inner.rerank(query, evidence)
        finally:
            self.timer.record("rerank", time.perf_counter() - started)
        self.timer.ranked = list(ranked)
        return ranked


class IdentityReranker:
    """Ablation: keeps reciprocal-rank-fusion order, isolating the reranker's effect.

    FlashRank's default cross-encoder is English-only, so comparing this against the real
    reranker per language is the direct test of whether reranking helps or hurts
    Sinhala/Tamil retrieval.
    """

    def __init__(self, timer: StageTimer) -> None:
        self.timer = timer

    async def rerank(self, query: str, evidence: list[Evidence]) -> list[Evidence]:
        self.timer.record("rerank", 0.0)
        self.timer.ranked = list(evidence)
        return list(evidence)


class DenseOnlyRetriever(PostgresHybridRetriever):
    """Ablation: suppress the lexical channel. Subclassing, not editing."""

    async def _query(
        self, mode: str, query: str, params: Mapping[str, object]
    ) -> list[Evidence]:
        if mode == "lexical":
            return []
        return await super()._query(mode, query, params)


class LexicalOnlyRetriever(PostgresHybridRetriever):
    """Ablation: suppress the dense channel while keeping a working embedder."""

    async def _query(
        self, mode: str, query: str, params: Mapping[str, object]
    ) -> list[Evidence]:
        if mode == "dense":
            return []
        return await super()._query(mode, query, params)


class TimedRetriever:
    def __init__(self, inner: Any, timer: StageTimer) -> None:
        self.inner, self.timer = inner, timer

    async def retrieve(self, context: QueryContext) -> RetrievalResult:
        started = time.perf_counter()
        try:
            result = await self.inner.retrieve(context)
        finally:
            self.timer.record("retrieve_total", time.perf_counter() - started)
        self.timer.retrieval = result
        return result


class TimedProvider:
    """Wraps the provider and records which one actually answered.

    `FallbackProvider` exposes `last_provider` after a call, so Groq-vs-Gemini failover
    is observable per probe rather than only in aggregate.
    """

    def __init__(self, inner: LLMProvider, timer: StageTimer) -> None:
        self.inner, self.timer = inner, timer
        self.name = inner.name

    @property
    def last_provider(self) -> str:
        return str(getattr(self.inner, "last_provider", self.inner.name))

    async def generate(self, *, system: str, user: str) -> str:
        started = time.perf_counter()
        try:
            return await self.inner.generate(system=system, user=user)
        finally:
            self.timer.record("generate", time.perf_counter() - started)


RETRIEVER_VARIANTS = {
    "hybrid": PostgresHybridRetriever,
    "dense_only": DenseOnlyRetriever,
    "lexical_only": LexicalOnlyRetriever,
}


def build_service(
    db: Any,
    settings: Settings,
    timer: StageTimer,
    *,
    retriever_variant: str = "hybrid",
    disable_embedder: bool = False,
    disable_reranker: bool = False,
    cache_embeddings: bool = False,
    generation_provider: LLMProvider | None = None,
) -> ConsumerRAGService:
    """Assemble the real service from production factories with wrapped components."""
    timer.final_limit = settings.rag_final_limit
    embedder, reranker = model_components()
    wrapped_embedder: Any
    if disable_embedder:
        wrapped_embedder = FailingEmbedder(timer)
    elif cache_embeddings:
        wrapped_embedder = CachingEmbedder(embedder, timer, settings.rag_embedding_model)
    else:
        wrapped_embedder = TimedEmbedder(embedder, timer)
    wrapped_reranker: Any = (
        IdentityReranker(timer) if disable_reranker else TimedReranker(reranker, timer)
    )
    retriever = RETRIEVER_VARIANTS[retriever_variant](
        db,
        wrapped_embedder,
        wrapped_reranker,
        candidate_limit=settings.rag_candidate_limit,
        final_limit=settings.rag_final_limit,
        min_confidence=settings.rag_min_confidence,
        review_max_age_days=settings.rag_review_max_age_days,
    )
    selected_provider = generation_provider or provider(settings)
    return ConsumerRAGService(
        TimedRetriever(retriever, timer), TimedProvider(selected_provider, timer)
    )
