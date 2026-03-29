"""Job status and result models for the evaluation pipeline."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    """Lifecycle states for an evaluation job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class CandidateInput(BaseModel):
    """Simplified candidate input from frontend."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=200)
    cv_text: str = Field(max_length=50_000)
    big_five: dict[str, float] | None = Field(default=None, description="OCEAN scores 0-1")
    personality_source: str | None = Field(default=None)


class JobCreate(BaseModel):
    """Input for creating a new evaluation job."""

    model_config = ConfigDict(extra="forbid")

    jd_text: str = Field(max_length=50_000)
    candidates: list[CandidateInput]
    scenario: str = Field(description="ScenarioName value")
    provider: str = Field(default="anthropic", description="LLM provider")
    model: str | None = Field(default=None, description="Model override")


class JobInfo(BaseModel):
    """Job status response."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobStatus
    created_at: str  # ISO timestamp
    scenario: str
    candidate_count: int
    error: str | None = None
