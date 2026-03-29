"""D5: Assessment mode determination.

Determines per-candidate AssessmentMode (full or partial) based on
BigFiveScores presence. Zero LLM calls — entirely deterministic.
"""

from meridian.models.candidates import CandidateData
from meridian.models.pipeline import AssessmentMode


def determine_assessment_mode(
    candidate: CandidateData,
) -> tuple[AssessmentMode, str]:
    """Determine assessment mode for a single candidate.

    Returns:
        Tuple of (mode, provenance_description).
        provenance_description explains the data source.
    """
    mode = AssessmentMode.FULL if candidate.big_five is not None else AssessmentMode.PARTIAL
    provenance = _resolve_provenance(candidate.personality_source, candidate.big_five)
    return mode, provenance


def determine_modes_batch(
    candidates: list[CandidateData],
) -> dict[str, tuple[AssessmentMode, str]]:
    """Determine assessment mode for all candidates.

    Returns:
        Dict mapping candidate name to (mode, provenance_description).
    """
    return {candidate.name: determine_assessment_mode(candidate) for candidate in candidates}


def _resolve_provenance(
    personality_source: str | None,
    big_five: object | None,
) -> str:
    """Build a human-readable provenance description.

    Args:
        personality_source: The personality_source field from CandidateData.
        big_five: The big_five field (used only for None check).

    Returns:
        A provenance description string.
    """
    if personality_source is None and big_five is None:
        return "No personality data provided"

    if personality_source is None:
        return "Unknown source"

    _PRESET_PREFIX = "Preset — "
    if personality_source.startswith(_PRESET_PREFIX):
        archetype_name = personality_source[len(_PRESET_PREFIX) :]
        return f"Preset archetype — {archetype_name}"

    if personality_source.startswith("Preset"):
        return personality_source

    if personality_source.startswith("Modified preset"):
        return personality_source

    if personality_source == "manual":
        return "Manual Big Five score entry"

    return personality_source
