# 20260809T040959Z__alloc__t3pct

- **kind** alloc · **scenario** t3pct
- **utc** 2026-08-09T04:09:59.423981+00:00
- **config sha** `e3afd7065c5eab84`
- **headline** target 3.0000% | base +3.51% | EUR 5,768,025 unbenchmarked takes +3.44% | theta moves 60 cells

## Allocation run

```
{
  "rows": 213,
  "base_eur": 5768025.0,
  "delta_base": 0.03512061234096109,
  "weighted_increase": 0.02999999999964842,
  "revenue_delta_eur": 173040.74999797207,
  "n_capped": 0,
  "n_floored": 0,
  "n_zero_evidence": 213,
  "n_unbenchmarked_premium": 213,
  "n_theta_vetoed": 10,
  "n_theta_unwired": 0,
  "n_theta_moving": 60
}
```

### By reason code

| reason_code      |   cells |    base_eur |   mean_delta |   rev_delta |
|:-----------------|--------:|------------:|-------------:|------------:|
| NO_EVIDENCE_HOLD |     213 | 5.76802e+06 |       0.0344 |      173041 |


### Momentum (theta_parc)

```
{
  "theta_source": "UIO_carpark_for_GPS_recalc_2026-07-30.csv",
  "n_cells": 213,
  "n_unmatched": 0,
  "n_gated": 11,
  "eur_gated": 627170.0,
  "weighted_theta_parc": 1.0130307451010023,
  "by_bucket": {
    "declining": 1748879.0,
    "growing": 588979.0,
    "stable": 3430167.0
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

|                                      |   cells |         base_eur |   theta |   d_theta |   mean_delta |
|:-------------------------------------|--------:|-----------------:|--------:|----------:|-------------:|
| ('declining', 'uio_constant_hazard') |      21 | 577995           |  0.9276 |   -0.02   |       0.0151 |
| ('declining', 'uio_locked')          |      12 |      1.17088e+06 |  0.9402 |   -0.02   |       0.0151 |
| ('growing', 'uio_constant_hazard')   |      27 | 588979           |  1.1508 |    0.0189 |       0.054  |
| ('stable', 'uio_cohort_model')       |      12 |      1.22935e+06 |  1.0483 |    0      |       0.0351 |
| ('stable', 'uio_constant_hazard')    |     130 |      1.57365e+06 |  1.0102 |    0      |       0.0351 |
| ('stable', 'uio_known_defect')       |      11 | 627170           |  1.0447 |    0      |       0.0351 |