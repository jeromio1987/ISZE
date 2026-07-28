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
