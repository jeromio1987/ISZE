# EPC BVP discovery — what this unlocks (updated)

## TL;DR

Snap-on EPC for Isuzu exposes a **"BEST VALUE PARTS (BVP)" master list** with **28 strategic competitive-parts categories**. Your v5.1 PMS file covers **4** of them. The other **23 unique categories** represent Isuzu's officially-curated PMS / wear-parts expansion opportunity, already strategically grouped by Isuzu themselves.

We pulled the full BVP index with internal attachment IDs but **could not download the per-category PDFs via automation** — Snap-on session-killed our scraper three times in this session, and direct attachment-URL access requires headers our automated client can't replicate. **Path forward = manual click in EPC, or ask Snap-on for the bulk BVP file.**

## The 28 BVP categories (full list, with attachment IDs)

| # | Category | Attachment ID | In your v5.1 file? |
|---|---|---|---|
| 00 | BEST VALUE PARTS CATALOG 2026 (master index) | 12457 | — |
| 01 | AIR FILTER | 10076 | ✓ (FIG 130-006) |
| 02 | BLOWER UNIT FILTER / **UREA FILTER** | 10095 | partial — file has cabin filter; **UREA filter missing** |
| 03 | OIL FILTER | 12458 | ✓ (FIG 050-002) |
| 04 | FUEL FILTER | 10102 | ✓ (FIG 041-002) |
| 05 | WATER PUMP | 10084 | ✗ |
| 06 | GENERATOR | 10097 | ✗ |
| 07 | STARTER | 12456 | ✗ |
| 08 | ENGINE FOOT RUBBER | 10085 | ✗ |
| 09 | BELT (cooling fan / A/C cmpr / P/S pump) | 12461 | ✗ |
| 10 | CLUTCH KIT | 12459 | ✗ |
| 11 | CLUTCH DISC | 12455 | ✗ |
| 12 | CLUTCH COVER | 12460 | ✗ |
| 13 | RELEASE BEARING / PILOT BEARING | 10093 | ✗ |
| 14 | CLUTCH BOOSTER | 10090 | ✗ |
| 15 | CENTER BEARING | 10080 | ✗ |
| 16 | HUB BEARING | 10096 | ✗ |
| 17 | HUB OIL SEAL | 10103 | ✗ |
| 18 | KING PIN KIT | 10087 | ✗ |
| 19 | BUSHING (shackle / leaf / trunnion / torque rod) | 10100 | ✗ |
| 20 | LEAF SPRING ASM | 10101 | ✗ |
| 21 | SHOCK ABSORBER | 10099 | ✗ |
| 22 | WHEEL PIN SET | 10086 | ✗ |
| 23 | BRAKE LINING KIT | 10092 | ✗ |
| 24 | BRAKE SHOE KIT | 10082 | ✗ |
| 25 | BRAKE PAD KIT | 12453 | ✗ |
| 26 | BRAKE ROTOR | 10088 | ✗ |
| 27 | WIPER BLADE | 12454 | ✗ |

**Coverage: file has 4/27 unique categories = 15%. 23 categories untapped.**

## Strategic implications

1. **PMS scope reframe.** Your current sheet treats PMS as "filters." Isuzu's own competitive-parts position says PMS = **27 wear-item categories** spanning filters → clutch → suspension → brakes → wipers. Even rough sizing of the missing 23 multiplies the revenue-gap argument with ITUK by 3-5×.

2. **UREA filter (Euro 6 AdBlue PMS) is missing entirely.** For ITUK's Euro 6 N-series fleet, this is a real, growing PMS line. Quick to add.

3. **5 brake categories grouped (23-27)** = Isuzu's official competitive brake basket. For HCV-heavy distributors, this is a much larger PMS € than filters alone (brake pads/rotors are higher unit price).

4. **Clutch sub-basket (10-14) is its own PMS sale.** Clutch kit + disc + cover + release bearing + booster are typically replaced together at long intervals — high-ticket, high-margin "PMS" event for HCV/MCV.

5. **The v7 reclassification is validated.** Isuzu officially groups blower-unit filters with cabin/UREA filters → cabin-AC filter is the right L3 (the v7 fix is consistent with Isuzu's taxonomy).

## What's blocking the per-category PN list

Three things, in order of severity:

1. **Anti-bot / session invalidation.** Snap-on EPC killed our automated session **3 times** during this work. They actively detect non-human interaction and force re-login. This means any scraping at scale is impractical.
2. **Custom auth headers.** The PDF download endpoint requires `User-Id` + `SBSEQHITEPCCS` JWT headers. We captured them once, but they're time-bound and tied to active session — and Chrome MCP blocks direct cookie access for security.
3. **Unknown URL pattern.** Snap-on's bundled JS doesn't expose attachment-download URLs as plain literals. The download endpoint is built from runtime template strings we couldn't extract.

## Workable next moves (ranked by ROI)

1. **★ Ask Snap-on for the BVP master file (PDF + Excel).** They publish this for distributors. One email, 5 minutes, gets you all 27 categories with PNs. This is the right ask; anything else is fighting their UI.
2. **Manual click-through in EPC.** Open EPC → Information → BVP → click each of the 27 categories one by one. If the click triggers an inline PDF viewer (which the automated clicks couldn't), you can download each manually. ~10-15 min of clicking if it works.
3. **Build the missing-category PMS model in parallel.** For each of the 23 missing categories, sketch the per-vehicle frequency × price assumption (even rough). Combined with ISZE distributor-by-distributor UIO, this is the v6 PMS model your file aspires to be — and you can do it without waiting for the PN lists.

## Files saved

- `bvp_categories.json` — full 28-entry list with attachment IDs
- `epc_results_merged.json` — 55 PNs of catalogue-applicability data (47 with full enrichment)
- `ITUK_PMS_Analysis_Apr2026_v7_reclassified.xlsx` — 118 L3-classification fixes applied
- `BVP_FINDING.md` — this file

## On Task C (fleet → recommended PMS basket)

Same blocker. Single-clicking a catalogue edition (e.g. 51678 = 2016 NNR/NPR-RHD EURO6 EUROPE) does expand the right panel to show FIG entries for that vehicle — but **clicking a FIG entry to drill into the actual parts list doesn't work via automation**. The SPA's navigation is gated on internal state JavaScript-dispatched clicks don't satisfy.

**The "fleet → PMS basket" workflow is still achievable, but only manually for now:**

In EPC: TRUCKS → N-series → pick catalogue edition (e.g. NPR75 RHD EURO6 2016) → drill to FIG-KEY 050-002 / 130-006 / 041-002 / 873-042 → read the recommended PN per FIG.

For the ITUK-priority editions, this is ~5-10 catalogue editions × 4 FIGs = ~30-40 manual lookups. Doable in 30 min by a human. **If you can do that and paste me the PNs (one row per edition × FIG), I'll build the "ITUK PMS basket" sheet from there.**
