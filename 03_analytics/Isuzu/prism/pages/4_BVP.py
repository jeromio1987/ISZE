"""
PRISM — BVP Intelligence (Genuine vs Best Value Parts)

BVP catalog-wide (8 product groups, ~27 subgroups). Mix scope per distributor =
lifetime Genuine sales via bvp_addressable_basket.csv. Capture / GPS / AIM live on their home pages.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(APP_DIR))

from config import BETA_MODE, COMPETITIVENESS_AUTODOC_RISK_CSV, DERIVED_DIR  # noqa: E402
from modules.bvp_dashboard_data import (  # noqa: E402
    COLOR_BVP,
    COLOR_GENUINE,
    COLOR_TOTAL,
    PILOT_DIST,
    default_group,
    default_subgroup,
    derived_status,
    fmt_eur,
    fmt_pct,
    is_ready,
    load_bvp_bundle,
)
from modules.bvp_product_nav import (  # noqa: E402
    GROUP_ORDER,
    PMS_STRICT_SUBCATEGORIES,
    PRODUCT_GROUPS,
    addressable_subgroups_for,
    filter_mix_addressable,
    groups_for_distributor,
    group_label,
    subcategories_for_group,
    subgroup_label,
)
from modules.bvp_substitution_story import render_substitution_story  # noqa: E402
from modules.ui_links import page_link  # noqa: E402

st.markdown(
    """
<style>
    :root { --isze-blue: #1B3A6B; --isze-orange: #E87722; }
    .bvp-hero {
        background: linear-gradient(120deg, #1B3A6B 0%, #2C5AA0 55%, #E87722 100%);
        padding: 1.25rem 1.5rem; border-radius: 12px; margin-bottom: 1.25rem;
    }
    .bvp-hero h1 { color: #fff !important; margin: 0; font-size: 1.75rem; font-weight: 700; }
    .bvp-hero p { color: #E8F0FA; margin: 0.35rem 0 0; font-size: 0.9rem; }
    .insight-card {
        background: #F8FAFC; border: 1px solid #E2E8F0;
        border-left: 4px solid var(--isze-orange); border-radius: 8px;
        padding: 0.85rem 1rem; margin: 0.5rem 0 1rem; font-size: 0.92rem;
    }
    div[data-testid="metric-container"] {
        border: 1px solid #E0E0E0; border-left: 4px solid #1B3A6B;
        border-radius: 8px; background: #fff;
    }
    [data-testid="stMetricValue"] { color: #1B3A6B; font-weight: 700; }
</style>
""",
    unsafe_allow_html=True,
)

if st.session_state.get("beta_mode", BETA_MODE):
    st.warning("BETA MODE — not for distribution", icon="⚠️")

from modules.plotly_style import BASE_LAYOUT as PLOTLY, style
ISZE_BLUE = "#1B3A6B"

CAPTURE_HELP = """
**PMS capture rate** answers: *of expected service demand, how much did we sell?*

- **Expected units** = UIO (trucks) × service frequency × addressable % × wear factor (by part type).
- **Total capture** = (genuine + BVP units sold) ÷ expected, **capped at 100%**.
- **Genuine capture** = genuine units sold ÷ same expected (can be read as genuine’s share of demand).
- **BVP has no capture rate** — BVP is measured as **mix** (BVP units ÷ genuine + BVP), not vs expected demand.

Charts use the **latest selected year** only so rates stay on a 0–100% scale.
"""


def _finish_chart(fig, title: str, y_pct: bool = True, legend_below: bool = True):
    layout = dict(
        PLOTLY,
        title=dict(text=title, x=0, xanchor="left", font=dict(size=15)),
        margin=dict(l=52, r=28, t=64, b=88 if legend_below else 48),
        xaxis=dict(title=""),
    )
    if y_pct:
        layout["yaxis"] = dict(title="", tickformat=".0%", range=[0, 1.05])
    if legend_below:
        layout["legend"] = dict(orientation="h", yanchor="top", y=-0.28, x=0, font=dict(size=11))
    else:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.04, x=0)
    fig.update_layout(**layout)
    return fig


def _weighted_capture(df_total: pd.DataFrame) -> float | None:
    """Sum(actual) / sum(expected) across rows (same expected per row category)."""
    if df_total.empty:
        return None
    exp = df_total["expected_qty"].sum()
    if exp <= 0:
        return None
    return float(df_total["actual_qty"].sum() / exp)


@st.cache_data(show_spinner="Loading BVP analytics…")
def _load():
    return load_bvp_bundle()


def _years_dists(df, years, dists):
    if df is None or df.empty:
        return df
    out = df.copy()
    if years and "year" in out.columns:
        out = out[out["year"].isin(years)]
    if dists and "distributor_code" in out.columns:
        out = out[out["distributor_code"].isin(dists)]
    return out


def _filter_subgroup(df, group_id, subcats):
    if df is None or df.empty:
        return df
    out = df[df["product_group"] == group_id] if "product_group" in df.columns else df
    sub_col = "product_subgroup" if "product_subgroup" in out.columns else "pms_category"
    if subcats and sub_col in out.columns:
        out = out[out[sub_col].isin(subcats)]
    return out


def _narrative(pms, mix_sub, highlight, group_id, subcats, latest_y) -> str:
    lines = []
    sub_col = "pms_category"
    if not pms.empty and latest_y:
        pc = pms[
            (pms["distributor_code"] == highlight)
            & (pms["year"] == latest_y)
            & (pms["line_type"] == "total")
        ]
        if subcats:
            pc = pc[pc[sub_col].isin(subcats)]
        for _, row in pc.sort_values(sub_col).iterrows():
            lines.append(
                f"**{subgroup_label(row[sub_col])}** total capture **{row['capture_rate']*100:.1f}%** "
                f"({fmt_eur(row['revenue_gap_eur'])} untapped € at avg SP)."
            )
    if not mix_sub.empty and latest_y:
        ms = mix_sub[
            (mix_sub["distributor_code"] == highlight) & (mix_sub["year"] == latest_y)
        ]
        if len(ms) == 1:
            r = ms.iloc[0]
            lines.append(
                f"BVP unit share **{r['bvp_share_units']*100:.1f}%** on "
                f"{subgroup_label(r.get('product_subgroup'))}."
            )
        elif len(ms) > 1:
            lines.append(
                f"Group **{group_label(group_id)}** BVP share ranges "
                f"{ms['bvp_share_units'].min()*100:.0f}–{ms['bvp_share_units'].max()*100:.0f}% "
                f"across selected subcategories."
            )
    return " ".join(lines) if lines else f"Select **{highlight}** and years with data."


bundle = _load()
status = derived_status()

st.markdown(
    """
<div class="bvp-hero">
  <h1>Best Value Parts — Winning the Value Segment</h1>
  <p>How much of the price-sensitive parts business ISZE captures with its own Best Value line, versus losing it to third-party aftermarket.</p>
</div>
""",
    unsafe_allow_html=True,
)

if not is_ready(bundle):
    st.error(
        "Derived BVP files missing. Run (full paths):\n\n"
        "```\n"
        "cd C:\\Users\\jerom\\Desktop\\claude\\ISZE\\03_analytics\\Isuzu\\prism\n"
        "python scripts\\build_sales_fact_from_cy.py\n"
        "python scripts\\build_bvp_p0_p1.py\n"
        "python scripts\\build_bvp_crossref_sales.py\n"
        "python scripts\\build_bvp_p2_mix.py\n"
        "python scripts\\build_bvp_p4_p5.py\n"
        "python scripts\\build_bvp_addressable_basket.py\n"
        "```"
    )
    with st.expander("File status"):
        st.json(status)
    st.stop()

pms_all = bundle["pms_capture"]
years_avail = sorted(pms_all["year"].dropna().astype(int).unique().tolist())
dists_avail = sorted(pms_all["distributor_code"].dropna().unique().tolist())

with st.sidebar:
    st.markdown("### Scope")
    year_sel = st.multiselect("Years", years_avail, default=years_avail[-3:])
    dist_sel = st.multiselect(
        "Distributors",
        dists_avail,
        default=[PILOT_DIST] if PILOT_DIST in dists_avail else dists_avail[:5],
    )
    highlight = st.selectbox(
        "Highlight distributor",
        [PILOT_DIST] + [d for d in dists_avail if d != PILOT_DIST],
    )

    st.markdown("### Product")
    groups_avail = groups_for_distributor(highlight)
    group_labels = {gid: PRODUCT_GROUPS[gid]["label"] for gid in groups_avail}
    default_g = default_group() if default_group() in groups_avail else groups_avail[0]
    group_pick = st.selectbox(
        "Product group",
        groups_avail,
        format_func=lambda g: group_labels[g],
        index=groups_avail.index(default_g),
    )
    subs_all = subcategories_for_group(group_pick)
    addr_sg = addressable_subgroups_for(highlight)
    subs_avail = [s for s in subs_all if not addr_sg or s in addr_sg]
    sub_pick = st.multiselect(
        "Subcategories",
        subs_avail,
        default=subs_avail,
        format_func=subgroup_label,
        help="Filtered to subgroups this distributor can address (lifetime Genuine sales).",
    )
    if not sub_pick:
        sub_pick = subs_avail

    n_addr = len(addr_sg) if addr_sg else 0
    st.caption(
        f"**{highlight}:** {n_addr} addressable subgroups from lifetime Genuine sales. "
        "Capture rates, spend per unit, and AIM risk live on PMS / GPS / AIM Review."
    )
    st.divider()
    for label, ok in status.items():
        st.write(f"{'✅' if ok else '❌'} `{label}`")

latest_y = max(year_sel) if year_sel else None
pms = _filter_subgroup(_years_dists(bundle["pms_capture"], year_sel, dist_sel), group_pick, sub_pick)
mix_sub = filter_mix_addressable(
    _filter_subgroup(
        _years_dists(bundle["mix_subgroup"], year_sel, dist_sel), group_pick, sub_pick
    ),
    highlight,
)
mix_grp = filter_mix_addressable(
    _filter_subgroup(
        _years_dists(bundle["mix_group"], year_sel, dist_sel), group_pick, None
    ),
    highlight,
)
bench_sub = filter_mix_addressable(
    _filter_subgroup(
        _years_dists(bundle["benchmark_subgroup"], year_sel, dist_sel), group_pick, sub_pick
    ),
    highlight,
)
tab_ov, tab_mix, tab_sub, tab_cat, tab_db = st.tabs(
    [
        "Overview",
        "Mix & trends",
        "Substitution story",
        "Catalog",
        "DB mix split",
    ]
)

# ── Overview ──────────────────────────────────────────────────────────────────
with tab_ov:
    with st.expander("What is capture rate?", expanded=False):
        st.markdown(CAPTURE_HELP)

    st.markdown(
        f'<div class="insight-card">{_narrative(pms, mix_sub, highlight, group_pick, sub_pick, latest_y)}</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    ph = pms[(pms["distributor_code"] == highlight) & (pms["year"] == latest_y)] if latest_y else pd.DataFrame()
    if not ph.empty:
        tot = ph[(ph["line_type"] == "total") & (ph["pms_category"].isin(sub_pick))]
        gen = ph[(ph["line_type"] == "genuine") & (ph["pms_category"].isin(sub_pick))]
        cap_tot = _weighted_capture(tot)
        cap_gen = _weighted_capture(gen)
        ms = mix_sub[
            (mix_sub["distributor_code"] == highlight) & (mix_sub["year"] == latest_y)
        ]
        bvp_share = float(ms["bvp_share_units"].mean()) if not ms.empty else None
        c1.metric("Total capture", fmt_pct(cap_tot) if cap_tot is not None else "—")
        c2.metric(
            "Genuine capture",
            fmt_pct(min(cap_gen, 1.0)) if cap_gen is not None else "—",
            help="Genuine units ÷ expected demand (same denominator as total; not capped in source data).",
        )
        c3.metric("BVP unit share", fmt_pct(bvp_share) if bvp_share is not None else "—")
        c4.metric("Untapped € (total)", fmt_eur(tot["revenue_gap_eur"].sum()) if len(tot) else "—")
    else:
        c1.metric("Total capture", "—")
        c2.metric("Genuine capture", "—")
        c3.metric("BVP unit share", "—")
        c4.metric("Untapped € (total)", "—")

    st.caption("Full capture, spend-per-unit, and AIM pricing-risk charts are not repeated here.")
    l1, l2, l3 = st.columns(3)
    with l1:
        page_link("pages/3_PMS.py", "PMS — Capture Rate", "🔧")
    with l2:
        page_link("pages/2_GPS.py", "GPS — Spend per Unit", "📊")
    with l3:
        page_link("pages/network_intelligence.py", "Network Intelligence — AIM & pricing", "💶")

    col_l, col_r = st.columns(2)
    with col_l:
        if not pms.empty and latest_y:
            tot = pms[
                (pms["line_type"] == "total")
                & (pms["year"] == latest_y)
                & (pms["pms_category"].isin(sub_pick))
            ].copy()
            tot["subcategory"] = tot["pms_category"].map(subgroup_label)
            fig = px.bar(
                tot,
                x="subcategory",
                y="capture_rate",
                color="distributor_code",
                barmode="group",
                category_orders={"subcategory": [subgroup_label(s) for s in sub_pick]},
            )
            _finish_chart(fig, f"Total PMS capture — {group_labels[group_pick]} ({latest_y})")
            st.plotly_chart(style(fig), width='stretch')
    with col_r:
        st.caption(
            "Higher BVP share in *contested* categories = good (we captured the value "
            "shopper with our own cheaper line); genuine-only categories have no BVP alternative."
        )
        if not mix_sub.empty:
            mplot = mix_sub.copy()
            mplot["year"] = mplot["year"].astype(int)
            mplot["subcategory"] = mplot["product_subgroup"].map(subgroup_label)
            fig2 = px.line(
                mplot,
                x="year",
                y="bvp_share_units",
                color="subcategory",
                markers=True,
            )
            _finish_chart(fig2, "BVP unit share (mix)")
            st.plotly_chart(style(fig2), width='stretch')

# ── Mix ───────────────────────────────────────────────────────────────────────
with tab_mix:
    view = st.radio("View", ["By subcategory", "Group roll-up"], horizontal=True)

    if view == "By subcategory" and not mix_sub.empty:
        heat = mix_sub.pivot_table(
            index="distributor_code",
            columns="year",
            values="bvp_share_units",
            aggfunc="mean",
        )
        fig_h = px.imshow(
            heat,
            labels=dict(color="BVP share"),
            color_continuous_scale=["#1B3A6B", "#D6E4F0", "#E87722"],
            title=f"BVP share — {group_labels[group_pick]} (selected subcategories)",
        )
        _finish_chart(fig_h, fig_h.layout.title.text, y_pct=False)
        st.plotly_chart(style(fig_h), width='stretch')

        if not bench_sub.empty:
            st.caption(
                "**pp** = percentage points (a gap of +10 pp = 10 points above the network "
                "median, not 10%). Above median in *contested* categories = good."
            )
            b = bench_sub[bench_sub["year"] == bench_sub["year"].max()]
            fig_b = px.bar(
                b.sort_values("vs_network_median_pp"),
                x="vs_network_median_pp",
                y="distributor_code",
                color="product_subgroup",
                orientation="h",
                title="vs network median (pp), latest year",
                labels={"vs_network_median_pp": "pp vs median"},
            )
            fig_b.for_each_trace(lambda t: t.update(name=subgroup_label(t.name)))
            _finish_chart(fig_b, "vs network median BVP mix (pp)", y_pct=False)
            st.plotly_chart(style(fig_b), width='stretch')
    elif not mix_grp.empty:
        mg = mix_grp[mix_grp["product_group"] == group_pick]
        fig_g = px.line(
            mg,
            x="year",
            y="bvp_share_units",
            color="distributor_code",
            markers=True,
            title=f"Group roll-up — {group_labels[group_pick]} (all PMS subcategories)",
        )
        _finish_chart(fig_g, fig_g.layout.title.text)
        st.plotly_chart(style(fig_g), width='stretch')

    flags = mix_sub[mix_sub["substitution_flag"] if "substitution_flag" in mix_sub.columns else pd.Series(False, index=mix_sub.index)]
    if not flags.empty:
        st.warning(f"Substitution signals ({len(flags)} rows)", icon="↔️")
        st.dataframe(
            flags[
                [
                    "year",
                    "distributor_code",
                    "product_subgroup",
                    "bvp_share_units_yoy_pp",
                    "genuine_qty_yoy_pct",
                ]
            ].head(15),
            width='stretch',
            hide_index=True,
        )

# ── Substitution story ────────────────────────────────────────────────────────
with tab_sub:
    render_substitution_story(
        bundle,
        highlight=highlight,
        year_sel=year_sel,
        dist_sel=dist_sel,
        group_pick=group_pick,
        sub_pick=sub_pick,
        latest_y=latest_y,
    )

    st.divider()
    st.markdown("#### Network & pair drill-down")
    st.caption(
        "From `sales_with_crossref.parquet`: sales tied to catalog/registry pairs. "
        "**Both** = genuine and BVP sold in the same year; "
        "**BVP only** = BVP without paired genuine in that year."
    )
    sub_db = bundle.get("substitution_db", pd.DataFrame())
    sub_pair = bundle.get("substitution_pair", pd.DataFrame())

    if sub_db.empty:
        st.warning(
            "Substitution tables missing. Run:\n\n"
            "`python scripts\\build_bvp_crossref_sales.py`"
        )
    else:
        sub_db = _filter_subgroup(_years_dists(sub_db, year_sel, dist_sel), group_pick, sub_pick)
        sub_pair = _filter_subgroup(
            _years_dists(sub_pair, year_sel, dist_sel), group_pick, sub_pick
        )

        if latest_y and not sub_db.empty:
            ly = sub_db[sub_db["year"] == latest_y]
            hi = ly[ly["distributor_code"] == highlight]
            c1, c2, c3, c4 = st.columns(4)
            if not hi.empty:
                c1.metric(
                    "Pairs with sales",
                    f"{int(hi['pairs_with_sales'].sum()):,}",
                )
                c2.metric("Pairs: both sold", f"{int(hi['pairs_both'].sum()):,}")
                c3.metric("Pairs: BVP only", f"{int(hi['pairs_bvp_only'].sum()):,}")
                bvp_q = hi["bvp_qty"].sum() if "bvp_qty" in hi.columns else 0
                tot = hi["total_qty"].sum() if "total_qty" in hi.columns else bvp_q
                c4.metric(
                    "BVP unit share (pairs)",
                    fmt_pct(bvp_q / tot) if tot > 0 else "—",
                )
            else:
                for col in (c1, c2, c3, c4):
                    col.metric("—", "—")

        if not sub_db.empty and latest_y:
            agg_cols = {
                "pairs_with_sales": ("pairs_with_sales", "sum"),
                "pairs_both": ("pairs_both", "sum"),
                "pairs_bvp_only": ("pairs_bvp_only", "sum"),
            }
            if "bvp_qty" in sub_db.columns:
                agg_cols["bvp_qty"] = ("bvp_qty", "sum")
                agg_cols["total_qty"] = ("total_qty", "sum")
            top = (
                sub_db[sub_db["year"] == latest_y]
                .groupby("distributor_code", as_index=False)
                .agg(**agg_cols)
            )
            top["pct_both"] = top["pairs_both"] / top["pairs_with_sales"].replace(0, np.nan)
            top = top.sort_values("pairs_both", ascending=False).head(20)
            fig_sub = px.bar(
                top,
                x="pct_both",
                y="distributor_code",
                orientation="h",
                title=f"Share of active pairs with BOTH genuine + BVP sold ({latest_y})",
                labels={"pct_both": "Pairs with both", "distributor_code": ""},
                color_discrete_sequence=[ISZE_BLUE],
            )
            fig_sub.update_layout(**PLOTLY, xaxis_tickformat=".0%", height=max(320, 22 * len(top)))
            st.plotly_chart(style(fig_sub), width='stretch')

        with st.expander("By subcategory (highlight DB)", expanded=True):
            if latest_y and not sub_db.empty:
                hi_tbl = sub_db[
                    (sub_db["distributor_code"] == highlight) & (sub_db["year"] == latest_y)
                ]
                if "product_subgroup" in hi_tbl.columns:
                    show_cols = [
                        "product_subgroup",
                        "pairs_with_sales",
                        "pairs_both",
                        "pairs_genuine_only",
                        "pairs_bvp_only",
                        "pct_pairs_both",
                        "bvp_share_units",
                    ]
                    if "genuine_qty" in hi_tbl.columns:
                        show_cols.extend(["genuine_qty", "bvp_qty"])
                    tbl = hi_tbl[[c for c in show_cols if c in hi_tbl.columns]].copy()
                    tbl["product_subgroup"] = tbl["product_subgroup"].map(subgroup_label)
                    if "pct_pairs_both" in tbl.columns:
                        tbl["pct_pairs_both"] = tbl["pct_pairs_both"].map(
                            lambda x: f"{x * 100:.0f}%" if pd.notna(x) else "—"
                        )
                    if "bvp_share_units" in tbl.columns:
                        tbl["bvp_share_units"] = tbl["bvp_share_units"].map(
                            lambda x: f"{x * 100:.0f}%" if pd.notna(x) else "—"
                        )
                    st.dataframe(tbl, width='stretch', hide_index=True)

        st.markdown("#### Pair drill-down")
        pat_filter = st.multiselect(
            "Substitution pattern",
            ["both", "genuine_only", "bvp_only"],
            default=["both", "bvp_only"],
            key="sub_pat",
        )
        if not sub_pair.empty and pat_filter:
            drill = sub_pair[sub_pair["substitution_pattern"].isin(pat_filter)]
            if latest_y:
                drill = drill[drill["year"] == latest_y]
            pn_q = st.text_input("Filter pair PN", key="sub_pn_q")
            if pn_q.strip():
                q = pn_q.strip()
                if q.isdigit():
                    q = q.zfill(10)
                drill = drill[
                    drill["xref_genuine_pn"].astype(str).str.contains(q, na=False)
                    | drill["xref_bvp_pn"].astype(str).str.contains(q, na=False)
                ]
            drill_cols = [
                "distributor_code",
                "year",
                "xref_genuine_pn",
                "xref_bvp_pn",
                "product_subgroup",
                "substitution_pattern",
                "genuine_qty",
                "bvp_qty",
                "bvp_share_units",
                "vehicle_model",
            ]
            st.dataframe(
                drill[[c for c in drill_cols if c in drill.columns]].head(400),
                width='stretch',
                hide_index=True,
            )

# ── Catalog (PMS in-scope PNs only) ─────────────────────────────────────────
with tab_cat:
    dim = bundle["dimension"]
    xref = bundle.get("crossref", pd.DataFrame())
    dim_g = dim[dim["product_group"] == group_pick] if "product_group" in dim.columns else dim
    dim_g = dim_g[dim_g["product_subgroup"].isin(sub_pick)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PNs (in scope)", f"{len(dim_g):,}")
    c2.metric("BVP lines", f"{(dim_g['line_type'] == 'bvp').sum():,}")
    c3.metric("Genuine (registry)", f"{(dim_g['line_type'] == 'genuine').sum():,}")
    if not xref.empty and "product_subgroup" in xref.columns:
        xref_g = xref[xref["product_subgroup"].isin(sub_pick)]
        c4.metric("OE↔BVP pairs", f"{len(xref_g):,}")
    else:
        c4.metric("OE↔BVP pairs", "—")

    sub_cat = st.selectbox("Browse subcategory", sub_pick, format_func=subgroup_label, key="cat_sub")
    show = dim_g[dim_g["product_subgroup"] == sub_cat]
    st.dataframe(
        show[["part_number", "line_type", "pms_category", "sheet_source"]].head(250),
        width='stretch',
        hide_index=True,
    )

    st.markdown("#### Genuine ↔ BVP cross-reference")
    if xref.empty:
        st.info(
            "Cross-reference not built. Run "
            "`python scripts\\build_bvp_p0_p1.py` (writes `genuine_bvp_crossref.csv`)."
        )
    else:
        xref_sub = xref[xref["product_subgroup"] == sub_cat].copy()
        st.caption(
            f"{len(xref_sub):,} mapped pairs for **{subgroup_label(sub_cat)}** "
            "(catalog row pairs + ITUK registry supplements)."
        )
        q = st.text_input("Search PN (genuine or BVP)", key="xref_search")
        if q.strip():
            qn = q.strip().lstrip("0").zfill(10) if q.strip().isdigit() else q.strip()
            xref_sub = xref_sub[
                xref_sub["genuine_pn"].str.contains(qn, na=False)
                | xref_sub["bvp_pn"].str.contains(qn, na=False)
            ]
        cols = [
            "genuine_pn",
            "bvp_pn",
            "pair_source",
            "vehicle_model",
            "engine_type",
            "catalog_type",
            "sheet_source",
        ]
        st.dataframe(
            xref_sub[cols].head(500),
            width='stretch',
            hide_index=True,
        )


    st.markdown("#### Autodoc Class C substitution risk")
    st.caption(
        "Competitor min price under 75% of PR00 (scraped sample). "
        "Run `build_competitiveness_autodoc_risk.py`."
    )
    if COMPETITIVENESS_AUTODOC_RISK_CSV.exists():
        ad = pd.read_csv(COMPETITIVENESS_AUTODOC_RISK_CSV)
        st.metric("Flagged PNs (sample)", f"{len(ad):,}")
        show_ad = ad.head(100)
        if "ratio" in show_ad.columns:
            show_ad = show_ad.copy()
            show_ad["ratio_pct"] = (pd.to_numeric(show_ad["ratio"], errors="coerce") * 100).round(0)
        st.dataframe(show_ad, width="stretch", hide_index=True)
    else:
        st.info("Missing competitiveness_autodoc_risk.csv — run the build script after Autodoc scrape.")

st.caption(
    f"BVP Intelligence · PMS in-scope only · Data: `{DERIVED_DIR}` · "
    "Rebuild: `build_bvp_p0_p1.py` -> `build_bvp_crossref_sales.py` -> `build_bvp_p2_mix.py`"
)


# ── DB mix split (absorbed from 13_DB_Parts_Mix.py, IA phase 4) ────────────────
with tab_db:
    MIX_CSV = DERIVED_DIR / "db_parts_mix_classification.csv"
    if not MIX_CSV.exists():
        st.error(f"Missing {MIX_CSV.name}. Run scripts/build_db_parts_classification.py first.")
    else:
        dfmix = pd.read_csv(MIX_CSV)
        mix_years = sorted(dfmix["year"].unique())
        mix_year = st.selectbox("Year", mix_years, index=len(mix_years) - 1, key="dbmix_year")
        dm = dfmix[dfmix["year"] == mix_year].copy()

        net = dm["total_eur"].sum()
        bvp = dm["bvp_eur"].sum()
        contested = dm["contested_eur"].sum()
        k1, k2, k3 = st.columns(3)
        k1.metric("Network parts revenue", f"€{net:,.0f}")
        k2.metric("BVP share of total", f"{bvp / net:.1%}" if net else "—")
        k3.metric("BVP share of contested basket", f"{bvp / contested:.1%}" if contested else "—")

        st.info(
            "**Contested** = genuine parts with a BVP equivalent in the catalogue — "
            "the conquerable basket. **Genuine only** has no BVP alternative. "
            "Non-Isuzu aftermarket brands never touch the invoice and are not shown.",
            icon="ℹ️",
        )

        _BUCKET_COLORS = {
            "BVP": "#E2231A",
            "Genuine (contested)": ISZE_BLUE,
            "Genuine only": "#E87722",
        }
        plot = dm.sort_values("total_eur", ascending=True)
        fig_mix = go.Figure()
        for col, name in (
            ("bvp_pct", "BVP"),
            ("genuine_contested_pct", "Genuine (contested)"),
            ("genuine_only_pct", "Genuine only"),
        ):
            fig_mix.add_bar(
                y=plot["distributor_code"], x=plot[col], name=name,
                orientation="h", marker_color=_BUCKET_COLORS[name],
            )
        fig_mix.update_layout(
            barmode="stack", height=620, title=f"Parts mix per distributor (CY{mix_year})",
            xaxis_title="Share of total parts revenue", xaxis_tickformat=".0%",
            legend_orientation="h", legend_y=-0.12, margin=dict(l=10, r=10, t=50, b=10),
        )
        st.plotly_chart(style(fig_mix), width="stretch")

        dbs = dm.sort_values("total_eur", ascending=False)["distributor_code"].tolist()
        pick = st.selectbox("Distributor", dbs, key="dbmix_dist")
        row = dm[dm["distributor_code"] == pick].iloc[0]
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Parts revenue", f"€{row.total_eur:,.0f}")
        d2.metric("BVP %", f"{row.bvp_pct:.1%}")
        d3.metric("Contested %", f"{row.genuine_contested_pct:.1%}")
        d4.metric(
            "Contested BVP capture",
            f"{row.contested_bvp_capture:.1%}" if pd.notna(row.contested_bvp_capture) else "—",
        )
        donut = px.pie(
            names=["BVP", "Genuine (contested)", "Genuine only"],
            values=[row.bvp_eur, row.genuine_contested_eur, row.genuine_only_eur],
            color=["BVP", "Genuine (contested)", "Genuine only"],
            color_discrete_map=_BUCKET_COLORS, hole=0.55,
        )
        donut.update_layout(height=380, title=f"{pick} — revenue by bucket (CY{mix_year})")
        st.plotly_chart(style(donut), width="stretch")

        st.dataframe(
            dm[
                [
                    "distributor_code", "total_eur", "bvp_pct",
                    "genuine_contested_pct", "genuine_only_pct", "contested_bvp_capture",
                ]
            ].sort_values("total_eur", ascending=False),
            width="stretch", hide_index=True,
        )
