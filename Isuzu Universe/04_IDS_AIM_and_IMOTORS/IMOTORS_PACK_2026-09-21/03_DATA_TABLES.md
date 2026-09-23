# Data tables — Imotors (Portugal)

Every table here is an aggregate. No line-level billing, no customer names.
`source` is the file the table was read from; nothing was recalculated beyond the arithmetic stated in the note.

## TABLE `portugal_dealer_dimension`  (16 rows)

*One row per dealer: 2026 dealer-standards score and its five section scores, city, address, coordinates, the date ISZE visited and how many vehicles the workshop sees a month. The score is the dealer's own self-assessment; the IMG/ISZE block of the same scorecard is zero on all 16 sheets, so there is no independent assessment to compare it with.*

```csv
ids_rank,dealer,ids_score_pct,points_scored,points_max,ids_band,A_Premises_facility_clothing,B_Organisation_management_personnel,C_Service,D_Parts_and_accessories,E_Vehicle_sales,ids_score_pct_summary,place,address,lat,lon,evaluation_date,vehicles_serviced_per_month,other_brands_serviced,models_available,evaluator
1,AMATOSCAR EVORA,99.29,278,280,Good,100.0,97.5,100.0,100.0,100.0,99.29,Évora,,38.5667,-7.9,2026-04-27,44.0,,"D-Max, N-Series, F-Series",Diogo Fona
2,AUTO RENO MINHO POVOA,96.07,269,280,Good,95.7,97.5,92.5,97.9,100.0,96.43,Póvoa de Varzim,"R. de São Brás 269 - 4490-455 Póvoa de Varzim
",41.3833,-8.7667,2026-04-13,6.0,Opel | Peugoet | Citroen | Leapmotor,"D-Max, N-Series, F-Series",Nuno Botelho
2,AUTO RENO PAÇOS FERREIRA,96.07,269,280,Good,95.7,97.5,92.5,97.9,100.0,96.43,Paços de Ferreira,"R. da Estrada 387, 4590-778 Paços de Ferreira",41.276,-8.376,2026-04-07,,Opel | Peugoet | Citroen | Leapmotor| Maxus | Mitsubishi | Piaggio | FUSO,"D-Max, N-Series, F-Series",Manuel Ribeiro
2,AUTO RENO MINHO VIANA,96.07,269,280,Good,95.7,97.5,92.5,97.9,100.0,96.43,Viana do Castelo,"Zona Industrial 1ª Fase, Rua Abilio Peixoto, nº 596 - 4935-231 Viana Do Castelo",41.6918,-8.8344,2026-04-13,15.0,Opel | Peugoet | Citren | Fiat | JEEP | Leapmotor,"D-Max, N-Series, F-Series",Nuno Botelho
5,AUTO RENO PENAFIEL,94.29,264,280,Good,84.8,97.5,92.5,97.9,100.0,94.29,Penafiel,"Rua Zona Industrial Nº2, 4560-323 Penafiel",41.208,-8.282,2026-04-07,,Opel | Peugoet | Citroen | Leapmotor,"D-Max, N-Series, F-Series",Manuel Ribeiro
6,AMATOSCAR PORTALEGRE,92.5,259,280,Good,89.1,91.2,93.8,95.7,92.6,92.86,Portalegre,AV. FRANCISCO FINO N.º 35 ,39.2938,-7.4312,2026-04-15,25.0,"Opel, Fiat, Citroen, Peugeot, Nissan, Hyundai, Seat","D-Max, N-Series, F-Series",Filipe Fernandes
7,ROLMAX,90.71,254,280,Good,87.0,95.0,85.0,93.6,96.3,90.71,Vila Nova de Gaia,Rua Doutor Ribeiro Magalhaes Nº168  4400-073 Candal Vila Nova de Gaia,41.1239,-8.6118,2026-04-29,150.0,Mitsubishi  /  Fuso / Maxus / Piaggio,"D-Max, N-Series, F-Series",Rui Matos
7,AUTO INDUSTRIAL LEIRIA,90.71,254,280,Good,84.8,87.5,95.0,89.4,100.0,91.43,Leiria,"Rua do Alto Vieiro, Estrada Nacional 1, 2400-822 Leiria",39.7436,-8.8071,2026-04-28,20.0,"Opel, Citroen, Fiat, Changan, Forthing, BMW, Mini, Maxus, Lancia, Peugeot","D-Max, N-Series, F-Series",Contacto do Concessionário e Função
9,AUTO IMPERIAL,86.43,242,280,Good,84.8,88.8,88.8,85.1,77.8,86.43,Bragança,"Avenida das Cantarias, 130, 5300-107 Bragança",41.8061,-6.7567,2026-04-13,,"Toyota, Hyundai, Xpeng, DongFeng, Farizon, Voyhan","D-Max, N-Series, F-Series",Daniel Vicente
10,SOCARROS CALDAS,82.14,230,280,Good,78.3,83.8,87.5,78.7,74.1,82.5,Caldas da Rainha,"Rua Mártires de Timor, Nº 25 
2500-839 Caldas da Rainha",39.407,-9.135,2026-04-30,432.0,Peugeot/Ford/Kia,"D-Max, N-Series, F-Series",João Oliveira
11,ASTARA RETAIL LISBOA,78.57,220,280,Medium,76.1,82.5,80.0,80.9,63.0,78.93,Lisboa,Rua José Espirito Santo 38 - 1950-097 Lisboa,38.7223,-9.1393,2026-04-24,8.0,"Mitsubishi, Aiways, Fuso, KIA, Suzuki, Maxus, Piaggio, KGM","D-Max, N-Series, F-Series",Paulo Oliveira
12,MSCAR,77.86,218,280,Medium,71.7,76.2,83.8,85.1,63.0,77.86,Almancil,"N125 Km 97,3, 8001-904 Faro",37.087,-8.0307,2026-03-31,110.0,Iveco; Maxus; Piaggio,"D-Max, N-Series, F-Series",Pedro Arez
12,SOTERMÁQUINAS,77.86,218,280,Medium,78.3,76.2,80.0,83.0,66.7,77.86,Angra do Heroísmo,"Canada Nova, Santa Luzia -S/N 9700-130 Angra do Heroísmo",38.6593,-27.2194,2026-04-28,20.0,"Opel, Peugeot, Mercedes","D-Max, N-Series, F-Series",Sidónio Gonçalves
12,XANAUTO,77.86,218,280,Medium,76.1,65.0,85.0,80.9,92.6,77.86,Loures,,38.8309,-9.1681,,,,"D-Max, N-Series, F-Series",Contacto do Concessionário e Função
15,ASTARA RETAIL CASCAIS,76.43,214,280,Medium,69.6,81.2,78.8,78.7,63.0,76.79,Cascais,Rua S. João 8 - 2645-303 Alcabideche,38.6979,-9.4215,2026-04-24,12.0,"Mitsubishi, Aiways, Fuso, KIA, Suzuki, Maxus, Piaggio, KGM","D-Max, N-Series, F-Series",Paulo Oliveira
16,AMATOSCAR BEJA,74.64,209,280,Medium,54.3,72.5,81.2,74.5,96.3,74.64,Beja,"Rua da Ciência Lote 2/4, 7800-010 Beja",38.0151,-7.8632,2026-03-31,,Hyundai | Kia,"D-Max, N-Series, F-Series",Contacto do Concessionário e Função
```

## TABLE `portugal_checklist_areas`  (13 rows)

*The same 16 dealers read by checklist subcategory, weakest first. Taken from the self-assessment block; the IMG/ISZE block is zero throughout.*

```csv
checklist_subcategory,dealers_scored,avg_pct,weakest_dealer_pct,strongest_dealer_pct,avg_items_scored_pct
B.3 Education,16,78.125,25.0,100.0,81.25
A.3 Uniforms,16,78.90625,37.5,112.5,89.0625
A.2 Stationary / Publications,16,83.33375,50.0,100.0,81.25
B.5 Environment / Workshop - 5S,16,84.61625000000001,69.23,100.0,86.365
E.2 Marketing,16,86.25,40.0,120.0,94.79125
C.4 Service Shop Operation,16,87.30562499999999,75.0,100.0,93.46375
B.2 Organization,16,87.499375,66.67,100.0,98.86375
B.7 Self-evaluation of Dealer Standards,16,87.5,0.0,100.0,87.5
D.2 Operation and Management,16,88.09375,71.43,104.76,94.48625
B.4 Compliance with Laws,16,89.205625,63.64,100.0,96.09375
C.2 Facility for Employees,16,91.6675,66.67,100.0,91.6675
B.6 Customer Handling,16,93.27125,84.62,100.0,95.0
C.3 Administration,16,95.1375,77.78,100.0,96.875
```

## TABLE `portugal_billing_and_fleet`  (4 rows)

*ISZE billing Portugal, the fleet denominator used, the target spend and the resulting capture.*

```csv
year,total_sales_eur,warranty_parts_eur,sales_ex_warranty_eur,uio_units,spend_per_unit_eur,spend_per_unit_ex_warranty_eur,max_spend_eur,gps_capture_vs_max,gps_capture_ex_warranty_vs_max,uio_source
2023,1363632.82,,,6091.0,223.8766737809884,,,,,v18_actual
2024,1536813.75,,,6903.0,222.62983485441111,,,,,v18_actual
2025,1709793.99,130588.0,1579205.99,8176.0,209.12,193.15,3494069.0,0.4893,0.452,v18_actual
2026,1205888.02,,,8444.0,142.81004500236855,,4093046.0,0.2946,,v18_actual
```

## TABLE `network_billing_and_fleet_2025`  (18 rows)

*Every distributor with a 2025 full-year row, so Portugal can be read against the network.*

```csv
distributor_code,country,total_sales_eur,uio_units,spend_per_unit_eur,max_spend_eur,gps_capture_vs_max
FINLAND,Finland,277920.61,1204.0,230.83,301000.0,0.9233
BELGIUM,Belgium,2109331.62,9594.0,219.86,2454394.0,0.8594
IRELAND,Ireland,1187458.62,3056.0,388.57,1391176.0,0.8536
ICELAND,Iceland,85281.57,406.0,210.05,101500.0,0.8402
GERMANY,Germany,2535931.82,12855.0,197.27,3412284.0,0.7432
UMI,Israel,3319344.16,18542.0,179.02,4635500.0,0.7161
NORWAY,Norway,1416551.93,7929.0,178.65,1982250.0,0.7146
DENMARK,Denmark,148220.51,851.0,174.17,213239.0,0.6951
ROMANIA,Romania,175218.43,1071.0,163.6,267750.0,0.6544
CYPRUS,Cyprus,428443.11,2308.0,185.63,676267.0,0.6335
SWEDEN,Sweden,1278462.18,8443.0,151.42,2110750.0,0.6057
GREECE,Greece,520303.94,3742.0,139.04,953593.0,0.5456
MALTA,Malta,206502.27,1040.0,198.56,378827.0,0.5451
IUK,United Kingdom,6131920.41,47783.0,128.33,11945750.0,0.5133
PORTUGAL,Portugal,1709793.99,8176.0,209.12,3494069.0,0.4893
ITUK,United Kingdom,5564543.92,22389.0,248.54,11835911.0,0.4701
UTI,Israel,3331511.94,10336.0,322.32,8271300.0,0.4028
HUNGARY,Hungary,330030.58,3734.0,88.39,933500.0,0.3535
```

## TABLE `portugal_sales_to_dealer_by_family_2025`  (30 rows)

*What Imotors passed on to its dealers in CY2025, valued at ISZE's own billed prices, split by service family.*

```csv
pms_category,units,eur_total,bvp_eur,contested_genuine_eur,genuine_only_eur,bvp_share_pct,eur_per_unit
(unclassified),36761.0,1167261.83,0.0,0.0,1167261.83,0.0,31.75
brake_pad,980.0,61815.630000000005,3936.06,7171.02,50708.55,6.4,63.08
fuel_filter,3074.0,27164.18,18705.37,204.07,8254.74,68.9,8.84
brake_rotor,431.0,26676.815000000002,0.0,1412.9,25263.915,0.0,61.9
clutch_kit,386.0,25364.81,24485.36,848.33,31.12,96.5,65.71
air_filter,1273.0,24348.04,8704.07,11057.429999999998,4586.539999999999,35.7,19.13
clutch_disc,187.0,19354.6,353.64,111.7,18889.26,1.8,103.5
oil_filter,3652.0,17429.449999999997,9452.15,80.5,7896.799999999998,54.2,4.77
blower_filter,1396.0,15774.28,15774.28,0.0,0.0,100.0,11.3
leaf_spring,250.0,12176.625,0.0,0.0,12176.625,0.0,48.71
brake_shoe,397.0,10697.740000000002,0.0,4920.87,5776.870000000001,0.0,26.95
clutch_pressure_plate,105.0,10244.62,0.0,1704.78,8539.84,0.0,97.57
shock_absorber,223.0,4835.81,1974.15,1079.02,1782.64,40.8,21.69
wiper_blade,270.0,2730.605,317.81,0.0,2412.795,11.6,10.11
starter,12.0,2029.32,2029.32,0.0,0.0,100.0,169.11
hub_bearing,159.0,1586.65,1234.91,351.74,0.0,77.8,9.98
king_pin,41.0,1525.3000000000002,818.0,707.3000000000001,0.0,53.6,37.2
fan_belt,194.0,1346.05,524.79,0.0,821.26,39.0,6.94
water_pump,32.0,1143.245,604.29,0.0,538.9549999999999,52.9,35.73
wheel_pin,792.0,1007.075,0.0,1007.075,0.0,0.0,1.27
release_bearing,62.0,1002.07,1002.07,0.0,0.0,100.0,16.16
clutch_booster,5.0,958.3,0.0,0.0,958.3,0.0,191.66
bushing,539.0,839.7900000000001,192.68,267.3,379.81000000000006,22.9,1.56
urea_filter,80.0,829.07,0.0,0.0,829.07,0.0,10.36
engine_mount,18.0,494.02,164.57,329.45,0.0,33.3,27.45
generator,1.0,251.26,251.26,0.0,0.0,100.0,251.26
brake_lining,4.0,128.9,40.28,88.62,0.0,31.2,32.22
center_bearing,3.0,74.56,25.03,49.53,0.0,33.6,24.85
hub_oil_seal,23.0,60.86,0.0,60.86,0.0,0.0,2.65
pilot_bearing,13.0,36.6,0.0,36.6,0.0,0.0,2.82
```

## TABLE `portugal_light_vehicle_share`  (1 rows)

*The measured N-series light share for Portugal and its basis.*

```csv
distributor_code,market,n35_share,basis,units_2025e,evidence_note
PORTUGAL,Portugal,0.6364,imotors_parc_bands,2206,"Confirmed. Official I-Motors registrations (01_data/07_UIO/Matriculas Isuzu SAP.xlsx) convolved with the UIO V19 survival curve in 01_data/08_Distributor/Imotors_Portugal_UIO_GPS_PMS_Study.xlsx sheet UIO_Rebuild. 2025 N-series parc: N35 1,521.31 + N75/N50/N62 869.00 = 2,390.31; light share 1,521.31/2,390.31 = 0.6364. (2024 = 0.6386.) Replaces the 2026-09-18 JP shipment mix 0.6899 (NLR 1,299/1,883). units_2025e stays the workbook LD row (2,206); the study rebuilt stock is 2,390 — fleet-base swap is a separate decision."
```

## TABLE `portugal_sales_to_dealer_headline`  (1 rows)

*The single Portugal row of the sales-to-dealer layer.*

```csv
entity,layer,year,bvp_eur,genuine_contested_eur,genuine_only_eur,bvp_pct,qty_year,qty_unvalued_share,uio_units,sellout_spu_eur,total_eur
PORTUGAL (network aggregate),sellout_db_dlr,2025,90590.09,31489.095,1317108.92,0.0629452742732333,51363.0,0.0819072094698518,8176.0,176.0259423923679,1439188.105
```
