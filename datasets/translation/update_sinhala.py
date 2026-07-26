#!/usr/bin/env python3
"""
Apply hand-authored Sinhala corrections (re-worded to match a user's Singlish
edit) back into `sinhala/train_labeled.csv`, IN PLACE by id — as
opposed to append_sinhala.py, which only appends brand-new rows.

Input: a JSON file mapping id (as string) -> new Sinhala text, e.g.
    {"0": "තාම මගේ කාඩ් එක තැපැලෙන් ආවෙ නෑ"}

Guarantees:
  * every index is in range
  * category/sentiment/priority/text_en are left untouched
  * refuses to touch a row whose text didn't actually change, unless --force
"""
import argparse
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
SINHALA = os.path.join(DATASETS, "sinhala", "train_labeled.csv")
COLS = ["id", "text_en", "text", "category", "sentiment", "priority"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("json", help="path to {id: new sinhala text} json")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(SINHALA, encoding="utf-8")))
    mapping = json.load(open(args.json, encoding="utf-8"))

    bad, unchanged, updated = [], 0, 0
    for idx_s in sorted(mapping, key=lambda x: int(x)):
        i = int(idx_s)
        if not (0 <= i < len(rows)):
            bad.append(i)
            continue
        new_si = mapping[idx_s].strip()
        if not new_si:
            bad.append(i)
            continue
        if rows[i]["text"] == new_si and not args.force:
            unchanged += 1
            continue
        rows[i]["text"] = new_si
        updated += 1

    if bad:
        raise SystemExit(f"ERROR: bad/empty indices: {bad[:20]}")

    with open(SINHALA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)

    print(f"updated {updated} row(s) (skipped {unchanged} already matching); "
          f"{len(rows)} total rows in {os.path.relpath(SINHALA, DATASETS)}")


if __name__ == "__main__":
    main()
