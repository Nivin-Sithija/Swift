#!/usr/bin/env python3
"""
Find rows where the hand-edited `singlish/train_labeled.csv`
differs from what generate_singlish.py would produce from the CURRENT
`sinhala/train_labeled.csv` — i.e. rows the user has hand-fixed in Singlish
that still need the matching edit applied to Sinhala's `text`.

sinhala/train_labeled.csv is never touched by the user directly (no Sinhala
keyboard), so re-deriving the "expected" Singlish on the fly and diffing
against the actual file is enough; no separate baseline snapshot is needed.

Usage:
    python singlish_diff.py                 # print changed rows
    python singlish_diff.py --json out.json # {id: new_singlish_text}
"""
import argparse
import csv
import json
import os

from singlishify import singlishify

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
SINHALA = os.path.join(DATASETS, "sinhala", "train_labeled.csv")
SINGLISH = os.path.join(DATASETS, "singlish", "train_labeled.csv")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write {id: new_singlish_text} here")
    args = ap.parse_args()

    si_rows = list(csv.DictReader(open(SINHALA, encoding="utf-8")))
    sg_rows = list(csv.DictReader(open(SINGLISH, encoding="utf-8")))
    if len(si_rows) != len(sg_rows):
        raise SystemExit(
            f"row count mismatch: sinhala={len(si_rows)} singlish={len(sg_rows)} "
            "(did rows get added/removed? this tool only expects text edits)"
        )

    changed = {}
    for i, (si_r, sg_r) in enumerate(zip(si_rows, sg_rows)):
        expected = singlishify(si_r["text"])
        actual = sg_r["text"]
        if actual != expected:
            changed[i] = {
                "text_en": si_r["text_en"],
                "current_text_si": si_r["text"],
                "old_singlish": expected,
                "new_singlish": actual,
            }

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({str(k): v["new_singlish"] for k, v in changed.items()}, f,
                      ensure_ascii=False, indent=2)
        print(f"wrote {len(changed)} changed rows -> {args.json}")
        return

    print(f"{len(changed)} row(s) edited:\n")
    for i, d in changed.items():
        print(f"[{i}] {d['text_en']}")
        print(f"  current si : {d['current_text_si']}")
        print(f"  old singlish: {d['old_singlish']}")
        print(f"  new singlish: {d['new_singlish']}")
        print()


if __name__ == "__main__":
    main()
