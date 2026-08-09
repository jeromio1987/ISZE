# 20260805T094653Z__launch__dmax_22_base

- **kind** launch · **scenario** dmax_22_base
- **utc** 2026-08-05T09:46:53.297056+00:00
- **config sha** `8ac2b06c4a0f2751`
- **headline** dmax_22: best tactic 'warranty_load' NPV GP EUR 70,222,601

## D-Max 2.2L (RG21 / RZ4F-TC, SCR, Euro 6d/7)

Spec confirmed: **True** — 00_docs/ISZE_ROADMAP.md LCV bucket item, 4 OEM schedules read 2026-07-15

Services/vehicle/yr: 1.33 (20,000 km / 15,000 km interval)


### Scenario comparison (10y discounted GP)

| scenario      | fork   | label                                                 |   revenue_10y |   rev_warranty_10y |   gp_npv |   gp_npv_wear |   gp_npv_captive |   capture_y10_wear |   capture_y10_captive |   captive_index_y10 |   vs_class_only |   vs_class_only_pct |
|:--------------|:-------|:------------------------------------------------------|--------------:|-------------------:|---------:|--------------:|-----------------:|-------------------:|----------------------:|--------------------:|----------------:|--------------------:|
| warranty_load | base   | Load the warranty phase, then freeze captive (Jerome) |     157936714 |           86860305 | 70222601 |       3619992 |         66602609 |              0.232 |                 0.508 |               2.008 |        17182410 |                32.4 |
| split         | base   | Habit on wear, harvest on captive                     |     158969711 |           87028249 | 70131461 |       3619992 |         66511469 |              0.232 |                 0.477 |               2.22  |        17091270 |                32.2 |
| harvest       | base   | Harvest the monopoly window                           |     148289004 |           80445702 | 64018633 |       4400131 |         59618502 |              0.169 |                 0.507 |               2.042 |        10978442 |                20.7 |
| split_freeze  | base   | Split, then hold captive flat once warranty ends      |     147903766 |           80491174 | 63483631 |       3619992 |         59863639 |              0.232 |                 0.532 |               1.859 |        10443440 |                19.7 |
| class_only    | base   | Baseline - class factor as issued, no ISZE adjustment |     132823023 |           69952788 | 53040191 |       3913942 |         49126249 |              0.194 |                 0.553 |               1.776 |               0 |                 0   |
| habit         | base   | Buy the dealer habit before IAM arrives               |     133585777 |           69798013 | 52746241 |       3619992 |         49126249 |              0.232 |                 0.553 |               1.776 |         -293950 |                -0.6 |


### Price book — recommended scenario

| pn          | description                   | role    | part_class   |   sp_class_implied |   sp_launch |   price_y10 |   gp_pct_launch |   index_launch |   index_y10 |   revenue_warranty_10y |   gp_npv |
|:------------|:------------------------------|:--------|:-------------|-------------------:|------------:|------------:|----------------:|---------------:|------------:|-----------------------:|---------:|
| TBD-OF-22   | ELEMENT; OIL FILTER           | wear    | C            |               6.8  |        5.78 |        7.54 |          0.4471 |          0.839 |       1.095 |                  64216 |   566444 |
| TBD-FF-22   | ELEMENT KIT; FUEL FILTER      | wear    | C            |              13.86 |       11.78 |       15.37 |          0.4471 |          2.003 |       2.613 |                  65434 |   157861 |
| TBD-AF-22   | FILTER; ACL                   | wear    | C            |              21.19 |       18.01 |       23.5  |          0.4471 |          1.289 |       1.682 |                 100052 |   639875 |
| TBD-CF-22   | FILTER; BLOWER UNIT           | wear    | C            |              16.36 |       13.9  |       18.14 |          0.4471 |          3.531 |       4.607 |                  77227 |   153026 |
| TBD-UF-22   | FILTER; UREA / DEF            | wear    | D            |              24.46 |       20.79 |       27.13 |          0.4353 |          0.85  |       0.85  |                  38492 |   336800 |
| TBD-BPF-22  | PAD KIT; CALIPER DISC BRK FRT | wear    | F            |              70.7  |       60.09 |       78.41 |          0.3824 |          1.796 |       2.344 |                 182052 |   523950 |
| TBD-BPR-22  | PAD KIT; CALIPER DISC BRK RR  | wear    | F            |              59.16 |       50.28 |       65.61 |          0.3824 |          1.726 |       2.252 |                 111708 |   333906 |
| TBD-BRF-22  | ROTOR; DISC BRK FRT           | wear    | F            |              73.58 |       62.55 |       81.61 |          0.3824 |          1.269 |       1.656 |                 104215 |   605272 |
| TBD-BLT-22  | BELT; DRIVE                   | wear    | C            |              19.34 |       16.44 |       21.45 |          0.4471 |          1.63  |       2.127 |                  21913 |    80591 |
| TBD-CLD-22  | DISC; CLUTCH                  | wear    | J            |             126.25 |      107.31 |      140.02 |          0.3471 |          2.016 |       2.631 |                 111751 |   222267 |
| TBD-DPF-22  | DPD / DPF ASM                 | captive | P            |            1446.1  |     1952.24 |     2133.27 |          0.6741 |          4.482 |       4.898 |               24048130 | 12745493 |
| TBD-SCR-22  | CATALYST ASM; SCR             | captive | P            |            1222.3  |     1650.11 |     1803.12 |          0.6741 |          1.35  |       1.131 |               12703997 | 11996580 |
| TBD-NOX1-22 | SENSOR; NOX UPSTREAM          | captive | P            |             266.84 |      360.23 |      393.64 |          0.6741 |          1.35  |       1.131 |                5916603 |  5587140 |
| TBD-NOX2-22 | SENSOR; NOX DOWNSTREAM        | captive | P            |             253.93 |      342.8  |      374.59 |          0.6741 |          1.35  |       1.131 |                4967926 |  4691289 |
| TBD-DEFP-22 | PUMP ASM; DEF                 | captive | P            |             499.25 |      673.99 |      736.48 |          0.6741 |          1.35  |       1.131 |                8302331 |  7840019 |
| TBD-DEFI-22 | INJECTOR; DEF                 | captive | P            |             206.59 |      278.89 |      304.75 |          0.6741 |          1.35  |       1.131 |                3435447 |  3244146 |
| TBD-EGR-22  | VALVE; EGR                    | captive | P            |             288.36 |      389.29 |      425.38 |          0.6741 |          2.413 |       2.636 |                5328124 |  3364758 |
| TBD-TRB-22  | TURBOCHARGER ASM              | captive | P            |             826.35 |     1115.57 |     1219.01 |          0.6741 |          1.35  |       1.131 |                9161192 |  8651055 |
| TBD-INJ-22  | NOZZLE ASM; INJ               | captive | P            |             473.43 |      639.13 |      698.39 |          0.6741 |          4.233 |       4.626 |                7157182 |  3796141 |
| TBD-ECU-22  | ECU; ENGINE                   | captive | P            |             671.41 |      906.4  |      990.45 |          0.6741 |          1.35  |       1.131 |                4962313 |  4685988 |