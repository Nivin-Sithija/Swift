#!/usr/bin/env python3
"""
One-shot evaluation: label the 500-row blind benchmark with a real LLM call
(via the `claude` CLI's non-interactive mode) using a given prompt file as
instructions, then score against the hand-annotated gold labels already
present in 500_benchmarkset.csv (sentiment/priority columns, from the
label-studio annotation pass).

The model only ever sees ticket text + category - the gold columns are read
only for scoring, never fed into the prompt.

Usage:
    python3 llm_label_gold.py --prompt ../../translation/prompts/labeling_prompt_v5.md --tag v5
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD_PATH = f"{HERE}/500_benchmarkset.csv"
BATCH_SIZE = 20


def build_batch_prompt(base_prompt, batch):
    lines = [base_prompt, "", "---", "",
             f"Label the following {len(batch)} tickets per the rules above. "
             'Output ONLY a JSON array, no other text, no markdown fences - '
             'one object per ticket in the same order, each shaped exactly '
             'like {"id": <id>, "sentiment": "Neutral"|"Negative", "priority": "Low"|"Medium"|"High"}.',
             ""]
    for i, row in enumerate(batch, 1):
        text = row["text"].replace('"', "'")
        lines.append(f'{i}. [id={row["row_id"]}] [category={row["category"]}] "{text}"')
    return "\n".join(lines)


def call_claude(prompt, retries=3):
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["claude", "-p"], input=prompt, capture_output=True,
                text=True, timeout=180,
            )
            out = result.stdout.strip()
            out = re.sub(r"^```(json)?\s*|\s*```$", "", out.strip(), flags=re.MULTILINE).strip()
            return json.loads(out)
        except Exception as e:
            print(f"  attempt {attempt+1} failed: {e}", file=sys.stderr)
            time.sleep(2)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True, help="path to the labeling prompt .md file")
    ap.add_argument("--tag", required=True, help="short tag for output filenames, e.g. v5")
    args = ap.parse_args()

    base_prompt = open(args.prompt, encoding="utf-8").read()
    out_path = f"{HERE}/llm_gold_predictions_{args.tag}.csv"
    mismatch_path = f"{HERE}/llm_gold_{args.tag}_mismatches.csv"

    gold = list(csv.DictReader(open(GOLD_PATH, encoding="utf-8")))
    tasks = [{"row_id": g["row_id"], "category": g["category"], "text": g["text"]} for g in gold]

    results = {}
    batches = [tasks[i:i + BATCH_SIZE] for i in range(0, len(tasks), BATCH_SIZE)]
    for bi, batch in enumerate(batches, 1):
        print(f"batch {bi}/{len(batches)} ({len(batch)} tickets)...", file=sys.stderr)
        data = call_claude(build_batch_prompt(base_prompt, batch))
        if data is None:
            print(f"  FAILED batch {bi}, skipping {len(batch)} rows", file=sys.stderr)
            continue
        for item in data:
            results[str(item["id"])] = {"sentiment": item["sentiment"], "priority": item["priority"]}

    sent_correct = sent_total = 0
    prio_correct = prio_total = 0
    both_correct = 0
    sent_confusion, prio_confusion = {}, {}
    mismatches = []

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "row_id", "text", "category",
            "gold_sentiment", "pred_sentiment",
            "gold_priority", "pred_priority",
        ])
        w.writeheader()
        missing = 0
        for g in gold:
            r = results.get(g["row_id"])
            if r is None:
                missing += 1
                continue
            gold_sent, pred_sent = g["sentiment"], r["sentiment"]
            gold_prio, pred_prio = g["priority"], r["priority"]

            sent_total += 1
            if gold_sent == pred_sent:
                sent_correct += 1
            else:
                sent_confusion[(gold_sent, pred_sent)] = sent_confusion.get((gold_sent, pred_sent), 0) + 1

            prio_total += 1
            if gold_prio == pred_prio:
                prio_correct += 1
            else:
                prio_confusion[(gold_prio, pred_prio)] = prio_confusion.get((gold_prio, pred_prio), 0) + 1

            row = {
                "row_id": g["row_id"], "text": g["text"], "category": g["category"],
                "gold_sentiment": gold_sent, "pred_sentiment": pred_sent,
                "gold_priority": gold_prio, "pred_priority": pred_prio,
            }
            w.writerow(row)
            if gold_sent == pred_sent and gold_prio == pred_prio:
                both_correct += 1
            else:
                mismatches.append(row)

    print(f"\nlabeled {len(gold)-missing}/{len(gold)} rows -> {out_path}", file=sys.stderr)
    if missing:
        print(f"WARNING: {missing} rows missing (batch failures)", file=sys.stderr)

    if sent_total:
        print(f"\nSentiment accuracy: {sent_correct}/{sent_total} = {sent_correct/sent_total:.3%}")
        print("Sentiment confusion (gold -> pred : count):")
        for (g_, p_), c in sorted(sent_confusion.items(), key=lambda x: -x[1]):
            print(f"  {g_} -> {p_} : {c}")
    if prio_total:
        print(f"\nPriority accuracy: {prio_correct}/{prio_total} = {prio_correct/prio_total:.3%}")
        print("Priority confusion (gold -> pred : count):")
        for (g_, p_), c in sorted(prio_confusion.items(), key=lambda x: -x[1]):
            print(f"  {g_} -> {p_} : {c}")
    if sent_total:
        print(f"\nBoth-correct (exact match on both labels): {both_correct}/{sent_total} = {both_correct/sent_total:.3%}")

    if mismatches:
        with open(mismatch_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(mismatches[0].keys()))
            w.writeheader()
            w.writerows(mismatches)
        print(f"\n{len(mismatches)} mismatches written -> {mismatch_path}")


if __name__ == "__main__":
    main()
