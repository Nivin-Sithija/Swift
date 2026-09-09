"""Persist per-ticket posterior distributions -- the input the scoring function needs.

Why this exists
---------------
Every prediction file in `ml/predictions/runs/` holds hard labels only
(`id,language,y_true,y_pred`). That is all a paired significance test needs, and it
is not enough for the Ticket Urgency Score, whose whole argument is that a
confident Low and a 0.49/0.51 Low-Medium coin flip must not receive the same
position in the queue. The score consumes `P(class | ticket)`, so the posteriors
have to be materialised.

Contamination discipline -- read before adding a source here
------------------------------------------------------------
The saved LaBSE checkpoints were fit on `train+dev`, because they exist to be
scored on test. Their **dev** posteriors are therefore contaminated: dev was in
their training data, and any weight fitted against them would be fitted against
memorisation.

So the two portions come from deliberately different fits:

    test  <- LaBSE (train+dev)   and  TF-IDF (train+dev)   -- scored once, never tuned on
    dev   <- TF-IDF (train only)                           -- what the TUS weights are fit on

Fitting the TUS weights on TF-IDF dev posteriors and applying them to LaBSE test
posteriors is not a compromise forced by the checkpoints; it is the better design.
It keeps the weights from being tuned to one encoder's confidence idiosyncrasies,
and it is what makes the classifier-substitution ablation (SYSTEM_PLAN Layer 5) a
controlled comparison rather than two separately-tuned systems.

Self-check
----------
The LaBSE test posteriors are verified against the recorded run scores before
anything is written. If argmax over these posteriors does not reproduce sentiment
Negative-F1 0.7138 and priority macro-F1 0.8900, the inference path has drifted
from the training path -- almost always `max_length`, which is not stored in the
checkpoint -- and the run aborts rather than writing plausible-looking garbage.

Run:
    .venv312/bin/python paper/experiments/save_posteriors.py
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

from swiftbench import config, data, imbalance, metrics, models, splits  # noqa: E402

OUT = REPO / "paper" / "results" / "posteriors"
CKPT = REPO / "ml" / "models" / "encoders"
MAX_LENGTH = 128          # must match training; not stored in the checkpoint
BATCH = 64

# The arm each classical model won pooled on, mirroring save_test_predictions.py.
CLASSICAL_ARM = {"sentiment": "ros", "priority": "ros", "intent": "none"}

# What the recorded runs scored, to catch an inference path that has drifted.
EXPECTED = {"sentiment": ("negative_f1", 0.7138), "priority": ("macro_f1", 0.8900)}


def device() -> str:
    import torch
    if torch.backends.mps.is_available():
        return "mps"
    return "cuda" if torch.cuda.is_available() else "cpu"


def encoder_posteriors(task: str, frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Softmax over the saved train+dev LaBSE checkpoint for `task`."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    path = CKPT / f"{task}_labse"
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path).eval()
    dev = device()
    model.to(dev)

    # Never hardcode the index order -- a wrong guess does not raise, it silently
    # permutes every column of the posterior.
    labels = [model.config.id2label[i] for i in range(model.config.num_labels)]

    texts = frame[config.TEXT_COLUMN].tolist()
    out = np.empty((len(texts), len(labels)), dtype=np.float64)
    started = time.time()
    with torch.no_grad():
        for i in range(0, len(texts), BATCH):
            batch = tok(texts[i:i + BATCH], return_tensors="pt", padding=True,
                        truncation=True, max_length=MAX_LENGTH).to(dev)
            out[i:i + BATCH] = model(**batch).logits.softmax(-1).float().cpu().numpy()
            if i % (BATCH * 40) == 0:
                print(f"    {task} {i:>6}/{len(texts)}  {time.time() - started:5.0f}s", flush=True)
    del model
    return out, labels


def classical_posteriors(task: str, fit: pd.DataFrame,
                         evalf: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """TF-IDF logistic regression, refit here so the fit portion is explicit."""
    label_col = data.label_column(task)
    arm = CLASSICAL_ARM[task]
    resampled = imbalance.resample(fit, label_col, arm)
    clf = models.build("tfidf-logreg", class_weight=imbalance.class_weight_for(arm))
    clf.fit(resampled[config.TEXT_COLUMN], resampled[label_col])
    proba = clf.predict_proba(evalf[config.TEXT_COLUMN])
    return proba, [str(c) for c in clf.classes_]


def write(frame: pd.DataFrame, proba: np.ndarray, labels: list[str], task: str,
          model: str, portion: str, fit_portion: str) -> Path:
    label_col = data.label_column(task)
    out = pd.DataFrame({"id": frame["id"].to_numpy(),
                        "language": frame["language"].to_numpy(),
                        "y_true": frame[label_col].to_numpy()})
    for j, name in enumerate(labels):
        out[f"p_{name}"] = proba[:, j]
    out["y_pred"] = [labels[k] for k in proba.argmax(1)]

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{task}__{model}__{portion}.csv"
    with path.open("w") as fh:
        fh.write(f"# split={splits.sha()} task={task} model={model} "
                 f"fit={fit_portion} eval={portion} label_version=v8 "
                 f"max_length={MAX_LENGTH} generated_by=save_posteriors.py\n")
        out.to_csv(fh, index=False)
    return path


def check(task: str, frame: pd.DataFrame, proba: np.ndarray, labels: list[str]) -> None:
    if task not in EXPECTED:
        return
    key, expected = EXPECTED[task]
    y_pred = np.asarray([labels[k] for k in proba.argmax(1)])
    got = metrics.score(frame[data.label_column(task)].to_numpy(), y_pred, task)[key]
    print(f"  self-check {task} {key}: {got:.4f}  (recorded {expected:.4f})")
    if abs(got - expected) > 5e-4:
        raise SystemExit(
            f"ABORT: {task} {key} is {got:.4f}, recorded run says {expected:.4f}.\n"
            f"The inference path does not match the training path. Check MAX_LENGTH "
            f"({MAX_LENGTH}) and the label order first -- neither is stored in a way "
            f"that fails loudly.")


def main() -> None:
    print(f"split {splits.sha()}  device {device()}  ->  {OUT}")
    train = splits.get(config.LANGUAGES, "train")
    dev = splits.get(config.LANGUAGES, "dev")
    test = splits.get(config.LANGUAGES, "test")
    train_dev = pd.concat([train, dev], ignore_index=True)
    print(f"train {len(train)}  dev {len(dev)}  test {len(test)}")

    written: list[Path] = []

    # --- test, LaBSE (train+dev fit) -- the system the paper reports -------------
    for task in ("sentiment", "priority"):
        print(f"\nlabse {task} -> test")
        proba, labels = encoder_posteriors(task, test)
        check(task, test, proba, labels)
        written.append(write(test, proba, labels, task, "labse", "test", "train+dev"))

    # --- test, TF-IDF (train+dev fit) -- the classifier-substitution control -----
    for task in ("sentiment", "priority", "intent"):
        print(f"\ntfidf-logreg {task} -> test")
        proba, labels = classical_posteriors(task, train_dev, test)
        written.append(write(test, proba, labels, task, "tfidf-logreg", "test", "train+dev"))

    # --- dev, TF-IDF (train fit only) -- what the TUS weights are fitted on ------
    for task in ("sentiment", "priority", "intent"):
        print(f"\ntfidf-logreg {task} -> dev")
        proba, labels = classical_posteriors(task, train, dev)
        written.append(write(dev, proba, labels, task, "tfidf-logreg", "dev", "train"))

    # --- kappa(i) = P(High | intent), estimated on train+dev ONLY ---------------
    # The per-intent criticality term of the score. Estimated away from test so the
    # score carries no information about the rows it is scored on.
    crit = (train_dev.assign(is_high=(train_dev["priority"] == "High").astype(float))
            .groupby("category")["is_high"].agg(["mean", "size"])
            .rename(columns={"mean": "kappa", "size": "n"})
            .sort_values("kappa", ascending=False))
    crit_path = OUT / "intent_criticality.csv"
    with crit_path.open("w") as fh:
        fh.write(f"# kappa(i) = P(priority=High | intent=i), estimated on train+dev "
                 f"({len(train_dev)} rows). split={splits.sha()} label_version=v8\n")
        crit.to_csv(fh)
    written.append(crit_path)
    print(f"\nkappa over {len(crit)} intents: "
          f"min {crit['kappa'].min():.3f}  max {crit['kappa'].max():.3f}  "
          f"mean {crit['kappa'].mean():.3f}")
    print("  most critical:", ", ".join(crit.head(5).index))
    print("  least critical:", ", ".join(crit.tail(5).index))

    (OUT / "MANIFEST.json").write_text(json.dumps(
        {"split": splits.sha(), "label_version": "v8", "max_length": MAX_LENGTH,
         "files": [p.name for p in written]}, indent=2))
    print(f"\nwrote {len(written)} files")


if __name__ == "__main__":
    main()
