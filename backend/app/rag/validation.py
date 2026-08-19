import re

from app.rag.citations import citations_are_valid
from app.rag.types import Evidence

ACTION_CLAIMS = re.compile(r"\b(i|we) (have |successfully )?(transferred|cancelled|reversed|blocked|unblocked|opened|closed|paid)\b", re.I)
SENSITIVE_REQUEST = re.compile(r"\b(send|provide|share) (your )?(pin|otp|password|full card|account number)\b", re.I)


def validate_grounding(answer: str, evidence: list[Evidence]) -> tuple[bool, str | None]:
    if answer.strip() == "INSUFFICIENT_EVIDENCE":
        return False, "model_reported_insufficient_evidence"
    if ACTION_CLAIMS.search(answer):
        return False, "prohibited_action_claim"
    if SENSITIVE_REQUEST.search(answer):
        return False, "sensitive_data_request"
    if not citations_are_valid(answer, evidence):
        return False, "invalid_or_missing_citations"
    return True, None
