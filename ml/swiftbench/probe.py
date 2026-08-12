"""Linear probing: how much task signal is in a backbone *before* fine-tuning.

`train_encoder` answers "how good is this model after we train it on our labels".
This module answers the prior question: how much of that was already there. The
backbone is frozen and never receives a gradient -- one forward pass produces a
fixed sentence vector per row, and a logistic regression on those vectors is the
only thing that trains.

The number that matters is **not** the probe's absolute score. It is the gap
between the probe and the fine-tune of the same model on the same task and split.
A probe that lands near its fine-tune means fine-tuning added little and the
representation already carried the signal; a probe that collapses means the model
genuinely learned the task from our labels. For sentiment specifically that gap is
the difference between a label problem and a modelling problem -- `label_ceiling.csv`
puts v5-vs-human agreement at 0.5769 and the champion fine-tune at 0.566, so
knowing which of the two is binding decides whether the next move is a better
model or a relabel.

Four things this module refuses to get wrong. Every one of them produced a plausible
number before it was caught, and none of them raised anything:

- **Pooling is not one convention across the roster.** LaBSE is trained with a
  dual-encoder objective, so its CLS vector *is* the sentence representation.
  XLM-R's CLS is close to useless unfrozen while its mean-pooled vector is fine.
  Fixing one pooling for everybody would measure "does this model happen to put
  meaning in CLS", not "does it encode sentiment". So every pooling a backbone
  supports is extracted in the same forward pass and probed separately, under its
  own model name, and the notebook picks -- there is no hidden selection in here.
- **Embeddings are L2-normalised per row, then standardised per dimension.** The row
  normalisation is required for the cross-model column to mean anything: Gemma's
  activation scale is nowhere near BERT's, and unnormalised features under one fixed
  `C` would hand each backbone a different effective regularisation strength, leaving
  the table ranking activation norms. The `StandardScaler` after it is required for
  the probe to fit at all -- see `_normalise` for the 0.167-vs-0.807 story.
- **`last` pooling scans the mask from the right, never `mask.sum(1) - 1`.** Gemma's
  tokenizer pads on the *left*, so a count-based index lands inside the padding. It
  read 0.0768 macro-F1 on intent against 0.7990 for the same model's mean pooling --
  low enough to look like a finding about decoders rather than an indexing bug.
- **Cached vectors carry their own `id` array and are asserted against the frame
  they are used with.** A stale cache silently mis-aligns labels to rows and every
  metric downstream stays plausible. See the Indic tokenizer defect in
  `ml/reports/final_test_results.md` for what that class of bug costs.

And one that is not about this module: the fine-tuned checkpoints in
`ml/models/encoders/` were fit on `train+dev`, so probing them and scoring on dev
measures memorised rows. `score()` refuses that combination outright.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import config, data, imbalance, metrics, results, splits
from .train_encoder import DECODERS, ENCODERS, MONOLINGUAL, device

# Extraction writes here; regenerable from the checkpoints, so gitignored.
CACHE_DIR = config.REPO_ROOT / "ml" / "cache" / "embeddings"

# Which pooled vectors each backbone family produces.
#
# `cls` is position 0 of the last hidden state -- for LaBSE that is what the
# translation-ranking objective actually optimised, for an MLM-only encoder it is
# whatever the [CLS] position drifted to.
# `mean` is the attention-masked mean over real tokens, never over padding.
# `last` is the final non-pad token, which is what a causal LM's sequence
# classification head pools. A decoder is causal, so position 0 has seen nothing
# and its mean is dominated by prefix positions with almost no context -- probing
# a decoder on `cls` would measure the wrong thing entirely, which is why the
# decoders get their own pooling rather than being forced into the encoder ones.
ENCODER_POOLINGS = ("cls", "mean")
DECODER_POOLINGS = ("last", "mean")


def poolings_for(model: str) -> tuple[str, ...]:
    return DECODER_POOLINGS if model in DECODERS or model in _FT_DECODERS else ENCODER_POOLINGS


# Backbones that are a local directory rather than a hub id. These are our own
# fine-tuned checkpoints, and probing them against their pretrained counterpart is
# the direct measurement of what fine-tuning put into the representation (rather
# than into the classification head).
#
# `ml/models/encoders/` is gitignored and may not exist on a given machine --
# `resolve()` raises with the regeneration command rather than letting
# `from_pretrained` fail with a hub 404 for a path that was never a hub id.
FINETUNED: dict[str, tuple[str, int]] = {
    "labse-ft-sentiment":       ("ml/models/encoders/sentiment_labse",        128),
    "labse-ft-priority":        ("ml/models/encoders/priority_labse",         128),
    # Registered but deliberately not in ROSTER: two more 1B-scale extractions for
    # a control we only need on one model. Pass them to `sweep()` explicitly.
    "gemma-1b-ft-sentiment":    ("ml/models/encoders/sentiment_gemma-3-1b",   128),
    "gemma-1b-ft-priority":     ("ml/models/encoders/priority_gemma-3-1b",    128),
    "gemma-270m-ft-sentiment":  ("ml/models/encoders/sentiment_gemma-3-270m", 128),
    "gemma-270m-ft-priority":   ("ml/models/encoders/priority_gemma-3-270m",  128),
}

# Which split portions each fine-tuned checkpoint's backbone was trained on. Every
# checkpoint in `ml/models/encoders/` was produced with `--fit-portion train+dev`
# (`ml/models/README.md`), because they were the chosen winners being prepared for a
# single test scoring -- so **dev is inside their training data**.
#
# That makes probing them and scoring on dev meaningless, and not visibly so: the
# first run of this sweep had `labse-ft-priority` probing 0.9645 on dev against its
# own fine-tune's 0.9168, and `labse-ft-sentiment` at 0.6498 against 0.633. Both
# read as "fine-tuning produced a wonderfully linearly-separable representation"
# when they are simply memorised rows. `score()` refuses the combination rather
# than leaving it to whoever reads the table to remember.
FINETUNED_SAW: dict[str, set[str]] = {name: {"train", "dev"} for name in FINETUNED}

# Fine-tuned Gemma checkpoints pool like their base model, not like an encoder. Kept in a set of
# our own rather than added to `train_encoder.DECODERS` -- that set drives dtype pinning and LoRA
# target selection over there, and quietly growing another module's globals from this one is the
# kind of coupling that breaks the next time either file is read in isolation.
_FT_DECODERS = {name for name in FINETUNED if name.startswith("gemma")}

BACKBONES: dict[str, tuple[str, int]] = {**ENCODERS, **FINETUNED}

# The default sweep: every backbone in the fine-tuning roster, so each probe cell has
# a fine-tune cell to be subtracted from. `sinhalaberto` leads because it is the
# smallest and monolingual, so a missing dependency or a broken environment surfaces
# in seconds rather than after an hour of extraction.
ROSTER = ["sinhalaberto", "labse", "xlmr-base", "twhin-bert", "mmbert",
          "canine-c", "sinbert-large", "gemma-3-270m", "gemma-3-1b"]


def resolve(model: str) -> tuple[str, int]:
    """(checkpoint, max_length) for a backbone name. Local paths are made absolute."""
    if model not in BACKBONES:
        raise ValueError(f"unknown backbone {model!r}; expected one of {sorted(BACKBONES)}")
    ref, max_length = BACKBONES[model]
    if model in FINETUNED:
        path = config.REPO_ROOT / ref
        if not path.exists():
            raise FileNotFoundError(
                f"{model!r} expects the fine-tuned checkpoint at {path}, which is not on this "
                f"machine (ml/models/encoders/ is gitignored -- see ml/models/README.md for how "
                f"to regenerate or fetch it)."
            )
        return str(path), max_length
    return ref, max_length


def probe_name(model: str, pooling: str) -> str:
    """The name a probe run is recorded under.

    `results.run_id()` keys on task/model/langs/eval/arm and knows nothing about
    pooling or about probing, so a probe that reused the backbone's own name would
    overwrite that backbone's fine-tune result file. The suffix keeps them apart
    and makes the leaderboard row self-describing.
    """
    return f"{model}-probe-{pooling}"


# ---------------------------------------------------------------------------
# extraction
# ---------------------------------------------------------------------------

def _cache_path(model: str, lang: str, portion: str) -> Path:
    return CACHE_DIR / f"{model}__{lang}__{portion}.npz"


def _pool(hidden, mask, pooling: str):
    """Pool a (batch, tokens, dim) hidden state down to (batch, dim)."""
    import torch

    if pooling == "cls":
        return hidden[:, 0]
    if pooling == "mean":
        m = mask.unsqueeze(-1).to(hidden.dtype)
        return (hidden * m).sum(1) / m.sum(1).clamp(min=1e-9)
    if pooling == "last":
        # Index of the final real token per row, found by scanning the mask from the
        # right. NOT `mask.sum(1) - 1`: that assumes right-padding, and **Gemma's
        # tokenizer pads on the left** (`padding_side='left'`), so the count-based
        # index lands inside the padding block. It cost 0.0768 macro-F1 on intent
        # against 0.7990 for the same model's mean pooling -- a number low enough to
        # look like a genuine finding about decoders rather than an indexing bug.
        # Scanning from the right is correct for either padding side.
        rev = torch.flip(mask, dims=[1])
        idx = mask.size(1) - 1 - rev.float().argmax(dim=1)
        return hidden[torch.arange(hidden.size(0), device=hidden.device), idx.long()]
    raise ValueError(f"unknown pooling {pooling!r}")


def embed(model: str, lang: str, portion: str, batch_size: int = 64,
          max_length: int | None = None, refresh: bool = False,
          verbose: bool = True) -> tuple[dict[str, np.ndarray], np.ndarray]:
    """Pooled vectors for one (backbone, language, portion). Cached on disk.

    Returns `({pooling: (n, dim) float32}, ids)`. Rows are in `splits.get()` order
    and `ids` is that frame's `id` column, so a caller can assert alignment rather
    than assume it.

    Stored as float16: the probe is a linear model on L2-normalised vectors and is
    unaffected by that precision, while the cache for the full roster is ~2 GB
    instead of ~4 GB.
    """
    path = _cache_path(model, lang, portion)
    wanted = poolings_for(model)

    frame = splits.get([lang], portion)
    ids = frame["id"].to_numpy()

    if path.exists() and not refresh:
        with np.load(path) as z:
            fresh = (set(wanted).issubset(z.files)
                     and str(z["split_sha"]) == splits.sha()
                     and len(z["ids"]) == len(ids) and (z["ids"] == ids).all())
            if fresh:
                return {p: z[p].astype(np.float32) for p in wanted}, ids
            # A cache that does not describe the current split is not repairable,
            # only replaceable. Falling through re-extracts rather than returning
            # vectors whose row order no longer matches the frame.
            if verbose:
                print(f"  cache at {path.name} does not match the current split -- re-extracting")

    import torch
    from transformers import AutoModel, AutoTokenizer, DataCollatorWithPadding

    hf_name, default_len = resolve(model)
    max_length = max_length or default_len
    dev = device()

    tokenizer = AutoTokenizer.from_pretrained(hf_name)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    # `AutoModel`, not `AutoModelForSequenceClassification`: we want the backbone's
    # hidden states, and on a fine-tuned checkpoint the classification head is
    # exactly the part we are trying to exclude from the measurement.
    net = AutoModel.from_pretrained(hf_name, dtype=torch.float32).to(dev).eval()

    enc = tokenizer(frame[config.TEXT_COLUMN].tolist(), truncation=True, max_length=max_length)
    collate = DataCollatorWithPadding(tokenizer, return_tensors="pt")

    out: dict[str, list] = {p: [] for p in wanted}
    started = time.time()
    with torch.no_grad():
        for i in range(0, len(ids), batch_size):
            sl = range(i, min(i + batch_size, len(ids)))
            batch = collate([{k: enc[k][j] for k in enc} for j in sl])
            batch = {k: v.to(dev) for k, v in batch.items()}
            hidden = net(**batch).last_hidden_state
            mask = batch.get("attention_mask")
            if mask is None:
                mask = torch.ones(hidden.shape[:2], device=hidden.device)
            for p in wanted:
                out[p].append(_pool(hidden, mask, p).float().cpu().numpy())
            if verbose and i and (i // batch_size) % 50 == 0:
                done = i + len(sl)
                print(f"    {model}/{lang}/{portion}  {done:,}/{len(ids):,} rows "
                      f"({done / max(time.time() - started, 1e-9):.0f}/s)", flush=True)

    vecs = {p: np.concatenate(out[p]) for p in wanted}
    seconds = time.time() - started

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, ids=ids, split_sha=np.array(splits.sha()),
                        **{p: v.astype(np.float16) for p, v in vecs.items()})
    if verbose:
        print(f"  {model}/{lang}/{portion}: {len(ids):,} rows, dim {vecs[wanted[0]].shape[1]}, "
              f"{seconds / 60:.1f} min -> {path.name}")
    return vecs, ids


def features(model: str, langs: list[str], portion: str, pooling: str,
             batch_size: int = 64, refresh: bool = False,
             verbose: bool = True) -> tuple[np.ndarray, pd.DataFrame]:
    """Pooled vectors for several languages, plus the frame they line up with.

    Per-language caches are concatenated in `langs` order, which is the order
    `splits.get()` stacks them in (`data.load_languages` concatenates in list
    order and the id filter preserves the blocks). That is asserted on `id`
    rather than assumed -- if it ever stops holding, every probe score computed
    afterwards would be labels matched to the wrong rows.
    """
    frame = splits.get(langs, portion)
    blocks, id_blocks = [], []
    for lang in langs:
        vecs, ids = embed(model, lang, portion, batch_size=batch_size,
                          refresh=refresh, verbose=verbose)
        blocks.append(vecs[pooling])
        id_blocks.append(ids)
    X = np.concatenate(blocks)

    if len(X) != len(frame):
        raise AssertionError(
            f"{model}/{pooling}: {len(X)} cached vectors against {len(frame)} rows in "
            f"splits.get({langs}, {portion!r})"
        )
    if not (np.concatenate(id_blocks) == frame["id"].to_numpy()).all():
        raise AssertionError(
            f"{model}/{pooling}: cached row order does not match splits.get({langs}, {portion!r}). "
            f"Re-extract with refresh=True."
        )
    return X, frame


def _normalise(X: np.ndarray) -> np.ndarray:
    """L2-normalise rows. See the module docstring -- this is load-bearing.

    Row normalisation alone is not enough to make the probe fit, though. A unit-norm
    row spreads its length over `dim` coordinates, so each feature is O(1/sqrt(dim))
    and the L2 penalty at `C=1` dominates the likelihood from the first step: lbfgs
    hits its gradient tolerance after ~4 iterations and returns an underfit model
    that still reports a plausible-looking score. That is why the estimator below is
    a pipeline with a `StandardScaler` rather than a bare `LogisticRegression` --
    the scaler restores unit per-dimension variance so `C` means what it usually
    means, and it also strips the dominant mean direction that makes raw
    transformer embeddings anisotropic.
    """
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.maximum(norms, 1e-12)


# ---------------------------------------------------------------------------
# probing
# ---------------------------------------------------------------------------

@dataclass
class ProbeFit:
    """A fitted probe plus the identity needed to record any number scored from it.

    Kept separate from scoring so a sweep can fit once per (backbone, pooling) and
    evaluate against six language cells, rather than refitting the same logistic
    regression six times over 42,500 x 768 -- the same reason
    `train_classical.sweep_regimes` reuses its fits.
    """

    estimator: object
    task: str
    model: str
    pooling: str
    train_langs: list[str]
    arm: str
    meta: dict


def fit(task: str = "sentiment", model: str = "labse", pooling: str = "mean",
        train_langs: list[str] | None = None, arm: str = "class_weight",
        fit_portion: str = "train", C: float = 1.0, max_iter: int = 2000,
        batch_size: int = 64, subsample: int | None = None,
        seed: int = config.RANDOM_STATE, refresh: bool = False,
        verbose: bool = True) -> ProbeFit:
    """Fit a logistic regression on `model`'s frozen vectors. No scoring, no saving.

    `arm` defaults to `class_weight` to match the encoder roster in
    `ENCODER_FINDINGS.md` -- a probe scored under a different balancing arm than
    its fine-tune is not a probe-vs-fine-tune comparison.

    `C=1.0` on L2-normalised features is the default rather than a swept value:
    a CV grid over 42,500 x 768 for the 77-way intent task, nine times over, costs
    more than the extraction does. `sweep_C()` exists to check that on one
    model/task instead of assuming it.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    if pooling not in poolings_for(model):
        raise ValueError(
            f"{model!r} does not produce a {pooling!r} vector; it pools "
            f"{poolings_for(model)}. (Decoders pool the last non-pad token, which "
            f"is what their sequence-classification head does.)"
        )
    if arm not in imbalance.ARMS:
        raise ValueError(f"unknown arm {arm!r}; expected one of {imbalance.ARMS}")

    label_col = data.label_column(task)
    train_langs = train_langs or (
        [MONOLINGUAL[model]] if model in MONOLINGUAL else list(config.LANGUAGES)
    )

    if fit_portion == "train+dev":
        # `splits.get` has no "train+dev" portion; the union is the whole on-disk
        # train file, which is what `train_encoder` uses for the same case.
        parts, frames = [], []
        for p in ("train", "dev"):
            Xp, fp = features(model, train_langs, p, pooling, batch_size=batch_size,
                              refresh=refresh, verbose=verbose)
            parts.append(Xp); frames.append(fp)
        X, frame = np.concatenate(parts), pd.concat(frames, ignore_index=True)
    elif fit_portion == "train":
        X, frame = features(model, train_langs, "train", pooling, batch_size=batch_size,
                            refresh=refresh, verbose=verbose)
    else:
        raise ValueError(f"fit_portion must be 'train' or 'train+dev', got {fit_portion!r}")

    if subsample:                                   # smoke tests only
        keep = np.random.default_rng(seed).choice(
            len(frame), min(subsample, len(frame)), replace=False)
        X, frame = X[keep], frame.iloc[keep].reset_index(drop=True)

    n_before = len(frame)
    if arm == "ros":
        # Resample positions, not rows: the frame and the matrix have to move
        # together, and `imbalance.resample` only knows about the frame.
        pos = imbalance.resample(
            frame.assign(_pos=np.arange(len(frame))), label_col, arm
        )["_pos"].to_numpy()
        X, frame = X[pos], frame.iloc[pos].reset_index(drop=True)

    clf = Pipeline([
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(
            C=C, max_iter=max_iter, class_weight=imbalance.class_weight_for(arm),
            solver="lbfgs", random_state=seed,
        )),
    ])
    started = time.time()
    clf.fit(_normalise(X), frame[label_col])
    seconds = time.time() - started

    n_iter = int(np.max(clf["clf"].n_iter_))
    if n_iter >= max_iter:
        # Not fatal, but the score is then a function of the iteration budget rather
        # than of the representation, and it would silently understate the backbone.
        print(f"  warning: {probe_name(model, pooling)}/{task} hit max_iter={max_iter} "
              f"without converging -- raise it before trusting this cell")
    if verbose:
        print(f"  fit {probe_name(model, pooling):26s} {task:9s} "
              f"{len(frame):,} rows x {X.shape[1]} dims  "
              f"{n_iter} iters  [{seconds:.0f}s]")

    return ProbeFit(
        estimator=clf, task=task, model=model, pooling=pooling,
        train_langs=list(train_langs), arm=arm,
        meta={
            "n_train": int(len(frame)), "n_train_before_resample": int(n_before),
            "pooling": pooling, "dim": int(X.shape[1]), "C": float(C),
            "backbone": model, "hf_name": resolve(model)[0],
            "fit_portion": fit_portion, "fit_seconds": round(seconds, 1),
            "n_iter": n_iter, "frozen": True,
        },
    )


def score(pf: ProbeFit, eval_lang: str = "all", portion: str = "dev",
          batch_size: int = 64, author: str = "", save: bool = True,
          refresh: bool = False, verbose: bool = True) -> dict:
    """Score a fitted probe on one evaluation language, and record it."""
    seen = FINETUNED_SAW.get(pf.model)
    if seen and portion in seen:
        raise ValueError(
            f"{pf.model!r} was fine-tuned on {'+'.join(sorted(seen))} "
            f"(ml/models/README.md), so scoring its probe on {portion!r} measures "
            f"memorised rows, not representation quality. Score it on 'test' -- the "
            f"only portion its backbone never saw -- and compare against that "
            f"checkpoint's recorded test number, not its dev number."
        )
    label_col = data.label_column(pf.task)
    eval_langs = list(config.LANGUAGES) if eval_lang == "all" else [eval_lang]
    X, frame = features(pf.model, eval_langs, portion, pf.pooling,
                        batch_size=batch_size, refresh=refresh, verbose=False)

    y_pred = pf.estimator.predict(_normalise(X))
    scores = metrics.score(frame[label_col], y_pred, pf.task)
    scores.update(pf.meta)

    if verbose:
        print(f"{pf.task:9s} {probe_name(pf.model, pf.pooling):26s} arm={pf.arm:12s} "
              f"eval={eval_lang:9s} ({portion}) "
              f"{scores['headline_metric']}={scores['headline']:.4f} "
              f"acc={scores['accuracy']:.4f}")

    if save:
        results.save(pf.task, probe_name(pf.model, pf.pooling), pf.train_langs, eval_lang,
                     pf.arm, portion, scores, author=author,
                     extra={"regime": "multi" if len(pf.train_langs) > 1 else "mono",
                            "family": "probe"})

    scores["_predictions"] = y_pred
    scores["_estimator"] = pf.estimator
    scores["_eval_frame"] = frame
    return scores


def run(task: str = "sentiment", model: str = "labse", pooling: str = "mean",
        train_langs: list[str] | None = None, eval_lang: str = "all",
        arm: str = "class_weight", portion: str = "dev", fit_portion: str = "train",
        C: float = 1.0, max_iter: int = 2000, batch_size: int = 64,
        subsample: int | None = None, seed: int = config.RANDOM_STATE,
        author: str = "", save: bool = True, refresh: bool = False,
        verbose: bool = True) -> dict:
    """One probe end to end: fit on frozen vectors, score on `eval_lang`, record it."""
    pf = fit(task=task, model=model, pooling=pooling, train_langs=train_langs, arm=arm,
             fit_portion=fit_portion, C=C, max_iter=max_iter, batch_size=batch_size,
             subsample=subsample, seed=seed, refresh=refresh, verbose=verbose)
    return score(pf, eval_lang=eval_lang, portion=portion, batch_size=batch_size,
                 author=author, save=save, refresh=refresh, verbose=verbose)


def sweep(task: str = "sentiment", models: list[str] | None = None,
          poolings: list[str] | None = None, eval_langs: list[str] | None = None,
          arm: str = "class_weight", portion: str = "dev", fit_portion: str = "train",
          C: float = 1.0, batch_size: int = 64, author: str = "",
          verbose: bool = True) -> pd.DataFrame:
    """Probe every (backbone x pooling), scored pooled and per language.

    The fit happens once per (backbone, pooling) and is reused across all six
    evaluation cells. A monolingual backbone gets only its own language's cell --
    scoring `sinbert-large` on Tamil would be reporting a number nobody should read.
    """
    models = models or ROSTER
    rows = []
    for model in models:
        cells = ["all"] + list(eval_langs or config.LANGUAGES)
        if model in MONOLINGUAL:
            cells = [MONOLINGUAL[model]]
        for pooling in (poolings or poolings_for(model)):
            if pooling not in poolings_for(model):
                continue
            pf = fit(task=task, model=model, pooling=pooling, arm=arm,
                     fit_portion=fit_portion, C=C, batch_size=batch_size, verbose=verbose)
            for cell in cells:
                sc = score(pf, eval_lang=cell, portion=portion, batch_size=batch_size,
                           author=author, save=True, verbose=verbose and cell == "all")
                rows.append({"model": model, "pooling": pooling, "eval_lang": cell,
                             **{k: v for k, v in sc.items() if not k.startswith("_")}})
    return pd.DataFrame(rows)


def sweep_C(task: str = "sentiment", model: str = "labse", pooling: str = "mean",
            grid: list[float] | None = None, portion: str = "dev",
            arm: str = "class_weight", verbose: bool = True) -> pd.DataFrame:
    """What `C` costs us. Run once, on one model, to justify the default.

    Never saved to `reports/runs/` -- these are tuning rows, and the leaderboard
    must not fill up with variants of one model that differ only in a
    hyperparameter the rest of the roster did not get to tune.
    """
    grid = grid or [0.01, 0.1, 1.0, 10.0, 100.0]
    rows = []
    for C in grid:
        sc = run(task=task, model=model, pooling=pooling, arm=arm, portion=portion,
                 C=C, save=False, verbose=False)
        rows.append({"C": C, "headline": sc["headline"], "accuracy": sc["accuracy"],
                     "macro_f1": sc["macro_f1"], "fit_seconds": sc["fit_seconds"]})
        if verbose:
            print(f"  C={C:<7g} {sc['headline_metric']}={sc['headline']:.4f}")
    return pd.DataFrame(rows)


def deltas(task: str, portion: str = "dev") -> pd.DataFrame:
    """Probe against fine-tune, per backbone -- the table this module exists for.

    Reads both families out of `reports/runs/`, so it only shows backbones that
    have *both* a probe and a fine-tune recorded at the current split sha.
    """
    df = results.load_all(portion)
    if df.empty:
        return df
    df = df[df["task"] == task]
    if df.empty or "family" not in df.columns:
        return pd.DataFrame()

    # `backbone` is a probe-only column, so it is already present on `df` (NaN on the
    # encoder rows). Renaming `model` into it without dropping it first would leave two
    # columns of the same name and the selection below would silently return a frame.
    ft = (df[(df["family"] == "encoder") & (df["eval_lang"] == "all")]
          .drop(columns=["backbone"], errors="ignore")
          .rename(columns={"headline": "finetune", "model": "backbone"})[["backbone", "finetune"]])
    pr = df[(df["family"] == "probe") & (df["eval_lang"] == "all")].copy()
    if pr.empty or ft.empty:
        return pd.DataFrame()

    # Best pooling per backbone, chosen on this portion -- which is dev by default,
    # the portion selection is allowed to happen on.
    pr = (pr.sort_values("headline", ascending=False)
            .groupby("backbone", as_index=False).first()[["backbone", "pooling", "headline"]]
            .rename(columns={"headline": "probe"}))

    # `max` per backbone because LoRA and full fine-tune runs of one model share a
    # run_id (see the note in `train_encoder.run`) -- the best recorded fine-tune is
    # the honest thing to measure a probe against.
    out = pr.merge(ft.groupby("backbone", as_index=False).max(), on="backbone", how="inner")
    out["gap"] = out["finetune"] - out["probe"]
    out["retained"] = out["probe"] / out["finetune"].replace(0, np.nan)
    return out.sort_values("probe", ascending=False).reset_index(drop=True)
