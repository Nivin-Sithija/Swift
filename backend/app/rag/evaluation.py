"""Provider-independent multilingual RAG evaluation metrics and runner contracts."""

import math
import statistics
from dataclasses import dataclass


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    return len(set(retrieved[:k]) & relevant) / len(relevant) if relevant else 1.0


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    return next((1 / rank for rank, item in enumerate(retrieved, 1) if item in relevant), 0.0)


def ndcg_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    # Each relevant item earns gain once, at its best rank. `retrieved` is chunk-level and
    # several chunks routinely resolve to the same source id, so counting every occurrence let
    # DCG exceed the ideal -- ndcg@5(["a","a","a","b","c"], {"a"}) returned 2.13 on a metric
    # defined to be bounded in [0, 1]. The ideal is built from distinct items, so the DCG has
    # to be too.
    seen: set[str] = set()
    dcg = 0.0
    for rank, item in enumerate(retrieved[:k], 1):
        if item in relevant and item not in seen:
            seen.add(item)
            dcg += 1 / math.log2(rank + 1)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(relevant)) + 1))
    # No relevant items defined: nothing was retrievable, so this scores as vacuously perfect
    # (matching `recall_at_k`). It is free credit in the mean -- keep such queries out of the
    # evaluation set rather than relying on this branch.
    return dcg / ideal if ideal else 1.0


@dataclass(frozen=True)
class EvaluationRecord:
    language: str
    category: str
    expected_route: str
    actual_route: str
    relevant_chunks: set[str]
    retrieved_chunks: list[str]
    faithfulness: float
    relevance: float
    citation_correctness: float
    language_correct: bool
    unsafe_answer: bool
    latency_ms: float


def summarize(records: list[EvaluationRecord], k: int = 5) -> dict[str, float]:
    if not records:
        return {}
    mean = statistics.fmean
    return {
        f"recall@{k}": mean(recall_at_k(r.retrieved_chunks, r.relevant_chunks, k) for r in records),
        "mrr": mean(reciprocal_rank(r.retrieved_chunks, r.relevant_chunks) for r in records),
        f"ndcg@{k}": mean(ndcg_at_k(r.retrieved_chunks, r.relevant_chunks, k) for r in records),
        "answer_faithfulness": mean(r.faithfulness for r in records),
        "answer_relevance": mean(r.relevance for r in records),
        "citation_correctness": mean(r.citation_correctness for r in records),
        "language_correctness": mean(float(r.language_correct) for r in records),
        "refusal_escalation_accuracy": mean(float(r.expected_route == r.actual_route) for r in records),
        "latency_ms_mean": mean(r.latency_ms for r in records),
        "latency_ms_p95": sorted(r.latency_ms for r in records)[max(0, math.ceil(len(records) * 0.95) - 1)],
        "unsafe_answer_rate": mean(float(r.unsafe_answer) for r in records),
    }


def slice_summary(records: list[EvaluationRecord]) -> dict[str, dict[str, dict[str, float]]]:
    languages = sorted({r.language for r in records})
    categories = sorted({r.category for r in records})
    return {
        "language": {key: summarize([r for r in records if r.language == key]) for key in languages},
        "category": {key: summarize([r for r in records if r.category == key]) for key in categories},
    }
