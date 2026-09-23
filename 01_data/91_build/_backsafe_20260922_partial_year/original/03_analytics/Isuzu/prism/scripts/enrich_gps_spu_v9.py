#!/usr/bin/env python3
"""
Enrich gps_spu_by_distributor.csv with GPS v9 max-spend targets (UIO v18 + study rates).

Run after build_bvp_p4_p5.py. Re-reads uio_v18_gps.json (build via Data/_build/gps_v9_loaders.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import DATA_BUILD_DIR, DERIVED_DIR, GPS_SPU_BY_DB_CSV  # noqa: E402
from modules.bvp_analytics import UIO_OVERRIDES  # noqa: E402

V9_JSON = DATA_BUILD_DIR / "uio_v19_gps.json"
if not V9_JSON.is_file():
    V9_JSON = DATA_BUILD_DIR / "uio_v18_gps.json"


def _traffic_light_v9(capture: float) -> str:
    if pd.isna(capture):
        return "unknown"
    if capture >= 0.85:
        return "green"
    if capture >= 0.50:
        return "amber"
    return "red"


def main() -> None:
    if not GPS_SPU_BY_DB_CSV.exists():
        print("SKIP: gps_spu_by_distributor.csv missing", flush=True)
        return
    if not V9_JSON.exists():
        # Build snapshot on demand
        sys.path.insert(0, str(DATA_BUILD_DIR))
        import gps_v9_loaders as g9  # type: ignore

        g9.main()
        print("Built", V9_JSON, flush=True)

    payload = json.loads(V9_JSON.read_text(encoding="utf-8"))
    dists = payload.get("distributors", {})

    df = pd.read_csv(GPS_SPU_BY_DB_CSV)
    max_spend: list[float | None] = []
    capture_pct: list[float | None] = []
    lights: list[str] = []

    for _, row in df.iterrows():
        db = row["distributor_code"]
        year = int(row["year"])
        d = dists.get(db, {})
        ms = (d.get("max_spend") or {}).get(str(year))
        if ms is None and year == 2025:
            ms = (d.get("max_spend") or {}).get("2025")
        sales = float(row.get("total_sales_eur") or 0)
        max_spend.append(round(float(ms), 2) if ms else None)
        cap = sales / float(ms) if ms and float(ms) > 0 else None
        capture_pct.append(round(cap, 4) if cap is not None else None)
        lights.append(_traffic_light_v9(cap) if cap is not None else row.get("traffic_light", "unknown"))

    df["max_spend_eur"] = max_spend
    df["gps_capture_vs_max"] = capture_pct
    df["traffic_light_v9"] = lights
    df["gps_capture_ex_warranty_vs_max"] = None
    df["traffic_light_v9_ex_warranty"] = None

    # Align 2025 UIO with v18 workbook totals where present (ITUK override kept in pipeline)
    def _uio_total(d: dict, year: int) -> float | None:
        uio_by_year = d.get("uio") or {}
        buckets = uio_by_year.get(year) or uio_by_year.get(str(year))
        if isinstance(buckets, dict):
            return sum(float(v) for v in buckets.values())
        if buckets is not None:
            return float(buckets)
        return None

    for idx, row in df[df["year"] == 2025].iterrows():
        db = row["distributor_code"]
        uio_v9 = _uio_total(dists.get(db, {}), 2025)
        if db in UIO_OVERRIDES:
            o = UIO_OVERRIDES[db]
            df.at[idx, "uio_units"] = int(o["uio_units"])
            df.at[idx, "uio_source"] = o["uio_source"]
            uio_v9 = float(o["uio_units"])
        elif uio_v9:
            df.at[idx, "uio_units"] = int(round(uio_v9))
            if str(row.get("uio_source", "")).startswith("v18"):
                df.at[idx, "uio_source"] = "v18_actual"
        if uio_v9 and row.get("total_sales_eur"):
            df.at[idx, "spend_per_unit_eur"] = round(
                float(row["total_sales_eur"]) / float(uio_v9), 2
            )
        sales = float(df.at[idx, "total_sales_eur"] or 0)
        ms = df.at[idx, "max_spend_eur"]
        if ms and float(ms) > 0:
            cap = sales / float(ms)
            df.at[idx, "gps_capture_vs_max"] = round(cap, 4)
            df.at[idx, "traffic_light_v9"] = _traffic_light_v9(cap)
        sales_ex = df.at[idx, "sales_ex_warranty_eur"]
        if ms and pd.notna(sales_ex) and float(ms) > 0:
            cap_ex = float(sales_ex) / float(ms)
            df.at[idx, "gps_capture_ex_warranty_vs_max"] = round(cap_ex, 4)
            df.at[idx, "traffic_light_v9_ex_warranty"] = _traffic_light_v9(cap_ex)
        if pd.notna(df.at[idx, "sales_ex_warranty_eur"]) and uio_v9:
            df.at[idx, "spend_per_unit_ex_warranty_eur"] = round(
                float(df.at[idx, "sales_ex_warranty_eur"]) / float(uio_v9 or row["uio_units"]), 2
            )

    for idx, row in df.iterrows():
        ms = row.get("max_spend_eur")
        sales_ex = row.get("sales_ex_warranty_eur")
        if ms and pd.notna(sales_ex) and float(ms) > 0:
            cap_ex = float(sales_ex) / float(ms)
            df.at[idx, "gps_capture_ex_warranty_vs_max"] = round(cap_ex, 4)
            df.at[idx, "traffic_light_v9_ex_warranty"] = _traffic_light_v9(cap_ex)

    df.to_csv(GPS_SPU_BY_DB_CSV, index=False)
    n_ms = df["max_spend_eur"].notna().sum()
    print(f"enrich_gps_spu_v9: {len(df)} rows, max_spend on {n_ms} -> {GPS_SPU_BY_DB_CSV}", flush=True)


if __name__ == "__main__":
    main()
