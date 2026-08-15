import asyncio
from dataclasses import replace
from typing import Any, cast

from app.rag.types import Evidence


class BGEM3Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3") -> None:
        try:
            from FlagEmbedding import BGEM3FlagModel  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install Swift with the 'rag' extra to use BGE-M3") from exc
        self._model: Any = BGEM3FlagModel(model_name, use_fp16=False)

    async def embed_query(self, text: str) -> list[float]:
        result = await asyncio.to_thread(self._model.encode, [text])
        return cast(list[float], result["dense_vecs"][0].tolist())


class FlashRankReranker:
    def __init__(self) -> None:
        try:
            from flashrank import Ranker  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("Install Swift with the 'rag' extra to use FlashRank") from exc
        self._ranker: Any = Ranker()

    async def rerank(self, query: str, evidence: list[Evidence]) -> list[Evidence]:
        from flashrank import RerankRequest
        passages = [{"id": item.chunk_id, "text": item.text} for item in evidence]
        results = await asyncio.to_thread(self._ranker.rerank, RerankRequest(query=query, passages=passages))
        by_id = {item.chunk_id: item for item in evidence}
        return [replace(by_id[str(row["id"])], rerank_score=float(row["score"])) for row in results]
