"""
Romanization module: Sinhala -> Singlish, Tamil -> Tamilish.

Uses aksharamukha's `RomanColloquial` scheme, which produces natural,
diacritic-free chat-style Latin text (how Sri Lankans actually type on
phones), e.g.:

    Sinhala  මම මගේ කාඩ්පත සොයා ගන්නේ කෙසේද?  -> mama mage kadpata soya ganne keseda?
    Tamil    எனது அட்டையை நான் எவ்வாறு...     -> enathu attaiyai nan evvaru...

Note: aksharamukha imports `from ast import Str`, removed in Python 3.12+.
We shim the removed names before importing so it runs on modern Python.
"""
import ast as _ast

for _n in ("Str", "Bytes", "Num", "NameConstant", "Ellipsis"):
    if not hasattr(_ast, _n):
        setattr(_ast, _n, str)

import aksharamukha.transliterate as _t  # noqa: E402

_SCRIPT = {
    "singlish": "Sinhala",
    "tamilish": "Tamil",
}
_SCHEME = "RomanColloquial"


def romanize(native_text: str, roman_lang: str) -> str:
    """Romanize a Sinhala/Tamil string.

    roman_lang: "singlish" (from Sinhala) or "tamilish" (from Tamil).
    """
    if roman_lang not in _SCRIPT:
        raise ValueError(f"unknown roman language: {roman_lang!r}")
    if not native_text:
        return native_text
    return _t.process(_SCRIPT[roman_lang], _SCHEME, native_text)


if __name__ == "__main__":
    demo_si = "මම මගේ කාඩ්පත සොයා ගන්නේ කෙසේද?"
    demo_ta = "எனது அட்டையை நான் எவ்வாறு கண்டறிவது?"
    print("singlish:", romanize(demo_si, "singlish"))
    print("tamilish:", romanize(demo_ta, "tamilish"))
