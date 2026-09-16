# Oil-filter hazard-function pilot — 2026-08-18

**Status:** null. Do not change `pms_engine` frequencies from this file.
**Repro:** `python scripts/pilot_oil_filter_hazard.py` → `docs/pilot_oil_filter_hazard.json`
**Category:** `oil_filter` only (ITUK anchors already reconcile to FACTS.md §1b).

## What was tested

Current expected demand for oil filter is still a **flat interval**: bucket services/year (`cv_std` 0.5, `f_series` 0.6667, `lcv` 1.0) × consumable factor 1.0 × UIO. The transferable OEM idea (Volvo/Scania/etc.) is a **fitted** intensity per segment instead of that constant.

ISZE has **no telematics and no VIN-linked sales**, so a true age-decay / remaining-useful-life hazard is not identifiable. This pilot therefore fits the covariates we already have — the CV-standard / F-Series / LCV UIO split in `data/uio_by_model_bucket.csv` — as:

```
actual_qty ≈ λ_cv * cv_uio + λ_f * f_uio + λ_lcv * lcv_uio
```

Two specs, rolling-origin holdout on complete years only (CY2026 dropped, coverage 0.25):

| Spec | Train sample | What λ actually is |
|---|---|---|
| All DB-years | every complete DB-year | intensity × **network-average capture** |
| High-capture | DB-years with total capture ≥ 80% | closest thing to revealed frequency among markets that already buy the job |

Baseline to beat: current `expected_qty` from `pms_capture_by_db_year.csv`. Metric: MAE of predicted qty vs actual. A spec clears only if it beats baseline on **both** folds (train 2023→holdout 2024; train 2023–24→holdout 2025).

## Result

| Fold | n train / test | MAE baseline | MAE all-DB fit | MAE high-capture fit |
|---|---|---|---|---|
| Holdout 2024 | 18 / 18 | 3,111.8 | **2,401.4** (beats) | 3,744.9 (loses) |
| Holdout 2025 | 36 / 18 | 3,730.0 | **1,802.2** (beats) | 4,062.8 (loses) |

Fitted λ vs assumed (0.50 / 0.67 / 1.00):

- All-DB: ~**0.84 / 0.00 / 0.34–0.45**. LCV intensity collapses toward average under-capture. F-Series unidentified (almost no UIO outside ITUK).
- High-capture: n=3 then n=8; F-Series λ ≈ **18** (overfit); CV-standard λ ≈ 0–0.08. Does not beat baseline on either fold.

## Why the all-DB MAE win is not a pass

Shipping the all-DB λ as a “fitted hazard” would **recode under-capture as lower service frequency** and shrink the capture gap PMS exists to show. That is the same class of mistake as a face-valid rubric: it improves a fit statistic without being a frequency. The only spec that could have been a frequency (high-capture) **failed** the backtest.

UIO mix is a single 2025E snapshot, not a year-varying age curve. No VIN-level usage. No telematics. Those are closed constraints, not a next-step shopping list.

**Decision:** leave oil-filter expected demand on the current bucketed constants. Do not present a new flat number as if it were fitted.
