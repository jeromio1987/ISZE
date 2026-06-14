# ISZE GPT Enterprise — Context Briefing
**Owner:** Jérôme Van der Pluym — VP Vehicle Parts Sales, Isuzu Motors Europe (ISZE)
**Date:** April 2026

---

## Who I Am and What I Do

I manage Vehicle Parts Sales for Isuzu Motors Europe (ISZE) — a parts distribution hub supplying distributors across Europe and Israel. My team: Ling, Koen, Hadi. I report into IML (Isuzu Japan parent) under a Kosha plan framework.

---

## Key Abbreviations — Decode These Before Answering

| Term | Meaning |
|------|---------|
| ISZE | Isuzu Motors Europe (my company) |
| IML / ISZJ | Isuzu Motors Limited — Japan parent |
| ITUK | Isuzu Truck UK Ltd — largest distributor |
| IMG | Isuzu Motors Germany |
| IMIE | Isuzu Motors Intl Europe (vehicle sales, separate from parts) |
| IAS | Isuzu Accessories Supplier (Thailand) |
| DB / DLR | Distributor / Dealer |
| VP / ACC | Vehicle Parts / Accessories |
| PMS | Periodic Maintenance Service (filters, clutch, brake) |
| UIO | Units In Operation — fleet size estimate |
| SPA | Special Price Agreement |
| DLOD | Don't Lose Deal (ITUK program) |
| PR00 | Standard European price list (SAP condition type) |
| ZPR1 | Israel-specific price list |
| Source J | Parts from Japan — discount factor 0.62 |
| Source T | Parts from Thailand — discount factor 0.611 |
| BP | Base Price in JPY (from IML) |
| FOB | FOB price in EUR = BP_JPY ÷ FX × source_discount |
| Class C/D/F/J/M/P/V/T | Parts classification driving margin factor |
| Eucon | External price benchmarking provider |
| AIM | Aftermarket Intelligence Map (internal tool) |
| GPS | Genuine Parts Spend (spend-per-vehicle metric) |
| FY | Fiscal Year — April to March |
| Kosha | IML's long-range sales plan |

---

## Pricing Formula

**FOB price (EUR)** = BP_JPY ÷ FX_rate × source_discount_factor

- FY2026 FX rate: **163.7 JPY/EUR**
- Source J discount factor: **0.62** (Japan/IML-sourced)
- Source T discount factor: **0.611** (Thailand/IMIT-sourced)
- Selling Price (SP) = FOB × class_margin_factor

**FX history:** 146.6 (Oct 2023) → 153.3 (Apr 2024) → 163.7 (Oct 2025). JPY weakening = lower EUR cost. The +5.3% EUR price increase in FY2026 was driven by IML raising BP_JPY (2030 Vision programme), not FX.

---

## Data Files Uploaded — What Each Contains

### Ready for Computation

| # | File | What It Contains | Key Use |
|---|------|-----------------|---------|
| 1 | `sales_detailed_for_claude_full_fixed.csv` | Full CY sales detail — PN, distributor, month, value | KPI reporting, actuals baseline |
| 2 | `uio_distributor_year.csv` | Units In Operation by distributor and year | Capture rate and PMS gap calcs |
| 3 | `distributor_master_mapping.csv` | DB codes → distributor names and regions | Reference mapping for all analysis |
| 4 | `IE40 Price list PR00_3_level_classified.xlsx` | Full ISZE price list (Mar 2026) with ABC classification | Pricing analysis, SPA feasibility |
| 5 | `ISUZU_UIO_Overview_2026_v13.xlsx` | Detailed UIO model — ITUK DVLA-sourced (22,389 vehicles) | PMS gap sizing, GPS analysis |
| 6 | `ITUK_PMS_Analysis_Apr2026_v2.xlsx` | ITUK PMS gap analysis — capture rates, a material amount opportunity | PMS gap reporting |
| 7 | `ISZE Vehicle Parts FY2026 Year-End Review.xlsx` | Full FY2026 actuals | Variance vs budget |
| 8 | `Sales CY25.XLSX` | Calendar year 2025 sales actuals | Trend analysis, YoY comparison |
| 9 | `Niguri FY25.26 Extract 20260413_ITUK.xlsx` | Latest ITUK extract (13 Apr 2026) | Most current ITUK actuals |
| 10 | `ISZE_Chain_Pricing_Intelligence.xlsx` | Internal pricing intelligence vs. IAM channels | Benchmarking context |
| 11 | `preliminary_pricefile2026.xlsx` | 2026 preliminary price file | Cross-check vs final IE40 list |
| 12 | `LCV_WA Data 201501-202502.xlsx` | LCV market registration data 2015–2025 | Market sizing, UIO validation |
| 13 | `sales_classification_PBI.xlsx` | Sales classification (ABC/product line) | Power BI alignment, overstock |
| 14 | `Nox Sensor SPA Requests_.xlsx` | Sample SPA request data (Nox Sensor product) | Template/format only — not full SPA list |
| 15 | `ISZE_TenderIntelligence_StrategyBrief_v6.pdf` | Tender strategy brief — relevant CPV categories | Tender scanning context |

### Already in Your Knowledge Base

| File | Content |
|------|---------|
| `Active_Projects_Apr2026.md` | Live project status + confirmed data points |
| `Pricing_Logic.md` | Full pricing formula, class factors, FX history, ITUK pricing position |
| `ISZE_Company_Context.md` | Org structure, key people, strategic context |
| `Glossary_and_Terms.md` | All abbreviations |
| `Jerome_Working_Style.md` | Response style calibration |
| `Email_Templates.md` | ISZE email formats |
| `gps_pms_framework_spec.md` | GPS/PMS calculation methodology |

---

## Confirmed Data Points (use these — do not estimate)

- **ITUK UIO (DVLA, Mar 2026):** 22,389 total | N35: 10,900 | N75: 9,359 | N50/55: 651 | N62/65: 257 | F-series: 805
- **ITUK PMS gap:** a material amount | Oil filter capture rate: very low (100 units actual vs  the expected volume)
- **FY26 ITUK target:** £13.13M | True Sales average: £580.65/vehicle/year
- **ITUK basket impact 2025→2026:** +€298,911 / +5.3% (confirmed line-by-line)
- **Class 0 PNs:** 10 (all Source J) — pricing anomaly flagged in ISZE_DataIntegrity_Dashboard.xlsx
- **Kosha targets:** FY2024 €29.6M → FY2025 €32.5M → FY2026 €32.3M → FY2031 €52.1M (+76%)
- **AIM classification:** 93.5% complete (as of 14 Mar 2026)
- **D-Max EGR filter (TH, PN 8983320160):** €235.55 | D-Max oil filter (TH, PN 8982705240): €6.80

---

## Active Projects — Current Status

| Project | Status | Key Issue |
|---------|--------|-----------|
| ITUK pricing 2026 | 🔥 Active | James Marsh (ITUK) challenging +5.3% methodology — precedent risk |
| PMS Coverage (ITUK pilot) | In pilot | EQ-HIT gap: no PN→service interval mapping |
| Lubricants project | On hold | Awaiting IML go-ahead post Feb 2026 meeting |
| UIO Tool (v9→v10) | FY2027 refresh due | Awaiting fresh data from distributors |
| AIM (Aftermarket Intelligence) | Live CY2025 | VKWRT + CY2024 data still needed |
| Competitiveness Dashboard | Live Mar 2026 | N/F-Series estimates only |

---

## What I Need You to Compute

Please confirm which uploaded files you have access to, then state what you can start calculating immediately for each of the following use cases:

1. **SPA Batch Processing** — analyse SPA requests, flag anomalies, structure output
2. **Distributor KPI Reporting** — compute actuals vs target by DB (I will provide targets)
3. **Parts Price Benchmarking** — compare IE40 prices vs IAM/Eucon reference (I will provide benchmark data)
4. **PMS Coverage Gap** — compute capture rates vs expected frequency by model and DB
5. **Forecast vs Actuals** — variance analysis by distributor and product line (I will provide FY2027 budget)
