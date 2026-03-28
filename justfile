# Meridian — C-Suite Decision Intelligence Tool
# Run `just --list` to see all available commands.

# Run all tests (no LLM calls)
test-all:
    uv run pytest shared/ stages/ tests/ -x -q --ignore=tests/e2e -m "not integration"

# Run shared models tests
test-shared:
    uv run pytest shared/tests/ -x -q

# Run Stage C tests (no LLM)
test-c:
    uv run pytest stages/stage_c/tests/ -x -q -m "not integration"

# Run Stage D tests (no LLM)
test-d:
    uv run pytest stages/stage_d/tests/ -x -q

# Run Stage E tests (no LLM)
test-e:
    uv run pytest stages/stage_e/tests/ -x -q -m "not integration"

# Run integration tests (hits cheap LLM — manual only)
integration:
    uv run pytest stages/ -x -q -m "integration" --timeout=60

# Run golden-path end-to-end test
e2e:
    uv run pytest tests/e2e/ -x -q --timeout=120

# Lint + format check + type check
lint:
    uv run ruff check .
    uv run ruff format --check .
    uv run pyright

# Auto-fix lint + format
fix:
    uv run ruff check --fix .
    uv run ruff format .

# Show project status
status:
    @cat .orchestrator/status.md

# Show blockers
blockers:
    @cat .orchestrator/blockers.md

# Show inter-stage contracts
interfaces:
    @cat .orchestrator/interfaces.md

# Show recent errors
errors:
    @tail -20 .orchestrator/errors.md

# Create a new feature worktree
# Usage: just new-worktree stage-c c1-jd-extraction
new-worktree stage component:
    git worktree add ../worktrees/feat-{{stage}}-{{component}} -b feat/{{stage}}/{{component}}
    cd ../worktrees/feat-{{stage}}-{{component}} && uv sync
    @echo "Worktree created at ../worktrees/feat-{{stage}}-{{component}}"
    @echo "Branch: feat/{{stage}}/{{component}}"

# Remove a feature worktree
# Usage: just rm-worktree stage-c c1-jd-extraction
rm-worktree stage component:
    git worktree remove ../worktrees/feat-{{stage}}-{{component}}
    @echo "Worktree removed: feat-{{stage}}-{{component}}"

# List active worktrees
worktrees:
    git worktree list
