import httpx

from app.rag.types import LLMProvider


class ProviderError(RuntimeError):
    pass


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str, timeout: float = 20.0) -> None:
        self.api_key, self.model, self.timeout = api_key, model, timeout

    async def generate(self, *, system: str, user: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "temperature": 0, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                )
                response.raise_for_status()
                return str(response.json()["choices"][0]["message"]["content"]).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Groq generation failed") from exc


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float = 20.0) -> None:
        self.api_key, self.model, self.timeout = api_key, model, timeout

    async def generate(self, *, system: str, user: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, params={"key": self.api_key}, json={
                    "system_instruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"temperature": 0},
                })
                response.raise_for_status()
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
