# UK delivery/tax fill result — 2026-10-07

## Verdict

65 shop-URL rows filled honestly from live seller delivery pages (KS + TMC). UK eligible comparable offers stay at **0** after coverage rebuild: a `delivery_included=no` still needs a delivered cost in euros for the evidence rule, and the coverage builder still passes `delivery_cost_eur=None`. Portugal was not touched.

## Attempted

| Bucket | Count | Action |
|---|---:|---|
| Priority 1 with http URL | 8 | All filled (2 KS + 6 TMC oil filters) |
| Priority 2 with http URL | 57 filled of ~59 | KS all filled; TMC under £150 filled; 2 TMC brake-pad listings at £189.73 left blank (at/above free-delivery threshold — do not invent `yes`) |
| Eucon survey / no URL | 12 in UK focus | Skipped — no shop page |
| Live network | OK | KS Delivery Information HTTP 200; TMC `/delivery/` HTTP 200; product PDPs HTTP 200. Partial fails on bare `/delivery` and `/shipping` KS aliases (connection aborted) — CMS path worked |
| Saved HTML cache | Read | U26/U29b `_probe/_u26/A2/pages/cat_79148.html` (TMC) and KS search caches — product HTML itself silent on carriage; seller policy pages used instead |

## Filled

| Source | Rows | delivery_basis | tax_basis | Evidence |
|---|---:|---|---|---|
| KS International | 58 | `no` | `excluded` | Live https://www.ks-international.com/delivery-information — minimum UK mainland carriage **GBP 10.00** for filter kits (named). Listing wrappers `data-label="Excl. VAT"` |
| T & M Commercials | 7 | `no` | *(blank)* | Live https://www.tmcgroup.co.uk/delivery/ — free delivery option on UK Mainland orders **over £150**; otherwise charge at checkout. All filled TMC prices on the sheet are under £150. Product pages do not state ex/inc VAT |

Output (filled rows only):

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UNIVERSE_UK_DELIVERY_TAX_FILLED_20261007.csv`

Companion note:

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\UNIVERSE_UK_DELIVERY_TAX_FILLED_20261007.md`

Live HTML kept under:

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_delivery_live_20261007\`

## Parquet patch (U29-B)

- Worktree: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b`
- File: `01_data\00_derived\price_observations.parquet`
- Backup: `price_observations.parquet.bak_20261007T135452Z_before_uk_delivery_fill`
- Patched by `obs_id`: `delivery_included=no`, `delivery_note=<quote>`; KS `vat` already `excl` (no overwrite needed)
- `ISZE_u29b_pieceB` has no `price_observations.parquet` on disk — patch applied on `ISZE_u29b` only

## Coverage rebuild proof

Command (from U29-B worktree):

```text
python 01_data/91_build/build_market_data_gap_coverage_20261007.py
```

| Metric (UK) | Before | After |
|---|---:|---:|
| eligible_rows / usable_rows | **0** | **0** |
| rows_stating_a_delivery_basis | 0 | **67** |
| DELIVERY_BASIS_NOT_STATED | 79 | 12 |
| DELIVERY_COST_NOT_SUPPLIED | 0 | **67** |
| TAX_BASIS_NOT_STATED | 9 | 9 |
| Portugal eligible | 0 | 0 (untouched) |

Metrics file after rebuild:

`C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_20261007.metrics.json`

(`built_at`: 2026-10-07T13:55:05+00:00)

## Blockers (why eligible stays 0)

1. **DELIVERY_COST_NOT_SUPPLIED** on every filled `no` row — coverage `row_to_evidence_input` hardcodes `delivery_cost_eur=None`. KS states a GBP 10 minimum in the hand sheet `delivery_cost_if_stated`, but that field is not read into the evidence cost today.
2. **TAX_BASIS_NOT_STATED** still on 9 rows (TMC PDPs) — company VAT number is not a price tax basis.
3. **PRODUCT_MATCH_UNRESOLVED** / **PACK_CONTENTS_UNKNOWN** still dominate many priority-2 KS rows.
4. Eucon file-backed survey rows still have no delivery basis (no shop URL).
5. Durability: a full `build_price_ledger.py` rebuild would wipe this parquet-only patch unless an overlay or parser change lands later.

## Not invented

No delivery or tax guessed from silence. No eligible claim without the coverage rebuild above. Portugal skipped.

## Note on 67 vs 65

This fill wrote **65** rows into the filled CSV and patched those obs_ids. After coverage rebuild, UK 
ows_stating_a_delivery_basis is **67**. The extra two are TMC brake-pad listings at GBP 189.73 (75020181e206565e, cc02c0635c49ccbf), which were left out of the filled CSV because they sit on/above the GBP 150 free-delivery threshold. They already carry delivery_included=no with a separate site-policy note that the listed product price does not include delivery. They were not invented by this fill file.


## Follow-up (same evening) — wire KS £10 into evidence

Parent follow-up after [UK delivery scan](agent): the filled CSV already had `delivery_cost_if_stated = GBP 10.00` for 58 KS rows, but coverage hardcoded `delivery_cost_eur=None`.

- Added ledger columns `delivery_cost_amount` / `delivery_cost_currency` on the 58 KS rows (10 GBP).
- Patched `build_market_data_gap_coverage_20261007.py` to convert that cost with the observation FX.
- Rebuilt coverage.

| Metric (UK) | After cost wire |
|---|---:|
| eligible_rows | **2** |
| eligible_pns | **1** (`8982705240` oil filter) |
| billed EUR of that PN (all-market size) | 773,803.72 |
| DELIVERY_COST_NOT_SUPPLIED | 9 (remaining TMC) |
| Still killed mainly by | PRODUCT_MATCH_UNRESOLVED 54, PACK_CONTENTS_UNKNOWN 33 |

Usable rows 2 is still **insufficient** vs the 50-row bar. Eucon stays the main market source. Board banner updated to 2.

## Follow-up hunt — TMC under-£150 charge + VAT; KS re-check (same evening, continued)

### TMC delivery cost under £150

**Not found as a published flat amount.** Live `/delivery/` still only states free option over £150 and that the charge is added at checkout / estimated in the basket. WooCommerce Table Rate Shipping is loaded (`shipping_table_rate` / `woocommerce-table-rate-shipping`), but no numeric mainland under-threshold rate appears in page HTML or policy text.

Basket / cart / checkout: **blocked honestly**. `POST ?add-to-cart=4376` and `GET /basket/`, `/cart/`, `/checkout/` returned **504 Gateway Timeout** or timed out (2026-10-07 evening). Did not invent a rate from a failed checkout. Saved delivery HTML: `01_data/90_INBOX/_uk_delivery_live_20261007/tmc_delivery_rehunt_20261007.html`. Saved PDP: `.../tmc_pdp_8980188580.html`.

### TMC tax basis

**Found on PDP structured data, not as a visible "inc VAT" label next to the £.** Schema.org `Offer` → `UnitPriceSpecification` → `valueAddedTaxIncluded: true` on multiple live PDPs (oil filter + brake pad kit checked). Footer VAT number alone is still not a price basis; this JSON-LD field is. **VAT rate is not stated** on the page (no "20%" tax wording in product/delivery copy).

Ledger: 9 TMC `delivery_included=no` rows now `vat=incl` with note citing that schema field. Coverage after rebuild: UK `TAX_BASIS_NOT_STATED` **0** on those (was 9); they move to **`TAX_RATE_NOT_STATED` 9** + still **`DELIVERY_COST_NOT_SUPPLIED` 9**. Eligible unchanged.

### KS International

**Confirmed live** (not silent): https://www.ks-international.com/delivery-information — UK mainland minimum carriage **£10.00** for filter kits / clutch kit / exhaust muffler / etc. Listing tax already **excl** (`data-label` / ledger `vat=excl`). Cost already wired as `delivery_cost_amount=10` GBP → evidence ~€11.63. No further KS patch this pass.

### Coverage after this hunt

| Metric (UK) | After this hunt |
|---|---:|
| eligible_rows / usable_rows | **2** (unchanged) |
| eligible_pns | **1** (`8982705240`) |
| DELIVERY_COST_NOT_SUPPLIED | **9** (TMC only) |
| TAX_RATE_NOT_STATED | **9** (TMC: incl without stated %) |
| TAX_BASIS_NOT_STATED | **0** (UK focus; was 9) |
| Still mainly killed by | PRODUCT_MATCH_UNRESOLVED 54, PACK_CONTENTS_UNKNOWN 33 |

Metrics: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\market_data_gap_coverage_20261007.metrics.json`

### INTERNAL AIM one-liner

Wired in source `Isuzu Universe/05_AIM_Universe/src/ui/app.js` → `metadataLine`: default note **Market prices: Eucon primary; UK eligible shop offers = 2 (still below the 50-row bar)** (overridable via `D.meta.market_path_note`). Dist HTML not rebuilt this pass — source only until an explicit AIM rebuild.

### Not invented

No TMC under-£150 £. No UK VAT %. No basket rate from a 504. No new shop feeds.
