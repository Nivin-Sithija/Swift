from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.api.v1 import routes
from app.domain.enums import InterfaceLanguage, PredictionTask, UserRole
from app.rag.service import AssistanceResult


@pytest.mark.asyncio
async def test_customer_assistance_uses_owned_ticket_context(monkeypatch) -> None:
    service = AsyncMock()
    service.assist.return_value = AssistanceResult(
        "human_escalation", "my balance", "my balance", "english", None, [], 0.0,
        "private_account_data",
    )
    ticket = SimpleNamespace(
        original_text="What is my balance?",
        response_language=InterfaceLanguage.english,
        predictions=[
            SimpleNamespace(task=PredictionTask.category, value="card_payment", reviewed_value=None),
            SimpleNamespace(task=PredictionTask.sentiment, value="neutral", reviewed_value=None),
            SimpleNamespace(task=PredictionTask.priority, value="medium", reviewed_value=None),
        ],
    )
    monkeypatch.setattr(routes, "get_ticket", AsyncMock(return_value=ticket))
    customer = SimpleNamespace(role=UserRole.customer)
    response = await routes.create_customer_ticket_assistance(
        "SW-2026-000001",
        customer,
        object(),  # type: ignore[arg-type]
        service,
    )
    assert response.route == "human_escalation"
    assert response.approval_required is False
    service.assist.assert_awaited_once_with(
        query="What is my balance?",
        institution=None,
        category="card_payment",
        language="english",
        intent="card_payment",
        sentiment="neutral",
        priority="medium",
    )


@pytest.mark.asyncio
async def test_staff_cannot_call_customer_ticket_assistance() -> None:
    with pytest.raises(HTTPException) as denied:
        await routes.create_customer_ticket_assistance(
            "SW-2026-000001",
            SimpleNamespace(role=UserRole.agent),
            object(),  # type: ignore[arg-type]
            AsyncMock(),
        )
    assert denied.value.status_code == 403
    assert denied.value.detail == "Customer access required"
