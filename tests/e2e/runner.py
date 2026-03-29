"""Scenario execution logic — runs Stage C → D → E pipeline and collects metrics."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from rich.progress import Progress, TaskID
from stage_c.pipeline import run_stage_c
from stage_c.schemas import C1_REQUIREMENTS_SCHEMA, C3_ASSESSMENTS_SCHEMA
from stage_d.pipeline import run_stage_d
from stage_e.pipeline import run_stage_e

from e2e.checks import run_stage_c_checks, run_stage_d_checks, run_stage_e_checks
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
    """Run a single scenario through Stage C + Stage D. Updates progress at each checkpoint."""
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

        # --- Stage C ---
        if use_structured:
            progress.update(task_id, description=f"[cyan]{name}[/] Stage C (structured)...")
        else:
            progress.update(task_id, description=f"[cyan]{name}[/] Stage C...")

        t0 = time.time()
        stage_c_output, cv_flags, c_warnings = await run_stage_c(
            jd_text=jd_text,
            candidates=candidates,
            scenario=scenario_config,
            llm_client=client,
            c1_response_format=c1_fmt,
            c3_response_format=c3_fmt,
        )
        c_elapsed = time.time() - t0
        result["stage_c_latency_s"] = round(c_elapsed, 1)
        result["stage_c_warnings"] = c_warnings

        # Stage C checks
        c_checks = run_stage_c_checks(stage_c_output, cv_flags, candidates)
        result["stage_c_checks"] = c_checks

        # --- Stage D ---
        progress.update(task_id, description=f"[cyan]{name}[/] Stage D...")
        t1 = time.time()
        stage_d_output = run_stage_d(stage_c_output, cv_flags)
        d_elapsed = time.time() - t1
        result["stage_d_latency_s"] = round(d_elapsed, 3)

        # Stage D checks
        d_checks = run_stage_d_checks(stage_d_output, candidates)
        result["stage_d_checks"] = d_checks

        # --- Stage E ---
        progress.update(task_id, description=f"[cyan]{name}[/] Stage E (agents)...")
        t2 = time.time()
        synthesis, e_warnings = await run_stage_e(stage_d_output, client)
        e_elapsed = time.time() - t2
        result["stage_e_latency_s"] = round(e_elapsed, 1)
        result["stage_e_warnings"] = e_warnings

        # Stage E checks
        e_checks = run_stage_e_checks(synthesis, candidates, e_warnings)
        result["stage_e_checks"] = e_checks

        # Combined metrics
        total_elapsed = c_elapsed + d_elapsed + e_elapsed
        result["latency_s"] = round(total_elapsed, 1)
        all_checks = c_checks + d_checks + e_checks
        passed = sum(1 for c in all_checks if c["passed"])
        result["checks"] = all_checks
        result["checks_passed"] = passed
        result["checks_total"] = len(all_checks)

        # Extract detailed metrics
        result.update(_extract_metrics(stage_c_output, cv_flags, stage_d_output, synthesis, candidates))

        result["status"] = "passed" if passed == len(all_checks) else "partial"
        progress.update(
            task_id,
            description=f"[green]{name}[/] {passed}/{len(all_checks)} checks  {total_elapsed:.0f}s",
            completed=True,
        )

    except Exception as e:
        result["status"] = "error"
        result["error"] = f"{type(e).__name__}: {e}"
        progress.update(task_id, description=f"[red]{name}[/] ERROR: {type(e).__name__}")

    return result


def _extract_metrics(
    stage_c_output: object,
    cv_flags: list,
    stage_d_output: object,
    synthesis: object,
    candidates: list,
) -> dict[str, Any]:
    """Extract structured metrics from Stage C, D, and E outputs."""
    sc = stage_c_output  # type: ignore[assignment]
    sd = stage_d_output  # type: ignore[assignment]
    se = synthesis  # type: ignore[assignment]

    cv_reqs = [r for r in sc.requirements if r.assessable_from_cv]
    beh_reqs = [r for r in sc.requirements if not r.assessable_from_cv]

    per_candidate: dict[str, Any] = {}
    for cand in candidates:
        # Stage C metrics
        cand_assessments = [a for a in sc.rubric_assessments if a.candidate_name == cand.name]
        cand_cv_flags = [f for f in cv_flags if f.candidate_name == cand.name]
        level_counts: dict[str, int] = {}
        for a in cand_assessments:
            level_counts[a.rubric_level.value] = level_counts.get(a.rubric_level.value, 0) + 1
        cv_flag_counts: dict[str, int] = {}
        for f in cand_cv_flags:
            cv_flag_counts[f.name] = cv_flag_counts.get(f.name, 0) + 1

        # Stage D metrics
        cand_d_flags = [f for f in sd.flags if f.candidate_name == cand.name]
        d_flag_counts: dict[str, int] = {}
        for f in cand_d_flags:
            d_flag_counts[f.name] = d_flag_counts.get(f.name, 0) + 1
        prov = sd.provenance_per_candidate.get(cand.name)

        per_candidate[cand.name] = {
            "rubric": level_counts,
            "cv_flags": cv_flag_counts,
            "d_flags": d_flag_counts,
            "assessment_count": len(cand_assessments),
            "cv_flag_count": len(cand_cv_flags),
            "d_total_flags": len(cand_d_flags),
            "d_personality_flags": prov.personality_flag_count if prov else 0,
            "d_cv_flags": prov.cv_flag_count if prov else 0,
            "has_big_five": cand.big_five is not None,
            "assessment_mode": prov.assessment_mode.value if prov else "unknown",
        }

    return {
        "requirements_total": len(sc.requirements),
        "requirements_cv": len(cv_reqs),
        "requirements_behavioral": len(beh_reqs),
        "assessments_total": len(sc.rubric_assessments),
        "cv_flags_total": len(cv_flags),
        "d_flags_total": len(sd.flags),
        "e_matrix_cells": len(se.trade_off_matrix),
        "e_contested_signals": len(se.contested_signals),
        "e_trade_off_statement_len": len(se.trade_off_statement),
        "per_candidate": per_candidate,
        "requirements_detail": [
            {"id": r.requirement_id, "text": r.text, "assessable": r.assessable_from_cv}
            for r in sc.requirements
        ],
    }
