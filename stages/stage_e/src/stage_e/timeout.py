"""E9: Timeout + graceful degradation (F16).

Provides timeout wrappers for async agent calls and utilities for handling
partial results when one or more agents time out.

Per-agent timeout is 15 seconds. On timeout the runner receives None for that
agent's result. The synthesis step uses ``is_viable_result`` to decide whether
to proceed and ``build_degradation_notice`` to surface missing assessments to
the reader.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from stage_e.schemas import AgentRole, AgentVerdict

if TYPE_CHECKING:
    from collections.abc import Coroutine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role-to-description mapping used in human-readable notices
# ---------------------------------------------------------------------------

_ROLE_DESCRIPTIONS: dict[str, str] = {
    AgentRole.ROLE_FIT: "role-fit",
    AgentRole.TEAM_DYNAMICS: "team dynamics",
    AgentRole.RISK: "risk",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_with_timeout[T](
    coro: Coroutine[Any, Any, T],
    timeout_seconds: float = 15.0,
    agent_role: str = "unknown",
) -> T | None:
    """Run a coroutine with a timeout. Returns None on timeout.

    Wraps *coro* in ``asyncio.wait_for``. If the coroutine does not complete
    within *timeout_seconds* the task is cancelled, a warning is logged, and
    ``None`` is returned so the caller can continue with partial results.

    Any exception other than ``TimeoutError`` propagates to the caller
    unchanged — this function never silently swallows non-timeout errors.

    Args:
        coro: The coroutine to run.
        timeout_seconds: Maximum seconds to wait before cancelling.
        agent_role: Human-readable role label used in log output only.

    Returns:
        The coroutine's return value, or ``None`` if it timed out.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except TimeoutError:
        logger.warning(
            "Agent '%s' timed out after %.1fs — result excluded from synthesis",
            agent_role,
            timeout_seconds,
        )
        return None


def build_degradation_notice(missing_agents: list[str]) -> str:
    """Build a human-readable notice about missing agent assessments.

    Called when one or more agents timed out so the synthesis layer can
    surface a clear explanation to the reader.

    Examples::

        >>> build_degradation_notice([AgentRole.TEAM_DYNAMICS])
        'Team dynamics assessment unavailable — evaluation covers role-fit and risk only'

        >>> build_degradation_notice([AgentRole.ROLE_FIT, AgentRole.RISK])
        'Role-fit and risk assessments unavailable — evaluation covers team dynamics only'

        >>> build_degradation_notice([])
        ''

    Args:
        missing_agents: List of ``AgentRole`` values (strings) that did not
            produce a verdict.

    Returns:
        A single-sentence notice string, or an empty string when no agents
        are missing.
    """
    if not missing_agents:
        return ""

    # Build the "unavailable" part
    missing_labels = [_role_description(role) for role in missing_agents]
    if len(missing_labels) == 1:
        unavailable = missing_labels[0].capitalize()
    else:
        unavailable = ", ".join(label.capitalize() for label in missing_labels[:-1]) + " and " + missing_labels[-1]

    # Build the "covers" part — roles that are NOT missing
    all_roles = [r.value for r in AgentRole]
    present_roles = [r for r in all_roles if r not in missing_agents]
    if present_roles:
        present_labels = [_role_description(r) for r in present_roles]
        covers = present_labels[0] if len(present_labels) == 1 else " and ".join(present_labels)
        suffix = f" — evaluation covers {covers} only"
    else:
        suffix = " — no agent assessments available"

    # Pluralise "assessment" / "assessments"
    noun = "assessment" if len(missing_labels) == 1 else "assessments"
    return f"{unavailable} {noun} unavailable{suffix}"


def is_viable_result(results: dict[str, AgentVerdict | None]) -> bool:
    """Check if we have enough agent results for a meaningful synthesis.

    A result set is viable when at least one agent returned a verdict. The
    rule reflects the product's design decision (F16): 2-agent output is 80%
    as useful as 3-agent output; a frozen screen is 0%.

    Args:
        results: Mapping of agent role string to ``AgentVerdict`` or ``None``.
            An empty dict is treated as non-viable.

    Returns:
        ``True`` if at least one value in *results* is a non-``None``
        ``AgentVerdict``, ``False`` otherwise.
    """
    if not results:
        return False
    return any(verdict is not None for verdict in results.values())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _role_description(role: str) -> str:
    """Return the human-readable description for *role*, falling back to the raw value."""
    return _ROLE_DESCRIPTIONS.get(role, role)
