"""Payload construction helpers for pipeline SSE events.

Builds SSEEvent payloads from pipeline stage outputs. Includes assessment
statistics, flag counting, synthesis summary extraction, and per-event
builder functions for Stage D and agent results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from api.sse.events import (
    AgentCompletePayload,
    AgentTimeoutPayload,
    SSEEvent,
    SSEEventType,
    StageDCompletePayload,
)

if TYPE_CHECKING:
    from shared.models.flags import Flag
    from shared.models.rubric import RubricAssessment
    from stage_e.schemas import AgentVerdict
    from stage_e.synthesis.models import SynthesisOutput


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
    """Extract candidate -> verdict label from synthesis output.

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
