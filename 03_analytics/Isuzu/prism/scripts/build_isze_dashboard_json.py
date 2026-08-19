#!/usr/bin/env python3
"""
Merge PRISM-derived KPIs into Data/dashboards/isze_data.json for static HTML dashboards.

Run after verify_derived_pipeline.py (or with --force).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PRISM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PRISM_ROOT))

from config import (  # noqa: E402
    AIM_GPS_MATRIX_CSV,
    DASHBOARDS_JSON_DIR,
    DERIVED_DIR,
    GPS_SPU_BY_DB_CSV,
)
from modules.year_coverage import latest_complete_year  # noqa: E402

ISZE_DATA_JSON = DASHBOARDS_JSON_DIR / "isze_data.json"
PMS_CSV = DERIVED_DIR / "pms_capture_by_db_year.csv"
PMS_SUMMARY_CSV = DERIVED_DIR / "pms_summary_by_db.csv"
IML_V7_YAML = PRISM_ROOT / "data" / "iml_v7_ituk_cy2025.yaml"
REPORT_JSON = DERIVED_DIR / "_verification_report.json"


def _load_iml_v7_ituk() -> dict:
    """Model B — IML v7 schedule (ITUK external standard since 2026-07-02)."""
    if not IML_V7_YAML.exists():
        raise SystemExit(f"Missing {IML_V7_YAML}")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(IML_V7_YAML.read_text(encoding="utf-8"))
    except ImportError:
        # Minimal fallback if PyYAML absent
        raw = IML_V7_YAML.read_text(encoding="utf-8")
        import json as _json

        # Pre-serialized constants — keep in sync with yaml
        return _json.loads(
            (PRISM_ROOT / "data" / "iml_v7_ituk_cy2025.json").read_text(encoding="utf-8")
        )


def _build_iml_v7_ituk_block(iml: dict) -> dict:
    cats = []
    for c in iml["categories"]:
        cats.append(
            {
                "category": c["key"],
                "label": c["label"],
                "cover_rate_pct": c["cover_pct"],
                "expected_qty": c["expected_demand"],
                "actual_qty": c["actual_sales"],
                "revenue_gap_eur": c["revenue_gap_eur"],
                "actual_rev_eur": c["actual_rev_eur"],
                "expected_rev_eur": c["expected_rev_eur"],
                "iml_freq_yr": c["freq_yr"],
            }
        )
    oil = next(c for c in cats if c["category"] == "oil_filter")
    h = iml["headline"]
    return {
        "model": "iml_v7",
        "year": iml["year"],
        "uio_dvla": iml["uio_dvla"],
        "scope": iml["scope"],
        "addressable_pct": iml["addressable_pct"],
        "methodology": iml["methodology"],
        "source_workbook": iml["source_workbook"],
        "revenue_gap_eur_sum": h["revenue_gap_eur_sum"],
        "weighted_cover_pct": h["weighted_cover_pct"],
        "oil_filter": {
            "capture_rate_pct": oil["cover_rate_pct"],
            "capture_rate_raw_pct": oil["cover_rate_pct"],
            "expected_qty": oil["expected_qty"],
            "actual_qty": oil["actual_qty"],
            "revenue_gap_eur": oil["revenue_gap_eur"],
        },
        "categories": cats,
    }


def _require_verify_ok(force: bool) -> None:
    if force:
        print("WARNING: --force skips verification gate", flush=True)
        return
    if not REPORT_JSON.exists():
        raise SystemExit(f"Missing {REPORT_JSON} — run verify_derived_pipeline.py first")
    summary = json.loads(REPORT_JSON.read_text(encoding="utf-8")).get("summary", {})
    if not summary.get("ok"):
        raise SystemExit("Verification not green — fix pipeline or pass --force")


def _build_pms_block() -> dict:
    iml = _load_iml_v7_ituk()
    ituk_iml = _build_iml_v7_ituk_block(iml)

    df = pd.read_csv(PMS_CSV)
    totals = df[df["line_type"] == "total"].copy()
    ituk = totals[totals["distributor_code"] == "ITUK"].copy()
    if ituk.empty:
        raise SystemExit("No ITUK rows in pms_capture_by_db_year.csv")

    # Same guard as GPS: year.max() publishes a partial CY2026 as the PRISM lane.
    latest_year = latest_complete_year([int(y) for y in ituk["year"].dropna().unique()])
    yr = ituk[ituk["year"] == latest_year].copy()
    yr = yr.sort_values("pms_category")

    prism_categories = []
    prism_gap_sum = 0.0
    for _, row in yr.iterrows():
        cap = float(row["capture_rate"])
        gap = float(row.get("revenue_gap_eur", 0) or 0)
        prism_gap_sum += gap
        prism_categories.append(
            {
                "category": str(row["pms_category"]),
                "label": str(row.get("category_label", row["pms_category"])),
                "capture_rate_pct": round(min(cap, 1.0) * 100, 1),
                "capture_rate_raw_pct": round(cap * 100, 1),
                "expected_qty": round(float(row["expected_qty"]), 1),
                "actual_qty": round(float(row["actual_qty"]), 1),
                "revenue_gap_eur": round(gap, 0),
            }
        )

    prism_oil = next((c for c in prism_categories if c["category"] == "oil_filter"), None)
    uio = int(yr["uio_units"].iloc[0]) if len(yr) else 22389

    by_db: list[dict] = []
    if PMS_SUMMARY_CSV.exists():
        summ = pd.read_csv(PMS_SUMMARY_CSV)
        if "year" in summ.columns:
            summ = summ[summ["year"] == latest_year]
        for _, row in summ.sort_values("revenue_gap_eur_sum", ascending=False).iterrows():
            code = str(row["distributor_code"])
            entry = {
                "year": latest_year,
                "distributor_code": code,
                "country": str(row.get("country", "")),
                "uio_units": int(row.get("uio_units", 0) or 0),
                "capture_rate_total_wtd_pct": round(float(row["capture_rate_total_wtd"]) * 100, 1),
                "capture_rate_genuine_wtd_pct": round(float(row["capture_rate_genuine_wtd"]) * 100, 1),
                "revenue_gap_eur_sum": round(float(row["revenue_gap_eur_sum"]), 0),
                "oil_filter_capture_pct": round(float(row["oil_filter_capture"]) * 100, 1)
                if pd.notna(row.get("oil_filter_capture"))
                else None,
                "top_gap_categories": str(row.get("top_gap_categories", "")).split("|"),
            }
            if code == "ITUK":
                entry["revenue_gap_eur_sum"] = ituk_iml["revenue_gap_eur_sum"]
                entry["oil_filter_capture_pct"] = ituk_iml["oil_filter"]["capture_rate_pct"]
                entry["capture_rate_total_wtd_pct"] = ituk_iml["weighted_cover_pct"]
                entry["pms_model"] = "iml_v7"
            by_db.append(entry)

    return {
        "methodology": (
            "ITUK: IML v7 service schedule (Model B) — "
            + iml["methodology"]
            + " Network league (other DBs): PRISM registry vs UIO × interval assumptions."
        ),
        "source_file": iml["source_workbook"],
        "prism_source_file": "Data/derived/pms_capture_by_db_year.csv",
        "league_year": latest_year,
        "distributor_count": len(by_db),
        "by_distributor": by_db,
        "ituk": ituk_iml,
        "ituk_prism_lane": {
            "year": latest_year,
            "uio_dvla": uio,
            "revenue_gap_eur_sum": round(prism_gap_sum, 0),
            "oil_filter": prism_oil,
            "categories": prism_categories,
            "note": "Internal network KPI lane only — not IML headline",
        },
    }


def _gps_row_payload(row: pd.Series) -> dict:
    out = {
        "spend_per_unit_eur": round(float(row["spend_per_unit_eur"]), 1),
        "total_sales_eur": round(float(row["total_sales_eur"]), 0),
        "uio_units": int(row.get("uio_units", 0) or 0),
        "traffic_light": str(row.get("traffic_light_v9") or row.get("traffic_light", "")),
        "gps_capture_vs_max_pct": round(float(row["gps_capture_vs_max"]) * 100, 1)
        if pd.notna(row.get("gps_capture_vs_max"))
        else None,
    }
    if pd.notna(row.get("warranty_parts_eur")):
        out["warranty_parts_eur"] = round(float(row["warranty_parts_eur"]), 0)
        out["sales_ex_warranty_eur"] = round(float(row["sales_ex_warranty_eur"]), 0)
        out["spend_per_unit_ex_warranty_eur"] = round(float(row["spend_per_unit_ex_warranty_eur"]), 1)
        out["gps_capture_ex_warranty_vs_max_pct"] = round(
            float(row["gps_capture_ex_warranty_vs_max"]) * 100, 1
        ) if pd.notna(row.get("gps_capture_ex_warranty_vs_max")) else None
        out["traffic_light_ex_warranty"] = str(row.get("traffic_light_v9_ex_warranty", ""))
        out["warranty_data_gap"] = bool(row.get("warranty_data_gap", False))
    return out


def _build_gps_block() -> dict:
    if not GPS_SPU_BY_DB_CSV.exists():
        return {}
    df = pd.read_csv(GPS_SPU_BY_DB_CSV)
    # Latest COMPLETE year, not year.max(). sales_fact gained a partial CY2026
    # (Jan-Mar) on 2026-07-03; year.max() silently published a quarter-year
    # network median (~EUR 48) as the headline annual figure.
    yr = latest_complete_year([int(y) for y in df["year"].dropna().unique()])
    sub = df[df["year"] == yr].copy()
    ituk = sub[sub["distributor_code"] == "ITUK"]
    row = ituk.iloc[0] if not ituk.empty else None
    by_db = [_gps_row_payload(r) | {"distributor_code": str(r["distributor_code"])} for _, r in sub.iterrows()]
    return {
        "year": yr,
        "methodology": "UIO v18 + CY2025 warranty ex-adjustment (claim files); max-spend GPS v9",
        "network_median_spu_eur": round(float(sub["spend_per_unit_eur"].median()), 1),
        "network_median_spu_ex_warranty_eur": round(
            float(sub["spend_per_unit_ex_warranty_eur"].median()), 1
        )
        if "spend_per_unit_ex_warranty_eur" in sub.columns and sub["spend_per_unit_ex_warranty_eur"].notna().any()
        else None,
        "by_distributor": by_db,
        "ituk": None if row is None else _gps_row_payload(row),
    }


def _build_aim_gps_block() -> dict:
    if not AIM_GPS_MATRIX_CSV.exists():
        return {}
    df = pd.read_csv(AIM_GPS_MATRIX_CSV)
    yr = latest_complete_year([int(y) for y in df["year"].dropna().unique()])
    sub = df[df["year"] == yr]
    counts = sub["quadrant"].value_counts().to_dict()
    ituk = sub[sub["distributor_code"] == "ITUK"]
    ituk_row = ituk.iloc[0].to_dict() if not ituk.empty else {}
    return {"year": yr, "quadrant_counts": counts, "ituk": ituk_row}


def main() -> int:
    parser = argparse.ArgumentParser(description="Update isze_data.json from derived CSVs")
    parser.add_argument("--force", action="store_true", help="Skip verification gate")
    args = parser.parse_args()

    _require_verify_ok(args.force)

    payload: dict = {}
    if ISZE_DATA_JSON.exists():
        payload = json.loads(ISZE_DATA_JSON.read_text(encoding="utf-8"))

    meta = payload.setdefault("_meta", {})
    meta["prism_refreshed"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["pms_refreshed"] = meta["prism_refreshed"]
    meta["pms_source"] = "build_isze_dashboard_json.py"

    payload["pms"] = _build_pms_block()
    payload["gps"] = _build_gps_block()
    payload["aim_gps"] = _build_aim_gps_block()

    # Risk cockpit viz (parallel JSON for ISZE_Risk_Cockpit.html)
    try:
        from build_risk_cockpit_viz import build_payload as _risk_payload  # noqa: WPS433

        risk = _risk_payload(force=args.force)
        VIZ_DIR = DASHBOARDS_JSON_DIR / "viz"
        VIZ_DIR.mkdir(parents=True, exist_ok=True)
        (VIZ_DIR / "risk_cockpit.json").write_text(
            json.dumps(risk, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        payload["risk_cockpit"] = risk.get("headline", {})
    except Exception as exc:
        print(f"WARNING: risk_cockpit viz skipped: {exc}", flush=True)

    ISZE_DATA_JSON.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    ISZE_DATA_JSON.write_text(body, encoding="utf-8")
    preload = ISZE_DATA_JSON.with_suffix(".preload.js")
    compact = json.dumps(payload, ensure_ascii=False, allow_nan=True)
    preload.write_text(
        "window.__PRELOADS__ = window.__PRELOADS__ || {};\n"
        f'window.__PRELOADS__["../Data/dashboards/isze_data.json"] = {compact};\n',
        encoding="utf-8",
    )

    pms = payload["pms"]["ituk"]
    prism = payload["pms"].get("ituk_prism_lane") or {}
    print(f"Wrote {ISZE_DATA_JSON}")
    print(f"Wrote {preload}")
    print(
        f"  ITUK {pms['year']} (IML v7): UIO {pms['uio_dvla']:,} | "
        f"gap €{pms['revenue_gap_eur_sum']:,.0f} | "
        f"oil {pms['oil_filter']['capture_rate_raw_pct']}% cover"
    )
    if prism:
        oil = (prism.get("oil_filter") or {}).get("capture_rate_raw_pct")
        print(
            f"  ITUK {prism.get('year')} (PRISM lane): oil {oil}% | "
            f"gap €{prism.get('revenue_gap_eur_sum', 0):,.0f}"
        )
    if payload.get("gps", {}).get("ituk"):
        g = payload["gps"]["ituk"]
        print(f"  GPS ITUK SPU €{g['spend_per_unit_eur']:,.0f} ({g['traffic_light']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
