"""Tests for the evaluate route (A5).

Covers:
1. POST /api/evaluate returns SSE stream (text/event-stream content type)
2. GET /api/result/{job_id} returns 404 for unknown job
3. Health endpoint still works after router mount
4. POST /api/evaluate with invalid scenario returns 400
5. GET /api/result/{job_id} returns 202 while job is still running
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

from httpx import ASGITransport, AsyncClient

from meridian.api.app import app
from meridian.api.jobs.models import CandidateInput, JobCreate

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import pytest

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def _make_job_create(*, scenario: str = "digital_transformation") -> dict:
    """Build a minimal POST /api/evaluate request body."""
    return {
        "jd_text": "Chief Technology Officer required for digital transformation.",
        "candidates": [
            {"name": "Alice", "cv_text": "10 years of enterprise software delivery."},
        ],
        "scenario": scenario,
        "provider": "anthropic",
        "model": None,
    }


def _make_mock_llm_client() -> MagicMock:
    """Build a mock LLM client that satisfies the LLMClient protocol."""
    mock = MagicMock()
    mock.complete = AsyncMock(return_value='{"requirements": []}')
    return mock


async def _mock_evaluate_pipeline_stream(
    jd_text: str,
    candidates: list[Any],
    scenario: Any,
    llm_client: Any,
    job_id: str,
) -> AsyncIterator[Any]:
    """Minimal stub that yields a single COMPLETE event and returns."""
    from meridian.api.sse.events import SSEEvent, SSEEventType

    yield SSEEvent(
        event=SSEEventType.COMPLETE,
        data={
            "job_id": job_id,
            "elapsed_seconds": 0.1,
            "result_summary": "1 candidates evaluated: Alice",
        },
    )


# ---------------------------------------------------------------------------
# Test: health endpoint still works after router mount
# ---------------------------------------------------------------------------


async def test_health_endpoint_still_works_after_router_mount() -> None:
    """Health endpoint must remain reachable after the evaluate router is mounted."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Test: POST /api/evaluate returns 200 with text/event-stream
# ---------------------------------------------------------------------------


async def test_post_evaluate_returns_sse_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/evaluate should return 200 with text/event-stream content type."""
    monkeypatch.setattr(
        "meridian.api.routes.evaluate.create_llm_client",
        lambda provider, model: _make_mock_llm_client(),
    )
    monkeypatch.setattr(
        "meridian.api.routes.evaluate.evaluate_pipeline_stream",
        _mock_evaluate_pipeline_stream,
    )

    transport = ASGITransport(app=app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as client,
        client.stream(
            "POST",
            "/api/evaluate",
            json=_make_job_create(),
        ) as response,
    ):
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type


# ---------------------------------------------------------------------------
# Test: POST /api/evaluate response contains X-Job-Id header
# ---------------------------------------------------------------------------


async def test_post_evaluate_response_has_job_id_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/evaluate should return X-Job-Id header with a UUID."""
    monkeypatch.setattr(
        "meridian.api.routes.evaluate.create_llm_client",
        lambda provider, model: _make_mock_llm_client(),
    )
    monkeypatch.setattr(
        "meridian.api.routes.evaluate.evaluate_pipeline_stream",
        _mock_evaluate_pipeline_stream,
    )

    transport = ASGITransport(app=app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as client,
        client.stream(
            "POST",
            "/api/evaluate",
            json=_make_job_create(),
        ) as response,
    ):
        assert response.status_code == 200
        assert "x-job-id" in response.headers
        job_id = response.headers["x-job-id"]
        # Must be a non-empty string (UUID)
        assert len(job_id) == 36


# ---------------------------------------------------------------------------
# Test: POST /api/evaluate with invalid scenario returns 400
# ---------------------------------------------------------------------------


async def test_post_evaluate_invalid_scenario_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/evaluate with an unrecognised scenario name must return 400."""
    monkeypatch.setattr(
        "meridian.api.routes.evaluate.create_llm_client",
        lambda provider, model: _make_mock_llm_client(),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/evaluate",
            json=_make_job_create(scenario="NOT_A_REAL_SCENARIO"),
        )
    assert response.status_code == 400
    assert "NOT_A_REAL_SCENARIO" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Test: GET /api/result/{job_id} returns 404 for unknown job
# ---------------------------------------------------------------------------


async def test_get_result_unknown_job_returns_404() -> None:
    """GET /api/result/{job_id} must return 404 when the job_id does not exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/result/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Test: GET /api/result/{job_id} returns 202 while job is still running
# ---------------------------------------------------------------------------


async def test_get_result_running_job_returns_202() -> None:
    """GET /api/result/{job_id} must return 202 when the job exists but is not complete.

    Seeds the job manager directly so no actual pipeline is needed.
    """
    from meridian.api.jobs.manager import JobManager
    from meridian.api.jobs.models import JobStatus

    # Build a fresh manager and create a job, then set it to RUNNING
    manager = JobManager()
    job_create = JobCreate(
        jd_text="Test JD text.",
        candidates=[CandidateInput(name="Alice", cv_text="CV text.")],
        scenario="digital_transformation",
    )
    job_id = await manager.create_job(job_create)
    await manager.update_status(job_id, JobStatus.RUNNING)

    # Monkeypatch the module-level _job_manager used by the route
    import meridian.api.routes.evaluate as evaluate_module

    original_manager = evaluate_module._job_manager
    evaluate_module._job_manager = manager
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/result/{job_id}")
        assert response.status_code == 202
    finally:
        evaluate_module._job_manager = original_manager


# ---------------------------------------------------------------------------
# Test: SSE stream body contains valid event lines
# ---------------------------------------------------------------------------


async def test_post_evaluate_stream_body_contains_sse_events(monkeypatch: pytest.MonkeyPatch) -> None:
    """The SSE stream body must contain at least one 'event:' and 'data:' line."""
    monkeypatch.setattr(
        "meridian.api.routes.evaluate.create_llm_client",
        lambda provider, model: _make_mock_llm_client(),
    )
    monkeypatch.setattr(
        "meridian.api.routes.evaluate.evaluate_pipeline_stream",
        _mock_evaluate_pipeline_stream,
    )

    transport = ASGITransport(app=app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as client,
        client.stream(
            "POST",
            "/api/evaluate",
            json=_make_job_create(),
        ) as response,
    ):
        assert response.status_code == 200
        body = await response.aread()

    text = body.decode()
    assert "event:" in text
    assert "data:" in text
    assert "complete" in text  # SSEEventType.COMPLETE value
