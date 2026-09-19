import asyncio
import json

import httpx
import pytest

from app.inference import services

# Three gr.Label outputs, in the order the Space returns them: intent, sentiment, priority.
SPACE_OUTPUT = [
    {
        "label": "card_payment_fee_charged",
        "confidences": [{"label": "card_payment_fee_charged", "confidence": 0.91}],
    },
    {"label": "Negative", "confidences": [{"label": "Negative", "confidence": 0.83}]},
    {"label": "High", "confidences": [{"label": "High", "confidence": 0.77}]},
]


def sse(data: list) -> str:
    """Body of a completed Gradio server-sent-event stream."""
    return f"event: complete\ndata: {json.dumps(data)}\n"


class FakeResponse:
    def __init__(self, *, json_data=None, text: str = "", error: bool = False) -> None:
        self._json_data = json_data
        self.text = text
        self.error = error

    def json(self):
        return self._json_data

    def raise_for_status(self) -> None:
        if self.error:
            raise httpx.ConnectError("Space unavailable")


class FakeClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args) -> None:
        return None

    async def post(self, *args, **kwargs) -> FakeResponse:
        return FakeResponse(json_data={"event_id": "event-1"})

    async def get(self, *args, **kwargs) -> FakeResponse:
        return FakeResponse(text=sse(SPACE_OUTPUT))


@pytest.mark.asyncio
async def test_remote_space_prediction(monkeypatch) -> None:
    monkeypatch.setattr(services.httpx, "AsyncClient", FakeClient)

    category, priority, sentiment = await services.classify(
        "I was charged an extra card payment fee"
    )

    assert category.value == "card_payment_fee_charged"
    assert category.confidence == pytest.approx(0.91)
    assert category.model_version == "Swift-Support/labse-intent-1.0"
    assert (priority.value, priority.confidence) == ("high", pytest.approx(0.77))
    assert priority.model_version == "Swift-Support/labse-priority-1.0"
    assert (sentiment.value, sentiment.confidence) == ("negative", pytest.approx(0.83))
    assert sentiment.model_version == "Swift-Support/labse-sentiment-1.0"


@pytest.mark.asyncio
async def test_fraud_words_raise_the_model_priority_to_critical(monkeypatch) -> None:
    monkeypatch.setattr(services.httpx, "AsyncClient", FakeClient)

    _, priority, _ = await services.classify("Someone made an unauthorized payment")

    # The priority model has no critical class; the keyword rule supplies it.
    assert priority.value == "critical"


@pytest.mark.asyncio
async def test_unexpected_space_labels_fall_back_to_rules(monkeypatch) -> None:
    class OddClient(FakeClient):
        async def get(self, *args, **kwargs) -> FakeResponse:
            urgent = {"label": "Urgent", "confidences": [{"label": "Urgent", "confidence": 0.9}]}
            return FakeResponse(text=sse([SPACE_OUTPUT[0], SPACE_OUTPUT[1], urgent]))

    monkeypatch.setattr(services.httpx, "AsyncClient", OddClient)

    category, priority, _ = await services.classify("A normal customer message")

    assert category.model_version == "huggingface-space-unavailable"
    assert priority.model_version == "development-rules-priority-1.0"


@pytest.mark.asyncio
async def test_remote_space_failure_routes_to_manual_review(monkeypatch) -> None:
    class FailingClient(FakeClient):
        async def post(self, *args, **kwargs) -> FakeResponse:
            return FakeResponse(error=True)

    monkeypatch.setattr(services.httpx, "AsyncClient", FailingClient)

    category, _, _ = await services.classify("A normal customer message")

    assert category.value == "unknown"
    assert category.confidence == 0.0
    assert category.model_version == "huggingface-space-unavailable"


@pytest.mark.asyncio
async def test_slow_remote_inference_does_not_block_ticket_submission(monkeypatch) -> None:
    async def slow_prediction(_text: str):
        await asyncio.sleep(1)

    monkeypatch.setattr(services, "classify_with_space", slow_prediction)
    monkeypatch.setattr(services.settings, "ticket_submission_inference_timeout_seconds", 0.01)

    category, _, _ = await services.classify("A normal customer message")

    assert category.value == "unknown"
    assert category.confidence == 0.0
    assert category.model_version == "huggingface-space-timeout"
