"""Route-specific abuse budgets with Redis enforcement and a local fallback."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass

import jwt
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Limit:
    name: str
    maximum: int
    window_seconds: int


LIMITS = {
    ("POST", "/api/v1/auth/login"): Limit("login", 20, 300),
    ("POST", "/api/v1/auth/register"): Limit("register", 20, 300),
    ("POST", "/api/v1/tickets"): Limit("ticket_create", 25, 300),
}


def limit_for(method: str, path: str) -> Limit | None:
    exact = LIMITS.get((method, path))
    if exact:
        return exact
    if method == "POST" and path.endswith("/attachments") and "/api/v1/tickets/" in path:
        return Limit("attachment_upload", 15, 300)
    if method == "POST" and path.endswith("/assistance") and "/api/v1/tickets/" in path:
        return Limit("assistance", 10, 300)
    return None


class RateLimiter:
    def __init__(self, redis_url: str, *, use_redis: bool) -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True) if use_redis else None
        self._memory: dict[str, tuple[int, float]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def identity(client_host: str, authorization: str | None) -> str:
        # Never retain a bearer token in a limiter key or log. Authenticated routes
        # use the stable subject claim; anonymous routes use source IP.
        if authorization:
            scheme, _, token = authorization.partition(" ")
            if scheme.casefold() == "bearer" and token:
                try:
                    subject = str(decode_access_token(token)["sub"])
                    return "user:" + subject
                except (jwt.InvalidTokenError, KeyError, ValueError):
                    pass
            return "auth:" + hashlib.sha256(authorization.encode()).hexdigest()[:24]
        return "ip:" + client_host

    async def hit(self, limit: Limit, identity: str) -> tuple[bool, int]:
        key = f"swift:rate:{limit.name}:{identity}"
        if self._redis is not None:
            try:
                count = int(await self._redis.incr(key))
                if count == 1:
                    await self._redis.expire(key, limit.window_seconds)
                ttl = max(1, int(await self._redis.ttl(key)))
                return count <= limit.maximum, ttl
            except RedisError:
                # A limiter outage must not turn into unlimited traffic. The local
                # fallback retains protection for this process and emits diagnostics.
                logger.exception("Redis rate limiter unavailable; using process-local fallback")
        return await self._memory_hit(key, limit)

    async def _memory_hit(self, key: str, limit: Limit) -> tuple[bool, int]:
        now = time.monotonic()
        async with self._lock:
            count, expires = self._memory.get(key, (0, now + limit.window_seconds))
            if expires <= now:
                count, expires = 0, now + limit.window_seconds
            count += 1
            self._memory[key] = (count, expires)
        retry_after = max(1, int(expires - now))
        return count <= limit.maximum, retry_after

    def reset_memory(self) -> None:
        self._memory.clear()
