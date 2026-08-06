# 20260805T094654Z__launch__dmax_22_long

- **kind** launch · **scenario** dmax_22_long
- **utc** 2026-08-05T09:46:54.727318+00:00
- **config sha** `8ac2b06c4a0f2751`
- **headline** dmax_22: best tactic 'warranty_load' NPV GP EUR 54,628,867

## D-Max 2.2L (RG21 / RZ4F-TC, SCR, Euro 6d/7)

Spec confirmed: **True** — 00_docs/ISZE_ROADMAP.md LCV bucket item, 4 OEM schedules read 2026-07-15

Services/vehicle/yr: 1.33 (20,000 km / 15,000 km interval)


### Scenario comparison (10y discounted GP)

| scenario      | fork   | label                                                 |   revenue_10y |   rev_warranty_10y |   gp_npv |   gp_npv_wear |   gp_npv_captive |   capture_y10_wear |   capture_y10_captive |   captive_index_y10 |   vs_class_only |   vs_class_only_pct |
|:--------------|:-------|:------------------------------------------------------|--------------:|-------------------:|---------:|--------------:|-----------------:|-------------------:|----------------------:|--------------------:|----------------:|--------------------:|
| warranty_load | long   | Load the warranty phase, then freeze captive (Jerome) |     122985479 |           67456980 | 54628867 |       2943190 |         51685677 |              0.232 |                 0.508 |               2.008 |        13325097 |                32.3 |
| split         | long   | Habit on wear, harvest on captive                     |     123790293 |           67587351 | 54560343 |       2943190 |         51617153 |              0.232 |                 0.477 |               2.22  |        13256573 |                32.1 |
| harvest       | long   | Harvest the monopoly window                           |     115533438 |           62488301 | 49867794 |       3617096 |         46250698 |              0.169 |                 0.507 |               2.042 |         8564024 |                20.7 |
| split_freeze  | long   | Split, then hold captive flat once warranty ends      |     115195966 |           62512854 | 49397983 |       2943190 |         46454793 |              0.232 |                 0.532 |               1.859 |         8094213 |                19.6 |
| class_only    | long   | Baseline - class factor as issued, no ISZE adjustment |     103459759 |           54337653 | 41303770 |       3208660 |         38095110 |              0.194 |                 0.553 |               1.776 |               0 |                 0   |
| habit         | long   | Buy the dealer habit before IAM arrives               |     104010609 |           54212135 | 41038300 |       2943190 |         38095110 |              0.232 |                 0.553 |               1.776 |         -265470 |                -0.6 |


### Price book — recommended scenario

| pn          | description                   | role    | part_class   |   sp_class_implied |   sp_launch |   price_y10 |   gp_pct_launch |   index_launch |   index_y10 |   revenue_warranty_10y |   gp_npv |
|:------------|:------------------------------|:--------|:-------------|-------------------:|------------:|------------:|----------------:|---------------:|------------:|-----------------------:|---------:|
| TBD-OF-22   | ELEMENT; OIL FILTER           | wear    | C            |               6.8  |        5.78 |        7.54 |          0.4471 |          0.839 |       1.095 |                  64216 |   566444 |
| TBD-FF-22   | ELEMENT KIT; FUEL FILTER      | wear    | C            |              13.86 |       11.78 |       15.37 |          0.4471 |          2.003 |       2.613 |                  43622 |   105241 |
| TBD-AF-22   | FILTER; ACL                   | wear    | C            |              21.19 |       18.01 |       23.5  |          0.4471 |          1.289 |       1.682 |                  66702 |   426583 |
| TBD-CF-22   | FILTER; BLOWER UNIT           | wear    | C            |              16.36 |       13.9  |       18.14 |          0.4471 |          3.531 |       4.607 |                  77227 |   153026 |
| TBD-UF-22   | FILTER; UREA / DEF            | wear    | D            |              24.46 |       20.79 |       27.13 |          0.4353 |          0.85  |       0.85  |                  28869 |   252600 |
| TBD-BPF-22  | PAD KIT; CALIPER DISC BRK FRT | wear    | F            |              70.7  |       60.09 |       78.41 |          0.3824 |          1.796 |       2.344 |                 143041 |   411675 |
| TBD-BPR-22  | PAD KIT; CALIPER DISC BRK RR  | wear    | F            |              59.16 |       50.28 |       65.61 |          0.3824 |          1.726 |       2.252 |                  93090 |   278255 |
| TBD-BRF-22  | ROTOR; DISC BRK FRT           | wear    | F            |              73.58 |       62.55 |       81.61 |          0.3824 |          1.269 |       1.656 |                  86846 |   504393 |
| TBD-BLT-22  | BELT; DRIVE                   | wear    | C            |              19.34 |       16.44 |       21.45 |          0.4471 |          1.63  |       2.127 |                  18261 |    67159 |
| TBD-CLD-22  | DISC; CLUTCH                  | wear    | J            |             126.25 |      107.31 |      140.02 |          0.3471 |          2.016 |       2.631 |                  89400 |   177814 |
| TBD-DPF-22  | DPD / DPF ASM                 | captive | P            |            1446.1  |     1952.24 |     2133.27 |          0.6741 |          4.482 |       4.898 |               19238504 | 10196395 |
| TBD-SCR-22  | CATALYST ASM; SCR             | captive | P            |            1222.3  |     1650.11 |     1803.12 |          0.6741 |          1.35  |       1.131 |               10163198 |  9597264 |
| TBD-NOX1-22 | SENSOR; NOX UPSTREAM          | captive | P            |             266.84 |      360.23 |      393.64 |          0.6741 |          1.35  |       1.131 |                4437453 |  4190355 |
| TBD-NOX2-22 | SENSOR; NOX DOWNSTREAM        | captive | P            |             253.93 |      342.8  |      374.59 |          0.6741 |          1.35  |       1.131 |                3838852 |  3625087 |
| TBD-DEFP-22 | PUMP ASM; DEF                 | captive | P            |             499.25 |      673.99 |      736.48 |          0.6741 |          1.35  |       1.131 |                6641864 |  6272015 |
| TBD-DEFI-22 | INJECTOR; DEF                 | captive | P            |             206.59 |      278.89 |      304.75 |          0.6741 |          1.35  |       1.131 |                2748358 |  2595316 |
| TBD-EGR-22  | VALVE; EGR                    | captive | P            |             288.36 |      389.29 |      425.38 |          0.6741 |          2.413 |       2.636 |                3836249 |  2422626 |
| TBD-TRB-22  | TURBOCHARGER ASM              | captive | P            |             826.35 |     1115.57 |     1219.01 |          0.6741 |          1.35  |       1.131 |                6870894 |  6488291 |
| TBD-INJ-22  | NOZZLE ASM; INJ               | captive | P            |             473.43 |      639.13 |      698.39 |          0.6741 |          4.233 |       4.626 |                5248600 |  2783837 |
| TBD-ECU-22  | ECU; ENGINE                   | captive | P            |             671.41 |      906.4  |      990.45 |          0.6741 |          1.35  |       1.131 |                3721734 |  3514491 |