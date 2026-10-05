# AIM + PRISM reinvention — 2 prompts

**Status 2026-08-18:** both prompts executed. Working programme (not a new score): [`roadmaps/aim_prism_reinvention.md`](roadmaps/aim_prism_reinvention.md). Do not re-run Prompt 1 hoping for a different 0–100.

**Purpose (original):** two standalone prompts, each addressed to a fresh Claude Code session with full ISZE repo access. Paste one at a time into a new session — do not run both in the same session (they touch different files and have different kill-criteria). Each is self-contained: it does not assume this conversation's context.

**Grounding basis:** built from a 5-agent research pass (2026-08-18) — 3 agents read the AIM/PRISM/pipeline code and docs in full, 2 did market research on OEM aftermarket pricing engines and predictive-maintenance/parts programs. Every fact cited below is sourced to a file path or an external URL; nothing here is a new calculation. Source list at the bottom.

---

## Prompt 1 — Reinvent AIM: from a face-valid rubric to a backtested, outcome-validated model

```
You are working in the ISZE repo (Isuzu Motors Europe, parts distribution hub). Read
CLAUDE.md and AGENTS.md first and follow them exactly, including: never load
01_data/raw/sales/*.XLSX into context; new/unsorted files go to 01_data/90_INBOX/ only;
numbers must trace to green 01_data/00_derived/_verification_report.json ->
metrics_snapshot.json -> FACTS.md; never fabricate a number.

CONTEXT — what AIM actually is and why its scoring layer failed

AIM ("Aftermarket Intelligence Model") is a GPT-built parts framework
(05_memory/glossary.md lines 121-144) with two genuinely separate layers that later got
conflated:

1. A PN classification engine (Category L1/L2/L3, 3-level taxonomy) —
   03_analytics/Isuzu/prism/modules/aim_pn_classifier.py. This layer WORKS: residual
   unclassified revenue is down to 1.6-1.8% (03_analytics/Isuzu/prism/docs/
   aim_classification_gap_report.md, 2026-07-02). DO NOT touch or rebuild this layer.
   It is out of scope for this task.

2. A pricing-risk / opportunity scoring layer — a hand-weighted 0-100 "Strategic Score"
   (sales, volume, criticality, competition, margin, growth) and a "Pricing Risk Map"
   (class distortion, kit/component inversion, margin leakage). THIS layer is your
   subject.

The pricing-risk layer has already failed a real test, on the record. Read
DECISIONS.md, entry "2026-07-17 — Quadrant page 16: AIM pricing-risk axis retired."
Exact finding: build_aim_gps_matrix.py gated a quadrant x-axis on
`aim_high_risk_pct > RISK_HIGH_PCT (hardcoded 0.12)`. The metric's all-time max across
88 distributor-year rows was 0.0487 (Norway 2023); CY2025 network level was 0.0099.
Zero rows ever crossed 0.12. The axis was a 1-D restatement of GPS — it never separated
one distributor from another. It was retired 2026-07-17 and replaced by PMS total
capture; AIM's pricing-risk output is now kept only as a context column
(03_analytics/Isuzu/prism/pages/16_AIM_GPS_Matrix.py), not a decision surface.

This is not a tuning problem. Read the finding again: the metric was "sound and
correctly denominated" — the threshold was simply never calibrated against outcomes.
That is the generic failure mode of a face-valid weighted rubric: it can look sensible
and still have no relationship to reality, because nothing about its construction ties
it to a real outcome.

MARKET BENCHMARK (from 2026-08-18 research pass — do not re-derive, cite if useful)

Every serious OEM/aftermarket pricing system found in research (Syncron, PTC
Servigistics, Vendavo — used by Volvo Trucks and TruckPro, Zilliant, PROS, o9, and the
purpose-built competitor-price platform MarktPilot) keeps classification and pricing
risk as two SEPARATE functions, and treats the pricing-risk/elasticity output as a
STATISTICALLY FIT model validated against realized outcomes — never a hand-weighted
score. The validation step every one of them uses and AIM skipped is backtesting: hold
out a period or a set of distributors, generate the flag from prior data only, then
check out-of-sample whether it actually predicts who under/over-performed. BCG built
one such platform for an unnamed global OEM and reports +2 EBIT points on spare parts —
a real, board-relevant outcome delta, not a plausibility score. (Lokad's own vendor
review is worth reading in spirit even if you don't fetch it: it explicitly criticizes
rule-based "always X% above competitor" pricing logic and flags that most vendor
case-study numbers carry no stated baseline — hold your own work to a higher bar than
that.)

Your job is not to build a bigger, smarter rubric. Your job is to find out whether a
FITTED model of pricing risk / opportunity can be shown, by backtest, to separate real
ISZE outcomes — and to report the honest answer even if it is no, with the same
precision as the 2026-07-17 DECISIONS.md entry.

HARD CONSTRAINTS

- Do not touch modules/aim_pn_classifier.py or the classification pipeline. Out of
  scope.
- sales_fact is net-only, permanently (closed 2026-08-11, see 00_docs/ISZE_ROADMAP.md
  line 44 and DECISIONS.md). No gross, SPA, or condition data exists or will exist.
  Build only on net sales + dated PR00/ZPR1 price-list history
  (01_data/01_Pricing/PRICING_DATA.md) — do not ask for a decomposition that has
  already been closed.
- Competitive-pricing scrape data is PN-indexed ONLY for KS International, and only
  partially for Mekonomen (0/22 confirmed filter PNs hit in the current pull). TMC and
  Tranzparts are category crawls with no PN column. Auto365 (Israel) has no OEM PN join
  key at all (04_tools/autodoc_scraper/AUTO365_PN_JOIN.md — this is a closed
  finding, don't re-investigate it, just respect it). The current eucon_price_gap.csv
  (44 PNs) is mislabeled "2023" but is actually PartsPool data dated 2026-03-29
  (04_tools/autodoc_scraper/PROPOSAL_EUCON_AND_SCRAPER_EXPAND.md) — fix or flag this
  mislabel before using the file; do not trust its vintage tag silently.
- Every "this predicts X" claim needs an explicit train/holdout split (by year and/or
  by distributor) and a stated error or separation metric against a naive baseline
  (e.g. "flag nobody" / "flag everybody," given AIM's own history of a threshold that
  flagged nobody). Face validity is explicitly disqualifying — that is the exact
  mistake being corrected.
- Any change that touches FACTS.md or ships to a live page must pass
  scripts/run_pipeline_and_verify.ps1 green first.
- Write your finding to DECISIONS.md in the same style and precision as the 2026-07-17
  entry — including if the answer is "no candidate cleared backtest."

TASK

1. Read DECISIONS.md (2026-07-17 and 2026-07-21 entries), aim_classification_gap_report.md,
   03_analytics/Isuzu/prism/evidence-app/pages/aim-leakage.md, and
   03_analytics/Isuzu/prism/docs/BVP_Strategy_Report_2026-05-28.md. Write a half-page
   "what AIM's scoring layer actually is vs. what it claims to be" note.
2. Identify the real outcome variables to backtest against: GPS spend-per-unit level/
   trend (01_data/00_derived/gps_spu_by_distributor.csv) and PMS total capture level/
   trend (01_data/00_derived/pms_capture_by_db_year.csv), at distributor-year grain.
3. Propose 2-3 candidate pricing-risk/opportunity formulations that are FITTED
   statistics, not weighted scores — e.g. a regression of KS-competitor price gap
   (PN-indexed rows only) against realized sellout/capture outcome, segmented by a
   genuine elasticity proxy you can already build from existing data: safety-critical/
   maintenance-mandatory categories (via Category L1/L2/L3 + Demand Type) vs.
   commodity categories with confirmed IAM competition (via the genuine/BVP contested
   split already computed for BVP_Strategy_Report). Do not invent a new taxonomy —
   reuse what's already classified.
4. Backtest each candidate with a real holdout (rolling-origin by year is preferred
   given only ~3 years of clean data). Report the separation result plainly, including
   if it is null.
5. If a candidate clears backtest: propose (do not silently ship) how it would replace
   or supplement the current context-only aim_high_risk_pct column on
   pages/7_AIM_Review.py and/or pages/16_AIM_GPS_Matrix.py, with the same file-touch
   discipline as the 2026-07-17 rewrite (one coherent change, DECISIONS.md entry,
   ISZE_ROADMAP.md updated).
6. If no candidate clears backtest: say so, in DECISIONS.md, with the same rigor as the
   2026-07-17 entry. Recommend explicitly whether AIM's pricing-risk ambition should be
   formally retired (redirect effort to the classification layer, which works, and to
   the P4 deterministic account-health signals spec at 00_docs/P4_DETERMINISTIC_SIGNALS.md,
   which is a different, already-speced approach to "who needs attention").

DEFINITION OF DONE

A DECISIONS.md entry with an honest backtest result (pass or null), updated docs if a
candidate shipped, and — critically — no new weighted rubric presented as if it were
validated. A well-argued "this doesn't work, here's why, here's what to do instead" is
a complete and successful outcome of this task.
```

---

## Prompt 2 — Reinvent PRISM: consolidate the surface, replace the flat-interval demand model with a fitted one

```
You are working in the ISZE repo (Isuzu Motors Europe, parts distribution hub). Read
CLAUDE.md and AGENTS.md first and follow them exactly, including: never load
01_data/raw/sales/*.XLSX into context; numbers must trace to green
01_data/00_derived/_verification_report.json -> metrics_snapshot.json -> FACTS.md;
never fabricate a number, and never present an external benchmark as an ISZE target
without saying explicitly it is external.

CONTEXT — what PRISM actually is today

PRISM (03_analytics/Isuzu/prism/) is a genuinely live, actively-used Streamlit app
implementing a 3-lens hierarchy: UIO (fleet size, IML-sourced) -> GPS (Level 2A,
net sales / UIO, EUR/truck, modules/gps_engine.py) -> PMS (Level 2B, actual PN sold /
expected demand = capture rate, modules/pms_engine.py). Read
03_analytics/Isuzu/prism/ARCHITECTURE.md for the full hierarchy and dependency matrix
(note: its "70% addressable parc" figure is stale — the code default is now 100%, see
pms_engine.py DEFAULT_PARC_CONFIG, "Jerome 2026-07-03").

Two structural problems, both on the record, both real leverage points:

PROBLEM A — the product is fragmenting across three surfaces instead of consolidating.
20 Streamlit pages across 8 nav sections; a separate Dash app (dash_app/, port 8050)
reusing the same chart modules; and a working Evidence.dev prototype (evidence-app/,
confirmed run via evidence-app/.devlog.txt) that re-implements the same UIO->GPS->PMS
spine as a distributable, SQL-templated BI site explicitly positioned as "diagnostic,
not descriptive, BI." A redesign plan exists — 03_analytics/Isuzu/prism/docs/
DASHBOARD_IA.md — to collapse the Streamlit nav from 19 pages to 10; phases 0-2 plus an
out-of-band Early Warning page are done, phases 3-8 (the big Network Intelligence merge,
Mix trim, ITUK hub, Decision cleanup, Tools consolidation) are not started. Nobody has
decided which of the three surfaces is the actual shipped product.

There is also a live bug leaking into distributor-facing output right now: read
03_analytics/Isuzu/prism/docs/EARLY_WARNING_DESIGN.md — regressing capture_trajectory
through the current partial year manufactures 29 of 35 "declining capture" alerts as
artifacts (network median capture reads 0.019 in the partial year vs. 0.094 complete).
modules/strategic_build.build_capture_trajectory() is NOT yet fixed and the same
contaminated slope feeds modules/scorecard_pdf.py and modules/review_pack_pdf.py —
i.e. distributor scorecards and QBR packs are printing a false 83% decline rate today.
Fix this first, before anything else in this task, because it is live and wrong.

PROBLEM B — PMS's "expected demand" is still a flat, pre-telematics assumption: fleet
age bucket x a flat service-frequency constant (N75=0.5/yr, N35=0.75/yr blended,
LCV=1.0/yr — modules/pms_engine.py), not fitted to any actual usage or failure signal.

MARKET BENCHMARK (from 2026-08-18 research pass — do not re-derive, cite if useful)

Every named OEM predictive-parts program found in research — Volvo Trucks Remote
Diagnostics/ASIST (on Decisiv SRM, the same platform underlying Isuzu's own N.A.
commercial-truck dealer network), Scania ProCare (predicts failure per individual
vehicle across ~1M connected vehicles and ~90 component groups, accounting for
topology/climate/driving style, not a flat interval), Daimler Truck OMNIplus/Detroit
Connect, Cummins Connected Diagnostics, MAN ServiceCare on RIO, GM OnStar Proactive
Alerts + Dealer Maintenance Notification — replaces a flat mileage/time interval with
survival-analysis / remaining-useful-life modeling on vehicle-level covariates. ISZE
has no telematics and none of that vehicle-level signal — do not treat "get telematics"
as an actionable recommendation, it is a data-acquisition problem, not a modeling one,
and is out of scope. The transferable idea, not the infrastructure, is this: fit a
hazard/decay function per fleet SEGMENT (using covariates ISZE already has — model,
region, age bucket, duty type) instead of one flat multiplier per model family, the
same way ISZE could statistically estimate a service-frequency curve from its own
historical capture data rather than assuming one constant.

On wallet share: research found genuine-parts capture is managed elsewhere as a
composite incentive scorecard (penetration rate + volume threshold + uptime/response
performance + telematics-activation rate), not a dashboard read alone — a structural
analogy worth having in view for how IDS + GPS/PMS could evolve, but do not build this
without Jerome's explicit steer, it touches distributor commercial terms. Also: no
defensible public benchmark exists for "healthy" genuine-parts capture rate. J.D.
Power's ~88% is service-visit capture (warranty-period-biased), NADA's ~72% is service
retention, DataMac's >60% is market-level OE-brand share of CV parts purchased — three
different metrics at three different levels. Do not splice any of them into a PMS/GPS
target. If you want an external comparator, name it explicitly as external and state
which of these three families it belongs to.

HARD CONSTRAINTS

- Fix the capture_trajectory partial-year bug FIRST, as an isolated, verifiable change,
  before any consolidation or modeling work. This is a correctness bug in production
  output, not a design choice.
- sales_fact is net-only, permanently (00_docs/ISZE_ROADMAP.md line 44). No telematics,
  no VIN-level usage, no gross/SPA/condition data exists or will exist. Do not propose
  acquiring it.
- Do not silently re-touch already-fixed, on-the-record PMS logic: the brake front/
  rear consolidation (DECISIONS.md 2026-07-16), the country_overrides bucketed-factor
  fix (DECISIONS.md 2026-07-21), or the provisional air_filter 0.5 factor (still
  provisional, pending IML confirmation per DATA_INTEGRITY_FLAGS_2026-05-28.md flag C)
  — read DATA_INTEGRITY_FLAGS_2026-05-28.md and DECISIONS.md before changing any PMS
  assumption.
- Respect INTERNAL_MODE gating in config.py — internal-only content (dealer leakage,
  attach, elasticity, demand-flow Sankey, aftermarket scrape) must stay off any
  distributor-facing export.
- The email/LLM "Track B" work (P2b/P3/P6 in 00_docs/roadmaps/ai_sales_intelligence.md)
  is separately gated behind G0b (unsigned as of 2026-08-12) and out of scope for this
  task entirely — do not touch 01_data/17_interactions/ or propose using it here.
- Any change touching FACTS.md or a live page must pass
  scripts/run_pipeline_and_verify.ps1 green first.
- Do not fabricate or import an external capture-rate/wallet-share benchmark as an ISZE
  target (see above).

TASK

1. Fix modules/strategic_build.build_capture_trajectory() with a partial-year guard
   (Early Warning's own page already has a working guarded recompute you can pattern-
   match against — read pages/0_Early_Warning.py and scripts/build_early_warning.py
   first). Verify the fix propagates correctly into modules/scorecard_pdf.py and
   modules/review_pack_pdf.py. Log the before/after false-alarm count the way
   EARLY_WARNING_DESIGN.md logged its own numbers.
2. Resolve the documented dual-writer conflict on pages/18_Decision_Models.py
   (DASHBOARD_IA.md flags this — the Defection-tab-removal commit and an in-flight
   waterfall over_target_eur rework are stacked uncommitted in the same file).
3. Consolidation: read DASHBOARD_IA.md phases 3-8 in full. Either execute them, or — if
   the scope has changed since 2026-07-17 — write an updated IA plan and get explicit
   sign-off before executing. As part of this, make and justify a recommendation on
   which of the three rendering surfaces (Streamlit, Dash, Evidence.dev) is the
   canonical shipped product going forward, stating the real tradeoff: Streamlit is
   what's actually used daily today; Evidence.dev is the more "diagnostic BI" -aligned
   prototype but has never been shared with anyone. Do not silently keep maintaining
   three.
4. Hazard-function pilot (bounded scope — one category, not a rewrite): pick
   oil_filter (ITUK anchors already reconcile to FACTS.md, lowest-risk category to
   pilot on). Fit a segment-level hazard/decay function against real historical PMS
   capture data as an alternative to the current flat service-frequency assumption.
   Backtest it the same way Prompt 1 requires: does the fitted curve correlate better
   with realized capture than the flat constant, out of sample? Report honestly,
   including if the answer is no.
5. Optional, explicitly flagged as a proposal only, not a build: sketch what a
   composite dealer wallet-share scorecard (GPS + PMS + response latency from
   db_response_latency.parquet, once/if shared-mailbox scope is cleared) could look
   like structurally. Do not build it. Flag it for Jerome's steer.

DEFINITION OF DONE

The capture_trajectory bug is fixed and verified with a before/after count. An updated
DASHBOARD_IA.md status and an explicit, justified canonical-surface recommendation.
One documented hazard-function pilot result on oil_filter, reported honestly (pass or
null), with the same backtest discipline as Prompt 1. No new flat assumption presented
as if it were fitted.
```

---

## Sources

**Internal (2026-08-18 read-in-full):** `DECISIONS.md`, `05_memory/glossary.md`,
`00_docs/ISZE_ROADMAP.md`, `03_analytics/Isuzu/prism/ARCHITECTURE.md`,
`03_analytics/Isuzu/prism/docs/aim_classification_gap_report.md`,
`03_analytics/Isuzu/prism/pages/16_AIM_GPS_Matrix.py`,
`03_analytics/Isuzu/prism/scripts/build_aim_gps_matrix.py`,
`03_analytics/Isuzu/prism/modules/aim_pn_classifier.py`,
`03_analytics/Isuzu/prism/pages/7_AIM_Review.py`,
`05_memory/projects/aftermarket-intelligence.md`,
`03_analytics/Isuzu/prism/modules/gps_engine.py`, `modules/pms_engine.py`,
`03_analytics/Isuzu/prism/docs/DASHBOARD_IA.md`,
`03_analytics/Isuzu/prism/docs/EARLY_WARNING_DESIGN.md`,
`03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md`,
`03_analytics/Isuzu/prism/docs/BVP_Strategy_Report_2026-05-28.md`,
`03_analytics/Isuzu/prism/NAME_CANDIDATES.md`, `evidence-app/pages/*.md`,
`00_docs/roadmaps/ai_sales_intelligence.md`, `00_docs/P4_DETERMINISTIC_SIGNALS.md`,
`00_docs/agent/AI_STACK_ARCHITECTURE_Apr2026.md`, `00_docs/AUTOMATION_REGISTER.md`,
`01_data/DATA_MANIFEST.md`, `01_data/01_Pricing/PRICING_DATA.md`,
`04_tools/autodoc_scraper/PROPOSAL_EUCON_AND_SCRAPER_EXPAND.md`,
`04_tools/autodoc_scraper/AUTO365_PN_JOIN.md`, `04_tools/interactions/collect_mapi.py`.

**External (market research, full URL list in the research task journal):** Syncron,
PTC Servigistics, Vendavo (Volvo Trucks, TruckPro case studies), Zilliant, PROS, o9
Solutions, Lokad, MarktPilot, McKinsey (aftermarket pricing/AI in aftersales), BCG
(dynamic B2B pricing, CV aftermarket AI value) — pricing side. Volvo Trucks Remote
Diagnostics/ASIST, Decisiv SRM, Daimler Truck OMNIplus/Detroit Connect, Scania
ProCare/Services 360 Pro, MAN ServiceCare (RIO), Cummins Connected Diagnostics, Toyota/
Lexus Safety Connect, GM OnStar Proactive Alerts/DMN, J.D. Power ASI, NADA, DataMac —
predictive-demand/wallet-share side. Vendor claims (e.g. PROS's stated error-reduction
%) are flagged inline in the prompts as vendor-stated and unaudited, not adopted as
fact.
