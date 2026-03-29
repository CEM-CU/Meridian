"""Input conversion helpers for the pipeline SSE stream.

Converts API-facing input types to shared pipeline types and resolves
scenario name strings to ScenarioConfig objects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.models import ScenarioConfig
from shared.models.candidates import BigFiveScores, CandidateData
from shared.models.scenarios import ScenarioName

if TYPE_CHECKING:
    from api.jobs.models import CandidateInput


def _convert_candidate_input(inputs: list[CandidateInput]) -> list[CandidateData]:
    """Convert API CandidateInput to shared CandidateData.

    Args:
        inputs: List of frontend-facing CandidateInput objects.

    Returns:
        List of CandidateData objects ready for pipeline consumption.
    """
    candidates: list[CandidateData] = []
    for inp in inputs:
        big_five: BigFiveScores | None = None
        if inp.big_five is not None:
            big_five = BigFiveScores(
                O=inp.big_five.get("O", 0.5),
                C=inp.big_five.get("C", 0.5),
                E=inp.big_five.get("E", 0.5),
                A=inp.big_five.get("A", 0.5),
                N=inp.big_five.get("N", 0.5),
            )
        candidates.append(
            CandidateData(
                name=inp.name,
                cv_text=inp.cv_text,
                big_five=big_five,
                personality_source=inp.personality_source,
            )
        )
    return candidates


def _resolve_scenario(name: str) -> ScenarioConfig:
    """Resolve scenario name string to ScenarioConfig with default weights.

    Args:
        name: Scenario name string (case-insensitive ScenarioName value).

    Returns:
        ScenarioConfig with an empty category_weights dict (defaults apply).

    Raises:
        ValueError: If the name is not a valid ScenarioName value.
    """
    try:
        scenario_name = ScenarioName(name.lower())
    except ValueError as exc:
        valid = [e.value for e in ScenarioName]
        raise ValueError(f"Unknown scenario {name!r}. Valid values: {valid}") from exc
    return ScenarioConfig(name=scenario_name, category_weights={})
