"""Tests for D2: CV flag stream validation."""

from __future__ import annotations

from shared.models import (
    EvidenceType,
    Flag,
    FlagCategory,
    Priority,
    Requirement,
    ScenarioName,
    ScenarioPriority,
    Valence,
)
from stage_d.cv_flag_validation import validate_cv_flags

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scenario_priority(
    *,
    digital_transformation: Priority = Priority.HIGH,
    post_acquisition: Priority = Priority.MEDIUM,
    turnaround: Priority = Priority.MEDIUM,
    stabilization: Priority = Priority.LOW,
    growth: Priority = Priority.HIGH,
) -> ScenarioPriority:
    return ScenarioPriority(
        digital_transformation=digital_transformation,
        post_acquisition=post_acquisition,
        turnaround=turnaround,
        stabilization=stabilization,
        growth=growth,
    )


def _make_requirement(
    req_id: str = "REQ-01",
    priority: Priority = Priority.HIGH,
    scenario: ScenarioName = ScenarioName.DIGITAL_TRANSFORMATION,
) -> Requirement:
    """Build a Requirement with the given ID and priority for the given scenario."""
    # Build ScenarioPriority so the scenario's field gets the given priority.
    kwargs: dict[str, Priority] = {
        "digital_transformation": Priority.MEDIUM,
        "post_acquisition": Priority.MEDIUM,
        "turnaround": Priority.MEDIUM,
        "stabilization": Priority.MEDIUM,
        "growth": Priority.MEDIUM,
    }
    kwargs[scenario.value] = priority
    sp = ScenarioPriority(**kwargs)
    return Requirement(
        requirement_id=req_id,
        text=f"Requirement {req_id}",
        source_quote=f"Source for {req_id}",
        assessable_from_cv=True,
        scenario_priority=sp,
    )


def _make_cv_flag(
    name: str = "CV_GAP",
    requirement_id: str | None = "REQ-01",
    rubric_level: str | None = "gap",
    evidence_type: EvidenceType = EvidenceType.CV_RUBRIC,
    metadata: dict | None = None,
    candidate_name: str = "Alice",
) -> Flag:
    """Build a minimal CV-derived Flag."""
    if metadata is None:
        metadata = {"active_priority": "high"}
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=FlagCategory.EXPERIENCE_GAP,
        valence=Valence.NEGATIVE,
        evidence_type=evidence_type,
        rubric_level=rubric_level,
        requirement_id=requirement_id,
        metadata=metadata,
    )


def _make_pattern_flag(
    name: str = "CV_LOW_CONFIDENCE_CLUSTER",
    rubric_level: str = "partial",
    evidence_type: EvidenceType = EvidenceType.CV_PATTERN,
) -> Flag:
    """Build a pattern flag (no requirement_id, no active_priority)."""
    return Flag(
        name=name,
        candidate_name="Alice",
        category=FlagCategory.EVIDENCE_QUALITY,
        valence=Valence.NEUTRAL,
        evidence_type=evidence_type,
        rubric_level=rubric_level,
        requirement_id=None,
        metadata={},
    )


SCENARIO = ScenarioName.DIGITAL_TRANSFORMATION


# ---------------------------------------------------------------------------
# Valid flags pass through unchanged
# ---------------------------------------------------------------------------


class TestValidFlagsPassThrough:
    """Valid CV flags should be returned unchanged with no warnings."""

    def test_single_valid_cv_gap_flag(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(
            name="CV_GAP",
            requirement_id="REQ-01",
            metadata={"active_priority": "high"},
        )
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == [flag]
        assert warnings == []

    def test_multiple_valid_flags_all_returned(self) -> None:
        req1 = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        req2 = _make_requirement("REQ-02", Priority.MEDIUM, SCENARIO)
        flag1 = _make_cv_flag("CV_GAP", "REQ-01", metadata={"active_priority": "high"})
        flag2 = _make_cv_flag(
            "CV_PARTIAL",
            "REQ-02",
            rubric_level="partial",
            evidence_type=EvidenceType.CV_RUBRIC,
            metadata={"active_priority": "medium"},
        )
        valid, warnings = validate_cv_flags([flag1, flag2], [req1, req2], SCENARIO)
        assert valid == [flag1, flag2]
        assert warnings == []

    def test_all_vocabulary_names_accepted(self) -> None:
        vocab = [
            "CV_GAP",
            "CV_PARTIAL",
            "CV_EXCEEDS",
            "CV_BEHAVIORAL_ROUTED",
        ]
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        evidence_map = {
            "CV_GAP": EvidenceType.CV_RUBRIC,
            "CV_PARTIAL": EvidenceType.CV_RUBRIC,
            "CV_EXCEEDS": EvidenceType.CV_RUBRIC,
            "CV_BEHAVIORAL_ROUTED": EvidenceType.ROUTING,
        }
        flags = [
            _make_cv_flag(
                name=name,
                requirement_id="REQ-01",
                rubric_level="meets",
                evidence_type=evidence_map[name],
                metadata={"active_priority": "high"},
            )
            for name in vocab
        ]
        valid, warnings = validate_cv_flags(flags, [req], SCENARIO)
        assert len(valid) == len(vocab)
        assert warnings == []


# ---------------------------------------------------------------------------
# Flag with invalid name → stripped
# ---------------------------------------------------------------------------


class TestInvalidFlagName:
    """Flags with names not in the CV vocabulary must be stripped."""

    def test_unknown_flag_name_stripped(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(name="PERSONALITY_FLAG", requirement_id="REQ-01")
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1
        assert "PERSONALITY_FLAG" in warnings[0]

    def test_empty_string_name_stripped(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(name="", requirement_id="REQ-01")
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1

    def test_lowercase_cv_gap_stripped(self) -> None:
        """Flag names are case-sensitive; lowercase variant must be rejected."""
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(name="cv_gap", requirement_id="REQ-01")
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Flag missing requirement_id → stripped
# ---------------------------------------------------------------------------


class TestMissingRequirementId:
    """Non-pattern CV flags without requirement_id must be stripped."""

    def test_cv_gap_without_requirement_id_stripped(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(name="CV_GAP", requirement_id=None, metadata={})
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1
        assert "requirement_id" in warnings[0]

    def test_cv_partial_without_requirement_id_stripped(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(name="CV_PARTIAL", requirement_id=None, metadata={})
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Flag with non-existent requirement_id → stripped
# ---------------------------------------------------------------------------


class TestUnknownRequirementId:
    """Flags referencing a requirement not in the confirmed list must be stripped."""

    def test_nonexistent_requirement_id_stripped(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(
            name="CV_GAP",
            requirement_id="REQ-99",
            metadata={"active_priority": "high"},
        )
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1
        assert "REQ-99" in warnings[0]

    def test_empty_requirements_list_strips_all_non_pattern_flags(self) -> None:
        flag = _make_cv_flag("CV_GAP", "REQ-01", metadata={"active_priority": "high"})
        valid, warnings = validate_cv_flags([flag], [], SCENARIO)
        assert valid == []
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Flag with mismatched priority metadata → stripped
# ---------------------------------------------------------------------------


class TestPriorityMismatch:
    """Flags whose active_priority doesn't match the requirement's scenario priority must be stripped."""

    def test_wrong_active_priority_stripped(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(
            name="CV_GAP",
            requirement_id="REQ-01",
            metadata={"active_priority": "low"},  # wrong — should be "high"
        )
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1
        assert "active_priority" in warnings[0]

    def test_missing_active_priority_stripped(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(
            name="CV_GAP",
            requirement_id="REQ-01",
            metadata={},  # active_priority absent
        )
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1
        assert "active_priority" in warnings[0]

    def test_correct_priority_passes(self) -> None:
        req = _make_requirement("REQ-01", Priority.MEDIUM, SCENARIO)
        flag = _make_cv_flag(
            name="CV_GAP",
            requirement_id="REQ-01",
            metadata={"active_priority": "medium"},
        )
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == [flag]
        assert warnings == []


# ---------------------------------------------------------------------------
# Pattern flags without requirement_id → valid
# ---------------------------------------------------------------------------


class TestPatternFlags:
    """Pattern flags (CV_LOW_CONFIDENCE_CLUSTER, CV_SYSTEMATIC_GAP) are exempt from
    requirement_id and active_priority checks."""

    def test_cv_low_confidence_cluster_without_requirement_id_passes(self) -> None:
        flag = _make_pattern_flag("CV_LOW_CONFIDENCE_CLUSTER")
        valid, warnings = validate_cv_flags([flag], [], SCENARIO)
        assert valid == [flag]
        assert warnings == []

    def test_cv_systematic_gap_without_requirement_id_passes(self) -> None:
        flag = _make_pattern_flag("CV_SYSTEMATIC_GAP")
        valid, warnings = validate_cv_flags([flag], [], SCENARIO)
        assert valid == [flag]
        assert warnings == []

    def test_pattern_flag_without_active_priority_passes(self) -> None:
        """Pattern flags need no active_priority in metadata."""
        flag = _make_pattern_flag("CV_LOW_CONFIDENCE_CLUSTER")
        assert flag.metadata == {}
        valid, warnings = validate_cv_flags([flag], [], SCENARIO)
        assert valid == [flag]
        assert warnings == []

    def test_pattern_flag_with_requirement_id_still_passes(self) -> None:
        """Pattern flags with an optional requirement_id don't fail if it's set but
        also don't require it. No priority check is done for pattern flags."""
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        # Pattern flag with a requirement_id but no active_priority — should still pass
        flag = Flag(
            name="CV_LOW_CONFIDENCE_CLUSTER",
            candidate_name="Alice",
            category=FlagCategory.EVIDENCE_QUALITY,
            valence=Valence.NEUTRAL,
            evidence_type=EvidenceType.CV_PATTERN,
            rubric_level="partial",
            requirement_id="REQ-01",
            metadata={},
        )
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == [flag]
        assert warnings == []


# ---------------------------------------------------------------------------
# Empty input → empty output
# ---------------------------------------------------------------------------


class TestEmptyInput:
    """Empty flag list should return empty list with no warnings."""

    def test_empty_flags_returns_empty(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        valid, warnings = validate_cv_flags([], [req], SCENARIO)
        assert valid == []
        assert warnings == []

    def test_empty_flags_empty_requirements_returns_empty(self) -> None:
        valid, warnings = validate_cv_flags([], [], SCENARIO)
        assert valid == []
        assert warnings == []


# ---------------------------------------------------------------------------
# Mix of valid and invalid → only valid returned
# ---------------------------------------------------------------------------


class TestMixedFlags:
    """When valid and invalid flags are mixed, only valid ones are returned."""

    def test_mixed_flags_only_valid_returned(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        valid_flag = _make_cv_flag("CV_GAP", "REQ-01", metadata={"active_priority": "high"})
        bad_name = _make_cv_flag(name="INVALID_NAME", requirement_id="REQ-01")
        bad_req = _make_cv_flag(
            "CV_PARTIAL",
            requirement_id="REQ-99",
            metadata={"active_priority": "high"},
        )
        bad_priority = _make_cv_flag(
            "CV_EXCEEDS",
            "REQ-01",
            rubric_level="exceeds",
            metadata={"active_priority": "low"},  # wrong
        )
        pattern_flag = _make_pattern_flag("CV_SYSTEMATIC_GAP")

        all_flags = [valid_flag, bad_name, bad_req, bad_priority, pattern_flag]
        valid, warnings = validate_cv_flags(all_flags, [req], SCENARIO)

        assert valid == [valid_flag, pattern_flag]
        assert len(warnings) == 3  # bad_name, bad_req, bad_priority

    def test_order_preserved_for_valid_flags(self) -> None:
        req1 = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        req2 = _make_requirement("REQ-02", Priority.MEDIUM, SCENARIO)
        flag1 = _make_cv_flag("CV_GAP", "REQ-01", metadata={"active_priority": "high"})
        bad = _make_cv_flag(name="BAD_FLAG", requirement_id="REQ-01")
        flag2 = _make_cv_flag(
            "CV_PARTIAL",
            "REQ-02",
            rubric_level="partial",
            metadata={"active_priority": "medium"},
        )
        valid, warnings = validate_cv_flags([flag1, bad, flag2], [req1, req2], SCENARIO)
        assert valid == [flag1, flag2]
        assert len(warnings) == 1

    def test_scenario_specific_priority_resolution(self) -> None:
        """Priority must match the active scenario, not any other scenario."""
        # REQ-01 is high priority for digital_transformation, medium for growth
        sp = ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.MEDIUM,
        )
        req = Requirement(
            requirement_id="REQ-01",
            text="Some requirement",
            source_quote="Quote",
            assessable_from_cv=True,
            scenario_priority=sp,
        )
        # Under DIGITAL_TRANSFORMATION the priority is HIGH — correct metadata
        flag_correct = _make_cv_flag("CV_GAP", "REQ-01", metadata={"active_priority": "high"})
        # Under GROWTH the priority would be MEDIUM — but we validate against DIGITAL_TRANSFORMATION
        flag_wrong = _make_cv_flag(
            "CV_PARTIAL", "REQ-01", rubric_level="partial", metadata={"active_priority": "medium"}
        )
        valid, warnings = validate_cv_flags([flag_correct, flag_wrong], [req], ScenarioName.DIGITAL_TRANSFORMATION)
        assert valid == [flag_correct]
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Missing rubric_level → stripped
# ---------------------------------------------------------------------------


class TestMissingRubricLevel:
    """Flags without rubric_level must be stripped."""

    def test_flag_without_rubric_level_stripped(self) -> None:
        req = _make_requirement("REQ-01", Priority.HIGH, SCENARIO)
        flag = _make_cv_flag(
            name="CV_GAP",
            requirement_id="REQ-01",
            rubric_level=None,
            metadata={"active_priority": "high"},
        )
        valid, warnings = validate_cv_flags([flag], [req], SCENARIO)
        assert valid == []
        assert len(warnings) == 1
        assert "rubric_level" in warnings[0]
