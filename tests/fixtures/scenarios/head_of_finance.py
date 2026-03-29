"""Synthetic Head of Finance scenario fixture for NovaMart (e-commerce, post-IPO stabilisation).

Scenario: STABILIZATION — 18 months post-IPO. NovaMart needs mature financial controls,
SOX compliance, and a professional investor relations cadence. The outgoing Head of Finance
was a startup-era generalist. The role reports to the CFO and leads a 28-person finance team
across London HQ, Netherlands, and Poland.

Three candidates:
- Elena Vasquez: strong fit — post-IPO SOX lead, e-commerce Finance Director, SAP expert.
- David Chen: partial fit — strong compliance/audit in manufacturing, no e-commerce or IR.
- Aisha Okonkwo: stretch — FP&A depth, e-commerce unit economics, no SOX or team scale.
  NO Big Five (partial assessment mode).
"""

from shared.models import (
    BigFiveScores,
    CandidateData,
    ScenarioConfig,
    ScenarioName,
)

# ---------------------------------------------------------------------------
# Job Description
# ---------------------------------------------------------------------------

JD_TEXT: str = """
NovaMart — Head of Finance

Location: London, UK (HQ) with regular travel to Amsterdam (Netherlands) and Warsaw (Poland)
Reports to: Chief Financial Officer
Direct reports: Finance team of 28 (FP&A, accounting, tax, treasury, and compliance sub-functions)

About NovaMart

NovaMart is the UK's fastest-growing pure-play online retailer, serving 11 million active
customers across the UK, Netherlands, Poland, and the Republic of Ireland. Founded in 2017,
NovaMart completed its IPO on the London Stock Exchange in October 2023, raising £320M at
a valuation of £2.4B. Today the business generates £1.2B in annual net revenue, operates
4 fulfilment centres (Coventry, Amsterdam, Wrocław, and Dublin), and employs approximately
3,200 people. We are now 18 months into our public-company journey and building the financial
infrastructure, governance, and external reporting cadence that our shareholders, auditors,
and regulators rightly expect.

The Role

We are looking for an experienced Head of Finance to serve as a senior business partner to
the CFO and to lead our finance function through its next phase of maturity. The previous
postholder built strong commercial instincts during our scale-up years; we now need someone
who can layer rigorous internal controls, SOX-equivalent compliance, and world-class
financial reporting on top of that commercial foundation — without losing the speed and
agility that got us here.

You will own the operating finance function end-to-end: financial planning and analysis,
statutory and management reporting, treasury and cash management, tax compliance across
four jurisdictions, internal controls, and our Big 4 external audit relationship. You will
also play a central role in preparing quarterly earnings materials and supporting investor
relations activities in partnership with the CFO.

Key Responsibilities

Financial Planning & Analysis
- Own the annual budget process and rolling three-year financial plan for a £52M annual
  operating budget, coordinating inputs from all business units and reporting to the
  Board Audit & Risk Committee.
- Lead monthly and quarterly business performance reviews: produce variance analyses,
  commentary packs, and forward-looking scenario models that enable the CFO and executive
  team to make high-quality decisions at speed.
- Build and maintain a suite of e-commerce-specific unit economic metrics — contribution
  margin by channel, customer acquisition cost (CAC), lifetime value (LTV), return rate
  impact, and fulfilment cost per order — that connect operational KPIs to P&L outcomes.

Financial Controls & Compliance
- Design and operate a financial controls framework aligned with SOX Section 302 and 404
  requirements, working with internal audit and our external auditors (currently Deloitte)
  to achieve a clean opinion on internal controls in the FY2025 annual report cycle.
- Maintain compliance with IFRS 15, IFRS 16 (significant lease portfolio across four
  fulfilment centres), and relevant UK and EU statutory reporting requirements.
- Manage multi-entity consolidation across five legal entities spanning GBP, EUR, PLN,
  and USD, ensuring accurate intercompany eliminations and currency translation.

Investor Relations & External Reporting
- Partner with the CFO to prepare quarterly earnings materials: draft the investor
  presentation, CFO commentary script, and Q&A briefing document for each results
  announcement cycle (four per year).
- Coordinate the preparation and review of the Annual Report and Accounts, liaising
  with legal, company secretary, and IR teams to meet regulatory disclosure deadlines.
- Support ad hoc investor and analyst requests, providing financial models and
  supplemental data packs that accurately represent NovaMart's business economics.

Team Leadership & ERP Ownership
- Lead, develop, and retain a 28-person finance team across London, Amsterdam, and
  Warsaw; manage a team structure that delivers both technical depth and commercial
  business partnering capacity.
- Own the ERP and financial systems roadmap; NovaMart is currently mid-way through
  a migration from NetSuite to SAP S/4HANA (go-live target: Q3 2026) and requires a
  leader who can manage delivery risk while maintaining business continuity.

Required Qualifications & Experience

- ACA, ACCA, or CPA qualified, with a minimum of 10 years post-qualification experience
  in a multi-entity commercial finance environment.
- Proven track record implementing or operating within a SOX or SOX-equivalent internal
  controls framework in a publicly listed company.
- Experience managing a finance team of at least 20 people across multiple office locations,
  including hiring, performance management, and organisational design.
- Direct involvement in investor relations activities — earnings preparation, analyst
  briefings, or Annual Report drafting — in a listed company context.
- Hands-on experience with ERP platforms (SAP S/4HANA or NetSuite); experience managing
  or leading an ERP migration is strongly preferred.
- Demonstrable experience managing the Big 4 external audit relationship, including
  coordinating audit fieldwork, resolving audit queries, and presenting to Audit Committees.
- Exposure to multi-currency, multi-entity consolidation under IFRS in a business with
  significant transactional volumes (GBP, EUR, PLN as a minimum).
- Experience in e-commerce, retail, or a high-volume consumer business, with working
  knowledge of unit economics metrics relevant to online retail.
- Experience preparing or owning the annual operating budget at a scale of £30M+ and
  managing rolling forecast processes used by the Board.

Desired Attributes

- Comfortable presenting financial results and forward-looking scenarios to a listed-company
  board and its committees; able to translate complex financial narratives into clear,
  concise investor language under time pressure.
- Demonstrated ability to influence cross-functional stakeholders — logistics, commercial,
  technology — to embed financial discipline without creating bureaucratic friction.
- Calm and systematic during month-end and quarter-end close cycles, able to maintain
  control quality and team morale simultaneously.
""".strip()

# ---------------------------------------------------------------------------
# Candidate A — Elena Vasquez (Strong Fit)
# ---------------------------------------------------------------------------

ELENA_VASQUEZ_CV_TEXT: str = """
ELENA VASQUEZ ACA
Finance Director | E-Commerce & Retail | London

PROFESSIONAL SUMMARY

Finance Director with 12 years of progressive experience in high-growth e-commerce and
retail environments. Currently leading the finance function at a £900M online retailer
through the post-IPO build-out phase. Track record includes owning a full SOX 302/404
implementation from scratch, migrating a 22-entity NetSuite landscape to SAP S/4HANA,
and managing a 28-person team across the UK and Netherlands. Frequent presenter to the
Audit Committee and Board; experienced in quarterly earnings preparation and investor
briefing materials.

PROFESSIONAL EXPERIENCE

Finance Director -- Bloom & Basket Ltd, London, UK (Jan 2020 - Present)
Bloom & Basket is a UK-listed (AIM) online grocery and home goods retailer with £900M
net revenue, 2.6M active customers, and operations in the UK, Netherlands, and Belgium.

- Own end-to-end finance function: FP&A, statutory reporting, treasury, tax, and internal
  controls across four legal entities (GBP, EUR, PLN-adjacent supplier contracts).
- Led the SOX 302 and 404 implementation programme following AIM listing in 2021:
  scoped 47 key controls across revenue recognition, procure-to-pay, and financial
  reporting; achieved clean external auditor opinion (EY) on internal controls for
  FY2021 and FY2022 annual reports.
- Deliver quarterly earnings materials in partnership with the CEO and CFO: draft investor
  presentations (12 slides), CFO commentary scripts, and analyst Q&A briefing packs for
  each of four results cycles per year; materials reviewed by the Board before release.
- Manage a 28-person finance team (8 in Amsterdam, 20 in London); reduced voluntary
  attrition from 24% to 11% over three years through structured development programmes
  and clearer career paths.
- Owning the SAP S/4HANA migration (project budget £4.2M), replacing a fragmented
  NetSuite + spreadsheet landscape; Phase 1 (GL, AP, AR) went live January 2024 on
  time and within 3% of budget.
- Produce monthly e-commerce unit economics dashboard: contribution margin by channel
  (marketplace vs. direct), CAC by acquisition cohort, LTV:CAC ratios, fulfilment cost
  per order, and return rate impact on gross margin; used by the CEO in monthly
  performance reviews.
- Manage the annual operating budget of £38M; introduced zero-based budgeting for
  overhead functions, reducing cost growth by 6.2% year-on-year in FY2023.

Head of FP&A -- Kestrel Commerce Group, London, UK (Mar 2016 - Dec 2019)
Kestrel Commerce is a privately owned multi-channel retailer (fashion and homeware),
with £280M revenue across UK and Irish operations.

- Built the FP&A function from a 3-person team to 9 analysts; introduced a rolling
  13-week cash flow forecast model that reduced CFO blind-spots during peak trading
  periods (Black Friday, January sale).
- Prepared board pack financial narratives for monthly ExCo meetings; presented to
  non-executive directors on three occasions in the CFO's absence.
- Managed multi-entity consolidation (5 entities, GBP and EUR) under IFRS; led first-time
  adoption of IFRS 16 in FY2019, modelling the lease liability impact across 34 store and
  warehouse leases (£62M right-of-use asset).
- Coordinated annual audit with Deloitte; reduced audit completion time by 3 weeks by
  introducing a structured PBC (prepared by client) document management process.

Senior Finance Business Partner -- ASOS plc, London, UK (Sep 2012 - Feb 2016)
- Business partner to the Technology and Logistics functions (combined cost base £95M),
  providing monthly actuals, forecasts, and investment appraisals to functional directors.
- Built fulfilment cost-per-order model used to assess profitability of introducing
  next-day delivery; analysis directly informed the decision to invest £14M in the
  Barnsley fulfilment centre automation project.

EDUCATION
- ACA, Institute of Chartered Accountants in England and Wales (First time passes, 2012)
- BSc Economics — University of Warwick (2:1, 2009)

CERTIFICATIONS & PROFESSIONAL DEVELOPMENT
- SAP S/4HANA Finance (TS4FI) certified, 2023
- ICAEW Corporate Finance qualification (awarded 2018)

LANGUAGES: English (native), Spanish (conversational)
""".strip()

ELENA_VASQUEZ_BIG_FIVE = BigFiveScores(
    O=0.48,  # Medium — pragmatic, not driven by novelty; works within established frameworks
    C=0.92,  # Very high — highly disciplined, meticulous controls orientation
    E=0.55,  # Medium — capable communicator with Board and analysts but not dominant
    A=0.65,  # Moderately high — builds cross-functional relationships without conflict avoidance
    N=0.18,  # Very low — exceptionally calm; thrives during close cycles and audit season
)

CANDIDATE_ELENA = CandidateData(
    name="Elena Vasquez",
    cv_text=ELENA_VASQUEZ_CV_TEXT,
    big_five=ELENA_VASQUEZ_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — David Chen (Partial Fit)
# ---------------------------------------------------------------------------

DAVID_CHEN_CV_TEXT: str = """
DAVID CHEN CPA
VP Finance | Manufacturing & Industrial | Chicago

PROFESSIONAL SUMMARY

Finance leader with 15 years of experience in US-listed and PE-backed manufacturing
businesses. Deep expertise in SOX compliance, cost accounting, P&L management, and
Big 4 audit relationships. Proven track record managing large finance teams (up to 35
people) and delivering clean audit opinions across complex multi-plant environments.
Seeking a senior finance leadership role in a high-growth consumer or retail business
where my operational finance rigour can drive commercial performance improvement.

PROFESSIONAL EXPERIENCE

VP Finance -- Cortex Industrial Solutions Inc., Chicago, IL, USA (Jun 2018 - Present)
Cortex Industrial is a NYSE-listed precision components manufacturer with USD 780M
revenue, 4,200 employees, and 11 manufacturing plants across the US, Mexico, and Canada.

- Lead a 35-person finance organisation across plant controllers, FP&A, and corporate
  accounting; direct reports include 4 Finance Managers and a Financial Controller.
- Own SOX 302 and 404 compliance programme across 11 business units: maintain 63
  documented key controls; liaise directly with KPMG on annual controls testing; achieved
  clean opinion every year from 2019 through 2024.
- Manage the annual operating budget of USD 58M; introduced a driver-based budgeting model
  in FY2022 that reduced preparation cycle time from 14 weeks to 9 weeks.
- Lead the annual audit with KPMG (Big 4); manage the PBC schedule, fieldwork coordination,
  and Audit Committee presentation; audit completed within agreed timeline for 6 consecutive
  years.
- Oversee month-end and quarter-end close for all US entities; reduced close cycle from
  8 days to 5 days through standardised journal entry templates and close calendars.
- Business partner to COO for capital allocation decisions: produced investment cases for
  three plant automation programmes (combined capex USD 42M); all three approved by Board.
- Coordinate statutory filings across US federal, 8 state jurisdictions, and Canadian
  provincial tax requirements in partnership with external tax advisers (PwC).

Finance Director -- Apex Precision Components, Detroit, MI, USA (Aug 2013 - May 2018)
Apex is a PE-backed (Carlyle Group) automotive parts manufacturer with USD 340M revenue.

- Directed a 18-person finance team through two full PE investment cycles; prepared
  financial models and data rooms for both the 2014 add-on acquisition (USD 55M target)
  and the 2017 exit process (sold to Cortex at USD 410M EV).
- Implemented standard costing and variance analysis framework across 4 plants; identified
  USD 3.8M in avoidable scrap and rework costs in first 12 months of operation.
- Led the Sarbanes-Oxley readiness assessment ahead of the potential 2016 IPO process
  (ultimately shelved); documented 38 key controls and remediated 11 material weaknesses.
- Managed annual audit with Ernst & Young; first clean opinion on internal controls
  achieved in FY2015 after two years of remediation work.

Senior Finance Manager -- Harmon Industrial Coatings, Columbus, OH, USA (Jan 2009 - Jul 2013)
- Managed plant-level financial reporting for 3 manufacturing sites (combined revenue
  USD 85M); responsible for standard cost rolls, variance reporting, and capital
  expenditure tracking.
- Assisted with annual audit preparation; primary liaison with external audit team during
  fieldwork phases.

EDUCATION
- MBA, Finance — Kellogg School of Management, Northwestern University (2009)
- BComm, Accounting — University of Michigan, Ross School of Business (2006)

CERTIFICATIONS
- CPA (Illinois), licensed since 2008
- CGMA (Chartered Global Management Accountant), 2015

LANGUAGES: English (native), Mandarin (intermediate reading, limited spoken)
""".strip()

DAVID_CHEN_BIG_FIVE = BigFiveScores(
    O=0.38,  # Low — conventional, prefers proven frameworks over novel approaches
    C=0.88,  # Very high — rigorous process discipline; strong controls orientation
    E=0.42,  # Below medium — measured communicator; less comfortable with public IR
    A=0.72,  # High — collaborative, consensus-building; strong team relationships
    N=0.30,  # Low-medium — generally stable but some stress during high-complexity cycles
)

CANDIDATE_DAVID = CandidateData(
    name="David Chen",
    cv_text=DAVID_CHEN_CV_TEXT,
    big_five=DAVID_CHEN_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Aisha Okonkwo (Stretch / Partial Assessment Mode)
# ---------------------------------------------------------------------------

AISHA_OKONKWO_CV_TEXT: str = """
AISHA OKONKWO ACA
Senior FP&A Manager | High-Growth DTC & E-Commerce | London

PROFESSIONAL SUMMARY

Commercially sharp finance professional with 8 years of experience in direct-to-consumer
and high-growth e-commerce businesses. Built financial planning infrastructure from
scratch at two DTC brands, including a full suite of e-commerce unit economics models
that are now used in board-level performance reviews. Known for translating complex
analytical work into clear business decisions. Looking to step up into a Head of Finance
or VP Finance role where my analytical depth and commercial instincts can be applied
at greater scale.

PROFESSIONAL EXPERIENCE

Senior FP&A Manager -- PureLayer DTC Ltd, London, UK (Feb 2021 - Present)
PureLayer is a high-growth direct-to-consumer skincare and wellness brand with £85M
net revenue, selling primarily via its own website and selected marketplace channels
(Amazon UK, Zalando).

- Lead an FP&A team of 8 (3 FP&A analysts, 2 management accountants, 1 data analyst,
  1 AR specialist, 1 AP specialist); responsible for hiring, performance management,
  and development of the full team.
- Built the company's first structured annual budget process and three-year financial
  plan; previous planning had been ad hoc monthly spreadsheet extrapolations. First
  formal budget cycle (FY2022) completed within 6 weeks.
- Own the unit economics model: contribution margin by channel and SKU, CAC by paid
  acquisition channel (Meta, Google, TikTok, affiliates), 12-month and 36-month LTV
  cohort analysis, return rate by product category, and fulfilment cost per order
  (broken down by carrier, zone, and packaging tier). Model is refreshed weekly and
  used in the weekly trading meeting chaired by the CEO.
- Introduced a 13-week rolling cash flow forecast that reduced peak working capital
  drawdowns on the RCF by £2.1M in the first full year of operation.
- Partnered with logistics and commercial teams to model the contribution margin impact
  of shifting 30% of volume from Royal Mail to DPD; analysis supported a £640K annual
  cost saving decision.
- Manage NetSuite administration and reporting configuration; built 24 custom saved
  searches and 6 dashboards used across the business for daily operational reporting.
- Supported the year-end statutory accounts preparation; liaised with external auditors
  (BDO, not Big 4); no audit adjustments in FY2022 or FY2023.

FP&A Manager -- Kite Sportswear Ltd, London, UK (Sep 2018 - Jan 2021)
Kite Sportswear is an omnichannel sports and outdoor retailer (£140M revenue, 45 stores
plus e-commerce) backed by Permira Growth Opportunities.

- Managed a team of 4 analysts; owned the monthly management accounts, rolling forecast,
  and annual budget process for the e-commerce channel (£48M revenue).
- Built the e-commerce P&L reporting framework from scratch following the acquisition of
  an online-only brand; integrated its Shopify data into the group NetSuite instance.
- Produced the financial sections of quarterly board packs for the Permira investment
  committee; no IR experience in listed-company context.
- Partnered with commercial team on pricing and promotional strategy modelling; analysis
  supporting the introduction of a tiered loyalty programme contributed to a 9% increase
  in repeat purchase rate over 12 months.

Finance Analyst -- Accenture, London (Sep 2016 - Aug 2018)
- Worked within the CFO Advisory practice on two engagements: a cost reduction programme
  for a UK supermarket (£2.1B revenue) and a financial systems implementation for a
  logistics company. Built financial models and contributed to client presentations.

EDUCATION
- ACA, Institute of Chartered Accountants in England and Wales (2016, first time passes)
- BSc Mathematics — University of Bristol (First Class Honours, 2014)

CERTIFICATIONS
- NetSuite SuiteFoundation certified (2022)
- CFA Level 1 candidate (examination booked, March 2026)

LANGUAGES: English (native), Yoruba (native), French (professional working proficiency)
""".strip()

CANDIDATE_AISHA = CandidateData(
    name="Aisha Okonkwo",
    cv_text=AISHA_OKONKWO_CV_TEXT,
    big_five=None,  # Partial assessment mode — no Big Five available
    personality_source=None,
)

# ---------------------------------------------------------------------------
# All candidates
# ---------------------------------------------------------------------------

ALL_CANDIDATES: list[CandidateData] = [CANDIDATE_ELENA, CANDIDATE_DAVID, CANDIDATE_AISHA]

# ---------------------------------------------------------------------------
# Ground truth: (candidate_name, requirement_domain) -> expected_direction
#
# expected_direction values:
#   "exceeds"  — candidate clearly exceeds what the JD asks for in this domain
#   "meets"    — candidate demonstrably meets the requirement
#   "partial"  — candidate has some relevant experience but with meaningful gaps
#   "gap"      — candidate has no credible evidence for this domain
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[tuple[str, str], str] = {
    # --- Elena Vasquez ---
    ("Elena Vasquez", "fp_and_a_depth"): "meets",
    ("Elena Vasquez", "sox_compliance"): "exceeds",  # Led full SOX 302/404 from scratch at AIM-listed co.
    ("Elena Vasquez", "team_leadership_25_to_35"): "meets",  # 28-person team across two locations
    ("Elena Vasquez", "investor_relations_earnings_prep"): "meets",  # Quarterly earnings materials
    ("Elena Vasquez", "erp_sap_netsuite"): "exceeds",  # SAP S/4HANA migration lead + NetSuite; SAP certified
    ("Elena Vasquez", "budget_management_50m_plus"): "meets",  # £38M budget (adjacent to £52M ask)
    ("Elena Vasquez", "audit_management_big4"): "meets",  # Deloitte at Kestrel, EY at Bloom & Basket
    ("Elena Vasquez", "cash_flow_treasury"): "meets",  # 13-week cash model; treasury ownership current role
    ("Elena Vasquez", "multi_entity_multi_currency"): "meets",  # 4 entities, GBP/EUR/PLN
    ("Elena Vasquez", "ecommerce_unit_economics"): "exceeds",  # Weekly CAC/LTV/contribution margin dashboard
    ("Elena Vasquez", "board_presentation_skills"): "meets",  # Quarterly Board + Audit Committee presenter
    ("Elena Vasquez", "cross_functional_influence"): "meets",
    ("Elena Vasquez", "calm_under_pressure_close"): "meets",  # N=0.18; explicit close-cycle ownership
    # --- David Chen ---
    ("David Chen", "fp_and_a_depth"): "meets",  # Driver-based budgeting; manufacturing context
    ("David Chen", "sox_compliance"): "exceeds",  # 6 consecutive clean opinions; 63 documented controls
    ("David Chen", "team_leadership_25_to_35"): "meets",  # 35-person team at Cortex
    ("David Chen", "investor_relations_earnings_prep"): "gap",  # PE-backed/private; no listed IR
    ("David Chen", "erp_sap_netsuite"): "gap",  # No SAP or NetSuite; manufacturing ERP unspecified
    ("David Chen", "budget_management_50m_plus"): "meets",  # USD 58M operating budget at Cortex
    ("David Chen", "audit_management_big4"): "exceeds",  # 6 years KPMG; Audit Committee presenter
    ("David Chen", "cash_flow_treasury"): "partial",  # Cash incidental; no treasury ownership cited
    ("David Chen", "multi_entity_multi_currency"): "partial",  # US/MX/CA only; no EUR/PLN or IFRS
    ("David Chen", "ecommerce_unit_economics"): "gap",  # Manufacturing; no e-commerce KPI evidence
    ("David Chen", "board_presentation_skills"): "partial",  # Audit Cmte only; no investor-facing IR
    ("David Chen", "cross_functional_influence"): "meets",  # COO partner; capital allocation decisions
    ("David Chen", "calm_under_pressure_close"): "meets",  # Close 8->5 days; 6-year audit consistency
    # --- Aisha Okonkwo ---
    ("Aisha Okonkwo", "fp_and_a_depth"): "meets",  # Built FP&A from scratch; strong modelling depth
    ("Aisha Okonkwo", "sox_compliance"): "gap",  # No SOX; BDO (non-Big 4); no internal controls
    ("Aisha Okonkwo", "team_leadership_25_to_35"): "partial",  # Team of 8; well below 25-35 ask
    ("Aisha Okonkwo", "investor_relations_earnings_prep"): "gap",  # Private only; no listed-co IR
    ("Aisha Okonkwo", "erp_sap_netsuite"): "partial",  # NetSuite admin only; no SAP; no migration
    ("Aisha Okonkwo", "budget_management_50m_plus"): "partial",  # No stated budget >£10M owned
    ("Aisha Okonkwo", "audit_management_big4"): "gap",  # BDO only; no Big 4 relationship managed
    ("Aisha Okonkwo", "cash_flow_treasury"): "partial",  # 13-week cash; no treasury ownership
    ("Aisha Okonkwo", "multi_entity_multi_currency"): "gap",  # Single entity, GBP-only businesses
    ("Aisha Okonkwo", "ecommerce_unit_economics"): "exceeds",  # Weekly CAC/LTV/fulfilment model
    ("Aisha Okonkwo", "board_presentation_skills"): "partial",  # Permira packs; no listed-co Board
    ("Aisha Okonkwo", "cross_functional_influence"): "meets",  # Logistics + commercial partnering
    ("Aisha Okonkwo", "calm_under_pressure_close"): "partial",  # No listed-co close evidence
}

# ---------------------------------------------------------------------------
# Scenario configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG = ScenarioConfig(
    name=ScenarioName.STABILIZATION,
    category_weights={
        # Controls and governance are paramount in a post-IPO stabilisation context
        "compliance": 1.8,
        "execution": 1.5,
        "leadership": 1.3,
        "commercial": 1.0,
        "strategic": 0.8,
    },
)

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "AISHA_OKONKWO_CV_TEXT",
    "ALL_CANDIDATES",
    "CANDIDATE_AISHA",
    "CANDIDATE_DAVID",
    "CANDIDATE_ELENA",
    "DAVID_CHEN_BIG_FIVE",
    "DAVID_CHEN_CV_TEXT",
    "ELENA_VASQUEZ_BIG_FIVE",
    "ELENA_VASQUEZ_CV_TEXT",
    "GROUND_TRUTH",
    "JD_TEXT",
    "SCENARIO_CONFIG",
]
