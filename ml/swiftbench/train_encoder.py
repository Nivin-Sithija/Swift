"""One encoder fine-tuning run: fit, score, record -- the mirror of `train_classical`.

Six candidate encoders are benchmarked in `notebooks/modeling/11..16_encoder_*.ipynb`, one
notebook each. They all call `run()` from here rather than carrying their own training loop,
for the same reason `train_classical` exists: three people on three machines have to produce
numbers that sit in one table, and six copies of a training loop drift within a week.

Two things this module refuses to get wrong, because both are silent:

- **The split comes from `swiftbench.splits`**, drawn on ticket `id`. `ml/scripts/train_transformer.py`
  builds its validation split with `train_test_split` over pooled five-language rows, so a
  ticket's English copy trains while its Sinhala copy validates. That inflates validation
  scores and cannot be detected from the metrics.
- **Selection is on `negative_f1`, never loss or accuracy.** At 95.5% Neutral a model that
  predicts Neutral for everything reaches ~0.956 accuracy and a falling eval loss while
  catching zero angry customers.

A plain PyTorch loop is used rather than `transformers.Trainer` -- the loop is ~60 lines, the
per-epoch progress is legible in a notebook, and it does not move under us across transformers
releases.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config, data, imbalance, metrics, results, splits

# name -> (hf checkpoint, max_length). Lengths are the p99 tokenised length measured per
# tokenizer in `07_encoder_bakeoff.ipynb`, rounded up -- not a shared guess.
#
# CANINE is character-level, so its "tokens" are Unicode codepoints and its length is ~4x the
# subword models'. That is inherent to the architecture, not a misconfiguration.
ENCODERS: dict[str, tuple[str, int]] = {
    "xlmr-base":     ("FacebookAI/xlm-roberta-base",     128),
    "mmbert":        ("jhu-clsp/mmBERT-base",            160),
    "labse":         ("sentence-transformers/LaBSE",     128),
    "canine-c":      ("google/canine-c",                 512),
    "sinbert-large": ("NLPC-UOM/SinBERT-large",          256),
    "sinhalaberto":  ("keshan/SinhalaBERTo",             256),
    # Code-mix-aware. model-research.md §5 names TwHIN-BERT as the "process romanized directly"
    # (Strategy B) model -- Twitter multilingual, trained on the code-switched register.
    "twhin-bert":    ("Twitter/twhin-bert-base",         128),
}

# Sinhala-only checkpoints. Serving them the other four language tracks is not a fair test of
# the model, so the notebooks train them on `sinhala` alone and compare against the
# multilingual models' sinhala cell.
MONOLINGUAL: dict[str, str] = {"sinbert-large": "sinhala", "sinhalaberto": "sinhala"}


def device() -> str:
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@dataclass
class EncoderRun:
    """Everything a notebook needs after a run, without re-deriving it."""

    scores: dict
    history: pd.DataFrame
    predictions: np.ndarray
    scores_positive: np.ndarray          # raw P(Negative) / logit margin, for threshold work
    eval_frame: pd.DataFrame
    label_order: list[str] = field(default_factory=list)
    seconds: float = 0.0


def _encode(tokenizer, texts: list[str], max_length: int):
    return tokenizer(texts, truncation=True, max_length=max_length)


def _batches(n: int, size: int, shuffle: bool, rng):
    idx = rng.permutation(n) if shuffle else np.arange(n)
    for i in range(0, n, size):
        yield idx[i : i + size]


def run(
    task: str = "sentiment",
    model: str = "xlmr-base",
    train_langs: list[str] | None = None,
    eval_lang: str = "all",
    arm: str = "class_weight",
    portion: str = "dev",
    fit_portion: str = "train",
    epochs: int = 3,
    batch_size: int = 32,
    lr: float = 2e-5,
    warmup_frac: float = 0.1,
    max_length: int | None = None,
    subsample: int | None = None,
    seed: int = config.RANDOM_STATE,
    author: str = "",
    save: bool = True,
    verbose: bool = True,
    fp16: bool | None = None,
    lora: bool = False,
    lora_r: int = 8,
    lora_alpha: int = 16,
) -> EncoderRun:
    """Fine-tune `model` on `train_langs`, score on `eval_lang`/`portion`.

    `fit_portion` is "train" (8,500 ids -- use while selecting) or "train+dev" (9,998 ids --
    only for a model already chosen, immediately before scoring test).
    `arm` is the class-balancing arm: "class_weight" weights the loss, "ros" oversamples rows,
    "none" does neither. No SMOTE arm -- see `imbalance`.

    `fp16` defaults to on for CUDA and off elsewhere. Kaggle's T4s are Turing, which has fp16
    tensor cores but **no bf16** -- asking for bf16 there fails or silently falls back. MPS is
    left in fp32 because its autocast support is not worth the risk for a ~2x that does not
    materialise on this model size.
    """
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding

    if model not in ENCODERS:
        raise ValueError(f"unknown encoder {model!r}; expected one of {sorted(ENCODERS)}")
    if arm not in imbalance.ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {imbalance.ARMS}")

    hf_name, default_len = ENCODERS[model]
    max_length = max_length or default_len
    train_langs = train_langs or (
        [MONOLINGUAL[model]] if model in MONOLINGUAL else list(config.LANGUAGES)
    )
    label_col = data.label_column(task)
    dev_name = device()
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)

    # ---- data ---------------------------------------------------------------
    if fit_portion == "train+dev":
        train_df = data.load_languages(train_langs, "train")
    elif fit_portion == "train":
        train_df = splits.get(train_langs, "train")
    else:
        raise ValueError(f"fit_portion must be 'train' or 'train+dev', got {fit_portion!r}")

    eval_langs = list(config.LANGUAGES) if eval_lang == "all" else [eval_lang]
    eval_df = splits.get(eval_langs, portion)

    if subsample:                                   # smoke tests only
        train_df = train_df.sample(min(subsample, len(train_df)), random_state=seed)
        eval_df = eval_df.sample(min(subsample, len(eval_df)), random_state=seed)

    n_before = len(train_df)
    train_df = imbalance.resample(train_df, label_col, arm)

    labels = (
        config.SENTIMENT_LABELS if task == "sentiment"
        else config.PRIORITY_LABELS if task == "priority"
        else sorted(train_df[label_col].unique())
    )
    lut = {l: i for i, l in enumerate(labels)}
    y_train = np.array([lut[v] for v in train_df[label_col]])
    y_eval = np.array([lut[v] for v in eval_df[label_col]])

    tokenizer = AutoTokenizer.from_pretrained(hf_name)
    enc_train = _encode(tokenizer, train_df[config.TEXT_COLUMN].tolist(), max_length)
    enc_eval = _encode(tokenizer, eval_df[config.TEXT_COLUMN].tolist(), max_length)
    collate = DataCollatorWithPadding(tokenizer, return_tensors="pt")

    def rows(enc, y, idx):
        return collate([{**{k: enc[k][i] for k in enc}, "labels": int(y[i])} for i in idx])

    # ---- model --------------------------------------------------------------
    net = AutoModelForSequenceClassification.from_pretrained(hf_name, num_labels=len(labels))
    if lora:
        # Freeze the backbone, train only low-rank adapters + the classifier head. Target the
        # attention projections, named differently across architectures (BERT/RoBERTa: query/value;
        # CANINE has none of these, so LoRA is not applicable there).
        from peft import LoraConfig, TaskType, get_peft_model

        present = {n.split(".")[-1] for n, _ in net.named_modules()}
        targets = [t for t in ("query", "key", "value", "q_lin", "v_lin", "query_proj", "value_proj")
                   if t in present]
        if not targets:
            raise ValueError(f"LoRA: no attention projection modules found in {model!r} to target")
        cfg = LoraConfig(task_type=TaskType.SEQ_CLS, r=lora_r, lora_alpha=lora_alpha,
                         lora_dropout=0.05, target_modules=targets,
                         modules_to_save=["classifier"])
        net = get_peft_model(net, cfg)
        if verbose:
            net.print_trainable_parameters()
    net.to(dev_name)

    if arm == "class_weight":
        counts = np.bincount(y_train, minlength=len(labels)).astype(float)
        w = torch.tensor(len(y_train) / (len(labels) * np.maximum(counts, 1)), dtype=torch.float32)
    else:
        w = torch.ones(len(labels), dtype=torch.float32)
    loss_fn = torch.nn.CrossEntropyLoss(weight=w.to(dev_name))

    steps = int(np.ceil(len(y_train) / batch_size)) * epochs
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(
        opt, max_lr=lr, total_steps=steps, pct_start=warmup_frac, anneal_strategy="linear"
    )

    use_amp = (dev_name == "cuda") if fp16 is None else (fp16 and dev_name == "cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    if verbose:
        print(f"{model} ({hf_name})  device={dev_name}  max_length={max_length}"
              f"  fp16={use_amp}")
        print(f"  train {len(y_train):,} rows (was {n_before:,}, arm={arm})   "
              f"eval {len(y_eval):,} rows   {steps:,} steps")

    # ---- train --------------------------------------------------------------
    started = time.time()
    history, best = [], None
    for epoch in range(epochs):
        net.train()
        running, seen = 0.0, 0
        for bi, idx in enumerate(_batches(len(y_train), batch_size, True, rng)):
            batch = {k: v.to(dev_name) for k, v in rows(enc_train, y_train, idx).items()}
            y = batch.pop("labels")
            with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
                out = net(**batch)
                loss = loss_fn(out.logits, y)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            scaler.step(opt); scaler.update()
            sched.step(); opt.zero_grad(set_to_none=True)
            running += float(loss) * len(idx); seen += len(idx)
            if verbose and bi % 100 == 0:
                print(f"    epoch {epoch+1}/{epochs}  step {bi:5d}  loss {running/max(seen,1):.4f}",
                      flush=True)

        logits = _infer(net, enc_eval, y_eval, batch_size, dev_name, rows, use_amp)
        pred = np.array(labels)[logits.argmax(1)]
        sc = metrics.score(eval_df[label_col].to_numpy(), pred, task)
        history.append({"epoch": epoch + 1, "train_loss": running / max(seen, 1),
                        **{k: v for k, v in sc.items() if not isinstance(v, str)}})
        if verbose:
            print(f"  epoch {epoch+1}: train_loss {history[-1]['train_loss']:.4f}  "
                  f"{sc['headline_metric']} {sc['headline']:.4f}  acc {sc['accuracy']:.4f}",
                  flush=True)
        # select on the headline metric, never on loss
        if best is None or sc["headline"] > best[0]:
            best = (sc["headline"], epoch + 1, sc, pred, logits)

    seconds = time.time() - started
    _, best_epoch, scores, pred, logits = best

    # raw positive-class score, for threshold tuning downstream
    if task == "sentiment":
        e = np.exp(logits - logits.max(1, keepdims=True))
        pos = (e / e.sum(1, keepdims=True))[:, labels.index(config.SENTIMENT_POSITIVE_CLASS)]
    else:
        pos = logits.max(1)

    scores = dict(scores)
    scores.update({
        "n_train": int(len(y_train)), "n_train_before_resample": int(n_before),
        "best_epoch": int(best_epoch), "epochs": int(epochs), "lr": lr,
        "batch_size": int(batch_size), "max_length": int(max_length),
        "train_seconds": round(seconds, 1), "hf_name": hf_name,
        "fit_portion": fit_portion, "device": dev_name, "fp16": bool(use_amp),
        "rows_per_second": round(len(y_train) * epochs / max(seconds, 1e-9), 1),
    })

    if verbose:
        print(f"  best epoch {best_epoch}: {scores['headline_metric']} {scores['headline']:.4f}"
              f"   [{seconds/60:.1f} min]")

    if save:
        results.save(task, model, train_langs, eval_lang, arm, portion, scores,
                     author=author, extra={"regime": "multi" if len(train_langs) > 1 else "mono",
                                           "family": "encoder"})

    return EncoderRun(scores=scores, history=pd.DataFrame(history), predictions=pred,
                      scores_positive=pos, eval_frame=eval_df, label_order=list(labels),
                      seconds=seconds)


def _infer(net, enc, y, batch_size, dev_name, rows, use_amp=False) -> np.ndarray:
    import torch

    net.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(y), batch_size):
            idx = np.arange(i, min(i + batch_size, len(y)))
            batch = {k: v.to(dev_name) for k, v in rows(enc, y, idx).items()}
            batch.pop("labels")
            with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
                logits = net(**batch).logits
            out.append(logits.float().cpu().numpy())
    return np.concatenate(out)
