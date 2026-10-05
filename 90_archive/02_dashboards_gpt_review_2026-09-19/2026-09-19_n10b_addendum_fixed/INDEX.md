# N10B addendum fixes — review copies only

**Folder:** `C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_n10b_addendum_fixed\`  
**Date:** 2026-09-19  
**Rule:** Live originals under `02_dashboards\sales\`, `pricing\`, `md_pack\`, `fleet\`, `ops\` were **not** modified. These are new copies for Jerome’s review.

**Source pack (lineage):** `C:\Users\jerom\Desktop\claude\ISZE\08_gpt\html_dashboard_review_next10b_2026-09-19\`  
(The older `html_dashboard_review_next10_2026-09-19` MAP numbers different files — AIM/pricing. **Trust the addendum evidence**, not that MAP.)

## File mapping (addendum # → this folder)

| Addendum # | Finding focus | Staged copy | Live original (lineage only) |
|---|---|---|---|
| 03 | Air-filter / expected-vs-billed scale (Cyprus >100%) | `03_ISZE_PMS_Family_Compare.html` | `02_dashboards\sales\ISZE_PMS_Family_Compare.html` |
| 04 | ITUK distributor review (benchmarks + service table) | `04_ISZE_Sales_Performance_Review_ITUK.html` | `02_dashboards\sales\leakage_packs\ISZE_Sales_Performance_Review_ITUK.html` |
| 05 | Belgium distributor review | `05_ISZE_Sales_Performance_Review_BELGIUM.html` | `…\leakage_packs\ISZE_Sales_Performance_Review_BELGIUM.html` |
| 06 | Sweden distributor review | `06_ISZE_Sales_Performance_Review_SWEDEN.html` | `…\leakage_packs\ISZE_Sales_Performance_Review_SWEDEN.html` |
| 07 | MD pack dark mode + value-part profit | `07_ISZE_MD_Pack_Capture_FY27_FY28.html` | `02_dashboards\md_pack\ISZE_MD_Pack_Capture_FY27_FY28.html` |
| 08 | Explanation tooltips / keyboard | `08_ISZE_UIO_Car_Park_V19_V20.html` | `02_dashboards\fleet\ISZE_UIO_Car_Park_V19_V20.html` |
| 09 | Multi-tab print scope (Network / ITUK / FY2027) | `09_ISZE_GPS_Dashboard.html` | `02_dashboards\fleet\ISZE_GPS_Dashboard.html` |
| 10 | Mobile chart bars (equal-width note) | `10_ISZE_OS_Console.html` | `02_dashboards\ops\ISZE_OS_Console.html` |

Addendum files **01–02** (KPI Dashboard, Growth Plan) are out of scope for N10B-048–061.

## How to open

Double-click the matching `0N_OPEN_*.cmd` (CRLF, `%~dp0`). Do not use chat `file://` links.

| Open | Opens |
|---|---|
| `03_OPEN_PMS_Family_Compare.cmd` | Family compare |
| `04_OPEN_Sales_Review_ITUK.cmd` | ITUK review |
| `05_OPEN_Sales_Review_BELGIUM.cmd` | Belgium review |
| `06_OPEN_Sales_Review_SWEDEN.cmd` | Sweden review |
| `07_OPEN_MD_Pack_Capture_FY27_FY28.cmd` | MD pack |
| `08_OPEN_UIO_Car_Park_V19_V20.cmd` | UIO V19/V20 |
| `09_OPEN_ISZE_GPS_Dashboard.cmd` | GPS dashboard |
| `10_OPEN_OS_Console.cmd` | OS console |

## Start here

1. `PING_JEROME.md` — what to open and what to check  
2. `FIX_LOG.md` — each N10B finding → fixed / deferred  
3. `_qa\*_hero.png` — headless heroes (agent image-read; not auto-started for you)

## Integrity

- Copies started as byte copies of the next10b pack, then patched in this folder only.  
- ITUK live vs this copy: different (expected). Belgium live still has the old “schedules agree” label.
