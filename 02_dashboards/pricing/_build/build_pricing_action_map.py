"""
ISZE Pricing Action Map — data prep.

Fuses (all existing, audited feeds — no new math on raw billing):
  - 01_data/00_derived/pms_opportunity_matrix.csv   (capture + gap EUR + TAM per DB x category, CY2025)
  - 01_data/00_derived/pms_capture_by_db_year.csv   (captured revenue, line_type=total = genuine+BVP)
  - 01_data/00_derived/eucon_price_gap.csv          (network IAM benchmark, 44 PNs, IE40 raw -> street x1.785 here)
  - 01_data/00_derived/price_volume_elasticity.csv  (category elasticity reading, low-power labelled)
  - 01_data/00_derived/parts_catalog_dimension.csv  (PN -> pms_category, authoritative)
  - 04_tools/autodoc_scraper/_HANDOFF_BUNDLE/ks_results.csv  (UK street, PN-level, scraped 2026-05-09)
  - 04_tools/autodoc_scraper/{tranzparts,tmc,auto365}_results.csv (category-level street, scraped 2026-07-13)
  - 04_tools/autodoc_scraper/mekonomen_results.csv  (SE — filtered: repeated-price page artifacts excluded)

Channel normalization: genuine street = ISZE list (IE40/PR00) x 1.40 (DB) x 1.275 (DLR) = x1.785.
Scraper prices are retail/street already. Stated on every price view.

BVP rule: capture = line_type 'total' (genuine+BVP). Genuine->BVP mix is never counted as loss.

Output: pricing_action_map.json (consumed by the dashboard HTML).
"""
from __future__ import annotations
import json
from pathlib import Path

import pandas as pd

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
SCRAPE = ISZE / "04_tools" / "autodoc_scraper"
OUT = Path(__file__).parent / "pricing_action_map.json"

STREET = 1.40 * 1.275  # = 1.785
YEAR = 2025
RAISE_SCENARIO = 0.05  # +5% list scenario, labelled as scenario in UI

# ---------------------------------------------------------------------------
# Mekonomen RETIRED 2026-09-24 (Jerome's go, card 0.4/C3) — see mekonomen_filtered().
# The seven PNs below were all false: the site's part-number search echoes the query
# and serves an unrelated in-stock item. Re-enable only with a real product page
# showing the part number and a price together.
# ---------------------------------------------------------------------------
MEKONOMEN_RETIRED = True
MEKONOMEN_FALSE_PNS = frozenset({
    "8975056801",  # PAD KIT; CALIPER,DISC BRK,FRT -> returned a Kilen coil spring, 957 SEK
    "8983373180",  # SENSOR ASM; DEF TANK
    "8982932120",  # DRIVE ASM; FINAL,RR
    "8982924321",  # SENSOR; SPD,FRT WHEEL
    "8983937793",  # SUPPORT; RR BUMPER
    "8983288004",  # LAMP ASM; RR COMB
    "8982606011",  # DOOR ASM; FRT,WO/TRIM
})

CAT_LABEL = {
    "oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
    "blower_filter": "Cabin/blower filter", "urea_filter": "Urea filter",
    "brake_pad": "Brake pads", "brake_pad_front": "Brake pads (frt)", "brake_pad_rear": "Brake pads (rr)",
    "brake_rotor": "Brake rotors", "brake_shoe": "Brake shoes",
    "brake_shoe_front": "Brake shoes (frt)", "brake_shoe_rear": "Brake shoes (rr)",
    "clutch_disc": "Clutch disc", "clutch_kit": "Clutch kit", "clutch_pressure_plate": "Pressure plate",
    "clutch_booster": "Clutch booster", "release_bearing": "Release bearing", "pilot_bearing": "Pilot bearing",
}
# coarse scraper bucket -> matrix categories (display mapping only, per bridge ROLLUP)
COARSE = {
    "oil_filter": ["oil_filter"], "fuel_filter": ["fuel_filter"], "air_filter": ["air_filter"],
    "clutch": ["clutch_disc", "clutch_kit", "clutch_pressure_plate", "release_bearing", "pilot_bearing", "clutch_booster"],
    "brake": ["brake_pad", "brake_pad_front", "brake_pad_rear", "brake_rotor",
              "brake_shoe", "brake_shoe_front", "brake_shoe_rear"],
}


def load_matrix() -> pd.DataFrame:
    m = pd.read_csv(DERIVED / "pms_opportunity_matrix.csv")
    m = m[(m.year == YEAR) & (m.tam_eur > 0)].copy()
    # guard against parent + front/rear double counting within one DB
    for db, g in m.groupby("distributor_code"):
        cats = set(g[g.tam_eur > 0].pms_category)
        for parent, kids in [("brake_pad", {"brake_pad_front", "brake_pad_rear"}),
                             ("brake_shoe", {"brake_shoe_front", "brake_shoe_rear"})]:
            assert not (parent in cats and cats & kids), f"double count {db} {parent}"
    return m


def load_captured() -> pd.DataFrame:
    c = pd.read_csv(DERIVED / "pms_capture_by_db_year.csv")
    c = c[(c.year == YEAR) & (c.line_type == "total")]
    return c.groupby(["distributor_code", "pms_category"], as_index=False).agg(
        captured_rev_eur=("actual_rev_eur", "sum"))


def eucon_by_category() -> tuple[pd.DataFrame, pd.DataFrame]:
    eu = pd.read_csv(DERIVED / "eucon_price_gap.csv")
    cat = pd.read_csv(DERIVED / "parts_catalog_dimension.csv", dtype={"part_number": str}, low_memory=False)
    eu["pn"] = eu["pn"].astype(str)
    eu = eu.merge(cat[["part_number", "pms_category"]].drop_duplicates("part_number"),
                  left_on="pn", right_on="part_number", how="left")
    eu["street_eur"] = eu["ISZE_IE40_Price_EUR"] * STREET
    eu["street_delta_pct"] = eu["street_eur"] / eu["Avg_Competitor_EUR"] - 1
    eu["undercut"] = eu["Avg_Competitor_EUR"] < eu["street_eur"]
    by_cat = (eu.dropna(subset=["pms_category"])
                .groupby("pms_category", as_index=False)
                .agg(n_pns=("pn", "count"),
                     med_street_delta_pct=("street_delta_pct", "median"),
                     rev_eur=("rev_eur", "sum"),
                     undercut_pns=("undercut", "sum")))
    return by_cat, eu


def ks_by_category() -> tuple[pd.DataFrame, str]:
    # live file, restored + maintained non-destructively by the weekly refresh task since 2026-07-16
    ks = pd.read_csv(SCRAPE / "ks_results.csv", dtype={"PN": str})
    ks_date = str(ks["Scraped_At"].max())[:10]
    cat = pd.read_csv(DERIVED / "parts_catalog_dimension.csv", dtype={"part_number": str}, low_memory=False)
    ks = ks.merge(cat[["part_number", "pms_category"]].drop_duplicates("part_number"),
                  left_on="PN", right_on="part_number", how="left")
    # observed street premium: KS genuine listing vs KS IAM listing, same shop, same PN
    both = ks.dropna(subset=["KS_GEN_MinPrice_GBP", "KS_AM_MinPrice_GBP", "pms_category"]).copy()
    both["premium_pct"] = both.KS_GEN_MinPrice_GBP / both.KS_AM_MinPrice_GBP - 1
    obs = both.groupby("pms_category", as_index=False).agg(
        n_pns=("PN", "count"), med_premium_pct=("premium_pct", "median"))
    # derived street premium: PR00 x 1.785 vs KS IAM
    am = ks.dropna(subset=["KS_AM_MinPrice_GBP", "PR00_EUR", "pms_category"]).copy()
    # KS is GBP; PR00 EUR. Use in-file EUR conversion factor from tranzparts (GBP->EUR 1.17)
    am["derived_premium_pct"] = (am.PR00_EUR * STREET) / (am.KS_AM_MinPrice_GBP * 1.17) - 1
    der = am.groupby("pms_category", as_index=False).agg(
        n_am=("PN", "count"), med_derived_premium_pct=("derived_premium_pct", "median"))
    return obs.merge(der, on="pms_category", how="outer"), ks_date


def coarse_scrapers() -> pd.DataFrame:
    frames = []
    for f, market in [("tranzparts_results.csv", "UK"), ("tmc_results.csv", "UK"),
                      ("auto365_results.csv", "IL")]:
        df = pd.read_csv(SCRAPE / f)
        df = df.dropna(subset=["PMS_Category", "Price_EUR"])
        df["market"] = market
        frames.append(df[["market", "Site", "PMS_Category", "Price_EUR"]])
    all_ = pd.concat(frames)
    return all_.groupby(["market", "PMS_Category"], as_index=False).agg(
        n=("Price_EUR", "count"), med_iam_street_eur=("Price_EUR", "median"))


def mekonomen_filtered() -> pd.DataFrame:
    """RETIRED 2026-09-24 — Mekonomen's part-number search returns unrelated items.

    Asking for 8975056801 "PAD KIT; CALIPER,DISC BRK,FRT" returned a Kilen coil spring
    at 957 SEK; every part number returned exactly one unrelated item on every snapshot
    from 2026-07-09 to 2026-09-22. All seven rows were false. The earlier artifact guard
    below (identical price on >=3 unrelated PNs) did NOT catch them, because each one
    carried a different price — so it is not a usable guard for this failure.

    Returns an empty frame. The seven PNs are named so they can never re-enter, and the
    scraper is out of the weekly run (see autodoc_scraper/refresh_and_check_drift.py).
    """
    if MEKONOMEN_RETIRED:
        print("  Mekonomen: RETIRED — source not read; no price evidence from it")
        return pd.DataFrame(columns=["PN", "suspect"])
    mek = pd.read_csv(SCRAPE / "mekonomen_results.csv", dtype={"PN": str})
    mek = mek[~mek["PN"].isin(MEKONOMEN_FALSE_PNS)]
    hit = mek.dropna(subset=["MEK_AM_MinPrice_SEK"]).copy()
    # page-artifact guard: identical min price on >=3 unrelated PNs = search-page chrome, not a part price
    counts = hit.MEK_AM_MinPrice_SEK.value_counts()
    artifacts = set(counts[counts >= 3].index)
    hit["suspect"] = hit.MEK_AM_MinPrice_SEK.isin(artifacts)
    return hit


def main() -> None:
    m = load_matrix()
    cap = load_captured()
    m = m.merge(cap, on=["distributor_code", "pms_category"], how="left")
    m["captured_rev_eur"] = m["captured_rev_eur"].fillna(0.0)
    m["capture_capped"] = m["capture_rate_total"].clip(upper=1.0)

    # decision classification per DB x category
    def classify(r):
        if r.capture_capped >= 0.80:
            return "raise"          # captive: headroom scenario
        if r.capture_capped >= 0.45:
            return "contested"
        return "defend"             # majority of wallet already at IAM
    m["zone"] = m.apply(classify, axis=1)
    m["headroom_eur"] = (m.captured_rev_eur * RAISE_SCENARIO).where(m.zone == "raise", 0.0)
    m["at_risk_eur"] = m.revenue_gap_eur.where(m.zone != "raise", 0.0)

    ela = pd.read_csv(DERIVED / "price_volume_elasticity.csv")
    ela_map = ela.set_index("category")[["reading", "low_power"]].to_dict("index")

    eu_cat, eu_pn = eucon_by_category()
    ks, ks_date = ks_by_category()
    coarse = coarse_scrapers()
    mek = mekonomen_filtered()

    price_ev = {}
    for _, r in eu_cat.iterrows():
        price_ev.setdefault(r.pms_category, {})["eucon"] = {
            "n": int(r.n_pns), "med_street_delta_pct": round(float(r.med_street_delta_pct), 3),
            "undercut_pns": int(r.undercut_pns)}
    for _, r in ks.iterrows():
        d = price_ev.setdefault(r.pms_category, {})
        if pd.notna(r.get("med_premium_pct")):
            d["ks_observed"] = {"n": int(r.n_pns), "med_premium_pct": round(float(r.med_premium_pct), 3)}
        if pd.notna(r.get("med_derived_premium_pct")):
            d["ks_derived"] = {"n": int(r.n_am), "med_premium_pct": round(float(r.med_derived_premium_pct), 3)}

    rows = []
    for _, r in m.iterrows():
        rows.append({
            "db": r.distributor_code, "cat": r.pms_category,
            "label": CAT_LABEL.get(r.pms_category, r.pms_category),
            "capture": round(float(r.capture_capped), 4),
            "tam": round(float(r.tam_eur)), "gap": round(float(r.revenue_gap_eur)),
            "captured": round(float(r.captured_rev_eur)),
            "zone": r.zone,
            "headroom": round(float(r.headroom_eur)), "at_risk": round(float(r.at_risk_eur)),
            "elasticity": ela_map.get(r.pms_category, {}).get("reading"),
        })

    top_eucon = eu_pn.dropna(subset=["Avg_Competitor_EUR"]).nlargest(15, "rev_eur")[
        ["pn", "description", "pms_category", "rev_eur", "ISZE_IE40_Price_EUR",
         "street_eur", "Avg_Competitor_EUR", "street_delta_pct", "Brands_Found"]]
    mek_clean = mek[~mek.suspect]

    # DB-level context: AIM competitive exposure + Eucon street-undercut + captive base
    aimx = pd.read_csv(DERIVED / "aim_exposure_by_db_year.csv")
    aimx = aimx[aimx.year == YEAR]
    risk = pd.read_csv(DERIVED / "db_aftersales_risk.csv")
    risk = risk[risk.year == YEAR]
    mix = pd.read_csv(DERIVED / "db_parts_mix_classification.csv")
    mix = mix[mix.year == YEAR]
    db_ctx = (aimx[["distributor_code", "net_sales_eur", "high_risk_rev_eur", "high_risk_rev_pct"]]
              .merge(risk[["distributor_code", "risk_score", "eucon_undercut_rev_eur", "eucon_undercut_pct"]],
                     on="distributor_code", how="left")
              .merge(mix[["distributor_code", "genuine_only_eur", "genuine_only_pct", "bvp_pct"]],
                     on="distributor_code", how="left"))
    db_ctx["captive_rev_eur"] = db_ctx.net_sales_eur - db_ctx.high_risk_rev_eur.fillna(0)
    db_ctx["plus1pct_eur"] = db_ctx.captive_rev_eur * 0.01

    out = {
        "meta": {
            "built": pd.Timestamp.now().strftime("%Y-%m-%d"), "year": YEAR,
            "street_factor": STREET, "raise_scenario": RAISE_SCENARIO,
            "sources": {
                "capture": "pms_opportunity_matrix / pms_capture_by_db_year (pipeline verify green 2026-07-06)",
                "eucon": "eucon_price_gap.csv (44 PNs, network)",
                "ks": f"KS International UK, scraped {ks_date}"
                      + (" (stale flag)" if ks_date < "2026-07-01" else ""),
                "coarse": "Tranzparts/TMC (UK), Auto365 (IL), scraped 2026-07-13",
                "mekonomen": "RETIRED 2026-09-24 — search returned unrelated items; no price evidence used",
            },
        },
        "cells": rows,
        "db_context": db_ctx.round(2).to_dict("records"),
        "price_evidence": price_ev,
        "coarse_street": coarse.to_dict("records"),
        "eucon_top": top_eucon.round(2).to_dict("records"),
        "mekonomen": {
            "retired": True,
            "clean": [],   # no row is usable — every one of the seven was a false match
            "suspect_n": 0,
        },
    }
    def denan(o):
        if isinstance(o, dict):
            return {k: denan(v) for k, v in o.items()}
        if isinstance(o, list):
            return [denan(v) for v in o]
        if isinstance(o, float) and o != o:  # NaN — invalid in browser JSON
            return None
        return o

    OUT.write_text(json.dumps(denan(out), indent=1, allow_nan=False), encoding="utf-8")

    tot_head = sum(r["headroom"] for r in rows)
    tot_risk = sum(r["at_risk"] for r in rows)
    print(f"cells={len(rows)}  headroom(+5% scenario)=EUR {tot_head:,.0f}  at-risk gap=EUR {tot_risk:,.0f}")
    print(m.groupby("zone").agg(n=("distributor_code", "count"),
                                headroom=("headroom_eur", "sum"),
                                at_risk=("at_risk_eur", "sum")))
    print("\nTop raise cells:")
    print(m[m.zone == "raise"].nlargest(8, "headroom_eur")[
        ["distributor_code", "pms_category", "capture_capped", "captured_rev_eur", "headroom_eur"]])
    print("\nTop defend cells:")
    print(m[m.zone == "defend"].nlargest(8, "at_risk_eur")[
        ["distributor_code", "pms_category", "capture_capped", "revenue_gap_eur"]])
    print("\nPrice evidence cats:", sorted(price_ev.keys()))


if __name__ == "__main__":
    main()
