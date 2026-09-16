"""Per-row intent test predictions, recovered from the saved K6b checkpoints.

Why this exists
---------------
K6b produced the project's first clean intent test numbers -- LaBSE 88.35, XLM-R
88.01, mmBERT 86.80 -- but that Kaggle run wrote no per-row prediction files, so
the ranking was a **point estimate with no test behind it**. `results.md` §18 says
so explicitly and declines to call mmBERT beaten.

The checkpoints came back, so the predictions are recoverable without another GPU
hour: re-run inference over the same frozen test set and save what the run should
have saved.

Two things that will silently corrupt this if got wrong
-------------------------------------------------------
* **`max_length` is per model and is not stored in the checkpoint.** K6b ran LaBSE
  at 128 and mmBERT at **160**. Using one value for both changes mmBERT's inputs
  and the reproduction check below will fail -- which is what it is for.
* **Label order.** Read from `label_order.json` / `config.id2label`, never an
  index guess. A permuted order does not raise; it silently scrambles 77 classes.

Each model's pooled macro-F1 is checked against its recorded K6b run before
anything is written. `xlmr-base` is absent because its checkpoint download failed
partway (configs only, no weights).

Run:
    .venv312/bin/python paper/experiments/intent_test_predictions.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml"))

from swiftbench import config, data, metrics, splits  # noqa: E402

OUT = REPO / "paper" / "results" / "posteriors"
PRED = REPO / "ml" / "predictions" / "runs"
CKPT = REPO / "ml" / "models" / "encoders"
BATCH = 64

# max_length as K6b actually ran it, per model. Not recoverable from the checkpoint.
MODELS = {"labse": 128, "mmbert": 160}


def recorded_macro_f1(model: str) -> float | None:
    hits = [p for p in (REPO / "ml" / "reports" / "runs").glob(
        f"intent__{model}__*__ev-all__*__test.json")]
    for p in hits:
        rec = json.loads(p.read_text())
        if rec.get("fit_portion") == "train+dev" and rec.get("epochs") == 6:
            return float(rec["macro_f1"])
    return None


def infer(model: str, max_length: int, frame: pd.DataFrame):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    path = CKPT / f"intent_{model}"
    tok = AutoTokenizer.from_pretrained(path)
    net = AutoModelForSequenceClassification.from_pretrained(path).eval()
    dev = "mps" if torch.backends.mps.is_available() else (
        "cuda" if torch.cuda.is_available() else "cpu")
    net.to(dev)
    labels = [net.config.id2label[i] for i in range(net.config.num_labels)]

    texts = frame[config.TEXT_COLUMN].tolist()
    probs = np.empty((len(texts), len(labels)), dtype=np.float32)
    started = time.time()
    with torch.no_grad():
        for i in range(0, len(texts), BATCH):
            b = tok(texts[i:i + BATCH], return_tensors="pt", padding=True,
                    truncation=True, max_length=max_length).to(dev)
            probs[i:i + BATCH] = net(**b).logits.softmax(-1).float().cpu().numpy()
            if i % (BATCH * 50) == 0:
                print(f"    {model} {i:>6}/{len(texts)}  {time.time()-started:5.0f}s",
                      flush=True)
    del net
    return probs, labels


def main() -> None:
    test = splits.get(config.LANGUAGES, "test")
    label_col = data.label_column("intent")
    y_true = test[label_col].to_numpy()
    print(f"split {splits.sha()}  test {len(test)} rows")

    OUT.mkdir(parents=True, exist_ok=True)
    PRED.mkdir(parents=True, exist_ok=True)
    for model, max_length in MODELS.items():
        if not (CKPT / f"intent_{model}" / "model.safetensors").exists():
            print(f"  SKIP {model}: no weights on disk")
            continue
        print(f"\n{model} (max_length={max_length})")
        probs, labels = infer(model, max_length, test)
        y_pred = np.asarray(labels)[probs.argmax(1)]

        got = metrics.score(y_true, y_pred, "intent")["macro_f1"]
        want = recorded_macro_f1(model)
        print(f"  macro_f1 {got:.4f}   recorded K6b {want:.4f}" if want else
              f"  macro_f1 {got:.4f}   (no recorded run to check against)")
        if want is not None and abs(got - want) > 5e-4:
            raise SystemExit(
                f"ABORT: {model} reproduces {got:.4f}, K6b recorded {want:.4f}. "
                f"Check max_length (using {max_length}) and the label order before "
                f"trusting anything written from these predictions.")

        # config.LANGUAGES order, not sorted() -- every existing prediction and run
        # filename in the repo uses the config order, and a sorted variant writes a
        # second file that the paired tests will never find.
        stem = (f"intent__{model}__tr-{'-'.join(config.LANGUAGES)}"
                f"__ev-all__arm-class-weight__test")
        pd.DataFrame({"id": test["id"].to_numpy(),
                      "language": test["language"].to_numpy(),
                      "y_true": y_true, "y_pred": y_pred}).to_csv(
            PRED / f"{stem}.csv", index=False)

        post = pd.DataFrame({"id": test["id"].to_numpy(),
                             "language": test["language"].to_numpy(), "y_true": y_true})
        for j, lab in enumerate(labels):
            post[f"p_{lab}"] = probs[:, j]
        post["y_pred"] = y_pred
        path = OUT / f"intent__{model}__test.csv"
        with path.open("w") as fh:
            fh.write(f"# split={splits.sha()} task=intent model={model} fit=train+dev "
                     f"eval=test label_version=v8 max_length={max_length} "
                     f"recovered_from=checkpoint generated_by=intent_test_predictions.py\n")
            post.to_csv(fh, index=False)
        print(f"  -> {path.relative_to(REPO)} and {(PRED/f'{stem}.csv').relative_to(REPO)}")


if __name__ == "__main__":
    main()
