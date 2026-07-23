# Distributor Warranty Expense (fiscal)

**What it is.** Parts warranty claims paid (or assessed) per distributor, in EUR, by **fiscal year** (Apr–Mar — same basis as GPS billing).

**File to use:** `01_data/00_derived/distributor_warranty_expense_fiscal.csv`  
(Technical alias: `warranty_by_db_FY_canonical.csv` — identical content.)

**Rebuild:** `python 01_data/91_build/build_warranty_canonical.py`

---

## How v3d uses it

| Step | Logic |
|------|--------|
| **Actuals (FY24–26)** | Net GPS billing = **gross parts billing (v3c) − warranty expense** for that DB and FY |
| **GPS % (actuals)** | Net billing ÷ **full** market cap (UIO × rate) |
| **Forecast (FY27–30)** | GPS % = required net ÷ **effective** market cap = full cap **− average warranty expense** for that DB |
| **Revenue toward BP** | Net capture **+** average warranty expense (warranty parts are still billed revenue) |

**Warranty average** = mean of FY2024, FY2025, FY2026 expense for that distributor (FY24+25 only for ITUK/UTI where FY26 CV is thin in source).

---

## Fiscal year basis (matches billing)

| FY | Period |
|----|--------|
| FY2024 | Apr 2023 – Mar 2024 |
| FY2025 | Apr 2024 – Mar 2025 |
| FY2026 | Apr 2025 – Mar 2026 |

Claim month (`REPA6` / `AssessMonth`): month ≥ April → fiscal year = calendar year + 1.

---

## Data sources

| Source | Segment | Role |
|--------|---------|------|
| `CV Warranty.xlsx`, `Warranty_CV_2025.xlsx`, `CV warranty01_03_2026.xlsx` | CV | **Authoritative** for ITUK, UTI (monthly REPA6) |
| `warranty_raw_grain.csv` | LCV / mixed | Line-level claims → fiscal FY |
| `gps_warranty_cy2025.json` | CV+LCV | Jan–Sep 2025 lump split 3/9 → FY25, 6/9 → FY26 |
| UMI warranty export | LCV (UMI) | Full history in grain |

JPY claims converted at **163.7 JPY/EUR**.

---

## Distributor name map (v3c / v3d)

| Canonical name | Meaning |
|----------------|---------|
| **RSA** | Norway distributor (not South Africa) |
| **Greece** | Petros Petropoulos |

Toggle workbook uses separate row labels (Norway / RSA for Greece); amounts map via this file.

---

## Do not use

`gps_master.csv` `warr_*` columns — undercounts network warranty (~85% low). Always use this file for Kosha net GPS.
