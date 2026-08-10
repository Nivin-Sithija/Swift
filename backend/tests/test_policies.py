from app.domain.enums import Priority, Sentiment, TicketStatus
from app.domain.policies import can_transition, requires_manual_review
from app.inference.services import detect_language, response_template


def test_status_transition_rules() -> None:
    assert can_transition(TicketStatus.new, TicketStatus.processing)
    assert not can_transition(TicketStatus.closed, TicketStatus.processing)


def test_manual_review_rules() -> None:
    assert requires_manual_review(
        confidence_values=[0.9],
        priority=Priority.critical,
        sentiment=Sentiment.neutral,
        category="cash_withdrawal",
    )
    assert not requires_manual_review(
        confidence_values=[0.9],
        priority=Priority.medium,
        sentiment=Sentiment.neutral,
        category="beneficiary_not_allowed",
    )


def test_language_detection_and_safe_templates() -> None:
    assert detect_language("මගේ card eka වැඩ නැහැ").value == "code_mixed"
    assert "does not confirm" in response_template("english")
