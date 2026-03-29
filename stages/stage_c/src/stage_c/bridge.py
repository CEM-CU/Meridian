"""C4: Rubric-to-flag bridge.

Deterministic function (zero LLM calls) that converts RubricAssessments into Flags.
This is how CV evidence enters the flag pipeline. Each assessment is mapped to a flag
based on the rubric_level and the requirement's active priority under the selected scenario.
"""

from dataclasses import dataclass
from typing import NamedTuple

from shared.models import (
    Confidence,
    EvidenceType,
    Flag,
    FlagCategory,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioName,
    Valence,
)

# Stopwords filtered from topic_keywords (common English words that add no signal).
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


# ---------------------------------------------------------------------------
# Declarative mapping table: (rubric_level, priority) -> flag spec
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _FlagSpec:
    """Declarative specification for a flag produced by a (level, priority) pair."""

    name: str
    category: FlagCategory
    valence: Valence
    evidence_type: EvidenceType


class _MappingKey(NamedTuple):
    level: RubricLevel
    priority: Priority


# Open/Closed: adding a new mapping is a data change, not a code change.
_LEVEL_PRIORITY_MAP: dict[_MappingKey, _FlagSpec] = {
    # GAP on high or medium -> CV_GAP (low produces no flag)
    _MappingKey(RubricLevel.GAP, Priority.HIGH): _FlagSpec(
        name="CV_GAP",
        category=FlagCategory.EXPERIENCE_GAP,
        valence=Valence.NEGATIVE,
        evidence_type=EvidenceType.REQUIREMENT_GAP,
    ),
    _MappingKey(RubricLevel.GAP, Priority.MEDIUM): _FlagSpec(
        name="CV_GAP",
        category=FlagCategory.EXPERIENCE_GAP,
        valence=Valence.NEGATIVE,
        evidence_type=EvidenceType.REQUIREMENT_GAP,
    ),
    # PARTIAL on high only
    _MappingKey(RubricLevel.PARTIAL, Priority.HIGH): _FlagSpec(
        name="CV_PARTIAL",
        category=FlagCategory.EXPERIENCE_GAP,
        valence=Valence.NEGATIVE,
        evidence_type=EvidenceType.CV_RUBRIC,
    ),
    # EXCEEDS on high or medium
    _MappingKey(RubricLevel.EXCEEDS, Priority.HIGH): _FlagSpec(
        name="CV_EXCEEDS",
        category=FlagCategory.EXPERIENCE_STRENGTH,
        valence=Valence.POSITIVE,
        evidence_type=EvidenceType.CV_RUBRIC,
    ),
    _MappingKey(RubricLevel.EXCEEDS, Priority.MEDIUM): _FlagSpec(
        name="CV_EXCEEDS",
        category=FlagCategory.EXPERIENCE_STRENGTH,
        valence=Valence.POSITIVE,
        evidence_type=EvidenceType.CV_RUBRIC,
    ),
}

_BEHAVIORAL_ROUTING_SPEC = _FlagSpec(
    name="CV_BEHAVIORAL_ROUTED",
    category=FlagCategory.ROUTING,
    valence=Valence.NEUTRAL,
    evidence_type=EvidenceType.ROUTING,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def bridge_rubric_to_flags(
    assessments: list[RubricAssessment],
    requirements: list[Requirement],
    scenario_name: ScenarioName,
) -> list[Flag]:
    """Convert rubric assessments into flags for the flag pipeline.

    Resolves each requirement's active priority under the given scenario,
    applies mapping rules per (rubric_level, priority) pair, then runs
    pattern-level detectors across the full assessment set per candidate.
    """
    req_lookup = _build_requirement_lookup(requirements)
    individual_flags = _map_individual_flags(assessments, req_lookup, scenario_name)
    pattern_flags = _detect_pattern_flags(assessments, req_lookup, scenario_name)
    return [*individual_flags, *pattern_flags]


def _build_requirement_lookup(requirements: list[Requirement]) -> dict[str, Requirement]:
    """Build a requirement_id -> Requirement dict for O(1) lookups."""
    return {r.requirement_id: r for r in requirements}


def _map_individual_flags(
    assessments: list[RubricAssessment],
    req_lookup: dict[str, Requirement],
    scenario_name: ScenarioName,
) -> list[Flag]:
    """Apply per-assessment mapping rules to produce individual flags.

    Assessments referencing unknown requirement IDs are silently skipped.
    """
    flags: list[Flag] = []
    for assessment in assessments:
        requirement = req_lookup.get(assessment.requirement_id)
        if requirement is None:
            continue
        flag = _map_single_assessment(assessment, requirement, scenario_name)
        if flag is not None:
            flags.append(flag)
    return flags


def _map_single_assessment(
    assessment: RubricAssessment,
    requirement: Requirement,
    scenario_name: ScenarioName,
) -> Flag | None:
    """Map one (assessment, requirement, scenario) triple to a Flag or None.

    Returns None for MEETS (baseline), GAP on low-priority (background noise),
    and any other combination not in the mapping table.
    """
    level = assessment.rubric_level
    active_priority = requirement.scenario_priority.for_scenario(scenario_name)

    # Behavioral routing: NOT_ASSESSABLE on non-CV-assessable requirement
    if level == RubricLevel.NOT_ASSESSABLE and not requirement.assessable_from_cv:
        return _build_flag(
            spec=_BEHAVIORAL_ROUTING_SPEC,
            assessment=assessment,
            requirement=requirement,
            active_priority=active_priority,
        )

    # Table lookup for all standard (level, priority) combinations
    spec = _LEVEL_PRIORITY_MAP.get(_MappingKey(level, active_priority))
    if spec is None:
        return None

    return _build_flag(
        spec=spec,
        assessment=assessment,
        requirement=requirement,
        active_priority=active_priority,
    )


def _build_flag(
    *,
    spec: _FlagSpec,
    assessment: RubricAssessment,
    requirement: Requirement,
    active_priority: Priority,
) -> Flag:
    """Construct a Flag with full provenance from an assessment and requirement."""
    return Flag(
        name=spec.name,
        candidate_name=assessment.candidate_name,
        category=spec.category,
        valence=spec.valence,
        evidence_type=spec.evidence_type,
        requirement_id=assessment.requirement_id,
        rubric_level=str(assessment.rubric_level),
        cv_citation=assessment.cv_citation,
        cv_location=assessment.cv_location,
        confidence=str(assessment.confidence),
        notes=assessment.notes,
        investigation_question=assessment.investigation_question,
        topic_keywords=_extract_topic_keywords(requirement.text),
        metadata={
            "active_priority": str(active_priority),
            "requirement_text": requirement.text,
        },
    )


def _extract_topic_keywords(text: str) -> list[str]:
    """Derive topic keywords from requirement text.

    Splits on whitespace, lowercases, strips non-alpha chars, and filters stopwords.
    """
    words = text.lower().split()
    cleaned = [_strip_non_alpha(w) for w in words]
    return [w for w in cleaned if w and w not in _STOPWORDS]


def _strip_non_alpha(word: str) -> str:
    """Remove leading/trailing non-alphabetic characters from a word."""
    return word.strip(".,;:!?()[]{}\"'`~@#$%^&*-_+=<>/\\|0123456789")


# ---------------------------------------------------------------------------
# Pattern-level flag detectors
# ---------------------------------------------------------------------------


def _detect_pattern_flags(
    assessments: list[RubricAssessment],
    req_lookup: dict[str, Requirement],
    scenario_name: ScenarioName,
) -> list[Flag]:
    """Run pattern detectors across all assessments, grouped by candidate."""
    candidates = _group_by_candidate(assessments)
    pattern_flags: list[Flag] = []
    for candidate_name, candidate_assessments in candidates.items():
        pattern_flags.extend(_detect_low_confidence_cluster(candidate_name, candidate_assessments, req_lookup))
        pattern_flags.extend(_detect_systematic_gap(candidate_name, candidate_assessments, req_lookup, scenario_name))
    return pattern_flags


def _group_by_candidate(assessments: list[RubricAssessment]) -> dict[str, list[RubricAssessment]]:
    """Group assessments by candidate_name, preserving order."""
    groups: dict[str, list[RubricAssessment]] = {}
    for a in assessments:
        groups.setdefault(a.candidate_name, []).append(a)
    return groups


def _collect_keywords_for_requirements(
    requirement_ids: list[str],
    req_lookup: dict[str, Requirement],
) -> list[str]:
    """Gather topic keywords for a list of requirement IDs."""
    keywords: list[str] = []
    for rid in requirement_ids:
        if rid in req_lookup:
            keywords.extend(_extract_topic_keywords(req_lookup[rid].text))
    return keywords


def _detect_low_confidence_cluster(
    candidate_name: str,
    assessments: list[RubricAssessment],
    req_lookup: dict[str, Requirement],
) -> list[Flag]:
    """3+ low-confidence assessments -> CV_LOW_CONFIDENCE_CLUSTER flag."""
    low_conf = [a for a in assessments if a.confidence == Confidence.LOW]
    if len(low_conf) < 3:
        return []

    req_ids = [a.requirement_id for a in low_conf]
    return [
        Flag(
            name="CV_LOW_CONFIDENCE_CLUSTER",
            candidate_name=candidate_name,
            category=FlagCategory.EVIDENCE_QUALITY,
            valence=Valence.NEGATIVE,
            evidence_type=EvidenceType.CV_PATTERN,
            topic_keywords=_collect_keywords_for_requirements(req_ids, req_lookup),
            metadata={
                "low_confidence_count": len(low_conf),
                "requirement_ids": req_ids,
            },
        )
    ]


def _detect_systematic_gap(
    candidate_name: str,
    assessments: list[RubricAssessment],
    req_lookup: dict[str, Requirement],
    scenario_name: ScenarioName,
) -> list[Flag]:
    """>50% of high-priority requirements are GAP -> CV_SYSTEMATIC_GAP flag."""
    high_priority_assessments = [
        a
        for a in assessments
        if a.requirement_id in req_lookup
        and req_lookup[a.requirement_id].scenario_priority.for_scenario(scenario_name) == Priority.HIGH
    ]
    if not high_priority_assessments:
        return []

    gap_count = sum(1 for a in high_priority_assessments if a.rubric_level == RubricLevel.GAP)
    if gap_count <= len(high_priority_assessments) / 2:
        return []

    gap_req_ids = [a.requirement_id for a in high_priority_assessments if a.rubric_level == RubricLevel.GAP]
    return [
        Flag(
            name="CV_SYSTEMATIC_GAP",
            candidate_name=candidate_name,
            category=FlagCategory.EXPERIENCE_GAP,
            valence=Valence.NEGATIVE,
            evidence_type=EvidenceType.CV_PATTERN,
            topic_keywords=_collect_keywords_for_requirements(gap_req_ids, req_lookup),
            metadata={
                "high_priority_total": len(high_priority_assessments),
                "gap_count": gap_count,
                "gap_requirement_ids": gap_req_ids,
            },
        )
    ]
