# Stage D — Task List

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Overview

Stage D converts raw signals (Big Five scores + CV rubric assessments) into a unified, validated flag set. Zero LLM calls. Entirely deterministic Python. This is the firewall between noisy upstream data and the auditable evaluation pipeline downstream. Latency: <1s.

## Tasks (ordered by dependency)

### D1: Personality Flag Derivation [NOT STARTED]
- **Blocked by:** shared models (Flag, BigFiveScores, ScenarioConfig)
- **Input:** BigFiveScores per candidate + ScenarioConfig + optional TeamMember list
- **Output:** list[Flag] with evidence_type=scored_flag
- **LLM calls:** 0
- **Implementation:**
  - Trait threshold logic: each Big Five dimension × scenario → threshold check → flag
  - Flags generated include: EXECUTION_CONSCIENTIOUSNESS_FIT (C above threshold + scenario requires execution), COLLISION_DUAL_DOMINANCE (candidate E high + existing team member E high), DERAILMENT_NEUROTICISM_UNDER_STRESS (N above risk threshold), and similar
  - Threshold values are scenario-dependent: high openness is positive under digital_transformation but not under stabilization
  - Team context flags (COMPLEMENT_*, COLLISION_*, FRICTION_*) require existing team Big Five profiles. Without team context, these flags are not generated — not an error, just reduced scope
  - Every flag carries: big_five_source (O/C/E/A/N), big_five_score, threshold_used, topic_keywords
  - Assessment mode gating: if Big Five scores unavailable → skip entire stream, set assessment_mode=partial
- **Key design decision:** Define thresholds as a config dict, not hardcoded. Makes tuning easy without code changes. Structure: `{scenario: {dimension: {flag_name: threshold_value, direction: "above"|"below"}}}`
- **Tests:** For each scenario × dimension, verify correct flag fires at boundary. Test with scores exactly at threshold (boundary behavior). Test without team context → no complementarity/collision flags. Test without Big Five → empty list + partial mode.

### D2: CV Flag Stream Validation [NOT STARTED]
- **Blocked by:** C4 output format (Flag model)
- **Input:** list[Flag] from C4 bridge
- **Output:** list[Flag] (validated, potentially stripped of invalid flags)
- **LLM calls:** 0
- **Implementation:**
  - Verify every flag name exists in canonical CV flag vocabulary: CV_GAP, CV_PARTIAL, CV_EXCEEDS, CV_BEHAVIORAL_ROUTED, CV_LOW_CONFIDENCE_CLUSTER, CV_SYSTEMATIC_GAP
  - Verify every CV flag has: requirement_id, rubric_level, evidence_type in {cv_rubric, requirement_gap, cv_pattern, routing}
  - Verify requirement_id references a requirement in the confirmed list
  - Verify flag metadata contains valid active_priority matching the requirement's scenario_priority for the active scenario
  - On any violation: strip flag, log, continue
- **Tests:** Valid flags pass through unchanged. Flag with invalid name → stripped. Flag with missing requirement_id → stripped. Flag with mismatched priority metadata → stripped.

### D3: Merge [NOT STARTED]
- **Blocked by:** D1 + D2
- **Input:** personality flags + validated CV flags
- **Output:** merged list[Flag] (personality first, then CV — deterministic ordering)
- **LLM calls:** 0
- **Implementation:**
  - Simple concatenation. No deduplication, no conflict resolution, no cross-stream weighting
  - Personality flags first, then CV flags — for deterministic ordering in audit and agent inputs
  - A candidate might have 6 personality + 8 CV = 14 flags. This is correct — different evidence streams
- **Tests:** Merge preserves all flags from both streams. Order is personality-first. Empty personality stream (partial mode) → CV-only output.

### D4: Validation Layer 0 (5 Checks) [NOT STARTED]
- **Blocked by:** D3
- **Input:** merged flag set + Big Five scores + requirement list + rubric assessments
- **Output:** validated flag set + warnings list + coherence notes
- **LLM calls:** 0
- **Implementation:**
  - **Check 1: Flag-Score Consistency.** Personality: verify threshold match. CV: verify flag's rubric_level matches the actual rubric assessment data (a CV_GAP flag must reference a GAP rubric level). Cross-stream: NOT checked (personality+CV are independent).
  - **Check 2: Mutual Exclusivity.** Unconditional contradictions (personality pairs like EXECUTION_LOW_CONSCIENTIOUSNESS_RISK vs EXECUTION_CONSCIENTIOUSNESS_FIT): flag names alone. Conditional contradictions (CV_EXCEEDS vs CV_GAP on SAME requirement_id): must compare requirement_ids — only contradicts if same requirement. Different requirement_ids are fine. On contradiction: remove lower-confidence flag (CV: use confidence tag; personality: lower severity×priority product).
  - **Check 3: Dimension Coverage.** Personality: all 5 Big Five dimensions have ≥1 flag (full mode only). Requirements: every CV-assessable requirement has either a flag OR rubric_level=meets. Missing → log.
  - **Check 4: Cross-Stream Coherence (advisory).** Positive CV flag + negative personality flag on same domain → advisory note. Does NOT block pipeline.
  - **Check 5: Flag Count Reasonableness (advisory).** >25 per candidate → warn "noisy." <3 → warn "thin." Expected: 8-18.
- **Tests:** Test each check independently with crafted flag sets. Contradiction removal picks correct flag. Requirement coverage catches missing requirements. Cross-stream coherence detects tension. Count check fires at boundaries.

### D5: Assessment Mode Determination [NOT STARTED]
- **Blocked by:** shared models
- **Input:** CandidateData per candidate
- **Output:** AssessmentMode per candidate + provenance metadata
- **LLM calls:** 0
- **Implementation:**
  - Per-candidate (not global): Big Five scores present for all 5 dimensions → full. Otherwise → partial.
  - Preset handling: preset Big Five scores treated as full mode. Provenance records source: "Preset archetype — {name}" or "Modified preset — based on {name} with manual adjustments"
  - Mode flows into agent prompt preambles (Stage E) and provenance header
- **Tests:** Candidate with all 5 scores → full. Candidate missing any dimension → partial. Preset → full with correct provenance string.

### D6: Output Assembly [NOT STARTED]
- **Blocked by:** D3 + D4 + D5
- **Input:** validated flags + mode per candidate + all upstream data
- **Output:** StageDOutput (the contract Stage E consumes)
- **Implementation:**
  - Assemble FlagProvenance per candidate: personality_flag_count, cv_flag_count, total, big_five_available, requirements_assessed, high_priority_gap_count, dimension_coverage_warnings, cross_stream_coherence_notes
  - Pass through: confirmed_requirements, candidate_data (with raw CV text), rubric_matrix, scenario
- **Tests:** StageDOutput validates against Pydantic schema. All pass-through fields present. Provenance counts match actual flag counts.

### D Integration Test [NOT STARTED]
- **Blocked by:** D1-D6
- **Input:** Mock StageCOutput (from fixtures)
- **Output:** Valid StageDOutput
- **Checks:** Flag count in expected range, no validation errors, correct assessment mode per candidate, provenance metadata consistent
