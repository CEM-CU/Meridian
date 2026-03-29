"""Meridian API — C-Suite Decision Intelligence Tool.

FastAPI application serving the evaluation pipeline via SSE streams.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from meridian.api.routes.evaluate import router as evaluate_router
from meridian.api.routes.scenarios import router as scenarios_router
from meridian.api.routes.upload import router as upload_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup/shutdown hooks."""
    # Future: initialise shared resources (e.g. LLM client pool) here
    yield
    # Future: clean up shared resources here


app = FastAPI(
    title="Meridian API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


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
