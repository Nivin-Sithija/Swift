"""L1a -- language detection accuracy, measured at scale on held-out rows.

Why this runs offline and first: `detect_consumer_language` is pure regex and keyword
counting over `app.rag.types`, so it needs no database, no embeddings and no provider.
That makes it the one failure group in this workstream measurable at n>15,000 rather
than n=5.

Evaluation rows are `datasets/*/test_labeled.csv` -- the official BANKING77 test ids,
which `ml/splits/split_manifest.json` records as never used for model selection.

The five language tracks are *translations of the same tickets*, keyed by a shared `id`.
They are therefore paired, not independent samples, so language-vs-language comparisons
use McNemar's exact test over ids present in all five tracks. Treating them as
independent would overstate the significance of every comparison.

Scope: production overrides detection with `ticket.response_language` on the first turn
(`routes.py:239-241`) and passes `language=None` only on follow-up chat turns, so this
error rate applies to follow-ups.
"""

from __future__ import annotations

import csv
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple

from app.rag.languages import detect_consumer_language
from evaluation.analysis.reporting import write_report

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASETS = REPO_ROOT / "datasets"
TRACKS = ("english", "sinhala", "tamil", "singlish", "tamilish")
LABELS = (*TRACKS, "unknown")
BOOTSTRAP_ROUNDS = 2000
BOOTSTRAP_SEED = 42


class Row(NamedTuple):
    ticket_id: str
    track: str
    detected: str
    text: str


def load_track(track: str) -> list[Row]:
    path = DATASETS / track / "test_labeled.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            Row(record["id"], track, detect_consumer_language(record["text"]).value, record["text"])
            for record in csv.DictReader(handle)
        ]


def confusion(rows: list[Row]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        counts[row.track][row.detected] += 1
    return {track: {label: counts[track][label] for label in LABELS} for track in TRACKS}


def accuracy(rows: list[Row], track: str) -> tuple[int, int]:
    subset = [row for row in rows if row.track == track]
    return sum(row.detected == track for row in subset), len(subset)


def paired_bootstrap_ci(
    correct_by_id: dict[str, bool], rounds: int = BOOTSTRAP_ROUNDS
) -> tuple[float, float]:
    """Resample tickets (not rows) so the CI respects the paired design."""
    ids = list(correct_by_id)
    if not ids:
        return (0.0, 0.0)
    rng = random.Random(BOOTSTRAP_SEED)
    means = []
    for _ in range(rounds):
        sample = [correct_by_id[rng.choice(ids)] for _ in ids]
        means.append(sum(sample) / len(sample))
    means.sort()
    return (means[int(0.025 * rounds)], means[int(0.975 * rounds) - 1])


def mcnemar_exact(only_a: int, only_b: int) -> float:
    """Two-sided exact McNemar p-value on the discordant pairs."""
    total = only_a + only_b
    if total == 0:
        return 1.0
    tail = min(only_a, only_b)
    cumulative = sum(math.comb(total, k) for k in range(tail + 1)) * (0.5**total)
    return min(1.0, 2 * cumulative)


def token_diagnostics(rows: list[Row]) -> dict[str, object]:
    """Root-cause the romanized misses: which keywords actually fire, and what was missed.

    `detect_consumer_language` decides singlish/tamilish by counting keyword hits, so a
    miss is either a token that never fires on real text or a discriminative word-form the
    list omits. Both are measurable directly.
    """
    from app.rag.languages import detect_consumer_language as _detector  # noqa: F401

    tamilish_tokens = ("enna", "epdi", "panna", "mudiyala", "irukku", "venum", "aayiduchu")
    singlish_tokens = ("mage", "kohomada", "karanna", "puluwanda", "naha", "tiyenawa", "eka")
    text_by_track = {
        track: [row.text.casefold() for row in rows if row.track == track] for track in TRACKS
    }

    def coverage(tokens: tuple[str, ...], track: str) -> dict[str, dict[str, float]]:
        corpus = text_by_track[track]
        english = text_by_track["english"]
        return {
            token: {
                "fires_on_track_pct": round(
                    100 * sum(token in text for text in corpus) / len(corpus), 2
                ),
                "fires_on_english_pct": round(
                    100 * sum(token in text for text in english) / len(english), 2
                ),
            }
            for token in tokens
        }

    def missed_candidates(track: str, listed: tuple[str, ...]) -> list[dict[str, object]]:
        """Frequent word-forms in the track that are absent from the list and rare in English."""
        import re as _re

        counts: Counter[str] = Counter()
        for text in text_by_track[track]:
            counts.update(set(_re.findall(r"[a-z]{4,}", text)))
        english_counts: Counter[str] = Counter()
        for text in text_by_track["english"]:
            english_counts.update(set(_re.findall(r"[a-z]{4,}", text)))
        total, english_total = len(text_by_track[track]), len(text_by_track["english"])
        ranked = []
        for word, count in counts.most_common(400):
            if any(token in word for token in listed):
                continue
            track_rate = count / total
            english_rate = english_counts[word] / english_total
            if track_rate >= 0.02 and english_rate <= 0.002:
                ranked.append(
                    {
                        "token": word,
                        "track_pct": round(100 * track_rate, 2),
                        "english_pct": round(100 * english_rate, 2),
                    }
                )
        return ranked[:15]

    return {
        "tamilish_token_coverage": coverage(tamilish_tokens, "tamilish"),
        "singlish_token_coverage": coverage(singlish_tokens, "singlish"),
        "tamilish_missed_candidates": missed_candidates("tamilish", tamilish_tokens),
        "singlish_missed_candidates": missed_candidates("singlish", singlish_tokens),
    }


def main() -> None:
    rows: list[Row] = []
    for track in TRACKS:
        rows.extend(load_track(track))

    matrix = confusion(rows)

    # Paired analysis uses only tickets rendered in all five languages.
    by_id: dict[str, dict[str, Row]] = defaultdict(dict)
    for row in rows:
        by_id[row.ticket_id][row.track] = row
    complete = {tid: tracks for tid, tracks in by_id.items() if len(tracks) == len(TRACKS)}

    per_language = {}
    for track in TRACKS:
        hits, total = accuracy(rows, track)
        correct_by_id = {
            tid: tracks[track].detected == track for tid, tracks in complete.items()
        }
        low, high = paired_bootstrap_ci(correct_by_id)
        per_language[track] = {
            "n": total,
            "correct": hits,
            "accuracy": round(hits / total, 4) if total else 0.0,
            "ci95_low": round(low, 4),
            "ci95_high": round(high, 4),
            "misread_as": {
                label: matrix[track][label]
                for label in LABELS
                if label != track and matrix[track][label]
            },
        }

    comparisons = {}
    for index, first in enumerate(TRACKS):
        for second in TRACKS[index + 1 :]:
            only_first = sum(
                tracks[first].detected == first and tracks[second].detected != second
                for tracks in complete.values()
            )
            only_second = sum(
                tracks[second].detected == second and tracks[first].detected != first
                for tracks in complete.values()
            )
            comparisons[f"{first}_vs_{second}"] = {
                "discordant_favouring_first": only_first,
                "discordant_favouring_second": only_second,
                "mcnemar_exact_p": round(mcnemar_exact(only_first, only_second), 6),
            }

    # Representative traces: tickets where the same underlying question is detected
    # correctly in one language and wrongly in another -- the cleanest evidence that
    # the failure is the detector, not the ticket.
    traces = []
    for tid, tracks in complete.items():
        wrong = [t for t in TRACKS if tracks[t].detected != t]
        if len(wrong) == 1 and wrong[0] == "tamilish":
            traces.append(
                {
                    "ticket_id": tid,
                    "english_text": tracks["english"].text,
                    "tamilish_text": tracks["tamilish"].text,
                    "tamilish_detected_as": tracks["tamilish"].detected,
                }
            )
        if len(traces) >= 10:
            break

    report = {
        "diagnostic": "L1a_language_detection",
        "source": "datasets/*/test_labeled.csv (official BANKING77 test ids)",
        "paired_tickets": len(complete),
        "total_rows": len(rows),
        "confusion_matrix": matrix,
        "per_language": per_language,
        "paired_comparisons": comparisons,
        "root_cause": token_diagnostics(rows),
        "representative_traces": traces,
    }
    print(f"wrote {write_report('offline_language', report)}")


if __name__ == "__main__":
    main()
