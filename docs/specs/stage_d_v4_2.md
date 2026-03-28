# Stage D v4.2 — Flag Derivation (Dual-Stream)

> BMW Hackathon C-Suite Decision Intelligence Tool — March 28, 2026
>
> Stage D sits between Stage C (extraction) and Stage E (evaluation).
> It converts raw signals — Big Five scores and CV rubric assessments —
> into a unified, validated flag set that Stage E's agents evaluate.
>
> Zero LLM calls. Entirely deterministic Python. This stage is the
> firewall between noisy upstream data and the auditable evaluation
> pipeline downstream.
>
> Build time: ~2h. Latency: <1s.

---

## What Stage D Does

Stage D has one job: produce a validated, merged flag set from two independent input streams. Every flag in the output has a known provenance (which stream generated it), a known evidence type (how it was derived), and has passed validation checks guaranteeing internal consistency. Stage E agents never see raw Big Five scores or rubric assessments — they see flags only. This is the abstraction boundary.

---

## The Two Input Streams

### Stream 1: Personality Flags (from Big Five Scores)

Active only in full assessment mode (Big Five scores available). Takes the 5 OCEAN scores per candidate and applies trait threshold logic to generate personality flags. This is the same derivation logic as v4.1 — unchanged.

**What it produces:** Flags like `EXECUTION_CONSCIENTIOUSNESS_FIT` (conscientiousness score above threshold + scenario requires execution), `COLLISION_DUAL_DOMINANCE` (candidate extraversion high + existing team member extraversion high), `DERAILMENT_NEUROTICISM_UNDER_STRESS` (neuroticism above risk threshold), and similar personality-derived signals. Each flag has `evidence_type: scored_flag` and carries the specific Big Five dimension and score that triggered it.

**What it needs beyond Big Five scores:** Team context — the existing C-suite members' Big Five profiles (if provided) — for computing complementarity and collision flags. Without team context, complementarity flags (`COMPLEMENT_EXTRAVERSION_BALANCE`, `FRICTION_CONSCIENTIOUSNESS_GAP`) cannot be derived. Scenario context — which traits are weighted higher under the selected scenario. This modulates which threshold checks fire: high openness generates a positive flag under digital transformation but not under stabilization.

**Assessment mode gating:** If Big Five scores are unavailable (partial mode), this entire stream is skipped. No personality flags are generated. Personality-dependent flag categories (EXECUTION, STRATEGIC, COLLISION, COMPLEMENT, FRICTION, DERAILMENT, DARK_SIDE, GROUPTHINK, INTEGRATION) are absent from the flag set. Agents receive mode-aware instructions telling them not to make personality-based claims.

### Stream 2: CV-Derived Flags (from Stage C Rubric Bridge)

Always active (CV data is required input). Takes the rubric-to-flag bridge output from Stage C's C4 step — a list of flags derived deterministically from rubric assessments.

**What it produces:** Flags like `CV_GAP_HIGH_PRIORITY` (no CV evidence for a high-priority JD requirement), `CV_EXCEEDS_HIGH_PRIORITY` (candidate surpasses a high-priority requirement), `CV_SCOPE_GAP`, `CV_INDUSTRY_MISMATCH`, `CV_BEHAVIORAL_ROUTED` (behavioral requirement routed to personality layer), and pattern-level flags like `CV_LOW_CONFIDENCE_CLUSTER`. Each flag has `evidence_type: cv_rubric`, `requirement_gap`, `cv_pattern`, or `routing` and carries the full provenance chain (requirement_id, requirement_text, rubric_level, CV citation, confidence).

**What it needs beyond C4 output:** Nothing. The bridge output is already in flag format. Stage D's contribution for this stream is validation, not derivation.

---

## The Merge

Both streams produce flags in the same format: flag name, candidate name, category, valence, evidence_type, and metadata. The merge is simple concatenation — no deduplication, no conflict resolution, no cross-stream weighting. A candidate might have 6 personality flags and 8 CV-derived flags, giving a merged set of 14 flags.

**Why no conflict resolution.** Personality flags and CV flags measure different things. `CV_EXCEEDS_HIGH_PRIORITY` on "10+ years automotive" and `DERAILMENT_NEUROTICISM_UNDER_STRESS` are not in tension — one is track record, the other is personality risk. Even when they touch the same domain (CV shows strong execution experience while Big Five shows low conscientiousness), this is a genuine signal worth surfacing, not an artifact to resolve. The synthesis template in Stage E handles it: "strong execution track record alongside personality profile suggesting inconsistent execution discipline under stress."

**Merge order.** Personality flags first, then CV-derived flags. This is not semantically meaningful — it's for deterministic ordering in downstream processing so that audit checks and agent inputs are reproducible across runs.

---

## Flag Vocabulary Update (v4.2 Extension of F01)

### New Flag Categories

Four new categories added to the canonical flag vocabulary. These sit alongside the existing personality-derived categories.

**EXPERIENCE_STRENGTH (positive valence, CV-derived).** Two flags: `CV_EXCEEDS_HIGH_PRIORITY` and `CV_SCOPE_EXCEEDS`. Indicate demonstrable surplus against JD requirements. No `big_five_source` — these are entirely CV-grounded.

**EXPERIENCE_GAP (negative valence, CV-derived).** Four flags: `CV_GAP_HIGH_PRIORITY`, `CV_GAP_MEDIUM_PRIORITY`, `CV_PARTIAL_HIGH_PRIORITY`, `CV_SCOPE_GAP`. Indicate confirmed absence or insufficiency of evidence against JD requirements. Strongest negative CV signals because they represent verified searches that found nothing.

**EVIDENCE_QUALITY (negative valence, meta-signal).** Two flags: `CV_LOW_CONFIDENCE_CLUSTER` and `CV_INDUSTRY_MISMATCH`. Meta-signals about assessment reliability — they describe the quality of the evidence, not the quality of the candidate.

**ROUTING (neutral valence, system signal).** One flag: `CV_BEHAVIORAL_ROUTED`. Information-routing marker — tells downstream agents which JD requirements must be assessed via personality data rather than CV data. Not a positive or negative signal about the candidate.

### New Contradiction Pairs

Two additions to the contradiction set. Both are requirement_id-conditional — they only fire when both flags reference the SAME requirement.

`(CV_SCOPE_EXCEEDS, CV_SCOPE_GAP)` — cannot simultaneously exceed and gap on scope for the same requirement.

`(CV_EXCEEDS_HIGH_PRIORITY, CV_GAP_HIGH_PRIORITY)` — cannot simultaneously exceed and gap on the same requirement. Different requirement_ids are fine (exceeding one requirement and gapping another is normal).

The validation check must compare requirement_ids, not just flag names. This is different from v4.1's contradiction pairs which were unconditional.

### Topic Keywords for New Flags

Each new flag carries topic_keywords for F05 semantic drift detection in Stage E. CV-derived flag keywords are drawn from the requirement text and rubric vocabulary rather than Big Five trait language. Examples: `CV_GAP_HIGH_PRIORITY` has keywords ["gap", "missing", "requirement", "experience"]. `CV_SCOPE_EXCEEDS` has ["scope", "scale", "team", "revenue", "exceeds"]. This means semantic drift detection for CV-derived flags checks whether the agent's claim relates to the JD requirement topic, not to a personality dimension.

### Agent Allowlist Updates

**Role-fit agent gains:** EXPERIENCE_STRENGTH, EXPERIENCE_GAP. This agent becomes the primary consumer of CV-derived flags — evaluating whether track record matches role requirements.

**Team dynamics agent gains:** ROUTING. Receives `CV_BEHAVIORAL_ROUTED` flags telling it which behavioral requirements to address via personality data. Does NOT receive EXPERIENCE_STRENGTH or EXPERIENCE_GAP — track record is the role-fit agent's mandate, not team dynamics.

**Risk agent gains:** EXPERIENCE_GAP, EVIDENCE_QUALITY, MISMATCH (existing category, now includes `CV_INDUSTRY_MISMATCH`). CV-derived gaps and quality issues are risk signals — a high-priority gap means the candidate may fail because they lack a key qualification.

No agent sees all CV-derived flag categories. Independence preserved.

---

## Validation (Layer 0)

Five checks run on the merged flag set before it passes to Stage E. All deterministic.

### Check 1: Flag-Score Consistency (Both Streams)

**Personality stream:** unchanged from v4.1 — verify that flag thresholds match actual Big Five scores. If `EXECUTION_CONSCIENTIOUSNESS_FIT` fired, conscientiousness must be above the threshold for the current scenario.

**CV stream:** verify that the flag type matches the rubric assessment data. A `CV_GAP_HIGH_PRIORITY` flag must reference a requirement with priority "high" and rubric level "gap." A `CV_EXCEEDS_HIGH_PRIORITY` must reference priority "high" and rubric level "exceeds." If these don't match, the bridge has a bug.

Cross-stream consistency is NOT checked. Personality and CV signals are independent — a high conscientiousness score alongside a CV gap on an execution requirement is a valid state, not an error.

### Check 2: Mutual Exclusivity

Expanded from v4.1 to include the new requirement_id-conditional contradiction pairs. The check iterates all flag pairs per candidate. For unconditional contradictions (existing v4.1 pairs like `EXECUTION_LOW_CONSCIENTIOUSNESS_RISK` vs `EXECUTION_CONSCIENTIOUSNESS_FIT`), flag names alone determine the contradiction. For conditional contradictions (new CV-derived pairs), the check also compares requirement_ids — the contradiction only fires if both flags reference the same requirement.

On contradiction detected: log, remove the lower-confidence flag (for CV-derived flags, use the confidence tag; for personality flags, they're all deterministic so remove the one with lower severity-priority product from the flag vocabulary).

### Check 3: Dimension Coverage (Split)

**Personality dimensions:** checks all 5 Big Five dimensions have at least one flag. Only runs in full mode. If a dimension has no flags, log warning: "Dimension {X} has no scored flags — assessment on this dimension is limited." This warning appears in the provenance header.

**Requirement coverage:** checks that every CV-assessable requirement from the confirmed list has either a corresponding CV-derived flag OR a rubric level of "meets" (which generates no flag by design). If a requirement has neither a flag nor a "meets" assessment, something was lost in the bridge — log error and investigate.

### Check 4: Cross-Stream Coherence (Advisory)

New check, advisory only — does not block the pipeline. Detects interesting tensions between streams. If a candidate has a positive CV flag (EXPERIENCE_STRENGTH category) for a domain where they also have a negative personality flag (e.g., `CV_EXCEEDS_HIGH_PRIORITY` on an execution requirement AND `EXECUTION_LOW_CONSCIENTIOUSNESS_RISK`), generate an advisory note: "Cross-stream tension: strong CV evidence for [requirement] alongside personality risk [flag]. Both signals valid — committee should weight appropriately." This note feeds into the synthesis template.

### Check 5: Flag Count Reasonableness

New check, advisory. If total flag count exceeds 25 per candidate, warn that the evaluation may be noisy — agents will have too many signals to process meaningfully. If total is below 3, warn that assessment data is thin. Expected range for a well-functioning pipeline: 8-18 flags per candidate.

---

## Assessment Mode Determination

### Logic

If Big Five scores are present for all 5 dimensions for at least one candidate → full mode for that candidate. Assessment mode is determined PER CANDIDATE, not globally. One candidate might have Big Five scores (full mode) while another uses a preset (also full mode) and a third has no personality data (partial mode). The provenance header and agent prompts reflect per-candidate mode.

If no candidates have Big Five scores → all agents receive partial mode preamble. Team dynamics and risk agents operate in reduced scope.

### Personality Preset Handling

When a judge selects a preset (e.g., "The Turnaround Driver"), the preset's Big Five scores are injected as if they were manually entered. The mode becomes full. The provenance header records: "Personality data source: Preset archetype — The Turnaround Driver (synthetic profile based on executive research archetypes)." If the judge modifies scores after selecting a preset: "Modified preset — based on The Turnaround Driver with manual adjustments."

The preset name flows through to Stage E's provenance header and output. The tool never pretends preset scores are validated assessment data.

### Mode Impact on Flag Set

In full mode: merged flag set contains both personality and CV-derived flags. Typical: 6-8 personality flags + 6-10 CV-derived flags = 12-18 total per candidate.

In partial mode: flag set contains only CV-derived flags. Typical: 6-10 flags per candidate. Personality flag categories are entirely absent. Flag count is lower, which means agents have less to work with — their assessments will be shorter and more focused on track record.

---

## Output to Stage E

Stage D passes to Stage E:

**Merged validated flag set** — the list of all flags for all candidates, each with full provenance metadata.

**Assessment mode per candidate** — full or partial.

**Provenance metadata** — personality flag count, CV flag count, total flags, Big Five availability per candidate, requirements assessed count, high-priority gap count, dimension coverage warnings, cross-stream coherence notes.

**Confirmed requirement list** — the full list of JD requirements with priorities (from C2). Stage E agents reference these for context — they understand what the role requires.

**Raw CV text per candidate** — not for agent consumption, but for F04's biographical reference validation in Stage E's audit layer. Agents use structured flags; the audit uses raw text as ground truth.

**Rubric assessment matrix** — the full per-requirement, per-candidate rubric data. Not for agents (they work with flags), but for the synthesis template's trade-off matrix output in Stage E.

---

## Stage D Does NOT Do

**No LLM calls.** Stage D is entirely deterministic. Every flag is derived from threshold checks, lookup tables, or deterministic bridge mappings.

**No scenario weighting.** Scenario weight application happens in Stage E Layer 1, not here. Stage D produces flags with their raw valence and metadata. Stage E decides how much each flag matters under the current scenario.

**No agent-level processing.** Stage D doesn't know which agent will see which flag. It produces the complete flag set. Stage E's Layer 2 applies agent allowlists to filter which flags each agent receives.

**No output generation.** Stage D produces internal data structures consumed by Stage E. It does not generate any user-facing output. The provenance header content is metadata — Stage E's synthesis template renders it.

**No candidate ranking.** Stage D does not rank candidates. It provides evidence. Stage E's agents form independent assessments, and the synthesis template assembles the comparison.
