"""Kernel body: fine-tune the encoder roster on Kaggle's T4s.

`runner.py` prepends the configuration constants (MODELS, TASK, EPOCHS, BATCH_SIZE, SMOKE,
DATASET_DIR) before pushing, so this file is the logic only.

Runs each model in sequence, writes one result JSON per run to /kaggle/working (which becomes the
kernel's downloadable output), and keeps going if one candidate fails -- a bad checkpoint should
not cost the whole GPU session.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

# --------------------------------------------------------------- environment
WORK = Path("/kaggle/working")
INPUT = Path("/kaggle/input")
ROOT = WORK / "repo"


MARKER = Path("datasets/english/train_labeled.csv")   # proves we found the real payload root


def find_payload() -> Path:
    """Locate the attached dataset by looking for a known file, not by guessing a path.

    Kaggle's mount directory is not reliably the dataset slug: it depends on the title, on how
    uploaded archives were expanded, and on whether the payload landed one level up. Searching for
    a marker file is robust to all of that; a hardcoded path is not, and it fails minutes into a
    paid GPU session.
    """
    # Kaggle CLI 2.2.x mounts at /kaggle/input/datasets/<owner>/<slug>/, older versions at
    # /kaggle/input/<slug>/. Check both, then fall back to a recursive search for the marker.
    candidates = [INPUT / Path(DATASET_DIR).name, INPUT]  # noqa: F821 -- injected by runner.py
    if INPUT.is_dir():
        candidates += sorted(p for p in INPUT.iterdir() if p.is_dir())
    for cand in candidates:
        if (cand / MARKER).exists():
            print(f"payload root: {cand}")
            return cand
    for hit in INPUT.rglob(MARKER.name):
        if hit.parent.name == "english" and hit.parent.parent.name == "datasets":
            root = hit.parents[2]
            print(f"payload root (search): {root}")
            return root

    tree = []
    for p in sorted(INPUT.rglob("*"))[:60] if INPUT.is_dir() else []:
        tree.append(str(p.relative_to(INPUT)))
    raise SystemExit(
        f"Could not find {MARKER} under {INPUT}.\nFirst 60 entries:\n  " + "\n  ".join(tree) +
        "\n\nRe-run `runner.py sync`, wait for the dataset to report 'ready', then re-run."
    )


def find_swiftbench(root: Path) -> Path:
    """The `ml/` parent to put on sys.path -- may not sit beside `datasets/`."""
    if (root / "ml" / "swiftbench" / "config.py").exists():
        return root / "ml"
    for hit in INPUT.rglob("swiftbench/config.py"):
        print(f"swiftbench found at {hit.parent} (outside the payload root)")
        return hit.parents[1]
    raise SystemExit(f"swiftbench not found under {INPUT} -- re-run `runner.py sync`")


SOURCE = find_payload()

ML_SRC = find_swiftbench(SOURCE)

# /kaggle/input is read-only, and `results.save()` writes to <root>/ml/reports/runs. So the
# payload is assembled in a writable root first -- it is ~20 MB, which costs nothing.
if not ROOT.exists():
    ROOT.mkdir(parents=True)
    shutil.copytree(SOURCE / "datasets", ROOT / "datasets")
    shutil.copytree(ML_SRC, ROOT / "ml")
    print(f"assembled payload -> {ROOT}")

# swiftbench resolves its data paths from SWIFT_REPO_ROOT; without it, importing from
# /kaggle/working/repo/ml/swiftbench would walk up two parents and land on the wrong directory.
os.environ["SWIFT_REPO_ROOT"] = str(ROOT)
sys.path.insert(0, str(ROOT / "ml"))

subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "indic-nlp-library", "regex"], check=False)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

print("=" * 70)
print("torch", torch.__version__, "| cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        p = torch.cuda.get_device_properties(i)
        print(f"  GPU{i}: {p.name}  {p.total_memory/1e9:.1f} GB  sm_{p.major}{p.minor}")
    # T4 is Turing (sm_75): fp16 tensor cores, no bf16.
    print("  bf16 supported:", torch.cuda.is_bf16_supported())
print("=" * 70)

import swiftbench as sb  # noqa: E402
from swiftbench import config, splits, train_encoder as te  # noqa: E402

print("split sha:", splits.sha(), splits.ensure()["counts"])
print("languages:", config.LANGUAGES)

# --------------------------------------------------------------- sanity
# If the payload did not attach correctly every downstream number would be silently wrong,
# so fail loudly here instead.
for lang in config.LANGUAGES:
    p = config.DATASETS_DIR / lang / "train_labeled.csv"
    assert p.exists(), f"missing {p} -- did `runner.py sync` finish processing?"
print("payload OK:", config.DATASETS_DIR)

# --------------------------------------------------------------- per-language matrix
# Tests the dilution hypothesis on the encoder: does training one model on all five
# languages help or hurt each language vs a model trained on that language alone?
import swiftbench as sb  # noqa: E402
from swiftbench import metrics, data, results  # noqa: E402

MODEL_LIST = [m.strip() for m in MODELS.split(",") if m.strip()]  # noqa: F821
label = data.label_column(TASK)  # noqa: F821
LANGS = list(config.LANGUAGES)
summary = []

def record(regime, model, lang, sc, secs):
    row = {"model": model, "regime": regime, "language": lang,
           "negative_f1": sc.get("negative_f1"), "macro_f1": sc.get("macro_f1"),
           "accuracy": sc.get("accuracy"), "wall_s": round(secs, 1)}
    summary.append(row)
    pd.DataFrame(summary).to_csv(WORK / "perlang_summary.csv", index=False)
    print(f"  {model:12s} {regime:11s} {lang:9s} "
          f"negF1={row['negative_f1']:.4f} macroF1={row['macro_f1']:.4f}", flush=True)

for MODEL in MODEL_LIST:
    # 1) MULTI: fit once on all five, then slice the pooled eval frame into per-language cells.
    print("\n" + "=" * 70 + f"\n### MULTI  {MODEL}  (fit all 5, eval each cell)\n" + "=" * 70, flush=True)
    t0 = time.time()
    try:
        run = te.run(task=TASK, model=MODEL, train_langs=LANGS, eval_lang="all",  # noqa: F821
                     arm="class_weight", portion="dev", fit_portion="train",
                     epochs=EPOCHS, batch_size=BATCH_SIZE, author="perlang-multi",  # noqa: F821
                     save=True, verbose=True)
        secs = time.time() - t0
        ev = run.eval_frame.copy(); ev["pred"] = run.predictions
        for lang in LANGS:
            m = ev.language == lang
            sc = metrics.score(ev.loc[m, label], ev.loc[m, "pred"], TASK)  # noqa: F821
            results.save(TASK, MODEL, LANGS, lang, "class_weight", "dev", sc,  # noqa: F821
                         author="perlang-multi", extra={"regime": "multi-cell"})
            record("multi", MODEL, lang, sc, secs)
    except Exception:
        traceback.print_exc()
        record("multi-FAILED", MODEL, "all", {}, time.time() - t0)

    # 2) MONO: fit a fresh model on each single language, eval that language.
    for lang in LANGS:
        print("\n" + "=" * 70 + f"\n### MONO  {MODEL}  train+eval {lang}\n" + "=" * 70, flush=True)
        t0 = time.time()
        try:
            r = te.run(task=TASK, model=MODEL, train_langs=[lang], eval_lang=lang,  # noqa: F821
                       arm="class_weight", portion="dev", fit_portion="train",
                       epochs=EPOCHS, batch_size=BATCH_SIZE, author="perlang-mono",  # noqa: F821
                       save=True, verbose=True)
            record("mono", MODEL, lang, r.scores, time.time() - t0)
        except Exception:
            traceback.print_exc()
            record("mono-FAILED", MODEL, lang, {}, time.time() - t0)

print("\n" + "=" * 70)
print(pd.DataFrame(summary).to_string(index=False))
print("=" * 70)
src = config.REPORTS_DIR / "runs"
if src.exists():
    for f in src.glob("*.json"):
        (WORK / f.name).write_text(f.read_text())
print("outputs:", sorted(p.name for p in WORK.iterdir()))
