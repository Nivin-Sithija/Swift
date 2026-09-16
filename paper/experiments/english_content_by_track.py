#!/usr/bin/env python3
"""How much of each track is literally English, measured in words rather than characters.

`corpus_stats.py` reports a Latin *character* fraction. That conflates two very
different things on a romanized track, where every character is Latin by
construction whether the underlying word is English or a transliterated native
word. This measures words, and separates them:

  latin_token_pct     tokens containing a Latin letter
  english_token_pct   tokens that are also words of the BANKING77 English source

On a native-script track the two coincide, and the second is the honest measure of
how much English survived translation. On a romanized track they diverge sharply,
and `english_token_pct` is the one that means anything.

CAVEAT on romanized tracks: a transliterated native word can collide with an
English string by accident ("eka", "mata"), so `english_token_pct` there is a
slight over-count rather than an exact figure.

`latin_types` is reported because it is diagnostic rather than descriptive: two
tracks rendering the same 3,079 tickets at the same length should need comparable
vocabularies, and a track that needs three times as many is not a stable
rendering.

Run:
    .venv312/bin/python paper/experiments/english_content_by_track.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
TRACKS = ["english", "sinhala", "singlish", "tamil", "tamilish"]
OUT = REPO / "paper" / "results" / "tables" / "english_content_by_track.csv"
WORD = re.compile(r"[A-Za-z']+")
HAS_LATIN = re.compile(r"[A-Za-z]")


def english_vocabulary() -> set[str]:
    """Every word type of the English source track, lowercased."""
    en = pd.read_csv(REPO / "datasets" / "english" / "test_labeled.csv")
    return {w.lower() for text in en["text"] for w in WORD.findall(str(text))}


def main() -> None:
    vocab = english_vocabulary()
    rows = []
    for track in TRACKS:
        df = pd.read_csv(REPO / "datasets" / track / "test_labeled.csv")
        tokens = latin = english = 0
        latin_types: set[str] = set()
        for text in df["text"]:
            for tok in str(text).split():
                tokens += 1
                if HAS_LATIN.search(tok):
                    latin += 1
                    stem = re.sub(r"[^A-Za-z']", "", tok).lower()
                    latin_types.add(stem)
                    if stem in vocab:
                        english += 1
        rows.append({
            "track": track,
            "tokens_per_ticket": round(tokens / len(df), 2),
            "latin_token_pct": round(100 * latin / tokens, 1),
            "english_token_pct": round(100 * english / tokens, 1),
            "latin_types": len(latin_types),
            "n_tickets": len(df),
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        fh.write("# English content per track, test split, measured in word tokens.\n"
                 "# english_token_pct = tokens that are also words of the BANKING77 source.\n"
                 "# On romanized tracks every token is Latin by construction, so read\n"
                 "# english_token_pct rather than latin_token_pct there; it is a slight\n"
                 "# over-count, since a transliterated native word can collide with an\n"
                 "# English string. latin_types is diagnostic: tracks rendering the same\n"
                 "# tickets at the same length should need comparable vocabularies.\n"
                 "# generated_by=english_content_by_track.py\n")
        df.to_csv(fh, index=False)

    print(df.to_string(index=False))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
