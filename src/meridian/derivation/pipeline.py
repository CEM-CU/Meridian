"""Stage D pipeline orchestrator.

Wires D1 (personality flags) → D2 (CV flag validation) → D3 (merge) →
D4 (validation) → D5 (assessment mode) → D6 (output assembly) and
returns the final StageDOutput contract for Stage E consumption.

Zero LLM calls. Entirely deterministic. Latency: <1s.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from meridian.derivation.assessment_mode import determine_modes_batch
from meridian.derivation.cv_flag_validation import validate_cv_flags
from meridian.derivation.merge import merge_all_candidates
from meridian.derivation.output_assembly import assemble_stage_d_output
from meridian.derivation.personality_flags import derive_personality_flags
from meridian.derivation.validation import validate_merged_flags

if TYPE_CHECKING:
    from meridian.models import Flag
    from meridian.models.pipeline import StageCOutput, StageDOutput

logger = logging.getLogger(__name__)


def run_stage_d(
    stage_c_output: StageCOutput,
    cv_flags: list[Flag],
) -> StageDOutput:
    """Execute the full Stage D pipeline: derive → validate → merge → validate → assemble.

    Args:
        stage_c_output: Complete Stage C output (requirements, rubric assessments,
            candidate data, scenario config).
        cv_flags: CV-derived flags from the Stage C bridge (C4 output).

    Returns:
        Complete StageDOutput ready for Stage E consumption.
    """
    scenario = stage_c_output.scenario
    candidates = stage_c_output.candidate_data
    requirements = stage_c_output.requirements
    rubric_assessments = stage_c_output.rubric_assessments

    # D5: Assessment mode determination (needed early for D1 gating and D4 checks)
    modes = determine_modes_batch(candidates)
    logger.info(
        "D5 complete: modes=%s",
        {name: mode.value for name, (mode, _) in modes.items()},
    )

    # D1: Personality flag derivation (per candidate)
    personality_flags_per_candidate: dict[str, list[Flag]] = {}
    for candidate in candidates:
        personality_flags_per_candidate[candidate.name] = derive_personality_flags(
            candidate, scenario, candidate.team_context or None
        )
    total_personality = sum(len(f) for f in personality_flags_per_candidate.values())
    logger.info("D1 complete: %d personality flags across %d candidates", total_personality, len(candidates))

    # D2: CV flag validation (per candidate)
    cv_flags_by_candidate: dict[str, list[Flag]] = {}
    for candidate in candidates:
        candidate_cv_flags = [f for f in cv_flags if f.candidate_name == candidate.name]
        validated, d2_warnings = validate_cv_flags(candidate_cv_flags, requirements, scenario.name)
        cv_flags_by_candidate[candidate.name] = validated
        for w in d2_warnings:
            logger.warning("D2: %s", w)
    total_cv = sum(len(f) for f in cv_flags_by_candidate.values())
    logger.info("D2 complete: %d validated CV flags across %d candidates", total_cv, len(candidates))

    # D3: Merge
    merged = merge_all_candidates(personality_flags_per_candidate, cv_flags_by_candidate)
    total_merged = sum(len(f) for f in merged.values())
    logger.info("D3 complete: %d merged flags", total_merged)

    # D4: Validation Layer 0
    assessment_mode_strings = {name: mode.value for name, (mode, _) in modes.items()}
    validated_flags, validation_warnings, coherence_notes = validate_merged_flags(
        merged, rubric_assessments, requirements, assessment_mode_strings
    )
    for w in validation_warnings:
        logger.warning("D4: %s", w)
    for n in coherence_notes:
        logger.info("D4 coherence: %s", n)
    total_validated = sum(len(f) for f in validated_flags.values())
    logger.info("D4 complete: %d flags after validation (%d warnings)", total_validated, len(validation_warnings))

    # D6: Output assembly
    output = assemble_stage_d_output(
        validated_flags_per_candidate=validated_flags,
        modes_per_candidate=modes,
        stage_c_output=stage_c_output,
        validation_warnings=validation_warnings,
        coherence_notes=coherence_notes,
    )
    logger.info("D6 complete: StageDOutput assembled with %d total flags", len(output.flags))

    return output
