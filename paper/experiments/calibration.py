"""Layer 4 -- calibration, per language.

Why this is load-bearing rather than hygiene
--------------------------------------------
Every F1 table in this project consumes the *argmax* of a posterior, where
calibration is irrelevant. The Ticket Urgency Score consumes the posterior itself:
`E[sev|t] = sum_k p_k sev_k`. An over-confident model pushes that expectation
towards 0 or 1 and throws away exactly the graded confidence the score exists to
exploit -- so a model can be more accurate and still order a queue worse.

That is not hypothetical here. The classifier-substitution control found the
TF-IDF-fed queue serving urgent tickets *sooner* than the LaBSE-fed one on every
track, and this script exists to establish whether calibration is why.

Two things get measured, both per language track:

  ECE   expected calibration error, 15 equal-width confidence bins
  ES    the mean of E[sev|t], which reveals over-confidence directly

Run:
    .venv312/bin/python paper/experiments/calibration.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO / "ml"))

import scoring  # noqa: E402
from swiftbench import metrics  # noqa: E402

TABLES = REPO / "paper" / "results" / "tables"
N_BINS = 15


def ece(conf: np.ndarray, correct: np.ndarray, n_bins: int = N_BINS) -> float:
    """Expected calibration error over equal-width confidence bins."""
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(total)


def rows_for(task: str, model: str) -> list[dict]:
    post = scoring.load_posteriors(task, model, "test")
    pcols = [c for c in post.columns if c.startswith("p_")]
    probs = post[pcols].to_numpy()
    conf = probs.max(1)
    correct = (post["y_pred"].to_numpy() == post["y_true"].to_numpy()).astype(float)
    out = []
    for lang in ["all"] + sorted(post["language"].unique()):
        m = np.ones(len(post), bool) if lang == "all" else (post["language"] == lang).to_numpy()
        row = {"task": task, "model": model, "language": lang, "n": int(m.sum()),
               "accuracy": float(correct[m].mean()),
               "mean_confidence": float(conf[m].mean()),
               "ece": ece(conf[m], correct[m]),
               # Positive => over-confident: the model claims more than it delivers.
               "overconfidence": float(conf[m].mean() - correct[m].mean())}
        row["macro_f1"] = metrics.score(post["y_true"].to_numpy()[m],
                                        post["y_pred"].to_numpy()[m], task)["macro_f1"]
        out.append(row)
    return out


def main() -> None:
    rows = []
    for task in ("priority", "sentiment"):
        for model in ("labse", "tfidf-logreg"):
            rows += rows_for(task, model)
    frame = pd.DataFrame(rows)
    TABLES.mkdir(parents=True, exist_ok=True)
    path = TABLES / "calibration.csv"
    with path.open("w") as fh:
        fh.write(f"# per-language calibration on test, {N_BINS} equal-width bins. "
                 f"split=e7b5934392cd label_version=v8 "
                 f"generated_by=calibration.py\n")
        frame.to_csv(fh, index=False)
    print(f"-> {path.relative_to(REPO)}")

    for task in ("priority", "sentiment"):
        sub = frame[frame["task"] == task]
        piv = sub.pivot(index="language", columns="model",
                        values=["macro_f1", "ece", "overconfidence"])
        print(f"\n=== {task} ===")
        print(piv.round(4).to_string())
        a = sub[(sub.model == "labse") & (sub.language == "all")].iloc[0]
        b = sub[(sub.model == "tfidf-logreg") & (sub.language == "all")].iloc[0]
        print(f"  pooled: LaBSE macro-F1 {a.macro_f1:.4f} ECE {a.ece:.4f}  |  "
              f"TF-IDF macro-F1 {b.macro_f1:.4f} ECE {b.ece:.4f}")
        if a.macro_f1 > b.macro_f1 and a.ece > b.ece:
            print("  -> LaBSE is the more accurate model and the worse calibrated one. "
                  "For an argmax metric that is invisible; for a score built on the "
                  "posterior it is not.")




# ---------------------------------------------------------------------------
# Temperature scaling -- does fixing the calibration fix the queue?
# ---------------------------------------------------------------------------
# The diagnosis above is a correlation: LaBSE is worse calibrated and its queue is
# slower. This tests the causal claim by scaling the temperature and re-running.
#
# HONESTY NOTE ON THE FIT. The proper place to fit T is dev, and it is not
# available: the saved LaBSE checkpoints were fit on train+dev, so their dev
# posteriors are memorised and would return T ~ 1. So T is **cross-fitted on test
# halves split by ticket id** -- T from half A scores half B and vice versa, so no
# ticket's own data ever sets its own temperature. That is standard for a single
# nuisance scalar, but it does touch test, and this project's discipline is that
# test is scored once. It is therefore reported as a labelled sensitivity analysis
# demonstrating a mechanism, **not** as a held-out result. The clean dev-fitted
# version needs a train-only LaBSE run with posteriors saved (tracker E6b).

def fit_temperature(logits_like: np.ndarray, y_idx: np.ndarray) -> float:
    """T minimising NLL. Grid then golden-section; the objective is 1-D and convex."""
    from scipy.optimize import minimize_scalar
    log_p = np.log(np.clip(logits_like, 1e-12, 1.0))

    def nll(log_t: float) -> float:
        scaled = log_p / np.exp(log_t)
        scaled -= scaled.max(1, keepdims=True)
        p = np.exp(scaled)
        p /= p.sum(1, keepdims=True)
        return float(-np.log(np.clip(p[np.arange(len(y_idx)), y_idx], 1e-12, 1)).mean())

    res = minimize_scalar(nll, bounds=(np.log(0.2), np.log(10.0)), method="bounded")
    return float(np.exp(res.x))


def apply_temperature(probs: np.ndarray, t: float) -> np.ndarray:
    scaled = np.log(np.clip(probs, 1e-12, 1.0)) / t
    scaled -= scaled.max(1, keepdims=True)
    p = np.exp(scaled)
    return p / p.sum(1, keepdims=True)


def temperature_study() -> None:
    import queue_sim
    from scoring import Weights

    print("\n=== temperature scaling (cross-fitted on test halves -- see note) ===")
    weights = pd.read_csv(TABLES / "tus_weights.csv", comment="#").iloc[0]
    w = Weights(float(weights.w_priority), float(weights.w_sentiment),
                float(weights.w_intent), float(weights.alpha))

    calibrated: dict[str, pd.DataFrame] = {}
    temps: dict[str, tuple[float, float]] = {}
    for task in ("priority", "sentiment"):
        post = scoring.load_posteriors(task, "labse", "test").copy()
        pcols = [c for c in post.columns if c.startswith("p_")]
        labels = [c[2:] for c in pcols]
        probs = post[pcols].to_numpy()
        y_idx = np.array([labels.index(v) for v in post["y_true"]])
        half = (post["id"].to_numpy() % 2 == 0)

        out = probs.copy()
        t_a = fit_temperature(probs[half], y_idx[half])
        t_b = fit_temperature(probs[~half], y_idx[~half])
        out[~half] = apply_temperature(probs[~half], t_a)
        out[half] = apply_temperature(probs[half], t_b)
        temps[task] = (t_a, t_b)

        conf, corr = out.max(1), (out.argmax(1) == y_idx).astype(float)
        print(f"  {task}: T = {t_a:.3f} / {t_b:.3f}   "
              f"ECE {ece(probs.max(1), corr):.4f} -> {ece(conf, corr):.4f}")
        post[pcols] = out
        calibrated[task] = post

    # Rebuild the signal frame from the calibrated posteriors and re-run the queue.
    frame = scoring.build_signal_frame("labse", "labse", "tfidf-logreg", "test")
    pri, sen = calibrated["priority"], calibrated["sentiment"]
    key = pd.MultiIndex.from_arrays([frame["id"], frame["language"]])
    frame = frame.copy()
    frame["sev_hat"] = (pri.set_index(["id", "language"])
                        .pipe(lambda d: sum(d[f"p_{k}"] * v
                                            for k, v in scoring.SEVERITY.items()))
                        .reindex(key).to_numpy())
    frame["p_negative"] = (sen.set_index(["id", "language"])["p_Negative"]
                           .reindex(key).to_numpy())

    base = scoring.build_signal_frame("labse", "labse", "tfidf-logreg", "test")
    rows = []
    for name, fr in (("LaBSE uncalibrated", base), ("LaBSE temperature-scaled", frame)):
        s, pl = queue_sim.run_grid(fr, (1.05,), range(200), w, policies=("tus",))
        lang = pl.groupby("language")["mean_wait"].mean()
        rows.append({"system": name, "high_mean_wait": s["high_mean_wait"].mean(),
                     "spread_across_tracks": float(lang.max() - lang.min()),
                     "tamilish_minus_english": float(lang["tamilish"] - lang["english"]),
                     **{f"wait_{k}": v for k, v in lang.items()}})
    res = pd.DataFrame(rows)
    path = TABLES / "calibration_queue_effect.csv"
    with path.open("w") as fh:
        fh.write("# SENSITIVITY ANALYSIS, not a held-out result: temperature "
                 "cross-fitted on test halves by ticket id parity, because the saved "
                 "LaBSE checkpoints were fit on train+dev and have no clean dev. "
                 f"rho=1.05, 200 seeds. temps={temps}. generated_by=calibration.py\n")
        res.to_csv(fh, index=False)
    print(f"-> {path.relative_to(REPO)}")
    print(res.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
    temperature_study()
