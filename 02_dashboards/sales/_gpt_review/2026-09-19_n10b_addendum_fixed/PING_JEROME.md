# PING JEROME TO REVIEW

**PING JEROME TO REVIEW**

Sorry — the first review copy you opened was broken because of our patch, not because the live dashboard failed. That is fixed in this folder. Live originals are still untouched.

Review folder:

`C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_n10b_addendum_fixed\`

## Paint QA (all eight files — re-checked after repair)

| # | Open this | Paint | What broke / what you should see |
|---|---|---|---|
| **03** | `03_OPEN_PMS_Family_Compare.cmd` | **PASS** | Was dead (empty selects, Ireland seed only). Now: Question filled, many ranked bars, mix panel paints. Residual + Air Filter: Cyprus can show **above 100%** with a 100% mark. |
| **04** | `04_OPEN_Sales_Review_ITUK.cmd` | **PASS** | Was failing Service families (`periodStats` in wrong section). Now: 3 compare groups only; Service families heat paints. |
| **05** | `05_OPEN_Sales_Review_BELGIUM.cmd` | **PASS** | Same scope fix. Oil/Fuel interval: **Truck 40,000 / pickup 20,000 km** where schedules differ. |
| **06** | `06_OPEN_Sales_Review_SWEDEN.cmd` | **PASS** | Same scope fix. Oil/Fuel Interval: **20,000 km** (D-Max), not 40,000. |
| **07** | `07_OPEN_MD_Pack_Capture_FY27_FY28.cmd` | **PASS** | Substitution sensitivity callout; charts paint. |
| **08** | `08_OPEN_UIO_Car_Park_V19_V20.cmd` | **PASS** | KPI labels keyboard-focusable; slope paints. |
| **09** | `09_OPEN_ISZE_GPS_Dashboard.cmd` | **PASS** | Network GPS bars + table; print-scope control present. |
| **10** | `10_OPEN_OS_Console.cmd` | **PASS** | Console hero + loop diagram paint. |

Detail and honesty on the break: `FIX_LOG.md` (incident section at top). Mapping: `INDEX.md`.

## Please re-check first (the one that failed for you)

1. Double-click `03_OPEN_PMS_Family_Compare.cmd`  
   - Question dropdown has options (not blank).  
   - Left chart shows a full market list, not one Ireland bar.  
   - Optional: residual question + Air Filter — look for markets above 100% with a 100% mark.

2. Then `04` / `06` / `05` for the interval and compare-group checks as before.

## Decision needed from you

Say **ship** / **rebuild live** if these copies should replace the live files. Until then they stay in this review folder only.
