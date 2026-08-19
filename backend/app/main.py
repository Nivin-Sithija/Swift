import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.api.v1.routes import router
from app.core.config import get_settings

settings = get_settings()
settings.storage_root.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="Swift Ticket Management API", version="1.0.0")
app.mount("/attachments", StaticFiles(directory=str(settings.storage_root)), name="attachments")
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
