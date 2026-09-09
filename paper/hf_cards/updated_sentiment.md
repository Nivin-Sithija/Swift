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
| **v8 (this model)** | **0.7931 Negative-F1**, 97.6% agreement | **0.780** |

v8 replaced 711 of 13,077 sentiment labels on 2026-08-19 and nearly doubled the labelling rule's
agreement with a human annotator. **This model's 0.7138 reaches 90.0% of its 0.7931 ceiling.**

> **Corrected 2026-09-08.** This card previously gave the v8 ceiling as 0.7812 (97.2% agreement,
> κ = 0.766). That figure scored the **prompt's raw output**, not the labels actually shipped in the
> dataset — the two differ on 8 of the 500 gold tickets. Against the shipped labels, which are what
> this model trained on, the ceiling is **0.7931** (95% CI [0.6667, 0.8956]; agreement 0.976,
> κ = 0.780).
>
> The interval is wide because the gold set holds only **31 Negative tickets, annotated by one
> person**. Treat 0.7931 as a point estimate with real uncertainty, not a hard bound — it is the
> weakest link in every claim on this card.

**Do not compare this score to any Swift sentiment number recorded before 2026-08-19.** Those score
against v5 labels on a test set with 505 Negatives rather than 975; the metric moves on the label
change alone. The previous LaBSE checkpoint scored 0.5664 on v5 and is not this model.

## Per-language results

From the same fit, sliced by track (3,079 tickets and 195 Negatives each):

| track | script | Negative-F1 |
|---|---|---:|
| English | Latin (native) | 0.8032 |
| Tamil | Tamil | 0.7606 |
| Sinhala | Sinhala | 0.7234 |
| Singlish | romanized Sinhala | 0.6757 |
| Tanglish | romanized Tamil | **0.5948** |

**A 20.8-point spread.** Every track is significantly below English (paired bootstrap on the same
tickets, all CIs clear of zero). Expect materially worse service for customers writing in
transliteration.

### The advantage over TF-IDF exists only on native script

Pooled, this model beats a TF-IDF+SVM baseline by +0.0485 (95% CI [+0.0257, +0.0721], p < 0.0001).
That gain is not spread evenly:

| track | gain over TF-IDF+SVM | p |
|---|---:|---:|
| English | +0.0834 | <0.001 |
| Sinhala | +0.0822 | 0.004 |
| Tamil | +0.0357 | 0.144 |
| Singlish | +0.0124 | 0.712 |
| Tanglish | +0.0225 | 0.490 |

**On both romanized tracks the encoder's advantage is indistinguishable from zero.** Sinhala and
Singlish are the same tickets in the same language differing only in script, so the contrast can be
tested directly: the difference of differences is +0.0698 (95% CI [+0.0140, +0.1283], p = 0.012).
Romanizing the same tickets removes about 7 points of the encoder's advantage. The same test on
Tamil/Tanglish is not significant (p = 0.762), so this is established for Sinhala only.

If your traffic is predominantly romanized, this model is not measurably better than TF-IDF and
costs 1.8 GB and a GPU to serve.

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

### How to cite

**Citing BANKING77 alone is not sufficient attribution for this corpus.** BANKING77 supplies
the English text and the 77-way intent labels — 20% of the rows and one of the three label
columns. The rest is this project's work:

| | |
|---|---|
| Rows whose text is **new** (Sinhala, Tamil, Singlish, Tanglish) | **52,308 of 65,385 — 80%** |
| Rows inherited from BANKING77 (English) | 13,077 — 20% |
| Label columns inherited | 1 (`category` / intent) |
| Label columns **added** | 2 (`sentiment`, `priority`) — 26,154 new per-ticket assignments |
| Split | the frozen `id`-level split is this project's, not BANKING77's |

If you use the translated tracks, the sentiment or priority labels, the frozen split, or any
of the models, **cite this work**. If you additionally use the English text or the intent
labels, cite BANKING77 as well. Both licences are CC-BY-4.0, so attribution is a licence
condition, not a courtesy.

### This work — the corpus

```bibtex
@misc{swift_tickets_2026,
  author       = {Sithija Seneviratne and Ruththiragayan Sutharsan and Shazan Shaheed},
  title        = {Swift Support Tickets: A Multilingual Ticket-Triage Corpus for Sinhala,
                  Tamil and English, Including Romanized Code-Mixed Text},
  year         = {2026},
  publisher    = {Hugging Face},
  howpublished = {\url{https://huggingface.co/datasets/Swift-Support/swift-support-tickets-1.0}},
  note         = {Derived from BANKING77. Adds four language tracks and the sentiment and
                  priority label columns. Paper in preparation.}
}
```

### This work — the models

```bibtex
@misc{swift_models_2026,
  author       = {Sithija Seneviratne and Ruththiragayan Sutharsan and Shazan Shaheed},
  title        = {Swift: Multilingual Baselines for Support-Ticket Triage in Sinhala,
                  Tamil and English},
  year         = {2026},
  publisher    = {Hugging Face},
  howpublished = {\url{https://huggingface.co/Swift-Support}},
  note         = {Intent, sentiment and priority classifiers. Paper in preparation.}
}
```

### BANKING77 — the source of the English text and the intent labels

```bibtex
@inproceedings{casanueva2020banking77,
  author    = {Casanueva, I{\~n}igo and Tem{\v c}inas, Tadas and Gerz, Daniela and
               Henderson, Matthew and Vuli{\'c}, Ivan},
  title     = {Efficient Intent Detection with Dual Sentence Encoders},
  booktitle = {Proceedings of the 2nd Workshop on Natural Language Processing for
               Conversational AI},
  pages     = {38--45},
  year      = {2020},
  publisher = {Association for Computational Linguistics},
  doi       = {10.18653/v1/2020.nlp4convai-1.5},
  url       = {https://aclanthology.org/2020.nlp4convai-1.5/}
}
```
