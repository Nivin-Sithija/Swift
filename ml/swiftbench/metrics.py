"""Task-aware scoring.

Each task gets a single `headline` number, because the obvious metric is
misleading for two of the three tasks:

- **sentiment** is 95%+ Neutral. Predicting "Neutral" for every ticket scores
  ~0.956 accuracy while catching zero of the angry customers the escalation
  path exists for. Headline is therefore F1 on the Negative class alone.
- **priority** is dominated by Low. Accuracy hides collapse on High, which is
  the class with the operational cost. Headline is macro-F1.
- **intent** is 77 roughly balanced classes, so macro-F1 is honest.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)

from . import config

HEADLINE = {
    "intent": "macro_f1",
    "sentiment": "negative_f1",
    "priority": "macro_f1",
}

LABELS = {
    "sentiment": config.SENTIMENT_LABELS,
    "priority": config.PRIORITY_LABELS,
    "intent": None,  # 77 classes, inferred from the data
}


def score(y_true, y_pred, task: str) -> dict:
    """All metrics for a task, plus a `headline` key naming the one that counts."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(macro_f1),
        "macro_precision": float(macro_p),
        "macro_recall": float(macro_r),
        "weighted_f1": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "n": int(len(y_true)),
    }

    if task == "sentiment":
        pos = config.SENTIMENT_POSITIVE_CLASS
        p, r, f, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=[pos], average="binary",
            pos_label=pos, zero_division=0,
        )
        out["negative_f1"] = float(f)
        out["negative_precision"] = float(p)
        out["negative_recall"] = float(r)
        out["n_negative_true"] = int((y_true == pos).sum())
        out["n_negative_pred"] = int((y_pred == pos).sum())

    if task == "priority":
        per_class = f1_score(
            y_true, y_pred, labels=config.PRIORITY_LABELS,
            average=None, zero_division=0,
        )
        for label, val in zip(config.PRIORITY_LABELS, per_class):
            out[f"f1_{label.lower()}"] = float(val)

    out["headline_metric"] = HEADLINE[task]
    out["headline"] = out[HEADLINE[task]]
    return out


def per_class_table(y_true, y_pred, task: str) -> dict:
    return classification_report(
        y_true, y_pred, labels=LABELS.get(task), output_dict=True, zero_division=0
    )


def confusion(y_true, y_pred, task: str):
    labels = LABELS.get(task)
    if labels is None:
        labels = sorted(set(np.asarray(y_true)) | set(np.asarray(y_pred)))
    return labels, confusion_matrix(y_true, y_pred, labels=labels).tolist()
