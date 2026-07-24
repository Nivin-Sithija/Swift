"""
Sinhala -> Singlish for a full sentence: word-level override dict first
(singlish_overrides.OVERRIDES), falling back to aksharamukha's
RomanColloquial romanizer per Sinhala-script run. English words, numbers,
and punctuation already present in the source text pass through unchanged.
"""
import re

from romanize import romanize
from singlish_overrides import OVERRIDES

# a maximal run of Sinhala-script characters (incl. ZWJ used in conjuncts)
_SI_RUN = re.compile(r"[඀-෿‍]+")


def singlishify(text_si: str) -> str:
    if not text_si:
        return text_si

    def repl(m: re.Match) -> str:
        token = m.group(0)
        if token in OVERRIDES:
            return OVERRIDES[token]
        return romanize(token, "singlish")

    return _SI_RUN.sub(repl, text_si)


if __name__ == "__main__":
    examples = [
        "මගේ කාඩ් එක තාම එන්නේ නෑ?",
        "සති 2ක් ගියත් මගේ කාඩ් එක තාම ආවේ නෑ, මම මොකද කරන්න ඕනේ?",
    ]
    for e in examples:
        print(e, "->", singlishify(e))
