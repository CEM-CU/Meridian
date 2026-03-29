"""VP of Sales — TitanForge scenario fixture.

TitanForge is a PE-backed industrial manufacturing company ($340M revenue,
1,800 employees) expanding from North American dominance (95% of revenue) into
EMEA. The target is 70/30 NA/EMEA within 3 years. The VP of Sales must build
a European sales organisation from scratch, reporting to the CRO.

Scenario: GROWTH

Candidates:
- Marcus Weber: Strong Fit — incumbent EMEA VP at peer industrial company,
  proven EMEA build-out track record, deep manufacturing relationships.
- Linda Okafor-Mills: Partial Fit — strong SaaS sales leader, excellent
  people-builder, no EMEA or manufacturing experience.
- Kenji Watanabe: Stretch — manufacturing domain expertise and APAC expansion
  experience but limited quota ownership and no European presence. Partial mode
  (no Big Five).

Ground truth expectations and scenario config are included for use in
integration tests and Stage C/D validation.
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
    "CANDIDATE_KENJI_WATANABE",
    "CANDIDATE_LINDA_OKAFOR_MILLS",
    "CANDIDATE_MARCUS_WEBER",
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
TitanForge Industries — Vice President of Sales
Location: Chicago, IL (HQ) + Frankfurt, Germany (new EMEA hub)
Reports to: Chief Revenue Officer
Base: $210,000–$240,000 | OTE: $380,000–$440,000 (60/40 base/variable)
Territory: North America (primary) + EMEA (build)

About TitanForge

TitanForge Industries is a leading North American manufacturer of heavy industrial
equipment — hydraulic press systems, large-format CNC machining centres, and
automated material-handling solutions for aerospace, automotive, and energy
customers. Founded in 1987 and headquartered in Chicago, TitanForge generates
$340M in annual revenue across 1,800 employees. In 2023, TitanForge received a
strategic investment from Evercore Capital Partners, marking the company's
transition to PE ownership and the launch of an aggressive international
expansion programme.

Today 95% of TitanForge's revenue comes from North America. We have signed
letters of intent with two Tier 1 German automotive suppliers and a major UK
aerospace OEM, and we are establishing a European sales hub in Frankfurt. The
mandate for the incoming VP of Sales is unambiguous: build the EMEA sales
organisation from zero and grow EMEA contribution from <5% of revenue today to
30% ($102M) within 36 months.

The Opportunity

This is a greenfield EMEA build — not a territory takeover. There is no existing
European sales team to inherit, no installed base to manage, and no playbook to
follow. The VP of Sales will define the EMEA go-to-market structure, hire and
develop a regional sales team, establish channel partnerships, and carry personal
quota alongside building. For candidates who want to architect something from
scratch inside a PE-backed company with full CRO backing and a clear mandate,
this role is the opportunity.

The North American business is healthy ($323M, growing at 8% CAGR), with an
established enterprise sales team of 22 reps and a Salesforce-based RevOps
function. The VP of Sales inherits NA quota ownership as well and will be
expected to sustain NA performance while investing capacity in EMEA.

Key Responsibilities

- Own combined revenue quota of $68M in Year 1, scaling to $95M by Year 3
  (NA retention + EMEA ramp); report directly to the CRO on weekly pipeline
  and monthly forecast.
- Build the EMEA sales organisation from scratch: define org structure, create
  hiring plan, recruit and onboard first 8–12 EMEA sales hires (account
  executives, sales engineers, regional managers) within 18 months.
- Establish EMEA channel and distribution partnerships in priority markets
  (DACH, Nordics, UK/Benelux) — identify, qualify, and sign 4–6 strategic
  resellers or agents in Year 1.
- Lead long-cycle enterprise deals from discovery through close (typical deal
  size $1.2M–$4.5M, sales cycle 9–18 months), including executive-level
  engagement with C-suite and procurement stakeholders at target accounts.
- Define and implement EMEA pricing strategy, working with the CFO and CRO to
  adapt North American list pricing for local market conditions, currency risk,
  import duties, and competitive dynamics.
- Drive Salesforce adoption and pipeline hygiene across both NA and EMEA teams;
  partner with RevOps to build EMEA-specific reporting and forecasting models.
- Represent TitanForge at key European industry events (Hannover Messe, EuroBLECH,
  Formnext) and build the company's brand presence in EMEA markets.
- Coach and develop the broader sales team: run weekly deal reviews, deliver
  structured onboarding for new hires, and establish quota-carrying performance
  management norms.

Required Qualifications

- 12+ years of B2B enterprise sales experience, with at least 6 years in a
  sales leadership role (VP, Regional VP, or equivalent); demonstrated
  progression from individual contributor to team leader to multi-region
  executive.
- Proven ownership of revenue quota of $50M or greater, with a consistent
  track record of 100%+ attainment across at least three consecutive years.
- Direct experience building a sales team from scratch — not inheriting an
  existing team — in a new geography or market segment; must include hiring,
  structuring, and ramping the team independently.
- Demonstrated success entering and developing EMEA markets: establishing
  pipeline, closing enterprise deals, and building partner/channel networks
  in at least two European countries.
- Industry experience in industrial manufacturing, heavy equipment, capital
  equipment, or an adjacent sector (automation, robotics, aerospace/defence
  industrial supply) where capital goods are sold to plant managers, VP
  Operations, and C-suite buyers.
- Hands-on experience managing long sales cycles (minimum 6 months, ideally
  9–18 months) with average deal sizes exceeding $500K; must demonstrate
  pipeline management discipline appropriate for low-volume, high-value selling.
- Advanced Salesforce proficiency: pipeline management, forecasting, custom
  reporting, and experience partnering with RevOps to instrument a sales org.
- Demonstrable executive relationship-building capability: track record of
  opening, developing, and closing deals with C-suite and VP-level economic
  buyers at large industrial customers.
- Cross-cultural selling experience: experience adapting sales process,
  communication style, and negotiation approach across Northern European and
  Anglo-Saxon business cultures.
- Pricing strategy experience for new market entry: has developed or co-developed
  localised pricing models for a product line entering a new geographic market.

Preferred Qualifications

- Fluency in German, French, or another major European language beyond English;
  relationships with DACH or Nordic industrial accounts strongly preferred.
- MBA or equivalent from a recognised institution; formal sales methodology
  training (MEDDIC/MEDDPICC, Miller Heiman, Challenger Sale) preferred.

Behavioural Profile

- Hunter mentality with builder patience: capable of personally sourcing new
  logos and opening markets, while sustaining the multi-year relationship
  investment required in industrial capital equipment selling.
- Cultural adaptability: comfortable shifting between Chicago boardroom culture,
  German engineering-culture selling environments, and Scandinavian consensus
  decision-making processes.
- Coach-first leadership: invests in developing reps as a primary management
  obligation — quota attainment through team capability, not personal heroics.
""".strip()

# ---------------------------------------------------------------------------
# Requirements (as would be extracted by Stage C1)
# ---------------------------------------------------------------------------

REQUIREMENTS: list[Requirement] = [
    Requirement(
        requirement_id="REQ-01",
        text="12+ years B2B enterprise sales experience with 6+ years in sales leadership",
        source_quote="12+ years of B2B enterprise sales experience, with at least 6 years in a sales leadership role (VP, Regional VP, or equivalent)",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-02",
        text="Proven revenue quota ownership of $50M+ with 100%+ attainment over 3+ consecutive years",
        source_quote="Proven ownership of revenue quota of $50M or greater, with a consistent track record of 100%+ attainment across at least three consecutive years",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-03",
        text="Experience building a sales team from scratch in a new geography or market segment",
        source_quote="Direct experience building a sales team from scratch — not inheriting an existing team — in a new geography or market segment",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-04",
        text="Demonstrated EMEA market development: pipeline, enterprise deals, and channel networks in 2+ European countries",
        source_quote="Demonstrated success entering and developing EMEA markets: establishing pipeline, closing enterprise deals, and building partner/channel networks in at least two European countries",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.LOW,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-05",
        text="Industry experience in industrial manufacturing, heavy equipment, or capital equipment",
        source_quote="Industry experience in industrial manufacturing, heavy equipment, capital equipment, or an adjacent sector (automation, robotics, aerospace/defence industrial supply)",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-06",
        text="Long sales cycle management: 6–18 month cycles with $500K+ average deal sizes",
        source_quote="Hands-on experience managing long sales cycles (minimum 6 months, ideally 9–18 months) with average deal sizes exceeding $500K",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-07",
        text="Advanced Salesforce proficiency with RevOps partnership experience",
        source_quote="Advanced Salesforce proficiency: pipeline management, forecasting, custom reporting, and experience partnering with RevOps to instrument a sales org",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.LOW,
            stabilization=Priority.MEDIUM,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-08",
        text="Executive relationship-building: track record closing deals with C-suite buyers at large industrial customers",
        source_quote="Demonstrable executive relationship-building capability: track record of opening, developing, and closing deals with C-suite and VP-level economic buyers",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-09",
        text="Cross-cultural selling experience across Northern European and Anglo-Saxon business cultures",
        source_quote="experience adapting sales process, communication style, and negotiation approach across Northern European and Anglo-Saxon business cultures",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.LOW,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-10",
        text="Pricing strategy experience for new market entry: developing localised pricing models for a new geographic market",
        source_quote="has developed or co-developed localised pricing models for a product line entering a new geographic market",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-11",
        text="Fluency in German or another major European language with DACH or Nordic industrial relationships",
        source_quote="Fluency in German, French, or another major European language beyond English; relationships with DACH or Nordic industrial accounts strongly preferred",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.LOW,
            turnaround=Priority.LOW,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-12",
        text="Hunter mentality: capable of personally sourcing new logos and opening new markets",
        source_quote="capable of personally sourcing new logos and opening markets, while sustaining the multi-year relationship investment required in industrial capital equipment selling",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-13",
        text="Cultural adaptability: comfortable operating across Chicago boardroom, German engineering, and Scandinavian consensus environments",
        source_quote="comfortable shifting between Chicago boardroom culture, German engineering-culture selling environments, and Scandinavian consensus decision-making processes",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.LOW,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-14",
        text="Coach-first leadership: develops reps as primary management obligation, not personal quota heroics",
        source_quote="invests in developing reps as a primary management obligation — quota attainment through team capability, not personal heroics",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
]

# ---------------------------------------------------------------------------
# Candidate A — Marcus Weber (Strong Fit)
# ---------------------------------------------------------------------------

MARCUS_WEBER_CV_TEXT: str = """
MARCUS WEBER
VP Sales — Industrial Automation & Heavy Equipment | EMEA

Chicago, IL | Frankfurt, Germany
m.weber@email.com | +1 312 555 0147

PROFESSIONAL SUMMARY

Bilingual sales executive (German / English) with 16 years driving enterprise B2B
revenue in industrial automation and process equipment. Built the EMEA sales
organisation for Vortex Automation Systems from zero to $45M in 4 years, growing
a pan-European team from 0 to 32. Known for opening C-suite relationships at
plant-operator and Tier 1 automotive accounts in DACH, the Nordics, and the UK.
Consistent quota attainment: 115% average across the last 6 years.

PROFESSIONAL EXPERIENCE

Regional VP Sales — EMEA, Vortex Automation Systems  |  Chicago, IL / Frankfurt  |  2020–Present
Vortex Automation Systems ($500M revenue) manufactures servo-driven automation
platforms and large-format robotic welding cells for automotive, aerospace, and
heavy-industry customers.

- Chartered the EMEA sales function from a blank sheet: wrote the go-to-market
  plan, defined territory segmentation across DACH / Nordics / UK-Benelux, and
  secured CEO sign-off on a 3-year hiring roadmap.
- Grew EMEA revenue from $0 to $45M ARR in 48 months; EMEA now represents 28%
  of total company revenue (from 0% in 2020).
- Built and now lead a team of 32 (12 account executives, 8 sales engineers,
  6 channel managers, 4 inside sales / BDRs, 2 sales ops) across Frankfurt,
  Stockholm, and Birmingham offices.
- Personally closed 11 anchor deals in Year 1 and Year 2 ($1.4M–$6.2M per
  deal) to prove market viability before scaling the team; average EMEA deal
  size is $2.1M, cycle length 11 months.
- Signed 7 strategic distribution partners across DACH (3), Nordics (2), and
  UK/Benelux (2); channel partners now account for 35% of EMEA bookings.
- Implemented MEDDPICC across the EMEA team within 6 months of hire; Salesforce
  pipeline coverage improved from 1.4x to 3.1x in 12 months.
- Combined NA + EMEA quota (Year 3): $62M; attainment: 118%.
- Conducts bi-weekly deal reviews and quarterly coaching clinics; EMEA team
  average attainment: 112% in FY2023, 124% in FY2024.

Director of Sales — North America Industrial, Vortex Automation Systems  |  Chicago, IL  |  2017–2020
- Managed 9-person North American enterprise sales team covering heavy
  manufacturing (steel, automotive, energy) vertical.
- Grew NA industrial segment from $18M to $34M over 3 years; quota: $32M,
  attainment: 106% (2017), 119% (2018), 128% (2019).
- Opened 3 new logo accounts in the US Gulf Coast energy sector (total ACV
  $7.4M) with 14-month average sales cycle.
- Deployed Salesforce Sales Cloud enterprise edition across NA team; worked
  with RevOps to build custom forecasting dashboards reducing forecast
  variance from ±22% to ±8%.

Senior Account Executive — Enterprise, Kellner Industrial Equipment  |  Stuttgart, Germany  |  2014–2017
Kellner manufactures large CNC machining centres ($180M revenue) for aerospace
and automotive OEMs.

- Individual contributor covering DACH and Nordics territory; quota $8M/year.
- FY2014: 107% | FY2015: 131% | FY2016: 122% attainment.
- Closed a $9.8M CNC cell programme with an Airbus Tier 1 supplier in Hamburg —
  company's largest single deal at that time; 16-month sales cycle.
- Built relationships with VP Operations and Head of Manufacturing at 6 BMW
  Group supplier plants across Bavaria and Baden-Württemberg.

Account Executive — Capital Equipment, Bremer Maschinenfabrik  |  Bremen, Germany  |  2009–2014
- Sold hydraulic press systems and tooling to automotive stamping plants across
  Germany and Austria.
- Grew territory revenue from €2.1M to €5.8M over 5 years; consistent 110%+
  attainment.
- Developed relationships with procurement directors and VP Manufacturing at
  Volkswagen Group, Daimler, and ZF Friedrichshafen.

EDUCATION

MBA, Kellogg School of Management, Northwestern University  |  2009
BSc, Industrial Engineering, RWTH Aachen University  |  2006

LANGUAGES

German: Native | English: Fluent (professional) | French: Conversational

CERTIFICATIONS & TRAINING

MEDDPICC Sales Methodology (Force Management, 2021)
Salesforce Certified Administrator (2020)
Miller Heiman Strategic Selling (2016)
""".strip()

MARCUS_WEBER_BIG_FIVE = BigFiveScores(
    O=0.55,   # Medium openness — pragmatic, experience-tested approach over novelty
    C=0.78,   # High conscientiousness — structured, rigorous pipeline discipline
    E=0.85,   # Very high extraversion — energetic prospector, builds relationships at C-suite
    A=0.42,   # Below-average agreeableness — direct, willing to push back on terms
    N=0.20,   # Low neuroticism — calm in long drawn-out deal negotiations
)

CANDIDATE_MARCUS_WEBER = CandidateData(
    name="Marcus Weber",
    cv_text=MARCUS_WEBER_CV_TEXT,
    big_five=MARCUS_WEBER_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — Linda Okafor-Mills (Partial Fit)
# ---------------------------------------------------------------------------

LINDA_OKAFOR_MILLS_CV_TEXT: str = """
LINDA OKAFOR-MILLS
VP Sales | SaaS & Enterprise Software

Austin, TX
l.okafor-mills@email.com | +1 512 555 0293

PROFESSIONAL SUMMARY

Sales leader with 12 years of progressive B2B experience, the last 7 years at
VP level. Scaled a SaaS sales organisation from 15 to 60 quota-carrying reps
while growing ARR from $22M to $80M. Known as a talent developer — 11 direct
reports have been promoted into senior roles during my tenure. Consistent
attainment: 105% average across the last 5 years. Expert in Salesforce-driven
RevOps, MEDDIC methodology, and structured sales coaching.

PROFESSIONAL EXPERIENCE

VP Sales, Axiom Workforce Technologies  |  Austin, TX  |  2019–Present
Axiom provides HR automation and workforce management SaaS to mid-market and
enterprise customers (2,500–25,000 employees) in manufacturing, logistics, and
retail verticals.

- Own $80M ARR quota across 18 account executives and 4 regional managers
  covering US and Canada; FY2022: 101%, FY2023: 108%, FY2024: 107% attainment.
- Scaled sales headcount from 15 to 60 in 4 years: designed 3-tier hiring
  framework, built structured 90-day onboarding curriculum, reduced new-hire
  ramp time from 9 months to 5.5 months.
- Introduced MEDDIC across the team in 2020; average pipeline coverage improved
  from 2.1x to 3.8x; win rate improved from 19% to 28% over 24 months.
- Led Salesforce Migration from legacy CRM (HubSpot) to Salesforce Sales Cloud;
  worked with RevOps to design custom lead-routing, forecasting, and activity
  dashboards; reduced forecast variance to ±6%.
- Developed quarterly coaching framework (deal coaching, call coaching, career
  pathing) that contributed to 11 promotions within the sales org over 5 years.
- Closed 4 anchor enterprise deals personally ($900K–$2.1M ACV) in the
  manufacturing vertical during expansion into that segment (FY2022–FY2023);
  sales cycles of 6–8 months.
- Partnered with Marketing and Product to launch a partner / reseller programme
  targeting HR consultancies; signed 12 US-based reseller agreements in Year 1,
  contributing $3.4M in influenced ARR.

Director of Sales — Mid-Market, Axiom Workforce Technologies  |  Austin, TX  |  2017–2019
- Managed 8 mid-market AEs covering East and Central US; quota $18M ARR.
  FY2017: 103%, FY2018: 112% attainment.
- Rebuilt the mid-market compensation structure to improve alignment between
  quota fairness and territory potential; voluntary rep attrition fell from
  34% to 11% within 18 months.

Senior Account Executive — Enterprise, Salesbridge Inc.  |  Chicago, IL  |  2013–2017
Salesbridge provides sales enablement SaaS to Fortune 1000 companies.

- Enterprise AE covering Fortune 500 accounts in financial services and
  insurance; quota $4.5M ARR.
- FY2013: 98%, FY2014: 118%, FY2015: 109%, FY2016: 104% attainment.
- Opened Nationwide Insurance as a net-new logo ($780K ACV); 9-month sales
  cycle involving VP Sales Ops, CIO, and CFO as economic buyers.

Account Executive, Momentum Software  |  Chicago, IL  |  2012–2013
- SaaS AE in the SMB segment; quota $1.2M ARR; 106% attainment.

EDUCATION

MBA, McCombs School of Business, University of Texas at Austin  |  2012
BA, Communications, Northwestern University  |  2008

LANGUAGES

English: Native

CERTIFICATIONS & TRAINING

MEDDIC Practitioner Certified (Force Management, 2020)
Salesforce Certified Sales Cloud Consultant (2021)
Challenger Sale Certification (CEB, 2018)
""".strip()

LINDA_OKAFOR_MILLS_BIG_FIVE = BigFiveScores(
    O=0.62,   # Moderately high openness — adaptive, open to new methods
    C=0.75,   # High conscientiousness — data-disciplined, methodical
    E=0.90,   # Very high extraversion — energetic, commanding presence, vocal
    A=0.50,   # Medium agreeableness — collaborative but commercially firm
    N=0.15,   # Very low neuroticism — highly resilient, emotionally steady
)

CANDIDATE_LINDA_OKAFOR_MILLS = CandidateData(
    name="Linda Okafor-Mills",
    cv_text=LINDA_OKAFOR_MILLS_CV_TEXT,
    big_five=LINDA_OKAFOR_MILLS_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Kenji Watanabe (Stretch / Partial Mode)
# ---------------------------------------------------------------------------

KENJI_WATANABE_CV_TEXT: str = """
KENJI WATANABE
Director, Business Development | Industrial Machinery & Factory Automation

Tokyo, Japan
k.watanabe@email.com | +81 3 5555 0188

PROFESSIONAL SUMMARY

Business development leader with 9 years in industrial machinery and factory
automation, including successful market-entry execution across Japan, Thailand,
Vietnam, and Indonesia. Strong manufacturing domain fluency — heavy machinery,
press systems, and factory automation equipment — with C-suite relationships
at major Japanese and Southeast Asian OEMs. Led an 8-person BD team to $12M
in annual new-business bookings. No prior EMEA market experience.

PROFESSIONAL EXPERIENCE

Director, Business Development — Southeast Asia, Fujikawa Heavy Industries  |  Tokyo / Bangkok  |  2020–Present
Fujikawa Heavy Industries ($1.8B revenue) manufactures large industrial presses,
metal-forming equipment, and automated material-handling systems.

- Lead an 8-person BD team (5 BD managers, 2 applications engineers, 1 BD
  coordinator) covering Southeast Asia expansion markets.
- Grew annual new-business bookings in SEA from $0 to $12M in 3 years
  (FY2021: $3.1M, FY2022: $7.4M, FY2023: $11.8M, FY2024 run-rate: $12.6M);
  regional target: $20M by FY2026.
- Opened 14 net-new accounts across Thailand (5), Vietnam (4), Indonesia (3),
  and Malaysia (2), all in automotive stamping and electronics housing
  manufacturing.
- Closed anchor deal with a Thai Tier 1 automotive stamping plant (Toyota
  supply chain): $3.6M hydraulic press line, 14-month sales cycle; engaged
  VP Manufacturing, Plant Director, and CFO as economic buyers.
- Built and signed 3 regional distributor agreements (Bangkok, Ho Chi Minh
  City, Jakarta); distributors now account for 40% of SEA bookings.
- Drove localised pricing strategy for SEA markets: adjusted list prices for
  import tariffs (10–15%), FX volatility (JPY/THB), and competitive pressure
  from local Chinese press manufacturers; maintained 38% gross margin target.
- Partnered with Fujikawa's service division to bundle after-sales maintenance
  contracts into capital equipment deals, improving deal economics by $180K
  average per transaction.

Senior Business Development Manager, Fujikawa Heavy Industries  |  Tokyo  |  2018–2020
- BD manager covering Japan domestic accounts in automotive and aerospace.
- Personal quota: ¥800M (~$7.2M); FY2018: 104%, FY2019: 97% attainment.
- Developed relationships with VP Manufacturing and Director of Procurement
  at Honda, Subaru, and Kawasaki Aerospace.
- Managed a 12-month competitive tender at Subaru's Gunma stamping plant
  ($2.9M press system); Fujikawa won on total cost of ownership.

Business Development Representative, Nissei Industry  |  Osaka, Japan  |  2015–2018
Nissei manufactures injection-moulding machines and industrial robots for
the automotive and consumer electronics industries ($420M revenue).

- BDR then junior BD manager in Japan domestic market; quota JPY ¥240M in
  final year (~$2.2M); 108% attainment (FY2018).
- Supported senior managers on enterprise deal cycles of 8–15 months with
  Toyota Group, Panasonic, and Sharp.

EDUCATION

MBA, Hitotsubashi University, Graduate School of International Corporate Strategy  |  2015
BEng, Mechanical Engineering, Osaka University  |  2012

LANGUAGES

Japanese: Native | English: Business fluent | Mandarin: Fluent

ADDITIONAL

Presented at Japan Society for Technology of Plasticity (JSTP) on hydraulic
press precision tolerances in lightweight EV body-panel stamping (2022).
Completed Fujikawa internal leadership programme (2021).
""".strip()

CANDIDATE_KENJI_WATANABE = CandidateData(
    name="Kenji Watanabe",
    cv_text=KENJI_WATANABE_CV_TEXT,
    big_five=None,
    personality_source=None,
)

# ---------------------------------------------------------------------------
# All candidates (ordered: strong fit → partial fit → stretch)
# ---------------------------------------------------------------------------

ALL_CANDIDATES: list[CandidateData] = [
    CANDIDATE_MARCUS_WEBER,
    CANDIDATE_LINDA_OKAFOR_MILLS,
    CANDIDATE_KENJI_WATANABE,
]

# ---------------------------------------------------------------------------
# Rubric assessments (as would be produced by Stage C3)
# Each cell: one requirement × one candidate
# ---------------------------------------------------------------------------

RUBRIC_ASSESSMENTS: list[RubricAssessment] = [
    # ---- REQ-01: 12+ years B2B enterprise sales, 6+ years leadership ----
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="16 years B2B sales; Regional VP EMEA since 2020; Director of Sales NA 2017–2020",
        cv_location="Professional Experience — VP Sales EMEA and Director of Sales NA sections",
        notes="16 years total; 7+ years in leadership roles at VP and Director level.",
    ),
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="12 years B2B experience; VP Sales since 2019 (5 years), Director of Sales 2017–2019",
        cv_location="Professional Experience — VP Sales and Director of Sales sections",
        notes="12 years total; 7 years in VP/Director leadership. Meets minimum threshold exactly.",
    ),
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="9 years sales experience; Director BD since 2020; previously Senior BD Manager",
        cv_location="Professional Summary and Experience sections",
        notes="9 years is below 12-year minimum. Director title but BD/pre-sales orientation, not quota-carrying sales leadership at scale.",
        investigation_question="Is Kenji's Director BD role functionally equivalent to a VP Sales role with quota ownership and team P&L accountability?",
    ),
    # ---- REQ-02: $50M+ quota, 100%+ attainment 3+ consecutive years ----
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Combined NA + EMEA quota Year 3: $62M; attainment 118%. NA industrial: quota $32M, attainment 106/119/128%",
        cv_location="Regional VP Sales EMEA and Director of Sales NA sections",
        notes="$62M combined quota at 118% in most recent role; prior 3-year NA run at 106/119/128%.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="$80M ARR quota; FY2022: 101%, FY2023: 108%, FY2024: 107%",
        cv_location="VP Sales, Axiom Workforce Technologies section",
        notes="$80M quota exceeds $50M threshold; 5-year run above 100% with 3 most-recent years documented.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="New-business bookings FY2021: $3.1M, FY2022: $7.4M, FY2023: $11.8M; personal quota ¥800M (~$7.2M) in 2018–2020",
        cv_location="Director BD SEA and Senior BD Manager sections",
        notes="Team bookings grew to $12M but far below $50M threshold. Personal quota ~$7M. Attainment: 104/97% in prior role.",
        investigation_question="Does Kenji carry personal quota ownership separate from team bookings target, and if so what is the dollar value?",
    ),
    # ---- REQ-03: Building sales team from scratch ----
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Chartered the EMEA sales function from a blank sheet… grew team from 0 to 32",
        cv_location="Regional VP Sales EMEA section",
        notes="Direct greenfield build: wrote go-to-market plan, defined territory, recruited 32-person team. Precise match to TitanForge requirement.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Scaled sales headcount from 15 to 60 in 4 years",
        cv_location="VP Sales, Axiom Workforce Technologies section",
        notes="Impressive scaling but started from an existing team of 15, not zero. No evidence of true greenfield org-build.",
        investigation_question="Has Linda ever built a sales team from zero headcount in a market or segment with no prior sales presence?",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Grew annual new-business bookings in SEA from $0 to $12M in 3 years… built and signed 3 regional distributor agreements",
        cv_location="Director BD SEA section",
        notes="Built a new market and a small team (8 people) from scratch in SEA. Scale is limited — 8 headcount vs 12-hire Year 1 target for TitanForge.",
        investigation_question="Did Kenji have full hiring authority and headcount budget ownership for the SEA team, or did Fujikawa HQ retain headcount decisions?",
    ),
    # ---- REQ-04: EMEA market development ----
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Signed 7 strategic distribution partners across DACH (3), Nordics (2), UK/Benelux (2); EMEA revenue $0 to $45M in 48 months",
        cv_location="Regional VP Sales EMEA section",
        notes="Direct EMEA market build across DACH, Nordics, and UK. 7 channel partners signed. Precisely the markets TitanForge is entering.",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="US and Canada coverage throughout career. US-based reseller programme signed 12 US-based reseller agreements.",
        cv_location="All Professional Experience sections",
        notes="Zero EMEA market presence. Career is exclusively US/Canada. No European deal or partnership evidence.",
        investigation_question="Has Linda ever had any responsibility for international markets, even in an indirect or supporting capacity?",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="Southeast Asia expansion: Thailand, Vietnam, Indonesia, Malaysia. Japan domestic previously.",
        cv_location="Director BD SEA and Senior BD Manager sections",
        notes="APAC-only track record. No European market experience, partnerships, or customer relationships.",
        investigation_question="Does Kenji have any exposure to European industrial customers through Fujikawa's global operations or trade events?",
    ),
    # ---- REQ-05: Industrial manufacturing / capital equipment industry ----
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Industrial automation platforms and robotic welding cells (Vortex); large CNC machining centres (Kellner); hydraulic press systems (Bremer)",
        cv_location="All Professional Experience sections",
        notes="16-year career entirely in industrial manufacturing capital equipment. Deep sector fluency.",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="HR automation and workforce management SaaS; sales enablement SaaS",
        cv_location="All Professional Experience sections",
        notes="Career entirely in SaaS. Manufacturing listed as a vertical she sells into but she does not have industrial capital equipment domain expertise.",
        investigation_question="What is the depth of Linda's manufacturing vertical knowledge — does she understand capital equipment buying processes and plant-floor decision-making?",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Large industrial presses, metal-forming equipment, automated material-handling (Fujikawa); injection-moulding machines and industrial robots (Nissei)",
        cv_location="All Professional Experience sections",
        notes="Deep manufacturing domain expertise — heavy machinery, press systems, factory automation. Strong match to TitanForge product set.",
    ),
    # ---- REQ-06: Long sales cycle management (6–18 months, $500K+ deals) ----
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Average EMEA deal size $2.1M, cycle length 11 months; $9.8M CNC programme 16-month cycle; average deal $1.4M–$6.2M",
        cv_location="Regional VP Sales EMEA and Senior AE Kellner sections",
        notes="All deal experience matches long-cycle capital equipment selling. Average deal well above $500K.",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Closed 4 anchor enterprise deals ($900K–$2.1M ACV) in manufacturing vertical; sales cycles of 6–8 months",
        cv_location="VP Sales Axiom section",
        notes="Primarily SaaS sales cycles (3–6 months typical). Manufacturing deals cited are 6–8 months — at low end of 9–18 month range for industrial capital equipment. Deal sizes are ACV-based, not capital equipment project values.",
        investigation_question="Has Linda managed sales cycles longer than 9 months, and does she have experience with capital equipment procurement rather than SaaS subscription buying?",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Thai Tier 1 stamping plant: $3.6M deal, 14-month cycle. Subaru Gunma: $2.9M, 12 months. BDR support on 8–15 month cycles.",
        cv_location="Director BD SEA and Senior BD Manager sections",
        notes="Solid long-cycle capital equipment selling experience. Deal sizes ($2.9M–$3.6M) well above threshold.",
    ),
    # ---- REQ-07: Salesforce proficiency + RevOps partnership ----
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Salesforce pipeline coverage improved 1.4x to 3.1x in 12 months; Salesforce Certified Administrator; custom forecasting dashboards, forecast variance ±8%",
        cv_location="Regional VP EMEA and Director of Sales NA sections",
        notes="Strong Salesforce user and implementation driver. Certified admin. Worked directly with RevOps on dashboards.",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Led Salesforce Migration from HubSpot; designed custom lead-routing, forecasting, activity dashboards; Salesforce Certified Sales Cloud Consultant; forecast variance ±6%",
        cv_location="VP Sales Axiom section and Certifications",
        notes="Deep Salesforce and RevOps capability. Led full CRM migration, built custom architecture. Certified Sales Cloud Consultant — higher credential than Weber.",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="No mention of Salesforce or any CRM system in the CV. Japanese industrial context may use different sales tools.",
        investigation_question="Does Kenji have experience with Salesforce or comparable Western CRM platforms, or has his pipeline management been through internal Japanese enterprise systems?",
    ),
    # ---- REQ-08: Executive relationship-building with C-suite buyers ----
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Relationships with VP Operations and Head of Manufacturing at 6 BMW Group supplier plants; VP Manufacturing and Director Procurement at VW, Daimler, ZF",
        cv_location="Senior AE Kellner and AE Bremer sections",
        notes="Proven access to VP Manufacturing, Director Procurement, Plant Director at major European industrial OEMs. Precisely the buyer profile at TitanForge's EMEA targets.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Engaged VP Sales Ops, CIO, and CFO at Nationwide Insurance. C-suite engagement in SaaS deals.",
        cv_location="Senior AE Salesbridge section",
        notes="C-suite relationship experience exists but in SaaS/software context (CIO, CFO, VP Sales Ops). No evidence of industrial buyer relationships (VP Manufacturing, Plant Director, COO at manufacturing companies).",
        investigation_question="Can Linda credibly navigate the technical and operational complexity of C-suite conversations at manufacturing companies where buyers are engineers, not technology buyers?",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="VP Manufacturing and Plant Director at Thai Tier 1 stamping plant; Director Procurement at Subaru; VP Manufacturing, Director Procurement at Honda, Kawasaki Aerospace",
        cv_location="Director BD SEA and Senior BD Manager sections",
        notes="Direct C-suite and VP-level engagement with manufacturing buyers — the right buyer profile for TitanForge. Strong evidence.",
    ),
    # ---- REQ-09: Cross-cultural selling (Northern European, Anglo-Saxon) ----
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Native German, fluent English; offices in Frankfurt, Stockholm, Birmingham; DACH, Nordics, UK/Benelux territory",
        cv_location="Professional Summary and Regional VP EMEA section",
        notes="Lived and sold across German, Scandinavian, and UK markets. Native German speaker. Direct cultural fluency across the exact geographies TitanForge is entering.",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="US and Canada only throughout career. English native only.",
        cv_location="All Professional Experience sections",
        notes="No international selling experience. No European language skills. No evidence of navigating non-US business cultures.",
        investigation_question="Has Linda sold to or collaborated with international colleagues in a way that demonstrates cultural adaptability?",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Southeast Asia: Thailand, Vietnam, Indonesia, Malaysia. Languages: Japanese, English, Mandarin.",
        cv_location="Director BD SEA section",
        notes="Cross-cultural selling experience, but in APAC contexts (Japanese, Chinese, Southeast Asian cultures). European cultural dynamics (German directness, Nordic consensus) are different and untested.",
        investigation_question="Has Kenji engaged with European customers or partners in any capacity, and has he studied or reflected on differences between APAC and European business cultures?",
    ),
    # ---- REQ-10: Pricing strategy for new market entry ----
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="Worked with CFO and CRO to adapt North American list pricing for EMEA; defined territory segmentation across DACH / Nordics / UK-Benelux",
        cv_location="Regional VP Sales EMEA section",
        notes="Involved in EMEA pricing adaptation at Vortex. Evidence is inferred from market build description rather than explicit pricing strategy deliverable.",
        investigation_question="What was Marcus's specific contribution to EMEA pricing strategy — did he own the model, co-develop it, or implement a model the CFO designed?",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="No pricing strategy work mentioned in CV.",
        cv_location=None,
        notes="CV contains no evidence of pricing strategy development for market entry. All pricing context is US-domestic SaaS ARR.",
        investigation_question="Has Linda been involved in international pricing decisions, currency risk management, or localised pricing model development?",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Adjusted list prices for import tariffs (10–15%), FX volatility (JPY/THB), and competitive pressure from Chinese press manufacturers; maintained 38% gross margin target",
        cv_location="Director BD SEA section",
        notes="Explicit localised pricing strategy for SEA market entry with tariff, FX, and competitive adjustments. Strong evidence — methodology is transferable even if geographies differ.",
    ),
    # ---- REQ-11: European language fluency + DACH/Nordic industrial relationships ----
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="German: Native; French: Conversational. Relationships with VP Manufacturing at 6 BMW Group supplier plants across Bavaria and Baden-Württemberg.",
        cv_location="Languages section and Senior AE Kellner section",
        notes="Native German speaker with existing industrial relationships across DACH. Exceeds the requirement.",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="English: Native. No other languages listed.",
        cv_location="Languages section",
        notes="English only. No European language capability and no European industrial relationships.",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="Japanese: Native, English: Business fluent, Mandarin: Fluent. No European languages.",
        cv_location="Languages section",
        notes="No European languages. No DACH or Nordic customer relationships. APAC language set.",
    ),
    # ---- REQ-12: Hunter mentality (behavioral — not CV assessable) ----
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. CV shows new logo opening in early EMEA tenure (11 anchor deals personally). Consistent with hunter orientation.",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. CV shows some new logo activity but primary narrative is team scaling and coaching, not market hunting.",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. CV shows 14 net-new accounts in SEA — consistent with BD/hunting mentality. Limited evidence on sustained market-open behaviour over years.",
    ),
    # ---- REQ-13: Cultural adaptability (behavioral — not CV assessable) ----
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. Native German, raised in German business culture, has operated in Scandinavian and UK contexts. Strong circumstantial CV evidence.",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. No evidence of cross-cultural selling. US-only career limits assessment.",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. Demonstrated APAC cross-cultural selling (Japan, Thailand, Vietnam, Indonesia). European cultural agility untested.",
    ),
    # ---- REQ-14: Coach-first leadership (behavioral — not CV assessable) ----
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Marcus Weber",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. CV notes bi-weekly deal reviews, quarterly coaching clinics, team attainment 112–124%. Structural coaching evidence.",
    ),
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Linda Okafor-Mills",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. CV shows 11 promotions from direct reports, structured 90-day onboarding, quarterly coaching framework. Strongest coaching narrative of all three candidates.",
    ),
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Kenji Watanabe",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral attribute. Small team (8 people). Completed Fujikawa leadership programme. Insufficient evidence of coaching at scale.",
    ),
]

# ---------------------------------------------------------------------------
# Scenario configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG = ScenarioConfig(
    name=ScenarioName.GROWTH,
    category_weights={
        "EXPERIENCE_STRENGTH": 1.4,
        "EXPERIENCE_GAP": 1.4,
        "EXECUTION": 1.2,
        "STRATEGIC": 1.2,
        "CULTURAL": 1.1,
        "FRICTION": 1.0,
        "COMPLEMENT": 1.0,
        "COLLISION": 0.9,
        "DERAILMENT": 0.8,
        "DARK_SIDE": 0.8,
        "INTEGRATION": 0.7,
        "TENURE": 0.7,
        "GROUPTHINK": 0.6,
        "EVIDENCE_QUALITY": 0.6,
        "ROUTING": 0.5,
    },
)

# ---------------------------------------------------------------------------
# Ground truth expectation map
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, object] = {
    # Expected relative ranking under GROWTH scenario
    "expected_ranking": ["Marcus Weber", "Linda Okafor-Mills", "Kenji Watanabe"],
    # Assessment modes
    "assessment_modes": {
        "Marcus Weber": "full",
        "Linda Okafor-Mills": "full",
        "Kenji Watanabe": "partial",
    },
    # Per-candidate rubric profiles (expected RubricLevel distribution across 14 requirements)
    "rubric_profiles": {
        "Marcus Weber": {
            "exceeds_count": 7,   # REQ-01,04,05,06,08,09,11
            "meets_count": 3,     # REQ-02 (also exceeds), REQ-07, REQ-10
            "partial_count": 0,
            "gap_count": 0,
            "not_assessable_count": 4,  # REQ-12,13,14 (behavioral) + REQ-02 shares space
            "notes": "All high-priority GROWTH requirements either exceed or meet. Behaviorals unassessable.",
        },
        "Linda Okafor-Mills": {
            "exceeds_count": 2,   # REQ-02, REQ-07
            "meets_count": 1,     # REQ-01
            "partial_count": 3,   # REQ-03, REQ-06, REQ-08
            "gap_count": 5,       # REQ-04, REQ-05, REQ-09, REQ-10, REQ-11
            "not_assessable_count": 3,  # REQ-12,13,14 (behavioral)
            "notes": "Critical EMEA and manufacturing gaps. Strongest candidate on quota scale and Salesforce.",
        },
        "Kenji Watanabe": {
            "exceeds_count": 1,   # REQ-05
            "meets_count": 3,     # REQ-06, REQ-08, REQ-10
            "partial_count": 3,   # REQ-02, REQ-03, REQ-09
            "gap_count": 4,       # REQ-01, REQ-04, REQ-11, and implicitly REQ-07
            "not_assessable_count": 4,  # REQ-07 (no CRM evidence), REQ-12,13,14 (behavioral)
            "notes": "Strong manufacturing domain fit. Disqualifying gap: no EMEA market experience. Partial mode — no Big Five.",
        },
    },
    # High-priority GROWTH requirements and expected gap candidates
    "high_priority_growth_reqs": [
        "REQ-01", "REQ-02", "REQ-03", "REQ-04",
        "REQ-05", "REQ-06", "REQ-08", "REQ-09",
        "REQ-10", "REQ-11", "REQ-12", "REQ-13", "REQ-14",
    ],
    "critical_gaps_by_candidate": {
        "Marcus Weber": [],
        "Linda Okafor-Mills": ["REQ-04", "REQ-05", "REQ-09", "REQ-11"],
        "Kenji Watanabe": ["REQ-01", "REQ-02", "REQ-04", "REQ-11"],
    },
    # Scenario notes
    "scenario_notes": (
        "GROWTH scenario heavily weights EMEA experience, market-entry capability, "
        "and industrial domain. Marcus Weber is the clear fit. Linda Okafor-Mills "
        "is a strong people-leader and Salesforce expert but lacks EMEA and "
        "manufacturing fundamentals — a high-development-risk hire. Kenji Watanabe "
        "has deep manufacturing domain fit and transferable market-build experience "
        "but lacks EMEA presence, quota scale, and European languages — a stretch."
    ),
}
