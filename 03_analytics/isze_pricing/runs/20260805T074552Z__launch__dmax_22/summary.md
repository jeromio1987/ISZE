# 20260805T074552Z__launch__dmax_22

- **kind** launch · **scenario** dmax_22
- **utc** 2026-08-05T07:45:52.780581+00:00
- **config sha** `dac60960e1fe42f8`
- **headline** dmax_22: best tactic 'split' NPV GP EUR 45,540,635

## D-Max 2.2L (RG21 / RZ4F-TC, SCR, Euro 6d/7)

Spec confirmed: **True** — 00_docs/ISZE_ROADMAP.md LCV bucket item, 4 OEM schedules read 2026-07-15

Services/vehicle/yr: 1.33 (20,000 km / 15,000 km interval)


### Scenario comparison (10y discounted GP)

| scenario   | label                                                   |   revenue_10y |   gp_10y |   gp_npv |   gp_npv_wear |   gp_npv_captive |   mean_capture_y10_wear |   vs_class_only |   vs_class_only_pct |
|:-----------|:--------------------------------------------------------|--------------:|---------:|---------:|--------------:|-----------------:|------------------------:|----------------:|--------------------:|
| split      | Habit on wear, harvest on captive (spec recommendation) |     119875109 | 74028829 | 45540635 |       4027887 |         41512748 |                   0.354 |        11554552 |                34   |
| harvest    | Harvest the monopoly window                             |     113511338 | 69141976 | 42837765 |       6450050 |         36387715 |                   0.246 |         8851682 |                26   |
| class_only | Baseline - class factor as issued, no ISZE adjustment   |      99858891 | 54912866 | 33986083 |       5285913 |         28700170 |                   0.292 |               0 |                 0   |
| habit      | Buy the dealer habit before IAM arrives                 |      98935667 | 53089386 | 32728057 |       4027887 |         28700170 |                   0.354 |        -1258026 |                -3.7 |


### Price book — recommended scenario

| pn          | description                   | role    | part_class   |   sp_class_implied |   sp_launch |   gp_pct_launch |   price_index |   gp_npv |
|:------------|:------------------------------|:--------|:-------------|-------------------:|------------:|----------------:|--------------:|---------:|
| TBD-OF-22   | ELEMENT; OIL FILTER           | wear    | C            |               6.8  |        5.78 |          0.4471 |         0.839 |   394904 |
| TBD-FF-22   | ELEMENT KIT; FUEL FILTER      | wear    | C            |              13.86 |       11.78 |          0.4471 |         2.003 |   242673 |
| TBD-AF-22   | FILTER; ACL                   | wear    | C            |              21.19 |       18.01 |          0.4471 |         1.289 |   549384 |
| TBD-CF-22   | FILTER; BLOWER UNIT           | wear    | C            |              16.36 |       13.9  |          0.4471 |         3.531 |   241848 |
| TBD-UF-22   | FILTER; UREA / DEF            | wear    | D            |              24.46 |       20.79 |          0.4353 |         0.85  |   456352 |
| TBD-BPF-22  | PAD KIT; CALIPER DISC BRK FRT | wear    | F            |              70.7  |       60.09 |          0.3824 |         1.796 |   725659 |
| TBD-BPR-22  | PAD KIT; CALIPER DISC BRK RR  | wear    | F            |              59.16 |       50.28 |          0.3824 |         1.726 |   474686 |
| TBD-BRF-22  | ROTOR; DISC BRK FRT           | wear    | F            |              73.58 |       62.55 |          0.3824 |         1.269 |   493612 |
| TBD-BLT-22  | BELT; DRIVE                   | wear    | C            |              19.34 |       16.44 |          0.4471 |         1.63  |   114833 |
| TBD-CLD-22  | DISC; CLUTCH                  | wear    | J            |             126.25 |      107.31 |          0.3471 |         2.016 |   333936 |
| TBD-DPF-22  | DPD / DPF ASM                 | captive | P            |            1446.1  |     1807.63 |          0.648  |         4.15  | 17062120 |
| TBD-SCR-22  | CATALYST ASM; SCR             | captive | P            |            1222.3  |     1527.88 |          0.648  |         1.25  |  4326466 |
| TBD-NOX1-22 | SENSOR; NOX UPSTREAM          | captive | P            |             266.84 |      333.55 |          0.648  |         1.25  |  2518694 |
| TBD-NOX2-22 | SENSOR; NOX DOWNSTREAM        | captive | P            |             253.93 |      317.41 |          0.648  |         1.25  |  2097219 |
| TBD-DEFP-22 | PUMP ASM; DEF                 | captive | P            |             499.25 |      624.06 |          0.648  |         1.25  |  2945247 |
| TBD-DEFI-22 | INJECTOR; DEF                 | captive | P            |             206.59 |      258.23 |          0.648  |         1.25  |  1218723 |
| TBD-EGR-22  | VALVE; EGR                    | captive | P            |             288.36 |      360.45 |          0.648  |         2.234 |  2041361 |
| TBD-TRB-22  | TURBOCHARGER ASM              | captive | P            |             826.35 |     1032.93 |          0.648  |         1.25  |  2924935 |
| TBD-INJ-22  | NOZZLE ASM; INJ               | captive | P            |             473.43 |      591.78 |          0.648  |         3.92  |  5585813 |
| TBD-ECU-22  | ECU; ENGINE                   | captive | P            |             671.41 |      839.26 |          0.648  |         1.25  |   792170 |