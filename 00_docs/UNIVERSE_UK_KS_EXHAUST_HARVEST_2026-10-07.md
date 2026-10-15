# UK KS exhaust-class harvest — result — 2026-10-07

## Verdict

**Accepted `exact_oem`: 0 of 15.** Fifteen Isuzu muffler / silencer / exhaust-pipe numbers (not already wider-eligible, excluding `8983682091`) were searched live on KS International. Fourteen returned empty product grids. One (`8983656821`, exhaust silencer) returned a genuine silencer card with VAT excl **£215**, but the Isuzu PN is **not** printed on the card — `category_only`, rejected. Nothing appended to the U29b ledger. No £10 delivery wire. Wider UK shop eligible stays **18 offers / 13 PNs**.

Stopped here — did not invent OE, did not widen to body/brake, did not re-run the earlier failed filter/clutch 8-PN or competitor-SKU methods.

## Method

1. Shortlist from EPC / billed proxies (`revision_book_b_review_pack`, unpriced one-side, live-order unclassified, eq_hit, EPC heavy) matching muffler / silencer / `PIPE; EXH` / tail pipe. Cap **15**. Exclude already-eligible PNs and `8983682091`. Prefer silencer wording, then billed euro proxy.
2. Search `https://www.ks-international.com/catalogsearch/result/?q=<PN>`.
3. Parse with `site_ks.parse`. Accept only `exact_oem` (Isuzu PN on the product card). Reject `category_only`.
4. Wire £10 + `delivery_included=no` only for accepted exhaust-class rows — **not run** (zero accepts).
5. Rebuild coverage from U29b: `python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact`.

## Shortlist (15)

| # | Part number | EPC / desc | Euro proxy (L12M / billed where known) |
|---|---|---|---:|
| 1 | 8983656821 | EXHAUST SILENCER ASSEMBLY (prior KS relevance) | — |
| 2 | 7551987570 | PIPE; EXH,BRK VLV TO SILENCER | 9039.48 |
| 3 | 7551987560 | PIPE; EXH,BRK VLV TO SILENCER | 447.06 |
| 4 | 8975042231 | PIPE; EXH,BRK VLV TO SILENCER | 222.38 |
| 5 | 8982925490 | PIPE; EXH,BRK VLV TO SILENCER | 98.83 |
| 6 | 8978857370 | PIPE; EXH,SILENCER | 60.51 |
| 7 | 1221408800 | SILENCER ASM; EXH | — |
| 8 | 7551987600 | PIPE; EXH,SILENCER | — |
| 9 | 7552094370 | PIPE; EXH,SILENCER | — |
| 10 | 7552197200 | PIPE; EXH,BRK VLV TO SILENCER | — |
| 11 | 7552752940 | PIPE; EXH,BRK VLV TO SILENCER | — |
| 12 | 8976526890 | PIPE; EXH,SILENCER | — |
| 13 | 8976657111 | PIPE; EXH,BRK VLV TO SILENCER | — |
| 14 | 8978249232 | PIPE; EXH,BRK VLV TO SILENCER | — |
| 15 | 8978334772 | PIPE; EXH,BRK VLV TO SILENCER | — |

## Per-PN outcome

| # | Part number | KS search | Cards | Verdict |
|---|---|---|---:|---|
| 1 | 8983656821 | HTTP 200 | 1 | rejected — `category_only` (sku `0707741G`, excl £215; no Isuzu PN on card) |
| 2 | 7551987570 | HTTP 200 | 0 | rejected — no product cards |
| 3 | 7551987560 | HTTP 200 | 0 | rejected — no product cards |
| 4 | 8975042231 | HTTP 200 | 0 | rejected — no product cards |
| 5 | 8982925490 | HTTP 200 | 0 | rejected — no product cards |
| 6 | 8978857370 | HTTP 200 | 0 | rejected — no product cards |
| 7 | 1221408800 | HTTP 200 | 0 | rejected — no product cards |
| 8 | 7551987600 | HTTP 200 | 0 | rejected — no product cards |
| 9 | 7552094370 | HTTP 200 | 0 | rejected — no product cards |
| 10 | 7552197200 | HTTP 200 | 0 | rejected — no product cards |
| 11 | 7552752940 | HTTP 200 | 0 | rejected — no product cards |
| 12 | 8976526890 | HTTP 200 | 0 | rejected — no product cards |
| 13 | 8976657111 | HTTP 200 | 0 | rejected — no product cards |
| 14 | 8978249232 | HTTP 200 | 0 | rejected — no product cards |
| 15 | 8978334772 | HTTP 200 | 0 | rejected — no product cards |

**Counts:** accepted exact_oem **0**; rejected **15** (14 `no_product_cards`, 1 `category_only`).

## Ledger / coverage

| Step | Result |
|---|---|
| Staging CSV for accepted rows | Header only (0 data rows) |
| Append / £10 wire on U29b parquet | **Not run** (nothing to append; no backup) |
| Wider rebuild `--also-uk-exact` (U29b) | Eligible unchanged |

| Metric | Before | After |
|---|---:|---:|
| Wider UK eligible offers | **18** | **18** |
| Wider UK eligible PNs | **13** | **13** |
| New exhaust eligible delta | — | **0 offers / 0 PNs** |

Wider metrics (U29b):  
`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`

## Paths

| Artefact | Path |
|---|---|
| This note | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UNIVERSE_UK_KS_EXHAUST_HARVEST_2026-10-07.md` |
| Shortlist CSV | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_exhaust_harvest_20261007\shortlist_exhaust_20261007.csv` |
| Saved search HTML (15) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_exhaust_harvest_20261007\` |
| Parse summary | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_exhaust_harvest_20261007\harvest_parse_summary.json` |
| Reject log | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_exhaust_harvest_20261007\harvest_rejects_20261007.csv` |
| Empty staging | `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_exhaust_harvest_20261007\staging_exact_oem_accepted_exhaust_20261007.csv` |
| U29b ledger (unchanged) | `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet` |

## Honesty

- No invented OE / no `category_only` → `exact_oem`.
- No £10 on non-accepted rows; silencer card left unwired because OE is not on the card.
- No body / brake widen after empty harvest.
- Board / INTERNAL not rebuilt (owned elsewhere).
