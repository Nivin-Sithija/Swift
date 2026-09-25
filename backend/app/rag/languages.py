import re
import unicodedata

from app.rag.types import ConsumerLanguage

SINHALA = re.compile(r"[\u0D80-\u0DFF]")
TAMIL = re.compile(r"[\u0B80-\u0BFF]")
SPACE = re.compile(r"\s+")

# The romanized tracks carry no script signal, so they are recognised from marker
# words drawn from the labelled corpora. Spelling varies in romanization, so both
# forms are listed where the corpus uses both ("epdi"/"eppadi", "seyya"/"seiya").
TAMILISH_MARKERS = (
    "enna", "epdi", "eppadi", "panna", "mudiyala", "mudiyuma", "irukku", "venum",
    "vendum", "aayiduchu", "enoda", "naan", "enakku", "endru", "athu", "athai",
    "innum", "seyya", "seiya", "evvalavu", "intha", "panathai",
)
SINGLISH_MARKERS = (
    "mage", "mama", "mata", "kohomada", "karanna", "karanne", "karaganna",
    "puluwanda", "puluvanda", "naha", "tiyenawa", "eka", "eken", "kiyala",
    "kala", "salli", "pavichchi", "vada", "vuna", "mokada", "mokakda", "hari",
)


def _markers(tokens: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    """Anchor each marker at a word start, but leave the end open.

    Sinhala and Tamil agglutinate, so a suffixed form has to keep matching its
    stem: "eka" must still fire on "ekak" and "ekata". Anchoring only the start
    keeps that behaviour while stopping a marker from matching inside an
    unrelated English word, which is how "enna" used to fire on "antenna".
    """
    return tuple(re.compile(rf"\b{re.escape(token)}") for token in tokens)


TAMILISH = _markers(TAMILISH_MARKERS)
SINGLISH = _markers(SINGLISH_MARKERS)


def detect_consumer_language(text: str) -> ConsumerLanguage:
    if SINHALA.search(text):
        return ConsumerLanguage.sinhala
    if TAMIL.search(text):
        return ConsumerLanguage.tamil
    lowered = text.casefold()
    ta = sum(bool(marker.search(lowered)) for marker in TAMILISH)
    si = sum(bool(marker.search(lowered)) for marker in SINGLISH)
    if ta > si and ta:
        return ConsumerLanguage.tamilish
    if si:
        return ConsumerLanguage.singlish
    return ConsumerLanguage.english if re.search(r"[A-Za-z]", text) else ConsumerLanguage.unknown


def normalize_query(text: str) -> str:
    """Conservative normalization: preserve meaning and never replace the original query."""
    return SPACE.sub(" ", unicodedata.normalize("NFKC", text)).strip()
