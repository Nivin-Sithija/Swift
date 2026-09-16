<!-- Shared citation block. Paste verbatim into every Swift-Support card so the citation
     is identical across the org. ACTION REQUIRED before publishing: see the note at the
     foot of this file. -->

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

---

<!-- BEFORE PUBLISHING, CONFIRM:

  1. AUTHOR ORDER. The three names are confirmed. The ORDER is not — Sithija Seneviratne
     is listed first as the repository owner, which is an assumption, not a decision. Confirm
     the intended order, and whether a supervisor belongs on the list. Note also that the
     corpus and the models may warrant different author lists (translators and annotators on
     one, implementers on the other).

  2. Once the paper has a venue or a preprint DOI, replace both @misc entries' `note` fields
     with the real citation, and keep the @misc entries as the "corpus" and "models"
     citations alongside it.

  3. Consider whether the corpus and models should carry the same author list. They often
     differ (annotators and translators on the corpus; implementers on the models).
-->
