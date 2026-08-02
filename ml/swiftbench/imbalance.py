"""Class-balancing arms.

Three arms only: `none`, `class_weight`, `ros`. Deliberately no SMOTE arm --
three papers in `research/` report plain random oversampling matching or beating
SMOTE on code-mixed and low-resource text, and synthetic interpolation between
TF-IDF vectors of two different tickets does not correspond to any sentence
anybody would write. Do not add one.

Oversampling happens on the training rows only, after the split, never on dev
or test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

ARMS = ["none", "class_weight", "ros"]


def class_weight_for(arm: str):
    """The `class_weight` argument to hand the estimator for this arm."""
    return "balanced" if arm == "class_weight" else None


def resample(df: pd.DataFrame, label_col: str, arm: str,
             random_state: int = config.RANDOM_STATE) -> pd.DataFrame:
    """Apply the arm's row-level resampling. Only `ros` changes anything."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {ARMS}")
    if arm != "ros":
        return df

    rng = np.random.default_rng(random_state)
    target = df[label_col].value_counts().max()

    parts = []
    for _, group in df.groupby(label_col, sort=False):
        deficit = target - len(group)
        parts.append(group)
        if deficit > 0:
            picks = rng.integers(0, len(group), size=deficit)
            parts.append(group.iloc[picks])

    out = pd.concat(parts, ignore_index=True)
    return out.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
