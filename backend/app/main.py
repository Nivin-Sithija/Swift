import uuid
from collections.abc import Awaitable, Callable

import logfire
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.api.v1.routes import router
from app.core.config import get_settings

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    identifier = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = identifier
    response = await call_next(request)
    response.headers["x-request-id"] = identifier
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
