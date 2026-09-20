"""Conservative safety routing for account-specific data and financial actions."""

from app.rag.types import QueryContext, RouteDecision

RULES: dict[str, tuple[str, ...]] = {
    "private_account_data": (
        "my balance", "account balance", "my statement", "my account number",
        "transaction history", "මගේ ශේෂය", "මගේ ගිණුම", "என் இருப்பு", "எனது கணக்கு",
        "en balance", "ennoda balance", "mage balance", "statement eka",
        "unauthorized transaction", "transaction i didn't make", "transaction i did not make",
        "මම නොකළ ගනුදෙනුව", "அங்கீகரிக்கப்படாத பரிவர்த்தனை",
        "naan pannatha transaction", "mama nokala ganudenuwa",
    ),
    "financial_action": (
        "transfer money", "send money", "cancel transfer", "cancel my transfer",
        "cancel a transfer", "cancel panna", "reverse transaction",
        "reverse my transaction", "close my account", "open an account for me",
        "pay this", "මුදල් මාරු", "ගිණුම වහන්න", "பணம் அனுப்பு",
        "transfer panna", "account close panna", "salli yawanna",
    ),
}

# The stored classifier intent is id-aligned across all five language tracks.
# Routing on it closes the language-equity gap without pretending a small
# romanization keyword list is a multilingual semantic model.
INTENT_RULES: dict[str, frozenset[str]] = {
    "private_account_data": frozenset({
        "extra_charge_on_statement", "Refund_not_showing_up",
        "balance_not_updated_after_cheque_or_cash_deposit",
        "card_payment_not_recognised", "balance_not_updated_after_bank_transfer",
        "cash_withdrawal_not_recognised", "direct_debit_payment_not_recognised",
        "card_payment_wrong_exchange_rate", "pending_cash_withdrawal",
        "transfer_timing", "top_up_by_cash_or_cheque",
    }),
    "financial_action": frozenset({
        "transfer_into_account", "cancel_transfer", "topping_up_by_card",
        "terminate_account", "beneficiary_not_allowed", "top_up_by_bank_transfer_charge",
        "failed_transfer", "declined_transfer", "pending_transfer", "receiving_money",
    }),
}


def route_safety(context: QueryContext) -> RouteDecision:
    text = f"{context.original_query}\n{context.normalized_query}".casefold()
    matches = [
        name
        for name, terms in RULES.items()
        if any(term.casefold() in text for term in terms)
    ]
    intent = context.intent or context.category
    if intent:
        matches.extend(name for name, intents in INTENT_RULES.items() if intent in intents)
    unique = tuple(dict.fromkeys(matches))
    return RouteDecision(bool(unique), unique[0] if unique else None, unique)
