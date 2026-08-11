#!/usr/bin/env python3
"""Build AIM billing windows — CY and FY — from sales_fact (billing-only).

Outputs:
  01_data/00_derived/aim_billing_windows.json
  01_data/00_derived/aim_billing_by_db_window.csv

Windows (ISZE fiscal = Apr–Mar):
  CY2024, CY2025, CY2026 YTD
  FY2025 (= 2025-04-01 … 2026-03-31), FY2026 YTD (= 2026-04-01 … max)

No AIM workbook scoring — actual net sales only + aim_pn_classification join.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DERIVED = ISZE / "01_data" / "00_derived"
sys.path.insert(0, str(ISZE / "03_analytics" / "Isuzu" / "prism"))

from config import DERIVED_DIR  # noqa: E402
from modules.bvp_analytics import normalize_pn_value  # noqa: E402
from modules.data_prep import EXCLUDED_CODES, load_distributor_mapping  # noqa: E402
from modules.sales_loader import load_prism_sales  # noqa: E402
from config import resolve_mapping_path  # noqa: E402

OUT_JSON = DERIVED / "aim_billing_windows.json"
OUT_CSV = DERIVED / "aim_billing_by_db_window.csv"


def _norm_pn(v) -> str:
    return normalize_pn_value(v) or ""


def _window_mask(df: pd.DataFrame, start: date, end: date) -> pd.Series:
    d = df["billing_date"].dt.date
    return (d >= start) & (d <= end)


def main() -> int:
    df_map = load_distributor_mapping(str(resolve_mapping_path()))
    sf, src = load_prism_sales(df_map)
    sf = sf[(sf["line_kind"] == "part") & (~sf["distributor_code"].isin(EXCLUDED_CODES))].copy()
    # Prefer real billing_date; fall back to year-month mid-month
    if "billing_date" not in sf.columns or sf["billing_date"].isna().all():
        sf["billing_date"] = pd.to_datetime(
            dict(year=sf["year"], month=sf["month"], day=15), errors="coerce"
        )
    else:
        sf["billing_date"] = pd.to_datetime(sf["billing_date"], errors="coerce")
    sf = sf.dropna(subset=["billing_date"])

    cls_path = DERIVED_DIR / "aim_pn_classification.csv"
    if cls_path.exists():
        cls = pd.read_csv(cls_path, dtype=str)
        cls["_pn"] = cls["part_number"].map(_norm_pn)
        cls = cls.drop_duplicates("_pn").set_index("_pn")
        sf["_pn"] = sf["part_number"].map(_norm_pn) if "part_number" in sf.columns else sf.get(
            "material_num", pd.Series("", index=sf.index)
        ).map(_norm_pn)
        if "part_number" not in sf.columns and "material" in sf.columns:
            sf["_pn"] = sf["material"].map(_norm_pn)
        sf = sf.join(cls[["aim_l1"]], on="_pn", how="left")
        sf["classified"] = sf["aim_l1"].notna() & (sf["aim_l1"].astype(str).str.strip() != "")
    else:
        sf["classified"] = False
        sf["aim_l1"] = None

    max_d = sf["billing_date"].max().date()
    windows = {
        "CY2024": (date(2024, 1, 1), date(2024, 12, 31)),
        "CY2025": (date(2025, 1, 1), date(2025, 12, 31)),
        "CY2026_YTD": (date(2026, 1, 1), max_d),
        "FY2025": (date(2025, 4, 1), date(2026, 3, 31)),
        "FY2026_YTD": (date(2026, 4, 1), max_d),
    }

    summary = []
    rows = []
    for label, (start, end) in windows.items():
        if start > max_d:
            summary.append(
                {
                    "window": label,
                    "start": str(start),
                    "end": str(end),
                    "status": "empty_future",
                    "eur": 0,
                    "rows": 0,
                }
            )
            continue
        end_eff = min(end, max_d)
        m = _window_mask(sf, start, end_eff)
        g = sf.loc[m]
        eur = float(g["net_sales_value"].sum())
        cov = (
            float(g.loc[g["classified"], "net_sales_value"].sum()) / eur * 100 if eur else None
        )
        summary.append(
            {
                "window": label,
                "start": str(start),
                "end": str(end_eff),
                "status": "ok",
                "eur": round(eur),
                "rows": int(len(g)),
                "coverage_pct": round(cov, 1) if cov is not None else None,
            }
        )
        by_db = (
            g.groupby("distributor_code", dropna=False)["net_sales_value"]
            .sum()
            .sort_values(ascending=False)
        )
        for db, v in by_db.items():
            rows.append(
                {
                    "window": label,
                    "start": str(start),
                    "end": str(end_eff),
                    "distributor_code": db,
                    "net_sales_eur": round(float(v), 2),
                }
            )

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": str(src),
            "basis": "Actual SAP net sales (sales_fact) — billing only, no AIM Qty×PR00 scoring",
            "fiscal_rule": "FY = Apr–Mar (JP/ISZE). FY2025 = 2025-04-01 … 2026-03-31.",
            "max_billing_date": str(max_d),
        },
        "windows": summary,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv(OUT_CSV, index=False)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_CSV} ({len(rows)} rows)")
    for s in summary:
        print(
            f"  {s['window']:12} {s.get('eur', 0):>12,} EUR  "
            f"{s.get('start')} -> {s.get('end')}  cov={s.get('coverage_pct')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
