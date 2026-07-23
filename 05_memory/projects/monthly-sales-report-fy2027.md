---
topic: monthly-sales-report-fy2027
read_when: [monthly report, sales amount, order amount, Q1 FY27, Q2 FY27, VP sales, budget vs actual, BP reached]
canonical: 01_data/04_sales/(VP) Monthly report *.pdf, 01_data/12_raw/sales/Q*FY*.XLSX
last_validated: 2026-07-05
---

# Project: Monthly Sales & Order report (Vehicle Parts) — FY2027 tracker

_Last validated: 2026-07-05_

## Status: Active — updated as new monthly report PDFs arrive

**Source files (do not load raw XLSX into chat — reference this file or a derived CSV instead):**
- `01_data/04_sales/(VP) Monthly report 2026-06.pdf` — 14-page formatted report, per-customer Order/Sales/Budget/BP/target%/YoY, June 2026 = FY2027 Q1 final month.
- `01_data/12_raw/sales/Q1FY2027.XLSX` — raw SAP billing extract (SOrg IE40), Apr–Jun 2026, 31,929 clean transaction lines after stripping 2 SAP-export footer/total rows. Tagged version: `01_data/00_derived/q1fy2027_billing_tagged.csv` (flag columns for transport/Shell-lube/rebate/late-payment/service/demurrage + SaTy treatment + sign-corrected net value — nothing dropped, so warranty and Shell can be filtered later without rebuilding. Warranty is NOT in this file; it's a separate per-distributor € figure from `06_Warranty/`, joined at whatever aggregation stage — "excluding warranty" means subtracting that known amount, not filtering rows here).

## FY2027 Q1 (Apr–Jun 2026) — company total, from the monthly report PDF

| Month | Order amount | Sales amount | Budget/BP | BP reached | vs LY |
|---|---|---|---|---|---|
| Apr 2026 | €2,344K | €3,086K | €2,855K | 8% | +37% |
| May 2026 | €2,262K | €2,305K | €2,661K | -13% | -5% |
| Jun 2026 | €3,146K | €3,220K | €3,081K | 5% | +8% |
| **Q1 Total** | **€7,752K** | **€8,611K** | **€8,596K** | **0%** | **+13%** |

**Summary commentary (from PDF):** Order intake €3.146K (+2.1% vs target) in June. June sales €3.220K, +4.35% over BP, +9.02% YoY. UTI reached 233.5% of BP (+€363K, first SPA order). ITUK 74.38% of BP on paper but €165K sitting in WIP for July 1 invoicing — adjusted ITUK ≈ €605K vs €599K BP (would have hit target). IUK 70.93% of BP. UMI 58.62% of BP (-€21K vs LY) — **halt of Shell deliveries strongly affecting UMI's purchase performance** (Jerome's own note when asked to "exclude Shell" — this is the real-world driver, not a data artifact).

## Per-customer Q1 FY27 Sales amount (from PDF, €)

| Customer | Apr | May | Jun | Q1 Total | vs Budget | vs LY |
|---|---|---|---|---|---|---|
| ITUK | 529K | 415K | 446K | 1,390K | -19% | -19% |
| IUK | 929K | 357K | 377K | 1,663K | +13% | +41% |
| UTI | 211K | 191K | 635K | 1,037K | +38% | +29% |
| IBX | 203K | 157K | 235K | 595K | +7% | +72% |
| RSA | 116K | 108K | 173K | 397K | -7% | +3% |
| ISZ Sweden | 133K | 114K | 194K | 441K | +24% | +48% |
| Isuzu Ireland | 82K | 92K | 111K | 284K | (see PDF) | |
| BL Ehf (Iceland) | 6K | 5K | 8K | 19K | -26% | -18% |
| ISZ Denmark | 17K | 13K | 15K | 45K | -0% | |
| GasanZammit (Malta) | 13K | 22K | 23K | 58K | +3% | +15% |
| Petros (Greece) | 31K | 59K | 71K | 160K | +15% | |
| ISUZU ROM AUTO SRL | 13K | 13K | 15K | 41K | -22% | -18% |
| ISZ Armenia | 25K | 34K | 71K | 130K | +101% | +56% |
| ISZ Kazakhstan | — | 31K | — | 31K | -38% | |

_UMI not shown as an individual customer page in this 14-page report despite ranking #6 in the customer table — likely folded into a combined view or the report simply doesn't break it out separately this month._

## Reconciliation status vs raw billing extract — **RESOLVED 2026-07-05**

The first `Q1FY2027.XLSX` delivered was a **partial SD extract** (confirmed, not a report/scope problem): for the same billing documents, it was missing the majority of line items in many cases (e.g. one doc had 6 lines/€485 vs 751 lines/€185,937 in the complete version). Jerome supplied a second, complete export (`EXPORT.XLSX` — richer schema with Plant/Profit Ctr/JPY+EUR+GBP cost detail, already sign-corrected for G2/RE) which reconciles almost exactly to the monthly report: **€8,719,233 vs €8,611,000 (+1.3%)**, and per-DB ties to the euro for IUK, ITUK, UTI, IBX, Sweden, Ireland, Petros, Armenia. **IUK was never really "off" — it was just the worst-hit by the partial extract** (only ~35% of its true Q1 value was in the first file). UMI/UTI "merge" was also a false read — the complete file shows them as separate payer codes (1797 / 1799) that both tie to the report.

**Canonical source going forward:** the complete export, filed as `12_raw/sales/Q1FY2027_full.XLSX` pending Jerome closing the old file in Excel so it can be swapped in as `Q1FY2027.XLSX` (see `_data_integrity_open_issues.md` → Q1FY27-CANONICAL-SWAP). Real entity names discovered from the "Name" field in the complete export — useful, differs from the generic Payer name: **IUK = DS/E International Motors Limited**, **ITUK = TVS Supply Chain Solutions Ltd**, **IBX = Katoen Natie**, **Petros = SARMED Facility**, **AW Hungary = CTPark Budapest West**, **UTI = Universal Trucks Israel Ltd**, **UMI = Universal Motors Israel Ltd** (confirmed distinct).

**Order type (SOR/VOR/RUSH) caveat:** the complete export has no SaTy field. Joined it back in from the old partial file via Sales Doc. — clean 1:1 mapping, but only 70.4% of Q1 value has a matched order type, and coverage is uneven by DB (IUK 35%, KOMTRANSKOMPLEKT 28%, Grand Avto 38% — low/unreliable; most others 85–99%). RUSH-share-by-DB chart built for Jerome's presentation: `01_data/00_derived/rush_order_share_by_db_q1fy2027.png`, data at `01_data/00_derived/q1fy2027_export_with_saty.csv`.

## Connections
→ `05_memory/projects/gps-reconciliation.md` — GPS calc uses per-DB billing; same UMI/UTI merge issue applies there.
→ `06_Warranty/` — warranty € figures needed to compute "ex-warranty" sales/GPS; not in this billing file.
→ isze-gps-auditor skill — exclusion rules (transport, Shell/Rimula 550047xxx/550070xxx codes, rebate, late payment interest, service, demurrage, SaTy CR/RE/G2 sign correction) applied in `q1fy2027_billing_tagged.csv`.

## Open items
- ~~Explain the €2.0–2.4M reconciliation gap~~ RESOLVED — see above (partial extract, not IUK-specific).
- "I.M. PARTS & SERVICE Limited" identity resolved via the "Name" field in the complete export: **IUK = DS/E International Motors Limited**.
- **CORRECTION (2026-07-05):** earlier note "no Shell/Rimula lube codes in Q1FY27" was **wrong** — caused by the Material/Material-Number column-swap bug (see `_data_integrity_open_issues.md` → CY-MATNR-SWAP). Re-checked with the correct field on `Q1FY2027_full.XLSX`: **2 Shell/Rimula lines, €35,576 total, both under UMI (Universal Motors Israel Ltd)**. Small in Q1 FY27 terms but confirmed present and real — don't repeat the "not present" claim elsewhere.
- Update this file each month as new `(VP) Monthly report YYYY-MM.pdf` files arrive.
