# Project: Aftermarket Intelligence (AIM)

_Last validated: 2026-05-08 (CY2025 sell-out classification confirmed complete)_

**Status:** ✅ Live — CY2025 data classified · CY2024 cross-validated (15 Mar 2026)

**Also called:** AIM, Aftermarket Intelligence Model, AIM Framework

## Source files
- `Isuzu/AIM_Dashboard_CY2025.html` — live dashboard
- `Isuzu/AIM_CY2025_Analysis.xlsx` — full scoring workbook
- `Isuzu/ISZE_CY2024_Sales_Analysis.xlsx` — AIM Validation tab (CY2024 cross-check)
- `isuzu_aftermarket_intelligence_framework.docx` — original design spec
- `isuzu_aftermarket_full_build_v1.xlsx` — implementation template

## What it does
Scores every SKU across: revenue concentration, volume stability, ABC class, competitiveness signal, cross-sell linkage.
Aggregates to distributor and category level → Strategic Score, Pricing Risk Map, Opportunity Engine.

## Classification status

### CY2024 (count-based, Mar 2026)
- **Classification rate: 93.5%** (was 75.6% at start of session — +17.9pp improvement)
- **CY2024 cross-validation: 95% revenue coverage confirmed** (15,510 PNs matched vs 16,338 unique PNs)
- Residual 5% (~€1.6M in CY2024) = unclassified, needs manual review
- 10 Class 0 PNs identified — all Source J, no margin factor assigned — see ISZE_DataIntegrity_Dashboard.xlsx Tab 5

### CY2025 sell-out (revenue-weighted, May 2026) ✅
- **Classification rate: ~87% of revenue** (from Assumptions sheet of `AIM_CY2025_Analysis.xlsx`)
- Note: 87% is revenue-weighted; 93.5% was CY2024 count-based — these metrics are not directly comparable
- Total classified revenue = ~€28.2M of €32.4M total (AIM Distributor View confirmed €32,403,410)
- Do not cite 93.5% for CY2025 — use 87% rev-weighted when discussing CY2025 classification externally

## ⚠️ Critical entity mapping (confirmed 23 Mar 2026)
Sales2024.XLSX is ITUK → dealer level data.
- **Cust 2574 = IUK** (separate entity, NOT ITUK — do NOT conflate with ITUK)
- **Cust 2575 = ITUK only**
Any analysis treating Cust 2574 as ITUK will overstate ITUK volumes. This distinction is essential for PMS capture rate and AIM gap analysis.

## Data integrity split
| Layer | Source | Integrity |
|-------|--------|-----------|
| CY2024 revenue (AIM input) | Sales2024.XLSX — actual SAP billing (154K lines) | ✅ HIGH — real invoiced prices incl. ZPR1/order-type conditions |
| CY2025 revenue (AIM scoring) | Qty × PR00 (planning estimate) | 🔴 PR00 only — missing ZPR1 (Israel) and surcharges. High-SPA customers may be over-scored. |
| Classification layer | Keyword rules on description | ✅ 93.5% covered |
| Competitiveness signal | IE40 prices only | 🔴 No IAM benchmark loaded yet — placeholder |

## Key findings (CY2024 actual)
- ITUK: €6.75M, 45.7% GP — above network avg (+2.8pp)
- Israel (UMI+UTI): €5.74M, 40.8% GP — 17.6% of network
- Top PN by revenue: DPF sensor 8978808270 (€630K, 69.3% margin)
- Oil filter 8982705240: €231K, 19.2% GP — low margin flag
- Lubricant PN 550047337: SAP margin wrong (kickback not in COGS — actual ~13%)
- KOMTRANSKOMPLEKT Jan 2024: −€85K GP from overstock campaign returns (one-time)

## CY2025 ITUK sell-out data (loaded 24 Mar 2026)
File: `Isuzu/Sales to Dealers_ITUK_CY2025.xlsx` (also in memory/projects/)
Format: pivot table (Customer × PN × month), 35,655 rows — different format from CY2024 flat file (154K rows).
- **Unique dealers: 64**
- **Unique PNs: 5,587**
- **Total units sold CY2025: 223,897**
- Monthly range: 15,769 (Dec) – 22,129 (Mar) — fairly even distribution
- Top dealers by volume: Warrington Vehicle Centre (13,801), SW Commercials (12,311), Ferndown Commercials (12,214)
- Top PN: 8941583280 (7,971 units) — classification TBC
- Oil filter 8982705240: **5,815 units CY2025** vs 3,288 CY2024 — +76.9% YoY

⚠️ Comparability note: CY2024 had customer codes (2574/2575 split). CY2025 file has dealer names only — no entity code split. Treat as full ITUK→dealer aggregate.

## YoY status
- **Oil filter (8982705240)**: CY2025 capture rate = 5,815 / 33,584 expected = **17.3%** (up from 9.8% CY2024)
- ✅ CY2025 sell-out classification: **completed** (confirmed 2026-05-08) — **~87% of revenue classified** (from Assumptions sheet, AIM_CY2025_Analysis.xlsx)
- SAP billing YoY: still blocked — CY2025 PR00 estimate not comparable to CY2024 actual billing

## Next steps
1. ✅ ~~Run CY2025 sell-out through Parts Sales Classification engine~~ — completed May 2026
2. ✅ ~~Document updated classification rate from CY2025 run~~ — **done May 2026**: ~87% revenue-weighted (Assumptions sheet). Classification status section above updated.
3. Manual classify residual 5% (~€1.6M CY2024) — still open
4. Load VKWRT (net revenue field) for SPA-adjusted scoring — still open
5. Link Competitiveness Dashboard IAM benchmarks into scoring — still open
6. Collect equivalent sell-out data from other DBs (FY2027 20% KPI condition — see ISZE_DealerData_Initiative_FY2027.docx) — still open
