# CLAUDE.md — Meridian: C-Suite Decision Intelligence Tool

> last_updated: 2026-03-29T00:00:00Z by human

## What This Project Is

Multi-agent evaluation pipeline for C-suite hiring decisions. Stages C→D→E.
Stage C: LLM-based JD extraction + CV rubric assessment (4 LLM calls).
Stage D: Deterministic flag derivation from Big Five scores + CV rubric output. Zero LLM calls.
Stage E: 3 parallel evaluation agents + audit + synthesis (4 LLM calls).
Backend only. No frontend yet. No web framework during build — pure Python packages + Pydantic contracts.

## Reference Specs (read-only, do not modify)

`docs/specs/` contains the original stage design documents. Consult when `.agent/` files lack context for an implementation decision. Do not treat as task lists — use `.agent/tasks.md` for that.

## Before Doing Anything

1. Read `.orchestrator/status.md` — know where the project stands.
2. Read `.orchestrator/blockers.md` — know what's blocked on what.
3. Read `.orchestrator/interfaces.md` — know the inter-stage contracts.
4. If working on a specific stage, read `stages/<stage>/.agent/tasks.md`.

## Architectural Constraints — Hard Rules

- **shared/models/ is the single source of truth for inter-stage types.** Every stage imports from `shared.models`. No stage defines its own version of `Flag`, `Requirement`, `RubricAssessment`, `CandidateData`, or any cross-boundary type. If you need a new field, add it in shared and update `.orchestrator/interfaces.md`.
- **Stage D has ZERO LLM calls.** All flag derivation is deterministic Python. If you're tempted to add an LLM call in Stage D, you're doing it wrong.
- **Stage E agents never see pre-computed signal labels or risk bands.** They receive flags + tension map + candidate data + requirement list. No verdicts. This is constraint F02.
- **No global mutable state.** Every function takes typed inputs and returns typed outputs. No singletons, no module-level caches, no side effects.
- **All LLM outputs are JSON.** Agents return structured JSON validated against schemas. No free-text parsing.
- **research_general evidence capped at 2 per agent.** Hard limit, enforced in audit.

## Write-After-Act Rule — MANDATORY

After completing any task, modifying any interface, or discovering any error:
1. Update the relevant `stages/<stage>/.agent/tasks.md` with completion status.
2. If you changed a Pydantic model in `shared/models/`, update `.orchestrator/interfaces.md` — mark all consumers as STALE.
3. If you discovered a bug, append to `.orchestrator/errors.md`.
4. If you made an architectural decision, append to `.orchestrator/decisions.md`.
5. **No task is done until its tracking files reflect reality.**

## Staleness Protocol

Every context file has a `last_updated` header. When reading a file, check its timestamp against files it depends on. If `.orchestrator/interfaces.md` is newer than the `.agent/tasks.md` you're reading, the task list may not reflect the latest contracts. Flag it and re-read before proceeding.

## Coding Standards

- Python 3.12+, type hints everywhere, Pydantic v2 for all data models.
- Must pass `ruff check`, `ruff format --check`, and `pyright` with zero warnings.
- Tests: pytest + hypothesis for deterministic stages, structured mocks for LLM stages.
- Async where parallelism matters (Stage C candidate calls, Stage E agent calls). Use `httpx.AsyncClient` for LLM API calls.
- Every public function has a docstring. Every module has a module-level docstring.
- **SOLID/DRY/KISS** — All code must follow these principles:
  - Single Responsibility: each function/class/module does one thing
  - Open/Closed: extend via composition, not modification
  - Dependency Inversion: depend on abstractions (protocols/interfaces), not concretions
  - DRY: no duplicated logic — extract shared utilities
  - KISS: simplest correct solution — no premature abstraction
- **Fully modular and decoupled** — stages communicate only through `shared.models` contracts. No direct imports between stages.

## Do NOT

- Import Django, Flask, FastAPI, or any web framework. Not yet.
- Use `print()` for debugging. Use `logging` with structured output.
- Put stage-specific types in `shared/models/`. Only cross-boundary contracts go there.
- Hardcode API keys. Use environment variables via `os.environ`.
- Create files outside the designated directories without updating tracking files.
- Mark your own work as complete without updating the orchestrator files.
- Assume context from a previous session. Always re-read tracking files.
- Make personality-based claims in Stage D or Stage E partial mode.

## Directory Map

```
├── .claude/CLAUDE.md           ← you are here
├── .orchestrator/              ← project state (read first)
│   ├── status.md               ← current state of every task
│   ├── blockers.md             ← dependency graph
│   ├── decisions.md            ← architectural decisions log
│   ├── errors.md               ← bug log
│   └── interfaces.md           ← inter-stage contracts (canonical)
├── shared/                     ← cross-boundary types + utilities
│   └── src/shared/models/      ← Pydantic models (THE source of truth)
├── stages/
│   ├── stage_c/                ← JD extraction + CV rubric assessment
│   │   ├── .agent/             ← agent context for Stage C work
│   │   ├── src/stage_c/        ← implementation
│   │   └── tests/              ← stage-level tests
│   ├── stage_d/                ← flag derivation (deterministic)
│   │   ├── .agent/
│   │   ├── src/stage_d/
│   │   └── tests/
│   └── stage_e/                ← multi-agent evaluation + synthesis
│       ├── .agent/
│       ├── src/stage_e/
│       └── tests/
├── tests/
│   ├── fixtures/               ← synthetic test data
│   └── e2e/                    ← golden-path integration test
├── justfile                    ← command runner
└── pyproject.toml              ← uv workspace root
```

## Git Workflow

Branch naming: `feat/<stage>/<component>` (e.g., `feat/stage-c/c1-jd-extraction`).
Worktree location: `../worktrees/<branch-slug>/` (outside main tree).
Merge flow: feature → stage branch → main. Squash on feature→stage, regular merge stage→main.
