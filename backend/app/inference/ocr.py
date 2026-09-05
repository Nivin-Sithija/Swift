"""Text extraction for image attachments.

Two engines are kept side by side so Google Cloud Vision can be benchmarked
against the incumbent Tesseract path before either is made the default.
"""

import asyncio
import base64
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytesseract
from PIL import Image

from app.core.config import get_settings

VISION_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate"
VISION_LANGUAGE_HINTS = ["en", "si", "ta"]
TESSERACT_LANGUAGES = "eng+tam+sin"


class OcrError(RuntimeError):
    pass


@dataclass(frozen=True)
class OcrResult:
    text: str
    engine: str
    confidence: float | None = None


async def extract_text(path: Path | str, *, engine: str | None = None) -> OcrResult:
    """Run the configured OCR engine, or the one named by the caller."""
    settings = get_settings()
    chosen = (engine or settings.ocr_engine).strip().lower()
    if chosen == "google_vision":
        return await google_vision_ocr(path)
    if chosen == "tesseract":
        return await tesseract_ocr(path)
    raise OcrError(f"Unknown OCR engine '{chosen}'")


async def tesseract_ocr(path: Path | str) -> OcrResult:
    def run() -> str:
        with Image.open(path) as image:
            return str(pytesseract.image_to_string(image, lang=TESSERACT_LANGUAGES)).strip()

    # Tesseract is blocking, so keep it off the event loop serving other requests.
    return OcrResult(await asyncio.to_thread(run), "tesseract")


async def google_vision_ocr(path: Path | str) -> OcrResult:
    """Call the Cloud Vision REST API with DOCUMENT_TEXT_DETECTION."""
    settings = get_settings()
    if not settings.google_vision_api_key:
        raise OcrError("SWIFT_GOOGLE_VISION_API_KEY is not configured")

    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    payload = {
        "requests": [
            {
                "image": {"content": encoded},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "imageContext": {"languageHints": VISION_LANGUAGE_HINTS},
            }
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ocr_request_timeout_seconds) as client:
            response = await client.post(
                VISION_ENDPOINT,
                params={"key": settings.google_vision_api_key},
                json=payload,
            )
            response.raise_for_status()
            body = response.json()["responses"][0]
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
        raise OcrError("Google Vision OCR request failed") from exc

    if "error" in body:
        raise OcrError(f"Google Vision OCR failed: {body['error'].get('message', 'unknown error')}")

    annotation = body.get("fullTextAnnotation")
    if not annotation:
        # A readable image with no text is a normal outcome, not a failure.
        return OcrResult("", "google_vision", None)
    return OcrResult(
        str(annotation.get("text", "")).strip(),
        "google_vision",
        _page_confidence(annotation),
    )


def _page_confidence(annotation: dict) -> float | None:
    scores = [
        float(page["confidence"])
        for page in annotation.get("pages", [])
        if isinstance(page, dict) and page.get("confidence") is not None
    ]
    return sum(scores) / len(scores) if scores else None
