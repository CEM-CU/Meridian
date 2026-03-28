# Stage C — Test Plan

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Unit Tests (pytest, no LLM calls)

### C1 Validation (test_c1_validation.py)
- Schema check catches missing fields, wrong types, non-sequential IDs, missing scenario_priority fields
- Schema check verifies scenario_priority has all 5 scenarios with valid Priority values
- Duplicate detection flags two requirements with >60% keyword overlap
- Duplicate detection does NOT flag <60% overlap (legitimately different)
- Routing consistency: assessable_from_cv=false requirements have scenario_priority ignored downstream (no auto-correction needed, just advisory)
- Priority values are valid (high/medium/low only, no nulls, no unknown values)

### C2 Priority Resolution (test_c2_resolution.py)
- Same requirements, different active scenario → different resolved priorities
- Behavioral requirements (assessable_from_cv=false) → priority is None/sentinel regardless of scenario
- Each of 5 scenarios resolves correctly from scenario_priority field on requirement

### C4 Bridge (test_c4_bridge.py)
- GAP on high-priority → CV_GAP with priority=high in metadata
- GAP on medium-priority → CV_GAP with priority=medium in metadata
- GAP on low-priority → no flag
- PARTIAL on high-priority → CV_PARTIAL with priority=high
- EXCEEDS on high-priority → CV_EXCEEDS with priority=high
- EXCEEDS on medium-priority → CV_EXCEEDS with priority=medium
- MEETS → no flag
- NOT_ASSESSABLE on behavioral → CV_BEHAVIORAL_ROUTED
- Pattern: 3+ low-confidence → CV_LOW_CONFIDENCE_CLUSTER
- Pattern: >50% high-priority GAP → CV_SYSTEMATIC_GAP
- Pattern: >60% EXCEEDS → metadata warning, NOT a flag
- Every generated flag has valid provenance chain (requirement_id, rubric_level, evidence_type, active_priority)
- topic_keywords are non-empty and derived from requirement text
- Scenario switch: same rubric assessments, different scenario → different flags (priority thresholds shift)

### C4 Property Tests (hypothesis)
- Flag count ≤ requirement_count + 3 per candidate (3 = max pattern flags)
- Every flag.requirement_id references a valid requirement in the input list
- Every flag.evidence_type is one of {cv_rubric, requirement_gap, cv_pattern, routing}
- No duplicate flags per candidate (same name + same requirement_id)
- MEETS-only input → zero flags

## Mock LLM Tests (structured fixtures, no API calls)

### C1 Extraction (test_c1_extraction.py)
- Valid LLM response → parsed into list[Requirement] correctly
- LLM returns non-JSON → error handled, logged
- LLM returns JSON with extra fields → ignored (strict parsing)
- LLM returns fewer than 6 requirements → warning generated
- LLM returns more than 18 requirements → consolidation suggestion

### C3 Assessment (test_c3_assessment.py)
- Valid LLM response → parsed into list[RubricAssessment] correctly
- LLM drops a requirement → drop detection fires, follow-up triggered
- LLM returns MEETS without citation → downgraded to GAP, CITATION_MISSING logged
- LLM returns EXCEEDS without citation → downgraded to GAP
- LLM returns GAP with citation → citation ignored (GAP means nothing found)
- All assessments for a short CV are GAP → 70% threshold warning fires

## Integration Tests (@pytest.mark.integration, skip by default)

### C1→C2→C3→C4 Pipeline (test_c_pipeline.py)
- Synthetic BMW CTO JD → extract requirements → assign priorities → assess 3 CVs → bridge to flags
- Verify: requirement count in 8-15 range, all priorities assigned, all candidates assessed, flag count per candidate in 3-15 range, no validation errors
- This test hits real (cheap) LLM — run manually before demo, not in CI
