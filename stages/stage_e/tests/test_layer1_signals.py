"""Tests for E2: Layer 1 — Scenario Weight Application, Signal Computation, and Tension Map.

Covers:
1. Weight application correct per category
2. ROUTING category gets 0 weight (excluded from signal computation)
3. Signal label: all positive flags → strong_positive
4. Signal label: all negative → strong_negative
5. Signal label: mixed flags → mixed
6. Risk band: 0 risk flags → low
7. Risk band: 3+ risk flags → elevated/high
8. Tension map detects cross-stream tension
9. Tension map: no tension → empty
10. F02 verification: signal_labels and risk_bands not in agent input structures
11. Partial mode candidate → INSUFFICIENT_DATA + note
12. ScenarioConfig.category_weights override defaults when provided
13. Empty flags → sensible defaults (insufficient_data)
"""

from __future__ import annotations

import pytest
from shared.models import EvidenceType, Flag, FlagCategory, ScenarioConfig, ScenarioName, Valence
from stage_e.layer1_signals import (
    _DEFAULT_CATEGORY_WEIGHTS,
    Layer1Output,
    RiskBand,
    SignalStrength,
    TensionPair,
    _resolve_weights,
    compute_layer1,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_flag(
    name: str,
    candidate_name: str,
    category: FlagCategory,
    valence: Valence,
    evidence_type: EvidenceType = EvidenceType.SCORED_FLAG,
    big_five_source: str | None = "C",
    requirement_id: str | None = None,
) -> Flag:
    """Create a minimal Flag for testing."""
    return Flag(
        name=name,
        candidate_name=candidate_name,
        category=category,
        valence=valence,
        evidence_type=evidence_type,
        big_five_source=big_five_source,
        requirement_id=requirement_id,
    )


def _make_scenario(category_weights: dict[str, float] | None = None) -> ScenarioConfig:
    """Create a ScenarioConfig with optional weight overrides."""
    return ScenarioConfig(
        name=ScenarioName.DIGITAL_TRANSFORMATION,
        category_weights=category_weights or {},
    )


# ---------------------------------------------------------------------------
# 1. Weight application correct per category
# ---------------------------------------------------------------------------


def test_weight_application_uses_category_weight() -> None:
    """Weighted score must reflect the category weight for each flag."""
    # DARK_SIDE weight is 1.3 (highest). One positive DARK_SIDE flag → score = 1.3.
    flags = [
        _make_flag("DARK_SIDE_FLAG", "Alice", FlagCategory.DARK_SIDE, Valence.POSITIVE),
    ]
    scenario = _make_scenario()
    result = compute_layer1(flags, scenario, ["Alice"], {"Alice": "full"})
    assert pytest.approx(result.weighted_scores_per_candidate["Alice"]) == 1.3


def test_weight_application_negative_flag_subtracts() -> None:
    """A negative DERAILMENT flag (weight 1.2) should subtract from score."""
    flags = [
        _make_flag("DERAILMENT_FLAG", "Alice", FlagCategory.DERAILMENT, Valence.NEGATIVE),
    ]
    scenario = _make_scenario()
    result = compute_layer1(flags, scenario, ["Alice"], {"Alice": "full"})
    assert pytest.approx(result.weighted_scores_per_candidate["Alice"]) == -1.2


def test_weight_application_multiple_categories_sum() -> None:
    """Multiple flags from different categories produce correct weighted sum."""
    flags = [
        _make_flag("EXEC_FLAG", "Alice", FlagCategory.EXECUTION, Valence.POSITIVE),  # +1.0
        _make_flag("DARK_SIDE_FLAG", "Alice", FlagCategory.DARK_SIDE, Valence.NEGATIVE),  # -1.3
    ]
    scenario = _make_scenario()
    result = compute_layer1(flags, scenario, ["Alice"], {"Alice": "full"})
    assert pytest.approx(result.weighted_scores_per_candidate["Alice"]) == 1.0 - 1.3


# ---------------------------------------------------------------------------
# 2. ROUTING category gets 0 weight
# ---------------------------------------------------------------------------


def test_routing_flag_contributes_zero_to_score() -> None:
    """A ROUTING flag should contribute nothing to the weighted score."""
    flags = [
        _make_flag(
            "ROUTING_FLAG",
            "Alice",
            FlagCategory.ROUTING,
            Valence.POSITIVE,
            evidence_type=EvidenceType.ROUTING,
            big_five_source=None,
        ),
    ]
    scenario = _make_scenario()
    result = compute_layer1(flags, scenario, ["Alice"], {"Alice": "full"})
    assert result.weighted_scores_per_candidate["Alice"] == 0.0
    assert result.signal_labels["Alice"] == SignalStrength.INSUFFICIENT_DATA


def test_routing_default_weight_is_zero() -> None:
    """_DEFAULT_CATEGORY_WEIGHTS must have ROUTING = 0.0."""
    assert _DEFAULT_CATEGORY_WEIGHTS["ROUTING"] == 0.0


# ---------------------------------------------------------------------------
# 3. Signal label: all positive → strong_positive
# ---------------------------------------------------------------------------


def test_signal_label_all_positive_is_strong_positive() -> None:
    """All positive flags with no negative flags → STRONG_POSITIVE."""
    flags = [
        _make_flag("F1", "Alice", FlagCategory.EXECUTION, Valence.POSITIVE),
        _make_flag("F2", "Alice", FlagCategory.STRATEGIC, Valence.POSITIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.signal_labels["Alice"] == SignalStrength.STRONG_POSITIVE


# ---------------------------------------------------------------------------
# 4. Signal label: all negative → strong_negative
# ---------------------------------------------------------------------------


def test_signal_label_all_negative_is_strong_negative() -> None:
    """All negative flags with no positive flags → STRONG_NEGATIVE."""
    flags = [
        _make_flag("F1", "Alice", FlagCategory.EXECUTION, Valence.NEGATIVE),
        _make_flag("F2", "Alice", FlagCategory.DARK_SIDE, Valence.NEGATIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.signal_labels["Alice"] == SignalStrength.STRONG_NEGATIVE


# ---------------------------------------------------------------------------
# 5. Signal label: mixed flags → mixed
# ---------------------------------------------------------------------------


def test_signal_label_balanced_positive_negative_is_mixed() -> None:
    """Roughly equal positive and negative weighted sums → MIXED."""
    # EXECUTION weight = 1.0 both sides → balanced
    flags = [
        _make_flag("F1", "Alice", FlagCategory.EXECUTION, Valence.POSITIVE),
        _make_flag("F2", "Alice", FlagCategory.EXECUTION, Valence.NEGATIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.signal_labels["Alice"] == SignalStrength.MIXED


# ---------------------------------------------------------------------------
# 6. Risk band: 0 risk flags → low
# ---------------------------------------------------------------------------


def test_risk_band_no_risk_flags_is_low() -> None:
    """Candidate with only EXECUTION flags (not risk categories) → LOW risk band."""
    flags = [
        _make_flag("F1", "Alice", FlagCategory.EXECUTION, Valence.POSITIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.risk_bands["Alice"] == RiskBand.LOW


def test_risk_band_single_derailment_flag_is_moderate() -> None:
    """One DERAILMENT flag → MODERATE risk band (count=1)."""
    flags = [
        _make_flag("DERAIL1", "Alice", FlagCategory.DERAILMENT, Valence.NEGATIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.risk_bands["Alice"] == RiskBand.MODERATE


# ---------------------------------------------------------------------------
# 7. Risk band: 3+ risk flags → elevated/high
# ---------------------------------------------------------------------------


def test_risk_band_three_risk_flags_is_elevated() -> None:
    """Three risk-category flags → ELEVATED."""
    flags = [
        _make_flag("D1", "Alice", FlagCategory.DERAILMENT, Valence.NEGATIVE),
        _make_flag("D2", "Alice", FlagCategory.DARK_SIDE, Valence.NEGATIVE),
        _make_flag("T1", "Alice", FlagCategory.TENURE, Valence.NEGATIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.risk_bands["Alice"] == RiskBand.ELEVATED


def test_risk_band_five_risk_flags_is_high() -> None:
    """Five or more risk-category flags → HIGH."""
    flags = [
        _make_flag("D1", "Alice", FlagCategory.DERAILMENT, Valence.NEGATIVE),
        _make_flag("D2", "Alice", FlagCategory.DARK_SIDE, Valence.NEGATIVE),
        _make_flag("T1", "Alice", FlagCategory.TENURE, Valence.NEGATIVE),
        _make_flag("E1", "Alice", FlagCategory.EVIDENCE_QUALITY, Valence.NEGATIVE),
        _make_flag("D3", "Alice", FlagCategory.DERAILMENT, Valence.NEGATIVE, big_five_source="N"),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.risk_bands["Alice"] == RiskBand.HIGH


def test_risk_band_high_priority_experience_gap_counts() -> None:
    """CV_GAP flags in EXPERIENCE_GAP category count toward risk band."""
    flags = [
        _make_flag(
            "CV_GAP",
            "Alice",
            FlagCategory.EXPERIENCE_GAP,
            Valence.NEGATIVE,
            evidence_type=EvidenceType.REQUIREMENT_GAP,
            big_five_source=None,
            requirement_id="REQ-01",
        ),
        _make_flag(
            "CV_GAP",
            "Alice",
            FlagCategory.EXPERIENCE_GAP,
            Valence.NEGATIVE,
            evidence_type=EvidenceType.REQUIREMENT_GAP,
            big_five_source=None,
            requirement_id="REQ-02",
        ),
        _make_flag(
            "CV_GAP",
            "Alice",
            FlagCategory.EXPERIENCE_GAP,
            Valence.NEGATIVE,
            evidence_type=EvidenceType.REQUIREMENT_GAP,
            big_five_source=None,
            requirement_id="REQ-03",
        ),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.risk_bands["Alice"] == RiskBand.ELEVATED


# ---------------------------------------------------------------------------
# 8. Tension map: cross-stream tension detected
# ---------------------------------------------------------------------------


def test_tension_map_detects_cross_stream_tension() -> None:
    """Positive EXPERIENCE_STRENGTH flag + negative EXECUTION flag → cross_stream tension."""
    flags = [
        _make_flag(
            "CV_EXCEEDS_EXECUTION",
            "Alice",
            FlagCategory.EXPERIENCE_STRENGTH,
            Valence.POSITIVE,
            evidence_type=EvidenceType.CV_RUBRIC,
            big_five_source=None,
            requirement_id="REQ-01",
        ),
        _make_flag(
            "EXECUTION_LOW_CONSCIENTIOUSNESS_RISK",
            "Alice",
            FlagCategory.EXECUTION,
            Valence.NEGATIVE,
            evidence_type=EvidenceType.SCORED_FLAG,
            big_five_source="C",
        ),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert len(result.tension_map) >= 1
    cross_stream = [t for t in result.tension_map if t.tension_type == "cross_stream"]
    assert len(cross_stream) >= 1
    tension = cross_stream[0]
    assert tension.candidate_name == "Alice"
    assert tension.domain == "EXECUTION"
    assert tension.positive_flag == "CV_EXCEEDS_EXECUTION"
    assert tension.negative_flag == "EXECUTION_LOW_CONSCIENTIOUSNESS_RISK"


# ---------------------------------------------------------------------------
# 9. Tension map: no tension → empty
# ---------------------------------------------------------------------------


def test_tension_map_empty_when_no_tension() -> None:
    """All-positive flags with no cross-stream or intra-stream contradictions → empty tension map."""
    flags = [
        _make_flag("F1", "Alice", FlagCategory.EXECUTION, Valence.POSITIVE),
        _make_flag("F2", "Alice", FlagCategory.STRATEGIC, Valence.POSITIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.tension_map == []


# ---------------------------------------------------------------------------
# 10. F02 verification: signal_labels and risk_bands not in agent input types
# ---------------------------------------------------------------------------


def test_f02_layer1_output_fields_are_separate_from_agent_input() -> None:
    """F02: Layer1Output must have signal_labels and risk_bands as top-level fields.

    Agents receive only: flags + tension_map + candidate data + requirements.
    Verify that Layer1Output is a distinct type from what agents receive —
    signal_labels and risk_bands are attributes of Layer1Output only.
    """
    from stage_e.schemas import AgentVerdict, Claim, EvidenceBasis

    # AgentVerdict must NOT have signal_labels or risk_bands fields.
    verdict_fields = set(AgentVerdict.model_fields.keys())
    assert "signal_labels" not in verdict_fields, "AgentVerdict must not contain signal_labels (F02 violation)"
    assert "risk_bands" not in verdict_fields, "AgentVerdict must not contain risk_bands (F02 violation)"

    # Claim must NOT have signal_labels or risk_bands fields.
    claim_fields = set(Claim.model_fields.keys())
    assert "signal_labels" not in claim_fields, "Claim must not contain signal_labels (F02 violation)"
    assert "risk_bands" not in claim_fields, "Claim must not contain risk_bands (F02 violation)"

    # EvidenceBasis must NOT have signal_labels or risk_bands fields.
    evidence_fields = set(EvidenceBasis.model_fields.keys())
    assert "signal_labels" not in evidence_fields, "EvidenceBasis must not contain signal_labels (F02 violation)"
    assert "risk_bands" not in evidence_fields, "EvidenceBasis must not contain risk_bands (F02 violation)"

    # Layer1Output MUST have these fields (they exist for synthesis only).
    assert hasattr(Layer1Output, "__dataclass_fields__")
    output_fields = set(Layer1Output.__dataclass_fields__.keys())
    assert "signal_labels" in output_fields, "Layer1Output must have signal_labels"
    assert "risk_bands" in output_fields, "Layer1Output must have risk_bands"


# ---------------------------------------------------------------------------
# 11. Partial mode candidate → INSUFFICIENT_DATA + note
# ---------------------------------------------------------------------------


def test_partial_mode_no_personality_flags_gives_insufficient_data() -> None:
    """Partial-mode candidate with only CV flags → INSUFFICIENT_DATA risk band + note."""
    flags = [
        _make_flag(
            "CV_EXCEEDS",
            "Alice",
            FlagCategory.EXPERIENCE_STRENGTH,
            Valence.POSITIVE,
            evidence_type=EvidenceType.CV_RUBRIC,
            big_five_source=None,
            requirement_id="REQ-01",
        ),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "partial"})
    assert result.risk_bands["Alice"] == RiskBand.INSUFFICIENT_DATA
    assert len(result.partial_mode_notes) == 1
    assert "Alice" in result.partial_mode_notes[0]
    assert "experience-based signals" in result.partial_mode_notes[0]


def test_partial_mode_with_personality_flags_uses_normal_risk_band() -> None:
    """Partial-mode candidate WHO DOES have personality flags still gets risk band computed."""
    flags = [
        _make_flag("DERAIL1", "Alice", FlagCategory.DERAILMENT, Valence.NEGATIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "partial"})
    # Has a SCORED_FLAG (default evidence_type), so partial mode note should not fire.
    assert result.risk_bands["Alice"] == RiskBand.MODERATE
    assert len(result.partial_mode_notes) == 0


# ---------------------------------------------------------------------------
# 12. ScenarioConfig.category_weights override defaults
# ---------------------------------------------------------------------------


def test_scenario_category_weights_override_defaults() -> None:
    """Custom category_weights in ScenarioConfig override _DEFAULT_CATEGORY_WEIGHTS."""
    # Override EXECUTION weight from 1.0 to 3.0
    scenario = _make_scenario({"EXECUTION": 3.0})
    flags = [
        _make_flag("F1", "Alice", FlagCategory.EXECUTION, Valence.POSITIVE),
    ]
    result = compute_layer1(flags, scenario, ["Alice"], {"Alice": "full"})
    assert pytest.approx(result.weighted_scores_per_candidate["Alice"]) == 3.0


def test_scenario_weights_only_override_specified_categories() -> None:
    """Non-overridden categories still use default weights."""
    scenario = _make_scenario({"EXECUTION": 3.0})
    weights = _resolve_weights(scenario)
    # DARK_SIDE should still be the default 1.3
    assert pytest.approx(weights["DARK_SIDE"]) == 1.3
    # EXECUTION should be overridden
    assert pytest.approx(weights["EXECUTION"]) == 3.0


def test_scenario_weights_can_zero_out_category() -> None:
    """A scenario can set a category weight to 0.0, making its flags count as neutral."""
    scenario = _make_scenario({"DARK_SIDE": 0.0})
    flags = [
        _make_flag("DS1", "Alice", FlagCategory.DARK_SIDE, Valence.POSITIVE),
    ]
    result = compute_layer1(flags, scenario, ["Alice"], {"Alice": "full"})
    assert result.weighted_scores_per_candidate["Alice"] == 0.0


# ---------------------------------------------------------------------------
# 13. Empty flags → sensible defaults (insufficient_data)
# ---------------------------------------------------------------------------


def test_empty_flags_signal_label_is_insufficient_data() -> None:
    """Candidate with no flags → INSUFFICIENT_DATA signal label."""
    result = compute_layer1([], _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.signal_labels["Alice"] == SignalStrength.INSUFFICIENT_DATA


def test_empty_flags_risk_band_is_low() -> None:
    """Candidate with no flags → LOW risk band (no risk flags = 0 count)."""
    result = compute_layer1([], _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.risk_bands["Alice"] == RiskBand.LOW


def test_empty_flags_weighted_score_is_zero() -> None:
    """Candidate with no flags → weighted score of 0.0."""
    result = compute_layer1([], _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.weighted_scores_per_candidate["Alice"] == 0.0


def test_empty_flags_tension_map_is_empty() -> None:
    """No flags → no tensions."""
    result = compute_layer1([], _make_scenario(), ["Alice"], {"Alice": "full"})
    assert result.tension_map == []


# ---------------------------------------------------------------------------
# Additional: multi-candidate isolation
# ---------------------------------------------------------------------------


def test_candidates_are_scored_independently() -> None:
    """Flags for Alice do not influence Bob's score."""
    flags = [
        _make_flag("F1", "Alice", FlagCategory.EXECUTION, Valence.POSITIVE),
        _make_flag("F2", "Bob", FlagCategory.DARK_SIDE, Valence.NEGATIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice", "Bob"], {"Alice": "full", "Bob": "full"})
    assert pytest.approx(result.weighted_scores_per_candidate["Alice"]) == 1.0
    assert pytest.approx(result.weighted_scores_per_candidate["Bob"]) == -1.3


def test_tension_map_separates_candidates() -> None:
    """Tension map entries carry the correct candidate_name."""
    flags = [
        _make_flag(
            "CV_EXCEEDS",
            "Alice",
            FlagCategory.EXPERIENCE_STRENGTH,
            Valence.POSITIVE,
            evidence_type=EvidenceType.CV_RUBRIC,
            big_five_source=None,
        ),
        _make_flag(
            "EXEC_NEG",
            "Alice",
            FlagCategory.EXECUTION,
            Valence.NEGATIVE,
        ),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice", "Bob"], {"Alice": "full", "Bob": "full"})
    for tension in result.tension_map:
        assert tension.candidate_name == "Alice"


# ---------------------------------------------------------------------------
# Additional: intra-stream tension
# ---------------------------------------------------------------------------


def test_tension_map_detects_intra_stream_tension() -> None:
    """Positive and negative flags in same category → intra_stream tension."""
    flags = [
        _make_flag("EXEC_POS", "Alice", FlagCategory.EXECUTION, Valence.POSITIVE),
        _make_flag("EXEC_NEG", "Alice", FlagCategory.EXECUTION, Valence.NEGATIVE),
    ]
    result = compute_layer1(flags, _make_scenario(), ["Alice"], {"Alice": "full"})
    intra = [t for t in result.tension_map if t.tension_type == "intra_stream"]
    assert len(intra) >= 1
    assert intra[0].positive_flag == "EXEC_POS"
    assert intra[0].negative_flag == "EXEC_NEG"


# ---------------------------------------------------------------------------
# Additional: Layer1Output is immutable (frozen dataclass)
# ---------------------------------------------------------------------------


def test_layer1_output_is_frozen() -> None:
    """Layer1Output must be a frozen dataclass — mutation raises FrozenInstanceError."""
    result = compute_layer1([], _make_scenario(), ["Alice"], {"Alice": "full"})
    with pytest.raises((AttributeError, TypeError)):
        result.signal_labels = {}  # type: ignore[misc]


def test_tension_pair_is_frozen() -> None:
    """TensionPair must be frozen."""
    tp = TensionPair(
        candidate_name="Alice",
        positive_flag="F1",
        negative_flag="F2",
        domain="EXECUTION",
        tension_type="cross_stream",
        description="test",
    )
    with pytest.raises((AttributeError, TypeError)):
        tp.candidate_name = "Bob"  # type: ignore[misc]
