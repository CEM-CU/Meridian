"""Personality flag derivation (D1).

Derives personality flags from Big Five scores using scenario-specific thresholds.
Zero LLM calls — entirely deterministic threshold-based logic.
"""

from __future__ import annotations

from shared.models import (
    BigFiveScores,
    CandidateData,
    EvidenceType,
    Flag,
    FlagCategory,
    ScenarioConfig,
    TeamMember,
    Valence,
)

from stage_d.config.thresholds import (
    BIG_FIVE_DIMENSIONS,
    SCENARIO_TRAIT_THRESHOLDS,
    TEAM_THRESHOLDS,
    TeamThreshold,
    TraitThreshold,
)


def derive_personality_flags(
    candidate: CandidateData,
    scenario: ScenarioConfig,
    team_members: list[TeamMember] | None = None,
) -> list[Flag]:
    """Derive personality flags from Big Five scores for a single candidate.

    Returns an empty list if the candidate has no Big Five scores (partial mode).
    Team context flags are only generated when team_members is provided and non-empty.
    """
    if candidate.big_five is None:
        return []

    trait_flags = _derive_trait_flags(candidate, scenario)
    team_flags = _derive_team_flags(candidate, scenario, team_members or [])

    return [*trait_flags, *team_flags]


def _derive_trait_flags(
    candidate: CandidateData,
    scenario: ScenarioConfig,
) -> list[Flag]:
    """Derive individual trait flags from Big Five scores against scenario thresholds."""
    assert candidate.big_five is not None

    dimension_thresholds = SCENARIO_TRAIT_THRESHOLDS.get(scenario.name, {})
    flags: list[Flag] = []

    for dimension in BIG_FIVE_DIMENSIONS:
        thresholds = dimension_thresholds.get(dimension, ())
        score = _get_dimension_score(candidate, dimension)
        for threshold_def in thresholds:
            flag = _evaluate_trait_threshold(candidate, scenario, dimension, score, threshold_def)
            if flag is not None:
                flags.append(flag)

    return flags


def _derive_team_flags(
    candidate: CandidateData,
    scenario: ScenarioConfig,
    team_members: list[TeamMember],
) -> list[Flag]:
    """Derive team context flags from candidate vs. team Big Five profiles."""
    if not team_members:
        return []

    assert candidate.big_five is not None

    flags: list[Flag] = []
    for team_threshold in TEAM_THRESHOLDS:
        flag = _evaluate_team_threshold(candidate, scenario, team_members, team_threshold)
        if flag is not None:
            flags.append(flag)

    return flags


def _evaluate_trait_threshold(
    candidate: CandidateData,
    scenario: ScenarioConfig,
    dimension: str,
    score: float,
    threshold_def: TraitThreshold,
) -> Flag | None:
    """Evaluate a single trait threshold and return a Flag if the threshold is met."""
    if not _check_direction(score, threshold_def.threshold, threshold_def.direction):
        return None

    return _build_flag(
        name=threshold_def.flag_name,
        candidate_name=candidate.name,
        category=threshold_def.category,
        valence=threshold_def.valence,
        dimension=dimension,
        score=score,
        threshold=threshold_def.threshold,
        direction=threshold_def.direction,
        scenario_name=str(scenario.name),
        topic_keywords=list(threshold_def.topic_keywords),
    )


def _evaluate_team_threshold(
    candidate: CandidateData,
    scenario: ScenarioConfig,
    team_members: list[TeamMember],
    team_def: TeamThreshold,
) -> Flag | None:
    """Evaluate a single team threshold and return a Flag if the condition is met."""
    assert candidate.big_five is not None

    candidate_score = _get_dimension_score(candidate, team_def.dimension)

    # Check candidate-side threshold (if non-zero; 0.0 means "any value")
    if team_def.candidate_threshold > 0.0 and not _check_direction(
        candidate_score, team_def.candidate_threshold, team_def.candidate_direction
    ):
        return None

    team_scores = _get_team_dimension_scores(team_members, team_def.dimension)
    if not team_scores:
        return None

    if not _check_team_condition(candidate_score, team_scores, team_def):
        return None

    return _build_flag(
        name=team_def.flag_name,
        candidate_name=candidate.name,
        category=team_def.category,
        valence=team_def.valence,
        dimension=team_def.dimension,
        score=candidate_score,
        threshold=team_def.team_threshold,
        direction=team_def.candidate_direction,
        scenario_name=str(scenario.name),
        topic_keywords=list(team_def.topic_keywords),
    )


def _check_direction(score: float, threshold: float, direction: str) -> bool:
    """Check whether a score passes a threshold in the given direction.

    Boundary behavior: score exactly at threshold does NOT fire the flag.
    'above' requires strictly greater than; 'below' requires strictly less than.
    """
    if direction == "above":
        return score > threshold
    return score < threshold


def _check_team_condition(
    candidate_score: float,
    team_scores: list[float],
    team_def: TeamThreshold,
) -> bool:
    """Evaluate a team condition against team member scores."""
    if team_def.team_condition == "member_above":
        return any(ts > team_def.team_threshold for ts in team_scores)

    team_mean = sum(team_scores) / len(team_scores)

    if team_def.team_condition == "mean_diff_above":
        return abs(candidate_score - team_mean) > team_def.team_threshold

    if team_def.team_condition == "mean_above":
        return team_mean > team_def.team_threshold

    return False


def _score_for_dimension(scores: BigFiveScores, dimension: str) -> float:
    """Extract a single dimension score from a BigFiveScores object."""
    mapping: dict[str, float] = {"O": scores.O, "C": scores.C, "E": scores.E, "A": scores.A, "N": scores.N}
    return mapping[dimension]


def _get_dimension_score(candidate: CandidateData, dimension: str) -> float:
    """Extract a single Big Five dimension score from a candidate."""
    assert candidate.big_five is not None
    return _score_for_dimension(candidate.big_five, dimension)


def _get_team_dimension_scores(team_members: list[TeamMember], dimension: str) -> list[float]:
    """Extract a single dimension score from each team member."""
    return [_score_for_dimension(member.big_five, dimension) for member in team_members]


def _build_flag(
    *,
    name: str,
    candidate_name: str,
    category: FlagCategory,
    valence: Valence,
    dimension: str,
    score: float,
    threshold: float,
    direction: str,
    scenario_name: str,
    topic_keywords: list[str],
) -> Flag:
    """Construct a Flag with all required personality flag fields."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory(category),
        valence=Valence(valence),
        evidence_type=EvidenceType.SCORED_FLAG,
        big_five_source=dimension,
        big_five_score=score,
        threshold_used=threshold,
        topic_keywords=topic_keywords,
        metadata={"scenario": scenario_name, "direction": direction},
    )
