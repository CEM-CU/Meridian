"""D4: Validation Layer 0 — 5 deterministic checks on the merged flag set.

Validates internal consistency of the flag set before it passes to Stage E.
All checks are deterministic (zero LLM calls). Checks 1-3 may remove flags.
Checks 4-5 are advisory (produce warnings but don't modify flags).
"""

from __future__ import annotations

from collections import defaultdict

from shared.models import (
    EvidenceType,
    Flag,
    FlagCategory,
    Requirement,
    RubricAssessment,
    RubricLevel,
    Valence,
)

# ---------------------------------------------------------------------------
# Contradiction data (declarative, Open/Closed)
# ---------------------------------------------------------------------------

_UNCONDITIONAL_CONTRADICTIONS: list[tuple[str, str]] = [
    ("EXECUTION_CONSCIENTIOUSNESS_FIT", "EXECUTION_LOW_CONSCIENTIOUSNESS_RISK"),
    ("STRATEGIC_OPENNESS_FIT", "STRATEGIC_LOW_OPENNESS_RISK"),
    ("CULTURAL_EXTRAVERSION_FIT", "CULTURAL_INTROVERSION_NOTE"),
]

# CV flag name pairs that contradict only when they share the same requirement_id.
_CONDITIONAL_CONTRADICTIONS: list[tuple[str, str]] = [
    ("CV_EXCEEDS", "CV_GAP"),
    ("CV_EXCEEDS", "CV_PARTIAL"),
    ("CV_SCOPE_EXCEEDS", "CV_SCOPE_GAP"),
    ("CV_EXCEEDS_HIGH_PRIORITY", "CV_GAP_HIGH_PRIORITY"),
]

# Big Five dimension → personality flag category domain mapping for cross-stream check.
_PERSONALITY_CATEGORY_DOMAIN: dict[FlagCategory, str] = {
    FlagCategory.EXECUTION: "EXECUTION",
    FlagCategory.STRATEGIC: "STRATEGIC",
    FlagCategory.CULTURAL: "CULTURAL",
    FlagCategory.DERAILMENT: "EXECUTION",
    FlagCategory.DARK_SIDE: "EXECUTION",
}

# CV flag category → domain mapping for cross-stream check.
_CV_CATEGORY_DOMAIN: dict[FlagCategory, str] = {
    FlagCategory.EXPERIENCE_STRENGTH: "EXECUTION",
    FlagCategory.EXPERIENCE_GAP: "EXECUTION",
}

# CV flag names → rubric levels they must reference.
_CV_FLAG_EXPECTED_RUBRIC: dict[str, str] = {
    "CV_GAP": RubricLevel.GAP,
    "CV_GAP_HIGH_PRIORITY": RubricLevel.GAP,
    "CV_GAP_MEDIUM_PRIORITY": RubricLevel.GAP,
    "CV_PARTIAL": RubricLevel.PARTIAL,
    "CV_PARTIAL_HIGH_PRIORITY": RubricLevel.PARTIAL,
    "CV_EXCEEDS": RubricLevel.EXCEEDS,
    "CV_EXCEEDS_HIGH_PRIORITY": RubricLevel.EXCEEDS,
    "CV_SCOPE_EXCEEDS": RubricLevel.EXCEEDS,
    "CV_SCOPE_GAP": RubricLevel.GAP,
}

BIG_FIVE_DIMENSIONS: tuple[str, ...] = ("O", "C", "E", "A", "N")


# ---------------------------------------------------------------------------
# Check 1: Flag-Score Consistency
# ---------------------------------------------------------------------------


def _is_personality_flag_consistent(flag: Flag) -> bool:
    """Return True if the personality flag's score is on the correct side of its threshold."""
    if flag.big_five_score is None or flag.threshold_used is None:
        return False

    direction = flag.metadata.get("direction", "")
    if direction == "above":
        return flag.big_five_score > flag.threshold_used
    if direction == "below":
        return flag.big_five_score < flag.threshold_used
    return False


def _is_cv_flag_consistent(flag: Flag, rubric_index: dict[tuple[str, str], RubricAssessment]) -> bool:
    """Return True if the CV flag's name matches the actual rubric assessment data."""
    if flag.requirement_id is None:
        return False

    expected_rubric = _CV_FLAG_EXPECTED_RUBRIC.get(flag.name)
    if expected_rubric is None:
        # Flag name not in CV mapping — not a consistency issue for this check.
        return True

    assessment = rubric_index.get((flag.requirement_id, flag.candidate_name))
    if assessment is None:
        return False

    return assessment.rubric_level == expected_rubric


def _build_rubric_index(rubric_assessments: list[RubricAssessment]) -> dict[tuple[str, str], RubricAssessment]:
    """Build a lookup index keyed by (requirement_id, candidate_name)."""
    return {(a.requirement_id, a.candidate_name): a for a in rubric_assessments}


def check_flag_score_consistency(
    flags: list[Flag],
    rubric_assessments: list[RubricAssessment],
) -> tuple[list[Flag], list[str]]:
    """Verify personality flags match thresholds and CV flags match rubric data.

    Personality: verify that a personality flag's big_five_score is on the correct
    side of its threshold_used (above for "above" direction, below for "below").

    CV: verify that a CV flag references a requirement with the matching rubric_level.
    E.g., a CV_GAP flag must reference a requirement assessed as 'gap', CV_EXCEEDS
    must reference 'exceeds'. Mismatch indicates a bridge bug.

    Cross-stream: NOT checked (personality and CV are independent).

    Returns:
        (validated_flags, warnings). Inconsistent flags are removed.
    """
    rubric_index = _build_rubric_index(rubric_assessments)
    validated: list[Flag] = []
    warnings: list[str] = []

    for flag in flags:
        if flag.evidence_type == EvidenceType.SCORED_FLAG:
            if _is_personality_flag_consistent(flag):
                validated.append(flag)
            else:
                warnings.append(
                    f"[Check1] Personality flag '{flag.name}' for '{flag.candidate_name}' "
                    f"is inconsistent with threshold (score={flag.big_five_score}, "
                    f"threshold={flag.threshold_used}, direction={flag.metadata.get('direction')}). "
                    "Removed."
                )
        elif flag.evidence_type in {
            EvidenceType.CV_RUBRIC,
            EvidenceType.REQUIREMENT_GAP,
        }:
            if _is_cv_flag_consistent(flag, rubric_index):
                validated.append(flag)
            else:
                warnings.append(
                    f"[Check1] CV flag '{flag.name}' for '{flag.candidate_name}' "
                    f"(requirement={flag.requirement_id}) rubric level mismatch. "
                    "Removed."
                )
        else:
            # CV_PATTERN and ROUTING flags are not subject to this check.
            validated.append(flag)

    return validated, warnings


# ---------------------------------------------------------------------------
# Check 2: Mutual Exclusivity
# ---------------------------------------------------------------------------


def _unconditional_contradiction_set() -> frozenset[frozenset[str]]:
    """Return unconditional contradiction pairs as frozensets for O(1) lookup."""
    return frozenset(frozenset(pair) for pair in _UNCONDITIONAL_CONTRADICTIONS)


def _resolve_personality_contradiction(flag_a: Flag, flag_b: Flag) -> Flag:
    """Return the personality flag to REMOVE from a contradicting pair.

    Strategy: remove the flag with negative valence. If both or neither are
    negative, fall back to removing the second flag in iteration order.
    """
    a_negative = flag_a.valence == Valence.NEGATIVE
    b_negative = flag_b.valence == Valence.NEGATIVE
    if a_negative and not b_negative:
        return flag_a
    if b_negative and not a_negative:
        return flag_b
    # Both same valence — remove flag_b (arbitrary but deterministic).
    return flag_b


def _resolve_cv_contradiction(flag_a: Flag, flag_b: Flag) -> Flag:
    """Return the CV flag to REMOVE from a contradicting pair.

    Strategy: remove lower-confidence flag. Confidence ordering: high > medium > low.
    If equal or missing, remove the negative-valence flag. If still tied, remove flag_b.
    """
    _confidence_rank: dict[str | None, int] = {"high": 2, "medium": 1, "low": 0, None: -1}
    rank_a = _confidence_rank.get(flag_a.confidence, -1)
    rank_b = _confidence_rank.get(flag_b.confidence, -1)
    if rank_a > rank_b:
        return flag_b
    if rank_b > rank_a:
        return flag_a
    # Equal confidence — remove negative-valence flag.
    if flag_a.valence == Valence.NEGATIVE and flag_b.valence != Valence.NEGATIVE:
        return flag_a
    if flag_b.valence == Valence.NEGATIVE and flag_a.valence != Valence.NEGATIVE:
        return flag_b
    return flag_b


def _find_flags_to_remove(flags: list[Flag]) -> set[int]:
    """Identify indices of flags to remove due to mutual exclusivity violations."""
    uc_pairs = _unconditional_contradiction_set()
    remove_indices: set[int] = set()

    for i in range(len(flags)):
        for j in range(i + 1, len(flags)):
            if i in remove_indices or j in remove_indices:
                continue

            flag_a = flags[i]
            flag_b = flags[j]

            # Unconditional contradiction — flag names alone.
            pair = frozenset({flag_a.name, flag_b.name})
            if pair in uc_pairs:
                to_remove = _resolve_personality_contradiction(flag_a, flag_b)
                remove_indices.add(i if to_remove is flag_a else j)
                continue

            # Conditional contradiction — requires same requirement_id.
            for name_pos, name_neg in _CONDITIONAL_CONTRADICTIONS:
                names_match = (flag_a.name == name_pos and flag_b.name == name_neg) or (
                    flag_b.name == name_pos and flag_a.name == name_neg
                )
                if not names_match:
                    continue
                if flag_a.requirement_id is None or flag_a.requirement_id != flag_b.requirement_id:
                    continue
                to_remove = _resolve_cv_contradiction(flag_a, flag_b)
                remove_indices.add(i if to_remove is flag_a else j)
                break

    return remove_indices


def check_mutual_exclusivity(
    flags: list[Flag],
) -> tuple[list[Flag], list[str]]:
    """Remove contradictory flag pairs.

    Unconditional contradictions (personality): flag name pairs that can never coexist.
    Conditional contradictions (CV): CV flag name pairs that only contradict when they
    reference the SAME requirement_id.

    On contradiction: remove lower-confidence flag (CV) or negative-valence flag
    (personality).

    Returns:
        (validated_flags, warnings). Removed flags produce a warning entry.
    """
    remove_indices = _find_flags_to_remove(flags)
    validated: list[Flag] = []
    warnings: list[str] = []

    for idx, flag in enumerate(flags):
        if idx in remove_indices:
            warnings.append(
                f"[Check2] Contradiction: flag '{flag.name}' for '{flag.candidate_name}' "
                "removed (mutual exclusivity). "
                f"requirement_id={flag.requirement_id}"
            )
        else:
            validated.append(flag)

    return validated, warnings


# ---------------------------------------------------------------------------
# Check 3: Dimension Coverage
# ---------------------------------------------------------------------------


def _flags_by_candidate_dimension(flags: list[Flag]) -> dict[str, set[str]]:
    """Return a mapping of candidate_name → set of Big Five dimensions with ≥1 flag."""
    result: dict[str, set[str]] = defaultdict(set)
    for flag in flags:
        if flag.evidence_type == EvidenceType.SCORED_FLAG and flag.big_five_source:
            result[flag.candidate_name].add(flag.big_five_source)
    return result


def _flags_by_candidate_requirement(flags: list[Flag]) -> dict[str, set[str]]:
    """Return a mapping of candidate_name → set of requirement_ids with a flag."""
    result: dict[str, set[str]] = defaultdict(set)
    for flag in flags:
        if flag.requirement_id is not None:
            result[flag.candidate_name].add(flag.requirement_id)
    return result


def check_dimension_coverage(
    flags: list[Flag],
    requirements: list[Requirement],
    rubric_assessments: list[RubricAssessment],
    assessment_mode_per_candidate: dict[str, str],
) -> list[str]:
    """Check coverage completeness. Advisory warnings only, no flag removal.

    Personality (full mode only): all 5 Big Five dimensions should have ≥1 flag.
    Requirements: every CV-assessable requirement should have either a flag OR
    rubric_level=meets (no flag by design). Missing both → warning.

    Returns:
        warnings — list of advisory warning strings.
    """
    warnings: list[str] = []

    dimension_coverage = _flags_by_candidate_dimension(flags)
    candidate_req_flags = _flags_by_candidate_requirement(flags)

    # Build rubric index for meets lookup.
    rubric_index = _build_rubric_index(rubric_assessments)

    # Personality dimension coverage — full mode only.
    all_candidates = set(assessment_mode_per_candidate.keys())
    for candidate in all_candidates:
        if assessment_mode_per_candidate.get(candidate) != "full":
            continue
        covered = dimension_coverage.get(candidate, set())
        for dimension in BIG_FIVE_DIMENSIONS:
            if dimension not in covered:
                warnings.append(
                    f"[Check3] Candidate '{candidate}': dimension '{dimension}' has no "
                    "scored flags — assessment on this dimension is limited."
                )

    # Requirement coverage — every CV-assessable requirement.
    cv_assessable = [r for r in requirements if r.assessable_from_cv]
    for candidate in all_candidates:
        covered_reqs = candidate_req_flags.get(candidate, set())
        for req in cv_assessable:
            if req.requirement_id in covered_reqs:
                continue
            # Check if the rubric assessment is 'meets' (no flag by design).
            assessment = rubric_index.get((req.requirement_id, candidate))
            if assessment is not None and assessment.rubric_level == RubricLevel.MEETS:
                continue
            warnings.append(
                f"[Check3] Candidate '{candidate}': requirement '{req.requirement_id}' "
                "has no flag and no 'meets' rubric assessment — may have been lost in bridge."
            )

    return warnings


# ---------------------------------------------------------------------------
# Check 4: Cross-Stream Coherence (advisory)
# ---------------------------------------------------------------------------


def _positive_cv_domains(flags: list[Flag]) -> set[str]:
    """Return domains where the candidate has a positive CV flag."""
    domains: set[str] = set()
    for flag in flags:
        if flag.category in _CV_CATEGORY_DOMAIN and flag.valence == Valence.POSITIVE:
            domains.add(_CV_CATEGORY_DOMAIN[flag.category])
    return domains


def _negative_personality_flags_by_domain(flags: list[Flag]) -> dict[str, list[Flag]]:
    """Return negative-valence personality flags grouped by their domain."""
    result: dict[str, list[Flag]] = defaultdict(list)
    for flag in flags:
        if flag.evidence_type != EvidenceType.SCORED_FLAG:
            continue
        if flag.valence != Valence.NEGATIVE:
            continue
        domain = _PERSONALITY_CATEGORY_DOMAIN.get(flag.category)
        if domain is not None:
            result[domain].append(flag)
    return result


def check_cross_stream_coherence(
    flags: list[Flag],
) -> list[str]:
    """Detect interesting tensions between personality and CV streams. Advisory only.

    Positive CV flag + negative personality flag on same domain → advisory note.

    Returns:
        coherence_notes — advisory cross-stream tension observations.
    """
    notes: list[str] = []

    # Group flags per candidate.
    per_candidate: dict[str, list[Flag]] = defaultdict(list)
    for flag in flags:
        per_candidate[flag.candidate_name].append(flag)

    for candidate, candidate_flags in per_candidate.items():
        positive_cv = _positive_cv_domains(candidate_flags)
        negative_personality = _negative_personality_flags_by_domain(candidate_flags)

        for domain in positive_cv & set(negative_personality.keys()):
            neg_flag_names = [f.name for f in negative_personality[domain]]
            notes.append(
                f"[Check4] Cross-stream tension for '{candidate}': strong CV evidence in "
                f"domain '{domain}' alongside personality risk flag(s) {neg_flag_names}. "
                "Both signals valid — committee should weight appropriately."
            )

    return notes


# ---------------------------------------------------------------------------
# Check 5: Flag Count Reasonableness (advisory)
# ---------------------------------------------------------------------------

_FLAG_COUNT_HIGH_WATERMARK: int = 25
_FLAG_COUNT_LOW_WATERMARK: int = 3


def check_flag_count(
    flags: list[Flag],
) -> list[str]:
    """Advisory warnings about flag count per candidate.

    >25 per candidate → warn "noisy"
    <3 per candidate → warn "thin"
    Expected: 8-18

    Returns:
        warnings — advisory warning strings.
    """
    per_candidate: dict[str, int] = defaultdict(int)
    for flag in flags:
        per_candidate[flag.candidate_name] += 1

    warnings: list[str] = []
    for candidate, count in per_candidate.items():
        if count > _FLAG_COUNT_HIGH_WATERMARK:
            warnings.append(
                f"[Check5] Candidate '{candidate}' has {count} flags (>{_FLAG_COUNT_HIGH_WATERMARK}): "
                "evaluation may be noisy — agents will have too many signals to process meaningfully."
            )
        elif count < _FLAG_COUNT_LOW_WATERMARK:
            warnings.append(
                f"[Check5] Candidate '{candidate}' has {count} flag(s) (<{_FLAG_COUNT_LOW_WATERMARK}): "
                "assessment data is thin — evaluation quality will be limited."
            )

    return warnings


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def validate_merged_flags(
    flags_per_candidate: dict[str, list[Flag]],
    rubric_assessments: list[RubricAssessment],
    requirements: list[Requirement],
    assessment_mode_per_candidate: dict[str, str],
) -> tuple[dict[str, list[Flag]], list[str], list[str]]:
    """Run all 5 validation checks on the merged flag set.

    Checks 1-2 may remove flags (consistency, mutual exclusivity).
    Check 3 is advisory on coverage (warnings only).
    Checks 4-5 are advisory (coherence notes and count warnings).

    Args:
        flags_per_candidate: Candidate name → merged flags (from D3).
        rubric_assessments: All rubric assessments from Stage C3.
        requirements: Confirmed requirement list from Stage C2.
        assessment_mode_per_candidate: Candidate name → "full" or "partial".

    Returns:
        (validated_flags_per_candidate, warnings, coherence_notes)

        warnings: issues that caused flag removal or indicate gaps.
        coherence_notes: advisory cross-stream tension observations.
    """
    all_warnings: list[str] = []
    all_coherence_notes: list[str] = []
    validated_per_candidate: dict[str, list[Flag]] = {}

    # Run per-candidate checks 1-2, collect all flags for checks 3-5.
    for candidate, flags in flags_per_candidate.items():
        checked, w1 = check_flag_score_consistency(flags, rubric_assessments)
        checked, w2 = check_mutual_exclusivity(checked)

        all_warnings.extend(w1)
        all_warnings.extend(w2)
        validated_per_candidate[candidate] = checked

    # Flatten all validated flags for checks 3-5.
    all_flags: list[Flag] = [f for fs in validated_per_candidate.values() for f in fs]

    # Check 3: dimension coverage (advisory warnings).
    w3 = check_dimension_coverage(
        all_flags,
        requirements,
        rubric_assessments,
        assessment_mode_per_candidate,
    )
    all_warnings.extend(w3)

    # Check 4: cross-stream coherence (advisory notes).
    all_coherence_notes.extend(check_cross_stream_coherence(all_flags))

    # Check 5: flag count (advisory warnings).
    for _candidate, flags in validated_per_candidate.items():
        count_warnings = check_flag_count(flags)
        all_warnings.extend(count_warnings)

    return validated_per_candidate, all_warnings, all_coherence_notes
