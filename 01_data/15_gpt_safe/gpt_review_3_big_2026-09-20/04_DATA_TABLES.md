# Data tables for the multi-hour review

ChatGPT rejected the earlier multi-section `.csv` (comment lines + mixed schemas).
This markdown carries the tables ChatGPT needs for the hour-scale review.
If you also got `04_DATA_TABLES.csv` to upload: it is a valid 3-column file
`table,row_id,payload_json` — filter by `table`, parse JSON per row.

Tables in this file:

- `wallet_all_years` — 54 rows
- `wallet_rollup_2025` — 6 rows
- `gps_spu_by_distributor` — 89 rows
- `opportunity_matrix_full` — 1008 rows
- `opportunity_network_by_category_year` — 56 rows
- `pms_capture_by_db_year` — 3024 rows
- `mix_genuine_bvp_pms` — 1504 rows
- `n35_share` — 9 rows
- `benchmark_tables` — 240 rows
- `pricing_stack` — 19 rows
- `classification_jp_claims` — 23 rows

## TABLE `wallet_rollup_2025` (6 rows)

```csv
metric,value,note
network_ceiling_eur,55253312.0,year=2025
network_captured_total_eur,30756771.610000003,
network_gps_pct,55.66502802583129,captured/ceiling
fleet_uio_units,163198.0,
flat250_market_count,8.0,"IUK,UMI,SWEDEN,NORWAY,HUNGARY,FINLAND,ROMANIA,ICELAND"
flat250_share_of_ceiling_pct,40.31975494971233,
```

## TABLE `n35_share` (9 rows)

```csv
distributor_code,market,n35_share,basis,units_2025e,evidence_note
ITUK,United Kingdom,0.5051,workbook_2b,22191,"Confirmed. Live read from the UIO workbook sheet '2. Vehicle Volume' section B: N35 10,900 of 21,584 N-series. The live read always overrides this value."
UTI,Israel,0.0,cv_claims_plus_ministry,6059,"Confirmed zero. 2,360 distinct CV claim VINs (Dec 2023-Mar 2026): NPR75 895, FRR90 817, FSR90 627, and zero NLR/NMR/NKR. The Israeli Ministry of Transport band table starts at 6.5-7.5 t. No 3.5 t truck exists in the market."
PORTUGAL,Portugal,0.6364,imotors_parc_bands,2206,"Confirmed. Official I-Motors registrations (01_data/07_UIO/Matriculas Isuzu SAP.xlsx) convolved with the UIO V19 survival curve in 01_data/08_Distributor/Imotors_Portugal_UIO_GPS_PMS_Study.xlsx sheet UIO_Rebuild. 2025 N-series parc: N35 1,521.31 + N75/N50/N62 869.00 = 2,390.31; light share 1,521.31/2,390.31 = 0.6364. (2024 = 0.6386.) Replaces the 2026-09-18 JP shipment mix 0.6899 (NLR 1,299/1,883). units_2025e stays the workbook LD row (2,206); the study rebuilt stock is 2,390 — fleet-base swap is a separate decision."
MALTA,Malta,0.369,unmeasured,243,"Unmeasured. JP VIN register destination MT holds 130 shipments: NPR75 73, NMR88 / NMR85 48, FRR 9. NMR88 is a 9.5 t truck, not a 3.5 t N35, so the NMR-class count is NOT evidence of a 3.5 t parc. The previous 0.369 rested on reading 48 NMR as N35. No parc basis exists for Malta. The current rate is kept rather than guessing."
GERMANY,Germany,0.22,helwig_parc_bands,697,"Confirmed. Helwig Schmitt parc overview at 31/12/2025 (mail 2026-06-11 from Sebastian Mueller; on disk 01_data/90_INBOX/_isd_std_mail_20260818/attachments/2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Uebersicht_D_.xlsx): Nfz 787 = <=3.40 t 25 + 3.41-3.50 t 153 + 3.51-5.50 t 79 + 5.51-6.50 t 147 + 6.51-7.50 t 318 + 7.51-12.0 t 35. The 3.41-7.50 t block is 697 and 153/697 = 0.2195, so 0.220 stands."
IRELAND,Ireland,0.3089,simi_bands_parc,731,"SIMI national registrations (01_data/07_UIO/isuzuregdata.xlsx sheet Sheet2, 2010-2025) convolved against the ISZE scrap-adjusted CV curve, evaluated at 2025: N35 464 of N35+N75 1,502 = 0.3089. Flow basis for reference: 663/1,963 = 0.3377; 663/(663+1300+122) = 0.3180. Basis is the parc, because the split is applied to a parc. The previous 0.063 was NOT the SIMI number: it is 36/570 from the JP VIN register (IE), which is a shipment flow of 647 trucks. Fixed 2026-09-18."
BELGIUM,Belgium,0.8571,jp_vin_shipments,113,"JP VIN register destination BE: 49 shipments, NLR 42 (all 3.5 t) -> 42/49 = 0.8571. The previous 0.918 read 45/49 but the register holds 42 NLR, 3 NMR (5.5 t), 4 NPR (7.5 t) and no F. Corrected 2026-09-18. Sample is small (49) but the wallet is almost all D-Max (LCV 9,480 vs cv_std 113) so the effect is immaterial either way."
CYPRUS,Cyprus,0.053,unmeasured,203,"Unmeasured. JP VIN register destination CY holds 114 shipments and ZERO at 3.5 t: NPR 7.5 t 60, NNR 6.5 t 48, NMR 5.5 t 6. NMR is not an N35 (N35 = NLR/NMR 3.5 t only). There is no parc basis for Cyprus. The current rate is kept rather than guessing; a measured or distributor-confirmed figure is needed before this market is split."
GREECE,Greece,0.0,jp_vin_shipments,37,"Confirmed zero. JP VIN register destination GR holds 4 shipments: NMR85 2 (5.5 t) and NPR75 2 (7.5 t). No 3.5 t truck at all, and cv_std is 37 units. Nothing to split."
```

## TABLE `pricing_stack` (19 rows)

```csv
section,label,value,note,rows,billed_eur,weight_share_pct,part_numbers
whole_book,weighted_increase_pct,5.961599453926434,47617 rows,,,,
whole_book,japan_pct,6.208063018487108,,,,,
whole_book,thailand_pct,6.308754566062438,,,,,
live_inputs,fx,178.5,applied not chosen,,,,
live_inputs,discount_J_pct,67.30000000000001,vehicle parts,,,,
live_inputs,discount_T_pct,61.1,,,,,
figure_replaced,earlier_thailand_pct_WRONG,-2.45,factor chain,,,,
by_source,Japan (IML),6.208063018487108,J,22731.0,15401370.75,47.712091692388285,
by_source,Thailand (IMIT),6.308754566062438,T,23085.0,14252360.9,43.08056503308608,
by_source,no source label,3.0601185620378315,(none),1801.0,2942120.98,9.207343274525638,
by_market,PR00,5.921147633739341,Main EU distributor list.,32434.0,12831245.78,,10968.0
by_market,UTI,5.580775741103503,"Israel, sold-to 1799. Never combined with UMI.",1869.0,3400405.3899999997,,1869.0
by_market,UMI,5.6370090038081555,"Israel, sold-to 1797. Never combined with UTI.",2428.0,2429159.96,,2428.0
by_market,CIS,4.8455367219081875,GA Armenia and CBC Kazakhstan.,3090.0,1455811.0699999998,,2674.0
proposals,flat_5pct_paper_eur,1749680.47,paper only,,,,
proposals,published_step_eur,1652140.71,5.9616%,,,,
proposals,in_scope_billed_eur,34993609.39,48653 lines,,,,
proposals,competitor_cover_pct,16.47,T1-T3,,,,
proposals,max_points_at_8pct_cap,1.32,,,,,
```

## TABLE `classification_jp_claims` (23 rows)

```csv
domain,metric,value,note
jp_codes,zkk_distinct,142.0,3 chars
jp_codes,zuk_distinct,359.0,5 chars
jp_codes,hkk_distinct,125.0,4 chars
jp_codes,zkk_euro_cover_pct,88.11,
jp_codes,zkk_hit_eur,46183083.72,
jp_codes,spine_l12m_eur,52414407.82,
jp_codes,blank_jp_rows,25689.0,
jp_codes,blank_jp_eur,6231324.0,
jp_codes,zkk_equals_full_hkk,0.0,of 142
jp_codes,zkk_match_hkk_prefix_live,5.0,of 142
jp_codes,zuk_equals_hkk_or_zkk,0.0,of 359
jp_codes,zkk_114_XC_pct,77.4,not 100
jp_codes,zkk_275_share_covered_pct,46.77,
jp_codes,zkk_fragmented_share_pct,97.86,
jp_codes,benchmark_purity_published,82.59,UNUSABLE
jp_codes,benchmark_purity_jp_desc_zkk,12.32,remeasured
classification,gate_pass,18.0,of 18
classification,residual_share_pct,5.74,
classification,classification_rows,164667.0,
classification,true_open_pns,9164.0,
classification,true_open_l12m_eur,114516.0,
classification,eq_needs_human_pns,360.0,of 744
classification,switch_today,0.0,do not
```

## TABLE `opportunity_network_by_category_year` (56 rows)

```csv
year,pms_category,revenue_gap_eur,tam_eur,markets,avg_capture_total
2023,air_filter,856643.6799999999,1420886.2916564113,18,0.4860166666666667
2023,blower_filter,1434988.98,1741706.476289633,18,0.17093333333333333
2023,brake_pad,3544158.0,4674604.227535428,18,0.28952222222222224
2023,brake_rotor,1569973.56,2446119.694136512,18,0.5102555555555556
2023,brake_shoe,2536749.68,2739796.4291759185,18,0.08310000000000001
2023,clutch_booster,548701.71,564318.7137169812,18,0.006427777777777778
2023,clutch_disc,3554244.92,3713075.421423827,18,0.07046666666666666
2023,clutch_kit,987873.62,1226148.1228871502,18,0.22077222222222223
2023,clutch_pressure_plate,2203804.8200000003,2308727.441248703,18,0.06988888888888889
2023,fuel_filter,998384.02,1589966.3496169192,18,0.42588888888888893
2023,oil_filter,416781.11,901686.3284478227,18,0.5786388888888889
2023,pilot_bearing,30879.74,31745.248688470067,18,0.018044444444444443
2023,release_bearing,474461.95,493544.8694617969,18,0.03296666666666667
2023,urea_filter,524278.37,559955.2299289053,18,0.021822222222222225
2024,air_filter,895866.62,1505838.452288051,18,0.5511444444444444
2024,blower_filter,1416656.71,1852703.2173702128,18,0.20804999999999998
2024,brake_pad,3034930.26,4371056.222092846,18,0.3167
2024,brake_rotor,1315633.19,2509144.9074753076,18,0.5896277777777779
2024,brake_shoe,2474748.65,2710329.0961372186,18,0.08528333333333332
2024,clutch_booster,1225932.81,1239797.5454000002,18,0.0029444444444444444
2024,clutch_disc,3481614.88,3669162.5933559057,18,0.07773333333333333
2024,clutch_kit,1029369.48,1254096.2747126804,18,0.22547777777777778
2024,clutch_pressure_plate,2098830.11,2226993.9184752717,18,0.07972777777777779
2024,fuel_filter,1024969.17,1627608.3979370827,18,0.46401666666666663
2024,oil_filter,329893.61,876437.0179755053,18,0.7207111111111111
2024,pilot_bearing,35325.189999999995,36281.630097112866,18,0.025505555555555556
2024,release_bearing,473429.24,495431.69288518885,18,0.034422222222222215
2024,urea_filter,547859.1,575435.6202405245,18,0.025861111111111112
2025,air_filter,739360.89,1468157.6173341628,18,0.7441555555555556
2025,blower_filter,1434690.67,1790053.1856445451,18,0.23222222222222222
2025,brake_pad,3010831.19,4259200.236480269,18,0.33169444444444446
2025,brake_rotor,1410562.03,2605175.928194612,18,0.6054388888888889
2025,brake_shoe,2608365.68,2834860.7179246643,18,0.09869444444444445
2025,clutch_booster,794416.02,803142.671768116,18,0.0018
2025,clutch_disc,3265784.7600000002,3446202.664485993,18,0.07113888888888889
2025,clutch_kit,1036659.3400000001,1219993.303924857,18,0.153
2025,clutch_pressure_plate,2090834.9900000002,2231484.9141900744,18,0.07948888888888889
2025,fuel_filter,1026902.26,1659327.020415101,18,0.5105555555555555
2025,oil_filter,350423.96,896686.6906347853,18,0.7040944444444445
2025,pilot_bearing,27609.68,28431.355621390376,18,0.013144444444444445
2025,release_bearing,451055.67000000004,472581.9284652475,18,0.03997222222222222
2025,urea_filter,521510.75000000006,574294.4729368837,18,0.04655555555555555
2026,air_filter,1192460.36,1535125.9763116052,18,0.2667777777777778
2026,blower_filter,2088462.21,2319954.831981138,18,0.11821111111111111
2026,brake_pad,3801594.66,4335212.797734416,18,0.11469444444444443
2026,brake_rotor,2056452.1300000001,2776476.885727786,18,0.21713333333333332
2026,brake_shoe,2439845.98,2552351.839554049,18,0.04204444444444445
2026,clutch_booster,616963.99,623712.2269689441,18,0.0031444444444444445
2026,clutch_disc,3877665.3499999996,3958666.9885477307,18,0.028466666666666664
2026,clutch_kit,1026113.54,1109513.4463513524,18,0.0687
2026,clutch_pressure_plate,2149997.77,2215181.5489034075,18,0.03152222222222222
2026,fuel_filter,1339872.49,1723179.24069515,18,0.23017222222222225
2026,oil_filter,664983.75,966613.1582752859,18,0.3179166666666667
2026,pilot_bearing,27900.76,28145.289523809523,18,0.002955555555555556
2026,release_bearing,409746.97,419335.99133277213,18,0.01393888888888889
2026,urea_filter,442495.1,460227.3636087409,18,0.01985
```

## TABLE `wallet_all_years` (54 rows)

```csv
distributor_code,country,year,uio_units,uio_proxy,theoretical_wallet_eur,captured_genuine_eur,captured_bvp_eur,captured_total_eur,uncaptured_eur,addressable_uncaptured_eur,structural_nonaddressable_eur,over_target_eur,gps_pct,bvp_share_of_captured_pct,assumption_note,rate_per_uio
IUK,United Kingdom,2023,46592,False,11648000.0,5176492.13,25871.65,5202363.78,6445636.22,6445636.22,0.0,0.0,44.7,0.5,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
ITUK,United Kingdom,2023,20204,False,10650705.0,5589960.11,209234.45,5799194.56,4851510.44,4851510.44,0.0,0.0,54.4,3.6,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",527.1582359928727
UTI,Israel,2023,9647,False,7663857.0,3317332.02,318011.37,3635343.39,4028513.61,4028513.61,0.0,0.0,47.4,8.7,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",794.4290452990567
UMI,Israel,2023,18153,False,4538250.0,3580216.39,84351.12,3664567.51,873682.49,873682.49,0.0,0.0,80.7,2.3,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
GERMANY,Germany,2023,12936,False,3619918.0,2006361.53,35437.64,2041799.17,1578118.83,1578118.83,0.0,0.0,56.4,1.7,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",279.83286951144095
PORTUGAL,Portugal,2023,6091,False,2688979.0,1268958.92,94673.9,1363632.82,1325346.18,1325346.18,0.0,0.0,50.7,6.9,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",441.46757511081927
BELGIUM,Belgium,2023,8814,False,2260861.0,1682381.26,78002.82,1760384.08,500476.92,500476.92,0.0,0.0,77.9,4.4,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",256.5079419105968
NORWAY,Norway,2023,8640,False,2160000.0,1111066.18,15281.0,1126347.18,1033652.82,1033652.82,0.0,0.0,52.1,1.4,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
SWEDEN,Sweden,2023,6356,False,1589000.0,704359.17,0.0,704359.17,884640.83,884640.83,0.0,0.0,44.3,0.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
HUNGARY,Hungary,2023,3799,False,949750.0,345304.36,12310.33,357614.69,592135.31,592135.31,0.0,0.0,37.7,3.4,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
IRELAND,Ireland,2023,1796,False,839062.0,1132621.13,62174.52,1194795.65,0.0,0.0,0.0,355733.65,142.4,5.2,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",467.1837416481069
GREECE,Greece,2023,2593,False,671233.0,403743.51,28525.54,432269.05,238963.95,238963.95,0.0,0.0,64.4,6.6,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",258.8634785962206
CYPRUS,Cyprus,2023,1934,False,581300.0,280400.7,10668.58,291069.28,290230.72,290230.72,0.0,0.0,50.1,3.7,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",300.56876938986557
MALTA,Malta,2023,973,False,349363.0,189025.95,845.55,189871.5,159491.5,159491.5,0.0,0.0,54.3,0.4,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",359.0575539568345
FINLAND,Finland,2023,1282,False,320500.0,217410.45,193.84,217604.29,102895.71,102895.71,0.0,0.0,67.9,0.1,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
ROMANIA,Romania,2023,905,False,226250.0,135965.62,5903.58,141869.2,84380.8,84380.8,0.0,0.0,62.7,4.2,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
DENMARK,Denmark,2023,706,False,176989.0,110414.52,0.0,110414.52,66574.48,66574.48,0.0,0.0,62.4,0.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.69263456090653
ICELAND,Iceland,2023,294,False,73500.0,80339.6,0.0,80339.6,0.0,0.0,0.0,6839.6,109.3,0.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
IUK,United Kingdom,2024,48876,False,12219000.0,7343416.44,78098.58,7421515.02,4797484.98,4797484.98,0.0,0.0,60.7,1.1,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
ITUK,United Kingdom,2024,22389,False,11835911.0,6447467.72,136285.58,6583753.3,5252157.7,5252157.7,0.0,0.0,55.6,2.1,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",528.6484880968333
UTI,Israel,2024,10049,False,8014955.0,2328628.51,310242.17,2638870.68,5376084.32,5376084.32,0.0,0.0,32.9,11.8,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",797.5873221216042
UMI,Israel,2024,18349,False,4587250.0,3190125.69,149529.83,3339655.52,1247594.48,1247594.48,0.0,0.0,72.8,4.5,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
GERMANY,Germany,2024,13464,False,3740523.0,2645106.68,52083.73,2697190.41,1043332.59,1043332.59,0.0,0.0,72.1,1.9,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",277.8166221033868
PORTUGAL,Portugal,2024,6903,False,2982419.0,1411587.89,125225.86,1536813.75,1445605.25,1445605.25,0.0,0.0,51.5,8.1,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",432.04679125018106
BELGIUM,Belgium,2024,9311,False,2388534.0,1994352.26,80707.99,2075060.25,313473.75,313473.75,0.0,0.0,86.9,3.9,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",256.52819246053053
NORWAY,Norway,2024,8237,False,2059250.0,1140330.4,21429.4,1161759.8,897490.2,897490.2,0.0,0.0,56.4,1.8,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
SWEDEN,Sweden,2024,7221,False,1805250.0,1097347.84,0.0,1097347.84,707902.16,707902.16,0.0,0.0,60.8,0.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
HUNGARY,Hungary,2024,3714,False,928500.0,380628.62,9007.36,389635.98,538864.02,538864.02,0.0,0.0,42.0,2.3,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
IRELAND,Ireland,2024,1951,False,896690.0,1209858.54,64894.85,1274753.39,0.0,0.0,0.0,378063.39,142.2,5.1,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",459.6053305996925
GREECE,Greece,2024,3118,False,800527.0,425389.19,31169.66,456558.85,343968.15,343968.15,0.0,0.0,57.0,6.8,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",256.74374599101986
CYPRUS,Cyprus,2024,2072,False,622157.0,366474.74,21123.5,387598.24,234558.76,234558.76,0.0,0.0,62.3,5.4,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",300.2688223938224
MALTA,Malta,2024,1054,False,391129.0,217739.75,0.0,217739.75,173389.25,173389.25,0.0,0.0,55.7,0.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",371.09013282732445
FINLAND,Finland,2024,1259,False,314750.0,271604.82,722.78,272327.6,42422.4,42422.4,0.0,0.0,86.5,0.3,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
ROMANIA,Romania,2024,986,False,246500.0,151041.61,3388.21,154429.82,92070.18,92070.18,0.0,0.0,62.6,2.2,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
DENMARK,Denmark,2024,830,False,207989.0,176896.06,350.5,177246.56,30742.44,30742.44,0.0,0.0,85.2,0.2,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.58915662650602
ICELAND,Iceland,2024,342,False,85500.0,76379.73,0.0,76379.73,9120.27,9120.27,0.0,0.0,89.3,0.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
ITUK,United Kingdom,2025,23067,False,12212051.0,5415593.07,148950.85,5564543.92,6647507.08,6647507.08,0.0,0.0,45.6,2.7,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",529.416525772749
IUK,United Kingdom,2025,47783,False,11945750.0,6078616.15,53304.26,6131920.41,5813829.59,5813829.59,0.0,0.0,51.3,0.9,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
UTI,Israel,2025,10336,False,8271300.0,2960730.57,370781.37,3331511.94,4939788.06,4939788.06,0.0,0.0,40.3,11.1,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",800.2418730650155
UMI,Israel,2025,18542,False,4635500.0,3195666.26,123677.9,3319344.16,1316155.84,1316155.84,0.0,0.0,71.6,3.7,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
GERMANY,Germany,2025,13780,False,3808128.0,2518135.14,17796.68,2535931.82,1272196.18,1272196.18,0.0,0.0,66.6,0.7,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",276.35181422351235
PORTUGAL,Portugal,2025,7208,False,3052087.0,1606888.39,102905.6,1709793.99,1342293.01,1342293.01,0.0,0.0,56.0,6.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",423.4304938956715
BELGIUM,Belgium,2025,9593,False,2453507.0,2037228.79,72102.83,2109331.62,344175.38,344175.38,0.0,0.0,86.0,3.4,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",255.76013760033356
SWEDEN,Sweden,2025,8443,False,2110750.0,1277089.38,1372.8,1278462.18,832287.82,832287.82,0.0,0.0,60.6,0.1,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
NORWAY,Norway,2025,7929,False,1982250.0,1391446.18,25105.75,1416551.93,565698.07,565698.07,0.0,0.0,71.5,1.8,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
IRELAND,Ireland,2025,2161,False,956313.0,1134000.36,53458.26,1187458.62,0.0,0.0,0.0,231145.62,124.2,4.5,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",442.5326237852846
GREECE,Greece,2025,3742,False,953593.0,479638.89,40665.05,520303.94,433289.06,433289.06,0.0,0.0,54.6,7.8,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",254.83511491181187
HUNGARY,Hungary,2025,3734,False,933500.0,318741.13,11289.45,330030.58,603469.42,603469.42,0.0,0.0,35.4,3.4,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
CYPRUS,Cyprus,2025,2308,False,676267.0,391862.17,36580.94,428443.11,247823.89,247823.89,0.0,0.0,63.4,8.5,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",293.00996533795495
MALTA,Malta,2025,1040,False,378827.0,206295.86,206.41,206502.27,172324.73,172324.73,0.0,0.0,54.5,0.1,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",364.2567307692308
FINLAND,Finland,2025,1204,False,301000.0,277256.75,663.86,277920.61,23079.39,23079.39,0.0,0.0,92.3,0.2,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
ROMANIA,Romania,2025,1071,False,267750.0,169383.22,5835.21,175218.43,92531.57,92531.57,0.0,0.0,65.4,3.3,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
DENMARK,Denmark,2025,851,False,213239.0,148214.21,6.3,148220.51,65018.49,65018.49,0.0,0.0,69.5,0.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.57461809635723
ICELAND,Iceland,2025,406,False,101500.0,85281.57,0.0,85281.57,16218.43,16218.43,0.0,0.0,84.0,0.0,"addressable split = 100% ASSUMPTION (PMS convention); wallet = GPS max-spend targets (ceiling, not forecast); targets flat across vehicle age",250.0
```

## TABLE `gps_spu_by_distributor` (89 rows)

```csv
year,distributor_code,country,region,total_sales_eur,warranty_parts_eur,sales_ex_warranty_eur,uio_units,spend_per_unit_eur,spend_per_unit_ex_warranty_eur,uio_proxy,uio_source,traffic_light,warranty_data_gap,max_spend_eur,gps_capture_vs_max,traffic_light_v9,gps_capture_ex_warranty_vs_max,traffic_light_v9_ex_warranty,period_basis,coverage_note
2023,IRELAND,Ireland,UK/IE,1194795.65,,,1796.0,665.2537026726058,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,UTI,Israel,MENA,3635343.39,,,9647.0,376.8366735772779,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,ITUK,United Kingdom,UK/IE,5799194.56,,,20204.0,287.0320015838448,,False,ituk_dvla_2026,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,ICELAND,Iceland,Nordics,80339.6,,,294.0,273.2639455782313,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,PORTUGAL,Portugal,Iberia,1363632.82,,,6091.0,223.8766737809884,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,UMI,Israel,MENA,3664567.51,,,18153.0,201.8711788685066,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,BELGIUM,Belgium,Benelux,1760384.08,,,8814.0,199.7258997050148,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,MALTA,Malta,Med,189871.5,,,973.0,195.14028776978412,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,FINLAND,Finland,Nordics,217604.29,,,1282.0,169.73813572542903,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,GREECE,Greece,Med,432269.05,,,2593.0,166.70615117624374,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,GERMANY,Germany,DACH,2041799.17,,,12936.0,157.83852581941866,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,ROMANIA,Romania,CEE,141869.2,,,905.0,156.761546961326,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,DENMARK,Denmark,Nordics,110414.52,,,706.0,156.3945042492918,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,CYPRUS,Cyprus,Med,291069.28,,,1934.0,150.5011789038263,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2023,NORWAY,Norway,Nordics,1126347.18,,,8640.0,130.36425694444443,,False,v18_actual,amber,False,,,amber,,,full_year,FULL YEAR - calendar year complete.
2023,IUK,United Kingdom,UK/IE,5202363.78,,,46592.0,111.65787645947805,,False,v18_actual,amber,False,,,amber,,,full_year,FULL YEAR - calendar year complete.
2023,SWEDEN,Sweden,Nordics,704359.17,,,6356.0,110.81799402139713,,False,v18_actual,amber,False,,,amber,,,full_year,FULL YEAR - calendar year complete.
2023,HUNGARY,Hungary,CEE,357614.69,,,3799.0,94.13390102658596,,False,v18_actual,amber,False,,,amber,,,full_year,FULL YEAR - calendar year complete.
2023,UKRAINE,Ukraine,CIS,503073.33,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2023,ARMENIA,Armenia,CIS,276921.22,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2023,KAZAKHSTAN,Kazakhstan,CIS,176849.86,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2023,PALESTINE,Palestine,MENA,11402.13,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2024,IRELAND,Ireland,UK/IE,1274753.39,,,1951.0,653.3846181445413,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,ITUK,United Kingdom,UK/IE,6583753.3,,,22389.0,294.06196346420114,,False,ituk_dvla_2026,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,UTI,Israel,MENA,2638870.68,,,10049.0,262.6003264006369,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,ICELAND,Iceland,Nordics,76379.73,,,342.0,223.33254385964912,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,BELGIUM,Belgium,Benelux,2075060.25,,,9311.0,222.86115884437763,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,PORTUGAL,Portugal,Iberia,1536813.75,,,6903.0,222.62983485441111,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,FINLAND,Finland,Nordics,272327.6,,,1259.0,216.30468625893565,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,DENMARK,Denmark,Nordics,177246.56,,,830.0,213.55007228915665,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,MALTA,Malta,Med,217739.75,,,1054.0,206.5842030360532,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,GERMANY,Germany,DACH,2697190.41,,,13464.0,200.3260851158645,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,CYPRUS,Cyprus,Med,387598.24,,,2072.0,187.06478764478763,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,UMI,Israel,MENA,3339655.52,,,18349.0,182.0074946863589,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,ROMANIA,Romania,CEE,154429.82,,,986.0,156.6225354969574,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,SWEDEN,Sweden,Nordics,1097347.84,,,7221.0,151.9661875086553,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,IUK,United Kingdom,UK/IE,7421515.02,,,48876.0,151.84374785170635,,False,v18_actual,green,False,,,green,,,full_year,FULL YEAR - calendar year complete.
2024,GREECE,Greece,Med,456558.85,,,3118.0,146.42682809493263,,False,v18_actual,amber,False,,,amber,,,full_year,FULL YEAR - calendar year complete.
2024,NORWAY,Norway,Nordics,1161759.8,,,8237.0,141.04161709360204,,False,v18_actual,amber,False,,,amber,,,full_year,FULL YEAR - calendar year complete.
2024,HUNGARY,Hungary,CEE,389635.98,,,3714.0,104.9100646203554,,False,v18_actual,amber,False,,,amber,,,full_year,FULL YEAR - calendar year complete.
2024,UKRAINE,Ukraine,CIS,890339.43,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2024,KAZAKHSTAN,Kazakhstan,CIS,160728.16,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2024,ARMENIA,Armenia,CIS,129169.79,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2024,PALESTINE,Palestine,MENA,6642.62,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2025,IRELAND,Ireland,UK/IE,1187458.62,34857.0,1152601.62,3056.0,388.57,377.16,False,v18_actual,green,False,1391176.0,0.8536,green,0.8285,amber,full_year,FULL YEAR - calendar year complete.
2025,UTI,Israel,MENA,3331511.94,255967.77,3075544.17,10336.0,322.32,297.56,False,v18_actual,green,False,8271300.0,0.4028,red,0.3718,red,full_year,FULL YEAR - calendar year complete.
2025,ITUK,United Kingdom,UK/IE,5564543.92,374426.05,5190117.87,22389.0,248.54,231.82,False,ituk_dvla_2026,green,False,11835911.0,0.4701,red,0.4385,red,full_year,FULL YEAR - calendar year complete.
2025,PORTUGAL,Portugal,Iberia,1709793.99,130588.0,1579205.99,8176.0,209.12,193.15,False,v18_actual,green,False,3494069.0,0.4893,red,0.452,red,full_year,FULL YEAR - calendar year complete.
2025,FINLAND,Finland,Nordics,277920.61,48676.0,229244.61,1204.0,230.83,190.4,False,v18_actual,green,False,301000.0,0.9233,green,0.7616,amber,full_year,FULL YEAR - calendar year complete.
2025,BELGIUM,Belgium,Benelux,2109331.62,74677.0,2034654.62,9594.0,219.86,212.08,False,v18_actual,green,False,2454394.0,0.8594,green,0.829,amber,full_year,FULL YEAR - calendar year complete.
2025,ICELAND,Iceland,Nordics,85281.57,7035.0,78246.57,406.0,210.05,192.73,False,v18_actual,green,False,101500.0,0.8402,amber,0.7709,amber,full_year,FULL YEAR - calendar year complete.
2025,MALTA,Malta,Med,206502.27,18219.0,188283.27,1040.0,198.56,181.04,False,v18_actual,green,False,378827.0,0.5451,amber,0.497,red,full_year,FULL YEAR - calendar year complete.
2025,CYPRUS,Cyprus,Med,428443.11,28041.0,400402.11,2308.0,185.63,173.48,False,v18_actual,green,False,676267.0,0.6335,amber,0.5921,amber,full_year,FULL YEAR - calendar year complete.
2025,GERMANY,Germany,DACH,2535931.82,259675.0,2276256.82,12855.0,197.27,177.07,False,v18_actual,green,False,3412284.0,0.7432,amber,0.6671,amber,full_year,FULL YEAR - calendar year complete.
2025,UMI,Israel,MENA,3319344.16,1791020.28,1528323.88,18542.0,179.02,82.42,False,v18_actual,green,False,4635500.0,0.7161,amber,0.3297,red,full_year,FULL YEAR - calendar year complete.
2025,NORWAY,Norway,Nordics,1416551.93,290712.0,1125839.93,7929.0,178.65,141.99,False,v18_actual,green,False,1982250.0,0.7146,amber,0.568,amber,full_year,FULL YEAR - calendar year complete.
2025,DENMARK,Denmark,Nordics,148220.51,9115.0,139105.51,851.0,174.17,163.46,False,v18_actual,green,False,213239.0,0.6951,amber,0.6523,amber,full_year,FULL YEAR - calendar year complete.
2025,ROMANIA,Romania,CEE,175218.43,19377.0,155841.43,1071.0,163.6,145.51,False,v18_actual,green,False,267750.0,0.6544,amber,0.582,amber,full_year,FULL YEAR - calendar year complete.
2025,SWEDEN,Sweden,Nordics,1278462.18,189618.0,1088844.18,8443.0,151.42,128.96,False,v18_actual,green,False,2110750.0,0.6057,amber,0.5159,amber,full_year,FULL YEAR - calendar year complete.
2025,GREECE,Greece,Med,520303.94,56159.0,464144.94,3742.0,139.04,124.04,False,v18_actual,amber,False,953593.0,0.5456,amber,0.4867,red,full_year,FULL YEAR - calendar year complete.
2025,IUK,United Kingdom,UK/IE,6131920.41,1054395.0,5077525.41,47783.0,128.33,106.26,False,v18_actual,amber,False,11945750.0,0.5133,amber,0.425,red,full_year,FULL YEAR - calendar year complete.
2025,HUNGARY,Hungary,CEE,330030.58,77434.0,252596.58,3734.0,88.39,67.65,False,v18_actual,amber,False,933500.0,0.3535,red,0.2706,red,full_year,FULL YEAR - calendar year complete.
2025,UKRAINE,Ukraine,CIS,1160671.97,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2025,ARMENIA,Armenia,CIS,274583.25,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2025,KAZAKHSTAN,Kazakhstan,CIS,161948.74,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2025,PALESTINE,Palestine,MENA,27335.98,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,full_year,FULL YEAR - calendar year complete.
2026,ITUK,United Kingdom,UK/IE,2200830.53,,,24172.0,91.04875599867614,,False,ituk_dvla_2026,amber,False,12537530.67,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,IRELAND,Ireland,UK/IE,246731.93,,,2778.0,88.81638948884088,,False,v18_actual,amber,False,1788780.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,BELGIUM,Belgium,Benelux,768031.23,,,10180.0,75.44511100196463,,False,v18_actual,amber,False,2605317.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,UTI,Israel,MENA,714801.15,,,10760.0,66.43133364312268,,False,v18_actual,amber,False,8610536.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,PORTUGAL,Portugal,Iberia,509806.47,,,8444.0,60.374996447181424,,False,v18_actual,amber,False,4093046.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,ICELAND,Iceland,Nordics,24320.15,,,439.0,55.3989749430524,,False,v18_actual,amber,False,109750.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,FINLAND,Finland,Nordics,64812.86,,,1308.0,49.55111620795107,,False,v18_actual,red,False,327000.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,DENMARK,Denmark,Nordics,45915.87,,,945.0,48.58822222222223,,False,v18_actual,red,False,236000.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,NORWAY,Norway,Nordics,392247.49,,,8111.0,48.35994205400074,,False,v18_actual,red,False,2027750.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,GERMANY,Germany,DACH,713380.09,,,14757.0,48.34180998848005,,False,v18_actual,red,False,3654465.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,MALTA,Malta,Med,47775.24,,,1108.0,43.1184476534296,,False,v18_actual,red,False,403651.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,SWEDEN,Sweden,Nordics,378949.71,,,9090.0,41.688636963696375,,False,v18_actual,red,False,2272500.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,UMI,Israel,MENA,691441.38,,,18886.0,36.611319495922906,,False,v18_actual,red,False,4721500.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,ROMANIA,Romania,CEE,43725.25,,,1209.0,36.16645988420182,,False,v18_actual,red,False,302250.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,CYPRUS,Cyprus,Med,93946.86,,,2634.0,35.666993166287014,,False,v18_actual,red,False,771948.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,IUK,United Kingdom,UK/IE,1651157.18,,,49280.0,33.50562459415584,,False,v18_actual,red,False,12320000.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,HUNGARY,Hungary,CEE,98570.5,,,3992.0,24.69200901803607,,False,v18_actual,red,False,998000.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,GREECE,Greece,Med,74673.79,,,4285.0,17.42678879813302,,False,v18_actual,red,False,1091788.0,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,UNMAPPED,,,178452.56,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,UKRAINE,Ukraine,CIS,126812.86,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,ARMENIA,Armenia,CIS,57154.53,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,KAZAKHSTAN,Kazakhstan,CIS,38581.43,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
2026,PALESTINE,Palestine,MENA,22859.86,,,0.0,,,False,v18_proxy_2025,unknown,False,,,unknown,,,partial_year,"PARTIAL YEAR - total_sales_eur covers part of the calendar year, NOT 12 months. Do not compare against a full-year row, and do not read a capture % or traffic light off this row: the max-spend target is a full-year figure. Basis not reconcilable to a clean quarter from sales_fact; see 01_data/00_derived/_data_integrity_open_issues.md."
```

## TABLE `opportunity_matrix_full` (1008 rows)

```csv
distributor_code,pms_category,year,capture_rate_total,capture_rate_genuine,revenue_gap_eur,revenue_gap_quotable,avg_sp_eur,tam_eur,uio_units,genuine_bvp_gap_pp,country,region
BELGIUM,air_filter,2023,0.3195,0.2944,61881.17,True,18.973455258001305,90930.28432397124,9593,0.0251,Belgium,Benelux
BELGIUM,blower_filter,2023,0.2256,0.1126,108505.9,True,14.61768270120259,140109.0269227567,9593,0.1129999999999999,Belgium,Benelux
BELGIUM,brake_pad,2023,0.2729,0.2513,220561.81,True,78.9,303331.05000000005,9593,0.0215999999999999,Belgium,Benelux
BELGIUM,brake_rotor,2023,0.4695,0.4695,73615.24,True,57.90866666666667,138760.74706666666,9593,0.0,Belgium,Benelux
BELGIUM,brake_shoe,2023,0.0726,0.0624,174386.57,True,39.236839080459774,188042.55129310343,9593,0.0102,Belgium,Benelux
BELGIUM,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,9593,0.0,Belgium,Benelux
BELGIUM,clutch_disc,2023,0.133,0.0579,141796.83,True,85.31780392156863,163554.23011764706,9593,0.0751,Belgium,Benelux
BELGIUM,clutch_kit,2023,0.1941,0.0758,50135.52,True,43.2673476702509,62205.46574551972,9593,0.1182999999999999,Belgium,Benelux
BELGIUM,clutch_pressure_plate,2023,0.0923,0.0459,133006.45,True,76.44118644067797,146537.75440677966,9593,0.0463999999999999,Belgium,Benelux
BELGIUM,fuel_filter,2023,0.3156,0.0187,48504.4,True,7.394052892561983,70871.25756991735,9593,0.2969,Belgium,Benelux
BELGIUM,oil_filter,2023,0.6283,0.4367,18734.6,True,5.258214878777815,50399.463791597474,9593,0.1916,Belgium,Benelux
BELGIUM,pilot_bearing,2023,0.0365,0.0365,2868.37,True,3.106,2977.101,9593,0.0,Belgium,Benelux
BELGIUM,release_bearing,2023,0.057,0.0522,35066.83,True,25.865487804878047,37186.81181707317,9593,0.0047999999999999,Belgium,Benelux
BELGIUM,urea_filter,2023,0.0204,0.0204,95898.88,True,10.303969072164948,97898.01015463917,9593,0.0,Belgium,Benelux
CYPRUS,air_filter,2023,0.4566,0.3979,9388.8,True,15.623524752475248,17278.05602376238,2308,0.0587,Cyprus,Med
CYPRUS,blower_filter,2023,0.1049,0.0285,30728.5,True,15.520387931034485,34329.54606465517,2308,0.0764,Cyprus,Med
CYPRUS,brake_pad,2023,0.3227,0.1474,39134.56,True,64.53166089965399,57781.649169550175,2308,0.1752999999999999,Cyprus,Med
CYPRUS,brake_rotor,2023,0.1971,0.1971,28835.97,True,64.9502752293578,35917.50220183486,2308,0.0,Cyprus,Med
CYPRUS,brake_shoe,2023,0.0995,0.0995,40775.04,True,40.941272727272725,45276.95350909091,2308,0.0,Cyprus,Med
CYPRUS,clutch_booster,2023,0.009,0.009,20809.7,True,94.94,21000.728,2308,0.0,Cyprus,Med
CYPRUS,clutch_disc,2023,0.0565,0.0565,38788.24,True,92.9336,41113.824640000006,2308,0.0,Cyprus,Med
CYPRUS,clutch_kit,2023,0.4732,0.437,8438.58,True,48.28063694267516,16019.515337579618,2308,0.0362,Cyprus,Med
CYPRUS,clutch_pressure_plate,2023,0.0565,0.0497,12728.8,True,30.4972,13491.96128,2308,0.0068,Cyprus,Med
CYPRUS,fuel_filter,2023,0.311,0.1044,12500.22,True,8.202892441860465,18143.977792151163,2308,0.2066,Cyprus,Med
CYPRUS,oil_filter,2023,0.6144,0.4358,4493.63,True,5.268778513612952,11654.011194260487,2308,0.1785999999999999,Cyprus,Med
CYPRUS,pilot_bearing,2023,0.0226,0.0226,644.24,True,2.98,659.1759999999999,2308,0.0,Cyprus,Med
CYPRUS,release_bearing,2023,0.0301,0.0301,10210.78,True,31.732,10528.6776,2308,0.0,Cyprus,Med
CYPRUS,urea_filter,2023,0.0056,0.0056,21714.64,True,10.27,21838.128,2308,0.0,Cyprus,Med
DENMARK,air_filter,2023,0.3104,0.3104,5604.25,True,19.110833333333336,8125.926333333334,851,0.0,Denmark,Nordics
DENMARK,blower_filter,2023,0.1317,0.1317,10212.4,True,13.828571428571427,11761.2,851,0.0,Denmark,Nordics
DENMARK,brake_pad,2023,0.432,0.4115,14641.51,True,75.76462585034014,25775.125714285718,851,0.0205,Denmark,Nordics
DENMARK,brake_rotor,2023,0.5267,0.5267,5488.87,True,54.54776785714286,11596.855446428572,851,0.0,Denmark,Nordics
DENMARK,brake_shoe,2023,0.087,0.087,10009.82,True,25.78189189189189,10962.460432432432,851,0.0,Denmark,Nordics
DENMARK,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_disc,2023,0.0059,0.0059,28128.09,True,166.34,28294.434,851,0.0,Denmark,Nordics
DENMARK,clutch_kit,2023,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_pressure_plate,2023,0.0059,0.0059,24458.62,True,144.64,24603.264,851,0.0,Denmark,Nordics
DENMARK,fuel_filter,2023,0.1446,0.1446,8944.82,True,12.295284552845528,10457.13951219512,851,0.0,Denmark,Nordics
DENMARK,oil_filter,2023,0.2939,0.2939,2998.66,True,4.993600000000001,4247.0568,851,0.0,Denmark,Nordics
DENMARK,pilot_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,release_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,urea_filter,2023,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
FINLAND,air_filter,2023,0.407,0.407,6720.87,True,18.82595918367347,11333.227428571428,1204,0.0,Finland,Nordics
FINLAND,blower_filter,2023,0.3189,0.314,11972.9,True,14.60109375,17579.716875,1204,0.0049,Finland,Nordics
FINLAND,brake_pad,2023,0.1329,0.1204,31229.11,True,74.78234375,36015.17675,1204,0.0124999999999999,Finland,Nordics
FINLAND,brake_rotor,2023,0.206,0.206,19054.16,True,79.72451612903225,23997.07935483871,1204,0.0,Finland,Nordics
FINLAND,brake_shoe,2023,0.015,0.015,23915.69,True,40.330000000000005,24278.660000000003,1204,0.0,Finland,Nordics
FINLAND,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,clutch_disc,2023,0.0208,0.0208,34660.24,True,146.99,35395.192,1204,0.0,Finland,Nordics
FINLAND,clutch_kit,2023,0.0332,0.0332,13127.01,True,75.18333333333334,13578.11,1204,0.0,Finland,Nordics
FINLAND,clutch_pressure_plate,2023,0.0249,0.0249,16490.0,True,70.23,16911.384000000002,1204,0.0,Finland,Nordics
FINLAND,fuel_filter,2023,0.1578,0.1578,13349.58,True,13.165263157894737,15850.976842105263,1204,0.0,Finland,Nordics
FINLAND,oil_filter,2023,0.6204,0.6138,2407.28,True,5.267563587684069,6342.14655957162,1204,0.0065999999999999,Finland,Nordics
FINLAND,pilot_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,release_bearing,2023,0.0332,0.0332,4574.52,True,26.2,4731.719999999999,1204,0.0,Finland,Nordics
FINLAND,urea_filter,2023,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
GERMANY,air_filter,2023,0.2991,0.2967,91553.72,True,19.35899405351833,130620.94057730424,13780,0.0023999999999999,Germany,DACH
GERMANY,blower_filter,2023,0.2526,0.1956,145157.14,True,14.392628336755648,194221.3230903491,13780,0.0569999999999999,Germany,DACH
GERMANY,brake_pad,2023,0.1961,0.1806,336317.13,True,76.86440487347704,418334.5235238988,13780,0.0154999999999999,Germany,DACH
GERMANY,brake_rotor,2023,0.5635,0.5635,78620.38,True,53.38773277222514,180108.85528037875,13780,0.0,Germany,DACH
GERMANY,brake_shoe,2023,0.0356,0.0304,191354.66,True,29.406333333333336,198413.35290000003,13780,0.0052,Germany,DACH
GERMANY,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,13780,0.0,Germany,DACH
GERMANY,clutch_disc,2023,0.0408,0.0352,316814.54,True,122.374,330275.1886,13780,0.0056,Germany,DACH
GERMANY,clutch_kit,2023,0.082,0.0578,105613.91,True,56.83734939759036,115050.1626506024,13780,0.0242,Germany,DACH
GERMANY,clutch_pressure_plate,2023,0.033,0.027,208660.95,True,79.94966292134832,215776.145258427,13780,0.006,Germany,DACH
GERMANY,fuel_filter,2023,0.267,0.1638,105413.93,True,10.656999722453511,143810.88275464892,13780,0.1032,Germany,DACH
GERMANY,oil_filter,2023,0.3152,0.2739,49100.83,True,5.313068422290148,71697.2018245944,13780,0.0413,Germany,DACH
GERMANY,pilot_bearing,2023,0.0608,0.0608,3798.34,True,2.996829268292683,4044.221097560976,13780,0.0,Germany,DACH
GERMANY,release_bearing,2023,0.04,0.0351,49393.67,True,25.41901234567901,51453.16479012346,13780,0.0049,Germany,DACH
GERMANY,urea_filter,2023,0.0032,0.0032,120532.92,True,9.204285714285714,120919.4627142857,13780,0.0,Germany,DACH
GREECE,air_filter,2023,0.3996,0.3733,16870.45,True,15.093225806451612,28100.56780645161,3742,0.0262999999999999,Greece,Med
GREECE,blower_filter,2023,0.1064,0.0338,50455.32,True,15.163131313131316,56459.91944444445,3742,0.0726,Greece,Med
GREECE,brake_pad,2023,0.2381,0.1569,77149.45,True,67.89830985915493,101249.95966197184,3742,0.0812,Greece,Med
GREECE,brake_rotor,2023,0.2632,0.2632,46356.25,True,67.58702040816327,62916.75729795919,3742,0.0,Greece,Med
GREECE,brake_shoe,2023,0.0628,0.0591,70736.79,True,40.54264957264957,75482.30497435898,3742,0.0036999999999999,Greece,Med
GREECE,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,3742,0.0,Greece,Med
GREECE,clutch_disc,2023,0.0618,0.0134,58319.58,True,83.4686956521739,62159.13765217392,3742,0.0484,Greece,Med
GREECE,clutch_kit,2023,0.2077,0.0555,17305.55,True,39.10637931034483,21840.912844827588,3742,0.1522,Greece,Med
GREECE,clutch_pressure_plate,2023,0.0792,0.0389,43157.49,True,62.93932203389831,46870.91311864407,3742,0.0403,Greece,Med
GREECE,fuel_filter,2023,0.3516,0.1286,21643.0,True,8.96375859434683,33376.55512605042,3742,0.223,Greece,Med
GREECE,oil_filter,2023,0.5092,0.2487,8892.17,True,4.865754219409283,18117.635835970465,3742,0.2604999999999999,Greece,Med
GREECE,pilot_bearing,2023,0.0107,0.0107,1097.68,True,2.98,1109.752,3742,0.0,Greece,Med
GREECE,release_bearing,2023,0.0179,0.0072,14044.98,True,25.605,14300.3925,3742,0.0107,Greece,Med
GREECE,urea_filter,2023,0.0005,0.0005,39216.89,True,10.58,39238.046,3742,0.0,Greece,Med
HUNGARY,air_filter,2023,0.4242,0.4242,20123.39,True,18.719431818181818,34949.17920454546,3734,0.0,Hungary,CEE
HUNGARY,blower_filter,2023,0.2606,0.1374,40133.67,True,14.535919835560124,54277.1246659815,3734,0.1232,Hungary,CEE
HUNGARY,brake_pad,2023,0.1165,0.0984,102328.31,True,77.54494252873563,115821.12616091954,3734,0.0181,Hungary,CEE
HUNGARY,brake_rotor,2023,0.2239,0.2239,55162.08,True,76.13813397129186,71074.94806220096,3734,0.0,Hungary,CEE
HUNGARY,brake_shoe,2023,0.0086,0.008,71961.1,True,38.876875,72583.125625,3734,0.0005999999999999,Hungary,CEE
HUNGARY,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,clutch_disc,2023,0.0147,0.0147,107318.44,True,145.8527272727273,108922.81672727272,3734,0.0,Hungary,CEE
HUNGARY,clutch_kit,2023,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,clutch_pressure_plate,2023,0.0134,0.0134,52056.39,True,70.652,52762.9136,3734,0.0,Hungary,CEE
HUNGARY,fuel_filter,2023,0.1243,0.0005,23035.53,True,7.044504310344828,26304.17909482759,3734,0.1238,Hungary,CEE
HUNGARY,oil_filter,2023,0.4462,0.3816,10196.44,True,4.930582232893157,18410.79405762305,3734,0.0645999999999999,Hungary,CEE
HUNGARY,pilot_bearing,2023,0.0161,0.0161,1100.36,True,2.995,1118.333,3734,0.0,Hungary,CEE
HUNGARY,release_bearing,2023,0.0179,0.0,8993.03,True,16.348,9156.5148,3734,0.0179,Hungary,CEE
HUNGARY,urea_filter,2023,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
ICELAND,air_filter,2023,0.5222,0.5222,1915.47,True,19.747075471698118,4008.656320754717,406,0.0,Iceland,Nordics
ICELAND,blower_filter,2023,0.1773,0.1773,4727.03,True,14.15277777777778,5746.027777777778,406,0.0,Iceland,Nordics
ICELAND,brake_pad,2023,0.2155,0.197,9658.45,True,75.812,12311.8688,406,0.0184999999999999,Iceland,Nordics
ICELAND,brake_rotor,2023,0.5813,0.5813,2554.22,True,60.09932203389831,6100.081186440679,406,0.0,Iceland,Nordics
ICELAND,brake_shoe,2023,0.0443,0.0443,6322.89,True,32.59222222222222,6616.22111111111,406,0.0,Iceland,Nordics
ICELAND,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,clutch_disc,2023,0.0616,0.0616,10616.79,True,139.328,11313.4336,406,0.0,Iceland,Nordics
ICELAND,clutch_kit,2023,0.0657,0.0657,1747.54,True,30.7125,1870.39125,406,0.0,Iceland,Nordics
ICELAND,clutch_pressure_plate,2023,0.0739,0.0739,7764.53,True,103.25166666666668,8384.035333333333,406,0.0,Iceland,Nordics
ICELAND,fuel_filter,2023,0.2734,0.2734,3762.15,True,12.75306306306306,5177.743603603603,406,0.0,Iceland,Nordics
ICELAND,oil_filter,2023,0.367,0.367,1472.82,True,5.730805369127516,2326.706979865772,406,0.0,Iceland,Nordics
ICELAND,pilot_bearing,2023,0.0493,0.0493,113.87,True,2.95,119.77,406,0.0,Iceland,Nordics
ICELAND,release_bearing,2023,0.0328,0.0328,1528.45,True,25.95,1580.355,406,0.0,Iceland,Nordics
ICELAND,urea_filter,2023,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
IRELAND,air_filter,2023,1.6424,1.4315,0.0,True,25.346070038910504,23797.42515953307,2161,0.2109000000000001,Ireland,UK/IE
IRELAND,blower_filter,2023,0.1406,0.0831,20242.43,True,12.544090909090908,23554.0395,2161,0.0575,Ireland,UK/IE
IRELAND,brake_pad,2023,0.6956,0.6472,21003.81,True,85.71183928571428,69006.60180892856,2161,0.0484,Ireland,UK/IE
IRELAND,brake_rotor,2023,2.2858,2.2858,0.0,True,60.47251630941286,28385.7991556384,2161,0.0,Ireland,UK/IE
IRELAND,brake_shoe,2023,0.3515,0.3355,22421.08,True,36.82521212121212,34575.191660606055,2161,0.0159999999999999,Ireland,UK/IE
IRELAND,clutch_booster,2023,0.0053,0.0053,63625.16,True,340.66,63975.94800000001,2161,0.0,Ireland,UK/IE
IRELAND,clutch_disc,2023,0.5725,0.2397,11931.72,True,74.32213953488372,27907.96339534884,2161,0.3328,Ireland,UK/IE
IRELAND,clutch_kit,2023,1.7113,1.0509,0.0,True,43.91842323651452,12371.81982572614,2161,0.6604000000000001,Ireland,UK/IE
IRELAND,clutch_pressure_plate,2023,0.5885,0.1891,11441.64,True,74.03647058823529,27800.69470588235,2161,0.3994,Ireland,UK/IE
IRELAND,fuel_filter,2023,1.8288,0.9639,0.0,True,12.882093768200347,24188.7074685498,2161,0.8649,Ireland,UK/IE
IRELAND,oil_filter,2023,1.6233,1.1045,0.0,True,7.767168635170604,14584.412546259844,2161,0.5187999999999999,Ireland,UK/IE
IRELAND,pilot_bearing,2023,0.0852,0.0852,511.88,True,2.98,559.644,2161,0.0,Ireland,UK/IE
IRELAND,release_bearing,2023,0.1172,0.0817,6064.18,True,24.387878787878787,6870.065454545454,2161,0.0355,Ireland,UK/IE
IRELAND,urea_filter,2023,0.0467,0.0467,14261.69,True,10.27,14960.309,2161,0.0,Ireland,UK/IE
ITUK,air_filter,2023,0.4253,0.3618,144073.46,True,29.007366702937976,250704.86894015232,23068,0.0635,United Kingdom,UK/IE
ITUK,blower_filter,2023,0.0,0.0,0.0,False,0.0,0.0,23068,0.0,United Kingdom,UK/IE
ITUK,brake_pad,2023,0.4906,0.4906,300271.57,True,85.25039209905661,589438.2610512972,23068,0.0,United Kingdom,UK/IE
ITUK,brake_rotor,2023,1.4891,1.4891,0.0,True,50.44925874125874,218011.4267244755,23068,0.0,United Kingdom,UK/IE
ITUK,brake_shoe,2023,0.139,0.139,249405.31,True,41.89411030176899,289664.2574484911,23068,0.0,United Kingdom,UK/IE
ITUK,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,23068,0.0,United Kingdom,UK/IE
ITUK,clutch_disc,2023,0.0622,0.0388,251776.81,True,77.65818604651162,268472.1149813953,23068,0.0233999999999999,United Kingdom,UK/IE
ITUK,clutch_kit,2023,0.2457,0.1327,145279.45,True,74.27995290423863,192593.06189010997,23068,0.1129999999999999,United Kingdom,UK/IE
ITUK,clutch_pressure_plate,2023,0.039,0.0185,222640.06,True,67.01755555555556,231686.39131111116,23068,0.0205,United Kingdom,UK/IE
ITUK,fuel_filter,2023,0.9826,0.7532,3472.72,True,11.553487194583456,199708.9582506918,23068,0.2294,United Kingdom,UK/IE
ITUK,oil_filter,2023,1.0431,0.4983,0.0,True,7.6681397670549085,132548.39675740432,23068,0.5448,United Kingdom,UK/IE
ITUK,pilot_bearing,2023,0.0168,0.0168,4928.72,True,2.9,5012.94,23068,0.0,United Kingdom,UK/IE
ITUK,release_bearing,2023,0.0247,0.0139,57079.4,True,22.57140625,58523.142125,23068,0.0108,United Kingdom,UK/IE
ITUK,urea_filter,2023,0.2857,0.2857,79627.67,True,31.31940019665684,111478.27305998036,23068,0.0,United Kingdom,UK/IE
IUK,air_filter,2023,0.3112,0.3112,241135.33,True,14.65289307330195,350079.5948607936,47783,0.0,United Kingdom,UK/IE
IUK,blower_filter,2023,0.1753,0.1659,523672.56,True,13.288483582089553,634963.6110029852,47783,0.0094,United Kingdom,UK/IE
IUK,brake_pad,2023,0.1708,0.1406,1136556.79,True,71.7151975497703,1370706.9138082697,47783,0.0302,United Kingdom,UK/IE
IUK,brake_rotor,2023,0.3136,0.3136,499088.12,True,60.86626001067806,727096.168835558,47783,0.0,United Kingdom,UK/IE
IUK,brake_shoe,2023,0.0597,0.0597,775923.24,True,34.53843618513324,825175.0481171107,47783,0.0,United Kingdom,UK/IE
IUK,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,47783,0.0,United Kingdom,UK/IE
IUK,clutch_disc,2023,0.0427,0.0427,1302339.09,True,142.35392156862744,1360419.4868627451,47783,0.0,United Kingdom,UK/IE
IUK,clutch_kit,2023,0.0066,0.0066,346918.93,True,48.721489361702126,349206.4028510638,47783,0.0,United Kingdom,UK/IE
IUK,clutch_pressure_plate,2023,0.0418,0.0418,579322.17,True,63.26135338345864,604563.4497443609,47783,0.0,United Kingdom,UK/IE
IUK,fuel_filter,2023,0.152,0.152,475741.23,True,11.74031951521829,560987.6873956756,47783,0.0,United Kingdom,UK/IE
IUK,oil_filter,2023,0.3157,0.3047,159170.46,True,4.868193809239743,232616.90478690265,47783,0.0109999999999999,United Kingdom,UK/IE
IUK,pilot_bearing,2023,0.023,0.023,13557.17,True,2.904090909090909,13876.61759090909,47783,0.0,United Kingdom,UK/IE
IUK,release_bearing,2023,0.0487,0.0439,165401.53,True,24.25793696275072,173866.3373868195,47783,0.0047999999999999,United Kingdom,UK/IE
IUK,urea_filter,2023,0.0,0.0,0.0,False,0.0,0.0,47783,0.0,United Kingdom,UK/IE
MALTA,air_filter,2023,0.5211,0.5211,4760.83,True,20.639442231075694,9942.019322709164,1040,0.0,Malta,Med
MALTA,blower_filter,2023,0.1526,0.1526,12577.92,True,15.4078231292517,14842.356020408162,1040,0.0,Malta,Med
MALTA,brake_pad,2023,0.2911,0.2513,21769.39,True,76.39273504273505,30709.879487179493,1040,0.0398,Malta,Med
MALTA,brake_rotor,2023,0.2865,0.2865,10029.29,True,58.36637681159421,14054.623536231886,1040,0.0,Malta,Med
MALTA,brake_shoe,2023,0.0415,0.0415,18361.64,True,39.7725,19158.41325,1040,0.0,Malta,Med
MALTA,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
MALTA,clutch_disc,2023,0.026,0.026,24978.44,True,133.1,25648.37,1040,0.0,Malta,Med
MALTA,clutch_kit,2023,0.0415,0.0415,5116.19,True,36.94,5337.83,1040,0.0,Malta,Med
MALTA,clutch_pressure_plate,2023,0.0156,0.0156,13320.29,True,70.23,13533.321,1040,0.0,Malta,Med
MALTA,fuel_filter,2023,0.4069,0.4069,7730.48,True,13.530586734693877,13034.01420153061,1040,0.0,Malta,Med
MALTA,oil_filter,2023,0.8201,0.8045,1178.46,True,6.798822784810127,6549.305988607594,1040,0.0156,Malta,Med
MALTA,pilot_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
MALTA,release_bearing,2023,0.0138,0.0138,3733.5,True,26.2,3785.9,1040,0.0,Malta,Med
MALTA,urea_filter,2023,0.0181,0.0181,8372.79,True,10.27,8527.181,1040,0.0,Malta,Med
NORWAY,air_filter,2023,0.5095,0.5095,36207.55,True,18.62049504950495,73820.95262376238,7929,0.0,Norway,Nordics
NORWAY,blower_filter,2023,0.2775,0.2775,82945.5,True,14.478181818181818,114797.50363636365,7929,0.0,Norway,Nordics
NORWAY,brake_pad,2023,0.3676,0.3484,139793.74,True,69.70170668953688,221065.9329365352,7929,0.0191999999999999,Norway,Nordics
NORWAY,brake_rotor,2023,0.5242,0.5242,55278.89,True,58.60470644850818,116166.24912223293,7929,0.0,Norway,Nordics
NORWAY,brake_shoe,2023,0.0444,0.0444,155930.14,True,41.158806818181816,163174.08963068182,7929,0.0,Norway,Nordics
NORWAY,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,clutch_disc,2023,0.0063,0.0063,232083.82,True,147.28,233556.624,7929,0.0,Norway,Nordics
NORWAY,clutch_kit,2023,0.0025,0.0025,37203.94,True,31.36,37296.448,7929,0.0,Norway,Nordics
NORWAY,clutch_pressure_plate,2023,0.005,0.005,145244.38,True,92.055,145980.81900000002,7929,0.0,Norway,Nordics
NORWAY,fuel_filter,2023,0.2763,0.0001,38802.05,True,6.762295755362849,53618.24304427203,7929,0.2762,Norway,Nordics
NORWAY,oil_filter,2023,0.5059,0.492,18677.34,True,4.767060583395662,37798.02336574421,7929,0.0139,Norway,Nordics
NORWAY,pilot_bearing,2023,0.0038,0.0038,2259.11,True,2.86,2267.694,7929,0.0,Norway,Nordics
NORWAY,release_bearing,2023,0.005,0.005,29808.59,True,25.19,29958.467,7929,0.0,Norway,Nordics
NORWAY,urea_filter,2023,0.0004,0.0004,80607.42,True,10.17,80637.93,7929,0.0,Norway,Nordics
PORTUGAL,air_filter,2023,0.2704,0.1665,59771.99,True,24.178668122270743,81919.7454650655,7208,0.1038999999999999,Portugal,Iberia
PORTUGAL,blower_filter,2023,0.126,0.001,65416.22,True,11.045948477751756,74849.55607494144,7208,0.125,Portugal,Iberia
PORTUGAL,brake_pad,2023,0.5143,0.2124,75173.42,True,53.09623082054703,154764.89359573048,7208,0.3018999999999999,Portugal,Iberia
PORTUGAL,brake_rotor,2023,0.2751,0.2751,83838.12,True,68.26942060085837,115648.39849785408,7208,0.0,Portugal,Iberia
PORTUGAL,brake_shoe,2023,0.0761,0.0679,165905.39,True,53.003294573643416,179580.46234496124,7208,0.0081999999999999,Portugal,Iberia
PORTUGAL,clutch_booster,2023,0.0044,0.003,127226.43,True,188.59,127788.584,7208,0.0014,Portugal,Iberia
PORTUGAL,clutch_disc,2023,0.0937,0.0317,106084.59,True,86.37133858267717,117050.4380472441,7208,0.062,Portugal,Iberia
PORTUGAL,clutch_kit,2023,0.2637,0.063,56145.31,True,75.01757462686567,76247.86285074626,7208,0.2007,Portugal,Iberia
PORTUGAL,clutch_pressure_plate,2023,0.0849,0.0288,114915.52,True,92.656,125567.41120000002,7208,0.0561,Portugal,Iberia
PORTUGAL,fuel_filter,2023,0.3592,0.0276,36152.05,True,8.325760065735416,56417.01535743632,7208,0.3316,Portugal,Iberia
PORTUGAL,oil_filter,2023,0.4587,0.0208,21866.26,True,5.961045688545688,40393.23779472329,7208,0.4379,Portugal,Iberia
PORTUGAL,pilot_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,7208,0.0,Portugal,Iberia
PORTUGAL,release_bearing,2023,0.0335,0.003,15627.55,True,15.907058823529413,16167.934588235295,7208,0.0305,Portugal,Iberia
PORTUGAL,urea_filter,2023,0.0066,0.0066,52777.77,True,10.27,53126.71,7208,0.0,Portugal,Iberia
ROMANIA,air_filter,2023,0.7152,0.7152,2780.5,True,18.23279373368146,9763.661044386425,1071,0.0,Romania,CEE
ROMANIA,blower_filter,2023,0.38,0.3613,8768.62,True,13.205749385749384,14143.357592137592,1071,0.0186999999999999,Romania,CEE
ROMANIA,brake_pad,2023,0.3688,0.2124,17616.95,True,65.15145569620253,27910.883620253164,1071,0.1564,Romania,CEE
ROMANIA,brake_rotor,2023,0.605,0.605,6867.6,True,64.94185185185185,17391.427925925927,1071,0.0,Romania,CEE
ROMANIA,brake_shoe,2023,0.099,0.099,20415.76,True,42.31245283018868,22658.318490566035,1071,0.0,Romania,CEE
ROMANIA,clutch_booster,2023,0.056,0.056,5771.8,True,57.09,6114.339,1071,0.0,Romania,CEE
ROMANIA,clutch_disc,2023,0.042,0.042,30599.42,True,149.12,31941.504,1071,0.0,Romania,CEE
ROMANIA,clutch_kit,2023,0.1681,0.0373,9826.99,True,73.52777777777777,11815.913888888888,1071,0.1308,Romania,CEE
ROMANIA,clutch_pressure_plate,2023,0.0373,0.0373,14736.6,True,71.4675,15308.3385,1071,0.0,Romania,CEE
ROMANIA,fuel_filter,2023,0.3035,0.0047,5407.51,True,7.248676923076924,7763.332984615386,1071,0.2988,Romania,CEE
ROMANIA,oil_filter,2023,0.4444,0.3978,3080.45,True,5.177226890756303,5544.81,1071,0.0466,Romania,CEE
ROMANIA,pilot_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,1071,0.0,Romania,CEE
ROMANIA,release_bearing,2023,0.0622,0.0622,4025.37,True,26.72,4293.904,1071,0.0,Romania,CEE
ROMANIA,urea_filter,2023,0.0056,0.0056,11267.7,True,10.58,11331.18,1071,0.0,Romania,CEE
SWEDEN,air_filter,2023,0.2307,0.2307,53148.64,True,16.36601642710472,69089.13834702258,8443,0.0,Sweden,Nordics
SWEDEN,blower_filter,2023,0.2366,0.2366,91077.4,True,14.13148148148148,119312.09814814814,8443,0.0,Sweden,Nordics
SWEDEN,brake_pad,2023,0.1353,0.1353,219255.9,True,75.08249452954047,253568.60052516405,8443,0.0,Sweden,Nordics
SWEDEN,brake_rotor,2023,0.2014,0.2014,119804.03,True,71.06868235294117,150011.77471058822,8443,0.0,Sweden,Nordics
SWEDEN,brake_shoe,2023,0.0147,0.0147,155145.32,True,37.299032258064514,157457.86467741933,8443,0.0,Sweden,Nordics
SWEDEN,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,clutch_disc,2023,0.0047,0.0047,243434.91,True,144.85,244593.71,8443,0.0,Sweden,Nordics
SWEDEN,clutch_kit,2023,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,clutch_pressure_plate,2023,0.0036,0.0036,118169.0,True,70.23,118590.378,8443,0.0,Sweden,Nordics
SWEDEN,fuel_filter,2023,0.1424,0.1424,92722.99,True,12.805274542429284,108114.93296173045,8443,0.0,Sweden,Nordics
SWEDEN,oil_filter,2023,0.2879,0.2879,30579.34,True,5.086384204031263,42944.341834635954,8443,0.0,Sweden,Nordics
SWEDEN,pilot_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,release_bearing,2023,0.0055,0.0055,32997.59,True,26.2,33182.3,8443,0.0,Sweden,Nordics
SWEDEN,urea_filter,2023,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
UMI,air_filter,2023,0.0475,0.0475,92478.63,True,10.472045454545452,97086.3334090909,18542,0.0,Israel,MENA
UMI,blower_filter,2023,0.0102,0.0,228395.47,True,12.445263157894736,230760.06947368415,18542,0.0102,Israel,MENA
UMI,brake_pad,2023,0.1693,0.0938,311652.01,True,50.58628980891719,375188.39425477706,18542,0.0755,Israel,MENA
UMI,brake_rotor,2023,0.1102,0.1102,194473.48,True,47.1508023483366,218567.5442857143,18542,0.0,Israel,MENA
UMI,brake_shoe,2023,0.0669,0.0453,276904.42,True,32.00837096774193,296749.60724193545,18542,0.0216,Israel,MENA
UMI,clutch_booster,2023,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UMI,clutch_disc,2023,0.0135,0.0135,482213.7,True,131.81,488804.204,18542,0.0,Israel,MENA
UMI,clutch_kit,2023,0.0457,0.0,36509.37,True,13.754803149606298,38256.234,18542,0.0457,Israel,MENA
UMI,clutch_pressure_plate,2023,0.045,0.045,197986.95,True,55.90640718562874,207323.32040718565,18542,0.0,Israel,MENA
UMI,fuel_filter,2023,0.1986,0.0179,101201.36,True,6.810320478001086,126276.96230309614,18542,0.1807,Israel,MENA
UMI,oil_filter,2023,0.4271,0.0,45372.99,True,4.271203434777119,79196.65408763735,18542,0.4271,Israel,MENA
UMI,pilot_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UMI,release_bearing,2023,0.0539,0.0,35911.98,True,13.648,37959.182400000005,18542,0.0539,Israel,MENA
UMI,urea_filter,2023,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UTI,air_filter,2023,0.9364,0.0076,8228.63,True,20.02100843114565,129335.71446520089,10336,0.9288,Israel,MENA
UTI,blower_filter,2023,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,brake_pad,2023,0.0813,0.0813,470044.09,True,79.19866666666667,511623.38666666666,10336,0.0,Israel,MENA
UTI,brake_rotor,2023,0.0625,0.0625,290906.86,True,96.07227722772276,310313.4554455445,10336,0.0,Israel,MENA
UTI,brake_shoe,2023,0.1776,0.1776,106874.82,True,20.11571926765475,129947.54646904967,10336,0.0,Israel,MENA
UTI,clutch_booster,2023,0.041,0.0348,331268.62,True,267.3677358490566,345439.1147169812,10336,0.0062,Israel,MENA
UTI,clutch_disc,2023,0.0097,0.0,132359.67,True,51.7232,133652.7488,10336,0.0097,Israel,MENA
UTI,clutch_kit,2023,0.4329,0.0062,154505.33,True,140.5871990464839,272457.9917520858,10336,0.4267,Israel,MENA
UTI,clutch_pressure_plate,2023,0.0182,0.0085,287704.98,True,113.4036170212766,293034.9463829788,10336,0.0097,Israel,MENA
UTI,fuel_filter,2023,1.0704,0.5092,0.0,True,8.967785089305083,115863.78335382168,10336,0.5612,Israel,MENA
UTI,oil_filter,2023,0.6947,0.283,38559.38,True,9.776720142602494,126315.22424242424,10336,0.4117,Israel,MENA
UTI,pilot_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,release_bearing,2023,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,urea_filter,2023,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
BELGIUM,air_filter,2024,0.3134,0.2589,65929.91,True,20.036684420772303,96025.81008655128,9593,0.0544999999999999,Belgium,Benelux
BELGIUM,blower_filter,2024,0.2346,0.1588,117257.33,True,15.983997332147622,153205.01602890174,9593,0.0758,Belgium,Benelux
BELGIUM,brake_pad,2024,0.3298,0.2279,180529.62,True,70.06885646687697,269379.7186869085,9593,0.1018999999999999,Belgium,Benelux
BELGIUM,brake_rotor,2024,0.5317,0.5317,66513.72,True,59.26923076923077,142020.93076923076,9593,0.0,Belgium,Benelux
BELGIUM,brake_shoe,2024,0.0624,0.0499,158663.03,True,35.30976588628763,169222.05301003347,9593,0.0124999999999999,Belgium,Benelux
BELGIUM,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,9593,0.0,Belgium,Benelux
BELGIUM,clutch_disc,2024,0.1195,0.0417,144655.08,True,85.69694323144104,164281.04017467247,9593,0.0778,Belgium,Benelux
BELGIUM,clutch_kit,2024,0.1996,0.0522,44453.53,True,38.63045296167248,55539.00222299652,9593,0.1474,Belgium,Benelux
BELGIUM,clutch_pressure_plate,2024,0.1033,0.035,134102.03,True,78.01237373737374,149549.72045454546,9593,0.0683,Belgium,Benelux
BELGIUM,fuel_filter,2024,0.3338,0.0419,46962.81,True,7.354116911534854,70488.47518537042,9593,0.2919,Belgium,Benelux
BELGIUM,oil_filter,2024,0.6697,0.5127,18179.77,True,5.742333696837513,55039.69425081788,9593,0.1569999999999999,Belgium,Benelux
BELGIUM,pilot_bearing,2024,0.0741,0.0741,2696.98,True,3.03887323943662,2912.76,9593,0.0,Belgium,Benelux
BELGIUM,release_bearing,2024,0.0619,0.057,33731.48,True,25.009662921348315,35956.39238202247,9593,0.0048999999999999,Belgium,Benelux
BELGIUM,urea_filter,2024,0.0118,0.0118,97551.54,True,10.39,98715.39,9593,0.0,Belgium,Benelux
CYPRUS,air_filter,2024,1.0561,0.8165,0.0,True,17.21951198630137,19043.058305650688,2308,0.2396,Cyprus,Med
CYPRUS,blower_filter,2024,0.326,0.2062,24211.04,True,16.239431345353676,35919.9981927878,2308,0.1198,Cyprus,Med
CYPRUS,brake_pad,2024,0.6366,0.2267,19041.02,True,58.50859649122808,52388.597298245615,2308,0.4099,Cyprus,Med
CYPRUS,brake_rotor,2024,0.4196,0.4196,23283.38,True,72.54068965517241,40115.00137931034,2308,0.0,Cyprus,Med
CYPRUS,brake_shoe,2024,0.1067,0.1067,40699.1,True,41.19593220338983,45558.581423728814,2308,0.0,Cyprus,Med
CYPRUS,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,2308,0.0,Cyprus,Med
CYPRUS,clutch_disc,2024,0.0746,0.0701,41247.35,True,100.75666666666666,44574.749333333326,2308,0.0045,Cyprus,Med
CYPRUS,clutch_kit,2024,0.6571,0.5757,5009.84,True,44.03022935779816,14609.230100917432,2308,0.0814,Cyprus,Med
CYPRUS,clutch_pressure_plate,2024,0.0407,0.0294,38456.94,True,90.62,40090.288,2308,0.0113,Cyprus,Med
CYPRUS,fuel_filter,2024,0.4937,0.2084,9821.49,True,8.770128205128204,19398.646576923074,2308,0.2853,Cyprus,Med
CYPRUS,oil_filter,2024,0.8509,0.5945,1876.59,True,5.688724760892668,12582.890298618491,2308,0.2563999999999999,Cyprus,Med
CYPRUS,pilot_bearing,2024,0.0407,0.0407,647.88,True,3.053333333333333,675.3973333333332,2308,0.0,Cyprus,Med
CYPRUS,release_bearing,2024,0.0301,0.0301,9763.19,True,30.341,10067.1438,2308,0.0,Cyprus,Med
CYPRUS,urea_filter,2024,0.0235,0.0235,21634.18,True,10.4192,22155.38688,2308,0.0,Cyprus,Med
DENMARK,air_filter,2024,0.4633,0.4633,4180.78,True,18.31664974619289,7788.239472081218,851,0.0,Denmark,Nordics
DENMARK,blower_filter,2024,0.214,0.214,10073.93,True,15.069450549450549,12816.567692307692,851,0.0,Denmark,Nordics
DENMARK,brake_pad,2024,0.3938,0.2821,14326.63,True,69.46246268656716,23631.129805970148,851,0.1116999999999999,Denmark,Nordics
DENMARK,brake_rotor,2024,0.5173,0.5173,7515.73,True,73.2349090909091,15569.741672727274,851,0.0,Denmark,Nordics
DENMARK,brake_shoe,2024,0.0752,0.0752,13881.6,True,35.2996875,15009.427124999998,851,0.0,Denmark,Nordics
DENMARK,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_disc,2024,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_kit,2024,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_pressure_plate,2024,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,fuel_filter,2024,0.1881,0.1293,7930.82,True,11.485625,9768.5240625,851,0.0587999999999999,Denmark,Nordics
DENMARK,oil_filter,2024,1.6943,1.6943,0.0,True,6.387855655794587,5432.871235253296,851,0.0,Denmark,Nordics
DENMARK,pilot_bearing,2024,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,release_bearing,2024,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,urea_filter,2024,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
FINLAND,air_filter,2024,0.407,0.3953,7439.76,True,20.839673469387755,12545.483428571428,1204,0.0116999999999999,Finland,Nordics
FINLAND,blower_filter,2024,0.3422,0.3372,14550.89,True,18.372330097087374,22120.2854368932,1204,0.005,Finland,Nordics
FINLAND,brake_pad,2024,0.1267,0.0664,30569.9,True,72.6816393442623,35003.477508196724,1204,0.0603,Finland,Nordics
FINLAND,brake_rotor,2024,0.2027,0.2027,16883.57,True,70.34819672131147,21174.807213114756,1204,0.0,Finland,Nordics
FINLAND,brake_shoe,2024,0.0415,0.0415,22409.53,True,38.838,23380.476,1204,0.0,Finland,Nordics
FINLAND,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,clutch_disc,2024,0.0249,0.0249,34276.1,True,145.98,35151.984,1204,0.0,Finland,Nordics
FINLAND,clutch_kit,2024,0.0443,0.0332,13888.04,True,80.46375,14531.75325,1204,0.0110999999999999,Finland,Nordics
FINLAND,clutch_pressure_plate,2024,0.0208,0.0208,16447.05,True,69.75,16795.8,1204,0.0,Finland,Nordics
FINLAND,fuel_filter,2024,0.1952,0.1894,12970.83,True,13.385787234042551,16116.487829787236,1204,0.0058,Finland,Nordics
FINLAND,oil_filter,2024,0.7118,0.7118,1888.57,True,5.442567094515752,6552.850781796966,1204,0.0,Finland,Nordics
FINLAND,pilot_bearing,2024,0.1661,0.1661,304.21,True,3.03,364.81200000000007,1204,0.0,Finland,Nordics
FINLAND,release_bearing,2024,0.0277,0.0277,4523.46,True,25.76,4652.256,1204,0.0,Finland,Nordics
FINLAND,urea_filter,2024,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
GERMANY,air_filter,2024,0.343,0.3406,85815.77,True,19.35726015557476,130609.2414477096,13780,0.0024,Germany,DACH
GERMANY,blower_filter,2024,0.3157,0.2527,127719.13,True,13.83061971830986,186637.2977887324,13780,0.063,Germany,DACH
GERMANY,brake_pad,2024,0.2769,0.1979,260080.76,True,66.08649635036497,359675.7563868613,13780,0.0789999999999999,Germany,DACH
GERMANY,brake_rotor,2024,0.7929,0.7929,45915.88,True,65.7227476635514,221722.261517757,13780,0.0,Germany,DACH
GERMANY,brake_shoe,2024,0.0381,0.0314,249415.39,True,38.42918287937743,259293.2256420233,13780,0.0067,Germany,DACH
GERMANY,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,13780,0.0,Germany,DACH
GERMANY,clutch_disc,2024,0.0445,0.0374,301916.8,True,117.07175,315964.94607500004,13780,0.0070999999999999,Germany,DACH
GERMANY,clutch_kit,2024,0.0795,0.0529,101196.02,True,54.31366459627329,109941.7198757764,13780,0.0266,Germany,DACH
GERMANY,clutch_pressure_plate,2024,0.0508,0.0445,185994.98,True,72.60029197080291,195940.928,13780,0.0063,Germany,DACH
GERMANY,fuel_filter,2024,0.3664,0.1378,80369.99,True,9.399427588996764,126840.57559971685,13780,0.2286,Germany,DACH
GERMANY,oil_filter,2024,0.5544,0.4978,29877.28,True,4.969178027265437,67056.57288893344,13780,0.0565999999999999,Germany,DACH
GERMANY,pilot_bearing,2024,0.0333,0.0333,3952.49,True,3.03,4088.985,13780,0.0,Germany,DACH
GERMANY,release_bearing,2024,0.0336,0.0336,51570.03,True,26.36264705882353,53363.27017647059,13780,0.0,Germany,DACH
GERMANY,urea_filter,2024,0.0046,0.0046,113307.25,True,8.665081967213116,113835.78132786886,13780,0.0,Germany,DACH
GREECE,air_filter,2024,0.5028,0.4249,15027.41,True,16.232692307692307,30222.026538461538,3742,0.0779,Greece,Med
GREECE,blower_filter,2024,0.1397,0.0967,52439.75,True,16.36951923076923,60951.90485576924,3742,0.043,Greece,Med
GREECE,brake_pad,2024,0.2508,0.1757,80624.37,True,72.16323529411764,107609.81647058822,3742,0.0751,Greece,Med
GREECE,brake_rotor,2024,0.2793,0.2793,49372.68,True,73.59446153846154,68509.08424615386,3742,0.0,Greece,Med
GREECE,brake_shoe,2024,0.0671,0.0671,72416.22,True,41.6964,77630.35752,3742,0.0,Greece,Med
GREECE,clutch_booster,2024,0.0027,0.0027,36971.61,True,99.56,37076.144,3742,0.0,Greece,Med
GREECE,clutch_disc,2024,0.0671,0.0282,64343.95,True,92.6212,68975.00764000001,3742,0.0389,Greece,Med
GREECE,clutch_kit,2024,0.2542,0.0627,18723.68,True,44.95211267605634,25105.754929577462,3742,0.1914999999999999,Greece,Med
GREECE,clutch_pressure_plate,2024,0.0752,0.0389,47216.41,True,68.55875,51055.70112500001,3742,0.0363,Greece,Med
GREECE,fuel_filter,2024,0.4515,0.1512,18366.23,True,8.992034503271862,33481.840472932774,3742,0.3003,Greece,Med
GREECE,oil_filter,2024,0.7018,0.4225,5816.41,True,5.237646383467279,19502.37630884041,3742,0.2793,Greece,Med
GREECE,pilot_bearing,2024,0.0,0.0,0.0,False,0.0,0.0,3742,0.0,Greece,Med
GREECE,release_bearing,2024,0.0358,0.0304,14311.84,True,26.576,14842.696,3742,0.0053999999999999,Greece,Med
GREECE,urea_filter,2024,0.0005,0.0005,39809.96,True,10.74,39831.438,3742,0.0,Greece,Med
HUNGARY,air_filter,2024,0.3996,0.3899,23062.23,True,20.572908847184987,38409.62081769437,3734,0.0096999999999999,Hungary,CEE
HUNGARY,blower_filter,2024,0.233,0.161,46593.72,True,16.268758620689656,60747.54468965517,3734,0.072,Hungary,CEE
HUNGARY,brake_pad,2024,0.1111,0.1065,109975.82,True,82.83807228915663,123726.94477108434,3734,0.0046,Hungary,CEE
HUNGARY,brake_rotor,2024,0.2539,0.2539,53159.32,True,76.32350210970463,71247.98921940928,3734,0.0,Hungary,CEE
HUNGARY,brake_shoe,2024,0.0086,0.0086,45804.15,True,24.745625,46200.081875,3734,0.0,Hungary,CEE
HUNGARY,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,clutch_disc,2024,0.0094,0.0094,109959.64,True,148.6342857142857,111000.08457142855,3734,0.0,Hungary,CEE
HUNGARY,clutch_kit,2024,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,clutch_pressure_plate,2024,0.0121,0.0121,55713.74,True,75.51333333333334,56393.35733333333,3734,0.0,Hungary,CEE
HUNGARY,fuel_filter,2024,0.1267,0.0,22892.77,True,7.020169133192389,26213.31154334038,3734,0.1267,Hungary,CEE
HUNGARY,oil_filter,2024,0.463,0.4135,9942.21,True,4.95871023713129,18515.82402544824,3734,0.0495,Hungary,CEE
HUNGARY,pilot_bearing,2024,0.0054,0.0054,1125.34,True,3.03,1131.4019999999998,3734,0.0,Hungary,CEE
HUNGARY,release_bearing,2024,0.0143,0.0,8822.56,True,15.98,8950.398000000001,3734,0.0143,Hungary,CEE
HUNGARY,urea_filter,2024,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
ICELAND,air_filter,2024,0.3251,0.3251,2877.81,True,21.005909090909093,4264.199545454546,406,0.0,Iceland,Nordics
ICELAND,blower_filter,2024,0.1429,0.1429,5710.68,True,16.41,6662.46,406,0.0,Iceland,Nordics
ICELAND,brake_pad,2024,0.1047,0.1047,11147.05,True,76.66470588235293,12450.348235294116,406,0.0,Iceland,Nordics
ICELAND,brake_rotor,2024,0.5123,0.5123,2072.91,True,41.87692307692308,4250.507692307692,406,0.0,Iceland,Nordics
ICELAND,brake_shoe,2024,0.0148,0.0148,670.0,True,3.35,680.0500000000001,406,0.0,Iceland,Nordics
ICELAND,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,clutch_disc,2024,0.0246,0.0246,12065.33,True,152.34,12370.008,406,0.0,Iceland,Nordics
ICELAND,clutch_kit,2024,0.0985,0.0985,2782.79,True,50.68833333333333,3086.9195,406,0.0,Iceland,Nordics
ICELAND,clutch_pressure_plate,2024,0.0246,0.0246,7623.0,True,96.25,7815.5,406,0.0,Iceland,Nordics
ICELAND,fuel_filter,2024,0.069,0.069,4665.33,True,12.342142857142855,5010.91,406,0.0,Iceland,Nordics
ICELAND,oil_filter,2024,0.4507,0.4507,1458.53,True,6.540491803278689,2655.439672131148,406,0.0,Iceland,Nordics
ICELAND,pilot_bearing,2024,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,release_bearing,2024,0.0164,0.0164,1527.45,True,25.5,1552.95,406,0.0,Iceland,Nordics
ICELAND,urea_filter,2024,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
IRELAND,air_filter,2024,1.8235,1.4209,0.0,True,24.006109813084112,22539.336503504677,2161,0.4025999999999998,Ireland,UK/IE
IRELAND,blower_filter,2024,0.0756,0.0756,31532.83,True,18.167183098591547,34112.51970422535,2161,0.0,Ireland,UK/IE
IRELAND,brake_pad,2024,0.8409,0.7167,9822.69,True,76.70895125553915,61758.37665583457,2161,0.1241999999999999,Ireland,UK/IE
IRELAND,brake_rotor,2024,2.8439,2.8439,0.0,True,49.3772734082397,23177.692137827715,2161,0.0,Ireland,UK/IE
IRELAND,brake_shoe,2024,0.311,0.2812,23471.58,True,36.2858904109589,34068.82250684931,2161,0.0297999999999999,Ireland,UK/IE
IRELAND,clutch_booster,2024,0.0107,0.0107,38578.91,True,207.67,39000.426,2161,0.0,Ireland,UK/IE
IRELAND,clutch_disc,2024,0.6417,0.2636,10501.71,True,78.05609958506224,29310.06539419087,2161,0.3781,Ireland,UK/IE
IRELAND,clutch_kit,2024,1.4734,0.8202,0.0,True,51.4382891566265,14490.166055421683,2161,0.6532,Ireland,UK/IE
IRELAND,clutch_pressure_plate,2024,0.7456,0.3382,6421.19,True,67.2090357142857,25236.99291071428,2161,0.4074,Ireland,UK/IE
IRELAND,fuel_filter,2024,1.7862,0.9757,0.0,True,13.472853309481216,25297.97665921288,2161,0.8105,Ireland,UK/IE
IRELAND,oil_filter,2024,1.3948,0.9789,0.0,True,8.223959526536845,15442.128802978234,2161,0.4159,Ireland,UK/IE
IRELAND,pilot_bearing,2024,0.032,0.032,550.76,True,3.03,569.034,2161,0.0,Ireland,UK/IE
IRELAND,release_bearing,2024,0.1065,0.0817,6354.63,True,25.25133333333333,7113.3006,2161,0.0248,Ireland,UK/IE
IRELAND,urea_filter,2024,0.0714,0.0714,37333.55,True,27.59980769230769,40204.63986538462,2161,0.0,Ireland,UK/IE
ITUK,air_filter,2024,0.5451,0.4559,111899.99,True,28.46032689450223,245976.91328380385,23068,0.0892,United Kingdom,UK/IE
ITUK,blower_filter,2024,0.0,0.0,0.0,False,0.0,0.0,23068,0.0,United Kingdom,UK/IE
ITUK,brake_pad,2024,0.6607,0.6607,178711.21,True,76.16948992994746,526651.0872736428,23068,0.0,United Kingdom,UK/IE
ITUK,brake_rotor,2024,1.4796,1.4796,0.0,True,44.54988270253363,192517.8631107288,23068,0.0,United Kingdom,UK/IE
ITUK,brake_shoe,2024,0.1101,0.1101,278215.95,True,45.2146123521682,312622.8727253614,23068,0.0,United Kingdom,UK/IE
ITUK,clutch_booster,2024,0.0012,0.0012,603665.01,True,349.635,604379.061,23068,0.0,United Kingdom,UK/IE
ITUK,clutch_disc,2024,0.0795,0.0642,279948.05,True,87.97545454545454,304139.9439090909,23068,0.0153,United Kingdom,UK/IE
ITUK,clutch_kit,2024,0.2758,0.1369,162264.7,True,86.41044755244755,224045.008413986,23068,0.1389,United Kingdom,UK/IE
ITUK,clutch_pressure_plate,2024,0.0474,0.0292,237996.07,True,72.27079268292682,249847.3573841463,23068,0.0181999999999999,United Kingdom,UK/IE
ITUK,fuel_filter,2024,1.1161,0.9367,0.0,True,10.593755442670538,183119.41907982584,23068,0.1794000000000001,United Kingdom,UK/IE
ITUK,oil_filter,2024,0.5641,0.4199,48214.94,True,6.398307692307692,110598.58744615383,23068,0.1442,United Kingdom,UK/IE
ITUK,pilot_bearing,2024,0.015,0.015,5022.55,True,2.95,5099.37,23068,0.0,United Kingdom,UK/IE
ITUK,release_bearing,2024,0.0436,0.0282,53919.55,True,21.74318584070797,56375.732247787615,23068,0.0154,United Kingdom,UK/IE
ITUK,urea_filter,2024,0.2798,0.2798,52040.49,True,20.301044176706828,72259.53664257028,23068,0.0,United Kingdom,UK/IE
IUK,air_filter,2024,0.1924,0.1924,342568.54,True,17.75472482053513,424187.0080498151,47783,0.0,United Kingdom,UK/IE
IUK,blower_filter,2024,0.2745,0.2658,508706.97,True,14.673675181090356,701152.2211780404,47783,0.0087,United Kingdom,UK/IE
IUK,brake_pad,2024,0.3111,0.1797,831246.49,True,63.13008745375042,1206617.9875210226,47783,0.1314,United Kingdom,UK/IE
IUK,brake_rotor,2024,0.5651,0.5651,328532.42,True,63.24316249444527,755490.1705261443,47783,0.0,United Kingdom,UK/IE
IUK,brake_shoe,2024,0.0734,0.0734,764492.56,True,34.53382554161916,825064.8929275941,47783,0.0,United Kingdom,UK/IE
IUK,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,47783,0.0,United Kingdom,UK/IE
IUK,clutch_disc,2024,0.0408,0.0408,1327916.69,True,144.8646923076923,1384413.9185076924,47783,0.0,United Kingdom,UK/IE
IUK,clutch_kit,2024,0.0045,0.0045,401221.89,True,56.229375,403018.422375,47783,0.0,United Kingdom,UK/IE
IUK,clutch_pressure_plate,2024,0.0552,0.0552,565857.93,True,62.673939393939385,598949.7692121211,47783,0.0,United Kingdom,UK/IE
IUK,fuel_filter,2024,0.1171,0.1171,550086.04,True,13.03861279942796,623024.0353950661,47783,0.0,United Kingdom,UK/IE
IUK,oil_filter,2024,0.5085,0.4682,113409.96,True,4.829243590271204,230755.7464739289,47783,0.0402999999999999,United Kingdom,UK/IE
IUK,pilot_bearing,2024,0.0266,0.0266,13735.98,True,2.953149606299213,14111.03476377953,47783,0.0,United Kingdom,UK/IE
IUK,release_bearing,2024,0.0606,0.0544,162636.71,True,24.153548387096773,173118.1427096774,47783,0.0062,United Kingdom,UK/IE
IUK,urea_filter,2024,0.0,0.0,0.0,False,0.0,0.0,47783,0.0,United Kingdom,UK/IE
MALTA,air_filter,2024,0.3612,0.3612,7266.96,True,23.619597701149427,11377.56021264368,1040,0.0,Malta,Med
MALTA,blower_filter,2024,0.1391,0.1391,15426.47,True,18.6010447761194,17918.386432835818,1040,0.0,Malta,Med
MALTA,brake_pad,2024,0.4105,0.3657,18250.35,True,77.01648484848485,30960.626909090908,1040,0.0447999999999999,Malta,Med
MALTA,brake_rotor,2024,0.2616,0.2616,11754.96,True,66.10095238095238,15917.109333333334,1040,0.0,Malta,Med
MALTA,brake_shoe,2024,0.0394,0.0394,17051.7,True,36.85526315789474,17753.180263157898,1040,0.0,Malta,Med
MALTA,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
MALTA,clutch_disc,2024,0.0104,0.0104,16240.99,True,85.18,16414.186,1040,0.0,Malta,Med
MALTA,clutch_kit,2024,0.1176,0.1176,5071.88,True,39.77941176470589,5748.125,1040,0.0,Malta,Med
MALTA,clutch_pressure_plate,2024,0.0052,0.0052,23339.25,True,121.77,23465.079,1040,0.0,Malta,Med
MALTA,fuel_filter,2024,0.3156,0.3156,8494.8,True,12.88391447368421,12411.0748125,1040,0.0,Malta,Med
MALTA,oil_filter,2024,0.6384,0.6384,2171.51,True,6.233983739837399,6005.196536585366,1040,0.0,Malta,Med
MALTA,pilot_bearing,2024,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
MALTA,release_bearing,2024,0.0069,0.0069,5887.81,True,41.03,5928.835,1040,0.0,Malta,Med
MALTA,urea_filter,2024,0.0145,0.0145,12569.26,True,15.360833333333334,12754.099916666666,1040,0.0,Malta,Med
NORWAY,air_filter,2024,0.3715,0.3713,45278.61,True,18.17323150033944,72047.7762830957,7929,0.0001999999999999,Norway,Nordics
NORWAY,blower_filter,2024,0.1892,0.1892,87357.25,True,13.588,107739.252,7929,0.0,Norway,Nordics
NORWAY,brake_pad,2024,0.2084,0.2018,166678.51,True,66.38990922844177,210562.2361089259,7929,0.0065999999999999,Norway,Nordics
NORWAY,brake_rotor,2024,0.5045,0.5045,62221.88,True,63.34628,125564.996216,7929,0.0,Norway,Nordics
NORWAY,brake_shoe,2024,0.059,0.059,128041.6,True,34.322905982905986,136073.16076923077,7929,0.0,Norway,Nordics
NORWAY,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,clutch_disc,2024,0.0038,0.0038,221709.13,True,140.34,222551.172,7929,0.0,Norway,Nordics
NORWAY,clutch_kit,2024,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,clutch_pressure_plate,2024,0.0038,0.0038,105925.59,True,67.05,106327.89,7929,0.0,Norway,Nordics
NORWAY,fuel_filter,2024,0.2424,0.0003,40731.27,True,6.780634755463059,53763.652976066594,7929,0.2421,Norway,Nordics
NORWAY,oil_filter,2024,0.385,0.3636,24600.39,True,5.045198165738618,40003.3762561415,7929,0.0214,Norway,Nordics
NORWAY,pilot_bearing,2024,0.0013,0.0013,2304.43,True,2.91,2307.339,7929,0.0,Norway,Nordics
NORWAY,release_bearing,2024,0.0025,0.0025,29374.03,True,24.76,29447.068,7929,0.0,Norway,Nordics
NORWAY,urea_filter,2024,0.0001,0.0001,84750.32,True,10.69,84761.01,7929,0.0,Norway,Nordics
PORTUGAL,air_filter,2024,0.4787,0.3279,38928.92,True,22.042361282367448,74681.72426078915,7208,0.1508,Portugal,Iberia
PORTUGAL,blower_filter,2024,0.1771,0.0,79489.63,True,14.255183333333337,96595.97330333336,7208,0.1771,Portugal,Iberia
PORTUGAL,brake_pad,2024,0.1997,0.1774,175824.43,True,75.37068728522337,219690.4792989691,7208,0.0222999999999999,Portugal,Iberia
PORTUGAL,brake_rotor,2024,0.4173,0.4173,65901.35,True,66.76611032531825,113101.79089108911,7208,0.0,Portugal,Iberia
PORTUGAL,brake_shoe,2024,0.075,0.0484,165188.2,True,52.70681102362205,178575.94642913388,7208,0.0266,Portugal,Iberia
PORTUGAL,clutch_booster,2024,0.0074,0.0074,197295.35,True,293.324,198756.3424,7208,0.0,Portugal,Iberia
PORTUGAL,clutch_disc,2024,0.1343,0.0531,100405.35,True,85.57967032967034,115977.56923076924,7208,0.0812,Portugal,Iberia
PORTUGAL,clutch_kit,2024,0.2883,0.063,43408.02,True,60.00317406143345,60987.22611604096,7208,0.2253,Portugal,Iberia
PORTUGAL,clutch_pressure_plate,2024,0.1217,0.048,93197.9,True,78.30187878787879,106114.70613333334,7208,0.0737,Portugal,Iberia
PORTUGAL,fuel_filter,2024,0.5949,0.0403,21801.73,True,7.941788638055073,53815.14816918878,7208,0.5546,Portugal,Iberia
PORTUGAL,oil_filter,2024,0.7067,0.0682,12973.54,True,6.528582167467112,44238.97848319064,7208,0.6385,Portugal,Iberia
PORTUGAL,pilot_bearing,2024,0.0074,0.0074,2038.04,True,3.03,2053.128,7208,0.0,Portugal,Iberia
PORTUGAL,release_bearing,2024,0.0443,0.0,15689.87,True,16.151333333333334,16416.2152,7208,0.0443,Portugal,Iberia
PORTUGAL,urea_filter,2024,0.0205,0.0205,52701.82,True,10.400943396226417,53804.08018867925,7208,0.0,Portugal,Iberia
ROMANIA,air_filter,2024,0.915,0.915,845.99,True,18.593081632653064,9956.595214285717,1071,0.0,Romania,CEE
ROMANIA,blower_filter,2024,0.5789,0.5789,6637.99,True,14.718387096774192,15763.39258064516,1071,0.0,Romania,CEE
ROMANIA,brake_pad,2024,0.3455,0.3315,22867.26,True,81.5522972972973,34937.004162162164,1071,0.0139999999999999,Romania,CEE
ROMANIA,brake_rotor,2024,0.4743,0.4743,9290.75,True,66.00889763779527,17677.182787401576,1071,0.0,Romania,CEE
ROMANIA,brake_shoe,2024,0.0635,0.0243,17457.51,True,34.81058823529412,18641.07,1071,0.0392,Romania,CEE
ROMANIA,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,1071,0.0,Romania,CEE
ROMANIA,clutch_disc,2024,0.0467,0.0467,26867.41,True,131.574,28183.1508,1071,0.0,Romania,CEE
ROMANIA,clutch_kit,2024,0.1556,0.0996,8707.32,True,64.1896,10315.268719999998,1071,0.0559999999999999,Romania,CEE
ROMANIA,clutch_pressure_plate,2024,0.0467,0.042,14995.43,True,73.435,15729.777,1071,0.0046999999999999,Romania,CEE
ROMANIA,fuel_filter,2024,0.3175,0.0093,5303.73,True,7.255441176470588,7770.577499999999,1071,0.3082,Romania,CEE
ROMANIA,oil_filter,2024,0.592,0.5826,2246.56,True,5.140867507886435,5505.869100946372,1071,0.0093999999999999,Romania,CEE
ROMANIA,pilot_bearing,2024,0.056,0.056,315.43,True,3.12,334.152,1071,0.0,Romania,CEE
ROMANIA,release_bearing,2024,0.0871,0.0871,3890.62,True,26.53,4263.371,1071,0.0,Romania,CEE
ROMANIA,urea_filter,2024,0.0028,0.0028,11484.56,True,10.753333333333332,11516.819999999998,1071,0.0,Romania,CEE
SWEDEN,air_filter,2024,0.3406,0.3406,50525.91,True,18.15193324061196,76628.38617524339,8443,0.0,Sweden,Nordics
SWEDEN,blower_filter,2024,0.3482,0.3482,90875.12,True,16.51374149659864,139425.5194557823,8443,0.0,Sweden,Nordics
SWEDEN,brake_pad,2024,0.2011,0.1617,199653.89,True,73.99521354933727,249896.6351988218,8443,0.0393999999999999,Sweden,Nordics
SWEDEN,brake_rotor,2024,0.3184,0.3184,100096.69,True,69.57197916666667,146852.533625,8443,0.0,Sweden,Nordics
SWEDEN,brake_shoe,2024,0.0182,0.0182,144902.48,True,34.9625974025974,147594.60493506494,8443,0.0,Sweden,Nordics
SWEDEN,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,clutch_disc,2024,0.0018,0.0018,246063.89,True,145.98,246501.828,8443,0.0,Sweden,Nordics
SWEDEN,clutch_kit,2024,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,clutch_pressure_plate,2024,0.0018,0.0018,117570.6,True,69.75,117779.85,8443,0.0,Sweden,Nordics
SWEDEN,fuel_filter,2024,0.1774,0.1774,93447.34,True,13.455340453938584,113603.43945260346,8443,0.0,Sweden,Nordics
SWEDEN,oil_filter,2024,0.3612,0.3612,27285.57,True,5.05944262295082,42716.87406557377,8443,0.0,Sweden,Nordics
SWEDEN,pilot_bearing,2024,0.0012,0.0012,2631.1,True,3.12,2634.216,8443,0.0,Sweden,Nordics
SWEDEN,release_bearing,2024,0.0016,0.0016,32572.23,True,25.76,32625.04,8443,0.0,Sweden,Nordics
SWEDEN,urea_filter,2024,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
UMI,air_filter,2024,0.0922,0.0671,92958.51,True,11.045450292397662,102402.36966081872,18542,0.0250999999999999,Israel,MENA
UMI,blower_filter,2024,0.0142,0.0,198073.98,True,10.836742424242424,200934.87803030305,18542,0.0142,Israel,MENA
UMI,brake_pad,2024,0.173,0.1069,301472.54,True,49.14939204988308,364531.2109555728,18542,0.0660999999999999,Israel,MENA
UMI,brake_rotor,2024,0.1609,0.1609,196699.16,True,50.571836461126,234425.74791554955,18542,0.0,Israel,MENA
UMI,brake_shoe,2024,0.1556,0.0694,223496.61,True,28.55092169092169,264695.59499653504,18542,0.0861999999999999,Israel,MENA
UMI,clutch_booster,2024,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UMI,clutch_disc,2024,0.0566,0.0558,377169.33,True,107.81195238095238,399809.8442095238,18542,0.0007999999999999,Israel,MENA
UMI,clutch_kit,2024,0.0536,0.0,67004.75,True,25.4548322147651,70797.52483892618,18542,0.0536,Israel,MENA
UMI,clutch_pressure_plate,2024,0.0504,0.0496,186253.25,True,52.89181818181818,196144.0185454545,18542,0.0008,Israel,MENA
UMI,fuel_filter,2024,0.2291,0.008,101123.99,True,7.074576271186441,131176.793220339,18542,0.2211,Israel,MENA
UMI,oil_filter,2024,0.9445,0.0,4243.38,True,4.123792611203106,76463.36259692798,18542,0.9445,Israel,MENA
UMI,pilot_bearing,2024,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UMI,release_bearing,2024,0.0467,0.0,38853.78,True,14.654615384615385,40758.88176923077,18542,0.0467,Israel,MENA
UMI,urea_filter,2024,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UTI,air_filter,2024,0.9901,0.0149,1259.52,True,19.6800469043152,127133.10300187618,10336,0.9752,Israel,MENA
UTI,blower_filter,2024,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,brake_pad,2024,0.1193,0.1193,424107.72,True,74.548728923476,481584.788845655,10336,0.0,Israel,MENA
UTI,brake_rotor,2024,0.078,0.078,276418.79,True,92.82027777777778,299809.4972222222,10336,0.0,Israel,MENA
UTI,brake_shoe,2024,0.2155,0.2155,108471.44,True,21.403204022988504,138264.69798850574,10336,0.0,Israel,MENA
UTI,clutch_booster,2024,0.031,0.0263,349421.93,True,279.091,360585.572,10336,0.0046999999999999,Israel,MENA
UTI,clutch_disc,2024,0.019,0.0097,166328.08,True,65.61265306122449,169543.0955102041,10336,0.0093,Israel,MENA
UTI,clutch_kit,2024,0.3566,0.0077,155637.02,True,124.80916063675832,241880.15331403763,10336,0.3489,Israel,MENA
UTI,clutch_pressure_plate,2024,0.0298,0.0205,261718.75,True,104.3951948051948,269757.1833766234,10336,0.0093,Israel,MENA
UTI,fuel_filter,2024,1.2316,0.6136,0.0,True,9.002129210658623,116307.5094017094,10336,0.618,Israel,MENA
UTI,oil_filter,2024,0.781,0.2701,25708.4,True,9.084239841427156,117368.37875123884,10336,0.5109,Israel,MENA
UTI,pilot_bearing,2024,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,release_bearing,2024,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,urea_filter,2024,0.036,0.036,24676.17,True,9.906129032258065,25597.43741935484,10336,0.0,Israel,MENA
BELGIUM,air_filter,2025,0.5166,0.3067,43266.03,True,18.67764943457189,89512.63491518579,9593,0.2098999999999999,Belgium,Benelux
BELGIUM,blower_filter,2025,0.2307,0.1899,122142.74,True,16.56415196743555,158765.740192673,9593,0.0407999999999999,Belgium,Benelux
BELGIUM,brake_pad,2025,0.2562,0.1581,202799.25,True,70.92221319796955,272660.448639594,9593,0.0980999999999999,Belgium,Benelux
BELGIUM,brake_rotor,2025,0.4645,0.4645,86223.15,True,67.19227313566937,161006.12488769094,9593,0.0,Belgium,Benelux
BELGIUM,brake_shoe,2025,0.0672,0.0626,346326.0,True,77.46987577639752,371274.37965838506,9593,0.0045999999999999,Belgium,Benelux
BELGIUM,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,9593,0.0,Belgium,Benelux
BELGIUM,clutch_disc,2025,0.0876,0.036,160669.59,True,91.8645238095238,176104.29214285713,9593,0.0516,Belgium,Benelux
BELGIUM,clutch_kit,2025,0.0988,0.0396,64440.34,True,49.73253521126761,71500.46587323945,9593,0.0591999999999999,Belgium,Benelux
BELGIUM,clutch_pressure_plate,2025,0.0772,0.0323,151903.14,True,85.87027027027027,164613.30810810812,9593,0.0449,Belgium,Benelux
BELGIUM,fuel_filter,2025,0.2603,0.0236,53171.16,True,7.499543086172345,71882.3705266533,9593,0.2366999999999999,Belgium,Benelux
BELGIUM,oil_filter,2025,0.6231,0.5328,19138.41,True,5.297211989283323,50773.24719608172,9593,0.0902999999999999,Belgium,Benelux
BELGIUM,pilot_bearing,2025,0.0146,0.0146,2880.7,True,3.0500000000000003,2923.425,9593,0.0,Belgium,Benelux
BELGIUM,release_bearing,2025,0.064,0.0577,18402.68,True,13.67478260869565,19660.234956521737,9593,0.0063,Belgium,Benelux
BELGIUM,urea_filter,2025,0.0073,0.0073,118765.08,True,12.591739130434783,119634.11347826089,9593,0.0,Belgium,Benelux
CYPRUS,air_filter,2025,1.4296,0.5498,0.0,True,15.435224541429475,17069.814820366857,2308,0.8798,Cyprus,Med
CYPRUS,blower_filter,2025,0.3504,0.2238,23653.54,True,16.46174193548387,36411.72698709678,2308,0.1266,Cyprus,Med
CYPRUS,brake_pad,2025,0.6198,0.1563,20678.09,True,60.73935135135135,54386.0152,2308,0.4635,Cyprus,Med
CYPRUS,brake_rotor,2025,0.5425,0.5425,18419.35,True,72.81243333333333,40265.27563333333,2308,0.0,Cyprus,Med
CYPRUS,brake_shoe,2025,0.1402,0.104,36618.36,True,38.507548387096776,42585.49776129033,2308,0.0361999999999999,Cyprus,Med
CYPRUS,clutch_booster,2025,0.0045,0.0045,23095.51,True,104.89,23201.668,2308,0.0,Cyprus,Med
CYPRUS,clutch_disc,2025,0.0746,0.052,36948.66,True,90.2560606060606,39929.281212121205,2308,0.0226,Cyprus,Med
CYPRUS,clutch_kit,2025,0.422,0.3074,7660.67,True,39.94471428571429,13253.6562,2308,0.1145999999999999,Cyprus,Med
CYPRUS,clutch_pressure_plate,2025,0.1153,0.0995,27445.58,True,70.12588235294118,31023.690352941176,2308,0.0157999999999999,Cyprus,Med
CYPRUS,fuel_filter,2025,0.7017,0.2405,6235.21,True,9.449007731958764,20900.26020231959,2308,0.4612,Cyprus,Med
CYPRUS,oil_filter,2025,0.9101,0.651,1111.05,True,5.586537506209638,12356.862309985096,2308,0.2591,Cyprus,Med
CYPRUS,pilot_bearing,2025,0.0362,0.0362,650.22,True,3.05,674.66,2308,0.0,Cyprus,Med
CYPRUS,release_bearing,2025,0.0874,0.0874,8292.88,True,27.388965517241378,9087.65875862069,2308,0.0,Cyprus,Med
CYPRUS,urea_filter,2025,0.024,0.024,21091.52,True,10.162745098039217,21610.061176470583,2308,0.0,Cyprus,Med
DENMARK,air_filter,2025,0.5456,0.5456,5034.9,True,26.053793103448275,11078.072827586206,851,0.0,Denmark,Nordics
DENMARK,blower_filter,2025,0.2281,0.2281,9351.33,True,14.244226804123713,12114.714896907217,851,0.0,Denmark,Nordics
DENMARK,brake_pad,2025,0.3586,0.2116,16450.74,True,75.37565573770492,25642.79808196721,851,0.1469999999999999,Denmark,Nordics
DENMARK,brake_rotor,2025,1.0676,1.0676,0.0,True,78.16118942731278,16617.068872246695,851,0.0,Denmark,Nordics
DENMARK,brake_shoe,2025,0.0705,0.0705,12328.11,True,31.19066666666667,13262.271466666669,851,0.0,Denmark,Nordics
DENMARK,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_disc,2025,0.0353,0.0353,27180.7,True,165.635,28174.5135,851,0.0,Denmark,Nordics
DENMARK,clutch_kit,2025,0.0235,0.0,261.61,True,2.1,267.96,851,0.0235,Denmark,Nordics
DENMARK,clutch_pressure_plate,2025,0.047,0.047,14026.31,True,86.52875,14718.540375,851,0.0,Denmark,Nordics
DENMARK,fuel_filter,2025,0.2504,0.2504,8829.79,True,13.850657276995303,11779.984014084506,851,0.0,Denmark,Nordics
DENMARK,oil_filter,2025,0.495,0.495,3395.96,True,7.906769596199525,6724.707541567696,851,0.0,Denmark,Nordics
DENMARK,pilot_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,release_bearing,2025,0.0314,0.0314,3519.42,True,28.48,3634.048,851,0.0,Denmark,Nordics
DENMARK,urea_filter,2025,0.26,0.26,6647.79,True,10.56714932126697,8983.13363800905,851,0.0,Denmark,Nordics
FINLAND,air_filter,2025,0.5914,0.5581,5149.32,True,20.932191011235957,12601.178988764044,1204,0.0332999999999999,Finland,Nordics
FINLAND,blower_filter,2025,0.4277,0.4219,12681.39,True,18.40549514563107,22160.216155339807,1204,0.0058,Finland,Nordics
FINLAND,brake_pad,2025,0.1869,0.1246,28775.99,True,73.4831111111111,35389.46631111111,1204,0.0623,Finland,Nordics
FINLAND,brake_rotor,2025,0.4252,0.4252,13156.68,True,76.05015625,22891.09703125,1204,0.0,Finland,Nordics
FINLAND,brake_shoe,2025,0.0365,0.0365,20058.77,True,34.58409090909091,20819.622727272726,1204,0.0,Finland,Nordics
FINLAND,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,clutch_disc,2025,0.0125,0.0125,34714.04,True,145.98,35151.984,1204,0.0,Finland,Nordics
FINLAND,clutch_kit,2025,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,clutch_pressure_plate,2025,0.0166,0.0166,16516.8,True,69.75,16795.8,1204,0.0,Finland,Nordics
FINLAND,fuel_filter,2025,0.1819,0.1645,12665.57,True,12.858447488584474,15481.570776255709,1204,0.0174,Finland,Nordics
FINLAND,oil_filter,2025,0.7824,0.7716,1425.82,True,5.442070063694268,6552.252356687898,1204,0.0108,Finland,Nordics
FINLAND,pilot_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,release_bearing,2025,0.0221,0.0221,4572.17,True,25.89,4675.734,1204,0.0,Finland,Nordics
FINLAND,urea_filter,2025,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
GERMANY,air_filter,2025,0.2795,0.2253,91602.14,True,18.843292682926823,127141.34871951216,13780,0.0542,Germany,DACH
GERMANY,blower_filter,2025,0.1229,0.1229,179153.89,True,15.136968053044004,204265.8153918023,13780,0.0,Germany,DACH
GERMANY,brake_pad,2025,0.386,0.2275,214959.83,True,64.33110899571632,350122.0607091861,13780,0.1585,Germany,DACH
GERMANY,brake_rotor,2025,0.5312,0.5312,108512.76,True,68.60818080357143,231456.55875892856,13780,0.0,Germany,DACH
GERMANY,brake_shoe,2025,0.0353,0.0331,242486.89,True,37.25260504201681,251354.50200000004,13780,0.0022,Germany,DACH
GERMANY,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,13780,0.0,Germany,DACH
GERMANY,clutch_disc,2025,0.0315,0.0315,321799.57,True,123.11070588235296,332263.48410588235,13780,0.0,Germany,DACH
GERMANY,clutch_kit,2025,0.0287,0.0262,103604.7,True,52.69344827586207,106662.078,13780,0.0024999999999999,Germany,DACH
GERMANY,clutch_pressure_plate,2025,0.0367,0.0348,168979.32,True,64.99444444444444,175413.5061111111,13780,0.0019,Germany,DACH
GERMANY,fuel_filter,2025,0.1634,0.1621,153339.53,True,13.582467120181406,183288.602553288,13780,0.0012999999999999,Germany,DACH
GERMANY,oil_filter,2025,0.1504,0.1463,60724.65,True,5.296283883686545,71470.70286840809,13780,0.0040999999999999,Germany,DACH
GERMANY,pilot_bearing,2025,0.0259,0.0259,4009.08,True,3.05,4115.974999999999,13780,0.0,Germany,DACH
GERMANY,release_bearing,2025,0.0346,0.0296,47849.44,True,24.485714285714284,49563.98285714285,13780,0.0049999999999999,Germany,DACH
GERMANY,urea_filter,2025,0.0002,0.0002,169445.42,True,12.9,169471.16999999998,13780,0.0,Germany,DACH
GREECE,air_filter,2025,0.9206,0.5554,2326.58,True,15.746767794632438,29317.332280046678,3742,0.3651999999999999,Greece,Med
GREECE,blower_filter,2025,0.2369,0.1743,47063.07,True,16.562755102040818,61671.41862244898,3742,0.0625999999999999,Greece,Med
GREECE,brake_pad,2025,0.3105,0.1998,68720.28,True,66.83226781857451,99660.2777710583,3742,0.1106999999999999,Greece,Med
GREECE,brake_rotor,2025,0.3642,0.3642,42381.43,True,71.60536873156343,66657.4377522124,3742,0.0,Greece,Med
GREECE,brake_shoe,2025,0.087,0.0795,68478.63,True,40.28746913580247,75007.21003703703,3742,0.0074999999999999,Greece,Med
GREECE,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,3742,0.0,Greece,Med
GREECE,clutch_disc,2025,0.0497,0.0349,73661.24,True,104.0854054054054,77512.4014054054,3742,0.0148,Greece,Med
GREECE,clutch_kit,2025,0.145,0.0734,22805.36,True,47.757407407407406,26672.512037037035,3742,0.0715999999999999,Greece,Med
GREECE,clutch_pressure_plate,2025,0.0483,0.0363,62078.38,True,87.59472222222222,65231.78963888889,3742,0.012,Greece,Med
GREECE,fuel_filter,2025,0.665,0.199,10857.24,True,8.703194668820679,32406.3453493538,3742,0.466,Greece,Med
GREECE,oil_filter,2025,0.9717,0.5954,541.09,True,5.1288308457711445,19097.20165422885,3742,0.3762999999999999,Greece,Med
GREECE,pilot_bearing,2025,0.0134,0.0134,1162.3,True,3.164,1178.2736,3742,0.0,Greece,Med
GREECE,release_bearing,2025,0.0197,0.0143,14092.8,True,25.73909090909091,14375.282272727272,3742,0.0053999999999999,Greece,Med
GREECE,urea_filter,2025,0.0,0.0,0.0,False,0.0,0.0,3742,0.0,Greece,Med
HUNGARY,air_filter,2025,0.4585,0.3755,19690.69,True,19.47644859813084,36362.52953271028,3734,0.083,Hungary,CEE
HUNGARY,blower_filter,2025,0.2228,0.1864,47997.02,True,16.539290865384615,61757.71209134616,3734,0.0363999999999999,Hungary,CEE
HUNGARY,brake_pad,2025,0.156,0.1091,97350.62,True,77.22562231759656,115344.1894935622,3734,0.0469,Hungary,CEE
HUNGARY,brake_rotor,2025,0.361,0.361,45676.66,True,76.57445103857567,71482.2500445104,3734,0.0,Hungary,CEE
HUNGARY,brake_shoe,2025,0.0048,0.0043,71225.4,True,38.33444444444444,71570.40777777777,3734,0.0004999999999999,Hungary,CEE
HUNGARY,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,clutch_disc,2025,0.0094,0.0094,110422.55,True,149.26,111467.368,3734,0.0,Hungary,CEE
HUNGARY,clutch_kit,2025,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,clutch_pressure_plate,2025,0.0121,0.0121,55713.74,True,75.51333333333334,56393.35733333333,3734,0.0,Hungary,CEE
HUNGARY,fuel_filter,2025,0.1883,0.0,21247.31,True,7.01,26175.34,3734,0.1883,Hungary,CEE
HUNGARY,oil_filter,2025,0.4502,0.4063,10088.64,True,4.914098750743605,18349.24473527662,3734,0.0438999999999999,Hungary,CEE
HUNGARY,pilot_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,release_bearing,2025,0.0143,0.0,8855.68,True,16.04,8984.003999999999,3734,0.0143,Hungary,CEE
HUNGARY,urea_filter,2025,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
ICELAND,air_filter,2025,0.7094,0.7094,1218.42,True,20.651111111111117,4192.1755555555565,406,0.0,Iceland,Nordics
ICELAND,blower_filter,2025,0.33,0.33,4595.7,True,16.89597014925373,6859.763880597015,406,0.0,Iceland,Nordics
ICELAND,brake_pad,2025,0.2217,0.1909,9796.04,True,77.50027777777778,12586.045111111112,406,0.0308,Iceland,Nordics
ICELAND,brake_rotor,2025,0.7291,0.7291,1583.05,True,57.56540540540541,5842.888648648649,406,0.0,Iceland,Nordics
ICELAND,brake_shoe,2025,0.1281,0.1281,3561.92,True,20.12384615384616,4085.14076923077,406,0.0,Iceland,Nordics
ICELAND,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,clutch_disc,2025,0.0246,0.0246,12232.04,True,154.445,12540.934,406,0.0,Iceland,Nordics
ICELAND,clutch_kit,2025,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,clutch_pressure_plate,2025,0.0246,0.0246,7544.59,True,95.26,7735.112000000001,406,0.0,Iceland,Nordics
ICELAND,fuel_filter,2025,0.2365,0.2365,3989.12,True,12.868125,5224.45875,406,0.0,Iceland,Nordics
ICELAND,oil_filter,2025,0.7069,0.7069,638.81,True,5.36815331010453,2179.470243902439,406,0.0,Iceland,Nordics
ICELAND,pilot_bearing,2025,0.0246,0.0246,119.59,True,3.02,122.612,406,0.0,Iceland,Nordics
ICELAND,release_bearing,2025,0.0328,0.0328,1539.35,True,26.135,1591.6215,406,0.0,Iceland,Nordics
ICELAND,urea_filter,2025,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
IRELAND,air_filter,2025,1.9471,1.6904,0.0,True,22.35845185995624,20992.35045131291,2161,0.2567000000000001,Ireland,UK/IE
IRELAND,blower_filter,2025,0.1092,0.1092,25429.73,True,15.202780487804878,28546.26092195122,2161,0.0,Ireland,UK/IE
IRELAND,brake_pad,2025,0.8124,0.6198,10985.7,True,72.72819571865443,58553.47037308868,2161,0.1926,Ireland,UK/IE
IRELAND,brake_rotor,2025,2.1239,2.1239,0.0,True,53.12637913741224,24937.5223671013,2161,0.0,Ireland,UK/IE
IRELAND,brake_shoe,2025,0.2833,0.2279,22520.74,True,33.4706015037594,31425.547751879694,2161,0.0554,Ireland,UK/IE
IRELAND,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,2161,0.0,Ireland,UK/IE
IRELAND,clutch_disc,2025,0.5113,0.2237,14736.33,True,80.28921875,30148.601640625,2161,0.2875999999999999,Ireland,UK/IE
IRELAND,clutch_kit,2025,1.0651,0.5503,0.0,True,47.05433333333333,13255.2057,2161,0.5147999999999999,Ireland,UK/IE
IRELAND,clutch_pressure_plate,2025,0.5485,0.3009,13792.1,True,81.34985436893204,30546.870315533983,2161,0.2476,Ireland,UK/IE
IRELAND,fuel_filter,2025,1.9961,1.1647,0.0,True,11.464581109925293,21527.043950106723,2161,0.8313999999999999,Ireland,UK/IE
IRELAND,oil_filter,2025,1.791,1.3996,0.0,True,7.825135295866786,14693.256545049064,2161,0.3913999999999999,Ireland,UK/IE
IRELAND,pilot_bearing,2025,0.0533,0.0533,542.2,True,3.05,572.79,2161,0.0,Ireland,UK/IE
IRELAND,release_bearing,2025,0.0959,0.0852,6573.51,True,25.813333333333336,7271.616000000001,2161,0.0107,Ireland,UK/IE
IRELAND,urea_filter,2025,0.0975,0.094,32833.99,True,24.975,36381.0825,2161,0.0035,Ireland,UK/IE
ITUK,air_filter,2025,0.638,0.5044,88609.81,True,28.320803409503085,244771.03970765325,23068,0.1336,United Kingdom,UK/IE
ITUK,blower_filter,2025,0.0,0.0,0.0,False,0.0,0.0,23068,0.0,United Kingdom,UK/IE
ITUK,brake_pad,2025,0.4923,0.4923,311991.42,True,88.88059635722679,614538.2193331375,23068,0.0,United Kingdom,UK/IE
ITUK,brake_rotor,2025,1.3357,1.3357,0.0,True,49.24215696465696,212795.0571070686,23068,0.0,United Kingdom,UK/IE
ITUK,brake_shoe,2025,0.0808,0.0808,325637.49,True,51.23928443649373,354278.660450805,23068,0.0,United Kingdom,UK/IE
ITUK,clutch_booster,2025,0.0012,0.0012,236538.41,True,137.0,236818.2,23068,0.0,United Kingdom,UK/IE
ITUK,clutch_disc,2025,0.0929,0.0778,285260.09,True,90.95968847352026,314456.73902180686,23068,0.0151,United Kingdom,UK/IE
ITUK,clutch_kit,2025,0.2164,0.0899,168870.39,True,83.11219251336898,215493.2927486631,23068,0.1265,United Kingdom,UK/IE
ITUK,clutch_pressure_plate,2025,0.0914,0.0697,253289.61,True,80.63683544303798,278769.6038101266,23068,0.0216999999999999,United Kingdom,UK/IE
ITUK,fuel_filter,2025,1.0609,0.8723,0.0,True,11.871822891106383,205211.5817665085,23068,0.1886,United Kingdom,UK/IE
ITUK,oil_filter,2025,0.7867,0.5919,26031.24,True,7.061086844620928,122055.1227613795,23068,0.1947999999999999,United Kingdom,UK/IE
ITUK,pilot_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,23068,0.0,United Kingdom,UK/IE
ITUK,release_bearing,2025,0.0417,0.0336,56825.68,True,22.86898148148148,59294.69518518519,23068,0.0081,United Kingdom,UK/IE
ITUK,urea_filter,2025,0.3706,0.3576,74029.21,True,33.04227445034117,117610.67167854436,23068,0.013,United Kingdom,UK/IE
IUK,air_filter,2025,0.2876,0.2288,288132.99,True,16.928585358754184,404449.2970986756,47783,0.0588,United Kingdom,UK/IE
IUK,blower_filter,2025,0.184,0.1674,470252.92,True,12.059931740614337,576259.7183617748,47783,0.0166,United Kingdom,UK/IE
IUK,brake_pad,2025,0.2407,0.1145,806882.05,True,55.59642608695652,1062625.6110852174,47783,0.1261999999999999,United Kingdom,UK/IE
IUK,brake_rotor,2025,0.4347,0.4347,469224.14,True,69.48637781629117,830070.3721178509,47783,0.0,United Kingdom,UK/IE
IUK,brake_shoe,2025,0.0558,0.0558,694104.74,True,30.769099774943736,735119.9472730682,47783,0.0,United Kingdom,UK/IE
IUK,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,47783,0.0,United Kingdom,UK/IE
IUK,clutch_disc,2025,0.0449,0.0449,1338472.75,True,146.64016317016316,1401381.3833519814,47783,0.0,United Kingdom,UK/IE
IUK,clutch_kit,2025,0.0021,0.0021,373081.33,True,52.16133333333333,373861.1405333333,47783,0.0,United Kingdom,UK/IE
IUK,clutch_pressure_plate,2025,0.0647,0.0647,565153.54,True,63.22618122977346,604227.3235404531,47783,0.0,United Kingdom,UK/IE
IUK,fuel_filter,2025,0.1599,0.158,485078.22,True,12.084057060594162,577412.4985263709,47783,0.0018999999999999,United Kingdom,UK/IE
IUK,oil_filter,2025,0.3774,0.3654,139982.79,True,4.705461905290008,224841.08622047244,47783,0.012,United Kingdom,UK/IE
IUK,pilot_bearing,2025,0.0391,0.0391,13564.96,True,2.9544919786096258,14117.449021390375,47783,0.0,United Kingdom,UK/IE
IUK,release_bearing,2025,0.0619,0.0544,158245.03,True,23.536283783783784,168693.9603918919,47783,0.0075,United Kingdom,UK/IE
IUK,urea_filter,2025,0.0,0.0,0.0,False,0.0,0.0,47783,0.0,United Kingdom,UK/IE
MALTA,air_filter,2025,0.6291,0.6291,3863.62,True,21.62475247524753,10416.643267326734,1040,0.0,Malta,Med
MALTA,blower_filter,2025,0.2367,0.2367,14239.8,True,19.365087719298245,18654.389,1040,0.0,Malta,Med
MALTA,brake_pad,2025,0.2612,0.2587,23166.15,True,78.0092380952381,31359.71371428572,1040,0.0025,Malta,Med
MALTA,brake_rotor,2025,0.3239,0.3239,12012.87,True,73.77397435897436,17764.773025641025,1040,0.0,Malta,Med
MALTA,brake_shoe,2025,0.0872,0.0872,13943.72,True,31.714285714285715,15276.771428571428,1040,0.0,Malta,Med
MALTA,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
MALTA,clutch_disc,2025,0.0156,0.0156,25531.67,True,134.61333333333332,25939.989333333328,1040,0.0,Malta,Med
MALTA,clutch_kit,2025,0.0761,0.0692,6670.15,True,49.96363636363637,7219.745454545455,1040,0.0069,Malta,Med
MALTA,clutch_pressure_plate,2025,0.0727,0.0727,7401.01,True,41.42357142857143,7982.322214285714,1040,0.0,Malta,Med
MALTA,fuel_filter,2025,0.3747,0.3747,7858.27,True,13.046371191135734,12567.569368421053,1040,0.0,Malta,Med
MALTA,oil_filter,2025,0.8626,0.8564,833.39,True,6.297665463297232,6066.541140794223,1040,0.0061999999999999,Malta,Med
MALTA,pilot_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
MALTA,release_bearing,2025,0.0277,0.0277,3637.55,True,25.89,3741.105,1040,0.0,Malta,Med
MALTA,urea_filter,2025,0.0048,0.0048,8667.54,True,10.49,8709.847,1040,0.0,Malta,Med
NORWAY,air_filter,2025,0.558,0.558,33640.96,True,19.19598553345389,76102.48464737793,7929,0.0,Norway,Nordics
NORWAY,blower_filter,2025,0.309,0.309,96259.32,True,17.56877551020408,139302.82102040816,7929,0.0,Norway,Nordics
NORWAY,brake_pad,2025,0.4373,0.4288,132181.26,True,74.06772170151406,234913.186148522,7929,0.0085,Norway,Nordics
NORWAY,brake_rotor,2025,0.8183,0.8183,23107.64,True,64.14334155363748,127144.93162762024,7929,0.0,Norway,Nordics
NORWAY,brake_shoe,2025,0.0464,0.0464,140920.4,True,37.27559782608696,147779.10758152173,7929,0.0,Norway,Nordics
NORWAY,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,clutch_disc,2025,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,clutch_kit,2025,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,clutch_pressure_plate,2025,0.0013,0.0013,95859.5,True,60.525,95980.545,7929,0.0,Norway,Nordics
NORWAY,fuel_filter,2025,0.2907,0.0,38046.66,True,6.765054229934925,53640.11498915402,7929,0.2907,Norway,Nordics
NORWAY,oil_filter,2025,0.478,0.4566,20780.4,True,5.020633245382586,39808.60100263853,7929,0.0213999999999999,Norway,Nordics
NORWAY,pilot_bearing,2025,0.0025,0.0025,2317.34,True,2.93,2323.197,7929,0.0,Norway,Nordics
NORWAY,release_bearing,2025,0.0017,0.0017,29553.14,True,24.89,29601.677,7929,0.0,Norway,Nordics
NORWAY,urea_filter,2025,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
PORTUGAL,air_filter,2025,0.5637,0.2828,30431.28,True,20.588167539267012,69754.77043979058,7208,0.2809,Portugal,Iberia
PORTUGAL,blower_filter,2025,0.2149,0.0,56778.87,True,10.672335164835165,72317.87754395604,7208,0.2149,Portugal,Iberia
PORTUGAL,brake_pad,2025,0.5527,0.3297,72680.92,True,55.74563004345128,162487.3624506518,7208,0.2229999999999999,Portugal,Iberia
PORTUGAL,brake_rotor,2025,0.4569,0.4569,64276.81,True,69.86245478036176,118346.99839793282,7208,0.0,Portugal,Iberia
PORTUGAL,brake_shoe,2025,0.1048,0.1048,141219.15,True,46.55940845070423,157747.93177183098,7208,0.0,Portugal,Iberia
PORTUGAL,clutch_booster,2025,0.0089,0.0089,146642.45,True,218.34166666666667,147948.31333333335,7208,0.0,Portugal,Iberia
PORTUGAL,clutch_disc,2025,0.1572,0.0944,113011.4,True,98.93854460093895,134081.51564319248,7208,0.0628,Portugal,Iberia
PORTUGAL,clutch_kit,2025,0.304,0.0502,48278.81,True,68.24546925566342,69364.6949514563,7208,0.2537999999999999,Portugal,Iberia
PORTUGAL,clutch_pressure_plate,2025,0.1513,0.0908,101431.55,True,88.1830731707317,119505.7007609756,7208,0.0604999999999999,Portugal,Iberia
PORTUGAL,fuel_filter,2025,0.3982,0.1063,33843.85,True,8.29873980726464,56233.92068198665,7208,0.2919,Portugal,Iberia
PORTUGAL,oil_filter,2025,0.4626,0.1364,18081.97,True,4.965948963317384,33650.26336523126,7208,0.3262,Portugal,Iberia
PORTUGAL,pilot_bearing,2025,0.0177,0.0177,2030.14,True,3.0500000000000003,2066.6800000000003,7208,0.0,Portugal,Iberia
PORTUGAL,release_bearing,2025,0.0748,0.0,15138.43,True,16.097368421052632,16361.365263157895,7208,0.0748,Portugal,Iberia
PORTUGAL,urea_filter,2025,0.013,0.013,53575.9,True,10.49268656716418,54278.6676119403,7208,0.0,Portugal,Iberia
ROMANIA,air_filter,2025,1.3707,1.0159,0.0,True,19.28901907356948,10329.269713896458,1071,0.3548,Romania,CEE
ROMANIA,blower_filter,2025,0.5322,0.5322,8569.47,True,17.104736842105265,18319.17315789474,1071,0.0,Romania,CEE
ROMANIA,brake_pad,2025,0.2708,0.2661,25720.59,True,82.33224137931035,35271.13220689655,1071,0.0046999999999999,Romania,CEE
ROMANIA,brake_rotor,2025,0.2054,0.2054,17761.53,True,83.48545454545454,22357.40472727273,1071,0.0,Romania,CEE
ROMANIA,brake_shoe,2025,0.084,0.084,11213.27,True,22.86088888888889,12242.006,1071,0.0,Romania,CEE
ROMANIA,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,1071,0.0,Romania,CEE
ROMANIA,clutch_disc,2025,0.0794,0.0747,24220.34,True,122.82117647058824,26308.296,1071,0.0046999999999999,Romania,CEE
ROMANIA,clutch_kit,2025,0.0311,0.0062,3353.32,True,21.544,3462.1208,1071,0.0249,Romania,CEE
ROMANIA,clutch_pressure_plate,2025,0.0607,0.0467,14791.3,True,73.51538461538462,15746.995384615384,1071,0.0139999999999999,Romania,CEE
ROMANIA,fuel_filter,2025,0.3361,0.0187,5419.28,True,7.622055555555556,8163.221500000001,1071,0.3174,Romania,CEE
ROMANIA,oil_filter,2025,0.5733,0.5173,2325.73,True,5.089120521172638,5450.448078175895,1071,0.056,Romania,CEE
ROMANIA,pilot_bearing,2025,0.0093,0.0093,333.15,True,3.14,336.294,1071,0.0,Romania,CEE
ROMANIA,release_bearing,2025,0.0622,0.0622,3411.92,True,22.648,3639.5336,1071,0.0,Romania,CEE
ROMANIA,urea_filter,2025,0.0289,0.0289,11232.0,True,10.8,11566.8,1071,0.0,Romania,CEE
SWEDEN,air_filter,2025,0.4053,0.3792,44699.24,True,17.804915254237287,75163.4497457627,8443,0.0261,Sweden,Nordics
SWEDEN,blower_filter,2025,0.4375,0.4375,69914.38,True,14.721916621548456,124297.14203573365,8443,0.0,Sweden,Nordics
SWEDEN,brake_pad,2025,0.2496,0.1679,179111.42,True,70.67769869513643,238692.72403321476,8443,0.0817,Sweden,Nordics
SWEDEN,brake_rotor,2025,0.5012,0.5012,75313.33,True,71.53961247637051,151005.8140151229,8443,0.0,Sweden,Nordics
SWEDEN,brake_shoe,2025,0.0178,0.0178,155667.9,True,37.542,158483.553,8443,0.0,Sweden,Nordics
SWEDEN,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,clutch_disc,2025,0.0024,0.0024,245917.91,True,145.98,246501.828,8443,0.0,Sweden,Nordics
SWEDEN,clutch_kit,2025,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,clutch_pressure_plate,2025,0.0018,0.0018,117570.6,True,69.75,117779.85,8443,0.0,Sweden,Nordics
SWEDEN,fuel_filter,2025,0.2124,0.2124,89864.38,True,13.513441160066924,114093.98371444506,8443,0.0,Sweden,Nordics
SWEDEN,oil_filter,2025,0.4873,0.4873,21588.07,True,4.986849781234809,42103.97270296549,8443,0.0,Sweden,Nordics
SWEDEN,pilot_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,release_bearing,2025,0.0024,0.0024,32710.72,True,25.89,32789.685,8443,0.0,Sweden,Nordics
SWEDEN,urea_filter,2025,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
UMI,air_filter,2025,0.2295,0.0796,81694.91,True,11.437058270676692,106032.96722744362,18542,0.1499,Israel,MENA
UMI,blower_filter,2025,0.007,0.0,246607.5,True,13.393846153846154,248348.6953846154,18542,0.007,Israel,MENA
UMI,brake_pad,2025,0.0874,0.0419,332399.47,True,49.1075925925926,364221.1927407408,18542,0.0455,Israel,MENA
UMI,brake_rotor,2025,0.1197,0.1197,216996.14,True,53.178810810810816,246510.37751351355,18542,0.0,Israel,MENA
UMI,brake_shoe,2025,0.1378,0.0721,224772.67,True,28.12118935837245,260711.54654147103,18542,0.0657,Israel,MENA
UMI,clutch_booster,2025,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UMI,clutch_disc,2025,0.0388,0.0383,274156.57,True,76.91520833333334,285232.3585833334,18542,0.0005,Israel,MENA
UMI,clutch_kit,2025,0.0151,0.0004,71806.18,True,26.21333333333333,72907.14400000001,18542,0.0147,Israel,MENA
UMI,clutch_pressure_plate,2025,0.0467,0.0467,166247.38,True,47.02364161849711,174382.47257803468,18542,0.0,Israel,MENA
UMI,fuel_filter,2025,0.2644,0.0082,96456.67,True,7.071603427172582,131121.67074663402,18542,0.2562,Israel,MENA
UMI,oil_filter,2025,0.8516,0.3192,11140.82,True,4.049735925527199,75090.20353112533,18542,0.5324,Israel,MENA
UMI,pilot_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UMI,release_bearing,2025,0.0449,0.0,37835.27,True,14.2436,39615.72468000001,18542,0.0449,Israel,MENA
UMI,urea_filter,2025,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UTI,air_filter,2025,1.3146,0.0243,0.0,True,19.020163683466794,122870.2573951955,10336,1.2903,Israel,MENA
UTI,blower_filter,2025,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,brake_pad,2025,0.0704,0.0704,456181.37,True,75.96692307692307,490746.323076923,10336,0.0,Israel,MENA
UTI,brake_rotor,2025,0.0929,0.0929,215916.49,True,73.69163333333334,238023.9756666667,10336,0.0,Israel,MENA
UTI,brake_shoe,2025,0.309,0.309,77281.52,True,17.312169338677354,111836.61392785572,10336,0.0,Israel,MENA
UTI,clutch_booster,2025,0.0178,0.0178,388139.65,True,305.86260869565217,395174.4904347826,10336,0.0,Israel,MENA
UTI,clutch_disc,2025,0.0128,0.0066,166849.31,True,65.40545454545455,169007.69454545455,10336,0.0062,Israel,MENA
UTI,clutch_kit,2025,0.3261,0.0088,165826.48,True,126.9728006329114,246073.28762658223,10336,0.3173,Israel,MENA
UTI,clutch_pressure_plate,2025,0.0139,0.0074,251090.54,True,98.54416666666668,254638.12666666668,10336,0.0064999999999999,Israel,MENA
UTI,fuel_filter,2025,1.4491,0.5657,0.0,True,8.685486300272391,112216.48299951928,10336,0.8834000000000001,Israel,MENA
UTI,oil_filter,2025,0.9134,0.5264,12595.12,True,11.25568934836031,145423.5063808152,10336,0.387,Israel,MENA
UTI,pilot_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,release_bearing,2025,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,urea_filter,2025,0.0317,0.0317,25222.3,True,10.080853658536585,26048.925853658533,10336,0.0,Israel,MENA
BELGIUM,air_filter,2026,0.2761,0.1344,64988.79,True,18.73167044595616,89771.5306122449,9593,0.1417,Belgium,Benelux
BELGIUM,blower_filter,2026,0.1625,0.1365,133461.88,True,16.62678433889602,159366.06520988446,9593,0.0259999999999999,Belgium,Benelux
BELGIUM,brake_pad,2026,0.1259,0.078,241511.49,True,71.86857438016528,276298.73420454544,9593,0.0479,Belgium,Benelux
BELGIUM,brake_rotor,2026,0.2032,0.2032,128796.39,True,67.45985626283367,161647.30757700204,9593,0.0,Belgium,Benelux
BELGIUM,brake_shoe,2026,0.0307,0.0284,164080.5,True,35.32061224489796,169274.03418367347,9593,0.0023,Belgium,Benelux
BELGIUM,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,9593,0.0,Belgium,Benelux
BELGIUM,clutch_disc,2026,0.0511,0.0188,164115.43,True,90.22367346938776,172958.78204081635,9593,0.0322999999999999,Belgium,Benelux
BELGIUM,clutch_kit,2026,0.0536,0.0028,65341.58,True,48.01922077922078,69037.23371428571,9593,0.0508,Belgium,Benelux
BELGIUM,clutch_pressure_plate,2026,0.0501,0.012,153123.14,True,84.088125,161196.935625,9593,0.0380999999999999,Belgium,Benelux
BELGIUM,fuel_filter,2026,0.186,0.0468,64873.69,True,8.315092540661805,79699.33049298933,9593,0.1392,Belgium,Benelux
BELGIUM,oil_filter,2026,0.4174,0.2905,31823.43,True,5.699120219945014,54625.49739615096,9593,0.1269,Belgium,Benelux
BELGIUM,pilot_bearing,2026,0.0094,0.0094,2972.97,True,3.131111111111111,3001.17,9593,0.0,Belgium,Benelux
BELGIUM,release_bearing,2026,0.0341,0.0292,26357.4,True,18.97938775510204,27286.66577551021,9593,0.0048999999999999,Belgium,Benelux
BELGIUM,urea_filter,2026,0.0008,0.0008,99249.15,True,10.455,99332.955,9593,0.0,Belgium,Benelux
CYPRUS,air_filter,2026,0.2233,0.0497,12802.62,True,14.905141700404858,16483.596206477734,2308,0.1736,Cyprus,Med
CYPRUS,blower_filter,2026,0.1799,0.1573,29983.52,True,16.53005025125628,36562.81815075377,2308,0.0226,Cyprus,Med
CYPRUS,brake_pad,2026,0.1284,0.0279,48657.7,True,62.34652173913044,55825.07556521739,2308,0.1004999999999999,Cyprus,Med
CYPRUS,brake_rotor,2026,0.0326,0.0326,27357.17,True,51.13777777777778,28279.19111111111,2308,0.0,Cyprus,Med
CYPRUS,brake_shoe,2026,0.0289,0.0289,46811.02,True,43.588125,48204.1074375,2308,0.0,Cyprus,Med
CYPRUS,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,2308,0.0,Cyprus,Med
CYPRUS,clutch_disc,2026,0.0294,0.0226,41645.83,True,96.99153846153848,42909.056615384616,2308,0.0068,Cyprus,Med
CYPRUS,clutch_kit,2026,0.1929,0.1055,12983.03,True,48.48359375,16086.85640625,2308,0.0873999999999999,Cyprus,Med
CYPRUS,clutch_pressure_plate,2026,0.0362,0.0271,25069.57,True,58.796875,26011.7375,2308,0.0091,Cyprus,Med
CYPRUS,fuel_filter,2026,0.2016,0.0746,15592.08,True,8.829641255605381,19530.283493273542,2308,0.127,Cyprus,Med
CYPRUS,oil_filter,2026,0.3581,0.2948,10217.04,True,7.195707070707071,15916.184469696973,2308,0.0632999999999999,Cyprus,Med
CYPRUS,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,2308,0.0,Cyprus,Med
CYPRUS,release_bearing,2026,0.006,0.006,13587.02,True,41.2,13670.160000000002,2308,0.0,Cyprus,Med
CYPRUS,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,2308,0.0,Cyprus,Med
DENMARK,air_filter,2026,0.3598,0.3598,7496.54,True,27.535490196078435,11708.09043137255,851,0.0,Denmark,Nordics
DENMARK,blower_filter,2026,0.0894,0.0894,14355.36,True,18.535,15764.0175,851,0.0,Denmark,Nordics
DENMARK,brake_pad,2026,0.1499,0.0294,17829.48,True,61.640392156862745,20970.061411764706,851,0.1205,Denmark,Nordics
DENMARK,brake_rotor,2026,0.1834,0.1834,13439.11,True,77.40307692307692,16455.894153846155,851,0.0,Denmark,Nordics
DENMARK,brake_shoe,2026,0.0071,0.0071,10262.08,True,24.30333333333333,10333.777333333332,851,0.0,Denmark,Nordics
DENMARK,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_disc,2026,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_kit,2026,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,clutch_pressure_plate,2026,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,fuel_filter,2026,0.1282,0.1282,10115.15,True,13.641467889908258,11602.068440366971,851,0.0,Denmark,Nordics
DENMARK,oil_filter,2026,0.2822,0.2822,6515.1,True,10.67175,9076.323375,851,0.0,Denmark,Nordics
DENMARK,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,release_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,851,0.0,Denmark,Nordics
DENMARK,urea_filter,2026,0.0965,0.0965,7907.87,True,10.295365853658536,8752.090512195122,851,0.0,Denmark,Nordics
FINLAND,air_filter,2026,0.2309,0.2226,9812.37,True,21.193021582733813,12758.198992805756,1204,0.0083,Finland,Nordics
FINLAND,blower_filter,2026,0.1844,0.1844,18239.94,True,18.57427927927928,22363.43225225225,1204,0.0,Finland,Nordics
FINLAND,brake_pad,2026,0.0187,0.0042,32870.91,True,69.55333333333334,33496.88533333334,1204,0.0145,Finland,Nordics
FINLAND,brake_rotor,2026,0.0864,0.0864,15837.78,True,57.59192307692308,17335.168846153847,1204,0.0,Finland,Nordics
FINLAND,brake_shoe,2026,0.0033,0.0033,5292.0,True,8.82,5309.64,1204,0.0,Finland,Nordics
FINLAND,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,clutch_disc,2026,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,clutch_kit,2026,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,clutch_pressure_plate,2026,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,fuel_filter,2026,0.1279,0.0939,12452.32,True,11.859350649350649,14278.658181818182,1204,0.034,Finland,Nordics
FINLAND,oil_filter,2026,0.3447,0.3447,4903.07,True,6.2142891566265055,7482.004144578313,1204,0.0,Finland,Nordics
FINLAND,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,release_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
FINLAND,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,1204,0.0,Finland,Nordics
GERMANY,air_filter,2026,0.1032,0.0797,122781.11,True,20.2901724137931,136903.8803275862,13780,0.0235,Germany,DACH
GERMANY,blower_filter,2026,0.0667,0.0667,207389.76,True,16.466666666666665,222209.4333333333,13780,0.0,Germany,DACH
GERMANY,brake_pad,2026,0.0702,0.0204,334865.34,True,66.1729057591623,360146.03959424084,13780,0.0498,Germany,DACH
GERMANY,brake_rotor,2026,0.3234,0.3234,130284.28,True,57.07638863428048,192552.9046966086,13780,0.0,Germany,DACH
GERMANY,brake_shoe,2026,0.0261,0.0261,223357.13,True,33.99,229340.727,13780,0.0,Germany,DACH
GERMANY,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,13780,0.0,Germany,DACH
GERMANY,clutch_disc,2026,0.02,0.02,370506.48,True,140.08314814814815,378070.4085370371,13780,0.0,Germany,DACH
GERMANY,clutch_kit,2026,0.0188,0.0173,92148.21,True,46.39473684210526,93912.22631578946,13780,0.0015,Germany,DACH
GERMANY,clutch_pressure_plate,2026,0.0204,0.0185,183981.11,True,69.58690909090909,187808.10894545456,13780,0.0019,Germany,DACH
GERMANY,fuel_filter,2026,0.1707,0.1678,152973.39,True,13.669908854166668,184468.5850325521,13780,0.0028999999999999,Germany,DACH
GERMANY,oil_filter,2026,0.2316,0.2153,61150.69,True,5.897725527831095,79586.8571353167,13780,0.0163,Germany,DACH
GERMANY,pilot_bearing,2026,0.0148,0.0148,4227.66,True,3.18,4291.41,13780,0.0,Germany,DACH
GERMANY,release_bearing,2026,0.0104,0.0099,52357.35,True,26.13714285714285,52906.80457142857,13780,0.0004999999999999,Germany,DACH
GERMANY,urea_filter,2026,0.0008,0.0008,133242.14,True,10.15,133343.595,13780,0.0,Germany,DACH
GREECE,air_filter,2026,0.2927,0.0709,20916.83,True,15.88519266055046,29575.051695412843,3742,0.2218,Greece,Med
GREECE,blower_filter,2026,0.141,0.1168,53433.84,True,16.705904761904762,62204.43638095238,3742,0.0241999999999999,Greece,Med
GREECE,brake_pad,2026,0.0785,0.0563,105334.5,True,76.64871794871794,114298.5682051282,3742,0.0221999999999999,Greece,Med
GREECE,brake_rotor,2026,0.0956,0.0956,70669.35,True,83.94280898876404,78142.36088764045,3742,0.0,Greece,Med
GREECE,brake_shoe,2026,0.0113,0.0113,93646.84,True,50.87428571428571,94717.74514285714,3742,0.0,Greece,Med
GREECE,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,3742,0.0,Greece,Med
GREECE,clutch_disc,2026,0.0242,0.0134,80700.84,True,111.05111111111113,82699.76244444445,3742,0.0107999999999999,Greece,Med
GREECE,clutch_kit,2026,0.043,0.0286,18332.65,True,34.29708333333333,19154.92104166667,3742,0.0143999999999999,Greece,Med
GREECE,clutch_pressure_plate,2026,0.0309,0.0201,67356.26,True,93.33,69502.85100000001,3742,0.0108,Greece,Med
GREECE,fuel_filter,2026,0.2396,0.1133,26470.59,True,9.34860986547085,34809.54883408071,3742,0.1263,Greece,Med
GREECE,oil_filter,2026,0.4391,0.3169,13561.03,True,6.493192660550459,24177.40287155964,3742,0.1221999999999999,Greece,Med
GREECE,pilot_bearing,2026,0.0027,0.0027,1218.03,True,3.28,1221.4719999999998,3742,0.0,Greece,Med
GREECE,release_bearing,2026,0.0018,0.0018,14869.19,True,26.67,14895.195000000002,3742,0.0,Greece,Med
GREECE,urea_filter,2026,0.0005,0.0005,39494.89,True,10.655,39516.1985,3742,0.0,Greece,Med
HUNGARY,air_filter,2026,0.2464,0.2212,28972.67,True,20.591804347826088,38444.898717391305,3734,0.0252,Hungary,CEE
HUNGARY,blower_filter,2026,0.1114,0.1039,54516.18,True,16.430432692307694,61351.23567307693,3734,0.0074999999999999,Hungary,CEE
HUNGARY,brake_pad,2026,0.0549,0.0275,102196.05,True,72.39731707317073,108132.6327804878,3734,0.0273999999999999,Hungary,CEE
HUNGARY,brake_rotor,2026,0.0814,0.0814,66230.37,True,77.23657894736841,72100.34644736841,3734,0.0,Hungary,CEE
HUNGARY,brake_shoe,2026,0.008,0.007,35095.4,True,18.95,35379.65,3734,0.001,Hungary,CEE
HUNGARY,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,clutch_disc,2026,0.0054,0.004,100623.4,True,135.465,101165.262,3734,0.0014,Hungary,CEE
HUNGARY,clutch_kit,2026,0.0018,0.0,12792.21,True,22.88,12815.088,3734,0.0018,Hungary,CEE
HUNGARY,clutch_pressure_plate,2026,0.004,0.0027,59479.21,True,79.96666666666667,59719.10666666667,3734,0.0013,Hungary,CEE
HUNGARY,fuel_filter,2026,0.0828,0.0,24071.54,True,7.028187702265372,26243.2528802589,3734,0.0828,Hungary,CEE
HUNGARY,oil_filter,2026,0.2429,0.1869,16139.77,True,5.709151047409041,21317.97001102536,3734,0.0559999999999999,Hungary,CEE
HUNGARY,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
HUNGARY,release_bearing,2026,0.0036,0.0,9247.72,True,16.57,9280.857,3734,0.0036,Hungary,CEE
HUNGARY,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,3734,0.0,Hungary,CEE
ICELAND,air_filter,2026,0.3645,0.3645,2612.28,True,20.25027027027027,4110.804864864865,406,0.0,Iceland,Nordics
ICELAND,blower_filter,2026,0.1872,0.1872,5546.08,True,16.806315789473683,6823.364210526315,406,0.0,Iceland,Nordics
ICELAND,brake_pad,2026,0.1539,0.0369,7970.52,True,58.0096,9420.75904,406,0.117,Iceland,Nordics
ICELAND,brake_rotor,2026,0.2365,0.2365,6239.65,True,80.51166666666667,8171.934166666667,406,0.0,Iceland,Nordics
ICELAND,brake_shoe,2026,0.0049,0.0049,7362.9,True,36.45,7399.35,406,0.0,Iceland,Nordics
ICELAND,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,clutch_disc,2026,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,clutch_kit,2026,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,clutch_pressure_plate,2026,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,fuel_filter,2026,0.1232,0.1232,4714.01,True,13.2416,5376.0896,406,0.0,Iceland,Nordics
ICELAND,oil_filter,2026,0.1921,0.1921,2207.44,True,6.73,2732.38,406,0.0,Iceland,Nordics
ICELAND,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,release_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
ICELAND,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,406,0.0,Iceland,Nordics
IRELAND,air_filter,2026,0.474,0.3664,13782.07,True,27.90732584269663,26202.188233707864,2161,0.1075999999999999,Ireland,UK/IE
IRELAND,blower_filter,2026,0.0623,0.0623,29036.1,True,16.491196581196583,30965.519820512825,2161,0.0,Ireland,UK/IE
IRELAND,brake_pad,2026,0.2012,0.1354,46932.31,True,72.98376543209876,58759.22954938272,2161,0.0658,Ireland,UK/IE
IRELAND,brake_rotor,2026,0.7903,0.7903,6478.98,True,65.82614555256065,30898.792722371967,2161,0.0,Ireland,UK/IE
IRELAND,brake_shoe,2026,0.1076,0.0831,22217.16,True,26.51683168316832,24896.65326732673,2161,0.0245,Ireland,UK/IE
IRELAND,clutch_booster,2026,0.0373,0.0373,26670.07,True,147.53571428571428,27707.207142857143,2161,0.0,Ireland,UK/IE
IRELAND,clutch_disc,2026,0.1731,0.0719,24284.7,True,78.20138461538461,29364.619923076923,2161,0.1012,Ireland,UK/IE
IRELAND,clutch_kit,2026,0.4687,0.2876,5706.12,True,38.12840909090909,10740.772840909089,2161,0.1810999999999999,Ireland,UK/IE
IRELAND,clutch_pressure_plate,2026,0.221,0.1198,20024.01,True,68.44867469879517,25702.477349397588,2161,0.1012,Ireland,UK/IE
IRELAND,fuel_filter,2026,0.7003,0.4106,8240.43,True,14.644365019011406,27497.72419619772,2161,0.2897,Ireland,UK/IE
IRELAND,oil_filter,2026,0.3259,0.204,11856.72,True,9.367696078431372,17589.72292647059,2161,0.1219,Ireland,UK/IE
IRELAND,pilot_bearing,2026,0.0107,0.0107,590.75,True,3.18,597.2040000000001,2161,0.0,Ireland,UK/IE
IRELAND,release_bearing,2026,0.0533,0.032,6530.39,True,24.49,6898.8330000000005,2161,0.0213,Ireland,UK/IE
IRELAND,urea_filter,2026,0.0309,0.0309,8910.8,True,6.312222222222222,9195.014111111112,2161,0.0,Ireland,UK/IE
ITUK,air_filter,2026,0.2591,0.2175,181877.87,True,28.40160339437249,245469.3778168825,23068,0.0416,United Kingdom,UK/IE
ITUK,blower_filter,2026,0.0003,0.0003,294115.43,True,17.02,294200.91199999995,23068,0.0,United Kingdom,UK/IE
ITUK,brake_pad,2026,0.2974,0.2864,408685.7,True,84.12232976653696,581638.6124717898,23068,0.011,United Kingdom,UK/IE
ITUK,brake_rotor,2026,0.5366,0.5366,161308.96,True,80.55803794739111,348123.5051858559,23068,0.0,United Kingdom,UK/IE
ITUK,brake_shoe,2026,0.0879,0.0879,305380.79,True,48.42524671052632,334821.84080592106,23068,0.0,United Kingdom,UK/IE
ITUK,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,23068,0.0,United Kingdom,UK/IE
ITUK,clutch_disc,2026,0.0521,0.0434,290915.73,True,88.7718888888889,306893.2970777778,23068,0.0087,United Kingdom,UK/IE
ITUK,clutch_kit,2026,0.096,0.0544,156311.31,True,66.69036144578314,172914.76915662654,23068,0.0416,United Kingdom,UK/IE
ITUK,clutch_pressure_plate,2026,0.0469,0.039,295354.01,True,89.63388888888889,309873.31727777777,23068,0.0078999999999999,United Kingdom,UK/IE
ITUK,fuel_filter,2026,0.5486,0.4586,95146.63,True,12.194256037119056,210785.03215522517,23068,0.0899999999999999,United Kingdom,UK/IE
ITUK,oil_filter,2026,0.3151,0.2144,95595.26,True,8.074894437304938,139579.3952854782,23068,0.1006999999999999,United Kingdom,UK/IE
ITUK,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,23068,0.0,United Kingdom,UK/IE
ITUK,release_bearing,2026,0.0289,0.0243,59117.46,True,23.479466666666667,60877.561173333335,23068,0.0046,United Kingdom,UK/IE
ITUK,urea_filter,2026,0.202,0.1809,57336.74,True,20.18586926286509,71849.583054242,23068,0.0211,United Kingdom,UK/IE
IUK,air_filter,2026,0.1388,0.1116,381889.35,True,18.560392038600725,443435.6063902292,47783,0.0272,United Kingdom,UK/IE
IUK,blower_filter,2026,0.1316,0.1224,655099.93,True,15.788203497615262,754407.7277265501,47783,0.0092,United Kingdom,UK/IE
IUK,brake_pad,2026,0.1103,0.0385,1009672.62,True,59.37434535104365,1134833.7375635677,47783,0.0718,United Kingdom,UK/IE
IUK,brake_rotor,2026,0.2942,0.2942,599275.72,True,71.08213655761024,849132.9868899004,47783,0.0,United Kingdom,UK/IE
IUK,brake_shoe,2026,0.0204,0.0204,750088.89,True,32.0502868852459,765729.4291188525,47783,0.0,United Kingdom,UK/IE
IUK,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,47783,0.0,United Kingdom,UK/IE
IUK,clutch_disc,2026,0.0138,0.0138,1431289.73,True,151.86742424242425,1451336.2265151516,47783,0.0,United Kingdom,UK/IE
IUK,clutch_kit,2026,0.0008,0.0008,380917.53,True,53.19,381234.006,47783,0.0,United Kingdom,UK/IE
IUK,clutch_pressure_plate,2026,0.0224,0.0224,663971.6,True,71.0692523364486,679180.4168785047,47783,0.0,United Kingdom,UK/IE
IUK,fuel_filter,2026,0.0721,0.0692,554908.45,True,12.51597911227154,598051.029921671,47783,0.0029,United Kingdom,UK/IE
IUK,oil_filter,2026,0.2523,0.2289,168356.95,True,4.712580859180627,225181.2511942279,47783,0.0234,United Kingdom,UK/IE
IUK,pilot_bearing,2026,0.0088,0.0088,14360.01,True,3.031904761904762,14487.350523809524,47783,0.0,United Kingdom,UK/IE
IUK,release_bearing,2026,0.0268,0.0225,161367.59,True,23.133645833333333,165808.09314583332,47783,0.0043,United Kingdom,UK/IE
IUK,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,47783,0.0,United Kingdom,UK/IE
MALTA,air_filter,2026,0.0311,0.0311,9884.0,True,21.18,10202.406,1040,0.0,Malta,Med
MALTA,blower_filter,2026,0.0727,0.0727,14771.27,True,16.535,15928.1655,1040,0.0,Malta,Med
MALTA,brake_pad,2026,0.1294,0.1144,28899.58,True,82.57807692307694,33196.38692307693,1040,0.0149999999999999,Malta,Med
MALTA,brake_rotor,2026,0.1412,0.1412,14503.34,True,70.12088235294118,16885.10847058824,1040,0.0,Malta,Med
MALTA,brake_shoe,2026,0.0478,0.0478,18848.01,True,41.09304347826087,19794.51904347826,1040,0.0,Malta,Med
MALTA,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
MALTA,clutch_disc,2026,0.0156,0.0156,29873.77,True,157.50666666666666,30351.534666666663,1040,0.0,Malta,Med
MALTA,clutch_kit,2026,0.0554,0.0415,12319.3,True,90.25125,13041.305625,1040,0.0138999999999999,Malta,Med
MALTA,clutch_pressure_plate,2026,0.0156,0.0156,21670.05,True,114.25333333333332,22016.61733333333,1040,0.0,Malta,Med
MALTA,fuel_filter,2026,0.1567,0.1567,10617.31,True,13.070132450331124,12590.458589403972,1040,0.0,Malta,Med
MALTA,oil_filter,2026,0.4983,0.491,3515.42,True,7.273270833333333,7006.34179375,1040,0.0073,Malta,Med
MALTA,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
MALTA,release_bearing,2026,0.0208,0.0208,4385.56,True,30.993333333333336,4478.536666666667,1040,0.0,Malta,Med
MALTA,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,1040,0.0,Malta,Med
NORWAY,air_filter,2026,0.2245,0.2245,57718.73,True,18.773370786516853,74427.02848314606,7929,0.0,Norway,Nordics
NORWAY,blower_filter,2026,0.1072,0.1072,124802.77,True,17.63,139788.27,7929,0.0,Norway,Nordics
NORWAY,brake_pad,2026,0.1573,0.1498,202705.52,True,75.84581162324649,240552.57614428856,7929,0.0075,Norway,Nordics
NORWAY,brake_rotor,2026,0.3506,0.3506,96192.47,True,74.72710791366906,148124.0733064748,7929,0.0,Norway,Nordics
NORWAY,brake_shoe,2026,0.0204,0.0204,150038.3,True,38.63481481481482,153167.72333333333,7929,0.0,Norway,Nordics
NORWAY,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,clutch_disc,2026,0.0006,0.0006,253774.02,True,160.13,253934.154,7929,0.0,Norway,Nordics
NORWAY,clutch_kit,2026,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,clutch_pressure_plate,2026,0.0006,0.0006,189922.43,True,119.84,190042.272,7929,0.0,Norway,Nordics
NORWAY,fuel_filter,2026,0.0971,0.0,48609.61,True,6.79,53837.91,7929,0.0971,Norway,Nordics
NORWAY,oil_filter,2026,0.2863,0.28,33430.98,True,5.907577092511014,46841.17876651983,7929,0.0062999999999999,Norway,Nordics
NORWAY,pilot_bearing,2026,0.0038,0.0038,2382.87,True,3.016666666666667,2391.9150000000004,7929,0.0,Norway,Nordics
NORWAY,release_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
NORWAY,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,7929,0.0,Norway,Nordics
PORTUGAL,air_filter,2026,0.3102,0.1437,50534.19,True,21.62264509990485,73259.68386298763,7208,0.1664999999999999,Portugal,Iberia
PORTUGAL,blower_filter,2026,0.1246,0.0,74847.39,True,12.617156398104264,85496.3751848341,7208,0.1246,Portugal,Iberia
PORTUGAL,brake_pad,2026,0.0271,0.0268,236417.07,True,83.36886075949367,243003.55534177215,7208,0.0002999999999999,Portugal,Iberia
PORTUGAL,brake_rotor,2026,0.1978,0.1978,110596.52,True,81.37794029850747,137854.23086567165,7208,0.0,Portugal,Iberia
PORTUGAL,brake_shoe,2026,0.0602,0.0599,129595.04,True,40.70073529411765,137898.16125,7208,0.0002999999999999,Portugal,Iberia
PORTUGAL,clutch_booster,2026,0.0015,0.0015,299113.04,True,442.07,299546.632,7208,0.0,Portugal,Iberia
PORTUGAL,clutch_disc,2026,0.0664,0.0421,138179.35,True,109.21211111111111,148004.2529777778,7208,0.0243,Portugal,Iberia
PORTUGAL,clutch_kit,2026,0.1161,0.0118,54727.64,True,60.91483050847457,61913.83372881355,7208,0.1042999999999999,Portugal,Iberia
PORTUGAL,clutch_pressure_plate,2026,0.0664,0.0398,132633.11,True,104.82855555555555,142063.6584888889,7208,0.0266,Portugal,Iberia
PORTUGAL,fuel_filter,2026,0.2336,0.0217,40897.22,True,7.875161086544535,53363.66655464308,7208,0.2119,Portugal,Iberia
PORTUGAL,oil_filter,2026,0.2921,0.0344,27610.9,True,5.755639211723093,39001.36242647802,7208,0.2577,Portugal,Iberia
PORTUGAL,pilot_bearing,2026,0.003,0.003,2148.47,True,3.18,2154.768,7208,0.0,Portugal,Iberia
PORTUGAL,release_bearing,2026,0.0384,0.0,16195.99,True,16.57,16841.748,7208,0.0384,Portugal,Iberia
PORTUGAL,urea_filter,2026,0.0211,0.0141,85117.87,True,16.80834862385321,86949.58743119266,7208,0.007,Portugal,Iberia
ROMANIA,air_filter,2026,0.4332,0.4332,6667.52,True,21.96875,11764.265625,1071,0.0,Romania,CEE
ROMANIA,blower_filter,2026,0.3175,0.3175,12412.81,True,16.980588235294118,18186.21,1071,0.0,Romania,CEE
ROMANIA,brake_pad,2026,0.119,0.1144,29310.96,True,77.66549019607844,33271.896,1071,0.0045999999999999,Romania,CEE
ROMANIA,brake_rotor,2026,0.0448,0.0448,20830.84,True,81.45,21812.31,1071,0.0,Romania,CEE
ROMANIA,brake_shoe,2026,0.0411,0.0411,18051.39,True,35.153636363636366,18824.772272727278,1071,0.0,Romania,CEE
ROMANIA,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,1071,0.0,Romania,CEE
ROMANIA,clutch_disc,2026,0.0373,0.0327,30869.69,True,149.7075,32067.3465,1071,0.0046,Romania,CEE
ROMANIA,clutch_kit,2026,0.0,0.0,0.0,False,0.0,0.0,1071,0.0,Romania,CEE
ROMANIA,clutch_pressure_plate,2026,0.028,0.028,25210.94,True,121.09,25937.478,1071,0.0,Romania,CEE
ROMANIA,fuel_filter,2026,0.1615,0.0028,6584.0,True,7.3318497109826595,7852.411040462428,1071,0.1587,Romania,CEE
ROMANIA,oil_filter,2026,0.3175,0.3175,4718.82,True,6.45529411764706,6913.620000000001,1071,0.0,Romania,CEE
ROMANIA,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,1071,0.0,Romania,CEE
ROMANIA,release_bearing,2026,0.0124,0.0124,4228.02,True,26.65,4282.655,1071,0.0,Romania,CEE
ROMANIA,urea_filter,2026,0.0047,0.0047,11235.64,True,10.54,11288.34,1071,0.0,Romania,CEE
SWEDEN,air_filter,2026,0.1743,0.1672,72660.46,True,20.84649456521739,88003.47680706522,8443,0.0071,Sweden,Nordics
SWEDEN,blower_filter,2026,0.1848,0.1848,118297.59,True,17.186923076923076,145109.19153846154,8443,0.0,Sweden,Nordics
SWEDEN,brake_pad,2026,0.0865,0.0506,216515.11,True,70.1786301369863,237007.2696986301,8443,0.0358999999999999,Sweden,Nordics
SWEDEN,brake_rotor,2026,0.1791,0.1791,128971.1,True,74.43145502645503,157109.9152698413,8443,0.0,Sweden,Nordics
SWEDEN,brake_shoe,2026,0.0078,0.0078,119657.83,True,28.568181818181817,120600.57954545454,8443,0.0,Sweden,Nordics
SWEDEN,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,clutch_disc,2026,0.0006,0.0006,265358.22,True,157.24,265515.464,8443,0.0,Sweden,Nordics
SWEDEN,clutch_kit,2026,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,clutch_pressure_plate,2026,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,fuel_filter,2026,0.0884,0.0884,105169.08,True,13.663646112600537,115362.16412868632,8443,0.0,Sweden,Nordics
SWEDEN,oil_filter,2026,0.2167,0.2167,40233.06,True,6.083934426229509,51366.65836065574,8443,0.0,Sweden,Nordics
SWEDEN,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,release_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
SWEDEN,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,8443,0.0,Sweden,Nordics
UMI,air_filter,2026,0.0766,0.0216,98955.51,True,11.558873239436618,107162.31380281688,18542,0.055,Israel,MENA
UMI,blower_filter,2026,0.0043,0.0,248152.36,True,13.44125,249227.6575,18542,0.0043,Israel,MENA
UMI,brake_pad,2026,0.0675,0.0206,316442.16,True,45.75640718562874,339366.1208143712,18542,0.0469,Israel,MENA
UMI,brake_rotor,2026,0.0697,0.0697,243006.44,True,56.34931888544892,261207.2676934985,18542,0.0,Israel,MENA
UMI,brake_shoe,2026,0.0696,0.0394,257569.28,True,29.85964341085272,276828.7540620155,18542,0.0301999999999999,Israel,MENA
UMI,clutch_booster,2026,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UMI,clutch_disc,2026,0.0124,0.0124,473193.23,True,129.20304347826087,479136.5664347826,18542,0.0,Israel,MENA
UMI,clutch_kit,2026,0.0104,0.0007,12823.82,True,4.6593103448275865,12958.939862068968,18542,0.0097,Israel,MENA
UMI,clutch_pressure_plate,2026,0.0121,0.0121,175407.66,True,47.88111111111111,177562.31244444443,18542,0.0,Israel,MENA
UMI,fuel_filter,2026,0.1311,0.0017,118002.31,True,7.324331550802139,135807.75561497326,18542,0.1294,Israel,MENA
UMI,oil_filter,2026,0.2372,0.0,58696.25,True,4.149904502046384,76947.52927694406,18542,0.2372,Israel,MENA
UMI,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UMI,release_bearing,2026,0.0144,0.0,41503.28,True,15.14,42108.882000000005,18542,0.0144,Israel,MENA
UMI,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,18542,0.0,Israel,MENA
UTI,air_filter,2026,0.5833,0.0054,48107.45,True,17.870522823779194,115443.5774416136,10336,0.5779000000000001,Israel,MENA
UTI,blower_filter,2026,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,brake_pad,2026,0.0884,0.0884,414777.64,True,70.43260945709281,454994.6570928196,10336,0.0,Israel,MENA
UTI,brake_rotor,2026,0.0616,0.0616,216433.66,True,71.40668341708543,230643.58743718595,10336,0.0,Israel,MENA
UTI,brake_shoe,2026,0.1737,0.1737,82491.42,True,15.45361853832442,99830.37575757576,10336,0.0,Israel,MENA
UTI,clutch_booster,2026,0.0178,0.0155,291180.88,True,229.45695652173916,296458.3878260869,10336,0.0023,Israel,MENA
UTI,clutch_disc,2026,0.0104,0.0062,182334.93,True,71.30814814814815,184260.2548148148,10336,0.0042,Israel,MENA
UTI,clutch_kit,2026,0.1791,0.0,201710.14,True,126.78198847262249,245703.49365994235,10336,0.1791,Israel,MENA
UTI,clutch_pressure_plate,2026,0.0128,0.0093,136794.67,True,53.6239393939394,138564.2593939394,10336,0.0035,Israel,MENA
UTI,fuel_filter,2026,0.6937,0.4374,40434.68,True,10.218519468927814,132023.27153854736,10336,0.2563,Israel,MENA
UTI,oil_filter,2026,0.473,0.244,74451.82,True,10.93432498772705,141271.4788414335,10336,0.2289999999999999,Israel,MENA
UTI,pilot_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,release_bearing,2026,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
UTI,urea_filter,2026,0.0,0.0,0.0,False,0.0,0.0,10336,0.0,Israel,MENA
```

## TABLE `benchmark_tables` (240 rows)

```csv
system,code,pns,eur,pct_of_system
ZKK (Japan),275,19874.0,21597704.51,46.77
ZKK (Japan),200,16718.0,6282982.05,13.6
ZKK (Japan),283,12993.0,4926347.27,10.67
ZKK (Japan),114,22093.0,2278168.14,4.93
ZKK (Japan),287,6621.0,2244840.64,4.86
ZKK (Japan),277,6360.0,1497035.98,3.24
ZKK (Japan),276,2018.0,1449622.95,3.14
ZKK (Japan),288,4922.0,839732.29,1.82
ZKK (Japan),280,6517.0,796536.95,1.72
ZKK (Japan),299,60.0,589792.82,1.28
ZKK (Japan),273,4469.0,569290.57,1.23
ZKK (Japan),070,1862.0,509958.86,1.1
ZKK (Japan),272,3381.0,371190.12,0.8
ZKK (Japan),270,4652.0,328306.63,0.71
ZKK (Japan),281,1038.0,314728.83,0.68
ZUK (Japan),11G00,61508.0,32042424.79,69.38
ZUK (Japan),11A99,5157.0,3045491.18,6.59
ZUK (Japan),11G75,1538.0,2143045.31,4.64
ZUK (Japan),11C97,1242.0,714061.36,1.55
ZUK (Japan),11G20,5016.0,651245.09,1.41
ZUK (Japan),11C94,2767.0,431823.94,0.94
ZUK (Japan),13G00,1239.0,429134.89,0.93
ZUK (Japan),11C95,158.0,394442.21,0.85
ZUK (Japan),11E94,2085.0,391012.54,0.85
ZUK (Japan),11G14,13.0,354725.28,0.77
ZUK (Japan),11C96,2124.0,344317.24,0.75
ZUK (Japan),11G22,5506.0,342364.26,0.74
ZUK (Japan),11C99,1232.0,267665.43,0.58
ZUK (Japan),11G09,2980.0,249568.49,0.54
ZUK (Japan),11G10,1010.0,233187.66,0.5
HKK (Japan),1110,116816.0,35450059.14,76.76
HKK (Japan),1133,118.0,1426690.55,3.09
HKK (Japan),112Z,219.0,1078286.35,2.33
HKK (Japan),112T,199.0,958746.58,2.08
HKK (Japan),112L,396.0,956080.7,2.07
HKK (Japan),111J,708.0,917699.69,1.99
HKK (Japan),1111,167.0,847161.72,1.83
HKK (Japan),1128,568.0,460672.69,1.0
HKK (Japan),113G,9501.0,422800.36,0.92
HKK (Japan),113F,259.0,381709.52,0.83
HKK (Japan),1131,1407.0,315218.5,0.68
HKK (Japan),313A,913.0,297413.65,0.64
HKK (Japan),1299,25.0,244399.46,0.53
HKK (Japan),1129,351.0,228104.7,0.49
HKK (Japan),111X,312.0,223797.26,0.48
ZKK + EPLE (Japan),275,13467.0,20599729.06,44.6
ZKK + EPLE (Japan),200,7283.0,6166519.31,13.35
ZKK + EPLE (Japan),283,8467.0,4712164.15,10.2
ZKK + EPLE (Japan),287,4570.0,2164392.25,4.69
ZKK + EPLE (Japan),277,4110.0,1468125.32,3.18
ZKK + EPLE (Japan),276,1469.0,1448322.63,3.14
ZKK + EPLE (Japan),114,1935.0,1131886.38,2.45
ZKK + EPLE (Japan),288,3610.0,837022.14,1.81
ZKK + EPLE (Japan),280,2385.0,735473.56,1.59
ZKK + EPLE (Japan),299,29.0,589789.43,1.28
ZKK + EPLE (Japan),273,2260.0,562905.46,1.22
ZKK + EPLE (Japan),070,823.0,486418.42,1.05
ZKK + EPLE (Japan),114-2207,59.0,425229.34,0.92
ZKK + EPLE (Japan),272,1476.0,360105.7,0.78
ZKK + EPLE (Japan),270,1958.0,305608.67,0.66
Figure key prefix (Japan),146,686.0,3665473.24,7.95
Figure key prefix (Japan),150,2397.0,2479312.01,5.38
Figure key prefix (Japan),302,416.0,1930713.4,4.19
Figure key prefix (Japan),411,830.0,1847888.3,4.01
Figure key prefix (Japan),040,2193.0,1837813.07,3.99
Figure key prefix (Japan),803,759.0,1318540.81,2.86
Figure key prefix (Japan),601,1289.0,1271560.44,2.76
Figure key prefix (Japan),130,696.0,1239786.15,2.69
Figure key prefix (Japan),057,952.0,1151546.55,2.5
Figure key prefix (Japan),826,1263.0,1112228.56,2.41
Figure key prefix (Japan),801,2118.0,1106420.75,2.4
Figure key prefix (Japan),201,1788.0,1092893.95,2.37
Figure key prefix (Japan),050,1274.0,961468.6,2.09
Figure key prefix (Japan),055,130.0,955046.28,2.07
Figure key prefix (Japan),425,1528.0,909342.76,1.97
"AIM L1 (ISZE, live)",Intake Exhaust Emission,926.0,7878944.47,17.06
"AIM L1 (ISZE, live)",Accident & Body,3698.0,6799860.54,14.72
"AIM L1 (ISZE, live)",Brakes,689.0,4825888.08,10.45
"AIM L1 (ISZE, live)",Maintenance Service,545.0,4682408.75,10.14
"AIM L1 (ISZE, live)",Electrical,1764.0,3656643.78,7.92
"AIM L1 (ISZE, live)",Fuel System,877.0,2934074.89,6.35
"AIM L1 (ISZE, live)",Lighting,910.0,2551169.95,5.52
"AIM L1 (ISZE, live)",Wheels Hub,960.0,1767447.74,3.83
"AIM L1 (ISZE, live)",Driveline Axle,464.0,1381881.71,2.99
"AIM L1 (ISZE, live)",Cabin Interior,1075.0,1257159.71,2.72
"AIM L1 (ISZE, live)",Unknown,4180.0,1123510.37,2.43
"AIM L1 (ISZE, live)",Suspension,660.0,1118508.77,2.42
"AIM L1 (ISZE, live)",Steering,454.0,1118017.17,2.42
"AIM L1 (ISZE, live)",Transmission,1309.0,1086756.48,2.35
"AIM L1 (ISZE, live)",Clutch,248.0,1031011.65,2.23
"AIM L2 (ISZE, live)",Panels,2815.0,4322692.96,9.36
"AIM L2 (ISZE, live)",Sensors,66.0,3596931.71,7.79
"AIM L2 (ISZE, live)",Discs & Drums,89.0,2206461.17,4.78
"AIM L2 (ISZE, live)",Lamps,289.0,1973615.64,4.27
"AIM L2 (ISZE, live)",Pads & Shoes,267.0,1725515.2,3.74
"AIM L2 (ISZE, live)",Filters (unspecified),172.0,1569923.95,3.4
"AIM L2 (ISZE, live)",Wheel Rim,725.0,1402090.52,3.04
"AIM L2 (ISZE, live)",Fuel Control,68.0,1237668.83,2.68
"AIM L2 (ISZE, live)",Air Filter,52.0,1203146.04,2.61
"AIM L2 (ISZE, live)",Unknown,4180.0,1123510.37,2.43
"AIM L2 (ISZE, live)",DEF System,98.0,991662.81,2.15
"AIM L2 (ISZE, live)",EGR,192.0,986984.6,2.14
"AIM L2 (ISZE, live)",Turbo,295.0,887070.9,1.92
"AIM L2 (ISZE, live)",Oil Filter,51.0,864090.09,1.87
"AIM L2 (ISZE, live)",Clutch Kit,126.0,856946.76,1.86
"AIM L1>L2>L3 (ISZE, live)",Intake Exhaust Emission > Sensors > PM Sensor,6.0,2151978.71,4.66
"AIM L1>L2>L3 (ISZE, live)",Brakes > Discs & Drums > Brake Rotor,24.0,1660880.33,3.6
"AIM L1>L2>L3 (ISZE, live)",Wheels Hub > Wheel Rim > Wheel,553.0,1354864.22,2.93
"AIM L1>L2>L3 (ISZE, live)",Brakes > Pads & Shoes > Brake Pad Kit,37.0,1316022.14,2.85
"AIM L1>L2>L3 (ISZE, live)",Maintenance Service > Air Filter > Air Cleaner Filter,52.0,1203146.04,2.61
"AIM L1>L2>L3 (ISZE, live)",Lighting > Lamps > Rear Combination Lamp,102.0,1201482.81,2.6
"AIM L1>L2>L3 (ISZE, live)",Accident & Body > Panels > Panel,606.0,1157134.83,2.51
"AIM L1>L2>L3 (ISZE, live)",Intake Exhaust Emission > Sensors > NOx Sensor,20.0,1141314.58,2.47
"AIM L1>L2>L3 (ISZE, live)",Unknown > Unknown > Unknown,4180.0,1123510.37,2.43
"AIM L1>L2>L3 (ISZE, live)",Intake Exhaust Emission > EGR > EGR Component,192.0,986984.6,2.14
"AIM L1>L2>L3 (ISZE, live)",Maintenance Service > Filters (unspecified) > Filter Assembly,62.0,986137.83,2.14
"AIM L1>L2>L3 (ISZE, live)",Accident & Body > Panels > Door,1245.0,938353.14,2.03
"AIM L1>L2>L3 (ISZE, live)",Intake Exhaust Emission > Turbo > Turbocharger,295.0,887070.9,1.92
"AIM L1>L2>L3 (ISZE, live)",Accident & Body > Panels > Bumper,316.0,885831.56,1.92
"AIM L1>L2>L3 (ISZE, live)",Fuel System > Fuel Control > Injector Nozzle,35.0,876443.24,1.9
"15-level functional (ISZE, Apr 2026)",EXHAUST & EMISSION,849.0,7852204.3,17.82
"15-level functional (ISZE, Apr 2026)",ELECTRICAL & SENSORS,1685.0,5438871.95,12.35
"15-level functional (ISZE, Apr 2026)",BRAKES,794.0,5117837.91,11.62
"15-level functional (ISZE, Apr 2026)",BODY & EXTERIOR,1124.0,4614627.99,10.47
"15-level functional (ISZE, Apr 2026)",FILTERS & MAINTENANCE,227.0,4207611.18,9.55
"15-level functional (ISZE, Apr 2026)",UNCLASSIFIED,3335.0,3749866.85,8.51
"15-level functional (ISZE, Apr 2026)",DRIVETRAIN & CLUTCH,646.0,3245174.74,7.37
"15-level functional (ISZE, Apr 2026)",FUEL SYSTEM,460.0,1928883.64,4.38
"15-level functional (ISZE, Apr 2026)",ENGINE,1440.0,1612231.29,3.66
"15-level functional (ISZE, Apr 2026)",COOLING SYSTEM,665.0,1201523.76,2.73
"15-level functional (ISZE, Apr 2026)",STEERING & SUSPENSION,534.0,1179021.67,2.68
"15-level functional (ISZE, Apr 2026)",INTERIOR & CAB,839.0,1110220.27,2.52
"15-level functional (ISZE, Apr 2026)",CLIMATE CONTROL (HVAC),197.0,889422.1,2.02
"15-level functional (ISZE, Apr 2026)",GLASS & WIPERS,381.0,867849.61,1.97
"15-level functional (ISZE, Apr 2026)",ACCESSORIES & MISC,1684.0,717503.16,1.63
"15-level functional L1>L2 (ISZE, Apr 2026)",UNCLASSIFIED > Unclassified,3335.0,3749866.85,8.51
"15-level functional L1>L2 (ISZE, Apr 2026)",BRAKES > Front Disc Brakes,191.0,3577992.04,8.12
"15-level functional L1>L2 (ISZE, Apr 2026)",ELECTRICAL & SENSORS > Lamps & Lighting,560.0,2280636.81,5.18
"15-level functional L1>L2 (ISZE, Apr 2026)",EXHAUST & EMISSION > DPF & PM Sensors,4.0,2151978.71,4.88
"15-level functional L1>L2 (ISZE, Apr 2026)",EXHAUST & EMISSION > DEF / AdBlue System,282.0,2121099.16,4.81
"15-level functional L1>L2 (ISZE, Apr 2026)",ELECTRICAL & SENSORS > Engine Sensors & ECU,344.0,1928526.98,4.38
"15-level functional L1>L2 (ISZE, Apr 2026)",FUEL SYSTEM > Fuel Injection & Common Rail,178.0,1414401.58,3.21
"15-level functional L1>L2 (ISZE, Apr 2026)",FILTERS & MAINTENANCE > Air Filter / Cleaner,54.0,1207989.22,2.74
"15-level functional L1>L2 (ISZE, Apr 2026)",BODY & EXTERIOR > Front Bumper,161.0,1165432.24,2.65
"15-level functional L1>L2 (ISZE, Apr 2026)",FILTERS & MAINTENANCE > Transmission & Other Filters,59.0,1115989.22,2.53
"15-level functional L1>L2 (ISZE, Apr 2026)",DRIVETRAIN & CLUTCH > Rear Axle & Final Drive,202.0,1021286.38,2.32
"15-level functional L1>L2 (ISZE, Apr 2026)",EXHAUST & EMISSION > NOx & Emission Sensors,6.0,1010698.27,2.29
"15-level functional L1>L2 (ISZE, Apr 2026)",EXHAUST & EMISSION > EGR System,137.0,983908.08,2.23
"15-level functional L1>L2 (ISZE, Apr 2026)",FILTERS & MAINTENANCE > Fuel Filter,57.0,975103.59,2.21
"15-level functional L1>L2 (ISZE, Apr 2026)","BODY & EXTERIOR > Side Panels, Steps & Mudguards",246.0,955377.36,2.17
METRICS — ZKK (Japan),codes_used,132.0,,
METRICS — ZKK (Japan),codes_ge_0p5pct,16.0,,
METRICS — ZKK (Japan),codes_ge_1pct,12.0,,
METRICS — ZKK (Japan),max_code_share_pct,46.77,,
METRICS — ZKK (Japan),top10_share_pct,92.03,,
METRICS — ZKK (Japan),leading_noun_purity_pct,82.59,,
METRICS — ZKK (Japan),service_top_code_share_pct,34.07,,
METRICS — ZKK (Japan),service_top3_share_pct,73.44,,
METRICS — ZKK (Japan),eur_coverage_pct,100.0,,
METRICS — ZUK (Japan),codes_used,284.0,,
METRICS — ZUK (Japan),codes_ge_0p5pct,15.0,,
METRICS — ZUK (Japan),codes_ge_1pct,5.0,,
METRICS — ZUK (Japan),max_code_share_pct,69.38,,
METRICS — ZUK (Japan),top10_share_pct,87.91,,
METRICS — ZUK (Japan),leading_noun_purity_pct,82.6,,
METRICS — ZUK (Japan),service_top_code_share_pct,65.78,,
METRICS — ZUK (Japan),service_top3_share_pct,82.57,,
METRICS — ZUK (Japan),eur_coverage_pct,100.0,,
METRICS — HKK (Japan),codes_used,72.0,,
METRICS — HKK (Japan),codes_ge_0p5pct,13.0,,
METRICS — HKK (Japan),codes_ge_1pct,7.0,,
METRICS — HKK (Japan),max_code_share_pct,76.76,,
METRICS — HKK (Japan),top10_share_pct,92.89,,
METRICS — HKK (Japan),leading_noun_purity_pct,82.59,,
METRICS — HKK (Japan),service_top_code_share_pct,23.03,,
METRICS — HKK (Japan),service_top3_share_pct,63.92,,
METRICS — HKK (Japan),eur_coverage_pct,100.0,,
METRICS — ZKK + EPLE (Japan),codes_used,12268.0,,
METRICS — ZKK + EPLE (Japan),codes_ge_0p5pct,16.0,,
METRICS — ZKK + EPLE (Japan),codes_ge_1pct,12.0,,
METRICS — ZKK + EPLE (Japan),max_code_share_pct,44.6,,
METRICS — ZKK + EPLE (Japan),top10_share_pct,86.29,,
METRICS — ZKK + EPLE (Japan),leading_noun_purity_pct,82.85,,
METRICS — ZKK + EPLE (Japan),service_top_code_share_pct,33.98,,
METRICS — ZKK + EPLE (Japan),service_top3_share_pct,71.96,,
METRICS — ZKK + EPLE (Japan),eur_coverage_pct,100.0,,
METRICS — Figure key prefix (Japan),codes_used,287.0,,
METRICS — Figure key prefix (Japan),codes_ge_0p5pct,48.0,,
METRICS — Figure key prefix (Japan),codes_ge_1pct,33.0,,
METRICS — Figure key prefix (Japan),max_code_share_pct,7.95,,
METRICS — Figure key prefix (Japan),top10_share_pct,38.72,,
METRICS — Figure key prefix (Japan),leading_noun_purity_pct,82.55,,
METRICS — Figure key prefix (Japan),service_top_code_share_pct,25.7,,
METRICS — Figure key prefix (Japan),service_top3_share_pct,64.38,,
METRICS — Figure key prefix (Japan),eur_coverage_pct,99.84,,
"METRICS — AIM L1 (ISZE, live)",codes_used,25.0,,
"METRICS — AIM L1 (ISZE, live)",codes_ge_0p5pct,19.0,,
"METRICS — AIM L1 (ISZE, live)",codes_ge_1pct,18.0,,
"METRICS — AIM L1 (ISZE, live)",max_code_share_pct,17.06,,
"METRICS — AIM L1 (ISZE, live)",top10_share_pct,81.71,,
"METRICS — AIM L1 (ISZE, live)",leading_noun_purity_pct,86.18,,
"METRICS — AIM L1 (ISZE, live)",service_top_code_share_pct,100.0,,
"METRICS — AIM L1 (ISZE, live)",service_top3_share_pct,100.0,,
"METRICS — AIM L1 (ISZE, live)",eur_coverage_pct,100.0,,
"METRICS — AIM L2 (ISZE, live)",codes_used,110.0,,
"METRICS — AIM L2 (ISZE, live)",codes_ge_0p5pct,50.0,,
"METRICS — AIM L2 (ISZE, live)",codes_ge_1pct,30.0,,
"METRICS — AIM L2 (ISZE, live)",max_code_share_pct,9.36,,
"METRICS — AIM L2 (ISZE, live)",top10_share_pct,44.09,,
"METRICS — AIM L2 (ISZE, live)",leading_noun_purity_pct,88.77,,
"METRICS — AIM L2 (ISZE, live)",service_top_code_share_pct,33.53,,
"METRICS — AIM L2 (ISZE, live)",service_top3_share_pct,77.68,,
"METRICS — AIM L2 (ISZE, live)",eur_coverage_pct,100.0,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",codes_used,518.0,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",codes_ge_0p5pct,60.0,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",codes_ge_1pct,32.0,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",max_code_share_pct,4.66,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",top10_share_pct,28.79,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",leading_noun_purity_pct,90.49,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",service_top_code_share_pct,25.7,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",service_top3_share_pct,65.21,,
"METRICS — AIM L1>L2>L3 (ISZE, live)",eur_coverage_pct,100.0,,
"METRICS — 15-level functional (ISZE, Apr 2026)",codes_used,16.0,,
"METRICS — 15-level functional (ISZE, Apr 2026)",codes_ge_0p5pct,16.0,,
"METRICS — 15-level functional (ISZE, Apr 2026)",codes_ge_1pct,15.0,,
"METRICS — 15-level functional (ISZE, Apr 2026)",max_code_share_pct,17.82,,
"METRICS — 15-level functional (ISZE, Apr 2026)",top10_share_pct,88.45,,
"METRICS — 15-level functional (ISZE, Apr 2026)",leading_noun_purity_pct,20.09,,
"METRICS — 15-level functional (ISZE, Apr 2026)",service_top_code_share_pct,91.61,,
"METRICS — 15-level functional (ISZE, Apr 2026)",service_top3_share_pct,99.22,,
"METRICS — 15-level functional (ISZE, Apr 2026)",eur_coverage_pct,95.4,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",codes_used,94.0,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",codes_ge_0p5pct,47.0,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",codes_ge_1pct,29.0,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",max_code_share_pct,8.51,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",top10_share_pct,47.02,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",leading_noun_purity_pct,37.78,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",service_top_code_share_pct,26.71,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",service_top3_share_pct,71.43,,
"METRICS — 15-level functional L1>L2 (ISZE, Apr 2026)",eur_coverage_pct,95.4,,
```

## TABLE `pms_capture_by_db_year` — sample 60 of 3024 rows (full set in CSV)

```csv
year,distributor_code,pms_category,category_label,line_type,uio_units,uio_proxy_used,uio_source,expected_qty,actual_qty,actual_rev_eur,capture_rate,avg_sp_eur,revenue_gap_eur,revenue_gap_quotable,scope
2023,BELGIUM,oil_filter,Oil Filter,genuine,9593,False,model_bucket_split,9584.9,4186.0,22140.41,0.4367,5.29,28555.74,True,model_bucket
2023,BELGIUM,oil_filter,Oil Filter,bvp,9593,False,model_bucket_split,9584.9,1836.0,9524.56,0.1916,5.19,40198.83,True,model_bucket
2023,BELGIUM,oil_filter,Oil Filter,total,9593,False,model_bucket_split,9584.9,6022.0,31664.97,0.6283,5.26,18734.6,True,model_bucket
2023,BELGIUM,fuel_filter,Fuel Filter,genuine,9593,False,model_bucket_split,9584.9,179.0,1893.19,0.0187,10.58,99481.53,True,model_bucket
2023,BELGIUM,fuel_filter,Fuel Filter,bvp,9593,False,model_bucket_split,9584.9,2846.0,20473.82,0.2969,7.19,48479.07,True,model_bucket
2023,BELGIUM,fuel_filter,Fuel Filter,total,9593,False,model_bucket_split,9584.9,3025.0,22367.01,0.3156,7.39,48504.4,True,model_bucket
2023,BELGIUM,air_filter,Air Filter,genuine,9593,False,model_bucket_split,4792.5,1411.0,26772.53,0.2944,18.97,64160.34,True,model_bucket
2023,BELGIUM,air_filter,Air Filter,bvp,9593,False,model_bucket_split,4792.5,120.0,2275.83,0.025,18.97,88614.38,True,model_bucket
2023,BELGIUM,air_filter,Air Filter,total,9593,False,model_bucket_split,4792.5,1531.0,29048.36,0.3195,18.97,61881.17,True,model_bucket
2023,BELGIUM,urea_filter,Urea (AdBlue) Filter,genuine,9593,False,model_bucket_split,9501.0,194.0,1998.97,0.0204,10.3,95898.88,True,model_bucket
2023,BELGIUM,urea_filter,Urea (AdBlue) Filter,bvp,9593,False,model_bucket_split,9501.0,0.0,0.0,0.0,0.0,0.0,False,model_bucket
2023,BELGIUM,urea_filter,Urea (AdBlue) Filter,total,9593,False,model_bucket_split,9501.0,194.0,1998.97,0.0204,10.3,95898.88,True,model_bucket
2023,BELGIUM,blower_filter,Blower Unit Filter,genuine,9593,False,model_bucket_split,9584.9,1079.0,13949.25,0.1126,12.93,109964.05,True,model_bucket
2023,BELGIUM,blower_filter,Blower Unit Filter,bvp,9593,False,model_bucket_split,9584.9,1083.0,17654.18,0.113,16.3,138591.35,True,model_bucket
2023,BELGIUM,blower_filter,Blower Unit Filter,total,9593,False,model_bucket_split,9584.9,2162.0,31603.43,0.2256,14.62,108505.9,True,model_bucket
2023,BELGIUM,brake_pad,Brake Pad,genuine,9593,False,model_bucket_split,3844.5,966.0,78337.94,0.2513,81.1,233429.24,True,model_bucket
2023,BELGIUM,brake_pad,Brake Pad,bvp,9593,False,model_bucket_split,3844.5,83.0,4428.16,0.0216,53.35,200678.89,True,model_bucket
2023,BELGIUM,brake_pad,Brake Pad,total,9593,False,model_bucket_split,3844.5,1049.0,82766.1,0.2729,78.9,220561.81,True,model_bucket
2023,BELGIUM,brake_shoe,Brake Shoe,genuine,9593,False,model_bucket_split,4792.5,299.0,12423.87,0.0624,41.55,186709.59,True,model_bucket
2023,BELGIUM,brake_shoe,Brake Shoe,bvp,9593,False,model_bucket_split,4792.5,49.0,1230.55,0.0102,25.11,119123.78,True,model_bucket
2023,BELGIUM,brake_shoe,Brake Shoe,total,9593,False,model_bucket_split,4792.5,348.0,13654.42,0.0726,39.24,174386.57,True,model_bucket
2023,BELGIUM,clutch_disc,Clutch Disc,genuine,9593,False,model_bucket_split,1917.0,111.0,13129.55,0.0579,118.28,213619.45,True,model_bucket
2023,BELGIUM,clutch_disc,Clutch Disc,bvp,9593,False,model_bucket_split,1917.0,144.0,8626.49,0.0751,59.91,106212.71,True,model_bucket
2023,BELGIUM,clutch_disc,Clutch Disc,total,9593,False,model_bucket_split,1917.0,255.0,21756.04,0.133,85.32,141796.83,True,model_bucket
2023,BELGIUM,clutch_pressure_plate,Clutch Pressure Plate,genuine,9593,False,model_bucket_split,1917.0,88.0,6037.7,0.0459,68.61,125487.01,True,model_bucket
2023,BELGIUM,clutch_pressure_plate,Clutch Pressure Plate,bvp,9593,False,model_bucket_split,1917.0,89.0,7492.39,0.0464,84.18,153887.3,True,model_bucket
2023,BELGIUM,clutch_pressure_plate,Clutch Pressure Plate,total,9593,False,model_bucket_split,1917.0,177.0,13530.09,0.0923,76.44,133006.45,True,model_bucket
2023,BELGIUM,clutch_kit,Clutch Kit,genuine,9593,False,model_bucket_split,1437.7,109.0,6400.02,0.0758,58.72,78017.89,True,model_bucket
2023,BELGIUM,clutch_kit,Clutch Kit,bvp,9593,False,model_bucket_split,1437.7,170.0,5671.57,0.1182,33.36,42294.5,True,model_bucket
2023,BELGIUM,clutch_kit,Clutch Kit,total,9593,False,model_bucket_split,1437.7,279.0,12071.59,0.1941,43.27,50135.52,True,model_bucket
2023,BELGIUM,release_bearing,Release Bearing,genuine,9593,False,model_bucket_split,1437.7,75.0,1969.54,0.0522,26.26,35786.23,True,model_bucket
2023,BELGIUM,release_bearing,Release Bearing,bvp,9593,False,model_bucket_split,1437.7,7.0,151.43,0.0049,21.63,30950.95,True,model_bucket
2023,BELGIUM,release_bearing,Release Bearing,total,9593,False,model_bucket_split,1437.7,82.0,2120.97,0.057,25.87,35066.83,True,model_bucket
2023,BELGIUM,pilot_bearing,Pilot Bearing,genuine,9593,False,model_bucket_split,958.5,35.0,108.71,0.0365,3.11,2868.37,True,model_bucket
2023,BELGIUM,pilot_bearing,Pilot Bearing,bvp,9593,False,model_bucket_split,958.5,0.0,0.0,0.0,0.0,0.0,False,model_bucket
2023,BELGIUM,pilot_bearing,Pilot Bearing,total,9593,False,model_bucket_split,958.5,35.0,108.71,0.0365,3.11,2868.37,True,model_bucket
2023,BELGIUM,clutch_booster,Clutch Booster,genuine,9593,False,model_bucket_split,958.5,0.0,0.0,0.0,0.0,0.0,False,model_bucket
2023,BELGIUM,clutch_booster,Clutch Booster,bvp,9593,False,model_bucket_split,958.5,0.0,0.0,0.0,0.0,0.0,False,model_bucket
2023,BELGIUM,clutch_booster,Clutch Booster,total,9593,False,model_bucket_split,958.5,0.0,0.0,0.0,0.0,0.0,False,model_bucket
2023,BELGIUM,brake_rotor,Brake Rotor,genuine,9593,False,model_bucket_split,2396.2,1125.0,65147.25,0.4695,57.91,73615.24,True,model_bucket
2023,BELGIUM,brake_rotor,Brake Rotor,bvp,9593,False,model_bucket_split,2396.2,0.0,0.0,0.0,0.0,0.0,False,model_bucket
2023,BELGIUM,brake_rotor,Brake Rotor,total,9593,False,model_bucket_split,2396.2,1125.0,65147.25,0.4695,57.91,73615.24,True,model_bucket
2023,CYPRUS,oil_filter,Oil Filter,genuine,2308,False,model_bucket_split,2211.9,964.0,5041.12,0.4358,5.23,6525.63,True,model_bucket
2023,CYPRUS,oil_filter,Oil Filter,bvp,2308,False,model_bucket_split,2211.9,395.0,2119.15,0.1786,5.36,9747.44,True,model_bucket
2023,CYPRUS,oil_filter,Oil Filter,total,2308,False,model_bucket_split,2211.9,1359.0,7160.27,0.6144,5.27,4493.63,True,model_bucket
2023,CYPRUS,fuel_filter,Fuel Filter,genuine,2308,False,model_bucket_split,2211.9,231.0,2488.27,0.1044,10.77,21337.5,True,model_bucket
2023,CYPRUS,fuel_filter,Fuel Filter,bvp,2308,False,model_bucket_split,2211.9,457.0,3155.32,0.2066,6.9,12116.43,True,model_bucket
2023,CYPRUS,fuel_filter,Fuel Filter,total,2308,False,model_bucket_split,2211.9,688.0,5643.59,0.311,8.2,12500.22,True,model_bucket
2023,CYPRUS,air_filter,Air Filter,genuine,2308,False,model_bucket_split,1105.9,440.0,6722.03,0.3979,15.28,10173.79,True,model_bucket
2023,CYPRUS,air_filter,Air Filter,bvp,2308,False,model_bucket_split,1105.9,65.0,1167.85,0.0588,17.97,18702.48,True,model_bucket
2023,CYPRUS,air_filter,Air Filter,total,2308,False,model_bucket_split,1105.9,505.0,7889.88,0.4566,15.62,9388.8,True,model_bucket
2023,CYPRUS,urea_filter,Urea (AdBlue) Filter,genuine,2308,False,model_bucket_split,2126.4,12.0,123.24,0.0056,10.27,21714.64,True,model_bucket
2023,CYPRUS,urea_filter,Urea (AdBlue) Filter,bvp,2308,False,model_bucket_split,2126.4,0.0,0.0,0.0,0.0,0.0,False,model_bucket
2023,CYPRUS,urea_filter,Urea (AdBlue) Filter,total,2308,False,model_bucket_split,2126.4,12.0,123.24,0.0056,10.27,21714.64,True,model_bucket
2023,CYPRUS,blower_filter,Blower Unit Filter,genuine,2308,False,model_bucket_split,2211.9,63.0,815.4,0.0285,12.94,27812.64,True,model_bucket
2023,CYPRUS,blower_filter,Blower Unit Filter,bvp,2308,False,model_bucket_split,2211.9,169.0,2785.33,0.0764,16.48,33669.19,True,model_bucket
2023,CYPRUS,blower_filter,Blower Unit Filter,total,2308,False,model_bucket_split,2211.9,232.0,3600.73,0.1049,15.52,30728.5,True,model_bucket
2023,CYPRUS,brake_pad,Brake Pad,genuine,2308,False,model_bucket_split,895.4,132.0,11015.89,0.1474,83.45,63711.88,True,model_bucket
2023,CYPRUS,brake_pad,Brake Pad,bvp,2308,False,model_bucket_split,895.4,157.0,7633.76,0.1753,48.62,35904.92,True,model_bucket
2023,CYPRUS,brake_pad,Brake Pad,total,2308,False,model_bucket_split,895.4,289.0,18649.65,0.3227,64.53,39134.56,True,model_bucket
```

## TABLE `mix_genuine_bvp_pms` — sample 60 of 1504 rows (full set in CSV)

```csv
year,distributor_code,product_group,product_subgroup,bvp_qty,genuine_qty,bvp_eur,genuine_eur,bvp_share_units,bvp_share_eur,total_qty,total_eur,product_group_label,prior_year,bvp_share_units_prior,bvp_share_eur_prior,total_qty_prior,genuine_qty_prior,bvp_share_units_yoy_pp,bvp_share_eur_yoy_pp,total_qty_yoy_pct,genuine_qty_yoy_pct,substitution_flag,product_family
2024,ARMENIA,brakes,brake_lining,4.0,0.0,235.8,0.0,1.0,1.0,4.0,235.8,Brakes,,,,,,,,,,False,brakes
2023,ARMENIA,brakes,brake_pad,3.0,10.0,81.17999999999999,1281.8,0.2307692307692307,0.0595606685351215,13.0,1362.98,Brakes,,,,,,,,,,False,brakes
2024,ARMENIA,brakes,brake_pad,20.0,5.0,1769.0,640.9,0.8,0.7340553549939831,25.0,2409.9,Brakes,2023.0,0.2307692307692307,0.0595606685351215,13.0,10.0,56.92307692307692,67.44946864588616,92.3076923076923,-50.0,False,brakes
2025,ARMENIA,brakes,brake_pad,39.0,2.0,2789.09,262.98,0.951219512195122,0.913835528018689,41.0,3052.07,Brakes,2024.0,0.8,0.7340553549939831,25.0,5.0,15.121951219512187,17.978017302470583,64.0,,False,brakes
2026,ARMENIA,brakes,brake_pad,20.0,0.0,1423.0,0.0,1.0,1.0,20.0,1423.0,Brakes,2025.0,0.951219512195122,0.913835528018689,41.0,2.0,4.878048780487809,8.616447198131105,-51.21951219512195,,False,brakes
2024,ARMENIA,brakes,brake_rotor,4.0,0.0,517.8,0.0,1.0,1.0,4.0,517.8,Brakes,,,,,,,,,,False,brakes
2023,ARMENIA,brakes,brake_shoe,1.0,120.0,41.0,18666.0,0.0082644628099173,0.0021916929491634,121.0,18707.0,Brakes,,,,,,,,,,False,brakes
2024,ARMENIA,brakes,brake_shoe,0.0,50.0,0.0,7777.5,0.0,0.0,50.0,7777.5,Brakes,2023.0,0.0082644628099173,0.0021916929491634,121.0,120.0,-0.8264462809917356,-0.2191692949163415,-58.67768595041323,-58.333333333333336,False,brakes
2025,ARMENIA,brakes,brake_shoe,15.0,258.0,615.3,40481.26,0.0549450549450549,0.0149720560553,273.0,41096.560000000005,Brakes,2024.0,0.0,0.0,50.0,50.0,5.494505494505495,1.4972056055300005,446.0,416.0,False,brakes
2026,ARMENIA,brakes,brake_shoe,5.0,30.0,205.1,4666.5,0.1428571428571428,0.0421011577305197,35.0,4871.6,Brakes,2025.0,0.0549450549450549,0.0149720560553,273.0,258.0,8.79120879120879,2.7129101675219736,-87.17948717948718,-88.37209302325581,False,brakes
2023,ARMENIA,clutch,clutch_kit,83.0,1.0,5618.41,133.68,0.988095238095238,0.9767597516728702,84.0,5752.09,Clutch & driveline,,,,,,,,,,False,clutch
2024,ARMENIA,clutch,clutch_kit,102.0,0.0,4968.37,0.0,1.0,1.0,102.0,4968.37,Clutch & driveline,2023.0,0.988095238095238,0.9767597516728702,84.0,1.0,1.1904761904761862,2.3240248327129787,21.428571428571427,,False,clutch
2025,ARMENIA,clutch,clutch_kit,257.0,11.0,16330.27,506.0,0.9589552238805972,0.9699458371717726,268.0,16836.27,Clutch & driveline,2024.0,1.0,1.0,102.0,0.0,-4.104477611940293,-3.005416282822737,162.7450980392157,,False,clutch
2026,ARMENIA,clutch,clutch_kit,34.0,17.0,1680.44,659.09,0.6666666666666666,0.7182810222566071,51.0,2339.53,Clutch & driveline,2025.0,0.9589552238805972,0.9699458371717726,268.0,11.0,-29.22885572139304,-25.16648149151656,-80.97014925373134,54.54545454545454,False,clutch
2025,ARMENIA,electrical,starter,4.0,0.0,952.08,0.0,1.0,1.0,4.0,952.08,Electrical,,,,,,,,,,False,electrical
2026,ARMENIA,electrical,starter,2.0,0.0,476.04,0.0,1.0,1.0,2.0,476.04,Electrical,2025.0,1.0,1.0,4.0,0.0,0.0,0.0,,,False,electrical
2023,ARMENIA,engine_cooling,fan_belt,159.0,6.0,912.92,59.61,0.9636363636363636,0.9387062609893784,165.0,972.53,Engine & cooling,,,,,,,,,,False,engine_cooling
2024,ARMENIA,engine_cooling,fan_belt,150.0,0.0,870.0,0.0,1.0,1.0,150.0,870.0,Engine & cooling,2023.0,0.9636363636363636,0.9387062609893784,165.0,6.0,3.6363636363636376,6.1293739010621735,-9.090909090909092,,False,engine_cooling
2025,ARMENIA,engine_cooling,fan_belt,362.0,0.0,2116.03,0.0,1.0,1.0,362.0,2116.03,Engine & cooling,2024.0,1.0,1.0,150.0,0.0,0.0,0.0,141.33333333333334,,False,engine_cooling
2026,ARMENIA,engine_cooling,fan_belt,9.0,0.0,52.2,0.0,1.0,1.0,9.0,52.2,Engine & cooling,2025.0,1.0,1.0,362.0,0.0,0.0,0.0,-97.51381215469614,,False,engine_cooling
2025,ARMENIA,engine_cooling,water_pump,0.0,1.0,0.0,128.07,0.0,0.0,1.0,128.07,Engine & cooling,,,,,,,,,,False,engine_cooling
2023,ARMENIA,filters,air_filter,13.0,46.0,396.67,1934.1,0.2203389830508474,0.1701883926770981,59.0,2330.77,Filters,,,,,,,,,,False,filters
2024,ARMENIA,filters,air_filter,80.0,0.0,2030.4,0.0,1.0,1.0,80.0,2030.4,Filters,2023.0,0.2203389830508474,0.1701883926770981,59.0,46.0,77.96610169491525,82.98116073229018,35.59322033898305,-100.0,False,filters
2025,ARMENIA,filters,air_filter,455.0,0.0,11501.3,0.0,1.0,1.0,455.0,11501.3,Filters,2024.0,1.0,1.0,80.0,0.0,0.0,0.0,468.75,,False,filters
2026,ARMENIA,filters,air_filter,172.0,0.0,4550.860000000001,0.0,1.0,1.0,172.0,4550.860000000001,Filters,2025.0,1.0,1.0,455.0,0.0,0.0,0.0,-62.1978021978022,,False,filters
2023,ARMENIA,filters,blower_filter,0.0,59.0,0.0,1358.18,0.0,0.0,59.0,1358.18,Filters,,,,,,,,,,False,filters
2025,ARMENIA,filters,blower_filter,0.0,37.0,0.0,785.33,0.0,0.0,37.0,785.33,Filters,2023.0,0.0,0.0,59.0,59.0,0.0,0.0,-37.28813559322034,-37.28813559322034,False,filters
2026,ARMENIA,filters,blower_filter,0.0,30.0,0.0,644.8,0.0,0.0,30.0,644.8,Filters,2025.0,0.0,0.0,37.0,37.0,0.0,0.0,-18.91891891891892,-18.91891891891892,False,filters
2023,ARMENIA,filters,fuel_filter,335.0,0.0,4502.25,0.0,1.0,1.0,335.0,4502.25,Filters,,,,,,,,,,False,filters
2024,ARMENIA,filters,fuel_filter,220.0,71.0,2477.3,683.51,0.7560137457044673,0.7837547970298752,291.0,3160.8100000000004,Filters,2023.0,1.0,1.0,335.0,0.0,-24.398625429553267,-21.624520297012484,-13.134328358208954,,False,filters
2025,ARMENIA,filters,fuel_filter,790.0,90.0,9952.0,858.6,0.8977272727272727,0.9205779512700496,880.0,10810.6,Filters,2024.0,0.7560137457044673,0.7837547970298752,291.0,71.0,14.171352702280537,13.682315424017457,202.40549828178692,26.76056338028169,False,filters
2026,ARMENIA,filters,fuel_filter,150.0,0.0,2053.5,0.0,1.0,1.0,150.0,2053.5,Filters,2025.0,0.8977272727272727,0.9205779512700496,880.0,90.0,10.22727272727273,7.942204872995029,-82.95454545454545,-100.0,False,filters
2023,ARMENIA,filters,oil_filter,507.0,225.0,4690.88,3814.16,0.6926229508196722,0.5515412038038622,732.0,8505.04,Filters,,,,,,,,,,False,filters
2024,ARMENIA,filters,oil_filter,648.0,0.0,6644.72,0.0,1.0,1.0,648.0,6644.72,Filters,2023.0,0.6926229508196722,0.5515412038038622,732.0,225.0,30.737704918032783,44.84587961961378,-11.475409836065571,-100.0,False,filters
2025,ARMENIA,filters,oil_filter,1700.0,0.0,16697.600000000002,0.0,1.0,1.0,1700.0,16697.600000000002,Filters,2024.0,1.0,1.0,648.0,0.0,0.0,0.0,162.3456790123457,,False,filters
2026,ARMENIA,filters,oil_filter,260.0,0.0,2676.0,0.0,1.0,1.0,260.0,2676.0,Filters,2025.0,1.0,1.0,1700.0,0.0,0.0,0.0,-84.70588235294117,,False,filters
2023,ARMENIA,suspension,bushing,0.0,2.0,0.0,17.24,0.0,0.0,2.0,17.24,Suspension & chassis,,,,,,,,,,False,suspension
2026,ARMENIA,suspension,bushing,0.0,20.0,0.0,35.0,0.0,0.0,20.0,35.0,Suspension & chassis,2023.0,0.0,0.0,2.0,2.0,0.0,0.0,,,False,suspension
2025,ARMENIA,suspension,center_bearing,2.0,0.0,68.4,0.0,1.0,1.0,2.0,68.4,Suspension & chassis,,,,,,,,,,False,suspension
2023,ARMENIA,suspension,hub_bearing,0.0,1.0,0.0,16.37,0.0,0.0,1.0,16.37,Suspension & chassis,,,,,,,,,,False,suspension
2023,ARMENIA,suspension,hub_oil_seal,0.0,170.0,0.0,957.1,0.0,0.0,170.0,957.1,Suspension & chassis,,,,,,,,,,False,suspension
2024,ARMENIA,suspension,hub_oil_seal,20.0,0.0,75.2,0.0,1.0,1.0,20.0,75.2,Suspension & chassis,2023.0,0.0,0.0,170.0,170.0,100.0,100.0,-88.23529411764706,-100.0,False,suspension
2023,ARMENIA,suspension,king_pin,0.0,6.0,0.0,686.58,0.0,0.0,6.0,686.58,Suspension & chassis,,,,,,,,,,False,suspension
2024,ARMENIA,suspension,king_pin,2.0,8.0,123.08,915.44,0.2,0.1185148095366483,10.0,1038.52,Suspension & chassis,2023.0,0.0,0.0,6.0,6.0,20.0,11.851480953664831,,,False,suspension
2025,ARMENIA,suspension,king_pin,0.0,10.0,0.0,1144.3,0.0,0.0,10.0,1144.3,Suspension & chassis,2024.0,0.2,0.1185148095366483,10.0,8.0,-20.0,-11.851480953664831,0.0,,False,suspension
2023,ARMENIA,suspension,shock_absorber,110.0,8.0,2403.5,454.88,0.9322033898305084,0.8408609072271706,118.0,2858.38,Suspension & chassis,,,,,,,,,,False,suspension
2024,ARMENIA,suspension,shock_absorber,42.0,0.0,922.46,0.0,1.0,1.0,42.0,922.46,Suspension & chassis,2023.0,0.9322033898305084,0.8408609072271706,118.0,8.0,6.779661016949157,15.913909277282944,-64.40677966101694,,False,suspension
2025,ARMENIA,suspension,shock_absorber,136.0,0.0,2977.92,0.0,1.0,1.0,136.0,2977.92,Suspension & chassis,2024.0,1.0,1.0,42.0,0.0,0.0,0.0,223.80952380952385,,False,suspension
2026,ARMENIA,suspension,shock_absorber,20.0,0.0,437.0,0.0,1.0,1.0,20.0,437.0,Suspension & chassis,2025.0,1.0,1.0,136.0,0.0,0.0,0.0,-85.29411764705883,,False,suspension
2023,ARMENIA,suspension,wheel_pin,0.0,212.0,0.0,512.24,0.0,0.0,212.0,512.24,Suspension & chassis,,,,,,,,,,False,suspension
2025,ARMENIA,suspension,wheel_pin,0.0,60.0,0.0,123.3,0.0,0.0,60.0,123.3,Suspension & chassis,2023.0,0.0,0.0,212.0,212.0,0.0,0.0,-71.69811320754717,-71.69811320754717,False,suspension
2026,ARMENIA,suspension,wheel_pin,0.0,110.0,0.0,224.9,0.0,0.0,110.0,224.9,Suspension & chassis,2025.0,0.0,0.0,60.0,60.0,0.0,0.0,83.33333333333334,83.33333333333334,False,suspension
2023,BELGIUM,brakes,brake_lining,0.0,1.0,0.0,91.53,0.0,0.0,1.0,91.53,Brakes,,,,,,,,,,False,brakes
2024,BELGIUM,brakes,brake_lining,1.0,1.0,61.49,90.55,0.5,0.4044330439358064,2.0,152.04,Brakes,2023.0,0.0,0.0,1.0,1.0,50.0,40.44330439358064,,,False,brakes
2025,BELGIUM,brakes,brake_lining,68.0,0.0,3907.96,0.0,1.0,1.0,68.0,3907.96,Brakes,2024.0,0.5,0.4044330439358064,2.0,1.0,50.0,59.55669560641936,,,False,brakes
2023,BELGIUM,brakes,brake_pad,83.0,465.0,4428.16,41178.28,0.1514598540145985,0.0970950593819644,548.0,45606.44,Brakes,,,,,,,,,,False,brakes
2024,BELGIUM,brakes,brake_pad,392.0,346.0,20596.5,29900.52,0.5311653116531165,0.4078755538445635,738.0,50497.02,Brakes,2023.0,0.1514598540145985,0.0970950593819644,548.0,465.0,37.9705457638518,31.078049446259904,34.67153284671533,-25.591397849462368,False,brakes
2025,BELGIUM,brakes,brake_pad,377.0,189.0,21104.14,16218.17,0.666077738515901,0.5654564253927477,566.0,37322.31,Brakes,2024.0,0.5311653116531165,0.4078755538445635,738.0,346.0,13.491242686278447,15.758087154818416,-23.306233062330623,-45.3757225433526,False,brakes
2026,BELGIUM,brakes,brake_pad,125.0,64.0,7133.88,5439.28,0.6613756613756614,0.5673895822529897,189.0,12573.16,Brakes,2025.0,0.666077738515901,0.5654564253927477,566.0,189.0,-0.4702077140239624,0.1933156860242091,-66.6077738515901,-66.13756613756614,False,brakes
2024,BELGIUM,brakes,brake_rotor,0.0,2.0,0.0,298.12,0.0,0.0,2.0,298.12,Brakes,,,,,,,,,,False,brakes
```
