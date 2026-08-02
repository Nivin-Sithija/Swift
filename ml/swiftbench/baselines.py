"""Model-free floors.

Every trained model has to be read against these. Two of them are the reason
this module exists at all:

- **majority** on sentiment scores ~0.956 accuracy by answering "Neutral" to
  everything. Any sentiment result quoted as accuracy is meaningless.
- **intent_lookup** on priority maps each intent to the most common priority
  seen for that intent in train. Given *gold* intent this is very strong -- but
  it is an **oracle**, not a bar, because at serving time nobody hands you the
  gold intent. `intent_chained` is the honest version: run the real intent
  classifier, then look up. That is the number a direct priority model has to
  beat to justify existing.
"""
from __future__ import annotations

import pandas as pd

from . import config, data, metrics


def majority(train: pd.DataFrame, evaluate: pd.DataFrame, task: str) -> dict:
    """Always predict the most frequent training label."""
    col = data.label_column(task)
    label = train[col].value_counts().idxmax()
    y_pred = [label] * len(evaluate)
    out = metrics.score(evaluate[col], y_pred, task)
    out["constant_label"] = label
    return out


def build_intent_lookup(train: pd.DataFrame, task: str) -> dict:
    """intent -> most common label for that intent in train."""
    col = data.label_column(task)
    intent_col = data.label_column("intent")
    table = (
        train.groupby(intent_col)[col]
        .agg(lambda s: s.value_counts().idxmax())
        .to_dict()
    )
    return table


def intent_lookup(train: pd.DataFrame, evaluate: pd.DataFrame, task: str) -> dict:
    """ORACLE. Uses the gold intent of the evaluation rows -- not servable."""
    col = data.label_column(task)
    intent_col = data.label_column("intent")
    table = build_intent_lookup(train, task)
    fallback = train[col].value_counts().idxmax()

    y_pred = [table.get(i, fallback) for i in evaluate[intent_col]]
    out = metrics.score(evaluate[col], y_pred, task)
    out["is_oracle"] = True
    out["note"] = "uses gold intent; upper bound, not a target"
    return out


def intent_chained(train: pd.DataFrame, evaluate: pd.DataFrame, task: str,
                   intent_model: str = "tfidf-svm") -> dict:
    """Honest version: predict intent from text, then look up the label.

    This is the real bar for a direct text -> priority model.
    """
    from . import models

    col = data.label_column(task)
    intent_col = data.label_column("intent")

    clf = models.build(intent_model)
    clf.fit(train[config.TEXT_COLUMN], train[intent_col])
    predicted_intent = clf.predict(evaluate[config.TEXT_COLUMN])

    table = build_intent_lookup(train, task)
    fallback = train[col].value_counts().idxmax()
    y_pred = [table.get(i, fallback) for i in predicted_intent]

    out = metrics.score(evaluate[col], y_pred, task)
    out["is_oracle"] = False
    out["intent_model"] = intent_model
    out["intent_accuracy"] = float(
        (predicted_intent == evaluate[intent_col].values).mean()
    )
    return out
