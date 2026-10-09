# UK KS eligible recipe — how the ledger rows got in — 2026-10-07

## Verdict

The UK shop-eligible KS rows did **not** land via an OE-on-card harvest. They came from the weekly Isuzu-PN Magento search (`ks_scraper.py` → `ks_results.csv` → ledger loaders `ks_am` / `ks_gen`), which **hardcodes** `match_method = exact_oem` and leaves `competitor_pn` empty. Delivery £10 was wired later from the live KS delivery page for filter / clutch / exhaust (plus an earlier focus pad fill). Live ledger count today is **18 offers / 13 PNs** (the wider metrics JSON still says 17 / 12 — stale). Isuzu-PN search for the new 8-PN pilot returned 0/8 because those PNs were already `no_results` in the same 2026-10-05 scrape file. A repeatable harvest that can grow eligible **without** relying on Isuzu-PN search must start from **KS SKU or competitor number**, then accept `exact_oem` only when the Isuzu PN is printed on the card (the `site_ks` bar).

## Columns used (ledger → eligibility)

Ledger file:

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet`

| Column | What the 18 eligible rows carry |
|---|---|
| `part_no` | Isuzu PN (10-digit) — the scrape query key |
| `match_method` | `exact_oem` (set by loader, not proven on card) |
| `competitor_pn` | **always null** for `ks_am` / `ks_gen` |
| `competitor_brand` | null |
| `loader` | `ks_am` (aftermarket min) and/or `ks_gen` (genuine/grey min) |
| `source` | `ks-international.com` |
| `source_url` | `https://www.ks-international.com/catalogsearch/result/?q=<part_no>` |
| `country` | `UK` |
| `observed_at` | **2026-10-05** (date part of `Scraped_At` in `ks_results.csv`) |
| `vintage` | `KS 2026-10-05` |
| `price` / `currency` | GBP ex-VAT min for that AM or GEN bucket |
| `vat` | `excl` (from `.price-excluding-tax` on the search card) |
| `price_type` | `aftermarket_trade` (`ks_am`) or `genuine_grey` (`ks_gen`) |
| `delivery_included` | `no` (patched after scrape) |
| `delivery_cost_amount` / `delivery_cost_currency` | `10` / `GBP` (patched) |
| `delivery_note` | cites live KS delivery-information quote |

Wider eligibility also needs the coverage builder’s evidence rules (delivery basis + tax basis). Wider report:

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.csv`

## Sample URLs (from the 18)

All use the same pattern — Isuzu PN in `q=`, never a KS SKU:

| part_no | loader | price | source_url |
|---|---|---:|---|
| 8974995480 | ks_gen | £30 | https://www.ks-international.com/catalogsearch/result/?q=8974995480 |
| 8981596930 | ks_am / ks_gen | £5 / £25 | https://www.ks-international.com/catalogsearch/result/?q=8981596930 |
| 8982705240 | ks_am / ks_gen | £10 / £15 | https://www.ks-international.com/catalogsearch/result/?q=8982705240 |
| 8975546610 | ks_am / ks_gen | £15 / £125 | https://www.ks-international.com/catalogsearch/result/?q=8975546610 |
| 8982831940 | ks_gen | £300 | https://www.ks-international.com/catalogsearch/result/?q=8982831940 |
| 8983682091 | ks_gen | £1675 | https://www.ks-international.com/catalogsearch/result/?q=8983682091 |
| 8981394280 | ks_am | £4 | https://www.ks-international.com/catalogsearch/result/?q=8981394280 |

Control fact from `site_ks.py`: searching `8974995480` returns one card whose SKU is `0707723G` and whose card text does **not** contain the Isuzu PN. Strict parse → `category_only`. The ledger row for that PN is still `exact_oem` because `load_ks()` hardcodes it.

## Loader names and pipeline

```
Isuzu PN list (top billed / PN file)
    → 04_tools/autodoc_scraper/ks_scraper.py
         GET catalogsearch/result/?q={PN}
         parse cards → AM vs GEN (GENUINE badge / name)
         append 04_tools/autodoc_scraper/ks_results.csv
    → 04_tools/price_ledger/build_price_ledger.py :: load_ks()
         Status==ok + price > £2.34 placeholder
         emits loader ks_am and/or ks_gen, match_method=exact_oem, competitor_pn=None
    → price_observations.parquet
    → later: 01_data/91_build/_uk_wider_eligible_scan_20261007.py
         £10 mainland wire when family/desc matches filter|clutch|exhaust
         (focus brake pads already carried £10 from an earlier fill)
    → build_market_data_gap_coverage_20261007.py --also-uk-exact
```

Related (different job — does **not** grow wider `exact_oem` eligible):

| Loader / tool | Query key | match_method | Notes |
|---|---|---|---|
| `ks` (plain) | mixed / hand | varies | 3 UK exact rows; bearing kit has delivery_note only |
| `ks_crossref` | **competitor PN** via `run_crossref_queries.py` | `crossref` | Accepts card only if searched competitor number is on the card; U26 A1 used this path |
| `site_ks.parse` | page HTML | `exact_oem` only if Isuzu PN on card, else `category_only` | Honest bar for new harvest |

Was `competitor_pn` the search key for the 18? **No.** The search key was the Isuzu `part_no`. `competitor_pn` is null on every `ks_am` / `ks_gen` row.

## observed_at

All 18 eligible KS rows: **2026-10-05** (from `ks_results.csv` `Scraped_At`, e.g. `2026-10-05 07:00:50` … `07:19:02`). Three older plain-`ks` exact rows sit on 2026-10-01 and are not in the eligible 18.

## Why the 8-PN Isuzu search pilot returned 0/8

Those eight PNs are already in `ks_results.csv` from the same 2026-10-05 run with `Status=no_results`. Re-fetching `?q=<Isuzu PN>` cannot invent catalogue cards KS does not index under that OE string. Do not widen the remaining 32 with the same query method.

## Repeatable harvest recipe (NOT Isuzu-PN search)

Goal: new `exact_oem` rows that can take VAT excl + £10 (filter/clutch/exhaust) without pretending OE is on the card.

### A. Seed (no Isuzu PN as the HTTP `q`)

1. **KS SKU** from a known card (example: control air-filter card SKU `0707723G` for relevance hit on 8974995480), from `KS_AM_SKUs` / `KS_GEN_SKUs` when the CSV fills them, or from PDP/category HTML.
2. **Competitor / IAM number** from graded Eucon / AIM edges (same seed style as U26 A1 `run_crossref_queries.py --seed-csv`).
3. **Category / sitemap browse** — U26 already has Magento HTML under:

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\90_INBOX\scrape_targets\_probe\cache\www.ks-international.com`

(~897 files) plus `sitemap_cache\www.ks-international.com`. Re-parse cache before new fetches where possible.

### B. Query

```
https://www.ks-international.com/catalogsearch/result/?q=<KS_SKU_or_competitor_pn>
```

Optional: open each product-item link (PDP) when the search card is thin.

### C. Accept gate (stricter than `load_ks`)

Use `04_tools/delegation/parsers/site_ks.py` (or equivalent on the PDP):

- Emit `exact_oem` **only if** the target Isuzu PN appears in the product card / OE field / title (not merely in the search box or page title).
- Otherwise `category_only` or reject — **do not** hardcode `exact_oem` the way `load_ks()` does.
- Keep `competitor_pn` = the KS SKU or IAM number actually searched when that is what was on the card.
- Price = ex-VAT GBP; `vat=excl` when the Excl. VAT label is present.

### D. Delivery / tax wire (no invent)

Live page https://www.ks-international.com/delivery-information (fetched 2026-10-07):

> minimum charge … £10.00 e.g. Filter kits, clutch kit, exhaust muffler, tail pipe etc  
> additional charge for most boxed body panels …

Apply `delivery_included=no`, `delivery_cost_amount=10`, `GBP` **only** for filter / clutch / exhaust (incl. EPC `PIPE; EXH`). Do **not** apply £10 to body panels, grilles, or brake rotors. Do not invent TMC under-£150 £.

### E. Land in ledger

Append rows with loaders that preserve provenance (prefer a SKU/OE-gated loader or staged CSV → ledger append). Rebuild:

```
python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact
```

against the U29b parquet (or the ledger you just wrote).

### F. What not to do

- Do not re-run Isuzu-PN search on PNs already `no_results` in `ks_results.csv`.
- Do not treat `ks_crossref` (`match_method=crossref`) as wider `exact_oem` eligible.
- Do not upgrade `category_only` → `exact_oem` without OE on the card.
- Do not copy `load_ks()`’s hardcode for new harvests if the programme bar is OE-on-card.

## How to reproduce for new PNs (checklist)

1. Build a seed list of **KS SKUs or competitor numbers** linked to the Isuzu PN (edges, prior cards, category HTML) — not a bare Isuzu PN list.
2. Fetch `catalogsearch/result/?q=<seed>` (reuse U26 cache when the URL hash already exists).
3. Parse with OE-on-card gate; stage only `exact_oem`.
4. If family is filter/clutch/exhaust, wire £10 + note from the delivery page.
5. Append → coverage `--also-uk-exact` → confirm eligible count moved.

Script sketches already on disk (SKU path started, Isuzu path failed):

- `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_sku_pilot_fetch_20261007.py`
- `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_pilot_parse_20261007.py`
- `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\04_tools\delegation\parsers\run_crossref_queries.py`

## Next 20 without new scrape — honest count

**Zero** further UK KS `exact_oem` rows can grow eligible with only a small honest wire.

- Already delivery+cost on ledger: **18** (all filter / clutch / exhaust / wired focus pads).
- Remaining KS `exact_oem` with `vat=excl` and only `DELIVERY_BASIS_NOT_STATED`: **66** rows / many PNs.
- Honest £10 policy matches left in that pile: **0** (exhaust pipe already wired; no more filter/clutch/exhaust text).
- Body / grille / panel and brake rotor rows are explicitly outside the £10 examples.
- Sensors, turbos, DPD, injectors, etc. have **no** published flat mainland £ on that page.

So growth to the 50-row bar needs **new OE-on-card pages** (SKU/competitor/category recipe above) or a **published** delivery £ for other classes — not another policy patch on the current 66.

### Closest 20 KS `exact_oem` PNs (already in ledger; only delivery blocks them)

These are the highest listed GBP among non-eligible KS `exact_oem` (one row per PN). They do **not** qualify for the £10 filter/clutch/exhaust wire. Listed so the wall is concrete.

| # | part_no | loader (sample) | £ | description | why not wireable without new evidence |
|---|---|---|---:|---|---|
| 1 | 8982278993 | ks_gen | 2750 | DPD ASM | no published flat £ |
| 2 | 8981776324 | ks_gen | 2150 | DPD ASM | no published flat £ |
| 3 | 8974985741 | ks_gen | 1650 | TURBOCHARGER ASM | no published flat £ |
| 4 | 8975074241 | ks_am | 1250 | TURBOCHARGER ASM | no published flat £ |
| 5 | 8981506872 | ks_gen | 750 | TURBOCHARGER ASM | no published flat £ |
| 6 | 8983300950 | ks_gen | 545 | SENSOR; PM | no published flat £ |
| 7 | 8983724250 | ks_gen | 395 | FLYWHEEL | no published flat £ |
| 8 | 8983852180 | ks_gen | 395 | GENERATOR ASM | no published flat £ |
| 9 | 8983929650 | ks_gen | 370 | SHAFT ASM; FRT DRIVE | no published flat £ |
| 10 | 8982074350 | ks_am | 350 | NOZZLE ASM; INJ | no published flat £ |
| 11 | 8983320160 | ks_gen | 350 | VALVE; EGR | no published flat £ |
| 12 | 8981647861 | ks_gen | 350 | VALVE; EGR | no published flat £ |
| 13 | 8981226950 | ks_gen | 340 | PANEL ASM; FRT | body panel — page says extra charge, not £10 |
| 14 | 8978808250 | ks_gen | 325 | SENSOR; PM | no published flat £ |
| 15 | 8982201270 | ks_gen | 325 | SENSOR; SPEED | no published flat £ |
| 16 | 8983320591 | ks_gen | 310 | NOZZLE ASM; INJ | no published flat £ |
| 17 | 8984890190 | ks_gen | 300 | NOZZLE ASM; INJ | no published flat £ |
| 18 | 8983314120 | ks_am | 295 | SENSOR; PRESSURE,DPD | no published flat £ |
| 19 | 8974814492 | ks_gen | 275 | ACTUATOR; AXLE | no published flat £ |
| 20 | 8982410681 | ks_gen | 275 | GRILLE; RAD | body — not £10 |

(Sibling `ks_am`/`ks_gen` rows on the same PNs bring the non-eligible KS exact pile to 66+; fixing one PN’s delivery would unlock both loaders when both exist.)

## Count note (17 vs 18)

| Source | Eligible offers | Eligible PNs |
|---|---:|---:|
| Stale `market_data_gap_coverage_uk_wider_exact_20261007.metrics.json` | 17 | 12 |
| Live wider CSV + U29b parquet after exhaust wire | **18** | **13** |

The extra row is `8983682091` / `f9cefffef16de794` (`PIPE; EXH`, ks_gen £1675) with the same £10 policy. Rebuild the metrics JSON when you next run `--also-uk-exact`.

## Paths

| Artefact | Path |
|---|---|
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_ELIGIBLE_RECIPE_2026-10-07.md` |
| U29b ledger | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet` |
| Scrape CSV | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\04_tools\autodoc_scraper\ks_results.csv` |
| Scraper | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\04_tools\autodoc_scraper\ks_scraper.py` |
| Loader | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\04_tools\price_ledger\build_price_ledger.py` (`load_ks`) |
| Strict parser | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\04_tools\delegation\parsers\site_ks.py` |
| £10 policy patch | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\91_build\_uk_wider_eligible_scan_20261007.py` |
| U26 KS HTML cache | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u26\01_data\90_INBOX\scrape_targets\_probe\cache\www.ks-international.com` |
| 8-PN Isuzu pilot result | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_PILOT_8PN_RESULT_2026-10-07.md` |
