# 20260806T154452Z__launch__dmax_22_base

- **kind** launch · **scenario** dmax_22_base
- **utc** 2026-08-06T15:44:52.748840+00:00
- **config sha** `1989b92c8abb17c9`
- **headline** dmax_22: best tactic 'warranty_load' NPV GP EUR 72,752,723

## D-Max 2.2L (RG21 / RZ4F-TC, SCR, Euro 6d/7)

Spec confirmed: **True** — 00_docs/ISZE_ROADMAP.md LCV bucket item, 4 OEM schedules read 2026-07-15

Services/vehicle/yr: 1.33 (20,000 km / 15,000 km interval)


### Scenario comparison (10y discounted GP)

| scenario      | fork   | label                                                 |   revenue_10y |   rev_warranty_10y |   gp_npv |   gp_npv_wear |   gp_npv_captive |   gp_npv_new_parts |   gp_npv_carryover |   capture_y10_wear |   capture_y10_captive |   captive_index_y10 |   vs_class_only |   vs_class_only_pct |
|:--------------|:-------|:------------------------------------------------------|--------------:|-------------------:|---------:|--------------:|-----------------:|-------------------:|-------------------:|-------------------:|----------------------:|--------------------:|----------------:|--------------------:|
| warranty_load | base   | Load the warranty phase, then freeze captive (Jerome) |     163789371 |           89589577 | 72752723 |       3620000 |         69132723 |           36172899 |           36579824 |              0.232 |                 0.524 |               1.928 |        17920449 |                32.7 |
| split         | base   | Habit on wear, harvest on captive                     |     164834378 |           89762852 | 72646584 |       3620000 |         69026584 |           36251535 |           36395049 |              0.232 |                 0.491 |               2.131 |        17814310 |                32.5 |
| harvest       | base   | Harvest the monopoly window                           |     153737057 |           82961537 | 66252669 |       4415423 |         61837246 |           32619332 |           33633337 |              0.169 |                 0.523 |               1.961 |        11420395 |                20.8 |
| split_freeze  | base   | Split, then hold captive flat once warranty ends      |     153338059 |           83018278 | 65733676 |       3620000 |         62113676 |           32575174 |           33158502 |              0.232 |                 0.549 |               1.785 |        10901402 |                19.9 |
| class_only    | base   | Baseline - class factor as issued, no ISZE adjustment |     137601490 |           72140470 | 54832274 |       3920451 |         50911823 |           26661990 |           28170284 |              0.194 |                 0.57  |               1.705 |               0 |                 0   |
| habit         | base   | Buy the dealer habit before IAM arrives               |     138350656 |           71985695 | 54531823 |       3620000 |         50911823 |           26547312 |           27984511 |              0.232 |                 0.57  |               1.705 |         -300451 |                -0.5 |


### Price book — recommended scenario

| pn          | description                   | role    | part_class   |   sp_class_implied |   sp_launch |   price_y10 |   gp_pct_launch |   index_launch |   index_y10 |   revenue_warranty_10y |   gp_npv |
|:------------|:------------------------------|:--------|:-------------|-------------------:|------------:|------------:|----------------:|---------------:|------------:|-----------------------:|---------:|
| TBD-OF-22   | ELEMENT; OIL FILTER           | wear    | C            |               6.8  |        5.78 |        7.54 |          0.4471 |          0.839 |       1.095 |                  64216 |   566444 |
| TBD-FF-22   | ELEMENT KIT; FUEL FILTER      | wear    | C            |              13.86 |       11.78 |       15.37 |          0.4471 |          2.003 |       2.613 |                  65434 |   157861 |
| TBD-AF-22   | FILTER; ACL                   | wear    | C            |              21.19 |       18.01 |       23.5  |          0.4471 |          1.289 |       1.682 |                 100052 |   639875 |
| TBD-CF-22   | FILTER; BLOWER UNIT           | wear    | C            |              16.36 |       13.9  |       18.14 |          0.4471 |          3.531 |       4.607 |                  77227 |   153034 |
| TBD-UF-22   | FILTER; UREA / DEF            | wear    | D            |              24.46 |       20.79 |       27.13 |          0.4353 |          0.85  |       0.85  |                  38492 |   336800 |
| TBD-BPF-22  | PAD KIT; CALIPER DISC BRK FRT | wear    | F            |              70.7  |       60.09 |       78.41 |          0.3824 |          1.796 |       2.344 |                 182052 |   523950 |
| TBD-BPR-22  | PAD KIT; CALIPER DISC BRK RR  | wear    | F            |              59.16 |       50.28 |       65.61 |          0.3824 |          1.726 |       2.252 |                 111708 |   333906 |
| TBD-BRF-22  | ROTOR; DISC BRK FRT           | wear    | F            |              73.58 |       62.55 |       81.61 |          0.3824 |          1.269 |       1.656 |                 104215 |   605272 |
| TBD-BLT-22  | BELT; DRIVE                   | wear    | C            |              19.34 |       16.44 |       21.45 |          0.4471 |          1.63  |       2.127 |                  21913 |    80591 |
| TBD-CLD-22  | DISC; CLUTCH                  | wear    | J            |             126.25 |      107.31 |      140.02 |          0.3471 |          2.016 |       2.631 |                 111751 |   222267 |
| TBD-DPF-22  | DPD / DPF ASM                 | captive | P            |            1446.1  |     1952.24 |     2133.27 |          0.6741 |          4.482 |       4.898 |               24048130 | 12788671 |
| TBD-SCR-22  | CATALYST ASM; SCR             | captive | P            |            1222.3  |     1650.11 |     1803.12 |          0.6741 |          1.35  |       1.131 |               12703997 | 11996580 |
| TBD-NOX1-22 | SENSOR; NOX UPSTREAM          | captive | P            |             266.84 |      360.23 |      393.64 |          0.6741 |          1.35  |       1.131 |                5916603 |  5587140 |
| TBD-NOX2-22 | SENSOR; NOX DOWNSTREAM        | captive | P            |             253.93 |      342.8  |      374.59 |          0.6741 |          1.35  |       1.131 |                4967926 |  4691289 |
| TBD-DEFP-22 | PUMP ASM; DEF                 | captive | P            |             499.25 |      673.99 |      736.48 |          0.6741 |          1.35  |       1.131 |                8302331 |  7840019 |
| TBD-DEFI-22 | INJECTOR; DEF                 | captive | P            |             206.59 |      278.89 |      304.75 |          0.6741 |          1.35  |       1.131 |                3435447 |  3244146 |
| TBD-DEFL-22 | SENSOR; DEF LEVEL / QUALITY   | captive | D            |             205.15 |      276.95 |      302.64 |          0.6444 |          1.35  |       1.131 |                2729272 |  2476925 |
| TBD-EGR-22  | VALVE; EGR                    | captive | P            |             288.36 |      389.29 |      425.38 |          0.6741 |          2.413 |       2.636 |                5328124 |  3364758 |
| TBD-TRB-22  | TURBOCHARGER ASM              | captive | P            |             826.35 |     1115.57 |     1219.01 |          0.6741 |          1.35  |       1.131 |                9161192 |  8651055 |
| TBD-INJ-22  | NOZZLE ASM; INJ               | captive | P            |             473.43 |      639.13 |      698.39 |          0.6741 |          4.233 |       4.626 |                7157182 |  3806152 |
| TBD-ECU-22  | ECU; ENGINE                   | captive | P            |             671.41 |      906.4  |      990.45 |          0.6741 |          1.35  |       1.131 |                4962313 |  4685988 |