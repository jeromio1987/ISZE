#!/usr/bin/env python3
"""Check brake / clutch / urea are tagged as PMS across BVP catalog + parts_catalog_dimension."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from modules.bvp_catalog_io import PMS_SUBGROUP_AS_CATEGORY  # noqa: E402

DER = Path(PRISM_ROOT).parent.parent.parent / "Data" / "derived"
WEAR = [
    "brake_pad",
    "brake_shoe",
    "clutch_disc",
    "clutch_pressure_plate",
    "clutch_kit",
    "release_bearing",
    "pilot_bearing",
    "clutch_booster",
    "urea_filter",
]


def main() -> int:
    dim = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str)
    cat = pd.read_csv(DER / "parts_catalog_dimension.csv", dtype=str)
    pms = dim[dim["pms_flag"].astype(str).str.lower().isin(["true", "1"])]

    print("BVP catalog — PMS-flagged by category (product_subgroup / pms_category)")
    for sg in WEAR:
        sub = pms[
            (pms["product_subgroup"] == sg)
            | (pms["pms_category"].fillna("") == sg)
        ]
        miss_cat = sub[sub["pms_category"].isna() | (sub["pms_category"].astype(str).str.strip() == "")]
        print(f"  {sg:24} {len(sub):4} PNs  missing pms_category: {len(miss_cat)}")

    print("\nparts_catalog_dimension — rows with pms_category in wear/urea list")
    for sg in WEAR:
        n = len(cat[cat["pms_category"] == sg])
        print(f"  {sg:24} {n:6}")

    expected_subgroups = set(PMS_SUBGROUP_AS_CATEGORY)
    print(f"\nExpected PMS subgroups in code: {len(expected_subgroups)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
