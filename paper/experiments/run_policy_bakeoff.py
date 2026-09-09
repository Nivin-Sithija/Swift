"""Run the literature bake-off: 5 label models x 6 published policies.

Fitting discipline, unchanged from the rest of the project: everything that is estimated
is estimated on train+dev gold or on dev posteriors from a train-only fit, and applied
unchanged to test. Test is scored once.

    python paper/experiments/run_policy_bakeoff.py --seeds 40
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import policy_bakeoff as pb   # noqa: E402

OUT = pb.OUT
RHOS = (0.85, 1.05)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--beta", type=float, default=2.0)
    ap.add_argument("--sample-rows", type=int, default=400)
    args = ap.parse_args()

    print("building frames (dev = tf-idf train-only fit; test = labse)")
    dev = pb.build_frame("tfidf-logreg", "tfidf-logreg", "tfidf-logreg", "dev")
    test = pb.build_frame("labse", "labse", "labse", "test")
    print(f"  dev {len(dev)}   test {len(test)}")

    fitted = pb.fit_label_models(dev)
    print(f"  P(prio|intent) over {fitted['p_prio_given_intent'].shape[0]} intents")

    # ---- the posteriors each label model produces on test --------------------
    posteriors = {name: pb.label_model(name, test, fitted) for name in pb.LABEL_MODELS}

    # ---- how well does each label model estimate priority at all? ------------
    # A scheduling index is only as good as the distribution it consumes, so the
    # label models are scored as probability estimates BEFORE any queue is simulated.
    from sklearn.metrics import log_loss, f1_score
    y = test["gold_priority"].to_numpy()
    quality = []
    for name, P in posteriors.items():
        pred = np.array(pb.PRIORITY_CLASSES)[P.argmax(axis=1)]
        quality.append({
            "label_model": name,
            "log_loss": log_loss(y, P, labels=pb.PRIORITY_CLASSES),
            "macro_f1": f1_score(y, pred, average="macro"),
            # Argon & Ziya section 7: among signals, higher variability is better.
            # This is the quantity that result is about, so it is reported directly.
            "score_sd": float((P @ pb.C).std()),
            "score_iqr": float(np.subtract(*np.percentile(P @ pb.C, [75, 25]))),
        })
    quality = pd.DataFrame(quality).sort_values("log_loss")
    _save(quality, "bakeoff_label_models.csv",
          "Label models as probability estimators on test, before any queue is run. "
          "score_sd/iqr report signal variability, which Argon & Ziya (2009) sec 7 "
          "show is the property that lowers long-run cost.")
    print("\n=== label models as estimators ===")
    print(quality.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    # ---- the queue bake-off --------------------------------------------------
    rows = []
    combos = [(lm, po) for lm in pb.LABEL_MODELS for po in pb.POLICIES]
    # fcfs ignores the posterior entirely, so run it once rather than five times.
    combos = [(lm, po) for lm, po in combos if po != "fcfs" or lm == "marginal"]
    print(f"\nsimulating {len(combos)} combinations x {len(RHOS)} loads "
          f"x {args.seeds} seeds")

    for rho in RHOS:
        cfg = pb.SimConfig(rho=rho, beta=args.beta)
        for lm, po in combos:
            P = posteriors[lm]
            reps = [pb.summarise(pb.simulate(test, P, po, cfg, seed))
                    for seed in range(args.seeds)]
            r = pd.DataFrame(reps).mean().to_dict()
            r.update({"label_model": "-" if po == "fcfs" else lm,
                      "policy": po, "rho": rho})
            rows.append(r)
        print(f"  rho={rho} done")

    res = pd.DataFrame(rows)
    front = ["policy", "label_model", "rho", "rel_tardiness", "wait_High", "p95_High",
             "worst_High", "lang_spread_High", "breach_rate", "wait_Low", "mean_wait"]
    res = res[front + [c for c in res.columns if c not in front]]
    _save(res, "bakeoff_policies.csv",
          f"5 label models x 6 published ordering policies, {args.seeds} seeds, "
          f"beta={args.beta}. Scored against gold priority. Lower is better throughout.")

    print("\n=== queue bake-off, rho = 1.05, ranked by relative tardiness ===")
    hot = res[res.rho == 1.05].sort_values("rel_tardiness")
    print(hot[["policy", "label_model", "rel_tardiness", "wait_High", "p95_High",
               "worst_High", "lang_spread_High", "wait_Low"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    # ---- the sample set ------------------------------------------------------
    # A hand-inspectable slice: for a fixed set of tickets, what each label model
    # believes and where each policy would place the ticket in the queue at t=0.
    rng = np.random.default_rng(42)
    idx = rng.choice(len(test), size=args.sample_rows, replace=False)
    sam = test.iloc[idx][["id", "language", "gold_priority", "pred_priority",
                          "pred_intent", "p_negative"]].reset_index(drop=True)
    for lm, P in posteriors.items():
        Ps = P[idx]
        for j, k in enumerate(pb.PRIORITY_CLASSES):
            sam[f"{lm}__p{k}"] = Ps[:, j]
        sam[f"{lm}__cmu_index"] = Ps @ pb.C
        sam[f"{lm}__rank"] = (-(Ps @ pb.C)).argsort().argsort() + 1
    sam = sam.sort_values("marginal__rank")
    _save(sam, "bakeoff_sample_set.csv",
          f"{args.sample_rows} test tickets, seed 42. For each label model: the full "
          "priority posterior, the c-mu index it implies, and the rank that index "
          "gives the ticket at t=0. Sorted by the binary-relevance rank so that "
          "disagreements between models are adjacent and readable.")

    # Where do the models disagree most? That is what is worth eyeballing.
    dis = sam.assign(
        spread=sam[[f"{lm}__rank" for lm in pb.LABEL_MODELS]].max(axis=1)
             - sam[[f"{lm}__rank" for lm in pb.LABEL_MODELS]].min(axis=1))
    cols = ["id", "language", "gold_priority", "pred_intent", "p_negative", "spread"] + \
           [f"{lm}__rank" for lm in pb.LABEL_MODELS]
    _save(dis.sort_values("spread", ascending=False)[cols].head(60),
          "bakeoff_disagreements.csv",
          "The 60 sample tickets the label models rank most differently -- the rows "
          "that actually discriminate between the models.")
    print("\n=== 15 tickets the label models most disagree about ===")
    print(dis.sort_values("spread", ascending=False)[cols].head(15)
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    return 0


def _save(df: pd.DataFrame, name: str, note: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with path.open("w") as fh:
        fh.write(f"# {note}\n")
        df.to_csv(fh, index=False)
    print(f"  -> {path.relative_to(pb.REPO)}")


if __name__ == "__main__":
    raise SystemExit(main())
