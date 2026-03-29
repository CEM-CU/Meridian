"""Pipeline SSE stream generator.

Wraps the C→D→E evaluation pipeline as an async generator of SSEEvents.
Yields progress events at 18+ checkpoints for real-time frontend updates.

Key design: asyncio.as_completed is used for C3 (per-candidate) and E3
(per-agent) so that progress events stream as each unit finishes rather
than waiting for all to complete.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from shared.models import ScenarioConfig
from shared.models.candidates import BigFiveScores, CandidateData
from shared.models.scenarios import ScenarioName

from api.sse.events import (
    AgentCompletePayload,
    AgentsStartedPayload,
    AgentTimeoutPayload,
    AuditCompletePayload,
    C1CompletePayload,
    C1StartedPayload,
    C2CompletePayload,
    C3CandidateDonePayload,
    C3StartedPayload,
    C4CompletePayload,
    CompletePayload,
    ErrorPayload,
    SignalsComputedPayload,
    SSEEvent,
    SSEEventType,
    StageDCompletePayload,
    SwitchCompletePayload,
    SwitchStartedPayload,
    SynthesisCompletePayload,
    SynthesisStartedPayload,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from shared.models.flags import Flag
    from shared.models.requirements import Requirement
    from shared.models.rubric import RubricAssessment
    from stage_c.protocols import LLMClient
    from stage_e.layer1_signals import TensionPair
    from stage_e.scenario_switch import CachedPipelineState
    from stage_e.schemas import AgentVerdict
    from stage_e.synthesis.models import SynthesisOutput

    from api.jobs.models import CandidateInput

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers: input conversion and scenario resolution
# ---------------------------------------------------------------------------


def _convert_candidate_input(inputs: list[CandidateInput]) -> list[CandidateData]:
    """Convert API CandidateInput to shared CandidateData.

    Args:
        inputs: List of frontend-facing CandidateInput objects.

    Returns:
        List of CandidateData objects ready for pipeline consumption.
    """
    candidates: list[CandidateData] = []
    for inp in inputs:
        big_five: BigFiveScores | None = None
        if inp.big_five is not None:
            big_five = BigFiveScores(
                O=inp.big_five.get("O", 0.5),
                C=inp.big_five.get("C", 0.5),
                E=inp.big_five.get("E", 0.5),
                A=inp.big_five.get("A", 0.5),
                N=inp.big_five.get("N", 0.5),
            )
        candidates.append(
            CandidateData(
                name=inp.name,
                cv_text=inp.cv_text,
                big_five=big_five,
                personality_source=inp.personality_source,
            )
        )
    return candidates


def _resolve_scenario(name: str) -> ScenarioConfig:
    """Resolve scenario name string to ScenarioConfig with default weights.

    Args:
        name: Scenario name string (case-insensitive ScenarioName value).

    Returns:
        ScenarioConfig with an empty category_weights dict (defaults apply).

    Raises:
        ValueError: If the name is not a valid ScenarioName value.
    """
    try:
        scenario_name = ScenarioName(name.lower())
    except ValueError as exc:
        valid = [e.value for e in ScenarioName]
        raise ValueError(f"Unknown scenario {name!r}. Valid values: {valid}") from exc
    return ScenarioConfig(name=scenario_name, category_weights={})


# ---------------------------------------------------------------------------
# Assessment stats helper
# ---------------------------------------------------------------------------


def _assessment_stats(assessments: list[RubricAssessment]) -> dict[str, int]:
    """Count rubric levels across a list of assessments.

    Args:
        assessments: Rubric assessments for a single candidate.

    Returns:
        Dict with keys: exceeds, meets, partial, gap, not_assessable.
    """
    stats: dict[str, int] = {"exceeds": 0, "meets": 0, "partial": 0, "gap": 0, "not_assessable": 0}
    for a in assessments:
        level = a.rubric_level.value if hasattr(a.rubric_level, "value") else str(a.rubric_level)
        if level in stats:
            stats[level] += 1
    return stats


# ---------------------------------------------------------------------------
# Flag counting helpers
# ---------------------------------------------------------------------------


def _count_personality_flags(flags: list[Flag]) -> int:
    """Count flags derived from personality (SCORED_FLAG evidence type)."""
    from shared.models.flags import EvidenceType

    return sum(1 for f in flags if f.evidence_type == EvidenceType.SCORED_FLAG)


def _count_cv_flags(flags: list[Flag]) -> int:
    """Count flags derived from CV rubric assessment."""
    from shared.models.flags import EvidenceType

    cv_types = {EvidenceType.CV_RUBRIC, EvidenceType.REQUIREMENT_GAP, EvidenceType.CV_PATTERN, EvidenceType.ROUTING}
    return sum(1 for f in flags if f.evidence_type in cv_types)


def _count_not_assessable(assessments: list[RubricAssessment]) -> int:
    """Count assessments with not_assessable rubric level."""
    from shared.models.rubric import RubricLevel

    return sum(1 for a in assessments if a.rubric_level == RubricLevel.NOT_ASSESSABLE)


# ---------------------------------------------------------------------------
# Synthesis summary helpers
# ---------------------------------------------------------------------------


def _build_synthesis_candidates_map(synthesis: SynthesisOutput) -> dict[str, str]:
    """Extract candidate → verdict label from synthesis output.

    Args:
        synthesis: The assembled SynthesisOutput from Stage E.

    Returns:
        Dict mapping candidate name to a verdict label string.
    """
    result: dict[str, str] = {}
    for summary in synthesis.candidate_summaries:
        verdict = "evaluated" if summary.agent_highlights else "insufficient_data"
        result[summary.candidate_name] = verdict
    return result


def _count_investigation_questions(synthesis: SynthesisOutput) -> int:
    """Sum all investigation questions across all candidate summaries.

    Args:
        synthesis: The assembled SynthesisOutput from Stage E.

    Returns:
        Total count of investigation questions.
    """
    return sum(len(s.investigation_questions) for s in synthesis.candidate_summaries)


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
        assessment_modes: Candidate name → "full" or "partial".
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
# Agent event helper
# ---------------------------------------------------------------------------


def _make_agent_event(
    role_name: str,
    verdict: AgentVerdict | None,
    elapsed: float,
    timeout_seconds: float = 15.0,
) -> SSEEvent:
    """Build AGENT_COMPLETE or AGENT_TIMEOUT event from a verdict result.

    Args:
        role_name: Agent role name string.
        verdict: AgentVerdict if successful, None if timed out.
        elapsed: Wall-clock seconds for this agent call.
        timeout_seconds: Timeout threshold for generating AGENT_TIMEOUT.

    Returns:
        An SSEEvent with the appropriate event type and payload.
    """
    if verdict is None:
        return SSEEvent(
            event=SSEEventType.AGENT_TIMEOUT,
            data=AgentTimeoutPayload(
                agent_name=role_name,
                timeout_seconds=timeout_seconds,
            ).model_dump(),
        )
    finding_count = len(verdict.claims)
    evidence_types: dict[str, int] = {}
    for claim in verdict.claims:
        et = claim.evidence_basis.type.value
        evidence_types[et] = evidence_types.get(et, 0) + 1
    evidence_count = sum(evidence_types.values())
    return SSEEvent(
        event=SSEEventType.AGENT_COMPLETE,
        data=AgentCompletePayload(
            agent_name=role_name,
            finding_count=finding_count,
            evidence_count=evidence_count,
            elapsed_seconds=round(elapsed, 2),
            summary=verdict.summary,
            evidence_types=evidence_types,
            unaddressed_flags=verdict.unaddressed_flags,
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Stage D event helper
# ---------------------------------------------------------------------------


def _make_stage_d_event(stage_d_output: Any) -> SSEEvent:
    """Build STAGE_D_COMPLETE event from StageDOutput.

    Args:
        stage_d_output: The StageDOutput produced by run_stage_d.

    Returns:
        An SSEEvent with flag counts and assessment modes.
    """
    assessment_modes: dict[str, str] = {
        name: prov.assessment_mode.value for name, prov in stage_d_output.provenance_per_candidate.items()
    }
    per_candidate: dict[str, dict] = {
        name: {
            "mode": prov.assessment_mode.value,
            "personality_flags": prov.personality_flag_count,
            "cv_flags": prov.cv_flag_count,
            "total": prov.total_flags,
            "big_five_available": prov.big_five_available,
        }
        for name, prov in stage_d_output.provenance_per_candidate.items()
    }
    return SSEEvent(
        event=SSEEventType.STAGE_D_COMPLETE,
        data=StageDCompletePayload(
            flag_count=len(stage_d_output.flags),
            personality_flag_count=_count_personality_flags(stage_d_output.flags),
            cv_flag_count=_count_cv_flags(stage_d_output.flags),
            validation_warnings=[],
            assessment_modes=assessment_modes,
            per_candidate=per_candidate,
        ).model_dump(),
    )


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
    """Async generator yielding SSE events through the full C→D→E pipeline.

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

    from shared.models.pipeline import StageCOutput
    from stage_c.bridge import bridge_rubric_to_flags
    from stage_c.cv_assessment import _build_priority_order
    from stage_c.jd_extraction import extract_requirements
    from stage_c.priority_resolution import resolve_active_priorities
    from stage_d.pipeline import run_stage_d
    from stage_e.layer0_validation import validate_stage_d_output
    from stage_e.layer1_signals import compute_layer1
    from stage_e.layer2_agents.runner import _AGENT_CONFIGS
    from stage_e.layer3_audit.runner import run_audit
    from stage_e.synthesis.assembler import assemble_synthesis

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
                scenario=scenario.name.value,
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
            data=SynthesisStartedPayload(candidate_count=len(candidates)).model_dump(),
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
    """Async generator for scenario switch — skips C1/C3, uses cached state.

    Re-runs C2 → C4 → Stage D → E1 → E2 → E3 → E5 → E7 using pre-cached
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
    from shared.models.pipeline import StageCOutput
    from stage_c.bridge import bridge_rubric_to_flags
    from stage_c.priority_resolution import resolve_active_priorities
    from stage_d.pipeline import run_stage_d
    from stage_e.layer0_validation import validate_stage_d_output
    from stage_e.layer1_signals import compute_layer1
    from stage_e.layer2_agents.runner import _AGENT_CONFIGS
    from stage_e.layer3_audit.runner import run_audit
    from stage_e.synthesis.assembler import assemble_synthesis

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

        # ------------------------------------------------------------------ E1 + E2
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
                scenario=new_scenario.name.value,
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
            data=SynthesisStartedPayload(candidate_count=len(cached_state.candidates)).model_dump(),
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
