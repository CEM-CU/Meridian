"""C1: JD requirement extraction pipeline.

Orchestrates one LLM call to extract discrete requirements from a job description,
then applies deterministic post-extraction validation. No mutable state — every
function takes typed inputs and returns typed outputs.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from shared.models import Priority, Requirement, ScenarioName

from stage_c.prompts.jd_extraction import build_jd_extraction_prompt
from stage_c.text_utils import strip_markdown_fences

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM client protocol (Dependency Inversion)
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMClient(Protocol):
    """Protocol defining the async LLM client interface for JD extraction.

    Any object with a matching ``complete`` method satisfies this protocol.
    """

    async def complete(self, system: str, user: str) -> str: ...


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Stopwords filtered during keyword overlap computation.
_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "have",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "was",
        "were",
        "will",
        "with",
        "not",
        "but",
        "can",
        "do",
        "if",
        "no",
        "so",
        "up",
        "out",
        "all",
        "been",
        "had",
        "her",
        "his",
        "how",
        "may",
        "new",
        "now",
        "old",
        "our",
        "own",
        "say",
        "she",
        "too",
        "who",
        "also",
        "than",
        "then",
        "this",
        "very",
    }
)

# Behavioral keywords that signal a requirement is NOT assessable from CV.
_BEHAVIORAL_KEYWORDS: frozenset[str] = frozenset(
    {
        "leadership",
        "interpersonal",
        "communication",
        "collaborative",
        "influence",
        "empathy",
        "mentoring",
        "coaching",
        "charisma",
        "emotional",
        "intelligence",
        "cultural",
        "fit",
        "style",
        "motivat",
        "inspir",
        "vision",
        "stakeholder",
        "relationship",
        "conflict",
        "resolution",
        "negotiat",
        "diplomacy",
        "trust",
        "team",
        "building",
        "adaptab",
        "resilien",
        "agil",
    }
)

# Expected sequential ID pattern.
_REQ_ID_PATTERN: re.Pattern[str] = re.compile(r"^REQ-(\d{2,})$")

# All scenario names for validation.
_ALL_SCENARIOS: frozenset[str] = frozenset(s.value for s in ScenarioName)


# ---------------------------------------------------------------------------
# Validation check type aliases (Open/Closed registry)
# ---------------------------------------------------------------------------

# A warning-only check: takes requirements, returns warnings.
type WarningCheck = Callable[[list[Requirement]], list[str]]

# A correcting check: takes requirements, returns (corrected_requirements, warnings).
type CorrectingCheck = Callable[[list[Requirement]], tuple[list[Requirement], list[str]]]

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_llm_response(raw_json: str) -> list[Requirement]:
    """Parse raw LLM JSON response into a Requirement list.

    Strips markdown fences if present, then validates against the Requirement schema.

    Args:
        raw_json: Raw JSON string from LLM.

    Returns:
        List of validated Requirement objects.

    Raises:
        ValueError: If JSON is invalid or doesn't match the Requirement schema.
    """
    cleaned = strip_markdown_fences(raw_json)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from LLM: {exc}") from exc

    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")

    requirements: list[Requirement] = []
    for idx, item in enumerate(parsed):
        try:
            requirements.append(Requirement.model_validate(item))
        except Exception as exc:
            raise ValueError(f"Requirement at index {idx} failed validation: {exc}") from exc

    return requirements


# ---------------------------------------------------------------------------
# Individual validation checks
# ---------------------------------------------------------------------------


def _check_sequential_ids(requirements: list[Requirement]) -> list[str]:
    """Verify requirement IDs are sequential: REQ-01, REQ-02, ..."""
    warnings: list[str] = []
    for idx, req in enumerate(requirements):
        expected_id = f"REQ-{idx + 1:02d}"
        match = _REQ_ID_PATTERN.match(req.requirement_id)
        if not match:
            warnings.append(f"Invalid ID format '{req.requirement_id}' at position {idx}; expected {expected_id}")
        elif req.requirement_id != expected_id:
            warnings.append(f"Non-sequential ID '{req.requirement_id}' at position {idx}; expected {expected_id}")
    return warnings


def _check_scenario_completeness(requirements: list[Requirement]) -> list[str]:
    """Verify each requirement has scenario_priority for all 5 scenarios."""
    warnings: list[str] = []
    for req in requirements:
        model_fields = set(type(req.scenario_priority).model_fields.keys())
        missing = _ALL_SCENARIOS - model_fields
        if missing:
            warnings.append(f"{req.requirement_id}: missing scenario priorities: {sorted(missing)}")
    return warnings


def _check_duplicates(requirements: list[Requirement]) -> list[str]:
    """Detect requirement pairs with >60% keyword overlap. Warn but do not merge."""
    warnings: list[str] = []
    for i in range(len(requirements)):
        for j in range(i + 1, len(requirements)):
            overlap = _keyword_overlap(requirements[i].text, requirements[j].text)
            if overlap > 0.6:
                warnings.append(
                    f"Possible duplicate: {requirements[i].requirement_id} and "
                    f"{requirements[j].requirement_id} have {overlap:.0%} keyword overlap"
                )
    return warnings


def _check_routing_consistency(
    requirements: list[Requirement],
) -> tuple[list[Requirement], list[str]]:
    """If assessable_from_cv=True but requirement looks behavioral, auto-correct to False.

    Returns a new list (no mutation) and any warnings generated.
    """
    warnings: list[str] = []
    corrected: list[Requirement] = []
    for req in requirements:
        if req.assessable_from_cv and _looks_behavioral(req.text):
            warnings.append(
                f"{req.requirement_id}: behavioral requirement marked assessable_from_cv=True; auto-corrected to False"
            )
            corrected.append(req.model_copy(update={"assessable_from_cv": False}))
        else:
            corrected.append(req)
    return corrected, warnings


def _check_priority_values(requirements: list[Requirement]) -> list[str]:
    """Verify all scenario_priority values are valid Priority enum values."""
    warnings: list[str] = []
    valid_values = {p.value for p in Priority}
    for req in requirements:
        sp = req.scenario_priority
        for scenario in _ALL_SCENARIOS:
            value = sp.for_scenario(scenario)
            if str(value) not in valid_values:
                warnings.append(f"{req.requirement_id}: invalid priority '{value}' for scenario '{scenario}'")
    return warnings


# ---------------------------------------------------------------------------
# Validation check registries (Open/Closed)
# ---------------------------------------------------------------------------

# Warning-only checks run first against the original requirements.
_WARNING_CHECKS: tuple[WarningCheck, ...] = (
    _check_sequential_ids,
    _check_scenario_completeness,
    _check_duplicates,
)

# Correcting checks run in sequence; each receives the output of the previous.
# Currently only routing consistency, but new correcting checks can be appended.
_CORRECTING_CHECKS: tuple[CorrectingCheck, ...] = (_check_routing_consistency,)

# Warning-only checks that run after corrections are applied.
_POST_CORRECTION_CHECKS: tuple[WarningCheck, ...] = (_check_priority_values,)


# ---------------------------------------------------------------------------
# Validation runner (KISS — single loop over registries)
# ---------------------------------------------------------------------------


def validate_extracted_requirements(
    requirements: list[Requirement],
) -> tuple[list[Requirement], list[str]]:
    """Run all registered validation checks.

    Executes warning-only checks, then correcting checks in sequence,
    then post-correction checks. Returns a new list of (possibly corrected)
    requirements and a list of warnings. Does not mutate the input list.

    Returns:
        Tuple of (validated_requirements, warnings).
    """
    warnings: list[str] = []

    for check in _WARNING_CHECKS:
        warnings.extend(check(requirements))

    corrected = list(requirements)
    for check in _CORRECTING_CHECKS:
        corrected, check_warnings = check(corrected)
        warnings.extend(check_warnings)

    for check in _POST_CORRECTION_CHECKS:
        warnings.extend(check(corrected))

    return corrected, warnings


# ---------------------------------------------------------------------------
# Text analysis helpers
# ---------------------------------------------------------------------------


def _looks_behavioral(text: str) -> bool:
    """Heuristic: does the requirement text look behavioral/interpersonal?

    Returns True if 2+ behavioral keywords appear in the text.
    """
    lower_text = text.lower()
    matches = sum(1 for kw in _BEHAVIORAL_KEYWORDS if kw in lower_text)
    return matches >= 2


def _keyword_overlap(text_a: str, text_b: str) -> float:
    """Compute keyword overlap ratio between two texts.

    Uses set intersection / set union on lowercased words, filtering stopwords.
    Returns 0.0 if both texts produce empty keyword sets.
    """
    keywords_a = _extract_keywords(text_a)
    keywords_b = _extract_keywords(text_b)
    if not keywords_a and not keywords_b:
        return 0.0
    intersection = keywords_a & keywords_b
    union = keywords_a | keywords_b
    return len(intersection) / len(union)


def _extract_keywords(text: str) -> set[str]:
    """Extract lowercased, non-stopword keywords from text."""
    words = text.lower().split()
    cleaned = (_strip_non_alpha(w) for w in words)
    return {w for w in cleaned if w and w not in _STOPWORDS}


def _strip_non_alpha(word: str) -> str:
    """Remove leading/trailing non-alphabetic characters from a word."""
    return word.strip(".,;:!?()[]{}\"'`~@#$%^&*-_+=<>/\\|0123456789")


# ---------------------------------------------------------------------------
# Count warnings
# ---------------------------------------------------------------------------


def count_warnings(requirements: list[Requirement]) -> list[str]:
    """Generate warnings about requirement count.

    Below 6: warning JD is too vague.
    Above 18: suggest consolidation.

    Returns:
        List of warning strings (may be empty).
    """
    warnings: list[str] = []
    count = len(requirements)
    if count < 6:
        warnings.append(f"Only {count} requirements extracted — JD may be too vague for reliable assessment")
    elif count > 18:
        warnings.append(f"{count} requirements extracted — consider consolidating to improve assessment focus")
    return warnings


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def extract_requirements(
    jd_text: str,
    llm_client: LLMClient,
) -> tuple[list[Requirement], list[str]]:
    """Full C1 pipeline: build prompt -> call LLM -> parse -> validate.

    Args:
        jd_text: Raw JD text.
        llm_client: Async LLM client satisfying the ``LLMClient`` protocol.

    Returns:
        Tuple of (validated_requirements, all_warnings).
    """
    system_prompt, user_prompt = build_jd_extraction_prompt(jd_text)

    raw_response = await llm_client.complete(system=system_prompt, user=user_prompt)
    logger.info("LLM response received for JD extraction (%d chars)", len(raw_response))

    requirements = parse_llm_response(raw_response)

    validated, validation_warnings = validate_extracted_requirements(requirements)

    all_warnings = [*count_warnings(validated), *validation_warnings]

    return validated, all_warnings
