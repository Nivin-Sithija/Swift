#!/usr/bin/env python3
"""
Append hand-authored colloquial Sinhala translations to
sinhala/sinhala_translation_progress.csv, keeping rows aligned to the
English TRAIN set and preserving category/sentiment/priority verbatim.

Input: a JSON file mapping TRAIN id (as string) -> Sinhala text, e.g.
    {"404": "...", "405": "...", ...}

Guarantees:
  * every index maps to an existing train row
  * refuses to append a train row already present (by text_en) unless --force
  * writes properly CSV-escaped rows in ascending index order
"""
import csv, json, os, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
TRAIN = os.path.join(DATASETS, "english", "train_labeled.csv")
PROG = os.path.join(DATASETS, "sinhala", "sinhala_translation_progress.csv")
COLS = ["id", "text_en", "text", "category", "sentiment", "priority"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json", help="path to {id: sinhala} json")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    train = list(csv.DictReader(open(TRAIN, encoding="utf-8")))
    mapping = json.load(open(args.json, encoding="utf-8"))

    existing_en = set()
    if os.path.exists(PROG):
        existing_en = {r["text_en"] for r in csv.DictReader(open(PROG, encoding="utf-8"))}

    new_rows, skipped, bad = [], 0, []
    for idx_s in sorted(mapping, key=lambda x: int(x)):
        i = int(idx_s)
        if not (0 <= i < len(train)):
            bad.append(i); continue
        r = train[i]
        si = mapping[idx_s].strip()
        if not si:
            bad.append(i); continue
        if r["text"] in existing_en and not args.force:
            skipped += 1; continue
        new_rows.append({"id": r["id"], "text_en": r["text"], "text": si,
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
