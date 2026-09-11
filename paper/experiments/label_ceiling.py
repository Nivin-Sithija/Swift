"""The label ceiling: how good a classifier could possibly look on these labels.

The paper's central claim is that label quality, not model capacity, binds
sentiment. That claim is a comparison between two numbers -- the champion's score
and the ceiling -- so the ceiling has to be computed against exactly the labels
the champion trained on, and joined to the human gold set without error.

Two things this fixes
---------------------
**The join.** The gold benchmark's `id` column matches 1,000 dataset rows (train
and test ids overlap) and its `row_id` matches only 76% of texts. Neither is a
key. This joins on normalised text and then *verifies* the join by checking the
intent column, which neither side ever modified: a correct join gives exactly
1.0 agreement there, and anything less means the rows are misaligned.

**Which labels get scored.** The recorded ceiling of 0.7812 scored
`prompt_v8_all_labels.csv`'s `sentiment_pred` -- the prompt's raw output. The
shipped CSVs differ from that on 8 of the 500 gold rows, so models train on
something the recorded ceiling did not measure. The ceiling the paper needs is
against the shipped labels.

When the inter-annotator batch returns (task C2), rerun with `--with-iaa` to get
the human-human bound alongside, which is what turns "agreement with one person"
into "the task's reliability limit".

Run:
    .venv312/bin/python paper/experiments/label_ceiling.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, data, metrics  # noqa: E402

GOLD = REPO / "ml" / "reports" / "500_benchmarkset.csv"
PROMPT = REPO / "ml" / "reports" / "prompt_v8_all_labels.csv"
RETURNED = REPO / "paper" / "annotation" / "returned"
OUT = REPO / "paper" / "results" / "tables"
RESAMPLES = 1000


def norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)


def join_gold() -> pd.DataFrame:
    gold = pd.read_csv(GOLD)
    eng = pd.concat([data.load_language("english", "train"),
                     data.load_language("english", "test")], ignore_index=True)
    gold["_n"] = norm(gold["text"])
    eng["_n"] = norm(eng["text_en"])

    ds = (eng[["_n", "id", "sentiment", "priority", "category"]]
          .drop_duplicates("_n")
          .rename(columns={"id": "ds_id", "sentiment": "sent_shipped",
                           "priority": "pri_shipped", "category": "cat_shipped"}))
    m = gold.merge(ds, on="_n", how="left")

    unmatched = int(m["ds_id"].isna().sum())
    if unmatched:
        raise SystemExit(f"{unmatched} gold rows did not join -- do not trust any number below")

    # The join's own test. Intent came from BANKING77 and was never edited on either
    # side, so anything below 1.0 means rows are paired with the wrong tickets.
    intent_agreement = float((m["category"] == m["cat_shipped"]).mean())
    if intent_agreement < 1.0:
        raise SystemExit(f"join verification failed: intent agreement {intent_agreement:.4f}, "
                         "expected 1.0 -- rows are misaligned")
    print(f"joined {len(m)}/500 on normalised text; intent agreement 1.0000 (join verified)")
    return m


def bootstrap(y_true, y_pred, task: str, seed: int = config.RANDOM_STATE) -> tuple[float, float]:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    rng = np.random.default_rng(seed)
    draws = [metrics.score(y_true[i], y_pred[i], task)["headline"]
             for i in (rng.integers(0, len(y_true), len(y_true)) for _ in range(RESAMPLES))]
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def cohen_kappa(a, b) -> float:
    a, b = pd.Series(list(a)), pd.Series(list(b))
    labels = sorted(set(a) | set(b))
    observed = float((a.to_numpy() == b.to_numpy()).mean())
    expected = sum((a == l).mean() * (b == l).mean() for l in labels)
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-iaa", action="store_true",
                    help="also read paper/annotation/returned/ for the human-human bound")
    args = ap.parse_args()

    m = join_gold()
    rows = []

    for task, human_col, shipped_col in (("sentiment", "sentiment", "sent_shipped"),
                                         ("priority", "priority", "pri_shipped")):
        lo, hi = bootstrap(m[human_col], m[shipped_col], task)
        rows.append({
            "task": task, "compared": "shipped labels vs human gold",
            "n": len(m),
            "headline": round(metrics.score(m[human_col], m[shipped_col], task)["headline"], 4),
            "ci_low": round(lo, 4), "ci_high": round(hi, 4),
            "agreement": round(float((m[human_col] == m[shipped_col]).mean()), 4),
            "cohen_kappa": round(cohen_kappa(m[human_col], m[shipped_col]), 4),
            "note": "the labels models actually train on -- this is the ceiling to quote",
        })

    # The prompt's raw output, for the record: it is what the previously published
    # 0.7812 measured, and it is not what shipped.
    if PROMPT.exists():
        p = pd.read_csv(PROMPT)
        p["_n"] = norm(p["text"])
        j = m.merge(p[["_n", "sentiment_pred"]], on="_n", how="inner")
        if len(j):
            drift = int((j["sentiment_pred"].astype(str) != j["sent_shipped"].astype(str)).sum())
            lo, hi = bootstrap(j["sentiment"], j["sentiment_pred"], "sentiment")
            rows.append({
                "task": "sentiment", "compared": "prompt v8 raw output vs human gold",
                "n": len(j),
                "headline": round(metrics.score(j["sentiment"], j["sentiment_pred"],
                                                "sentiment")["headline"], 4),
                "ci_low": round(lo, 4), "ci_high": round(hi, 4),
                "agreement": round(float((j["sentiment"] == j["sentiment_pred"]).mean()), 4),
                "cohen_kappa": round(cohen_kappa(j["sentiment"], j["sentiment_pred"]), 4),
                "note": f"superseded: differs from shipped on {drift}/{len(j)} rows",
            })

    if args.with_iaa:
        found = sorted(RETURNED.glob("batch_*.csv"))
        if not found:
            print(f"  no returned annotation files in {RETURNED.relative_to(REPO)}/ -- "
                  "human-human bound not computed (task C2)")
        else:
            print(f"  found {len(found)} returned annotator file(s)")
            # Deliberately delegated: build_annotation_batches.py score is the one
            # place that knows the batch layout and computes kappa/alpha.
            print("  run: .venv312/bin/python paper/experiments/build_annotation_batches.py score")

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "label_ceiling.csv", index=False)
    print()
    print(df.to_string(index=False))
    print(f"\nwritten to {(OUT / 'label_ceiling.csv').relative_to(REPO)}")


if __name__ == "__main__":
    main()
