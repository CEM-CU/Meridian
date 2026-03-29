"""Head of Marketing scenario fixture — Vela Beauty (DTC consumer, $65M revenue).

Hiring context: GROWTH — expanding from US-only to UK, Germany, and France.
Three candidates with distinct strength/gap profiles:
- Isabelle Moreau: strong fit — international DTC experience, full-stack marketing
- Derek Washington: partial fit — exceptional performance/growth, zero brand/international
- Léa Dubois: stretch — deep EU brand expertise, limited scale and DTC analytics, NO Big Five
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
Vela Beauty — Head of Marketing

Location: Los Angeles, CA (Hybrid) | Reports to: CEO
Employment: Full-Time

About Vela Beauty

Vela Beauty is a DTC consumer brand redefining clean, performance-driven personal care
for the modern consumer. Since our founding in 2018, we have grown from a single hero
product to a portfolio of 34 SKUs, reaching $65M in net revenue in 2025 with a team of
220 people. We are 85% digital — built on owned-channel relationships, a subscriber base
of 190,000 active customers, and a creator-led community of over 2,000 brand advocates.

We are at an inflection point. Our US foundation is strong. Now we are expanding into
the United Kingdom, Germany, and France in 2026-2027, exploring retail partnerships
with premium beauty destinations, and investing in brand-building that will carry Vela
beyond performance channels. This is a rare opportunity to own the full marketing
function at a high-growth consumer brand and leave a visible mark on its global chapter.

The Role

The Head of Marketing will own Vela Beauty's brand, growth, and go-to-market strategy
across all channels and geographies. Reporting directly to the CEO, you will lead a
marketing team of 18 (performance, brand, content, PR, and influencer) and partner with
product, commercial, and finance leadership to drive sustainable, profitable growth.
This is an executive seat — you will shape strategy, hold budget accountability, and
represent the brand externally.

What You Will Do

- Own the marketing P&L, managing an annual advertising and media budget of $18M across
  paid social, search, video, affiliate, and emerging channels; optimise toward blended
  CAC and LTV targets that sustain our unit economics through international expansion.
- Lead international market launches in UK, Germany, and France — from localised brand
  positioning and channel strategy to media planning, regulatory compliance on claims,
  and cultural adaptation of creative assets. EU expansion begins Q3 2026.
- Build and lead a high-performing marketing team of 18 across performance marketing,
  brand, content, PR, and influencer functions; develop talent, set structure, and
  close capability gaps as the team scales alongside international growth.
- Drive brand-building strategy that elevates Vela beyond performance channels —
  establishing emotional resonance, a consistent brand voice, and earned-media presence
  in an increasingly competitive clean beauty category.
- Develop and execute a retail and wholesale go-to-market strategy as Vela evaluates
  partnerships with Sephora, Space NK, Douglas, and select pharmacy chains in Europe;
  coordinate with commercial and operations teams on trade marketing, planogram
  strategy, and in-store activation.
- Own influencer and creator strategy — evolve Vela's community of 2,000+ creators into
  a differentiated, brand-safe programme that drives both awareness and measurable
  lower-funnel impact; set standards for brief development, vetting, and performance
  measurement.
- Lead content and creative direction across all consumer touchpoints — from
  hero campaign concepting through to channel-specific execution; partner with in-house
  creative team and external agencies to maintain brand consistency while adapting
  to local market aesthetics and cultural nuance.
- Oversee marketing analytics and measurement infrastructure: attribution modelling,
  Media Mix Modelling (MMM), incrementality testing, and cohort LTV analysis; turn
  data into decisions that improve efficiency and justify investment at board level.
- Build earned media and PR presence in the US and across EU markets; cultivate
  relationships with beauty editors, journalists, and trade press to drive organic
  coverage in editorial, podcasts, and digital publications.
- Partner with the CEO and product leadership on new product launch strategy —
  go-to-market sequencing, positioning, launch activation, and post-launch optimisation
  across channels and geographies.

What We Are Looking For

Experience and Skills

- 10+ years in consumer brand or DTC marketing, with demonstrated experience managing
  performance marketing at scale ($15M+ annual paid media spend) and responsibility for
  CAC/LTV performance across the full funnel.
- Proven track record launching or significantly scaling a consumer brand in at least
  two of the target EU markets (UK, Germany, France) — including localised positioning,
  cultural adaptation, and channel-specific media strategy.
- Experience leading and developing a marketing team of 15 or more across diverse
  functions; strong talent developer who can recruit, structure, and retain in a
  competitive market.
- Deep familiarity with beauty, personal care, or adjacent consumer category — ideally
  with hands-on knowledge of category dynamics, retail buyer relationships, and
  consumer behavior in DTC and omnichannel contexts.
- Track record in retail or wholesale channel go-to-market, including joint business
  planning with retail partners and experience coordinating in-store and digital
  co-marketing programmes.
- Expertise in influencer and creator marketing — strategy, programme architecture,
  measurement, and the ability to navigate a creator ecosystem at scale without
  sacrificing brand integrity.
- Proficiency in content and creative direction — able to brief, evaluate, and elevate
  creative output across brand, product, and performance contexts; a point of view on
  visual identity and brand voice.
- Command of marketing analytics — attribution tools, MMM methodology, incrementality
  testing, cohort analysis; comfort in a data-dense environment and ability to
  translate measurement into budget decisions.
- Experience with PR and earned media strategy across at least two geographies;
  existing media relationships in beauty or lifestyle a plus.

Behavioral Attributes

- Creative vision balanced with analytical rigor: you are equally comfortable writing
  a brief for a hero campaign and interrogating a CAC waterfall with your growth team.
- A natural storyteller who can translate data, brand strategy, and consumer insight
  into a compelling narrative — for internal alignment, board presentations, retail
  buyer meetings, and external audiences.
- Cross-cultural fluency and curiosity: you approach new markets with genuine
  intellectual curiosity, adapt quickly to local consumer dynamics, and build teams
  that reflect the markets they serve.

Compensation: $220,000-$260,000 base + performance bonus + equity
""".strip()

# ---------------------------------------------------------------------------
# Candidate A — Isabelle Moreau (Strong Fit)
# ---------------------------------------------------------------------------

ISABELLE_MOREAU_CV_TEXT: str = """
ISABELLE MOREAU
VP Marketing | DTC Consumer Brand Builder | International Expansion

Los Angeles, CA | isabelle.moreau@email.com

PROFESSIONAL EXPERIENCE

VP Marketing, Luminary Wellness — Los Angeles, CA (2020-Present)
Luminary Wellness is a DTC health and wellness brand with $90M net revenue,
190,000 active subscribers, and a portfolio of supplements, skincare, and personal
care products sold direct-to-consumer across the US, UK, and Germany.

- Own full marketing P&L: $20M annual paid media budget across Meta, Google, TikTok,
  YouTube, and programmatic; responsible for blended CAC, LTV, and contribution margin
  targets across all markets and channels.
- Led Luminary's international expansion from zero international revenue to $18M in
  24 months — launched UK market in Q2 2022 and Germany in Q1 2023, including
  localised brand positioning, EU regulatory compliance (GDPR, cosmetics claims),
  cultural adaptation of creative assets, and market-specific influencer strategy.
- Reduced blended CAC by 34% over 18 months through channel mix optimisation,
  creative testing cadence (120+ A/B tests per quarter), and improved attribution via
  custom Northbeam implementation and quarterly MMM refresh.
- Secured Sephora Europe retail partnership — 120 doors across UK, France, and Germany;
  led joint business planning, trade marketing activation, in-store visual merchandising
  strategy, and launch campaign resulting in sell-through exceeding forecast by 22%.
- Lead and develop a 22-person marketing team spanning performance marketing (7),
  brand and creative (5), content and social (4), influencer and creator (4), and PR (2);
  promoted 4 internal candidates to senior roles in the last 18 months.
- Overhauled influencer programme: restructured from a transactional gifting model to
  a tiered creator community of 1,800 partners with performance tiers, co-creation
  briefs, and quarterly performance reviews; programme drove 28% of new subscriber
  acquisition in Q4 2024.
- Built and own Luminary's earned media strategy; grew editorial coverage from 12 to
  47 placements per quarter in Vogue, Allure, Glamour, and Refinery29; established
  relationships with UK beauty editors at Harper's Bazaar UK and Cosmopolitan UK ahead
  of market launch.
- Partner with CEO on new product launch strategy — own go-to-market sequencing,
  positioning, and cross-channel activation for 6 major product launches since 2021,
  including two hero launches that each exceeded $4M first-year revenue.

Head of Growth Marketing, Bask Skincare — San Francisco, CA (2017-2020)
Bask Skincare was a $28M DTC skincare brand (acquired by Unilever Ventures in 2021).

- Managed $6M annual paid media budget; grew ROAS from 1.8x to 3.1x in 18 months
  through structured creative testing and audience segmentation on Meta and Google.
- Built performance marketing team from 2 to 9; established first attribution framework
  and weekly CAC/LTV reporting cadence.
- Launched Amazon DTC storefront — became second-largest channel within 12 months,
  contributing $5.2M incremental revenue in year one.

Senior Brand Manager, L'Oréal Paris — New York, NY (2013-2017)
- Managed $12M brand marketing budget for two haircare lines; led creative briefing,
  agency management, and campaign execution across TV, digital, and in-store.
- Worked with European counterparts on product localisation for French and German
  markets; participated in EU regulatory submissions for product claims.
- Managed relationship with two creative agencies and one PR firm; delivered 3
  integrated brand campaigns, including one that won a Cannes Lions bronze (2016).

EDUCATION
- MBA, Marketing — UCLA Anderson School of Management (2013)
- BA, Communications — University of Southern California (2010)

LANGUAGES: English (native), French (native bilingual), German (professional working)

KEY METRICS SUMMARY
- Peak annual paid media managed: $20M (current)
- CAC reduction delivered: 34% over 18 months
- International revenue built: $0 → $18M in 24 months (UK + Germany)
- Team built and led: 22 direct and indirect
- Retail partnership executed: Sephora Europe, 120 doors
""".strip()

ISABELLE_MOREAU_BIG_FIVE = BigFiveScores(
    O=0.85,  # Very high openness — creative vision, cultural curiosity, embraces new markets
    C=0.68,  # High conscientiousness — data-rigorous, structured campaign execution
    E=0.78,  # High extraversion — external brand storyteller, retail and media relationships
    A=0.52,  # Medium agreeableness — collaborative but will hold position on brand standards
    N=0.18,  # Very low neuroticism — steady through complex multi-market launches
)

CANDIDATE_ISABELLE = CandidateData(
    name="Isabelle Moreau",
    cv_text=ISABELLE_MOREAU_CV_TEXT,
    big_five=ISABELLE_MOREAU_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — Derek Washington (Partial Fit)
# ---------------------------------------------------------------------------

DEREK_WASHINGTON_CV_TEXT: str = """
DEREK WASHINGTON
Head of Growth | Performance Marketing & Analytics | DTC Scale

Austin, TX | derek.washington@email.com

PROFESSIONAL EXPERIENCE

Head of Growth, Meridio Financial — Austin, TX (2021-Present)
Meridio Financial is a Series D consumer fintech (BNPL + embedded credit), $310M ARR,
2.1M registered users. Raised $180M Series D in 2023.

- Own full growth marketing function with $30M annual paid media budget across Meta,
  Google, TikTok, CTV, and affiliate; primary KPIs are CAC, activation rate, and
  LTV:CAC ratio across three product lines.
- Built and lead growth team from 4 to 18 — performance marketing (8), marketing
  analytics (5), lifecycle/CRM (3), and experimentation (2); all internal hires
  promoted from team or recruited from top fintech and DTC competitors.
- Implemented incrementality testing programme with 12 always-on geo-holdout experiments
  running in parallel; identified $4.8M in wasted spend in first 6 months, redirected
  to highest-incremental channels.
- Built custom MMM (Media Mix Model) in-house using PyMC — first iteration delivered in
  90 days; now refreshed quarterly and used for annual budget allocation and board-level
  investment cases.
- Reduced blended CAC by 41% over 28 months through channel diversification, multi-touch
  attribution migration (from last-click to data-driven via Rockerbox), and creative
  iteration at scale (200+ creative variants tested annually).
- Drove LTV optimisation: partnered with data science team to build cohort LTV model
  with 12-month predictive accuracy of 87%; used to shift acquisition toward higher-LTV
  segments, improving 12-month payback period from 14 to 9 months.
- Built experimentation culture: 40+ A/B tests per month across landing pages, ad
  creative, and onboarding flows; established statistical standards (90% power,
  Bayesian reporting) and trained team on interpreting results.

Senior Growth Manager, Finch Health — New York, NY (2018-2021)
Finch Health was a digital health startup (Series B, $45M raised, 280K users).

- Managed $8M paid media budget; grew subscriber base from 65K to 280K in 30 months.
- Built first marketing analytics stack (Segment, Amplitude, Looker); reduced reporting
  time from 3 days to 4 hours.
- Led app store optimisation (ASO) effort that increased organic install rate by 63%
  within 6 months.

Growth Marketing Manager, Ladder Financial — San Francisco, CA (2015-2018)
- Managed $3.5M paid media budget across Google and Facebook; reduced CPA by 29% in
  12 months through audience segmentation and landing page optimisation.
- First marketing analytics hire; built attribution reporting that became the standard
  framework adopted company-wide.

EDUCATION
- BS, Statistics — University of Michigan (2015)

KEY METRICS SUMMARY
- Peak annual paid media managed: $30M (current)
- CAC reduction delivered: 41% over 28 months
- Team built and led: 4 → 18 (current)
- MMM built: in-house PyMC model, quarterly refresh
- Incrementality programme: 12 geo-holdout experiments in parallel
- Industries: fintech, digital health (no consumer/beauty, no international, no retail)
""".strip()

DEREK_WASHINGTON_BIG_FIVE = BigFiveScores(
    O=0.55,  # Medium openness — data-first thinker, pragmatic about tools and methods
    C=0.82,  # High conscientiousness — rigorous, process-oriented, measurement-obsessed
    E=0.70,  # High extraversion — confident presenter, builds team culture through clarity
    A=0.45,  # Below-average agreeableness — direct, optimises for outcomes over harmony
    N=0.22,  # Low neuroticism — calm under pressure, evidence-based decision-making
)

CANDIDATE_DEREK = CandidateData(
    name="Derek Washington",
    cv_text=DEREK_WASHINGTON_CV_TEXT,
    big_five=DEREK_WASHINGTON_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Léa Dubois (Stretch, NO Big Five)
# ---------------------------------------------------------------------------

LEA_DUBOIS_CV_TEXT: str = """
LÉA DUBOIS
Marketing Director | Luxury Beauty & Brand Strategy | EU Markets

Paris, France | lea.dubois@email.com

PROFESSIONAL EXPERIENCE

Marketing Director, Maison Clarté — Paris, France (2021-Present)
Maison Clarté is a French luxury skincare and fragrance brand, €48M revenue, distributed
through Galeries Lafayette, Le Bon Marché, Douglas Germany, and Harrods in the UK.
The brand is 70% retail, 30% e-commerce. Marketing team of 6.

- Own all marketing strategy and execution with a €2.8M annual marketing budget
  (inclusive of all paid media, production, PR, and events); responsible for brand
  health KPIs, editorial coverage, and retail sell-through metrics.
- Define and execute localised brand strategy across France, Germany, and the UK —
  adapted positioning, visual identity variations, and campaign messaging to reflect
  distinct cultural expectations of luxury and efficacy in each market; Germany
  campaigns emphasise clinical credibility, UK campaigns lead on heritage and craft.
- Built and manage influencer and creator partnership programme: 220 active partnerships
  across France (140), Germany (50), and UK (30); manage briefing process, gifting
  logistics, exclusivity windows, and performance review; programme generated
  estimated earned media value of €4.1M in 2024.
- Led brand repositioning project (2022-2023): refreshed visual identity, revised brand
  voice guidelines, and introduced new hero campaign platform ("La Clarté du Geste")
  — earned coverage in Le Monde, Vogue Paris, ELLE Germany, and Harper's Bazaar UK.
- Manage agency roster: brand strategy agency, production house, PR firm (France + UK),
  and digital performance agency; oversee briefs, creative quality, and delivery.
- Established Maison Clarté's earned media programme from near-zero: built relationships
  with 60+ beauty editors and journalists across France, Germany, and UK; secured
  brand features in 3 major UK print titles and front-of-book placement in Vogue Paris.
- Partner with commercial team on retail activation — seasonal in-store events,
  gondola refresh strategy, and co-marketing with Douglas and Harrods; supported two
  new retail launches (Selfridges, 2022; Galeries Lafayette Haussmann pop-up, 2023).

Senior Brand Manager, Lancôme (L'Oréal Group) — Paris, France (2018-2021)
- Managed brand campaigns for the Absolue skincare line across France and Southern
  Europe; €8M production and media budget.
- Led cross-functional project to refresh Absolue's visual identity for Gen Z consumers;
  collaborated with global creative, digital, and retail teams across 6 markets.
- Managed two external agencies; delivered two integrated campaigns including digital,
  OOH, and print; one campaign shortlisted for an Effie France award (2020).

Brand Manager, NUXE — Paris, France (2016-2018)
- Supported marketing director on campaign execution for Huile Prodigieuse line;
  managed influencer gifting programme (80 creators) and PR outreach calendar.
- Coordinated with German and Spanish market teams on localisation of pan-European
  campaign assets.

EDUCATION
- MSc, Luxury Brand Management — ESSEC Business School (2016)
- BA, Marketing and Communications — Sciences Po Paris (2014)

LANGUAGES: French (native), English (professional fluency), German (conversational)

PROFILE NOTE
My background is grounded in brand, creative, and earned media strategy in luxury beauty.
I am building depth in performance marketing and DTC analytics — I completed a
Certificate in Digital Marketing Analytics (CXL Institute, 2024) and have been working
closely with Maison Clarté's digital agency on Meta campaigns for the past 12 months.
I am drawn to Vela Beauty because I want to operate at larger scale and bring EU brand
expertise to a DTC-native context.
""".strip()

CANDIDATE_LEA = CandidateData(
    name="Léa Dubois",
    cv_text=LEA_DUBOIS_CV_TEXT,
    big_five=None,
    personality_source=None,
)

# ---------------------------------------------------------------------------
# All Candidates
# ---------------------------------------------------------------------------

ALL_CANDIDATES: list[CandidateData] = [CANDIDATE_ISABELLE, CANDIDATE_DEREK, CANDIDATE_LEA]

# ---------------------------------------------------------------------------
# Requirements (extracted from JD — 13 requirements)
# ---------------------------------------------------------------------------

REQUIREMENTS: list[Requirement] = [
    Requirement(
        requirement_id="REQ-01",
        text="Performance marketing at scale: $15M+ annual paid media spend with CAC/LTV accountability",
        source_quote="managing an annual advertising and media budget of $18M across paid social, search, "
        "video, affiliate, and emerging channels; optimise toward blended CAC and LTV targets",
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
        requirement_id="REQ-02",
        text="International market launch experience in EU markets (UK, Germany, France)",
        source_quote="Proven track record launching or significantly scaling a consumer brand in at least "
        "two of the target EU markets (UK, Germany, France)",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.LOW,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-03",
        text="Marketing team leadership: building and developing teams of 15+",
        source_quote="Experience leading and developing a marketing team of 15 or more across diverse "
        "functions; strong talent developer who can recruit, structure, and retain",
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
        requirement_id="REQ-04",
        text="Beauty or consumer category expertise (DTC or omnichannel context)",
        source_quote="Deep familiarity with beauty, personal care, or adjacent consumer category — ideally "
        "with hands-on knowledge of category dynamics, retail buyer relationships, and consumer behavior",
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
        requirement_id="REQ-05",
        text="Retail and wholesale go-to-market experience (joint business planning, in-store activation)",
        source_quote="Track record in retail or wholesale channel go-to-market, including joint business "
        "planning with retail partners and experience coordinating in-store and digital co-marketing",
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
        text="Influencer and creator programme strategy and management at scale",
        source_quote="Expertise in influencer and creator marketing — strategy, programme architecture, "
        "measurement, and the ability to navigate a creator ecosystem at scale",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.LOW,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-07",
        text="Content and creative direction across brand, product, and performance contexts",
        source_quote="Proficiency in content and creative direction — able to brief, evaluate, and elevate "
        "creative output across brand, product, and performance contexts; a point of view on visual identity",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.LOW,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-08",
        text="Marketing analytics: attribution, MMM, incrementality testing, cohort LTV analysis",
        source_quote="Command of marketing analytics — attribution tools, MMM methodology, incrementality "
        "testing, cohort analysis; comfort in a data-dense environment",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-09",
        text="PR and earned media strategy across multiple geographies",
        source_quote="Experience with PR and earned media strategy across at least two geographies; "
        "existing media relationships in beauty or lifestyle a plus",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.LOW,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-10",
        text="Brand-building strategy with clear brand voice and emotional resonance beyond performance",
        source_quote="Drive brand-building strategy that elevates Vela beyond performance channels — "
        "establishing emotional resonance, a consistent brand voice, and earned-media presence",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.LOW,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-11",
        text="Localization and cultural adaptation for EU consumer markets",
        source_quote="cultural adaptation of creative assets. EU expansion begins Q3 2026",
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
        text="Creative vision balanced with analytical rigor — operates across both brand and performance",
        source_quote="you are equally comfortable writing a brief for a hero campaign and interrogating a "
        "CAC waterfall with your growth team",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-13",
        text="Cross-cultural fluency and storytelling for internal and external audiences",
        source_quote="A natural storyteller who can translate data, brand strategy, and consumer insight "
        "into a compelling narrative — for internal alignment, board presentations, retail buyer meetings",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.HIGH,
        ),
    ),
]

# ---------------------------------------------------------------------------
# Rubric Assessments
# ---------------------------------------------------------------------------

RUBRIC_ASSESSMENTS: list[RubricAssessment] = [
    # --- Isabelle Moreau ---
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="$20M annual paid media budget across Meta, Google, TikTok, YouTube, and "
        "programmatic; reduced blended CAC by 34% over 18 months",
        cv_location="VP Marketing, Luminary Wellness (2020-Present)",
        notes="Exceeds $15M threshold; CAC improvement with attribution tooling is directly relevant.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Led Luminary's international expansion from zero international revenue to $18M in "
        "24 months — launched UK market in Q2 2022 and Germany in Q1 2023",
        cv_location="VP Marketing, Luminary Wellness (2020-Present)",
        notes="Launched two of the three target markets; includes EU regulatory compliance and "
        "cultural adaptation — exactly what Vela needs.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Lead and develop a 22-person marketing team spanning performance marketing (7), "
        "brand and creative (5), content and social (4), influencer and creator (4), and PR (2)",
        cv_location="VP Marketing, Luminary Wellness (2020-Present)",
        notes="22-person team exceeds 15-person threshold; all relevant subfunctions represented.",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Luminary Wellness is a DTC health and wellness brand with $90M net revenue; "
        "prior role at Bask Skincare (DTC skincare); L'Oréal Paris brand management",
        cv_location="Multiple roles",
        notes="Deep DTC consumer experience in wellness/personal care; L'Oréal background adds category depth.",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Secured Sephora Europe retail partnership — 120 doors across UK, France, and "
        "Germany; led joint business planning, trade marketing activation, in-store visual "
        "merchandising strategy",
        cv_location="VP Marketing, Luminary Wellness (2020-Present)",
        notes="Directly comparable retail execution with a top-tier beauty retailer in the target markets.",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="restructured from a transactional gifting model to a tiered creator community of "
        "1,800 partners with performance tiers, co-creation briefs, and quarterly performance reviews; "
        "programme drove 28% of new subscriber acquisition",
        cv_location="VP Marketing, Luminary Wellness (2020-Present)",
        notes="1,800-partner programme with measurable performance impact is directly transferable.",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="partner with in-house creative team and external agencies to maintain brand "
        "consistency; L'Oréal Paris brand campaigns across TV, digital, and in-store",
        cv_location="Multiple roles",
        notes="Creative direction evident but not independently leading a visual identity refresh — "
        "primarily executing with agencies. Confidence medium pending interview.",
        investigation_question="Can you describe a brand identity decision you personally drove, "
        "including specific creative choices and how you evaluated the outcome?",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="custom Northbeam implementation and quarterly MMM refresh; reduced blended CAC "
        "by 34% over 18 months through channel mix optimisation",
        cv_location="VP Marketing, Luminary Wellness (2020-Present)",
        notes="Northbeam attribution plus MMM refresh cycle and demonstrated CAC impact.",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="grew editorial coverage from 12 to 47 placements per quarter in Vogue, Allure, "
        "Glamour, and Refinery29; established relationships with UK beauty editors at Harper's Bazaar UK",
        cv_location="VP Marketing, Luminary Wellness (2020-Present)",
        notes="US + UK earned media with named relationships; quantified growth in placements.",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="Drive brand-building strategy; L'Oréal Paris — Cannes Lions bronze; Bask Skincare "
        "brand work prior to performance focus",
        cv_location="Multiple roles",
        notes="Brand credentials present but Luminary role is predominantly performance-led. "
        "Brand-building depth at Vela's scale needs validation.",
        investigation_question="How have you balanced performance channel accountability with "
        "longer-term brand equity investment, and what trade-offs have you made?",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="cultural adaptation of creative assets; Germany campaigns emphasised clinical "
        "credibility, UK positioned on lifestyle; EU regulatory compliance (GDPR, cosmetics claims)",
        cv_location="VP Marketing, Luminary Wellness (2020-Present)",
        notes="Hands-on EU localisation with regulatory awareness — directly matches Vela's needs.",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        notes="Behavioral requirement — not directly assessable from CV.",
        investigation_question="Walk me through a situation where you had to defend a creative "
        "decision to data-focused stakeholders, or vice versa.",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Isabelle Moreau",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        notes="Behavioral requirement — not directly assessable from CV.",
        investigation_question="Describe how you communicated the rationale behind a major "
        "strategic marketing decision to the board and to your team.",
    ),
    # --- Derek Washington ---
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="$30M annual paid media budget across Meta, Google, TikTok, CTV, and affiliate; "
        "reduced blended CAC by 41% over 28 months",
        cv_location="Head of Growth, Meridio Financial (2021-Present)",
        notes="Exceeds $15M threshold by 2x; strongest CAC improvement of all three candidates. "
        "Fintech context but mechanics are directly transferable.",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No international market experience anywhere in CV. All roles US-only.",
        investigation_question="Have you had any exposure to international market launches, "
        "even in an adjacent capacity such as supporting a global team?",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Built and lead growth team from 4 to 18 — performance marketing (8), marketing "
        "analytics (5), lifecycle/CRM (3), and experimentation (2)",
        cv_location="Head of Growth, Meridio Financial (2021-Present)",
        notes="Meets team-size threshold but team is narrowly scoped to growth/analytics — no brand, "
        "content, PR, or influencer functions. Leading a full-stack marketing team is unproven.",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="All experience is in fintech and digital health — no consumer, beauty, or personal care "
        "background. No retail buyer relationships, no category dynamics knowledge.",
        investigation_question="What is your understanding of the DTC beauty consumer, and "
        "have you engaged with any beauty or consumer category work professionally?",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="Zero retail or wholesale channel experience across all roles. Fintech and digital health "
        "are direct-to-consumer digital only.",
        investigation_question="Have you worked with retail or wholesale channel partners in any capacity?",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of influencer or creator strategy in any role. Growth function in fintech "
        "is entirely paid/owned/earned through digital performance channels.",
        investigation_question="Have you designed or managed a creator or influencer programme?",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of content or creative direction. CV is entirely quantitative — no brand "
        "creative, campaign concepting, or visual identity work mentioned.",
        investigation_question="Describe your experience directing creative work — briefing, "
        "evaluating, and providing feedback on brand or campaign creative.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Built custom MMM in-house using PyMC; incrementality testing programme with 12 "
        "always-on geo-holdout experiments; Rockerbox multi-touch attribution migration; "
        "cohort LTV model with 12-month predictive accuracy of 87%",
        cv_location="Head of Growth, Meridio Financial (2021-Present)",
        notes="The most analytically rigorous candidate. MMM, incrementality, attribution, and LTV "
        "modelling all evidenced with specific methodologies.",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No PR or earned media experience in any role. Growth function is paid-only.",
        investigation_question="Have you worked with PR teams or managed an earned media programme?",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No brand-building experience. Entire career is performance/growth — no brand equity "
        "work, no campaign narrative, no emotional brand positioning.",
        investigation_question="How do you think about brand equity and its relationship to "
        "performance channel efficiency over a 3-year horizon?",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No localization or cultural adaptation experience. No international exposure.",
        investigation_question="Have you adapted marketing strategy or creative for non-US audiences?",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        notes="Behavioral requirement — not directly assessable from CV.",
        investigation_question="Describe a time you had to defend a non-data-driven brand decision, "
        "or a time data led you to override your creative instinct.",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Derek Washington",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        notes="Behavioral requirement — not directly assessable from CV.",
        investigation_question="How do you communicate a marketing strategy to a non-marketing "
        "audience such as a board, a retail buyer, or an ops team?",
    ),
    # --- Léa Dubois ---
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="€2.8M annual marketing budget (inclusive of all paid media, production, PR, and events)",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="Total marketing budget is €2.8M, a fraction of the $15M+ paid media threshold. "
        "Completed a certificate in digital analytics but no hands-on DTC performance marketing "
        "at meaningful scale.",
        investigation_question="What is the largest paid media budget you have directly managed, "
        "and what was your role in campaign optimisation versus delegating to an agency?",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="localised brand strategy across France, Germany, and the UK — adapted positioning, "
        "visual identity variations, and campaign messaging; Germany campaigns emphasise clinical "
        "credibility, UK campaigns lead on heritage and craft",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="All three target EU markets covered with nuanced cultural differentiation — strongest "
        "EU localisation expertise of the three candidates.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Marketing team of 6",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="Team of 6 is well below the 15-person threshold. Leadership capability is evident "
        "but at much smaller scale with limited breadth of functions managed.",
        investigation_question="How would you approach building a team from 6 to 18+ across "
        "performance, brand, content, PR, and influencer functions you have not previously managed?",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Maison Clarté (luxury skincare and fragrance); Lancôme, L'Oréal Group (Absolue "
        "skincare line); NUXE (Huile Prodigieuse)",
        cv_location="Multiple roles",
        notes="Deepest beauty category expertise of all three candidates — luxury skincare, fragrance, "
        "and mass prestige across three brands. Retail channel knowledge via Galeries Lafayette, "
        "Douglas, and Harrods.",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="seasonal in-store events, gondola refresh strategy, and co-marketing with "
        "Douglas and Harrods; supported two new retail launches (Selfridges, 2022; "
        "Galeries Lafayette Haussmann pop-up, 2023)",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="Retail activation experience is real but at luxury scale and in a support/marketing "
        "capacity — no evidence of joint business planning or P&L ownership of retail channel.",
        investigation_question="Have you been involved in joint business planning with a retail buyer, "
        "including commercial targets, trade terms, or promotional funding?",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="220 active partnerships across France (140), Germany (50), and UK (30); "
        "manage briefing process, gifting logistics, exclusivity windows, and performance review; "
        "programme generated estimated earned media value of €4.1M in 2024",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="220-partner programme across three markets with EMV measurement — strong influencer "
        "competency, though at luxury/brand rather than DTC performance orientation.",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Led brand repositioning project: refreshed visual identity, revised brand voice "
        "guidelines, and introduced new hero campaign platform ('La Clarté du Geste'); "
        "Manage agency roster: brand strategy agency, production house, PR firm",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="Strongest creative direction evidence of all three candidates — end-to-end brand "
        "repositioning with named campaign platform and agency management.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="Certificate in Digital Marketing Analytics (CXL Institute, 2024); working closely "
        "with Maison Clarté's digital agency on Meta campaigns for the past 12 months",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="Self-declared gap acknowledged by candidate. CXL certificate and agency collaboration "
        "show awareness and intent but not operational depth in attribution, MMM, or LTV modelling.",
        investigation_question="Walk me through how you would approach building an attribution "
        "and MMM framework for a DTC brand — what vendors, methodologies, and team members "
        "would you involve?",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="built relationships with 60+ beauty editors and journalists across France, "
        "Germany, and UK; secured brand features in 3 major UK print titles and front-of-book "
        "placement in Vogue Paris",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="Strongest EU earned media relationships of all three candidates — France, Germany, "
        "and UK all covered with named publications.",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="refreshed visual identity, revised brand voice guidelines; brand repositioning "
        "project earned coverage in Le Monde, Vogue Paris, ELLE Germany, and Harper's Bazaar UK",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="Brand-building is the core competency — visual identity, brand voice, editorial "
        "narrative, and cross-market brand consistency all evidenced.",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="adapted positioning, visual identity variations, and campaign messaging to reflect "
        "distinct cultural expectations of luxury and efficacy in each market; Germany campaigns "
        "emphasise clinical credibility, UK campaigns lead on heritage and craft",
        cv_location="Marketing Director, Maison Clarté (2021-Present)",
        notes="Most granular EU cultural localisation evidence of all three candidates.",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        notes="Behavioral requirement — not directly assessable from CV. Notable that candidate "
        "self-identifies analytics as a development area, which is relevant context.",
        investigation_question="Describe a situation where you needed to make a budget or "
        "channel decision under data uncertainty — what was your process?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Léa Dubois",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        notes="Behavioral requirement — not directly assessable from CV.",
        investigation_question="Give an example of a time you adapted your communication style "
        "to a culturally different audience — what changed and what stayed the same?",
    ),
]

# ---------------------------------------------------------------------------
# Ground Truth
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, object] = {
    # Overall candidate ranking for GROWTH scenario
    "candidate_ranking": ["Isabelle Moreau", "Léa Dubois", "Derek Washington"],
    # Assessment modes
    "assessment_modes": {
        "Isabelle Moreau": "full",  # Big Five available
        "Derek Washington": "full",  # Big Five available
        "Léa Dubois": "partial",  # No Big Five
    },
    # Expected rubric-level summaries per candidate (counts by level, excluding NOT_ASSESSABLE)
    "rubric_summary": {
        "Isabelle Moreau": {
            "exceeds": 8,  # REQ-01,02,03,04,05,06,08,09,11
            "meets": 2,  # REQ-07, REQ-10
            "partial": 0,
            "gap": 0,
            "not_assessable": 2,  # REQ-12, REQ-13 (behavioral)
        },
        "Derek Washington": {
            "exceeds": 2,  # REQ-01, REQ-08
            "meets": 1,  # REQ-03
            "partial": 0,
            "gap": 8,  # REQ-02,04,05,06,07,09,10,11
            "not_assessable": 2,  # REQ-12, REQ-13 (behavioral)
        },
        "Léa Dubois": {
            "exceeds": 7,  # REQ-02,04,06,07,09,10,11
            "meets": 0,
            "partial": 2,  # REQ-03, REQ-05
            "gap": 2,  # REQ-01, REQ-08
            "not_assessable": 2,  # REQ-12, REQ-13 (behavioral)
        },
    },
    # High-priority gaps for GROWTH scenario (HIGH priority requirements with GAP level)
    "high_priority_gaps": {
        "Isabelle Moreau": [],
        "Derek Washington": [
            "REQ-02",  # International EU launch — HIGH in GROWTH
            "REQ-04",  # Beauty category — HIGH in GROWTH
            "REQ-05",  # Retail GTM — HIGH in GROWTH
            "REQ-06",  # Influencer strategy — HIGH in GROWTH
            "REQ-07",  # Creative direction — HIGH in GROWTH
            "REQ-09",  # PR/earned media — HIGH in GROWTH
            "REQ-10",  # Brand building — HIGH in GROWTH
            "REQ-11",  # EU localisation — HIGH in GROWTH
        ],
        "Léa Dubois": [
            "REQ-01",  # Performance marketing scale — HIGH in GROWTH
            "REQ-08",  # Marketing analytics — HIGH in GROWTH
        ],
    },
    # Expected flag categories likely present per candidate (informational, not exhaustive)
    "expected_flag_categories": {
        "Isabelle Moreau": [
            "EXPERIENCE_STRENGTH",  # International DTC launch, full-stack team, retail partnership
            "EXECUTION",  # CAC reduction, MMM, attribution
            "STRATEGIC",  # International expansion strategy
            "COMPLEMENT",  # Full-stack brand + performance balance
        ],
        "Derek Washington": [
            "EXPERIENCE_GAP",  # No brand, no international, no beauty, no retail, no creator
            "EXPERIENCE_STRENGTH",  # Performance marketing analytics
            "EXECUTION",  # CAC, MMM, incrementality
            "FRICTION",  # Pure-performance profile vs brand-led DTC role
        ],
        "Léa Dubois": [
            "EXPERIENCE_STRENGTH",  # EU brand expertise, influencer, creative direction, earned media
            "EXPERIENCE_GAP",  # Performance marketing scale, DTC analytics
            "ROUTING",  # Partial mode — personality flags unavailable
        ],
    },
    # Key tensions for Stage E evaluation
    "key_tensions": [
        "Derek Washington: exceptional analytics depth vs zero brand/beauty/international coverage — "
        "binary fit gap that cannot be bridged by coaching alone at Head of Marketing level.",
        "Léa Dubois: strongest EU expertise and brand credentials but material scale gap on performance "
        "marketing; COO/CEO should assess whether analytics gap is closeable within 12 months.",
        "Isabelle Moreau: strongest overall fit but behavioral requirements (creative-analytical balance, "
        "cross-cultural storytelling) should be probed in depth — CV leans performance.",
    ],
    # Scenario-specific notes
    "scenario_notes": "GROWTH scenario weights international expansion (REQ-02, REQ-11) and full-stack "
    "marketing leadership (REQ-03) most heavily. A performance-only profile like Derek Washington "
    "represents a structural mismatch for this hiring context regardless of analytics excellence.",
}

# ---------------------------------------------------------------------------
# Scenario Configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG = ScenarioConfig(
    name=ScenarioName.GROWTH,
    category_weights={
        "EXPERIENCE_STRENGTH": 1.4,
        "EXPERIENCE_GAP": 1.3,
        "EXECUTION": 1.2,
        "STRATEGIC": 1.2,
        "FRICTION": 1.1,
        "CULTURAL": 1.1,
        "COMPLEMENT": 1.0,
        "COLLISION": 0.9,
        "DERAILMENT": 0.8,
        "DARK_SIDE": 0.8,
        "EVIDENCE_QUALITY": 0.7,
        "ROUTING": 0.5,
    },
)

# ---------------------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------------------

__all__ = [
    "ALL_CANDIDATES",
    "CANDIDATE_DEREK",
    "CANDIDATE_ISABELLE",
    "CANDIDATE_LEA",
    "DEREK_WASHINGTON_BIG_FIVE",
    "DEREK_WASHINGTON_CV_TEXT",
    "GROUND_TRUTH",
    "ISABELLE_MOREAU_BIG_FIVE",
    "ISABELLE_MOREAU_CV_TEXT",
    "JD_TEXT",
    "LEA_DUBOIS_CV_TEXT",
    "REQUIREMENTS",
    "RUBRIC_ASSESSMENTS",
    "SCENARIO_CONFIG",
]
