"""Flag models. Produced by Stage D, consumed by Stage E."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FlagCategory(StrEnum):
    EXECUTION = "EXECUTION"
    STRATEGIC = "STRATEGIC"
    COLLISION = "COLLISION"
    COMPLEMENT = "COMPLEMENT"
    FRICTION = "FRICTION"
    CULTURAL = "CULTURAL"
    DERAILMENT = "DERAILMENT"
    DARK_SIDE = "DARK_SIDE"
    INTEGRATION = "INTEGRATION"
    TENURE = "TENURE"
    GROUPTHINK = "GROUPTHINK"
    EXPERIENCE_STRENGTH = "EXPERIENCE_STRENGTH"
    EXPERIENCE_GAP = "EXPERIENCE_GAP"
    EVIDENCE_QUALITY = "EVIDENCE_QUALITY"
    ROUTING = "ROUTING"


class Valence(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EvidenceType(StrEnum):
    SCORED_FLAG = "scored_flag"
    CV_RUBRIC = "cv_rubric"
    REQUIREMENT_GAP = "requirement_gap"
    CV_PATTERN = "cv_pattern"
    ROUTING = "routing"


class Flag(BaseModel):
    """Single flag in the merged flag set. Both personality and CV-derived flags use this model."""

    model_config = ConfigDict(extra="forbid")

    name: str
    candidate_name: str
    category: FlagCategory
    valence: Valence
    evidence_type: EvidenceType
    topic_keywords: list[str] = Field(default_factory=list)

    # Personality flag fields (None for CV-derived flags)
    big_five_source: str | None = Field(default=None, description="O, C, E, A, or N")
    big_five_score: float | None = Field(default=None)
    threshold_used: float | None = Field(default=None)

    # CV-derived flag fields (None for personality flags)
    requirement_id: str | None = Field(default=None)
    rubric_level: str | None = Field(default=None)
    cv_citation: str | None = Field(default=None)
    cv_location: str | None = Field(default=None, description="Role name, section, or paragraph reference from CV")
    confidence: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    investigation_question: str | None = Field(default=None)

    metadata: dict[str, Any] = Field(default_factory=dict)
