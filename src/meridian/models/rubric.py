"""CV rubric assessment models. Produced by Stage C3, consumed by C4/D/E."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RubricLevel(StrEnum):
    EXCEEDS = "exceeds"
    MEETS = "meets"
    PARTIAL = "partial"
    GAP = "gap"
    NOT_ASSESSABLE = "not_assessable"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RubricAssessment(BaseModel):
    """Single rubric evaluation: one requirement x one candidate."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    candidate_name: str
    rubric_level: RubricLevel
    confidence: Confidence
    cv_citation: str | None = Field(default=None, description="Specific CV passage. Required for EXCEEDS/MEETS/PARTIAL")
    cv_location: str | None = Field(default=None, description="Role name, section, or paragraph reference")
    notes: str | None = Field(default=None, description="Assessor notes, recency concerns, conflicts")
    investigation_question: str | None = Field(
        default=None, description="Specific question for GAP/PARTIAL/low-confidence"
    )
