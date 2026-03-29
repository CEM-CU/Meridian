"""Tests for D6: Output assembly — StageDOutput construction."""

from __future__ import annotations

from shared.models.candidates import BigFiveScores, CandidateData
from shared.models.flags import EvidenceType, Flag, FlagCategory, Valence
from shared.models.pipeline import (
    AssessmentMode,
    StageCOutput,
    StageDOutput,
)
from shared.models.requirements import Priority, Requirement, ScenarioPriority
from shared.models.rubric import Confidence, RubricAssessment, RubricLevel
from shared.models.scenarios import ScenarioConfig, ScenarioName
from stage_d.output_assembly import assemble_stage_d_output

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def _scenario_priority(default: Priority = Priority.MEDIUM) -> ScenarioPriority:
    return ScenarioPriority(
        digital_transformation=default,
        post_acquisition=default,
        turnaround=default,
        stabilization=default,
        growth=default,
    )


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
    level: RubricLevel = RubricLevel.MEETS,
    confidence: Confidence = Confidence.HIGH,
) -> RubricAssessment:
    return RubricAssessment(
        requirement_id=req_id,
        candidate_name=candidate,
        rubric_level=level,
        confidence=confidence,
        notes=None,
    )


def _make_candidate(
    name: str = "Alice",
    big_five: BigFiveScores | None = None,
    personality_source: str | None = None,
) -> CandidateData:
    return CandidateData(
        name=name,
        cv_text="Sample CV text.",
        big_five=big_five,
        personality_source=personality_source,
    )


def _all_scores() -> BigFiveScores:
    return BigFiveScores(O=0.7, C=0.6, E=0.5, A=0.4, N=0.3)


def _make_scenario() -> ScenarioConfig:
    return ScenarioConfig(
        name=ScenarioName.DIGITAL_TRANSFORMATION,
        category_weights={},
    )


def _make_personality_flag(
    name: str = "EXECUTION_CONSCIENTIOUSNESS_FIT",
    candidate_name: str = "Alice",
) -> Flag:
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory.EXECUTION,
        valence=Valence.POSITIVE,
        evidence_type=EvidenceType.SCORED_FLAG,
        big_five_source="C",
        big_five_score=0.8,
        threshold_used=0.7,
        topic_keywords=["execution", "conscientiousness"],
        metadata={"scenario": "digital_transformation", "direction": "above"},
    )


def _make_cv_gap_flag(
    candidate_name: str = "Alice",
    req_id: str = "REQ-01",
    priority: str = "high",
) -> Flag:
    return Flag(
        name="CV_GAP",
        candidate_name=candidate_name,
        category=FlagCategory.EXPERIENCE_GAP,
        valence=Valence.NEGATIVE,
        evidence_type=EvidenceType.CV_RUBRIC,
        requirement_id=req_id,
        rubric_level=RubricLevel.GAP,
        confidence="high",
        topic_keywords=["gap", "missing"],
        metadata={"active_priority": priority},
    )


def _make_cv_exceeds_flag(
    candidate_name: str = "Alice",
    req_id: str = "REQ-02",
) -> Flag:
    return Flag(
        name="CV_EXCEEDS",
        candidate_name=candidate_name,
        category=FlagCategory.EXPERIENCE_STRENGTH,
        valence=Valence.POSITIVE,
        evidence_type=EvidenceType.CV_RUBRIC,
        requirement_id=req_id,
        rubric_level=RubricLevel.EXCEEDS,
        confidence="high",
        topic_keywords=["exceeds", "strong"],
        metadata={"active_priority": "medium"},
    )


def _make_stage_c_output(
    candidates: list[CandidateData] | None = None,
    requirements: list[Requirement] | None = None,
    rubric_assessments: list[RubricAssessment] | None = None,
) -> StageCOutput:
    if candidates is None:
        candidates = [_make_candidate()]
    if requirements is None:
        requirements = [_make_requirement("REQ-01"), _make_requirement("REQ-02")]
    if rubric_assessments is None:
        rubric_assessments = [
            _make_rubric("REQ-01", candidates[0].name),
            _make_rubric("REQ-02", candidates[0].name),
        ]
    return StageCOutput(
        requirements=requirements,
        rubric_assessments=rubric_assessments,
        candidate_data=candidates,
        scenario=_make_scenario(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestStageDOutputAllFields:
    """Test 1: Assembled output has all required fields."""

    def test_stage_d_output_has_all_fields(self) -> None:
        candidate = _make_candidate("Alice", _all_scores(), "manual")
        stage_c = _make_stage_c_output(candidates=[candidate])
        flags = {"Alice": [_make_cv_gap_flag("Alice")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Alice": (AssessmentMode.FULL, "Manual Big Five score entry")}

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        assert isinstance(result, StageDOutput)
        assert result.flags is not None
        assert result.provenance_per_candidate is not None
        assert result.confirmed_requirements is not None
        assert result.candidate_data is not None
        assert result.rubric_matrix is not None
        assert result.scenario is not None


class TestProvenanceCounts:
    """Test 2: personality_flag_count + cv_flag_count == total_flags == len(flags)."""

    def test_provenance_counts_match_actual_flags(self) -> None:
        candidate = _make_candidate("Alice", _all_scores(), "manual")
        stage_c = _make_stage_c_output(candidates=[candidate])
        p_flag = _make_personality_flag(candidate_name="Alice")
        cv_flag = _make_cv_gap_flag("Alice")
        flags = {"Alice": [p_flag, cv_flag]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Alice": (AssessmentMode.FULL, "Manual Big Five score entry")}

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        prov = result.provenance_per_candidate["Alice"]
        assert prov.personality_flag_count == 1
        assert prov.cv_flag_count == 1
        assert prov.total_flags == 2
        assert prov.total_flags == len(flags["Alice"])


class TestAssessmentModeInProvenance:
    """Test 3: Full mode candidate → FULL, partial → PARTIAL."""

    def test_provenance_assessment_mode_full(self) -> None:
        candidate = _make_candidate("Alice", _all_scores(), "manual")
        stage_c = _make_stage_c_output(candidates=[candidate])
        flags = {"Alice": [_make_cv_gap_flag("Alice")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Alice": (AssessmentMode.FULL, "Manual Big Five score entry")}

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        assert result.provenance_per_candidate["Alice"].assessment_mode == AssessmentMode.FULL

    def test_provenance_assessment_mode_partial(self) -> None:
        candidate = _make_candidate("Bob")
        stage_c = _make_stage_c_output(candidates=[candidate])
        flags = {"Bob": [_make_cv_gap_flag("Bob")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Bob": (AssessmentMode.PARTIAL, "No personality data provided")}

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        assert result.provenance_per_candidate["Bob"].assessment_mode == AssessmentMode.PARTIAL


class TestBigFiveAvailable:
    """Test 4: Full mode → big_five_available=True, partial → False."""

    def test_provenance_big_five_available_full(self) -> None:
        candidate = _make_candidate("Alice", _all_scores(), "manual")
        stage_c = _make_stage_c_output(candidates=[candidate])
        flags = {"Alice": [_make_personality_flag(candidate_name="Alice")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Alice": (AssessmentMode.FULL, "Manual Big Five score entry")}

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        assert result.provenance_per_candidate["Alice"].big_five_available is True

    def test_provenance_big_five_available_partial(self) -> None:
        candidate = _make_candidate("Bob")
        stage_c = _make_stage_c_output(candidates=[candidate])
        flags = {"Bob": [_make_cv_gap_flag("Bob")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Bob": (AssessmentMode.PARTIAL, "No personality data provided")}

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        assert result.provenance_per_candidate["Bob"].big_five_available is False


class TestHighPriorityGapCount:
    """Test 5: Correctly counts CV_GAP flags with high priority in metadata."""

    def test_provenance_high_priority_gap_count(self) -> None:
        candidate = _make_candidate("Alice")
        requirements = [
            _make_requirement("REQ-01"),
            _make_requirement("REQ-02"),
            _make_requirement("REQ-03"),
        ]
        rubrics = [
            _make_rubric("REQ-01", "Alice", RubricLevel.GAP),
            _make_rubric("REQ-02", "Alice", RubricLevel.GAP),
            _make_rubric("REQ-03", "Alice", RubricLevel.PARTIAL),
        ]
        stage_c = _make_stage_c_output(candidates=[candidate], requirements=requirements, rubric_assessments=rubrics)
        # Two high priority gaps, one medium, one exceeds
        flags = {
            "Alice": [
                _make_cv_gap_flag("Alice", "REQ-01", "high"),
                _make_cv_gap_flag("Alice", "REQ-02", "high"),
                _make_cv_gap_flag("Alice", "REQ-03", "medium"),
                _make_cv_exceeds_flag("Alice"),
            ]
        }
        modes: dict[str, tuple[AssessmentMode, str]] = {
            "Alice": (AssessmentMode.PARTIAL, "No personality data provided")
        }

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        assert result.provenance_per_candidate["Alice"].high_priority_gap_count == 2


class TestPassThroughFields:
    """Test 6: requirements, candidate_data, rubric_matrix, scenario are identical to StageCOutput."""

    def test_pass_through_fields_from_stage_c(self) -> None:
        candidate = _make_candidate("Alice", _all_scores(), "manual")
        requirements = [_make_requirement("REQ-01"), _make_requirement("REQ-02")]
        rubrics = [_make_rubric("REQ-01", "Alice"), _make_rubric("REQ-02", "Alice")]
        scenario = _make_scenario()
        stage_c = StageCOutput(
            requirements=requirements,
            rubric_assessments=rubrics,
            candidate_data=[candidate],
            scenario=scenario,
        )
        flags = {"Alice": [_make_cv_gap_flag("Alice")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Alice": (AssessmentMode.FULL, "Manual Big Five score entry")}

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        assert result.confirmed_requirements == requirements
        assert result.candidate_data == [candidate]
        assert result.rubric_matrix == rubrics
        assert result.scenario == scenario


class TestFlatFlagList:
    """Test 7: All candidates' flags concatenated into single list."""

    def test_flags_is_flat_list(self) -> None:
        alice = _make_candidate("Alice", _all_scores(), "manual")
        bob = _make_candidate("Bob")
        stage_c = _make_stage_c_output(candidates=[alice, bob])
        alice_flags = [_make_personality_flag(candidate_name="Alice"), _make_cv_gap_flag("Alice")]
        bob_flags = [_make_cv_gap_flag("Bob", "REQ-02")]
        flags = {"Alice": alice_flags, "Bob": bob_flags}
        modes: dict[str, tuple[AssessmentMode, str]] = {
            "Alice": (AssessmentMode.FULL, "Manual Big Five score entry"),
            "Bob": (AssessmentMode.PARTIAL, "No personality data provided"),
        }

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        assert len(result.flags) == len(alice_flags) + len(bob_flags)
        result_names = {f.candidate_name for f in result.flags}
        assert result_names == {"Alice", "Bob"}


class TestRoundTripSerialization:
    """Test 8: StageDOutput.model_dump() → StageDOutput.model_validate() succeeds."""

    def test_round_trip_serialization(self) -> None:
        candidate = _make_candidate("Alice", _all_scores(), "manual")
        stage_c = _make_stage_c_output(candidates=[candidate])
        flags = {"Alice": [_make_personality_flag(candidate_name="Alice"), _make_cv_gap_flag("Alice")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Alice": (AssessmentMode.FULL, "Manual Big Five score entry")}

        original = assemble_stage_d_output(flags, modes, stage_c, [], [])
        serialized = original.model_dump()
        reconstructed = StageDOutput.model_validate(serialized)

        assert reconstructed.flags == original.flags
        assert reconstructed.provenance_per_candidate == original.provenance_per_candidate
        assert reconstructed.scenario == original.scenario


class TestPartialModePersonalityFlags:
    """Test 9: Partial mode candidate has personality_flag_count=0."""

    def test_partial_mode_candidate_zero_personality_flags(self) -> None:
        candidate = _make_candidate("Bob")
        stage_c = _make_stage_c_output(candidates=[candidate])
        # Only CV flags, no personality flags
        flags = {"Bob": [_make_cv_gap_flag("Bob"), _make_cv_exceeds_flag("Bob")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Bob": (AssessmentMode.PARTIAL, "No personality data provided")}

        result = assemble_stage_d_output(flags, modes, stage_c, [], [])

        prov = result.provenance_per_candidate["Bob"]
        assert prov.personality_flag_count == 0
        assert prov.cv_flag_count == 2
        assert prov.total_flags == 2


class TestDimensionWarningsInProvenance:
    """Test 10: Warnings from D4 Check 3 appear in provenance."""

    def test_dimension_warnings_in_provenance(self) -> None:
        candidate = _make_candidate("Alice", _all_scores(), "manual")
        stage_c = _make_stage_c_output(candidates=[candidate])
        flags = {"Alice": [_make_cv_gap_flag("Alice")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Alice": (AssessmentMode.FULL, "Manual Big Five score entry")}
        # Simulate dimension coverage warnings from D4 Check 3
        warnings = [
            "[Check3] Candidate 'Alice': dimension 'N' has no scored flags — assessment on this dimension is limited."
        ]

        result = assemble_stage_d_output(flags, modes, stage_c, warnings, [])

        prov = result.provenance_per_candidate["Alice"]
        assert len(prov.dimension_coverage_warnings) == 1
        assert "Alice" in prov.dimension_coverage_warnings[0]
        assert "dimension 'N'" in prov.dimension_coverage_warnings[0]


class TestCoherenceNotesInProvenance:
    """Test 11: Notes from D4 Check 4 appear in provenance."""

    def test_coherence_notes_in_provenance(self) -> None:
        candidate = _make_candidate("Alice", _all_scores(), "manual")
        stage_c = _make_stage_c_output(candidates=[candidate])
        flags = {"Alice": [_make_personality_flag(candidate_name="Alice"), _make_cv_exceeds_flag("Alice")]}
        modes: dict[str, tuple[AssessmentMode, str]] = {"Alice": (AssessmentMode.FULL, "Manual Big Five score entry")}
        # Simulate coherence notes from D4 Check 4
        notes = [
            "[Check4] Cross-stream tension for 'Alice': strong CV evidence in domain 'EXECUTION' "
            "alongside personality risk flag(s) ['EXECUTION_LOW_CONSCIENTIOUSNESS_RISK']. "
            "Both signals valid — committee should weight appropriately."
        ]

        result = assemble_stage_d_output(flags, modes, stage_c, [], notes)

        prov = result.provenance_per_candidate["Alice"]
        assert len(prov.cross_stream_coherence_notes) == 1
        assert "Alice" in prov.cross_stream_coherence_notes[0]

    def test_coherence_notes_not_mixed_between_candidates(self) -> None:
        """Notes for Alice should not appear in Bob's provenance."""
        alice = _make_candidate("Alice", _all_scores(), "manual")
        bob = _make_candidate("Bob")
        stage_c = _make_stage_c_output(candidates=[alice, bob])
        flags = {
            "Alice": [_make_cv_gap_flag("Alice")],
            "Bob": [_make_cv_gap_flag("Bob")],
        }
        modes: dict[str, tuple[AssessmentMode, str]] = {
            "Alice": (AssessmentMode.FULL, "Manual Big Five score entry"),
            "Bob": (AssessmentMode.PARTIAL, "No personality data provided"),
        }
        notes = ["[Check4] Cross-stream tension for 'Alice': strong CV evidence alongside personality risk."]

        result = assemble_stage_d_output(flags, modes, stage_c, [], notes)

        assert len(result.provenance_per_candidate["Alice"].cross_stream_coherence_notes) == 1
        assert len(result.provenance_per_candidate["Bob"].cross_stream_coherence_notes) == 0
