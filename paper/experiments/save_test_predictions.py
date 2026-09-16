"""Persist per-row test predictions for the classical roster.

Why separate from `run_v8_classical.py`
---------------------------------------
That script now saves predictions too, so future runs need nothing extra. But the
records it has already written carry 1,000-resample bootstrap CIs that took most
of two hours, and re-running it purely to emit prediction CSVs would rewrite
those records for no gain. This refits the same models and writes **only** the
predictions -- it never touches `ml/reports/runs/`.

Predictions are what a paired significance test needs: comparing two systems
honestly requires knowing which rows each got right, not just how many.

Run:
    .venv312/bin/python paper/experiments/save_test_predictions.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, data, imbalance, models, results, splits  # noqa: E402

# Only the arm that won pooled for each (task, model) -- that is the system the
# paper reports, and predictions for the losing arms would never be cited.
WINNING_ARM = {
    ("intent", "tfidf-logreg"): "none",   ("intent", "tfidf-svm"): "none",
    ("intent", "tfidf-sgd"): "none",      ("intent", "tfidf-cnb"): "none",
    ("sentiment", "tfidf-logreg"): "ros", ("sentiment", "tfidf-svm"): "class_weight",
    ("sentiment", "tfidf-sgd"): "ros",    ("sentiment", "tfidf-cnb"): "ros",
    ("priority", "tfidf-logreg"): "ros",  ("priority", "tfidf-svm"): "class_weight",
    ("priority", "tfidf-sgd"): "ros",     ("priority", "tfidf-cnb"): "class_weight",
}


def main() -> None:
    print(f"split {splits.sha()}  ->  {config.PREDICTIONS_DIR / 'runs'}")
    train = pd.concat([splits.get(config.LANGUAGES, "train"),
                       splits.get(config.LANGUAGES, "dev")], ignore_index=True)
    test = splits.get(config.LANGUAGES, "test")

    started = time.time()
    for (task, model), arm in WINNING_ARM.items():
        label_col = data.label_column(task)
        fit = imbalance.resample(train, label_col, arm)
        clf = models.build(model, class_weight=imbalance.class_weight_for(arm))
        clf.fit(fit[config.TEXT_COLUMN], fit[label_col])
        y_pred = clf.predict(test[config.TEXT_COLUMN])

        path = results.save_predictions(
            task, model, config.LANGUAGES, "all", arm, "test",
            ids=test["id"].to_numpy(), languages=test["language"].to_numpy(),
            y_true=test[label_col].to_numpy(), y_pred=y_pred)
        agree = float((test[label_col].to_numpy() == y_pred).mean())
        print(f"  {task:9s} {model:13s} arm={arm:12s} acc={agree:.4f}  {Path(path).name}")

    print(f"\n{len(WINNING_ARM)} prediction files, {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
