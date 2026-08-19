import httpx
import pytest

from app.inference import services


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
        return FakeResponse(
            text=(
                'event: complete\n'
                'data: [{"label":"card_payment_fee_charged",'
                '"confidences":[{"label":"card_payment_fee_charged",'
                '"confidence":0.91}]}]\n'
            )
        )


@pytest.mark.asyncio
async def test_remote_space_prediction(monkeypatch) -> None:
    monkeypatch.setattr(services.httpx, "AsyncClient", FakeClient)

    category, priority, sentiment = await services.classify(
        "I was charged an extra card payment fee"
    )

    assert category.value == "card_payment_fee_charged"
    assert category.confidence == pytest.approx(0.91)
    assert category.model_version == "Swift-Support/labse-intent-1.0"
    assert priority.value == "medium"
    assert sentiment.value == "neutral"


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
