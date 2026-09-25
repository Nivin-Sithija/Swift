import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path

import logfire
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.api.v1.routes import router
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter, limit_for

settings = get_settings()
# Unguarded on purpose: without a token this no-ops, so the instrumentation path
# still runs in dev and CI instead of only ever executing in production.
logfire.configure(
    token=settings.logfire_token,
    service_name="swift-backend",
    environment=settings.environment,
    send_to_logfire="if-token-present",
    # Span attributes on the console are for reading traces by eye in dev; production
    # ships them to Logfire instead, where the extra console noise is not wanted.
    console=logfire.ConsoleOptions(verbose=settings.environment == "development"),
)
app = FastAPI(title="Swift Ticket Management API", version="1.0.0")
logfire.instrument_fastapi(app)
logfire.instrument_httpx()
try:
    settings.storage_root.mkdir(parents=True, exist_ok=True)
except OSError:
    if settings.environment not in {"development", "test"}:
        raise
    # A checked-in/container .env may point at /data. Local tooling must remain
    # importable without root-owned container mounts.
    settings.storage_root = Path("storage")
    settings.storage_root.mkdir(parents=True, exist_ok=True)
app.mount("/attachments", StaticFiles(directory=str(settings.storage_root)), name="attachments")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rate_limiter = RateLimiter(
    settings.redis_url,
    use_redis=settings.environment == "production",
)
app.state.rate_limiter = rate_limiter


@app.middleware("http")
async def enforce_rate_limits(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    limit = limit_for(request.method, request.url.path)
    if limit is not None:
        client_host = request.client.host if request.client else "unknown"
        identity = rate_limiter.identity(client_host, request.headers.get("authorization"))
        allowed, retry_after = await rate_limiter.hit(limit, identity)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"code": "rate_limited", "message": "Too many requests"},
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)


@app.middleware("http")
async def request_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    identifier = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = identifier
    response = await call_next(request)
    response.headers["x-request-id"] = identifier
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(Exception)
async def unhandled(request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


app.include_router(router, prefix="/api/v1")
