"""CV flag stream validation (D2).

Validates CV-derived flags from the C4 bridge. Strips invalid flags, logs issues,
and returns a clean set. Zero LLM calls — entirely deterministic validation logic.
"""

from __future__ import annotations

import logging

from meridian.models import (
    EvidenceType,
    Flag,
    Requirement,
    ScenarioName,
)

logger = logging.getLogger(__name__)

# Canonical set of valid CV flag names.
_CV_FLAG_VOCABULARY: frozenset[str] = frozenset(
    {
        "CV_GAP",
        "CV_PARTIAL",
        "CV_EXCEEDS",
        "CV_BEHAVIORAL_ROUTED",
        "CV_LOW_CONFIDENCE_CLUSTER",
        "CV_SYSTEMATIC_GAP",
    }
)

# Valid evidence types for CV-derived flags.
_CV_EVIDENCE_TYPES: frozenset[str] = frozenset(
    {
        EvidenceType.CV_RUBRIC,
        EvidenceType.REQUIREMENT_GAP,
        EvidenceType.CV_PATTERN,
        EvidenceType.ROUTING,
    }
)

# Pattern flags that do not require requirement_id or active_priority metadata.
_PATTERN_FLAGS: frozenset[str] = frozenset(
    {
        "CV_LOW_CONFIDENCE_CLUSTER",
        "CV_SYSTEMATIC_GAP",
    }
)


def validate_cv_flags(
    flags: list[Flag],
    confirmed_requirements: list[Requirement],
    scenario_name: ScenarioName,
) -> tuple[list[Flag], list[str]]:
    """Validate CV-derived flags. Strip invalid, return clean set + warnings.

    Performs the following checks against each flag:
    1. Flag name must be in the canonical CV flag vocabulary.
    2. Every CV flag must have requirement_id, rubric_level, and an evidence_type
       in the valid CV evidence types set. Pattern flags are exempt from
       requirement_id.
    3. requirement_id (when present) must reference a requirement in the
       confirmed_requirements list.
    4. Flag metadata must contain active_priority matching the requirement's
       scenario_priority for the active scenario. Pattern flags are exempt.

    On any violation, the flag is stripped and a warning string is added.

    Args:
        flags: List of CV-derived Flag objects from the C4 bridge.
        confirmed_requirements: List of confirmed Requirement objects from C1.
        scenario_name: The active scenario used to resolve scenario-specific priorities.

    Returns:
        A tuple of (valid_flags, warnings) where valid_flags is the cleaned list
        and warnings is a list of human-readable warning strings for each stripped flag.
    """
    req_map: dict[str, Requirement] = {r.requirement_id: r for r in confirmed_requirements}
    valid_flags: list[Flag] = []
    warnings: list[str] = []

    for flag in flags:
        rejection_reason = _validate_single_flag(flag, req_map, scenario_name)
        if rejection_reason is None:
            valid_flags.append(flag)
        else:
            warning = f"CV flag '{flag.name}' stripped: {rejection_reason}"
            warnings.append(warning)
            logger.warning(warning)

    return valid_flags, warnings


def _validate_single_flag(
    flag: Flag,
    req_map: dict[str, Requirement],
    scenario_name: ScenarioName,
) -> str | None:
    """Validate a single CV flag against all rules.

    Returns None if valid, or a reason string if the flag should be stripped.
    """
    # Check 1: Flag name must be in the canonical vocabulary.
    if flag.name not in _CV_FLAG_VOCABULARY:
        return f"name '{flag.name}' not in CV flag vocabulary"

    # Check 2a: Evidence type must be a valid CV evidence type.
    if flag.evidence_type.value not in _CV_EVIDENCE_TYPES:
        return f"evidence_type '{flag.evidence_type}' not in valid CV evidence types"

    # Check 2b: rubric_level must be present for all CV flags.
    if flag.rubric_level is None:
        return "missing required field: rubric_level"

    is_pattern_flag = flag.name in _PATTERN_FLAGS

    # Check 2c: requirement_id required for non-pattern flags.
    if not is_pattern_flag and flag.requirement_id is None:
        return "missing required field: requirement_id"

    # Check 3: requirement_id must reference a known requirement (non-pattern flags).
    if not is_pattern_flag and flag.requirement_id is not None:
        if flag.requirement_id not in req_map:
            return f"requirement_id '{flag.requirement_id}' not found in confirmed requirements"

        # Check 4: active_priority in metadata must match the requirement's scenario priority.
        requirement = req_map[flag.requirement_id]
        expected_priority = requirement.scenario_priority.for_scenario(scenario_name.value)
        active_priority = flag.metadata.get("active_priority")

        if active_priority is None:
            return "metadata missing required field: active_priority"

        if active_priority != expected_priority.value:
            return (
                f"metadata active_priority '{active_priority}' does not match "
                f"expected '{expected_priority.value}' for scenario '{scenario_name}'"
            )

    return None
