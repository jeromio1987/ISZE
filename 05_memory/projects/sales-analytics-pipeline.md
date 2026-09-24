---
topic: sales-analytics-pipeline
read_when: [pipeline, derived, parquet, data-ingest, phase-models]
canonical: 01_data/derived/, metric_dictionary.md, DATA_MANIFEST.md
last_validated: 2026-06-13
---

# Project: Sales analytics pipeline (3-phase)

_Last validated: 2026-06-13 (numbered paths)_

## Status: Active — PRISM builds `derived/`; Excel phase models remain parallel

**Canonical numbers:** `01_data/derived/*` after green `verify_derived_pipeline.py` (see `03_analytics/Isuzu/prism/docs/metric_dictionary.md`).

| Build | Script | Output |
|-------|--------|--------|
| Sales fact | `03_analytics/Isuzu/prism/scripts/build_sales_fact_from_cy.py` | `01_data/derived/sales_fact.parquet` |
| Full derived stack | `03_analytics/Isuzu/prism/scripts/run_pipeline_and_verify.ps1` | PMS, GPS, BVP CSVs + `_verification_report.*` |
| Dashboard JSON | `build_isze_dashboard_json.py` | `01_data/dashboards/isze_data.json` |

## Canonical paths

All paths under `$env:ISZE_ROOT/01_data/`:

| Role | Path |
|------|------|
| Manifest | `01_data/DATA_MANIFEST.md` |
| Data dictionary | `01_data/DATA_DICTIONARY.md` |
| Raw CY billing | `12_raw/sales/CY2023-2024.XLSX`, `12_raw/sales/CY2024-2025.XLSX` (supersedes old `CY2025.XLSX` — still on disk, not canonical) |
| Reference | `12_raw/reference/` (BVP catalog, margin, FY27 order VP) |
| Phase models | `13_models/Phase1_Sales_Clean_Model_Starter.xlsx` … `Phase3_Demand_Stocking_Model.xlsx` |
| Planning | `11_planning/` (KPI Master, FY2027 VPACC) |
| Derived | `00_derived/sales_fact.parquet`, `00_derived/pms_capture_by_db_year.csv`, etc. |
| GPT-safe slices | `15_gpt_safe/` |
| Dashboard JSON | `14_dashboards/isze_data.json`, `14_dashboards/tender_data.json` |
| Ingest staging | `90_INBOX/` |

_Path prefixes corrected 2026-08-10 — table previously used pre-reorg names (`raw/`, `derived/`, etc.); confirmed no such entries exist under `01_data/` (numbered folders only) and updated to the real numbered paths, per Jerome's request._

**Do not** re-copy CY files into `new files/`, duplicate trees, or legacy `Isuzu/data/` paths.

## Phase 1 — Sales clean (Excel path)

- **Input:** ~435k billing lines (CY2023-24 + CY2025), optional margin + customer order VP.
- **Workbook:** `models/Phase1_Sales_Clean_Model_Starter.xlsx` — Column_Mapping, Order_Type_Master, Sales_Fact_Template, DQ checks.
- **Output:** `Sales_Fact` table → may export to `derived/sales_fact.parquet` (PRISM build is primary for agents).

## Phase 2 — Order behaviour

- **Input:** Sales_Fact from Phase 1 or parquet.
- **Workbook:** `models/Phase2_Order_Behaviour_Model.xlsx`
- **Output:** `derived/phase2_*.csv` when exported.

## Phase 3 — Demand & stocking

- **Input:** Sales_Fact + Phase 2 + `raw/reference/BVP PARTS CATALOG.xlsx`.
- **Workbook:** `models/Phase3_Demand_Stocking_Model.xlsx`

## AI routing

- **Claude / Cursor:** Full `01_data/` except never push raw billing to external tools.
- **GPT Enterprise:** `gpt_safe/` + Context Pack MD only; monthly aggregates by DB, not payer-level.
- **HTML dashboards:** `dashboards/*.json` only (deploy fetch uses `../Data/dashboards/` compatibility paths).

## Next actions

- [x] Clear current verify **fails** in `_verification_report.md` — **confirmed clear 2026-07-27**: report generated 2026-07-26T20:05:36Z shows 106 pass / 0 warn / 0 fail. **Reconfirmed 2026-08-03** (report generated 2026-08-03T06:13:45Z): still 106/0/0; `_facts_drift_report.md` (same run) shows 0 drifted / 0 missing / 12 aligned. **Reconfirmed 2026-08-24**: `_verification_report.md` regenerated 2026-08-18T15:12:22Z now shows 108 pass / 0 warn / 0 fail (up from 106 — two checks added, not a regression; no fail introduced). **Reconfirmed 2026-09-23**: regenerated 2026-09-22T19:43:13Z shows 164 pass / 1 warn / 0 fail — the one warn is `uio_year.historical_gaps` (DENMARK 2012/2013 left unfilled in older years), not a fail.
- [ ] Refresh `gpt_safe/` aggregates after green verify
- [ ] Keep `DATA_MANIFEST.md` “Last refreshed” row current when CY files change
- [ ] Jerome: confirm GitHub PAT revoked (Settings → Developer settings → PATs) — archive files in `90_archive/root_files/` still contain old token until scrubbed — **done 2026-06-13** (template + living-copy paths documented)

## Related

- `00_docs/RUNBOOK_MONTHLY_REFRESH.md` — monthly W1 ritual
- `00_docs/agent/AI_STACK.md` — Tier 0–3 governance
- `05_memory/projects/pms-coverage.md`, `competitiveness.md` — downstream use cases
