# ISZE analyst brief — 2026-06-10

## TL;DR
- 2 defection alert(s) with >EUR10K trailing revenue


## Status
- Pipeline verify: **96 pass / 0 fail** (2026-06-04T16:15:03Z)
- FACTS drift check: **ALIGNED**

## Input freshness
- CY2025 billing: 26d old
- UIO workbook: 51d old
- sales_fact.parquet: 18d old
- gpt_safe export: 0d old
- Sales data horizon: **2025-12** (alerts are relative to this, not today)

## Defection alerts (19)
- [distributor] **ITUK** / brake_pad: silent 3m (median gap 1.0m, last 2025-09, trailing-12m EUR36,631)
- [distributor] **PORTUGAL** / brake_pad: silent 4m (median gap 1.0m, last 2025-08, trailing-12m EUR16,502)
- [distributor] **UKRAINE** / air_filter: silent 9m (median gap 2.0m, last 2025-03, trailing-12m EUR8,718)
- [distributor] **UTI** / clutch_disc: silent 2m (median gap 1.0m, last 2025-10, trailing-12m EUR3,521)
- [distributor] **GERMANY** / clutch_pressure_plate: silent 4m (median gap 1.0m, last 2025-08, trailing-12m EUR2,488)
- [distributor] **UMI** / clutch_kit: silent 8m (median gap 4.0m, last 2025-04, trailing-12m EUR996)
- [distributor] **FINLAND** / brake_shoe: silent 4m (median gap 2.0m, last 2025-08, trailing-12m EUR551)
- [distributor] **GERMANY** / clutch_disc: silent 11m (median gap 1.0m, last 2025-01, trailing-12m EUR485)

## ITUK dealer leakage (benchmark gap EUR79,755)
- MOTUS GROUP UK LTD: EUR9,726
- SAPPHIRE VEHICLE SERVICES LIMITED: EUR5,959
- FERNDOWN COMMERCIALS LTD: EUR5,277
- HARRY MOORE COMMERCIALS LTD: EUR3,615
- SW COMMERCIALS LTD: EUR3,016

## Model headlines
- Network GPS CY2025 (waterfall identity): **40.2**
- Network wallet ceiling CY2025 (EUR): **75,149,582.0**
- Network wallet 2030, age-flat (EUR): **90,055,968.0**
- ITUK dealer benchmark gap (EUR): **79,755.0**
- Elasticity: 18 categories show negative price response (adequate n; LOW POWER — direction only)
