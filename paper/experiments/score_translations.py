"""Reference-free automatic scoring for the translation comparison.

Every metric here scores a translation against its **English source**. None uses
a reference translation, because the only candidate reference available is our
own output, and scoring competitors against it measures similarity to us rather
than quality. That experiment cannot support the claim it appears to support.

Metrics
-------
**LaBSE cross-lingual cosine** (always available). LaBSE embeds 109 languages
including Sinhala and Tamil into one space, so the cosine between the English
source and a candidate translation is a direct semantic-preservation signal. The
project already depends on LaBSE, so this adds nothing to the stack.

**COMET-Kiwi** (optional, `pip install unbabel-comet`). Purpose-built
reference-free MT quality estimation and the metric an MT reviewer will look for.
Skipped with a clear message when not installed, rather than failing the run.

**Script fidelity** (always available). The share of letters in the expected
script. Catches a failure mode the semantic metrics miss entirely: a system that
answers in English, transliterates instead of translating, or emits a refusal.
A candidate with high cosine and 0% target script is not a translation.

Run:
    .venv312/bin/python paper/experiments/score_translations.py
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

TE = REPO / "paper" / "translation_eval"
SAMPLES, SYSTEMS = TE / "samples", TE / "systems"
OUT = REPO / "paper" / "results" / "tables"

LANGS = ["sinhala", "tamil"]
EXTERNAL = ["google", "openai", "gptoss"]
BLOCKS = {"sinhala": [(0x0D80, 0x0DFF)], "tamil": [(0x0B80, 0x0BFF)]}


def script_fraction(text: str, lang: str) -> float:
    ranges = BLOCKS[lang]
    letters = [c for c in str(text) if unicodedata.category(c).startswith("L")]
    if not letters:
        return 0.0
    return sum(any(lo <= ord(c) <= hi for lo, hi in ranges) for c in letters) / len(letters)


def collect(lang: str) -> pd.DataFrame:
    sample = pd.read_csv(SAMPLES / "sample_ids.csv")
    rows = [{"id": r.id, "source_en": r.text_en, "system": "swift",
             "translation": getattr(r, f"swift_{lang}")} for r in sample.itertuples(index=False)]
    for name in EXTERNAL:
        path = SYSTEMS / f"{name}_{lang}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path).merge(sample[["id", "text_en"]], on="id", how="right")
        rows += [{"id": r.id, "source_en": r.text_en, "system": name,
                  "translation": r.translation} for r in df.itertuples(index=False)]
    return pd.DataFrame(rows)


def labse_cosine(df: pd.DataFrame, batch: int = 64) -> np.ndarray:
    import torch
    from transformers import AutoModel, AutoTokenizer

    name = "sentence-transformers/LaBSE"
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModel.from_pretrained(name).eval()

    def embed(texts):
        out = []
        for i in range(0, len(texts), batch):
            enc = tok([str(t) for t in texts[i:i + batch]], padding=True,
                      truncation=True, max_length=128, return_tensors="pt")
            with torch.no_grad():
                # LaBSE's sentence vector is the pooler output, not mean-pooling --
                # its dual-encoder objective was trained on exactly that head.
                v = model(**enc).pooler_output
            out.append(torch.nn.functional.normalize(v, dim=1))
        return torch.cat(out)

    src = embed(df["source_en"].tolist())
    tgt = embed(df["translation"].tolist())
    return (src * tgt).sum(1).numpy()


def comet_kiwi(df: pd.DataFrame) -> np.ndarray | None:
    try:
        from comet import download_model, load_from_checkpoint
    except ImportError:
        print("  COMET-Kiwi skipped -- `pip install unbabel-comet` to enable")
        return None
    path = download_model("Unbabel/wmt22-cometkiwi-da")
    model = load_from_checkpoint(path)
    data = [{"src": str(s), "mt": str(t)}
            for s, t in zip(df["source_en"], df["translation"])]
    return np.asarray(model.predict(data, batch_size=32, gpus=0).scores)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-labse", action="store_true")
    ap.add_argument("--comet", action="store_true", help="also run COMET-Kiwi (slow)")
    args = ap.parse_args()

    frames = []
    for lang in LANGS:
        df = collect(lang)
        present = sorted(df["system"].unique())
        print(f"{lang}: {len(present)} system(s) -> {', '.join(present)}")
        if len(present) < 2:
            print("  need at least 2 systems to compare, skipped\n")
            continue

        df["language"] = lang
        df["script_fidelity"] = [script_fraction(t, lang) for t in df["translation"]]
        df["empty"] = df["translation"].isna() | (df["translation"].astype(str).str.strip() == "")

        if not args.no_labse:
            try:
                df["labse_cosine"] = labse_cosine(df)
            except Exception as e:  # noqa: BLE001
                print(f"  LaBSE unavailable ({type(e).__name__}); continuing without it")
        if args.comet:
            s = comet_kiwi(df)
            if s is not None:
                df["comet_kiwi"] = s
        frames.append(df)
        print()

    if not frames:
        print("Nothing scored. Put system outputs in "
              f"{SYSTEMS.relative_to(REPO)}/ first -- see paper/TRACKER.md task B2.")
        return

    long = pd.concat(frames, ignore_index=True)
    metric_cols = [c for c in ("labse_cosine", "comet_kiwi", "script_fidelity")
                   if c in long.columns]
    summary = (long.groupby(["language", "system"])
               .agg(n=("id", "count"), missing=("empty", "sum"),
                    **{c: (c, "mean") for c in metric_cols})
               .round(4).reset_index())

    OUT.mkdir(parents=True, exist_ok=True)
    long.to_csv(OUT / "translation_auto_long.csv", index=False)
    summary.to_csv(OUT / "translation_auto.csv", index=False)
    print(summary.to_string(index=False))
    print(f"\nwritten to {OUT.relative_to(REPO)}/")
    print("These are supporting evidence. The headline claim rests on the blind "
          "human ratings (build_rating_sheets.py).")


if __name__ == "__main__":
    main()
