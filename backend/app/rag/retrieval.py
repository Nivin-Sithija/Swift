import logging
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.types import Embedder, Evidence, QueryContext, Reranker, RetrievalResult

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    rankings: list[list[Evidence]], *, k: int = 60, limit: int = 20
) -> list[Evidence]:
    scores: dict[str, float] = defaultdict(float)
    items: dict[str, Evidence] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            scores[item.chunk_id] += 1.0 / (k + rank)
            items[item.chunk_id] = item
    ordered = sorted(scores, key=lambda key: (-scores[key], key))[:limit]
    return [replace(items[key], fused_score=scores[key]) for key in ordered]


class PostgresHybridRetriever:
    def __init__(
        self,
        db: AsyncSession,
        embedder: Embedder,
        reranker: Reranker,
        *,
        candidate_limit: int = 20,
        final_limit: int = 5,
        min_confidence: float = 0.55,
        review_max_age_days: int = 365,
    ) -> None:
        self.db, self.embedder, self.reranker = db, embedder, reranker
        self.candidate_limit, self.final_limit = candidate_limit, final_limit
        self.min_confidence = min_confidence
        self.review_max_age_days = review_max_age_days

    async def retrieve(self, context: QueryContext) -> RetrievalResult:
        query_variants = list(dict.fromkeys((context.original_query, context.normalized_query)))
        embedding: list[float] | None = None
        embedding_error: str | None = None
        try:
            embedding = await self.embedder.embed_query(context.normalized_query)
        except RuntimeError as exc:
            # Hosted embeddings are an enhancement, not a reason to make customer
            # assistance unavailable. PostgreSQL FTS remains a grounded retriever.
            embedding_error = type(exc).__name__
            logger.warning("Dense embedding unavailable; using lexical retrieval", exc_info=True)
        params = {
            "embedding": str(embedding) if embedding is not None else None,
            "limit": self.candidate_limit,
            "institution": context.institution,
            "category": context.category,
            "review_days": self.review_max_age_days,
        }
        dense = (
            await self._query("dense", context.normalized_query, params)
            if embedding is not None
            else []
        )
        lexical_rankings = [
            await self._query("lexical", query, {**params, "query": query})
            for query in query_variants
        ]
        # Ticket classifier labels are finer-grained than knowledge-base categories.
        # If an exact category yields nothing, retry approved sources without it.
        if context.category and not any(lexical_rankings):
            lexical_rankings = [
                await self._query("lexical", query, {**params, "query": query, "category": None})
                for query in query_variants
            ]
        fused = reciprocal_rank_fusion([dense, *lexical_rankings], limit=self.candidate_limit)
        reranked = (await self.reranker.rerank(context.normalized_query, fused))[: self.final_limit]
        expanded = await self._expand_neighbors(reranked)
        confidence = evidence_confidence(reranked)
        return RetrievalResult(
            expanded if confidence >= self.min_confidence else [],
            confidence,
            {
                "dense": len(dense),
                "lexical": sum(map(len, lexical_rankings)),
                "fused": len(fused),
                "selected": len(reranked),
                "embedding_fallback": embedding_error or "none",
            },
        )

    async def _query(self, mode: str, query: str, params: dict[str, object]) -> list[Evidence]:
        filters = "a.approval_status = 'approved' AND a.review_date >= CURRENT_DATE - CAST(:review_days AS integer) AND (CAST(:institution AS text) IS NULL OR a.institution = CAST(:institution AS text)) AND (CAST(:category AS text) IS NULL OR a.category = CAST(:category AS text))"
        if mode == "dense":
            sql = f"""SELECT c.id::text AS chunk_id, a.source_id, a.title, a.source_url,
                a.institution, a.category, a.language, a.source_authority, a.version,
                a.review_date, a.approval_status, c.chunk_index, c.content,
                1 - (c.embedding <=> CAST(:embedding AS vector)) AS score
                FROM knowledge_chunks c JOIN knowledge_articles a ON a.id=c.article_id
                WHERE {filters} ORDER BY c.embedding <=> CAST(:embedding AS vector) LIMIT :limit"""
        else:
            sql = f"""SELECT c.id::text AS chunk_id, a.source_id, a.title, a.source_url,
                a.institution, a.category, a.language, a.source_authority, a.version,
                a.review_date, a.approval_status, c.chunk_index, c.content,
                ts_rank_cd(c.search_vector, websearch_to_tsquery('simple', :query)) AS score
                FROM knowledge_chunks c JOIN knowledge_articles a ON a.id=c.article_id
                WHERE {filters} AND c.search_vector @@ websearch_to_tsquery('simple', :query)
                ORDER BY score DESC LIMIT :limit"""
        rows = (await self.db.execute(text(sql), params)).mappings().all()
        return [self._evidence(row, mode) for row in rows]

    @staticmethod
    def _evidence(row: Mapping[Any, Any], mode: str) -> Evidence:
        values = dict(row)
        score = float(values.pop("score") or 0)
        values["text"] = values.pop("content")
        values[f"{mode}_score"] = score
        return Evidence(**values)

    async def _expand_neighbors(self, selected: list[Evidence]) -> list[Evidence]:
        if not selected:
            return []
        ids = [item.chunk_id for item in selected]
        sql = """SELECT n.id::text AS chunk_id, a.source_id, a.title, a.source_url,
            a.institution, a.category, a.language, a.source_authority, a.version,
            a.review_date, a.approval_status, n.chunk_index, n.content
            FROM knowledge_chunks seed
            JOIN knowledge_chunks n ON n.article_id=seed.article_id
              AND n.chunk_index BETWEEN seed.chunk_index-1 AND seed.chunk_index+1
            JOIN knowledge_articles a ON a.id=n.article_id
            WHERE seed.id = ANY(CAST(:ids AS uuid[])) AND a.approval_status='approved'
            ORDER BY a.source_id, n.chunk_index"""
        rows = (await self.db.execute(text(sql), {"ids": ids})).mappings().all()
        selected_ids = set(ids)
        return [
            replace(
                self._evidence({**dict(row), "score": 0}, "dense"),
                is_neighbor=row["chunk_id"] not in selected_ids,
            )
            for row in rows
        ]


def evidence_confidence(evidence: list[Evidence]) -> float:
    """Deterministic quality score; never asks the LLM to grade itself."""
    if not evidence:
        return 0.0
    top = evidence[0]
    rerank = max(0.0, min(1.0, top.rerank_score))
    retrieval = max(0.0, min(1.0, top.dense_score or top.lexical_score or top.fused_score * 30))
    authority = sum(
        e.approval_status == "approved" and bool(e.source_authority) for e in evidence
    ) / len(evidence)
    coherence = max(sum(e.institution == top.institution for e in evidence) / len(evidence), 0.0)
    return round(0.45 * rerank + 0.30 * retrieval + 0.15 * authority + 0.10 * coherence, 4)
