"""One classical run: fit on train, score on dev, record the result.

`test` is not reachable from here by accident -- you have to pass
`portion="test"` explicitly, and you should only do that once, at the end, for
a model already chosen on dev.
"""
from __future__ import annotations

import pandas as pd

from . import config, data, imbalance, metrics, models, results, splits


def run(task: str, model: str, train_langs: list[str], eval_lang: str,
        arm: str = "none", portion: str = "dev", author: str = "",
        C: float = 1.0, save: bool = True, verbose: bool = True) -> dict:
    """Fit `model` on `train_langs`, evaluate on `eval_lang`, return the scores."""
    label_col = data.label_column(task)

    train = splits.get(train_langs, "train")
    evaluate = splits.get([eval_lang], portion)

    n_before = len(train)
    train = imbalance.resample(train, label_col, arm)

    clf = models.build(model, class_weight=imbalance.class_weight_for(arm), C=C)
    clf.fit(train[config.TEXT_COLUMN], train[label_col])
    y_pred = clf.predict(evaluate[config.TEXT_COLUMN])

    scores = metrics.score(evaluate[label_col], y_pred, task)
    scores["n_train"] = int(len(train))
    scores["n_train_before_resample"] = int(n_before)

    if verbose:
        print(
            f"{task:9s} {model:13s} arm={arm:12s} "
            f"train={'+'.join(train_langs):20s} eval={eval_lang:9s} ({portion}) "
            f"{scores['headline_metric']}={scores['headline']:.4f} acc={scores['accuracy']:.4f}"
        )

    if save:
        results.save(task, model, train_langs, eval_lang, arm, portion, scores, author=author)

    scores["_predictions"] = y_pred
    scores["_estimator"] = clf
    return scores


def sweep(task: str, langs: list[str] | None = None, model_names: list[str] | None = None,
          arms: list[str] | None = None, portion: str = "dev",
          author: str = "") -> pd.DataFrame:
    """Every (language x model x arm) combination, monolingual, on dev."""
    langs = langs or config.LANGUAGES
    model_names = model_names or models.NAMES
    arms = arms or imbalance.ARMS

    rows = []
    for lang in langs:
        for model in model_names:
            for arm in arms:
                scores = run(task, model, [lang], lang, arm=arm, portion=portion,
                             author=author)
                rows.append(
                    {
                        "regime": "mono", "language": lang, "model": model, "arm": arm,
                        **{k: v for k, v in scores.items() if not k.startswith("_")},
                    }
                )
    return pd.DataFrame(rows)


# The three ways a model can be given its training data. Which one wins is the
# actual deployment question -- one multilingual model or five monolingual ones.
REGIMES = {
    # train on the evaluation language only
    "mono": lambda lang: [lang],
    # one model over all five languages, evaluated per language
    "multi": lambda lang: list(config.LANGUAGES),
    # never sees the evaluation language: measures cross-lingual transfer, and
    # is the only regime that says anything about an unseen sixth language
    "zeroshot-en": lambda lang: ["english"],
}


def sweep_regimes(task: str, model_names: list[str] | None = None,
                  arms: list[str] | None = None, langs: list[str] | None = None,
                  regimes: list[str] | None = None, portion: str = "dev",
                  author: str = "") -> pd.DataFrame:
    """Full bake-off: regime x language x model x arm.

    `multi` and `zeroshot-en` train one model that is then evaluated against
    several languages, so the fit is done once per (train set, model, arm) and
    reused across evaluation languages. Refitting per language would be the same
    model five times over 42,500 rows.
    """
    import time

    model_names = model_names or models.NAMES
    arms = arms or imbalance.ARMS
    langs = langs or config.LANGUAGES
    regimes = regimes or list(REGIMES)
    label_col = data.label_column(task)

    # group evaluation languages by the training set they share
    jobs: dict[tuple[str, tuple[str, ...]], list[str]] = {}
    for regime in regimes:
        for lang in langs:
            if regime == "zeroshot-en" and lang == "english":
                continue  # not zero-shot if it trained on english
            key = (regime, tuple(REGIMES[regime](lang)))
            jobs.setdefault(key, []).append(lang)

    rows = []
    for (regime, train_langs), eval_langs in jobs.items():
        train_full = splits.get(list(train_langs), "train")
        for model in model_names:
            for arm in arms:
                started = time.time()
                train = imbalance.resample(train_full, label_col, arm)
                clf = models.build(model, class_weight=imbalance.class_weight_for(arm))
                clf.fit(train[config.TEXT_COLUMN], train[label_col])
                fit_seconds = time.time() - started

                for lang in eval_langs:
                    evaluate = splits.get([lang], portion)
                    y_pred = clf.predict(evaluate[config.TEXT_COLUMN])
                    scores = metrics.score(evaluate[label_col], y_pred, task)
                    scores["n_train"] = int(len(train))
                    scores["fit_seconds"] = round(fit_seconds, 2)

                    results.save(task, model, list(train_langs), lang, arm,
                                 portion, scores, author=author,
                                 extra={"regime": regime})
                    rows.append({"regime": regime, "language": lang,
                                 "model": model, "arm": arm, **scores})

        print(f"  {regime:12s} train={'+'.join(train_langs)[:28]:28s} "
              f"{len(model_names) * len(arms)} fits -> {len(eval_langs)} eval lang(s)")
    return pd.DataFrame(rows)
