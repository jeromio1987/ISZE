# Verification - AIM comparison, ALL

Built 2026-10-02T13:12:16+00:00. 61 of 61 checks pass.

## All checks

| Check | Expected | Actual | Result | Note |
|---|---|---|---|---|
| month rows equal the total row: dealer_sellout_long_GREECE_CY2025.csv | 24777.0 | 24777.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_IRELAND_CY2025.csv | 53328.0 | 53328.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_IRELAND_CY2026YTD.csv | 25986.0 | 25986.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_ITUK_CY2023.csv | 219061.0 | 219061.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_ITUK_CY2024.csv | 230586.0 | 230586.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_ITUK_CY2026YTD.csv | 155974.0 | 155974.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_ITUK_network_CY2025.csv | 224587.0 | 224587.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_IUK_CY2025.csv | 248638.0 | 248638.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_IUK_CY2026YTD.csv | 142040.0 | 142040.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_PORTUGAL_CY2025.csv | 51363.0 | 51363.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_PORTUGAL_CY2026YTD.csv | 39790.0 | 39790.0 | PASS |  |
| month rows against the total row: dealer_sellout_long_UTI_CY2025.csv | 92660.0 | 55570.0 | PASS | the brief names this file: its year row holds the whole year (92,660) while the month rows cover January and August to December only (55,570), because February to July 2025 are genuinely absent. Only the month rows are used, and the missing months are reported. |
| month rows against the total row: dealer_sellout_long_UTI_CY2026YTD.csv | no total row in the file | 61833.0 | PASS | the file carries month rows only |
| UTI 2025: year row 92,660 against month rows 55,570 | 92660.0 | 92660.0 | PASS | month rows 55,570; the brief states 55,570, measured 55,570 |
| longest unbroken sales-to-dealer run: GREECE | reported, not a gate | 12 months, 2025-01 to 2025-12, longest equal split 6 against 6 | PASS | reported, not a gate |
| longest unbroken sales-to-dealer run: IRELAND | reported, not a gate | 19 months, 2025-01 to 2026-07, longest equal split 9 against 9 | PASS | reported, not a gate |
| longest unbroken sales-to-dealer run: ITUK | reported, not a gate | 44 months, 2023-01 to 2026-08, longest equal split 22 against 22 | PASS | reported, not a gate |
| longest unbroken sales-to-dealer run: IUK | reported, not a gate | 19 months, 2025-01 to 2026-07, longest equal split 9 against 9 | PASS | reported, not a gate |
| longest unbroken sales-to-dealer run: PORTUGAL | reported, not a gate | 20 months, 2025-01 to 2026-08, longest equal split 10 against 10 | PASS | reported, not a gate |
| longest unbroken sales-to-dealer run: UTI | reported, not a gate | 11 months, 2025-08 to 2026-06, longest equal split 5 against 5 | PASS | reported, not a gate |
| longest unbroken both-stage run (ISZE billing and sales to dealer together): GREECE | reported, not a gate | 12 months, 2025-01 to 2025-12, longest equal split 6 against 6 | PASS | reported, not a gate. The ranking basis is sales to dealer, so the billing gaps of April to June 2026 do not decide the period pair; they only shorten this second run |
| longest unbroken both-stage run (ISZE billing and sales to dealer together): IRELAND | reported, not a gate | 15 months, 2025-01 to 2026-03, longest equal split 7 against 7 | PASS | reported, not a gate. The ranking basis is sales to dealer, so the billing gaps of April to June 2026 do not decide the period pair; they only shorten this second run |
| longest unbroken both-stage run (ISZE billing and sales to dealer together): ITUK | reported, not a gate | 39 months, 2023-01 to 2026-03, longest equal split 19 against 19 | PASS | reported, not a gate. The ranking basis is sales to dealer, so the billing gaps of April to June 2026 do not decide the period pair; they only shorten this second run |
| longest unbroken both-stage run (ISZE billing and sales to dealer together): IUK | reported, not a gate | 15 months, 2025-01 to 2026-03, longest equal split 7 against 7 | PASS | reported, not a gate. The ranking basis is sales to dealer, so the billing gaps of April to June 2026 do not decide the period pair; they only shorten this second run |
| longest unbroken both-stage run (ISZE billing and sales to dealer together): PORTUGAL | reported, not a gate | 15 months, 2025-01 to 2026-03, longest equal split 7 against 7 | PASS | reported, not a gate. The ranking basis is sales to dealer, so the billing gaps of April to June 2026 do not decide the period pair; they only shorten this second run |
| longest unbroken both-stage run (ISZE billing and sales to dealer together): UTI | reported, not a gate | 8 months, 2025-08 to 2026-03, longest equal split 4 against 4 | PASS | reported, not a gate. The ranking basis is sales to dealer, so the billing gaps of April to June 2026 do not decide the period pair; they only shorten this second run |
| pair is carried by 2N contiguous months: GREECE 2025-01..2025-12 | 2N contiguous months present | 12 months | PASS |  |
| pair is carried by 2N contiguous months: IRELAND 2025-01..2025-12 | 2N contiguous months present | 12 months | PASS |  |
| pair is carried by 2N contiguous months: ITUK 2025-01..2025-12 | 2N contiguous months present | 12 months | PASS |  |
| pair is carried by 2N contiguous months: IUK 2025-01..2025-12 | 2N contiguous months present | 12 months | PASS |  |
| pair is carried by 2N contiguous months: PORTUGAL 2025-01..2025-12 | 2N contiguous months present | 12 months | PASS |  |
| pair is carried by 2N contiguous months: GREECE 2025-03..2025-12 | 2N contiguous months present | 10 months | PASS |  |
| pair is carried by 2N contiguous months: IRELAND 2025-03..2025-12 | 2N contiguous months present | 10 months | PASS |  |
| pair is carried by 2N contiguous months: ITUK 2025-03..2025-12 | 2N contiguous months present | 10 months | PASS |  |
| pair is carried by 2N contiguous months: IUK 2025-03..2025-12 | 2N contiguous months present | 10 months | PASS |  |
| pair is carried by 2N contiguous months: PORTUGAL 2025-03..2025-12 | 2N contiguous months present | 10 months | PASS |  |
| pair is carried by 2N contiguous months: ITUK 2023-01..2026-08 | 2N contiguous months present | 44 months | PASS |  |
| units reconcile to the sales-to-dealer rows: GREECE 2025-01..2025-12 | 24777.0 | 24777.0 | PASS | on the page 24,762.0 units + 15.0 units dropped by the scope rule (non-part lines and lubricants) = 24,777.0 source units |
| units reconcile to the sales-to-dealer rows: IRELAND 2025-01..2025-12 | 53328.0 | 53328.0 | PASS | on the page 53,267.0 units + 61.0 units dropped by the scope rule (non-part lines and lubricants) = 53,328.0 source units |
| units reconcile to the sales-to-dealer rows: ITUK 2025-01..2025-12 | 224587.0 | 224587.0 | PASS | on the page 223,717.0 units + 870.0 units dropped by the scope rule (non-part lines and lubricants) = 224,587.0 source units |
| units reconcile to the sales-to-dealer rows: IUK 2025-01..2025-12 | 248638.0 | 248638.0 | PASS | on the page 248,242.0 units + 396.0 units dropped by the scope rule (non-part lines and lubricants) = 248,638.0 source units. IUK reports part of its sales to dealer in half units; they are kept as reported rather than rounded, so the figures still sum to the source |
| units reconcile to the sales-to-dealer rows: PORTUGAL 2025-01..2025-12 | 51363.0 | 51363.0 | PASS | on the page 50,750.0 units + 613.0 units dropped by the scope rule (non-part lines and lubricants) = 51,363.0 source units |
| sales to dealer, period A: units not classified in AIM | reported, not a gate | 4.12% of 320,786 units | PASS | reported, not a gate |
| sales to dealer, period A: units with no price on the list | reported, not a gate | 1.59% of 320,786 units | PASS | reported, not a gate |
| sales to dealer, period B: units not classified in AIM | reported, not a gate | 2.12% of 336,574 units | PASS | reported, not a gate |
| sales to dealer, period B: units with no price on the list | reported, not a gate | 1.11% of 336,574 units | PASS | reported, not a gate |
| the growth and decline euro sums back to the movement between the two period totals | 757313.53 | 757313.52 | PASS | 2,411,643.49 up and -1,654,329.97 down across 20,048 priced part numbers. The right-hand figure is the difference between the two period totals read straight from the periods, so nothing is lost between the two ranked lists. The tolerance is five cents, which is the rounding the page carries at this size |
| the drill conserves the euro: AIM level 1 group against its level 2 groups | 0.0 | 0.0 | PASS | opening a bar must not lose or double count any euro; the largest gap found across all groups is 0.0000 euro (in group 0) |
| the drill conserves the euro: level 2 group against its level 3 groups | 0.0 | 0.0 | PASS | opening a bar must not lose or double count any euro; the largest gap found across all groups is 0.0000 euro (in group 0) |
| the drill conserves the euro: level 3 group against its part numbers | 0.0 | 0.0 | PASS | opening a bar must not lose or double count any euro; the largest gap found across all groups is 0.0000 euro |
| no NaN or infinity in the embedded rows | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: a1 | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: sp | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: fam | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: bvp | 0 | 0 | PASS |  |
| no NaN or infinity in the part-number dimension: src | 0 | 0 | PASS |  |
| ISZE billing euro excluded by document type | reported, not a gate | 5848908.52 | PASS | 17,403 rows, saty in CR, RE, DR, ZDR, FD or blank |
| sales to dealer reported in half units | reported, not a gate | 90 rows | PASS | IUK is the only distributor that reports part of its sales to dealer in half units, and they are kept as reported so the figures still sum to the source. By distributor: IUK: 90 |
| sales to dealer units dropped by the scope rule (lubricants and non-part lines) | reported, not a gate | 5149.0 | PASS | lubricant (Fluids Chemicals): 5,120; not a part line: 29 |
| ISZE billing euro dropped by the scope rule | reported, not a gate | 349625.38 | PASS | lubricant (Fluids Chemicals): 200,530.27; not a part line: 149,095.11 |
| HTML file size | under 15 MB | 8.19 | PASS | MB; self-contained, data and Chart.js inline, no server and no internet |

## default_pair

```json
{
  "n": 6,
  "a_from": "2025-01",
  "a_to": "2025-06",
  "b_from": "2025-07",
  "b_to": "2025-12",
  "dbs": [
    "GREECE",
    "IRELAND",
    "ITUK",
    "IUK",
    "PORTUGAL"
  ],
  "n_dbs": 5,
  "months_a": [
    "2025-01",
    "2025-02",
    "2025-03",
    "2025-04",
    "2025-05",
    "2025-06"
  ],
  "months_b": [
    "2025-07",
    "2025-08",
    "2025-09",
    "2025-10",
    "2025-11",
    "2025-12"
  ]
}
```

## pairs_offered

```json
{
  "ALL": [
    {
      "n": 6,
      "a_from": "2025-01",
      "a_to": "2025-06",
      "b_from": "2025-07",
      "b_to": "2025-12",
      "dbs": [
        "GREECE",
        "IRELAND",
        "ITUK",
        "IUK",
        "PORTUGAL"
      ],
      "n_dbs": 5,
      "months_a": [
        "2025-01",
        "2025-02",
        "2025-03",
        "2025-04",
        "2025-05",
        "2025-06"
      ],
      "months_b": [
        "2025-07",
        "2025-08",
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12"
      ]
    },
    {
      "n": 5,
      "a_from": "2025-03",
      "a_to": "2025-07",
      "b_from": "2025-08",
      "b_to": "2025-12",
      "dbs": [
        "GREECE",
        "IRELAND",
        "ITUK",
        "IUK",
        "PORTUGAL"
      ],
      "n_dbs": 5,
      "months_a": [
        "2025-03",
        "2025-04",
        "2025-05",
        "2025-06",
        "2025-07"
      ],
      "months_b": [
        "2025-08",
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12"
      ]
    },
    {
      "n": 22,
      "a_from": "2023-01",
      "a_to": "2024-10",
      "b_from": "2024-11",
      "b_to": "2026-08",
      "dbs": [
        "ITUK"
      ],
      "n_dbs": 1,
      "months_a": [
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
        "2024-10"
      ],
      "months_b": [
        "2024-11",
        "2024-12",
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
  ],
  "GREECE": [
    {
      "n": 6,
      "a_from": "2025-01",
      "a_to": "2025-06",
      "b_from": "2025-07",
      "b_to": "2025-12",
      "dbs": [
        "GREECE"
      ],
      "n_dbs": 1,
      "months_a": [
        "2025-01",
        "2025-02",
        "2025-03",
        "2025-04",
        "2025-05",
        "2025-06"
      ],
      "months_b": [
        "2025-07",
        "2025-08",
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12"
      ]
    }
  ],
  "IRELAND": [
    {
      "n": 9,
      "a_from": "2025-02",
      "a_to": "2025-10",
      "b_from": "2025-11",
      "b_to": "2026-07",
      "dbs": [
        "IRELAND"
      ],
      "n_dbs": 1,
      "months_a": [
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
        "2026-07"
      ]
    },
    {
      "n": 9,
      "a_from": "2025-01",
      "a_to": "2025-09",
      "b_from": "2025-10",
      "b_to": "2026-06",
      "dbs": [
        "IRELAND"
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
        "2025-09"
      ],
      "months_b": [
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06"
      ]
    }
  ],
  "ITUK": [
    {
      "n": 22,
      "a_from": "2023-01",
      "a_to": "2024-10",
      "b_from": "2024-11",
      "b_to": "2026-08",
      "dbs": [
        "ITUK"
      ],
      "n_dbs": 1,
      "months_a": [
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
        "2024-10"
      ],
      "months_b": [
        "2024-11",
        "2024-12",
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
  ],
  "IUK": [
    {
      "n": 9,
      "a_from": "2025-02",
      "a_to": "2025-10",
      "b_from": "2025-11",
      "b_to": "2026-07",
      "dbs": [
        "IUK"
      ],
      "n_dbs": 1,
      "months_a": [
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
        "2026-07"
      ]
    },
    {
      "n": 9,
      "a_from": "2025-01",
      "a_to": "2025-09",
      "b_from": "2025-10",
      "b_to": "2026-06",
      "dbs": [
        "IUK"
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
        "2025-09"
      ],
      "months_b": [
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06"
      ]
    }
  ],
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
  ],
  "UTI": [
    {
      "n": 5,
      "a_from": "2025-09",
      "a_to": "2026-01",
      "b_from": "2026-02",
      "b_to": "2026-06",
      "dbs": [
        "UTI"
      ],
      "n_dbs": 1,
      "months_a": [
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01"
      ],
      "months_b": [
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06"
      ]
    },
    {
      "n": 5,
      "a_from": "2025-08",
      "a_to": "2025-12",
      "b_from": "2026-01",
      "b_to": "2026-05",
      "dbs": [
        "UTI"
      ],
      "n_dbs": 1,
      "months_a": [
        "2025-08",
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12"
      ],
      "months_b": [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05"
      ]
    }
  ]
}
```

## coverage

```json
[
  {
    "db": "GREECE",
    "label": "RSA",
    "scope": "MIXED",
    "sold_scope": "D-MAX",
    "sold_scope_note": "D-Max only, calendar 2025 only",
    "sold_months": 12,
    "billed_months": 41,
    "run_months": 12,
    "run_span": "2025-01 to 2025-12",
    "max_n": 6,
    "offers": true,
    "longest_pair_n": 6,
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
      "2024-12",
      "2026-01",
      "2026-02",
      "2026-03",
      "2026-07",
      "2026-08"
    ]
  },
  {
    "db": "IRELAND",
    "label": "Ireland",
    "scope": "MIXED",
    "sold_scope": "MIXED",
    "sold_scope_note": "network level, all families",
    "sold_months": 19,
    "billed_months": 41,
    "run_months": 19,
    "run_span": "2025-01 to 2026-07",
    "max_n": 9,
    "offers": true,
    "longest_pair_n": 9,
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
      "2024-12",
      "2026-08"
    ]
  },
  {
    "db": "ITUK",
    "label": "ITUK",
    "scope": "CV",
    "sold_scope": "CV",
    "sold_scope_note": "commercial vehicles only (CV)",
    "sold_months": 44,
    "billed_months": 41,
    "run_months": 44,
    "run_span": "2023-01 to 2026-08",
    "max_n": 22,
    "offers": true,
    "longest_pair_n": 22,
    "sold_missing_where_billed": []
  },
  {
    "db": "IUK",
    "label": "IUK",
    "scope": "LCV",
    "sold_scope": "D-MAX",
    "sold_scope_note": "D-Max only",
    "sold_months": 19,
    "billed_months": 41,
    "run_months": 19,
    "run_span": "2025-01 to 2026-07",
    "max_n": 9,
    "offers": true,
    "longest_pair_n": 9,
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
      "2024-12",
      "2026-08"
    ]
  },
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
  },
  {
    "db": "UTI",
    "label": "UTI",
    "scope": "CV",
    "sold_scope": "MIXED",
    "sold_scope_note": "network level; Feb-Jul 2025 absent",
    "sold_months": 12,
    "billed_months": 41,
    "run_months": 11,
    "run_span": "2025-08 to 2026-06",
    "max_n": 5,
    "offers": true,
    "longest_pair_n": 5,
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
      "2024-12",
      "2025-02",
      "2025-03",
      "2025-04",
      "2025-05",
      "2025-06",
      "2025-07",
      "2026-07",
      "2026-08"
    ]
  }
]
```

## reconciliation_month_rows_vs_total_rows

```json
{
  "dealer_sellout_long_GREECE_CY2025.csv": {
    "distributor": "GREECE",
    "month_rows": 5673,
    "month_rows_qty": 24777.0,
    "total_row_qty": 24777.0,
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
  "dealer_sellout_long_IRELAND_CY2025.csv": {
    "distributor": "IRELAND",
    "month_rows": 13743,
    "month_rows_qty": 53328.0,
    "total_row_qty": 53328.0,
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
  "dealer_sellout_long_IRELAND_CY2026YTD.csv": {
    "distributor": "IRELAND",
    "month_rows": 6909,
    "month_rows_qty": 25986.0,
    "total_row_qty": 25986.0,
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
      "2026-07"
    ]
  },
  "dealer_sellout_long_ITUK_CY2023.csv": {
    "distributor": "ITUK",
    "month_rows": 22213,
    "month_rows_qty": 219061.0,
    "total_row_qty": 219061.0,
    "total_row_periods": [
      "2023"
    ],
    "month_periods": [
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
      "2023-12"
    ]
  },
  "dealer_sellout_long_ITUK_CY2024.csv": {
    "distributor": "ITUK",
    "month_rows": 23006,
    "month_rows_qty": 230586.0,
    "total_row_qty": 230586.0,
    "total_row_periods": [
      "2024"
    ],
    "month_periods": [
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
  },
  "dealer_sellout_long_ITUK_network_CY2025.csv": {
    "distributor": "ITUK",
    "month_rows": 22905,
    "month_rows_qty": 224587.0,
    "total_row_qty": 224587.0,
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
  "dealer_sellout_long_ITUK_CY2026YTD.csv": {
    "distributor": "ITUK",
    "month_rows": 16145,
    "month_rows_qty": 155974.0,
    "total_row_qty": 155974.0,
    "total_row_periods": [
      "2026"
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
  },
  "dealer_sellout_long_IUK_CY2025.csv": {
    "distributor": "IUK",
    "month_rows": 20112,
    "month_rows_qty": 248638.0,
    "total_row_qty": 248638.0,
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
  "dealer_sellout_long_IUK_CY2026YTD.csv": {
    "distributor": "IUK",
    "month_rows": 11704,
    "month_rows_qty": 142040.0,
    "total_row_qty": 142040.0,
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
      "2026-07"
    ]
  },
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
  },
  "dealer_sellout_long_UTI_CY2025.csv": {
    "distributor": "UTI",
    "month_rows": 4681,
    "month_rows_qty": 55570.0,
    "total_row_qty": 92660.0,
    "total_row_periods": [
      "2025"
    ],
    "month_periods": [
      "2025-01",
      "2025-08",
      "2025-09",
      "2025-10",
      "2025-11",
      "2025-12"
    ]
  },
  "dealer_sellout_long_UTI_CY2026YTD.csv": {
    "distributor": "UTI",
    "month_rows": 5489,
    "month_rows_qty": 61833.0,
    "total_row_qty": 0.0,
    "total_row_periods": [],
    "month_periods": [
      "2026-01",
      "2026-02",
      "2026-03",
      "2026-04",
      "2026-05",
      "2026-06"
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
  "file": "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\01_data\\00_derived\\AIM_Master_PN_Categories_Figkey_release_2026-10-02-chassis-frame.csv",
  "release": {
    "release_id": "2026-10-02-chassis-frame",
    "path": "aim_pn_classification_release_2026-10-02-chassis-frame.csv",
    "sha256": "9bb86a9b4d89c5954cd6dd15fdc977db44e66cddaa15e3e70bd0285e3bf3e65b",
    "status": "APPROVED",
    "rows": 164919,
    "rows_note": "data rows, header excluded (same as 2026-10-02)",
    "source": "release 2026-10-02 (aim_pn_classification_release_2026-10-02.csv, sha256 0ac91379...) + next_release_proposal_2026-10-02.csv (42 parts) + body filing (cab mounting members on Chassis Frame) + 2 wrong-in-both fixes",
    "recommendation": "APPROVAL_SUMMARY_2026-10-02-candidate.md; Jerome decisions 2026-10-02 (cab mounting members to Chassis Frame; 4 to-check parts as proposed)",
    "notes": "Cut 2026-10-02 by claude-opus: the 2026-10-02-candidate with Jerome's decision (1) applied (142 cab mounting member rows differ, AIM columns only). Change log aim_pn_classification_release_2026-10-02-chassis-frame.changes.csv; body list aim_pn_classification_release_2026-10-02-chassis-frame.body_filing.csv. Release id: the candidate entry's sha256 is its identity and its file is never overwritten, so a new id in the date + hyphen suffix form; no version label. PCV kits 8981065790 / 8980023462: check against the parts catalogue (EPC).",
    "approved_by": "Jerome",
    "approved_on": "2026-10-02",
    "approved_note": "Jerome approved in chat on 2026-10-02 ('all yes' on APPROVAL_SUMMARY_2026-10-02-candidate.md): cab mounting members to AIM Chassis Frame > Crossmember & Brackets > Bracket (catalogue Body structure); the 4 to-check parts as proposed, PCV kits 8981065790 / 8980023462 to be checked against the parts catalogue (EPC). sha256 re-verified against this register immediately before the status change. Candidate gate (aim_pn_classification_release_2026-10-02-chassis-frame.gate.json): 18 checks pass, release_approved PENDING, 0 fail. Supersedes 2026-10-02 in the same edit; replaces the unapproved 2026-10-02-candidate."
  }
}
```
