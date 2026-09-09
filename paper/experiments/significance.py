"""Paired significance tests between systems on the test set.

Nothing in this project has ever carried a p-value, so every ranking in it is
"A scored higher than B" with no statement about whether that would survive a
different sample. Two tests, because they answer different questions:

**Paired bootstrap** on the headline metric. Resamples *test rows* -- the same
rows for both systems on every draw, which is what makes it paired -- and reports
how often the observed direction reverses. This is the right test for macro-F1
and Negative-F1, which are not row-decomposable and so have no per-row statistic
a sign test could use.

**McNemar** on per-row correctness. Ignores the rows both systems get right or
both get wrong, and asks whether the disagreements are lopsided. Sharper than the
bootstrap when the systems are highly correlated, which fine-tuned models on the
same corpus always are.

Both need per-row predictions, which is why `save_test_predictions.py` exists.

A caveat this cannot fix: these test whether two *fitted models* differ on this
test set. They say nothing about seed variance, which needs repeated training
runs (task A6). Report both or the CIs will read as tighter than they are.

Run:
    .venv312/bin/python paper/experiments/significance.py
    .venv312/bin/python paper/experiments/significance.py --task sentiment
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, metrics, results  # noqa: E402

OUT = REPO / "paper" / "results" / "tables"
PRED_DIR = config.PREDICTIONS_DIR / "runs"
TASKS = ["intent", "sentiment", "priority"]
RESAMPLES = 1000


def discover(task: str) -> dict[str, pd.DataFrame]:
    """Every system with saved test predictions for this task, keyed by model name."""
    out = {}
    for path in sorted(PRED_DIR.glob(f"{task}__*__ev-all__*__test.csv")):
        model = path.name.split("__")[1]
        out[model] = pd.read_csv(path)
    return out


def _encode(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[np.ndarray, np.ndarray, list]:
    classes = sorted(set(y_true) | set(y_pred))
    lut = {c: i for i, c in enumerate(classes)}
    return (np.array([lut[v] for v in y_true]),
            np.array([lut[v] for v in y_pred]), classes)


def _headline_from_counts(counts: np.ndarray, task: str, pos: int | None) -> float:
    """Headline metric from a K x K confusion matrix (rows true, cols predicted).

    `metrics.score` costs 72 ms per call, which puts a 1,000-resample bootstrap
    over three tasks past an hour. The metric only ever depends on per-class
    TP/FP/FN, so each resample reduces to one `bincount` and some arithmetic --
    about 2,000x faster, and verified equal to `metrics.score` in `_selftest`.
    """
    tp = np.diag(counts).astype(float)
    fp = counts.sum(0) - tp
    fn = counts.sum(1) - tp
    denom = 2 * tp + fp + fn
    f1 = np.divide(2 * tp, denom, out=np.zeros_like(tp), where=denom > 0)

    if task == "sentiment":
        return float(f1[pos]) if pos is not None else float("nan")
    # sklearn's macro average with zero_division=0 spans the labels present in
    # either y_true or y_pred for *this* sample, so a resample that drops a rare
    # class averages over fewer of them. Match that, or the CI drifts.
    present = (counts.sum(1) > 0) | (counts.sum(0) > 0)
    return float(f1[present].mean()) if present.any() else 0.0


def _selftest(y_true, y_pred, task) -> None:
    """Confusion-matrix headline must equal metrics.score on the full sample.

    Encodes independently rather than reusing the caller's label space, so this
    checks the formula itself and not just that two encodings agree.
    """
    t, p, classes = _encode(y_true, y_pred)
    k = len(classes)
    counts = np.bincount(t * k + p, minlength=k * k).reshape(k, k)
    pos = (classes.index(config.SENTIMENT_POSITIVE_CLASS)
           if task == "sentiment" and config.SENTIMENT_POSITIVE_CLASS in classes else None)
    fast = _headline_from_counts(counts, task, pos)
    slow = metrics.score(y_true, y_pred, task)["headline"]
    if abs(fast - slow) > 1e-9:
        raise AssertionError(f"{task}: fast headline {fast} != metrics.score {slow}")


def paired_bootstrap(a: pd.DataFrame, b: pd.DataFrame, task: str,
                     resamples: int = RESAMPLES, seed: int = config.RANDOM_STATE) -> dict:
    """Two-sided paired bootstrap on the headline metric."""
    # Align on (id, language): the same ticket exists five times, so id alone is not a key.
    key = ["id", "language"]
    merged = a.merge(b, on=key, suffixes=("_a", "_b"))
    if len(merged) != len(a):
        raise ValueError(f"alignment lost rows: {len(a)} -> {len(merged)}")
    if not (merged["y_true_a"] == merged["y_true_b"]).all():
        raise ValueError("the two systems were scored against different labels")

    y_true = merged["y_true_a"].to_numpy()
    pa, pb = merged["y_pred_a"].to_numpy(), merged["y_pred_b"].to_numpy()

    obs = (metrics.score(y_true, pa, task)["headline"]
           - metrics.score(y_true, pb, task)["headline"])

    # One shared label space for both systems, so the two confusion matrices are
    # the same shape and the same class index means the same class in each.
    classes = sorted(set(y_true) | set(pa) | set(pb))
    lut = {c: i for i, c in enumerate(classes)}
    k = len(classes)
    t = np.array([lut[v] for v in y_true])
    ia = t * k + np.array([lut[v] for v in pa])
    ib = t * k + np.array([lut[v] for v in pb])
    pos = lut.get(config.SENTIMENT_POSITIVE_CLASS) if task == "sentiment" else None

    _selftest(y_true, pa, task)
    _selftest(y_true, pb, task)

    rng = np.random.default_rng(seed)
    n = len(y_true)
    deltas = np.empty(resamples)
    for i in range(resamples):
        idx = rng.integers(0, n, size=n)
        ca = np.bincount(ia[idx], minlength=k * k).reshape(k, k)
        cb = np.bincount(ib[idx], minlength=k * k).reshape(k, k)
        deltas[i] = (_headline_from_counts(ca, task, pos)
                     - _headline_from_counts(cb, task, pos))

    # Fraction of draws on the opposite side of zero from the observed difference,
    # doubled for a two-sided test.
    p = 2 * (np.mean(deltas <= 0) if obs > 0 else np.mean(deltas >= 0))
    return {"delta": float(obs),
            "delta_ci_lower": float(np.percentile(deltas, 2.5)),
            "delta_ci_upper": float(np.percentile(deltas, 97.5)),
            "p_bootstrap": float(min(p, 1.0))}


def mcnemar(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    """Exact McNemar on per-row correctness."""
    from scipy.stats import binomtest

    key = ["id", "language"]
    m = a.merge(b, on=key, suffixes=("_a", "_b"))
    ca = (m["y_pred_a"] == m["y_true_a"]).to_numpy()
    cb = (m["y_pred_b"] == m["y_true_b"]).to_numpy()

    b_only = int((ca & ~cb).sum())    # a right, b wrong
    c_only = int((~ca & cb).sum())    # a wrong, b right
    if b_only + c_only == 0:
        return {"a_only_correct": 0, "b_only_correct": 0, "p_mcnemar": 1.0}
    # Exact binomial rather than the chi-square approximation: discordant counts
    # get small on the easier tasks and the approximation is unreliable there.
    p = binomtest(b_only, b_only + c_only, 0.5).pvalue
    return {"a_only_correct": b_only, "b_only_correct": c_only, "p_mcnemar": float(p)}


def to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    numeric = {c for c in cols if pd.api.types.is_numeric_dtype(df[c])}
    cells = [[("" if pd.isna(v) else str(v)) for v in r] for r in df.to_numpy()]
    w = {c: max(len(c), *(len(r[i]) for r in cells)) if cells else len(c)
         for i, c in enumerate(cols)}
    ln = lambda vals: "| " + " | ".join(  # noqa: E731
        v.rjust(w[c]) if c in numeric else v.ljust(w[c]) for c, v in zip(cols, vals)) + " |"
    rule = "|" + "|".join(("-" * (w[c] + 1) + ":") if c in numeric else (":" + "-" * (w[c] + 1))
                          for c in cols) + "|"
    return "\n".join([ln(cols), rule, *(ln(r) for r in cells)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="+", default=TASKS)
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    args = ap.parse_args()

    rows = []
    for task in args.tasks:
        systems = discover(task)
        if len(systems) < 2:
            print(f"{task}: {len(systems)} system(s) with predictions, need 2+ -- skipped")
            continue
        print(f"{task}: {len(systems)} systems -> {len(list(itertools.combinations(systems, 2)))} pairs")
        for a_name, b_name in itertools.combinations(sorted(systems), 2):
            a, b = systems[a_name], systems[b_name]
            r = {"task": task, "system_a": a_name, "system_b": b_name}
            r.update(paired_bootstrap(a, b, task, args.resamples))
            r.update(mcnemar(a, b))
            r["significant_05"] = bool(r["p_bootstrap"] < 0.05 and r["p_mcnemar"] < 0.05)
            rows.append(r)
            print(f"  {a_name:13s} vs {b_name:13s} "
                  f"delta={r['delta']:+.4f} [{r['delta_ci_lower']:+.4f}, {r['delta_ci_upper']:+.4f}] "
                  f"p_boot={r['p_bootstrap']:.4f} p_mcnemar={r['p_mcnemar']:.3g}"
                  f"{'  *' if r['significant_05'] else ''}")

    if not rows:
        print("\nno pairs scored -- run save_test_predictions.py first")
        return

    df = pd.DataFrame(rows).round(6)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "significance.csv", index=False)
    (OUT / "significance.md").write_text(
        f"<!-- generated by paper/experiments/significance.py · {args.resamples} resamples · "
        f"two-sided · '*' = both tests below 0.05 -->\n\n" + to_markdown(df) + "\n")
    print(f"\n{len(df)} pairs -> paper/results/tables/significance.{{csv,md}}")


if __name__ == "__main__":
    main()
