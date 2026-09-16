# 20260805T094652Z__launch__dmax_22_short

- **kind** launch · **scenario** dmax_22_short
- **utc** 2026-08-05T09:46:52.000261+00:00
- **config sha** `8ac2b06c4a0f2751`
- **headline** dmax_22: best tactic 'warranty_load' NPV GP EUR 98,040,241

## D-Max 2.2L (RG21 / RZ4F-TC, SCR, Euro 6d/7)

Spec confirmed: **True** — 00_docs/ISZE_ROADMAP.md LCV bucket item, 4 OEM schedules read 2026-07-15

Services/vehicle/yr: 1.33 (20,000 km / 15,000 km interval)


### Scenario comparison (10y discounted GP)

| scenario      | fork   | label                                                 |   revenue_10y |   rev_warranty_10y |   gp_npv |   gp_npv_wear |   gp_npv_captive |   capture_y10_wear |   capture_y10_captive |   captive_index_y10 |   vs_class_only |   vs_class_only_pct |
|:--------------|:-------|:------------------------------------------------------|--------------:|-------------------:|---------:|--------------:|-----------------:|-------------------:|----------------------:|--------------------:|----------------:|--------------------:|
| warranty_load | short  | Load the warranty phase, then freeze captive (Jerome) |     220561894 |          120867100 | 98040241 |       5264665 |         92775576 |              0.232 |                 0.508 |               2.008 |        23901964 |                32.2 |
| split         | short  | Habit on wear, harvest on captive                     |     221995645 |          121100635 | 97911193 |       5264665 |         92646528 |              0.232 |                 0.477 |               2.22  |        23772916 |                32.1 |
| harvest       | short  | Harvest the monopoly window                           |     207030499 |          111977138 | 89408352 |       6329153 |         83079199 |              0.169 |                 0.507 |               2.042 |        15270075 |                20.6 |
| split_freeze  | short  | Split, then hold captive flat once warranty ends      |     206594871 |          112010574 | 88656421 |       5264665 |         83391756 |              0.232 |                 0.532 |               1.859 |        14518144 |                19.6 |
| class_only    | short  | Baseline - class factor as issued, no ISZE adjustment |     185595371 |           97371425 | 74138277 |       5651033 |         68487244 |              0.194 |                 0.553 |               1.776 |               0 |                 0   |
| habit         | short  | Buy the dealer habit before IAM arrives               |     186789456 |           97141308 | 73751909 |       5264665 |         68487244 |              0.232 |                 0.553 |               1.776 |         -386368 |                -0.5 |


### Price book — recommended scenario

| pn          | description                   | role    | part_class   |   sp_class_implied |   sp_launch |   price_y10 |   gp_pct_launch |   index_launch |   index_y10 |   revenue_warranty_10y |   gp_npv |
|:------------|:------------------------------|:--------|:-------------|-------------------:|------------:|------------:|----------------:|---------------:|------------:|-----------------------:|---------:|
| TBD-OF-22   | ELEMENT; OIL FILTER           | wear    | C            |               6.8  |        5.78 |        7.54 |          0.4471 |          0.839 |       1.095 |                  64216 |   566444 |
| TBD-FF-22   | ELEMENT KIT; FUEL FILTER      | wear    | C            |              13.86 |       11.78 |       15.37 |          0.4471 |          2.003 |       2.613 |                 130867 |   315723 |
| TBD-AF-22   | FILTER; ACL                   | wear    | C            |              21.19 |       18.01 |       23.5  |          0.4471 |          1.289 |       1.682 |                 200105 |  1279750 |
| TBD-CF-22   | FILTER; BLOWER UNIT           | wear    | C            |              16.36 |       13.9  |       18.14 |          0.4471 |          3.531 |       4.607 |                 154454 |   306051 |
| TBD-UF-22   | FILTER; UREA / DEF            | wear    | D            |              24.46 |       20.79 |       27.13 |          0.4353 |          0.85  |       0.85  |                  57738 |   505199 |
| TBD-BPF-22  | PAD KIT; CALIPER DISC BRK FRT | wear    | F            |              70.7  |       60.09 |       78.41 |          0.3824 |          1.796 |       2.344 |                 250321 |   720431 |
| TBD-BPR-22  | PAD KIT; CALIPER DISC BRK RR  | wear    | F            |              59.16 |       50.28 |       65.61 |          0.3824 |          1.726 |       2.252 |                 139635 |   417382 |
| TBD-BRF-22  | ROTOR; DISC BRK FRT           | wear    | F            |              73.58 |       62.55 |       81.61 |          0.3824 |          1.269 |       1.656 |                 130269 |   756589 |
| TBD-BLT-22  | BELT; DRIVE                   | wear    | C            |              19.34 |       16.44 |       21.45 |          0.4471 |          1.63  |       2.127 |                  27391 |   100739 |
| TBD-CLD-22  | DISC; CLUTCH                  | wear    | J            |             126.25 |      107.31 |      140.02 |          0.3471 |          2.016 |       2.631 |                 149001 |   296357 |
| TBD-DPF-22  | DPD / DPF ASM                 | captive | P            |            1446.1  |     1952.24 |     2133.27 |          0.6741 |          4.482 |       4.898 |               32064173 | 16993991 |
| TBD-SCR-22  | CATALYST ASM; SCR             | captive | P            |            1222.3  |     1650.11 |     1803.12 |          0.6741 |          1.35  |       1.131 |               16261116 | 15355623 |
| TBD-NOX1-22 | SENSOR; NOX UPSTREAM          | captive | P            |             266.84 |      360.23 |      393.64 |          0.6741 |          1.35  |       1.131 |                8874905 |  8380709 |
| TBD-NOX2-22 | SENSOR; NOX DOWNSTREAM        | captive | P            |             253.93 |      342.8  |      374.59 |          0.6741 |          1.35  |       1.131 |                7037895 |  6645993 |
| TBD-DEFP-22 | PUMP ASM; DEF                 | captive | P            |             499.25 |      673.99 |      736.48 |          0.6741 |          1.35  |       1.131 |               11069774 | 10453358 |
| TBD-DEFI-22 | INJECTOR; DEF                 | captive | P            |             206.59 |      278.89 |      304.75 |          0.6741 |          1.35  |       1.131 |                4580596 |  4325527 |
| TBD-EGR-22  | VALVE; EGR                    | captive | P            |             288.36 |      389.29 |      425.38 |          0.6741 |          2.413 |       2.636 |                7992186 |  5047137 |
| TBD-TRB-22  | TURBOCHARGER ASM              | captive | P            |             826.35 |     1115.57 |     1219.01 |          0.6741 |          1.35  |       1.131 |               13741789 | 12976582 |
| TBD-INJ-22  | NOZZLE ASM; INJ               | captive | P            |             473.43 |      639.13 |      698.39 |          0.6741 |          4.233 |       4.626 |               10497200 |  5567674 |
| TBD-ECU-22  | ECU; ENGINE                   | captive | P            |             671.41 |      906.4  |      990.45 |          0.6741 |          1.35  |       1.131 |                7443469 |  7028982 |