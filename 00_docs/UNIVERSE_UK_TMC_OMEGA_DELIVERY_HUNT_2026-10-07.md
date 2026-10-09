# UK TMC / Omega delivery hunt — 2026-10-07

## Verdict

**Omega:** live WooCommerce Store API cart quote states **UK Free Economy Delivery = GBP 0.00** (and Express **GBP 7.95**) for both ledger SKUs on GB mainland. Patched 10 `exact_oem` rows → `delivery_included=yes` + VAT incl **20%** from Terms of Business. Wider UK eligible **18 → 28** offers (**13 → 14** PNs).

**T&M (tmcgroup):** still **no inventable under-£150 mainland £**. Policy page only names free over £150; table-rate JS has no rates; cart / WC shipping REST still **504**. Not patched.

## Ledger inspect (U29b `price_observations.parquet`)

| Host | exact_oem rows | PNs | Sample URLs |
|---|---:|---:|---|
| www.tmcgroup.co.uk | 55 | 55 | e.g. `/product/absorber-asm-shock-frt/`, oil-filter / brake-pad PDPs |
| omegaspareparts.com | 10 | 2 (`8970622940`, `8980806782`) | PDP `0011765k-…`, PDP `8980806782-…`, search `?s=<PN>&post_type=product` |

Before this hunt: TMC had 9 rows already `delivery_included=no` (under £150) with **blank cost**; Omega all blank on delivery.

## What was fetched

Live HTML / JSON under:

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_tmc_omega_delivery_hunt_20261007\`

### T&M Commercials

| Endpoint | Result |
|---|---|
| `/delivery/` | **200** — free UK Mainland option on qualifying orders **over £150**; otherwise “estimated shipping rates” / charge at checkout. Only money figure on page: **£150** threshold |
| `/shipping/`, terms, FAQ, help, `sitemap.xml`, `wp-sitemap.xml` | **504** |
| WC v3 shipping zones/methods, Store cart / shipping-rates | **504** |
| HTML `/sitemap/` | **200** — links to `/delivery/`, `/basket/` only for this topic |
| Table-rate frontend JS `woocommerce-table-rate-shipping/.../frontend-checkout.min.js` | **200** — abort-text UI helper only; **no rate table / no £** |
| Theme `woocommerce.js`, `admin-ajax` fragments | **200** — empty basket fragment; no £ |
| `?wc-ajax=get_refreshed_fragments` | **504** |

**Wall:** under-£150 carriage is checkout-only and the checkout/cart path stays 504. Do not invent a flat £.

### Omega Spare Parts

| Endpoint | Result |
|---|---|
| Home, FAQ, returns, about, `/tob/` (Terms of Business), country shipping list post | **200** |
| Guessed `/delivery/`, `/shipping/`, … | connection closed |
| WC v3 shipping zones/methods | **401** |
| Empty Store cart GET | **200** — `shipping_rates=[]` |
| **Store API** `POST .../cart/add-item` + `update-customer` (GB `SW1A 1AA`) | **200** — rates returned |

Country shipping list = ship-to yes/no only (no £). FAQ: “Postage costs are clearly displayed at checkout.” TOB: “Standard carriage applies to the UK Mainland only” **without a £ amount**; “All advertised prices include VAT at **20%**”. The £50 on TOB is **insurance**, not carriage.

#### Store API quote (clear amount)

| Product id | PN / SKU | UK Free Economy | UK Express 24hr |
|---|---|---:|---:|
| 85383 | 8970622940 / 0011765K | **GBP 0.00** | GBP 7.95 |
| 92596 | 8980806782 axle | **GBP 0.00** | GBP 7.95 |

Saved: `omega_cart_after.html`, `omega_cart_axle_after.html`. Delivered basis used for the ledger: **free economy** → `delivery_included=yes` (no cost column). Express £7.95 recorded in the note only.

## Patch applied (Omega only)

- Worktree ledger: `C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b\01_data\00_derived\price_observations.parquet`
- Backup: `price_observations.parquet.bak_20261007T160502Z_before_omega_delivery`
- 10 rows: `delivery_included=yes`, `vat=incl`, `vat_rate=20`, note cites Store API + TOB
- Coverage builder: pass ledger `vat_rate` into evidence when tax is included (u29b + main `build_market_data_gap_coverage_20261007.py`)
- Receipt: `01_data/90_INBOX/_uk_tmc_omega_delivery_hunt_20261007/_omega_patch_receipt.json`

TMC: **not patched**.

## Wider coverage rebuild

```text
python 01_data/91_build/build_market_data_gap_coverage_20261007.py --also-uk-exact
```

(from U29b worktree)

| Metric (UK wider exact_oem) | Before | After | Delta |
|---|---:|---:|---:|
| eligible_rows | **18** | **28** | **+10** |
| eligible_pns | **13** | **14** | **+1** (`8980806782`; `8970622940` already had KS) |
| focus eligible (oil/brake) | 4 | 4 | 0 |

Metrics/CSV copied to main clone:

- `01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.metrics.json`
- `01_data/00_derived/market_data_gap_coverage_uk_wider_exact_20261007.csv`

## Not invented

- No TMC under-£150 £ from silence or 504.
- Omega free £0 and Express £7.95 taken only from Store API response bodies on disk.
- VAT 20% only from live TOB text (+ cart tax lines matching 20%).

## Related earlier note

A shorter endpoint-only pass lived in `UNIVERSE_UK_TMC_OMEGA_ENDPOINT_FETCH_2026-10-07.md` (before Store API add-item). This hunt supersedes it for Omega; TMC wall unchanged.
