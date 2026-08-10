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

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

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

    # Decoder SLMs (`ml/reports/SLM_RESEARCH.md`). They run through this same function rather than
    # a parallel one: a causal LM with a sequence-classification head is the *same* fit/score loop,
    # and `AutoModelForSequenceClassification` resolves Gemma3ForSequenceClassification for us.
    # Only Gemma 3 is here because only Gemma 3 survived the fertility gate --
    # `ml/reports/slm_tokenizer_fertility.csv` has Qwen3 at 4.3-5.0x LaBSE on Sinhala/Tamil and
    # Llama-3.2 at 5.4-6.2x, against Gemma's 1.6x/1.2x. Do not add those back without new evidence.
    # 128 covers the measured p99 (75 tokens, Sinhala and Tamilish) and matches LaBSE's length, so
    # the comparison is not confounded by one model truncating and the other not.
    # `unsloth/` rather than `google/` because the originals are gated behind a licence click that
    # a Kaggle kernel cannot perform; the vocabularies and weights are identical.
    "gemma-3-1b":    ("unsloth/gemma-3-1b-pt",           128),
    "gemma-3-270m":  ("unsloth/gemma-3-270m",            128),
}

# Causal-LM backbones. Two things differ from an encoder here and both fail silently if missed:
# sequence classification on a decoder pools the **last non-pad token**, so `pad_token_id` has to
# be set on the model config or it pools whatever ends up last; and the attention projections are
# named `q_proj`/`v_proj`, which the encoder LoRA target list does not contain.
DECODERS: set[str] = {"gemma-3-1b", "gemma-3-270m"}

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
    lora_targets: str = "attn",
    save_dir: str | None = None,
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

    `lora_targets` picks which modules get adapters: `"attn"` is Q/V only (the historical default,
    and what the first Gemma intent runs used), `"all"` adds K/O and the MLP projections, which is
    what arXiv:2606.08051's recipe actually specifies. It changes nothing for the encoders, whose
    module names appear in both lists. **A run's `lora_targets` is stamped into its scores**, because
    two runs that differ only in this are not comparable and nothing else in the filename says so.

    `save_dir`, if given, writes the **best epoch's** weights there via `save_pretrained` (the
    tokenizer too) once training finishes. This is opt-in and off by default: the roster runs in
    `notebooks/modeling/11..16_encoder_*.ipynb` compare seven candidates per task and would
    otherwise write seven multi-hundred-MB checkpoints per run for models that are not the
    champion. `lora=True` saves adapter weights only (`peft`'s normal `save_pretrained`
    behaviour), not the merged full model.
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

    # The label space is fixed from the **full** training frame, before any subsampling. Sentiment
    # and priority read theirs from `config`, but intent's 77 classes are derived from the data, and
    # a 1,200-row smoke sample does not contain all 77 -- deriving it after the sample gives a
    # smaller label space than the eval rows use, and the lookup raises on the first unseen intent.
    labels = (
        config.SENTIMENT_LABELS if task == "sentiment"
        else config.PRIORITY_LABELS if task == "priority"
        else sorted(train_df[label_col].unique())
    )

    if subsample:                                   # smoke tests only
        train_df = train_df.sample(min(subsample, len(train_df)), random_state=seed)
        eval_df = eval_df.sample(min(subsample, len(eval_df)), random_state=seed)

    n_before = len(train_df)
    train_df = imbalance.resample(train_df, label_col, arm)

    lut = {l: i for i, l in enumerate(labels)}
    y_train = np.array([lut[v] for v in train_df[label_col]])
    y_eval = np.array([lut[v] for v in eval_df[label_col]])

    tokenizer = AutoTokenizer.from_pretrained(hf_name)
    if tokenizer.pad_token_id is None:          # some causal-LM tokenizers ship without one
        tokenizer.pad_token = tokenizer.eos_token
    enc_train = _encode(tokenizer, train_df[config.TEXT_COLUMN].tolist(), max_length)
    enc_eval = _encode(tokenizer, eval_df[config.TEXT_COLUMN].tolist(), max_length)
    collate = DataCollatorWithPadding(tokenizer, return_tensors="pt")

    def rows(enc, y, idx):
        return collate([{**{k: enc[k][i] for k in enc}, "labels": int(y[i])} for i in idx])

    # ---- model --------------------------------------------------------------
    load_kwargs = {}
    if model in DECODERS:
        # The dtype must be pinned, not inherited: Gemma 3's checkpoints are stored in **bfloat16**
        # and transformers honours the stored dtype, but the T4 is Turing and has no bf16 at all.
        #
        # fp32 rather than fp16, even on CUDA. A half-precision backbone makes the LoRA parameters
        # half-precision too, and `GradScaler.unscale_` refuses fp16 gradients outright
        # ("Attempting to unscale FP16 gradients") -- the master weights an fp16 training step
        # unscales into have to be fp32. Autocast below still runs the matmuls in fp16 on the
        # tensor cores, so the speed is kept; only the stored weights are fp32. At 1B that is 4 GB
        # on a 16 GB card, and with LoRA the optimizer state covers the adapters alone, so the
        # memory this was originally trying to save was never the binding constraint.
        load_kwargs["dtype"] = torch.float32
    net = AutoModelForSequenceClassification.from_pretrained(
        hf_name, num_labels=len(labels), **load_kwargs)
    if net.config.pad_token_id is None:
        # Decoder sequence classification pools the last non-pad token. With pad_token_id unset,
        # transformers cannot find where the real text ends and pools the final padding position
        # instead -- every short row in a batch gets classified from a pad embedding. No error, and
        # the metrics stay plausible, which is exactly the failure mode this project has been bitten
        # by before (see the Indic tokenizer defect in ml/reports/final_test_results.md).
        net.config.pad_token_id = tokenizer.pad_token_id
    # Embed the label order in the config so a saved checkpoint is self-describing. Without this
    # `save_pretrained` writes LABEL_0/LABEL_1 and the mapping survives only in `config.py` --
    # anyone loading the weights later has no way to tell which index means "Negative", and
    # guessing wrong inverts the prediction silently.
    net.config.id2label = {i: l for i, l in enumerate(labels)}
    net.config.label2id = {l: i for i, l in enumerate(labels)}
    if lora:
        # Freeze the backbone, train only low-rank adapters + the classifier head. Target the
        # attention projections, named differently across architectures (BERT/RoBERTa: query/value;
        # CANINE has none of these, so LoRA is not applicable there).
        from peft import LoraConfig, TaskType, get_peft_model

        present = {n.split(".")[-1] for n, _ in net.named_modules()}
        if lora_targets == "attn":
            wanted = ("query", "key", "value", "q_lin", "v_lin", "query_proj", "value_proj",
                      "q_proj", "v_proj")
        elif lora_targets == "all":
            # Every attention *and* MLP projection. arXiv:2606.08051 -- the study the r=8/alpha=16/
            # lr 1e-4 recipe comes from -- adapts "all attention and MLP projection matrices within
            # each transformer block", not just Q/V. On Gemma 3 the attention-only list reaches 2 of
            # the 7 projections (q_proj, v_proj), leaving k_proj, o_proj and the whole MLP stack
            # (gate_proj, up_proj, down_proj) frozen. Encoders are unaffected: they have none of
            # these names, so this resolves to the same modules the attention-only list finds.
            wanted = ("query", "key", "value", "q_lin", "v_lin", "query_proj", "value_proj",
                      "q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",
                      "intermediate.dense", "output.dense")
        else:
            raise ValueError(f"lora_targets must be 'attn' or 'all', got {lora_targets!r}")
        targets = [t for t in wanted if t in present]
        if not targets:
            raise ValueError(f"LoRA: no attention projection modules found in {model!r} to target")
        # The classification head is named `score` on causal-LM backbones and `classifier` on the
        # encoders. Naming the wrong one leaves the head frozen at its random init, and the run
        # trains adapters underneath a head that never learns.
        head = [h for h in ("classifier", "score") if h in present]
        cfg = LoraConfig(task_type=TaskType.SEQ_CLS, r=lora_r, lora_alpha=lora_alpha,
                         lora_dropout=0.05, target_modules=targets,
                         modules_to_save=head)
        net = get_peft_model(net, cfg)
        # Belt and braces for the same failure: whatever dtype the backbone arrived in, anything
        # that will receive a gradient is forced to fp32 so `GradScaler.unscale_` has fp32 master
        # weights to work with. A no-op when the backbone is already fp32.
        for p in net.parameters():
            if p.requires_grad and p.dtype in (torch.float16, torch.bfloat16):
                p.data = p.data.float()
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
    history, best, best_state = [], None, None
    for epoch in range(epochs):
        net.train()
        running, seen = 0.0, 0
        for bi, idx in enumerate(_batches(len(y_train), batch_size, True, rng)):
            batch = {k: v.to(dev_name) for k, v in rows(enc_train, y_train, idx).items()}
            y = batch.pop("labels")
            with torch.autocast("cuda", dtype=torch.float16, enabled=use_amp):
                out = net(**batch)
                # `.float()` so the loss is always computed in fp32. Under CUDA autocast this is
                # already the case, but a half-precision backbone off CUDA hands back half-precision
                # logits that the fp32 class-weight tensor will not multiply against.
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
            if save_dir:
                # Snapshotted to CPU so the next epoch's forward/backward has the GPU memory
                # back -- an on-device copy per epoch would OOM the larger candidates on a T4.
                best_state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}

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
        # LoRA settings belong in the record: the run filename encodes task/model/langs/arm/portion
        # and none of these, so two LoRA configs of the same model write to the *same* path. Without
        # this a rerun is indistinguishable from the run it overwrote.
        "lora": bool(lora),
        **({"lora_r": int(lora_r), "lora_alpha": int(lora_alpha),
            "lora_targets": lora_targets,
            "lora_modules": ",".join(targets)} if lora else {}),
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

    if save_dir:
        net.load_state_dict(best_state)
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)
        net.save_pretrained(out)
        tokenizer.save_pretrained(out)
        # A LoRA save writes `adapter_config.json` and the adapter tensors -- not the base model's
        # `config.json`, which is where `id2label` lives. So the label order does not survive a
        # LoRA checkpoint, and a caller loading it has no way to tell which index means "Negative";
        # guessing wrong inverts predictions with no error. Written explicitly, next to the weights,
        # for every save so the artifact is self-describing either way.
        (out / "label_order.json").write_text(json.dumps({
            "task": task,
            "labels": list(labels),
            "base_model": hf_name,
            "lora": bool(lora),
            "lora_targets": lora_targets if lora else None,
            "split_sha": splits.sha(),
        }, indent=2))
        if verbose:
            print(f"  saved best-epoch ({best_epoch}) weights -> {out}")

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
