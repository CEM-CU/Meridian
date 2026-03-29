"""Tests for Stage E agent verdict JSON output schemas."""

import pytest
from pydantic import ValidationError
from stage_e.schemas import (
    AgentEvidenceType,
    AgentRole,
    AgentVerdict,
    Claim,
    EvidenceBasis,
    validate_research_general_cap,
)

# ---------------------------------------------------------------------------
# Helpers — reusable valid fixtures (immutable via function call)
# ---------------------------------------------------------------------------


def _valid_evidence_basis(**overrides: object) -> dict:
    """Return a valid EvidenceBasis dict with optional overrides."""
    base: dict = {
        "type": "scored_flag",
        "reference": "HIGH_CONSCIENTIOUSNESS",
        "detail": "Big Five C score = 0.85",
    }
    return {**base, **overrides}


def _valid_claim(**overrides: object) -> dict:
    """Return a valid Claim dict with optional overrides."""
    base: dict = {
        "text": "Candidate shows strong conscientiousness relevant to the CTO role",
        "evidence_basis": _valid_evidence_basis(),
        "confidence": "high",
        "candidate_name": "Jane Doe",
    }
    return {**base, **overrides}


def _valid_verdict(**overrides: object) -> dict:
    """Return a valid AgentVerdict dict with optional overrides."""
    base: dict = {
        "agent_role": "role_fit",
        "claims": [_valid_claim()],
        "summary": "Overall strong fit for the CTO position based on experience and personality.",
        "assessment_mode": "full",
        "unaddressed_flags": [],
    }
    return {**base, **overrides}


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestValidParsing:
    """Valid inputs parse without error."""

    def test_valid_agent_verdict_parses(self) -> None:
        verdict = AgentVerdict.model_validate(_valid_verdict())
        assert verdict.agent_role == "role_fit"
        assert len(verdict.claims) == 1
        assert verdict.assessment_mode == "full"

    def test_valid_verdict_partial_mode(self) -> None:
        verdict = AgentVerdict.model_validate(_valid_verdict(assessment_mode="partial"))
        assert verdict.assessment_mode == "partial"

    def test_all_agent_roles_accepted(self) -> None:
        for role in AgentRole:
            verdict = AgentVerdict.model_validate(_valid_verdict(agent_role=role.value))
            assert verdict.agent_role == role.value

    def test_all_evidence_types_accepted(self) -> None:
        for etype in AgentEvidenceType:
            eb = EvidenceBasis.model_validate(_valid_evidence_basis(type=etype.value))
            assert eb.type == etype

    def test_detail_is_optional(self) -> None:
        eb = EvidenceBasis.model_validate(_valid_evidence_basis(detail=None))
        assert eb.detail is None

    def test_unaddressed_flags_defaults_empty(self) -> None:
        data = _valid_verdict()
        del data["unaddressed_flags"]
        verdict = AgentVerdict.model_validate(data)
        assert verdict.unaddressed_flags == []


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestValidationErrors:
    """Invalid inputs produce ValidationError."""

    def test_missing_evidence_basis_rejected(self) -> None:
        data = _valid_claim()
        del data["evidence_basis"]
        with pytest.raises(ValidationError):
            Claim.model_validate(data)

    def test_unknown_evidence_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            EvidenceBasis.model_validate(_valid_evidence_basis(type="invented_type"))

    def test_invalid_agent_role_rejected(self) -> None:
        with pytest.raises(ValidationError, match="agent_role"):
            AgentVerdict.model_validate(_valid_verdict(agent_role="strategist"))

    def test_invalid_assessment_mode_rejected(self) -> None:
        with pytest.raises(ValidationError, match="assessment_mode"):
            AgentVerdict.model_validate(_valid_verdict(assessment_mode="hybrid"))

    def test_invalid_confidence_rejected(self) -> None:
        with pytest.raises(ValidationError, match="confidence"):
            Claim.model_validate(_valid_claim(confidence="very_high"))

    def test_empty_claims_list_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentVerdict.model_validate(_valid_verdict(claims=[]))

    def test_claim_text_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Claim.model_validate(_valid_claim(text="Short"))

    def test_claim_text_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Claim.model_validate(_valid_claim(text="x" * 501))

    def test_summary_too_short_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentVerdict.model_validate(_valid_verdict(summary="Too short."))

    def test_summary_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentVerdict.model_validate(_valid_verdict(summary="x" * 1001))


# ---------------------------------------------------------------------------
# research_general cap validation
# ---------------------------------------------------------------------------


class TestResearchGeneralCap:
    """validate_research_general_cap enforces the per-agent cap."""

    def _make_verdict_with_research_count(self, count: int) -> AgentVerdict:
        """Build a verdict with a given number of research_general claims."""
        claims = [
            _valid_claim(
                text=f"Research-based inference number {i + 1} about the candidate",
                evidence_basis=_valid_evidence_basis(
                    type="research_general",
                    reference="I/O psychology literature",
                ),
            )
            for i in range(count)
        ]
        # Ensure at least one claim if count is 0
        if not claims:
            claims = [_valid_claim()]
        return AgentVerdict.model_validate(_valid_verdict(claims=claims))

    def test_at_cap_no_warnings(self) -> None:
        verdict = self._make_verdict_with_research_count(2)
        warnings = validate_research_general_cap(verdict)
        assert warnings == []

    def test_below_cap_no_warnings(self) -> None:
        verdict = self._make_verdict_with_research_count(1)
        warnings = validate_research_general_cap(verdict)
        assert warnings == []

    def test_above_cap_returns_warning(self) -> None:
        verdict = self._make_verdict_with_research_count(3)
        warnings = validate_research_general_cap(verdict)
        assert len(warnings) == 1
        assert "3" in warnings[0]
        assert "cap is 2" in warnings[0]

    def test_custom_cap(self) -> None:
        verdict = self._make_verdict_with_research_count(2)
        warnings = validate_research_general_cap(verdict, cap=1)
        assert len(warnings) == 1


# ---------------------------------------------------------------------------
# Round-trip serialization
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """model_dump -> model_validate produces identical object."""

    def test_round_trip_agent_verdict(self) -> None:
        original = AgentVerdict.model_validate(_valid_verdict())
        dumped = original.model_dump()
        restored = AgentVerdict.model_validate(dumped)
        assert original == restored

    def test_round_trip_with_unaddressed_flags(self) -> None:
        original = AgentVerdict.model_validate(_valid_verdict(unaddressed_flags=["FLAG_A", "FLAG_B"]))
        dumped = original.model_dump()
        restored = AgentVerdict.model_validate(dumped)
        assert original == restored


# ---------------------------------------------------------------------------
# Enum value checks
# ---------------------------------------------------------------------------


class TestEnumValues:
    """All enum values are lowercase strings."""

    def test_agent_evidence_type_values_lowercase(self) -> None:
        for member in AgentEvidenceType:
            assert member.value == member.value.lower()
            assert isinstance(member.value, str)

    def test_agent_role_values_lowercase(self) -> None:
        for member in AgentRole:
            assert member.value == member.value.lower()
            assert isinstance(member.value, str)
