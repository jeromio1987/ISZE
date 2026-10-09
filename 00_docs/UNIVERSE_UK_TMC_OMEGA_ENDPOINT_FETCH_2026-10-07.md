# TMC / Omega delivery endpoint fetch — 2026-10-07

## Verdict

Re-fetched delivery-related URLs for T&M Commercials and Omega. **No new inventable under-£150 flat carriage** appeared. Eligible UK shop counts stay on the KS path only (wider **18** / focus **4** at time of write).

## Fetch folder

`C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_tmc_omega_delivery_hunt_20261007\`  
Index: `_fetch_index.json`

## What returned

| Host | Hit | Result |
|---|---|---|
| TMC `/delivery/` | **200** | Same policy as before: free UK Mainland option on qualifying orders **over £150**; otherwise “estimated shipping rates” / charge at checkout. No under-£150 £ amount. |
| TMC shipping / terms / FAQ / WC shipping JSON / cart shipping-rates | **504** | Gateway timeout — no usable £ |
| TMC HTML sitemap / robots | **200** | No flat £ found in this pass |
| Omega home / FAQ / sitemaps / robots / empty cart JSON | **200** | FAQ: “Postage costs are clearly displayed at checkout.” No flat mainland £. Empty cart: `total_shipping=null`, `shipping_rates=[]` |
| Omega guessed delivery/shipping URLs | connection closed | No page |
| Omega WC v3 shipping zones/methods | **401** | Auth required — not a public quote |

## Do not invent

- Do not wire a TMC or Omega `delivery_cost_amount` from this fetch.
- Free ≥ £150 on TMC remains a threshold, not a cost for the under-£150 exact_oem rows already on the ledger.

## Batch 2 (table-rate JS + Omega pages)

Also fetched into the same folder:

| URL class | Result |
|---|---|
| TMC WooCommerce table-rate frontend JS | **200** — UI helper only; **no rate table / no £ amounts** |
| TMC theme `woocommerce.js` | **200** — no £ / shipping amounts |
| TMC WC store/cart JSON | **504** again |
| Omega WP pages API, shipping/delivery search, returns, about, checkout, sample PDP | **200** — returns/FAQ-style text still points to checkout; PDP shows product £ only, not carriage |
| Omega WC v3 shipping methods | **401** |

Still **no** inventable under-£150 flat mainland carriage.

## Next (only if a live £ appears)

Basket/checkout quote with a printed £ on a specific SKU, or a newly published policy page with a fixed mainland amount. Until then TMC/Omega stay non-eligible for the shop bar.
