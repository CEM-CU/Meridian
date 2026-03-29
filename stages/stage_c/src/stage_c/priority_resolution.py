"""C2: Active Priority Resolution.

Deterministic function (zero LLM calls) that pairs each requirement with its
priority under the active scenario. Behavioral requirements (assessable_from_cv=False)
receive priority=None because they route to the personality layer regardless of priority.
"""

from shared.models import Priority, Requirement, ScenarioConfig


def resolve_active_priorities(
    requirements: list[Requirement],
    scenario: ScenarioConfig,
) -> list[tuple[Requirement, Priority | None]]:
    """Pair each requirement with its priority under the active scenario.

    Behavioral requirements (assessable_from_cv=False) get priority=None
    since they route to personality layer regardless of priority.

    Args:
        requirements: List of requirements produced by C1 JD extraction.
        scenario: Active scenario configuration carrying the scenario name.

    Returns:
        A list of (Requirement, Priority | None) tuples. CV-assessable
        requirements carry their resolved Priority; behavioral requirements
        carry None.
    """
    result: list[tuple[Requirement, Priority | None]] = []
    for req in requirements:
        if not req.assessable_from_cv:
            result.append((req, None))
        else:
            priority = req.scenario_priority.for_scenario(scenario.name.value)
            result.append((req, priority))
    return result
