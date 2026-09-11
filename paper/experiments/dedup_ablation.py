"""Does the result survive removing test rows whose text also appears in training?

The splits are drawn on ticket `id`, which is the right defence and keeps them
clean at ticket level. But BANKING77 contains near-duplicate customer phrasings
under different ids, so some *text* still recurs across the boundary:

    english 6 (0.19%) · sinhala 71 (2.31%) · singlish 84 (2.73%)
    tamil 70 (2.31%)  · tamilish 7 (0.23%)

Those are documented and never ablated. The asymmetry is the reason to bother:
overlap is ~12x higher in the Sinhala and Tamil tracks than in English, because
translation collapses distinct English phrasings onto one target string. If that
inflated anything it would inflate exactly the tracks the paper's cross-lingual
claims rest on.

This recomputes every headline metric with the overlapping test rows dropped and
reports the delta. Small deltas make the footnote a strength; large ones would
mean the per-language table needs rebuilding on a deduplicated test set.

Run:
    .venv312/bin/python paper/experiments/dedup_ablation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, metrics, results, splits  # noqa: E402

OUT = REPO / "paper" / "results" / "tables"
PRED_DIR = config.PREDICTIONS_DIR / "runs"
TASKS = ["intent", "sentiment", "priority"]


def normalise(s: pd.Series) -> pd.Series:
    """Whitespace- and case-normalised text, so trivial formatting differences do
    not hide a genuine duplicate."""
    return s.astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)


def overlapping_ids() -> tuple[dict[str, set], pd.DataFrame]:
    """Per language, the test ids whose normalised text also occurs in train+dev."""
    train = pd.concat([splits.get(config.LANGUAGES, "train"),
                       splits.get(config.LANGUAGES, "dev")], ignore_index=True)
    test = splits.get(config.LANGUAGES, "test")
    train["_n"] = normalise(train["text"])
    test["_n"] = normalise(test["text"])

    per_lang, rows = {}, []
    for lang in config.LANGUAGES:
        seen = set(train.loc[train["language"] == lang, "_n"])
        t = test[test["language"] == lang]
        hit = t[t["_n"].isin(seen)]
        per_lang[lang] = set(hit["id"])
        rows.append({"language": lang, "test_rows": len(t),
                     "overlapping_rows": len(hit),
                     "pct": round(100 * len(hit) / len(t), 2)})
    return per_lang, pd.DataFrame(rows)


def main() -> None:
    per_lang, summary = overlapping_ids()
    print(f"split {splits.sha()}\n")
    print(summary.to_string(index=False))

    rows = []
    for path in sorted(PRED_DIR.glob("*__ev-all__*__test.csv")):
        task, model = path.name.split("__")[0], path.name.split("__")[1]
        if task not in TASKS:
            continue
        pred = pd.read_csv(path)

        drop = pred.apply(lambda r: r["id"] in per_lang.get(r["language"], ()), axis=1)
        kept = pred[~drop]

        full = metrics.score(pred["y_true"], pred["y_pred"], task)["headline"]
        deduped = metrics.score(kept["y_true"], kept["y_pred"], task)["headline"]
        rows.append({
            "task": task, "model": model,
            "headline_full": round(full, 4),
            "headline_deduped": round(deduped, 4),
            "delta": round(deduped - full, 4),
            "rows_full": len(pred), "rows_deduped": len(kept),
            "rows_dropped": int(drop.sum()),
        })

    if not rows:
        print("\nno prediction files -- run save_test_predictions.py first")
        return

    df = pd.DataFrame(rows).sort_values(["task", "model"]).reset_index(drop=True)
    OUT.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT / "dedup_overlap.csv", index=False)
    df.to_csv(OUT / "dedup_ablation.csv", index=False)

    print("\n" + df.to_string(index=False))
    worst = df.loc[df["delta"].abs().idxmax()]
    print(f"\nlargest shift: {worst['task']}/{worst['model']} {worst['delta']:+.4f}")
    print(f"written to {OUT.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
