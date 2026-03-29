"""Layer 0 — Stage D Output Validation (E1).

Entry gate for Stage E. Validates Stage D's merged flag set before any
downstream evaluation logic touches it. Zero LLM calls. Fail-open: strips
invalid flags, logs issues, and proceeds with the clean subset. Never blocks
the pipeline.

Three checks:
1. Flag vocabulary membership — every flag name must exist in the canonical set.
2. Metadata completeness — required fields present for each flag type.
3. Provenance chain integrity — requirement_ids and big_five_source dimensions
   must resolve to real objects in the input data.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from meridian.models.flags import EvidenceType, Flag

if TYPE_CHECKING:
    from meridian.models.candidates import CandidateData
    from meridian.models.pipeline import StageDOutput
    from meridian.models.requirements import Requirement

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical flag vocabulary
# ---------------------------------------------------------------------------

_PERSONALITY_FLAG_NAMES: frozenset[str] = frozenset(
    {
        "EXECUTION_CONSCIENTIOUSNESS_FIT",
        "EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
        "STRATEGIC_OPENNESS_FIT",
        "STRATEGIC_LOW_OPENNESS_RISK",
        "DERAILMENT_NEUROTICISM_UNDER_STRESS",
        "DARK_SIDE_LOW_AGREEABLENESS",
        "CULTURAL_EXTRAVERSION_FIT",
        "CULTURAL_INTROVERSION_NOTE",
        "COLLISION_DUAL_DOMINANCE",
        "COMPLEMENT_EXTRAVERSION_BALANCE",
        "FRICTION_CONSCIENTIOUSNESS_GAP",
        "COMPLEMENT_OPENNESS_DIVERSITY",
        "GROUPTHINK_AGREEABLENESS_CLUSTER",
    }
)

_CV_FLAG_NAMES: frozenset[str] = frozenset(
    {
        "CV_GAP",
        "CV_PARTIAL",
        "CV_EXCEEDS",
        "CV_BEHAVIORAL_ROUTED",
        "CV_LOW_CONFIDENCE_CLUSTER",
        "CV_SYSTEMATIC_GAP",
    }
)

_ALL_FLAG_NAMES: frozenset[str] = _PERSONALITY_FLAG_NAMES | _CV_FLAG_NAMES

# CV evidence types — flags carrying these are treated as CV-derived.
_CV_EVIDENCE_TYPES: frozenset[EvidenceType] = frozenset(
    {
        EvidenceType.CV_RUBRIC,
        EvidenceType.REQUIREMENT_GAP,
        EvidenceType.CV_PATTERN,
        EvidenceType.ROUTING,
    }
)

# Pattern flags exempt from requirement_id / rubric_level checks.
_PATTERN_FLAGS: frozenset[str] = frozenset(
    {
        "CV_LOW_CONFIDENCE_CLUSTER",
        "CV_SYSTEMATIC_GAP",
    }
)

# Valid Big Five dimension characters.
_VALID_BIG_FIVE_DIMS: frozenset[str] = frozenset({"O", "C", "E", "A", "N"})


# ---------------------------------------------------------------------------
# Per-flag validation helpers
# ---------------------------------------------------------------------------


def _check_vocabulary(flag: Flag) -> str | None:
    """Return an error string if the flag name is not in the canonical vocabulary."""
    if flag.name not in _ALL_FLAG_NAMES:
        return f"HALLUCINATED_FLAG_IN_DERIVATION: name '{flag.name}' not in canonical vocabulary"
    return None


def _check_metadata(flag: Flag) -> list[str]:
    """Return a list of error strings for any missing required metadata fields."""
    errors: list[str] = []

    # Universal required fields (already enforced by Pydantic, but guard defensively)
    for field in ("candidate_name", "category", "valence", "evidence_type"):
        if not getattr(flag, field, None):
            errors.append(f"missing required field: {field}")

    is_cv = flag.evidence_type in _CV_EVIDENCE_TYPES
    is_pattern = flag.name in _PATTERN_FLAGS

    if is_cv and not is_pattern:
        if flag.requirement_id is None:
            errors.append("CV flag missing required field: requirement_id")
        if flag.rubric_level is None:
            errors.append("CV flag missing required field: rubric_level")
    elif not is_cv:
        # Personality flag
        if flag.big_five_source is None:
            errors.append("personality flag missing required field: big_five_source")

    return errors


def _check_provenance(
    flag: Flag,
    req_map: dict[str, Requirement],
    candidate_map: dict[str, CandidateData],
) -> list[str]:
    """Return a list of error strings for broken provenance chain references."""
    errors: list[str] = []

    is_cv = flag.evidence_type in _CV_EVIDENCE_TYPES
    is_pattern = flag.name in _PATTERN_FLAGS

    if is_cv and not is_pattern and flag.requirement_id is not None and flag.requirement_id not in req_map:
        errors.append(f"CV flag requirement_id '{flag.requirement_id}' not found in confirmed_requirements")

    if not is_cv and flag.big_five_source is not None:
        source = flag.big_five_source
        if source not in _VALID_BIG_FIVE_DIMS:
            errors.append(f"personality flag big_five_source '{source}' is not one of O/C/E/A/N")
        else:
            candidate = candidate_map.get(flag.candidate_name)
            if candidate is None or candidate.big_five is None:
                errors.append(
                    f"personality flag big_five_source '{source}' cannot be verified: "
                    f"candidate '{flag.candidate_name}' has no Big Five scores"
                )
            else:
                score = getattr(candidate.big_five, source, None)
                if score is None:
                    errors.append(
                        f"personality flag big_five_source '{source}' not found "
                        f"on candidate '{flag.candidate_name}' Big Five scores"
                    )

    return errors


# ---------------------------------------------------------------------------
# Single-flag orchestrator
# ---------------------------------------------------------------------------


def _validate_flag(
    flag: Flag,
    req_map: dict[str, Requirement],
    candidate_map: dict[str, CandidateData],
) -> list[str]:
    """Run all three checks on a single flag.

    Returns a (possibly empty) list of failure reasons. An empty list means
    the flag is valid. Multiple failures on the same flag are collected and
    reported together, but the flag is still stripped only once.
    """
    reasons: list[str] = []

    vocab_error = _check_vocabulary(flag)
    if vocab_error:
        # Skip the remaining checks — there is no meaningful provenance to verify
        # for a flag with an unknown name.
        return [vocab_error]

    reasons.extend(_check_metadata(flag))
    reasons.extend(_check_provenance(flag, req_map, candidate_map))
    return reasons


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_stage_d_output(
    stage_d_output: StageDOutput,
) -> tuple[StageDOutput, list[str]]:
    """Validate Stage D output and return a cleaned version.

    Runs all three validation checks (vocabulary, metadata completeness,
    provenance chain) on every flag in ``stage_d_output.flags``. Invalid
    flags are stripped and a human-readable warning is appended to the
    returned list. A new ``StageDOutput`` is constructed via ``model_copy``
    so the input object is never mutated.

    Never raises or blocks the pipeline. On total failure (every flag
    invalid) the output carries an empty flag list.

    Args:
        stage_d_output: The ``StageDOutput`` produced by Stage D.

    Returns:
        A tuple of ``(cleaned_output, warnings)`` where ``cleaned_output``
        is a new ``StageDOutput`` with only valid flags and ``warnings`` is
        a list of strings describing each stripped flag and the reasons.
    """
    req_map: dict[str, Requirement] = {r.requirement_id: r for r in stage_d_output.confirmed_requirements}
    candidate_map: dict[str, CandidateData] = {c.name: c for c in stage_d_output.candidate_data}

    valid_flags: list[Flag] = []
    warnings: list[str] = []

    for flag in stage_d_output.flags:
        reasons = _validate_flag(flag, req_map, candidate_map)
        if not reasons:
            valid_flags.append(flag)
        else:
            combined = "; ".join(reasons)
            warning = f"Flag '{flag.name}' (candidate='{flag.candidate_name}') stripped: {combined}"
            warnings.append(warning)
            logger.warning(warning)

    cleaned = stage_d_output.model_copy(update={"flags": valid_flags})
    return cleaned, warnings
