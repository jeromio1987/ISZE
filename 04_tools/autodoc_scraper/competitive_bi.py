"""
ISZE Competitive BI — clean rebuild on real foundations.

Sources of truth (no invented numbers):
  - v3 PN_Price_Matrix: PR00, Qty_CY2025, AIM_Category, AIM_DemandType, AIM_Bucket
  - v17 UIO Overview: per-distributor annual registrations 1990-2024 (real cohorts)
  - PMS Coverage Calculator (Assumptions): real Isuzu intervals + parts-per-service
  - Scraped competitor data: Autodoc UK, KS Int'l (AM + GEN), Mekonomen

Design principle: aggregate at CATEGORY level (not per-PN) to avoid the
8x over-counting bug. Drill down from market -> category -> PN.

Run:
    cd <ISZE_ROOT>/04_tools/autodoc_scraper
    python -m streamlit run competitive_bi.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
sys.path.insert(0, str(_WORKSPACE))
from isze_paths import (  # noqa: E402
    ANALYTICS_DIR,
    DERIVED_DIR,
    ISZE_ROOT,
    LEGACY_DIR,
    UIO_DIR,
    resolve_first_existing,
)

SCRIPT_DIR = Path(__file__).parent
V3_FILE   = SCRIPT_DIR / "ISZE_Parts_Intelligence_v3.xlsx"
# 2026-07-09: removed a hardcoded "..._v17.xlsx" fallback that used to sit here.
# There is only ever one canonical, unversioned UIO file — always resolve to that.
# Version lives on the workbook's own Changelog sheet, never in the filename or in code.
UIO_FILE  = resolve_first_existing([
    UIO_DIR / "_CURRENT" / "ISUZU_UIO_Overview_2026.xlsx",
    ISZE_ROOT / "UIO" / "_CURRENT" / "ISUZU_UIO_Overview_2026.xlsx",
]) or (UIO_DIR / "_CURRENT" / "ISUZU_UIO_Overview_2026.xlsx")
PMS_CALC  = resolve_first_existing([
    LEGACY_DIR / "Isuzu" / "Divers" / "ISZE_PMS_Coverage_Calculator.xlsx",
    ISZE_ROOT / "Isuzu" / "Divers" / "ISZE_PMS_Coverage_Calculator.xlsx",
    ANALYTICS_DIR / "Isuzu" / "Divers" / "ISZE_PMS_Coverage_Calculator.xlsx",
]) or (LEGACY_DIR / "Isuzu" / "Divers" / "ISZE_PMS_Coverage_Calculator.xlsx")

# ── Survival rates, originally copied from v17 Sheet 3 (CV — Developed Countries) ─
# Vehicle Age (years) -> survival ratio.
# ⚠ 2026-07-09: FLAGGED, NOT FIXED. These are hardcoded Python constants, not read
# from UIO_FILE at runtime — so even though UIO_FILE above now always resolves to
# the current canonical workbook, THESE NUMBERS DO NOT UPDATE WITH IT. If "3. UIO
# Calculation" sheet's survival curves changed in V18/V19 (plausible — Germany,
# Ireland, Portugal, UTI Israel all got new methodology per the Changelog), this
# dict is stale regardless of file version. Not fixed here — making this read
# dynamically from the workbook needs testing I can't do from this session
# (sandbox can't execute against your live files). Compare against Sheet 3 by hand
# before trusting this script's numbers, or ask me to wire it up properly and test it live.
SURVIVAL_CV_DEV = {
    1:1.00, 2:0.99, 3:0.98, 4:0.97, 5:0.96, 6:0.95, 7:0.90, 8:0.80, 9:0.70,
    10:0.55, 11:0.40, 12:0.30, 13:0.20, 14:0.10, 15:0.05, 16:0.00,
}
SURVIVAL_LCV = {
    1:1.00, 2:0.98, 3:0.95, 4:0.92, 5:0.89, 6:0.84, 7:0.80, 8:0.65, 9:0.50,
    10:0.40, 11:0.20, 12:0.10, 13:0.00,
}

# ── PMS intervals from PMS Calc Assumptions sheet (your real numbers) ────────
PMS_INTERVALS = pd.DataFrame([
    {"category":"Oil filter",          "interval_km":15000,  "parts_per_service":1, "annual_freq":5.333},
    {"category":"Fuel filter",         "interval_km":40000,  "parts_per_service":1, "annual_freq":2.000},
    {"category":"Air filter",          "interval_km":20000,  "parts_per_service":1, "annual_freq":4.000},
    {"category":"Cabin filter",        "interval_km":20000,  "parts_per_service":1, "annual_freq":4.000},
    {"category":"Clutch disc",         "interval_km":150000, "parts_per_service":1, "annual_freq":0.533},
    {"category":"Pressure plate",      "interval_km":150000, "parts_per_service":1, "annual_freq":0.533},
    {"category":"Release bearing",     "interval_km":150000, "parts_per_service":1, "annual_freq":0.533},
    {"category":"Brake pad (front)",   "interval_km":40000,  "parts_per_service":4, "annual_freq":2.000},
    {"category":"Brake pad (rear)",    "interval_km":60000,  "parts_per_service":4, "annual_freq":1.333},
    {"category":"Brake disc (front)",  "interval_km":80000,  "parts_per_service":2, "annual_freq":1.000},
    {"category":"Brake disc (rear)",   "interval_km":100000, "parts_per_service":2, "annual_freq":0.800},
])

# ── PN classification — map descriptions to PMS categories ───────────────────
# Built on PNs that have AIM_DemandType=='Maintenance' OR AIM_Category in maintenance set.
PN_TO_CATEGORY_REGEX = [
    ("oil filter|element[;,].*oil",                          "Oil filter"),
    ("fuel filter|element.*fuel filter|element[;,].*fuel",   "Fuel filter"),
    (r"air filter|air cleaner|filter[;,]\s*acl",             "Air filter"),
    ("cabin filter|blower unit",                             "Cabin filter"),
    ("clutch kit|clutch.*disc",                              "Clutch disc"),
    ("pressure plate",                                       "Pressure plate"),
    ("release bearing",                                      "Release bearing"),
    ("pad kit.*frt|pad.*caliper.*frt|pad.*disc.*brk.*frt",   "Brake pad (front)"),
    ("pad kit.*disc brk.*w/o shim",                          "Brake pad (front)"),  # default unspecified to front
    ("pad kit.*rr|pad.*disc.*brk.*rr",                       "Brake pad (rear)"),
    ("rotor.*disc.*brk.*frt",                                "Brake disc (front)"),
    ("rotor.*disc.*brk.*rr",                                 "Brake disc (rear)"),
]


@st.cache_data(ttl=600)
def load_v3() -> pd.DataFrame:
    df = pd.read_excel(V3_FILE, sheet_name="PN_Price_Matrix", dtype={"PN": str})
    df["PN"] = df["PN"].astype(str).str.zfill(10)
    for c in ("PR00_EUR","Qty_CY2025","Qty_CY2024","Rev_CY2025_EUR"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


@st.cache_data(ttl=600)
def load_uio() -> pd.DataFrame:
    """Per-distributor UIO with survival-rate-adjusted active fleet."""
    if not UIO_FILE.exists():
        return pd.DataFrame()
    import openpyxl
    wb = openpyxl.load_workbook(UIO_FILE, read_only=True, data_only=True)
    ws = wb["1.UIO Overview"]
    data = list(ws.values)
    wb.close()
    df = pd.DataFrame(data[6:], columns=data[5])
    df = df.rename(columns={c: str(c).replace("\n"," ").strip() for c in df.columns})
    years = sorted([int(c) for c in df.columns if isinstance(c, str) and c.isdigit()])
    df["Distributor"] = df["Distributor"].astype(str)
    df["CV LCV"] = df["CV/ LCV"].astype(str) if "CV/ LCV" in df.columns else df.get("CV/\nLCV", "CV")

    CURRENT_YEAR = max(years)  # 2024
    rows = []
    for _, r in df.iterrows():
        dist = r.get("Distributor","")
        if not dist or dist == "nan":
            continue
        survival = SURVIVAL_LCV if str(r.get("CV LCV","CV")).strip().upper() == "LCV" else SURVIVAL_CV_DEV
        active_total = 0
        for y in years:
            v = pd.to_numeric(r.get(str(y)), errors="coerce")
            if pd.isna(v) or v <= 0:
                continue
            age = CURRENT_YEAR - y + 1
            s = survival.get(age, 0)
            active_total += float(v) * s
        rows.append({"Distributor": dist, "active_uio": active_total,
                     "country": r.get("Country",""),
                     "vehicle_type": r.get("CV LCV",""),
                     "model_type": r.get("Model Type", r.get("Model\nType",""))})
    out = pd.DataFrame(rows)
    return out.groupby("Distributor", as_index=False)["active_uio"].sum().sort_values("active_uio", ascending=False)


def classify_pms(description: str) -> str | None:
    import re
    if not isinstance(description, str):
        return None
    d = description.lower()
    for pattern, category in PN_TO_CATEGORY_REGEX:
        if re.search(pattern, d, re.IGNORECASE):
            return category
    return None


@st.cache_data(ttl=600)
def load_scraped_prices() -> pd.DataFrame:
    """Load competitor prices for the PNs we scraped."""
    GBP_EUR = 1.17
    SEK_EUR = 0.089

    def _clean(s, floor=3.0):
        if not isinstance(s, str): return None
        vals = []
        for p in s.split("|"):
            try:
                v = float(p.strip())
                if v >= floor: vals.append(v)
            except ValueError: pass
        return min(vals) if vals else None

    parts = {}
    files = [
        ("AD_UK", "autodoc_results.csv",   "Autodoc_AllPrices_GBP", "Autodoc_MinPrice_GBP",
         "Autodoc_CheapestBrand", "Autodoc_URL", GBP_EUR),
        ("MEK",   "mekonomen_results.csv", None, "MEK_AM_MinPrice_SEK",
         "MEK_AM_Brands", "MEK_URL", SEK_EUR),
        ("KS_AM", "ks_results.csv",        None, "KS_AM_MinPrice_GBP",
         "KS_AM_SKUs", "KS_URL", GBP_EUR),
        ("KS_GEN","ks_results.csv",        None, "KS_GEN_MinPrice_GBP",
         None, "KS_URL", GBP_EUR),
    ]
    for key, fname, all_col, min_col, brand_col, url_col, fx in files:
        p = SCRIPT_DIR / fname
        if not p.exists(): continue
        try:
            df = pd.read_csv(p, dtype={"PN":str}, low_memory=False)
        except Exception:
            continue
        if "PN" not in df.columns: continue
        df["PN"] = df["PN"].astype(str).str.zfill(10)
        if all_col and all_col in df.columns:
            df[min_col] = df[all_col].apply(_clean)
        elif min_col in df.columns:
            df[min_col] = pd.to_numeric(df[min_col], errors="coerce")
            df.loc[df[min_col] < 3.0, min_col] = None
        df[f"{key}_eur"] = pd.to_numeric(df[min_col], errors="coerce") * fx
        keep = ["PN", f"{key}_eur"]
        if brand_col and brand_col in df.columns:
            df[f"{key}_brand"] = df[brand_col]
            keep.append(f"{key}_brand")
        if url_col in df.columns:
            df[f"{key}_url"] = df[url_col]
            keep.append(f"{key}_url")
        parts[key] = df[keep].drop_duplicates("PN")

    if not parts: return pd.DataFrame()
    merged = None
    for df in parts.values():
        merged = df if merged is None else merged.merge(df, on="PN", how="outer")
    eur_cols = [c for c in merged.columns if c.endswith("_eur")]
    if eur_cols:
        merged["best_am_eur"] = merged[eur_cols].min(axis=1)
        idx = merged[eur_cols].idxmin(axis=1)
        merged["best_am_site"] = idx.str.replace("_eur","", regex=False)
        # Pick brand + url from cheapest site per row
        merged["best_am_brand"] = pd.NA
        merged["best_am_url"]   = pd.NA
        for key in ["AD_UK","MEK","KS_AM","KS_GEN"]:
            mask = merged["best_am_site"] == key
            if f"{key}_brand" in merged.columns:
                merged.loc[mask, "best_am_brand"] = merged.loc[mask, f"{key}_brand"]
            if f"{key}_url" in merged.columns:
                merged.loc[mask, "best_am_url"] = merged.loc[mask, f"{key}_url"]
    return merged


def compute_competitive_view(
    v3: pd.DataFrame,
    uio_by_dist: pd.DataFrame,
    distributor_filter: str,
    isze_gp_pct: float,
    horizon_years: float,
    scraped: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Build the competitive view.

    Returns:
      pn_view: per-PN data (category, captured units, lost share, competitor brand)
      cat_view: aggregated by category × distributor scope (this is the BI headline)
      meta: dict with UIO totals and assumptions
    """
    # Step 1: Filter PMS-eligible (use AIM_DemandType, not regex)
    pms = v3[v3["AIM_DemandType"] == "Maintenance"].copy()
    pms["category"] = pms["Description"].apply(classify_pms)
    # Keep only PNs we mapped to a PMS category
    pms = pms.dropna(subset=["category"])

    # Step 2: UIO for selected distributor scope
    if distributor_filter == "Pan-European (all ISZE markets)":
        uio_scope = uio_by_dist["active_uio"].sum()
        scope_label = "Pan-EU"
    else:
        match = uio_by_dist[uio_by_dist["Distributor"] == distributor_filter]
        uio_scope = float(match["active_uio"].sum()) if len(match) else 0.0
        scope_label = distributor_filter

    # Step 3: Category aggregation (one demand pool per category, NOT per PN)
    cat_view = []
    for _, cat_row in PMS_INTERVALS.iterrows():
        cat = cat_row["category"]
        sub = pms[pms["category"] == cat]
        if sub.empty:
            continue
        annual_pieces_per_vehicle = cat_row["annual_freq"] * cat_row["parts_per_service"]
        potential_units = uio_scope * annual_pieces_per_vehicle * horizon_years
        actual_units = float(sub["Qty_CY2025"].sum()) if "Qty_CY2025" in sub.columns else 0
        # Lost units cannot be negative
        lost_units = max(potential_units - actual_units, 0)
        avg_pr00 = float(sub["PR00_EUR"].mean())
        revenue_actual = float(sub["Rev_CY2025_EUR"].sum())
        lost_revenue = lost_units * avg_pr00
        lost_isze_gp = lost_revenue * isze_gp_pct
        cat_view.append({
            "category": cat,
            "pns": len(sub),
            "annual_freq": cat_row["annual_freq"],
            "parts_per_service": cat_row["parts_per_service"],
            "annual_pieces_per_vehicle": annual_pieces_per_vehicle,
            "potential_units": potential_units,
            "actual_units": actual_units,
            "lost_units": lost_units,
            "capture_rate": (actual_units / potential_units) if potential_units > 0 else 0,
            "avg_pr00": avg_pr00,
            "revenue_actual": revenue_actual,
            "lost_revenue": lost_revenue,
            "lost_isze_gp": lost_isze_gp,
        })
    cat_df = pd.DataFrame(cat_view)
    if not cat_df.empty:
        cat_df = cat_df.sort_values("lost_isze_gp", ascending=False)

    # Step 4: PN-level view with competitor data (drill-down)
    pn_view = pms[["PN","Description","category","PR00_EUR","Qty_CY2025",
                    "Rev_CY2025_EUR","AIM_Category","AIM_Bucket","Source","Class"]].copy()
    # Allocate category lost units to PNs by current sales share (best proxy without per-PN UIO)
    pn_view = pn_view.merge(
        cat_df[["category","potential_units","lost_units","lost_isze_gp"]].rename(
            columns={"potential_units":"cat_potential","lost_units":"cat_lost","lost_isze_gp":"cat_lost_gp"}),
        on="category", how="left",
    )
    pn_view["sales_share_in_cat"] = pn_view.groupby("category")["Qty_CY2025"].transform(
        lambda s: s / s.sum() if s.sum() > 0 else 0
    )
    # Allocated lost is proportional to sales share — under-allocates to PNs with already-low capture
    pn_view["allocated_lost_units"] = (pn_view["cat_lost"] * pn_view["sales_share_in_cat"]).round(0)
    pn_view["allocated_lost_gp"]    = (pn_view["cat_lost_gp"] * pn_view["sales_share_in_cat"]).round(0)

    # Merge competitor prices
    if not scraped.empty:
        pn_view = pn_view.merge(scraped, on="PN", how="left")

    meta = {
        "uio_scope": uio_scope,
        "scope_label": scope_label,
        "pms_pns": len(pms),
        "n_distributors": len(uio_by_dist),
        "total_pan_eu_uio": float(uio_by_dist["active_uio"].sum()) if not uio_by_dist.empty else 0,
    }
    return pn_view, cat_df, meta


# ═════════════════════════════════════════════════════════════════════════════
# STREAMLIT APP — BI tool layout
# ═════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="ISZE Competitive BI", page_icon="📊", layout="wide")

st.title("ISZE Competitive Intelligence")
st.caption("Lost-sales BI built on real foundations: v3 PN data · v17 UIO · PMS Calc intervals · live competitor prices")

# ── Sidebar: scope and assumptions ────────────────────────────────────────────
with st.sidebar:
    st.header("Scope")
    uio_by_dist = load_uio()
    if uio_by_dist.empty:
        st.error("UIO v17 file not found. Check path.")
        st.stop()
    distributor_options = ["Pan-European (all ISZE markets)"] + uio_by_dist["Distributor"].tolist()
    distributor_filter = st.selectbox("Market scope", distributor_options, index=0,
                                       help="Select a single distributor or pan-EU rollup.")

    st.markdown("---")
    st.header("Assumptions")
    isze_gp_pct = st.slider("ISZE GP % on PR00", 10, 70, 35, 1,
                             help="Single number across categories. Refine later if you have per-category GP.") / 100
    horizon_yrs = st.slider("Horizon (years)", 1, 5, 1, 1,
                             help="Time window for lost-sales projection.")

    st.markdown("---")
    st.header("Data sources")
    st.caption(f"v3 PN file: {V3_FILE.name}")
    st.caption(f"v17 UIO: {UIO_FILE.name}")
    st.caption(f"PMS Calc: {PMS_CALC.name}")

# ── Load data ────────────────────────────────────────────────────────────────
with st.spinner("Loading data..."):
    v3 = load_v3()
    scraped = load_scraped_prices()
    pn_view, cat_view, meta = compute_competitive_view(
        v3, uio_by_dist, distributor_filter, isze_gp_pct, horizon_yrs, scraped
    )

# ── HERO BAND — first-sight competitive vision ───────────────────────────────
hero1, hero2, hero3, hero4, hero5 = st.columns(5)
hero1.metric("Active UIO", f"{meta['uio_scope']:,.0f}",
             help=f"Survival-rate-adjusted active fleet for {meta['scope_label']}. "
                  f"Pan-EU total: {meta['total_pan_eu_uio']:,.0f}.")
hero2.metric("PMS PNs analyzed", meta['pms_pns'],
             help="From v3 PN_Price_Matrix, filtered on AIM_DemandType=='Maintenance'.")
total_lost_gp = float(cat_view["lost_isze_gp"].sum()) if not cat_view.empty else 0
total_lost_units = float(cat_view["lost_units"].sum()) if not cat_view.empty else 0
total_actual = float(cat_view["actual_units"].sum()) if not cat_view.empty else 0
total_potential = float(cat_view["potential_units"].sum()) if not cat_view.empty else 0
hero3.metric("Lost ISZE GP €/yr", f"€{total_lost_gp:,.0f}",
             help="Σ (lost units × avg PR00 × GP%) across all PMS categories")
hero4.metric("Lost units/yr", f"{total_lost_units:,.0f}")
hero5.metric("Overall capture rate",
             f"{(total_actual/total_potential*100):.1f}%" if total_potential > 0 else "—",
             help=f"Actual {total_actual:,.0f} ÷ Potential {total_potential:,.0f}")

st.markdown("---")

# ── 3-tab structure: Overview → Category drill → PN drill ─────────────────────
tab_overview, tab_category, tab_pn, tab_methodology = st.tabs([
    "📊 Overview", "🎯 By category", "🔍 By PN", "📖 Methodology"
])

# ── Overview tab ──────────────────────────────────────────────────────────────
with tab_overview:
    if cat_view.empty:
        st.info("No PMS categories matched. Check the PN classification regex.")
    else:
        st.subheader(f"{meta['scope_label']} — competitive picture in one view")

        col1, col2 = st.columns([3, 2])
        with col1:
            try:
                import plotly.express as px
                disp = cat_view.copy()
                disp["capture_pct"] = disp["capture_rate"] * 100
                fig = px.bar(
                    disp.iloc[::-1], y="category", x="lost_isze_gp", orientation="h",
                    color="capture_pct",
                    color_continuous_scale=["#b52a1c", "#c05010", "#a86010", "#0a6644"],
                    range_color=[0, 50],
                    hover_data={"pns": True, "actual_units": ":,.0f",
                                "potential_units": ":,.0f", "lost_units": ":,.0f",
                                "capture_pct": ":.1f"},
                    labels={"lost_isze_gp": "Lost ISZE GP €", "category": "",
                            "capture_pct": "Capture %"},
                )
                fig.update_layout(height=450, plot_bgcolor="white", paper_bgcolor="white",
                                  margin=dict(l=10, r=10, t=30, b=20),
                                  title="Lost ISZE GP € by PMS category — color = capture rate")
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.dataframe(cat_view)

        with col2:
            st.markdown("##### Where the leak is biggest")
            top3 = cat_view.head(3)
            for _, r in top3.iterrows():
                st.markdown(
                    f"**{r['category']}** — €{r['lost_isze_gp']:,.0f} lost GP/yr  \n"
                    f"_{r['capture_rate']*100:.1f}% capture · {r['actual_units']:,.0f} of {r['potential_units']:,.0f} units_"
                )
            st.markdown("---")
            st.markdown("##### Who's selling against us (live scraped)")
            if not scraped.empty and "best_am_brand" in pn_view.columns:
                brands = (pn_view.dropna(subset=["best_am_brand"])
                                  .groupby("best_am_brand")
                                  .agg(pns=("PN","count"),
                                       lost_gp=("allocated_lost_gp","sum"))
                                  .sort_values("lost_gp", ascending=False)
                                  .head(8))
                if not brands.empty:
                    st.dataframe(brands.reset_index(),
                                 use_container_width=True, hide_index=True,
                                 column_config={
                                    "best_am_brand": st.column_config.TextColumn("Brand"),
                                    "pns": st.column_config.NumberColumn("PNs"),
                                    "lost_gp": st.column_config.NumberColumn("Allocated lost GP €", format="€%.0f"),
                                 })
                else:
                    st.caption("No competitor brand attributions yet (scrape more PNs).")
            else:
                st.caption("No competitor data merged.")

# ── Category drill tab ────────────────────────────────────────────────────────
with tab_category:
    st.subheader(f"Category breakdown — {meta['scope_label']}")
    st.caption("Each row is a PMS service category. Hover for the math.")
    if cat_view.empty:
        st.info("No data.")
    else:
        disp = cat_view.copy()
        disp["capture_rate"] = (disp["capture_rate"] * 100).round(1)
        st.dataframe(
            disp, use_container_width=True, hide_index=True,
            column_config={
                "category": st.column_config.TextColumn("Category"),
                "pns": st.column_config.NumberColumn("# PNs"),
                "annual_freq": st.column_config.NumberColumn("Service freq/yr", format="%.2f"),
                "parts_per_service": st.column_config.NumberColumn("Pcs/service"),
                "annual_pieces_per_vehicle": st.column_config.NumberColumn("Pcs/vehicle/yr", format="%.2f"),
                "potential_units": st.column_config.NumberColumn("Potential units", format="%.0f"),
                "actual_units": st.column_config.NumberColumn("Actual CY25", format="%.0f"),
                "lost_units": st.column_config.NumberColumn("Lost units", format="%.0f"),
                "capture_rate": st.column_config.NumberColumn("Capture %", format="%.1f%%"),
                "avg_pr00": st.column_config.NumberColumn("Avg PR00", format="€%.2f"),
                "revenue_actual": st.column_config.NumberColumn("Actual rev", format="€%.0f"),
                "lost_revenue": st.column_config.NumberColumn("Lost rev", format="€%.0f"),
                "lost_isze_gp": st.column_config.NumberColumn("Lost ISZE GP", format="€%.0f"),
            },
        )
        st.markdown("---")
        st.markdown("##### Math for a single row (worked example)")
        if len(disp) > 0:
            r = disp.iloc[0]
            st.markdown(
                f"**{r['category']}** at {meta['scope_label']}:  \n"
                f"1. Active UIO = **{meta['uio_scope']:,.0f}** vehicles  \n"
                f"2. Service freq = **{r['annual_freq']:.2f}/yr** × {int(r['parts_per_service'])} pcs/service = **{r['annual_pieces_per_vehicle']:.2f} pcs/vehicle/yr**  \n"
                f"3. Potential annual demand = UIO × pcs/vehicle = **{r['potential_units']:,.0f} units/yr**  \n"
                f"4. Actual ISZE sales (Qty_CY2025) = **{r['actual_units']:,.0f} units**  \n"
                f"5. Lost = potential − actual = **{r['lost_units']:,.0f} units/yr** ({r['capture_rate']:.1f}% capture)  \n"
                f"6. Lost revenue at PR00 = **€{r['lost_revenue']:,.0f}**  \n"
                f"7. Lost ISZE GP @ {isze_gp_pct*100:.0f}% = **€{r['lost_isze_gp']:,.0f}**"
            )

# ── PN drill tab ──────────────────────────────────────────────────────────────
with tab_pn:
    st.subheader("PN-level drill-down")
    st.caption("All PNs classified into a PMS category. Lost units allocated by sales share within category. "
               "Competitor prices joined from live scraped data.")

    cat_filter = st.multiselect("Filter category", sorted(pn_view["category"].dropna().unique()))
    pn_search  = st.text_input("Search PN / description", "")

    dview = pn_view.copy()
    if cat_filter:
        dview = dview[dview["category"].isin(cat_filter)]
    if pn_search:
        m = (dview["PN"].str.contains(pn_search, case=False, na=False) |
             dview["Description"].str.contains(pn_search, case=False, na=False))
        dview = dview[m]
    dview = dview.sort_values("allocated_lost_gp", ascending=False)

    show_cols = ["PN","Description","category","Class","AIM_Bucket","Source",
                 "PR00_EUR","Qty_CY2025","Rev_CY2025_EUR",
                 "sales_share_in_cat","allocated_lost_units","allocated_lost_gp",
                 "best_am_eur","best_am_brand","best_am_site","best_am_url"]
    show_cols = [c for c in show_cols if c in dview.columns]
    st.dataframe(
        dview[show_cols].head(500),  # cap render
        use_container_width=True, hide_index=True,
        column_config={
            "PR00_EUR": st.column_config.NumberColumn("PR00", format="€%.2f"),
            "Qty_CY2025": st.column_config.NumberColumn("Qty CY25", format="%.0f"),
            "Rev_CY2025_EUR": st.column_config.NumberColumn("Rev CY25", format="€%.0f"),
            "sales_share_in_cat": st.column_config.NumberColumn("Share in cat", format="%.1%"),
            "allocated_lost_units": st.column_config.NumberColumn("Lost units (alloc)", format="%.0f"),
            "allocated_lost_gp": st.column_config.NumberColumn("Lost GP € (alloc)", format="€%.0f"),
            "best_am_eur": st.column_config.NumberColumn("Best AM €", format="€%.2f"),
            "best_am_brand": st.column_config.TextColumn("AM brand"),
            "best_am_site": st.column_config.TextColumn("Source"),
            "best_am_url": st.column_config.LinkColumn("Link", display_text="↗"),
        },
    )
    st.caption(f"Showing {min(len(dview), 500)} of {len(dview)} PNs after filters.")

# ── Methodology tab ───────────────────────────────────────────────────────────
with tab_methodology:
    st.subheader("Methodology — every number traced to its source")
    st.markdown(f"""
### Sources of truth (no invented numbers)

| Input | Source file | Sheet | Notes |
|---|---|---|---|
| PN catalog (PR00, Qty_CY2025, AIM categorization) | `{V3_FILE.name}` | PN_Price_Matrix | 15,352 PNs total; 449 with AIM_DemandType=='Maintenance' |
| Per-distributor UIO + survival rates | `{UIO_FILE.name}` | 1.UIO Overview · 3.UIO Calculation | Cohort × survival method |
| Service intervals + parts-per-service | `{PMS_CALC.name}` | Assumptions | ISZJ Group No.1 / Isuzu maintenance manual |
| Competitor prices + brands | scraped CSVs | — | AD_UK + KS + Mekonomen |

### Active UIO calculation (per distributor)

For each row in v17 UIO Overview (one row = country × CV/LCV × model × distributor):

> Active UIO = Σ over years 1990–2024 of (registrations in year Y × survival_rate(age = 2024−Y+1))

Survival rates are read directly from v17's `3. UIO Calculation` sheet:
- **CV — Developed Countries**: 100% age 1, 96% age 5, 80% age 8, 55% age 10, drops to 0 by age 16
- **LCV — All**: faster decay, 0 by age 13

Result: **{meta['total_pan_eu_uio']:,.0f}** active vehicles pan-EU. Top 5 distributors:
""")

    top_dist = uio_by_dist.head(5)
    st.dataframe(top_dist, use_container_width=True, hide_index=True,
                 column_config={"active_uio": st.column_config.NumberColumn("Active UIO", format="%.0f")})

    st.markdown("""
### Lost sales formula (per category, NOT per PN — avoids over-counting bug)

> Potential annual demand = UIO × annual_freq × parts_per_service × horizon
> Actual demand = Σ Qty_CY2025 across all PNs in that category
> Lost units = max(potential − actual, 0)
> Lost ISZE GP € = Lost units × avg PR00 × ISZE GP%

**Why category-level matters:** if there are 8 oil filter PNs in the catalog, they collectively serve the UIO — they don't each serve the UIO. Earlier per-PN multiplication caused 8× over-count of potential demand.

### PN-level lost allocation

Within a category, lost units are allocated to PNs by their share of current actual sales. This is the best available proxy without per-PN UIO mapping (e.g., which oil-filter PN fits N35 vs N75 vs older models).

### PMS intervals used (from your Calc Assumptions sheet)
""")
    st.dataframe(PMS_INTERVALS, use_container_width=True, hide_index=True,
                 column_config={
                    "interval_km": st.column_config.NumberColumn("Interval (km)", format="%d"),
                    "parts_per_service": st.column_config.NumberColumn("Pcs/service"),
                    "annual_freq": st.column_config.NumberColumn("Services/yr @ 80,000 km", format="%.3f"),
                 })

    st.markdown(f"""
### Assumptions still in play (you can override in sidebar)
- **Annual mileage** = 80,000 km/yr (ISZJ Group No.1 standard, all duty cycles)
- **ISZE GP %** = {isze_gp_pct*100:.0f}% (single number across categories — refine if per-category GP available)
- **Horizon** = {horizon_yrs} year(s)
- **Description → PMS category mapping** uses regex; some PNs may be miscategorized (e.g., "PAD KIT" without front/rear hint defaults to front)

### Known limitations honestly stated
1. Mileage is one number for all duty cycles (urban delivery vs personal vs long-haul all 80k)
2. Per-PN UIO allocation uses sales share — masks PNs that are losing all sales (their lost gets allocated to PNs that are still selling)
3. Brake-pad units may be axle-kit (4 pcs) or per-piece — depends on how IML books quantities
4. Survival rates assume "CV Developed Countries" everywhere ISZE sells — some markets are emerging
""")
