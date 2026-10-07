# A1 report — work package A, KS International half

Agent A1, U26 market-data harvest. Base 8729346926caf7b2265f2487ff460f98d18f2d21.
HEAD at start 8729346926caf7b2265f2487ff460f98d18f2d21.

## One line per source

| host | robots | pages fetched | rows |
|---|---|---|---|
| www.ks-international.com | allowed (check_scrape_consent.py exit 0 for /catalogsearch/result/) | 272 (149 competitor + 123 OE) | 33 (all relevance, 0 strict) |

## Numbers

- Competitor pass: 149 seeded (153 lines, 149 distinct after separator squash), 149 queried, 0 with a strict row, 149 still empty. 145 queries returned no card, 4 returned cards that did not print the searched number.
- OE pass: 123 queried, 16 with rows, 107 still empty (no card). 33 relevance rows total.
- Strict acceptance (number printed on the card): 0 of 272 queries. KS prints the searched number in the page plumbing (title, search box, cache URL) 12 times and in the card 0 times, measured on 8982705240 and 8975546610.
- Rows kept: 33, all match_method=category_only, crossref_grade=category_only_relevance. 14 genuine_grey, 19 aftermarket_retail. 33 of 33 priced, ex-VAT GBP, all 33 verbatim in their own saved page. Schema clean (ledger_schema.row_problems empty).

## Sources dropped

- None dropped for robots or a bot check. KS answered every request with HTTP 200; no 403, no 429, no login, no CAPTCHA.
- Competitor numbers KS does not index are not a dropped source, they are a measurement: 0 of 149 cards carried the searched Eucon aftermarket number, so no aftermarket price could be proven on KS by that route.

## Patches (on the branch, committed)

- run_crossref_queries.py: --seed-csv (query a fixed competitor-number file), --out-rows / --out-report / --pages-dir / --tried-csv (write into the agent folder instead of the shared 04_tools/price_ledger/KS_CROSSREF_ROWS.csv and _crossref_query_run.json). Acceptance rule, fetch discipline and data boundary unchanged.
- run_dated_pass.py: pns_from_csv now reads a headerless one-number-per-line seed file (the old DictReader returned 0 of 123 for the A/B/C seed_oe_pns.csv); --cache-root and --stop-file. Per-pass cache and fetch discipline unchanged.
- _u26_a1_build.py: new; assembles rows.csv, pages/, tried.csv, status.json from the two passes.

## KNOWN ISSUE

match_method=crossref_candidate / crossref_corroborated are not in MATCH_METHODS, so the ledger would reject them. MATCH_METHODS was NOT widened. Rows keep match_method="crossref" and carry the grade in crossref_grade. On this source nothing reached the crossref grade at all (0 strict).

## Could not do

- Nothing on KS meets the strict rule. A1 produces real observed prices only as category_only relevance rows; whether those may be used as comparables is the evidence rules' call, not this agent's.
- Shared files untouched: KS_CROSSREF_ROWS.csv, _crossref_query_run.json, page_manifest.csv, OFFERED_ROWS.csv, price_observations.parquet all unchanged on this branch.
