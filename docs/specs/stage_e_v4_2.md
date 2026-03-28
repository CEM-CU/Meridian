# Stage E v4.2 — Multi-Agent Evaluation & Synthesis

> BMW Hackathon C-Suite Decision Intelligence Tool — March 28, 2026
>
> Stage E is the evaluation engine. It takes Stage D's validated flag set,
> runs 3 independent agents in parallel, audits their output, and assembles
> the final synthesis. This is where flags become assessments and assessments
> become the document the CHRO reads.
>
> All v4.1 fixes (F01–F23) remain in effect. v4.2 changes are additive —
> they extend the pipeline to handle dual-source flags (personality + CV)
> and produce a trade-off matrix as the primary output view.
>
> LLM calls: 4 (3 parallel agents + 1 synthesis trade-off statement).
> Latency: ~10-13s (agents parallel, synthesis sequential).
> Build time: ~10h.

---

## Layer 0: Stage D Output Validation

Receives the merged flag set from Stage D and runs entry validation before anything else in Stage E touches the data. This is the same Layer 0 as v4.1 but it now validates a larger, dual-source flag set.

### What It Checks

**Flag vocabulary membership.** Every flag name in the set must exist in the canonical vocabulary (F01, extended with CV-derived flags in v4.2). Any flag not in the vocabulary is a derivation bug. On detection: strip the flag, log HALLUCINATED_FLAG_IN_DERIVATION (this shouldn't happen since Stage D is deterministic, but defensive programming applies).

**Metadata completeness.** Every flag must carry: candidate name, category, valence, evidence_type. CV-derived flags must additionally carry requirement_id and rubric_level. Personality flags must carry big_five_source. Missing metadata → log, strip flag.

**Provenance chain integrity.** For CV-derived flags: verify that the requirement_id references a requirement in the confirmed requirement list. For personality flags: verify that the big_five_source is one of O, C, E, A, N and that the candidate actually has a Big Five score for that dimension.

On any failure: fail-open with transparency. Strip the offending flag, log the issue, include in audit output. Never block the pipeline on validation failures — always proceed with the clean subset.

---

## Layer 1: Scenario Weight Application & Signal Computation

Identical logic to v4.1 but operates on a larger flag set that now includes CV-derived categories.

### What It Does

Takes the validated flag set and the current scenario, applies scenario-specific weight vectors to flag categories, computes signal-strength labels, risk bands, and the tension map.

### Scenario Weight Vectors — Extended

v4.1's weight vectors covered personality flag categories (EXECUTION, STRATEGIC, COLLISION, COMPLEMENT, FRICTION, CULTURAL, DERAILMENT, DARK_SIDE, INTEGRATION, TENURE, GROUPTHINK). v4.2 adds weights for the new CV-derived categories.

**EXPERIENCE_STRENGTH weight:** High under all scenarios — a candidate exceeding a JD requirement is always relevant. Varies slightly: highest under stabilization (track record is paramount), slightly lower under digital transformation (capability matters more than history).

**EXPERIENCE_GAP weight:** Scenario-dependent via the priority system. The weight isn't applied to the flag category globally — it's already encoded in the flag itself through requirement priorities. A `CV_GAP_HIGH_PRIORITY` flag inherently carries higher weight than `CV_GAP_MEDIUM_PRIORITY`. When the scenario switches, requirement priorities reassign (Stage C2/C4), which changes WHICH requirements generate high-priority gap flags. This means EXPERIENCE_GAP doesn't need a separate scenario weight — the scenario modulation happens upstream in the bridge. Set category weight to 1.0 (neutral) and let the priority system do the work.

**EVIDENCE_QUALITY weight:** Constant across scenarios. Evidence quality issues are equally concerning regardless of strategic context. Weight: moderate.

**ROUTING weight:** Zero. Routing flags are system signals, not evaluation signals. They don't contribute to signal-strength computation.

### Signal Labels and Risk Bands — Unchanged Logic

Signal-strength labels are computed from weighted flag sums per candidate. Risk bands are computed from risk-category flag counts (DERAILMENT, DARK_SIDE, TENURE + now also EXPERIENCE_GAP for high-priority gaps and EVIDENCE_QUALITY). The band thresholds are the same as v4.1. Ordinal differentiation within bands (F13) still applies.

**One change:** A candidate in partial mode (no personality data) may have fewer risk-category flags than a full-mode candidate. The risk band computation must not penalize partial-mode candidates for having fewer flags — it should note: "Risk assessment limited to experience-based signals. Personality-based derailment risk not assessed."

### Independence Protection — Still Enforced (F02)

Signal-strength labels and risk bands are computed here but DO NOT enter agent inputs. They are reserved for the synthesis template. Agents receive: validated flags + tension map + candidate data + confirmed requirement list. No pre-computed verdicts. This is unchanged from v4.1's F02 — the most important architectural constraint.

### Tension Map — Extended

The tension map identifies flag pairs within the same candidate that create interpretive tension. v4.1's tension map covered personality flag pairs (e.g., high openness is positive for transformation but creates risk in structured environments). v4.2 extends it to cross-stream tensions.

**New tension type: CV-personality divergence.** When a candidate has a positive CV flag and a negative personality flag (or vice versa) touching the same competency domain, this is a meaningful tension. Example: `CV_EXCEEDS_HIGH_PRIORITY` on an execution requirement + `EXECUTION_LOW_CONSCIENTIOUSNESS_RISK` = "strong track record of execution, but personality profile suggests discipline may be inconsistent under stress." The tension map captures these pairs with a `cross_stream` marker so agents and the synthesis template can surface them.

Domain matching for cross-stream tensions uses a lightweight lookup table mapping requirement types to personality flag categories: experience_depth/scope → EXECUTION; technical → STRATEGIC; leadership_context → STRATEGIC/EXECUTION; geographic/industry → CULTURAL. This is approximate — false positives are acceptable here because the tension map is advisory input, not a constraint.

---

## Layer 2: Parallel Agent Evaluation

Three agents run in parallel with independent contexts. No agent sees another agent's output. No agent sees pre-computed signal labels or risk bands. Each agent receives the flag subset defined by its allowlist + the tension map + candidate data + confirmed requirement list + assessment mode per candidate.

### Agent Architecture — Unchanged from v4.1

**Role-Fit Agent ("The Researcher").** Evaluates whether each candidate's qualifications match the role requirements. In v4.1, this worked primarily with mandate-level personality flags. In v4.2, this agent becomes the primary consumer of CV-derived flags — it has direct evidence of CV-JD alignment.

**Team Dynamics Agent ("The Devil's Advocate").** Evaluates how each candidate would interact with the existing team. In full mode: personality-based complementarity, collision, groupthink analysis. In partial mode: reduced scope — can still assess whether the candidate brings functional experience the team lacks (from CV flags) but cannot assess personality-based dynamics. For behavioral requirements routed via `CV_BEHAVIORAL_ROUTED`: must acknowledge them and either address via Big Five data (full mode) or state "requires personality data" (partial mode).

**Risk Agent ("The Risk Analyst").** Evaluates derailment risk, dark-side concerns, and failure pathways. In v4.2, also evaluates experience gaps on high-priority requirements as risk signals, and evidence quality issues as meta-risk. In partial mode: limited to CV-derived risk signals — cannot assess personality-based derailment.

### Mode-Aware Agent Prompts

Every agent prompt begins with a mode-dependent preamble. The preamble does three things: states the assessment mode (full or partial), lists available evidence types for this mode, and instructs on what claims the agent may and may not make.

**Full mode preamble (common to all agents):** Assessment mode is FULL. Both CV-derived evidence and personality data available. All evidence types permitted: `scored_flag`, `cv_rubric`, `requirement_gap`, `biographical_pattern`, `research_general` (max 2). Agent must specify evidence type for every claim.

**Partial mode preamble (common to all agents):** Assessment mode is PARTIAL — experience only. No personality data. Agent must not make personality-based claims, must not infer leadership style or derailment risk from CV language, must not guess at Big Five dimensions. Available evidence types: `cv_rubric`, `requirement_gap`, `biographical_pattern`, `research_general` (max 2). NOT available: `scored_flag`. For behavioral requirements tagged `CV_BEHAVIORAL_ROUTED`: state explicitly that assessment requires personality data — do not skip.

**Partial mode: team dynamics agent specific.** Without personality scores, cannot assess complementarity/collision with team members, groupthink risk, behavioral integration likelihood, or leadership style compatibility. CAN still assess: whether the candidate brings functional experience the team lacks (from CV-derived flags + team context if provided), and whether career patterns suggest collaborative or independent orientation (biographical_pattern, flagged as low confidence). For every behavioral JD requirement routed to this agent: generate an investigation question instead of an assessment.

**Partial mode: risk agent specific.** Without personality scores, cannot assess derailment risk, dark-side tendencies, neuroticism under stress, or interpersonal abrasion risk. CAN still assess: experience-mandate gaps as failure risk (CV_GAP_HIGH_PRIORITY on critical requirements), evidence quality concerns (CV_LOW_CONFIDENCE_CLUSTER suggesting the committee is deciding on thin data), and tenure pattern risks (if tenure data available from CV extraction).

### How Agents Handle CV-Derived Flags

All agent prompts include a section explaining the new flag types. Key instruction: when citing `cv_rubric` or `requirement_gap` evidence, reference the specific JD requirement and rubric level. Do NOT override the rubric level — if Stage C assessed PARTIAL, the agent cites it as PARTIAL. The agent's job is to interpret the IMPLICATIONS of the rubric level for its mandate, not to second-guess the rubric assessment.

Example of correct agent behavior: "Chen has PARTIAL coverage on EMEA operations experience (REQ-05). CV shows 18 months as Regional Director EMEA at Rivian — relevant but brief for a role requiring sustained multi-country leadership. In a post-acquisition scenario requiring cross-border integration, this gap becomes critical."

Example of incorrect agent behavior: "Chen meets the EMEA requirement based on her Rivian experience." (Wrong: rubric was PARTIAL, not MEETS. Agent overrode Stage C's assessment.)

### Output Schema — Extended Evidence Types

Agent outputs follow the same JSON structure as v4.1 (F03) with two additions to the `evidence_basis.type` enum.

The complete enum is now: `scored_flag` (from Big Five, highest credibility), `cv_rubric` (from structured rubric assessment against JD requirement, high credibility), `requirement_gap` (confirmed absence of evidence, high credibility for negative findings), `biographical_pattern` (from career data, medium credibility), `research_general` (LLM inference from I/O psychology, lowest credibility, capped at 2 per agent).

For `cv_rubric` references, the `evidence_basis.reference` field contains the requirement_id (e.g., "REQ-04") rather than a flag name. The audit pipeline resolves this against the requirement list and the original rubric assessment.

For `requirement_gap` references, the reference field contains the requirement_id where no evidence was found. The audit verifies this against the rubric assessment matrix.

### Token Budget

Per-agent input is larger in v4.2: ~5,000 tokens (was ~3,700). The increase comes from CV-derived flags carrying richer metadata (requirement text, rubric levels, citations) and the mode-aware preamble. Expected output: ~1,800 tokens per agent (was ~1,500 — agents must reference CV evidence in structured format). Total Stage E LLM cost per run: ~22,900 tokens across 4 calls. At Sonnet pricing: ~$0.08-0.12.

---

## Layer 3: Consistency Audit (8 Checks + Enhancements)

All 8 checks from v4.1 remain. Two checks gain significant capability from Stage C integration.

### Check 1: JSON Schema Validation — Unchanged

Validates agent output structure. Extended enum for `evidence_basis.type` (now includes `cv_rubric` and `requirement_gap`). On failure: re-run agent once. Hard block on second failure.

### Check 2: Flag Scope Enforcement — Unchanged

Verifies agents only cite flags from their allowlist. Now includes the new CV-derived categories in allowlists. On violation: strip claim, log.

### Check 3: Unaddressed Flag Detection — Unchanged

Detects flags in an agent's allowlist that it silently dropped. On detection: surface as "unaddressed signals" in output.

### Check 4: Hallucinated Flag Detection — Extended

Verifies cited flag names exist in the canonical vocabulary. Now includes CV-derived flag names. Also verifies that `cv_rubric` references resolve to actual requirement_ids in the confirmed list. If an agent cites "REQ-17" but the requirement list only goes to REQ-12, that's a hallucinated reference. On detection: strip claim, log.

### Check 5: Biographical Reference Validation (F04) — CRITICAL ENHANCEMENT

This check goes from the weakest to the strongest in the audit pipeline.

**v4.1 state:** F04 validated `biographical_pattern` references against candidate_data. Problem: candidate_data was often just a name and Big Five scores — nothing to validate against.

**v4.2 state:** candidate_data now includes the full CV text (passed through from Stage C). F04 can now validate:

For `biographical_pattern` references: dot-path resolution against structured candidate data. Now these structured fields are populated by Stage C extraction, so there are many more fields to resolve against.

For `cv_rubric` references: the agent cites a CV passage. F04 checks whether that passage actually appears in the raw CV text using substring matching with normalization (lowercase, whitespace-collapsed). If the agent claims "CV: managed $800M P&L at Siemens" but the CV text says "$80M budget at Siemens," F04 catches the numerical discrepancy. This is citation fabrication detection — agents in Stage E are re-citing passages from Stage C's rubric assessments, and those original passages are verifiable against the raw CV.

For `requirement_gap` references: F04 verifies that the requirement_id exists in the confirmed list AND that the rubric assessment for that requirement × candidate is indeed "gap" or "not_assessable." If an agent claims "no evidence of M&A experience" but the rubric actually assessed PARTIAL, F04 catches the misrepresentation.

**Implementation detail:** The raw CV text is included in candidate_data but NOT exposed to agents in their prompts. Agents work with structured flags. The raw text is only used by this deterministic audit check as ground truth.

### Check 6: Semantic Drift Detection (F05) — Extended

For `scored_flag` citations: unchanged — keyword overlap between claim text and flag topic_keywords.

For `cv_rubric` citations: keyword overlap between claim text and the topic_keywords of the CV-derived flag that corresponds to the cited requirement. Since CV-derived flag keywords are drawn from requirement text rather than personality language, this catches agents making personality-based claims while citing CV evidence (which would be a category error).

Threshold: <20% overlap triggers SEMANTIC_DRIFT_WARNING. Not a hard rejection — surfaced as [DRIFT] marker in output.

### Check 7: research_general Cap (F07) — Unchanged

Max 2 per agent. With CV-derived evidence types now available, agents have more grounded alternatives. If an agent still hits the cap of 2, it's a stronger warning than in v4.1 — it means the agent couldn't ground its claims in any available data source.

### Check 8: Downweight Ratio Warning (F14) — Extended

Now applies to CV-derived flags too. If the role-fit agent receives 8 CV-derived flags but downweights 5 of them, the warning fires. Systematic downweighting of CV evidence is as concerning as systematic downweighting of personality evidence.

---

## Layer 3b: Self-Consistency Pre-Computation

Unchanged logic from v4.1 F15. Run full pipeline 3× per scenario. Diff rankings across runs. Annotate instabilities.

**Efficiency gain from Stage C caching:** Stage C results (rubric assessments) are scenario-independent and cached from the initial run. Self-consistency re-runs only cover Stage D flag re-derivation (with scenario-specific priorities) and Stage E evaluation. The 3 CV assessment LLM calls do NOT re-run for self-consistency — only the 4 Stage E calls × 3 runs = 12 additional calls per scenario.

---

## Synthesis: Template Assembly

### Output Structure — Three Progressive Layers

v4.2 restructures the output from a single synthesis document into three progressive-disclosure layers. The CHRO sees Layer 1 first and drills down into Layers 2 and 3 as needed.

### Layer 1: Trade-Off Matrix (NEW — Primary View)

A requirement × candidate grid. Each cell shows the rubric level (color-coded: green for exceeds, light green for meets, yellow for partial, red for gap, gray for not assessable), the confidence tag, and the CV citation (expandable). Rows sorted by requirement priority (high first).

The matrix does not compute or display composite scores. The CHRO reads the matrix and forms their own judgment about which trade-offs matter. This is consistent with the product's lens philosophy — structure the evidence, don't pre-empt the conclusion.

**What the scenario switch does to the matrix:** When the scenario changes, requirement priorities re-sort (from Stage C2 defaults). Rows slide up and down — a low-priority row may become high-priority. The rubric levels in cells do NOT change — the underlying evidence is scenario-independent. What changes is the visual hierarchy: high-priority gaps become prominent, formerly critical requirements recede. Colors may shift in emphasis (a partial on a now-high-priority row is visually stronger than a partial on a low-priority row). The animation of rows reordering is the demo's "wow moment" on the CV-JD axis, complementing the agent-debate reordering on the personality axis.

**Partial mode matrix:** Fully functional for CV-derived assessments. Behavioral requirement rows show "Requires personality data" in gray with a locked state. The matrix is useful even without personality data — it shows experience-mandate fit clearly.

### Layer 2: Per-Candidate Agent Summary (Existing, Repositioned)

Click on a candidate column header to expand. Contains: agent debate highlights (role-fit, team dynamics, risk assessments), contested signals (where agents disagree on the same flag — now includes cross-stream contests where role-fit cites CV evidence of strength while risk cites personality evidence of danger), concordance/discordance between agent risk assessment and deterministic risk band (F02), investigation questions collected from all GAP, PARTIAL, and low-confidence assessments across both stages.

### Layer 3: Full Evidence Trail (Existing, Repositioned)

Click on any specific claim or cell. Contains: the individual rubric assessment with full CV citation, the flag derivation chain (which rubric level generated which flag, or which Big Five score generated which flag), audit warnings ([DRIFT] markers, citation validation results, confidence issues), cross-agent flag concordance.

### Provenance Header (F08 — Rewritten)

The provenance header now reflects both data sources and assessment mode.

Full mode content: Input sources (JD requirements count with CV-assessable vs behavioral breakdown, CV data quality indicator per candidate, personality data source with preset name or "manual entry" or "validated instrument"), assessment mode FULL. CV assessment summary (high/medium/low confidence counts across all candidates, gap count on high-priority requirements). Personality assessment summary (Big Five dimension coverage, dimension gap warnings). Quality checks (flag-score consistency pass/fail per stream, mutual exclusivity pass/fail, requirement coverage pass/fail, total flag counts per stream).

Partial mode: same structure but personality assessment section reads "NOT PROVIDED — assessment covers experience-mandate fit only. Team dynamics, derailment risk, and behavioral requirement analysis require Big Five scores."

### Epistemic Disclaimers (F09, F10 — Updated)

F10 (top-level disclaimer): "This tool surfaces patterns from personality and CV data to inform committee judgment. It generates structured hypotheses grounded in published organizational psychology research and verifiable CV evidence — not predictions. Confidence levels reflect signal density, not outcome probability. All outputs are advisory and require human deliberation."

F09 (team dynamics section): In full mode, unchanged. In partial mode: "No personality data available. Team dynamics assessment limited to experience-based factors (skill gaps, functional diversity). Personality-based dynamics (complementarity, collision risk, groupthink vulnerability) require validated Big Five scores."

### Synthesis Trade-Off Statement (1 LLM Call)

One scoped LLM call produces a 2-4 sentence trade-off statement summarizing the cross-candidate comparison. This is the same call as v4.1 but with richer input — it now sees both the trade-off matrix and the agent verdicts. The call is strictly constrained: no new analysis permitted, references only structured input, output is appended to the template without modification.

### Contested Signal Callouts (F12 — Extended)

v4.1's contested signals detected when the same flag was cited by multiple agents with different interpretive valence. v4.2 adds a richer contest type: cross-stream contests.

**Cross-stream contest:** When the role-fit agent cites `cv_rubric` evidence showing the candidate exceeds on a requirement, while the risk agent cites `scored_flag` evidence showing personality-based risk on the same competency domain. This surfaces as: "[CONTESTED SIGNAL]: Strong CV evidence for [requirement] alongside personality risk [flag]. The same domain is assessed positively by track record and negatively by personality profile. Committee should weigh demonstrated history against predicted behavior."

This is the most informative type of contested signal — it makes a genuine tension visible rather than just showing agents disagreeing on the same data.

---

## Scenario Switch Mechanics

### Pre-Computed Scenarios (Demo)

Both planned scenarios fully pre-computed during setup. Stage C runs once (rubric assessments cached). Stage D + E run per scenario (different priorities → different flags → different evaluations). Self-consistency check runs per scenario. Total pre-computation: ~2-3 minutes during setup. Scenario switch during demo: instant swap with 2-second theatrical delay.

### Live Scenario Switch (Judge Test)

Stage C rubric assessments are scenario-independent and cached after the initial analysis. When the judge switches scenarios:

1. Stage C2 re-applies scenario-specific priority defaults (deterministic, <100ms).
2. Stage C4 re-runs rubric-to-flag bridge with new priorities (deterministic, <100ms).
3. Stage D re-derives merged flag set with new CV-derived flags (deterministic, <100ms).
4. Stage E Layer 1 re-applies scenario weights (deterministic, <100ms).
5. Stage E Layer 2 re-runs 3 agents with new flag set (3 parallel LLM calls, ~5-6s).
6. Stage E Layer 3 audits new output (~100ms).
7. Synthesis re-assembles with new data + 1 LLM call (~3-4s).

**Total live scenario switch: ~10-13 seconds.** This is the critical architectural insight: by separating evidence assessment (scenario-independent, cached) from evidence weighting (scenario-dependent, fast to re-run), the scenario switch is fast even without pre-computation. The expensive part (Stage C's 3 LLM calls) runs once.

### Unplanned Scenarios

If the judge requests a scenario not in the 5 pre-defined set, the system handles it with the closest matching scenario defaults as a starting point, or allows the judge to manually adjust priority ordering. The pipeline runs identically — latency is the same ~10-13 seconds. No self-consistency check for unplanned scenarios — noted in output.

---

## What Does NOT Change from v4.1

Listed explicitly to prevent implementation drift.

**F02 (signal isolation).** Pre-computed labels and risk bands still excluded from agent inputs. CV-derived flags do not change this — agents see flags, not verdicts.

**F03 (JSON output).** All agent outputs remain JSON. New evidence types follow same schema patterns.

**F06 (counterfactual reasoning framing).** No do-calculus claims. The trade-off matrix strengthens the counterfactual framing: "what changes if priorities shift" is now visible in both the matrix and the agent debate.

**F07 (research_general cap).** Still 2 per agent.

**F11 (scenario weight framing).** Weights encode stakeholder priorities, not causal truth. Now applies to a larger flag set but the framing is identical.

**F13 (risk band ordinal differentiation).** Risk bands now incorporate CV-derived risk flags. More flags feeding computation = finer differentiation. Logic unchanged.

**F16 (timeout + graceful degradation).** Per-agent timeouts still apply. A timed-out agent produces partial output with fallback notice. 2-agent output is 80% as useful as 3-agent; a frozen screen is 0%.

**F18 (input sanitization).** Now applies to CV text and JD text in addition to candidate profiles. Prompt injection patterns stripped from all string inputs before LLM injection.

**F23 (feedback loop roadmap).** Richer story with Stage C: "Phase 2 tracks which requirements AND rubric assessments predicted actual outcomes — calibrating scenario weights AND rubric reliability."

---

## Evidence Credibility Hierarchy

The evidence types now form a clear credibility gradient visible in the output. The CHRO can see at a glance which claims rest on what foundation.

1. **scored_flag** — from validated Big Five instrument via deterministic thresholds. Highest credibility. No LLM interpretation involved in derivation.

2. **cv_rubric** — from structured rubric evaluation of a specific CV passage against a specific JD requirement. High credibility. Citable and verifiable against source document. Stage C's LLM produced it; Stage E's F04 validates it.

3. **requirement_gap** — confirmed absence of evidence after systematic CV search. High credibility for negative findings. The value is in the verified search, not a positive claim.

4. **biographical_pattern** — from candidate career data. Medium credibility. May involve interpretation of role titles, company contexts, or career trajectories.

5. **research_general** — LLM inference from general I/O psychology knowledge. Lowest credibility. Capped at 2 per agent. Not grounded in candidate-specific data.

This hierarchy is rendered in the output using visual markers. The synthesis template shows the evidence type alongside each claim. The CHRO can immediately distinguish instrument-grounded claims from LLM inference. This directly addresses Research 09's trust requirements.

---

## Build Plan — Stage E Only

| Task | Hours |
|---|---|
| Layer 0 validation (extended for dual-stream) | 0.5h |
| Layer 1 scenario weights (add CV-derived categories) | 0.25h |
| Layer 1 tension map (add cross-stream detection) | 0.25h |
| Agent system prompts × 3 (mode-aware, CV flag handling) | 2h |
| JSON output schemas (extended evidence types) | 0.5h |
| Layer 3 audit — 8 checks (F04 enhancement primary work) | 2h |
| Layer 3b self-consistency pre-computation | 0.75h |
| Synthesis template (trade-off matrix + 3-layer output) | 1.5h |
| Trade-off matrix frontend component | 1h |
| Scenario switch wiring (re-derivation + re-evaluation) | 0.5h |
| Integration test with synthetic data | 0.5h |
| Timeout + graceful degradation (F16) | 0.25h |
| **Stage E total** | **~10h** |

### What to Cut If Time-Pressured

First cut: reduce Layer 3b from 3× to 1× self-consistency run per scenario. Saves ~0.25h and reduces pre-computation calls.

Second cut: simplify cross-stream tension detection in tension map to hardcoded domain mapping instead of dynamic lookup. Saves ~0.15h.

Third cut: drop Layer 3 (full evidence trail) from the frontend — keep it in the data model but don't build the drill-down UI. Judges likely won't click that deep. Saves ~0.5h of frontend work.

Fourth cut: accept a simpler trade-off matrix without animated row reordering. Use a static re-render instead of CSS transitions. Saves ~0.25h but loses demo impact.
