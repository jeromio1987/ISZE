# FACTS drift report

**Checked:** 2026-08-03T06:18:30Z
**Snapshot as-of:** 2026-08-03T06:18:29Z

| Anchor | FACTS value | Pipeline value | Drift | Status |
|---|---|---|---|---|
| sales.parts_base_eur | 1.03574e+08 | 1.03574e+08 | 0.00% | ok |
| ituk.oil_filter.2023.total.capture_uncapped_pct | 154.4 | 154.4 | 0.00% | ok |
| ituk.oil_filter.2024.total.capture_uncapped_pct | 83.5 | 83.5 | 0.00% | ok |
| ituk.oil_filter.2025.total.capture_uncapped_pct | 116.4 | 116.4 | 0.00% | ok |
| ituk.oil_filter.2024.genuine.capture_uncapped_pct | 62.1 | 62.1 | 0.00% | ok |
| ituk.oil_filter.2025.genuine.capture_uncapped_pct | 87.6 | 87.6 | 0.00% | ok |
| ituk.oil_filter.uio_units | 23068 | 23068 | 0.00% | ok |
| ituk.oil_filter.expected_qty | 11680.2 | 11680.2 | 0.00% | ok |
| mix.ITUK.genuine_share_eur_pct_2025 | 97.3 | 97.3 | 0.00% | ok |
| mix.UTI.genuine_share_eur_pct_2025 | 88.9 | 88.9 | 0.00% | ok |
| waterfall.network.gps_pct_2025 | 51.1 | 51.1 | 0.00% | ok |
| verify.fail | 0 | 0 | 0.00% | ok |

**Result: ALIGNED** — 0 drifted, 0 missing, 12 aligned.

On DRIFT: decide which side is right. If the pipeline changed legitimately, update FACTS.md **and** facts_anchor.yaml together, then re-export Data/gpt_safe. Never leave them disagreeing.