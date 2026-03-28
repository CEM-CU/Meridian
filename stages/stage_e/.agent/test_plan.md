# Stage E — Test Plan

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## Unit Tests (pytest, zero LLM calls)

### E1: Layer 0 Validation (test_layer0.py)
- Valid StageDOutput passes through unchanged
- Flag with unknown name → stripped, HALLUCINATED_FLAG_IN_DERIVATION logged
- Flag missing candidate_name → stripped
- CV flag missing requirement_id → stripped
- Personality flag missing big_five_source → stripped
- CV flag with requirement_id not in confirmed list → stripped
- Personality flag with big_five_source not in {O,C,E,A,N} → stripped
- Multiple violations in same flag set → all caught independently

### E2: Layer 1 (test_layer1.py)
- Scenario weight vectors apply correctly to each flag category
- ROUTING flags contribute zero to signal computation
- EXPERIENCE_GAP category weight is 1.0 (neutral) across all scenarios
- Signal-strength labels computed from weighted sums — verify arithmetic
- Risk bands incorporate EXPERIENCE_GAP (high-priority) and EVIDENCE_QUALITY
- Partial mode candidate: risk band annotation "limited to experience-based signals"
- Tension map detects cross-stream tension (positive CV + negative personality on same domain)
- Tension map skips partial mode candidates (no personality flags to create tension)
- **F02 enforcement: verify signal labels and risk bands are NOT in the data structure passed to agents**

### E3: Layer 2 Agents (test_agents.py)
- Allowlist filtering: role-fit agent receives only its allowed categories
- Allowlist filtering: team dynamics agent does NOT receive EXPERIENCE_STRENGTH or EXPERIENCE_GAP
- Allowlist filtering: risk agent receives EXPERIENCE_GAP (shared with role-fit — intentional)
- Full mode preamble includes scored_flag in available evidence types
- Partial mode preamble excludes scored_flag, bans personality claims
- Agent with zero flags → produces "insufficient data" output, not empty/error
- Timeout simulation → partial AgentVerdict with timed_out=True

### E4: Output Schemas (test_schemas.py)
- Valid agent JSON parses into AgentVerdict
- Claim with valid evidence_basis parses correctly
- Claim with unknown evidence_basis.type → validation error
- Claim missing evidence_basis → validation error
- evidence_basis.reference with valid requirement_id format → accepted
- Agent output with >2 research_general claims → parseable but flagged by Check 7

### E5: Layer 3 Audit (test_audit.py)
- Check 1: malformed JSON → triggers re-run flag
- Check 2: agent cites flag outside allowlist → claim stripped
- Check 3: flag in allowlist not cited by agent → "unaddressed signal" surfaced
- Check 4: agent cites "REQ-17" when list goes to REQ-12 → claim stripped, HALLUCINATED_REFERENCE logged
- Check 4: agent cites valid flag name → passes
- Check 5 (F04): citation matches CV text → passes. Citation has wrong number ($800M vs $80M in CV) → fails. Citation is reasonable paraphrase (ratio > 0.7) → passes
- Check 5 (F04): agent claims requirement_gap for REQ-05 but rubric says PARTIAL → misrepresentation caught
- Check 6 (F05): claim text has <20% keyword overlap with flag topic_keywords → DRIFT warning
- Check 6 (F05): claim uses personality language while citing cv_rubric evidence → DRIFT warning (category error)
- Check 7 (F07): agent has 3 research_general claims → third stripped, warning logged
- Check 8 (F14): agent downweights 6/10 flags → DOWNWEIGHT_RATIO_WARNING

### E7: Synthesis (test_synthesis.py)
- Template assembles with all 3 layers present
- Trade-off matrix: rows sorted by priority (high first)
- Trade-off matrix: partial mode behavioral rows show "Requires personality data"
- Contested signals: same flag cited by two agents with different valence → detected
- Contested signals: cross-stream (CV strength + personality risk on same domain) → detected and formatted
- Provenance header: full mode shows both data sources
- Provenance header: partial mode shows limitation disclaimer
- 2-agent input (one timed out) → synthesis handles gracefully, notes missing agent

## Mock LLM Tests (structured fixtures)

### Agent Response Parsing (test_agent_parsing.py)
- Well-formed JSON response → AgentVerdict parsed correctly
- JSON with extra fields → ignored (strict=False on parse)
- Non-JSON response → caught, retry flag set
- JSON with all required fields but some claims have invalid evidence types → parseable, flagged by audit

### Synthesis Statement (test_synthesis_llm.py)
- Mock synthesis LLM call → statement inserted into template correctly
- Synthesis statement contains new analysis not grounded in input → should be caught by human review (no automated check for this — noted limitation)

## Integration Tests (@pytest.mark.integration)

### E Pipeline (test_e_pipeline.py)
- Mock StageDOutput (full mode) → all layers execute → synthesis output produced
- Mock StageDOutput (partial mode) → reduced scope noted, no personality claims in output
- Mock StageDOutput (mixed mode: one full, one partial) → per-candidate handling correct
