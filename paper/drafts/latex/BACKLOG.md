# What the paper still owes

Restored 2026-09-10 after the 11-page draft was deleted and rewritten to the
ICATC 6-page limit. Compliance items live in `COMPLIANCE.md`; this file is the
research backlog.

## Blocking, before you upload to CMT

**1. Similarity check.** The call desk-rejects above 30%. The manuscript prose is
newly written, but your public dataset and model cards describe this corpus in
overlapping language, and Section III is the most exposed. Check before, not
after.

**2. Set `\draftmodefalse`, export, confirm 6 pages.** The page count is only
valid in clean mode.

**3. Decide the one `\gap` in Section VII.** It is worded as scope rather than as
a hole and is hidden in clean mode, so it is safe to ship as-is. Read it once and
confirm you are happy conceding the disparity result rather than claiming it.

## Reproducibility defects -- both now FIXED

**A. FIXED: `encoder_gain_by_script.py` could not reproduce the paper's
headline.**
`experiments/encoder_gain_by_script.py:57` selects its input by glob:

```python
hits = sorted(PRED_DIR.glob(f"{TASK}__{model}__*__ev-all__*__test.csv"))
df = pd.read_csv(hits[0])
```

Two LaBSE sentiment test prediction files now exist, and sorted, the **seed-43**
file comes first. The stored `encoder_gain_by_script.csv` was seed 42 and correct, which is what
Table III reports, but re-running would have silently recomputed the paper's
central difference-in-differences on different weights.

Fixed: the script now resolves the file for a named seed, defaulting to
`config.RANDOM_STATE`, and exits with the candidate list rather than guessing
when it cannot identify exactly one. Verified after the fix: the default path
reproduces `+0.0698 CI [+0.0140, +0.1283] p=0.0120` and rewrites the stored
table byte-identically. `--seed 43` exits cleanly, because no seed-43 classical
run exists to pair against.

**B. RETRACTED: the tokenizer correlations do reproduce.** I previously recorded
that `results.md` §14's rho = -0.521 / -0.035 did not reproduce, having got
-0.635 / +0.216. That recomputation used the wrong statistic. The generator
computes **Spearman** over the **non-English cells**; I computed Pearson over
every row. On n=20 with a heavily zero-inflated predictor those are different
tests, and they disagree in magnitude and, for fertility, in sign. The published
pair is correct and the paper now quotes it.

The underlying defect was real but different: the coefficients were printed to
stdout and never written to a table, which is what allowed a hand recomputation
to diverge unnoticed. `tokenizer_to_downstream.py` now writes
`tokenizer_correlations_<task>_<portion>.csv` recording the rho, the method, the
scope, and the non-zero cell count, so it cannot be requoted as something else.

Fixing that surfaced a caveat worth keeping: **only 2 of 20 cells have a
non-zero `[UNK]` rate**, so rho = -0.521 is carried by those two. Section VI now
reports the mechanism as a case study and leads on the >10% contrast, which is
what the roster supports.

## A third defect, which the 6-page paper avoids by not citing it

**`per_language.csv` and `main_pooled.csv` disagree for LaBSE sentiment.**
Pooled reports 0.7138 (seed 42, 3 epochs); per-language reports `all = 0.6963`,
which is the seed-43 6-epoch run, because that is the run that wrote per-language
slices. Same model, same task, two tables, two runs, neither labelled with its
seed. The submitted paper cites only the pooled figure and the seed-42 gain
table, so it is unaffected. Any future version quoting per-language sentiment
must resolve this first.

## Corpus facts settled this session

**Tanglish is not a romanization of the Tamil track.** It was translated directly
from the BANKING77 English source (author-confirmed). So `tamil`/`tamilish` are
two independent translations of one English original, not one text in two
scripts, and they are not a script pair. `sinhala`/`singlish` is the only
controlled contrast, since Singlish is a deterministic rule-based romanization of
the Sinhala track.

This explains three things at once that were previously separate puzzles: the
null `tamil - tamilish` difference-in-differences (expected, not a failure to
replicate), Tanglish's 60.3% out-of-vocabulary rate against its own train split,
and its 0.73 loanword retention against Tamil's 0.06. `corpus_stats.py` now
records the corrected provenance.

**Register, measured on all four non-English tracks** (`register_by_track.csv`,
new): sinhala 0.6464, singlish 0.9641, tamil 0.0614, tamilish 0.7288. Only the
two native tracks are comparable, because a romanized track is Latin by
construction and the metric cannot separate a kept English word from a romanized
native borrowing. The native contrast is the meaningful one: Sinhala keeps 65% of
banking terms in English, Tamil 6%.

The paper states this as design intent plus measurement, not as a finding about
the two languages, for two reasons recorded in Section III: Tamil-English
code-mixing is well attested in a work we cite, and only Sinhala received a hand
pass, so register and treatment are confounded in our data.

## For the next version

**1. The cross-script service disparity.** The result that would join Sections VI
and VII by converting the accuracy gap into minutes of customer waiting time.
It needs no GPU. The current bake-off scores against gold priority by design, so
classifier error never enters the queue and no disparity can appear
(`lang_spread_High` reads 0.00--0.09 min). Re-run `policy_bakeoff.py` with the
queue driven by **predicted** priority, reporting **fixed per-track contrasts
against English**, with FIFO and gold-label arms as null controls. Do not report
max-minus-min spread, which is upward-biased and scores 16 min on a policy that
never reads the ticket. `experiments/policy_bakeoff.py:420` is where it goes.

**2. Inter-annotator agreement.** Guidelines written, batches built (200 rows,
all 31 Negatives), `annotation/returned/` empty. The sentiment ceiling is
currently agreement with one annotator over 31 Negative tickets, CI
[0.667, 0.896], and the paper's 90.0%-of-ceiling claim inherits that width.

**3. Simulation parameters from literature.** Arrival rate, service
distribution, agent count, and the 30/120/480 windows are assumed. Published
helpdesk statistics would convert the largest threat to Section VII into a
citation. A reading task.

**4. Runs that close remaining cells.** Multitask Gemma at 6 epochs and matched
batch (the only thing that makes a multitask claim possible); Gemma 3 270M on
sentiment and priority test; per-language priority for LaBSE, XLM-R, and mmBERT
(the second-task script sighting rests on MuRIL alone); seeds 44--46; CANINE at
convergence as the architectural control.

**5. Translation study.** Scoped, sampled, scripted, and it has produced
nothing. It supports none of the four contributions and is not in the paper.
Cut it or run it.

## Repository housekeeping

- **The v8 CSVs are committed.** `paper/TRACKER.md` still lists this as the
  repo's top risk under "Critical", and that entry is stale: commit `7e92966`
  applied the v8 relabel to all five tracks, and `HEAD` and the working tree
  both carry 195 English test Negatives. Delete the stale warning from the
  tracker so it stops costing attention.
- **`paper/drafts/latex/` is untracked.** Commit it.
- **Code has no root LICENSE.** The corpus is settled (CC BY 4.0, inherited from
  BANKING77, not a free choice). MIT recommended for the code.
- **Author list and order** are an assumption, and are needed only for the
  camera-ready.
