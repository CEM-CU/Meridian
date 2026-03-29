"""API integration tests (A8).

Tests the full HTTP API surface using httpx.AsyncClient + ASGITransport with
a MockLLMClient injected via monkeypatch. All LLM calls are intercepted; no
real network traffic is made.

Covered:
1. test_full_evaluate_flow          — POST /api/evaluate streams all expected
                                       event types; GET /api/result/{id} → 200
2. test_scenarios_list              — GET /api/scenarios → 5 items, name + desc
3. test_upload_jd_text              — POST /api/upload/jd JSON → 200, correct shape
4. test_upload_cv_text              — POST /api/upload/cv JSON → 200
5. test_evaluate_invalid_scenario   — POST /api/evaluate bad scenario → 400
6. test_result_not_found            — GET /api/result/nonexistent → 404
7. test_health_still_works          — GET /health → 200
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from api.app import app
from api.sse.events import SSEEventType

# ---------------------------------------------------------------------------
# SSE parsing helpers
# ---------------------------------------------------------------------------


def _parse_sse_events(body: str) -> list[tuple[str, dict[str, Any]]]:
    """Parse an SSE response body into a list of (event_type, data) tuples.

    Processes lines sequentially: ``event:`` lines record the current type,
    ``data:`` lines parse the JSON payload and append an entry.

    Args:
        body: Full SSE response body text.

    Returns:
        Ordered list of ``(event_type_str, data_dict)`` tuples.
    """
    lines = body.split("\n")
    events: list[tuple[str, dict[str, Any]]] = []
    event_type: str = ""
    for line in lines:
        if line.startswith("event: "):
            event_type = line[7:].strip()
        elif line.startswith("data: "):
            raw = line[6:].strip()
            if raw:
                try:
                    data: dict[str, Any] = json.loads(raw)
                except json.JSONDecodeError:
                    data = {}
                events.append((event_type, data))
    return events


def _event_types(events: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Extract just the event type strings from a parsed event list."""
    return [et for et, _ in events]


# ---------------------------------------------------------------------------
# Mock LLM factory
# ---------------------------------------------------------------------------


def _make_pipeline_mock_client() -> Any:
    """Return a MockLLMClient pre-loaded with valid JSON for every LLM call.

    Call order for a single-candidate full pipeline:
      1. C1 — extract_requirements
      2. C3 — assess_candidate (one per candidate)
      3. E3 — _run_single_agent x3
      4. E7 — assemble_synthesis (trade_off_statement)

    Returns:
        A configured MockLLMClient instance.
    """
    from shared.llm_client import MockLLMClient

    c1_response = json.dumps(
        {
            "requirements": [
                {
                    "requirement_id": "REQ-01",
                    "text": "Lead digital transformation initiatives",
                    "source_quote": "Lead digital transformation initiatives across the organisation.",
                    "assessable_from_cv": True,
                    "scenario_priority": {
                        "digital_transformation": "high",
                        "post_acquisition": "medium",
                        "turnaround": "medium",
                        "stabilization": "low",
                        "growth": "medium",
                    },
                },
                {
                    "requirement_id": "REQ-02",
                    "text": "Stakeholder engagement experience",
                    "source_quote": "Demonstrated stakeholder engagement at board level.",
                    "assessable_from_cv": True,
                    "scenario_priority": {
                        "digital_transformation": "high",
                        "post_acquisition": "high",
                        "turnaround": "medium",
                        "stabilization": "medium",
                        "growth": "high",
                    },
                },
            ]
        }
    )

    c3_response = json.dumps(
        [
            {
                "requirement_id": "REQ-01",
                "candidate_name": "Alice",
                "rubric_level": "meets",
                "confidence": "high",
                "cv_citation": "Alice delivered ERP rollout across 12 sites.",
            },
            {
                "requirement_id": "REQ-02",
                "candidate_name": "Alice",
                "rubric_level": "exceeds",
                "confidence": "high",
                "cv_citation": "Alice presented quarterly strategy updates to the board.",
            },
        ]
    )

    def _agent_response(role: str) -> str:
        return json.dumps(
            {
                "agent_role": role,
                "claims": [
                    {
                        "text": f"{role}: strong positive signal for Alice",
                        "evidence_basis": {
                            "type": "cv_rubric",
                            "reference": "REQ-01",
                        },
                        "confidence": "high",
                        "candidate_name": "Alice",
                    }
                ],
                "summary": f"{role} agent: assessment complete for Alice.",
                "assessment_mode": "full",
                "unaddressed_flags": [],
            }
        )

    synthesis_response = json.dumps(
        {
            "trade_off_statement": "Alice presents a well-rounded profile for digital transformation.",
        }
    )

    responses = [
        c1_response,
        c3_response,
        _agent_response("role_fit"),
        _agent_response("team_dynamics"),
        _agent_response("risk"),
        synthesis_response,
    ]
    return MockLLMClient(responses)


def _make_job_body(*, scenario: str = "digital_transformation") -> dict[str, Any]:
    """Build a minimal POST /api/evaluate request body.

    Args:
        scenario: Scenario name string to use.

    Returns:
        Dict suitable for use as the JSON body of POST /api/evaluate.
    """
    return {
        "jd_text": (
            "Chief Technology Officer required to lead digital transformation initiatives "
            "across the organisation. Demonstrated stakeholder engagement at board level."
        ),
        "candidates": [
            {
                "name": "Alice",
                "cv_text": (
                    "10 years of enterprise software delivery. "
                    "Delivered ERP rollout across 12 sites. "
                    "Presented quarterly strategy updates to the board."
                ),
                "big_five": {"O": 0.75, "C": 0.80, "E": 0.60, "A": 0.55, "N": 0.30},
                "personality_source": "manual",
            }
        ],
        "scenario": scenario,
        "provider": "anthropic",
        "model": None,
    }


# ---------------------------------------------------------------------------
# Test 1 — full evaluate flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_evaluate_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/evaluate with valid payload streams all expected events.

    Injects a MockLLMClient so no real API calls are made.  Verifies that:
    - The SSE stream contains JOB_CREATED, C1_COMPLETE, C3_CANDIDATE_DONE,
      STAGE_D_COMPLETE, AGENT_COMPLETE (x3), SYNTHESIS_COMPLETE, COMPLETE.
    - job_id is extractable from the first JOB_CREATED event.
    - GET /api/result/{job_id} returns HTTP 200 after the stream completes.
    """
    mock_client = _make_pipeline_mock_client()
    monkeypatch.setattr(
        "api.routes.evaluate.create_llm_client",
        lambda **_kwargs: mock_client,
    )

    transport = ASGITransport(app=app)
    async with (
        AsyncClient(transport=transport, base_url="http://test") as client,
        client.stream("POST", "/api/evaluate", json=_make_job_body()) as response,
    ):
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        body = await response.aread()

    text = body.decode()
    events = _parse_sse_events(text)
    types = _event_types(events)

    # Required event types that must appear
    required = {
        SSEEventType.JOB_CREATED,
        SSEEventType.C1_COMPLETE,
        SSEEventType.C3_CANDIDATE_DONE,
        SSEEventType.STAGE_D_COMPLETE,
        SSEEventType.SYNTHESIS_COMPLETE,
        SSEEventType.COMPLETE,
    }
    for event_type in required:
        assert event_type.value in types, f"Missing expected event: {event_type.value}"

    # At least 3 AGENT_COMPLETE (or AGENT_TIMEOUT) events
    agent_events = [t for t in types if t in (SSEEventType.AGENT_COMPLETE, SSEEventType.AGENT_TIMEOUT)]
    assert len(agent_events) >= 3, f"Expected ≥3 agent events, got {len(agent_events)}: {types}"

    # Extract job_id from the first JOB_CREATED event
    job_created_data = next((d for et, d in events if et == SSEEventType.JOB_CREATED), None)
    assert job_created_data is not None, "No JOB_CREATED event found"
    job_id: str = job_created_data["job_id"]
    assert job_id, "job_id must be a non-empty string"

    # Wait for job to settle then retrieve result
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        result_response = await client.get(f"/api/result/{job_id}")

    assert result_response.status_code == 200, (
        f"GET /api/result/{job_id} returned {result_response.status_code}: {result_response.text}"
    )
    result_data = result_response.json()
    assert result_data["job_id"] == job_id
    assert "result" in result_data or "status" in result_data


# ---------------------------------------------------------------------------
# Test 2 — scenarios list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scenarios_list() -> None:
    """GET /api/scenarios returns HTTP 200, exactly 5 scenarios, each with name and description."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/scenarios")

    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data, "Response must contain 'scenarios' key"
    scenarios = data["scenarios"]
    assert len(scenarios) == 5, f"Expected 5 scenarios, got {len(scenarios)}"

    for item in scenarios:
        assert "name" in item, f"Scenario missing 'name': {item}"
        assert "description" in item, f"Scenario missing 'description': {item}"
        assert isinstance(item["name"], str) and item["name"], "name must be a non-empty string"
        assert isinstance(item["description"], str) and item["description"], "description must be a non-empty string"


# ---------------------------------------------------------------------------
# Test 3 — upload JD text
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_jd_text() -> None:
    """POST /api/upload/jd with JSON text body returns 200 with text, char_count, source=paste."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload/jd",
            json={"text": "Chief Technology Officer required for digital transformation."},
        )

    assert response.status_code == 200
    data = response.json()
    assert "text" in data, "Response must include 'text'"
    assert "char_count" in data, "Response must include 'char_count'"
    assert "source" in data, "Response must include 'source'"
    assert data["source"] == "paste", f"Expected source='paste', got {data['source']!r}"
    assert data["char_count"] > 0, "char_count must be positive"
    assert isinstance(data["text"], str) and data["text"], "text must be a non-empty string"


# ---------------------------------------------------------------------------
# Test 4 — upload CV text
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_cv_text() -> None:
    """POST /api/upload/cv with JSON text body returns 200 with expected structure."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload/cv",
            json={"text": "10 years of enterprise software delivery and board-level presentations."},
        )

    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "char_count" in data
    assert "source" in data
    assert data["source"] == "paste"
    assert data["char_count"] > 0


# ---------------------------------------------------------------------------
# Test 5 — evaluate with invalid scenario
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_invalid_scenario(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/evaluate with an unrecognised scenario name returns HTTP 400.

    The mock LLM client is patched so the test does not fail due to missing
    API keys before scenario validation can reject the request.
    """
    mock_client = _make_pipeline_mock_client()
    monkeypatch.setattr(
        "api.routes.evaluate.create_llm_client",
        lambda **_kwargs: mock_client,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/evaluate",
            json=_make_job_body(scenario="NOT_A_REAL_SCENARIO"),
        )

    assert response.status_code == 400, (
        f"Expected 400 for invalid scenario, got {response.status_code}: {response.text}"
    )
    detail = response.json().get("detail", "")
    assert "NOT_A_REAL_SCENARIO" in detail, f"Error detail should mention the bad scenario name: {detail!r}"


# ---------------------------------------------------------------------------
# Test 6 — result not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_not_found() -> None:
    """GET /api/result/{id} with an unknown job_id returns HTTP 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/result/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404, f"Expected 404 for unknown job, got {response.status_code}: {response.text}"


# ---------------------------------------------------------------------------
# Test 7 — health endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_still_works() -> None:
    """GET /health returns HTTP 200 with status=ok, unaffected by router mounts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
