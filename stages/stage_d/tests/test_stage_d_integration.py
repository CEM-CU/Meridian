"""D Integration Test — golden-path through D1 → D2 → D3 → D4 → D5 → D6.

Exercises the full Stage D pipeline: StageCOutput → StageDOutput.
Stage D is entirely deterministic (zero LLM calls), so no mocking is needed.

Why this test exists:
- Unit tests verify individual components in isolation.
- This integration test verifies the WIRING: that each stage's output is a valid
  input for the next, and that the final StageDOutput satisfies all cross-cutting
  contracts (provenance consistency, passthrough fidelity, mode gating).
"""

from __future__ import annotations

import pytest
from shared.models.candidates import BigFiveScores, CandidateData
from shared.models.flags import EvidenceType, Flag, FlagCategory, Valence
from shared.models.pipeline import AssessmentMode, StageCOutput, StageDOutput
from shared.models.requirements import Priority, Requirement, ScenarioPriority
from shared.models.rubric import Confidence, RubricAssessment, RubricLevel
from shared.models.scenarios import ScenarioConfig, ScenarioName
from stage_d.assessment_mode import determine_modes_batch
from stage_d.cv_flag_validation import validate_cv_flags
from stage_d.merge import merge_all_candidates
from stage_d.output_assembly import assemble_stage_d_output
from stage_d.personality_flags import derive_personality_flags
from stage_d.validation import validate_merged_flags

# ---------------------------------------------------------------------------
# Helper: StageCOutput factory
# ---------------------------------------------------------------------------

_DIGITAL_TRANSFORMATION_WEIGHTS: dict[str, float] = {
    "EXECUTION": 1.0,
    "STRATEGIC": 1.2,
    "COLLISION": 0.8,
    "COMPLEMENT": 0.9,
    "FRICTION": 1.0,
    "CULTURAL": 1.1,
    "DERAILMENT": 1.3,
    "DARK_SIDE": 1.2,
    "INTEGRATION": 1.1,
    "TENURE": 0.7,
    "GROUPTHINK": 0.8,
    "EXPERIENCE_STRENGTH": 1.0,
    "EXPERIENCE_GAP": 1.2,
    "EVIDENCE_QUALITY": 0.9,
    "ROUTING": 0.5,
}

_TURNAROUND_WEIGHTS: dict[str, float] = {
    "EXECUTION": 1.5,
    "STRATEGIC": 0.9,
    "COLLISION": 0.8,
    "COMPLEMENT": 0.7,
    "FRICTION": 1.3,
    "CULTURAL": 0.9,
    "DERAILMENT": 1.5,
    "DARK_SIDE": 1.4,
    "INTEGRATION": 1.0,
    "TENURE": 0.6,
    "GROUPTHINK": 0.7,
    "EXPERIENCE_STRENGTH": 1.3,
    "EXPERIENCE_GAP": 1.5,
    "EVIDENCE_QUALITY": 0.8,
    "ROUTING": 0.4,
}


def _scenario_priority(
    digital_transformation: Priority = Priority.MEDIUM,
    post_acquisition: Priority = Priority.MEDIUM,
    turnaround: Priority = Priority.MEDIUM,
    stabilization: Priority = Priority.MEDIUM,
    growth: Priority = Priority.MEDIUM,
) -> ScenarioPriority:
    """Build a ScenarioPriority with explicit per-scenario priorities."""
    return ScenarioPriority(
        digital_transformation=digital_transformation,
        post_acquisition=post_acquisition,
        turnaround=turnaround,
        stabilization=stabilization,
        growth=growth,
    )


def _build_requirements() -> list[Requirement]:
    """Build 10 requirements (8 CV-assessable, 2 behavioral).

    Priorities are intentionally varied across scenarios so that the
    scenario_switch test (test 5) can detect meaningful flag differences.
    """
    return [
        Requirement(
            requirement_id="REQ-01",
            text="12+ years progressive technology leadership in automotive or adjacent deep-tech",
            source_quote="12+ years of progressive technology leadership",
            assessable_from_cv=True,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.HIGH,
                turnaround=Priority.HIGH,
            ),
        ),
        Requirement(
            requirement_id="REQ-02",
            text="P&L accountability of USD 500M+ or equivalent",
            source_quote="managing a P&L of USD 500M+",
            assessable_from_cv=True,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.HIGH,
                turnaround=Priority.HIGH,
            ),
        ),
        Requirement(
            requirement_id="REQ-03",
            text="Led engineering organisations of 200+ across multiple geographies",
            source_quote="leading engineering organisations of 200+ people",
            assessable_from_cv=True,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.HIGH,
                turnaround=Priority.MEDIUM,
            ),
        ),
        Requirement(
            requirement_id="REQ-04",
            text="Deep technical fluency in EV powertrain architecture or SDV middleware",
            source_quote="Deep technical fluency in EV powertrain architecture or SDV middleware",
            assessable_from_cv=True,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.HIGH,
                turnaround=Priority.MEDIUM,
            ),
        ),
        Requirement(
            requirement_id="REQ-05",
            text="Track record of successful post-acquisition technology integration",
            source_quote="Track record of successful post-acquisition technology integration",
            assessable_from_cv=True,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.MEDIUM,
                turnaround=Priority.HIGH,
            ),
        ),
        Requirement(
            requirement_id="REQ-06",
            text="Experience in premium automotive or tier-1 supplier environments",
            source_quote="Experience operating in premium automotive environments",
            assessable_from_cv=True,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.MEDIUM,
                turnaround=Priority.HIGH,
            ),
        ),
        Requirement(
            requirement_id="REQ-07",
            text="Direct technology delivery accountability in EMEA and APAC markets",
            source_quote="Direct accountability for technology delivery in EMEA and APAC",
            assessable_from_cv=True,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.MEDIUM,
                turnaround=Priority.LOW,
            ),
        ),
        Requirement(
            requirement_id="REQ-08",
            text="MBA, MS, or PhD in engineering or computer science",
            source_quote="MBA, MS, or PhD in engineering or computer science",
            assessable_from_cv=True,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.LOW,
                turnaround=Priority.LOW,
            ),
        ),
        # REQ-09 and REQ-10 are behavioral (not CV-assessable).
        Requirement(
            requirement_id="REQ-09",
            text="Ability to navigate complex stakeholder landscapes",
            source_quote="Proven ability to navigate complex stakeholder landscapes",
            assessable_from_cv=False,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.HIGH,
                turnaround=Priority.HIGH,
            ),
        ),
        Requirement(
            requirement_id="REQ-10",
            text="Comfort operating in consensus-driven corporate culture",
            source_quote="Comfort operating in a consensus-driven corporate culture",
            assessable_from_cv=False,
            scenario_priority=_scenario_priority(
                digital_transformation=Priority.HIGH,
                turnaround=Priority.HIGH,
            ),
        ),
    ]


def _build_candidates() -> tuple[CandidateData, CandidateData, CandidateData]:
    """Build 3 candidates: two full-mode (Big Five present), one partial (no Big Five).

    Returns:
        Tuple of (alpha, beta, gamma) where gamma has no Big Five scores.
    """
    # Candidate Alpha — high O, high C, moderate E: fires STRATEGIC_OPENNESS_FIT and
    # EXECUTION_CONSCIENTIOUSNESS_FIT for digital_transformation scenario.
    alpha = CandidateData(
        name="Alpha Candidate",
        cv_text=(
            "CTO, TechAlpha Inc. (2015-Present)\n"
            "- Led 350-person engineering org across 4 geographies, USD 600M P&L.\n"
            "- Architected digital transformation spanning 12 BUs.\n"
            "- PhD Computer Science — MIT (2010)."
        ),
        big_five=BigFiveScores(
            O=0.80,  # above 0.70 → STRATEGIC_OPENNESS_FIT fires for digital_transformation
            C=0.75,  # above 0.65 → EXECUTION_CONSCIENTIOUSNESS_FIT fires
            E=0.65,  # above 0.60 → CULTURAL_EXTRAVERSION_FIT fires
            A=0.50,  # above 0.25 → DARK_SIDE_LOW_AGREEABLENESS does NOT fire
            N=0.30,  # below 0.65 → DERAILMENT_NEUROTICISM_UNDER_STRESS does NOT fire
        ),
        personality_source="manual",
    )

    # Candidate Beta — high C, moderate O, high N: fires DERAILMENT_NEUROTICISM_UNDER_STRESS
    # and EXECUTION_CONSCIENTIOUSNESS_FIT. Different profile from Alpha.
    beta = CandidateData(
        name="Beta Candidate",
        cv_text=(
            "SVP Technology, BetaCorp (2017-Present)\n"
            "- Led 220-person engineering organisation, EUR 480M P&L.\n"
            "- Drove enterprise digital transformation across EMEA and LatAm.\n"
            "- MBA INSEAD (2007), MEng Loughborough (2002)."
        ),
        big_five=BigFiveScores(
            O=0.60,  # below 0.70 → STRATEGIC_OPENNESS_FIT does NOT fire for digital_transformation
            C=0.85,  # above 0.65 → EXECUTION_CONSCIENTIOUSNESS_FIT fires
            E=0.55,  # below 0.60 → CULTURAL_EXTRAVERSION_FIT does NOT fire
            A=0.68,  # above 0.25 → DARK_SIDE_LOW_AGREEABLENESS does NOT fire
            N=0.70,  # above 0.65 → DERAILMENT_NEUROTICISM_UNDER_STRESS fires
        ),
        personality_source="manual",
    )

    # Candidate Gamma — no Big Five (partial mode). Zero personality flags expected.
    gamma = CandidateData(
        name="Gamma Candidate",
        cv_text=(
            "CTO, Gamma Motors (2020-Present)\n"
            "- Led 90-person engineering team, EUR 95M division revenue.\n"
            "- Built AUTOSAR Adaptive middleware for European OEMs.\n"
            "- MS Computer Science — University of Tokyo (2010)."
        ),
        big_five=None,
        personality_source=None,
    )

    return alpha, beta, gamma


def _build_rubric_assessments(
    candidates: list[CandidateData],
    requirements: list[Requirement],
) -> list[RubricAssessment]:
    """Build rubric assessments for all candidates x 8 CV-assessable requirements.

    Assessment design:
    - Alpha: meets/exceeds everything (no CV flags expected except CV_PARTIAL for REQ-07)
    - Beta: meets most, gap on REQ-06 (automotive), partial on REQ-07
    - Gamma: meets most, gap on REQ-02 (P&L scope) and REQ-03 (org size)

    We deliberately set some GAP and PARTIAL levels so D2/D4 have real CV flags to
    process, and to verify consistency checks in D4.
    """
    cv_assessable_ids = [r.requirement_id for r in requirements if r.assessable_from_cv]

    # Profile matrix: (candidate_name, req_id) → (level, confidence, citation, note)
    _profiles: dict[tuple[str, str], tuple[RubricLevel, Confidence, str | None, str | None]] = {
        # Alpha: strong all-round
        ("Alpha Candidate", "REQ-01"): (RubricLevel.MEETS, Confidence.HIGH, "15+ years tech leadership", None),
        ("Alpha Candidate", "REQ-02"): (RubricLevel.EXCEEDS, Confidence.HIGH, "USD 600M P&L at TechAlpha", None),
        ("Alpha Candidate", "REQ-03"): (RubricLevel.EXCEEDS, Confidence.HIGH, "350-person org across 4 geos", None),
        ("Alpha Candidate", "REQ-04"): (RubricLevel.MEETS, Confidence.HIGH, "Digital platform architecture", None),
        ("Alpha Candidate", "REQ-05"): (RubricLevel.MEETS, Confidence.MEDIUM, "2 acquisitions integrated", None),
        ("Alpha Candidate", "REQ-06"): (RubricLevel.GAP, Confidence.HIGH, None, "No automotive OEM exposure"),
        ("Alpha Candidate", "REQ-07"): (RubricLevel.PARTIAL, Confidence.MEDIUM, "EMEA only, no APAC", None),
        ("Alpha Candidate", "REQ-08"): (RubricLevel.EXCEEDS, Confidence.HIGH, "PhD CS MIT 2010", None),
        # Beta: meets most, gap on automotive industry
        ("Beta Candidate", "REQ-01"): (RubricLevel.EXCEEDS, Confidence.HIGH, "18+ years automotive leadership", None),
        ("Beta Candidate", "REQ-02"): (RubricLevel.MEETS, Confidence.HIGH, "EUR 480M P&L at BetaCorp", None),
        ("Beta Candidate", "REQ-03"): (RubricLevel.MEETS, Confidence.HIGH, "220-person org EMEA + LatAm", None),
        ("Beta Candidate", "REQ-04"): (
            RubricLevel.PARTIAL,
            Confidence.MEDIUM,
            "Legacy automotive, limited EV/SDV",
            None,
        ),
        ("Beta Candidate", "REQ-05"): (RubricLevel.EXCEEDS, Confidence.HIGH, "PSA-FCA merger integration", None),
        ("Beta Candidate", "REQ-06"): (RubricLevel.EXCEEDS, Confidence.HIGH, "Stellantis, Continental, JLR", None),
        ("Beta Candidate", "REQ-07"): (
            RubricLevel.PARTIAL,
            Confidence.MEDIUM,
            "EMEA extensive, APAC limited",
            None,
        ),
        ("Beta Candidate", "REQ-08"): (RubricLevel.EXCEEDS, Confidence.HIGH, "MBA INSEAD, MEng Loughborough", None),
        # Gamma: balanced, scope gaps
        ("Gamma Candidate", "REQ-01"): (RubricLevel.MEETS, Confidence.HIGH, "15+ years automotive tech", None),
        ("Gamma Candidate", "REQ-02"): (RubricLevel.GAP, Confidence.HIGH, None, "EUR 95M — well below USD 500M"),
        ("Gamma Candidate", "REQ-03"): (RubricLevel.GAP, Confidence.HIGH, None, "85-person team, below 200+"),
        ("Gamma Candidate", "REQ-04"): (RubricLevel.MEETS, Confidence.HIGH, "AUTOSAR Adaptive, EV BMS", None),
        ("Gamma Candidate", "REQ-05"): (
            RubricLevel.PARTIAL,
            Confidence.LOW,
            "No direct M&A integration",
            "Has Gamma been involved in M&A not on CV?",
        ),
        ("Gamma Candidate", "REQ-06"): (RubricLevel.MEETS, Confidence.HIGH, "Toyota, Honda, BMW supply", None),
        ("Gamma Candidate", "REQ-07"): (
            RubricLevel.MEETS,
            Confidence.MEDIUM,
            "Tokyo + Munich presence",
            None,
        ),
        ("Gamma Candidate", "REQ-08"): (RubricLevel.MEETS, Confidence.HIGH, "MS CS University of Tokyo", None),
    }

    assessments: list[RubricAssessment] = []
    for candidate in candidates:
        for req_id in cv_assessable_ids:
            key = (candidate.name, req_id)
            level, conf, citation, note = _profiles[key]
            assessments.append(
                RubricAssessment(
                    requirement_id=req_id,
                    candidate_name=candidate.name,
                    rubric_level=level,
                    confidence=conf,
                    cv_citation=citation,
                    cv_location=f"{candidate.name} CV — {req_id}",
                    notes=note if level == RubricLevel.GAP else None,
                    investigation_question=(note if level in {RubricLevel.PARTIAL, RubricLevel.GAP} and note else None),
                )
            )

    return assessments


def _build_cv_flags(
    candidates: list[CandidateData],
    requirements: list[Requirement],
    rubric_assessments: list[RubricAssessment],
    scenario_name: ScenarioName,
) -> dict[str, list[Flag]]:
    """Build CV flags derived from rubric assessments, matching D2 validation rules.

    Each GAP assessment produces a CV_GAP flag; each PARTIAL a CV_PARTIAL flag;
    each EXCEEDS produces a CV_EXCEEDS flag. MEETS levels produce no flags (by design).

    Flags are constructed to be valid for D2 validation: correct names, evidence
    types, and active_priority metadata matching the requirement's scenario_priority.
    """
    # Index rubric assessments by (requirement_id, candidate_name) for fast lookup.
    rubric_index: dict[tuple[str, str], RubricAssessment] = {
        (a.requirement_id, a.candidate_name): a for a in rubric_assessments
    }
    # Map rubric level → (flag name, evidence type, valence, flag category)
    _level_to_flag: dict[RubricLevel, tuple[str, EvidenceType, Valence, FlagCategory]] = {
        RubricLevel.GAP: (
            "CV_GAP",
            EvidenceType.REQUIREMENT_GAP,
            Valence.NEGATIVE,
            FlagCategory.EXPERIENCE_GAP,
        ),
        RubricLevel.PARTIAL: (
            "CV_PARTIAL",
            EvidenceType.CV_RUBRIC,
            Valence.NEGATIVE,
            FlagCategory.EXPERIENCE_GAP,
        ),
        RubricLevel.EXCEEDS: (
            "CV_EXCEEDS",
            EvidenceType.CV_RUBRIC,
            Valence.POSITIVE,
            FlagCategory.EXPERIENCE_STRENGTH,
        ),
    }

    cv_flags_per_candidate: dict[str, list[Flag]] = {c.name: [] for c in candidates}
    cv_reqs = [r for r in requirements if r.assessable_from_cv]

    for candidate in candidates:
        for req in cv_reqs:
            assessment = rubric_index.get((req.requirement_id, candidate.name))
            if assessment is None:
                continue

            level = assessment.rubric_level
            if level not in _level_to_flag:
                # MEETS and NOT_ASSESSABLE produce no flags.
                continue

            flag_name, evidence_type, valence, category = _level_to_flag[level]
            active_priority = req.scenario_priority.for_scenario(scenario_name.value)

            cv_flags_per_candidate[candidate.name].append(
                Flag(
                    name=flag_name,
                    candidate_name=candidate.name,
                    category=category,
                    valence=valence,
                    evidence_type=evidence_type,
                    rubric_level=level.value,
                    requirement_id=req.requirement_id,
                    cv_citation=assessment.cv_citation,
                    cv_location=assessment.cv_location,
                    confidence=assessment.confidence.value,
                    notes=assessment.notes,
                    investigation_question=assessment.investigation_question,
                    topic_keywords=["cv", "rubric", req.requirement_id.lower()],
                    metadata={"active_priority": active_priority.value},
                )
            )

    return cv_flags_per_candidate


def _build_stage_c_output(
    scenario_name: ScenarioName = ScenarioName.DIGITAL_TRANSFORMATION,
    category_weights: dict[str, float] | None = None,
) -> StageCOutput:
    """Construct a complete StageCOutput with realistic data.

    Builds 3 candidates (2 full-mode, 1 partial), 10 requirements (8 CV-assessable,
    2 behavioral), and rubric assessments for all candidates x CV-assessable reqs.

    Args:
        scenario_name: Active scenario for this StageCOutput.
        category_weights: Category weights for the ScenarioConfig. Defaults to
            digital_transformation weights.

    Returns:
        A valid StageCOutput ready for the Stage D pipeline.
    """
    if category_weights is None:
        category_weights = _DIGITAL_TRANSFORMATION_WEIGHTS

    alpha, beta, gamma = _build_candidates()
    candidates = [alpha, beta, gamma]
    requirements = _build_requirements()

    scenario = ScenarioConfig(
        name=scenario_name,
        category_weights=category_weights,
    )

    rubric_assessments = _build_rubric_assessments(candidates, requirements)

    return StageCOutput(
        requirements=requirements,
        rubric_assessments=rubric_assessments,
        candidate_data=candidates,
        scenario=scenario,
    )


# ---------------------------------------------------------------------------
# Pipeline runner helper
# ---------------------------------------------------------------------------


def _run_stage_d_pipeline(stage_c_output: StageCOutput) -> StageDOutput:
    """Run the full Stage D pipeline D1 → D2 → D3 → D4 → D5 → D6.

    This mirrors what the Stage D orchestrator will call in production.
    All steps are deterministic and produce no side effects.

    Args:
        stage_c_output: The complete Stage C output.

    Returns:
        The assembled StageDOutput.
    """
    candidates = stage_c_output.candidate_data
    requirements = stage_c_output.requirements
    rubric_assessments = stage_c_output.rubric_assessments
    scenario = stage_c_output.scenario

    # D1: Personality flag derivation (per candidate).
    personality_flags_per_candidate: dict[str, list[Flag]] = {
        c.name: derive_personality_flags(c, scenario) for c in candidates
    }

    # Build raw CV flags from rubric assessments (this is what C4 bridge produces).
    raw_cv_flags_per_candidate = _build_cv_flags(candidates, requirements, rubric_assessments, scenario.name)

    # D2: CV flag stream validation (per candidate).
    validated_cv_flags_per_candidate: dict[str, list[Flag]] = {}
    for candidate in candidates:
        valid_flags, _warnings = validate_cv_flags(
            raw_cv_flags_per_candidate[candidate.name],
            requirements,
            scenario.name,
        )
        validated_cv_flags_per_candidate[candidate.name] = valid_flags

    # D3: Merge personality + CV flags (per candidate, deterministic ordering).
    merged_flags_per_candidate = merge_all_candidates(
        personality_flags_per_candidate,
        validated_cv_flags_per_candidate,
    )

    # D5: Assessment mode determination (must happen before D4 coverage check).
    modes_per_candidate = determine_modes_batch(candidates)
    mode_strings: dict[str, str] = {name: mode.value for name, (mode, _prov) in modes_per_candidate.items()}

    # D4: Validation (5 checks). May remove flags for checks 1-2; advisories for 3-5.
    validated_flags_per_candidate, validation_warnings, coherence_notes = validate_merged_flags(
        merged_flags_per_candidate,
        rubric_assessments,
        requirements,
        mode_strings,
    )

    # D6: Output assembly.
    return assemble_stage_d_output(
        validated_flags_per_candidate=validated_flags_per_candidate,
        modes_per_candidate=modes_per_candidate,
        stage_c_output=stage_c_output,
        validation_warnings=validation_warnings,
        coherence_notes=coherence_notes,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFullD1ThroughD6Pipeline:
    """Test 1: Verify full pipeline produces a valid StageDOutput with expected structure."""

    @pytest.fixture()
    def stage_d_output(self) -> StageDOutput:
        """Run the full pipeline and return the output. Used across multiple assertions."""
        stage_c_output = _build_stage_c_output()
        return _run_stage_d_pipeline(stage_c_output)

    def test_output_is_valid_stage_d_output(self, stage_d_output: StageDOutput) -> None:
        """StageDOutput must be a valid Pydantic model with no missing required fields."""
        assert isinstance(stage_d_output, StageDOutput)

    def test_flags_list_is_non_empty(self, stage_d_output: StageDOutput) -> None:
        """Full pipeline with 3 candidates should produce at least 1 flag total."""
        assert len(stage_d_output.flags) > 0

    def test_provenance_has_all_three_candidates(self, stage_d_output: StageDOutput) -> None:
        """provenance_per_candidate must contain entries for all 3 candidates."""
        expected_names = {"Alpha Candidate", "Beta Candidate", "Gamma Candidate"}
        assert set(stage_d_output.provenance_per_candidate.keys()) == expected_names

    def test_full_mode_candidates_have_personality_flags(self, stage_d_output: StageDOutput) -> None:
        """Alpha and Beta have Big Five — their personality_flag_count must be > 0."""
        alpha_prov = stage_d_output.provenance_per_candidate["Alpha Candidate"]
        beta_prov = stage_d_output.provenance_per_candidate["Beta Candidate"]
        assert alpha_prov.personality_flag_count > 0, "Alpha should have personality flags"
        assert beta_prov.personality_flag_count > 0, "Beta should have personality flags"

    def test_partial_mode_candidate_has_zero_personality_flags(self, stage_d_output: StageDOutput) -> None:
        """Gamma has no Big Five — personality_flag_count must be 0."""
        gamma_prov = stage_d_output.provenance_per_candidate["Gamma Candidate"]
        assert gamma_prov.personality_flag_count == 0

    def test_confirmed_requirements_matches_input(self, stage_d_output: StageDOutput) -> None:
        """Passthrough: confirmed_requirements must match the 10-requirement input."""
        assert len(stage_d_output.confirmed_requirements) == 10
        output_ids = {r.requirement_id for r in stage_d_output.confirmed_requirements}
        expected_ids = {f"REQ-{i:02d}" for i in range(1, 11)}
        assert output_ids == expected_ids

    def test_candidate_data_matches_input(self, stage_d_output: StageDOutput) -> None:
        """Passthrough: candidate_data must preserve all 3 candidates."""
        output_names = {c.name for c in stage_d_output.candidate_data}
        assert output_names == {"Alpha Candidate", "Beta Candidate", "Gamma Candidate"}

    def test_rubric_matrix_matches_input(self, stage_d_output: StageDOutput) -> None:
        """Passthrough: rubric_matrix must contain assessments for 3 candidates x 8 CV reqs = 24."""
        assert len(stage_d_output.rubric_matrix) == 24  # 3 candidates x 8 CV-assessable reqs

    def test_scenario_matches_input(self, stage_d_output: StageDOutput) -> None:
        """Passthrough: scenario must be digital_transformation."""
        assert stage_d_output.scenario.name == ScenarioName.DIGITAL_TRANSFORMATION


class TestStageDOutputRoundTrip:
    """Test 2: StageDOutput survives a Pydantic round-trip (serialize → deserialize)."""

    def test_round_trip_succeeds(self) -> None:
        """model_dump + model_validate must produce an identical model without errors."""
        stage_c_output = _build_stage_c_output()
        original = _run_stage_d_pipeline(stage_c_output)

        serialized = original.model_dump()
        restored = StageDOutput.model_validate(serialized)

        # Spot-check key fields after round-trip.
        assert len(restored.flags) == len(original.flags)
        assert set(restored.provenance_per_candidate.keys()) == set(original.provenance_per_candidate.keys())
        assert len(restored.confirmed_requirements) == len(original.confirmed_requirements)
        assert restored.scenario.name == original.scenario.name


class TestProvenanceCountsConsistent:
    """Test 3: personality_flag_count + cv_flag_count == total_flags, and total_flags
    matches the actual number of flags for that candidate in the flat flags list."""

    def test_provenance_sums_are_consistent(self) -> None:
        """For every candidate, personality + cv == total, and total matches the flat list."""
        stage_c_output = _build_stage_c_output()
        output = _run_stage_d_pipeline(stage_c_output)

        # Build ground-truth count from the flat flags list.
        actual_counts: dict[str, int] = {}
        for flag in output.flags:
            actual_counts[flag.candidate_name] = actual_counts.get(flag.candidate_name, 0) + 1

        for candidate_name, provenance in output.provenance_per_candidate.items():
            with pytest.MonkeyPatch.context() as _m:
                # Arithmetic consistency: personality + cv == total_flags in provenance.
                assert provenance.personality_flag_count + provenance.cv_flag_count == provenance.total_flags, (
                    f"{candidate_name}: personality({provenance.personality_flag_count}) + "
                    f"cv({provenance.cv_flag_count}) != total({provenance.total_flags})"
                )

                # Cross-check: total_flags in provenance == actual flag count in flat list.
                expected_total = actual_counts.get(candidate_name, 0)
                assert provenance.total_flags == expected_total, (
                    f"{candidate_name}: provenance.total_flags={provenance.total_flags} "
                    f"but flat list has {expected_total} flags"
                )


class TestPartialModeNoPersonalityClaims:
    """Test 4: Partial mode candidate must have no personality data in the output."""

    def test_gamma_is_partial_mode(self) -> None:
        """Gamma (no Big Five) must have assessment_mode == PARTIAL."""
        stage_c_output = _build_stage_c_output()
        output = _run_stage_d_pipeline(stage_c_output)

        gamma_prov = output.provenance_per_candidate["Gamma Candidate"]
        assert gamma_prov.assessment_mode == AssessmentMode.PARTIAL

    def test_gamma_has_zero_personality_flag_count(self) -> None:
        """Gamma must have personality_flag_count == 0."""
        stage_c_output = _build_stage_c_output()
        output = _run_stage_d_pipeline(stage_c_output)

        gamma_prov = output.provenance_per_candidate["Gamma Candidate"]
        assert gamma_prov.personality_flag_count == 0

    def test_gamma_big_five_available_is_false(self) -> None:
        """Gamma must have big_five_available == False."""
        stage_c_output = _build_stage_c_output()
        output = _run_stage_d_pipeline(stage_c_output)

        gamma_prov = output.provenance_per_candidate["Gamma Candidate"]
        assert gamma_prov.big_five_available is False

    def test_gamma_has_no_personality_flags_in_flat_list(self) -> None:
        """No SCORED_FLAG evidence_type flags should exist for Gamma in the flat list."""
        stage_c_output = _build_stage_c_output()
        output = _run_stage_d_pipeline(stage_c_output)

        gamma_personality_flags = [
            f
            for f in output.flags
            if f.candidate_name == "Gamma Candidate" and f.evidence_type == EvidenceType.SCORED_FLAG
        ]
        assert gamma_personality_flags == []

    def test_full_mode_candidates_have_big_five_available_true(self) -> None:
        """Alpha and Beta must have big_five_available == True."""
        stage_c_output = _build_stage_c_output()
        output = _run_stage_d_pipeline(stage_c_output)

        alpha_prov = output.provenance_per_candidate["Alpha Candidate"]
        beta_prov = output.provenance_per_candidate["Beta Candidate"]
        assert alpha_prov.big_five_available is True
        assert beta_prov.big_five_available is True


class TestScenarioSwitchChangesOutput:
    """Test 5: Different scenarios produce different flags due to different thresholds
    and active_priority values.

    The digital_transformation scenario has higher openness and extraversion thresholds,
    and different requirement priority weighting compared to turnaround. This means
    different personality flags fire and CV flags carry different active_priority metadata,
    resulting in measurably different StageDOutput.
    """

    def test_different_scenarios_yield_different_flag_sets(self) -> None:
        """Running the same candidates under digital_transformation vs turnaround must
        produce different flag collections."""
        digital_c_output = _build_stage_c_output(
            scenario_name=ScenarioName.DIGITAL_TRANSFORMATION,
            category_weights=_DIGITAL_TRANSFORMATION_WEIGHTS,
        )
        turnaround_c_output = _build_stage_c_output(
            scenario_name=ScenarioName.TURNAROUND,
            category_weights=_TURNAROUND_WEIGHTS,
        )

        digital_output = _run_stage_d_pipeline(digital_c_output)
        turnaround_output = _run_stage_d_pipeline(turnaround_c_output)

        # Collect (name, candidate_name) pairs from each output.
        digital_flag_ids = {(f.name, f.candidate_name) for f in digital_output.flags}
        turnaround_flag_ids = {(f.name, f.candidate_name) for f in turnaround_output.flags}

        assert digital_flag_ids != turnaround_flag_ids, (
            "Expected different flag sets for digital_transformation vs turnaround "
            "but got identical sets — scenario switching has no effect."
        )

    def test_scenario_name_is_preserved_in_output(self) -> None:
        """The scenario name in StageDOutput must match the input StageCOutput scenario."""
        for scenario_name, weights in [
            (ScenarioName.DIGITAL_TRANSFORMATION, _DIGITAL_TRANSFORMATION_WEIGHTS),
            (ScenarioName.TURNAROUND, _TURNAROUND_WEIGHTS),
        ]:
            stage_c_output = _build_stage_c_output(
                scenario_name=scenario_name,
                category_weights=weights,
            )
            output = _run_stage_d_pipeline(stage_c_output)
            assert output.scenario.name == scenario_name


class TestNoValidationErrorsOnCleanInput:
    """Test 6: Well-formed StageCOutput should pass D4 without any flags being removed
    by the consistency or mutual exclusivity checks.

    The test data is carefully constructed so:
    - Every personality flag has a score on the correct side of its threshold.
    - Every CV flag references a requirement with a matching rubric_level.
    - No contradicting flag pairs exist for the same candidate.

    This means D4 Check 1 and Check 2 should remove zero flags.
    """

    def test_no_flags_stripped_by_consistency_check(self) -> None:
        """D4 Check 1 must not remove any personality or CV flags from clean input."""
        from stage_d.validation import check_flag_score_consistency

        stage_c_output = _build_stage_c_output()
        candidates = stage_c_output.candidate_data
        requirements = stage_c_output.requirements
        rubric_assessments = stage_c_output.rubric_assessments
        scenario = stage_c_output.scenario

        # Build flags through D1-D3 without validation.
        personality_flags_per_candidate: dict[str, list[Flag]] = {
            c.name: derive_personality_flags(c, scenario) for c in candidates
        }
        raw_cv_flags = _build_cv_flags(candidates, requirements, rubric_assessments, scenario.name)
        validated_cv: dict[str, list[Flag]] = {}
        for candidate in candidates:
            valid_flags, _w = validate_cv_flags(raw_cv_flags[candidate.name], requirements, scenario.name)
            validated_cv[candidate.name] = valid_flags

        merged = merge_all_candidates(personality_flags_per_candidate, validated_cv)

        # Run Check 1 on each candidate's merged flags.
        for candidate_name, flags in merged.items():
            validated, warnings = check_flag_score_consistency(flags, rubric_assessments)
            stripped_count = len(flags) - len(validated)
            assert stripped_count == 0, (
                f"D4 Check 1 stripped {stripped_count} flag(s) for '{candidate_name}': {warnings}"
            )

    def test_no_flags_stripped_by_mutual_exclusivity_check(self) -> None:
        """D4 Check 2 must not remove any flags because no contradicting pairs exist."""
        from stage_d.validation import check_mutual_exclusivity

        stage_c_output = _build_stage_c_output()
        candidates = stage_c_output.candidate_data
        requirements = stage_c_output.requirements
        rubric_assessments = stage_c_output.rubric_assessments
        scenario = stage_c_output.scenario

        personality_flags_per_candidate: dict[str, list[Flag]] = {
            c.name: derive_personality_flags(c, scenario) for c in candidates
        }
        raw_cv_flags = _build_cv_flags(candidates, requirements, rubric_assessments, scenario.name)
        validated_cv: dict[str, list[Flag]] = {}
        for candidate in candidates:
            valid_flags, _w = validate_cv_flags(raw_cv_flags[candidate.name], requirements, scenario.name)
            validated_cv[candidate.name] = valid_flags

        merged = merge_all_candidates(personality_flags_per_candidate, validated_cv)

        for candidate_name, flags in merged.items():
            validated, warnings = check_mutual_exclusivity(flags)
            stripped_count = len(flags) - len(validated)
            assert stripped_count == 0, (
                f"D4 Check 2 stripped {stripped_count} flag(s) for '{candidate_name}': {warnings}"
            )

    def test_full_pipeline_flag_count_is_in_expected_range(self) -> None:
        """Each full-mode candidate should produce 3-25 flags (D4 Check 5 advisory bounds)."""
        stage_c_output = _build_stage_c_output()
        output = _run_stage_d_pipeline(stage_c_output)

        for candidate_name, provenance in output.provenance_per_candidate.items():
            if provenance.assessment_mode == AssessmentMode.PARTIAL:
                # Partial mode: only CV flags, fewer total expected — just check non-negative.
                assert provenance.total_flags >= 0
                continue
            # Full mode: expect at least 3 flags (Check 5 low watermark).
            assert provenance.total_flags >= 3, (
                f"'{candidate_name}' has only {provenance.total_flags} flag(s) — assessment data is unexpectedly thin."
            )
            assert provenance.total_flags <= 25, (
                f"'{candidate_name}' has {provenance.total_flags} flags — exceeds noisy threshold."
            )
