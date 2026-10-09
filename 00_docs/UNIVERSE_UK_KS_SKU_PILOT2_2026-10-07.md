# UK KS competitor-SKU pilot2 — result — 2026-10-07

## Verdict

**Accepted `exact_oem`: 0 of 20.** Twenty untried competitor/IAM SKUs (filter / clutch / exhaust families, not from the first SKU pilot’s eight PNs) were searched on KS International. Nineteen returned empty product grids. One returned a relevance card that failed the dual gate (competitor SKU + Isuzu OE on the same card/PDP). Nothing appended to the U29b ledger. No £10 delivery wire. Coverage rebuild skipped (no accepts). Eligible delta from this pilot: **0**.

Stopped at 20 as briefed.

## Method

1. Seed from graded / spareto / edges bridges on disk (same sources as SKU pilot 1). Exclude the eight pilot-1 PNs and every compact SKU already searched in pilot 1 (36 compact forms).
2. Prefer harvest2 filter/clutch PNs and exhaust shortlist; fill to 20 with other filter/clutch/exhaust bridges (`confirmed` / `likely` first, then `doubtful`).
3. Search `https://www.ks-international.com/catalogsearch/result/?q=<competitor SKU>`.
4. Accept only when **both** hold on the same search card or PDP: (a) the competitor SKU appears, (b) the target Isuzu OE is printed. Price must be ex-VAT £.
5. On accept: VAT excl + £10 for filter/clutch/exhaust; backup parquet before write; rebuild wider `--also-uk-exact`. **Not run** (zero accepts).
6. No invent. No ACCEPT. Board / INTERNAL not rebuilt.

## SKUs tried (20)

| # | Isuzu PN | Family | Tier | Brand | SKU searched | KS outcome |
|---|---|---|---|---|---|---|
| 1 | 5876150021 | air_filter | confirmed | Febi Bilstein | `184046` | empty |
| 2 | 5876150021 | air_filter | confirmed | Blue Print | `ADBP220063` | empty |
| 3 | 8981402650 | FILTER; ACL | confirmed | Febi Bilstein | `183982` | empty |
| 4 | 8981402650 | FILTER; ACL | confirmed | Ashika | `2009921` | empty |
| 5 | 8981394280 | FILTER; BLOWER UNIT | confirmed | Bosch | `0 986 628 519` | empty |
| 6 | 8981394280 | FILTER; BLOWER UNIT | confirmed | Kraft | `1735555` | empty |
| 7 | 8981596930 | ELEMENT KIT; FUEL FILTER | confirmed | Magneti Marelli | `153071762332` | empty |
| 8 | 8981596930 | ELEMENT KIT; FUEL FILTER | confirmed | UFI | `26.045.00` | empty |
| 9 | 8982705240 | ELEMENT; OIL FILTER | confirmed | Ashika | `10ECO150` | empty |
| 10 | 8982705240 | ELEMENT; OIL FILTER | confirmed | Iap Quality Parts | `12309023` | empty |
| 11 | 5876150180 | blower_filter | likely | Purro | `PURPC2001AG` | empty |
| 12 | 5876150000 | oil_filter | likely | Magneti Marelli | `153071762840` | empty |
| 13 | 5876150000 | oil_filter | likely | Valeo | `586188` | empty |
| 14 | 8983989321 | clutch_pressure_plate | likely | Exedy | `ISC842` | empty |
| 15 | 8970622940 | FILTER; AIR CLEANER | likely | BLUE PRINT | `ADZ92215` | empty |
| 16 | 8970622940 | FILTER; AIR CLEANER | likely | FLEETGUARD | `AF27693` | empty |
| 17 | 8983476230 | clutch_disc | doubtful | LUK | `328 0896 10` | empty |
| 18 | 8983476230 | clutch_disc | doubtful | Exedy | `ISD220` | empty |
| 19 | 8981475700 | fuel_filter | doubtful | KAMOKA | `F329901` | empty |
| 20 | 8981398300 | fuel_filter | doubtful | FEBI BILSTEIN | `35021` | **gate fail** (see below) |

Excluded pilot-1 PNs (no bridges reused from them): `5876150170`, `1876100934`, `1876101132`, `8975488420`, `8975425390`, `8982120690`, `8975056801`, `8978279610`.

## KS outcomes

| Outcome | Count |
|---|---:|
| SKU searches | **20** |
| No product cards | **19** |
| Cards but dual gate failed | **1** |
| Accepted exact_oem | **0** |

### The one non-empty search (rejected)

| Isuzu PN | SKU searched | KS cards | Why rejected |
|---|---|---:|---|
| 8981398300 | `35021` (Febi, doubtful) | 1 | Card is “FRONT DRIVE SHAFT C.V BOOT OUTER”, KS sku `0077072`. No `8981398300` on card. PDP lists Toyota-style PNs that contain the digit string `35021` as a substring — not a real competitor-SKU match for the fuel filter. |

## Ledger / coverage

| Step | Result |
|---|---|
| Staging CSV for accepted rows | Header only (0 data rows) |
| Backup + append to u29b `price_observations.parquet` | **Not run** |
| Wider rebuild `--also-uk-exact` | **Not run** (no accepts) |

| Metric | This pilot delta |
|---|---:|
| Wider UK eligible offers | **+0** |
| Wider UK eligible PNs | **+0** |

Live wider metrics on disk at write time (from Omega Store delivery wire earlier the same day, not from this pilot): **28 offers / 14 PNs**. Job brief started from **18 / 13**.

## What this means

Competitor-SKU search on KS for a second, diversified filter/clutch set behaves like pilot 1: almost all IAM numbers we hold are not indexed on KS, and the one hit is relevance noise. Combined with pilot 1 (0/32 SKU searches) this path has **0** OE-on-card accepts across **52** competitor-SKU queries. Stopped at 20. Do not invent SKUs or carriage.

## Paths

| Artefact | Path |
|---|---|
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_SKU_PILOT2_2026-10-07.md` |
| Bridge pick | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot2_20261007\sku_bridges_pilot2_20261007.json` |
| Search queue | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot2_20261007\sku_search_queue_pilot2_20261007.csv` |
| Fetch summary | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot2_20261007\sku_pilot2_fetch_summary_20261007.json` |
| Reject log | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot2_20261007\sku_pilot2_rejects_20261007.csv` |
| Empty staging | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot2_20261007\staging_exact_oem_accepted_sku_pilot2_20261007.csv` |
| Eligible rollup | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_sku_pilot2_20261007\sku_pilot2_eligible_before_after_20261007.json` |
| Bridge script | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_sku_pilot2_bridges_20261007.py` |
| Fetch script | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_sku_pilot2_fetch_20261007.py` |
| Prior SKU pilot (0 accepts) | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_SKU_PILOT_RESULT_2026-10-07.md` |

## Honesty

- No invented SKU / OE / £.
- Dual gate enforced (competitor SKU + Isuzu OE); no `category_only` written as ledger upgrades.
- No delivery £10 applied.
- No board / INTERNAL rebuild.
- No ACCEPT.
- Pilot stopped at 20 SKUs after zero accepts.
