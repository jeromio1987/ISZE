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
GROUP_N75_N50_N62 = "N75_N50_N62"
GROUP_F_SERIES_MD = "F_Series_MD"
GROUP_LCV_D_MAX = "LCV_D_Max"


def map_uio_row_to_model_group(model: str, cv_lcv: str) -> str:
    """
    Map V17 UIO row (model + CV/LCV segment) → GPS target group.

    Groups match ISZE GPS maximum spend per unit:
      N75 / N50 / N62  → €1,120
      F-Series / MD    → €1,344
      LCV / D-Max      → €250
    """
    m = (model or "").strip().upper()
    seg = (cv_lcv or "").strip().upper()

    if "D-MAX" in m or "DMAX" in m or "D MAX" in m:
        return GROUP_LCV_D_MAX
    if seg == "LCV" or "NLR" in m or "N35" in m or "NLR8" in m:
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
    if seg == "LCV":
        return GROUP_LCV_D_MAX
    return "Other_LCV" if seg == "LCV" else "Other_CV"


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
