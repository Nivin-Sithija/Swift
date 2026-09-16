---
title: Swift - Multilingual Banking Ticket Classifier
emoji: 🎫
colorFrom: blue
colorTo: indigo
sdk: static
pinned: false
---

# Swift — Multilingual Banking Ticket Classifier

Swift is a research organization for multilingual NLP resources built around
customer support ticket triage in Sri Lankan banking and fintech. We host datasets, models,
and evaluation artifacts for Sinhala, Tamil, English, and romanized code-mixed text.

Our current work focuses on the **Swift Support Tickets corpus**: a trilingual, five-track
ticket collection derived from BANKING77 and extended into the scripts customers actually
write in. The project supports research in low-resource NLP, script robustness, code-mixed
text classification, and annotation-quality measurement.

This is a research organization. It is not affiliated with, endorsed by, or a publication
channel for any bank or financial institution, and the tickets are not real customer records.

## Featured Resources

- **Dataset:** https://huggingface.co/datasets/Swift-Support/swift-support-tickets-1.0
- **Intent model:** https://huggingface.co/Swift-Support/labse-intent-1.0
- **Sentiment model:** https://huggingface.co/Swift-Support/labse-sentiment-1.0
- **Priority model:** https://huggingface.co/Swift-Support/labse-priority-1.0
- **Code repository:** https://github.com/Nivin-Sithija/Swift
- **Source corpus:** https://huggingface.co/datasets/PolyAI/banking77
- **Paper:** in preparation

## Current Dataset

### Swift Support Tickets 1.0

A five-track support-ticket corpus covering Sinhala, Tamil, English, and their romanized
code-mixed forms.

The dataset includes:

- **65,385 rows** — 13,077 tickets rendered in each of five language tracks
- **Five tracks:** English, Sinhala, Tamil, Singlish (romanized Sinhala), Tanglish (romanized Tamil)
- **77-way intent labels** inherited from BANKING77's human gold annotation
- **Sentiment labels** (`Neutral` / `Negative`; 12,253 / 824 per ticket)
- **Priority labels** (`Low` / `Medium` / `High`; 7,001 / 4,790 / 1,286 per ticket)
- A **frozen train/dev/test split**, identity `e7b5934392cd`, drawn once on ticket `id` and
  fanned out to all five tracks
- A 500-ticket human-annotated benchmark subset used to measure label quality

The five renderings of a ticket share one `id`. **The split is drawn on `id`, not on rows** —
splitting randomly by row puts a ticket's English copy in train and its Sinhala copy in test,
and every score after that measures memorisation rather than generalisation.

> **Why the viewer says ~131k rows.** The corpus is **65,385 unique rows**, shipped twice: once
> as the pooled `all` configuration (42,500 train + 7,490 validation + 15,395 test) and once as
> five per-language configurations (13,077 rows each). The dataset viewer sums every
> configuration, giving 130,770. Load `all` **or** the per-language configs — never both, or
> every row is duplicated.

## Research Context

This organization supports the research project:

**Swift: Multilingual Support-Ticket Triage for Sinhala, Tamil and English, Including
Romanized Code-Mixed Text**

The work covers an end-to-end triage pipeline — intent, sentiment and priority — evaluated
across classical, encoder and decoder baselines on a single frozen split, with paired
significance testing and an explicit measurement of the label ceiling.

Two findings shape how these resources should be used:

**Multilingual pretraining transfers across languages it has seen, not across scripts it has
not.** A fine-tuned multilingual encoder beats a TF-IDF baseline by a significant margin on
native-script tracks, and by an amount indistinguishable from zero on both romanized tracks —
which is how a large share of real support traffic is written.

**Label quality, not model capacity, binds the sentiment task.** Agreement between the shipped
sentiment labels and a human annotator is 0.7931 negative-F1. The best model reaches 90% of
that, so further modelling effort is likely worth less than effort spent on labels.

## Intended Uses

Resources hosted by this organization are intended for:

- Multilingual and low-resource NLP research
- Sinhala and Tamil language technology, including romanized and code-mixed text
- Script robustness and tokenizer evaluation
- Support-ticket triage, intent classification and text classification research
- Annotation quality, label noise and ceiling-estimation research
- Fairness evaluation across language and script

## Responsible Use

**Only the intent labels are human ground truth.** `category` is inherited from BANKING77 and
is real human annotation. `sentiment` and `priority` are **LLM-generated** from a documented
prompt and benchmarked against a hand-annotated subset. A model scoring 0.89 against the
priority labels has learned the labelling rule, not human judgement — report both numbers.

**Never report accuracy on sentiment.** Roughly 94% of tickets are `Neutral`, so a
majority-class predictor exceeds 0.93 while detecting nothing. The headline metric is
**Negative-F1**. Priority is reported as macro-F1 for the same reason.

**Performance is not uniform across languages.** Every system measured performs worst on
romanized Tamil and best on English, with a spread of over 20 points on sentiment. Anyone
deploying these models should expect materially worse service for customers writing in
transliteration, and should treat that as a fairness property to measure rather than a
footnote.

**Sentiment here is closer to topic than to tone.** A predictor given only the intent label
and no text at all reaches half the best text model's Negative-F1. Read a `Negative`
prediction as "this ticket concerns a class of problem that tends to be serious", not as
"this customer is angry".

These are triage aids for a human-in-the-loop workflow, not adjudicators. Do not use them for
customer-facing decisions without review.

## Citation

**Citing BANKING77 alone is not sufficient attribution.** BANKING77 supplies the English text
and the 77-way intent labels — 20% of the rows and one of the three label columns. The four
other language tracks, both added label columns, and the frozen split are this project's work:

| | |
|---|---|
| Rows whose text is **new** (Sinhala, Tamil, Singlish, Tanglish) | **52,308 of 65,385 — 80%** |
| Rows inherited from BANKING77 (English) | 13,077 — 20% |
| Label columns inherited | 1 (`category` / intent) |
| Label columns **added** | 2 (`sentiment`, `priority`) — 26,154 per-ticket assignments |
| Split | the frozen `id`-level split is this project's |

If you use the translated tracks, the sentiment or priority labels, the frozen split, or any
of the models, **cite this work**. If you additionally use the English text or the intent
labels, cite BANKING77 as well. Both are CC-BY-4.0, so attribution is a licence condition.

### The corpus

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

### The models

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

### BANKING77 — source of the English text and the intent labels

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

## Project Team

- Sithija Seneviratne
- Ruththiragayan Sutharsan
- Shazan Shaheed

## Contact

For code, reproducibility notes, or issue reports, use the companion repository:

https://github.com/Nivin-Sithija/Swift
