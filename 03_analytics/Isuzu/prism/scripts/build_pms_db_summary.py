#!/usr/bin/env python3
"""
Per-distributor PMS capture summary (all 18 ISZE GPS-base DBs in pms_capture).

Output: Data/derived/pms_summary_by_db.csv
Run after build_bvp_p0_p1.py (needs pms_capture_by_db_year.csv).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, PMS_CAPTURE_BY_DB_CSV  # noqa: E402

OUTPUT_CSV = DERIVED_DIR / "pms_summary_by_db.csv"


def build_pms_db_summary(pms_path: Path = PMS_CAPTURE_BY_DB_CSV) -> pd.DataFrame:
    if not pms_path.exists():
        raise FileNotFoundError(f"Missing {pms_path}")

    df = pd.read_csv(pms_path)
    totals = df[df["line_type"] == "total"].copy()
    genuine = df[df["line_type"] == "genuine"].copy()
    latest_year = int(totals["year"].max())

    rows: list[dict] = []
    for dist in sorted(totals["distributor_code"].dropna().unique()):
        t = totals[(totals["distributor_code"] == dist) & (totals["year"] == latest_year)]
        g = genuine[(genuine["distributor_code"] == dist) & (genuine["year"] == latest_year)]
        if t.empty:
            continue

        uio = int(t["uio_units"].iloc[0])
        country = str(t["country"].iloc[0]) if "country" in t.columns else ""
        region = str(t["region"].iloc[0]) if "region" in t.columns else ""

        exp = t["expected_qty"].astype(float)
        act = t["actual_qty"].astype(float)
        rev = t["actual_rev_eur"].astype(float)
        wtd_total = float((t["capture_rate"].astype(float) * exp).sum() / exp.sum()) if exp.sum() > 0 else 0.0

        g_merge = t.merge(
            g[["pms_category", "capture_rate"]].rename(columns={"capture_rate": "cap_gen"}),
            on="pms_category",
            how="left",
        )
        exp_g = g_merge["expected_qty"].astype(float)
        wtd_gen = (
            float((g_merge["cap_gen"].fillna(0) * exp_g).sum() / exp_g.sum()) if exp_g.sum() > 0 else 0.0
        )

        gap_sum = float(t["revenue_gap_eur"].fillna(0).sum())
        oil = t[t["pms_category"] == "oil_filter"]
        oil_cap = float(oil["capture_rate"].iloc[0]) if not oil.empty else np.nan

        top_gap = (
            t[t["revenue_gap_eur"].fillna(0) > 0]
            .sort_values("revenue_gap_eur", ascending=False)
            .head(3)["pms_category"]
            .tolist()
        )

        rows.append(
            {
                "year": latest_year,
                "distributor_code": dist,
                "country": country,
                "region": region,
                "uio_units": uio,
                "categories_scored": int(len(t)),
                "capture_rate_total_wtd": round(wtd_total, 4),
                "capture_rate_genuine_wtd": round(wtd_gen, 4),
                "revenue_gap_eur_sum": round(gap_sum, 0),
                "oil_filter_capture": round(oil_cap, 4) if not np.isnan(oil_cap) else None,
                "top_gap_categories": "|".join(top_gap),
            }
        )

    return pd.DataFrame(rows)


def main() -> int:
    out = build_pms_db_summary()
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_CSV, index=False)
    print(f"pms_summary_by_db: {len(out)} distributors @ {out['year'].iloc[0]} -> {OUTPUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
