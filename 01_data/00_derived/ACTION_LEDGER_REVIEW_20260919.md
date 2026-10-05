# Action Ledger review — 20260919

**internal · internal only.** Attribution wording: co-movement only.

## Data-sufficiency verdict

Sufficient to build and backfill (nine surfaces, green pipeline, sales_fact billing through 2026-06-30). Insufficient for measurable outcomes past billing horizon 2026-06-30 — those rows stay NOT_MEASURABLE with realised_eur NULL; never estimated.

## What we said (open book)

- Opportunities on ledger: **23763** (source: `action_ledger.parquet`)
- Open (NEW/TRIAGED/ACTIONED): **23763**
- € at stake (sum of source cells, mixed bases — do not treat as one wallet): **€16,263,425.84**
- Rejects this run: **0**

### Top 15 open by €

| opportunity_id | signal | db | entity | € at stake | basis | source |
|---|---|---|---|---:|---|---|
| `a65f48abce0561c5` | BOOK_B | GREECE | 8983767550 | 639,901.78 | L12M | revision_book_b_top_review.csv |
| `8336fe9a6dce4d33` | BOOK_B | IUK | 8983767550 | 639,901.78 | L12M | revision_book_b_top_review.csv |
| `a97f7a60b0742682` | BOOK_B | IRELAND | 8983767550 | 639,901.78 | L12M | revision_book_b_top_review.csv |
| `32169937e7643606` | CATALOGUE_GAP | — | 550047337 | 433,820.16 | CY2025 | no_pr00_gap_cy2025_ranked.csv |
| `268803f1ca0ad0cd` | BOOK_B | UTI | 8982447940 | 355,338.39 | L12M | revision_book_b_top_review.csv |
| `5b5d9593d115e304` | BOOK_B | IRELAND | 8982447940 | 355,338.39 | L12M | revision_book_b_top_review.csv |
| `682ea7bdb5bb55ef` | BOOK_B | ITUK | 8982447940 | 355,338.39 | L12M | revision_book_b_top_review.csv |
| `e0b4ce354adfe311` | DEFECTION | ITUK | ITUK|fuel_filter | 232,926.57 | TRAILING_12M | defection_alerts.csv |
| `a08550c9ce207f09` | BOOK_B | ITUK | 8981596930 | 219,442.73 | L12M | revision_book_b_top_review.csv |
| `c7db79aa7ba9cb92` | BOOK_B | IRELAND | 8981596930 | 219,442.73 | L12M | revision_book_b_top_review.csv |
| `bd2c4c4d0b782afc` | BOOK_B | IUK | 8981596930 | 219,442.73 | L12M | revision_book_b_top_review.csv |
| `77a113eafdb91a46` | BOOK_B | IRELAND | 8982705240 | 204,375.72 | L12M | revision_book_b_top_review.csv |
| `02f63c0f73c7dcf8` | BOOK_B | IUK | 8982705240 | 204,375.72 | L12M | revision_book_b_top_review.csv |
| `9b93e8435294a051` | BOOK_B | ITUK | 8982705240 | 204,375.72 | L12M | revision_book_b_top_review.csv |
| `85d8f34e34e42400` | BOOK_B | GREECE | 8982705240 | 204,375.72 | L12M | revision_book_b_top_review.csv |

## What happened (outcomes)

No ACTIONED-or-later decisions yet — outcomes empty by design. Edit `action_ledger_decisions.csv` to triage.

## Rejects & not-measurable

Rejects file: `action_ledger_rejects.csv` (0 rows).
NOT_MEASURABLE rows name the billing horizon (currently **2026-06-30**) when the window cannot close.

## Adapter counts

- `dealer_leakage_ituk`: in=260 out=260 [ok]
- `revision_exception_queue`: in=20750 out=20750 [ok]
- `replenishment_exceptions_cy2025`: in=1934 out=1934 [ok]
- `early_warning`: in=19 out=19 [ok]
- `defection_alerts`: in=265 out=265 [ok]
- `no_pr00_gap_cy2025_ranked`: in=31 out=31 [ok]
- `revision_book_b_top_review`: in=500 out=500 [ok]
- `leakage_monday_actions`: in=50 out=50 [ok]
- `account_health_latest_flagged`: in=16 out=16 [ok]
- EXCLUDED: portfolio_triage_20260819.csv — rollup of early_warning + account_health; excluded to avoid double-count

_produced_at 2026-09-19T19:07:58Z · run_id `20260919T190758Z_d4d285`_
