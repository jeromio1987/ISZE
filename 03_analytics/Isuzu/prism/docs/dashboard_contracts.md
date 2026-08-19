# ISZE Dashboard Data Contracts

Division of labour: **Cursor builds the CSV** · **Claude builds the visual**

Handoff rule: Cursor runs `run_pipeline_and_verify.ps1` → green → Claude writes the page.
Each contract below is a complete brief for a `build_*.py` script.

---

## How to use this document

1. Pick a dashboard below
2. Cursor implements the `build_*.py` script producing the stated output file with the stated columns
3. Add a verify fixture entry (schema + min_rows) to `data/verification_fixtures.yaml`
4. Run `python scripts/verify_derived_pipeline.py` → must be green
5. Claude writes the Streamlit chart page

---

## Status

| # | Dashboard | Build script | Output CSV | Status |
|---|-----------|-------------|------------|--------|
| 4 | Triple Threat Quadrant | _(runtime join — no build needed)_ | — | ✅ Done |
| 3 | PMS Opportunity Matrix | `build_pms_opportunity_matrix.py` | `pms_opportunity_matrix.csv` | ✅ Done |
| 10 | Network Percentile Radar | `build_network_percentile.py` | `network_percentile.csv` | ✅ Done |
| 1 | Flying Gold Map | `build_strategic_contracts.py` | `vor_airfreight_risk.csv` | ✅ Done |
| 6 | VOR Seasonality Wheel | `build_strategic_contracts.py` | `vor_seasonality.csv` | ✅ Done |
| 12 | VOR Order Profile | `build_strategic_contracts.py` | `vor_profile.csv` | ✅ Done |
| 7 | Capture Trajectory + Forecast | `build_strategic_contracts.py` | `capture_trajectory.csv` | ✅ Done |
| 9 | Part Lifecycle Map | `build_strategic_contracts.py` | `part_lifecycle.csv` | ✅ Done |
| 14 | Revenue Concentration (Gini) | `build_strategic_contracts.py` | `revenue_concentration.csv` | ✅ Done |
| 5 | Genuine Revenue Waterfall | `build_strategic_contracts.py` | `revenue_waterfall.csv` | ✅ Done |
| 13 | Price Premium Acceptance | `build_strategic_contracts.py` | `price_premium.csv` | ✅ Done |
| 8 | PMS Basket Correlation | `build_strategic_contracts.py` | `basket_correlation.csv` | ✅ Done |
| 2 | Substitution Invasion Curve | `build_strategic_contracts.py` | `substitution_timeline.csv` | ✅ Done |
| 11 | Geographic Risk Map | `build_strategic_contracts.py` | `prism/data/distributor_geo.csv` | ✅ Done |
| 15 | Capture Recovery Simulator | `build_strategic_contracts.py` | `capture_recovery_model.csv` | ✅ Done |
| 16 | ITUK PMS PN Audit | `build_ituk_pms_pn_audit.py` | `ituk_pms_pn_audit.csv` | ✅ Done |

---

## Contract 3 — PMS Opportunity Matrix

**File:** `scripts/build_pms_opportunity_matrix.py`
**Output:** `01_data/derived/pms_opportunity_matrix.csv`

```
distributor_code    str    e.g. "ITUK"
pms_category        str    oil_filter / air_filter / fuel_filter / brake_pad / clutch
year                int    2023 / 2024 / 2025
capture_rate_total  float  actual_qty_total / expected_qty (line_type=total)
capture_rate_genuine float actual_qty_genuine / expected_qty (line_type=genuine)
revenue_gap_eur     float  from pms_capture_by_db_year (already there)
avg_sp_eur          float  actual_rev_eur / actual_qty (total)
tam_eur             float  expected_qty × avg_sp_eur  ← NEW: total addressable market
uio_units           int
genuine_bvp_gap_pp  float  capture_rate_total - capture_rate_genuine (BVP's share of capture)
country             str    from gps_spu_by_distributor join
region              str
```

**Logic:**
- Source: `pms_capture_by_db_year.csv` + `gps_spu_by_distributor.csv`
- Pivot line_type to get total + genuine capture side by side
- Compute `avg_sp_eur` = actual_rev_eur / actual_qty where actual_qty > 0 (use total line_type)
- Compute `tam_eur` = expected_qty × avg_sp_eur
- Left-join country/region from gps_spu_by_distributor on (distributor_code, year)
- Only include rows where expected_qty > 0

**Verify fixture to add:**
```yaml
pms_opportunity_matrix:
  min_rows: 200
  capture_rate_max: 1.05
  tam_eur_min: 1.0
```

---

## Contract 10 — Network Percentile Radar

**File:** `scripts/build_network_percentile.py`
**Output:** `01_data/derived/network_percentile.csv`

```
distributor_code     str
year                 int
metric               str    gps_spu / total_capture / genuine_capture / bvp_mix / aim_risk
raw_value            float  the actual value for this distributor/year/metric
percentile_rank      float  0–100 (higher = better for all metrics; invert bvp_mix and aim_risk)
network_median       float  median raw_value across all distributors for this year/metric
vs_median            float  raw_value - network_median (positive = above median)
n_distributors       int    how many distributors in the network for this year/metric
```

**Logic:**
- Source: join `gps_spu_by_distributor.csv` + `pms_capture_by_db_year.csv` + `aim_exposure_by_db_year.csv`
- For each year, compute one row per distributor × metric:
  - `gps_spu`: spend_per_unit_eur from gps_spu_by_distributor
  - `total_capture`: sum(actual_qty) / sum(expected_qty) for line_type=total across all pms_categories
  - `genuine_capture`: same for line_type=genuine
  - `bvp_mix`: from mix_genuine_bvp_by_family — mean bvp_share_units across product families (ALL in-scope)
  - `aim_risk`: high_risk_rev_pct from aim_exposure_by_db_year
- Percentile rank: rank within year (1=worst, n=best). For bvp_mix and aim_risk, invert (lower = better percentile).
  Formula: `percentile = (rank - 1) / (n - 1) * 100`

**Verify fixture to add:**
```yaml
network_percentile:
  min_rows: 200
  metrics: [gps_spu, total_capture, genuine_capture, bvp_mix, aim_risk]
  percentile_range: [0, 100]
```

---

## Contract 7 — Capture Trajectory + Forward Projection

**File:** `scripts/build_capture_trajectory.py`
**Output:** `01_data/derived/capture_trajectory.csv`

```
distributor_code         str
pms_category             str
year                     int    includes projected years (2026, 2027)
capture_rate             float  actual for historical, projected for future
is_projected             bool
trend_slope_pp_per_year  float  regression slope (negative = declining)
trend_r2                 float  0–1 fit quality
alert_declining          bool   slope < -0.05 AND r2 > 0.5
```

**Logic:**
- Source: `pms_capture_by_db_year.csv`, line_type=total only
- For each distributor × pms_category:
  - Fit linear regression on **complete billing years only** (`modules/year_coverage.is_partial`). Partial-year actuals are still emitted (`is_projected=False`) but do not enter the slope, R², or `alert_declining` flag. Guard added 2026-08-18 after Early Warning showed 83% of declining alerts were partial-year artifacts (re-measured 33→5, 0 real declines hidden).
  - Store slope (misnomer: values are capture-rate fractions per year, not percentage points), R²
  - Project years 2026 and 2027 using the complete-year regression line (clip at [0, 1.05])
  - Flag alert_declining = True when slope < -0.05 AND r2 > 0.5
- Use `scipy.stats.linregress`

**Verify fixture to add:**
```yaml
capture_trajectory:
  min_rows: 200
  projected_years: [2026, 2027]
  r2_range: [0, 1]
```

---

## Contract 9 — Part Lifecycle Map

**File:** `scripts/build_part_lifecycle.py`
**Output:** `01_data/derived/part_lifecycle.csv`

```
part_number           str
line_type             str    genuine / bvp
product_family        str    from bvp_pn_dimension
pms_category          str    null if not PMS
first_billing_year    int
peak_billing_year     int    year with highest billed_qty
last_billing_year     int
total_revenue_eur     float  sum across all years
cagr_2yr              float  (qty_last2 / qty_first2)^0.5 - 1  (null if < 2 years)
lifecycle_stage       str    emerging / growing / mature / declining / zombie
has_bvp_equivalent    bool   True if this genuine PN has a paired BVP PN in crossref
```

**Lifecycle rules:**
- `emerging`: first_billing_year >= 2024 AND cagr_2yr > 0
- `growing`: cagr_2yr > 0.15
- `mature`: abs(cagr_2yr) <= 0.15
- `declining`: cagr_2yr < -0.10
- `zombie`: line_type=genuine AND last_billing_year <= 2023 AND has_bvp_equivalent=True

**Logic:**
- Source: `sales_fact.parquet` (via sales_loader to map sold_to → distributor_code) + `bvp_pn_dimension.csv`
- Group by part_number + line_type across all distributors
- Join product_family from bvp_pn_dimension on part_number
- Note: do NOT filter to PMS-only — show full catalog

**Verify fixture to add:**
```yaml
part_lifecycle:
  min_rows: 300
  lifecycle_stages: [emerging, growing, mature, declining, zombie]
  cagr_range: [-1.0, 5.0]
```

---

## Contract 14 — Revenue Concentration (Gini)

**File:** `scripts/build_revenue_concentration.py`
**Output:** `01_data/derived/revenue_concentration.csv`

```
distributor_code    str
year                int
line_type           str    genuine / bvp / total
gini_coefficient    float  0=equal, 1=max concentration
top10_rev_share     float  % revenue from top 10 PNs
top1_rev_share      float  % revenue from single top PN
total_pns_billed    int
total_revenue_eur   float
```

**Gini formula:**
```python
def gini(revenues):
    n = len(revenues)
    if n == 0: return 0
    s = sorted(revenues)
    cumsum = sum((i+1)*v for i, v in enumerate(s))
    return (2*cumsum) / (n * sum(s)) - (n+1)/n
```

**Logic:**
- Source: `sales_fact.parquet` grouped by distributor_code × year × line_type × part_number → sum(net_sales_value)
- line_type from join with `bvp_pn_dimension.csv` on part_number; use "total" = genuine + bvp combined
- For each distributor × year × line_type, apply Gini formula on PN-level revenues
- Also compute top-1 and top-10 shares

**Verify fixture to add:**
```yaml
revenue_concentration:
  min_rows: 100
  gini_range: [0, 1]
```

---

## Contract 5 — Genuine Revenue Waterfall

**File:** `scripts/build_revenue_waterfall.py`
**Output:** `01_data/derived/revenue_waterfall.csv`

```
distributor_code    str
year_from           int    e.g. 2023
year_to             int    e.g. 2024
product_family      str
delta_volume_eur    float  (qty_to - qty_from) × asp_from  — volume effect
delta_price_eur     float  (asp_to - asp_from) × qty_to    — price effect
delta_mix_eur       float  residual (genuine→BVP shift)     — mix effect
revenue_base_eur    float  genuine revenue in year_from
revenue_end_eur     float  genuine revenue in year_to
total_delta_eur     float  revenue_end - revenue_base (should ≈ sum of three deltas)
```

**Logic:**
- Source: `sales_fact.parquet` grouped by distributor × product_family × year for genuine PNs only
- Compute ASP = net_sales_value / billed_qty per group
- For consecutive year pairs (2023→2024, 2024→2025):
  - delta_volume = (qty_to - qty_from) × asp_from
  - delta_price = (asp_to - asp_from) × qty_to
  - delta_mix = total_delta - delta_volume - delta_price
- Only include rows where both years have revenue > 0

**Verify fixture to add:**
```yaml
revenue_waterfall:
  min_rows: 100
  year_pairs: [[2023, 2024], [2024, 2025]]
```

---

## Contract 13 — Genuine Price Premium Acceptance

**File:** `scripts/build_price_premium.py`
**Output:** `01_data/derived/price_premium.csv`

```
distributor_code        str
pms_category            str
year                    int
genuine_asp_eur         float  avg selling price genuine PNs in this category
bvp_asp_eur             float  avg selling price BVP PNs in this category
price_premium_pct       float  (genuine_asp - bvp_asp) / bvp_asp
genuine_unit_share      float  genuine_qty / (genuine_qty + bvp_qty)
genuine_units           int
bvp_units               int
n_genuine_pns           int    distinct genuine PNs billed
n_bvp_pns               int    distinct BVP PNs billed
```

**Logic:**
- Source: `sales_fact.parquet` + `bvp_pn_dimension.csv`
- Only include rows where BOTH genuine and BVP were billed for this distributor × category × year
- Group by part_number to get PN-level ASP, then average across PNs (not transactions)
- Exclude rows where bvp_units = 0 or genuine_units = 0

**Verify fixture to add:**
```yaml
price_premium:
  min_rows: 30
  price_premium_range: [-0.5, 10.0]
  genuine_unit_share_range: [0, 1]
```

---

## Contract 8 — PMS Basket Correlation

**File:** `scripts/build_basket_correlation.py`
**Output:** `01_data/derived/basket_correlation.csv`

```
distributor_code    str
year                int
pms_cat_a           str
pms_cat_b           str    always pms_cat_a < pms_cat_b (no duplicates)
correlation         float  Pearson r on monthly order quantities
co_order_months     int    months where both categories had >0 qty
total_months        int    12 (or fewer if data starts mid-year)
p_value             float  statistical significance
```

**Logic:**
- Source: `sales_fact.parquet` + `bvp_pn_dimension.csv` (to get pms_category per PN)
- Group by distributor × year × billing_month × pms_category → sum(billed_qty)
- Pivot to wide format: columns = pms_categories, rows = months
- Compute pairwise Pearson correlation across 12 months
- Only compute pairs where both categories had ≥3 months of billing
- Use `scipy.stats.pearsonr` for correlation + p_value

**Verify fixture to add:**
```yaml
basket_correlation:
  min_rows: 30
  correlation_range: [-1, 1]
```

---

## Contract 2 — Substitution Invasion Curve

**File:** `scripts/build_substitution_timeline.py`
**Output:** `01_data/derived/substitution_timeline.csv`

```
product_family              str
distributor_code            str
year                        int    2020–2025 (backfill from sales_fact if available)
genuine_units               int    total genuine billed_qty across all PNs in family
bvp_units                   int
genuine_unit_share          float  genuine / (genuine + bvp), null if both zero
bvp_first_billing_year      int    first year ANY bvp PN in this family appeared in billing
years_since_bvp_entry       int    year - bvp_first_billing_year (negative = before entry)
pre_entry_genuine_share     float  genuine_unit_share in bvp_first_billing_year - 1 (baseline)
```

**Logic:**
- Source: `sales_fact.parquet` + `bvp_pn_dimension.csv`
- For each product_family, find min(year) where a BVP PN was billed → bvp_first_billing_year
- Compute genuine and BVP units per family × distributor × year
- Compute genuine_unit_share; null when no billing at all
- Add years_since_bvp_entry = year - bvp_first_billing_year
- Families with no BVP billing at all: bvp_first_billing_year = null, years_since = null

**Verify fixture to add:**
```yaml
substitution_timeline:
  min_rows: 100
  genuine_unit_share_range: [0, 1]
```

---

## Contract 1 — Flying Gold Map  _(requires SATY data)_

**File:** `scripts/build_vor_airfreight_risk.py`
**Output:** `01_data/derived/vor_airfreight_risk.csv`

```
distributor_code        str
product_family          str
year                    int
vor_line_count          int    SATY lines flagged as VOR/urgent for this family
total_line_count        int
vor_pct                 float  vor_line_count / total_line_count
vor_revenue_eur         float  net_sales_value on VOR lines
backorder_rate          float  lines that went BO / total_line_count
weight_class            str    light (<2kg) / medium (2–10kg) / heavy (>10kg)  — from part attributes
airfreight_risk_score   float  vor_pct × backorder_rate  (0–1 composite)
```

**Logic:**
- Source: `sales_fact.parquet` with SATY order type field + part weight attribute
- VOR flag: SAP `SaTy` in **VOR**, **SVOR** → `vor`; **RUSH** → `urgent` (see `modules/saty_mapping.py`)
- Backorder: `SaTy` in **BO**, **BK** (none observed in CY2023–25; backorder_rate may be 0)
- Weight class: derive from part_number prefix rules or join with a weight reference file
- Group by distributor × product_family × year

**Implemented:** `saty` column on `sales_fact.parquet` from CY export `SaTy`.

---

## Contract 6 — VOR Seasonality Wheel  _(requires SATY data)_

**File:** `scripts/build_vor_seasonality.py`
**Output:** `01_data/derived/vor_seasonality.csv`

```
distributor_code    str
year                int
week_of_year        int    1–52
vor_count           int
total_order_count   int
vor_pct             float
```

**Logic:**
- Source: `sales_fact.parquet` with SATY order type
- Extract week_of_year from billing_date
- Group by distributor × year × week_of_year
- VOR = same flag as Contract 1

---

## Contract 12 — VOR Order Profile  _(requires SATY data)_

**File:** `scripts/build_vor_profile.py`
**Output:** `01_data/derived/vor_profile.csv`

```
distributor_code    str
year                int
order_type          str    standard / vor / urgent / backorder / other
line_count          int
revenue_eur         float
pct_of_total_lines  float
network_avg_pct     float  same order_type average across all distributors for this year
vs_network_pp       float  pct_of_total_lines - network_avg_pct
```

**Logic:**
- Source: `sales_fact.parquet` with SATY order type
- Group by distributor × year × order_type
- Compute network_avg_pct as mean across distributors for each year × order_type

---

## Contract 11 — Geographic Risk Map  _(requires lat/lon reference)_

**File:** `data/distributor_geo.csv` (static reference, Cursor or manual fill)

```
distributor_code    str
country             str
lat                 float
lon                 float
territory_label     str    e.g. "UK & Ireland"
```

**Source:** Manual lookup or geocoding from country name. No build script needed.
Join at runtime in Streamlit with gps_spu_by_distributor for the chart.

---

## Contract 15 — Capture Recovery Simulator

**File:** `scripts/build_capture_recovery_model.py`
**Output:** `01_data/derived/capture_recovery_model.csv`

```
distributor_code        str
pms_category            str
year                    int    latest year only (base for simulation)
capture_rate_actual     float
expected_qty            int
actual_qty              int
avg_sp_genuine_eur      float  from price_premium.csv or direct from sales_fact
avg_sp_bvp_eur          float
bvp_unit_share          float
gap_units               int    expected_qty - actual_qty (total)
gap_type                str    substitution / under_service / catalog_gap
gap_revenue_at_genuine  float  gap_units × avg_sp_genuine_eur
```

**Gap type rules:**
- `substitution`: BVP billed for this category AND bvp_unit_share > 0.05
- `catalog_gap`: expected_qty > 0 AND no genuine PN exists in catalog for this category × distributor
- `under_service`: everything else (demand exists, no substitution, not a catalog gap)

**Logic:**
- Source: `pms_capture_by_db_year.csv` + `bvp_pn_dimension.csv` + `price_premium.csv` (if built)
- Use latest available year only
- One row per distributor × pms_category

**Verify fixture to add:**
```yaml
capture_recovery_model:
  min_rows: 50
  gap_types: [substitution, under_service, catalog_gap]
```

---

## Contract 16 — ITUK PMS PN Audit

**File:** `scripts/build_ituk_pms_pn_audit.py`  
**Output:** `01_data/derived/ituk_pms_pn_audit.csv`  
**Page:** `pages/6_ITUK_PMS_Audit.py`

```
year                  int
distributor_code      str    ITUK
pms_category          str
category_label        str
part_number           str
pms_type              str    genuine / bvp
pms_model             str
actual_qty            float
actual_rev_eur        float
share_of_category_qty float  PN qty / category total
scope                 str    N75_only
```

**Logic:** PMS registry lines for ITUK after `filter_pms_by_scope`; group by year × category × PN.

---

_Last updated: 2026-05-22_
_Claude writes all Streamlit chart pages. Cursor writes all build_*.py scripts._
