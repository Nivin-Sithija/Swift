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
- intent-classification
- labse
- multilingual
- code-mixed
- sinhala
- tamil
metrics:
- f1
---

# Swift-Support LaBSE Intent Classifier (v1.0)

Fine-tuned **LaBSE** for 77-way banking intent classification across English, Sinhala, Tamil
and their romanized code-mixed forms (Singlish, Tanglish). Part of the **Swift** support-ticket
triage project.

> **Card revised 2026-09-08.** The previous version reported a 3-epoch training run and
> explained the Indic specialists' failure with a mechanism the data does not support. Both are
> corrected below, and the correction is kept visible rather than quietly overwritten. See
> *What changed and why*.

## Model details

| | |
|---|---|
| Base model | `sentence-transformers/LaBSE` (501k vocabulary) |
| Task | 77-way intent classification (BANKING77 taxonomy) |
| Languages | English, Sinhala, Tamil, Singlish (romanized Sinhala), Tanglish (romanized Tamil) |
| Metric | **macro-F1** over 77 classes |
| Split | frozen, identity `e7b5934392cd` — drawn once on ticket `id`, then fanned to all five tracks |
| Training data | [`Swift-Support/swift-support-tickets-1.0`](https://huggingface.co/datasets/Swift-Support/swift-support-tickets-1.0) |
| Licence | CC-BY-4.0 |

**The split matters and is not the official BANKING77 split.** The same ticket exists five
times under one `id`. Scores here are macro-F1 pooled over all five tracks of the frozen
split, so they are not comparable to BANKING77 leaderboard numbers, which are English-only
accuracy on the official split.

## Evaluation

Six encoders, identical budget (6 epochs, lr 2e-5, batch 32, max length 128, fp16, seed 42),
fitted on `train` and scored on `dev`.

### Pooled and per-track macro-F1 (dev, %)

| model | English | Sinhala | Tamil | Singlish | Tanglish | **pooled** |
|---|---:|---:|---:|---:|---:|---:|
| **mmBERT** | 93.97 | 93.71 | 93.75 | 92.08 | 91.22 | **92.94** |
| **LaBSE** (this model) | 93.09 | 94.05 | 93.42 | 92.40 | 91.70 | **92.93** |
| XLM-R base | 92.68 | 93.61 | 92.40 | 90.75 | 91.55 | 92.19 |
| IndicBERT | 91.83 | 90.00 | 92.90 | 90.69 | 89.82 | 91.04 |
| TwHIN-BERT | 91.20 | 92.12 | 90.87 | 89.99 | 89.96 | 90.82 |
| MuRIL | 90.03 | **76.33** | 90.09 | 88.79 | 90.23 | 87.03 |

**LaBSE and mmBERT are statistically indistinguishable on this task.** Paired bootstrap over
1,000 resamples: Δ = −0.0001, 95% CI [−0.0045, +0.0046], p = 0.944. This card previously
called LaBSE "the intent champion". It is not; it ties. Either model is a defensible choice,
and mmBERT is the smaller of the two.

**These are dev numbers.** The held-out test numbers are now available — see below.

## Held-out test results

Fitted on `train+dev` (49,990 rows), scored **once** on the frozen split's test set
(15,395 rows). `epoch_selection = final-epoch` with `best_epoch = 6 of 6` for all three, so
no epoch-selection bias is possible.

| model | pooled | english | sinhala | tamil | singlish | tamilish |
|---|---:|---:|---:|---:|---:|---:|
| **LaBSE** (this model) | **88.35** | 94.12 | **93.19** | **93.29** | **90.34** | 69.28 |
| XLM-R base | 88.01 | 94.02 | 92.44 | 91.51 | 89.87 | **70.67** |
| mmBERT | 86.80 | 93.74 | 91.23 | 91.47 | 90.13 | 65.66 |

On dev, mmBERT and LaBSE tied and XLM-R trailed. On test the order is LaBSE > XLM-R >
mmBERT. **This is a point estimate, not a tested difference** — that run wrote no per-row
predictions, so no paired test is possible. Do not read it as mmBERT being beaten.

### ⚠️ The tamilish column is a corpus defect, not a model result

Tamilish scores 69.28 on test against **91.70 on dev**, a drop no other track shows
(english, sinhala and tamil move 1–3 points; singlish 2). The cause is a vocabulary
discontinuity between the train and test renderings of that one track:

| track | OOV vs train (dev) | **OOV vs train (test)** |
|---|---:|---:|
| english | 14.8% | 20.3% |
| singlish | 13.3% | 27.8% |
| sinhala | 13.7% | 30.2% |
| tamil | 21.6% | 29.8% |
| **tamilish** | 22.3% | **60.3%** |

The tamilish rendering of the BANKING77 **test** file was produced by a different
transliteration process from the tamilish rendering of the **train** file. Tamilish test
text also averages more characters but fewer words than tamilish train, and is the only
track with duplicate test strings.

**Do not quote 69.28 as this model's ability to handle romanized Tamil.** It measures a
train/test mismatch in the corpus. The effect is task-dependent — priority on tamilish is
0.8142 against english's 0.9229, a gap rather than a collapse — because a 3-way task
tolerates vocabulary drift that a 77-way task does not. This is being fixed for corpus
v1.1.

## What changed and why

**1. The old table was trained for 3 epochs and understated the whole roster.** Five of six
models were still improving when training stopped at 6, so even these numbers are a lower
bound. The effect on MuRIL was severe — its Tamil score was reported at 66.01% and is 90.09%
at an adequate budget.

**2. The old explanation of the Indic specialists' failure was backwards.** The previous card
said MuRIL and IndicBERT "failed outright on the pooled and code-mixed tracks because their
smaller vocabularies couldn't handle heavy romanization or English slang".

The data says the opposite. MuRIL's romanized tracks are among its *best*: Tanglish 90.23,
Singlish 88.79. It fails on exactly one track — **native-script Sinhala, at 76.33**, 13.7
points below its own English. The mechanism is in its tokenizer:

| MuRIL tokenizer | English | Sinhala | Tamil | Singlish | Tanglish |
|---|---:|---:|---:|---:|---:|
| `[UNK]` rate (% of characters) | 0.0 | **64.5** | 0.0 | 0.0 | 0.0 |

MuRIL maps **64.5% of Sinhala characters to `[UNK]`** — the characters are destroyed before
the first transformer layer, and no amount of fine-tuning recovers them. Every other model in
the roster is at 0.0% on every track.

So the correct claim is not "specialists cannot handle romanization". It is **"check the
tokenizer's `[UNK]` rate on your script before fine-tuning anything"**. Romanization is
handled fine by every model here; script coverage is what varies.

Note also that token *fertility* (tokens per word) does **not** predict downstream quality
across this roster — Spearman ρ = −0.035 against per-language deficit, versus −0.521 for
`[UNK]` rate. Fertility is a cost; `[UNK]` is destruction. They are often conflated.

## Intended use and limitations

**Intended:** routing inbound banking support tickets to one of 77 intents, as a triage aid
with a human in the loop.

**Out of scope:** non-banking domains (the taxonomy and vocabulary are banking-specific);
languages or scripts outside the five tracks; any customer-facing decision taken without
review.

**Performance is not uniform across tracks.** Tanglish trails English on every system
measured. Expect worse service for customers writing in transliteration — which, in this
setting, correlates with who those customers are.

**Intent labels are BANKING77's human gold**, unlike this project's sentiment and priority
labels, which are LLM-generated. That makes intent the most trustworthy of the three tasks
here.

## Usage

```python
from transformers import pipeline

classifier = pipeline("text-classification", model="Swift-Support/labse-intent-1.0")
print(classifier("I lost my credit card yesterday, please help me cancel it"))
```

---

## Citation

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
