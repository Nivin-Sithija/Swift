from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Protocol


class ConsumerLanguage(StrEnum):
    english = "english"
    sinhala = "sinhala"
    tamil = "tamil"
    singlish = "singlish"
    tamilish = "tamilish"
    unknown = "unknown"


@dataclass(frozen=True)
class QueryContext:
    original_query: str
    normalized_query: str
    language: ConsumerLanguage
    institution: str | None
    category: str | None = None
    intent: str | None = None
    sentiment: str | None = None
    priority: str | None = None


@dataclass(frozen=True)
class Evidence:
    chunk_id: str
    source_id: str
    title: str
    source_url: str
    institution: str
    category: str
    language: str
    source_authority: str
    version: str
    review_date: date
    approval_status: str
    chunk_index: int
    text: str
    dense_score: float = 0.0
    lexical_score: float = 0.0
    fused_score: float = 0.0
    rerank_score: float = 0.0
    is_neighbor: bool = False


@dataclass(frozen=True)
class Citation:
    marker: str
    source_id: str
    title: str
    institution: str
    url: str
    version: str
    review_date: date
    chunk_ids: tuple[str, ...]


@dataclass(frozen=True)
class RouteDecision:
    escalate: bool
    reason: str | None = None
    matched_rules: tuple[str, ...] = ()


@dataclass(frozen=True)
class RetrievalResult:
    evidence: list[Evidence]
    confidence: float
    diagnostics: dict[str, float | int | str] = field(default_factory=dict)


class Embedder(Protocol):
    async def embed_query(self, text: str) -> list[float]: ...


class Reranker(Protocol):
    async def rerank(self, query: str, evidence: list[Evidence]) -> list[Evidence]: ...


class LLMProvider(Protocol):
    name: str
    async def generate(self, *, system: str, user: str) -> str: ...
