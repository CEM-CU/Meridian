"""VP of Engineering fixture — Cloudbridge, Series C, GROWTH scenario.

Cloudbridge is a B2B SaaS company ($85M ARR, 280 employees) in the enterprise
cloud-infrastructure space. The company is in an aggressive growth phase:
scaling engineering from 40 to 150 engineers in 18 months, opening a new
engineering hub in Berlin, and migrating a production monolith to a
microservices architecture.

Three candidates with distinct strength/gap profiles:
- Priya Sharma:  strong fit — 14-year VP with multi-continent scaling track record
- James O'Brien: partial fit — deep enterprise architecture, no startup-speed experience
- Nina Kowalski: stretch — impressive velocity at smaller scale, no Big Five scores

Requirement domains covered in GROUND_TRUTH:
    engineering_leadership_tenure, team_scaling, distributed_team_management,
    microservices_architecture, hiring_at_scale, budget_ownership,
    cross_functional_collaboration, devops_cicd, industry_experience,
    international_experience, mentoring_culture, exec_communication
"""

from shared.models import BigFiveScores, CandidateData, ScenarioConfig, ScenarioName

# ---------------------------------------------------------------------------
# Job Description
# ---------------------------------------------------------------------------

JD_TEXT: str = """
Cloudbridge — Vice President of Engineering

Location: San Francisco, CA (HQ) + Berlin, Germany (new hub opening Q3)
Reports to: Chief Technology Officer
Direct reports: 4 Engineering Directors, Head of Platform, Head of Developer Experience

About Cloudbridge

Cloudbridge is the infrastructure intelligence layer for the modern enterprise cloud.
Our platform gives DevOps and platform-engineering teams unified observability,
cost governance, and automated remediation across multi-cloud environments — AWS,
Azure, and GCP — from a single control plane. Founded in 2018 and headquartered in
San Francisco, we have grown to $85M in annual recurring revenue, serve 340 enterprise
customers (including three Fortune 100 accounts), and raised a $120M Series C led by
Accel Partners in early 2025. Our 280-person company includes a 40-person engineering
organization that we are now preparing to scale aggressively to meet demand.

The Opportunity

This is the defining engineering leadership hire of Cloudbridge's next chapter. We
are scaling our engineering organization from 40 to 150 engineers over the next
18 months while simultaneously opening a new engineering hub in Berlin and executing
a multi-year migration from our production Django monolith to a microservices
architecture on Kubernetes. We need a VP of Engineering who has done this before —
someone who has scaled a high-growth SaaS engineering org through a step-change in
headcount, built distributed teams across time zones, and navigated the technical
and organizational complexity of a major architecture transformation without stalling
product velocity.

Success in this role means: 150 engineers hired, ramped, and productive within
18 months; the Berlin hub operating as a full-capability team (not a satellite office);
our first 12 microservices in production with clear migration sequencing for the
remainder; and an engineering culture that retains top talent through the chaos of
hyper-growth. The VP of Engineering will be the most operationally impactful hire we
make this year.

Key Responsibilities

Engineering Leadership and Team Building
You will own the full engineering organization — its structure, its talent, its
culture, and its output. That means designing the org chart as we triple in size,
deciding which disciplines to hire ahead of demand, building the management layer
below you, and personally recruiting for senior and staff engineer roles. You will
establish a leveling framework, a performance review process, and a career-growth
system that functions at 150 people and does not require rebuilding at 300.

Architecture and Technical Strategy
You will partner with the CTO on the long-term technical vision while owning
day-to-day architectural governance. Our immediate priority is the microservices
migration: decomposing 6 years of accumulated Django monolith into independently
deployable services while keeping production SLAs intact for enterprise customers.
You have a strong point of view on service boundaries, data consistency patterns,
API versioning, and the organizational structures (stream-aligned teams, platform
teams) that make a distributed architecture sustainable rather than a maintenance
nightmare. You are equally comfortable in a design review and a post-incident review.

Berlin Hub Establishment
You will lead the buildout of Cloudbridge's first international engineering hub in
Berlin — from office selection through hiring, through building the social fabric
that makes a satellite office feel like a real part of the company rather than a
timezone-adjusted Slack channel. You understand what makes distributed engineering
teams work: clear charters, deliberate communication rhythms, async-first culture,
and leadership in both locations with genuine authority.

Hiring and Talent Acquisition at Scale
Tripling a 40-person engineering team in 18 months is a hiring operation, not just
a recruiting effort. You will define the hiring process end-to-end, establish
sourcing partnerships, build a structured interviewing system that scales without
sacrificing signal quality, and personally close candidates at the senior and staff
level. You have done this before and have a philosophy about what makes high-volume
hiring work without destroying culture.

Cross-Functional Partnership
Engineering at Cloudbridge does not operate as a back-office function. You will sit
in the leadership team alongside the CPO, CRO, and CFO. You will translate
customer escalations into technical prioritization decisions, push back constructively
on roadmap scope when engineering capacity constraints require trade-offs, and
represent engineering interests in board-level conversations about product strategy
and infrastructure investment. Our product and design teams expect a true partner,
not a service organization.

DevOps, Platform, and Engineering Excellence
We ship to production dozens of times per day across multiple product lines. You
will own the platform engineering roadmap — CI/CD pipelines, developer tooling,
testing infrastructure, observability stack, and incident response processes. We
have a strong foundation, but there is significant work to do as we scale: build
times have crept up, on-call rotation is burning out junior engineers, and our
staging environment strategy needs a rethink for a microservices world.

Required Qualifications

- 10 or more years of progressive engineering leadership experience, with at least
  5 years as VP of Engineering, Head of Engineering, or equivalent title carrying
  full organizational ownership of an engineering team.
- Demonstrated experience scaling an engineering organization through at least one
  step-change growth phase — taking a team from under 50 engineers to 120 or more.
  We are not interested in candidates who have managed stable large teams; we need
  someone who has built the team while shipping the product.
- Direct experience building or managing distributed engineering teams across at
  least two geographic locations, including at least one non-US location.
- Hands-on technical involvement in a microservices migration or cloud-native
  architecture transformation. You do not need to write production code today, but
  you need architectural opinions rooted in having lived through the complexity.
- Budget ownership for engineering including headcount, infrastructure, tooling, and
  vendor contracts — minimum $5M annual budget with accountability for spend-versus-plan.
- A track record of building mentoring and career-growth programs that retain senior
  engineers through rapid organizational change.
- B2B SaaS experience. Our customers are enterprise IT teams. The sales motion, the
  support obligation, and the SLA requirements of enterprise SaaS are different from
  consumer and internal tooling environments, and we need a leader who understands
  those differences at an operational level.

Desired Qualifications

- Experience with a hypergrowth hiring push — personally closing 30 or more
  engineering hires in a single 12-month period at senior IC or management level.
- Familiarity with European employment law, works council dynamics, or the practical
  realities of standing up a German GmbH engineering entity.
- Direct experience with cloud-infrastructure, observability, or DevOps tooling
  companies; understanding of the platform-engineering buyer persona.
- Bachelor's or Master's degree in Computer Science, Software Engineering, or a
  related technical field.

Who You Are

You build trust with engineers by being technically credible and operationally
reliable, not by being the smartest person in the room. You are comfortable with
ambiguity and make decisions with incomplete information. You have strong opinions
about engineering culture — about what makes a team want to stay and do their best
work — and you have the track record to back them up. When something breaks at 2am,
your instinct is to ask what in the system failed rather than who.

You communicate clearly at every level of the organization: in a 1:1 with a junior
engineer debugging their first on-call incident, in a design review with senior
architects, and in a board meeting explaining why the migration is taking longer than
the original estimate. You are comfortable being the VP of Engineering at a company
where the C-suite has strong technical opinions, and you do not lose sleep over that.
""".strip()

# ---------------------------------------------------------------------------
# Candidate A — Priya Sharma (Strong Fit)
# ---------------------------------------------------------------------------

PRIYA_SHARMA_CV_TEXT: str = """
PRIYA SHARMA
VP of Engineering | B2B SaaS | Distributed Teams | Platform Architecture

SUMMARY

Engineering leader with 14 years of progressive experience building and scaling
high-growth B2B SaaS engineering organizations. Currently VP of Engineering at
Vantage Analytics (Series D, $310M ARR), where I lead a 200-person engineering
organization spanning San Francisco, Bangalore, and London. Over the past three
years I scaled the team from 30 engineers to 180, led a full migration from a
Rails monolith to a microservices architecture on Kubernetes, and established the
company's first international engineering hub in Bangalore. I own an $18M annual
engineering budget covering headcount, infrastructure, and tooling. I am seeking
a VP of Engineering role at a company in the $50M–$150M ARR range where the
engineering scaling challenge is the primary mandate, not a secondary concern.

PROFESSIONAL EXPERIENCE

VP of Engineering — Vantage Analytics, San Francisco, CA (March 2021 – Present)
Vantage Analytics provides revenue intelligence software to B2B sales organizations;
$310M ARR, 680 employees, 200 engineering staff across three continents.

When I joined, the engineering team was 30 engineers, all in San Francisco, running
a 6-year-old Ruby on Rails monolith deployed on a single AWS region. Over the next
36 months I rebuilt the engineering organization from the ground up while keeping
the product shipping. I restructured the engineering org into 8 product teams and 2
platform teams, hired 150 net-new engineers (including 12 engineering managers and
4 directors), and established the Bangalore engineering hub, which now operates as
a full-capability team of 55 engineers with its own director and a 5-person senior
engineering staff. The London hub has 28 engineers focused on EMEA-specific compliance
and localization features.

The monolith-to-microservices migration was the most technically complex initiative
of my tenure. We decomposed 11 years of accumulated Rails code into 34 independently
deployable services over 28 months, using a strangler-fig pattern with a purpose-built
API gateway. I established the architectural review board, defined our service ownership
model (each service owned by a single stream-aligned team), and made the call to build
a shared internal developer platform rather than asking each team to manage its own
Kubernetes operational burden. That decision cost 6 months of platform team headcount
but reduced on-call pages per engineer per quarter from 22 to 4 by the time we reached
full decomposition.

On talent: I personally recruited and closed 34 senior and staff engineers over the
past three years, maintaining a 91-day median time-to-hire for senior IC roles and a
74% offer-acceptance rate against a highly competitive San Francisco talent market.
I built our structured interview system from scratch — calibrated rubrics, panel
alignment protocols, and a take-home project format that replaced the whiteboard
fizzbuzz that was driving away senior candidates. Engineering attrition at Vantage
is 8% annually against an industry benchmark of 14% for companies at our growth stage.

Budget: I own the $18M engineering budget end-to-end — annual planning, quarterly
reforecast, infrastructure cost optimization ($1.2M in cloud spend reduction in FY2024
through right-sizing and reserved-instance strategy), and vendor contract negotiation.

I attend the board and investor meetings quarterly to represent engineering. I have
presented the microservices migration roadmap to the board twice, including the
18-month delay to the original timeline and the rationale for the trade-offs made.
That conversation was not comfortable, but it was necessary and it went well.

Director of Engineering, Platform — Stripe, San Francisco, CA (January 2017 – February 2021)
Led the 45-person Platform Engineering team responsible for Stripe's internal developer
platform, build and deployment infrastructure, and developer experience tooling.
Managed a distributed team across San Francisco and Dublin (12 engineers). Owned the
migration from Buildkite-based per-repo CI to a unified build graph that reduced median
build time from 22 minutes to 7 minutes across 800 active repositories. Partnered with
the Infrastructure org to design Stripe's service mesh strategy ahead of the move to
Kubernetes-native deployments.

Engineering Manager, Infrastructure — Segment (acquired by Twilio), San Francisco, CA (2014 – 2016)
Managed a 12-person infrastructure engineering team building the data pipeline
processing platform that ingested 300 billion events per month for enterprise customers.
Hired 7 engineers in 14 months during a period of 4x data volume growth.

Software Engineer / Senior Software Engineer — Palantir Technologies, Palo Alto, CA (2010 – 2014)
Individual contributor building distributed data processing systems for US federal
government and financial services customers.

EDUCATION

M.S., Computer Science (Distributed Systems) — Carnegie Mellon University, 2010
B.Tech., Computer Science and Engineering — IIT Bombay, 2008

SKILLS AND TECHNOLOGIES

Languages: Python, Go, Ruby (legacy), Java (reading)
Infrastructure: Kubernetes, AWS (EKS, RDS, S3, CloudFront), Terraform, Datadog
Architecture: microservices, event-driven architecture, API gateway patterns,
service mesh (Istio), internal developer platforms
Process: OKRs, structured hiring (Greenhouse, Karat), incident management (PagerDuty,
blameless post-mortems), engineering leveling frameworks

PERSONAL

Languages: English (native), Hindi (conversational), Kannada (native)
""".strip()

PRIYA_SHARMA_BIG_FIVE = BigFiveScores(
    O=0.72,  # High openness — architectural curiosity, welcomes new approaches
    C=0.85,  # Very high conscientiousness — disciplined execution, strong follow-through
    E=0.68,  # Moderately high extraversion — confident communicator, effective in groups
    A=0.55,  # Medium agreeableness — collaborative but willing to push back
    N=0.22,  # Low neuroticism — calm under sustained operational pressure
)

CANDIDATE_PRIYA = CandidateData(
    name="Priya Sharma",
    cv_text=PRIYA_SHARMA_CV_TEXT,
    big_five=PRIYA_SHARMA_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — James O'Brien (Partial Fit)
# ---------------------------------------------------------------------------

JAMES_OBRIEN_CV_TEXT: str = """
JAMES O'BRIEN
Senior Director of Engineering | Enterprise Architecture | Large-Scale Systems

SUMMARY

Engineering leader with 10 years of management experience in large enterprise
software organizations. Currently Senior Director of Engineering at Oracle NetSuite,
where I lead a 120-person engineering organization responsible for the core Financial
Management and ERP integration platform. Deep expertise in enterprise software
architecture, large-scale distributed systems, and rigorous software engineering
process. Looking for a VP of Engineering role where I can bring enterprise-grade
engineering discipline to a high-growth technology company.

PROFESSIONAL EXPERIENCE

Senior Director of Engineering — Oracle NetSuite, Austin, TX (September 2019 – Present)
Oracle NetSuite is the world's leading cloud ERP platform, serving 40,000+ organizations
across 219 countries. I lead the Financial Management Engineering organization — a
120-person team organized into 9 product squads covering general ledger, accounts
payable, accounts receivable, fixed assets, and multi-subsidiary consolidation.

My team operates in a stable, mature product environment with stringent uptime
requirements: our services underpin the financial close processes for publicly traded
companies, which means a 99.97% availability SLA and no tolerance for data corruption
of any kind. Over the past five years I have implemented a comprehensive engineering
quality program including formal architectural review gates, automated regression
suite expansion (from 18% to 74% statement coverage), and a change management
process that has reduced production incidents caused by software defects by 62%.

I manage the full engineering budget for the Financial Management organization —
$14M per year covering 120 headcount, infrastructure, and tooling — and I present
quarterly spend reviews to the NetSuite CTO. Headcount planning at NetSuite involves
formal workforce management processes, including collaboration with HR and finance
on headcount requisition approvals, which has given me deep familiarity with the
operational mechanics of large-organization hiring — though the velocity of individual
hiring pushes is constrained by the annual planning cycle.

I hold technical authority for the Financial Management architecture. NetSuite's
core platform is a Java-based multi-tenant SaaS application that was originally
designed as a single-tenant hosted application in 2000. Over the past decade the
engineering organization has been gradually extracting subsystems into separately
deployed modules while maintaining the original relational data model. I have driven
three significant architectural extraction projects during my tenure: the payment
processing module, the tax calculation engine, and the reporting and analytics
pipeline. Each of these involved careful migration planning, feature-flag-based
rollout, and extended parallel-run periods to ensure correctness.

Director of Engineering — SAP SuccessFactors, San Francisco, CA (June 2014 – August 2019)
Led a 65-person engineering team building the Workforce Analytics and Planning module
of the SAP SuccessFactors HCM suite. Managed the full product engineering lifecycle
from requirements through deployment for a product serving 3,500 enterprise customers.
Implemented SAP's Engineering Excellence framework across the team, achieving a
formal quality certification in 2017. Drove the migration of the module from an
on-premises deployment model to full SaaS multi-tenancy over a 3-year program,
working closely with SAP's infrastructure and cloud platform organizations.

Engineering Manager — PeopleSoft (acquired by Oracle), Pleasanton, CA (2013 – 2014)
Managed a 15-person team maintaining and extending the PeopleSoft HCM Payroll engine.

Senior Software Engineer — Lawson Software, Minneapolis, MN (2009 – 2013)
Individual contributor developing the financials module of the Lawson S3 ERP platform.

EDUCATION

M.S., Information Systems — University of Minnesota, 2009
B.S., Computer Science — University of Wisconsin-Madison, 2007

CERTIFICATIONS

AWS Certified Solutions Architect — Professional (2022)
SAFe Program Consultant (SPC) — Scaled Agile, Inc. (2018)

SKILLS AND TECHNOLOGIES

Languages: Java, Python, SQL (Oracle, PostgreSQL)
Architecture: multi-tenant SaaS, service-oriented architecture, relational data
modeling, API design (REST, GraphQL), enterprise integration patterns
Process: SAFe Agile, change management, formal quality gates, ISO 27001,
SOC 2 Type II
""".strip()

JAMES_OBRIEN_BIG_FIVE = BigFiveScores(
    O=0.45,  # Below-medium openness — conservative, prefers proven approaches
    C=0.90,  # Very high conscientiousness — meticulous process discipline
    E=0.52,  # Medium extraversion — competent communicator, not energizing
    A=0.70,  # High agreeableness — consensus-seeking, avoids conflict
    N=0.35,  # Low-medium neuroticism — generally stable, some risk aversion
)

CANDIDATE_JAMES = CandidateData(
    name="James O'Brien",
    cv_text=JAMES_OBRIEN_CV_TEXT,
    big_five=JAMES_OBRIEN_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Nina Kowalski (Stretch Candidate, no Big Five)
# ---------------------------------------------------------------------------

NINA_KOWALSKI_CV_TEXT: str = """
NINA KOWALSKI
Director of Engineering | Developer Infrastructure | Remote-First Teams

SUMMARY

Engineering leader with 7 years of management experience, currently Director of
Engineering at Depot (Series B, $22M ARR), where I built the engineering organization
from 8 to 45 engineers over 2 years while establishing a fully remote-first
engineering culture across the US and Poland. Deep expertise in developer infrastructure,
CI/CD systems, and cloud-native architecture. I am seeking a VP of Engineering role
that will stretch my organizational scope — I am ready to lead a team significantly
larger than 45 engineers and looking for the opportunity to prove it.

PROFESSIONAL EXPERIENCE

Director of Engineering — Depot, Inc., Remote (US + Poland) (January 2023 – Present)
Depot is a developer-infrastructure company that builds high-performance cloud build
infrastructure for Docker and GitHub Actions workloads; $22M ARR, 68 employees,
45 engineering staff.

I joined as the fourth engineering hire and effectively the first engineering manager.
The founding team had shipped a compelling initial product and closed a $12M Series A,
but the engineering organization was an undifferentiated group of individual
contributors with no management layer, no hiring process, and no operational
scaffolding. Over the next 24 months I built it into a structured 45-person
organization.

Hiring: I ran 312 interviews across engineering roles in 2023 and 2024, closed 38
net-new hires (including 6 engineering managers and 2 staff engineers), and reduced
time-to-hire from 94 days to 51 days by building a structured sourcing pipeline with
Ashby and a standardized take-home evaluation system. Offer acceptance rate was 81%.

Remote culture: Depot has never had an office. The team is distributed across 11
US states and 3 Polish cities (Warsaw, Wroclaw, Krakow). I established the async-first
communication norms, the weekly engineering all-hands format, the quarterly in-person
engineering summit cadence, and the on-call rotation structure that prevents timezone
imbalance from burning out the Polish team. We currently have a Glassdoor rating of
4.6 and an engineering attrition rate of 6%.

CI/CD and DevOps: I designed and built the internal deployment platform that runs
Depot's production infrastructure — Kubernetes on GKE, ArgoCD for GitOps deployment,
GitHub Actions for CI, Datadog for observability, PagerDuty for incident management.
Mean time to recovery for P1 incidents has improved from 47 minutes to 12 minutes
over 18 months. We ship to production an average of 22 times per day. I wrote the
initial versions of several core infrastructure components and still review all
architectural changes to the deployment platform.

Architecture: Depot's product is itself a distributed system — we orchestrate
ephemeral Kubernetes build clusters across AWS, GCP, and Azure, and we built a
custom layer 4 network proxy to route build traffic to the optimal cloud region.
I drove the architectural evolution from a single-region AWS deployment to our
current multi-cloud, multi-region architecture. We have 14 independently deployable
services and I defined the service ownership model and API contract standards that
govern inter-service communication.

Budget: I own the engineering headcount budget ($3.8M annually) but infrastructure
and tooling spend is managed directly by the co-founder/CTO. I prepare the headcount
plan and present it to the board quarterly alongside the CTO.

Engineering Manager — Oxide Computer Company, Remote (July 2020 – December 2022)
Oxide builds rack-scale compute hardware and software infrastructure for on-premises
private cloud deployments. I managed a 10-person firmware and systems software team
building the Oxide control plane and rack management software stack. Deep exposure to
Rust, distributed consensus protocols, and hardware-software co-design.

Senior Software Engineer → Tech Lead — Netlify, San Francisco, CA (2017 – 2020)
Individual contributor and eventual tech lead on the build and deployment pipeline
team, responsible for the build execution environment that runs 500,000+ user
deployments per day. Contributed core architectural work on Netlify's container
orchestration layer and cache invalidation pipeline.

EDUCATION

B.S., Computer Science — AGH University of Science and Technology, Krakow, Poland, 2017

SKILLS AND TECHNOLOGIES

Languages: Go, Rust, Python, TypeScript
Infrastructure: Kubernetes (GKE, EKS), Terraform, ArgoCD, GitHub Actions, Datadog,
PagerDuty, AWS, GCP, Azure
Architecture: microservices, GitOps, multi-cloud, layer 4 networking, distributed
build systems, internal developer platforms
Process: async-first remote culture, structured interviewing (Ashby, Karat),
blameless post-mortems, OKR planning
""".strip()

CANDIDATE_NINA = CandidateData(
    name="Nina Kowalski",
    cv_text=NINA_KOWALSKI_CV_TEXT,
    big_five=None,
    personality_source=None,
)

# ---------------------------------------------------------------------------
# All candidates
# ---------------------------------------------------------------------------

ALL_CANDIDATES: list[CandidateData] = [CANDIDATE_PRIYA, CANDIDATE_JAMES, CANDIDATE_NINA]

# ---------------------------------------------------------------------------
# Ground truth expectation map
# (candidate_name, requirement_domain) -> expected_direction
#
# Directions: "exceeds" | "meets" | "partial" | "gap"
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[tuple[str, str], str] = {
    # --- Priya Sharma ---
    # 14 years eng leadership, 5+ as VP
    ("Priya Sharma", "engineering_leadership_tenure"): "exceeds",
    # Scaled 30 → 180 (well past the 50 → 120+ threshold)
    ("Priya Sharma", "team_scaling"): "exceeds",
    # SF + Bangalore (55 eng) + London (28 eng), genuine multi-continent distributed
    ("Priya Sharma", "distributed_team_management"): "exceeds",
    # Led full monolith-to-microservices migration (34 services, strangler-fig pattern)
    ("Priya Sharma", "microservices_architecture"): "exceeds",
    # Personally closed 34 senior/staff hires; structured interview system from scratch
    ("Priya Sharma", "hiring_at_scale"): "exceeds",
    # $18M engineering budget, quarterly board presentations
    ("Priya Sharma", "budget_ownership"): "exceeds",
    # Sits in leadership alongside CPO; active roadmap negotiation
    ("Priya Sharma", "cross_functional_collaboration"): "meets",
    # Strong CI/CD platform ownership (Stripe background + Vantage internal dev platform)
    ("Priya Sharma", "devops_cicd"): "exceeds",
    # Vantage and Segment are B2B SaaS; Stripe is B2B developer tooling — close match
    ("Priya Sharma", "industry_experience"): "meets",
    # Bangalore hub establishment, London team, multi-timezone operations
    ("Priya Sharma", "international_experience"): "exceeds",
    # 8% attrition vs 14% benchmark; career-growth system mentioned explicitly
    ("Priya Sharma", "mentoring_culture"): "meets",
    # Board presentations including delivering bad news on migration delay
    ("Priya Sharma", "exec_communication"): "meets",

    # --- James O'Brien ---
    # 10 years eng management, currently Senior Director (not VP title)
    ("James O'Brien", "engineering_leadership_tenure"): "partial",
    # 120-person team but in stable org — no step-change growth phase managed
    ("James O'Brien", "team_scaling"): "gap",
    # US-only; no international team management in CV
    ("James O'Brien", "distributed_team_management"): "gap",
    # Incremental module extraction from monolith (not a full microservices migration)
    ("James O'Brien", "microservices_architecture"): "partial",
    # Hiring constrained by annual planning cycles; no hypergrowth hiring track record
    ("James O'Brien", "hiring_at_scale"): "partial",
    # $14M budget with quarterly spend reviews — meets threshold
    ("James O'Brien", "budget_ownership"): "meets",
    # Partners with HR and finance on headcount; cross-functional in enterprise context
    ("James O'Brien", "cross_functional_collaboration"): "partial",
    # Formal CI/CD processes and quality gates, but enterprise-pace — not fast-ship culture
    ("James O'Brien", "devops_cicd"): "partial",
    # Enterprise SaaS (Oracle, SAP) — B2B, but ERP not cloud infrastructure
    ("James O'Brien", "industry_experience"): "partial",
    # No international team management; US-only experience throughout CV
    ("James O'Brien", "international_experience"): "gap",
    # Formal quality programs and certifications but mentoring culture not evidenced
    ("James O'Brien", "mentoring_culture"): "partial",
    # Quarterly spend reviews with CTO; board exposure limited
    ("James O'Brien", "exec_communication"): "partial",

    # --- Nina Kowalski ---
    # 7 years eng leadership, Director title — below VP tenure bar
    ("Nina Kowalski", "engineering_leadership_tenure"): "partial",
    # 8 → 45 in 24 months — impressive velocity but absolute scale is below threshold
    ("Nina Kowalski", "team_scaling"): "partial",
    # US + Poland (3 cities), async-first remote culture — genuine multi-timezone experience
    ("Nina Kowalski", "distributed_team_management"): "meets",
    # 14 microservices, multi-cloud architecture — built from scratch, not migrated
    ("Nina Kowalski", "microservices_architecture"): "meets",
    # 38 hires in 2 years, structured process, 81% acceptance rate — strong for org size
    ("Nina Kowalski", "hiring_at_scale"): "meets",
    # Headcount budget only ($3.8M); infrastructure spend owned by CTO — gap on full P&L
    ("Nina Kowalski", "budget_ownership"): "partial",
    # Prepares headcount plan for board; limited CPO-level partnership evidence
    ("Nina Kowalski", "cross_functional_collaboration"): "partial",
    # Built entire CI/CD and DevOps stack from scratch — strongest of the three candidates
    ("Nina Kowalski", "devops_cicd"): "exceeds",
    # Depot is B2B developer infrastructure — very close to Cloudbridge's buyer persona
    ("Nina Kowalski", "industry_experience"): "meets",
    # Poland team management, experience with European time zones
    ("Nina Kowalski", "international_experience"): "meets",
    # 6% attrition; explicit async culture investment; Glassdoor 4.6
    ("Nina Kowalski", "mentoring_culture"): "meets",
    # Board headcount presentations alongside CTO; limited solo exec communication
    ("Nina Kowalski", "exec_communication"): "partial",
}

# ---------------------------------------------------------------------------
# Scenario configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG = ScenarioConfig(
    name=ScenarioName.GROWTH,
    category_weights={
        "team_scaling": 1.5,
        "hiring_at_scale": 1.4,
        "distributed_team_management": 1.3,
        "microservices_architecture": 1.2,
        "engineering_leadership_tenure": 1.1,
        "devops_cicd": 1.0,
        "budget_ownership": 1.0,
        "cross_functional_collaboration": 0.9,
        "industry_experience": 0.9,
        "international_experience": 1.2,
        "mentoring_culture": 0.8,
        "exec_communication": 0.8,
    },
)

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "ALL_CANDIDATES",
    "CANDIDATE_JAMES",
    "CANDIDATE_NINA",
    "CANDIDATE_PRIYA",
    "GROUND_TRUTH",
    "JAMES_OBRIEN_BIG_FIVE",
    "JAMES_OBRIEN_CV_TEXT",
    "JD_TEXT",
    "NINA_KOWALSKI_CV_TEXT",
    "PRIYA_SHARMA_BIG_FIVE",
    "PRIYA_SHARMA_CV_TEXT",
    "SCENARIO_CONFIG",
]
