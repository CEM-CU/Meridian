# CV-JD Matching: Requirement Extraction → Per-Requirement Assessment → Trade-Off Surfacing

---

## Why Not a Match Score

Every existing CV-JD tool produces a single compatibility number or a dimensional breakdown (skills: 80%, experience: 70%). This is useful for screening hundreds of applicants down to a shortlist. It is useless for our use case.

At the C-suite finalist stage, everyone already matches the JD. They wouldn't be finalists otherwise. The recruiter doesn't need to know "Candidate A is an 87% match." They need to know: "Candidate A exceeds on industry depth but has a gap in international scope. Candidate B meets both but exceeds neither. That's the trade-off — which gap matters more for this scenario?"

A single score hides this. A per-requirement assessment surfaces it.

---

## The Three-Step Process

### Step 1: Structured Requirement Extraction from JD

The JD agent reads the job description and extracts a **typed list of discrete requirements**. Not keywords. Not embeddings. Named, categorized requirements that the recruiter can review and confirm.

**Requirement types:**

| Type | What it captures | Example |
|---|---|---|
| Experience depth | Years in function/role/industry | "10+ years in automotive or adjacent manufacturing" |
| Experience breadth | Range of functional areas | "Cross-functional experience spanning operations and finance" |
| Scope | Team size, revenue, geographic responsibility | "P&L responsibility for $500M+ business unit" |
| Industry | Specific sector requirements | "Direct experience in premium automotive or luxury goods" |
| Geographic / cultural | International or regional requirements | "Experience leading teams across EMEA and APAC" |
| Technical / domain | Specific technical knowledge | "Deep understanding of EV powertrain technology" |
| Leadership context | Prior experience with specific situations | "Track record of leading post-acquisition integration" |
| Qualification | Education, certification, language | "MBA or equivalent; fluent German and English" |

**Output format per requirement:**

```json
{
  "id": "REQ-04",
  "type": "scope",
  "text": "P&L responsibility for business unit of $500M+",
  "source": "JD paragraph 3, line 2",
  "priority": null
}
```

Priority is null on extraction — the recruiter assigns priority in the confirmation step. The system does not decide which requirements matter most. The recruiter does. This is consistent with the lens philosophy: we extract and structure, the human prioritizes.

**Why LLM extraction, not keyword matching:** A JD that says "you will lead our digital transformation across all plants and regions" contains an implicit scope requirement (all plants = large-scale), a leadership context requirement (transformation), and a geographic requirement (all regions). Keyword matching sees words. The LLM extracts the underlying requirements. But the LLM extraction must produce structured typed output, not free text — so it can be reviewed, confirmed, and scored against.

**Recruiter confirmation step:** The extracted requirements are shown to the recruiter before any CV assessment runs. They can edit the text, change the type, delete irrelevant requirements, add missing ones, and rank priority. This takes 2-3 minutes and ensures the assessment runs against what actually matters, not what the LLM inferred.

---

### Step 2: Per-Requirement Rubric Assessment Against Each CV

For each requirement × candidate pair, the CV agent reads the candidate's CV and produces a rubric assessment.

**The rubric (fixed, not LLM-generated):**

| Level | Definition | When to assign |
|---|---|---|
| **Exceeds** | Candidate evidence clearly surpasses the requirement in scope, depth, or duration | CV shows more years, larger teams, broader geography, or more complex context than required |
| **Meets** | Candidate evidence satisfies the requirement as stated | CV shows experience that directly matches the requirement |
| **Partial** | Some evidence exists but with identifiable gaps | CV shows related but not directly matching experience, or insufficient depth/duration |
| **Gap** | No supporting evidence found in the CV | Nothing in the CV addresses this requirement |
| **Not assessable** | The requirement cannot be evaluated from CV data alone | Requirement is about leadership style, personality, values, or other non-CV-observable dimensions |

**Output format per assessment:**

```json
{
  "requirement_id": "REQ-04",
  "candidate": "Marcus Weber",
  "level": "meets",
  "evidence": "CV page 2: 'VP Digital Strategy, BMW Group. P&L ownership for Digital Manufacturing division ($620M annual budget, 2019-2024).'",
  "evidence_page": 2,
  "confidence": "high",
  "notes": "Budget figure ($620M) exceeds $500M threshold. However, this was a divisional budget within a larger business unit, not a standalone P&L. Borderline between 'meets' and 'exceeds' — recruiter should verify organizational structure."
}
```

**Design decisions for the rubric assessment:**

**One requirement at a time.** The CV agent does not assess the entire CV against the entire JD in one pass. It assesses one requirement at a time. This is the "pointwise rubric evaluation" approach from LLM grading research — LLMs are significantly more reliable when evaluating one dimension per call than when asked for holistic assessment. It also makes the output auditable: if the recruiter disagrees with one assessment, they can check that specific evidence passage without re-reading the entire analysis.

**Must cite or say "not found."** The agent cannot assign Meets/Exceeds/Partial without quoting a specific CV passage. If it can't find evidence, it must assign Gap or Not assessable. This is the "cite before you speak" constraint from structured interview evaluation research — it prevents the LLM from generating plausible-sounding assessments that aren't grounded in the actual document.

**Confidence tagging.** Each assessment carries a confidence level:
- **High**: direct, unambiguous evidence in the CV (e.g., explicit years, explicit team sizes)
- **Medium**: evidence requires inference (e.g., "led EMEA expansion" implies international scope but doesn't name specific countries)
- **Low**: evidence is indirect or the assessment depends on interpretation (e.g., "managed cross-functional teams" could mean 5 people or 500)

Low-confidence assessments automatically generate investigation questions for the interview stage.

**"Not assessable" is a feature, not a failure.** When the JD requires "ability to navigate complex stakeholder environments" and the CV says nothing about this, the correct answer is Not assessable — not a guess. This requirement gets routed to the personality × scenario layer (where agreeableness and extraversion scores may be relevant) or to the interview stage. The CV agent does not overreach.

---

### Step 3: Trade-Off Surfacing

When you lay the rubric assessments side by side across candidates for the same requirement, the trade-offs emerge without anyone computing a composite score.

**The trade-off matrix:**

| Requirement | Priority | Candidate A | Candidate B | Candidate C |
|---|---|---|---|---|
| 10+ years automotive | High | **Exceeds** (14 yrs) | Partial (6 yrs, adjacent) | **Meets** (11 yrs) |
| P&L $500M+ | High | **Meets** ($620M div.) | **Exceeds** ($1.2B standalone) | Gap |
| Post-acquisition integration | Medium | Gap | **Meets** (led 2 integrations) | Partial (involved, not led) |
| EMEA + APAC experience | Medium | Partial (EMEA only) | **Exceeds** (EMEA + APAC + NA) | **Meets** (EMEA + APAC) |
| Fluent German + English | High | **Meets** (native DE, fluent EN) | Partial (fluent EN, basic DE) | **Meets** (fluent both) |
| EV powertrain knowledge | Low | Gap | Gap | **Exceeds** (8 yrs EV) |

**What the recruiter sees from this matrix without anyone telling them:**

- Candidate A is the deepest on automotive and language but has never done M&A integration and lacks APAC experience.
- Candidate B has the broadest scope and international experience but may struggle with German-language stakeholder environments.
- Candidate C has the technical depth but has never held standalone P&L — the biggest gap on a high-priority requirement.

No algorithm needed. No composite score. The structure does the work. The recruiter reads the matrix and sees the trade-offs.

**But the scenario layer adds value here too.** If the scenario is M&A integration, the "Post-acquisition integration" requirement jumps to critical priority and Candidate B's position strengthens. If the scenario is digital transformation, the "EV powertrain knowledge" requirement gains weight and Candidate C becomes more competitive. The scenario doesn't just re-weight personality traits — it re-prioritizes which CV-JD gaps matter.

---

## Design Considerations

### How many requirements to extract?

For C-suite JDs, typically 8-15 discrete requirements. Fewer than 6 means the JD is too vague and the recruiter should be prompted to add requirements manually. More than 20 means the requirements are too granular (splitting "10 years experience in automotive" into separate requirements for "years" and "industry") and should be consolidated.

### How to handle implicit requirements?

Many C-suite JDs have implicit requirements that are never stated. "Lead BMW's digital transformation" implies change management experience, technology fluency, stakeholder navigation skills, and probably German language capability — none of which may be stated explicitly. The JD agent should extract these as "inferred requirements" with a tag indicating they were not stated explicitly. The recruiter confirms or removes them.

### How to handle conflicting evidence in the CV?

A CV might say "led a team of 200" in one role and "managed a team of 15" in the most recent role. Which is the relevant evidence for a scope requirement? The CV agent should cite the most relevant passage (matching the requirement context) and note any conflicting evidence. The notes field handles this: "Most recent role shows team of 15 (startup context). Previous role at Siemens shows team of 200 (enterprise context). JD requires enterprise-scale scope — Siemens evidence is more relevant but is 3 years old."

### What about requirements that overlap with personality assessment?

Some JD requirements are about behavior, not track record: "strong communicator," "resilient under pressure," "collaborative leadership style." These should be tagged as Not assessable by the CV agent and explicitly routed to the personality × scenario layer. This routing is the connection between the two systems — the JD requirement extraction identifies what needs to be assessed, and the assessment type determines which agent handles it:

- Track record requirements → CV agent (rubric assessment)
- Behavioral / style requirements → Personality agent (trait-context scoring)
- Contextual requirements → Scenario agent (scenario weight modulation)

This is also what justifies separate agents: they handle genuinely different requirement types that need different data sources and different assessment methods.

### How to handle the LLM reliability question?

The recruiter rightly should not trust an LLM's judgment on whether a CV "meets" a requirement. Three mechanisms control for this:

1. **Evidence citation is mandatory.** The recruiter can read the cited passage and form their own judgment. The rubric level is a suggestion, the evidence is the substance.

2. **One requirement at a time.** Easier to audit, easier to disagree with, easier to override. If the recruiter changes one assessment from "Meets" to "Partial," the trade-off matrix updates but nothing else breaks.

3. **Confidence tagging routes low-confidence assessments to human review.** The system doesn't pretend to be certain when it's not. Low-confidence assessments are flagged and become investigation questions rather than conclusions.

The rubric assessment is a structured first draft that saves the recruiter hours of manual comparison — not a verdict they must accept.

---

## How This Connects to the Full Architecture

```
JD Agent
  → Extracts typed requirement list
  → Recruiter confirms and prioritizes
  ↓
CV Agent (per candidate × per requirement)
  → Rubric assessment: Exceeds / Meets / Partial / Gap / Not assessable
  → Evidence citation from CV
  → Confidence tagging
  → Trade-off matrix assembled automatically
  ↓
Personality Agent
  → Receives "Not assessable" requirements routed from CV agent
  → Scores behavioral requirements via OCEAN × scenario weights
  → Adds trait-context flags and derailer estimates
  ↓
Synthesis Agent
  → Combines trade-off matrix + personality scores + scenario context
  → Identifies where CV strengths align or conflict with personality profile
  → Generates per-candidate summary: "Strong on track record for this role,
    but personality profile raises risk flags for this specific scenario"
  → Generates investigation questions from gaps and low-confidence assessments
```

Four agents, four genuinely different tasks, four different data sources and assessment methods. The multi-agent architecture is justified by the problem structure, not imposed on it.
