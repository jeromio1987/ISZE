# 20260805T075013Z__launch__dmax_22

- **kind** launch · **scenario** dmax_22
- **utc** 2026-08-05T07:50:13.073778+00:00
- **config sha** `cad6d3ca6e79c1e2`
- **headline** dmax_22: best tactic 'harvest' NPV GP EUR 13,976,025

## D-Max 2.2L (RG21 / RZ4F-TC, SCR, Euro 6d/7)

Spec confirmed: **True** — 00_docs/ISZE_ROADMAP.md LCV bucket item, 4 OEM schedules read 2026-07-15

Services/vehicle/yr: 1.33 (20,000 km / 15,000 km interval)


### Scenario comparison (10y discounted GP)

| scenario   | label                                                   |   revenue_10y |   gp_10y |   gp_npv |   gp_npv_wear |   gp_npv_captive |   mean_capture_y10_wear |   vs_class_only |   vs_class_only_pct |
|:-----------|:--------------------------------------------------------|--------------:|---------:|---------:|--------------:|-----------------:|------------------------:|----------------:|--------------------:|
| harvest    | Harvest the monopoly window                             |      36547670 | 21988991 | 13976025 |       4193895 |          9782130 |                   0.224 |         2011963 |                16.8 |
| split      | Habit on wear, harvest on captive (spec recommendation) |      38341924 | 22055386 | 13959100 |       3115668 |         10843432 |                   0.331 |         1995038 |                16.7 |
| class_only | Baseline - class factor as issued, no ISZE adjustment   |      34903268 | 18878337 | 11964062 |       3735170 |          8228892 |                   0.269 |               0 |                 0   |
| habit      | Buy the dealer habit before IAM arrives                 |      35227405 | 17973773 | 11344560 |       3115668 |          8228892 |                   0.331 |         -619502 |                -5.2 |


### Price book — recommended scenario

| pn          | description                   | role    | part_class   |   sp_class_implied |   sp_launch |   gp_pct_launch |   price_index |   gp_npv |
|:------------|:------------------------------|:--------|:-------------|-------------------:|------------:|----------------:|--------------:|---------:|
| TBD-OF-22   | ELEMENT; OIL FILTER           | wear    | C            |               6.8  |        7.82 |          0.5913 |         1.135 |   650550 |
| TBD-FF-22   | ELEMENT KIT; FUEL FILTER      | wear    | C            |              13.86 |       15.94 |          0.5913 |         2.71  |   197512 |
| TBD-AF-22   | FILTER; ACL                   | wear    | C            |              21.19 |       24.37 |          0.5913 |         1.744 |   529757 |
| TBD-CF-22   | FILTER; BLOWER UNIT           | wear    | C            |              16.36 |       18.81 |          0.5913 |         4.777 |   175236 |
| TBD-UF-22   | FILTER; UREA / DEF            | wear    | D            |              24.46 |       28.13 |          0.5826 |         1.15  |   753143 |
| TBD-BPF-22  | PAD KIT; CALIPER DISC BRK FRT | wear    | F            |              70.7  |       81.3  |          0.5435 |         2.431 |   590133 |
| TBD-BPR-22  | PAD KIT; CALIPER DISC BRK RR  | wear    | F            |              59.16 |       68.03 |          0.5435 |         2.335 |   378695 |
| TBD-BRF-22  | ROTOR; DISC BRK FRT           | wear    | F            |              73.58 |       84.62 |          0.5435 |         1.717 |   529598 |
| TBD-BLT-22  | BELT; DRIVE                   | wear    | C            |              19.34 |       22.24 |          0.5913 |         2.206 |    83442 |
| TBD-CLD-22  | DISC; CLUTCH                  | wear    | J            |             126.25 |      145.18 |          0.5174 |         2.728 |   305829 |
| TBD-DPF-22  | DPD / DPF ASM                 | captive | P            |            1446.1  |     1663.02 |          0.6174 |         3.818 |   808028 |
| TBD-SCR-22  | CATALYST ASM; SCR             | captive | P            |            1222.3  |     1405.65 |          0.6174 |         1.15  |  1808430 |
| TBD-NOX1-22 | SENSOR; NOX UPSTREAM          | captive | P            |             266.84 |      306.87 |          0.6174 |         1.15  |  1315994 |
| TBD-NOX2-22 | SENSOR; NOX DOWNSTREAM        | captive | P            |             253.93 |      292.02 |          0.6174 |         1.15  |  1001854 |
| TBD-DEFP-22 | PUMP ASM; DEF                 | captive | P            |             499.25 |      574.14 |          0.6174 |         1.15  |  1477309 |
| TBD-DEFI-22 | INJECTOR; DEF                 | captive | P            |             206.59 |      237.57 |          0.6174 |         1.15  |   611300 |
| TBD-EGR-22  | VALVE; EGR                    | captive | P            |             288.36 |      331.61 |          0.6174 |         2.055 |   751784 |
| TBD-TRB-22  | TURBOCHARGER ASM              | captive | P            |             826.35 |      950.3  |          0.6174 |         1.15  |  1222601 |
| TBD-INJ-22  | NOZZLE ASM; INJ               | captive | P            |             473.43 |      544.44 |          0.6174 |         3.606 |   453709 |
| TBD-ECU-22  | ECU; ENGINE                   | captive | P            |             671.41 |      772.12 |          0.6174 |         1.15  |   331121 |