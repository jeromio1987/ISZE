# REPORT B2 - U26 work package B, Portugal (hosts after B1's first)

Agent B2. Branch `cursor/2026-10-07-universe-u26-market-harvest`.
Worktree `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26`.
Every fetch through `fetch_polite.PoliteFetcher` (robots/consent gate first, >= 2.2 s per
host, byte cache). No bot check bypassed, no account created, no seller contacted.
Autodoc and Oscaro not attempted (retired, Turnstile).

## Verdict

**No reachable Portuguese host publishes an Isuzu part price without JavaScript.**
Six hosts passed the three gates (HTTP 200, path allowed by robots.txt, search page
loads) and were swept across all 123 Isuzu OE numbers and all 153 competitor numbers -
1,370 queries on those six - and returned no usable price. `rows.csv` is header-only:
**0 rows, 0 of 123 numbers evidenced.**

Two apparent hits were checked and discarded (evidence in `_part_*.tried.csv`):
`spareparts.pt` printed "o preco mais alto e EUR 264,99", which is a price-filter
widget, not a product (that shop is a household-appliance spares site); `www.isuzu.pt`
printed "DESDE 345EUR +IVA/mes", the D-MAX finance banner on its homepage.

## Hosts tried

296 distinct hosts robots-checked by the project's own gate. Full list in `tried.csv`
(host, url pattern, robots verdict, http status, outcome) and every query in
`tried_queries.csv`.

| verdict | hosts |
|---|---|
| allowed by robots.txt | 43 |
| blocked by robots.txt (explicit Disallow) | 4 (`motointegrator.com`, `cars245.com`, `micksgarage.com`, `rrr.lt`) |
| unknown (robots 403/404/DNS/SSL/timeout -> treated as blocked) | ~245 |

Retired / previously blocked, not retried: Autodoc, Oscaro, Mister-Auto, Trodo
(2026-10-01 recon + brief).

## The six swept hosts

| host | what it is | queries | empty | page with no price | priced | outcome |
|---|---|---|---|---|---|---|
| `www.truckparts.pt` | PT truck-parts, WP | 274 | 261 | 0 | 0 | search misses every number; 13 robots=503 -> consent refused |
| `www.turbopecas.pt` | PT parts shop, WP | 274 | 274 | 0 | 0 | "Nothing Found" on all |
| `www.isuzu.pt` | Isuzu Portugal importer | 274 | 271 | 2 | 1 (discarded) | only the D-MAX homepage finance banner |
| `www.ascendum.pt` | PT distributor group | 274 | 274 | 0 | 0 | "We couldn't find any results" |
| `www.sotecnica.pt` | PT industrial/energy group | 274 | 17 | 257 | 0 | search page never matches a part |
| `spareparts.pt` | PT household-appliance spares (Shopify) | 274 | 17 | 254 | 3 (discarded) | price-filter widget, not products |

## Why every other allowed host is unusable

- **Catalogue behind JavaScript**: `pecauto.com` returns a 127-byte shell; `europart.net`
  product search is a JS app (`/assortment/product-search/filter?...` returns the shop
  shell, no results); `roady.pt`, `midas.pt` are JS chain shells.
- **POST-only search**: `b-parts.com` search is a POST form; GET query URLs return
  HTTP 405 (B1 also saw 403 on its product paths).
- **Not a parts shop**: `carglass.pt` (glass), `salvadorcaetano.pt` (car dealer),
  `alcampo.es` (supermarket), `datapremium.pt` (platform vendor), `carservice.es`
  (workshop chain), `euromaster.pt` (tyres/workshops), `baterias.pt` (batteries),
  `radiadores.pt` (empty), `turbodiesel.pt` (workshop), `baterias.pt`.
- **Guessed-domain 404s / dead**: `truckparts.pt/loja`, `turbopecas.pt/loja`,
  `mcr.pt` (city council), `bragauto.pt` ("Sem resultados"), `sulpecas.pt`,
  `andres.pt` (property), `lojadepecas.pt` (Eurotyre), `autosueco.pt` (Volvo).
- **Unreachable to our identity**: the ~245 `unknown` hosts returned robots 403/404 or
  failed DNS/SSL/timeout for every search path tried.

## Same three tests per host

1. Price visible without JavaScript - **failed on every host** (no host served a part
   price in raw HTML for our numbers).
2. HTTP 200 - passed on many, but the page then held no part data.
3. robots.txt allows the path - checked before every fetch; `consent_refused` count
   recorded per host (13 on `www.truckparts.pt` when its robots went 503 mid-sweep).

## Numbers

- OE numbers queried: 122 distinct (the 123-list has one duplicate); competitor numbers:
  152 distinct. 1,370 seed queries on the six swept hosts.
- Numbers with at least one row: **0**. Numbers still empty: **all 122**.
- Pages saved under `pages/`: 0 (no row survived the false-positive check).
- Parser written: none. `price_parsers.py --selftest` passes (10 sites) - no new parser
  was added because no PT host yielded a parseable price.

## The ledger-schema reconciliation the run instructions asked to settle

`match_method=crossref_candidate` / `crossref_corroborated` are not in `MATCH_METHODS`,
so `ledger_schema.row_problems()` would reject them. I did **not** widen `MATCH_METHODS`.
Rows carry `match_method="crossref"` (schema-valid) and the grade travels in the extra
column `crossref_grade` (candidate | corroborated) in this folder's `rows.csv`. No row is
ever "approved" unless Eucon-listed or graded confirmed. (This run wrote no rows, so the
point is recorded for the merge step.)

## Files in this folder

- `rows.csv` - header-only (0 observations)
- `pages/` - empty (nothing passed the false-positive check)
- `tried.csv` - 296 hosts, host-level
- `tried_queries.csv` - 1,644 per-number query outcomes
- `status.json` - counts, per-host breakdown, could-not-do list
- `_probe_robots*.py`, `_probe_content*.py`, `_sweep_host.py`, `_make_outputs.py` - the
  probes and the sweep (all fetch through `PoliteFetcher`)
- `_robots_probe*.csv`, `_content_probe*.json` - raw evidence per probe
- `_part_*.{json,csv}` - per-host sweep output
