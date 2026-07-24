#!/usr/bin/env python3
"""
Defection early-warning — purchase-rhythm alarms.

Two levels:
  1. distributor x pms_category (sales_fact monthly, 2023-2025): inter-order
     gap analysis. Alert when current silence >= gap_alert_factor x median gap.
  2. ITUK dealer level (Sales to Dealers_ITUK_CY2025.xlsx via
     dealer_sales_loader): dealers active >= N months that went silent before
     data end.

"Current silence" is measured against the LAST MONTH PRESENT IN THE DATA,
not today — the data horizon is printed and written into the output.

Output: Data/derived/defection_alerts.csv  (column `level` = distributor | dealer)
Run from prism/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DERIVED_DIR, GENUINE_BVP_CROSSREF_CSV, resolve_mapping_path  # noqa: E402
from modules.data_prep import EXCLUDED_CODES, load_distributor_mapping  # noqa: E402
from modules.dealer_sales_loader import MONTHS, load_ituk_dealer_sales  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402

OUT_CSV = DERIVED_DIR / "defection_alerts.csv"
ASSUMPTIONS = PRISM_ROOT / "data" / "decision_model_assumptions.yaml"


def _norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lstrip("0")


def _month_index(year: pd.Series, month: pd.Series) -> pd.Series:
    return year.astype(int) * 12 + month.astype(int) - 1


def distributor_level(cfg: dict) -> tuple[pd.DataFrame, int]:
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    df, src = load_prism_sales(df_map)
    print(f"defection: {len(df):,} sales rows from {src}")
    df = df[~df["distributor_code"].isin(EXCLUDED_CODES | {"UNMAPPED"})]
    if "line_kind" in df.columns:
        df = df[df["line_kind"] == "part"]

    xref = pd.read_csv(GENUINE_BVP_CROSSREF_CSV, dtype={"genuine_pn": str, "bvp_pn": str})
    cat_map: dict[str, str] = {}
    for col in ("genuine_pn", "bvp_pn"):
        sub = xref.dropna(subset=[col, "pms_category"])
        cat_map.update(dict(zip(_norm(sub[col]), sub["pms_category"])))

    df = df.copy()
    df["pms_category"] = _norm(df["part_number"]).map(cat_map)
    df = df.dropna(subset=["pms_category"])
    df["month"] = pd.to_datetime(df["billing_date"]).dt.month
    df["midx"] = _month_index(df["year"], df["month"])
    data_end = int(df["midx"].max())

    monthly = (
        df[df["billed_qty"] >= cfg["min_qty_per_month"]]
        .groupby(["distributor_code", "pms_category", "midx"])
        .agg(qty=("billed_qty", "sum"), rev=("net_sales_value", "sum"))
        .reset_index()
    )

    rows = []
    for (dist, cat), grp in monthly.groupby(["distributor_code", "pms_category"]):
        m = sorted(grp["midx"].unique())
        if len(m) < cfg["min_historical_orders"]:
            continue
        gaps = np.diff(m)
        median_gap = float(np.median(gaps)) if len(gaps) else 1.0
        current_gap = data_end - m[-1]
        alert = current_gap >= cfg["gap_alert_factor"] * max(median_gap, 1.0)
        rows.append(
            {
                "level": "distributor",
                "entity": dist,
                "distributor_code": dist,
                "pms_category": cat,
                "active_months": len(m),
                "median_gap_months": round(median_gap, 1),
                "last_order_month": f"{m[-1] // 12}-{m[-1] % 12 + 1:02d}",
                "silent_months": int(current_gap),
                "trailing_12m_rev_eur": round(
                    float(grp[grp["midx"] > data_end - 12]["rev"].sum()), 2
                ),
                "alert": bool(alert),
            }
        )
    return pd.DataFrame(rows), data_end


def dealer_level(cfg: dict) -> pd.DataFrame:
    df = load_ituk_dealer_sales(2025)
    if df.empty:
        print("WARN: ITUK dealer sell-out file not found — dealer level skipped")
        return pd.DataFrame()
    month_cols = [c for c in MONTHS if c in df.columns]
    agg = df.groupby("dealer_name")[month_cols].sum()
    n_months = len(month_cols)

    rows = []
    for dealer, r in agg.iterrows():
        active = [i for i, c in enumerate(month_cols) if r[c] > 0]
        if len(active) < cfg["dealer_min_active_months"]:
            continue
        last_active = active[-1]
        silent = (n_months - 1) - last_active
        alert = silent >= cfg["dealer_silent_months"]
        rows.append(
            {
                "level": "dealer",
                "entity": dealer,
                "distributor_code": "ITUK",
                "pms_category": "all_parts",
                "active_months": len(active),
                "median_gap_months": None,
                "last_order_month": f"2025-{last_active + 1:02d}",
                "silent_months": int(silent),
                "trailing_12m_rev_eur": None,  # sell-out file is units only
                "alert": bool(alert),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    cfg = yaml.safe_load(ASSUMPTIONS.read_text(encoding="utf-8"))["defection"]

    df_dist, data_end = distributor_level(cfg)
    df_dealer = dealer_level(cfg)
    out = pd.concat([df_dist, df_dealer], ignore_index=True)
    horizon = f"{data_end // 12}-{data_end % 12 + 1:02d}"
    out["data_horizon"] = horizon
    out = out.sort_values(["alert", "silent_months"], ascending=[False, False])
    out.to_csv(OUT_CSV, index=False)

    n_alerts = int(out["alert"].sum())
    print(
        f"defection: {len(out)} series -> {OUT_CSV.name} | {n_alerts} alerts "
        f"({int(out[(out['alert']) & (out['level'] == 'dealer')].shape[0])} dealer-level) "
        f"| data horizon {horizon}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
