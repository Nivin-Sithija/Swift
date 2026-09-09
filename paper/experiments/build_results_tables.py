"""Generate the paper's results tables from the run records.

`results.md` opens by saying its figures were "generated directly from
`ml/reports/runs/*.json` -- no figure here was retyped by hand". There was no
script. This is that script, and from here the claim is true.

What it emits, into `paper/results/tables/`:

    main_pooled.{csv,md}        T4  -- 3 tasks x model, pooled test
    per_language.{csv,md}       T5  -- 3 tasks x model x 5 tracks, test
    balancing_arms.{csv,md}     T8  -- accuracy vs Negative-F1 by arm
    coverage.{csv,md}                -- what has and has not been run

Label-version safety
--------------------
Sentiment records written before the v8 relabel carry no `label_version` field.
An unstamped sentiment record is v5 and is **excluded** from every sentiment
table here rather than silently ranked against a v8 one -- that mixing is the
defect this whole pass exists to remove. Intent and priority were untouched by
the relabel, so their unstamped records are fine.

Run:
    .venv312/bin/python paper/experiments/build_results_tables.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, results, splits  # noqa: E402

OUT = REPO / "paper" / "results" / "tables"
TASKS = ["intent", "sentiment", "priority"]
HEADLINE_NAME = {"intent": "macro-F1", "sentiment": "Negative-F1", "priority": "macro-F1"}


# Negative counts the v8 labels produce, by (eval portion, pooled?). Read off the CSVs
# on disk, and the discriminator for records written before `label_version` existed:
# the v8 relabel moved pooled test from 505 Negatives to 975, so `n_negative_true`
# identifies which label set a record was scored against without any stamp.
V8_NEGATIVES = {("dev", True): 435, ("dev", False): 87,
                ("test", True): 975, ("test", False): 195}


def infer_label_version(row) -> str | None:
    """Resolve a record's label set, stamped or not.

    Six models were re-scored on v8 by Kaggle jobs that ran before the stamp
    existed. Treating "unstamped" as "v5" silently drops them -- including the
    sentiment champion -- so the count is used instead, and only genuinely
    ambiguous records fall back to unknown.
    """
    if row.get("label_version") in ("v5", "v8"):
        return row["label_version"]
    if row.get("task") != "sentiment":
        return row.get("label_version")
    expected = V8_NEGATIVES.get((row.get("eval_portion"), row.get("eval_lang") == "all"))
    n_neg = row.get("n_negative_true")
    if expected is None or pd.isna(n_neg):
        return None
    return "v8" if int(n_neg) == expected else "v5"


def load(portion: str) -> pd.DataFrame:
    df = results.load_all(portion)
    if df.empty:
        return df
    for col in ("label_version", "family", "fit_portion", "ci_lower", "ci_upper", "seed"):
        if col not in df.columns:
            df[col] = None
    df["label_version"] = df.apply(infer_label_version, axis=1)

    # Flag test records whose epoch was picked on the test set itself.
    #
    # `train_encoder`/`train_multitask` used to select the best epoch on `eval_df`,
    # which on a test run is the test set -- making the reported number a maximum
    # over `epochs` draws. Fixed 2026-09-08; records written before carry no
    # `epoch_selection` stamp. An unstamped *test* record is therefore suspect, and
    # a stamped `best-on-dev` test record definitely is.
    if "epoch_selection" not in df.columns:
        df["epoch_selection"] = None
    trained = df["epochs"].notna() if "epochs" in df.columns else False
    unstamped_test = ((df["eval_portion"] == "test") & trained
                      & (df["epoch_selection"] != "final-epoch"))

    # Selection can only inflate a score when it had something to choose. Where the
    # argmax epoch *is* the last epoch, "max over `epochs` draws" and "the final draw"
    # are the same draw and the bias is exactly zero -- confirmed empirically: the
    # labse sentiment test cell (best_epoch 3 of 3) re-ran under the patched code and
    # came back bit-identical to 17 significant figures. So the flag has to be
    # `best_epoch < epochs`, not merely "unstamped".
    if "best_epoch" in df.columns and "epochs" in df.columns:
        could_bias = df["best_epoch"].notna() & (df["best_epoch"] < df["epochs"])
    else:
        could_bias = True
    df["epoch_selection_ok"] = ~(unstamped_test & could_bias)
    df["epoch_selection_inert"] = unstamped_test & ~could_bias

    n_bad = int((~df["epoch_selection_ok"]).sum())
    n_inert = int(df["epoch_selection_inert"].sum())
    if n_inert:
        print(f"  {n_inert} unstamped test record(s) selected the FINAL epoch anyway "
              f"(best_epoch == epochs) -- selection had nothing to choose, bias is zero")
    if n_bad:
        print(f"  WARNING: {n_bad} test record(s) genuinely biased -- the argmax epoch "
              f"was earlier than the last, so the score is a max over draws")
    keep = (df["task"] != "sentiment") | (df["label_version"] == "v8")
    dropped = int((~keep).sum())
    if dropped:
        print(f"  excluded {dropped} sentiment record(s) resolved to v5")
    return df[keep].reset_index(drop=True)


def fmt(row) -> str:
    """Headline with its CI, when one was recorded."""
    val = f"{row['headline']:.4f}"
    if pd.notna(row.get("ci_lower")):
        val += f" [{row['ci_lower']:.4f}, {row['ci_upper']:.4f}]"
    return val


def main_pooled(test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for task in TASKS:
        sub = test[(test["task"] == task) & (test["eval_lang"] == "all")]
        if sub.empty:
            continue
        # Best arm per model: the arm is a training choice, not a separate system,
        # so the table reports each model at its best rather than once per arm.
        best = sub.sort_values("headline", ascending=False).groupby("model", as_index=False).first()
        for r in best.sort_values("headline", ascending=False).itertuples():
            rows.append({
                "task": task,
                "metric": HEADLINE_NAME[task],
                "model": r.model,
                "family": r.family or "",
                "arm": r.arm,
                "headline": round(r.headline, 4),
                "ci_lower": round(r.ci_lower, 4) if pd.notna(r.ci_lower) else None,
                "ci_upper": round(r.ci_upper, 4) if pd.notna(r.ci_upper) else None,
                "accuracy": round(r.accuracy, 4),
                "n": int(r.n),
                "n_train": int(r.n_train) if pd.notna(getattr(r, "n_train", None)) else None,
                "fit_portion": r.fit_portion or "",
                "label_version": r.label_version or "",
                # False = epoch chosen on the test set; do not cite without re-running.
                "epoch_selection_ok": bool(r.epoch_selection_ok),
            })
    return pd.DataFrame(rows)


def per_language(test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for task in TASKS:
        sub = test[test["task"] == task]
        if sub.empty:
            continue
        for model in sorted(sub["model"].unique()):
            m = sub[sub["model"] == model]
            # Pin to the arm that won pooled, so the row is one system across columns.
            pooled = m[m["eval_lang"] == "all"]
            if pooled.empty:
                continue
            arm = pooled.sort_values("headline", ascending=False).iloc[0]["arm"]
            m = m[m["arm"] == arm]
            row = {"task": task, "metric": HEADLINE_NAME[task], "model": model,
                   "family": m.iloc[0]["family"] or "", "arm": arm}
            for lang in config.LANGUAGES + ["all"]:
                cell = m[m["eval_lang"] == lang]
                row[lang] = round(float(cell.iloc[0]["headline"]), 4) if not cell.empty else None
            rows.append(row)
    return pd.DataFrame(rows)


def balancing_arms(test: pd.DataFrame) -> pd.DataFrame:
    """The accuracy-vs-Negative-F1 inversion, which needs both numbers side by side."""
    sub = test[(test["task"] == "sentiment") & (test["eval_lang"] == "all")]
    if sub.empty:
        return pd.DataFrame()
    return (
        sub[["model", "family", "arm", "accuracy", "headline", "negative_precision",
             "negative_recall", "n_negative_pred", "label_version"]]
        .rename(columns={"headline": "negative_f1"})
        .sort_values(["model", "arm"])
        .round(4)
        .reset_index(drop=True)
    )


def coverage(dev: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    """Which (task, model) cells exist, so blanks read as unrun rather than zero."""
    rows = []
    models = sorted(set(dev["model"]) | set(test["model"]))
    for task in TASKS:
        for model in models:
            t = test[(test["task"] == task) & (test["model"] == model)]
            d = dev[(dev["task"] == task) & (dev["model"] == model)]
            rows.append({
                "task": task, "model": model,
                "family": (t["family"].iloc[0] if not t.empty else
                           d["family"].iloc[0] if not d.empty else ""),
                "dev_pooled": int(not d[d["eval_lang"] == "all"].empty),
                "test_pooled": int(not t[t["eval_lang"] == "all"].empty),
                "test_per_language": int(t[t["eval_lang"] != "all"]["eval_lang"].nunique()),
                "has_ci": int(t["ci_lower"].notna().any()),
                "seeds": int(t["seed"].nunique()) if not t.empty else 0,
            })
    return pd.DataFrame(rows)


def to_markdown(df: pd.DataFrame) -> str:
    """Minimal markdown table.

    Hand-rolled rather than `df.to_markdown()`, which needs `tabulate` -- one more
    dependency between a fresh checkout and the paper's tables is not worth it.
    Numeric columns are right-aligned so the digits line up when read as text.
    """
    cols = list(df.columns)
    numeric = {c for c in cols if pd.api.types.is_numeric_dtype(df[c])}
    cells = [[("" if pd.isna(v) else str(v)) for v in row] for row in df.to_numpy()]
    width = {c: max(len(c), *(len(r[i]) for r in cells)) if cells else len(c)
             for i, c in enumerate(cols)}

    def line(vals):
        return "| " + " | ".join(
            v.rjust(width[c]) if c in numeric else v.ljust(width[c])
            for c, v in zip(cols, vals)
        ) + " |"

    rule = "|" + "|".join(
        ("-" * (width[c] + 1) + ":") if c in numeric else (":" + "-" * (width[c] + 1))
        for c in cols
    ) + "|"
    return "\n".join([line(cols), rule, *(line(r) for r in cells)])


def write(name: str, df: pd.DataFrame, note: str) -> None:
    if df.empty:
        print(f"  {name}: empty, skipped")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / f"{name}.csv", index=False)
    header = (f"<!-- generated by paper/experiments/build_results_tables.py · "
              f"split {splits.sha()} · {note} -->\n\n")
    (OUT / f"{name}.md").write_text(header + to_markdown(df) + "\n")
    print(f"  {name}: {len(df)} rows")


def main() -> None:
    print(f"split {splits.sha()}")
    dev, test = load("dev"), load("test")
    print(f"loaded {len(dev)} dev / {len(test)} test records\n")

    write("main_pooled", main_pooled(test), "pooled test, best arm per model")
    write("per_language", per_language(test), "test, arm pinned to the pooled winner")
    write("balancing_arms", balancing_arms(test), "sentiment, v8 labels only")
    write("coverage", coverage(dev, test), "0 = not run")

    print(f"\nwritten to {OUT.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
