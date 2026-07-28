# ISZE Excel Conventions

*Apply when building or editing any Excel model for Jerome at ISZE.*

---

## General Model Principles

- **Formulas over hard-coded values** — if a number comes from a calculation, it must be a formula.
  Hard-coded constants belong in a clearly labelled "Inputs / Assumptions" section only.
- **Never modify source files** — always create a new versioned file or a new sheet.
- **Named ranges or clearly labelled cells** for all key inputs (FX rate, source discount, class factors).
- **Color coding** (Jerome's convention):
  - Blue cell = manual input / assumption
  - Black formula = derived value (no manual editing)
  - Red / orange highlight = flagged issue or anomaly
- **One formula style** per column — don't mix relative and absolute references inconsistently.
- **All monetary values in EUR** unless explicitly working with JPY base prices.
- **Clearly label units**: €, JPY, %, units, litres, etc. in column headers.

---

## Pricing Formula (ISZE Standard)

This is the core formula. Get it exactly right — errors here propagate across the entire price list.

```
FOB_EUR = BP_JPY / FX_rate × source_discount
SP_EUR  = FOB_EUR / class_factor
```

### Input values (confirmed FY2026)

| Parameter | Value | Source |
|-----------|-------|--------|
| FX rate (FY2026) | 163.7 JPY/EUR | Oct 2025, documented in `pricing simulation 2026 5%.xlsx` Legend |
| FX rate (FY2025) | 146.6 JPY/EUR | Oct 2023 |
| Source J discount | 0.62 | Japan/IML sourced parts |
| Source T discount | 0.611 | Thailand/IMIT sourced parts |

### PR00 Class Factors (FY2026)

| Class | Factor (FOB/SP) | Gross Margin |
|-------|-----------------|--------------|
| C | 0.47 | 53.0% |
| D | 0.48 | 52.0% |
| F | 0.525 | 47.5% |
| J | 0.555 | 44.5% |
| M | 0.50 | 50.0% |
| P | 0.44 | 56.0% |
| V | 0.55 | 45.0% |
| T | 0.80 | 20.0% |

> Class C (consumables/brakes) = highest margin. Class T = lowest.
> Class 0 = UNDEFINED — 10 PNs in FY2026 file, all Source J. Flag these explicitly in any model.

### CIS Pricing (uniform, class-independent)
```
SP_CIS = FOB_EUR / 0.40   → ~60% gross margin
```

### Israel ZPR1 (class-dependent, lower than PR00)
Israel prices use separate per-class factors. See `pricing_logic_2026.md` §3 for exact values.
Israel turnover runs ~10% below PR00 equivalent.

---

## Pricing Simulation Models

Jerome's main pricing files:

| File | What it contains |
|------|-----------------|
| `Divers/pricing simulation 2026 5%.xlsx` | Master: 15,355 PR00 lines, 4,567 Israel, 690 CIS |
| `Divers/ISZE_PriceCalc_2026_v3.xlsx` | Pricing calculator (newer) |
| `Divers/ISZE_Pricing_PnL_Model.xlsx` | P&L impact model |

When building a new pricing tool, use the exact same FX rate and class factors as the
master simulation. If the rates differ from above, flag it immediately and confirm with Jerome.

**Class 0 handling**: Always check for Class 0 PNs in any batch. Flag them in a separate
tab or highlighted range. Do not apply a default class factor — leave them as errors to be resolved.

---

## PMS Coverage Model

Purpose: estimate expected PMS parts demand vs. actual ISZE/ITUK sales.

Key inputs:
- UIO (Units In Operation) by model line — use DVLA-confirmed figures for ITUK (22,389 total)
- Service interval: N-Series = typically 30,000–50,000 km or annual; D-Max = 5,000–10,000 km
- Parts per service: 1 oil filter, 1 air filter, 1 fuel filter, etc. per service event
- Capture rate = actual units sold / expected units

**ITUK confirmed data (15 Mar 2026):**
- Total UIO = 22,389 | N35: 10,900 | N75: 9,359 | N50/55: 651 | N62/65: 257 | F-series: 805
- PMS gap = ~€3.5M+ (recalculated with DVLA 22,389 — was ~€2.5M using old Hasegawa 17,135 figure)

The old 17,135 figure (Hasegawa) is WRONG. Do not use it for ITUK calculations.

Key file: `Divers/ISZE_PMS_Coverage_Calculator.xlsx`

When building or updating PMS models:
1. Source UIO from `UIO/` directory (most recent version)
2. Show expected demand calculation explicitly (UIO × service frequency × parts per service)
3. Show actual sales from ISZE billing data
4. Calculate capture rate and gap in EUR
5. Flag assumptions about service frequency and parts-per-service explicitly

---

## UIO (Units In Operation) Tool

- Current version: v19 (latest)
- Location: `UIO/` directory
- Drives: PMS volume estimates, Golden Window revenue projections
- Do NOT use the old Hasegawa 17,135 figure for ITUK — use DVLA 22,389

---

## AIM (Aftermarket Intelligence) Model

Purpose: classify ISZE parts by aftermarket substitution risk to inform pricing strategy.

Current state:
- CY2025 sell-out run completed May 2026 (64 dealers, 5,587 PNs, 223,897 units).
  Classification % from this run is not yet documented — confirm the current rate against
  `AIM_CY2025_Analysis.xlsx` before citing a number; do not carry forward older classification
  percentages without checking the source file.
- Key file: `AIM_CY2025_Analysis.xlsx`

Classification categories to understand:
- **Captive / proprietary** — low substitution risk. Full strategic pricing applies.
- **High aftermarket exposure** — price sensitivity to aftermarket equivalents. Examples: oil filters, EGR valves, belts.
- **ABC analysis**: A = high volume/value, B = medium, C = low. Combined ABC:Class drives pricing strategy.

**For pricing strategy work**: Use AIM to identify which PNs are high-substitution-risk.
These are the ones where the next pricing cycle should differentiate.

When building AIM-linked models:
- Always show the classification basis (ABC category, substitution flag, source)
- Highlight PNs where AIM score suggests pricing is above aftermarket equivalent
- Separate captive PNs from exposed PNs in any sensitivity analysis

---

## Kosha / Long-Range Forecast Models

Source file: `Divers/ISZE PL Plan FY2026 2027 2028 20260130.xlsx` (IX study sheet)

| Year | VP Sales Target (€M) | Parts Total (€M) |
|------|---------------------|-----------------|
| FY2024 actual | 29.6 | 48.0 |
| FY2025 actual | 32.5 | 51.2 |
| FY2026 | 32.3 | 50.0 |
| FY2027 | 35.3 | 52.4 |
| FY2028 | 37.5 | 56.3 |
| FY2031 | 52.1 | 84.4 |

**GP compression warning**: IML's own Kosha plan projects GP% declining from 37.4%
(FY2025 actual) to 26.1% by FY2028. Any model that shows ISZE hitting Kosha volume
while maintaining margin should be flagged as structurally inconsistent.

When building forecast models:
- Always show the Kosha targets as a reference line
- Show the gap between current trajectory and Kosha (do not hide it)
- Model realistic base case separately from Kosha aspiration
- Flag if assumptions required to hit Kosha are unrealistic

---

## Table and Chart Conventions in Excel

- **Tables**: Use Excel Table objects (Ctrl+T) for data ranges. This makes formulas consistent and filtering automatic.
- **Charts**: Use solid fills, Isuzu Red (#CC0E1E) as primary series colour, grey (#888888) for secondary.
- **Number formats**:
  - Currency: `€#,##0.00` or `€#,##0` depending on precision needed
  - Percentages: `0.0%` (one decimal)
  - JPY base prices: `¥#,##0` (whole numbers)
  - Large numbers (millions): `€#,##0.0,,` + "M" label in header
- **Conditional formatting**: Use for capture rates (green > 50%, amber 20–50%, red < 20%)
  and for variance vs budget (red = negative vs. target for sales, green = positive)

---

## Key Excel Files Cheat Sheet

| Purpose | File |
|---------|------|
| 2026 pricing master | `Divers/pricing simulation 2026 5%.xlsx` |
| Pricing calculator | `Divers/ISZE_PriceCalc_2026_v3.xlsx` |
| PMS coverage | `Divers/ISZE_PMS_Coverage_Calculator.xlsx` |
| Action plan FY2026 | `Divers/Action plan FY2026 VPACC_*.xlsx` |
| FY2027 action plan | `ISZE_FY2027_ActionPlan_VP.xlsx` |
| Kosha plan | `Divers/ISZE PL Plan FY2026 2027 2028 20260130.xlsx` |
| AIM analysis | `AIM_CY2025_Analysis.xlsx` |
| Data integrity | `ISZE_DataIntegrity_Dashboard.xlsx` (Tab 5 = Class 0 PNs) |
| ITUK dealer network | `ITUK_Dealer_Network_Analysis.xlsx` |
| DB KPI scorecard | `Divers/ISZE_DB_KPI_Scorecard.xlsx` |
| EV readiness | `Divers/ISZE_EV_Readiness_Checklist.xlsx` |
| GPS calculator | `Divers/ISZE_GPS_Calculator.xlsx` |
| CY2025 sales analysis | `ISZE_CY2025_Analysis_v1.xlsx` |
| Golden Window model | `ISZE_GoldenWindow_Revenue_Model.xlsx` |
