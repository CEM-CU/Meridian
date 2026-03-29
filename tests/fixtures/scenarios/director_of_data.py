"""Synthetic fixture: Director of Data & Analytics at ShieldSure (insurance / insurtech).

Scenario: DIGITAL_TRANSFORMATION — legacy on-prem Oracle DW, board-mandated modernisation.

Three candidates with distinct strength/gap profiles:
- Ananya Reddy: strong fit — insurtech domain, Oracle→Snowflake migration track record,
  manages full-stack data org (eng + analysts + data science), ML pricing models.
- Michael Torres: partial fit — deep data engineering (finserv, not insurance), manages
  engineers only (no analysts or data scientists), weak business-facing analytics/BI.
- Sophie Laurent: stretch — analytics & BI strength, no data engineering depth,
  no insurance/financial services experience, NO Big Five (partial mode).
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

__all__ = [
    "ALL_CANDIDATES",
    "CANDIDATE_ANANYA",
    "CANDIDATE_MICHAEL",
    "CANDIDATE_SOPHIE",
    "GROUND_TRUTH",
    "JD_TEXT",
    "REQUIREMENTS",
    "RUBRIC_ASSESSMENTS",
    "SCENARIO_CONFIG",
]

# ---------------------------------------------------------------------------
# Job Description
# ---------------------------------------------------------------------------

JD_TEXT: str = """
ShieldSure — Director of Data & Analytics

Location: Hartford, CT (hybrid — 3 days on-site, 2 days remote)
Reports to: Chief Information Officer
Direct reports: Data Engineering (8), Analytics (10), Data Science (6) — 24 FTE today,
               growing to 30 over 18 months
Compensation: $210,000-$250,000 base + 20% target bonus + equity participation

About ShieldSure

ShieldSure is one of the Mid-Atlantic's fastest-growing personal and commercial lines
insurers, writing $600M in gross written premium (GWP) across 14 states with 1,100
employees. We distribute through 4,200 independent agents and a growing direct channel.
Over the past three years we have expanded into small-business commercial lines and
launched a telematics-based auto product — growth that has exposed the structural limits
of our existing data infrastructure.

Today our analytics capability rests on a twelve-year-old on-premises Oracle Data
Warehouse, hand-built ETL scripts maintained by two engineers who pre-date the Affordable
Care Act, and a patchwork of Tableau Server dashboards that require manual data pulls.
Our Board of Directors mandated in Q4 2025 a three-year data modernisation roadmap with
$8M in committed capital. The Director of Data & Analytics will own and execute that
roadmap. This is the most consequential hire the CIO organisation will make in 2026.

The Role

You will build ShieldSure's modern data platform from the ground up while simultaneously
running the existing Oracle environment until migration is complete. You will be a
builder and an operator. You will translate complex data concepts for actuaries,
underwriters, and claims managers who are expert in insurance but unfamiliar with
modern data tooling. You will hire, grow, and retain a 24-person organisation spanning
data engineering, analytics, and data science.

Key Responsibilities

- Design and execute the migration from the legacy on-premises Oracle Data Warehouse
  to a cloud-based lakehouse architecture (Snowflake or Databricks preferred), including
  decommissioning of legacy ETL and standing up dbt transformation layers and Airflow
  orchestration.
- Recruit, develop, and manage a blended team of 24 data professionals (data engineers,
  analytics engineers, business analysts, and data scientists), growing to 30 by Q4 2027.
- Own the data platform budget of $5M-$8M annually, including vendor contracts
  (cloud compute, BI tooling, data catalog), headcount, and infrastructure.
- Define and enforce data governance standards: data dictionary, lineage documentation,
  PII classification, and access controls aligned with SOC 2 Type II requirements and
  applicable state insurance data regulations.
- Partner with the Chief Actuary, VP of Underwriting, and VP of Claims to build the
  analytics products they need: loss-development triangles, combined-ratio dashboards,
  agent-performance reporting, and telematics scoring feeds.
- Stand up a machine learning capability: claims frequency/severity prediction models,
  renewal pricing optimisation, and fraud detection — in close collaboration with the
  actuarial team.
- Modernise the BI and reporting layer, migrating from Tableau Server to a self-service
  platform (Tableau Cloud or Looker) that empowers business users to answer their own
  questions without waiting for analyst bandwidth.
- Establish a data literacy programme to build analytical confidence across the
  organisation, with particular focus on underwriting and claims desk populations who
  are resistant to change.
- Ensure all data practices comply with NAIC model regulations, applicable state
  insurance department data requirements, and ShieldSure's internal audit standards.

Required Qualifications

- 10+ years of progressive data and analytics leadership, including at least 4 years
  managing a multi-disciplinary data organisation (engineering + analytics + data science).
- Demonstrated experience architecting or leading migration from legacy on-premises
  data infrastructure to a cloud data platform (Snowflake, Databricks, BigQuery, or
  equivalent); end-to-end ownership of at least one such migration is required.
- Hands-on fluency with the modern data stack: cloud data warehouse, dbt, Airflow or
  equivalent orchestration, and a major BI platform (Tableau or Looker).
- Insurance or financial services domain experience, with working knowledge of actuarial
  concepts, loss ratios, combined ratios, and regulatory reporting obligations.
- Experience owning a data or technology budget of $3M or more.
- Track record of building or significantly scaling a data team through hiring,
  onboarding, and developing talent at multiple levels.
- Data governance experience: schema management, data cataloguing, PII/data-classification
  frameworks, and compliance with regulated-industry data standards (SOC 2, state
  insurance regs, or equivalent).
- Track record of delivering ML models in a production environment (not just prototypes),
  with measurable business outcomes.

Preferred Qualifications

- Experience with insurance-specific data sources: policy administration systems
  (Guidewire, Duck Creek), claims data, telematics feeds, ISO/Verisk data products.
- Familiarity with NAIC Own Risk and Solvency Assessment (ORSA) data requirements
  and state insurance department examination data requests.
- MS or PhD in Statistics, Computer Science, Mathematics, or a quantitative field.

Desired Attributes

- Ability to translate complex data and ML concepts into plain language for non-technical
  stakeholders — actuaries understand statistics but not distributed compute; underwriters
  understand risk but not data pipelines. You must speak both languages.
- Patience and persistence in building data literacy across a legacy insurance culture
  where "we've always done it this way" is a common refrain. Change management is as
  important as technical execution in this role.
- Comfort with ambiguity: the roadmap exists at the Board level; you will write the
  implementation detail. This role requires someone who thrives when handed a mandate
  and a budget rather than a fully scoped backlog.
""".strip()

# ---------------------------------------------------------------------------
# Requirements (extracted, as Stage C1 would produce)
# ---------------------------------------------------------------------------

REQUIREMENTS: list[Requirement] = [
    Requirement(
        requirement_id="REQ-01",
        text="10+ years progressive data/analytics leadership including 4+ years managing multi-disciplinary data org",
        source_quote="10+ years of progressive data and analytics leadership, including at least 4 years managing a multi-disciplinary data organisation",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-02",
        text="Demonstrated end-to-end ownership of legacy on-prem to cloud data platform migration",
        source_quote="Demonstrated experience architecting or leading migration from legacy on-premises data infrastructure to a cloud data platform; end-to-end ownership of at least one such migration is required",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.LOW,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-03",
        text="Hands-on fluency with modern data stack: cloud DW, dbt, Airflow/orchestration, Tableau or Looker",
        source_quote="Hands-on fluency with the modern data stack: cloud data warehouse, dbt, Airflow or equivalent orchestration, and a major BI platform (Tableau or Looker)",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-04",
        text="Insurance or financial services domain experience with working knowledge of actuarial concepts and regulatory reporting",
        source_quote="Insurance or financial services domain experience, with working knowledge of actuarial concepts, loss ratios, combined ratios, and regulatory reporting obligations",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-05",
        text="Budget ownership of $3M+ data or technology budget",
        source_quote="Experience owning a data or technology budget of $3M or more",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.MEDIUM,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-06",
        text="Track record of building and scaling a data team through hiring and development at multiple levels",
        source_quote="Track record of building or significantly scaling a data team through hiring, onboarding, and developing talent at multiple levels",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-07",
        text="Data governance: schema management, data cataloguing, PII classification, regulated-industry compliance (SOC 2 or equivalent)",
        source_quote="Data governance experience: schema management, data cataloguing, PII/data-classification frameworks, and compliance with regulated-industry data standards",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-08",
        text="Production ML models with measurable business outcomes (not just prototypes)",
        source_quote="Track record of delivering ML models in a production environment (not just prototypes), with measurable business outcomes",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-09",
        text="Manage blended data org of 24 FTE across data engineering, analytics engineering, analytics, and data science",
        source_quote="Recruit, develop, and manage a blended team of 24 data professionals (data engineers, analytics engineers, business analysts, and data scientists)",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-10",
        text="Own $5M-$8M annual data platform budget including vendor contracts, headcount, and infrastructure",
        source_quote="Own the data platform budget of $5M-$8M annually, including vendor contracts, headcount, and infrastructure",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.MEDIUM,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-11",
        text="Partner with actuaries, underwriters, and claims managers to build analytics products they need",
        source_quote="Partner with the Chief Actuary, VP of Underwriting, and VP of Claims to build the analytics products they need",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-12",
        text="Translate complex data and ML concepts into plain language for non-technical stakeholders (actuaries, underwriters)",
        source_quote="Ability to translate complex data and ML concepts into plain language for non-technical stakeholders — actuaries understand statistics but not distributed compute",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-13",
        text="Build data literacy across a legacy insurance culture resistant to change",
        source_quote="Patience and persistence in building data literacy across a legacy insurance culture where 'we've always done it this way' is a common refrain",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.LOW,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.LOW,
        ),
    ),
    Requirement(
        requirement_id="REQ-14",
        text="Comfort with ambiguity: translate Board-level mandate into detailed implementation roadmap",
        source_quote="This role requires someone who thrives when handed a mandate and a budget rather than a fully scoped backlog",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.LOW,
            growth=Priority.MEDIUM,
        ),
    ),
]

# ---------------------------------------------------------------------------
# Candidate A — Ananya Reddy (Strong Fit)
# ---------------------------------------------------------------------------

_ANANYA_CV: str = """
ANANYA REDDY
Senior Director of Data & Analytics | Insurance & Insurtech

Hartford, CT · ananya.reddy@email.com · linkedin.com/in/ananyareddy

PROFESSIONAL EXPERIENCE

Senior Director of Data & Analytics — Pivot Insurance Group, Boston, MA (Jan 2021-Present)
Pivot is a $400M GWP personal lines insurtech serving 620,000 policyholders across
11 states, operating on a modern digital distribution stack with a hybrid agency and
direct channel.

- Promoted from Director after 14 months; now lead a 24-person data organisation
  comprising 8 data engineers, 10 analytics engineers and business analysts, and
  6 data scientists. Annual headcount + vendor budget: $7.2M.
- Architected and delivered a three-year Oracle Data Warehouse → Snowflake migration
  across three business units (personal auto, homeowners, renters). Decommissioned
  legacy Oracle 19c environment March 2024, 6 weeks ahead of schedule. Rebuilt all
  ETL in dbt; replaced bespoke job scheduler with Airflow on Kubernetes.
- Migrated BI layer from Tableau Server 2018 to Tableau Cloud; onboarded 180 business
  users within 90 days and reduced ad-hoc analyst query load by 41%.
- Built and deployed three production ML models: (1) renewal pricing optimisation —
  reduced loss ratio by 4.2 percentage points in personal auto across the 2023 renewal
  cohort; (2) claims fraud detection — $3.1M in flagged fraudulent payments prevented in
  2024; (3) telematics driving-score model deployed to 95,000 policyholders.
- Established SOC 2 Type II data controls programme across the data platform; passed
  first examination June 2023 with zero exceptions.
- Defined company-wide data governance framework: data dictionary (1,200 assets),
  PII classification policy, lineage documentation via DataHub, and role-based access
  controls integrated with Okta.
- Partnered weekly with Chief Actuary and VP of Claims on loss-development triangles
  and combined-ratio dashboards; translated Snowflake compute concepts into actuary-
  friendly language for executive steering committee reviews.

Director of Analytics — Beacon Mutual Holdings, Providence, RI (Mar 2018-Dec 2020)
Workers' compensation and commercial property carrier, $190M GWP.

- Managed 11-person analytics team (6 analysts, 3 data scientists, 2 data engineers).
  Owned $3.4M analytics budget.
- Led migration of on-prem SQL Server reporting estate to Redshift; implemented dbt
  for transformation layer and Looker for self-service BI.
- Built first-generation claims severity prediction model (gradient-boosted trees,
  Python/scikit-learn) deployed to claims adjusters via Salesforce integration;
  reduced average claim cycle time by 8.3 days.
- Designed NAIC regulatory reporting pipeline delivering ORSA data extracts to 6 state
  insurance departments with zero SLA misses over 3 years.
- Authored data literacy curriculum ("Data Foundations for Claims Professionals")
  delivered to 280 adjusters and underwriters; post-training data tool adoption
  increased 63% over 6 months.

Senior Analytics Manager — Amica Mutual Insurance, Lincoln, RI (Jul 2015-Feb 2018)
Personal lines carrier, $1.8B GWP, consistently ranked #1 in J.D. Power auto claims
satisfaction.

- Led 7-person analytics team supporting personal auto and homeowners underwriting.
- Built Python-based automated reporting suite replacing 40+ manual Excel-based
  reports; saved ~120 analyst-hours per month.
- Co-led selection and implementation of Tableau Server; trained 90 underwriters on
  self-service reporting.

Analytics Manager — Liberty Mutual Insurance, Boston, MA (Aug 2012-Jun 2015)
- Data analyst to manager track within commercial lines analytics group.
- Developed predictive models for commercial auto loss frequency; contributed to
  rate-filing submissions in 4 states.

EDUCATION
MS, Statistics — Carnegie Mellon University, Pittsburgh, PA (2012)
BS, Mathematics — University of Massachusetts, Amherst, MA (2010)

CERTIFICATIONS & SKILLS
Snowflake SnowPro Core Certified (2022) · dbt Certified Developer (2023)
Airflow, Kubernetes, DataHub, Tableau Cloud, Looker, Python (pandas, scikit-learn,
XGBoost), SQL (expert), Redshift, Oracle, Spark (working knowledge)
Insurance domain: ISO/Verisk, Guidewire Claims Center (integration), Duck Creek Policy
""".strip()

CANDIDATE_ANANYA: CandidateData = CandidateData(
    name="Ananya Reddy",
    cv_text=_ANANYA_CV,
    big_five=BigFiveScores(
        O=0.80,  # High openness — drives modernisation, embraces new tooling
        C=0.78,  # High conscientiousness — structured execution, SOC 2 compliance
        E=0.60,  # Moderate extraversion — competent communicator with executives
        A=0.55,  # Medium agreeableness — collaborative but holds the line on governance
        N=0.22,  # Low neuroticism — calm through multi-year migration projects
    ),
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — Michael Torres (Partial Fit)
# ---------------------------------------------------------------------------

_MICHAEL_CV: str = """
MICHAEL TORRES
Director of Data Engineering | Financial Services & Real-Time Analytics

New York, NY · michael.torres@email.com · linkedin.com/in/michaeltorres

PROFESSIONAL EXPERIENCE

Director of Data Engineering — Broadridge Financial Solutions, New York, NY (Feb 2020-Present)
Broadridge is a $6B revenue fintech and financial services processing company serving
broker-dealers, asset managers, and banks across 100+ countries.

- Lead an 18-person data engineering team building and operating Broadridge's
  real-time data platform: event streaming (Kafka, 2.8M events/sec peak), batch
  ETL (Spark on Databricks), and Snowflake enterprise data warehouse (420 TB, 600+
  daily dbt jobs).
- Architected migration from legacy Hadoop/Hive on-prem cluster to Databricks + Snowflake
  cloud platform over 26 months (2020-2022); decommissioned 480-node on-prem cluster,
  reducing infrastructure cost by $4.1M annually.
- Own $6.3M annual platform budget (cloud compute, vendor licences, headcount).
- Implemented Apache Airflow 2.x on Kubernetes for pipeline orchestration; reduced
  pipeline failure rate from 4.2% to 0.3% over 18 months.
- Established data platform governance: Collibra data catalog (3,400 assets), column-
  level lineage, PII classification aligned with SOC 2 Type II and GDPR/CCPA.
- Drove Snowflake performance optimisation initiative reducing average query time by
  67% and monthly compute spend by $180K.
- Partnered with CISO to achieve SOC 2 Type II certification for data platform;
  passed examination November 2022 with two minor observations, both remediated.

Senior Data Engineer → Lead Data Engineer — JPMorgan Chase, New York, NY (Jun 2014-Jan 2020)
- Progressed from individual contributor to tech lead on the Market Risk data pipeline
  team (8 engineers).
- Designed real-time VaR (Value-at-Risk) data pipeline processing 14M trades/day from
  35 source systems into the firm's risk analytics platform; achieved sub-second latency
  SLA for regulatory reporting.
- Led technical migration of equity derivatives data mart from Oracle Exadata to
  Redshift; 180TB dataset, zero downtime cutover.
- Built automated regulatory data reconciliation framework used by 4 trading desks;
  reduced manual reconciliation effort by 1,400 analyst-hours per year.

Data Engineer — Fidelity Investments, Boston, MA (Aug 2010-May 2014)
- Member of the Enterprise Data Warehouse team (SQL Server, SSIS, SSRS).
- Built and maintained ETL pipelines for mutual fund NAV reporting and fund
  accounting; supported month-end close processes across 240 fund entities.

EDUCATION
MS, Computer Science — Northeastern University, Boston, MA (2010)
BS, Computer Engineering — University of Florida, Gainesville, FL (2008)

CERTIFICATIONS & SKILLS
Databricks Certified Data Engineer Professional (2023)
Snowflake SnowPro Advanced: Data Engineer (2022)
Apache Kafka, Apache Spark, Apache Airflow (expert), dbt, Kubernetes, Terraform,
Python (PySpark, pandas), SQL (expert), Collibra, Snowflake, Databricks, Redshift,
Oracle Exadata, Hadoop/Hive
Financial services regulatory: SEC Rule 17a-4, CFTC swap data reporting, GDPR/CCPA
""".strip()

CANDIDATE_MICHAEL: CandidateData = CandidateData(
    name="Michael Torres",
    cv_text=_MICHAEL_CV,
    big_five=BigFiveScores(
        O=0.70,  # Moderately high openness — adopts new tech, less people/culture focus
        C=0.82,  # High conscientiousness — disciplined platform engineering
        E=0.45,  # Below-average extraversion — builder, not natural business translator
        A=0.60,  # Medium agreeableness — collaborative within eng, less with business
        N=0.28,  # Low neuroticism — steady under complex migrations
    ),
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Sophie Laurent (Stretch / Partial Mode)
# ---------------------------------------------------------------------------

_SOPHIE_CV: str = """
SOPHIE LAURENT
Head of Analytics | Retail & Consumer Insights

Chicago, IL · sophie.laurent@email.com · linkedin.com/in/sophielaurent

PROFESSIONAL EXPERIENCE

Head of Analytics — HomeGoods Direct, Chicago, IL (Mar 2022-Present)
HomeGoods Direct is a $1.1B revenue omnichannel home furnishings retailer operating
380 stores and a growing e-commerce platform (38% of revenue in 2025).

- Built and lead a 12-person analytics organisation from a team of 2 part-time analysts
  at a time when the company had no analytics function. Team composition: 4 analytics
  engineers, 5 business analysts, 3 data scientists.
- Partnered with CTO to select and deploy Looker as the company's self-service BI
  platform (replacing Tableau Desktop plus ad-hoc Excel); onboarded 220 business
  users across merchandising, finance, and supply chain within 4 months.
- Designed and launched "Analytics Academy" — a data literacy programme for 350
  non-technical staff across buying, planning, and store operations; 78% of programme
  graduates report independently using Looker for weekly reporting within 3 months.
- Defined data governance framework: LookML semantic layer as single source of truth,
  dbt data quality tests across 140 models, metadata documentation in dbt Docs.
- Managed $2.8M analytics budget (tooling + headcount).
- Built customer lifetime value (CLV) model and churn prediction model (XGBoost);
  CLV model integrated into email campaign targeting, driving 22% uplift in repeat
  purchase rate for predicted top-decile customers.
- Partnered with VP of Finance and Chief Merchandising Officer on weekly trading
  performance reviews; translated statistical model outputs into plain-language
  business narratives for non-technical leadership.

Senior Analytics Manager — Walgreens Boots Alliance, Deerfield, IL (Aug 2019-Feb 2022)
- Led 7-person analytics team supporting store operations and pharmacy benefits
  management analytics.
- Stood up dbt + BigQuery transformation layer replacing a legacy Informatica ETL
  estate; reduced report refresh latency from 48 hours to 90 minutes.
- Designed pharmacy fill-rate and patient-adherence dashboards used by 800+ pharmacists
  across the Midwest region.
- Collaborated with vendor data scientists on medication adherence prediction model;
  contributed feature engineering and business validation.

Analytics Manager — Nielsen, Chicago, IL (Jun 2016-Jul 2019)
- Managed 4-person team delivering retail sales measurement analytics for CPG clients
  (Procter & Gamble, Unilever, Kimberly-Clark).
- Automated client reporting pipeline (Python, SQL, Tableau); reduced report delivery
  time from 5 days to same-day for 12 key accounts.

EDUCATION
MBA — Kellogg School of Management, Northwestern University, Evanston, IL (2016)
BS, Economics — McGill University, Montréal, QC (2013)

CERTIFICATIONS & SKILLS
Looker (LookML), dbt Certified Developer (2023), BigQuery, Tableau, Python (pandas,
scikit-learn, XGBoost), SQL (advanced), Google Analytics 4
Retail/CPG domain: Nielsen, IRI, Salesforce Marketing Cloud
Languages: English (native), French (native), Spanish (intermediate)
""".strip()

CANDIDATE_SOPHIE: CandidateData = CandidateData(
    name="Sophie Laurent",
    cv_text=_SOPHIE_CV,
    big_five=None,  # No Big Five — partial assessment mode
    personality_source=None,
)

ALL_CANDIDATES: list[CandidateData] = [
    CANDIDATE_ANANYA,
    CANDIDATE_MICHAEL,
    CANDIDATE_SOPHIE,
]

# ---------------------------------------------------------------------------
# Rubric assessments (as Stage C3 would produce -- one per candidate x requirement)
# ---------------------------------------------------------------------------

RUBRIC_ASSESSMENTS: list[RubricAssessment] = [
    # ----------------------------
    # Ananya Reddy
    # ----------------------------
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="lead a 24-person data organisation comprising 8 data engineers, 10 analytics engineers and business analysts, and 6 data scientists",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="12 years total experience; 7 years in management across Amica, Beacon, Pivot. Current role exceeds scope of target role.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Architected and delivered a three-year Oracle Data Warehouse → Snowflake migration across three business units. Decommissioned legacy Oracle 19c environment March 2024, 6 weeks ahead of schedule. Rebuilt all ETL in dbt; replaced bespoke job scheduler with Airflow on Kubernetes.",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="End-to-end Oracle→Snowflake migration with dbt and Airflow — exact technology match. Plus prior Redshift migration at Beacon.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Snowflake SnowPro Core Certified (2022) · dbt Certified Developer (2023). Airflow, Kubernetes, DataHub, Tableau Cloud, Looker, Python",
        cv_location="Certifications & Skills section",
        notes="Full modern stack coverage — Snowflake, dbt, Airflow, and both major BI platforms. Certifications add confidence.",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Designed NAIC regulatory reporting pipeline delivering ORSA data extracts to 6 state insurance departments. Partnered weekly with Chief Actuary and VP of Claims on loss-development triangles and combined-ratio dashboards.",
        cv_location="Director of Analytics — Beacon Mutual Holdings; Senior Director — Pivot",
        notes="8 years in insurance across personal lines, commercial lines, and workers comp. Deep actuarial and regulatory familiarity.",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Annual headcount + vendor budget: $7.2M",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="$7.2M current budget exceeds the $5-8M target. Also owned $3.4M at Beacon — consistent budget ownership track record.",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="built and leads a 24-person data organisation comprising 8 data engineers, 10 analytics engineers and business analysts, and 6 data scientists",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="Team grew from ~11 (Beacon) to 24 (Pivot current). Clear trajectory of building multi-disciplinary orgs.",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Established SOC 2 Type II data controls programme across the data platform; passed first examination June 2023 with zero exceptions. Defined company-wide data governance framework: data dictionary (1,200 assets), PII classification policy, lineage documentation via DataHub",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="SOC 2 Type II with zero exceptions is the gold standard result. Governance framework scope and specificity are strong.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="renewal pricing optimisation — reduced loss ratio by 4.2 percentage points in personal auto; claims fraud detection — $3.1M in flagged fraudulent payments prevented in 2024; telematics driving-score model deployed to 95,000 policyholders",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="Three production ML models in insurance domain with specific, quantified business outcomes. Outstanding evidence quality.",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="lead a 24-person data organisation comprising 8 data engineers, 10 analytics engineers and business analysts, and 6 data scientists",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="Exact headcount match. Note current org is already at target size (24 FTE); ShieldSure wants to grow to 30 — Ananya has grown from 11→24 so trajectory is positive.",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Annual headcount + vendor budget: $7.2M",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="$7.2M sits within the $5-8M target range. Budget experience aligns closely.",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Partnered weekly with Chief Actuary and VP of Claims on loss-development triangles and combined-ratio dashboards",
        cv_location="Senior Director of Data & Analytics — Pivot Insurance Group (2021-Present)",
        notes="Direct actuary and claims partnership documented. Beacon NAIC ORSA deliveries also evidence stakeholder delivery to senior insurance professionals.",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. CV mentions actuary partnership and translation work but cannot assess communication style from text alone.",
        investigation_question="Can you walk us through how you explained the renewal pricing model's assumptions and limitations to the Chief Actuary and board audit committee?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.MEDIUM,
        cv_citation="Authored data literacy curriculum ('Data Foundations for Claims Professionals') delivered to 280 adjusters and underwriters; post-training data tool adoption increased 63% over 6 months",
        cv_location="Director of Analytics — Beacon Mutual Holdings (2018-2020)",
        notes="Structured data literacy programme in an insurance context with measurable adoption outcome. Strong evidence for this behavioral attribute. Recency note: this was at Beacon (2018-2020), not current role.",
        investigation_question="What specific resistance patterns did you encounter when rolling out the curriculum and how did you adapt the approach?",
    ),
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Ananya Reddy",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute (ambiguity tolerance). CV shows initiative and ownership but cannot assess comfort with mandate-without-backlog from text.",
        investigation_question="Describe the state of the data roadmap when you joined Pivot. How much of the implementation plan existed, and how did you go from Board mandate to operating plan?",
    ),
    # ----------------------------
    # Michael Torres
    # ----------------------------
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Lead an 18-person data engineering team",
        cv_location="Director of Data Engineering — Broadridge Financial Solutions (2020-Present)",
        notes="14 years experience meets tenure requirement. However manages engineers only — no analysts, no data scientists. The 'multi-disciplinary' requirement (eng + analytics + data science) is not met.",
        investigation_question="Have you had P&L or functional accountability for analytics or data science teams, even in a dotted-line or project-lead capacity?",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Architected migration from legacy Hadoop/Hive on-prem cluster to Databricks + Snowflake cloud platform over 26 months (2020-2022); decommissioned 480-node on-prem cluster, reducing infrastructure cost by $4.1M annually.",
        cv_location="Director of Data Engineering — Broadridge Financial Solutions (2020-Present)",
        notes="End-to-end on-prem to cloud migration with full decommission. Larger scale and comparable complexity to ShieldSure Oracle migration.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Databricks Certified Data Engineer Professional (2023). Snowflake SnowPro Advanced: Data Engineer (2022). Apache Kafka, Apache Spark, Apache Airflow (expert), dbt, Kubernetes",
        cv_location="Certifications & Skills section",
        notes="Deep hands-on stack coverage — advanced certifications in Snowflake and Databricks. dbt and Airflow both present. BI platform coverage absent (no Tableau or Looker experience in CV).",
        investigation_question="What has been your personal involvement with Tableau or Looker? Do you have hands-on experience defining BI strategy, or have you primarily handed off to a separate BI team?",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Financial services regulatory: SEC Rule 17a-4, CFTC swap data reporting, GDPR/CCPA",
        cv_location="Certifications & Skills section",
        notes="Strong financial services background (JPMorgan, Broadridge) but zero insurance experience. Regulatory landscape differs materially: NAIC, state DOI examinations, insurance-specific data standards are absent. Actuarial concepts (loss ratios, combined ratios) not evidenced.",
        investigation_question="How familiar are you with insurance-specific regulatory data requirements — NAIC ORSA filings, state DOI data examinations — and actuarial concepts like loss development?",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Own $6.3M annual platform budget (cloud compute, vendor licences, headcount)",
        cv_location="Director of Data Engineering — Broadridge Financial Solutions (2020-Present)",
        notes="$6.3M budget ownership, within the $5-8M target range. Meets threshold with margin.",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Lead an 18-person data engineering team",
        cv_location="Director of Data Engineering — Broadridge Financial Solutions (2020-Present)",
        notes="Has grown and led engineering teams, but no evidence of building analytics or data science talent. ShieldSure needs multi-disciplinary team building. The 10→18 engineering growth is positive signal within the narrow eng scope.",
        investigation_question="Describe how you have recruited and developed non-engineering data talent — analytics engineers, business analysts, or data scientists.",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Established data platform governance: Collibra data catalog (3,400 assets), column-level lineage, PII classification aligned with SOC 2 Type II and GDPR/CCPA. Partnered with CISO to achieve SOC 2 Type II certification.",
        cv_location="Director of Data Engineering — Broadridge Financial Solutions (2020-Present)",
        notes="SOC 2 Type II achieved at Broadridge. Collibra catalog at 3,400 assets — larger and more mature than typical. Insurance-specific standards (NAIC) not present but core governance competency is strong.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of ML model ownership or data science partnership. CV is entirely focused on data engineering and platform infrastructure. JPMorgan VaR pipeline is risk analytics infrastructure, not ML model development.",
        investigation_question="Have you had direct responsibility for ML model development, deployment, or production monitoring — or have data science teams always owned that layer independently?",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Lead an 18-person data engineering team",
        cv_location="Director of Data Engineering — Broadridge Financial Solutions (2020-Present)",
        notes="18 engineers but no analysts or data scientists. ShieldSure org (24 FTE) is blended across three disciplines; Michael has managed only one. Gap is structural, not cosmetic.",
        investigation_question="The ShieldSure data org is 8 engineers, 10 analysts/analytics engineers, and 6 data scientists. How would you approach leading the analytics and data science functions you haven't directly managed before?",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Own $6.3M annual platform budget (cloud compute, vendor licences, headcount)",
        cv_location="Director of Data Engineering — Broadridge Financial Solutions (2020-Present)",
        notes="$6.3M within target range.",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of partnering with non-technical business stakeholders (actuaries, underwriters, claims). JPMorgan work involved trading desk partnership but those are quantitatively sophisticated. ShieldSure requires translating for non-technical insurance professionals — a material gap for a low-E candidate.",
        investigation_question="Describe a situation where you had to work closely with non-technical business stakeholders to define their analytics needs and translate those into a data platform capability.",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral. Low E score (0.45) may create friction here; no CV evidence of business translation work.",
        investigation_question="Walk us through how you explained your Databricks migration architecture to non-technical executives at Broadridge. What was your approach to making technical concepts accessible?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of data literacy programming in CV. Engineering-focused background makes this a likely gap.",
        investigation_question="Have you ever designed or led a data literacy programme for non-technical employees? How have you approached building data culture in resistant organisations?",
    ),
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Michael Torres",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral. Cannot assess from CV text.",
        investigation_question="Describe a situation where you were handed a mandate with budget but no detailed specification. How did you move from concept to operating plan?",
    ),
    # ----------------------------
    # Sophie Laurent
    # ----------------------------
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="8 years analytics, currently Head of Analytics at a mid-size retailer",
        cv_location="Professional Experience — aggregate",
        notes="8 years total experience — below the 10+ year threshold. Team of 12 is below the 24-person target. Has managed analytics engineers and data scientists but no data engineers. Partial on experience depth and multi-disciplinary scope.",
        investigation_question="Have you had functional accountability for data engineering teams, even with a dotted-line reporting structure?",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of legacy on-prem to cloud DW migration ownership. Walgreens BigQuery work replaced Informatica ETL but was scoped as a manager-level contribution, not end-to-end architecture ownership. ShieldSure requires direct Oracle migration leadership.",
        investigation_question="The core infrastructure deliverable is migrating ShieldSure's on-prem Oracle DW to Snowflake. Describe your experience with data warehouse migrations at that architectural level.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="dbt Certified Developer (2023), BigQuery, Tableau, Python (pandas, scikit-learn, XGBoost), SQL (advanced). Looker (LookML)",
        cv_location="Certifications & Skills section",
        notes="Strong BI (Looker LookML, Tableau) and dbt. No Snowflake, no Airflow, no cloud DW architecture experience beyond BigQuery at manager level. Modern stack is partial — BI layer strong, infrastructure/orchestration layer absent.",
        investigation_question="How deep is your hands-on experience with Snowflake and Airflow? Have you designed warehouse architecture or primarily consumed the platform built by an engineering team?",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="Retail and CPG background (HomeGoods Direct, Walgreens, Nielsen). No insurance or financial services experience. No evidence of actuarial concepts, loss ratios, regulatory reporting. Walgreens pharmacy work involves healthcare data but is not insurance regulation.",
        investigation_question="What is your familiarity with insurance industry concepts — loss ratios, combined ratios, NAIC regulatory filings, state DOI data requirements?",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Managed $2.8M analytics budget (tooling + headcount)",
        cv_location="Head of Analytics — HomeGoods Direct (2022-Present)",
        notes="$2.8M is below the $3M threshold stated in the JD (and well below the $5-8M target). First significant budget ownership role.",
        investigation_question="The ShieldSure data platform budget is $5-8M annually. What is the largest budget you have directly managed and what does that scope-up look like for you?",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Built and lead a 12-person analytics organisation from a team of 2 part-time analysts at a time when the company had no analytics function.",
        cv_location="Head of Analytics — HomeGoods Direct (2022-Present)",
        notes="0→12 team build is compelling evidence for team-building capability. However, team is analytics-only; ShieldSure needs eng + analytics + data science.",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Defined data governance framework: LookML semantic layer as single source of truth, dbt data quality tests across 140 models, metadata documentation in dbt Docs.",
        cv_location="Head of Analytics — HomeGoods Direct (2022-Present)",
        notes="Analytics-layer governance (LookML, dbt tests, docs) is present but no SOC 2, no PII classification at scale, no regulated-industry compliance experience. Insurance data governance is more demanding.",
        investigation_question="Describe your experience with formal data compliance programmes — SOC 2, PII classification, or regulated-industry data standards beyond retail/CPG.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Built customer lifetime value (CLV) model and churn prediction model (XGBoost); CLV model integrated into email campaign targeting, driving 22% uplift in repeat purchase rate",
        cv_location="Head of Analytics — HomeGoods Direct (2022-Present)",
        notes="Two production ML models with business outcomes. Positive signal. However retail CLV/churn is significantly less complex than insurance pricing or claims severity models; regulatory constraints absent.",
        investigation_question="The ShieldSure ML roadmap includes claims frequency/severity prediction and pricing optimisation. How does your experience with CLV and churn modelling translate to actuarially regulated pricing models?",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="12-person analytics organisation: 4 analytics engineers, 5 business analysts, 3 data scientists",
        cv_location="Head of Analytics — HomeGoods Direct (2022-Present)",
        notes="12 FTE vs 24 target — half the scale. No data engineers in current org. ShieldSure's 8 data engineers would be new territory for Sophie.",
        investigation_question="How would you approach managing the data engineering function when your current team has no dedicated data engineers?",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="Managed $2.8M analytics budget",
        cv_location="Head of Analytics — HomeGoods Direct (2022-Present)",
        notes="$2.8M is significantly below the $5-8M target. ShieldSure budget includes infrastructure and compute spend Sophie has not owned.",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Partnered with VP of Finance and Chief Merchandising Officer on weekly trading performance reviews; translated statistical model outputs into plain-language business narratives for non-technical leadership.",
        cv_location="Head of Analytics — HomeGoods Direct (2022-Present)",
        notes="Strong executive partnership and business translation evidence. Retail context differs from insurance but stakeholder management quality is evident.",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral. CV shows strong business-narrative translation practice; direct assessment requires interview.",
        investigation_question="How would you approach explaining the difference between a Snowflake compute cluster and a traditional data warehouse to ShieldSure's Chief Actuary?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="designed and launched 'Analytics Academy' — a data literacy programme for 350 non-technical staff; 78% of programme graduates report independently using Looker for weekly reporting within 3 months",
        cv_location="Head of Analytics — HomeGoods Direct (2022-Present)",
        notes="Structured data literacy programme with quantified adoption outcome. Best evidence on this requirement across all three candidates. Industry context is retail, not insurance, but programme design quality is high.",
    ),
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Sophie Laurent",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral. 0→12 team build at HomeGoods suggests comfort with building from scratch, but mandate scale differs.",
        investigation_question="When you joined HomeGoods Direct, what existed in terms of data roadmap? How did you determine priorities when the function was effectively greenfield?",
    ),
]

# ---------------------------------------------------------------------------
# Ground truth expectations (for test assertion)
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, dict] = {
    "Ananya Reddy": {
        "overall_fit": "strong",
        "assessment_mode": "full",
        "key_strengths": [
            "REQ-02",  # Oracle→Snowflake migration end-to-end
            "REQ-04",  # Insurance domain depth (8 years, NAIC, actuarial partnership)
            "REQ-08",  # Three production ML models with quantified insurance outcomes
            "REQ-07",  # SOC 2 Type II with zero exceptions
        ],
        "notable_gaps": [],
        "behavioral_flags": [
            "REQ-12",  # Stakeholder translation: not assessable from CV — needs interview
        ],
        "high_priority_gaps": [],
        "expected_rubric_distribution": {
            RubricLevel.EXCEEDS: 8,
            RubricLevel.MEETS: 2,
            RubricLevel.PARTIAL: 0,
            RubricLevel.GAP: 0,
            RubricLevel.NOT_ASSESSABLE: 3,
        },
        "advance_to_interview": True,
        "advance_rationale": (
            "Exceeds on all assessable technical and domain requirements. "
            "Insurance-domain ML outcomes (4.2pp loss ratio reduction) are directly "
            "transferable. Current org size matches ShieldSure target exactly. "
            "Only open items are three behavioral attributes requiring interview validation."
        ),
    },
    "Michael Torres": {
        "overall_fit": "partial",
        "assessment_mode": "full",
        "key_strengths": [
            "REQ-02",  # Hadoop→Databricks+Snowflake migration at larger scale
            "REQ-03",  # Deep modern data stack (Databricks certified, Snowflake advanced)
            "REQ-07",  # SOC 2 Type II at Broadridge
        ],
        "notable_gaps": [
            "REQ-04",  # No insurance domain; financial services but not insurance regulatory
            "REQ-08",  # No ML model ownership; data engineering only
            "REQ-11",  # No non-technical business stakeholder partnership evidence
        ],
        "high_priority_gaps": [
            "REQ-04",  # Insurance domain is HIGH priority under digital_transformation
            "REQ-08",  # ML production is HIGH priority under digital_transformation
        ],
        "behavioral_flags": [
            "REQ-12",  # Low E (0.45) + no business translation evidence = risk flag
            "REQ-13",  # No data literacy programme evidence
        ],
        "advance_to_interview": True,
        "advance_rationale": (
            "Strong on platform engineering and migration execution — the hardest "
            "technical requirements. Key gaps are insurance domain knowledge, ML "
            "ownership, and business-facing analytics management. Interview should "
            "probe depth of financial services regulatory transfer and appetite to "
            "expand scope to analytics and data science disciplines."
        ),
    },
    "Sophie Laurent": {
        "overall_fit": "stretch",
        "assessment_mode": "partial",  # No Big Five — partial mode
        "key_strengths": [
            "REQ-06",  # 0→12 team build
            "REQ-11",  # Stakeholder partnership and business translation
            "REQ-13",  # Analytics Academy — data literacy programme
        ],
        "notable_gaps": [
            "REQ-02",  # No legacy on-prem DW migration ownership — critical gap
            "REQ-04",  # No insurance/financial services domain
            "REQ-10",  # Budget ($2.8M) significantly below target ($5-8M)
        ],
        "high_priority_gaps": [
            "REQ-02",  # HIGH priority under digital_transformation — the core deliverable
            "REQ-04",  # HIGH priority under digital_transformation
        ],
        "behavioral_flags": [],
        "advance_to_interview": False,
        "advance_rationale": (
            "Exceptional data literacy and stakeholder management. However, absence of "
            "end-to-end data warehouse migration experience is a disqualifying gap for "
            "this specific role — the Oracle migration is the primary Year 1 deliverable. "
            "No insurance domain experience adds further risk. Recommend revisiting if "
            "the role is restructured to de-emphasise the migration component, or as a "
            "strong candidate for a Head of Analytics role if ShieldSure splits the function."
        ),
    },
    "_scenario_notes": {
        "scenario": "digital_transformation",
        "critical_requirements": ["REQ-02", "REQ-04", "REQ-08"],
        "differentiating_requirement": "REQ-02",  # Migration ownership separates A from B and C
        "behavioral_requirements_not_cv_assessable": ["REQ-12", "REQ-13", "REQ-14"],
        "expected_ranking": ["Ananya Reddy", "Michael Torres", "Sophie Laurent"],
    },
}

# ---------------------------------------------------------------------------
# Scenario configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG: ScenarioConfig = ScenarioConfig(
    name=ScenarioName.DIGITAL_TRANSFORMATION,
    category_weights={
        "EXECUTION": 1.6,  # Migration execution is the primary Year 1 deliverable
        "EXPERIENCE_STRENGTH": 1.4,  # Domain depth (insurance) is differentiating
        "EXPERIENCE_GAP": 1.5,  # Gaps in critical requirements are penalised heavily
        "STRATEGIC": 1.2,  # ML/AI strategy and platform roadmap ownership
        "CULTURAL": 1.1,  # Change management and data literacy
        "EVIDENCE_QUALITY": 1.0,
        "FRICTION": 0.9,  # Personality friction less critical than execution risk
        "DERAILMENT": 1.0,
        "COLLISION": 0.8,
        "COMPLEMENT": 0.8,
        "INTEGRATION": 1.0,
        "TENURE": 0.7,
        "GROUPTHINK": 0.6,
        "DARK_SIDE": 1.0,
        "ROUTING": 1.0,
    },
)
