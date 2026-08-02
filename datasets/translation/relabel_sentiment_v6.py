#!/usr/bin/env python3
"""Re-label sentiment across the corpus with the v6 prompt.

Two phases, deliberately separate:

    python datasets/translation/relabel_sentiment_v6.py --stage
    python datasets/translation/relabel_sentiment_v6.py --apply

`--stage` calls the LLM and writes `ml/reports/relabel_v6_staging.csv`. It reads
the datasets but never writes to them, so it is safe to run at any time and can
be re-run if a batch fails.

`--apply` copies the staged sentiment into all five language folders. It rewrites
source data, so it is a separate, explicit step.

**Only the `sentiment` column is touched.** v6's priority section is byte-identical
to v5's -- a fee reprior was tried and regressed on the held-out gold half -- so
re-running priority would only inject LLM sampling noise into labels that are not
meant to change.

Labels stay id-aligned: sentiment is decided once on the English text and copied
to all five languages, exactly as v5 did. Nothing is ever labelled per-language.
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
PROMPT = REPO / "datasets" / "translation" / "prompts" / "labeling_prompt_v6.md"
DATASETS = REPO / "datasets"
STAGING = REPO / "ml" / "reports" / "relabel_v6_staging.csv"
SNAPSHOT = REPO / "ml" / "reports" / "relabel_v6_pre_snapshot.csv"
LANGUAGES = ["english", "sinhala", "singlish", "tamil", "tamilish"]
BATCH = 10


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
    print(f"  batch failed after {retries} tries: {last}", file=sys.stderr)
    return None


def batch_prompt(instructions: str, rows: pd.DataFrame) -> str:
    tickets = [{"n": i, "category": r.category, "text": str(r.text_en)}
               for i, r in enumerate(rows.itertuples())]
    return (
        instructions
        + "\n\n---\n\n# Tickets to label\n\n"
        + json.dumps(tickets, ensure_ascii=False, indent=1)
        + "\n\nReturn a JSON array with one object per ticket, in the same order, "
          'each exactly {"n": <n>, "sentiment": "Neutral"|"Negative"}. '
          "Return only the JSON array."
    )


def stage(workers: int, limit: int | None) -> None:
    instructions = PROMPT.read_text(encoding="utf-8")
    frames = []
    for split in ("train", "test"):
        df = pd.read_csv(DATASETS / "english" / f"{split}_labeled.csv")
        df["split"] = split
        frames.append(df)
    english = pd.concat(frames, ignore_index=True)
    if limit:
        english = english.head(limit)

    english[["id", "split", "sentiment", "priority"]].to_csv(SNAPSHOT, index=False)
    print(f"snapshot of current labels -> {SNAPSHOT}")
    print(f"labelling {len(english)} English rows with v6, {workers} workers")

    chunks = [english.iloc[i:i + BATCH] for i in range(0, len(english), BATCH)]
    results: dict[int, str] = {}
    started = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(call_claude, batch_prompt(instructions, c)): ci
                   for ci, c in enumerate(chunks)}
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            ci, parsed, done = futures[fut], fut.result(), done + 1
            if done % 10 == 0 or done == len(chunks):
                rate = done / max(time.time() - started, 1e-9)
                eta = (len(chunks) - done) / max(rate, 1e-9) / 60
                print(f"  {done}/{len(chunks)} batches  eta {eta:.0f}m", flush=True)
            if not parsed:
                continue
            for item in parsed:
                try:
                    pos = ci * BATCH + int(item["n"])
                    val = str(item["sentiment"]).strip().title()
                    if val in {"Neutral", "Negative"} and pos < len(english):
                        results[pos] = val
                except (KeyError, TypeError, ValueError):
                    continue

    out = english[["id", "split", "text_en", "category", "sentiment", "priority"]].copy()
    out = out.rename(columns={"sentiment": "sentiment_v5"})
    out["sentiment_v6"] = [results.get(i) for i in range(len(out))]

    missing = out.sentiment_v6.isna().sum()
    out.to_csv(STAGING, index=False)
    print(f"\nwrote {STAGING}")
    print(f"unlabelled rows: {missing} (re-run --stage to retry; existing rows are kept)")

    ok = out[out.sentiment_v6.notna()]
    print(f"\nv5 -> v6 sentiment shift on {len(ok)} rows:")
    print(pd.crosstab(ok.sentiment_v5, ok.sentiment_v6).to_string())
    print(f"\nv5 Negative rate: {(ok.sentiment_v5 == 'Negative').mean():.4f}")
    print(f"v6 Negative rate: {(ok.sentiment_v6 == 'Negative').mean():.4f}")
    print(f"rows changed    : {(ok.sentiment_v5 != ok.sentiment_v6).sum()}")


def apply() -> None:
    if not STAGING.exists():
        raise SystemExit(f"no staging file: {STAGING}. Run --stage first.")

    staged = pd.read_csv(STAGING)
    staged = staged[staged.sentiment_v6.notna()]
    if staged.empty:
        raise SystemExit("staging file has no labelled rows")

    lookup = {(r.split, r.id): r.sentiment_v6 for r in staged.itertuples()}
    print(f"applying {len(lookup)} sentiment labels to {len(LANGUAGES)} languages")

    for lang in LANGUAGES:
        for split in ("train", "test"):
            path = DATASETS / lang / f"{split}_labeled.csv"
            df = pd.read_csv(path)
            new = [lookup.get((split, i), old)
                   for i, old in zip(df["id"], df["sentiment"])]
            changed = sum(a != b for a, b in zip(df["sentiment"], new))
            df["sentiment"] = new
            df.to_csv(path, index=False)
            print(f"  {lang:9s} {split:5s} {changed:5d} labels changed")

    # the invariant that matters: sentiment identical across languages per id
    base = {}
    for split in ("train", "test"):
        ref = pd.read_csv(DATASETS / "english" / f"{split}_labeled.csv").set_index("id")
        for lang in LANGUAGES[1:]:
            other = pd.read_csv(DATASETS / lang / f"{split}_labeled.csv").set_index("id")
            common = ref.index.intersection(other.index)
            bad = int((ref.loc[common, "sentiment"] != other.loc[common, "sentiment"]).sum())
            base[f"{lang}/{split}"] = bad
    if any(base.values()):
        raise SystemExit(f"ALIGNMENT BROKEN: {base}")
    print("\nid-alignment verified: sentiment identical across all five languages")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", action="store_true", help="call the LLM, write staging only")
    ap.add_argument("--apply", action="store_true", help="copy staged labels into datasets/")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None, help="stage only the first N rows")
    args = ap.parse_args()

    if args.stage:
        stage(args.workers, args.limit)
    elif args.apply:
        apply()
    else:
        ap.error("pass --stage or --apply")


if __name__ == "__main__":
    main()
