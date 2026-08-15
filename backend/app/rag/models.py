import asyncio
from dataclasses import replace
from typing import Any, cast

import httpx
import numpy as np

from app.rag.types import Embedder, Evidence


class _TokenTypeSessionAdapter:
    """Work around FlashRank 0.2.x omitting required all-zero segment IDs."""

    def __init__(self, session: Any) -> None:
        self._session = session

    def run(self, output_names: Any, input_feed: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
        if "token_type_ids" not in input_feed and "input_ids" in input_feed:
            input_feed = {
                **input_feed,
                "token_type_ids": np.zeros_like(input_feed["input_ids"], dtype=np.int64),
            }
        return self._session.run(output_names, input_feed, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._session, name)


class BGEM3Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        try:
            from FlagEmbedding import BGEM3FlagModel  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install Swift with the 'rag-local' extra to run BGE-M3 locally") from exc
        self._model: Any = BGEM3FlagModel(model_name, use_fp16=False)

    async def embed_query(self, text: str) -> list[float]:
        result = await asyncio.to_thread(self._model.encode, [text])
        return cast(list[float], result["dense_vecs"][0].tolist())


class HuggingFaceEmbedder:
    """BGE-M3 embeddings hosted by HF Inference or a dedicated HF endpoint."""

    def __init__(
        self,
        *,
        token: str,
        model_name: str = "BAAI/bge-m3",
        provider: str = "hf-inference",
        endpoint_url: str | None = None,
        timeout: float = 20.0,
        dimensions: int = 1024,
    ) -> None:
        if not token:
            raise RuntimeError("SWIFT_HUGGINGFACE_TOKEN is required for hosted embeddings")
        if not endpoint_url and provider != "hf-inference":
            raise RuntimeError("Only the hf-inference provider or a dedicated endpoint URL is supported")
        self.dimensions = dimensions
        self.url = endpoint_url or (
            f"https://router.huggingface.co/hf-inference/models/{model_name}"
            "/pipeline/feature-extraction"
        )
        self.token, self.timeout = token, timeout

    async def embed_query(self, text: str) -> list[float]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.url,
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={"inputs": text},
                )
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError("Hosted Hugging Face embedding request failed") from exc
        values: Any = result.tolist() if hasattr(result, "tolist") else result
        while isinstance(values, list) and len(values) == 1 and isinstance(values[0], list):
            values = values[0]
        if not isinstance(values, list) or len(values) != self.dimensions:
            size = len(values) if isinstance(values, list) else 0
            raise RuntimeError(
                f"Hosted embedding returned {size} dimensions; expected {self.dimensions}"
            )
        if not all(isinstance(value, (int, float)) for value in values):
            raise RuntimeError("Hosted embedding response was not a numeric vector")
        return [float(value) for value in values]


def build_embedder(
    *,
    provider: str,
    model_name: str,
    dimensions: int,
    timeout: float,
    huggingface_token: str | None = None,
    huggingface_provider: str = "hf-inference",
    huggingface_endpoint_url: str | None = None,
) -> Embedder:
    if provider == "local":
        return BGEM3Embedder(model_name)
    if provider == "huggingface":
        return HuggingFaceEmbedder(
            token=huggingface_token or "",
            model_name=model_name,
            provider=huggingface_provider,
            endpoint_url=huggingface_endpoint_url,
            timeout=timeout,
            dimensions=dimensions,
        )
    raise RuntimeError(f"Unsupported RAG embedding provider: {provider}")


class FlashRankReranker:
    def __init__(self) -> None:
        try:
            from flashrank import Ranker  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install Swift with the 'rag' extra to use FlashRank") from exc
        self._ranker: Any = Ranker()
        required_inputs = {item.name for item in self._ranker.session.get_inputs()}
        if "token_type_ids" in required_inputs:
            self._ranker.session = _TokenTypeSessionAdapter(self._ranker.session)

    async def rerank(self, query: str, evidence: list[Evidence]) -> list[Evidence]:
        from flashrank import RerankRequest

        if not evidence:
            return []
        passages = [{"id": item.chunk_id, "text": item.text} for item in evidence]
        results = await asyncio.to_thread(self._ranker.rerank, RerankRequest(query=query, passages=passages))
        by_id = {item.chunk_id: item for item in evidence}
        return [replace(by_id[str(row["id"])], rerank_score=float(row["score"])) for row in results]
