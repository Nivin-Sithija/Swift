"""Is the per-language deficit real, or is it sampling noise?

The paper's largest per-language claim is that Tanglish trails every other track
by a wide margin -- intent error +28.9pp over English on the classical champion.
That has never been tested. It is quoted as a difference between two point
estimates on 3,079 rows each.

The comparison is **paired**, which most readers will not expect and which makes
it much sharper than it looks: the same 3,079 ticket ids appear in all five
tracks, so the English and Tanglish predictions are two labellings of the same
tickets. McNemar applies directly -- of the tickets where exactly one track is
correct, is the split lopsided?

Two questions, both answered per model:

  1. **Track vs English.** Same tickets, same model, different language. This is
     the deficit the paper claims.
  2. **Is the deficit bigger than the gap between the two English-adjacent
     tracks?** Reported alongside so a reader can see the scale of ordinary
     cross-track variation before reading the Tanglish number as exceptional.

Run:
    .venv312/bin/python paper/experiments/language_gap.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from significance import _headline_from_counts  # noqa: E402
from swiftbench import config, metrics  # noqa: E402

RESAMPLES = 1000

OUT = REPO / "paper" / "results" / "tables"
PRED_DIR = config.PREDICTIONS_DIR / "runs"
TASKS = ["intent", "sentiment", "priority"]
REFERENCE = "english"


def paired_mcnemar(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    """a and b are the same model's predictions on the same ids, two languages."""
    m = a.merge(b, on="id", suffixes=("_a", "_b"))
    ca = (m["y_pred_a"] == m["y_true_a"]).to_numpy()
    cb = (m["y_pred_b"] == m["y_true_b"]).to_numpy()
    a_only = int((ca & ~cb).sum())
    b_only = int((~ca & cb).sum())
    n_disc = a_only + b_only
    p = binomtest(a_only, n_disc, 0.5).pvalue if n_disc else 1.0
    return {"n_paired": len(m), "ref_only_correct": a_only,
            "track_only_correct": b_only, "discordant": n_disc, "p_mcnemar": float(p)}


def paired_bootstrap_headline(ref: pd.DataFrame, track: pd.DataFrame, task: str,
                              seed: int = config.RANDOM_STATE) -> dict:
    """Paired bootstrap on the headline metric, resampling ticket ids.

    McNemar above tests **row correctness**, i.e. accuracy. On sentiment the
    headline is Negative-F1, and the two disagree in sign on real rows here: a
    track can make fewer errors overall while scoring worse on the only class that
    matters. Reporting McNemar alone would mark those "significant" in the wrong
    direction. The pairing is on ticket id, since the same ticket exists in both
    tracks.
    """
    m = ref.merge(track, on="id", suffixes=("_a", "_b"))
    classes = sorted(set(m["y_true_a"]) | set(m["y_pred_a"])
                     | set(m["y_true_b"]) | set(m["y_pred_b"]))
    lut = {c: i for i, c in enumerate(classes)}
    k = len(classes)
    ia = np.array([lut[v] for v in m["y_true_a"]]) * k + np.array([lut[v] for v in m["y_pred_a"]])
    ib = np.array([lut[v] for v in m["y_true_b"]]) * k + np.array([lut[v] for v in m["y_pred_b"]])
    pos = lut.get(config.SENTIMENT_POSITIVE_CLASS) if task == "sentiment" else None

    obs = (metrics.score(m["y_true_b"], m["y_pred_b"], task)["headline"]
           - metrics.score(m["y_true_a"], m["y_pred_a"], task)["headline"])

    rng = np.random.default_rng(seed)
    n = len(m)
    deltas = np.empty(RESAMPLES)
    for i in range(RESAMPLES):
        idx = rng.integers(0, n, size=n)
        cb = np.bincount(ib[idx], minlength=k * k).reshape(k, k)
        ca = np.bincount(ia[idx], minlength=k * k).reshape(k, k)
        deltas[i] = (_headline_from_counts(cb, task, pos)
                     - _headline_from_counts(ca, task, pos))
    p = 2 * (np.mean(deltas >= 0) if obs < 0 else np.mean(deltas <= 0))
    return {"delta_ci_low": round(float(np.percentile(deltas, 2.5)), 4),
            "delta_ci_high": round(float(np.percentile(deltas, 97.5)), 4),
            "p_bootstrap": round(float(min(p, 1.0)), 4)}


def main() -> None:
    rows = []
    for path in sorted(PRED_DIR.glob("*__ev-all__*__test.csv")):
        task, model = path.name.split("__")[0], path.name.split("__")[1]
        if task not in TASKS:
            continue
        pred = pd.read_csv(path)
        if "language" not in pred.columns:
            continue

        ref = pred[pred["language"] == REFERENCE][["id", "y_true", "y_pred"]]
        if ref.empty:
            continue
        ref_headline = metrics.score(ref["y_true"], ref["y_pred"], task)["headline"]
        ref_err = float((ref["y_true"] != ref["y_pred"]).mean())

        for lang in config.LANGUAGES:
            if lang == REFERENCE:
                continue
            sub = pred[pred["language"] == lang][["id", "y_true", "y_pred"]]
            if sub.empty:
                continue
            headline = metrics.score(sub["y_true"], sub["y_pred"], task)["headline"]
            err = float((sub["y_true"] != sub["y_pred"]).mean())
            r = {"task": task, "model": model, "track": lang,
                 "headline": round(headline, 4),
                 "headline_english": round(ref_headline, 4),
                 "delta_headline": round(headline - ref_headline, 4),
                 "error_rate": round(err, 4),
                 "error_rate_english": round(ref_err, 4),
                 "delta_error_pp": round(100 * (err - ref_err), 2)}
            r.update(paired_mcnemar(ref, sub))
            r.update(paired_bootstrap_headline(ref, sub, task))
            # The headline metric's own test decides significance. McNemar is kept
            # alongside because where the two disagree, that disagreement is itself
            # the finding.
            r["significant_05"] = bool(r["p_bootstrap"] < 0.05)
            r["tests_agree"] = bool((r["p_bootstrap"] < 0.05) == (r["p_mcnemar"] < 0.05))
            rows.append(r)

    if not rows:
        print("no per-language predictions found -- run save_test_predictions.py first")
        return

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "language_gap.csv", index=False)

    for task in TASKS:
        sub = df[df["task"] == task]
        if sub.empty:
            continue
        print(f"\n{task} -- paired against english, same {sub['n_paired'].iloc[0]} tickets")
        print(sub[["model", "track", "delta_headline", "delta_ci_low", "delta_ci_high",
                   "p_bootstrap", "p_mcnemar", "significant_05", "tests_agree"]]
              .to_string(index=False))

    n_sig = int(df["significant_05"].sum())
    n_dis = int((~df["tests_agree"]).sum())
    print(f"\n{n_sig} of {len(df)} track-vs-english comparisons significant at 0.05 "
          f"on the headline metric")
    if n_dis:
        print(f"{n_dis} comparison(s) where McNemar (accuracy) and the headline test "
              f"disagree -- accuracy-based testing would misreport these")
    print(f"written to {(OUT / 'language_gap.csv').relative_to(REPO)}")


if __name__ == "__main__":
    main()
