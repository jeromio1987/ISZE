"""Book B provisional weight rollup — PN + bucket summary from APL seeds.

Wraps the Aug-12 scaffold logic; adds bucket rollups for Jerome review.
Does NOT run an official Book B alloc (+4%/+5%) — ambition % still his call.

Outputs:
  01_data/00_derived/book_b_provisional_weights.csv
  01_data/00_derived/book_b_bucket_summary.csv
  01_data/00_derived/book_b_provisional.meta.json
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "01_data" / "00_derived"
SCAFFOLD_SCRIPT = ROOT / "01_data" / "01_Pricing" / "_build_forecast_weight_scaffold.py"
STAMP = "20260812"

OUT_PN = DERIVED / "book_b_provisional_weights.csv"
OUT_BUCKET = DERIVED / "book_b_bucket_summary.csv"
OUT_META = DERIVED / "book_b_provisional.meta.json"
SCAFFOLD_CSV = DERIVED / f"forecast_weight_scaffold_{STAMP}.csv"


def _ensure_scaffold() -> None:
    if SCAFFOLD_CSV.is_file():
        return
    spec = importlib.util.spec_from_file_location("fw_scaffold", SCAFFOLD_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.main()


def main() -> int:
    _ensure_scaffold()
    sc = pd.read_csv(SCAFFOLD_CSV, dtype=str)
    for col in ("l12m_eur", "growth_factor", "forecast_weight_eur"):
        if col in sc.columns:
            sc[col] = pd.to_numeric(sc[col], errors="coerce")

    sc["status"] = sc["forecast_weight_eur"].notna().map({True: "HAS_WEIGHT", False: "NEED_SEED_OR_NO_L12M"})
    sc.to_csv(OUT_PN, index=False)

    has_fw = sc.dropna(subset=["forecast_weight_eur"])
    bucket = (
        has_fw.groupby("book_b_bucket", dropna=False)
        .agg(
            pn_count=("pn", "nunique"),
            l12m_eur=("l12m_eur", "sum"),
            forecast_weight_eur=("forecast_weight_eur", "sum"),
            avg_growth_factor=("growth_factor", "mean"),
        )
        .reset_index()
        .sort_values("forecast_weight_eur", ascending=False)
    )
    total_fw = float(bucket["forecast_weight_eur"].sum()) or 1.0
    bucket["share_of_book_b_weight"] = (bucket["forecast_weight_eur"] / total_fw).round(4)
    bucket.to_csv(OUT_BUCKET, index=False)

    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_scaffold": str(SCAFFOLD_CSV.relative_to(ROOT)),
        "pn_rows": int(len(sc)),
        "pn_with_weight": int(has_fw["pn"].nunique()),
        "pn_need_seed": int(sc[sc["status"] != "HAS_WEIGHT"]["pn"].nunique()),
        "total_forecast_weight_eur": float(has_fw["forecast_weight_eur"].sum()),
        "buckets": len(bucket),
        "provisional": True,
        "ambition_target_pct": "NOT_SET — Jerome chooses Book B target (+4% / +5% / launch-only)",
        "note": "Growth factors are midpoints from PLAN_FORECAST_WEIGHTED_AMBITION.md — not signed off.",
    }
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"wrote {OUT_PN} ({len(sc):,} PN)")
    print(f"wrote {OUT_BUCKET} ({len(bucket)} buckets, total fw €{meta['total_forecast_weight_eur']:,.0f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
