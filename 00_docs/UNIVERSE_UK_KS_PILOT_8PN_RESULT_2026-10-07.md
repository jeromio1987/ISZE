# UK KS International 8-PN pilot — result — 2026-10-07

## Verdict

**Accepted `exact_oem`: 0 of 8.** Every pilot PN returned a live KS search page with **no product cards** (“Your search returned no results”). No PDPs to open, no OE-on-card to judge, nothing appended to the U29b ledger. Stopped here — did not widen to the remaining 32.

Wider UK shop eligible is unchanged: **17 offers / 12 PNs** before and after.

## Method (executed)

1. Search `https://www.ks-international.com/catalogsearch/result/?q=<PN>` for each of the eight PNs (urllib fetch + browser spot-check on `5876150170` and `8982120690`).
2. Parse saved HTML with `site_ks.parse` (OE must appear on the product card for `exact_oem`).
3. Accept only `exact_oem`; do not write `category_only` upgrades.
4. Control fetch of known ledger PN `8974995480` still returns a product card (parser: `category_only` today) — so empty results are not a fetch failure.

## Per-PN outcome

| # | Part number | Family | KS search | Cards | Verdict |
|---|---|---|---|---:|---|
| 1 | 5876150170 | fuel_filter | HTTP 200 | 0 | rejected — no results |
| 2 | 1876100934 | fuel_filter | HTTP 200 | 0 | rejected — no results |
| 3 | 1876101132 | air_filter | HTTP 200 | 0 | rejected — no results |
| 4 | 8975488420 | blower_filter | HTTP 200 | 0 | rejected — no results |
| 5 | 8975425390 | fuel_filter | HTTP 200 | 0 | rejected — no results |
| 6 | 8982120690 | clutch_disc | HTTP 200 | 0 | rejected — no results |
| 7 | 8975056801 | brake_pad | HTTP 200 | 0 | rejected — no results |
| 8 | 8978279610 | brake_pad | HTTP 200 | 0 | rejected — no results |

**Counts:** accepted exact_oem **0**; rejected **8** (all `no_product_cards`). No relevance-only cards to reject as `category_only` — the searches were empty.

## Ledger / coverage

| Step | Result |
|---|---|
| Staging CSV for accepted rows | Header only (0 data rows) |
| Append to u29b `price_observations.parquet` | **Not run** (nothing to append; no backup needed) |
| Wider rebuild `--also-uk-exact` | Re-run after pilot; eligible unchanged |

| Metric | Before | After |
|---|---:|---:|
| Wider UK eligible offers | **17** | **17** |
| Wider UK eligible PNs | **12** | **12** |

Baseline / after metrics file: `01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json` (ledger still U29b).

## What this means next

Isuzu-PN search on KS for these eight high-euro filter/clutch/pad numbers does not surface catalogue cards. The harvest brief already warned the hit rate might be empty; that is what happened. Do **not** bulk-run the remaining 32 with the same query method. Next options (outside this pilot): competitor-number search with OE printed on the card, or another host (TMC only if a published under-£150 £ appears — do not invent).

## Paths

| Artefact | Path |
|---|---|
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_PILOT_8PN_RESULT_2026-10-07.md` |
| Saved search HTML (8) + control | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pilot_20261007\` |
| Parse summary | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pilot_20261007\pilot_parse_summary.json` |
| Reject log | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pilot_20261007\pilot_rejects_20261007.csv` |
| Empty staging (accepted) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pilot_20261007\staging_exact_oem_accepted_20261007.csv` |
| Wider metrics | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json` |
| U29b ledger (unchanged) | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet` |

## Honesty

- No invented OE.
- No invented TMC £.
- No `category_only` written as ledger upgrades.
- No delivery £10 applied (no accepted rows).
- Pilot stopped at eight PNs.
