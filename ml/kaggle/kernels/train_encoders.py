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

# Refuse a stale dataset version. Kaggle needs a minute or two to process a new version, and a
# kernel started inside that window silently attaches the previous one -- old code, tracebacks
# pointing at line numbers that no longer exist, and a diagnosis that sends you chasing a bug you
# already fixed. Checked before anything else so the failure costs seconds, not a GPU session.
try:
    EXPECTED_PAYLOAD_SHA  # noqa: F821 -- injected by runner.py; absent from older headers
except NameError:
    EXPECTED_PAYLOAD_SHA = None
if EXPECTED_PAYLOAD_SHA:
    stamp_file = ML_SRC / "splits" / "payload_stamp.json"
    got = json.loads(stamp_file.read_text())["sha"] if stamp_file.exists() else None
    if got != EXPECTED_PAYLOAD_SHA:
        raise SystemExit(
            f"STALE PAYLOAD: kernel expects {EXPECTED_PAYLOAD_SHA}, attached dataset is {got}.\n"
            "Kaggle had not finished processing the new dataset version when this kernel started.\n"
            "Wait for `kaggle datasets status` to report 'ready', then re-run."
        )
    print(f"payload sha {got} -- matches the kernel")

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

# --------------------------------------------------------------- run
models = [m.strip() for m in MODELS.split(",") if m.strip()]  # noqa: F821
# Backward-compatible defaults: older runner headers do not inject these.
try:
    FIT_PORTION
except NameError:
    FIT_PORTION = "train"
try:
    EVAL_PORTION
except NameError:
    EVAL_PORTION = "dev"
summary = []
# Older runner headers do not inject this -- default to off so a routine bake-off run does not
# suddenly start writing multi-hundred-MB checkpoints for every candidate.
try:
    SAVE_MODELS
except NameError:
    SAVE_MODELS = False
# LoRA + learning rate arrived with the decoder SLM candidates; older runner headers omit them.
try:
    LORA
except NameError:
    LORA, LORA_R, LORA_ALPHA = False, 8, 16
try:
    LORA_TARGETS
except NameError:
    LORA_TARGETS = "attn"
try:
    LR
except NameError:
    LR = None

if LORA:
    # peft is not in the Kaggle image by default. Installed only when needed so an encoder run
    # does not pay for it, and pinned to nothing so the image's transformers stays satisfied.
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "peft"], check=False)
    # ...and then torchao is removed. peft's LoRA layer dispatcher calls `is_torchao_available()`
    # unconditionally, and that helper *raises* on an out-of-range version rather than returning
    # False. The Kaggle image ships torchao 0.10.0; current peft wants >0.16.0, so every
    # `get_peft_model` call dies with an ImportError before a single step runs. We do not quantize,
    # so nothing here needs torchao -- and uninstalling is safer than upgrading it, which would
    # drag in a torch the image's CUDA build may not match.
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)

for name in models:
    print("\n" + "=" * 70)
    print(f"### {name}   task={TASK}  epochs={EPOCHS}  batch={BATCH_SIZE}  "  # noqa: F821
          f"fit={FIT_PORTION}  eval={EVAL_PORTION}  smoke={SMOKE}  "         # noqa: F821
          f"save_models={SAVE_MODELS}  lora={LORA}({LORA_TARGETS})  lr={LR}")
    print("=" * 70, flush=True)
    started = time.time()
    try:
        run = te.run(
            task=TASK,                                    # noqa: F821
            model=name,
            arm="class_weight",
            portion=EVAL_PORTION,
            fit_portion=FIT_PORTION,
            epochs=1 if SMOKE else EPOCHS,                # noqa: F821
            batch_size=BATCH_SIZE,                        # noqa: F821
            subsample=1200 if SMOKE else None,            # noqa: F821
            lora=LORA, lora_r=LORA_R, lora_alpha=LORA_ALPHA, lora_targets=LORA_TARGETS,
            **({"lr": LR} if LR else {}),
            author="kaggle",
            save=True,
            verbose=True,
            save_dir=str(WORK / "models" / f"{TASK}_{name}") if SAVE_MODELS else None,  # noqa: F821
        )
        row = {"model": name, "status": "ok",
               **{k: v for k, v in run.scores.items() if not isinstance(v, (list, dict))}}
        run.history.to_csv(WORK / f"history_{name}.csv", index=False)

        # per-language breakdown, so the leaderboard does not need a refit to get it
        ev = run.eval_frame.copy()
        ev["pred"] = run.predictions
        per_lang = []
        for lang in ev.language.unique():
            m = ev.language == lang
            s = sb.metrics.score(ev.loc[m, sb.data.label_column(TASK)], ev.loc[m, "pred"], TASK)  # noqa: F821
            per_lang.append({"model": name, "language": lang,
                             **{k: v for k, v in s.items() if not isinstance(v, str)}})
        pd.DataFrame(per_lang).to_csv(WORK / f"per_language_{name}.csv", index=False)

    except Exception:
        traceback.print_exc()
        row = {"model": name, "status": "failed", "error": traceback.format_exc()[-600:]}

    row["wall_seconds"] = round(time.time() - started, 1)
    summary.append(row)
    pd.DataFrame(summary).to_csv(WORK / "encoder_summary.csv", index=False)
    print(f"--- {name} done in {row['wall_seconds']/60:.1f} min ---", flush=True)

# --------------------------------------------------------------- collect
# swiftbench wrote its run JSONs under the (read-only-ish) reports dir inside the payload copy;
# mirror them into /kaggle/working so they come back with the kernel output.
src = config.REPORTS_DIR / "runs"
if src.exists():
    for f in src.glob("*.json"):
        (WORK / f.name).write_text(f.read_text())

print("\n" + "=" * 70)
print(pd.DataFrame(summary).to_string(index=False))
print("=" * 70)
print("outputs:", sorted(p.name for p in WORK.iterdir()))
