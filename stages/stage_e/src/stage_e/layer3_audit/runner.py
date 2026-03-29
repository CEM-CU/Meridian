"""Layer 3 Audit runner — orchestrates 8 deterministic checks (E5).

Runs all 8 checks sequentially on each agent verdict. None verdicts (timed-out
agents) are skipped. Returns cleaned verdicts and all accumulated warnings.

Zero LLM calls. Never blocks the pipeline.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from stage_e.layer2_agents.allowlists import (
    RISK_ALLOWLIST,
    ROLE_FIT_ALLOWLIST,
    TEAM_DYNAMICS_ALLOWLIST,
    filter_flags_for_agent,
)
from stage_e.layer3_audit.checks import (
    ALL_FLAG_NAMES,
    check_biographical_references,
    check_downweight_ratio,
    check_flag_scope,
    check_hallucinated_references,
    check_research_general_cap,
    check_schema_validity,
    check_semantic_drift,
    check_unaddressed_flags,
)
from stage_e.schemas import AgentRole, AgentVerdict

if TYPE_CHECKING:
    from shared.models.candidates import CandidateData
    from shared.models.flags import Flag, FlagCategory
    from shared.models.requirements import Requirement
    from shared.models.rubric import RubricAssessment

logger = logging.getLogger(__name__)

# Map each agent role to its flag allowlist.
_ROLE_ALLOWLIST: dict[str, frozenset[FlagCategory]] = {
    AgentRole.ROLE_FIT.value: ROLE_FIT_ALLOWLIST,
    AgentRole.TEAM_DYNAMICS.value: TEAM_DYNAMICS_ALLOWLIST,
    AgentRole.RISK.value: RISK_ALLOWLIST,
}


def _audit_single_verdict(
    role: str,
    verdict: AgentVerdict,
    flags: list[Flag],
    candidate_data: list[CandidateData],
    rubric_assessments: list[RubricAssessment],
    requirements: list[Requirement],
    valid_requirement_ids: frozenset[str],
) -> tuple[AgentVerdict, list[str]]:
    """Run all 8 audit checks on a single agent verdict.

    Args:
        role: Agent role string (e.g. "role_fit").
        verdict: The agent verdict to audit.
        flags: Full flag set (pre-filtered to this agent's allowlist).
        candidate_data: All candidate data with raw CV text.
        rubric_assessments: Stage C rubric assessment matrix.
        requirements: Confirmed JD requirement list.
        valid_requirement_ids: Frozenset of valid requirement IDs.

    Returns:
        Tuple of (audited_verdict, all_warnings).
    """
    all_warnings: list[str] = []
    allowlist = _ROLE_ALLOWLIST.get(role, frozenset())

    # Check 1: Schema re-validation
    warnings_1 = check_schema_validity(verdict)
    all_warnings.extend(warnings_1)

    # Check 2: Flag scope enforcement
    verdict, warnings_2 = check_flag_scope(verdict, allowlist, flags)
    all_warnings.extend(warnings_2)

    # Check 3: Unaddressed flag detection
    warnings_3 = check_unaddressed_flags(verdict, flags)
    all_warnings.extend(warnings_3)

    # Check 4: Hallucinated flag / reference detection
    verdict, warnings_4 = check_hallucinated_references(
        verdict,
        valid_flag_names=ALL_FLAG_NAMES,
        valid_requirement_ids=valid_requirement_ids,
    )
    all_warnings.extend(warnings_4)

    # Check 5 (F04): Biographical reference validation
    verdict, warnings_5 = check_biographical_references(
        verdict,
        candidate_data=candidate_data,
        rubric_assessments=rubric_assessments,
        requirements=requirements,
    )
    all_warnings.extend(warnings_5)

    # Check 6 (F05): Semantic drift detection (advisory only, no stripping)
    warnings_6 = check_semantic_drift(verdict, flags)
    all_warnings.extend(warnings_6)

    # Check 7 (F07): research_general cap
    warnings_7 = check_research_general_cap(verdict)
    all_warnings.extend(warnings_7)

    # Check 8 (F14): Downweight ratio warning
    warnings_8 = check_downweight_ratio(verdict, flags)
    all_warnings.extend(warnings_8)

    if all_warnings:
        logger.info(
            "Audit for '%s': %d warning(s) produced, %d claim(s) remain",
            role,
            len(all_warnings),
            len(verdict.claims),
        )

    return verdict, all_warnings


def run_audit(
    verdicts: dict[str, AgentVerdict | None],
    flags: list[Flag],
    candidate_data: list[CandidateData],
    rubric_assessments: list[RubricAssessment],
    requirements: list[Requirement],
) -> tuple[dict[str, AgentVerdict], list[str]]:
    """Run all 8 audit checks on agent verdicts.

    None verdicts (timed-out agents) are skipped. Each verdict is audited
    against its role-specific allowlist. Checks run sequentially per verdict;
    verdicts are processed in role order.

    Args:
        verdicts: Mapping of agent role → AgentVerdict or None (from Layer 2).
        flags: Full validated flag set from Layer 1.
        candidate_data: All candidate data (with raw CV text for F04).
        rubric_assessments: Stage C rubric assessment matrix (for F04).
        requirements: Confirmed JD requirement list.

    Returns:
        Tuple of:
        - ``audited_verdicts``: Dict mapping role string → cleaned AgentVerdict.
          Only non-None input verdicts are included.
        - ``all_warnings``: All warnings produced across all checks and agents.
    """
    valid_requirement_ids: frozenset[str] = frozenset(r.requirement_id for r in requirements)

    audited_verdicts: dict[str, AgentVerdict] = {}
    all_warnings: list[str] = []

    for role, verdict in verdicts.items():
        if verdict is None:
            logger.info("Audit: skipping '%s' — timed out or failed", role)
            continue

        # Filter flags to this agent's allowlist for scope/drift/downweight checks.
        allowlist = _ROLE_ALLOWLIST.get(role, frozenset())
        agent_flags = filter_flags_for_agent(flags, allowlist)

        audited, warnings = _audit_single_verdict(
            role=role,
            verdict=verdict,
            flags=agent_flags,
            candidate_data=candidate_data,
            rubric_assessments=rubric_assessments,
            requirements=requirements,
            valid_requirement_ids=valid_requirement_ids,
        )
        audited_verdicts[role] = audited
        all_warnings.extend(warnings)

    logger.info(
        "Layer 3 audit complete: %d/%d verdicts audited, %d total warning(s)",
        len(audited_verdicts),
        len(verdicts),
        len(all_warnings),
    )

    return audited_verdicts, all_warnings
