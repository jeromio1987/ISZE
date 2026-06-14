# Runbook — Monthly sales analytics refresh (W1)

**Owner:** Jerome  
**Cadence:** Monthly (or when new CY billing arrives)  
**Prerequisite:** New SAP export approved for ingest  
**Sign-off:** Green `01_data/derived/_verification_report.json` (**0 fail**)

**Human overview:** [HUMAN_ONBOARDING.md](HUMAN_ONBOARDING.md) §3

---

## Scope

End-to-end: SAP XLSX → Phase 1 parquet (`build_sales_fact_from_cy.py` **or** Excel PQ living model) → optional Phase 2/3 CSV exports → PRISM derived CSVs → dashboard JSON → optional HTML publish.

---

## Preconditions

- [ ] New file in `01_data/_INBOX/` (or existing CY file updated in `01_data/raw/sales/`)
- [ ] UIO workbook current if parc changed — see `06_uio/_CURRENT/README.md`
- [ ] No uncommitted experimental edits in `03_analytics/Isuzu/prism/scripts/`
- [ ] `$env:ISZE_ROOT` set (or use default ISZE path)

---

## Step 1 — Ingest raw billing

1. Move SAP export from `_INBOX/` to `01_data/raw/sales/` (naming: `CY2025.XLSX`, etc.).
2. Update **Last refreshed** row in `01_data/DATA_MANIFEST.md`.
3. **Do not** load raw files into GPT or external tools.

---

## Step 2 — Phase 1 (Sales_Fact)

**Workbook (schema + DQ template):** `01_data/models/Phase1_Sales_Clean_Model_Starter.xlsx`  
**Raw inputs:** `01_data/raw/sales/CY2023-2024.XLSX`, `CY2025.XLSX` (+ `FY26.XLSX` when filed)  
**Machine output:** `01_data/derived/sales_fact.parquet`

> **Repo note (2026-06-13):** the checked-in Phase 1 file is a **starter template** (no Power Query mashup embedded). W1 production builds parquet via PRISM Python (Step 4). Use the Excel clicks below when you maintain a **living copy** with PQ saved in the workbook, or for one-time PQ build from the `Import_Instructions` sheet.

### 2A — Authoritative path (current monthly default)

Skip Excel for parquet. Step 4 runs `build_sales_fact_from_cy.py`, which reads the CY files above and writes `sales_fact.parquet` (~434,861 rows as of 2026-05-15).

### 2B — Excel Power Query path (living workbook)

**One-time build** (follow `Import_Instructions` sheet in the Phase 1 workbook):

| Step | Excel clicks | Detail |
|------|--------------|--------|
| 1 | **Data** → **Get Data** → **From File** → **From Workbook** | Load each CY file separately (`CY2023-2024.XLSX`, `CY2025.XLSX`, `FY26.XLSX` when present). Path: `$env:ISZE_ROOT\01_data\raw\sales\`. **Do not edit raw workbooks.** |
| 2 | Power Query Editor → **Transform** → **Use First Row as Headers** | Promote headers; remove empty top rows only if present. |
| 3 | Per query: **Choose Columns** | Keep fields listed on `Column_Mapping` sheet (Billing Date, Sold-to pt, Material, SaTy, Billed Quantity, Net value, …). |
| 4 | **Add Column** → **Custom Column** | Hardcode `Source File` = file name (e.g. `CY2025.XLSX`). |
| 5 | Set types | Dates → date; customer/material/doc → text; qty/value → decimal number. |
| 6 | **Add Column** → **Custom Column** on SaTy | `Text.Upper(Text.Trim([SaTy]))` |
| 7 | **Home** → **Append Queries** → **Append Queries as New** | Append the three staging queries → name **`Sales_Fact`**. |
| 8 | **Home** → **Merge Queries** | Merge `Sales_Fact` with **`Order_Type_Master`** query (from `Order_Type_Master` sheet table) on **SaTy** → add factor, urgency weight, planned/urgent group. |
| 9 | **Add Column** | `Estimated Base Sales` = Net Sales ÷ SaTy Factor; `SaTy Impact` = Net Sales − Base Sales (per `Column_Mapping`). |
| 10 | **Close & Load To…** → **Table** → **Existing worksheet** | Load to `Sales_Fact_Template` sheet (or new `Sales_Fact` sheet). |

**Monthly refresh** (after PQ exists in your living copy):

1. Open your Phase 1 living workbook (save-as from starter if needed).
2. **Data** → **Refresh All** (or **Queries & Connections** → **Refresh All**).
3. Open **`Data_Quality_Checks`** sheet → review **`DataQualityChecks`** table (missing date/customer/material/SaTy, unknown SaTy, zero/negative qty/sales).
4. On **`Sales_Fact`** / **`Sales_Fact_Template`**: confirm row count vs prior month (~434,861 baseline; log delta in `CHANGELOG.md` if material).
5. **Export parquet** — Excel has no native parquet export. Either:
   - **Preferred:** rely on Step 4 `build_sales_fact_from_cy.py` (same raw inputs), or
   - **Excel-only fallback:** load `Sales_Fact` query → **Close & Load** to sheet → save intermediate CSV to `_INBOX/` → convert with PRISM script (do not hand-edit parquet).

**Sanity check:** raw CY row totals should reconcile to parquet (footer/grand-total rows dropped — see comment in `build_sales_fact_from_cy.py`).

---

## Step 3 — Excel Phase 2 & 3

**Workbooks:**

- `01_data/models/Phase2_Order_Behaviour_Model.xlsx`
- `01_data/models/Phase3_Demand_Stocking_Model.xlsx`

**Prerequisite:** `sales_fact.parquet` exists (Step 2A or 2B) **or** `Sales_Fact` table populated in Phase 2 workbook via PQ link.

> Phase 2/3 repo files are **formula + pivot templates**. Refresh pivots / recalc after Sales_Fact updates. Export the three summary CSVs below when you use Phase 2/3 for customer meetings (optional for PRISM KPIs — Step 4 rebuilds GPS/PMS from parquet).

### Phase 2 — Order behaviour

1. Open `Phase2_Order_Behaviour_Model.xlsx`.
2. If Sales_Fact is a PQ connection: **Data** → **Refresh All**.  
   If formula-only: **Formulas** → **Calculate Now** (or **F9**).
3. Review **`Phase2_Dashboard`** KPIs (Total Sales, Urgent Sales Share, SOR/PRD share) — should match loaded Sales_Fact.
4. **Export CSVs** (one file per table; active sheet only):

| Output file | Sheet | Excel table name | Clicks |
|-------------|-------|------------------|--------|
| `01_data/derived/phase2_customer_saty.csv` | `Customer_SaTy_Model` | `CustomerSaTyModel` | Activate sheet → **File** → **Save As** → `$env:ISZE_ROOT\01_data\derived\phase2_customer_saty.csv` → **CSV UTF-8 (Comma delimited) (*.csv)** → **Save** → confirm active sheet |
| `01_data/derived/phase2_part_criticality.csv` | `Part_Criticality_Model` | `PartCriticalityModel` | Same pattern → `phase2_part_criticality.csv` |

Optional review sheets (no standard export): `SaTy_Financial_Impact` / `Action_Engine`.

### Phase 3 — Demand & stocking

1. Open `Phase3_Demand_Stocking_Model.xlsx`.
2. Confirm **`raw/reference/BVP PARTS CATALOG.xlsx`** is current (Phase 3 taxonomy input).
3. **Data** → **Refresh All** (if PQ/Pivot connections exist) **or** **Formulas** → **Calculate Now**.
4. Review **`Phase3_Dashboard`** decision buckets (local stock / central stock / PRD / campaign candidates).
5. **Export:**

| Output file | Sheet | Excel table name | Clicks |
|-------------|-------|------------------|--------|
| `01_data/derived/phase3_stocking_actions.csv` | `Stocking_Action_List` | `StockingActionList` | Activate sheet → **File** → **Save As** → `$env:ISZE_ROOT\01_data\derived\phase3_stocking_actions.csv` → **CSV UTF-8** → **Save** |

6. Update **`Stocking_Action_List`** Owner / Status / Due Date columns in Excel before export if used for meeting follow-ups.

---

## Step 4 — PRISM Python build + verify

```powershell
$env:ISZE_ROOT = 'C:\Users\jerom\Desktop\claude\ISZE'  # or your clone
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
.\scripts\run_pipeline_and_verify.ps1
```

1. Read `01_data/derived/_verification_report.md`.
2. **If fail:** fix root cause; do **not** update `FACTS.md`.
3. **If warn:** document reason in `03_analytics/Isuzu/prism/CHANGELOG.md` or root `CHANGELOG.md`.

Cursor skill equivalent: `.cursor/skills/isze-verify-pipeline/SKILL.md`

---

## Step 5 — Headline figures

1. If metrics changed **intentionally**: update `FACTS.md` + `03_analytics/Isuzu/prism/data/facts_anchor.yaml` together.
2. `verify_facts_drift.py` runs as part of the pipeline — must pass after FACTS edit.

---

## Step 6 — Dashboard JSON

```powershell
cd $env:ISZE_ROOT\03_analytics\Isuzu\prism
python scripts\build_isze_dashboard_json.py
```

Confirm `01_data/dashboards/isze_data.json` mtime updated.

Tender JSON (`tender_data.json`) is refreshed by weekly `isze-weekly-tender-scrape` — not part of monthly billing refresh unless tender pipeline also ran.

---

## Step 7 — Optional publish

| Target | Action |
|--------|--------|
| HTML dashboards | Edit `02_dashboards/` → `02_dashboards/sync_to_deploys.ps1` |
| GitHub context MD | `02_dashboards/sync_context_to_github.ps1` if whitelist docs changed |

**Never** edit `07_deploy/` directly.

---

## Step 8 — GPT-safe slice (month-end)

1. Rebuild `01_data/gpt_safe/` aggregates per `01_data/gpt_safe/EXPORT_MANIFEST.md`.
2. Reconcile figures with `FACTS.md` before upload.
3. Update `08_gpt/UPLOAD_STATUS.md` after GPT Enterprise upload.

---

## Rollback

| Asset | Policy |
|-------|--------|
| Previous parquet/CSVs | `[TODO: Jerome — backup location before overwrite]` |
| Git | ISZE root + PRISM submodule; deploy via `isze-dashboard` repo only |
| FACTS.md | Git history or manual revert to prior verified figures |

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| ITUK capture band fail | `data/verification_fixtures.yaml` vs UIO override in `config.py` |
| Row count warn | New CY rows — log in `CHANGELOG.md` |
| Parquet stale mtime | Phase 1 PQ not re-run |
| FACTS drift fail | Update `facts_anchor.yaml` with intentional change |
| `gpt_safe/` stale figures | Re-export after green verify (see FACTS.md change log) |

---

## Automation cross-reference

Manual W1 refresh — not a scheduled job. Related automations:

| Job | Relationship |
|-----|--------------|
| `isze-memory-review` | Run after large doc edits post-refresh |
| `isze-dashboard-freshness-check` | Flags stale HTML/JSON mtimes |
| `autodoc-monthly-refresh` | Separate competitive price data |

Register: [AUTOMATION_REGISTER.md](AUTOMATION_REGISTER.md)
