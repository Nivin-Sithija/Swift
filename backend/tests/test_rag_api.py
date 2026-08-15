from unittest.mock import AsyncMock

import pytest

from app.api.v1.routes import create_consumer_assistance_draft
from app.rag.service import AssistanceResult
from app.schemas.api import ConsumerAssistanceRequest


@pytest.mark.asyncio
async def test_consumer_assistance_endpoint_returns_unapproved_draft() -> None:
    service = AsyncMock()
    service.assist.return_value = AssistanceResult(
        "human_escalation", "my balance", "my balance", "english", None, [], 0.0,
        "private_account_data",
    )
    response = await create_consumer_assistance_draft(
        ConsumerAssistanceRequest(query="What is my balance?", institution="Commercial Bank"),
        object(),  # type: ignore[arg-type]
        service,
    )
    assert response.route == "human_escalation"
    assert response.approval_required is True
    service.assist.assert_awaited_once()
