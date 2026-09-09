# Swift — all results, one file

Every measured number in this project, consolidated. Generated **2026-09-05** directly from
`ml/reports/runs/*.json` (735 run records) plus the report CSVs — no figure here was retyped by
hand. Blank cells (`—`) mean **not run**, not zero; §8 lists the gaps explicitly.

Per-task reports remain the narrative source: [`ml/reports/v8_relabel_slm_results.md`](ml/reports/v8_relabel_slm_results.md)
(current), [`ENCODER_FINDINGS.md`](ml/reports/ENCODER_FINDINGS.md), [`RESULTS.md`](ml/reports/RESULTS.md),
[`final_test_results.md`](ml/reports/final_test_results.md). This file is the numbers only.

---

## 0. Four things that make cells non-comparable

Read these before comparing any two numbers in this file.

**(a) Two different splits.** Most of this project uses the **frozen swiftbench split**
`e7b5934392cd` — 8,500 train / 1,498 dev / 3,079 test per language track (42,500 / 7,490 / 15,395
pooled), drawn once on ticket `id` and fanned out to all five languages. The intent transformer
benchmark in §5 instead uses the **official BANKING77 split** (9,998 train / 3,079 test, no dev).
**Numbers from the two splits cannot be tabled against each other**, and the official-split runs
carry no split-sha stamp and no `runs/*.json` record.

**(b) Two different sentiment label sets.** The v8 relabel (2026-08-19) changed 711 of 13,077
sentiment labels. Any sentiment number recorded before that date scores against **v5** labels and
is **not comparable** to a v8 number — the test set went from 505 to 975 Negatives, which moves the
metric on its own. Every sentiment table below is split by label version. Intent and priority were
untouched by v8.

**(c) Dev is not test, and some checkpoints saw dev.** Models fit on `train+dev` (all §1 test rows)
have dev inside their training data and **must not** be scored on dev — doing so reads as a
breakthrough (`labse-ft-priority` probed 0.9645 against its own 0.9168). Dev tables in §3–§4 are
fit on `train` only.

**(d) Two test numbers below had their epoch chosen on the test set — not, as first stated,
all of them.** Added 2026-09-08, corrected the same day.
`train_encoder.run()` and both `train_multitask` training functions selected the best epoch by
scoring `eval_df` — which on a test run **is the test set**. Where that mattered the reported
figure is a maximum over `epochs` draws rather than a held-out estimate.

**It only mattered where selection had something to choose.** Where the argmax epoch *is* the
final epoch, "max over `epochs` draws" and "the last draw" are the same draw and the bias is
exactly zero. Counted by `paper/experiments/build_results_tables.py`:

| | records |
|---|---:|
| classical + probe (no epoch loop at all) | 24 — clean by construction |
| unstamped test records where `best_epoch == epochs` | **15 — selection inert, bias exactly zero** |
| unstamped test records where `best_epoch < epochs` | **2 — genuinely biased** |

The two genuinely biased records are `sinbert-large` (best epoch 2 of 3) and `sinhalaberto`
(best epoch 1 of 3), both sentiment, both minor models — **not** the headline systems.

This was confirmed empirically, not just argued: the `labse` sentiment test cell
(`best_epoch` 3 of 3) was re-run under the patched code and came back **bit-identical to 17
significant figures** (§15). §1.2's headline comparison is therefore sound as printed, and the
gap **can** be quoted — the earlier instruction not to is withdrawn.

The caveat that survives: inertness is a property of the *run*, not of the code. At a larger
epoch budget these same cells would not be inert — §14 shows `labse` peaking at epoch 3 of 6 on
dev — so any future run must use the patched path rather than rely on this.

Fixed 2026-09-08: dev runs may still pick their best epoch, test runs report their final epoch,
and every record now stamps `epoch_selection` (`best-on-dev` / `final-epoch`). Records without
that stamp predate the fix and are judged by `best_epoch` vs `epochs` as above.

**Metrics**: intent = macro-F1 (77 classes) · sentiment = **Negative-F1** (never accuracy — ~94%
Neutral) · priority = macro-F1 (~55/36/9% Low/Medium/High).

---

## 1. Headline — test set, pooled (frozen split `e7b5934392cd`)

Fit on `train+dev` (49,990 rows), scored **once** on test (15,395 rows). This is the decision table.

### 1.1 Intent — macro-F1
| model | family | headline | recorded |
|---|---|---:|---|
| `gemma-3-1b-multitask-sharedhead` | Decoder (joint MT) | **0.8673** | 2026-08-20 |
| `gemma-3-1b-multitask-shared3head` | Decoder (joint MT) | **0.8616** | 2026-08-20 |
| `gemma-3-1b` | Decoder (LoRA) | **0.8586** | 2026-08-20 |
| `tfidf-svm` | Classical | **0.8307** | 2026-08-20 |
| `labse-ft-priority-probe-mean` | Probe (frozen) | **0.7971** | 2026-08-09 |
| `labse-ft-priority-probe-cls` | Probe (frozen) | **0.7962** | 2026-08-09 |
| `labse-probe-mean` | Probe (frozen) | **0.7822** | 2026-08-09 |
| `labse-probe-cls` | Probe (frozen) | **0.7773** | 2026-08-09 |
| `labse-ft-sentiment-probe-mean` | Probe (frozen) | **0.7676** | 2026-08-09 |
| `labse-ft-sentiment-probe-cls` | Probe (frozen) | **0.7594** | 2026-08-09 |


> `tfidf-svm` here is the frozen-split classical intent run (0.8307). The classical intent baselines
> in §5 (83.18% pooled) are the **official**-split figures — different split, close by coincidence.

### 1.2 Sentiment — Negative-F1

**Only the six `v8` rows are current and mutually comparable.** The `v5` rows are the same models
scored against labels this project no longer ships; they are kept because the runs happened, not
because they can be ranked against the v8 block.

| model | family | headline | labels | recorded |
|---|---|---:|---|---|
| `labse` | Encoder | **0.7138** | v8 | 2026-08-19 |
| `gemma-3-1b` | Decoder (LoRA) | **0.7126** | v8 | 2026-08-19 |
| `gemma-3-1b-multitask-sharedhead` | Decoder (joint MT) | **0.7048** | v8 | 2026-08-20 |
| `gemma-3-1b-multitask-shared3head` | Decoder (joint MT) | **0.7042** | v8 | 2026-08-20 |
| `tfidf-svm` | Classical | **0.6663** | v8 | 2026-08-19 |
| `tfidf-logreg` | Classical | **0.6415** | v8 | 2026-08-19 |
| `xlmr-base` | Encoder | **0.5396** | v5 | 2026-08-01 |
| `mmbert` | Encoder | **0.5321** | v5 | 2026-08-01 |
| `labse-ft-sentiment-probe-mean` | Probe (frozen) | **0.4810** | v5 | 2026-08-09 |
| `canine-c` | Encoder | **0.4702** | v5 | 2026-08-01 |
| `labse-ft-sentiment-probe-cls` | Probe (frozen) | **0.4633** | v5 | 2026-08-09 |
| `labse-ft-priority-probe-mean` | Probe (frozen) | **0.3867** | v5 | 2026-08-09 |
| `labse-ft-priority-probe-cls` | Probe (frozen) | **0.3828** | v5 | 2026-08-09 |
| `labse-probe-mean` | Probe (frozen) | **0.3735** | v5 | 2026-08-09 |
| `labse-probe-cls` | Probe (frozen) | **0.3682** | v5 | 2026-08-09 |
| `sinhalaberto` | Encoder | **0.1296** | v5 | 2026-08-01 |
| `sinbert-large` | Encoder | **0.1182** | v5 | 2026-08-01 |


### 1.3 Priority — macro-F1

| model | family | headline | recorded |
|---|---|---:|---|
| `gemma-3-1b-multitask-sharedhead` | Decoder (joint MT) | **0.8904** | 2026-08-20 |
| `labse` | Encoder | **0.8900** | 2026-08-07 |
| `gemma-3-1b` | Decoder (LoRA) | **0.8898** | 2026-08-20 |
| `gemma-3-1b-multitask-shared3head` | Decoder (joint MT) | **0.8895** | 2026-08-20 |
| `mmbert` | Encoder | **0.8887** | 2026-08-02 |
| `xlmr-base` | Encoder | **0.8872** | 2026-08-02 |
| `labse-ft-priority-probe-cls` | Probe (frozen) | **0.8825** | 2026-08-09 |
| `labse-ft-priority-probe-mean` | Probe (frozen) | **0.8816** | 2026-08-09 |
| `tfidf-svm` | Classical | **0.8722** | 2026-08-01 |
| `tfidf-logreg` | Classical | **0.8683** | 2026-08-01 |
| `labse-ft-sentiment-probe-mean` | Probe (frozen) | **0.8040** | 2026-08-09 |
| `labse-probe-mean` | Probe (frozen) | **0.8015** | 2026-08-09 |
| `labse-probe-cls` | Probe (frozen) | **0.8008** | 2026-08-09 |
| `labse-ft-sentiment-probe-cls` | Probe (frozen) | **0.7990** | 2026-08-09 |


---

## 2. Test set, per language (frozen split, v8 labels)

**This section was rewritten 2026-09-09.** It previously said per-language test coverage was
thin and carried a single v8 sentiment row. The v8 roster runs each wrote six records (pooled
plus all five tracks), so coverage is now 8 models on sentiment, 7 on priority, 9 on intent,
with every track filled. The old §2.3 v5 table is deleted rather than kept as "superseded" —
v8 rows now exist for the same models, so nothing depends on it.

Every cell below is `label_version` v8 on split `e7b5934392cd`. `spread` is best track minus
worst track *within a model* — the number that says how unevenly a model serves the five
languages, which pooled accuracy hides entirely.

### 2.1 Priority — macro-F1

| model | family | English | Sinhala | Singlish | Tamil | Tanglish | **pooled** | spread | source |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `labse` | encoder | 0.9229 | 0.9179 | 0.8817 | 0.9130 | 0.8142 | **0.8900** | 0.1087 | re-scored |
| `xlmr-base` | encoder | 0.9234 | 0.9116 | 0.8780 | 0.8990 | 0.8229 | **0.8872** | 0.1005 | re-scored |
| `tfidf-svm` | classical | 0.9050 | 0.8848 | 0.8918 | 0.8854 | 0.7984 | **0.8734** | 0.1066 | run record |
| `muril-base` | encoder | 0.9095 | **0.8072** | 0.8861 | 0.9120 | 0.8412 | **0.8717** | 0.1048 | run record |
| `tfidf-logreg` | classical | 0.8987 | 0.8810 | 0.8889 | 0.8849 | 0.7985 | **0.8706** | 0.1002 | run record |
| `tfidf-sgd` | classical | 0.8953 | 0.8802 | 0.8831 | 0.8853 | 0.7805 | **0.8659** | 0.1148 | run record |
| `tfidf-cnb` | classical | 0.8643 | 0.8479 | 0.8540 | 0.8653 | 0.7782 | **0.8422** | 0.0871 | run record |

> **Two provenances in one table, which is why the column is there.** The `run record` rows
> come from `per_language.csv`, built from the per-track run JSONs. The `re-scored` rows were
> generated 2026-09-05 by re-scoring saved checkpoints, because those two models were
> originally scored pooled-only; LaBSE's re-scored pooled reproduces its recorded 0.8900 to
> +0.00005, which is the check that licenses mixing them. Do not compare a `re-scored` cell
> against a `run record` cell to three decimal places.
>
> **MuRIL's Sinhala is the outlier, and only its Sinhala.** At 0.8072 it sits **7 to 11 points
> below every other model on that track** — even `tfidf-cnb`, the weakest model in the table,
> holds 0.8479. Its other four tracks are unremarkable and competitive: English 0.9095 and
> Tamil 0.9120 are within 1.4 and 0.1 points of the best. MuRIL's pretraining covers 17 Indian
> languages **including Tamil and excluding Sinhala**, and that is exactly the shape of the
> damage — the one track its pretraining never saw.
>
> This is why pooled accuracy is the wrong summary. MuRIL loses pooled to a bag of character
> n-grams (0.8717 vs 0.8734) and reads as a mediocre model; it is a competent model with one
> hole, and the hole is the language the pooled average dilutes to a fifth of its weight.
>
> `tfidf-svm` wins **Singlish** outright (0.8918, beating every encoder including LaBSE's
> 0.8817). Romanized text is where character n-grams stay competitive with subword encoders.

### 2.2 Sentiment — Negative-F1

| model | family | English | Sinhala | Singlish | Tamil | Tanglish | **pooled** | spread |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `labse` | encoder | 0.7550 | 0.7139 | 0.6402 | 0.7535 | 0.6185 | **0.7138** | 0.1365 |
| `xlmr-base` | encoder | 0.7838 | 0.7215 | 0.6361 | 0.7473 | 0.5981 | **0.7007** | 0.1857 |
| `mmbert` | encoder | 0.7723 | 0.6766 | 0.6905 | 0.7386 | 0.6159 | **0.7000** | 0.1564 |
| `muril-base` | encoder | 0.7967 | 0.5577 | 0.6463 | 0.7465 | 0.6235 | **0.6790** | 0.2390 |
| `tfidf-svm` | classical | 0.7198 | 0.6412 | 0.6633 | 0.7249 | 0.5722 | **0.6653** | 0.1527 |
| `tfidf-logreg` | classical | 0.6995 | 0.6256 | 0.6545 | 0.6776 | 0.5074 | **0.6383** | 0.1921 |
| `tfidf-sgd` | classical | 0.6842 | 0.5954 | 0.6218 | 0.6608 | 0.4577 | **0.6092** | 0.2265 |
| `tfidf-cnb` | classical | 0.5139 | 0.5083 | 0.5302 | 0.5239 | 0.3738 | **0.4968** | 0.1564 |

> The same MuRIL pattern, sharper: **best English of any model (0.7967) and worst Sinhala of
> any model (0.5577)**, a 0.2390 within-model spread — the widest in the table. It beats
> LaBSE on English by 4 points and loses to it on Sinhala by 16.
>
> The ordering english > tamil > sinhala > singlish > tanglish holds for nearly every model,
> which tracks **script familiarity, not language family** — the two romanized tracks are the
> weakest even though their underlying languages are the strongest elsewhere.

### 2.3 Intent — macro-F1

| model | family | English | Sinhala | Singlish | Tamil | Tanglish | **pooled** | spread |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `labse` | encoder | 0.9412 | 0.9319 | 0.9034 | 0.9329 | 0.6928 | **0.8835** | 0.2484 |
| `xlmr-base` | encoder | 0.9402 | 0.9244 | 0.8987 | 0.9151 | 0.7067 | **0.8801** | 0.2335 |
| `mmbert` | encoder | 0.9374 | 0.9123 | 0.9013 | 0.9147 | 0.6566 | **0.8680** | 0.2808 |
| `gemma-3-1b` | decoder | 0.9358 | 0.9221 | 0.8962 | 0.9110 | 0.6281 | **0.8635** | 0.3077 |
| `tfidf-svm` | classical | 0.9180 | 0.8666 | 0.8793 | 0.8528 | 0.6127 | **0.8308** | 0.3053 |
| `gemma-3-270m` | decoder | 0.9209 | 0.8805 | 0.8539 | 0.8833 | 0.5909 | **0.8305** | 0.3300 |
| `tfidf-logreg` | classical | 0.9096 | 0.8595 | 0.8751 | 0.8302 | 0.5854 | **0.8189** | 0.3242 |
| `tfidf-sgd` | classical | 0.9079 | 0.8489 | 0.8646 | 0.8305 | 0.5669 | **0.8115** | 0.3410 |
| `tfidf-cnb` | classical | 0.7772 | 0.6732 | 0.7194 | 0.7234 | 0.4925 | **0.6792** | 0.2847 |

> Tanglish is the floor for every model without exception, and the gap is enormous: LaBSE
> scores 0.9412 on English and **0.6928 on Tanglish**. Intent has the widest spreads of the
> three tasks (0.23–0.34 against sentiment's 0.14–0.24).
>
> **Pooled ranking is not per-track ranking.** `tfidf-svm` outranks `gemma-3-270m` pooled
> (0.8308 vs 0.8305) while losing to it on English, Sinhala and Tamil — it wins only by
> degrading less on the two romanized tracks. A pooled table alone would not show this.

---

## 3. Dev set, per language — multilingual regime (`multi`)

One model trained on all five tracks, evaluated per track. Fit on `train` (42,500 rows), scored on
dev (7,490 pooled / 1,498 per track). **This is the richest per-language coverage in the project.**

Fine-tuned encoders and decoders were mostly scored pooled only; the frozen **probes** were scored
per language, which is why they carry full rows and the fine-tunes do not.

### 3.1 Intent — macro-F1

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `gemma-3-1b-multitask-sharedhead` | Decoder (joint MT) | — | — | — | — | — | **0.9284** |
| `mmbert` | Encoder | — | — | — | — | — | **0.9280** |
| `gemma-3-1b` | Decoder (LoRA) | — | — | — | — | — | **0.9232** |
| `labse` | Encoder | — | — | — | — | — | **0.9224** |
| `gemma-3-1b-multitask-shared3head` | Decoder (joint MT) | — | — | — | — | — | **0.9211** |
| `tfidf-svm` | Classical | — | — | — | — | — | **0.9201** |
| `tfidf-logreg` | Classical | — | — | — | — | — | **0.9104** |
| `tfidf-sgd` | Classical | — | — | — | — | — | **0.9050** |
| `gemma-3-270m` | Decoder (LoRA) | — | — | — | — | — | **0.9038** |
| `labse-probe-mean` | Probe (frozen) | 0.8780 | 0.8883 | 0.8507 | 0.8533 | 0.8368 | **0.8614** |
| `labse-probe-cls` | Probe (frozen) | 0.8781 | 0.8925 | 0.8450 | 0.8542 | 0.8254 | **0.8590** |
| `gemma-3-1b-probe-mean` | Probe (frozen) | 0.8557 | 0.8762 | 0.8362 | 0.8892 | 0.8278 | **0.8570** |
| `gemma-3-1b-probe-last` | Probe (frozen) | 0.8425 | 0.8675 | 0.8138 | 0.8776 | 0.8009 | **0.8408** |
| `twhin-bert-probe-mean` | Probe (frozen) | 0.8251 | 0.8482 | 0.8278 | 0.8042 | 0.8194 | **0.8249** |
| `mmbert-probe-mean` | Probe (frozen) | 0.8481 | 0.8455 | 0.7790 | 0.8590 | 0.7514 | **0.8170** |
| `xlmr-base-probe-mean` | Probe (frozen) | 0.8359 | 0.8427 | 0.7803 | 0.8338 | 0.7432 | **0.8074** |
| `mmbert-probe-cls` | Probe (frozen) | 0.8475 | 0.8075 | 0.7879 | 0.8164 | 0.7671 | **0.8054** |
| `tfidf-cnb` | Classical | — | — | — | — | — | **0.8048** |
| `gemma-3-270m-probe-mean` | Probe (frozen) | 0.7743 | 0.8199 | 0.8047 | 0.8410 | 0.7535 | **0.7990** |
| `gemma-3-270m-probe-last` | Probe (frozen) | 0.8071 | 0.8379 | 0.7749 | 0.8057 | 0.7334 | **0.7918** |
| `xlmr-base-probe-cls` | Probe (frozen) | 0.8474 | 0.8211 | 0.7494 | 0.8234 | 0.7089 | **0.7906** |
| `twhin-bert-probe-cls` | Probe (frozen) | 0.7885 | 0.8213 | 0.7638 | 0.7724 | 0.7402 | **0.7770** |
| `canine-c-probe-mean` | Probe (frozen) | 0.5910 | 0.6748 | 0.6848 | 0.6087 | 0.6421 | **0.6410** |
| `canine-c-probe-cls` | Probe (frozen) | 0.3252 | 0.5448 | 0.5457 | 0.4598 | 0.4851 | **0.4734** |


### 3.2 Sentiment — Negative-F1 · v8 labels

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `labse` | Encoder | — | — | — | — | — | **0.7331** |
| `gemma-3-1b` | Decoder (LoRA) | — | — | — | — | — | **0.7098** |
| `gemma-3-1b-multitask-shared3head` | Decoder (joint MT) | — | — | — | — | — | **0.7046** |
| `gemma-3-1b-multitask-sharedhead` | Decoder (joint MT) | — | — | — | — | — | **0.6857** |
| `tfidf-svm` | Classical | 0.6323 | 0.6443 | 0.6486 | 0.6486 | 0.6509 | **—** |
| `tfidf-logreg` | Classical | 0.6038 | 0.6058 | 0.6010 | 0.6354 | 0.6310 | **—** |
| `tfidf-sgd` | Classical | 0.5926 | 0.6329 | 0.6012 | 0.6118 | 0.5578 | **—** |
| `tfidf-cnb` | Classical | 0.4520 | 0.4912 | 0.5541 | 0.4667 | 0.4795 | **—** |


### 3.3 Sentiment — Negative-F1 · ⚠️ v5 labels (superseded)

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `labse` | Encoder | 0.6569 | 0.6713 | 0.6475 | 0.6324 | 0.5512 | **—** |
| `mmbert` | Encoder | — | — | — | — | — | **0.6203** |
| `twhin-bert` | Encoder | 0.6533 | 0.6133 | 0.5594 | 0.6259 | 0.5342 | **0.5978** |
| `tfidf-svm` | Classical | — | — | — | — | — | **0.5954** |
| `tfidf-logreg` | Classical | — | — | — | — | — | **0.5720** |
| `gemma-3-270m` | Decoder (LoRA) | — | — | — | — | — | **0.5611** |
| `canine-c` | Encoder | — | — | — | — | — | **0.5323** |
| `xlmr-base` | Encoder | 0.5844 | 0.4865 | 0.4889 | 0.4845 | 0.4693 | **0.5012** |
| `labse-probe-cls` | Probe (frozen) | 0.5463 | 0.5377 | 0.4000 | 0.4907 | 0.4028 | **0.4666** |
| `labse-probe-mean` | Probe (frozen) | 0.5075 | 0.5140 | 0.4029 | 0.5049 | 0.3929 | **0.4563** |
| `gemma-3-1b-probe-last` | Probe (frozen) | 0.4500 | 0.4324 | 0.4375 | 0.4552 | 0.4226 | **0.4391** |
| `mmbert-probe-mean` | Probe (frozen) | 0.5673 | 0.4055 | 0.3849 | 0.4014 | 0.3545 | **0.4137** |
| `gemma-3-1b-probe-mean` | Probe (frozen) | 0.5417 | 0.4086 | 0.3864 | 0.4188 | 0.3409 | **0.4122** |
| `labse-lora` | Encoder (LoRA) | 0.3821 | 0.4767 | 0.3944 | 0.4242 | 0.3621 | **—** |
| `xlmr-base-probe-mean` | Probe (frozen) | 0.4800 | 0.4615 | 0.3793 | 0.4075 | 0.3279 | **0.4068** |
| `xlmr-base-probe-cls` | Probe (frozen) | 0.4959 | 0.4148 | 0.3668 | 0.3709 | 0.3058 | **0.3849** |
| `twhin-bert-probe-mean` | Probe (frozen) | 0.4167 | 0.3984 | 0.3612 | 0.3849 | 0.3579 | **0.3828** |
| `mmbert-probe-cls` | Probe (frozen) | 0.4762 | 0.3610 | 0.3553 | 0.3901 | 0.3273 | **0.3779** |
| `twhin-bert-probe-cls` | Probe (frozen) | 0.3860 | 0.3851 | 0.3684 | 0.3631 | 0.3354 | **0.3668** |
| `gemma-3-270m-probe-last` | Probe (frozen) | 0.4094 | 0.3478 | 0.3663 | 0.3193 | 0.3438 | **0.3539** |
| `gemma-3-270m-probe-mean` | Probe (frozen) | 0.4418 | 0.3046 | 0.3529 | 0.2782 | 0.2941 | **0.3250** |
| `canine-c-probe-mean` | Probe (frozen) | 0.3174 | 0.3259 | 0.3312 | 0.2866 | 0.3228 | **0.3164** |
| `canine-c-probe-cls` | Probe (frozen) | 0.2939 | 0.2269 | 0.3274 | 0.2703 | 0.2925 | **0.2807** |


### 3.4 Priority — macro-F1

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `gemma-3-1b-multitask-sharedhead` | Decoder (joint MT) | — | — | — | — | — | **0.9186** |
| `gemma-3-1b` | Decoder (LoRA) | — | — | — | — | — | **0.9170** |
| `labse` | Encoder | — | — | — | — | — | **0.9168** |
| `xlmr-base` | Encoder | — | — | — | — | — | **0.9162** |
| `gemma-3-1b-multitask-shared3head` | Decoder (joint MT) | — | — | — | — | — | **0.9152** |
| `mmbert` | Encoder | — | — | — | — | — | **0.9148** |
| `tfidf-svm` | Classical | 0.8975 | 0.9016 | 0.9089 | 0.9119 | 0.9018 | **—** |
| `gemma-3-270m` | Decoder (LoRA) | — | — | — | — | — | **0.9040** |
| `tfidf-sgd` | Classical | 0.8874 | 0.9015 | 0.9070 | 0.8977 | 0.9074 | **—** |
| `tfidf-logreg` | Classical | 0.8932 | 0.9004 | 0.9015 | 0.8962 | 0.9027 | **—** |
| `twhin-bert` | Encoder | — | — | — | — | — | **0.8907** |
| `canine-c` | Encoder | — | — | — | — | — | **0.8786** |
| `tfidf-cnb` | Classical | 0.8577 | 0.8572 | 0.8636 | 0.8483 | 0.8669 | **—** |
| `labse-probe-cls` | Probe (frozen) | 0.8576 | 0.8678 | 0.7953 | 0.8462 | 0.7695 | **0.8265** |
| `labse-probe-mean` | Probe (frozen) | 0.8468 | 0.8630 | 0.7960 | 0.8489 | 0.7724 | **0.8247** |
| `gemma-3-1b-probe-mean` | Probe (frozen) | 0.8252 | 0.7985 | 0.7935 | 0.7822 | 0.7453 | **0.7887** |
| `gemma-3-1b-probe-last` | Probe (frozen) | 0.8291 | 0.7873 | 0.7850 | 0.7794 | 0.7530 | **0.7864** |
| `mmbert-probe-mean` | Probe (frozen) | 0.8233 | 0.7821 | 0.7441 | 0.7947 | 0.7195 | **0.7719** |
| `mmbert-probe-cls` | Probe (frozen) | 0.8161 | 0.7872 | 0.7381 | 0.7880 | 0.7217 | **0.7694** |
| `twhin-bert-probe-mean` | Probe (frozen) | 0.7891 | 0.7803 | 0.7686 | 0.7589 | 0.7463 | **0.7685** |
| `xlmr-base-probe-mean` | Probe (frozen) | 0.7945 | 0.8020 | 0.7367 | 0.7776 | 0.7141 | **0.7643** |
| `xlmr-base-probe-cls` | Probe (frozen) | 0.8020 | 0.7911 | 0.7254 | 0.7843 | 0.7058 | **0.7609** |
| `twhin-bert-probe-cls` | Probe (frozen) | 0.7732 | 0.7406 | 0.7237 | 0.7038 | 0.7031 | **0.7283** |
| `gemma-3-270m-probe-last` | Probe (frozen) | 0.8013 | 0.7069 | 0.7517 | 0.6687 | 0.7041 | **0.7255** |
| `gemma-3-270m-probe-mean` | Probe (frozen) | 0.7797 | 0.6829 | 0.7493 | 0.6793 | 0.7112 | **0.7190** |
| `canine-c-probe-mean` | Probe (frozen) | 0.6488 | 0.6780 | 0.6646 | 0.6384 | 0.6529 | **0.6565** |
| `canine-c-probe-cls` | Probe (frozen) | 0.6005 | 0.6371 | 0.6276 | 0.6178 | 0.6078 | **0.6181** |


---

## 4. Dev set — the other two training regimes

`multi` (§3) is the shipping regime. These two answer different questions.

### 4.1 Monolingual (`mono`) — one model per language, trained on that language alone

Answers: *does one multilingual model dilute per-language quality?*

**Priority — macro-F1**

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `intent-lookup-oracle` | Classical | 0.9147 | 0.9147 | 0.9147 | 0.9147 | 0.9147 | **—** |
| `tfidf-svm` | Classical | 0.8999 | 0.9079 | 0.9115 | 0.9109 | 0.9036 | **—** |
| `tfidf-logreg` | Classical | 0.8997 | 0.9062 | 0.9068 | 0.8966 | 0.8993 | **—** |
| `intent-chained` | Classical | 0.8931 | 0.9011 | 0.9040 | 0.8921 | 0.8945 | **—** |
| `tfidf-sgd` | Classical | 0.8724 | 0.8891 | 0.8964 | 0.8884 | 0.8912 | **—** |
| `tfidf-cnb` | Classical | 0.8622 | 0.8639 | 0.8667 | 0.8536 | 0.8739 | **—** |
| `sinhalaberto-probe-mean` | Probe (frozen) | — | 0.7856 | — | — | — | **—** |
| `sinbert-large-probe-mean` | Probe (frozen) | — | 0.7685 | — | — | — | **—** |
| `sinhalaberto-probe-cls` | Probe (frozen) | — | 0.7657 | — | — | — | **—** |
| `sinbert-large-probe-cls` | Probe (frozen) | — | 0.7531 | — | — | — | **—** |
| `majority` | Classical | 0.2302 | 0.2302 | 0.2302 | 0.2302 | 0.2302 | **—** |


**Sentiment — Negative-F1 · v8 labels**

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `tfidf-svm` | Classical | 0.6592 | 0.6301 | 0.6389 | 0.6971 | 0.6265 | **—** |
| `tfidf-logreg` | Classical | 0.6473 | 0.6075 | 0.6146 | 0.6492 | 0.6176 | **—** |
| `tfidf-sgd` | Classical | 0.5333 | 0.5638 | 0.5732 | 0.6065 | 0.5478 | **—** |
| `tfidf-cnb` | Classical | 0.4746 | 0.4891 | 0.4926 | 0.5000 | 0.5198 | **—** |


**Sentiment — Negative-F1 · ⚠️ v5 labels (superseded)**

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `labse` | Encoder | 0.6667 | 0.6963 | 0.6303 | 0.6803 | 0.5526 | **—** |
| `twhin-bert` | Encoder | 0.6438 | 0.5630 | 0.5373 | 0.5811 | 0.5000 | **—** |
| `xlmr-base` | Encoder | 0.5752 | 0.5333 | 0.3626 | 0.5436 | 0.3364 | **—** |
| `sinhalaberto-probe-mean` | Probe (frozen) | — | 0.4646 | — | — | — | **—** |
| `sinhalaberto-probe-cls` | Probe (frozen) | — | 0.4227 | — | — | — | **—** |
| `sinbert-large-probe-mean` | Probe (frozen) | — | 0.4145 | — | — | — | **—** |
| `sinbert-large-probe-cls` | Probe (frozen) | — | 0.3612 | — | — | — | **—** |
| `labse-lora` | Encoder (LoRA) | 0.3226 | 0.3223 | 0.2629 | 0.3219 | 0.2739 | **—** |
| `majority` | Classical | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | **—** |


> Compare `labse` mono (english 0.6667 / sinhala 0.6963 / tamil 0.6803) against `labse` multi in
> §3.3 (0.6569 / 0.6713 / 0.6324): monolingual buys a small native-script edge but **loses on
> Singlish** (0.6303 vs 0.6475) — romanized text leans on cross-lingual transfer. All deltas sit
> inside the CI. Conclusion on record: **do not ship per-language models.**

### 4.2 Zero-shot from English (`zeroshot-en`) — trained on English only, never sees the target language

Answers: *what would a sixth, unseen language get?* Classical only — no encoder was run zero-shot.

**Priority — macro-F1**

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `tfidf-logreg` | Classical | — | 0.7141 | 0.7296 | 0.2919 | 0.7302 | **—** |
| `tfidf-svm` | Classical | — | 0.6966 | 0.7090 | 0.2913 | 0.6985 | **—** |
| `tfidf-cnb` | Classical | — | 0.6958 | 0.7579 | 0.1743 | 0.7224 | **—** |
| `tfidf-sgd` | Classical | — | 0.6110 | 0.5441 | 0.2659 | 0.5196 | **—** |


**Sentiment — Negative-F1 · v8 labels**

| model | family | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---|---:|---:|---:|---:|---:|---:|
| `tfidf-cnb` | Classical | — | 0.2494 | 0.2759 | 0.1131 | 0.3125 | **—** |
| `tfidf-logreg` | Classical | — | 0.1455 | 0.1224 | 0.0000 | 0.1600 | **—** |
| `tfidf-svm` | Classical | — | 0.1400 | 0.1212 | 0.0449 | 0.1053 | **—** |
| `tfidf-sgd` | Classical | — | 0.0000 | 0.0000 | 0.0000 | 0.0000 | **—** |


> **Zero-shot sentiment collapses** (0.00–0.31) and **Tamil collapses hardest on both tasks**
> (priority 0.17–0.29 against 0.61–0.76 for the other three). TF-IDF transfers nothing across
> scripts — expected, since a word/char n-gram model shares almost no features between Latin and
> Tamil script. The romanized tracks (singlish/tamilish) transfer far better than native script,
> which is the same Latin-alphabet overlap effect, not genuine language transfer.

### 4.3 Frozen linear probes — how much is in the backbone before any fine-tuning

Backbone frozen, one forward pass, logistic regression on the pooled vector. Full per-language rows
appear in §3.1/§3.3/§3.4 (rows tagged `Probe (frozen)`). Retention (probe ÷ fine-tune, pooled dev):

| task | best probe (pooled dev) | best fine-tune (pooled dev) | retained |
|---|---:|---:|---:|
| intent | `labse-probe-mean` 0.8614 | `gemma-3-1b-multitask-sharedhead` 0.9284 | **0.928** |
| priority | `labse-probe-cls` 0.8265 | `gemma-3-1b-multitask-sharedhead` 0.9186 | **0.900** |
| sentiment (v5) | `labse-probe-cls` 0.4666 | `mmbert` 0.6203 | **0.752** |

**Retention is ordered intent > priority > sentiment for all seven backbones, no exceptions.**
Fine-tuning does the most work on exactly the task whose labels agree with humans least.

> ⚠️ **No probe was ever run on v8 sentiment labels** — all 282 probe records predate the relabel,
> so the sentiment retention figure above is a v5 measurement and the whole probe analysis is
> pinned to superseded labels for that one task. Intent and priority probes are unaffected. Listed
> in §8.2.

---

## 5. Intent on the **official BANKING77 split** — a separate universe

⚠️ **These numbers are on a different split from every table above** (9,998 train / 3,079 test per
track, no dev; `ml/scripts/train_transformer.py`, run on Colab). They carry no split-sha and no
`runs/*.json` record, so they cannot be compared cell-to-cell with §1–§4. They are here because
they are the only intent transformer numbers on a held-out set, and the classical row is the
like-for-like baseline they were gated against.

### 5.1 Four-architecture ablation — macro-F1 %

| model | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---:|---:|---:|---:|---:|---:|
| `LaBSE` (501k vocab) | **94.13** | **92.95** | **90.65** | **93.27** | 70.57 | **88.54** |
| `XLM-R base` (250k) | 93.88 | 92.42 | 90.03 | 91.74 | **72.04** | 88.29 |
| `IndicBERT` (200k) | — | — | — | 89.81 | 61.25 | 76.24 |
| `MuRIL` (36k) | — | — | — | 66.01 | 57.62 | 62.10 |
| `Linear SVM` (classical) | 90.98 | 82.75 | 86.49 | 86.35 | 61.05 | 83.18 |
| `Logistic Regression` (classical) | 90.48 | 83.08 | 86.07 | 84.22 | 59.05 | 82.16 |

> **LaBSE vs XLM-R is a tie on every track.** Gaps are 0.25–1.53pp; per-track bootstrap 95% CI
> *widths* are 2.07–2.97pp and no CIs or repeat seeds were run for these. What separates cleanly is
> transformer vs classical (+3.15 to +10.99pp) and multilingual vs Indic-specialist (+12 to +26pp
> pooled).
>
> **Both Indic specialists fail below the classical baseline pooled** (MuRIL 62.10, IndicBERT 76.24
> vs classical 83.18) — a specialist vocabulary is not a substitute for multilingual coverage when
> the input mixes five tracks.
>
> `Swift-Support/labse-intent-1.0` on HF publishes the 88.54 figure. It is **not** on the frozen
> split, so it cannot be tabled next to §1.1's 0.8673.

### 5.2 Classical intent — mono vs pooled training (official split, macro-F1 %)

| model | english | sinhala | singlish | tamil | tamilish | **pooled** |
|---|---:|---:|---:|---:|---:|---:|
| `Linear SVM` mono | 90.98 | 82.75 | 86.49 | 86.35 | 61.05 | **83.18** |
| `Logistic Regression` mono | 90.48 | 83.08 | 86.07 | 84.22 | 59.05 | **82.16** |

---

## 6. Label ceilings — what the labels themselves are worth

How well the prompt-generated labels agree with a human annotator on the 500-ticket hand-annotated
gold set. **This is a label-quality read, not a bound on achievable model score.**

| task | prompt | vs human | 95% CI | agreement | Cohen's κ | status |
|---|---|---:|---|---:|---:|---|
| intent (`category`) | — | 1.0000 | [1.00, 1.00] | 100.0% | 1.000 | inherited from BANKING77 — **real ground truth** |
| priority | v5 | 0.7722 | [0.7263, 0.8147] | 80.4% | 0.644 | **current** — untouched by v8 |
| sentiment | **v8** | **0.7812** | [0.6545, 0.8824] | 97.2% | 0.766 | **current** — what the datasets ship |
| sentiment | v5 | 0.5769 | [0.4000, 0.7273] | 95.6% | 0.555 | superseded 2026-08-19 |

Read against §1:

- **Priority (test 0.8904) sits ~0.12 ABOVE its ceiling (0.7722).** The model has learned the v5
  labelling rule better than the rule agrees with a human. There is no headroom for a bigger model —
  any further gain is fitting the rule harder, not classifying better.
- **Sentiment (test 0.7138) sits just BELOW its ceiling (0.7812).** Post-v8 this is a coherent place
  to be, and unlike priority there is still real headroom.
- Quoting 0.89 as "priority accuracy" overstates what a human reviewer would call correct.

---

## 7. Shipped artifacts — what actually exists as weights

Scores are worthless without a checkpoint behind them. `swiftbench` scored and discarded by default,
so most rows above have **no saved model**.

| task | artifact | test score | where |
|---|---|---:|---|
| intent | `tfidf_linear_svm_all.joblib` | 83.18% (official split) | `ml/models/` — in git |
| intent | LaBSE fine-tune | 88.54% (official split) | [`Swift-Support/labse-intent-1.0`](https://huggingface.co/Swift-Support/labse-intent-1.0) — public |
| priority | LaBSE fine-tune | **0.8901** | [`Swift-Support/labse-priority-1.0`](https://huggingface.co/Swift-Support/labse-priority-1.0) — public · local `ml/models/encoders/priority_labse/` (gitignored) |
| sentiment | LaBSE fine-tune (v8) | **0.7138** | re-trained 2026-09-05, upload pending |
| — | dataset (5 tracks, v8 labels, frozen split) | — | [`Swift-Support/swift-support-tickets-1.0`](https://huggingface.co/datasets/Swift-Support/swift-support-tickets-1.0) — public |

**No saved checkpoint exists for:** every classical sentiment/priority model (`swiftbench` never
dumped estimators — serving one needs a refit), every Gemma single-task and joint multi-task
adapter, and every non-champion encoder (`mmbert`, `xlmr-base`, `canine-c`, `twhin-bert`,
`sinbert-large`, `sinhalaberto`).

---

## 8. Gaps — what has not been run

Explicit blanks, so the table above is read as incomplete rather than negative.

### 8.1 Per-language test scores (the largest gap)

Only 5 model-rows in the whole project have per-language **test** numbers (§2). Everything else was
scored pooled only. Missing per-language test for: every encoder except `labse`/`xlmr-base` on
priority, every decoder and joint multi-task variant on all three tasks, and every sentiment model
except `labse` on v8 labels.

### 8.2 v8 sentiment re-runs never done

The relabel landed 2026-08-19; only 6 models were re-scored against it. Still on v5 labels and
therefore unrankable against the current champion:

| what | models | status |
|---|---|---|
| encoder test runs | `xlmr-base`, `mmbert`, `canine-c`, `sinbert-large`, `sinhalaberto`, `twhin-bert` | ⬜ not re-run |
| all frozen probes | 7 backbones × 2 poolings, dev **and** test | ⬜ not re-run (282 records, all v5) |
| per-language dev | `labse`, `twhin-bert`, `xlmr-base`, `labse-lora` | ⬜ not re-run |
| per-language test | `tfidf-svm`, `tfidf-logreg` | ⬜ not re-run |
| per-language test, `labse` | — | ✅ done 2026-09-05 (§2.2) |
| label ceiling recompute | — | ✅ done 2026-09-05 (0.7812) |

### 8.3 Never measured at all

| gap | detail |
|---|---|
| **Intent on the frozen split, per language** | only pooled exists (§1.1); no per-language frozen-split intent number for any model |
| **LaBSE intent on the frozen split** | `Swift-Support/labse-intent-1.0`'s 88.54% is official-split only; the frozen-split run was attempted 2026-08-20 and **died on CPU** (`cuda False`, killed at the 12 h cap) |
| **Zero-shot for any neural model** | §4.2 is classical-only; no encoder or decoder was run `zeroshot-en` |
| **Mono regime for decoders** | no Gemma or joint multi-task run in the `mono` regime |
| **Confidence intervals on §5** | official-split intent runs are single-seed with no CIs — LaBSE vs XLM-R cannot be separated |
| **CIs for most frozen-split runs** | only the classical sentiment/priority test runs carry bootstrap CIs (`final_test_results.csv`); no encoder or decoder test run has one |
| **Repeat seeds** | every number in this file is a **single seed**. No variance estimate exists for any model |
| **Human-typed romanized text** | Singlish is rule-generated, Tanglish machine-translated — every romanized cell is an optimistic upper bound and no romanized-specific conclusion is safe |
| **Calibration** | no model here is calibrated; threshold tuning was measured and **failed to transfer** (−0.005 on the champion) |

### 8.4 Known data defects

| defect | scale | status |
|---|---|---|
| Ticket `id` 5160 has a different `category` in the `tamilish` track than the other four | 1 of 9,998 | ⬜ open, pre-existing in git |
| Train/test text overlap: english 6 (0.19%), sinhala 71 (2.31%), singlish 84 (2.73%), tamil 70 (2.31%), tamilish 7 (0.23%) | ≤3.2% of unique test texts | ⬜ documented, id-level splits are clean |

---

## 9. Provenance

- **735 run records**, all stamped split sha `e7b5934392cd`, in `ml/reports/runs/*.json`
- Per-language test: `ml/reports/per_language_priority_labse_test.csv` (generated 2026-09-05),
  `per_language_xlmr-base.csv`, `final_test_results.csv`
- Official-split intent: `RESULTS.md` §16, `baseline_summary.csv`
- Label ceilings: `label_ceiling.csv`, `prompt_v8_all_scores.csv`, `prompt_v6_holdout_scores.csv`
- All six Kaggle kernels (`swift-job-{train-encoders,train-encoders-b,multitask,multitask-b,perlang,perlang-lora}`)
  were checked on 2026-09-05: **every run JSON they hold is already in `ml/reports/runs/`.** Nothing
  is stranded on Kaggle.

---

## 10. v8 classical re-run — one split, one label set, with intervals

**Added 2026-09-08.** Generated by `ml/scripts/run_v8_classical.py` (336 records) and
`paper/experiments/build_results_tables.py`. This section exists because §8.1 and §8.2 listed
per-language test coverage and the v8 re-score as the project's two largest gaps. For the
classical family both are now closed, and every cell carries a 1,000-resample bootstrap CI.

Validation against previously recorded numbers, to show the harness use is identical:
`tfidf-svm` intent test **0.8308** (recorded 0.8307) · sentiment **0.6653** (recorded 0.6663) ·
priority **0.8734** (recorded 0.8722).

Every record written here stamps `label_version`, which no earlier record carried — the absence
of that field is precisely why v5 and v8 numbers were tabled together for three weeks.

### 10.1 Pooled test, best arm per model — with 95% bootstrap CIs

| task | model | arm | headline | 95% CI |
|---|---|---|---:|---|
| intent | `tfidf-svm` | none | **0.8308** | [0.8249, 0.8359] |
| intent | `tfidf-logreg` | none | 0.8189 | [0.8126, 0.8240] |
| intent | `tfidf-sgd` | none | 0.8115 | [0.8053, 0.8167] |
| intent | `tfidf-cnb` | none | 0.6792 | [0.6710, 0.6859] |
| sentiment | `tfidf-svm` | class_weight | **0.6653** | [0.6411, 0.6889] |
| sentiment | `tfidf-logreg` | ros | 0.6383 | [0.6144, 0.6630] |
| sentiment | `tfidf-sgd` | ros | 0.6092 | [0.5817, 0.6377] |
| sentiment | `tfidf-cnb` | ros | 0.4968 | [0.4735, 0.5202] |
| priority | `tfidf-svm` | class_weight | **0.8734** | [0.8669, 0.8797] |
| priority | `tfidf-logreg` | ros | 0.8706 | [0.8638, 0.8771] |
| priority | `tfidf-sgd` | ros | 0.8659 | [0.8594, 0.8721] |
| priority | `tfidf-cnb` | class_weight | 0.8422 | [0.8352, 0.8481] |

### 10.2 Per-language test — the gap §8.3 called "never measured at all"

| task | model | english | sinhala | singlish | tamil | tamilish | pooled |
|---|---|---:|---:|---:|---:|---:|---:|
| intent | `tfidf-svm` | 0.9180 | 0.8666 | 0.8793 | 0.8528 | **0.6127** | 0.8308 |
| intent | `tfidf-logreg` | 0.9096 | 0.8595 | 0.8751 | 0.8302 | **0.5854** | 0.8189 |
| sentiment | `tfidf-svm` | 0.7198 | 0.6412 | 0.6633 | 0.7249 | **0.5722** | 0.6653 |
| sentiment | `tfidf-logreg` | 0.6995 | 0.6256 | 0.6545 | 0.6776 | **0.5074** | 0.6383 |
| priority | `tfidf-svm` | 0.9050 | 0.8848 | 0.8918 | 0.8854 | **0.7984** | 0.8734 |
| priority | `tfidf-logreg` | 0.8987 | 0.8810 | 0.8889 | 0.8849 | **0.7985** | 0.8706 |

Tanglish is the weak track on all three tasks, confirmed on test with per-language numbers for
the first time. Error rate against English: intent **+28.9pp**, priority **+7.1pp**,
sentiment **+1.6pp**.

### 10.3 Significance — the first p-values in this project

`paper/experiments/significance.py`, 1,000-resample paired bootstrap plus exact McNemar.
Two results change how the table above should be read:

- **`tfidf-logreg` and `tfidf-svm` are indistinguishable on priority** — delta −0.0027,
  CI [−0.0069, +0.0014], p = 0.222. The 0.8734 / 0.8706 ordering is not a result.
- **On sentiment, `tfidf-sgd` vs `tfidf-svm` gives p(McNemar) = 0.866 but p(bootstrap) = 0.0000.**
  The two models agree on almost every row's correctness while differing by 0.056 Negative-F1.
  An accuracy-based significance test would have called this a tie. Report the metric's own test.

### 10.4 Train/test text overlap does not carry any result

`paper/experiments/dedup_ablation.py`. Normalised test text recurring in train+dev:
english 0.23% · sinhala 2.92% · singlish 3.41% · tamil 3.02% · tanglish 0.32% (stricter than
§8.4's figures — case- and whitespace-normalised, and against train+dev rather than train).

Removing all 305 affected rows moves the headline by at most **−0.0047** (intent `tfidf-cnb`);
the champion shifts −0.0029 on intent, −0.0013 on priority, **+0.0007** on sentiment. Every
delta is far inside its bootstrap CI. §8.4 can be downgraded from a defect to a footnote.

### 10.5 Re-runs in flight

Launched 2026-09-08 on Kaggle T4, payload sha `bc73eb006cfc` (v8 verified: 195 English test
Negatives). Encoders 6 epochs, decoders 8 — up from the previous roster's 3, which several
models were still improving at.

| job | models | task | portion | state |
|---|---|---|---|---|
| K1 | labse, xlmr-base, mmbert, muril-base, indicbert, twhin-bert | sentiment | dev | running |
| K2 | same six | intent | dev | running |
| K3 | same six | priority | dev | queued |
| K6 | champion + rival | all three | test | after K1–K3 |
| K7 | gemma-3-1b, gemma-3-270m (LoRA-all, lr 1e-4) | all three | dev+test | queued |
| K8 | champion + rival, seeds 43–46 | all three | test | after K6 |

Dev runs first because the epoch budget is now a hyperparameter, and dev is the only place it
can legitimately be chosen (§0d). `muril-base` and `indicbert` are in the harness for the first
time — their published 62.10% / 76.24% figures come from a different script on the official
split and have no `runs/*.json` record, so the Indic-specialist claim has never been measurable
against anything else in this file.

### 10.6 What is still open

Encoders and decoders have **no per-language test coverage and no CIs**. `train_encoder.py` now
emits per-language records and per-row predictions, so the next Kaggle batch closes it — but
until that batch runs, §10.1's encoder and decoder rows do not exist and the family comparison
in §1 remains single-seed, pooled-only, and without intervals.

---

## 11. Label ceiling, recomputed — the number to quote is 0.7931, not 0.7812

**Added 2026-09-08.** Generated by `paper/experiments/label_ceiling.py`.

### 11.1 The join was never verified, and neither id column is a key

The gold benchmark's `id` column matches **1,000** dataset rows (train and test id
ranges overlap) and its `row_id` matches only **76%** of texts. Neither is a join key. The
ceiling is now computed on a normalised-text join, verified by the intent column — which
neither side ever edited, so a correct join must give exactly 1.0 agreement there. It does.

### 11.2 The published ceiling measured the prompt, not the shipped labels

| compared | Negative-F1 | 95% CI | agreement | κ |
|---|---:|---|---:|---:|
| **shipped labels vs human gold** | **0.7931** | [0.6667, 0.8956] | 0.976 | 0.7804 |
| prompt v8 raw output vs human gold | 0.7812 | [0.6557, 0.8842] | 0.972 | 0.7663 |
| priority, shipped vs human gold | 0.7722 | [0.7258, 0.8150] | 0.804 | 0.6446 |

The recorded 0.7812 scored `prompt_v8_all_labels.csv`'s `sentiment_pred` — the prompt's raw
output. **The shipped CSVs differ from that output on 8 of the 500 gold rows**, in both
directions: the rollout dropped two Negatives the prompt and the human both agreed on, and
added one neither did. Models train on the shipped labels, so 0.7931 is the ceiling their
scores should be read against.

Provenance is otherwise clean and reproduces the documented figures exactly: shipped labels
differ from v5 on **711 of 13,077** rows, and from `relabel_v8_staging.csv`'s applied column
on **0**. Priority is untouched, 0 rows changed. The 8-row gap is between the prompt output
and the applied labels, not between the staging file and the CSVs.

### 11.3 What this does to the headline claim

Sentiment headroom is slightly **larger** than the project believed, not smaller:

| | score | ceiling | gap |
|---|---:|---:|---:|
| classical champion `tfidf-svm` (clean) | 0.6653 | 0.7931 | 0.1278 |
| `labse` (⚠️ epoch-selected on test, §0d) | 0.7138 | 0.7931 | 0.0793 |

The ceiling's own CI is **[0.6667, 0.8956]** — wide, because the gold set holds only 31
Negatives. The "labels bind, not model capacity" claim rests on a ceiling estimated from 31
rows by one annotator. That is the strongest argument for finishing the inter-annotator batch
before the claim goes in a paper.

---

## 12. Is the per-language deficit significant? Yes — and testing it wrong flips three cells

**Added 2026-09-08.** Generated by `paper/experiments/language_gap.py`.

The Tanglish deficit is the project's largest per-language claim and had never been tested.
The comparison is **paired**, which makes it far sharper than it looks: the same 3,079 ticket
ids appear in all five tracks, so English and Tanglish predictions are two labellings of the
same tickets.

### 12.1 Tanglish, against English on the same tickets

`tfidf-svm`, paired bootstrap on the headline metric, 1,000 resamples:

| task | Δ headline | 95% CI | p |
|---|---:|---|---:|
| intent | **−0.3053** | [−0.3234, −0.2907] | 0.000 |
| priority | **−0.1067** | [−0.1260, −0.0904] | 0.000 |
| sentiment | **−0.1476** | [−0.2136, −0.0855] | 0.000 |

Tanglish is significantly worse than English on **all 12** model × task combinations, with
every confidence interval clear of zero. The claim holds, and now has a number behind it.

Across all 48 track-vs-English comparisons, **35 are significant** on the headline metric.

### 12.2 The trap: McNemar tests accuracy, not the metric being reported

Three of the 48 comparisons flip depending on which test is used, all on sentiment:

| model | track | Δ Negative-F1 | p (headline) | p (McNemar) |
|---|---|---:|---:|---:|
| `tfidf-cnb` | sinhala | −0.0056 | **0.840** | 0.003 |
| `tfidf-cnb` | singlish | +0.0163 | **0.364** | 0.001 |
| `tfidf-cnb` | tamil | +0.0100 | 0.498 | 0.108 |

On the first two, McNemar reports a highly significant difference while the reported metric
shows nothing. The mechanism is the one already visible pooled (§10.3): these tracks make
*fewer errors overall* than English while scoring the same or worse on the Negative class.
McNemar sees the accuracy difference, which is real — and irrelevant, because the paper
reports Negative-F1.

**A per-language significance table built on McNemar would assert two cross-lingual sentiment
effects that do not exist in the metric being reported.** Both tests are kept in
`language_gap.csv` with a `tests_agree` column, because where they disagree the disagreement
is itself the finding.

---

## 13. Half the Negative signal is reachable without reading the ticket

**Added 2026-09-08.** Generated by `paper/experiments/negative_is_topic.py`.

`RESULTS.md` records that "Negative looks like a topic construct, not polarity" — an
observation about a mined word list, never tested. It is now a number, and the test needs
no text at all.

### 13.1 The test

Fit a predictor that sees **only BANKING77's 77-way gold intent label**. Intent carries no
tone information whatsoever: two tickets with the same intent can be furious or perfectly
calm. Per-intent Negative rate learned on train+dev, threshold swept on train+dev (never on
test), applied once to test.

| system | Negative-F1 | precision | recall |
|---|---:|---:|---:|
| **intent label only, no text** | **0.3301** | 0.2656 | 0.4359 |
| `tfidf-svm` on text | 0.6653 | — | — |

**Half of the champion's Negative-F1 — 49.6% of it — is reachable from the topic label alone,
without reading a single word of the ticket.**

### 13.2 The mechanism, visible in the per-intent rates

| intent | Negative rate |
|---|---:|
| `terminate_account` | 0.444 |
| `declined_transfer` | 0.256 |
| `failed_transfer` | 0.255 |
| `declined_card_payment` | 0.229 |
| `Refund_not_showing_up` | 0.198 |

These are failure and loss topics, not emotional registers. Negatives are concentrated
accordingly: **the top 10 of 77 intents hold 48.8% of all Negatives**, and 30 intents cover 90%.

### 13.3 What it means for the paper

The claim should be stated as measured, not as folklore: the label is **partly** a topic
construct — about half — and partly genuine tone the text model reads. That is a more
defensible and more interesting statement than either extreme.

It also reframes the label-ceiling result (§11). A sentiment label half-predictable from
topic is one an annotator can disagree with for structural reasons, which is consistent with
the wide ceiling CI [0.6667, 0.8956] and with the guideline's need to define Negative as tone
explicitly — the trap written into `paper/annotation/guidelines/annotation_guideline_v1.md`
before any annotator sees a row.

---

## 14. Encoder roster on v8, frozen split, 6 epochs — dev

**Added 2026-09-08.** Kaggle T4, payload sha `bc73eb006cfc`, fit on `train`, scored on dev,
best epoch selected on dev (§0d). Six encoders, three of which (`muril-base`, `indicbert`,
`twhin-bert`) enter the harness here for the first time.

### 14.1 Pooled dev

| model | sentiment Neg-F1 | best ep | intent macro-F1 | best ep |
|---|---:|---|---:|---|
| `labse` | **0.7579** | 3/6 | 0.9293 | 5/6 |
| `mmbert` | 0.6991 | 6/6 | **0.9294** | 6/6 |
| `indicbert` | 0.6940 | 4/6 | 0.9104 | 6/6 |
| `xlmr-base` | 0.6869 | 6/6 | 0.9219 | 5/6 |
| `muril-base` | 0.6547 | 6/6 | 0.8703 | 6/6 |
| `twhin-bert` | 0.6461 | 5/6 | 0.9082 | 6/6 |

### 14.2 The 3-epoch budget was not neutral

LaBSE peaks at epoch 3. **XLM-R, mmBERT, MuRIL, IndicBERT and TwHIN-BERT were all still
improving at the budget edge** — five of six select epoch 5 or 6. The previous roster's
3-epoch budget therefore under-trained most of the field at a setting that happened to suit
the eventual winner. LaBSE still wins sentiment at 6 epochs, so the conclusion survives; the
margin it was won by did not.

Intent is still budget-bound at 6 (four of six select epoch 6), so intent numbers here remain
a lower bound.

### 14.3 Significance — one champion, and one tie

Paired bootstrap, 1,000 resamples, on dev predictions:

| task | pair | Δ | 95% CI | p |
|---|---|---:|---|---:|
| intent | `labse` vs `mmbert` | **−0.0001** | [−0.0045, +0.0046] | **0.944** |
| intent | `labse` vs `xlmr-base` | +0.0074 | [+0.0026, +0.0120] | 0.004 |
| sentiment | `labse` vs `mmbert` | +0.0587 | [+0.0292, +0.0911] | 0.000 |
| sentiment | `mmbert` vs `xlmr-base` | +0.0122 | [−0.0185, +0.0429] | 0.442 |

**On intent, LaBSE and mmBERT are indistinguishable** — the difference is one ten-thousandth
of a point. Both are significantly ahead of everything else. **On sentiment LaBSE wins
outright**, significantly ahead of all five rivals.

The defensible claim is therefore *"LaBSE is the sentiment champion and ties mmBERT on
intent"*, not *"LaBSE is the champion"*.

### 14.4 MuRIL's Sinhala collapse, and what causes it

Per-language dev — the coverage gap §8.1 called the project's largest, closed for encoders:

| model | english | sinhala | singlish | tamil | tamilish |
|---|---:|---:|---:|---:|---:|
| `labse` (sentiment) | 0.8092 | 0.7811 | 0.7134 | 0.7929 | 0.6835 |
| `muril-base` (sentiment) | 0.7407 | **0.5070** | 0.6351 | 0.7200 | 0.6452 |
| `muril-base` (intent) | 0.9003 | **0.7633** | 0.8879 | 0.9009 | 0.9023 |

MuRIL loses **23.4 points** on Sinhala sentiment and **13.7** on Sinhala intent, against its
own English — on both tasks, and on no other language. Joined to the tokenizer screen, the
mechanism is unambiguous: **MuRIL maps 64.5% of Sinhala characters to `[UNK]`.** Every other
model in the roster is at 0.0%.

This closes a loop the project had left open. §7.3 concluded "fertility does not predict
encoder quality" — correct, and now sharpened, because the two tokenizer diagnostics behave
completely differently:

| diagnostic | Spearman ρ with per-language deficit |
|---|---:|
| fertility (tokens/word) | **−0.035** |
| `[UNK]` rate | **−0.521** |

Fertility is a *cost*: mmBERT pays 3.67 tokens per Sinhala word and loses only 3.7 points.
`[UNK]` is *destruction*: the characters are gone before the first layer and fine-tuning
cannot recover them. Conflating the two is what produced the earlier null result.

> **Caveat, and it is a real one.** Only **1 of 20** model × non-English cells has a high
> `[UNK]` rate, and 18 are tied at exactly 0.0%. The ρ of −0.521 is carried by that single
> cell, so this is a strong *case study* — the worst cell in the table by 9.9 points, with a
> mechanism that predicts it — and not a fitted relationship. Establishing the relationship
> would need more high-`[UNK]` tokenizers in the roster.


---

## 15. The first unbiased fine-tuned test number — and an exact reproduction

**Job K6a**, 2026-09-08: `labse`, sentiment, **test**, fitted on `train+dev` (49,990 rows),
scored once on the 15,395-row pooled test set. 3 epochs — the budget dev selected in §14.
Run under the patched `train_encoder.run()`, so the reported epoch is the **final** one, not
the best one on the test set. Record stamps `epoch_selection: final-epoch`.

### The result

| | Negative-F1 | precision | recall | macro-F1 | accuracy |
|---|---:|---:|---:|---:|---:|
| labse, sentiment, test | **0.7138** | 0.7601 | 0.6728 | 0.8478 | 0.9658 |

### It is bit-identical to the record it was meant to replace

The pre-patch record for this cell reads `headline = 0.7138193688792165`.
The re-run reads `headline = 0.7138193688792165`. Seventeen significant figures, exact.

Two separate things follow, and they should not be conflated.

**(a) The epoch-selection bias on this cell is exactly zero.** Per-epoch, the headline was
0.6749 → 0.7115 → **0.7138**: monotonically increasing across the whole budget. The best
epoch *was* the final epoch, so selecting on test had nothing to select — the maximum over
three draws and the last of three draws are the same draw. The defect was real in mechanism
and inert in this instance.

**Generalising it needed a count, not an assumption**, and the count is in §0(d): of the 17
unstamped test records, **15 have `best_epoch == epochs`** and are inert for exactly the same
reason, leaving **2 genuinely biased** — `sinbert-large` (best 2 of 3) and `sinhalaberto`
(best 1 of 3), both sentiment, both minor models. The earlier claim that every fine-tuned test
number was affected was wrong: it counted records that *ran* the defective code rather than
records where the defect could change the answer.

The caveat that does survive: inertness is a property of the run, not the code. §14 shows
`labse` peaking at epoch 3 of 6 on dev, so at a 6-epoch budget this same cell would *not* have
been inert.

**(b) Training is deterministic to the bit.** Same seed, same config, different Kaggle
session, nineteen days apart (2026-08-20 and 2026-09-08) — and 17 matching significant
figures. The two runs are not the same execution: wall-clock training differs (1325.7s vs
1319.0s), so the hardware and scheduling differed while the arithmetic did not.
That is a stronger reproducibility statement than the paper currently makes, and it is free:
it means the seed-variance study (K8) will measure *seed* effect and nothing else, with no
run-to-run noise floor underneath it.

### What this unblocks

The headline comparison can now be quoted. It could not be before, because it set a biased
encoder number against a clean classical one.

| system | Negative-F1 (test) | epoch selection |
|---|---:|---|
| **labse** (encoder, fine-tuned) | **0.7138** | final-epoch — clean |
| tfidf-svm (classical champion, v8) | 0.6653 | n/a — no epoch loop |
| intent label only, no text (§13) | 0.3301 | n/a |
| **label ceiling** (§11, shipped labels vs human gold) | **0.7931** | n/a |

The encoder is **+0.0485** over the classical champion, and reaches **90.0% of the label
ceiling**. Both halves of that sentence are now measured on the same split, the same labels
and the same discipline.

**The gap is significant.** Paired bootstrap over 1,000 resamples of the 15,395 test rows:
Δ = **+0.0485, 95% CI [+0.0257, +0.0721], p < 0.0001**; exact McNemar p = 1.4e-07. LaBSE also
beats every other classical system by a wider and equally significant margin (vs `tfidf-logreg`
+0.0755, vs `tfidf-sgd` +0.1046, vs `tfidf-cnb` +0.2171).

Per language, from the same fit:

| track | Negative-F1 |
|---|---:|
| english | 0.8032 |
| tamil | 0.7606 |
| sinhala | 0.7234 |
| singlish | 0.6757 |
| tamilish | **0.5948** |

A 20.8-point spread, with Tanglish last — the same ordering §12 found on the classical systems,
now reproduced by the champion encoder.

### Checkpoint

`--save-models` wrote `models/sentiment_labse/` — the project's first saved champion
checkpoint fitted on `train+dev` under v8 labels, replacing the stale v5-label weights.
Closes the serving half of task A7 for sentiment; intent and priority still have none.

---

## 16. The encoder's advantage is not spread evenly across scripts

§15 established the pooled gap: `labse` beats `tfidf-svm` by +0.0485 Negative-F1 on the test
set. A pooled number says nothing about where a gain lives, and this one is concentrated.

Paired within each track — same tickets, both systems, 3,079 rows and 195 Negatives per cell:

| track | script | tfidf-svm | labse | encoder gain | 95% CI | p |
|---|---|---:|---:|---:|---|---:|
| english | native | 0.7198 | 0.8032 | **+0.0834** | [+0.0383, +0.1327] | <0.001 |
| sinhala | native | 0.6412 | 0.7234 | **+0.0822** | [+0.0315, +0.1353] | 0.004 |
| tamil | native | 0.7249 | 0.7606 | +0.0357 | [−0.0098, +0.0839] | 0.144 |
| singlish | romanized | 0.6633 | 0.6757 | +0.0124 | [−0.0455, +0.0655] | 0.712 |
| tamilish | romanized | 0.5722 | 0.5948 | +0.0225 | [−0.0440, +0.0825] | 0.490 |

**On both romanized tracks the encoder's advantage is indistinguishable from zero.** Every
point of the pooled +0.0485 is earned on native script. The mechanism is not mysterious:
LaBSE's pretraining contains Sinhala and Tamil in their own scripts and contains essentially
no Sinhala or Tamil written in Latin characters, which is exactly what the romanized tracks
are.

### Tested as a contrast, not by comparing two p-values

"Significant on sinhala, not significant on singlish" is not evidence that the two gains
differ — the difference between significant and non-significant is not itself significant.
The contrast has to be tested directly, which the frozen split makes clean: `sinhala` and
`singlish` are **the same tickets in the same language**, differing only in script, so a
difference of differences cannot be a language, topic or sampling effect.

| pair | difference of differences | 95% CI | p | |
|---|---:|---|---:|---|
| sinhala − singlish | **+0.0698** | [+0.0140, +0.1283] | **0.012** | significant |
| tamil − tamilish | +0.0132 | [−0.0664, +0.0882] | 0.762 | not significant |

**The claim holds for Sinhala and is not established for Tamil.** Romanizing the same Sinhala
tickets removes about 7 points of the encoder's advantage. The Tamil pair points the same way
and the test does not support it.

### The two pairs are not measuring the same thing

§corpus stats put the *native* tracks' own Latin-character content at **40.35% for sinhala**
against **1.26% for tamil**. So the two contrasts have different baselines: sinhala/singlish
is "heavily code-mixed native script vs fully romanized", while tamil/tamilish is "nearly pure
Tamil script vs fully romanized". Whether that asymmetry is a property of the two languages or
an artifact of how the tracks were produced is open — and it is the same open question as the
"manually verified" claim (Tamil is documented as having had no hand pass). **The two pairs
must not be presented as two measurements of one effect until that is settled.**

### Why this matters for the paper

It reframes the contribution. "A multilingual encoder beats TF-IDF on a trilingual ticket
corpus" is a weak, expected result. What the split actually shows is sharper and more useful:

> multilingual pretraining transfers across *languages* it has seen, and does not transfer
> across *scripts* it has not — and romanized code-mixed text, which is how customers in this
> setting actually write, is precisely the case it does not cover.

The classical baseline loses almost nothing by comparison on romanized input, because
character n-grams never depended on the script being in a pretraining corpus in the first
place.

Generator: `paper/experiments/encoder_gain_by_script.py`

---

## 17. From classifier to queue — the Ticket Urgency Score

Everything above measures what the models *know*. This section measures what that
knowledge is worth to a support desk, which is a different question with a different
answer. Design and full methodology: `paper/SYSTEM_PLAN.md`. Generators:
`paper/experiments/{save_posteriors,scoring,queue_sim,run_system_eval,calibration}.py`.

### 17.1 The score

```
U(t, τ) = S(t) · (1 + α · age(t, τ) / D)
S(t)    = w_P · Ê[sev|t] + w_S · P̂(Negative|t) + w_I · κ(intent(t))
```

`Ê[sev|t] = Σ_k p̂_k · sev_k` over `sev = (Low 0, Medium ½, High 1)` — the **posterior,
not the argmax**. `κ(i) = P̂(High | intent = i)` estimated on train+dev only. Aging is
multiplicative so a stale Low climbs but still climbs more slowly than a stale High.

**Weights fitted on dev, applied unchanged to test: `w_P = 0.80, w_S = 0.10,
w_I = 0.10, α = 16`.** Dev posteriors come from a **train-only TF-IDF** fit; the saved
LaBSE checkpoints were fit on train+dev and their dev posteriors are memorised.

**The weight surface is flat and the exact vector is not the finding.** 71 of the 231
simplex points sit within 5% of the optimum, spanning `w_P ∈ [0.10, 0.90]`. What the fit
establishes is that priority carries most of the score and that no corner of the simplex is
competitive — not that 0.80 is meaningfully better than 0.70. Reporting the argmin as
though it were identified would overclaim; the full surface ships as
`tus_weight_surface.csv`.

Simulation: M/G/5, LogNormal service, mean 8 min; SLA 30 / 120 / 480 min for
High / Medium / Low; 1,000 tickets per replication; 200 seeds; ρ ∈ {0.85, 0.95, 1.05}.
Every one of those is a **stated assumption**, not a measurement from a real desk.

### 17.2 The queue result

Mean time-to-first-response for gold-High tickets, and attainment
`(FIFO − TUS) / (FIFO − oracle)` — which separates "the scoring function is good" from
"the classifiers are good":

| ρ | FIFO | TUS | oracle | **attainment** | 95% CI |
|---|---:|---:|---:|---:|---|
| 0.85 | 5.78 | 1.13 | 0.99 | **0.971** | [0.966, 0.977] |
| 0.95 | 16.76 | 1.54 | 1.30 | **0.985** | [0.982, 0.987] |
| 1.05 | 52.46 | 1.98 | 1.47 | **0.990** | [0.988, 0.992] |

TUS captures ~98–99% of the improvement a perfect classifier would deliver. The
remaining headroom is a tenth of a minute, so **further classifier accuracy cannot
buy much here** — a conclusion invisible from the F1 tables.

### 17.3 Rank correlation is the wrong metric for a queue

| system | Kendall τ_b | nDCG@10 | P(High)@10 | P(High)@100 |
|---|---:|---:|---:|---:|
| predicted tier (argmax) | **0.822** | 0.351 | **0.50** | 0.90 |
| TUS (LaBSE) | 0.686 | **1.000** | **1.00** | **1.00** |
| priority posterior only | 0.690 | 1.000 | 1.00 | 0.99 |
| oracle (gold tier) | 1.000 | 1.000 | 1.00 | 1.00 |

**The argmax-tier policy has the highest rank correlation of any system and the worst
queue head.** τ rewards getting the global ordering right; the tier score is 3-valued
like the gold label, so it scores well — but within the top tier every ticket ties and
ordering is arbitrary, so half of the first ten tickets an agent opens are not urgent.

A queue is consumed from the top. Selecting on τ would have picked exactly the wrong
system. This is the concrete justification for evaluating triage at the queue level
rather than with a ranking correlation.

### 17.4 Script-based service disparity — and that the score largely closes it

Mean wait for gold-High tickets, **each track minus english**, ρ = 1.05, 200 seeds,
bootstrap CIs (`paper/results/tables/tus_disparity.csv`):

| policy | singlish | sinhala | tamil | tamilish |
|---|---:|---:|---:|---:|
| FIFO | −0.85 [−2.23, +0.50] | −0.22 [−1.60, +1.19] | −0.23 [−1.85, +1.44] | −0.82 [−2.25, +0.59] |
| **tier** (naive argmax) | **+4.07 [+2.96, +5.21]** | +0.37 [−0.56, +1.30] | −0.01 [−1.07, +1.07] | **+6.99 [+5.76, +8.19]** |
| **TUS** | **+0.37 [+0.05, +0.68]** | +0.24 [−0.02, +0.49] | +0.02 [−0.21, +0.22] | **+0.50 [+0.26, +0.72]** |
| oracle (gold control) | −0.02 [−0.09, +0.04] | 0.00 [−0.06, +0.07] | 0.00 [−0.07, +0.07] | −0.01 [−0.07, +0.06] |

Bold marks intervals excluding zero. Read the table as four nested controls:

- **Under FIFO, nothing.** All four contrasts straddle zero. FIFO never reads the ticket,
  so there is nothing for a script to degrade — the arrival process contributes no gap.
- **Under the gold-label control, nothing.** Same tickets, same arrival stream, labels not
  predicted. Any gap in between is therefore **attributable to the model**.
- **Under the naive deployment, exactly and only the two romanized tracks.** Singlish
  +4.07 min and Tanglish +6.99 min; the two *native* non-English tracks are
  indistinguishable from English. This is §16's native-versus-romanized finding expressed
  in minutes of customer waiting time, and it is a sharper result than §16's, because
  Sinhala and Tamil come out at zero rather than merely smaller.
- **TUS cuts both by about an order of magnitude** — singlish +4.07 → +0.37, tamilish
  +6.99 → +0.50. Paired on the simulation seed it removes **3.70 min [2.57, 4.85]** of the
  singlish gap and **6.49 min [5.32, 7.77]** of the tamilish one. It does not remove all of
  it: both residuals still exclude zero.

**The finding does not depend on the unstable track.** §18 shows tamilish carries 60.3% OOV
against its own train split (versus 20–30% everywhere else) because its romanization is
non-deterministic, which inflates every tamilish test number. **Singlish carries the result on its own** — +4.07 min under the naive policy,
with a wholly ordinary OOV profile — and singlish and tamilish behave alike here, which is
what the script hypothesis predicts and the data-defect hypothesis does not.

The mechanism is the one the score was designed for: `κ(intent)` is a script-robust prior
that backstops the priority head where the text is degraded, and the continuous posterior
avoids the tier collapse that makes the argmax policy discriminate hardest exactly where it
is least accurate.

**A note on the summary statistic.** An earlier draft reported the max-minus-min *spread*
across the five tracks. That statistic is upward-biased — it selects the extreme of five
noisy means — and the proof is that FIFO scores a "spread" of 16.2 minutes while every one
of its fixed contrasts is indistinguishable from zero. The spread is retained in the table
as `spread_biased` with that caveat; the contrasts are what the paper reports.

### 17.5 What the encoder's accuracy advantage buys the queue: nothing measurable

Same score, same weights, priority and sentiment posteriors swapped
(ρ = 1.05, 200 seeds):

| | LaBSE | TF-IDF |
|---|---:|---:|
| priority macro-F1 (test) | **0.8901** | 0.8706 |
| High mean wait | 1.98 min | **1.80 min** |
| High median wait | 1.11 | **1.10** |
| High p95 wait | **5.32** | 5.42 |
| High p99 wait | 13.27 | **12.05** |
| **High worst-case wait** | **362.1** | **97.9** |

The more accurate model is not the better queue. Through the median and the 95th
percentile the two are indistinguishable — tenths of a minute, changing sign. They
separate in the **tail**, where LaBSE's worst-served urgent ticket waits **six hours
against TF-IDF's ninety-eight minutes**.

The claim is not "TF-IDF wins": it is that **a 2-point macro-F1 advantage buys nothing
through the body of the queue and costs something in the tail.**

The mechanism is in the tail, and it is a metric F1 cannot see:

| | gold-High missed | **buried below score 0.1** | missed-High mean Ê[sev] |
|---|---:|---:|---:|
| LaBSE | 165 / 1460 (11.3%) | **68** | 0.274 (p10 = 0.002) |
| TF-IDF | 193 / 1460 (13.2%) | **8** | 0.407 (p10 = 0.157) |

LaBSE makes **fewer** mistakes and **8.5× more confident** ones. A confidently-missed
High falls to the bottom of the queue and stays there — which is exactly the six-hour
worst case above; a hedged miss lands mid-queue and is picked up soon. Macro-F1 counts
both as one error.

**Buried urgent tickets — gold-High scored below 0.1 — is a triage-specific error metric
worth reporting alongside F1.** It is what the queue actually feels.

### 17.6 A refuted hypothesis, kept visible

Calibration measured per track (`paper/results/tables/calibration.csv`) supported a
tidy explanation:

| priority, test | LaBSE | TF-IDF |
|---|---:|---:|
| macro-F1 | 0.8901 | 0.8706 |
| ECE | 0.0658 | **0.0180** |
| over-confidence | +0.066 | −0.017 |
| ECE on tamilish | **0.1071** | 0.0235 |

LaBSE is the more accurate model, 3.7× the worse calibrated, and worst calibrated
exactly on the track it is least accurate on — the double penalty predicted in
`SYSTEM_PLAN` §3 Layer 4. The obvious inference was that calibration causes the queue
gap and temperature scaling would close it.

**It does not** — and this is now a **held-out result**, not the sensitivity analysis it
was. A train-only LaBSE run (tracker E6b) supplied clean dev posteriors, so the temperature
is fitted the way deployment would fit it: on data the model never trained on.

The two estimates agree, which is worth noting because it means the earlier cross-fitted
figure was not an artifact of touching test: **T = 2.347 / 1.919** (priority / sentiment)
fitted on clean dev, against 1.93 / 1.89 cross-fitted. Same direction, same magnitude.

Fitting it properly makes the queue **worse than the cross-fitted version did**:

| | ECE (priority) | High mean wait | tamilish − english |
|---|---:|---:|---:|
| LaBSE uncalibrated | 0.0658 | **1.98** | **+0.50** |
| T cross-fitted on test halves | **0.0180** | 2.32 | +0.72 |
| **T fitted on clean dev (held out)** | — | **2.65** | **+0.97** |

The properly-calibrated system serves urgent tickets **34% more slowly** and nearly
**doubles** the cross-script disparity.

Softening the distribution compresses `Ê[sev]` toward the middle for *every* ticket,
which costs discrimination everywhere in exchange for rescuing the confident errors it
cannot identify. **ECE is agreement between top-1 confidence and accuracy; a queue needs
posteriors that separate tickets.** Those are not the same objective, and "calibrate
before you score" — standard advice — was wrong here.

The buried-ticket asymmetry in §17.5 stands as the mechanism; ECE is a symptom of it,
not the handle on it.

### 17.7 The objective that selected a degenerate system

Recorded because any triage study can walk into it. The first fitting objective was
absolute tardiness weighted by severity (Low 0.5 / Medium 1.0 / High 1.5). The class
mix is 55% Low / 36% Medium / 9% High, so **Low carried 0.275 of the objective's mass
against High's 0.143** — it rewarded not starving Low nearly twice as much as serving
High. The argmin was `w = (0, 0, 1)`: intent criticality alone, a scorer that cannot
separate Medium from Low at all (κ ≈ 0.023 for both) and whose top-100 precision on
gold-High is 0.77 against the fitted system's 1.00.

The fix is to denominate lateness in units of the promise made to that customer —
relative tardiness, `max(0, wait − d) / d` — so a High 30 minutes late and a Low 480
minutes late both score 1.0. **Weighting classes by population share rather than by
urgency inverts what a triage system is for.**

### 17.8 The aging term is a dial, not a fitted constant

| α | High mean wait | Low p95 wait | relative tardiness |
|---|---:|---:|---:|
| 0 | 1.78 | 600.7 | 0.031 |
| 1 | 1.76 | 447.3 | 0.011 |
| 8 | 1.94 | 382.3 | 0.007 |
| **16 (fitted)** | 1.97 | 372.6 | 0.006 |
| 32 | 2.01 | 365.8 | 0.006 |
| 128 | 2.21 | 361.1 | 0.006 |

A real frontier: without aging the score starves Low tickets for ten hours at the 95th
percentile. The objective is nearly flat above α ≈ 8 while High wait keeps degrading,
so the fitted α = 16 sits on a plateau rather than at the grid edge — the grid was
extended to 128 to confirm that. **α is a policy dial for the desk to set along this
frontier, not a constant this study should claim to have optimised.**

### 17.9 Where this leaves the paper

| | contribution | status |
|---|---|---|
| C1 | five-track corpus, frozen split, measured label ceiling | done |
| C2 | multilingual pretraining transfers across languages, not scripts; mechanism is `[UNK]`, not fertility | done (§16, §14) |
| **C3** | **a ticket-ordering system consuming posteriors, and a queue-level evaluation methodology** | **done (§17.1–17.3)** |
| **C4** | **script-based service disparity, and that the score removes ~85% of it** | **done (§17.4)** |
| **C5** | **accuracy does not transfer to the queue; confident errors are what the queue feels** | **done (§17.5–17.6)** |

C1–C2 are the NLP track; C3–C5 are the use-case track. C4 is the join: the cost of C2
is not visible until C3 exists to measure it.

### 17.10 The recommended system

What the evidence above actually supports deploying, as against what a benchmark table
would have suggested.

| decision | recommendation | why |
|---|---|---|
| **Consume the posterior, not the argmax** | required | §17.3 — the argmax-tier policy has the best rank correlation and half its first ten tickets are not urgent |
| **Priority head** | LaBSE **or** TF-IDF | §17.5 — a 2-point macro-F1 advantage buys nothing through the body of the queue. TF-IDF is ~1,000× cheaper to serve. Prefer LaBSE only if the tail matters less than the mean, which is unusual for a desk |
| **Sentiment head** | **do not deploy a second encoder** | ablation: w_S fits to 0.10 and removing it costs little. §13 already showed half the Negative signal is reachable from intent alone. A 1.9 GB model for a 0.10 weight on a redundant signal is not worth serving |
| **Intent term κ(i)** | keep — it is 77 floats | script-robust prior that backstops the priority head where the text is degraded; it is a lookup table, not a model |
| **Aging α** | expose as a dial, default 8–16 | §17.8 — a real frontier. Without aging the score starves Low tickets for ten hours at p95 |
| **Calibration** | **do not temperature-scale** | §17.6 — it fixed ECE and made the queue worse |
| **Escalation gating** | never | 0.67 Negative recall. The score is an ordering, not a decision |
| **Monitor** | buried-urgent count, and wait by language | §17.5 and §17.4 — both are invisible to macro-F1, and both are what the desk and the customer actually feel |

The uncomfortable summary: **the cheapest classifier in the roster, consumed properly,
serves this queue as well as the best one.** The scoring function and the aging dial
matter more than the encoder, and the one thing worth spending on is not a bigger model —
it is the labels, which cap sentiment at 0.7931 (§11).

**What would change this conclusion.** Attainment is already 0.97–0.99 (§17.2), so the
gap between the deployed system and a *perfect* classifier is a tenth of a minute at every
load tested. That is a strong claim resting on assumed arrival and service parameters
(tracker E10); a real desk running hotter, or with a heavier-tailed service distribution,
would widen the room a better classifier could occupy. The load sweep is there so that a
reader with real numbers can find their own row.

---

## 18. Intent on test — the first clean numbers, and a corpus defect they exposed

K6b: `labse`, `mmbert`, `xlmr-base`, 6 epochs, lr 2e-5, batch 32, fp16, seed 42, fitted on
`train+dev` (49,990 rows), scored once on test (15,395 rows). All three record
`epoch_selection = final-epoch` with `best_epoch = 6 of 6`, so **the epoch-selection defect
is inert here by construction** — there was no earlier epoch to select.

### Macro-F1 (%), frozen split `e7b5934392cd`, v8

| model | pooled | english | sinhala | tamil | singlish | **tamilish** |
|---|---:|---:|---:|---:|---:|---:|
| **LaBSE** | **88.35** | 94.12 | **93.19** | **93.29** | **90.34** | 69.28 |
| XLM-R base | 88.01 | 94.02 | 92.44 | 91.51 | 89.87 | **70.67** |
| mmBERT | 86.80 | 93.74 | 91.23 | 91.47 | 90.13 | 65.66 |

On dev, mmBERT and LaBSE were statistically indistinguishable (Δ = −0.0001, p = 0.944). On
test the order is **LaBSE > XLM-R > mmBERT**.

### 18.1 The dev tie does not survive on test — and the gap is a script gap

K6b wrote no per-row predictions, so this was initially a point estimate. The checkpoints
came back, so the predictions were recovered by re-running inference over the same frozen
test set (`paper/experiments/intent_test_predictions.py`, reproducing both recorded scores
to within 1e-4). The paired tests are therefore now possible.

**LaBSE − mmBERT, intent test macro-F1:**

| slice | Δ | 95% CI | McNemar |
|---|---:|---|---|
| all five tracks | **+0.0155** | [+0.0114, +0.0197] | p = 7.8e-13 |
| tamilish excluded | **+0.0106** | [+0.0066, +0.0148] | p = 7.1e-07 |
| english | +0.0037 | [−0.0036, +0.0113] | p = 0.375 — **n.s.** |
| **sinhala** | **+0.0196** | [+0.0117, +0.0276] | p = 1.8e-06 |
| **tamil** | **+0.0178** | [+0.0102, +0.0263] | p = 2.8e-05 |
| singlish | +0.0022 | [−0.0080, +0.0118] | p = 0.742 — **n.s.** |
| tamilish *(defective track)* | +0.0363 | [+0.0227, +0.0506] | p = 1.7e-07 |

**mmBERT is beaten on test**, and the result survives dropping the defective track. But the
pooled number hides the shape: **the advantage is confined to the two non-Latin scripts.**
English and Singlish — both written in Latin characters — show no difference at all. Sinhala
and Tamil both show ~+0.018 to +0.020.

So LaBSE's edge over mmBERT here is a **script-coverage** edge, consistent with its 501k
vocabulary, not a general modelling edge. This is a third independent sighting of the
native/romanized structure in §16 and §17.4, and the first in a contrast between two
*encoders* rather than between an encoder and a classical baseline.

**A caution on reading the dev-to-test flip.** The dev comparison was fitted on `train`; the
test comparison on `train+dev`. They are different fits, so "a tie became a win" may be a
fit-portion effect as much as a generalisation one. What is solid is the test result itself,
which is a single-shot comparison of two models fitted identically.

**And it corroborates §18.2.** Tamilish is Latin script, so by the pattern above it should
behave like english and singlish and show *no* gap. It shows the largest gap of any track.
That is what a degraded input looks like — when the text is broken, model capacity starts to
matter on a track where it otherwise would not.

For reference, against the classical champion on the same test set: **LaBSE − tfidf-svm =
+0.0526 [+0.0475, +0.0579]**, McNemar p = 3.2e-87.

### 18.2 The tamilish column is not a model result — it is a corpus defect

Tamilish scores 65–71 on test against **91.2–91.7 on dev**, a drop of ~22 points that no
other track shows (english, sinhala and tamil move by 1–3 points; singlish by 2).

That asymmetry is not a generalisation gap. It is a vocabulary discontinuity between the
train and test renderings of that one track:

| track | OOV rate, dev vs train | **OOV rate, test vs train** |
|---|---:|---:|
| english | 14.8% | 20.3% |
| singlish | 13.3% | 27.8% |
| sinhala | 13.7% | 30.2% |
| tamil | 21.6% | 29.8% |
| **tamilish** | 22.3% | **60.3%** |

Every track's OOV rate rises from dev to test — dev is carved from the BANKING77 *train*
file while test is the official *test* file, so some rise is expected. Tamilish rises
**38 points**, against 6–17 for everything else, and its dev figure (22.3%) is unremarkable
and in line with tamil's.

**The cause is romanization instability, not a second pipeline.** An earlier draft of this
section attributed the gap to the test file having been produced by a different process.
That was wrong, and the vocabulary statistics say so plainly:

| track | train vocabulary | test vocabulary | test types also seen in train |
|---|---:|---:|---:|
| singlish | 3,293 | 1,823 | **72.2%** |
| **tamilish** | **7,250** | 4,744 | **39.7%** |

Both tracks render the same 8,500 training tickets, and tamilish needs **2.2× the vocabulary**
to do it. That is the signature of a romanization step emitting many spellings for one
underlying word — not of two different corpora.

The corpus documentation already holds the reason. **Singlish is rule-generated** from the
Sinhala text, so it is deterministic: one Sinhala word, one Latin spelling, every time.
**Tanglish is machine-translated**, so the Latin form is produced freely and the same Tamil
word can surface several ways. One process, applied consistently — the instability is
intrinsic to the method, not a fault in how it was run.

Corroborating: tamilish test text averages **more characters but fewer words** than tamilish
train (71.5 chars / 8.74 words vs 68.6 / 9.79) — the same content spelled longer — and
tamilish is the only track with duplicate test strings (3,034 unique of 3,079). Its 0.23%
train/test text overlap, the lowest of any track and previously filed under "less leakage,
good", is the same instability seen from the other side: near-zero overlap because
near-nothing is spelled the same way twice.

**The consequence for the numbers is unchanged.** A vocabulary that does not transfer
between splits is a vocabulary the model cannot use, whatever produced it.

**Consequences, stated plainly.**

- The tamilish intent test number measures a train/test transliteration mismatch, not a
  model's handling of romanized Tamil. It must not be quoted as the latter.
- The effect is task-dependent: priority on tamilish is 0.8142 macro-F1 against english's
  0.9229 — a 10.9-point gap, not a collapse. A 3-way task tolerates vocabulary drift that a
  77-way task does not.
- **§16 and §17 do not rest on it.** §16's tamil−tamilish difference-in-differences was
  already not significant (p = 0.762), so the defect did not manufacture a positive result
  there; and §17.4's disparity is carried by **singlish**, whose OOV profile is normal —
  see §17.4.
- This is a **data-side finding, not a modelling one**. The fix is a deterministic
  romanization step for Tanglish, matching how Singlish is generated (tracker E11). Until
  then the dataset card must carry it.
- It predicts something testable, and the prediction holds: any task whose difficulty scales
  with vocabulary size should degrade on tamilish and not elsewhere. 77-way intent drops 22
  points dev to test; 3-way priority drops about 1.

---

## 19. Priority on dev — six encoders, and a second sighting of MuRIL's tokenizer

K3: the full encoder roster on priority, 6 epochs, fitted on `train`, scored on `dev`.
`epoch_selection = best-on-dev`: the recorded figure is the best epoch's dev score, so it is
a **selection-optimistic estimate of dev performance**. All six models receive identical
treatment, so the comparison between them is fair; the absolute values are not held-out
numbers and must not be read as such.

### Macro-F1 (%), priority, dev

| model | pooled | english | sinhala | tamil | singlish | tamilish |
|---|---:|---:|---:|---:|---:|---:|
| **LaBSE** | **91.67** | 92.60 | 92.51 | 92.03 | 90.74 | 90.46 |
| XLM-R base | 91.55 | 92.53 | **92.58** | 91.68 | 90.89 | 90.05 |
| mmBERT | 91.30 | **92.79** | 91.74 | 91.27 | 91.22 | 89.48 |
| IndicBERT | 90.88 | 92.53 | 89.28 | 91.98 | **91.37** | 89.22 |
| TwHIN-BERT | 89.87 | 90.30 | 89.87 | 90.04 | 90.34 | 88.78 |
| MuRIL | 89.57 | 92.23 | **83.13** | 91.09 | 91.08 | 90.31 |

**The roster is flat.** 2.1 points separate six architectures, and the top three sit inside
0.4 of each other. Priority is the task where model choice matters least — consistent with
§17.5, where swapping LaBSE for TF-IDF changed the queue by fractions of a minute.

**MuRIL's Sinhala deficit reappears, with the same signature and a smaller magnitude.** Its
sinhala score is 83.13 against its own english 92.23 — a 9.1-point hole on exactly one
track, while its romanized tracks (singlish 91.08, tamilish 90.31) are among the roster's
best. This is the §14 mechanism seen on a second task: MuRIL maps 64.5% of Sinhala
characters to `[UNK]`, and no amount of fine-tuning recovers them.

The magnitude is instructive. The same tokenizer destruction costs ~14 points on 77-way
intent and ~9 on 3-way priority. **A coarser label space tolerates more input destruction**
— which is the same lesson §18 draws from the opposite direction, where a vocabulary shift
that costs priority 10.9 points costs intent 24.8.

---

## 20. Register, measured before the comparison is run

The translation comparison (tracker B2) has no external system collected yet. This section
records the metric and **this corpus's own numbers on it, fixed in advance**, so the
comparison cannot later be steered toward a favourable conclusion.

### 20.1 Why not chrF or BLEU

Scoring competing systems against *our* translation as the reference measures similarity to
us. We would score 1.0 by construction and every legitimate paraphrase would be penalised.
That is the definition of the metric, not a finding. The comparison is therefore
**reference-free**: COMET-Kiwi QE, LaBSE source–translation cosine, and blind human
adequacy/fluency ratings, all three systems on identical terms.

### 20.2 The one axis a domain corpus can legitimately claim

The corpus was built with an explicit instruction to **keep English banking loanwords in
English** — *card*, *account*, *PIN*, *ATM*, *top-up* — because that is what a Sri Lankan
bank customer types. Generic MT tends to nativise them into formal coinages nobody says
aloud. So define, over a fixed 31-term lexicon taken from the corpus prompt itself:

```
retention(system, w) = P(translation contains w in Latin script | source contains w)
```

Countable, comparable, and able to lose.

### 20.3 The two tracks were not built to the same standard

| track | loanword retention | Latin character fraction |
|---|---:|---:|
| **Sinhala** | **0.6456** | **0.3529** |
| **Tamil** | **0.0759** | 0.0183 |

`paper/results/tables/register_summary.csv`, 150-row sample, 77/77 intents.

The Sinhala track keeps roughly **two-thirds** of English banking terms in English and is
35% Latin by character. The Tamil track keeps **under eight percent** and is essentially
pure Tamil script.

**These are not two renderings of one editorial policy.** They are two different policies,
and only the Sinhala one implements the code-mixing the corpus documentation claims. So:

- For **Sinhala** there is a specific, falsifiable claim available — that this corpus matches
  the register of Sri Lankan banking support better than generic MT — which the comparison
  can confirm or refute.
- For **Tamil** the claim is very likely **false**, and should not be made. At 7.6%
  retention the Tamil track is formal-register translation, and a frontier model instructed
  to code-mix would beat it on this metric trivially.

This is a **register decision, not a pipeline difference.** The two tracks came out of the
same corpus process; what differs is how much English survived translation into each target
language. Alongside `corpus_stats.py`'s 40.35%-vs-1.26% Latin split and §18.2's romanization
instability, the consistent picture is that **the Sinhala side preserved the code-mixing the
documentation describes and the Tamil side did not** — so the documentation's claim holds for
one track of two, and the paper should say which.

### 20.4 What this study is not allowed to conclude

That this corpus is the best translation, on the grounds that we would like it to be. Raw
adequacy is where a frontier model most plausibly wins: our Sinhala and Tamil are
machine-translated and unaudited at scale, and §18.2 shows at least one track has a
provenance defect. **A comparison whose conclusion is fixed in advance is not evidence**,
and a reviewer who spots reference-based scoring against our own text will discount every
other number in the paper.

If we lose, that is publishable and cheap to say: it motivates the v1.1 retranslation that
§18.2 already requires, and a corpus paper that reports its own resource's weaknesses is
more credible, not less.


---

## 21. Decoders on test — a 270M LoRA decoder ties a bag of character n-grams

A5, first slot. `gemma-3-270m`, LoRA on all seven projections (r=8, α=16), lr 1e-4, batch 32,
6 epochs, fitted on `train+dev` (49,990 rows), scored once on test (15,395 rows).
`epoch_selection = final-epoch` with `best_epoch = 6 of 6`, so the epoch-selection defect is
**inert by construction** — there was no earlier epoch to select.

### 21.1 Intent, test, frozen split `e7b5934392cd`, v8

| family | model | macro-F1 |
|---|---|---:|
| encoder | **LaBSE** | **0.8835** |
| encoder | XLM-R base | 0.8801 |
| encoder | mmBERT | 0.8680 |
| classical | tfidf-svm | 0.8308 |
| **decoder** | **gemma-3-270m** (LoRA-all) | **0.8305** |
| classical | tfidf-logreg | 0.8189 |
| classical | tfidf-sgd | 0.8115 |
| classical | tfidf-cnb | 0.6792 |

**The decoder lands 0.0003 below TF-IDF + linear SVM and 5.3 points below LaBSE.** On a 77-way
intent task at this corpus size, a 270M-parameter autoregressive model adapted with LoRA buys
nothing over character n-grams and a linear margin, while a 471M bidirectional encoder
fine-tuned end-to-end beats both comfortably.

This is the cheap version of the claim the SLM literature invites, and it goes the other way.
It belongs in the paper as a negative result with the cost attached: the decoder run cost
2,694 GPU-seconds; `tfidf-svm` fits on a laptop CPU in under a minute for the same score.

### 21.2 `gemma-3-1b` OOM'd and is not yet in this table

The 1B model **failed to train at all** — CUDA OOM 88 seconds in, before the first step, at
batch 32 × seq 128 with adapters on all seven projections (it asked for 90 MiB with 14.50 GiB
of the card's 14.56 GiB already committed). Relaunched at **batch 8**.

**Comparability caveat, to be stated wherever both decoders appear:** the retry runs at batch 8
against `gemma-3-270m`'s batch 32. The two decoders are matched on epochs, lr, LoRA config,
fit portion and split, but **not on batch size**. Compare each against the encoder and
classical rosters; do not read a 1b-vs-270m difference as a scale effect until one is re-run.

The pre-v8 `gemma-3-1b` records already in `ml/reports/runs/` (intent test 0.8586, sentiment
0.7126, priority 0.8898) are **not** substitutes: they carry no `label_version` stamp and were
produced under the pre-patch epoch-selection path.

### 21.3 Seed sensitivity, measured once

`labse` sentiment test re-run at **seed 43** (seed 42 = the record the paper quotes):

| | epoch 3 | epoch 6 |
|---|---:|---:|
| seed 42 (3-epoch run) | **0.7138** | — |
| seed 43 (6-epoch run) | **0.6980** | 0.6963 |

At matched epoch the spread is **0.0158**, and seed 43's curve is flat from epoch 2 onward, so
budget is not the driver. Consequences, kept separate because the metrics differ in noisiness:

- §15's labse − tfidf-svm sentiment gap (+0.0485) and §16's DiD (+0.0698) are 3× and 4.4× the
  spread. Both **survive**.
- §18.1's labse − mmBERT intent gap (+0.0155) is the same order — **but it is macro-F1 over
  15,395 rows, while 0.0158 was measured on Negative-F1 over 975 positives.** The two are not
  interchangeable and the intent result is not refuted by this. It is, however, no longer
  defensible to present [+0.0114, +0.0197] as total uncertainty.

**Every confidence interval in this report is a within-fit bootstrap interval and excludes
seed variance.** One repeat is not a variance estimate; the paper must say so rather than
imply the intervals cover training noise.

---

## 22. Ordering the queue, from the literature only

§17's Ticket Urgency Score was a scoring function we designed. It is withdrawn. Everything
below is a published rule, applied unchanged, with the result that licenses it. Nothing here
is fitted to make a number look good; the only estimated objects are the label models, and
they are estimated on dev and applied once to test.

Artifacts: `paper/experiments/policy_bakeoff.py`, `run_policy_bakeoff.py`,
tables `bakeoff_label_models.csv`, `bakeoff_policies.csv`, `bakeoff_sample_set.csv`,
`bakeoff_disagreements.csv`. 200 seeds, M/G/5, LogNormal service (mean 8 min, sigma 0.75).

### 22.1 Why the three labels cannot be three additive terms

Measured on train (english, n = 9,998), in nats:

| quantity | value | as a share |
|---|---|---|
| H(priority) | 0.9333 | — |
| I(intent; priority) | 0.7178 | 76.9% of H(priority) |
| I(sentiment; priority) | 0.0172 | 1.8% of H(priority) |
| I(sent; prio \| intent) | 0.0149 | 86.6% of the sentiment-priority association survives conditioning on intent |

Intent nearly determines priority, so an additive score `w_P·(priority head) + w_I·(intent head)`
adds two estimates of the same quantity and its fitted weight measures collinearity, not
contribution. That is why §17's weight surface was flat. Sentiment is the mirror image: almost
no information in absolute terms, but what it has is *not* redundant with intent. Neither fact
is visible in a simplex weight, which is the argument for a joint model over an additive score.

### 22.2 A defect in the label-model table, and what it changes

The first version of this table called `log_loss(y, P, labels=["Low","Medium","High"])`.
sklearn binarises `labels` through `LabelBinarizer`, which **sorts** them, and then reads the
columns of `y_prob` in that sorted order regardless of the order `labels` was written in. Our
columns are Low, Medium, High; sorted they are High, Low, Medium. Every probability was
therefore scored against the wrong class. The tell was in the magnitudes — the reported values
ran 4.7 to 7.2, when a three-class uniform predictor gives ln 3 = 1.0986, so every model was
being scored as far worse than guessing. Measured directly: **a perfect predictor scores 36.04
under the old call and 0.0 under the corrected one.**

Corrected, on test:

| label model | log_loss | macro_F1 | score_sd |
|---|---|---|---|
| **logpool** (log opinion pool) | **0.2683** | **0.8983** | 0.0086 |
| chain-full (2-parent chain) | 0.3111 | 0.8749 | 0.0080 |
| chain-intent (classifier chain) | 0.3160 | 0.8742 | 0.0080 |
| stacked (Wolpert 1992) | 0.3333 | 0.8914 | 0.0087 |
| marginal (binary relevance) | 0.3697 | 0.8901 | 0.0088 |

The correction **changed the winner**: `stacked` was reported first and is now fourth;
`logpool` was fourth and is now first. The one claim that survives unchanged is the one the
section is actually about — **binary relevance is last**, and modelling label dependence cuts
log-loss **27%** (0.3697 → 0.2683). The earlier "35%" figure was an artifact of the permutation
and should not be quoted. Macro-F1 still barely moves (0.874–0.898), so the gain is in
*calibration*, not in argmax accuracy — which is precisely what a scheduling index consumes.

### 22.3 Each policy wins on the objective its own theorem optimizes

The earlier run ranked policies by `rel_tardiness`, which counts only delay past the SLA. **No
cited theorem optimizes that.** Cox & Smith (1961) and Argon & Ziya (2009) Thm 3 are stated over
the *linear* delay cost Σ c_k·w, and Van Mieghem (1995) over a *convex* cost. Both are now
measured directly (`lin_cost` = mean w/D_k, `conv_cost` = mean (w/D_k)^2). At ρ = 1.05:

| objective | best policy | best value | runner-up family |
|---|---|---|---|
| linear (Cox–Smith, A&Z Thm 3) | **cmu-hsf** | 0.121 | edd/gcmu 0.146–0.158 |
| convex (Van Mieghem) | **gcmu** | 0.064 | apq 0.099, edd 0.111 |

**Each rule wins exactly where its theorem says it should, and loses elsewhere.** cμ/HSF sweeps
the top five slots on linear cost (0.121–0.125) and is mid-table on convex; Gcμ sweeps convex
(0.064–0.091) and is mid-table on linear. So the choice between them is **a choice of cost
model, not an empirical horse race** — the desk decides whether lateness hurts linearly or
super-linearly, and that decision picks the rule.

**Argon & Ziya Theorem 3 holds, tested on its own metric.** Against the *same* label model,
the posterior index beats the argmax tier every time on linear cost:

| label model | cmu-hsf | static-tier |
|---|---|---|
| marginal | 0.121 | 0.163 |
| logpool | 0.121 | 0.161 |
| stacked | 0.123 | 0.168 |
| chain-full | 0.124 | 0.165 |
| chain-intent | 0.125 | 0.166 |

The two ranges do not overlap — a 25% cost reduction from consuming the posterior instead of
its argmax. On `rel_tardiness`, the metric the earlier run used, this comparison is a tie
(0.021 vs 0.021) and the theorem appears to fail. It does not fail; it was being tested against
an objective it says nothing about.

**Argon & Ziya §9 on starvation also holds**, though modestly: cμ/HSF leaves Low waiting
92–93 min, Gcμ 85–86 min.

### 22.4 What actually matters, and what does not

Under linear cost the five label models span 0.121–0.125 — **a 3% spread — while the policy
spans 0.121 to 0.381 (fcfs), a 3.1× spread.** The ordering rule dominates the label model. Under
convex cost the label model earns more: gcmu spans 0.064 (logpool) to 0.091 (stacked), a 42%
spread. So dependence modelling pays only once the cost is convex.

`logpool` is the one model that is best or near-best on all three views — log-loss, macro-F1,
and convex cost under every policy — which makes it the defensible default.

**At ρ = 0.85 none of this is visible**: lin_cost is 0.019–0.022 across every combination. With
no queue there is nothing to order. Every claim above is an overload claim.

### 22.5 What is still assumed

The SLA windows D_k (30/120/480 min) are an assumption about the desk, not a measurement —
tracker E10. Service times are LogNormal(mean 8 min, sigma 0.75), also assumed. The bake-off
scores against *gold* priority, so it measures the ordering rule and not the classifier;
the classifier's contribution enters only through the posterior it supplies.

---

## 23. Was the epoch budget enough? An audit, because 23 of 25 runs end on their best epoch

**The flag.** Across the 25 fine-tuned test records, **23 have `best_epoch == epochs`** — the
best epoch was the last one trained. Taken alone that is the signature of an undertrained
roster: if training stops while the metric is still rising, every score is a lower bound and
model comparisons are comparisons of budget.

It is not sufficient evidence on its own, because a *flat* curve also ends on its last epoch.
So the question is settled from the per-epoch histories in `paper/results/runs/history/`, not
from `best_epoch`. Verdict: **the budget is adequate for the load-bearing claims, and
inadequate for two specific things that must therefore not be claimed.**

### 23.1 Where the budget is justified

| run | per-epoch curve | last gain | verdict |
|---|---|---:|---|
| labse sentiment (3 ep) | 0.8246 → 0.8467 → 0.8478 | +0.0011 | converged |
| labse priority (dev, 6 ep) | 0.9027 → 0.9074 → 0.9155 → 0.9152 → 0.9167 → 0.9103 | −0.0064 | **past the peak** |

Sentiment at 3 epochs is converged, not truncated. Priority is the stronger case: the 6-epoch
dev curve **peaks at epoch 5 and then declines**, and epoch 3 (0.9155) is only 0.0012 below
that peak. So the 3-epoch priority test budget sits on the plateau. More epochs would not have
helped and epoch 6 would have hurt.

This also settles a comparison that looked confounded. On sentiment test, **LaBSE ran 3 epochs
and xlmr-base, mmbert and muril-base ran 6** — an unmatched budget. But it is unmatched *against*
the winner: LaBSE converged in 3 and still beat three models given twice the budget. The
mismatch works against the reported result, so it cannot manufacture it.

### 23.2 Where it is not — two things that must not be claimed

**1. Intent is still improving at epoch 6.** Both leaders are climbing when training stops:

| epoch | 1 | 2 | 3 | 4 | 5 | 6 | last gain |
|---|---|---|---|---|---|---|---:|
| labse | 0.8273 | 0.8641 | 0.8757 | 0.8794 | 0.8792 | **0.8835** | +0.0043 |
| mmbert | 0.7962 | 0.8507 | 0.8597 | 0.8643 | 0.8654 | **0.8680** | +0.0025 |

So **every intent number in this report is a lower bound**, and the roster ordering is a
statement about a 6-epoch budget, not about the models at convergence.

The headline contrast survives this, and it is worth showing why rather than asserting it.
The LaBSE−mmBERT gap across the last three epochs is **+0.0151, +0.0138, +0.0155** — stable to
±0.001 while both curves are still rising. The gap is not an artifact of where training
stopped. §18.1's +0.0155 stands; "LaBSE reaches 0.8835 on intent" should be written as a
budgeted result, not a converged one.

**2. The three failed models are undertrained, and their scores are not evidence.**

| model | epochs | curve | last gain | reported |
|---|---|---|---:|---|
| sinbert-large | 3 | 0.4419 → 0.4632 → 0.4939 | **+0.0306** | 0.1182 |
| canine-c | 3 | — | **+0.0180** | 0.4702 |
| sinhalaberto | 3 | — | +0.0051 | 0.1296 |

These are the only runs climbing steeply at cutoff — an order of magnitude faster than the
converged models. **Their low scores measure the budget, not the model.** Concretely:
`canine-c` must not be cited as evidence about character-level models. The outline positions
`clark2022canine` as "the design that cannot have this failure"; that is an argument from
architecture and it stays, but the 0.4702 number cannot be used to support or refute it.

### 23.3 What this changes

- Intent results are lower bounds; say so once, in §3, and do not restate per number.
- The LaBSE−mmBERT intent gap is budget-stable and can be claimed as-is.
- Priority's 3-epoch budget is justified by its own dev curve — state that, since 3 looks thin
  next to the 6 used elsewhere and a reviewer will ask.
- Sentiment's budget mismatch runs against the winner and is safe to report plainly.
- **sinbert-large, sinhalaberto and canine-c must be dropped from every comparative claim**, or
  rerun to convergence. They are currently reported as if their scores were meaningful.

---

## 24. The "manually verified" claim, reconciled against the per-language results (B5)

**There is no contradiction inside the repository.** README.md and RESULTS.md agree: Sinhala
was hand-corrected to colloquial code-mixed text, Singlish was rule-generated, **Tamil was
Gemini-translated with no hand pass**. The conflict is between that and the external
"translations were manually verified" claim carried in `data_statement.md` as `[CONFIRM]`.
The repository's own record is the more specific and it is the one to keep.

The open question was whether that asymmetry *matters*. It does, and the per-language test
results now say exactly where.

### 24.1 The prediction

If Sinhala received a hand pass that made it colloquial and code-mixed (measured: **40.35%
Latin characters**, against Tamil's **1.26%**), and Tamil is raw MT output, then Tamil is the
*cleaner, more monolingual* track. It should therefore be **easier** — and not uniformly, but
specifically on the label that depends on register. Intent is topic classification over 77
banking categories and should be largely register-invariant; sentiment depends on how
frustration is colloquially expressed and should not be.

### 24.2 Tamil minus Sinhala, every model with both tracks scored

| task | mean Δ | Tamil higher in | Δ excluding muril-base |
|---|---:|---:|---:|
| **sentiment** | **+0.0666** | **8 of 8** | +0.0492 |
| priority | +0.0163 | 5 of 7 | **+0.0016** |
| intent | −0.0028 | 4 of 9 | −0.0028 |

**The prediction holds, and cleanly.** Tamil beats Sinhala on sentiment for **every single
model, without exception**, by about 5 points once MuRIL is set aside. On intent the
difference vanishes (−0.003, Tamil higher in fewer than half the models). On priority it is
**+0.0016 excluding MuRIL — two orders of magnitude smaller than the sentiment effect** — and
the sign is no longer consistent (LaBSE −0.0049, XLM-R −0.0126 both favour Sinhala).

So the effect is not a general "Tamil is easier" advantage. It is **specific to sentiment**,
which is the register-dependent label, and absent on the two labels that are not.

MuRIL is excluded from the summary column because it is the §2 Sinhala-blind case
(Δ +0.1888 sentiment, +0.1048 priority) and would otherwise carry the average on its own.
Its exclusion makes the finding *weaker* and it still holds 7/7 and 4/4.

### 24.3 What this settles, and what it does not

**Settled.** The provenance asymmetry is not a documentation detail — it has a measurable,
task-specific signature that matches what an un-hand-passed track would produce. The Tamil
track is easier because it is cleaner, not because Tamil is intrinsically easier than Sinhala.

**Consequences the paper must carry:**

1. **The tamil/tamilish contrast is not a second measurement of the sinhala/singlish effect.**
   §16's caution was right and this is the evidence for it: the two pairs have different
   baselines (40.35% vs 1.26% Latin) *and* different provenance. Report the sinhala/singlish
   DiD as the finding; report tamil/tamilish as a track whose confound is now quantified.
2. **Sentiment comparisons across sinhala and tamil are confounded** and must not be read as a
   language effect. Intent comparisons are safe — the audit shows no track advantage there.
3. `data_statement.md`'s `[CONFIRM]` should be resolved *against* the external claim: state
   that Tamil received no hand pass, and cite the 1.26% Latin figure as the constraint that
   makes any "manually verified" claim untenable for that track.

**Not settled, and still needs a human record (tracker B5):** who performed the Sinhala pass,
how many rows they touched, against what criteria, and what fraction changed. The analysis
above establishes the *consequence* of the asymmetry; it cannot reconstruct the *process*.
