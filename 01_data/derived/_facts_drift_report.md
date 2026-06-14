# FACTS drift report

**Checked:** 2026-06-12T17:27:51Z
**Snapshot as-of:** 2026-06-12T17:27:50Z

| Anchor | FACTS value | Pipeline value | Drift | Status |
|---|---|---|---|---|
| sales.parts_base_eur | 9.42622e+07 | 9.42622e+07 | 0.00% | ok |
| ituk.oil_filter.2023.total.capture_uncapped_pct | 217.1 | 217.1 | 0.00% | ok |
| ituk.oil_filter.2024.total.capture_uncapped_pct | 120.9 | 120.9 | 0.00% | ok |
| ituk.oil_filter.2025.total.capture_uncapped_pct | 162.1 | 162.1 | 0.00% | ok |
| ituk.oil_filter.2024.genuine.capture_uncapped_pct | 89.4 | 89.4 | 0.00% | ok |
| ituk.oil_filter.2025.genuine.capture_uncapped_pct | 120 | 120 | 0.00% | ok |
| ituk.oil_filter.uio_units | 22389 | 22389 | 0.00% | ok |
| ituk.oil_filter.expected_qty | 7836.1 | 7836.1 | 0.00% | ok |
| mix.ITUK.genuine_share_eur_pct_2025 | 97.3 | 97.3 | 0.00% | ok |
| mix.UTI.genuine_share_eur_pct_2025 | 88.9 | 88.9 | 0.00% | ok |
| waterfall.network.gps_pct_2025 | 40.2 | 50.2 | 24.88% | DRIFT |
| verify.fail | 0 | 0 | 0.00% | ok |

**Result: DRIFT DETECTED** — 1 drifted, 0 missing, 11 aligned.

On DRIFT: decide which side is right. If the pipeline changed legitimately, update FACTS.md **and** facts_anchor.yaml together, then re-export Data/gpt_safe. Never leave them disagreeing.