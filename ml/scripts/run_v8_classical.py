"""Classical baselines re-run against the v8 sentiment labels, frozen split.

Why this exists
---------------
The v8 relabel (2026-08-19) changed 711 of 13,077 sentiment labels and moved the
pooled test set from 505 to 975 Negatives. Six models were re-scored against it;
the classical roster was not. A results table that mixes v5 and v8 rows is not a
model comparison, so every classical cell that appears in the paper has to be
regenerated here.

Two things this does that `train_classical.run` does not:

1. **Fits once, scores many.** The per-language test numbers are the same fitted
   model scored on language subsets, not separate models. Fitting per language
   would be both slower and wrong.
2. **Fits on train+dev for test**, matching what the encoder and decoder test
   runs already stamp as `fit_portion: "train+dev"` (n_train 49,990). Dev runs
   fit on train alone.

Every record stamps `label_version`, which no existing run record carries -- that
absence is exactly why the v5/v8 mix went unnoticed.

Run:
    .venv312/bin/python ml/scripts/run_v8_classical.py
    .venv312/bin/python ml/scripts/run_v8_classical.py --tasks sentiment --models tfidf-svm
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from swiftbench import config, data, imbalance, metrics, models, results, splits  # noqa: E402

LABEL_VERSION = "v8"
BOOTSTRAP_RESAMPLES = 1000

# intent is 77 roughly balanced classes -- the balancing arms exist for the two
# skewed tasks and only muddy the intent table.
TASK_ARMS = {
    "intent": ["none"],
    "sentiment": ["none", "class_weight", "ros"],
    "priority": ["none", "class_weight", "ros"],
}


def bootstrap_ci(y_true, y_pred, task: str, resamples: int = BOOTSTRAP_RESAMPLES,
                 seed: int = config.RANDOM_STATE) -> dict:
    """Percentile CI for the headline metric, resampling evaluation rows.

    For a deterministic estimator on a fixed test set this is the honest variance
    estimate: it answers "how much of this number is the test sample" rather than
    "how much is the seed". Seed variance still needs repeat training runs.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    rng = np.random.default_rng(seed)
    n = len(y_true)

    draws = []
    for _ in range(resamples):
        idx = rng.integers(0, n, size=n)
        # A resample can drop the minority class entirely; zero_division=0 inside
        # metrics.score makes that a 0.0 draw rather than a crash, which is the
        # correct behaviour for the lower tail.
        draws.append(metrics.score(y_true[idx], y_pred[idx], task)["headline"])

    draws = np.asarray(draws, dtype=float)
    return {
        "ci_lower": float(np.percentile(draws, 2.5)),
        "ci_upper": float(np.percentile(draws, 97.5)),
        "ci_mean": float(draws.mean()),
        "ci_std": float(draws.std(ddof=1)),
        "ci_resamples": resamples,
        "ci_method": "percentile bootstrap over evaluation rows",
    }


def fit_and_score(task: str, model: str, arm: str, portion: str,
                  author: str, with_ci: bool) -> list[dict]:
    """One fit, scored pooled and per language. Returns the saved records."""
    label_col = data.label_column(task)

    if portion == "test":
        fit_portion = "train+dev"
        train = splits.get(config.LANGUAGES, "train")
        dev = splits.get(config.LANGUAGES, "dev")
        train = pd.concat([train, dev], ignore_index=True)
    else:
        fit_portion = "train"
        train = splits.get(config.LANGUAGES, "train")

    n_before = len(train)
    train = imbalance.resample(train, label_col, arm)

    t0 = time.time()
    clf = models.build(model, class_weight=imbalance.class_weight_for(arm))
    clf.fit(train[config.TEXT_COLUMN], train[label_col])
    train_seconds = time.time() - t0

    evaluate = splits.get(config.LANGUAGES, portion)
    y_pred_all = clf.predict(evaluate[config.TEXT_COLUMN])

    saved = []
    # "all" is the pooled row; then the same predictions sliced by language.
    for eval_lang in ["all"] + config.LANGUAGES:
        if eval_lang == "all":
            mask = np.ones(len(evaluate), dtype=bool)
        else:
            mask = (evaluate["language"] == eval_lang).to_numpy()

        y_true = evaluate.loc[mask, label_col].to_numpy()
        y_pred = np.asarray(y_pred_all)[mask]

        scores = metrics.score(y_true, y_pred, task)
        scores["n_train"] = int(len(train))
        scores["n_train_before_resample"] = int(n_before)

        extra = {
            "label_version": LABEL_VERSION,
            "fit_portion": fit_portion,
            "family": "classical",
            "regime": "multi",
            "device": "cpu",
            "seed": config.RANDOM_STATE,
            "train_seconds": round(train_seconds, 1),
        }
        if with_ci and portion == "test":
            extra.update(bootstrap_ci(y_true, y_pred, task))

        results.save(task, model, config.LANGUAGES, eval_lang, arm, portion,
                     scores, author=author, extra=extra)
        if eval_lang == "all":
            # Pooled only: the per-language rows are slices of this same frame, so
            # storing them again would just duplicate it.
            results.save_predictions(
                task, model, config.LANGUAGES, eval_lang, arm, portion,
                ids=evaluate["id"].to_numpy(), languages=evaluate["language"].to_numpy(),
                y_true=y_true, y_pred=y_pred)
        saved.append({"eval_lang": eval_lang, **scores, **extra})

        ci = ""
        if "ci_lower" in extra:
            ci = f"  [{extra['ci_lower']:.4f}, {extra['ci_upper']:.4f}]"
        print(f"  {task:9s} {model:13s} arm={arm:12s} {portion:4s} "
              f"ev={eval_lang:9s} {scores['headline_metric']:>11s}="
              f"{scores['headline']:.4f}{ci}", flush=True)

    return saved


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="+", default=["intent", "sentiment", "priority"])
    ap.add_argument("--models", nargs="+", default=models.NAMES)
    ap.add_argument("--portions", nargs="+", default=["dev", "test"])
    ap.add_argument("--author", default="local-v8-sweep")
    ap.add_argument("--no-ci", action="store_true")
    args = ap.parse_args()

    manifest = splits.ensure()
    print(f"split sha {manifest['sha']}  labels {LABEL_VERSION}")
    print(f"tasks={args.tasks} models={args.models} portions={args.portions}\n", flush=True)

    started = time.time()
    total = 0
    for task in args.tasks:
        for model in args.models:
            for arm in TASK_ARMS[task]:
                for portion in args.portions:
                    fit_and_score(task, model, arm, portion,
                                  author=args.author, with_ci=not args.no_ci)
                    total += 1
    print(f"\n{total} fits, {total * 6} records, {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
