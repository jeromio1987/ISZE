"""
BVP substitution story — narrative, YoY mix, pair drill-down, opportunity €.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.bvp_dashboard_data import COLOR_BVP, COLOR_GENUINE, fmt_eur, fmt_pct
from modules.bvp_product_nav import subgroup_label

ISZE_BLUE = "#1B3A6B"
ISZE_ORANGE = "#E87722"

PLOTLY = dict(
    template="plotly_white",
    font=dict(family="Segoe UI, sans-serif", size=12),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#FAFBFC",
)


def _filter_scope(
    df: pd.DataFrame,
    years: list[int] | None,
    dists: list[str] | None,
    subcats: list[str] | None,
    sub_col: str = "product_subgroup",
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if years and "year" in out.columns:
        out = out[out["year"].isin(years)]
    if dists and "distributor_code" in out.columns:
        out = out[out["distributor_code"].isin(dists)]
    if subcats:
        if sub_col in out.columns:
            out = out[out[sub_col].isin(subcats)]
        elif "pms_category" in out.columns:
            out = out[out["pms_category"].isin(subcats)]
    return out


def _pair_yoy(sub_pair: pd.DataFrame, highlight: str, subcats: list[str]) -> pd.DataFrame:
    """Pair-level YoY: BVP share and qty deltas for highlight distributor."""
    if sub_pair.empty:
        return pd.DataFrame()
    d = sub_pair[sub_pair["distributor_code"] == highlight].copy()
    if subcats and "product_subgroup" in d.columns:
        d = d[d["product_subgroup"].isin(subcats)]
    if d.empty or "year" not in d.columns:
        return pd.DataFrame()

    keys = ["xref_genuine_pn", "xref_bvp_pn", "product_subgroup"]
    d = d.sort_values(keys + ["year"])
    d["prior_year"] = d.groupby(keys)["year"].shift(1)
    d["bvp_share_prior"] = d.groupby(keys)["bvp_share_units"].shift(1)
    d["bvp_qty_prior"] = d.groupby(keys)["bvp_qty"].shift(1)
    d["genuine_qty_prior"] = d.groupby(keys)["genuine_qty"].shift(1)
    d["bvp_share_yoy_pp"] = (d["bvp_share_units"] - d["bvp_share_prior"]) * 100
    d["total_qty"] = d["genuine_qty"] + d["bvp_qty"]
    d["total_qty_prior"] = d["genuine_qty_prior"].fillna(0) + d["bvp_qty_prior"].fillna(0)
    return d


def _story_narrative(
    highlight: str,
    latest_y: int | None,
    opp_y: pd.DataFrame,
    mix_y: pd.DataFrame,
    sub_y: pd.DataFrame,
    subcats: list[str],
) -> str:
    if not latest_y:
        return f"Select years and **{highlight}** to generate the substitution story."

    parts = [f"**{highlight}** · **{latest_y}** · " + ", ".join(subgroup_label(s) for s in subcats[:4])]
    if len(subcats) > 4:
        parts[0] += f" (+{len(subcats) - 4} more)"

    if not opp_y.empty:
        gap_eur = float(opp_y["revenue_gap_eur"].sum())
        tam = float(opp_y["tam_eur"].sum())
        avg_gap_pp = float(opp_y["genuine_bvp_gap_pp"].mean())
        parts.append(
            f"**{fmt_eur(gap_eur)}** revenue gap across categories "
            f"(TAM **{fmt_eur(tam)}**). BVP accounts for **{avg_gap_pp * 100:.1f} pp** "
            f"of captured demand on average (total capture − genuine capture)."
        )

    if not mix_y.empty and "bvp_share_units_yoy_pp" in mix_y.columns:
        mix_y = mix_y.dropna(subset=["bvp_share_units_yoy_pp"])
        if not mix_y.empty:
            up = mix_y[mix_y["bvp_share_units_yoy_pp"] > 2]
            down = mix_y[mix_y["bvp_share_units_yoy_pp"] < -2]
            if not up.empty:
                names = ", ".join(subgroup_label(s) for s in up["product_subgroup"].head(3))
                parts.append(f"BVP mix **up** YoY ({names}).")
            if not down.empty:
                names = ", ".join(subgroup_label(s) for s in down["product_subgroup"].head(3))
                parts.append(f"Genuine regaining share ({names}).")

    if not sub_y.empty:
        pairs = int(sub_y["pairs_with_sales"].sum())
        both = int(sub_y["pairs_both"].sum())
        bvp_only = int(sub_y["pairs_bvp_only"].sum())
        pct_both = both / pairs * 100 if pairs else 0
        parts.append(
            f"**{pairs}** mapped pairs with sales; **{both}** ({pct_both:.0f}%) sold **both** "
            f"genuine and BVP; **{bvp_only}** BVP-only."
        )

    return " ".join(parts)


def render_substitution_story(
    bundle: dict[str, pd.DataFrame],
    *,
    highlight: str,
    year_sel: list[int],
    dist_sel: list[str],
    group_pick: str,
    sub_pick: list[str],
    latest_y: int | None,
) -> None:
    """Substitution story tab body: KPIs, YoY mix, opportunity €, pair table."""
    st.markdown("#### Substitution story")
    st.caption(
        "Genuine→BVP **catalog pairs**, **YoY mix** shift, and **PMS opportunity €** "
        "(same derived pipeline as verify). See `prism/docs/metric_dictionary.md`."
    )

    opp = _filter_scope(bundle.get("pms_opportunity", pd.DataFrame()), year_sel, dist_sel, sub_pick, "pms_category")
    mix = _filter_scope(bundle.get("mix_subgroup", pd.DataFrame()), year_sel, dist_sel, sub_pick)
    if not mix.empty and "product_group" in mix.columns:
        mix = mix[mix["product_group"] == group_pick]

    sub_db = _filter_scope(bundle.get("substitution_db", pd.DataFrame()), year_sel, dist_sel, sub_pick)
    sub_pair = _filter_scope(bundle.get("substitution_pair", pd.DataFrame()), year_sel, dist_sel, sub_pick)
    crossref = bundle.get("crossref", pd.DataFrame())

    if sub_db.empty and sub_pair.empty:
        st.warning(
            "Substitution tables missing. Run:\n\n"
            "`python scripts/build_bvp_crossref_sales.py`"
        )
        return

    prior_y = max((y for y in year_sel if latest_y and y < latest_y), default=None)

    opp_hi = opp[(opp["distributor_code"] == highlight) & (opp["year"] == latest_y)] if latest_y else pd.DataFrame()
    mix_hi = mix[(mix["distributor_code"] == highlight)] if not mix.empty else pd.DataFrame()
    mix_latest = mix_hi[mix_hi["year"] == latest_y] if latest_y and not mix_hi.empty else pd.DataFrame()
    mix_prior = mix_hi[mix_hi["year"] == prior_y] if prior_y and not mix_hi.empty else pd.DataFrame()
    sub_latest = (
        sub_db[(sub_db["distributor_code"] == highlight) & (sub_db["year"] == latest_y)]
        if latest_y and not sub_db.empty
        else pd.DataFrame()
    )

    st.markdown(
        f'<div style="background:#F8FAFC;border-left:4px solid {ISZE_ORANGE};'
        f'padding:0.85rem 1rem;border-radius:8px;margin-bottom:1rem;font-size:0.92rem;">'
        f"{_story_narrative(highlight, latest_y, opp_hi, mix_latest, sub_latest, sub_pick)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── KPIs ──────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        gap = float(opp_hi["revenue_gap_eur"].sum()) if not opp_hi.empty else None
        st.metric("Revenue gap €", fmt_eur(gap) if gap is not None else "—", help="Σ revenue_gap from opportunity matrix")
    with c2:
        if not mix_latest.empty:
            st.metric(
                "BVP unit share",
                fmt_pct(float(mix_latest["bvp_share_units"].mean())),
            )
        else:
            st.metric("BVP unit share", "—")
    with c3:
        if not mix_latest.empty and "bvp_share_units_yoy_pp" in mix_latest.columns:
            yoy = float(mix_latest["bvp_share_units_yoy_pp"].mean())
            st.metric("YoY BVP mix", f"{yoy:+.1f} pp", help="Mean pp change vs prior year in scope")
        else:
            st.metric("YoY BVP mix", "—")
    with c4:
        if not sub_latest.empty:
            st.metric(
                "Pairs: both sold",
                f"{int(sub_latest['pairs_both'].sum())} / {int(sub_latest['pairs_with_sales'].sum())}",
            )
        else:
            st.metric("Pairs: both sold", "—")
    with c5:
        if not opp_hi.empty:
            st.metric(
                "BVP gap (pp)",
                f"{float(opp_hi['genuine_bvp_gap_pp'].mean()) * 100:.1f}",
                help="Capture_total − capture_genuine",
            )
        else:
            st.metric("BVP gap (pp)", "—")

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("##### YoY BVP mix by subcategory")
        if mix_hi.empty:
            st.info("No mix data for selection.")
        else:
            plot_mix = mix_hi.copy()
            plot_mix["label"] = plot_mix["product_subgroup"].map(subgroup_label)
            fig_mix = px.line(
                plot_mix.sort_values(["product_subgroup", "year"]),
                x="year",
                y="bvp_share_units",
                color="label",
                markers=True,
                labels={"bvp_share_units": "BVP unit share", "year": "Year"},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_mix.update_layout(
                **PLOTLY,
                yaxis_tickformat=".0%",
                yaxis_range=[0, 1.05],
                height=380,
                legend=dict(orientation="h", y=-0.25),
            )
            st.plotly_chart(fig_mix, width='stretch')

            if prior_y and not mix_latest.empty and "bvp_share_units_yoy_pp" in mix_latest.columns:
                yoy_df = mix_latest.sort_values("bvp_share_units_yoy_pp")
                fig_yoy = px.bar(
                    yoy_df,
                    x="bvp_share_units_yoy_pp",
                    y=yoy_df["product_subgroup"].map(subgroup_label),
                    orientation="h",
                    color="bvp_share_units_yoy_pp",
                    color_continuous_scale=["#1B3A6B", "#94A3B8", "#E87722"],
                    labels={"bvp_share_units_yoy_pp": "YoY change (pp)"},
                    title=f"BVP mix shift {prior_y} → {latest_y}",
                )
                fig_yoy.update_layout(**PLOTLY, showlegend=False, height=max(260, 36 * len(yoy_df)))
                st.plotly_chart(fig_yoy, width='stretch')

    with col_r:
        st.markdown("##### Opportunity € by category")
        if opp_hi.empty:
            st.info("No opportunity rows for highlight year.")
        else:
            opp_plot = opp_hi.sort_values("revenue_gap_eur", ascending=True).copy()
            opp_plot["label"] = opp_plot["pms_category"].map(subgroup_label)
            fig_opp = go.Figure()
            fig_opp.add_trace(
                go.Bar(
                    y=opp_plot["label"],
                    x=opp_plot["revenue_gap_eur"],
                    name="Revenue gap",
                    marker_color=ISZE_BLUE,
                    orientation="h",
                )
            )
            fig_opp.add_trace(
                go.Bar(
                    y=opp_plot["label"],
                    x=opp_plot["tam_eur"],
                    name="TAM",
                    marker_color="#D6E4F0",
                    orientation="h",
                    opacity=0.55,
                )
            )
            fig_opp.update_layout(
                **PLOTLY,
                barmode="overlay",
                title=f"{highlight} — gap vs TAM ({latest_y})",
                xaxis_tickprefix="€",
                height=380,
                legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(fig_opp, width='stretch')

    # ── Capture vs BVP gap scatter ────────────────────────────────────────────
    if not opp_hi.empty and len(opp_hi) > 1:
        st.markdown("##### Capture vs BVP substitution gap")
        fig_sc = px.scatter(
            opp_hi,
            x="capture_rate_total",
            y="genuine_bvp_gap_pp",
            size="tam_eur",
            color="pms_category",
            hover_name=opp_hi["pms_category"].map(subgroup_label),
            labels={
                "capture_rate_total": "Total PMS capture",
                "genuine_bvp_gap_pp": "BVP share of capture (pp)",
                "tam_eur": "TAM €",
            },
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        fig_sc.update_layout(**PLOTLY, height=360)
        fig_sc.update_xaxes(tickformat=".0%")
        fig_sc.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig_sc, width='stretch')

    # ── Top pairs table ─────────────────────────────────────────────────────────
    st.markdown("##### Top genuine ↔ BVP pairs (latest year)")
    if not latest_y or sub_pair.empty:
        st.info("No pair-level data.")
    else:
        pairs = sub_pair[
            (sub_pair["distributor_code"] == highlight) & (sub_pair["year"] == latest_y)
        ].copy()
        if pairs.empty:
            st.info(f"No pair sales for {highlight} in {latest_y}.")
        else:
            pairs = pairs.sort_values("total_qty", ascending=False).head(40)
            pair_yoy_all = _pair_yoy(sub_pair, highlight, sub_pick)
            if not pair_yoy_all.empty and latest_y:
                py = pair_yoy_all[pair_yoy_all["year"] == latest_y][
                    [
                        "xref_genuine_pn",
                        "xref_bvp_pn",
                        "bvp_share_yoy_pp",
                    ]
                ]
                pairs = pairs.merge(py, on=["xref_genuine_pn", "xref_bvp_pn"], how="left")

            show = pairs[
                [
                    "xref_genuine_pn",
                    "xref_bvp_pn",
                    "product_subgroup",
                    "substitution_pattern",
                    "genuine_qty",
                    "bvp_qty",
                    "bvp_share_units",
                    "total_eur",
                ]
                + (["bvp_share_yoy_pp"] if "bvp_share_yoy_pp" in pairs.columns else [])
            ].copy()
            show["product_subgroup"] = show["product_subgroup"].map(subgroup_label)
            show["bvp_share_units"] = show["bvp_share_units"].map(
                lambda x: f"{x * 100:.0f}%" if pd.notna(x) else "—"
            )
            if "bvp_share_yoy_pp" in show.columns:
                show["bvp_share_yoy_pp"] = show["bvp_share_yoy_pp"].map(
                    lambda x: f"{x:+.1f}" if pd.notna(x) else "—"
                )
            show = show.rename(
                columns={
                    "xref_genuine_pn": "Genuine PN",
                    "xref_bvp_pn": "BVP PN",
                    "product_subgroup": "Category",
                    "substitution_pattern": "Pattern",
                    "genuine_qty": "Genuine qty",
                    "bvp_qty": "BVP qty",
                    "bvp_share_units": "BVP share",
                    "total_eur": "Total €",
                    "bvp_share_yoy_pp": "YoY share (pp)",
                }
            )
            st.dataframe(show, width='stretch', hide_index=True)

            # Stacked qty for top 8 pairs across years
            top_ids = pairs.head(8)[["xref_genuine_pn", "xref_bvp_pn"]]
            trend = sub_pair[sub_pair["distributor_code"] == highlight].merge(
                top_ids, on=["xref_genuine_pn", "xref_bvp_pn"]
            )
            if not trend.empty:
                st.markdown("##### Pair trajectory (top 8 by volume)")
                trend["pair"] = (
                    trend["xref_genuine_pn"].astype(str).str[-6:]
                    + " → "
                    + trend["xref_bvp_pn"].astype(str).str[-6:]
                )
                long = trend.melt(
                    id_vars=["year", "pair"],
                    value_vars=["genuine_qty", "bvp_qty"],
                    var_name="line",
                    value_name="qty",
                )
                long["line"] = long["line"].map(
                    {"genuine_qty": "Genuine", "bvp_qty": "BVP"}
                )
                fig_tr = px.bar(
                    long.sort_values(["pair", "year"]),
                    x="year",
                    y="qty",
                    color="line",
                    facet_col="pair",
                    facet_col_wrap=4,
                    barmode="stack",
                    color_discrete_map={"Genuine": COLOR_GENUINE, "BVP": COLOR_BVP},
                )
                fig_tr.update_layout(**PLOTLY, height=420, showlegend=True)
                st.plotly_chart(fig_tr, width='stretch')

    with st.expander("Crossref catalog (sample)", expanded=False):
        if crossref.empty:
            st.caption("No crossref file.")
        else:
            cr = crossref
            if sub_pick and "product_subgroup" in cr.columns:
                cr = cr[cr["product_subgroup"].isin(sub_pick)]
            st.dataframe(cr.head(50), width='stretch', hide_index=True)
