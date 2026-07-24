#!/usr/bin/env python3
"""
Append hand-authored colloquial Sinhala translations to
llm-zeroshot/sinhala/test_translation_progress.csv, keeping rows aligned to
the English TEST set (llm-zeroshot/english/test_labeled.csv) and preserving
category/sentiment/priority verbatim. Mirrors append_sinhala.py (train).

Input: a JSON file mapping TEST row-index (as string) -> Sinhala text, e.g.
    {"0": "...", "1": "...", ...}

Guarantees:
  * every index maps to an existing test row
  * refuses to append a test row already present (by text_en) unless --force
  * writes properly CSV-escaped rows in ascending index order
"""
import csv, json, os, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
TEST = os.path.join(DATASETS, "llm-zeroshot", "english", "test_labeled.csv")
PROG = os.path.join(DATASETS, "llm-zeroshot", "sinhala", "test_translation_progress.csv")
COLS = ["text_en", "text_si", "category", "sentiment", "priority"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json", help="path to {index: sinhala} json")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    test = list(csv.DictReader(open(TEST, encoding="utf-8")))
    mapping = json.load(open(args.json, encoding="utf-8"))

    existing_en = set()
    if os.path.exists(PROG):
        existing_en = {r["text_en"] for r in csv.DictReader(open(PROG, encoding="utf-8"))}

    new_rows, skipped, bad = [], 0, []
    for idx_s in sorted(mapping, key=lambda x: int(x)):
        i = int(idx_s)
        if not (0 <= i < len(test)):
            bad.append(i); continue
        r = test[i]
        si = mapping[idx_s].strip()
        if not si:
            bad.append(i); continue
        if r["text"] in existing_en and not args.force:
            skipped += 1; continue
        new_rows.append({"text_en": r["text"], "text_si": si,
                         "category": r["category"], "sentiment": r["sentiment"],
                         "priority": r["priority"]})

    if bad:
        print(f"ERROR: bad/empty indices: {bad[:20]}", file=sys.stderr)
        sys.exit(1)

    write_header = not os.path.exists(PROG) or os.path.getsize(PROG) == 0
    with open(PROG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        if write_header:
            w.writeheader()
        w.writerows(new_rows)

    total = sum(1 for _ in csv.DictReader(open(PROG, encoding="utf-8")))
    print(f"appended {len(new_rows)} rows (skipped {skipped} already-present); "
          f"progress file now has {total} rows")


if __name__ == "__main__":
    main()
