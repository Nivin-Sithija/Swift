"""Where does the encoder's advantage over classical actually come from?

The pooled comparison says LaBSE beats the classical champion by +0.0485 Negative-F1
(significant, CI clear of zero). Pooled numbers hide where a gain lives, and this one is not
spread evenly: LaBSE gains ~8 points on English and Sinhala and ~1-2 points on the two
romanized tracks.

That split lines up with pretraining rather than with language. LaBSE saw native-script
Sinhala and Tamil; it did not see Sinhala or Tamil written in Latin characters with English
function words mixed in, which is what the `singlish` and `tamilish` tracks are. So the
hypothesis under test is:

    the encoder's advantage is a function of whether the *script* was in pretraining,
    not of which language the ticket is in

`sinhala` and `singlish` are the decisive pair, because they are the **same tickets in the
same language**, differing only in script. Any gain difference between them cannot be a
language effect, a topic effect, or a sampling effect -- the ids are identical.

Each track's gain is tested with a paired bootstrap over ticket ids, so the two systems are
compared on exactly the same rows.

Run:
    .venv312/bin/python paper/experiments/encoder_gain_by_script.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from significance import _headline_from_counts  # noqa: E402
from swiftbench import config, metrics  # noqa: E402

OUT = REPO / "paper" / "results" / "tables"
PRED_DIR = config.PREDICTIONS_DIR / "runs"
RESAMPLES = 1000
TASK = "sentiment"

ENCODER = "labse"
CLASSICAL = "tfidf-svm"

# Which tracks were written in a script LaBSE saw during pretraining. The romanized tracks are
# Latin characters, but they are not English -- they are Sinhala/Tamil transliterated, which no
# pretraining corpus of consequence contains.
NATIVE_SCRIPT = {"english": True, "sinhala": True, "tamil": True,
                 "singlish": False, "tamilish": False}


def load(model: str) -> pd.DataFrame:
    hits = sorted(PRED_DIR.glob(f"{TASK}__{model}__*__ev-all__*__test.csv"))
    if not hits:
        sys.exit(f"no test predictions for {model} -- expected one in {PRED_DIR}")
    df = pd.read_csv(hits[0])
    if "language" not in df.columns:
        sys.exit(f"{hits[0].name} has no language column")
    return df


def paired_delta(a: pd.DataFrame, b: pd.DataFrame, seed: int = config.RANDOM_STATE) -> dict:
    """b - a on the headline metric, resampling ticket ids. a and b cover the same ids."""
    m = a.merge(b, on="id", suffixes=("_a", "_b"))
    assert (m["y_true_a"] == m["y_true_b"]).all(), "same ids must carry the same gold label"

    classes = sorted(set(m["y_true_a"]) | set(m["y_pred_a"]) | set(m["y_pred_b"]))
    lut = {c: i for i, c in enumerate(classes)}
    k = len(classes)
    yt = np.array([lut[v] for v in m["y_true_a"]])
    ia = yt * k + np.array([lut[v] for v in m["y_pred_a"]])
    ib = yt * k + np.array([lut[v] for v in m["y_pred_b"]])
    pos = lut.get(config.SENTIMENT_POSITIVE_CLASS)

    obs = (metrics.score(m["y_true_b"], m["y_pred_b"], TASK)["headline"]
           - metrics.score(m["y_true_a"], m["y_pred_a"], TASK)["headline"])

    rng = np.random.default_rng(seed)
    n = len(m)
    deltas = np.empty(RESAMPLES)
    for i in range(RESAMPLES):
        idx = rng.integers(0, n, size=n)
        deltas[i] = (_headline_from_counts(np.bincount(ib[idx], minlength=k * k).reshape(k, k),
                                           TASK, pos)
                     - _headline_from_counts(np.bincount(ia[idx], minlength=k * k).reshape(k, k),
                                             TASK, pos))
    p = 2 * (np.mean(deltas >= 0) if obs < 0 else np.mean(deltas <= 0))
    return {"gain": round(float(obs), 4),
            "ci_low": round(float(np.percentile(deltas, 2.5)), 4),
            "ci_high": round(float(np.percentile(deltas, 97.5)), 4),
            "p": round(float(min(p, 1.0)), 4),
            "n": n}


def diff_in_diff(enc: pd.DataFrame, cls: pd.DataFrame, native: str, roman: str,
                 seed: int = config.RANDOM_STATE) -> dict:
    """(encoder gain on `native`) minus (encoder gain on `roman`), with a CI.

    All four cells are the same tickets -- the split fans one ticket id into five language
    tracks -- so a single resample of ticket ids drives every cell together and the
    correlation between them is preserved. Resampling the tracks independently would inflate
    the variance and understate the contrast.
    """
    def cell(df: pd.DataFrame, track: str) -> pd.DataFrame:
        return (df[df["language"] == track][["id", "y_true", "y_pred"]]
                .set_index("id").sort_index())

    cells = {(sys_, tr): cell(df, tr)
             for sys_, df in (("enc", enc), ("cls", cls))
             for tr in (native, roman)}
    ids = sorted(set.intersection(*(set(c.index) for c in cells.values())))
    cells = {k: v.loc[ids] for k, v in cells.items()}

    classes = sorted({v for c in cells.values() for v in c["y_true"]}
                     | {v for c in cells.values() for v in c["y_pred"]})
    lut = {c: i for i, c in enumerate(classes)}
    k = len(classes)
    pos = lut.get(config.SENTIMENT_POSITIVE_CLASS)
    flat = {key: (np.array([lut[v] for v in c["y_true"]]) * k
                  + np.array([lut[v] for v in c["y_pred"]])) for key, c in cells.items()}

    def headline(key, idx):
        return _headline_from_counts(
            np.bincount(flat[key][idx], minlength=k * k).reshape(k, k), TASK, pos)

    whole = np.arange(len(ids))
    obs = ((headline(("enc", native), whole) - headline(("cls", native), whole))
           - (headline(("enc", roman), whole) - headline(("cls", roman), whole)))

    rng = np.random.default_rng(seed)
    draws = np.empty(RESAMPLES)
    for i in range(RESAMPLES):
        idx = rng.integers(0, len(ids), size=len(ids))
        draws[i] = ((headline(("enc", native), idx) - headline(("cls", native), idx))
                    - (headline(("enc", roman), idx) - headline(("cls", roman), idx)))
    p = 2 * (np.mean(draws >= 0) if obs < 0 else np.mean(draws <= 0))
    return {"did": round(float(obs), 4),
            "ci_low": round(float(np.percentile(draws, 2.5)), 4),
            "ci_high": round(float(np.percentile(draws, 97.5)), 4),
            "p": round(float(min(p, 1.0)), 4), "n": len(ids)}


def main() -> None:
    enc, cls = load(ENCODER), load(CLASSICAL)

    rows = []
    for track in ["english", "sinhala", "tamil", "singlish", "tamilish"]:
        a = cls[cls["language"] == track][["id", "y_true", "y_pred"]]
        b = enc[enc["language"] == track][["id", "y_true", "y_pred"]]
        if a.empty or b.empty:
            continue
        r = {"track": track, "native_script": NATIVE_SCRIPT[track],
             "classical": round(metrics.score(a["y_true"], a["y_pred"], TASK)["headline"], 4),
             "encoder": round(metrics.score(b["y_true"], b["y_pred"], TASK)["headline"], 4)}
        r.update(paired_delta(a, b))
        r["significant_05"] = bool(r["p"] < 0.05)
        rows.append(r)

    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "encoder_gain_by_script.csv", index=False)

    print(f"{ENCODER} minus {CLASSICAL}, {TASK} test, paired within each track\n")
    print(df[["track", "native_script", "classical", "encoder", "gain",
              "ci_low", "ci_high", "p", "significant_05"]].to_string(index=False))

    nat = df[df["native_script"]]["gain"]
    rom = df[~df["native_script"]]["gain"]
    print(f"\nmean gain, native-script tracks   : {nat.mean():+.4f}  (n={len(nat)})")
    print(f"mean gain, romanized tracks       : {rom.mean():+.4f}  (n={len(rom)})")

    # The decisive within-language pair: same tickets, same language, different script.
    #
    # This MUST be tested as a difference of differences. "Significant on sinhala, not
    # significant on singlish" is not evidence that the two gains differ -- the difference
    # between significant and non-significant is not itself significant (Gelman & Stern).
    # Reading the two p-values as a contrast is the error this block exists to avoid.
    for native, roman in (("sinhala", "singlish"), ("tamil", "tamilish")):
        if not {native, roman} <= set(df["track"]):
            continue
        did = diff_in_diff(enc, cls, native, roman)
        g_n = float(df.loc[df["track"] == native, "gain"].iloc[0])
        g_r = float(df.loc[df["track"] == roman, "gain"].iloc[0])
        print(f"\n{native} vs {roman} -- same tickets, same language, different script")
        print(f"  encoder gain, native script  {g_n:+.4f}")
        print(f"  encoder gain, romanized      {g_r:+.4f}")
        print(f"  difference of differences    {did['did']:+.4f} "
              f"CI [{did['ci_low']:+.4f}, {did['ci_high']:+.4f}] p={did['p']:.4f}"
              f"  {'SIGNIFICANT' if did['p'] < 0.05 else 'not significant'}")
        rows.append({"track": f"{native}-minus-{roman}", "native_script": None,
                     "classical": None, "encoder": None, "gain": did["did"],
                     "ci_low": did["ci_low"], "ci_high": did["ci_high"], "p": did["p"],
                     "n": did["n"], "significant_05": bool(did["p"] < 0.05)})
        df = pd.DataFrame(rows)
        df.to_csv(OUT / "encoder_gain_by_script.csv", index=False)

    print("\nCAUTION: 5 tracks is 5 points. The native/romanized means are a description of\n"
          "those 5, not a fitted effect. The within-language script pairs above are the\n"
          "load-bearing evidence, because they hold language and tickets fixed and vary\n"
          "only script -- and they are tested as a contrast, not by comparing two p-values.")
    print("\nAND THE TWO PAIRS ARE NOT EQUIVALENT. `corpus_stats.py` measured the *native*\n"
          "tracks' own Latin-character content at 40.35% for sinhala and 1.26% for tamil.\n"
          "So the sinhala/singlish contrast is 'heavily code-mixed native script' vs\n"
          "'fully romanized', while tamil/tamilish is 'nearly pure Tamil script' vs\n"
          "'fully romanized' -- a different comparison with a different baseline. Whether\n"
          "that asymmetry is a property of the languages or an artifact of how the two\n"
          "tracks were produced is open, and is the same question as task B5 (Tamil is\n"
          "documented as having had no manual pass). Do not present the two pairs as two\n"
          "measurements of one effect until B5 is settled.")
    print(f"\nwritten to {(OUT / 'encoder_gain_by_script.csv').relative_to(REPO)}")


if __name__ == "__main__":
    main()
