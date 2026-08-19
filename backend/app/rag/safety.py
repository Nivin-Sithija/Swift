import re

from app.rag.types import QueryContext, RouteDecision

RULES: dict[str, tuple[str, ...]] = {
    "fraud_or_dispute": ("fraud", "scam", "dispute", "chargeback", "not my transaction", "not recognise", "unauthori", "වංච", "මගේ නොවේ", "මම නොකළ", "மோசடி", "என்னுடையது அல்ல"),
    "lost_or_stolen_action": ("lost card", "stolen card", "block my card", "freeze my card", "card eka nathi", "කාඩ්පත නැති", "அட்டை தொலை", "card tholainju"),
    "unauthorized_access": ("account hacked", "logged in to my account", "otp stolen", "password stolen", "ගිණුමට ඇතුළු", "கணக்கு hack"),
    "private_account_data": ("my balance", "account balance", "my statement", "my account number", "transaction history", "මගේ ශේෂය", "என் இருப்பு"),
    "financial_action": ("transfer money", "send money", "cancel transfer", "cancel my transfer", "cancel a transfer", "cancel panna", "reverse transaction", "reverse my transaction", "close my account", "open an account for me", "pay this", "මුදල් මාරු", "பணம் அனுப்பு"),
}


def route_safety(context: QueryContext) -> RouteDecision:
    text = context.original_query.casefold()
    matches = tuple(name for name, terms in RULES.items() if any(term in text for term in terms))
    priority = (context.priority or "").casefold()
    intent = re.sub(r"[_-]+", " ", (context.intent or "").casefold())
    if any(term in intent for term in ("fraud", "cash withdrawal dispute", "card stolen", "cash withdrawal not recognised")):
        matches += ("sensitive_intent",)
    if priority in {"high", "critical", "urgent"}:
        matches += ("high_priority",)
    return RouteDecision(bool(matches), matches[0] if matches else None, tuple(dict.fromkeys(matches)))
