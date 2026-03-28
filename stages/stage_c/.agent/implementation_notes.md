# Stage C — Implementation Notes

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Module Structure

```
stages/stage_c/src/stage_c/
├── __init__.py
├── c1_jd_extraction.py      # JD → requirements (1 LLM call + 4 validation checks)
├── c2_priority_resolution.py # requirements + active scenario → resolved priorities (deterministic read)
├── c3_cv_assessment.py       # requirements + CVs → rubric assessments (3 parallel LLM calls)
├── c4_rubric_bridge.py       # rubric assessments + active priorities → CV-derived flags (deterministic)
├── prompts/
│   ├── jd_extraction.py      # C1 system prompt + output schema (includes scenario descriptions for priority assignment)
│   └── cv_assessment.py      # C3 system prompt + output schema
├── validation.py             # C1 post-extraction checks, C3 drop detection + citation check
└── pipeline.py               # C1→C2→C3→C4 orchestration, produces StageCOutput
```

## LLM Client

Use `httpx.AsyncClient` for all LLM calls. C3's three candidate calls run via `asyncio.gather()`. Do not use `aiohttp` — httpx is already a project dependency and its async API is cleaner.

All LLM calls go through a single `llm_client.py` in shared utilities (not in stage_c). This shared client handles: API key from env, model selection, retry with exponential backoff (max 2 retries), timeout (30s per call), response parsing, and structured logging of token usage.

## Prompt Design

C1 and C3 prompts must enforce JSON-only output. Use a system prompt that ends with: "Respond ONLY with a valid JSON array. No markdown, no backticks, no preamble." Include a 1-shot example in the system prompt showing the exact output format expected.

C1 prompt includes brief descriptions of all 5 scenarios (2-3 sentences each) so the LLM can assign per-scenario priorities in the same extraction call. The LLM judges "is this requirement critical under turnaround?" directly from the requirement text — no type classification intermediate step. This is more accurate than the two-hop proxy and costs zero additional tokens since it's in the same call.

C3 prompt receives requirements ordered by active priority (high first). The prompt includes requirement_id, requirement_text, and assessable_from_cv for each requirement. Requirements with assessable_from_cv=false are excluded from the prompt entirely — the bridge handles them as CV_BEHAVIORAL_ROUTED.

## Scenario Independence

C3 rubric assessments are scenario-independent — the rubric level (EXCEEDS/MEETS/PARTIAL/GAP) depends only on the CV content vs the requirement text, not on the requirement's priority. Priority only affects WHICH FLAGS are generated in C4, not the assessment itself. This is why C3 results can be cached across scenario switches.

C1 extraction is ALSO scenario-independent in a sense: the `scenario_priority` fields cover ALL scenarios in one extraction. When the scenario switches, C1 does not re-run — the requirement's priority for the new scenario is already stored on the requirement object. Only C2 (priority resolution) and C4 (bridge) need to re-read with the new scenario name.

## Key Invariants

- len(rubric_assessments) == len(cv_assessable_requirements) × len(candidates)
- Every RubricAssessment has exactly one of the 5 rubric levels
- Every EXCEEDS/MEETS/PARTIAL has a non-empty cv_citation
- Every requirement_id in assessments references a valid Requirement
- Every Requirement has scenario_priority with all 5 scenarios populated
- C4 output flag count ≤ len(cv_assessable_requirements) + 3 (pattern flags) per candidate
