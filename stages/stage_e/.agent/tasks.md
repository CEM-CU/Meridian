# Stage E — Task List

> last_updated: 2026-03-29T00:00:00Z by agent (E4 done)

## Overview

Stage E is the evaluation engine. Takes Stage D's validated flag set, runs 3 independent agents in parallel, audits their output, and assembles the final synthesis. 4 LLM calls (3 agents + 1 synthesis statement). Latency: ~10-13s.

## Tasks (ordered by dependency)

### E1: Layer 0 — Stage D Output Validation [NOT STARTED]
- **Blocked by:** StageDOutput contract (shared models)
- **Input:** StageDOutput
- **Output:** validated StageDOutput (bad flags stripped, issues logged)
- **LLM calls:** 0
- **Implementation:**
  - Flag vocabulary membership: every flag name must exist in canonical vocabulary. Strip + log HALLUCINATED_FLAG_IN_DERIVATION if not (shouldn't happen since D is deterministic, but defensive)
  - Metadata completeness: every flag must have candidate_name, category, valence, evidence_type. CV flags must have requirement_id + rubric_level. Personality flags must have big_five_source. Missing → strip + log
  - Provenance chain: CV flag requirement_id must reference confirmed requirement list. Personality flag big_five_source must be valid dimension + candidate must have that score
  - Fail-open: strip offending flags, log, proceed with clean subset. Never block pipeline
- **Tests:** Valid input passes unchanged. Flag with unknown name → stripped. Flag missing required metadata → stripped. Invalid requirement_id reference → stripped.

### E2: Layer 1 — Scenario Weights + Signal Computation [NOT STARTED]
- **Blocked by:** E1
- **Input:** validated flag set + ScenarioConfig
- **Output:** weighted flags + signal-strength labels + risk bands + tension map
- **LLM calls:** 0
- **Implementation:**
  - Apply scenario weight vectors to flag categories. CV-derived category weights: EXPERIENCE_STRENGTH=high (varies slightly by scenario), EXPERIENCE_GAP=1.0 (neutral — priority system handles weighting), EVIDENCE_QUALITY=moderate (constant), ROUTING=0 (system signal, not evaluation)
  - Signal-strength labels: computed from weighted flag sums per candidate. Risk bands: from risk-category flag counts (DERAILMENT, DARK_SIDE, TENURE + EXPERIENCE_GAP for high-priority + EVIDENCE_QUALITY)
  - Partial mode: do not penalize for fewer flags. Note "Risk assessment limited to experience-based signals"
  - **CRITICAL (F02):** Signal labels and risk bands DO NOT enter agent inputs. Reserved for synthesis template only
  - Tension map: identify flag pairs creating interpretive tension within a candidate. v4.2 adds cross-stream tensions (positive CV + negative personality on same domain). Domain matching via lookup: experience_depth/scope→EXECUTION, technical→STRATEGIC, leadership_context→STRATEGIC/EXECUTION, geographic/industry→CULTURAL
- **Tests:** Verify weight application is correct per scenario. Verify F02 — signal labels not in agent input structure. Tension map detects cross-stream tension. Partial mode noted correctly.

### E3: Layer 2 — Agent Prompts (×3) [NOT STARTED]
- **Blocked by:** E2 (tension map), flag allowlist definitions
- **Input per agent:** filtered flag subset (via allowlist) + tension map + candidate data + requirement list + assessment mode
- **Output per agent:** JSON verdict with claims, each carrying evidence_basis
- **LLM calls:** 3 (parallel via asyncio.gather)
- **Implementation:**
  - **Role-Fit Agent ("The Researcher"):** allowlist includes EXECUTION, STRATEGIC, CULTURAL, EXPERIENCE_STRENGTH, EXPERIENCE_GAP. Primary consumer of CV-derived flags. Evaluates track record vs role requirements
  - **Team Dynamics Agent ("The Devil's Advocate"):** allowlist includes COLLISION, COMPLEMENT, FRICTION, GROUPTHINK, INTEGRATION, ROUTING. Receives CV_BEHAVIORAL_ROUTED flags. In partial mode: reduced scope, generates investigation questions instead of assessments for behavioral requirements
  - **Risk Agent ("The Risk Analyst"):** allowlist includes DERAILMENT, DARK_SIDE, TENURE, EXPERIENCE_GAP, EVIDENCE_QUALITY. CV gaps on high-priority requirements = risk signals. Industry mismatch is now surfaced via CV_GAP flag on an industry-related requirement — the requirement text carries the context
  - **No agent sees all flag categories.** Independence preserved
  - Mode-aware preamble: full mode lists all evidence types. Partial mode restricts to CV-derived types, explicitly bans personality claims
  - Agents must specify evidence_basis.type for every claim: scored_flag, cv_rubric, requirement_gap, biographical_pattern, research_general (max 2)
  - For cv_rubric references: evidence_basis.reference = requirement_id. Agent must NOT override rubric level
  - Output: JSON with claims array, each claim having text, evidence_basis (type + reference), and confidence
  - Per-agent timeout: 15s. On timeout: partial output with fallback notice
- **Tests:** Mock agent responses → parse correctly. Verify allowlist filtering is correct per agent. Verify mode preamble changes between full/partial. Timeout handling returns partial output.

### E4: Layer 2 — JSON Output Schemas [DONE]
- **Blocked by:** shared models
- **Implementation:**
  - Define Pydantic models for agent output: AgentVerdict, Claim, EvidenceBasis
  - evidence_basis.type enum: scored_flag, cv_rubric, requirement_gap, biographical_pattern, research_general
  - Strict validation: unknown evidence types rejected, missing fields rejected
- **Tests:** Valid agent JSON parses correctly. Missing evidence_basis → rejected. Unknown evidence type → rejected.

### E5: Layer 3 — Audit (8 Checks) [NOT STARTED]
- **Blocked by:** E3 + E4
- **Input:** 3 agent verdicts + flag set + requirement list + candidate data (with raw CV text)
- **Output:** audited verdicts with warnings/stripped claims
- **LLM calls:** 0
- **Implementation:**
  - Check 1: JSON schema validation (re-run agent once on failure, hard block on second failure)
  - Check 2: Flag scope enforcement — agent only cites flags from its allowlist. Violation → strip claim, log
  - Check 3: Unaddressed flag detection — flags in allowlist that agent silently dropped → surface as "unaddressed signals"
  - Check 4: Hallucinated flag detection — cited flag names must exist in vocabulary. cv_rubric references must resolve to valid requirement_ids. "REQ-17" when list goes to REQ-12 → hallucinated reference → strip
  - Check 5 (F04): Biographical reference validation. cv_rubric citations checked against raw CV text via substring match (lowercase, whitespace-collapsed). Numerical discrepancies caught. requirement_gap references verified against rubric matrix. THIS IS THE STRONGEST CHECK — catches agent fabrication
  - Check 6 (F05): Semantic drift detection. Keyword overlap between claim text and flag topic_keywords. <20% overlap → DRIFT warning. For cv_rubric: checks against requirement text keywords, not personality language
  - Check 7 (F07): research_general cap. Max 2 per agent. With CV evidence available, hitting the cap is a stronger warning than in v4.1
  - Check 8 (F14): Downweight ratio. If agent downweights >50% of its in-mandate flags → warning. Applies to both personality and CV flags
- **Tests:** Each check tested independently with crafted inputs. F04 catches numerical discrepancy in citation. F05 catches personality claim on CV evidence. F07 enforces cap. F14 fires at >50% threshold.

### E6: Layer 3b — Self-Consistency [NOT STARTED]
- **Blocked by:** E5
- **Input:** full pipeline function + scenario
- **Output:** instability annotations per candidate
- **LLM calls:** 12 per scenario (4 Stage E calls × 3 runs)
- **Implementation:**
  - Run full D+E pipeline 3× per scenario. Diff rankings across runs. Annotate instabilities
  - Stage C results cached (scenario-independent) — only D+E re-run
  - If any candidate's ranking changes across runs → instability annotation in output
- **Tests:** Deterministic mock → consistent across runs. Intentionally varied mock → instability detected.

### E7: Synthesis Template [NOT STARTED]
- **Blocked by:** E5
- **Input:** audited agent verdicts + signal labels + risk bands + rubric matrix + provenance
- **Output:** structured synthesis document (3 progressive layers)
- **LLM calls:** 1 (trade-off statement only)
- **Implementation:**
  - Layer 1 (primary): Trade-off matrix. Requirement × candidate grid. Cells: rubric level (color-coded), confidence, citation (expandable). Rows sorted by priority. Scenario switch re-sorts rows, rubric levels don't change. Partial mode: behavioral rows show "Requires personality data"
  - Layer 2: Per-candidate agent summary. Expandable. Contested signals, concordance/discordance, investigation questions
  - Layer 3: Full evidence trail. Drill-down per claim. Rubric assessment, flag derivation chain, audit warnings, cross-agent concordance
  - Provenance header: data sources, assessment mode, quality checks
  - Epistemic disclaimers (F09, F10)
  - 1 LLM call for 2-4 sentence trade-off statement. Strictly constrained: no new analysis, references only structured input
  - Contested signal callouts (F12): same flag + different agent valence, cross-stream contests (CV evidence of strength + personality risk on same domain)
- **Tests:** Template assembles with all sections present. Partial mode shows correct disclaimers. Contested signals detected and formatted.

### E8: Scenario Switch Wiring [NOT STARTED]
- **Blocked by:** E7
- **Implementation:**
  - C3 results cached. On switch: C2 re-apply priorities → C4 re-bridge → D re-derive → E re-evaluate
  - Pre-compute both demo scenarios during setup. Scenario switch swaps cached output with 2s theatrical delay
  - Live switch: ~10-13s (3 agent calls + 1 synthesis call)
- **Tests:** Two scenarios produce different outputs from same input. Cached output matches live computation.

### E9: Timeout + Graceful Degradation (F16) [NOT STARTED]
- **Blocked by:** E3
- **Implementation:**
  - Per-agent timeout: 15s. On timeout: partial output with fallback notice
  - 2-agent output is 80% as useful as 3-agent. Frozen screen is 0%
  - Missing agent noted in synthesis: "Team dynamics assessment unavailable — evaluation covers role-fit and risk only"
- **Tests:** Simulated timeout → partial output generated. Synthesis handles 2-agent input correctly.

### E Integration Test [NOT STARTED]
- **Blocked by:** E1-E9
- **Input:** Mock StageDOutput from fixtures
- **Output:** Full synthesis document
- **Checks:** All layers present, no audit errors on valid input, synthesis statement generated, partial mode handled correctly
