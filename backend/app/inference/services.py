import json
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
import joblib

from app.core.config import get_settings
from app.domain.enums import LanguageForm, Priority, Sentiment

_svm_pipeline = None
settings = get_settings()


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


async def classify(text: str, is_ocr: bool = False) -> tuple[Result, Result, Result]:
    global _svm_pipeline

    ml_dir = Path("/app/ml")
    if not ml_dir.exists():
        ml_dir = Path(__file__).resolve().parents[3] / "ml"
    
    # 1. Intent Classification Router
    if is_ocr:
        # Route OCR text to SVM
        if _svm_pipeline is None:
            svm_path = ml_dir / "models" / "tfidf_linear_svm_all.joblib"
            _svm_pipeline = joblib.load(svm_path)
            
        pred = _svm_pipeline.predict([text])[0]
        intent_result = Result(pred, 0.85, "svm-intent-1.0")
    else:
        intent_result = await classify_intent_with_space(text)

    # 2. Priority & Sentiment (Keeping mocked for now)
    lowered = text.lower()
    critical = any(
        x in lowered for x in ("fraud", "stolen", "not recognise", "unauthorised", "unauthorized")
    )
    negative = any(
        x in lowered for x in ("failed", "deduct", "missing", "blocked", "නැහැ", "தோல்வி")
    )
    return (
        intent_result,
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


async def classify_intent_with_space(text: str) -> Result:
    """Call the public Gradio API hosted by the configured Hugging Face Space."""
    base_url = settings.intent_space_url.rstrip("/")
    headers = {}
    if settings.huggingface_token:
        headers["Authorization"] = f"Bearer {settings.huggingface_token}"

    try:
        async with httpx.AsyncClient(
            headers=headers,
            timeout=settings.intent_request_timeout_seconds,
        ) as client:
            started = await client.post(
                f"{base_url}/gradio_api/call/predict",
                json={"data": [text]},
            )
            started.raise_for_status()
            event_id = started.json()["event_id"]
            completed = await client.get(
                f"{base_url}/gradio_api/call/predict/{event_id}"
            )
            completed.raise_for_status()

        data_lines = [
            line.removeprefix("data: ")
            for line in completed.text.splitlines()
            if line.startswith("data: ")
        ]
        if not data_lines:
            raise ValueError("Hugging Face Space returned no prediction data")
        data_line = data_lines[-1]
        result = json.loads(data_line)[0]
        confidence_by_label = {
            item["label"]: item["confidence"] for item in result["confidences"]
        }
        confidence = confidence_by_label[result["label"]]
        return Result(
            str(result["label"]),
            float(confidence),
            settings.intent_model_id,
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        # External inference must not prevent a customer from creating a ticket.
        return Result("unknown", 0.0, "huggingface-space-unavailable")


def response_template(language: str) -> str:
    templates = {
        "sinhala": "අප හා සම්බන්ධ වීම ගැන ස්තුතියි. ඔබ ලබා දුන් තොරතුරු සහාය නිලධාරියෙකු විසින් සමාලෝචනය කරනු ඇත. මෙම පණිවිඩය කිසිදු බැංකු ක්‍රියාවක් සම්පූර්ණ වූ බව තහවුරු නොකරයි.",
        "tamil": "எங்களைத் தொடர்புகொண்டதற்கு நன்றி. நீங்கள் வழங்கிய தகவலை ஆதரவு அலுவலர் சரிபார்ப்பார். இந்தச் செய்தி எந்த வங்கிச் செயலும் நிறைவடைந்ததை உறுதிப்படுத்தவில்லை.",
        "english": "Thank you for contacting Swift Support. A support agent will review the information you provided. This message does not confirm that any banking action has been completed.",
    }
    return templates.get(language, templates["english"])
