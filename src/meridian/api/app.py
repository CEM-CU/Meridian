"""Meridian API — C-Suite Decision Intelligence Tool.

FastAPI application serving the evaluation pipeline via SSE streams.
"""

import time
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from meridian.api.routes.evaluate import router as evaluate_router
from meridian.api.routes.scenarios import router as scenarios_router
from meridian.api.routes.upload import router as upload_router

# ---------------------------------------------------------------------------
# In-memory rate limiter (per-IP, sliding window)
# ---------------------------------------------------------------------------

_RATE_LIMIT_REQUESTS: int = 30
_RATE_LIMIT_WINDOW_S: float = 60.0
_request_log: dict[str, list[float]] = defaultdict(list)


def _is_rate_limited(client_ip: str) -> bool:
    """Check if client_ip has exceeded the rate limit in the current window."""
    now = time.monotonic()
    cutoff = now - _RATE_LIMIT_WINDOW_S
    log = _request_log[client_ip]
    # Prune old entries
    _request_log[client_ip] = [t for t in log if t > cutoff]
    if len(_request_log[client_ip]) >= _RATE_LIMIT_REQUESTS:
        return True
    _request_log[client_ip].append(now)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup/shutdown hooks."""
    yield
    _request_log.clear()


app = FastAPI(
    title="Meridian API",
    version="0.1.0",
    lifespan=lifespan,
)

_ALLOWED_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: object) -> Response:
    """Reject requests that exceed the per-IP rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    if request.url.path != "/health" and _is_rate_limited(client_ip):
        return Response(content="Rate limit exceeded", status_code=429)
    return await call_next(request)  # type: ignore[operator]


@app.get("/health")
async def health() -> dict[str, str]:
    """Return API health status."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Router mounting
# ---------------------------------------------------------------------------

app.include_router(evaluate_router, prefix="/api")
app.include_router(scenarios_router, prefix="/api")
app.include_router(upload_router, prefix="/api/upload")
