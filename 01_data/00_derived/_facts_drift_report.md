# FACTS drift report

**Checked:** 2026-09-22T19:45:53Z
**Snapshot as-of:** 2026-09-22T19:42:18Z

| Anchor | FACTS value | Pipeline value | Drift | Status |
|---|---|---|---|---|
| sales.parts_base_eur | 1.17601e+08 | 1.17601e+08 | 0.00% | ok |
| sales.parts_base_through_prior_quarter_eur | 1.03574e+08 | 1.12089e+08 | 8.22% | DRIFT |
| ituk.oil_filter.2023.total.capture_uncapped_pct | 154.4 | 104.3 | 32.45% | DRIFT |
| ituk.oil_filter.2024.total.capture_uncapped_pct | 83.5 | 56.4 | 32.46% | DRIFT |
| ituk.oil_filter.2025.total.capture_uncapped_pct | 116.4 | 78.7 | 32.39% | DRIFT |
| ituk.oil_filter.2024.genuine.capture_uncapped_pct | 62.1 | 42 | 32.37% | DRIFT |
| ituk.oil_filter.2025.genuine.capture_uncapped_pct | 87.6 | 59.2 | 32.42% | DRIFT |
| ituk.oil_filter.uio_units | 23068 | 23068 | 0.00% | ok |
| ituk.oil_filter.expected_qty | 11680.2 | 17285.6 | 47.99% | DRIFT |
| mix.ITUK.genuine_share_eur_pct_2025 | 97.3 | 97.3 | 0.00% | ok |
| mix.UTI.genuine_share_eur_pct_2025 | 88.9 | 88.9 | 0.00% | ok |
| waterfall.network.gps_pct_2025 | 56.6 | 56.6 | 0.00% | ok |
| verify.fail | 0 | 0 | 0.00% | ok |

**Result: DRIFT DETECTED** — 7 drifted, 0 missing, 6 aligned.

On DRIFT: decide which side is right. If the pipeline changed legitimately, update FACTS.md **and** facts_anchor.yaml together, then re-export Data/gpt_safe. Never leave them disagreeing.