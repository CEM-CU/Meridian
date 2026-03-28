# Stage E — Implementation Notes

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Module Structure

```
stages/stage_e/src/stage_e/
├── __init__.py
├── layer0_validation.py       # E1: Stage D output validation
├── layer1_weights.py          # E2: scenario weights, signal labels, risk bands, tension map
├── layer2_agents/
│   ├── __init__.py
│   ├── base.py                # shared agent runner (LLM call, timeout, JSON parse)
│   ├── role_fit.py            # "The Researcher" — allowlist, prompt template
│   ├── team_dynamics.py       # "The Devil's Advocate" — allowlist, prompt template
│   ├── risk.py                # "The Risk Analyst" — allowlist, prompt template
│   ├── allowlists.py          # canonical allowlist per agent (data, not logic)
│   └── prompts/
│       ├── preamble.py        # mode-aware preamble templates (full/partial)
│       └── agent_prompts.py   # per-agent system prompts
├── layer3_audit/
│   ├── __init__.py
│   ├── checks.py              # 8 audit checks (F02-F14)
│   └── f04_citation.py        # biographical reference validation (substring matching)
├── layer3b_consistency.py     # self-consistency pre-computation
├── synthesis/
│   ├── __init__.py
│   ├── template.py            # 3-layer output assembly
│   ├── tradeoff_matrix.py     # requirement × candidate grid
│   ├── contested_signals.py   # F12 detection
│   └── provenance.py          # provenance header assembly
├── schemas.py                 # AgentVerdict, Claim, EvidenceBasis Pydantic models
└── pipeline.py                # Layer 0→1→2→3→3b→Synthesis orchestration
```

## Agent Runner Pattern

All three agents share the same execution pattern (base.py): receive filtered flags via allowlist, inject into prompt template with mode-aware preamble, call LLM with JSON output instruction, parse response, validate against schema, return AgentVerdict. The per-agent modules only define the allowlist and the prompt template — execution logic is shared.

`asyncio.gather()` runs all three in parallel. Each wrapped in `asyncio.wait_for(timeout=15)`. On timeout: return partial AgentVerdict with `timed_out=True` and whatever partial output was received.

## Agent Allowlists (canonical, in allowlists.py)

Role-Fit: EXECUTION, STRATEGIC, CULTURAL, EXPERIENCE_STRENGTH, EXPERIENCE_GAP
Team Dynamics: COLLISION, COMPLEMENT, FRICTION, GROUPTHINK, INTEGRATION, ROUTING
Risk: DERAILMENT, DARK_SIDE, TENURE, EXPERIENCE_GAP, EVIDENCE_QUALITY

Note EXPERIENCE_GAP appears in both role-fit and risk — intentional. Role-fit interprets it as "candidate doesn't match requirements." Risk interprets it as "candidate may fail because they lack qualifications." Different mandate, same flag.

CV flags are now generic (CV_GAP, CV_PARTIAL, CV_EXCEEDS) — the requirement text on the flag carries domain context. Agents read "GAP on REQ-05: P&L responsibility $500M+" directly instead of inferring domain from a specialized flag name like CV_SCOPE_GAP.

## F04 Citation Validation

The strongest anti-fabrication check. Raw CV text is NOT in agent prompts — agents work from structured flags. But agents may re-cite CV passages from the flags they receive. F04 validates these citations against the actual CV text.

Implementation: normalize both the cited text and the CV text (lowercase, collapse whitespace, strip punctuation). Use fuzzy substring matching (e.g., difflib.SequenceMatcher with ratio > 0.7) rather than exact match — agents may paraphrase slightly. If the agent claims a number ($800M) that doesn't appear in the CV, that's a hard fail regardless of text similarity.

Numerical extraction: regex for dollar amounts, percentages, team sizes, year counts. Compare extracted numbers between citation and CV text. Mismatch = fabrication.

## Evidence Credibility Hierarchy (rendered in output)

1. scored_flag — Big Five instrument, deterministic thresholds. Highest.
2. cv_rubric — structured rubric evaluation of CV passage vs JD requirement. High.
3. requirement_gap — confirmed absence after systematic CV search. High for negatives.
4. biographical_pattern — career data interpretation. Medium.
5. research_general — LLM inference from I/O psychology. Lowest. Capped at 2/agent.

## Key Invariants

- Agents never see signal-strength labels or risk bands (F02)
- Agents only cite flags from their allowlist (Check 2)
- Every claim has evidence_basis with type from the 5-value enum
- research_general ≤ 2 per agent (Check 7)
- CV rubric citations validate against raw CV text (Check 5)
- Synthesis template never adds new analysis beyond the 1 constrained LLM call
