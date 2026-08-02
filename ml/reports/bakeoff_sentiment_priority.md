# Sentiment & priority bake-off — results

> **Read the correction in §6 before quoting any sentiment number from this
> report.** The headline 0.6395 is the maximum of 168 draws from a noisy
> distribution; cross-validation puts the honest figure at **0.5525 ± 0.044**.
> The priority findings are unaffected — its classes are large enough to measure.

Dev set, split sha `e7b5934392cd` (8,500 / 1,498 / 3,079). 336 evaluations per
pair of tasks: 3 regimes × 5 languages × 4 models × 3 class-balancing arms.
**Test was not touched.**

Reproduce with [`../../notebooks/modeling/03_benchmark_sentiment.ipynb`](../../notebooks/modeling/03_benchmark_sentiment.ipynb)
and [`04_benchmark_priority.ipynb`](../../notebooks/modeling/04_benchmark_priority.ipynb).
Raw per-run JSON is in `runs/`; flat tables are `sentiment_bakeoff_dev.csv` and
`priority_bakeoff_dev.csv`.

---

## Headline

| task | floor | champion | config | verdict |
|---|---|---|---|---|
| **sentiment** | 0.000 Negative-F1 (always-Neutral) | 0.6395 single-split → **0.5525 ± 0.044 CV** (§6) | `tfidf-svm` / `class_weight` / C=0.5 | wide headroom — **fine-tune an encoder** |
| **priority** | 0.9040 macro-F1 (`intent-chained`) | **0.9119** | `tfidf-svm` / `class_weight` / tamil / multi | ~0.3pt from the oracle ceiling — **ship classical, don't fine-tune** |

---

## 1. Regime: one multilingual model, not five monolingual ones

| regime | sentiment (mean / best Negative-F1) | priority (mean / best macro-F1) |
|---|---|---|
| `mono` — train on eval language | 0.4773 / 0.6395 | 0.8858 / 0.9115 |
| `multi` — one model, all 5 languages | **0.4985** / 0.6331 | **0.8874** / 0.9119 |
| `zeroshot-en` — never sees eval language | 0.0847 / 0.3158 | 0.5625 / 0.7579 |

**`multi` matches or beats `mono` on both tasks.** One model serving all five
languages costs nothing in accuracy and removes four models from the serving
path. This is the deployment answer.

**`zeroshot-en` collapses.** Sentiment falls from ~0.48 to 0.085; priority's
`High` class falls to 0.39 F1. Cross-script transfer from English does not
happen for free, which means the translated training data is doing real work —
and that a sixth language would need its own data, not transfer.

## 2. Class balancing

Sentiment, averaged over all 168 runs:

| arm | accuracy | Negative-F1 |
|---|---|---|
| `none` | **0.9281** | 0.3171 |
| `class_weight` | 0.9252 | **0.4061** |
| `ros` | 0.9293 | 0.3949 |

The unbalanced arm posts competitive accuracy and the worst Negative-F1 of the
three. This is why the project reports Negative-F1: at 95.5% Neutral, accuracy
rewards a model for declining to do the job.

For priority the arms are nearly indistinguishable (0.7905–0.7962 macro-F1) —
53/37/10 is mild enough that balancing barely moves it.

## 3. Estimator

| model | sentiment (mean / max) | priority (mean / max) |
|---|---|---|
| `tfidf-svm` | **0.4082** / 0.6331 | **0.8137** / 0.9119 |
| `tfidf-logreg` | 0.3566 / **0.6395** | 0.8093 / 0.9068 |
| `tfidf-cnb` | 0.3744 / 0.5304 | 0.7796 / 0.8739 |
| `tfidf-sgd` | 0.3517 / 0.5802 | 0.7735 / 0.9074 |

`tfidf-svm` is the most reliable; `tfidf-logreg` + `ros` takes the single best
sentiment cell. The spread between estimators (~0.05) is smaller than the spread
between arms (~0.09) — **the balancing choice matters more than the model
choice.**

## 4. Priority: direct beats the chained bar everywhere

| language | `intent-chained` (bar) | direct best | oracle | beats bar by | gap to oracle |
|---|---|---|---|---|---|
| english | 0.8931 | 0.8999 | 0.9147 | +0.0068 | 0.0148 |
| singlish | 0.9040 | 0.9115 | 0.9147 | +0.0074 | 0.0032 |
| sinhala | 0.9011 | 0.9079 | 0.9147 | +0.0068 | 0.0068 |
| tamil | 0.8921 | 0.9119 | 0.9147 | +0.0198 | 0.0028 |
| tamilish | 0.8945 | 0.9074 | 0.9147 | +0.0129 | 0.0073 |

Reading text directly beats routing through a predicted intent in all five
languages, so priority gets its own head and stops inheriting the intent
classifier's errors. `High`-class F1 holds at 0.90–0.91 — it is not collapsing
behind a healthy macro average.

The oracle (gold intent → majority-priority lookup, 0.9147) is a **ceiling, not
a target**: at serving time nobody supplies the gold intent. The direct model
sits within 0.3–1.5pt of it.

---

## 5. Fine-tuning decision

**Priority — do not fine-tune.** The classical champion is within ~0.3pt of the
gold-intent oracle. Priority is close to a deterministic function of intent, and
the label was derived from the same ticket text the model already reads. There
is roughly one point of headroom in total and an encoder cannot meaningfully
exceed the oracle. Ship `tfidf-svm` / `class_weight` / `multi`.

**Sentiment — fine-tune.** The champion sits at 0.6395 Negative-F1 with 0.529
precision, so roughly a third of genuinely angry customers still get routed to
an auto-reply. The binding constraint is that only **462 of 9,998** training
tickets are Negative — exactly the low-resource regime where a pretrained
multilingual encoder should beat TF-IDF, because it brings sentiment knowledge
those 462 examples cannot supply.

### Which encoder — measured, not assumed

Tokens per word (lower = less fragmentation = more pretrained signal survives):

| tokenizer | english | singlish | tamilish | sinhala (native script) |
|---|---|---|---|---|
| `xlm-roberta-base` | 1.14 | 2.40 | 2.17 | **1.60** |
| `mmBERT-base` | 1.14 | **2.00** | **2.00** | **4.60** |

mmBERT is modestly better on romanized text but **shatters native Sinhala script
at 4.6 tokens/word, nearly 3× XLM-R**. Since the multilingual (`multi`) regime is
the one we want to ship, and it must handle native Sinhala and Tamil alongside
the romanized tracks, **XLM-R is the first candidate.** mmBERT is worth trying
only for a romanized-only model.

This is also why mmBERT's 1,833-language claim should not be taken on trust for
this project — it was verified and it failed on the script that matters most.

### Setup

[`../../notebooks/modeling/11_encoder_xlmr_base.ipynb`](../../notebooks/modeling/11_encoder_xlmr_base.ipynb),
`SMOKE = True` by default. It deliberately does not reuse
`../scripts/train_transformer.py`, which builds its validation split with
`train_test_split` over pooled five-language rows — one ticket is five rows
sharing an `id`, so a ticket's English copy can train while its Sinhala copy
validates. This notebook takes its split from `swiftbench` (drawn on `id`) and
selects on `negative_f1`, not accuracy or loss.

---

## 6. Correction — the sentiment ranking above is not statistically supported

Added after [`06_improve_sentiment.ipynb`](../../notebooks/modeling/06_improve_sentiment.ipynb).
Everything in §1–§5 for **sentiment** was selected on a single dev split at the
default 0.5 threshold with `C` pinned at 1.0. All three were mistakes.

**Dev holds 68 Negative tickets.** Bootstrapping the champion, resampled by
ticket `id`:

```
negative_f1 0.6395    95% CI [0.5521, 0.7174]    width 0.165
```

**All 10 of the top 10 configurations fall inside that interval.** Their ordering
is noise. The `mono` vs `multi` regime gap for sentiment (0.4773 vs 0.4985) is
far smaller than this and should not be read as a real difference either — the
priority regime comparison is unaffected, since its classes are large.

Pooling languages does not add evidence: the pooled dev set has 340 Negative
*rows* but only **68 unique Negative tickets**. The other 272 are translations of
those same tickets. Any CI computed over 340 rows is dishonestly narrow, which is
why `tuning.bootstrap_ci` resamples over ids with all five copies travelling
together.

### What the honest numbers are

5-fold cross-validation over train+dev, folds drawn on `id`:

| setup | Negative-F1 |
|---|---|
| bake-off headline (single dev, C=1.0, threshold 0.5) | 0.6395 |
| CV, tuned `C` | **0.5525 ± 0.044** |
| CV, tuned `C` + tuned threshold | **0.5721** |

The ~0.087 gap is selection optimism, not a regression. **0.55 is what to expect
on unseen data.**

### Two practices the bake-off skipped

- **Threshold tuning** — worth **+0.027** on the champion (0.50 → 0.58). Larger
  than most of the model gaps §3 was ranking on, and free.
- **`C` search** — 1.0 was wrong for both estimators (`tfidf-logreg` prefers 3.0,
  `tfidf-svm` prefers 0.5).

The operating point is a **product decision**: at 95% Negative recall, roughly
3 in 4 escalations are false alarms. How much of that agents will absorb is not
an ML question.

### Encoder candidates — the first pass was inadequate

The §5 comparison tested two encoders on a four-sentence tokenizer probe and
ignored [`tokenizer_comparison.md`](tokenizer_comparison.md), an existing
15,000-sample study. [`07_encoder_bakeoff.ipynb`](../../notebooks/modeling/07_encoder_bakeoff.ipynb)
runs the full roster from `model-research.md` §4 over 2,000 real rows per
language. Corrected findings in
[`encoder_tokenizer_fertility.csv`](encoder_tokenizer_fertility.csv):

| model | mean fertility | Sinhala `[UNK]` % | status |
|---|---|---|---|
| muril | 1.599 (best) | **64.53** | **disqualified** |
| xlmr-base / xlmr-large / twhin-bert | 1.791 | 0.00 | shortlisted |
| indicbert | 2.050 | 0.59 | shortlisted |
| mbert | 2.069 | **61.35** | **disqualified** |
| mmbert | 2.525 (worst) | 0.00 | shortlisted |

**Ranking on fertility alone would have picked the worst candidate.** MuRIL
leads on mean fertility precisely *because* it maps two-thirds of Sinhala to
`[UNK]` — discarded text is cheap to tokenize. Fertility must always be read
next to `[UNK]` rate.

mmBERT's real Sinhala fertility is 3.67, not the 4.60 the four-sentence probe
reported, and it is also worst on Tamil (3.72) — which that probe never tested.
TwHIN-BERT, XLM-R base and XLM-R large share XLM-R's tokenizer exactly, so any
difference between them isolates pretraining data from tokenization.

### Fine-tuning screen — and the tokenizer heuristic fails to predict it

800 balanced training rows, 3 epochs, identical budget per candidate, evaluated
on the full 7,490-row dev set. **These numbers rank candidates; they are not
comparable to the full-data results above**, because 800 rows is a fraction of
the training data.

| model | params | Negative-F1 | recall | precision | train s |
|---|---|---|---|---|---|
| **mmbert** | 307M | **0.3268** | 0.888 | 0.200 | 891 |
| xlmr-base | 278M | 0.2343 | 0.897 | 0.135 | 282 |
| twhin-bert | 278M | 0.2235 | 0.771 | 0.131 | 544 |
| indicbert | 278M | 0.2134 | 0.821 | 0.123 | 266 |
| xlmr-large | 560M | 0.2082 | 0.818 | 0.119 | 1263 |
| *tfidf-svm, same 800 rows* | — | *0.2619* | — | — | — |

Classical comparator on the identical subsample and rows: **0.2619, 95% CI
[0.2106, 0.3125]**.

**mmBERT — the candidate with the worst tokenizer fertility — won**, and is the
only one whose point estimate falls outside the classical CI. XLM-R large, the
largest and most expensive model, came last. The fertility ranking predicted
almost the reverse order.

Conclusion: **fertility screens for efficiency and for catastrophic failure
(`[UNK]`), not for downstream accuracy.** It correctly disqualified mBERT and
MuRIL, which genuinely cannot read Sinhala. It had no predictive value at all
for ranking the models that *can*. Do not use it as a proxy for quality again.

Two limits on the mmBERT result:

- Clearing the *classical* CI is weaker than a significance test. A paired test,
  or a CI on mmBERT itself, is needed before calling the gap real.
- Precision is 0.12–0.20 across every encoder against 0.77–0.90 recall. They were
  trained on balanced 400/400 data and evaluated on a 95/5 distribution, which
  shifts the decision boundary hard toward Negative. Threshold tuning should
  recover much of this and must be applied before the next comparison.

`ms_per_sample` in [`encoder_screen_dev.csv`](encoder_screen_dev.csv) (0.24–0.64ms)
is **batched throughput on MPS, not single-request latency** — it is not a valid
check against the 100ms serving budget. Measure batch-size-1 on the target
serving hardware before using it that way.

---

## 7. Correction — retracted by the test set (2026-08-01)

Three claims in the sections above did not survive contact with the held-out test set. Full
working in [`final_test_results.md`](final_test_results.md) and
[`../../notebooks/modeling/10_final_test_eval.ipynb`](../../notebooks/modeling/10_final_test_eval.ipynb).

**§6's threshold tuning is retracted.** It reported tuning worth **+0.027**. Re-derived by 5-fold
CV over train+dev and applied once to test, the champion got **worse**:

| model | default | CV-tuned | Δ on test |
|---|---|---|---|
| `tfidf-svm` / class_weight | **0.4572** | 0.4524 | **−0.0048** |
| `tfidf-logreg` / ros | 0.4225 | 0.4287 | +0.0062 |

The +0.027 was a property of the dev split, not of the method. §6 also used
`tuning._positive_scores`, which min-max normalises the decision function — that scaling is
fit- and dataset-specific, so a threshold chosen on one set means something different on another.
Threshold work should use the raw `decision_function` / `predict_proba`.

**§6's "0.55 is what to expect on unseen data" was optimistic.** Test came in at **0.4572**,
0.095 below the CV estimate. Of the 0.157 dev→test drop, 0.059 is test's lower Negative
prevalence (3.28% vs dev's 4.54%) and **0.098 is genuine generalization loss**.

**§5's priority reasoning was right, for a partly wrong reason.** "Do not fine-tune priority" still
holds, but the binding constraint is not the intent oracle — it is the **label ceiling**. Priority
scores 0.8722 on test against labels that agree with human annotation at only **0.7722**
(κ=0.64). The model has learned the v5 labeling rule better than that rule matches human judgement,
so 0.7722 is the real operational ceiling. Quote it alongside any priority number.

**Also fixed since:** the word tokenizer. `models.py` was using scikit-learn's default
`token_pattern`, which discards **40.1% of Sinhala and 69.3% of Tamil characters**. Every number in
this report predates the fix and is mildly conservative for those two tracks. See
[`../../notebooks/modeling/08_word_tokenizer_comparison.ipynb`](../../notebooks/modeling/08_word_tokenizer_comparison.ipynb).
