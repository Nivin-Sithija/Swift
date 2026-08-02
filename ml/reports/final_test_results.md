# Sentiment & priority — final test results

Split sha `e7b5934392cd` (8,500 train / 1,498 dev / 3,079 test). Test is the official BANKING77
test file, opened once.

Reproduce with [`../../notebooks/modeling/10_final_test_eval.ipynb`](../../notebooks/modeling/10_final_test_eval.ipynb).

> **The gold 500 is not an evaluation set here.** All 500 of its tickets match train text; **zero**
> match test text. It is a labeling-quality benchmark and nothing in this report scores against it.
> Ground truth throughout is the `sentiment` / `priority` columns in
> `datasets/<lang>/{train,test}_labeled.csv`.

---

## Headline

Trained on **train+dev** (9,998 ids × 5 languages = 49,990 rows), `multi` regime, default
threshold, scored once on test (3,079 ids × 5 = 15,395 rows).

| task | model | dev | **test** | 95% CI (test) | label ceiling |
|---|---|---|---|---|---|
| **sentiment** | `tfidf-svm` / class_weight / C=0.5 | 0.6144 | **0.4572** | [0.3970, 0.5130] | 0.5769 |
| sentiment | `tfidf-logreg` / ros / C=3.0 | 0.5933 | 0.4225 | [0.3627, 0.4788] | " |
| **priority** | `tfidf-svm` / class_weight | 0.9028 | **0.8722** | [0.8605, 0.8831] | 0.7722 |
| priority | `tfidf-logreg` / class_weight | 0.8972 | 0.8683 | [0.8557, 0.8802] | " |

Sentiment is `negative_f1`; priority is `macro_f1`. Never accuracy — 95.5% of tickets are Neutral.

### Per language, on test

| task | english | singlish | sinhala | tamil | tamilish |
|---|---|---|---|---|---|
| sentiment | 0.4582 | 0.4615 | 0.4138 | **0.5252** | 0.4229 |
| priority | **0.9032** | 0.8915 | 0.8745 | 0.8905 | **0.7994** |

**Tamilish is the weak track on priority** — 0.7994 against 0.87–0.90 everywhere else, a 10-point
gap that no other language shows.

---

## 1. Both tasks lost ground from dev to test, and most of it is real

Sentiment fell 0.6144 → 0.4572. Two candidate causes, and they are separable:

| component | value |
|---|---|
| total dev → test drop | 0.1571 |
| attributable to **prevalence** (test is 3.28% Negative vs dev's 4.54%) | 0.0592 |
| **genuine generalization loss** | **0.0979** |

Measured by holding the model and threshold fixed and resampling test down to dev's Negative rate
by dropping Neutral *tickets* (all five language copies together), 25 draws:
`0.5165 ± 0.0065`.

So roughly a third of the drop is the easier-to-excuse kind and two thirds is not. The CV estimate
in `bakeoff_sentiment_priority.md` §6 (0.5525) was meant to be the honest figure and **test still
came in 0.095 below it**.

## 2. Threshold tuning did not transfer

`06_improve_sentiment.ipynb` reported threshold tuning worth **+0.027**. Re-derived by 5-fold CV
over train+dev (folds on `id`, raw `decision_function` rather than the min-max normalised score,
which is fit-specific and does not transfer), then applied once to test:

| model | default | CV-tuned | Δ on test |
|---|---|---|---|
| `tfidf-svm` / class_weight | **0.4572** | 0.4524 | **−0.0048** |
| `tfidf-logreg` / ros | 0.4225 | 0.4287 | +0.0062 |

CV promised +0.006 to +0.011 and delivered −0.005 on the champion. Both deltas sit far inside the
CI. **Do not promote a model on a tuned-threshold number.**

## 3. The label ceiling reframes both tasks

From `label_ceiling.csv` — v5 prompt labels (what everything trains and scores against) versus
human annotation on the gold 500:

| task | v5 vs human | κ | test result | reading |
|---|---|---|---|---|
| sentiment | 0.5769, CI [0.40, 0.73] | 0.55 | 0.4572 | **inside the ceiling's own CI** |
| priority | 0.7722 | 0.64 | 0.8722 | **exceeds the ceiling by 10 points** |

This does not cap the measured scores — against v5 labels a model could in principle reach 1.0. It
caps what they *mean*.

**Priority at 0.8722 has learned the v5 labeling rule well.** The rule itself agrees with human
judgement at 0.7722, so that is the operational ceiling no matter what the model scores. Ship it,
and state this in any external write-up — quoting 0.87 as "priority accuracy" overstates what a
human would call correct.

**Sentiment sits inside its ceiling's confidence interval**, which is the stronger argument for the
**v6 relabel** than for a bigger model: on the 250-row holdout, v6 lifts negative-F1 from v5's
0.4615 to **0.6875**. `relabel_v6_staging.csv` is currently 40 pilot rows, train split only.

---

## 4. A tokenization defect, found and fixed

`swiftbench/models.py` used scikit-learn's default `token_pattern=r"(?u)\b\w\w+\b"`. `\w` excludes
Unicode categories `Mn`/`Mc` — **every Sinhala and Tamil vowel sign**.

Measured character loss on dev: **Sinhala 40.1%, Tamil 69.3%.** English and the romanized tracks
are unaffected.

```
කවුරු හරි මගේ කාඩ් එක පාවිච්චි   ->  ['කව', 'හර', 'මග', 'එක']      ("paavichchi" vanishes)
இது மற்றும் கவலை உதவி            ->  ['இத', 'மற', 'கவல', 'உதவ']
```

Nothing raised. Words differing only in vowel signs collapsed onto one token.

**Impact, measured** ([`08_word_tokenizer_comparison.ipynb`](../../notebooks/modeling/08_word_tokenizer_comparison.ipynb)):

| features | mean gain from the fix | max |
|---|---|---|
| word only | **+0.0200** | +0.0558 (intent, tamil) |
| word + `char_wb` (production) | +0.0020 | +0.0237 |

**`char_wb` had been silently compensating**, which is why the defect survived — the production
metric barely moves. It is fixed anyway, because it corrupted everything built on word features:
the mined lexicon in notebook 20 was extracting `කව හර` instead of `කවුරු හරි`.

**Fix:** `swiftbench/tokenize.py`, using `indic_nlp_library` dispatched on script. A plain
Unicode regex (`[\p{L}\p{M}\p{N}]+`) was rejected — it recovers the vowel signs but splits on
**ZWJ (U+200D)**, breaking `ට්‍රැක්` ("track") into two fragments. That is the exact ZWJ gotcha
`research/README.md` §3.19.3 flags. Agreement with indic-nlp: Tamil 99.5%, Sinhala 92.4%, with
every Sinhala disagreement being a ZWJ conjunct.

**Numbers in this report predate the fix** and are therefore mildly conservative for Sinhala and
Tamil. The classical dev baseline moved 0.6144 → 0.6173 after it.

---

## 5. Techniques

### Lexicon correction — null result

[`20_technique_lexicon_correction.ipynb`](../../notebooks/modeling/20_technique_lexicon_correction.ipynb).
Senevirathna et al. (2025) report **+10.2pp accuracy / +0.10 F1** on banking Sinhala/Singlish
sentiment from a lexicon-correction layer.

Mined here from train by log-odds with an informative Dirichlet prior, blended as
`z(model) + α·z(lexicon)`, α and threshold tuned by 5-fold CV *within* train:

| α | 0.0 | 0.05 | 0.2 | 0.5 | 1.0 | 1.5 |
|---|---|---|---|---|---|---|
| CV negative-F1 | **0.5554** | 0.5544 | 0.5489 | 0.5106 | 0.4697 | 0.4438 |

**CV selected α = 0.0 — use no lexicon.** On dev the best non-zero α costs **−0.0075**, negative
in all five languages.

This was predicted in the notebook before running: **their lexicon was authored externally, ours
is mined from the rows the classifier already trained on.** It carries no information the model has
not already extracted. The result says the +10.2pp came from the lexicon's *externality*, not from
the correction mechanism.

**The mined terms explain it.** Top Negative-associated terms are `someone has`, `kavuru hari`
(*someone*), `romba` (*very*), `poiduchu` (*lost/gone*), `செய்யாத` (*didn't do*) — these are
**topic markers for fraud and loss, not polarity words**. Negative sentiment in this dataset is
largely a function of what the ticket is about, which TF-IDF already captures directly.

Testing Senevirathna's actual claim needs a hand-authored banking-polarity lexicon. That is a
labeling task, and it is the follow-up — not a refutation.

### Strategy A, augmentation, adapters — built, not yet run

| notebook | status | expectation on record |
|---|---|---|
| `21_technique_strategy_a_transliteration` | built, `SMOKE=True` | **Will score well and mean little** — our Singlish is rule-generated by `singlishify.py`, so reverse-transliteration inverts a function we applied. Singlish dev OOV is 1.18%, *identical to English's*. |
| `22_technique_codeswitch_augmentation` | built, `SMOKE=True` | Includes a `duplicate` control arm so a gain can't be confused with more data. |
| `23_technique_adapters_unfrozen` | built, needs `peft` | Rathnayake Technique 3. Their own sentiment numbers move only 53→55 across *all* adapter methods — this checks a documented near-null. |

---

## 6. Encoders — roster built, runs pending

Six candidates, one notebook each (11–16), all driving the shared `swiftbench.train_encoder`.

**Tokenizer probe** (fertility, tokens/word, 300 dev tickets per language):

| model | english | sinhala | singlish | tamil | tamilish |
|---|---|---|---|---|---|
| **LaBSE** | **1.36** | **1.74** | **1.89** | **2.01** | **2.19** |
| xlmr-base | 1.43 | 1.81 | 2.23 | 2.35 | 2.35 |
| mmbert | 1.37 | 4.40 | 2.17 | 3.91 | 2.40 |
| sinhalaberto | 1.41 | 3.40 | 2.16 | 7.15 | 2.63 |
| sinbert-large | 5.09 | 4.26 | 6.65 | 6.95 | 7.20 |
| canine-c (chars) | 5.10 | 5.97 | 6.67 | 8.46 | 7.21 |

Two findings from the probe alone:

- **LaBSE beats XLM-R on every track** and was never screened — `model-research.md` §4 lists it
  only under *Embeddings (RAG)*.
- **The monolingual Sinhala checkpoints tokenize Sinhala worse than the multilingual ones**
  (SinBERT-large 4.26, SinhalaBERTo 3.40 vs XLM-R 1.81, LaBSE 1.74).

**All six report 0% `[UNK]`, and that is meaningless** — they are byte-BPE or character models,
which structurally cannot emit `UNK`. The earlier mBERT/MuRIL disqualification on `[UNK]` still
stands; those are WordPiece.

**Cost.** Measured MPS throughput is **24.1 rows/s** for xlmr-base — ~88 min for one model at 3
epochs over 42,500 rows, and roughly 12 h for all six, with CANINE worst at ~4× sequence length.
Per `classifier-bakeoff-phase3`, Kaggle T4×2 is the intended home for these.

---

## 7. Recommendations

1. **Ship priority classical now** — `tfidf-svm` / class_weight / `multi`, 0.8722 test. Do not
   fine-tune: it already exceeds its own label ceiling. State the 0.7722 human-agreement figure
   alongside it.
2. **Sentiment: relabel before re-modelling.** v6 nearly doubles holdout negative-F1 over v5
   (0.6875 vs 0.4615). The model sits inside the label ceiling's CI, so model capacity is not the
   binding constraint — label quality is.
3. **Run the encoder roster on Kaggle, not MPS.** Promote to test only if a candidate clears
   classical dev by more than the CI width (~0.08).
4. **Investigate Tamilish priority (0.7994).** It is the only double-digit per-language gap in the
   report.
5. **Get human-typed romanized tickets.** Three separate findings — Strategy A's circularity,
   augmentation's untestability, and Singlish's 1.18% OOV — all reduce to the same root cause: our
   romanized text is machine-generated and too regular to evaluate romanized techniques on.
