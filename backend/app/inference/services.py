import re
from dataclasses import dataclass

from app.domain.enums import LanguageForm, Priority, Sentiment


@dataclass(frozen=True)
class Result:
    value: str
    confidence: float
    model_version: str


SINHALA = re.compile(r"[\u0D80-\u0DFF]")
TAMIL = re.compile(r"[\u0B80-\u0BFF]")
LATIN = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> Result:
    si, ta, en = len(SINHALA.findall(text)), len(TAMIL.findall(text)), len(LATIN.findall(text))
    if si and en:
        value = LanguageForm.code_mixed
    elif ta and en:
        value = LanguageForm.code_mixed
    elif si:
        value = LanguageForm.sinhala
    elif ta:
        value = LanguageForm.tamil
    elif en:
        lowered = text.lower()
        if any(x in lowered for x in ("eka", "naha", "mage", "karanna", "wela")):
            value = LanguageForm.singlish
        elif any(x in lowered for x in ("enna", "panna", "varala", "mudiyala", "aayiduchu")):
            value = LanguageForm.tanglish
        else:
            value = LanguageForm.english
    else:
        value = LanguageForm.unknown
    return Result(value.value, 0.90 if value != LanguageForm.unknown else 0.30, "unicode-rules-1.0")


def classify(text: str) -> tuple[Result, Result, Result]:
    lowered = text.lower()
    category = (
        "cash_withdrawal"
        if any(x in lowered for x in ("atm", "cash", "සල්ලි", "பணம்"))
        else "card_payment_wrong_exchange_rate"
        if "card" in lowered
        else "cash_withdrawal"
    )
    critical = any(
        x in lowered for x in ("fraud", "stolen", "not recognise", "unauthorised", "unauthorized")
    )
    negative = any(
        x in lowered for x in ("failed", "deduct", "missing", "blocked", "නැහැ", "தோல்வி")
    )
    return (
        Result(category, 0.62, "development-keyword-intent-1.0"),
        Result(
            (
                Priority.critical if critical else Priority.high if negative else Priority.medium
            ).value,
            0.68,
            "development-rules-priority-1.0",
        ),
        Result(
            (Sentiment.negative if negative else Sentiment.neutral).value,
            0.66,
            "development-rules-sentiment-1.0",
        ),
    )


def response_template(language: str) -> str:
    templates = {
        "sinhala": "අප හා සම්බන්ධ වීම ගැන ස්තුතියි. ඔබ ලබා දුන් තොරතුරු සහාය නිලධාරියෙකු විසින් සමාලෝචනය කරනු ඇත. මෙම පණිවිඩය කිසිදු බැංකු ක්‍රියාවක් සම්පූර්ණ වූ බව තහවුරු නොකරයි.",
        "tamil": "எங்களைத் தொடர்புகொண்டதற்கு நன்றி. நீங்கள் வழங்கிய தகவலை ஆதரவு அலுவலர் சரிபார்ப்பார். இந்தச் செய்தி எந்த வங்கிச் செயலும் நிறைவடைந்ததை உறுதிப்படுத்தவில்லை.",
        "english": "Thank you for contacting Swift Support. A support agent will review the information you provided. This message does not confirm that any banking action has been completed.",
    }
    return templates.get(language, templates["english"])
