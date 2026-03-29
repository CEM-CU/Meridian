"""Evaluate endpoint — runs the full C→D→E pipeline via SSE stream."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from shared.llm_client import create_llm_client

from api.jobs.manager import JobManager
from api.jobs.models import JobCreate, JobInfo, JobStatus
from api.sse.events import SSEEvent, SSEEventType
from api.sse.pipeline_stream import (
    _convert_candidate_input,
    _resolve_scenario,
    evaluate_pipeline_stream,
)
from api.sse.stream import sse_response_generator

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Module-level job manager (singleton for this process)
# ---------------------------------------------------------------------------

_job_manager = JobManager(max_concurrent=3, ttl_seconds=3600)


# ---------------------------------------------------------------------------
# Stream wrapper: updates job status and collects the last COMPLETE payload
# ---------------------------------------------------------------------------


async def _pipeline_stream_with_tracking(
    job_id: str,
    jd_text: str,
    candidates: list[Any],
    scenario: Any,
    llm_client: Any,
    job_manager: JobManager,
) -> AsyncIterator[SSEEvent]:
    """Wrap evaluate_pipeline_stream to track job status and store results.

    Acquires the concurrency semaphore, updates status to RUNNING at entry,
    then updates to COMPLETED or FAILED when the stream ends.

    Args:
        job_id: UUID string identifying this job.
        jd_text: Raw job description text.
        candidates: Converted CandidateData objects.
        scenario: Resolved ScenarioConfig.
        llm_client: Async LLM client.
        job_manager: JobManager instance for status/result persistence.

    Yields:
        SSEEvent objects from the pipeline.
    """
    final_event_data: dict | None = None
    failed = False

    async with job_manager.acquire_slot():
        await job_manager.update_status(job_id, JobStatus.RUNNING)
        try:
            async for event in evaluate_pipeline_stream(
                jd_text=jd_text,
                candidates=candidates,
                scenario=scenario,
                llm_client=llm_client,
                job_id=job_id,
            ):
                if event.event == SSEEventType.ERROR:
                    failed = True
                    final_event_data = event.data
                elif event.event == SSEEventType.COMPLETE:
                    final_event_data = event.data
                yield event
        except Exception as exc:
            logger.exception("Unhandled error in pipeline stream for job %s: %s", job_id, exc)
            failed = True
            final_event_data = {"job_id": job_id, "error": str(exc)}

    if failed:
        error_msg = str(final_event_data) if final_event_data else "Unknown pipeline error"
        await job_manager.update_status(job_id, JobStatus.FAILED, error=error_msg[:500])
    else:
        await job_manager.update_status(job_id, JobStatus.COMPLETED)
        if final_event_data is not None:
            await job_manager.store_result(job_id, final_event_data)


# ---------------------------------------------------------------------------
# POST /evaluate
# ---------------------------------------------------------------------------


@router.post("/evaluate")
async def post_evaluate(body: JobCreate) -> StreamingResponse:
    """Accept a job create request and return an SSE stream of pipeline events.

    Creates a job in the manager, converts candidates, resolves scenario,
    and streams the full C→D→E pipeline via Server-Sent Events.

    Args:
        body: Validated job creation payload including jd_text, candidates,
              scenario name, and optional LLM provider/model override.

    Returns:
        StreamingResponse with media_type ``text/event-stream``.

    Raises:
        HTTPException 400: If the scenario name is invalid.
        HTTPException 503: If the LLM client cannot be created (missing key).
    """
    try:
        scenario = _resolve_scenario(body.scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        llm_client = create_llm_client(provider=body.provider, model=body.model)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    candidates = _convert_candidate_input(body.candidates)
    job_id = await _job_manager.create_job(body)

    stream = _pipeline_stream_with_tracking(
        job_id=job_id,
        jd_text=body.jd_text,
        candidates=candidates,
        scenario=scenario,
        llm_client=llm_client,
        job_manager=_job_manager,
    )

    return StreamingResponse(
        sse_response_generator(stream),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Job-Id": job_id,
        },
    )


# ---------------------------------------------------------------------------
# GET /result/{job_id}
# ---------------------------------------------------------------------------


@router.get("/result/{job_id}")
async def get_result(job_id: str) -> dict:
    """Return the cached evaluation result for a completed job.

    Args:
        job_id: UUID string of the target job.

    Returns:
        The stored result dict for a COMPLETED job.

    Raises:
        HTTPException 404: If the job_id is not found.
        HTTPException 202: If the job exists but is still running (not completed).
    """
    job: JobInfo | None = await _job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found.")

    if job.status not in (JobStatus.COMPLETED, JobStatus.FAILED):
        raise HTTPException(
            status_code=202,
            detail=f"Job {job_id!r} is still {job.status.value}. Retry later.",
        )

    result = await _job_manager.get_result(job_id)
    if result is None:
        # Job completed but no result stored (e.g. FAILED with no payload)
        return {"job_id": job_id, "status": job.status.value, "error": job.error}

    return {"job_id": job_id, "status": job.status.value, "result": result}
