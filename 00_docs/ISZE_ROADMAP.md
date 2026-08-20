# ISZE — Consolidated roadmap

**Last updated:** 2026-08-18  
**Domain detail:** [`roadmaps/`](roadmaps/) · **Registry:** [`MAP_REGISTRY.yaml`](MAP_REGISTRY.yaml)

> **Numbers:** `../FACTS.md` wins over any deck, memory, or GPT file. Pipeline: green `01_data/derived/_verification_report.json` → `metrics_snapshot.json`.

---

## Live now (PRISM + derived pipeline)

| Capability | Location |
|------------|----------|
| GPS spend per unit | PRISM `pages/2_GPS.py` · `gps_spu_by_distributor.csv` |
| PMS capture (registry + BVP catalogue) | `pages/3_PMS.py` · `pms_capture_by_db_year.csv` |
| Fig-key / PR00 catalogue | `parts_catalog_dimension.csv` · `gps_v2_fig_key.md` |
| GPS × PMS-capture quadrant | `pages/16_AIM_GPS_Matrix.py` · `aim_gps_matrix.csv` (x-axis was AIM pricing risk until 2026-07-17 — it never separated anyone; **2026-08-18: fitted replacement also null**, AIM pricing-risk *ambition* retired — see `DECISIONS.md`) |
| Decision models | `pages/18_Decision_Models.py` · `wallet_waterfall.csv`, etc. |
| Pipeline verify | `scripts/run_pipeline_and_verify.ps1` |
| PMS assumptions (editable) | `prism/data/pms_capture_assumptions.yaml` |
| Static HTML refresh | `build_isze_dashboard_json.py` + `inject_dashboard_overlays.py` |
| Data integrity audit | `pages/10_Data_Integrity.py` · `mislabelled_sku_audit.csv` |
| Warranty Intelligence | `pages/20_Warranty.py` · `distributor_warranty_expense_fiscal.csv` |
| Price Realization | `pages/21_Realization.py` · `pr00_realization_*_cy.csv` · `zpr1_vs_pr00_by_payer_year.csv` |
| Parc Cohorts | `pages/22_Parc_Cohort.py` · `07_UIO/vin/VIN_register.csv` (JP cohort, not UIO v19) |
| Dealer Sell-out | `pages/23_Dealer_Sellout.py` · `sellout_aim_network_mix_2025.csv` · `sellout_aim_by_subgroup_2025.csv` |
| VPACC tracker | `pages/24_VPACC.py` · `vpacc_fy2027_action_plan_july.parquet` (July update) · `vpacc_fy2027_monthly_db_block.parquet` (legacy) |
| Static twins (HTML) | `02_dashboards/bi/` (4 self-contained snapshots, built by `_build_bi_twins.py`) |

Run PRISM: `03_analytics/Isuzu/prism/run_prism.ps1` (port **8503**)

---

## Build now

| Item | Blocker | Domain |
|------|---------|--------|
| **PRISM next (nav / surfaces)** | **Not a 4-session merge.** Streamlit :8503 is the product; freeze Dash + Evidence. **INTERNAL_MODE shipped 2026-08-18** (`run_prism.ps1` MD-safe; `run_prism_internal.ps1` for extra tabs). **Duplicate tabs dropped 2026-08-18** (cross-link, not a 7-tab Network Intelligence rewrite). Detail: `prism/docs/DASHBOARD_IA.md` §8. | PRISM |
| Interval-aware air vs oil capture | ⚠ shipped 2026-07-02 with **provisional 0.5 air factor** — IML ratio confirmation still open | PRISM |
| SAP fig key on `sales_fact` | ✅ done 2026-07-02 via `parts_catalog_dimension` join (98.9% coverage); SAP column auto-ingested when CY export adds it | Pipeline |
| 2025 UIO in capture | ✅ done — V19 (DVLA-based) confirmed wired 2026-07-03, `uio_proxy_used=False` on all 2025 rows | UIO |
| FY2025 completeness (Jan-Mar 2026 data) | ✅ done 2026-07-03 — `sales_2026tillApril.XLSX` wired in, FY2025 now a complete 12 months | Pipeline |
| CR/RE credit-note/return exclusion (flag H) | ✅ done 2026-07-03, judgment call not ERP-confirmed — see FACTS.md flag H | Pipeline |
| CY2026 AIM dashboard | ✅ Billing-only OK 2026-08-11 — dual CY+FY windows in `aim_billing_windows.json` (no AIM workbook) | HTML |
| Supabase live Master KPIs | Schema + credentials | HTML V4 |
| Discount scraper refresh | Optional (personal promos) | [scrapers](roadmaps/scrapers.md) |
| Dashboard filename renames | Build scripts hardcode vN | [html](roadmaps/html.md) · [`CANONICAL.md`](CANONICAL.md) |
| Tender Monitor Task Scheduler | ✅ live `ISZE Tender Monitor` (verified 2026-07-26) | [scrapers](roadmaps/scrapers.md) |
| Competitive pricing refresh scheduler | ✅ live `ISZE_PMS_IAM_Refresh` — do **not** also import spare XML; manual refresh 2026-07-26 after interrupt | [scrapers](roadmaps/scrapers.md) |
| **Dated price-list history** | ✅ **PR00 + ZPR1 2023/2024/2025 landed 2026-08-11** under `01_data/01_Pricing/history/` (+ current 2026 lists). Cheap 2023 parquet extracts in `00_derived/`. Year-matched list-to-pocket **possible but not yet validated** — do not quote leakage until joins checked. | Pricing / Pipeline |
| Gross + condition values on the billing extract | **Closed 2026-08-11 — not available.** Jerome: cannot provide gross / SPA / condition columns on the SAP billing extract. `sales_fact` stays **net-only**. Discount vs SPA vs mix **cannot** be decomposed from billing — do not re-ask; design pricing work around net + dated lists only. | Pricing / Pipeline |
| 522 part numbers billed with no PR00 entry | **Updated 2026-08-12.** Original 2026-08-01 measure: €4.96M / 15.1%. Spec C4 SAP pull closed **220 PN / €4.36M**. Catalogue-parts PR00 coverage now **98.2%**. Residual: admin non-PN (REBATE/TRANSPORT/interest) + parked UMI Shell + **24 PN / €67k** ZPR1-path hardware. Classification: `01_data/00_derived/pn_coverage_classification.csv`. Supersession billed-on-old: 925 PN / €2.48M (IE40 map, not EPC-validated). Detail: [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) §6. | Pricing |
| `price_volume_elasticity.csv` is not quotable | ✅ **Deferred 2026-08-11 — DB→DLR only.** Annotate/ignore ISZE→DB file (`price_volume_elasticity.README.md`). Resume when more dealer sell-out coverage exists. | Pricing |
| LCV bucket generation-aware interval split | **Schedules on disk** (`01_data/03_PMS/service_schedules/` + mail pull). RG21 RZ4F-TC **with SCR** = 15k km; without SCR / older = 20k. Still blocked on **chassis/reg-year cutoffs** for parc weighting — PDFs alone do not map UIO years → SCR vs non-SCR. | PRISM / PMS |
| Brake front/rear split categories never get real actual sales | ✅ **Fixed 2026-07-16 — option (b), Jerome's call.** `brake_pad_front/rear` + `brake_shoe_front/rear` dropped from `wear_factor` (`pms_capture_assumptions.yaml`); parent `brake_pad`/`brake_shoe` retained and now restated explicitly in the YAML. The 2026-07-15 diagnosis understated it: the parents were **already** in `P1_CATEGORIES` via `_DEFAULT_WEAR` in `modules/pms_capture_config.py` (the YAML is merged **onto** that dict, not substituted for it), so brake demand was estimated **three times** over one parc (parent 0.5 + front 0.5 + rear 0.5) — the drag was phantom *expected* demand in the denominator, not the empty numerators. Option (a) was rejected on that basis: it would have filled the numerators while leaving the denominator tripled, converting a visible zero row into an invisible wrong rate. Rationale for (b): front/rear is not a unit of commercial action (there is no front-pad campaign), and the only market with real data (ITUK, IML slide 2026-07-14) has front+rear replaced together as one job — not independent wear cycles. Verified by re-run: P1 3,888 → 3,024 rows (864 = 4 cats × 72 × 3 line_types), all surviving actuals byte-identical, network expected-weighted capture CY2025 **23.8% → 32.0%** (`total` line_type; matches the 31.9% quoted 2026-07-15 within data drift), ITUK oil-filter anchors unchanged, 40/40 prism tests pass. | PRISM / PMS |
| `country_overrides.factors` is dead config for every bucketed distributor | **✅ FIXED 2026-07-21 — Jerome approved via "do all" on Safety&capital top-10.** `modules/pms_engine.expected_by_category_bucketed()` now reads `cfg["factor_overrides"]` before falling back to `LCV_BUCKET_FACTOR_OVERRIDES`/global factors (same override-replaces-default pattern as `scripts/build_bvp_p0_p1.py::_expected_qty_for_db()`); the legacy single-scope loop in `calculate_pms_capture()` got the identical fix since it never applied `factor_overrides` either. Verified on real data: ITUK brake_pad CY2025 expected 5,840.1 → **4,672.1** (0.5 → 0.4 denominator), capture **58.3% → 72.8%** (registry-only actuals 3,402 units). 61/61 prism tests pass. `country_overrides.services_per_year` was already live via `BUCKET_SERVICES_PER_YEAR_OVERRIDES` (UTI) — untouched. See `DECISIONS.md` 2026-07-21. The units question below (0.4 vs 0.8) is still open — this fix makes the *configured* 0.4 finally take effect, it does not resolve whether 0.4 is the right number. | PRISM / PMS |
| ITUK brake wear factor — is 0.4 or 0.8 the right basis? | **Pending — expect ITUK data soon (2026-08-11).** Leave 0.4 until then; do not quote ITUK brake capture as locked. | PRISM / PMS |
| AIM pricing-risk fitted model (replace `aim_high_risk_pct` as a decision surface) | **Closed 2026-08-18 — null backtest.** Replacement programme: [`roadmaps/aim_prism_reinvention.md`](roadmaps/aim_prism_reinvention.md). Do not ship a new 0–100 onto pages 7/16. | PRISM / AIM |
| P4 account-health (who went quiet) — AIM-replacement queue | **Next real build.** Spec ready; P2a tables live; **G0b not required.** ~1.5 weeks + 1 day calibration. | [`P4_DETERMINISTIC_SIGNALS.md`](P4_DETERMINISTIC_SIGNALS.md) · AIM/P4 |
| PRISM INTERNAL_MODE launcher (hide leakage/attach/elasticity/scrape) | ✅ **done 2026-08-18** — `run_prism.ps1` MD-safe; `run_prism_internal.ps1` extra tabs. | PRISM |
| Competitor file vintages on Mode A (PartsPool 2026-03-29 ≠ Eucon UK 2023) | Meta already flags; UI label needs rebuild/ship when asked. | Pricing |
| PRISM IA phases 3–8 (Network Intelligence merge) | ✅ **done 2026-08-20.** Phases 3–8 shipped: Network Intelligence merged (7 tabs), Mix absorbed DB-mix-split, ITUK hub, Tools retired Scorecard/Customer-Risk + added Marketing Calendar + internal shelf. Archived source pages to `pages/_archive/`. 71 tests green. Canonical surface = Streamlit :8503. | PRISM |
| Fitted oil-filter service frequency (replace flat 0.5/1.0) | **Closed 2026-08-18 — null.** All-DB OLS beats MAE by absorbing under-capture into λ; high-capture spec loses both holdouts. Leave bucketed constants. `docs/pilot_oil_filter_hazard.md`. | PRISM / PMS |
| `capture_trajectory` partial-year false alarms | ✅ **Fixed 2026-08-18.** 33 declining alerts → 5; 28 artifacts; 0 real declines hidden. Scorecard/QBR inherit the CSV. | PRISM |

---

## Domain roadmaps

| Domain | File | Status |
|--------|------|--------|
| HTML dashboards | [`roadmaps/html.md`](roadmaps/html.md) | V3 overlay + V4 Supabase |
| Scrapers | [`roadmaps/scrapers.md`](roadmaps/scrapers.md) | Tender path fixed; refresh scheduler XML ready; Autodoc retired from health check |
| GPS / fig-key / AIM | [`roadmaps/gps.md`](roadmaps/gps.md) | V2 enrichment in PRISM. **V3 scoring superseded** |
| AIM + PRISM after scoring failed | [`roadmaps/aim_prism_reinvention.md`](roadmaps/aim_prism_reinvention.md) | **Active.** Score closed; P4 + PN prices + Streamlit :8503 |
| Jarvis / tools | [`roadmaps/tools.md`](roadmaps/tools.md) | V2 data-out-of-code |
| AI sales intelligence (email → action, account health, forecast) | [`roadmaps/ai_sales_intelligence.md`](roadmaps/ai_sales_intelligence.md) | **Track A active (P1).** Catalogue PR00 98.2%. Mail: MAPI open, Graph closed; **G0a** before ingest. **P4 now first in the AIM-replacement queue** |

---

## Data integrity (do not quote externally until closed)

See `03_analytics/Isuzu/prism/docs/DATA_INTEGRITY_FLAGS_2026-05-28.md` — priority: interval-aware PMS (C), returns confirmation (H).

---

## Workspace cleanup

Open decisions (UI primary for external share, ISZE_Dashboard merge): [`ISZE_Cleanup_Plan.md`](ISZE_Cleanup_Plan.md)
