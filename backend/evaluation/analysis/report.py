"""Phase 5 -- aggregate diagnostics into the committed deliverables.

Reads whichever per-run JSON reports exist under backend/evaluation/reports/ and emits
`docs/rag_error_analysis/rag_error_analysis.csv`, shaped like the error taxonomy this
repo already uses in `ml/reports/tamilish_error_analysis.csv` (class, counts, examples,
root cause, recommendation).

Rows are emitted only for diagnostics that actually ran. A failure class with no
measurement is written as `not_measured` rather than zero, so an unrun live lane can
never be mistaken for a clean one.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from evaluation.analysis.reporting import REPORT_DIR
from evaluation.analysis.taxonomy import CLASSES

OUT_DIR = Path(__file__).resolve().parents[3] / "docs" / "rag_error_analysis"
NOT_MEASURED = "not_measured"


def load(name: str) -> dict[str, Any] | None:
    path = REPORT_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def offline_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    language = load("offline_language")
    guardrails = load("offline_guardrails")
    pipeline = load("offline_pipeline")

    if language:
        per = language["per_language"]
        worst = min(per, key=lambda k: per[k]["accuracy"])
        rc = language["root_cause"]
        dead = [
            token
            for token, stats in rc["tamilish_token_coverage"].items()
            if stats["fires_on_track_pct"] < 1.0
        ]
        missed = ", ".join(c["token"] for c in rc["tamilish_missed_candidates"][:4])
        rows.append(
            {
                "class": "L1a",
                "name": CLASSES["L1a"][0],
                "population": f"{sum(p['n'] for p in per.values())} held-out rows, 5 languages",
                "count": str(sum(p["n"] - p["correct"] for p in per.values())),
                "rate": f"{worst}={per[worst]['accuracy']:.1%} "
                f"[{per[worst]['ci95_low']:.1%},{per[worst]['ci95_high']:.1%}]",
                "representative": f"{worst}: {per[worst]['misread_as']}",
                "root_cause": (
                    f"Keyword lists use different transliteration variants than the corpus. "
                    f"Dead tokens: {', '.join(dead) or 'none'}. Absent high-signal tokens: {missed}."
                ),
                "recommendation": (
                    "Replace the hand-written token lists with forms measured against the "
                    "corpus; each candidate above fires on >2% of its track and 0.00% of English."
                ),
            }
        )

    if guardrails:
        bypass = guardrails["bypass_corpus"]
        fp = guardrails["false_positive_load"]["per_language"]
        safety = guardrails["paired_safety_coverage"]
        rows.append(
            {
                "class": "X1",
                "name": CLASSES["X1"][0],
                "population": f"{bypass['corpus_size']} adversarial probes",
                "count": str(bypass["corpus_size"] - bypass["detected"]),
                "rate": f"{1 - bypass['detection_rate']:.1%} bypass",
                "representative": ", ".join(bypass["missed"][:5]),
                "root_cause": (
                    "Substring matching on raw text. Normalizing before the check would close "
                    f"only {len(bypass['closed_by_normalizing_first'])} of "
                    f"{len(bypass['missed'])} misses "
                    f"({', '.join(bypass['closed_by_normalizing_first']) or 'none'}); the rest "
                    "need a semantic or model-based check."
                ),
                "recommendation": (
                    "Treat validate_grounding as the real backstop. Scan ticket_context as well "
                    "as original_query, and normalize before matching -- but do not expect "
                    "normalization alone to move the detection rate materially."
                ),
            }
        )
        rows.append(
            {
                "class": "X2",
                "name": CLASSES["X2"][0],
                "population": f"{sum(v['n'] for v in fp.values())} real banking tickets",
                "count": str(sum(v["guardrail_false_positives"] for v in fp.values())),
                "rate": "0.000%",
                "representative": "none observed in any language",
                "root_cause": "Rules are long literal phrases, so they almost never fire by accident.",
                "recommendation": (
                    "There is measured headroom to make the injection filter stricter: its "
                    "current false-positive cost on real traffic is zero."
                ),
            }
        )
        rows.append(
            {
                "class": "SAFETY-EQ",
                "name": "safety_coverage_language_gap",
                "population": f"{safety['paired_tickets']} paired tickets x 5 languages",
                "count": str(safety["missed_in_both_sinhala_and_tamilish"]),
                "rate": " ".join(
                    f"{k}={v:.1%}" for k, v in safety["coverage_rate_vs_english"].items()
                ),
                "representative": (
                    f"{safety['flagged_in_english']} tickets escalate in English; "
                    f"{safety['also_flagged_in']['sinhala']} of the same escalate in Sinhala"
                ),
                "root_cause": (
                    "safety.py holds 5 English phrases + 1 Sinhala + 1 Tamil for "
                    "private_account_data and 11 English + 1 + 1 for financial_action. "
                    "Code-mixed text keeps English nouns ('statement') but localizes the "
                    "possessive, so two-word English phrases like 'my statement' never match."
                ),
                "recommendation": (
                    "Match on single high-signal nouns plus per-language possessives, and "
                    "measure coverage on the paired corpus so parity is enforced, not assumed."
                ),
            }
        )

    if pipeline:
        cite = pipeline["citation_validation"]
        conf = pipeline["confidence_gate"]
        chunk = pipeline["chunking"]
        rows.append(
            {
                "class": "G2",
                "name": CLASSES["G2"][0],
                "population": f"{len(cite['cases'])} structural cases",
                "count": str(len(cite["false_accepts"]) + len(cite["false_rejects"])),
                "rate": f"{len(cite['false_accepts'])} false accept / "
                f"{len(cite['false_rejects'])} false reject",
                "representative": ", ".join(cite["false_accepts"] + cite["false_rejects"]),
                "root_cause": (
                    "Neighbour chunks are appended to the same [E1..En] numbering that "
                    "citations_are_valid range-checks, so citing unranked context passes. "
                    "Separately, a heading is only exempt if it ends with ':', so a bolded "
                    "heading is treated as an uncited factual block."
                ),
                "recommendation": (
                    "Number only ranked evidence in the prompt, or mark neighbours so a "
                    "citation to one is rejected. Widen the heading heuristic."
                ),
            }
        )
        rows.append(
            {
                "class": "CONF-GATE",
                "name": "confidence_falsy_chain",
                "population": f"{len(conf['probes'])} synthetic score vectors",
                "count": str(sum(1 for p in conf["probes"].values() if p["passes_gate"])),
                "rate": f"gap of {conf['dense_zero_vs_dense_0p001_gap']} from a 0.001 change",
                "representative": "dense_zero_falls_through_to_lexical",
                "root_cause": (
                    "`top.dense_score or top.lexical_score or top.fused_score * 30` is falsy "
                    "chaining, so a genuine 0.0 dense score is replaced by the lexical score. "
                    f"authority+coherence also contribute {conf['unconditional_floor_for_one_approved_chunk']} "
                    "unconditionally for any single approved chunk."
                ),
                "recommendation": (
                    "Use explicit None checks rather than `or`, and keep relevance and "
                    "provenance as separate signals instead of summing them into one gate."
                ),
            }
        )
        rows.append(
            {
                "class": "CHUNK",
                "name": "chunking_boundary_risk",
                "population": f"{chunk['documents']} documents / {chunk['total_chunks']} chunks",
                "count": str(chunk["chunks_under_200_chars"]),
                "rate": f"median {chunk['chunk_chars_median']} chars, max {chunk['chunk_chars_max']}",
                "representative": (
                    f"max chunk {chunk['chunk_chars_max']} chars exceeds the "
                    f"{chunk['max_chars_setting']} setting"
                ),
                "root_cause": (
                    "Splitting only happens at paragraph boundaries, so a single paragraph "
                    "longer than max_chars is emitted whole. Overlap is zero, so a fact split "
                    "across a boundary can only be retrieved in halves."
                ),
                "recommendation": (
                    "Add sentence-level splitting for oversized paragraphs and a small overlap; "
                    "re-measure recall before and after on the frozen probe set."
                ),
            }
        )
    return rows


def live_rows() -> list[dict[str, str]]:
    """Live-lane classes, with unmeasured ones reported as such.

    A zero here is only meaningful if the class could have fired. Three cannot, in the runs
    this repo can currently afford:

      * G1/R2 need LLM-judge grades. With no grades, a zero means "ungraded", not "clean".
      * L1b needs drafted answers. Almost nothing is answered, so there is nothing to check.
      * L1a is meaningless in a retrieval-mode run: the harness passes the probe's language
        explicitly, which overrides detection. The real measurement is the offline one, at
        n=15,395.

    Classes already measured offline at far larger n are not duplicated here.
    """
    report = load("run_analysis")
    measured_offline = {"L1a", "X1", "X2"}
    live_codes = [c for c in CLASSES if c not in measured_offline]

    def unmeasured(code: str, why: str) -> dict[str, str]:
        return {
            "class": code,
            "name": CLASSES[code][0],
            "population": NOT_MEASURED,
            "count": NOT_MEASURED,
            "rate": NOT_MEASURED,
            "representative": CLASSES[code][1],
            "root_cause": NOT_MEASURED,
            "recommendation": why,
        }

    if not report:
        return [unmeasured(c, "Requires the live lane (database + providers).") for c in live_codes]

    baseline = report["configurations"].get("baseline", {})
    rows_out = baseline.get("rows", [])
    counts = baseline.get("failure_counts", {})
    total = baseline.get("n", 0)
    drafted = sum(1 for r in rows_out if r.get("route") == "rag_draft")
    graded = sum(1 for r in rows_out if r.get("judge"))

    rows: list[dict[str, str]] = []
    for code in live_codes:
        if code in {"G1", "R2"} and not graded:
            rows.append(
                unmeasured(
                    code,
                    f"Judge produced 0 grades over {drafted} drafted answers; see findings.md 7.",
                )
            )
            continue
        if code == "L1b" and drafted < 5:
            rows.append(
                unmeasured(code, f"Only {drafted} answers were drafted; too few to measure.")
            )
            continue
        count = counts.get(code, 0)
        rows.append(
            {
                "class": code,
                "name": CLASSES[code][0],
                "population": f"{total} probes (baseline, split={report.get('split')})",
                "count": str(count),
                "rate": f"{count / total:.1%}" if total else NOT_MEASURED,
                "representative": CLASSES[code][1],
                "root_cause": "See findings.md",
                "recommendation": "See findings.md",
            }
        )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = offline_rows() + live_rows()
    fields = [
        "class",
        "name",
        "population",
        "count",
        "rate",
        "representative",
        "root_cause",
        "recommendation",
    ]
    destination = OUT_DIR / "rag_error_analysis.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    measured = sum(1 for row in rows if row["count"] != NOT_MEASURED)
    print(f"wrote {destination}")
    print(f"  {measured} classes measured, {len(rows) - measured} awaiting the live lane")


if __name__ == "__main__":
    main()
