"""VP of Operations scenario fixture — SwiftHaul (3PL turnaround).

Self-contained fixture for a margin-recovery turnaround at a $280M regional 3PL:
- Patricia Hawkins: strong fit — proven turnaround exec, Six Sigma Black Belt, large-team DC leadership
- Ahmed Hassan: partial fit — deep e-commerce ops, no turnaround or fleet experience
- Yuki Tanaka: stretch — small-scale courier ops manager, no P&L ownership, no Big Five

Designed to produce 12-14 extractable requirements covering: P&L ownership, network
rationalization, fleet management, cost reduction, team leadership, WMS/TMS systems,
lean/six sigma, labor relations, safety/compliance, SLA management, vendor negotiation,
and behavioral requirements around hard decisions, morale, and communication.
"""

from shared.models.candidates import BigFiveScores, CandidateData
from shared.models.requirements import Priority, Requirement, ScenarioPriority
from shared.models.rubric import Confidence, RubricAssessment, RubricLevel
from shared.models.scenarios import ScenarioConfig, ScenarioName

# ---------------------------------------------------------------------------
# Job Description
# ---------------------------------------------------------------------------

JD_TEXT: str = """
SwiftHaul Logistics — Vice President of Operations

Location: Atlanta, GA (HQ) with regular travel to 14 distribution centres across the US Southeast
Reports to: Chief Operating Officer
Direct reports: 4 Regional Operations Directors, 1 Safety & Compliance Manager (~340 total ops staff)

About SwiftHaul

SwiftHaul is a third-party logistics (3PL) provider operating across the US Southeast,
managing freight, warehousing, and last-mile delivery for regional retail, manufacturing,
and e-commerce clients. Revenue stands at $280M with 2,400 employees, including 1,800
warehouse associates and fleet drivers across 14 distribution centres in Georgia, Florida,
Tennessee, North Carolina, Alabama, and South Carolina.

Over the past two years, rapid geographic expansion drove headcount and DC footprint
beyond what our revenue base could sustain. Operating margins have compressed from
12% to 4%, putting the business under severe board pressure. The incoming VP of
Operations will lead a disciplined network rationalization, cost restructuring, and
operational excellence programme designed to return SwiftHaul to 9% operating margin
within 18 months — while protecting the client relationships and service levels that
define our competitive position in the market.

This is not a maintenance role. We need a proven turnaround operator who has made hard
decisions before — site closures, workforce reductions, carrier contract renegotiations
— and who can do so with the discipline and empathy required to maintain organisational
trust during a difficult period.

The Role

The VP of Operations owns the full operational P&L for SwiftHaul's warehouse and
distribution network. You will serve as the senior operational decision-maker for
network design, cost structure, labour strategy, fleet management, and compliance across
all 14 DC locations. You will work directly with the COO and CFO on the turnaround
programme and present operational performance to the board on a quarterly basis.

Key Responsibilities

- Own the operational P&L (budgetary accountability of $110M annually), delivering against
  margin recovery targets set by the board; present monthly performance to COO and
  quarterly to the board.
- Lead a comprehensive network rationalization: evaluate all 14 DCs against contribution
  margin, throughput utilisation, and strategic fit; recommend and execute closures,
  consolidations, or capacity reductions within 90 days of start.
- Drive a minimum 20% reduction in controllable operating costs within the first 12 months
  without violating SLAs or triggering client attrition above 5%.
- Manage the fleet operation (310 vehicles, mix of owned and leased), including
  route optimisation, preventive maintenance scheduling, fuel cost management, and
  carrier partner negotiations to reduce fleet cost per mile by at least 12%.
- Lead, develop, and retain a 340-person operations team across Regional Directors,
  warehouse supervisors, and front-line staff; maintain engagement and retention during
  the restructuring.
- Implement or upgrade Warehouse Management System (WMS) and Transportation Management
  System (TMS) capabilities to enable data-driven throughput optimisation and SLA
  reporting; current environment includes legacy Manhattan Associates WMS and a
  partially deployed Oracle TMS.
- Apply lean operations and continuous improvement methodology (Six Sigma or equivalent)
  to eliminate waste across pick-pack, loading, routing, and dwell-time processes;
  target a 15% improvement in labour productivity within 18 months.
- Manage all labor relations and workforce planning activity, including union and
  non-union employee relations at 6 facilities, scheduling, overtime management,
  and workforce reduction processes conducted in compliance with applicable WARN Act
  and state notification requirements.
- Ensure full compliance with OSHA workplace safety regulations and DOT fleet
  regulations across all facilities and vehicles; target a lost-time injury rate
  below 1.5 per 100 FTE and maintain a satisfactory DOT safety rating.
- Manage SLAs across all client accounts during the restructuring period; coordinate
  with the commercial team to retain at least 95% of contracted revenue through
  the network transition.
- Lead carrier and vendor negotiations — third-party linehaul, drayage, packaging
  suppliers, fuel hedging — targeting aggregate cost reduction of 8-12% across
  indirect spend categories.

Required Qualifications

- 12+ years of progressive operations leadership in logistics, supply chain, or
  3PL environments, with at least 4 years at Director or VP level.
- Demonstrated P&L ownership at $100M+ scale; track record of delivering measurable
  cost reduction (15%+ improvement) in a constrained or declining margin environment.
- Experience leading network rationalization — including DC closures, consolidations,
  or capacity reductions — with documented results.
- Fleet management expertise: owned/leased mixed fleet of 150+ vehicles, including
  DOT compliance, driver management, route optimisation, and cost-per-mile accountability.
- Proven leadership of large, distributed operations teams (200+ headcount across
  multiple sites); track record of maintaining performance through change.
- Hands-on experience with enterprise WMS and TMS platforms (Manhattan Associates,
  Oracle TMS, or comparable tier-1 systems).
- Lean/Six Sigma certification (Green Belt minimum; Black Belt strongly preferred);
  demonstrated application to warehousing or transportation processes.
- Experience managing labour relations in union and non-union environments; working
  knowledge of WARN Act obligations and workforce reduction compliance.
- Strong safety culture leadership; demonstrable improvement in OSHA recordable and
  lost-time injury rates.
- Experience managing SLA performance for multi-client accounts during periods of
  operational disruption or restructuring.
- Vendor and carrier negotiation experience with documented savings outcomes.

Desired Attributes

- Demonstrated ability to make and execute hard operational decisions — site closures,
  workforce reductions, carrier exits — with speed, fairness, and clear rationale.
- Track record of maintaining team morale, engagement, and retention during cost
  restructuring programmes; ability to hold difficult conversations without losing
  the confidence of the team.
- Transparent, structured communicator able to present operational complexity clearly
  to board-level audiences, front-line teams, and external clients simultaneously.
""".strip()

# ---------------------------------------------------------------------------
# Requirements (ground-truth extraction — as would be produced by Stage C1)
# ---------------------------------------------------------------------------

REQUIREMENTS: list[Requirement] = [
    Requirement(
        requirement_id="REQ-01",
        text="P&L ownership at $100M+ operational budget scale with margin improvement track record",
        source_quote="Demonstrated P&L ownership at $100M+ scale; track record of delivering measurable cost reduction (15%+ improvement) in a constrained or declining margin environment.",
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
        requirement_id="REQ-02",
        text="DC network rationalization experience (closures, consolidations, capacity reductions)",
        source_quote="Experience leading network rationalization — including DC closures, consolidations, or capacity reductions — with documented results.",
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
        requirement_id="REQ-03",
        text="Fleet management of 150+ vehicle mixed fleet with DOT compliance and cost-per-mile accountability",
        source_quote="Fleet management expertise: owned/leased mixed fleet of 150+ vehicles, including DOT compliance, driver management, route optimisation, and cost-per-mile accountability.",
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
        requirement_id="REQ-04",
        text="Leadership of 200+ person distributed operations team across multiple sites",
        source_quote="Proven leadership of large, distributed operations teams (200+ headcount across multiple sites); track record of maintaining performance through change.",
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
        requirement_id="REQ-05",
        text="WMS/TMS platform experience (Manhattan Associates, Oracle TMS, or tier-1 equivalent)",
        source_quote="Hands-on experience with enterprise WMS and TMS platforms (Manhattan Associates, Oracle TMS, or comparable tier-1 systems).",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.HIGH,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.MEDIUM,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-06",
        text="Lean/Six Sigma certification (Green Belt minimum; Black Belt preferred) applied to logistics",
        source_quote="Lean/Six Sigma certification (Green Belt minimum; Black Belt strongly preferred); demonstrated application to warehousing or transportation processes.",
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
        requirement_id="REQ-07",
        text="Labor relations experience in union and non-union environments with WARN Act compliance",
        source_quote="Experience managing labour relations in union and non-union environments; working knowledge of WARN Act obligations and workforce reduction compliance.",
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
        requirement_id="REQ-08",
        text="Safety culture leadership with measurable OSHA recordable and lost-time injury improvement",
        source_quote="Strong safety culture leadership; demonstrable improvement in OSHA recordable and lost-time injury rates.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.MEDIUM,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-09",
        text="SLA management across multi-client accounts during operational disruption or restructuring",
        source_quote="Experience managing SLA performance for multi-client accounts during periods of operational disruption or restructuring.",
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
        text="Vendor and carrier negotiation with documented savings outcomes",
        source_quote="Vendor and carrier negotiation experience with documented savings outcomes.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.MEDIUM,
            growth=Priority.MEDIUM,
        ),
    ),
    Requirement(
        requirement_id="REQ-11",
        text="12+ years progressive operations leadership in logistics/3PL with 4+ years at Director/VP level",
        source_quote="12+ years of progressive operations leadership in logistics, supply chain, or 3PL environments, with at least 4 years at Director or VP level.",
        assessable_from_cv=True,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.HIGH,
        ),
    ),
    Requirement(
        requirement_id="REQ-12",
        text="Ability to make and execute hard operational decisions (closures, reductions) with speed and fairness",
        source_quote="Demonstrated ability to make and execute hard operational decisions — site closures, workforce reductions, carrier exits — with speed, fairness, and clear rationale.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.LOW,
            post_acquisition=Priority.MEDIUM,
            turnaround=Priority.HIGH,
            stabilization=Priority.MEDIUM,
            growth=Priority.LOW,
        ),
    ),
    Requirement(
        requirement_id="REQ-13",
        text="Maintaining team morale and retention during cost restructuring programmes",
        source_quote="Track record of maintaining team morale, engagement, and retention during cost restructuring programmes; ability to hold difficult conversations without losing the confidence of the team.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.LOW,
        ),
    ),
    Requirement(
        requirement_id="REQ-14",
        text="Transparent communication across board, front-line teams, and external clients simultaneously",
        source_quote="Transparent, structured communicator able to present operational complexity clearly to board-level audiences, front-line teams, and external clients simultaneously.",
        assessable_from_cv=False,
        scenario_priority=ScenarioPriority(
            digital_transformation=Priority.MEDIUM,
            post_acquisition=Priority.HIGH,
            turnaround=Priority.HIGH,
            stabilization=Priority.HIGH,
            growth=Priority.MEDIUM,
        ),
    ),
]

# ---------------------------------------------------------------------------
# Candidate A — Patricia Hawkins (Strong Fit)
# ---------------------------------------------------------------------------

PATRICIA_HAWKINS_CV_TEXT: str = """
PATRICIA HAWKINS
VP of Operations | Third-Party Logistics & Distribution Network Turnarounds

PROFESSIONAL SUMMARY
Seasoned operations executive with 18 years in logistics and 3PL environments. Built a
reputation for margin recovery and disciplined network rationalization. Led a $90M
operational cost restructuring that restored a struggling mid-size 3PL from near-insolvency
to sustained double-digit margins. Six Sigma Black Belt with deep WMS/TMS implementation
expertise and a direct, people-first approach to managing change.

PROFESSIONAL EXPERIENCE

Vice President of Operations — Meridian Freight Partners, Charlotte, NC (2019–Present)
Meridian is a Southeast regional 3PL with $400M revenue, 8 distribution centres, and a
310-vehicle owned/leased fleet serving retail, CPG, and e-commerce clients.

- Inherited a 5% operating margin following aggressive geographic expansion in 2017-2018.
  Designed and executed a 14-month turnaround programme that returned the business to
  11% operating margin by Q4 2020.
- Reduced controllable operating costs by 22% ($90M absolute reduction) through DC
  network consolidation, labour productivity improvement, and carrier renegotiation.
- Closed 3 underperforming distribution centres (Memphis TN, Savannah GA, Augusta GA)
  after contribution margin analysis; redeployed 60% of displaced staff to retained sites,
  reducing severance liability while maintaining workforce trust.
- Lead a 340-person operations organisation across 4 Regional Directors, site managers,
  and ~280 warehouse and fleet associates.
- Manage full operational P&L ($110M annually); present monthly operational KPIs to COO
  and quarterly performance to the board of directors.
- Negotiated new carrier contracts with 6 linehaul providers and 3 drayage partners,
  achieving 14% aggregate rate reduction and dynamic rate adjustments tied to fuel indices.
- Led Oracle TMS deployment across all sites over 9 months (replacing 3 legacy systems);
  improved route optimisation, reducing fleet cost per mile by 16%.
- Maintained Manhattan Associates WMS across all sites; drove a pick-accuracy improvement
  from 96.8% to 99.4% over 18 months through process redesign and supervisor coaching.
- Managed workforce reduction of 85 positions across 3 closed sites in compliance with
  WARN Act obligations; collaborated with legal and HR to execute 60-day notices and
  severance packages; zero employment litigation.
- Reduced lost-time injury rate from 3.2 to 1.1 per 100 FTE over 3 years through a
  mandatory safety observation programme and revised onboarding for new hires.
- Negotiated with union representatives at 2 unionised facilities (UFCW Local 204) on
  schedule changes, overtime caps, and part-time conversion — reached agreement in all
  cases without work stoppages.

Senior Director, Distribution Operations — AmeriCore Logistics, Atlanta, GA (2014–2019)
AmeriCore is a national 3PL with $1.1B revenue and 22 DCs.

- Directed operations for 5 Southeast DCs (Atlanta, Birmingham, Jacksonville, Nashville,
  Tampa); combined headcount of 220 direct reports.
- Reduced per-unit handling cost by 18% through Six Sigma DMAIC projects targeting
  dwell time and cross-dock cycle times at three facilities.
- Managed SLA compliance for 12 client accounts during a 7-month IT migration; achieved
  99.1% on-time delivery rate versus 97% contractual threshold.
- Oversaw fleet operations for 180-vehicle mixed fleet in the Southeast region; introduced
  driver behaviour telematics, cutting fuel consumption by 9% and reducing at-fault
  incidents by 34%.
- Maintained DOT satisfactory safety rating across all audits; achieved OSHA VPP Star
  recognition at the Atlanta facility.

Operations Manager — FastPath Distribution, Greenville, SC (2011–2014)
- Managed a single 350,000 sq ft DC with 90 associates and a 40-vehicle local delivery fleet.
- Led a Lean transformation of the inbound receiving process, reducing dock-to-shelf cycle
  time by 31% and eliminating 12,000 hours of annual labour waste.
- Promoted to Senior Ops Manager within 14 months; site recognised as top-performing
  facility in the FastPath Southeast region in 2013.

Logistics Supervisor — Inland Distribution Group, Columbia, SC (2007–2011)

EDUCATION
- MBA, Operations & Supply Chain — Georgia State University, Robinson College of Business (2009)
- BS, Industrial Engineering — Clemson University (2006)

CERTIFICATIONS
- Six Sigma Black Belt — American Society for Quality (ASQ), 2013
- OSHA 30-Hour General Industry, 2015 (renewed 2021)
- APICS CSCP (Certified Supply Chain Professional), 2016
""".strip()

PATRICIA_HAWKINS_BIG_FIVE = BigFiveScores(
    O=0.42,  # Below-average openness — pragmatic operator, prefers proven methods
    C=0.88,  # Very high conscientiousness — disciplined, systematic execution
    E=0.65,  # Moderate extraversion — confident in leadership, direct communicator
    A=0.38,  # Low agreeableness — willing to make hard calls, challenges pushback
    N=0.20,  # Very low neuroticism — steady under pressure and difficult decisions
)

CANDIDATE_PATRICIA = CandidateData(
    name="Patricia Hawkins",
    cv_text=PATRICIA_HAWKINS_CV_TEXT,
    big_five=PATRICIA_HAWKINS_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate B — Ahmed Hassan (Partial Fit)
# ---------------------------------------------------------------------------

AHMED_HASSAN_CV_TEXT: str = """
AHMED HASSAN
Director of Supply Chain & Operations | E-Commerce Fulfillment & Automation

PROFESSIONAL SUMMARY
Results-driven operations leader with 12 years building and scaling high-velocity
fulfillment operations for e-commerce businesses. Deep expertise in warehouse automation,
WMS optimisation, and inventory management at speed and scale. Adept at leading
cross-functional teams through rapid growth and system transformation. Seeking to apply
fulfillment expertise to a larger, more complex operational environment.

PROFESSIONAL EXPERIENCE

Director, Supply Chain Operations — Luxe Retail Group, Atlanta, GA (2020–Present)
Luxe is a direct-to-consumer apparel and home goods brand with $320M in annual GMV,
operating 3 fulfillment centres (Atlanta, Dallas, Ontario CA) and using a hybrid
carrier model (UPS, FedEx, regional partners) for all outbound shipments. No owned fleet.

- Lead end-to-end supply chain and fulfillment operations for 3 FCs with a combined
  150-person team (3 site managers, 12 supervisors, ~130 associates).
- Own $42M operational budget covering labour, consumables, systems, and third-party
  carrier spend; delivered 8% cost savings in FY2023 through carrier rate negotiation
  and labour scheduling optimisation.
- Oversaw deployment of a new Infor WMS across all 3 sites over 14 months; achieved
  full cutover with zero SLA breaches; improved order accuracy from 97.2% to 99.6%.
- Drove robotics pilot (Locus autonomous mobile robots) at Atlanta FC, reducing pick
  labour hours per unit by 28%; programme now expanding to Dallas.
- Managed peak season operations (Black Friday / Cyber Monday) processing 45,000 orders/day
  across all FCs with 99.3% same-day ship compliance — up from 96.8% the prior year.
- Reduced carrier cost per shipment by 11% through renegotiated agreements with UPS,
  OnTrac, and regional LTL partners; introduced multi-carrier rate shopping via ShipBob.
- Maintained OSHA compliance across all sites; zero OSHA recordable incidents in 2022
  and 2023; implemented near-miss reporting culture that generated 140+ improvement ideas.

Senior Manager, Fulfillment Operations — NovaBuy.com, Chicago, IL (2016–2020)
NovaBuy is a marketplace e-commerce platform with $800M GMV, 2 fulfillment centres
(Chicago and Columbus), and 3rd-party carrier partners for all outbound.

- Managed 2 FC sites with combined 120 associates; drove throughput from 18,000 to
  31,000 units/day across 2 years.
- Led Six Sigma Green Belt project to reduce mis-sort rate at Chicago FC by 62%;
  estimated annual savings of $480K.
- Partnered with WMS vendor (HighJump) to implement slotting optimisation; cut average
  pick path distance by 22%.
- Developed a dynamic labour model using historical order volume patterns; reduced
  overtime spend by 17% while maintaining SLA compliance above 98.5%.
- Managed a 90-day peak-season expansion that added 80 temporary associates at 2 sites;
  maintained quality and compliance throughout ramp.

Operations Analyst → Fulfillment Manager — Dispatch Technologies, New York, NY (2013–2016)
- Joined as analyst modelling fulfillment capacity and carrier cost scenarios;
  promoted to Fulfillment Manager in 2014 managing 35 associates at a single NYC warehouse.
- Built the company's first SLA tracking dashboard; reduced SLA breach rate from 4.1%
  to 0.9% in 6 months.

EDUCATION
- MS, Supply Chain Management — Northwestern University, Kellogg (2013)
- BS, Industrial Engineering — University of Illinois Urbana-Champaign (2011)

CERTIFICATIONS
- Six Sigma Green Belt — ASQ, 2018
- APICS CPIM (Certified in Production and Inventory Management), 2017
""".strip()

AHMED_HASSAN_BIG_FIVE = BigFiveScores(
    O=0.65,  # Above-average openness — drawn to automation and tech innovation
    C=0.80,  # High conscientiousness — systematic, metric-driven
    E=0.58,  # Moderate extraversion — collaborative team leader
    A=0.62,  # Above-average agreeableness — consensus-oriented, avoids hard conflict
    N=0.25,  # Low neuroticism — composed under operational pressure
)

CANDIDATE_AHMED = CandidateData(
    name="Ahmed Hassan",
    cv_text=AHMED_HASSAN_CV_TEXT,
    big_five=AHMED_HASSAN_BIG_FIVE,
    personality_source="manual",
)

# ---------------------------------------------------------------------------
# Candidate C — Yuki Tanaka (Stretch / Partial Mode)
# ---------------------------------------------------------------------------

YUKI_TANAKA_CV_TEXT: str = """
YUKI TANAKA
Operations Manager | Regional Courier & Last-Mile Delivery

PROFESSIONAL SUMMARY
Dedicated operations professional with 9 years of progressive experience in courier
and last-mile delivery. Passionate about fleet safety, route efficiency, and building
cohesive frontline teams. Known for building strong safety cultures and maintaining
operational consistency in fast-moving environments. Looking to take on a broader
leadership role in a larger logistics organisation.

PROFESSIONAL EXPERIENCE

Senior Operations Manager — RapidRoute Courier Services, Atlanta, GA (2020–Present)
RapidRoute is a regional courier and same-day delivery provider with $15M revenue,
3 depots (Atlanta, Macon, Savannah), an 80-person workforce, and a 55-vehicle fleet.

- Oversee all daily operations across 3 depot locations; manage a team of 80 including
  3 depot supervisors, 12 lead drivers, and ~65 couriers and dock staff.
- Report to the CEO (company is privately held, no formal COO layer); present weekly
  operational metrics in management meetings.
- Redesigned route structure for Atlanta and Savannah using OptimoRoute software,
  reducing average kilometres per delivery by 17% and cutting fuel spend by $88K
  annually.
- Built a preventive maintenance programme for the 55-vehicle fleet; reduced
  unscheduled downtime from 9.4% to 3.2% of fleet hours over 18 months.
- Achieved zero lost-time injuries across all 3 depots for 4 consecutive years
  (2021-2024); implemented daily pre-shift safety huddles and monthly incident review
  boards.
- Maintained a satisfactory DOT safety rating across the full fleet; no out-of-service
  violations in 3 years.
- Managed peak volume periods (holiday, back-to-school) with ad hoc driver additions
  and temporary route extensions without SLA degradation.
- Reduced driver turnover from 34% to 18% annually by improving onboarding, scheduling
  predictability, and informal recognition programmes.

Operations Coordinator → Depot Manager — FastTrack Parcel, Nashville, TN (2016–2020)
- Started as Operations Coordinator, promoted to Depot Manager in 2017 overseeing a
  single Nashville depot with 35 drivers and a 22-vehicle fleet.
- Introduced driver performance scorecards (on-time, route efficiency, customer complaints);
  on-time delivery rate improved from 91% to 97.3% over 18 months.
- Partnered with IT to implement a digital proof-of-delivery (ePOD) system; eliminated
  $12K/year in disputed delivery claims.
- Managed seasonal staffing increases of 40-50% during peak periods; maintained
  compliance and productivity throughout.

Courier / Driver Lead — Metro Express Delivery, Atlanta, GA (2015–2016)
- Senior driver and informal team lead for a 12-vehicle evening delivery crew.

EDUCATION
- BS, Business Administration (Operations) — Georgia State University (2015)

CERTIFICATIONS
- DOT Supervisor Reasonable Suspicion Training, 2019 (renewed 2023)
- OSHA 10-Hour General Industry, 2020
- OptimoRoute Certified Planner, 2021
""".strip()

CANDIDATE_YUKI = CandidateData(
    name="Yuki Tanaka",
    cv_text=YUKI_TANAKA_CV_TEXT,
    big_five=None,
    personality_source=None,
)

# ---------------------------------------------------------------------------
# All candidates list
# ---------------------------------------------------------------------------

ALL_CANDIDATES: list[CandidateData] = [CANDIDATE_PATRICIA, CANDIDATE_AHMED, CANDIDATE_YUKI]

# ---------------------------------------------------------------------------
# Ground-truth rubric assessments (as would be produced by Stage C3)
# ---------------------------------------------------------------------------

RUBRIC_ASSESSMENTS: list[RubricAssessment] = [
    # ---- Patricia Hawkins ----
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Manage full operational P&L ($110M annually); returned the business to 11% operating margin by Q4 2020 after 14-month turnaround; reduced controllable operating costs by 22%",
        cv_location="VP of Operations, Meridian Freight Partners",
        notes="Direct match: $110M P&L, 22% cost reduction from 5% to 11% margin in 14 months",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Closed 3 underperforming distribution centres (Memphis TN, Savannah GA, Augusta GA) after contribution margin analysis; redeployed 60% of displaced staff to retained sites",
        cv_location="VP of Operations, Meridian Freight Partners",
        notes="Exact match: 3 DC closures with documented rationale and staff redeployment outcome",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Led Oracle TMS deployment across all sites; reducing fleet cost per mile by 16%; maintained 310-vehicle owned/leased fleet",
        cv_location="VP of Operations, Meridian Freight Partners",
        notes="310-vehicle mixed fleet, direct cost-per-mile improvement, DOT-satisfactory rating confirmed at prior role",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Lead a 340-person operations organisation across 4 Regional Directors, site managers, and ~280 warehouse and fleet associates",
        cv_location="VP of Operations, Meridian Freight Partners",
        notes="340 headcount across 8 DCs — exceeds 200+ requirement",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Led Oracle TMS deployment across all sites over 9 months; maintained Manhattan Associates WMS across all sites; drove pick-accuracy improvement from 96.8% to 99.4%",
        cv_location="VP of Operations, Meridian Freight Partners",
        notes="Named systems match exactly: Manhattan Associates WMS and Oracle TMS — same systems referenced in JD",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Six Sigma Black Belt — American Society for Quality (ASQ), 2013; reduced per-unit handling cost by 18% through Six Sigma DMAIC projects targeting dwell time and cross-dock cycle times",
        cv_location="Certifications / Senior Director, AmeriCore Logistics",
        notes="Black Belt (highest level sought); applied in a direct warehousing/distribution context",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Managed workforce reduction of 85 positions in compliance with WARN Act obligations; Negotiated with union representatives at 2 unionised facilities (UFCW Local 204) — reached agreement without work stoppages",
        cv_location="VP of Operations, Meridian Freight Partners",
        notes="Both union negotiation and WARN Act compliance directly documented",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Reduced lost-time injury rate from 3.2 to 1.1 per 100 FTE over 3 years; OSHA VPP Star recognition at the Atlanta facility",
        cv_location="VP of Operations, Meridian Freight Partners / Senior Director, AmeriCore Logistics",
        notes="Quantified LTI improvement and voluntary protection programme recognition — strong evidence",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.MEDIUM,
        cv_citation="Managed SLA compliance for 12 client accounts during a 7-month IT migration; achieved 99.1% on-time delivery rate",
        cv_location="Senior Director, AmeriCore Logistics",
        notes="Documented SLA management during disruption, though at prior (not current) role; no turnaround-specific SLA context at Meridian",
        investigation_question="Can Patricia speak to how SLAs were managed during the DC closures at Meridian, and what client attrition (if any) occurred?",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Negotiated new carrier contracts with 6 linehaul providers and 3 drayage partners, achieving 14% aggregate rate reduction",
        cv_location="VP of Operations, Meridian Freight Partners",
        notes="Specific savings percentage documented; scope (9 contracts) and carrier types align with JD",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="18 years operations/logistics; VP since 2019; Director 2014-2019",
        cv_location="Career timeline",
        notes="18 years total; 5+ years VP/Director in 3PL — exceeds both tenure and seniority requirements",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. DC closures and workforce reduction mentioned in CV, but decision-quality and emotional execution cannot be assessed from text alone.",
        investigation_question="Walk me through how you communicated the Memphis DC closure to the site team. What was the hardest part of the decision, and how did you handle resistance?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. 60% staff redeployment rate is a positive signal but morale/retention quality cannot be assessed from CV.",
        investigation_question="After the 3 site closures, how did you maintain engagement and retention among the staff who remained at active sites?",
    ),
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Patricia Hawkins",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Board-level presentation is documented but communication style and quality cannot be inferred from CV.",
        investigation_question="Describe how you communicated the turnaround plan and milestone progress to the board, the ops team, and clients simultaneously.",
    ),
    # ---- Ahmed Hassan ----
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Own $42M operational budget; delivered 8% cost savings in FY2023",
        cv_location="Director, Supply Chain Operations, Luxe Retail Group",
        notes="$42M budget vs. $100M+ requirement — significant scope gap; no margin recovery context, always in growth mode",
        investigation_question="Have you had accountability for an operational budget above $80M, or managed through a period of margin pressure requiring absolute cost reduction?",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No evidence of DC closures, network consolidation, or capacity reduction. All career experience has been in scaling-up or stable growth contexts.",
        investigation_question="Have you ever been responsible for closing or consolidating a fulfillment centre, or reducing a network footprint? If so, describe the process.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="E-commerce model uses carrier partners for all outbound — no owned or leased fleet. No fleet management, driver management, or DOT compliance experience cited anywhere in CV.",
        investigation_question="Do you have experience managing an owned or leased vehicle fleet, including DOT compliance, driver management, and cost-per-mile accountability?",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Lead end-to-end supply chain and fulfillment operations for 3 FCs with a combined 150-person team",
        cv_location="Director, Supply Chain Operations, Luxe Retail Group",
        notes="150 people across 3 sites — below 200+ threshold; no multi-DC leadership in turnaround or restructuring context",
        investigation_question="Largest team you have led across multiple sites simultaneously, and how did you maintain cohesion during organisational change?",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Oversaw deployment of a new Infor WMS across all 3 sites; partnered with WMS vendor (HighJump) to implement slotting optimisation",
        cv_location="Director, Luxe Retail Group / Senior Manager, NovaBuy.com",
        notes="WMS implementation experience present but with Infor/HighJump, not Manhattan Associates or Oracle TMS; no TMS experience (uses carrier APIs, not TMS)",
        investigation_question="Have you worked directly with Manhattan Associates WMS or Oracle TMS? How quickly do you typically come up to speed on a new WMS platform?",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Led Six Sigma Green Belt project to reduce mis-sort rate at Chicago FC by 62%; estimated annual savings of $480K",
        cv_location="Senior Manager, NovaBuy.com",
        notes="Green Belt (not Black Belt as preferred); applied in an e-commerce FC context, not a 3PL or fleet/DC network context",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No mention of union relations, WARN Act, or workforce reduction compliance anywhere in CV. E-commerce FCs are typically non-union and have not required reductions.",
        investigation_question="Have you managed employees in a unionised environment, or led a workforce reduction requiring WARN Act notification? Describe your experience.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.MEETS,
        confidence=Confidence.HIGH,
        cv_citation="Zero OSHA recordable incidents in 2022 and 2023; implemented near-miss reporting culture that generated 140+ improvement ideas",
        cv_location="Director, Supply Chain Operations, Luxe Retail Group",
        notes="Strong safety record, though at smaller scale; no explicit LTI rate improvement metrics provided",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Achieved full cutover [WMS] with zero SLA breaches; maintained SLA compliance above 98.5%",
        cv_location="Director, Luxe Retail Group / Senior Manager, NovaBuy.com",
        notes="SLA management experience is present but in a single-client (brand-to-consumer) or growth context, not multi-client 3PL. No restructuring or disruption SLA context.",
        investigation_question="Describe a situation where you had to manage client SLA commitments during a period of significant operational disruption. What was the outcome?",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="Reduced carrier cost per shipment by 11% through renegotiated agreements with UPS, OnTrac, and regional LTL partners",
        cv_location="Director, Supply Chain Operations, Luxe Retail Group",
        notes="Parcel/LTL carrier negotiation documented; no evidence of linehaul, drayage, or fuel hedging negotiation relevant to asset-heavy 3PL context",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="12 years operations; Director since 2020; Senior Manager 2016-2020",
        cv_location="Career timeline",
        notes="12 years total meets the floor; only 4 years at Director level (not VP); entire career in e-commerce, not 3PL",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. No evidence of hard decisions (closures, reductions) in CV — growth-only context makes this impossible to assess.",
        investigation_question="Have you ever had to make a decision that resulted in site closure, significant headcount reduction, or exiting a major vendor? How did you navigate it?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Collaborative leadership style is implied by tenure and team results, but no restructuring context exists to test this.",
        investigation_question="Tell me about a time when you had to maintain team morale during a period of significant change or uncertainty. What specifically did you do?",
    ),
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Ahmed Hassan",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. No board-level communication context cited; e-commerce Director role unlikely to involve board or client-facing simultaneous communication.",
        investigation_question="Describe your experience communicating complex operational plans to senior leadership and front-line teams simultaneously. What adjustments do you make?",
    ),
    # ---- Yuki Tanaka ----
    RubricAssessment(
        requirement_id="REQ-01",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No P&L ownership cited. Reports to CEO in a $15M revenue company; budget accountability not mentioned anywhere in CV.",
        investigation_question="Have you had any direct P&L or budget accountability? What is the largest budget you have managed, and how was financial performance reported?",
    ),
    RubricAssessment(
        requirement_id="REQ-02",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No DC consolidation, closure, or network rationalization experience. Three-depot regional courier — no capacity reduction decisions documented.",
        investigation_question="Have you ever evaluated whether a depot or facility should be closed or consolidated? Describe your involvement in any network-level decisions.",
    ),
    RubricAssessment(
        requirement_id="REQ-03",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Built a preventive maintenance programme for the 55-vehicle fleet; reduced unscheduled downtime from 9.4% to 3.2%; maintained a satisfactory DOT safety rating; route optimisation reducing average km per delivery by 17%",
        cv_location="Senior Operations Manager, RapidRoute Courier Services",
        notes="Strong fleet fundamentals and DOT compliance at small scale (55 vehicles vs 310+ required); no mixed owned/leased fleet cost-per-mile accountability at relevant scale",
    ),
    RubricAssessment(
        requirement_id="REQ-04",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.HIGH,
        cv_citation="Oversee all daily operations across 3 depot locations; manage a team of 80",
        cv_location="Senior Operations Manager, RapidRoute Courier Services",
        notes="80 people across 3 sites — well below 200+ requirement; no evidence of leading through significant change or restructuring",
    ),
    RubricAssessment(
        requirement_id="REQ-05",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="OptimoRoute (route planning tool) and ePOD system cited — these are not enterprise WMS/TMS platforms. No Manhattan Associates, Oracle TMS, or equivalent experience.",
        investigation_question="Have you worked with enterprise WMS or TMS platforms such as Manhattan Associates or Oracle TMS? What is your largest WMS/TMS implementation experience?",
    ),
    RubricAssessment(
        requirement_id="REQ-06",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No Six Sigma certification or equivalent continuous improvement methodology mentioned anywhere in CV.",
        investigation_question="Do you have any Lean or Six Sigma training or certification? Have you led formal continuous improvement projects?",
    ),
    RubricAssessment(
        requirement_id="REQ-07",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No union relations, WARN Act, or workforce reduction experience cited. Small courier company context makes this absence expected.",
        investigation_question="Have you managed employees in a unionised environment, or been involved in a significant workforce reduction? Describe any relevant experience.",
    ),
    RubricAssessment(
        requirement_id="REQ-08",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.EXCEEDS,
        confidence=Confidence.HIGH,
        cv_citation="Zero lost-time injuries across all 3 depots for 4 consecutive years (2021-2024); maintained a satisfactory DOT safety rating; no out-of-service violations in 3 years",
        cv_location="Senior Operations Manager, RapidRoute Courier Services",
        notes="Exceptional safety record is the standout strength in this profile; consistent zero-LTI for 4 years is demonstrably above threshold",
    ),
    RubricAssessment(
        requirement_id="REQ-09",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.PARTIAL,
        confidence=Confidence.MEDIUM,
        cv_citation="managed peak volume periods with ad hoc driver additions and temporary route extensions without SLA degradation",
        cv_location="Senior Operations Manager, RapidRoute Courier Services",
        notes="SLA maintenance during peak periods cited but not in a multi-client 3PL or disruption/restructuring context",
        investigation_question="Describe your experience managing service level commitments for multiple clients simultaneously. Have you ever had to manage SLAs during a period of operational disruption?",
    ),
    RubricAssessment(
        requirement_id="REQ-10",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation=None,
        cv_location=None,
        notes="No vendor or carrier negotiation mentioned. Small courier company purchasing at minimal scale with no documented savings.",
        investigation_question="Have you conducted carrier or vendor contract negotiations? Describe the largest procurement decision you have owned and the outcome.",
    ),
    RubricAssessment(
        requirement_id="REQ-11",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.GAP,
        confidence=Confidence.HIGH,
        cv_citation="9 years operations; Senior Operations Manager since 2020",
        cv_location="Career timeline",
        notes="9 years total falls short of the 12-year requirement; never held a Director or VP title; company size ($15M revenue) far below 3PL context required",
    ),
    RubricAssessment(
        requirement_id="REQ-12",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. No hard-decision context exists in CV to evaluate against.",
        investigation_question="Describe the hardest operational decision you have had to make. What made it difficult, and how did you execute it?",
    ),
    RubricAssessment(
        requirement_id="REQ-13",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Driver turnover improvement (34%→18%) is a positive signal for team engagement but is insufficient to assess restructuring-context morale management.",
        investigation_question="Describe a time when your team faced significant uncertainty or change. How did you maintain morale, and what was the outcome?",
    ),
    RubricAssessment(
        requirement_id="REQ-14",
        candidate_name="Yuki Tanaka",
        rubric_level=RubricLevel.NOT_ASSESSABLE,
        confidence=Confidence.LOW,
        cv_citation=None,
        cv_location=None,
        notes="Behavioral requirement. Reports to CEO in a small company context — no board, multi-stakeholder, or client-facing simultaneous communication experience.",
        investigation_question="Have you presented operational performance to senior leadership, clients, and frontline staff in the same period? How do you adjust your communication for each audience?",
    ),
]

# ---------------------------------------------------------------------------
# Ground-truth expectations
# ---------------------------------------------------------------------------

GROUND_TRUTH: dict[str, object] = {
    # Overall fit tier per candidate
    "fit_tiers": {
        "Patricia Hawkins": "strong",
        "Ahmed Hassan": "partial",
        "Yuki Tanaka": "stretch",
    },
    # Expected rubric levels per candidate per requirement
    "rubric_levels": {
        "Patricia Hawkins": {
            "REQ-01": RubricLevel.EXCEEDS,
            "REQ-02": RubricLevel.EXCEEDS,
            "REQ-03": RubricLevel.EXCEEDS,
            "REQ-04": RubricLevel.EXCEEDS,
            "REQ-05": RubricLevel.EXCEEDS,
            "REQ-06": RubricLevel.EXCEEDS,
            "REQ-07": RubricLevel.MEETS,
            "REQ-08": RubricLevel.EXCEEDS,
            "REQ-09": RubricLevel.MEETS,
            "REQ-10": RubricLevel.EXCEEDS,
            "REQ-11": RubricLevel.EXCEEDS,
            "REQ-12": RubricLevel.NOT_ASSESSABLE,
            "REQ-13": RubricLevel.NOT_ASSESSABLE,
            "REQ-14": RubricLevel.NOT_ASSESSABLE,
        },
        "Ahmed Hassan": {
            "REQ-01": RubricLevel.PARTIAL,
            "REQ-02": RubricLevel.GAP,
            "REQ-03": RubricLevel.GAP,
            "REQ-04": RubricLevel.PARTIAL,
            "REQ-05": RubricLevel.PARTIAL,
            "REQ-06": RubricLevel.PARTIAL,
            "REQ-07": RubricLevel.GAP,
            "REQ-08": RubricLevel.MEETS,
            "REQ-09": RubricLevel.PARTIAL,
            "REQ-10": RubricLevel.PARTIAL,
            "REQ-11": RubricLevel.PARTIAL,
            "REQ-12": RubricLevel.NOT_ASSESSABLE,
            "REQ-13": RubricLevel.NOT_ASSESSABLE,
            "REQ-14": RubricLevel.NOT_ASSESSABLE,
        },
        "Yuki Tanaka": {
            "REQ-01": RubricLevel.GAP,
            "REQ-02": RubricLevel.GAP,
            "REQ-03": RubricLevel.PARTIAL,
            "REQ-04": RubricLevel.PARTIAL,
            "REQ-05": RubricLevel.GAP,
            "REQ-06": RubricLevel.GAP,
            "REQ-07": RubricLevel.GAP,
            "REQ-08": RubricLevel.EXCEEDS,
            "REQ-09": RubricLevel.PARTIAL,
            "REQ-10": RubricLevel.GAP,
            "REQ-11": RubricLevel.GAP,
            "REQ-12": RubricLevel.NOT_ASSESSABLE,
            "REQ-13": RubricLevel.NOT_ASSESSABLE,
            "REQ-14": RubricLevel.NOT_ASSESSABLE,
        },
    },
    # Expected critical gaps per candidate — high-priority requirements with GAP or PARTIAL
    "critical_gaps": {
        "Patricia Hawkins": [],  # No critical gaps; turnaround-weighted reqs all met or exceeded
        "Ahmed Hassan": [
            "REQ-02",  # No network rationalization experience — HIGH turnaround priority
            "REQ-03",  # No fleet management — HIGH turnaround priority
            "REQ-07",  # No labor relations / WARN Act — HIGH turnaround priority
        ],
        "Yuki Tanaka": [
            "REQ-01",  # No P&L ownership — HIGH turnaround priority
            "REQ-02",  # No network rationalization — HIGH turnaround priority
            "REQ-05",  # No WMS/TMS — MEDIUM but disqualifying at VP scope
            "REQ-06",  # No Six Sigma — HIGH turnaround priority
            "REQ-07",  # No labor relations — HIGH turnaround priority
            "REQ-11",  # Experience depth gap — below 12-year / VP threshold
        ],
    },
    # Expected assessment mode per candidate
    "assessment_modes": {
        "Patricia Hawkins": "full",
        "Ahmed Hassan": "full",
        "Yuki Tanaka": "partial",  # No Big Five — partial mode
    },
    # Key differentiators to test flag generation
    "expected_flags": {
        "Patricia Hawkins": [
            "turnaround_operator",        # Proven margin recovery — positive execution flag
            "network_rationalization",    # 3 DC closures with documented outcomes
            "six_sigma_black_belt",       # Certification + applied evidence
            "hard_decision_track_record", # Closures + WARN Act reductions executed
            "low_agreeableness_high_c",   # A=0.38, C=0.88 — decisive under pressure profile
        ],
        "Ahmed Hassan": [
            "no_turnaround_experience",   # Always growth mode — experience gap flag
            "no_fleet_management",        # Fleet ownership never held
            "no_labor_union_experience",  # Labor relations gap
            "ecommerce_to_3pl_transition", # Domain shift risk
            "scale_gap_pl",               # $42M vs $110M P&L — experience gap
        ],
        "Yuki Tanaka": [
            "safety_excellence",          # 4-year zero-LTI record — standout positive
            "scale_gap_severe",           # 80 people / $15M vs 340 / $280M — large gap
            "no_pl_ownership",            # No budget accountability
            "no_wms_tms_experience",      # Route planning tool only
            "partial_mode_no_big_five",   # No personality assessment available
        ],
    },
}

# ---------------------------------------------------------------------------
# Scenario configuration
# ---------------------------------------------------------------------------

SCENARIO_CONFIG = ScenarioConfig(
    name=ScenarioName.TURNAROUND,
    category_weights={
        "EXECUTION": 1.8,       # Margin recovery is execution-driven — highest weight
        "EXPERIENCE_GAP": 1.6,  # Critical gaps disqualify in turnaround context
        "DERAILMENT": 1.5,      # Derailment risk elevated when hard decisions required
        "STRATEGIC": 1.2,       # Network design and P&L strategy matter
        "FRICTION": 1.3,        # Team conflict during restructuring elevated risk
        "CULTURAL": 0.9,        # Culture fit matters but secondary to execution
        "COMPLEMENT": 0.8,      # Team complement secondary to direct capability
        "GROUPTHINK": 0.7,      # Lower weight — turnaround needs decisive leader
        "COLLISION": 0.8,
        "DARK_SIDE": 1.4,       # Dark side traits elevated during sustained pressure
        "INTEGRATION": 0.6,     # Not an acquisition scenario
        "TENURE": 0.9,
        "EXPERIENCE_STRENGTH": 1.2,
        "EVIDENCE_QUALITY": 1.0,
        "ROUTING": 1.0,
    },
)

# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    "AHMED_HASSAN_BIG_FIVE",
    "AHMED_HASSAN_CV_TEXT",
    "ALL_CANDIDATES",
    "CANDIDATE_AHMED",
    "CANDIDATE_PATRICIA",
    "CANDIDATE_YUKI",
    "GROUND_TRUTH",
    "JD_TEXT",
    "PATRICIA_HAWKINS_BIG_FIVE",
    "PATRICIA_HAWKINS_CV_TEXT",
    "REQUIREMENTS",
    "RUBRIC_ASSESSMENTS",
    "SCENARIO_CONFIG",
    "YUKI_TANAKA_CV_TEXT",
]
