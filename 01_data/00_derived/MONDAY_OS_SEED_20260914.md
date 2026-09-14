# Monday OS seed — 2026-09-14 (Mode B)

**State used:** `TRIAGED` (legal human state). The plan said REVIEW; that token is **illegal** in `build_action_ledger.py` and would reject. TRIAGED = review; confirm or drop. **Not ACTIONED.** No `realised_eur`.

**Source:** top 15 `eur_at_stake` on `action_ledger_open.csv` (mixed-basis cells — **do not sum**). Five rows, one per distinct entity, skipping duplicate PN×DB copies of 8983767550.

| opportunity_id | Rank in top-15 | Signal | DB | Entity | € cell | Basis |
|---|---|---|---|---|---|---|
| `8336fe9a6dce4d33` | 1 | BOOK_B | IUK | 8983767550 | 639,902 | L12M |
| `635017e34dec6292` | 5 | LEAKAGE | IUK | 7552348280 | 555,970 | ANNUALISED_SOURCE (Monday list) |
| `9130cba985b4ed1e` | 6 | LEAKAGE | IUK | 8978808250 | 458,359 | ANNUALISED_SOURCE (Monday list) |
| `32169937e7643606` | 8 | CATALOGUE_GAP | — | 550047337 | 433,820 | CY2025 (`5500*` Shell lubricant SKU) |
| `e0b4ce354adfe311` | 15 | DEFECTION | ITUK | ITUK\|fuel_filter | 232,927 | TRAILING_12M |

**IUK ≠ ITUK.** The Book B / leakage seeds are IUK. The defection seed is ITUK.

**Human file:** `action_ledger_decisions.csv` — owner blank. Builder does not write this file.

**Crosswalk (all 40 Monday PNs):** `monday_pn_opportunity_crosswalk_20260914.csv` (40/40 matched). Command Center HTML **not** rebuilt.

**Outcomes:** empty until a later cycle after ACTIONED + a data refresh.
