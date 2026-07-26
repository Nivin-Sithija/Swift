#!/usr/bin/env python3
"""
Generate the Singlish (romanized Sinhala) dataset from
`sinhala/train_labeled.csv`, row-aligned.

Output: `singlish/train_labeled.csv`, columns
    id,text_en,text,category,sentiment,priority
`id` is the 0-based data-row index in sinhala/train_labeled.csv — the
key used by singlish_diff.py / update_sinhala.py to keep the two files
aligned once the user starts hand-editing text.

Usage:
    python generate_singlish.py
"""
import csv
import os

from singlishify import singlishify

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
SINHALA = os.path.join(DATASETS, "sinhala", "train_labeled.csv")
OUT = os.path.join(DATASETS, "singlish", "train_labeled.csv")
OUT_COLS = ["id", "text_en", "text", "category", "sentiment", "priority"]


def main() -> None:
    rows = list(csv.DictReader(open(SINHALA, encoding="utf-8")))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLS)
        w.writeheader()
        for i, r in enumerate(rows):
            w.writerow({
                "id": i,
                "text_en": r["text_en"],
                "text": singlishify(r["text"]),
                "category": r["category"],
                "sentiment": r["sentiment"],
                "priority": r["priority"],
            })
    print(f"wrote {len(rows)} rows -> {os.path.relpath(OUT, DATASETS)}")


if __name__ == "__main__":
    main()
