"""Per-stage streaming helpers for the pipeline SSE stream.

Provides coroutine wrappers and async generators for streaming C3
(per-candidate CV assessment), E3 (per-agent evaluation), and the
full Stage E tail (E1+E2+E3+E5+E7) as reusable async generators
via asyncio.as_completed for real-time progress updates.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

from api.sse.events import (
    AgentsStartedPayload,
    AuditCompletePayload,
    SignalsComputedPayload,
    SSEEvent,
    SSEEventType,
    SynthesisCompletePayload,
    SynthesisStartedPayload,
)
from api.sse.payload_builders import (
    _build_synthesis_candidates_map,
    _count_investigation_questions,
    _make_agent_event,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from shared.models.candidates import CandidateData
    from shared.models.flags import Flag
    from shared.models.requirements import Requirement
    from shared.models.rubric import RubricAssessment
    from stage_c.protocols import LLMClient
    from stage_e.layer1_signals import TensionPair
    from stage_e.schemas import AgentVerdict


# ---------------------------------------------------------------------------
# Tagged coroutine wrapper for as_completed identity tracking
# ---------------------------------------------------------------------------


async def _tagged(key: Any, coro: Any) -> tuple[Any, Any]:
    """Wrap a coroutine to return (key, result) so as_completed can track identity.

    Args:
        key: Arbitrary identifier to associate with the result.
        coro: Coroutine to await.

    Returns:
        Tuple of (key, result).
    """
    result = await coro
    return key, result


# ---------------------------------------------------------------------------
# C3 per-candidate streaming
# ---------------------------------------------------------------------------


async def _stream_c3_candidates(
    candidates: list[CandidateData],
    cv_assessable: list[Requirement],
    priority_order: list[Any],
    llm_client: LLMClient,
) -> AsyncIterator[tuple[str, list[RubricAssessment]]]:
    """Run per-candidate CV assessment with as_completed streaming.

    Args:
        candidates: All candidates to assess.
        cv_assessable: CV-assessable requirements.
        priority_order: Priority-ordered (Requirement, Priority) pairs.
        llm_client: Async LLM client.

    Yields:
        Tuples of (candidate_name, assessments_list) as each candidate finishes.
    """
    from stage_c.cv_assessment import assess_candidate

    tasks = [
        asyncio.create_task(
            _tagged(
                candidate.name,
                assess_candidate(
                    candidate_name=candidate.name,
                    cv_text=candidate.cv_text,
                    requirements=cv_assessable,
                    priority_order=priority_order,
                    llm_client=llm_client,
                ),
            )
        )
        for candidate in candidates
    ]
    try:
        for future in asyncio.as_completed(tasks):
            candidate_name, result = await future
            yield candidate_name, result
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()


# ---------------------------------------------------------------------------
# E3 per-agent streaming
# ---------------------------------------------------------------------------


async def _stream_e3_agents(
    flags: list[Flag],
    tension_map: list[TensionPair],
    candidates: list[CandidateData],
    requirements: list[Requirement],
    assessment_modes: dict[str, str],
    llm_client: LLMClient,
    timeout_seconds: float = 15.0,
) -> AsyncIterator[tuple[str, AgentVerdict | None, float]]:
    """Run 3 evaluation agents with as_completed streaming.

    Args:
        flags: Validated flag set from Layer 1.
        tension_map: Tension pairs from Layer 1.
        candidates: All candidate data.
        requirements: Confirmed JD requirements.
        assessment_modes: Candidate name -> "full" or "partial".
        llm_client: Async LLM client.
        timeout_seconds: Per-agent timeout.

    Yields:
        Tuples of (role_name, verdict_or_none, elapsed_seconds) as each agent finishes.
    """
    from stage_e.layer2_agents.allowlists import filter_flags_for_agent
    from stage_e.layer2_agents.runner import _AGENT_CONFIGS, _run_single_agent

    tasks = []
    start_times: dict[str, float] = {}

    for role, allowlist, prompt_builder in _AGENT_CONFIGS:
        agent_flags = filter_flags_for_agent(flags, allowlist)
        start_times[role.value] = time.monotonic()
        tasks.append(
            asyncio.create_task(
                _tagged(
                    role.value,
                    _run_single_agent(
                        role=role,
                        flags=agent_flags,
                        tension_map=tension_map,
                        candidates=candidates,
                        requirements=requirements,
                        assessment_modes=assessment_modes,
                        prompt_builder=prompt_builder,
                        llm_client=llm_client,
                        timeout_seconds=timeout_seconds,
                    ),
                )
            )
        )

    try:
        for future in asyncio.as_completed(tasks):
            role_name, verdict = await future
            elapsed = time.monotonic() - start_times.get(role_name, time.monotonic())
            yield role_name, verdict, elapsed
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()


# ---------------------------------------------------------------------------
# Stage E tail: E1 + E2 + E3 + E5 + E7 (shared by evaluate and switch)
# ---------------------------------------------------------------------------


async def _stream_stage_e_tail(
    stage_d_output: Any,
    scenario_name_value: str,
    candidate_count: int,
    llm_client: LLMClient,
) -> AsyncIterator[SSEEvent]:
    """Run the full Stage E pipeline tail and yield SSE events.

    Shared between evaluate_pipeline_stream and switch_scenario_stream.
    Covers E1 (validation), E2 (signals), E3 (agents), E5 (audit),
    and E7 (synthesis).

    Args:
        stage_d_output: The validated StageDOutput from run_stage_d.
        scenario_name_value: Scenario name string for event payloads.
        candidate_count: Number of candidates (for synthesis started event).
        llm_client: Async LLM client for agent and synthesis calls.

    Yields:
        SSEEvent objects for each Stage E checkpoint.
    """
    from stage_e.layer0_validation import validate_stage_d_output
    from stage_e.layer1_signals import compute_layer1
    from stage_e.layer2_agents.runner import _AGENT_CONFIGS
    from stage_e.layer3_audit.runner import run_audit
    from stage_e.synthesis.assembler import assemble_synthesis

    # ------------------------------------------------------------------ E1 + E2: Validation + signals
    validated, _validation_warnings = validate_stage_d_output(stage_d_output)
    candidate_names = [c.name for c in validated.candidate_data]
    validated_modes: dict[str, str] = {
        name: prov.assessment_mode.value for name, prov in validated.provenance_per_candidate.items()
    }
    layer1 = compute_layer1(
        flags=validated.flags,
        scenario=validated.scenario,
        candidate_names=candidate_names,
        assessment_modes=validated_modes,
    )
    yield SSEEvent(
        event=SSEEventType.SIGNALS_COMPUTED,
        data=SignalsComputedPayload(
            signal_count=len(validated.flags),
            tension_pairs=len(layer1.tension_map),
            scenario=scenario_name_value,
            signal_labels={k: v.value for k, v in layer1.signal_labels.items()},
            risk_bands={k: v.value for k, v in layer1.risk_bands.items()},
            tensions=[
                {
                    "candidate_name": t.candidate_name,
                    "positive_flag": t.positive_flag,
                    "negative_flag": t.negative_flag,
                    "domain": t.domain,
                    "tension_type": t.tension_type,
                    "description": t.description,
                }
                for t in layer1.tension_map
            ],
            partial_mode_notes=layer1.partial_mode_notes,
        ).model_dump(),
    )

    # ------------------------------------------------------------------ E3: Per-agent streaming
    agent_names = [role.value for role, _, _ in _AGENT_CONFIGS]
    yield SSEEvent(
        event=SSEEventType.AGENTS_STARTED,
        data=AgentsStartedPayload(agent_names=agent_names).model_dump(),
    )

    verdicts: dict[str, AgentVerdict | None] = {}
    async for role_name, verdict, elapsed in _stream_e3_agents(
        flags=validated.flags,
        tension_map=layer1.tension_map,
        candidates=validated.candidate_data,
        requirements=validated.confirmed_requirements,
        assessment_modes=validated_modes,
        llm_client=llm_client,
    ):
        verdicts[role_name] = verdict
        yield _make_agent_event(role_name, verdict, elapsed)

    # ------------------------------------------------------------------ E5: Audit
    audited_verdicts, audit_warnings = run_audit(
        verdicts=verdicts,
        flags=validated.flags,
        candidate_data=validated.candidate_data,
        rubric_assessments=validated.rubric_matrix,
        requirements=validated.confirmed_requirements,
    )
    checks_run = len(audited_verdicts) * 8
    yield SSEEvent(
        event=SSEEventType.AUDIT_COMPLETE,
        data=AuditCompletePayload(
            checks_run=checks_run,
            checks_passed=max(0, checks_run - len(audit_warnings)),
            checks_failed=len(audit_warnings),
            audit_warnings=audit_warnings[:20],
        ).model_dump(),
    )

    # ------------------------------------------------------------------ E7: Synthesis
    yield SSEEvent(
        event=SSEEventType.SYNTHESIS_STARTED,
        data=SynthesisStartedPayload(candidate_count=candidate_count).model_dump(),
    )
    synthesis = await asyncio.wait_for(
        assemble_synthesis(
            stage_d_output=validated,
            layer1_output=layer1,
            audited_verdicts=audited_verdicts,
            audit_warnings=audit_warnings,
            llm_client=llm_client,
        ),
        timeout=60.0,
    )
    yield SSEEvent(
        event=SSEEventType.SYNTHESIS_COMPLETE,
        data=SynthesisCompletePayload(
            candidates=_build_synthesis_candidates_map(synthesis),
            trade_off_count=len(synthesis.trade_off_matrix),
            investigation_question_count=_count_investigation_questions(synthesis),
            trade_off_matrix=[cell.model_dump() for cell in synthesis.trade_off_matrix],
            candidate_summaries=[s.model_dump() for s in synthesis.candidate_summaries],
            trade_off_statement=synthesis.trade_off_statement,
            contested_signals=[cs.model_dump() for cs in synthesis.contested_signals],
            provenance=synthesis.provenance.model_dump(),
            epistemic_disclaimer=synthesis.epistemic_disclaimer,
            partial_mode_disclaimer=synthesis.partial_mode_disclaimer,
        ).model_dump(),
    )
