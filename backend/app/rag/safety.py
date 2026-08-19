from app.rag.types import QueryContext, RouteDecision

RULES: dict[str, tuple[str, ...]] = {
    "private_account_data": (
        "my balance",
        "account balance",
        "my statement",
        "my account number",
        "transaction history",
        "මගේ ශේෂය",
        "என் இருப்பு",
    ),
    "financial_action": (
        "transfer money",
        "send money",
        "cancel transfer",
        "cancel my transfer",
        "cancel a transfer",
        "cancel panna",
        "reverse transaction",
        "reverse my transaction",
        "close my account",
        "open an account for me",
        "pay this",
        "මුදල් මාරු",
        "பணம் அனுப்பு",
    ),
}


def route_safety(context: QueryContext) -> RouteDecision:
    text = context.original_query.casefold()
    matches = tuple(name for name, terms in RULES.items() if any(term in text for term in terms))
    return RouteDecision(
        bool(matches), matches[0] if matches else None, tuple(dict.fromkeys(matches))
    )
