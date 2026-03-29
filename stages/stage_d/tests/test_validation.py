"""Tests for D4: Validation Layer 0 — 5 deterministic checks on the merged flag set."""

from __future__ import annotations

from shared.models import (
    Confidence,
    EvidenceType,
    Flag,
    FlagCategory,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioPriority,
    Valence,
)
from stage_d.validation import (
    check_cross_stream_coherence,
    check_dimension_coverage,
    check_flag_count,
    check_flag_score_consistency,
    check_mutual_exclusivity,
    validate_merged_flags,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _scenario_priority(
    high_under: str = "digital_transformation",
) -> ScenarioPriority:
    """Build a ScenarioPriority with one field set high, others medium."""
    kwargs: dict[str, Priority] = {
        "digital_transformation": Priority.MEDIUM,
        "post_acquisition": Priority.MEDIUM,
        "turnaround": Priority.MEDIUM,
        "stabilization": Priority.MEDIUM,
        "growth": Priority.MEDIUM,
    }
    kwargs[high_under] = Priority.HIGH
    return ScenarioPriority(**kwargs)


def _make_requirement(req_id: str = "REQ-01", assessable: bool = True) -> Requirement:
    return Requirement(
        requirement_id=req_id,
        text=f"Requirement {req_id}",
        source_quote=f"Source for {req_id}",
        assessable_from_cv=assessable,
        scenario_priority=_scenario_priority(),
    )


def _make_rubric(
    req_id: str = "REQ-01",
    candidate: str = "Alice",
    level: RubricLevel = RubricLevel.GAP,
    confidence: Confidence = Confidence.HIGH,
) -> RubricAssessment:
    return RubricAssessment(
        requirement_id=req_id,
        candidate_name=candidate,
        rubric_level=level,
        confidence=confidence,
    )


def _make_personality_flag(
    name: str = "EXECUTION_CONSCIENTIOUSNESS_FIT",
    candidate: str = "Alice",
    score: float = 0.8,
    threshold: float = 0.65,
    direction: str = "above",
    valence: Valence = Valence.POSITIVE,
    category: FlagCategory = FlagCategory.EXECUTION,
    dimension: str = "C",
) -> Flag:
    return Flag(
        name=name,
        candidate_name=candidate,
        category=category,
        valence=valence,
        evidence_type=EvidenceType.SCORED_FLAG,
        big_five_source=dimension,
        big_five_score=score,
        threshold_used=threshold,
        topic_keywords=["execution", "conscientiousness"],
        metadata={"scenario": "digital_transformation", "direction": direction},
    )


def _make_cv_flag(
    name: str = "CV_GAP",
    candidate: str = "Alice",
    req_id: str = "REQ-01",
    rubric_level: str = "gap",
    valence: Valence = Valence.NEGATIVE,
    category: FlagCategory = FlagCategory.EXPERIENCE_GAP,
    confidence: str | None = "high",
    evidence_type: EvidenceType = EvidenceType.CV_RUBRIC,
) -> Flag:
    return Flag(
        name=name,
        candidate_name=candidate,
        category=category,
        valence=valence,
        evidence_type=evidence_type,
        requirement_id=req_id,
        rubric_level=rubric_level,
        confidence=confidence,
        metadata={"active_priority": "high"},
    )


# ---------------------------------------------------------------------------
# Check 1: Flag-Score Consistency
# ---------------------------------------------------------------------------


class TestCheckFlagScoreConsistency:
    """Tests for check_flag_score_consistency."""

    def test_personality_flag_correct_threshold_passes(self) -> None:
        """Personality flag with score above threshold and direction=above → passes."""
        flag = _make_personality_flag(score=0.80, threshold=0.65, direction="above")
        validated, warnings = check_flag_score_consistency([flag], [])
        assert validated == [flag]
        assert not warnings

    def test_personality_flag_wrong_direction_removed(self) -> None:
        """Personality flag with score=0.50 and direction=above, threshold=0.65 → inconsistent."""
        flag = _make_personality_flag(score=0.50, threshold=0.65, direction="above")
        validated, warnings = check_flag_score_consistency([flag], [])
        assert validated == []
        assert len(warnings) == 1
        assert "Removed" in warnings[0]

    def test_personality_flag_below_direction_passes(self) -> None:
        """Personality flag with score=0.20 below threshold=0.35, direction=below → passes."""
        flag = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            score=0.20,
            threshold=0.35,
            direction="below",
            valence=Valence.NEGATIVE,
        )
        validated, warnings = check_flag_score_consistency([flag], [])
        assert validated == [flag]
        assert not warnings

    def test_personality_flag_below_direction_wrong_score_removed(self) -> None:
        """Personality flag with score=0.80 but direction=below, threshold=0.35 → removed."""
        flag = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            score=0.80,
            threshold=0.35,
            direction="below",
            valence=Valence.NEGATIVE,
        )
        validated, warnings = check_flag_score_consistency([flag], [])
        assert validated == []
        assert len(warnings) == 1

    def test_cv_gap_flag_with_actual_gap_rubric_passes(self) -> None:
        """CV_GAP flag where rubric assessment is 'gap' → passes."""
        flag = _make_cv_flag(name="CV_GAP", rubric_level="gap")
        rubric = _make_rubric(req_id="REQ-01", candidate="Alice", level=RubricLevel.GAP)
        validated, warnings = check_flag_score_consistency([flag], [rubric])
        assert validated == [flag]
        assert not warnings

    def test_cv_gap_flag_with_meets_rubric_removed(self) -> None:
        """CV_GAP flag where rubric assessment is 'meets' → bridge bug, removed."""
        flag = _make_cv_flag(name="CV_GAP", rubric_level="gap")
        rubric = _make_rubric(req_id="REQ-01", candidate="Alice", level=RubricLevel.MEETS)
        validated, warnings = check_flag_score_consistency([flag], [rubric])
        assert validated == []
        assert len(warnings) == 1
        assert "rubric level mismatch" in warnings[0]

    def test_cv_exceeds_with_actual_exceeds_passes(self) -> None:
        """CV_EXCEEDS flag where rubric assessment is 'exceeds' → passes."""
        flag = _make_cv_flag(
            name="CV_EXCEEDS",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        rubric = _make_rubric(req_id="REQ-01", candidate="Alice", level=RubricLevel.EXCEEDS)
        validated, warnings = check_flag_score_consistency([flag], [rubric])
        assert validated == [flag]
        assert not warnings

    def test_cv_exceeds_with_gap_rubric_removed(self) -> None:
        """CV_EXCEEDS flag where rubric assessment is 'gap' → bridge bug, removed."""
        flag = _make_cv_flag(
            name="CV_EXCEEDS",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        rubric = _make_rubric(req_id="REQ-01", candidate="Alice", level=RubricLevel.GAP)
        validated, warnings = check_flag_score_consistency([flag], [rubric])
        assert validated == []
        assert len(warnings) == 1

    def test_cv_partial_with_partial_rubric_passes(self) -> None:
        """CV_PARTIAL flag where rubric assessment is 'partial' → passes."""
        flag = _make_cv_flag(name="CV_PARTIAL", rubric_level="partial")
        rubric = _make_rubric(req_id="REQ-01", candidate="Alice", level=RubricLevel.PARTIAL)
        validated, warnings = check_flag_score_consistency([flag], [rubric])
        assert validated == [flag]
        assert not warnings

    def test_routing_flag_not_subject_to_cv_check(self) -> None:
        """CV_BEHAVIORAL_ROUTED (evidence_type=routing) is not checked for rubric level."""
        flag = Flag(
            name="CV_BEHAVIORAL_ROUTED",
            candidate_name="Alice",
            category=FlagCategory.ROUTING,
            valence=Valence.NEUTRAL,
            evidence_type=EvidenceType.ROUTING,
            requirement_id="REQ-01",
            rubric_level=None,
        )
        validated, warnings = check_flag_score_consistency([flag], [])
        assert validated == [flag]
        assert not warnings

    def test_unknown_cv_flag_name_passes_without_rubric(self) -> None:
        """CV flag with unknown name (not in mapping) passes consistency check."""
        flag = _make_cv_flag(name="CV_SYSTEMATIC_GAP")
        validated, _warnings = check_flag_score_consistency([flag], [])
        assert validated == [flag]

    def test_personality_flag_at_exact_threshold_removed(self) -> None:
        """Personality flag with score exactly equal to threshold is NOT consistent (strict)."""
        flag = _make_personality_flag(score=0.65, threshold=0.65, direction="above")
        validated, warnings = check_flag_score_consistency([flag], [])
        assert validated == []
        assert len(warnings) == 1

    def test_multiple_flags_mixed_results(self) -> None:
        """Mix of consistent and inconsistent flags — only inconsistent removed."""
        good_flag = _make_personality_flag(score=0.80, threshold=0.65, direction="above")
        bad_flag = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            score=0.80,
            threshold=0.35,
            direction="below",
            valence=Valence.NEGATIVE,
        )
        validated, warnings = check_flag_score_consistency([good_flag, bad_flag], [])
        assert validated == [good_flag]
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Check 2: Mutual Exclusivity
# ---------------------------------------------------------------------------


class TestCheckMutualExclusivity:
    """Tests for check_mutual_exclusivity."""

    def test_unconditional_contradiction_removes_negative_flag(self) -> None:
        """EXECUTION_CONSCIENTIOUSNESS_FIT vs EXECUTION_LOW_CONSCIENTIOUSNESS_RISK → remove negative."""
        positive_flag = _make_personality_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            valence=Valence.POSITIVE,
        )
        negative_flag = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            valence=Valence.NEGATIVE,
        )
        validated, warnings = check_mutual_exclusivity([positive_flag, negative_flag])
        assert len(validated) == 1
        assert validated[0].name == "EXECUTION_CONSCIENTIOUSNESS_FIT"
        assert len(warnings) == 1
        assert "Contradiction" in warnings[0]

    def test_no_contradiction_both_flags_survive(self) -> None:
        """Two unrelated flags → no removal."""
        flag_a = _make_personality_flag(name="EXECUTION_CONSCIENTIOUSNESS_FIT")
        flag_b = _make_personality_flag(
            name="DERAILMENT_NEUROTICISM_UNDER_STRESS",
            valence=Valence.NEGATIVE,
            category=FlagCategory.DERAILMENT,
            dimension="N",
        )
        validated, warnings = check_mutual_exclusivity([flag_a, flag_b])
        assert len(validated) == 2
        assert not warnings

    def test_strategic_openness_contradiction(self) -> None:
        """STRATEGIC_OPENNESS_FIT vs STRATEGIC_LOW_OPENNESS_RISK → remove negative."""
        positive_flag = _make_personality_flag(
            name="STRATEGIC_OPENNESS_FIT",
            category=FlagCategory.STRATEGIC,
            valence=Valence.POSITIVE,
        )
        negative_flag = _make_personality_flag(
            name="STRATEGIC_LOW_OPENNESS_RISK",
            category=FlagCategory.STRATEGIC,
            valence=Valence.NEGATIVE,
        )
        validated, _warnings = check_mutual_exclusivity([positive_flag, negative_flag])
        assert len(validated) == 1
        assert validated[0].name == "STRATEGIC_OPENNESS_FIT"

    def test_cultural_extraversion_contradiction(self) -> None:
        """CULTURAL_EXTRAVERSION_FIT vs CULTURAL_INTROVERSION_NOTE → remove neutral note."""
        pos_flag = _make_personality_flag(
            name="CULTURAL_EXTRAVERSION_FIT",
            category=FlagCategory.CULTURAL,
            valence=Valence.POSITIVE,
        )
        neutral_flag = _make_personality_flag(
            name="CULTURAL_INTROVERSION_NOTE",
            category=FlagCategory.CULTURAL,
            valence=Valence.NEUTRAL,
        )
        validated, _warnings = check_mutual_exclusivity([pos_flag, neutral_flag])
        assert len(validated) == 1
        assert validated[0].name == "CULTURAL_EXTRAVERSION_FIT"

    def test_same_valence_contradiction_removes_second_flag(self) -> None:
        """Both flags negative → second flag removed (deterministic tiebreaker)."""
        flag_a = _make_personality_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            valence=Valence.NEGATIVE,
            category=FlagCategory.EXECUTION,
        )
        flag_b = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            valence=Valence.NEGATIVE,
            category=FlagCategory.EXECUTION,
        )
        validated, warnings = check_mutual_exclusivity([flag_a, flag_b])
        assert len(validated) == 1
        assert validated[0] is flag_a
        assert len(warnings) == 1

    def test_conditional_contradiction_same_requirement_removes_lower_confidence(self) -> None:
        """CV_EXCEEDS vs CV_GAP on SAME requirement_id → remove lower-confidence flag."""
        high_conf = _make_cv_flag(
            name="CV_EXCEEDS",
            req_id="REQ-01",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
            confidence="high",
        )
        low_conf = _make_cv_flag(
            name="CV_GAP",
            req_id="REQ-01",
            rubric_level="gap",
            confidence="low",
        )
        validated, warnings = check_mutual_exclusivity([high_conf, low_conf])
        assert len(validated) == 1
        assert validated[0].name == "CV_EXCEEDS"
        assert len(warnings) == 1

    def test_conditional_contradiction_different_requirements_both_survive(self) -> None:
        """CV_EXCEEDS on REQ-01 vs CV_GAP on REQ-02 → different requirements, no contradiction."""
        exceeds_flag = _make_cv_flag(
            name="CV_EXCEEDS",
            req_id="REQ-01",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        gap_flag = _make_cv_flag(
            name="CV_GAP",
            req_id="REQ-02",
            rubric_level="gap",
        )
        validated, warnings = check_mutual_exclusivity([exceeds_flag, gap_flag])
        assert len(validated) == 2
        assert not warnings

    def test_cv_exceeds_vs_cv_partial_same_req_removes_lower_confidence(self) -> None:
        """CV_EXCEEDS vs CV_PARTIAL on same requirement → lower-confidence removed."""
        exceeds = _make_cv_flag(
            name="CV_EXCEEDS",
            req_id="REQ-03",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
            confidence="high",
        )
        partial = _make_cv_flag(
            name="CV_PARTIAL",
            req_id="REQ-03",
            rubric_level="partial",
            confidence="medium",
        )
        validated, _warnings = check_mutual_exclusivity([exceeds, partial])
        assert len(validated) == 1
        assert validated[0].name == "CV_EXCEEDS"

    def test_cv_exceeds_vs_cv_partial_different_req_both_survive(self) -> None:
        """CV_EXCEEDS on REQ-01 and CV_PARTIAL on REQ-02 → no contradiction."""
        exceeds = _make_cv_flag(
            name="CV_EXCEEDS",
            req_id="REQ-01",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        partial = _make_cv_flag(
            name="CV_PARTIAL",
            req_id="REQ-02",
            rubric_level="partial",
        )
        validated, warnings = check_mutual_exclusivity([exceeds, partial])
        assert len(validated) == 2
        assert not warnings

    def test_no_flags_returns_empty(self) -> None:
        """Empty flag list → empty output."""
        validated, warnings = check_mutual_exclusivity([])
        assert validated == []
        assert not warnings

    def test_multiple_non_contradicting_flags_all_survive(self) -> None:
        """Four unrelated flags → all survive."""
        flags = [
            _make_personality_flag("EXECUTION_CONSCIENTIOUSNESS_FIT"),
            _make_cv_flag("CV_GAP", req_id="REQ-01"),
            _make_cv_flag("CV_GAP", req_id="REQ-02"),
            _make_cv_flag(
                "CV_EXCEEDS", req_id="REQ-03", valence=Valence.POSITIVE, category=FlagCategory.EXPERIENCE_STRENGTH
            ),
        ]
        validated, warnings = check_mutual_exclusivity(flags)
        assert len(validated) == 4
        assert not warnings


# ---------------------------------------------------------------------------
# Check 3: Dimension Coverage
# ---------------------------------------------------------------------------


class TestCheckDimensionCoverage:
    """Tests for check_dimension_coverage."""

    def _all_dims_flags(self, candidate: str = "Alice") -> list[Flag]:
        """Build one flag per Big Five dimension for a candidate."""
        dims = [
            ("O", "STRATEGIC_OPENNESS_FIT", FlagCategory.STRATEGIC, Valence.POSITIVE),
            ("C", "EXECUTION_CONSCIENTIOUSNESS_FIT", FlagCategory.EXECUTION, Valence.POSITIVE),
            ("E", "CULTURAL_EXTRAVERSION_FIT", FlagCategory.CULTURAL, Valence.POSITIVE),
            ("A", "DARK_SIDE_LOW_AGREEABLENESS", FlagCategory.DARK_SIDE, Valence.NEGATIVE),
            ("N", "DERAILMENT_NEUROTICISM_UNDER_STRESS", FlagCategory.DERAILMENT, Valence.NEGATIVE),
        ]
        return [
            _make_personality_flag(
                name=name,
                candidate=candidate,
                dimension=dim,
                category=cat,
                valence=val,
            )
            for dim, name, cat, val in dims
        ]

    def test_full_mode_all_dimensions_covered_no_warning(self) -> None:
        """Full mode with flags for all 5 dimensions → no dimension warnings."""
        flags = self._all_dims_flags()
        warnings = check_dimension_coverage(flags, [], [], {"Alice": "full"})
        dim_warnings = [w for w in warnings if "dimension" in w]
        assert not dim_warnings

    def test_full_mode_missing_dimension_warns(self) -> None:
        """Full mode missing Agreeableness flag → warning for dimension 'A'."""
        flags = [f for f in self._all_dims_flags() if f.big_five_source != "A"]
        warnings = check_dimension_coverage(flags, [], [], {"Alice": "full"})
        assert any("dimension 'A'" in w for w in warnings)

    def test_partial_mode_skips_personality_dimension_check(self) -> None:
        """Partial mode → personality dimension coverage check is skipped entirely."""
        warnings = check_dimension_coverage([], [], [], {"Alice": "partial"})
        assert not any("dimension" in w for w in warnings)

    def test_requirement_with_meets_rubric_no_flag_ok(self) -> None:
        """Requirement assessed as 'meets' with no flag → by design, no warning."""
        req = _make_requirement("REQ-01", assessable=True)
        rubric = _make_rubric("REQ-01", "Alice", RubricLevel.MEETS)
        warnings = check_dimension_coverage([], [req], [rubric], {"Alice": "full"})
        req_warnings = [w for w in warnings if "REQ-01" in w]
        assert not req_warnings

    def test_requirement_with_no_flag_and_no_meets_warns(self) -> None:
        """CV-assessable requirement with no flag and no rubric → warning."""
        req = _make_requirement("REQ-05", assessable=True)
        warnings = check_dimension_coverage([], [req], [], {"Alice": "full"})
        assert any("REQ-05" in w for w in warnings)

    def test_non_assessable_requirement_not_checked(self) -> None:
        """Requirement with assessable_from_cv=False → never triggers coverage warning."""
        req = _make_requirement("REQ-BEHAV", assessable=False)
        warnings = check_dimension_coverage([], [req], [], {"Alice": "full"})
        req_warnings = [w for w in warnings if "REQ-BEHAV" in w]
        assert not req_warnings

    def test_requirement_with_gap_rubric_and_flag_no_warning(self) -> None:
        """Requirement with CV_GAP flag → covered, no warning."""
        req = _make_requirement("REQ-01", assessable=True)
        rubric = _make_rubric("REQ-01", "Alice", RubricLevel.GAP)
        flag = _make_cv_flag(name="CV_GAP", candidate="Alice", req_id="REQ-01")
        warnings = check_dimension_coverage([flag], [req], [rubric], {"Alice": "full"})
        req_warnings = [w for w in warnings if "REQ-01" in w]
        assert not req_warnings

    def test_full_mode_five_dimensions_missing_two(self) -> None:
        """Full mode missing O and N → two dimension warnings."""
        flags = [f for f in self._all_dims_flags() if f.big_five_source not in {"O", "N"}]
        warnings = check_dimension_coverage(flags, [], [], {"Alice": "full"})
        assert any("dimension 'O'" in w for w in warnings)
        assert any("dimension 'N'" in w for w in warnings)


# ---------------------------------------------------------------------------
# Check 4: Cross-Stream Coherence
# ---------------------------------------------------------------------------


class TestCheckCrossStreamCoherence:
    """Tests for check_cross_stream_coherence."""

    def test_positive_cv_and_negative_personality_same_domain_produces_note(self) -> None:
        """EXPERIENCE_STRENGTH CV flag + EXECUTION negative personality flag → coherence note."""
        cv_pos = _make_cv_flag(
            name="CV_EXCEEDS",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        personality_neg = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            valence=Valence.NEGATIVE,
            category=FlagCategory.EXECUTION,
        )
        notes = check_cross_stream_coherence([cv_pos, personality_neg])
        assert len(notes) == 1
        assert "Cross-stream tension" in notes[0]
        assert "Alice" in notes[0]

    def test_no_cross_stream_tension_no_notes(self) -> None:
        """Positive CV flag with no negative personality flag → no coherence notes."""
        cv_pos = _make_cv_flag(
            name="CV_EXCEEDS",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        notes = check_cross_stream_coherence([cv_pos])
        assert not notes

    def test_negative_personality_only_no_notes(self) -> None:
        """Only negative personality flag, no positive CV flag → no coherence notes."""
        personality_neg = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            valence=Valence.NEGATIVE,
            category=FlagCategory.EXECUTION,
        )
        notes = check_cross_stream_coherence([personality_neg])
        assert not notes

    def test_positive_personality_and_positive_cv_no_notes(self) -> None:
        """Both positive → no tension."""
        cv_pos = _make_cv_flag(
            name="CV_EXCEEDS",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        personality_pos = _make_personality_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXECUTION,
        )
        notes = check_cross_stream_coherence([cv_pos, personality_pos])
        assert not notes

    def test_cross_stream_tension_per_candidate(self) -> None:
        """Each candidate's cross-stream tension is reported independently."""
        alice_cv = _make_cv_flag(
            name="CV_EXCEEDS",
            candidate="Alice",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        alice_neg = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            candidate="Alice",
            valence=Valence.NEGATIVE,
            category=FlagCategory.EXECUTION,
        )
        bob_pos = _make_personality_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            candidate="Bob",
            valence=Valence.POSITIVE,
        )
        notes = check_cross_stream_coherence([alice_cv, alice_neg, bob_pos])
        alice_notes = [n for n in notes if "Alice" in n]
        bob_notes = [n for n in notes if "Bob" in n]
        assert len(alice_notes) == 1
        assert not bob_notes

    def test_empty_flags_no_notes(self) -> None:
        """Empty flag list → no coherence notes."""
        notes = check_cross_stream_coherence([])
        assert not notes


# ---------------------------------------------------------------------------
# Check 5: Flag Count Reasonableness
# ---------------------------------------------------------------------------


class TestCheckFlagCount:
    """Tests for check_flag_count."""

    def _make_flags(self, candidate: str, count: int) -> list[Flag]:
        return [
            _make_personality_flag(
                name=f"FLAG_{i}",
                candidate=candidate,
            )
            for i in range(count)
        ]

    def test_thirty_flags_warns_noisy(self) -> None:
        """30 flags for a candidate → 'noisy' warning."""
        flags = self._make_flags("Alice", 30)
        warnings = check_flag_count(flags)
        assert len(warnings) == 1
        assert "noisy" in warnings[0]
        assert "Alice" in warnings[0]

    def test_twenty_six_flags_warns_noisy(self) -> None:
        """26 flags (just above 25) → noisy warning."""
        flags = self._make_flags("Alice", 26)
        warnings = check_flag_count(flags)
        assert any("noisy" in w for w in warnings)

    def test_twenty_five_flags_no_warning(self) -> None:
        """Exactly 25 flags (at watermark, not above) → no warning."""
        flags = self._make_flags("Alice", 25)
        warnings = check_flag_count(flags)
        assert not warnings

    def test_two_flags_warns_thin(self) -> None:
        """2 flags for a candidate → 'thin' warning."""
        flags = self._make_flags("Alice", 2)
        warnings = check_flag_count(flags)
        assert len(warnings) == 1
        assert "thin" in warnings[0]
        assert "Alice" in warnings[0]

    def test_zero_flags_warns_thin(self) -> None:
        """0 flags (empty candidate in dict) doesn't appear in warnings if not counted."""
        # check_flag_count only warns about candidates present in the flag list.
        warnings = check_flag_count([])
        assert not warnings

    def test_three_flags_no_warning(self) -> None:
        """Exactly 3 flags (at low watermark, not below) → no warning."""
        flags = self._make_flags("Alice", 3)
        warnings = check_flag_count(flags)
        assert not warnings

    def test_twelve_flags_no_warning(self) -> None:
        """12 flags (in normal range 8-18) → no warning."""
        flags = self._make_flags("Alice", 12)
        warnings = check_flag_count(flags)
        assert not warnings

    def test_multiple_candidates_each_checked_independently(self) -> None:
        """Alice noisy + Bob thin + Carol normal → two warnings, Carol none."""
        alice_flags = self._make_flags("Alice", 30)
        bob_flags = self._make_flags("Bob", 2)
        carol_flags = self._make_flags("Carol", 10)
        warnings = check_flag_count(alice_flags + bob_flags + carol_flags)
        alice_warnings = [w for w in warnings if "Alice" in w]
        bob_warnings = [w for w in warnings if "Bob" in w]
        carol_warnings = [w for w in warnings if "Carol" in w]
        assert len(alice_warnings) == 1
        assert "noisy" in alice_warnings[0]
        assert len(bob_warnings) == 1
        assert "thin" in bob_warnings[0]
        assert not carol_warnings


# ---------------------------------------------------------------------------
# Runner: validate_merged_flags
# ---------------------------------------------------------------------------


class TestValidateMergedFlags:
    """Tests for the validate_merged_flags runner."""

    def test_runner_full_pipeline_mixed_flags(self) -> None:
        """Full pipeline with valid, inconsistent, and contradictory flags."""
        # Consistent personality flag — should survive.
        good_personality = _make_personality_flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            score=0.80,
            threshold=0.65,
            direction="above",
        )
        # Inconsistent personality flag (score below threshold for 'above' direction).
        bad_personality = _make_personality_flag(
            name="STRATEGIC_OPENNESS_FIT",
            score=0.30,
            threshold=0.70,
            direction="above",
            category=FlagCategory.STRATEGIC,
            valence=Valence.POSITIVE,
            dimension="O",
        )
        # CV flag consistent with rubric.
        cv_gap = _make_cv_flag(name="CV_GAP", req_id="REQ-01", rubric_level="gap")
        # CV flag inconsistent with rubric (CV_EXCEEDS but rubric says gap).
        cv_bad = _make_cv_flag(
            name="CV_EXCEEDS",
            req_id="REQ-02",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )

        rubric_gap = _make_rubric("REQ-01", "Alice", RubricLevel.GAP)
        rubric_bad = _make_rubric("REQ-02", "Alice", RubricLevel.GAP)  # contradicts CV_EXCEEDS

        req1 = _make_requirement("REQ-01")
        req2 = _make_requirement("REQ-02")

        result, warnings, _coherence_notes = validate_merged_flags(
            {"Alice": [good_personality, bad_personality, cv_gap, cv_bad]},
            rubric_assessments=[rubric_gap, rubric_bad],
            requirements=[req1, req2],
            assessment_mode_per_candidate={"Alice": "full"},
        )

        # bad_personality removed in Check 1. cv_bad removed in Check 1.
        alice_names = [f.name for f in result["Alice"]]
        assert "EXECUTION_CONSCIENTIOUSNESS_FIT" in alice_names
        assert "STRATEGIC_OPENNESS_FIT" not in alice_names
        assert "CV_GAP" in alice_names
        assert "CV_EXCEEDS" not in alice_names

        # Warnings generated for removals.
        assert len([w for w in warnings if "Removed" in w or "mismatch" in w]) >= 2

    def test_runner_returns_correct_structure(self) -> None:
        """Runner returns (dict, list, list) with correct types."""
        flag = _make_personality_flag()
        result, warnings, notes = validate_merged_flags(
            {"Alice": [flag]},
            rubric_assessments=[],
            requirements=[],
            assessment_mode_per_candidate={"Alice": "full"},
        )
        assert isinstance(result, dict)
        assert isinstance(warnings, list)
        assert isinstance(notes, list)

    def test_runner_partial_mode_skips_dimension_check(self) -> None:
        """Partial mode candidate generates no dimension coverage warnings."""
        flag = _make_cv_flag()
        _result, warnings, _notes = validate_merged_flags(
            {"Alice": [flag]},
            rubric_assessments=[],
            requirements=[],
            assessment_mode_per_candidate={"Alice": "partial"},
        )
        dim_warnings = [w for w in warnings if "dimension" in w]
        assert not dim_warnings

    def test_runner_count_warning_surfaced(self) -> None:
        """Runner surfaces count warnings for noisy flag sets."""
        flags = [_make_personality_flag(name=f"FLAG_{i}", score=0.8) for i in range(30)]
        _result, warnings, _notes = validate_merged_flags(
            {"Alice": flags},
            rubric_assessments=[],
            requirements=[],
            assessment_mode_per_candidate={"Alice": "full"},
        )
        assert any("noisy" in w for w in warnings)

    def test_runner_multiple_candidates(self) -> None:
        """Runner handles multiple candidates independently."""
        alice_flag = _make_personality_flag(candidate="Alice", score=0.8)
        bob_flag = _make_personality_flag(candidate="Bob", score=0.8)
        result, _warnings, _notes = validate_merged_flags(
            {"Alice": [alice_flag], "Bob": [bob_flag]},
            rubric_assessments=[],
            requirements=[],
            assessment_mode_per_candidate={"Alice": "full", "Bob": "full"},
        )
        assert set(result.keys()) == {"Alice", "Bob"}
        assert len(result["Alice"]) == 1
        assert len(result["Bob"]) == 1

    def test_runner_coherence_note_surfaced(self) -> None:
        """Runner surfaces coherence notes for cross-stream tension."""
        cv_pos = _make_cv_flag(
            name="CV_EXCEEDS",
            rubric_level="exceeds",
            valence=Valence.POSITIVE,
            category=FlagCategory.EXPERIENCE_STRENGTH,
        )
        personality_neg = _make_personality_flag(
            name="EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            valence=Valence.NEGATIVE,
            category=FlagCategory.EXECUTION,
            score=0.20,
            threshold=0.35,
            direction="below",
        )
        rubric = _make_rubric("REQ-01", "Alice", RubricLevel.EXCEEDS)
        _result, _warnings, notes = validate_merged_flags(
            {"Alice": [cv_pos, personality_neg]},
            rubric_assessments=[rubric],
            requirements=[],
            assessment_mode_per_candidate={"Alice": "full"},
        )
        assert any("Cross-stream tension" in n for n in notes)

    def test_runner_empty_input(self) -> None:
        """Empty flags_per_candidate → empty outputs."""
        result, warnings, notes = validate_merged_flags(
            {},
            rubric_assessments=[],
            requirements=[],
            assessment_mode_per_candidate={},
        )
        assert result == {}
        assert not warnings
        assert not notes

    def test_runner_does_not_mutate_input(self) -> None:
        """Runner must not mutate the input flag lists."""
        flag = _make_personality_flag()
        original_flags = [flag]
        flags_per_candidate = {"Alice": original_flags}

        validate_merged_flags(
            flags_per_candidate,
            rubric_assessments=[],
            requirements=[],
            assessment_mode_per_candidate={"Alice": "full"},
        )

        # Original list unchanged.
        assert flags_per_candidate["Alice"] is original_flags
        assert len(original_flags) == 1
