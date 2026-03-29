# Project Status

> last_updated: 2026-03-29T21:00:00Z by agent (A4 SSE review fixes — 10 issues fixed: task leak, CancelledError, timeouts, evidence_types, per_candidate provenance, signal labels/bands/tensions, agent summary+evidence_types+unaddressed, full SynthesisOutput in SYNTHESIS_COMPLETE, event ordering test, test file split; 88 tests passing; ruff + pyright clean)

## Overall

Phase: BOOTSTRAP COMPLETE — ready for Layer 0 (shared models + test fixtures)
Build window: ~16h remaining
Active worktrees: none

## Shared Utilities

| Component | Status | Notes |
|---|---|---|
| sanitize.py | DONE | sanitize_for_prompt — F18 prompt injection prevention; used by stage_c jd_extraction and C3 cv_assessment |
| llm_client.py | DONE | AnthropicClient (httpx + Anthropic Messages API) + MockLLMClient; satisfies LLMClient Protocol; 14 tests passing; ruff + pyright clean |

## Shared Models

| Component | Status | Notes |
|---|---|---|
| requirements.py | DONE (bootstrap) | Requirement, Priority, ScenarioPriority (no RequirementType — killed by patch) |
| rubric.py | DONE (bootstrap) | RubricAssessment, RubricLevel, Confidence |
| flags.py | DONE (bootstrap) | Flag, FlagCategory, Valence, EvidenceType |
| candidates.py | DONE (bootstrap) | CandidateData, BigFiveScores, TeamMember |
| scenarios.py | DONE (bootstrap) | ScenarioConfig, ScenarioName (no SCENARIO_PRIORITY_DEFAULTS — killed by patch) |
| pipeline.py | DONE (bootstrap) | StageCOutput, StageDOutput, FlagProvenance, AssessmentMode |

## Stage C — JD Extraction + CV Rubric Assessment

| Task | Status | Blocked By | Est. Hours |
|---|---|---|---|
| C1: JD extraction prompt + schema + validation | DONE | shared models | 0.5h |
| C2: Active priority resolution (scenario read) | DONE | C1 | 0.05h |
| C3: CV rubric assessment prompt + schema + drop detection | DONE | C1 (needs requirement list) | 0.75h |
| C4: Rubric-to-flag bridge (deterministic) | DONE | shared models (Flag) | 0.4h |
| C integration test | NOT STARTED | C1-C4 | 0.25h |

## Stage D — Flag Derivation (Deterministic)

| Task | Status | Blocked By | Est. Hours |
|---|---|---|---|
| Personality flag derivation (Big Five thresholds) | DONE | shared models | 1.5h |
| CV flag stream validation | DONE | C4 output format | 0.25h |
| Merge (concatenation + ordering) | DONE | personality flags + CV validation | 0.25h |
| Validation Layer 0 (5 checks) | DONE | merge | 0.75h |
| Assessment mode determination | DONE | shared models | 0.25h |
| Output assembly (StageDOutput) | DONE | all above | 0.25h |
| D integration test | DONE | all above | 0.25h |

## Stage E — Multi-Agent Evaluation + Synthesis

| Task | Status | Blocked By | Est. Hours |
|---|---|---|---|
| Layer 0: Stage D output validation | DONE | StageDOutput contract | 0.5h |
| Layer 1: Scenario weights + signal computation + tension map | DONE | Layer 0 | 0.5h |
| Layer 2: Agent prompts × 3 (mode-aware) | DONE | Layer 1 | 2h |
| Layer 2: JSON output schemas | DONE | shared models | 0.5h |
| Layer 3: Audit (8 checks) | DONE | Layer 2 | 2h |
| Layer 3b: Self-consistency pre-computation | DONE | Layer 3 | 0.75h |
| Synthesis template (trade-off matrix + 3-layer output) | DONE | Layer 3 | 1.5h |
| Synthesis trade-off statement (1 LLM call) | DONE | synthesis template | 0.25h |
| Scenario switch wiring | DONE | E8 — scenario_switch.py, 6 tests | 0.5h |
| Timeout + graceful degradation (F16) | DONE | Layer 2 | 0.25h |
| E integration test | NOT STARTED | all above | 0.5h |

## Test Fixtures

| Component | Status | Notes |
|---|---|---|
| Synthetic BMW CTO JD | DONE | tests/fixtures/synthetic_jd.py — 12+ extractable requirements |
| Synthetic candidate CVs × 3 | DONE | tests/fixtures/synthetic_candidates.py — Marcus, Sarah, Kenji |
| Big Five presets (5 archetypes) | DONE | tests/fixtures/big_five_presets.py — 5 archetypes |
| conftest.py fixtures | DONE | tests/conftest.py — 9 fixtures + 12 requirements + 30 rubric assessments |
| Expected flag outputs (golden) | NOT STARTED | after D is built |

## API Layer

| Component | Status | Notes |
|---|---|---|
| A1: FastAPI skeleton | DONE | api/app.py — GET /health, CORS, lifespan stub; 2 tests passing |
| A3: SSE event schema + stream helpers | DONE | api/sse/events.py (19 event types, 19 payload models, PAYLOAD_MODELS map) + api/sse/stream.py (format_sse_event, sse_response_generator); 39 tests passing |
| A4: Pipeline SSE Wrapper | DONE (reviewed) | api/sse/pipeline_stream.py — 10 review fixes applied: task leak guard, CancelledError handling, wait_for timeouts on C1+synthesis, evidence_types breakdown, per_candidate provenance in STAGE_D_COMPLETE, signal_labels+risk_bands+tensions in SIGNALS_COMPUTED, summary+evidence_types+unaddressed_flags in AGENT_COMPLETE, full SynthesisOutput fields in SYNTHESIS_COMPLETE; api/sse/events.py updated accordingly; api/tests/_pipeline_fixtures.py extracted; ordering test added; 88 tests passing |

## Parallelization Windows

Layer 0 (now): shared models ✓ + test fixtures (parallelizable)
Layer 1 (next): D personality flags ∥ C4 bridge (both depend only on shared models)
Layer 2: C1 ∥ C3 (both depend on Requirement model, not on each other)
Layer 3: D merge+validation (needs Layer 1 done)
Layer 4: E (needs Stage D done)
