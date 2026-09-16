# Preserved per-epoch training curves

`ml/reports/history_<model>.csv` is written with **one filename per model**, so a later job
for the same model silently overwrites the earlier curve. LaBSE's intent-dev curve was lost
to its sentiment-test run exactly that way, which is why `intent_epochs.pdf` is missing one
of its six models.

These are copies taken 2026-09-08 before the K3 (priority dev) and K6b (intent test) fetches
overwrote them again.

## Naming

`history_<task>-<portion>_<model>_epochs<n>.csv`

**`intent-dev`** — the six-epoch curves are from K2, the only completed six-epoch job at the
time of the snapshot (K1's sentiment-dev curves had already been overwritten by it, and K3
was still running). Attribution is by elimination, not by a stamp in the file.

**`sentiment`** — files carrying a `negative_f1` column, which only the sentiment path writes.

**`unknown-task`** — three-epoch curves from earlier runs whose history format predates the
`negative_f1` column, so the task cannot be recovered from the file. `sinbert-large` and
`sinhalaberto` are almost certainly sentiment (they appear nowhere else), but "almost
certainly" is not a provenance record, so they stay unlabelled.

## Fixed at source

`ml/kaggle/kernels/train_encoders{,_b}.py` now write
`history_{TASK}_{model}_{EVAL_PORTION}.csv`. That takes effect from the next kernel push —
K3 and K6b were already running against the old code, so their curves will still arrive
unqualified and need filing by hand.
