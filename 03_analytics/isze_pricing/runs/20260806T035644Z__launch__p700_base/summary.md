# 20260806T035644Z__launch__p700_base

- **kind** launch · **scenario** p700_base
- **utc** 2026-08-06T03:56:44.669781+00:00
- **config sha** `8ac2b06c4a0f2751`
- **headline** p700: best tactic 'split' NPV GP EUR 58,493,030

## P700 (truck)

Spec confirmed: **False** — SPEC NOT CONFIRMED - Jerome to supply model/parts detail

Services/vehicle/yr: 1.50 (60,000 km / 40,000 km interval)


### Scenario comparison (10y discounted GP)

| scenario      | fork   | label                                                 |   revenue_10y |   rev_warranty_10y |   gp_npv |   gp_npv_wear |   gp_npv_captive |   capture_y10_wear |   capture_y10_captive |   captive_index_y10 |   vs_class_only |   vs_class_only_pct |
|:--------------|:-------|:------------------------------------------------------|--------------:|-------------------:|---------:|--------------:|-----------------:|-------------------:|----------------------:|--------------------:|----------------:|--------------------:|
| split         | base   | Habit on wear, harvest on captive                     |     138342134 |           59443599 | 58493030 |       5892810 |         52600220 |              0.584 |                 0.638 |               1.25  |        12129364 |                26.2 |
| warranty_load | base   | Load the warranty phase, then freeze captive (Jerome) |     137179457 |           59145610 | 58214867 |       5892810 |         52322057 |              0.584 |                 0.683 |               1.131 |        11851201 |                25.6 |
| harvest       | base   | Harvest the monopoly window                           |     134460661 |           55012794 | 56350299 |       9357371 |         46992928 |              0.511 |                 0.68  |               1.15  |         9986633 |                21.5 |
| split_freeze  | base   | Split, then hold captive flat once warranty ends      |     129262508 |           54820003 | 52946181 |       5892810 |         47053371 |              0.584 |                 0.717 |               1.047 |         6582515 |                14.2 |
| class_only    | base   | Baseline - class factor as issued, no ISZE adjustment |     120114145 |           47837209 | 46363666 |       8007417 |         38356249 |              0.584 |                 0.74  |               1     |               0 |                 0   |
| habit         | base   | Buy the dealer habit before IAM arrives               |     116811610 |           47704867 | 44249059 |       5892810 |         38356249 |              0.584 |                 0.74  |               1     |        -2114607 |                -4.6 |


### Price book — recommended scenario

| pn          | description                | role    | part_class   |   sp_class_implied |   sp_launch |   price_y10 |   gp_pct_launch |   index_launch |   index_y10 |   revenue_warranty_10y |   gp_npv |
|:------------|:---------------------------|:--------|:-------------|-------------------:|------------:|------------:|----------------:|---------------:|------------:|-----------------------:|---------:|
| TBD-OF-P7   | ELEMENT; OIL FILTER        | wear    | C            |              15.31 |       13.01 |       16.98 |          0.4471 |           0.85 |        0.85 |                  30971 |   262186 |
| TBD-FF-P7   | ELEMENT KIT; FUEL FILTER   | wear    | C            |              27.4  |       23.29 |       30.39 |          0.4471 |           0.85 |        0.85 |                  55421 |   469175 |
| TBD-AF-P7   | FILTER; ACL                | wear    | C            |              41.9  |       35.62 |       46.47 |          0.4471 |           0.85 |        0.85 |                  42381 |   358781 |
| TBD-UF-P7   | FILTER; UREA / DEF         | wear    | D            |              48.13 |       40.91 |       53.38 |          0.4353 |           0.85 |        0.85 |                  25963 |   215642 |
| TBD-BPF-P7  | PAD KIT; BRAKE FRT         | wear    | F            |             173.14 |      147.17 |      192.02 |          0.3824 |           0.85 |        0.85 |                 233482 |  1771322 |
| TBD-BSR-P7  | SHOE KIT; BRAKE RR         | wear    | F            |             137.07 |      116.51 |      152.02 |          0.3824 |           0.85 |        0.85 |                 123227 |   934864 |
| TBD-BRF-P7  | DISC; BRAKE FRT            | wear    | F            |             223.64 |      190.09 |      248.03 |          0.3824 |           0.85 |        0.85 |                 139191 |  1055980 |
| TBD-DCTO-P7 | OIL + FILTER KIT; ISIM DCT | wear    | D            |             110.47 |       93.9  |      122.51 |          0.4353 |           0.85 |        0.85 |                  99311 |   824860 |
| TBD-DCTC-P7 | CLUTCH PACK ASM; ISIM DCT  | captive | P            |            1592.44 |     1990.55 |     2597.21 |          0.648  |           1.25 |        1.25 |                8084474 |  7286917 |
| TBD-DCTM-P7 | MECHATRONIC UNIT; ISIM DCT | captive | P            |            2065.86 |     2582.33 |     3369.35 |          0.648  |           1.25 |        1.25 |                8739972 |  7877749 |
| TBD-BSIS-P7 | MODULE; BLIND SPOT INFO    | captive | P            |             550.9  |      688.62 |      898.49 |          0.648  |           1.25 |        1.25 |                2330659 |  2100733 |
| TBD-TSR-P7  | CAMERA; TRAFFIC SIGN RECOG | captive | P            |             499.25 |      624.06 |      814.26 |          0.648  |           1.25 |        1.25 |                2112160 |  1903789 |
| TBD-TPMS-P7 | SENSOR SET; TPMS           | captive | D            |             165.7  |      207.12 |      270.25 |          0.616  |           1.25 |        1.25 |                1752546 |  1518986 |
| TBD-LED-P7  | LAMP ASM; LED HEAD         | captive | F            |             519.42 |      649.27 |      847.15 |          0.58   |           1.25 |        1.25 |                3296218 |  2728567 |
| TBD-DPF-P7  | DPD / DPF ASM              | captive | P            |            2668.41 |     3335.51 |     4352.08 |          0.648  |           1.25 |        1.25 |               16933695 | 15263138 |
| TBD-NOX1-P7 | SENSOR; NOX UPSTREAM       | captive | P            |             395.96 |      494.95 |      645.79 |          0.648  |           1.25 |        1.25 |                3426466 |  3088436 |
| TBD-INJ-P7  | NOZZLE ASM; INJ            | captive | P            |             757.48 |      946.85 |     1235.43 |          0.648  |           1.25 |        1.25 |                4806985 |  4332762 |
| TBD-TRB-P7  | TURBOCHARGER ASM           | captive | P            |            1420.28 |     1775.35 |     2316.43 |          0.648  |           1.25 |        1.25 |                7210477 |  6499143 |