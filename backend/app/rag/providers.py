import asyncio
import random
from typing import Any

import httpx

from app.rag.types import LLMProvider

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_HONORED_RETRY_AFTER = 5.0


class ProviderError(RuntimeError):
    pass


def _retry_delay(response: httpx.Response, attempt: int, base_delay: float) -> float | None:
    """None means the wait is longer than a customer-facing request should hold — fail over instead."""
    header = response.headers.get("retry-after")
    if header:
        try:
            requested: float = float(header)
        except ValueError:
            requested = base_delay * (2.0**attempt)
        return None if requested > MAX_HONORED_RETRY_AFTER else requested
    return base_delay * (2.0**attempt) + random.uniform(0, base_delay)


async def _post_with_retry(
    client: httpx.AsyncClient, url: str, *, max_retries: int, base_delay: float, **kwargs: Any
) -> httpx.Response:
    attempt = 0
    while True:
        try:
            response = await client.post(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in RETRYABLE_STATUS or attempt >= max_retries:
                raise
            delay = _retry_delay(exc.response, attempt, base_delay)
            if delay is None:
                raise
        except httpx.TransportError:
            if attempt >= max_retries:
                raise
            delay = base_delay * (2.0**attempt)
        attempt += 1
        await asyncio.sleep(delay)


class GroqProvider:
    name = "groq"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 20.0,
        max_retries: int = 2,
        retry_base_delay: float = 0.5,
    ) -> None:
        self.api_key, self.model, self.timeout = api_key, model, timeout
        self.max_retries, self.retry_base_delay = max_retries, retry_base_delay

    async def generate(self, *, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if self.model.startswith("qwen/"):
            payload["reasoning_format"] = "hidden"
            payload["reasoning_effort"] = "none"
            payload["max_completion_tokens"] = 2048
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await _post_with_retry(
                    client,
                    "https://api.groq.com/openai/v1/chat/completions",
                    max_retries=self.max_retries,
                    base_delay=self.retry_base_delay,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                return str(response.json()["choices"][0]["message"]["content"]).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Groq generation failed") from exc


class GeminiProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 20.0,
        max_retries: int = 2,
        retry_base_delay: float = 0.5,
    ) -> None:
        self.api_key, self.model, self.timeout = api_key, model, timeout
        self.max_retries, self.retry_base_delay = max_retries, retry_base_delay

    async def generate(self, *, system: str, user: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await _post_with_retry(
                    client,
                    url,
                    max_retries=self.max_retries,
                    base_delay=self.retry_base_delay,
                    # Header, not ?key= — a query-string key leaks into request logs and traces.
                    headers={"x-goog-api-key": self.api_key},
                    json={
                        "system_instruction": {"parts": [{"text": system}]},
                        "contents": [{"role": "user", "parts": [{"text": user}]}],
                        "generationConfig": {"temperature": 0},
                    },
                )
                return str(response.json()["candidates"][0]["content"]["parts"][0]["text"]).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Gemini generation failed") from exc


class FallbackProvider:
    name = "groq_with_gemini_fallback"

    def __init__(self, primary: LLMProvider, fallback: LLMProvider | None) -> None:
        self.primary, self.fallback = primary, fallback
        self.last_provider = primary.name

    async def generate(self, *, system: str, user: str) -> str:
        try:
            answer = await self.primary.generate(system=system, user=user)
            self.last_provider = self.primary.name
            return answer
        except ProviderError:
            if not self.fallback:
                raise
            answer = await self.fallback.generate(system=system, user=user)
            self.last_provider = self.fallback.name
            return answer
