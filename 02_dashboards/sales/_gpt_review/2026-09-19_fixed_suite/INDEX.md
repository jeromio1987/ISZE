# Fixed aftermarket suite — 2026-09-19

Separate review map for the six dashboards fixed against `ISZE_HTML_DASHBOARD_FIX_BRIEF.md`.
These are copies of the rebuilt files under `02_dashboards/sales/` — open from **this** folder so the originals stay untouched while you review.

Folder:

`C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite`

Double-click the matching `OPEN_*.cmd` (CRLF, uses `%~dp0`).

| # | Page | What it is for | HTML | OPEN launcher |
|---|------|----------------|------|---------------|
| 1 | Executive aftermarket opportunity | Modelled target-spend gap by market and service family — euro-first, fleet denominator stated. Not observed "lost sales". | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\ISZE_Lost_Sales_Model.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\OPEN_ISZE_Lost_Sales_Model.cmd` |
| 2 | Family performance diagnostic | Parts billed and service capture by AIM family over time (calendar / ISZE year). | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\ISZE_PMS_Family_Evolution_v2.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\OPEN_ISZE_PMS_Family_Evolution_v2.cmd` |
| 3 | Service-demand / tonnage diagnostic | Expected service demand vs parts billed by tonnage band. | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\ISZE_PMS_Tonnage_Evolution.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\OPEN_ISZE_PMS_Tonnage_Evolution.cmd` |
| 4 | Replenishment exceptions | PN x DB bill vs dealer-sales imbalance for the five distributors with dealer files (ITUK · UTI · IRELAND · IUK · GREECE). | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\ISZE_DB_DLR_Replenishment_CY2025.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\OPEN_DB_DLR_Replenishment.cmd` |
| 5 | Narrative explainer | Written walk-through of non-additive gap types (do not sum across pages). | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\ISZE_DB_Leakage_Review_CY2025.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\OPEN_ISZE_DB_Leakage_Review.cmd` |
| 6 | Suite index (former command center) | Retired mega-dashboard — links into the five focused pages above. | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\ISZE_Aftermarket_BI_Command_Center.html` | `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_fixed_suite\OPEN_Aftermarket_BI_Command_Center.cmd` |

## QA (2026-09-19 delivery)

- Brief text gate `_qa_brief_fix_check.py`: **PASS** (all six).
- Headless Chrome screenshots under `_qa/`; each page has a sibling `*.SHIP_RECEIPT.json` with matching taken/read counts.
- Extra fix found in visual QA: Family Evolution pair chart had category labels on the value axis (0-4 on the left). Fixed in `build_family_evolution_v2.py`, rebuilt, and re-copied here. Period dropdown widened so "Calendar year (January to December)" is not clipped.
- Controlled CY2025 basis on opportunity pages: 163,198 trucks · EUR 55.253M modelled ceiling · EUR 30.757M parts billed · 55.7% · EUR 24.497M gap by subtraction.
