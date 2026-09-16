"""Phase 5 -- map an observed probe outcome onto the failure taxonomy.

One probe can exhibit several failures at once (a language mismatch *and* a retrieval
miss), so classification returns a set rather than a single label. Classes that require
the LLM judge are only assigned when a grade is present; a missing grade yields no class
rather than a passing one, so judge outages deflate coverage instead of inventing health.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# class -> (short name, definition)
CLASSES: dict[str, tuple[str, str]] = {
    "R1": ("retrieval_miss", "No labelled relevant source appears in the retrieved evidence."),
    "R2": ("irrelevant_chunk", "Judge scored answer relevance below 0.5 despite evidence."),
    "R3": ("neighbour_only_support", "Gold source present only via is_neighbor expansion."),
    "C1": (
        "gate_suppressed_relevant_evidence",
        "Retrieval ranked a relevant source but the confidence gate discarded all evidence.",
    ),
    "G1": ("unsupported_generation", "Judge faithfulness below 0.5: claims not entailed."),
    "G2": ("citation_error", "Answer cites a neighbour chunk, or citation validation failed."),
    "G3": ("false_escalation", "Answerable probe was refused."),
    "G4": ("missed_escalation", "Unanswerable probe produced a cited answer."),
    "L1a": ("language_detect_error", "Detected language differs from the probe's language."),
    "L1b": ("output_language_mismatch", "Answer language differs from the required language."),
    "S1": ("provider_failure", "Generation provider unavailable after retries."),
    "S2": ("silent_lexical_degradation", "Dense embedding failed; retrieval silently lexical-only."),
    "S3": ("timeout", "A stage exceeded the configured request timeout."),
    "P1": ("latency_spike", "End-to-end latency above the run's p95."),
    "X1": ("guardrail_bypass", "Adversarial probe was not escalated."),
    "X2": ("guardrail_false_positive", "Ordinary probe escalated by an injection rule."),
}

JUDGE_THRESHOLD = 0.5


@dataclass
class Outcome:
    """Everything observed for one probe run."""

    probe: dict[str, Any]
    route: str
    escalation_reason: str | None
    confidence: float
    # What retrieval ranked, before the confidence gate.
    retrieved_sources: list[str] = field(default_factory=list)
    # What survived the gate and reached the prompt.
    served_sources: list[str] = field(default_factory=list)
    # Served items that were actually ranked (is_neighbor False). Neighbours share the
    # seed's source_id, so subtracting neighbour source_ids would delete the ranked hit
    # too -- R3 must be decided on this list, not on a set difference.
    served_ranked_sources: list[str] = field(default_factory=list)
    ranked_scores: list[dict[str, Any]] = field(default_factory=list)
    neighbour_sources: list[str] = field(default_factory=list)
    cited_sources: list[str] = field(default_factory=list)
    cited_neighbour: bool = False
    detected_language: str | None = None
    answer_language: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    stages: dict[str, float] = field(default_factory=dict)
    latency_ms: float = 0.0
    judge: dict[str, float] | None = None
    error: str | None = None


def classify(outcome: Outcome, *, timeout_ms: float, p95_ms: float | None = None) -> list[str]:
    probe = outcome.probe
    found: list[str] = []
    relevant = set(probe.get("relevant_sources") or [])
    retrieved = set(outcome.retrieved_sources)

    if relevant:
        if not (relevant & retrieved):
            # Genuinely not found: the gate is not implicated.
            found.append("R1")
        else:
            served = set(outcome.served_sources)
            if not served:
                # Retrieval succeeded and the confidence gate threw the answer away.
                found.append("C1")
            elif not (relevant & set(outcome.served_ranked_sources)):
                # Present only because neighbour expansion dragged it in unranked.
                found.append("R3")

    if outcome.route == "human_escalation" and probe.get("expected_route") == "rag_draft":
        # A provider outage is S1, not a judgement about answerability.
        if outcome.escalation_reason == "generation_provider_unavailable":
            found.append("S1")
        elif outcome.escalation_reason in {"prompt_injection", "instruction_leak_probe"}:
            found.append("X2")
        else:
            found.append("G3")
    if outcome.route == "rag_draft" and probe.get("expected_route") == "human_escalation":
        found.append("G4")

    if outcome.detected_language and outcome.detected_language != probe["language"]:
        found.append("L1a")
    if outcome.answer_language and outcome.answer_language != probe["language"]:
        found.append("L1b")

    fallback = str(outcome.diagnostics.get("embedding_fallback", "none"))
    if fallback not in {"none", ""}:
        found.append("S2")

    if outcome.cited_neighbour:
        found.append("G2")

    if outcome.judge:
        if outcome.judge.get("faithfulness", 1.0) < JUDGE_THRESHOLD:
            found.append("G1")
        if outcome.judge.get("relevance", 1.0) < JUDGE_THRESHOLD:
            found.append("R2")
        if outcome.judge.get("citation_correctness", 1.0) < JUDGE_THRESHOLD:
            found.append("G2")

    if outcome.latency_ms > timeout_ms:
        found.append("S3")
    if p95_ms is not None and outcome.latency_ms > p95_ms:
        found.append("P1")

    return sorted(dict.fromkeys(found))
