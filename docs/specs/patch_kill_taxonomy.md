# Patch: Kill Taxonomy, Add Per-Requirement Scenario Priority

> Applies to: Stage C v1.1, Stage D v4.2, Stage E v4.2
> Generated March 28, 2026

---

## What Changes

Remove the 9-type requirement taxonomy from C1 extraction. Replace with two fields per requirement:

1. `assessable_from_cv` (boolean) — can a CV answer this? LLM is highly reliable on this distinction.
2. `scenario_priority` (object) — LLM assigns high/medium/low for each of the 5 scenarios during extraction, same call, zero additional cost.

The LLM judges "is post-acquisition integration experience critical under turnaround?" directly from the requirement text. This is more accurate than the two-hop proxy of "classify as leadership_context → look up leadership_context priority under turnaround → high."

---

## What Dies

- The `type` field on requirements (experience_depth, scope, technical, etc.) — gone.
- `SCENARIO_PRIORITY_DEFAULTS` mapping type → priority per scenario — gone. Replaced by per-requirement values from extraction.
- Specialized flag variants (`CV_SCOPE_GAP`, `CV_INDUSTRY_MISMATCH`, `CV_SCOPE_EXCEEDS`) — gone. Replaced by `CV_GAP` / `CV_EXCEEDS` / `CV_PARTIAL` + the requirement's scenario priority determines weight.
- Type-based validation checks (coverage across types, narrow extraction warning) — gone.
- Type-based agent allowlist differentiation for CV flags — simplified to EXPERIENCE_STRENGTH, EXPERIENCE_GAP, EVIDENCE_QUALITY, ROUTING.

---

## What Survives

- Behavioral routing: `assessable_from_cv: false` routes to the Big Five lookup table in Stage D (v4.2.1 patch). Unchanged.
- Scenario switch mechanism: matrix re-sorts by `scenario_priority[current_scenario]` per requirement. Faster to implement — direct read from cached extraction, no lookup table hop.
- Rubric-to-flag bridge: mapping is now rubric_level × scenario_priority → flag. Simpler: GAP + high → `CV_GAP` flag with high weight. EXCEEDS + high → `CV_EXCEEDS` flag. MEETS → no flag. Same logic, fewer flag names.
- Requirement drop detection, citation validation, confidence tagging, investigation questions — all unchanged.

---

## Net Effect

~15 minutes saved in build time. One fewer classification step that could hallucinate. Simpler flag vocabulary. Same demo capability — scenario switch still re-sorts the matrix and shifts which gaps matter.
