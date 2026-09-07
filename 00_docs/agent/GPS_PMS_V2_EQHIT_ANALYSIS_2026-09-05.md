# GPS / PMS V2 — EQ-HIT extract analysis (Mode B)

**Built:** 2026-09-05 · shadow only · **no V1 cutover · no more EQ-HIT pulls**  
**SSOT extract:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\eqhit_extract_priority_cy2025.csv`  
**2311 rows / 37 PNs** · oil skipped · seed-PN applicability (not full catalogue)

---

## Verdict

EQ-HIT extract is now **wired into V2 shadow fitment**. Opt1 oil lens unchanged (BVP). Contested € still sits in clutch + blower; brake seed PNs reclassify as **CV-heavy**, which shrinks LCV expected for pad/shoe and lifts network capture >100% on pads — treat as **seed bias**, not “LCV has no brakes.”

---

## 1. What was built

| Artefact | Absolute path |
|----------|---------------|
| Fitment weights (BVP + EQ-HIT overlay) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_v2_fitment_weights.csv` |
| EQ-HIT coverage by category | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_v2_eqhit_fitment_coverage.csv` |
| Category gap (network, extract cats) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_v2_eqhit_category_gap_cy2025.csv` |
| Contested DB × category | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_v2_eqhit_contested_by_db_cy2025.csv` |
| PMS capture V2 (refreshed) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_capture_by_db_year_v2_mileage.csv` |
| Wallet index V2 (refreshed) | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_wallet_v2_by_distributor.csv` |
| Opt1/2/3 skeleton | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_v2_lcv_opt_skeleton.csv` |
| Opt1 sensitivity | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\pms_v2_lcv_opt1_sensitivity.csv` |
| Findings refresh | `C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\gps_pms_v2_findings.md` |
| Shadow builder | `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\scripts\build_gps_pms_v2_shadow.py` |
| Config | `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\data\gps_pms_v2_config.yaml` |
| This pack | `C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\GPS_PMS_V2_EQHIT_ANALYSIS_2026-09-05.md` |

Primary capture = **total** sales (`line_type=total`).

---

## 2. Fitment coverage (extract-backed)

| Category | Rows | PNs | cv_std | f_series | lcv | LCV gen RT/RG/unknown |
|----------|-----:|----:|-------:|---------:|----:|-----------------------|
| fuel_filter | 767 | 4 | 367 | 160 | 227 | 124 / 0 / 103 |
| brake_rotor | 335 | 8 | 226 | 0 | 109 | 18 / 0 / 91 |
| brake_pad | 320 | 3 | 320 | 0 | **0** | — |
| clutch_disc | 295 | 4 | 273 | 1 | 18 | 18 / 0 / 0 |
| clutch_pressure_plate | 259 | 3 | 195 | 1 | 47 | 41 / 5 / 1 |
| brake_shoe | 168 | 2 | 168 | 0 | **0** | — |
| blower_filter | 167 | 3 | 0 | 0 | 165 | 75 / 0 / 90 |
| oil_filter | — | — | BVP | BVP | BVP | **skipped** |

**BVP → EQ-HIT flips (binary weight):**

| Category / bucket | BVP | EQ-HIT | Read |
|-------------------|----:|-------:|------|
| brake_pad / lcv | 1 | **0** | Seed PNs = N-series only → LCV expected zeroed |
| brake_pad / cv_std | 0 | **1** | Same seeds open CV demand |
| brake_shoe / lcv | 1 | **0** | Same pattern |
| brake_rotor / cv_std | 0 | **1** | New CV applicability |
| brake_rotor / lcv | 0 | **1** | New LCV applicability |

Still **BVP stub** (no extract): clutch_kit, air_filter, clutch_booster, release_bearing, urea_filter, pilot_bearing.

---

## 3. V1 vs V2 Opt1 movers (oil_filter · total · CY2025)

Mileage + cohort only (oil not in EQ-HIT). Capture falls where LCV km raises expected.

| Direction | DB | V1 → V2 | Δ |
|-----------|-----|---------|--:|
| **Down hardest** | IRELAND | 1.91 → 1.40 | −0.50 |
| | UMI | 0.85 → 0.49 | −0.36 |
| | FINLAND | 0.78 → 0.63 | −0.15 |
| | SWEDEN | 0.49 → 0.37 | −0.12 |
| | BELGIUM | 0.63 → 0.52 | −0.11 |
| **Up** | MALTA | 0.90 → 1.34 | +0.44 |
| | CYPRUS | 0.91 → 0.93 | +0.02 |
| | GERMANY | 0.15 → 0.16 | +0.01 |
| Flat (no LCV km) | ITUK, UTI | unchanged | 0 |

---

## 4. Wallet index (actual PMS € / V2 wallet) — lowest CY2025

Wallet = Σ expected_v2 × avg SP (total line). EQ-HIT zeroing LCV pad/shoe **shrinks** wallet vs prior BVP-only run → indices move up slightly; ranking of weak DBs stable.

| DB | Index | Wallet € | Actual PMS € |
|----|------:|---------:|-------------:|
| UMI | 0.10 | 2.38M | 244k |
| HUNGARY | 0.17 | 0.51M | 90k |
| IUK | 0.18 | 6.34M | 1.17M |
| SWEDEN | 0.22 | 1.21M | 269k |
| FINLAND | 0.25 | 0.17M | 43k |
| UTI | 0.26 | 2.42M | 627k |
| GERMANY | 0.28 | 1.39M | 390k |
| BELGIUM | 0.29 | 1.17M | 340k |

---

## 5. Opt2 / Opt3 (IE + PT) — what EQ-HIT changes

| DB | Opt2 | Opt3 | Opt1 cap | Opt2 cap | Opt3 cap |
|----|------|------|---------:|---------:|---------:|
| IRELAND | ON (SIMI Trooper vs D-Max agg) | VIN proxy only | 1.40 | 1.72 | 1.40 |
| PORTUGAL | ON (Matriculas RT/RG) | ON Matriculas age≤10 (0.62) | 0.45 | 0.56 | 0.73 |

**EQ-HIT effect on Opt2/3 today:** none on the oil skeleton (oil skipped). Fitment overlay **does** change expected/gap for clutch/brake/blower/fuel/rotor in Opt1 capture CSV. Opt2 PN-level generation intensity stays stub: LCV `lcv_generation` still mostly `unknown` (Trooper tags = 0 in extract).

---

## 6. Top gaps / contested capture (extract categories · total)

| Category | Network capture V2 | EUR gap | Worst DBs (capture) | Largest € gap DBs |
|----------|-------------------:|--------:|---------------------|-------------------|
| clutch_disc | 4.6% | **3.84M** | NO/SE/HU ~0 | IUK 1.65M · UMI 0.48M · SE 0.33M |
| clutch_pressure_plate | 5.3% | **2.37M** | NO/SE/HU ~0 | IUK 0.70M · UMI 0.29M · UTI 0.25M |
| blower_filter | 15.8% | **1.82M** | UMI 0.4% · IE · DE | IUK 0.60M · UMI 0.43M · DE 0.16M |
| brake_rotor | 45.3% | **1.71M** | UMI/UTI/RO | IUK 0.66M · UMI 0.40M · UTI 0.22M |
| fuel_filter | 38.5% | **1.16M** | IUK/HU/FI | IUK 0.61M · UMI 0.19M · DE 0.14M |
| brake_shoe | 54.1% | 0.31M | ITUK/UTI/PT | ITUK 0.26M · UTI 77k |
| brake_pad | **140%** | 0.29M | UTI/ITUK | UTI 0.46M · ITUK 0.19M |

**Brake pad >100% capture** = expected collapsed after LCV fitment=0 on CV-only seeds while actual still includes LCV sales. Do **not** celebrate; expand LCV brake PNs later if Jerome asks — this pass was analysis-only.

---

## 7. Still stub

- Full EQ-HIT catalogue (only 37 seed PNs)
- Remaining PMS cats without extract → BVP
- Opt2 Trooper/RT/RG PN intensity (generation tags thin)
- SCR 15k vs 20k (IMIT)
- V20 UIO on live workbook
- Mode A / V1 replacement

---

## 8. Dual-lane reminder

V1 `pms_capture_by_db_year.csv` / `gps_spu_by_distributor.csv` **untouched**. Quote network KPI from V1 + green verify only. This pack = Mode B shadow.
