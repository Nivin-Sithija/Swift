# `paper/` — everything the NLP-track paper is built from

One rule: **if the paper cites it, it is generated into this folder by a script in
`experiments/`, never retyped.** A number that exists only in a chat message, a
notebook output cell or someone's memory does not go in the paper.

The full step-by-step plan, with rationale for every task, lives in the build
plan artifact. This file is the folder contract and the status board.

**The paper has two tracks.** The NLP track is the corpus, the roster and the
script/tokenizer findings. The use-case track is the **ticket-ordering system** built on
top of them — design and methodology in `SYSTEM_PLAN.md`, results in `results.md` §17.
A benchmark alone does not tell a support desk which ticket to open next; §17 is what
does.

## Layout

```text
paper/
  experiments/          scripts that generate everything in results/
  results/
    tables/             one file per paper table, generated
    figures/            one file per paper figure, generated
    runs/               the filtered run records the paper roster covers
  notebooks/            analysis that is exploratory, not load-bearing
  translation_eval/     the MT comparison study
    samples/            source rows + the exact prompts sent to each system
    systems/            returned translations, one file per system per language
    ratings/            blind human adequacy/fluency ratings
  annotation/           the inter-annotator agreement study
    guidelines/         written before any annotation happens
    batches/            what each annotator receives
    returned/           what they send back
  bibliography/         refs.bib
  drafts/               the manuscript
```

## Conventions

**Label version.** Every run record written from now on stamps `label_version`.
The sentiment labels on disk are **v8 and final** — nothing in this folder
relabels anything. Older records carry no stamp, which is exactly why v5 and v8
numbers were silently tabled together; treat any unstamped sentiment record as
v5 and out of scope.

**Split.** Frozen split `e7b5934392cd` only — 8,500 / 1,498 / 3,079 per track.
The official-BANKING77-split intent numbers are a separate universe and appear
only in an appendix, framed as external comparability.

**Test discipline.** Test is fit on `train+dev` and scored once. Dev fits on
`train` alone. Any table mixing the two is wrong.

**Provenance.** Every generated table carries the split sha, label version, seed
and generating script in a header comment or a sidecar column.

## Status

| # | Artifact | Produced by | State |
|---|---|---|---|
| 1 | Classical roster, v8, all 3 tasks, pooled + per language, dev + test, bootstrap CIs | `ml/scripts/run_v8_classical.py` | running |
| 2 | Encoder roster, v8, same coverage | Kaggle `runner.py run` | not started |
| 3 | Decoder roster, v8, same coverage | Kaggle `runner.py run --lora` | not started |
| 4 | Seed-variance study (5 seeds, champion + rival) | Kaggle, needs `--seed` flag added | blocked — flag missing |
| 5 | Frozen-split intent for encoders/decoders | Kaggle | not started |
| 6 | Translation comparison sample + prompts | `experiments/build_translation_sample.py` | done |
| 7 | Translation: system outputs | manual — 3 external systems | awaiting user |
| 8 | Translation: blind rating sheets | `experiments/build_rating_sheets.py` | not written |
| 9 | Translation: automatic QE (COMET-Kiwi, LaBSE cosine) | `experiments/score_translations.py` | not written |
| 10 | IAA study: guidelines, batches, κ/α | `experiments/build_annotation_batches.py` | not written |
| 11 | Dedup ablation (train/test text overlap) | `experiments/dedup_ablation.py` | not written |
| 12 | Error analysis tables | `notebooks/` → `results/tables/` | not started |
| 13 | Significance tests between systems | `experiments/significance.py` | not written |
| 14 | Bibliography | manual | 26 entries verified; 6 gap areas open |
| 15 | Posteriors on test (the scoring function's input) | `experiments/save_posteriors.py` | done |
| 16 | TUS ranking, queue simulation, attainment | `experiments/run_system_eval.py` | done |
| 17 | Wait-time disparity by script, with gold-label control | `experiments/run_system_eval.py` | done |
| 18 | Per-language calibration + temperature study | `experiments/calibration.py` | done |
| 19 | System figures (disparity, frontier, attainment) | `experiments/build_figures.py` | done |

## Reproducing

```bash
# 1. classical roster, local, CPU, ~30 min
.venv312/bin/python ml/scripts/run_v8_classical.py

# 2. encoders and decoders, Kaggle T4
.venv312/bin/python ml/kaggle/runner.py sync
.venv312/bin/python ml/kaggle/runner.py run --models labse,xlmr-base,mmbert --task sentiment \
    --fit-portion train+dev --eval-portion test
.venv312/bin/python ml/kaggle/runner.py fetch

# 3. translation study sample
.venv312/bin/python paper/experiments/build_translation_sample.py
```
