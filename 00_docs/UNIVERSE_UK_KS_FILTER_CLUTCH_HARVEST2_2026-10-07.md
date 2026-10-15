# UK KS filter/clutch harvest2 — result — 2026-10-07

## Verdict

**Accepted `exact_oem`: 0 of 12.** Next twelve high-euro filter/clutch PNs (never tried in the earlier 8-PN Isuzu or SKU pilots) were searched on KS International by Isuzu PN. Every search returned HTTP 200 with **no product cards**. Nothing appended to the U29b ledger. No £10 wire (nothing to wire). Stopped here as briefed.

Wider UK shop eligible unchanged: **18 offers / 13 PNs**.

## Selection

Source: `01_data/90_INBOX/UNIVERSE_UK_NEXT_HARVEST_PNS_20261007.csv`  
Filter: `no_uk_ledger_row` + filter/clutch families only (`fuel` / `air` / `blower` / `oil` / `clutch_disc` / `clutch_pressure_plate`), sorted by all-market billed euro descending.

**Excluded closed walls (do not re-search):**  
`5876150170`, `1876100934`, `1876101132`, `8975488420`, `8975425390`, `8982120690`, `8975056801`, `8978279610`.

## Method

1. Search `https://www.ks-international.com/catalogsearch/result/?q=<PN>` for each of the twelve.
2. Parse saved HTML with `site_ks.parse`.
3. Accept only `exact_oem` when the **searched** Isuzu PN is printed on the product card.
4. On accept + filter/clutch class: VAT excl + £10 mainland cost — **not applied** (zero accepts).
5. Rebuild coverage `--also-uk-exact` after the run.

## Per-PN outcome

| # | Part number | Family | All-market billed € | KS search | Cards | Verdict |
|---|---|---|---:|---|---:|---|
| 1 | 8983476230 | clutch_disc | 134,145 | HTTP 200 | 0 | rejected — no product cards |
| 2 | 5876150180 | blower_filter | 131,844 | HTTP 200 | 0 | rejected — no product cards |
| 3 | 5876150021 | air_filter | 123,517 | HTTP 200 | 0 | rejected — no product cards |
| 4 | 8981475700 | fuel_filter | 118,278 | HTTP 200 | 0 | rejected — no product cards |
| 5 | 8975435900 | clutch_disc | 86,237 | HTTP 200 | 0 | rejected — no product cards |
| 6 | 5876150000 | oil_filter | 78,626 | HTTP 200 | 0 | rejected — no product cards |
| 7 | 8981398300 | fuel_filter | 77,435 | HTTP 200 | 0 | rejected — no product cards |
| 8 | 8981402660 | air_filter | 73,474 | HTTP 200 | 0 | rejected — no product cards |
| 9 | 5876150521 | air_filter | 72,127 | HTTP 200 | 0 | rejected — no product cards |
| 10 | 1876101141 | air_filter | 72,031 | HTTP 200 | 0 | rejected — no product cards |
| 11 | 5876101570 | fuel_filter | 68,991 | HTTP 200 | 0 | rejected — no product cards |
| 12 | 8983989321 | clutch_pressure_plate | 65,415 | HTTP 200 | 0 | rejected — no product cards |

**Counts:** accepted exact_oem **0**; rejected **12** (all `rejected_no_cards`). No relevance-only cards to judge as `category_only`.

## Ledger / coverage

| Step | Result |
|---|---|
| Staging CSV for accepted rows | Header only (0 data rows) |
| Append to u29b `price_observations.parquet` | **Not run** (nothing to append) |
| Wider rebuild `--also-uk-exact` | Re-run; eligible unchanged |

| Metric | Before | After | Delta |
|---|---:|---:|---:|
| Wider UK eligible offers | **18** | **18** | **0** |
| Wider UK eligible PNs | **13** | **13** | **0** |

## What this means

Isuzu-PN search on KS for the next twelve filter/clutch numbers behaves like the first eight: live empty search pages, not a fetch failure. Combined with the closed 8-PN walls, **20** distinct high-euro filter/clutch/pad Isuzu-PN searches on KS have returned **0** OE-on-card accepts. Do not invent SKUs or carriage. Do not widen the same Isuzu-PN method further without a different query strategy.

## Paths

| Artefact | Path |
|---|---|
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_FILTER_CLUTCH_HARVEST2_2026-10-07.md` |
| Runner | `C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_uk_ks_filter_clutch_harvest2_20261007.py` |
| PN queue + HTML + parse/reject/staging | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_filter_clutch_harvest2_20261007\` |
| Eligible before/after | `...\harvest2_eligible_before_after_20261007.json` |
| Wider metrics | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json` |
| U29b ledger (unchanged) | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet` |
| Prior Isuzu-PN pilot (0/8) | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_PILOT_8PN_RESULT_2026-10-07.md` |
| Prior SKU pilot (0/8) | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_SKU_PILOT_RESULT_2026-10-07.md` |

## Honesty

- No invented OE / £ / SKU.
- Closed 8 PNs not re-searched.
- No `category_only` written as ledger upgrades.
- No delivery £10 applied.
- No board / INTERNAL rebuild.
- Stopped at twelve after 0 accepts.
