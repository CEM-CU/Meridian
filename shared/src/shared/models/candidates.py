"""Candidate data models. Input to pipeline, passed through to Stage E."""

from pydantic import BaseModel, Field


class BigFiveScores(BaseModel):
    """OCEAN scores, each 0.0 to 1.0."""

    O: float = Field(ge=0.0, le=1.0, description="Openness")
    C: float = Field(ge=0.0, le=1.0, description="Conscientiousness")
    E: float = Field(ge=0.0, le=1.0, description="Extraversion")
    A: float = Field(ge=0.0, le=1.0, description="Agreeableness")
    N: float = Field(ge=0.0, le=1.0, description="Neuroticism")


class TeamMember(BaseModel):
    """Existing C-suite team member for complementarity/collision analysis."""

    name: str
    role: str
    big_five: BigFiveScores


class CandidateData(BaseModel):
    """Full candidate data passed through the pipeline."""

    name: str
    cv_text: str = Field(description="Raw CV text — ground truth for F04 validation")
    big_five: BigFiveScores | None = Field(default=None)
    personality_source: str | None = Field(default=None, description="'manual', 'Preset — {name}', 'Modified preset — {name}'")
    team_context: list[TeamMember] = Field(default_factory=list)
