from dataclasses import dataclass
from typing import Protocol

from app.rag.citations import build_citations
from app.rag.languages import detect_consumer_language, normalize_query
from app.rag.prompts import build_prompt
from app.rag.providers import ProviderError
from app.rag.safety import route_safety
from app.rag.types import Citation, LLMProvider, QueryContext, RetrievalResult
from app.rag.validation import validate_grounding


class Retriever(Protocol):
    async def retrieve(self, context: QueryContext) -> RetrievalResult: ...


@dataclass(frozen=True)
class AssistanceResult:
    route: str
    original_query: str
    normalized_query: str
    language: str
    draft: str | None
    citations: list[Citation]
    confidence: float
    escalation_reason: str | None
    approval_required: bool = False
    provider: str | None = None


class ConsumerRAGService:
    def __init__(self, retriever: Retriever, llm: LLMProvider) -> None:
        self.retriever, self.llm = retriever, llm

    async def assist(self, *, query: str, institution: str | None, category: str | None = None,
                     language: str | None = None, intent: str | None = None,
                     sentiment: str | None = None, priority: str | None = None,
                     ticket_context: str | None = None) -> AssistanceResult:
        detected = detect_consumer_language(query)
        if language:
            detected = type(detected)(language)
        context = QueryContext(query, normalize_query(query), detected, institution, category, intent, sentiment, priority)
        safety = route_safety(context)
        if safety.escalate:
            return self._escalation(context, safety.reason or "safety_policy")
        retrieval = await self.retriever.retrieve(context)
        if not retrieval.evidence:
            return self._escalation(context, "low_evidence_confidence", retrieval.confidence)
        system, user = build_prompt(context, retrieval.evidence, ticket_context=ticket_context)
        try:
            answer = await self.llm.generate(system=system, user=user)
        except ProviderError:
            return self._escalation(context, "generation_provider_unavailable", retrieval.confidence)
        valid, reason = validate_grounding(answer, retrieval.evidence)
        if not valid:
            return self._escalation(context, reason or "grounding_validation_failed", retrieval.confidence)
        return AssistanceResult("rag_draft", query, context.normalized_query, detected.value, answer,
                                build_citations(answer, retrieval.evidence), retrieval.confidence, None,
                                provider=getattr(self.llm, "last_provider", self.llm.name))

    @staticmethod
    def _escalation(context: QueryContext, reason: str, confidence: float = 0.0) -> AssistanceResult:
        return AssistanceResult("human_escalation", context.original_query, context.normalized_query,
                                context.language.value, None, [], confidence, reason)
