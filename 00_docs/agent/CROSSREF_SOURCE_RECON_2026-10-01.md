# Cross-reference source recon — 2026-10-01

**Question.** The 19:40 board row said that searching by competitor number needs a site that indexes aftermarket brand numbers against Isuzu numbers, and that none of the working sites does. Is there a public site that, for an Isuzu number, lists the brand equivalents (Bosch, Mann, Febi, Blue Print …) and ideally works in reverse too? It must work without a login and allow automated access.

**Answer.** Yes, one: **Spareto** (`https://spareto.com/oe/<isuzu number>`). It found brand numbers for 4 of the 5 seed numbers and for 8 of 9 numbers in total. robots.txt allows the pages and the Conditions of Sale say nothing against automated access. It is also the first source we have that does not come from Eucon. Every other candidate was blocked by robots.txt, sat behind a bot check, only loads its data from a robots-blocked API, or did not cover Isuzu. A parser with a passing selftest is written. Nothing was run at volume.

Evidence root: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\delegation\parsers\_recon_crossref\`. It holds one folder per site, each fetched page as `<name>.html`, and a `<name>.meta.txt` next to it with the URL, final URL, HTTP status, bytes, timestamp and user agent. Every robots.txt is in `robots\<host>.robots.txt`. All fetches used the declared bot identity `ISZE-parts-research/1.0`, the consent gate's robots matcher (`check_scrape_consent.allowed`) and at least 2.2 s per host. No bot check was bypassed, no consent banner was clicked, no account was made and no credentials were used.

## Test numbers

These come from `04_tools\aftermarket_intelligence\state\seed_reach_tierA.csv`. Three are tagged `n_series_truck` in `01_data\00_derived\epc_decode_nseries_banded.csv`, so the test covers truck parts and not only D-Max parts.

| # | Isuzu number | Seed description | Why chosen |
|---|---|---|---|
| 1 | 8982705240 | ELEMENT; OIL FILTER | maintenance; 64 brand numbers in our existing cross-reference graph, so we have a known answer to check against |
| 2 | 8981596930 | ELEMENT KIT; FUEL FILTER | maintenance; 155 brand numbers in the graph |
| 3 | 8982447940 | PAD KIT; CALIPER,DISC BRK,FRT | `n_series_truck` (brake_pad) |
| 4 | 5876102320 | CLUTCH KIT | `n_series_truck` (clutch_kit) |
| 5 | 8981919560 | ROTOR; DISC BRK,RR | `n_series_truck` (brake_rotor) |

Spareto was also given 8974995480 (air filter), 8983767550 (front brake disc), 8975546610 (front pad kit) and 8982984040 (oil filter). Those were the first picks, made before the truck tag was checked.

## Ranking

| Rank | Site | Isuzu coverage (evidence) | Search without login | robots / terms | 5-number test | Verdict |
|---|---|---|---|---|---|---|
| **1** | **Spareto** `spareto.com/oe/<pn>` (seller Spareto OÜ, Tallinn) | N-series truck numbers resolve: 8982447940 → 13 brand cards, 8981919560 → 2 (`spareto\oe_8982447940.html`, `oe_8981919560.html`). D-Max fitment is shown for one brake disc: `product_delphi_bg5331c.html` "Fit Vehicles ISUZU … D-MAX 2017 - ...". The truck **fitment** list is empty on `product_blueprint_adz94218.html` and `product_febi_192691.html`. F-series not tested. | Yes | `/oe/` and `/products/` not disallowed; `Crawl-delay: 1` (`robots\spareto.com.robots.txt`). `spareto\terms.html`: no clause on automated access (searched for automat/robot/scrap/crawl/spider/harvest/reproduc/intellectual). Prices "including VAT for customers within the European Union". | **4 of 5** (13 / 31 / 13 / **0** / 2 cards; the clutch kit page says "Nothing Matches your Search") | **Usable. Parser written.** |
| 2 | bilstein group partsfinder (febi, SWAG, Blue Print) `partsfinder.bilsteingroup.com` | not established: the page holds no results (see next cell) | the page loads, but the HTML is only a script shell (`bilstein_partsfinder\search_q_8982705240.html`: 87 characters of visible text, and the query only appears inside the app's state) | **`Disallow: /api/`**, and the results come from `/api/` | 0 of 1 readable | Not usable without breaking robots. Covers only its own brands anyway. |
| 3 | MANN-FILTER catalogue (also the platform behind Filtron and WIX) | not established | the search page is a script shell (`mann_filter\search_8982705240.html`: the number does not appear on the page) | **`Disallow: /api/graphql/`**, which is where the page gets its data (the page config names `graphqlEndpoint: /api/graphql/catalog-prod`) | 0 of 1 readable | Not usable |
| 4 | Sakura Filter `sakurafilter.com/search?keyword=` | none found | Yes | allows everything | **0 of 5** ("No result found" on all 5, plus the dashed form `8-98270524-0`) | No Isuzu numbers indexed |
| 5 | Fleetguard `fleetguard.com` | not established | Salesforce app with no server-side content; the guessed search URL gave a 404 (`fleetguard\search_8982705240.html`) | allows everything | not testable without a browser | Not usable this way |
| — | Hengst online catalogue `catalog.hengst.com` | — | — | robots allows, `Crawl-delay: 10` | the search page returns Cloudflare "Just a moment..." (`hengst\catalog_search_page.html`, HTTP 403) | **Stopped: bot check** |
| — | daparto.de | — | — | **`Disallow: /Teilenummernsuche/Teile/`**, which is exactly its part-number search | not fetched | Blocked by robots |
| — | finditparts.com (US truck parts) | — | — | **`Disallow: /search`** and `/*?*s=` | not fetched | Blocked by robots |
| — | Baldwin cross-reference | — | — | **`Disallow: /cross-reference-result-page*`** | not fetched | Blocked by robots |
| — | eurocarparts.com, winparts.be, megazip.net, motointegrator.com | — | — | search paths disallowed (`/search?query=`, `/zoekresultaten?zoek=`, `/search`, `/*?*`) | not fetched | Blocked by robots |
| — | kfzteile24.de, ebay.co.uk | — | — | `Disallow: /`; eBay's robots.txt also says automated access is prohibited without permission | not fetched | Blocked by robots |
| — | autodoc.co.uk, autodoc.de, onlinecarparts.co.uk, buycarparts.co.uk, trodo.com, ridex.eu, oscaro.com, mister-auto.com, autoteile-meile.de, teilehaber.de, autopartspro.co.uk, partsouq.com | — | — | robots.txt itself returns HTTP 403 (Cloudflare challenge); partsouq's home page too | not fetched | **Stopped: bot check.** Unknown counts as blocked |
| — | shop.donaldson.com, emex.com, japko.pl, kavoparts.com, katalog.intercars.eu | — | — | robots.txt timed out, failed DNS, failed SSL, or returned HTTP 522 | not fetched | Unreachable, so treated as blocked |
| — | web.tecalliance.net (TecDoc catalogue) | — | home page is a script shell titled "TecDoc" with no content | allows everything | not tested | Whether it needs an account was **not established**. If it does: needs an account, Jerome's call |
| — | exist.ru | — | — | robots allows `/Price/` | **not fetched on purpose** | Russian retailer: a compliance call, Jerome's |
| — | lubefinder.com, japanparts.com, herthundbuss.com | lubricants shop (0 hits); a Japanese used-parts site, not Japanparts (Italy); the H+B `/suche/` search returned 404 | — | allow | — | Not relevant. The H+B pages were 26 MB, so only their first 4 KB is kept |

## Spareto in detail

**What a page gives.** `/oe/8982705240` has the title `8982705240 - Oil filter, oil filter by ISUZU` and 13 brand cards. Each card carries a JSON block with `item_brand` and `item_id`, the price, the currency, and a dispatch line. Examples: BLUE PRINT ADZ92130 EUR 8.54, ASHIKA 10-ECO150 EUR 6.58, BOSCH F 026 407 349 EUR 8.47, HENGST FILTER E1194H D1072 EUR 8.20 (`spareto\oe_8982705240.html`). Across the 9 pages there are **94 rows** (`spareto\SPARETO_CROSSREF_SAMPLE.csv`).

**Agreement with our Eucon-derived graph** (`crossref_graded.csv`, numbers compared with spaces, dashes, dots and slashes removed):

| Isuzu number | Spareto brand numbers (distinct) | already in graph | of which confirmed/likely | new vs graph |
|---|---|---|---|---|
| 8982705240 | 13 | 12 | 9 | 1 |
| 8981596930 | 30 | 28 | 13 | 2 |
| 8982447940 (N-series) | 12 | 3 | 0 | 9 |
| 5876102320 (N-series) | 0 | 0 | 0 | 0 |
| 8981919560 (N-series) | 2 | 0 | 0 | 2 |
| 8974995480 | 4 | 3 | 2 | 1 |
| 8983767550 | 9 | 6 | 1 | 3 |
| 8975546610 | 21 | 20 | 6 | 1 |
| 8982984040 | 1 | 0 | 0 | 1 |
| **Total** | **92** | **72** | **31** | **20** |

72 of 92 Spareto pairs are already in the graph, so where both sources hold a number, Spareto agrees with it. 41 of those 72 are graded doubtful or reject today, and a second, independent, non-Eucon source is exactly what the grading said they lack ("single source file, no corroboration"). Where the graph is thin, on the N-series numbers, Spareto adds 11 pairs. *(Computed by the scratch script `compare.py` over the saved pages; it was not kept in the workspace.)*

**Reverse direction (brand number → Isuzu number).** This works in two ways:
- A brand product page lists its OE numbers. `product_blueprint_adz94218.html` gives ISUZU 8-97168-634-0, 8-97378-446-0, 8-98216-926-0 and **8-98244-794-0 (= 8982447940)**, plus cross-reference numbers from 96 makes.
- `/oe/<brand number>` falls through to a product search: `reverse_oe_ADZ94218.html` shows "Search results for "ADZ94218" … 1 BLUE PRINT". The site's own declared search is `https://spareto.com/products?keywords={term}`, from the Organization JSON-LD on the product page. `/search?keywords=` returns 404 (`search_ADZ92130.html`).

**Limits. Do not over-read the coverage.**
- 1 of 5 seed numbers (the clutch kit) is missing. The sample is 9 numbers, so it gives no hit rate for Tier A as a whole.
- The truck fitment list is empty. Spareto holds the number link for N-series parts but does not list the truck as a vehicle that fits.
- Prices are retail, in EUR, **including VAT**, for the delivery country the page shows, which was Belgium (taken from our IP). The VAT rate is not stated, so the parser stores `vat="incl"` and does not back the VAT out.
- Spareto's pages do not say where its cross-reference data comes from.
- Whether reusing a retailer's displayed cross-reference at volume is acceptable is a business and legal call. robots.txt and the terms do not object. That is all this recon can say.

## What was built

- `04_tools\delegation\parsers\site_spareto.py`. It follows the per-site parser pattern (`SITE`, `PROBE_PAGE`, `parse()`, `selftest()`), so `registry.py`, `run_probe.py` and `price_parsers.py --selftest` pick it up.
  - `parse(html)` turns an `/oe/<pn>` page into one row per brand card, with the ledger `COLUMNS` in order, the same shape as `KS_CROSSREF_ROWS.csv`.
  - `part_no` is taken only from the page title (`<pn> - … by … ISUZU`), never from a card. `match_method="crossref"`, `price_type="aftermarket_retail"` (`genuine_grey` if the brand is ISUZU), `vat="incl"`, `loader="spareto_crossref"`.
  - A "Nothing Matches" page returns `[]`. Any page that is not an OE page raises `ParseError`.
  - `parse_product(html)` does the reverse lookup.
  - The CLI has `--selftest`, `--parse-recon` (offline) and `--online --pn … --limit 5`, which fetches only through `fetch_polite.PoliteFetcher`.
- Selftest: **PASS**. It checks 13 rows, four exact brand/number/price triples, 11 of 13 cards marked in stock, the clean miss, the reverse lookup and the refusal of a non-OE page. `price_parsers.py --selftest`: **ALL SELFTESTS PASS (8 sites)**, and `run_probe.py --site spareto` gives 13 rows with schema clean.
- The fixture was copied to `01_data\90_INBOX\scrape_targets\_probe\v_spareto_oe_8982705240.html`, because that is where `run_probe.py` looks.
- One live check through the consent gate: `--online --pn 8982447940` fetched 1 page, 0 refused, and wrote 13 rows to `spareto\ONLINE_PATH_CHECK.csv`.
- **Not done:** no volume run, nothing loaded into the ledger, `build_price_ledger.py` and `grade_crossref_edges.py` not changed, no git commit.

## Decisions for Jerome

1. **Go or no-go on Spareto at volume.** Tier A is 491 numbers, which is about 491 pages at 2.2 s each, roughly 18 minutes of fetching.
2. **If go:** do Spareto rows (a) go into the price ledger as a new source, (b) go into `grade_crossref_edges.py` as a second, independent source, so that a Eucon edge Spareto also lists can move up from doubtful, or (c) both?
3. **TecDoc / bilstein / MANN:** these hold the data, but only behind a login or a robots-blocked API. A data agreement would be the route there, not scraping.
