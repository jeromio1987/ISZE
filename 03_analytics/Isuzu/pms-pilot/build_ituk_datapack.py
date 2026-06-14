"""
ISZE ITUK Data Pack v1 — Tier S use cases in one Excel.

Reads the on-disk derived CSVs (no fresh computation, no scraping) and produces
ISZE_ITUK_DataPack_v1.xlsx with the following sheets:

  1. README                — guide to the pack
  2. WhiteSpace            — per distributor × subgroup: addressable PNs vs sold
  3. PricingGap_Pairs      — per Genuine↔BVP pair: ASP gap, who's winning
  4. Substitution_Momentum — Genuine ↓ + BVP ↑ signal, ranked by severity
  5. ITUK_vs_Network_PMS   — ITUK SPU/GPS vs network median per PMS subgroup
  6. Kosha_Gap_OneNumber   — single PMS revenue-gap number for the narrative
  7. AIM_BVP_CrossLink     — where AIM is heavy + BVP penetration low
  8. UREA_QuickWin         — UREA filter (Euro 6 PMS) penetration snapshot

All inputs from C:\\Users\\jerom\\Desktop\\claude\\ISZE\\Data\\derived\\.
Run: python build_ituk_datapack.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import numpy as np

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\Data\derived")
OUT = Path(__file__).parent / "ISZE_ITUK_DataPack_v1.xlsx"
ITUK = "ITUK"

PMS_SUBGROUPS_NARROW = {
    "oil_filter", "fuel_filter", "air_filter",
    "brake_pad", "brake_shoe",
    "clutch_disc", "clutch_pressure_plate",
}

SUBGROUP_LABEL = {
    "oil_filter": "Oil filter",
    "fuel_filter": "Fuel filter",
    "air_filter": "Air filter",
    "blower_filter": "Cabin / blower filter",
    "urea_filter": "Urea (AdBlue) filter",
    "brake_pad": "Brake pads",
    "brake_shoe": "Brake shoes",
    "brake_lining": "Brake lining",
    "brake_rotor": "Brake rotor",
    "clutch_kit": "Clutch kit",
    "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate",
    "clutch_booster": "Clutch booster",
    "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing",
    "center_bearing": "Center bearing",
    "shock_absorber": "Shock absorber",
    "leaf_spring": "Leaf spring",
    "bushing": "Bushing",
    "king_pin": "King pin kit",
    "wheel_pin": "Wheel pin",
    "hub_bearing": "Hub bearing",
    "hub_oil_seal": "Hub oil seal",
    "fan_belt": "Fan belt",
    "water_pump": "Water pump",
    "engine_mount": "Engine foot rubber",
    "generator": "Generator",
    "starter": "Starter",
    "wiper_blade": "Wiper blade",
}


def _label(s):
    return SUBGROUP_LABEL.get(s, str(s).replace("_", " ").title()) if pd.notna(s) else "—"


def build_readme():
    return pd.DataFrame(
        [
            ("Pack", "ISZE ITUK Data Pack v1"),
            ("Purpose", "Tier-S evidence pack for ITUK pricing conversation + Kosha narrative"),
            ("Source", "C:\\Users\\jerom\\Desktop\\claude\\ISZE\\Data\\derived\\ (lifetime through CY2025)"),
            ("Sheets", ""),
            ("WhiteSpace", "Per distributor × BVP subgroup: how many PNs CAN they sell (addressable basket) vs how many they DO sell. Distributor 'white space' = (addressable − sold)."),
            ("PricingGap_Pairs", "Per Genuine↔BVP pair: avg sell price both sides, premium %, where Genuine is most exposed to BVP price."),
            ("Substitution_Momentum", "Per (distributor × subgroup) rows where BVP unit share rose YoY while Genuine units fell YoY. Smoking-gun substitution signal."),
            ("ITUK_vs_Network_PMS", "ITUK GPS / SPU / capture rate per PMS subgroup vs network median. Direct quantification of 'ITUK pays X% more than network for fuel filters'."),
            ("Kosha_Gap_OneNumber", "Single PMS revenue-gap € figure = sum of revenue_gap_eur across PMS subgroups, latest year, total + by distributor top-15."),
            ("AIM_BVP_CrossLink", "Per (distributor × product_family): AIM high-risk € share × BVP € share. Highest substitution opportunity = high AIM + low BVP."),
            ("UREA_QuickWin", "UREA / AdBlue filter (Euro 6 PMS, currently outside dashboard scope). Per distributor: sales today vs UIO-implied opportunity."),
        ],
        columns=["Section", "Description"],
    )


# ── 1. White-space per distributor ───────────────────────────────────────────
def build_whitespace() -> pd.DataFrame:
    abk = pd.read_csv(DERIVED / "bvp_addressable_basket.csv")
    # addressable basket has currently_selling_bvp; rollup per (distributor × subgroup)
    grp = abk.groupby(
        ["distributor_code", "product_subgroup", "product_family"], as_index=False
    ).agg(
        addressable_bvp_pns=("bvp_pn", "nunique"),
        selling_bvp_pns=("currently_selling_bvp", "sum"),
    )
    grp["selling_bvp_pns"] = grp["selling_bvp_pns"].astype(int)
    grp["whitespace_pns"] = grp["addressable_bvp_pns"] - grp["selling_bvp_pns"]
    grp["penetration_pct"] = (grp["selling_bvp_pns"] / grp["addressable_bvp_pns"] * 100).round(1)
    grp["subgroup_label"] = grp["product_subgroup"].map(_label)
    grp = grp.sort_values(["distributor_code", "whitespace_pns"], ascending=[True, False])
    return grp[[
        "distributor_code", "product_family", "product_subgroup", "subgroup_label",
        "addressable_bvp_pns", "selling_bvp_pns", "whitespace_pns", "penetration_pct",
    ]]


# ── 2. Pricing-gap per Genuine↔BVP pair ──────────────────────────────────────
def build_pricing_gap() -> pd.DataFrame:
    pp = pd.read_csv(DERIVED / "price_premium.csv")
    pp["subgroup_label"] = pp["pms_category"].map(_label)
    pp = pp.sort_values(["year", "distributor_code", "price_premium_pct"], ascending=[False, True, False])
    # Most exposed first (highest premium = biggest opportunity for BVP)
    cols = [
        "year", "distributor_code", "pms_category", "subgroup_label",
        "genuine_asp_eur", "bvp_asp_eur", "price_premium_pct",
        "genuine_units", "bvp_units" if "bvp_units" in pp.columns else "genuine_unit_share",
    ]
    return pp[[c for c in cols if c in pp.columns]]


# ── 3. Substitution momentum ─────────────────────────────────────────────────
def build_substitution_momentum() -> pd.DataFrame:
    mix = pd.read_csv(DERIVED / "mix_genuine_bvp_pms.csv")
    # Filter to rows with YoY columns populated
    cols_needed = [
        "year", "distributor_code", "product_subgroup",
        "bvp_share_units_yoy_pp", "genuine_qty_yoy_pct", "substitution_flag",
        "bvp_qty", "genuine_qty", "bvp_eur", "genuine_eur",
    ]
    cols_present = [c for c in cols_needed if c in mix.columns]
    sub = mix[cols_present].copy()
    sub["subgroup_label"] = sub["product_subgroup"].map(_label)
    # Severity score = bvp_share_yoy_pp - genuine_qty_yoy_pct (positive = bvp rising faster than genuine declining)
    if "bvp_share_units_yoy_pp" in sub.columns and "genuine_qty_yoy_pct" in sub.columns:
        sub["severity_score"] = sub["bvp_share_units_yoy_pp"].fillna(0) - sub["genuine_qty_yoy_pct"].fillna(0).clip(upper=0)
    # Filter to flagged rows or material moves
    if "substitution_flag" in sub.columns:
        signal = sub[sub["substitution_flag"].fillna(False).astype(bool)].copy()
    else:
        signal = sub[
            (sub.get("bvp_share_units_yoy_pp", 0).fillna(0) > 5)
            & (sub.get("genuine_qty_yoy_pct", 0).fillna(0) < -5)
        ].copy()
    signal = signal.sort_values("severity_score", ascending=False) if "severity_score" in signal.columns else signal
    return signal


# ── 4. ITUK vs network median per PMS subgroup ──────────────────────────────
def build_ituk_vs_network() -> pd.DataFrame:
    spu = pd.read_csv(DERIVED / "gps_spu_pms.csv")
    cap = pd.read_csv(DERIVED / "pms_capture_by_db_year.csv")
    # Use total line_type for both; latest year
    latest_year = int(spu["year"].max())
    spu_l = spu[(spu["year"] == latest_year) & (spu["line_type"] == "all")].copy() if "line_type" in spu.columns else spu[spu["year"] == latest_year].copy()
    # Compute network median per pms_category
    spu_med = spu_l.groupby("pms_category", as_index=False).agg(
        network_median_spu_eur=("net_sales_eur", "median"),
        network_median_uio=("uio_units", "median"),
    )
    # ITUK row
    ituk = spu_l[spu_l["distributor_code"] == ITUK][[
        "pms_category", "net_sales_eur", "uio_units"
    ]].rename(columns={"net_sales_eur": "ituk_net_sales_eur", "uio_units": "ituk_uio"})
    out = spu_med.merge(ituk, on="pms_category", how="left")
    out["subgroup_label"] = out["pms_category"].map(_label)
    out["ituk_spu_eur"] = out["ituk_net_sales_eur"] / out["ituk_uio"].replace(0, np.nan)
    out["network_spu_eur"] = out["network_median_spu_eur"] / out["network_median_uio"].replace(0, np.nan)
    out["spu_vs_network_pct"] = ((out["ituk_spu_eur"] - out["network_spu_eur"]) / out["network_spu_eur"] * 100).round(1)
    # add capture from pms_capture
    cap_l = cap[(cap["year"] == latest_year) & (cap["line_type"] == "total") & (cap["distributor_code"] == ITUK)]
    if "capture_rate" in cap_l.columns:
        cap_short = cap_l[["pms_category", "capture_rate"]].rename(columns={"capture_rate": "ituk_capture_rate"})
        out = out.merge(cap_short, on="pms_category", how="left")
    # network median capture
    cap_net = cap[(cap["year"] == latest_year) & (cap["line_type"] == "total")]
    if "capture_rate" in cap_net.columns:
        net_cap = cap_net.groupby("pms_category", as_index=False)["capture_rate"].median().rename(columns={"capture_rate": "network_median_capture"})
        out = out.merge(net_cap, on="pms_category", how="left")
    out["capture_gap_pp"] = ((out.get("ituk_capture_rate", 0) - out.get("network_median_capture", 0)) * 100).round(1)
    return out[[
        "pms_category", "subgroup_label",
        "ituk_spu_eur", "network_spu_eur", "spu_vs_network_pct",
        "ituk_capture_rate", "network_median_capture", "capture_gap_pp",
    ]].sort_values("spu_vs_network_pct", ascending=False)


# ── 5. Kosha gap — one number + top-15 distributor breakdown ────────────────
def build_kosha_gap() -> tuple[pd.DataFrame, float]:
    opp = pd.read_csv(DERIVED / "pms_opportunity_matrix.csv")
    latest_year = int(opp["year"].max())
    opp_l = opp[opp["year"] == latest_year]
    total_gap = float(opp_l["revenue_gap_eur"].sum())
    by_dist = opp_l.groupby("distributor_code", as_index=False).agg(
        revenue_gap_eur=("revenue_gap_eur", "sum"),
        tam_eur=("tam_eur", "sum") if "tam_eur" in opp_l.columns else ("revenue_gap_eur", "sum"),
    )
    by_dist["gap_share_of_tam"] = (by_dist["revenue_gap_eur"] / by_dist["tam_eur"] * 100).round(1)
    by_dist = by_dist.sort_values("revenue_gap_eur", ascending=False).head(15)
    by_dist.loc[len(by_dist)] = ["TOTAL_NETWORK", total_gap, by_dist["tam_eur"].sum(), None]
    return by_dist, total_gap


# ── 6. AIM × BVP cross-link ─────────────────────────────────────────────────
def build_aim_bvp_crosslink() -> pd.DataFrame:
    aim = pd.read_csv(DERIVED / "aim_bvp_family_risk.csv")
    latest_year = int(aim["year"].max())
    aim_l = aim[aim["year"] == latest_year].copy()
    # Substitution opportunity = high AIM exposure + low BVP share = where IAM is eating us and Isuzu's own competitive line is under-deployed
    aim_l["opportunity_score"] = (
        aim_l["aim_high_risk_rev_pct"].fillna(0) * 100
        * (1 - aim_l["bvp_share_eur"].fillna(0))
    ).round(1)
    aim_l = aim_l.sort_values("opportunity_score", ascending=False)
    return aim_l[[
        "distributor_code", "product_family", "aim_l1_hints",
        "genuine_eur", "bvp_eur", "bvp_share_eur",
        "aim_high_risk_rev_eur", "aim_high_risk_rev_pct",
        "opportunity_score",
    ]].head(80)


# ── 7. UREA filter quick-win ─────────────────────────────────────────────────
def build_urea() -> pd.DataFrame:
    swx = pd.read_parquet(DERIVED / "sales_with_crossref.parquet")
    xref = pd.read_csv(DERIVED / "genuine_bvp_crossref.csv")
    urea_pairs = xref[xref["product_subgroup"] == "urea_filter"]
    gen_pns = set(urea_pairs["genuine_pn"].astype(str))
    bvp_pns = set(urea_pairs["bvp_pn"].astype(str))
    urea_pns = gen_pns | bvp_pns
    s = swx[swx["part_number"].astype(str).isin(urea_pns)].copy() if "part_number" in swx.columns else pd.DataFrame()
    if not s.empty:
        s = s.copy()
        s["role"] = np.where(s["part_number"].astype(str).isin(gen_pns), "genuine", "bvp")
        # Aggregate flat (no pivot)
        rollup = s.groupby(["distributor_code", "role"], as_index=False).agg(
            units=("billed_qty", "sum"),
            net_sales_eur=("net_sales_value", "sum"),
        )
        # Wide form: distributor × role pivot
        units = rollup.pivot(index="distributor_code", columns="role", values="units").fillna(0)
        sales = rollup.pivot(index="distributor_code", columns="role", values="net_sales_eur").fillna(0)
        units.columns = [f"units_{c}" for c in units.columns]
        sales.columns = [f"eur_{c}" for c in sales.columns]
        rollup = units.join(sales).reset_index()
    else:
        rollup = pd.DataFrame(columns=["distributor_code"])
    # Layer UIO from GPS table
    gps = pd.read_csv(DERIVED / "gps_spu_by_distributor.csv")
    latest_year = int(gps["year"].max())
    gps_l = gps[gps["year"] == latest_year][["distributor_code", "country", "region", "uio_units"]]
    out = rollup.merge(gps_l, on="distributor_code", how="left")
    out = out.rename(columns={"uio_units": "uio_latest"})
    out["pairs_count_in_catalog"] = len(urea_pairs)
    out = out.sort_values("uio_latest", ascending=False, na_position="last")
    return out


def main():
    print("Reading derived data…")
    readme = build_readme()
    print("  WhiteSpace…")
    ws = build_whitespace()
    print(f"    {len(ws):,} rows")
    print("  PricingGap_Pairs…")
    pg = build_pricing_gap()
    print(f"    {len(pg):,} rows")
    print("  Substitution_Momentum…")
    sm = build_substitution_momentum()
    print(f"    {len(sm):,} rows")
    print("  ITUK_vs_Network_PMS…")
    iv = build_ituk_vs_network()
    print(f"    {len(iv):,} rows")
    print("  Kosha_Gap_OneNumber…")
    kosha_tbl, kosha_total = build_kosha_gap()
    print(f"    network gap (latest year): EUR {kosha_total:,.0f}")
    print("  AIM_BVP_CrossLink…")
    aim = build_aim_bvp_crosslink()
    print(f"    {len(aim):,} rows")
    print("  UREA_QuickWin…")
    urea = build_urea()
    print(f"    {len(urea):,} rows")

    print(f"\nWriting {OUT}…")
    with pd.ExcelWriter(OUT, engine="openpyxl") as xl:
        readme.to_excel(xl, sheet_name="README", index=False)
        ws.to_excel(xl, sheet_name="WhiteSpace", index=False)
        pg.to_excel(xl, sheet_name="PricingGap_Pairs", index=False)
        sm.to_excel(xl, sheet_name="Substitution_Momentum", index=False)
        iv.to_excel(xl, sheet_name="ITUK_vs_Network_PMS", index=False)
        kosha_tbl.to_excel(xl, sheet_name="Kosha_Gap_OneNumber", index=False)
        aim.to_excel(xl, sheet_name="AIM_BVP_CrossLink", index=False)
        urea.to_excel(xl, sheet_name="UREA_QuickWin", index=False)
    print(f"Done — {OUT.name} written.")


if __name__ == "__main__":
    main()
