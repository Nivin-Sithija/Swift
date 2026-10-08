import logging
import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.types import Embedder, Evidence, QueryContext, Reranker, RetrievalResult

logger = logging.getLogger(__name__)

# Function words that would otherwise match nearly every chunk once search words are
# OR-ed together. The index uses the 'simple' configuration, which keeps them.
LEXICAL_STOPWORDS = frozenset(
    "a an and are be can did do does for from has have how i in is it me my not of on "
    "or please the this that to was what when where who why will with you your".split()
)
# websearch_to_tsquery reads quotes as phrases and a leading "-" as NOT.
LEXICAL_STRIP = "\"'-.,;:!?()[]{}<>/\\|`~@#$%^&*+=_"


def lexical_query(text: str) -> str:
    """Match chunks containing any meaningful search word, not every word.

    websearch_to_tsquery joins plain words with AND, so a full ticket sentence
    matched almost nothing. Splitting on whitespace (not regex \\w) keeps Sinhala and Tamil
    words whole, since their vowel signs are not word characters.
    """
    words = [word.strip(LEXICAL_STRIP).lower() for word in text.split()]
    kept = [word for word in words if len(word) > 2 and word not in LEXICAL_STOPWORDS]
    return " or ".join(dict.fromkeys(kept)) or text


def reciprocal_rank_fusion(
    rankings: list[list[Evidence]], *, k: int = 60, limit: int = 20
) -> list[Evidence]:
    scores: dict[str, float] = defaultdict(float)
    items: dict[str, Evidence] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            scores[item.chunk_id] += 1.0 / (k + rank)
            existing = items.get(item.chunk_id)
            if existing is None:
                items[item.chunk_id] = item
            else:
                # A chunk can appear in both dense and lexical rankings. Preserve
                # both scores instead of letting the last channel erase the first.
                items[item.chunk_id] = replace(
                    existing,
                    dense_score=max(existing.dense_score, item.dense_score),
                    lexical_score=max(existing.lexical_score, item.lexical_score),
                )
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
            await self._query(
                "lexical", query, {**params, "query": lexical_websearch_query(query)}
            )
            for query in query_variants
        ]
        # Ticket classifier labels are finer-grained than knowledge-base categories
        # and may also be "unknown". If category filtering yields nothing, retry
        # every retrieval channel across all approved source categories.
        if context.category and not dense and not any(lexical_rankings):
            broad_params = {**params, "category": None}
            dense = (
                await self._query("dense", context.normalized_query, broad_params)
                if embedding is not None
                else []
            )
            lexical_rankings = [
                await self._query(
                    "lexical", query, {**broad_params, "query": lexical_websearch_query(query)}
                )
                for query in query_variants
            ]
        fused = reciprocal_rank_fusion([dense, *lexical_rankings], limit=self.candidate_limit)
        reranked = (await self.reranker.rerank(context.normalized_query, fused))[: self.final_limit]
        expanded = await self._expand_neighbors(reranked)
        confidence = evidence_confidence(reranked, expected_category=context.category)
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

    async def _query(
        self, mode: str, query: str, params: Mapping[str, object]
    ) -> list[Evidence]:
        # Every caller-supplied value is a bound parameter (:embedding, :query,
        # :limit, :institution, :category, :review_days). Pinned by
        # tests/database/test_integrity.py::test_retrieval_sql_interpolates_no_caller_data.
        if mode == "dense":
            sql = """SELECT c.id::text AS chunk_id, a.source_id, a.title, a.source_url,
                a.institution, a.category, a.language, a.source_authority, a.version,
                a.review_date, a.approval_status, c.chunk_index, c.content,
                1 - (c.embedding <=> CAST(:embedding AS vector)) AS score
                FROM knowledge_chunks c JOIN knowledge_articles a ON a.id=c.article_id
                WHERE a.approval_status = 'approved'
                  AND a.review_date >= CURRENT_DATE - CAST(:review_days AS integer)
                  AND (CAST(:institution AS text) IS NULL OR a.institution = CAST(:institution AS text))
                  AND (CAST(:category AS text) IS NULL OR a.category = CAST(:category AS text))
                ORDER BY c.embedding <=> CAST(:embedding AS vector) LIMIT :limit"""
        else:
            sql = """SELECT c.id::text AS chunk_id, a.source_id, a.title, a.source_url,
                a.institution, a.category, a.language, a.source_authority, a.version,
                a.review_date, a.approval_status, c.chunk_index, c.content,
                ts_rank_cd(c.search_vector, websearch_to_tsquery('simple', :query)) AS score
                FROM knowledge_chunks c JOIN knowledge_articles a ON a.id=c.article_id
                WHERE a.approval_status = 'approved'
                  AND a.review_date >= CURRENT_DATE - CAST(:review_days AS integer)
                  AND (CAST(:institution AS text) IS NULL OR a.institution = CAST(:institution AS text))
                  AND (CAST(:category AS text) IS NULL OR a.category = CAST(:category AS text))
                  AND c.search_vector @@ websearch_to_tsquery('simple', :query)
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
        # Keep ranked seeds first, then add only unique neighboring context.
        # Capping this list prevents provider request/token-limit failures.
        expanded = list(selected)
        seen = set(selected_ids)
        limit = self.final_limit + 3
        for row in rows:
            chunk_id = row["chunk_id"]
            if chunk_id in seen:
                continue
            expanded.append(
                replace(
                    self._evidence({**dict(row), "score": 0}, "dense"),
                    is_neighbor=True,
                )
            )
            seen.add(chunk_id)
            if len(expanded) >= limit:
                break
        return expanded


def evidence_confidence(
    evidence: list[Evidence], *, expected_category: str | None = None
) -> float:
    """Calibrated multilingual relevance score for the selected evidence set.

    BGE-M3 is multilingual while the compact FlashRank model is English-biased, so
    dense relevance is the primary signal and reranking is only a small bonus. The
    best selected score is used because reranking can move a relevant Sinhala/Tamil
    chunk below an English distractor without removing it from the prompt.
    """
    if not evidence:
        return 0.0
    rerank = max(max(0.0, min(1.0, item.rerank_score)) for item in evidence)
    dense = max(max(0.0, min(1.0, item.dense_score)) for item in evidence)
    # Three input rankings contribute at most approximately 3 / (60 + 1) at rank one.
    rrf = max(
        max(0.0, min(1.0, item.fused_score / (3.0 / 61.0))) for item in evidence
    )
    category_agreement = 0.05 if expected_category and any(
        item.category == expected_category for item in evidence
    ) else 0.0
    return round(min(1.0, 0.85 * dense + 0.10 * rrf + 0.05 * rerank + category_agreement), 4)


def lexical_websearch_query(query: str) -> str:
    """Build a bound OR query so one unmatched conversational word cannot erase a hit."""
    terms = list(
        dict.fromkeys(
            "".join(
                character
                for character in raw
                if unicodedata.category(character)[0] in {"L", "M", "N"}
            )
            for raw in re.split(r"\s+", query.casefold())
        )
    )
    useful = [term for term in terms if len(term) > 1]
    return " OR ".join(useful) or query
