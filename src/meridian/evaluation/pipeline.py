"""Stage E pipeline orchestrator.

Wires E1 (validation) → E2 (signals) → E3 (agents) → E5 (audit) → E7 (synthesis)
and returns the final SynthesisOutput.

4 LLM calls: 3 parallel agents + 1 synthesis trade-off statement.
Latency: ~10-13s.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from meridian.evaluation.agents.runner import run_agents
from meridian.evaluation.audit.runner import run_audit
from meridian.evaluation.layer0_validation import validate_stage_d_output
from meridian.evaluation.layer1_signals import compute_layer1
from meridian.evaluation.synthesis.assembler import assemble_synthesis

if TYPE_CHECKING:
    from meridian.evaluation.synthesis.models import SynthesisOutput
    from meridian.extraction.protocols import LLMClient
    from meridian.models.pipeline import StageDOutput

logger = logging.getLogger(__name__)


async def run_stage_e(
    stage_d_output: StageDOutput,
    llm_client: LLMClient,
) -> tuple[SynthesisOutput, list[str]]:
    """Execute the full Stage E pipeline: E1 → E2 → E3 → E5 → E7.

    Args:
        stage_d_output: Complete Stage D output (flags, provenance, requirements,
            candidate data, rubric matrix, scenario).
        llm_client: Async LLM client for agent calls and synthesis statement.

    Returns:
        Tuple of (SynthesisOutput, all_warnings).
    """
    # E1: Layer 0 — Stage D output validation
    validated, validation_warnings = validate_stage_d_output(stage_d_output)
    logger.info("E1 complete: %d flags validated, %d warnings", len(validated.flags), len(validation_warnings))

    # E2: Layer 1 — scenario weights + signal computation + tension map
    candidate_names = [c.name for c in validated.candidate_data]
    assessment_modes: dict[str, str] = {
        name: prov.assessment_mode.value for name, prov in validated.provenance_per_candidate.items()
    }
    layer1 = compute_layer1(
        flags=validated.flags,
        scenario=validated.scenario,
        candidate_names=candidate_names,
        assessment_modes=assessment_modes,
    )
    logger.info("E2 complete: %d tensions, %d partial notes", len(layer1.tension_map), len(layer1.partial_mode_notes))

    # E3: Layer 2 — 3 parallel agent evaluations
    agent_verdicts = await run_agents(
        flags=validated.flags,
        tension_map=layer1.tension_map,
        candidates=validated.candidate_data,
        requirements=validated.confirmed_requirements,
        assessment_modes=assessment_modes,
        llm_client=llm_client,
    )
    successful = sum(1 for v in agent_verdicts.values() if v is not None)
    logger.info("E3 complete: %d/%d agents returned verdicts", successful, len(agent_verdicts))

    # E5: Layer 3 — audit (8 checks)
    audited_verdicts, audit_warnings = run_audit(
        verdicts=agent_verdicts,
        flags=validated.flags,
        candidate_data=validated.candidate_data,
        rubric_assessments=validated.rubric_matrix,
        requirements=validated.confirmed_requirements,
    )
    logger.info("E5 complete: %d verdicts audited, %d warnings", len(audited_verdicts), len(audit_warnings))

    # E7: Synthesis assembly (1 LLM call for trade-off statement)
    synthesis = await assemble_synthesis(
        stage_d_output=validated,
        layer1_output=layer1,
        audited_verdicts=audited_verdicts,
        audit_warnings=audit_warnings,
        llm_client=llm_client,
    )
    logger.info("E7 complete: synthesis assembled")

    all_warnings = [*validation_warnings, *audit_warnings]
    return synthesis, all_warnings
