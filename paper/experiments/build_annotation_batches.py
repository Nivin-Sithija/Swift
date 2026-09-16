"""Draw the inter-annotator agreement batch, and score it when it comes back.

The problem being fixed
-----------------------
`ml/reports/500_benchmarkset.csv` has an `annotator` column holding the value `1`
for all 500 rows. There is one annotator, so the "label ceiling" of 0.7812 is
agreement with one person, and no human-human agreement figure exists anywhere in
the project. That makes the paper's most interesting claim -- that label quality
binds the task, not model capacity -- unfalsifiable.

Sampling
--------
Stratified on **sentiment**, not proportional. The gold 500 holds 31 Negatives
against 469 Neutrals, so a proportional 200-row draw would contain ~12 Negatives
and the agreement figure for the minority class -- the only class anyone cares
about -- would rest on a dozen rows. This oversamples Negative deliberately and
records the sampling weights so the numbers can be reported honestly as
class-conditional agreement.

Two modes:
    build   draw the batch, write one blank file per annotator
    score   read the returned files, compute Cohen's kappa and Krippendorff's alpha

Run:
    .venv312/bin/python paper/experiments/build_annotation_batches.py build
    .venv312/bin/python paper/experiments/build_annotation_batches.py score
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

from swiftbench import config  # noqa: E402

GOLD = REPO / "ml" / "reports" / "500_benchmarkset.csv"
BATCHES = REPO / "paper" / "annotation" / "batches"
RETURNED = REPO / "paper" / "annotation" / "returned"
OUT = REPO / "paper" / "results" / "tables"

N_ROWS = 200
N_NEGATIVE = 60          # of 31 available -- take all, then fill from Neutral
ANNOTATORS = ["a2", "a3"]


def build(seed: int) -> None:
    gold = pd.read_csv(GOLD)
    rng = np.random.default_rng(seed)

    neg = gold[gold["sentiment"] == "Negative"]
    neu = gold[gold["sentiment"] != "Negative"]
    take_neg = min(len(neg), N_NEGATIVE)
    # Stratify the Neutral remainder on priority so all three priority classes
    # are represented -- High is 12% of the gold set and would otherwise thin out.
    neu_take = N_ROWS - take_neg
    per_pri = neu.groupby("priority", group_keys=False)
    picks = [g.sample(min(len(g), max(1, neu_take // neu["priority"].nunique())),
                      random_state=seed).index for _, g in per_pri]
    chosen_neu = neu.loc[[i for idx in picks for i in idx]]
    if len(chosen_neu) < neu_take:
        rest = neu[~neu.index.isin(chosen_neu.index)]
        chosen_neu = pd.concat(
            [chosen_neu, rest.sample(neu_take - len(chosen_neu), random_state=seed)])

    batch = pd.concat([neg.sample(take_neg, random_state=seed), chosen_neu])
    batch = batch.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    BATCHES.mkdir(parents=True, exist_ok=True)
    # The reference labels stay here and are NOT shipped to annotators.
    batch[["id", "row_id", "text", "sentiment", "priority"]].rename(
        columns={"sentiment": "sentiment_a1", "priority": "priority_a1"}
    ).to_csv(BATCHES / "batch_reference.csv", index=False)

    blank = batch[["id", "text"]].copy()
    blank["sentiment"] = ""
    blank["priority"] = ""
    blank["notes"] = ""
    for who in ANNOTATORS:
        blank.to_csv(BATCHES / f"batch_{who}.csv", index=False)

    print(f"batch: {len(batch)} rows "
          f"({take_neg} Negative, {len(batch) - take_neg} Neutral), seed {seed}")
    print(f"priority mix: {batch['priority'].value_counts().to_dict()}")
    print(f"\nwritten to {BATCHES.relative_to(REPO)}/")
    for p in sorted(BATCHES.iterdir()):
        print(f"  {p.name}")
    print("\nSend batch_a2.csv and batch_a3.csv with "
          "paper/annotation/guidelines/annotation_guideline_v1.md.")
    print("Do NOT send batch_reference.csv -- it contains the existing labels.")


def cohen_kappa(a: pd.Series, b: pd.Series) -> float:
    labels = sorted(set(a) | set(b))
    n = len(a)
    observed = float((a.to_numpy() == b.to_numpy()).mean())
    expected = sum((a == l).mean() * (b == l).mean() for l in labels)
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def krippendorff_alpha(matrix: list[pd.Series]) -> float:
    """Nominal alpha for a fully-crossed design (every rater labels every item).

    Computed directly rather than pulled from a package: the fully-crossed
    nominal case is a dozen lines, and it avoids a dependency the rest of the
    pipeline does not need.
    """
    df = pd.concat(matrix, axis=1).dropna()
    if df.empty:
        return float("nan")
    m = df.shape[1]
    labels = sorted(set(df.to_numpy().ravel()))

    # Observed disagreement: per item, the share of rater pairs that differ.
    do = 0.0
    for _, row in df.iterrows():
        vals = row.to_numpy()
        pairs = list(itertools.combinations(range(m), 2))
        do += sum(vals[i] != vals[j] for i, j in pairs) / len(pairs)
    do /= len(df)

    # Expected disagreement: probability two labels drawn from the pooled
    # marginal distribution differ.
    flat = pd.Series(df.to_numpy().ravel())
    p = flat.value_counts(normalize=True)
    de = 1 - sum(p.get(l, 0.0) ** 2 for l in labels)
    return 1 - do / de if de else float("nan")


def score() -> None:
    ref_path = BATCHES / "batch_reference.csv"
    if not ref_path.exists():
        sys.exit("no batch_reference.csv -- run `build` first")
    ref = pd.read_csv(ref_path)

    returned = {}
    for who in ANNOTATORS:
        p = RETURNED / f"batch_{who}.csv"
        if p.exists():
            returned[who] = pd.read_csv(p)
        else:
            print(f"  missing: {p.relative_to(REPO)}")
    if not returned:
        sys.exit("\nNo returned files yet. Nothing to score.")

    rows = []
    for task, ref_col in (("sentiment", "sentiment_a1"), ("priority", "priority_a1")):
        series = {"a1": ref.set_index("id")[ref_col]}
        for who, df in returned.items():
            s = df.set_index("id")[task]
            series[who] = s[s.astype(str).str.upper() != "SKIP"]

        common = set.intersection(*(set(s.dropna().index) for s in series.values()))
        aligned = {k: v.loc[sorted(common)] for k, v in series.items()}

        for x, y in itertools.combinations(sorted(aligned), 2):
            rows.append({"task": task, "pair": f"{x}-{y}", "n": len(common),
                         "agreement": round(float((aligned[x].to_numpy()
                                                   == aligned[y].to_numpy()).mean()), 4),
                         "cohen_kappa": round(cohen_kappa(aligned[x], aligned[y]), 4)})
        rows.append({"task": task, "pair": f"alpha (all {len(aligned)})", "n": len(common),
                     "agreement": None,
                     "cohen_kappa": round(krippendorff_alpha(list(aligned.values())), 4)})

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "annotator_agreement.csv", index=False)
    print(df.to_string(index=False))
    print(f"\nwritten to {(OUT / 'annotator_agreement.csv').relative_to(REPO)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "score"])
    ap.add_argument("--seed", type=int, default=config.RANDOM_STATE)
    args = ap.parse_args()
    build(args.seed) if args.mode == "build" else score()


if __name__ == "__main__":
    main()
