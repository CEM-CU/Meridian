"""Scenario configuration."""

from enum import StrEnum

from pydantic import BaseModel, Field


class ScenarioName(StrEnum):
    DIGITAL_TRANSFORMATION = "digital_transformation"
    POST_ACQUISITION = "post_acquisition"
    TURNAROUND = "turnaround"
    STABILIZATION = "stabilization"
    GROWTH = "growth"


class ScenarioConfig(BaseModel):
    """Active scenario. Priority per requirement is stored ON the requirement (ScenarioPriority),
    not in a global lookup table. This model carries the active scenario name and Layer 1 weight vectors."""

    name: ScenarioName
    category_weights: dict[str, float] = Field(default_factory=dict, description="FlagCategory → weight for Layer 1")
