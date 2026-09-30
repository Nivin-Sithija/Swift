"""Is the Negative label polarity, or is it a topic?

`RESULTS.md` records the observation that "Negative looks like a topic construct,
not polarity" -- a mined lexicon returned fraud and loss markers rather than
sentiment words. That was an observation about a word list. It has never been
tested, and it is one of the paper's more interesting claims, so it needs a
number.

The decisive test needs no text at all
--------------------------------------
If `Negative` really encodes *what the ticket is about* rather than *how the
customer sounds*, then the 77-way intent label alone should predict it. Intent is
BANKING77's human gold and contains no tone information whatsoever -- two tickets
with the same intent can be furious or perfectly calm.

So: fit a predictor that sees **only the intent label**, and compare its
Negative-F1 to the text-based champion's.

  - If intent-only lands near the text model, the label is largely topic.
  - If intent-only is near zero, the label carries genuine tone the text model
    is reading.

The intent-only rule is fit on train+dev and applied to test, exactly like every
other system here, so the comparison is like-for-like.

Run:
    .venv312/bin/python paper/experiments/negative_is_topic.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, metrics, splits  # noqa: E402

OUT = REPO / "paper" / "results" / "tables"
PRED_DIR = config.PREDICTIONS_DIR / "runs"


def main() -> None:
    train = pd.concat([splits.get(config.LANGUAGES, "train"),
                       splits.get(config.LANGUAGES, "dev")], ignore_index=True)
    test = splits.get(config.LANGUAGES, "test")

    # Per-intent Negative rate, learned on train+dev only.
    rate = train.groupby("category")["sentiment"].apply(
        lambda s: float((s == "Negative").mean()))
    prior = float((train["sentiment"] == "Negative").mean())

    p_test = test["category"].map(rate).fillna(prior).to_numpy()
    y_true = test["sentiment"].to_numpy()

    # Sweep the threshold on train+dev, never on test -- picking it on test would
    # be exactly the selection-on-test defect this project has already been bitten by.
    p_train = train["category"].map(rate).fillna(prior).to_numpy()
    y_train = train["sentiment"].to_numpy()
    grid = np.unique(np.round(np.linspace(0.01, 0.99, 99), 4))
    best_t, best_f1 = 0.5, -1.0
    for t in grid:
        pred = np.where(p_train >= t, "Negative", "Neutral")
        f1 = metrics.score(y_train, pred, "sentiment")["headline"]
        if f1 > best_f1:
            best_t, best_f1 = float(t), f1

    pred_test = np.where(p_test >= best_t, "Negative", "Neutral")
    topic_only = metrics.score(y_true, pred_test, "sentiment")

    # The text-based champion, for comparison.
    hits = sorted(PRED_DIR.glob("sentiment__tfidf-svm__*__ev-all__*__test.csv"))
    text_f1 = None
    if hits:
        tp = pd.read_csv(hits[0])
        text_f1 = metrics.score(tp["y_true"], tp["y_pred"], "sentiment")["headline"]

    # How concentrated is Negative in a handful of intents?
    counts = (train[train["sentiment"] == "Negative"]["category"]
              .value_counts(normalize=True))
    top10 = float(counts.head(10).sum())
    n_intents_90 = int((counts.cumsum() <= 0.90).sum() + 1)

    rows = [{
        "system": "intent-label only (no text)",
        "negative_f1": round(topic_only["headline"], 4),
        "precision": round(topic_only["negative_precision"], 4),
        "recall": round(topic_only["negative_recall"], 4),
        "threshold": best_t,
        "note": "sees only BANKING77's 77-way gold intent; contains no tone information",
    }]
    if text_f1 is not None:
        rows.append({
            "system": "tfidf-svm on text",
            "negative_f1": round(text_f1, 4), "precision": None, "recall": None,
            "threshold": None, "note": "the classical champion, for comparison",
        })
        rows.append({
            "system": "topic share of the text model",
            "negative_f1": round(topic_only["headline"] / text_f1, 4),
            "precision": None, "recall": None, "threshold": None,
            "note": "fraction of the champion's Negative-F1 reachable from intent alone",
        })

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "negative_is_topic.csv", index=False)

    print(df.to_string(index=False))
    print(f"\nNegative concentration in train+dev: top 10 of 77 intents hold "
          f"{100*top10:.1f}% of all Negatives; {n_intents_90} intents cover 90%.")
    print("\nMost Negative-heavy intents (rate within intent):")
    print(rate.sort_values(ascending=False).head(10).round(3).to_string())
    print(f"\nwritten to {(OUT / 'negative_is_topic.csv').relative_to(REPO)}")


if __name__ == "__main__":
    main()
