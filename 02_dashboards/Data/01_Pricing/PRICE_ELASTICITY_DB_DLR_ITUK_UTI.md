# Price response DB→DLR — ITUK + UTI (internal method note)

**As of:** 2026-08-10  
**Output:** `01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv`  
**Builder:** `01_data/91_build/build_price_elasticity_db_dlr_ituk_uti.py`  
**Constraint:** elasticity / response **only** at DB→DLR. Do **not** claim ISZE→DB elasticity.  
**Israel:** UTI only — never blend UMI.

---

## Verdict

**True YoY arc elasticity is blocked** — only one full calendar year of sell-out (CY2025) for ITUK and UTI. The file labelled `UTIPartSalesCY2024.xlsx` under `01_data/05_Dealer_sellout/` is a **Jan-2025 YTD** snapshot (same family as `UTIPartSales_2025-01.xlsx`), not CY2024.

Delivered rows are therefore **`measure_kind=proxy`** (plus `blocked` stub rows for the YoY method). Filename keeps `price_elasticity_*` for roadmap discoverability; read the `measure_kind` column.

**Proceed with what we have** (Jerome 2026-08-10): do **not** wait for a second-year sell-out before using these proxies as labeled soft diagnostics. Second CY still unlocks `measure_kind=elasticity` later — it is not a gate on wiring the proxy path.

---

## Axes

| Axis | What we use | Honesty |
|------|-------------|---------|
| **Volume** | Sell-out qty CY2025 — ITUK summed dealer×PN → network PN; UTI network PN | True DB→DLR volume |
| **Price (proxy A)** | Median ISZE→DB ASP from `sales_fact` CY2025 (qty×median unit price, same as DEALER_SELL_OUT valuation) | Upstream cost to DB — **not** dealer invoice |
| **Price (proxy B)** | PR00 sim list SP % 2025→2026 (`pricing_sim_pr00_l12m`) | Planned list shock; sell-out used as **weight only** |

No SAP pocket / waterfall. Talk in **%** for list moves. FY27 target remains **+3% weighted** (separate).

### Price basis — lasting (not temporary)

**ASP / list pass-through is the lasting price axis for now.**  
DB→DLR dealer **invoice** unit prices are **not a near-term ask** (Jerome 2026-08-10) — drop that from the blocker list. If invoice series ever arrive, they can replace the proxy axis; until then every reading must stay labeled **proxy / pass-through**, never “dealer invoice elasticity.”

---

## Coverage

- **ITUK:** {'source': 'Sales to Dealers_ITUK_CY2025.xlsx', 'grain_raw': 'dealer_pn', 'n_dealers': 64, 'n_pn': 5586, 'qty': 223897.0, 'years': [2025]}
- **UTI:** {'source': 'UTIPartSales_2025-12_YTD.xlsx', 'grain_raw': 'network_pn', 'n_dealers': 0, 'n_pn': 792, 'qty': 92660.0, 'years': [2025], 'misnamed_cy2024_note': 'UTIPartSalesCY2024.xlsx is report 1/2025 (Jan YTD), NOT CY2024 — YoY blocked.'}
- Cross-section proxy categories: **42** rows (ITUK 25 / UTI 17)
- List-exposure proxy categories: **43** rows

### Gates

- Drop PN with sell-out qty < **10**
- Category needs ≥ **8** PNs to emit; `low_power` if n < **20**
- Winsorize log levels at **2%** / **98%** for cross-section

---

## Methods in the CSV

| method | measure_kind | Meaning |
|--------|--------------|---------|
| `yoy_arc_elasticity` | `blocked` | Would be real arc β from YoY lnQ/lnP — insufficient years |
| `cross_section_lnq_lnp_asp` | `proxy` | Category WLS: ln(sell-out qty) ~ ln(ASP). Level association, confounded |
| `list_shock_exposure_2025_2026` | `proxy` | Sell-out-weighted mean planned SP % change — **not** a response β |

---

## vs existing `price_volume_elasticity.csv`

That file is **ISZE→DB stocking** (billing qty × realized ASP across distributors). It must **not** be labelled DB→DLR or end-market elasticity. This new CSV is the sell-out-side track for ITUK/UTI only.

---

## Engine / allocation plug-in (wired soft signal)

Config: `paths.db_dlr_response` → `01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv`  
Code: `03_analytics/isze_pricing/db_dlr_response.py` (called from `cli.cmd_alloc`).

| What alloc does | What it does **not** do |
|-----------------|-------------------------|
| Hash the CSV as a run input | Multiply `delta` by `beta` |
| Copy proxy table into the run folder | Treat proxy as `measure_kind=elasticity` |
| Join exact `(db, PMS cat)` beta / list-shock % onto `alloc_detail` | Invent AIM→PMS maps for unmatched AIM rows |
| Flag `PROXY_ADVERSE_CROSS_SECTION` when powered beta < −0.5 | Change the +3% weighted target |

1. Keep `allocation.target = 0.03` (+3% weighted) unchanged.
2. Do **not** multiply deltas by `beta` until `measure_kind=elasticity` exists with adequate n.
3. Soft signal is diagnostic only — read `db_dlr_proxy_flag` / run `summary.md` § DB→DLR.
4. Most proxy rows are AIM taxonomy; exact PMS joins today are sparse (`air_filter` / `fuel_filter` where present). AIM rows still appear in the diagnostic export.

---

## Rebuild

```powershell
cd $env:ISZE_ROOT
python 01_data/91_build/build_price_elasticity_db_dlr_ituk_uti.py
```

### Later: unblock true elasticity (optional, not a near-term gate)

- File full-CY sell-out for ITUK and/or UTI for a second year (CY2024 or CY2026).
- Keep ASP/list pass-through as the price axis unless dealer invoice series appear.
- Re-run builder; rows with `measure_kind=elasticity` appear only when YoY pairs clear gates.
