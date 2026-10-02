# Verification - PORTUGAL

Built 2026-10-02T07:15:00+00:00. 17 of 17 gating checks pass.

## All checks

| Check | Expected | Actual | Result | Note |
|---|---|---|---|---|
| month rows equal the total row: dealer_sellout_long_PORTUGAL_CY2025.csv | 51363.0 | 51363.0 | PASS |  |
| month rows equal the total row: dealer_sellout_long_PORTUGAL_CY2026YTD.csv | 39790.0 | 39790.0 | PASS |  |
| Sold to dealer units, month rows, Jan-Dec 2025 | 51363 | 51363.0 | PASS | supersession off, as the spec requires; matches the I Motors deck exactly. After the lubricant and non-part rule of section 2.4 the same figure is 50,750 (-613), because the deck it came from did not apply that rule. |
| Sold to dealer units, month rows, Jan-Aug 2026 | 39790 | 39790.0 | PASS | supersession off, as the spec requires; matches the I Motors deck exactly. After the lubricant and non-part rule of section 2.4 the same figure is 39,252 (-538), because the deck it came from did not apply that rule. |
| Billed units FY2026 (Apr 2025 - Mar 2026), brake pad | 1370 | 1370.0 | PASS | supersession off; the lubricant and non-part rule moves it by nothing |
| Billed units FY2026, oil filter | 2743 | 2743.0 | PASS | supersession off; the lubricant and non-part rule moves it by nothing |
| Billed units FY2026, brake shoe | 348 | 348.0 | PASS | supersession off; the lubricant and non-part rule moves it by nothing |
| Sold to dealer units FY2026, brake pad | 994 | 994.0 | PASS | supersession off; the lubricant and non-part rule moves it by nothing |
| Sold to dealer units FY2026, oil filter | 3694 | 3694.0 | PASS | supersession off; the lubricant and non-part rule moves it by nothing |
| Sold to dealer units FY2027 Apr-Aug, brake pad | 406 | 406.0 | PASS | supersession off; the lubricant and non-part rule moves it by nothing |
| Portugal: effect of the section 2.4 scope rule on the eight deck figures | reported, not a gate | 1151.0 | reported | reported, not a gate |
| Portugal: what the supersession mapping of section 4.2 moves, billing FY2026 | reported, not a gate | clutch_kit 288 to 336 (+48); brake_pad 1,370 to 1,370 (+0); oil_filter 2,743 to 2,743 (+0); brake_shoe 348 to 348 (+0) | PASS | The mapping rolls an old part number into its newest number before the AIM tree and the price are looked up, which section 4.2 requires. It moves clutch_kit on these four families. Where it moves a family, the page shows the mapped figure; the I Motors deck it is checked against did not apply the mapping. |
| comparison offered exactly when 2N contiguous months exist: PORTUGAL | offered on a window that sits inside the run | cannot carry it (longest unbroken both-stage run 15 months ending 2026-03; longest comparison 7 against 7); on the last-12 window ending 2026-08: withheld; on a 12-month window ending 2026-03: withheld | PASS | the gate is 'both windows inside one unbroken both-stage run', exactly as the page applies it. The break at Apr-Jun 2026 sits inside every span ending 2026-08, so on the window the page lands on nobody is offered one; ITUK gets it as soon as the window ends at 2026-03 or earlier. No shorter comparison is offered as a fallback anywhere |
| last-12-month window: both-stage coverage per distributor | reported, not a gate | PORTUGAL 9/12 | PASS | months of the last twelve that carry billing AND sales to dealer |
| longest contiguous both-stage run, per distributor | reported, not a gate | PORTUGAL 15 months ending 2026-03 | PASS | contiguity is measured, not inferred; the breaks are the months whose billing rows all carry a blank document type |
| distributors that can carry a 12-versus-12 comparison at all | reported, not a gate | none | PASS | ITUK is the only one whose unbroken both-stage run reaches 24 months; everybody else is withheld, with no shorter fallback offered |
| billed: units not classified in AIM | None | 2.68 | reported | reported, not a gate |
| billed: units with no price on the list | None | 0.03 | reported | reported, not a gate |
| sold: units not classified in AIM | None | 6.28 | reported | reported, not a gate |
| sold: units with no price on the list | None | 4.16 | reported | reported, not a gate |
| PMS cover above 100% carries a warning in the page | every instance flagged | None | PASS | the page marks every percentage above 100% with a warning and a reason |
| HTML file size | under 15 MB for run 2 | 1.74 | PASS | MB, self-contained: data and Chart.js inline, no treemap plugin since that chart was removed, no server and no internet needed |

## coverage

```json
[
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
  }
]
```

## excluded

```json
{
  "doc_types": {
    "rule": "saty in CR, RE, DR, ZDR, FD or blank",
    "rows": 2895,
    "eur": 485604.57,
    "by_db": {
      "PORTUGAL": 485604.57
    }
  },
  "scope": {
    "billing": {
      "rows": 293,
      "eur": 87551.2,
      "units": 2335.0,
      "by_reason": {
        "lubricant (Fluids Chemicals)": 69535.86,
        "not a part line": 18015.34
      }
    },
    "sold": {
      "rows": 131,
      "units": 1151.0,
      "by_reason": {
        "lubricant (Fluids Chemicals)": 1140.0,
        "not a part line": 11.0
      }
    }
  }
}
```

## files

```json
{
  "html": "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.html",
  "opener": "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\02_dashboards\\sales\\OPEN_ISZE_AIM_DB_DLR_Deep_Dive_PORTUGAL.cmd"
}
```

## aim_tree

```json
{
  "file": "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\01_data\\00_derived\\AIM_Master_PN_Categories_Figkey_release_2026-10-02.csv",
  "release": {
    "release_id": "2026-10-02",
    "path": "aim_pn_classification_release_2026-10-02.csv",
    "sha256": "0ac9137903a326430c68e4d619fa4f836a796a01d9d40f6f6f1183e7d4c52360",
    "status": "APPROVED",
    "rows": 164916,
    "rows_note": "data rows, header excluded (the two earlier entries record 164908 = 164,907 data rows + header)",
    "source": "catalogue tree: aim_pn_classification_release_2026-09-20.csv; AIM labels: aim_pn_classification_20260920.csv per level, aim_master_v2.csv where blank (the live page export's rule)",
    "recommendation": "00_docs/AIM_RELEASE_RETEST_2026-09-25.md s7 item 4; Jerome decisions 2026-10-02 (keep Filter element leaf; side sills to Panels > Panel; cut a new release)",
    "notes": "Cut 2026-10-02 by claude-opus. Adds the 24 Sep AIM work, the side-sill decision, the 8980913940 air-filter catalogue fix and both lubricant key forms; change log aim_pn_classification_release_2026-10-02.changes.csv. Supersedes the 2026-09-24-candidate as the thing to approve. Bookkeeping: that candidate's recorded sha256 e5824683... is the hash of aim_pn_classification_20260920.csv.bak_pre_cab_class_20260924_192113, not of its recorded path (now 092e9815...); its entry was left unchanged because sha256 is the identity field the gate matches on.",
    "approved_by": "Jerome",
    "approved_on": "2026-10-02",
    "approved_note": "Jerome approved release 2026-10-02 in chat on 2026-10-02. sha256 re-verified against this register immediately before the status change. Candidate gate (aim_pn_classification_release_2026-10-02.candidate_gate_2026-10-02.json): 18 checks pass, release_approved PENDING, 0 fail, with pr00_copy_integrity measured against the pinned 20 Sep pr00 reference pr00_classification_reference_20260920.csv (git c813330f, sha256 98e64b5b...), Jerome decision 2026-10-02, because today's pr00 carries the 21 Sep regression (1,660 rows). Lubricant relabel accepted (Shell keys to Fluids Chemicals > Lubricants; 9-digit keys line_kind lubricant_or_tool). Supersedes 2026-09-20 in the same edit.",
    "pr00_reference": {
      "file": "pr00_classification_reference_20260920.csv",
      "sha256": "98e64b5bdaef73819cf954ce96241f1a9b49d8fbd998d02700ae8494028bea34",
      "source": "git c813330f"
    }
  }
}
```

## html_mb

```json
1.74
```
