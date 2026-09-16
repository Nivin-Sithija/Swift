"""Phase 5 -- emit representative traces, one file per failure class.

A trace is the evidence a reader needs to check a claim without rerunning anything: the
query, what retrieval ranked and with what component scores, what the gate did, and how the
request was routed. Probe queries are synthetic BANKING77-derived text, so traces carry no
customer PII and are safe to commit.

Production traces must NOT be produced this way: `tests/observability/test_logfire.py`
deliberately keeps customer query text out of exported spans.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.analysis.report import load

DOCS = Path(__file__).resolve().parents[3] / "docs" / "rag_error_analysis"
OUT_DIR = DOCS / "traces"


def probe_queries() -> dict[str, str]:
    """Join query text back in by probe_id so a trace is readable on its own.

    Safe to commit: probe queries are synthetic BANKING77-derived text, not customer data.
    """
    path = DOCS / "probes.jsonl"
    if not path.exists():
        return {}
    return {
        probe["probe_id"]: probe["query"]
        for probe in (
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
        )
    }


def _fmt_scores(row: dict[str, Any]) -> str:
    top = row.get("top_scores")
    if not top:
        return "  (no ranked evidence)"
    return (
        f"  top hit: {top['source_id']} chunk {top['chunk_index']}  "
        f"dense={top['dense']:.4f} lexical={top['lexical']:.4f} "
        f"fused={top['fused']:.6f} rerank={top['rerank']:.4f}"
    )


def _probe_trace(row: dict[str, Any]) -> str:
    return (
        f"### `{row['probe_id']}` — {row['language']} / {row['intent']}\n\n"
        f"```\n"
        f"query        : {row['query'][:160] if 'query' in row else '(see probes.jsonl)'}\n"
        f"route        : {row['route']}   (expected {row['expected_route']})\n"
        f"reason       : {row['escalation_reason']}\n"
        f"confidence   : {row['confidence']}   (gate 0.55)\n"
        f"ranked       : {row['retrieved_sources']}\n"
        f"served       : {row['served_sources']}\n"
        f"{_fmt_scores(row)}\n"
        f"diagnostics  : {row['diagnostics']}\n"
        f"stages_ms    : {row['stages_ms']}\n"
        f"classes      : {row['failure_classes']}\n"
        f"```\n"
    )


def live_traces() -> dict[str, str]:
    report = load("run_analysis")
    scored = load("dev_scores")
    if not report:
        return {}
    rows = report["configurations"]["baseline"]["rows"]
    queries = probe_queries()
    for row in rows:
        row["query"] = queries.get(row["probe_id"], "(unknown)")
    # dev_scores carries top_scores; merge it in by probe_id where available.
    if scored:
        by_id = {
            r["probe_id"]: r.get("top_scores")
            for r in scored["configurations"]["baseline"]["rows"]
        }
        for row in rows:
            row.setdefault("top_scores", by_id.get(row["probe_id"]))

    out: dict[str, str] = {}
    for code in ("C1", "R1", "S2", "S3", "G3"):
        matching = [r for r in rows if code in r["failure_classes"]]
        if not matching:
            continue
        # One per language where possible, so the language axis is visible in the trace.
        chosen: list[dict[str, Any]] = []
        for language in ("english", "sinhala", "tamil", "singlish", "tamilish"):
            found = next((r for r in matching if r["language"] == language), None)
            if found:
                chosen.append(found)
        chosen = chosen or matching[:3]
        body = "\n".join(_probe_trace(r) for r in chosen[:5])
        out[code] = (
            f"# `{code}` — representative traces\n\n"
            f"{len(matching)} of {len(rows)} baseline probes exhibited this class.\n\n{body}"
        )
    return out


def offline_traces() -> dict[str, str]:
    out: dict[str, str] = {}
    guardrails = load("offline_guardrails")
    language = load("offline_language")

    if guardrails:
        safety = guardrails["paired_safety_coverage"]
        lines = []
        for example in safety["examples"][:5]:
            lines.append(
                f"### ticket `{example['ticket_id']}` — rule `{example['english_reason']}`\n\n"
                f"```\n"
                f"en  (ESCALATED): {example['english']}\n"
                f"si  (MISSED)   : {example['sinhala_missed']}\n"
                f"ta* (MISSED)   : {example['tamilish_missed']}\n"
                f"```\n"
            )
        out["SAFETY-EQ"] = (
            "# `SAFETY-EQ` — safety coverage language gap\n\n"
            f"{safety['flagged_in_english']} tickets escalate in English; "
            f"{safety['also_flagged_in']['sinhala']} of the *same* tickets escalate in "
            f"Sinhala. {safety['missed_in_both_sinhala_and_tamilish']} are missed in both "
            "Sinhala and Tamilish.\n\n"
            "These are translations of one another, so the correct behaviour is identical "
            "in all five renderings.\n\n" + "\n".join(lines)
        )

        bypass = guardrails["bypass_corpus"]
        out["X1"] = (
            "# `X1` — guardrail bypasses\n\n"
            f"Detected {bypass['detected']}/{bypass['corpus_size']} "
            f"({bypass['detection_rate']:.1%}).\n\n"
            f"**Caught:** {', '.join(bypass['caught'])}\n\n"
            f"**Missed:** {', '.join(bypass['missed'])}\n\n"
            f"**Closed by normalizing before the check:** "
            f"{', '.join(bypass['closed_by_normalizing_first']) or 'none'} "
            f"— {len(bypass['closed_by_normalizing_first'])} of {len(bypass['missed'])}.\n"
        )

    if language:
        traces = language["representative_traces"][:6]
        lines = [
            f"```\nid {t['ticket_id']}\n"
            f"  en  : {t['english_text']}\n"
            f"  ta* : {t['tamilish_text']}\n"
            f"  -> detected as: {t['tamilish_detected_as']}\n```\n"
            for t in traces
        ]
        per = language["per_language"]["tamilish"]
        out["L1a"] = (
            "# `L1a` — language detection\n\n"
            f"Tamilish accuracy {per['accuracy']:.1%} "
            f"[{per['ci95_low']:.1%}, {per['ci95_high']:.1%}] over n={per['n']}. "
            "Each ticket below is detected correctly in the other four languages and wrongly "
            "only in tamilish, so the failure is the detector, not the ticket.\n\n"
            + "\n".join(lines)
        )
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    traces = {**offline_traces(), **live_traces()}
    for code, body in traces.items():
        (OUT_DIR / f"{code}.md").write_text(body, encoding="utf-8")
    print(f"wrote {len(traces)} trace files to {OUT_DIR}")
    for code in sorted(traces):
        print(f"  {code}.md")


if __name__ == "__main__":
    main()
