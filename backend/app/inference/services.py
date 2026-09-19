import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
import joblib
import numpy as np

from app.core.config import get_settings
from app.domain.enums import LanguageForm, Priority, Sentiment

_svm_pipeline = None
_svm_calibration: dict[str, float] | None = None
settings = get_settings()

OCR_INTENT_MODEL_VERSION = "svm-ocr-intent-1.0"
# Below this, the LaBSE prediction on the customer's own words is weak enough that the
# attachment text is allowed to decide. It matches the manual-review confidence floor.
TEXT_INTENT_CONFIDENCE_FLOOR = 0.60


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


async def classify(text: str) -> tuple[Result, Result, Result]:
    # Intent comes from LaBSE on the customer's own words. Attachment text is
    # classified separately (classify_ocr_intent) and combined with fuse_intent.
    try:
        intent_result = await asyncio.wait_for(
            classify_intent_with_space(text),
            timeout=settings.ticket_submission_inference_timeout_seconds,
        )
    except TimeoutError:
        # A cold or unavailable external model must not hold the customer's
        # ticket submission open. Low confidence routes this for review.
        intent_result = Result("unknown", 0.0, "huggingface-space-timeout")

    priority, sentiment = classify_priority_and_sentiment(text)
    return intent_result, priority, sentiment


def classify_priority_and_sentiment(text: str) -> tuple[Result, Result]:
    # Development keyword rules until the priority and sentiment models are served.
    lowered = text.lower()
    critical = any(
        x in lowered for x in ("fraud", "stolen", "not recognise", "unauthorised", "unauthorized")
    )
    negative = any(
        x in lowered for x in ("failed", "deduct", "missing", "blocked", "නැහැ", "தோல்வி")
    )
    return (
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


def _ml_dir() -> Path:
    ml_dir = Path("/app/ml")
    if not ml_dir.exists():
        ml_dir = Path(__file__).resolve().parents[3] / "ml"
    return ml_dir


def classify_ocr_intent(text: str) -> Result:
    """Classify attachment (OCR) text with the local TF-IDF SVM.

    On screenshot text the SVM matches LaBSE (ml/reports/intent_accuracy_by_ocr_engine.md)
    and runs locally. LinearSVC scores are margins, so the confidence comes from the
    calibration fitted by ml/scripts/calibrate_svm_confidence.py.
    """
    global _svm_pipeline, _svm_calibration

    if _svm_pipeline is None or _svm_calibration is None:
        models = _ml_dir() / "models"
        _svm_pipeline = joblib.load(models / "tfidf_linear_svm_all.joblib")
        _svm_calibration = json.loads(
            (models / "tfidf_linear_svm_all.calibration.json").read_text(encoding="utf-8")
        )

    scores = _svm_pipeline.decision_function([text])[0]
    top, runner_up = np.sort(scores)[::-1][:2]
    logit = (
        _svm_calibration["w_top"] * top
        + _svm_calibration["w_margin"] * (top - runner_up)
        + _svm_calibration["bias"]
    )
    confidence = float(1 / (1 + np.exp(-logit)))
    label = str(_svm_pipeline.classes_[int(np.argmax(scores))])
    return Result(label, confidence, OCR_INTENT_MODEL_VERSION)


def fuse_intent(text_intent: Result, ocr_intent: Result | None) -> Result:
    """Combine the customer-text prediction with the attachment-text prediction.

    The customer's own words stay the primary signal. Attachment text decides only
    when the text prediction is weak (e.g. a message that only says "see attached").
    """
    if ocr_intent is None or text_intent.confidence >= TEXT_INTENT_CONFIDENCE_FLOOR:
        return text_intent
    if ocr_intent.value == text_intent.value:
        # Two independent sources agree: keep the label, take the stronger evidence.
        # The combined version keeps this from being reused as a text-only prediction.
        return Result(
            text_intent.value,
            max(text_intent.confidence, ocr_intent.confidence),
            f"{text_intent.model_version}+{ocr_intent.model_version}",
        )
    if ocr_intent.confidence > text_intent.confidence:
        return ocr_intent
    return text_intent


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
