"""Stage C pipeline orchestrator.

Wires C1 (JD extraction) → C2 (priority resolution) → C3 (CV assessment) → C4 (bridge)
and assembles the final StageCOutput contract for Stage D consumption.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from shared.models.pipeline import StageCOutput

from stage_c.bridge import bridge_rubric_to_flags
from stage_c.cv_assessment import assess_all_candidates
from stage_c.jd_extraction import extract_requirements
from stage_c.priority_resolution import resolve_active_priorities

if TYPE_CHECKING:
    from shared.models import CandidateData, Flag, ScenarioConfig

    from stage_c.protocols import LLMClient

logger = logging.getLogger(__name__)


async def run_stage_c(
    jd_text: str,
    candidates: list[CandidateData],
    scenario: ScenarioConfig,
    llm_client: LLMClient,
    c1_response_format: dict | None = None,
    c3_response_format: dict | None = None,
) -> tuple[StageCOutput, list[Flag], list[str]]:
    """Execute the full Stage C pipeline: extract → resolve → assess → bridge.

    Args:
        jd_text: Raw job description text.
        candidates: Candidate data including raw CV text.
        scenario: Active scenario configuration.
        llm_client: Async LLM client satisfying the LLMClient protocol.

    Returns:
        Tuple of (stage_c_output, cv_flags, all_warnings).
        cv_flags are produced by the bridge but NOT included in StageCOutput —
        they feed into Stage D's merge step.
    """
    all_warnings: list[str] = []

    # C1: Extract requirements from JD
    requirements, extraction_warnings = await extract_requirements(
        jd_text, llm_client, response_format=c1_response_format
    )
    all_warnings.extend(extraction_warnings)
    logger.info("C1 complete: %d requirements extracted", len(requirements))

    # C2: Resolve active priorities (deterministic, used for C3 prompt ordering)
    _priority_pairs = resolve_active_priorities(requirements, scenario)
    logger.info("C2 complete: priorities resolved for scenario=%s", scenario.name)

    # C3: Assess all candidates against CV-assessable requirements
    rubric_assessments = await assess_all_candidates(
        candidates, requirements, scenario, llm_client, response_format=c3_response_format
    )
    logger.info("C3 complete: %d rubric assessments", len(rubric_assessments))

    # C4: Bridge rubric assessments into CV-derived flags
    cv_flags = bridge_rubric_to_flags(rubric_assessments, requirements, scenario.name)
    logger.info("C4 complete: %d CV flags produced", len(cv_flags))

    # Assemble StageCOutput contract
    output = StageCOutput(
        requirements=requirements,
        rubric_assessments=rubric_assessments,
        candidate_data=candidates,
        scenario=scenario,
    )

    return output, cv_flags, all_warnings
