#!/usr/bin/env python3
"""
Data-quality audit for the trilingual BANKING77 classifier bake-off.

Non-destructive: audits all five language/script folders (`english`, `sinhala`,
`singlish`, `tamil`, `tamilish`) x both splits (`train`, `test`) and reports
every issue that would affect training or evaluation. It NEVER mutates the
source CSVs — it prints a report and writes ROW-LEVEL review CSVs to
`cleaning_report/` so each flagged row can be inspected by hand.

The issue-collectors (`get_*`) return review-ready DataFrames and are imported
by `data_cleaning.ipynb` for interactive review — keep display logic out of them.

Checks / exports:
  1. Structural integrity   — row/id counts, id-alignment across languages.
  2. Label consistency      — labels identical across languages for the same id.
  3. Empty fields           — empty text or label.
  4. Untranslated rows      — non-English rows where `text` == `text_en`.
                              -> untranslated_rows.csv
  5. Within-split duplicates — exact dup rows vs. same text with CONFLICTING
                              labels (real noise). -> conflicting_label_duplicates.csv
  6. Train/test leakage     — same English source ticket in both splits.
                              -> train_test_leakage.csv
  7. Class balance          — per task distribution + rare-class flags.
  8. Text length            — length distribution + short/long outliers.

Usage:
    python data_cleaning.py                 # full audit, writes review CSVs
    python data_cleaning.py --no-write       # print only
"""
from __future__ import annotations

import argparse
import os
from collections import defaultdict

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATASETS = os.path.join(REPO, "datasets")
REPORT_DIR = os.path.join(HERE, "cleaning_report")

LANGS = ["english", "sinhala", "singlish", "tamil", "tamilish"]
SPLITS = ["train", "test"]
LABEL_COLS = ["category", "sentiment", "priority"]
EXPECTED_COLS = ["id", "text_en", "text", "category", "sentiment", "priority"]
RARE_THRESHOLD = 20  # category count below which the 77-way class is "rare"


# --------------------------------------------------------------------------- IO
def path(lang: str, split: str) -> str:
    return os.path.join(DATASETS, lang, f"{split}_labeled.csv")


def load() -> dict[tuple[str, str], pd.DataFrame]:
    """Load every existing (lang, split) CSV; skip missing ones (e.g. Tamil test)."""
    data: dict[tuple[str, str], pd.DataFrame] = {}
    for lang in LANGS:
        for split in SPLITS:
            p = path(lang, split)
            if os.path.exists(p):
                data[(lang, split)] = pd.read_csv(p, dtype=str, keep_default_na=False)
    return data


# ================================================================ issue collectors
# Each returns a review-ready, row-level DataFrame (empty if no issues).

def get_label_mismatches(data) -> pd.DataFrame:
    """Rows whose label differs from the canonical English label for that id."""
    out = []
    for split in SPLITS:
        if ("english", split) not in data:
            continue
        en = data[("english", split)].set_index("id")
        for lang in LANGS:
            if lang == "english" or (lang, split) not in data:
                continue
            other = data[(lang, split)].set_index("id").reindex(en.index)
            for col in LABEL_COLS:
                diff = en.index[en[col] != other[col]]
                for i in diff:
                    out.append({"split": split, "lang": lang, "id": i, "field": col,
                                "english": en.loc[i, col], "other": other.loc[i, col]})
    return pd.DataFrame(out)


def get_untranslated(data) -> pd.DataFrame:
    """Non-English rows where translated text equals the English source verbatim."""
    out = []
    for (lang, split), df in data.items():
        if lang == "english":
            continue
        m = df["text"].str.strip() == df["text_en"].str.strip()
        for _, r in df[m].iterrows():
            out.append({"lang": lang, "split": split, "id": r["id"],
                        "text_en": r["text_en"], "text": r["text"],
                        "category": r["category"], "sentiment": r["sentiment"],
                        "priority": r["priority"]})
    return pd.DataFrame(out)


def get_conflicting_duplicates(data) -> pd.DataFrame:
    """
    Row-level view of every collision where one `text` string carries >1 distinct
    (category, sentiment, priority) tuple within a split. All member rows of each
    collision are emitted together, tagged with a `group` id so they can be
    eyeballed side by side.
    """
    out = []
    for (lang, split), df in data.items():
        t = df["text"].str.strip()
        labels = df[LABEL_COLS].agg("|".join, axis=1)
        groups = defaultdict(set)
        for txt, lab in zip(t, labels):
            groups[txt].add(lab)
        conflicts = {txt for txt, labs in groups.items() if len(labs) > 1}
        gid = 0
        for txt in conflicts:
            members = df[t == txt]
            for _, r in members.iterrows():
                out.append({"lang": lang, "split": split, "group": gid, "id": r["id"],
                            "text": r["text"], "text_en": r["text_en"],
                            "category": r["category"], "sentiment": r["sentiment"],
                            "priority": r["priority"]})
            gid += 1
    return pd.DataFrame(out)


def get_exact_duplicates(data) -> pd.DataFrame:
    """Rows sharing BOTH text and full label tuple (safe-to-dedup redundancy)."""
    out = []
    for (lang, split), df in data.items():
        key = df["text"].str.strip() + "␟" + df[LABEL_COLS].agg("|".join, axis=1)
        dup_mask = key.duplicated(keep=False)
        codes = key[dup_mask].astype("category").cat.codes
        for (_, r), g in zip(df[dup_mask].iterrows(), codes):
            out.append({"lang": lang, "split": split, "group": int(g), "id": r["id"],
                        "text": r["text"], "category": r["category"],
                        "sentiment": r["sentiment"], "priority": r["priority"]})
    return pd.DataFrame(out)


def get_leakage(data) -> pd.DataFrame:
    """Test rows whose English source ticket (text_en) also appears in train."""
    if ("english", "train") not in data or ("english", "test") not in data:
        return pd.DataFrame()
    tr = data[("english", "train")]
    te = data[("english", "test")]
    tr_map = tr.assign(t=tr["text_en"].str.strip()).groupby("t")["id"].apply(list)
    te = te.assign(t=te["text_en"].str.strip())
    leaked = te[te["t"].isin(tr_map.index)]
    out = []
    for _, r in leaked.iterrows():
        out.append({"text_en": r["text_en"], "test_id": r["id"],
                    "test_sentiment": r["sentiment"], "test_priority": r["priority"],
                    "train_ids": ",".join(tr_map[r["t"]])})
    return pd.DataFrame(out)


# ============================================================= report + write
def header(title: str) -> None:
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def write_csv(df: pd.DataFrame, name: str, do_write: bool) -> None:
    if not do_write:
        return
    os.makedirs(REPORT_DIR, exist_ok=True)
    out = os.path.join(REPORT_DIR, name)
    df.to_csv(out, index=False)
    print(f"    -> {os.path.relpath(out, REPO)} ({len(df)} rows)")


def report(data, do_write: bool) -> None:
    missing = [(l, s) for l in LANGS for s in SPLITS if (l, s) not in data]
    if missing:
        print(f"NOTE: missing (skipped) splits: {missing}")

    header("1. STRUCTURAL INTEGRITY")
    rows = []
    for (lang, split), df in data.items():
        ids = df["id"].astype(int)
        rows.append({"lang": lang, "split": split, "rows": len(df),
                     "unique_ids": ids.nunique(), "id_min": ids.min(),
                     "id_max": ids.max(), "cols_ok": list(df.columns) == EXPECTED_COLS})
    print(pd.DataFrame(rows).to_string(index=False))
    print("\n  id-set alignment across languages (within split):")
    for split in SPLITS:
        present = [l for l in LANGS if (l, split) in data]
        if not present:
            continue
        ref = set(data[(present[0], split)]["id"])
        aligned = all(set(data[(l, split)]["id"]) == ref for l in present)
        print(f"    {split:5} langs={present} aligned={aligned} (n={len(ref)})")

    header("2. CROSS-LANGUAGE LABEL CONSISTENCY")
    lm = get_label_mismatches(data)
    print(f"  label mismatches vs english: {len(lm)}")
    write_csv(lm, "label_mismatches.csv", do_write and not lm.empty)

    header("3. EMPTY FIELDS")
    for (lang, split), df in data.items():
        et = (df["text"].str.strip() == "").sum()
        el = ((df["category"].str.strip() == "") | (df["sentiment"].str.strip() == "")
              | (df["priority"].str.strip() == "")).sum()
        if et or el:
            print(f"  {lang:9} {split:5} empty_text={et} empty_label={el}")
    print("  (none)" if all(
        (df["text"].str.strip() != "").all() for df in data.values()) else "")

    header("4. UNTRANSLATED ROWS (text == text_en)")
    un = get_untranslated(data)
    print(un.groupby(["lang", "split"]).size().to_string() if not un.empty else "  (none)")
    write_csv(un, "untranslated_rows.csv", do_write)

    header("5. WITHIN-SPLIT DUPLICATES")
    conf = get_conflicting_duplicates(data)
    exact = get_exact_duplicates(data)
    print("  conflicting-label collisions (one text -> >1 label tuple):")
    if conf.empty:
        print("    (none)")
    else:
        summ = conf.groupby(["lang", "split"])["group"].nunique()
        print(summ.to_string().replace("\n", "\n    ").rjust(0))
        print(f"    total collision groups: {conf['group'].nunique() if conf['lang'].nunique()==1 else summ.sum()}, "
              f"member rows: {len(conf)}")
    print("\n  exact duplicates (same text AND same labels — safe to dedup):")
    print("    " + (exact.groupby(["lang", "split"]).size().to_string().replace("\n", "\n    ")
                    if not exact.empty else "(none)"))
    write_csv(conf, "conflicting_label_duplicates.csv", do_write and not conf.empty)
    write_csv(exact, "exact_duplicates.csv", do_write and not exact.empty)

    header("6. TRAIN/TEST LEAKAGE (same text_en in both splits)")
    lk = get_leakage(data)
    print(f"  test rows whose text_en also appears in train: {len(lk)}")
    write_csv(lk, "train_test_leakage.csv", do_write and not lk.empty)

    header("7. CLASS BALANCE (english train)")
    if ("english", "train") in data:
        df = data[("english", "train")]
        for task in ["sentiment", "priority"]:
            vc = df[task].value_counts()
            print(f"\n  {task}  (imbalance {vc.max() / vc.min():.1f}x)")
            for k, v in vc.items():
                print(f"      {k:10} {v:6}  {v / len(df) * 100:5.1f}%")
        cat = df["category"].value_counts()
        rare = cat[cat < RARE_THRESHOLD]
        print(f"\n  category (77-way): {len(cat)} classes, min={cat.min()} "
              f"max={cat.max()} median={int(cat.median())}, "
              f"< {RARE_THRESHOLD} samples: {len(rare)} classes")

    header("8. TEXT LENGTH (chars)")
    print(f"  {'lang':9} {'split':5} {'min':>4} {'median':>7} {'max':>5}")
    for (lang, split), df in data.items():
        c = df["text"].str.len()
        print(f"  {lang:9} {split:5} {c.min():>4} {int(c.median()):>7} {c.max():>5}")

    if do_write:
        print(f"\nReview CSVs in {os.path.relpath(REPORT_DIR, REPO)}/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true", help="print only, no CSVs")
    args = ap.parse_args()
    report(load(), do_write=not args.no_write)


if __name__ == "__main__":
    main()
