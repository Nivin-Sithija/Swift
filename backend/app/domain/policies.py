from app.domain.enums import Priority, Sentiment, TicketStatus

ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.new: {TicketStatus.processing, TicketStatus.assigned, TicketStatus.escalated},
    TicketStatus.processing: {TicketStatus.in_review, TicketStatus.escalated},
    TicketStatus.in_review: {
        TicketStatus.assigned,
        TicketStatus.escalated,
        TicketStatus.response_draft,
    },
    TicketStatus.assigned: {
        TicketStatus.escalated,
        TicketStatus.response_draft,
        TicketStatus.resolved,
    },
    TicketStatus.escalated: {
        TicketStatus.assigned,
        TicketStatus.response_draft,
        TicketStatus.resolved,
    },
    TicketStatus.response_draft: {TicketStatus.responded, TicketStatus.assigned},
    TicketStatus.responded: {TicketStatus.resolved, TicketStatus.reopened},
    TicketStatus.resolved: {TicketStatus.closed, TicketStatus.reopened},
    TicketStatus.closed: {TicketStatus.reopened},
    TicketStatus.reopened: {TicketStatus.assigned, TicketStatus.escalated},
}


def can_transition(current: TicketStatus, target: TicketStatus) -> bool:
    return current == target or target in ALLOWED_TRANSITIONS.get(current, set())


def requires_manual_review(
    *, confidence_values: list[float], priority: Priority, sentiment: Sentiment, category: str
) -> bool:
    sensitive = any(
        word in category.lower() for word in ("fraud", "cash withdrawal", "card stolen")
    )
    return (
        any(value < 0.60 for value in confidence_values)
        or priority == Priority.critical
        or sentiment == Sentiment.negative
        or sensitive
    )
