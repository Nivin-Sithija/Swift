#!/usr/bin/env python3
"""
STEP 1 — Fix conflicting sentiment/priority labels (LLM).

A translation collapse can surface a v5 labeling inconsistency: two near-identical
English tickets in the SAME category translated to identical target text but were
given different sentiment/priority by the original v5 pass. This re-labels each
such conflict group as a UNIT with the v5 rules, forcing one consistent label for
the whole group, and propagates it to all five language files (labels are
id-aligned across languages).

Only same-category conflicts are touched. Groups whose category differs are
distinct intents that merely collapsed in translation — their differing labels
are correct; they are handled by the reword step, not here.

Usage:
    python fix_labeling.py --dry-run     # show what would change, no writes, no CSV delete
    python fix_labeling.py               # apply, then delete the conflicting-dup report CSV
"""
from __future__ import annotations

import argparse
from collections import defaultdict

import clean_common as cc


def same_category_conflict_groups() -> dict[str, list[frozenset]]:
    """Per split, the unique id-sets that share a text but conflict on
    sentiment/priority within one category. Deduped across languages."""
    out: dict[str, set[frozenset]] = defaultdict(set)
    for lang, split in cc.existing_splits():
        rows = cc.load_rows(lang, split)
        by_text = defaultdict(list)
        for r in rows:
            by_text[r["text"].strip()].append(r)
        for members in by_text.values():
            if len(members) < 2:
                continue
            cats = {m["category"] for m in members}
            labs = {(m["sentiment"], m["priority"]) for m in members}
            if len(cats) == 1 and len(labs) > 1:
                out[split].add(frozenset(m["id"] for m in members))
    return {s: sorted(v, key=lambda fs: sorted(fs)) for s, v in out.items()}


def build_prompt(base: str, category: str, tickets: list[tuple[str, str]]) -> str:
    lines = [base, "", "---", "",
             "The following tickets are near-duplicate customer messages in the "
             f"SAME category (`{category}`) — they should receive ONE consistent "
             "sentiment and priority. Apply the v5 rules above and return a SINGLE "
             "JSON object (no markdown, no prose) shaped exactly like "
             '{"sentiment": "Neutral"|"Negative", "priority": "Low"|"Medium"|"High"}.',
             ""]
    for tid, text in tickets:
        lines.append(f'[id={tid}] "{text.replace(chr(34), chr(39))}"')
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = cc.v5_prompt()
    groups_by_split = same_category_conflict_groups()
    n_groups = sum(len(v) for v in groups_by_split.values())
    print(f"same-category conflict groups to relabel: {n_groups}")

    grand_total = 0
    total_failed = 0
    for split, groups in groups_by_split.items():
        en = {r["id"]: r for r in cc.load_rows("english", split)}
        prompts, meta = [], []
        for ids in groups:
            ids = sorted(ids)
            cat = en[ids[0]]["category"]
            tickets = [(i, en[i]["text"]) for i in ids]
            prompts.append(build_prompt(base, cat, tickets))
            meta.append((ids, cat))

        updates: dict[str, dict] = {}
        n_failed = 0
        done = 0
        for idx, parsed in cc.run_batches(prompts, max_workers=4):
            done += 1
            ids, cat = meta[idx]
            if not isinstance(parsed, dict) or "sentiment" not in parsed:
                n_failed += 1
                print(f"  [{done}/{len(prompts)}] group {ids} FAILED — left unchanged")
                continue
            lab = {"sentiment": parsed["sentiment"], "priority": parsed["priority"]}
            for i in ids:
                old = (en[i]["sentiment"], en[i]["priority"])
                if (lab["sentiment"], lab["priority"]) != old:
                    updates[i] = lab
            print(f"  [{done}/{len(prompts)}] {cat}: ids {ids} -> {lab['sentiment']}/{lab['priority']}")

        if args.dry_run:
            print(f"  [{split}] DRY-RUN: {len(updates)} rows would change")
            continue
        changed = cc.apply_label_updates(split, updates)
        grand_total += changed
        total_failed += n_failed
        print(f"  [{split}] applied — {len(updates)} ids updated, {changed} cells rewritten "
              f"across all languages ({n_failed} groups failed, left as-is)")

    if not args.dry_run:
        remaining = same_category_conflict_groups()
        n_remaining = sum(len(v) for v in remaining.values())
        print(f"\nSTEP 1: {grand_total} label cells rewritten across languages; "
              f"{n_remaining} conflict groups still unresolved.")
        if n_remaining == 0:
            cc.delete_report("conflicting_label_duplicates.csv")
        else:
            print("  NOT deleting conflicting_label_duplicates.csv (stale, but re-run this "
                  "script to retry the remaining groups — it only touches unresolved ones).")


if __name__ == "__main__":
    main()
