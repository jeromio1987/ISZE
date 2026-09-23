# Isuzu Universe - detailed task register

**21 September 2026 | Rewrite R1 | Planning record, not dispatch or acceptance**

All 42 Cursor and 24 ChatGPT task IDs are retained from the supplied orchestration register. Only C01-C07 are selected for R0. See 07_REVISION_NOTES.md for the commercial-only pilot sequencing change.

The JSON register carries the same dependencies and explicit conditional dependencies. Every linked-IDS use still requires approved identity and assessment evidence.

## P0 - Establish the truth

**Outcome:** A verified baseline and a point-by-point response to the original critique.

**Acceptance condition:** G0: the current build, available source packs and original paper/critique are reconciled. Each proposed change is already satisfied, required, deferred or unresolved. Missing originals keep the critique decision open.

### C01 | Cursor | Fingerprint the real baseline

**Planning state:** Ready. Not independently verified.

**Work:** Identify the actual entry point, stack, active branch or equivalent snapshot, dirty working tree, version labels and reproducible start commands. Do not reset or overwrite local work.

**Inputs:** Repository at the user-supplied root.

**Output:** BASELINE.md plus tracked-file or SHA-256 manifest.

**Acceptance:** A second reviewer can identify exactly which build was inspected. Version 2.2 is confirmed, corrected or left explicitly unverified.

**Dependencies:** None before inspection/drafting.

### C02 | Cursor | Return the original critique and paper

**Planning state:** Ready. Not independently verified.

**Work:** Read the exact critique path. Identify the paper it critiques from the file or repository; do not silently choose a different paper. Preserve both originals unchanged.

**Inputs:** Original critique and its referenced strategy paper.

**Output:** Original critique copy, exact paper identity, and CRITIQUE_INDEX.md with headings and source locations.

**Acceptance:** Every criticism can be traced to the original text; a missing paper is reported, not guessed.

**Dependencies:** None before inspection/drafting.

### C03 | Cursor | Inventory protected features and regressions

**Planning state:** Ready. Not independently verified.

**Work:** Record where the portfolio overview and Genuine/BVP comparisons live, how they work, and whether the sales cube is absent and photographs remain deferred. Capture existing journeys before change.

**Inputs:** Running baseline and existing tests.

**Output:** FEATURE_BASELINE.md and labelled screenshots.

**Acceptance:** Existing work is recorded as present, partial, absent or unverified; no working feature is put back into the backlog as a rebuild without justification.

**Dependencies:** None before inspection/drafting.

### C04 | Cursor | Catalogue source packs and supersession

**Planning state:** Ready. Not independently verified.

**Work:** Locate corrected tonnage v2 and the ITUK dealer-data/source-code pack. Inventory schemas, periods, source levels and correction evidence. Quarantine v1 from active ingestion without deleting originals.

**Inputs:** Pack manifests, read-me files, correction logs and source files.

**Output:** SOURCE_MANIFEST.json and PACK_STATUS.md.

**Acceptance:** The selected pack version and hash are explicit. Previously corrected v2 issues are marked resolved unless a new reproducible regression exists.

**Dependencies:** None before inspection/drafting.

### C05 | Cursor | Audit code reuse and PRISM boundaries

**Planning state:** Ready. Not independently verified.

**Work:** Read the available source code and PRISM overview. Identify useful existing components, transformations, routes, output contracts and coupling. Do not infer what PRISM does from its name.

**Inputs:** Actual application code and any PRISM documentation.

**Output:** REUSE_MAP.md with reuse, adapter, isolate or investigate recommendations.

**Acceptance:** Every recommendation cites a file or function. No framework rewrite or duplicate calculation engine is proposed without evidence.

**Dependencies:** None before inspection/drafting.

### C06 | Cursor | Reproduce the baseline run

**Planning state:** Planned. Not independently verified.

**Work:** Use documented local commands where available. Report test results, build errors, route failures and environment details. Do not install unknown dependencies or change configuration merely to manufacture a pass.

**Inputs:** C01 baseline and approved local environment.

**Output:** BASELINE_TEST_REPORT.md with commands, results and known limitations.

**Acceptance:** A failed or unavailable check remains visible; screenshots and a successful build are not represented as numerical validation.

**Dependencies:** C01

### C07 | Cursor | Package a compact evidence handoff

**Planning state:** Planned. Not independently verified.

**Work:** Assemble the baseline, critique, feature inventory, source manifests, reuse map and test report. Include only necessary safe samples; exclude credentials, caches and bulk unrelated data.

**Inputs:** C01-C06 outputs.

**Output:** A dated R0 review packet with MANIFEST.md and OPEN_QUESTIONS.md.

**Acceptance:** The packet is sufficient for ChatGPT to review without pretending it has local repository access. Missing items are listed.

**Dependencies:** C01, C02, C03, C04, C05, C06

### A01 | ChatGPT | Set the orchestration charter and current-state register

**Planning state:** Drafted. Specification draft available; not accepted.

**Work:** Separate reported baseline, agreed decisions, verified evidence and proposals. Define the handoff loop and release authority.

**Inputs:** Existing conversation decisions; later reconcile to C07.

**Output:** Current-state register and orchestration charter in this roadmap.

**Acceptance:** No repository inspection, critique review or Cursor dispatch is falsely claimed.

**Dependencies:** None before inspection/drafting.

### A02 | ChatGPT | Adjudicate the original critique point by point

**Planning state:** Blocked. Not independently verified.

**Work:** Read the original criticism alongside the exact paper and build evidence. Accept, partly accept, rebut with evidence, defer or flag each item as unverifiable.

**Inputs:** C02 originals; C03-C06 supporting evidence.

**Output:** CRITIQUE_RESPONSE.md with evidence, decision, affected ticket and acceptance test per item.

**Acceptance:** No criticism is invented or answered from a second-hand paraphrase. The original wording remains traceable.

**Dependencies:** C02, C07

### A03 | ChatGPT | Publish the verified maturity assessment

**Planning state:** Planned. Not independently verified.

**Work:** Assess product journeys, data readiness, mapping readiness, test coverage and deployment evidence separately. Report unknowns rather than an invented completion percentage.

**Inputs:** C07 review packet.

**Output:** STATE_OF_UNIVERSE.md and a feature evidence register.

**Acceptance:** Each status is tied to a build or artifact. Reported v2.2 and proposed milestones are not confused.

**Dependencies:** C07

### A04 | ChatGPT | Reconcile the backlog and decide G0

**Planning state:** Planned. Not independently verified.

**Work:** Close tasks already satisfied by evidence, retain real gaps and convert accepted critique points into scoped work orders.

**Inputs:** A02-A03 and all P0 evidence.

**Output:** Approved next work order and G0 disposition.

**Acceptance:** No repeated tonnage-v1 feedback, no automatic redesign, and no unreviewed product change enters the next packet.

**Dependencies:** A02, A03

## P1 - Certify the data meaning

**Outcome:** One clear contract for identity, periods, commercial levels and financial measures.

**Acceptance condition:** G1: approved metric definitions, source coverage, reconciled totals and executable data checks are available. Deliberately invalid examples fail; valid corrected examples pass.

### C08 | Cursor | Write dataset contracts

**Planning state:** Planned. Not independently verified.

**Work:** For each selected source, record grain, keys, measures, units, commercial level, reporting clock, coverage, freshness and provenance. Record whether a value is observed, derived or modelled.

**Inputs:** Approved source inventory and real schema samples.

**Output:** DATA_CONTRACTS.md plus machine-readable schema checks.

**Acceptance:** Every source used by a pilot view has a contract; no field meaning is inferred only from a convenient column name.

**Dependencies:** A04, C04

### C09 | Cursor | Normalize identifiers without destroying identity

**Planning state:** Planned. Not independently verified.

**Work:** Preserve part numbers and customer/dealer/site IDs as strings. Keep original and normalized values, leading zeros and collision reports. Apply only approved equivalence rules.

**Inputs:** C08 contracts and source identifier samples.

**Output:** Identifier transforms and collision/alias exception report.

**Acceptance:** Normalization is reversible or traceable; two unrelated entities are never merged because a name or country looks similar.

**Dependencies:** C08

### C10 | Cursor | Reconcile transactions at each commercial level

**Planning state:** Planned. Not independently verified.

**Work:** Reconcile raw-to-loaded quantities and values separately for ISZE-to-distributor and distributor-to-dealer data. Test duplicates, returns, credits, unit conversions and exclusions.

**Inputs:** Transaction sources and C08 contracts.

**Output:** RECONCILIATION.md plus executable reconciliation tests.

**Acceptance:** Reported totals match the declared source scope within an agreed rounding tolerance. No cross-level double counting or join fan-out occurs.

**Dependencies:** C08, C09

### C11 | Cursor | Make periods and coverage explicit

**Planning state:** Planned. Not independently verified.

**Work:** Identify complete months, partial extracts, CY/FY calendars, time zones where relevant, and currency/FX policy. Retain source currency and original period before any derived presentation conversion.

**Inputs:** Source contracts and refresh history.

**Output:** PERIOD_COVERAGE.md and shared period-filter tests.

**Acceptance:** One clock and period per measure; L12 is anchored to twelve complete eligible months, not assumed to be the latest calendar year.

**Dependencies:** C08, C10

### C12 | Cursor | Implement measure-basis metadata

**Planning state:** Planned. Not independently verified.

**Work:** Carry quantity, valuation basis, transaction level, reporting period, currency, population and source alongside every metric. Keep reference-price valuation separate from actual billing and modelled demand.

**Inputs:** A06 draft dictionary, approved after source review.

**Output:** Metric metadata interface and rendering fixtures.

**Acceptance:** An unpriced quantity never becomes euros; an indicative reference valuation never appears under an actual-revenue label.

**Dependencies:** A06, C08, C11

### C13 | Cursor | Provide lineage and exception evidence

**Planning state:** Planned. Not independently verified.

**Work:** Connect each displayed aggregate to source version, scope, transformations and exclusions. Keep unmatched parts/dealers, missing prices and ambiguous applicability visible in an exception ledger.

**Inputs:** C08-C12 outputs.

**Output:** Evidence record and EXCEPTIONS.md or equivalent table.

**Acceptance:** A reviewer can explain an aggregate without downloading confidential bulk data; excluded records remain countable and retrievable within permission.

**Dependencies:** C10, C12

### C14 | Cursor | Automate the non-negotiable data tests

**Planning state:** Planned. Not independently verified.

**Work:** Turn the approved business rules into tests, including null versus zero, duplicate joins, clocks, quantities versus euros, exclusive versus pooled applicability and repeated market actuals.

**Inputs:** A05-A08 decisions and C08-C13 transforms.

**Output:** DATA_INVARIANTS test suite and G1 evidence report.

**Acceptance:** Deliberately broken fixtures fail the relevant tests; valid corrected tonnage-v2 fixtures pass.

**Dependencies:** C13, A05, A06, A07, A08

### A05 | ChatGPT | Build the distributor source-coverage map

**Planning state:** Planned. Not independently verified.

**Work:** Declare which source levels, periods, dealer populations and measure bases are available per distributor. Decide which comparisons are eligible before any ranking.

**Inputs:** C04, C08 and C11.

**Output:** COVERAGE_MAP.md with eligible, restricted and unknown uses.

**Acceptance:** Missing dealer data is recorded as unknown downstream activity, not zero. Warranty is not used to infer scheduled servicing.

**Dependencies:** A04, C08, C11

### A06 | ChatGPT | Approve the metric and financial-basis dictionary

**Planning state:** Drafted. Specification draft available; not accepted.

**Work:** Define what each figure means, its formula, denominator and forbidden interpretations. Refine the draft in this roadmap against actual source contracts.

**Inputs:** Draft dictionary plus C08-C11 evidence.

**Output:** Approved METRIC_DICTIONARY.md.

**Acceptance:** Measured quantities, indicative valuation, actual billing and modelled expectation cannot be confused by wording or presentation.

**Dependencies:** C08, C10, C11

### A07 | ChatGPT | Test ITUK pilot eligibility

**Planning state:** Planned. Not independently verified.

**Work:** Profile the real ITUK data for grain, scope, periods, customer identity, values and source completeness. Select only justified dealer/site populations and measures.

**Inputs:** ITUK pack and C08-C11 reports.

**Output:** ITUK_PILOT_ELIGIBILITY.md with exclusions and unresolved questions.

**Acceptance:** A commercial-level pilot can proceed independently of IDS where dealer-to-IDS identity is not yet approved.

**Dependencies:** C08, C09, C10, C11

### A08 | ChatGPT | Review corrected tonnage v2 once, against evidence

**Planning state:** Planned. Not independently verified.

**Work:** Read the correction log and evidence before testing residual issues. Record closed corrections and test only remaining uncertainties or new regressions.

**Inputs:** Corrected tonnage v2, C04 and C13 evidence.

**Output:** TONNAGE_V2_DISPOSITION.md and G1 semantic decision.

**Acceptance:** No apportionment of shared parts; exclusive numerator uses the declared filter; CY and FY are not added; repeated market actuals remain context, not band numerator.

**Dependencies:** C04, C08, C13

## P2 - Prove a dealer pilot

**Outcome:** An ITUK dealer review connected to IDS only where identity is validated.

**Acceptance condition:** Full G2: the declared population reconciles, linked identities are approved, exclusions are visible and context survives the dealer-to-IDS journey. A commercial-only decision leaves full G2 open.

### C15 | Cursor | Create the approved dealer/customer/site bridge

**Planning state:** Planned. Not independently verified.

**Work:** Implement a versioned identity bridge with source IDs, entity type, parent/child relationships, validity dates, approval provenance and mapping status. Support unmatched and multi-site customers explicitly.

**Inputs:** A09 mapping policy and actual source identities.

**Output:** DEALER_SITE_BRIDGE plus validation report.

**Acceptance:** No country, submission cohort or fuzzy-name inference creates an approved relationship. Multi-site billing is not allocated to sites without evidence.

**Dependencies:** C14, A09

### C16 | Cursor | Ingest IDS as dated dealer assessments

**Planning state:** Planned. Not independently verified.

**Work:** Preserve assessment date, dealer/site identity, questionnaire version, section scores, response completeness and source. Do not overwrite previous assessments with only the latest value.

**Inputs:** Actual IDS source and scoring definitions.

**Output:** IDS assessment contract and validated snapshots.

**Acceptance:** A score retains its date, scoring version and assessed population; dealer self-assessment is not renamed a distributor audit.

**Dependencies:** C14, A09

### C17 | Cursor | Expose ambiguous and excluded joins

**Planning state:** Planned. Not independently verified.

**Work:** Provide a mapping review table for approved, unresolved, rejected and out-of-scope joins. Measure one-to-many and many-to-many risks before enabling linked views.

**Inputs:** C15-C16 joins.

**Output:** JOIN_EXCEPTIONS and pre/post-join reconciliation.

**Acceptance:** Unresolved records stay outside linked metrics while remaining visible; row fan-out cannot inflate quantities or values.

**Dependencies:** C15, C16

### C18 | Cursor | Build the dealer commercial review slice

**Planning state:** Planned. Not independently verified.

**Work:** Use the existing architecture to show dealer purchasing by eligible period, category, part and Genuine/BVP tier with source-basis labels and declared coverage. A commercial-only version can use an approved commercial customer/dealer identity without an IDS site link. Unsupported site detail remains unavailable.

**Inputs:** Approved ITUK pilot slice and A10 review specification.

**Output:** Dealer commercial view with source-reconciled fixtures.

**Acceptance:** This is distributor-to-dealer purchasing where supported, not dealer-to-end-customer sales or inferred servicing. Commercial identity is validated for the declared population; IDS linking is not a prerequisite for this commercial-only scope.

**Dependencies:** C14, A07, A10

### C19 | Cursor | Connect eligible IDS detail without scoring a distributor

**Planning state:** Planned. Not independently verified.

**Work:** Add the linked assessment summary and sections only for approved identities. Show assessment date, matched population and denominator for any aggregate.

**Inputs:** C16-C18 and A11 comparison rules.

**Output:** Dealer-to-IDS view and linked-population summary.

**Acceptance:** A distributor node remains commercial. Any dealer-assessment summary names its exact population, date basis and scoring scope.

**Dependencies:** C18, C17, A11

### C20 | Cursor | Preserve context across linked journeys

**Planning state:** Planned. Not independently verified.

**Work:** Retain distributor, dealer, sales period, taxonomy filters and financial basis across drill-through. Keep the assessment date independent from the sales clock.

**Inputs:** A10 journey and existing route/state architecture.

**Output:** Shareable route/state contract and journey tests.

**Acceptance:** Opening IDS cannot silently change the sales period; unmatched mappings produce an explanation, not a fake zero.

**Dependencies:** C18, C19

### C21 | Cursor | Return a representative pilot evidence set

**Planning state:** Planned. Not independently verified.

**Work:** Test approved normal, unmatched, multi-site, missing-price, returns and partial-period cases. Reconcile visible totals before and after joins and filters. State whether the packet covers commercial-only or linked-IDS scope. A commercial-only packet cannot claim completion of C19/C20 or full G2.

**Inputs:** C15-C20 and agreed sample selection.

**Output:** PILOT_EVIDENCE.md, fixtures and screenshots.

**Acceptance:** The sample includes edge cases rather than only clean success paths; the declared pilot population is reproducible.

**Dependencies:** C18, A10

**Additional dependencies for linked IDS scope:** C20, A11.

### A09 | ChatGPT | Define and approve identity-mapping rules

**Planning state:** Drafted. Specification draft available; not accepted.

**Work:** Separate distributor, commercial customer, dealer entity and physical site. Define the evidence needed for an approved link and route business ownership questions to Jerome or the responsible distributor.

**Inputs:** Draft policy here, source contracts and actual identity candidates.

**Output:** MAPPING_POLICY.md and mapping approval register.

**Acceptance:** ChatGPT does not invent site responsibility or certify a fuzzy match. Multi-site commercial facts stay at their measured grain.

**Dependencies:** C09, A07

### A10 | ChatGPT | Specify the connected dealer review

**Planning state:** Planned. Not independently verified.

**Work:** Define a review that answers what was purchased, how the mix changed, what IDS actually says, what evidence is missing, and what follow-up is agreed.

**Inputs:** A07 eligibility and existing dealer/IDS journeys.

**Output:** DEALER_REVIEW_SPEC.md with fields, states and acceptance examples.

**Acceptance:** Commercial and assessment evidence stay separate; the review gives a distributor useful monthly output rather than only requesting data.

**Dependencies:** A07, A09

### A11 | ChatGPT | Approve fair IDS comparisons

**Planning state:** Planned. Not independently verified.

**Work:** Define eligible scoring versions, section denominators, dated cohorts, missing-response treatment and whether entity/site aggregation is permissible. Do not imply causation from coincident scores and purchases.

**Inputs:** IDS definitions and C16-C17 evidence.

**Output:** IDS_COMPARISON_RULES.md.

**Acceptance:** The displayed comparator is named and reproducible; inconsistent questionnaires or undefined populations are not pooled.

**Dependencies:** C16, C17

### A12 | ChatGPT | Review pilot findings and decide G2

**Planning state:** Planned. Not independently verified.

**Work:** Review numerical, identity and interaction evidence. Separate a usable commercial pilot from a still-blocked IDS connection and decide the scope actually supportable.

**Inputs:** C21 and A09-A11.

**Output:** PILOT_REVIEW.md and G2 decision.

**Acceptance:** The decision states accepted scope, exclusions, unresolved mapping ownership and any rejected claims. A limited commercial-pilot decision leaves full G2 and unresolved IDS tasks open.

**Dependencies:** C21, A10

**Additional dependencies for linked IDS scope:** A11, C20.

## P3 - Make comparisons useful

**Outcome:** Preserved portfolio breadth, better Genuine/BVP comparisons and defensible commercial review.

**Acceptance condition:** G3: comparisons state applicability, units, period, financial basis and coverage. Modelled demand is not presented as measured loss; repeated market actuals never become band service cover.

### C22 | Cursor | Protect and strengthen the portfolio overview

**Planning state:** Planned. Not independently verified.

**Work:** Keep the existing overview and its navigation. Improve filters, coverage states and links to evidence only where the audit identifies a gap; avoid substituting a dealer-only homepage.

**Inputs:** C03 protected-feature baseline and approved metric contracts.

**Output:** Portfolio improvements with before/after regression evidence.

**Acceptance:** Existing supported portfolio journeys still work; no removed sales cube is reintroduced under a new name.

**Dependencies:** C14, C03

### C23 | Cursor | Build a documented Genuine/BVP relationship layer

**Planning state:** Planned. Not independently verified.

**Work:** Use validated relationship data, not name similarity alone. Record fitment/applicability, relationship type, units/pack, range validity, price availability and source.

**Inputs:** A13 eligibility policy and actual parts reference data.

**Output:** GENUINE_BVP_RELATIONSHIPS with exception register.

**Acceptance:** Only evidence-supported comparisons are eligible; missing BVP coverage is not filled with speculative substitutes.

**Dependencies:** C14, A13

### C24 | Cursor | Implement like-for-like comparisons

**Planning state:** Planned. Not independently verified.

**Work:** Show eligible Genuine/BVP unit prices, quantities and mix with common unit, currency, date and transaction/reference basis. Explain non-comparable cases in place.

**Inputs:** C23 plus approved financial metadata.

**Output:** Comparison view and numeric fixtures.

**Acceptance:** Reference-price differences are labelled indicative, not realized savings or actual customer prices. Different pack sizes are not compared unadjusted.

**Dependencies:** C23, C12

### C25 | Cursor | Show purchasing patterns with coverage context

**Planning state:** Planned. Not independently verified.

**Work:** Describe regular, intermittent and absent recorded purchasing only within a declared complete scope. Support seasonality and returns visibility without inferring end-customer demand.

**Inputs:** Eligible dealer/distributor transactions and coverage map.

**Output:** Purchasing-pattern view with explicit unknown states.

**Acceptance:** No recorded purchase is not labelled leakage automatically; stock, applicability, availability and source completeness remain review questions.

**Dependencies:** C14, A14

### C26 | Cursor | Integrate the three tonnage lenses safely

**Planning state:** Planned. Not independently verified.

**Work:** Expose recorded exclusive-applicability purchasing, modelled expected demand by band, and market actual purchasing as separate views. Reuse v2 corrections rather than recreating v1 transformations.

**Inputs:** Approved v2 disposition and real corrected files.

**Output:** Tonnage integration with regression fixtures.

**Acceptance:** Use sums_to_n_series_total == yes where specified; single_band_only is the exclusive numerator; also_fits_band is non-additive; shared records remain pooled.

**Dependencies:** C14, A08

### C27 | Cursor | Separate observed change, modelled potential and unknowns

**Planning state:** Planned. Not independently verified.

**Work:** Display evidence class alongside each candidate review item. Keep measured change distinct from reference-valued or modelled potential and unassessed gaps.

**Inputs:** A14 policy and approved metric metadata.

**Output:** Commercial-review candidate schema and view.

**Acceptance:** No modelled band gap becomes measured leakage, service cover or a distributor-performance ranking.

**Dependencies:** C24, C25, C26, A14

### C28 | Cursor | Export a defensible distributor review

**Planning state:** Planned. Not independently verified.

**Work:** Export the selected scope, comparison tables, source basis, coverage exceptions and evidence references. Keep sales levels and dates in headings, not hidden footnotes only.

**Inputs:** A16 storyboard and approved comparison views.

**Output:** Review export and verification fixtures.

**Acceptance:** An exported screenshot or table remains interpretable outside the app and contains only authorized population data.

**Dependencies:** C27, A16

### A13 | ChatGPT | Approve Genuine/BVP comparison eligibility

**Planning state:** Drafted. Specification draft available; not accepted.

**Work:** Define the minimum evidence for comparable range, fitment, pack unit, price basis, validity and availability. Distinguish documented alternatives from broader category comparisons.

**Inputs:** Draft policy here and actual relationship sources.

**Output:** COMPARISON_ELIGIBILITY.md with accepted and rejected examples.

**Acceptance:** A valid category comparison never silently asserts technical interchangeability or realized financial benefit.

**Dependencies:** C08, C12

### A14 | ChatGPT | Design honest opportunity prioritization

**Planning state:** Planned. Not independently verified.

**Work:** Classify review candidates by evidence strength and actionability. Require source coverage before rankings and define which additional facts are needed before discussing a commercial intervention.

**Inputs:** A05 coverage map and real purchasing/parts evidence.

**Output:** OPPORTUNITY_POLICY.md and review rubric.

**Acceptance:** Warranty, absent files, missing recorded purchasing and reference-valued gaps are not treated as proof of leakage.

**Dependencies:** A05, A06, A13

### A15 | ChatGPT | Challenge financial and service-demand conclusions

**Planning state:** Planned. Not independently verified.

**Work:** Trace representative displayed calculations to source. Test whether quantities, value bases, exclusive applicability and model assumptions support the stated conclusion.

**Inputs:** C24-C27 fixtures and source lineage.

**Output:** NUMERICAL_REVIEW.md and G3 calculation decision.

**Acceptance:** Every accepted claim is limited to its measured or modelled basis; repeated market actuals cannot become a band-specific ratio.

**Dependencies:** C27, A08

### A16 | ChatGPT | Define the distributor monthly-review story

**Planning state:** Planned. Not independently verified.

**Work:** Specify the practical return to distributors: connected dealer review, eligible Genuine/BVP comparison, purchasing-pattern discussion and owned follow-ups.

**Inputs:** A10, A14 and actual pilot capabilities.

**Output:** MONTHLY_REVIEW_STORYBOARD.md.

**Acceptance:** The story supports ISZE-to-distributor collaboration, not an invented direct-to-retail sales offer or complete-repair ordering workflow.

**Dependencies:** A10, A14

## P4 - Make the experience exceptional

**Outcome:** A distinctive, fast interface with trustworthy interactions and clear evidence.

**Acceptance condition:** G4: critical journeys pass visual, calculation, interaction, accessibility, performance and access checks on the selected scope. A screenshot alone does not prove interaction or numerical correctness.

### C29 | Cursor | Unify navigation without a framework rewrite

**Planning state:** Planned. Not independently verified.

**Work:** Implement a coherent path from portfolio to distributor context, eligible dealer, part/category evidence and action. Reuse actual shared components and existing routing where possible.

**Inputs:** C05 reuse map and A17-A18 UX specification.

**Output:** Navigation change with route regression tests.

**Acceptance:** A user can return to the portfolio without losing context; the implementation fits the audited stack rather than assuming a new one.

**Dependencies:** A17, A18, C22, C20, A12, A15

### C30 | Cursor | Apply a coherent visual system

**Planning state:** Planned. Not independently verified.

**Work:** Use restrained dark surfaces, clear typography, deliberate Isuzu-red emphasis and generous space as a proposed visual direction. Reconcile with existing approved design tokens before changing working screens.

**Inputs:** Approved existing design assets and A17 brief.

**Output:** Shared tokens and component examples.

**Acceptance:** Numerical hierarchy is legible, status is not color-only, and decorative treatment never hides labels or changes semantic meaning.

**Dependencies:** A17

### C31 | Cursor | Build signature views that reveal useful information

**Planning state:** Planned. Not independently verified.

**Work:** Prototype a stable portfolio composition view, a Genuine/BVP purchasing time trace and a linked dealer commercial/assessment view. Choose scales and encodings from the real measure contract.

**Inputs:** A18 interaction specification and validated data slices.

**Output:** Three evaluated view prototypes, retaining only those that improve the task.

**Acceptance:** Area, position and color have labelled meanings; IDS is not combined into a synthetic sales-performance score; a table alternative exists.

**Dependencies:** C30, A18, C24, C19

### C32 | Cursor | Add progressive detail and evidence drawers

**Planning state:** Planned. Not independently verified.

**Work:** Keep overview screens focused while making definitions, scope, price basis, match status, exclusions and lineage available in one consistent evidence drawer.

**Inputs:** C13 evidence record and A18 specification.

**Output:** Reusable evidence panel and interaction tests.

**Acceptance:** Critical basis labels remain visible without opening the drawer; the drawer adds detail rather than concealing caveats.

**Dependencies:** C29, C31, C13

### C33 | Cursor | Design every non-happy-path state

**Planning state:** Planned. Not independently verified.

**Work:** Implement empty, unknown, filtered-out, stale, partial-period, denied-access, ambiguous-join and calculation-error states. Provide meaningful recovery and preserve user context.

**Inputs:** Source contracts, access model and pilot edge cases.

**Output:** State catalogue with executable view tests.

**Acceptance:** Unknown data never renders as zero; errors do not expose secrets; stale evidence is not displayed as current without a label.

**Dependencies:** C32

### C34 | Cursor | Benchmark performance and accessibility

**Planning state:** Planned. Not independently verified.

**Work:** Measure real dataset size, startup, filtering and drill-through on an agreed reference machine. Test keyboard access, focus order, contrast, reduced motion and table alternatives. Optimize only measured bottlenecks.

**Inputs:** Baseline run, actual pilot build and A19 user tasks.

**Output:** PERFORMANCE_ACCESSIBILITY_REPORT.md with before/after evidence.

**Acceptance:** Budgets are agreed from the baseline, not claimed in advance; any virtualization or worker is justified by measured need.

**Dependencies:** C33, A19

### C35 | Cursor | Test access control and complete product regression

**Planning state:** Planned. Not independently verified.

**Work:** Check distributor/dealer data isolation in the actual deployment model, including exports and underlying data delivery. Re-run protected-feature, semantic and journey tests.

**Inputs:** Audited deployment architecture, C14 and completed pilot views.

**Output:** SECURITY_REGRESSION.md and G4 evidence packet.

**Acceptance:** Client-side hiding alone is not claimed as authorization. A cross-distributor account cannot fetch or export unauthorized rows.

**Dependencies:** C34, C28

### A17 | ChatGPT | Set the design brief against the existing baseline

**Planning state:** Planned. Not independently verified.

**Work:** Translate the desired distinctive presentation into a practical hierarchy, layout, density and motion brief. Identify what must stay unchanged and what genuinely needs improvement.

**Inputs:** C03 screenshots, current approved styling and pilot use cases.

**Output:** VISUAL_BRIEF.md and annotated review criteria.

**Acceptance:** The brief is grounded in actual screens; no claim is made that an unseen presentation theme has been matched exactly.

**Dependencies:** C03, A10, A16

### A18 | ChatGPT | Specify signature interactions and truth-preserving encodings

**Planning state:** Drafted. Specification draft available; not accepted.

**Work:** Define what each proposed graphic helps the user decide, its grain, axes or area, tooltip, drill-through and uncertainty states. Reject visuals that merely decorate missing evidence.

**Inputs:** Draft interaction rules here plus validated metric contracts.

**Output:** INTERACTION_SPEC.md.

**Acceptance:** No arbitrary 3D globe, force-layout relationship or merged score creates a false analytic relationship. Motion helps orientation and can be reduced.

**Dependencies:** A06, A10, A13

### A19 | ChatGPT | Define task-based usability acceptance

**Planning state:** Planned. Not independently verified.

**Work:** Write user tests for portfolio exploration, a like-for-like BVP comparison, a dealer-to-IDS review, an unknown-state explanation and a review export.

**Inputs:** A17-A18 and agreed ISZE/distributor tasks.

**Output:** USER_ACCEPTANCE_SCENARIOS.md.

**Acceptance:** Success means finding the right answer with its limitations, not merely clicking through a polished screen.

**Dependencies:** A17, A18

### A20 | ChatGPT | Review visual, numerical and interaction evidence

**Planning state:** Planned. Not independently verified.

**Work:** Inspect screenshots and returned run evidence against the brief and user tasks. Separate directly inspected appearance from interactions that still require local execution.

**Inputs:** C35 packet, screenshots and A19 scenarios.

**Output:** UX_REVIEW.md and G4 disposition.

**Acceptance:** No interaction is called tested solely from a screenshot, and no chart is accepted solely because it looks impressive.

**Dependencies:** C35, A19

## P5 - Operate and expand safely

**Outcome:** A repeatable monthly review, controlled refresh and evidence-based expansion.

**Acceptance condition:** G5: refresh and rollback are evidenced, operating responsibility is assigned, user acceptance is recorded and the business owner authorizes the declared release scope.

### C36 | Cursor | Make refreshes reproducible and safe

**Planning state:** Planned. Not independently verified.

**Work:** Document ingest, validation and publishing steps. Preserve a last-known-good dataset, block failed new inputs and display dataset version and freshness.

**Inputs:** Approved source contracts and real operational environment.

**Output:** REFRESH_RUNBOOK.md and failure/recovery evidence.

**Acceptance:** A failed refresh cannot silently replace good data with partial or empty results; rollback is proven.

**Dependencies:** A20, C14

### C37 | Cursor | Create a minimal review-action workflow

**Planning state:** Planned. Not independently verified.

**Work:** Reuse a suitable existing action store if present. Capture owner, distributor/dealer scope, evidence reference, decision, due date and status with appropriate permissions.

**Inputs:** A21 playbook and C05 reuse findings.

**Output:** Action workflow and export contract.

**Acceptance:** Actions refer to an actual review and approved evidence. No autonomous external messages or commercial commitments are sent.

**Dependencies:** A21, C35

### C38 | Cursor | Produce shareable, access-safe review packets

**Planning state:** Planned. Not independently verified.

**Work:** Package the selected review with measure definitions, source versions, unresolved items and actions. Remove unauthorized populations and avoid embedding sensitive raw data unnecessarily.

**Inputs:** C28 exports and C37 action model.

**Output:** Reusable distributor review packet and access tests.

**Acceptance:** A shared packet includes enough provenance to interpret its numbers and no hidden rows from another distributor.

**Dependencies:** C28, C37

### C39 | Cursor | Create release evidence and regression snapshots

**Planning state:** Planned. Not independently verified.

**Work:** Capture the build fingerprint, dataset versions, tested journeys, reconciliation results, known issues and approved exceptions for each candidate release.

**Inputs:** Current code and data/test evidence.

**Output:** RELEASE_EVIDENCE.md with reproducible snapshots.

**Acceptance:** Source, data and review versions are traceable together; visual snapshots do not replace calculation tests.

**Dependencies:** C36, C38

### C40 | Cursor | Prepare deployment, rollback and change notes

**Planning state:** Planned. Not independently verified.

**Work:** Use the actual hosting and access model. Document migration scope, rollback point, protected features and known limitations. Do not deploy to shared users without explicit release authorization.

**Inputs:** C39 release packet and A22 decision.

**Output:** DEPLOYMENT_RUNBOOK.md and release candidate.

**Acceptance:** The release can be rolled back and its acceptance scope is clear. Jerome or the named product owner authorizes rollout.

**Dependencies:** C39, A22

### C41 | Cursor | Implement a PRISM adapter only if approved

**Planning state:** Planned. Not independently verified.

**Work:** If the evidence-based decision calls for integration, reuse validated outputs through a narrow versioned contract. Otherwise record the deferral and leave the module independent.

**Inputs:** C05 source-code review and A24 decision.

**Output:** A small tested adapter, or documented no-integration decision.

**Acceptance:** No duplicate business-calculation engine is introduced; PRISM remains undefined until its actual code and purpose are reviewed.

**Dependencies:** C05, A24

### C42 | Cursor | Template onboarding for the next distributor

**Planning state:** Planned. Not independently verified.

**Work:** Parameterize proven contracts, coverage reporting, identity mapping and access tests. Add a new market only through its own evidence and approvals.

**Inputs:** Accepted pilot, A24 expansion decision and operational runbooks.

**Output:** DISTRIBUTOR_ONBOARDING.md and reusable validation template.

**Acceptance:** Country or a previous distributor mapping never becomes a shortcut for validating the new population.

**Dependencies:** C40, A24

### A21 | ChatGPT | Define the operating review and ownership loop

**Planning state:** Planned. Not independently verified.

**Work:** Specify who supplies each dataset, who approves identity, who reviews exceptions and who owns actions. Define a repeatable review agenda without scheduling an unrequested automation.

**Inputs:** A16 story and pilot feedback.

**Output:** OPERATING_PLAYBOOK.md and responsibility matrix.

**Acceptance:** Each unresolved issue has an owner and next decision; the system provides useful output to participating distributors.

**Dependencies:** A12, A16

### A22 | ChatGPT | Issue the release recommendation and G5 assessment

**Planning state:** Planned. Not independently verified.

**Work:** Review operational, numerical, access and user-acceptance evidence. Recommend accept, limited pilot, hold or reject with explicit reasons; leave commercial rollout authority with Jerome.

**Inputs:** C39, A20, A21 and actual user feedback.

**Output:** RELEASE_REVIEW.md with approved scope and remaining risks.

**Acceptance:** No production readiness is claimed without execution and user evidence; an approved limited pilot is not called a network rollout.

**Dependencies:** C39, A20, A21

### A23 | ChatGPT | Measure pilot value without inventing impact

**Planning state:** Drafted. Specification draft available; not accepted.

**Work:** Define baseline measures for correct task completion, review effort, traceability, unresolved mappings and action follow-through. Separate observed improvements from revenue hypotheses.

**Inputs:** Draft scorecard here and actual before/after review observations.

**Output:** PILOT_VALUE_SCORECARD.md.

**Acceptance:** No estimated savings, sales uplift or leakage recovery is reported as realized value without the required observations.

**Dependencies:** A19, A21

### A24 | ChatGPT | Decide the next distributor and PRISM role

**Planning state:** Planned. Not independently verified.

**Work:** Compare next-market source readiness and business value. Choose reuse, integration, independence or deferral for PRISM from its inspected code, not its name. Recheck deferred scope before expansion.

**Inputs:** A12, A22, A23 and C05 evidence.

**Output:** NEXT_RELEASE_DECISION.md with entry criteria and conditional work order.

**Acceptance:** Expansion follows verified data/access readiness. Photography and the removed sales cube do not return by default.

**Dependencies:** A12, A22, A23, C05
