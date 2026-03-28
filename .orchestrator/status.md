# Project Status

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Overall

Phase: BOOTSTRAP COMPLETE — ready for Layer 0 (shared models + test fixtures)
Build window: ~16h remaining
Active worktrees: none

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
| C1: JD extraction prompt + schema + validation | NOT STARTED | shared models | 0.5h |
| C2: Active priority resolution (scenario read) | NOT STARTED | C1 | 0.05h |
| C3: CV rubric assessment prompt + schema + drop detection | NOT STARTED | C1 (needs requirement list) | 0.75h |
| C4: Rubric-to-flag bridge (deterministic) | NOT STARTED | shared models (Flag) | 0.4h |
| C integration test | NOT STARTED | C1-C4 | 0.25h |

## Stage D — Flag Derivation (Deterministic)

| Task | Status | Blocked By | Est. Hours |
|---|---|---|---|
| Personality flag derivation (Big Five thresholds) | NOT STARTED | shared models | 1.5h |
| CV flag stream validation | NOT STARTED | C4 output format | 0.25h |
| Merge (concatenation + ordering) | NOT STARTED | personality flags + CV validation | 0.25h |
| Validation Layer 0 (5 checks) | NOT STARTED | merge | 0.75h |
| Assessment mode determination | NOT STARTED | shared models | 0.25h |
| Output assembly (StageDOutput) | NOT STARTED | all above | 0.25h |
| D integration test | NOT STARTED | all above | 0.25h |

## Stage E — Multi-Agent Evaluation + Synthesis

| Task | Status | Blocked By | Est. Hours |
|---|---|---|---|
| Layer 0: Stage D output validation | NOT STARTED | StageDOutput contract | 0.5h |
| Layer 1: Scenario weights + signal computation + tension map | NOT STARTED | Layer 0 | 0.5h |
| Layer 2: Agent prompts × 3 (mode-aware) | NOT STARTED | Layer 1 | 2h |
| Layer 2: JSON output schemas | NOT STARTED | shared models | 0.5h |
| Layer 3: Audit (8 checks) | NOT STARTED | Layer 2 | 2h |
| Layer 3b: Self-consistency pre-computation | NOT STARTED | Layer 3 | 0.75h |
| Synthesis template (trade-off matrix + 3-layer output) | NOT STARTED | Layer 3 | 1.5h |
| Synthesis trade-off statement (1 LLM call) | NOT STARTED | synthesis template | 0.25h |
| Scenario switch wiring | NOT STARTED | all above | 0.5h |
| Timeout + graceful degradation (F16) | NOT STARTED | Layer 2 | 0.25h |
| E integration test | NOT STARTED | all above | 0.5h |

## Test Fixtures

| Component | Status | Notes |
|---|---|---|
| Synthetic BMW CTO JD | NOT STARTED | — |
| Synthetic candidate CVs × 3 | NOT STARTED | — |
| Big Five presets (5 archetypes) | NOT STARTED | — |
| Expected flag outputs (golden) | NOT STARTED | after D is built |

## Parallelization Windows

Layer 0 (now): shared models ✓ + test fixtures (parallelizable)
Layer 1 (next): D personality flags ∥ C4 bridge (both depend only on shared models)
Layer 2: C1 ∥ C3 (both depend on Requirement model, not on each other)
Layer 3: D merge+validation (needs Layer 1 done)
Layer 4: E (needs Stage D done)
