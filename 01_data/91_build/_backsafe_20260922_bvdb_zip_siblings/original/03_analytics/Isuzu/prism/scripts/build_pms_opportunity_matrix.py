#!/usr/bin/env python3
"""
Contract 3 — PMS Opportunity Matrix.

Output: Data/derived/pms_opportunity_matrix.csv
Sources: pms_capture_by_db_year.csv + gps_spu_by_distributor.csv

Run after build_bvp_p0_p1.py and build_bvp_p4_p5.py (GPS SPU).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
    PMS_CAPTURE_BY_DB_CSV,
)

OUTPUT_CSV = DERIVED_DIR / "pms_opportunity_matrix.csv"


def build_pms_opportunity_matrix(
    pms_path: Path = PMS_CAPTURE_BY_DB_CSV,
    gps_path: Path = GPS_SPU_BY_DB_CSV,
) -> pd.DataFrame:
    if not pms_path.exists():
        raise FileNotFoundError(f"Missing {pms_path}")
    if not gps_path.exists():
        raise FileNotFoundError(f"Missing {gps_path}")

    pms = pd.read_csv(pms_path)
    gps = pd.read_csv(gps_path)[["year", "distributor_code", "country", "region"]]

    keys = ["year", "distributor_code", "pms_category"]
    total = pms[pms["line_type"] == "total"].copy()
    genuine = pms[pms["line_type"] == "genuine"].copy()

    total = total[total["expected_qty"] > 0]
    if total.empty:
        return pd.DataFrame()

    gen_cols = {
        "capture_rate": "capture_rate_genuine",
        "actual_qty": "actual_qty_genuine",
    }
    gen = genuine[keys + ["capture_rate"]].rename(columns=gen_cols)

    out = total[keys + [
        "uio_units",
        "expected_qty",
        "actual_qty",
        "actual_rev_eur",
        "capture_rate",
        "revenue_gap_eur",
        "revenue_gap_quotable",
    ]].rename(columns={"capture_rate": "capture_rate_total"})

    out = out.merge(gen, on=keys, how="left")
    out["capture_rate_genuine"] = out["capture_rate_genuine"].fillna(0.0)

    out["avg_sp_eur"] = np.where(
        out["actual_qty"] > 0,
        out["actual_rev_eur"] / out["actual_qty"],
        0.0,
    )
    out["tam_eur"] = out["expected_qty"] * out["avg_sp_eur"]
    out["genuine_bvp_gap_pp"] = out["capture_rate_total"] - out["capture_rate_genuine"]
    out["uio_units"] = out["uio_units"].astype(int)

    out = out.merge(gps, on=["year", "distributor_code"], how="left")

    columns = [
        "distributor_code",
        "pms_category",
        "year",
        "capture_rate_total",
        "capture_rate_genuine",
        "revenue_gap_eur",
        "revenue_gap_quotable",
        "avg_sp_eur",
        "tam_eur",
        "uio_units",
        "genuine_bvp_gap_pp",
        "country",
        "region",
    ]
    out = out[columns].sort_values(["year", "distributor_code", "pms_category"]).reset_index(drop=True)
    return out


def main() -> int:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_pms_opportunity_matrix()
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"pms_opportunity_matrix: {len(df):,} rows -> {OUTPUT_CSV}")
    if df.empty:
        print("  WARNING: no rows produced")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
