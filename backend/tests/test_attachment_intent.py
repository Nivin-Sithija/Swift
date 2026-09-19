"""Attachment (OCR) text as a second intent signal next to the customer's own words.

The customer text keeps its LaBSE prediction unless that prediction is weak; the OCR
text is classified separately by the local SVM and never rewrites the ticket text or
a prediction a staff member has already reviewed.
"""

from app.inference import services
from app.inference.ocr import OcrResult
from app.inference.services import Result, classify_ocr_intent, fuse_intent

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
TEXT_MODEL = "Swift-Support/labse-intent-1.0"
OCR_MODEL = services.OCR_INTENT_MODEL_VERSION


# --- fusion rule ------------------------------------------------------------


def test_confident_customer_text_wins_over_attachment_text() -> None:
    text = Result("lost_or_stolen_card", 0.91, TEXT_MODEL)
    ocr = Result("failed_transfer", 0.99, OCR_MODEL)
    assert fuse_intent(text, ocr) == text


def test_weak_customer_text_defers_to_a_stronger_attachment() -> None:
    text = Result("card_arrival", 0.20, TEXT_MODEL)
    ocr = Result("failed_transfer", 0.80, OCR_MODEL)
    assert fuse_intent(text, ocr) == ocr


def test_agreement_keeps_the_text_label_with_the_stronger_confidence() -> None:
    text = Result("failed_transfer", 0.40, TEXT_MODEL)
    ocr = Result("failed_transfer", 0.75, OCR_MODEL)
    assert fuse_intent(text, ocr) == Result("failed_transfer", 0.75, TEXT_MODEL)


def test_weak_attachment_does_not_replace_weak_text() -> None:
    text = Result("card_arrival", 0.40, TEXT_MODEL)
    ocr = Result("failed_transfer", 0.30, OCR_MODEL)
    assert fuse_intent(text, ocr) == text


def test_no_attachment_text_keeps_the_text_prediction() -> None:
    text = Result("unknown", 0.0, "huggingface-space-unavailable")
    assert fuse_intent(text, None) == text


# --- calibrated SVM confidence ------------------------------------------------


def test_svm_confidence_is_calibrated_not_fixed() -> None:
    clear = classify_ocr_intent("My card payment was declined at the shop")
    vague = classify_ocr_intent("see attached")

    assert clear.value == "declined_card_payment"
    assert clear.model_version == OCR_MODEL
    assert 0.0 <= vague.confidence < clear.confidence <= 1.0
    assert clear.confidence != 0.85


# --- upload flow --------------------------------------------------------------


def _stub_ocr(monkeypatch, text: str) -> None:
    from app.api.v1 import routes

    async def _extract(_path, **_kwargs):
        return OcrResult(text=text, confidence=0.95, engine="test-ocr")

    monkeypatch.setattr(routes, "extract_text", _extract)


async def _upload(client, ticket: str, headers):
    response = await client.post(
        f"/tickets/{ticket}/attachments",
        files={"file": ("proof.png", PNG, "image/png")},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_attachment_keeps_customer_text_and_reviewed_prediction(
    client, customer, agent, new_ticket, auth_headers, monkeypatch
):
    ticket = await new_ticket(customer)
    before = (await client.get(f"/tickets/{ticket}", headers=auth_headers(agent))).json()

    review = await client.put(
        f"/predictions/{before['category']['id']}/reviews",
        json={"value": "transaction_charged_twice", "reason": "Customer describes a double charge"},
        headers=auth_headers(agent),
    )
    assert review.status_code == 200, review.text

    _stub_ocr(monkeypatch, "Transaction failed. Reference 4471")
    uploaded = await _upload(client, ticket, auth_headers(customer))
    assert uploaded["ocr_text"] == "Transaction failed. Reference 4471"

    after = (await client.get(f"/tickets/{ticket}", headers=auth_headers(agent))).json()
    assert after["message"] == before["message"], "OCR text was written into the customer's text"
    assert after["category"]["value"] == "transaction_charged_twice", "staff review was lost"
    assert after["category"]["id"] == before["category"]["id"]
    # Unreviewed keyword predictions do read the screenshot ("failed").
    assert after["priority"]["value"] == "high"
    assert after["attachments"][0]["ocr_text"] == "Transaction failed. Reference 4471"


async def test_attachment_decides_when_the_customer_text_is_weak(
    client, customer, agent, new_ticket, auth_headers, monkeypatch
):
    from app.api.v1 import routes

    async def _weak(text: str):
        return (
            Result("card_arrival", 0.10, TEXT_MODEL),
            Result("medium", 0.80, "test-stub-priority"),
            Result("neutral", 0.80, "test-stub-sentiment"),
        )

    monkeypatch.setattr(routes, "classify", _weak)
    monkeypatch.setattr(
        routes, "classify_ocr_intent", lambda _text: Result("failed_transfer", 0.90, OCR_MODEL)
    )
    ticket = await new_ticket(customer)

    _stub_ocr(monkeypatch, "Transfer failed")
    await _upload(client, ticket, auth_headers(customer))

    after = (await client.get(f"/tickets/{ticket}", headers=auth_headers(agent))).json()
    assert after["category"]["value"] == "failed_transfer"
    assert after["category"]["model_version"] == OCR_MODEL
