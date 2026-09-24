"""Billing (ISZE -> I Motors) against sales to dealer (I Motors -> dealers), on the same periods and the same basis.

Used by build_merged_deck.py for the PMS cover slide and the Genuine / BVP slide.

  ISZE billing     : 01_data/00_derived/sales_fact.parquet, sold-to 519 + 92, credit notes / returns (CR, RE) excluded
  sales to dealer  : 01_data/00_derived/dealer_sellout_long_PORTUGAL_CY2025.csv + _CY2026YTD.csv, MONTH rows only
                     (the files also carry a year-total row; summing both would double the units)
  PMS family       : 01_data/00_derived/parts_catalog_dimension.csv (pms_category), same mapping for both stages
  PMS demand       : ISZE PMS model on the FY2026 fleet (scrap-rate model, I Motors registrations), see
                     ../../charcoal_first7/_build/pms_fy.py. FY2027 Apr-Aug = 5/12 of the FY2026 yearly demand
                     (the registration file ends June 2026).
  Genuine / BVP    : 01_data/00_derived/bvp_pn_dimension.csv (line_type genuine | bvp, product_family)
  price basis      : 01_data/00_derived/pricing_pr00_ie40.parquet = 01_data/01_Pricing/Price_file_PR00_IE40_20260810.xlsx
                     (IE40 PR00 list, newest file, 10 Aug 2026). Both stages are valued at this list, so the euro
                     figures compare like for like. It is the ISZE list price, not I Motors' net price or dealer price.
"""
import os, sys, pathlib, importlib.util
import pandas as pd

R = pathlib.Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = R / "01_data" / "00_derived"
HERE = pathlib.Path(__file__).resolve().parent

FAMS = ["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter",
        "brake_pad", "brake_shoe", "brake_rotor",
        "clutch_kit", "clutch_disc", "clutch_pressure_plate", "release_bearing", "pilot_bearing", "clutch_booster"]
CLUTCH = {"clutch_kit", "clutch_disc", "clutch_pressure_plate", "release_bearing", "pilot_bearing", "clutch_booster"}
LAB = {"oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter", "blower_filter": "Cabin (blower) filter",
       "urea_filter": "AdBlue (urea) filter", "brake_pad": "Brake pad", "brake_shoe": "Brake shoe", "brake_rotor": "Brake rotor",
       "clutch_kit": "Clutch kit *", "clutch_disc": "Clutch disc *", "clutch_pressure_plate": "Clutch pressure plate *",
       "release_bearing": "Release bearing *", "pilot_bearing": "Pilot bearing *", "clutch_booster": "Clutch booster *"}
PERIODS = {"FY2026": ("2025-04-01", "2026-03-31", 12), "FY2027 Apr-Aug": ("2026-04-01", "2026-08-31", 5)}


def norm(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.lstrip("0").replace("", "0")


def fam_of(c):
    c = str(c)
    if c.startswith("brake_pad"): return "brake_pad"
    if c.startswith("brake_shoe") or c.startswith("brake_lining"): return "brake_shoe"
    return c if c in FAMS else None


def billing():
    sf = pd.read_parquet(DER / "sales_fact.parquet", columns=["billing_date", "sold_to_sap", "part_number", "billed_qty", "net_sales_value", "saty"])
    b = sf[sf.sold_to_sap.isin([519, 92]) & ~sf.saty.isin(["CR", "RE"])].copy()
    b["pn"] = norm(b.part_number); b["date"] = b.billing_date; b["qty"] = b.billed_qty
    return b[["date", "pn", "qty", "net_sales_value"]]


def sellout():
    so = pd.concat([pd.read_csv(DER / f"dealer_sellout_long_PORTUGAL_{p}.csv", dtype={"part_number": str, "period": str})
                    for p in ("CY2025", "CY2026YTD")])
    so = so[so.period_grain == "month"].copy()
    so["date"] = pd.to_datetime(so.period + "-01"); so["pn"] = norm(so.part_number)
    so["qty"] = pd.to_numeric(so.qty, errors="coerce").fillna(0)
    return so[["date", "pn", "qty"]]


def price_list():
    p = pd.read_parquet(DER / "pricing_pr00_ie40.parquet", columns=["part_number", "newest_pn", "sp_eur"])
    p["pn"] = norm(p.part_number); p["new"] = norm(p.newest_pn)
    p = p[p.sp_eur > 0]
    own = p.drop_duplicates("pn").set_index("pn").sp_eur
    newest = p.set_index("pn").sp_eur.reindex(p.new.values)          # price of the newest number, for superseded numbers
    newest.index = p.pn.values
    return own.combine_first(newest[~newest.index.duplicated()].dropna())


def pms_demand_fy2026():
    spec = importlib.util.spec_from_file_location("pms_fy", str(HERE.parent.parent / "charcoal_first7" / "_build" / "pms_fy.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    prism = m.PRISM
    sys.path.insert(0, str(prism)); cwd = os.getcwd(); os.chdir(prism)
    try:
        import modules.pms_capture_config as cc
        from modules.pms_engine import parc_config_for_distributor, expected_by_category_bucketed
        cfg = parc_config_for_distributor("PORTUGAL"); saved = cc.UIO_BY_BUCKET.get("PORTUGAL")
        f = m._fleet(m._regs(), 2026, "scrap")
        cc.UIO_BY_BUCKET["PORTUGAL"] = {"cv_std": f["LD"], "f_series": f["F"], "lcv": f["LCV"]}
        e = expected_by_category_bucketed("PORTUGAL", cfg)
        cc.UIO_BY_BUCKET["PORTUGAL"] = saved
    finally:
        os.chdir(cwd)
    return {c: e[c]["qty"] for c in FAMS}, sum(f.values())


def in_period(df, per):
    a, b, _ = PERIODS[per]
    return df[(df.date >= a) & (df.date <= b)]


def pms_compare():
    cat = pd.read_csv(DER / "parts_catalog_dimension.csv", dtype=str, usecols=["part_number", "pms_category"])
    cat["pn"] = norm(cat.part_number); cat = cat.drop_duplicates("pn"); cat["fam"] = cat.pms_category.map(fam_of)
    cat = cat[cat.fam.notna()][["pn", "fam"]]
    demand, fleet = pms_demand_fy2026()
    rows = []
    for stage, df in (("billed", billing()), ("sold", sellout())):
        d = df.merge(cat, on="pn")
        for per in PERIODS:
            u = in_period(d, per).groupby("fam").qty.sum()
            for c in FAMS:
                rows.append(dict(fam=c, period=per, stage=stage, units=float(u.get(c, 0.0))))
    t = pd.DataFrame(rows).pivot_table(index=["fam", "period"], columns="stage", values="units").reset_index()
    t["demand"] = [demand[f] * PERIODS[p][2] / 12 for f, p in zip(t.fam, t.period)]
    t["cov_billed"] = t.billed / t.demand; t["cov_sold"] = t.sold / t.demand
    return t, fleet


def bvp_compare():
    dim = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str)
    dim["pn"] = norm(dim.part_number); dim = dim.drop_duplicates("pn")
    grp = {"PMS_Filters": "Filters", "Brakes": "Brakes", "Clutch_Driveline": "Clutch"}
    dim["grp"] = dim.product_family.map(grp); dim = dim[dim.grp.notna()][["pn", "grp", "line_type"]]
    price = price_list()
    per = {"2023": ("2023-01-01", "2023-12-31"), "2024": ("2024-01-01", "2024-12-31"), "2025": ("2025-01-01", "2025-12-31"),
           "2026 Jan-Aug": ("2026-01-01", "2026-08-31")}
    out, cover = [], {}
    for stage, df in (("billed", billing()), ("sold", sellout())):
        d = df.merge(dim, on="pn")
        d["list_eur"] = d.qty * d.pn.map(price)
        for p, (a, b) in per.items():
            x = d[(d.date >= a) & (d.date <= b)]
            if x.empty: continue
            cover[(stage, p)] = x[x.list_eur.notna()].qty.sum() / x.qty.sum()
            g = x.groupby(["grp", "line_type"]).agg(units=("qty", "sum"), list_eur=("list_eur", "sum")).reset_index()
            g["stage"], g["period"] = stage, p
            out.append(g)
    return pd.concat(out, ignore_index=True), cover


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    t, fl = pms_compare()
    print("FY2026 fleet (scrap-rate model):", round(fl))
    print(t.round(3).to_string())
    b, cov = bvp_compare()
    print(b.round(0).to_string())
    print({k: round(v, 3) for k, v in cov.items()})
