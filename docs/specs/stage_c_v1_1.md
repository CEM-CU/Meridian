# Stage C v1.1 — CV-JD Extraction & Rubric Assessment

> BMW Hackathon C-Suite Decision Intelligence Tool — March 28, 2026
>
> New stage between wizard input and Stage D. Transforms raw JD and CV
> text into structured, typed, citable data. Stage D consumes the output
> deterministically.
>
> LLM calls: 4 total (1 JD extraction + 3 batched CV assessments).
> Latency: ~6-8s (JD extraction first, then 3 candidate calls in parallel).
> Build time: ~2.5h.

---

## C1: JD Requirement Extraction

### Purpose

One LLM call reads JD text and extracts a flat list of discrete, typed requirements. Each requirement is one assessable claim about what the candidate must have, must have done, or must be able to do.

### Requirement Type Taxonomy

Closed set of 9 types. The LLM selects from these — no free-form types allowed. The type determines two things downstream: whether the requirement routes to CV assessment or personality assessment, and which default priority it receives under each scenario.

**experience_depth** — years in function, role, or industry. CV-assessable by counting employment dates. Example: "10+ years in automotive or adjacent manufacturing."

**experience_breadth** — range of functional areas covered. CV-assessable by counting distinct domains across career history. Example: "Cross-functional experience spanning operations and finance."

**scope** — team size, revenue/budget responsibility, geographic span of authority. CV-assessable but frequently requires inference because CVs often omit numbers. This is the most common source of medium-confidence assessments. Example: "P&L responsibility for business unit of $500M+."

**industry** — specific sector requirements. CV-assessable by matching company names and described sectors. Example: "Direct experience in premium automotive or luxury goods."

**geographic** — international or regional experience. CV-assessable, though often implicit from company locations rather than explicitly stated. Example: "Experience leading teams across EMEA and APAC."

**technical** — specific domain or technical knowledge. Partially CV-assessable — CV shows roles in relevant areas but cannot confirm knowledge depth. Example: "Deep understanding of EV powertrain or software-defined vehicle architecture."

**leadership_context** — prior experience with specific strategic situations. Partially CV-assessable — CV may show the candidate was present during a transformation or acquisition but not whether they led it. Example: "Track record of leading post-acquisition integration."

**qualification** — education, certification, language ability. Fully CV-assessable for degrees and certifications. Partially CV-assessable for language — may require inference from nationality and work locations. Example: "MBA or equivalent; fluent German and English."

**behavioral** — leadership style, interpersonal qualities, personality-dependent capabilities. NOT CV-assessable. These requirements are tagged `assessable_from_cv: false` and route entirely to the personality assessment layer in Stage D. The CV agent must assign `not_assessable` for these and move on. Example: "Ability to navigate complex stakeholder environments in consensus-driven culture."

### Extraction Rules

The LLM must decompose compound requirements. "10 years automotive AND P&L responsibility" becomes two entries — one experience_depth, one scope. Without decomposition, the rubric assessment is ambiguous: what does "partial" mean when the candidate has 14 years automotive but no P&L?

The LLM must extract implicit requirements. "Lead our digital transformation across all plants and regions" contains at minimum: scope (all plants implies large team), leadership_context (transformation), geographic (multi-region). Each becomes a separate requirement.

Target count: 8-15 requirements per JD. Below 6 triggers a warning that the JD is too vague. Above 18 triggers a consolidation suggestion. Most C-suite JDs land at 10-14.

Each requirement carries: a sequential ID (REQ-01 through REQ-N), the type, a normalized requirement statement (max 200 characters — must work as a column header in the trade-off matrix), a verbatim or near-verbatim source quote from the JD (max 300 characters), the `assessable_from_cv` boolean, and a null priority field. Priority is always null on extraction — the recruiter or scenario defaults assign it in C2.

### Validation After Extraction

Five deterministic checks run after the LLM returns.

Schema validation: all fields present, types correct, IDs sequential, requirement type from closed set.

Duplicate detection: if two requirements share the same type AND >60% keyword overlap in their text field, flag for recruiter review. Do not auto-merge — the recruiter decides. This catches the LLM extracting "10 years technology leadership" and "decade of experience leading technology teams" as separate requirements.

Routing consistency: every behavioral type must have `assessable_from_cv: false`. If violated, auto-correct to false and log.

Coverage check: if fewer than 3 requirement types are represented, warn that extraction may be too narrow.

Priority override: if the LLM assigned any non-null priority despite instructions, reset to null and log.

### Edge Cases

**JD is a single paragraph.** Common for internal postings or LinkedIn descriptions. Extraction will produce 5-8 requirements. Warn: "Brief job description — consider adding requirements manually."

**JD is in German.** Extraction works in both languages. Requirement text stays in the JD's language. Type taxonomy labels remain in English (internal system labels only, not shown to CHRO).

**JD contains boilerplate.** Equal opportunity statements, company descriptions, benefits. The prompt must instruct: extract only candidate requirements, ignore everything else.

**JD describes the role, not the candidate.** "This role will lead digital transformation" must be reframed as "Track record of leading digital transformation initiatives." The LLM reframes role descriptions as candidate requirements.

---

## C2: Recruiter Confirmation

### Two Modes

**Demo mode (auto-confirm).** Requirements extracted, scenario-based default priorities applied automatically, pipeline continues. The demo video shows the requirement list briefly (3-5 seconds of screen time) but does not pause.

**Live test mode (interactive).** Requirements shown in a sortable list. The judge can reorder (top = highest priority), delete, edit text, and click confirm. Expected interaction: 1-3 minutes.

### Scenario Priority Defaults

Each scenario maps a default priority (high/medium/low) to each requirement type. This is how scenario switching re-prioritizes JD requirements — and it's what makes the trade-off matrix shift.

**Digital transformation:** technical=high, leadership_context=high, scope=high. experience_depth=medium, industry=medium, geographic=medium. experience_breadth=low, qualification=low.

**Post-acquisition integration:** leadership_context=high, geographic=high, scope=high. experience_breadth=medium, industry=medium, qualification=medium. technical=low, experience_depth=low.

**Turnaround:** leadership_context=high, scope=high, experience_depth=high. industry=medium, experience_breadth=medium. technical=low, geographic=low, qualification=low.

**Stabilization:** experience_depth=high, industry=high, scope=high. qualification=medium, geographic=medium. leadership_context=low, technical=low, experience_breadth=low.

**Growth:** scope=high, leadership_context=high, experience_breadth=high. technical=medium, industry=medium, geographic=medium. experience_depth=low, qualification=low.

Behavioral requirements always receive `routed_to_personality` regardless of scenario.

### The Scenario Switch Mechanism

When the scenario changes, priority defaults re-apply. Rows in the trade-off matrix re-sort by new priorities. A requirement that was low priority under digital transformation becomes high priority under turnaround. The same candidate who had all green on high-priority rows now has a red gap on a newly critical row. This is deterministic — no LLM call needed for the re-sort.

---

## C3: Batched CV Rubric Assessment

### Architecture: One Call Per Candidate

Each LLM call evaluates ALL CV-assessable requirements for ONE candidate. Output is a JSON array of rubric entries — one entry per requirement. Three candidates = three parallel calls. Total latency: ~5-6 seconds.

This replaced the original per-requirement design (36 calls, ~50-60s). Auditability is preserved in the output schema, not the call structure — each entry in the array has its own citation, rubric level, confidence tag, and notes field. The recruiter inspects and overrides individual cells regardless of how many LLM calls produced them.

### Why Batching Is Safe Here

The per-requirement isolation argument assumes LLMs suffer halo effects when evaluating multiple dimensions simultaneously. This is true for holistic judgment ("rate this candidate overall") but much less true for independent factual extraction ("does this CV contain evidence for requirement X?"). Each rubric assessment is a lookup task — search the CV for specific evidence, cite it or say "not found," assign a level. These are parallel searches in the same document, not comparative judgments. Batching 12 lookups doesn't create cross-contamination the way batching 12 judgment calls would.

### Safeguard: Requirement Drop Detection

After the batched call returns, a deterministic check verifies every requirement_id from the input appears in the output. If any requirement is missing (the LLM dropped it — happens in ~5-10% of batched calls, usually affecting 1-2 requirements), run a single targeted follow-up call for the missing requirements only. Normal case: 3 calls. Worst case: 4-5 calls and ~8-10 seconds.

### Ordering Within the Batch

Requirements are ordered by priority (high first) in the prompt. LLMs sometimes lose output quality toward the end of long structured responses. By placing high-priority requirements first, any quality degradation affects low-priority assessments — where the impact on the trade-off matrix is minimal.

### The Rubric

Five levels, strictly defined. The LLM picks exactly one per requirement.

**EXCEEDS.** CV evidence clearly surpasses the requirement. Shows MORE than what was asked for. Only assign when the surplus is unambiguous — "P&L $500M+ required, CV shows $1.2B standalone P&L" is exceeds. "P&L $500M+ required, CV shows $520M" is meets, not exceeds.

**MEETS.** CV evidence satisfies the requirement as stated. Direct, clear match. No inference needed.

**PARTIAL.** Some evidence exists but with identifiable gaps. Related but not directly matching experience, or insufficient depth/duration. The assessment must explain specifically what is present AND what is missing. This is the most useful rubric level for the recruiter — it tells them exactly where to probe.

**GAP.** No supporting evidence found in the CV. The LLM searched the entire document and found nothing addressing this requirement. This is not a failure — it's the correct answer when evidence doesn't exist.

**NOT_ASSESSABLE.** The requirement cannot be evaluated from CV data alone. Used exclusively for behavioral requirements and for requirements so vague that no CV evidence could meaningfully address them.

### Mandatory Evidence Citation

For every EXCEEDS, MEETS, or PARTIAL, the LLM must cite a specific CV passage with approximate location (role name, section, paragraph). If the LLM assigns MEETS or EXCEEDS without a citation, the deterministic audit downgrades to GAP and logs CITATION_MISSING. This is the strongest anti-fabrication constraint in Stage C.

For GAP and NOT_ASSESSABLE, no citation is needed — the output records "not found" or "routed to personality layer."

### Confidence Tagging

Each assessment carries high, medium, or low confidence.

**High:** direct, unambiguous evidence. Explicit years, explicit team sizes, explicit revenue figures, named degrees.

**Medium:** evidence requires inference. "Led EMEA expansion" implies international scope but doesn't name countries. "Managed cross-functional teams" without specifying size. Role title implies scope but isn't explicit.

**Low:** evidence is indirect or heavily interpretive. Candidate was at a company during a transformation but their role in it is unclear. Title could mean different things in different organizations.

Downstream effects: high-confidence meets/exceeds generate flags with no investigation question. Medium-confidence anything generates a flag plus an investigation question. Low-confidence anything generates a flag with EVIDENCE_QUALITY marker, mandatory investigation question, and prominent surfacing in output.

### Investigation Question Generation

For every GAP, PARTIAL, or low-confidence assessment, the LLM generates a specific investigation question referencing the requirement and the evidence gap. Not generic — specific. "Clarify whether the $620M divisional budget constituted standalone P&L ownership or was a cost center within a larger business unit — the distinction affects scope assessment."

These questions are collected across all candidates and surfaced in the final output as "Questions for interview follow-up." This is what Research 09 says CHROs want — the tool identifies what to probe, not just what to conclude.

### Edge Cases

**CV is very short (1-paragraph LinkedIn summary).** Most requirements will be GAP or low-confidence PARTIAL. Correct behavior. If GAP percentage exceeds 70%, add top-level warning: "CV is brief — assessment is limited. Request a detailed CV for complete analysis."

**CV is very long (10+ pages).** LLM may find multiple conflicting evidence passages. Instruction: cite the MOST RELEVANT passage to the specific requirement and note conflicts in the notes field. "Most recent role shows team of 15 (startup). Previous role at Siemens shows team of 200 (enterprise). JD requires enterprise-scale — Siemens evidence more relevant but 3 years old."

**Same CV passage applies to multiple requirements.** A single sentence about leading a $2B acquisition touches scope, leadership_context, geographic, and experience_breadth. The LLM will cite it for multiple assessments. This is correct — the same evidence can support multiple requirements.

**CV language doesn't match JD language.** JD says "transformation experience," CV says "organizational redesign." The LLM must match by meaning, not keywords. The prompt explicitly instructs semantic matching. Confidence should be MEDIUM when the match is semantic rather than lexical.

**Experience exists but is old.** Candidate managed 800 people 8 years ago, current team is 40. Assign MEETS (experience exists) but note recency: "Relevant experience from 2016-2019. Current role significantly smaller scope. Recency may affect transferability."

**LLM fabricates a citation.** Claims the CV says "managed $800M P&L" when it actually says "$80M budget." Stage C cannot catch this alone. Stage E's F04 (biographical reference validation) catches it by checking citations against raw CV text. This is why raw CV text must be passed through to Stage E as ground truth — not just the structured extraction output.

**Requirement is impossible.** "20 years EV experience" when the EV industry is ~15 years old. Assign GAP and note: "Requirement may exceed industry timeline — no candidate likely to fully meet this."

**All three candidates get identical assessments.** If assessments are nearly identical, the matrix provides no differentiation. Surface: "Minimal differentiation across candidates. Consider adding more specific requirements or using personality analysis."

---

## C4: Rubric-to-Flag Bridge

### Purpose

Deterministic function (no LLM call) converting rubric assessments into flags compatible with Stage D's flag vocabulary. This is the Path B integration point where CV evidence enters the flag pipeline.

### Mapping Rules

**GAP on high-priority requirement → flag.** Generates `CV_GAP_HIGH_PRIORITY`. Specialized variants: scope-type gaps generate `CV_SCOPE_GAP`, industry-type gaps generate `CV_INDUSTRY_MISMATCH`. These are the strongest negative CV signals — confirmed absence of evidence for critical requirements.

**GAP on medium-priority requirement → flag.** Generates `CV_GAP_MEDIUM_PRIORITY`. Low-priority gaps generate no flag — background noise at the finalist stage.

**PARTIAL on high-priority requirement → flag.** Generates `CV_PARTIAL_HIGH_PRIORITY`. Carries both what was found AND what is missing. Most nuanced flag — tells the recruiter exactly where to probe.

**EXCEEDS on high-priority requirement → flag.** Generates `CV_EXCEEDS_HIGH_PRIORITY`. Specialized: scope-type exceeds generates `CV_SCOPE_EXCEEDS`. Positive valence flags counterbalancing gap flags in synthesis.

**MEETS generates no flag.** Meeting a requirement is baseline at the finalist stage. Flags signal deviations — positive or negative — from baseline.

**NOT_ASSESSABLE on behavioral → flag.** Generates `CV_BEHAVIORAL_ROUTED`. Routing signal, not assessment. Tells the personality layer in Stage D: this requirement exists, the CV couldn't address it, you handle it via Big Five data.

### Pattern-Level Flags

After individual mapping, the bridge runs cross-assessment pattern detection per candidate.

**Low confidence cluster.** 3+ assessments have low confidence → `CV_LOW_CONFIDENCE_CLUSTER`. Indicates the CV is thin, ambiguous, or poorly structured. Overall assessment reliability is reduced.

**Systematic gap.** More than 50% of high-priority requirements are GAP → `CV_SYSTEMATIC_GAP`. Qualitatively different from individual gaps — suggests fundamental misalignment between candidate and role.

**Overqualification anomaly.** More than 60% of requirements are EXCEEDS → metadata warning (not a flag). Massive overqualification may indicate the role is a step down. Surfaced for recruiter consideration.

### Flag Metadata

Every CV-derived flag carries full provenance: requirement_id, requirement_text, requirement_priority, rubric_level, cv_citation (the specific passage from the CV), cv_location (where in the CV), confidence tag, notes, and investigation_question (if applicable). This provenance chain is what makes F04 in Stage E able to validate these flags against the raw CV text.

### What Feeds Into Stage D

Stage D receives from C4: a list of CV-derived flags with evidence_type `cv_rubric`, `requirement_gap`, `cv_pattern`, or `routing`. These merge with personality-derived flags (if Big Five scores are available) into a single flag set. The merge is simple concatenation — no conflict resolution, no deduplication. Both streams provide independent signals.

---

## Updated Build Plan

| Task | Hours |
|---|---|
| JD extraction prompt + output schema + validation | 0.5h |
| Batched CV assessment prompt + output schema | 0.75h |
| Requirement drop detection safeguard | 0.15h |
| Rubric-to-flag bridge (deterministic mapping) | 0.5h |
| Scenario priority defaults (5 scenarios × 9 types) | 0.15h |
| Wizard UI: JD paste + CV paste + confirmation step | 0.25h |
| Integration test: full C1→C4 pipeline with synthetic data | 0.25h |
| **Stage C total** | **~2.5h** |

### What to Cut If Time-Pressured

First cut: drop interactive confirmation (C2 live mode) — auto-confirm only. Saves 0.15h build + removes a UI component.

Second cut: drop pattern-level flags (low confidence cluster, systematic gap, overqualification). Individual flags are sufficient for demo. Saves 0.15h.

Third cut: reduce max requirements from 15 to 10. Fewer requirements = shorter outputs = lower quality-degradation risk on batched calls. Saves ~0.1h on validation edge cases.
