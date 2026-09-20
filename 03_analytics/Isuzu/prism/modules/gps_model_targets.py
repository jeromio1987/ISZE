"""
Per-model GPS maximum spend targets (€/vehicle/year).

Loaded from prism/data/gps_model_targets.csv — update when ISZE revises
the GPS workbook maximum spend per unit by model family.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PRISM_DATA = Path(__file__).resolve().parent.parent / "data"
DEFAULT_TARGETS_CSV = PRISM_DATA / "gps_model_targets.csv"

# Official ISZE maximum spend/unit groups (GPS workbook)
GROUP_N35_GRAFTER = "N35_Grafter"
GROUP_N75_N50_N62 = "N75_N50_N62"
GROUP_F_SERIES_MD = "F_Series_MD"
GROUP_LCV_D_MAX = "LCV_D_Max"

# Rate bands in descending price order. Used when splitting a collapsed "LD" UIO row into its
# N35 and N75 parts: the split is always [N35, N75], never the reverse.
CV_TRUCK_BANDS = (GROUP_N35_GRAFTER, GROUP_N75_N50_N62)


def map_uio_row_to_model_group(model: str, cv_lcv: str) -> str:
    """
    Map a UIO row (model + CV/LCV segment) → GPS target group.

    Group rates are the values actually loaded from gps_model_targets.csv, which is the source
    the engine uses. Corrected 2026-09-17: this docstring previously stated 1,120 / 1,344 / 250,
    which is 1.52x the CSV. The CSV derives 739 / 887 from the £ study
    (£1,000 and £1,200 x (1 - GP 34%) x FX 1.12); the 1,120 / 1,344 figures have no source on
    disk and did not match what the code applied.

      N35 Grafter      -> €296
      N75 / N50 / N62  -> €739
      F-Series / MD    -> €887
      LCV / D-Max      -> €250

    N35 vs N75 SPLIT (2026-09-17). The UIO workbook labels every N-prefix model "LD", so this
    mapper used to return the N75 group for all of them and priced the whole N35 Grafter fleet at
    the N75 rate — a €4.83M error on the ITUK ceiling alone. Two paths now keep them apart:

      * Explicit N35 / NMR / NLR codes -> N35_Grafter.
      * Model literally "LD" -> resolved upstream. ``_interpolate_uio_detail`` splits a bare
        "LD" row into N35 and N75 rows using the workbook's own ITUK carpark breakdown
        (sheet '2. Vehicle Volume' section B), so this function only ever sees split rows.
    """
    m = (model or "").strip().upper()
    seg = (cv_lcv or "").strip().upper()

    # N35 Grafter. Checked BEFORE the generic LD rule, because the UIO workbook collapses
    # N35 into the "LD" label and only the ITUK carpark sheet separates them.
    if "N35" in m or "GRAFTER" in m or "NLR" in m or "NMR" in m:
        return GROUP_N35_GRAFTER

    if "D-MAX" in m or "DMAX" in m or "D MAX" in m:
        return GROUP_LCV_D_MAX
    if seg == "LCV":
        return GROUP_LCV_D_MAX
    if (
        "F-SERIES" in m
        or "F SERIES" in m
        or "F110" in m
        or "F120" in m
        or "F-SER" in m
        or m.startswith("F ")
        or " MD" in m
        or m == "MD"
    ):
        return GROUP_F_SERIES_MD
    if (
        "N75" in m
        or "N50" in m
        or "N62" in m
        or "N65" in m
        or "NPR7" in m
        or "NPR8" in m
        or "NQR" in m
        or "LD" in m
        or (seg == "CV" and "NPR" in m)
    ):
        return GROUP_N75_N50_N62
    if seg == "CV":
        return GROUP_N75_N50_N62
    return "Other_LCV"


def load_gps_model_targets(path: Path | str | None = None) -> pd.DataFrame:
    csv_path = Path(path) if path else DEFAULT_TARGETS_CSV
    if not csv_path.exists():
        raise FileNotFoundError(
            f"GPS model targets not found: {csv_path}\n"
            "Create gps_model_targets.csv under prism/data/."
        )
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    required = {"model_group", "target_eur_per_vehicle"}
    if not required.issubset(df.columns):
        raise ValueError(f"gps_model_targets.csv must include columns: {required}")
    df["target_eur_per_vehicle"] = pd.to_numeric(
        df["target_eur_per_vehicle"], errors="coerce"
    )
    return df


def targets_by_group(path: Path | str | None = None) -> dict[str, float]:
    df = load_gps_model_targets(path)
    return dict(zip(df["model_group"], df["target_eur_per_vehicle"]))
