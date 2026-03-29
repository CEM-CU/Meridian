"""Director of Engineering — CipherShield stabilization scenario.

Post-hypergrowth stabilization fixture. CipherShield grew from 12 to 65 engineers
in 18 months and is now drowning in tech debt, elevated incident rates, and senior
IC attrition. The role demands a leader who has done this before: reduce chaos,
rebuild engineering culture, and retain the talent that built the product.

Three candidates:
- Avi Lerner (A): Strong fit. Security domain + cross-timezone management + proven
  platform stabilization at comparable scale.
- Sarah Mitchell (B): Partial fit. Exceptional process maturity and retention track
  record; no security domain knowledge and US-only management experience.
- Raj Patel (C): Stretch. Deep security expertise as an IC, first-time manager at
  15 reports, no process maturity. Partial mode — no Big Five.
"""

from shared.models import (
    BigFiveScores,
    CandidateData,
    Confidence,
    Priority,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
    ScenarioPriority,
)

# ---------------------------------------------------------------------------
# Job Description
# ---------------------------------------------------------------------------

JD_TEXT: str = """
CipherShield — Director of Engineering

Location: Austin, TX (hybrid) + remote across US and Israel
Reports to: Chief Technology Officer
Team: ~65 engineers (platform, detection, integrations, infrastructure)
Series B · $18M ARR · 95 employees

---

About CipherShield

CipherShield builds enterprise security infrastructure for mid-market and Fortune 500
customers. Our core platform delivers real-time threat detection, SIEM ingestion, and
zero-trust network enforcement from a single SaaS control plane. We protect over 1,200
enterprise tenants across financial services, healthcare, and critical infrastructure.

We went from 12 to 65 engineers in 18 months following our Series A close. That growth
was necessary — and it came with a cost. We accumulated significant technical debt across
our detection pipeline, our multi-tenant data layer, and our CI/CD infrastructure. Our
P1 incident rate has climbed. Our senior engineers are burning out. We need to fix this
before it costs us the company.

This is a stabilization hire, not a growth hire. The person who succeeds in this role
will be deeply comfortable being the adult in the room: slowing down to speed up,
saying no to feature requests when the platform is not ready, and rebuilding trust with
a skeptical senior IC population that has seen too many promises broken.

---

About the Role

The Director of Engineering will own the full engineering organisation (currently 65
engineers across four squads: Platform Core, Threat Detection, Integrations, and
Infrastructure/SRE). You will report directly to the CTO and sit on the engineering
leadership team. You will have four engineering managers as direct reports, each leading
a squad of 12-20 engineers.

This is a player-coach role in year one. You will need to get into the details — reading
postmortems, reviewing architecture proposals, sitting in on on-call handoffs — before
you can effectively delegate. We expect you to transition to a full people-leadership
mode by month nine.

The team is split across Austin (primary office), distributed US remote, and a Tel Aviv
engineering hub (14 engineers, primarily focused on detection algorithms and threat intel
enrichment). You will manage across both time zones and cultures.

---

Key Responsibilities

Engineering Stability and Incident Reduction
- Own the platform reliability program. Current state: 99.6% uptime, target 99.95%.
  P1 incidents averaging 3.2 per month; target below 0.5 within 12 months.
- Build and institutionalise a postmortem culture: blameless retrospectives, action
  item ownership, systemic fix tracking across squads.
- Oversee on-call rotation design and engineer well-being. Reduce on-call burden from
  current 1-in-4 to 1-in-8 rotation within 6 months by improving alert quality and
  runbook coverage.
- Establish SRE practices: SLO definitions, error budgets, chaos engineering program.

Technical Debt Reduction
- Audit existing technical debt across all squads and create a sequenced paydown plan
  aligned with commercial priorities.
- Introduce an engineering council to arbitrate tech debt vs. feature velocity trade-offs
  with product and sales.
- Drive concrete outcomes: reduce debt backlog by 35% within 12 months while maintaining
  feature delivery commitments.

Engineering Process Maturity
- Standardise sprint planning, story estimation, and definition-of-done across all
  squads. Current state is inconsistent — some squads run Kanban, some ad hoc Scrum,
  one squad has no sprint cadence.
- Implement a code review culture with enforced standards: no direct-to-main pushes,
  required review coverage, automated static analysis gates in CI.
- Establish architecture review board (ARB) for cross-squad technical decisions.

Talent Retention and Hiring
- Stabilise attrition: current voluntary attrition at 22% annually (vs. 12% industry
  average for security engineering). Target below 14% within 18 months.
- Build individualised growth paths for the 9 senior engineers (Staff/Principal level)
  currently at risk per last engagement survey.
- Own technical hiring: sourcing pipelines, interview loop design, hiring bar definition
  for security-domain engineering roles.
- Manage distributed hiring across Austin and Tel Aviv job markets.

Security Domain Leadership
- Maintain credible technical authority with the detection engineering team. You do not
  need to write detection rules, but you must understand SIEM pipelines, EDR integrations,
  and zero-trust enforcement well enough to make architectural trade-off decisions.
- Partner with the Head of Security Research on roadmap prioritisation for the threat
  intelligence platform.
- Participate in customer escalations involving P0 security events. Communicate
  technical status clearly to enterprise customers and their security teams (SOC leads,
  CISOs).

Cross-Timezone and Distributed Team Management
- Own the working model between Austin and Tel Aviv. Define overlap hours, async
  communication norms, and escalation paths.
- Build direct relationships with the Tel Aviv engineering leads. Monthly in-person
  visits in year one are expected.
- Manage around Israeli holidays, local labour regulations, and the cultural communication
  differences between the US and Israeli engineering teams.

---

Required Qualifications

- 8+ years of engineering leadership, including at least 3 years managing managers.
- Demonstrated experience managing an engineering organisation of 40-80 engineers.
- Proven track record of platform stabilization: incident rate reduction, tech debt
  paydown, and on-call burden improvement in a high-growth environment.
- Prior experience in cybersecurity, enterprise security, or adjacent domains (threat
  detection, SIEM, EDR, network security, zero trust). Depth is required — enough to
  maintain technical credibility with senior security engineers.
- Hands-on experience with SRE practices: SLO/SLI definition, error budgets, on-call
  rotation design, postmortem facilitation.
- Strong command of CI/CD pipeline architecture and release engineering. Ability to
  diagnose and improve deployment reliability and release cadence.
- Experience managing distributed teams across multiple time zones, including at least
  one non-US engineering hub.
- Track record of senior IC retention in competitive talent markets. Ability to build
  individualized growth paths and navigate compensation conversations.

Preferred Qualifications

- Direct experience with SIEM platforms (Splunk, Elastic SIEM, Chronicle, or equivalent),
  EDR tooling (CrowdStrike, SentinelOne, or equivalent), or zero-trust frameworks
  (BeyondCorp, Zscaler, or equivalent).
- Experience with Israeli engineering culture and cross-cultural distributed team
  management.
- Background as a software engineer or security engineer before moving into management.

Behavioral Requirements

- Demonstrated empathy for burned-out engineering teams. Can diagnose cultural damage,
  not just process gaps, and knows how to rebuild psychological safety.
- Comfortable saying no to feature requests when the platform is not ready. Can defend
  engineering capacity decisions to product leadership and executive stakeholders.
- Ability to build trust with skeptical senior ICs who have been disappointed by
  previous leadership. Patient, credible, and consistent over a 6-12 month horizon.
""".strip()

# ---------------------------------------------------------------------------
# Requirements
# ---------------------------------------------------------------------------

REQUIREMENTS: list[Requirement] = [
    Requirement(
        requirement_id="REQ-01",
        text="8+ years engineering leadership including 3+ years managing managers",
        source_quote="8+ years of engineering leadership, including at least 3 years managing managers",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-02",
        text="Managed engineering organisation of 40-80 engineers",
        source_quote="Demonstrated experience managing an engineering organisation of 40-80 engineers",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-03",
        text="Proven platform stabilization: incident rate reduction and tech debt paydown",
        source_quote="Proven track record of platform stabilization: incident rate reduction, tech debt paydown, "
        "and on-call burden improvement in a high-growth environment",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.LOW,
        ),
    ),
    Requirement(
        requirement_id="REQ-04",
        text="Cybersecurity domain experience: threat detection, SIEM, EDR, or zero trust",
        source_quote="Prior experience in cybersecurity, enterprise security, or adjacent domains "
        "(threat detection, SIEM, EDR, network security, zero trust)",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-05",
        text="SRE practices: SLO/SLI, error budgets, on-call rotation, postmortems",
        source_quote="Hands-on experience with SRE practices: SLO/SLI definition, error budgets, "
        "on-call rotation design, postmortem facilitation",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-06",
        text="CI/CD pipeline architecture and release engineering experience",
        source_quote="Strong command of CI/CD pipeline architecture and release engineering",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-07",
        text="Distributed team management across multiple time zones including non-US engineering hub",
        source_quote="Experience managing distributed teams across multiple time zones, "
        "including at least one non-US engineering hub",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-08",
        text="Senior IC retention and individual growth path development in competitive talent market",
        source_quote="Track record of senior IC retention in competitive talent markets. "
        "Ability to build individualized growth paths",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-09",
        text="Engineering process maturity: sprint planning, code review standards, definition-of-done",
        source_quote="Standardise sprint planning, story estimation, and definition-of-done across all squads",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-10",
        text="Technical hiring: sourcing, interview loop design, and hiring bar definition",
        source_quote="Own technical hiring: sourcing pipelines, interview loop design, "
        "hiring bar definition for security-domain engineering roles",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-11",
        text="Empathy for burned-out teams and ability to diagnose cultural damage",
        source_quote="Demonstrated empathy for burned-out engineering teams. Can diagnose cultural damage, "
        "not just process gaps, and knows how to rebuild psychological safety",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.LOW,
        ),
    ),
    Requirement(
        requirement_id="REQ-12",
        text="Ability to say no to feature requests and defend engineering capacity decisions",
        source_quote="Comfortable saying no to feature requests when the platform is not ready. "
        "Can defend engineering capacity decisions to product leadership",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.LOW,
        ),
    ),
    Requirement(
        requirement_id="REQ-13",
        text="Ability to build trust with skeptical senior ICs over 6-12 month horizon",
        source_quote="Ability to build trust with skeptical senior ICs who have been disappointed "
        "by previous leadership. Patient, credible, and consistent over a 6-12 month horizon",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.LOW,
        ),
    ),
]

# ---------------------------------------------------------------------------
# Candidate A — Avi Lerner (Strong Fit)
# ---------------------------------------------------------------------------

AVI_LERNER_CV_TEXT: str = """
AVI LERNER
Engineering Leadership | Cybersecurity Platforms | US + Israel

PROFESSIONAL EXPERIENCE

Senior Engineering Manager — Fortinet (Sunnyvale, CA + Tel Aviv, Israel)
October 2020 - Present

Lead a 52-engineer organisation distributed across three US sites (Sunnyvale, Austin,
Atlanta) and Fortinet's Tel Aviv R&D hub (18 engineers). Teams own the FortiSIEM SaaS
platform, the EDR agent pipeline, and the threat intelligence enrichment service.

Following Fortinet's acquisition of ShieldLogic in Q1 2021, I inherited a fragile
platform running on legacy monolithic services with no SLO framework, a P1 incident
rate of 4.1 per month, and an on-call rotation so punishing (1-in-3) that three Staff
engineers had resigned in the preceding quarter.

Platform stabilization outcomes (Jan 2021 - Jan 2022):
- Reduced P1 incidents from 4.1/month to 0.9/month (78% reduction) through root cause
  investment, runbook coverage, and automated anomaly detection on ingest pipeline.
- Established SLO framework across all six service tiers; defined error budgets and
  automated budget burn alerting integrated with PagerDuty.
- Redesigned on-call rotation from 1-in-3 to 1-in-7 by hiring 4 SRE-focused engineers
  and improving alert signal-to-noise ratio (false positive rate dropped from 34% to 6%).
- Cleared 40% of documented tech debt backlog in 12 months by running monthly
  "reliability sprints" alongside feature delivery — no feature freeze required.
- Retained all 9 Staff and Principal engineers at attrition risk. Implemented
  individualised IC growth tracks; two Staff engineers promoted to Principal.

Engineering process maturity (ongoing):
- Introduced consistent sprint cadence (2-week cycles) across all five squads, replacing
  an inconsistent mix of Kanban and ad hoc planning.
- Enforced branch protection, required code review (minimum two approvals for platform
  changes), and integrated static analysis (Semgrep, Bandit) into the CI pipeline.
- Established architecture review board meeting bi-weekly; 23 ADRs filed and ratified
  in first year.
- Postmortem culture: blameless retrospectives within 48 hours of all P1s; systemic
  action items tracked in Jira with 30-day closure SLA. 94% closure rate over 24 months.

Cross-timezone management:
- Built structured overlap hours (2pm-5pm IST / 7am-10am ET) as the daily synchronous
  window for US-Israel alignment.
- Travel cadence: quarterly to Tel Aviv for 5-day in-person sprints with Israel team leads.
- Navigated Israeli holiday calendar, local labour law differences, and direct
  communication style differences between US and Israeli engineering cultures.

Security domain:
- 9 years embedded in cybersecurity engineering. Deep familiarity with SIEM pipeline
  architecture (FortiSIEM, Splunk), EDR agent telemetry, and zero-trust enforcement
  (FortiNAC, BeyondCorp integration projects).
- Served as technical escalation owner for 4 enterprise P0 security incidents, including
  two that required direct communication with CISO-level customer contacts.
- Collaborated with threat intelligence team on roadmap for MITRE ATT&CK mapping layer.

Hiring:
- Built interview loop framework for security engineering roles (SWE + domain knowledge
  assessment); reduced time-to-hire from 94 days to 47 days.
- Hired 18 engineers across US and Israel in 18 months, including 3 Staff-level
  security engineers in a highly competitive market.

Engineering Manager — CrowdStrike (Austin, TX)
March 2016 - September 2020

Managed a 14-engineer team building the Falcon sensor telemetry ingestion pipeline.
Grew team from 8 to 14 while scaling ingestion throughput from 1.2M events/sec to
11M events/sec. Introduced automated integration testing suite reducing regression
rate by 61%.

Software Engineer / Senior Software Engineer — Imperva (Tel Aviv, Israel)
August 2012 - February 2016

Contributed to WAF inspection engine and DDoS mitigation pipeline. Promoted to Senior
SWE in 2014. Last role: technical lead for the anomaly detection module.

EDUCATION
B.Sc. Computer Science — Technion (Israel Institute of Technology), 2012

LANGUAGES
English (fluent), Hebrew (native)
""".strip()

AVI_LERNER_BIG_FIVE = BigFiveScores(
    O=0.60,  # Medium-high — pragmatic innovator, not wedded to novelty
    C=0.85,  # Very high — disciplined, process-driven, follows through
    E=0.55,  # Medium — steady communicator, not dominant
    A=0.65,  # Medium-high — collaborative while maintaining standards
    N=0.22,  # Low — calm under sustained operational pressure
)

CANDIDATE_AVI = CandidateData(
    name="Avi Lerner",
    cv_text=AVI_LERNER_CV_TEXT,
    big_five=AVI_LERNER_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — Sarah Mitchell (Partial Fit)
# ---------------------------------------------------------------------------

SARAH_MITCHELL_CV_TEXT: str = """
SARAH MITCHELL
Director of Engineering | SaaS Platform Leadership

PROFESSIONAL EXPERIENCE

Director of Engineering — Lattice (San Francisco, CA)
January 2019 - Present

Lead Lattice's engineering organisation of 70 engineers across four product squads
(Core HR, Performance, Compensation, and Platform/Infrastructure). Four engineering
managers report to me directly. Full hiring accountability for engineering, including
interview loop design, levelling framework, and offer negotiations.

Team health and retention:
- Voluntary attrition has averaged 8% annually across my tenure (vs. 18% industry
  average for SaaS engineering per Radford 2023 survey).
- Designed Lattice's engineering career ladder in 2020 (8 levels, IC and management
  tracks); ladder adopted company-wide and credited by senior engineers as a key reason
  for staying.
- Built a Staff Engineer program formalising scope, sponsorship, and promotion criteria
  for Staff+ ICs; 6 engineers promoted through the program since 2020.
- Conducted bi-annual 1:1 deep dives with all Staff and Principal engineers to align on
  growth trajectory and identify flight risks 6+ months in advance.

Platform reliability:
- Lattice serves 5,200 enterprise customers with a 99.99% uptime SLA commitment.
  Maintained 99.992% actual uptime across 2022 and 2023.
- Introduced SRE function in 2020 (started with 3 engineers, now 7); defined SLOs for
  all 18 product services, established error budget policy.
- Reduced mean time to recovery (MTTR) from 47 minutes to 11 minutes via runbook
  automation and on-call rotation redesign (1-in-6 across platform squad).
- P1 incidents: averaged 0.8/month in 2023, down from 2.4/month in 2019.

Engineering process:
- Standardised sprint planning, story pointing, and retrospective formats across all
  squads in 2019-2020. Each squad runs 2-week cycles with shared definition-of-done.
- Implemented mandatory code review (2 approvals, required CI green), branch protection
  rules, and architecture review for any cross-squad API contract changes.
- Introduced quarterly engineering health checks: test coverage, dependency freshness,
  incident trends, and tech debt burn rate reported to engineering leadership monthly.

Technical leadership:
- Background as IC: 6 years as a software engineer (2007-2013) before moving into
  management. Promoted from IC to manager to director entirely at Lattice.
- Deep experience with distributed systems, multi-tenant data architectures, and
  PostgreSQL-at-scale (Lattice's primary data store, serving 150M+ rows).
- Led platform migration from Heroku to AWS EKS in 2021: 18-month program, zero
  downtime cutover, $2.1M annual infrastructure cost reduction.

Hiring at scale:
- Hired 38 engineers in 2022 alone during hypergrowth phase. Redesigned interview
  loop to improve signal quality; candidate NPS improved from 41 to 74.
- Managed engineering hiring budgets of $8.4M annually including compensation bands,
  recruiter allocations, and offer approval authority.

Previous Experience

Engineering Manager — Intercom (San Francisco, CA) · 2015 - 2019
Managed Messaging Platform team (12 engineers). Grew team from 6 to 12 through two
funding rounds. Introduced on-call rotation, runbook discipline, and weekly incident
review ceremonies.

Senior Software Engineer — Stripe (San Francisco, CA) · 2013 - 2015
Contributed to payments reconciliation infrastructure. Part of on-call rotation for
critical payment processing services.

Software Engineer — LinkedIn (Mountain View, CA) · 2007 - 2013
Member of technical staff on the Feed relevance team; grew to Senior SWE.

EDUCATION
B.S. Computer Science — University of Washington, 2007

LANGUAGES
English (native)
""".strip()

SARAH_MITCHELL_BIG_FIVE = BigFiveScores(
    O=0.50,  # Medium — pragmatic, applies proven methods
    C=0.88,  # Very high — meticulous process discipline
    E=0.62,  # Medium-high — effective communicator, not dominant
    A=0.72,  # High — collaborative, builds trust through consistency
    N=0.18,  # Very low — exceptionally steady under pressure
)

CANDIDATE_SARAH = CandidateData(
    name="Sarah Mitchell",
    cv_text=SARAH_MITCHELL_CV_TEXT,
    big_five=SARAH_MITCHELL_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Raj Patel (Stretch / Partial Mode)
# ---------------------------------------------------------------------------

RAJ_PATEL_CV_TEXT: str = """
RAJ PATEL
Engineering Manager | Security Platform Engineering

PROFESSIONAL EXPERIENCE

Engineering Manager — Dune Security (Austin, TX)
April 2024 - Present

First management role. Lead a team of 15 engineers building Dune's threat detection
and behavioural analytics platform. Transitioned from Tech Lead to Engineering Manager
when the company reached Series A and headcount grew from 6 to 15. The transition was
largely informal — I was already coordinating the work; the title change followed.

Team and context:
- Managing 15 engineers: 3 senior, 8 mid-level, 4 junior. Flat team reporting directly
  to me. No sub-team structure; I have no reports who are managers.
- No formal sprint cadence existed when I took over. Introduced lightweight Kanban with
  weekly scope reviews and async standup via Geekbot. Process is still evolving — we
  ship fast but cross-squad coordination is largely manual and depends on me.
- Attrition: 1 engineer departure in 14 months (performance-related). Team is small
  enough that individual 1:1 relationships carry most of the retention work; no formal
  career ladder or levelling framework exists yet.
- Onboarding: created the company's first engineering onboarding checklist and
  architectural overview document. First-week ramp time dropped from ~3 weeks to 8 days.

Technical work (hands-on, ~40% of time):
- Designed and own the architecture for Dune's streaming threat detection pipeline:
  Kafka ingest → Flink stateful processing → Elasticsearch index → alert enrichment
  via MITRE ATT&CK lookup service. Processes 280M events/day with sub-200ms end-to-end
  detection latency from ingest to alert.
- Authored the zero-trust network segmentation design for Dune's multi-tenant SaaS
  deployment on AWS: per-tenant VPC isolation, service mesh via Linkerd, mTLS for all
  internal east-west traffic.
- Led integration of three external threat intel feeds (VirusTotal Enterprise, Recorded
  Future, Shodan Monitor) into the enrichment pipeline; reduced false positive alert
  rate by 29% within 60 days of integration.
- Credited on CVE-2023-41912 and CVE-2024-08234 (both related to parsing vulnerabilities
  in third-party SIEM connectors we audited as part of our integration work). Worked
  with CISA and the affected vendors on responsible disclosure and patch coordination.
- Technical owner of Dune's SOC 2 Type II readiness program; coordinated engineering
  controls evidence across 14 control domains.

Previous: Tech Lead, Threat Detection — Dune Security (Austin, TX)
October 2021 - March 2024

Individual contributor and informal technical lead for the detection team (then 6
engineers). Designed the original threat detection pipeline from scratch and scaled it
from zero to 280M events/day over 30 months. Interviewed and onboarded 6 of the 9
engineers who joined during this period.

Senior Software Engineer — Palo Alto Networks (Santa Clara, CA)
June 2019 - September 2021

Member of the Cortex XDR behavioural detection team. Contributed to the machine
learning-based anomaly detection module used for ransomware pre-execution detection.
Collaborated with threat research team on detections for supply chain attack techniques
(SUNBURST campaign post-analysis). Stack: Python, Go, Kafka, Spark. Published two
internal threat research notes on lateral movement detection patterns.

Software Engineer — Cisco (San Jose, CA)
August 2017 - May 2019

Security product engineering on the Cisco Umbrella DNS-layer security platform.
Implemented new threat category classification features in the policy engine.
Contributed to integration of Cisco Talos threat intelligence into the Umbrella
categorisation pipeline. Participated in the on-call rotation for the DNS resolution
service (250M+ daily queries).

EDUCATION
B.S. Computer Engineering — UT Austin, 2017 (Dean's List)

CERTIFICATIONS
GIAC Security Expert (GSE) · OSCP · AWS Certified Security - Specialty

LANGUAGES
English (native), Hindi (conversational)
""".strip()

CANDIDATE_RAJ = CandidateData(
    name="Raj Patel",
    cv_text=RAJ_PATEL_CV_TEXT,
    big_five=None,
    personality_source=None,
)

# ---------------------------------------------------------------------------
# All Candidates
# ---------------------------------------------------------------------------

ALL_CANDIDATES: list[CandidateData] = [CANDIDATE_AVI, CANDIDATE_SARAH, CANDIDATE_RAJ]

# ---------------------------------------------------------------------------
# Rubric Assessments — Avi Lerner
# ---------------------------------------------------------------------------

RUBRIC_AVI: list[RubricAssessment] = [
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="11 years engineering leadership: EM at CrowdStrike (4 yrs), Senior EM at Fortinet "
        "(4+ yrs managing managers of 52 engineers)",
        cv_location="Fortinet role, CrowdStrike role",
        notes="Currently managing 4 EMs who each manage 12-15 engineers. Clearly managing managers.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Lead a 52-engineer organisation distributed across three US sites and Fortinet's Tel Aviv "
        "R&D hub (18 engineers)",
        cv_location="Fortinet role, summary paragraph",
        notes="52 engineers sits in the middle of the 40-80 range. Exact match.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Reduced P1 incidents from 4.1/month to 0.9/month (78% reduction). Cleared 40% of "
        "documented tech debt backlog in 12 months.",
        cv_location="Fortinet role, platform stabilization outcomes",
        notes="Precise quantification of both incident reduction and tech debt clearance. Timeline and "
        "method described. Near-identical context to CipherShield's stated problem.",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="9 years embedded in cybersecurity engineering. Deep familiarity with SIEM pipeline "
        "architecture (FortiSIEM, Splunk), EDR agent telemetry, and zero-trust enforcement.",
        cv_location="Fortinet role, security domain section",
        notes="Names specific products matching JD keywords. 9 years domain depth. P0 escalation experience "
        "with CISO-level customers.",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Established SLO framework across all six service tiers; defined error budgets and automated "
        "budget burn alerting. Postmortem culture: blameless retrospectives within 48 hours of all P1s.",
        cv_location="Fortinet role, platform stabilization outcomes",
        notes="Covers SLO, error budgets, on-call redesign (1-in-3 to 1-in-7), and postmortem cadence with "
        "closure rate data.",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="Enforced branch protection, required code review, and integrated static analysis (Semgrep, "
        "Bandit) into the CI pipeline.",
        cv_location="Fortinet role, engineering process maturity section",
        notes="CI integration mentioned with specific tooling. Release engineering depth not explicitly "
        "described — warrants investigation on deployment pipeline ownership.",
        investigation_question="Can you walk us through your ownership of CI/CD pipeline architecture at "
        "Fortinet? Specifically: deployment strategy, rollback mechanisms, and release cadence improvements?",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Lead a 52-engineer organisation distributed across three US sites and Fortinet's Tel Aviv "
        "R&D hub (18 engineers). Built structured overlap hours (2pm-5pm IST / 7am-10am ET).",
        cv_location="Fortinet role, cross-timezone management section",
        notes="Israel hub specifically mentioned. Overlap hours design, travel cadence, cultural navigation "
        "all addressed. Direct analogue to CipherShield's 14-person Tel Aviv hub.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Retained all 9 Staff and Principal engineers at attrition risk. Implemented individualised "
        "IC growth tracks; two Staff engineers promoted to Principal.",
        cv_location="Fortinet role, platform stabilization outcomes",
        notes="Specific retention of at-risk senior ICs during post-acquisition chaos. Exact parallel to "
        "CipherShield's 9 at-risk senior engineers.",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Introduced consistent sprint cadence across all five squads. Enforced branch protection, "
        "required code review. Established architecture review board meeting bi-weekly; 23 ADRs filed.",
        cv_location="Fortinet role, engineering process maturity section",
        notes="Covers sprint standardisation, code review, and ARB. Specific metrics (23 ADRs, 94% postmortem "
        "closure rate) demonstrate institutionalisation, not just initiation.",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Built interview loop framework for security engineering roles; reduced time-to-hire from "
        "94 days to 47 days. Hired 18 engineers across US and Israel in 18 months.",
        cv_location="Fortinet role, hiring section",
        notes="Specific time-to-hire improvement and cross-border hiring. Scope (18 hires) is smaller than "
        "Sarah Mitchell but domain-specific (security roles).",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. CV describes outcomes (retention, on-call burden reduction) consistent "
        "with empathetic management but direct evidence of cultural diagnosis approach not available from CV.",
        investigation_question="Describe a time you diagnosed cultural damage versus a process problem in an "
        "engineering team. How did you differentiate, and what did you do differently as a result?",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. No direct CV evidence of saying no to feature requests. "
        "Engineering council establishment implies some capacity arbitration.",
        investigation_question="Give an example of a time you refused a feature request from product or sales "
        "to protect engineering capacity. How did you make the case and what was the outcome?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Avi Lerner",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Post-acquisition Senior IC retention outcome is positive signal but "
        "does not directly evidence trust-building with skeptical ICs.",
        investigation_question="After joining Fortinet post-acquisition, how did you build credibility with "
        "senior engineers who had been through a failed integration attempt previously?",
    ),
]

# ---------------------------------------------------------------------------
# Rubric Assessments — Sarah Mitchell
# ---------------------------------------------------------------------------

RUBRIC_SARAH: list[RubricAssessment] = [
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Promoted from IC to manager to director entirely at Lattice. Four engineering managers "
        "report to me directly.",
        cv_location="Lattice role, overview",
        notes="13 years engineering career, Director role since 2019 (6 years managing managers).",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Lead Lattice's engineering organisation of 70 engineers across four product squads.",
        cv_location="Lattice role, summary",
        notes="70 engineers is at the upper end of the 40-80 range. Exceeds given scope and duration.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="P1 incidents: averaged 0.8/month in 2023, down from 2.4/month in 2019. MTTR from "
        "47 minutes to 11 minutes.",
        cv_location="Lattice role, platform reliability section",
        notes="Strong incident reduction track record. Tech debt paydown not explicitly quantified — "
        "quarterly engineering health checks mention debt burn rate tracking.",
        investigation_question="Can you give us a concrete example of a tech debt paydown initiative you "
        "led at Lattice? What was the debt, what was the approach, and what did you measure?",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No cybersecurity domain experience. Background is HR tech (Lattice), messaging (Intercom), "
        "payments (Stripe), and social (LinkedIn). No SIEM, EDR, zero-trust, or threat detection exposure.",
        investigation_question="CipherShield's engineering team builds SIEM and EDR products. How would you "
        "develop sufficient security domain fluency to maintain technical credibility with the detection team?",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Introduced SRE function in 2020; defined SLOs for all 18 product services, established "
        "error budget policy. Maintained 99.992% actual uptime across 2022 and 2023.",
        cv_location="Lattice role, platform reliability section",
        notes="SRE function built from scratch. SLO coverage across 18 services. Uptime track record strong. "
        "On-call rotation redesign documented.",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="Led platform migration from Heroku to AWS EKS in 2021: 18-month program, zero downtime "
        "cutover, $2.1M annual infrastructure cost reduction.",
        cv_location="Lattice role, technical leadership section",
        notes="EKS migration implies CI/CD pipeline ownership. Specific tool stack and pipeline architecture "
        "not detailed in CV.",
        investigation_question="What was your direct involvement in CI/CD pipeline design during the EKS "
        "migration? What deployment strategy did you adopt and why?",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="All roles at US companies with US-only engineering teams. LinkedIn, Stripe, Intercom, Lattice — "
        "no international engineering hub management. No evidence of cross-timezone or cross-cultural EM.",
        investigation_question="Have you managed engineering teams in non-US locations or across significant "
        "time zone gaps? How would you approach the US-Israel management challenge at CipherShield?",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Voluntary attrition has averaged 8% annually (vs. 18% industry average). Designed "
        "Lattice's engineering career ladder; built Staff Engineer program; 6 promoted through program.",
        cv_location="Lattice role, team health and retention section",
        notes="8% vs 18% industry benchmark is one of the strongest retention signals in this candidate pool. "
        "Structural interventions (career ladder, Staff program) show systemic approach, not ad hoc.",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Standardised sprint planning, story pointing, and retrospective formats across all squads "
        "in 2019-2020. Each squad runs 2-week cycles with shared definition-of-done.",
        cv_location="Lattice role, engineering process section",
        notes="Covers sprint standardisation, code review enforcement, branch protection, ARB for API changes. "
        "Quarterly health checks with tech debt burn rate reporting demonstrates mature process governance.",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Hired 38 engineers in 2022 alone. Redesigned interview loop; candidate NPS improved from "
        "41 to 74. Managed engineering hiring budgets of $8.4M annually.",
        cv_location="Lattice role, hiring section",
        notes="Highest hiring volume in candidate pool. Interview loop redesign with NPS measurement shows "
        "systematic approach. Budget authority scale exceeds role requirements.",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Lattice context was hypergrowth, not burnout recovery — different "
        "cultural challenge. Career ladder and retention metrics are consistent with empathetic management "
        "but do not evidence response to burned-out team specifically.",
        investigation_question="Have you ever joined or inherited a team that was burned out or had low "
        "psychological safety? What did you diagnose as the root cause and what did you do first?",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Quarterly engineering health checks reporting to leadership implies "
        "some capacity visibility but no direct evidence of saying no to feature requests.",
        investigation_question="Describe a situation where you pushed back on product leadership to protect "
        "engineering capacity for reliability or debt work. How did you make the case?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Sarah Mitchell",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Lattice career ladder and Staff program imply credibility with senior "
        "ICs in a stable organisation; skeptical ICs in a burned-out startup is a different context.",
        investigation_question="Tell us about a time a senior IC on your team had lost faith in engineering "
        "leadership. How did you re-establish trust and over what time horizon?",
    ),
]

# ---------------------------------------------------------------------------
# Rubric Assessments — Raj Patel
# ---------------------------------------------------------------------------

RUBRIC_RAJ: list[RubricAssessment] = [
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="First management role. Lead a team of 15 engineers. Transitioned from Tech Lead to EM "
        "when the company reached Series A (14 months ago).",
        cv_location="Dune Security EM role, overview",
        notes="18 months total management experience. No sub-team structure, no reports who are managers. "
        "Does not meet the 3-year managing managers requirement. Engineering career is 7 years total.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="Managing 15 engineers: 3 senior, 8 mid-level, 4 junior.",
        cv_location="Dune Security EM role",
        notes="15 engineers is well below the 40-engineer floor of the requirement. No prior experience at "
        "the required scale.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of platform stabilization, incident reduction program, or tech debt paydown "
        "initiative. Dune is a startup in chaos mode per CV description ('process is still evolving — "
        "we ship fast but coordination is manual').",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Designed and own the architecture for Dune's streaming threat detection pipeline: Kafka "
        "ingest → Flink processing → Elasticsearch index. CVE-2023-41912 and CVE-2024-08234 credited.",
        cv_location="Dune Security EM role, technical work section",
        notes="Strongest security domain depth in the candidate pool. Built threat detection pipeline from "
        "scratch. CVE credits. Prior roles at CrowdStrike, Palo Alto Networks, Cisco. GSE + OSCP certified.",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of SLO frameworks, error budgets, on-call rotation design, or blameless postmortem "
        "culture. Startup context with informal process ('Kanban with weekly scope reviews').",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="As an IC and Tech Lead at Dune, Raj likely touched CI/CD infrastructure but no evidence of "
        "pipeline ownership or release engineering at organisational level.",
        investigation_question="Describe your involvement in CI/CD and release engineering at Dune. Do you "
        "own the pipeline architecture or is that owned by someone else?",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="All experience is at US companies with US-only teams. No international management. No "
        "distributed team experience beyond a single Austin office.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.LOW,
        cv_citation="Attrition: 1 engineer departure in 14 months (performance-related). Team is small enough "
        "that 1:1 relationships are strong; no formal career ladder in place.",
        cv_location="Dune Security EM role, team and context",
        notes="Low attrition at small scale with strong 1:1 relationships is positive but not transferable "
        "evidence for senior IC retention at 50-65 engineer scale. No career ladder.",
        investigation_question="You currently manage 15 engineers with strong 1:1 relationships. How would "
        "you approach retention of 9 at-risk Staff/Principal engineers you haven't built relationships "
        "with yet?",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="No formal sprint cadence when I took over. Introduced lightweight Kanban with weekly "
        "scope reviews. Process is still evolving.",
        cv_location="Dune Security EM role, team and context",
        notes="Self-reported process immaturity. No code review standards, no definition-of-done, no "
        "architecture review described. Startup chaos mode explicitly acknowledged.",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="No hiring at scale evidence. Dune is 15-person team; any hiring would be small volume. "
        "No interview loop design or sourcing strategy mentioned.",
        investigation_question="Describe your experience with technical hiring. How many engineers have you "
        "hired, what was your interview loop design, and have you hired in competitive security talent markets?",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Insufficient management tenure to assess. 18 months as EM at a "
        "small startup does not provide a reliable signal on this dimension.",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Not assessable from CV.",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Raj Patel",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Not assessable from CV.",
    ),
]

ALL_RUBRIC_ASSESSMENTS: list[RubricAssessment] = RUBRIC_AVI + RUBRIC_SARAH + RUBRIC_RAJ

# ---------------------------------------------------------------------------
# Scenario Configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG = ScenarioConfig(
    name=ScenarioName.STABILIZATION,
    category_weights={
        "EXECUTION": 1.4,
        "EXPERIENCE_STRENGTH": 1.3,
        "EXPERIENCE_GAP": 1.3,
        "DERAILMENT": 1.2,
        "CULTURAL": 1.1,
        "STRATEGIC": 0.8,
        "INTEGRATION": 0.9,
        "COMPLEMENT": 0.7,
        "COLLISION": 0.7,
        "FRICTION": 0.9,
        "DARK_SIDE": 1.2,
        "GROUPTHINK": 0.6,
        "EVIDENCE_QUALITY": 1.0,
        "ROUTING": 1.0,
        "TENURE": 1.0,
    },
)

# ---------------------------------------------------------------------------
# Ground Truth
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, object] = {
    # Overall fit ranking for the stabilization scenario
    "fit_ranking": ["Avi Lerner", "Sarah Mitchell", "Raj Patel"],
    # Assessment modes
    "assessment_modes": {
        "Avi Lerner": "full",
        "Sarah Mitchell": "full",
        "Raj Patel": "partial",
    },
    # Critical gaps per candidate (REQ IDs)
    "critical_gaps": {
        "Avi Lerner": [],
        "Sarah Mitchell": ["REQ-04", "REQ-07"],
        "Raj Patel": ["REQ-01", "REQ-02", "REQ-03", "REQ-05", "REQ-07", "REQ-09"],
    },
    # Expected EXCEEDS ratings per candidate
    "exceeds_requirements": {
        "Avi Lerner": ["REQ-01", "REQ-03", "REQ-04", "REQ-05", "REQ-07", "REQ-08", "REQ-09"],
        "Sarah Mitchell": ["REQ-01", "REQ-02", "REQ-05", "REQ-08", "REQ-09", "REQ-10"],
        "Raj Patel": ["REQ-04"],
    },
    # Behavioral requirements (not assessable from CV) — always NOT_ASSESSABLE
    "not_assessable_requirements": ["REQ-11", "REQ-12", "REQ-13"],
    # Key differentiators between Avi and Sarah
    "avi_vs_sarah_differentiators": [
        "security_domain_depth",
        "cross_timezone_israel_management",
        "platform_stabilization_at_analogous_scale",
    ],
    # Key risks per candidate
    "candidate_risks": {
        "Avi Lerner": [
            "CI/CD depth not fully evidenced — may need validation",
            "Fortinet is a large company; CipherShield startup pace may differ",
        ],
        "Sarah Mitchell": [
            "Zero cybersecurity domain knowledge — high ramp cost",
            "No international management experience — Israel hub is a real gap",
            "Lattice SaaS context (HR tech) is far from security domain",
        ],
        "Raj Patel": [
            "First-time manager at 18 months — insufficient management depth",
            "No experience managing more than 15 reports",
            "No process maturity experience — has not built the discipline CipherShield needs",
            "Stretch hire risk: would need 18-24 months to be effective at this scale",
        ],
    },
    # Scenario-specific notes
    "scenario_notes": (
        "STABILIZATION scenario heavily weights EXECUTION and EXPERIENCE flags. "
        "Avi Lerner's direct stabilization track record (78% P1 reduction, 40% tech debt "
        "clearance, Israel hub management) maps precisely to CipherShield's stated problems. "
        "Sarah Mitchell is a compelling alternative if security domain ramp is acceptable — "
        "her retention and process depth are superior, but the security gap and absence of "
        "international management are material risks for this specific role. "
        "Raj Patel is a stretch hire and should be evaluated only if the company is willing "
        "to invest 18+ months in management development alongside domain depth."
    ),
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "ALL_CANDIDATES",
    "ALL_RUBRIC_ASSESSMENTS",
    "AVI_LERNER_BIG_FIVE",
    "AVI_LERNER_CV_TEXT",
    "CANDIDATE_AVI",
    "CANDIDATE_RAJ",
    "CANDIDATE_SARAH",
    "GROUND_TRUTH",
    "JD_TEXT",
    "RAJ_PATEL_CV_TEXT",
    "REQUIREMENTS",
    "RUBRIC_AVI",
    "RUBRIC_RAJ",
    "RUBRIC_SARAH",
    "SARAH_MITCHELL_BIG_FIVE",
    "SARAH_MITCHELL_CV_TEXT",
    "SCENARIO_CONFIG",
]
