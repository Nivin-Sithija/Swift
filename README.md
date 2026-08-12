<h1 align="center">
  <img src="frontend/public/logo.png" alt="" width="44" height="44" align="center" />
  &nbsp;Swift
</h1>

Trilingual (Sinhala / English / Tamil), multimodal AI support-ticket triage for banking and fintech. Tickets — text, voice, or image — are transcribed/OCR'd, classified by intent, priority and sentiment, then routed: routine questions get a RAG-grounded draft reply, fraud and negative-sentiment tickets escalate to a human.

Pipeline: BANKING77 → translate + romanize to 5 tracks → LLM-label sentiment/priority → frozen split → classifier bake-off → serve.

## Layout

- `datasets/`: 5 language tracks, translation, romanization and labeling scripts.
- `ml/swiftbench/`: shared harness — frozen split, metrics, baselines, result format.
- `ml/scripts/`, `ml/configs/`, `ml/kaggle/`: CLI training runs (intent only) and their committed configs; Kaggle T4 job runner.
- `ml/OCR/`: image→text pipeline — dataset generator, Tesseract/EasyOCR evaluation, CER analysis.
- `ml/models/`, `ml/predictions/`, `ml/reports/`: run artifacts. **`ml/reports/RESULTS.md` is the master results report.**
- `notebooks/modeling/`: the experiment notebooks that drive swiftbench.
- `research/`: primary-source papers backing each modeling decision.
- `backend/`, `frontend/`: FastAPI + PostgreSQL service; Vite + React prototype.
- `rag/`, `docs/`, `context/`: RAG sources; formal documents; spec and architecture notes.

## Dataset

[BANKING77](https://huggingface.co/datasets/PolyAI/banking77) → labeled, multi-script, five-track corpus. One ticket exists five times under one `id`.

- Tracks: `english`, `sinhala`, `singlish` (romanized Sinhala), `tamil`, `tamilish` (romanized Tamil).
- Schema, all 10 CSVs: `id, text_en, text, category, sentiment, priority`. **`category` is the column, `intent` is the task.**
- 9,998 train / 3,079 test per track; 65,385 rows total.
- `intent` = genuine BANKING77 ground truth. `sentiment` / `priority` = **LLM-derived, prompt v5** — a classifier trained on them learns to reproduce v5, not truth.
- Sinhala hand-corrected to colloquial code-mixed; Singlish rule-generated preserving loanword spelling (`card`, not `kad`); Tamil Gemini-translated, no hand pass yet.
- Audits never mutate source CSVs — they emit review files for a human pass.

## Evaluations

Frozen split `e7b5934392cd` — 8,500 / 1,498 / 3,079 tickets, drawn on `id`, never regenerated. Dev ranks, test confirms once. Full workings: [`ml/reports/RESULTS.md`](ml/reports/RESULTS.md).

Floors: sentiment always-`Neutral` = 95.5% acc / **0.000** Neg-F1 · priority always-`Low` = 0.2302 · priority `intent-chained` = 0.9040 (the honest bar; the 0.9147 gold-intent version is an oracle).

| Task | Champion | Test | Beats | Label ceiling |
|---|---|---:|---|---:|
| intent | LaBSE fine-tuned, `all` | **88.54%** macro-F1 | classical 83.18% | 1.00 |
| sentiment | LaBSE fine-tuned, `class_weight` | **0.5664** Neg-F1 | classical 0.4572 | 0.5769 |
| priority | LaBSE fine-tuned, `class_weight` | **0.8900** macro-F1 | classical 0.8722 | **0.7722** |

Intent's number comes from the **official** split (9,998/3,079 per track), not the frozen one — the same split its classical baseline was measured on, so the promotion comparison holds, but it does not sit in one table with the frozen-split dev figures. LaBSE clears all six +3.00pp promotion gates; XLM-R clears five and misses english by 0.10pp.

Challenged twice, held both times: Gemma 3 1B + LoRA-all ties LaBSE on all three tasks and wins none (dev); linear probing shows LaBSE wins the *frozen* probe too, so its lead predates training.

**OCR** — 2,000 synthetic ticket images (500 renders × 4 conditions), CER. Language-routed Tesseract vs an EasyOCR Latin-model baseline; **bold wins the cell**:

| Script | clean | rotation | blur | low-res |
|---|---|---|---|---|
| Latin | **9.94** / 10.14 | **30.76** / 52.58 | 34.96 / **17.54** | 55.34 / **46.58** |
| Sinhala | **11.26** / 21.81 | **33.93** / 58.20 | 39.92 / **29.11** | 64.52 / **57.07** |
| Tamil | **10.63** / 26.41 | **31.97** / 60.28 | 34.45 / **33.57** | **58.49** / 60.13 |

Routing to the `sin`/`tam` packs erases the native-script penalty on clean input — Tamil −15.78pp, Sinhala −10.55pp, all three scripts landing at ~10–11% — and wins rotation by 22–28pp. It **loses under blur and low-resolution**, which is the phone-camera case; that fallback is unmeasured. Feed Tesseract raw RGB: every OpenCV pre-processing variant tried made CER worse.

Labeling prompts vs the 500-row human gold set:

| v1 | v5 (frozen) | v6 | v7 | v8 |
|---:|---:|---:|---:|---:|
| 0.622 | **0.5769** | 0.6875 *(holdout)* | 0.6667 | **0.7812** |

## Findings

- **Labels bind sentiment, not model capacity.** Champion 0.5664 vs a 0.5769 ceiling — inside its own CI. No frozen backbone probes above the classical baseline either. Relabel before re-modelling.
- **Priority's 0.8900 is agreement with the v5 rule, not with humans** (κ=0.64, 0.7722). Quote the ceiling next to the score.
- **Class balancing beats model choice, and the highest-accuracy arm is the worst model** — 0.9281 acc / 0.3171 Neg-F1 unbalanced vs 0.9252 / 0.4061 with `class_weight`.
- **Rank on the CI.** The 0.6395 bake-off headline was the max of 168 noisy draws; all top-10 configs sat in one interval. Dev has 340 Negative *rows* but only **68 unique Negative tickets**.
- **One multilingual model, all three tasks.** Sinhala +3.35pp, Singlish +1.34pp, neutral elsewhere. No per-language specialist wins. Zero-shot to an unseen script collapses (0.085).
- **Recalibrating the category→priority table was the biggest labeling gain** — 4% → 92% on the 25 affected gold rows.
- **Negative looks like a topic construct, not polarity** — mined lexicon returns fraud/loss markers. Reproducing published lexicon correction gave a null result (CV picked α=0).
- **Positive does not exist** — Neutral 9,540 / Negative 463 / Positive 0. Downstream code must tolerate a zero-count class.
- **Tamilish is the weak track everywhere** — intent 61.05% classical / 72.04% fine-tuned, priority 0.7994–0.8229. Cause: unstandardized romanization Singlish avoids. Transformers narrow it by ~11pp and it still trails every other track by ~18pp.
- **Indic-specialist encoders lose to multilingual ones on a mixed-script corpus** — on pooled intent, MuRIL 62.10% and IndicBERT 76.24% land *below* the 83.18% classical baseline that XLM-R and LaBSE clear by 5pp. IndicBERT buys 0.20pp on Tanglish; informal romanized text wants web-scale pretraining, not curated Indic corpora.
- **Never pre-process images for Tesseract.** Binarization spiked CER past 80%; even deskew+grayscale alone cost Sinhala 4.3pp. Its internal Leptonica already does adaptive localized binarization — external OpenCV work blinds it. Same silent-failure shape as the tokenizer defect.
- **A pooled OCR CER hides an inverted ranking** — Tesseract wins clean and rotation, EasyOCR wins blur and low-res. Report CER by script *and* condition or the engine recommendation flips silently.
- **Default tokenizers silently drop Indic script** — sklearn's `token_pattern` discarded 40.1% of Sinhala and 69.3% of Tamil characters. Fixed; always measure character preservation.
- **Fertility does not predict encoder quality** — the screen's winner had the worst fertility; MuRIL led it only by mapping ⅔ of Sinhala to `[UNK]`.
- **Romanized conclusions are unresolved** — Singlish is rule-generated, Tamilish machine-translated, so romanized-specific techniques test a function we applied.

## Next

1. **Roll out prompt v8** beyond the staging file — +0.20 gold Neg-F1, larger than any modelling gain measured.
2. **Reconcile the two intent workstreams.** LaBSE 88.54% is banked on the official split; mmBERT 0.9280 / LaBSE 0.9224 / Gemma 0.9243 sit on frozen-split dev. Neither has been run against the other's split, and no intent checkpoint is saved.
3. **Chain OCR into the classifier and measure end-to-end.** CER stops at 10–11% on clean images; what that costs in intent macro-F1 is the number the multimodal claim actually rests on.
4. **Close the Tamilish gap** — the only double-digit per-language deficit, still ~18pp after fine-tuning.
5. **Handle degraded images.** Tesseract loses to EasyOCR on blur and low-res; a condition-aware fallback, or a better engine (Cloud Vision, Surya, PaddleOCR), is untested.
6. **Collect human-typed romanized tickets** — blocks Strategy A, code-switch augmentation and the TwHIN-BERT claim. Real photographs are the same gap on the image side: every CER here is synthetic and optimistic.
7. **Measure single-request latency.** The 0.24–0.64 ms/sample figure is batched throughput, not a check against the 100ms serving budget — and OCR, the slower half, has no published latency at all.
8. **Untested and open:** joint multi-task fine-tuning, LoRA adapters over one shared backbone, a fair LoRA sweep at lr ~1e-4.
