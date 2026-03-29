"""Tests for scenario listing and scenario switch endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from meridian.api.app import app
from meridian.models.scenarios import ScenarioName

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ALL_SCENARIO_NAMES = {name.value for name in ScenarioName}


# ---------------------------------------------------------------------------
# GET /api/scenarios
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_scenarios_returns_200() -> None:
    """GET /api/scenarios should return HTTP 200."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/scenarios")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_scenarios_returns_five_scenarios() -> None:
    """GET /api/scenarios must return exactly 5 scenario objects."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/scenarios")
    data = response.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) == 5


@pytest.mark.asyncio
async def test_list_scenarios_has_correct_names() -> None:
    """Each scenario in the list must have a name matching a ScenarioName value."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/scenarios")
    data = response.json()
    returned_names = {item["name"] for item in data["scenarios"]}
    assert returned_names == _ALL_SCENARIO_NAMES


@pytest.mark.asyncio
async def test_list_scenarios_each_item_has_description() -> None:
    """Every scenario object must include a non-empty description string."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/scenarios")
    data = response.json()
    for item in data["scenarios"]:
        assert "description" in item
        assert isinstance(item["description"], str)
        assert len(item["description"]) > 0


# ---------------------------------------------------------------------------
# POST /api/evaluate/switch — 404 cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_switch_returns_404_for_unknown_job_id() -> None:
    """POST /api/evaluate/switch must return 404 when job_id has no cached state."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/evaluate/switch",
            json={"job_id": "00000000-0000-4000-8000-000000000000", "scenario": "growth"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_switch_returns_404_detail_mentions_job_id() -> None:
    """404 detail from switch must reference the unknown job_id."""
    job_id = "aaaaaaaa-0000-4000-8000-000000000000"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/evaluate/switch",
            json={"job_id": job_id, "scenario": "turnaround"},
        )
    assert response.status_code == 404
    detail = response.json().get("detail", "")
    assert job_id in detail


@pytest.mark.asyncio
async def test_switch_returns_400_for_invalid_scenario() -> None:
    """POST /api/evaluate/switch must return 400 when scenario name is invalid."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/evaluate/switch",
            json={"job_id": "00000000-0000-4000-8000-000000000000", "scenario": "not_a_real_scenario"},
        )
    assert response.status_code == 400
