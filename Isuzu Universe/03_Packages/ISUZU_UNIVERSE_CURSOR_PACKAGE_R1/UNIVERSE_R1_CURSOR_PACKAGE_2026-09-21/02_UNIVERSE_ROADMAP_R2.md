# Isuzu Universe | Master roadmap R2

**21 September 2026 | Evidence-led continuation after R0**  
**Purpose:** Delivery roadmap, not a replacement for the strategy paper.  
**Current decision:** R0 evidence accepted; G0 partly closed; R1 validation and synthetic interaction work authorised for local handoff. No deployed application is claimed.

## The product we are building

**Universe is the distributor's connected aftersales review: understand the parts business through AIM, review dealer self-assessment evidence through IDS, interpret commercial signals through PRISM, and turn the result into an owned action.**

The map makes those relationships navigable. It is not a fourth analytical pillar and cannot create an identity relationship that the sources do not establish. Tenders and permitted market-price observations are integrated supporting modules. Actions are the common follow-through layer.

| Pillar | Role in the product | Give to the distributor | Ask / contribution |
|---|---|---|---|
| AIM - Aftermarket Intelligence Model | Common classification of the parts portfolio; family and Genuine/BVP exploration | Explain purchasing by family and range; identify well-supported comparison questions | Regular sales to dealer with stable dealer identifier, part number, period and quantity |
| IDS - Isuzu Dealer Standards | Dealer self-assessment context and improvement discussion | Reuse assessment/feedback material for the known population and available detail | Record jointly agreed Kaizen progress; no forced question links where questions are unavailable |
| PRISM | Reused commercial calculations: appropriately scoped billing, modelled demand, mix and replenishment context | Interpret the commercial question and assess whether evidence supports action, including SPA/DLOD review | Improve source quality and, where useful and agreed, provide case outcomes; workshop information comes later |

Month one does not impose three separate new upload exercises. The single non-negotiable data ask is the agreed recurring named-dealer sales-to-dealer feed. Capture the review's agreed action together; keep additional DLOD and tender feedback lightweight and optional.

## How the pillars work together

A user opens ITUK's monthly review and selects a declared commercial period. AIM provides the family selection and portfolio context. The network view shows eligible commercial accounts, retaining unmapped accounts outside the map. Selecting an account opens its measured purchasing detail. PRISM adds only the calculations supported at that level; a market-level model remains market-level context, not a dealer allocation. IDS shows the relevant self-assessment only when the relationship is approved, or remains a separate selection with an explicit explanation. The review creates an action linked to the evidence snapshot. The next comparable submission shows what changed and what the owner learned.

**Understand -> investigate -> act -> review the next observation.** A fall in purchases does not identify a cause; an action and later increase do not by themselves establish incremental profit.

The same commercial distributor, period, family and measurement basis travel across applicable views. Assessment round/date, tender freshness and reference-price vintage retain their own clocks. 'One experience' must not mean pretending all evidence was measured in the same month.

## Starting position after R0

The uploaded return reports an existing asset collection, not a verified integrated build. Separate AIM/IDS/network HTML surfaces and PRISM reuse candidates exist; runtime behaviour was not tested. The expected application directory is absent in the reported search, and the label 'v2.2' is unverified. Source discovery is useful progress, not something to repeat as a new project. [S01-S07 in the accompanying review]

ITUK CY2025 named-dealer data is the best identified starting population in this pack. It supports a **retrospective demonstrator after reconciliation**. It is not yet a current recurring monthly service. Updated recurring input and an owner for the refresh are separate distributor-pilot gates.

## Delivery sequence and gates

These are acceptance milestones, not promises of calendar delivery. R1, R2 and later labels below are work orders; G0-G5 retain the predecessor roadmap's gate identities.

| Stage | Visible outcome | Cursor work | ChatGPT work | Gate / current status |
|---|---|---|---|---|
| R0 / baseline review | An honest asset, source and critique inventory | C01-C07 inspection returned | A02-A04 review completed for returned evidence | G0 partly closed; host/runtime and reproduced checks remain open |
| R1 / certify and demonstrate interaction | Pinned ITUK sources, reconciliations, safe PRISM reuse boundary, synthetic connected journey | C08-C14; bounded C01/C05/C06/C15 follow-up; prototype subsets of C29/C32/C33/C41 | A05-A08 and A09/A10/A13/A18/A19 decisions after evidence; drafts supplied now | G1 not passed; no external demo or production writes |
| R2 / bind the commercial demonstrator | Internal, real-data ITUK CY2025 review with three pillars visible at their valid levels | C18/C20/C21; C22-C25 as supported; C29/C32/C33; move bounded C37/C41 earlier | A10-A12, A15-A16 and A20 review | G2-C: commercial retrospective demo; not full linked G2 |
| R3 / close the review loop | Distributor-ready action record, selected DLOD evidence, thin tenders and permitted references | C37/C38/C43-C45; C15-C19 only for validated links; C28 export | A11/A13-A16/A19 and A25-A27 | G3 comparability and G2-I only for approved IDS-linked population |
| R4 / controlled distributor pilot | Current agreed feed, access-scoped experience, reviewed brief and named operator | C30/C34-C36/C38-C40; authorised deployment work only | A20-A23 and business/IT approval | G4 and G5 operation prerequisites before any external access |
| R5 / prove and expand | Repeated useful reviews, justified next distributor and a workshop go/no-go | C42; C46 only if phase-2 trigger is met | A23/A24/A28 | G5 repeatability; evidence of usefulness, not a claimed uplift |

Comparability and access are constraints throughout, not checks postponed until the last stage. A price or part-alternative feature does not ship in R2 without its own G3 conditions. External sharing does not happen before permissions and payload-isolation tests, even if the user interface looks ready.

### R1: progress on two tracks

**Data and reuse track.** Resolve the exact local sources; pin the AIM release; preserve source identifiers; reconcile dealer quantities and time grain; audit pricing and fleet fields; inspect the existing PRISM loaders/calculators; demonstrate good and intentionally invalid data cases. Keep tonnage v2 corrections and their blocked checks intact. Produce no new conclusion from a blocked model.

**Interaction track.** Build one isolated synthetic prototype in the authorised work folder. It must show portfolio -> family -> mapped/unmapped commercial accounts -> PRISM context -> IDS link state -> action draft, with state preserved and limitations visible. No new production framework, real dealer embedding, user login, live tender feed or dashboard replacement. The prototype proves the interaction design, not business results.

### R2: a narrow real-data vertical slice

The first real-data demonstrator uses a bounded ITUK CY2025 population that has passed G1. It must retain the portfolio, Genuine/BVP category comparison and the selected period. It includes the three pillars in one review even if IDS is not yet joined at dealer level. Where only totals are available, show those totals in an independent assessment pane with the correct population; do not synthesise section scores. PRISM is reused at the first relevant commercial slice, not deferred to the end of the programme.

If a usable existing host is found and approved, adapt it in a bounded branch/copy. If none exists, return a minimal host proposal for authorisation. This roadmap is not permission to choose a new framework, migrate PRISM or create a replacement application by default.

### R3: the action loop, not another reporting obligation

Move C37's minimum action record forward: evidence snapshot, commercial account or market scope, question, action, owner, due date, status and review outcome. Include an IDS question reference only where it exists and the relationship is approved. Record permission scope so internal distributor notes are not silently shared with ISZE.

For ITUK DLOD, reuse verified support history and optionally capture a structured case. An annual rebate is not a won deal. Support spending, purchasing change and incremental contribution are different measures. Tenders sit inside Universe as a modest UK-relevant panel when a usable authorised feed exists; they do not gate the core commercial build. Market references follow source-specific permission and comparability checks.

### R4: a real distributor pilot

Separate internal historical demonstration from external pilot operation. Before ITUK receives access, prove an agreed current refresh route, a validated allowed audience, tenant-scoped data delivery and exports, named commercial/technical owners, and recovery to a last-known-good release. Browser-hidden menus do not protect embedded all-network data.

The first participant review must produce a useful question and one agreed follow-up, not an obligation to fill every available field. A distributor-approved review brief may then be shared with the dealer through the existing relationship.

### R5: repeat, judge and expand

After two completed monthly reviews, assess correct task completion, time spent, recurring feed quality and whether an owned action affected a real decision. Inspect unresolved questions for a possible workshop-data experiment. After two pilot quarters, require a concrete changed SPA/DLOD/range/stock decision to justify continued investment; do not mistake this for proof of incremental profit.

Select the next distributor by source coverage, willing ownership and permitted access. National-only sales-to-dealer data may support a useful market review but does not unlock a fabricated dealer map. Keep optional maintenance/service data separate until its exact decision use, contributor and rights are established.

## What is brought forward, retained and deferred

**Bring forward:** PRISM calculation reuse (bounded C41), action follow-through (minimum C37), context-preserving navigation (part of C29) and access design (C35 before external use). The predecessor roadmap placed some of these too late for a coherent distributor product.

**Retain:** Broad portfolio access, Genuine/BVP comparison, corrected tonnage v2, source-level distinctions, current assets, named identity approval and independent review.

**Defer:** Photography, workshop/VIN/odometer integration, official service-book ambitions, complex tender UX, wider-market launch, alternative naming and unapproved framework migration. The sales cube remains removed, not deferred for reintroduction.

## Business decisions: proposed working defaults

Use two independent commercial/IDS selections until an approved crosswalk exists. Start Kaizen with parts-review actions; add IDS question links only where supported. Treat DLOD outcome entry as optional and verify history before showing it. Keep tenders inside the product with a thin UK panel when the source is eligible, without blocking the core pilot. These are working recommendations, not new approvals recorded for Jerome.

Identity approval, permitted sharing, host selection, current feed ownership and participant launch remain hard approvals. Synthetic design and data certification do not need to wait for them.

## Non-negotiable measurement rules

Keep ISZE-to-distributor billing, distributor-to-dealer quantities and reference-price valuations distinct. No sum of upstream and downstream sales as total revenue. No dealer fleet ratio from market fleet, no missing-source zero, no dealer history inferred from national history, no unapproved site allocation and no return rate from warranty.

Keep recorded exclusive-applicability purchasing, modelled expected demand and market actuals separate. Pool shared applicability; do not allocate it by fleet share. In the relevant N-series evolution file, sum only the correct `sums_to_n_series_total == "yes"` population; `also_fits_band` remains non-additive. Do not add CY and FY, repeat market actuals across band totals or turn a modelled gap into leakage.

Use a classification-only AIM projection by default. Keep unmatched parts visible. Every output states its scope, period, value basis, release pin and coverage limitations. Measurement differences must be visible next to the result, not hidden in an optional help page.

## How we will know the work is useful

Test the exact review task against the existing process: find and explain a supported purchasing change, distinguish a model/reference from actual value, identify a justified comparison, recognise missing evidence and record a follow-up. Report observed task completion and preparation time; do not invent targets before measuring the baseline.

A prototype passes on interaction evidence. A dataset passes on reproducible reconciliation. A user-facing release passes only with both, plus disclosure and operational checks. Monetary impact requires a separate finance-reconciled assessment of gross profit, support, displacement, timing and relevant programme costs. Avoid double-counting rebates already netted in the ledger and time savings already counted as realised cost reduction.

## Ownership and handoff

Cursor inspects and implements only the current work order and returns evidence. ChatGPT defines the interpretation, reviews the return and issues the next bounded order. Jerome/ISZE approves business identities, priorities and rollout; the designated IT/security owner approves production operation and access.

The task register is the delivery record. The HTML board is a portable view of this version, not a live application or a cloud-synchronised project. No task is accepted merely because a file exists or Cursor reports it complete.
