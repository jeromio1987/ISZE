# ISZE data dictionary

**Last schema sync:** 2026-06-13 (index created — column detail phased)  
**Authority split:**

| Layer | File | Owns |
|-------|------|------|
| Column semantics (this file) | `01_data/DATA_DICTIONARY.md` | Fact table, derived CSVs, dashboard JSON keys |
| Business formulas | `03_analytics/Isuzu/prism/docs/metric_dictionary.md` | PMS, GPS, BVP capture definitions |
| Dashboard build contracts | `03_analytics/Isuzu/prism/docs/dashboard_contracts.md` | Build script ↔ output column lists |
| GPT-upload subset | `01_data/gpt_safe/DATA_DICTIONARY.md` | Safe field blurbs only — links here |

**Change protocol:** schema change in `build_*.py` → update this file + `dashboard_contracts.md` + `verification_fixtures.yaml` → run pipeline + verify → note in `03_analytics/Isuzu/prism/CHANGELOG.md`.

---

## sales_fact.parquet (Phase 1 / PRISM)

**Grain:** one row per billing line  
**Build:** `03_analytics/Isuzu/prism/scripts/build_sales_fact_from_cy.py` (primary for agents) or Excel Phase 1 export  
**Location:** `01_data/derived/sales_fact.parquet`

| Column | Type | Definition | Source | Sensitive |
|--------|------|------------|--------|-----------|
| billing_date | date | SAP billing date | `raw/sales/CY*.XLSX` | |
| sold_to | str | Distributor / customer code | SAP | **Y** — never upload |
| material | str | Part number | SAP | |
| billed_qty | float | Quantity billed | SAP | |
| net_sales_eur | float | Net value EUR | SAP + FX rules | |
| saty | str | Order type (SaTy) | SAP | |
| saty_factor | float | Price/urgency factor | `Order_Type_Master` (Phase 1) | |
| dq_flag | str | Phase 1 data-quality flag | Phase 1 DQ checks | |
| line_kind | str | parts / transport / rebate / etc. | PRISM load tagging | |
| distributor_code | str | Normalised DB code (ITUK, UTI, …) | Master mapping | |

> **Phase 1:** Expand with full parquet schema introspection after Jerome confirms column list from Excel template.

---

## Derived CSVs (index)

| File | Build script | Row grain | Key columns | Contract |
|------|--------------|-----------|-------------|----------|
| `pms_capture_by_db_year.csv` | `build_bvp_p0_p1.py` | db × year × category × line_type | capture_rate, expected_qty, actual_qty | metric_dictionary § PMS |
| `gps_spu_by_distributor.csv` | GPS engine | db × year | spu_eur, uio_units | metric_dictionary § GPS |
| `mix_genuine_bvp_pms.csv` | pipeline | db × year | bvp_share_units, bvp_share_eur | metric_dictionary |
| `genuine_bvp_crossref.csv` | crossref build | genuine_pn × bvp_pn | pair mapping | metric_dictionary |
| `pms_opportunity_matrix.csv` | `build_pms_opportunity_matrix.py` | db × category × year | tam_eur, capture_rate_* | dashboard_contracts §3 |
| `metrics_snapshot.json` | `build_metrics_snapshot.py` | headline KPIs | machine-readable | FACTS.md anchor |

Full build list: `03_analytics/Isuzu/prism/docs/dashboard_contracts.md` status table.

---

## Dashboard JSON keys

### isze_data.json (`01_data/dashboards/`)

Aggregated KPIs for static HTML. Built by `build_isze_dashboard_json.py`.  
**Deploy-side fetch:** `../Data/dashboards/isze_data.json` (GitHub Pages compatibility path — not local source).

### tender_data.json (`01_data/dashboards/`)

Tender monitor feed. Built by `04_tools/ISZE_Tender_Monitor_Install/tender_scraper_v3.py` + publish step.

---

## Enums & codes

| Code set | Definition |
|----------|------------|
| SaTy values | Phase 1 `Order_Type_Master` |
| `line_type` | `total` \| `genuine` \| `bvp` (PMS capture splits) |
| `pms_category` | oil_filter, air_filter, fuel_filter, brake_pad, clutch, … |
| `dq_flag` | Phase 1 DQ checks — see Phase 1 workbook |
| Traffic light (GPS) | green ≥ €150 SPU, amber €50–150, red < €50 |
| `distributor_code` (DB) name variants + SAP sold-to codes | `03_analytics/Isuzu/prism/data/db_name_and_sold_to_mapping.csv` |

---

## Phase models (Excel)

| Workbook | Role | Output |
|----------|------|--------|
| `models/Phase1_Sales_Clean_Model_Starter.xlsx` | Sales_Fact clean | `derived/sales_fact.parquet` |
| `models/Phase2_Order_Behaviour_Model.xlsx` | Order behaviour | `derived/phase2_*.csv` |
| `models/Phase3_Demand_Stocking_Model.xlsx` | Demand / stocking | `derived/phase3_*.csv` |

See `01_data/DATA_MANIFEST.md` and [RUNBOOK_MONTHLY_REFRESH.md](../00_docs/RUNBOOK_MONTHLY_REFRESH.md).

---

## Expansion roadmap (P1)

1. Full `sales_fact.parquet` column list from schema dump.
2. Top 10 derived CSVs — column tables from `dashboard_contracts.md`.
3. `isze_data.json` key-path table for HTML maintainers.
