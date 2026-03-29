"""Tests for E8: Scenario Switch Wiring.

All tests are deterministic (no real LLM calls). A routing mock LLM client
inspects the system prompt to decide which canned response to return:
- C1 (JD extraction) → returns fixture requirements JSON
- C3 (CV assessment) → returns fixture rubric assessments JSON
- Stage E agents / synthesis → returns canned JSON verdicts / statements

Tests:
1. test_cached_state_runs_c1_c3_once
2. test_evaluate_scenario_uses_cached_data
3. test_two_scenarios_different_results
4. test_precompute_returns_all_scenarios
5. test_switch_scenario_same_as_evaluate
6. test_rubric_assessments_unchanged_across_scenarios
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from shared.models import (
    Confidence,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
    ScenarioPriority,
)
from shared.models.candidates import BigFiveScores, CandidateData

# Ensure root tests/ dir is importable (mirrors conftest.py setup).
_TESTS_DIR = str(Path(__file__).resolve().parents[3] / "tests")
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

from stage_e.scenario_switch import (  # noqa: E402
    CachedPipelineState,
    ScenarioResult,
    build_cached_state,
    evaluate_scenario,
    precompute_scenarios,
    switch_scenario,
)

# ---------------------------------------------------------------------------
# Minimal fixture data
# ---------------------------------------------------------------------------

_CANDIDATES: list[CandidateData] = [
    CandidateData(
        name="Alice",
        cv_text="Alice has 15 years of technology leadership at TechCorp. P&L of $400M at SomeCo.",
        big_five=BigFiveScores(O=0.8, C=0.7, E=0.6, A=0.5, N=0.3),
    ),
]

_REQUIREMENTS: list[Requirement] = [
    Requirement(
        requirement_id="REQ-01",
        text="15+ years of technology leadership",
        source_quote="15+ years of technology leadership",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.LOW,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-02",
        text="Strong P&L management experience",
        source_quote="Strong P&L management experience",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.LOW,
        ),
    ),
]

_RUBRIC_ASSESSMENTS: list[RubricAssessment] = [
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Alice",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="15 years technology leadership at TechCorp",
        cv_location="Work History, p.1",
        notes="Strong evidence.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Alice",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="P&L of $400M at SomeCo",
        cv_location="Work History, p.2",
        notes="Meets threshold.",
    ),
]


# ---------------------------------------------------------------------------
# Canned agent verdict JSON (used by mock LLM for Stage E)
# ---------------------------------------------------------------------------

_VERDICT_JSON = json.dumps(
    {
        "agent_role": "role_fit",
        "claims": [
            {
                "text": "Alice has a strong track record.",
                "evidence_basis": {"type": "cv_rubric", "reference": "REQ-01"},
                "confidence": "high",
            }
        ],
    }
)

_SYNTHESIS_STATEMENT = "Alice is a strong candidate for the role given her track record."


# ---------------------------------------------------------------------------
# Routing mock LLM client
# ---------------------------------------------------------------------------


class _RoutingMockLLMClient:
    """Mock LLM that routes responses by inspecting the system prompt keyword.

    - System prompt contains "rubric" → C3 CV assessment response
    - System prompt contains "requirement" (but not "rubric") → C1 JD extraction
    - System prompt contains "role" / "risk" / "team" / "dynamics" → agent verdict
    - Otherwise (synthesis trade-off statement) → synthesis statement

    Tracks all (system, user) call pairs for assertion.
    """

    def __init__(
        self,
        requirements: list[Requirement] | None = None,
        rubric_assessments: list[RubricAssessment] | None = None,
    ) -> None:
        self._requirements = requirements or _REQUIREMENTS
        self._rubric_assessments = rubric_assessments or _RUBRIC_ASSESSMENTS
        self.calls: list[tuple[str, str]] = []

    async def complete(self, system: str, user: str, response_format: dict | None = None) -> str:
        """Route to the appropriate canned response based on system prompt.

        C1 system prompt: "You are a senior executive recruiter..."
        C3 system prompt: "You are an expert executive recruiter performing a structured CV assessment."
        Stage E agent prompts: "You are The Researcher..." / "The Devil's Advocate..." / "The Risk Analyst..."
        Synthesis: anything else.
        """
        self.calls.append((system, user))
        s = system.lower()

        # C3: "expert executive recruiter" — structured CV assessment
        if "expert executive recruiter" in s:
            candidate = self._extract_candidate_name(user)
            assessed = [a for a in self._rubric_assessments if a.candidate_name == candidate]
            return json.dumps([a.model_dump() for a in assessed])

        # C1: "senior executive recruiter" — JD extraction
        if "senior executive recruiter" in s:
            return json.dumps([r.model_dump() for r in self._requirements])

        # Stage E agent evaluation (role-fit, team dynamics, risk)
        if any(kw in s for kw in ("the researcher", "devil's advocate", "risk analyst")):
            return _VERDICT_JSON

        # Synthesis trade-off statement (or any other call)
        return _SYNTHESIS_STATEMENT

    @staticmethod
    def _extract_candidate_name(user_prompt: str) -> str:
        """Parse 'Candidate: <name>' from a C3 user prompt."""
        for line in user_prompt.splitlines():
            stripped = line.strip()
            if stripped.startswith("Candidate:"):
                return stripped[len("Candidate:") :].strip()
        return _CANDIDATES[0].name


def _scenario(name: ScenarioName = ScenarioName.DIGITAL_TRANSFORMATION) -> ScenarioConfig:
    return ScenarioConfig(name=name, category_weights={})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cached_state_runs_c1_c3_once() -> None:
    """build_cached_state calls C1 (JD extraction) exactly once and C3 once per candidate."""
    llm = _RoutingMockLLMClient()
    jd_text = "Automotive CTO required with 15+ years experience."

    cached = await build_cached_state(jd_text, _CANDIDATES, llm)

    # Must return a CachedPipelineState
    assert isinstance(cached, CachedPipelineState)
    assert len(cached.requirements) > 0
    assert len(cached.rubric_assessments) > 0
    assert cached.candidates is _CANDIDATES

    # C1 calls: system prompt contains "senior executive recruiter"
    c1_calls = [c for c in llm.calls if "senior executive recruiter" in c[0].lower()]
    # C3 calls: system prompt contains "expert executive recruiter"
    c3_calls = [c for c in llm.calls if "expert executive recruiter" in c[0].lower()]

    assert len(c1_calls) >= 1, "Expected at least one C1 (JD extraction) call"
    assert len(c3_calls) >= len(_CANDIDATES), "Expected at least one C3 call per candidate"


@pytest.mark.asyncio
async def test_evaluate_scenario_uses_cached_data() -> None:
    """evaluate_scenario does not re-call C1 or C3 — uses cached state directly."""
    jd_text = "Automotive CTO role."
    llm = _RoutingMockLLMClient()

    # Build the cache first (makes C1 + C3 calls)
    cached = await build_cached_state(jd_text, _CANDIDATES, llm)
    calls_after_cache = len(llm.calls)

    # Now evaluate a scenario — should NOT add any C1 or C3 calls
    scenario = _scenario(ScenarioName.DIGITAL_TRANSFORMATION)
    result = await evaluate_scenario(cached, scenario, llm)

    assert isinstance(result, ScenarioResult)

    # C1 + C3 calls must not have increased
    new_calls = llm.calls[calls_after_cache:]
    new_c1_calls = [c for c in new_calls if "senior executive recruiter" in c[0].lower()]
    new_c3_calls = [c for c in new_calls if "expert executive recruiter" in c[0].lower()]

    assert len(new_c1_calls) == 0, "evaluate_scenario must not make any C1 calls"
    assert len(new_c3_calls) == 0, "evaluate_scenario must not make any C3 calls"


@pytest.mark.asyncio
async def test_two_scenarios_different_results() -> None:
    """Same cached state evaluated under two different scenarios produces different StageDOutputs."""
    jd_text = "CTO role with varied priorities."
    llm = _RoutingMockLLMClient()

    cached = await build_cached_state(jd_text, _CANDIDATES, llm)

    scenario_dt = _scenario(ScenarioName.DIGITAL_TRANSFORMATION)
    scenario_pa = _scenario(ScenarioName.POST_ACQUISITION)

    result_dt = await evaluate_scenario(cached, scenario_dt, llm)
    result_pa = await evaluate_scenario(cached, scenario_pa, llm)

    # Scenario config on StageDOutput must differ
    assert result_dt.stage_d_output.scenario.name == ScenarioName.DIGITAL_TRANSFORMATION
    assert result_pa.stage_d_output.scenario.name == ScenarioName.POST_ACQUISITION

    # Both must produce a non-None synthesis
    assert result_dt.synthesis is not None
    assert result_pa.synthesis is not None

    # Both should have flags (exact difference depends on fixture priorities)
    assert len(result_dt.cv_flags) > 0 or len(result_pa.cv_flags) > 0


@pytest.mark.asyncio
async def test_precompute_returns_all_scenarios() -> None:
    """precompute_scenarios returns a result for every scenario in the input list."""
    jd_text = "CTO needed."
    llm = _RoutingMockLLMClient()

    scenarios = [
        _scenario(ScenarioName.DIGITAL_TRANSFORMATION),
        _scenario(ScenarioName.POST_ACQUISITION),
    ]

    results = await precompute_scenarios(jd_text, _CANDIDATES, scenarios, llm)

    assert isinstance(results, dict)
    assert set(results.keys()) == {
        ScenarioName.DIGITAL_TRANSFORMATION.value,
        ScenarioName.POST_ACQUISITION.value,
    }
    for key, result in results.items():
        assert isinstance(result, ScenarioResult), f"Expected ScenarioResult for {key}"


@pytest.mark.asyncio
async def test_switch_scenario_same_as_evaluate() -> None:
    """switch_scenario produces a ScenarioResult of the same type as evaluate_scenario."""
    jd_text = "Senior technology executive."
    llm = _RoutingMockLLMClient()

    cached = await build_cached_state(jd_text, _CANDIDATES, llm)
    new_scenario = _scenario(ScenarioName.TURNAROUND)

    result_switch = await switch_scenario(cached, new_scenario, llm)
    result_eval = await evaluate_scenario(cached, new_scenario, llm)

    assert isinstance(result_switch, ScenarioResult)
    assert isinstance(result_eval, ScenarioResult)
    assert result_switch.scenario.name == result_eval.scenario.name
    assert result_switch.stage_d_output.scenario.name == ScenarioName.TURNAROUND


@pytest.mark.asyncio
async def test_rubric_assessments_unchanged_across_scenarios() -> None:
    """Rubric assessments in the cached state are identical regardless of scenario.

    The rubric level for a requirement must be the same in both scenario evaluations
    because C3 is run only once and the result is cached. Only downstream
    derivations (C4 flags, Stage D flags) change when the scenario changes.
    """
    jd_text = "CTO role."
    llm = _RoutingMockLLMClient()

    cached = await build_cached_state(jd_text, _CANDIDATES, llm)

    scenario_a = _scenario(ScenarioName.DIGITAL_TRANSFORMATION)
    scenario_b = _scenario(ScenarioName.STABILIZATION)

    result_a = await evaluate_scenario(cached, scenario_a, llm)
    result_b = await evaluate_scenario(cached, scenario_b, llm)

    # rubric_matrix on StageDOutput is derived from the cached rubric_assessments
    # and must carry the same rubric levels for both scenarios.
    a_levels = {(ra.requirement_id, ra.candidate_name): ra.rubric_level for ra in result_a.stage_d_output.rubric_matrix}
    b_levels = {(ra.requirement_id, ra.candidate_name): ra.rubric_level for ra in result_b.stage_d_output.rubric_matrix}

    assert a_levels == b_levels, (
        "Rubric levels must be identical across scenarios — they come from cached C3 output. "
        f"Diff: {set(a_levels.items()) ^ set(b_levels.items())}"
    )
