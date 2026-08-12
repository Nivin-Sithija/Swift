"""swiftbench — the shared harness for the Swift classifier bake-off.

Several people run experiments from this package on different machines. It
exists so that every run uses the same splits, the same hyperparameters, and
the same result format, and so that everyone's results merge into one
comparison table without anybody having to coordinate.

Typical use:

    from swiftbench import train_classical, baselines, results, splits

    train_classical.run(task="sentiment", model="tfidf-svm",
                        train_langs=["sinhala"], eval_lang="sinhala",
                        arm="ros", author="sithija")

Three things the harness enforces, because getting any of them wrong silently
produces a good-looking number that means nothing:

1. The split is drawn on `id`, once, and fanned out to all five languages --
   the same ticket exists five times and must never straddle train and dev.
2. `dev` is the default evaluation portion. `test` requires asking for it.
3. Sentiment is scored on Negative-class F1, never accuracy (95.6% of tickets
   are Neutral).

Do not edit `config.py` for a single run -- see the note at the top of it.

Submodules are imported on demand rather than eagerly, so that `import
swiftbench` does not drag in scikit-learn for someone who only needs the split
manifest.
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

__all__ = ["baselines", "config", "data", "imbalance", "metrics", "models", "probe",
           "results", "splits", "tokenize", "train_classical", "train_encoder", "tuning"]

if TYPE_CHECKING:  # pragma: no cover
    from . import (baselines, config, data, imbalance, metrics, models, probe,
                   results, splits, tokenize, train_classical, train_encoder, tuning)


def __getattr__(name: str):
    if name in __all__:
        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
