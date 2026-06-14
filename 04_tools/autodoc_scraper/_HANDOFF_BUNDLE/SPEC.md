# SPEC — engine contract (`engine.py` + `bi_shell.py`)

**Rule:** every number traces to a source file or editable config in `sources.yaml` / `pms_parts_config.yaml`.

**Status:** Engine implemented. IAM scoring is **out of scope** for this bundle (parent folder only).

---

## Decisions (signed for this build)

| Topic | Decision |
|-------|----------|
| **ITUK UIO (default)** | `smmt_car_park` — v17 sheet 4 `2024A` (~22,389), aligned with PRISM `uio_units`. `pms_calc` (11,900) for fleet exercise only. Sheet 1 cohort (~121k) = diagnostic. |
| **PRISM vs engine** | **Do not compare** ITUK tab `potential_units` with All distributors `expected_qty`. PRISM scope is usually `N75_only`; engine uses PMS Calc whole-fleet frequencies. |
| **UIO attribution** | Display PRISM `uio_source` field verbatim (e.g. `ituk_dvla_2026`). Workbook sheet 4 cites SMMT via ITUK — confirm with PRISM pipeline owner. |
| **PMS classification** | Primary: PMS Calc category list. **Description regex allowed only** for axle-level splits (brake front/rear) where `AIM_Category` cannot separate. |
| **PMS basket (default)** | `Maintenance + Wear Repair` per `AIM_DemandType`, filtered to mapped PMS categories. **Per-model PMS parts:** collect via `MODEL_REFINEMENT_TRACKER.xlsx` (not yet in engine). |
| **Brake pad qty (v3 / sales)** | **1 qty = 1 brake pad** (signed Jerome, May 2026). Engine `parts_per_service` in yaml still reflects pads per axle for *potential* calc. |
| **Pan-EU distributors** | Only names in `sources.yaml` → `distributor_aliases` with v17 UIO and/or PRISM row. **Exclude MIDI Europe** and territories without UIO. |
| **PRISM capture** | Use **`N75_only`** `expected_qty` for multi-DB capture (signed — same as audit). |
| **Mileage (segmented)** | Default engine still reads PMS Calc **80,000 km/yr**; recommended overrides by tonnage in `MODEL_REFINEMENT_TRACKER.xlsx` (e.g. LCV D-Max **45,000** until DB confirms). |
| **FX** | `sources.yaml` → `fx_rates` (GBP_EUR, SEK_EUR, `as_of`). |
| **GP %** | ITUK: PN-level **Margin %** from `ITUK_Parts_Sales_Classification_CY2025.xlsx` (PR00-weighted). Fallback 35% in `sources.yaml`. `Sales to Dealers_ITUK` = qty only — no cost/turnover. |
| **Multi-DB actuals** | Prefer PRISM `pms_capture_by_db_year.csv`; ITUK dealer sales file when present. |
| **IAM T/Q / P(sub)** | **Not in bundle.** Parent `iam_scoring.py` + CSVs — lookup lab only. |

---

## `compute_view()` outputs

- `Summary KPIs`, `Category lost sales` (includes `over_capture_units`), `PN drill-down`, `Brand league` (scraped)
- `PMS by model (summary|detail)`, `ITUK car park by model` — proportional UIO share until PN×model actuals
- `PMS by distributor (summary|detail)` — PRISM path includes `prism_scope`, `prism_uio_source`
- `Unmapped PMS PNs` — regex gap report
- `Methodology` — scope note string

---

## Things the bundle engine must NOT do

- No `substitution_probability` or invented P(sub)
- No `iam_brand_tiers` judgment table inside engine
- No hardcoded 80,000 km/yr without reading PMS Calc (flag default if missing)
- No comparing PRISM and engine potentials without UI warnings

---

## Refinement tracker (per model)

**`MODEL_REFINEMENT_TRACKER.xlsx`** — tabs: Files guide, Decisions, **Model refinement** (checklist), ITUK car park by model, Distributor scope, PMS Calc models.

Regenerate after v17 upgrade:

```powershell
python scripts/build_model_refinement_sheet.py
```

---

## Still open (data collection — not blocking BI)

1. **Per-model PMS mileage** — `pms_parts_config.yaml` `models:` block scales ITUK allocation by `annual_mileage_km` (N75 80k, N35 60k, LCV 45k). Category intervals still global until PN×model actuals exist.
2. **ITUK N35/N75 VIN UIO** — replace placeholders in PMS Calc `UIO Data` sheet.
3. **PRISM `uio_source` label** — confirm SMMT vs DVLA wording with pipeline owner (number 22,389 agreed).
4. **DB mileage validation** — each distributor confirms km/yr per tonnage (see tracker `db_to_check` column).

---

## Inputs (via `sources.yaml`)

- v3 PN matrix, v17 UIO (sheet 4 for ITUK car park), PMS Calc Assumptions, PRISM derived CSV, dealer sales pattern, scraper CSVs.

---

## How to use

1. `run_bi.bat` → Engine output tab  
2. Pick ITUK UIO basis and period/year in sidebar  
3. Use **All distributors** for PRISM capture; **ITUK tab** for PMS Calc what-if  
4. For HTML: parent `build_executive_dashboard.py --variant all`
