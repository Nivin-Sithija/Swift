"""Kernel body: joint multi-task Gemma-3 fine-tuning (`swiftbench.train_multitask`).

`runner.py` prepends the configuration constants before pushing. Reuses the `TASK` slot (normally
a single task name) as the **variant** selector, since both variants here always cover all three
tasks in one run: `TASK="shared-heads"` -> `train_multitask.run_shared_heads()` (one adapter, three
heads), `TASK="shared-head"` -> `train_multitask.run_shared_head()` (one adapter, one head over the
union label space, task given as a text prefix). `MODELS` is a single decoder model, e.g.
`gemma-3-1b` -- gemma-3-270m is excluded by default here because RESULTS.md §14.5 already measured
it collapsing on sentiment (-0.082 vs 1b) and is not a serious candidate for a joint run that pays
that cost on all three tasks at once.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

WORK = Path("/kaggle/working")
INPUT = Path("/kaggle/input")
ROOT = WORK / "repo"

MARKER = Path("datasets/english/train_labeled.csv")


def find_payload() -> Path:
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
    if (root / "ml" / "swiftbench" / "config.py").exists():
        return root / "ml"
    for hit in INPUT.rglob("swiftbench/config.py"):
        print(f"swiftbench found at {hit.parent} (outside the payload root)")
        return hit.parents[1]
    raise SystemExit(f"swiftbench not found under {INPUT} -- re-run `runner.py sync`")


SOURCE = find_payload()
ML_SRC = find_swiftbench(SOURCE)

try:
    EXPECTED_PAYLOAD_SHA  # noqa: F821
except NameError:
    EXPECTED_PAYLOAD_SHA = None
if EXPECTED_PAYLOAD_SHA:
    stamp_file = ML_SRC / "splits" / "payload_stamp.json"
    got = json.loads(stamp_file.read_text())["sha"] if stamp_file.exists() else None
    if got != EXPECTED_PAYLOAD_SHA:
        raise SystemExit(
            f"STALE PAYLOAD: kernel expects {EXPECTED_PAYLOAD_SHA}, attached dataset is {got}.\n"
            "Wait for `kaggle datasets status` to report 'ready', then re-run."
        )
    print(f"payload sha {got} -- matches the kernel")

if not ROOT.exists():
    ROOT.mkdir(parents=True)
    shutil.copytree(SOURCE / "datasets", ROOT / "datasets")
    shutil.copytree(ML_SRC, ROOT / "ml")
    print(f"assembled payload -> {ROOT}")

os.environ["SWIFT_REPO_ROOT"] = str(ROOT)
sys.path.insert(0, str(ROOT / "ml"))

subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                "indic-nlp-library", "regex", "peft"], check=False)
# Same torchao incompatibility as train_encoders.py / perlang_lora.py: Kaggle ships 0.10.0, peft's
# LoRA dispatcher hard-raises below 0.16.0. Not needed for plain fp16 LoRA.
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)

import pandas as pd  # noqa: E402
import torch  # noqa: E402

print("=" * 70)
print("torch", torch.__version__, "| cuda", torch.cuda.is_available())
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        p = torch.cuda.get_device_properties(i)
        print(f"  GPU{i}: {p.name}  {p.total_memory/1e9:.1f} GB  sm_{p.major}{p.minor}")
    print("  bf16 supported:", torch.cuda.is_bf16_supported())
print("=" * 70)

from swiftbench import config, splits, train_multitask as tm  # noqa: E402

print("split sha:", splits.sha(), splits.ensure()["counts"])
for lang in config.LANGUAGES:
    assert (config.DATASETS_DIR / lang / "train_labeled.csv").exists(), \
        f"missing {lang} train_labeled.csv -- did `runner.py sync` finish processing?"
print("payload OK:", config.DATASETS_DIR)

VARIANT = TASK  # noqa: F821 -- "shared-heads" or "shared-head"
MODEL = [m.strip() for m in MODELS.split(",") if m.strip()][0]  # noqa: F821
RUN_FN = {"shared-heads": tm.run_shared_heads, "shared-head": tm.run_shared_head}[VARIANT]

print(f"\n### multitask variant={VARIANT}  model={MODEL}  fit={FIT_PORTION}  "  # noqa: F821
      f"eval={EVAL_PORTION}  epochs={EPOCHS}  smoke={SMOKE}  save_models={SAVE_MODELS}")  # noqa: F821

started = time.time()
summary = []
try:
    run = RUN_FN(
        model=MODEL,
        portion=EVAL_PORTION,          # noqa: F821
        fit_portion=FIT_PORTION,       # noqa: F821
        epochs=1 if SMOKE else EPOCHS,  # noqa: F821
        batch_size=BATCH_SIZE,         # noqa: F821
        lr=LR or 1e-4,                 # noqa: F821
        lora_targets=LORA_TARGETS,     # noqa: F821
        subsample=1200 if SMOKE else None,  # noqa: F821
        author="kaggle",
        save=True,
        verbose=True,
        save_dir=str(WORK / "models" / f"multitask-{VARIANT}_{MODEL}") if SAVE_MODELS else None,  # noqa: F821
    )
    for t, sc in run.scores.items():
        summary.append({"task": t, "status": "ok",
                        **{k: v for k, v in sc.items() if not isinstance(v, (list, dict))}})
    run.history.to_csv(WORK / f"history_multitask_{VARIANT}.csv", index=False)
except Exception:
    traceback.print_exc()
    summary.append({"task": "ALL", "status": "failed", "error": traceback.format_exc()[-800:]})

pd.DataFrame(summary).to_csv(WORK / f"multitask_{VARIANT}_summary.csv", index=False)
print(f"--- multitask {VARIANT} done in {(time.time()-started)/60:.1f} min ---", flush=True)

src = config.REPORTS_DIR / "runs"
if src.exists():
    for f in src.glob("*.json"):
        (WORK / f.name).write_text(f.read_text())

print("\n" + "=" * 70)
print(pd.DataFrame(summary).to_string(index=False))
print("=" * 70)
print("outputs:", sorted(p.name for p in WORK.iterdir()))
