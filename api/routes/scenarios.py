"""Scenario routes — scenario listing and scenario switch endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from shared.llm_client import create_llm_client
from shared.models.scenarios import ScenarioName

from api.sse.pipeline_stream import _resolve_scenario, switch_scenario_stream
from api.sse.stream import sse_response_generator

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Static scenario metadata
# ---------------------------------------------------------------------------

_SCENARIO_DESCRIPTIONS: dict[ScenarioName, str] = {
    ScenarioName.DIGITAL_TRANSFORMATION: (
        "Evaluates candidates for roles requiring rapid digital change leadership, "
        "technology adoption, and organisational transformation."
    ),
    ScenarioName.POST_ACQUISITION: (
        "Assesses suitability for post-merger integration, cultural alignment, "
        "and cross-functional consolidation challenges."
    ),
    ScenarioName.TURNAROUND: (
        "Focuses on candidates capable of crisis leadership, cost restructuring, "
        "and performance recovery under pressure."
    ),
    ScenarioName.STABILIZATION: (
        "Prioritises operational resilience, process discipline, and steady-state "
        "management over growth or transformation."
    ),
    ScenarioName.GROWTH: (
        "Weights attributes suited to scaling teams, entering new markets, and sustaining high-velocity revenue growth."
    ),
}

# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------


class SwitchRequest(BaseModel):
    """Request body for POST /api/evaluate/switch."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    scenario: str


# ---------------------------------------------------------------------------
# GET /api/scenarios
# ---------------------------------------------------------------------------


@router.get("/scenarios")
async def list_scenarios() -> dict:
    """Return the list of available evaluation scenarios with descriptions.

    Returns:
        Dict with ``scenarios`` key containing a list of objects with
        ``name`` and ``description`` fields.
    """
    return {"scenarios": [{"name": name.value, "description": _SCENARIO_DESCRIPTIONS[name]} for name in ScenarioName]}


# ---------------------------------------------------------------------------
# POST /api/evaluate/switch
# ---------------------------------------------------------------------------


@router.post("/evaluate/switch")
async def post_switch_scenario(body: SwitchRequest) -> StreamingResponse:
    """Switch the active scenario for a completed evaluation job via SSE.

    Looks up the cached pipeline state for ``job_id``, resolves the new
    scenario, and streams C2→D→E re-evaluation events without repeating
    the expensive C1/C3 LLM calls.

    Args:
        body: Validated switch request with ``job_id`` and ``scenario`` name.

    Returns:
        StreamingResponse with media_type ``text/event-stream``.

    Raises:
        HTTPException 400: If the scenario name is invalid.
        HTTPException 404: If the job_id is not found or has no cached state.
        HTTPException 503: If the LLM client cannot be created (missing key).
    """
    from api.routes.evaluate import _job_manager  # avoid circular at module level

    try:
        new_scenario = _resolve_scenario(body.scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cached_state = await _job_manager.get_cached_state(body.job_id)
    if cached_state is None:
        raise HTTPException(
            status_code=404,
            detail=f"No cached state for job {body.job_id!r}. Run /api/evaluate first, or the job may have expired.",
        )

    try:
        llm_client = create_llm_client()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    job = await _job_manager.get_job(body.job_id)
    from_scenario = job.scenario if job is not None else "unknown"

    stream = switch_scenario_stream(
        cached_state=cached_state,
        new_scenario=new_scenario,
        llm_client=llm_client,
        job_id=body.job_id,
        from_scenario=from_scenario,
    )

    return StreamingResponse(
        sse_response_generator(stream),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Job-Id": body.job_id,
        },
    )
