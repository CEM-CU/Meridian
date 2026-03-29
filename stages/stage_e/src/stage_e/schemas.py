"""JSON output schemas for Stage E evaluation agent verdicts.

Defines Pydantic v2 models for the structured JSON that each of the 3 evaluation
agents (role_fit, team_dynamics, risk) returns. These models are validated by the
Layer 3 audit and consumed by the synthesis layer.
"""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator
from shared.models.pipeline import AssessmentMode


class AgentEvidenceType(StrEnum):
    """Evidence types available to evaluation agents.

    Superset of shared.models.EvidenceType — agents may cite biographical
    patterns and research-general inferences that don't exist in the flag pipeline.
    """

    SCORED_FLAG = "scored_flag"
    CV_RUBRIC = "cv_rubric"
    REQUIREMENT_GAP = "requirement_gap"
    BIOGRAPHICAL_PATTERN = "biographical_pattern"
    RESEARCH_GENERAL = "research_general"


class AgentRole(StrEnum):
    """The three evaluation agent roles in Stage E Layer 2."""

    ROLE_FIT = "role_fit"
    TEAM_DYNAMICS = "team_dynamics"
    RISK = "risk"


_VALID_CONFIDENCE_VALUES = frozenset({"high", "medium", "low"})
_VALID_AGENT_ROLES = frozenset(r.value for r in AgentRole)
_VALID_ASSESSMENT_MODES = frozenset(m.value for m in AssessmentMode)


def _check_membership(value: str, allowed: frozenset[str], field_name: str) -> None:
    """Validate that a value is in the allowed set, raising ValueError if not."""
    if value not in allowed:
        msg = f"{field_name} must be one of {sorted(allowed)}, got '{value}'"
        raise ValueError(msg)


class EvidenceBasis(BaseModel):
    """Evidence backing a single claim."""

    type: AgentEvidenceType
    reference: str = Field(
        description=("Flag name for scored_flag, requirement_id for cv_rubric/requirement_gap, free-text for others"),
    )
    detail: str | None = Field(
        default=None,
        description="Additional context for the evidence reference",
    )


class Claim(BaseModel):
    """Single evaluative claim made by an agent."""

    text: str = Field(min_length=10, max_length=500, description="The claim text")
    evidence_basis: EvidenceBasis
    confidence: str = Field(description="high, medium, or low")
    candidate_name: str

    @model_validator(mode="after")
    def _validate_confidence(self) -> "Claim":
        """Ensure confidence is one of the allowed values."""
        _check_membership(self.confidence, _VALID_CONFIDENCE_VALUES, "confidence")
        return self


class AgentVerdict(BaseModel):
    """Complete output from a single evaluation agent."""

    agent_role: str = Field(description="role_fit, team_dynamics, or risk")
    claims: list[Claim] = Field(min_length=1, description="At least one claim required")
    summary: str = Field(min_length=20, max_length=1000, description="Agent's overall summary")
    assessment_mode: str = Field(description="full or partial")
    unaddressed_flags: list[str] = Field(
        default_factory=list,
        description="Flags in allowlist that agent chose not to address",
    )

    @model_validator(mode="after")
    def _validate_role_and_mode(self) -> "AgentVerdict":
        """Ensure agent_role and assessment_mode are valid."""
        errors: list[str] = []
        for value, allowed, field_name in (
            (self.agent_role, _VALID_AGENT_ROLES, "agent_role"),
            (self.assessment_mode, _VALID_ASSESSMENT_MODES, "assessment_mode"),
        ):
            if value not in allowed:
                errors.append(f"{field_name} must be one of {sorted(allowed)}, got '{value}'")
        if errors:
            raise ValueError("; ".join(errors))
        return self


def validate_research_general_cap(verdict: AgentVerdict, cap: int = 2) -> list[str]:
    """Check that research_general evidence count doesn't exceed cap.

    Returns list of warning strings (empty if within cap).
    """
    count = sum(1 for claim in verdict.claims if claim.evidence_basis.type == AgentEvidenceType.RESEARCH_GENERAL)
    if count > cap:
        return [f"Agent '{verdict.agent_role}' has {count} research_general claims (cap is {cap})"]
    return []
