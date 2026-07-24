#!/usr/bin/env python3
"""
Build all strategic dashboard CSVs (contracts 1–15 except #4 runtime-only).

Run after P0–P5 pipeline. Use --rebuild-sales to refresh sales_fact with SaTy.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, PRISM_DATA_DIR  # noqa: E402
from modules.strategic_build import (  # noqa: E402
    build_basket_correlation,
    build_capture_recovery_model,
    build_capture_trajectory,
    build_distributor_geo,
    build_part_lifecycle,
    build_price_premium,
    build_revenue_concentration,
    build_revenue_waterfall,
    build_substitution_timeline,
    build_vor_airfreight_risk,
    build_vor_profile,
    build_vor_seasonality,
)

BUILDS: list[tuple[str, Path, object]] = [
    ("vor_airfreight_risk", DERIVED_DIR / "vor_airfreight_risk.csv", build_vor_airfreight_risk),
    ("vor_seasonality", DERIVED_DIR / "vor_seasonality.csv", build_vor_seasonality),
    ("vor_profile", DERIVED_DIR / "vor_profile.csv", build_vor_profile),
    ("capture_trajectory", DERIVED_DIR / "capture_trajectory.csv", build_capture_trajectory),
    ("part_lifecycle", DERIVED_DIR / "part_lifecycle.csv", build_part_lifecycle),
    ("revenue_concentration", DERIVED_DIR / "revenue_concentration.csv", build_revenue_concentration),
    ("revenue_waterfall", DERIVED_DIR / "revenue_waterfall.csv", build_revenue_waterfall),
    ("price_premium", DERIVED_DIR / "price_premium.csv", build_price_premium),
    ("basket_correlation", DERIVED_DIR / "basket_correlation.csv", build_basket_correlation),
    ("substitution_timeline", DERIVED_DIR / "substitution_timeline.csv", build_substitution_timeline),
    ("distributor_geo", PRISM_DATA_DIR / "distributor_geo.csv", build_distributor_geo),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rebuild-sales",
        action="store_true",
        help="Re-run build_sales_fact_from_cy.py to refresh saty column",
    )
    args = parser.parse_args()

    if args.rebuild_sales:
        rc = subprocess.call([sys.executable, str(PRISM_ROOT / "scripts" / "build_sales_fact_from_cy.py")])
        if rc != 0:
            return rc

    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    PRISM_DATA_DIR.mkdir(parents=True, exist_ok=True)

    failed = 0
    price_df = None
    for name, path, fn in BUILDS:
        print(f">> {name} …", flush=True)
        try:
            df = fn()
            path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(path, index=False)
            print(f"   {len(df):,} rows -> {path}")
            if name == "price_premium":
                price_df = df
        except Exception as e:
            print(f"   FAILED: {e}", flush=True)
            failed += 1

    print(">> capture_recovery_model …", flush=True)
    try:
        rec = build_capture_recovery_model(price_premium=price_df)
        out = DERIVED_DIR / "capture_recovery_model.csv"
        rec.to_csv(out, index=False)
        print(f"   {len(rec):,} rows -> {out}")
    except Exception as e:
        print(f"   FAILED: {e}", flush=True)
        failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
