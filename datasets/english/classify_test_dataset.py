#!/usr/bin/env python3
"""
Classify sentiment + priority for every row of test_labeled.csv using the
final v5 prompt, via concurrent `claude -p` CLI calls. Same pipeline as
classify_full_dataset.py (which did this for train_labeled.csv), pointed at
the test split instead so both splits carry v5 labels in the same style.

Reads text/category from the CURRENT test_labeled.csv (not "original
dataset/test.csv") so any hand-edits already made to the English test text
are preserved; only sentiment/priority are replaced.
"""
import argparse
import concurrent.futures
import csv
import json
import re
import subprocess
import sys
import time

ROOT = "/Users/sithijaseneviratne/Documents/Github/Swift/datasets"
PROMPT_PATH = f"{ROOT}/translation/prompts/labeling_prompt_v5.md"
SRC_PATH = f"{ROOT}/english/test_labeled.csv"
OUT_PATH = f"{ROOT}/english/test_labeled_v5_full.csv"
BATCH_SIZE = 20
MAX_WORKERS = 10

BASE_PROMPT = open(PROMPT_PATH, encoding="utf-8").read()


def build_batch_prompt(batch):
    lines = [BASE_PROMPT, "", "---", "",
             f"Label the following {len(batch)} tickets per the rules above. "
             'Output ONLY a JSON array, no other text, no markdown fences - '
             'one object per ticket in the same order, each shaped exactly '
             'like {"id": <id>, "sentiment": "Neutral"|"Negative", "priority": "Low"|"Medium"|"High"}.',
             ""]
    for row in batch:
        text = row["text"].replace('"', "'")
        lines.append(f'{row["row_index"]}. [id={row["row_index"]}] [category={row["category"]}] "{text}"')
    return "\n".join(lines)


def call_claude(prompt, retries=3):
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["claude", "-p"], input=prompt, capture_output=True,
                text=True, timeout=180,
            )
            out = result.stdout.strip()
            out = re.sub(r"^```(json)?\s*|\s*```$", "", out, flags=re.MULTILINE).strip()
            return json.loads(out)
        except Exception as e:
            print(f"    retry {attempt+1}: {e}", file=sys.stderr)
            time.sleep(2)
    return None


def process_batch(bi, batch):
    return bi, call_claude(build_batch_prompt(batch))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="only process the first N rows (smoke test)")
    ap.add_argument("--out", default=OUT_PATH)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(SRC_PATH, encoding="utf-8")))
    for i, r in enumerate(rows):
        r["row_index"] = i
    if args.limit:
        rows = rows[:args.limit]

    batches = [rows[i:i + BATCH_SIZE] for i in range(0, len(rows), BATCH_SIZE)]
    results = {}
    failed_batches = []
    done = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(process_batch, bi, b): bi for bi, b in enumerate(batches, 1)}
        for fut in concurrent.futures.as_completed(futures):
            bi, data = fut.result()
            done += 1
            if data is None:
                failed_batches.append(bi)
                print(f"[{done}/{len(batches)}] batch {bi} FAILED", file=sys.stderr)
                continue
            for item in data:
                results[int(item["id"])] = {"sentiment": item["sentiment"], "priority": item["priority"]}
            print(f"[{done}/{len(batches)}] batch {bi} ok ({len(results)} labeled so far)", file=sys.stderr)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["row_index", "text", "category", "sentiment", "priority"])
        w.writeheader()
        missing = 0
        for i, r in enumerate(rows):
            res = results.get(r["row_index"])
            if res is None:
                missing += 1
                w.writerow({"row_index": r["row_index"], "text": r["text"], "category": r["category"],
                            "sentiment": "", "priority": ""})
                continue
            w.writerow({"row_index": r["row_index"], "text": r["text"], "category": r["category"], **res})

    print(f"\ndone: {len(rows) - missing}/{len(rows)} labeled -> {args.out}", file=sys.stderr)
    if failed_batches:
        print(f"FAILED batches (need re-run): {failed_batches}", file=sys.stderr)


if __name__ == "__main__":
    main()
