"""Synthetic Head of People / CHRO fixture for PayNova (post-acquisition scenario).

PayNova is a 500-person fintech that has just acquired a 120-person payments startup
(AcquiPay). The acquisition creates a culture-integration crisis: AcquiPay has an
eng-first culture, different comp structures, and different values. Retention risk
is high. This fixture stress-tests the `assessable_from_cv=False` routing path —
approximately half of requirements are behavioral/interpersonal and cannot be inferred
from a CV alone.

Candidates:
- Samantha Park (A): Strong Fit — fintech VP People with 2 prior M&A integrations.
- Robert Njoku (B): Partial Fit — seasoned CHRO but zero acquisition experience,
  traditional manufacturing background.
- Maya Johansson (C): Stretch — startup Head of People, strong culture + DEI,
  no acquisition or multi-jurisdiction experience. NO Big Five (partial mode).
"""

from meridian.models import (
    BigFiveScores,
    CandidateData,
    Confidence,
    Requirement,
    RubricAssessment,
    RubricLevel,
    ScenarioConfig,
    ScenarioName,
    ScenarioPriority,
)

# ---------------------------------------------------------------------------
# JD Text — Head of People / CHRO, PayNova
# 800-1200 words, ~50% behavioral requirements
# ---------------------------------------------------------------------------

JD_TEXT: str = """
PayNova — Head of People / Chief Human Resources Officer (CHRO)

Location: New York, NY (HQ) | Austin, TX | London, UK
Reports to: Chief Executive Officer
Team: HR function of 15-20 professionals across three offices
Compensation: $280,000 – $340,000 base + equity + performance bonus

About PayNova

PayNova is a 500-person fintech company powering real-time payment infrastructure for
mid-market and enterprise clients across North America and Europe. Our platform processes
more than $14 billion in annual transaction volume and serves 1,100 business customers.

In January 2026, PayNova completed the acquisition of AcquiPay — a 120-person payments
startup headquartered in Austin, Texas. AcquiPay brought deep expertise in embedded
finance and developer-first tooling, along with a fierce, independent engineering culture
that is fundamentally different from PayNova's more structured, process-oriented approach.
Compensation structures differ significantly: AcquiPay operated on aggressive startup
equity with below-market base salaries, while PayNova runs a conventional base-heavy
total-rewards model. Voluntary attrition among AcquiPay engineers has already reached
18% in the 60 days since close.

The People function is at the centre of everything that happens next.

The Role

We are seeking a Head of People / CHRO to lead the integration of two organisations
into one — and to build the people infrastructure that will carry PayNova through its
next growth chapter. This is a CEO-level priority and a CEO-level relationship.

This role is not for someone who wants to run a compliance-and-policy HR function. It
is for a people leader who understands that the real work of integration happens in
one-on-one conversations, in how leaders behave on their worst days, and in whether
employees trust that the company is acting in good faith.

Key Responsibilities

- Design and execute the post-acquisition people integration strategy, covering culture,
  compensation harmonisation, org design, benefits alignment, and workforce planning
  across New York, Austin, and London.
- Rebuild trust with AcquiPay employees — conduct structured listening sessions, identify
  at-risk talent, and develop targeted retention packages for engineers and product leaders.
- Coach and challenge PayNova's senior leadership team (SLT) through the cultural
  discomfort of integration, including leaders who are resistant, dismissive of AcquiPay's
  culture, or struggling to manage teams they did not hire.
- Redesign the total-rewards architecture to create a single, equitable compensation
  framework that retains AcquiPay talent without destabilising PayNova's existing salary
  bands — a politically and analytically complex problem.
- Build psychological safety across combined teams, particularly in the Austin office
  where AcquiPay employees feel like a conquered entity rather than valued contributors.
- Lead organisational design work: determine optimal team structures, reporting lines,
  and spans of control as the combined company scales from 620 to a projected 800+
  employees over the next 18 months.
- Manage, develop, and scale the HR team from its current 12 members to 15-20 as
  the company grows, including hiring an HR Business Partner dedicated to the Austin
  office.
- Own and evolve the HRIS platform (currently Workday) and build out people analytics
  capabilities — headcount forecasting, attrition modelling, compensation benchmarking
  — to give the SLT real data for decisions.
- Navigate multi-jurisdiction employment law across New York, Texas, and the United
  Kingdom, including UK employment law, TUPE obligations that may arise from future
  transactions, and US multi-state wage-and-hour compliance.
- Lead DEI strategy and programmes, moving PayNova beyond compliance-driven diversity
  metrics toward genuine inclusion in a combined workforce with different cultural
  starting points.
- Develop and maintain the employer brand to support talent acquisition in a competitive
  fintech labour market, leveraging the combined company's scale and mission.
- Serve as a trusted advisor and sounding board to the CEO and Board on all
  people-related matters, including succession planning for SLT roles.

Required Qualifications

- 10+ years of progressive HR / People leadership experience, with at least 4 years
  as VP People, CPO, or CHRO.
- Direct, hands-on experience leading at least one post-acquisition culture integration
  involving 75+ acquired employees — not participation in a workstream, but ownership
  of the integration outcome.
- Experience building and leading HR teams of 10 or more professionals.
- Demonstrated experience managing comp-and-benefits redesign programmes, specifically
  harmonising compensation structures across organisations with different philosophies.
- Working knowledge of Workday or a comparable enterprise HRIS; ability to build and
  interpret people analytics dashboards.
- Solid grounding in US multi-state employment law and UK employment law; ability to
  partner effectively with employment counsel across jurisdictions.
- Experience operating in high-growth technology or fintech environments where change
  velocity is high and processes are still being established.

Behavioral and Leadership Attributes We Are Looking For

The following attributes are not checkboxes on a CV. They describe how this person
operates, and we will probe for them directly in our assessment process.

- Empathy and trust-building: Ability to walk into a room full of sceptical, grieving
  AcquiPay employees and make them feel genuinely heard — not managed. This requires
  emotional intelligence that cannot be faked.
- Navigating political dynamics: Confidence to operate in the middle of a power
  struggle between two merged cultures, remain neutral enough to be trusted by both
  sides, and still get things done.
- Coaching resistant leaders: Ability to work alongside SLT members who openly doubt
  the value of people-ops, who dismiss "culture stuff," or who are used to leading
  through control rather than influence. This person must be able to shift those
  leaders' behaviour without losing the relationship.
- Conflict mediation: Skill in de-escalating and resolving disputes between acquired
  and acquirer teams — at the individual, team, and organisational level — before
  they become attrition or legal events.
- Cultural sensitivity across acquired teams: Deep appreciation for what AcquiPay's
  employees valued about their previous culture and what they fear losing — and the
  ability to honour that while guiding the organisation forward.
- Change management orientation: A genuine belief that how change is communicated
  is as important as the change itself — and a track record of bringing people along
  rather than announcing and moving on.
""".strip()

# ---------------------------------------------------------------------------
# Requirements — 13 requirements, ~6 behavioral (assessable_from_cv=False)
# ---------------------------------------------------------------------------

REQUIREMENTS: list[Requirement] = [
    # CV-assessable requirements
    Requirement(
        requirement_id="REQ-01",
        text="10+ years HR/People leadership, min 4 years at VP/CPO/CHRO level",
        source_quote="10+ years of progressive HR / People leadership experience, with at least 4 years as VP People, CPO, or CHRO.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation="medium",
            post_acquisition="high",
            turnaround="high",
            stabilization="medium",
            growth="medium",
        ),
    ),
    Requirement(
        requirement_id="REQ-02",
        text="Hands-on ownership of at least one post-acquisition culture integration (75+ acquired employees)",
        source_quote="Direct, hands-on experience leading at least one post-acquisition culture integration involving 75+ acquired employees — not participation in a workstream, but ownership of the integration outcome.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation="low",
            post_acquisition="high",
            turnaround="medium",
            stabilization="low",
            growth="low",
        ),
    ),
    Requirement(
        requirement_id="REQ-03",
        text="Built and led HR teams of 10+ professionals",
        source_quote="Experience building and leading HR teams of 10 or more professionals.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation="medium",
            post_acquisition="high",
            turnaround="medium",
            stabilization="medium",
            growth="high",
        ),
    ),
    Requirement(
        requirement_id="REQ-04",
        text="Managed comp-and-benefits redesign programmes harmonising compensation across organisations with different philosophies",
        source_quote="Demonstrated experience managing comp-and-benefits redesign programmes, specifically harmonising compensation structures across organisations with different philosophies.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation="low",
            post_acquisition="high",
            turnaround="medium",
            stabilization="medium",
            growth="low",
        ),
    ),
    Requirement(
        requirement_id="REQ-05",
        text="Working knowledge of Workday or comparable enterprise HRIS; builds and interprets people analytics dashboards",
        source_quote="Working knowledge of Workday or a comparable enterprise HRIS; ability to build and interpret people analytics dashboards.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation="high",
            post_acquisition="medium",
            turnaround="low",
            stabilization="medium",
            growth="medium",
        ),
    ),
    Requirement(
        requirement_id="REQ-06",
        text="Solid grounding in US multi-state employment law and UK employment law",
        source_quote="Solid grounding in US multi-state employment law and UK employment law; ability to partner effectively with employment counsel across jurisdictions.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation="low",
            post_acquisition="medium",
            turnaround="medium",
            stabilization="high",
            growth="medium",
        ),
    ),
    Requirement(
        requirement_id="REQ-07",
        text="Experience in high-growth technology or fintech environments with high change velocity",
        source_quote="Experience operating in high-growth technology or fintech environments where change velocity is high and processes are still being established.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation="high",
            post_acquisition="medium",
            turnaround="medium",
            stabilization="low",
            growth="high",
        ),
    ),
    # Behavioral requirements (assessable_from_cv=False)
    Requirement(
        requirement_id="REQ-08",
        text="Empathy and trust-building with sceptical acquired-company employees",
        source_quote="Ability to walk into a room full of sceptical, grieving AcquiPay employees and make them feel genuinely heard — not managed.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation="low",
            post_acquisition="high",
            turnaround="medium",
            stabilization="medium",
            growth="low",
        ),
    ),
    Requirement(
        requirement_id="REQ-09",
        text="Navigating political dynamics between merged cultures while remaining trusted by both sides",
        source_quote="Confidence to operate in the middle of a power struggle between two merged cultures, remain neutral enough to be trusted by both sides, and still get things done.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation="low",
            post_acquisition="high",
            turnaround="high",
            stabilization="medium",
            growth="low",
        ),
    ),
    Requirement(
        requirement_id="REQ-10",
        text="Coaching SLT members who are resistant to people-ops or lead through control rather than influence",
        source_quote="Ability to work alongside SLT members who openly doubt the value of people-ops, who dismiss 'culture stuff,' or who are used to leading through control rather than influence.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation="medium",
            post_acquisition="high",
            turnaround="high",
            stabilization="medium",
            growth="medium",
        ),
    ),
    Requirement(
        requirement_id="REQ-11",
        text="Conflict mediation between acquired and acquirer teams before disputes become attrition or legal events",
        source_quote="Skill in de-escalating and resolving disputes between acquired and acquirer teams — at the individual, team, and organisational level — before they become attrition or legal events.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation="low",
            post_acquisition="high",
            turnaround="medium",
            stabilization="medium",
            growth="low",
        ),
    ),
    Requirement(
        requirement_id="REQ-12",
        text="Cultural sensitivity for what acquired-team employees valued and feared losing",
        source_quote="Deep appreciation for what AcquiPay's employees valued about their previous culture and what they fear losing — and the ability to honour that while guiding the organisation forward.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation="low",
            post_acquisition="high",
            turnaround="medium",
            stabilization="medium",
            growth="low",
        ),
    ),
    Requirement(
        requirement_id="REQ-13",
        text="Change management orientation: communicates change in ways that bring people along rather than announces and moves on",
        source_quote="A genuine belief that how change is communicated is as important as the change itself — and a track record of bringing people along rather than announcing and moving on.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation="high",
            post_acquisition="high",
            turnaround="high",
            stabilization="medium",
            growth="medium",
        ),
    ),
]

# ---------------------------------------------------------------------------
# Candidate A — Samantha Park (Strong Fit)
# ---------------------------------------------------------------------------

SAMANTHA_PARK_CV_TEXT: str = """
SAMANTHA PARK
Head of People | VP People | Fintech & High-Growth Technology

New York, NY | samanthapark.work@email.com | LinkedIn: /in/samanthapark

PROFESSIONAL EXPERIENCE

VP People, Remora Financial — New York, NY (April 2021 – Present)
Remora is a 400-person B2B payments and embedded finance company serving 600+
enterprise clients with $9.2B in annual payment volume.

- Built and lead a People team of 18 (up from 3 when I joined) across New York,
  San Francisco, and Dublin, spanning HRBPs, talent acquisition, L&D, total rewards,
  and people analytics.
- Led full culture and people integration for two acquisitions: Parsec Payments
  (80-person Austin-based startup, closed Q3 2022) and Kestrel Analytics (150-person
  London-based data company, closed Q1 2024). Both integrations completed on schedule
  with first-year attrition below 12% against a 22% industry benchmark.
- For the Parsec integration: designed and executed a compensation harmonisation
  programme that merged Parsec's equity-heavy, sub-market-base structure into
  Remora's total-rewards framework. Retained 87% of Parsec engineering staff through
  12 months post-close; conducted 140+ individual stay conversations.
- For the Kestrel integration: navigated UK TUPE implications, restructured London
  benefits (private medical, pension, holiday entitlement) to align with US package
  equivalents, and established a dedicated UK HR Business Partner.
- Implemented Workday HCM and Workday Peakon in 2022; built a real-time people
  analytics dashboard tracking attrition probability, headcount vs. plan, and
  compensation equity by level, function, and gender.
- Partnered with the CEO and CFO to redesign the performance and compensation
  architecture in 2023: moved from a static annual review to a continuous-feedback
  model tied to quarterly OKRs, increasing employee satisfaction scores from 62% to
  79% favourable on the annual engagement survey.
- Launched DEI roadmap in 2022: raised underrepresented minority representation
  in senior roles from 14% to 26% over 3 years; introduced structured interview
  panels, blind CV screening, and semi-annual pay equity audits.
- Developed and own the employer brand strategy; Remora was named to the Crain's
  New York Business Fast 50 Best Places to Work list in 2023 and 2024.

Senior HR Business Partner, Braintree / PayPal — New York, NY (2017 – 2021)
- Served as HRBP to PayPal's North America Merchant Solutions division (650
  employees); supported two reorgs and one product-line divestiture.
- Coached 14 directors and VPs through leadership development programmes;
  three were promoted to SVP level within 24 months.
- Managed multi-state compliance across NY, NJ, CT, TX, CA, and FL; partnered
  with employment counsel on FLSA classification review affecting 320 contractor
  relationships.

HR Manager, Stripe — San Francisco, CA (2014 – 2017)
- Early People team hire (employee #7 in People function); helped scale company
  from 200 to 750 employees.
- Built Stripe's first structured onboarding programme and manager training
  curriculum; reduced 90-day involuntary attrition from 18% to 6%.
- Supported international expansion into UK and Ireland: established employment
  contracts, statutory benefits, and HMRC payroll compliance.

EDUCATION
- MBA, Cornell University SC Johnson College of Business (2014)
- BA, Psychology, Columbia University (2011)

CERTIFICATIONS
- SHRM-SCP (Senior Certified Professional), 2019
- Workday HCM Certified (Core HCM + Reporting), 2022

BOARD & ADVISORY
- People Advisory Board Member, Fintech for America Coalition, 2023-present
- Mentor, First Round Capital "People School" programme for HR leaders at portfolio
  companies; supported 5 VP People hires across Series A-B companies in 2023.

NOTABLE TALKS & PUBLICATIONS
- Speaker, HR Transform 2024 (Las Vegas): "Culture Integration Playbook — What Actually
  Works in the First 90 Days After Acquisition Close"
- Speaker, Workday Rising 2023: "Building Real-Time Attrition Prediction with Peakon Data"
- Quoted in Bloomberg Law article on equity-heavy startup comp harmonisation (August 2023)

LANGUAGES: English (native), Korean (conversational)
""".strip()

SAMANTHA_PARK_BIG_FIVE: BigFiveScores = BigFiveScores(
    O=0.68,  # Moderately high — adaptive to new contexts, open to unconventional solutions
    C=0.75,  # High — structured execution, detail-oriented on people processes
    E=0.72,  # High — warm and present in group settings, builds rapport quickly
    A=0.82,  # Very high — genuinely empathetic, earns trust across hierarchies
    N=0.20,  # Low — calm in high-stakes integration moments, steady under pressure
)

CANDIDATE_SAMANTHA: CandidateData = CandidateData(
    name="Samantha Park",
    cv_text=SAMANTHA_PARK_CV_TEXT,
    big_five=SAMANTHA_PARK_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — Robert Njoku (Partial Fit)
# ---------------------------------------------------------------------------

ROBERT_NJOKU_CV_TEXT: str = """
ROBERT NJOKU, SHRM-SCP | SPHR
Chief Human Resources Officer

Chicago, IL | robertnjoku@email.com | LinkedIn: /in/robertnjoku-chro

PROFESSIONAL EXPERIENCE

Chief Human Resources Officer, Hartwell Industrial Group — Chicago, IL (2018 – Present)
Hartwell is a 2,100-person specialty manufacturing and distribution company with
operations in 14 US states and a 380-person UK subsidiary (Hartwell UK Ltd).

- Report directly to the CEO and sit on the Executive Leadership Team; oversee an
  HR function of 22 professionals across US and UK operations.
- Own total rewards, talent acquisition, HRIS, compliance, L&D, employee relations,
  and UK HR operations.
- Redesigned the US compensation structure in 2020: moved from a legacy pay-grade
  system to a market-referenced job architecture covering 85 job families across 6
  career levels. Achieved 94% pay-equity pass rate on annual third-party audit.
- Deep expertise in US federal and multi-state employment law: FMLA, ADA, Title VII,
  FLSA, WARN Act administration, and wage-and-hour compliance across NY, IL, CA, TX,
  WA, and FL. Managed 3 EEOC charges and 2 DOL wage-and-hour investigations to
  resolution without litigation.
- Oversaw UK HR operations through Hartwell UK Ltd; managed 4 TUPE transfers
  (business acquisitions by Hartwell UK of small regional distributors) with full
  statutory compliance; worked closely with UK employment solicitors throughout.
  Restructured UK pension scheme from a defined-benefit liability into a defined-
  contribution arrangement in 2021.
- Led deployment of SAP SuccessFactors across all US and UK locations (2019-2020);
  currently evaluating migration to Workday for 2027 fiscal year.
- Designed and delivered Hartwell's first formal Management Development Programme
  (MDP): 120 managers completed the 6-month blended programme; 360-degree feedback
  scores improved by an average of 1.4 points (5-point scale) at programme completion.
- Reduced voluntary attrition from 24% (2018 baseline) to 16% (2024 actuals) through
  stay-interview programmes, competitive market adjustments, and improved internal
  mobility processes.
- Established Hartwell's first formal DEI Council in 2022; published first
  Diversity & Inclusion Report in 2023, covering workforce demographics, pay equity,
  and inclusion survey results.

VP Human Resources, Midland Fabricators Inc. — Detroit, MI (2012 – 2018)
- Led HR function of 9 for a 780-person precision-parts manufacturer; oversaw
  3 union contracts (UAW and IBEW) and managed 2 CBA renegotiations.
- Implemented Oracle HRMS; migrated payroll from ADP legacy platform.
- Redesigned benefits programme: reduced per-employee benefits cost by 11% while
  maintaining employee satisfaction scores above 70% favourable.

HR Business Partner / HR Manager — Ford Motor Company, Dearborn, MI (2006 – 2012)
- Supported manufacturing and engineering divisions totalling 4,500 employees; managed
  two plant-level restructuring events affecting 380 hourly workers.
- Led HR due diligence workstream for two small acquisitions (30 and 55 employees)
  as part of the M&A support team — did not own integration delivery.

EDUCATION
- MS, Human Resources Management, Michigan State University (2006)
- BS, Business Administration, University of Michigan (2004)

CERTIFICATIONS
- SPHR (Senior Professional in Human Resources), 2010
- SHRM-SCP (Senior Certified Professional), 2015

BOARD MEMBERSHIPS & PROFESSIONAL INVOLVEMENT
- Board Member, HR Policy Association (Manufacturing Sector Council), 2021-present
- Instructor, SHRM eLearning Faculty, "Multi-State Compliance in US Manufacturing", 2020
- Member, CIPD (Chartered Institute of Personnel and Development), UK chapter, 2019-present
  — maintains active UK HR network relevant to ongoing Hartwell UK operations

SELECTED ACHIEVEMENTS
- Managed Hartwell through 2 government audits (OFCCP compliance review, 2020;
  OSHA recordkeeping audit, 2022) with zero findings and no corrective action required.
- Reduced HR function operating cost by 9% in FY2023 through HRIS optimisation and
  restructuring of talent acquisition vendor arrangements, while maintaining service
  levels across all business units.

LANGUAGES: English (native), Igbo (conversational)
""".strip()

ROBERT_NJOKU_BIG_FIVE: BigFiveScores = BigFiveScores(
    O=0.35,  # Low — conventional, process-adherent; limited appetite for culture experiments
    C=0.90,  # Very high — meticulous compliance and process orientation
    E=0.50,  # Medium — competent in structured settings, less comfortable in ambiguous ones
    A=0.68,  # Moderately high — professional empathy, not the warmest presence in conflict
    N=0.32,  # Low-medium — generally composed, some stress under high-velocity change
)

CANDIDATE_ROBERT: CandidateData = CandidateData(
    name="Robert Njoku",
    cv_text=ROBERT_NJOKU_CV_TEXT,
    big_five=ROBERT_NJOKU_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Maya Johansson (Stretch — NO Big Five, partial mode)
# ---------------------------------------------------------------------------

MAYA_JOHANSSON_CV_TEXT: str = """
MAYA JOHANSSON
Head of People | Culture Architect | Employer Branding

Brooklyn, NY | mayajohansson@email.com | LinkedIn: /in/mayajohansson-people

PROFESSIONAL EXPERIENCE

Head of People, Finch Labs — New York, NY (August 2022 – Present)
Finch Labs is a 90-person Series A fintech startup building open-banking infrastructure
for US credit unions and community banks.

- Sole People leader from company's 18-person founding phase; built the full People
  function from scratch including onboarding, performance management, compensation
  philosophy, benefits, and compliance.
- Grew the team from 18 to 90 employees over 30 months while maintaining Glassdoor
  rating above 4.5 and scoring 82% favourable on bi-annual engagement survey.
- Designed Finch Labs' total-rewards philosophy and implemented Rippling as the HRIS;
  built manager dashboards tracking headcount, offer-acceptance rates, and 90-day
  retention by team and hiring manager.
- Authored and launched the DEI strategy in Q1 2023: introduced structured hiring
  panels and standardised rubric-based evaluation to reduce affinity bias; increased
  women in technical roles from 17% to 34% over 24 months.
- Nominated for and accepted into the 2024 Built In NYC "Best Places to Work" list
  (companies 50-200 employees) — sole finalist among NYC-based fintech startups in
  the category.
- Designed and facilitate a quarterly "Culture Forum" — a candid, cross-functional
  session where any employee can raise concerns directly with leadership. Credited by
  CEO as a key factor in retaining key engineers during a difficult fundraising period
  (Q3 2023).
- No acquisition, merger, or multi-company integration experience to date.

Senior People Operations Manager, Capsule — New York, NY (2019 – 2022)
Capsule is a digital pharmacy startup that grew from 180 to 320 employees during
my tenure.

- Owned People Ops for the corporate and tech functions (130 employees); managed
  two HRBPs.
- Led the design and rollout of Capsule's first competency framework, used for
  structured performance reviews and promotion decisions.
- Managed New York and New Jersey employment compliance; no multi-state or
  international experience in this role.
- Partnered with the VP People on Capsule's Series C talent strategy, including
  compensation benchmarking and offer calibration for 40+ engineering hires in 6
  months.

People Coordinator → HR Generalist, Betterment — New York, NY (2016 – 2019)
- Generalist responsibilities across onboarding, offboarding, benefits administration,
  and employee relations for a 200-person fintech.
- Supported rollout of Lattice performance platform; became internal admin and
  trained 30+ managers on continuous feedback practices.

EDUCATION
- BA, Organizational Behavior, New York University (2016)

CERTIFICATIONS
- SHRM-CP (Certified Professional), 2020
- ICF Associate Certified Coach (ACC), 2023

AWARDS & RECOGNITION
- 2024 Built In NYC Best Places to Work (Finch Labs, 50-200 category)
- 2023 HR Executive Magazine "Up and Coming HR Leader to Watch"

SPEAKING, WRITING & COMMUNITY
- Panelist, People & Culture Summit NYC 2024: "Building Belonging in Founder-Led Companies"
- Contributor, HR Brew newsletter: two-part series on structured hiring rubrics in Series A startups (March 2024)
- Facilitator, Out in Tech mentoring programme: paired with 3 early-career People Ops professionals (2023-present)
- Volunteer instructor, General Assembly NYC: "People Ops Fundamentals for Founders" workshop (quarterly, 2023-present)
- Participant, YC Founders School People & Culture Track (audited, Spring 2024) — built network of 40+ HR peers at seed-stage companies

LANGUAGES: English (native), Swedish (conversational)
""".strip()

CANDIDATE_MAYA: CandidateData = CandidateData(
    name="Maya Johansson",
    cv_text=MAYA_JOHANSSON_CV_TEXT,
    big_five=None,
    personality_source=None,
)

ALL_CANDIDATES: list[CandidateData] = [CANDIDATE_SAMANTHA, CANDIDATE_ROBERT, CANDIDATE_MAYA]

# ---------------------------------------------------------------------------
# Ground Truth — Expected rubric assessments per candidate per requirement
#
# Behavioral requirements (REQ-08 through REQ-13) receive RubricLevel.NOT_ASSESSABLE
# for all candidates in ground truth — the LLM should route these correctly.
# CV-assessable requirements receive substantive levels.
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, dict[str, RubricLevel]] = {
    # Format: {requirement_id: {candidate_name: expected_rubric_level}}
    "REQ-01": {
        # 10+ years HR, 4+ years VP/CPO/CHRO
        "Samantha Park": RubricLevel.EXCEEDS,   # 13 years, VP People since 2021
        "Robert Njoku": RubricLevel.EXCEEDS,    # 20 years, CHRO since 2018
        "Maya Johansson": RubricLevel.PARTIAL,  # 9 years total, Head of People at Series A — not VP/CHRO
    },
    "REQ-02": {
        # Hands-on ownership of post-acquisition integration (75+ employees)
        "Samantha Park": RubricLevel.EXCEEDS,   # 2 integrations: 80-person + 150-person, ownership confirmed
        "Robert Njoku": RubricLevel.PARTIAL,    # M&A support workstream at Ford, did not own delivery
        "Maya Johansson": RubricLevel.GAP,      # Explicitly states no acquisition experience
    },
    "REQ-03": {
        # Built and led HR teams of 10+
        "Samantha Park": RubricLevel.EXCEEDS,   # Built team 3→18
        "Robert Njoku": RubricLevel.MEETS,      # Led team of 22 at Hartwell, 9 at Midland
        "Maya Johansson": RubricLevel.PARTIAL,  # Managed 2 HRBPs at Capsule; sole People leader at Finch (90-person)
    },
    "REQ-04": {
        # Comp-and-benefits harmonisation across orgs with different philosophies
        "Samantha Park": RubricLevel.EXCEEDS,   # Parsec integration: merged equity-heavy startup comp into Remora framework
        "Robert Njoku": RubricLevel.PARTIAL,    # Redesigned Hartwell comp structure (internal only, not cross-company harmonisation)
        "Maya Johansson": RubricLevel.GAP,      # Built comp philosophy from scratch at single org; no cross-org harmonisation
    },
    "REQ-05": {
        # Workday or comparable HRIS; people analytics dashboards
        "Samantha Park": RubricLevel.EXCEEDS,   # Workday HCM + Peakon certified; built real-time analytics dashboard
        "Robert Njoku": RubricLevel.MEETS,      # SAP SuccessFactors deployed; evaluating Workday but not certified
        "Maya Johansson": RubricLevel.PARTIAL,  # Rippling (not enterprise-grade); built basic manager dashboards
    },
    "REQ-06": {
        # US multi-state + UK employment law
        "Samantha Park": RubricLevel.MEETS,     # Multi-state US (6 states) + UK TUPE at Kestrel; solid but not deep compliance specialist
        "Robert Njoku": RubricLevel.EXCEEDS,    # Deep US multi-state (14 states), 3 EEOC + 2 DOL resolutions, UK TUPE ×4
        "Maya Johansson": RubricLevel.GAP,      # NY and NJ only; explicitly no multi-state or international experience
    },
    "REQ-07": {
        # High-growth tech/fintech environment
        "Samantha Park": RubricLevel.EXCEEDS,   # Stripe (200→750), Remora (payments fintech, high-growth)
        "Robert Njoku": RubricLevel.PARTIAL,    # Manufacturing background; Hartwell is stable, not high-growth
        "Maya Johansson": RubricLevel.EXCEEDS,  # Finch Labs Series A, Capsule Series C — native startup environment
    },
    # Behavioral requirements — not assessable from CV for any candidate
    "REQ-08": {
        "Samantha Park": RubricLevel.NOT_ASSESSABLE,
        "Robert Njoku": RubricLevel.NOT_ASSESSABLE,
        "Maya Johansson": RubricLevel.NOT_ASSESSABLE,
    },
    "REQ-09": {
        "Samantha Park": RubricLevel.NOT_ASSESSABLE,
        "Robert Njoku": RubricLevel.NOT_ASSESSABLE,
        "Maya Johansson": RubricLevel.NOT_ASSESSABLE,
    },
    "REQ-10": {
        "Samantha Park": RubricLevel.NOT_ASSESSABLE,
        "Robert Njoku": RubricLevel.NOT_ASSESSABLE,
        "Maya Johansson": RubricLevel.NOT_ASSESSABLE,
    },
    "REQ-11": {
        "Samantha Park": RubricLevel.NOT_ASSESSABLE,
        "Robert Njoku": RubricLevel.NOT_ASSESSABLE,
        "Maya Johansson": RubricLevel.NOT_ASSESSABLE,
    },
    "REQ-12": {
        "Samantha Park": RubricLevel.NOT_ASSESSABLE,
        "Robert Njoku": RubricLevel.NOT_ASSESSABLE,
        "Maya Johansson": RubricLevel.NOT_ASSESSABLE,
    },
    "REQ-13": {
        "Samantha Park": RubricLevel.NOT_ASSESSABLE,
        "Robert Njoku": RubricLevel.NOT_ASSESSABLE,
        "Maya Johansson": RubricLevel.NOT_ASSESSABLE,
    },
}

# ---------------------------------------------------------------------------
# Expected rubric assessments (ground truth as RubricAssessment objects)
# Only CV-assessable requirements are included; behavioral requirements are omitted
# since the correct output is NOT_ASSESSABLE, which bypasses the rubric assessor.
# ---------------------------------------------------------------------------

EXPECTED_RUBRIC_ASSESSMENTS: list[RubricAssessment] = [
    # REQ-01
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Samantha Park",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="13 years HR/People, VP People since April 2021",
        cv_location="VP People, Remora Financial",
        notes="13 total years; VP-level since 2021. Comfortably exceeds the 10-year / 4-year VP threshold.",
    ),
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Robert Njoku",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="CHRO since 2018; prior VP HR from 2012",
        cv_location="CHRO, Hartwell Industrial Group",
        notes="20 years total HR experience; CHRO since 2018, VP HR from 2012-2018.",
    ),
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Maya Johansson",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Head of People at 90-person Series A; prior Senior People Ops Manager",
        cv_location="Head of People, Finch Labs",
        notes="9 years total experience; title is Head of People at a 90-person startup, not VP/CPO/CHRO at scale.",
        investigation_question="Has Maya held any VP or C-level People title at a company of 200+ employees?",
    ),
    # REQ-02
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Samantha Park",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Led full culture and people integration for two acquisitions: Parsec Payments (80-person) and Kestrel Analytics (150-person)",
        cv_location="VP People, Remora Financial",
        notes="Two acquisitions with full ownership of integration outcome; attrition below 12% vs 22% benchmark.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Robert Njoku",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Led HR due diligence workstream for two small acquisitions (30 and 55 employees) — did not own integration delivery",
        cv_location="HR Business Partner, Ford Motor Company",
        notes="CV explicitly states workstream participation, not ownership. TUPE transfers at Hartwell UK are business asset acquisitions by Hartwell, not culture integrations of incoming talent populations.",
        investigation_question="Has Robert ever owned the people-integration outcome for an acquisition where the acquired employees were joining as a cultural unit, not just assets?",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Maya Johansson",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="No acquisition, merger, or multi-company integration experience to date.",
        cv_location="Head of People, Finch Labs",
        notes="Candidate self-discloses the gap explicitly.",
    ),
    # REQ-03
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Samantha Park",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Built People team of 18 (up from 3 when I joined)",
        cv_location="VP People, Remora Financial",
        notes="Built team from 3 to 18 across three offices.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Robert Njoku",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="oversee an HR function of 22 professionals across US and UK operations",
        cv_location="CHRO, Hartwell Industrial Group",
        notes="Currently leads 22-person HR function. Meets requirement comfortably.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Maya Johansson",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="managed two HRBPs [at Capsule]; sole People leader [at Finch Labs]",
        cv_location="Senior People Operations Manager, Capsule",
        notes="Largest formal team managed is 2 HRBPs. At Finch Labs she is a solo practitioner. Below the 10+ threshold.",
        investigation_question="Has Maya ever managed more than 2-3 direct reports on a People team?",
    ),
    # REQ-04
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Samantha Park",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="designed and executed a compensation harmonisation programme that merged Parsec's equity-heavy, sub-market-base structure into Remora's total-rewards framework",
        cv_location="VP People, Remora Financial",
        notes="Exact scenario: equity-heavy startup comp merged into conventional base-heavy framework. 87% retention.",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Robert Njoku",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Redesigned the US compensation structure in 2020: moved from a legacy pay-grade system to a market-referenced job architecture",
        cv_location="CHRO, Hartwell Industrial Group",
        notes="Strong internal comp redesign experience but within a single organisation, not across companies with different comp philosophies post-acquisition.",
        investigation_question="Has Robert led a comp harmonisation that required bridging two companies with fundamentally different total-rewards philosophies — e.g. startup equity vs corporate base?",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Maya Johansson",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="Designed Finch Labs' total-rewards philosophy",
        cv_location="Head of People, Finch Labs",
        notes="Built comp from scratch at a single small company. No evidence of cross-company harmonisation.",
    ),
    # REQ-05
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Samantha Park",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Implemented Workday HCM and Workday Peakon in 2022; built a real-time people analytics dashboard",
        cv_location="VP People, Remora Financial",
        notes="Workday HCM certified. Built analytics dashboard covering attrition probability, headcount vs plan, compensation equity.",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Robert Njoku",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="Led deployment of SAP SuccessFactors across all US and UK locations (2019-2020); currently evaluating migration to Workday",
        cv_location="CHRO, Hartwell Industrial Group",
        notes="Enterprise HRIS experience (SuccessFactors) but no Workday certification and no mention of analytics dashboard builds.",
        investigation_question="Can Robert build and own people analytics reporting, or does he rely on HRIS vendors / analysts to surface data?",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Maya Johansson",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="implemented Rippling as the HRIS; built manager dashboards",
        cv_location="Head of People, Finch Labs",
        notes="Rippling is an SMB-scale HRIS, not enterprise-grade. Dashboard experience is present but at limited scope and scale.",
        investigation_question="Has Maya worked with Workday or an enterprise HRIS at scale? Can she own Workday administration and reporting at a 600+ person company?",
    ),
    # REQ-06
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Samantha Park",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="Managed multi-state compliance across NY, NJ, CT, TX, CA, and FL; supported international expansion into UK and Ireland",
        cv_location="Senior HR Business Partner, Braintree / PayPal",
        notes="Multi-state US and UK employment experience. TUPE involvement at Kestrel integration. Solid but she is a practitioner, not a deep compliance specialist.",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Robert Njoku",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Managed 3 EEOC charges and 2 DOL wage-and-hour investigations; 4 TUPE transfers; restructured UK pension scheme",
        cv_location="CHRO, Hartwell Industrial Group",
        notes="Deepest employment law experience in the candidate pool. 14 US states, EEOC/DOL resolution, UK TUPE ×4, pension restructuring.",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Maya Johansson",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="Managed New York and New Jersey employment compliance; no multi-state or international experience in this role",
        cv_location="Senior People Operations Manager, Capsule",
        notes="CV explicitly states absence of multi-state and international experience.",
    ),
    # REQ-07
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Samantha Park",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Early People team hire at Stripe; helped scale company from 200 to 750 employees",
        cv_location="HR Manager, Stripe",
        notes="Stripe, Remora Financial — consistently in high-growth fintech/payments environments.",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Robert Njoku",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Hartwell Industrial Group — 2,100-person specialty manufacturing and distribution company",
        cv_location="CHRO, Hartwell Industrial Group",
        notes="20-year career in manufacturing and Ford Motor Company. Stable, process-oriented environments. Not fintech or high-growth tech.",
        investigation_question="How would Robert adapt his approach to a company where processes are still being established and change velocity is 3-4x what he has experienced?",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Maya Johansson",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Finch Labs Series A; Capsule Series C; Betterment",
        cv_location="Head of People, Finch Labs",
        notes="Entire career in high-growth NYC fintech and startup environments. Deeply native to the context.",
    ),
]

# ---------------------------------------------------------------------------
# Scenario Configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG: ScenarioConfig = ScenarioConfig(
    name=ScenarioName.POST_ACQUISITION,
    category_weights={
        "INTEGRATION": 2.0,    # Post-acquisition integration is the dominant concern
        "CULTURAL": 1.8,       # Culture clash and trust-building are critical
        "EXECUTION": 1.4,      # Delivery against integration plan
        "EXPERIENCE_GAP": 1.5, # Gaps in acquisition experience are disqualifying
        "EXPERIENCE_STRENGTH": 1.2,
        "FRICTION": 1.3,       # Political and personality friction in combined org
        "DERAILMENT": 1.6,     # High-risk: attrition already elevated
        "STRATEGIC": 1.0,
        "COMPLEMENT": 0.9,
        "COLLISION": 0.8,
    },
)

# ---------------------------------------------------------------------------
# Module-level export list
# ---------------------------------------------------------------------------

__all__ = [
    "ALL_CANDIDATES",
    "CANDIDATE_MAYA",
    "CANDIDATE_ROBERT",
    "CANDIDATE_SAMANTHA",
    "EXPECTED_RUBRIC_ASSESSMENTS",
    "GROUND_TRUTH",
    "JD_TEXT",
    "MAYA_JOHANSSON_CV_TEXT",
    "REQUIREMENTS",
    "ROBERT_NJOKU_BIG_FIVE",
    "ROBERT_NJOKU_CV_TEXT",
    "SAMANTHA_PARK_BIG_FIVE",
    "SAMANTHA_PARK_CV_TEXT",
    "SCENARIO_CONFIG",
]
