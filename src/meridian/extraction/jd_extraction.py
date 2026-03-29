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

from meridian.extraction.prompts.jd_extraction import build_jd_extraction_prompt
from meridian.extraction.protocols import LLMClient
from meridian.extraction.text_utils import strip_markdown_fences
from meridian.models import Requirement

logger = logging.getLogger(__name__)

__all__ = ["LLMClient"]


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


_VALID_SCENARIO_FIELDS: frozenset[str] = frozenset({
    "digital_transformation",
    "post_acquisition",
    "turnaround",
    "stabilization",
    "growth",
})


def parse_llm_response(raw_json: str) -> list[Requirement]:
    """Parse raw LLM JSON response into a Requirement list.

    Strips markdown fences if present, normalizes common LLM typos in
    scenario_priority field names, then validates against the Requirement schema.
    Individual requirements that fail validation are skipped with a warning.

    Args:
        raw_json: Raw JSON string from LLM.

    Returns:
        List of validated Requirement objects. May be shorter than the LLM output
        if individual items failed validation.

    Raises:
        ValueError: If JSON is invalid or not an array.
    """
    cleaned = strip_markdown_fences(raw_json)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from LLM: {exc}") from exc

    # Handle structured output wrapper: {"requirements": [...]}
    if isinstance(parsed, dict) and "requirements" in parsed:
        parsed = parsed["requirements"]

    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array (or {{requirements: [...]}}), got {type(parsed).__name__}")

    requirements: list[Requirement] = []
    for idx, item in enumerate(parsed):
        if isinstance(item, dict) and "scenario_priority" in item:
            item = {**item, "scenario_priority": _normalize_scenario_priority(item["scenario_priority"])}
        try:
            requirements.append(Requirement.model_validate(item))
        except Exception as exc:
            logger.warning("Requirement at index %d skipped (validation failed): %s", idx, exc)

    return requirements


def _normalize_scenario_priority(sp: dict) -> dict:
    """Fix common LLM typos in scenario_priority field names.

    Uses edit-distance-1 matching to map misspelled keys to valid field names.
    """
    if not isinstance(sp, dict):
        return sp

    normalized: dict[str, str] = {}
    for key, value in sp.items():
        if key in _VALID_SCENARIO_FIELDS:
            normalized[key] = value
        else:
            # Try to find closest valid field name
            match = _fuzzy_match_field(key)
            if match:
                logger.warning("Normalized scenario_priority field '%s' -> '%s'", key, match)
                normalized[match] = value
            else:
                logger.warning("Dropped unknown scenario_priority field '%s'", key)

    # Fill missing fields with 'medium' as safe default
    for field in _VALID_SCENARIO_FIELDS:
        if field not in normalized:
            logger.warning("Missing scenario_priority field '%s', defaulting to 'medium'", field)
            normalized[field] = "medium"

    return normalized


def _fuzzy_match_field(candidate: str) -> str | None:
    """Find the closest valid scenario field within edit distance 2."""
    candidate_lower = candidate.lower().strip()
    for valid in _VALID_SCENARIO_FIELDS:
        if _edit_distance(candidate_lower, valid) <= 2:
            return valid
    return None


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        return _edit_distance(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


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



# ---------------------------------------------------------------------------
# Validation check registries (Open/Closed)
# ---------------------------------------------------------------------------

# Warning-only checks run first against the original requirements.
_WARNING_CHECKS: tuple[WarningCheck, ...] = (
    _check_sequential_ids,
    _check_duplicates,
)

# Correcting checks run in sequence; each receives the output of the previous.
_CORRECTING_CHECKS: tuple[CorrectingCheck, ...] = (_check_routing_consistency,)


# ---------------------------------------------------------------------------
# Validation runner (KISS — single loop over registries)
# ---------------------------------------------------------------------------


def validate_extracted_requirements(
    requirements: list[Requirement],
) -> tuple[list[Requirement], list[str]]:
    """Run all registered validation checks.

    Executes warning-only checks, then correcting checks in sequence.
    Returns a new list of (possibly corrected) requirements and a list
    of warnings. Does not mutate the input list.

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
    response_format: dict | None = None,
) -> tuple[list[Requirement], list[str]]:
    """Full C1 pipeline: build prompt -> call LLM -> parse -> validate.

    Args:
        jd_text: Raw JD text.
        llm_client: Async LLM client satisfying the ``LLMClient`` protocol.
        response_format: Optional structured output schema for OpenAI-compatible models.

    Returns:
        Tuple of (validated_requirements, all_warnings).
    """
    system_prompt, user_prompt = build_jd_extraction_prompt(jd_text)

    raw_response = await llm_client.complete(
        system=system_prompt, user=user_prompt, response_format=response_format
    )
    logger.info("LLM response received for JD extraction (%d chars)", len(raw_response))

    requirements = parse_llm_response(raw_response)

    validated, validation_warnings = validate_extracted_requirements(requirements)

    all_warnings = [*count_warnings(validated), *validation_warnings]

    return validated, all_warnings
