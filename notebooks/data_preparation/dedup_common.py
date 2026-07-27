#!/usr/bin/env python3
"""
Shared helpers for `dedup_banking77.ipynb` (STEP 2 — within-split duplicate
resolution). Kept out of the notebook so the notebook can stay a findings/
review surface while the mechanics are testable/importable code.

Two categories of within-language duplicate text (post STEP 1 label fix):

  TRUE DUPLICATE   — the underlying English ticket (`text_en`) is itself
                     duplicated. Provable directly against the untouched
                     `datasets/original-dataset/{train,test}.csv`, since `id`
                     is a 0-based row index into that file (verified 1:1,
                     0 mismatches). Not a translation artifact — remove the
                     redundant id from every language file.

  COLLAPSE         — two DIFFERENT English tickets translated to identical
                     target-language text. A real translation-side event
                     (near-identical phrasing colliding), not a BANKING77
                     duplicate. Fix by rewording the target text so the two
                     tickets read distinctly again, via `claude -p`.
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict

import clean_common as cc

ORIG_DIR = os.path.join(cc.DATASETS, "original-dataset")
STYLE_GUIDE = os.path.join(cc.DATASETS, "translation", "SINHALA_STYLE.md")


# --------------------------------------------------------------- original-file proof
def load_original(split: str) -> list[dict]:
    with open(os.path.join(ORIG_DIR, f"{split}.csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def verify_id_alignment(split: str) -> bool:
    """Confirm `id` in english/{split}_labeled.csv is a 0-based index into the
    untouched original-dataset file (the basis for the true-dup proof)."""
    orig = load_original(split)
    en = cc.load_rows("english", split)
    return all(orig[int(r["id"])]["text"].strip() == r["text_en"].strip() for r in en)


# --------------------------------------------------------------------- categorize
def true_duplicate_groups(split: str) -> list[list[str]]:
    """
    Groups of ids whose source text is identical — a genuine BANKING77 source
    duplicate, not ours to blame. Sourced from the UNTOUCHED
    `original-dataset/{split}.csv` (id == 0-based row index, verified) rather
    than the mutable per-language CSVs, so this stays correct and reproducible
    even after Action A has already dropped the redundant ids elsewhere.
    """
    orig = load_original(split)
    by_text = defaultdict(list)
    for i, r in enumerate(orig):
        by_text[r["text"].strip()].append(str(i))
    return [ids for ids in by_text.values() if len(ids) > 1]


def true_dup_drop_ids(split: str) -> set[str]:
    """Ids to remove (keep the lowest id per true-dup group)."""
    drop = set()
    for ids in true_duplicate_groups(split):
        ids_sorted = sorted(ids, key=int)
        drop.update(ids_sorted[1:])
    return drop


def collapse_groups(lang: str, split: str) -> list[dict]:
    """
    Within `lang`'s current text, groups of ids sharing identical text whose
    text_en DIFFERS (i.e. NOT a true duplicate) — translation collapses that
    need rewording. Excludes any id already marked for removal as a true dup.
    """
    rows = cc.load_rows(lang, split)
    drop = true_dup_drop_ids(split)
    by_text = defaultdict(list)
    for r in rows:
        if r["id"] in drop:
            continue
        by_text[r["text"].strip()].append(r)
    out = []
    for text, members in by_text.items():
        if len(members) < 2:
            continue
        if len({m["text_en"].strip() for m in members}) > 1:
            out.append({"lang": lang, "split": split, "text": text, "members": members})
    return out


# ------------------------------------------------------------------- action A: drop
def apply_true_dup_removal(dry_run: bool = True) -> dict[str, int]:
    """Drop the redundant ids (keep-lowest) from EVERY language file, both splits."""
    result = {}
    for split in ("train", "test"):
        drop = true_dup_drop_ids(split)
        if not drop:
            result[split] = 0
            continue
        if not dry_run:
            for lang in cc.LANGS:
                if not os.path.exists(cc.path(lang, split)):
                    continue
                rows = cc.load_rows(lang, split)
                kept = [r for r in rows if r["id"] not in drop]
                cc.save_rows(lang, split, kept)
        result[split] = len(drop)
    return result


# --------------------------------------------------------------- action B: reword
REWORD_SYSTEM = """\
You are fixing a trilingual (English source -> Sinhala/Tamil target) banking-support
ticket dataset. Two DIFFERENT English tickets were independently translated and ended
up with the IDENTICAL {lang_name} text below, which is wrong -- the dataset needs one
row per ticket to read distinctly, in this dataset's established colloquial register.

{style_note}

Given the tickets below (same current {lang_name} text, different English originals),
rewrite the {lang_name} text for EACH ticket so it accurately, naturally translates its
OWN English original and reads distinctly from the others -- do not just paraphrase
randomly, translate what that specific English ticket actually says.

Return ONLY a JSON array, no markdown fences, one object per ticket in the given order,
shaped exactly like {{"id": <id>, "text": "<new {lang_name} text>"}}.
"""

SI_STYLE_NOTE = ("Style: colloquial, code-mixed spoken Sinhala (address the bank as "
                 "ඔයාලා, keep English banking terms in Sinhala script e.g. කාඩ් එක, "
                 "පේමන්ට් එක -- see datasets/translation/SINHALA_STYLE.md for the full "
                 "glossary/register guide).")
TA_STYLE_NOTE = ("Style: colloquial spoken Tamil as used in a banking support chat, "
                 "keeping common English banking terms (card, PIN, OTP, transfer, app, "
                 "account) in Tamil script the way a Sri Lankan Tamil customer would "
                 "actually type them.")

LANG_NAME = {"sinhala": "Sinhala", "tamil": "Tamil"}
STYLE_NOTE = {"sinhala": SI_STYLE_NOTE, "tamil": TA_STYLE_NOTE}


def build_reword_prompt(lang: str, members: list[dict]) -> str:
    header = REWORD_SYSTEM.format(lang_name=LANG_NAME[lang], style_note=STYLE_NOTE[lang])
    lines = [header, ""]
    for m in members:
        lines.append(f'[id={m["id"]}] english="{m["text_en"]}" current_{lang}="{m["text"]}"')
    return "\n".join(lines)


def reword_groups(lang: str, groups: list[dict], max_workers: int = 4):
    """Run the reword LLM call for each collapse group. Yields (group, result_or_None)."""
    prompts = [build_reword_prompt(lang, g["members"]) for g in groups]
    results = [None] * len(groups)
    for idx, parsed in cc.run_batches(prompts, max_workers=max_workers):
        results[idx] = parsed
    for g, r in zip(groups, results):
        yield g, r


def apply_reword_results(lang: str, split: str, groups: list[dict], results: list) -> int:
    """Write new text per id for successfully reworded groups. Returns rows changed."""
    updates: dict[str, str] = {}
    for g, parsed in zip(groups, results):
        if not isinstance(parsed, list):
            continue
        by_id = {str(item["id"]): item["text"] for item in parsed if "id" in item and "text" in item}
        expected_ids = {m["id"] for m in g["members"]}
        if set(by_id) != expected_ids:
            continue  # malformed/partial response -- skip, leave original text
        updates.update(by_id)

    if not updates:
        return 0
    rows = cc.load_rows(lang, split)
    changed = 0
    for r in rows:
        if r["id"] in updates and r["text"] != updates[r["id"]]:
            r["text"] = updates[r["id"]]
            changed += 1
    cc.save_rows(lang, split, rows)
    return changed
