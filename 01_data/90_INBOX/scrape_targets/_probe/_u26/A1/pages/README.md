# A1 pages

One saved page per row, 16 files, 172 KB total.

Each file is the parser slice of the KS search page the row was read from (site_ks._slim_for_parse): the title, the name="q" search box and the product grid. That is the exact input the parser turned into rows, so the verbatim check runs on it. The full KS page is ~2.4 MB of Magento CSS/JS chrome; the raw bytes of all 123 OE pages are kept in the per-pass cache at 01_data/90_INBOX/scrape_targets/_probe/_u26/A1/passes/u26_a1_oe_20261007/cache/www.ks-international.com/ (fetched 2026-10-07, 123 pages, all HTTP 200 through fetch_polite.PoliteFetcher).

File naming: oe_<searched number>_<url hash>.html.

Every row on these pages is a relevance card (match_method=category_only): KS returns cards for the searched OE number but prints our number only in the page plumbing, never in the card, so no card carries the searched number. All 33 rows are still real observed prices and are kept as such. See ../status.json.
