import re
import unicodedata

from app.rag.types import ConsumerLanguage

SINHALA = re.compile(r"[\u0D80-\u0DFF]")
TAMIL = re.compile(r"[\u0B80-\u0BFF]")
SPACE = re.compile(r"\s+")


def detect_consumer_language(text: str) -> ConsumerLanguage:
    if SINHALA.search(text):
        return ConsumerLanguage.sinhala
    if TAMIL.search(text):
        return ConsumerLanguage.tamil
    lowered = text.casefold()
    tamilish = ("enna", "epdi", "panna", "mudiyala", "irukku", "venum", "aayiduchu")
    singlish = ("mage", "kohomada", "karanna", "puluwanda", "naha", "tiyenawa", "eka")
    ta = sum(token in lowered for token in tamilish)
    si = sum(token in lowered for token in singlish)
    if ta > si and ta:
        return ConsumerLanguage.tamilish
    if si:
        return ConsumerLanguage.singlish
    return ConsumerLanguage.english if re.search(r"[A-Za-z]", text) else ConsumerLanguage.unknown


def normalize_query(text: str) -> str:
    """Conservative normalization: preserve meaning and never replace the original query."""
    return SPACE.sub(" ", unicodedata.normalize("NFKC", text)).strip()
