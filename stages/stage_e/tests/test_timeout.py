"""Tests for E9: Timeout + Graceful Degradation (F16).

Covers:
- run_with_timeout: success path, timeout path, exception propagation
- build_degradation_notice: 1 missing, 2 missing, empty list
- is_viable_result: all verdicts, partial verdicts, all None, empty dict
"""

from __future__ import annotations

import asyncio

import pytest
from stage_e.schemas import AgentEvidenceType, AgentRole, AgentVerdict, Claim, EvidenceBasis
from stage_e.timeout import build_degradation_notice, is_viable_result, run_with_timeout

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_verdict(role: str = AgentRole.ROLE_FIT) -> AgentVerdict:
    """Return a minimal valid AgentVerdict for use in tests."""
    claim = Claim(
        text="Candidate has strong operational background.",
        evidence_basis=EvidenceBasis(type=AgentEvidenceType.SCORED_FLAG, reference="HIGH_CONSCIENTIOUSNESS"),
        confidence="high",
        candidate_name="Alice",
    )
    return AgentVerdict(
        agent_role=role,
        claims=[claim],
        summary="Candidate demonstrates a solid track record across all evaluated dimensions.",
        assessment_mode="full",
        unaddressed_flags=[],
    )


async def _fast_coro(value: int = 42) -> int:
    """Coroutine that completes immediately."""
    return value


async def _slow_coro(delay: float = 30.0) -> int:
    """Coroutine that sleeps longer than any test timeout."""
    await asyncio.sleep(delay)
    return 999


async def _error_coro() -> int:
    """Coroutine that raises a non-timeout exception."""
    raise ValueError("deliberate test error")


# ---------------------------------------------------------------------------
# run_with_timeout tests
# ---------------------------------------------------------------------------


class TestRunWithTimeout:
    """Tests for run_with_timeout."""

    async def test_successful_coro_returns_result(self) -> None:
        """A coroutine that completes within the timeout returns its value."""
        result = await run_with_timeout(_fast_coro(7), timeout_seconds=5.0)
        assert result == 7

    async def test_slow_coro_returns_none_on_timeout(self) -> None:
        """A coroutine that exceeds the timeout returns None instead of blocking."""
        result = await run_with_timeout(_slow_coro(delay=30.0), timeout_seconds=0.05)
        assert result is None

    async def test_exception_in_coro_propagates(self) -> None:
        """Non-timeout exceptions are not swallowed — they propagate to the caller."""
        with pytest.raises(ValueError, match="deliberate test error"):
            await run_with_timeout(_error_coro(), timeout_seconds=5.0)

    async def test_timeout_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """A timeout emits a WARNING-level log entry mentioning the agent role."""
        import logging

        with caplog.at_level(logging.WARNING, logger="stage_e.timeout"):
            await run_with_timeout(_slow_coro(delay=30.0), timeout_seconds=0.05, agent_role="risk")

        assert any("risk" in record.message and "timed out" in record.message for record in caplog.records)


# ---------------------------------------------------------------------------
# build_degradation_notice tests
# ---------------------------------------------------------------------------


class TestBuildDegradationNotice:
    """Tests for build_degradation_notice."""

    def test_one_missing_agent_team_dynamics(self) -> None:
        """Single missing team_dynamics agent produces the canonical notice."""
        notice = build_degradation_notice([AgentRole.TEAM_DYNAMICS])
        assert "Team dynamics" in notice
        assert "unavailable" in notice
        assert "role-fit" in notice
        assert "risk" in notice

    def test_one_missing_agent_role_fit(self) -> None:
        """Single missing role_fit agent mentions the correct remaining agents."""
        notice = build_degradation_notice([AgentRole.ROLE_FIT])
        assert "Role-fit" in notice
        assert "unavailable" in notice
        assert "team dynamics" in notice
        assert "risk" in notice

    def test_two_missing_agents_produces_combined_message(self) -> None:
        """Two missing agents produce a combined notice covering only the remaining one."""
        notice = build_degradation_notice([AgentRole.ROLE_FIT, AgentRole.RISK])
        # Both missing roles named
        assert "Role-fit" in notice
        assert "risk" in notice
        # Only remaining agent referenced in "covers" part
        assert "team dynamics" in notice
        assert "unavailable" in notice

    def test_empty_list_returns_empty_string(self) -> None:
        """No missing agents → empty string (no notice needed)."""
        assert build_degradation_notice([]) == ""

    def test_all_agents_missing_no_covers_clause(self) -> None:
        """All three agents missing → notice contains no 'evaluation covers' clause."""
        notice = build_degradation_notice([AgentRole.ROLE_FIT, AgentRole.TEAM_DYNAMICS, AgentRole.RISK])
        assert "unavailable" in notice
        assert "no agent assessments available" in notice

    def test_single_agent_uses_singular_noun(self) -> None:
        """One missing agent → 'assessment' (singular), not 'assessments'."""
        notice = build_degradation_notice([AgentRole.RISK])
        assert " assessment " in notice or notice.endswith(" assessment")
        assert "assessments" not in notice

    def test_two_missing_agents_uses_plural_noun(self) -> None:
        """Two missing agents → 'assessments' (plural)."""
        notice = build_degradation_notice([AgentRole.ROLE_FIT, AgentRole.TEAM_DYNAMICS])
        assert "assessments" in notice


# ---------------------------------------------------------------------------
# is_viable_result tests
# ---------------------------------------------------------------------------


class TestIsViableResult:
    """Tests for is_viable_result."""

    def test_three_verdicts_is_viable(self) -> None:
        """All three agents returned verdicts → viable."""
        results: dict[str, AgentVerdict | None] = {
            AgentRole.ROLE_FIT: _make_verdict(AgentRole.ROLE_FIT),
            AgentRole.TEAM_DYNAMICS: _make_verdict(AgentRole.TEAM_DYNAMICS),
            AgentRole.RISK: _make_verdict(AgentRole.RISK),
        }
        assert is_viable_result(results) is True

    def test_two_verdicts_one_none_is_viable(self) -> None:
        """Two verdicts + one timeout → still viable (2-agent = 80% useful)."""
        results: dict[str, AgentVerdict | None] = {
            AgentRole.ROLE_FIT: _make_verdict(AgentRole.ROLE_FIT),
            AgentRole.TEAM_DYNAMICS: None,
            AgentRole.RISK: _make_verdict(AgentRole.RISK),
        }
        assert is_viable_result(results) is True

    def test_one_verdict_two_none_is_viable(self) -> None:
        """One verdict + two timeouts → still viable (better than frozen screen)."""
        results: dict[str, AgentVerdict | None] = {
            AgentRole.ROLE_FIT: None,
            AgentRole.TEAM_DYNAMICS: None,
            AgentRole.RISK: _make_verdict(AgentRole.RISK),
        }
        assert is_viable_result(results) is True

    def test_all_none_is_not_viable(self) -> None:
        """All agents timed out → not viable, synthesis cannot proceed."""
        results: dict[str, AgentVerdict | None] = {
            AgentRole.ROLE_FIT: None,
            AgentRole.TEAM_DYNAMICS: None,
            AgentRole.RISK: None,
        }
        assert is_viable_result(results) is False

    def test_empty_dict_is_not_viable(self) -> None:
        """Empty results dict → not viable."""
        assert is_viable_result({}) is False
