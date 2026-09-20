#!/usr/bin/env python3
"""
Build the lost-sales model (where are we losing sales, by market, family and service category).

Run standalone:
  python scripts/build_lost_sales_model.py

Ordering inside run_pipeline_and_verify.ps1 matters: this script must run AFTER
``scripts/build_wallet_waterfall.py`` (it consumes the ceiling, the uncaptured euro and the GPS %)
and after ``scripts/build_strategic_contracts.py`` (capture_recovery_model, substitution_timeline,
capture_trajectory). It is a separate step rather than a line inside build_strategic_contracts
precisely because wallet_waterfall is rebuilt later in the same pipeline run, so building the
ceiling lockstep would leave this model holding the previous run's ceiling.

Writes:
  Data/derived/lost_sales_model.csv                  market x family x service category x year
  Data/derived/lost_sales_market.csv                 market x year, ceiling and cover
  Data/derived/lost_sales_competitor_pn.csv          the part numbers that carry a competitor price
  Data/derived/lost_sales_competitor_coverage.csv    coverage share per competitor source
  Data/derived/lost_sales_model.meta.json            sources, vintages and the limits that apply

Verified by ``scripts/verify_derived_pipeline.py`` -> check_lost_sales_model /
check_lost_sales_competitor. Exit 0 does not mean the numbers are right; the verifier does.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from modules.lost_sales_build import write_model  # noqa: E402


def main() -> int:
    summary = write_model()
    tie = summary.get("tieouts", {})
    print(f"  -> {summary['rows']:,} rows over {summary['distributors']} markets, "
          f"years {summary['years']}")
    print(f"     billed EUR {tie.get('model_billed_eur'):,.2f} "
          f"vs parts base EUR {tie.get('parts_base_eur'):,.2f} "
          f"(delta {tie.get('billed_delta_eur')})")
    print(f"     service-axis coverage "
          f"{tie.get('pms_category_coverage_pct_of_billed')}% of billed euro")
    for name, path in summary.get("outputs", {}).items():
        print(f"     {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
