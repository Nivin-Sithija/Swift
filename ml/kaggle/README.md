# Running on Kaggle's T4 GPUs from this project

The encoder roster (notebooks 11–16) costs about **12 hours on local MPS** — measured throughput is
24.1 rows/s for `xlm-roberta-base`, so one model at 3 epochs over 42,500 rows is ~88 minutes, and
CANINE is ~4× worse because its sequences are ~4× longer. Kaggle gives two T4s and roughly
30 GPU-hours a week per account.

This directory drives those T4s from here: you edit locally, it executes on Kaggle, results land
back in `ml/reports/runs/` in the same format as every local run.

```text
ml/kaggle/
  runner.py            the local CLI (sync / run / status / fetch / logs)
  kernels/
    train_encoders.py  the job body that executes on Kaggle
  .stage/              generated dataset payload   (gitignored)
  .stage_kernel/       generated kernel + metadata (gitignored)
  .output/             raw fetched output          (gitignored)
```

## Why the Kernels API and not an SSH tunnel

Reverse-tunnelling out of a Kaggle session (ngrok/cloudflared + Remote-SSH) to get an interactive
VS Code window on their hardware **violates Kaggle's Terms of Service**, and accounts are
suspended for it. The Kernels API is the supported path and gets the same outcome: local editing,
remote T4 execution, results back in the repo.

The one thing it costs you is an interactive debugger on the remote machine. `--smoke` covers most
of that — it runs the identical code path on a 1,200-row subsample in a couple of minutes, so
config and import errors surface before you spend an hour of quota.

## Setup (once)

1. **Get a token.** kaggle.com → profile → **Settings** → **API** → *Create New Token*. That
   downloads `kaggle.json`.
2. **Install it:**
   ```bash
   mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/kaggle.json
   chmod 600 ~/.kaggle/kaggle.json
   ```
3. **Verify:**
   ```bash
   .venv312/bin/python ml/kaggle/runner.py doctor
   ```
4. **Enable GPU on your account** if you have not: Kaggle requires phone verification before
   `enable_gpu` works. Without it the kernel runs on CPU and takes ~20× longer, silently.

## The loop

```bash
# 1. upload code + data as a private Kaggle Dataset (~20 MB). Re-run whenever either changes.
.venv312/bin/python ml/kaggle/runner.py sync

# 2. smoke first -- same code path, 1,200 rows, ~2 min. Catches import and config errors cheaply.
.venv312/bin/python ml/kaggle/runner.py run --models xlmr-base --smoke

# 3. the real run
.venv312/bin/python ml/kaggle/runner.py run --models xlmr-base,mmbert,labse --epochs 3

# 4. poll (or --watch to block)
.venv312/bin/python ml/kaggle/runner.py status --watch

# 5. pull results into ml/reports/runs/, then rank them
.venv312/bin/python ml/kaggle/runner.py fetch
```

Then open [`../../notebooks/modeling/30_leaderboard.ipynb`](../../notebooks/modeling/30_leaderboard.ipynb) —
fetched runs merge with local ones automatically, because every result file stamps the split sha
and `results.load_all()` drops anything recorded against a different one.

From VS Code, the same steps are in the Command Palette under **Tasks: Run Task** → `Kaggle: …`.

## Splitting the roster across sessions

Kaggle caps a kernel at **12 hours** and GPU quota is weekly, so run the roster in batches rather
than one job:

| batch | models | rough T4 cost |
|---|---|---|
| 1 | `xlmr-base,labse` | ~1.5 h |
| 2 | `mmbert` | ~1.5 h |
| 3 | `canine-c` | ~3 h (4× sequence length) |
| 4 | `sinbert-large,sinhalaberto` | ~0.5 h (Sinhala track only) |

Each batch writes its own run JSONs, so a failed batch never costs you the earlier ones — and the
job body catches per-model exceptions so one bad checkpoint does not end the session.

## Things that will bite you

- **`sync` is not instant.** Kaggle processes the dataset for a minute or two after upload. A
  kernel pushed immediately can attach the *previous* version. Check the dataset page before
  running if you just changed data.
- **T4 is Turing: fp16 yes, bf16 no.** `train_encoder.run()` enables fp16 autocast automatically on
  CUDA and leaves MPS in fp32. Do not force bf16; it fails or silently falls back.
- **`enable_internet` is on** because the job pulls checkpoints from Hugging Face. Kaggle requires
  a phone-verified account for internet access in kernels.
- **`/kaggle/input` is read-only.** The job copies the payload to `/kaggle/working/repo` and points
  `SWIFT_REPO_ROOT` there, because `results.save()` writes under the repo root.
- **Results are only comparable if the split sha matches.** `sync` ships
  `ml/splits/split_manifest.json`, so it does — but if you ever regenerate the split locally,
  re-`sync` before running or the fetched results will be dropped on load.
