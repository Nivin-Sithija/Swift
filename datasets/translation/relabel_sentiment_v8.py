#!/usr/bin/env python3
"""Re-label sentiment across the corpus with the v8 prompt.

Two phases, deliberately separate, same convention as `relabel_sentiment_v6.py`:

    python datasets/translation/relabel_sentiment_v8.py --stage
    python datasets/translation/relabel_sentiment_v8.py --apply

`--stage` calls the LLM and writes `ml/reports/relabel_v8_staging.csv`. It reads the
datasets but never writes to them, so it is safe to run at any time. `--apply` copies
the staged sentiment into all five language folders -- a separate, explicit step,
because it rewrites source data.

**v8 withholds category from the labeler, on purpose.** Unlike `relabel_sentiment_v6.py`,
the ticket payload here carries `text` only. This is the entire point of v8/v7: a
topic-only predictor explains ~61% of the v5 label (`ml/reports/RESULTS.md` §15.2), and
showing the category is how that leak happens. Re-adding it here to "help" the model would
silently undo the whole exercise.

**Sequential and resumable, deliberately.** A prior run of the eval harness at
`--workers 6` silently dropped 140/500 rows (empty stdout from `claude -p` under
concurrency, caught as a JSON parse failure and scored as unparsed). `--workers 1` here
by default avoids that class of failure outright. Every batch is written to the staging
file as it completes -- not buffered to the end -- so a crash or a `Ctrl-C` loses at most
one in-flight batch, and re-running `--stage` picks up exactly where it left off by
skipping rows the staging file already has an answer for.

**Rate limits wait, they do not fail the run.** If a batch's raw output looks like a
usage-limit message rather than a parse hiccup, the run sleeps six hours and retries the
same batch indefinitely rather than marking those rows unlabelled and moving on. A
genuine parse failure (malformed JSON, a truncated response) is not treated this way --
it gets the normal bounded retry budget and then is skipped and reported, exactly as
`relabel_sentiment_v6.py` does, so the run does not hang forever on a batch that will
never succeed.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO / "datasets" / "translation" / "prompts" / "labeling_prompt_v8.md"
DATASETS = REPO / "datasets"
STAGING = REPO / "ml" / "reports" / "relabel_v8_staging.csv"
SNAPSHOT = REPO / "ml" / "reports" / "relabel_v8_pre_snapshot.csv"
LANGUAGES = ["english", "sinhala", "singlish", "tamil", "tamilish"]
BATCH = 10
RATE_LIMIT_SLEEP_SECONDS = 6 * 60 * 60

# Substrings that mark a `claude -p` response as a usage-limit refusal rather than a
# malformed-JSON hiccup. Matched case-insensitively against raw stdout+stderr, before any
# JSON parsing is attempted -- a rate-limit message is not JSON at all.
RATE_LIMIT_MARKERS = (
    "usage limit", "rate limit", "quota", "try again later",
    "too many requests", "429",
)


def looks_rate_limited(text: str) -> bool:
    # Empty output counts as rate-limited too. Measured directly: one run had 993/1308
    # batches fail with a JSONDecodeError on an *empty* string -- `claude -p` returning
    # normally (exit 0, no stderr) with nothing on stdout -- and no textual marker of any
    # kind. An interactive call immediately afterward succeeded instantly. That is a silent
    # throttle, not a malformed response, and treating it as a hard failure would have
    # permanently dropped three quarters of the corpus instead of waiting it out.
    if not text.strip():
        return True
    low = text.lower()
    return any(m in low for m in RATE_LIMIT_MARKERS)


def call_claude(prompt: str, retries: int = 4, timeout: int = 180):
    """Returns (parsed_json_or_None, raw_text). Callers decide what a None means."""
    last_raw = ""
    for attempt in range(retries):
        try:
            res = subprocess.run(["claude", "-p"], input=prompt, capture_output=True,
                                 text=True, timeout=timeout)
        except Exception as exc:
            # Only a subprocess-level failure (timeout, launch error) loses the raw text --
            # there was no response to lose. A parse failure below keeps `raw` intact instead
            # of being overwritten by the exception message, which is what silently destroyed
            # the diagnostic signal in the version of this function that produced the empty-
            # response failures in the first place.
            last_raw = f"{type(exc).__name__}: {exc}"
            time.sleep(min(2 ** attempt, 20))
            continue

        raw = (res.stdout or "") + (res.stderr or "")
        last_raw = raw
        if looks_rate_limited(raw):
            return None, raw
        try:
            out = re.sub(r"^```(json)?\s*|\s*```$", "", res.stdout.strip(),
                         flags=re.MULTILINE).strip()
            m = re.search(r"(\[.*\]|\{.*\})", out, flags=re.DOTALL)
            return json.loads(m.group(1) if m else out), raw
        except Exception:
            time.sleep(min(2 ** attempt, 20))
    return None, last_raw


def call_claude_patient(prompt: str) -> dict | None:
    """Retries forever through rate-limit responses; gives up after one non-rate-limit failure."""
    while True:
        parsed, raw = call_claude(prompt)
        if parsed is not None:
            return parsed
        if looks_rate_limited(raw):
            print(f"\n  rate-limited -- sleeping {RATE_LIMIT_SLEEP_SECONDS/3600:.0f}h "
                  f"({time.strftime('%Y-%m-%d %H:%M:%S')})", flush=True)
            time.sleep(RATE_LIMIT_SLEEP_SECONDS)
            print(f"  resuming ({time.strftime('%Y-%m-%d %H:%M:%S')})", flush=True)
            continue
        print(f"  batch failed (not rate-limit): {raw[:200]!r}", file=sys.stderr)
        return None


def batch_prompt(instructions: str, rows: pd.DataFrame) -> str:
    # No `category` key -- withholding it is the entire point of v7/v8.
    tickets = [{"n": i, "text": str(r.text_en)} for i, r in enumerate(rows.itertuples())]
    return (
        instructions
        + "\n\n---\n\n# Tickets to label\n\n"
        + json.dumps(tickets, ensure_ascii=False, indent=1)
        + "\n\nReturn a JSON array with one object per ticket, in the same order, "
          'each exactly {"n": <n>, "sentiment": "Neutral"|"Negative"}. '
          "Return only the JSON array."
    )


def _load_english() -> pd.DataFrame:
    frames = []
    for split in ("train", "test"):
        df = pd.read_csv(DATASETS / "english" / f"{split}_labeled.csv")
        df["split"] = split
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def stage(workers: int, limit: int | None) -> None:
    if workers != 1:
        print(f"note: --workers {workers} requested, but concurrency is what dropped 140/500 "
              f"rows in the eval run this staging script exists to avoid. Ignoring; running "
              f"sequential.", file=sys.stderr)

    instructions = PROMPT_PATH.read_text(encoding="utf-8")
    english = _load_english()
    if limit:
        english = english.head(limit)

    if not SNAPSHOT.exists():
        english[["id", "split", "sentiment", "priority"]].to_csv(SNAPSHOT, index=False)
        print(f"snapshot of current labels -> {SNAPSHOT}")

    # Resume: whatever the staging file already has an answer for is not re-queried.
    done: dict[tuple[str, int], str] = {}
    if STAGING.exists():
        prior = pd.read_csv(STAGING)
        prior = prior[prior.sentiment_v6.notna()]
        done = {(r.split, r.id): r.sentiment_v6 for r in prior.itertuples()}
        print(f"resuming: {len(done)} rows already labelled in {STAGING}")

    remaining = english[~english.apply(lambda r: (r.split, r.id) in done, axis=1)]
    print(f"labelling {len(remaining)} of {len(english)} English rows with v8 "
          f"(category withheld), sequential, {len(remaining) // BATCH + 1} batches")

    chunks = [remaining.iloc[i:i + BATCH] for i in range(0, len(remaining), BATCH)]
    started = time.time()

    for ci, chunk in enumerate(chunks):
        parsed = call_claude_patient(batch_prompt(instructions, chunk))
        if parsed:
            for item in parsed:
                try:
                    pos = int(item["n"])
                    val = str(item["sentiment"]).strip().title()
                    if val in {"Neutral", "Negative"} and pos < len(chunk):
                        row = chunk.iloc[pos]
                        done[(row.split, row.id)] = val
                except (KeyError, TypeError, ValueError, IndexError):
                    continue

        # Write progress after every batch, not at the end.
        out = english[["id", "split", "text_en", "category", "sentiment", "priority"]].copy()
        out = out.rename(columns={"sentiment": "sentiment_v5"})
        out["sentiment_v6"] = [done.get((r.split, r.id)) for r in out.itertuples()]
        out.to_csv(STAGING, index=False)

        rate = (ci + 1) / max(time.time() - started, 1e-9)
        eta = (len(chunks) - ci - 1) / max(rate, 1e-9) / 60
        if (ci + 1) % 5 == 0 or ci + 1 == len(chunks):
            print(f"  {ci+1}/{len(chunks)} batches  {len(done)}/{len(english)} labelled  "
                  f"eta {eta:.0f}m", flush=True)

    ok = pd.read_csv(STAGING)
    ok = ok[ok.sentiment_v6.notna()]
    missing = len(english) - len(ok)
    print(f"\nwrote {STAGING}")
    print(f"unlabelled rows: {missing} (re-run --stage to retry; existing rows are kept)")
    if len(ok):
        print(f"\nv5 -> v8 sentiment shift on {len(ok)} rows:")
        print(pd.crosstab(ok.sentiment_v5, ok.sentiment_v6).to_string())
        print(f"\nv5 Negative rate: {(ok.sentiment_v5 == 'Negative').mean():.4f}")
        print(f"v8 Negative rate: {(ok.sentiment_v6 == 'Negative').mean():.4f}")
        print(f"rows changed    : {(ok.sentiment_v5 != ok.sentiment_v6).sum()}")


def apply() -> None:
    if not STAGING.exists():
        raise SystemExit(f"no staging file: {STAGING}. Run --stage first.")

    staged = pd.read_csv(STAGING)
    staged = staged[staged.sentiment_v6.notna()]
    if staged.empty:
        raise SystemExit("staging file has no labelled rows")
    if len(staged) < len(_load_english()):
        missing = len(_load_english()) - len(staged)
        raise SystemExit(
            f"staging is incomplete: {missing} rows have no v8 label yet. "
            f"Re-run --stage until it reports 0 unlabelled rows before applying -- "
            f"applying a partial staging silently leaves those rows on v5."
        )

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
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None, help="stage only the first N rows")
    args = ap.parse_args()

    if args.stage:
        stage(args.workers, args.limit)
    elif args.apply:
        apply()
    else:
        raise SystemExit("pass --stage or --apply")


if __name__ == "__main__":
    main()
