"""Tests for D1: Personality flag derivation.

Covers individual trait flags, team context flags, boundary values,
scenario variation, partial mode, and structural invariants.
"""

from __future__ import annotations

import pytest
from shared.models import (
    BigFiveScores,
    CandidateData,
    EvidenceType,
    Flag,
    FlagCategory,
    ScenarioConfig,
    ScenarioName,
    TeamMember,
    Valence,
)
from stage_d.personality_flags import derive_personality_flags

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _candidate(
    *,
    name: str = "Alice",
    o: float = 0.50,
    c: float = 0.50,
    e: float = 0.50,
    a: float = 0.50,
    n: float = 0.50,
    big_five: BigFiveScores | None = ...,  # type: ignore[assignment]
) -> CandidateData:
    """Build a CandidateData with given Big Five scores (or None)."""
    if big_five is ...:
        big_five = BigFiveScores(O=o, C=c, E=e, A=a, N=n)
    return CandidateData(name=name, cv_text="dummy cv", big_five=big_five)


def _scenario(name: ScenarioName = ScenarioName.DIGITAL_TRANSFORMATION) -> ScenarioConfig:
    return ScenarioConfig(name=name)


def _team_member(
    *,
    name: str = "Bob",
    role: str = "CFO",
    o: float = 0.50,
    c: float = 0.50,
    e: float = 0.50,
    a: float = 0.50,
    n: float = 0.50,
) -> TeamMember:
    return TeamMember(name=name, role=role, big_five=BigFiveScores(O=o, C=c, E=e, A=a, N=n))


def _flag_names(flags: list[Flag]) -> set[str]:
    return {f.name for f in flags}


# ---------------------------------------------------------------------------
# No Big Five → empty list (partial mode)
# ---------------------------------------------------------------------------


class TestPartialMode:
    """When Big Five scores are absent, no personality flags are generated."""

    def test_no_big_five_returns_empty(self) -> None:
        candidate = _candidate(big_five=None)
        result = derive_personality_flags(candidate, _scenario())
        assert result == []

    def test_no_big_five_with_team_returns_empty(self) -> None:
        candidate = _candidate(big_five=None)
        team = [_team_member()]
        result = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert result == []


# ---------------------------------------------------------------------------
# Structural invariants on all returned flags
# ---------------------------------------------------------------------------


class TestFlagStructure:
    """Every returned flag must have the correct evidence type, valid source, etc."""

    def test_all_flags_have_scored_flag_evidence_type(self) -> None:
        candidate = _candidate(o=0.80, c=0.80, e=0.80, a=0.10, n=0.80)
        flags = derive_personality_flags(candidate, _scenario())
        for flag in flags:
            assert flag.evidence_type == EvidenceType.SCORED_FLAG

    def test_all_flags_have_valid_big_five_source(self) -> None:
        candidate = _candidate(o=0.80, c=0.80, e=0.80, a=0.10, n=0.80)
        flags = derive_personality_flags(candidate, _scenario())
        valid_sources = {"O", "C", "E", "A", "N"}
        for flag in flags:
            assert flag.big_five_source in valid_sources

    def test_all_flags_have_candidate_name(self) -> None:
        candidate = _candidate(name="TestPerson", o=0.80, c=0.80)
        flags = derive_personality_flags(candidate, _scenario())
        for flag in flags:
            assert flag.candidate_name == "TestPerson"

    def test_all_flags_have_metadata_with_scenario(self) -> None:
        candidate = _candidate(o=0.80, c=0.80)
        flags = derive_personality_flags(candidate, _scenario(ScenarioName.GROWTH))
        for flag in flags:
            assert flag.metadata["scenario"] == "growth"
            assert flag.metadata["direction"] in ("above", "below")

    def test_all_flags_have_topic_keywords(self) -> None:
        candidate = _candidate(o=0.80, c=0.80, e=0.80, a=0.10, n=0.80)
        flags = derive_personality_flags(candidate, _scenario())
        for flag in flags:
            assert len(flag.topic_keywords) > 0

    def test_all_flags_have_threshold_and_score(self) -> None:
        candidate = _candidate(o=0.80, c=0.80)
        flags = derive_personality_flags(candidate, _scenario())
        for flag in flags:
            assert flag.big_five_score is not None
            assert flag.threshold_used is not None


# ---------------------------------------------------------------------------
# Individual trait flags — digital transformation scenario
# ---------------------------------------------------------------------------


class TestDigitalTransformTraitFlags:
    """Test individual trait thresholds under digital_transformation."""

    def test_conscientiousness_fit_fires_above_threshold(self) -> None:
        candidate = _candidate(c=0.70)
        flags = derive_personality_flags(candidate, _scenario())
        assert "EXECUTION_CONSCIENTIOUSNESS_FIT" in _flag_names(flags)

    def test_conscientiousness_fit_does_not_fire_at_threshold(self) -> None:
        candidate = _candidate(c=0.65)
        flags = derive_personality_flags(candidate, _scenario())
        assert "EXECUTION_CONSCIENTIOUSNESS_FIT" not in _flag_names(flags)

    def test_conscientiousness_fit_does_not_fire_below_threshold(self) -> None:
        candidate = _candidate(c=0.60)
        flags = derive_personality_flags(candidate, _scenario())
        assert "EXECUTION_CONSCIENTIOUSNESS_FIT" not in _flag_names(flags)

    def test_low_conscientiousness_risk_fires_below_threshold(self) -> None:
        candidate = _candidate(c=0.30)
        flags = derive_personality_flags(candidate, _scenario())
        assert "EXECUTION_LOW_CONSCIENTIOUSNESS_RISK" in _flag_names(flags)

    def test_low_conscientiousness_risk_does_not_fire_at_threshold(self) -> None:
        candidate = _candidate(c=0.35)
        flags = derive_personality_flags(candidate, _scenario())
        assert "EXECUTION_LOW_CONSCIENTIOUSNESS_RISK" not in _flag_names(flags)

    def test_openness_fit_fires_above_threshold(self) -> None:
        candidate = _candidate(o=0.75)
        flags = derive_personality_flags(candidate, _scenario())
        assert "STRATEGIC_OPENNESS_FIT" in _flag_names(flags)

    def test_openness_fit_does_not_fire_at_threshold(self) -> None:
        candidate = _candidate(o=0.70)
        flags = derive_personality_flags(candidate, _scenario())
        assert "STRATEGIC_OPENNESS_FIT" not in _flag_names(flags)

    def test_low_openness_risk_fires_below_threshold(self) -> None:
        candidate = _candidate(o=0.25)
        flags = derive_personality_flags(candidate, _scenario())
        assert "STRATEGIC_LOW_OPENNESS_RISK" in _flag_names(flags)

    def test_low_openness_risk_does_not_fire_at_threshold(self) -> None:
        candidate = _candidate(o=0.30)
        flags = derive_personality_flags(candidate, _scenario())
        assert "STRATEGIC_LOW_OPENNESS_RISK" not in _flag_names(flags)

    def test_neuroticism_fires_above_threshold(self) -> None:
        candidate = _candidate(n=0.70)
        flags = derive_personality_flags(candidate, _scenario())
        assert "DERAILMENT_NEUROTICISM_UNDER_STRESS" in _flag_names(flags)

    def test_neuroticism_does_not_fire_at_threshold(self) -> None:
        candidate = _candidate(n=0.65)
        flags = derive_personality_flags(candidate, _scenario())
        assert "DERAILMENT_NEUROTICISM_UNDER_STRESS" not in _flag_names(flags)

    def test_low_agreeableness_fires_below_threshold(self) -> None:
        candidate = _candidate(a=0.20)
        flags = derive_personality_flags(candidate, _scenario())
        assert "DARK_SIDE_LOW_AGREEABLENESS" in _flag_names(flags)

    def test_low_agreeableness_does_not_fire_at_threshold(self) -> None:
        candidate = _candidate(a=0.25)
        flags = derive_personality_flags(candidate, _scenario())
        assert "DARK_SIDE_LOW_AGREEABLENESS" not in _flag_names(flags)

    def test_extraversion_fit_fires_above_threshold(self) -> None:
        candidate = _candidate(e=0.65)
        flags = derive_personality_flags(candidate, _scenario())
        assert "CULTURAL_EXTRAVERSION_FIT" in _flag_names(flags)

    def test_extraversion_fit_does_not_fire_at_threshold(self) -> None:
        candidate = _candidate(e=0.60)
        flags = derive_personality_flags(candidate, _scenario())
        assert "CULTURAL_EXTRAVERSION_FIT" not in _flag_names(flags)

    def test_introversion_note_fires_below_threshold(self) -> None:
        candidate = _candidate(e=0.25)
        flags = derive_personality_flags(candidate, _scenario())
        names = _flag_names(flags)
        assert "CULTURAL_INTROVERSION_NOTE" in names
        intro_flag = next(f for f in flags if f.name == "CULTURAL_INTROVERSION_NOTE")
        assert intro_flag.valence == Valence.NEUTRAL

    def test_introversion_note_does_not_fire_at_threshold(self) -> None:
        candidate = _candidate(e=0.30)
        flags = derive_personality_flags(candidate, _scenario())
        assert "CULTURAL_INTROVERSION_NOTE" not in _flag_names(flags)


# ---------------------------------------------------------------------------
# Scenario variation — same scores, different thresholds
# ---------------------------------------------------------------------------


class TestScenarioVariation:
    """Different scenarios apply different thresholds to the same scores."""

    def test_conscientiousness_fit_threshold_varies(self) -> None:
        """C=0.66 fires under digital_transform (0.65) but not under turnaround (0.70)."""
        candidate = _candidate(c=0.66)
        dt_flags = derive_personality_flags(candidate, _scenario(ScenarioName.DIGITAL_TRANSFORMATION))
        ta_flags = derive_personality_flags(candidate, _scenario(ScenarioName.TURNAROUND))
        assert "EXECUTION_CONSCIENTIOUSNESS_FIT" in _flag_names(dt_flags)
        assert "EXECUTION_CONSCIENTIOUSNESS_FIT" not in _flag_names(ta_flags)

    def test_openness_fit_threshold_varies(self) -> None:
        """O=0.56 fires under growth (0.55) but not under digital_transform (0.70)."""
        candidate = _candidate(o=0.56)
        growth_flags = derive_personality_flags(candidate, _scenario(ScenarioName.GROWTH))
        dt_flags = derive_personality_flags(candidate, _scenario(ScenarioName.DIGITAL_TRANSFORMATION))
        assert "STRATEGIC_OPENNESS_FIT" in _flag_names(growth_flags)
        assert "STRATEGIC_OPENNESS_FIT" not in _flag_names(dt_flags)

    def test_low_openness_risk_not_present_in_stabilization(self) -> None:
        """Stabilization has no STRATEGIC_LOW_OPENNESS_RISK threshold."""
        candidate = _candidate(o=0.10)
        flags = derive_personality_flags(candidate, _scenario(ScenarioName.STABILIZATION))
        assert "STRATEGIC_LOW_OPENNESS_RISK" not in _flag_names(flags)

    def test_extraversion_fit_threshold_varies(self) -> None:
        """E=0.56 fires under stabilization (0.55) but not under turnaround (0.70)."""
        candidate = _candidate(e=0.56)
        stab_flags = derive_personality_flags(candidate, _scenario(ScenarioName.STABILIZATION))
        ta_flags = derive_personality_flags(candidate, _scenario(ScenarioName.TURNAROUND))
        assert "CULTURAL_EXTRAVERSION_FIT" in _flag_names(stab_flags)
        assert "CULTURAL_EXTRAVERSION_FIT" not in _flag_names(ta_flags)

    def test_all_scenarios_covered(self) -> None:
        """Every ScenarioName has a threshold config entry."""
        from stage_d.config.thresholds import SCENARIO_TRAIT_THRESHOLDS

        for scenario_name in ScenarioName:
            assert scenario_name in SCENARIO_TRAIT_THRESHOLDS, f"Missing config for {scenario_name}"


# ---------------------------------------------------------------------------
# Category and valence correctness
# ---------------------------------------------------------------------------


class TestCategoryValence:
    """Verify correct category and valence on specific flags."""

    def test_execution_conscientiousness_fit_is_positive_execution(self) -> None:
        candidate = _candidate(c=0.80)
        flags = derive_personality_flags(candidate, _scenario())
        flag = next(f for f in flags if f.name == "EXECUTION_CONSCIENTIOUSNESS_FIT")
        assert flag.category == FlagCategory.EXECUTION
        assert flag.valence == Valence.POSITIVE

    def test_low_conscientiousness_risk_is_negative_execution(self) -> None:
        candidate = _candidate(c=0.20)
        flags = derive_personality_flags(candidate, _scenario())
        flag = next(f for f in flags if f.name == "EXECUTION_LOW_CONSCIENTIOUSNESS_RISK")
        assert flag.category == FlagCategory.EXECUTION
        assert flag.valence == Valence.NEGATIVE

    def test_neuroticism_is_negative_derailment(self) -> None:
        candidate = _candidate(n=0.80)
        flags = derive_personality_flags(candidate, _scenario())
        flag = next(f for f in flags if f.name == "DERAILMENT_NEUROTICISM_UNDER_STRESS")
        assert flag.category == FlagCategory.DERAILMENT
        assert flag.valence == Valence.NEGATIVE

    def test_dark_side_low_agreeableness_is_negative_dark_side(self) -> None:
        candidate = _candidate(a=0.10)
        flags = derive_personality_flags(candidate, _scenario())
        flag = next(f for f in flags if f.name == "DARK_SIDE_LOW_AGREEABLENESS")
        assert flag.category == FlagCategory.DARK_SIDE
        assert flag.valence == Valence.NEGATIVE

    def test_introversion_note_is_neutral_cultural(self) -> None:
        candidate = _candidate(e=0.20)
        flags = derive_personality_flags(candidate, _scenario())
        flag = next(f for f in flags if f.name == "CULTURAL_INTROVERSION_NOTE")
        assert flag.category == FlagCategory.CULTURAL
        assert flag.valence == Valence.NEUTRAL


# ---------------------------------------------------------------------------
# No team context → no team flags
# ---------------------------------------------------------------------------


class TestNoTeamContext:
    """Without team members, no collision/complement/friction/groupthink flags."""

    def test_no_team_members_no_team_flags(self) -> None:
        candidate = _candidate(e=0.80, c=0.80, o=0.80, a=0.10, n=0.80)
        flags = derive_personality_flags(candidate, _scenario())
        team_categories = {
            FlagCategory.COLLISION,
            FlagCategory.COMPLEMENT,
            FlagCategory.FRICTION,
            FlagCategory.GROUPTHINK,
        }
        for flag in flags:
            assert flag.category not in team_categories

    def test_empty_team_list_no_team_flags(self) -> None:
        candidate = _candidate(e=0.80)
        flags = derive_personality_flags(candidate, _scenario(), team_members=[])
        team_categories = {
            FlagCategory.COLLISION,
            FlagCategory.COMPLEMENT,
            FlagCategory.FRICTION,
            FlagCategory.GROUPTHINK,
        }
        for flag in flags:
            assert flag.category not in team_categories


# ---------------------------------------------------------------------------
# Team context flags
# ---------------------------------------------------------------------------


class TestTeamFlags:
    """Team context flag derivation with provided team members."""

    def test_collision_dual_dominance_fires(self) -> None:
        candidate = _candidate(e=0.80)
        team = [_team_member(e=0.80)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "COLLISION_DUAL_DOMINANCE" in _flag_names(flags)

    def test_collision_dual_dominance_does_not_fire_candidate_below(self) -> None:
        candidate = _candidate(e=0.70)
        team = [_team_member(e=0.80)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "COLLISION_DUAL_DOMINANCE" not in _flag_names(flags)

    def test_collision_dual_dominance_does_not_fire_team_below(self) -> None:
        candidate = _candidate(e=0.80)
        team = [_team_member(e=0.70)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "COLLISION_DUAL_DOMINANCE" not in _flag_names(flags)

    def test_collision_at_exact_threshold_does_not_fire(self) -> None:
        candidate = _candidate(e=0.75)
        team = [_team_member(e=0.75)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "COLLISION_DUAL_DOMINANCE" not in _flag_names(flags)

    def test_complement_extraversion_balance_fires(self) -> None:
        candidate = _candidate(e=0.80)
        team = [_team_member(e=0.40)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "COMPLEMENT_EXTRAVERSION_BALANCE" in _flag_names(flags)

    def test_complement_extraversion_balance_does_not_fire_small_diff(self) -> None:
        candidate = _candidate(e=0.50)
        team = [_team_member(e=0.50)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "COMPLEMENT_EXTRAVERSION_BALANCE" not in _flag_names(flags)

    def test_friction_conscientiousness_gap_fires(self) -> None:
        candidate = _candidate(c=0.90)
        team = [_team_member(c=0.40)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "FRICTION_CONSCIENTIOUSNESS_GAP" in _flag_names(flags)

    def test_friction_conscientiousness_gap_at_threshold_does_not_fire(self) -> None:
        candidate = _candidate(c=0.70)
        team = [_team_member(c=0.35)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "FRICTION_CONSCIENTIOUSNESS_GAP" not in _flag_names(flags)

    def test_complement_openness_diversity_fires(self) -> None:
        candidate = _candidate(o=0.80)
        team = [_team_member(o=0.40)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "COMPLEMENT_OPENNESS_DIVERSITY" in _flag_names(flags)

    def test_complement_openness_diversity_does_not_fire_small_diff(self) -> None:
        candidate = _candidate(o=0.50)
        team = [_team_member(o=0.40)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "COMPLEMENT_OPENNESS_DIVERSITY" not in _flag_names(flags)

    def test_groupthink_agreeableness_cluster_fires(self) -> None:
        candidate = _candidate(a=0.80)
        team = [_team_member(a=0.80), _team_member(name="Carol", a=0.75)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "GROUPTHINK_AGREEABLENESS_CLUSTER" in _flag_names(flags)

    def test_groupthink_does_not_fire_candidate_below(self) -> None:
        candidate = _candidate(a=0.65)
        team = [_team_member(a=0.80)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "GROUPTHINK_AGREEABLENESS_CLUSTER" not in _flag_names(flags)

    def test_groupthink_does_not_fire_team_mean_below(self) -> None:
        candidate = _candidate(a=0.80)
        team = [_team_member(a=0.60)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "GROUPTHINK_AGREEABLENESS_CLUSTER" not in _flag_names(flags)

    def test_team_flags_have_correct_evidence_type(self) -> None:
        candidate = _candidate(e=0.80)
        team = [_team_member(e=0.80)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        team_flag = next(f for f in flags if f.name == "COLLISION_DUAL_DOMINANCE")
        assert team_flag.evidence_type == EvidenceType.SCORED_FLAG

    def test_collision_category_and_valence(self) -> None:
        candidate = _candidate(e=0.80)
        team = [_team_member(e=0.80)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        flag = next(f for f in flags if f.name == "COLLISION_DUAL_DOMINANCE")
        assert flag.category == FlagCategory.COLLISION
        assert flag.valence == Valence.NEGATIVE

    def test_multiple_team_members_mean_calculation(self) -> None:
        """Friction uses mean. Two team members at 0.40 and 0.60 → mean 0.50.
        Candidate at 0.90 → gap 0.40 > 0.35 threshold → fires."""
        candidate = _candidate(c=0.90)
        team = [_team_member(c=0.40), _team_member(name="Carol", c=0.60)]
        flags = derive_personality_flags(candidate, _scenario(), team_members=team)
        assert "FRICTION_CONSCIENTIOUSNESS_GAP" in _flag_names(flags)


# ---------------------------------------------------------------------------
# Middleware scores — no flags for moderate values
# ---------------------------------------------------------------------------


class TestModerateScores:
    """Moderate scores should not trigger any flags."""

    def test_all_moderate_returns_no_flags(self) -> None:
        candidate = _candidate(o=0.50, c=0.50, e=0.50, a=0.50, n=0.50)
        flags = derive_personality_flags(candidate, _scenario())
        assert flags == []

    @pytest.mark.parametrize("scenario_name", list(ScenarioName))
    def test_moderate_scores_no_flags_any_scenario(self, scenario_name: ScenarioName) -> None:
        candidate = _candidate(o=0.50, c=0.50, e=0.50, a=0.50, n=0.50)
        flags = derive_personality_flags(candidate, _scenario(scenario_name))
        assert flags == []


# ---------------------------------------------------------------------------
# Post-acquisition specific thresholds
# ---------------------------------------------------------------------------


class TestPostAcquisitionScenario:
    """Post-acquisition has specific openness threshold (0.50)."""

    def test_openness_fit_fires_at_post_acquisition(self) -> None:
        candidate = _candidate(o=0.55)
        flags = derive_personality_flags(candidate, _scenario(ScenarioName.POST_ACQUISITION))
        assert "STRATEGIC_OPENNESS_FIT" in _flag_names(flags)

    def test_no_low_openness_risk_in_post_acquisition(self) -> None:
        """Post-acquisition does not have STRATEGIC_LOW_OPENNESS_RISK."""
        candidate = _candidate(o=0.10)
        flags = derive_personality_flags(candidate, _scenario(ScenarioName.POST_ACQUISITION))
        assert "STRATEGIC_LOW_OPENNESS_RISK" not in _flag_names(flags)
