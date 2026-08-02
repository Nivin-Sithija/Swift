"""Word tokenization that does not destroy Sinhala and Tamil.

scikit-learn's default `token_pattern=r"(?u)\\b\\w\\w+\\b"` matches `\\w`, which excludes Unicode
categories `Mn`/`Mc` -- every Sinhala and Tamil vowel sign. Measured on the dev split, the default
**discards 40.1% of Sinhala characters and 69.3% of Tamil characters**:

    කවුරු හරි මගේ කාඩ් එක පාවිච්චි   ->  ['කව', 'හර', 'මග', 'එක']       ("paavichchi" vanishes)
    இது மற்றும் கவலை உதவி           ->  ['இத', 'மற', 'கவல', 'உதவ']

Words differing only in vowel signs collapse onto the same token, so the word-level features for
two of the five language tracks have been partly noise.

**Why indic-nlp-library and not a regex.** The obvious fix, `regex` with `[\\p{L}\\p{M}\\p{N}]+`,
recovers the vowel signs but still splits on **ZWJ (U+200D)**, the zero-width joiner that forms
Sinhala conjuncts -- it breaks `ට්‍රැක්` ("track", a high-frequency banking term here) into
`ට්` + `රැක්`. That is the exact ZWJ gotcha `research/README.md` §3.19.3 flags as recurring across
Sinhala tooling. Measured agreement with indic-nlp on dev: Tamil 99.5%, Sinhala **92.4%**, and
every Sinhala disagreement is a ZWJ conjunct.

`indic_nlp_library` (Kunchukuttan) is the standard Indic tokenizer -- the same lineage as the
IndicNLPSuite work behind IndicBERT, already a candidate in `model-research.md` §4 -- and handles
both correctly. It is used here for Sinhala and Tamil; Latin-script text (english, singlish,
tamilish) keeps a Unicode-aware regex, which agrees with it at 99.4-99.5%.

Dispatch is on **script**, detected from the text itself, not on the dataset's `language` column:
a vectorizer only ever sees a string, and code-mixed rows carry both scripts anyway.
"""
from __future__ import annotations

import re

# Unicode blocks. Sinhala U+0D80-U+0DFF, Tamil U+0B80-U+0BFF.
_SINHALA = re.compile(r"[඀-෿]")
_TAMIL = re.compile(r"[஀-௿]")

# Latin-script fallback: letters, marks and digits, two or more. `regex` is used rather than `re`
# because only it supports the \p{...} Unicode property classes.
try:
    import regex as _re2

    _LATIN = _re2.compile(r"[\p{L}\p{M}\p{N}]{2,}")
    _HAVE_REGEX = True
except ImportError:  # pragma: no cover
    _LATIN = re.compile(r"[^\W_]{2,}", re.UNICODE)
    _HAVE_REGEX = False

MIN_TOKEN_LEN = 2


def script_of(text: str) -> str:
    """'si', 'ta' or 'en' -- whichever Indic block appears, else Latin."""
    if _SINHALA.search(text):
        return "si"
    if _TAMIL.search(text):
        return "ta"
    return "en"


def tokenize(text: str) -> list[str]:
    """Word tokens, dispatched on script. Safe to hand to a scikit-learn vectorizer."""
    script = script_of(text)
    if script == "en":
        return _LATIN.findall(text)

    from indicnlp.tokenize import indic_tokenize

    return [
        t for t in indic_tokenize.trivial_tokenize(text, script)
        if len(t) >= MIN_TOKEN_LEN and any(c.isalnum() for c in t)
    ]


def char_preservation(text: str) -> float:
    """Share of non-space characters surviving tokenization. 1.0 means nothing was dropped.

    The check that caught the original defect -- a tokenizer silently discarding two thirds of a
    script produces no error, only worse numbers.
    """
    toks = tokenize(text)
    total = len(re.sub(r"\s", "", text))
    return 1.0 if total == 0 else sum(len(t) for t in toks) / total
