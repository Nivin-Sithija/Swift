# Reproducibility checklist and AI-usage disclosure

Draft for the paper's appendix. `[CONFIRM]` marks a fact only the authors have.

---

## 1. Data

| Item | Value |
|---|---|
| Source dataset | BANKING77 (PolyAI), CC-BY-4.0 |
| Tickets | 13,077 (9,998 train file + 3,079 test file) |
| Tracks | 5 — english, sinhala, singlish, tamil, tamilish |
| Rows total | 65,385 |
| Split | frozen, sha `e7b5934392cd`, drawn once on ticket `id`, stratified on the 77-way intent |
| Split sizes | 8,500 / 1,498 / 3,079 tickets → 42,500 / 7,490 / 15,395 rows |
| Sentiment/priority labels | LLM-generated, prompt v8, final |
| Label distribution | sentiment 93.70% Neutral / 6.30% Negative · priority 53.54 / 36.63 / 9.83% |

The split is drawn on `id`, not on rows. The same ticket exists five times, so a
row-level split would put a ticket's English copy in train and its Sinhala copy
in dev, and every subsequent score would measure memorisation. Regenerating the
split invalidates every result file: each record stamps the split sha and
`results.load_all()` drops any record whose sha does not match.

## 2. Models and hyperparameters

**Classical.** TF-IDF feature union — word 1–2 grams (`min_df=2`, `max_df=0.98`,
`max_features=25,000`, sublinear tf) plus `char_wb` 3–5 grams (`min_df=2`,
`max_features=50,000`). A custom tokenizer replaces sklearn's default
`token_pattern`, which discards 40.1% of Sinhala and 69.3% of Tamil characters.
Estimators: LinearSVC, LogisticRegression (lbfgs, `max_iter=1000`), SGDClassifier
(modified_huber, `alpha=1e-5`), ComplementNB (`alpha=0.3`). `C=1.0` throughout.

**Encoders / decoders.** 3 epochs, lr 2e-5, batch 32, `max_length` per tokenizer
p99 (128 for most, 160 mmBERT, 256 SinBERT/SinhalaBERTo, 512 CANINE), 10% warmup,
fp16 on CUDA only. Model selection on the headline metric per epoch, never on
loss — at 93.7% Neutral a model predicting Neutral everywhere reaches ~0.94
accuracy with a falling eval loss and zero Negative recall.
Decoder SLMs use LoRA (`r=8`, `alpha=16`); `lora_targets=all` covers all seven
projections, `attn` reaches only two of seven on Gemma 3.

**Class balancing.** Three arms: `none`, `class_weight` (balanced loss), `ros`
(random oversampling). No SMOTE — interpolating between TF-IDF vectors of two
different tickets does not correspond to any sentence anyone would write.

## 3. Seeds and variance

`RANDOM_STATE = 42` throughout.

**Every result currently reported is single-seed.** The variance reported is
bootstrap over *evaluation rows* (1,000 resamples, percentile method), which
answers "how much of this number is the test sample" — not "how much is the
seed". Seed variance requires repeated training runs and is task A6.

State both explicitly in the paper. A bootstrap CI presented without that
distinction reads as tighter than the evidence supports.

`[CONFIRM]` After A6: list the seeds used and report mean ± sd alongside the CIs.

## 4. Significance testing

Two tests per system pair, both on the test set:

- **Paired bootstrap**, 1,000 resamples, two-sided, on the headline metric.
- **Exact McNemar** (binomial, not chi-square) on per-row correctness.

Both are reported because they disagree in an instructive way: on sentiment,
`tfidf-sgd` vs `tfidf-svm` gives p(McNemar) = 0.866 and p(bootstrap) = 0.0000 —
the systems agree on nearly every row's correctness while differing by 0.056
Negative-F1. Reporting only an accuracy-based test would call that a tie.

## 5. Compute

| Item | Value |
|---|---|
| Classical roster (56 fits, 336 records, 1,000-resample CIs) | 8,202 s, CPU, Apple Silicon |
| Encoder fine-tune, reference | ~1,326 s per model/task on one Kaggle T4, fp16, 113 rows/s |
| Local MPS throughput, reference | 24.1 rows/s (xlm-roberta-base) — ~4.7x slower than T4 |

**Running total: 43.9 GPU-hours** across all unique fits recorded to date
(2026-09-08), on Kaggle T4s:

| family | GPU-hours |
|---|---:|
| `slm-multitask` (Gemma 3 LoRA) | 25.1 |
| encoder fine-tunes | 18.4 |
| classical (recorded fit time only) | 0.4 |
| **total** | **43.9** |

Counted per *fit*, not per record — one fit emits up to six records (pooled plus five
language tracks), so counting records would inflate this roughly six-fold. The classical
roster's 8,202 s of CPU wall-clock is listed in the table above and is not GPU time.

`[CONFIRM]` Re-run this tally after K3, K6b, K7 and K8 land; the generator is a ten-line
script over `ml/reports/runs/*.json` keyed on `(task, model, arm, fit_portion, epochs, seed,
train_seconds)`.

## 6. Software

Python 3.12, scikit-learn 1.9.0, pandas 3.0.5, scipy 1.18.0, PyTorch + Hugging
Face `transformers`, `peft` for LoRA. Every run record stamps its Python version.

## 7. Artifacts

| Artifact | State |
|---|---|
| Corpus, 5 tracks | [`Swift-Support/swift-support-tickets-1.0`](https://huggingface.co/datasets/Swift-Support/swift-support-tickets-1.0), CC-BY-4.0, public — see *Published-artifact defects* below |
| Frozen split manifest | in repository, `ml/splits/split_manifest.json` |
| Run records | `ml/reports/runs/*.json`, one per run, split-sha stamped |
| Per-row test predictions | `ml/predictions/runs/*.csv` |
| Table generators | `paper/experiments/` |
| Model checkpoints | sentiment: `ml/models/encoders/sentiment_labse/` (1.88 GB, train+dev, v8) with a model card at `paper/drafts/model_card_sentiment_labse.md`. **Intent riding K6b; priority still none** — task A7 |
| Figures | `paper/results/figures/*.{pdf,png}`, generator `paper/experiments/build_figures.py` |
| Per-epoch training curves | `paper/results/runs/history/` — preserved copies; the live `ml/reports/history_<model>.csv` is overwritten by each later job for the same model |

## 8. AI-usage disclosure

This is **method, not tooling**, and belongs in the methods section as well as here.

- **Machine translation.** English → Sinhala and Tamil, and romanisation to the
  two Latin-script tracks. The Sinhala track received a human correction pass to
  colloquial code-mixed register; measured code-mixing 40.35% Latin characters
  against Tamil's 1.26%. `[CONFIRM]` exact model, version, dates, and the scope
  of the human pass per track.
- **Label generation.** Sentiment and priority labels are LLM-generated using a
  documented prompt, iterated v1 → v8 and validated against a 500-row
  human-annotated benchmark at each version. v8 is final. Prompts are in
  `datasets/translation/prompts/`.
- **Not used for.** Intent labels (BANKING77's own human gold), the human gold
  benchmark, the inter-annotator agreement batch, or any reported metric.
- `[CONFIRM]` Assistance in writing the manuscript itself, per venue policy.

## 9. Known limitations to state, not bury

1. Sentiment and priority labels are model-generated; a classifier trained on
   them reproduces the prompt, not ground truth.
2. Every number is single-seed (§3).
3. Two of five tracks are machine-generated romanisation, so romanized-specific
   findings bound a generated function, not human text.
4. The Tamil track lacks the Sinhala track's colloquial correction pass, and the
   1.26% Latin-character rate shows it — cross-track comparisons involving Tamil
   inherit that confound.
5. The label ceiling rests on **one** annotator until task C2 completes.


---

## 10. Published-artifact defects found 2026-09-08

The Hugging Face artifacts predate several corrections in this document. Both items below
are **on the live public cards** and must be fixed before the paper cites them, because a
reviewer who follows the link will find numbers that disagree with the paper.

### Dataset card, `swift-support-tickets-1.0`

1. ~~**Row count is double the truth.**~~ **RETRACTED 2026-09-08.** This defect does not
   exist. It came from a summarisation of the card, not from the card, and was recorded here
   without checking the source. The card's row figures are correct throughout: its split table
   reads 42,500 train + 7,490 dev + 15,395 test = 65,385, and no total-row claim of 130,770
   appears anywhere in it. Left visible rather than deleted, because the failure mode — taking
   a summary of a document as evidence about the document — is worth not repeating.
2. **Quotes the superseded label ceiling.** *Confirmed against the card source.* The card's
   sentiment row reads "negative-F1 **0.7812**, agreement 97.2%, κ = 0.766" — which matches the
   *prompt's raw output* row of `label_ceiling.csv` exactly. The shipped `sentiment` column,
   which is what the card describes and what models train on, gives **0.7931 / 0.976 / κ 0.780**;
   the two differ on 8 of the 500 gold rows. The card's `priority` row (0.7722 / 80.4% / κ 0.644)
   matches shipped exactly and is correct — priority was never relabelled, so its prompt output
   and shipped column are identical.

Correct in the card's favour: it is CC-BY-4.0, it credits BANKING77, it states the sentiment
column already holds v8, and it warns against random re-splitting. Those are all right.

### Model card, `labse-intent-1.0`

3. **Does not say which split produced 88.54%.** `results.md` §7 annotates this figure as
   "official split"; the card presents it as pooled macro-F1 across the five tracks, which is
   the *frozen* split's framing. The two are different evaluations and cannot both be right.
   No local `intent__labse__…__test` record exists to settle it — the only local intent/labse
   records are **dev** (0.9293 pooled, best epoch 5 of 6). K6b is producing the frozen-split
   test number now; the card should be restated against that and the ambiguity removed.
4. **No epochs and no licence stated.** Both are required for the reproducibility checklist.
5. **The stated failure mechanism is backwards, and this is the substantive one.** The card
   explains MuRIL's and IndicBERT's collapse as "their smaller vocabularies couldn't handle
   heavy romanization or English slang". At a 6-epoch budget MuRIL's romanized tracks are among
   its *best* (Tanglish 90.23, Singlish 88.79); it fails on exactly one track, **native-script
   Sinhala at 76.33**, 13.7 points below its own English. Its tokenizer maps **64.5% of Sinhala
   characters to `[UNK]`** and 0.0% on every other track, including both romanized ones. The
   published claim asserts the opposite of what the data shows.
6. **The whole results table is from a 3-epoch run and understates the roster**, MuRIL most of
   all (Tamil reported 66.01%, actually 90.09% at 6 epochs). mmBERT is absent entirely, and it
   ties LaBSE (p = 0.944) — so the card's "LaBSE is the Intent Champion" is unsupported.

### Consequence for §7 above

The "Model checkpoints" row previously read "none for intent". That was wrong — an intent
checkpoint is public, and `ml/models/encoders/` also holds `priority_labse`,
`priority_gemma-3-1b`, `priority_gemma-3-270m`, `sentiment_gemma-3-1b` and
`sentiment_gemma-3-270m` locally. What is genuinely missing is a **frozen-split, v8-era intent
checkpoint whose provenance matches the paper's experiments**, which is what K6b produces.
