# 20260810T161318Z__alloc__t3pct

- **kind** alloc · **scenario** t3pct
- **utc** 2026-08-10T16:13:18.584584+00:00
- **config sha** `8f0ef974dd89ce95`
- **headline** target 3.0000% | base +6.51% | EUR 1,373,506 unbenchmarked takes +6.43% | theta moves 60 cells

## Allocation run

```
{
  "rows": 213,
  "base_eur": 5768025.0,
  "delta_base": 0.06514140628178211,
  "weighted_increase": 0.030000000000036622,
  "revenue_delta_eur": 173040.75000021124,
  "n_capped": 17,
  "n_floored": 0,
  "n_zero_evidence": 125,
  "n_unbenchmarked_premium": 125,
  "n_theta_vetoed": 10,
  "n_theta_unwired": 0,
  "n_theta_moving": 60
}
```

### By reason code

```
                        cells   base_eur  mean_delta   rev_delta
reason_code                                                     
CAPTIVE_RAISE              26  1554283.0      0.0636  98306.5004
CONTESTED_ABOVE_MARKET     22  1117220.0      0.0033   2774.7019
DEFEND_CUT                 40  1723016.0     -0.0004 -12454.1147
NO_EVIDENCE_HOLD          125  1373506.0      0.0643  84413.6624
```


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

```
                                  cells   base_eur   theta  d_theta  mean_delta
theta_bucket theta_basis                                                       
declining    uio_constant_hazard     21   577995.0  0.9276  -0.0200      0.0223
             uio_locked              12  1170884.0  0.9402  -0.0200      0.0201
growing      uio_constant_hazard     27   588979.0  1.1508   0.0189      0.0634
stable       uio_cohort_model        12  1229351.0  1.0483   0.0000      0.0601
             uio_constant_hazard    130  1573646.0  1.0102   0.0000      0.0462
             uio_known_defect        11   627170.0  1.0447   0.0000      0.0542
```