#!/usr/bin/env python3
"""Score a labeling prompt against the human-annotated gold set.

The point of this script is to stop prompt versions being trusted on the basis
of the labels they themselves produced. A prompt is only better if it agrees
more with the *human* annotation in `datasets/english/500_benchmarkset.csv`.

The gold set is split in half. Prompt changes are developed against `dev` and
scored once on `holdout`. Scoring a prompt on the same rows that motivated its
changes measures memorisation, not improvement.

Usage:
    python datasets/translation/run_prompt_eval.py --prompt v6 --split dev
    python datasets/translation/run_prompt_eval.py --prompt v6 --split holdout
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
PROMPTS = REPO / "datasets" / "translation" / "prompts"
GOLD = REPO / "datasets" / "english" / "500_benchmarkset.csv"
TRAIN = REPO / "datasets" / "english" / "train_labeled.csv"
OUT_DIR = REPO / "ml" / "reports"
BATCH = 10
SEED = 42


def load_gold() -> pd.DataFrame:
    gold = pd.read_csv(GOLD)
    train = pd.read_csv(TRAIN)
    merged = gold.merge(train[["id", "sentiment", "priority"]],
                        left_on="row_id", right_on="id",
                        suffixes=("_gold", "_v5"))
    if len(merged) != len(gold):
        raise SystemExit(f"gold/train alignment lost: {len(merged)} of {len(gold)}")
    return merged


def split_gold(merged: pd.DataFrame, which: str) -> pd.DataFrame:
    """Deterministic stratified half-split. Must match across every run."""
    from sklearn.model_selection import train_test_split

    strat = merged.sentiment_gold + "|" + merged.priority_gold
    dev, holdout = train_test_split(merged, test_size=0.5, random_state=SEED,
                                    stratify=strat)
    return {"dev": dev, "holdout": holdout, "all": merged}[which].reset_index(drop=True)


def call_claude(prompt: str, retries: int = 4, timeout: int = 180):
    last = None
    for attempt in range(retries):
        try:
            res = subprocess.run(["claude", "-p"], input=prompt, capture_output=True,
                                 text=True, timeout=timeout)
            out = re.sub(r"^```(json)?\s*|\s*```$", "", res.stdout.strip(),
                         flags=re.MULTILINE).strip()
            m = re.search(r"(\[.*\]|\{.*\})", out, flags=re.DOTALL)
            return json.loads(m.group(1) if m else out)
        except Exception as exc:
            last = exc
            time.sleep(min(2 ** attempt, 20))
    print(f"    batch failed after {retries} tries: {last}", file=sys.stderr)
    return None


def build_batch_prompt(instructions: str, rows: pd.DataFrame) -> str:
    # `text` and `category` come only from the gold file, so the merge leaves
    # them unsuffixed; only sentiment/priority collide and get _gold/_v5.
    tickets = [{"n": i, "category": r.category, "text": str(r.text)}
               for i, r in enumerate(rows.itertuples())]
    return (
        instructions
        + "\n\n---\n\n# Tickets to label\n\n"
        + json.dumps(tickets, ensure_ascii=False, indent=1)
        + "\n\nReturn a JSON array with one object per ticket, in the same order, "
          'each exactly {"n": <n>, "sentiment": "...", "priority": "..."}. '
          "Return only the JSON array."
    )


def label(instructions: str, rows: pd.DataFrame, workers: int = 6) -> pd.DataFrame:
    chunks = [rows.iloc[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    results: dict[int, dict] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(call_claude, build_batch_prompt(instructions, c)): ci
                   for ci, c in enumerate(chunks)}
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            ci = futures[fut]
            parsed = fut.result()
            done += 1
            print(f"  batch {done}/{len(chunks)}", end="\r", flush=True)
            if not parsed:
                continue
            for item in parsed:
                try:
                    results[ci * BATCH + int(item["n"])] = item
                except (KeyError, TypeError, ValueError):
                    continue
    print()

    out = rows.copy()
    out["sentiment_pred"] = [results.get(i, {}).get("sentiment") for i in range(len(rows))]
    out["priority_pred"] = [results.get(i, {}).get("priority") for i in range(len(rows))]
    return out


def score(df: pd.DataFrame, sent_col: str, prio_col: str) -> dict:
    from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score

    ok = df[df[sent_col].notna() & df[prio_col].notna()]
    return {
        "n_scored": len(ok),
        "n_unparsed": len(df) - len(ok),
        "sentiment_negative_f1": round(
            f1_score(ok.sentiment_gold, ok[sent_col], pos_label="Negative",
                     zero_division=0), 4),
        "sentiment_negative_recall": round(
            ((ok.sentiment_gold == "Negative") & (ok[sent_col] == "Negative")).sum()
            / max((ok.sentiment_gold == "Negative").sum(), 1), 4),
        "sentiment_agreement": round(accuracy_score(ok.sentiment_gold, ok[sent_col]), 4),
        "sentiment_kappa": round(cohen_kappa_score(ok.sentiment_gold, ok[sent_col]), 4),
        "priority_macro_f1": round(
            f1_score(ok.priority_gold, ok[prio_col], average="macro", zero_division=0), 4),
        "priority_agreement": round(accuracy_score(ok.priority_gold, ok[prio_col]), 4),
        "priority_kappa": round(cohen_kappa_score(ok.priority_gold, ok[prio_col]), 4),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="v6", help="prompt version, e.g. v6")
    ap.add_argument("--split", default="dev", choices=["dev", "holdout", "all"])
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    path = PROMPTS / f"labeling_prompt_{args.prompt}.md"
    if not path.exists():
        raise SystemExit(f"no such prompt: {path}")

    rows = split_gold(load_gold(), args.split)
    print(f"prompt {args.prompt} | split {args.split} | {len(rows)} rows")
    print(f"gold: sentiment {rows.sentiment_gold.value_counts().to_dict()}")

    labelled = label(path.read_text(encoding="utf-8"), rows, workers=args.workers)

    new = score(labelled, "sentiment_pred", "priority_pred")
    old = score(labelled.assign(s=labelled.sentiment_v5, p=labelled.priority_v5), "s", "p")

    print(f"\n{'metric':32s}{'v5':>10s}{args.prompt:>10s}{'delta':>10s}")
    for k in ["sentiment_negative_f1", "sentiment_negative_recall", "sentiment_kappa",
              "priority_macro_f1", "priority_agreement", "priority_kappa"]:
        print(f"{k:32s}{old[k]:>10.4f}{new[k]:>10.4f}{new[k] - old[k]:>+10.4f}")
    if new["n_unparsed"]:
        print(f"\nWARNING: {new['n_unparsed']} rows unparsed and excluded")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    labelled.to_csv(OUT_DIR / f"prompt_{args.prompt}_{args.split}_labels.csv", index=False)
    pd.DataFrame([{"prompt": "v5", "split": args.split, **old},
                  {"prompt": args.prompt, "split": args.split, **new}]).to_csv(
        OUT_DIR / f"prompt_{args.prompt}_{args.split}_scores.csv", index=False)
    print(f"\nwrote {OUT_DIR / f'prompt_{args.prompt}_{args.split}_scores.csv'}")


if __name__ == "__main__":
    main()
