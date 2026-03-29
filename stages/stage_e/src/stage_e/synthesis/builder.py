"""E7 synthesis builder -- pure assembly logic for all non-LLM sections.

All functions are pure (no mutation, no side effects). Each takes typed
inputs and returns typed outputs. No singletons, no module-level caches.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shared.models.requirements import Priority
from shared.models.rubric import RubricLevel

if TYPE_CHECKING:
    from shared.models.pipeline import StageDOutput
    from shared.models.requirements import Requirement
    from shared.models.rubric import RubricAssessment
    from shared.models.scenarios import ScenarioConfig

    from stage_e.layer1_signals import TensionPair
    from stage_e.schemas import AgentVerdict

from .models import (
    CandidateSummary,
    ContestedSignal,
    ProvenanceHeader,
    TradeOffCell,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Epistemic disclaimer constants (F09, F10)
# ---------------------------------------------------------------------------

_F10_DISCLAIMER = (
    "This tool surfaces patterns from personality and CV data to inform "
    "committee judgment. It generates structured hypotheses grounded in "
    "published organizational psychology research and verifiable CV evidence "
    "-- not predictions. Confidence levels reflect signal density, not outcome "
    "probability. All outputs are advisory and require human deliberation."
)

_F09_PARTIAL_DISCLAIMER = (
    "No personality data available. Team dynamics "
    "assessment limited to experience-based factors (skill gaps, functional "
    "diversity). Personality-based dynamics (complementarity, collision risk, "
    "groupthink vulnerability) require validated Big Five scores."
)

# Priority sort order: high rows appear first.
_PRIORITY_ORDER: dict[str, int] = {
    Priority.HIGH: 0,
    Priority.MEDIUM: 1,
    Priority.LOW: 2,
}


# ---------------------------------------------------------------------------
# Layer 1: Trade-Off Matrix
# ---------------------------------------------------------------------------


def _active_priority(req: Requirement, scenario: ScenarioConfig) -> str:
    """Resolve the active priority for a requirement under the given scenario."""
    try:
        return req.scenario_priority.for_scenario(scenario.name.value)
    except (ValueError, AttributeError):
        logger.warning("Could not resolve priority for req %s in scenario %s", req.requirement_id, scenario.name)
        return Priority.LOW


def _cell_from_assessment(
    assessment: RubricAssessment,
    req: Requirement,
    active_priority: str,
    assessment_mode: str,
) -> TradeOffCell:
    """Build a single TradeOffCell from a RubricAssessment.

    Partial mode + non-CV-assessable requirement -> rubric_level forced to
    'not_assessable' per spec (behavioral rows show 'Requires personality data').
    """
    rubric_level = assessment.rubric_level.value
    if assessment_mode == "partial" and not req.assessable_from_cv:
        rubric_level = RubricLevel.NOT_ASSESSABLE.value

    return TradeOffCell(
        requirement_id=req.requirement_id,
        requirement_text=req.text,
        active_priority=active_priority,
        candidate_name=assessment.candidate_name,
        rubric_level=rubric_level,
        confidence=assessment.confidence.value,
        cv_citation=assessment.cv_citation,
        investigation_question=assessment.investigation_question,
    )


def build_trade_off_matrix(
    rubric_assessments: list[RubricAssessment],
    requirements: list[Requirement],
    scenario: ScenarioConfig,
    assessment_modes: dict[str, str],
) -> list[TradeOffCell]:
    """Build the requirement x candidate grid, sorted by priority (high first).

    Rows are sorted by active_priority (high -> medium -> low), then by
    requirement_id for stability within each priority tier. Rubric levels
    do NOT change when the scenario switches -- only the sort order changes.

    Args:
        rubric_assessments: All rubric assessments (all candidates x all reqs).
        requirements: Confirmed requirement list from Stage C.
        scenario: Active scenario (used for priority resolution and row sort).
        assessment_modes: Candidate name -> "full" or "partial".

    Returns:
        Flat list of TradeOffCell, sorted by active_priority then requirement_id.
    """
    req_by_id: dict[str, Requirement] = {r.requirement_id: r for r in requirements}

    cells: list[TradeOffCell] = []
    for assessment in rubric_assessments:
        req = req_by_id.get(assessment.requirement_id)
        if req is None:
            logger.warning("Requirement %s not found in confirmed list -- skipping cell", assessment.requirement_id)
            continue
        mode = assessment_modes.get(assessment.candidate_name, "full")
        priority = _active_priority(req, scenario)
        cells.append(_cell_from_assessment(assessment, req, priority, mode))

    return sorted(
        cells,
        key=lambda c: (_PRIORITY_ORDER.get(c.active_priority, 99), c.requirement_id),
    )


# ---------------------------------------------------------------------------
# Layer 2: Candidate Summaries
# ---------------------------------------------------------------------------


def _collect_investigation_questions(
    candidate: str,
    rubric_assessments: list[RubricAssessment],
) -> list[str]:
    """Collect investigation questions for one candidate from rubric assessments."""
    return [
        assessment.investigation_question
        for assessment in rubric_assessments
        if assessment.candidate_name == candidate and assessment.investigation_question
    ]


def _unique_candidates_from_verdicts(verdicts: dict[str, AgentVerdict]) -> list[str]:
    """Return a stable, deduplicated list of candidate names across all verdicts."""
    seen: set[str] = set()
    names: list[str] = []
    for verdict in verdicts.values():
        for claim in verdict.claims:
            if claim.candidate_name not in seen:
                seen.add(claim.candidate_name)
                names.append(claim.candidate_name)
    return names


def _index_contested_by_candidate(
    contested: list[ContestedSignal],
) -> dict[str, list[ContestedSignal]]:
    """Index contested signals by candidate name."""
    index: dict[str, list[ContestedSignal]] = {}
    for signal in contested:
        index.setdefault(signal.candidate_name, []).append(signal)
    return index


def _build_per_candidate_highlights(
    candidate: str,
    verdicts: dict[str, AgentVerdict],
) -> dict[str, str]:
    """Build per-candidate agent highlights from verdict claims filtered to that candidate.

    For each agent role, collect claims that reference the given candidate and
    join the first three claim texts as the highlight snippet. If no claims
    exist for that candidate, a placeholder string is returned.
    """
    agent_highlights: dict[str, str] = {}
    for role, verdict in verdicts.items():
        candidate_claims = [c for c in verdict.claims if c.candidate_name == candidate]
        if candidate_claims:
            highlight_parts = [c.text for c in candidate_claims[:3]]
            agent_highlights[role] = " ".join(highlight_parts)
        else:
            agent_highlights[role] = f"No specific claims for {candidate}."
    return agent_highlights


def build_candidate_summaries(
    verdicts: dict[str, AgentVerdict],
    tension_map: list[TensionPair],
    rubric_assessments: list[RubricAssessment],
    assessment_modes: dict[str, str],
) -> list[CandidateSummary]:
    """Build per-candidate Layer 2 summaries from audited verdicts.

    Each summary contains agent highlights (one per agent role), contested
    signals for this candidate, investigation questions, and any unaddressed
    flags from all agents.

    Args:
        verdicts: Audited agent verdicts keyed by agent_role.
        tension_map: Full tension map from Layer 1.
        rubric_assessments: Rubric matrix for investigation question harvest.
        assessment_modes: Candidate name -> "full" or "partial".

    Returns:
        List of CandidateSummary, one per unique candidate in verdicts.
    """
    candidate_names = _unique_candidates_from_verdicts(verdicts)

    contested_by_candidate = _index_contested_by_candidate(detect_contested_signals(verdicts, tension_map))

    summaries: list[CandidateSummary] = []
    for candidate in candidate_names:
        agent_highlights = _build_per_candidate_highlights(candidate, verdicts)
        all_unaddressed: list[str] = [flag for verdict in verdicts.values() for flag in verdict.unaddressed_flags]
        investigation_questions = _collect_investigation_questions(candidate, rubric_assessments)

        summaries.append(
            CandidateSummary(
                candidate_name=candidate,
                assessment_mode=assessment_modes.get(candidate, "full"),
                agent_highlights=agent_highlights,
                contested_signals=contested_by_candidate.get(candidate, []),
                investigation_questions=investigation_questions,
                unaddressed_flags=all_unaddressed,
            )
        )

    return summaries


# ---------------------------------------------------------------------------
# Contested Signal Detection (F12)
# ---------------------------------------------------------------------------


def detect_contested_signals(
    verdicts: dict[str, AgentVerdict],
    tension_map: list[TensionPair],
) -> list[ContestedSignal]:
    """Detect cross-agent and cross-stream contested signals (F12).

    Two types are detected:
    1. Cross-agent: the same evidence reference is cited by multiple agents
       but with different confidence levels (high vs low) for the same candidate.
    2. Cross-stream: a TensionPair with tension_type == 'cross_stream' from
       Layer 1, indicating a CV-personality divergence on the same domain.

    Args:
        verdicts: Audited agent verdicts keyed by agent_role.
        tension_map: Tension pairs from Layer 1 signal computation.

    Returns:
        List of ContestedSignal instances.
    """
    contested: list[ContestedSignal] = []
    contested.extend(_detect_cross_agent_contests(verdicts))
    contested.extend(_detect_cross_stream_contests(tension_map, verdicts))
    return contested


_POSITIVE_LENS_ROLES = frozenset({"role_fit"})
_NEGATIVE_LENS_ROLES = frozenset({"risk"})


def _detect_cross_agent_contests(
    verdicts: dict[str, AgentVerdict],
) -> list[ContestedSignal]:
    """Find cases where agents interpret the same reference through opposing lenses.

    Two contest criteria, either triggers a ContestedSignal:
    1. Opposing-lens: a positive-lens role (role_fit) and a negative-lens role
       (risk) both cite the same (candidate, reference) pair.
    2. Confidence divergence (additional signal): two agents cite the same pair
       but one rates it high-confidence and the other rates it low-confidence.
    """
    # Index: (candidate_name, reference) -> list of (role, confidence)
    citations: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for role, verdict in verdicts.items():
        for claim in verdict.claims:
            key = (claim.candidate_name, claim.evidence_basis.reference)
            citations.setdefault(key, []).append((role, claim.confidence))

    contested: list[ContestedSignal] = []
    for (candidate, reference), role_confidences in citations.items():
        if len(role_confidences) < 2:
            continue
        roles_cited = {role for role, _ in role_confidences}
        confidences = {conf for _, conf in role_confidences}

        opposing_lens = bool(_POSITIVE_LENS_ROLES & roles_cited) and bool(_NEGATIVE_LENS_ROLES & roles_cited)
        confidence_divergence = "high" in confidences and "low" in confidences

        if opposing_lens or confidence_divergence:
            agents_involved = [role for role, _ in role_confidences]
            contested.append(
                ContestedSignal(
                    candidate_name=candidate,
                    signal_type="cross_agent",
                    description=(
                        f"Agents disagree on evidence '{reference}' for {candidate}: "
                        f"confidence ratings diverge ({', '.join(f'{r}={c}' for r, c in role_confidences)})."
                    ),
                    agents_involved=agents_involved,
                )
            )
    return contested


def _detect_cross_stream_contests(
    tension_map: list[TensionPair],
    verdicts: dict[str, AgentVerdict],
) -> list[ContestedSignal]:
    """Convert cross_stream TensionPairs into ContestedSignal records.

    A cross-stream tension from Layer 1 becomes a contested signal when
    it surfaces in the synthesis layer (F12). We attach the agent roles
    that are most relevant to each side of the tension.
    """
    _CV_ROLES = ["role_fit"]
    _PERSONALITY_ROLES = ["risk", "team_dynamics"]

    contested: list[ContestedSignal] = []
    for tension in tension_map:
        if tension.tension_type != "cross_stream":
            continue

        agents_with_claims: list[str] = [
            role
            for role, verdict in verdicts.items()
            if any(c.candidate_name == tension.candidate_name for c in verdict.claims)
        ]

        agents_involved = [r for r in _CV_ROLES + _PERSONALITY_ROLES if r in agents_with_claims]
        if not agents_involved:
            agents_involved = agents_with_claims

        contested.append(
            ContestedSignal(
                candidate_name=tension.candidate_name,
                signal_type="cross_stream",
                description=(
                    f"[CONTESTED SIGNAL]: {tension.description} "
                    "Committee should weigh demonstrated history against predicted behaviour."
                ),
                agents_involved=agents_involved,
            )
        )
    return contested


# ---------------------------------------------------------------------------
# Provenance Header (F08)
# ---------------------------------------------------------------------------


def build_provenance_header(
    stage_d_output: StageDOutput,
    audit_warnings: list[str],
) -> ProvenanceHeader:
    """Build provenance metadata from Stage D output and audit warnings.

    Args:
        stage_d_output: Full Stage D output containing requirements, rubric
            matrix, candidate data, and per-candidate provenance.
        audit_warnings: Warnings collected by the Layer 3 audit.

    Returns:
        ProvenanceHeader with all provenance fields populated.
    """
    requirements = stage_d_output.confirmed_requirements
    cv_assessable_count = sum(1 for r in requirements if r.assessable_from_cv)
    behavioral_count = len(requirements) - cv_assessable_count

    assessment_modes: dict[str, str] = {
        name: prov.assessment_mode.value for name, prov in stage_d_output.provenance_per_candidate.items()
    }

    personality_sources: dict[str, str | None] = {
        name: prov.personality_source for name, prov in stage_d_output.provenance_per_candidate.items()
    }

    flag_counts: dict[str, int] = {
        name: prov.total_flags for name, prov in stage_d_output.provenance_per_candidate.items()
    }

    quality_checks_passed = len(audit_warnings) == 0

    return ProvenanceHeader(
        requirement_count=len(requirements),
        cv_assessable_count=cv_assessable_count,
        behavioral_count=behavioral_count,
        candidate_count=len(stage_d_output.candidate_data),
        assessment_modes=assessment_modes,
        personality_sources=personality_sources,
        flag_counts=flag_counts,
        quality_checks_passed=quality_checks_passed,
        warnings=list(audit_warnings),
    )


# ---------------------------------------------------------------------------
# Epistemic Disclaimers (F09, F10)
# ---------------------------------------------------------------------------


def build_epistemic_disclaimers(
    assessment_modes: dict[str, str],
) -> tuple[str, str | None]:
    """Build F10 top-level disclaimer and optional F09 partial mode disclaimer.

    F10 is always included. F09 is only included when at least one candidate
    has assessment_mode == 'partial'.

    Args:
        assessment_modes: Candidate name -> "full" or "partial".

    Returns:
        Tuple of (f10_disclaimer, f09_disclaimer_or_None).
    """
    has_partial = any(mode == "partial" for mode in assessment_modes.values())
    partial_disclaimer = _F09_PARTIAL_DISCLAIMER if has_partial else None
    return _F10_DISCLAIMER, partial_disclaimer
