# Stage E — Edge Cases

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Layer 0

- **Flag name not in vocabulary despite Stage D being deterministic.** Shouldn't happen. If it does, Stage D has a bug in flag_vocabulary.py. Strip, log, investigate D.
- **CV flag missing requirement_id.** Stage D should have caught this. Double-defense: strip here too.

## Layer 1

- **Partial mode candidate has fewer risk flags.** Do not penalize — note "Risk assessment limited to experience-based signals." The risk band for this candidate should annotate the limitation, not assume lower risk.
- **Cross-stream tension for partial mode candidate.** Cannot exist — no personality flags. Tension map skips automatically.
- **ROUTING flags in weight computation.** Weight is 0. Verify they contribute nothing to signal-strength labels.

## Layer 2 (Agents)

- **Agent overrides rubric level.** Stage C said PARTIAL, agent says "candidate meets this requirement." This is incorrect. Audit Check 5 (F04) catches it by comparing against the rubric matrix. The agent prompt explicitly instructs: "Do NOT override the rubric level."
- **Agent makes personality claim in partial mode.** Prompt preamble bans it. Audit Check 6 (F05 semantic drift) catches personality-language keywords in claims backed by CV evidence.
- **Agent receives zero flags.** Possible if allowlist has no matching flags for a candidate (e.g., team dynamics in partial mode with no team context). Agent should output: "Insufficient data for team dynamics assessment. Behavioral requirements require personality data."
- **Agent hits research_general cap.** With CV evidence available, this means the agent couldn't ground its claims in any data. Stronger warning than v4.1. Flag in output.
- **Agent timeout.** 15s passes with no/partial output. Return what you have. Synthesis handles 2-agent input. Note missing agent in output.
- **Agent returns non-JSON.** Retry once. Second failure: hard block for that agent. Synthesis continues with 2 agents.
- **Agent cites requirement_id that doesn't exist.** Hallucinated reference. Check 4 catches it. Strip claim.

## Layer 3

- **F04: Agent paraphrases CV citation slightly.** Fuzzy matching (ratio > 0.7) should still pass. If the agent changes numbers, it fails regardless of text similarity.
- **F04: CV text in different language than agent output.** Agent may translate. Substring matching will fail on translated text. Current limitation — log but don't hard-fail on language mismatch. Add language detection if time permits.
- **F05: Low keyword overlap because claim is highly abstracted.** "Chen's execution profile suggests moderate risk" has low overlap with execution-related keywords. Threshold of 20% is loose enough to avoid false positives on reasonable abstractions. Tune if too many drift warnings appear.

## Synthesis

- **All three agents agree.** No contested signals. Output is simpler. Concordance section notes agreement.
- **All three agents timed out.** Catastrophic failure. Output: "Agent evaluation failed. Pipeline returned Stage D flag set and trade-off matrix without agent interpretation." The matrix (from Stage C rubric data) is still useful on its own.
- **Trade-off matrix with all MEETS.** No differentiation. Surface: "Minimal differentiation across candidates on CV evidence. Consider personality analysis or additional requirements."
- **Scenario switch invalidates cached synthesis but not rubric data.** Correct behavior. Re-run D+E only. C3 results cached.
