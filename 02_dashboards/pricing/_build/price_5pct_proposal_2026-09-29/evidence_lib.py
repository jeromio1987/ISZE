"""Per-line evidence on the in-scope revision base, replicating the logic of
02_dashboards/pricing/_build/build_pricing_simulation_spec_basis.py (2026-09-20):
captured-demand zone ladder + independent-market benchmark with evidence tiers."""
import os
import sys

import numpy as np
import pandas as pd

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
PRISM = os.path.join(ISZE, "03_analytics", "Isuzu", "prism")
SNAP = os.path.join(ISZE, "04_tools", "autodoc_scraper", "_snapshots", "2026-09-15")

CATEGORY_LABELS = {
    "air_filter": "Air Filter", "blower_filter": "Blower Unit Filter", "brake_pad": "Brake Pad",
    "brake_rotor": "Brake Rotor", "brake_shoe": "Brake Shoe", "clutch_booster": "Clutch Booster",
    "clutch_disc": "Clutch Disc", "clutch_kit": "Clutch Kit",
    "clutch_pressure_plate": "Clutch Pressure Plate", "fuel_filter": "Fuel Filter",
    "oil_filter": "Oil Filter", "pilot_bearing": "Pilot Bearing", "release_bearing": "Release Bearing",
    "urea_filter": "Urea (AdBlue) Filter",
}
FILTER_WORDS = [("OIL", "oil_filter"), ("FUEL", "fuel_filter"), ("UREA", "urea_filter"),
                ("ADBLUE", "urea_filter"), ("BLOWER", "blower_filter"), ("AIR", "air_filter")]


def market_of(row):
    c = str(row["customer_code"]).strip()
    if c == "1799":
        return "UTI"
    if c == "1797":
        return "UMI"
    if row.get("region") == "CIS":
        return "CIS"
    if row.get("distributor_code") in ("ITUK", "IUK"):
        return "UK (ITUK + IUK)"
    return "PR00"


def load_base():
    df = pd.read_csv(os.path.join(DERIVED, "price_bp_weighted_compare_pn.csv"), dtype={"part_number": str})
    dd = pd.read_csv(os.path.join(DERIVED, "distributor_dimension.csv"), dtype=str)
    ins = df[df["in_scope"] == True].copy()  # noqa: E712
    ins["pn"] = ins["part_number"].str.strip()
    ins["movable"] = ins["bp_new_jpy"].notna() & ins["bp_prior_revised"].notna()
    # fill distributor/region labels from the dimension where the base file left them blank
    dmap = dd.drop_duplicates("sold_to_sap").set_index("sold_to_sap")
    code = ins["customer_code"].astype(str)
    ins["distributor_code"] = ins["distributor_code"].where(ins["distributor_code"].notna(),
                                                            code.map(dmap["distributor_code"]))
    ins["region"] = ins["region"].where(ins["region"].notna(), code.map(dmap["region"]))
    ins["market"] = ins.apply(market_of, axis=1)
    return ins


def attach_evidence(priced):
    sys.path.insert(0, PRISM)
    from modules.pms_engine import PMS_PN_REGISTRY, _MULTI_MODEL  # noqa: E402

    enq = pd.read_parquet(os.path.join(DERIVED, "pricing_pn_enquiry.parquet"),
                          columns=["part_number", "source", "sp_eur_pr00_ie40"])
    enq["pn"] = enq["part_number"].astype(str).str.strip()
    enq = enq.drop(columns=["part_number"]).drop_duplicates("pn")
    priced = priced.merge(enq.rename(columns={"source": "supply_source"}), on="pn", how="left")

    registry = {}
    for k, v in PMS_PN_REGISTRY.items():
        registry[str(int(k))] = v.get("category")
    for k, v in _MULTI_MODEL.items():
        registry.setdefault(str(int(k)), v[0].get("category"))
    bvp = pd.read_csv(os.path.join(DERIVED, "bvp_pn_dimension.csv"), dtype={"part_number": str})
    bvp["pn"] = bvp["part_number"].str.strip()
    bvp = bvp.drop_duplicates("pn")
    bvp_map = dict(zip(bvp["pn"], bvp["pms_category"]))
    bvp_family = dict(zip(bvp["pn"], bvp["product_family"]))

    def service_category(row):
        pn = row["pn"].lstrip("0")
        if pn in registry:
            return registry[pn]
        if bvp_family.get(row["pn"]) == "PMS_Filters":
            desc = str(row["billed_description"] or "").upper()
            for word, cat in FILTER_WORDS:
                if word in desc:
                    return cat
            return bvp_map.get(row["pn"])
        return None

    priced["service_category"] = priced.apply(service_category, axis=1)

    cap = pd.read_csv(os.path.join(DERIVED, "pms_capture_by_db_year.csv"))
    cap25 = cap[(cap["year"] == 2025) & (cap["line_type"] == "total")]
    cap_map = {(r.distributor_code, r.pms_category): r.capture_rate for r in cap25.itertuples()}
    cats14 = sorted(CATEGORY_LABELS)
    bvp_alt = bvp[bvp["in_bvp_catalog"] == True].groupby("pms_category").size().to_dict()  # noqa: E712
    family_contested = {c: (bvp_alt.get(c, 0) > 0) for c in cats14}
    auto = pd.read_csv(os.path.join(DERIVED, "competitiveness_autodoc_risk.csv"), dtype={"part_number": str})
    auto_pns = set(auto["part_number"].str.strip())
    aim_v2 = pd.read_csv(os.path.join(DERIVED, "aim_pn_classification_20260920.csv"),
                         usecols=["part_number", "catalog_node_present", "catalog_residual"], dtype=str)
    aim_v2["pn"] = aim_v2["part_number"].str.strip()
    aim_cat = dict(zip(aim_v2["pn"], aim_v2["catalog_node_present"]))
    aim_res = dict(zip(aim_v2["pn"], aim_v2["catalog_residual"]))

    def classify(row):
        cat, code = row["service_category"], row["distributor_code"]
        if pd.notna(cat) and cat in CATEGORY_LABELS and pd.notna(code):
            rate = cap_map.get((code, cat))
            if rate is not None and np.isfinite(rate):
                zone = "Captive" if rate >= 0.80 else "Contested" if rate >= 0.45 else "Lost"
                return zone, "Measured", rate
            return "Not classified", "No measure", np.nan
        if row["pn"] in auto_pns:
            return "Contested", "Proxy: competitor file", np.nan
        if bvp_family.get(row["pn"]) == "PMS_Filters":
            return ("Contested" if family_contested.get(cat or "", False) else "Captive"), "Proxy: filter family", np.nan
        if aim_res.get(row["pn"]) == "1":
            return "Not classified", "Catalogue residual", np.nan
        if aim_cat.get(row["pn"]) == "1":
            return "Captive (proxy)", "Proxy: catalogue node", np.nan
        return "Not classified", "No source", np.nan

    cl = priced.apply(classify, axis=1, result_type="expand")
    priced["zone"], priced["zone_basis"], priced["capture_rate"] = cl[0], cl[1], cl[2]

    ks = pd.read_csv(os.path.join(DERIVED, "iam_ks_price_gap.csv"), dtype={"pn": str})
    ks["db"] = ks["db"].astype(str).str.strip().str.upper()
    ks["pn"] = ks["pn"].str.strip()
    ks_db = {(r["db"], r["pn"]): float(r["ks_am_min_eur"]) for _, r in ks.iterrows()}
    ks_pn = ks.groupby("pn")["ks_am_min_eur"].min().to_dict()
    eu = pd.read_csv(os.path.join(DERIVED, "eucon_price_gap.csv"), dtype={"pn": str})
    eu["pn"] = eu["pn"].str.strip()
    eucon_map = {r["pn"]: float(r["Min_Competitor_EUR"]) for _, r in eu.iterrows()}
    t4 = {}
    frames = [pd.read_csv(os.path.join(SNAP, f)) for f in ["auto365_results.csv", "tmc_results.csv", "tranzparts_results.csv"]
              if os.path.exists(os.path.join(SNAP, f))]
    if frames:
        scrub = pd.concat(frames, ignore_index=True).dropna(subset=["PMS_Category"])
        med = scrub.groupby("PMS_Category")["Price_EUR"].median().to_dict()
        t4 = {"brake_pad": med.get("brake"), "brake_shoe": med.get("brake"), "clutch_disc": med.get("clutch"),
              "clutch_kit": med.get("clutch"), "air_filter": med.get("air_filter"),
              "fuel_filter": med.get("fuel_filter"), "oil_filter": med.get("oil_filter")}
        t4 = {k: (None if v is None or not np.isfinite(v) else float(v)) for k, v in t4.items()}

    def benchmark(row):
        pn, db = row["pn"], str(row["distributor_code"] or "").strip().upper()
        v = ks_db.get((db, pn))
        if v and np.isfinite(v) and v > 0:
            return v, "T1"
        v = ks_pn.get(pn)
        if v and np.isfinite(v) and v > 0:
            return v, "T2"
        v = eucon_map.get(pn)
        if v and np.isfinite(v) and v > 0:
            return v, "T3"
        v = t4.get(row["service_category"] or "")
        if v:
            return v, "T4"
        return np.nan, "T5"

    bm = priced.apply(benchmark, axis=1, result_type="expand")
    priced["independent_price_eur"], priced["evidence_tier"] = bm[0], bm[1]
    priced["ref_dealer_price_eur"] = priced["sp_eur_pr00_ie40"] * 1.785
    priced["price_index"] = priced["ref_dealer_price_eur"] / priced["independent_price_eur"]
    return priced
