"""
Apply the high-confidence Positive->Neutral bulk fix (sentiment_bulk_fix_candidates.csv)
to all three train_labeled.csv files. Sinhala/Singlish copy sentiment/priority
verbatim from English, so the same row-level fix applies to all three,
matched by English row_index (Singlish has its own row_index column aligned
1:1 with English; Sinhala is matched by text_en since it has no row_index).
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
EN_TRAIN = os.path.join(DATASETS, "english", "train_labeled.csv")
SI_TRAIN = os.path.join(DATASETS, "sinhala", "train_labeled.csv")
SG_TRAIN = os.path.join(DATASETS, "singlish", "train_labeled.csv")
BULK_FIX = os.path.join(HERE, "sentiment_bulk_fix_candidates.csv")


def load_fix_indices():
    rows = list(csv.DictReader(open(BULK_FIX, encoding="utf-8")))
    return {int(r["row_index"]) for r in rows}


def main():
    fix_indices = load_fix_indices()
    print(f"loaded {len(fix_indices)} row indices to fix (Positive -> Neutral)")

    en_rows = list(csv.DictReader(open(EN_TRAIN, encoding="utf-8")))
    en_fieldnames = list(en_rows[0].keys())
    en_text_by_index = {}
    changed = 0
    for i, row in enumerate(en_rows):
        en_text_by_index[i] = row["text"]
        if i in fix_indices:
            assert row["sentiment"] == "Positive", f"row {i} expected Positive, got {row['sentiment']}"
            row["sentiment"] = "Neutral"
            changed += 1
    with open(EN_TRAIN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=en_fieldnames)
        w.writeheader()
        w.writerows(en_rows)
    print(f"english: {changed} rows fixed -> {EN_TRAIN}")

    fix_texts = {en_text_by_index[i] for i in fix_indices}

    si_rows = list(csv.DictReader(open(SI_TRAIN, encoding="utf-8")))
    si_fieldnames = list(si_rows[0].keys())
    si_changed = 0
    for row in si_rows:
        if row["text_en"] in fix_texts:
            row["sentiment"] = "Neutral"
            si_changed += 1
    with open(SI_TRAIN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=si_fieldnames)
        w.writeheader()
        w.writerows(si_rows)
    print(f"sinhala: {si_changed} rows fixed -> {SI_TRAIN}")

    sg_rows = list(csv.DictReader(open(SG_TRAIN, encoding="utf-8")))
    sg_fieldnames = list(sg_rows[0].keys())
    sg_changed = 0
    for row in sg_rows:
        if int(row["row_index"]) in fix_indices:
            row["sentiment"] = "Neutral"
            sg_changed += 1
    with open(SG_TRAIN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sg_fieldnames)
        w.writeheader()
        w.writerows(sg_rows)
    print(f"singlish: {sg_changed} rows fixed -> {SG_TRAIN}")


if __name__ == "__main__":
    main()
