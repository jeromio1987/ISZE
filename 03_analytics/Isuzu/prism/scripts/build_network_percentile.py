#!/usr/bin/env python3
"""
Contract 10 — Network Percentile Radar.

Output: Data/derived/network_percentile.csv
Sources: gps_spu_by_distributor + pms_capture_by_db_year + mix_genuine_bvp_by_family
         + aim_exposure_by_db_year

Run after P0–P5 pipeline outputs exist.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    AIM_EXPOSURE_BY_DB_CSV,
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
    MIX_BY_FAMILY_CSV,
    PMS_CAPTURE_BY_DB_CSV,
)

OUTPUT_CSV = DERIVED_DIR / "network_percentile.csv"

METRICS_ASCENDING = ("gps_spu", "total_capture", "genuine_capture")
METRICS_INVERTED = ("bvp_mix", "aim_risk")
ALL_METRICS = METRICS_ASCENDING + METRICS_INVERTED


def _percentile_rank(values: pd.Series, invert: bool = False) -> pd.Series:
    """Map raw values to 0–100 percentile within the series (higher = better)."""
    n = values.notna().sum()
    if n <= 1:
        return pd.Series(50.0 if n == 1 else np.nan, index=values.index)

    ranked = values.rank(method="min", ascending=not invert)
    return (ranked - 1) / (n - 1) * 100.0


def _metric_block(
    base: pd.DataFrame,
    metric: str,
    raw_col: str = "raw_value",
    invert: bool = False,
) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for year, grp in base.groupby("year", sort=True):
        g = grp.copy()
        g["metric"] = metric
        g["raw_value"] = g[raw_col]
        g["network_median"] = g["raw_value"].median()
        g["vs_median"] = g["raw_value"] - g["network_median"]
        g["n_distributors"] = int(g["distributor_code"].nunique())
        g["percentile_rank"] = _percentile_rank(g["raw_value"], invert=invert)
        rows.append(
            g[["distributor_code", "year", "metric", "raw_value", "percentile_rank",
               "network_median", "vs_median", "n_distributors"]]
        )
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_network_percentile(
    gps_path: Path = GPS_SPU_BY_DB_CSV,
    pms_path: Path = PMS_CAPTURE_BY_DB_CSV,
    mix_path: Path = MIX_BY_FAMILY_CSV,
    aim_path: Path = AIM_EXPOSURE_BY_DB_CSV,
) -> pd.DataFrame:
    for label, path in [
        ("gps", gps_path),
        ("pms", pms_path),
        ("mix", mix_path),
        ("aim", aim_path),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"Missing {label}: {path}")

    gps = pd.read_csv(gps_path)
    pms = pd.read_csv(pms_path)
    mix = pd.read_csv(mix_path)
    aim = pd.read_csv(aim_path)

    blocks: list[pd.DataFrame] = []

    gps_base = gps[["year", "distributor_code", "spend_per_unit_eur"]].rename(
        columns={"spend_per_unit_eur": "raw_value"}
    )
    blocks.append(_metric_block(gps_base, "gps_spu", invert=False))

    for line_type, metric in (("total", "total_capture"), ("genuine", "genuine_capture")):
        sub = pms[pms["line_type"] == line_type]
        cap = (
            sub.groupby(["year", "distributor_code"], as_index=False)
            .agg(actual_qty=("actual_qty", "sum"), expected_qty=("expected_qty", "sum"))
        )
        cap["raw_value"] = cap["actual_qty"] / cap["expected_qty"].replace(0, np.nan)
        blocks.append(_metric_block(cap, metric, invert=False))

    mix_agg = (
        mix.groupby(["year", "distributor_code"], as_index=False)["bvp_share_units"]
        .mean()
        .rename(columns={"bvp_share_units": "raw_value"})
    )
    blocks.append(_metric_block(mix_agg, "bvp_mix", invert=True))

    aim_base = aim[["year", "distributor_code", "high_risk_rev_pct"]].rename(
        columns={"high_risk_rev_pct": "raw_value"}
    )
    blocks.append(_metric_block(aim_base, "aim_risk", invert=True))

    out = pd.concat(blocks, ignore_index=True)
    out["year"] = out["year"].astype(int)
    out = out.sort_values(["year", "metric", "distributor_code"]).reset_index(drop=True)
    return out


def main() -> int:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_network_percentile()
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"network_percentile: {len(df):,} rows -> {OUTPUT_CSV}")
    for m in ALL_METRICS:
        n = (df["metric"] == m).sum()
        print(f"  {m}: {n:,} rows")
    if df.empty:
        print("  WARNING: no rows produced")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
