# FACTS drift report

**Checked:** 2026-09-24T06:05:24Z
**Snapshot as-of:** 2026-09-24T06:00:26Z

| Anchor | FACTS value | Pipeline value | Drift | Status |
|---|---|---|---|---|
| sales.parts_base_eur | 1.17601e+08 | 1.17601e+08 | 0.00% | ok |
| sales.parts_base_through_prior_quarter_eur | 1.12089e+08 | 1.12089e+08 | 0.00% | ok |
| ituk.oil_filter.2023.total.capture_uncapped_pct | 104.3 | 104.3 | 0.00% | ok |
| ituk.oil_filter.2024.total.capture_uncapped_pct | 56.4 | 56.4 | 0.00% | ok |
| ituk.oil_filter.2025.total.capture_uncapped_pct | 78.7 | 78.7 | 0.00% | ok |
| ituk.oil_filter.2024.genuine.capture_uncapped_pct | 42 | 42 | 0.00% | ok |
| ituk.oil_filter.2025.genuine.capture_uncapped_pct | 59.2 | 59.2 | 0.00% | ok |
| ituk.oil_filter.uio_units | 23068 | 23068 | 0.00% | ok |
| ituk.oil_filter.expected_qty | 17285.6 | 17285.6 | 0.00% | ok |
| mix.ITUK.genuine_share_eur_pct_2025 | 97.3 | 97.3 | 0.00% | ok |
| mix.UTI.genuine_share_eur_pct_2025 | 88.9 | 88.9 | 0.00% | ok |
| waterfall.network.gps_pct_2025 | 56.5 | 56.5 | 0.00% | ok |
| verify.fail | 0 | 0 | 0.00% | ok |

**Result: ALIGNED** — 0 drifted, 0 missing, 13 aligned.

On DRIFT: decide which side is right. If the pipeline changed legitimately, update FACTS.md **and** facts_anchor.yaml together, then re-export Data/gpt_safe. Never leave them disagreeing.