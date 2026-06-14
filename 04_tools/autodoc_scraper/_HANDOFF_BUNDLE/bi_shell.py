"""
ISZE PMS Intelligence — Streamlit shell (product B in PRODUCT_LOGIC.md).

PMS lost sales / UIO / PRISM: engine.compute_view().
Competitor CSVs: optional tab only — not PMS actuals.
IAM scoring: parent folder only (not this app).

Run:
    cd .../_HANDOFF_BUNDLE
    python -m streamlit run bi_shell.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

SCRIPT_DIR = Path(__file__).parent

try:
    from engine import (
        classify_pms_category,
        compute_view,
        load_uio_by_distributor,
        parse_pms_assumptions,
        parse_survival_rates,
    )
    from sources_loader import (
        load_sources_config,
        resolve_paths,
        load_v3_pn_matrix,
        load_fx_rates,
        parse_ituk_car_park_uio,
        scrape_freshness,
        sanitize_scrape_frame,
        normalize_pn,
    )
    from bi_display import (
        data_mode_banner,
        format_brand_league_scrape,
        format_category_table,
        format_model_summary,
        format_pn_table,
        format_model_detail,
        format_prism_detail,
        format_prism_summary,
        format_scrape_compact,
        format_v3_preview,
    )
    from bi_source_views import render_data_lineage_tab

    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

    def render_data_lineage_tab(*args, **kwargs):
        pass

    def compute_view(*args, **kwargs):
        return None

    def load_sources_config():
        return {}

    def resolve_paths(_cfg):
        return {}

    def load_v3_pn_matrix(_paths):
        return pd.DataFrame()


@st.cache_data(ttl=600)
def _load_excel_sheets(path_str: str) -> dict[str, pd.DataFrame]:
    fp = Path(path_str)
    if not fp.exists():
        return {}
    import openpyxl

    wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
    out = {sh: pd.DataFrame(list(wb[sh].values)) for sh in wb.sheetnames}
    wb.close()
    return out


@st.cache_data(ttl=600)
def load_scraped_competitor_prices() -> pd.DataFrame:
    files = [
        ("AD_UK", "autodoc_results.csv"),
        ("MEK", "mekonomen_results.csv"),
        ("KS", "ks_results.csv"),
    ]
    merged = None
    for prefix, fname in files:
        p = SCRIPT_DIR / fname
        if not p.exists():
            continue
        try:
            df = pd.read_csv(p, dtype={"PN": str}, low_memory=False)
        except Exception:
            continue
        if "PN" not in df.columns:
            continue
        if ENGINE_AVAILABLE:
            df = sanitize_scrape_frame(df)
        else:
            df["PN"] = df["PN"].astype(str).str.zfill(10)
        df = df.rename(columns={c: f"{prefix}__{c}" for c in df.columns if c != "PN"})
        merged = df if merged is None else merged.merge(df, on="PN", how="outer")
    return merged if merged is not None else pd.DataFrame()


def enrich_scrape_for_display(scraped: pd.DataFrame, v3: pd.DataFrame) -> pd.DataFrame:
    """
    Add canonical v3 Description + PMS category (description regex).

    v3 AIM_Category is often wrong for air filters (e.g. 'Fluids Chemicals').
    PMS engine ignores AIM for basket mapping — this tab shows the correct PMS label.
    """
    if scraped.empty:
        return scraped
    out = scraped.copy()
    if not v3.empty and "PN" in v3.columns:
        v3m = v3[["PN", "Description", "AIM_Category", "AIM_DemandType"]].copy()
        v3m["PN"] = v3m["PN"].astype(str).str.zfill(10)
        out["PN"] = out["PN"].astype(str).str.zfill(10)
        out = out.drop(
            columns=[c for c in ("Description", "AIM_Category", "AIM_DemandType") if c in out.columns],
            errors="ignore",
        )
        out = out.merge(v3m, on="PN", how="left")
    desc = out["Description"] if "Description" in out.columns else pd.Series([""] * len(out))
    if ENGINE_AVAILABLE:
        out["pms_category"] = desc.apply(classify_pms_category)
    else:
        out["pms_category"] = None
    if "AIM_Category" in out.columns:
        air_like = desc.astype(str).str.contains(r"air\s+cleaner|air\s+filter|element.*air", case=False, na=False)
        wrong_aim = out["AIM_Category"].astype(str).eq("Fluids Chemicals")
        out["v3_aim_flag"] = np.where(
            air_like & wrong_aim,
            "v3 AIM mis-tag (Fluids) — use pms_category",
            "",
        )
    return out


st.set_page_config(page_title="ISZE PMS Intelligence", page_icon="📊", layout="wide")
st.title("ISZE PMS Intelligence")
st.caption(
    "**PMS product** (engine + PRISM) — not the Autodoc scraper. "
    "Competitor prices = optional tab. IAM = parent `run_dashboard.bat`. "
    "Logic: `PRODUCT_LOGIC.md` · map: `DASHBOARD_MAP.md`."
)
st.markdown(
    "**Open the `PMS results` tab** for KPIs, charts, lost GP, capture, and PRISM. "
    "`Data lineage` shows source health only — not the executive view."
)

cfg = load_sources_config() if ENGINE_AVAILABLE else {}
paths = resolve_paths(cfg) if ENGINE_AVAILABLE and cfg else {}
defaults = (cfg.get("defaults") or {}) if cfg else {}

with st.sidebar:
    st.header("Upgradeable sources")
    st.caption("Edit `sources.yaml` in this folder, then rerun.")
    if paths:
        for key in ("v3_pn_matrix", "uio_overview", "pms_coverage_calculator", "pms_capture_by_db"):
            fp = paths.get(key)
            if fp:
                if fp.exists():
                    st.success(f"✓ {key}")
                else:
                    st.error(f"✗ {key}")
        sales_dir = paths.get("sales_to_dealers_dir")
        if sales_dir and sales_dir.exists():
            st.success("✓ sales_to_dealers_dir")
    if ENGINE_AVAILABLE and paths:
        fx = load_fx_rates(cfg)
        st.caption(f"FX (yaml): GBP→EUR {fx['GBP_EUR']} · SEK→EUR {fx['SEK_EUR']} · as of {fx.get('as_of', '—')}")

    st.markdown("---")
    st.header("PMS scope")

    uio_path = str(paths.get("uio_overview", "")) if paths else ""
    pms_path = str(paths.get("pms_coverage_calculator", "")) if paths else ""
    uio_sheets = _load_excel_sheets(uio_path) if uio_path else {}
    pms_sheets = _load_excel_sheets(pms_path) if pms_path else {}
    _, pms_defaults = (
        parse_pms_assumptions(pms_sheets) if ENGINE_AVAILABLE else (pd.DataFrame(), {})
    )

    dist_list: list[str] = []
    if ENGINE_AVAILABLE and uio_sheets:
        survival = parse_survival_rates(uio_sheets)
        uio_by_dist = load_uio_by_distributor(uio_sheets, survival)
        dist_list = uio_by_dist["Distributor"].tolist() if not uio_by_dist.empty else []

    market_options = ["Pan-European (all distributors)"] + dist_list + ["ITUK (PMS Calc pilot)"]
    market_scope = st.selectbox(
        "Market scope",
        market_options,
        index=0,
        help="Pan-EU or one distributor. ITUK pilot is last — uses UK car park / dealer file.",
    )

    default_ituk_src = defaults.get("ituk_uio_source", "smmt_car_park")
    ituk_uio_source = default_ituk_src
    if market_scope == "ITUK (PMS Calc pilot)":
        st.caption(
            "**Policy:** `smmt_car_park` for PRISM/external alignment · "
            "`pms_calc` for 11,900 fleet exercise only."
        )
        ituk_pick = st.radio(
            "ITUK UIO basis",
            [
                "Car park ~22,389 (v17 sheet 4 / PRISM uio_source)",
                "PMS Calc Step 2 (~11,900 fleet exercise)",
            ],
            index=0 if default_ituk_src == "smmt_car_park" else 1,
        )
        ituk_uio_source = "smmt_car_park" if "22,389" in ituk_pick or "Car park" in ituk_pick else "pms_calc"
        if ENGINE_AVAILABLE:
            smmt_y = int(defaults.get("ituk_smmt_car_park_year", 2024))
            val, lbl = parse_ituk_car_park_uio(uio_sheets, smmt_y, paths)
            if val is not None:
                st.caption(f"**{lbl}:** {val:,.0f} vehicles")
        with st.expander("Diagnostic: v17 sheet 1 cohort (not car park)"):
            if uio_sheets:
                survival = parse_survival_rates(uio_sheets)
                uio_by_dist_preview = load_uio_by_distributor(uio_sheets, survival)
                ituk_row = uio_by_dist_preview[uio_by_dist_preview["Distributor"] == "ITUK"]
                if not ituk_row.empty:
                    st.caption(f"Sheet 1 ITUK: **{float(ituk_row['active_uio'].sum()):,.0f}** — do not use for PRISM letters.")
                ituk_uio_diag = st.checkbox("Use sheet 1 for engine run", value=False)
                if ituk_uio_diag:
                    ituk_uio_source = "v17_survival"

    distributor = None
    if market_scope not in (
        "ITUK (PMS Calc pilot)",
        "Pan-European (all distributors)",
    ):
        distributor = market_scope

    yaml_defaults = (cfg.get("defaults") or {}) if cfg else {}
    isze_gp_pct = float(yaml_defaults.get("isze_gp_pct", 0.35))
    st.caption(
        "**Lost GP €** = lost units × PR00 × **GP%**. "
        "ITUK: GP% from `ITUK_Parts_Sales_Classification` (Margin % column). "
        f"Fallback: {isze_gp_pct * 100:.0f}% in `sources.yaml`. "
        "`Sales to Dealers_ITUK` = **qty only** (no cost/turnover). Not DB margin."
    )
    cfg_horizon = int(float(yaml_defaults.get("horizon_years", 1)))
    sheet_horizon = int(float(pms_defaults.get("horizon_years", 1)))
    horizon_default = min(cfg_horizon, sheet_horizon) if cfg_horizon >= 1 else 1
    horizon_years = st.slider(
        "Horizon (years)",
        1,
        5,
        horizon_default,
        1,
        help="Potential demand = UIO × frequency × this many years. Use **1** for annual steering; PMS Calc workbook may use 5.",
    )
    pms_basket = st.selectbox(
        "PMS basket",
        [
            "Maintenance + Wear Repair (PMS pilot)",
            "Maintenance (AIM_DemandType)",
            "All mapped PNs (any demand type)",
        ],
        index=0,
    )

    st.markdown("---")
    st.header("Period & year")
    period_type = st.radio("Period", ["CY", "FY"], horizontal=True, index=0)
    sales_year = st.selectbox("Year", [2025, 2024, 2023], index=0)
    pms_data_mode = st.selectbox(
        "Multi-DB actuals",
        [
            "auto (PRISM derived if available)",
            "prism (force PRISM derived)",
            "computed (v17 UIO + v3 qty)",
        ],
        index=0,
        help="All distributors tab. PRISM file: Data/derived/pms_capture_by_db_year.csv",
    )
    data_mode_key = pms_data_mode.split()[0]

    st.markdown("---")
    st.caption(
        f"Mileage: {pms_defaults.get('annual_mileage_km', '—'):,.0f} km/yr — "
        f"{pms_defaults.get('mileage_source', 'PMS Calc')}\n\n"
        f"Potential UIO factor: {pms_defaults.get('potential_uio_factor', 0.5):.0%}"
    )

tab_engine, tab_scraped, tab_data = st.tabs(
    ["PMS results", "Competitor prices (optional)", "Data lineage"]
)

v3 = load_v3_pn_matrix(paths) if paths else pd.DataFrame()

with tab_data:
    if ENGINE_AVAILABLE:
        render_data_lineage_tab(paths, v3, uio_sheets, pms_sheets, cfg)
    else:
        st.warning("Engine modules not loaded — cannot render source views.")

with tab_scraped:
    scraped = load_scraped_competitor_prices()
    v3_preview = load_v3_pn_matrix(paths) if paths else pd.DataFrame()
    scraped_view = enrich_scrape_for_display(scraped, v3_preview)
    st.subheader("Competitor price scrapes (layer C)")
    st.caption(
        "Optional Autodoc / KS / Mekonomen CSVs. **Does not drive PMS actuals or PRISM capture.** "
        "**PMS category** = description regex (same as PMS results tab). "
        "**v3 AIM_Category** in scrape files can be wrong (e.g. air filter → Fluids Chemicals)."
    )
    if scraped.empty:
        st.info("No scraper CSVs in bundle. PMS engine tab works without them.")
    else:
        st.metric("PNs in scrape files", f"{len(scraped):,}")
        if "v3_aim_flag" in scraped_view.columns:
            n_flag = (scraped_view["v3_aim_flag"].astype(str).str.len() > 0).sum()
            if n_flag:
                st.warning(
                    f"**{n_flag}** PN(s) have v3 AIM_Category mis-tagged (air/cabin vs Fluids). "
                    "Use **pms_category** column — PMS engine already does."
                )
        if ENGINE_AVAILABLE and paths:
            fresh = scrape_freshness(paths, SCRIPT_DIR, int(defaults.get("scrape_max_age_days", 90)))
            if not fresh.empty:
                worst = fresh.loc[fresh["age_days"].idxmax()]
                st.caption(
                    f"Latest file date (informational): {worst['file']} · {worst['latest_scrape']} "
                    f"({int(worst['age_days'])} days ago)"
                )
        st.dataframe(
            format_scrape_compact(scraped_view),
            use_container_width=True,
            hide_index=True,
        )

with tab_engine:
    if not ENGINE_AVAILABLE:
        st.warning("`engine.py` not found.")
    else:
        with st.spinner("Computing PMS view..."):
            v3_path = paths.get("v3_pn_matrix") if paths else None
            v3_df = load_v3_pn_matrix(paths) if paths else pd.DataFrame()
            if v3_df.empty and v3_path and v3_path.exists():
                v3_df = pd.read_excel(v3_path, sheet_name="PN_Price_Matrix", dtype={"PN": str})
                v3_df["PN"] = v3_df["PN"].astype(str).str.zfill(10)

            result = compute_view(
                v3=v3_df,
                uio_sheets=uio_sheets,
                pms_sheets=pms_sheets,
                scraped=load_scraped_competitor_prices(),
                market_scope=market_scope,
                distributor=distributor,
                isze_gp_pct=isze_gp_pct,
                horizon_years=float(horizon_years),
                pms_basket=pms_basket,
                period_type=period_type,
                sales_year=int(sales_year),
                cfg=cfg,
                paths=paths,
                pms_data_mode=data_mode_key,
                ituk_uio_source=ituk_uio_source,
            )

        if result is None:
            st.info("Engine returned no data.")
        elif "error" in result:
            st.error(result["error"].iloc[0]["message"])
        else:
            validation = result.get("Validation", pd.DataFrame())
            if validation is not None and not validation.empty:
                for _, vr in validation.iterrows():
                    sev = str(vr.get("severity", ""))
                    msg = str(vr.get("message", ""))
                    if sev == "error":
                        st.error(f"**Data check:** {msg}")
                    elif sev == "warn":
                        st.warning(f"**Data check:** {msg}")
            kpis = result.get("Summary KPIs", pd.DataFrame())
            cat = result.get("Category lost sales", pd.DataFrame())
            pn = result.get("PN drill-down", pd.DataFrame())
            brands = result.get("Brand league", pd.DataFrame())

            if not kpis.empty:
                src = str(kpis.iloc[0].get("actual_data_source", ""))
                if market_scope == "ITUK (PMS Calc pilot)" and "dealer sales" not in src:
                    st.warning(
                        "ITUK: using pan-ISZE v3 qty — drop `Sales to Dealers_ITUK_CY{year}.xlsx` "
                        "in Isuzu folder (see sources.yaml) for dealer-level actuals."
                    )
                if period_type == "FY":
                    st.info(
                        "FY: v3 has CY columns only. Multi-DB uses PRISM derived; single-DB uses dealer file when present."
                    )

            if not kpis.empty:
                k = kpis.iloc[0]
                gp_src = str(k.get("gp_source", "") or "").strip()
                if gp_src:
                    st.caption(f"**GP basis:** {gp_src}")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("UIO scope", f"{k.get('total_uio', 0):,.0f}", help=k.get("scope_label", ""))
                c2.metric("PMS PNs", f"{int(k.get('pms_pns', 0)):,}")
                c3.metric("Lost ISZE GP €/yr", f"€{k.get('total_lost_gp', 0):,.0f}")
                c4.metric("Lost units/yr", f"{k.get('total_lost_units', 0):,.0f}")
                cap = k.get("overall_capture_rate")
                try:
                    from pms_validation import format_capture_pct

                    cap_disp = format_capture_pct(cap)
                except ImportError:
                    cap_disp = (
                        f"{float(cap) * 100:.1f}%"
                        if cap is not None and pd.notna(cap)
                        else "—"
                    )
                c5.metric("Overall capture", cap_disp)
                try:
                    cap_f = float(cap) if cap is not None and pd.notna(cap) else None
                except (TypeError, ValueError):
                    cap_f = None
                lost_gp_k = float(k.get("total_lost_gp", 0) or 0)
                if cap_f is not None and cap_f < 0.05 and lost_gp_k > 500_000:
                    st.warning(
                        f"Very low capture ({cap_disp}) with large lost GP — check **Horizon** (use 1 yr for annual view) "
                        "and **Market scope** actuals (ITUK dealer file vs pan-ISZE v3 qty)."
                    )

            pms_multi_sum = result.get("PMS by distributor (summary)", pd.DataFrame())
            pms_multi_det = result.get("PMS by distributor (detail)", pd.DataFrame())
            pms_mode_df = result.get("data_mode", pd.DataFrame())

            pms_model_sum = result.get("PMS by model (summary)", pd.DataFrame())
            pms_model_det = result.get("PMS by model (detail)", pd.DataFrame())
            pms_model_carpark = result.get("ITUK car park by model", pd.DataFrame())
            pms_model_note = result.get("PMS by model (note)", pd.DataFrame())

            sub_overview, sub_cat, sub_model, sub_pn, sub_brand, sub_multidb, sub_meta = st.tabs(
                [
                    "Overview",
                    "By category",
                    "By model",
                    "By PN",
                    "Competitor brands",
                    "PRISM all distributors",
                    "Methodology",
                ]
            )

            with sub_overview:
                if market_scope.startswith("ITUK"):
                    st.caption(
                        "ITUK engine: potential = UIO × PMS frequency × horizon. "
                        "PRISM tab uses different rules (often N75_only) — compare **capture %**, not unit totals."
                    )
                if cat.empty:
                    st.info("No PMS categories matched — check PN description mapping.")
                else:
                    try:
                        import plotly.express as px

                        disp = cat.copy()
                        disp["capture_pct"] = disp["capture_rate"] * 100
                        fig = px.bar(
                            disp.iloc[::-1],
                            y="category",
                            x="lost_isze_gp",
                            orientation="h",
                            color="capture_pct",
                            color_continuous_scale=["#b52a1c", "#c05010", "#0a6644"],
                            range_color=[0, 50],
                            labels={
                                "lost_isze_gp": "Lost ISZE GP €",
                                "capture_pct": "Capture %",
                            },
                        )
                        fig.update_layout(
                            height=420,
                            plot_bgcolor="white",
                            paper_bgcolor="white",
                            title="Lost ISZE GP by PMS category",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        st.dataframe(cat, use_container_width=True, hide_index=True)

                    st.markdown("##### Biggest leaks")
                    for _, r in cat.head(3).iterrows():
                        st.markdown(
                            f"**{r['category']}** — €{r['lost_isze_gp']:,.0f} lost GP · "
                            f"{r['capture_rate'] * 100:.1f}% capture"
                        )

            with sub_cat:
                if not cat.empty:
                    st.dataframe(
                        format_category_table(cat),
                        use_container_width=True,
                        hide_index=True,
                    )

            with sub_model:
                st.subheader("PMS by model (ITUK car park)")
                tracker = SCRIPT_DIR / "MODEL_REFINEMENT_TRACKER.xlsx"
                st.caption(
                    f"Refinement workbook: `{tracker.name}` · regenerate: "
                    "`python scripts/build_model_refinement_sheet.py`"
                )
                if not pms_model_note.empty and "message" in pms_model_note.columns:
                    st.info(pms_model_note.iloc[0]["message"])
                if not market_scope.startswith("ITUK"):
                    st.warning(
                        "Sidebar scope is not ITUK — category totals below are proportional "
                        "to ITUK model mix only. Set scope to **ITUK (PMS Calc pilot)** for aligned leaks."
                    )
                if pms_model_carpark.empty:
                    st.warning("No v17 sheet 4 §G model rows — check `uio_overview` path.")
                else:
                    cp = pms_model_carpark.copy()
                    if "pct_of_ituk_total" in cp.columns:
                        cp["pct_of_ituk_total"] = (cp["pct_of_ituk_total"] * 100).round(1)
                    st.markdown("##### Car park by model (2024A)")
                    cp_show = cp[
                        [
                            c
                            for c in (
                                "model",
                                "tonnage_class",
                                "car_park_uio",
                                "pct_of_ituk_total",
                                "recommended_km_yr",
                            )
                            if c in cp.columns
                        ]
                    ].rename(
                        columns={
                            "model": "Model",
                            "tonnage_class": "Class",
                            "car_park_uio": "UIO",
                            "pct_of_ituk_total": "% of ITUK",
                            "recommended_km_yr": "Rec. km/yr",
                        }
                    )
                    st.dataframe(cp_show, use_container_width=True, hide_index=True)

                if pms_model_sum.empty:
                    st.info("No model allocation — run engine with ITUK scope and PMS categories.")
                else:
                    try:
                        import plotly.express as px

                        top = pms_model_sum.head(12).iloc[::-1]
                        fig_m = px.bar(
                            top,
                            y="model",
                            x="lost_isze_gp",
                            orientation="h",
                            color="capture_rate",
                            color_continuous_scale=["#b52a1c", "#0a6644"],
                            labels={
                                "lost_isze_gp": "Allocated lost GP €",
                                "capture_rate": "Capture rate",
                            },
                            title="Allocated lost ISZE GP by model (UIO share)",
                        )
                        fig_m.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white")
                        st.plotly_chart(fig_m, use_container_width=True)
                    except ImportError:
                        pass
                    st.markdown("##### Summary by model")
                    st.dataframe(
                        format_model_summary(pms_model_sum),
                        use_container_width=True,
                        hide_index=True,
                    )

                    with st.expander("Model × category detail (optional)", expanded=False):
                        models = (
                            sorted(pms_model_det["model"].dropna().unique().tolist())
                            if not pms_model_det.empty
                            else []
                        )
                        mfilter = st.selectbox(
                            "Model",
                            ["(all)"] + models,
                            key="pms_model_filter",
                        )
                        det_m = pms_model_det
                        if mfilter != "(all)" and not det_m.empty:
                            det_m = det_m[det_m["model"] == mfilter]
                        if not det_m.empty:
                            st.dataframe(
                                format_model_detail(det_m.head(50)),
                                use_container_width=True,
                                hide_index=True,
                            )
                    st.caption(
                        "Allocated actuals are proportional until PN×model mapping exists. "
                        "PRISM N75 capture remains on **All distributors** tab."
                    )

            with sub_pn:
                if pn.empty:
                    st.info("No PN rows.")
                else:
                    cat_filter = st.selectbox(
                        "Category",
                        ["(all)"] + sorted(pn["category"].dropna().unique().tolist()),
                        key="pn_cat_filter",
                    )
                    search = st.text_input("Search PN / description", "")
                    dview = pn.copy()
                    if cat_filter != "(all)":
                        dview = dview[dview["category"] == cat_filter]
                    if search:
                        m = dview["PN"].str.contains(search, case=False, na=False) | dview[
                            "Description"
                        ].str.contains(search, case=False, na=False)
                        dview = dview[m]
                    st.dataframe(
                        format_pn_table(dview).head(100),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.caption(f"Top {min(len(dview), 100)} of {len(dview)} PNs by lost GP.")

            with sub_brand:
                if brands is None or brands.empty:
                    st.caption("No competitor brands in scraped data yet.")
                else:
                    st.dataframe(
                        format_brand_league_scrape(brands),
                        use_container_width=True,
                        hide_index=True,
                    )

            with sub_multidb:
                st.subheader(f"PRISM — all distributors — {period_type} {sales_year}")
                st.info(
                    "PRISM `expected_qty` is usually **N75_only**. "
                    "Do not compare unit potentials to the ITUK engine tab — use capture % and lost GP trends."
                )
                banner = data_mode_banner(pms_mode_df)
                if banner:
                    st.info(banner)

                if pms_multi_sum.empty:
                    st.info("No multi-DB rows. Check `pms_capture_by_db` in sources.yaml.")
                else:
                    prism_view = format_prism_summary(pms_multi_sum)
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Distributors", f"{len(prism_view):,}")
                    if "Lost GP (€)" in prism_view.columns:
                        c2.metric(
                            "Total lost GP",
                            f"€{prism_view['Lost GP (€)'].sum():,.0f}",
                        )
                    if "Capture %" in prism_view.columns:
                        w = prism_view["Capture %"].dropna()
                        c3.metric(
                            "Median capture",
                            f"{w.median():.1f}%" if len(w) else "—",
                        )
                    if "Scope" in prism_view.columns:
                        scopes = prism_view["Scope"].dropna().unique()
                        c4.metric("PRISM scope", scopes[0] if len(scopes) == 1 else "mixed")

                    try:
                        import plotly.express as px

                        top_db = prism_view.head(15).iloc[::-1]
                        fig_p = px.bar(
                            top_db,
                            y="Distributor",
                            x="Lost GP (€)",
                            orientation="h",
                            color="Capture %",
                            color_continuous_scale=["#b52a1c", "#0a6644"],
                            title="Top distributors by lost GP (PRISM)",
                        )
                        fig_p.update_layout(height=420, plot_bgcolor="white", paper_bgcolor="white")
                        st.plotly_chart(fig_p, use_container_width=True)
                    except ImportError:
                        pass

                    st.markdown("##### Ranked summary (top 18)")
                    st.dataframe(prism_view.head(18), use_container_width=True, hide_index=True)
                    if len(prism_view) > 18:
                        st.caption(f"{len(prism_view) - 18} more distributors — use expander below for category drill-down.")

                    with st.expander("Category breakdown — pick one distributor", expanded=False):
                        dist_list = (
                            sorted(pms_multi_det["distributor"].dropna().unique().tolist())
                            if not pms_multi_det.empty
                            else []
                        )
                        if not dist_list:
                            st.caption("No detail rows.")
                        else:
                            pick = st.selectbox("Distributor", dist_list, key="prism_dist_pick")
                            det = pms_multi_det[pms_multi_det["distributor"] == pick]
                            st.dataframe(
                                format_prism_detail(det),
                                use_container_width=True,
                                hide_index=True,
                            )

            with sub_meta:
                st.markdown("##### Upgrade checklist")
                st.markdown(
                    """
- **New UIO file** → update `uio_overview` in `sources.yaml`
- **New PMS parts / intervals** → edit `pms_parts_config.yaml` or PMS Calc Assumptions
- **Distributor sales** → add `Sales to Dealers_{DB}_CY{year}.xlsx` under `sales_to_dealers_dir`
- **All-DB actuals** → refresh `Data/derived/pms_capture_by_db_year.csv` (PRISM `run_pipeline_and_verify.ps1`)
                    """
                )
                if "data_mode" in result and not result["data_mode"].empty:
                    b = data_mode_banner(result["data_mode"])
                    if b:
                        st.markdown(f"**Data source:** {b}")
                for key in ("PMS intervals (from source)", "UIO by distributor"):
                    if key in result and isinstance(result[key], pd.DataFrame) and not result[key].empty:
                        st.subheader(key)
                        if key == "PMS intervals (from source)":
                            slim = result[key][
                                [
                                    c
                                    for c in (
                                        "category",
                                        "interval_km",
                                        "parts_per_service",
                                        "annual_freq",
                                    )
                                    if c in result[key].columns
                                ]
                            ]
                            st.dataframe(slim, use_container_width=True, hide_index=True)
                        elif key == "UIO by distributor":
                            st.dataframe(
                                result[key].head(20),
                                use_container_width=True,
                                hide_index=True,
                            )
                unmapped = result.get("Unmapped PMS PNs", pd.DataFrame())
                if unmapped is not None and not unmapped.empty:
                    st.subheader("Unmapped PMS PNs (regex gap)")
                    st.caption(f"{len(unmapped)} rows — excluded from category totals")
                    slim_um = unmapped[
                        [c for c in ("PN", "Description", "category") if c in unmapped.columns]
                    ].head(30)
                    st.dataframe(slim_um, use_container_width=True, hide_index=True)
                    if len(unmapped) > 30:
                        st.caption(f"Showing 30 of {len(unmapped)} unmapped PNs.")
                st.markdown(
                    """
**ITUK tab (engine):** potential = UIO × annual_pieces_per_vehicle × horizon (PMS Calc Assumptions).  
**All distributors (PRISM):** potential = `expected_qty` from CSV — scope usually **N75_only**.  
**Do not compare** these potentials on the same chart.

Classification: description regex for axle-level brakes (see SPEC § Decisions); AIM_Category alone cannot split front/rear.

**Sources:** `sources.yaml`, PMS Calc, v17 UIO sheet 4 (car park), PRISM derived, dealer sales files. Scraper CSVs optional (`SCRAPE_OPTIONAL.md`).
                    """
                )
