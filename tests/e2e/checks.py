"""Quality check definitions for Stage C and Stage D output."""

from __future__ import annotations

from typing import Any

from shared.models import EvidenceType, RubricLevel
from shared.models.pipeline import AssessmentMode, StageCOutput, StageDOutput


def run_stage_c_checks(
    output: StageCOutput,
    cv_flags: list,
    candidates: list,
) -> list[dict[str, Any]]:
    """Run Stage C quality checks. Returns list of {name, passed, detail}."""
    checks: list[dict[str, Any]] = []

    cv_reqs = [r for r in output.requirements if r.assessable_from_cv]
    beh_reqs = [r for r in output.requirements if not r.assessable_from_cv]

    n = len(output.requirements)
    checks.append({"name": "C: Req count 6-18", "passed": 6 <= n <= 18, "detail": str(n)})
    checks.append({"name": "C: Has behavioral reqs", "passed": len(beh_reqs) > 0, "detail": str(len(beh_reqs))})

    expected = len(cv_reqs) * len(candidates)
    actual = len(output.rubric_assessments)
    checks.append({"name": "C: Assessment coverage", "passed": actual == expected, "detail": f"{actual}/{expected}"})

    assessed_ids = {a.requirement_id for a in output.rubric_assessments}
    beh_ids = {r.requirement_id for r in beh_reqs}
    checks.append({"name": "C: Behavioral exclusion", "passed": beh_ids.isdisjoint(assessed_ids), "detail": ""})

    needs = [a for a in output.rubric_assessments if a.rubric_level in (RubricLevel.EXCEEDS, RubricLevel.MEETS, RubricLevel.PARTIAL)]
    has = [a for a in needs if a.cv_citation]
    rate = len(has) / len(needs) if needs else 1.0
    checks.append({"name": "C: Citation rate 100%", "passed": rate == 1.0, "detail": f"{rate:.0%} ({len(has)}/{len(needs)})"})

    valid_ids = {r.requirement_id for r in output.requirements}
    orphans = [f for f in cv_flags if f.requirement_id and f.requirement_id not in valid_ids]
    checks.append({"name": "C: No orphan flags", "passed": len(orphans) == 0, "detail": str(len(orphans))})

    checks.append({"name": "C: Has GAP flags", "passed": any(f.name == "CV_GAP" for f in cv_flags), "detail": ""})
    checks.append({"name": "C: Has EXCEEDS flags", "passed": any(f.name == "CV_EXCEEDS" for f in cv_flags), "detail": ""})

    try:
        StageCOutput.model_validate_json(output.model_dump_json())
        checks.append({"name": "C: Pydantic round-trip", "passed": True, "detail": ""})
    except Exception as e:
        checks.append({"name": "C: Pydantic round-trip", "passed": False, "detail": str(e)[:80]})

    return checks


def run_stage_d_checks(
    stage_d_output: StageDOutput,
    candidates: list,
) -> list[dict[str, Any]]:
    """Run Stage D quality checks. Returns list of {name, passed, detail}."""
    checks: list[dict[str, Any]] = []

    # 1. StageDOutput has flags
    checks.append({
        "name": "D: Has flags",
        "passed": len(stage_d_output.flags) > 0,
        "detail": str(len(stage_d_output.flags)),
    })

    # 2. Every candidate has provenance
    prov_names = set(stage_d_output.provenance_per_candidate.keys())
    cand_names = {c.name for c in candidates}
    checks.append({
        "name": "D: Provenance for all candidates",
        "passed": cand_names == prov_names,
        "detail": f"{len(prov_names)}/{len(cand_names)}",
    })

    # 3. Provenance counts match actual flags
    for cand_name, prov in stage_d_output.provenance_per_candidate.items():
        cand_flags = [f for f in stage_d_output.flags if f.candidate_name == cand_name]
        actual_personality = sum(1 for f in cand_flags if f.evidence_type == EvidenceType.SCORED_FLAG)
        actual_cv = sum(1 for f in cand_flags if f.evidence_type != EvidenceType.SCORED_FLAG)
        count_match = (
            prov.personality_flag_count == actual_personality
            and prov.cv_flag_count == actual_cv
            and prov.total_flags == len(cand_flags)
        )
        checks.append({
            "name": f"D: Provenance counts [{cand_name}]",
            "passed": count_match,
            "detail": f"p={actual_personality} cv={actual_cv} total={len(cand_flags)}",
        })

    # 4. Partial mode candidates have zero personality flags
    for cand_name, prov in stage_d_output.provenance_per_candidate.items():
        if prov.assessment_mode == AssessmentMode.PARTIAL:
            checks.append({
                "name": f"D: Partial mode no personality [{cand_name}]",
                "passed": prov.personality_flag_count == 0,
                "detail": str(prov.personality_flag_count),
            })

    # 5. Full mode candidates have personality flags
    full_mode_candidates = [
        name for name, prov in stage_d_output.provenance_per_candidate.items()
        if prov.assessment_mode == AssessmentMode.FULL
    ]
    if full_mode_candidates:
        has_any_personality = any(
            stage_d_output.provenance_per_candidate[name].personality_flag_count > 0
            for name in full_mode_candidates
        )
        checks.append({
            "name": "D: Full mode has personality flags",
            "passed": has_any_personality,
            "detail": f"{len(full_mode_candidates)} full-mode candidates",
        })

    # 6. Flag count per candidate in reasonable range (3-25)
    for cand_name in cand_names:
        cand_flags = [f for f in stage_d_output.flags if f.candidate_name == cand_name]
        count = len(cand_flags)
        checks.append({
            "name": f"D: Flag count 3-25 [{cand_name}]",
            "passed": 3 <= count <= 25,
            "detail": str(count),
        })

    # 7. Passthrough fields intact
    checks.append({
        "name": "D: Requirements passed through",
        "passed": len(stage_d_output.confirmed_requirements) > 0,
        "detail": str(len(stage_d_output.confirmed_requirements)),
    })
    checks.append({
        "name": "D: Rubric matrix passed through",
        "passed": len(stage_d_output.rubric_matrix) > 0,
        "detail": str(len(stage_d_output.rubric_matrix)),
    })
    checks.append({
        "name": "D: Candidate data passed through",
        "passed": len(stage_d_output.candidate_data) == len(candidates),
        "detail": str(len(stage_d_output.candidate_data)),
    })

    # 8. Pydantic round-trip
    try:
        StageDOutput.model_validate_json(stage_d_output.model_dump_json())
        checks.append({"name": "D: Pydantic round-trip", "passed": True, "detail": ""})
    except Exception as e:
        checks.append({"name": "D: Pydantic round-trip", "passed": False, "detail": str(e)[:80]})

    return checks


# Backward compatibility alias
run_quality_checks = run_stage_c_checks
