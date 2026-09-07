# GPS / PMS V2 shadow — findings

**Built:** 2026-09-06 · Mode B shadow · V1 untouched

## Mileage layer (LCV)

DBs with LCV km mapped: **16**

| DB | km/yr | VIN n | svc/yr LCV |
|----|------:|------:|-----------:|
| UMI | 34443 | 13611 | 1.722 |
| IRELAND | 27998 | 426 | 1.400 |
| SWEDEN | 26670 | 3378 | 1.333 |
| HUNGARY | 26334 | 1250 | 1.317 |
| FINLAND | 24811 | 376 | 1.241 |
| ROMANIA | 24726 | 248 | 1.236 |
| IUK | 24481 | 29646 | 1.224 |
| BELGIUM | 23348 | 2610 | 1.167 |

## Cohorts

VIN age intensity available for **7** DBs; others intensity=1.0.
SCR cutoffs: **still need** from IMIT (15k vs 20k not applied).

## Solo progress (2026-09-05)

- **Ireland Opt2:** ON — SIMI Trooper vs D-Max aggregate (RT/RG not separable; D-Max on RT col, RG=0). Trooper UIO≈3.4, D-Max/RT≈1334.6.
- **Portugal Opt3:** ON — share_age_le_10=**0.6201** (Matriculas preferred over VIN). Source: `Matriculas_SUM_LCV_age_le10_prefer_over_VIN`.
- **Opt2 enabled DBs:** IRELAND, PORTUGAL.
- **Opt1 sensitivity:** `pms_v2_lcv_opt1_sensitivity.csv` — method `db_annual_km_pm20pct` (±20% DB km); mid = current Opt1. Network km P25/mean/P75 context: 20709.0 / 23042.9 / 25192.1.

## EQ-HIT fitment overlay (seed extract → V2 weights)

- Extract SSOT: `eqhit_extract_priority_cy2025.csv` wired into `pms_v2_fitment_weights.csv`.
- Extract-backed categories: **blower_filter, brake_pad, brake_rotor, brake_shoe, clutch_disc, clutch_pressure_plate, fuel_filter**.
- Oil: **skipped** — Opt1 oil lens stays BVP (`eq_hit_status=skipped_oil_filter`).
- Scope caveat: weights = **seed-PN applicability** (37 PNs / 2311 rows), not full catalogue.
- **BVP → EQ-HIT weight flips** (bucket binary changed):
  - `brake_pad` / `cv_std`: BVP=0.0 → EQ-HIT=1.0 (rows=320)
  - `brake_pad` / `lcv`: BVP=1.0 → EQ-HIT=0.0 (rows=0)
  - `brake_rotor` / `cv_std`: BVP=0.0 → EQ-HIT=1.0 (rows=226)
  - `brake_rotor` / `lcv`: BVP=0.0 → EQ-HIT=1.0 (rows=109)
  - `brake_shoe` / `lcv`: BVP=1.0 → EQ-HIT=0.0 (rows=0)
- Coverage detail: `pms_v2_eqhit_fitment_coverage.csv`.

## Contested capture — EQ-HIT categories CY2025 (total)

| Category | capture V2 | EUR gap | LCV fitment | Lowest capture DBs |
|----------|-----------:|--------:|:-----------:|--------------------|
| clutch_disc | 0.0461 | 3836542 | 1.0 | NORWAY:0.000;SWEDEN:0.002;HUNGARY:0.007 |
| clutch_pressure_plate | 0.0528 | 2367266 | 1.0 | NORWAY:0.001;SWEDEN:0.001;HUNGARY:0.009 |
| blower_filter | 0.1576 | 1815168 | 1.0 | UMI:0.004;IRELAND:0.105;GERMANY:0.137 |
| brake_rotor | 0.4525 | 1710147 | 1.0 | UMI:0.070;UTI:0.093;ROMANIA:0.166 |
| fuel_filter | 0.3851 | 1162095 | 1.0 | IUK:0.131;HUNGARY:0.143;FINLAND:0.147 |
| brake_shoe | 0.5409 | 305944 | 0.0 | ITUK:0.101;UTI:0.309;PORTUGAL:0.616 |
| brake_pad | 1.4029 | 291500 | 0.0 | UTI:0.070;ITUK:0.614;MALTA:1.648 |

## Oil filter CY2025 — V1 vs V2 capture (total)

| DB | capture V1 | capture V2 | expected V1 | expected V2 |
|----|-----------:|-----------:|------------:|------------:|
| BELGIUM | 0.6262 | 0.5158 | 9536.5 | 11577.29 |
| CYPRUS | 0.9123 | 0.9319 | 2206.5 | 2160.12 |
| DENMARK | 0.495 | 0.4411 | 850.5 | 954.37 |
| FINLAND | 0.7824 | 0.6307 | 1204.0 | 1493.68 |
| GERMANY | 0.1513 | 0.1627 | 13414.0 | 12468.88 |
| GREECE | 0.9717 | 0.9327 | 3723.5 | 3878.87 |
| HUNGARY | 0.4502 | 0.3419 | 3734.0 | 4916.56 |
| ICELAND | 0.7069 | 0.6785 | 406.0 | 422.97 |
| IRELAND | 1.9056 | 1.4014 | 1764.8 | 2399.72 |
| ITUK | 1.1643 | 1.1643 | 11680.2 | 11680.16 |
| IUK | 0.3774 | 0.3083 | 47783.0 | 58491.17 |
| MALTA | 0.9047 | 1.3439 | 918.5 | 618.34 |
| NORWAY | 0.478 | 0.4472 | 7929.0 | 8474.52 |
| PORTUGAL | 0.5212 | 0.4499 | 6015.3 | 6967.46 |
| ROMANIA | 0.5733 | 0.4637 | 1071.0 | 1324.08 |
| SWEDEN | 0.4873 | 0.3654 | 8443.0 | 11258.74 |
| UMI | 0.8516 | 0.4945 | 18542.0 | 31931.18 |
| UTI | 0.9134 | 0.9134 | 12920.0 | 12920.0 |

## V1 → V2 Opt1 movers (oil_filter total CY2025) — capture delta

| Direction | DB | Δ capture | V1 | V2 |
|-----------|----|----------:|---:|---:|
| down | IRELAND | -0.5042 | 1.9056 | 1.4014 |
| down | UMI | -0.3571 | 0.8516 | 0.4945 |
| down | FINLAND | -0.1517 | 0.7824 | 0.6307 |
| down | SWEDEN | -0.1219 | 0.4873 | 0.3654 |
| down | BELGIUM | -0.1104 | 0.6262 | 0.5158 |
| up | MALTA | 0.4392 | 0.9047 | 1.3439 |
| up | CYPRUS | 0.0196 | 0.9123 | 0.9319 |
| up | GERMANY | 0.0114 | 0.1513 | 0.1627 |
| up | ITUK | 0.0000 | 1.1643 | 1.1643 |
| up | UTI | 0.0000 | 0.9134 | 0.9134 |

## GPS wallet index CY2025 (actual PMS € / wallet) — lowest first

| DB | index | wallet € | actual PMS € | V1 €/UIO |
|----|------:|---------:|-------------:|---------:|
| UMI | 0.10 | 2375057 | 244061 | 179 |
| HUNGARY | 0.17 | 514776 | 89618 | 88 |
| IUK | 0.18 | 6335266 | 1170885 | 128 |
| SWEDEN | 0.22 | 1205074 | 268549 | 151 |
| FINLAND | 0.25 | 169111 | 42802 | 231 |
| UTI | 0.26 | 2419774 | 627171 | 322 |
| GERMANY | 0.28 | 1391234 | 390119 | 197 |
| BELGIUM | 0.29 | 1171797 | 339981 | 220 |
| ICELAND | 0.33 | 48226 | 16142 | 210 |
| ROMANIA | 0.34 | 141066 | 48663 | 164 |
| GREECE | 0.38 | 411258 | 154620 | 139 |
| PORTUGAL | 0.40 | 794169 | 316319 | 209 |

## Still stub / open

- Categories without extract (clutch_kit, air_filter, clutch_booster, release_bearing, urea_filter, pilot_bearing): **BVP stub**.
- Opt2 PN-level generation intensity: LCV generation tags still mostly `unknown` except partial `dmax_rt`/`dmax_rg`.
- SCR cutoffs: need IMIT. V20 UIO not applied. No Mode A / V1 cutover.

## Constraints

- Do not quote V2 as the network KPI.
- IML Model B ITUK headline unchanged.
- Primary capture = **total** sales (not genuine-only).
