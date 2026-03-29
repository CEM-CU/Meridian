"""Synthetic candidate profiles for pipeline testing.

Three candidates with distinct strength/gap profiles against the BMW CTO JD:
- Marcus Chen: strong technical + scope, partial geographic, gap on industry
- Sarah Okafor: strong industry + experience depth, partial technical, exceeds leadership
- Kenji Tanaka: balanced, gap on scope, NO Big Five (partial mode)
"""

from meridian.models import BigFiveScores, CandidateData

# ---------------------------------------------------------------------------
# Candidate A — Marcus Chen
# Strong technical + scope, partial on geographic, gap on industry (tech, not automotive)
# ---------------------------------------------------------------------------

MARCUS_CHEN_CV_TEXT: str = """
MARCUS CHEN
Chief Technology Officer | Enterprise Technology & AI

PROFESSIONAL EXPERIENCE

CTO, Apex Robotics Inc. — San Francisco, CA (2019-Present)
- Lead 320-person engineering organisation across San Francisco, Berlin, and Singapore
  delivering autonomous logistics systems for warehouse and last-mile applications.
- Own full P&L responsibility for technology division (USD 620M annual budget),
  achieving 14% cost reduction while increasing R&D output by 22% over 3 years.
- Architected migration from monolithic embedded stack to SOA-based software-defined
  platform, reducing feature deployment cycle from 6 months to 3 weeks.
- Spearheaded integration of two acquisitions (Navtiq Sensors, 90 engineers; StackEdge
  AI, 55 engineers) — unified toolchains within 8 months, retained 91% of key talent.
- Built ADAS perception pipeline processing 12 TB/day from lidar + camera fusion,
  achieving L4 autonomy certification in controlled warehouse environments.

VP Engineering, Helion Cloud Systems — Seattle, WA (2015-2019)
- Managed 180 engineers building distributed infrastructure for real-time IoT data
  processing; grew annual recurring revenue from USD 45M to USD 210M.
- Designed cybersecurity framework achieving SOC 2 Type II and ISO 27001 compliance
  across 3 data centre regions.
- Led cross-functional collaboration with product, sales, and customer success teams
  to define technical roadmap aligned with enterprise customer needs.

Senior Director, Platform Engineering — Quanta Semiconductor (2011-2015)
- Directed 85-person team developing embedded RTOS and middleware for automotive-grade
  SoCs; products shipped in 14M vehicles across 6 OEMs.
- Established formal ASPICE Level 2 processes for software delivery to automotive
  clients; reduced field-defect rate by 38%.

EDUCATION
- PhD, Electrical Engineering — Stanford University (2011)
- BS, Computer Science — UC Berkeley (2005)

LANGUAGES: English (native), Mandarin (conversational)
""".strip()

MARCUS_CHEN_BIG_FIVE = BigFiveScores(
    O=0.78,  # High openness — innovation-oriented
    C=0.82,  # High conscientiousness — disciplined execution
    E=0.71,  # Moderately high extraversion — confident communicator
    A=0.45,  # Below-average agreeableness — direct, challenges status quo
    N=0.28,  # Low neuroticism — calm under pressure
)

CANDIDATE_MARCUS = CandidateData(
    name="Marcus Chen",
    cv_text=MARCUS_CHEN_CV_TEXT,
    big_five=MARCUS_CHEN_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — Sarah Okafor
# Strong industry + experience depth, partial on technical (legacy auto, not EV/SDV),
# exceeds on leadership context
# ---------------------------------------------------------------------------

SARAH_OKAFOR_CV_TEXT: str = """
SARAH OKAFOR
Senior Technology Executive | Premium Automotive & Mobility

PROFESSIONAL EXPERIENCE

SVP Technology & Innovation, Stellantis NV — Amsterdam / Turin (2018-Present)
- Oversee 210-person technology organisation across Netherlands, Italy, and Morocco
  delivering connected-vehicle platforms for Maserati, Alfa Romeo, and DS brands.
- Full P&L ownership for digital services division (EUR 480M), delivering 18%
  year-over-year growth in subscription-based connected services revenue.
- Led the post-merger technology integration following PSA-FCA merger: harmonised
  3 legacy infotainment platforms into a single connected-vehicle architecture within
  18 months, consolidating 4 engineering sites.
- Drove enterprise-wide digital transformation programme spanning manufacturing
  (Industry 4.0), supply chain (digital twin), and customer experience (OTA updates),
  affecting 11 business units across EMEA and Latin America.
- Established Stellantis CyberSec Centre of Excellence; achieved UNECE WP.29
  compliance 6 months ahead of regulatory deadline.

VP Engineering, Continental AG — Hannover / Shanghai (2013-2018)
- Directed 140 engineers building ADAS sensor-fusion modules for tier-1 supply to
  BMW, Mercedes-Benz, and Volkswagen Group; portfolio generated EUR 320M annual revenue.
- Managed China engineering centre (45 engineers, Shanghai); navigated local
  partnership and data-localisation requirements for 3 OEM programmes.
- Implemented V-model development with ASPICE Level 3 certification; reduced defect
  escape rate to customer by 52%.

Director, Powertrain Controls — Jaguar Land Rover, Coventry, UK (2007-2013)
- Led 60-person team developing engine management and transmission control software
  for internal combustion drivetrains across Range Rover and Jaguar XF lines.
- Delivered first hybrid-assist programme (Range Rover Sport P400e), managing
  cross-functional integration between mechanical and electrical engineering teams.

EDUCATION
- MBA, INSEAD (2007)
- MEng, Automotive Engineering — Loughborough University (2002)

LANGUAGES: English (native), German (professional fluency), French (business)
""".strip()

SARAH_OKAFOR_BIG_FIVE = BigFiveScores(
    O=0.55,  # Medium openness — pragmatic innovator
    C=0.88,  # Very high conscientiousness — process-driven
    E=0.65,  # Moderate extraversion — effective but not dominant
    A=0.72,  # High agreeableness — consensus-oriented
    N=0.22,  # Low neuroticism — steady under crisis
)

CANDIDATE_SARAH = CandidateData(
    name="Sarah Okafor",
    cv_text=SARAH_OKAFOR_CV_TEXT,
    big_five=SARAH_OKAFOR_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Kenji Tanaka
# Balanced across most requirements, gap on scope (mid-size company background).
# NO Big Five scores — partial assessment mode.
# ---------------------------------------------------------------------------

KENJI_TANAKA_CV_TEXT: str = """
KENJI TANAKA
Technology Leader | Automotive Software & Electrification

PROFESSIONAL EXPERIENCE

CTO, Zenith Mobility Solutions — Tokyo / Munich (2020-Present)
- Lead 85-person engineering team building EV battery management systems (BMS) and
  SDV middleware for European and Japanese OEMs; annual division revenue EUR 95M.
- Architected AUTOSAR Adaptive-compliant middleware platform adopted by 2 premium
  European OEMs for next-generation EV models (SOP 2026).
- Established Munich engineering hub (25 engineers) to serve EMEA clients; built
  relationships with BMW, Porsche, and Volvo engineering teams.
- Drove ISO 21434 cybersecurity compliance programme; achieved certification within
  12 months of programme launch.
- Led digital transformation of legacy hardware-centric engineering culture to
  software-first agile delivery, reducing release cadence from quarterly to bi-weekly.

Director, Connected Vehicle Platform — Toyota Motor Corporation, Tokyo (2015-2020)
- Managed 65-person team developing Toyota's connected services platform (T-Connect)
  serving 4.2M active subscribers in Japan and ASEAN markets.
- Designed OTA update architecture handling 800K+ concurrent device connections with
  99.97% delivery reliability.
- Partnered with DENSO and Renesas to co-develop automotive-grade SoC specifications
  for next-generation infotainment and ADAS ECUs.
- Represented Toyota on the JASPAR consortium for vehicle cybersecurity standards
  and contributed to UNECE WP.29 working group.

Senior Manager, ADAS Software — Honda R&D, Tochigi, Japan (2010-2015)
- Led 30-person team developing camera-based ADAS features (LDW, ACC, AEB) for
  Honda Sensing suite; deployed across 3.8M vehicles globally.
- Implemented ASPICE Level 2 practices; reduced software defect density by 41%.

EDUCATION
- MS, Computer Science — University of Tokyo (2010)
- BS, Mechanical Engineering — Kyoto University (2008)

LANGUAGES: Japanese (native), English (professional fluency), German (intermediate)
""".strip()

CANDIDATE_KENJI = CandidateData(
    name="Kenji Tanaka",
    cv_text=KENJI_TANAKA_CV_TEXT,
    big_five=None,
    personality_source=None,
)

ALL_CANDIDATES: list[CandidateData] = [CANDIDATE_MARCUS, CANDIDATE_SARAH, CANDIDATE_KENJI]
