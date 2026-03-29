"""Incremental JSON result writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_results(path: Path, results: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    """Write results to JSON, overwriting each time. Called after every scenario."""
    payload = {
        "meta": meta,
        "results": results,
        "summary": _build_summary(results),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str))


def _build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_scenarios": len(results),
        "passed": sum(1 for r in results if r.get("status") == "passed"),
        "partial": sum(1 for r in results if r.get("status") == "partial"),
        "errors": sum(1 for r in results if r.get("status") == "error"),
        "total_checks_passed": sum(r.get("checks_passed", 0) for r in results),
        "total_checks": sum(r.get("checks_total", 0) for r in results),
        "total_latency_s": round(sum(r.get("latency_s", 0) for r in results), 1),
    }
