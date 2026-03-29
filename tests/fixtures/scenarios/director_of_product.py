"""Synthetic fixture: Director of Product at MedAxis (healthcare / medtech, Series B).

Scenario: TURNAROUND -- product-market fit lost after failed pivot to enterprise.
Need to reset product strategy, rebuild PM team morale, and ship a focused v2 in 9 months.

Three candidates with distinct fit profiles against the MedAxis Director of Product JD:
- Carlos Rivera: strong fit -- healthtech turnaround track record, manages 8 PMs, deep domain
- Rachel Goldstein: partial fit -- deep clinical domain, no PM leadership or 0-to-1 experience
- Tomasz Nowak: stretch -- strong data/relaunch track record, zero healthcare, no Big Five

Ground-truth expectations map:
  (candidate_name, requirement_domain) -> expected RubricLevel direction

Scenario config: TURNAROUND with category weights reflecting urgency of execution,
strategic reset, and team leadership.
"""

from meridian.models import BigFiveScores, CandidateData, ScenarioConfig, ScenarioName

# ---------------------------------------------------------------------------
# Job Description
# ---------------------------------------------------------------------------

JD_TEXT: str = """
MedAxis -- Director of Product
Location: Boston, MA (hybrid; remote candidates considered for exceptional fit)
Reports to: Chief Executive Officer
Direct reports: 6 product managers (current team); expectation to grow to 8-10 within 18 months

About MedAxis

MedAxis is a Boston-based digital health company building clinical decision-support tools
for ambulatory care. Our flagship product, AxisPath, helps independent physician practices
manage chronic disease populations through predictive risk stratification, automated care-gap
alerts, and EHR-embedded workflow nudges. We serve 340 practices and 2.1 million attributed
patients across 14 states, generating $22M ARR.

In 2023 we made a deliberate bet to expand upmarket: we attempted to repackage AxisPath as
an enterprise population-health platform targeting regional health systems and ACOs. Eighteen
months and $6.8M in R&D spend later, we did not win a single health-system contract of
meaningful size. The pivot fractured our product roadmap, diluted engineering effort, and
confused our core physician-practice customers. Two of our five senior PMs resigned. The
board has made clear that the company has one window -- approximately nine months -- to ship
a differentiated, focused version 2 of AxisPath that re-establishes product-market fit with
independent practices and unlocks the next funding round.

We have brought in a new CEO to lead the reset. The Director of Product is the first
strategic hire under that reset and will own the product function end-to-end.

The Role

You will set the product strategy, rebuild a high-performing PM team, and ship AxisPath v2.
This is not a caretaker role. We need a product leader who has been in a burning building
before, knows how to focus when everything feels urgent, and can rebuild trust with a team
that has been through a demoralising eighteen months.

Key Responsibilities

- Define and own the product strategy for AxisPath v2: set the north star, prune the
  roadmap ruthlessly, and build board-level conviction around a focused bet.
- Lead customer discovery: return to basics -- 40+ customer interviews in the first 90 days,
  synthesise findings into a crisp problem statement, and validate the v2 thesis before
  a single line of code is written.
- Manage and rebuild the PM team: directly manage 6 PMs, run structured 1-1s, rebuild
  psychological safety, and establish a clear craft bar. Hire 2-3 additional PMs within
  six months.
- Drive the v2 roadmap to delivery: own prioritisation across a constrained engineering
  team (14 engineers), manage trade-offs transparently, and hold the team to a
  nine-month ship date.
- Rebuild confidence with clinical partners and physician practice customers: attend
  quarterly advisory board meetings, present roadmap to clinical advisory committee,
  and re-establish MedAxis as a trusted product partner.
- Represent the product function to the board and investors: present at quarterly board
  meetings, field diligence questions during Series C preparation.
- Partner with the Chief Medical Officer and clinical informatics team on HIPAA compliance
  workflows, data-use agreements, and FDA regulatory positioning for any features that
  touch clinical decision-making.

Required Qualifications

- 8+ years of product management experience, with at least 3 years in a leadership role
  managing a team of product managers (minimum 4 direct reports).
- Demonstrated experience shipping a product from 0 to 1 -- taking an idea from concept
  through customer validation, MVP, and commercial launch.
- Proven track record of product strategy reset or turnaround: killed features or product
  lines, refocused a roadmap, and measurably improved business outcomes within 12 months.
- Healthcare or regulated-industry experience: working knowledge of clinical workflows,
  EHR integrations (HL7/FHIR), HIPAA data-handling requirements, or FDA software-as-a-
  medical-device (SaMD) frameworks.
- Strong customer discovery and user research skills: ability to design and execute
  qualitative research programmes, synthesise insights, and turn them into actionable
  product decisions.
- Data-driven decision making: comfortable with product analytics, funnel analysis,
  retention modelling, and A/B testing frameworks. Able to challenge engineering estimates
  with data and defend prioritisation decisions quantitatively.
- Technical fluency: able to participate in architecture discussions, review API contracts,
  understand data pipeline design, and translate engineering constraints into product
  trade-offs. Not expected to write code.
- Roadmap prioritisation at resource constraint: experience using frameworks such as RICE,
  WSJF, or opportunity scoring to prioritise ruthlessly with limited engineering capacity.
- Stakeholder management: experience presenting product strategy to boards, investors,
  and clinical or scientific advisory committees.

Desired Attributes

- Resilience under sustained pressure: you have led a team through a difficult period
  without burning them out or losing credibility. You know the difference between
  urgency and panic.
- Trust rebuilder: you have a specific playbook for restoring team morale and psychological
  safety after organisational setbacks. People have followed you out of hard situations.
- Direct communicator: you give clear, candid feedback -- to engineers, to PMs, to the
  CEO, and to the board. You do not optimise for comfort in difficult conversations.
- Regulatory awareness without paranoia: you understand that HIPAA and FDA constraints
  shape what we can ship and when, but you do not use compliance as an excuse to
  slow down.
""".strip()

# ---------------------------------------------------------------------------
# Candidate A -- Carlos Rivera (Strong Fit)
# ---------------------------------------------------------------------------

CARLOS_RIVERA_CV_TEXT: str = """
CARLOS RIVERA
Product Leader | Digital Health & Clinical Workflow

Boston, MA  |  carlos.rivera@email.com  |  linkedin.com/in/carlosrivera

PROFESSIONAL EXPERIENCE

VP of Product, Luminary Health -- Cambridge, MA (January 2021 - Present)
Luminary Health is a Series C digital health company ($35M ARR) building care coordination
software for value-based care organisations. Reports to CEO. Manages 8 product managers
and 4 product designers across two product lines.

- Inherited a product organisation that had lost focus following a failed expansion into
  Medicare Advantage plan administration. Executed a 90-day product reset: deprecated 3
  feature sets that accounted for 22% of engineering surface area but less than 4% of
  customer value, and refocused the roadmap on care-gap management for primary care.
  Within 12 months, ARR grew from $25M to $35M (+40%), NPS improved from 18 to 47, and
  average contract value increased 31%.
- Led 0-to-1 launch of Luminary Longitudinal, a patient-journey analytics module built on
  FHIR R4 data ingestion from 6 EHR platforms. Took from concept to GA in 11 months.
  Product now accounts for 28% of new ARR.
- Rebuilt the PM team from 4 to 12 (including 4 designers) over 18 months. Introduced
  structured product reviews, a career ladder with clear levelling criteria, and a
  biweekly craft session. Zero PM attrition in the 18 months following the reset.
- Introduced RICE scoring framework for quarterly roadmap prioritisation; reduced
  unplanned engineering work from 34% to 11% of sprint capacity within two quarters.
- Partnered with CMO and clinical informatics team on HIPAA-compliant data architecture
  for the analytics module, including BAA structuring with 3 EHR vendors and a data-use
  agreement template adopted across the customer base.
- Presented product strategy at 4 consecutive board meetings and led product diligence
  sessions with 2 Series C investors; Series C closed at $68M in Q1 2024.

Director of Product Management, Catalyze Digital Health -- San Francisco, CA
(March 2018 - December 2020)
Catalyze built clinical documentation automation tools for hospital outpatient clinics.
Managed a team of 4 PMs and owned the practitioner-facing workflow product line.

- Led ground-up rebuild of the scheduling and intake product following a 2018 competitive
  displacement event. Conducted 52 practitioner interviews and 8 contextual inquiry
  sessions across 3 health systems over 60 days. Distilled findings into a revised
  problem statement that reframed the product from "documentation tool" to
  "pre-encounter workflow hub."
- Shipped the redesigned product (Catalyze Encounter) in 9 months. Reduced practitioner
  time-to-complete intake by 38%; drove 19-point increase in product satisfaction scores.
- Led HIPAA risk assessment for a new real-time messaging feature; worked with legal and
  security to implement end-to-end encryption and audit-logging compliant with 45 CFR
  Part 164.
- Developed internal opportunity-scoring framework for prioritisation under constrained
  engineering resources (7 engineers); framework adopted company-wide.

Senior Product Manager, Athenahealth -- Watertown, MA (July 2015 - February 2018)
Product lead for the chronic disease management module within athenaOne EHR. Worked
directly with clinical advisory board of 12 physicians.

- Managed HL7 v2 and CCDA integration workstreams with 11 external EHR and HIE partners.
- Led FDA SaMD classification assessment for a new risk-stratification scoring feature;
  worked with outside counsel to establish regulatory pathway and document clinical
  validation evidence.
- Built product analytics infrastructure in Mixpanel and Looker; defined retention and
  engagement KPIs that became the standard for the chronic disease product portfolio.

Product Manager, GetWell Network -- Bethesda, MD (August 2013 - June 2015)
PM for a patient engagement platform deployed in 140 hospitals. Owned the mobile care
plan product from MVP through v3 release.

EDUCATION
MBA, Boston University Questrom School of Business (2013)
BS, Biomedical Engineering, University of Michigan (2011)

CERTIFICATIONS
Certified Scrum Product Owner (CSPO), 2016
HIPAA Privacy & Security Compliance Certificate, AHIMA, 2017
""".strip()

CARLOS_RIVERA_BIG_FIVE = BigFiveScores(
    O=0.75,  # High openness -- embraces new frameworks, customer discovery orientation
    C=0.70,  # High conscientiousness -- disciplined execution under constraint
    E=0.72,  # High extraversion -- confident presenter, energises teams
    A=0.40,  # Below-average agreeableness -- willing to make unpopular calls, kill features
    N=0.25,  # Low neuroticism -- calm in a turnaround, does not panic under board pressure
)

CANDIDATE_CARLOS = CandidateData(
    name="Carlos Rivera",
    cv_text=CARLOS_RIVERA_CV_TEXT,
    big_five=CARLOS_RIVERA_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B -- Rachel Goldstein (Partial Fit)
# ---------------------------------------------------------------------------

RACHEL_GOLDSTEIN_CV_TEXT: str = """
RACHEL GOLDSTEIN
Senior Product Manager | Clinical Informatics & Patient Experience

Boston, MA  |  rachel.goldstein@email.com  |  linkedin.com/in/rachelgoldstein

PROFESSIONAL EXPERIENCE

Senior Product Manager -- Clinical Decision Support, Mass General Brigham (Partners eCare)
Boston, MA (September 2019 - Present)
MGB is one of the largest integrated health systems in the United States. Partners eCare
is the Epic-based EHR platform serving 80,000+ employees across 15 hospitals and 400
outpatient practices. This is an individual-contributor role embedded in the Clinical
Informatics division.

- Product owner for the Clinical Decision Support (CDS) Hooks infrastructure serving
  22 active clinical rules and 6,400 daily provider interactions. Reduced alert fatigue
  by 31% through rule rationalisation study (n=1,200 providers, 6-month trial).
- Led a CDS usability research programme -- published findings in JAMIA (Journal of the
  American Medical Informatics Association) in 2022: "Alert Design and Clinician
  Response Rates: a Mixed-Methods Study in a Large Academic Health System."
  (doi:10.1093/jamia/ocac147)
- Conducted 140+ structured user interviews with attending physicians, nurses, and
  pharmacists over 4 years; built and maintained a research repository in Dovetail
  with 3,200+ tagged observations.
- Designed and ran 3 A/B tests within the Epic Hyperspace environment (non-trivial
  in an EHR context); documented methodology in an internal playbook now used across
  the MGB digital team.
- Deep expertise in HL7 FHIR R4, CDS Hooks specification, SMART on FHIR application
  framework, and Epic's extension APIs. Regularly review and contribute to internal
  HL7 ballots.
- Led HIPAA Privacy Impact Assessment for a new genomic data integration feature;
  worked with IRB, legal, and compliance to establish appropriate consent frameworks
  and data-use restrictions.

Product Manager -- Patient Portal & Engagement, Dana-Farber Cancer Institute
Boston, MA (June 2016 - August 2019)
Individual contributor role managing MyChart patient portal features for oncology workflows.

- Owned the MyChart oncology care-plan module: redesigned information architecture
  based on 68 patient interviews and 12 caregiver sessions. Reduced portal abandonment
  rate by 24%.
- Led integration of a third-party symptom-tracking tool (Navigating Care) with Dana-Farber's
  Epic instance via SMART on FHIR; managed vendor relationship and technical integration
  specification.
- Partnered with clinical operations to embed portal messaging workflows into nurse
  triage protocols, reducing phone intake volume by 18%.
- Delivered 4 features under FDA Software as a Medical Device (SaMD) Class I exempt
  classification; worked with regulatory affairs team on 510(k) exemption documentation.

Associate Product Manager, athenahealth -- Watertown, MA (July 2014 - May 2016)
Rotational APM programme. Rotations in: billing, patient scheduling, and population
health analytics. Contributed to HL7 v2 interface testing and requirements documentation.

EDUCATION
Master of Public Health (MPH), Health Informatics concentration,
Harvard T.H. Chan School of Public Health (2014)
BA, Cognitive Science (with distinction), Yale University (2012)

PUBLICATIONS & PRESENTATIONS
- Goldstein R., et al. "Alert Design and Clinician Response Rates: a Mixed-Methods Study
  in a Large Academic Health System." JAMIA, 2022.
- Presenter, AMIA Annual Symposium 2023: "CDS Hooks in Production: Lessons from 22
  Clinical Rules at Scale."
- Presenter, Epic XGM 2022: "Reducing Alert Fatigue Through Systematic Rule Review."
""".strip()

RACHEL_GOLDSTEIN_BIG_FIVE = BigFiveScores(
    O=0.82,  # Very high openness -- researcher disposition, intellectually curious
    C=0.65,  # High conscientiousness -- rigorous, methodical, evidence-driven
    E=0.48,  # Medium extraversion -- competent in groups but not dominant; IC orientation
    A=0.75,  # High agreeableness -- collaborative, empathetic, consensus-builder
    N=0.28,  # Low neuroticism -- steady and measured, but less battle-tested under crisis
)

CANDIDATE_RACHEL = CandidateData(
    name="Rachel Goldstein",
    cv_text=RACHEL_GOLDSTEIN_CV_TEXT,
    big_five=RACHEL_GOLDSTEIN_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C -- Tomasz Nowak (Stretch / Partial Mode)
# ---------------------------------------------------------------------------

TOMASZ_NOWAK_CV_TEXT: str = """
TOMASZ NOWAK
Director of Product | Fintech & Data Platforms

New York, NY (remote-first, open to Boston relocation)
tomasz.nowak@email.com  |  linkedin.com/in/tomasznowak

PROFESSIONAL EXPERIENCE

Director of Product Management, Vantage Financial Technologies -- New York, NY (remote)
(February 2020 - Present)
Vantage is a Series B fintech ($18M ARR) providing embedded banking infrastructure
to mid-market software companies. Acquired by Meridian Capital Group in 2022. Reports
to CPO. Manages a team of 5 product managers distributed across New York, Warsaw, and
Singapore.

- Led product relaunch following Meridian acquisition: within 6 months of acquisition,
  new parent required Vantage to deprecate its own brand and reposition as a white-label
  infrastructure provider. Conducted rapid market research (28 customer interviews,
  14 prospect conversations in 45 days) to reframe the go-to-market thesis. Shipped
  the rebranded platform (Meridian Embedded Banking) 7 months post-acquisition with
  zero enterprise customer churn during transition.
- Managed a fully remote, cross-timezone PM team (UTC-5 / UTC+1 / UTC+8) through the
  acquisition and relaunch period. Established async-first collaboration norms,
  bi-weekly team retrospectives, and a structured OKR cadence that maintained
  morale through 8 months of organisational uncertainty.
- Built and shipped an internal experimentation platform from 0 to 1: designed the
  feature-flagging and A/B testing infrastructure that enabled 14 concurrent product
  experiments across the platform. Reduced time-from-hypothesis-to-data from 3 weeks
  to 4 days. Platform now handles 220M events per day.
- Introduced WSJF prioritisation across a 9-person engineering team; reduced backlog
  scope by 40% in one quarter while shipping 3 net-new revenue-generating features.
- Drove product analytics maturity from near-zero baseline: implemented Segment, built
  an event taxonomy of 180 standardised events, and established weekly data reviews
  as a standing PM team ritual.
- Presented product strategy at 5 board meetings; led due diligence sessions with
  3 prospective Series C investors.

Senior Product Manager -- Payments & Risk, Stripe -- San Francisco, CA
(April 2017 - January 2020)
Individual contributor PM for Stripe Radar (ML-based fraud detection) and Stripe Connect
(marketplace payments). Owned the dispute management and chargeback workflow product.

- Led 0-to-1 development of the Radar for Fraud Teams product: took from internal
  prototype to GA in 14 months. Product reached $4.2M ARR within 12 months of launch,
  serving 180 enterprise customers.
- Built a real-time event-streaming data pipeline (Kafka + Flink) for fraud signal
  processing; worked closely with ML and data engineering to define feature store
  schema and model retraining triggers.
- Designed API contracts for the Radar Rules engine; wrote and reviewed 12 API
  specifications against the OpenAPI 3.0 standard.
- Managed a demanding set of financial regulatory requirements: PCI-DSS compliance,
  FinCEN SAR filing workflows, and CFPB consumer-protection mapping. Developed
  a regulatory requirements register used across the payments product group.

Product Manager, TransferWise (now Wise) -- London, UK (remote)
(September 2015 - March 2017)
PM for the international transfers and currency exchange product. Managed the speed-
vs-cost routing engine and customer-facing transfer timeline features.

EDUCATION
MSc, Information Systems Management, London School of Economics (2015)
BEng, Computer Science, Warsaw University of Technology (2013)

LANGUAGES
Polish (native), English (fluent), German (professional working proficiency)

CERTIFICATIONS
AWS Certified Solutions Architect -- Associate (2021)
Pragmatic Marketing Certified Level IV (PMC-IV), 2019
""".strip()

CANDIDATE_TOMASZ = CandidateData(
    name="Tomasz Nowak",
    cv_text=TOMASZ_NOWAK_CV_TEXT,
    big_five=None,  # NO Big Five -- partial assessment mode
    personality_source=None,
)

# ---------------------------------------------------------------------------
# All candidates
# ---------------------------------------------------------------------------

ALL_CANDIDATES: list[CandidateData] = [CANDIDATE_CARLOS, CANDIDATE_RACHEL, CANDIDATE_TOMASZ]

# ---------------------------------------------------------------------------
# Ground truth: (candidate_name, requirement_domain) -> expected RubricLevel direction
#
# Values are RubricLevel strings: "exceeds", "meets", "partial", "gap", "not_assessable"
# Behavioral-only requirements are "not_assessable" for CV-based rubric.
# These represent the expected outcome an evaluator should reach given the CV evidence.
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[tuple[str, str], str] = {
    # --- Carlos Rivera ---
    # Strong fit across nearly every domain
    ("Carlos Rivera", "product_strategy_reset"): "exceeds",
    # 90-day reset at Luminary, killed 3 features, 40% ARR growth
    ("Carlos Rivera", "pm_team_leadership"): "exceeds",
    # 8 PMs + 4 designers; built from 4 to 12
    ("Carlos Rivera", "zero_to_one_launch"): "exceeds",
    # Luminary Longitudinal 0-to-GA in 11 months; GetWell mobile care plan
    ("Carlos Rivera", "customer_discovery"): "meets",
    # 52 practitioner interviews at Catalyze; 40+ cited in role
    ("Carlos Rivera", "healthcare_domain"): "exceeds",
    # Athenahealth, Catalyze, Luminary; EHR integrations, HIPAA, SaMD
    ("Carlos Rivera", "hipaa_regulatory_awareness"): "meets",
    # HIPAA cert; BAA structuring; HIPAA risk assessment at Catalyze
    ("Carlos Rivera", "fda_samd_awareness"): "partial",
    # SaMD classification assessment at Athenahealth; some depth, not deep
    ("Carlos Rivera", "data_driven_decision_making"): "meets",
    # RICE scoring; Mixpanel/Looker KPIs; reduced unplanned work 34% to 11%
    ("Carlos Rivera", "technical_fluency"): "meets",
    # FHIR data ingestion; API contracts; data pipeline discussions
    ("Carlos Rivera", "roadmap_prioritisation"): "exceeds",
    # RICE at Luminary; opportunity-scoring framework adopted company-wide
    ("Carlos Rivera", "stakeholder_management_board"): "exceeds",
    # 4 board presentations; Series C diligence at Luminary
    ("Carlos Rivera", "clinical_partner_relationships"): "meets",
    # Clinical advisory board at Athenahealth; CMO partnership at Luminary
    ("Carlos Rivera", "resilience_under_pressure"): "not_assessable",  # behavioral
    ("Carlos Rivera", "trust_rebuilding"): "not_assessable",  # behavioral
    ("Carlos Rivera", "direct_communication"): "not_assessable",  # behavioral
    # --- Rachel Goldstein ---
    # Strong on domain and research; significant gaps on leadership and commercial product
    ("Rachel Goldstein", "product_strategy_reset"): "gap",
    # No evidence of strategic reset; IC track, no P&L or roadmap ownership
    ("Rachel Goldstein", "pm_team_leadership"): "gap",
    # No direct reports, no PM management experience; IC throughout
    ("Rachel Goldstein", "zero_to_one_launch"): "gap",
    # Internal/EHR tools only; no commercial 0-to-1 product launch
    ("Rachel Goldstein", "customer_discovery"): "exceeds",
    # 140+ structured interviews; JAMIA publication; Dovetail repository
    ("Rachel Goldstein", "healthcare_domain"): "exceeds",
    # MGB, Dana-Farber, Athenahealth; FHIR, CDS Hooks, SMART; deep expertise
    ("Rachel Goldstein", "hipaa_regulatory_awareness"): "exceeds",
    # HIPAA PIA; genomic data consent frameworks; 45 CFR Part 164
    ("Rachel Goldstein", "fda_samd_awareness"): "meets",
    # SaMD Class I exempt work at Dana-Farber; 510(k) documentation
    ("Rachel Goldstein", "data_driven_decision_making"): "meets",
    # A/B tests in Epic; alert-fatigue study n=1,200; methodology playbook
    ("Rachel Goldstein", "technical_fluency"): "exceeds",
    # HL7 FHIR R4; CDS Hooks spec; SMART on FHIR; HL7 ballot contributions
    ("Rachel Goldstein", "roadmap_prioritisation"): "partial",
    # IC-level prioritisation; no cross-team or constrained-resource framing
    ("Rachel Goldstein", "stakeholder_management_board"): "partial",
    # No board exposure; clinical committee presentations only
    ("Rachel Goldstein", "clinical_partner_relationships"): "exceeds",
    # 4 years clinical advisory work; 6,400 daily provider interactions
    ("Rachel Goldstein", "resilience_under_pressure"): "not_assessable",  # behavioral
    ("Rachel Goldstein", "trust_rebuilding"): "not_assessable",  # behavioral
    ("Rachel Goldstein", "direct_communication"): "not_assessable",  # behavioral
    # --- Tomasz Nowak ---
    # Solid execution core; zero healthcare domain; regulatory gap is critical
    ("Tomasz Nowak", "product_strategy_reset"): "meets",
    # Vantage post-acquisition relaunch; zero churn; 7-month turnaround
    ("Tomasz Nowak", "pm_team_leadership"): "meets",
    # 5 PMs across 3 timezones; maintained morale through acquisition
    ("Tomasz Nowak", "zero_to_one_launch"): "exceeds",
    # Stripe Radar for Fraud Teams 0-to-GA; experimentation platform 0-to-1
    ("Tomasz Nowak", "customer_discovery"): "partial",
    # 28 interviews + 14 prospect conversations at Vantage; adequate but narrow
    ("Tomasz Nowak", "healthcare_domain"): "gap",
    # Zero healthcare experience; fintech only
    ("Tomasz Nowak", "hipaa_regulatory_awareness"): "gap",
    # No HIPAA exposure; PCI-DSS/FinCEN not analogous for hiring panel
    ("Tomasz Nowak", "fda_samd_awareness"): "gap",
    # No evidence; fintech regulatory (FinCEN, CFPB) is domain-mismatched
    ("Tomasz Nowak", "data_driven_decision_making"): "exceeds",
    # Experimentation platform; 220M events/day; Segment/event taxonomy
    ("Tomasz Nowak", "technical_fluency"): "exceeds",
    # Kafka/Flink pipelines; OpenAPI specs; AWS SA cert; feature-flag infra
    ("Tomasz Nowak", "roadmap_prioritisation"): "meets",
    # WSJF; reduced backlog 40%; 9-person engineering team
    ("Tomasz Nowak", "stakeholder_management_board"): "meets",
    # 5 board presentations; Series C diligence at Vantage
    ("Tomasz Nowak", "clinical_partner_relationships"): "gap",
    # No clinical partners or health-system relationships
    ("Tomasz Nowak", "resilience_under_pressure"): "not_assessable",  # behavioral
    ("Tomasz Nowak", "trust_rebuilding"): "not_assessable",  # behavioral
    ("Tomasz Nowak", "direct_communication"): "not_assessable",  # behavioral
}

# ---------------------------------------------------------------------------
# Scenario configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG = ScenarioConfig(
    name=ScenarioName.TURNAROUND,
    category_weights={
        # Execution is paramount: 9-month deadline, constrained team, must ship
        "EXECUTION": 1.8,
        # Strategic reset is the core mandate from the board
        "STRATEGIC": 1.6,
        # Team leadership: PM team is depleted, rebuilding is non-negotiable
        "EXPERIENCE_STRENGTH": 1.4,
        # Experience gaps in regulated domain are high-risk in healthcare
        "EXPERIENCE_GAP": 1.4,
        # Cultural fit for turnaround pace matters more than in steady-state
        "CULTURAL": 1.2,
        # Derailment risk elevated under board pressure
        "DERAILMENT": 1.2,
        # Evidence quality -- early-stage startup, less data available
        "EVIDENCE_QUALITY": 0.9,
        # Complement/collision dynamics matter but are secondary to execution
        "COMPLEMENT": 0.8,
        "COLLISION": 0.8,
        # Friction and groupthink are lower priority in turnaround context
        "FRICTION": 0.7,
        "GROUPTHINK": 0.6,
        # Integration and tenure flags are lower weight at Series B stage
        "INTEGRATION": 0.7,
        "TENURE": 0.6,
    },
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "ALL_CANDIDATES",
    "CANDIDATE_CARLOS",
    "CANDIDATE_RACHEL",
    "CANDIDATE_TOMASZ",
    "GROUND_TRUTH",
    "JD_TEXT",
    "SCENARIO_CONFIG",
]
