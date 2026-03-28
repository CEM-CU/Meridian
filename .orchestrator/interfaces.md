# Inter-Stage Contracts (Canonical)

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)
>
> THIS FILE IS THE SOURCE OF TRUTH for what crosses stage boundaries.
> Every Pydantic model listed here lives in `shared/src/shared/models/`.
> When a model changes, mark consumers as STALE and list what changed.

---

## Contract 1: Stage C → Stage D

**Model:** `StageCOutput` (shared.models.pipeline)

| Field | Type | Description |
|---|---|---|
| requirements | list[Requirement] | Confirmed JD requirements with per-scenario priorities (from C1 extraction) |
| rubric_assessments | list[RubricAssessment] | Per-requirement per-candidate rubric evaluations (from C3) |
| candidate_data | list[CandidateData] | Name, raw CV text, Big Five scores (if any), personality source |
| scenario | ScenarioConfig | Selected scenario with priority defaults and category weights |

**Producer:** Stage C (C4 assembles)
**Consumers:**

| Consumer | consumers_verified | Notes |
|---|---|---|
| Stage D: merge | 2026-03-29 (bootstrap) | Consumes rubric_assessments → CV flags via bridge |
| Stage D: assessment mode | 2026-03-29 (bootstrap) | Reads candidate_data.big_five presence |
| Stage E: Layer 2 agents | 2026-03-29 (bootstrap) | Agents receive confirmed_requirements for context |
| Stage E: F04 audit | 2026-03-29 (bootstrap) | Uses candidate_data.cv_text as ground truth |
| Stage E: synthesis | 2026-03-29 (bootstrap) | Uses rubric_assessments for trade-off matrix |

---

## Contract 2: Stage D → Stage E

**Model:** `StageDOutput` (shared.models.pipeline)

| Field | Type | Description |
|---|---|---|
| flags | list[Flag] | Merged validated flag set, personality + CV-derived |
| provenance_per_candidate | dict[str, FlagProvenance] | Per-candidate metadata (mode, counts, warnings) |
| confirmed_requirements | list[Requirement] | Pass-through from Stage C for agent context |
| candidate_data | list[CandidateData] | Pass-through — raw CV text for F04 |
| rubric_matrix | list[RubricAssessment] | Pass-through — for synthesis trade-off matrix |
| scenario | ScenarioConfig | Pass-through — for Layer 1 weight application |

**Producer:** Stage D (output assembly)
**Consumers:**

| Consumer | consumers_verified | Notes |
|---|---|---|
| Stage E: Layer 0 | 2026-03-29 (bootstrap) | Validates flag vocabulary + metadata completeness |
| Stage E: Layer 1 | 2026-03-29 (bootstrap) | Applies scenario weights, computes tension map |
| Stage E: Layer 2 | 2026-03-29 (bootstrap) | Agents receive filtered flag subsets via allowlists |
| Stage E: Layer 3 | 2026-03-29 (bootstrap) | F04 uses candidate_data.cv_text, F05 uses flag topic_keywords |
| Stage E: Synthesis | 2026-03-29 (bootstrap) | Uses rubric_matrix, provenance, flags for output assembly |

---

## Contract 3: Shared Enums (used by all stages)

**RubricLevel** — 5-value enum: exceeds, meets, partial, gap, not_assessable

**Confidence** — 3-value enum: high, medium, low

**Priority** — 3-value enum: high, medium, low

**FlagCategory** — 15-value enum: EXECUTION, STRATEGIC, COLLISION, COMPLEMENT, FRICTION, CULTURAL, DERAILMENT, DARK_SIDE, INTEGRATION, TENURE, GROUPTHINK, EXPERIENCE_STRENGTH, EXPERIENCE_GAP, EVIDENCE_QUALITY, ROUTING

**Valence** — 3-value enum: positive, negative, neutral

**EvidenceType** — 5-value enum: scored_flag, cv_rubric, requirement_gap, cv_pattern, routing

**AssessmentMode** — 2-value enum: full, partial

**ScenarioName** — 5-value enum: digital_transformation, post_acquisition, turnaround, stabilization, growth

**ScenarioPriority** — model (not enum): per-requirement object with one Priority field per scenario. Assigned by LLM in C1. Read via `requirement.scenario_priority.for_scenario(scenario_name)`.

### What Was Removed (Kill Taxonomy Patch)

**RequirementType** — REMOVED. The 9-type taxonomy (experience_depth, scope, technical, etc.) is gone. Requirements no longer carry a `type` field. Behavioral routing uses `assessable_from_cv: false` directly.

**SCENARIO_PRIORITY_DEFAULTS** — REMOVED. The type→priority lookup table is replaced by per-requirement `scenario_priority` assigned during C1 extraction. The LLM judges priority directly from requirement text, not via a type proxy.

**Specialized CV flag variants** — REMOVED. `CV_SCOPE_GAP`, `CV_INDUSTRY_MISMATCH`, `CV_SCOPE_EXCEEDS` are gone. Replaced by generic `CV_GAP`, `CV_EXCEEDS`, `CV_PARTIAL` — the requirement's scenario priority determines weight downstream.

---

## Contract 4: Flag Object (shared.models.flags.Flag)

Used by Stage D (producer) and Stage E (consumer). Full field list:

| Field | Type | Required | Used By |
|---|---|---|---|
| name | str | always | D derivation, E agents, E audit |
| candidate_name | str | always | all |
| category | FlagCategory | always | E Layer 1 weights, E Layer 2 allowlists |
| valence | Valence | always | E Layer 1 signal computation |
| evidence_type | EvidenceType | always | E agents (credibility hierarchy), E audit |
| big_five_source | str (O/C/E/A/N) | personality flags only | E audit (provenance check) |
| big_five_score | float | personality flags only | D validation (threshold check) |
| threshold_used | float | personality flags only | D validation, audit trail |
| requirement_id | str | CV flags only | E agents (JD reference), E audit (F04, F05) |
| rubric_level | str | CV flags only | E agents (must not override), E audit |
| cv_citation | str | CV flags only | E agents (evidence reference), E F04 |
| confidence | str | CV flags only | D validation, E risk assessment |
| notes | str | optional | E agents (context) |
| investigation_question | str | optional | E synthesis (investigation questions collection) |
| topic_keywords | list[str] | always | E F05 semantic drift detection |
| metadata | dict[str, Any] | optional | extensibility |

---

## Contract 5: Scenario Priority (on Requirement, not in lookup table)

**REMOVED: The old type → priority lookup table.** Priority is now stored directly on each Requirement as `scenario_priority: ScenarioPriority`, assigned by the LLM during C1 extraction in the same call.

**How scenario switch works now:** When scenario changes, C4 bridge reads `requirement.scenario_priority.for_scenario(new_scenario)` to determine which priority applies. No lookup table hop. The rubric assessments (C3) are still cached — only the priority read changes.

**How it enters the flag pipeline:** C4 bridge uses the active scenario's priority to determine flag type: GAP + high → `CV_GAP` with priority=high in metadata. The flag's weight in Stage E Layer 1 comes from the priority on the flag, not from a category-level weight.

---

## Change Protocol

When ANY model in `shared/models/` changes:
1. Update this file — change the field table, mark all consumer rows as `STALE`.
2. Update `.orchestrator/status.md` — note which stages need contract verification.
3. Add entry to `.orchestrator/decisions.md` with rationale for the change.
4. Each consumer stage agent must verify compatibility and update `consumers_verified` back to a date.
5. Integration tests must pass before any consumer is marked verified.
