# B1 report — U26 work package B, Portugal (discovery + first usable host)

Agent B1. Branch `cursor/2026-10-07-universe-u26-market-harvest`.
Worktree `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26`.
All fetching through `fetch_polite.PoliteFetcher` (consent gate first, >= 2.2 s per host,
disk cache). No bot check bypassed, no account created, no seller contacted.

## Result

**No Portuguese host passed the three gates at the same time** (price in the raw HTML
without JavaScript, HTTP 200 to our declared bot identity, and a path robots.txt allows).
So no rows were produced, and no `site_*.py` parser was written.

`status.json` → `rows: 0`, `usable_hosts: []`.

## Hosts tried — 186 distinct, robots verdict by the project's own gate

| verdict | count |
|---|---|
| allowed | 40 |
| unreachable (robots 403 / 404 / DNS / SSL / timeout → treated as blocked) | 143 |
| not_retried (already blocked or retired in the 2026-10-01 recon) | 3 |

Every one is in `tried.csv` (deduped) and `tried_raw.csv` (raw append order), with the
exact failure in `why_failed.csv`. The shared `_u26/B_HOSTS_CLAIMED.csv` carries one row
per B1 host (B2's 9 rows are untouched).

## Why each allowed host still failed

| host | what it is | blocker |
|---|---|---|
| `www.megapecas.pt` | PT used-parts shop, server-rendered EUR prices + IVA, ISUZU is a make | its search ignores the OE term: `Search=filtro`, `Search=travao`, both seed OEs and a brand number all return the same 24 cards (`numberOfItems:24` every time); `?Make=ISUZU` returns the same generic list; the make page shows no products. No Isuzu coverage reachable. |
| `www.b-parts.com` | PT (Porto) used-parts marketplace, home page prices server-rendered | `/auto-parts/search?...`, the PT Isuzu make path and every Isuzu product page from its own sitemap return HTTP 403 to our identity (bot check). Sitemap has 5,952 Isuzu PT product URLs; not fetched. |
| `www.pneubeato.com` | tyres + EBC brakes, has an Isuzu D-Max section | no prices in the HTML (JavaScript); the parts pages carry no prices at all |
| `www.autoparts24.eu` | used-parts platform, ships PT in EUR | `/search` is a JS shell: the term appears only in the meta description, 0 prices |
| `www.autocenter.pt` | WooCommerce | `/?s=` returns unrelated products, 0 prices in HTML, no Isuzu |
| `www.winparts.es` / `.nl` | TecDoc catalogue, ships PT in EUR | robots: `Disallow: /search?q=` and `Disallow: /parts/` (es), `Disallow: /zoekresultaten?zoek=` (nl); the robots-allowed `/piezas-de-auto/<pn>` returns 404; product pages carry no price in HTML |
| `www.todoparatucoche.com` | ES, ships PT | robots disallows `/buscar` and `?search_query=` |
| `www.soauto.pt`, `www.feuvert.pt`, `www.roady.pt` | PT chains | soauto blocks `/*?` and `/*search`; feuvert blocks `/catalogsearch/`, `/search/`, `/product*`; roady robots is 0 bytes and the site is a JS chain shell |
| `www.oscaro.pt`, `www.oscaro.es` | operator family | final `Disallow: /` catch-all — disallows crawlers entirely |
| `www.isuzu.pt`, `www.acp.pt`, `www.rasch.pt`, `www.rodasa.com`, `www.autosil.pt`, `www.lojadaspecas.pt`, `www.casadaspecas.pt`, `www.autopartslogistic.com`, `www.ersatzteile-24.com`, `www.motocar.pt`, `www.rodauto.pt`, `www.silvauto.pt`, `www.autolux.pt`, `www.nortecar.pt`, `www.midas.pt` | marketing site, club, industrial castors, battery shop, household-appliance spares, construction, moto dealer, car dealers, workshop chain, login-walled B2B | not a parts shop with prices, or wrong catalogue (white goods), or a login wall with no accessible search |
| `www.parts.pt`, `www.areal.pt`, `www.epecas.pt`, `www.autopecas.online`, `www.pecasauto.com`, `www.pecasoriginais.pt`, `www.pecasauto.com.pt`, `www.agauto.pt` | placeholder or dead | 1-URL sitemaps, 114-byte pages, HTTP 503, or a contact-only site |
| `www.custojusto.pt` | PT classifieds | robots header states that spiders and other automated methods are expressly forbidden; dropped |
| `www.motointegrator.pt` | EU platform PT storefront | robots allowed, home page returns HTTP 403 (bot check) |
| `www.intercars.pt`, `www.intercars.eu`, `katalog.intercars.eu` | major TecDoc distributor | robots.txt 404 / 403 / timeout → treated as blocked |

Blocked by a 403/Turnstile-style bot check (not attempted further): `norauto.pt`, `olx.pt`,
`endado.com`, `skruvat.com`, `b-parts.com` product pages, `autodoc.co.uk`, `oscaro.com`,
`trodo.com`, `alvadi.pt`.

Retired/blocked in the recon, **not retried**: Autodoc (Turnstile), Oscaro (Turnstile),
Mister-Auto, Trodo.

## Numbers

- 123 Isuzu OE numbers (`seed_oe_pns.csv`) and 153 competitor numbers
  (`seed_competitor_pns.csv`) — 0 of each queried against a usable host, because no
  host passed. 123 still empty.
- Pages saved: 71 under `pages/` (home pages, search probes, category pages).
- B2 has since claimed the same hosts I did and found the same wall:
  `truckparts.pt` 6 queries → 6 empty; `turbopecas.pt` search → "Nothing Found";
  `europart.net` product search → 0 prices. My `megapecas` finding is the closest any PT
  shop came to usable: real server-rendered prices, but no Isuzu coverage behind its search.

## Reconciled from the run instructions

- `match_method`: kept schema-valid `crossref`. The brief's `crossref_candidate` /
  `crossref_corroborated` are not in `MATCH_METHODS`, so the grade belongs in the separate
  `crossref_grade` column. `MATCH_METHODS` was not widened.
- Tax basis: Portuguese pages were read for IVA wording, but no allowed page states a price
  basis in readable HTML, so no `vat` value was written. The tax basis is the deciding field
  and it stayed empty rather than assumed.

## Verification

- `python 04_tools\delegation\parsers\price_parsers.py --selftest` → ALL SELFTESTS PASS
  (10 sites) and SELFTEST PASS on the ledger schema. No site parser was added.
- No shared file was modified except `_u26/B_HOSTS_CLAIMED.csv` (append-only; B2's rows intact).
  The ledger parquet was not touched.

## Files (in `_u26/B1/`)

`rows.csv` (header only), `pages/`, `tried.csv`, `tried_raw.csv`, `why_failed.csv`,
`robots/`, `status.json`, and the discovery scripts `_b1_*.py`.
Shared: `_u26/B_HOSTS_CLAIMED.csv`.
