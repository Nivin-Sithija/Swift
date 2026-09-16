"""Phase 2 -- build and freeze the probe set.

Design note, and a correction to the original plan
--------------------------------------------------
The plan assumed BANKING77 intents could be mapped onto the knowledge base to derive
`relevant_sources`. Inspecting both corpora shows that premise is only partly true:
BANKING77 is a *neobank* intent set (top-ups, virtual and disposable cards, fiat/crypto
support) while the knowledge base is five Sri Lankan retail-banking pages. `SRC-LOAN-001`
has no corresponding intent at all. Deriving relevance labels from intent names alone
would therefore have invented ground truth.

The probe set is instead built in two parts, each doing what it can actually support:

  Set A -- paired multilingual probes (NO labels required).
      Every sampled ticket appears in all five languages with a shared `ticket_id`, so
      the corpus, the question and the configuration are held constant and only the
      language varies. Retrieval divergence from the English rendering is then a direct
      measure of language-induced failure that needs no ground truth, and so cannot be
      contaminated by label choices. English is the reference because the corpus is
      entirely English.

  Set B -- answerability labels, grounded in the corpus text.
      `relevant_sources` is assigned only where the knowledge base demonstrably answers
      the intent, verified by reading the cleaned Markdown rather than by matching a
      category string. Each mapping records *why*, so a reviewer can check it. Intents
      with no KB coverage are labelled unanswerable and expected to escalate -- coverage
      the existing 5-case golden set almost entirely lacks.

Splitting is on `ticket_id`, never on probe rows: the five renderings of one ticket are
translations of each other, so a row-wise split would put a ticket's English copy in dev
and its Sinhala copy in holdout and leak straight across the boundary.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASETS = REPO_ROOT / "datasets"
OUT_DIR = REPO_ROOT / "docs" / "rag_error_analysis"
TRACKS = ("english", "sinhala", "tamil", "singlish", "tamilish")
SPLIT_SEED = 20260907
HOLDOUT_FRACTION = 0.5

# Intent -> (source_ids, why). Every entry was checked against the cleaned Markdown in
# docs/rag_sources/documents/cleaned/. `why` is the reviewable justification.
ANSWERABLE: dict[str, tuple[tuple[str, ...], str]] = {
    "lost_or_stolen_card": (
        ("SRC-CARD-001",),
        "Dispute policy: cardholder must immediately call the Card Centre, agent blocks "
        "the card, replacement dispatched within 5 working days.",
    ),
    "compromised_card": (
        ("SRC-CARD-001", "SRC-FRAUD-001"),
        "Dispute policy covers unauthorised use and liability; CBSL page covers not "
        "sharing PINs/OTPs and reporting suspicious activity.",
    ),
    "card_payment_not_recognised": (
        ("SRC-CARD-001",),
        "Dispute policy covers unauthorised transactions and the resolution procedure.",
    ),
    "cash_withdrawal_not_recognised": (
        ("SRC-CARD-001",),
        "Same unauthorised-transaction dispute path as card payments.",
    ),
    "card_swallowed": (
        ("SRC-CARD-001",),
        "Card Centre contact and card blocking/replacement procedure applies.",
    ),
    "age_limit": (
        ("SRC-ACC-001",),
        "Eligibility states: resident of Sri Lanka over 18 years of age.",
    ),
    "transfer_fee_charged": (
        ("SRC-TRF-001",),
        "Card-to-card page states a Rs 100 transaction fee for CRM cash deposits.",
    ),
}

# Intents the knowledge base demonstrably does not cover. A confident, cited answer to
# any of these is an unsupported-generation failure, not a success.
UNANSWERABLE: tuple[str, ...] = (
    "automatic_top_up",
    "top_up_by_card_charge",
    "top_up_limits",
    "get_disposable_virtual_card",
    "getting_virtual_card",
    "virtual_card_not_working",
    "apple_pay_or_google_pay",
    "fiat_currency_support",
    "exchange_via_app",
    "verify_source_of_funds",
    "country_support",
    "disposable_card_limits",
)


def load_tickets() -> dict[str, dict[str, Any]]:
    """Return {ticket_id: {intent, texts:{language: text}}} for ids present in all tracks."""
    tickets: dict[str, dict[str, Any]] = {}
    for track in TRACKS:
        path = DATASETS / track / "test_labeled.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            for record in csv.DictReader(handle):
                entry = tickets.setdefault(
                    record["id"], {"intent": record["category"], "texts": {}}
                )
                entry["texts"][track] = record["text"]
    return {tid: entry for tid, entry in tickets.items() if len(entry["texts"]) == len(TRACKS)}


def select(
    tickets: dict[str, dict[str, Any]], per_intent: int, unanswerable_per_intent: int
) -> list[dict[str, Any]]:
    rng = random.Random(SPLIT_SEED)
    chosen: list[dict[str, Any]] = []
    by_intent: dict[str, list[str]] = {}
    for tid, entry in tickets.items():
        by_intent.setdefault(entry["intent"], []).append(tid)

    for intent, (sources, why) in sorted(ANSWERABLE.items()):
        pool = sorted(by_intent.get(intent, []))
        for tid in rng.sample(pool, min(per_intent, len(pool))):
            chosen.append(
                {
                    "ticket_id": tid,
                    "intent": intent,
                    "answerable": True,
                    "relevant_sources": list(sources),
                    "label_reason": why,
                    "expected_route": "rag_draft",
                }
            )
    for intent in sorted(UNANSWERABLE):
        pool = sorted(by_intent.get(intent, []))
        for tid in rng.sample(pool, min(unanswerable_per_intent, len(pool))):
            chosen.append(
                {
                    "ticket_id": tid,
                    "intent": intent,
                    "answerable": False,
                    "relevant_sources": [],
                    "label_reason": "No knowledge-base document covers this product area.",
                    "expected_route": "human_escalation",
                }
            )
    return chosen


def assign_splits(selected: list[dict[str, Any]]) -> dict[str, str]:
    """Split on ticket_id so all five renderings of a ticket share a split."""
    rng = random.Random(SPLIT_SEED)
    ids = sorted({item["ticket_id"] for item in selected})
    rng.shuffle(ids)
    cut = int(len(ids) * (1 - HOLDOUT_FRACTION))
    return {tid: ("dev" if index < cut else "holdout") for index, tid in enumerate(ids)}


def build(per_intent: int, unanswerable_per_intent: int) -> dict[str, Any]:
    tickets = load_tickets()
    selected = select(tickets, per_intent, unanswerable_per_intent)
    splits = assign_splits(selected)

    probes = []
    for item in selected:
        entry = tickets[item["ticket_id"]]
        for language in TRACKS:
            probes.append(
                {
                    "probe_id": f"{item['ticket_id']}-{language}",
                    "ticket_id": item["ticket_id"],
                    "language": language,
                    "intent": item["intent"],
                    "query": entry["texts"][language],
                    "answerable": item["answerable"],
                    "relevant_sources": item["relevant_sources"],
                    "expected_route": item["expected_route"],
                    "split": splits[item["ticket_id"]],
                }
            )
    probes.sort(key=lambda probe: (probe["ticket_id"], probe["language"]))
    return {"probes": probes, "selected": selected, "splits": splits}


def manifest(result: dict[str, Any]) -> dict[str, Any]:
    probes = result["probes"]
    holdout_ids = sorted({p["ticket_id"] for p in probes if p["split"] == "holdout"})
    dev_ids = sorted({p["ticket_id"] for p in probes if p["split"] == "dev"})
    digest = hashlib.sha256(
        json.dumps([p["probe_id"] for p in probes], sort_keys=True).encode()
    ).hexdigest()[:12]
    return {
        "sha": digest,
        "seed": SPLIT_SEED,
        "drawn_on": "ticket_id, so all five language renderings share a split",
        "source": "datasets/*/test_labeled.csv (official BANKING77 test ids)",
        "counts": {
            "tickets": len(dev_ids) + len(holdout_ids),
            "probes": len(probes),
            "dev_tickets": len(dev_ids),
            "holdout_tickets": len(holdout_ids),
            "answerable_probes": sum(p["answerable"] for p in probes),
            "unanswerable_probes": sum(not p["answerable"] for p in probes),
        },
        "label_provenance": {
            intent: {"sources": list(sources), "why": why}
            for intent, (sources, why) in sorted(ANSWERABLE.items())
        },
        "unanswerable_intents": list(UNANSWERABLE),
        "caveats": [
            "Labels are authored from the corpus text, not human-verified; spot-check before"
            " quoting recall as ground truth.",
            "Thresholds are explored on dev only. Holdout is scored once and reported.",
            "The five language arms are translations of one ticket set, so language"
            " comparisons must use paired statistics.",
        ],
        "dev_ticket_ids": dev_ids,
        "holdout_ticket_ids": holdout_ids,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and freeze the RAG probe set")
    parser.add_argument("--per-intent", type=int, default=6)
    parser.add_argument("--unanswerable-per-intent", type=int, default=2)
    args = parser.parse_args()

    result = build(args.per_intent, args.unanswerable_per_intent)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    probe_path = OUT_DIR / "probes.jsonl"
    probe_path.write_text(
        "\n".join(json.dumps(probe, ensure_ascii=False) for probe in result["probes"]) + "\n",
        encoding="utf-8",
    )
    meta = manifest(result)
    (OUT_DIR / "probe_manifest.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"probes  : {probe_path}  ({meta['counts']['probes']} probes)")
    print(f"manifest: {OUT_DIR / 'probe_manifest.json'}  (sha {meta['sha']})")
    print(json.dumps(meta["counts"], indent=2))


if __name__ == "__main__":
    main()
