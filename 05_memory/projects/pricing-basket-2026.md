# ISZE pricing basket — confirmed figures (2026)

**Use:** `isze-pricing-basket-monitor` and GPT pricing sessions cite this file — do not embed figures in unattended prompts.

**Last verified:** 2026-06-29
**Source:** Jerome sign-off post FY2026 basket modelling

**Canonical price file:** `01_data/01_Pricing/IE40 Price list as of 13.03.2026 PR00_3_level_classified_GPT.xlsx` (164,381 rows, taxonomy-classified) — these are the active parts.

> **Read the dates correctly.** The price list is dated **13-03-2026** and has **not been revised since**
> (file mtime 2026-04-15). `2026-07-14` is the date its *canonical status was re-confirmed* — it is a
> confirmation date, **not** a file revision. Staleness reviews have repeatedly misread this as
> "the price file changed on 2026-07-14" and raised a phantom re-run action against
> [[competitiveness]] and this file. There is no such re-run pending. Do **not** use `01_data/01_Pricing/Price file 2026_full.xlsx` (674,119 rows, mod 2026-06-16) for pricing/basket figures — Jerome confirmed it is not the source to use. File left in place, not deleted; just not authoritative for pricing.

| Item | Value |
|------|-------|
| Basket impact 2025→2026 | +€298,911 / +5.3% |
| FX rate (FY2026) | 163.7 JPY/EUR (Oct 2025) |
| Class 0 PNs | 10 (all Source J) |
| Source J discount | 0.62 |
| Source T discount | 0.611 |

## Interpretation rails

- ISZE has no pricing discretion — pass-through of IML Base Prices in JPY.
- FX symmetry: ISZE has not reduced prices when JPY weakened without IML instruction.
- The +5.3% increase is driven by IML raising BP_JPY (2030 Vision), not FX movements alone.
- State facts only; do not soften the pricing position in automated reports.

## DB→DLR response (2026-08-10)

- Track: `01_data/00_derived/price_elasticity_db_dlr_ituk_uti.csv` — **ITUK + UTI only**, Israel = UTI not UMI.
- True YoY elasticity **blocked** (one CY sell-out). Rows are `measure_kind=proxy`.
- Price axis = **ASP / list pass-through** (lasting). Dealer invoice **not** a near-term ask.
- Proceed with proxies: soft-wired via `paths.db_dlr_response` / `db_dlr_response.py` (diagnostic flags only).
- Do **not** claim ISZE→DB elasticity; do not feed proxy `beta` into +3% allocation deltas.
- Second CY sell-out still unlocks `measure_kind=elasticity` later — not a gate on the soft path.
- OEM street arrange: `03_analytics/isze_pricing/OEM_STREET_ARRANGE.md` (22 OEs; **15/22** street filled 2026-08-10).
- Alloc with street: `20260810T171626Z__alloc__t3pct` — +3.0000% exact; `oem_benchmark` on air_filter + oil_filter.
- ZPR1 vs PR00 diagnostic (basket PNs): `01_data/00_derived/pricing_zpr1_pr00_diff_basket_20260810.csv` (UTI≠UMI).
- Evening pass 2: Ford shoe 1713904 still open (Ford shop 2138025 ≠ proven supersession). Eucon COMPARABLE = DAF/Hilux/Ranger only — no L200/Transit/Sprinter/MAN/Crafter maps. No new alloc (no new street).
- Readiness / street-vs-Isuze: `01_data/00_derived/oem_peer_readiness_20260810.json` · internal brief: `01_data/01_Pricing/PRICING_STATUS_BRIEF_2026-08-10.md`.
- CLI: `python -m isze_pricing.cli diagnose`.
