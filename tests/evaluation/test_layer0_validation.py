"""Tests for Layer 0 — Stage D Output Validation (E1).

Covers all 13 specified test cases plus helpers for building realistic
test fixtures from shared.models. No imports from stage_c or stage_d.
"""

from __future__ import annotations

from meridian.evaluation.layer0_validation import validate_stage_d_output
from meridian.models.candidates import BigFiveScores, CandidateData
from meridian.models.flags import EvidenceType, Flag, FlagCategory, Valence
from meridian.models.pipeline import AssessmentMode, FlagProvenance, StageDOutput
from meridian.models.requirements import Priority, Requirement, ScenarioPriority
from meridian.models.rubric import Confidence, RubricAssessment, RubricLevel
from meridian.models.scenarios import ScenarioConfig, ScenarioName

# ---------------------------------------------------------------------------
# Fixture helpers — all return new objects each call (no mutation risk)
# ---------------------------------------------------------------------------


def _scenario() -> ScenarioConfig:
    """Return a minimal ScenarioConfig."""
    return ScenarioConfig(name=ScenarioName.DIGITAL_TRANSFORMATION)


def _scenario_priority(default: Priority = Priority.HIGH) -> ScenarioPriority:
    return ScenarioPriority(
        digital_transformation=default,
        post_acquisition=default,
        turnaround=default,
        stabilization=default,
        growth=default,
    )


def _requirement(req_id: str = "REQ-01") -> Requirement:
    """Return a minimal Requirement."""
    return Requirement(
        requirement_id=req_id,
        text="Lead enterprise-wide digital transformation programmes",
        source_quote="Lead enterprise-wide digital transformation programmes",
        assessable_from_cv=True,
        scenario_priority=_scenario_priority(),
    )


def _big_five(
    O: float = 0.8,  # noqa: E741
    C: float = 0.7,
    E: float = 0.6,
    A: float = 0.5,
    N: float = 0.3,
) -> BigFiveScores:
    return BigFiveScores(O=O, C=C, E=E, A=A, N=N)


def _candidate(
    name: str = "Alice Chen",
    with_big_five: bool = True,
) -> CandidateData:
    return CandidateData(
        name=name,
        cv_text="Sample CV text for testing purposes.",
        big_five=_big_five() if with_big_five else None,
    )


def _provenance(candidate_name: str = "Alice Chen") -> FlagProvenance:
    return FlagProvenance(
        assessment_mode=AssessmentMode.FULL,
        personality_flag_count=1,
        cv_flag_count=1,
        total_flags=2,
        big_five_available=True,
    )


def _valid_personality_flag(
    candidate_name: str = "Alice Chen",
    name: str = "EXECUTION_CONSCIENTIOUSNESS_FIT",
    big_five_source: str = "C",
) -> Flag:
    """Return a valid personality flag."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory.EXECUTION,
        valence=Valence.POSITIVE,
        evidence_type=EvidenceType.SCORED_FLAG,
        big_five_source=big_five_source,
        big_five_score=0.7,
        threshold_used=0.6,
        topic_keywords=["conscientiousness", "execution"],
    )


def _valid_cv_flag(
    candidate_name: str = "Alice Chen",
    name: str = "CV_GAP",
    requirement_id: str = "REQ-01",
    rubric_level: str = "gap",
) -> Flag:
    """Return a valid CV-derived flag."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory.EXPERIENCE_GAP,
        valence=Valence.NEGATIVE,
        evidence_type=EvidenceType.REQUIREMENT_GAP,
        requirement_id=requirement_id,
        rubric_level=rubric_level,
        cv_citation=None,
        topic_keywords=["experience", "gap"],
    )


def _valid_pattern_flag(
    candidate_name: str = "Alice Chen",
    name: str = "CV_LOW_CONFIDENCE_CLUSTER",
) -> Flag:
    """Return a valid pattern flag (exempt from requirement_id check)."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory.EVIDENCE_QUALITY,
        valence=Valence.NEGATIVE,
        evidence_type=EvidenceType.CV_PATTERN,
        rubric_level="low_confidence",
        # requirement_id intentionally absent — pattern flags are exempt
    )


def _stage_d_output(
    flags: list[Flag] | None = None,
    requirements: list[Requirement] | None = None,
    candidates: list[CandidateData] | None = None,
) -> StageDOutput:
    """Build a minimal StageDOutput with sensible defaults."""
    reqs = requirements if requirements is not None else [_requirement("REQ-01")]
    cands = candidates if candidates is not None else [_candidate()]
    all_flags = flags if flags is not None else []
    provenance = {c.name: _provenance(c.name) for c in cands}

    return StageDOutput(
        flags=all_flags,
        provenance_per_candidate=provenance,
        confirmed_requirements=reqs,
        candidate_data=cands,
        rubric_matrix=[
            RubricAssessment(
                requirement_id="REQ-01",
                candidate_name=cands[0].name,
                rubric_level=RubricLevel.GAP,
                confidence=Confidence.HIGH,
            )
        ],
        scenario=_scenario(),
    )


# ---------------------------------------------------------------------------
# Test 1: Valid StageDOutput passes unchanged
# ---------------------------------------------------------------------------


class TestValidInputPassesUnchanged:
    """A fully valid StageDOutput produces no stripped flags and no warnings."""

    def test_valid_personality_flag_passes(self) -> None:
        flag = _valid_personality_flag()
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert warnings == []
        assert len(output.flags) == 1
        assert output.flags[0].name == "EXECUTION_CONSCIENTIOUSNESS_FIT"

    def test_valid_cv_flag_passes(self) -> None:
        flag = _valid_cv_flag()
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert warnings == []
        assert len(output.flags) == 1

    def test_both_valid_flags_pass(self) -> None:
        flags = [_valid_personality_flag(), _valid_cv_flag()]
        output, warnings = validate_stage_d_output(_stage_d_output(flags=flags))
        assert warnings == []
        assert len(output.flags) == 2


# ---------------------------------------------------------------------------
# Test 2: Unknown flag name → stripped + HALLUCINATED_FLAG warning
# ---------------------------------------------------------------------------


class TestUnknownFlagName:
    def test_unknown_name_stripped(self) -> None:
        bad_flag = Flag(
            name="INVENTED_SIGNAL_XYZ",
            candidate_name="Alice Chen",
            category=FlagCategory.EXECUTION,
            valence=Valence.POSITIVE,
            evidence_type=EvidenceType.SCORED_FLAG,
            big_five_source="C",
        )
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[bad_flag]))
        assert len(output.flags) == 0
        assert len(warnings) == 1
        assert "HALLUCINATED_FLAG_IN_DERIVATION" in warnings[0]
        assert "INVENTED_SIGNAL_XYZ" in warnings[0]


# ---------------------------------------------------------------------------
# Test 3: CV flag missing requirement_id → stripped
# ---------------------------------------------------------------------------


class TestCVFlagMissingRequirementId:
    def test_cv_flag_missing_requirement_id_stripped(self) -> None:
        flag = Flag(
            name="CV_GAP",
            candidate_name="Alice Chen",
            category=FlagCategory.EXPERIENCE_GAP,
            valence=Valence.NEGATIVE,
            evidence_type=EvidenceType.REQUIREMENT_GAP,
            rubric_level="gap",
            # requirement_id intentionally absent for a non-pattern flag
        )
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert len(output.flags) == 0
        assert any("requirement_id" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test 4: CV flag missing rubric_level → stripped
# ---------------------------------------------------------------------------


class TestCVFlagMissingRubricLevel:
    def test_cv_flag_missing_rubric_level_stripped(self) -> None:
        flag = Flag(
            name="CV_EXCEEDS",
            candidate_name="Alice Chen",
            category=FlagCategory.EXPERIENCE_STRENGTH,
            valence=Valence.POSITIVE,
            evidence_type=EvidenceType.CV_RUBRIC,
            requirement_id="REQ-01",
            # rubric_level intentionally absent
        )
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert len(output.flags) == 0
        assert any("rubric_level" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test 5: Personality flag missing big_five_source → stripped
# ---------------------------------------------------------------------------


class TestPersonalityFlagMissingBigFiveSource:
    def test_personality_flag_missing_big_five_source_stripped(self) -> None:
        flag = Flag(
            name="EXECUTION_CONSCIENTIOUSNESS_FIT",
            candidate_name="Alice Chen",
            category=FlagCategory.EXECUTION,
            valence=Valence.POSITIVE,
            evidence_type=EvidenceType.SCORED_FLAG,
            # big_five_source intentionally absent
        )
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert len(output.flags) == 0
        assert any("big_five_source" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test 6: CV flag with non-existent requirement_id → stripped
# ---------------------------------------------------------------------------


class TestCVFlagNonExistentRequirementId:
    def test_unknown_requirement_id_stripped(self) -> None:
        flag = _valid_cv_flag(requirement_id="REQ-99")
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag], requirements=[_requirement("REQ-01")]))
        assert len(output.flags) == 0
        assert any("REQ-99" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test 7: Personality flag with invalid big_five_source (e.g. "X") → stripped
# ---------------------------------------------------------------------------


class TestPersonalityFlagInvalidBigFiveSource:
    def test_invalid_big_five_source_stripped(self) -> None:
        flag = _valid_personality_flag(big_five_source="X")
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert len(output.flags) == 0
        assert any("X" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test 8: Personality flag referencing dimension but candidate has no big_five
# ---------------------------------------------------------------------------


class TestPersonalityFlagCandidateNoBigFive:
    def test_no_big_five_scores_strips_personality_flag(self) -> None:
        candidate = _candidate(with_big_five=False)
        flag = _valid_personality_flag(candidate_name=candidate.name)
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag], candidates=[candidate]))
        assert len(output.flags) == 0
        assert any("Big Five" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test 9: Pattern flags without requirement_id → passes (exempt)
# ---------------------------------------------------------------------------


class TestPatternFlagsExempt:
    def test_cv_low_confidence_cluster_without_req_id_passes(self) -> None:
        flag = _valid_pattern_flag(name="CV_LOW_CONFIDENCE_CLUSTER")
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert warnings == []
        assert len(output.flags) == 1

    def test_cv_systematic_gap_without_req_id_passes(self) -> None:
        flag = _valid_pattern_flag(name="CV_SYSTEMATIC_GAP")
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert warnings == []
        assert len(output.flags) == 1


# ---------------------------------------------------------------------------
# Test 10: Multiple violations on same flag → stripped once, combined warning
# ---------------------------------------------------------------------------


class TestMultipleViolationsCombined:
    def test_multiple_violations_produce_one_warning_entry(self) -> None:
        # CV flag missing both requirement_id and rubric_level
        flag = Flag(
            name="CV_PARTIAL",
            candidate_name="Alice Chen",
            category=FlagCategory.EXPERIENCE_GAP,
            valence=Valence.NEUTRAL,
            evidence_type=EvidenceType.CV_RUBRIC,
            # Both requirement_id and rubric_level absent
        )
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[flag]))
        assert len(output.flags) == 0
        # Only one warning entry for this flag (though it contains both reasons)
        assert len(warnings) == 1
        assert "requirement_id" in warnings[0]
        assert "rubric_level" in warnings[0]


# ---------------------------------------------------------------------------
# Test 11: Empty flag list → no crash, empty output
# ---------------------------------------------------------------------------


class TestEmptyFlagList:
    def test_empty_flag_list_returns_empty_output(self) -> None:
        output, warnings = validate_stage_d_output(_stage_d_output(flags=[]))
        assert output.flags == []
        assert warnings == []


# ---------------------------------------------------------------------------
# Test 12: Mix of valid and invalid → only valid survive, order preserved
# ---------------------------------------------------------------------------


class TestMixedValidInvalid:
    def test_only_valid_flags_survive_in_order(self) -> None:
        reqs = [_requirement("REQ-01"), _requirement("REQ-02")]
        candidates = [_candidate("Alice Chen"), _candidate("Bob Smith")]
        provenance = {c.name: _provenance(c.name) for c in candidates}

        flag_alice_valid = _valid_personality_flag(candidate_name="Alice Chen")
        flag_alice_bad = Flag(
            name="HALLUCINATED_FLAG",
            candidate_name="Alice Chen",
            category=FlagCategory.EXECUTION,
            valence=Valence.POSITIVE,
            evidence_type=EvidenceType.SCORED_FLAG,
            big_five_source="C",
        )
        flag_bob_valid = _valid_cv_flag(
            candidate_name="Bob Smith",
            requirement_id="REQ-02",
        )
        flag_bob_bad = _valid_cv_flag(
            candidate_name="Bob Smith",
            requirement_id="REQ-99",  # non-existent
        )

        rubric_matrix = [
            RubricAssessment(
                requirement_id="REQ-01",
                candidate_name="Alice Chen",
                rubric_level=RubricLevel.MEETS,
                confidence=Confidence.HIGH,
            ),
            RubricAssessment(
                requirement_id="REQ-02",
                candidate_name="Bob Smith",
                rubric_level=RubricLevel.GAP,
                confidence=Confidence.MEDIUM,
            ),
        ]

        stage_d = StageDOutput(
            flags=[flag_alice_valid, flag_alice_bad, flag_bob_valid, flag_bob_bad],
            provenance_per_candidate=provenance,
            confirmed_requirements=reqs,
            candidate_data=candidates,
            rubric_matrix=rubric_matrix,
            scenario=_scenario(),
        )

        output, warnings = validate_stage_d_output(stage_d)
        assert len(output.flags) == 2
        assert output.flags[0].name == "EXECUTION_CONSCIENTIOUSNESS_FIT"
        assert output.flags[1].name == "CV_GAP"
        assert output.flags[1].candidate_name == "Bob Smith"
        assert len(warnings) == 2

    def test_all_invalid_results_in_empty_flags(self) -> None:
        flags = [
            Flag(
                name="UNKNOWN_A",
                candidate_name="Alice Chen",
                category=FlagCategory.EXECUTION,
                valence=Valence.POSITIVE,
                evidence_type=EvidenceType.SCORED_FLAG,
                big_five_source="C",
            ),
            Flag(
                name="UNKNOWN_B",
                candidate_name="Alice Chen",
                category=FlagCategory.STRATEGIC,
                valence=Valence.NEGATIVE,
                evidence_type=EvidenceType.SCORED_FLAG,
                big_five_source="O",
            ),
        ]
        output, warnings = validate_stage_d_output(_stage_d_output(flags=flags))
        assert output.flags == []
        assert len(warnings) == 2


# ---------------------------------------------------------------------------
# Test 13: Pass-through fields unchanged after validation
# ---------------------------------------------------------------------------


class TestPassThroughFieldsUnchanged:
    def test_requirements_unchanged(self) -> None:
        reqs = [_requirement("REQ-01"), _requirement("REQ-02")]
        stage_d = _stage_d_output(requirements=reqs)
        output, _ = validate_stage_d_output(stage_d)
        assert output.confirmed_requirements == reqs

    def test_candidate_data_unchanged(self) -> None:
        candidates = [_candidate("Alice Chen"), _candidate("Bob Smith")]
        stage_d = _stage_d_output(candidates=candidates)
        # Build provenance for both candidates
        stage_d = StageDOutput(
            flags=[],
            provenance_per_candidate={c.name: _provenance(c.name) for c in candidates},
            confirmed_requirements=[_requirement()],
            candidate_data=candidates,
            rubric_matrix=[
                RubricAssessment(
                    requirement_id="REQ-01",
                    candidate_name="Alice Chen",
                    rubric_level=RubricLevel.MEETS,
                    confidence=Confidence.HIGH,
                )
            ],
            scenario=_scenario(),
        )
        output, _ = validate_stage_d_output(stage_d)
        assert output.candidate_data == candidates

    def test_rubric_matrix_unchanged(self) -> None:
        rubric = [
            RubricAssessment(
                requirement_id="REQ-01",
                candidate_name="Alice Chen",
                rubric_level=RubricLevel.EXCEEDS,
                confidence=Confidence.HIGH,
                cv_citation="Led $2B transformation at GlobalCo",
            )
        ]
        stage_d = StageDOutput(
            flags=[],
            provenance_per_candidate={"Alice Chen": _provenance()},
            confirmed_requirements=[_requirement()],
            candidate_data=[_candidate()],
            rubric_matrix=rubric,
            scenario=_scenario(),
        )
        output, _ = validate_stage_d_output(stage_d)
        assert output.rubric_matrix == rubric

    def test_scenario_unchanged(self) -> None:
        scenario = ScenarioConfig(
            name=ScenarioName.TURNAROUND,
            category_weights={"EXECUTION": 1.5},
        )
        stage_d = StageDOutput(
            flags=[],
            provenance_per_candidate={"Alice Chen": _provenance()},
            confirmed_requirements=[_requirement()],
            candidate_data=[_candidate()],
            rubric_matrix=[
                RubricAssessment(
                    requirement_id="REQ-01",
                    candidate_name="Alice Chen",
                    rubric_level=RubricLevel.GAP,
                    confidence=Confidence.LOW,
                )
            ],
            scenario=scenario,
        )
        output, _ = validate_stage_d_output(stage_d)
        assert output.scenario == scenario

    def test_input_not_mutated(self) -> None:
        """validate_stage_d_output must not mutate the input object."""
        flag = Flag(
            name="UNKNOWN_FLAG",
            candidate_name="Alice Chen",
            category=FlagCategory.EXECUTION,
            valence=Valence.POSITIVE,
            evidence_type=EvidenceType.SCORED_FLAG,
            big_five_source="C",
        )
        stage_d = _stage_d_output(flags=[flag])
        original_flag_count = len(stage_d.flags)
        validate_stage_d_output(stage_d)
        assert len(stage_d.flags) == original_flag_count  # input unchanged
