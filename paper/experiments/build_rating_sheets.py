"""Blind rating sheets for the translation comparison, and the scorer for them.

Design constraints that make this evidence rather than decoration
----------------------------------------------------------------
**Blind.** Raters never see which system produced a candidate. Systems are
shuffled independently per item, so a rater cannot learn "column B is always
ours" halfway through and start rewarding it.

**Our translation is a candidate, not the reference.** Scoring the other systems
against Swift's text with BLEU or chrF would measure similarity to us and
guarantee we win. There is no reference column anywhere in this file.

**Adequacy and fluency are separate judgements.** A translation can be perfectly
natural Sinhala that says the wrong thing, or a clumsy rendering that preserves
the meaning exactly. Collapsing them into one "quality" score loses the
distinction that matters for a support-ticket corpus.

**Ranking as well as rating.** Likert scores compress -- raters cluster on 3 and
4. A forced ranking over the four candidates recovers the ordering that ratings
alone blur, and is what the headline claim should rest on.

Two modes:
    build   one sheet per rater, systems shuffled, key held back
    score   read returned sheets, produce per-system means and win rates

Run:
    .venv312/bin/python paper/experiments/build_rating_sheets.py build
    .venv312/bin/python paper/experiments/build_rating_sheets.py score
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

TE = REPO / "paper" / "translation_eval"
SAMPLES, SYSTEMS, RATINGS = TE / "samples", TE / "systems", TE / "ratings"
OUT = REPO / "paper" / "results" / "tables"

LANGS = ["sinhala", "tamil"]
EXTERNAL = ["google", "openai", "gptoss"]
RATERS = ["r1", "r2"]


def collect(lang: str) -> pd.DataFrame | None:
    """Swift's translation plus whichever external systems have landed."""
    sample = pd.read_csv(SAMPLES / "sample_ids.csv")
    out = sample[["id", "text_en"]].copy()
    out["swift"] = sample[f"swift_{lang}"]

    found = ["swift"]
    for sysname in EXTERNAL:
        path = SYSTEMS / f"{sysname}_{lang}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "id" not in df.columns or "translation" not in df.columns:
            print(f"  {path.name}: expected columns id,translation -- skipped")
            continue
        merged = out.merge(df[["id", "translation"]].rename(
            columns={"translation": sysname}), on="id", how="left")
        missing = int(merged[sysname].isna().sum())
        if missing:
            print(f"  {path.name}: {missing} of {len(out)} ids missing "
                  f"-- rows dropped by the system, investigate before using")
        out = merged
        found.append(sysname)

    print(f"{lang}: {len(found)} system(s) -> {', '.join(found)}")
    return out if len(found) >= 2 else None


def build(seed: int) -> None:
    RATINGS.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    any_built = False

    for lang in LANGS:
        table = collect(lang)
        if table is None:
            print(f"  {lang}: need at least 2 systems, skipped\n")
            continue

        systems = [c for c in table.columns if c not in ("id", "text_en")]
        rows, key = [], []
        for r in table.itertuples(index=False):
            order = list(rng.permutation(systems))
            item = {"id": r.id, "source_en": r.text_en}
            for slot, sysname in enumerate(order, 1):
                item[f"candidate_{slot}"] = getattr(r, sysname)
                item[f"adequacy_{slot}"] = ""
                item[f"fluency_{slot}"] = ""
                key.append({"id": r.id, "slot": slot, "system": sysname})
            item["ranking_best_to_worst"] = ""
            item["notes"] = ""
            rows.append(item)

        sheet = pd.DataFrame(rows)
        for rater in RATERS:
            sheet.to_csv(RATINGS / f"sheet_{lang}_{rater}.csv", index=False)
        pd.DataFrame(key).to_csv(RATINGS / f"key_{lang}.csv", index=False)
        any_built = True
        print(f"  {lang}: {len(sheet)} items x {len(systems)} candidates, "
              f"sheets for {', '.join(RATERS)}\n")

    if not any_built:
        print("Nothing built. Put the returned system files in "
              f"{SYSTEMS.relative_to(REPO)}/ first:")
        for lang in LANGS:
            for s in EXTERNAL:
                print(f"  {s}_{lang}.csv   (columns: id,translation)")
        return

    print(f"written to {RATINGS.relative_to(REPO)}/")
    print("Send only the sheet_*.csv files. key_*.csv unblinds them -- keep it back.")
    print("\nRating scale, to give raters verbatim:")
    print("  adequacy 1-5  1 = meaning lost   5 = meaning fully preserved")
    print("  fluency  1-5  1 = unnatural      5 = reads as a real customer wrote it")
    print("  ranking       best to worst by slot number, e.g. '3,1,4,2'")


def score() -> None:
    rows = []
    for lang in LANGS:
        key_path = RATINGS / f"key_{lang}.csv"
        if not key_path.exists():
            continue
        key = pd.read_csv(key_path)
        lookup = {(r.id, r.slot): r.system for r in key.itertuples(index=False)}

        for rater in RATERS:
            path = RATINGS / f"sheet_{lang}_{rater}.csv"
            if not path.exists():
                print(f"  missing {path.name}")
                continue
            sheet = pd.read_csv(path)
            slots = sorted(int(c.split("_")[1]) for c in sheet.columns
                           if c.startswith("candidate_"))
            for r in sheet.itertuples(index=False):
                d = r._asdict()
                ranking = [s.strip() for s in str(d.get("ranking_best_to_worst", "")).split(",")
                           if s.strip().isdigit()]
                for slot in slots:
                    sysname = lookup.get((d["id"], slot))
                    if sysname is None:
                        continue
                    rows.append({
                        "language": lang, "rater": rater, "id": d["id"], "system": sysname,
                        "adequacy": pd.to_numeric(d.get(f"adequacy_{slot}"), errors="coerce"),
                        "fluency": pd.to_numeric(d.get(f"fluency_{slot}"), errors="coerce"),
                        "rank": ranking.index(str(slot)) + 1 if str(slot) in ranking else np.nan,
                    })

    if not rows:
        print("No returned rating sheets found.")
        return

    long = pd.DataFrame(rows)
    summary = (long.groupby(["language", "system"])
               .agg(n=("id", "count"),
                    adequacy=("adequacy", "mean"), fluency=("fluency", "mean"),
                    mean_rank=("rank", "mean"),
                    won=("rank", lambda s: float((s == 1).mean())))
               .round(3).reset_index()
               .sort_values(["language", "mean_rank"]))

    OUT.mkdir(parents=True, exist_ok=True)
    long.to_csv(OUT / "translation_ratings_long.csv", index=False)
    summary.to_csv(OUT / "translation_ratings.csv", index=False)

    print(summary.to_string(index=False))

    # Rater agreement on the ordering, so the ranking is not one person's taste.
    for lang in LANGS:
        sub = long[long["language"] == lang]
        for x, y in itertools.combinations(sorted(sub["rater"].unique()), 2):
            a = sub[sub["rater"] == x].set_index(["id", "system"])["rank"]
            b = sub[sub["rater"] == y].set_index(["id", "system"])["rank"]
            common = a.dropna().index.intersection(b.dropna().index)
            if len(common) > 2:
                rho = a.loc[common].corr(b.loc[common], method="spearman")
                print(f"\n{lang}: rater {x} vs {y} rank correlation rho={rho:.3f} "
                      f"(n={len(common)})")

    print(f"\nwritten to {OUT.relative_to(REPO)}/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["build", "score"])
    ap.add_argument("--seed", type=int, default=config.RANDOM_STATE)
    args = ap.parse_args()
    build(args.seed) if args.mode == "build" else score()


if __name__ == "__main__":
    main()
