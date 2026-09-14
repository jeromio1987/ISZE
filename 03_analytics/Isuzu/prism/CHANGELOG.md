# PRISM — Changelog

**Project:** PRISM (Parts Revenue Intelligence & Sales Monitor)
**Owner:** Jerome Van der Pluym, VP Sales, ISZE
**Location:** `ISZE/Projects/Isuzu/prism/`

---

## [Unreleased — v2.0 build in progress]

### 2026-09-14

#### Changed — fig-key honesty
- Filled **158** empty `fig_key` on existing `pr00_classification.csv` from `pricing_pr00_ie40.parquet`. Family/group kept; no new PNs.
- `build_parts_catalog_dimension` fills empty keys from the same parquet. Catalog **161,325** fig_key / **164,969** PNs.
- `data/fig_key_pn_overrides.csv` header only (`part_number,fig_key,source`).
- `validate_supersession_epc.py`: `--epc` optional; `BLOCKED_NO_EPC_EXPORT` when missing; `INTERNAL_IE40_CHECK` is not EPC MATCH.

### 2026-08-18

#### Added — duplicate tabs dropped (cross-link, not merge)
- BVP: dropped PMS capture / GPS / SPU / AIM risk; Overview links to PMS, GPS, AIM Review. Autodoc Class C moved to Catalog.
- Insights: dropped BVP × Capture; link to AIM × GPS Matrix.
- Strategic: dropped Most exposed and Basket correlation; link to Early Warning. Basket CSV still builds.
- Tests: `tests/test_duplicate_tabs.py`.

#### Added — INTERNAL_MODE hides leakage / attach / elasticity / scrape
- Default `run_prism.ps1` (port 8503) forces `PRISM_INTERNAL=false`. Extra tabs only via `run_prism_internal.ps1` (or `.bat`).
- Pages: Decision (Attach / ITUK Leakage / Elasticity), Offset (Demand-Flow Sankey), Customer Risk (Aftermarket scrape).
- Tests: `tests/test_internal_gate.py`.

#### Fixed — `capture_trajectory` no longer regresses through the partial year
- `modules/strategic_build.build_capture_trajectory()` fits slope / `alert_declining` on complete billing years only (`year_coverage.is_partial`). Live re-measure: 33 declining alerts → 5; 28 artifacts; 0 real declines hidden. CSV rebuilt. Scorecard and review-pack PDFs inherit the flag from the CSV.
- Tests: `tests/test_capture_trajectory.py`.
- Docs: `DECISIONS.md`, `docs/EARLY_WARNING_DESIGN.md`, `docs/DASHBOARD_IA.md` §6–7, `docs/dashboard_contracts.md` Contract 7.

#### Documented — Streamlit is the canonical PRISM surface; oil-filter hazard null
- `docs/DASHBOARD_IA.md` §7: Streamlit :8503 shipped; Dash :8050 and Evidence.dev frozen. Phases 3–8 paused for sign-off.
- `docs/pilot_oil_filter_hazard.md` — fitted bucket intensity does not replace the flat oil-filter interval. `pms_engine` frequencies unchanged.

### 2026-07-03

#### Added — Jan-Mar 2026 sales + more-complete 2025 re-export (FY2025 completeness closed)
- `scripts/build_sales_fact_from_cy.py` — `CY_FILE_YEARS` gives each source file explicit year ownership (`CY2023-2024.XLSX`→2023, `CY2024-2025.XLSX`→2024+2025, `sales_2026tillApril.XLSX`→2026) so the more-complete `CY2024-2025.XLSX` supersedes the old `CY2025.XLSX` (147,409→148,778 rows for 2025) without double-counting 2024. `sales_fact.parquet` 434,858→477,505 rows.
- `data/verification_fixtures.yaml` — row_count, years, required_raw updated to match.
- Verified `Sales_israel_1799&_1797.XLSX` (01_data root) is NOT additional data — row/euro-identical to the CY files, one grand-total footer row inflates its naive sum 2x. Left unwired.

#### Changed — credit notes/returns excluded (integrity flag H, judgment call)
- `modules/sales_loader.py`, `modules/data_prep.py` — `is_credit_note` extended from sign-only (`net_sales_value < 0`, which never fired — zero negative rows exist) to also catch SaTy `CR`/`RE` (280 rows, €1.65M network-wide, all positive-value).
- `scripts/build_metrics_snapshot.py`, `scripts/build_bvp_p0_p1.py` — wired the same exclusion into the parts base and PMS capture actuals (GPS already excluded via the pre-existing `gps_engine.py:130` filter). Not ERP-confirmed — reversible by narrowing the definition back to sign-only.

#### Changed — anchors reconciled after data refresh
- Parts base €94.26M→€103.57M (2026 quarter added more revenue than CR/RE removed); network GPS CY2025 50.2%→51.1% (more-complete 2025 data, partially offset by CR/RE). `facts_anchor.yaml` + `FACTS.md` updated together per the drift-reconcile protocol.

### 2026-07-02

#### Changed — interval-aware air-filter capture (integrity flag C)
- `data/pms_capture_assumptions.yaml` + `modules/pms_capture_config.py` — `air_filter` consumable_factor **1.0 → 0.5 (PROVISIONAL** — air element ~every 2nd service vs oil every service; pending IML ratio). All air capture %, gaps, and weighted totals roughly double vs earlier outputs. See `DECISIONS.md` 2026-07-02 + `docs/pms_service_intervals.md` §3.
- `pages/3_PMS.py` — network-league caveat updated (provisional 0.5× factor replaces "flat interval inflates air gaps").
- Docs synced: `metric_dictionary.md`, `pms_service_intervals.md`, `DATA_INTEGRITY_FLAGS_2026-05-28.md` (flag C → mitigated).

#### Added — SAP fig key on sales_fact (roadmap blocker closed)
- `scripts/build_sales_fact_from_cy.py` — `sales_fact.parquet` now carries `fig_key` + `fig_key_source`. CY export `FIG KEY CLASSIFICATION` ingested directly when present (`sap`); otherwise joined from `parts_catalog_dimension` (`catalog`, 98.9% row coverage).
- `scripts/verify_derived_pipeline.py` + `data/verification_fixtures.yaml` — new `sales_fact.fig_key` coverage check (min 90% non-null).

### 2026-05-15

#### Added — ISZE/Data integration
- `config.py` — resolves `ISZE/Data/derived`, `raw/sales`, UIO `_CURRENT`, mapping CSV candidates
- `modules/sales_loader.py` — loads `sales_fact.parquet` first, then CSV, then legacy TSV
- `scripts/build_sales_fact_from_cy.py` — builds parquet from `Data/raw/sales/CY*.XLSX`
- GPS + PMS pages use shared loaders; `gps_dashboard/app.py` delegates to PRISM when available
- `requirements.txt` — `pyarrow` for parquet

#### Added — Scaffold & Architecture
- `ARCHITECTURE.md` — full data hierarchy (Level 0 Fleet → Level 1 UIO → Level 2A GPS / Level 2B PMS), dependency matrix, key numbers, update protocols
- `config.py` — `BETA_MODE` env toggle (`PRISM_BETA=true`), UIO file selector (prod/beta paths)
- `NAME_CANDIDATES.md` — rejected name candidates (SHOGUN, ATLAS, FORGE, DELTA, PULSE, KENSEI, PARC) kept for reference
- `data/README.md` — UIO file safety rules, beta toggle instructions, promotion checklist
- `app.py` — Streamlit multi-page shell, sidebar nav, version badge, beta banner, About PRISM expander, home page with module table

#### Added — Modules (Layer 1)
- `modules/uio_loader.py` — loads and normalises UIO Excel; safe on missing file; column normalisation; Layer 1 docstring
- `modules/data_prep.py` — distributor mapping, UIO Excel loader (`load_uio_from_excel`), sales TSV/CSV loader, fiscal year logic, exclusion list (MIDI, Germany service, IML internal); migrated from `gps_dashboard/modules/data_prep.py`

#### Added — Modules (Layer 2A: GPS)
- `modules/gps_engine.py` — `calculate_spend_per_unit`, `calculate_multiyear_trends`, `calculate_monthly_sales`, `get_top_parts`, `get_summary_kpis`, `build_uio_lookup`; `build_uio_lookup` inlined (no cross-project dependency); Layer 2A docstring
- `modules/export_engine.py` — Excel export: Executive Summary, SPU sheet (traffic lights), YoY Trends, Metadata; migrated from `gps_dashboard/modules/export_engine.py`

#### Added — Modules (Layer 2B: PMS)
- `modules/pms_engine.py` — `PMS_PN_REGISTRY` (55 PNs, 4 models: N75/4HK1, N75/4JZ1, N35/RZ4E, N35/4JZ1), `CATEGORY_LABELS`, `PHASE1_CATEGORIES`, `classify_pms_sales`, `calculate_pms_capture`, `calculate_ituk_incentive`, `get_pms_summary_by_distributor`; Layer 2B docstring

#### Added — Pages
- `pages/1_UIO.py` — Layer 1 UIO explorer: IML surviving parc banner (always visible), 3-tab layout (Overview bar chart, Trends line chart, By Distributor); safe on missing data file
- `pages/2_GPS.py` — Layer 2A GPS dashboard: sidebar filters (year type, period, region, distributor), 5 tabs (GPS Overview with SPU bar chart + detail table, Trends YoY, By Region pie + bar, Part Explorer with PN registry-first classification, Export with Excel + CSV ZIP)
- `pages/3_PMS.py` — Layer 2B PMS coverage: 7 sections (Phase 1 scope notice, KPI row, capture rate bar chart, opportunity table, distributor breakdown, ITUK incentive panel with tier table + 2030 stretch tracker, 2026 marketing calendar); safe on missing PMS data

#### Fixed
- Removed `st.set_page_config` from all 3 sub-pages (causes Streamlit error in multi-page apps); consolidated in `app.py` only

#### Added — GPS Refinements (modules/gps_engine.py)
- `exclude_warranty` flag on `calculate_sales_by_distributor` and `calculate_spend_per_unit` — filters warranty credit notes (negative value + zero qty + "WARRANT" in description); adds `warranty_credits_eur` column to output (always present, 0.0 when not excluded)
- `calculate_spend_per_unit_by_segment` — same as SPU but adds `segment` (CV/LCV/TOTAL) and `parent_market` columns; enables UK (ITUK+IUK) and Israel (UTI+UMI) side-by-side comparison
- `weight_uio_by_age` — UIO weighting by registration year: peak (1–5 yr) = 1.0, decay (6–10 yr) = 0.85^n, old (>10 yr) = 0.5 floor; utility for future analysis
- `flag_pdi_parts` — adds boolean `is_pdi` column; flags Pre-Delivery Inspection parts that inflate GPS one-time at vehicle delivery (excluded from service revenue analysis)

#### Added — PMS Refinements (modules/pms_engine.py)
- `split_genuine_vs_bvp` — splits classified sales into `{'genuine', 'bvp', 'all_pms'}` DataFrames; enables separate genuine PN capture rate vs BVP acceptance rate reporting
- `calculate_pms_capture_with_cohort` — wrapper around `calculate_pms_capture` with `registration_year_range` parameter; interface ready for VIN-level data (currently `age_cohort_available=False` with clear warning until VIN data arrives)
- `get_seasonal_weights` — monthly demand multiplier (0.85–1.15) based on commercial vehicle service patterns and 2026 campaign calendar
- `calculate_annualised_capture` — YTD-to-full-year projection using seasonal weights when `current_month` is set; returns raw actuals when None
- `get_dealer_capture_detail` — PN-level drill-down for a single distributor: part_number, description, category, model, type, qty, revenue, avg SP; sorted by category then revenue

#### Smoke test results (2026-05-15)
- 15/15 files present ✓
- 11/11 Python files compile without syntax errors ✓
- All module imports resolve correctly ✓ (pandas, numpy, plotly, streamlit as external deps; all local modules found)
- PMS registry: 55 PNs confirmed ✓
- `BETA_MODE=False`, `UIO_FILE=data/UIO_v17.xlsx` ✓

#### Context
PRISM consolidates three previously separate tools:
- UIO module (from `ISUZU_UIO_Dashboard_2026_v17.html` — currently production, used company-wide)
- GPS Dashboard (from `gps_dashboard/` — Streamlit app, V1 delivered Apr 2026)
- PMS engine (new — built May 2026 based on ITUK PMS guidance Apr 2026)

`gps_dashboard/` is NOT modified — it remains the production GPS app until PRISM is promoted.

#### Beta versioning rule
UIOv17 is in active company-wide use. All UIO changes must be tested locally as beta first.
Toggle: `$env:PRISM_BETA="true"` → loads `data/UIO_v18_beta.xlsx`, shows yellow warning banner.
Promotion to production requires explicit sign-off from Jerome.

---

## [v1.0 — GPS Dashboard — Apr 2026]

Delivered as `gps_dashboard/`. Scope:
- Sales aggregation 2022–2026 YTD across ~23 ISZE distributors
- Spend per Unit = Net Sales EUR / UIO (year-matched from V13 Excel 2020–2024 actual)
- ITUK/IUK and UTI/UMI correctly split by CV/LCV segment
- Traffic light thresholds: >€150 / €50–€150 / <€50
- Year-on-year trend view (distributor level)
- Regional breakdown and pie chart
- Top parts explorer (keyword classification preview)
- Excel export (Executive Summary, SPU table, Trends, Metadata)
- CSV export for Power BI

---

*Format: [Unreleased] for in-progress work. Tag releases as [vX.Y — description — date] on promotion.*
