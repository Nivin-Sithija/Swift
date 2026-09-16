---
language:
- en
- si
- ta
license: cc-by-4.0
base_model: sentence-transformers/LaBSE
pipeline_tag: text-classification
tags:
- banking
- sentiment-analysis
- ticket-triage
- labse
- multilingual
- code-mixed
- sinhala
- tamil
metrics:
- f1
---

# Swift-Support LaBSE Sentiment Classifier (v1.0)

A fine-tuned **LaBSE** (Language-Agnostic BERT Sentence Embedding) model that flags a banking
support ticket as **Negative** or **Neutral**, across five language tracks. Built for the **Swift**
support-ticket triage project, alongside
[`Swift-Support/labse-intent-1.0`](https://huggingface.co/Swift-Support/labse-intent-1.0) and
[`Swift-Support/labse-priority-1.0`](https://huggingface.co/Swift-Support/labse-priority-1.0).

## Model details

* **Base architecture:** `sentence-transformers/LaBSE` (471M parameters, 501k vocabulary)
* **Task:** binary text classification (sentiment)
* **Classes:** `Neutral`, `Negative`
* **Languages:** English, Sinhala, Tamil, Singlish (romanized Sinhala), Tanglish (romanized Tamil)
* **Regime:** one multilingual model over all five tracks — *not* five per-language models

The headline metric is **Negative-F1**, never accuracy. About **94% of tickets are Neutral**, so a
model that predicts "Neutral" for everything scores ~0.94 accuracy and is useless. `Negative` is the
minority class, the one that matters for escalation, and the only one worth scoring on.

## Evaluation

Trained on `train+dev` (49,990 rows = 9,998 tickets × 5 languages), scored **once** on the held-out
test set (15,395 rows = 3,079 tickets × 5 languages, 975 Negatives). Frozen split `e7b5934392cd`;
test tickets come from the official BANKING77 test file and were never used for model selection.

**Pooled test Negative-F1: 0.7138** (precision 0.7601, recall 0.6728)

Macro-F1 0.8478 · accuracy 0.9658 · predicted 863 Negatives against 975 true.

### Against the alternatives (pooled test Negative-F1, same labels, same split)

| model | Negative-F1 |
|---|---:|
| **LaBSE (this model)** | **0.7138** |
| `gemma-3-1b` (LoRA, single-task) | 0.7126 |
| `gemma-3-1b` joint multi-task, shared head | 0.7048 |
| `gemma-3-1b` joint multi-task, 3 heads | 0.7042 |
| TF-IDF + LinearSVC (classical champion) | 0.6663 |
| TF-IDF + logistic regression | 0.6415 |

LaBSE beats the classical champion by **+0.048**. The Gemma decoder is a statistical tie (+0.001),
not a worse model — it is simply larger to serve for no measured gain.

### Per-epoch

| epoch | Negative-F1 | precision | recall |
|---|---:|---:|---:|
| 1 | 0.6749 | 0.5939 | 0.7815 |
| 2 | 0.7115 | 0.7697 | 0.6615 |
| **3** | **0.7138** | 0.7601 | 0.6728 |

Best epoch is 3 of 3 — still improving when training stopped, which is what a consistent labelling
target looks like. Under the older v5 labels the same model peaked at **epoch 1** and then degraded,
the signature of memorising contradictory labels. The relabel fixed that.

## ⚠️ Label provenance — this model was trained on v8 labels

The sentiment labels are **LLM-generated, not human**. They went through one major revision:

| prompt | agreement with human annotation (500-ticket gold set) | κ |
|---|---:|---:|
| v5 (superseded) | 0.5769 Negative-F1 | 0.55 |
| **v8 (this model)** | **0.7812 Negative-F1**, 97.2% agreement | **0.766** |

v8 replaced 711 of 13,077 sentiment labels on 2026-08-19 and nearly doubled the labelling rule's
agreement with a human annotator. **This model's 0.7138 sits just below its 0.7812 ceiling** — a
coherent place to be, with real headroom still available.

**Do not compare this score to any Swift sentiment number recorded before 2026-08-19.** Those score
against v5 labels on a test set with 505 Negatives rather than 975; the metric moves on the label
change alone. The previous LaBSE checkpoint scored 0.5664 on v5 and is not this model.

## Usage

```python
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

repo = "Swift-Support/labse-sentiment-1.0"
tok = AutoTokenizer.from_pretrained(repo)
model = AutoModelForSequenceClassification.from_pretrained(repo).eval()

texts = ["Someone has taken money from my account and nobody is helping me!",
         "How do I activate my new card?"]

with torch.no_grad():
    batch = tok(texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
    probs = model(**batch).logits.softmax(-1)

for text, p in zip(texts, probs):
    print(model.config.id2label[int(p.argmax())], f"{p.max():.3f}", "|", text)
```

Two things that will silently corrupt results if you get them wrong:

* **`max_length=128` must match training.** It is not stored in the checkpoint.
* **Read the label from `model.config.id2label`, never a hardcoded index.** This checkpoint carries
  an explicit mapping (`0: Neutral, 1: Negative`). A wrong guess does not raise — it silently
  **inverts** every prediction.

Cost: ~1.9 GB resident, roughly 100–300 ms per ticket on CPU. Load once at process start.

## Training

| | |
|---|---|
| base | `sentence-transformers/LaBSE` |
| fit portion | `train+dev`, 49,990 rows |
| epochs | 3 (best epoch: 3 of 3) |
| learning rate | 2e-5 |
| batch size | 32 |
| max sequence length | 128 |
| class imbalance | `class_weight` (balanced) |
| precision | fp16 |
| hardware | Kaggle T4, ~112 rows/s, 22 min wall |

## Limitations

* **Treat as advisory, not routing.** At 0.7138 Negative-F1 with 0.67 recall, roughly a third of
  genuinely negative tickets are missed. This is a prioritisation signal, not an escalation gate.
* **Labels are LLM-generated** — see the ceiling section. The model is measured against a rule that
  itself agrees with a human 97.2% of the time (κ 0.77), not against human judgement directly.
* **Romanized text is synthetic.** Singlish is rule-generated from Sinhala and Tanglish is
  machine-translated, so both are cleaner and more regular than text a human would type. No
  romanized-specific conclusion from this model should be trusted until re-measured on human-typed
  data.
* **No per-language test breakdown exists** for this model — it was scored pooled only.
* **Not calibrated.** Softmax scores are not probabilities to threshold on without re-calibrating;
  a CV-tuned threshold failed to transfer to test in this project (−0.005 on the champion).
* **Domain-bound.** Derived from BANKING77; behaviour outside retail-banking support is untested.
* Single seed, no repeats — no variance estimate.

## Citation & provenance

Derived from [BANKING77](https://huggingface.co/datasets/PolyAI/banking77) (PolyAI, CC-BY-4.0),
translated into Sinhala and Tamil and romanized into Singlish and Tanglish. Sentiment labels were
generated by an LLM prompt (v8) and benchmarked against human annotation as described above.

Training data: [`Swift-Support/swift-support-tickets-1.0`](https://huggingface.co/datasets/Swift-Support/swift-support-tickets-1.0)
