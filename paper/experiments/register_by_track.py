#!/usr/bin/env python3
"""Loanword retention for all four non-English tracks, on the full test split.

`register_metrics.py` measures the two *native* tracks on the 150-row translation
sample, because that is what the MT comparison needs. The corpus documentation's
code-mixing claim is about the corpus, so this measures every non-English track on
all 3,079 test tickets.

CAVEAT, and it decides how the numbers are read. Retention asks whether an English
banking term from the source survives in Latin script in the target. On a
native-script track that is unambiguous: the term is either in English or it was
translated. On a *romanized* track everything is Latin by construction, so the
metric cannot separate "the English word was kept" from "a native phonetic
borrowing was romanized back to the same spelling". Romanized retention is
therefore an upper bound and is not comparable to a native track's figure. The
native pair (sinhala vs tamil) is the comparison that carries meaning.

Run:
    .venv312/bin/python paper/experiments/register_by_track.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from register_metrics import LOANWORDS, latin_fraction, retention  # noqa: E402

TRACKS = ["sinhala", "singlish", "tamil", "tamilish"]
NATIVE_SCRIPT = {"sinhala": True, "singlish": False, "tamil": True, "tamilish": False}
OUT = REPO / "paper" / "results" / "tables" / "register_by_track.csv"


def main() -> None:
    en = pd.read_csv(REPO / "datasets" / "english" / "test_labeled.csv")[["id", "text"]]
    rows = []
    for track in TRACKS:
        tgt = pd.read_csv(REPO / "datasets" / track / "test_labeled.csv")[["id", "text"]]
        m = en.merge(tgt, on="id", suffixes=("_en", "_tgt"))
        if len(m) != len(en):
            sys.exit(f"{track}: joined {len(m)} of {len(en)} ids -- ids are not aligned")
        micro, _ = retention(m["text_en"], m["text_tgt"])
        rows.append({
            "track": track,
            "native_script": NATIVE_SCRIPT[track],
            "loanword_retention": round(float(micro), 4),
            "latin_char_fraction": round(float(m["text_tgt"].map(latin_fraction).mean()), 4),
            "comparable": "yes" if NATIVE_SCRIPT[track] else "upper bound only",
            "n_rows": len(m),
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        fh.write(f"# English banking-loanword retention over a {len(LOANWORDS)}-term lexicon,\n"
                 "# full test split. Romanized tracks are Latin by construction, so their\n"
                 "# retention cannot separate a kept English word from a romanized native\n"
                 "# borrowing: read those as an upper bound, not against a native track.\n"
                 "# The sinhala-vs-tamil contrast is the one that carries meaning.\n"
                 "# generated_by=register_by_track.py\n")
        df.to_csv(fh, index=False)

    print(df.to_string(index=False))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
