"""Layer 2 parallel agent runner.

Runs 3 independent evaluation agents (role_fit, team_dynamics, risk) in parallel
via asyncio.gather. Each agent receives only the flags matching its allowlist.
Per-agent timeout: 15s (F16). Timed-out agents return None.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from meridian.evaluation.agents.allowlists import (
    RISK_ALLOWLIST,
    ROLE_FIT_ALLOWLIST,
    TEAM_DYNAMICS_ALLOWLIST,
    filter_flags_for_agent,
)
from meridian.evaluation.agents.prompts.risk import build_risk_prompt
from meridian.evaluation.agents.prompts.role_fit import build_role_fit_prompt
from meridian.evaluation.agents.prompts.team_dynamics import build_team_dynamics_prompt
from meridian.evaluation.schemas import AgentRole, AgentVerdict

if TYPE_CHECKING:
    from meridian.evaluation.layer1_signals import TensionPair
    from meridian.extraction.protocols import LLMClient
    from meridian.models import CandidateData, Flag, Requirement

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent configuration
# ---------------------------------------------------------------------------

_AGENT_CONFIGS: list[tuple[AgentRole, frozenset, object]] = [
    (AgentRole.ROLE_FIT, ROLE_FIT_ALLOWLIST, build_role_fit_prompt),
    (AgentRole.TEAM_DYNAMICS, TEAM_DYNAMICS_ALLOWLIST, build_team_dynamics_prompt),
    (AgentRole.RISK, RISK_ALLOWLIST, build_risk_prompt),
]


# ---------------------------------------------------------------------------
# Single agent execution
# ---------------------------------------------------------------------------


async def _run_single_agent(
    role: AgentRole,
    flags: list[Flag],
    tension_map: list[TensionPair],
    candidates: list[CandidateData],
    requirements: list[Requirement],
    assessment_modes: dict[str, str],
    prompt_builder: object,
    llm_client: LLMClient,
    timeout_seconds: float,
) -> AgentVerdict | None:
    """Run a single evaluation agent with timeout handling.

    Returns AgentVerdict on success, None on timeout or parse failure.
    """
    try:
        system_prompt, user_prompt = prompt_builder(  # type: ignore[operator]
            flags=flags,
            tension_pairs=tension_map,
            candidates=candidates,
            requirements=requirements,
            assessment_modes=assessment_modes,
        )
        raw = await asyncio.wait_for(
            llm_client.complete(
                system=system_prompt,
                user=user_prompt,
                response_format={"type": "json_object"},
            ),
            timeout=timeout_seconds,
        )
        return _parse_agent_response(raw, role)
    except TimeoutError:
        logger.warning("Agent '%s' timed out after %.1fs", role.value, timeout_seconds)
        return None
    except Exception:
        logger.exception("Agent '%s' raised an unexpected error", role.value)
        return None


def _parse_agent_response(raw: str, role: AgentRole) -> AgentVerdict | None:
    """Parse and validate raw LLM JSON response into an AgentVerdict.

    Returns None if parsing or validation fails.
    """
    try:
        data = json.loads(raw)
        # Ensure agent_role matches the expected role (agent may not set it correctly)
        data["agent_role"] = role.value
        return AgentVerdict.model_validate(data)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Agent '%s' returned invalid JSON/schema: %s", role.value, exc)
        return None


# ---------------------------------------------------------------------------
# Public runner
# ---------------------------------------------------------------------------


async def run_agents(
    flags: list[Flag],
    tension_map: list[TensionPair],
    candidates: list[CandidateData],
    requirements: list[Requirement],
    assessment_modes: dict[str, str],
    llm_client: LLMClient,
    timeout_seconds: float = 15.0,
) -> dict[str, AgentVerdict | None]:
    """Run 3 evaluation agents in parallel via asyncio.gather.

    Each agent receives only flags matching its allowlist. Agents run concurrently;
    a timed-out or errored agent returns None (F16 graceful degradation).

    Args:
        flags: Full validated flag set from Layer 1.
        tension_map: Tension pairs from Layer 1 (shared across all agents).
        candidates: All candidate data.
        requirements: Confirmed JD requirement list.
        assessment_modes: Candidate name → "full" or "partial".
        llm_client: Async LLM client satisfying the LLMClient protocol.
        timeout_seconds: Per-agent timeout in seconds. Default 15.0.

    Returns:
        Dict mapping agent role string to AgentVerdict (or None if timed out/failed).
        Keys: "role_fit", "team_dynamics", "risk".
    """
    tasks = []
    role_order: list[str] = []

    for role, allowlist, prompt_builder in _AGENT_CONFIGS:
        agent_flags = filter_flags_for_agent(flags, allowlist)
        tasks.append(
            _run_single_agent(
                role=role,
                flags=agent_flags,
                tension_map=tension_map,
                candidates=candidates,
                requirements=requirements,
                assessment_modes=assessment_modes,
                prompt_builder=prompt_builder,
                llm_client=llm_client,
                timeout_seconds=timeout_seconds,
            )
        )
        role_order.append(role.value)

    results = await asyncio.gather(*tasks)

    verdicts: dict[str, AgentVerdict | None] = {
        role: verdict for role, verdict in zip(role_order, results, strict=True)
    }

    successful = sum(1 for v in verdicts.values() if v is not None)
    logger.info(
        "Layer 2 complete: %d/%d agents returned verdicts",
        successful,
        len(_AGENT_CONFIGS),
    )
    return verdicts
