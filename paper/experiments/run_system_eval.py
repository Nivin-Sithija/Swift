"""Evaluate the Ticket Urgency Score -- all five layers of SYSTEM_PLAN section 3.

    Layer 1  ranking quality        deterministic, no simulation
    Layer 2  queue simulation       5 policies x load sweep x seeds
    Layer 3  fairness by language   the headline
    Layer 5  ablation & frontier    does each signal earn its serving cost?

Layer 4 (calibration) is a separate script because it changes the posteriors
themselves rather than the way they are consumed.

Discipline: the weights are fitted on **dev** posteriors from a **train-only** fit,
and the fitted vector is applied unchanged to test. Nothing here tunes on test.

Run:
    .venv312/bin/python paper/experiments/run_system_eval.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import queue_sim  # noqa: E402
import scoring  # noqa: E402
from scoring import SLA_MINUTES, Weights  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TABLES = REPO / "paper" / "results" / "tables"

# Fitted across two loads, not one. The objective's *ordering* over the simplex is
# stable across loads, but at rho = 0.95 its magnitude is ~1e-3 and nearby cells sit
# within seed noise of each other. Averaging a contended load with an overloaded one
# picks weights that hold across the regime rather than at one operating point.
FIT_RHOS = (0.95, 1.05)
FIT_SEEDS = range(12)
ABLATION_RHO = 1.05
EVAL_RHOS = (0.85, 0.95, 1.05)
EVAL_SEEDS = range(200)
ALPHA_GRID = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)
SIMPLEX_STEP = 0.05


def save(frame: pd.DataFrame, name: str, note: str) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    path = TABLES / name
    with path.open("w") as fh:
        fh.write(f"# {note}\n")
        frame.to_csv(fh, index=False)
    print(f"  -> {path.relative_to(REPO)}  ({len(frame)} rows)")


# --------------------------------------------------------------------------
# Layer 1 -- ranking quality
# --------------------------------------------------------------------------

def ndcg_at_k(gain: np.ndarray, k: int) -> float:
    """Standard nDCG over a already-ordered gain vector."""
    g = gain[:k]
    disc = 1.0 / np.log2(np.arange(2, len(g) + 2))
    ideal = np.sort(gain)[::-1][:k]
    denom = float((ideal * disc[:len(ideal)]).sum())
    return float((g * disc).sum() / denom) if denom else 1.0


def ranking_metrics(frame: pd.DataFrame, score: np.ndarray, label: str) -> dict:
    from scipy.stats import kendalltau
    order = np.argsort(-score, kind="stable")
    gold = frame["gold_sev"].to_numpy()[order]
    is_high = (frame["gold_priority"].to_numpy()[order] == "High")
    row = {"system": label,
           "kendall_tau_b": float(kendalltau(score, frame["gold_sev"].to_numpy(),
                                             variant="b").statistic)}
    for k in (10, 50, 100):
        row[f"ndcg@{k}"] = ndcg_at_k(gold, k)
        row[f"P_high@{k}"] = float(is_high[:k].mean())
    row["base_rate_high"] = float((frame["gold_priority"] == "High").mean())
    return row


# --------------------------------------------------------------------------
# Layer 5 / E8 -- fit the weights on dev
# --------------------------------------------------------------------------

def fit_weights(dev: pd.DataFrame) -> tuple[Weights, pd.DataFrame]:
    """Grid search the 3-simplex x alpha, minimising mean *relative* tardiness on dev.

    Relative tardiness -- lateness measured in units of the class's own SLA window --
    is the objective because it is the only one of the queue metrics that charges for
    *both* failure modes, an urgent ticket left waiting and a low-priority ticket
    starved, without letting the class mix decide which one matters. Optimising High
    waiting time alone selects alpha = 0 every time and yields a system that never
    serves anything else; optimising *absolute* tardiness weighted by severity hands
    the objective to the 55% Low majority and selects a scorer that barely
    discriminates at all (see the note in queue_sim.summarise).
    """
    grid = scoring.simplex_grid(SIMPLEX_STEP)
    print(f"  fitting on dev: {len(grid)} simplex points x {len(ALPHA_GRID)} alphas "
          f"x {len(list(FIT_SEEDS))} seeds x rho in {FIT_RHOS}")
    rows = []
    started = time.time()
    for n, (wp, ws, wi) in enumerate(grid):
        for alpha in ALPHA_GRID:
            w = Weights(wp, ws, wi, alpha)
            vals = [queue_sim.summarise(
                        queue_sim.simulate(dev, "tus",
                                           queue_sim.SimConfig(rho=r, weights=w), s))
                    for r in FIT_RHOS for s in FIT_SEEDS]
            rows.append({"w_priority": wp, "w_sentiment": ws, "w_intent": wi,
                         "alpha": alpha,
                         "rel_tardiness": float(np.mean([v["rel_tardiness"]
                                                              for v in vals])),
                         "high_mean_wait": float(np.mean([v["high_mean_wait"]
                                                          for v in vals])),
                         "low_p95_wait": float(np.mean([v["low_p95_wait"]
                                                        for v in vals]))})
        if n % 40 == 0:
            print(f"    {n:>4}/{len(grid)}  {time.time() - started:5.0f}s", flush=True)
    surface = pd.DataFrame(rows)
    best = surface.loc[surface["rel_tardiness"].idxmin()]
    w = Weights(float(best["w_priority"]), float(best["w_sentiment"]),
                float(best["w_intent"]), float(best["alpha"]))
    print(f"  fitted: w_P={w.w_priority:.2f} w_S={w.w_sentiment:.2f} "
          f"w_I={w.w_intent:.2f} alpha={w.alpha}  "
          f"(dev mean relative tardiness {best['rel_tardiness']:.3f})")

    # How flat is the surface? If a wide region is within noise of the argmin, the
    # exact weights are not the finding and claiming them would be overclaiming.
    at_best_alpha = surface[surface["alpha"] == w.alpha]
    floor = at_best_alpha["rel_tardiness"].min()
    within = at_best_alpha[at_best_alpha["rel_tardiness"] <= floor * 1.05]
    print(f"  {len(within)}/{len(at_best_alpha)} simplex points within 5% of the "
          f"optimum -- w_P in [{within['w_priority'].min():.2f}, "
          f"{within['w_priority'].max():.2f}]")
    return w, surface


# --------------------------------------------------------------------------

def main() -> None:
    print(f"posteriors: {scoring.POSTERIORS.relative_to(REPO)}")
    dev = scoring.build_signal_frame("tfidf-logreg", "tfidf-logreg", "tfidf-logreg", "dev")
    test = scoring.build_signal_frame("labse", "labse", "tfidf-logreg", "test")
    test_tfidf = scoring.build_signal_frame("tfidf-logreg", "tfidf-logreg",
                                            "tfidf-logreg", "test")
    print(f"dev {len(dev)} rows   test {len(test)} rows\n")

    prov = (f"split=e7b5934392cd label_version=v8 "
            f"sla_high={SLA_MINUTES['High']} sla_med={SLA_MINUTES['Medium']} "
            f"sla_low={SLA_MINUTES['Low']} agents={queue_sim.N_AGENTS} "
            f"service_mean={queue_sim.SERVICE_MEAN_MIN}min "
            f"tickets_per_rep={queue_sim.TICKETS_PER_REPLICATION} "
            f"generated_by=run_system_eval.py")

    # ---- E8: fit on dev -------------------------------------------------
    print("[E8] weight fit (dev, tf-idf posteriors from a train-only fit)")
    w, surface = fit_weights(dev)
    save(surface, "tus_weight_surface.csv",
         f"dev weight-fit surface. fitted_on=dev fit_rhos={FIT_RHOS} {prov}")
    save(pd.DataFrame([w.as_dict()]), "tus_weights.csv",
         f"TUS weights fitted on dev, applied unchanged to test. {prov}")

    # ---- E3: Layer 1, ranking ------------------------------------------
    print("\n[E3] Layer 1 -- ranking quality on test")
    rank_rows = [
        ranking_metrics(test, scoring.content_score(test, w), "TUS (LaBSE)"),
        ranking_metrics(test_tfidf, scoring.content_score(test_tfidf, w), "TUS (TF-IDF)"),
        ranking_metrics(test, test["sev_hat"].to_numpy(), "priority posterior only"),
        ranking_metrics(test, test["pred_priority"].map(queue_sim.TIER_RANK).to_numpy(),
                        "predicted tier (argmax)"),
        ranking_metrics(test, test["p_negative"].to_numpy(), "sentiment only"),
        ranking_metrics(test, test["kappa"].to_numpy(), "intent criticality only"),
        ranking_metrics(test, scoring.oracle_content_score(test), "oracle (gold tier)"),
    ]
    ranking = pd.DataFrame(rank_rows)
    save(ranking, "tus_ranking.csv", f"Layer 1, test, ordered once. {prov}")
    print(ranking[["system", "kendall_tau_b", "ndcg@100", "P_high@100"]].to_string(index=False))

    # ---- E4: Layer 2, queue simulation ---------------------------------
    print(f"\n[E4] Layer 2 -- queue simulation, rho in {EVAL_RHOS}, "
          f"{len(list(EVAL_SEEDS))} seeds")
    started = time.time()
    summary, per_lang = queue_sim.run_grid(test, EVAL_RHOS, EVAL_SEEDS, w)
    print(f"  {len(summary)} replications in {time.time() - started:.0f}s")
    agg = (summary.groupby(["rho", "policy"])
           .agg(["mean", "std"]).round(3).reset_index())
    agg.columns = ["_".join(c).rstrip("_") for c in agg.columns]
    save(agg, "tus_queue_summary.csv", f"Layer 2, test. {prov}")
    save(summary, "tus_queue_replications.csv", f"Layer 2 raw replications. {prov}")

    att = pd.concat([queue_sim.attainment(summary, m)
                     for m in ("high_mean_wait", "high_p95_wait",
                               "rel_tardiness", "sla_breach_rate")],
                    ignore_index=True)
    save(att, "tus_attainment.csv",
         f"(fifo - tus) / (fifo - oracle), bootstrap CI over seeds. {prov}")
    print(att.round(3).to_string(index=False))

    # ---- E5: Layer 3, fairness -----------------------------------------
    print("\n[E5] Layer 3 -- waiting time by the language the customer wrote in")
    lang = (per_lang.groupby(["rho", "policy", "language"])["mean_wait"]
            .agg(["mean", "std", "count"]).reset_index()
            .rename(columns={"mean": "mean_wait_min"}))
    save(lang, "tus_wait_by_language.csv",
         f"Layer 3: mean wait for gold-High tickets, by track. "
         f"`oracle` is the gold-label control -- any gap there is the arrival "
         f"process, not the model. {prov}")
    for rho in EVAL_RHOS:
        piv = (lang[lang["rho"] == rho]
               .pivot(index="language", columns="policy", values="mean_wait_min"))
        print(f"\n  rho={rho}  mean wait (min) for gold-High tickets")
        print(piv.round(2).to_string())
        if {"tus", "oracle"} <= set(piv.columns):
            spread_t = piv["tus"].max() - piv["tus"].min()
            spread_o = piv["oracle"].max() - piv["oracle"].min()
            print(f"    spread across tracks: TUS {spread_t:.2f} min  "
                  f"vs gold-label control {spread_o:.2f} min")

    # ---- E5b: is the disparity real, and does TUS close it? ----------------
    # Reported as **fixed contrasts against english**, not as max-minus-min across
    # tracks. Max-minus-min is upward-biased by sampling noise -- it picks the extreme
    # of five noisy means -- and the proof is that FIFO, which never reads the ticket,
    # scores a "spread" of 16 minutes. A fixed contrast has no such bias, and FIFO's
    # contrasts are correctly indistinguishable from zero. The spread is kept as a
    # secondary column with that caveat attached, because it is the intuitive summary.
    print("\n[E5b] per-track contrasts against english, tested")
    rows = []
    rng = np.random.default_rng(0)
    for rho in EVAL_RHOS:
        wide = (per_lang[per_lang["rho"] == rho]
                .pivot_table(index=["policy", "seed"], columns="language",
                             values="mean_wait"))
        for policy in ("fifo", "tier", "tus", "oracle"):
            if policy not in wide.index.get_level_values(0):
                continue
            a = wide.loc[policy]
            arr = a.to_numpy()
            spread = arr.max(1) - arr.min(1)
            for track in [c for c in a.columns if c != "english"]:
                gap = (a[track] - a["english"]).to_numpy()
                boot = [gap[rng.integers(0, len(gap), len(gap))].mean()
                        for _ in range(2000)]
                lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
                rows.append({"rho": rho, "policy": policy, "track": track,
                             "minus_english": float(gap.mean()),
                             "ci_lo": lo, "ci_hi": hi,
                             "significant": not (lo <= 0 <= hi),
                             "spread_biased": float(spread.mean())})
        if {"tier", "tus"} <= set(wide.index.get_level_values(0)):
            t, u = wide.loc["tier"], wide.loc["tus"]
            for track in [c for c in t.columns if c != "english"]:
                d = ((t[track] - t["english"]) - (u[track] - u["english"])).to_numpy()
                boot = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
                lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
                rows.append({"rho": rho, "policy": "tier - tus (paired)", "track": track,
                             "minus_english": float(d.mean()), "ci_lo": lo, "ci_hi": hi,
                             "significant": not (lo <= 0 <= hi),
                             "spread_biased": np.nan})
    disparity = pd.DataFrame(rows)
    save(disparity, "tus_disparity.csv",
         f"Layer 3 tested: mean gold-High wait per track MINUS english, bootstrapped "
         f"over simulation seeds. `spread_biased` is max-minus-min across tracks and is "
         f"upward-biased by noise -- FIFO scores 16 min on it. Use the contrasts. {prov}")
    for rho in EVAL_RHOS:
        print(f"\n  rho={rho}")
        sub = disparity[(disparity.rho == rho) & (disparity.policy != "tier - tus (paired)")]
        print(sub[["policy", "track", "minus_english", "ci_lo", "ci_hi", "significant"]]
              .round(2).to_string(index=False))

    # ---- E7: Layer 5, ablation and frontier ----------------------------
    print("\n[E7] Layer 5 -- signal ablation and the alpha frontier")
    ablations = {
        "priority only":        Weights(1.0, 0.0, 0.0, w.alpha),
        "priority + sentiment": Weights(0.5, 0.5, 0.0, w.alpha),
        "priority + intent":    Weights(0.5, 0.0, 0.5, w.alpha),
        "full (fitted)":        w,
    }
    rows = []
    for name, wa in ablations.items():
        s, _ = queue_sim.run_grid(test, (ABLATION_RHO,), range(60), wa, policies=("tus",))
        m = s.mean(numeric_only=True)
        rows.append({"variant": name, **wa.as_dict(),
                     "high_mean_wait": m["high_mean_wait"],
                     "low_p95_wait": m["low_p95_wait"],
                     "rel_tardiness": m["rel_tardiness"],
                     "high_rel_tardiness": m["high_rel_tardiness"],
                     "low_rel_tardiness": m["low_rel_tardiness"],
                     "ranking_P_high@100": ranking_metrics(
                         test, scoring.content_score(test, wa), name)["P_high@100"]})
    ablation = pd.DataFrame(rows)
    save(ablation, "tus_ablation.csv", f"Layer 5 signal ablation, rho={ABLATION_RHO}. {prov}")
    print(ablation.round(3).to_string(index=False))

    rows = []
    for alpha in ALPHA_GRID:
        wa = Weights(w.w_priority, w.w_sentiment, w.w_intent, alpha)
        s, _ = queue_sim.run_grid(test, (ABLATION_RHO,), range(60), wa, policies=("tus",))
        m = s.mean(numeric_only=True)
        rows.append({"alpha": alpha, "high_p95_wait": m["high_p95_wait"],
                     "low_p95_wait": m["low_p95_wait"],
                     "high_mean_wait": m["high_mean_wait"],
                     "rel_tardiness": m["rel_tardiness"],
                     "high_rel_tardiness": m["high_rel_tardiness"],
                     "low_rel_tardiness": m["low_rel_tardiness"]})
    frontier = pd.DataFrame(rows)
    save(frontier, "tus_alpha_frontier.csv",
         f"Layer 5: the urgency/starvation frontier, rho={ABLATION_RHO}. {prov}")
    print(frontier.round(2).to_string(index=False))
    print("\ndone")


if __name__ == "__main__":
    main()
