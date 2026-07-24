"""
Word-level overrides applied on top of the deterministic aksharamukha
RomanColloquial romanization, for the Sinhala tokens where the mechanical
phonetic transliteration reads worse than how Sri Lankans actually type them
(English loanwords spelled out phonetically instead of in English, and a
couple of long-vowel negatives). Keyed by exact Sinhala token (whitespace-
delimited, as it appears in `sinhala/train_labeled.csv`).

This is a targeted, high-frequency subset (not exhaustive) — see
[[sinhala-translation-workflow]] for why: the rest is expected to be cleaned
up via the hand-edit + backport loop (singlish_diff.py / update_sinhala.py).
"""

OVERRIDES = {
    # negatives (long-vowel -> "aa", matches how it's actually typed)
    "නෑ": "naa",
    "බෑ": "baa",
    "දන්නෑ": "dannaa",
    "හම්බුන්නෑ": "hambunnaa",
    "තාම": "thama",

    # English loanwords kept in Sinhala script in the source text -> spell
    # them as the English word instead of aksharamukha's phonetic guess
    "කාඩ්": "card",
    "ඇප්": "app",
    "ට්‍රාන්සැක්ෂන්": "transaction",
    "එක්ස්චේන්ජ්": "exchange",
    "රේට්": "rate",
    "චාජ්": "charge",
    "ෆී": "fee",
    "ඇක්ටිවේට්": "activate",
    "ට්‍රැක්": "track",
    "ට්‍රැකින්": "tracking",
    "ට්‍රැවල්": "travel",
    "මැෂින්": "machine",
    "ජැකට්": "jacket",
    "පර්චේස්": "purchase",
    "ඩිලිවරි": "delivery",
    "ඕඩර්": "order",
}
