---
topic: pms-coverage
read_when: [pms, ituk, pilot, capture, iml]
canonical_metrics: FACTS.md, metric_dictionary.md §PMS, pms_capture_by_db_year.csv
last_validated: 2026-07-03
---

# Project: PMS Coverage

> **ITUK headline (IML v7 / Model B):** Oil filter **35.1%** cover · PMS gap **€2.04M** (5 cat) · UIO 22,389 full DVLA · 1.25× filters / 0.5× wear · 100% addressable. Source: `prism/data/iml_v7_ituk_cy2025.yaml` + v7 workbook.  
> **PRISM lane (internal network KPI only):** `pms_capture_by_db_year.csv` after green verify — 0.5 svc/yr × 70% addressable. Do not quote PRISM ITUK figures to IML without footnote.

## Status

Active — ITUK pilot with ISZJ (IML). Targets: Filters +1% retention, Clutch/Brake +3% retention.

## Decisions / clarifications

- **Model B adopted (2026-07-02):** IML v7 schedule is the ITUK/IML headline everywhere — **35.1%** oil filter, **€2.04M** gap, 1.25×/0.5× freqs, 100% addressable. See `DECISIONS.md` same date. PRISM lane retained for network dashboard only (`pms.ituk_prism_lane` in `isze_data.json`).
- **PMS study audit (2026-07-02)** — six contradictory ITUK figures documented; **resolved for IML** by Model B adoption. Do not quote 0.3% or ~€3.5M+ — both stale/rejected. PRISM 100%/173% oil filter is internal lane only.
- **Air-filter capture is interval-aware since 2026-07-02 on a PROVISIONAL 0.5 factor** (air element ~every 2nd service vs oil every service; `pms_capture_assumptions.yaml`). Air capture ~doubled vs earlier outputs — never compare air % across that date without noting the factor change. No IML ratio exists anywhere (SPA packs are price-only); one IML interval number replaces it (`pms_service_intervals.md` §6). See `DECISIONS.md` 2026-07-02.
- **Blower-filter consumable_factor corrected to 1.0 (2026-07-26, Jerome)** — aligned with oil/fuel/urea; was a 0.25 cabin-filter placeholder. See `metric_dictionary.md` §PMS capture rate, `pms_capture_assumptions.yaml`.
- **`sales_fact.parquet` carries `fig_key` since 2026-07-02** — from `parts_catalog_dimension` join (98.9% coverage, `fig_key_source=catalog`); SAP `FIG KEY CLASSIFICATION` auto-ingested when the CY export adds the column.
- **FY2025 completeness gap CLOSED 2026-07-03:** `sales_2026tillApril.XLSX` (Jan-Mar 2026) wired in; `sales_fact` grew 434,858→477,505 rows, years now [2023-2026]. `CY2024-2025.XLSX` (more-complete 2025 re-export) supersedes the old `CY2025.XLSX`. UIO confirmed on V19 (DVLA), `uio_proxy_used=False` for all 2025 rows — the 2024-proxy caveat no longer applies. Parts base €94.26M→€103.57M, network GPS CY2025 50.2%→51.1% (both reconciled in FACTS.md 2026-07-03 entry — legitimate, not a bug).
- **CR/RE (SaTy credit/return codes) excluded 2026-07-03 — NOT ERP-confirmed, a reversible judgment call.** 280 rows / €1.65M network-wide. See `DECISIONS.md` 2026-07-03 and FACTS.md flag H.
- **`Sales_israel_1799&_1797.XLSX` (01_data root) is NOT missing data** — verified row-for-row identical to the CY files already loaded, with one grand-total footer row (no billing date) that doubles its naive sum if misread. Do not wire it into the pipeline; UMI/Israel billing is already fully captured via the three CY files.
- **Legacy oil-filter rates (~61% / ~81% or ~10% / ~17%)** — wrong denominators; PRISM + `FACTS.md` win.
- **Cust 2574 = IUK, Cust 2575 = ITUK** — do not conflate in dealer pivots.
- **ITUK UIO:** **22,389** (DVLA Mar 2026) for capture denominator — not Hasegawa-only parc.
- **Cover ratios** (mapped fleet 12,010 vs DVLA 22,389) — different purpose than PRISM capture; state denominator when citing.

## Apr 2026 ITUK trip — confirmed inputs & phase-one scope

Visit 7–12 Apr 2026 (TVS Chorley, Warrington VC, JDS Manchester, CV Components); feedback mtg 27 Apr 2026. Source: `01_data/03_PMS/ISZE_ITUK_PMS_TripReport_Apr2026_revised (1).docx`.

- **Per-model mileage**, not single network avg. **N35 = 11,576 mi/yr** (MOT-date recalc). N75 higher mileage + better dealer retention; part of N35 fleet services outside network (supports the 70% addressable ceiling).
- **Service intervals per engine family: 4HK1 = fixed, 4JZ1 = flexible.** The "5–7 yr" figure = vehicle replacement cycle, **NOT** a service interval. Numbers belong in `prism/docs/pms_service_intervals.md` (still ASSUMPTIONS until R&M data lands).
- **N75 7.5T ≈ 4–5 service visits/veh/yr** — service *visits*, not item replacements; do not conflate with the 0.5 svc/yr replacement factor above.
- **R&M contract data = best real-world mileage source** (open ITUK request).
- **Phase-one scope (ITUK position):** N75 primary. **Brake + air filter = phase-one** (brake offensive / recover IAM share; filtration defensive / already competitive). Oil + fuel = service-pack support. **Clutch deferred — NOT phase-one** (refines the Status "Clutch/Brake +3%" target; genuine clutch barely sells — 1/78 fig-key-less PMS PNs ever sold, 2026-06-18). Drum brakes replaced as full kit.
- **Brake IAM gap (top commercial finding):** KS International brake parts ~**60–75% below ITUK wholesale**; JDS 9% avg retail discount vs RRP. Objective: close the gap, not raise prices.
- **Why normative UIO×freq is the only viable model:** Parts Eye uneconomic UK (~$1M/mo vs $1M/day US), DMS fragmentation, **Renault data lock-out**, GDPR — no bottom-up dealer data.
- **ITUK retention risk (flagged):** aggressive PMS targeting + higher TCO may push S1/S2 → S3/S4 (external-service) behaviour. S3/S4 fleets = key untapped target. Grow capture without breaking loyalty.
- **ISZE deliverable (JVdP):** review replacement frequencies, identify target items, shape promotion plan.

## Open questions

- EQ-HIT mapping for PN → service schedule (ITUK validation pending).
- CY2025 full PMS basket gap revalidation pending.
- **Service-frequency reconciliation:** **Resolved for IML** — Model B uses IML-schedule 1.25 svc/yr (filters). PRISM 0.5 svc/yr remains internal network KPI.
- **Business case v3 vs PRISM bridge:** **Resolved** — workspace now uses same Model B as business case v3.
- **✅ RESOLVED 2026-07-14 — Pilot Success Criteria baseline retired, no replacement target.** `91_legacy/Isuzu/Divers/ISZE_ITUK_PMS_Pilot_Success_Criteria.md` (2026-05-12) locked CY2025 oil-filter baseline at 17.3% DVLA; Model B reports 35.1% for the same year (freq 1.5→1.25 svc/yr + PN scope 5,815→9,818 units). Jerome's decision: the 17.3% baseline is superseded — 35.1%/Model B is the standard everywhere — but **no new numeric Tier-1/Tier-2 target was set** (explicitly declined, not deferred). Pilot is tracked on Model B methodology without a formal go/no-go percentage. See `DECISIONS.md` 2026-07-14 and `05_memory/briefs/PMS_Baseline_Reconciliation_2026-07.md` for the full reconciliation and the two target options that were considered and NOT adopted.

## Pointers (detail lives here — do not duplicate in chat)

| What | Path |
|------|------|
| Capture formulas | `Projects/Isuzu/prism/docs/metric_dictionary.md` |
| Headline capture figures | `FACTS.md`, `metrics_snapshot.json` |
| Calculator / deck | `Isuzu/Divers/ISZE_PMS_Coverage_Calculator.xlsx`, `PMS sales promotion ISZE_ISZJ.pptx` |
| Cover ratio workbook | `Projects/Isuzu/pms-pilot/PMS Parts sales ITUK WS2025(update 260323).xlsx` |
| Apr 2026 trip report | `01_data/03_PMS/ISZE_ITUK_PMS_TripReport_Apr2026_revised (1).docx` |
| IML PMS SPA campaign packs | `01_data/03_PMS/PMS SPA study_ISZE (1).xlsx` (4 packs N75/N35; 55 PNs — **not in this repo**, local file only, see SPA scope study below) |
| SPA scope study (2026-08-10) | `09_meetings/Preparation Meetings/IML_ITUK_PMS/ITUK_PMS_SPA_Scope_Study_2026-08-10.md` — pack performance vs phase-one, rear-brake-shoe SKU mismatch, urea filter whitespace, v2 scope draft |
| Competitiveness case | `Dashboards/ISZE_Competitiveness_Dashboard.html` |
| Programme memory | `memory/projects/competitiveness.md` |
| Business case (external, drives IML ask) | `03_analytics/Isuzu/pms-pilot/ITUK_PMS_BusinessCase_Apr2026_v3.docx` — ⚠ not built on PRISM data, see 2026-07-02 audit |
| ITUK working analysis (active) | `03_analytics/Isuzu/pms-pilot/ITUK_PMS_Analysis_Apr2026_v7_reclassified.xlsx` — ⚠ own methodology, differs from PRISM |
| EU-wide model + methodology walk-down | `03_analytics/Isuzu/pms-pilot/ISZE_EU_PMS_Model_Apr2026_v1.xlsx` (`Old_vs_New` tab = €10.2M→€0.5-1.6M reconciliation) |
| Datapack (PRISM-derived gap number) | `03_analytics/Isuzu/pms-pilot/ISZE_ITUK_DataPack_v1.xlsx` (`Kosha_Gap_OneNumber` tab) |
| Superseded — do not quote | `03_analytics/Isuzu/pms-pilot/_archive/*` (incl. `ISZE_PMS_Coverage_Analysis_Mar2026_v2.xlsx`, `ITUK_PMS_Analysis_Apr2026_v1-v4.xlsx`) |

## Connections

→ `memory/projects/action-plan-fy2026.md` (PMS campaign workstream)  
→ `memory/projects/uio.md` (ITUK parc methodology)
