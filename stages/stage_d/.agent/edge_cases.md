# Stage D — Edge Cases

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Personality Flags

- **Score exactly at threshold.** Define convention: threshold is inclusive (≥ for "above", ≤ for "below"). Document this in thresholds config. Inconsistency here causes non-determinism.
- **No team context provided.** Complementarity, collision, friction, groupthink flags cannot be derived. This is correct behavior — reduced flag set, not an error. Do NOT generate placeholder flags.
- **All Big Five scores identical (e.g., preset).** Valid state. May produce an unusual flag pattern (e.g., all dimensions moderate → few flags). Flag count reasonableness check may warn "thin."
- **Big Five scores at extreme values (0.0 or 1.0).** Valid. May trigger multiple flags per dimension. Ensure threshold logic handles boundary values.
- **One candidate has Big Five, another doesn't.** Per-candidate mode determination: one is full, other is partial. Both appear in the same flag set. Stage E agents get per-candidate mode preamble.

## CV Flag Validation

- **C4 produces a flag name not in vocabulary.** Bridge has a bug. Strip flag, log error. Canonical CV flag names: CV_GAP, CV_PARTIAL, CV_EXCEEDS, CV_BEHAVIORAL_ROUTED, CV_LOW_CONFIDENCE_CLUSTER, CV_SYSTEMATIC_GAP.
- **Flag references requirement_id not in confirmed list.** Bridge has a bug. Strip flag, log error.
- **Flag metadata has priority that doesn't match requirement's scenario_priority for active scenario.** C4 or C2 has stale data. Strip flag, log — indicates the bridge ran with a stale scenario context.

## Merge

- **Both streams empty.** No personality (partial mode) + no CV flags (all MEETS). Valid but unusual. Flag count check warns "thin" (<3). Agents will have almost nothing to work with.
- **Extremely large flag set.** Candidate with 10+ personality flags + 15 CV flags = 25+. Flag count check warns "noisy." Consider whether threshold config is too aggressive.

## Validation

- **Conditional contradiction: same flag name, different requirement_ids.** NOT a contradiction. CV_EXCEEDS on REQ-03 and CV_GAP on REQ-07 is normal (exceeding one requirement, gapping another).
- **Cross-stream coherence note with no personality data.** Cannot fire in partial mode — no personality flags to create tension with. Check skips automatically.
- **Requirement with neither flag nor MEETS assessment.** Something was lost in the C3→C4 bridge. Log error — investigate whether C3 dropped the requirement or C4 failed to map it.
