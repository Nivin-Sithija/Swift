# Swift — Master Results Report

Every experiment run on the trilingual banking-ticket classifiers, with scores, in one place.
Compiled 2026-08-02 from the artifacts in `ml/reports/` (CSV/JSON), the notebooks in
`notebooks/modeling/`, and the four topic reports listed in §12.

**This file summarises; it does not replace.** Where a number here is contested or was later
retracted, §11 says so and points at the source report.

---

## 0. How to read every number in this report

| Task | Column | Headline metric | Why not accuracy |
|---|---|---|---|
| **intent** | `intent` (was `category`) | macro-F1 over 77 classes | balanced 77-way, accuracy ≈ macro-F1 |
| **sentiment** | `sentiment` | **Negative-F1** | 95.5% of tickets are Neutral — always-Neutral scores 95.5% accuracy and 0.000 Negative-F1 |
| **priority** | `priority` | **macro-F1** (Low/Medium/High) | 53/37/10 split; macro keeps `High` visible |

Two further rules the project enforces:

1. **Rank on the confidence interval, not the point estimate.** Dev holds only **68 unique Negative
   tickets**, so the sentiment CI is ≈ ±0.08. Ties inside one interval are ties.
2. **Dev ranks, test confirms — once.** Winners are refit on train+dev and scored a single time on
   the held-out test set.

### Dataset & splits

| Item | Value |
|---|---|
| Source | BANKING77 (Casanueva et al., 2020), 77 intents |
| Language tracks | `english`, `sinhala`, `singlish` (romanized Sinhala), `tamil`, `tamilish` (romanized Tamil) |
| Schema (all 10 CSVs) | `id, text_en, text, intent, sentiment, priority` |
| Rows per language | 9,998 train / 3,079 test (65,385 total across 5 tracks + originals) |
| Frozen split sha | `e7b5934392cd` — **8,500 / 1,498 / 3,079 tickets** = 42,500 / 7,490 / 15,395 rows |
| Split drawn on | `id`, once, then fanned to all 5 languages (never per-language — that would leak a ticket's English copy into train while its Sinhala twin sits in dev) |
| Cross-split leakage | **0 source IDs** appear in both train and test (65,385 rows audited) |
| Test = 3,079 not 3,080 | `atm_support` has 39 official test samples, not 40 |
| Label provenance | `intent` = genuine BANKING77 ground truth. `sentiment`/`priority` = **LLM-derived** (prompt v5) — a classifier trained on them learns to reproduce v5, not truth. See §8. |

Class prevalence:

| Portion | Tickets | Negative | Negative % | Low % | Medium % | High % |
|---|---:|---:|---:|---:|---:|---:|
| dev | 1,498 | 68 | 4.54% | 52.74 | 37.12 | 10.15 |
| test | 3,079 | 101 | 3.28% | 54.82 | 35.69 | 9.48 |

*(Test's lower Negative rate accounts for ~0.059 of the sentiment dev→test drop — see §5.5.)*

---

## 1. Experiment index — what was run, and the verdict

| # | Experiment | Task | Status | Verdict |
|---|---|---|---|---|
| 1 | Tokenizer benchmark, 3 tokenizers × 15,000 samples | — | done | `max_length=128` = 100% coverage; mBERT fails Sinhala (60.3% UNK) |
| 2 | Tokenizer fertility, 7 encoders × 2,000 rows/lang | — | done | MuRIL & mBERT disqualified (61–65% Sinhala UNK); fertility ≠ accuracy |
| 3 | Classical TF-IDF baselines, 12 models × 6 tracks | intent | done | LinearSVC best; 90.98% en → 61.05% tamilish |
| 4 | TF-IDF feature ablation (word / char / both) | intent | done | char n-grams critical; Tamil word-only −10.45pp |
| 5 | Mono vs combined (`all`) training | intent | done | Combined helps Sinhala **+3.35pp**, Singlish +1.34pp |
| 6 | Bootstrap CIs, 1,000 resamples | intent | done | All tracks ±1.0–1.5pp |
| 7 | Sentiment/priority bake-off, 336 evals | sent + prio | done | `multi` ≥ `mono`; class balancing > model choice |
| 8 | Regime study (mono / multi / zeroshot-en) | sent + prio | done | zero-shot collapses (0.085 Negative-F1) |
| 9 | 5-fold CV correction of the bake-off | sentiment | done | Headline 0.6395 → honest **0.5525 ± 0.044** |
| 10 | Final test evaluation, classical | sent + prio | done | sentiment **0.4572**, priority **0.8722** |
| 11 | Threshold tuning transfer test | sentiment | done | **Retracted** — −0.005 on test |
| 12 | Label-ceiling measurement vs human gold 500 | sent + prio | done | sentiment 0.5769, priority 0.7722 |
| 13 | Indic word-tokenizer defect + fix | all | done+fixed | 40.1% Sinhala / 69.3% Tamil characters were being discarded |
| 14 | Encoder screen, 5 candidates × 800 rows | sentiment | done | mmBERT won; fertility ranking predicted ~the reverse |
| 15 | Encoder bake-off, full data (Kaggle T4) | sentiment | done | **LaBSE 0.566 test** beats classical 0.464 |
| 16 | Encoder bake-off, full data | priority | done | **LaBSE 0.890 test** beats classical 0.872 |
| 17 | Per-language specialisation (dilution test) | sentiment | done | No mono model beats multilingual LaBSE |
| 18 | LoRA adapters (peft), mono + multi | sentiment | done | Loses 0.2–0.3 everywhere at these hyperparameters |
| 19 | Lexicon correction (Senevirathna et al.) | sentiment | done | **Null result** — CV selected α = 0 |
| 20 | Prompt versions v1 / v4 / v5 vs gold 500 | labels | done | v5 frozen; priority on 4 recalibrated categories 4% → 92% |
| 21 | Prompt v6 relabel pilot | labels | pilot | Holdout Negative-F1 **0.4615 → 0.6875** |
| 22 | Strategy A — reverse transliteration | sentiment | **built, not run** | Would be circular: our Singlish is rule-generated |
| 23 | Code-switch augmentation | sentiment | **built, not run** | Blocked on human-typed romanized data |
| 24 | Adapters unfrozen (Rathnayake T3) | sentiment | **built, needs peft** | Checks a documented near-null |

---

## 2. Headline results — the numbers to quote

| Task | Champion | Config | Test score | 95% CI | Beats | Label ceiling |
|---|---|---|---:|---|---|---|
| **intent** | LinearSVC | word (1,2) + char (3,5) TF-IDF, `all` | **83.18%** macro-F1 | [82.55, 83.72] | — | 1.00 (BANKING77 ground truth) |
| **sentiment** | **LaBSE** (fine-tuned, multilingual) | 3 ep, lr 2e-5, bs 32, class_weight | **0.5664** Neg-F1 | — | classical 0.4572 (+0.109) | 0.5769 [0.40, 0.73] |
| **priority** | **LaBSE** (fine-tuned, multilingual) | same | **0.8900** macro-F1 | — | classical 0.8722 (+0.018) | **0.7722** |

> **Quote the priority ceiling alongside the priority score.** 0.8900 is agreement with the *v5
> labeling rule*. That rule agrees with human annotation at only **0.7722** (κ=0.64), so 0.7722 is
> the real operational ceiling. Reporting "89% priority accuracy" overstates what a human would call
> correct.

---

## 3. Intent (77-way) — classical baselines

### 3.1 Official baseline benchmark

Source: [`baseline_summary.csv`](baseline_summary.csv). Trained on the full 9,998-row train split,
scored on the official 3,079-row test split. Features: word TF-IDF (1,2) + char TF-IDF (3,5),
`sublinear_tf=True`, 250k max features.

| Track | Test n | **LinearSVC** Acc | **LinearSVC** Macro-F1 | LogReg Acc | LogReg Macro-F1 | Winner |
|---|---:|---:|---:|---:|---:|---|
| `english` | 3,079 | **90.97%** | **90.98%** | 90.48% | 90.48% | SVM |
| `singlish` | 3,079 | **86.55%** | **86.49%** | 86.20% | 86.07% | SVM |
| `tamil` | 3,079 | **86.85%** | **86.35%** | 85.00% | 84.22% | SVM |
| `sinhala` | 3,079 | 83.60% | 82.75% | **83.63%** | **83.08%** | LogReg |
| `tamilish` | 3,079 | **62.23%** | **61.05%** | 60.54% | 59.05% | SVM |
| `all` (combined) | 15,395 | **83.14%** | **83.18%** | 82.10% | 82.16% | SVM |

Training cost: 6–13 s per monolingual model, 53–58 s for `all`. scikit-learn 1.9.0 / Python 3.13.7.

### 3.2 Statistical reliability — 1,000-resample bootstrap CIs

| Track | Model | Macro-F1 mean | CI low | CI high | Width |
|---|---|---:|---:|---:|---:|
| `english` | LinearSVC | 90.89% | 89.84% | 91.91% | 2.07 |
| `english` | LogReg | 90.34% | 89.31% | 91.40% | 2.09 |
| `singlish` | LinearSVC | 86.32% | 85.17% | 87.52% | 2.35 |
| `singlish` | LogReg | 85.92% | 84.83% | 87.08% | 2.25 |
| `tamil` | LinearSVC | 86.22% | 85.15% | 87.37% | 2.22 |
| `tamil` | LogReg | 84.05% | 82.86% | 85.22% | 2.36 |
| `sinhala` | LinearSVC | 82.60% | 81.37% | 83.85% | 2.48 |
| `sinhala` | LogReg | 82.92% | 81.71% | 84.19% | 2.48 |
| `tamilish` | LinearSVC | 60.81% | 59.39% | 62.36% | 2.97 |
| `tamilish` | LogReg | 58.76% | 57.23% | 60.26% | 3.03 |
| `all` | LinearSVC | 83.14% | 82.55% | 83.72% | 1.17 |
| `all` | LogReg | 82.13% | 81.54% | 82.69% | 1.15 |

**Sinhala LinearSVC vs LogReg is a tie** (CIs overlap almost entirely). Everywhere else SVM's lead
is real except within-track noise.

### 3.3 Feature ablation — character n-grams are load-bearing

Macro-F1 delta vs the combined word + char pipeline ([`feature_ablation_results.csv`](feature_ablation_results.csv)):

| Track | Word (1,2) only | Char (3,5) only | Word + Char | Word-only penalty |
|---|---:|---:|---:|---:|
| `english` | 89.43% | 90.71% | **90.98%** | −1.55 |
| `sinhala` | 78.58% | 82.13% | **82.75%** | −4.17 |
| `singlish` | 84.56% | 85.07% | **86.49%** | −1.93 |
| `tamil` | 75.90% | 85.90% | **86.35%** | **−10.45** |
| `tamilish` | 57.75% | 59.86% | **61.05%** | −3.30 |
| `all` | 79.64% | 82.82% | **83.18%** | −3.54 |

Character n-grams alone come within 0.3–1.4pp of the full pipeline on every track. Tamil's −10.45pp
word-only collapse is partly the tokenizer defect of §7.4 — see that section.

### 3.4 Monolingual vs combined training — positive cross-lingual transfer

One unified LinearSVC over all five tracks, evaluated per language ([`combined_model_by_language.csv`](combined_model_by_language.csv)):

| Eval language | Monolingual Macro-F1 | Combined (`all`) Macro-F1 | Δ | Impact |
|---|---:|---:|---:|---|
| `sinhala` | 82.75% | **86.10%** | **+3.35** | Improves |
| `singlish` | 86.49% | **87.83%** | **+1.34** | Improves |
| `english` | 90.98% | **91.76%** | +0.78 | Improves |
| `tamilish` | 61.05% | 61.21% | +0.16 | Neutral |
| `tamil` | 86.35% | 86.35% | −0.00 | Neutral |

Cross-script training helps and never hurts. Combined with §5.1 (`multi` ≥ `mono` on sentiment and
priority too), **one multilingual model is the deployment answer for all three tasks** — it costs
nothing in accuracy and removes four models from the serving path.

### 3.5 Promotion gates for transformers (+3.00pp absolute)

| Track | Best classical Macro-F1 | Promotion threshold |
|---|---:|---:|
| `english` | 90.98% | **93.98%** |
| `singlish` | 86.49% | **89.49%** |
| `tamil` | 86.35% | **89.35%** |
| `sinhala` | 83.08% | **86.08%** |
| `tamilish` | 61.05% | **64.05%** |
| `all` | 83.18% | **86.18%** |

*No transformer has yet been run against these gates on the intent task — see §10.*

### 3.6 Tamilish error analysis — why 61%

| Confusion pair | Errors |
|---|---:|
| `unable_to_verify_identity` → `verify_my_identity` | 27 |
| `exchange_rate` → `card_payment_wrong_exchange_rate` | 27 |
| `top_up_reverted` → `top_up_failed` | 26 |
| `why_verify_identity` → `verify_my_identity` | 26 |
| `pin_blocked` → `get_physical_card` | 19 |
| `disposable_card_limits` → `get_disposable_virtual_card` | 19 |

Root cause: unstandardized romanization (`card` / `kaadu`, `account` / `akount` / `akkount`) that
static TF-IDF cannot map to a shared concept, layered on top of genuinely fine-grained intent pairs.
Singlish does not have this problem (86.49%) because it preserves English loanword spelling
consistently.

Dataset quality after `fix_tamilish.py` standardization (test split): FORMAL rows 766 → **14**
(−98.2%), formal pronouns 1,053 → **0**, mean Code-Mixing Index 8.9 → **12.6**.

---

## 4. Priority — baselines, bake-off, encoders, final test

### 4.1 The bar and the ceiling (dev)

| Reference | Macro-F1 | What it is |
|---|---:|---|
| `majority` (always Low) | 0.2302 | floor |
| `intent-chained` (predict intent → look up priority) | **0.9040** | **the honest bar** |
| `intent-lookup-oracle` (gold intent → lookup) | 0.9147 | **ceiling, not a target** — gold intent doesn't exist at serving time |

### 4.2 Direct text→priority beats the chained bar in every language (dev)

| Language | `intent-chained` bar | Direct best | Oracle | Beats bar by | Gap to oracle |
|---|---:|---:|---:|---:|---:|
| `english` | 0.8931 | 0.8999 | 0.9147 | +0.0068 | 0.0148 |
| `singlish` | 0.9040 | 0.9115 | 0.9147 | +0.0074 | 0.0032 |
| `sinhala` | 0.9011 | 0.9079 | 0.9147 | +0.0068 | 0.0068 |
| `tamil` | 0.8921 | **0.9119** | 0.9147 | **+0.0198** | 0.0028 |
| `tamilish` | 0.8945 | 0.9074 | 0.9147 | +0.0129 | 0.0073 |

→ Priority gets **its own head** and stops inheriting the intent classifier's errors.

### 4.3 Class-balancing arms — nearly indistinguishable

Priority macro-F1 averaged over all runs: `none` / `class_weight` / `ros` = **0.7905 – 0.7962**.
A 53/37/10 split is mild enough that balancing barely moves it.

### 4.4 Encoder bake-off, pooled dev

| Model | Dev macro-F1 | vs classical dev (0.9028) |
|---|---:|---:|
| **labse** | **0.9168** | +0.014 |
| xlmr-base | 0.9162 | +0.013 |
| mmbert | 0.9148 | +0.012 |
| twhin-bert | 0.8907 | −0.012 |
| canine-c | 0.8786 | −0.024 |
| *tfidf-svm (classical)* | *0.9028* | — |
| sinhalaberto (Sinhala-only) | 0.5573 | unfair on pooled eval |
| sinbert-large (Sinhala-only) | 0.4939 | unfair on pooled eval |

### 4.5 Final test — fit on train+dev (49,990 rows), scored once

| Model | Test macro-F1 | Accuracy | Weighted-F1 | F1 Low | F1 Medium | F1 High | vs classical 0.8722 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **labse** | **0.8900** | 0.9007 | 0.9002 | 0.9206 | 0.8760 | 0.8735 | **+0.018** |
| mmbert | 0.8887 | 0.9012 | 0.9005 | 0.9231 | 0.8741 | 0.8691 | +0.017 |
| xlmr-base | 0.8872 | 0.8992 | 0.8988 | 0.9202 | 0.8742 | 0.8673 | +0.015 |
| tfidf-svm / class_weight | 0.8722 | — | — | — | — | — | — |
| tfidf-logreg / class_weight | 0.8683 | — | — | — | — | — | −0.004 |

Classical CI is [0.8605, **0.8831**] — **labse and mmbert clear its upper bound**, a real if modest
win. twhin-bert and canine-c sit below the classical bar.

### 4.6 Priority per language, on test

| Model | english | sinhala | singlish | tamil | tamilish |
|---|---:|---:|---:|---:|---:|
| **labse** | 0.9229 | 0.9179 | 0.8814 | 0.9130 | **0.8142** |
| mmbert | **0.9269** | 0.9086 | 0.8950 | 0.9014 | 0.8094 |
| xlmr-base | 0.9234 | 0.9116 | 0.8780 | 0.8990 | **0.8229** |
| tfidf-svm (classical) | 0.9032 | 0.8745 | 0.8915 | 0.8905 | **0.7994** |

**Tamilish is the weak track on every model** — a 9–11 point gap that no other language shows. The
encoders narrow it (0.7994 → 0.8229) but do not close it.

### 4.7 Training cost (Kaggle T4, fp16)

| Model | HF name | Train s | Rows/s | Max len |
|---|---|---:|---:|---:|
| xlmr-base | `FacebookAI/xlm-roberta-base` | 933 | 160.7 | 128 |
| labse | `sentence-transformers/LaBSE` | 1,310 | 114.5 | 128 |
| mmbert | `jhu-clsp/mmBERT-base` | 1,607 | 93.3 | 160 |

LaBSE learning curve (test macro-F1 by epoch): 0.8753 → 0.8862 → **0.8900**.

---

## 5. Sentiment — the hardest task in the project

### 5.1 Regime study — `multi` wins, zero-shot collapses (dev)

| Regime | Sentiment mean / best Neg-F1 | Priority mean / best macro-F1 |
|---|---|---|
| `mono` (train on eval language) | 0.4773 / 0.6395 | 0.8858 / 0.9115 |
| **`multi`** (one model, 5 languages) | **0.4985** / 0.6331 | **0.8874** / 0.9119 |
| `zeroshot-en` (never sees eval language) | 0.0847 / 0.3158 | 0.5625 / 0.7579 |

Zero-shot cross-script transfer does not happen for free — the translated training data is doing
real work, and a sixth language would need its own data, not transfer.

### 5.2 Class balancing matters more than model choice

Averaged over all 168 sentiment runs:

| Arm | Accuracy | **Negative-F1** |
|---|---:|---:|
| `none` | **0.9281** | 0.3171 |
| `class_weight` | 0.9252 | **0.4061** |
| `ros` (random oversampling) | 0.9293 | 0.3949 |

The **highest-accuracy arm is the worst model.** This single table is why the project never reports
sentiment accuracy. Estimator spread (~0.05) is smaller than arm spread (~0.09).

| Estimator | Sentiment mean / max | Priority mean / max |
|---|---|---|
| `tfidf-svm` | **0.4082** / 0.6331 | **0.8137** / 0.9119 |
| `tfidf-logreg` | 0.3566 / **0.6395** | 0.8093 / 0.9068 |
| `tfidf-cnb` | 0.3744 / 0.5304 | 0.7796 / 0.8739 |
| `tfidf-sgd` | 0.3517 / 0.5802 | 0.7735 / 0.9074 |

### 5.3 The correction — the bake-off headline was noise

| Setup | Negative-F1 |
|---|---:|
| Bake-off headline (single dev split, C=1.0, threshold 0.5) | 0.6395 |
| **5-fold CV over train+dev, tuned C** | **0.5525 ± 0.044** |
| 5-fold CV, tuned C + tuned threshold | 0.5721 |

Bootstrapping the champion by ticket `id`: **0.6395, 95% CI [0.5521, 0.7174], width 0.165** —
**all 10 of the top 10 configurations fall inside that interval.** Their ordering was noise. Pooling
languages does not help: the pooled dev set has 340 Negative *rows* but only **68 unique Negative
tickets** (the other 272 are translations of the same tickets), so any CI over 340 rows is
dishonestly narrow.

### 5.4 Encoder screen — 800 balanced rows, identical budget

| Model | Params | Neg-F1 | Recall | Precision | Train s |
|---|---:|---:|---:|---:|---:|
| **mmbert** | 307M | **0.3268** | 0.888 | 0.200 | 891 |
| xlmr-base | 278M | 0.2343 | 0.897 | 0.135 | 282 |
| twhin-bert | 278M | 0.2235 | 0.771 | 0.131 | 544 |
| indicbert | 278M | 0.2134 | 0.821 | 0.123 | 266 |
| xlmr-large | 560M | 0.2082 | 0.818 | 0.119 | 1,263 |
| *tfidf-svm, same 800 rows* | — | *0.2619* CI [0.2106, 0.3125] | — | — | — |

**The candidate with the worst tokenizer fertility won**, and XLM-R large — the largest and most
expensive — came last. The fertility ranking predicted almost the reverse order (see §7.2).

### 5.5 Full-data encoder bake-off — dev and final test

3 epochs, lr 2e-5, batch 32, `class_weight`. Test = refit on train+dev, scored once.

| Model | Dev Neg-F1 | **Test Neg-F1** | dev→test Δ |
|---|---:|---:|---:|
| **labse** | 0.6334 | **0.5664** | −0.067 |
| mmbert | 0.6203 | 0.5321 | −0.088 |
| xlmr-base | 0.5012 | 0.5396 | **+0.038** |
| canine-c | 0.5323 | 0.4702 | −0.062 |
| *tfidf-svm (classical)* | *0.6144* | *0.4572* | *−0.157* |
| *tfidf-logreg (classical)* | *0.5933* | *0.4225* | *−0.171* |
| sinhalaberto (Sinhala-only) | 0.1730 | 0.1296 | — |
| sinbert-large (Sinhala-only) | 0.1238 | 0.1182 | — |

**The key pattern is in the delta column.** On dev, LaBSE only tied the classical champion within
the CI. On test — 505 Negatives vs dev's 340, so a tighter interval — the encoders separate cleanly:
classical dropped 0.157, the subword encoders dropped 0.06–0.09, and **XLM-R actually rose**.
Encoders generalize better here. LaBSE finishes **+0.109 over classical**.

canine-c (character-level) ≈ classical — the char model does not justify itself.

### 5.6 Classical champion — final test detail

| Model | Arm | C | Dev | **Test** | 95% CI (test) | Neg precision | Neg recall |
|---|---|---:|---:|---:|---|---:|---:|
| **tfidf-svm** | class_weight | 0.5 | 0.6144 | **0.4572** | [0.3970, 0.5130] | 0.364 | 0.614 |
| tfidf-logreg | ros | 3.0 | 0.5933 | 0.4225 | [0.3627, 0.4788] | 0.349 | 0.535 |

**Decomposing the 0.1571 dev→test drop** (resampling test down to dev's Negative rate by dropping
Neutral tickets, 25 draws → 0.5165 ± 0.0065):

| Component | Value |
|---|---:|
| Total dev → test drop | 0.1571 |
| Attributable to **prevalence** (3.28% vs 4.54% Negative) | 0.0592 |
| **Genuine generalization loss** | **0.0979** |

Roughly a third is the excusable kind and two thirds is not. The CV estimate of 0.5525 that was
meant to be the honest figure still came in **0.095 above** what test delivered.

### 5.7 Per-language sentiment, on test (classical)

| Model | english | singlish | sinhala | **tamil** | tamilish |
|---|---:|---:|---:|---:|---:|
| tfidf-svm / class_weight | 0.4582 | 0.4615 | 0.4138 | **0.5252** | 0.4229 |
| tfidf-logreg / ros | 0.4361 | 0.4170 | 0.3843 | 0.5018 | 0.3523 |

### 5.8 Per-language specialisation — does one model dilute?

Multi-trained dev Negative-F1 (per-language cells hold 14–68 Negatives, CI ≈ ±0.1 — read directions,
not orderings):

| Model | english | sinhala | singlish | tamil | tamilish |
|---|---:|---:|---:|---:|---:|
| **labse** | 0.657 | **0.671** | **0.647** | 0.632 | **0.551** |
| twhin-bert | 0.653 | 0.613 | 0.559 | 0.626 | 0.534 |
| xlmr-base | 0.584 | 0.487 | 0.489 | 0.485 | 0.469 |

Monolingual vs multilingual LaBSE:

| Language | ft-multi | ft-mono | Δ mono |
|---|---:|---:|---:|
| english | 0.657 | 0.667 | +0.010 |
| sinhala | 0.671 | 0.696 | +0.025 |
| singlish | 0.647 | 0.630 | **−0.017** |
| tamil | 0.632 | 0.680 | +0.048 |
| tamilish | 0.551 | 0.553 | +0.002 |

**LaBSE is best on every language, including the romanized tracks.** No specialised model beat it.
Monolingual gives a small native-script edge but **loses on Singlish** — romanized text leans on
cross-lingual transfer. All deltas sit inside noise. → **Do not ship per-language models.**

### 5.9 LoRA adapters — not competitive as a drop-in

| Language | ft-multi | ft-mono | lora-multi | lora-mono |
|---|---:|---:|---:|---:|
| english | 0.657 | 0.667 | 0.382 | 0.323 |
| sinhala | 0.671 | 0.696 | 0.477 | 0.322 |
| singlish | 0.647 | 0.630 | 0.394 | 0.263 |
| tamil | 0.632 | 0.680 | 0.424 | 0.322 |
| tamilish | 0.551 | 0.553 | 0.362 | 0.274 |

LoRA loses **0.2–0.3 everywhere**; per-language LoRA is the worst configuration of all four.
**Caveat:** LoRA ran at full-FT hyperparameters (lr 2e-5). LoRA conventionally wants ~1e-4 and more
epochs — this shows "drop-in LoRA at these settings fails," not "LoRA can't work." A fair test needs
its own sweep. It is fast, though: 308 s multi vs 1,159 s for full fine-tuning.

### 5.10 TwHIN-BERT for code-mixed romanized text

`model-research.md` §5 names TwHIN-BERT as the "process romanized directly" (Strategy B) model.
**It does not win on romanized here** — LaBSE beats it on singlish 0.647 vs 0.559 (−0.088) and on
tamilish. It does clearly beat xlm-roberta.

**Caveat:** our Singlish is *rule-generated* from Sinhala and Tamilish is *machine-translated* — an
optimistic upper bound. TwHIN-BERT's edge would most plausibly appear on **real human-typed**
code-mixing, which we do not have. → **Revisit with real romanized data.**

---

## 6. Baselines and floors, at a glance

| Task | Floor | What the floor is | Champion (test) | Headroom used |
|---|---:|---|---:|---|
| intent | ~1.3% | random over 77 classes | 83.18% (`all`) | — |
| sentiment | **0.000** | always-Neutral (95.5% accuracy) | 0.5664 | wide headroom remains |
| priority | 0.2302 | always-Low | 0.8900 | past its 0.7722 label ceiling |
| priority (fair bar) | 0.9040 | `intent-chained`, dev | 0.9168 dev | +0.013 |

---

## 7. Tokenizer studies — four separate investigations

### 7.1 Study 1 — 3 tokenizers × 15,000 stratified samples

Fragmentation ratio (tokens per word) and `[UNK]` rate ([`tokenizer_comparison.md`](tokenizer_comparison.md)):

| Tokenizer | english | sinhala | tamil | singlish | tamilish | Sinhala `[UNK]` |
|---|---:|---:|---:|---:|---:|---:|
| **xlm_roberta** | 1.25× | 1.45× | 2.17× | 1.94× | 2.14× | **0.0%** |
| mbert | 1.25× | 1.23× | 3.52× | 2.03× | 2.31× | **60.32%** ✗ |
| indicbert | 1.17× | 3.60× | 1.56× | 1.87× | 2.02× | 0.60% |

**`max_length` decision: 128.** Across all 65,385 rows the maximum tokenized length is **108 tokens**
— 128 gives **100.0% coverage / 0.0% truncation** on every track while minimising padding. Use
`DataCollatorWithPadding` for dynamic padding rather than static 128.

### 7.2 Study 2 — 7 encoders × 2,000 real rows per language

| Model | Mean fertility | Sinhala `[UNK]` % | Status |
|---|---:|---:|---|
| muril | **1.599** (best) | **64.53** | **disqualified** |
| xlmr-base / xlmr-large / twhin-bert | 1.791 | 0.00 | shortlisted |
| indicbert | 2.050 | 0.59 | shortlisted |
| mbert | 2.069 | **61.35** | **disqualified** |
| mmbert | 2.525 (worst) | 0.00 | shortlisted |

**Ranking on fertility alone would have picked the worst candidate.** MuRIL leads on mean fertility
precisely *because* it maps two-thirds of Sinhala to `[UNK]` — discarded text is cheap to tokenize.
**Fertility must always be read next to `[UNK]` rate**, and per §5.4 it has **no predictive value**
for downstream accuracy among the models that can actually read the script.

Also corrected here: mmBERT's real Sinhala fertility is **3.67**, not the 4.60 an earlier
four-sentence probe reported, and it is worst on Tamil (3.72) — which that probe never tested.

### 7.3 Study 3 — encoder-roster fertility (tokens/word, 300 dev tickets/language)

| Model | english | sinhala | singlish | tamil | tamilish |
|---|---:|---:|---:|---:|---:|
| **LaBSE** | **1.36** | **1.74** | **1.89** | **2.01** | **2.19** |
| xlmr-base | 1.43 | 1.81 | 2.23 | 2.35 | 2.35 |
| mmbert | 1.37 | 4.40 | 2.17 | 3.91 | 2.40 |
| sinhalaberto | 1.41 | 3.40 | 2.16 | 7.15 | 2.63 |
| sinbert-large | 5.09 | 4.26 | 6.65 | 6.95 | 7.20 |
| canine-c (chars) | 5.10 | 5.97 | 6.67 | 8.46 | 7.21 |

Two findings from the probe alone, both of which held up in the actual bake-off:

- **LaBSE beats XLM-R on every track** and had never been screened — `model-research.md` §4 listed
  it only under *Embeddings (RAG)*. It went on to win both tasks.
- **The monolingual Sinhala checkpoints tokenize Sinhala *worse* than the multilingual ones**
  (SinBERT-large 4.26, SinhalaBERTo 3.40 vs XLM-R 1.81, LaBSE 1.74) — and they scored 0.12–0.17
  Negative-F1 pooled.

All six report 0% `[UNK]`, **and that is meaningless** — they are byte-BPE or character models,
which structurally cannot emit `UNK`. The mBERT/MuRIL disqualification stands; those are WordPiece.

### 7.4 Study 4 — the Indic word-tokenizer defect (found, measured, fixed)

`swiftbench/models.py` used scikit-learn's default `token_pattern=r"(?u)\b\w\w+\b"`. `\w` excludes
Unicode categories `Mn`/`Mc` — **every Sinhala and Tamil vowel sign**. Silent failure: no error, no
warning, plausible-looking metrics.

**Character preservation rate on dev** ([`word_tokenizer_preservation.csv`](word_tokenizer_preservation.csv)):

| Language | sklearn default | regex-unicode | **indic-nlp (adopted)** |
|---|---:|---:|---:|
| english | 0.9357 | 0.9357 | 0.9357 |
| singlish | 0.9738 | 0.9738 | 0.9738 |
| tamilish | 0.9631 | 0.9631 | 0.9631 |
| **sinhala** | **0.5993** | 0.9681 | **0.9699** |
| **tamil** | **0.3072** | 0.9745 | **0.9746** |

40.1% of Sinhala and **69.3% of Tamil** characters were being discarded. Words differing only in
vowel signs collapsed onto one token: `කවුරු හරි මගේ කාඩ් එක පාවිච්චි` → `['කව','හර','මග','එක']`.

**Measured impact of the fix** ([`word_tokenizer_comparison.csv`](word_tokenizer_comparison.csv)):

| Task | Language | Word only: default → indic-nlp | Word + char_wb: default → indic-nlp |
|---|---|---|---|
| intent | sinhala | 0.9008 → 0.9170 (**+0.016**) | 0.9253 → 0.9266 (+0.001) |
| intent | tamil | 0.8100 → 0.8658 (**+0.056**) | 0.9155 → 0.9157 (+0.000) |
| priority | tamil | 0.8523 → 0.8889 (**+0.037**) | 0.9109 → 0.9028 (−0.008) |
| priority | sinhala | 0.8984 → 0.9060 (+0.008) | 0.9079 → 0.9088 (+0.001) |
| sentiment | sinhala | 0.5172 → 0.5696 (**+0.052**) | 0.6395 → 0.6395 (0.000) |
| sentiment | tamil | 0.5137 → 0.5250 (+0.011) | 0.6013 → 0.6250 (+0.024) |
| any | english | unchanged | unchanged |

| Features | Mean gain from fix | Max |
|---|---:|---:|
| word only | **+0.0200** | +0.0558 (intent, tamil) |
| word + `char_wb` (production) | +0.0020 | +0.0237 |

**`char_wb` had been silently compensating**, which is why the defect survived for so long — the
production metric barely moves. Fixed anyway, because it corrupted everything built on word
features: the mined lexicon in notebook 20 was extracting `කව හර` instead of `කවුරු හරි`.

**Fix:** `swiftbench/tokenize.py`, using `indic_nlp_library` dispatched on script. A plain Unicode
regex `[\p{L}\p{M}\p{N}]+` was **rejected** — it recovers the vowel signs but splits on **ZWJ
(U+200D)**, breaking `ට්‍රැක්` ("track") into two fragments (the exact gotcha `research/README.md`
§3.19.3 flags). Agreement with indic-nlp: Tamil 99.5%, Sinhala 92.4%, every Sinhala disagreement
being a ZWJ conjunct.

**All test numbers in §4–§5 predate the fix** and are therefore mildly conservative for Sinhala and
Tamil. The classical sentiment dev baseline moved 0.6144 → 0.6173 after it.

---

## 8. Label quality — the constraint that binds sentiment

### 8.1 Prompt versions vs the 500-row human gold benchmark

`sentiment`/`priority` have no upstream ground truth; they are LLM-derived. Prompts were iterated
against `datasets/english/500_benchmarkset.csv` (Label Studio, human-annotated, independent of
prompt tuning).

| Version | What changed | Outcome |
|---|---|---|
| v1 | Narrative rules, exhaustive emotion word lists, category→priority table built from the original dataset's *own heuristic* labels | Negative-F1 0.622 (P 0.535 / R 0.742) |
| v4 | Condensed rewrite of v1, same rule content and same category table | Priority barely moved off v1 |
| **v5 (frozen)** | Recalibrated the category→priority table against what the human annotator *actually did* | Sentiment acc **96.6%**, priority **77.2%**, both-exact **75.0%**; Negative-F1 **0.691** (P 0.792 / R 0.613) |

**The priority gap, isolated.** Four categories were hardcoded "High" in v1/v4 because the original
dataset's heuristic said so 100% of the time. On those 25 gold rows:

| Prompt | Priority accuracy on the 4 recalibrated categories (n=25) |
|---|---:|
| v4 | **4.0%** |
| v5 | **92.0%** |

Recalibrated: `pin_blocked`, `passcode_forgotten`, `card_swallowed` → Medium; `unable_to_verify_identity` → Low.

**v5 residual error:** 17/500 sentiment mismatches (12 Negative→Neutral, 5 Neutral→Negative).
**v5 full-dataset distribution** (n=10,003): Neutral 9,540 / Negative 463 / **Positive 0** — v5's
sentiment section is explicitly binary, and the human gold set independently agrees (0 Positive).
Downstream code must tolerate a zero-count Positive class.

### 8.2 The label ceiling — what the scores actually mean

v5 labels (what everything trains and scores against) vs human annotation on the gold 500
([`label_ceiling.csv`](label_ceiling.csv)):

| Task | v5 vs human | 95% CI | Agreement | Cohen's κ | Our test score | Reading |
|---|---:|---|---:|---:|---:|---|
| intent | 1.0000 | [1.00, 1.00] | 1.000 | 1.00 | 0.8318 | genuine ground truth |
| sentiment | 0.5769 | [0.40, 0.73] | 0.956 | 0.55 | 0.5664 | **inside the ceiling's own CI** |
| priority | 0.7722 | [0.73, 0.81] | 0.804 | 0.64 | 0.8900 | **exceeds the ceiling by 12 points** |

This does not *cap* the measured scores — against v5 labels a model could in principle reach 1.0. It
caps what they **mean**.

- **Priority has learned the v5 labeling rule well.** The rule itself agrees with humans at 0.7722,
  so that is the operational ceiling no matter what the model scores. Ship it, and state this in any
  external write-up.
- **Sentiment sits inside its ceiling's CI**, which is the stronger argument for **relabelling** than
  for a bigger model.

### 8.3 Prompt v6 relabel — the highest-leverage open item

| Prompt | Split | n | Sentiment Neg-F1 | Neg recall | κ | Priority macro-F1 | κ |
|---|---|---:|---:|---:|---:|---:|---:|
| v5 | dev | 250 | 0.6923 | 0.600 | 0.676 | 0.7481 | 0.629 |
| **v6** | dev | 250 | **0.7429** | **0.867** | **0.724** | 0.7359 | 0.628 |
| v5 | **holdout** | 250 | 0.4615 | 0.375 | 0.434 | 0.7959 | 0.660 |
| **v6** | **holdout** | 250 | **0.6875** | **0.688** | **0.666** | 0.7773 | 0.630 |

**v6 lifts holdout Negative-F1 from 0.4615 to 0.6875** — nearly a doubling — at a ~0.02 cost on
priority. `relabel_v6_staging.csv` is currently **40 pilot rows, train split only**. Rolling v6 out
is worth more than any modelling change currently on the table.

---

## 9. Techniques tested

### 9.1 Lexicon correction — null result

Senevirathna et al. (2025) report **+10.2pp accuracy / +0.10 F1** on banking Sinhala/Singlish
sentiment from a lexicon-correction layer. Reproduced here by mining a lexicon from train with
log-odds + an informative Dirichlet prior, blended as `z(model) + α·z(lexicon)`, α and threshold
tuned by 5-fold CV *within* train:

| α | 0.0 | 0.05 | 0.2 | 0.5 | 1.0 | 1.5 |
|---|---:|---:|---:|---:|---:|---:|
| CV Negative-F1 | **0.5554** | 0.5544 | 0.5489 | 0.5106 | 0.4697 | 0.4438 |

**CV selected α = 0.0 — use no lexicon.** On dev, the best non-zero α costs **−0.0075**, and it is
negative in all five languages:

| Language | model only | model + lexicon | Δ |
|---|---:|---:|---:|
| english | 0.6259 | 0.6234 | −0.0025 |
| singlish | 0.6483 | 0.6345 | −0.0138 |
| sinhala | 0.6207 | 0.6164 | −0.0043 |
| tamil | 0.6207 | 0.6069 | −0.0138 |
| tamilish | 0.5714 | 0.5676 | −0.0039 |

**Why**, predicted in the notebook *before* running: their lexicon was authored **externally**; ours
is mined from the rows the classifier already trained on, so it carries no information the model has
not already extracted. The +10.2pp came from the lexicon's *externality*, not from the correction
mechanism.

**The mined terms confirm it.** Top Negative-associated terms are `someone has`, `kavuru hari`
(*someone*), `romba` (*very*), `poiduchu` (*lost/gone*), `செய்யாத` (*didn't do*) — **topic markers
for fraud and loss, not polarity words**. Negative sentiment in this dataset is largely a function of
what the ticket is *about*, which TF-IDF already captures directly.

Testing Senevirathna's actual claim needs a hand-authored banking-polarity lexicon. That is a
labeling task, and it is the follow-up — not a refutation.

### 9.2 Built but deliberately not run

| Notebook | Status | Expectation on record |
|---|---|---|
| `21_technique_strategy_a_transliteration` | built, `SMOKE=True` | **Will score well and mean little** — our Singlish is rule-generated by `singlishify.py`, so reverse-transliteration inverts a function we applied. Singlish dev OOV is **1.18%, identical to English's**. |
| `22_technique_codeswitch_augmentation` | built, `SMOKE=True` | Includes a `duplicate` control arm so a gain can't be confused with more data. Defends against noise our eval set does not contain. |
| `23_technique_adapters_unfrozen` | built, needs `peft` | Rathnayake Technique 3. Their own sentiment numbers move only 53→55 across *all* adapter methods — this checks a documented near-null. |

All three, plus the TwHIN-BERT caveat in §5.10, reduce to one root cause: **our romanized text is
machine-generated and too regular to evaluate romanized techniques on.** The blocking dependency is
human-typed romanized tickets. The purpose-built `deshanksuman/romanized-sinhala-tokenizer` was also
**rejected on measurement** (fertility 2.64–3.08; fragments `card` → `c` + `ard`).

---

## 10. Open items and known gaps

| # | Item | Why it matters |
|---|---|---|
| 1 | **Roll out prompt v6** beyond the 40-row pilot | +0.226 holdout Negative-F1 — larger than any modelling gain measured in this report |
| 2 | **Intent has no transformer run** against the §3.5 promotion gates | The one task with genuine ground truth is still classical-only; published BERT on BANKING77 ≈ 93–94% vs our 90.98% English |
| 3 | **Tamilish is the weak track on every task** — priority 0.7994–0.8229, intent 61.05% | Only double-digit per-language gap in the project |
| 4 | **Human-typed romanized tickets** | Blocks Strategy A, augmentation, TwHIN-BERT, and any romanized-specific claim |
| 5 | **Fair LoRA sweep** at lr ~1e-4 | §5.9 shows drop-in failure, not that LoRA can't work |
| 6 | **Single-request latency** never measured | `ms_per_sample` 0.24–0.64 in `encoder_screen_dev.csv` is *batched MPS throughput*, not a valid check against the 100ms serving budget |
| 7 | **Intent score discrepancy across workstreams** | See §11, item 5 — unresolved |

---

## 11. Corrections and retractions log

Claims that were published in an earlier report and later withdrawn. Each is corrected in place
above; they are listed here so nothing quietly disappears.

| # | Retracted claim | Where it appeared | What actually happened |
|---|---|---|---|
| 1 | Sentiment champion = **0.6395** Negative-F1 | `bakeoff_sentiment_priority.md` §1–§5 | Maximum of 168 draws from a noisy distribution. CV says **0.5525 ± 0.044**; test says **0.4572**. All top-10 configs sat inside one CI. |
| 2 | Threshold tuning is worth **+0.027** | `06_improve_sentiment.ipynb`, bake-off §6 | On test the tuned threshold made the champion **worse** (0.4572 → 0.4524). The +0.027 was a property of the dev split. Also used a min-max-normalised score, which is fit-specific and does not transfer — use raw `decision_function`. |
| 3 | "0.55 is what to expect on unseen data" | bake-off §6 | Test came in at 0.4572, **0.095 below**. |
| 4 | "Don't fine-tune priority — the intent oracle caps it" | bake-off §5 | Conclusion right, reason wrong. The binding constraint is the **label ceiling (0.7722)**, not the oracle. And encoders *did* beat classical on test by 0.018. |
| 5 | mmBERT Sinhala fertility = 4.60 | bake-off §5 encoder probe | Real figure is **3.67**; the 4.60 came from a four-sentence probe that also never tested Tamil (3.72, its worst). |
| 6 | Fertility predicts encoder quality | implicit in early screening | **It does not.** §5.4's winner was the worst-fertility candidate. Fertility screens for efficiency and catastrophic `[UNK]` failure only. |
| 7 | All numbers in reports dated before 2026-08-01 | everywhere | Predate the Indic tokenizer fix (§7.4) and are mildly conservative for Sinhala and Tamil. |

### Two unresolved inconsistencies, flagged not fixed

**(a) Classical intent baselines differ across three documents.** `baseline_summary.csv` (used
throughout §3), `baseline_comparison.md`, and `final_baseline_report.md` quote figures for the same
models that differ by up to ~0.6pp (e.g. LogReg english 90.48 / 90.61 / 90.61; LogReg tamil 84.22 /
84.78 / —). These are separate runs of the same pipeline, not a metric disagreement. **§3 uses
`baseline_summary.csv`, the committed CSV artifact.**

**(b) Tamilish intent is reported at both 61% and 89%.** The classical baseline suite measures
tamilish intent macro-F1 at **61.05%** (official test split, full train). Phase-3 bake-off notes
record **0.8917** on the swiftbench dev split. That is a 28-point gap on the same task and language.
The likely explanation is the `fix_tamilish.py` style standardization (§3.6) landing between the two
measurements, plus test-vs-dev, but **this has not been verified** — do not quote either number for
tamilish intent without re-running.

---

## 12. Source map — where each number comes from

### Reports

| Report | Covers |
|---|---|
| [`final_baseline_report.md`](final_baseline_report.md) | Intent classical baselines, validation suite, leakage, CIs, promotion gates |
| [`baseline_comparison.md`](baseline_comparison.md) | Intent LR vs SVM comparison, saved model bundles |
| [`tokenizer_comparison.md`](tokenizer_comparison.md) | 3-tokenizer × 15k study, `max_length` decision |
| [`bakeoff_sentiment_priority.md`](bakeoff_sentiment_priority.md) | Sentiment/priority dev bake-off + §6 and §7 corrections |
| [`final_test_results.md`](final_test_results.md) | Classical final test, dev→test decomposition, label ceiling, tokenizer defect, techniques |
| [`ENCODER_FINDINGS.md`](ENCODER_FINDINGS.md) | Encoder bake-off both tasks, per-language, LoRA, TwHIN-BERT |
| [`progress_and_results_summary.md`](progress_and_results_summary.md) | Phase 1–3 narrative, XLM-R pipeline setup and smoke test |

### Notebooks (`notebooks/modeling/`)

| Range | Purpose |
|---|---|
| `00`–`02` | Setup checks, sentiment and priority runs |
| `03`–`06` | Benchmarks, label ceiling, sentiment improvement (source of retraction #2) |
| `07`–`08` | Encoder bake-off screen, word-tokenizer comparison |
| `10` | **Final test evaluation (classical)** |
| `11`–`16` | One notebook per encoder candidate |
| `20`–`23` | Techniques: lexicon, Strategy A, augmentation, adapters |
| `30` | **Leaderboard** — collates `runs/*.json`, enforces the promotion rule |
| `32`–`35` | Final test classical, final test encoders, per-language findings, priority encoders |
| `99` | Model selection |

### Key data artifacts

`runs/*.json` (425 run files, each stamped with the split sha — `results.load_all()` drops
mismatches so a stale run cannot enter a ranking) · `encoder_summary.csv` · `per_language_*.csv` ·
`history_*.csv` · `final_test_results.csv` · `label_ceiling.csv` · `prompt_v6_*_scores.csv` ·
`word_tokenizer_*.csv` · `encoder_tokenizer_fertility.csv` · `technique_lexicon_*.csv`

GPU driver: `ml/kaggle/runner.py` (T4 pinned; `--task`, `--fit-portion`, `--eval-portion`), kernels
in `ml/kaggle/kernels/`. **T4 is Turing: fp16 only, no bf16, no flash-attn-2.**

---

## 13. Decisions on record

1. **Ship one multilingually fine-tuned LaBSE** for sentiment and priority. Best model on both tasks
   and every language; clears the classical CI on both.
2. **Ship the classical LinearSVC `all` model for intent** until a transformer is run against the
   §3.5 gates.
3. **One multilingual model, not five monolingual ones** — true on all three tasks.
4. **No per-language models, no LoRA, no TwHIN-BERT** — none beat multilingual LaBSE on our data.
5. **Report Negative-F1 for sentiment and macro-F1 for priority. Never accuracy.**
6. **Rank on the confidence interval, not the point estimate.** Several dev leads did not survive to
   test; per-language cells are too small to order reliably.
7. **Never promote on a tuned-threshold number.**
8. **Quote the label ceiling next to every sentiment and priority score.**
9. **Relabel before re-modelling on sentiment** — the model sits inside the ceiling's CI, so label
   quality is the binding constraint, not model capacity.
10. **Plain random oversampling, never SMOTE** — three papers plus our own measurement.
11. **Never average Sinhala and Tamil** — Indo-Aryan vs Dravidian, documented family gap to 13pp.
12. **Romanized conclusions are unresolved by our data.** Synthetic Singlish/Tamilish cannot
    evaluate romanized-specific techniques. Real human-typed text is required first.
13. **Always measure character preservation when tokenizing non-Latin scripts** (§7.4 cost 40–69% of
    the characters and raised nothing).
