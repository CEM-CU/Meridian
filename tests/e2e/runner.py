"""Scenario execution logic — runs Stage C pipeline and collects metrics."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rich.progress import Progress, TaskID

from shared.models.pipeline import StageCOutput
from stage_c.pipeline import run_stage_c
from stage_c.schemas import C1_REQUIREMENTS_SCHEMA, C3_ASSESSMENTS_SCHEMA

from e2e.checks import run_quality_checks
from e2e.registry import load_scenario

# Models that support OpenAI-style structured outputs via response_format.
_STRUCTURED_OUTPUT_PREFIXES: tuple[str, ...] = ("openai/gpt-4.1", "openai/gpt-5", "openai/gpt-4o")

if TYPE_CHECKING:
    from shared.llm_client import OpenRouterClient


async def run_scenario(
    name: str,
    module_name: str,
    client: OpenRouterClient,
    progress: Progress,
    task_id: TaskID,
) -> dict[str, Any]:
    """Run a single scenario end-to-end. Updates progress at each checkpoint."""
    result: dict[str, Any] = {
        "scenario": name,
        "module": module_name,
        "status": "running",
    }

    try:
        # Load
        progress.update(task_id, description=f"[cyan]{name}[/] loading...")
        jd_text, candidates, scenario_config = load_scenario(module_name)
        result["jd_chars"] = len(jd_text)
        result["candidate_count"] = len(candidates)
        result["scenario_type"] = scenario_config.name.value

        # Determine if structured output is supported for this model
        use_structured = any(client.model.startswith(p) for p in _STRUCTURED_OUTPUT_PREFIXES)
        c1_fmt = C1_REQUIREMENTS_SCHEMA if use_structured else None
        c3_fmt = C3_ASSESSMENTS_SCHEMA if use_structured else None
        if use_structured:
            progress.update(task_id, description=f"[cyan]{name}[/] calling LLM (structured)...")
        else:
            progress.update(task_id, description=f"[cyan]{name}[/] calling LLM...")

        # Run pipeline
        t0 = time.time()
        output, cv_flags, warnings = await run_stage_c(
            jd_text=jd_text,
            candidates=candidates,
            scenario=scenario_config,
            llm_client=client,
            c1_response_format=c1_fmt,
            c3_response_format=c3_fmt,
        )
        elapsed = time.time() - t0
        result["latency_s"] = round(elapsed, 1)

        # Metrics
        result.update(_extract_metrics(output, cv_flags, warnings, candidates))

        # Quality checks
        progress.update(task_id, description=f"[cyan]{name}[/] checking quality...")
        checks = run_quality_checks(output, cv_flags, candidates)
        passed = sum(1 for c in checks if c["passed"])
        result["checks"] = checks
        result["checks_passed"] = passed
        result["checks_total"] = len(checks)
        result["status"] = "passed" if passed == len(checks) else "partial"

        progress.update(
            task_id,
            description=f"[green]{name}[/] {passed}/{len(checks)} checks  {elapsed:.0f}s",
            completed=True,
        )

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"{type(e).__name__}: {e}"
        progress.update(task_id, description=f"[red]{name}[/] ERROR: {type(e).__name__}")

    return result


def _extract_metrics(
    output: StageCOutput,
    cv_flags: list,
    warnings: list[str],
    candidates: list,
) -> dict[str, Any]:
    """Extract structured metrics from pipeline output."""
    cv_reqs = [r for r in output.requirements if r.assessable_from_cv]
    beh_reqs = [r for r in output.requirements if not r.assessable_from_cv]

    per_candidate: dict[str, Any] = {}
    for cand in candidates:
        cand_assessments = [a for a in output.rubric_assessments if a.candidate_name == cand.name]
        cand_flags = [f for f in cv_flags if f.candidate_name == cand.name]
        level_counts: dict[str, int] = {}
        for a in cand_assessments:
            level_counts[a.rubric_level.value] = level_counts.get(a.rubric_level.value, 0) + 1
        flag_counts: dict[str, int] = {}
        for f in cand_flags:
            flag_counts[f.name] = flag_counts.get(f.name, 0) + 1
        per_candidate[cand.name] = {
            "rubric": level_counts,
            "flags": flag_counts,
            "assessment_count": len(cand_assessments),
            "flag_count": len(cand_flags),
            "has_big_five": cand.big_five is not None,
        }

    return {
        "requirements_total": len(output.requirements),
        "requirements_cv": len(cv_reqs),
        "requirements_behavioral": len(beh_reqs),
        "assessments_total": len(output.rubric_assessments),
        "flags_total": len(cv_flags),
        "warnings": warnings,
        "per_candidate": per_candidate,
        "requirements_detail": [
            {"id": r.requirement_id, "text": r.text, "assessable": r.assessable_from_cv}
            for r in output.requirements
        ],
    }
