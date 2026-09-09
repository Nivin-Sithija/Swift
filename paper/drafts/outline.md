# Draft outline — every claim mapped to the artifact that proves it

**Rule this file enforces:** no sentence enters the manuscript unless this table names the
generated file its number comes from. A number that exists only in `results.md` prose, a
chat message, or memory does not go in the paper.

Status: **skeleton, no prose written yet.** Tracker task D6. Results first, abstract last.

Target: a conference with an NLP track and a use-case / industry track. Sections 1–5 are the
NLP contribution, 6–8 the use-case contribution, and §7 is the join.

---

## Title & framing

Working title: *From Classifiers to Queues: Multilingual Support-Ticket Triage for Sinhala,
Tamil and English, and What Script Coverage Costs a Customer*

**The one-sentence thesis.** Multilingual pretraining transfers across languages it has
seen but not across scripts it has not, and that gap is invisible in an F1 table and
measurable in minutes of customer waiting time once you build the queue.

**What makes this not a benchmark paper:** §6–8. The classifiers are the input layer.

---

## 1. Introduction

| claim | evidence | source |
|---|---|---|
| Triage is a queue problem, not only a labelling problem | — | framing |
| Prior deployed triage work stops at the per-ticket label | `montgomery2018escalation`, `mani2019deeptriage`, `lee2017industrialtriage` | refs.bib |
| Sri Lankan banking support is trilingual and heavily romanized | corpus motivation | §2 |

Contributions, in the order the paper earns them: **C1** corpus · **C2** script-not-language
finding + tokenizer mechanism · **C3** the ordering system and its evaluation methodology ·
**C4** script-based service disparity in minutes · **C5** accuracy does not transfer to the
queue.

## 2. The corpus

| claim | number | source |
|---|---|---|
| 13,077 tickets × 5 tracks = 65,385 rows | — | `split_sizes.csv`, `corpus_composition.csv` |
| Frozen split `e7b5934392cd`, drawn on `id` then fanned | 8,500 / 1,498 / 3,079 | `split_sizes.csv` |
| Label provenance differs by column | intent = BANKING77 human gold; sentiment/priority LLM | `label_ceiling.csv` |
| **Ceilings** | sentiment 0.7931, priority 0.7722 | `label_ceiling.csv`, Fig. `label_ceiling` |
| Romanized tracks are synthetic — results are an optimistic bound | Singlish OOV 1.18% ≈ English | `corpus_stats.py`; contrast with `chakravarthi2020tamilmix` (human-typed) |
| Train/test text overlap does not drive results | max shift −0.0047, inside CIs | `dedup_ablation.csv`, `dedup_overlap.csv` |
| **⚠ Tamilish test rendering is defective** | 60.3% OOV vs train | `results.md` §18.2 — **must be stated here, not only in results** |

## 3. Experimental setup

Frozen split · v8 labels (final) · dev for all selection, test scored once · identical budget
· every record stamped with split sha, label version, seed, epoch-selection rule.

Metrics: intent macro-F1 (77 classes) · sentiment **Negative-F1** (never accuracy — 94%
Neutral) · priority macro-F1.

Inference: paired bootstrap 1,000 resamples · exact McNemar · difference-in-differences for
script contrasts · `gelman2006significant` for why we never compare two p-values.

## 4. Roster results

| claim | number | source |
|---|---|---|
| Pooled leaderboard, all tasks | — | `main_pooled.csv/.md` |
| Per-language breakdown | — | `per_language.csv/.md` |
| Balancing arms | — | `balancing_arms.csv` |
| Coverage of the run matrix | 701 dev / 217 test records | `coverage.csv/.md` |
| Sentiment test: LaBSE 0.7138, 90% of the 0.7931 ceiling | +0.0485 over classical, CI [+0.0257,+0.0721] | `significance.csv`, §15 |
| Intent test: LaBSE 88.35 > XLM-R 88.01 > mmBERT 86.80 | Δ(LaBSE−mmBERT) +0.0155, McNemar 7.8e-13 | `significance.csv`, §18.1 |
| Priority dev: roster flat, 2.1 pts across six models | LaBSE 91.67 … MuRIL 89.57 | §19 |

## 5. It is script, not language *(the NLP contribution)*

| claim | number | source |
|---|---|---|
| Encoder gain confined to native script | english +0.0834, sinhala +0.0822; singlish +0.0124 n.s., tamilish +0.0225 n.s. | `encoder_gain_by_script.csv`, Fig. `encoder_gain_by_script` |
| Tested as a difference-in-differences | sinhala−singlish +0.0698, CI [+0.0140,+0.1283], p=0.012 | `encoder_gain_by_script.csv` |
| **Second sighting, between two encoders** | LaBSE−mmBERT significant on sinhala/tamil, **n.s. on english and singlish** | §18.1 |
| Mechanism is `[UNK]`, not fertility | MuRIL 64.5% `[UNK]` on Sinhala, 0.0% elsewhere; ρ=−0.521 vs −0.035 | `tokenizer_to_downstream_sentiment_dev.csv`, Fig. `tokenizer_to_downstream` |
| Confirmed on a second task | MuRIL priority sinhala 83.13 vs its own english 92.23 | §19 |
| Coarser label spaces tolerate more input destruction | ~14 pts on intent vs ~9 on priority | §19 |
| `clark2022canine` is the design that cannot have this failure | — | refs.bib |

**Caveat that must appear here:** §16's tamil−tamilish DiD was already n.s., so the §18.2
defect manufactured no positive result. Say it, don't let a reviewer find it.

## 6. The ordering system *(C3)*

| claim | number | source |
|---|---|---|
| TUS definition | `w=(0.80,0.10,0.10), α=16` | `tus_weights.csv` |
| Weights fitted on dev, applied unchanged to test | fit on train-only TF-IDF dev posteriors | `tus_weight_surface.csv` |
| **Surface is flat — the vector is not the finding** | 71/231 points within 5%, `w_P∈[0.10,0.90]` | `tus_weight_surface.csv` |
| Positioning: a c-μ rule with a *learned* cost term | — | `cox1961queues` |
| Attainment vs a perfect classifier | 0.971 / 0.985 / 0.990 across ρ | `tus_attainment.csv`, Fig. `attainment` |
| **Rank correlation is the wrong metric** | argmax-tier τ=0.822 (best) but P(High)@10 = 0.50 (worst) | `tus_ranking.csv` |
| nDCG is the right family | — | `jarvelin2002ndcg` |
| Aging is a dial, not a constant | α frontier; grid extended to 128 to show a plateau | `tus_alpha_frontier.csv`, Fig. `alpha_frontier` |
| Signal ablation | sentiment adds little once intent is in | `tus_ablation.csv` |
| Objective design matters | population-weighted tardiness selected a degenerate scorer | `results.md` §17.7, `pinedo2022scheduling` |

## 7. Script-based service disparity *(C4 — the join, and the headline)*

| claim | number | source |
|---|---|---|
| Null under FIFO | all four contrasts straddle zero | `tus_disparity.csv` |
| Null under gold-label control | ≈0.00 all tracks | `tus_disparity.csv` |
| **Significant only on romanized tracks** | singlish **+4.07** [2.96,5.21]; tamilish +6.99; sinhala/tamil n.s. | `tus_disparity.csv`, Fig. `queue_disparity` |
| TUS cuts it ~10× | singlish +0.37, tamilish +0.50 (both still ≠0) | `tus_disparity.csv` |
| Paired reduction | −3.70 min singlish, −6.49 min tamilish | `tus_disparity.csv` |
| **Independent of the defective track** | singlish carries it alone, ordinary OOV profile | §17.4 |
| Framing vs fairness-in-ranking | groups are *customers*, currency is waiting time not exposure | `singh2018fairexposure` |

## 8. Accuracy does not transfer to the queue *(C5)*

| claim | number | source |
|---|---|---|
| Swapping LaBSE→TF-IDF changes little, sign varies | mean 1.98→1.80, p95 5.32→5.42 | `tus_classifier_substitution.csv` |
| Separation is in the tail | worst-case wait **362 vs 98 min** | `tus_classifier_substitution.csv` |
| **Buried urgent tickets** — a metric F1 cannot see | LaBSE 68 vs TF-IDF 8, on *fewer* misses (165 vs 193) | `tus_classifier_substitution.csv` |
| Calibration diagnosis | LaBSE priority ECE 0.0658 vs 0.0180; worst on tamilish 0.1071 | `calibration.csv`, `guo2017calibration` |
| **Refuted hypothesis, kept visible** | temperature scaling fixed ECE and made the queue worse | `calibration_queue_effect.csv` |
| Deployment recommendation | the cheapest classifier, consumed properly, serves this queue as well as the best | `results.md` §17.10 |

## 9. Related work

Six areas already sourced (refs.bib): BANKING77/intent · multilingual encoders ·
code-mixed & romanized Indic · Sinhala/Tamil resources · MT quality estimation · evaluation
methodology. Four added for this paper: ranking & calibration metrics · queueing and
scheduling · fairness in ranking · label noise and annotation ceilings. `northcutt2021labelerrors`
is the closest prior work to the ceiling claim and belongs in the **introduction**, not
buried here.

## 10. Limitations

Every one of these is already measured or documented; none is a hedge.

1. Simulation parameters (λ, service distribution, agent count) are **assumed** — the
   largest threat. Mitigated by the load sweep and by attainment. Tracker E10.
2. Romanized tracks are synthetic → the disparity is an **optimistic lower bound**.
3. Tamilish test rendering is defective (§18.2) → excluded from load-bearing claims.
4. Sentiment/priority labels are LLM-generated; ceilings reported everywhere.
5. Single seed, no variance estimate (A6).
6. §17.6's temperature result is cross-fitted on test halves, not held out (E6b running).
7. Label ceiling rests on **one annotator and 31 Negatives** (C2).

---

## Blocking gaps before submission

| # | gap | owner | blocks |
|---|---|---|---|
| 1 | Two annotators × 200 rows (C2) | `you` | the ceiling's CI, §2 and §10 |
| 2 | Translation comparison outputs (B2) | `you` | a whole planned section — **cut it or run it** |
| 3 | "Manually verified" reconciliation (B5) | `you` | §2 methods |
| 4 | Author order and family-name assumption | `you` | title page |
| 5 | Seed variance (A6) | Kaggle | §10.5 |
| 6 | Decoder roster (A5) | Kaggle | §4 completeness, `gemma3` citation |
| 7 | Helpdesk arrival/service parameters from literature (E10) | `you` | §10.1, the biggest single win available |

**Note on B2.** The translation comparison is scoped, sampled and scripted but has produced
nothing, and it is the only planned section with no results at all. It is not needed for any
of C1–C5. Decide early whether the paper claims it — carrying a dead section into drafting
costs more than dropping it.
