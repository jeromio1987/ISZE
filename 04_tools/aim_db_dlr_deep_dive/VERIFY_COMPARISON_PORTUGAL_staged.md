# Verification - AIM comparison, PORTUGAL

Built 2026-10-02T12:55:58+00:00. 25 of 25 checks pass.

## All checks

| Check | Expected | Actual | Result | Note |
|---|---|---|---|---|
| month rows equal the total row: dealer_sellout_long_PORTUGAL_CY2025.csv | 51363.0 | 51363.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_PORTUGAL_CY2026YTD.csv | 39790.0 | 39790.0 | PASS |  |
| longest unbroken sales-to-dealer run: PORTUGAL | reported, not a gate | 20 months, 2025-01 to 2026-08, longest equal split 10 against 10 | PASS | reported, not a gate |
| longest unbroken both-stage run (ISZE billing and sales to dealer together): PORTUGAL | reported, not a gate | 15 months, 2025-01 to 2026-03, longest equal split 7 against 7 | PASS | reported, not a gate. The ranking basis is sales to dealer, so the billing gaps of April to June 2026 do not decide the period pair; they only shorten this second run |
| pair is carried by 2N contiguous months: PORTUGAL 2025-01..2026-08 | 2N contiguous months present | 20 months | PASS |  |
| units reconcile to the sales-to-dealer rows: PORTUGAL 2025-01..2026-08 | 91153.0 | 91153.0 | PASS | on the page 90,002.0 units + 1,151.0 units dropped by the scope rule (non-part lines and lubricants) = 91,153.0 source units |
| sales to dealer, period A: units not classified in AIM | reported, not a gate | 6.28% of 43,387 units | PASS | reported, not a gate |
| sales to dealer, period A: units with no price on the list | reported, not a gate | 3.90% of 43,387 units | PASS | reported, not a gate |
| sales to dealer, period B: units not classified in AIM | reported, not a gate | 6.51% of 46,675 units | PASS | reported, not a gate |
| sales to dealer, period B: units with no price on the list | reported, not a gate | 4.64% of 46,675 units | PASS | reported, not a gate |
| the growth and decline euro sums back to the movement between the two period totals | 190718.13 | 190718.13 | PASS | 579,380.96 up and -388,662.83 down across 9,379 priced part numbers. The right-hand figure is the difference between the two period totals read straight from the periods, so nothing is lost between the two ranked lists. The tolerance is five cents, which is the rounding the page carries at this size |
| the drill conserves the euro: AIM level 1 group against its level 2 groups | 0.0 | 0.0 | PASS | opening a bar must not lose or double count any euro; the largest gap found across all groups is 0.0000 euro (in group 0) |
| the drill conserves the euro: level 2 group against its level 3 groups | 0.0 | 0.0 | PASS | opening a bar must not lose or double count any euro; the largest gap found across all groups is 0.0000 euro (in group 0) |
| the drill conserves the euro: level 3 group against its part numbers | 0.0 | 0.0 | PASS | opening a bar must not lose or double count any euro; the largest gap found across all groups is 0.0000 euro |
| no NaN or infinity in the embedded rows | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: a1 | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: sp | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: fam | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: bvp | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: src | 0 | 0 | PASS |  |
| ISZE billing euro excluded by document type | reported, not a gate | 485604.57 | PASS | 2,895 rows, saty in CR, RE, DR, ZDR, FD or blank |
| sales to dealer reported in half units | reported, not a gate | 0 rows | PASS | none |
| sales to dealer units dropped by the scope rule (lubricants and non-part lines) | reported, not a gate | 1151.0 | PASS | lubricant (Fluids Chemicals): 1,140; not a part line: 11 |
| ISZE billing euro dropped by the scope rule | reported, not a gate | 87551.2 | PASS | lubricant (Fluids Chemicals): 69,535.86; not a part line: 18,015.34 |
| HTML file size | under 15 MB | 1.87 | PASS | MB; self-contained, data and Chart.js inline, no server and no internet |

## default_pair

```json
{
  "n": 10,
  "a_from": "2025-01",
  "a_to": "2025-10",
  "b_from": "2025-11",
  "b_to": "2026-08",
  "dbs": [
    "PORTUGAL"
  ],
  "n_dbs": 1,
  "months_a": [
    "2025-01",
    "2025-02",
    "2025-03",
    "2025-04",
    "2025-05",
    "2025-06",
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10"
  ],
  "months_b": [
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08"
  ]
}
```

## pairs_offered

```json
{
  "PORTUGAL": [
    {
      "n": 10,
      "a_from": "2025-01",
      "a_to": "2025-10",
      "b_from": "2025-11",
      "b_to": "2026-08",
      "dbs": [
        "PORTUGAL"
      ],
      "n_dbs": 1,
      "months_a": [
        "2025-01",
        "2025-02",
        "2025-03",
        "2025-04",
        "2025-05",
        "2025-06",
        "2025-07",
        "2025-08",
        "2025-09",
        "2025-10"
      ],
      "months_b": [
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
        "2026-08"
      ]
    }
  ]
}
```

## coverage

```json
[
  {
    "db": "PORTUGAL",
    "label": "Imotors",
    "scope": "MIXED",
    "sold_scope": "MIXED",
    "sold_scope_note": "network level, all families",
    "sold_months": 20,
    "billed_months": 41,
    "run_months": 20,
    "run_span": "2025-01 to 2026-08",
    "max_n": 10,
    "offers": true,
    "longest_pair_n": 10,
    "sold_missing_where_billed": [
      "2023-01",
      "2023-02",
      "2023-03",
      "2023-04",
      "2023-05",
      "2023-06",
      "2023-07",
      "2023-08",
      "2023-09",
      "2023-10",
      "2023-11",
      "2023-12",
      "2024-01",
      "2024-02",
      "2024-03",
      "2024-04",
      "2024-05",
      "2024-06",
      "2024-07",
      "2024-08",
      "2024-09",
      "2024-10",
      "2024-11",
      "2024-12"
    ]
  }
]
```

## reconciliation_month_rows_vs_total_rows

```json
{
  "dealer_sellout_long_PORTUGAL_CY2025.csv": {
    "distributor": "PORTUGAL",
    "month_rows": 15924,
    "month_rows_qty": 51363.0,
    "total_row_qty": 51363.0,
    "total_row_periods": [
      "2025"
    ],
    "month_periods": [
      "2025-01",
      "2025-02",
      "2025-03",
      "2025-04",
      "2025-05",
      "2025-06",
      "2025-07",
      "2025-08",
      "2025-09",
      "2025-10",
      "2025-11",
      "2025-12"
    ]
  },
  "dealer_sellout_long_PORTUGAL_CY2026YTD.csv": {
    "distributor": "PORTUGAL",
    "month_rows": 11042,
    "month_rows_qty": 39790.0,
    "total_row_qty": 39790.0,
    "total_row_periods": [
      "2026-YTD"
    ],
    "month_periods": [
      "2026-01",
      "2026-02",
      "2026-03",
      "2026-04",
      "2026-05",
      "2026-06",
      "2026-07",
      "2026-08"
    ]
  }
}
```

## open_questions

```json
[
  "The 35% gross margin on sales to dealer is an assumption supplied by Jerome, applied as list / 0.65 because margin is measured on the selling price. If he meant margin on cost (list x 1.35) the figure is about 14% lower. It is a modelled dealer price, not the distributor's turnover, its revenue, or an actual dealer purchase price.",
  "The shortest window per side the page will draw at all is three months. That floor is a judgement made in this build. If a shorter window should be allowed, it changes only which pairs appear in the control; the default pair, which is always the longest equal split, would not move.",
  "For the all-distributors view the default pair is the one that covers the most distributors, and ties are broken toward the longer window and then the more recent one. The other candidate pairs are in the control.",
  "Sales to dealer has no price of its own. Both periods are valued on the same ISZE price list of 10 Aug 2026, so a price change inside the comparison window is not visible in it.",
  "ITUK's sales-to-dealer history starts in January 2023, so its longest equal split is twenty-two months against twenty-two. If a shorter window is wanted for ITUK, the pair control allows it.",
  "In the all-distributors view the scopes differ between distributors: ITUK is commercial vehicles only, IUK and Greece are D-Max only, and the rest are the whole network. Adding them together mixes those scopes, which the page states rather than hides."
]
```

## aim_tree

```json
{
  "file": "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\01_data\\00_derived\\AIM_Master_PN_Categories_Figkey_release_2026-10-02-candidate.csv",
  "release": {
    "release_id": "2026-10-02-candidate",
    "path": "aim_pn_classification_release_2026-10-02-candidate.csv",
    "sha256": "d17bb48d9d9c5cd2f8643ea2e3515c9a1bda21c26aab657fe0a5140197c4c54e",
    "status": "PENDING_APPROVAL",
    "rows": 164919,
    "rows_note": "data rows, header excluded (same as 2026-10-02)",
    "source": "release 2026-10-02 (aim_pn_classification_release_2026-10-02.csv, sha256 0ac91379...) + next_release_proposal_2026-10-02.csv (42 parts) + body filing + 2 wrong-in-both fixes",
    "recommendation": "01_data/91_build/pr00_21sep_review_2026-10-02/REVIEW.md; UTI back-order findings 2 Oct (body parts not filed under body); Jerome go 2026-10-02",
    "notes": "Cut 2026-10-02 by claude-opus as the candidate after 2026-10-02. Change log aim_pn_classification_release_2026-10-02-candidate.changes.csv; body list aim_pn_classification_release_2026-10-02-candidate.body_filing.csv. Release id: 2026-10-02 taken; hyphen suffix on the date per the 2026-09-24-candidate precedent, no version label."
  }
}
```
