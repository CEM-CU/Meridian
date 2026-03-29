# Stage C — Task List

> last_updated: 2026-03-29T02:00:00Z by agent (C1 complete)

## Overview

Stage C transforms raw JD and CV text into structured, typed, citable data. 4 LLM calls total (1 JD + 3 batched CV). Latency: ~6-8s. Everything downstream depends on the quality of this extraction.

## Tasks (ordered by dependency)

### C1: JD Requirement Extraction [DONE]
- **Input:** Raw JD text string (pasted by user)
- **Output:** list[Requirement] with sequential IDs (REQ-01..REQ-N), assessable_from_cv boolean, scenario_priority per scenario
- **LLM calls:** 1
- **Implementation:**
  - System prompt instructs: extract every discrete requirement, decompose compounds, extract implicit requirements, reframe role descriptions as candidate requirements, ignore boilerplate
  - Output schema: JSON array of Requirement objects
  - Target: 8-15 requirements per JD. Warn below 6, suggest consolidation above 18
  - Requirement text max 200 chars (must work as column header in trade-off matrix)
  - Source quote max 300 chars (verbatim from JD)
  - `assessable_from_cv` boolean — LLM assigns directly. Behavioral/interpersonal/style requirements → false. Everything else → true. LLM is highly reliable on this distinction
  - `scenario_priority` — LLM assigns high/medium/low for each of 5 scenarios in the SAME extraction call (zero additional cost). Prompt includes brief scenario descriptions so the LLM can judge "is post-acquisition integration experience critical under turnaround?" directly from requirement text. This replaces the old type→priority lookup table — more accurate, one fewer classification hop
  - **4 post-extraction validation checks (deterministic, no LLM):**
    1. Schema validation: all fields present, types correct, IDs sequential, scenario_priority has all 5 scenarios
    2. Duplicate detection: >60% keyword overlap in text → flag for review (do not auto-merge)
    3. Routing consistency: if assessable_from_cv=false, verify scenario_priority is irrelevant (behavioral requirements route to personality layer regardless of priority)
    4. Priority override: verify all scenario_priority values are valid (high/medium/low only)
- **Tests:** Mock LLM response → validate all 4 checks fire correctly. Property test: output always has sequential IDs, valid priorities per scenario, boolean assessable_from_cv.

### C2: Active Priority Resolution [NOT STARTED]
- **Blocked by:** C1 (needs requirement list)
- **Input:** list[Requirement] from C1 + ScenarioConfig (active scenario name)
- **Output:** list[tuple[Requirement, Priority]] — each requirement paired with its priority under the active scenario
- **LLM calls:** 0 (purely deterministic read)
- **Implementation:**
  - For each requirement: `active_priority = requirement.scenario_priority.for_scenario(scenario.name)`
  - Behavioral requirements (assessable_from_cv=false): priority is irrelevant — they route to personality layer regardless. Set active_priority to None or a sentinel
  - Demo mode: auto-confirm, no UI pause
  - This is the scenario switch mechanism — when scenario changes, re-run C2 with new scenario name, each requirement resolves to a different priority, everything downstream re-derives
  - **Much simpler than the old C2** — no lookup table, no type classification. Just a field read
- **Tests:** Same requirements, different scenario → different active priorities. Behavioral requirement → routes regardless.

### C3: CV Rubric Assessment [NOT STARTED]
- **Blocked by:** C1 (needs requirement list with types for routing)
- **Input:** list[Requirement] (CV-assessable only) + raw CV text per candidate
- **Output:** list[RubricAssessment] per candidate
- **LLM calls:** 1 per candidate (3 total, parallelized)
- **Implementation:**
  - One call per candidate evaluates ALL CV-assessable requirements for that candidate
  - Requirements ordered by priority (high first) in prompt — quality degrades toward end of long outputs, so high-priority assessed first
  - Rubric: 5 levels (EXCEEDS, MEETS, PARTIAL, GAP, NOT_ASSESSABLE) — strictly defined in prompt
  - Mandatory citation for EXCEEDS/MEETS/PARTIAL (specific CV passage + location). If LLM returns MEETS/EXCEEDS without citation → deterministic downgrade to GAP + log CITATION_MISSING
  - Confidence tagging: high (direct, unambiguous), medium (requires inference), low (indirect/interpretive)
  - Investigation question for every GAP, PARTIAL, or low-confidence — specific, not generic
  - **Requirement drop detection safeguard:** After batched call returns, verify every input requirement_id appears in output. If any missing, run targeted follow-up call for missing requirements only. Normal: 3 calls. Worst case: 4-5 calls.
- **Tests:** Mock LLM response with dropped requirement → verify follow-up fires. Mock response with missing citation on MEETS → verify downgrade to GAP. Property test: output has exactly one assessment per requirement per candidate.

### C4: Rubric-to-Flag Bridge [DONE]
- **Blocked by:** shared models (Flag, RubricAssessment)
- **Input:** list[RubricAssessment] per candidate + list[Requirement] + active scenario name
- **Output:** list[Flag] with evidence_type cv_rubric/requirement_gap/cv_pattern/routing
- **LLM calls:** 0 (deterministic mapping)
- **Implementation:**
  - Resolve active priority per requirement: `requirement.scenario_priority.for_scenario(scenario_name)`
  - Mapping rules (rubric_level × active_priority → flag):
    - GAP on high-priority → `CV_GAP` flag with priority=high in metadata
    - GAP on medium-priority → `CV_GAP` flag with priority=medium in metadata
    - GAP on low-priority → no flag (background noise at finalist stage)
    - PARTIAL on high-priority → `CV_PARTIAL` flag with priority=high
    - EXCEEDS on high-priority → `CV_EXCEEDS` flag with priority=high
    - EXCEEDS on medium-priority → `CV_EXCEEDS` flag with priority=medium (positive signal still worth surfacing)
    - MEETS → no flag (baseline)
    - NOT_ASSESSABLE on behavioral → `CV_BEHAVIORAL_ROUTED` (routing signal)
  - **Specialized variants are GONE.** No CV_SCOPE_GAP, CV_INDUSTRY_MISMATCH, CV_SCOPE_EXCEEDS. The requirement text carries the domain context — agents read "GAP on REQ-05: P&L responsibility $500M+" directly. The priority metadata determines weight
  - Pattern-level flags (post-mapping, per candidate):
    - 3+ low-confidence assessments → CV_LOW_CONFIDENCE_CLUSTER
    - >50% high-priority requirements are GAP → CV_SYSTEMATIC_GAP
    - >60% requirements are EXCEEDS → metadata warning (not a flag)
  - Every flag carries full provenance: requirement_id, requirement_text, active_priority, rubric_level, cv_citation, cv_location, confidence, notes, investigation_question
  - topic_keywords derived from requirement text vocabulary
- **Tests:** Unit test every mapping rule. Property test: flag count ≤ requirement count + pattern flags. No flag references a non-existent requirement_id. All CV flags have valid evidence_type.

### C Integration Test [NOT STARTED]
- **Blocked by:** C1-C4 all complete
- **Input:** Synthetic BMW CTO JD + 3 candidate CVs
- **Output:** Verify full C1→C2→C3→C4 pipeline produces valid StageCOutput
- **Checks:** All requirements extracted, all priorities assigned, all candidates assessed, all flags have valid provenance, flag count in expected range (6-10 per candidate)
