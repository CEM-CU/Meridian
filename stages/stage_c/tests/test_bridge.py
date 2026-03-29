"""Tests for C4 rubric-to-flag bridge.

Covers every mapping rule, pattern-level detectors, topic keyword generation,
and property-based invariants.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from shared.models import (
    Confidence,
    EvidenceType,
    FlagCategory,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioName,
    ScenarioPriority,
    Valence,
)
from stage_c.bridge import _extract_topic_keywords, bridge_rubric_to_flags

# ---------------------------------------------------------------------------
# Test fixtures / helpers
# ---------------------------------------------------------------------------

_DEFAULT_SCENARIO = ScenarioName.DIGITAL_TRANSFORMATION


def _make_scenario_priority(
    target_scenario: ScenarioName = _DEFAULT_SCENARIO,
    target_priority: Priority = Priority.HIGH,
    default_priority: Priority = Priority.MEDIUM,
) -> ScenarioPriority:
    """Build a ScenarioPriority where `target_scenario` has `target_priority`."""
    mapping = {s.value: default_priority for s in ScenarioName}
    mapping[target_scenario.value] = target_priority
    return ScenarioPriority(**mapping)


def _make_requirement(
    req_id: str = "REQ-01",
    text: str = "P&L responsibility exceeding $500M",
    assessable_from_cv: bool = True,
    scenario: ScenarioName = _DEFAULT_SCENARIO,
    priority: Priority = Priority.HIGH,
) -> Requirement:
    return Requirement(
        requirement_id=req_id,
        text=text,
        source_quote="Direct from JD",
        assessable_from_cv=assessable_from_cv,
        scenario_priority=_make_scenario_priority(scenario, priority),
    )


def _make_assessment(
    req_id: str = "REQ-01",
    candidate: str = "Alice",
    level: RubricLevel = RubricLevel.GAP,
    confidence: Confidence = Confidence.HIGH,
    citation: str | None = "Led P&L of $200M at Acme Corp",
    notes: str | None = None,
    investigation_question: str | None = "What was the full P&L scope?",
) -> RubricAssessment:
    return RubricAssessment(
        requirement_id=req_id,
        candidate_name=candidate,
        rubric_level=level,
        confidence=confidence,
        cv_citation=citation,
        notes=notes,
        investigation_question=investigation_question,
    )


# ---------------------------------------------------------------------------
# Individual mapping rule tests
# ---------------------------------------------------------------------------


class TestGapHighPriority:
    """GAP on high-priority -> CV_GAP with priority=high."""

    def test_produces_cv_gap_flag(self) -> None:
        reqs = [
            _make_requirement(req_id="REQ-01", priority=Priority.HIGH),
            _make_requirement(req_id="REQ-02", priority=Priority.HIGH, text="Team leadership skills"),
        ]
        assessments = [
            _make_assessment(req_id="REQ-01", level=RubricLevel.GAP),
            _make_assessment(req_id="REQ-02", level=RubricLevel.MEETS),
        ]
        flags = bridge_rubric_to_flags(assessments, reqs, _DEFAULT_SCENARIO)

        gap_flags = [f for f in flags if f.name == "CV_GAP"]
        assert len(gap_flags) == 1
        flag = gap_flags[0]
        assert flag.name == "CV_GAP"
        assert flag.category == FlagCategory.EXPERIENCE_GAP
        assert flag.valence == Valence.NEGATIVE
        assert flag.evidence_type == EvidenceType.REQUIREMENT_GAP
        assert flag.metadata["active_priority"] == "high"

    def test_carries_provenance(self) -> None:
        req = _make_requirement()
        assessment = _make_assessment(
            level=RubricLevel.GAP,
            citation="Managed $200M budget",
            notes="Below threshold",
            investigation_question="Full scope?",
        )
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)
        flag = flags[0]

        assert flag.requirement_id == "REQ-01"
        assert flag.rubric_level == "gap"
        assert flag.cv_citation == "Managed $200M budget"
        assert flag.confidence == "high"
        assert flag.notes == "Below threshold"
        assert flag.investigation_question == "Full scope?"
        assert flag.metadata["requirement_text"] == req.text


class TestGapMediumPriority:
    """GAP on medium-priority -> CV_GAP with priority=medium."""

    def test_produces_cv_gap_medium(self) -> None:
        req = _make_requirement(priority=Priority.MEDIUM)
        assessment = _make_assessment(level=RubricLevel.GAP)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)

        assert len(flags) == 1
        assert flags[0].name == "CV_GAP"
        assert flags[0].metadata["active_priority"] == "medium"


class TestGapLowPriority:
    """GAP on low-priority -> NO FLAG."""

    def test_no_flag(self) -> None:
        req = _make_requirement(priority=Priority.LOW)
        assessment = _make_assessment(level=RubricLevel.GAP)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)
        assert len(flags) == 0


class TestPartialHighPriority:
    """PARTIAL on high-priority -> CV_PARTIAL."""

    def test_produces_cv_partial(self) -> None:
        req = _make_requirement(priority=Priority.HIGH)
        assessment = _make_assessment(level=RubricLevel.PARTIAL)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)

        assert len(flags) == 1
        flag = flags[0]
        assert flag.name == "CV_PARTIAL"
        assert flag.category == FlagCategory.EXPERIENCE_GAP
        assert flag.valence == Valence.NEGATIVE
        assert flag.evidence_type == EvidenceType.CV_RUBRIC
        assert flag.metadata["active_priority"] == "high"


class TestPartialMediumAndLow:
    """PARTIAL on medium/low-priority -> NO FLAG."""

    @pytest.mark.parametrize("priority", [Priority.MEDIUM, Priority.LOW])
    def test_no_flag(self, priority: Priority) -> None:
        req = _make_requirement(priority=priority)
        assessment = _make_assessment(level=RubricLevel.PARTIAL)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)
        assert len(flags) == 0


class TestExceedsHighPriority:
    """EXCEEDS on high-priority -> CV_EXCEEDS."""

    def test_produces_cv_exceeds(self) -> None:
        req = _make_requirement(priority=Priority.HIGH)
        assessment = _make_assessment(level=RubricLevel.EXCEEDS)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)

        assert len(flags) == 1
        flag = flags[0]
        assert flag.name == "CV_EXCEEDS"
        assert flag.category == FlagCategory.EXPERIENCE_STRENGTH
        assert flag.valence == Valence.POSITIVE
        assert flag.evidence_type == EvidenceType.CV_RUBRIC
        assert flag.metadata["active_priority"] == "high"


class TestExceedsMediumPriority:
    """EXCEEDS on medium-priority -> CV_EXCEEDS with priority=medium."""

    def test_produces_cv_exceeds_medium(self) -> None:
        req = _make_requirement(priority=Priority.MEDIUM)
        assessment = _make_assessment(level=RubricLevel.EXCEEDS)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)

        assert len(flags) == 1
        assert flags[0].name == "CV_EXCEEDS"
        assert flags[0].metadata["active_priority"] == "medium"


class TestExceedsLowPriority:
    """EXCEEDS on low-priority -> NO FLAG."""

    def test_no_flag(self) -> None:
        req = _make_requirement(priority=Priority.LOW)
        assessment = _make_assessment(level=RubricLevel.EXCEEDS)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)
        assert len(flags) == 0


class TestMeetsNoFlag:
    """MEETS -> NO FLAG (baseline)."""

    @pytest.mark.parametrize("priority", [Priority.HIGH, Priority.MEDIUM, Priority.LOW])
    def test_no_flag(self, priority: Priority) -> None:
        req = _make_requirement(priority=priority)
        assessment = _make_assessment(level=RubricLevel.MEETS)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)
        assert len(flags) == 0


class TestNotAssessableBehavioral:
    """NOT_ASSESSABLE on behavioral (assessable_from_cv=false) -> CV_BEHAVIORAL_ROUTED."""

    def test_produces_routing_flag(self) -> None:
        req = _make_requirement(assessable_from_cv=False)
        assessment = _make_assessment(level=RubricLevel.NOT_ASSESSABLE)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)

        assert len(flags) == 1
        flag = flags[0]
        assert flag.name == "CV_BEHAVIORAL_ROUTED"
        assert flag.category == FlagCategory.ROUTING
        assert flag.valence == Valence.NEUTRAL
        assert flag.evidence_type == EvidenceType.ROUTING


# ---------------------------------------------------------------------------
# Pattern-level flag tests
# ---------------------------------------------------------------------------


class TestLowConfidenceCluster:
    """3+ low-confidence assessments -> CV_LOW_CONFIDENCE_CLUSTER."""

    def test_fires_at_three(self) -> None:
        reqs = [_make_requirement(req_id=f"REQ-{i:02d}") for i in range(1, 4)]
        assessments = [
            _make_assessment(req_id=f"REQ-{i:02d}", level=RubricLevel.PARTIAL, confidence=Confidence.LOW)
            for i in range(1, 4)
        ]
        flags = bridge_rubric_to_flags(assessments, reqs, _DEFAULT_SCENARIO)

        pattern_flags = [f for f in flags if f.name == "CV_LOW_CONFIDENCE_CLUSTER"]
        assert len(pattern_flags) == 1
        assert pattern_flags[0].category == FlagCategory.EVIDENCE_QUALITY
        assert pattern_flags[0].valence == Valence.NEGATIVE
        assert pattern_flags[0].evidence_type == EvidenceType.CV_PATTERN

    def test_does_not_fire_at_two(self) -> None:
        reqs = [_make_requirement(req_id=f"REQ-{i:02d}") for i in range(1, 3)]
        assessments = [
            _make_assessment(req_id=f"REQ-{i:02d}", level=RubricLevel.MEETS, confidence=Confidence.LOW)
            for i in range(1, 3)
        ]
        flags = bridge_rubric_to_flags(assessments, reqs, _DEFAULT_SCENARIO)
        pattern_flags = [f for f in flags if f.name == "CV_LOW_CONFIDENCE_CLUSTER"]
        assert len(pattern_flags) == 0


class TestSystematicGap:
    """>50% of high-priority requirements are GAP -> CV_SYSTEMATIC_GAP."""

    def test_fires_when_majority_gap(self) -> None:
        reqs = [_make_requirement(req_id=f"REQ-{i:02d}", priority=Priority.HIGH) for i in range(1, 5)]
        assessments = [
            _make_assessment(req_id="REQ-01", level=RubricLevel.GAP),
            _make_assessment(req_id="REQ-02", level=RubricLevel.GAP),
            _make_assessment(req_id="REQ-03", level=RubricLevel.GAP),
            _make_assessment(req_id="REQ-04", level=RubricLevel.MEETS),
        ]
        flags = bridge_rubric_to_flags(assessments, reqs, _DEFAULT_SCENARIO)

        pattern_flags = [f for f in flags if f.name == "CV_SYSTEMATIC_GAP"]
        assert len(pattern_flags) == 1
        assert pattern_flags[0].category == FlagCategory.EXPERIENCE_GAP
        assert pattern_flags[0].evidence_type == EvidenceType.CV_PATTERN
        assert pattern_flags[0].metadata["gap_count"] == 3

    def test_does_not_fire_at_exactly_half(self) -> None:
        reqs = [_make_requirement(req_id=f"REQ-{i:02d}", priority=Priority.HIGH) for i in range(1, 5)]
        assessments = [
            _make_assessment(req_id="REQ-01", level=RubricLevel.GAP),
            _make_assessment(req_id="REQ-02", level=RubricLevel.GAP),
            _make_assessment(req_id="REQ-03", level=RubricLevel.MEETS),
            _make_assessment(req_id="REQ-04", level=RubricLevel.MEETS),
        ]
        flags = bridge_rubric_to_flags(assessments, reqs, _DEFAULT_SCENARIO)
        pattern_flags = [f for f in flags if f.name == "CV_SYSTEMATIC_GAP"]
        assert len(pattern_flags) == 0

    def test_ignores_medium_priority_gaps(self) -> None:
        """Only high-priority reqs count for systematic gap detection."""
        reqs = [
            _make_requirement(req_id="REQ-01", priority=Priority.HIGH),
            _make_requirement(req_id="REQ-02", priority=Priority.MEDIUM),
            _make_requirement(req_id="REQ-03", priority=Priority.MEDIUM),
        ]
        assessments = [
            _make_assessment(req_id="REQ-01", level=RubricLevel.MEETS),
            _make_assessment(req_id="REQ-02", level=RubricLevel.GAP),
            _make_assessment(req_id="REQ-03", level=RubricLevel.GAP),
        ]
        flags = bridge_rubric_to_flags(assessments, reqs, _DEFAULT_SCENARIO)
        pattern_flags = [f for f in flags if f.name == "CV_SYSTEMATIC_GAP"]
        assert len(pattern_flags) == 0


# ---------------------------------------------------------------------------
# Topic keywords
# ---------------------------------------------------------------------------


class TestTopicKeywords:
    """Topic keywords are derived from requirement text."""

    def test_filters_stopwords(self) -> None:
        keywords = _extract_topic_keywords("Experience in the management of large teams")
        assert "the" not in keywords
        assert "of" not in keywords
        assert "in" not in keywords
        assert "management" in keywords
        assert "large" in keywords
        assert "teams" in keywords

    def test_lowercases(self) -> None:
        keywords = _extract_topic_keywords("P&L Responsibility")
        assert all(w == w.lower() for w in keywords)

    def test_strips_punctuation(self) -> None:
        keywords = _extract_topic_keywords("(leadership), strategy.")
        assert "leadership" in keywords
        assert "strategy" in keywords

    def test_flag_carries_keywords(self) -> None:
        req = _make_requirement(text="Cloud infrastructure migration")
        assessment = _make_assessment(level=RubricLevel.GAP)
        flags = bridge_rubric_to_flags([assessment], [req], _DEFAULT_SCENARIO)
        assert "cloud" in flags[0].topic_keywords
        assert "infrastructure" in flags[0].topic_keywords
        assert "migration" in flags[0].topic_keywords


# ---------------------------------------------------------------------------
# Scenario switching
# ---------------------------------------------------------------------------


class TestScenarioSwitch:
    """Same assessments + different scenarios -> different flags due to priority changes."""

    def test_different_scenarios_different_flags(self) -> None:
        """A requirement high under digital_transformation but low under stabilization."""
        sp = ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.LOW,
            stabilization=Priority.LOW,
            growth=Priority.MEDIUM,
        )
        req = Requirement(
            requirement_id="REQ-01",
            text="Digital platform modernization",
            source_quote="Modernize our digital platforms",
            assessable_from_cv=True,
            scenario_priority=sp,
        )
        # Add a second high-priority MEETS req so systematic gap doesn't fire
        sp2 = ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        )
        req2 = Requirement(
            requirement_id="REQ-02",
            text="Team leadership",
            source_quote="Lead cross-functional teams",
            assessable_from_cv=True,
            scenario_priority=sp2,
        )
        assessment = _make_assessment(req_id="REQ-01", level=RubricLevel.GAP)
        assessment2 = _make_assessment(req_id="REQ-02", level=RubricLevel.MEETS)

        # Under digital_transformation: high priority -> CV_GAP
        flags_dt = bridge_rubric_to_flags([assessment, assessment2], [req, req2], ScenarioName.DIGITAL_TRANSFORMATION)
        gap_flags = [f for f in flags_dt if f.name == "CV_GAP"]
        assert len(gap_flags) == 1
        assert gap_flags[0].metadata["active_priority"] == "high"

        # Under stabilization: low priority -> no flag
        flags_stab = bridge_rubric_to_flags([assessment, assessment2], [req, req2], ScenarioName.STABILIZATION)
        gap_flags_stab = [f for f in flags_stab if f.name == "CV_GAP"]
        assert len(gap_flags_stab) == 0


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

_rubric_level_strategy = st.sampled_from(list(RubricLevel))
_confidence_strategy = st.sampled_from(list(Confidence))
_priority_strategy = st.sampled_from(list(Priority))
_scenario_strategy = st.sampled_from(list(ScenarioName))

_VALID_CV_EVIDENCE_TYPES = {
    EvidenceType.CV_RUBRIC,
    EvidenceType.REQUIREMENT_GAP,
    EvidenceType.CV_PATTERN,
    EvidenceType.ROUTING,
}


@st.composite
def assessment_and_req_strategy(draw: st.DrawFn) -> tuple[list[RubricAssessment], list[Requirement], ScenarioName]:
    """Generate a random set of assessments with matching requirements."""
    scenario = draw(_scenario_strategy)
    n_reqs = draw(st.integers(min_value=1, max_value=10))
    reqs: list[Requirement] = []
    assessments: list[RubricAssessment] = []
    for i in range(1, n_reqs + 1):
        req_id = f"REQ-{i:02d}"
        priority = draw(_priority_strategy)
        assessable = draw(st.booleans())
        req = _make_requirement(
            req_id=req_id,
            text=f"Requirement number {i}",
            assessable_from_cv=assessable,
            scenario=scenario,
            priority=priority,
        )
        reqs.append(req)

        level = draw(_rubric_level_strategy)
        confidence = draw(_confidence_strategy)
        assessment = _make_assessment(
            req_id=req_id,
            level=level,
            confidence=confidence,
        )
        assessments.append(assessment)

    return assessments, reqs, scenario


class TestProperties:
    """Property-based invariants for the bridge function."""

    @given(data=assessment_and_req_strategy())
    @settings(max_examples=100)
    def test_flag_count_bounded(self, data: tuple[list[RubricAssessment], list[Requirement], ScenarioName]) -> None:
        """Flag count <= assessment count + pattern flags (at most 2 pattern types)."""
        assessments, reqs, scenario = data
        flags = bridge_rubric_to_flags(assessments, reqs, scenario)
        # Pattern flags: at most 1 CV_LOW_CONFIDENCE_CLUSTER + 1 CV_SYSTEMATIC_GAP per candidate
        candidates = {a.candidate_name for a in assessments}
        max_pattern = len(candidates) * 2
        assert len(flags) <= len(assessments) + max_pattern

    @given(data=assessment_and_req_strategy())
    @settings(max_examples=100)
    def test_no_orphan_requirement_ids(
        self, data: tuple[list[RubricAssessment], list[Requirement], ScenarioName]
    ) -> None:
        """No flag references a requirement_id not in the input requirements."""
        assessments, reqs, scenario = data
        flags = bridge_rubric_to_flags(assessments, reqs, scenario)
        valid_ids = {r.requirement_id for r in reqs}
        for flag in flags:
            if flag.requirement_id is not None:
                assert flag.requirement_id in valid_ids

    @given(data=assessment_and_req_strategy())
    @settings(max_examples=100)
    def test_all_evidence_types_valid(
        self, data: tuple[list[RubricAssessment], list[Requirement], ScenarioName]
    ) -> None:
        """All CV flags have a valid evidence_type."""
        assessments, reqs, scenario = data
        flags = bridge_rubric_to_flags(assessments, reqs, scenario)
        for flag in flags:
            assert flag.evidence_type in _VALID_CV_EVIDENCE_TYPES


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and empty inputs."""

    def test_empty_assessments(self) -> None:
        flags = bridge_rubric_to_flags([], [], _DEFAULT_SCENARIO)
        assert flags == []

    def test_multiple_candidates(self) -> None:
        """Pattern flags fire per candidate, not globally."""
        reqs = [
            _make_requirement(req_id="REQ-01", priority=Priority.HIGH),
            _make_requirement(req_id="REQ-02", priority=Priority.HIGH, text="Team leadership"),
        ]
        assessments = [
            _make_assessment(req_id="REQ-01", candidate="Alice", level=RubricLevel.GAP),
            _make_assessment(req_id="REQ-02", candidate="Alice", level=RubricLevel.MEETS),
            _make_assessment(req_id="REQ-01", candidate="Bob", level=RubricLevel.MEETS),
            _make_assessment(req_id="REQ-02", candidate="Bob", level=RubricLevel.MEETS),
        ]
        flags = bridge_rubric_to_flags(assessments, reqs, _DEFAULT_SCENARIO)
        alice_flags = [f for f in flags if f.candidate_name == "Alice"]
        bob_flags = [f for f in flags if f.candidate_name == "Bob"]
        assert len(alice_flags) == 1
        assert alice_flags[0].name == "CV_GAP"
        assert len(bob_flags) == 0
