# Action Ledger review — 20260825

**internal · internal only.** Attribution wording: co-movement only.

## Data-sufficiency verdict

Sufficient to build and backfill (nine surfaces, green pipeline, sales_fact billing through 2026-06-30). Insufficient for measurable outcomes past billing horizon 2026-06-30 — those rows stay NOT_MEASURABLE with realised_eur NULL; never estimated.

## What we said (open book)

- Opportunities on ledger: **23236** (source: `action_ledger.parquet`)
- Open (NEW/TRIAGED/ACTIONED): **23236**
- € at stake (sum of source cells, mixed bases — do not treat as one wallet): **€22,110,563.54**
- Rejects this run: **0**

### Top 15 open by €

| opportunity_id | signal | db | entity | € at stake | basis | source |
|---|---|---|---|---:|---|---|
| `8336fe9a6dce4d33` | BOOK_B | IUK | 8983767550 | 639,901.78 | L12M | revision_book_b_top_review.csv |
| `a65f48abce0561c5` | BOOK_B | GREECE | 8983767550 | 639,901.78 | L12M | revision_book_b_top_review.csv |
| `a97f7a60b0742682` | BOOK_B | IRELAND | 8983767550 | 639,901.78 | L12M | revision_book_b_top_review.csv |
| `3b4361608b685ff0` | LEAKAGE | IUK | 8983767550 | 573,277.00 | ANNUALISED_SOURCE | leakage_monday_actions_20260819.csv |
| `635017e34dec6292` | LEAKAGE | IUK | 7552348280 | 555,970.00 | ANNUALISED_SOURCE | leakage_monday_actions_20260819.csv |
| `9130cba985b4ed1e` | LEAKAGE | IUK | 8978808250 | 458,359.00 | ANNUALISED_SOURCE | leakage_monday_actions_20260819.csv |
| `bc20b124a5f34cd7` | LEAKAGE | IUK | 8978808270 | 447,138.00 | ANNUALISED_SOURCE | leakage_monday_actions_20260819.csv |
| `32169937e7643606` | CATALOGUE_GAP | — | 550047337 | 433,820.16 | CY2025 | no_pr00_gap_cy2025_ranked.csv |
| `268803f1ca0ad0cd` | BOOK_B | UTI | 8982447940 | 355,338.39 | L12M | revision_book_b_top_review.csv |
| `5b5d9593d115e304` | BOOK_B | IRELAND | 8982447940 | 355,338.39 | L12M | revision_book_b_top_review.csv |
| `afff0d9c23dc34e4` | REPLENISHMENT | IUK | 8983767550 | 266,699.80 | CY2025 | replenishment_exceptions_cy2025.csv |
| `b6ec08c4a9c080fd` | BOOK_B | IUK | 8974995480 | 266,146.78 | L12M | revision_book_b_top_review.csv |
| `42da0fab34b308af` | BOOK_B | IRELAND | 8974995480 | 266,146.78 | L12M | revision_book_b_top_review.csv |
| `c048e62f5798bfb3` | BOOK_B | GREECE | 8974995480 | 266,146.78 | L12M | revision_book_b_top_review.csv |
| `e0b4ce354adfe311` | DEFECTION | ITUK | ITUK|fuel_filter | 232,926.57 | TRAILING_12M | defection_alerts.csv |

## What happened (outcomes)

No ACTIONED-or-later decisions yet — outcomes empty by design. Edit `action_ledger_decisions.csv` to triage.

## Rejects & not-measurable

Rejects file: `action_ledger_rejects.csv` (0 rows).
NOT_MEASURABLE rows name the billing horizon (currently **2026-06-30**) when the window cannot close.

## Adapter counts

- `dealer_leakage_ituk`: in=260 out=260 [ok]
- `revision_exception_queue`: in=20572 out=20572 [ok]
- `replenishment_exceptions_cy2025`: in=1595 out=1595 [ok]
- `early_warning`: in=19 out=19 [ok]
- `defection_alerts`: in=265 out=265 [ok]
- `no_pr00_gap_cy2025_ranked`: in=31 out=31 [ok]
- `revision_book_b_top_review`: in=500 out=500 [ok]
- `leakage_monday_actions`: in=40 out=40 [ok]
- `account_health_latest_flagged`: in=16 out=16 [ok]
- EXCLUDED: portfolio_triage_20260819.csv — rollup of early_warning + account_health; excluded to avoid double-count

_produced_at 2026-08-25T17:52:29Z · run_id `20260825T175229Z_48a077`_
