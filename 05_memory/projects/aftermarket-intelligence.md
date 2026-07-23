# Project: Aftermarket Intelligence (AIM)

_Last validated: 2026-07-02 (classification fallback fix + CY2026 dashboard shipped)_

**Status:** ✅ Live — CY2025 classified · CY2026 YTD dashboard live · residual gap closed to ~1.6–1.8%

## ✅ 2026-07-02 — classification gap closed + CY2026 dashboard (verified, 104-pass green)
- **Residual unclassified now 1.6% CY2024 / 1.8% CY2025 rev** (was 14.5% / 16.0% measured as
  workbook placeholder classes `Unknown`/`Unknown Review`/`Other / review`). Fix: classifier
  placeholder fallback (workbook → gap suggestion conf≥3 → PR00 catalog) in
  `03_analytics/Isuzu/prism/modules/aim_pn_classifier.py` + precedent-based
  `aim_gap_suggestions_20260702.csv` (190 PNs, €307K; script
  `build_aim_gap_suggestions_precedent.py`). Provenance in `aim_source` column.
- **Honest open residual: €1.12M over 2024+2025 (635 PNs, top 100 = 90%)** — wiper blades,
  stereo units, transfer asm, power chambers etc.; proposals for validation in
  `03_analytics/Isuzu/prism/docs/aim_classification_gap_report.md`. NOT auto-applied.
- The old "residual 5% ~€1.6M CY2024" figure is superseded — do not quote it.
- **CY2026 AIM dashboard**: `02_dashboards/sales/AIM_Dashboard_CY2026.html` +
  `aim_cy2026.data.js` (builder `scripts/build_aim_cy2026_dashboard.py`). Basis = ACTUAL
  billing (cy2026_q1.csv, GPS-auditor exclusions), unlike CY2025 workbook (Qty×PR00).
  CY2026 Jan–Mar clean €8.87M, +10.4% YoY same-window, coverage 97.6%.
  IAM benchmark wired network-level only (eucon_price_gap.csv, 44 PNs) with explicit
  footnote that DB-level IAM % cannot be computed. Local `_ui/plotly.min.js` (no CDN).
- **UTI 2026 "zero billing" flag RESOLVED**: UTI billing continues as sold-to 1799 under UMI
  payer 1797 (Jan–Mar 2026 gross €750K). Split Israel by sold-to, never by payer name.
- cy2026_q1.csv contains 2 SAP footer/total rows (Material=NaN, ~€10M) — always drop undated
  rows before summing. Fee materials appear WITHOUT spaces (`SERVICE`, `SERVICEFEEWITHINEUROPE`).

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
| Classification layer | Workbook desc-match → gap suggestions → PR00 catalog (aim_source per PN) | ✅ ~98% of revenue (2026-07-02) |
| Competitiveness signal | IE40 + Eucon/AutoDoc IAM benchmark (44 PNs) | 🟡 NETWORK-LEVEL ONLY — no DB attribution possible |
| CY2026 revenue (dashboard) | cy2026_q1.csv — actual SAP billing Jan–Mar 2026 | ✅ HIGH — invoiced values, GPS-auditor exclusions |

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

## ⚠️ BVP ≠ aftermarket (confirmed 1 Jul 2026, UTI deck review)
BVP ("Best Value Parts") is Isuzu's own budget OEM range — internal down-trade (revenue
retained, margin reduced), NOT the same as losing a sale to true third-party aftermarket
(IAM). "Genuine vs. BVP" = internal mix question. The real external-competitor threat is
the separate Eucon/AutoDoc price-benchmark data (network-level only, 44 PNs, no
distributor breakdown available — cannot quantify a single distributor's IAM exposure
from current data). Do not label BVP as "aftermarket" in any external-facing material.

## ⚠️ Genuine↔BVP crossref: check vehicle_model before calling a category "defended"
`genuine_bvp_crossref.csv` pairs are tagged by `vehicle_model`. Confirmed 1 Jul 2026: the
brake_pad (7 pairs) and brake_shoe (10 pairs) crossref entries are 100% TF*-model (D-Max/
LCV) — never F-series/N75 (CV truck range). So a CV-only distributor (e.g. UTI) showing
"100% genuine" on brake_pad/brake_shoe almost certainly means no BVP alternative applies
to their fleet at all, not a commercially defended category. Air filter, fuel filter, oil
filter and clutch kit crossref pairs do include F*/N*R model codes and are valid contested
categories for CV distributors.

## ✅ RESOLVED 2026-07-02 — UTI billing runs as sold-to 1799 under UMI payer (see top section)
## ⚠️ UTI (Universal Trucks Israel) — zero billed lines Jan–Mar 2026 (original flag, kept for history)
`sales_2026tillApril.XLSX` (line-level SAP extract, Jan 5 – Mar 31 2026) has 0 rows for
"UNIVERSAL TRUCKS ISRAEL LTD" (UTI/CV) vs 4,229 rows for "UNIVERSAL MOTORS ISRAEL LTD"
(UMI/LCV) in the same window. Not yet explained — could be a genuine order gap or a
data-routing issue. Needs a direct check before quoting any UTI 2026 figure. CY2025 total
for UTI is solid and cross-validated two ways (gps_spu_by_distributor.csv €3.331M vs raw
SAP pivot CY2025.XLSX €3.327M, within 0.1%).

## Next steps
1. ✅ ~~Run CY2025 sell-out through Parts Sales Classification engine~~ — completed May 2026
2. ✅ ~~Document updated classification rate from CY2025 run~~ — **done May 2026**: ~87% revenue-weighted (Assumptions sheet). Classification status section above updated.
3. ✅ ~~Manual classify residual~~ — closed to 1.6–1.8% on 2026-07-02 (see top section);
   remaining €1.12M proposals awaiting Jerome's validation in
   `prism/docs/aim_classification_gap_report.md`
4. Load VKWRT (net revenue field) for SPA-adjusted scoring — still open
5. ✅ ~~Link Competitiveness IAM benchmarks~~ — wired into CY2026 dashboard 2026-07-02,
   network-level only (per-DB IAM % impossible with current data; footnoted)
6. Collect equivalent sell-out data from other DBs (FY2027 20% KPI condition — see ISZE_DealerData_Initiative_FY2027.docx) — still open
