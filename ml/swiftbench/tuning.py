"""Statistical rigour: confidence intervals, thresholds, cross-validation.

This module exists because of one measurement: **dev contains 68 Negative
tickets.** Bootstrapping the sentiment champion gives a 95% CI of roughly
[0.554, 0.722] -- a width of 0.168. Every configuration in the top ten of the
bake-off sits inside that interval, so ranking them is reading noise.

Pooling the five languages does not help. The pooled dev set has 340 Negative
rows but only **68 unique Negative tickets**; the other 272 are translations of
those same tickets. Effective sample size is 68, not 340, and any CI computed
over the 340 rows is dishonestly narrow.

Two consequences, both implemented here:

- `bootstrap_ci` resamples **by ticket id**, not by row, so the interval
  reflects the real number of independent observations.
- `cross_validate` gives a tighter estimate than a single dev split by reusing
  train+dev across folds -- the right tool for selecting among close models.

And one thing the bake-off never did: every model was scored at the default
0.5 decision threshold. `tune_threshold` fixes that. On the sentiment champion
it is worth about +0.027 Negative-F1, which is larger than most of the gaps the
bake-off was ranking models on.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from . import config, imbalance, metrics, models


def bootstrap_ci(y_true, y_pred, task: str, groups=None, n_boot: int = 2000,
                 alpha: float = 0.05, random_state: int = config.RANDOM_STATE) -> dict:
    """Percentile bootstrap CI for a task's headline metric.

    `groups` should be the ticket `id` of each row. When given, resampling is
    done over unique ids and all rows of a sampled id travel together -- the
    five language copies of one ticket are not five independent draws.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    rng = np.random.default_rng(random_state)

    point = metrics.score(y_true, y_pred, task)["headline"]

    if groups is None:
        draws = [rng.integers(0, len(y_true), len(y_true)) for _ in range(n_boot)]
    else:
        groups = np.asarray(groups)
        unique = np.unique(groups)
        by_group = {g: np.flatnonzero(groups == g) for g in unique}
        draws = []
        for _ in range(n_boot):
            picked = rng.integers(0, len(unique), len(unique))
            draws.append(np.concatenate([by_group[unique[i]] for i in picked]))

    stats = []
    for idx in draws:
        try:
            stats.append(metrics.score(y_true[idx], y_pred[idx], task)["headline"])
        except (ValueError, ZeroDivisionError):
            continue

    lo, hi = np.percentile(stats, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "headline": float(point),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "ci_width": float(hi - lo),
        "n_effective": int(len(np.unique(groups)) if groups is not None else len(y_true)),
        "n_rows": int(len(y_true)),
    }


def tune_threshold(estimator, X, y_true, task: str, min_recall: float | None = None,
                   grid: np.ndarray | None = None) -> dict:
    """Pick the decision threshold on the positive class.

    Tune this on dev or in cross-validation, never on test. With
    `min_recall`, returns the best-F1 threshold that still clears that recall --
    the escalation use case cares more about not missing angry customers than
    about precision, and that is a product decision, not an ML one.
    """
    if task != "sentiment":
        raise ValueError("threshold tuning is defined here for binary sentiment only")

    pos = config.SENTIMENT_POSITIVE_CLASS
    neg = [l for l in config.SENTIMENT_LABELS if l != pos][0]
    grid = np.arange(0.02, 0.99, 0.01) if grid is None else grid

    scores = _positive_scores(estimator, X, pos)
    y_true = np.asarray(y_true)

    rows = []
    for t in grid:
        pred = np.where(scores >= t, pos, neg)
        s = metrics.score(y_true, pred, task)
        rows.append({"threshold": float(t), "negative_f1": s["negative_f1"],
                     "negative_precision": s["negative_precision"],
                     "negative_recall": s["negative_recall"],
                     "accuracy": s["accuracy"]})
    curve = pd.DataFrame(rows)

    eligible = curve if min_recall is None else curve[curve.negative_recall >= min_recall]
    if eligible.empty:
        raise ValueError(f"no threshold reaches recall >= {min_recall}")
    best = eligible.loc[eligible.negative_f1.idxmax()]

    default = metrics.score(y_true, np.where(scores >= 0.5, pos, neg), task)
    return {
        "threshold": float(best.threshold),
        "negative_f1": float(best.negative_f1),
        "negative_precision": float(best.negative_precision),
        "negative_recall": float(best.negative_recall),
        "default_threshold_negative_f1": float(default["negative_f1"]),
        "gain_over_default": float(best.negative_f1 - default["negative_f1"]),
        "min_recall": min_recall,
        "curve": curve,
    }


def _positive_scores(estimator, X, pos_label) -> np.ndarray:
    """P(positive) if available, else a min-max normalised decision function.

    LinearSVC has no `predict_proba`; its `decision_function` is monotonic in
    the same direction, so thresholding it is valid even though the values are
    not probabilities.
    """
    if hasattr(estimator, "predict_proba"):
        classes = list(estimator.classes_)
        return estimator.predict_proba(X)[:, classes.index(pos_label)]

    raw = estimator.decision_function(X)
    if raw.ndim > 1:
        classes = list(estimator.classes_)
        raw = raw[:, classes.index(pos_label)]
    elif list(estimator.classes_)[1] != pos_label:
        raw = -raw
    return (raw - raw.min()) / (raw.max() - raw.min() + 1e-12)


def cross_validate(task: str, model: str, langs: list[str], arm: str = "none",
                   C: float = 1.0, n_splits: int = 5,
                   random_state: int = config.RANDOM_STATE,
                   tune_thresholds: bool = False) -> pd.DataFrame:
    """Stratified k-fold over train+dev, split on ticket `id`.

    Folds are drawn over unique ids and fanned out to every language, exactly
    like the frozen split -- otherwise a ticket's English copy trains while its
    Sinhala copy validates.

    Uses train+dev rather than train alone. That is legitimate for *model
    selection* and gives a much tighter estimate than 68 Negative dev tickets
    can; the frozen test set remains untouched and is still the only clean
    estimate of final performance.
    """
    from . import data, splits

    label_col = data.label_column(task)
    manifest = splits.ensure()
    pool_ids = sorted(set(manifest["train_ids"]) | set(manifest["dev_ids"]))

    english = data.load_language("english", "train").set_index("id")
    strat = english.loc[pool_ids, label_col].values

    frames = {lang: data.load_language(lang, "train") for lang in langs}
    kfold = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    rows = []
    for fold, (tr_pos, va_pos) in enumerate(kfold.split(pool_ids, strat)):
        tr_ids = {pool_ids[i] for i in tr_pos}
        va_ids = {pool_ids[i] for i in va_pos}

        train = pd.concat([f[f.id.isin(tr_ids)] for f in frames.values()], ignore_index=True)
        valid = pd.concat([f[f.id.isin(va_ids)] for f in frames.values()], ignore_index=True)
        train = imbalance.resample(train, label_col, arm)

        clf = models.build(model, class_weight=imbalance.class_weight_for(arm), C=C)
        clf.fit(train[config.TEXT_COLUMN], train[label_col])

        scores = metrics.score(valid[label_col], clf.predict(valid[config.TEXT_COLUMN]), task)
        row = {"fold": fold, "model": model, "arm": arm, "C": C,
               "headline": scores["headline"], "accuracy": scores["accuracy"],
               "macro_f1": scores["macro_f1"], "n_valid": len(valid)}

        if tune_thresholds and task == "sentiment":
            tuned = tune_threshold(clf, valid[config.TEXT_COLUMN], valid[label_col], task)
            row["tuned_threshold"] = tuned["threshold"]
            row["tuned_headline"] = tuned["negative_f1"]

        rows.append(row)

    return pd.DataFrame(rows)


def summarise_cv(cv: pd.DataFrame) -> dict:
    """Mean +/- std across folds, with the fold-level standard error."""
    out = {"mean_headline": float(cv.headline.mean()),
           "std_headline": float(cv.headline.std(ddof=1)),
           "sem_headline": float(cv.headline.std(ddof=1) / np.sqrt(len(cv))),
           "n_folds": int(len(cv))}
    if "tuned_headline" in cv.columns:
        out["mean_tuned_headline"] = float(cv.tuned_headline.mean())
        out["mean_tuned_threshold"] = float(cv.tuned_threshold.mean())
    return out
