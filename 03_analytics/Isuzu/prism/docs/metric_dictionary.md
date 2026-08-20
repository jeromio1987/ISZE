# PRISM metric dictionary — BVP, PMS, GPS

Use this when building decks or comparing numbers across layers. **One green pipeline run**
(`run_pipeline_and_verify.ps1`) is the sign-off source for all derived metrics.

---

## Layer map

| Layer | Code / page | Primary question | Canonical derived file |
|-------|-------------|------------------|-------------------------|
| **UIO** | `1_UIO` | How many trucks in parc? | UIO Excel → loaders |
| **GPS** | `2_GPS` | EUR spent per truck per year? | `gps_spu_by_distributor.csv` |
| **PMS** | `3_PMS` | % of expected service demand sold? | `pms_capture_by_db_year.csv` |
| **BVP** | `4_BVP` | Of genuine+BVP sold, how much is BVP? | `mix_genuine_bvp_pms.csv` |

GPS and PMS are **siblings** (both need UIO). BVP **mix** sits on catalog-tagged sales, not on expected demand.

---

## PMS capture rate

**Definition:** `actual_qty ÷ expected_qty` (uncapped in `pms_capture_by_db_year.csv`).

**Display:** dashboards JSON / some charts show `min(rate, 100%)` for headline tiles only.

**Capture above 100%** on `line_type = total` is valid when actuals include sales beyond the
Isuzu UIO denominator (multi-segment PNs, LCV/N35 volume at truck distributors, cross-OEM
sales such as DAF). Do **not** remove those sales to force the rate below 100%.

**Expected demand (per distributor × year × category):**

```
base = UIO × services_per_year × addressable_pct
consumables (filters): expected = base × consumable_factor
wear (brake / clutch): expected = base × wear_factor
```

`consumable_factor`: oil / fuel / urea = 1.0; **air = 0.5** (provisional 2026-07-02 — air element
~every 2nd service, pending IML confirmation; was 1.0 flat, integrity flag C); blower = 1.0 (Jerome 2026-07-26 — aligned with oil/fuel/urea; was 0.25 cabin placeholder).
All factors editable in `data/pms_capture_assumptions.yaml` — see `docs/pms_service_intervals.md`.

| Scope | services_per_year | addressable_pct | wear (brake) |
|-------|-------------------|-----------------|--------------|
| N75 (ITUK, UTI, …) | **0.5** | **70%** | 0.5 |
| LCV (IUK, UMI) | 1.0 | 70% | 0.5 |
| N35 blend (all) | 0.75 | 70% | 0.5 |

**ITUK UIO override:** **22,389** (DVLA Mar 2026) — not V13 surviving parc alone.

**Actuals:** ITUK **registry** plus every **BVP-catalog** PMS part number with a `pms_category` (oil/fuel/air/urea filters, brake, clutch wear), then model scope (`N75_only` for ITUK). Registry wins when both apply (`build_bvp_p0_p1.py`, `CAPTURE_FILL_CATALOG_PMS`).

**Line types in `pms_capture_by_db_year.csv`:**

| line_type | Meaning | Cap at 100%? |
|-----------|---------|--------------|
| `total` | genuine + BVP | Display cap 100%; CSV uncapped |
| `genuine` | genuine only | No |
| `bvp` | BVP only | No |

### Fleet vs PMS pilot scope (ITUK)

| Concept | What it is |
|---------|------------|
| **DVLA fleet (22,389)** | All registered Isuzu vehicles in UK — N35, N75, N50, F-series, … |
| **PMS capture denominator** | Bucketed N75 UIO (cv_std + f_series) × 0.5 svc/yr × 100% addressable (re-based 2026-07-15) |
| **PMS capture actuals** | Registry + BVP catalogue PMS lines sold (incl. `pms_model = multi` and cross-OEM) |

High capture % means “more filter units sold than the N75-only proxy expects,” not “wrong data.”

**Do not confuse with:**

- **BVP unit share** (mix) — different numerator and denominator
- **Legacy 1.5 svc/yr** dealer math (~10% / ~17% oil filter) — obsolete vs PRISM
- **Cover ratio** from mapped fleet (12,010) — different UIO denominator

---

## BVP mix / share

**Definition:**

- `bvp_share_units` = `bvp_qty ÷ (genuine_qty + bvp_qty)`
- `bvp_share_eur` = `bvp_eur ÷ (genuine_eur + bvp_eur)`

**Universe:** Catalog-matched genuine and BVP lines with in-scope `pms_category` (broader than capture registry). Quantities are typically **higher** than PMS capture actuals.

**BVP has no capture rate** — it is not measured against expected demand.

**Related:** `genuine_bvp_gap_pp` in `pms_opportunity_matrix.csv` = total capture − genuine capture (percentage points of captured demand).

**Substitution story (PRISM tab):** Combines `substitution_by_pair_year.csv`, `substitution_by_db_year.csv`, `mix_genuine_bvp_by_subgroup.csv` (YoY), and `pms_opportunity_matrix.csv` (€ gap / TAM) for one distributor narrative.

---

## GPS (spend per unit)

**Definition:** `spend_per_unit_eur` = `total_sales_eur ÷ uio_units` (net parts sales after exclusions).

**Traffic light (default):** green ≥ €150, amber €50–150, red &lt; €50.

**UIO:** Year-specific when available; else **2024 proxy** (`uio_proxy_used = True`). ITUK uses **22,389** when override applies.

**Do not confuse with:** part-level “genuine parts share” in older specs — in PRISM, **GPS = spend per unit only**.

---

## ITUK PMS — IML v7 headline (external standard, adopted 2026-07-02)

Source: `ITUK_PMS_Analysis_Apr2026_v7_reclassified.xlsx` · ISZE→ITUK (General) · CY2025  
Constants: `prism/data/iml_v7_ituk_cy2025.yaml`

| Parameter | Value |
|-----------|-------|
| UIO | 22,389 full DVLA |
| Oil/Fuel/Air freq | 1.25×/yr |
| Clutch/Brake freq | 0.5×/yr |
| Addressable | 100% |
| Oil-filter cover | **35.1%** |
| PMS gap (5 cat) | **€2,038,471** |

**Story:** real workshop capture gap on IML schedule — not PRISM "mix not deficit."

## ITUK oil filter — PRISM internal lane (network KPI only)

Source: `01_data/derived/pms_capture_by_db_year.csv` — **do not use for IML headlines.**
Re-based 2026-07-15: bucketed UIO split (cv_std 22,190.9 + f_series 877.0 = **23,068**) × **100% addressable** → expected **11,680.2/yr** (see FACTS.md §1b).

| Year | actual total | uncapped total | **total capture (cap 100%)** | genuine | BVP | revenue (total) |
|------|--------------|----------------|-------------------------------|---------|------|------------------|
| 2023 | 18,030 | 154% | **100%** | 74% | 81% | €138,257 |
| 2024 | 9,750 | 84% | **84%** | **62%** | 21% | €62,384 |
| 2025 | 13,599 | 116% | **100%** | **88%** | 29% | €96,024 |

Read this as: internal network KPI — filters saturated on N75-scoped denominator. See `isze_data.json` → `pms.ituk_prism_lane`. The 2026-07-15 re-base was a bug fix (corrected a 2-market hardcoded allowlist that mis-scoped 14 of 18 distributors), not a data change.

## DO NOT QUOTE — obsolete oil-filter capture figures

The following numbers exist in older briefs / memos / chat history. They are **wrong** vs the verified PRISM pipeline and must not be used externally.

| Figure | Where it came from | Why it's wrong |
|--------|--------------------|----------------|
| **9.8% (CY2024) / 17.3% (CY2025)** | `project_isze.md` memory, older PMS slide | Denominator = UIO × **1.5 svc/yr** ≈ 33,584 (legacy ISZE-wide math, **not N75**). PRISM uses 0.5 svc/yr × 70% addressable = 7,836. |
| **~61% total CY2024** | earlier draft of this dictionary | Stale — actual capped total is 100% (uncapped 102%); pre-pipeline estimate |
| **~10% "legacy dealer capture"** | dealer math / 1.5 × UIO | Same defect as the 9.8% row |
| **very low** | very early note | Wrong denominator entirely (memory log confirms) |

**Rule:** IML/external ITUK quotes use **35.1%** oil filter / **€2.04M** gap (IML v7). PRISM 100% capped is internal lane only. Any figure of 0.3% or €3.5M+ is obsolete.

## Quick comparison — ITUK oil filter (other metric layers, CY2024)

| Layer | Metric | CY2024 | Source |
|-------|--------|--------|--------|
| PMS | total capture (capped) | **100%** | `pms_capture_by_db_year.csv` |
| PMS | total capture (uncapped) | **121%** | derived: 9,475 / 7,836.1 |
| PMS | genuine capture | **89%** | `pms_capture_by_db_year.csv` |
| BVP | unit share (mix) | see `mix_genuine_bvp_pms.csv` | catalog slice, all models |
| Legacy | dealer 1.5 svc/yr capture | **~10%** | DO NOT USE — see table above |

---

## Sign-off checklist

1. Run `prism/scripts/run_pipeline_and_verify.ps1`
2. Confirm `01_data/derived/_verification_report.md` — **0 fail**
3. PRISM PMS page: **Derived (verified pipeline)** mode
4. Cite files from `01_data/derived/` in external materials

---

## File index

| File | Contents |
|------|----------|
| `pms_capture_by_db_year.csv` | Capture by dist × year × category × line_type |
| `mix_genuine_bvp_pms.csv` | BVP mix by dist × year × PMS subgroup |
| `gps_spu_by_distributor.csv` | Spend per unit by dist × year |
| `pms_opportunity_matrix.csv` | TAM, gaps, `genuine_bvp_gap_pp` |
| `dashboard_contracts.md` | Column-level contracts |
