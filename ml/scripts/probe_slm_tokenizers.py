#!/usr/bin/env python
"""Tokenizer-fertility screen for the SLM candidates in `ml/reports/SLM_RESEARCH.md` §5.

This is Step 0 of that document's plan and it runs on CPU in minutes: a candidate whose Sinhala or
Tamil fertility is far above LaBSE's is shredding the input before the model ever sees it, and no
amount of GPU time fixes that. Dropping a model here costs nothing; discovering it after a 4-hour
T4 run costs a fifth of the weekly budget.

Mirrors the probe in `notebooks/modeling/07_encoder_bakeoff.ipynb` §1 -- same 2,000-row stratified
sample, same fertility definition -- so the numbers append to `encoder_tokenizer_fertility.csv`
and are directly comparable to the encoder roster already in it.

Two additions the encoder probe did not need:

- **Character preservation.** `sentiment-priority-test-results` records 40.1% of Sinhala and 69.3%
  of Tamil characters being silently discarded by a tokenizer that raised no error and produced
  plausible metrics. Decoder tokenizers are byte-BPE and structurally cannot emit `[UNK]`, so the
  UNK column is meaningless for them (all six encoders already showed a meaningless 0%). Round-trip
  decoding is the check that actually bites.
- **ZWJ survival.** `research/README.md` §3.19.3 flags U+200D as the recurring Sinhala gotcha; a
  tokenizer that splits `ට්‍රැක්` at the ZWJ breaks the word. Tested explicitly.

    .venv312/bin/python ml/scripts/probe_slm_tokenizers.py
"""
from __future__ import annotations

import os
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
os.environ.setdefault("SWIFT_REPO_ROOT", str(REPO))
sys.path.insert(0, str(REPO / "ml"))

import swiftbench as sb  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402

SAMPLE_N = 2000

# short name -> (hf checkpoint, note). LaBSE is the incumbent and the bar every candidate is
# measured against, so it is re-measured here rather than read from the old CSV -- same tokenizer
# library version, same sample, no cross-run drift.
CANDIDATES: dict[str, tuple[str, str]] = {
    "labse":            ("sentence-transformers/LaBSE",   "incumbent champion -- the bar"),
    "qwen3-emb-0.6b":   ("Qwen/Qwen3-Embedding-0.6B",     "tier A: decoder backbone, encoder interface"),
    "qwen3-0.6b":       ("Qwen/Qwen3-0.6B",               "same tokenizer family, causal LM"),
    "qwen3-1.7b":       ("Qwen/Qwen3-1.7B",               "tier B"),
    # Unsloth mirrors, not the `google/`+`meta-llama/` originals: those are gated behind a licence
    # click, which a Kaggle kernel cannot do without a stored HF token. The mirrors carry identical
    # vocabularies (262,145 / 128,256) and weights, so nothing is given up by using them, and the
    # same checkpoint string then works unchanged in the kernel.
    "gemma-3-1b":       ("unsloth/gemma-3-1b-pt",         "tier A: on the 1B knee, best Indic fertility"),
    "gemma-3-270m":     ("unsloth/gemma-3-270m",          "below the knee; tokenizer measured for reference"),
    "llama-3.2-1b":     ("unsloth/Llama-3.2-1B",          "tier B: the causal-LLM paper's family"),
    "sinllama":         ("polyglots/SinLlama_v01",        "tier C: Sinhala-extended Llama-3 vocab"),
}

# The ZWJ case from research/README.md §3.19.3 -- "track", which renders correctly only if the
# U+200D between ට් and ර survives tokenization.
ZWJ_PROBES = ["ට්‍රැක්", "ශ්‍රී ලංකා", "කාඩ්‍ පත"]


def char_preservation(tok, texts: list[str]) -> float:
    """Fraction of input characters that survive an encode->decode round trip.

    Compared on NFC-normalised, whitespace-stripped multisets so that a tokenizer is not penalised
    for regularising spacing. Combining marks (Unicode Mn/Mc) are what actually go missing in the
    Indic failure mode, and they are counted here like any other character.
    """
    kept = total = 0
    for t in texts:
        ids = tok(t, add_special_tokens=False)["input_ids"]
        back = tok.decode(ids, skip_special_tokens=True)
        a = [c for c in unicodedata.normalize("NFC", t) if not c.isspace()]
        b = [c for c in unicodedata.normalize("NFC", back) if not c.isspace()]
        bag = {}
        for c in b:
            bag[c] = bag.get(c, 0) + 1
        for c in a:
            if bag.get(c, 0) > 0:
                bag[c] -= 1
                kept += 1
        total += len(a)
    return round(kept / max(total, 1), 4)


def mark_preservation(tok, texts: list[str]) -> float:
    """Same round trip, restricted to combining marks -- the class that was silently dropped before."""
    kept = total = 0
    for t in texts:
        ids = tok(t, add_special_tokens=False)["input_ids"]
        back = tok.decode(ids, skip_special_tokens=True)
        a = [c for c in unicodedata.normalize("NFC", t) if unicodedata.category(c) in ("Mn", "Mc")]
        b = [c for c in unicodedata.normalize("NFC", back) if unicodedata.category(c) in ("Mn", "Mc")]
        bag = {}
        for c in b:
            bag[c] = bag.get(c, 0) + 1
        for c in a:
            if bag.get(c, 0) > 0:
                bag[c] -= 1
                kept += 1
        total += len(a)
    return round(kept / max(total, 1), 4) if total else float("nan")


def zwj_survives(tok) -> bool:
    """Does U+200D come back out of a round trip on all three probes?"""
    for p in ZWJ_PROBES:
        if "‍" not in p:
            continue
        back = tok.decode(tok(p, add_special_tokens=False)["input_ids"], skip_special_tokens=True)
        if "‍" not in back:
            return False
    return True


def main() -> int:
    samples = {}
    for lang in sb.config.LANGUAGES:
        df = sb.splits.get([lang], "train")
        samples[lang] = df.text.sample(min(SAMPLE_N, len(df)), random_state=42).tolist()
    print(f"sample: {SAMPLE_N} rows x {len(samples)} languages, split {sb.splits.sha()}\n")

    rows, skipped = [], []
    for short, (name, note) in CANDIDATES.items():
        try:
            tok = AutoTokenizer.from_pretrained(name)
        except Exception as exc:
            reason = f"{type(exc).__name__}: {str(exc).splitlines()[0][:90]}"
            print(f"{short:16s} SKIP  {reason}")
            skipped.append({"model": short, "checkpoint": name, "reason": reason})
            continue
        unk_id = tok.unk_token_id
        zwj = zwj_survives(tok)
        for lang, texts in samples.items():
            enc = tok(texts, add_special_tokens=False)["input_ids"]
            n_tok = np.array([len(e) for e in enc])
            n_word = np.array([max(len(t.split()), 1) for t in texts])
            unk = (sum(sum(1 for i in e if i == unk_id) for e in enc)
                   if unk_id is not None else 0)
            sub = texts[:300]   # round trips are slow; 300 rows is plenty to catch a systematic drop
            rows.append({
                "model": short, "checkpoint": name, "language": lang,
                "fertility": round(float((n_tok / n_word).mean()), 3),
                "mean_tokens": round(float(n_tok.mean()), 1),
                "p99_tokens": int(np.percentile(n_tok, 99)),
                "unk_pct": round(100 * unk / max(n_tok.sum(), 1), 3),
                "char_kept": char_preservation(tok, sub),
                "mark_kept": mark_preservation(tok, sub),
                "zwj_ok": zwj,
                "vocab_size": len(tok),
            })
        print(f"{short:16s} done  ({note})")

    fert = pd.DataFrame(rows)
    out = REPO / "ml" / "reports" / "slm_tokenizer_fertility.csv"
    fert.to_csv(out, index=False)
    if skipped:
        pd.DataFrame(skipped).to_csv(
            REPO / "ml" / "reports" / "slm_tokenizer_skipped.csv", index=False)

    print("\n--- fertility (subword tokens per whitespace word) ---")
    piv = fert.pivot_table(index="model", columns="language", values="fertility")
    print(piv.to_string())

    print("\n--- character preservation (round trip; 1.0 = nothing dropped) ---")
    print(fert.pivot_table(index="model", columns="language", values="char_kept").to_string())

    print("\n--- combining-mark preservation (Mn/Mc only -- the silent Indic failure) ---")
    print(fert.pivot_table(index="model", columns="language", values="mark_kept").to_string())

    # The gate from SLM_RESEARCH.md §6: >1.5x LaBSE on Sinhala or Tamil and the candidate is
    # dropped before it ever costs a GPU hour.
    if "labse" in piv.index:
        print("\n--- gate: Sinhala/Tamil fertility vs LaBSE ---")
        for m in piv.index:
            if m == "labse":
                continue
            ratios = {l: piv.loc[m, l] / piv.loc["labse", l] for l in ("sinhala", "tamil")
                      if l in piv.columns}
            worst = max(ratios.values())
            verdict = "PASS" if worst <= 1.5 else "DROP"
            detail = "  ".join(f"{l} {r:.2f}x" for l, r in ratios.items())
            print(f"  {m:16s} {detail}   -> {verdict}")

    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
