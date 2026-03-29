"""Allowlist definitions for Stage E Layer 2 evaluation agents.

Each agent receives only flags whose category is in its allowlist.
No agent sees all 15 categories — independence is preserved.
"""

from meridian.models.flags import Flag, FlagCategory

# ---------------------------------------------------------------------------
# Agent allowlists (frozen, immutable)
# ---------------------------------------------------------------------------

ROLE_FIT_ALLOWLIST: frozenset[FlagCategory] = frozenset(
    {
        FlagCategory.EXECUTION,
        FlagCategory.STRATEGIC,
        FlagCategory.CULTURAL,
        FlagCategory.EXPERIENCE_STRENGTH,
        FlagCategory.EXPERIENCE_GAP,
    }
)

TEAM_DYNAMICS_ALLOWLIST: frozenset[FlagCategory] = frozenset(
    {
        FlagCategory.COLLISION,
        FlagCategory.COMPLEMENT,
        FlagCategory.FRICTION,
        FlagCategory.GROUPTHINK,
        FlagCategory.INTEGRATION,
        FlagCategory.ROUTING,
    }
)

RISK_ALLOWLIST: frozenset[FlagCategory] = frozenset(
    {
        FlagCategory.DERAILMENT,
        FlagCategory.DARK_SIDE,
        FlagCategory.TENURE,
        FlagCategory.EXPERIENCE_GAP,
        FlagCategory.EVIDENCE_QUALITY,
    }
)


def filter_flags_for_agent(
    flags: list[Flag],
    allowlist: frozenset[FlagCategory],
) -> list[Flag]:
    """Return only the flags whose category is in the agent's allowlist.

    Args:
        flags: Full merged flag set from Layer 1.
        allowlist: The agent-specific set of permitted FlagCategory values.

    Returns:
        New list containing only flags whose category is in the allowlist.
        Original list is not mutated.
    """
    return [flag for flag in flags if flag.category in allowlist]
