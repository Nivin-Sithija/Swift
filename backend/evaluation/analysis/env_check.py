"""Pre-flight for the live lane: probe every external dependency and say what is missing.

The live diagnostics need four things that the offline lane does not: a reachable
pgvector database, an ingested knowledge base, a working embedding provider, and at
least one generation provider. Each fails differently and some fail silently -- a dead
embedding provider degrades to lexical-only retrieval (retrieval.py:49-55) rather than
erroring -- so this checks them one at a time and reports which are actually usable.

Read-only and cheap: one embedding call and one 5-token generation call per provider.
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

from app.core.config import get_settings
from app.rag.models import build_embedder
from app.rag.providers import GeminiProvider, GroqProvider, ProviderError

CHECK = "PASS"
FAIL = "FAIL"
WARN = "WARN"


def _database_url() -> str | None:
    """Settings first: pydantic-settings loads backend/.env, so the shell need not export it."""
    configured = str(get_settings().database_url or "")
    return configured or os.getenv("SWIFT_DATABASE_URL") or os.getenv("DATABASE_URL")


async def check_database() -> dict[str, Any]:
    url = _database_url()
    if not url:
        return {"status": FAIL, "detail": "SWIFT_DATABASE_URL is not set in this shell"}
    # asyncpg speaks the plain URL; strip the SQLAlchemy driver marker if present.
    dsn = re.sub(r"^postgresql\+\w+://", "postgresql://", url)
    redacted = re.sub(r"//[^@]*@", "//***@", dsn)
    try:
        import asyncpg
    except ImportError:
        return {"status": FAIL, "detail": "asyncpg not installed"}
    try:
        conn = await asyncio.wait_for(asyncpg.connect(dsn), timeout=10)
    except Exception as exc:  # noqa: BLE001 - report any connection failure verbatim
        return {"status": FAIL, "url": redacted, "detail": f"{type(exc).__name__}: {exc}"}
    try:
        extensions = [
            row["extname"] for row in await conn.fetch("SELECT extname FROM pg_extension")
        ]
        tables = [
            row["table_name"]
            for row in await conn.fetch(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            )
        ]
        result: dict[str, Any] = {
            "url": redacted,
            "extensions": extensions,
            "pgvector_installed": "vector" in extensions,
            "tables": sorted(tables),
        }
        if "knowledge_chunks" in tables:
            result["chunks"] = await conn.fetchval("SELECT count(*) FROM knowledge_chunks")
            result["chunks_with_embedding"] = await conn.fetchval(
                "SELECT count(embedding) FROM knowledge_chunks"
            )
            result["articles"] = await conn.fetchval("SELECT count(*) FROM knowledge_articles")
        else:
            result["chunks"] = 0
            result["articles"] = 0
        ingested = result.get("chunks_with_embedding", 0) or 0
        result["status"] = CHECK if ingested else WARN
        result["detail"] = (
            f"{result['articles']} articles / {ingested} embedded chunks"
            if ingested
            else "connected, but the knowledge base is not ingested yet (run swift-ingest-kb)"
        )
        return result
    finally:
        await conn.close()


async def check_embedder() -> dict[str, Any]:
    settings = get_settings()
    info = {
        "provider": settings.rag_embedding_provider,
        "model": settings.rag_embedding_model,
        "expected_dimensions": settings.rag_embedding_dimensions,
        "hf_token_set": bool(settings.huggingface_token),
    }
    try:
        embedder = build_embedder(
            provider=settings.rag_embedding_provider,
            model_name=settings.rag_embedding_model,
            dimensions=settings.rag_embedding_dimensions,
            timeout=settings.rag_request_timeout_seconds,
            huggingface_token=settings.huggingface_token,
            huggingface_provider=settings.huggingface_provider,
            huggingface_endpoint_url=settings.huggingface_endpoint_url,
        )
    except Exception as exc:  # noqa: BLE001
        return {**info, "status": FAIL, "detail": f"construction failed: {exc}"}
    try:
        vector = await embedder.embed_query("What documents do I need to open an account?")
    except Exception as exc:  # noqa: BLE001
        return {
            **info,
            "status": FAIL,
            "detail": (
                f"{type(exc).__name__}: {exc} -- retrieval would silently degrade to "
                "lexical-only (retrieval.py:49-55)"
            ),
        }
    return {
        **info,
        "status": CHECK if len(vector) == settings.rag_embedding_dimensions else FAIL,
        "returned_dimensions": len(vector),
        "detail": f"embedded a query into {len(vector)} dimensions",
    }


async def _groq_raw_error(model: str) -> str:
    """GroqProvider collapses every failure into 'Groq generation failed'.

    That is right for a customer-facing path and useless for diagnosis, so replay the
    exact production payload once and surface the real status and body. The qwen branch
    in providers.py:66-91 is reproduced here deliberately -- a 429 on output-tokens-per-
    minute is caused by `max_completion_tokens`, so a probe without it would not see it.
    """
    import httpx

    settings = get_settings()
    payload: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "Reply with the single word OK."},
            {"role": "user", "content": "Reply with the single word OK."},
        ],
    }
    if model.startswith("qwen/"):
        payload |= {
            "reasoning_format": "hidden",
            "reasoning_effort": "none",
            "max_completion_tokens": 2048,
        }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json=payload,
            )
        if response.status_code == 200:
            return "200 on replay (transient failure earlier)"
        body = response.json().get("error", {}).get("message", response.text)
        return f"HTTP {response.status_code}: {body[:220]}"
    except Exception as exc:  # noqa: BLE001
        return f"replay failed: {type(exc).__name__}: {exc}"


async def _probe_provider(name: str, provider: Any, model: str) -> dict[str, Any]:
    try:
        answer = await provider.generate(
            system="Reply with the single word OK.", user="Reply with the single word OK."
        )
    except ProviderError as exc:
        detail = f"ProviderError: {exc}"
        if name == "groq":
            detail += f" | underlying -> {await _groq_raw_error(model)}"
        return {"status": FAIL, "model": model, "detail": detail}
    except Exception as exc:  # noqa: BLE001
        return {"status": FAIL, "model": model, "detail": f"{type(exc).__name__}: {exc}"}
    return {"status": CHECK, "model": model, "detail": f"responded: {answer.strip()[:60]!r}"}


async def check_providers() -> dict[str, Any]:
    settings = get_settings()
    retries, backoff = 0, settings.rag_provider_retry_base_delay_seconds
    results: dict[str, Any] = {}

    if settings.groq_api_key:
        results["groq"] = await _probe_provider(
            "groq",
            GroqProvider(settings.groq_api_key, settings.groq_model, 30.0, retries, backoff),
            settings.groq_model,
        )
    else:
        results["groq"] = {"status": FAIL, "detail": "SWIFT_GROQ_API_KEY is empty"}

    if settings.gemini_api_key:
        results["gemini"] = await _probe_provider(
            "gemini",
            GeminiProvider(settings.gemini_api_key, settings.gemini_model, 30.0, retries, backoff),
            settings.gemini_model,
        )
    else:
        results["gemini"] = {
            "status": WARN,
            "detail": (
                "SWIFT_GEMINI_API_KEY is empty -- no provider fallback, and the LLM judge "
                "falls back to the Groq answer model, so it would grade its own output"
            ),
        }
    return results


async def main() -> None:
    database = await check_database()
    embedder = await check_embedder()
    providers = await check_providers()

    print("=" * 72)
    print("LIVE-LANE ENVIRONMENT CHECK")
    print("=" * 72)
    for label, result in (
        ("database", database),
        ("embedder", embedder),
        ("groq", providers["groq"]),
        ("gemini", providers["gemini"]),
    ):
        print(f"[{result['status']:<4}] {label:<10} {result.get('detail', '')}")
    print()
    if database["status"] != FAIL:
        print(f"       pgvector installed : {database.get('pgvector_installed')}")
        print(f"       articles / chunks  : {database.get('articles')} / {database.get('chunks')}")
    print()

    blockers = [
        name
        for name, result in (
            ("database", database),
            ("embedder", embedder),
            ("groq", providers["groq"]),
        )
        if result["status"] == FAIL
    ]
    print(f"BLOCKERS: {', '.join(blockers) if blockers else 'none -- live lane can run'}")


if __name__ == "__main__":
    asyncio.run(main())
