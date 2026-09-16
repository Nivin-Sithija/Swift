"""Joint multi-task fine-tuning: one Gemma-3 backbone serving intent, sentiment, and priority.

`RESULTS.md` open item #8: single-task LoRA adapters per task were measured (§14) -- a genuinely
*joint* multi-task fine-tune, and a shared base with per-task adapters, were not. This module
builds the joint side. The per-task-adapter side needs no new code: it is `train_encoder.run()`
called three times with `lora=True`, one call per task, sharing the same frozen base checkpoint.

Two variants, because "one model" is ambiguous and the ambiguity is worth measuring rather than
picking:

- `run_shared_heads()` -- **one** LoRA adapter, **three** task-specific classification heads,
  trained jointly. Every ticket in this dataset already carries all three labels (intent,
  sentiment, priority, on the same `text`), so this is a single forward pass per batch with three
  losses summed -- true hard parameter sharing, not three separate training runs glued together.
- `run_shared_head()` -- **one** LoRA adapter, **one** classification head over the union label
  space (77 intent + 2 sentiment + 3 priority = 82 classes), task identity given only as a text
  prefix. Each ticket becomes three training rows (one per task). This is the more literal "one
  model, one head" reading, and arXiv:2512.12677 (`SLM_RESEARCH.md` §1) found this style needs 8x
  the trainable params of an embedding head for equal F1 -- a weaker prior, kept anyway because it
  is the more literal interpretation of the request and worth measuring, not assuming.

Both are decoder-only and both reuse `train_encoder.py`'s hard-won integration fixes rather than
re-deriving them: fp32 master weights under fp16 autocast (Gemma ships bf16 checkpoints, the T4 has
no bf16 at all), `pad_token_id` resolved explicitly before pooling, LoRA over all attention *and*
MLP projections (Q/V-only cost 2.7-4.6pp in §14.2), id2label / label_order stamped at save time.

`run_shared_heads()` cannot reuse `AutoModelForSequenceClassification` -- HF's decoder
classification wrapper supports exactly one head. Its pooling (last non-pad token, robust to either
padding side) is copied verbatim from `transformers.modeling_layers.GenericForSequenceClassification`
rather than re-derived, because a plausible-looking re-derivation (`mask.sum(1)-1`) is exactly the
bug `linear-probe-findings` hit on Gemma's left padding. `run_shared_head()` needs no custom
pooling: it stays on the stock `AutoModelForSequenceClassification` path, just fed a pre-built,
task-prefixed frame over the union label space.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, data, metrics, results, splits
from . import train_encoder as te

TASKS = ["intent", "sentiment", "priority"]


def _task_labels(train_df: pd.DataFrame) -> dict[str, list[str]]:
    return {
        "intent": sorted(train_df[data.label_column("intent")].unique()),
        "sentiment": list(config.SENTIMENT_LABELS),
        "priority": list(config.PRIORITY_LABELS),
    }


def _class_weight(y: np.ndarray, n_labels: int):
    import torch

    counts = np.bincount(y, minlength=n_labels).astype(float)
    return torch.tensor(len(y) / (n_labels * np.maximum(counts, 1)), dtype=torch.float32)


def _pool_last_token(hidden_states, input_ids, pad_token_id: int):
    """Last non-pad token per row, robust to either padding side.

    Verbatim from `transformers.modeling_layers.GenericForSequenceClassification.forward` (the
    class every `*ForSequenceClassification` decoder in this repo's roster inherits from), applied
    to hidden states instead of post-head logits. Selecting a row then applying a linear head is
    the same operation as applying the head to every row then selecting -- Linear commutes with
    row selection -- so this is exactly HF's own pooling, not a re-derivation of it.
    """
    import torch

    non_pad = (input_ids != pad_token_id).to(hidden_states.device, torch.int32)
    idx = torch.arange(input_ids.shape[-1], device=hidden_states.device, dtype=torch.int32)
    last = (idx * non_pad).argmax(-1)
    return hidden_states[torch.arange(input_ids.shape[0], device=hidden_states.device), last]


def _lora_backbone(hf_name: str, lora_r: int, lora_alpha: int, lora_targets: str):
    """Bare decoder body (no task head), LoRA over all attention+MLP projections. See
    `train_encoder.run()`'s docstring for why `lora_targets='all'` matters on Gemma 3."""
    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModel

    net = AutoModel.from_pretrained(hf_name, dtype=torch.float32)
    present = {n.split(".")[-1] for n, _ in net.named_modules()}
    wanted = {
        "attn": ("q_proj", "v_proj"),
        "all": ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"),
    }[lora_targets]
    targets = [t for t in wanted if t in present]
    if not targets:
        raise ValueError(f"LoRA: no attention projection modules found in {hf_name!r}")
    cfg = LoraConfig(task_type=TaskType.FEATURE_EXTRACTION, r=lora_r, lora_alpha=lora_alpha,
                     lora_dropout=0.05, target_modules=targets)
    net = get_peft_model(net, cfg)
    for p in net.parameters():
        if p.requires_grad and p.dtype in (torch.float16, torch.bfloat16):
            p.data = p.data.float()
    return net


@dataclass
class MultiTaskRun:
    scores: dict[str, dict]                 # per task
    history: pd.DataFrame
    predictions: dict[str, np.ndarray]       # per task
    eval_frame: pd.DataFrame
    label_order: dict[str, list[str]]
    seconds: float = 0.0


# ============================================================== variant A
def run_shared_heads(
    model: str = "gemma-3-1b",
    train_langs: list[str] | None = None,
    eval_lang: str = "all",
    portion: str = "dev",
    fit_portion: str = "train",
    epochs: int = 3,
    batch_size: int = 16,
    lr: float = 1e-4,
    warmup_frac: float = 0.1,
    max_length: int | None = None,
    subsample: int | None = None,
    seed: int = config.RANDOM_STATE,
    author: str = "",
    save: bool = True,
    verbose: bool = True,
    fp16: bool | None = None,
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_targets: str = "all",
    save_dir: str | None = None,
) -> MultiTaskRun:
    """One LoRA adapter, three heads, trained jointly on the shared ticket text.

    Every row already carries an intent, a sentiment and a priority label, so one batch produces
    one shared pooled representation and three losses (summed, unweighted -- each task's own
    class-weighting already corrects for its internal imbalance; weighting *between* tasks would
    need a criterion this project has no basis for yet). "Best epoch" is picked by the sum of the
    three headline metrics, because all three heads share one adapter -- unlike per-task runs,
    there is no way to keep a different epoch's weights per task.
    """
    import torch
    from torch.utils.data import DataLoader  # noqa: F401  (kept for parity with train_encoder.py)
    from transformers import AutoTokenizer, DataCollatorWithPadding

    if model not in te.DECODERS:
        raise ValueError(f"run_shared_heads is decoder-only; got {model!r}, expected one of {sorted(te.DECODERS)}")
    hf_name, default_len = te.ENCODERS[model]
    max_length = max_length or default_len
    train_langs = train_langs or list(config.LANGUAGES)
    dev_name = te.device()
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)

    if fit_portion == "train+dev":
        train_df = data.load_languages(train_langs, "train")
    elif fit_portion == "train":
        train_df = splits.get(train_langs, "train")
    else:
        raise ValueError(f"fit_portion must be 'train' or 'train+dev', got {fit_portion!r}")
    eval_langs = list(config.LANGUAGES) if eval_lang == "all" else [eval_lang]
    select_on_eval = portion == "dev"
    eval_df = splits.get(eval_langs, portion)

    label_lists = _task_labels(train_df)
    luts = {t: {l: i for i, l in enumerate(label_lists[t])} for t in TASKS}
    col = {t: data.label_column(t) for t in TASKS}

    if subsample:
        train_df = train_df.sample(min(subsample, len(train_df)), random_state=seed)
        eval_df = eval_df.sample(min(subsample, len(eval_df)), random_state=seed)

    y_train = {t: np.array([luts[t][v] for v in train_df[col[t]]]) for t in TASKS}
    y_eval = {t: np.array([luts[t][v] for v in eval_df[col[t]]]) for t in TASKS}

    tokenizer = AutoTokenizer.from_pretrained(hf_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    enc_train = tokenizer(train_df[config.TEXT_COLUMN].tolist(), truncation=True, max_length=max_length)
    enc_eval = tokenizer(eval_df[config.TEXT_COLUMN].tolist(), truncation=True, max_length=max_length)
    collate = DataCollatorWithPadding(tokenizer, return_tensors="pt")

    def rows(enc, idx):
        return collate([{k: enc[k][i] for k in enc} for i in idx])

    net = _lora_backbone(hf_name, lora_r, lora_alpha, lora_targets)
    if net.config.pad_token_id is None:
        net.config.pad_token_id = tokenizer.pad_token_id
    pad_id = tokenizer.pad_token_id
    hidden_size = getattr(net.config, "hidden_size", None) or net.config.get_text_config().hidden_size
    heads = torch.nn.ModuleDict({t: torch.nn.Linear(hidden_size, len(label_lists[t])) for t in TASKS})
    net.to(dev_name); heads.to(dev_name)
    if verbose:
        net.print_trainable_parameters()

    loss_fns = {t: torch.nn.CrossEntropyLoss(weight=_class_weight(y_train[t], len(label_lists[t])).to(dev_name))
                for t in TASKS}

    params = [p for p in net.parameters() if p.requires_grad] + list(heads.parameters())
    steps = int(np.ceil(len(train_df) / batch_size)) * epochs
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps,
                                                pct_start=warmup_frac, anneal_strategy="linear")
    use_amp = (dev_name == "cuda") if fp16 is None else (fp16 and dev_name == "cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    if verbose:
        print(f"{model} multitask-3head ({hf_name})  device={dev_name}  max_length={max_length}  fp16={use_amp}")
        print(f"  train {len(train_df):,} rows (shared across intent/sentiment/priority)   "
              f"eval {len(eval_df):,} rows   {steps:,} steps")

    def forward_batch(idx_batch, enc):
        batch = {k: v.to(dev_name) for k, v in rows(enc, idx_batch).items()}
        with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
            hidden = net(input_ids=batch["input_ids"],
                        attention_mask=batch["attention_mask"]).last_hidden_state
            pooled = _pool_last_token(hidden, batch["input_ids"], pad_id)
            logits = {t: heads[t](pooled.float()) for t in TASKS}
        return logits

    started = time.time()
    history, best, best_state = [], None, None
    n = len(train_df)
    for epoch in range(epochs):
        net.train(); heads.train()
        running, seen = 0.0, 0
        order = rng.permutation(n)
        for bi in range(0, n, batch_size):
            idx = order[bi:bi + batch_size]
            logits = forward_batch(idx, enc_train)
            loss = sum(loss_fns[t](logits[t].float(), torch.tensor(y_train[t][idx], device=dev_name))
                      for t in TASKS)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            scaler.step(opt); scaler.update()
            sched.step(); opt.zero_grad(set_to_none=True)
            running += float(loss) * len(idx); seen += len(idx)
            if verbose and (bi // batch_size) % 100 == 0:
                print(f"    epoch {epoch+1}/{epochs}  step {bi // batch_size:5d}  "
                      f"loss {running/max(seen,1):.4f}", flush=True)

        net.eval(); heads.eval()
        preds, task_scores = {}, {}
        with torch.no_grad():
            all_logits = {t: [] for t in TASKS}
            for bi in range(0, len(eval_df), batch_size):
                idx = np.arange(bi, min(bi + batch_size, len(eval_df)))
                logits = forward_batch(idx, enc_eval)
                for t in TASKS:
                    all_logits[t].append(logits[t].float().cpu().numpy())
        combined = 0.0
        for t in TASKS:
            lg = np.concatenate(all_logits[t])
            pred = np.array(label_lists[t])[lg.argmax(1)]
            preds[t] = pred
            sc = metrics.score(eval_df[col[t]].to_numpy(), pred, t)
            task_scores[t] = sc
            combined += sc["headline"]

        history.append({"epoch": epoch + 1, "train_loss": running / max(seen, 1),
                        "combined_headline": combined,
                        **{f"{t}_{sc['headline_metric']}": task_scores[t]["headline"] for t, sc in
                            [(t, task_scores[t]) for t in TASKS]}})
        if verbose:
            print(f"  epoch {epoch+1}: loss {history[-1]['train_loss']:.4f}  combined {combined:.4f}  "
                  f"intent {task_scores['intent']['macro_f1']:.4f}  "
                  f"sentiment {task_scores['sentiment']['negative_f1']:.4f}  "
                  f"priority {task_scores['priority']['macro_f1']:.4f}", flush=True)
        # Only a dev run may pick its best epoch. On a test run `eval_df` IS the test
        # set, so selecting on `combined` makes all three reported task numbers a
        # maximum over `epochs` draws rather than held-out estimates -- and here the
        # selection is on a combined metric, so one task's noise moves the other two.
        # Test reports its final epoch; `epochs` is what dev already chose.
        take = (combined > best[0]) if (best is not None and select_on_eval) else \
               (best is None or not select_on_eval)
        if take:
            best = (combined, epoch + 1, task_scores, preds)
            if save_dir:
                best_state = {
                    "net": {k: v.detach().cpu().clone() for k, v in net.state_dict().items()},
                    "heads": {k: v.detach().cpu().clone() for k, v in heads.state_dict().items()},
                }

    seconds = time.time() - started
    combined_best, best_epoch, task_scores, preds = best
    for t in TASKS:
        task_scores[t] = dict(task_scores[t])
        task_scores[t].update({
            "n_train": int(len(train_df)), "best_epoch": int(best_epoch), "epochs": int(epochs),
            "lr": lr, "batch_size": int(batch_size), "max_length": int(max_length),
            "train_seconds": round(seconds, 1), "hf_name": hf_name, "lora": True,
            "lora_r": int(lora_r), "lora_alpha": int(lora_alpha), "lora_targets": lora_targets,
            "fit_portion": fit_portion, "device": dev_name, "fp16": bool(use_amp),
            "epoch_selection": "best-on-dev" if select_on_eval else "final-epoch",
            "combined_headline_all_tasks": float(combined_best),
        })
        if verbose:
            print(f"  [{t}] best epoch {best_epoch}: {task_scores[t]['headline_metric']} "
                  f"{task_scores[t]['headline']:.4f}")
        if save:
            results.save(t, f"{model}-multitask-shared3head", train_langs, eval_lang, "class_weight",
                        portion, task_scores[t], author=author,
                        extra={"family": "slm-multitask", "variant": "shared-adapter-3-heads",
                               "regime": "multi" if len(train_langs) > 1 else "mono"})

    if save_dir:
        net.load_state_dict(best_state["net"])
        heads.load_state_dict(best_state["heads"])
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)
        net.save_pretrained(out)                       # adapter_config.json + adapter weights
        tokenizer.save_pretrained(out)
        import torch as _torch
        _torch.save(heads.state_dict(), out / "heads.pt")
        (out / "label_order.json").write_text(json.dumps({
            "variant": "shared-adapter-3-heads", "base_model": hf_name,
            "labels": label_lists, "lora_targets": lora_targets, "split_sha": splits.sha(),
        }, indent=2))
        if verbose:
            print(f"  saved best-epoch ({best_epoch}) weights -> {out}")

    return MultiTaskRun(scores=task_scores, history=pd.DataFrame(history), predictions=preds,
                        eval_frame=eval_df, label_order=label_lists, seconds=seconds)


# ============================================================== variant B
_PREFIX = {"intent": "[INTENT]", "sentiment": "[SENTIMENT]", "priority": "[PRIORITY]"}


def _coerce_to_task_vocabulary(y_true: np.ndarray, y_pred: np.ndarray,
                               task_labels: list[str]) -> np.ndarray:
    """Map any prediction outside `task_labels` to a deterministic miss.

    `run_shared_head` deliberately does not mask logits to the current task's label subset (see
    its docstring), so a prediction can legitimately be a label string that belongs to a *different*
    task -- e.g. a sentiment row predicted as the intent class `card_arrival`. `metrics.score`'s
    sentiment path calls sklearn with `average="binary"`, which raises if the array holds more than
    two distinct values, regardless of `labels=`. An out-of-vocabulary prediction is already wrong
    by construction, so it is remapped to a fixed in-vocabulary label guaranteed to differ from the
    true label -- not to the true label itself, which would silently manufacture a correct answer
    out of a wrong-task prediction.
    """
    valid = set(task_labels)
    out = y_pred.copy()
    for i, (t, p) in enumerate(zip(y_true, y_pred)):
        if p not in valid:
            out[i] = task_labels[0] if t != task_labels[0] else task_labels[1]
    return out


def _prefixed_frame(df: pd.DataFrame, union_labels: list[str]) -> pd.DataFrame:
    """One ticket -> three rows, one per task, text prefixed with the task and label mapped into
    the union space. Kept as a plain function (not inlined) because both fit and eval need it."""
    lut = {l: i for i, l in enumerate(union_labels)}
    parts = []
    for t in TASKS:
        col = data.label_column(t)
        sub = df[[config.TEXT_COLUMN, col, "language"]].copy()
        sub["_task"] = t
        sub["_text"] = _PREFIX[t] + " " + sub[config.TEXT_COLUMN]
        sub["_label"] = [lut[v] for v in sub[col]]
        parts.append(sub)
    return pd.concat(parts, ignore_index=True)


def run_shared_head(
    model: str = "gemma-3-1b",
    train_langs: list[str] | None = None,
    eval_lang: str = "all",
    portion: str = "dev",
    fit_portion: str = "train",
    epochs: int = 3,
    batch_size: int = 16,
    lr: float = 1e-4,
    warmup_frac: float = 0.1,
    max_length: int | None = None,
    subsample: int | None = None,
    seed: int = config.RANDOM_STATE,
    author: str = "",
    save: bool = True,
    verbose: bool = True,
    fp16: bool | None = None,
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_targets: str = "all",
    save_dir: str | None = None,
) -> MultiTaskRun:
    """One LoRA adapter, one head over the union label space, task given as a text prefix.

    No masking at eval: the head sees the full 82-way space and its argmax is scored as-is. Masking
    to the current task's label subset would hand-hold the comparison and answer a different, easier
    question ("can it classify within a task it's told the shape of") than the one this variant
    exists to ask ("does a text prefix alone carry enough task identity"). Stays on the stock
    `AutoModelForSequenceClassification` path -- HF's own last-non-pad-token pooling handles the
    single head correctly, so nothing here needs the custom pooling `run_shared_heads()` does.
    """
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding

    if model not in te.DECODERS:
        raise ValueError(f"run_shared_head is decoder-only; got {model!r}, expected one of {sorted(te.DECODERS)}")
    hf_name, default_len = te.ENCODERS[model]
    max_length = max_length or default_len
    train_langs = train_langs or list(config.LANGUAGES)
    dev_name = te.device()
    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)

    if fit_portion == "train+dev":
        base_train = data.load_languages(train_langs, "train")
    elif fit_portion == "train":
        base_train = splits.get(train_langs, "train")
    else:
        raise ValueError(f"fit_portion must be 'train' or 'train+dev', got {fit_portion!r}")
    eval_langs = list(config.LANGUAGES) if eval_lang == "all" else [eval_lang]
    select_on_eval = portion == "dev"
    base_eval = splits.get(eval_langs, portion)

    label_lists = _task_labels(base_train)
    union_labels = label_lists["intent"] + label_lists["sentiment"] + label_lists["priority"]
    dupes = {l for l in union_labels if union_labels.count(l) > 1}
    if dupes:
        raise ValueError(f"union label space has collisions across tasks: {dupes}")

    if subsample:
        base_train = base_train.sample(min(subsample, len(base_train)), random_state=seed)
        base_eval = base_eval.sample(min(subsample, len(base_eval)), random_state=seed)

    train_df = _prefixed_frame(base_train, union_labels)
    eval_df = _prefixed_frame(base_eval, union_labels)
    y_train = train_df["_label"].to_numpy()
    y_eval = eval_df["_label"].to_numpy()

    tokenizer = AutoTokenizer.from_pretrained(hf_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    enc_train = tokenizer(train_df["_text"].tolist(), truncation=True, max_length=max_length)
    enc_eval = tokenizer(eval_df["_text"].tolist(), truncation=True, max_length=max_length)
    collate = DataCollatorWithPadding(tokenizer, return_tensors="pt")

    def rows(enc, y, idx):
        return collate([{**{k: enc[k][i] for k in enc}, "labels": int(y[i])} for i in idx])

    from peft import LoraConfig, TaskType, get_peft_model

    net = AutoModelForSequenceClassification.from_pretrained(hf_name, dtype=torch.float32,
                                                              num_labels=len(union_labels))
    if net.config.pad_token_id is None:
        net.config.pad_token_id = tokenizer.pad_token_id
    net.config.id2label = {i: l for i, l in enumerate(union_labels)}
    net.config.label2id = {l: i for i, l in enumerate(union_labels)}

    present = {n.split(".")[-1] for n, _ in net.named_modules()}
    wanted = {
        "attn": ("q_proj", "v_proj"),
        "all": ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"),
    }[lora_targets]
    targets = [t for t in wanted if t in present]
    cfg = LoraConfig(task_type=TaskType.SEQ_CLS, r=lora_r, lora_alpha=lora_alpha,
                     lora_dropout=0.05, target_modules=targets, modules_to_save=["score"])
    net = get_peft_model(net, cfg)
    for p in net.parameters():
        if p.requires_grad and p.dtype in (torch.float16, torch.bfloat16):
            p.data = p.data.float()
    net.to(dev_name)
    if verbose:
        net.print_trainable_parameters()

    w = _class_weight(y_train, len(union_labels)).to(dev_name)
    loss_fn = torch.nn.CrossEntropyLoss(weight=w)
    steps = int(np.ceil(len(y_train) / batch_size)) * epochs
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps,
                                                pct_start=warmup_frac, anneal_strategy="linear")
    use_amp = (dev_name == "cuda") if fp16 is None else (fp16 and dev_name == "cuda")
    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    if verbose:
        print(f"{model} multitask-sharedhead ({hf_name})  device={dev_name}  max_length={max_length}  "
              f"fp16={use_amp}  union_labels={len(union_labels)}")
        print(f"  train {len(y_train):,} rows (3x {len(base_train):,} tickets)   "
              f"eval {len(y_eval):,} rows   {steps:,} steps")

    started = time.time()
    history, best, best_state = [], None, None
    for epoch in range(epochs):
        net.train()
        running, seen = 0.0, 0
        for bi, idx in enumerate(np.array_split(rng.permutation(len(y_train)),
                                                max(1, len(y_train) // batch_size))):
            if len(idx) == 0:
                continue
            batch = {k: v.to(dev_name) for k, v in rows(enc_train, y_train, idx).items()}
            y = batch.pop("labels")
            with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
                out = net(**batch)
                loss = loss_fn(out.logits.float(), y)
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0)
            scaler.step(opt); scaler.update()
            sched.step(); opt.zero_grad(set_to_none=True)
            running += float(loss) * len(idx); seen += len(idx)
            if verbose and bi % 100 == 0:
                print(f"    epoch {epoch+1}/{epochs}  step {bi:5d}  loss {running/max(seen,1):.4f}",
                      flush=True)

        net.eval()
        logits_all = []
        with torch.no_grad():
            for i in range(0, len(y_eval), batch_size):
                idx = np.arange(i, min(i + batch_size, len(y_eval)))
                batch = {k: v.to(dev_name) for k, v in rows(enc_eval, y_eval, idx).items()}
                batch.pop("labels")
                with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
                    lg = net(**batch).logits
                logits_all.append(lg.float().cpu().numpy())
        logits = np.concatenate(logits_all)
        pred_global = np.array(union_labels)[logits.argmax(1)]

        combined, task_scores, preds = 0.0, {}, {}
        for t in TASKS:
            mask = eval_df["_task"] == t
            sub_true = eval_df.loc[mask, data.label_column(t)].to_numpy()
            raw_pred = pred_global[mask.to_numpy()]
            # Whether the prefix alone steers the head into the right task's region of the union
            # space is the actual question this variant asks -- worth recording even though the
            # scored prediction below coerces a miss so `metrics.score` does not crash on it.
            off_task_rate = float(np.mean([p not in set(label_lists[t]) for p in raw_pred]))
            sub_pred = _coerce_to_task_vocabulary(sub_true, raw_pred, label_lists[t])
            sc = metrics.score(sub_true, sub_pred, t)
            sc["off_task_prediction_rate"] = off_task_rate
            task_scores[t] = sc
            preds[t] = sub_pred
            combined += sc["headline"]

        history.append({"epoch": epoch + 1, "train_loss": running / max(seen, 1),
                        "combined_headline": combined,
                        **{f"{t}_{task_scores[t]['headline_metric']}": task_scores[t]["headline"]
                            for t in TASKS}})
        if verbose:
            print(f"  epoch {epoch+1}: loss {history[-1]['train_loss']:.4f}  combined {combined:.4f}  "
                  f"intent {task_scores['intent']['macro_f1']:.4f}  "
                  f"sentiment {task_scores['sentiment']['negative_f1']:.4f}  "
                  f"priority {task_scores['priority']['macro_f1']:.4f}", flush=True)
        # Only a dev run may pick its best epoch. On a test run `eval_df` IS the test
        # set, so selecting on `combined` makes all three reported task numbers a
        # maximum over `epochs` draws rather than held-out estimates -- and here the
        # selection is on a combined metric, so one task's noise moves the other two.
        # Test reports its final epoch; `epochs` is what dev already chose.
        take = (combined > best[0]) if (best is not None and select_on_eval) else \
               (best is None or not select_on_eval)
        if take:
            best = (combined, epoch + 1, task_scores, preds)
            if save_dir:
                best_state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}

    seconds = time.time() - started
    combined_best, best_epoch, task_scores, preds = best
    for t in TASKS:
        task_scores[t] = dict(task_scores[t])
        task_scores[t].update({
            "n_train": int(len(y_train)), "best_epoch": int(best_epoch), "epochs": int(epochs),
            "lr": lr, "batch_size": int(batch_size), "max_length": int(max_length),
            "train_seconds": round(seconds, 1), "hf_name": hf_name, "lora": True,
            "lora_r": int(lora_r), "lora_alpha": int(lora_alpha), "lora_targets": lora_targets,
            "fit_portion": fit_portion, "device": dev_name, "fp16": bool(use_amp),
            "epoch_selection": "best-on-dev" if select_on_eval else "final-epoch",
            "combined_headline_all_tasks": float(combined_best), "union_label_count": len(union_labels),
        })
        if verbose:
            print(f"  [{t}] best epoch {best_epoch}: {task_scores[t]['headline_metric']} "
                  f"{task_scores[t]['headline']:.4f}")
        if save:
            results.save(t, f"{model}-multitask-sharedhead", train_langs, eval_lang, "class_weight",
                        portion, task_scores[t], author=author,
                        extra={"family": "slm-multitask", "variant": "shared-adapter-shared-head",
                               "regime": "multi" if len(train_langs) > 1 else "mono"})

    if save_dir:
        net.load_state_dict(best_state)
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)
        net.save_pretrained(out)
        tokenizer.save_pretrained(out)
        (out / "label_order.json").write_text(json.dumps({
            "variant": "shared-adapter-shared-head", "base_model": hf_name,
            "union_labels": union_labels, "task_prefixes": _PREFIX,
            "lora_targets": lora_targets, "split_sha": splits.sha(),
        }, indent=2))
        if verbose:
            print(f"  saved best-epoch ({best_epoch}) weights -> {out}")

    return MultiTaskRun(scores=task_scores, history=pd.DataFrame(history), predictions=preds,
                        eval_frame=eval_df, label_order={"union": union_labels}, seconds=seconds)
