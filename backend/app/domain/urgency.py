"""ICATC Sections V-VI: log-pooled severity with SLA-relative multiplicative aging."""

import json
import math
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.enums import PredictionTask, TicketStatus
from app.models.entities import Prediction, Ticket
from app.schemas.api import UrgencyOut

CLASSES = ("low", "medium", "high")
SLA_MINUTES = {"low": 480.0, "medium": 120.0, "high": 30.0, "critical": 30.0}
ALPHA = 16.0
# Operational extension: an exactly zero score must still accrue waiting priority.
MIN_SEVERITY = 0.01
INACTIVE = {TicketStatus.responded, TicketStatus.resolved, TicketStatus.closed}


@lru_cache(maxsize=1)
def load_priors() -> dict[str, Any]:
    return json.loads(Path(__file__).with_name("queue_priors.json").read_text(encoding="utf-8"))


def normalized(values: dict[str, float] | None) -> dict[str, float] | None:
    """Reject missing/truncated probabilities instead of inventing the missing mass."""
    if not values or any(not math.isfinite(v) or v < 0 or v > 1 for v in values.values()):
        return None
    total = sum(values.values())
    if not math.isclose(total, 1.0, abs_tol=1e-6):
        return None
    return {k: v / total for k, v in values.items()}


def effective_distribution(prediction: Prediction | None) -> dict[str, float] | None:
    if prediction is None:
        return None
    if prediction.reviewed_value is not None:
        return {prediction.reviewed_value: 1.0}
    return normalized(prediction.probabilities)


def as_utc(value: datetime) -> datetime:
    # SQLite drops timezone info; PostgreSQL returns aware UTC timestamps.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def ticket_urgency(ticket: Ticket, now: datetime) -> UrgencyOut:
    priors = load_priors()
    predictions = {p.task: p for p in ticket.predictions}
    priority = predictions.get(PredictionTask.priority)
    intent = predictions.get(PredictionTask.category)
    sentiment = predictions.get(PredictionTask.sentiment)
    priority_value = (priority.reviewed_value or priority.value) if priority else ticket.priority
    intent_value = (intent.reviewed_value or intent.value) if intent else "unknown"
    sentiment_value = (sentiment.reviewed_value or sentiment.value) if sentiment else ticket.sentiment
    direct = effective_distribution(priority)
    intent_probs = effective_distribution(intent)
    sentiment_probs = effective_distribution(sentiment)
    mode = "log_pool"
    if priority is not None and priority.reviewed_value is not None:
        mode = "reviewed_priority"
    elif priority_value == "critical":
        mode = "critical_override"
    elif direct is None or not set(direct).issubset(CLASSES):
        mode = "label_fallback"
    elif intent_probs is None:
        mode = "priority_head"

    if mode == "log_pool":
        assert direct is not None and intent_probs is not None
        conditional = priors["priority_given_intent"]
        base = priors["base_priority"]
        chain = {
            k: sum(p * conditional.get(i, base)[k] for i, p in intent_probs.items())
            for k in CLASSES
        }
        pooled = {k: math.sqrt((direct.get(k, 0) + 1e-12) * (chain[k] + 1e-12)) for k in CLASSES}
        total = sum(pooled.values())
        posterior = {k: v / total for k, v in pooled.items()}
    elif mode == "priority_head":
        assert direct is not None
        posterior = direct
    else:
        # Legacy/rule results only have a label. Do not fabricate a model posterior
        # from top-label confidence. Critical is the existing app's fourth tier.
        label = "high" if priority_value == "critical" else priority_value
        posterior = {str(label): 1.0} if label in CLASSES else priors["base_priority"]

    severity = 0.5 * posterior.get("medium", 0) + posterior.get("high", 0)
    negative = sentiment_probs.get("negative", 0) if sentiment_probs else float(sentiment_value == "negative")
    criticality = priors["criticality"].get(intent_value, priors["base_priority"]["high"])
    intrinsic = max(MIN_SEVERITY, 0.8 * severity + 0.1 * negative + 0.1 * criticality)
    # SLA tier is the pooled argmax, except for explicit staff/rule decisions.
    tier = max(CLASSES, key=lambda k: posterior.get(k, 0))
    if priority_value == "critical":
        tier = "critical"
    deadline = SLA_MINUTES[tier]
    now = as_utc(now)
    wait = max(0.0, (now - as_utc(ticket.created_at)).total_seconds() / 60)
    active = ticket.status not in INACTIVE
    return UrgencyOut(
        score=intrinsic * (1 + ALPHA * wait / deadline) if active else 0.0,
        intrinsic_severity=intrinsic,
        expected_severity=severity,
        negative_probability=negative,
        intent_criticality=criticality,
        sla_minutes=deadline,
        waiting_minutes=wait,
        aging_alpha=ALPHA,
        evaluated_at=now,
        active=active,
        mode=mode,
        priority_posterior=posterior,
    )


def urgency_sort_key(ticket: Ticket, urgency: UrgencyOut) -> tuple[bool, float, datetime, str]:
    return (not urgency.active, -urgency.score, as_utc(ticket.created_at), ticket.public_id)
