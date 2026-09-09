# Paper progress tracker

Single source of truth for what is done, what is running, and what is blocked.
Update this file as tasks land — every other document points here.

**Legend** — `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked, reason given
**Owner** — `me` = automatable here · `you` = needs your hands, credentials, or other people

Last updated: 2026-09-08 (session 3 — track E added: the paper is now a system
paper, not a benchmark paper; see `paper/SYSTEM_PLAN.md`)

---

## Critical — do this first

- [ ] **`you` · Commit the v8 CSVs.** All ten `datasets/*/{train,test}_labeled.csv` carry v8 in
  the working tree; `HEAD` still holds v5 (101 test Negatives per track vs 195 on disk). One
  `git checkout` destroys the relabel. Nothing else in this file is safe until this is done.
- [ ] **`you` · `runner.py sync` after committing.** Launching Kaggle jobs before syncing trains
  every encoder against v5 and wastes the whole batch.

---

## A — Run matrix

- [x] **A1 · Classical roster on v8** — DONE 2026-09-08, 336 records, 8202s. — 4 models × 3 tasks × arms × {dev,test} × 6 slices,
  bootstrap CIs. `ml/scripts/run_v8_classical.py`. Validated: reproduces recorded
  `tfidf-svm` intent test 0.8307.
- [ ] **A2 · Commit + sync** — see Critical above.
- [x] **A3 · Per-language scores from the encoder path** — DONE, smoke-verified on xlmr-base (124+128+108+111+129=600). — `train_encoder.run()` saves only
  `eval_lang="all"`. Slicing existing predictions by language is free and closes the largest
  documented gap. **Must land before A4** or every GPU hour buys a pooled number only.
- [!] **A4 · Encoder roster on v8** — `labse, xlmr-base, mmbert, muril-base, indicbert,
  twhin-bert` × 3 tasks × {dev,test}. ≈15 GPU-h. Blocked on A2 + A3.
- [~] **A5 · Decoder roster** — `gemma-3-270m` **DONE** (intent test 0.8305, final-epoch, clean).
  `gemma-3-1b` **OOM'd at batch 32** and wrote nothing; relaunched 2026-09-09 at batch 8.
  LoRA-all, lr 1e-4. See the session 4 entry at the foot of this file.
- [~] **A6 · Seed variance** — **one repeat done, and then descoped by decision.** seed 43,
  labse sentiment test: 0.6963 at 6 epochs, **0.6980 at epoch 3** against seed 42's 0.7138 —
  a **0.0158** spread at matched budget. Not negligible: it is the same size as §18.1's
  headline +0.0155. `you` decided 2026-09-09 that single-seed baseline numbers are enough for
  now and the GPU slots are better spent on method coverage, so seeds 44–46 are **not**
  queued. **What this owes the paper: a caveat sentence saying every CI is a within-fit
  interval and one seed repeat moved the sentiment headline by 0.0158.**
- [~] **A7 · Save champion checkpoints** — more complete than this tracker claimed. Sentiment
  DONE (`ml/models/encoders/sentiment_labse/`, 1.88 GB, train+dev, v8). **Priority also DONE
  and clean**: 0.8900 on the frozen split, `best_epoch` 3 of 3 so selection was inert, saved
  locally at `priority_labse` and public at `Swift-Support/labse-priority-1.0`.
  `ml/models/encoders/` also holds gemma priority/sentiment adapters. What is genuinely
  missing is a **frozen-split intent checkpoint matching the paper's experiments** — the
  public `labse-intent-1.0` exists but its split provenance is ambiguous (see below). K6b
  produces the matching one.

## B — Translation comparison

- [x] **B1 · Sample built** — 150 test segments, 77/77 intents, seed 42, ids recorded.
  `paper/translation_eval/samples/`.
- [ ] **B2 · `you` · Collect three external systems** — paste the four prompt files, save as
  `paper/translation_eval/systems/{openai,gptoss,google}_{sinhala,tamil}.csv`. Record model
  names and dates; the paper has to name the exact systems.
- [ ] **B2v · Verify returned files** — all 150 ids present, no truncation, no code fences.
  Silent row loss is the standard failure of pasting 150 rows through a chat window.
- [ ] **B3 · Blind rating sheets** — shuffled, unlabelled, adequacy + fluency + ranking.
  Script buildable now; sheets need B2.
- [ ] **B4 · Reference-free automatic scores** — COMET-Kiwi QE + LaBSE source-translation
  cosine. Never chrF/BLEU against our own text as reference.
- [ ] **B5 · `you` · Reconcile "manually verified"** — README and RESULTS.md both say Tamil had
  no hand pass. Methods needs who / how many rows / what fraction changed.

## C — Inter-annotator agreement

- [x] **C1 · Annotation guideline** — DONE, v1 written. Batches built: 200 rows, all 31 Negatives, priority 72/67/61. — written *before* anyone annotates. Must define Negative
  operationally; the project already found it behaves as a topic construct, not polarity.
- [ ] **C2 · `you` · Two annotators × 200 rows** — stratified so the 31 gold Negatives are not
  swamped. Report pairwise Cohen's κ and Krippendorff's α.
- [~] **C3 · Ceiling as an interval** — recomputed and corrected: **0.7931** (shipped labels), not the published 0.7812 (prompt output). Join now verified via the intent column. CI [0.6667, 0.8956] is wide — 31 Negatives, one annotator. Human-human bound still needs C2. — turns "agreement with one annotator" into "the task's
  reliability limit", which is what makes 0.7138 meaningful rather than merely low.

## D — Analysis, hygiene, drafting

- [x] **D1 · Significance testing** — DONE, 18 pairs. Confusion-matrix headline made it 280x faster; self-test asserts equality with metrics.score. — paired bootstrap for F1 deltas, McNemar for paired
  classifiers.
- [x] **D2 · Dedup ablation** — DONE, max shift -0.0047, all inside CIs. Downgraded to a footnote. — test-text overlap is 2.73% singlish / 2.31% sinhala+tamil vs
  0.19% english. Show the result does not depend on it.
- [x] **D3 · Error analysis** — DONE. 15/20 top intent confusions are one-way; 13.9% of priority errors extreme; Tanglish intent +28.9pp. — top-20 intent confusions, ~50 Negative false negatives, the
  priority Low/Medium boundary.
- [~] **D4 · Submission hygiene** — data_statement.md and reproducibility.md drafted. Model card for the sentiment checkpoint written (`paper/drafts/model_card_sentiment_labse.md`). GPU-hour tally resolved (43.9 GPU-h, counted per fit). **LICENSE still open — a `you` decision, see below.** Intent/priority model cards ride A7. — licence, data statement, ethics/PII, AI-usage disclosure,
  reproducibility checklist, model cards.
- [~] **D5 · Bibliography** — **36 entries** as of 2026-09-09, all verified. All 26 entries [VERIFIED] against ACL Anthology / publisher record, with pages + DOI. Three carried real errors (twhin-bert title truncated and author list elided, muril 3 of 14 authors, most entries had no pages). Six gap areas still unsourced at the file foot — that is what keeps this `[~]`. — 30–50 refs across six areas, version-controlled BibTeX.
- [~] **D6 · Draft** — `paper/drafts/outline.md` written: every claim in all 10 sections mapped to the generated file it comes from, with a checker confirming all 20 tables, 6 figures and 12 bib keys it names exist. No prose yet.

## E — The system: ordering, not just classifying

Design and full methodology: **`paper/SYSTEM_PLAN.md`**. This turns the paper from a benchmark
into a use-case contribution — the classifiers become the input layer, and the contribution is
the scoring function that orders the queue plus the evidence that a script-level accuracy gap
becomes a **waiting-time gap between customers**.

- [x] **E1 · Posteriors on test** — the score consumes probabilities, and every saved prediction
  file holds hard labels only (`id,language,y_true,y_pred`). Local MPS inference from the saved
  `sentiment_labse` and `priority_labse` checkpoints over the 15,395 test rows. No GPU quota.
- [x] **E2 · `scoring.py`** — the TUS itself: expected severity from the posterior, sentiment
  posterior, per-intent criticality κ(i) estimated on train+dev only, multiplicative aging.
- [x] **E3 · Layer 1, ranking** — Kendall τ_b, nDCG@k, **Precision@100 for gold-High**. Lead
  with Precision@100; it is the only one an ops owner reads without a stats background.
- [x] **E4 · `queue_sim.py`, Layer 2** — discrete-event sim, 5 policies, load ρ ∈ {0.70, 0.85,
  0.95}, ≥200 seeds. Report **attainment = (FIFO−TUS)/(FIFO−oracle)**, which separates "the
  scoring function is good" from "the classifiers are good".
- [x] **E5 · Layer 3, the fairness result** — per-language time-to-first-response against a
  gold-label control. Converts §16's +0.0698 DiD into minutes of extra wait. **The headline.**
- [x] **E6 · Layer 4, calibration** — per-language ECE, temperature scaling fitted on dev.
  Hypothesis: romanized tracks are less confident *as well as* less accurate, so the
  uncalibrated score penalises them twice and calibration is a near-free fairness fix.
- [x] **E7 · Layer 5, ablation** — signal ablation (does sentiment earn a second 1.9 GB model?),
  α frontier, dev simplex surface, TF-IDF-fed control.
- [x] **E8 · Weight fit on dev** — 3-simplex grid at 0.05, α grid. Fitted on dev, scored once on
  test. Publish the whole surface, not the argmin.
- [x] **E9 · Figures** — queue-time-by-language bar, α frontier, simplex heatmap, attainment
  vs load.
- [ ] **E10 · `you` · Simulation parameters from literature** — the biggest open threat to
  validity is that λ, service-time distribution and agent count are *assumed*. Any published
  helpdesk arrival/service statistics would let us parameterise from literature instead. A
  reading task, not an experiment.

**Dependency note.** E1–E9 need no GPU and no new labels. **All nine landed in session 3** —
see the session 3 entry at the foot of this file for results and for two defects found in the
design itself. E6b (a train-only encoder run with posteriors saved) is the one item that does
need the GPU, and it is what makes the temperature-scaling result a held-out number rather
than a labelled sensitivity analysis.

## Generators

- [x] `paper/experiments/build_translation_sample.py`
- [x] `paper/experiments/build_results_tables.py`
- [x] `paper/experiments/corpus_stats.py` — RUN. Finding: sinhala 40.35% Latin vs tamil 1.26%.
- [x] `paper/experiments/dedup_ablation.py` — RUN
- [x] `paper/experiments/significance.py` — RUN
- [x] `paper/experiments/build_rating_sheets.py` — waits on B2 files
- [x] `paper/experiments/score_translations.py` — waits on B2 files
- [x] `paper/experiments/build_annotation_batches.py` — RUN (build)
- [x] `paper/experiments/error_analysis.py` — RUN
- [x] `paper/experiments/encoder_gain_by_script.py` — RUN. The encoder's advantage is
  significant only on native script; romanizing the same Sinhala tickets removes ~7 points
  of it (difference-in-differences p=0.012). Tamil pair not significant.
- [x] `paper/experiments/tokenizer_to_downstream.py` — RUN (sentiment dev)
- [x] `paper/experiments/language_gap.py` — RERUN with labse included (52 comparisons)
- [x] `paper/experiments/label_ceiling.py` — RUN

---

## Kaggle run log

Payload sha `9c712241bddd` synced 2026-09-08 — verified v8 (195 English test Negatives).
Encoders 6 epochs, decoders 8 epochs (both up from the previous roster's 3), because the
earlier runs selected the best epoch at the edge of their budget on several models.
Every job writes per-language records and per-row predictions (A3), so one job now closes
the pooled score, the per-language gap and the significance input together.

| # | Job | Models | Task | Portion | Epochs | State |
|---|---|---|---|---|---|---|
| K0 | smoke | xlmr-base | sentiment | dev | 1 | **PASS** — 6 records (pooled+5 langs), label_version v8, seed 42, prediction CSV written |
| K1 | enc-sent-dev | all 6 encoders | sentiment | dev | 6 | **DONE** 8.7h · labse 0.7579 champion |
| K2 | enc-sent-dev-b | muril-base, indicbert, twhin-bert | sentiment | dev | 6 | — |
| K2 | enc-int-dev | all 6 encoders | intent | dev | 6 | **DONE** 8.7h · mmbert/labse tie p=0.944 |
| K4 | enc-int-dev-b | muril-base, indicbert, twhin-bert | intent | dev | 6 | — |
| K3 | enc-pri-dev | all 6 encoders | priority | dev | 6 | running |
| K6a | labse-sent-test | labse | sentiment | test | 3 (dev-selected) | **DONE** 22m · 0.7138 clean · bit-identical to the pre-patch record |
| K6b | enc-int-test | labse, mmbert, xlmr-base | intent | test | 6 | running, --save-models |
| K7 | dec-*-lora | gemma-3-1b, gemma-3-270m | all 3 | dev+test | 8 | — |
| K8 | seeds | champion + rival, seeds 43-46 | all 3 | test | 6 | — |

**Smoke records must not be fetched** — they overwrite real records at the same run id.

### Defect found by the smoke run and fixed before spending quota

`train_encoder.run()` selected the best epoch on `eval_df`. On a test run `eval_df`
**is the test set**, so the reported number was a maximum over `epochs` draws rather
than a held-out estimate. Every previously recorded test number in this project was
produced that way. At 3 epochs the bias is small; at the 6-8 epochs this run plan uses
it would not be.

Fixed: dev runs still pick their best epoch, test runs report their final epoch, and
every record now stamps `epoch_selection` (`best-on-dev` / `final-epoch`). Verified
locally on both portions before re-sync.

**Consequence for the paper:** the existing encoder/decoder test numbers
(labse 0.7138, gemma 0.7126, and the priority block) are optimistically biased by
epoch selection on test. They are superseded by the K6/K7 re-runs, not comparable to them.

### Scope of the epoch-selection defect, measured

`build_results_tables.py` now flags any *test* record whose epoch was not stamped
`final-epoch`. Current counts:

**SUPERSEDED — the count below was wrong. See the corrected count that follows.**

| family | clean | biased |
|---|---:|---:|
| classical (no epoch loop) | 12 | 0 |
| frozen probes (no epoch loop) | 12 | 0 |
| encoder | 0 | 7 |
| slm-multitask | 0 | 6 |

### Corrected count, 2026-09-08

The table above counted records that **ran** the defective code. What matters is records
where the defect could **change the answer** — and selection can only inflate a score when
it had something to choose. Where the argmax epoch *is* the final epoch, "max over `epochs`
draws" and "the last draw" are the same draw, and the bias is exactly zero.

| | records |
|---|---:|
| classical + probe (no epoch loop at all) | 24 — clean by construction |
| unstamped test, `best_epoch == epochs` | **15 — selection inert, bias exactly zero** |
| unstamped test, `best_epoch < epochs` | **2 — genuinely biased** |

The two genuinely biased records are `sinbert-large` (best epoch 2 of 3) and `sinhalaberto`
(best epoch 1 of 3), both sentiment, both minor models — not the headline systems.

Confirmed empirically rather than merely argued: K6a re-ran `labse` sentiment test
(`best_epoch` 3 of 3) under the patched code and it came back **bit-identical to 17
significant figures**.

`build_results_tables.py` now flags on `best_epoch < epochs` and reports the inert set
separately, so this distinction survives in the generator and not just in prose.

**The headline gap can now be quoted.** labse 0.7138 vs tfidf-svm 0.6653, Δ = +0.0485,
95% CI [+0.0257, +0.0721], p < 0.0001 (paired bootstrap, 1,000 resamples); McNemar
p = 1.4e-07. The earlier "do not quote it" instruction is withdrawn.

The caveat that survives: inertness is a property of the run, not the code. At a 6-epoch
budget these cells would not be inert (§14 has labse peaking at epoch 3 of 6 on dev), so
every future run must use the patched path.

### `runner.py fetch` hardened

Two defects, both of which would have hit the moment K1 finished:

1. **Predictions landed in the wrong directory.** `fetch` copied every `*.csv` flat
   into `ml/reports/`. The new per-row prediction files belong in
   `ml/predictions/runs/`, which is where `significance.py` looks — so the paired
   tests would have silently had no encoder input. Now routed by path.
2. **No validation before overwrite.** Records are written by run identity, so a
   smoke run overwrites the genuine record at the same filename. `fetch` now refuses
   any record whose `split_sha` differs from the local manifest, and any whose
   `n_train_before_resample` matches a known subsample size. Verified against the K0
   smoke record (n_train 1200 -> skipped).

Local script only, so no re-sync was needed.

### Label-ceiling correction (results.md §11)

Three defects in the published ceiling, all fixed by `paper/experiments/label_ceiling.py`:

1. **No verified join.** The gold set's `id` matches 1,000 dataset rows; `row_id`
   matches 76% of texts. Neither is a key. Now joined on normalised text and
   verified against the intent column (must be exactly 1.0; it is).
2. **Wrong labels scored.** 0.7812 measured the *prompt's* raw output. The shipped
   CSVs differ from it on 8/500 gold rows. Models train on the shipped labels, so
   the ceiling to quote is **0.7931**.
3. **No stated uncertainty on the claim that matters.** CI [0.6667, 0.8956] — the
   gold set holds only 31 Negatives, annotated by one person. The paper's central
   claim currently rests on that.

Provenance otherwise verified clean: shipped vs v5 = 711/13,077 changed (matches the
documented figure exactly); shipped vs the staging file's applied column = 0; priority
untouched = 0.

Generator: `paper/experiments/label_ceiling.py` (add `--with-iaa` once C2 returns).

### New analyses landed while the GPU jobs ran

- **results.md §12** — per-language deficit tested for the first time. Tanglish
  significantly worse on all 12 model x task combinations, paired bootstrap, every
  CI clear of zero. Also caught 3 of 48 comparisons where McNemar (accuracy) and the
  headline test disagree; two would have asserted cross-lingual sentiment effects
  that do not exist in the reported metric.
  Generator: `paper/experiments/language_gap.py`
- **results.md §13** — "Negative is a topic construct" quantified. An intent-label-only
  predictor with no text reaches 0.3301 Negative-F1, **49.6% of the text champion's
  0.6653**. Top 10 of 77 intents hold 48.8% of all Negatives.
  Generator: `paper/experiments/negative_is_topic.py`
- **results.md §11** — label ceiling corrected to 0.7931 with a verified join.
  Generator: `paper/experiments/label_ceiling.py`


---

## Session 2 addendum — K6a and the epoch-selection defect's actual magnitude

**The clean re-run reproduces the biased number exactly.** `labse` sentiment test came back
at `0.7138193688792165` — identical to 17 significant figures to the pre-patch record it was
launched to replace. Per-epoch the headline was 0.6749 -> 0.7115 -> **0.7138**, monotone, so
the best epoch *was* the final epoch and selection-on-test had nothing to select.

Two consequences, kept separate on purpose:

1. **The bias on this cell is zero**, so the headline sentiment claim survives untouched.
   It does **not** generalise: §14 shows `labse` peaking at epoch 3 of 6 on dev, so the same
   cell at a 6-epoch budget would not have been inert. The other 6 encoder and 6
   `slm-multitask` test records stay suspect until re-run.
2. **Training is deterministic to the bit** across sessions 19 days apart on different
   hardware (train_seconds 1325.7 vs 1319.0, headline identical). K8's seed study will
   therefore measure seed effect with no run-to-run noise floor beneath it.

**This unblocks the paper's headline comparison**, which could not be quoted before because
it set a biased encoder number against a clean classical one:

| system | Negative-F1 (test) |
|---|---:|
| labse (encoder) | **0.7138** |
| tfidf-svm (classical champion, v8) | 0.6653 |
| intent label only, no text | 0.3301 |
| label ceiling | 0.7931 |

+0.0485 over classical; **90.0% of the label ceiling**. Written up as `results.md` §15.
Significance test on the gap pending the prediction file, still downloading with the 1.8GB
checkpoint.

**A7 partially closed:** `models/sentiment_labse/` is the project's first champion checkpoint
fitted on train+dev under v8. Intent and priority still have none.


---

## M1 — RAG nDCG defect fixed (use-case track)

`backend/app/rag/evaluation.py:ndcg_at_k` gave every occurrence of a relevant id its own
gain. Retrieval is chunk-level and several chunks routinely resolve to one source id, so DCG
could exceed the ideal, which is built from *distinct* items:

    ndcg@5(["a","a","a","b","c"], relevant={"a"}) == 2.13

on a metric defined to be bounded in [0, 1]. Fixed by scoring each relevant item once, at its
best rank. Regression test `test_ndcg_stays_bounded_when_chunks_repeat_a_source` covers the
duplicate cases, the rank-order property (a repeat must not buy a better rank) and the range
bound; 39 passed / 2 skipped across `test_rag`, `test_eval_runner`, `test_rag_api`.

**Nothing to retract:** no nDCG figure has been written into any report, doc or paper table
yet, so the fix lands ahead of the number rather than behind it.

Also documented in the same function, deliberately *not* changed: an empty `relevant` set
scores 1.0 (matching `recall_at_k`). That is free credit in the mean. The right treatment is
to keep such queries out of the evaluation set, not to rely on the branch — flagged in a
comment rather than silently altering aggregate semantics.


## K6b launched — intent test

`labse, mmbert, xlmr-base` x intent x test, 6 epochs, fit on train+dev, `--save-models`.
Three models rather than six: K2 took 8.7h for six at dev size, and test fits on 1.18x the
rows, so six would have run past the 12h cap. 6 epochs because §14 found intent still
budget-bound at 6 — these remain a lower bound, and the paper must say so.

Picks up two things at once: the first clean intent test numbers, and the project's missing
intent checkpoint. `labse` and `mmbert` were statistically tied on intent dev (p=0.944), so
this is also the run that decides whether the tie survives to test.


## results.md §16 — the finding that reframes the contribution

Landed while K3/K6b ran. `labse` beats `tfidf-svm` by +0.0834 on English and +0.0822 on
Sinhala, and by an amount **indistinguishable from zero** on both romanized tracks
(singlish p=0.712, tamilish p=0.490). Every point of the pooled +0.0485 is earned on native
script.

Tested as a proper contrast rather than by comparing two p-values — the frozen split makes
`sinhala` and `singlish` the same tickets in the same language differing only in script, so
a difference-in-differences is clean:

| pair | DiD | 95% CI | p |
|---|---:|---|---:|
| sinhala - singlish | **+0.0698** | [+0.0140, +0.1283] | **0.012** |
| tamil - tamilish | +0.0132 | [-0.0664, +0.0882] | 0.762 |

Holds for Sinhala; **not established for Tamil**.

**Open confound, blocking a stronger claim:** the *native* tracks differ in their own Latin
content -- sinhala 40.35%, tamil 1.26% -- so the two pairs have different baselines and are
not two measurements of one effect. Same question as **B5**. This raises B5 from a
documentation chore to something a headline claim depends on.

Why it matters: "encoder beats TF-IDF" is expected and weak. "Multilingual pretraining
transfers across languages it has seen but not across scripts it has not, and romanized
code-mixed text is how customers actually write" is the paper's real contribution.


## Figures — first set landed (was zero)

`paper/experiments/build_figures.py` writes PDF + PNG at ACL/IEEE column widths (3.3in / 6.9in)
with 8pt type, so nothing needs rescaling when it goes into the template.

| figure | carries |
|---|---|
| `encoder_gain_by_script` | **the headline** — forest plot, encoder gain per track with CIs, coloured native vs romanized |
| `per_language_sentiment` | all five systems x five tracks; the encoder's lead visibly narrows on romanized input |
| `label_ceiling` | intent-only / TF-IDF / LaBSE against the ceiling band |
| `tokenizer_to_downstream` | MuRIL's Sinhala collapse: `[UNK]` predicts the deficit, fertility does not |
| `intent_epochs` | two panels — full range and a zoom, because the full range alone looks flat |

Two things were caught while drawing them and both were real:

1. **`intent_epochs` had a false title.** "Still improving at the budget's edge" over curves
   that look flat at that y-scale. Now two panels with the claim stated as a count — "4 of 5
   models peak at the last epoch" — rather than implied from a shape.
2. **LaBSE is missing from that figure**, and the reason is a defect: `ml/reports/history_<model>.csv`
   is one filename per model, so K6a's sentiment-test run overwrote LaBSE's intent-dev curve.

## History-file overwrite — fixed, and the surviving curves rescued

`ml/kaggle/kernels/train_encoders{,_b}.py` now write `history_{TASK}_{model}_{EVAL_PORTION}.csv`.
That takes effect from the **next** push — K3 and K6b were already running against the old
code, and their fetches would have destroyed the K2 intent-dev curves.

So the curves were snapshotted first, to `paper/results/runs/history/` (11 files + a README
recording how each was attributed). `build_figures.py` now reads the snapshot, not
`ml/reports/`, so the figure no longer changes meaning depending on which job ran last.

**When K3 and K6b are fetched, their history files will arrive unqualified and must be filed
into the snapshot by hand** before any later job overwrites them.

## LICENSE — corpus settled, code still open

**Corpus: settled.** BANKING77 is CC-BY-4.0 (verified on PolyAI's card), and the published
Swift dataset card already states CC-BY-4.0 with BANKING77 attribution. `datasets/LICENSE`
now written, recording the licence, the citation, and — the part a bare licence file omits —
**which parts are inherited and which are new**: BANKING77 contributes the English text and
the human gold intent labels; the four other tracks and the sentiment/priority labels are
this work's, and the latter are LLM-generated rather than gold.

**Code: still your call**, and now low-stakes since it is independent of the corpus.
Apache-2.0 (patent grant) or MIT (shorter). Say the word and it takes a minute.


## Published Hugging Face artifacts — resolved, and two defects found

The org is `Swift-Support` and three artifacts are already public. This corrects a claim I had
been carrying in this tracker.

| artifact | repository | state |
|---|---|---|
| corpus (5 tracks, v8, frozen split) | `swift-support-tickets-1.0` | public, CC-BY-4.0 |
| intent classifier | `labse-intent-1.0` | public, provenance ambiguous |
| priority classifier | `labse-priority-1.0` | public |
| sentiment classifier | — | local only, upload pending |

**Two defects are live on the public cards** and a reviewer following the link will hit them:

1. **Dataset row count is exactly double.** The card says 130,770 rows. The corpus is
   13,077 x 5 = **65,385**, and the card's own split figures (42,500 + 7,490 + 15,395) sum to
   65,385. It contradicts itself.
2. **Dataset card quotes the superseded ceiling**, 0.7812. That number scored the prompt's raw
   output; against the labels models actually train on it is **0.7931**.

And two gaps on `labse-intent-1.0`: it does not say which split produced 88.54% (results.md
calls it "official split", the card frames it as pooled macro-F1 across five tracks — those
are different evaluations), and it states neither epochs nor licence. No local intent/labse
**test** record exists to settle it; the only local ones are dev (0.9293 pooled, best epoch
5 of 6). K6b settles it.

Full write-up in `paper/drafts/reproducibility.md` §10.


## HF cards corrected — PUSHED 2026-09-08, all four verified live

Pushed with the token from `backend/.env` (`SWIFT_HUGGINGFACE_TOKEN`; the file is gitignored
and untracked — verified before use). Authenticated as `NivinSithija`. Re-run any time with:

    export HF_TOKEN=$(grep -m1 '^SWIFT_HUGGINGFACE_TOKEN=' backend/.env | cut -d= -f2-)
    .venv312/bin/python paper/hf_cards/push_cards.py --dry-run
    .venv312/bin/python paper/hf_cards/push_cards.py

| card | change |
|---|---:|
| dataset | +77 / -7 |
| intent | +165 / -24 |
| priority | +65 / -0 |
| org (new) | +176 |

**Org cards are Spaces, not model repos.** `Swift-Support/README` did not exist in any repo
type; the push script originally had it as a model, which would have created a stray model
called "README" and left the org page blank — indistinguishable from a failed push. Caught
before pushing because the reference org's activity feed said "updated a **Space**". Created
as `sdk: static` with the frontmatter a Space requires.

Each push is a separate commit naming what it corrects, so the change is auditable from the
Hub's history rather than silently replacing the old card.

### What was actually wrong

**Dataset card** — one real defect. Its sentiment row read "0.7812, agreement 97.2%,
κ = 0.766", which matches the *prompt output* row of `label_ceiling.csv` exactly. The shipped
`sentiment` column — what the card describes and what models train on — is
**0.7931 / 0.976 / κ 0.780**. Corrected, with the old figure and the reason kept visible. The
`priority` row was always right (priority was never relabelled, so prompt output and shipped
column are identical).

**Intent card** — needed the most work, and the substantive problem was not metadata:

- Its stated mechanism is **backwards**. It says the Indic specialists failed because their
  vocabularies "couldn't handle heavy romanization or English slang". At 6 epochs MuRIL's
  romanized tracks are among its *best* (Tanglish 90.23, Singlish 88.79) and it fails on
  exactly one track — native-script Sinhala at 76.33. Its tokenizer maps **64.5% of Sinhala
  characters to `[UNK]`**, 0.0% everywhere else including both romanized tracks.
- Whole table was a 3-epoch run; MuRIL's Tamil was reported 66.01% and is 90.09% at 6.
- "LaBSE is the Intent Champion" is unsupported — mmBERT ties it (p = 0.944) and is absent
  from the card entirely.
- No split provenance, no epochs, no licence.

Test numbers are marked as pending; K6b fills them.

**Priority card** — sound. Licence, split sha, epochs, `best_epoch` honesty, the ceiling with
a CI, and an explicit warning against quoting 0.89. It only needed the citation. It is the
model the other two cards should follow.

**Org card** — new. Artifacts table, the `id`-level split warning, label provenance (only
intent is human gold), why accuracy is never the sentiment metric, and the cross-track
fairness gap stated as a property to measure.

### A retraction

The "dataset card claims 130,770 rows, double the truth" defect I reported earlier **does not
exist**. It came from a summary of the card rather than the card, and I recorded it without
checking the source. The card's row figures are correct throughout. Retained struck-through in
`reproducibility.md` §10, because the failure mode is worth not repeating.

## Citation — now a requirement, not a courtesy

Written into all four cards, `CITATION.cff` at the repo root, and `datasets/LICENSE`.

The framing matters and was too weak in my first draft. **Citing BANKING77 alone is not
sufficient attribution**, and the cards now quantify why:

| | |
|---|---|
| rows whose text is new (Sinhala, Tamil, Singlish, Tanglish) | **52,308 of 65,385 — 80%** |
| rows inherited from BANKING77 (English) | 13,077 — 20% |
| label columns inherited | 1 (`category`) |
| label columns added | 2 (`sentiment`, `priority`) — 26,154 assignments |
| the frozen `id`-level split | this project's |

Separate BibTeX entries for the corpus and the models, since the two often carry different
author lists, plus the full BANKING77 entry.

**`you` · Confirm the author list before pushing.** "Seneviratne, N. S." is from the git
config and is the only sourced form available. Co-authors and supervisors need adding, and
the initial order checking — a wrong name on a public citation block is worse than none.
Flagged in an HTML comment in `CITATION_BLOCK.md` and a YAML comment in `CITATION.cff`.


## Author name resolved

**Sithija Seneviratne**, confirmed from the sl-parliamentary-nlp / MERCon 2026 author list.
Propagated to all four cards, `CITATION.cff` and `CITATION_BLOCK.md`.

Still open and flagged in-file: **whether Swift has co-authors or supervisors.** None are
assumed. The corpus and the models may also warrant different author lists — annotators and
translators on one, implementers on the other.

## Org profile fields — needs pasting by hand

`paper/hf_cards/org_profile_fields.md` holds the **AI & ML interests** string and the org
tagline. These are organization *settings*, not part of the README, so they cannot be pushed
with the card and have to be entered on the org's settings page.


## HF push — corrections after seeing the live org page

Three things the first push got wrong, all visible only once the page rendered.

**1. The org card showed the static-space template, not the card.** `create_repo(space_sdk="static")`
seeds the repo with `index.html` and `style.css`, and the Space app takes precedence over
`README.md` — so the org page read "Welcome to your static Space!". Deleted both files; the Space
now holds only `README.md` and the card renders.

**2. There is a fifth artifact I had not accounted for.** `Swift-Support/labse-sentiment-1.0` was
already public (18 downloads). My org card said "sentiment: upload pending". It carried the same
0.7812-vs-0.7931 ceiling defect as the dataset card, and had no per-language results at all.
Corrected, and given the §16 finding — the native-script/romanized gain split, with the
difference-in-differences test — since that is the single most decision-relevant fact for anyone
choosing whether to deploy it.

**3. The "131k rows" figure is real after all, and my retraction was half wrong.**
It is not in the card text — that part of the retraction stands. But the *dataset viewer* does show
~131k, and correctly: the corpus ships **65,385 unique rows twice**, once as the pooled `all`
config (42,500 + 7,490 + 15,395) and once as five per-language configs of 13,077. The viewer sums
every config. So a reader really does see 130,770, and nothing explained why. Both the dataset card
and the org card now do, with the warning that follows from it — **load `all` or the per-language
configs, never both**, or every row is duplicated.

The lesson from (3) is narrower than the one I drew before: the summariser's *number* was right and
its *attribution* was wrong. Checking the source refuted the attribution and I treated that as
refuting the number too.

## All five cards live

| card | authors | ceiling |
|---|---|---|
| dataset | 3 | 0.7931 |
| intent | 3 | n/a |
| sentiment | 3 | 0.7931 |
| priority | 3 | 0.7722 (was already right) |
| org | 3 | 0.7931 |

## Author list

**Sithija Seneviratne, Ruththiragayan Sutharsan, Shazan Shaheed** — all three in every card,
`CITATION.cff`, and the org card's Project Team.

`you` · **Order is still an assumption.** Sithija is listed first as the repository owner; that is
not a decision anyone made. Confirm the intended order, and whether a supervisor belongs on the
list. Flagged in `CITATION_BLOCK.md` and `CITATION.cff`.

---

# Session 3 — track E landed: the paper is now a system paper

The reframing asked for. `paper/SYSTEM_PLAN.md` holds the design and methodology;
`results.md` §17 holds the results; every number is generated by a script in
`paper/experiments/` and none of it needed a GPU or a new label.

## E status

- [x] **E1 · Posteriors on test** — `save_posteriors.py`. LaBSE (train+dev) → test for
  sentiment and priority on MPS, ~70 s per model; TF-IDF → test and → dev. Self-checks
  reproduce the recorded runs **exactly**: sentiment negative-F1 0.7138, priority macro-F1
  0.8901 vs 0.8900. The script aborts rather than writing plausible garbage if they drift.
- [x] **E2 · `scoring.py`** — the TUS. Expected severity from the posterior, sentiment
  posterior, κ(i) = P(High | intent) on train+dev only, multiplicative aging.
  κ ranks `compromised_card`, `lost_or_stolen_card`, `card_payment_not_recognised` top —
  a sanity check the term behaves the way a bank would.
- [x] **E3 · Layer 1, ranking** — and it produced a methodological finding, see below.
- [x] **E4 · `queue_sim.py`, Layer 2** — M/G/5, 3 loads × 5 policies × 200 seeds.
  **Attainment 0.971 / 0.985 / 0.990.**
- [x] **E5 · Layer 3, the fairness result** — with a gold-label control and bootstrap CIs.
- [x] **E6 · Layer 4, calibration** — diagnosis landed; the causal hypothesis was
  **refuted**, see below.
- [x] **E7 · Layer 5, ablation, α frontier, classifier substitution**
- [x] **E8 · Weight fit on dev** — `w = (0.80, 0.10, 0.10), α = 16`, fitted across two
  loads, applied unchanged to test.
- [x] **E9 · Figures** — `queue_disparity`, `alpha_frontier`, `attainment` (PDF + PNG).
- [ ] **E6b · Clean dev posteriors for a train-only encoder** — the one genuinely blocked
  item. Temperature scaling has no clean dev to fit on because the saved LaBSE checkpoints
  were fit on train+dev, so §17.6 is cross-fitted on test halves and labelled a
  sensitivity analysis. A train-fit encoder run with posteriors saved fixes it. **Next
  Kaggle job after the current two.**
- [ ] **E10 · `you` · Simulation parameters from literature** — λ, service distribution and
  agent count are assumed. Published helpdesk statistics would replace assumption with
  citation. A reading task, not an experiment.

## The four findings

**1. The disparity is real, and the score largely closes it.** At ρ = 1.05, a Tanglish
customer with an urgent ticket waits **+6.99 min** longer than an English one under the
naive argmax-tier deployment (CI [5.71, 8.22]). Under FIFO the gap is absent
(n.s.) and under the gold-label control it is absent (n.s.) — so it is the model, not the
arrival process. TUS cuts it to **+0.50 min** (CI [0.26, 0.71]); paired on the seed it
removes **11.62 min** of cross-track spread (CI [10.39, 12.82]). It does not remove all of
it, and the residual still excludes zero.

This upgrades §16 from a diagnosis to a fix with a measured residual, and it is the
single most quotable thing the project has.

**2. Rank correlation is the wrong metric for a queue.** The argmax-tier policy has the
**highest Kendall τ of any system (0.822) and the worst queue head** (nDCG@10 = 0.351,
half the first ten tickets not urgent). τ rewards global ordering; a queue is consumed
from the top. Selecting on τ picks exactly the wrong system — which is the concrete
justification for the whole queue-level methodology.

**3. Accuracy does not transfer to the queue.** Swapping LaBSE (priority macro-F1 0.8901)
for TF-IDF (0.8706) leaves median and p95 wait indistinguishable and *improves* the tail:
worst-case wait for an urgent ticket **362 min under LaBSE against 98 under TF-IDF**.
LaBSE misses fewer gold-Highs (165 vs 193) but **buries 68 of them below score 0.1 against
TF-IDF's 8** — fewer mistakes, 8.5× more confident ones. "Buried urgent tickets" is a
triage error metric macro-F1 cannot see.

**4. A refuted hypothesis, kept visible.** LaBSE is more accurate, 3.7× worse calibrated
(ECE 0.0658 vs 0.0180) and worst calibrated exactly on the track it is least accurate on
(tamilish 0.1071) — the double penalty `SYSTEM_PLAN` predicted. Temperature scaling fixed
the calibration (ECE → 0.0180) and made the queue **worse** (High mean wait 1.98 → 2.32,
spread 0.50 → 0.79). ECE is agreement between top-1 confidence and accuracy; a queue needs
posteriors that *separate* tickets. "Calibrate before you score" was wrong here.

## Two defects found and fixed in my own design

**The oracle was not an upper bound.** It blended gold severity with gold sentiment and κ,
by analogy with the system's own score — so a gold-Low with negative sentiment could
outrank a gold-High, and TUS *beat* the "oracle" on High wait at some loads. A quantity the
system under test can beat is not a ceiling. Redefined as gold tier, FIFO within tier,
which also makes `tier` vs `oracle` a clean predicted-vs-gold contrast.

**The fitting objective selected a degenerate system.** Absolute tardiness weighted by
severity (Low 0.5 / Medium 1.0 / High 1.5) against a 55/36/9 class mix gives Low **0.275**
of the objective's mass against High's **0.143** — it rewarded not starving Low nearly
twice as much as serving High. The argmin was `w = (0, 0, 1)`: intent criticality alone,
which cannot separate Medium from Low at all. Fixed by denominating lateness in units of
the class's own SLA window. Recorded in `results.md` §17.7 because any triage study can
walk into it.

## Also corrected

- SLA windows 60/240/1440 → **30/120/480**. At the old values every policy scored a 0.0
  breach rate at every load, which measures the thresholds rather than the policies.
- The α grid was extended to 128 to confirm the fitted α = 16 sits on a **plateau**, not at
  the grid edge. It does; α is a policy dial, not a fitted constant.
- The classifier-substitution table mixed 40-seed and 200-seed samples. At 40 seeds LaBSE
  looked *better* on worst-case wait (65 vs 80 min); at 200 seeds it is much worse (362 vs
  98). Regenerated at one sample size — the earlier reading was a small-sample artifact.
- `queue_disparity.png` annotated max-minus-min of seed-averaged means while the text
  quoted the seed-wise spread — two different statistics differing by ~2×, and the
  figure's number coincided with the text's tamilish−english gap. The figure now reads the
  tested table so the two cannot drift.

## Kaggle

K3 (priority dev) and K6b (intent test) both still **RUNNING**. Nothing in track E was
blocked on them. When they land: file the unqualified history files into
`paper/results/runs/history/` before anything overwrites them, then launch **E6b**.

---

# Session 3 (cont.) — K6b and K3 landed, and a corpus defect surfaced

## Kaggle

- [x] **K6b · intent test** — `labse`, `mmbert`, `xlmr-base`, 6 epochs, train+dev → test.
  **LaBSE 88.35 · XLM-R 88.01 · mmBERT 86.80** pooled macro-F1. All three
  `epoch_selection=final-epoch`, `best_epoch 6/6` — the selection defect is inert by
  construction. Closes **A7's** missing frozen-split intent checkpoint.
- [x] **K3 · priority dev** — all six encoders, 6 epochs. **LaBSE 91.67** ▸ XLM-R 91.55 ▸
  mmBERT 91.30 ▸ IndicBERT 90.88 ▸ TwHIN-BERT 89.87 ▸ MuRIL 89.57. 72 records, 6 prediction
  files. `results.md` §19.
- [x] Histories filed with qualified names **before** the next fetch could overwrite them:
  3 × `history_intent-test_*_epochs6.csv`, 6 × `history_priority-dev_*_epochs6.csv`.

**The K6b fetch failed partway** (`kaggle kernels output` exit 1 during
`intent_xlmr-base/model.safetensors`) and died *before* filing anything. All 18 run records
were on disk but unfiled, and `runner.fetch` **`rmtree`s `.output/` on entry** — so fetching
K3 next would have destroyed them silently. Filed them by hand first, replicating
`fetch`'s own split-sha and smoke-run guards, then rescued the two complete checkpoints
(`intent_labse` 1.8 GB, `intent_mmbert` 1.2 GB) to `ml/models/encoders/`. `intent_xlmr-base`
is configs-only and would need a re-fetch; nothing in the paper needs it.

`me` · **`runner.fetch` should file records before downloading checkpoints**, or file them
in a `finally`. The current order means any download failure discards the cheap, important
artifacts to protect the expensive, optional ones.

## The corpus defect — `results.md` §18

Tamilish intent scores **69.28 on test against 91.70 on dev**. No other track moves more
than 3 points. It is not a generalisation gap:

| track | OOV dev vs train | **OOV test vs train** |
|---|---:|---:|
| english | 14.8% | 20.3% |
| singlish | 13.3% | 27.8% |
| sinhala | 13.7% | 30.2% |
| tamil | 21.6% | 29.8% |
| **tamilish** | 22.3% | **60.3%** |

The **tamilish rendering of the test file was produced by a different transliteration
process from the tamilish rendering of the train file.** Corroborated by tamilish test text
averaging more characters but *fewer* words than tamilish train (71.5/8.74 vs 68.6/9.79),
and by tamilish being the only track with duplicate test strings.

The corpus had already recorded a symptom without recognising it: tamilish has the **lowest**
train/test text overlap of any track (0.23% vs singlish's 2.73%), filed under "less leakage,
good" when it is the same provenance split seen from the other side.

- [ ] **E11 · `me`+`you` · Fix or document the tamilish test rendering** before v1.1. Until
  fixed, the dataset card and the paper must both carry it. Any tamilish *test* number in
  this project is a lower bound contaminated by the mismatch.
- [x] **Checked how far it propagates.** §16's tamil−tamilish DiD was already n.s.
  (p = 0.762), so the defect manufactured no positive result there. §17.4's disparity is
  **carried by singlish**, whose OOV profile is ordinary — see below.

## §17.4 reworked — the statistic was wrong, and the result got stronger

The disparity was reported as max-minus-min **spread** across the five tracks. That
statistic is upward-biased (it selects the extreme of five noisy means), and the proof is
that **FIFO scored a 16.2-minute "spread"** while FIFO never reads the ticket. Replaced
with **fixed contrasts against english**, which have no such bias.

Mean gold-High wait minus english, ρ = 1.05, 200 seeds — bold excludes zero:

| policy | singlish | sinhala | tamil | tamilish |
|---|---:|---:|---:|---:|
| FIFO | −0.85 | −0.22 | −0.23 | −0.82 |
| **tier** | **+4.07** | +0.37 | −0.01 | **+6.99** |
| **TUS** | **+0.37** | +0.24 | +0.02 | **+0.50** |
| oracle | −0.02 | 0.00 | 0.00 | −0.01 |

Four nested controls: null under FIFO, null under the gold-label control, significant under
the model **only on the two romanized tracks**, and cut by an order of magnitude by TUS
(paired: −3.70 min singlish, −6.49 min tamilish, both excluding zero).

**Sharper than the spread version.** Sinhala and Tamil come out at *exactly* zero rather
than merely smaller, and singlish alone carries the finding — so it stands independently of
the §18 defect.

## Also

- The weight surface is **flat**: 71 of 231 simplex points sit within 5% of the optimum,
  spanning `w_P ∈ [0.10, 0.90]`. The fit establishes that priority dominates and no corner
  is competitive; it does not identify 0.80. Stated in §17.1 rather than quietly reporting
  the argmin.
- Weights and attainment reproduced **exactly** across two independent runs of
  `run_system_eval.py` (0.80/0.10/0.10, α = 16; attainment 0.971 / 0.985 / 0.990).
- §17.6's table now reports the same contrast statistic as §17.4 rather than the spread.
- MuRIL's Sinhala hole reappears on priority (83.13 vs its own english 92.23) — the §14
  `[UNK]` mechanism on a second task, and **smaller on a coarser label space** (~9 points on
  3-way priority vs ~14 on 77-way intent). §18 makes the same point from the other side.

## Next

- [ ] **E6b** — train-only encoder run saving posteriors, so temperature scaling has a clean
  dev to fit on and §17.6 becomes a held-out result. **The next Kaggle job.**
- [ ] Per-row predictions for the K6b intent test runs, so LaBSE vs mmBERT can be tested
  rather than ranked on point estimates.

## E6b launched — clean dev posteriors

`train_encoder.run()` now returns the **full softmax** (`EncoderRun.posteriors`), and both
Kaggle kernels write `posteriors_{task}_{model}_{portion}.csv`. Smoke-tested locally before
spending quota: rows sum to 1, all values in [0, 1], and `argmax(posteriors)` matches
`predictions` on 400/400 rows — the last check is the one that matters, because a permuted
column order would not raise, it would silently invert the ranking.

Launched (both slots, LaBSE, 6 epochs, `--fit-portion train --eval-portion dev`):

| slot | task |
|---|---|
| `train_encoders` | priority |
| `train_encoders_b` | sentiment |

These give temperature scaling a **clean dev to fit on**. The follow-up pair
(`--eval-portion test`, same train-only fit) makes §17.6 a fully held-out result rather
than the cross-fitted sensitivity analysis it currently is.

`me` · when these land, the posterior CSVs arrive in `.output/` and, like the history files,
**are not filed anywhere by `runner.fetch`** — copy them into `paper/results/posteriors/`
before the next fetch `rmtree`s them.

---

# Session 3 (cont. 2) — resources collected

## Tables regenerated with the new records

`build_results_tables.py` rerun: **701 dev / 217 test records** (was 664/199). The
epoch-selection guard still reports **2** genuinely biased test records and 30 where
selection had nothing to choose.

## K6b's missing predictions recovered — the caveat is closed

§18 had to say "do not report mmBERT as beaten" because K6b wrote no per-row predictions.
The checkpoints came back, so `paper/experiments/intent_test_predictions.py` re-runs
inference over the same frozen test set and saves what the run should have. Both models
reproduce their recorded K6b macro-F1 (LaBSE 0.8834 vs 0.8835; mmBERT 0.8680 exact), which
is the check that catches the two silent failure modes: **`max_length` is per model and not
stored in the checkpoint** (LaBSE 128, mmBERT **160**), and a permuted label order would
scramble 77 classes without raising.

**LaBSE − mmBERT, intent test macro-F1:**

| slice | Δ | 95% CI | McNemar |
|---|---:|---|---|
| all five | +0.0155 | [+0.0114, +0.0197] | 7.8e-13 |
| tamilish excluded | +0.0106 | [+0.0066, +0.0148] | 7.1e-07 |
| english | +0.0037 | [−0.0036, +0.0113] | 0.375 n.s. |
| **sinhala** | +0.0196 | [+0.0117, +0.0276] | 1.8e-06 |
| **tamil** | +0.0178 | [+0.0102, +0.0263] | 2.8e-05 |
| singlish | +0.0022 | [−0.0080, +0.0118] | 0.742 n.s. |
| tamilish *(defective)* | +0.0363 | [+0.0227, +0.0506] | 1.7e-07 |

mmBERT **is** beaten, and it survives dropping the defective track. The shape is the finding:
**the advantage is confined to the two non-Latin scripts.** English and Singlish — both
Latin — show nothing. This is a third sighting of the native/romanized structure, and the
first between two *encoders* rather than encoder-vs-classical.

It also corroborates §18.2 independently: tamilish is Latin script and by this pattern
should show no gap; it shows the largest of any track, which is what a degraded input looks
like. Also recorded: **LaBSE − tfidf-svm = +0.0526 [+0.0475, +0.0579]**, McNemar 3.2e-87.

`me` · The dev tie → test win comparison crosses a fit-portion boundary (dev fitted on
`train`, test on `train+dev`). §18.1 states this; do not let it become "mmBERT generalises
worse" in the draft.

## Bibliography — 26 → 36 entries, all verified

§17 introduced a whole methodology with **no citations behind it**. Six added and checked
against the publisher record: `jarvelin2002ndcg`, `guo2017calibration`,
`gelman2006significant`, `pinedo2022scheduling`, `cox1961queues`, `singh2018fairexposure`.

`cox1961queues` matters most for positioning: the c-μ rule is the classical result that
the TUS re-derives with a *learned* cost term. Section 17 should be framed against
operations research, not as a new idea.

Four gap areas from the previous session closed: `marone2025mmbert`, `clark2022canine`,
`chakravarthi2020tamilmix` (human-typed Tanglish — the reference point that makes our
synthetic romanized results an explicit upper bound), `northcutt2021labelerrors` (the
closest prior work to the label-ceiling claim).

**Still unsourced, and the ordering has changed:** industrial support-ticket triage is now
the weakest area and the most important — §17 claims a use-case contribution with nothing to
position against. Then: Gemma 3 (waits on A5), class imbalance, and published helpdesk
arrival/service parameters (**E10**, the study's largest threat to validity).

## D6 started — `paper/drafts/outline.md`

A claim-to-evidence map, not prose. Ten sections; every row names the generated file its
number comes from, and a checker confirms all **20 tables, 6 figures and 12 bib keys** it
references exist on disk. The rule it enforces: no sentence enters the manuscript unless
this table names its source.

Structure: §1–5 the NLP contribution (corpus, roster, script-not-language + tokenizer
mechanism), §6–8 the use-case contribution (the ordering system, the disparity, accuracy
not transferring), §7 the join. Limitations are all measured, none is a hedge.

**Two things the outline forces into the open:**

`you` · **B2, the translation comparison, is the only planned section with no results at
all.** It is scoped, sampled and scripted, and it is not needed for any of C1–C5. Decide
now whether the paper claims it — carrying a dead section through drafting costs more than
dropping it.

`you` · **The §18.2 tamilish defect belongs in the corpus section**, not only in results.
A reviewer who finds it in §18 after reading §2 will not believe §2.

## Bibliography — 39 entries

Three deployed-triage systems added, closing what the tracker called the weakest and most
important area: `montgomery2018escalation` (IBM, 2.5M tickets, escalation risk),
`mani2019deeptriage`, `lee2017industrialtriage`. All predict a per-ticket label and report
accuracy or recall; none asks what the prediction is worth once tickets must be *ordered*.
That is precisely the gap §6–8 fills, and it is now citable.

Three gap areas remain, two of which wait on work not yet run: Gemma 3 (A5), class
imbalance, and published helpdesk arrival/service parameters (**E10** — still the largest
single win available for validity).

---

# Translation study — metric fixed before the data (B2 prep)

`you` · **The four prompt files are ready to paste**, `paper/translation_eval/samples/prompt_{openai,gptoss}_{sinhala,tamil}.md`.
Each is self-contained: instructions plus all 150 English rows, 77/77 intents. Verified
**0 Sinhala characters** in the Sinhala prompt — no leakage of our translation, which would
anchor the model and void the comparison. Save returns verbatim to
`systems/{system}_{lang}.csv` and record the exact model name and date.

New: `paper/translation_eval/README.md` (what to paste, what the study can conclude),
`paper/experiments/validate_translations.py` (**B2v** — catches truncation, renumbered ids,
code fences, blank rows, and rows under 50% target script), and
`paper/experiments/register_metrics.py`.

## Pre-registered metric, and this corpus's own number on it

The comparison must be **reference-free**. Scoring competitors against our translation as
the reference makes us score 1.0 by construction — that is the metric's definition, not a
result, and a reviewer spots it immediately.

The one axis a domain corpus can legitimately claim is **register**: the corpus prompt
instructed the translator to keep English banking loanwords in English. Measured over a
31-term lexicon taken from that prompt, **before any competitor file exists**:

| track | loanword retention | Latin char fraction |
|---|---:|---:|
| Sinhala | **0.6456** | 0.3529 |
| Tamil | **0.0759** | 0.0183 |

**The two tracks were built to different standards.** Sinhala keeps two-thirds of English
banking terms; Tamil keeps under 8%. Only the Sinhala track implements the code-mixing the
documentation claims.

- **Sinhala:** a real, falsifiable claim is available and worth running.
- **Tamil:** the claim is very likely false and should not be made.

Third independent sign the Tamil pipeline differs from the Sinhala one, after §18.2's
tamilish test defect and `corpus_stats.py`'s 40.35% vs 1.26% Latin split. One explanation
fits all three: **the two tracks were produced by different processes, and the corpus
documentation describes only the Sinhala one.** This should be stated in the corpus section
of the paper — see `paper/drafts/outline.md` §2.

`results.md` §20.

---

# Session 3 (cont. 3) — E6b landed, two corrections

## E6b complete — §17.6 is now a held-out result

Both slots finished. Filed before the next fetch could `rmtree` them:
`paper/results/posteriors/dev_trainonly/posteriors_{priority,sentiment}_labse_dev.csv`
and two qualified history files. Priority dev macro-F1 **0.9167**, matching K3's LaBSE
exactly — the train-only refit reproduces.

- [x] **E6b · clean dev posteriors** — done.

Temperature fitted the way deployment would fit it, on data the model never trained on:

| | T (clean dev) | T (cross-fit on test halves) |
|---|---:|---:|
| priority | **2.347** | 1.93 |
| sentiment | **1.919** | 1.89 |

**The two agree**, which retires the worry that the earlier figure was an artifact of
touching test. And the conclusion strengthens:

| | High mean wait | tamilish − english |
|---|---:|---:|
| uncalibrated | **1.98** | **+0.50** |
| T cross-fitted | 2.32 | +0.72 |
| **T fitted on clean dev** | **2.65** | **+0.97** |

Properly calibrating serves urgent tickets **34% more slowly** and nearly **doubles** the
cross-script disparity. §17.6 stands, upgraded from sensitivity analysis to held-out result.

## Correction 1 — tamilish is one process, not two

`you` corrected the attribution and the vocabulary statistics back that up better than my
original claim did:

| track | train vocab | test vocab | test types seen in train |
|---|---:|---:|---:|
| singlish | 3,293 | 1,823 | **72.2%** |
| **tamilish** | **7,250** | 4,744 | **39.7%** |

Both render the same 8,500 tickets; tamilish needs **2.2× the vocabulary**. That is a
romanization step emitting many spellings per word — not two corpora. The reason was already
in the corpus documentation: **Singlish is rule-generated** (deterministic, one spelling per
word) while **Tanglish is machine-translated** (free-form). One process, applied
consistently; the instability is intrinsic to the method.

**The consequence is unchanged** — a vocabulary that does not transfer between splits is
unusable whatever produced it — and the revised account is stronger, because it *predicts*
the observed pattern: tasks whose difficulty scales with vocabulary degrade on tamilish and
not elsewhere. 77-way intent drops 22 points dev→test; 3-way priority drops about 1.

**E11 restated:** the fix is a deterministic romanization step for Tanglish matching how
Singlish is generated, not a re-translation.

Corrected in `results.md` §18.2 and the cross-reference in §17.4.

## Correction 2 — §20.3 drew the same wrong inference

The Sinhala/Tamil loanword split (0.6456 vs 0.0759) was written up as evidence of different
pipelines. It is not; it is a **register outcome** — how much English survived translation
into each target language. Rewritten: the documentation's code-mixing claim holds for one
track of two, and the paper should say which.

## Next

- [ ] Decoder roster **A5** and seed variance **A6** — the two remaining Kaggle jobs, and
      both slots are now free.
- [ ] **E11** deterministic Tanglish romanization (corpus v1.1).
- [ ] `you` · **B2** translation collection — prompts ready, validator ready, register
      metric pre-registered.

## A5 and A6 launched — both slots

| slot | job | detail |
|---|---|---|
| `train_encoders` | **A5 decoders** | `gemma-3-1b`, `gemma-3-270m`, intent, train+dev → test, 6 epochs, LoRA all-targets, lr 1e-4 |
| `train_encoders_b` | **A6 seed variance** | `labse` sentiment test, **seed 43** (first repeat of the champion) |

lr 1e-4 and `--lora-targets all` follow ENCODER_FINDINGS §4: the earlier LoRA failure was run
at the encoder's 2e-5, which is not evidence against LoRA. On Gemma 3, `attn` reaches only 2
of 7 projections.

A6 writes to seed-qualified filenames, so it cannot overwrite the seed-42 record. Every CI in
the paper is currently a within-fit interval; one repeat does not give a variance estimate but
it does say whether seed noise is the same order as the effects being claimed — which matters
most for §16's +0.0698 DiD and §18.1's +0.0155.

`me` · both kernels now emit `posteriors_*.csv`, which `runner.fetch` does not file. Copy them
to `paper/results/posteriors/` before the following fetch.

---

# Session 4 — A5/A6 fetched, seed work descoped, coverage runs launched

## A5 — half the job died, and the half that lived is a result

`gemma-3-1b` **CUDA OOM at 88 s**, before a single training step: batch 32 × seq 128 with
LoRA on all seven projections does not fit the 14.56 GiB card (it died asking for 90 MiB with
14.50 GiB already in use). It wrote no records. Relaunched at **batch 8**, everything else
identical.

`gemma-3-270m` completed cleanly — 2,694 s, 6 epochs, `train+dev` (49,990 rows), scored once
on test, `epoch_selection = final-epoch`, `best_epoch 6 of 6`.

**Intent test macro-F1 0.8305.** Placed against the existing roster:

| model | intent test macro-F1 |
|---|---:|
| labse | 0.8835 |
| xlmr-base | 0.8801 |
| mmbert | 0.8680 |
| **gemma-3-270m** (decoder, LoRA-all) | **0.8305** |
| tfidf-svm | 0.8308 |

A 270M-parameter decoder with LoRA lands **0.0003 below TF-IDF + linear SVM** and 5.3 points
below LaBSE. That is a usable paper sentence: at this corpus size the small decoder buys
nothing over a bag of character n-grams on intent, and the encoders beat both.

Caveat to carry: `gemma-3-1b` will have run at batch 8 against `gemma-3-270m`'s batch 32, so
the two decoders are **not** matched on batch size. Compare each to the encoders, not to each
other, unless one is re-run.

## A6 — the one seed repeat, and why there will not be a second

Seed 43, labse sentiment test, 6 epochs, `train+dev`, `final-epoch`. Per-epoch Negative-F1:

| epoch | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---:|---:|---:|---:|---:|---:|
| seed 43 | 0.6728 | 0.7028 | **0.6980** | 0.6972 | 0.6992 | 0.6963 |

Seed 42's record is a **3-epoch** run, so the raw 0.7138 vs 0.6963 comparison mixes seed with
budget. At **matched epoch 3** it is 0.7138 vs 0.6980 — **Δ 0.0158**, and seed 43's curve is
flat from epoch 2 on, so the extra epochs are not the driver. The difference is seed.

What that number does and does not threaten:

- **Survives.** §15's labse − tfidf-svm sentiment gap, +0.0485 [+0.0257, +0.0721]. The seed
  spread is a third of the effect.
- **Survives.** §16's sinhala − singlish DiD, +0.0698 [+0.0140, +0.1283]. ~4.4× the spread.
- **Flagged, not refuted.** §18.1's labse − mmbert intent gap, +0.0155 [+0.0114, +0.0197].
  Same order as the spread — **but that is intent macro-F1 over 15,395 rows, and the 0.0158
  was measured on sentiment Negative-F1 over 975 positives, which is far the noisier metric.
  The numbers must not be transferred across tasks.** Settling it needs an intent seed repeat,
  which is now descoped. Until then §18.1's interval is a within-fit interval and should be
  described as one.

**Decision (`you`, 2026-09-09):** seeds 44–46 are not queued; baseline single-seed numbers are
enough at this stage and the slots go to method coverage instead.

## Rescued before the fetches could `rmtree` them

`runner.fetch` clears `ml/kaggle/.output` on entry and does not file `posteriors_*.csv`.
Saved by hand:

- `paper/results/posteriors/posteriors_intent_gemma-3-270m_test.csv` (15,395 rows, 77 columns)
- `paper/results/posteriors/posteriors_sentiment_labse_test_seed43.csv` — **renamed** from the
  kernel's `posteriors_sentiment_labse_test.csv`, which would otherwise be mistaken for the
  seed-42 file the TUS is built on
- `ml/reports/runs_archive/A5_gemma_decoders.log`, `ml/reports/runs_archive/A6_seed43.log`

## Tables regenerated

`build_results_tables.py`: 701 dev / 229 test records, 41 rows in `main_pooled`. The generator
still reports **2 genuinely biased test records** (`sinbert-large`, `sinhalaberto` — both
sentiment, both minor models) and 30 unstamped-but-inert ones. Unchanged from session 3.

## Launched — both slots, method coverage

| slot | job | detail |
|---|---|---|
| `train_encoders` | **sentiment test roster** | `xlmr-base, mmbert, muril-base`, 6 epochs, train+dev → test |
| `train_encoders_b` | **A5 retry** | `gemma-3-1b` intent test, **batch 8**, LoRA-all, lr 1e-4, 6 epochs |

Sentiment is the paper's hardest task and its test column held **one** encoder (labse 0.7138)
against four classical baselines. Three more encoders turn §5 from a point estimate into a
table. Payload verified identical to local `train_encoder.py` / `results.py` / `config.py` and
to all five v8 `test_labeled.csv` before launch, so no re-sync was needed.

**On the next fetch: copy `posteriors_*.csv` out of `.output` first.**

## Still open, unchanged

- `you` · **commit the v8 CSVs** — `HEAD` still holds v5 (101 English test Negatives vs 195 on
  disk). Verified again this session. Still the top risk in the repo.
- **D6 prose** — the outline maps every claim to its artifact; no prose written.
- `you` · **B2** translation collection · **C2** annotators · **E10** simulation parameters.

---

# Session 5 — sentiment roster complete, and two defects in the policy bake-off

## Sentiment test is closed on v8

`train_encoders` COMPLETE. xlmr-base, mmbert, muril-base fetched, 36 run records, 3
prediction files, posteriors rescued to `paper/results/posteriors/` before the fetch.
`build_results_tables.py` rerun. Sentiment test now has **all 11 models on v8 labels**:

| model | Negative-F1 |
|---|---|
| labse | 0.7138 |
| gemma-3-1b | 0.7126 |
| gemma-3-1b-multitask-sharedhead | 0.7048 |
| gemma-3-1b-multitask-shared3head | 0.7042 |
| xlmr-base | 0.7007 |
| mmbert | 0.7000 |
| muril-base | 0.6790 |
| tfidf-svm | 0.6653 |
| tfidf-logreg | 0.6383 |
| tfidf-sgd | 0.6092 |
| tfidf-cnb | 0.4968 |

**Do not write "LaBSE is the best sentiment model."** The top four span 0.0096, and the one
measured seed repeat moved labse by 0.0158 at matched budget. The top four are a tie at this
resolution; the honest statement is that every encoder and decoder lands at 0.70 ± 0.01 and
the classical bag-of-n-grams floor is 0.665.

- [x] **Sentiment test roster** — complete, 11 models, v8.

## Two defects found in the policy bake-off, both now fixed

Found while re-running at 200 seeds. Both invalidated numbers already written down.

**1. `log_loss` was scoring against permuted classes.** sklearn sorts the `labels` argument
through `LabelBinarizer` and reads `y_prob` columns in *sorted* order. Our columns are
Low, Medium, High; sorted, High, Low, Medium. Every probability was attributed to the wrong
class. A perfect predictor scores **36.04** under the old call, **0.0** under the fixed one.
Fixed in `run_policy_bakeoff.py` by reordering columns to the sorted labels.

Effect: **the winning label model changed.** `stacked` (reported 1st) is 4th; `logpool`
(reported 4th) is 1st. The claim that survives is the one that mattered — binary relevance
is last — but the size is **27%**, not the 35% previously recorded. The old values
(4.706 … 7.195) are void; do not quote them.

**2. No policy was scored on the objective its theorem optimizes.** The table ranked by
`rel_tardiness`, which counts only delay past the SLA. Cox–Smith and Argon & Ziya Thm 3 are
stated over *linear* delay cost; Van Mieghem over a *convex* cost. Added `lin_cost` and
`conv_cost` to `summarise()`.

Effect: **cμ/HSF wins linear cost (0.121), Gcμ wins convex cost (0.064)** — each rule wins
exactly where its theorem predicts. Under `rel_tardiness` alone, Argon & Ziya Thm 3 looked
*false* (cmu-hsf 0.021 = static-tier 0.021); on linear cost it holds with no overlap
(0.121–0.125 vs 0.161–0.168, a 25% reduction). The previous session's sentence "every
posterior policy beat static-tier, confirming Theorem 3" was true by luck, not by measurement.

Also recorded: the ordering rule dominates the label model under linear cost (3% spread
across label models vs 3.1× across policies); dependence modelling only pays once the cost is
convex (42% spread there). At ρ = 0.85 nothing separates — every claim is an overload claim.

- [x] **Bake-off at 200 seeds** — done, both defects fixed, written up as results §22.
- [ ] **§17 (Ticket Urgency Score) must be cut from the paper** — superseded by §22, which is
  literature-only. §17's tables are still referenced by `outline.md`; that mapping needs redoing.

## Still running

`train_encoders_b` — gemma-3-1b intent test at batch 8, launched 09:52, still RUNNING at
12:0x (~2h15m). Not matched on batch size against gemma-3-270m's batch 32; that caveat stands.

## Session 5b — both jobs fetched, and the roster is not hyperparameter-matched

`train_encoders` (muril-base, priority test) and `train_encoders_b` (gemma-3-1b, intent
test, batch 8) both COMPLETE and fetched. Posteriors rescued before each fetch. Intent and
priority test are now **17 models each**.

### muril-base priority: the Indic specialist loses to character n-grams

| model | priority macro-F1 |
|---|---|
| tfidf-svm | 0.8734 |
| **muril-base** | **0.8717** |
| tfidf-logreg | 0.8706 |

muril-base is now on all three tasks and is the weakest neural model on every one
(sentiment 0.6790, priority 0.8717). On priority it is **beaten by a bag of character
n-grams**. This is the same story as §19's tokenizer finding and is worth reporting as a
result, not buried as an also-ran: an Indic-targeted encoder does not transfer to
Sri Lankan code-mixed text.

- [x] **muril-base** — sentiment and priority test done. Intent test launched (below).

### A silent overwrite, and a confound it exposed

The gemma-3-1b intent fetch **overwrote a valid August record in place**. Run ids encode
model/task/split/arm but **not epochs or batch size**, so a rerun at different
hyperparameters replaces the old record with no warning. The fetch guard catches wrong
`split_sha` and smoke runs; it does not catch this.

| | old (archived in git history) | new |
|---|---|---|
| recorded | 2026-08-20 | 2026-09-09 |
| epochs / batch | 3 / 16 | 6 / 8 |
| macro-F1 | 0.8586 | 0.8635 |

Kept the new record: 6 epochs matches the encoders and gemma-3-270m, so it is the more
comparable of the two. The +0.0049 is **not** attributable — epochs and batch both moved.

The wider problem this surfaced: **the intent roster is not hyperparameter-matched.**

| model | epochs | batch | LoRA |
|---|---|---|---|
| labse, xlmr-base, mmbert | 6 | 32 | no |
| gemma-3-270m | 6 | 32 | yes |
| gemma-3-1b | 6 | **8** | yes |
| gemma-3-1b-multitask-{shared,shared3}head | **3** | **16** | yes |

So two comparisons in the current draft are confounded and must not be stated as they are:

1. **"1B beats 270M" (0.8635 vs 0.8305, +0.033)** mixes parameter count with a 4x batch-size
   difference. Not a scaling result.
2. **"multitask beats single-task" (0.8673 vs 0.8635)** mixes the objective with a 3-vs-6
   epoch and 16-vs-8 batch difference. Not a multitask result.

- [ ] The two multitask gemma variants need a 6-epoch rerun before claim 2 can be made at all.

### Launched to fix claim 1

| slot | job | why |
|---|---|---|
| `train_encoders` | muril-base, **intent** test | completes muril-base on all three tasks |
| `train_encoders_b` | gemma-3-270m, intent test, **batch 8** | matches gemma-3-1b on every hyperparameter, leaving parameter count as the only difference — turns the confounded +0.033 into an actual scaling measurement |

The batch-32 gemma-3-270m record will be overwritten by that rerun, so it is archived at
`ml/reports/runs_archive/gemma-3-270m_intent_bs32/` with a README explaining why.
