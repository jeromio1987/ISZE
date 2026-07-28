# ISZE Company Context

*Jerome Van der Pluym — VP Sales, ISZE (Branch IE40)*
*Use this reference for any task needing company knowledge, people context, terminology,
project status, or strategic framing.*

---

## Organisation

| Entity | What it is |
|--------|-----------|
| **ISZE** | Isuzu Motors Europe — European parts hub. Jerome's company. |
| **IML** | Isuzu Motors Limited — Japan parent. Sets BP_JPY, pricing strategy, Kosha targets. |
| **ISZJ** | Isuzu Japan (parts context = IML) |
| **ITUK** | Isuzu Truck UK Ltd — Jerome's largest distributor. |
| **IMG** | Isuzu Motors Germany — service/warranty |
| **IMIE** | Isuzu Motors International Europe — vehicle sales |
| **IMIT** | Isuzu Motors International Thailand — Source T parts |
| **IAS** | Isuzu Accessories Supplier (Thailand) |
| **Branch IE40** | ISZE's internal SAP branch code |

---

## Key People

| Person | Role | Notes |
|--------|------|-------|
| **Jerome / JVDP** | VP Sales, ISZE. Me. | Team: Ling, Koen, Hadi |
| **KM** | Colleague, ISZE Sales | |
| **HT** | Colleague, ISZE Sales / Accessories | |
| **DW** | Colleague, ISZE Accessories lead | |
| **SZ / Saida** | Colleague, ISZE Accessories backup | |
| **BVDB** | Colleague, ISZE Power BI reporting | Data and reporting outputs |
| **James Marsh** | Materials Expeditor, ITUK | Key ITUK contact. |
| **Ryusuke Tanaka** | Product Marketing, International Parts Sales Dept, IML | |
| **Tomoaki Hiratsuka** | International Parts Sales Dept, IML | |

---

## Key Terminology

| Term | Meaning |
|------|---------|
| **VP** | Vehicle Parts |
| **ACC** | Accessories |
| **PMS** | Periodic Maintenance Service parts (filters, clutch, brake) |
| **UIO** | Units In Operation |
| **SPA** | Special Price Agreement |
| **DLOD** | Don't Lose Deal (ITUK programme) |
| **VPACC** | Vehicle Parts & Accessories (action plan label) |
| **CR** | Cost Reduction |
| **DPD** | Diesel Particulate Diffuser |
| **EQ-HIT** | Parts catalog/lookup system — does NOT have PN→service mapping |
| **Eucon** | Price benchmarking study provider |
| **R&M** | Repair & Maintenance contracts |
| **FY** | Fiscal Year (Apr–Mar for Isuzu) |
| **IGS** | Isuzu Global Summit |
| **KPI** | Key Performance Indicator matrix (collected from DBs) |
| **PR00** | Standard European price list (all EU distributors/dealers) |
| **ZPR1** | Israel-specific price list condition type (SAP) |
| **CIS** | Price list for CIS region (GA=Armenia, CBC=Kazakhstan) |
| **UMI / 1797** | Israel distributor 1 (customer code 1797) — Universal Motors Israel |
| **UTI / 1799** | Israel distributor 2 (customer code 1799) — Universal Trucks Israel |
| **GA** | Green Armenia (CIS customer) |
| **CBC** | CBC Kazakhstan (CIS customer) |
| **DB / DLR** | Distributor / Dealer |
| **AIM** | Aftermarket Intelligence — ISZE's competitive parts classification system |
| **BP** | Base Price (in JPY, from IML) |
| **FOB** | FOB price in EUR = BP_JPY / FX × source_discount |
| **Source J** | Parts sourced from Japan/IML — discount factor 0.62 |
| **Source T** | Parts sourced from Thailand/IMIT — discount factor 0.611 |
| **Class C/D/F/J/M/P/V/T** | Parts classification driving margin factor in pricing |
| **Kosha** | IML's formal long-range corporate planning exercise |
| **SPLR** | Supplier |

---

## Active Projects (as of March 2026)

| Project | Status | Key context |
|---------|--------|-------------|
| **FY2026 VP Action Plan** | FY end review | Did we hit targets? File: `Divers/Action plan FY2026 VPACC_*.xlsx` |
| **PMS Coverage (ITUK pilot)** | In pilot | EQ-HIT gap — no PN→service mapping. Key file: `Divers/ISZE_PMS_Coverage_Calculator.xlsx` |
| **Competitiveness Dashboard** | Live Mar 2026 | N/F-Series estimated only. File: `Divers/ISZE_Competitiveness_Dashboard.html` |
| **UIO Tool (v19)** | Stable — canonical | 90% owner-operator override fixed, cohort model live. File: `Data/ISUZU_UIO_Overview_2026_v19.xlsx`. Dashboard HTML still v11 — naming drift. |
| **EV Readiness** | Planning | D-Max EV launch timeline unknown. File: `Divers/ISZE_EV_Readiness_Checklist.xlsx` |
| **AIM (Aftermarket Intelligence)** | ✅ Live — CY2025 sell-out classified (May 2026) | CY2025 ITUK sell-out run completed May 2026 (64 dealers, 5,587 PNs, 223,897 units). Classification rate from this run not yet documented — treat any earlier classification % as stale until confirmed. Key files: `Master Dashboard/AIM_CY2025_Analysis.xlsx`, `Isuzu/Sales to Dealers_ITUK_CY2025.xlsx` |

---

## Confirmed Key Data (IE40, March 2026)

- **D-Max EGR valve ABC:A** = €235.55 (PN 8983320160, TH) — NOT €124.98 (JP variant)
- **D-Max oil filter ABC:A** = €6.80 (PN 8982705240, TH)
- **N-Series 4HK1 EGR ABC:C** = €151.32 (JP)
- **N-Series clutch disc ABC:C** = €84.47 (JP, PN 8972599400)
- **FX history**: 146.6 JPY/EUR (Oct 2023, FY2025) → 153.3 (Apr–Sep 2024) → 163.7 (Oct 2025, FY2026)
- **Class 0 PNs**: 10 (all Source J) — in `ISZE_DataIntegrity_Dashboard.xlsx` Tab 5. Undefined class factor — flag explicitly in any pricing model.
- **ITUK car park (DVLA, 15 Mar 2026)**: 22,389 total | N35: 10,900 | N75: 9,359 | N+F total: 21,972
- **ITUK PMS gap**: ~€3.5M+ (using DVLA 22,389). Oil filter sell-out capture: 9.8% CY2024 (ITUK→dealer), 17.3% CY2025 (5,815 units sold vs 33,584 expected) — improving but still severely under-penetrated
- **ITUK FY26 parts target**: £13.13M | True Sales avg = £580.65/vehicle/yr (ITUK's own calc)
- **Kosha VP Targets**: FY2024 actual €29.6M → FY2031 €52.1M (+76%). GP% declining: FY2025 37.4% → FY2028 26.1% per IML's own plan.

---

## Strategic Framing (Honest Internal — not for external docs)

**These facts are confirmed by Jerome and should drive analysis, but must NOT appear in
external-facing documents.**

### 1. The Kosha Targets
- EUR 52.1M VP Sales by FY2031 is not achievable from current position.
- Everyone in the chain likely sees this. Japanese management culture prevents it being named.
- **Real objective**: Build a credible execution record so ISZE is not blamed when Kosha proves unreachable.
- Reviewable deliverables: PMS joint programme, AIM applied to pricing, fleet-age revenue model.

### 2. The PMS Gap
- The ITUK PMS gap is the most important commercial signal ISZE has produced in FY2026.
- Oil filter capture rate data needs refreshing — use the confirmed 9.8% (CY2024) / 17.3% (CY2025)
  figures above; do not cite older or conflicting figures without checking the source file first.
- Do NOT assert the gap proves ITUK execution failure — root cause is unknown. Could be aftermarket
  substitution, availability, R&M contracts, operator behaviour, or pricing.
- Use it to propose a joint root-cause programme, not as a weapon in any dispute.

### 3. D-Max vs N-Series Golden Window
- **D-Max**: Subject to UK ZEV mandate. ICE fleet declining from 2026. Window is real, bounded, urgent (2026–2030).
- **N-Series**: NOT subject to same ZEV rules. Longer service life. Window extends to 2033–2035+.
- Do not conflate them. Separate urgency narratives required.

---

## Project Connections (critical chain)

```
UIO → PMS volume → PMS campaign → Action Plan
IE40 price list → Competitiveness Dashboard
Pricing simulation → PR00 → Competitiveness Dashboard
AIM Strategic Score → Competitiveness Dashboard
AIM Pricing Risk Map → Class C sensitivity
UIO (Parc) → AIM Opportunity Engine → distributor gap analysis
```

---

## Key File Locations

All files live under `claude/Isuzu/` on Jerome's desktop.

| File | Purpose |
|------|---------|
| `Divers/pricing simulation 2026 5%.xlsx` | Master pricing simulation — 15,355 PR00 lines |
| `Divers/ISZE_PriceCalc_2026_v3.xlsx` | Pricing calculator |
| `Divers/pricing_logic_2026.md` | Full pricing formula documentation |
| `Divers/ISZE_PMS_Coverage_Calculator.xlsx` | PMS gap analysis |
| `Divers/ISZE_PL Plan FY2026 2027 2028 20260130.xlsx` | Kosha study (IX sheet) |
| `AIM_CY2025_Analysis.xlsx` | AIM competitive classification |
| `ISZE_DataIntegrity_Dashboard.xlsx` | Tab 5: Class 0 PNs |
| `isuzu-ppt-template/` | Branded PPTX template skill |
| `ISZE_Strategic_Position_2026.md` | Full strategic position paper |
| `MASTER_DASHBOARD.html` | Overview of all projects |
