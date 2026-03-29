"""D6: Output assembly — constructs the StageDOutput contract for Stage E.

Assembles validated flags, per-candidate provenance metadata, and pass-through
data from Stage C into the final StageDOutput. Zero LLM calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from meridian.models.flags import EvidenceType, Flag
from meridian.models.pipeline import (
    AssessmentMode,
    FlagProvenance,
    StageCOutput,
    StageDOutput,
)

if TYPE_CHECKING:
    from meridian.models.candidates import CandidateData


def assemble_stage_d_output(
    validated_flags_per_candidate: dict[str, list[Flag]],
    modes_per_candidate: dict[str, tuple[AssessmentMode, str]],
    stage_c_output: StageCOutput,
    validation_warnings: list[str],
    coherence_notes: list[str],
) -> StageDOutput:
    """Assemble the final Stage D output.

    Args:
        validated_flags_per_candidate: From D4 validation (post-merge, post-validation).
        modes_per_candidate: From D5 (assessment mode + provenance string).
        stage_c_output: The full Stage C output (for pass-through fields).
        validation_warnings: From D4 (dimension coverage warnings).
        coherence_notes: From D4 Check 4 (cross-stream coherence notes).

    Returns:
        Complete StageDOutput ready for Stage E consumption.
    """
    candidate_lookup: dict[str, CandidateData] = {c.name: c for c in stage_c_output.candidate_data}
    cv_assessable_count = sum(1 for r in stage_c_output.requirements if r.assessable_from_cv)

    provenance_per_candidate: dict[str, FlagProvenance] = {}
    for candidate_name, flags in validated_flags_per_candidate.items():
        mode, provenance_description = modes_per_candidate.get(candidate_name, (AssessmentMode.PARTIAL, ""))
        candidate_data = candidate_lookup[candidate_name]
        provenance_per_candidate[candidate_name] = _build_provenance(
            candidate_name=candidate_name,
            flags=flags,
            mode=mode,
            provenance_description=provenance_description,
            candidate_data=candidate_data,
            cv_assessable_count=cv_assessable_count,
            dimension_warnings=_filter_candidate_warnings(validation_warnings, candidate_name),
            coherence_notes=_filter_candidate_warnings(coherence_notes, candidate_name),
        )

    flat_flags: list[Flag] = [flag for flags in validated_flags_per_candidate.values() for flag in flags]

    return StageDOutput(
        flags=flat_flags,
        provenance_per_candidate=provenance_per_candidate,
        confirmed_requirements=list(stage_c_output.requirements),
        candidate_data=list(stage_c_output.candidate_data),
        rubric_matrix=list(stage_c_output.rubric_assessments),
        scenario=stage_c_output.scenario,
    )


def _build_provenance(
    candidate_name: str,
    flags: list[Flag],
    mode: AssessmentMode,
    provenance_description: str,
    candidate_data: CandidateData,
    cv_assessable_count: int,
    dimension_warnings: list[str],
    coherence_notes: list[str],
) -> FlagProvenance:
    """Build FlagProvenance for a single candidate.

    Args:
        candidate_name: Name of the candidate.
        flags: Validated flags for this candidate.
        mode: Assessment mode (full or partial).
        provenance_description: Human-readable provenance from D5.
        candidate_data: Full candidate data (for personality_source).
        cv_assessable_count: Number of CV-assessable requirements.
        dimension_warnings: Dimension coverage warnings from D4 Check 3.
        coherence_notes: Cross-stream coherence notes from D4 Check 4.

    Returns:
        FlagProvenance for the candidate.
    """
    personality_count = sum(1 for f in flags if f.evidence_type == EvidenceType.SCORED_FLAG)
    cv_count = sum(1 for f in flags if f.evidence_type != EvidenceType.SCORED_FLAG)
    high_gap_count = _count_high_priority_gaps(flags)

    return FlagProvenance(
        assessment_mode=mode,
        personality_flag_count=personality_count,
        cv_flag_count=cv_count,
        total_flags=personality_count + cv_count,
        big_five_available=(mode == AssessmentMode.FULL),
        personality_source=candidate_data.personality_source,
        requirements_assessed=cv_assessable_count,
        high_priority_gap_count=high_gap_count,
        dimension_coverage_warnings=dimension_warnings,
        cross_stream_coherence_notes=coherence_notes,
    )


def _count_high_priority_gaps(flags: list[Flag]) -> int:
    """Count CV_GAP flags with high active_priority in metadata.

    Args:
        flags: Flags for one candidate.

    Returns:
        Number of CV_GAP flags with metadata["active_priority"] == "high".
    """
    return sum(1 for f in flags if f.name == "CV_GAP" and f.metadata.get("active_priority") == "high")


def _filter_candidate_warnings(warnings: list[str], candidate_name: str) -> list[str]:
    """Filter a warning list to entries that mention the given candidate.

    Args:
        warnings: Full warning or note list from D4.
        candidate_name: Candidate name to filter by.

    Returns:
        Subset of warnings referencing this candidate.
    """
    return [w for w in warnings if f"'{candidate_name}'" in w]
