"""Pipeline inter-stage data containers."""

from enum import StrEnum
from pydantic import BaseModel, Field
from shared.models.requirements import Requirement
from shared.models.rubric import RubricAssessment
from shared.models.flags import Flag
from shared.models.candidates import CandidateData
from shared.models.scenarios import ScenarioConfig


class AssessmentMode(StrEnum):
    FULL = "full"
    PARTIAL = "partial"


class FlagProvenance(BaseModel):
    """Per-candidate provenance metadata for the flag set."""

    assessment_mode: AssessmentMode
    personality_flag_count: int = 0
    cv_flag_count: int = 0
    total_flags: int = 0
    big_five_available: bool = False
    personality_source: str | None = None
    requirements_assessed: int = 0
    high_priority_gap_count: int = 0
    dimension_coverage_warnings: list[str] = Field(default_factory=list)
    cross_stream_coherence_notes: list[str] = Field(default_factory=list)


class StageCOutput(BaseModel):
    """Stage C → Stage D contract."""

    requirements: list[Requirement]
    rubric_assessments: list[RubricAssessment]
    candidate_data: list[CandidateData]
    scenario: ScenarioConfig


class StageDOutput(BaseModel):
    """Stage D → Stage E contract."""

    flags: list[Flag]
    provenance_per_candidate: dict[str, FlagProvenance]
    confirmed_requirements: list[Requirement]
    candidate_data: list[CandidateData]
    rubric_matrix: list[RubricAssessment]
    scenario: ScenarioConfig
