# 20260805T091118Z__launch__dmax_22

- **kind** launch · **scenario** dmax_22
- **utc** 2026-08-05T09:11:18.612259+00:00
- **config sha** `1e28678ec3485a90`
- **headline** dmax_22: best tactic 'split' NPV GP EUR 23,512,262

## D-Max 2.2L (RG21 / RZ4F-TC, SCR, Euro 6d/7)

Spec confirmed: **True** — 00_docs/ISZE_ROADMAP.md LCV bucket item, 4 OEM schedules read 2026-07-15

Services/vehicle/yr: 1.33 (20,000 km / 15,000 km interval)


### Scenario comparison (10y discounted GP)

| scenario     | label                                                     |   revenue_10y |   rev_warranty_10y |   gp_npv |   gp_npv_wear |   gp_npv_captive |   capture_y10_wear |   capture_y10_captive |   captive_index_y10 |   vs_class_only |   vs_class_only_pct |
|:-------------|:----------------------------------------------------------|--------------:|-------------------:|---------:|--------------:|-----------------:|-------------------:|----------------------:|--------------------:|----------------:|--------------------:|
| split        | Habit on wear, harvest on captive                         |      55439076 |           27171925 | 23512262 |       4063153 |         19449109 |              0.232 |                 0.477 |               2.22  |         4638552 |                24.6 |
| harvest      | Harvest the monopoly window                               |      52142105 |           25411265 | 22498081 |       5053342 |         17444739 |              0.169 |                 0.507 |               2.042 |         3624371 |                19.2 |
| split_freeze | Split, then hold captive flat once warranty ends (Jerome) |      52204273 |           25182545 | 21577590 |       4063153 |         17514437 |              0.232 |                 0.532 |               1.859 |         2703880 |                14.3 |
| class_only   | Baseline - class factor as issued, no ISZE adjustment     |      47488903 |           22096752 | 18873710 |       4471504 |         14402206 |              0.194 |                 0.553 |               1.776 |               0 |                 0   |
| habit        | Buy the dealer habit before IAM arrives                   |      48119878 |           21928372 | 18465359 |       4063153 |         14402206 |              0.232 |                 0.553 |               1.776 |         -408351 |                -2.2 |


### Price book — recommended scenario

| pn          | description                   | role    | part_class   |   sp_class_implied |   sp_launch |   price_y10 |   gp_pct_launch |   index_launch |   index_y10 |   revenue_warranty_10y |   gp_npv |
|:------------|:------------------------------|:--------|:-------------|-------------------:|------------:|------------:|----------------:|---------------:|------------:|-----------------------:|---------:|
| TBD-OF-22   | ELEMENT; OIL FILTER           | wear    | C            |               6.8  |        5.78 |        7.54 |          0.4471 |          0.839 |       1.095 |                  64216 |   566444 |
| TBD-FF-22   | ELEMENT KIT; FUEL FILTER      | wear    | C            |              13.86 |       11.78 |       15.37 |          0.4471 |          2.003 |       2.613 |                  65434 |   157861 |
| TBD-AF-22   | FILTER; ACL                   | wear    | C            |              21.19 |       18.01 |       23.5  |          0.4471 |          1.289 |       1.682 |                 100052 |   639875 |
| TBD-CF-22   | FILTER; BLOWER UNIT           | wear    | C            |              16.36 |       13.9  |       18.14 |          0.4471 |          3.531 |       4.607 |                  77227 |   153026 |
| TBD-UF-22   | FILTER; UREA / DEF            | wear    | D            |              24.46 |       20.79 |       27.13 |          0.4353 |          0.85  |       0.85  |                  76214 |   666863 |
| TBD-BPF-22  | PAD KIT; CALIPER DISC BRK FRT | wear    | F            |              70.7  |       60.09 |       78.41 |          0.3824 |          1.796 |       2.344 |                 200257 |   576345 |
| TBD-BPR-22  | PAD KIT; CALIPER DISC BRK RR  | wear    | F            |              59.16 |       50.28 |       65.61 |          0.3824 |          1.726 |       2.252 |                 125672 |   375644 |
| TBD-BRF-22  | ROTOR; DISC BRK FRT           | wear    | F            |              73.58 |       62.55 |       81.61 |          0.3824 |          1.269 |       1.656 |                 104215 |   605272 |
| TBD-BLT-22  | BELT; DRIVE                   | wear    | C            |              19.34 |       16.44 |       21.45 |          0.4471 |          1.63  |       2.127 |                  24652 |    90665 |
| TBD-CLD-22  | DISC; CLUTCH                  | wear    | J            |             126.25 |      107.31 |      140.02 |          0.3471 |          2.016 |       2.631 |                 116221 |   231158 |
| TBD-DPF-22  | DPD / DPF ASM                 | captive | P            |            1446.1  |     1807.63 |     2358.55 |          0.648  |          4.15  |       5.415 |                7228530 |  3792664 |
| TBD-SCR-22  | CATALYST ASM; SCR             | captive | P            |            1222.3  |     1527.88 |     1993.53 |          0.648  |          1.25  |       1.25  |                3054915 |  2885418 |
| TBD-NOX1-22 | SENSOR; NOX UPSTREAM          | captive | P            |             266.84 |      333.55 |      435.21 |          0.648  |          1.25  |       1.25  |                2223060 |  2099718 |
| TBD-NOX2-22 | SENSOR; NOX DOWNSTREAM        | captive | P            |             253.93 |      317.41 |      414.15 |          0.648  |          1.25  |       1.25  |                1692394 |  1598495 |
| TBD-DEFP-22 | PUMP ASM; DEF                 | captive | P            |             499.25 |      624.06 |      814.26 |          0.648  |          1.25  |       1.25  |                2495564 |  2357102 |
| TBD-DEFI-22 | INJECTOR; DEF                 | captive | P            |             206.59 |      258.23 |      336.94 |          0.648  |          1.25  |       1.25  |                1032647 |   975353 |
| TBD-EGR-22  | VALVE; EGR                    | captive | P            |             288.36 |      360.45 |      470.31 |          0.648  |          2.234 |       2.915 |                1921871 |  1190234 |
| TBD-TRB-22  | TURBOCHARGER ASM              | captive | P            |             826.35 |     1032.93 |     1347.74 |          0.648  |          1.25  |       1.25  |                2065294 |  1950705 |
| TBD-INJ-22  | NOZZLE ASM; INJ               | captive | P            |             473.43 |      591.78 |      772.14 |          0.648  |          3.92  |       5.115 |                3944139 |  2071104 |
| TBD-ECU-22  | ECU; ENGINE                   | captive | P            |             671.41 |      839.26 |     1095.04 |          0.648  |          1.25  |       1.25  |                 559351 |   528316 |