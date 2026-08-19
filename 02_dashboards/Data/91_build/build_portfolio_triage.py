#!/usr/bin/env python3
"""Portfolio triage CSV — early warning + account health + GPS/PMS (Monday sort).

Writes : 01_data/00_derived/portfolio_triage_20260819.csv
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DER = ISZE / "01_data" / "00_derived"
INTER = ISZE / "01_data" / "17_interactions"
PRISM_DATA = ISZE / "03_analytics" / "Isuzu" / "prism" / "data"

OUT = DER / "portfolio_triage_20260819.csv"
OUT_META = DER / "portfolio_triage.meta.json"


def main() -> int:
    ew = pd.read_csv(DER / "early_warning.csv") if (DER / "early_warning.csv").is_file() else pd.DataFrame()
    ah_path = INTER / "account_health.parquet"
    ah = pd.read_parquet(ah_path) if ah_path.is_file() else pd.DataFrame()
    pms_path = PRISM_DATA / "pms_capture_by_db_year.csv"
    pms = pd.read_csv(pms_path) if pms_path.is_file() else pd.DataFrame()
    gps_path = DER / "gps_pure_sales_2026-08-13_v2.csv"
    gps = pd.read_csv(gps_path) if gps_path.is_file() else pd.DataFrame()

    # Early warning — distributor level only
    base = pd.DataFrame()
    if not ew.empty:
        base = ew[ew["level"] == "distributor"].copy()
        base = base.rename(
            columns={
                "distributor_code": "db_code",
                "severity_name": "ew_severity",
                "n_signals": "ew_n_signals",
                "eur_exposed": "ew_eur_exposed",
                "why_this_cycle": "ew_why",
                "priority": "ew_priority",
            }
        )
        base = base[
            [
                "db_code",
                "ew_priority",
                "ew_severity",
                "ew_n_signals",
                "ew_eur_exposed",
                "ew_why",
            ]
        ]

    # Account health latest
    ah_snap = pd.DataFrame()
    if not ah.empty:
        latest = ah["year_month"].max()
        ah_snap = ah[ah["year_month"] == latest][["db_code", "alert_level", "alert_reasons"]].copy()
        ah_snap = ah_snap.rename(columns={"alert_level": "ah_alert", "alert_reasons": "ah_reasons"})

    # PMS total capture CY2025
    pms_snap = pd.DataFrame()
    if not pms.empty:
        p25 = pms[(pms["year"] == 2025) & (pms["line_type"] == "total")]
        if not p25.empty:
            pms_snap = (
                p25.groupby("distributor_code", as_index=False)
                .agg(pms_capture_pct=("capture_rate", "mean"), pms_revenue_eur=("revenue_eur", "sum"))
                .rename(columns={"distributor_code": "db_code"})
            )

    # GPS CY2025
    gps_snap = pd.DataFrame()
    if not gps.empty and "year" in gps.columns:
        g25 = gps[gps["year"] == 2025]
        if not g25.empty and "distributor_code" in g25.columns:
            gps_snap = g25.groupby("distributor_code", as_index=False).agg(
                gps_pct=("gps_pct", "mean"),
                pure_sales_eur=("pure_sales_eur", "sum"),
            ).rename(columns={"distributor_code": "db_code"})

    # Union all DB codes
    codes = set()
    for df in (base, ah_snap, pms_snap, gps_snap):
        if not df.empty and "db_code" in df.columns:
            codes.update(df["db_code"].dropna().astype(str))

    rows = []
    for db in sorted(codes):
        row = {"db_code": db}
        if not base.empty:
            m = base[base["db_code"] == db]
            if not m.empty:
                row.update(m.iloc[0].to_dict())
        if not ah_snap.empty:
            m = ah_snap[ah_snap["db_code"] == db]
            if not m.empty:
                row.update(m.iloc[0].to_dict())
        if not pms_snap.empty:
            m = pms_snap[pms_snap["db_code"] == db]
            if not m.empty:
                row.update(m.iloc[0].to_dict())
        if not gps_snap.empty:
            m = gps_snap[gps_snap["db_code"] == db]
            if not m.empty:
                row.update(m.iloc[0].to_dict())
        # Sort key: EW priority, then AH alert
        ah_rank = {"RED": 0, "AMBER": 1, "NONE": 2}.get(str(row.get("ah_alert", "NONE")), 3)
        ew_rank = row.get("ew_priority", 999)
        row["triage_rank"] = (ew_rank if pd.notna(ew_rank) else 999) * 10 + ah_rank
        rows.append(row)

    out = pd.DataFrame(rows).sort_values("triage_rank")
    out.to_csv(OUT, index=False)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": int(len(out)),
        "sources": {
            "early_warning": (DER / "early_warning.csv").exists(),
            "account_health": ah_path.exists(),
            "pms_capture": pms_path.exists(),
            "gps": gps_path.exists(),
        },
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"wrote {OUT} ({len(out)} DBs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
