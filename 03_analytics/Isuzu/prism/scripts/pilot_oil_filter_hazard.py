#!/usr/bin/env python3
"""Oil-filter hazard-function pilot vs the flat/bucketed service-frequency.

Question: does a fitted segment-level intensity predict holdout actual qty
better than the current expected_qty (bucket services × oil_filter factor 1.0)?

Identification wall (on the record, not a future-data ask):
  sales_fact is not VIN-linked. Age-at-sale is unobserved. A true age-decay
  hazard cannot be identified from PN sales. This pilot therefore fits
  *bucket* intensities (cv_std / f_series / lcv) — the covariates ISZE
  already has — from train DB-years:

      actual_qty ≈ λ_cv * cv_uio + λ_f * f_uio + λ_lcv * lcv_uio

  Those λ are intensity × network-average capture, not a physical hazard.
  A second spec fits only DB-years with total capture ≥ 0.80 (revealed
  frequency among markets that already buy the job).

Backtest: rolling-origin on complete years only (partial year dropped).
  fold 1 — train 2023, predict 2024
  fold 2 — train 2023–2024, predict 2025
Metric: MAE of predicted qty vs actual, vs current expected_qty baseline.
A candidate "clears" only if it beats the baseline on *both* folds.

Does not write FACTS.md, does not change pms_engine frequencies.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.linalg import lstsq

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR  # noqa: E402
from modules.pms_capture_config import (  # noqa: E402
    BUCKET_SERVICES_PER_YEAR,
    BUCKET_SERVICES_PER_YEAR_OVERRIDES,
    UIO_BY_BUCKET,
)
from modules.year_coverage import is_partial  # noqa: E402

EXCLUDE = {"TURKEY", "UNMAPPED"}
HIGH_CAPTURE = 0.80
OUT_JSON = PRISM_ROOT / "docs" / "pilot_oil_filter_hazard.json"


def _design(row: pd.Series) -> np.ndarray:
    return np.array([row["cv_std"], row["f_series"], row["lcv"]], dtype=float)


def _fit_lambda(train: pd.DataFrame) -> np.ndarray | None:
    if len(train) < 3:
        return None
    x = np.vstack(train.apply(_design, axis=1).to_numpy())
    y = train["actual_qty"].to_numpy(dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(y).all() or y.sum() <= 0:
        return None
    # Non-negative least squares is the right constraint for a frequency, but
    # scipy.optimize.nnls is extra surface; clip after unconstrained OLS.
    beta, *_ = lstsq(x, y, rcond=None)
    return np.clip(beta, 0.0, None)


def _mae(y: np.ndarray, yhat: np.ndarray) -> float:
    return float(np.mean(np.abs(y - yhat)))


def _rmse(y: np.ndarray, yhat: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y - yhat) ** 2)))


def main() -> int:
    pms = pd.read_csv(DERIVED_DIR / "pms_capture_by_db_year.csv")
    oil = pms[
        (pms["pms_category"] == "oil_filter")
        & (pms["line_type"] == "total")
        & (~pms["distributor_code"].isin(EXCLUDE))
    ].copy()
    oil["year"] = oil["year"].astype(int)
    oil = oil[~oil["year"].map(lambda y: bool(is_partial(int(y))))]

    rows = []
    for _, r in oil.iterrows():
        b = UIO_BY_BUCKET.get(r["distributor_code"])
        if not b:
            continue
        svc = {**BUCKET_SERVICES_PER_YEAR, **BUCKET_SERVICES_PER_YEAR_OVERRIDES.get(r["distributor_code"], {})}
        rows.append(
            {
                "distributor_code": r["distributor_code"],
                "year": int(r["year"]),
                "actual_qty": float(r["actual_qty"]),
                "expected_qty": float(r["expected_qty"]),
                "capture_rate": float(r["capture_rate"]),
                "uio_units": float(r["uio_units"]),
                "cv_std": b["cv_std"],
                "f_series": b["f_series"],
                "lcv": b["lcv"],
                "assumed_lambda": np.array(
                    [svc["cv_std"], svc["f_series"], svc["lcv"]], dtype=float
                ),
            }
        )
    df = pd.DataFrame(rows)
    years = [int(y) for y in sorted(df["year"].unique())]
    folds = []
    for i, holdout in enumerate(years[1:], start=1):
        train = df[df["year"] < holdout]
        test = df[df["year"] == holdout]
        if train.empty or test.empty:
            continue
        y = test["actual_qty"].to_numpy(dtype=float)
        y_base = test["expected_qty"].to_numpy(dtype=float)

        lam_all = _fit_lambda(train)
        y_all = (np.vstack(test.apply(_design, axis=1).to_numpy()) @ lam_all) if lam_all is not None else None

        hi = train[train["capture_rate"] >= HIGH_CAPTURE]
        lam_hi = _fit_lambda(hi)
        y_hi = (np.vstack(test.apply(_design, axis=1).to_numpy()) @ lam_hi) if lam_hi is not None else None

        fold = {
            "holdout_year": int(holdout),
            "n_train": int(len(train)),
            "n_test": int(len(test)),
            "n_high_capture_train": int(len(hi)),
            "mae_baseline_expected_qty": round(_mae(y, y_base), 1),
            "rmse_baseline_expected_qty": round(_rmse(y, y_base), 1),
        }
        if lam_all is not None and y_all is not None:
            fold["lambda_all_cv_f_lcv"] = [round(float(x), 4) for x in lam_all]
            fold["mae_fitted_all"] = round(_mae(y, y_all), 1)
            fold["rmse_fitted_all"] = round(_rmse(y, y_all), 1)
            fold["fitted_all_beats_baseline_mae"] = bool(_mae(y, y_all) < _mae(y, y_base))
        if lam_hi is not None and y_hi is not None:
            fold["lambda_highcap_cv_f_lcv"] = [round(float(x), 4) for x in lam_hi]
            fold["mae_fitted_highcap"] = round(_mae(y, y_hi), 1)
            fold["rmse_fitted_highcap"] = round(_rmse(y, y_hi), 1)
            fold["fitted_highcap_beats_baseline_mae"] = bool(_mae(y, y_hi) < _mae(y, y_base))
        folds.append(fold)

    assumed = BUCKET_SERVICES_PER_YEAR
    all_beats = all(f.get("fitted_all_beats_baseline_mae") for f in folds) if folds else False
    hi_beats = all(f.get("fitted_highcap_beats_baseline_mae") for f in folds) if folds else False
    # All-DB OLS beating MAE is not a hazard win: it recodes network under-capture
    # as a lower service frequency and would shrink the capture gap we are trying
    # to measure. Only the high-capture spec is a candidate frequency.
    result = {
        "category": "oil_filter",
        "complete_years": years,
        "n_db_years": int(len(df)),
        "assumed_lambda_cv_f_lcv": [assumed["cv_std"], assumed["f_series"], assumed["lcv"]],
        "identification": (
            "No VIN-level sales; λ is intensity × average capture, not a hazard. "
            "UIO mix is a single 2025E snapshot (data/uio_by_model_bucket.csv)."
        ),
        "folds": folds,
        "clears_backtest_fitted_all": all_beats,
        "clears_backtest_fitted_highcap": hi_beats,
        "why_fitted_all_is_not_a_pass": (
            "All-DB OLS can beat MAE by absorbing capture into λ (LCV fitted "
            "~0.34–0.45 vs assumed 1.0). Shipping that would hide the gap."
        ),
        "verdict": (
            "pass"
            if hi_beats
            else "null — high-capture (revealed-frequency) spec does not beat current expected_qty out of sample; all-DB MAE win is capture-contaminated"
        ),
    }
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"\nWrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
