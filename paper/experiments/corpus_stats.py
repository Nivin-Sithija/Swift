"""Corpus composition table -- the paper's Table 1.

A resource paper is judged on this table before any model result is read, so it
carries what a reader needs to decide whether the corpus is what it claims:
size, provenance, script, length, label distribution, and the two things most
corpus tables omit and reviewers ask for anyway --

**Script composition.** What fraction of characters in each track is actually in
the script the track is named after. This is the number that makes the tokenizer
finding legible: a tokenizer discarding 40.1% of Sinhala matters in proportion to
how much Sinhala there is.

**Code-mixing rate.** Sri Lankan bank customers write `card eka`, not a native
coinage, so the tracks are code-mixed by design. Measuring the Latin-script
fraction inside the native-script tracks states that as a number rather than a
claim.

Run:
    .venv312/bin/python paper/experiments/corpus_stats.py
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, data, splits  # noqa: E402

OUT = REPO / "paper" / "results" / "tables"

# Unicode block ranges, so "is this Sinhala" is answered by the standard rather
# than by a guess about which codepoints a translator emits.
BLOCKS = {
    "sinhala": [(0x0D80, 0x0DFF)],
    "tamil":   [(0x0B80, 0x0BFF)],
    "latin":   [(0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F)],
}

PROVENANCE = {
    "english":  "BANKING77 source, unmodified",
    # Provenance decides which track pairs are controlled comparisons and which are
    # not, so the wording here is load-bearing rather than descriptive.
    #
    # `singlish` is a deterministic rule-based romanisation OF the sinhala track, so
    # sinhala/singlish hold the same content and differ only in script. That is the
    # paper's controlled contrast.
    #
    # `tamilish` is NOT a romanisation of the tamil track. It was translated directly
    # from the BANKING77 English source, so tamil and tamilish are two independent
    # translations of one English original rather than one text in two scripts. They
    # must not be read as a script pair, and this also explains tamilish's 60.3%
    # out-of-vocabulary rate against its own train split and its high retention of
    # English banking terms (0.73 against tamil's 0.06).
    "sinhala":  "machine-translated, hand-corrected to colloquial code-mixed",
    "singlish": "rule-based romanisation of the Sinhala track",
    "tamil":    "machine-translated from the English source",
    "tamilish": "machine-translated from the English source, romanised",
}


def script_fraction(texts: pd.Series, block: str) -> float:
    """Share of letter characters falling in `block`. Punctuation and digits are
    excluded -- they are script-neutral and would dilute every track equally."""
    ranges = BLOCKS[block]
    total = hits = 0
    for t in texts:
        for ch in str(t):
            if not unicodedata.category(ch).startswith("L"):
                continue
            total += 1
            cp = ord(ch)
            if any(lo <= cp <= hi for lo, hi in ranges):
                hits += 1
    return hits / total if total else 0.0


def main() -> None:
    manifest = splits.ensure()
    print(f"split {manifest['sha']}  {manifest['counts']}")

    rows = []
    for lang in config.LANGUAGES:
        train = data.load_language(lang, "train")
        test = data.load_language(lang, "test")
        both = pd.concat([train, test], ignore_index=True)
        texts = both["text"].astype(str)

        native = "latin" if lang in ("english", "singlish", "tamilish") else lang
        rows.append({
            "track": lang,
            "provenance": PROVENANCE[lang],
            "script": "Latin" if native == "latin" else native.capitalize(),
            "train_rows": len(train),
            "test_rows": len(test),
            "unique_intents": int(both["category"].nunique()),
            "chars_per_ticket": round(texts.str.len().mean(), 1),
            "words_per_ticket": round(texts.str.split().str.len().mean(), 1),
            "pct_native_script": round(100 * script_fraction(texts, native), 2),
            "pct_latin_chars": round(100 * script_fraction(texts, "latin"), 2),
        })

    corpus = pd.DataFrame(rows)

    # Labels are id-identical across tracks, so one distribution describes all five.
    eng = pd.concat([data.load_language("english", "train"),
                     data.load_language("english", "test")], ignore_index=True)
    label_rows = []
    for task, col in (("sentiment", "sentiment"), ("priority", "priority")):
        counts = eng[col].value_counts()
        for label, n in counts.items():
            label_rows.append({"task": task, "label": label, "tickets": int(n),
                               "pct": round(100 * n / len(eng), 2)})
    label_rows.append({"task": "intent", "label": f"{eng['category'].nunique()} classes",
                       "tickets": len(eng), "pct": 100.0})
    labels = pd.DataFrame(label_rows)

    split_df = pd.DataFrame([{
        "portion": p, "tickets": manifest["counts"][p],
        "rows_all_tracks": manifest["counts"][p] * len(config.LANGUAGES),
    } for p in ("train", "dev", "test")])

    OUT.mkdir(parents=True, exist_ok=True)
    for name, df in (("corpus_composition", corpus), ("label_distribution", labels),
                     ("split_sizes", split_df)):
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n{name}:")
        print(df.to_string(index=False))

    print(f"\nwritten to {OUT.relative_to(REPO)}/")


if __name__ == "__main__":
    main()
