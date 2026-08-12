# Trained model artifacts

Everything in this directory is a **fitted model ready for inference on raw text**. Metrics live
in `ml/reports/` — this file is only about the weights: what exists, how to load it, and what each
one can honestly be used for.

Two families, stored very differently:

| family | location | in git? | size |
|---|---|---|---|
| classical TF-IDF pipelines (`.joblib`) | `ml/models/*.joblib` | ✅ tracked | 14–49 MB each |
| fine-tuned encoders (LaBSE) | `ml/models/encoders/<task>_<model>/` | ❌ **gitignored** | ~1.9 GB each |

The encoders are excluded from git deliberately: GitHub rejects single files over 100 MB, and the
LFS free tier (1 GB) does not cover even one checkpoint. See [Obtaining the encoder
weights](#obtaining-the-encoder-weights).

---

## 1. Inventory & what each model predicts

### Classical `.joblib` — **intent only**

Twelve pipelines from `ml/scripts/train_baseline.py`: `tfidf_{linear_svm,logistic_regression}_{all,english,sinhala,singlish,tamil,tamilish}.joblib`.

All twelve predict **intent** (77-way BANKING77 routing). `linear_svm` was the stronger family;
`_all` is trained on all five languages pooled and is the one to use unless you have a reason to
pin a language.

There is **no saved classical model for sentiment or priority.** Those were benchmarked through
`swiftbench`, whose `results.save()` writes metric JSON only — it never persists an estimator. If
you want a classical sentiment/priority model as a deployable artifact, it has to be refit and
dumped; the scores in `ml/reports/` came from models that no longer exist.

### Fine-tuned encoders — sentiment & priority

`encoders/sentiment_labse/` and `encoders/priority_labse/`: `sentence-transformers/LaBSE`
fine-tuned on all five languages pooled, `class_weight` arm, fit on `train+dev` (49,990 rows),
scored once on test (15,395 rows). Produced by `ml/kaggle/runner.py ... --save-models`.

⚠️ **`train+dev` means dev is inside these checkpoints' training data.** Anything that re-evaluates
them — a linear probe, a calibration pass, a threshold sweep — must score on **test**, the only
portion their backbones never saw, and compare against their *test* numbers (sentiment 0.5664,
priority 0.8900), never their dev ones. Scoring one of them on dev does not error and does not look
wrong: `swiftbench.probe` first read `priority_labse` at 0.9645 macro-F1 against that model's own
0.9168 fine-tune, which is memorised rows presenting as a breakthrough. `probe.score()` now refuses
the combination; nothing else does.

**Intent has fine-tuned encoders on dev but no saved weights and no test scoring.**
`ml/reports/runs/` holds four intent encoder runs — mmbert 0.9280, gemma-3-1b 0.9243 (LoRA), labse
0.9224, gemma-3-270m 0.9038 (LoRA), all pooled dev macro-F1, all best-epoch 3 of 3. They post-date
the "intent is classical-only" note this paragraph used to carry. What is still true: no intent
encoder has been scored on test, and none was saved with `--save-models`, so the deployable intent
model remains the classical `tfidf_linear_svm_all.joblib`.

---

## 2. Loading

### Classical

The pipelines bundle their own fitted vectorizers and use stock `analyzer="word"` / `"char_wb"`
with no custom callables, so they unpickle standalone — `swiftbench` does **not** need to be
importable.

```python
import joblib
pipe = joblib.load("ml/models/tfidf_linear_svm_all.joblib")
pipe.predict(["How do I activate my new card?"])          # -> array(['activate_my_card'])
```

`LinearSVC` has no `predict_proba`. Use `decision_function()` if you need a confidence score, or
switch to the `logistic_regression` variant, which does expose probabilities at some cost in
accuracy.

### Encoders

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

path = "ml/models/encoders/sentiment_labse"
tok = AutoTokenizer.from_pretrained(path)
model = AutoModelForSequenceClassification.from_pretrained(path).eval()

with torch.no_grad():
    batch = tok(["My money is gone and nobody has helped me!"],
                return_tensors="pt", truncation=True, max_length=128)
    probs = model(**batch).logits.softmax(-1)[0]

label = model.config.id2label[int(probs.argmax())]         # -> 'Negative'
```

**`max_length` must match training** — 128 for LaBSE. It is not stored in the checkpoint; the
per-tokenizer values live in `ENCODERS` in `ml/swiftbench/train_encoder.py`.

**On label order.** These checkpoints carry an explicit `id2label`, so always read the name from
`model.config.id2label` rather than assuming an index. Do not hardcode "1 means Negative" — the
orders differ per task (`["Neutral", "Negative"]` vs `["Low", "Medium", "High"]`) and a wrong guess
inverts predictions silently rather than raising.

Checkpoints trained before 2026-08-07 were saved *without* this mapping and load as
`LABEL_0`/`LABEL_1`. `train_encoder.py` now embeds it at save time, and `runner.py fetch` repairs
any checkpoint that arrives without it — necessary because `fetch` replaces a checkpoint directory
wholesale, so a manual edit does not survive the next pull. If you ever see `LABEL_n` from a model
here, run:

```python
import sys; sys.path.insert(0, "ml/kaggle")
import runner; runner.stamp_labels(Path("ml/models/encoders/<name>"))
```

Cost: LaBSE is 471M parameters, ~1.9 GB resident, roughly 100–300 ms per ticket on CPU. Batch, or
use a GPU, if throughput matters. Load the model **once at process start**, never per request.

---

## 3. What each model is actually good for

| task | best artifact | test score | label source |
|---|---|---|---|
| **intent** (77-way) | `tfidf_linear_svm_all.joblib` | 83.18% macro-F1 `[82.55, 83.72]` | ✅ real BANKING77 ground truth |
| **priority** (3-way) | `encoders/priority_labse/` | 0.8900 macro-F1 (classical: 0.8722) | ⚠️ LLM-derived (prompt v5) |
| **sentiment** (2-way) | `encoders/sentiment_labse/` | 0.5664 negative-F1 (classical: 0.4572) | ❌ LLM-derived, inconsistent |

Priority per-class F1: Low 0.9206, Medium 0.8760, **High 0.8735**. High is the weakest class and
also the costliest to miss — a missed High is an escalation, a missed Low is nothing. If priority
drives routing, track High recall specifically rather than macro-F1.

Read the label-source column before trusting any of these in production.

**Intent is the only task with genuine ground truth.** Its labels are BANKING77's own. A score
there means what you expect it to mean.

**Priority and sentiment were trained on labels generated by prompt v5, not by humans.** A model
fit on them learns to reproduce v5, not to be correct. Measured against human annotation on the
500-row gold set, v5 itself scores 0.7722 (priority) and 0.5769 (sentiment) — so those are the
practical ceilings on real-world agreement no matter how good the classifier's test number looks.

**Sentiment deserves a specific warning.** Its 0.5664 is scored *against v5 labels* — the very
target it was trained on. Only half-agreeing with your own training target means the target is not
a consistent function: near-identical tickets carry different labels. `best_epoch: 1` (it peaked
after one epoch of three, then degraded) is the same story from another angle. Treat sentiment as a
soft advisory signal, not a routing decision, until the labels are fixed. Relabeling is the lever
here, not a bigger model — a v6 pilot scored 0.6875 vs v5's 0.4615 on holdout.

Also note: **accuracy is a trap on sentiment.** The test set is ~3.28% Negative, so predicting
"Neutral" for everything scores 96.7%. Always report `negative_f1`.

### Do you actually need the encoder?

For **priority**, probably not. LaBSE buys ~+0.017 macro-F1 over classical for 40× the size and a
GPU dependency — a poor production trade. (You'd need to refit and dump a classical priority model
first; see §1.) For **sentiment** the encoder gain is large in relative terms (+0.11) but lands at
a weak absolute number on unreliable labels.

---

## Obtaining the encoder weights

They are not in git. Either regenerate them or fetch them from the Kaggle run that produced them.

**Regenerate** (~20 min per task on a Kaggle T4):

```bash
python ml/kaggle/runner.py sync                     # upload code + data
python ml/kaggle/runner.py run  --job train_encoders --models labse \
       --task sentiment --fit-portion train+dev --eval-portion test --save-models
python ml/kaggle/runner.py status --job train_encoders --watch
python ml/kaggle/runner.py fetch --job train_encoders   # lands them here
```

Swap `--task priority` for the other one. `fetch` copies any checkpoint directory in the kernel
output into `ml/models/encoders/`.

Requires a **phone-verified** Kaggle account. Without verification Kaggle silently grants neither
GPU nor internet, and the run fails several minutes in with DNS errors reaching HuggingFace — the
log's first lines print `cuda True/False`, so check there before assuming a code problem.

**To share them with other people**, push to the HuggingFace Hub (free, private repos allowed) or
attach them as a Kaggle Dataset. Do not commit them, and do not add them to LFS without checking
the quota first.
