"""
Sanity checks for PMS engine outputs — used by Streamlit, HTML build, and CLI.

Run:
    python pms_validation.py
"""
from __future__ import annotations

import pandas as pd

MAX_CAPTURE_RATE = 2.0  # 200% — above → data error
MAX_ACTUAL_TO_POTENTIAL = 50.0
MAX_SINGLE_PN_QTY = 500_000


def validate_engine_result(result: dict) -> pd.DataFrame:
    """Return rows: severity (error|warn), check, message."""
    rows: list[dict[str, str]] = []

    if result is None:
        rows.append({"severity": "error", "check": "engine", "message": "No engine result."})
        return pd.DataFrame(rows)

    if "error" in result and not result["error"].empty:
        msg = str(result["error"].iloc[0].get("message", "engine error"))
        rows.append({"severity": "error", "check": "engine", "message": msg})
        return pd.DataFrame(rows)

    kpis = result.get("Summary KPIs", pd.DataFrame())
    cat = result.get("Category lost sales", pd.DataFrame())

    if kpis.empty:
        rows.append({"severity": "error", "check": "kpis", "message": "Summary KPIs missing."})
        return pd.DataFrame(rows)

    k = kpis.iloc[0]
    pot = float(k.get("total_potential_units") or 0)
    act = float(k.get("total_actual_units") or 0)
    cap = k.get("overall_capture_rate")
    src = str(k.get("actual_data_source", ""))

    if "dealer sales" in src.lower():
        rows.append(
            {
                "severity": "info",
                "check": "actuals_source",
                "message": f"Actuals from {src} (ITUK dealer file when present).",
            }
        )

    try:
        cap_f = float(cap) if cap is not None and pd.notna(cap) else None
    except (TypeError, ValueError):
        cap_f = None

    if cap_f is not None and cap_f > MAX_CAPTURE_RATE:
        rows.append(
            {
                "severity": "error",
                "check": "capture_rate",
                "message": (
                    f"Overall capture {cap_f * 100:.1f}% is impossible (>200%). "
                    "Usually dealer-sales qty parse bug or actuals >> potential."
                ),
            }
        )
    elif cap_f is not None and cap_f > 1.0:
        rows.append(
            {
                "severity": "warn",
                "check": "capture_rate",
                "message": f"Capture {cap_f * 100:.1f}% > 100% (over-capture vs PMS potential).",
            }
        )

    if pot > 0 and act / pot > MAX_ACTUAL_TO_POTENTIAL:
        rows.append(
            {
                "severity": "error",
                "check": "actual_vs_potential",
                "message": (
                    f"Actual units {act:,.0f} vs potential {pot:,.0f} "
                    f"(ratio {act / pot:,.0f}×)."
                ),
            }
        )

    if not cat.empty and "actual_units" in cat.columns:
        bad = cat[cat["actual_units"] > cat["potential_units"] * 10]
        if not bad.empty:
            rows.append(
                {
                    "severity": "warn",
                    "check": "category_actuals",
                    "message": (
                        f"{len(bad)} categories with actuals >> potential "
                        f"(e.g. {bad.iloc[0]['category']})."
                    ),
                }
            )

    pn = result.get("PN drill-down", pd.DataFrame())
    if not pn.empty and "actual_units" in pn.columns:
        hi = pn[pn["actual_units"] > MAX_SINGLE_PN_QTY]
        if not hi.empty:
            rows.append(
                {
                    "severity": "error",
                    "check": "pn_qty",
                    "message": (
                        f"{len(hi)} PN(s) with actual_units > {MAX_SINGLE_PN_QTY:,} "
                        f"(top PN {hi.iloc[0].get('PN', '')})."
                    ),
                }
            )

    if not rows:
        rows.append({"severity": "ok", "check": "all", "message": "KPI sanity checks passed."})
    return pd.DataFrame(rows)


def format_capture_pct(capture_rate) -> str:
    """Safe display for HTML/UI."""
    try:
        f = float(capture_rate)
        if pd.isna(f):
            return "—"
        if f > MAX_CAPTURE_RATE:
            return "⚠ data error"
        return f"{f * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def main() -> int:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    from sources_loader import load_sources_config, resolve_paths, load_v3_pn_matrix
    from engine import compute_view
    import openpyxl

    def load_sheets(p):
        if not p or not Path(p).exists():
            return {}
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        return {sh: pd.DataFrame(list(wb[sh].values)) for sh in wb.sheetnames}

    cfg = load_sources_config()
    paths = resolve_paths(cfg)
    v3 = load_v3_pn_matrix(paths)
    uio = load_sheets(paths.get("uio_overview"))
    pms = load_sheets(paths.get("pms_coverage_calculator"))
    r = compute_view(
        v3,
        uio,
        pms,
        pd.DataFrame(),
        market_scope="ITUK (PMS Calc pilot)",
        cfg=cfg,
        paths=paths,
        ituk_uio_source="smmt_car_park",
    )
    v = validate_engine_result(r)
    print(v.to_string(index=False))
    if not r.get("Summary KPIs", pd.DataFrame()).empty:
        k = r["Summary KPIs"].iloc[0]
        print(
            f"\nCapture display: {format_capture_pct(k.get('overall_capture_rate'))} "
            f"(raw {k.get('overall_capture_rate')})"
        )
    return 0 if v[v["severity"] == "error"].empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
