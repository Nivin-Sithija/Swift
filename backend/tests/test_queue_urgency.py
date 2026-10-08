from datetime import UTC, datetime, timedelta
from math import sqrt

import pytest
from sqlalchemy import select

from app.domain.enums import InterfaceLanguage, PredictionTask, Priority, TicketStatus
from app.domain.urgency import load_priors, ticket_urgency, urgency_sort_key
from app.inference.services import Result, _label_result
from app.models.entities import Prediction, Ticket

NOW = datetime(2026, 10, 2, 12, tzinfo=UTC)


def prediction(task, value, probabilities=None, reviewed_value=None):
    return Prediction(task=task, value=value, confidence=0.8, model_version="test",
                      probabilities=probabilities, reviewed_value=reviewed_value)


def ticket(*, priority="medium", age=0, probs=None, intent_probs=None, sentiment_probs=None):
    return Ticket(
        public_id="SW-TEST", created_at=NOW - timedelta(minutes=age),
        status=TicketStatus.in_review, priority=Priority(priority),
        predictions=[
            prediction(PredictionTask.priority, priority, probs),
            prediction(PredictionTask.category, "card_arrival", intent_probs),
            prediction(PredictionTask.sentiment, "neutral", sentiment_probs),
        ],
    )


def test_log_pool_marginalizes_full_intent_and_matches_paper_formula():
    direct = {"low": 0.2, "medium": 0.3, "high": 0.5}
    intents = {"card_arrival": 0.6, "lost_or_stolen_card": 0.4}
    item = ticket(age=60, probs=direct, intent_probs=intents,
                  sentiment_probs={"neutral": 0.75, "negative": 0.25})
    actual = ticket_urgency(item, NOW)
    priors = load_priors()
    chain = {k: sum(p * priors["priority_given_intent"][i][k] for i, p in intents.items())
             for k in direct}
    raw = {k: sqrt((direct[k] + 1e-12) * (chain[k] + 1e-12)) for k in direct}
    expected = {k: v / sum(raw.values()) for k, v in raw.items()}
    severity = 0.5 * expected["medium"] + expected["high"]
    intrinsic = 0.8 * severity + 0.1 * 0.25 + 0.1 * priors["criticality"]["card_arrival"]
    assert actual.mode == "log_pool"
    assert actual.priority_posterior == pytest.approx(expected)
    assert actual.intrinsic_severity == pytest.approx(intrinsic)
    assert actual.score == pytest.approx(intrinsic * (1 + 16 * 60 / actual.sla_minutes))


def test_old_low_can_overtake_fresh_medium_even_with_zero_raw_severity():
    low = ticket(priority="low", age=48 * 60)
    low.predictions[1].value = "unknown_zero"
    # Pick an empirically zero-risk intent so all three raw components are zero.
    low.predictions[1].value = next(i for i, k in load_priors()["criticality"].items() if k == 0)
    score = ticket_urgency(low, NOW)
    assert score.intrinsic_severity == 0.01
    assert score.score > ticket_urgency(ticket(), NOW).score


def test_continuous_posterior_distinguishes_same_priority_label():
    confident = ticket(priority="high", probs={"low": 0.01, "medium": 0, "high": 0.99})
    uncertain = ticket(priority="high", probs={"low": 0.49, "medium": 0, "high": 0.51})
    assert ticket_urgency(confident, NOW).score > ticket_urgency(uncertain, NOW).score


def test_manual_priority_review_bypasses_conflicting_model_distribution():
    item = ticket(priority="high", probs={"high": 1.0}, intent_probs={"lost_or_stolen_card": 1.0})
    item.predictions[0].reviewed_value = "low"
    result = ticket_urgency(item, NOW)
    assert result.mode == "reviewed_priority"
    assert result.expected_severity == 0
    assert result.sla_minutes == 480


@pytest.mark.parametrize("status", [TicketStatus.responded, TicketStatus.resolved, TicketStatus.closed])
def test_completed_tickets_stop_competing_for_dispatch(status):
    item = ticket(priority="critical", age=10000)
    item.status = status
    score = ticket_urgency(item, NOW)
    assert score.score == 0
    assert not score.active
    item.status = TicketStatus.reopened
    assert ticket_urgency(item, NOW).active


def test_critical_override_future_dates_and_naive_utc():
    item = ticket(priority="critical", age=-10)
    item.created_at = item.created_at.replace(tzinfo=None)
    result = ticket_urgency(item, NOW)
    assert result.mode == "critical_override"
    assert result.expected_severity == 1
    assert result.sla_minutes == 30
    assert result.waiting_minutes == 0


def test_equal_scores_use_oldest_then_id():
    older, newer = ticket(age=10), ticket()
    older.status = newer.status = TicketStatus.closed
    assert urgency_sort_key(older, ticket_urgency(older, NOW)) < urgency_sort_key(newer, ticket_urgency(newer, NOW))
    newer.created_at = older.created_at
    older.public_id, newer.public_id = "SW-001", "SW-002"
    assert urgency_sort_key(older, ticket_urgency(older, NOW)) < urgency_sort_key(newer, ticket_urgency(newer, NOW))


def test_full_space_probabilities_are_retained_but_truncated_values_are_not_fabricated():
    full = _label_result({"label": "High", "confidences": [
        {"label": "High", "confidence": 0.7},
        {"label": "Medium", "confidence": 0.2},
        {"label": "Low", "confidence": 0.1},
    ]}, "test", {"low", "medium", "high"})
    assert full.probabilities == pytest.approx({"high": 0.7, "medium": 0.2, "low": 0.1})
    partial = _label_result({"label": "High", "confidences": [
        {"label": "High", "confidence": 0.7},
    ]}, "test", {"high"})
    assert partial.probabilities is None
    truncated_certain = _label_result({"label": "card_arrival", "confidences": [
        {"label": "card_arrival", "confidence": 1.0},
    ]}, "intent", expected_classes=77)
    assert truncated_certain.probabilities is None
    with pytest.raises(ValueError):
        _label_result({"label": "High", "confidences": [{"label": "High", "confidence": float("nan")}]}, "test")


async def test_urgency_ranks_all_tickets_before_pagination_and_preserves_customer_scope(
    client, db, customer, other_customer, agent, administrator, auth_headers,
):
    for index in range(105):
        db.add(Ticket(
            public_id=f"SW-{index:03d}", customer_id=customer.id,
            subject="Queue test", original_text="Queue ordering regression fixture",
            response_language=InterfaceLanguage.english,
            priority=Priority.high if index == 0 else Priority.low,
            status=TicketStatus.in_review,
            created_at=NOW - timedelta(minutes=105 - index),
        ))
    await db.commit()
    for staff in (agent, administrator):
        response = await client.get("/tickets?sort=urgency&page_size=2", headers=auth_headers(staff))
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["total"] == 105
        assert data["items"][0]["id"] == "SW-000"
        assert len(data["items"]) == 2
        assert len({i["urgency"]["evaluated_at"] for i in data["items"]}) == 1
    customer_data = (await client.get("/tickets?sort=urgency", headers=auth_headers(customer))).json()
    assert customer_data["items"][0]["id"] == "SW-104"
    assert all(i["urgency"] is None for i in customer_data["items"])
    other = (await client.get("/tickets?sort=urgency", headers=auth_headers(other_customer))).json()
    assert other["total"] == 0


async def test_new_ticket_persists_distributions_and_staff_review_recalculates(
    client, db, customer, agent, new_ticket, auth_headers, monkeypatch,
):
    from app.api.v1 import routes

    async def classify(_text):
        return (Result("card_arrival", 0.8, "intent", {"card_arrival": 0.8, "lost_or_stolen_card": 0.2}),
                Result("medium", 0.6, "priority", {"low": 0.2, "medium": 0.6, "high": 0.2}),
                Result("neutral", 0.9, "sentiment", {"neutral": 0.9, "negative": 0.1}))

    monkeypatch.setattr(routes, "classify", classify)
    id_ = await new_ticket(customer)
    stored = (await db.scalars(select(Prediction))).all()
    assert sum(p.probabilities is not None for p in stored) == 3
    headers = auth_headers(agent)
    before = (await client.get(f"/tickets/{id_}", headers=headers)).json()
    assert before["urgency"]["mode"] == "log_pool"
    reviewed = await client.put(f"/predictions/{before['priority']['id']}/reviews",
                                json={"value": "critical", "reason": "Confirmed urgent incident"}, headers=headers)
    assert reviewed.status_code == 200, reviewed.text
    after = (await client.get(f"/tickets/{id_}", headers=headers)).json()
    assert after["urgency"]["mode"] == "reviewed_priority"
    assert after["urgency"]["expected_severity"] == 1
    assert after["urgency"]["sla_minutes"] == 30
