#!/usr/bin/env python3
"""
Resume classify_test_dataset.py for rows that came back empty (failed
batches) in test_labeled_v5_full.csv. Lower concurrency than the first pass
to avoid whatever caused the mid-run failure streak, and prints stderr on
failure so a real cause shows up instead of just the JSON-parse symptom.
"""
import concurrent.futures
import csv
import json
import re
import subprocess
import sys
import time

ROOT = "/Users/sithijaseneviratne/Documents/Github/Swift/datasets"
PROMPT_PATH = f"{ROOT}/translation/prompts/labeling_prompt_v5.md"
FULL_PATH = f"{ROOT}/english/test_labeled_v5_full.csv"
BATCH_SIZE = 20
MAX_WORKERS = 4

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


def call_claude(prompt, retries=4):
    last_stderr = ""
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["claude", "-p"], input=prompt, capture_output=True,
                text=True, timeout=180,
            )
            out = result.stdout.strip()
            out = re.sub(r"^```(json)?\s*|\s*```$", "", out, flags=re.MULTILINE).strip()
            if not out:
                last_stderr = result.stderr.strip()[:300]
                raise ValueError(f"empty stdout; stderr={last_stderr!r}; rc={result.returncode}")
            return json.loads(out)
        except Exception as e:
            print(f"    retry {attempt+1}: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    return None


def process_batch(bi, batch):
    return bi, call_claude(build_batch_prompt(batch))


def main():
    rows = list(csv.DictReader(open(FULL_PATH, encoding="utf-8")))
    missing_rows = [r for r in rows if not r["sentiment"]]
    print(f"resuming {len(missing_rows)} missing rows", file=sys.stderr)

    batches = [missing_rows[i:i + BATCH_SIZE] for i in range(0, len(missing_rows), BATCH_SIZE)]
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

    still_missing = 0
    for r in rows:
        idx = int(r["row_index"])
        if idx in results:
            r["sentiment"] = results[idx]["sentiment"]
            r["priority"] = results[idx]["priority"]
        elif not r["sentiment"]:
            still_missing += 1

    with open(FULL_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["row_index", "text", "category", "sentiment", "priority"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"\ndone: {len(rows) - still_missing}/{len(rows)} labeled -> {FULL_PATH}", file=sys.stderr)
    if failed_batches:
        print(f"FAILED batches (need re-run): {failed_batches}", file=sys.stderr)


if __name__ == "__main__":
    main()
