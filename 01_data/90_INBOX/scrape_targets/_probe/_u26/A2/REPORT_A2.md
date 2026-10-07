# U26 work package A (part) — agent A2: the UK sellers that are not KS

Scope owned: **T&M Commercials**, **Tranzparts**, and any further UK online seller that
lists UK prices for Isuzu parts. KS International belongs to A1, Omega to A3; neither was
touched. Branch `cursor/2026-10-07-universe-u26-market-harvest`.

Base commit at start: `8729346926caf7b2265f2487ff460f98d18f2d21`.
Every fetch went through `fetch_polite.PoliteFetcher` (consent gate first, >= 2.2 s per
host, disk cache). No 403/429 was seen on either harvested host. No CAPTCHA, login or
account was involved, and no seller was contacted.

## One line per host

| Host | Robots | Pages fetched | Rows written |
|---|---|---|---|
| tranzparts.co.uk | allowed | 278 (276 search + product) | 6 |
| www.tmcgroup.co.uk | allowed | 17 category pages | 55 |
| www.eurocarparts.com | **blocked** | 0 | 0 |
| www.carparts4less.co.uk | **blocked** | 0 | 0 |
| www.gsfcarparts.com | allowed, no usable route | 3 | 0 |
| www.milneroffroad.com | allowed, no usable route | 2 | 0 |
| www.ukpartsdirect.com | allowed, no usable route | 3 | 0 |
| www.japanpartsuk.co.uk | **unknown** (robots unreachable) | 0 | 0 |
| www.truckpartsonline.co.uk | **unknown** (robots unreachable) | 0 | 0 |
| www.buycarparts.co.uk | **unknown** (robots HTTP 403) | 0 | 0 |
| www.tmcshop.co.uk | **unknown** (host dead) | 0 | 0 |

## Numbers queried / with rows / still empty

| Pass | Queried | With at least one row | Empty |
|---|---|---|---|
| Tranzparts, Isuzu OE numbers | 123 | 5 | 118 |
| Tranzparts, competitor numbers | 153 | 0 usable (3 returned a card; see below) | 150 |
| T&M Commercials (category walk, no query URL exists) | 17 category pages | 55 distinct part numbers | n/a |

`rows.csv` holds **61 rows, every one priced**, all schema-clean against
`ledger_schema` (0 rows rejected). 15 of those rows are on the 123 worklist numbers,
covering **11 distinct** numbers. The other 46 are Isuzu parts outside the 123 that the
same category walk reached.

## The honest result, and the reason for it

**Tranzparts.** The search route works and returns server-rendered cards, but the
card does **not** print the searched number — it prints only vendor, title and price.
The number is on the *product page*, inside a `Cross reference:` list. The site's own
search index does match our Isuzu numbers against that list, so a search is a route to
a product page; it is not evidence on its own. Yield is therefore low: 276 searches
produced 9 cards, and 5 of the 123 OE numbers had a card at all.

**T&M Commercials has no part-number query URL at all.** `/?s=<pn>&post_type=product`,
`/wp-json/wc/store/v1/products?search=`, `/wp-json/wp/v2/product?search=`,
`/sitemap_index.xml` and `/product-sitemap.xml` each return **HTTP 504**, and
`/product-category/.../page/2/` is 504 while `/page/1` and the leaf categories answer.
The 2026-07-09 scraper note recorded the same search timeout. So the harvest route is a
**category walk**, not a per-number search, and that is why T&M contributes 55 rows the
worklist search would never have reached. Its cards carry the Isuzu number as
`data-product_sku` and a server-rendered `£ 76.04`, so they are readable without
JavaScript. A card whose sku is a shop code (`ISU708`) is skipped, not guessed.

**A real bug, found and fixed, worth recording.** The first version of the Tranzparts
parser emitted *every* 10-digit number on a product page. A competitor-number query for
`14459` returned a **DOUBLE CHECK VALVE** whose `Cross reference:` list holds 105
numbers — Bosch, Mahle/Knecht, Fleetguard, Brembo, EBS, Wabco — and **none of them
Isuzu**. That produced 20 fabricated rows, and a leading-digit shape filter still let
ten of them through (`1102681000`, `5000039183`, `5010038414`, `5021170111`,
`8283121000`, …). The parser now implements the toolchain's Mekonomen rule
(`verdict_for`): **the number that was searched for must be printed on the page**,
`parse()` requires `expected_pn` and returns one row for it, and the 105-number page is
kept as a fixture (`v_tranzparts_nonisuzu.html`) that the selftest asserts **raises**.
Competitor-number searches on this shop now write no rows at all: the product page does
not name the competitor brand behind a number, so there is nothing to cross-reference
from, and putting a non-10-digit competitor code in the `part_no` slot would be wrong
either way.

## Exact reason each dropped host was dropped

- **eurocarparts.com** — robots.txt disallows the search path; also listed blocked in
  `CROSSREF_SOURCE_RECON_2026-10-01.md`.
- **carparts4less.co.uk** — robots.txt disallows the search path.
- **gsfcarparts.com** — robots allows, but `/search?q=<pn>` and `/search-results?q=<pn>`
  both return HTTP 404; no query URL found from the home page either.
- **milneroffroad.com** — robots allows and `/?s=<pn>` renders a real search page, but
  it returns no product cards for an Isuzu number; no Isuzu coverage.
- **ukpartsdirect.com** — robots allows and the Magento route
  `/catalogsearch/result/?q=<pn>` works, but it returns 17 product cards with **no
  price** plus a no-results block; nothing readable.
- **japanpartsuk.co.uk** — robots.txt unreachable. UNKNOWN means stop.
- **truckpartsonline.co.uk** — robots.txt unreachable. UNKNOWN means stop.
- **buycarparts.co.uk** — robots.txt returns HTTP 403. UNKNOWN means stop.
- **tmcshop.co.uk** — robots.txt unreachable, the host is dead; the live T&M shop is
  `www.tmcgroup.co.uk`, which is allowed and harvested.

Full detail, including every individual URL and its outcome, is in `tried.csv`
(302 rows, 11 hosts).

## The U26 schema reconciliation (as instructed)

The U26 brief asks for `match_method=crossref_candidate` / `crossref_corroborated`.
Those strings are **not** in `MATCH_METHODS`, so `ledger_schema.row_problems()` would
reject them. `MATCH_METHODS` was **not** widened. Every row here keeps a schema-valid
`match_method` (`exact_oem`; the searched number is printed on the page) and carries the
grade in the separate **`crossref_grade`** column, which is `candidate` on every row.
Tranzparts additionally carries `crossref_grade=candidate` because the
cross-reference list behind the search is a single, unconfirmed source. Nothing is
"approved": approval needs the Eucon list or the existing grading rules.

## Fields, and where each was read

Price as shown, currency, VAT basis and stock are read from the page. **Pack contents
are not claimed on any row**: `parse()` never infers a kit or a set from a price, and
no row states a quantity. **Delivery is not a field in this ledger**, so the page's own
wording is carried in `fx_note` and its amounts (£5.99 / £19.99 ex VAT standard and
next-day; free over £80) are never read as the part price. VAT basis is read per source:
Tranzparts product pages print `EX VAT` under the price (so `excl`), while a Tranzparts
listing card and a T&M category card state no basis at all — T&M listing rows therefore
carry `vat="unknown"` rather than inheriting the product page's `incl`. Genuine rows
(T&M's own "Genuine Isuzu" wording) are `genuine_grey` and never mixed with
`aftermarket_retail`; a page whose wording says "non genuine" / "aftermarket" is never
badged genuine even though T&M's standing description text contains "Genuine,
guaranteed."

## Files written

- `rows.csv` — 61 priced rows, ledger columns + `page_file`, `crossref_grade`,
  `source_tried`
- `pages/` — 19 saved pages: 11 product/category pages holding the row evidence and the
  8 search pages that returned a card
- `tried.csv` — 302 rows, 11 hosts
- `status.json` — counts and the two measured limits
- `_a2_harvest.py`, `_harvest_log.txt` — the runner and its log
- Parsers, in `04_tools/delegation/parsers/`: `site_tmc.py`, `site_tranzparts.py`
  (registered automatically by `registry.py`; `price_parsers.py --selftest` now reports
  **ALL SELFTESTS PASS (10 sites)**)
- Fixtures, in `_probe/`: `v_tmc_product.html`, `v_tmc_category.html`,
  `v_tranzparts_product.html`, `v_tranzparts_search.html`, `v_tranzparts_search_two.html`,
  `v_tranzparts_nonisuzu.html`

## What could not be done

- **No competitor-price rows for the focus families from Tranzparts.** Its search does
  not index on competitor numbers we hold (KLTE0272 -> 0 cards), and where a
  competitor-number query did return a card the page named no competitor brand, so the
  row was dropped rather than invented.
- **No more than 5 of the 123 OE numbers on Tranzparts.** 107 of 123 return zero cards;
  the shop is a truck-and-trailer stockist, not an Isuzu dealer.
- **T&M cannot be queried by part number at all** (every search route 504s), so its 55
  rows come from a bounded 17-page category walk of the braking and service-items
  leaves. The `/page/2/` pagination is also 504, so deeper pages were unreachable.
- **Four further UK candidates were dropped on robots** (2 blocked, 2 unreachable) and
  **three allowed hosts had no usable route**; none was worked around.
