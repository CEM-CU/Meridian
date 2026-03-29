"""E8: Scenario switch wiring.

Caches scenario-independent data (C3 rubric assessments) and re-derives
everything downstream when the scenario changes. Supports both pre-computed
(demo) and live (judge test) scenario switching.

The re-evaluation path on scenario switch:
  C2: re-apply priorities (deterministic, <100ms)
  C4: re-bridge with new priorities (deterministic, <100ms)
  Stage D: full re-derive (deterministic, <100ms)
  Stage E: full re-evaluate (3 agent LLM calls + 1 synthesis call, ~10-13s)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from meridian.derivation.pipeline import run_stage_d
from meridian.evaluation.pipeline import run_stage_e
from meridian.extraction.bridge import bridge_rubric_to_flags
from meridian.extraction.cv_assessment import assess_all_candidates
from meridian.extraction.jd_extraction import extract_requirements
from meridian.extraction.priority_resolution import resolve_active_priorities
from meridian.models import ScenarioConfig
from meridian.models.pipeline import StageCOutput

if TYPE_CHECKING:
    from meridian.evaluation.synthesis.models import SynthesisOutput
    from meridian.extraction.protocols import LLMClient
    from meridian.models import CandidateData, Flag, Requirement, RubricAssessment
    from meridian.models.pipeline import StageDOutput

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class CachedPipelineState:
    """Cached scenario-independent pipeline state.

    Holds results from C1 (JD extraction) and C3 (rubric assessments).
    These are scenario-independent and can be reused across scenario switches
    without re-running any LLM calls.
    """

    requirements: list[Requirement]
    rubric_assessments: list[RubricAssessment]
    candidates: list[CandidateData]
    extraction_warnings: list[str]


@dataclass
class ScenarioResult:
    """Complete result for a single scenario evaluation.

    Packages every output stage produced for one scenario so callers can
    switch between pre-computed results without re-evaluating.
    """

    scenario: ScenarioConfig
    stage_c_output: StageCOutput
    stage_d_output: StageDOutput
    synthesis: SynthesisOutput
    cv_flags: list[Flag]
    warnings: list[str]


# ---------------------------------------------------------------------------
# C1 + C3 — scenario-independent setup
# ---------------------------------------------------------------------------


async def build_cached_state(
    jd_text: str,
    candidates: list[CandidateData],
    llm_client: LLMClient,
) -> CachedPipelineState:
    """Run C1 + C3 once. These results are scenario-independent.

    C2 is NOT run here — it needs a scenario. C4 is NOT run — it needs priorities.
    C3 requires a scenario for prompt ordering; we use DIGITAL_TRANSFORMATION as
    a neutral reference because rubric assessment is per-requirement, and the
    scenario only affects which requirements appear first in the prompt — not the
    rubric level assigned. Rubric levels are intrinsic to the CV evidence.

    Args:
        jd_text: Raw job description text.
        candidates: Candidate data including raw CV text.
        llm_client: Async LLM client satisfying the LLMClient protocol.

    Returns:
        CachedPipelineState with requirements and rubric_assessments ready
        for reuse across all scenario evaluations.
    """
    from meridian.models import ScenarioName

    # C1: Extract requirements (scenario-independent)
    requirements, extraction_warnings = await extract_requirements(jd_text, llm_client)
    logger.info("C1 complete (cached): %d requirements extracted", len(requirements))

    # C3: Assess all candidates — scenario used only for prompt ordering; levels are invariant
    reference_scenario = ScenarioConfig(name=ScenarioName.DIGITAL_TRANSFORMATION, category_weights={})
    rubric_assessments = await assess_all_candidates(candidates, requirements, reference_scenario, llm_client)
    logger.info("C3 complete (cached): %d rubric assessments", len(rubric_assessments))

    return CachedPipelineState(
        requirements=requirements,
        rubric_assessments=rubric_assessments,
        candidates=candidates,
        extraction_warnings=extraction_warnings,
    )


# ---------------------------------------------------------------------------
# Single scenario evaluation
# ---------------------------------------------------------------------------


def _run_c2_c4(
    cached: CachedPipelineState,
    scenario: ScenarioConfig,
) -> tuple[StageCOutput, list[Flag]]:
    """Run C2 (priority resolution) and C4 (rubric-to-flag bridge) deterministically.

    Both are sub-100ms and need no LLM calls. Returns the StageCOutput contract
    and the CV flags produced by the bridge.
    """
    # C2: Resolve active priorities for the new scenario (result used for ordering
    #     and metadata; C4 also reads priorities via the requirement model directly)
    _priority_pairs = resolve_active_priorities(cached.requirements, scenario)
    logger.debug("C2 complete: priorities resolved for scenario=%s", scenario.name)

    # C4: Bridge rubric assessments into CV-derived flags using new scenario priorities
    cv_flags = bridge_rubric_to_flags(cached.rubric_assessments, cached.requirements, scenario.name)
    logger.debug("C4 complete: %d CV flags produced", len(cv_flags))

    stage_c_output = StageCOutput(
        requirements=cached.requirements,
        rubric_assessments=cached.rubric_assessments,
        candidate_data=cached.candidates,
        scenario=scenario,
    )
    return stage_c_output, cv_flags


async def evaluate_scenario(
    cached: CachedPipelineState,
    scenario: ScenarioConfig,
    llm_client: LLMClient,
) -> ScenarioResult:
    """Evaluate a single scenario using cached C1/C3 data.

    Runs: C2 → C4 → Stage D → Stage E. C1 and C3 are not re-called.

    Args:
        cached: Pre-built state from build_cached_state (C1 + C3 results).
        scenario: Target scenario configuration to evaluate against.
        llm_client: Async LLM client satisfying the LLMClient protocol.

    Returns:
        ScenarioResult with all stage outputs for the given scenario.
    """
    all_warnings: list[str] = list(cached.extraction_warnings)

    # C2 + C4: deterministic, <100ms
    stage_c_output, cv_flags = _run_c2_c4(cached, scenario)
    logger.info("C2+C4 complete for scenario=%s: %d CV flags", scenario.name, len(cv_flags))

    # Stage D: deterministic, <100ms
    stage_d_output = run_stage_d(stage_c_output, cv_flags)
    logger.info("Stage D complete for scenario=%s", scenario.name)

    # Stage E: 3 LLM calls + 1 synthesis (~10-13s)
    synthesis, e_warnings = await run_stage_e(stage_d_output, llm_client)
    all_warnings.extend(e_warnings)
    logger.info("Stage E complete for scenario=%s", scenario.name)

    return ScenarioResult(
        scenario=scenario,
        stage_c_output=stage_c_output,
        stage_d_output=stage_d_output,
        synthesis=synthesis,
        cv_flags=cv_flags,
        warnings=all_warnings,
    )


# ---------------------------------------------------------------------------
# Multi-scenario pre-computation (demo mode)
# ---------------------------------------------------------------------------


async def precompute_scenarios(
    jd_text: str,
    candidates: list[CandidateData],
    scenarios: list[ScenarioConfig],
    llm_client: LLMClient,
) -> dict[str, ScenarioResult]:
    """Pre-compute multiple scenarios (demo mode).

    Runs C1 + C3 once, then evaluates each scenario concurrently using
    asyncio.gather. Returns a mapping of scenario_name → ScenarioResult.

    Args:
        jd_text: Raw job description text.
        candidates: Candidate data including raw CV text.
        scenarios: List of scenario configurations to evaluate.
        llm_client: Async LLM client satisfying the LLMClient protocol.

    Returns:
        Dict mapping scenario name string → ScenarioResult.
    """
    # C1 + C3 once — scenario-independent
    cached = await build_cached_state(jd_text, candidates, llm_client)
    logger.info(
        "Cached state built: %d requirements, %d assessments",
        len(cached.requirements),
        len(cached.rubric_assessments),
    )

    # All scenarios evaluated concurrently (each runs D + E independently).
    # return_exceptions=True isolates failures — a single bad scenario does not abort the rest.
    raw_results = await asyncio.gather(
        *[evaluate_scenario(cached, s, llm_client) for s in scenarios],
        return_exceptions=True,
    )
    results: dict[str, ScenarioResult] = {}
    for scenario, result in zip(scenarios, raw_results, strict=True):
        if isinstance(result, Exception):
            logger.error("Scenario %s failed: %s", scenario.name.value, result)
        else:
            results[result.scenario.name.value] = result  # type: ignore[union-attr]
    return results


# ---------------------------------------------------------------------------
# Live scenario switch (judge test mode)
# ---------------------------------------------------------------------------


async def switch_scenario(
    cached: CachedPipelineState,
    new_scenario: ScenarioConfig,
    llm_client: LLMClient,
) -> ScenarioResult:
    """Live scenario switch (judge test mode).

    Uses cached C1/C3 data. Re-runs C2 → C4 → D → E.
    Expected latency: ~10-13s (3 agent calls + 1 synthesis).

    Args:
        cached: Pre-built state from build_cached_state (C1 + C3 results).
        new_scenario: The scenario to switch to.
        llm_client: Async LLM client satisfying the LLMClient protocol.

    Returns:
        ScenarioResult for the new scenario.
    """
    logger.info("Scenario switch: evaluating scenario=%s", new_scenario.name)
    return await evaluate_scenario(cached, new_scenario, llm_client)
