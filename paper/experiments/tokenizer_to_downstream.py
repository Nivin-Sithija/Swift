"""Does a tokenizer diagnostic predict downstream performance? For [UNK], yes.

The project measured two tokenizer properties per encoder per language --
fertility (tokens per word) and `[UNK]` rate -- and separately concluded that
"fertility does not predict encoder quality". That conclusion was drawn from a
screen, before any per-language downstream numbers existed.

Per-language downstream numbers now exist (the encoder path emits them as of
2026-09-08), so the two can finally be joined on the same models and the same
languages. The question splits in two, and the answers differ:

  - **Fertility** is a cost, not a failure. A model paying 3.6 tokens per word
    still sees every character.
  - **`[UNK]` rate** is destruction. Characters mapped to `[UNK]` are gone before
    the first layer, and no amount of fine-tuning recovers them.

Treating them as one "tokenizer quality" number is what produced the earlier
null result.

Run:
    .venv312/bin/python paper/experiments/tokenizer_to_downstream.py
    .venv312/bin/python paper/experiments/tokenizer_to_downstream.py --task intent
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config  # noqa: E402

OUT = REPO / "paper" / "results" / "tables"
FERTILITY = REPO / "ml" / "reports" / "encoder_tokenizer_fertility.csv"

# The fertility screen and the run records name the same checkpoints differently.
ALIAS = {"muril": "muril-base"}


def downstream(task: str, portion: str) -> pd.DataFrame:
    rows = []
    for f in glob.glob(str(REPO / "ml" / "reports" / "runs" / f"{task}__*__{portion}.json")):
        d = json.load(open(f))
        if d.get("family") not in ("encoder", "decoder"):
            continue
        if task == "sentiment" and d.get("label_version") != "v8":
            continue
        if d["eval_lang"] not in config.LANGUAGES:
            continue
        rows.append({"model": d["model"], "language": d["eval_lang"],
                     "headline": d["headline"], "epochs": d.get("epochs")})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="sentiment")
    ap.add_argument("--portion", default="dev")
    args = ap.parse_args()

    perf = downstream(args.task, args.portion)
    if perf.empty:
        sys.exit(f"no per-language {args.task}/{args.portion} encoder records yet")

    fert = pd.read_csv(FERTILITY)
    fert["model"] = fert["model"].replace(ALIAS)

    m = perf.merge(fert[["model", "language", "fertility", "unk_pct"]],
                   on=["model", "language"], how="inner")
    if m.empty:
        sys.exit("no overlap between the fertility screen and the run records")

    # Each model against its own English cell: the question is not "which model is
    # best" but "how much does this model lose on this script", which controls for
    # the model's general strength.
    eng = (m[m["language"] == "english"]
           .set_index("model")["headline"].rename("headline_english"))
    m = m.join(eng, on="model")
    m["delta_vs_english"] = (m["headline"] - m["headline_english"]).round(4)
    m["headline"] = m["headline"].round(4)

    non_eng = m[m["language"] != "english"].copy()
    non_eng["destroys_script"] = non_eng["unk_pct"] > 10

    print(f"{args.task} / {args.portion} -- per-language, joined to the tokenizer screen\n")
    print(non_eng[["model", "language", "fertility", "unk_pct",
                   "headline", "delta_vs_english"]]
          .sort_values(["language", "unk_pct"], ascending=[True, False])
          .to_string(index=False))

    # These two coefficients are the paper's mechanism claim, so they are written to
    # a table rather than only printed. A number that exists only in stdout gets
    # recomputed by hand later, and the method drifts: Spearman over the non-English
    # cells (what this reports) and Pearson over every row are different statistics
    # that disagree in both magnitude and, for fertility, sign. The stored row names
    # its own method and scope so the paper cannot quote it as something else.
    print("\ncorrelation with delta_vs_english across all model x non-English cells:")
    corr_rows = []
    for col in ("unk_pct", "fertility"):
        r = non_eng[col].corr(non_eng["delta_vs_english"], method="spearman")
        n_nonzero = int((non_eng[col] > 0.001).sum())
        note = ""
        if col == "unk_pct":
            note = (f"  <- only {n_nonzero}/{len(non_eng)} cells are non-zero; "
                    "this rho is carried by them, not by a range")
        print(f"  {col:10s} spearman rho = {r:+.3f}{note}")
        corr_rows.append({"predictor": col, "method": "spearman",
                          "scope": "non-english cells", "rho": round(float(r), 4),
                          "n_cells": int(len(non_eng)), "n_nonzero": n_nonzero})

    corr = pd.DataFrame(corr_rows)
    corr_path = OUT / f"tokenizer_correlations_{args.task}_{args.portion}.csv"
    OUT.mkdir(parents=True, exist_ok=True)
    with corr_path.open("w", encoding="utf-8") as fh:
        fh.write("# Spearman rank correlation between each tokenizer statistic and the\n"
                 "# per-language deficit vs english, over non-English cells only. Rank\n"
                 "# correlation because unk_pct is zero for most cells and the claim is\n"
                 "# monotone association, not linear fit. Do not requote as Pearson.\n")
        corr.to_csv(fh, index=False)
    print(f"\nwrote {corr_path.relative_to(REPO)}")

    hi = non_eng[non_eng["destroys_script"]]
    lo = non_eng[~non_eng["destroys_script"]]
    if len(hi) and len(lo):
        print(f"\ncells where the tokenizer drops >10% of characters to [UNK]: "
              f"mean delta {hi['delta_vs_english'].mean():+.4f}  (n={len(hi)})")
        print(f"cells where it does not:                                    "
              f"mean delta {lo['delta_vs_english'].mean():+.4f}  (n={len(lo)})")
        if len(hi) < 3:
            print(f"\n  CAUTION: only {len(hi)} high-[UNK] cell(s) in the roster, so this is a\n"
                  "  case study, not a fitted relationship. It is strong as a case study --\n"
                  f"  the worst cell in the table by {abs(hi['delta_vs_english'].min() - lo['delta_vs_english'].min()):.3f} --\n"
                  "  but establishing the relationship needs more high-[UNK] tokenizers.")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"tokenizer_to_downstream_{args.task}_{args.portion}.csv"
    non_eng.to_csv(path, index=False)
    print(f"\nwritten to {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
