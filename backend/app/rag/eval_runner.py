"""Runs the golden set and guardrail probes through the real RAG service.

Requires a reachable DATABASE_URL with an ingested knowledge base and a configured
generation provider. Writes a timestamped JSON report under backend/evaluation/reports/.
"""

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import SessionLocal, engine
from app.rag.dependencies import consumer_rag_service
from app.rag.evaluation import EvaluationRecord, slice_summary, summarize
from app.rag.judge import judge_answer
from app.rag.providers import FallbackProvider, GeminiProvider, GroqProvider
from app.rag.service import ConsumerRAGService, Retriever
from app.rag.types import Evidence, LLMProvider, QueryContext, RetrievalResult

EVALUATION_DIR = Path(__file__).resolve().parents[2] / "evaluation"
GOLDEN_CASES = EVALUATION_DIR / "multilingual_cases.jsonl"
GUARDRAIL_CASES = EVALUATION_DIR / "guardrail_cases.jsonl"
REPORT_DIR = EVALUATION_DIR / "reports"
# Grading carries the full evidence text, so it needs a longer budget than a
# customer-facing generation call.
JUDGE_TIMEOUT_SECONDS = 90.0


class RecordingRetriever:
    """Wraps the real retriever so the harness can grade the evidence without retrieving twice."""

    def __init__(self, inner: Retriever) -> None:
        self.inner = inner
        self.last_result: RetrievalResult | None = None

    async def retrieve(self, context: QueryContext) -> RetrievalResult:
        self.last_result = await self.inner.retrieve(context)
        return self.last_result


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _instrumented(
    db: AsyncSession, settings: Settings
) -> tuple[ConsumerRAGService, RecordingRetriever]:
    service = consumer_rag_service(db, settings)
    recorder = RecordingRetriever(service.retriever)
    return ConsumerRAGService(recorder, service.llm), recorder


def _judge_provider(settings: Settings) -> LLMProvider:
    retries = settings.rag_provider_max_retries
    backoff = settings.rag_provider_retry_base_delay_seconds
    primary = GroqProvider(
        settings.groq_api_key or "", settings.groq_model, JUDGE_TIMEOUT_SECONDS, retries, backoff
    )
    fallback = (
        GeminiProvider(
            settings.gemini_api_key, settings.gemini_model, JUDGE_TIMEOUT_SECONDS, retries, backoff
        )
        if settings.gemini_api_key
        else None
    )
    return FallbackProvider(primary, fallback)


async def run_golden_cases(path: Path = GOLDEN_CASES) -> list[EvaluationRecord]:
    """Entry points dispose the pool: it binds to the running loop, so a later
    asyncio.run() (or a second pytest test) would otherwise inherit dead connections."""
    try:
        return (await _golden_cases(path))[0]
    finally:
        await engine.dispose()


async def _golden_cases(path: Path) -> tuple[list[EvaluationRecord], int]:
    cases = load_cases(path)
    settings = get_settings()
    judge = _judge_provider(settings)
    records: list[EvaluationRecord] = []
    judge_failures = 0
    async with SessionLocal() as db:
        service, recorder = _instrumented(db, settings)
        for case in cases:
            recorder.last_result = None
            started = time.perf_counter()
            result = await service.assist(
                query=case["query"],
                institution=case.get("institution"),
                category=case.get("category"),
                language=case.get("language"),
            )
            latency_ms = (time.perf_counter() - started) * 1000
            evidence: list[Evidence] = (
                recorder.last_result.evidence if recorder.last_result else []
            )
            # relevant_sources are document ids, so score against source_id — chunk_id is a
            # per-chunk uuid4 minted at ingest and can never match the golden set.
            retrieved = [item.source_id for item in evidence]
            judged = None
            if result.draft:
                judged = await judge_answer(
                    judge,
                    query=case["query"],
                    answer=result.draft,
                    evidence_text="\n\n".join(
                        f"[E{index}] {item.text}" for index, item in enumerate(evidence, 1)
                    ),
                )
                judge_failures += judged is None
            records.append(
                EvaluationRecord(
                    language=case["language"],
                    category=case.get("category", "unknown"),
                    expected_route=case["expected_route"],
                    actual_route=result.route,
                    relevant_chunks=set(case.get("relevant_sources", [])),
                    retrieved_chunks=retrieved,
                    faithfulness=judged.faithfulness if judged else 0.0,
                    relevance=judged.relevance if judged else 0.0,
                    citation_correctness=judged.citation_correctness if judged else 0.0,
                    language_correct=result.language == case["language"],
                    unsafe_answer=judged.unsafe if judged else False,
                    latency_ms=latency_ms,
                )
            )
    return records, judge_failures


async def run_guardrail_cases(path: Path = GUARDRAIL_CASES) -> list[dict[str, Any]]:
    try:
        return await _guardrail_cases(path)
    finally:
        await engine.dispose()


async def _guardrail_cases(path: Path) -> list[dict[str, Any]]:
    cases = load_cases(path)
    settings = get_settings()
    probes: list[dict[str, Any]] = []
    async with SessionLocal() as db:
        service, _ = _instrumented(db, settings)
        for case in cases:
            result = await service.assist(
                query=case["query"],
                institution=case.get("institution"),
                language=case.get("language"),
            )
            probes.append(
                {
                    "id": case["id"],
                    "expected_route": case["expected_route"],
                    "actual_route": result.route,
                    "escalation_reason": result.escalation_reason,
                    "passed": result.route == case["expected_route"],
                }
            )
    return probes


def build_report(
    records: list[EvaluationRecord], probes: list[dict[str, Any]], judge_failures: int = 0
) -> dict[str, Any]:
    return {
        "golden_set": {
            "cases": len(records),
            # Ungraded cases score 0.0, so a non-zero count here means the answer-quality
            # metrics are floors, not measurements.
            "judge_failures": judge_failures,
            "overall": summarize(records),
            "slices": slice_summary(records),
        },
        "guardrail_probes": {
            "cases": len(probes),
            "passed": sum(probe["passed"] for probe in probes),
            "results": probes,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the RAG pipeline against the golden set")
    parser.add_argument("--golden", type=Path, default=GOLDEN_CASES)
    parser.add_argument("--guardrails", type=Path, default=GUARDRAIL_CASES)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    async def both() -> tuple[list[EvaluationRecord], int, list[dict[str, Any]]]:
        try:
            records, failures = await _golden_cases(args.golden)
            return records, failures, await _guardrail_cases(args.guardrails)
        finally:
            # Must dispose on this loop; a second asyncio.run() would find it closed.
            await engine.dispose()

    records, judge_failures, probes = asyncio.run(both())
    report = build_report(records, probes, judge_failures)

    destination = args.out or REPORT_DIR / f"rag_eval_{time.strftime('%Y%m%dT%H%M%S')}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report["golden_set"]["overall"], indent=2))
    print(f"guardrail probes passed: {report['guardrail_probes']['passed']}/{len(probes)}")
    print(f"report: {destination}")


if __name__ == "__main__":
    main()
