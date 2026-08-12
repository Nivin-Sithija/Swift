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

# What each prompt version asks for, and what it is allowed to see.
#
# `show_category` is not a convenience switch. v7 withholds the ticket's category from the
# labeler *on purpose*: a topic-only predictor reaches 0.385 Negative-F1 against the fine-tuned
# encoder's 0.633, so roughly 61% of the v5 label is explained by topic alone, and topic predicts
# v5 at AUC 0.852 against the human's 0.790. No rule wording fixes that while the category sits in
# the labeler's context. Putting the contract here rather than in a CLI flag means a v7 run cannot
# accidentally be scored with the category restored.
CONTRACTS: dict[str, dict] = {
    "v7": {"labels": ("sentiment",), "show_category": False},
    "v8": {"labels": ("sentiment",), "show_category": False},
}
DEFAULT_CONTRACT = {"labels": ("sentiment", "priority"), "show_category": True}

# Instrumentation, not a rule change. v7's first 500-row run had precision 0.540 -- 23 false
# positives against only 4 false negatives -- so before touching the prompt's wording, find out
# *which* clause is doing the over-firing. This appends a request for a trigger tag to whatever
# prompt file `--prompt` names; it does not change what the model decides, only what it reports
# about the decision. Reading the resulting trigger *distribution* is aggregate diagnosis, not
# reading individual gold rows to hand-craft an exception -- the thing we are avoiding.
DIAGNOSTIC_SUFFIX = """

---

# Diagnostic instrumentation (does not change how you decide `sentiment`)

Alongside `sentiment`, also return which clause caused a **Negative** decision, or `"none"` for
**Neutral**:

- `"A1"` — worn down by repetition or duration
- `"A2"` — dissatisfaction with the service
- `"A3"` — grievance framing about being blindsided ("why was I charged", "you didn't warn me")
- `"A4"` — curt, demanding phrasing
- `"B"`  — something done to them without consent, with distress language also present
- `"none"` — Neutral, nothing fired

If more than one clause applies, return the one that mattered most. This field is collected for
internal calibration only.
"""
CONTRACTS["v7-diag"] = {
    "labels": ("sentiment", "trigger"), "show_category": False,
    "prompt_file": "v7", "instructions_suffix": DIAGNOSTIC_SUFFIX,
}


def contract(version: str) -> dict:
    return CONTRACTS.get(version, DEFAULT_CONTRACT)


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


def build_batch_prompt(instructions: str, rows: pd.DataFrame, spec: dict) -> str:
    # `text` and `category` come only from the gold file, so the merge leaves
    # them unsuffixed; only sentiment/priority collide and get _gold/_v5.
    tickets = [
        {"n": i, **({"category": r.category} if spec["show_category"] else {}),
         "text": str(r.text)}
        for i, r in enumerate(rows.itertuples())
    ]
    shape = ", ".join(f'"{l}": "..."' for l in spec["labels"])
    return (
        instructions
        + "\n\n---\n\n# Tickets to label\n\n"
        + json.dumps(tickets, ensure_ascii=False, indent=1)
        + "\n\nReturn a JSON array with one object per ticket, in the same order, "
          f'each exactly {{"n": <n>, {shape}}}. '
          "Return only the JSON array."
    )


def label(instructions: str, rows: pd.DataFrame, spec: dict, workers: int = 6) -> pd.DataFrame:
    chunks = [rows.iloc[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    results: dict[int, dict] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(call_claude, build_batch_prompt(instructions, c, spec)): ci
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
    for lbl in spec["labels"]:
        out[f"{lbl}_pred"] = [results.get(i, {}).get(lbl) for i in range(len(rows))]
    return out


def topic_auc(df: pd.DataFrame, col: str) -> float | None:
    """How well `P(Negative | category)`, fitted on train, predicts this label column.

    The number v7 exists to move. Topic predicts v5 at 0.852 and the human annotator at 0.790 --
    a label source above ~0.79 is more topic-coupled than a person is, which is what makes a
    model trained on it learn topic instead of tone. Threshold-free on purpose: the base rates
    of the label sources differ, and AUC does not care.
    """
    from sklearn.metrics import roc_auc_score

    train = pd.read_csv(TRAIN)
    rate = train.groupby("category").sentiment.apply(lambda s: (s == "Negative").mean())
    ok = df[df[col].notna()]
    score_ = ok.category.map(rate).fillna((train.sentiment == "Negative").mean())
    y = (ok[col] == "Negative").astype(int)
    if y.nunique() < 2:
        return None
    return round(roc_auc_score(y, score_), 4)


def score(df: pd.DataFrame, sent_col: str, prio_col: str | None) -> dict:
    from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score

    ok = df[df[sent_col].notna()]
    if prio_col is not None:
        ok = ok[ok[prio_col].notna()]
    out = {
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
        "sentiment_negative_rate": round((ok[sent_col] == "Negative").mean(), 4),
        "sentiment_topic_auc": topic_auc(ok, sent_col),
    }
    if prio_col is not None:
        out.update({
            "priority_macro_f1": round(
                f1_score(ok.priority_gold, ok[prio_col], average="macro", zero_division=0), 4),
            "priority_agreement": round(accuracy_score(ok.priority_gold, ok[prio_col]), 4),
            "priority_kappa": round(cohen_kappa_score(ok.priority_gold, ok[prio_col]), 4),
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="v6", help="prompt version, e.g. v6")
    ap.add_argument("--split", default="dev", choices=["dev", "holdout", "all"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, help="score only the first N rows (smoke runs)")
    args = ap.parse_args()

    spec = contract(args.prompt)
    path = PROMPTS / f"labeling_prompt_{spec.get('prompt_file', args.prompt)}.md"
    if not path.exists():
        raise SystemExit(f"no such prompt: {path}")

    rows = split_gold(load_gold(), args.split)
    if args.limit:
        rows = rows.head(args.limit)
    print(f"prompt {args.prompt} | split {args.split} | {len(rows)} rows | "
          f"labels {spec['labels']} | category shown: {spec['show_category']}")
    print(f"gold: sentiment {rows.sentiment_gold.value_counts().to_dict()}")

    instructions = path.read_text(encoding="utf-8") + spec.get("instructions_suffix", "")
    labelled = label(instructions, rows, spec, workers=args.workers)

    prio_pred = "priority_pred" if "priority" in spec["labels"] else None
    new = score(labelled, "sentiment_pred", prio_pred)
    old = score(labelled.assign(s=labelled.sentiment_v5, p=labelled.priority_v5),
                "s", "p" if prio_pred else None)

    keys = ["sentiment_negative_f1", "sentiment_negative_recall", "sentiment_kappa",
            "sentiment_agreement", "sentiment_negative_rate", "sentiment_topic_auc"]
    if prio_pred:
        keys += ["priority_macro_f1", "priority_agreement", "priority_kappa"]
    print(f"\n{'metric':32s}{'v5':>10s}{args.prompt:>10s}{'delta':>10s}")
    for k in keys:
        o, n = old.get(k), new.get(k)
        if o is None or n is None:
            print(f"{k:32s}{'—':>10s}{'—' if n is None else f'{n:.4f}':>10s}")
            continue
        print(f"{k:32s}{o:>10.4f}{n:>10.4f}{n - o:>+10.4f}")
    # The human annotator's own coupling, as the target rather than zero.
    hum = topic_auc(labelled.rename(columns={"sentiment_gold": "s_gold"})
                    .assign(sentiment_gold=labelled.sentiment_gold), "sentiment_gold")
    hum_s = f"{hum:.4f}" if hum is not None else "—"
    print(f"{'sentiment_topic_auc (human)':32s}{hum_s:>10s}   <- the target, not 0")

    if "trigger" in spec["labels"]:
        # Aggregate counts only -- which clause fired, split by whether the prediction agreed
        # with gold. This is the diagnosis for a precision problem: it says which sub-rule to
        # tighten without reading any individual ticket's text.
        fp = labelled[(labelled.sentiment_gold == "Neutral") & (labelled.sentiment_pred == "Negative")]
        tp = labelled[(labelled.sentiment_gold == "Negative") & (labelled.sentiment_pred == "Negative")]
        print(f"\ntrigger distribution, false positives (n={len(fp)}, pred Negative / gold Neutral):")
        print(fp.trigger_pred.value_counts().to_string())
        print(f"\ntrigger distribution, true positives (n={len(tp)}, pred Negative / gold Negative):")
        print(tp.trigger_pred.value_counts().to_string())
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
