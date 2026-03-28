# Blockers & Dependency Graph

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Active Blockers

None yet — shared models created during bootstrap.

## Dependency Graph

```
shared/models/* ──┬──→ Stage D: personality flags
                  ├──→ Stage D: CV flag validation
                  ├──→ Stage C4: rubric-to-flag bridge
                  ├──→ Stage C1: JD extraction (Requirement model)
                  └──→ Stage C3: CV rubric assessment (RubricAssessment model)

Stage C1 (JD extraction) ──→ Stage C2 (priority defaults) ──→ Stage C3 (CV assessment)
                                                                       │
Stage C3 ──→ Stage C4 (rubric-to-flag bridge)                         │
                       │                                               │
                       └──→ Stage D: merge ←── Stage D: personality flags
                                    │
                                    └──→ Stage D: validation Layer 0
                                              │
                                              └──→ Stage E: Layer 0 → Layer 1 → Layer 2 → Layer 3 → Synthesis
```

## Rules

- A stage agent must NOT begin a task if its "Blocked By" column in status.md shows incomplete dependencies.
- When a blocker clears, update BOTH this file AND status.md.
- If you discover a new dependency not listed here, add it immediately.
