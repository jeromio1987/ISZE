# ISZE Data manifest

**Last updated:** 2026-06-13  
**Root:** `01_data/` (under `$env:ISZE_ROOT`)

This folder is the **single canonical home** for ISZE sales analytics inputs, phase models, and dashboard JSON. Claude reads Tier 1 here; GPT Enterprise uses only `gpt_safe/` (see flags below).

---

## Folder layout

| Path | Purpose |
|------|---------|
| `_INBOX/` | Drop new SAP / BVDB exports here before filing into `raw/` |
| `raw/sales/` | Immutable billing extracts (CY2023–24, CY2025) |
| `raw/dealer_sales/` | Distributor→dealer sell-out (UTI PartSales, ITUK pivot) |
| `raw/reference/` | Catalog, margin bridge, FY27 order simulator |
| `models/` | Phase 1–3 Excel workbooks (living models) |
| `planning/` | KPI Master, VPACC action plan (not in ETL pipeline) |
| `derived/` | Machine exports: `sales_fact.parquet`, phase summaries (build after Phase 1 PQ) |
| `gpt_safe/` | Small MD/CSV only — upload to GPT Enterprise Knowledge |
| `dashboards/` | `isze_data.json`, `tender_data.json` for static HTML |

---

## File registry

| File | Location | ~Size | Phase | GPT upload? |
|------|----------|-------|-------|-------------|
| CY2023-2024.XLSX | `raw/sales/` | 22 MB | 1 — raw billing | **No** (line-level, payer) |
| CY2025.XLSX | `raw/sales/` | 15 MB | 1 — raw billing | **No** |
| BVP PARTS CATALOG.xlsx | `raw/reference/` | 347 KB | 3 — part taxonomy | No (use category summary in gpt_safe) |
| Margin analysis report.xlsx | `raw/reference/` | 216 KB | 1 — margin context | **No** (customer-level) |
| Customer order sales - VP.xlsx | `raw/reference/` | 61 KB | 1–2 — FY27 scenarios | Internal only |
| Phase1_Sales_Clean_Model_Starter.xlsx | `models/` | 19 KB | 1 — Sales_Fact | No |
| Phase2_Order_Behaviour_Model.xlsx | `models/` | 145 KB | 2 — order behaviour | No |
| Phase3_Demand_Stocking_Model.xlsx | `models/` | 51 KB | 3 — demand / stocking | No |
| KPI Master File april 2026.xlsx | `planning/` | 2.3 MB | — | No |
| Action plan FY2027 VPACC_April update.xlsx | `planning/` | 577 KB | — | No |
| UTIPartSales_2025-01 / _12_YTD | `raw/dealer_sales/UTI/` | — | UTI sell-out | No |
| DEALER_SELL_OUT.md | `raw/dealer_sales/` | — | Methodology + BVP rules | Yes |
| dealer_sellout_*.csv | `derived/` | — | PN audit / PMS compare / AIM+GPS | Internal |
| dealer_sellout_compare.json | `dashboards/` | — | UTI vs ITUK HTML | Internal |
| dealer_sellout_aim_gps.json | `dashboards/` | — | Network AIM BVP/genuine sell-out HTML | Internal |
| sellout_aim_network_mix_2025.csv | `derived/` | — | ITUK/UTI AIM mix sell-out vs billing | Internal |
| sellout_aim_by_pms_2025.csv | `derived/` | — | PMS × AIM bucket × dist | Internal |
| sellout_aim_by_subgroup_2025.csv | `derived/` | — | Subgroup × AIM bucket | Internal |
| sellout_aim_top_pn_2025.csv | `derived/` | — | Top BVP / contested genuine PNs | Internal |
| isze_data.json | `dashboards/` | — | HTML KPIs | Yes (aggregates only) |
| tender_data.json | `dashboards/` | — | Tender monitor | Yes |

**Also at Data root (unchanged):** `db_brief_mockup.html`, `ISZE_TenderIntelligence_StrategyBrief_v6.pdf`

---

## 3-phase pipeline

1. **Phase 1** — Power Query in `models/Phase1_*` loads `raw/sales/*` (+ optional margin / order files) → **`Sales_Fact`** table. Export to `derived/sales_fact.parquet` when built.
2. **Phase 2** — `models/Phase2_*` reads Sales_Fact → customer/SaTy, part criticality, action engine. Export summaries to `derived/phase2_*.csv`.
3. **Phase 3** — `models/Phase3_*` + BVP catalog → demand, stocking, PRD candidates. Export to `derived/phase3_*.csv`.

See `05_memory/projects/sales-analytics-pipeline.md` for detail.

---

## Refresh protocol

1. New SAP export → `_INBOX/` → move to `raw/sales/` (rename with date if needed).
2. Refresh Phase 1 Power Query → export `derived/sales_fact.parquet`.
3. Refresh Phase 2/3 pivots → export summary CSVs to `derived/`.
4. Regenerate `dashboards/isze_data.json` from aggregates (not from raw xlsx).
5. Update **Last refreshed** row below and optional `gpt_safe/` monthly CSV.

| Dataset | Last refreshed | Rows (approx) | Owner |
|---------|----------------|---------------|-------|
| CY2023-2024 billing | 2026-05-15 (migrated) | 287,453 | Jerome |
| CY2025 billing | 2026-05-15 (migrated) | 147,410 | Jerome |
| Sales_Fact (derived) | 2026-05-15 | 434,861 | Jerome |
| isze_data.json | *check file mtime* | — | Jerome |

---

## Dashboard JSON paths

**Local source:** `01_data/dashboards/isze_data.json`, `tender_data.json`

**Deploy-side compatibility** (GitHub Pages — do not use as local edit paths):

From `02_dashboards/*.html`:

```text
../Data/dashboards/isze_data.json
../Data/dashboards/tender_data.json
```

---

## Migration log

See `migration-log.txt` (2026-05-15 — all 10 files from `new files/` filed; `new files/` is empty).
