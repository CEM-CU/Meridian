#!/usr/bin/env python3
"""Stage C E2E smoke test CLI.

Usage:
    export OPENROUTER_API_KEY="sk-or-..."
    uv run python tests/e2e/cli.py
    uv run python tests/e2e/cli.py --model anthropic/claude-sonnet-4 --all
    uv run python tests/e2e/cli.py --scenarios 3 --output results.json
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

# Ensure project root and tests/ are on sys.path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_TESTS_DIR = Path(__file__).resolve().parent.parent
for _p in [str(_PROJECT_ROOT), str(_TESTS_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn  # noqa: E402
from rich.table import Table  # noqa: E402

from shared.llm_client import OpenRouterClient  # noqa: E402

from e2e.registry import SCENARIOS  # noqa: E402
from e2e.runner import run_scenario  # noqa: E402
from e2e.writer import write_results  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage C E2E smoke test")
    parser.add_argument("--model", default="deepseek/deepseek-v3.2", help="OpenRouter model ID")
    parser.add_argument("--scenarios", type=int, default=3, help="Number of scenarios (1-9)")
    parser.add_argument("--output", default="tests/e2e/results.json", help="JSON output path")
    parser.add_argument("--all", action="store_true", help="Run all 9 scenarios")
    return parser.parse_args()


def print_summary(console: Console, results: list[dict]) -> None:
    """Print Rich summary table + per-candidate detail + failed checks."""
    # Main table
    table = Table(title="Results Summary")
    table.add_column("Scenario", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Checks", justify="center")
    table.add_column("Reqs", justify="center")
    table.add_column("Assessments", justify="center")
    table.add_column("Flags", justify="center")
    table.add_column("Time", justify="right")

    for r in results:
        status_map = {"error": "[red]ERROR[/]", "passed": "[green]PASS[/]", "partial": "[yellow]PARTIAL[/]"}
        status = status_map.get(r["status"], r["status"])
        checks = f"{r['checks_passed']}/{r['checks_total']}" if r.get("checks_total") else "-"
        table.add_row(
            r["scenario"], status, checks,
            str(r.get("requirements_total", "-")),
            str(r.get("assessments_total", "-")),
            str(r.get("flags_total", "-")),
            f"{r.get('latency_s', 0):.0f}s",
        )

    console.print()
    console.print(table)

    # Per-candidate breakdown
    for r in results:
        if not r.get("per_candidate"):
            continue
        console.print(f"\n[bold cyan]{r['scenario']}[/] candidates:")
        for cand_name, d in r["per_candidate"].items():
            mode = "full" if d["has_big_five"] else "partial"
            rubric = ", ".join(f"{k}={v}" for k, v in sorted(d["rubric"].items()))
            flags = ", ".join(f"{k}={v}" for k, v in sorted(d["flags"].items())) or "(none)"
            console.print(f"  [{mode:>7s}] {cand_name:25s} | {rubric}")
            console.print(f"  {'':9s} {'':25s} | flags: {flags}")

    # Failed checks
    any_fail = False
    for r in results:
        for c in r.get("checks", []):
            if not c["passed"]:
                if not any_fail:
                    console.print("\n[bold red]Failed Checks:[/]")
                    any_fail = True
                detail = f" ({c['detail']})" if c["detail"] else ""
                console.print(f"  [red]FAIL[/] {r['scenario']}: {c['name']}{detail}")

    # Totals
    tp = sum(r.get("checks_passed", 0) for r in results)
    tt = sum(r.get("checks_total", 0) for r in results)
    tl = sum(r.get("latency_s", 0) for r in results)
    te = sum(1 for r in results if r["status"] == "error")
    console.print(f"\n[bold]Total: {tp}/{tt} checks, {tl:.0f}s, {te} errors[/]")


async def main() -> None:
    args = parse_args()
    console = Console()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]ERROR: Set OPENROUTER_API_KEY environment variable[/]")
        sys.exit(1)

    n = len(SCENARIOS) if args.all else min(args.scenarios, len(SCENARIOS))
    scenarios = SCENARIOS[:n]
    output_path = Path(args.output)
    client = OpenRouterClient(model=args.model, max_tokens=4096, api_key=api_key)

    meta = {
        "model": args.model,
        "scenarios_requested": n,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "output_path": str(output_path),
    }

    console.print(Panel(
        f"[bold]Stage C E2E Smoke Test[/]\n"
        f"Model: [cyan]{args.model}[/]\n"
        f"Scenarios: [cyan]{n}[/]\n"
        f"Output: [cyan]{output_path}[/]",
        title="Config",
    ))

    results: list[dict] = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TimeElapsedColumn(),
        console=console,
    )

    with progress:
        # Create all progress tasks upfront
        task_ids = {
            module_name: progress.add_task(f"[cyan]{label}[/] queued...", total=1)
            for label, module_name in scenarios
        }

        # Launch all scenarios in parallel
        async def _run_and_collect(label: str, module_name: str) -> dict:
            result = await run_scenario(label, module_name, client, progress, task_ids[module_name])
            if not progress.tasks[task_ids[module_name]].completed:
                progress.update(task_ids[module_name], completed=True)
            return result

        results = await asyncio.gather(
            *[_run_and_collect(label, mod) for label, mod in scenarios]
        )
        results = list(results)

    # Write final results
    meta["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    write_results(output_path, results, meta)

    print_summary(console, results)
    console.print(f"Results written to: [cyan]{output_path}[/]")


if __name__ == "__main__":
    asyncio.run(main())
