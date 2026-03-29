"""E7 synthesis assembler -- top-level orchestrator for Stage E output.

Assembles the complete SynthesisOutput from all upstream pipeline products:
- Stage D output (requirements, rubric matrix, provenance)
- Layer 1 output (tension map)
- Audited agent verdicts (Layer 3)
- Audit warnings (Layer 3)
- 1 LLM call for the trade-off statement

Zero mutation. All functions take typed inputs and return typed outputs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.models.pipeline import StageDOutput
    from stage_c.protocols import LLMClient

    from stage_e.layer1_signals import Layer1Output
    from stage_e.schemas import AgentVerdict

from .builder import (
    build_candidate_summaries,
    build_epistemic_disclaimers,
    build_provenance_header,
    build_trade_off_matrix,
    detect_contested_signals,
)
from .models import SynthesisOutput
from .trade_off_statement import generate_trade_off_statement

logger = logging.getLogger(__name__)


async def assemble_synthesis(
    stage_d_output: StageDOutput,
    layer1_output: Layer1Output,
    audited_verdicts: dict[str, AgentVerdict],
    audit_warnings: list[str],
    llm_client: LLMClient,
) -> SynthesisOutput:
    """Assemble the complete synthesis output.

    This is the top-level entry point for E7. It orchestrates all builder
    functions and makes the single LLM call for the trade-off statement.

    Assembly order (dependencies flow downward):
    1. Provenance header -- from Stage D output + audit warnings.
    2. Assessment modes -- derived from provenance_per_candidate.
    3. Trade-off matrix -- from rubric matrix + requirements + scenario + modes.
    4. Candidate summaries -- from verdicts + tension map + rubric matrix + modes.
    5. Contested signals -- from verdicts + tension map.
    6. Epistemic disclaimers -- from assessment modes (F09, F10).
    7. Trade-off statement -- 1 LLM call (depends on matrix + summaries).
    8. Final SynthesisOutput assembly.

    Args:
        stage_d_output: Full Stage D -> Stage E contract.
        layer1_output: Layer 1 computation (tension map, signal labels, risk bands).
        audited_verdicts: Agent verdicts after Layer 3 audit, keyed by agent_role.
        audit_warnings: Warning strings collected by the Layer 3 audit.
        llm_client: LLM client for the trade-off statement call.

    Returns:
        Fully assembled SynthesisOutput.
    """
    logger.debug("Assembling synthesis: %d verdicts, %d audit warnings", len(audited_verdicts), len(audit_warnings))

    # 1. Provenance header.
    provenance = build_provenance_header(stage_d_output, audit_warnings)

    # 2. Assessment modes (needed by matrix and summaries).
    assessment_modes: dict[str, str] = {
        name: prov.assessment_mode.value for name, prov in stage_d_output.provenance_per_candidate.items()
    }

    # 3. Trade-off matrix.
    trade_off_matrix = build_trade_off_matrix(
        rubric_assessments=stage_d_output.rubric_matrix,
        requirements=stage_d_output.confirmed_requirements,
        scenario=stage_d_output.scenario,
        assessment_modes=assessment_modes,
    )

    # 4. Candidate summaries.
    candidate_summaries = build_candidate_summaries(
        verdicts=audited_verdicts,
        tension_map=layer1_output.tension_map,
        rubric_assessments=stage_d_output.rubric_matrix,
        assessment_modes=assessment_modes,
    )

    # 5. Contested signals (global list; also embedded per-candidate in summaries).
    contested_signals = detect_contested_signals(
        verdicts=audited_verdicts,
        tension_map=layer1_output.tension_map,
    )

    # 6. Epistemic disclaimers.
    epistemic_disclaimer, partial_mode_disclaimer = build_epistemic_disclaimers(assessment_modes)

    # 7. Trade-off statement (LLM call).
    trade_off_statement = await generate_trade_off_statement(
        matrix=trade_off_matrix,
        candidate_summaries=candidate_summaries,
        llm_client=llm_client,
    )

    logger.debug("Synthesis assembly complete.")

    # 8. Final assembly.
    return SynthesisOutput(
        provenance=provenance,
        trade_off_matrix=trade_off_matrix,
        candidate_summaries=candidate_summaries,
        trade_off_statement=trade_off_statement,
        contested_signals=contested_signals,
        epistemic_disclaimer=epistemic_disclaimer,
        partial_mode_disclaimer=partial_mode_disclaimer,
    )
