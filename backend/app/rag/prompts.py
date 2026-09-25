from app.rag.types import Evidence, QueryContext

SYSTEM_PROMPT = """You answer a customer about the banking-support issue described in their ticket.
Use ONLY the numbered evidence supplied. Never invent or infer fees, rates, limits, eligibility,
policy, balances, transaction status, or completed actions. Do not request secrets, PINs, OTPs,
passwords, or full account/card numbers. Match the requested language, including romanized
Sinhala/Tamil when requested. Every factual claim must end with one or more evidence markers
exactly like [E1]. If evidence is insufficient, output exactly INSUFFICIENT_EVIDENCE.
Never claim an action was performed. Keep policies separated by institution. Be clear that the
answer is general policy guidance derived from approved sources, not confirmation of account activity."""

CITATION_FORMAT_REMINDER = """
Citation format is mandatory: every paragraph and every numbered or bulleted list item
that contains a factual statement must end with its own evidence marker. Do not put one
marker only at the end of a list. Example: `1. Identity document. [E1]`.
"""


def build_prompt(
    context: QueryContext,
    evidence: list[Evidence],
    ticket_context: str | None = None,
) -> tuple[str, str]:
    blocks = []
    for index, item in enumerate(evidence, 1):
        blocks.append(
            f"[E{index}] institution={item.institution}; source={item.title}; "
            f"version={item.version}; reviewed={item.review_date.isoformat()}; chunk={item.chunk_id}\n{item.text}"
        )
    user = (
        f"Ticket context: {ticket_context or context.original_query}\n"
        f"Original query (customer's current question): {context.original_query}\nNormalized retrieval query: {context.normalized_query}\n"
        f"Required response language: {context.language.value}\nInstitution scope: {context.institution or 'regulator/general only'}\n\n"
        "Evidence:\n" + "\n\n".join(blocks)
    )
    return SYSTEM_PROMPT + CITATION_FORMAT_REMINDER, user


def build_citation_retry_prompt(
    context: QueryContext,
    evidence: list[Evidence],
    previous_answer: str,
    ticket_context: str | None = None,
) -> tuple[str, str]:
    system, user = build_prompt(context, evidence, ticket_context=ticket_context)
    return (
        system
        + "\nYour previous draft failed citation-format validation. Rewrite the complete answer "
        "using only the same evidence and obey the citation rule exactly.",
        user + f"\n\nInvalid previous draft:\n{previous_answer}",
    )
