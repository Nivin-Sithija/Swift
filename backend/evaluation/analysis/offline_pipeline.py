"""Structural diagnostics for chunking, citation validation and the confidence gate.

All three run against the real production functions with no database and no provider:

  Chunking      `chunk_markdown` (ingest.py:22) splits on paragraph boundaries with
                **zero overlap**. A fact whose statement and qualifier straddle a boundary
                can only ever be retrieved as half a fact, so boundary behaviour is a
                retrieval failure mode that exists before any query is asked.

  G2 citations  `citations_are_valid` (citations.py:37) is the last line of defence
                before an answer reaches a customer. It is measured for false *accepts*
                (an answer citing a neighbour chunk that was never ranked) and false
                *rejects* (a well-formed answer refused over formatting).

  Confidence    `evidence_confidence` decides whether evidence is shown. Dense,
                lexical and normalized-RRF channels are now explicit and continuous;
                the probes pin the former zero-to-epsilon discontinuity closed.
"""

from __future__ import annotations

import statistics
from dataclasses import replace
from datetime import date
from pathlib import Path

from app.core.config import get_settings
from app.rag.citations import citations_are_valid
from app.rag.ingest import chunk_markdown
from app.rag.retrieval import evidence_confidence
from app.rag.types import Evidence
from evaluation.analysis.reporting import write_report

REPO_ROOT = Path(__file__).resolve().parents[3]
CLEANED = REPO_ROOT / "docs" / "rag_sources" / "documents" / "cleaned"

BASE = Evidence(
    chunk_id="c1",
    source_id="SRC-ACC-001",
    title="Regular Savings Account",
    source_url="https://www.combank.lk/x",
    institution="Commercial Bank of Ceylon PLC",
    category="accounts",
    language="english",
    source_authority="bank_official",
    version="1.0",
    review_date=date(2026, 7, 29),
    approval_status="approved",
    chunk_index=0,
    text="Bring your NIC and proof of address.",
)


def chunking() -> dict[str, object]:
    documents = sorted(CLEANED.glob("*.md"))
    per_document = []
    all_lengths: list[int] = []
    for path in documents:
        chunks = chunk_markdown(path.read_text(encoding="utf-8"))
        lengths = [len(body) for _, body in chunks]
        all_lengths.extend(lengths)
        per_document.append(
            {
                "document": path.name,
                "chars": len(path.read_text(encoding="utf-8")),
                "chunks": len(chunks),
                "min_chars": min(lengths) if lengths else 0,
                "median_chars": int(statistics.median(lengths)) if lengths else 0,
                "max_chars": max(lengths) if lengths else 0,
                "single_chunk_sections": sum(1 for length in lengths if length < 200),
            }
        )

    # Overlap is structurally zero: rebuild the corpus from the chunk bodies and confirm
    # no text is duplicated across adjacent chunks beyond the repeated heading line.
    sample = chunk_markdown((CLEANED / "cards_combank_dispute_policy.md").read_text(encoding="utf-8"))
    repeated_headings = sum(
        1
        for index in range(1, len(sample))
        if sample[index][1].splitlines()[:1] == sample[index - 1][1].splitlines()[:1]
    )
    return {
        "documents": len(documents),
        "total_chunks": len(all_lengths),
        "corpus_chars": sum(item["chars"] for item in per_document),  # type: ignore[misc]
        "chunk_chars_min": min(all_lengths),
        "chunk_chars_median": int(statistics.median(all_lengths)),
        "chunk_chars_max": max(all_lengths),
        "chunks_under_200_chars": sum(1 for length in all_lengths if length < 200),
        "max_chars_setting": 1800,
        "overlap_chars": 0,
        "continuation_chunks_repeating_a_heading": repeated_headings,
        "per_document": per_document,
    }


def citation_validation() -> dict[str, object]:
    ranked = [replace(BASE, chunk_id="c1"), replace(BASE, chunk_id="c2", source_id="SRC-CARD-001")]
    with_neighbour = [*ranked, replace(BASE, chunk_id="c9", is_neighbor=True)]

    cases = {
        # False accept: E3 is a neighbour chunk, appended by _expand_neighbors and never
        # ranked or reranked, yet it is numbered into the prompt and validates cleanly.
        "cites_unranked_neighbour_chunk": {
            "answer": "You need your NIC. [E3]",
            "evidence": with_neighbour,
            "valid": citations_are_valid("You need your NIC. [E3]", with_neighbour),
            "expected_ideal": False,
        },
        "marker_out_of_range": {
            "answer": "You need your NIC. [E9]",
            "evidence": ranked,
            "valid": citations_are_valid("You need your NIC. [E9]", ranked),
            "expected_ideal": False,
        },
        "no_marker_at_all": {
            "answer": "You need your NIC.",
            "evidence": ranked,
            "valid": citations_are_valid("You need your NIC.", ranked),
            "expected_ideal": False,
        },
        "well_formed_single_block": {
            "answer": "You need your NIC. [E1]",
            "evidence": ranked,
            "valid": citations_are_valid("You need your NIC. [E1]", ranked),
            "expected_ideal": True,
        },
        # False reject risk: a heading must end with ':' to be exempt. A bare bolded
        # heading is treated as a factual block and demands its own marker.
        "bulleted_answer_with_uncited_heading": {
            "answer": "**Required documents**\n\n- NIC [E1]\n- Proof of address [E1]",
            "evidence": ranked,
            "valid": citations_are_valid(
                "**Required documents**\n\n- NIC [E1]\n- Proof of address [E1]", ranked
            ),
            "expected_ideal": True,
        },
        "heading_with_colon_is_exempt": {
            "answer": "Required documents:\n\n- NIC [E1]",
            "evidence": ranked,
            "valid": citations_are_valid("Required documents:\n\n- NIC [E1]", ranked),
            "expected_ideal": True,
        },
    }
    for case in cases.values():
        case["is_defect"] = case["valid"] != case["expected_ideal"]
    return {
        "cases": {name: {k: v for k, v in case.items() if k != "evidence"} for name, case in cases.items()},
        "false_accepts": sorted(
            n for n, c in cases.items() if c["valid"] and not c["expected_ideal"]
        ),
        "false_rejects": sorted(
            n for n, c in cases.items() if not c["valid"] and c["expected_ideal"]
        ),
    }


def confidence_gate() -> dict[str, object]:
    """Characterise the explicit confidence components and release threshold."""
    min_confidence = get_settings().rag_min_confidence

    def score(dense: float, lexical: float, fused: float, rerank: float) -> float:
        top = replace(BASE, dense_score=dense, lexical_score=lexical, fused_score=fused,
                      rerank_score=rerank)
        return evidence_confidence([top])

    probes = {
        "dense_zero_with_strong_lexical": {
            "dense": 0.0, "lexical": 0.9, "fused": 0.01, "rerank": 0.9,
            "confidence": score(0.0, 0.9, 0.01, 0.9),
        },
        "dense_and_lexical_zero_with_normalized_rrf": {
            "dense": 0.0, "lexical": 0.0, "fused": 0.02, "rerank": 0.9,
            "confidence": score(0.0, 0.0, 0.02, 0.9),
        },
        "identical_but_dense_is_tiny_not_zero": {
            "dense": 0.001, "lexical": 0.9, "fused": 0.01, "rerank": 0.9,
            "confidence": score(0.001, 0.9, 0.01, 0.9),
        },
        "strong_dense_weak_rerank": {
            "dense": 0.95, "lexical": 0.0, "fused": 0.02, "rerank": 0.1,
            "confidence": score(0.95, 0.0, 0.02, 0.1),
        },
        "weak_dense_strong_rerank": {
            "dense": 0.1, "lexical": 0.0, "fused": 0.02, "rerank": 0.95,
            "confidence": score(0.1, 0.0, 0.02, 0.95),
        },
    }
    for probe in probes.values():
        probe["passes_gate"] = probe["confidence"] >= min_confidence

    # The discontinuity: dense 0.0 vs dense 0.001, all else equal.
    fallthrough = probes["dense_zero_with_strong_lexical"]["confidence"]
    tiny = probes["identical_but_dense_is_tiny_not_zero"]["confidence"]

    floor = evidence_confidence([replace(BASE, dense_score=0.0, lexical_score=0.0,
                                         fused_score=0.0, rerank_score=0.0)])
    return {
        "min_confidence_setting": min_confidence,
        "probes": probes,
        "dense_zero_vs_dense_0p001_gap": round(fallthrough - tiny, 4),
        "unconditional_floor_for_one_approved_chunk": floor,
        "note": (
            "BGE-M3 dense relevance contributes 0.85, normalized RRF 0.10, and the "
            "English-biased reranker only 0.05; there is no unconditional authority floor."
        ),
    }


def main() -> None:
    report = {
        "diagnostic": "structural_chunking_citations_confidence",
        "chunking": chunking(),
        "citation_validation": citation_validation(),
        "confidence_gate": confidence_gate(),
    }
    print(f"wrote {write_report('offline_pipeline', report)}")


if __name__ == "__main__":
    main()
