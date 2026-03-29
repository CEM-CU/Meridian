"""Pipeline SSE stream generator.

Wraps the C->D->E evaluation pipeline as an async generator of SSEEvents.
Yields progress events at 18+ checkpoints for real-time frontend updates.

Key design: asyncio.as_completed is used for C3 (per-candidate) and E3
(per-agent) so that progress events stream as each unit finishes rather
than waiting for all to complete.

Submodules:
    converters       - input conversion and scenario resolution
    payload_builders - SSE event payload construction
    stage_runners    - per-stage async streaming helpers
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from meridian.api.sse.converters import _convert_candidate_input, _resolve_scenario
from meridian.api.sse.events import (
    C1CompletePayload,
    C1StartedPayload,
    C2CompletePayload,
    C3CandidateDonePayload,
    C3StartedPayload,
    C4CompletePayload,
    CompletePayload,
    ErrorPayload,
    SSEEvent,
    SSEEventType,
    SwitchCompletePayload,
    SwitchStartedPayload,
)
from meridian.api.sse.payload_builders import (
    _assessment_stats,
    _count_cv_flags,
    _count_not_assessable,
    _count_personality_flags,
    _make_stage_d_event,
)
from meridian.api.sse.stage_runners import _stream_c3_candidates, _stream_stage_e_tail

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from meridian.evaluation.scenario_switch import CachedPipelineState
    from meridian.extraction.protocols import LLMClient
    from meridian.models import ScenarioConfig
    from meridian.models.candidates import CandidateData
    from meridian.models.rubric import RubricAssessment

logger = logging.getLogger(__name__)

# Re-export public helpers so existing imports from this module keep working.
__all__ = [
    "_assessment_stats",
    "_convert_candidate_input",
    "_count_cv_flags",
    "_count_not_assessable",
    "_count_personality_flags",
    "_resolve_scenario",
    "evaluate_pipeline_stream",
    "switch_scenario_stream",
]


# ---------------------------------------------------------------------------
# Main pipeline stream generator
# ---------------------------------------------------------------------------


async def evaluate_pipeline_stream(
    jd_text: str,
    candidates: list[CandidateData],
    scenario: ScenarioConfig,
    llm_client: LLMClient,
    job_id: str,
) -> AsyncIterator[SSEEvent]:
    """Async generator yielding SSE events through the full C->D->E pipeline.

    Streams per-candidate (C3) and per-agent (E3) progress via as_completed.
    On any error, yields an ERROR event and returns.

    Args:
        jd_text: Raw job description text.
        candidates: Candidate data objects (already converted from CandidateInput).
        scenario: Active scenario configuration.
        llm_client: Async LLM client.
        job_id: Job identifier for correlation.

    Yields:
        SSEEvent objects at each pipeline checkpoint.
    """
    from datetime import UTC, datetime

    from meridian.derivation.pipeline import run_stage_d
    from meridian.extraction.bridge import bridge_rubric_to_flags
    from meridian.extraction.cv_assessment import _build_priority_order
    from meridian.extraction.jd_extraction import extract_requirements
    from meridian.extraction.priority_resolution import resolve_active_priorities
    from meridian.models.pipeline import StageCOutput

    pipeline_start = time.monotonic()

    try:
        # ------------------------------------------------------------------ Job created
        yield SSEEvent(
            event=SSEEventType.JOB_CREATED,
            data={
                "job_id": job_id,
                "scenario": scenario.name.value,
                "candidate_count": len(candidates),
                "created_at": datetime.now(UTC).isoformat(),
            },
        )

        # ------------------------------------------------------------------ C1: JD extraction
        yield SSEEvent(
            event=SSEEventType.C1_STARTED,
            data=C1StartedPayload(job_id=job_id).model_dump(),
        )
        requirements, extraction_warnings = await asyncio.wait_for(
            extract_requirements(jd_text, llm_client), timeout=60.0
        )
        logger.info("C1 complete: %d requirements", len(requirements))

        yield SSEEvent(
            event=SSEEventType.C1_COMPLETE,
            data=C1CompletePayload(
                requirements=[r.model_dump() for r in requirements],
                cv_assessable=sum(1 for r in requirements if r.assessable_from_cv),
                behavioral=sum(1 for r in requirements if not r.assessable_from_cv),
                warnings=extraction_warnings,
            ).model_dump(),
        )

        # ------------------------------------------------------------------ C2: Priority resolution
        resolve_active_priorities(requirements, scenario)
        yield SSEEvent(
            event=SSEEventType.C2_COMPLETE,
            data=C2CompletePayload(
                scenario=scenario.name.value,
                requirement_count=sum(1 for r in requirements if r.assessable_from_cv),
            ).model_dump(),
        )

        # ------------------------------------------------------------------ C3: Per-candidate streaming
        cv_assessable = [r for r in requirements if r.assessable_from_cv]
        priority_order = _build_priority_order(cv_assessable, scenario)

        yield SSEEvent(
            event=SSEEventType.C3_STARTED,
            data=C3StartedPayload(
                candidate_count=len(candidates),
                requirement_count=len(cv_assessable),
            ).model_dump(),
        )

        all_assessments: list[RubricAssessment] = []
        done_count = 0
        total = len(candidates)

        async for candidate_name, result in _stream_c3_candidates(
            candidates, cv_assessable, priority_order, llm_client
        ):
            done_count += 1
            all_assessments.extend(result)
            yield SSEEvent(
                event=SSEEventType.C3_CANDIDATE_DONE,
                data=C3CandidateDonePayload(
                    candidate=candidate_name,
                    cells=[a.model_dump() for a in result],
                    stats=_assessment_stats(result),
                    done=done_count,
                    total=total,
                ).model_dump(),
            )

        logger.info("C3 complete: %d assessments", len(all_assessments))

        # ------------------------------------------------------------------ C4: Bridge
        cv_flags = bridge_rubric_to_flags(all_assessments, requirements, scenario.name)
        yield SSEEvent(
            event=SSEEventType.C4_COMPLETE,
            data=C4CompletePayload(
                cv_flag_count=len(cv_flags),
                drop_count=_count_not_assessable(all_assessments),
            ).model_dump(),
        )

        # ------------------------------------------------------------------ Stage D: Deterministic
        stage_c_output = StageCOutput(
            requirements=requirements,
            rubric_assessments=all_assessments,
            candidate_data=candidates,
            scenario=scenario,
        )
        stage_d_output = run_stage_d(stage_c_output, cv_flags)
        yield _make_stage_d_event(stage_d_output)

        # ------------------------------------------------------------------ E1 -> E7: Stage E tail
        async for event in _stream_stage_e_tail(
            stage_d_output=stage_d_output,
            scenario_name_value=scenario.name.value,
            candidate_count=len(candidates),
            llm_client=llm_client,
        ):
            yield event

        # ------------------------------------------------------------------ Complete
        elapsed_total = time.monotonic() - pipeline_start
        candidate_names_str = ", ".join(c.name for c in candidates)
        yield SSEEvent(
            event=SSEEventType.COMPLETE,
            data=CompletePayload(
                job_id=job_id,
                elapsed_seconds=round(elapsed_total, 2),
                result_summary=f"{len(candidates)} candidates evaluated: {candidate_names_str}",
            ).model_dump(),
        )

    except asyncio.CancelledError:
        logger.info("Pipeline stream cancelled for job %s", job_id)
        return
    except Exception as exc:
        logger.exception("Pipeline stream error in job %s: %s", job_id, exc)
        yield SSEEvent(
            event=SSEEventType.ERROR,
            data=ErrorPayload(
                job_id=job_id,
                code="PIPELINE_ERROR",
                message=str(exc)[:500],
                stage=None,
            ).model_dump(),
        )


# ---------------------------------------------------------------------------
# Scenario switch stream generator
# ---------------------------------------------------------------------------


async def switch_scenario_stream(
    cached_state: CachedPipelineState,
    new_scenario: ScenarioConfig,
    llm_client: LLMClient,
    job_id: str,
    from_scenario: str = "unknown",
) -> AsyncIterator[SSEEvent]:
    """Async generator for scenario switch -- skips C1/C3, uses cached state.

    Re-runs C2 -> C4 -> Stage D -> E1 -> E2 -> E3 -> E5 -> E7 using pre-cached
    requirements and rubric assessments from the initial evaluation.

    Args:
        cached_state: Pre-built state from build_cached_state (C1 + C3 results).
        new_scenario: Target scenario configuration to switch to.
        llm_client: Async LLM client for Stage E evaluation.
        job_id: Job identifier for correlation.
        from_scenario: Name of the scenario being switched from.

    Yields:
        SSEEvent objects at each pipeline checkpoint.
    """
    from meridian.derivation.pipeline import run_stage_d
    from meridian.extraction.bridge import bridge_rubric_to_flags
    from meridian.extraction.priority_resolution import resolve_active_priorities
    from meridian.models.pipeline import StageCOutput

    try:
        yield SSEEvent(
            event=SSEEventType.SWITCH_STARTED,
            data=SwitchStartedPayload(
                job_id=job_id,
                from_scenario=from_scenario,
                to_scenario=new_scenario.name.value,
            ).model_dump(),
        )

        # ------------------------------------------------------------------ C2 + C4 (deterministic)
        resolve_active_priorities(cached_state.requirements, new_scenario)
        cv_flags = bridge_rubric_to_flags(
            cached_state.rubric_assessments,
            cached_state.requirements,
            new_scenario.name,
        )
        stage_c_output = StageCOutput(
            requirements=cached_state.requirements,
            rubric_assessments=cached_state.rubric_assessments,
            candidate_data=cached_state.candidates,
            scenario=new_scenario,
        )

        # ------------------------------------------------------------------ Stage D
        stage_d_output = run_stage_d(stage_c_output, cv_flags)
        yield _make_stage_d_event(stage_d_output)

        # ------------------------------------------------------------------ E1 -> E7: Stage E tail
        async for event in _stream_stage_e_tail(
            stage_d_output=stage_d_output,
            scenario_name_value=new_scenario.name.value,
            candidate_count=len(cached_state.candidates),
            llm_client=llm_client,
        ):
            yield event

        # ------------------------------------------------------------------ Switch complete
        yield SSEEvent(
            event=SSEEventType.SWITCH_COMPLETE,
            data=SwitchCompletePayload(
                job_id=job_id,
                new_scenario=new_scenario.name.value,
                reused_rubric_cells=len(cached_state.rubric_assessments),
            ).model_dump(),
        )

    except asyncio.CancelledError:
        logger.info("Scenario switch stream cancelled for job %s", job_id)
        return
    except Exception as exc:
        logger.exception("Scenario switch error in job %s: %s", job_id, exc)
        yield SSEEvent(
            event=SSEEventType.ERROR,
            data=ErrorPayload(
                job_id=job_id,
                code="SWITCH_ERROR",
                message=str(exc)[:500],
                stage=None,
            ).model_dump(),
        )
