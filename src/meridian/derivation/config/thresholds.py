"""Personality flag threshold configuration.

Defines per-scenario, per-dimension thresholds for Big Five flag derivation.
All data structures are immutable (tuples and frozen dataclasses).

Architecture: Shared defaults are defined once for thresholds that are identical
across all scenarios. Per-scenario configs only specify overrides (threshold values
and topic keywords that differ). Adding a new scenario requires only a new entry
in _SCENARIO_OVERRIDES.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from meridian.models import FlagCategory, ScenarioName, Valence


@dataclass(frozen=True, slots=True)
class TraitThreshold:
    """Single threshold definition for a personality trait flag."""

    flag_name: str
    category: FlagCategory
    valence: Valence
    threshold: float
    direction: str  # "above" or "below"
    topic_keywords: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TeamThreshold:
    """Threshold definition for a team-context flag."""

    flag_name: str
    category: FlagCategory
    valence: Valence
    dimension: str  # O, C, E, A, or N
    candidate_threshold: float
    candidate_direction: str  # "above" or "below"
    team_condition: str  # "member_above", "mean_diff_above", "mean_above"
    team_threshold: float
    topic_keywords: tuple[str, ...]


# ---------------------------------------------------------------------------
# Shared defaults: thresholds identical across ALL scenarios
# ---------------------------------------------------------------------------

_NEUROTICISM_DEFAULT: Final[TraitThreshold] = TraitThreshold(
    "DERAILMENT_NEUROTICISM_UNDER_STRESS",
    FlagCategory.DERAILMENT,
    Valence.NEGATIVE,
    0.65,
    "above",
    ("derailment", "neuroticism", "stress", "volatility"),
)

_LOW_AGREEABLENESS_DEFAULT: Final[TraitThreshold] = TraitThreshold(
    "DARK_SIDE_LOW_AGREEABLENESS",
    FlagCategory.DARK_SIDE,
    Valence.NEGATIVE,
    0.25,
    "below",
    ("dark_side", "agreeableness", "conflict", "abrasiveness"),
)

_LOW_CONSCIENTIOUSNESS_DEFAULT: Final[TraitThreshold] = TraitThreshold(
    "EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
    FlagCategory.EXECUTION,
    Valence.NEGATIVE,
    0.35,
    "below",
    ("execution", "conscientiousness", "risk", "disorganization"),
)

_INTROVERSION_NOTE_DEFAULT: Final[TraitThreshold] = TraitThreshold(
    "CULTURAL_INTROVERSION_NOTE",
    FlagCategory.CULTURAL,
    Valence.NEUTRAL,
    0.30,
    "below",
    ("cultural", "introversion", "advisory", "communication"),
)


# ---------------------------------------------------------------------------
# Per-scenario factory helpers for thresholds that vary
# ---------------------------------------------------------------------------


def _conscientiousness_fit(threshold: float, keyword: str) -> TraitThreshold:
    """Create EXECUTION_CONSCIENTIOUSNESS_FIT with scenario-specific threshold and keyword."""
    return TraitThreshold(
        "EXECUTION_CONSCIENTIOUSNESS_FIT",
        FlagCategory.EXECUTION,
        Valence.POSITIVE,
        threshold,
        "above",
        ("execution", "conscientiousness", "discipline", keyword),
    )


def _openness_fit(threshold: float, keywords: tuple[str, ...]) -> TraitThreshold:
    """Create STRATEGIC_OPENNESS_FIT with scenario-specific threshold and keywords."""
    return TraitThreshold(
        "STRATEGIC_OPENNESS_FIT",
        FlagCategory.STRATEGIC,
        Valence.POSITIVE,
        threshold,
        "above",
        ("strategic", "openness", *keywords),
    )


def _low_openness_risk() -> TraitThreshold:
    """Create STRATEGIC_LOW_OPENNESS_RISK (only used by some scenarios)."""
    return TraitThreshold(
        "STRATEGIC_LOW_OPENNESS_RISK",
        FlagCategory.STRATEGIC,
        Valence.NEGATIVE,
        0.30,
        "below",
        ("strategic", "openness", "rigidity", "resistance"),
    )


def _extraversion_fit(threshold: float, keyword: str) -> TraitThreshold:
    """Create CULTURAL_EXTRAVERSION_FIT with scenario-specific threshold and keyword."""
    return TraitThreshold(
        "CULTURAL_EXTRAVERSION_FIT",
        FlagCategory.CULTURAL,
        Valence.POSITIVE,
        threshold,
        "above",
        ("cultural", "extraversion", "leadership", keyword),
    )


# ---------------------------------------------------------------------------
# Per-scenario trait assembly
# ---------------------------------------------------------------------------


def _build_scenario_traits(
    *,
    c_fit_threshold: float,
    c_fit_keyword: str,
    o_fit_threshold: float,
    o_fit_keywords: tuple[str, ...],
    e_fit_threshold: float,
    e_fit_keyword: str,
    include_low_openness_risk: bool = False,
) -> dict[str, tuple[TraitThreshold, ...]]:
    """Assemble a complete scenario trait config from per-scenario parameters.

    Shared defaults (neuroticism, low agreeableness, low conscientiousness,
    introversion note) are included automatically.
    """
    o_thresholds: tuple[TraitThreshold, ...] = (_openness_fit(o_fit_threshold, o_fit_keywords),)
    if include_low_openness_risk:
        o_thresholds = (*o_thresholds, _low_openness_risk())

    return {
        "C": (_conscientiousness_fit(c_fit_threshold, c_fit_keyword), _LOW_CONSCIENTIOUSNESS_DEFAULT),
        "O": o_thresholds,
        "N": (_NEUROTICISM_DEFAULT,),
        "A": (_LOW_AGREEABLENESS_DEFAULT,),
        "E": (_extraversion_fit(e_fit_threshold, e_fit_keyword), _INTROVERSION_NOTE_DEFAULT),
    }


# ---------------------------------------------------------------------------
# Scenario-specific trait configurations
# ---------------------------------------------------------------------------

_DIGITAL_TRANSFORM_TRAITS: Final[dict[str, tuple[TraitThreshold, ...]]] = _build_scenario_traits(
    c_fit_threshold=0.65,
    c_fit_keyword="reliability",
    o_fit_threshold=0.70,
    o_fit_keywords=("innovation", "digital"),
    e_fit_threshold=0.60,
    e_fit_keyword="communication",
    include_low_openness_risk=True,
)

_TURNAROUND_TRAITS: Final[dict[str, tuple[TraitThreshold, ...]]] = _build_scenario_traits(
    c_fit_threshold=0.70,
    c_fit_keyword="reliability",
    o_fit_threshold=0.60,
    o_fit_keywords=("innovation", "restructuring"),
    e_fit_threshold=0.70,
    e_fit_keyword="decisiveness",
)

_STABILIZATION_TRAITS: Final[dict[str, tuple[TraitThreshold, ...]]] = _build_scenario_traits(
    c_fit_threshold=0.70,
    c_fit_keyword="reliability",
    o_fit_threshold=0.55,
    o_fit_keywords=("process", "improvement"),
    e_fit_threshold=0.55,
    e_fit_keyword="steadiness",
)

_GROWTH_TRAITS: Final[dict[str, tuple[TraitThreshold, ...]]] = _build_scenario_traits(
    c_fit_threshold=0.60,
    c_fit_keyword="scaling",
    o_fit_threshold=0.55,
    o_fit_keywords=("growth", "opportunity"),
    e_fit_threshold=0.65,
    e_fit_keyword="growth",
    include_low_openness_risk=True,
)

_POST_ACQUISITION_TRAITS: Final[dict[str, tuple[TraitThreshold, ...]]] = _build_scenario_traits(
    c_fit_threshold=0.65,
    c_fit_keyword="integration",
    o_fit_threshold=0.50,
    o_fit_keywords=("integration", "adaptability"),
    e_fit_threshold=0.60,
    e_fit_keyword="integration",
)

SCENARIO_TRAIT_THRESHOLDS: Final[dict[ScenarioName, dict[str, tuple[TraitThreshold, ...]]]] = {
    ScenarioName.DIGITAL_TRANSFORMATION: _DIGITAL_TRANSFORM_TRAITS,
    ScenarioName.TURNAROUND: _TURNAROUND_TRAITS,
    ScenarioName.STABILIZATION: _STABILIZATION_TRAITS,
    ScenarioName.GROWTH: _GROWTH_TRAITS,
    ScenarioName.POST_ACQUISITION: _POST_ACQUISITION_TRAITS,
}

# --- Team context thresholds (scenario-independent) ---

TEAM_THRESHOLDS: Final[tuple[TeamThreshold, ...]] = (
    TeamThreshold(
        "COLLISION_DUAL_DOMINANCE",
        FlagCategory.COLLISION,
        Valence.NEGATIVE,
        "E",
        0.75,
        "above",
        "member_above",
        0.75,
        ("collision", "dominance", "extraversion", "power_struggle"),
    ),
    TeamThreshold(
        "COMPLEMENT_EXTRAVERSION_BALANCE",
        FlagCategory.COMPLEMENT,
        Valence.POSITIVE,
        "E",
        0.0,
        "above",
        "mean_diff_above",
        0.30,
        ("complement", "extraversion", "balance", "diversity"),
    ),
    TeamThreshold(
        "FRICTION_CONSCIENTIOUSNESS_GAP",
        FlagCategory.FRICTION,
        Valence.NEGATIVE,
        "C",
        0.0,
        "above",
        "mean_diff_above",
        0.35,
        ("friction", "conscientiousness", "gap", "misalignment"),
    ),
    TeamThreshold(
        "COMPLEMENT_OPENNESS_DIVERSITY",
        FlagCategory.COMPLEMENT,
        Valence.POSITIVE,
        "O",
        0.0,
        "above",
        "mean_diff_above",
        0.25,
        ("complement", "openness", "diversity", "perspective"),
    ),
    TeamThreshold(
        "GROUPTHINK_AGREEABLENESS_CLUSTER",
        FlagCategory.GROUPTHINK,
        Valence.NEGATIVE,
        "A",
        0.70,
        "above",
        "mean_above",
        0.70,
        ("groupthink", "agreeableness", "conformity", "challenge_deficit"),
    ),
)

BIG_FIVE_DIMENSIONS: Final[tuple[str, ...]] = ("O", "C", "E", "A", "N")
