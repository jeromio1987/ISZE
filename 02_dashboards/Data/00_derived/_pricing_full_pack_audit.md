# Pricing full pack audit

- **Verdict:** PASS_WITH_CAVEATS
- **Built / audited (UTC):** 2026-08-11T06:25:15Z
- **Integrity score (pack):** 48/100 (weak)
- **HTML:** `02_dashboards/pricing/ISZE_Pricing_Full_Analysis_Pack.html`
- **FAIL count:** 0 · **CAVEAT count:** 1

## Checks

| Status | Check | Detail |
|---|---|---|
| PASS | HTML exists | ISZE_Pricing_Full_Analysis_Pack.html (42,974 bytes) |
| PASS | HTML not stub | size=42974 |
| PASS | Meta JSON exists | C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pricing_full_analysis_pack.meta.json |
| PASS | CY2025 parts € match | recompute=33,707,573.78 meta=33707573.78 |
| PASS | CY2025 coverage match | recompute=84.12 meta=84.12 |
| PASS | CY2025 realization match | recompute=95.95 meta=95.95 |
| PASS | NO_LIST € vs ranked CSV | csv_sum=4,955,737 meta=4,955,737 |
| PASS_WITH_CAVEAT | NO_LIST vs realization no_list (order of magnitude) | ranked=4,955,737 recompute_nolist=5,351,223 (ranked file may use stricter usable-price rule — caveat if within 15%) |
| PASS | ZPR1 UTI 2025 vs PR00 median | recompute=-10.61 meta=-10.61 |
| PASS | ZPR1 UMI 2025 vs PR00 median | recompute=-15.28 meta=-15.28 |
| PASS | ZPR1 UTI 2026 vs PR00 median | recompute=-13.92 meta=-13.92 |
| PASS | ZPR1 UMI 2026 vs PR00 median | recompute=-5.24 meta=-5.24 |
| PASS | UMI YoY 25→26 | recompute=20.19 meta=20.19 |
| PASS | UTI YoY 25→26 | recompute=8.21 meta=8.21 |
| PASS | UTI≠UMI never blended | blended_hit=False separation_language=True |
| PASS | PMS total-primary headline | meta.primary=total total_in_html=True genuine_headline=False |
| PASS | Integrity score = 100 − deductions | score=48 expected=48 deduction_sum=52 meta_sum=52 |
| PASS | Integrity band matches score | score=48 band=weak |
| PASS | External quotability false | False |
| PASS | HTML contains CY2025 coverage | looked for 84.1% |
| PASS | HTML contains CY2025 realization | looked for 96.0% |
| PASS | HTML contains integrity score | score=48 |
| PASS | HTML € formatting (no raw+ M) | bad_samples=[] |
| PASS | shared language (no IML v7 / Model B) | scanned |
| PASS | PRISM verification green | {'pass': 106, 'warn': 0, 'fail': 0, 'ok': True} |
| PASS | Pack separates green verification from list-to-pocket | provisional language + verification note present |
| PASS | GPS UTI≠UMI values distinct | UTI=322 UMI=179 |

## Recompute anchors (CY2025)

```
{
  "parts_eur": 33707573.78,
  "matched_eur": 28356351.0,
  "no_list_eur": 5351222.78,
  "coverage_pct": 84.12,
  "realization_pct": 95.95,
  "list_value_eur": 29552482.8
}
```

## ZPR1 recompute

```
{
  "UTI_2025": -10.61,
  "UMI_2025": -15.28,
  "UTI_2026": -13.92,
  "UMI_2026": -5.24,
  "UTI_yoy_25_26": 8.21,
  "UMI_yoy_25_26": 20.19
}
```

## Notes

- PMS headline must remain **total** capture; genuine/BVP is extra.
- UTI and UMI must never be blended.
- List-to-pocket remains provisional even when PRISM verification is green.
- Send allowed only after PASS or PASS_WITH_CAVEATS, and only to Jerome self mailbox.
