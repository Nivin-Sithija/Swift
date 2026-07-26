#!/usr/bin/env python3
"""
Trilingual + romanized translation pipeline for the Swift banking-ticket
triage dataset.

Takes the English labeled CSVs (columns: text, category, sentiment, priority)
and produces ROW- and COLUMN-aligned datasets in four languages:

    sinhala   (si)  - Google Translate
    tamil     (ta)  - Google Translate
    singlish        - romanized Sinhala  (aksharamukha RomanColloquial)
    tamilish        - romanized Tamil    (aksharamukha RomanColloquial)

Only the `text` column is translated. `category`, `sentiment` and `priority`
are copied VERBATIM so labels stay aligned. An `id` column (0-based source
row index) is added to every output so cross-language rows can be joined and
alignment can be verified.

Engine: Google Translate via `deep-translator` (free web endpoint, no API key).
No paid LLM API is used.

Usage:
    # small curated sample (default 20 diverse rows of the test split)
    python gg_translate_generate.py --split test --sample 20 --suffix .sample

    # specific rows
    python gg_translate_generate.py --split test --ids 0,131,405,763 --suffix .demo

    # a full split (slow; free endpoint is rate-limited -> use --sleep, --resume)
    python gg_translate_generate.py --split test --sleep 0.6 --resume
    python gg_translate_generate.py --split train --sleep 0.6 --resume

    # only some languages
    python gg_translate_generate.py --split test --sample 20 --langs sinhala,singlish

Output layout: each language gets its own top-level folder directly under
datasets/ (e.g. datasets/sinhala/), with this script's output kept isolated
in a gg-translate-sample/ subfolder so it never collides with the real
hand-authored train_labeled.csv/test_labeled.csv in that folder.
"""
from __future__ import annotations
import argparse
import csv
import os
import sys
import time

from deep_translator import GoogleTranslator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romanize import romanize  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATASETS = os.path.dirname(HERE)
ENGLISH_DIR = os.path.join(DATASETS, "english")
OUT_ROOT = DATASETS

# our language label -> Google Translate target code
GT_CODE = {"sinhala": "si", "tamil": "ta"}
# romanized label -> native label it is derived from
ROMAN_SRC = {"singlish": "sinhala", "tamilish": "tamil"}
ALL_LANGS = ["sinhala", "tamil", "singlish", "tamilish"]
OUT_COLUMNS = ["id", "text", "category", "sentiment", "priority"]


# ----------------------------------------------------------------------------- IO
def read_english(split: str) -> list[dict]:
    path = os.path.join(ENGLISH_DIR, f"{split}_labeled.csv")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def out_path(lang: str, split: str, suffix: str) -> str:
    return os.path.join(OUT_ROOT, lang, "gg-translate-sample", f"{split}_labeled{suffix}.csv")


def rows_done(path: str) -> int:
    """Number of data rows already written (0 if file/header missing)."""
    if not os.path.exists(path):
        return 0
    with open(path, newline="", encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)


# --------------------------------------------------------------------- translate
def translate_retry(translator: GoogleTranslator, text: str, tries: int = 5) -> str:
    """Translate one string with exponential backoff on transient failures."""
    text = (text or "").strip()
    if not text:
        return text
    last = None
    for i in range(tries):
        try:
            out = translator.translate(text)
            if out:
                return out
            last = RuntimeError("empty result")
        except Exception as e:  # network / rate-limit / endpoint hiccups
            last = e
        time.sleep(min(2 ** i, 30))
    raise RuntimeError(f"translation failed after {tries} tries "
                       f"({text[:50]!r}): {last}")


def build(split: str, langs: list[str], ids: list[int] | None,
          sample: int | None, suffix: str, sleep: float, resume: bool) -> None:
    english = read_english(split)
    n_total = len(english)

    # which source rows to process
    if ids is not None:
        indices = [i for i in ids if 0 <= i < n_total]
    elif sample is not None:
        indices = pick_diverse(english, sample)
    else:
        indices = list(range(n_total))

    # native langs we must translate (romanized langs derive from these)
    native_needed = set()
    for lang in langs:
        native_needed.add(ROMAN_SRC.get(lang, lang))
    translators = {nl: GoogleTranslator(source="en", target=GT_CODE[nl])
                   for nl in native_needed if nl in GT_CODE}

    # prepare output files (+ resume)
    writers, files, start_at = {}, {}, 0
    if resume and ids is None:
        done_counts = [rows_done(out_path(l, split, suffix)) for l in langs]
        start_at = min(done_counts) if done_counts else 0
        if start_at:
            print(f"[resume] {min(done_counts)} rows already done; continuing")
    for lang in langs:
        p = out_path(lang, split, suffix)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        new_file = not (resume and os.path.exists(p) and start_at)
        f = open(p, "a" if not new_file else "w", newline="", encoding="utf-8")
        w = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        if new_file:
            w.writeheader()
        writers[lang], files[lang] = w, f

    work = indices[start_at:] if (resume and ids is None) else indices
    done = 0
    try:
        for src_idx in work:
            row = english[src_idx]
            base = {"category": row["category"],
                    "sentiment": row["sentiment"],
                    "priority": row["priority"]}
            # translate to needed native languages once
            native_text = {}
            for nl, tr in translators.items():
                native_text[nl] = translate_retry(tr, row["text"])
                if sleep:
                    time.sleep(sleep)
            # write each requested language
            for lang in langs:
                if lang in GT_CODE:
                    text = native_text[lang]
                else:  # romanized -> derive from its native source
                    text = romanize(native_text[ROMAN_SRC[lang]], lang)
                writers[lang].writerow({"id": src_idx, "text": text, **base})
                files[lang].flush()
            done += 1
            if done % 10 == 0 or done == len(work):
                print(f"  {done}/{len(work)} rows")
    finally:
        for f in files.values():
            f.close()

    print(f"[done] split={split} rows={done} langs={','.join(langs)}")
    for lang in langs:
        print(f"   -> {os.path.relpath(out_path(lang, split, suffix), DATASETS)}")


def pick_diverse(english: list[dict], k: int) -> list[int]:
    """Pick k rows spanning as many categories as possible (stable order)."""
    seen, picked = set(), []
    for i, row in enumerate(english):
        c = row["category"]
        if c not in seen:
            seen.add(c)
            picked.append(i)
        if len(picked) >= k:
            break
    if len(picked) < k:  # top up with earliest unused rows
        for i in range(len(english)):
            if i not in picked:
                picked.append(i)
            if len(picked) >= k:
                break
    return sorted(picked[:k])


# --------------------------------------------------------------------------- cli
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["train", "test"], default="test")
    ap.add_argument("--langs", default=",".join(ALL_LANGS),
                    help="comma list of: " + ",".join(ALL_LANGS))
    ap.add_argument("--ids", help="comma-separated source row indices (0-based)")
    ap.add_argument("--sample", type=int,
                    help="pick N diverse rows (one per category first)")
    ap.add_argument("--suffix", default="",
                    help="filename suffix, e.g. .sample -> test_labeled.sample.csv")
    ap.add_argument("--sleep", type=float, default=0.5,
                    help="seconds between translate calls (rate-limit safety)")
    ap.add_argument("--resume", action="store_true",
                    help="continue a partial run (aligns to min rows done)")
    args = ap.parse_args()

    langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    bad = [l for l in langs if l not in ALL_LANGS]
    if bad:
        ap.error(f"unknown langs: {bad}; choose from {ALL_LANGS}")
    ids = None
    if args.ids:
        ids = [int(x) for x in args.ids.split(",") if x.strip() != ""]

    build(args.split, langs, ids, args.sample, args.suffix, args.sleep, args.resume)


if __name__ == "__main__":
    main()
