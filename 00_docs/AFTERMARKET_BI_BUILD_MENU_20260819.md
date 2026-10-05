# Aftermarket BI — build menu (internal · 2026-08-19)

**KPI filter (2026-09-14):** [`ISZE_BI_FRAMEWORK.md`](ISZE_BI_FRAMEWORK.md) is which numbers to quote (FY first, euros first). This file is the **build list**, not the KPI stack.

**Pipeline:** green `_verification_report.json` (108/0) · safe to build on derived.  
**Commercial stack:** `01_data/01_Pricing/DB_DLR_COMMERCIAL_STACK.md`  
**Book B:** `01_data/01_Pricing/BOOK_B_CONCLUSIONS_20260819.md` · **no alloc** unless explicit.

Hard rules: **UTI ≠ UMI** · **IUK ≠ ITUK** · **IRELAND ≠ IUK** · reference sell-out = PR00 × 1.785 · PMS headline = **total capture**.

---

## Tier A — build now (no Jerome decision)

**BUILD ALL run:** 2026-08-19 · log `01_data/91_build/BUILD_ALL_TIER_A_20260819.meta.json` · **14 done · 1 skipped (A12)**

| # | Build | Status | Output |
|---|-------|--------|--------|
| A1 | **P5.2 baseline forecast** | ✅ | `01_data/00_derived/forecast_candidates.parquet`, `backtest_report.parquet` (548 series, median WAPE 49.4%) |
| A2 | **P5.6 forecast CSV + PRISM tab** | ✅ | `01_data/00_derived/forecast_final_2026_08.csv`, `forecast_final.parquet`, `03_analytics/Isuzu/prism/pages/19_Forecast.py` |
| A3 | **Multi-DB replenishment dashboard** | ✅ | `02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html`, `OPEN_DB_DLR_Replenishment.cmd` · UX rebuild 2026-08-19 (OS Data Map shell; NaN JSON fix) |
| A4 | **Book B revision review workbook** | ✅ | `01_data/01_Pricing/BOOK_B_REVISION_REVIEW_20260819.html`, `OPEN_BOOK_B_REVISION_REVIEW.cmd` · aligned to command-center shell |
| **A15** | **Aftermarket BI Command Center** | ✅ | `02_dashboards/sales/ISZE_Aftermarket_BI_Command_Center.html` · **SSR build-time** (0.41 MB) — duplicate `let sortKey` JS bug fixed 2026-08-19 · loop: `02_dashboards/_build/LOOP_AFTERMARKET_BI.md` |
| A5 | **GREECE in commercial stack** (5th DB) | ✅ | `build_db_dlr_commercial_stack.py` → 5 DBs incl. GREECE 2,723 PNs |
| A6 | **KS/IAM index refresh** | ✅ | KS matches **302** (126 unique PNs; was 277) in `revision_exception_queue.csv` — catalog tree expand 2026-08-25 (`ks_catalog_tree_expand_20260825.csv`, 69 rows); status `crawl_union_20260825`; Autodoc still frozen |
| A7 | **P1.3 supersession delta** | ✅ | `01_data/00_derived/supersession_billing_delta.csv`, `01_data/01_Pricing/SUPERSESSION_DELTA_NOTE_20260819.md` |
| A8 | **P1.4 list-to-pocket validation** | ✅ | `01_data/00_derived/list_to_pocket_validation_2023_2025.csv`, `LIST_TO_POCKET_VALIDATION_20260819.md` |
| A9 | **Account-health ops pack** | ✅ | `01_data/17_interactions/account_health_ops_triage.csv`, `ACCOUNT_HEALTH_OPS_TRIAGE_20260819.md` |
| A10 | **Portfolio triage CSV** | ✅ | `01_data/00_derived/portfolio_triage_20260819.csv` (20 DBs) |
| A11 | **Operating dashboard replenishment chip** | ✅ | `build_ledger.py` → `replenishment_cy2025` in ITUK/UTI ledgers |
| A12 | **db_sales_review deck** | ⏭ skipped | No explicit next DB in brief |
| A13 | **PMS BVP regain pack** | ✅ | `09_meetings/PMS_BVP_Regain_2026/PMS_BVP_Regain.html` (refreshed) |
| A14 | **Pricing history / realization pack** | ✅ | `build_pricing_history_findings.py` → derived CSVs + `02_dashboards/pricing/ISZE_Pricing_History_Findings_Dashboard.html` (integrity 59/100 provisional) |

<details><summary>Original Tier A spec (pre-build)</summary>

| # | Build | Inputs | Output | Effort |
|---|-------|--------|--------|--------|
| A1 | **P5.2 baseline forecast** (ETS/ARIMA/naive + parc) | `demand_series.parquet`, UIO v19 | `forecast_candidates.parquet`, `backtest_report.parquet` | M |
| A2 | **P5.6 forecast CSV + PRISM tab** | A1 | `forecast_final_*.csv`, `pages/19_Forecast.py` | S–M |
| A3 | **Multi-DB replenishment dashboard** | `replenishment_bridge*.parquet` | `02_dashboards/sales/ISZE_DB_DLR_Replenishment_CY2025.html` + launcher | M |
| A4 | **Book B revision review workbook** | `revision_book_b_top_review.csv` | Excel/HTML internal under `01_data/01_Pricing/` | S |
| A5 | **GREECE in commercial stack** (5th DB) | `dealer_sellout_long_GREECE_CY2025.csv` | Extend `build_db_dlr_commercial_stack.py` | S |
| A6 | **KS/IAM index refresh** | KS crawl CSVs, PR00 | More revision-queue matches (now ~148) | S |
| A7 | **P1.3 supersession delta** | `pn_supersession_map.csv`, billing | Derived CSV + note | S–M |
| A8 | **P1.4 list-to-pocket validation** | PR00/ZPR1 2023–25, billing | Validation note | M |
| A9 | **Account-health ops pack** (draft thresholds) | `account_health.parquet`, calibration CSVs | Internal triage / PRISM internal tab | S |
| A10 | **Portfolio triage CSV** | Early warning + account health + GPS/PMS | Monday sort table | M |
| A11 | **Operating dashboard replenishment chip** | Replenishment summary | Extend `build_ledger.py` + DB HTML | M |
| A12 | **db_sales_review deck** (next DB in profiles) | `db_profiles.yaml`, billing, PBI | `09_meetings/*_Sales_Review_*` | M/DB |
| A13 | **PMS BVP regain pack** | BVP crossref, billing | Per-DB report pattern | S/DB |
| A14 | **Pricing history / realization pack** | Dated lists + billing | `build_pricing_history_findings.py` | S–M |

</details>

---

## Tier B — one decision from Jerome

| # | Build | Decision |
|---|-------|----------|
| B1 | Book B **alloc** | **CLOSED 2026-09-22 — do not re-ask.** The ambition half (+4% / +5% / launch-only) is closed permanently per Jerome; the +5% flat simulation of 2026-09-22 is its last output. This row is historical. Record: `00_docs/PRICE_AMBITION_CLOSED_2026-09-22.md` |
| B2 | **Seed €** for 9,591 no-L12M PNs | IML BOM vs UTI placeholders |
| B3 | **Growth-factor sign-off** | Keep 1.24/1.25/×1.25 UTI table? |
| B4 | **Guardrail policy** | Auto-HOLD on IAM-undercut + proxy-adverse? |
| B5 | **P4 calibration (4.9)** | Amber/red thresholds |
| B6 | **G1 forecast go-live** | Sign 98.2% catalogue or wait P1.4/1.5 |
| B7 | **P5 override policy** | Who may delta forecast + audit |
| B8 | **Book A +3% alloc** | Explicit rebuild only |
| B9 | **ITUK brake wear factor** | 0.4 vs 0.8 |
| B10 | **Competitor vintage labels (shared)** | Rebuild when asked |

---

## Tier C — blocked on data / governance

| Blocker | Examples |
|---------|----------|
| Second full CY sell-out per DB | Real YoY elasticity (proxy only today) |
| UMI dealer sell-out (1797) | Never blend with UTI 1799 |
| OEM peer retail gaps | DAF scrape dead; manual quotes |
| θ_interval / SCR parc | Reg-year mix on UIO |
| Billing after 2026-03 | Signal→order latency |
| UTI PartSales H1 2025 hole | Feb–Jul mailbox gap |
| Email / LLM (P2b) | G0b governance |
| Autodoc at scale | Cloudflare 403 |
| EPC supersession | IE40 `newest_pn` only |
| ~15 DBs no sell-out | FY2027 programme |
| Gross/SPA from billing | Closed — net-only |

---

## If you say “build one more thing today”

0. **Command center (start here)** — `OPEN_Aftermarket_BI_Command_Center.cmd` · € leakage by DB/AIM, Monday fix list  
1. **A1 P5.2 forecast** — first measured WAPE baseline; zero pricing touch.  
2. **A3 replenishment HTML** — stack already on disk.  
3. **A4 Book B review workbook** — `revision_book_b_top_review.csv` (500 rows; leakage-heavy; **IUK ≠ ITUK**).  
4. **A5 GREECE in stack** — half-day, sell-out already in JSON.  
5. **A6 KS join refresh** — widen IAM guardrail coverage.

**Do not burn today without explicit ask:** Book B alloc · Book A +3% · real elasticity story · UMI+UTI blend · P2b email LLM.

---

## Coverage snapshot

| DB | Sell-out raw | Commercial stack | Notes |
|----|--------------|------------------|-------|
| ITUK | ✅ dealer×PN | ✅ | Richest grain |
| UTI | ✅ 1799 | ✅ | ≠ UMI 1797 |
| IUK | ✅ | ✅ | ≠ ITUK |
| IRELAND | ✅ Harris | ✅ | ≠ IUK |
| GREECE | ✅ Petros | ✅ | A5 done 2026-08-19 |
| UMI | ❌ | ❌ | IDS Israel only |
| KS/IAM | ~500 SKUs crawled | **302 in queue** (126 unique PNs) | catalog expand 2026-08-25; Autodoc frozen |

**PRISM:** 19 pages; no forecast page yet; account health not wired; internal-only leakage/elasticity/scrape.
