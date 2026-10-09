# U29-B ledger verify — delivery basis (7 Oct 2026)

## Verdict

The delivery-basis field does what it should. **Eligible comparable offers on real UK and Portugal focus rows are still 0.** That is not a scrape failure and not a missing column any more on the U29-B branch; the saved focus pages (and file-backed rows) do not state a delivery basis.

## Measured on PR 71 (`cursor/2026-10-07-universe-u29-b-delivery-basis`)

| Fact | Value |
|---|---|
| Ledger rows after rebuild | 6,690 with 23 columns including delivery fields |
| Rows that state a basis | **4 of 6,690** (all Tranzparts, below free-delivery threshold wording) |
| UK focus rows | 79 — all still blocked |
| Portugal focus rows | 27 — all still blocked |
| Eligible UK / PT | **0 / 0** |
| Mutation (set basis on 8 delivery-only rows) | eligible → 8; blank one → 7 |

### Why UK cannot move yet

| Source | Focus rows | States a basis |
|---|---:|---:|
| KS International | 54 | 0 |
| T&M Commercials | 12 | 0 |
| Tranzparts | 6 | 4 (then dropped as retired loader in coverage) |
| Eucon UK survey / KS crossref files | 66 | 0 (files do not state delivery) |

Larger UK exclusion after delivery is fixed in the abstract: `PRODUCT_MATCH_UNRESOLVED` (54 rows).

## Main clone / GitHub `main`

- PR 71 state: **OPEN, CONFLICTING** (base was U26 harvest branch; many coverage/parser files absent or deleted on `main`).
- Cherry-pick of `52f5bfb4` onto `main` after PR 70+72 was attempted 7 Oct and **aborted** — modify/delete conflicts on coverage CSVs, builders, site parsers, and `price_observations.meta.json`.
- Therefore: **schema groundwork is verified on the branch, not absorbed into main.** Eligible on real data remains 0 everywhere measured.

## What would move eligibility (honest)

1. Rebase/land U26 harvest + U29-B onto a mergeable base without inventing delivery.
2. Or collect pages (or hand notes) that **state** delivery/tax for UK focus numbers.
3. Do not default blank → “collected” or “ex-VAT” from the seller’s country.

Portugal: left **insufficient** per `UNIVERSE_DECISIONS_2026-10-07.md` — no third automated sweep.
