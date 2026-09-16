# 20260810T170454Z__alloc__t3pct

- **kind** alloc · **scenario** t3pct
- **utc** 2026-08-10T17:04:54.000490+00:00
- **config sha** `d34778727e499e7c`
- **headline** target 3.0000% | base +6.51% | EUR 1,373,506 unbenchmarked takes +6.43% | theta moves 60 cells | db_dlr proxy flags 0

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
  "n_unbenchmarked_premium": 107,
  "n_theta_vetoed": 10,
  "n_theta_unwired": 0,
  "n_theta_moving": 60,
  "db_dlr_soft": {
    "wired": true,
    "measure_kind": "proxy",
    "price_basis": "ASP_list_passthrough",
    "joined_to_deltas": false,
    "n_cells_flagged_adverse": 0,
    "n_cells_with_proxy": 2,
    "n_cells_with_list_shock": 3,
    "note": "Soft diagnostic only. ASP/list pass-through proxy \u2014 not dealer invoice elasticity. Do not treat beta as an allocation coefficient.",
    "adverse_beta_threshold": -0.5
  }
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


### DB→DLR response soft signal (ITUK/UTI proxy)
```
{
  "wired": true,
  "measure_kind": "proxy",
  "price_basis": "ASP_list_passthrough",
  "joined_to_deltas": false,
  "n_cells_flagged_adverse": 0,
  "n_cells_with_proxy": 2,
  "n_cells_with_list_shock": 3,
  "note": "Soft diagnostic only. ASP/list pass-through proxy \u2014 not dealer invoice elasticity. Do not treat beta as an allocation coefficient.",
  "adverse_beta_threshold": -0.5
}
```
Labeled **proxy** only (ASP / list pass-through). Not joined into allocation deltas. UTI ≠ UMI.

#### Cross-section proxies (all AIM + PMS cats)

```
distributor_code                     category  n_pns   beta  low_power                                                                reading
            ITUK             AIM: Lubrication     15 -2.121       True higher ASP ↔ lower sell-out qty (contestable / price-sensitive signal)
            ITUK                 AIM: Unknown     36 -1.012      False higher ASP ↔ lower sell-out qty (contestable / price-sensitive signal)
            ITUK              AIM: Wheels Hub    100 -0.640      False higher ASP ↔ lower sell-out qty (contestable / price-sensitive signal)
            ITUK           AIM: Chassis Frame    185 -0.523      False higher ASP ↔ lower sell-out qty (contestable / price-sensitive signal)
            ITUK     AIM: Maintenance Service     38 -0.479      False                                        weak negative level association
            ITUK              AIM: Suspension     46 -0.425      False                                        weak negative level association
            ITUK            AIM: Transmission     90 -0.410      False                                        weak negative level association
            ITUK       AIM: Competitive parts    107 -0.346      False                                        weak negative level association
            ITUK                  AIM: Engine     50 -0.299      False                                        weak negative level association
            ITUK                AIM: Steering     46 -0.282      False                                        weak negative level association
            ITUK          AIM: Driveline Axle     14 -0.273       True                                        weak negative level association
            ITUK          AIM: Accident parts     36 -0.238      False                                        weak negative level association
            ITUK             AIM: Fuel System     41 -0.227      False                                        weak negative level association
            ITUK              AIM: Electrical    126 -0.166      False                                        weak negative level association
            ITUK           AIM: Body Exterior    150 -0.077      False                                        weak negative level association
            ITUK            AIM: Repair parts     62  0.024      False               no negative level association (size/mix confound likely)
            ITUK  AIM: Hardware & consumables     73  0.028      False               no negative level association (size/mix confound likely)
            ITUK                 AIM: Cooling     15  0.042       True               no negative level association (size/mix confound likely)
            ITUK AIM: Intake Exhaust Emission     76  0.043      False               no negative level association (size/mix confound likely)
            ITUK       AIM: High value repair     26  0.061      False               no negative level association (size/mix confound likely)
            ITUK          AIM: Cabin Interior     22  0.120      False               no negative level association (size/mix confound likely)
            ITUK        AIM: Fluids Chemicals      8  0.235       True               no negative level association (size/mix confound likely)
            ITUK                  AIM: Brakes     50  0.337      False               no negative level association (size/mix confound likely)
            ITUK                  fuel_filter     16  0.541       True               no negative level association (size/mix confound likely)
            ITUK                   air_filter      9  1.567       True               no negative level association (size/mix confound likely)
             UTI              AIM: Wheels Hub     50 -0.651      False higher ASP ↔ lower sell-out qty (contestable / price-sensitive signal)
             UTI          AIM: Accident parts     13 -0.505       True higher ASP ↔ lower sell-out qty (contestable / price-sensitive signal)
             UTI           AIM: Body Exterior     84 -0.405      False                                        weak negative level association
             UTI                AIM: Steering     12 -0.381       True                                        weak negative level association
             UTI       AIM: Competitive parts     28 -0.345      False                                        weak negative level association
             UTI           AIM: Chassis Frame     21 -0.308      False                                        weak negative level association
             UTI            AIM: Transmission     22 -0.294      False                                        weak negative level association
             UTI             AIM: Fuel System     23 -0.224      False                                        weak negative level association
             UTI                  AIM: Engine     13 -0.178       True                                        weak negative level association
             UTI  AIM: Hardware & consumables     17 -0.160       True                                        weak negative level association
             UTI              AIM: Electrical     43 -0.141      False                                        weak negative level association
             UTI                  AIM: Brakes     14 -0.130       True                                        weak negative level association
             UTI              AIM: Suspension      9 -0.108       True                                        weak negative level association
             UTI     AIM: Maintenance Service     19  0.034       True               no negative level association (size/mix confound likely)
             UTI            AIM: Repair parts     27  0.061      False               no negative level association (size/mix confound likely)
             UTI AIM: Intake Exhaust Emission     22  0.200      False               no negative level association (size/mix confound likely)
             UTI                 AIM: Unknown     17  0.422       True               no negative level association (size/mix confound likely)
```
