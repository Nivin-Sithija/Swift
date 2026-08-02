# Encoder experiments — findings, results & decisions

Frozen split `e7b5934392cd` (train 42,500 / dev 7,490 / test 15,395, 5 languages).
Headline metrics: **sentiment = Negative-F1**, **priority = macro-F1** (never accuracy — 95.5% of
tickets are Neutral). Encoders fine-tuned on Kaggle T4 GPUs via `ml/kaggle/runner.py`; classical
baselines are the TF-IDF (word `indic-nlp` + char_wb) + linear model pipeline.

## Bottom line

**Ship one multilingually fine-tuned LaBSE.** It is the best model on both tasks and every language,
and it beats the classical champion on the held-out test set for both tasks:

| task | metric | classical (test) | LaBSE (test) | margin | verdict |
|---|---|---|---|---|---|
| sentiment | Negative-F1 | 0.464 | **0.566** | +0.10 | clears classical CI |
| priority | macro-F1 | 0.872 | **0.890** | +0.018 | clears classical CI (0.8831) |

Protocol for test numbers: winners refit on **train+dev** (49,990 rows), scored **once** on the
official held-out test set.

## 1. Sentiment encoder bake-off

Pooled dev, then final test (fit train+dev). All at 3 epochs, lr 2e-5, batch 32, class_weight.

| model | dev Neg-F1 | test Neg-F1 |
|---|---|---|
| **labse** | 0.633 | **0.566** |
| mmbert | 0.620 | 0.532 |
| canine-c | 0.532 | 0.470 |
| xlmr-base | 0.501 | 0.540 |
| tfidf-svm (classical) | 0.595 | 0.464 |
| tfidf-logreg (classical) | 0.572 | 0.450 |
| sinbert-large / sinhalaberto | — | Sinhala-only (unfair on pooled) |

**Decisions / notes**
- On **dev**, LaBSE (0.633) only tied the classical champion within the CI (~±0.08). On **test**
  (505 Negatives vs dev's 340, tighter CI) the encoders separate cleanly: LaBSE +0.10 over classical.
- Classical dropped ~0.13 dev→test; the subword encoders dropped only 0.07–0.09 and **xlm-roberta
  rose** (0.501→0.540). Encoders generalize better here.
- canine-c (character-level) ≈ classical — the char model does not justify itself.

## 2. Per-language specialization (dilution hypothesis) — sentiment

Does one multilingual model dilute per-language performance? Tested mono vs multi on three encoders.
Per-language dev cells have ~14–68 Negatives each, so CIs are wide (~±0.1) — read directions.

Multi-trained dev Negative-F1:

| model | english | sinhala | singlish | tamil | tamilish |
|---|---|---|---|---|---|
| **labse** | 0.657 | 0.671 | **0.647** | 0.632 | 0.551 |
| twhin-bert | 0.653 | 0.613 | 0.559 | 0.626 | 0.534 |
| xlmr-base | 0.584 | 0.487 | 0.489 | 0.485 | 0.469 |

**Decisions / notes**
- **LaBSE is best on every language, including the romanized tracks.** No specialized model beat it.
- For LaBSE, monolingual gives a small native-script edge (tamil +0.048, sinhala +0.025) but **loses
  on singlish** — romanized leans on cross-lingual transfer. All deltas within noise. → **Do not ship
  per-language models.**
- **xlm-roberta is the weakest** of the three per-language.

## 3. Code-mix model for romanized (TwHIN-BERT)

`model-research.md` §5 names TwHIN-BERT as the "process romanized directly" (Strategy B) model.

- **It does not win on romanized here.** LaBSE beats it on singlish (0.647 vs 0.559, −0.088) and
  tamilish. TwHIN-BERT does clearly beat xlm-roberta.
- **Caveat:** our Singlish is *rule-generated* from Sinhala (clean, consistent) and Tamilish is
  machine-translated — an optimistic upper bound. TwHIN-BERT's edge would most plausibly appear on
  **real human-typed** code-mixing, which we do not have. → **Revisit with real romanized data.**

## 4. LoRA per-language (peft)

Freeze LaBSE, train a low-rank adapter (+classifier) per language and a multi baseline.

| language | ft-multi | ft-mono | lora-multi | lora-mono |
|---|---|---|---|---|
| english | 0.657 | 0.667 | 0.382 | 0.323 |
| sinhala | 0.671 | 0.696 | 0.477 | 0.322 |
| singlish | 0.647 | 0.630 | 0.394 | 0.263 |
| tamil | 0.632 | 0.680 | 0.424 | 0.322 |
| tamilish | 0.551 | 0.553 | 0.362 | 0.274 |

**Decisions / notes**
- **LoRA loses by 0.2–0.3 everywhere**; per-language LoRA (lora-mono) is the worst config.
- **Caveat:** LoRA ran at full-FT hyperparameters (lr 2e-5). LoRA conventionally needs higher LR
  (~1e-4) and more epochs — so this shows "drop-in LoRA at these settings fails," not "LoRA can't
  work." → **Not competitive as a drop-in; a fair LoRA test needs its own hyperparameter sweep.**

## 5. Priority encoder bake-off + final test

Priority had only classical baselines (tfidf-svm test macro-F1 **0.8722**, CI [0.8605, 0.8831];
label ceiling ~0.77–0.80). Ran the full roster on `task=priority`.

Pooled dev macro-F1: labse 0.9168, xlmr-base 0.9162, mmbert 0.9148, twhin-bert 0.891, canine-c
0.879 (classical dev 0.9028). Sinhala-only models far below (unfair pooled).

Final test (fit train+dev):

| model | test macro-F1 | vs classical 0.8722 |
|---|---|---|
| **labse** | **0.8900** | +0.018 |
| mmbert | 0.8887 | +0.017 |
| xlmr-base | 0.8872 | +0.015 |

**Decisions / notes**
- Encoders beat classical on priority test by ~0.017, and **labse/mmbert clear the classical CI
  upper bound (0.8831)** — a real, if modest, win despite priority being near its label ceiling.
- twhin-bert and canine-c sit below the classical bar on priority.

## Cross-cutting decisions

1. **Champion = multilingually fine-tuned LaBSE** for both sentiment and priority.
2. **No per-language models, no LoRA, no TwHIN-BERT** — none beat multilingual LaBSE on our data.
3. **Romanized tracks are unresolved by our data** (synthetic Singlish/Tamilish). Real human-typed
   romanized text is required before trusting any romanized-specific conclusion; transliteration
   (Strategy A) was deliberately not run for the same reason.
4. **Rank on the confidence interval, not the point estimate** — several dev leads did not survive
   to test, and per-language cells are too small to order reliably.

## Reproducing

- Run JSONs: `ml/reports/runs/{sentiment,priority}__*.json` (each stamped with the split sha).
- Notebooks: `32_final_test_classical`, `33_final_test_encoders`, `34_per_language_findings`,
  `35_priority_encoders` (all under `notebooks/modeling/`).
- GPU driver: `ml/kaggle/runner.py` (T4 pinned; supports `--task`, `--fit-portion`, `--eval-portion`);
  kernels in `ml/kaggle/kernels/`.
