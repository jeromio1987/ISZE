# 20260806T154433Z__alloc__t3pct

- **kind** alloc · **scenario** t3pct
- **utc** 2026-08-06T15:44:33.165117+00:00
- **config sha** `5df4359657d2d72a`
- **headline** target 3.0000% | base +3.41% | EUR 5,768,025 unbenchmarked takes +3.29% | theta moves 12 cells

## Allocation run

```
{
  "rows": 213,
  "base_eur": 5768025.0,
  "delta_base": 0.03405991305544376,
  "weighted_increase": 0.03000000000028189,
  "revenue_delta_eur": 173040.75000162597,
  "n_capped": 0,
  "n_floored": 0,
  "n_zero_evidence": 213,
  "n_unbenchmarked_premium": 213,
  "n_theta_unwired": 0,
  "n_theta_moving": 12
}
```

### By reason code

| reason_code      |   cells |    base_eur |   mean_delta |   rev_delta |
|:-----------------|--------:|------------:|-------------:|------------:|
| NO_EVIDENCE_HOLD |     213 | 5.76802e+06 |       0.0329 |      173041 |


### Momentum (theta_parc)

```
{
  "theta_source": "UIO_carpark_for_GPS_recalc_2026-07-30.csv",
  "n_cells": 213,
  "n_unmatched": 0,
  "n_gated": 189,
  "eur_gated": 3367790.0,
  "weighted_theta_parc": 1.0130307451010023,
  "by_bucket": {
    "declining": 1170884.0,
    "stable": 4597141.0
  },
  "by_basis": {
    "uio_cohort_model": 1229351.0,
    "uio_constant_hazard": 2740620.0,
    "uio_known_defect": 627170.0,
    "uio_locked": 1170884.0
  },
  "components_wired": "theta_parc only (interval blocked, cohort/warranty partial)"
}
```

|                                   |   cells |         base_eur |   theta |   d_theta |   mean_delta |
|:----------------------------------|--------:|-----------------:|--------:|----------:|-------------:|
| ('declining', 'uio_locked')       |      12 |      1.17088e+06 |  0.9402 |     -0.02 |       0.0141 |
| ('stable', 'uio_cohort_model')    |      12 |      1.22935e+06 |  1.0483 |      0    |       0.0341 |
| ('stable', 'uio_constant_hazard') |     178 |      2.74062e+06 |  1.0218 |      0    |       0.0341 |
| ('stable', 'uio_known_defect')    |      11 | 627170           |  1.0447 |      0    |       0.0341 |