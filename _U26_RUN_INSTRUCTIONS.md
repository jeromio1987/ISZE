# U26 run instructions — shared by all nine agents

Authority: `C:\Users\jerom\Desktop\claude\docs\cursor_briefs\2026-10-07_U26_MEGA_market_data_harvest.md`
(status GO). Where U25 and U26 differ, U26 wins. Read both before you touch anything.

Worktree (do everything here): `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26`
Branch: `cursor/2026-10-07-universe-u26-market-harvest`
Base commit: `8729346926caf7b2265f2487ff460f98d18f2d21`

## Scope, unchanged and non-negotiable

IN: brake pads, oil filters. UK = ITUK (never IUK). Portugal. The 123 Isuzu numbers
in the worklist. 153 Eucon competitor numbers (UK/A only).

OUT: oil/lubricants; every other family and market; MIDI/Spain; Turkey; UTI/UMI
blending; contacting anyone; Nordics keys (closed); deploy; sync; merge to main.

NEVER: bypass a CAPTCHA, Turnstile or login; create an account; invent or estimate a
value; send an Eucon row to DeepSeek or any service outside the EU; contact a seller.

## Inputs — read these from the MAIN clone, they are not in this worktree

- Worklist: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\MARKET_SCRAPE_WORKLIST_20261007.csv`
  (680 rows; 123 distinct Isuzu numbers; 340 UK + 340 PT; `has_eucon_competitor_pn`)
- 112 with no Eucon cross-reference: `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\NEEDS_CROSSREF_112_PNS_20261007.csv`
  (41 brake_pad, 71 oil_filter). The other 11 of the 123 are the Eucon-approved ones.
- Source recon: `C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\CROSSREF_SOURCE_RECON_2026-10-01.md`
  Read the ranking table before you try any site. Most candidates are already known-blocked.
- Ledger: `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\price_observations.parquet` (read only)
- Graded crossref: `C:\Users\jerom\Desktop\claude\ISZE\04_tools\aftermarket_intelligence\state\crossref_graded.csv`
- Existing Spareto result (487 parts): `...\state\spareto_crossref.csv` + `spareto_crossref_per_part.csv`
- Eucon raw: `01_data\01_Pricing\_raw\eucon_pricing_partspool_20260329.xlsx`,
  `01_data\Eucon_Online28072025.xlsx`, `01_data\Eucon_March.xlsx`

Every agent writes only inside its own folder:
`<worktree>\01_data\90_INBOX\scrape_targets\_probe\_u26\<YOUR_ID>\`

Nothing writes into the shared `_probe\` root, the shared `page_manifest.csv`, the
shared `OFFERED_ROWS.csv`, or the ledger parquet. One later merge step does that.

## Fetching discipline (every fetch, no exception)

All fetching goes through `04_tools\delegation\parsers\fetch_polite.PoliteFetcher`, which
runs the robots/consent gate `04_tools\autodoc_scraper\check_scrape_consent.py` first,
keeps >= 2.2 s between requests to one host, and caches bytes to disk.

- >= 2.2 s per host. Stop immediately on any 403 or 429 and report the host.
- Declared bot identity stays as it is in `fetch_polite.py`. Do not change it.
- Check robots.txt and terms before the first fetch of a host. If it forbids, drop the
  source and record why. Autodoc / Oscaro are retired (Turnstile): do not attempt them.
- Python here is 3.14; run from the worktree root.

## Row fields — read off the page, never infer

price as shown, currency, tax included/excluded (+ rate if shown), delivery included or
not (+ cost if shown), pack contents (piece / set / kit + the quantity the page states),
competitor brand + number, source URL, observation date, stock. If the page does not
state a field, leave it empty. Never derive pack contents from the price.

Ledger columns (21) are fixed by `04_tools\delegation\parsers\ledger_schema.py`:
obs_id, part_no, match_method, competitor_brand, competitor_pn, description, source,
source_url, country, observed_at, vintage, price, price_avg, currency, price_eur,
fx_note, vat, price_type, stock, n_obs, loader.

Allowed `match_method`: `exact_oem`, `crossref`, `category_only`. Allowed `price_type`
includes `aftermarket_retail`, `aftermarket_trade`, `genuine_grey`, `marketplace`.

**KNOWN ISSUE — settle it and report it.** The U26 brief says store rows with
`match_method=crossref_candidate` or `crossref_corroborated`. Those two strings are NOT
in `MATCH_METHODS`, so `ledger_schema.row_problems()` rejects them and the row never
reaches the ledger. Do NOT widen `MATCH_METHODS` silently. Instead keep
`match_method="crossref"` (schema-valid) and carry the grade in a separate column
(`crossref_grade` = candidate | corroborated) written to your own row CSV, and state
this reconciliation in your report. Nothing is ever "approved" unless it is
Eucon-listed (Jerome-approved) or graded confirmed by the existing rules.

## Output every agent writes in its own folder

1. `rows.csv` — ledger-shaped rows, one per observation, plus `page_file`,
   `crossref_grade`, `source_tried` columns.
2. `pages\` — one saved page copy per row (for the verbatim check).
3. `tried.csv` — every source/host you attempted: host, url pattern, robots verdict
   (allowed/blocked/403), outcome. This is the "what was tried and failed" record.
4. `status.json` — counts: numbers queried, pages fetched, rows, priced rows,
   hits, misses, blocked hosts, and anything you could not do.

## Report back (short, no prose)

- One line per source/host: allowed or blocked, pages, rows.
- Numbers queried / numbers with at least one row / still empty.
- Every site you dropped and the exact reason.
- `git rev-parse HEAD` at start; commit your own files on the branch and give the hash.
- Anything you could not do, stated plainly.

## Stop and report, do not improvise

- A host returns 403/429 twice.
- A source needs a login, a key or a fee.
- You would have to touch a shared file, the shared manifest, or the ledger parquet.
- You would have to change a builder outside your own folder.
