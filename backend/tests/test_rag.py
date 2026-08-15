from datetime import date

import pytest

from app.rag.citations import build_citations, citations_are_valid
from app.rag.evaluation import ndcg_at_k, recall_at_k, reciprocal_rank
from app.rag.languages import detect_consumer_language, normalize_query
from app.rag.models import HuggingFaceEmbedder, build_embedder
from app.rag.retrieval import PostgresHybridRetriever, evidence_confidence, reciprocal_rank_fusion
from app.rag.safety import route_safety
from app.rag.service import ConsumerRAGService
from app.rag.types import ConsumerLanguage, Evidence, QueryContext, RetrievalResult


def evidence(chunk_id: str, institution: str = "Commercial Bank") -> Evidence:
    return Evidence(chunk_id, "SRC-1", "Savings", "https://bank.example/savings", institution,
                    "accounts", "english", "bank_official", "1.0", date(2026, 7, 29),
                    "approved", 0, "Minimum opening deposit is listed here.",
                    dense_score=0.9, rerank_score=0.9)


@pytest.mark.parametrize("query,priority", [
    ("This is fraud", "medium"), ("cancel my transfer", "medium"),
    ("What is my balance?", "medium"), ("routine question", "critical"),
    ("මම නොකළ ගනුදෙනුවක්", "medium"), ("transfer ah cancel panna venum", "medium"),
])
def test_safety_router_escalates(query: str, priority: str) -> None:
    context = QueryContext(query, query, ConsumerLanguage.english, "Commercial Bank", priority=priority)
    assert route_safety(context).escalate


def test_safety_router_allows_routine_information() -> None:
    context = QueryContext("What documents are required?", "What documents are required?",
                           ConsumerLanguage.english, "Commercial Bank", priority="low")
    assert not route_safety(context).escalate


def test_rrf_deduplicates_and_rewards_shared_results() -> None:
    a, b, c = evidence("a"), evidence("b"), evidence("c")
    fused = reciprocal_rank_fusion([[a, b], [b, c]])
    assert [item.chunk_id for item in fused] == ["b", "a", "c"]
    assert len({item.chunk_id for item in fused}) == 3


def test_confidence_uses_evidence_quality() -> None:
    assert evidence_confidence([evidence("a")]) >= 0.8
    assert evidence_confidence([]) == 0


def test_citations_preserve_source_metadata() -> None:
    item = evidence("a")
    answer = "The document lists the requirement. [E1]"
    assert citations_are_valid(answer, [item])
    citation = build_citations(answer, [item])[0]
    assert citation.source_id == "SRC-1"
    assert citation.chunk_ids == ("a",)
    assert not citations_are_valid("Unsupported claim", [item])
    assert citations_are_valid("Required documents:\n1. ID\n2. Address proof [E1]", [item])
    assert not citations_are_valid("Supported claim [E1]\n\nSeparate unsupported claim", [item])


def test_multilingual_detection_and_normalization() -> None:
    assert detect_consumer_language("mage account eka") == ConsumerLanguage.singlish
    assert detect_consumer_language("enna panna mudiyala") == ConsumerLanguage.tamilish
    assert detect_consumer_language("எனது கணக்கு") == ConsumerLanguage.tamil
    assert normalize_query("  fee\u00a0 details ") == "fee details"


class FakeRetriever:
    def __init__(self, result: RetrievalResult) -> None:
        self.result = result
    async def retrieve(self, _context: QueryContext) -> RetrievalResult:
        return self.result


class FakeLLM:
    name = "fake"
    async def generate(self, *, system: str, user: str) -> str:
        assert "ONLY" in system and "Original query" in user
        return "The required documents are in the official source. [E1]"


@pytest.mark.asyncio
async def test_low_confidence_refuses_without_calling_generation() -> None:
    service = ConsumerRAGService(FakeRetriever(RetrievalResult([], 0.2)), FakeLLM())
    result = await service.assist(query="What documents are required?", institution="Commercial Bank")
    assert result.route == "human_escalation"
    assert result.draft is None


@pytest.mark.asyncio
async def test_grounded_result_is_agent_approval_draft() -> None:
    service = ConsumerRAGService(FakeRetriever(RetrievalResult([evidence("a")], 0.9)), FakeLLM())
    result = await service.assist(query="What documents are required?", institution="Commercial Bank")
    assert result.route == "rag_draft"
    assert result.approval_required is True
    assert result.citations[0].source_id == "SRC-1"


def test_retrieval_metrics() -> None:
    assert recall_at_k(["a", "b"], {"b"}, 2) == 1
    assert reciprocal_rank(["a", "b"], {"b"}) == 0.5
    assert 0 < ndcg_at_k(["a", "b"], {"b"}, 2) < 1


class EmptyRows:
    def mappings(self) -> "EmptyRows":
        return self
    def all(self) -> list[object]:
        return []


class CapturingDB:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
    async def execute(self, _statement: object, params: dict[str, object]) -> EmptyRows:
        self.calls.append(params)
        return EmptyRows()


class FakeEmbedder:
    async def embed_query(self, _text: str) -> list[float]:
        return [0.0]


class FakeReranker:
    async def rerank(self, _query: str, items: list[Evidence]) -> list[Evidence]:
        return items


@pytest.mark.asyncio
async def test_institution_filter_is_passed_to_every_retrieval_channel() -> None:
    db = CapturingDB()
    retriever = PostgresHybridRetriever(db, FakeEmbedder(), FakeReranker())  # type: ignore[arg-type]
    context = QueryContext("fees", "fees", ConsumerLanguage.english, "People's Bank")
    await retriever.retrieve(context)
    assert len(db.calls) == 2
    assert all(call["institution"] == "People's Bank" for call in db.calls)


class FakeHFResponse:
    def raise_for_status(self) -> None:
        return None
    def json(self) -> list[list[float]]:
        return [[0.25, 0.75]]


class FakeHFClient:
    async def __aenter__(self) -> "FakeHFClient":
        return self
    async def __aexit__(self, *_args: object) -> None:
        return None
    async def post(self, url: str, **kwargs: object) -> FakeHFResponse:
        assert url.endswith("/BAAI/bge-m3/pipeline/feature-extraction")
        assert kwargs["json"] == {"inputs": "hello"}
        return FakeHFResponse()


@pytest.mark.asyncio
async def test_huggingface_embedder_flattens_and_validates_vector(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.rag.models.httpx.AsyncClient", lambda **_kwargs: FakeHFClient())
    embedder = HuggingFaceEmbedder(token="test-token", dimensions=2)
    assert await embedder.embed_query("hello") == [0.25, 0.75]


def test_hosted_embedder_requires_token() -> None:
    with pytest.raises(RuntimeError, match="SWIFT_HUGGINGFACE_TOKEN"):
        build_embedder(
            provider="huggingface", model_name="BAAI/bge-m3", dimensions=1024, timeout=20
        )
