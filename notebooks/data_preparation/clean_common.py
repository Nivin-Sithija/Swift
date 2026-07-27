#!/usr/bin/env python3
"""
Shared helpers for the data-cleaning fix scripts (fix_labeling / dedup_reword /
translate_untranslated). Centralises dataset IO, id-aligned label/text updates
across all five language folders, and the `claude -p` call pattern the project
already uses for LLM labeling (see datasets/english/classify_test_dataset.py).
"""
from __future__ import annotations

import concurrent.futures
import csv
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATASETS = os.path.join(REPO, "datasets")
REPORT_DIR = os.path.join(HERE, "cleaning_report")
V5_PROMPT = os.path.join(DATASETS, "translation", "prompts", "labeling_prompt_v5.md")

LANGS = ["english", "sinhala", "singlish", "tamil", "tamilish"]
COLS = ["id", "text_en", "text", "category", "sentiment", "priority"]


# ------------------------------------------------------------------------- IO
def path(lang: str, split: str) -> str:
    return os.path.join(DATASETS, lang, f"{split}_labeled.csv")


def load_rows(lang: str, split: str) -> list[dict]:
    with open(path(lang, split), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_rows(lang: str, split: str, rows: list[dict]) -> None:
    with open(path(lang, split), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)


def existing_splits() -> list[tuple[str, str]]:
    return [(l, s) for l in LANGS for s in ("train", "test") if os.path.exists(path(l, s))]


def apply_label_updates(split: str, updates: dict[str, dict]) -> int:
    """
    Apply {id: {"sentiment": .., "priority": ..}} to EVERY language file for a
    split (labels are id-aligned across languages). Returns rows changed per file
    summed. Only writes fields present in the update dict.
    """
    total = 0
    for lang in LANGS:
        if not os.path.exists(path(lang, split)):
            continue
        rows = load_rows(lang, split)
        changed = 0
        for r in rows:
            u = updates.get(r["id"])
            if not u:
                continue
            for k, v in u.items():
                if r[k] != v:
                    r[k] = v
                    changed += 1
        if changed:
            save_rows(lang, split, rows)
            total += changed
    return total


# ------------------------------------------------------------------ claude -p
def call_claude(prompt: str, retries: int = 4, timeout: int = 90):
    """Run one `claude -p` call, parse a JSON array/object from stdout."""
    last = None
    for attempt in range(retries):
        try:
            res = subprocess.run(["claude", "-p"], input=prompt, capture_output=True,
                                 text=True, timeout=timeout)
            out = res.stdout.strip()
            out = re.sub(r"^```(json)?\s*|\s*```$", "", out, flags=re.MULTILINE).strip()
            # tolerate leading/trailing prose around the JSON payload
            m = re.search(r"(\[.*\]|\{.*\})", out, flags=re.DOTALL)
            return json.loads(m.group(1) if m else out)
        except Exception as e:
            last = e
            time.sleep(min(2 ** attempt, 20))
    print(f"    call failed after {retries} tries: {last}", file=sys.stderr)
    return None


def run_batches(prompts: list[str], max_workers: int = 8):
    """Run many claude -p prompts concurrently; yields (index, parsed) as done."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(call_claude, p): i for i, p in enumerate(prompts)}
        for fut in concurrent.futures.as_completed(futures):
            yield futures[fut], fut.result()


def v5_prompt() -> str:
    return open(V5_PROMPT, encoding="utf-8").read()


def delete_report(name: str) -> None:
    p = os.path.join(REPORT_DIR, name)
    if os.path.exists(p):
        os.remove(p)
        print(f"deleted {os.path.relpath(p, REPO)}")
