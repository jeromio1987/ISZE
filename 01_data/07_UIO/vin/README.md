# JP VIN register — separate project

**Status:** structured; **wired into PRISM page 22 (Parc Cohorts) 2026-08-20** (reads `VIN_register.parquet`). Still **not** a UIO v19 denominator — cohort signal only.
**As-of for rolling 60m:** 2026-07-27
**Scope:** CV shipments from this JP extract — **ex ITUK & UTI** (those packs come later; F-heavy).

## Layout

| Path | Role |
|------|------|
| `raw/VIN_list_JP_YYYYMMDD.xlsx` | Immutable JP drop (SKD + CBU sheets) |
| `build_vin_register.py` | Rebuild slim unified register |
| `VIN_register.parquet` | ★ working register (SKD∪CBU) |
| `VIN_register.csv` | Same, for Excel |
| `model_dimension.csv` | Unique ISZJ models × counts |
| `VIN_register_summary.json` | Build counts |

Rebuild:

```powershell
python "$env:ISZE_ROOT\01_data\07_UIO\vin\build_vin_register.py"
```

## What we decode safely

From **VIN** (Europe `JAA`/`JAL` pattern in this file) + **ISZJ model name**:

- Series / N vs F / nominal GVW class (`75`→7.5t, …)
- Hand hint `L`≈LHD / `U`≈RHD (export naming)
- Wheelbase letter (model suffix / VIN pos 9)
- DB (+ `PT to BE`-style re-export origin→destination)
- Dates → `cohort_date` (invoice → shipment → assembly) → **`in_pms_rolling_60m`**

## Transmission (AT / MT / AMT) — honest answer

**Not visible as a reliable field in this VIN.**

- NHTSA vPIC does **not** decode these Europe `JAANPR75…` strings (US scheme differs; `TransmissionStyle` empty).
- VIN positions here encode WMI + embedded model (e.g. `NPR75`) + WB + plant/serial — **no validated gearbox character**.
- Model suffix letters (`VAYE` / `VWYE` / …) are **not** proven AT vs MT for Europe. LatAm catalog pages list both `…VAYN` and `…VWY` as **MYY-5T manual** — so a V/W heuristic would be a fault.

Until ISZJ supplies a **model_code / model_name → transmission** map (or Allison/AMT option list), columns stay:

`transmission = unknown` · `transmission_source = none`

## Enrichment path (later — do not auto-join yet)

Safe when ready:

1. Use this register as a **shipment cohort** (young parc from JP), never as a drop-in replacement for `06_uio/_CURRENT` registered UIO.
2. Join PMS / GPS at **DB × series × gvw × year** (or DB × year) — label denominator as “JP VIN cohort, rolling 60m”, not “UIO v19”.
3. When ITUK / UTI VIN packs arrive, append with `source_market` and keep F-series visible; still don’t blend into Israel IDS (UMI≠UTI rule unchanged).
4. Only after a signed transmission map: fill `transmission` and rebuild — then PMS ATF vs clutch basket splits are legitimate.

Unsafe (don’t):

- Overwrite UIO Overview totals with VIN counts
- Infer AT/MT from suffix guesses
- Mix this cohort €/UIO with full-network GPS without a clear label
