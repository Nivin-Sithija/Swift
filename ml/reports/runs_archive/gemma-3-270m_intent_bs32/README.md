# gemma-3-270m, intent test, batch 32 -- archived before the batch-8 rerun

The run id does not encode batch size, so re-running the same model/task/split at a
different batch size overwrites the record in place. These are the batch-32 files,
kept so the overwrite is recoverable and so both points remain quotable.

    macro_f1 0.8304788870896211   epochs 6   batch_size 32   lr 1e-4   LoRA all r=8

Why the rerun: gemma-3-1b's intent test record is at batch 8 (batch 32 OOM'd on a T4),
while this one was at batch 32. That makes the 1B-vs-270M gap a mixture of parameter
count and a 4x batch-size difference, which is not a scaling result. Re-running the
270M at batch 8 matches every other hyperparameter (6 epochs, lr 1e-4, LoRA all,
r=8/alpha=16, fit train+dev) and leaves parameter count as the only difference.
