"""Tests for the Meridian API application skeleton."""

import pytest
from httpx import ASGITransport, AsyncClient

from meridian.api.app import app


@pytest.mark.asyncio
async def test_health_returns_200_and_ok() -> None:
    """Health endpoint returns HTTP 200 with {status: ok}."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_cors_headers_present() -> None:
    """CORS middleware injects access-control headers on responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"
