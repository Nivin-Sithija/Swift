"""Check returned translation files before they are scored (tracker B2v).

Pasting 150 rows through a chat window fails in specific, silent ways: the model
truncates at row 80, drops the ids and renumbers, wraps the whole thing in a code
fence, or answers in English because it lost the instruction. Every one of those
produces a file that loads fine and scores nonsense.

This refuses the file instead. It checks nothing about translation *quality* --
that is COMET-Kiwi and the blind ratings -- only that the file is the thing it
claims to be.

Run:
    .venv312/bin/python paper/experiments/validate_translations.py
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EVAL = REPO / "paper" / "translation_eval"
SAMPLES = EVAL / "samples"
SYSTEMS = EVAL / "systems"

SYSTEM_NAMES = ("openai", "gptoss", "google")
# A Sinhala translation must be in Sinhala. The cheapest reliable check is the
# Unicode block of the letters actually present.
SCRIPT_RANGE = {"sinhala": (0x0D80, 0x0DFF), "tamil": (0x0B80, 0x0BFF)}


def script_fraction(text: str, lang: str) -> float:
    lo, hi = SCRIPT_RANGE[lang]
    letters = [c for c in str(text) if c.isalpha()]
    if not letters:
        return 0.0
    return sum(lo <= ord(c) <= hi for c in letters) / len(letters)


def check(path: Path, lang: str, expected_ids: set[int]) -> list[str]:
    problems: list[str] = []
    raw = path.read_text()
    if raw.lstrip().startswith("```"):
        problems.append("file starts with a code fence -- strip it")
    try:
        df = pd.read_csv(path)
    except Exception as exc:                                     # noqa: BLE001
        return [f"will not parse as CSV: {exc}"]

    if list(df.columns[:2]) != ["id", "translation"]:
        problems.append(f"columns are {list(df.columns)}, expected ['id','translation']")
        return problems

    df = df.dropna(subset=["id"])
    try:
        got = set(df["id"].astype(int))
    except ValueError:
        return problems + ["the id column is not integral -- ids were renumbered or lost"]

    missing, extra = expected_ids - got, got - expected_ids
    if missing:
        problems.append(f"{len(missing)} id(s) missing, e.g. {sorted(missing)[:5]}")
    if extra:
        problems.append(f"{len(extra)} unexpected id(s), e.g. {sorted(extra)[:5]}")
    if df["id"].duplicated().any():
        problems.append(f"{int(df['id'].duplicated().sum())} duplicate id(s)")

    blank = df["translation"].isna() | (df["translation"].astype(str).str.strip() == "")
    if blank.any():
        problems.append(f"{int(blank.sum())} blank translation(s)")

    # Wrong-script rows: the usual cause is the model answering in English, or
    # transliterating instead of translating.
    frac = df.loc[~blank, "translation"].map(lambda t: script_fraction(t, lang))
    wrong = frac[frac < 0.5]
    if len(wrong):
        ids = df.loc[wrong.index, "id"].tolist()[:5]
        problems.append(f"{len(wrong)} row(s) under 50% {lang} script, e.g. ids {ids} "
                        f"-- answered in English or transliterated?")

    # A translation that is byte-identical to the English source is a copy, not a
    # translation, and it will quietly inflate any similarity metric.
    return problems


def main() -> int:
    sample = pd.read_csv(SAMPLES / "sample_ids.csv")
    expected = set(sample["id"].astype(int))
    print(f"expecting {len(expected)} ids per file\n")

    found = failed = 0
    for system in SYSTEM_NAMES:
        for lang in ("sinhala", "tamil"):
            path = SYSTEMS / f"{system}_{lang}.csv"
            if not path.exists():
                print(f"  {system:7} {lang:8} -- not collected yet")
                continue
            found += 1
            problems = check(path, lang, expected)
            if problems:
                failed += 1
                print(f"  {system:7} {lang:8} REJECTED")
                for p in problems:
                    print(f"      - {p}")
            else:
                print(f"  {system:7} {lang:8} OK ({len(expected)} rows)")

    print(f"\n{found} file(s) present, {failed} rejected")
    if found == 0:
        print("Nothing to validate. See paper/translation_eval/README.md for what to paste.")
    elif failed == 0 and found == len(SYSTEM_NAMES) * 2:
        print("All systems collected and valid -- B2 done. "
              "Next: build_rating_sheets.py, then score_translations.py.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
