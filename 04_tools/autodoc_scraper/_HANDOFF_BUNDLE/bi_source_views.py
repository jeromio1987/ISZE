"""
Curated BI views for workbook sources — not raw Excel grid dumps.

Used by bi_shell.py tab «Data lineage».
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore

# Sheets that are cover / instructions — never show as default «data»
UIO_RAW_SKIP = frozenset({"Cover", "Charts", "Data Sources", "Assumptions & Mapping"})
PMS_RAW_SKIP = frozenset()


def _num(v: Any) -> float | None:
    try:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_pms_calc_dashboard_coverage(pms_sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """PMS Calc «Dashboard» — current vs FY27 category coverage (%)."""
    raw = pms_sheets.get("Dashboard")
    if raw is None or raw.empty or len(raw) < 8:
        return pd.DataFrame()

    header_row = None
    for i in range(min(15, len(raw))):
        row = raw.iloc[i]
        for j in range(raw.shape[1]):
            cell = str(row.iloc[j]) if pd.notna(row.iloc[j]) else ""
            if "filter" in cell.lower() and "coverage" in cell.lower():
                header_row = i
                break
        if header_row is not None:
            break
    if header_row is None:
        return pd.DataFrame()

    records: list[dict[str, Any]] = []
    for j in range(2, raw.shape[1]):
        label = raw.iloc[header_row, j]
        if pd.isna(label) or not str(label).strip():
            continue
        name = str(label).replace("\n", " ").strip()
        cur = _num(raw.iloc[header_row + 1, j])
        tgt = _num(raw.iloc[header_row + 3, j])
        if cur is None:
            continue
        records.append(
            {
                "category": name,
                "current_pct": round(cur * 100, 2),
                "fy27_target_pct": round(tgt * 100, 2) if tgt is not None else None,
                "gap_pp": round((tgt - cur) * 100, 2) if tgt is not None else None,
            }
        )
    return pd.DataFrame(records)


def parse_pms_dashboard_fleet(pms_sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """N35 / N75 / combined UIO from Dashboard sheet."""
    raw = pms_sheets.get("Dashboard")
    if raw is None or raw.empty:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for i in range(len(raw)):
        metric = str(raw.iloc[i, 1]).strip() if raw.shape[1] > 1 and pd.notna(raw.iloc[i, 1]) else ""
        if not metric or metric == "Metric":
            continue
        if "uio" not in metric.lower() and "potential" not in metric.lower():
            continue
        n35 = _num(raw.iloc[i, 2]) if raw.shape[1] > 2 else None
        n75 = _num(raw.iloc[i, 3]) if raw.shape[1] > 3 else None
        comb = _num(raw.iloc[i, 4]) if raw.shape[1] > 4 else None
        if n35 is None and n75 is None and comb is None:
            continue
        rows.append(
            {
                "metric": metric,
                "N35": n35,
                "N75": n75,
                "Combined": comb,
            }
        )
    return pd.DataFrame(rows)


def _plotly_bar(df: pd.DataFrame, **kwargs: Any) -> None:
    try:
        import plotly.express as px

        fig = px.bar(df, **kwargs)
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.dataframe(df, use_container_width=True, hide_index=True)


def render_source_health_strip(
    paths: dict[str, Path],
    v3: pd.DataFrame,
    uio_sheets: dict[str, pd.DataFrame],
    pms_sheets: dict[str, pd.DataFrame],
    cfg: dict[str, Any],
) -> None:
    """Top KPI strip — files loaded, scale of data."""
    from engine import parse_pms_assumptions, parse_pms_coverage_uio, parse_survival_rates, load_uio_by_distributor
    from sources_loader import parse_ituk_car_park_uio

    defaults = (cfg.get("defaults") or {}) if cfg else {}
    smmt_y = int(defaults.get("ituk_smmt_car_park_year", 2024))

    n_ok = sum(1 for k in ("v3_pn_matrix", "uio_overview", "pms_coverage_calculator", "pms_capture_by_db") if paths.get(k) and paths[k].exists())
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sources ready", f"{n_ok}/4", help="v3 · v17 UIO · PMS Calc · PRISM derived")
    c2.metric("v3 part numbers", f"{len(v3):,}" if not v3.empty else "—")
    car_park, _ = parse_ituk_car_park_uio(uio_sheets, smmt_y, paths) if uio_sheets else (None, "")
    c3.metric("ITUK car park", f"{car_park:,.0f}" if car_park else "—", help="v17 sheet 4 §G (SMMT)")
    pilot = parse_pms_coverage_uio(pms_sheets) if pms_sheets else None
    c4.metric("PMS Calc pilot UIO", f"{pilot:,.0f}" if pilot else "—", help="50% of 5-yr registrations")
    if uio_sheets:
        surv = parse_survival_rates(uio_sheets)
        ubd = load_uio_by_distributor(uio_sheets, surv)
        pan = float(ubd["active_uio"].sum()) if not ubd.empty else None
        c5.metric("Pan-EU active UIO", f"{pan:,.0f}" if pan else "—", help="v17 sheet 1 + survival")
    else:
        c5.metric("Pan-EU active UIO", "—")


def render_v3_portfolio(v3: pd.DataFrame) -> None:
    st.subheader("Parts portfolio (v3 matrix)")
    if v3.empty:
        st.warning("v3 file not found.")
        return

    maint = int((v3["AIM_DemandType"] == "Maintenance").sum()) if "AIM_DemandType" in v3.columns else 0
    wear = int((v3["AIM_DemandType"] == "Wear Repair").sum()) if "AIM_DemandType" in v3.columns else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Total PNs", f"{len(v3):,}")
    c2.metric("Maintenance", f"{maint:,}")
    c3.metric("Wear repair", f"{wear:,}")

    if "AIM_DemandType" in v3.columns:
        mix = v3["AIM_DemandType"].fillna("Unknown").value_counts().reset_index()
        mix.columns = ["Demand type", "PNs"]
        _plotly_bar(
            mix,
            x="PNs",
            y="Demand type",
            orientation="h",
            title="PNs by AIM demand type",
            color="PNs",
            color_continuous_scale=["#0c2461", "#0a6644"],
        )

    with st.expander("Sample PN rows (audit)", expanded=False):
        from bi_display import format_v3_preview

        st.dataframe(format_v3_preview(v3, max_rows=15), use_container_width=True, hide_index=True)


def render_uio_workbook(
    uio_sheets: dict[str, pd.DataFrame],
    paths: dict[str, Path],
    cfg: dict[str, Any],
) -> None:
    st.subheader("UIO & car park (v17 workbook)")
    if not uio_sheets:
        st.warning("v17 UIO file not found.")
        return

    from engine import parse_survival_rates, load_uio_by_distributor
    from sources_loader import parse_ituk_models_car_park, parse_ituk_car_park_uio

    defaults = (cfg.get("defaults") or {}) if cfg else {}
    year = int(defaults.get("ituk_smmt_car_park_year", 2024))
    car_park, label = parse_ituk_car_park_uio(uio_sheets, year, paths)
    if car_park:
        st.metric(label, f"{car_park:,.0f} vehicles")

    models = parse_ituk_models_car_park(uio_sheets, year=year)
    if not models.empty and "car_park_uio" in models.columns:
        top = models.nlargest(12, "car_park_uio").iloc[::-1]
        chart = top.rename(columns={"model": "Model", "car_park_uio": "UIO"})
        _plotly_bar(
            chart,
            x="UIO",
            y="Model",
            orientation="h",
            title=f"ITUK car park by model ({year}A)",
            color="UIO",
            color_continuous_scale=["#0c2461", "#4a7ab8"],
        )

    surv = parse_survival_rates(uio_sheets)
    ubd = load_uio_by_distributor(uio_sheets, surv)
    if not ubd.empty:
        top_d = ubd.nlargest(15, "active_uio").iloc[::-1]
        chart_d = top_d.rename(columns={"Distributor": "Distributor", "active_uio": "Active UIO"})
        _plotly_bar(
            chart_d,
            x="Active UIO",
            y="Distributor",
            orientation="h",
            title="Active UIO by distributor (v17)",
            color="Active UIO",
            color_continuous_scale=["#c05010", "#b52a1c"],
        )
        st.caption("Sheet 1 cohort × survival (sheet 3). ITUK car park for PRISM uses sheet 4 §G, not this total.")

    with st.expander("Raw Excel sheet (audit only)", expanded=False):
        names = [n for n in uio_sheets if n not in UIO_RAW_SKIP]
        if not names:
            names = list(uio_sheets.keys())
        pick = st.selectbox("Sheet", names, index=names.index("4. ITUK UIO Projection") if "4. ITUK UIO Projection" in names else 0, key="uio_raw_sheet")
        from bi_display import format_sheet_preview

        st.dataframe(format_sheet_preview(uio_sheets[pick], max_rows=25), use_container_width=True)


def render_pms_calc_workbook(pms_sheets: dict[str, pd.DataFrame]) -> None:
    st.subheader("PMS Coverage Calculator (ISZE × ISZJ pilot)")
    if not pms_sheets:
        st.warning("PMS Calc file not found.")
        return

    from engine import parse_pms_assumptions, parse_pms_coverage_uio

    cov = parse_pms_calc_dashboard_coverage(pms_sheets)
    fleet = parse_pms_dashboard_fleet(pms_sheets)
    intervals, defaults = parse_pms_assumptions(pms_sheets)
    pilot_uio = parse_pms_coverage_uio(pms_sheets)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Annual mileage", f"{defaults.get('annual_mileage_km', 0):,.0f} km", help=defaults.get("mileage_source", ""))
    c2.metric("Horizon", f"{int(defaults.get('horizon_years', 1))} yr")
    c3.metric("Potential UIO factor", f"{defaults.get('potential_uio_factor', 0.5):.0%}")
    c4.metric("Pilot potential units", f"{pilot_uio:,.0f}" if pilot_uio else "—")

    if not cov.empty:
        st.markdown("##### Coverage vs FY27 targets (workbook Dashboard)")
        long = cov.melt(
            id_vars=["category"],
            value_vars=["current_pct", "fy27_target_pct"],
            var_name="Series",
            value_name="Coverage %",
        )
        long["Series"] = long["Series"].map(
            {"current_pct": "Current", "fy27_target_pct": "FY27 target"}
        )
        _plotly_bar(
            long,
            x="Coverage %",
            y="category",
            color="Series",
            barmode="group",
            orientation="h",
            title="PMS category capture — current vs FY27 target (%)",
        )
        show = cov.rename(
            columns={
                "category": "Category",
                "current_pct": "Current %",
                "fy27_target_pct": "FY27 %",
                "gap_pp": "Gap (pp)",
            }
        )
        st.dataframe(show, use_container_width=True, hide_index=True)

    if not fleet.empty:
        st.markdown("##### Fleet scale (N35 / N75)")
        f_long = fleet.melt(id_vars=["metric"], var_name="Segment", value_name="Units")
        _plotly_bar(
            f_long.dropna(subset=["Units"]),
            x="Units",
            y="metric",
            color="Segment",
            barmode="group",
            orientation="h",
            title="PMS Calc fleet placeholders — update UIO Data sheet",
        )

    if not intervals.empty:
        st.markdown("##### Service intervals (Assumptions)")
        iv = intervals.copy()
        iv["label"] = iv["category"].str.slice(0, 28)
        _plotly_bar(
            iv.sort_values("annual_freq", ascending=True),
            x="annual_freq",
            y="label",
            orientation="h",
            title="Annual service frequency by PMS part type",
            labels={"annual_freq": "Services / vehicle / yr", "label": "Part type"},
        )

    with st.expander("Raw Excel sheet (audit only)", expanded=False):
        pick = st.selectbox("Sheet", list(pms_sheets.keys()), index=list(pms_sheets.keys()).index("Dashboard") if "Dashboard" in pms_sheets else 0, key="pms_raw_sheet")
        from bi_display import format_sheet_preview

        st.dataframe(format_sheet_preview(pms_sheets[pick], max_rows=25), use_container_width=True)


def render_data_lineage_tab(
    paths: dict[str, Path],
    v3: pd.DataFrame,
    uio_sheets: dict[str, pd.DataFrame],
    pms_sheets: dict[str, pd.DataFrame],
    cfg: dict[str, Any],
) -> None:
    """Full «Data lineage» tab — BI visuals, not Cover-sheet grids."""
    st.caption(
        "Source health and workbook insights. **Executive story → PMS results tab** "
        "(lost GP, capture, PRISM, model mix)."
    )
    render_source_health_strip(paths, v3, uio_sheets, pms_sheets, cfg)
    st.markdown("---")
    render_v3_portfolio(v3)
    st.markdown("---")
    render_uio_workbook(uio_sheets, paths, cfg)
    st.markdown("---")
    render_pms_calc_workbook(pms_sheets)
