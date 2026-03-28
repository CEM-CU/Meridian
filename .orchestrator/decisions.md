# Architectural Decisions Log

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Format

Each entry: `[DATE] DECISION: <what>. RATIONALE: <why>. FILES CHANGED: <list>. DOWNSTREAM IMPACT: <what's now stale>.`

## Entries

[2026-03-29] DECISION: No web framework during build phase. Pure Python packages + Pydantic contracts. FastAPI added as thin shell post-build in ~30min. RATIONALE: Zero framework overhead during 16h sprint. Pydantic models become API schemas with no refactoring. FILES CHANGED: pyproject.toml (no framework deps). DOWNSTREAM IMPACT: None — no code depends on a framework.

[2026-03-29] DECISION: uv workspaces with separate packages per stage + shared package. RATIONALE: Stage isolation — each stage can be tested independently. Shared models enforce contract discipline. FILES CHANGED: pyproject.toml (workspace config), per-stage pyproject.toml. DOWNSTREAM IMPACT: All imports must use package names (e.g., `from shared.models.flags import Flag`).

[2026-03-29] DECISION: Append-only logs for .agent/ and .orchestrator/ files unless explicitly told otherwise. RATIONALE: Prevents accidental data loss from agent overwrites. History is preserved. FILES CHANGED: .orchestrator/*.md, stages/*/.agent/*.md. DOWNSTREAM IMPACT: Files may grow — monitor size.

[2026-03-29] DECISION: Git worktrees per feature within stage, not per stage. Branch naming: feat/<stage>/<component>. RATIONALE: Finer parallelization granularity. Multiple features within a stage can be developed concurrently. FILES CHANGED: None (convention). DOWNSTREAM IMPACT: More branches to manage — orchestrator tracks active worktrees.

[2026-03-29] DECISION: LLM integration tests hit DeepSeek/OpenRouter (cheap), not Anthropic. Marked @pytest.mark.integration, skipped by default. RATIONALE: Cost control + speed. Prompt+schema+parsing validation doesn't need the production model. FILES CHANGED: pytest config, test markers. DOWNSTREAM IMPACT: Integration tests may behave differently than production — note prompt sensitivity.

[2026-03-29] DECISION: Stage C rubric assessments are scenario-independent, cached after initial run. Scenario switch re-runs C2 priority mapping → C4 bridge → D → E only. RATIONALE: The expensive LLM calls (C1+C3) run once. Scenario switch latency ~10-13s instead of ~60s. FILES CHANGED: Pipeline orchestration logic. DOWNSTREAM IMPACT: C3 output must NOT contain scenario-dependent information.

[2026-03-29] DECISION: Kill 9-type requirement taxonomy. Replace with per-requirement `assessable_from_cv` boolean + `scenario_priority` object (one priority per scenario, assigned by LLM during C1 extraction). RATIONALE: Eliminates a classification step that could hallucinate. The LLM judges "is this requirement critical under turnaround?" directly from the requirement text — more accurate than the two-hop proxy of "classify type → look up type priority." Specialized flag variants (CV_SCOPE_GAP, CV_INDUSTRY_MISMATCH, CV_SCOPE_EXCEEDS) replaced by generic CV_GAP/CV_EXCEEDS/CV_PARTIAL with priority in metadata. Saves ~15min build time. FILES CHANGED: shared/models/requirements.py (RequirementType removed, ScenarioPriority added), shared/models/scenarios.py (SCENARIO_PRIORITY_DEFAULTS removed), .orchestrator/interfaces.md (Contract 3, Contract 5 rewritten), all stage .agent/ files updated. DOWNSTREAM IMPACT: C2 step simplified (no type→priority lookup — priorities already on requirements). C4 bridge reads priority from requirement directly. D validation drops type-based checks. E agents see fewer flag names but same information content.
