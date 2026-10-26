# C-Suite Hiring Lens — Overview for Mentor Review

---

## The Problem

External executive hires fail 40–50% of the time (Kaplan & Sorensen 2021). Internal executive hires fail at approximately 25–30% (Bidwell 2011). Cost per failed C-suite hire: $5–25M.

The current process is:
- **Experience-driven and intuition-heavy.** Evaluations bias toward safe ratings and gut-feel pattern matching.
- **Oriented toward past performance rather than context fit.** Committees focus on "what has this person done?" far more than "what does this specific situation demand, and how does this person match it under different scenarios?"

HR professionals have the methods and the domain expertise to synthesize candidate data. What they lack is a structured way to evaluate trade-offs explicitly across multiple dimensions and scenarios at speed.

---

## What Changed and Why

### Why we dropped collaboration simulation

- These metrics are more suitable for team leads and managers, not C-suite where strategic fit and scenario alignment are the primary hiring drivers.
- It relies on interaction-level data that is difficult to collect — no company has this readily available.
- Agent-based simulation carries high cost for what is ultimately a complementary feature.

### What we switched to

We adopted the multi-agent workflow from the briefing: agents that process CVs, job descriptions, and scenario requirements — each reading a different source, each contributing a different evaluation dimension.

For assessing **track record fit**, we use structured requirement extraction from the JD followed by per-requirement assessment against each candidate's CV — surfacing the trade-offs between finalists rather than producing a single match score.

For assessing **leadership fit**, we use the Big Five personality model scored against the strategic scenario. The critical finding from our research: the relationship between traits and performance is context-dependent. The same trait can be an asset in one scenario and a liability in another (Herrmann & Nadkarni 2014, Strategic Management Journal).

For assessing **risk**, we use published correlations between Big Five traits and dark-side derailers (Furnham & Crump 2005–2020, N > 5,000 per study), disclosed as estimates with stated confidence.

All of this is backed by documented criteria that the agents follow — grounded in published research, auditable by the recruiter, and transparent in how every conclusion was reached.

---

## The Workflow

**1. Input.** The recruiter uploads candidate CVs, the job description, and Big Five personality assessment results.

**2. Requirement extraction.** The JD agent reads the job description and extracts a structured list of discrete requirements — not keywords, but typed requirements like "10+ years in automotive," "P&L responsibility $500M+," "post-acquisition integration experience." The recruiter reviews, edits, and prioritizes these before any assessment runs.

**3. Context setting.** The recruiter selects a strategic scenario and ranks priorities. This determines which requirements gain weight and which personality-context interactions are active.

**4. Assessment.** Each source is read by the appropriate agent within its domain constraints:
- The CV agent assesses each candidate against each requirement using a fixed rubric (Exceeds / Meets / Partial / Gap / Not assessable), citing the specific CV passage as evidence.
- The personality agent scores trait-context fit and flags risk patterns, citing the research basis for each.
- Requirements that the CV cannot answer (e.g., "resilient under pressure") are routed to the personality agent.

**5. Output.** Per-candidate profiles combining track record assessment, personality fit, and risk — all mapped to the selected scenario. A trade-off matrix shows where each candidate is strong and where the gaps are. Scenario switch available.

---

## How We Assess: Three Layers

### Layer 1 — Track Record vs. Requirements

At the C-suite finalist stage, every candidate already broadly matches the JD. A match score is meaningless — everyone is 85%+. What matters are the specific trade-offs between finalists that a single score hides.

The JD agent extracts requirements as a structured list. The CV agent assesses each candidate against each requirement independently, using a fixed rubric:

- **Exceeds** — candidate evidence clearly surpasses the requirement
- **Meets** — candidate evidence satisfies the requirement as stated
- **Partial** — some evidence, but with identifiable gaps
- **Gap** — no supporting evidence found
- **Not assessable** — cannot be evaluated from CV alone

Every assessment must cite the specific CV passage that supports it. If the agent can't find evidence, it must say so — not guess.

**Example trade-off matrix:**

| Requirement | Priority | Candidate A | Candidate B |
|---|---|---|---|
| 10+ years automotive | High | Exceeds (14 yrs) | Partial (6 yrs, adjacent) |
| P&L $500M+ | High | Meets ($620M div.) | Exceeds ($1.2B standalone) |
| Post-acquisition integration | Medium | Gap | Meets (led 2 integrations) |
| EMEA + APAC experience | Medium | Partial (EMEA only) | Exceeds (3 regions) |

The recruiter reads this and immediately sees: Candidate A has the deeper industry knowledge, Candidate B has the broader scope and M&A experience. That's the trade-off — and it's invisible in a single match score.

When the scenario changes, the **priority column shifts** — and that reshuffles which gaps matter most.

### Layer 2 — Personality × Scenario

Big Five personality traits correlate with leadership effectiveness, but the correlation is context-dependent. Our system scores candidates against the specific scenario, not in the abstract.

The most illustrative example: conscientiousness is generally the strongest personality predictor of job performance. But in transformation contexts, very high conscientiousness actually impedes execution of novel strategies — leaders over-plan, resist ambiguity, and struggle when the plan needs to change mid-execution (Herrmann & Nadkarni 2014, Strategic Management Journal). The same trait that makes a candidate ideal for stabilization becomes a risk factor for transformation.

This pattern holds across traits. Low openness predicts rigidity in dynamic environments (Nadkarni & Herrmann 2010). High agreeableness becomes a liability in turnarounds that require unpopular decisions (Kaplan & Sorensen 2012). The system captures these interactions by weighting traits differently per scenario — and showing the recruiter exactly what shifted and why when the context changes.

### Layer 3 — Risk Estimation

Beyond scenario fit, the system estimates dark-side tendencies using published correlations between Big Five traits and the Hogan Development Survey (Furnham & Crump series, N > 5,000 managers per study).

For example, the combination of high neuroticism with low agreeableness is the strongest predictor of skeptical, mistrustful leadership under stress — leaders who see hidden agendas and damage trust in their teams. High neuroticism in a turnaround context (maximum sustained stress) amplifies this risk further (Peterson et al. 2003).

These are explicitly disclosed as estimates, not diagnoses — Big Five scores explain approximately 20% of dark-side variance. Enough to flag risk for investigation, not enough to confirm it. The system recommends confirmatory assessment when risk is elevated.

---

## What We Output

**Per candidate, per scenario:**

- **Requirement assessment matrix** — how each candidate maps to each JD requirement, with evidence citations and identified gaps. Trade-offs between candidates are visible at a glance.

- **Personality-context fit** — how the candidate's trait profile aligns with what the scenario demands, with specific notes where traits interact with context in non-obvious ways.

- **Risk notes** — derailer risk estimates with confidence disclosure and research citations. Not generic warnings — specific to this candidate's profile in this scenario.

- **Investigation questions** — generated from gaps, low-confidence assessments, and risk notes. Specific probes for final interviews, tied to the actual findings. Example: "Candidate's conscientiousness is very high. In transformation contexts, research shows this can impede novel strategy execution. Probe: how does this candidate handle situations where the plan must change mid-execution?"

- **Scenario comparison** — same candidates re-assessed under a different strategic assumption. The recruiter sees which requirement priorities shift, which personality traits flip from asset to liability, and which candidate moves up or down — with the reasoning for every change.

---

## Conclusion

The only data requirement from the company is that candidates complete a Big Five personality survey — a standard 10–20 minute instrument. Combined with the CV and JD that already exist in every executive search, this gives the system everything it needs.

No internal company data collection. No interaction logs. No team member assessments (unless optionally provided).

Every assessment — whether track record, personality, or risk — traces to either a specific CV passage or a specific research citation. The recruiter can audit any claim by following the chain from output to evidence. The agents follow documented criteria, disclose confidence levels, and distinguish what the data shows from what it suggests.

The result is a structured, transparent, scenario-conditional evaluation lens that augments the recruiter's expertise with validated research they would not have time to apply manually.

---

## Key References

- Judge, T. A. et al. (2002). Personality and leadership. *J. Applied Psychology*, 87(4), 765–780.
- Nadkarni, S. & Herrmann, P. (2010). CEO personality, strategic flexibility, and firm performance. *Academy of Management Journal*, 53(5), 1050–1073.
- Herrmann, P. & Nadkarni, S. (2014). Managing strategic change: The duality of CEO personality. *Strategic Management Journal*, 35(9), 1318–1342.
- Peterson, R. S. et al. (2003). CEO personality on TMT dynamics. *J. Applied Psychology*, 88(5), 795–808.
- Kaplan, S. N. & Sorensen, M. (2021). Are CEOs different? *J. Finance*, 76(4), 1773–1811.
- Kaplan, S. N., Klebanov, M. M. & Sorensen, M. (2012). Which CEO characteristics matter? *J. Finance*, 67(3), 973–1007.
- Bidwell, M. (2011). Paying more to get less. *American Sociological Review*, 76(3), 365–394.
- Furnham, A. & Crump, J. (2005–2020). Big Five × HDS facet analyses series. Multiple journals. N > 5,000/study.
- Chen, G. & Hambrick, D. C. (2012). CEO replacement in turnaround situations. *Organization Science*, 23(1), 270–284.
