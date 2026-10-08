"""Verify the configured live Space supports the complete ICATC log pool."""

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.enums import PredictionTask, Priority, TicketStatus  # noqa: E402
from app.domain.urgency import ticket_urgency  # noqa: E402
from app.inference.services import classify  # noqa: E402
from app.models.entities import Prediction, Ticket  # noqa: E402


async def main() -> None:
    results = await classify("My card has not arrived yet. When should I expect it?")
    tasks = (PredictionTask.category, PredictionTask.priority, PredictionTask.sentiment)
    for task, result, expected in zip(tasks, results, (77, 3, 2), strict=True):
        probabilities = result.probabilities or {}
        if len(probabilities) != expected or abs(sum(probabilities.values()) - 1) > 1e-6:
            raise RuntimeError(f"Incomplete {task.value} distribution")
        print(f"{task.value}: {len(probabilities)} classes; normalized")
    now = datetime.now(UTC)
    ticket = Ticket(
        public_id="SYNTHETIC-VERIFICATION", created_at=now,
        status=TicketStatus.in_review, priority=Priority(results[1].value),
        predictions=[Prediction(task=task, value=result.value, confidence=result.confidence,
                                model_version=result.model_version, probabilities=result.probabilities)
                     for task, result in zip(tasks, results, strict=True)],
    )
    urgency = ticket_urgency(ticket, now)
    if urgency.mode != "log_pool":
        raise RuntimeError(f"Expected log_pool, received {urgency.mode}")
    print(f"Live model -> urgency scorer: {urgency.mode}; score={urgency.score:.6f}")
    print("Verification used synthetic text only and created no database tickets")


if __name__ == "__main__":
    asyncio.run(main())
