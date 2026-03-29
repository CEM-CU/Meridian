"""Quality check definitions for Stage C output."""

from __future__ import annotations

from typing import Any

from shared.models import RubricLevel
from shared.models.pipeline import StageCOutput


def run_quality_checks(
    output: StageCOutput,
    cv_flags: list,
    candidates: list,
) -> list[dict[str, Any]]:
    """Run all quality checks and return list of {name, passed, detail}."""
    checks: list[dict[str, Any]] = []

    cv_reqs = [r for r in output.requirements if r.assessable_from_cv]
    beh_reqs = [r for r in output.requirements if not r.assessable_from_cv]

    # 1. Requirement count in range
    n = len(output.requirements)
    checks.append({"name": "Req count 6-18", "passed": 6 <= n <= 18, "detail": str(n)})

    # 2. Has behavioral reqs
    checks.append({"name": "Has behavioral reqs", "passed": len(beh_reqs) > 0, "detail": str(len(beh_reqs))})

    # 3. Assessment coverage: every (candidate x cv_req) has an assessment
    expected = len(cv_reqs) * len(candidates)
    actual = len(output.rubric_assessments)
    checks.append({"name": "Assessment coverage", "passed": actual == expected, "detail": f"{actual}/{expected}"})

    # 4. Behavioral reqs excluded from assessment
    assessed_ids = {a.requirement_id for a in output.rubric_assessments}
    beh_ids = {r.requirement_id for r in beh_reqs}
    checks.append({"name": "Behavioral exclusion", "passed": beh_ids.isdisjoint(assessed_ids), "detail": ""})

    # 5. Citation rate 100% for exceeds/meets/partial
    needs = [a for a in output.rubric_assessments if a.rubric_level in (RubricLevel.EXCEEDS, RubricLevel.MEETS, RubricLevel.PARTIAL)]
    has = [a for a in needs if a.cv_citation]
    rate = len(has) / len(needs) if needs else 1.0
    checks.append({"name": "Citation rate 100%", "passed": rate == 1.0, "detail": f"{rate:.0%} ({len(has)}/{len(needs)})"})

    # 6. No orphan flags
    valid_ids = {r.requirement_id for r in output.requirements}
    orphans = [f for f in cv_flags if f.requirement_id and f.requirement_id not in valid_ids]
    checks.append({"name": "No orphan flags", "passed": len(orphans) == 0, "detail": str(len(orphans))})

    # 7. Has GAP flags
    checks.append({"name": "Has GAP flags", "passed": any(f.name == "CV_GAP" for f in cv_flags), "detail": ""})

    # 8. Has EXCEEDS flags
    checks.append({"name": "Has EXCEEDS flags", "passed": any(f.name == "CV_EXCEEDS" for f in cv_flags), "detail": ""})

    # 9. Pydantic round-trip
    try:
        StageCOutput.model_validate_json(output.model_dump_json())
        checks.append({"name": "Pydantic round-trip", "passed": True, "detail": ""})
    except Exception as e:
        checks.append({"name": "Pydantic round-trip", "passed": False, "detail": str(e)[:80]})

    return checks
