"""Phase 4 -- run the probe set through the real pipeline and record every outcome.

Tiering, because generation is the scarce resource
--------------------------------------------------
This Groq account is on a 1000 output-tokens-per-minute tier, so generation, not
retrieval, sets the pace. The run is therefore tiered:

  --mode retrieval   Retrieval, routing, confidence and per-stage latency, with no
                     LLM-judge grading. NOTE: this does not disable generation. `assist()`
                     is one pipeline, so the provider is still called whenever evidence
                     clears the confidence gate. At the shipped threshold that is rare
                     (4/165 probes), so the run is nearly free -- but with `gate_open` it
                     is not, and provider rate limits dominate the result.
  --mode full        Adds LLM-judge grading on top. Intended for a subset.

The judge is pinned to Gemini via --judge-model, deliberately not the Groq model that
wrote the answer: RAG.md:66-72 requires the answer model never be its own confidence
signal, and with a single provider it otherwise would be.

Splits: --split dev for anything exploratory. Holdout is scored once, at the end.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.db import SessionLocal, engine
from app.rag.citations import build_citations
from app.rag.judge import judge_answer
from app.rag.languages import detect_consumer_language
from app.rag.providers import GeminiProvider, GroqProvider, ProviderError
from app.rag.types import LLMProvider
from evaluation.analysis.reporting import write_report
from evaluation.analysis.taxonomy import CLASSES, Outcome, classify
from evaluation.analysis.wrappers import StageTimer, build_service

REPO_ROOT = Path(__file__).resolve().parents[3]
PROBES = REPO_ROOT / "docs" / "rag_error_analysis" / "probes.jsonl"
JUDGE_TIMEOUT_SECONDS = 90.0


def load_probes(split: str | None, limit: int | None, languages: list[str] | None) -> list[dict]:
    probes = [
        json.loads(line) for line in PROBES.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if split:
        probes = [p for p in probes if p["split"] == split]
    if languages:
        probes = [p for p in probes if p["language"] in languages]
    if limit:
        # Keep whole tickets together so the paired design survives truncation.
        keep: list[str] = []
        for probe in probes:
            if probe["ticket_id"] not in keep:
                keep.append(probe["ticket_id"])
            if len(keep) * 5 >= limit:
                break
        probes = [p for p in probes if p["ticket_id"] in keep]
    return probes


def judge_provider(settings: Settings, model: str | None) -> LLMProvider | None:
    """Prefer Gemini so the judge is independent of the Groq answer model."""
    if settings.gemini_api_key:
        return GeminiProvider(
            settings.gemini_api_key,
            model or settings.gemini_model,
            JUDGE_TIMEOUT_SECONDS,
            settings.rag_provider_max_retries,
            settings.rag_provider_retry_base_delay_seconds,
        )
    if settings.groq_api_key:
        return GroqProvider(
            settings.groq_api_key,
            settings.groq_model,
            JUDGE_TIMEOUT_SECONDS,
            settings.rag_provider_max_retries,
            settings.rag_provider_retry_base_delay_seconds,
        )
    return None


CONFIGURATIONS: dict[str, dict[str, Any]] = {
    "baseline": {},
    # Counterfactual, never a baseline: opens the confidence gate so that generation,
    # citation and output-language behaviour downstream of retrieval can be measured at
    # all. At the shipped 0.55 threshold almost nothing is answered, so G1/G2/L1b would
    # otherwise be unmeasurable rather than healthy.
    "gate_open": {"settings": {"rag_min_confidence": 0.0}},
    "final_limit_3": {"settings": {"rag_final_limit": 3}},
    "final_limit_8": {"settings": {"rag_final_limit": 8}},
    "candidate_limit_10": {"settings": {"rag_candidate_limit": 10}},
    "candidate_limit_40": {"settings": {"rag_candidate_limit": 40}},
    "min_confidence_045": {"settings": {"rag_min_confidence": 0.45}},
    "min_confidence_065": {"settings": {"rag_min_confidence": 0.65}},
    "no_rerank": {"build": {"disable_reranker": True}},
    "dense_only": {"build": {"retriever_variant": "dense_only"}},
    "lexical_only": {"build": {"retriever_variant": "lexical_only"}},
    "embedding_outage": {"build": {"disable_embedder": True}},
}


async def run_probe(
    service: Any,
    probe: dict,
    timer: StageTimer,
    judge: LLMProvider | None,
    generate: bool,
) -> Outcome:
    timer.reset()
    started = time.perf_counter()
    error = None
    try:
        result = await service.assist(
            query=probe["query"],
            institution=None,
            category=None,
            language=None if generate else probe["language"],
        )
    except Exception as exc:  # noqa: BLE001 - a crash is itself an outcome to record
        return Outcome(
            probe=probe,
            route="error",
            escalation_reason=None,
            confidence=0.0,
            latency_ms=(time.perf_counter() - started) * 1000,
            error=f"{type(exc).__name__}: {exc}",
            stages=timer.derived(),
        )
    latency_ms = (time.perf_counter() - started) * 1000

    retrieval = timer.retrieval
    # `served` is what reached the prompt (empty when the confidence gate fired);
    # `ranked` is what retrieval actually selected. Keeping them apart is what lets a
    # retrieval miss be told apart from a gate rejection.
    served = list(retrieval.evidence) if retrieval else []
    ranked = timer.selected()
    evidence = served
    neighbours = [item.source_id for item in evidence if item.is_neighbor]
    citations = build_citations(result.draft, evidence) if result.draft else []
    cited_ids = [c.source_id for c in citations]
    neighbour_chunks = {item.chunk_id for item in evidence if item.is_neighbor}
    cited_neighbour = any(
        chunk in neighbour_chunks for citation in citations for chunk in citation.chunk_ids
    )

    judged = None
    if generate and judge and result.draft:
        graded = await judge_answer(
            judge,
            query=probe["query"],
            answer=result.draft,
            evidence_text="\n\n".join(
                f"[E{index}] {item.text}" for index, item in enumerate(evidence, 1)
            ),
        )
        if graded:
            judged = {
                "faithfulness": graded.faithfulness,
                "relevance": graded.relevance,
                "citation_correctness": graded.citation_correctness,
                "unsafe": float(graded.unsafe),
            }

    return Outcome(
        probe=probe,
        route=result.route,
        escalation_reason=result.escalation_reason,
        confidence=result.confidence,
        retrieved_sources=[item.source_id for item in ranked],
        served_sources=[item.source_id for item in served],
        served_ranked_sources=[item.source_id for item in served if not item.is_neighbor],
        ranked_scores=[
            {
                "source_id": item.source_id,
                "chunk_index": item.chunk_index,
                "dense": round(item.dense_score, 4),
                "lexical": round(item.lexical_score, 4),
                "fused": round(item.fused_score, 6),
                "rerank": round(item.rerank_score, 4),
            }
            for item in ranked
        ],
        neighbour_sources=neighbours,
        cited_sources=cited_ids,
        cited_neighbour=cited_neighbour,
        detected_language=result.language,
        answer_language=(
            detect_consumer_language(result.draft).value if result.draft else None
        ),
        diagnostics=dict(retrieval.diagnostics) if retrieval else {},
        stages=timer.derived(),
        latency_ms=latency_ms,
        judge=judged,
        error=error,
    )


async def run_configuration(
    name: str,
    spec: dict[str, Any],
    probes: list[dict],
    judge: LLMProvider | None,
    generate: bool,
    cache_embeddings: bool = False,
) -> list[Outcome]:
    base = get_settings()
    settings = base.model_copy(update=spec.get("settings", {})) if spec.get("settings") else base
    timer = StageTimer()
    outcomes: list[Outcome] = []
    async with SessionLocal() as db:
        service = build_service(
            db, settings, timer, cache_embeddings=cache_embeddings, **spec.get("build", {})
        )
        for index, probe in enumerate(probes, 1):
            outcomes.append(await run_probe(service, probe, timer, judge, generate))
            if index % 25 == 0:
                print(f"    {name}: {index}/{len(probes)}", flush=True)
    return outcomes


def summarise(outcomes: list[Outcome], timeout_ms: float) -> dict[str, Any]:
    latencies = sorted(o.latency_ms for o in outcomes)
    p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)] if latencies else None

    rows = []
    for outcome in outcomes:
        classes = classify(outcome, timeout_ms=timeout_ms, p95_ms=p95)
        rows.append(
            {
                "probe_id": outcome.probe["probe_id"],
                "ticket_id": outcome.probe["ticket_id"],
                "language": outcome.probe["language"],
                "intent": outcome.probe["intent"],
                "answerable": outcome.probe["answerable"],
                "expected_route": outcome.probe["expected_route"],
                "route": outcome.route,
                "escalation_reason": outcome.escalation_reason,
                "confidence": round(outcome.confidence, 4),
                "retrieved_sources": outcome.retrieved_sources,
                "served_sources": outcome.served_sources,
                "served_ranked_sources": outcome.served_ranked_sources,
                # Only the top hit's component scores: enough to decompose the confidence
                # gate without making the report unreadably large.
                "top_scores": outcome.ranked_scores[0] if outcome.ranked_scores else None,
                "cited_sources": outcome.cited_sources,
                "detected_language": outcome.detected_language,
                "answer_language": outcome.answer_language,
                "diagnostics": outcome.diagnostics,
                "stages_ms": outcome.stages,
                "latency_ms": round(outcome.latency_ms, 2),
                "judge": outcome.judge,
                "error": outcome.error,
                "failure_classes": classes,
            }
        )

    def rate(predicate: Any, population: list[dict]) -> float:
        return round(sum(1 for r in population if predicate(r)) / len(population), 4) if population else 0.0

    by_language: dict[str, Any] = {}
    for language in sorted({r["language"] for r in rows}):
        subset = [r for r in rows if r["language"] == language]
        answerable = [r for r in subset if r["answerable"]]
        by_language[language] = {
            "n": len(subset),
            "route_match": rate(lambda r: r["route"] == r["expected_route"], subset),
            "recall_any_relevant": rate(
                lambda r: "R1" not in r["failure_classes"], answerable
            ),
            "latency_p50_ms": round(statistics.median([r["latency_ms"] for r in subset]), 2),
            "mean_confidence": round(
                statistics.fmean([r["confidence"] for r in subset]), 4
            ),
            "failure_counts": {
                code: sum(1 for r in subset if code in r["failure_classes"]) for code in CLASSES
            },
        }

    return {
        "n": len(rows),
        "latency_p50_ms": round(statistics.median(latencies), 2) if latencies else 0.0,
        "latency_p95_ms": round(p95, 2) if p95 else 0.0,
        "stage_medians_ms": {
            stage: round(
                statistics.median([r["stages_ms"].get(stage, 0.0) for r in rows]), 2
            )
            for stage in ("embed", "rerank", "retrieve_total", "sql_fusion_neighbours_derived", "generate")
        },
        "failure_counts": {
            code: sum(1 for r in rows if code in r["failure_classes"]) for code in CLASSES
        },
        "by_language": by_language,
        "rows": rows,
    }


async def main_async(args: argparse.Namespace) -> None:
    settings = get_settings()
    probes = load_probes(args.split, args.limit, args.languages)
    generate = args.mode == "full"
    judge = judge_provider(settings, args.judge_model) if generate else None
    judge_name = getattr(judge, "name", None)
    if generate and judge_name == "groq":
        print("WARNING: judge is Groq, the same provider as the generator (self-grading).")

    configurations = args.configurations or ["baseline"]
    print(f"probes={len(probes)} split={args.split} mode={args.mode} configs={configurations}")

    report: dict[str, Any] = {
        "mode": args.mode,
        "split": args.split,
        "probe_count": len(probes),
        "judge_provider": judge_name,
        "judge_model": args.judge_model,
        "settings": {
            "groq_model": settings.groq_model,
            "gemini_model": settings.gemini_model,
            "embedding_model": settings.rag_embedding_model,
            "candidate_limit": settings.rag_candidate_limit,
            "final_limit": settings.rag_final_limit,
            "min_confidence": settings.rag_min_confidence,
        },
        "configurations": {},
    }
    timeout_ms = settings.rag_request_timeout_seconds * 1000
    for position, name in enumerate(configurations):
        print(f"  running configuration: {name}", flush=True)
        try:
            outcomes = await run_configuration(
                name,
                CONFIGURATIONS[name],
                probes,
                judge,
                generate,
                cache_embeddings=args.cache_embeddings,
            )
        except ProviderError as exc:
            report["configurations"][name] = {"error": str(exc)}
            continue
        summary = summarise(outcomes, timeout_ms)
        # Only the first configuration runs with a cold embedding cache, so only its
        # latency reflects real request cost.
        summary["latency_is_representative"] = not args.cache_embeddings or position == 0
        report["configurations"][name] = summary

    await engine.dispose()
    destination = write_report(args.out, report)
    print(f"wrote {destination}")
    for name, summary in report["configurations"].items():
        if "failure_counts" in summary:
            top = {k: v for k, v in summary["failure_counts"].items() if v}
            print(f"  {name}: p50={summary['latency_p50_ms']}ms failures={top}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RAG error-analysis probe set")
    parser.add_argument("--mode", choices=["retrieval", "full"], default="retrieval")
    parser.add_argument("--split", choices=["dev", "holdout"], default="dev")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--languages", nargs="*", default=None)
    parser.add_argument("--configurations", nargs="*", default=None, choices=list(CONFIGURATIONS))
    parser.add_argument("--judge-model", default=None)
    parser.add_argument(
        "--cache-embeddings",
        action="store_true",
        help="Reuse query vectors across configurations. Only the first configuration's "
        "latency is then representative.",
    )
    parser.add_argument("--out", default="run_analysis")
    args = parser.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
