"""JD requirement extraction models. Produced by Stage C1, consumed by C2/C3/C4/D/E."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScenarioPriority(BaseModel):
    """Per-requirement priority under each scenario. Assigned by LLM during C1 extraction."""

    model_config = ConfigDict(extra="forbid")

    digital_transformation: Priority
    post_acquisition: Priority
    turnaround: Priority
    stabilization: Priority
    growth: Priority

    def for_scenario(self, scenario_name: str) -> Priority:
        """Get priority for a given scenario name.

        Raises:
            ValueError: If scenario_name is not a valid scenario.
        """
        valid_scenarios = set(ScenarioPriority.model_fields.keys())
        if scenario_name not in valid_scenarios:
            raise ValueError(f"Invalid scenario '{scenario_name}'; valid scenarios: {sorted(valid_scenarios)}")
        return getattr(self, scenario_name)


class Requirement(BaseModel):
    """Single assessable requirement extracted from a JD."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(description="Sequential ID: REQ-01 through REQ-N")
    text: str = Field(max_length=200, description="Normalized requirement statement")
    source_quote: str = Field(max_length=300, description="Verbatim or near-verbatim from JD")
    assessable_from_cv: bool = Field(
        description="False for behavioral requirements, true otherwise. LLM assigns during extraction."
    )
    scenario_priority: ScenarioPriority = Field(description="LLM assigns priority per scenario during C1 extraction")
