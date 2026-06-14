# PMS Catalogue Enrichment — Morning Status

## What got done overnight

**52 of 254 newest PNs scraped from Snap-on EPC** before the catalogue hard-throttled us. Workbook `ITUK_PMS_Analysis_Apr2026_v6_EPC_enriched.xlsx` has those 52 PNs enriched (226 rows in the FIG-KEY Parts sheet, since each newest P/N expands to its supersession group).

## Why the overnight run failed

1. **Snap-on rate-limiting kicked in hard after the first ~30 PNs.** Pace dropped from ~7 sec/PN (early) → ~100 sec/PN (overnight) with 90%+ "poll timeout" errors. The Loading… spinner just never resolved.
2. **Throttling longer made it worse, not better** — tried 3-sec, 5-sec, 12-sec inter-PN spacing. None helped because the limit is server-side, not client-pacing.
3. **Cancelled the loop** so we wouldn't burn the next day's quota too.

## What the 52-PN sample tells us (caveat: heavy/industrial-skewed)

| Bucket | PNs |
|---|---|
| Industrial | 13 |
| Bus | 9 |
| Marine | 7 |
| HCV (Trucks 810/C&E/F&G) | 13 |
| Component | 2 |
| **LCV (Trucks N)** | **1** |
| Stale (0 EPC results) | **28 / 52 (54%)** |

**Big methodology finding:** **54% of your "Newest P/N" entries are not findable in the live EPC.** The file's supersession-target column is heavily polluted with superseded-or-discontinued PNs that EPC no longer surfaces. Any PMS sizing built on the raw column without cross-check will misestimate the catalogue.

The LCV PNs (the ones that actually matter for ITUK/N-series distributors) come later in the FIG-KEY sheet's ordering — first 52 are mostly old industrial/marine/heavy. The 1 LCV we caught is meaningful but not representative.

## Three paths forward (your call)

1. **Wait 24h then resume** — Snap-on's throttle should reset by tomorrow. Re-run with 3-sec spacing in smaller chunks (~30 PNs at a time, break for 30 min between). Probably gets us to full 254 over 2-3 working days.
2. **Get bulk export from Snap-on** — they almost certainly have an admin/distributor export for EPC contents. One email to your Snap-on contact saves all this scraping. Worth a 5-min ask.
3. **Different angle: cross-check the "Newest P/N" column via IE40 itself** — IE40 PR00 should already have current/discontinued flags on each P/N. If we trust IE40 over the file's derived "Newest P/N", we can rebuild the supersession map without EPC at all. This is the bigger structural fix.

## Files left ready for you

- `ITUK_PMS_Analysis_Apr2026_v6_EPC_enriched.xlsx` — workbook with 52 enriched PNs (226 rows) + 222 rows marked `(pending)`
- `epc_results.json` — raw scrape data (re-runnable)
- `epc_enriched.json` — parsed enrichment data
- `parse_epc_results.py` — parser (reusable; re-run if more raw data arrives)
- `write_enriched_workbook.py` — workbook writer (re-runnable)
- `epc_scraper_install.js` — JS scraper code to paste back into Chrome console when resuming
- `remaining_pns.json` — the 202 PNs that still need EPC lookup

## Recommended order of operations when you read this

1. Open the v6 workbook. Look at the 226 enriched rows to see if the columns I added (`EPC_Found`, `EPC_Vehicle_Families`, `EPC_Buckets`, `EPC_Model_Series`, `EPC_GVW_Class`, `EPC_Markets`, `EPC_Emissions`, year span, `EPC_MultiPosFlag`) give you what you need.
2. **Decide:** is the workflow valuable enough to finish via path 1 (slow grind) or path 2 (Snap-on export)? Or do you want to pivot to path 3 (rebuild supersession from IE40 directly)?
3. **pricing discussion angle:** the "54% stale Newest P/N" finding is itself ammunition for the ITUK conversation — if the parts master used for PMS scoping is half-stale, the PMS sizing arguments need a different foundation.
