"""P5.6 — export forecast_final CSV from candidates + backtest winner.

Reads  : forecast_candidates.parquet, backtest_report.parquet
Writes : forecast_final_YYYY_MM.csv, forecast_final.parquet
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_TOOLS = Path(__file__).resolve().parent.parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from _shared.paths import DERIVED_DIR, ISZE_ROOT  # noqa: E402

BUILDER_VERSION = "p5.6-v1"
CAND_SRC = DERIVED_DIR / "forecast_candidates.parquet"
BACK_SRC = DERIVED_DIR / "backtest_report.parquet"
OUT_PARQUET = DERIVED_DIR / "forecast_final.parquet"
OUT_META = DERIVED_DIR / "forecast_final.meta.json"


def main() -> int:
    if not CAND_SRC.is_file() or not BACK_SRC.is_file():
        print("Run build_forecast_baseline.py first", file=sys.stderr)
        return 1

    cand = pd.read_parquet(CAND_SRC)
    back = pd.read_parquet(BACK_SRC)
    winners = back[["db_code", "category", "best_model", "wape_best"]].drop_duplicates()

    merged = cand.merge(winners, on=["db_code", "category"], how="left")
    merged["best_model"] = merged["best_model"].fillna("naive")
    final = merged[merged["model"] == merged["best_model"]].copy()
    final["override_delta_units"] = 0.0
    final["override_reason"] = ""
    final["builder_version"] = BUILDER_VERSION
    final["produced_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    stamp = datetime.now(timezone.utc).strftime("%Y_%m")
    out_csv = DERIVED_DIR / f"forecast_final_{stamp}.csv"
    cols = [
        "db_code",
        "category",
        "forecast_month",
        "horizon_step",
        "units_forecast",
        "revenue_forecast",
        "wape_best",
        "best_model",
        "override_delta_units",
        "override_reason",
        "sparse_flag",
        "history_months",
    ]
    final[cols].to_csv(out_csv, index=False)
    final.to_parquet(OUT_PARQUET, index=False)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder_version": BUILDER_VERSION,
        "rows": int(len(final)),
        "series": int(final[["db_code", "category"]].drop_duplicates().shape[0]),
        "csv": str(out_csv.relative_to(ISZE_ROOT)),
        "parquet": str(OUT_PARQUET.relative_to(ISZE_ROOT)),
    }
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"wrote {out_csv} ({len(final):,} rows)")
    print(f"wrote {OUT_PARQUET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
