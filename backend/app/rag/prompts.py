from app.rag.types import Evidence, QueryContext

SYSTEM_PROMPT = """You draft consumer banking support replies for review by a human agent.
Use ONLY the numbered evidence supplied. Never invent or infer fees, rates, limits, eligibility,
policy, balances, transaction status, or completed actions. Do not request secrets, PINs, OTPs,
passwords, or full account/card numbers. Match the requested language, including romanized
Sinhala/Tamil when requested. Every factual claim must end with one or more evidence markers
exactly like [E1]. If evidence is insufficient, output exactly INSUFFICIENT_EVIDENCE.
Never claim an action was performed. Keep policies separated by institution."""


def build_prompt(context: QueryContext, evidence: list[Evidence]) -> tuple[str, str]:
    blocks = []
    for index, item in enumerate(evidence, 1):
        blocks.append(
            f"[E{index}] institution={item.institution}; source={item.title}; "
            f"version={item.version}; reviewed={item.review_date.isoformat()}; chunk={item.chunk_id}\n{item.text}"
        )
    user = (
        f"Original query: {context.original_query}\nNormalized retrieval query: {context.normalized_query}\n"
        f"Required response language: {context.language.value}\nInstitution scope: {context.institution or 'regulator/general only'}\n\n"
        "Evidence:\n" + "\n\n".join(blocks)
    )
    return SYSTEM_PROMPT, user
