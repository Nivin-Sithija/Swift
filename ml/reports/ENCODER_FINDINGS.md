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

## 6. Linear probing — how much was there before fine-tuning

Backbone frozen, no gradient reaches it; one forward pass per row, then a logistic regression on
the pooled vector (`swiftbench/probe.py`, driven from `17_encoder_linear_probe.ipynb`). Extraction
is paid once per backbone and reused across all three tasks, so the whole roster costs one pass.

Pooled dev, `class_weight`, best pooling per cell. `retained` = probe ÷ fine-tune.

| task | backbone | probe | fine-tune | retained |
|---|---|---|---|---|
| **intent** | labse | **0.8614** | 0.9224 | **0.934** |
| | gemma-3-1b | 0.8570 | 0.9243 | 0.927 |
| | mmbert | 0.8170 | 0.9280 | 0.880 |
| **priority** | labse | **0.8265** | 0.9168 | **0.901** |
| | gemma-3-1b | 0.7887 | 0.9165 | 0.861 |
| | xlmr-base | 0.7643 | 0.9162 | 0.834 |
| | canine-c | 0.6565 | 0.8786 | 0.747 |
| **sentiment** | labse | **0.4666** | 0.6334 | **0.737** |
| | gemma-3-1b | 0.4391 | 0.6428 | 0.683 |
| | mmbert | 0.4137 | 0.6203 | 0.667 |
| | canine-c | 0.3164 | 0.5323 | 0.594 |

**Retention is ordered intent > priority > sentiment for every single backbone**, with no
exceptions across seven models. Intent is 88–93% linearly decodable from a representation that
never saw our data; sentiment is 59–74%. Fine-tuning does the most work on exactly the task whose
labels agree with humans least (κ=0.55 vs priority's 0.64).

**LaBSE wins the probe on all three tasks and retains the most on all three** — the same model the
fine-tune bake-off chose, now shown to have been the best *before* any training. Its advantage is
in the pretrained representation, not in how it responds to our labels.

### What fine-tuning changes is task-specific and does not transfer

Both saved checkpoints probed against pretrained LaBSE. **Scored on test** — they were fit on
`train+dev`, so dev is inside their training data (see the trap below).

| probe (test) | pretrained labse | labse-ft-sentiment | labse-ft-priority |
|---|---|---|---|
| sentiment | 0.3735 | **+0.1075** | +0.0132 |
| priority | 0.8015 | +0.0025 | **+0.0810** |
| intent | 0.7822 | −0.0146 | +0.0150 |

The diagonal is large and everything off it is noise. Fine-tuning for sentiment buys nothing for
priority and *costs* a little on intent.

**What this rules out, precisely:** fine-tuning one backbone on one task, freezing it, and hanging
the other two tasks' heads off it. That does not work — the representation moves toward its own task
only.

**What it does not rule out**, and must not be read as ruling out: **joint** multi-task fine-tuning
(all three losses updating one backbone together), or **LoRA adapters over a shared frozen base**
(`RESULTS.md` §14.8's proposal — one backbone plus three ~26 MB adapters). Both keep a per-task path
into the backbone, which is exactly the thing the probe shows you need. Neither has been measured.

How much of the fine-tuned model lives in the head, on test:

- **priority** — ft-probe 0.8825 vs the full fine-tuned model's 0.8900. The head adds **0.0075**;
  the fine-tuned representation is essentially linearly separable already.
- **sentiment** — ft-probe 0.4810 vs 0.5664. The head adds **0.0854**, eleven times priority's.

### A frozen backbone is not servable here

Pretrained LaBSE probe on test — priority **0.8015**, intent **0.7822** — sits *below* the classical
TF-IDF champion (0.8722 and 0.8318). The cheap-serving idea (one frozen encoder, three logistic
regressions, no fine-tuning) is measured and **rejected**: it loses to a model that fits in a
joblib.

### TwHIN-BERT was right about romanized text, and the fine-tune hid it

Native-script minus romanized, averaged (`(sinhala+tamil)/2 − (singlish+tamilish)/2`), pooled dev:

| backbone | sentiment | priority | intent |
|---|---|---|---|
| **twhin-bert** | **0.032** | **0.012** | **0.003** |
| canine-c | −0.021 | −0.001 | −0.022 |
| gemma-3-1b | 0.014 | 0.021 | 0.051 |
| labse | 0.113 | 0.075 | 0.027 |
| mmbert | 0.034 | 0.057 | 0.087 |
| xlmr-base | 0.081 | 0.064 | 0.077 |

§3 predicted TwHIN-BERT would handle the code-switched register and the fine-tune said it did not.
The probe says §3 was right about the *representation*: TwHIN-BERT is the most script-agnostic
model in the roster on all three tasks, and CANINE — character-level — is the only other one near
it. They lose on absolute quality, not on script transfer. LaBSE buys its lead on native script and
gives back the most on romanized. **This does not change the ship decision** (LaBSE still wins every
romanized cell outright) but it is the first evidence separating "handles romanized well" from
"is good at the task", and it is invisible to a fine-tune.

Caveat unchanged from §3: our Singlish is rule-generated and Tamilish machine-translated, so these
gaps are an optimistic floor. Real human-typed romanized text would widen every one of them.

### Four traps, all silent, all caught in the build

Recorded because each produced a plausible number and none raised anything.

1. **Unit-norm features do not fit at `C=1`.** Row L2-normalisation is required for cross-model
   comparability, but it makes each feature O(1/√dim) and the penalty then dominates: lbfgs stopped
   after **4 iterations** and intent read **0.167**. A `StandardScaler` in front of the regression —
   same vectors, same `C` — gives **0.807**. `probe.fit()` now reports `n_iter`.
2. **Gemma pads on the left.** `mask.sum(1) - 1` for last-token pooling indexes into the padding.
   Intent read **0.0768** against 0.7990 for the same model's mean pooling — low enough to look like
   a finding about decoders. Corrected (scan the mask from the right) it is **0.7918**, and last-token
   pooling in fact *beats* mean on sentiment and priority.
3. **The saved checkpoints cannot be scored on dev.** Fit on `train+dev`, so `labse-ft-priority`
   probed 0.9645 against its own fine-tune's 0.9168 — memorised rows presenting as a breakthrough.
   `probe.score()` refuses the combination now; 72 contaminated records were deleted.
4. **Pooling is per-model, and it matters.** LaBSE prefers **cls** on sentiment and priority (its
   dual-encoder objective optimised that position); every MLM encoder prefers **mean**, by up to
   0.048 on twhin-bert priority and 0.168 on canine-c intent. One fixed convention would have
   measured where a model stores sentence meaning rather than whether it encodes the task.

`C` was checked once on LaBSE rather than swept per cell: the optimum is 0.01–0.1 and the `C=1.0`
default costs 0.017 on intent, 0.005 on priority, 0.000 on sentiment (`probe_C_sweep.csv`).

## Cross-cutting decisions

1. **Champion = multilingually fine-tuned LaBSE** for both sentiment and priority. §6 strengthens
   this: LaBSE also wins the *frozen* probe on all three tasks, so its lead is in the pretrained
   representation rather than in how it responds to our labels.
2. **No per-language models, no LoRA, no TwHIN-BERT** — none beat multilingual LaBSE on our data.
   §6 adds a caveat to the TwHIN-BERT half: its *representation* is the most script-agnostic in the
   roster (native-minus-romanized gap 0.003–0.032 against LaBSE's 0.027–0.113). It still loses on
   absolute quality everywhere, so the decision stands, but the reason it loses is quality, not
   script handling.
3. **Romanized tracks are unresolved by our data** (synthetic Singlish/Tamilish). Real human-typed
   romanized text is required before trusting any romanized-specific conclusion; transliteration
   (Strategy A) was deliberately not run for the same reason.
4. **Rank on the confidence interval, not the point estimate** — several dev leads did not survive
   to test, and per-language cells are too small to order reliably.
5. **No "fine-tune once, freeze, add heads".** §6 finds what fine-tuning puts into the representation
   is task-specific: a sentiment fine-tune adds +0.108 to the sentiment probe and +0.003 to priority.
   A backbone frozen after one task's fine-tune carries nothing for the other two. This says nothing
   about *joint* multi-task fine-tuning or per-task LoRA adapters — both keep a path into the
   backbone and remain untested.
6. **No frozen-backbone serving.** A pretrained LaBSE probe on test (priority 0.8015, intent 0.7822)
   loses to the classical TF-IDF champion (0.8722, 0.8318). If a transformer is served at all, it
   has to be fine-tuned.

## Reproducing

- Run JSONs: `ml/reports/runs/{sentiment,priority,intent}__*.json` (each stamped with the split sha).
  Probe runs carry `family: "probe"` and a model name of `<backbone>-probe-<pooling>`.
- Notebooks: `32_final_test_classical`, `33_final_test_encoders`, `34_per_language_findings`,
  `35_priority_encoders`, `17_encoder_linear_probe` (all under `notebooks/modeling/`).
- Probe tables: `probe_dev.csv` (264 cells), `probe_test_finetuned.csv`, `probe_C_sweep.csv`.
  The embedding cache under `ml/cache/` is gitignored and regenerates in one forward pass.
- GPU driver: `ml/kaggle/runner.py` (T4 pinned; supports `--task`, `--fit-portion`, `--eval-portion`);
  kernels in `ml/kaggle/kernels/`.
