"""Estimator factory.

The TF-IDF feature union deliberately matches the one in
`ml/scripts/train_baseline.py` (word 1-2 grams + char_wb 3-5 grams) so that
sentiment and priority numbers sit on the same feature basis as the existing
77-way intent baselines and the three tasks stay comparable.

char_wb matters more here than it looks: Singlish and Tanglish are romanised
with no spelling standard, so `card eka` / `kaard eka` / `card-ai` only share
signal at the character level.
"""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from . import config
from .tokenize import tokenize as word_tokenize

NAMES = ["tfidf-logreg", "tfidf-svm", "tfidf-sgd", "tfidf-cnb"]

# ComplementNB ignores class_weight and sample duplication is the only lever
# that reaches it, so its `class_weight` arm is identical to `none`. Kept in the
# roster anyway: it is the standard strong baseline for imbalanced text and it
# fits in a second, which makes it a useful sanity check on the linear models.


def feature_union() -> FeatureUnion:
    return FeatureUnion(
        [
            (
                "word_tfidf",
                # `tokenizer=word_tokenize` rather than the default token_pattern: the default
                # drops Unicode combining marks and so discards 40% of Sinhala and 69% of Tamil
                # characters. See `tokenize.py` and `08_word_tokenizer_comparison.ipynb`.
                TfidfVectorizer(
                    analyzer="word", ngram_range=(1, 2), min_df=2, max_df=0.98,
                    sublinear_tf=True, max_features=25_000,
                    tokenizer=word_tokenize, token_pattern=None,
                ),
            ),
            (
                "char_tfidf",
                TfidfVectorizer(
                    analyzer="char_wb", ngram_range=(3, 5), min_df=2,
                    sublinear_tf=True, max_features=50_000,
                ),
            ),
        ]
    )


def build(name: str, class_weight=None, C: float = 1.0) -> Pipeline:
    if name == "tfidf-logreg":
        clf = LogisticRegression(
            C=C, max_iter=1000, class_weight=class_weight,
            solver="lbfgs", random_state=config.RANDOM_STATE,
        )
    elif name == "tfidf-svm":
        clf = LinearSVC(
            C=C, class_weight=class_weight, dual="auto", max_iter=5000,
            random_state=config.RANDOM_STATE,
        )
    elif name == "tfidf-sgd":
        # modified_huber keeps predict_proba available, which matters if a
        # decision threshold ever gets tuned on the Negative class.
        clf = SGDClassifier(
            loss="modified_huber", alpha=1e-5, max_iter=3000, tol=1e-4,
            class_weight=class_weight, random_state=config.RANDOM_STATE,
        )
    elif name == "tfidf-cnb":
        clf = ComplementNB(alpha=0.3)
    else:
        raise ValueError(f"unknown model {name!r}; expected one of {NAMES}")

    return Pipeline([("features", feature_union()), ("classifier", clf)])
