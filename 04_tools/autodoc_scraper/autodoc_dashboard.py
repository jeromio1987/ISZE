"""
ISZE — Aftermarket Price Comparison Dashboard
Compares ISZE PR00 vs: Autodoc UK, Autodoc EU, Autodoc DE,
                        Mister Auto, Oscaro, Mekonomen, KS International
Run: streamlit run autodoc_dashboard.py
"""

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

_HANDOFF = Path(__file__).resolve().parent / "_HANDOFF_BUNDLE"
if str(_HANDOFF) not in sys.path:
    sys.path.insert(0, str(_HANDOFF))
try:
    from iam_display import (
        format_brand_league,
        format_category_concentration,
        format_iam_pn,
        format_pms_category_iam,
        format_pms_pn_iam,
    )
except ImportError:
    format_brand_league = format_iam_pn = format_category_concentration = None  # type: ignore
    format_pms_category_iam = format_pms_pn_iam = None  # type: ignore

from iam_scoring import (
    compute_scores, compute_expected_loss, compute_lost_sales,
    load_brand_tiers, load_pms_intervals,
    summary_table, brand_league, category_concentration, data_quality_report,
)

# ── FX rates (update periodically) ───────────────────────────────────────────
GBP_EUR = 1.17
SEK_EUR = 0.089   # 1 SEK ≈ 0.089 EUR

SCRIPT_DIR = Path(__file__).parent

# ── Site registry ─────────────────────────────────────────────────────────────
SITES = [
    {
        "key":           "AD_UK",
        "label":         "Autodoc UK",
        "file":          "autodoc_results.csv",
        "min_col":       "Autodoc_MinPrice_GBP",
        "all_prices_col":"Autodoc_AllPrices_GBP",
        "brand_col":     "Autodoc_CheapestBrand",
        "url_col":       "Autodoc_URL",
        "currency":      "GBP",
        "to_eur":        GBP_EUR,
    },
    {
        "key":           "AD_EU",
        "label":         "Autodoc EU",
        "file":          "autodoc_eu_results.csv",
        "min_col":       "Autodoc_MinPrice_EUR",
        "all_prices_col":"Autodoc_AllPrices_EUR",
        "brand_col":     "Autodoc_CheapestBrand",
        "url_col":       "Autodoc_URL",
        "currency":      "EUR",
        "to_eur":        1.0,
    },
    {
        "key":           "AD_DE",
        "label":         "Autodoc DE",
        "file":          "autodoc_de_results.csv",
        "min_col":       "Autodoc_MinPrice_EUR",
        "all_prices_col":"Autodoc_AllPrices_EUR",
        "brand_col":     "Autodoc_CheapestBrand",
        "url_col":       "Autodoc_URL",
        "currency":      "EUR",
        "to_eur":        1.0,
    },
    {
        "key":      "MA",
        "label":    "Mister Auto",
        "file":     "mister_auto_results.csv",
        "min_col":  "MA_AM_MinPrice_EUR",
        "brand_col":"MA_AM_Brands",
        "url_col":  "MA_URL",
        "currency": "EUR",
        "to_eur":   1.0,
    },
    {
        "key":      "OSC",
        "label":    "Oscaro",
        "file":     "oscaro_results.csv",
        "min_col":  "OSC_AM_MinPrice_EUR",
        "brand_col":"OSC_AM_Brands",
        "url_col":  "OSC_URL",
        "currency": "EUR",
        "to_eur":   1.0,
    },
    {
        "key":      "MEK",
        "label":    "Mekonomen",
        "file":     "mekonomen_results.csv",
        "min_col":  "MEK_AM_MinPrice_SEK",
        "brand_col":"MEK_AM_Brands",
        "url_col":  "MEK_URL",
        "currency": "SEK",
        "to_eur":   SEK_EUR,
    },
    {
        "key":      "KS_AM",
        "label":    "KS Int'l (AM)",
        "file":     "ks_results.csv",
        "min_col":  "KS_AM_MinPrice_GBP",
        "brand_col":"KS_AM_SKUs",
        "url_col":  "KS_URL",
        "currency": "GBP",
        "to_eur":   GBP_EUR,
    },
    {
        "key":      "KS_GEN",
        "label":    "KS Int'l (OEM)",
        "file":     "ks_results.csv",
        "min_col":  "KS_GEN_MinPrice_GBP",
        "brand_col":None,
        "url_col":  "KS_URL",
        "currency": "GBP",
        "to_eur":   GBP_EUR,
    },
]

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ISZE IAM Lookup Lab",
    page_icon="🔩",
    layout="wide",
)
st.title("ISZE IAM Lookup Lab")
st.caption(
    "Threat / quality on **scraped** AM prices — lookup only, not PMS claims. "
    "For PMS + PRISM use `_HANDOFF_BUNDLE\\run_bi.bat`. See `PRODUCT_LOGIC.md`."
)
st.info(
    "**PMS lost sales & PRISM capture** → use **ISZE PMS Intelligence** (`_HANDOFF_BUNDLE\\run_bi.bat`). "
    "This app is IAM / substitution lookup on ~300 scraped PNs."
)
st.caption("ISZE PR00 vs competitor aftermarket prices — Autodoc · Mister Auto · Oscaro · Mekonomen · KS International")

# ── Load & merge ──────────────────────────────────────────────────────────────

def _clean_min_from_all_prices(all_prices_str: str, floor: float) -> float | None:
    """Re-derive true min price from pipe-separated AllPrices string, ignoring values below floor."""
    if not isinstance(all_prices_str, str) or not all_prices_str.strip():
        return None
    vals = []
    for part in all_prices_str.split("|"):
        try:
            v = float(part.strip())
            if v >= floor:
                vals.append(v)
        except ValueError:
            pass
    return min(vals) if vals else None


@st.cache_data(ttl=300)
def load_all(price_floor: float = 3.0) -> pd.DataFrame:
    loaded = {}
    for site in SITES:
        f = SCRIPT_DIR / site["file"]
        if not f.exists():
            continue
        key = site["key"]
        try:
            df = pd.read_csv(f, dtype={"PN": str}, low_memory=False)
        except Exception:
            continue
        if "PN" not in df.columns or df.empty:
            # Skip malformed / header-less / empty CSV files
            continue
        df["PN"] = df["PN"].astype(str).str.zfill(10)
        price_col = site["min_col"]
        all_col   = site.get("all_prices_col")

        # Re-derive clean min price from AllPrices if available
        if all_col and all_col in df.columns:
            df[price_col] = df[all_col].apply(
                lambda s: _clean_min_from_all_prices(s, price_floor)
            )
        elif price_col in df.columns:
            df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
            df.loc[df[price_col] < price_floor, price_col] = float("nan")

        # Rename to namespaced columns
        rename = {}
        if price_col in df.columns:
            rename[price_col] = f"{key}_min_native"
        if site["brand_col"] and site["brand_col"] in df.columns:
            rename[site["brand_col"]] = f"{key}_brand"
        if site["url_col"] and site["url_col"] in df.columns:
            rename[site["url_col"]] = f"{key}_url"
        df = df.rename(columns=rename)
        keep = ["PN"] + [v for v in rename.values() if v in df.rename(columns=rename).columns]
        # Add status for coverage
        if "Status" in df.columns:
            df = df.rename(columns={"Status": f"{key}_status"})
            keep += [f"{key}_status"]
        if "scrape_error" in df.columns:
            df = df.rename(columns={"scrape_error": f"{key}_scrape_error"})
            keep += [f"{key}_scrape_error"]
        # Preserve AD_UK ResultCount + AllPrices for scoring (range coverage, price consistency)
        if key == "AD_UK":
            for extra in ("Autodoc_ResultCount", "Autodoc_AllPrices_GBP"):
                if extra in df.columns:
                    keep.append(extra)
        loaded[key] = df[keep].drop_duplicates("PN")

    if not loaded:
        return pd.DataFrame()

    # Base: first available file with PN metadata
    base_file = None
    for site in SITES:
        f = SCRIPT_DIR / site["file"]
        if f.exists():
            try:
                _peek = pd.read_csv(f, nrows=1)
            except Exception:
                continue
            if "PN" in _peek.columns:
                base_file = f
                break
    if base_file is None:
        return pd.DataFrame()
    base = pd.read_csv(base_file, dtype={"PN": str}, low_memory=False)
    base["PN"] = base["PN"].astype(str).str.zfill(10)
    base["PR00_EUR"] = pd.to_numeric(base.get("PR00_EUR"), errors="coerce")
    base["Rev_CY2025_EUR"] = pd.to_numeric(base.get("Rev_CY2025_EUR"), errors="coerce").fillna(0)
    meta_cols = ["PN", "Description", "PR00_EUR", "Rev_CY2025_EUR"]
    for c in ("Qty_CY2025", "Source", "Class", "AIM_Category"):
        if c in base.columns:
            meta_cols.append(c)
    merged = base[meta_cols].drop_duplicates("PN")

    for key, df in loaded.items():
        merged = merged.merge(df, on="PN", how="left")

    # Add EUR-normalised price and premium columns per site
    for site in SITES:
        key = site["key"]
        native_col = f"{key}_min_native"
        eur_col    = f"{key}_min_eur"
        prem_col   = f"{key}_premium"
        if native_col not in merged.columns:
            merged[native_col] = float("nan")
        merged[eur_col]  = pd.to_numeric(merged[native_col], errors="coerce") * site["to_eur"]
        merged[prem_col] = merged["PR00_EUR"] / merged[eur_col].replace(0, float("nan"))

    # Best price across all sites (EUR)
    eur_cols = [f"{s['key']}_min_eur" for s in SITES]
    existing_eur = [c for c in eur_cols if c in merged.columns]
    if existing_eur:
        merged["best_price_eur"] = merged[existing_eur].min(axis=1)
        best_key_series = merged[existing_eur].idxmin(axis=1).str.replace("_min_eur", "")
        merged["best_site"] = best_key_series.map({s["key"]: s["label"] for s in SITES})
        merged["best_premium"] = merged["PR00_EUR"] / merged["best_price_eur"].replace(0, float("nan"))
        key_to_url_col = {s["key"]: s["url_col"] for s in SITES if s.get("url_col")}
        merged["best_url"] = pd.NA
        for _key, _url_col in key_to_url_col.items():
            if _url_col in merged.columns:
                merged.loc[best_key_series == _key, "best_url"] = merged.loc[best_key_series == _key, _url_col]

    return merged


# ── Price floor must be read BEFORE load_all ─────────────────────────────────
price_floor = st.sidebar.number_input(
    "Min price floor (native currency)",
    min_value=0.0, value=3.0, step=0.5, format="%.1f",
    help="Prices below this are treated as scraping artifacts (e.g. the £2 delivery badge Autodoc injects on every page).",
)

with st.spinner("Loading price data…"):
    df_all = load_all(price_floor=price_floor)

if df_all.empty:
    st.error("No result CSV files found in the autodoc_scraper folder.")
    st.stop()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    st.markdown("---")
    search = st.text_input("Search PN / Description", "")

    if "Class" in df_all.columns:
        classes = sorted(df_all["Class"].dropna().unique())
        sel_class = st.multiselect("Class", classes)
    else:
        sel_class = []

    if "AIM_Category" in df_all.columns:
        aims = sorted(df_all["AIM_Category"].dropna().unique())
        sel_aim = st.multiselect("AIM Category", aims)
    else:
        sel_aim = []

    min_rev = st.number_input("Min CY2025 Revenue (EUR)", min_value=0, value=0, step=5000)
    matched_only = st.toggle("Show only PNs with ≥1 price hit", value=False)

    st.markdown("---")
    st.caption(f"Total PNs: {len(df_all):,}")
    sites_loaded = [s["label"] for s in SITES if f"{s['key']}_min_native" in df_all.columns]
    st.caption("Sites loaded: " + " · ".join(sites_loaded))

    st.markdown("---")
    st.subheader("FX Rates")
    gbp_eur = st.number_input("GBP → EUR", value=GBP_EUR, step=0.01, format="%.3f")
    sek_eur = st.number_input("SEK → EUR", value=SEK_EUR, step=0.001, format="%.4f")

    st.markdown("---")
    st.subheader("Chain Margin Assumptions")
    db_gm      = st.slider("DB gross margin %",    min_value=0, max_value=60, value=37, step=1) / 100
    dlr_gm     = st.slider("DLR gross margin %",   min_value=0, max_value=60, value=25, step=1) / 100
    trade_disc = st.slider("Aftermarket trade discount %", min_value=0, max_value=60, value=35, step=1) / 100
    st.caption("DB buys at PR00. DLR buys at DB price. Trade = what a workshop pays after discount off retail.")

    st.markdown("---")
    st.subheader("Lost Sales (UIO)")
    uio_potential = st.number_input(
        "UIO potential (active units)", min_value=1000, max_value=100000,
        value=11900, step=500,
        help="ITUK pilot uses 11,900 = N35+N75 UIO 5y window × 50% potential factor.",
    )
    isze_gp_pct  = st.slider("ISZE GP % on PR00", min_value=10, max_value=70, value=35, step=1) / 100
    horizon_yrs  = st.slider("Time horizon (years)", min_value=1, max_value=5, value=1, step=1)
    st.caption("PMS lost sales = (UIO × annual_freq × horizon − Qty_CY2025) × PR00 × GP. Observed, not estimated.")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_all.copy()
if search:
    mask = (
        df["PN"].str.contains(search, case=False, na=False)
        | df["Description"].str.contains(search, case=False, na=False)
    )
    df = df[mask]
if sel_class:
    df = df[df["Class"].isin(sel_class)]
if sel_aim:
    df = df[df["AIM_Category"].isin(sel_aim)]
if min_rev:
    df = df[df["Rev_CY2025_EUR"] >= min_rev]
if matched_only:
    eur_cols = [f"{s['key']}_min_eur" for s in SITES if f"{s['key']}_min_eur" in df.columns]
    df = df[df[eur_cols].notna().any(axis=1)]

# ── Chain price columns ───────────────────────────────────────────────────────
# PR00 = ISZE → DB. DB sells to DLR. DLR sells to customer.
# GM convention: GM% = (SP - Cost) / SP  →  SP = Cost / (1 - GM%)
df["DB_price"]    = df["PR00_EUR"] / (1 - db_gm)       # what DLR pays for genuine
df["DLR_price"]   = df["DB_price"]  / (1 - dlr_gm)     # what end customer pays for genuine
# Best aftermarket trade price = cheapest site EUR × (1 - trade_disc)
if "best_price_eur" in df.columns:
    df["AM_trade"]    = df["best_price_eur"] * (1 - trade_disc)   # what workshop pays on Autodoc etc.
    # Key ratios
    df["dlr_vs_am_retail"] = df["DLR_price"] / df["best_price_eur"]   # customer: genuine vs AM retail
    df["db_vs_am_trade"]   = df["DB_price"]  / df["AM_trade"]          # dealer: genuine vs AM trade

# ── Compute scoring + expected loss + UIO lost sales once (used by all tabs) ─
if df.empty or "best_price_eur" not in df.columns:
    scored = df.assign(threat_score=float("nan"), quality_score=float("nan"),
                       expected_loss=0, p_substitution=0, eur_at_stake=0,
                       action_verdict="—", quadrant="No data",
                       primary_threat_brand="", brand_tier=1, brand_oe_flag=0,
                       pms_category=None, potential_demand=float("nan"),
                       actual_units=0, lost_units=float("nan"),
                       capture_rate=float("nan"), lost_revenue_eur=float("nan"),
                       lost_isze_gp_eur=float("nan"))
else:
    try:
        scored = compute_scores(df, db_gm=db_gm, dlr_gm=dlr_gm)
        scored = compute_expected_loss(scored, isze_gp_pct=isze_gp_pct, horizon_years=horizon_yrs)
        scored = compute_lost_sales(scored, uio_potential=float(uio_potential),
                                    isze_gp_pct=isze_gp_pct, horizon_years=horizon_yrs)
    except FileNotFoundError as e:
        st.error(str(e)); st.stop()

# ── Global header KPI band (visible on every tab) ────────────────────────────
total_pns = len(scored)
any_hit = scored["best_price_eur"].notna().sum() if "best_price_eur" in scored.columns else 0
total_el  = float(scored["expected_loss"].sum()) if "expected_loss" in scored.columns else 0
defend_n  = int((scored["action_verdict"] == "Defend").sum()) if "action_verdict" in scored.columns else 0
pms_n = int(scored["pms_category"].notna().sum()) if "pms_category" in scored.columns else 0
lost_gp_total = float(scored["lost_isze_gp_eur"].sum(skipna=True)) if "lost_isze_gp_eur" in scored.columns else 0

kpi_a, kpi_b, kpi_c, kpi_d, kpi_e = st.columns(5)
kpi_a.metric("PNs in view", f"{total_pns:,}")
kpi_b.metric("PMS-eligible", f"{pms_n}", help="PNs matched to a PMS service interval (filters, brakes, clutch)")
kpi_c.metric("PMS lost GP €", f"€{lost_gp_total:,.0f}",
             help=f"UIO-derived: (UIO {uio_potential:,} × freq × {horizon_yrs}y − actual Qty_CY25) × PR00 × {isze_gp_pct*100:.0f}% GP")
kpi_d.metric("Substitution EL €", f"€{total_el:,.0f}",
             help="Fallback estimate for breakdown parts (substitution probability × Rev × GP)")
kpi_e.metric("Defend now", f"{defend_n}", help="PNs flagged for strategic defense (substitution model)")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# 9-TAB INVESTING DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "Cockpit",
    "PMS Lost Sales",
    "Brand League",
    "Threat Map",
    "PN Deep Dive",
    "Category Heatmap",
    "Scenario Lab",
    "Geography",
    "Data Quality",
    "Methodology",
])

METHODOLOGY_FOOTER = (
    "**PMS Lost Sales (UIO method)** = (UIO potential × annual_freq × horizon − Qty_CY2025) × PR00 × ISZE GP. **Primary metric** for PMS-eligible parts (filters/brakes/clutch). Observed, not estimated. "
    "**Substitution EL** = price-gap-bucket × tier lookup × Rev × GP. Fallback for breakdown parts where no service interval exists. "
    f"Current run: UIO {uio_potential:,} · DB {db_gm*100:.0f}% · DLR {dlr_gm*100:.0f}% · ISZE GP {isze_gp_pct*100:.0f}% · horizon {horizon_yrs}y."
)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — EXECUTIVE COCKPIT
# ═══════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("Executive Cockpit")
    st.caption("5-second read. What's at risk, who's eating our lunch, what to do this week.")

    if scored.empty:
        st.info("No scoring data yet — run scrapers and refresh.")
    else:
        # Top KPI band — UIO-derived lost sales is the headline
        pms_df = scored[scored["pms_category"].notna()].copy() if "pms_category" in scored.columns else pd.DataFrame()
        pms_lost_gp = float(pms_df["lost_isze_gp_eur"].sum()) if not pms_df.empty else 0.0
        pms_lost_units = float(pms_df["lost_units"].sum()) if not pms_df.empty else 0.0
        pms_capture = (pms_df["actual_units"].sum() / pms_df["potential_demand"].sum() * 100) if (not pms_df.empty and pms_df["potential_demand"].sum() > 0) else 0
        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric("PMS Lost ISZE GP €",  f"€{pms_lost_gp:,.0f}",
                   help=f"UIO-derived. {len(pms_df)} PMS-eligible PNs. {pms_lost_units:,.0f} lost units/yr at UIO {uio_potential:,}.")
        kc2.metric("PMS capture rate",  f"{pms_capture:.1f}%",
                   help="Actual ÷ Potential units (weighted across PMS-eligible PNs)")
        kc3.metric("Defend (substitution model)", f"{defend_n}",
                   help="Breakdown PNs flagged for strategic defense via substitution-probability model")
        coverage_pct = any_hit / total_pns * 100 if total_pns else 0
        kc4.metric("AM-price coverage", f"{coverage_pct:.0f}%",
                   help=f"{any_hit} of {total_pns} PNs have at least one aftermarket price.")

        st.markdown("---")

        # Top threats (auto-generated narrative)
        bl = brand_league(scored)
        top_brand = bl.iloc[0] if not bl.empty else None
        top_pn    = scored.sort_values("expected_loss", ascending=False).iloc[0] if (scored["expected_loss"] > 0).any() else None
        cat_concentration = category_concentration(scored).sort_values("expected_loss_eur", ascending=False)
        top_cat   = cat_concentration.iloc[0] if not cat_concentration.empty else None

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown("##### Top threat brand")
            if top_brand is not None:
                st.markdown(f"**{top_brand['brand']}** (tier {int(top_brand['tier'])})")
                st.markdown(f"€{top_brand['expected_loss_eur']:,.0f} expected loss · {int(top_brand['pns_threatened'])} PNs")
                st.markdown(f"€{top_brand['rev_exposed_eur']:,.0f} revenue exposed")
            else:
                st.markdown("—")
        with sc2:
            st.markdown("##### Top threat PN")
            if top_pn is not None:
                st.markdown(f"**{top_pn['PN']}** — {top_pn['Description']}")
                st.markdown(f"€{top_pn['expected_loss']:,.0f} EL · P(sub) {top_pn['p_substitution']*100:.0f}%")
                st.markdown(f"AM brand: {top_pn['primary_threat_brand'] or '—'}")
            else:
                st.markdown("—")
        with sc3:
            st.markdown("##### Top threat category")
            if top_cat is not None:
                st.markdown(f"**{top_cat.get('AIM_Category','—')}** (class {top_cat.get('Class','—')})")
                st.markdown(f"€{top_cat['expected_loss_eur']:,.0f} expected loss · {int(top_cat['pns'])} PNs")
            else:
                st.markdown("—")

        st.markdown("---")

        # Auto-generated narrative — leads with UIO-derived lost sales
        story_parts = []
        if not pms_df.empty:
            top_cat_pms = pms_df.groupby("pms_category")["lost_isze_gp_eur"].sum().sort_values(ascending=False)
            if len(top_cat_pms):
                top_cat_name = top_cat_pms.index[0]
                top_cat_gp = top_cat_pms.iloc[0]
                story_parts.append(
                    f"At a UIO potential of **{uio_potential:,}** units (ITUK pilot), we are losing "
                    f"**€{pms_lost_gp:,.0f} of ISZE GP per year** on the {len(pms_df)} PMS-eligible PNs scraped. "
                    f"Capture rate is **{pms_capture:.1f}%**. Worst category: **{top_cat_name}** (€{top_cat_gp:,.0f} lost GP)."
                )
        if top_brand is not None:
            story_parts.append(
                f"On breakdown parts, the dominant IAM threat is **{top_brand['brand']}** "
                f"(tier {int(top_brand['tier'])}), present on **{int(top_brand['pns_threatened'])} PNs** "
                f"with **€{top_brand['expected_loss_eur']:,.0f}** of substitution-model expected loss."
            )
        if not story_parts:
            story_parts = ["Insufficient data — run more scrapers."]
        st.markdown("##### This week's read")
        st.markdown(" ".join(story_parts))

        st.markdown("---")
        st.markdown("##### Suggested actions (top 3)")
        actions = []
        if not pms_df.empty:
            worst_pms_pn = pms_df.sort_values("lost_isze_gp_eur", ascending=False).head(1)
            if len(worst_pms_pn):
                r = worst_pms_pn.iloc[0]
                actions.append(
                    f"**Recover {r['PN']}** ({r['Description']}, {r['pms_category']}) — "
                    f"only {int(r['actual_units']):,} of {int(r['potential_demand']):,} units captured "
                    f"({(r['capture_rate']*100):.1f}%). €{r['lost_isze_gp_eur']:,.0f} GP per year on this single PN."
                )
        if defend_n > 0:
            top_defend = scored[scored["action_verdict"] == "Defend"].sort_values("expected_loss", ascending=False).head(1)
            if len(top_defend):
                r = top_defend.iloc[0]
                actions.append(
                    f"**Defend {r['PN']}** ({r['Description']}) — counter {r['primary_threat_brand']} at "
                    f"€{r['best_price_eur']:,.2f} (vs DLR→WS €{r['dealer_workshop_price']:,.2f})."
                )
        if top_brand is not None and int(top_brand['tier']) >= 4:
            actions.append(
                f"**Counter-narrative** against **{top_brand['brand']}** — workshops perceive this brand as "
                f"OE-equivalent. Comms emphasis: warranty, fitment data, OEM provenance."
            )
        if not actions:
            actions = ["Insufficient scoring data — run more scrapers first."]
        for a in actions:
            st.markdown(f"- {a}")

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — PMS LOST SALES (UIO-derived, primary financial metric)
# ═══════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("PMS Lost Sales — UIO × interval methodology")
    st.markdown(
        f"**Observed**, not estimated. Same methodology as your existing ITUK PMS Coverage Calculator. "
        f"For each PMS-eligible PN: expected annual demand = **UIO × annual frequency × horizon**. "
        f"Lost units = expected − actual (Qty_CY2025). Lost ISZE GP = lost units × PR00 × ISZE GP%."
    )

    pms_df = scored[scored["pms_category"].notna()].copy() if "pms_category" in scored.columns else pd.DataFrame()

    if pms_df.empty:
        st.info("No PMS-eligible PNs in current view. Check filters or scraper coverage.")
    else:
        # ── Headline KPIs ──
        total_potential = float(pms_df["potential_demand"].sum())
        total_actual    = float(pms_df["actual_units"].sum())
        total_lost      = float(pms_df["lost_units"].sum())
        total_lost_rev  = float(pms_df["lost_revenue_eur"].sum())
        total_lost_gp   = float(pms_df["lost_isze_gp_eur"].sum())
        capture_rate    = (total_actual / total_potential * 100) if total_potential > 0 else 0

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("PMS PNs in view", f"{len(pms_df)}")
        p2.metric("Capture rate", f"{capture_rate:.1f}%",
                  help=f"Actual {total_actual:,.0f} ÷ Potential {total_potential:,.0f} units")
        p3.metric("Lost units / yr", f"{total_lost:,.0f}",
                  help=f"At UIO potential = {uio_potential:,} × {horizon_yrs}y horizon")
        p4.metric("Lost ISZE GP €", f"€{total_lost_gp:,.0f}",
                  help=f"{total_lost:,.0f} units × avg PR00 × {isze_gp_pct*100:.0f}% GP")

        st.markdown("---")

        # ── By category breakdown ──
        st.markdown("##### Lost sales by PMS category")
        cat_agg = pms_df.groupby("pms_category").agg(
            pns=("PN", "count"),
            potential=("potential_demand", "sum"),
            actual=("actual_units", "sum"),
            lost=("lost_units", "sum"),
            lost_revenue=("lost_revenue_eur", "sum"),
            lost_gp=("lost_isze_gp_eur", "sum"),
        ).reset_index()
        cat_agg["capture_pct"] = (cat_agg["actual"] / cat_agg["potential"] * 100).round(1)
        cat_agg = cat_agg.sort_values("lost_gp", ascending=False)

        try:
            import plotly.express as px
            fig = px.bar(
                cat_agg.iloc[::-1], y="pms_category", x="lost_gp", orientation="h",
                color="capture_pct",
                color_continuous_scale=["#b52a1c", "#c05010", "#a86010", "#0a6644"],
                hover_data={"pns": True, "potential": ":,.0f", "actual": ":,.0f",
                            "lost": ":,.0f", "lost_revenue": ":,.0f", "capture_pct": ":.1f"},
                labels={"lost_gp": "Lost ISZE GP €", "pms_category": "",
                        "capture_pct": "Capture %"},
            )
            fig.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10, r=10, t=10, b=20))
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

        if format_pms_category_iam:
            st.dataframe(format_pms_category_iam(cat_agg), use_container_width=True, hide_index=True)
        else:
            st.dataframe(cat_agg.head(10), use_container_width=True, hide_index=True)

        with st.expander("Top PMS PNs (detail)", expanded=False):
            top_pms = pms_df.sort_values("lost_isze_gp_eur", ascending=False)
            if format_pms_pn_iam:
                st.dataframe(format_pms_pn_iam(top_pms), use_container_width=True, hide_index=True)
            else:
                st.dataframe(top_pms.head(12), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("##### Breakdown vs PMS coverage")
        st.markdown(
            f"- This view covers **{len(pms_df)} PMS-eligible PNs** out of **{len(scored)} scraped**.  \n"
            f"- The remaining **{len(scored) - len(pms_df)} PNs are breakdown parts** (sensors, electronics, structural) — no service interval, no UIO-derived expected demand.  \n"
            f"- For those, the **Substitution EL** (Brand League / Threat Map tabs) is the fallback estimate.  \n"
            f"- **UIO assumption**: {uio_potential:,} potential units (ITUK pilot = 11,900). Adjust in sidebar to project across larger markets."
        )

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — BRAND LEAGUE TABLE
# ═══════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Brand League — who is undercutting ISZE")
    st.caption("Aggregated by primary threat brand. Sorted by expected loss €.")
    bl = brand_league(scored)
    if bl.empty:
        st.info("No brand data yet.")
    else:
        # Bar chart of top 15
        try:
            import plotly.express as px
            top15 = bl.head(15).iloc[::-1]
            fig = px.bar(
                top15, y="brand", x="expected_loss_eur", orientation="h",
                color="tier",
                color_continuous_scale=["#b52a1c", "#c05010", "#a86010", "#0c2461"],
                hover_data={"pns_threatened": True, "rev_exposed_eur": ":.0f", "defend_count": True, "tier": True},
                labels={"expected_loss_eur": "Expected Loss €", "brand": ""},
            )
            fig.update_layout(height=480, plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10, r=10, t=10, b=20),
                              coloraxis_colorbar=dict(title="Tier"))
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

        if format_brand_league:
            st.dataframe(format_brand_league(bl), use_container_width=True, hide_index=True)
        with st.expander("Brand league — all columns", expanded=False):
            st.dataframe(bl.head(20), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — THREAT MAP (2x2)
# ═══════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Threat × Quality Map")
    st.caption("2×2 visual. Bubble size = Expected Loss €. Reference lines at threshold = 50.")

    if scored.empty:
        st.info("No data.")
    else:
        try:
            import plotly.express as px
            plot_df = scored.dropna(subset=["threat_score", "quality_score"]).copy()
            plot_df["el_size"] = plot_df["expected_loss"].clip(lower=100)
            if not plot_df.empty:
                fig = px.scatter(
                    plot_df, x="quality_score", y="threat_score",
                    size="el_size",
                    color="action_verdict",
                    color_discrete_map={
                        "Defend":  "#b52a1c",
                        "Match":   "#c05010",
                        "Monitor": "#0c2461",
                        "Cede":    "#9aa0a8",
                    },
                    hover_data={
                        "PN": True, "Description": True, "primary_threat_brand": True,
                        "expected_loss": ":.0f", "p_substitution": ":.2f",
                        "Rev_CY2025_EUR": ":.0f", "el_size": False,
                    },
                    labels={"quality_score": "Quality (Q)", "threat_score": "Threat (T)"},
                )
                fig.add_hline(y=50, line_dash="dash", line_color="#888")
                fig.add_vline(x=50, line_dash="dash", line_color="#888")
                fig.update_layout(height=560, plot_bgcolor="white", paper_bgcolor="white",
                                  xaxis=dict(range=[0,105]), yaxis=dict(range=[0,105]))
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.warning("Install plotly")

        # Per-quadrant rollups (€-weighted, not count)
        st.markdown("##### Expected Loss by quadrant (€)")
        q_summary = scored.groupby("quadrant").agg(
            pns=("PN", "count"),
            rev_exposed=("Rev_CY2025_EUR", "sum"),
            expected_loss=("expected_loss", "sum"),
        ).reset_index()
        st.dataframe(q_summary, use_container_width=True, hide_index=True,
                     column_config={
                        "pns": st.column_config.NumberColumn("# PNs"),
                        "rev_exposed": st.column_config.NumberColumn("Rev exposed", format="€%.0f"),
                        "expected_loss": st.column_config.NumberColumn("Expected loss", format="€%.0f"),
                     })

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — PN DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("PN Deep Dive")
    st.caption("Search a PN or description, see the full price stack and threat breakdown.")

    search_pn = st.text_input("Search PN or description", "", key="pn_deep_search")
    candidates = scored.copy()
    if search_pn:
        m = (candidates["PN"].str.contains(search_pn, case=False, na=False) |
             candidates["Description"].str.contains(search_pn, case=False, na=False))
        candidates = candidates[m]
    candidates = candidates.sort_values("expected_loss", ascending=False)

    if candidates.empty:
        st.info("No matches.")
    else:
        options = [f"{r['PN']} — {r['Description']} (EL €{r['expected_loss']:,.0f})"
                   for _, r in candidates.head(50).iterrows()]
        pick = st.selectbox("Select a PN", options, index=0)
        sel_pn = pick.split(" — ")[0]
        row = candidates[candidates["PN"] == sel_pn].iloc[0]

        # Header card
        h1, h2, h3, h4 = st.columns(4)
        h1.markdown(f"**PN** `{row['PN']}`")
        h2.markdown(f"**Class** {row.get('Class','—')}")
        h3.markdown(f"**AIM** {row.get('AIM_Category','—')}")
        h4.markdown(f"**Rev CY25** €{row['Rev_CY2025_EUR']:,.0f}")
        st.markdown(f"#### {row['Description']}")
        st.markdown("---")

        # Price chain cards
        st.markdown("##### Price chain (apples-to-apples)")
        pc1, pc2, pc3, pc4, pc5 = st.columns(5)
        pc1.metric("PR00 (ISZE→DB)",  f"€{row['PR00_EUR']:,.2f}")
        pc2.metric("DB price",         f"€{row['PR00_EUR']/(1-db_gm):,.2f}", help="What DLR pays ISZE/DB for genuine")
        pc3.metric("DLR→customer",     f"€{row['PR00_EUR']/(1-db_gm)/(1-dlr_gm):,.2f}", help="Full retail (customer pays dealer)")
        pc4.metric("DLR→WS genuine",   f"€{row['dealer_workshop_price']:,.2f}", help="The apples-to-apples genuine workshop price")
        pc5.metric("AM retail",        f"€{row['best_price_eur']:,.2f}" if pd.notna(row['best_price_eur']) else "—",
                   help=f"Cheapest aftermarket online — {row.get('best_site','')}")

        st.markdown("---")

        # Threat breakdown
        st.markdown("##### Threat score breakdown")
        try:
            import plotly.graph_objects as go
            factors = ["Price gap", "Revenue at risk", "Range coverage", "Price consistency", "Multi-platform"]
            weights = [0.35, 0.30, 0.10, 0.10, 0.15]
            vals = [row.get('s_price_gap',0), row.get('s_revenue_at_risk',0),
                    row.get('s_range_coverage',0), row.get('s_price_consistency',0),
                    row.get('s_multi_platform',0)]
            weighted = [v*w for v,w in zip(vals, weights)]
            fig = go.Figure()
            fig.add_bar(name="Raw score", y=factors, x=vals, orientation="h",
                        marker_color="#dde3ec")
            fig.add_bar(name=f"Weighted contribution to T={row['threat_score']:.0f}",
                        y=factors, x=weighted, orientation="h",
                        marker_color="#b52a1c")
            fig.update_layout(barmode="overlay", height=240, plot_bgcolor="white",
                              margin=dict(l=10,r=10,t=10,b=20), xaxis_range=[0,100],
                              legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

        # Expected loss block
        el1, el2, el3, el4 = st.columns(4)
        el1.metric("P(substitution)", f"{row['p_substitution']*100:.0f}%")
        el2.metric("€ at stake", f"€{row['eur_at_stake']:,.0f}")
        el3.metric("Expected loss", f"€{row['expected_loss']:,.0f}")
        el4.metric("Verdict", row.get("action_verdict","—"))

        st.markdown("---")

        # All sites price stack
        st.markdown("##### Price stack across sources")
        stack = []
        for site in SITES:
            key = site["key"]; label = site["label"]
            ec = f"{key}_min_eur"
            if ec in row.index and pd.notna(row[ec]):
                bc = f"{key}_brand"
                uc = f"{key}_url"
                stack.append({
                    "Source": label,
                    "Price (€)": float(row[ec]),
                    "Brand": row.get(bc, "—"),
                    "URL": row.get(uc, ""),
                })
        if stack:
            sdf = pd.DataFrame(stack).sort_values("Price (€)")
            st.dataframe(sdf, use_container_width=True, hide_index=True,
                         column_config={
                             "Price (€)": st.column_config.NumberColumn(format="€%.2f"),
                             "URL": st.column_config.LinkColumn("Link", display_text="↗"),
                         })
        else:
            st.info("No aftermarket hits across any source for this PN.")

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — CATEGORY HEATMAP
# ═══════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("Category Concentration")
    st.caption("Where is the threat concentrated? Class × AIM Category — color = Expected Loss €.")

    cat = category_concentration(scored)
    if cat.empty or scored["expected_loss"].sum() == 0:
        st.info("No category data — needs Class + AIM_Category columns and scoring.")
    else:
        # Pivot for heatmap
        pivot = cat.pivot_table(index="AIM_Category", columns="Class",
                                values="expected_loss_eur", aggfunc="sum", fill_value=0)
        try:
            import plotly.express as px
            fig = px.imshow(pivot, color_continuous_scale=["#f4f7fb", "#fef3e2", "#fbeae8", "#b52a1c"],
                            aspect="auto", labels=dict(color="EL €"),
                            text_auto=".0f")
            fig.update_layout(height=520, paper_bgcolor="white",
                              margin=dict(l=10,r=10,t=10,b=20))
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.dataframe(pivot, use_container_width=True)

        # Concentration table
        st.markdown("##### Top categories by Expected Loss")
        if format_category_concentration:
            st.dataframe(format_category_concentration(cat), use_container_width=True, hide_index=True)
        else:
            st.dataframe(cat.sort_values("expected_loss_eur", ascending=False).head(10),
                         use_container_width=True, hide_index=True)

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 6 — SCENARIO LAB
# ═══════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("Scenario Lab — what-if")
    st.caption("Tune assumptions, see how the picture changes. Sidebar sliders drive these scenarios live.")

    if scored.empty or scored["expected_loss"].sum() == 0:
        st.info("Need scored data — adjust filters and refresh.")
    else:
        # Live comparison: current vs scenarios
        st.markdown("##### Pre-set scenarios vs current")
        scenarios = [
            ("Current (sidebar)", db_gm, dlr_gm, isze_gp_pct, horizon_yrs),
            ("Conservative",      0.30, 0.20, 0.25, 1),
            ("Aggressive defence",0.40, 0.30, 0.40, 2),
            ("Margin squeeze",    0.25, 0.20, 0.20, 1),
        ]
        rows = []
        for name, sdb, sdlr, sgp, syr in scenarios:
            tmp = compute_scores(df, db_gm=sdb, dlr_gm=sdlr) if not df.empty else df
            if not tmp.empty:
                tmp = compute_expected_loss(tmp, isze_gp_pct=sgp, horizon_years=syr)
                rows.append({
                    "Scenario": name,
                    "DB GM": f"{sdb*100:.0f}%",
                    "DLR GM": f"{sdlr*100:.0f}%",
                    "ISZE GP": f"{sgp*100:.0f}%",
                    "Horizon": f"{syr}y",
                    "Total EL (€)": float(tmp["expected_loss"].sum()),
                    "Defend": int((tmp["action_verdict"]=="Defend").sum()),
                    "Match":  int((tmp["action_verdict"]=="Match").sum()),
                    "Cede":   int((tmp["action_verdict"]=="Cede").sum()),
                })
        sdf = pd.DataFrame(rows)
        st.dataframe(sdf, use_container_width=True, hide_index=True,
                     column_config={"Total EL (€)": st.column_config.NumberColumn(format="€%.0f")})

        st.markdown("---")
        st.markdown("##### Where the chain breaks (current sidebar settings)")
        # PNs where DLR→WS < AM retail (workshop has no economic reason to use genuine)
        broken = scored[(scored["dealer_workshop_price"].notna()) &
                        (scored["best_price_eur"].notna()) &
                        (scored["dealer_workshop_price"] > scored["best_price_eur"] * 1.5)].copy()
        broken["gap_x"] = (broken["dealer_workshop_price"] / broken["best_price_eur"]).round(2)
        broken = broken.sort_values("expected_loss", ascending=False).head(20)
        if not broken.empty:
            disp = broken[["PN","Description","primary_threat_brand","PR00_EUR",
                          "dealer_workshop_price","best_price_eur","gap_x",
                          "expected_loss","action_verdict"]]
            st.dataframe(disp, use_container_width=True, hide_index=True,
                         column_config={
                            "PR00_EUR": st.column_config.NumberColumn("PR00", format="€%.2f"),
                            "dealer_workshop_price": st.column_config.NumberColumn("DLR→WS", format="€%.2f"),
                            "best_price_eur": st.column_config.NumberColumn("AM", format="€%.2f"),
                            "gap_x": st.column_config.NumberColumn("DLR÷AM", format="%.2f×"),
                            "expected_loss": st.column_config.NumberColumn("EL", format="€%.0f"),
                         })
        else:
            st.info("Chain looks intact at current margin assumptions.")

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 7 — GEOGRAPHY
# ═══════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.subheader("Geography — UK vs Nordics")
    st.caption("ITUK is UK's dominant Isuzu distributor — UK threat is strategically the most material.")

    if scored.empty:
        st.info("No data.")
    else:
        # UK = AD_UK or KS_AM/GEN provides best price
        uk_mask = pd.Series(False, index=scored.index)
        nordic_mask = pd.Series(False, index=scored.index)
        if "AD_UK_min_eur" in scored.columns:
            uk_mask = uk_mask | scored["AD_UK_min_eur"].notna()
        if "KS_AM_min_eur" in scored.columns:
            uk_mask = uk_mask | scored["KS_AM_min_eur"].notna()
        if "KS_GEN_min_eur" in scored.columns:
            uk_mask = uk_mask | scored["KS_GEN_min_eur"].notna()
        if "MEK_min_eur" in scored.columns:
            nordic_mask = scored["MEK_min_eur"].notna()

        gc1, gc2 = st.columns(2)
        with gc1:
            st.markdown("### United Kingdom (ITUK exposure)")
            uk_scored = scored[uk_mask]
            st.metric("# PNs threatened", len(uk_scored))
            st.metric("Rev exposed", f"€{uk_scored['Rev_CY2025_EUR'].sum():,.0f}")
            st.metric("Expected loss", f"€{uk_scored['expected_loss'].sum():,.0f}")
            st.metric("Defend now", int((uk_scored['action_verdict']=='Defend').sum()))
            # Top 5 UK brands
            uk_bl = brand_league(uk_scored).head(5)
            if not uk_bl.empty:
                st.markdown("##### Top brand threats")
                st.dataframe(uk_bl[["brand","tier","pns_threatened","expected_loss_eur"]],
                             use_container_width=True, hide_index=True,
                             column_config={
                                "tier": st.column_config.NumberColumn("Tier", format="%d"),
                                "pns_threatened": st.column_config.NumberColumn("# PNs"),
                                "expected_loss_eur": st.column_config.NumberColumn("EL", format="€%.0f"),
                             })
        with gc2:
            st.markdown("### Nordics (Mekonomen)")
            nor_scored = scored[nordic_mask]
            st.metric("# PNs threatened", len(nor_scored))
            st.metric("Rev exposed", f"€{nor_scored['Rev_CY2025_EUR'].sum():,.0f}")
            st.metric("Expected loss", f"€{nor_scored['expected_loss'].sum():,.0f}")
            st.metric("Defend now", int((nor_scored['action_verdict']=='Defend').sum()))
            nor_bl = brand_league(nor_scored).head(5)
            if not nor_bl.empty:
                st.markdown("##### Top brand threats")
                st.dataframe(nor_bl[["brand","tier","pns_threatened","expected_loss_eur"]],
                             use_container_width=True, hide_index=True,
                             column_config={
                                "tier": st.column_config.NumberColumn("Tier", format="%d"),
                                "pns_threatened": st.column_config.NumberColumn("# PNs"),
                                "expected_loss_eur": st.column_config.NumberColumn("EL", format="€%.0f"),
                             })

        st.markdown("---")
        st.caption("EU / DE / FR markets: scrapers tested but Autodoc EU/DE/Mister Auto/Oscaro do not carry Isuzu commercial PNs in their catalogs. No data available — not a scraper bug.")

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 8 — DATA QUALITY
# ═══════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.subheader("Data Quality & Freshness")
    st.caption("Honest signal about what we know vs don't know. Trust the dashboard only as much as the underlying data.")

    dq = data_quality_report(SCRIPT_DIR)
    if dq.empty:
        st.info("No source files found.")
    else:
        # Color-code status
        dq_show = dq[[c for c in ("source", "status", "hits", "hit_rate", "modified") if c in dq.columns]]
        st.dataframe(dq_show, use_container_width=True, hide_index=True,
                     column_config={
                        "hits": st.column_config.NumberColumn("Hits"),
                        "hit_rate": st.column_config.NumberColumn("Hit rate %", format="%.1f%%"),
                     })

        st.markdown("---")
        st.markdown("##### Honest disclosure")
        st.markdown("""
- **Autodoc UK** — only ~37% of PNs return hits because Cloudflare blocks the rest. The blocked ones aren't "no products" — they're "unknown."
- **Mekonomen** — Nordics-only, low Isuzu coverage (~5%). Hits are real (Bosch, Lesjöfors, Raufoss).
- **KS International** — UK Isuzu specialist. ~13% hit rate. KS_AM (aftermarket) vs KS_GEN (parallel-import genuine) distinguished.
- **Autodoc EU / DE / Mister Auto / Oscaro** — confirmed empirically that these sites do not carry Isuzu commercial PNs. Not a scraper bug. EU=country-selector landing page, DE=404 for Isuzu PNs, FR sites=passenger-car focus.
- **Brand tier table** — manually curated, ~57 brands. Not exhaustive; "unknown" tier (Q=30) used as default.
""")

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)

# ═══════════════════════════════════════════════════════════════════════════
# TAB 9 — METHODOLOGY
# ═══════════════════════════════════════════════════════════════════════════
with tabs[9]:
    st.subheader("Methodology — how the numbers are made")
    st.markdown("""
**Design principle:** no math model, no elasticity estimate, no sigmoid. Every number is either **observed** (UIO × interval method) or **looked up in an editable CSV** (substitution method).

### 0. Two complementary models

| Model | Applies to | Source of truth | Inputs |
|---|---|---|---|
| **PMS Lost Sales (UIO method)** — primary | PMS-eligible parts (filters, brakes, clutch) — **62 of 300** scraped | Observed sales vs deterministic potential | UIO × annual service frequency × ISZE GP |
| **Substitution Expected Loss** — fallback | Breakdown parts (sensors, body, electronics) — **238 of 300** | Estimated from price gap × brand tier | Lookup table cells |

### 1. PMS Lost Sales — the right way to compute lost €

> Potential annual demand = **UIO × annual frequency × horizon**
> Lost units = Potential − **actual Qty_CY2025**
> Lost ISZE GP = Lost units × **PR00** × ISZE GP%

This is the same methodology as your existing **ITUK PMS Coverage Calculator**:
- UIO potential = 11,900 (N35+N75 5-year window × 50% potential factor) — sidebar input
- Annual frequencies sourced from `pms_intervals.csv` (oil filter 5.33/yr @ 15000 km, fuel filter 2/yr @ 40000 km, brake pads 2/yr @ 40000 km, etc.)
- Annual mileage assumption: 80,000 km/yr (ISZJ Group No.1 standard)

No probability estimate. We **observe** the gap.

### 2. Substitution model — for breakdown parts only

For non-PMS parts (sensors, body, electronics, structural) we have no service interval, so no UIO-derived expected demand. The substitution model is a **fallback**:

P(substitution) is a **6 × 4 lookup table** in `substitution_probability.csv`:

> "If dealer chain is `N×` more expensive than AM, with a tier-`T` brand, P(workshop switches) = lookup[N][T]"

Then: Expected Loss = P(substitution) × Rev_CY2025 × ISZE GP × horizon

### 3. Apples-to-apples price comparison
- **Dealer sell to workshop (genuine)** = PR00 × 1/(1−DB GM) × 1/(1−DLR GM)
- **AM retail** = cheapest live price across working sources (AD_UK · Mekonomen · KS_AM · KS_GEN), converted to EUR
- **Ratio** = DLR→WS ÷ AM retail. Ratio > 1.0 = dealer chain is more expensive than aftermarket.

### 4. Threat score (T)
**Just the price gap, bucketed.** No weighting, no normalization.

| Price gap ratio | T score |
|---|---|
| < 1.0× (dealer cheaper) | 0 |
| 1.0–1.2× (marginal) | 20 |
| 1.2–1.5× (real) | 40 |
| 1.5–2.0× (significant) | 60 |
| 2.0–3.0× (large) | 80 |
| ≥ 3.0× (extreme) | 100 |

### 5. Quality score (Q)
Brand tier (manual) + OE-supplier flag.

| Brand tier | Q score |
|---|---|
| 4 (Bosch, Denso, Febi, Hengst, NRF, Purflux, Lesjöfors, Raufoss) | 75 |
| 3 (Blue Print, DT Spare Parts, KAVO Parts, Borg & Beck) | 55 |
| 2 (RIDEX, KAMOKA, NB Parts, STARK) | 35 |
| 1 (unknown / unclassified) | 20 |
| **+ 25 if confirmed OE supplier flag** (capped at 100) | |

Source: `iam_brand_tiers.csv` — edit to refine.

### 6. P(substitution) — fallback model for breakdown parts
**A 6 × 4 lookup table.** No formula.

> "If dealer chain is `N×` more expensive than AM, with a tier-`T` brand carrying it, the chance a workshop switches is the cell at (N, T)."

The default table is in `substitution_probability.csv`. Edit it to update the model.

### 7. Expected Loss (€) — for breakdown parts
> Expected Loss = P(substitution) × Rev_CY2025 × ISZE GP% × horizon

That's the whole financial model. Three multiplications.

### 8. Action verdicts
Decision rules, not scores:

| Verdict | Condition |
|---|---|
| **Defend** | EL ≥ 75th percentile **AND** brand tier ≥ 3 |
| **Match**  | EL ≥ median **AND** brand tier < 3 |
| **Monitor**| EL < median **AND** brand tier ≥ 3 **AND** EL > 0 |
| **Cede**   | everything else |

### What's NOT in the model (intentionally)
- Sigmoids, weighted composites, log normalization, coefficient of variation → all removed for transparency
- Sentiment data (Reddit, Trustpilot) → deferred
- Time trend → only one snapshot (add monthly logging)
- Workshop direct-buy share by market
- Stock availability / lead times
- Warranty cost differential genuine vs AM

### Sources
- `ISZE_Parts_Intelligence_v3.xlsx` — PR00, Rev_CY2025, Class, AIM_Category
- Scraped (working): Autodoc UK · Mekonomen · KS International (AM + GEN)
- Confirmed empty (no Isuzu commercial in catalog): Autodoc EU · Autodoc DE · Mister Auto · Oscaro

### How to challenge a number
1. Disagree with the UIO assumption? → sidebar input (default 11,900 = ITUK pilot)
2. Disagree with a PMS service interval? → edit `pms_intervals.csv`
3. Disagree with the P(substitution) for a (gap × tier) combo? → edit `substitution_probability.csv`
4. Disagree with a brand's tier or OE flag? → edit `iam_brand_tiers.csv`
5. Disagree with ISZE GP%, DB margin, DLR margin, or horizon? → sidebar sliders
6. Click rerun. Done.
""")

    with st.expander("Substitution probability table (CSV)", expanded=False):
        try:
            sub_df = pd.read_csv(SCRIPT_DIR / "substitution_probability.csv")
            st.dataframe(sub_df, use_container_width=True, hide_index=True)
            st.caption("Row × column: price_gap_bucket × tier_N = P(workshop switches).")
        except Exception as e:
            st.error(f"Could not load substitution table: {e}")

    with st.expander("Brand tier table (CSV)", expanded=False):
        try:
            tiers = load_brand_tiers()
            st.dataframe(tiers[["brand", "tier", "oe_supplier"]],
                         use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Could not load tier table: {e}")

    st.markdown("---")
    st.caption(METHODOLOGY_FOOTER)
