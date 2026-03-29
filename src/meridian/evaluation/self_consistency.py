"""E6: Self-consistency pre-computation (Layer 3b).

Runs the Stage E evaluation pipeline multiple times on the same StageDOutput
to detect instabilities in agent assessments. If a candidate's relative ranking
changes across runs, that instability is annotated in the output.

Stage C results are cached (scenario-independent). Stage D is deterministic.
Only Stage E's LLM calls (3 agents + 1 synthesis) vary between runs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from meridian.evaluation.agents.runner import run_agents
from meridian.evaluation.audit.runner import run_audit
from meridian.evaluation.layer0_validation import validate_stage_d_output
from meridian.evaluation.layer1_signals import Layer1Output, compute_layer1
from meridian.evaluation.synthesis.assembler import assemble_synthesis

if TYPE_CHECKING:
    from meridian.evaluation.synthesis.models import SynthesisOutput
    from meridian.extraction.protocols import LLMClient
    from meridian.models.pipeline import StageDOutput

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InstabilityAnnotation:
    """Annotation for a candidate whose ranking changed across runs."""

    candidate_name: str
    description: str
    run_rankings: tuple[int, ...]  # ranking position per run (1-indexed)


@dataclass(frozen=True)
class ConsistencyResult:
    """Result of self-consistency check."""

    num_runs: int
    is_consistent: bool  # True if no rankings changed
    annotations: tuple[InstabilityAnnotation, ...]
    run_summaries: tuple[str, ...]  # trade-off statements from each run


# ---------------------------------------------------------------------------
# Ranking extraction
# ---------------------------------------------------------------------------


def _extract_candidate_ranking(
    synthesis: SynthesisOutput,
) -> dict[str, int]:
    """Extract implicit ranking from synthesis output.

    Rank by: count of EXCEEDS cells (desc), then count of GAP cells (asc),
    then alphabetical. Returns candidate_name -> rank (1-indexed).
    """
    # Collect per-candidate cell stats from the trade-off matrix.
    exceeds_counts: dict[str, int] = {}
    gap_counts: dict[str, int] = {}

    for cell in synthesis.trade_off_matrix:
        name = cell.candidate_name
        if name not in exceeds_counts:
            exceeds_counts[name] = 0
            gap_counts[name] = 0
        if cell.rubric_level == "exceeds":
            exceeds_counts[name] += 1
        elif cell.rubric_level == "gap":
            gap_counts[name] += 1

    candidate_names = sorted(exceeds_counts.keys())

    # Sort: more EXCEEDS first, fewer GAPS first, then alphabetical.
    sorted_names = sorted(
        candidate_names,
        key=lambda n: (-exceeds_counts[n], gap_counts[n], n),
    )

    return {name: rank for rank, name in enumerate(sorted_names, start=1)}


# ---------------------------------------------------------------------------
# Ranking comparison
# ---------------------------------------------------------------------------


def _compare_rankings(
    rankings: list[dict[str, int]],
    candidate_names: list[str],
) -> list[InstabilityAnnotation]:
    """Compare rankings across runs. Return annotations for candidates
    whose rank changed in any run.

    Missing candidates in a ranking dict are assigned a sentinel value of
    len(candidate_names) + 1 (last place) and a warning is logged.
    """
    annotations: list[InstabilityAnnotation] = []
    sentinel = len(candidate_names) + 1

    for name in candidate_names:
        run_rankings_list: list[int] = []
        for i, r in enumerate(rankings):
            if name not in r:
                logger.warning(
                    "Candidate '%s' missing from run %d ranking dict; using sentinel %d",
                    name,
                    i + 1,
                    sentinel,
                )
                run_rankings_list.append(sentinel)
            else:
                run_rankings_list.append(r[name])
        run_rankings = tuple(run_rankings_list)
        unique_ranks = set(run_rankings)
        if len(unique_ranks) > 1:
            annotations.append(
                InstabilityAnnotation(
                    candidate_name=name,
                    description=(
                        f"Candidate '{name}' received different rankings across runs: "
                        + ", ".join(f"run {i + 1}=rank {r}" for i, r in enumerate(run_rankings))
                        + ". Agent assessment is not stable for this candidate."
                    ),
                    run_rankings=run_rankings,
                )
            )

    return annotations


# ---------------------------------------------------------------------------
# Single pipeline run (E1 + E2 once; E3 + E5 + E7 per run)
# ---------------------------------------------------------------------------


async def _run_single_evaluation(
    cleaned_stage_d: StageDOutput,
    candidate_names: list[str],
    assessment_modes: dict[str, str],
    layer1_output: Layer1Output,
    llm_client: LLMClient,
) -> SynthesisOutput:
    """Run one Stage E evaluation (E3 + E5 + E7) on pre-computed Layer 0/1 output.

    E1 (validation) and E2 (signals) are deterministic and already computed
    once by the caller. This function only re-runs the LLM-dependent layers.
    """
    # E3: Run 3 agents (3 LLM calls, parallel).
    verdicts = await run_agents(
        flags=cleaned_stage_d.flags,
        tension_map=layer1_output.tension_map,
        candidates=cleaned_stage_d.candidate_data,
        requirements=cleaned_stage_d.confirmed_requirements,
        assessment_modes=assessment_modes,
        llm_client=llm_client,
    )

    # E5: Audit (deterministic — 0 LLM calls).
    audited_verdicts, audit_warnings = run_audit(
        verdicts=verdicts,
        flags=cleaned_stage_d.flags,
        candidate_data=cleaned_stage_d.candidate_data,
        rubric_assessments=cleaned_stage_d.rubric_matrix,
        requirements=cleaned_stage_d.confirmed_requirements,
    )

    # E7: Synthesis (1 LLM call).
    synthesis = await assemble_synthesis(
        stage_d_output=cleaned_stage_d,
        layer1_output=layer1_output,
        audited_verdicts=audited_verdicts,
        audit_warnings=audit_warnings,
        llm_client=llm_client,
    )

    return synthesis


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_consistency_check(
    stage_d_output: StageDOutput,
    llm_client: LLMClient,
    num_runs: int = 3,
) -> ConsistencyResult:
    """Run Stage E pipeline num_runs times and compare rankings.

    Each run: E1 validation -> E2 signals -> E3 agents -> E5 audit -> E7 synthesis.
    E1 and E2 are deterministic (run once, cache). E3-E7 re-run each time.

    Args:
        stage_d_output: The Stage D output to evaluate.
        llm_client: Async LLM client satisfying the LLMClient protocol.
        num_runs: Number of times to run the LLM-dependent pipeline. Default 3.

    Returns:
        ConsistencyResult with stability annotations and per-run summaries.
    """
    if num_runs < 1:
        raise ValueError(f"num_runs must be >= 1, got {num_runs}")

    logger.info("Starting self-consistency check: %d runs", num_runs)

    # E1: Validate Stage D output (deterministic — run once).
    cleaned, validation_warnings = validate_stage_d_output(stage_d_output)
    if validation_warnings:
        logger.info("Layer 0 validation produced %d warnings", len(validation_warnings))

    # Derive candidate names and assessment modes (deterministic).
    candidate_names: list[str] = [c.name for c in cleaned.candidate_data]
    assessment_modes: dict[str, str] = {
        name: prov.assessment_mode.value for name, prov in cleaned.provenance_per_candidate.items()
    }

    # E2: Compute Layer 1 signals (deterministic — run once).
    layer1_output = compute_layer1(
        flags=cleaned.flags,
        scenario=cleaned.scenario,
        candidate_names=candidate_names,
        assessment_modes=assessment_modes,
    )

    # Run LLM-dependent pipeline num_runs times.
    all_rankings: list[dict[str, int]] = []
    run_summaries: list[str] = []

    for run_idx in range(num_runs):
        logger.debug("Self-consistency run %d/%d", run_idx + 1, num_runs)
        try:
            synthesis = await _run_single_evaluation(
                cleaned_stage_d=cleaned,
                candidate_names=candidate_names,
                assessment_modes=assessment_modes,
                layer1_output=layer1_output,
                llm_client=llm_client,
            )
        except Exception:
            logger.warning(
                "Self-consistency run %d/%d failed; skipping this run's ranking",
                run_idx + 1,
                num_runs,
                exc_info=True,
            )
            continue
        ranking = _extract_candidate_ranking(synthesis)
        all_rankings.append(ranking)
        run_summaries.append(synthesis.trade_off_statement)
        logger.debug("Run %d ranking: %s", run_idx + 1, ranking)

    # If we had failures and fewer than 2 successful runs survived, we cannot make a
    # meaningful stability comparison.  (num_runs=1 intentionally produces 1 run and
    # is always considered consistent — the guard only fires when runs were *lost* to errors.)
    successful_runs = len(all_rankings)
    if successful_runs < num_runs and successful_runs < 2:
        logger.warning(
            "Only %d successful run(s) out of %d requested; marking result as inconsistent",
            successful_runs,
            num_runs,
        )
        return ConsistencyResult(
            num_runs=num_runs,
            is_consistent=False,
            annotations=(),
            run_summaries=tuple(run_summaries),
        )

    # Compare rankings across runs.
    raw_annotations = _compare_rankings(all_rankings, candidate_names)
    is_consistent = len(raw_annotations) == 0

    logger.info(
        "Self-consistency check complete: %d runs, consistent=%s, %d annotation(s)",
        num_runs,
        is_consistent,
        len(raw_annotations),
    )

    return ConsistencyResult(
        num_runs=num_runs,
        is_consistent=is_consistent,
        annotations=tuple(raw_annotations),
        run_summaries=tuple(run_summaries),
    )
