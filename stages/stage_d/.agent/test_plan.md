# Stage D — Test Plan

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Unit Tests (pytest, zero LLM calls, zero network)

### D1: Personality Flags (test_personality_flags.py)
- For each scenario (5) × each dimension (5) × each threshold direction: verify correct flag fires/doesn't fire
- Boundary test: score exactly at threshold → flag fires (inclusive convention)
- Score just below threshold → flag does NOT fire
- With team context: collision flag fires when both candidate and team member have high E
- Without team context: no collision/complement/friction flags generated, no error
- No Big Five scores → empty list returned, no exception

### D1: Property Tests (hypothesis, test_personality_flags_props.py)
- Given random valid BigFiveScores + random valid ScenarioConfig → output is always list[Flag]
- Every flag in output has evidence_type=scored_flag
- Every flag has big_five_source in {"O","C","E","A","N"}
- Every flag has big_five_score matching the input score for that dimension
- No two flags have the same name for the same candidate (dedup invariant)
- Flag names are all in canonical vocabulary

### D2: CV Validation (test_cv_validation.py)
- Valid CV flags pass through unchanged
- Flag with invalid name (e.g., old "CV_SCOPE_GAP") → stripped, logged
- Flag with missing requirement_id → stripped
- Flag with priority metadata mismatching requirement's scenario_priority → stripped
- Flag with valid data → preserved with all metadata intact

### D3: Merge (test_merge.py)
- Personality + CV flags → merged list, personality first
- Empty personality (partial mode) → CV-only
- Empty CV (all MEETS) → personality-only
- Both empty → empty list

### D4: Validation Checks (test_validation.py)
- Check 1: personality flag with wrong threshold → caught. CV flag with mismatched rubric → caught
- Check 2 unconditional: contradictory personality flags → lower-priority removed
- Check 2 conditional: CV_EXCEEDS + CV_GAP same requirement_id → contradiction. CV_EXCEEDS + CV_GAP different req_id → NOT contradiction
- Check 3 personality: missing dimension → warning logged
- Check 3 requirements: requirement with no flag and no MEETS → error logged
- Check 4: positive CV + negative personality on same domain → advisory note generated
- Check 5: >25 flags → "noisy" warning. <3 flags → "thin" warning. 8-18 → no warning

### D5: Assessment Mode (test_mode.py)
- All 5 dimensions present → full
- 4 of 5 dimensions → partial
- Zero dimensions → partial
- Preset scores → full, provenance = "Preset archetype — {name}"
- Modified preset → full, provenance = "Modified preset — based on {name}"

### D6: Output Assembly (test_output.py)
- StageDOutput passes Pydantic validation
- Provenance counts match actual flag counts in output
- All pass-through fields (requirements, candidate_data, rubric_matrix, scenario) are identical to input

## Integration Test

### D Pipeline (test_d_pipeline.py)
- Mock StageCOutput from fixtures → run full D pipeline → verify StageDOutput
- Full mode candidate + partial mode candidate in same run → correct per-candidate mode
- Scenario switch: same input, different scenario → different personality flags, same CV flags (CV flags are scenario-independent at this point — priority was already baked in by C4)
