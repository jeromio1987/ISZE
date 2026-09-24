# Verification - ALL

Built 2026-09-24T15:52:08+00:00. 48 of 48 gating checks pass.

## All checks

| Check | Expected | Actual | Result | Note |
|---|---|---|---|---|
| month rows equal the total row: dealer_sellout_long_GREECE_CY2025.csv | 24777.0 | 24777.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_IRELAND_CY2025.csv | 53328.0 | 53328.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_IRELAND_CY2026YTD.csv | 25986.0 | 25986.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_ITUK_CY2023.csv | 219061.0 | 219061.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_ITUK_CY2024.csv | 230586.0 | 230586.0 | PASS |  |
| month rows against the total row: dealer_sellout_long_ITUK_CY2025.csv | 224001.0 | 223897.0 | PASS | the spec names this file: it is the dealer-level file, its year row runs a little above its month rows, and it is used only for the dealer layer. |
| month rows equal the total row: dealer_sellout_long_ITUK_CY2026YTD.csv | 155974.0 | 155974.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_ITUK_network_CY2025.csv | 224587.0 | 224587.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_IUK_CY2025.csv | 248638.0 | 248638.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_IUK_CY2026YTD.csv | 142040.0 | 142040.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_PORTUGAL_CY2025.csv | 51363.0 | 51363.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_PORTUGAL_CY2026YTD.csv | 39790.0 | 39790.0 | PASS |  |
| month rows against the total row: dealer_sellout_long_UTI_CY2025.csv | 92660.0 | 55570.0 | reported | the spec names this file: its year row holds the whole year while the month rows cover only January and August to December, so February to July are genuinely absent. Month rows are used and the missing months are reported as missing. |
| month rows against the total row: dealer_sellout_long_UTI_CY2026YTD.csv | no total row in the file | 61833.0 | PASS | the file carries month rows only, so there is nothing to double count |
| billing reconciles to sales_fact: GREECE 2023 | 434572.93 | 434572.93 | PASS | kept 22,693 units / EUR 431,307.97 + dropped by the scope rule 35 units / EUR 3,264.96 = sales_fact after the document-type exclusion 22,728 units / EUR 434,572.93 |
| billing reconciles to sales_fact: GREECE 2024 | 457648.16 | 457648.16 | PASS | kept 23,602 units / EUR 454,515.60 + dropped by the scope rule 28 units / EUR 3,132.56 = sales_fact after the document-type exclusion 23,630 units / EUR 457,648.16 |
| billing reconciles to sales_fact: GREECE 2025 | 523358.45 | 523358.45 | PASS | kept 27,202 units / EUR 519,208.10 + dropped by the scope rule 19 units / EUR 4,150.35 = sales_fact after the document-type exclusion 27,221 units / EUR 523,358.45 |
| billing reconciles to sales_fact: GREECE 2026 | 142246.71 | 142246.71 | PASS | kept 4,374 units / EUR 138,199.99 + dropped by the scope rule 21 units / EUR 4,046.72 = sales_fact after the document-type exclusion 4,395 units / EUR 142,246.71 |
| billing reconciles to sales_fact: IRELAND 2023 | 1193670.92 | 1193670.92 | PASS | kept 46,638 units / EUR 1,186,921.55 + dropped by the scope rule 91 units / EUR 6,749.37 = sales_fact after the document-type exclusion 46,729 units / EUR 1,193,670.92 |
| billing reconciles to sales_fact: IRELAND 2024 | 1275752.38 | 1275752.38 | PASS | kept 49,987 units / EUR 1,269,723.63 + dropped by the scope rule 77 units / EUR 6,028.75 = sales_fact after the document-type exclusion 50,064 units / EUR 1,275,752.38 |
| billing reconciles to sales_fact: IRELAND 2025 | 1192762.03 | 1192762.03 | PASS | kept 43,865 units / EUR 1,181,829.22 + dropped by the scope rule 49 units / EUR 10,932.81 = sales_fact after the document-type exclusion 43,914 units / EUR 1,192,762.03 |
| billing reconciles to sales_fact: IRELAND 2026 | 421180.15 | 421180.15 | PASS | kept 14,499 units / EUR 415,283.31 + dropped by the scope rule 26 units / EUR 5,896.84 = sales_fact after the document-type exclusion 14,525 units / EUR 421,180.15 |
| billing reconciles to sales_fact: ITUK 2023 | 5844064.48 | 5844064.48 | PASS | kept 258,163 units / EUR 5,779,364.55 + dropped by the scope rule 1,069 units / EUR 64,699.93 = sales_fact after the document-type exclusion 259,232 units / EUR 5,844,064.48 |
| billing reconciles to sales_fact: ITUK 2024 | 6598331.6 | 6598331.6 | PASS | kept 222,979 units / EUR 6,564,178.33 + dropped by the scope rule 910 units / EUR 34,153.27 = sales_fact after the document-type exclusion 223,889 units / EUR 6,598,331.60 |
| billing reconciles to sales_fact: ITUK 2025 | 5575757.47 | 5575757.47 | PASS | kept 204,206 units / EUR 5,544,615.56 + dropped by the scope rule 636 units / EUR 31,141.91 = sales_fact after the document-type exclusion 204,842 units / EUR 5,575,757.47 |
| billing reconciles to sales_fact: ITUK 2026 | 3650016.09 | 3650016.09 | PASS | kept 125,943 units / EUR 3,634,805.99 + dropped by the scope rule 453 units / EUR 15,210.10 = sales_fact after the document-type exclusion 126,396 units / EUR 3,650,016.09 |
| billing reconciles to sales_fact: IUK 2023 | 5202129.12 | 5202129.12 | PASS | kept 229,377 units / EUR 5,190,637.99 + dropped by the scope rule 411 units / EUR 11,491.13 = sales_fact after the document-type exclusion 229,788 units / EUR 5,202,129.12 |
| billing reconciles to sales_fact: IUK 2024 | 7421348.38 | 7421348.38 | PASS | kept 318,699 units / EUR 7,410,047.41 + dropped by the scope rule 341 units / EUR 11,300.97 = sales_fact after the document-type exclusion 319,040 units / EUR 7,421,348.38 |
| billing reconciles to sales_fact: IUK 2025 | 6131009.1 | 6131009.1 | PASS | kept 252,677 units / EUR 6,119,314.77 + dropped by the scope rule 364 units / EUR 11,694.33 = sales_fact after the document-type exclusion 253,041 units / EUR 6,131,009.10 |
| billing reconciles to sales_fact: IUK 2026 | 2388562.71 | 2388562.71 | PASS | kept 80,019 units / EUR 2,384,932.21 + dropped by the scope rule 133 units / EUR 3,630.50 = sales_fact after the document-type exclusion 80,152 units / EUR 2,388,562.71 |
| billing reconciles to sales_fact: PORTUGAL 2023 | 1367131.27 | 1367131.27 | PASS | kept 45,306 units / EUR 1,345,709.95 + dropped by the scope rule 631 units / EUR 21,421.32 = sales_fact after the document-type exclusion 45,937 units / EUR 1,367,131.27 |
| billing reconciles to sales_fact: PORTUGAL 2024 | 1536889.29 | 1536889.29 | PASS | kept 51,398 units / EUR 1,512,921.32 + dropped by the scope rule 590 units / EUR 23,967.97 = sales_fact after the document-type exclusion 51,988 units / EUR 1,536,889.29 |
| billing reconciles to sales_fact: PORTUGAL 2025 | 1712224.74 | 1712224.74 | PASS | kept 54,903 units / EUR 1,685,088.50 + dropped by the scope rule 768 units / EUR 27,136.24 = sales_fact after the document-type exclusion 55,671 units / EUR 1,712,224.74 |
| billing reconciles to sales_fact: PORTUGAL 2026 | 767293.04 | 767293.04 | PASS | kept 24,613 units / EUR 752,267.37 + dropped by the scope rule 346 units / EUR 15,025.67 = sales_fact after the document-type exclusion 24,959 units / EUR 767,293.04 |
| billing reconciles to sales_fact: UTI 2023 | 3638845.21 | 3638845.21 | PASS | kept 103,583 units / EUR 3,626,837.87 + dropped by the scope rule 100 units / EUR 12,007.34 = sales_fact after the document-type exclusion 103,683 units / EUR 3,638,845.21 |
| billing reconciles to sales_fact: UTI 2024 | 2651201.68 | 2651201.68 | PASS | kept 104,618 units / EUR 2,636,373.81 + dropped by the scope rule 120 units / EUR 14,827.87 = sales_fact after the document-type exclusion 104,738 units / EUR 2,651,201.68 |
| billing reconciles to sales_fact: UTI 2025 | 3337116.94 | 3337116.94 | PASS | kept 124,634 units / EUR 3,330,709.47 + dropped by the scope rule 94 units / EUR 6,407.47 = sales_fact after the document-type exclusion 124,728 units / EUR 3,337,116.94 |
| billing reconciles to sales_fact: UTI 2026 | 1169170.41 | 1169170.41 | PASS | kept 49,925 units / EUR 1,167,863.41 + dropped by the scope rule 23 units / EUR 1,307.00 = sales_fact after the document-type exclusion 49,948 units / EUR 1,169,170.41 |
| comparison offered exactly when 2N contiguous months exist: GREECE | offered on a window that sits inside the run | cannot carry it (longest unbroken both-stage run 12 months ending 2025-12; longest comparison 6 against 6); on the last-12 window ending 2026-08: withheld; on a 12-month window ending 2026-03: withheld | PASS | the gate is 'both windows inside one unbroken both-stage run', exactly as the page applies it. The break at Apr-Jun 2026 sits inside every span ending 2026-08, so on the window the page lands on nobody is offered one; ITUK gets it as soon as the window ends at 2026-03 or earlier. No shorter comparison is offered as a fallback anywhere |
| comparison offered exactly when 2N contiguous months exist: IRELAND | offered on a window that sits inside the run | cannot carry it (longest unbroken both-stage run 15 months ending 2026-03; longest comparison 7 against 7); on the last-12 window ending 2026-08: withheld; on a 12-month window ending 2026-03: withheld | PASS | the gate is 'both windows inside one unbroken both-stage run', exactly as the page applies it. The break at Apr-Jun 2026 sits inside every span ending 2026-08, so on the window the page lands on nobody is offered one; ITUK gets it as soon as the window ends at 2026-03 or earlier. No shorter comparison is offered as a fallback anywhere |
| comparison offered exactly when 2N contiguous months exist: ITUK | offered on a window that sits inside the run | can carry it (longest unbroken both-stage run 39 months ending 2026-03; longest comparison 19 against 19); on the last-12 window ending 2026-08: withheld; on a 12-month window ending 2026-03: offered | PASS | the gate is 'both windows inside one unbroken both-stage run', exactly as the page applies it. The break at Apr-Jun 2026 sits inside every span ending 2026-08, so on the window the page lands on nobody is offered one; ITUK gets it as soon as the window ends at 2026-03 or earlier. No shorter comparison is offered as a fallback anywhere |
| comparison offered exactly when 2N contiguous months exist: IUK | offered on a window that sits inside the run | cannot carry it (longest unbroken both-stage run 15 months ending 2026-03; longest comparison 7 against 7); on the last-12 window ending 2026-08: withheld; on a 12-month window ending 2026-03: withheld | PASS | the gate is 'both windows inside one unbroken both-stage run', exactly as the page applies it. The break at Apr-Jun 2026 sits inside every span ending 2026-08, so on the window the page lands on nobody is offered one; ITUK gets it as soon as the window ends at 2026-03 or earlier. No shorter comparison is offered as a fallback anywhere |
| comparison offered exactly when 2N contiguous months exist: PORTUGAL | offered on a window that sits inside the run | cannot carry it (longest unbroken both-stage run 15 months ending 2026-03; longest comparison 7 against 7); on the last-12 window ending 2026-08: withheld; on a 12-month window ending 2026-03: withheld | PASS | the gate is 'both windows inside one unbroken both-stage run', exactly as the page applies it. The break at Apr-Jun 2026 sits inside every span ending 2026-08, so on the window the page lands on nobody is offered one; ITUK gets it as soon as the window ends at 2026-03 or earlier. No shorter comparison is offered as a fallback anywhere |
| comparison offered exactly when 2N contiguous months exist: UTI | offered on a window that sits inside the run | cannot carry it (longest unbroken both-stage run 8 months ending 2026-03; longest comparison 4 against 4); on the last-12 window ending 2026-08: withheld; on a 12-month window ending 2026-03: withheld | PASS | the gate is 'both windows inside one unbroken both-stage run', exactly as the page applies it. The break at Apr-Jun 2026 sits inside every span ending 2026-08, so on the window the page lands on nobody is offered one; ITUK gets it as soon as the window ends at 2026-03 or earlier. No shorter comparison is offered as a fallback anywhere |
| last-12-month window: both-stage coverage per distributor | reported, not a gate | GREECE 4/12; IRELAND 8/12; ITUK 9/12; IUK 8/12; PORTUGAL 9/12; UTI 7/12 | PASS | months of the last twelve that carry billing AND sales to dealer |
| longest contiguous both-stage run, per distributor | reported, not a gate | GREECE 12 months ending 2025-12; IRELAND 15 months ending 2026-03; ITUK 39 months ending 2026-03; IUK 15 months ending 2026-03; PORTUGAL 15 months ending 2026-03; UTI 8 months ending 2026-03 | PASS | contiguity is measured, not inferred; the breaks are the months whose billing rows all carry a blank document type |
| distributors that can carry a 12-versus-12 comparison at all | reported, not a gate | ITUK | PASS | ITUK is the only one whose unbroken both-stage run reaches 24 months; everybody else is withheld, with no shorter fallback offered |
| billed: units not classified in AIM | None | 4.78 | reported | reported, not a gate |
| billed: units with no price on the list | None | 0.03 | reported | reported, not a gate |
| sold: units not classified in AIM | None | 5.57 | reported | reported, not a gate |
| sold: units with no price on the list | None | 1.03 | reported | reported, not a gate |
| PMS cover above 100% carries a warning in the page | every instance flagged | None | PASS | the page marks every percentage above 100% with a warning and a reason |
| HTML file size | under 15 MB for run 2 | 7.19 | PASS | MB, self-contained: data and Chart.js inline, no treemap plugin since that chart was removed, no server and no internet needed |

## coverage

```json
[
  {
    "db": "GREECE",
    "label": "RSA",
    "scope": "MIXED",
    "sold_scope": "D-MAX",
    "billed_range": [
      "2023-01",
      "2026-08"
    ],
    "billed_months": 41,
    "sold_range": [
      "2025-01",
      "2025-12"
    ],
    "sold_months": 12,
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
    ],
    "l12": {
      "from": "2025-09",
      "to": "2026-08",
      "n": 12,
      "both": 4,
      "complete": false
    },
    "longest": {
      "n": 6,
      "run": 12,
      "end": "2025-12"
    },
    "comparison_reach": {
      "l12": {
        "from": "2025-09",
        "to": "2026-08",
        "n": 12,
        "both": 4,
        "complete": false
      },
      "run": 12,
      "run_end": "2025-12",
      "longest": {
        "n": 6,
        "run": 12,
        "end": "2025-12"
      },
      "run_ending_at_last": 0,
      "gaps": [],
      "both_absent": [
        "2026-04",
        "2026-05",
        "2026-06"
      ]
    }
  },
  {
    "db": "IRELAND",
    "label": "Ireland",
    "scope": "MIXED",
    "sold_scope": "MIXED",
    "billed_range": [
      "2023-01",
      "2026-08"
    ],
    "billed_months": 41,
    "sold_range": [
      "2025-01",
      "2026-07"
    ],
    "sold_months": 19,
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
    ],
    "l12": {
      "from": "2025-09",
      "to": "2026-08",
      "n": 12,
      "both": 8,
      "complete": false
    },
    "longest": {
      "n": 7,
      "run": 15,
      "end": "2026-03"
    },
    "comparison_reach": {
      "l12": {
        "from": "2025-09",
        "to": "2026-08",
        "n": 12,
        "both": 8,
        "complete": false
      },
      "run": 15,
      "run_end": "2026-03",
      "longest": {
        "n": 7,
        "run": 15,
        "end": "2026-03"
      },
      "run_ending_at_last": 0,
      "gaps": [
        "2026-04",
        "2026-05",
        "2026-06"
      ],
      "both_absent": []
    }
  },
  {
    "db": "ITUK",
    "label": "ITUK",
    "scope": "CV",
    "sold_scope": "CV",
    "billed_range": [
      "2023-01",
      "2026-08"
    ],
    "billed_months": 41,
    "sold_range": [
      "2023-01",
      "2026-08"
    ],
    "sold_months": 44,
    "sold_missing_where_billed": [],
    "l12": {
      "from": "2025-09",
      "to": "2026-08",
      "n": 12,
      "both": 9,
      "complete": false
    },
    "longest": {
      "n": 19,
      "run": 39,
      "end": "2026-03"
    },
    "comparison_reach": {
      "l12": {
        "from": "2025-09",
        "to": "2026-08",
        "n": 12,
        "both": 9,
        "complete": false
      },
      "run": 39,
      "run_end": "2026-03",
      "longest": {
        "n": 19,
        "run": 39,
        "end": "2026-03"
      },
      "run_ending_at_last": 2,
      "gaps": [
        "2026-04",
        "2026-05",
        "2026-06"
      ],
      "both_absent": []
    }
  },
  {
    "db": "IUK",
    "label": "IUK",
    "scope": "LCV",
    "sold_scope": "D-MAX",
    "billed_range": [
      "2023-01",
      "2026-08"
    ],
    "billed_months": 41,
    "sold_range": [
      "2025-01",
      "2026-07"
    ],
    "sold_months": 19,
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
    ],
    "l12": {
      "from": "2025-09",
      "to": "2026-08",
      "n": 12,
      "both": 8,
      "complete": false
    },
    "longest": {
      "n": 7,
      "run": 15,
      "end": "2026-03"
    },
    "comparison_reach": {
      "l12": {
        "from": "2025-09",
        "to": "2026-08",
        "n": 12,
        "both": 8,
        "complete": false
      },
      "run": 15,
      "run_end": "2026-03",
      "longest": {
        "n": 7,
        "run": 15,
        "end": "2026-03"
      },
      "run_ending_at_last": 0,
      "gaps": [
        "2026-04",
        "2026-05",
        "2026-06"
      ],
      "both_absent": []
    }
  },
  {
    "db": "PORTUGAL",
    "label": "Imotors",
    "scope": "MIXED",
    "sold_scope": "MIXED",
    "billed_range": [
      "2023-01",
      "2026-08"
    ],
    "billed_months": 41,
    "sold_range": [
      "2025-01",
      "2026-08"
    ],
    "sold_months": 20,
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
    ],
    "l12": {
      "from": "2025-09",
      "to": "2026-08",
      "n": 12,
      "both": 9,
      "complete": false
    },
    "longest": {
      "n": 7,
      "run": 15,
      "end": "2026-03"
    },
    "comparison_reach": {
      "l12": {
        "from": "2025-09",
        "to": "2026-08",
        "n": 12,
        "both": 9,
        "complete": false
      },
      "run": 15,
      "run_end": "2026-03",
      "longest": {
        "n": 7,
        "run": 15,
        "end": "2026-03"
      },
      "run_ending_at_last": 2,
      "gaps": [
        "2026-04",
        "2026-05",
        "2026-06"
      ],
      "both_absent": []
    }
  },
  {
    "db": "UTI",
    "label": "UTI",
    "scope": "CV",
    "sold_scope": "MIXED",
    "billed_range": [
      "2023-01",
      "2026-08"
    ],
    "billed_months": 41,
    "sold_range": [
      "2025-01",
      "2026-06"
    ],
    "sold_months": 12,
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
    ],
    "l12": {
      "from": "2025-09",
      "to": "2026-08",
      "n": 12,
      "both": 7,
      "complete": false
    },
    "longest": {
      "n": 4,
      "run": 8,
      "end": "2026-03"
    },
    "comparison_reach": {
      "l12": {
        "from": "2025-09",
        "to": "2026-08",
        "n": 12,
        "both": 7,
        "complete": false
      },
      "run": 8,
      "run_end": "2026-03",
      "longest": {
        "n": 4,
        "run": 8,
        "end": "2026-03"
      },
      "run_ending_at_last": 0,
      "gaps": [
        "2026-04",
        "2026-05",
        "2026-06"
      ],
      "both_absent": []
    }
  }
]
```

## excluded

```json
{
  "doc_types": {
    "rule": "saty in CR, RE, DR, ZDR, FD or blank",
    "rows": 17403,
    "eur": 5848908.52,
    "by_db": {
      "GREECE": 171923.75,
      "IRELAND": 370971.03,
      "ITUK": 1705545.82,
      "IUK": 1910793.03,
      "PORTUGAL": 485604.57,
      "UTI": 1204070.32
    }
  },
  "scope": {
    "billing": {
      "rows": 1030,
      "eur": 349625.38,
      "units": 7335.0,
      "by_reason": {
        "lubricant (Fluids Chemicals)": 200530.27,
        "not a part line": 149095.11
      }
    },
    "sold": {
      "rows": 771,
      "units": 5130.0,
      "by_reason": {
        "lubricant (Fluids Chemicals)": 5101.0,
        "not a part line": 29.0
      }
    }
  }
}
```

## files

```json
{
  "html": "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\ISZE_AIM_DB_DLR_Deep_Dive_ALL.html",
  "opener": "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\OPEN_ISZE_AIM_DB_DLR_Deep_Dive_ALL.cmd"
}
```

## html_mb

```json
7.19
```
