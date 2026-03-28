# Stage C — Edge Cases

> last_updated: 2026-03-29T00:00:00Z by human (bootstrap)

## C1: JD Extraction

- **JD is a single paragraph.** Common for internal postings. Will produce 5-8 requirements. Warn: "Brief job description — consider adding requirements manually."
- **JD is in German.** Extraction works in both languages. Requirement text stays in JD's language. Type taxonomy labels remain English (internal system labels).
- **JD contains boilerplate.** Equal opportunity statements, company descriptions, benefits. Prompt must instruct: extract only candidate requirements, ignore everything else.
- **JD describes the role, not the candidate.** "This role will lead digital transformation" must be reframed as "Track record of leading digital transformation initiatives."
- **Compound requirements.** "10 years automotive AND P&L responsibility" → two entries. Without decomposition, rubric assessment is ambiguous.
- **Implicit requirements.** "Lead our digital transformation across all plants and regions" → scope (all plants), leadership_context (transformation), geographic (multi-region).

## C3: CV Rubric Assessment

- **CV is very short (1-paragraph LinkedIn summary).** Most requirements will be GAP or low-confidence PARTIAL. If GAP% exceeds 70%, add warning: "CV is brief — assessment is limited."
- **CV is very long (10+ pages).** Multiple conflicting evidence passages possible. Cite MOST RELEVANT passage to specific requirement. Note conflicts in notes field.
- **Same CV passage applies to multiple requirements.** A single sentence about leading a $2B acquisition touches scope, leadership_context, geographic, experience_breadth. Cite it for all — this is correct.
- **CV language doesn't match JD language.** "Transformation experience" in JD vs "organizational redesign" in CV. LLM must match by meaning, not keywords. Confidence: MEDIUM for semantic-only matches.
- **Experience exists but is old.** Candidate managed 800 people 8 years ago, current team is 40. Assign MEETS but note recency.
- **LLM fabricates a citation.** Claims CV says "$800M P&L" when it says "$80M budget." Stage C cannot catch this alone — Stage E's F04 catches it using raw CV text as ground truth.
- **Requirement is impossible.** "20 years EV experience" when industry is ~15 years old. Assign GAP, note: "Requirement may exceed industry timeline."
- **All three candidates get identical assessments.** Minimal differentiation. Surface: "Consider adding more specific requirements or using personality analysis."
- **Requirement drop in batched call.** LLM drops 1-2 requirements in ~5-10% of batched calls. Drop detection safeguard runs targeted follow-up.

## C4: Rubric-to-Flag Bridge

- **All assessments are MEETS.** No flags generated — all baseline. Flag count will be 0 for this candidate. Stage D flag count reasonableness check will warn "assessment data is thin."
- **Low-priority GAP.** Generates no flag by design. If all gaps are on low-priority requirements, the candidate appears stronger than they might be. Advisory only — the trade-off matrix shows it.
- **Scenario switch changes which requirements are high-priority.** A GAP that generated no flag under scenario A (low priority) may generate a CV_GAP flag under scenario B (high priority). This is correct and is the core mechanism of the scenario switch demo.
