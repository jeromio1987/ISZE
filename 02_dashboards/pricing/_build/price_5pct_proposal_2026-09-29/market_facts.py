"""Per-market fact base for the market-by-market pricing exercise (read-only on all sources).

Run: python market_facts.py  ->  market_facts_2026-09-30.json
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
D = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
PROPOSAL = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\01_Pricing\Price_Increase_5pct_Proposal_2026-09-29.xlsx")
CARPARK = Path(r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\Data\00_derived\UIO_carpark_for_GPS_recalc_2026-07-30.csv")
OUT = HERE / "market_facts_2026-09-30.json"
z = lambda s: s.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(10)

dd = pd.read_csv(D / "distributor_dimension.csv", dtype=str)
code_of = dict(zip(dd.sold_to_sap, dd.distributor_code))

# ------------------------------------------------------------------ billing
sf = pd.read_parquet(D / "sales_fact.parquet", columns=["billing_date", "sold_to_sap", "part_number", "description",
                                                        "billed_qty", "net_sales_value", "saty"])
sf["db"] = sf.sold_to_sap.astype("Int64").astype(str).map(code_of)
sf["pn"] = z(sf.part_number)
sf["y"], sf["m"] = sf.billing_date.dt.year, sf.billing_date.dt.month
sf = sf[sf.db.notna() & ~sf.db.isin(["GERMANY_SERVICE", "MIDI"]) & (sf.billed_qty > 0) & (sf.net_sales_value > 0)]
lub = sf.pn.str.startswith("05") & sf.description.fillna("").str.upper().str.contains("RIM|TELLUS|SHELL|HELIX|SPIRAX")
sf = sf[~lub & sf.pn.str.fullmatch(r"\d{10}")]

aim = pd.read_csv(D / "aim_master_v2.csv", dtype=str, usecols=["part_number", "aim_l1", "cat_pms_flag"])
aim["pn"] = z(aim.part_number)
aim = aim.drop_duplicates("pn").set_index("pn")
bvp = pd.read_csv(D / "genuine_bvp_crossref.csv", dtype=str)
bvp_pns = set(z(bvp.bvp_pn.dropna()))
pms = set(z(bvp.dropna(subset=["pms_category"]).genuine_pn)) | set(z(bvp.dropna(subset=["pms_category"]).bvp_pn)) \
    | set(aim.index[aim.cat_pms_flag == "1"])
sf["family"] = sf.pn.map(aim.aim_l1).fillna("Unclassified")
sf["seg"] = np.select([sf.family.eq("Accident & Body"), sf.pn.isin(pms)], ["body", "service"], default="repair")
sf["bvp"] = sf.pn.isin(bvp_pns)

lst25 = pd.read_parquet(D / "pricing_pr00_ie40_2025.parquet")
lst25["pn"] = z(lst25.Material.astype("Int64"))
lst25 = lst25[lst25.Price_EUR > 0].groupby("pn").Price_EUR.max()

buyers = sf[sf.y.between(2023, 2025)].groupby("pn").db.agg(lambda s: frozenset(s))
sf["only_here"] = sf.pn.map(buyers.map(len)).eq(1)

# ------------------------------------------------------------------ fleet
g = pd.read_csv(D / "gps_spu_by_distributor.csv")
fleet = g.pivot_table(index="distributor_code", columns="year", values="uio_units")
cp = pd.read_csv(CARPARK)
cp_code = {"UTI": "UTI", "UMI": "UMI", "ITUK": "ITUK", "IUK": "IUK"}
cp["code"] = cp.distributor_DB.map(cp_code).fillna(cp.country.str.upper().replace({"PORTUGL": "PORTUGAL"}))
f26 = cp.groupby("code").uio_CY2026_corrected.sum()
f25c = cp.groupby("code").uio_CY2025_unchanged.sum()
fstatus = cp[cp.uio_CY2025_unchanged > 0].groupby("code").status.agg(lambda s: ", ".join(sorted(set(s))))

# ------------------------------------------------------------------ service share (capture)
cap = pd.read_csv(D / "pms_capture_by_db_year.csv")
cap = cap[cap.expected_qty > 0]

# ------------------------------------------------------------------ proposal effect
base = pd.read_csv(D / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str})
base = base[(base.in_scope == True) & base.bp_new_jpy.notna() & base.bp_prior_revised.notna()].copy()  # noqa: E712
base["db"] = base.customer_code.astype(str).map(code_of)
base["pn"] = z(base.part_number)
prop = pd.read_excel(PROPOSAL, sheet_name="Proposal", dtype={"Part number": str})
prop["pn"] = z(prop["Part number"])
pmap = prop.set_index("pn")
base["d"] = base.pn.map(pmap["Proposed move"])
base["c"] = base.pn.map(pmap["Factory move"])
base["seg"] = np.select([base.pn.map(aim.aim_l1).eq("Accident & Body"), base.pn.isin(pms)], ["body", "service"], default="repair")
TOT_STEP = float((base.net_sales_value * base.d).sum())
TOT_BASE = float(base.net_sales_value.sum())

resp = json.loads((HERE / "dealer_price_response_2026-09-29.json").read_text(encoding="utf-8"))
resp_map = {"ITUK": "ITUK (UK trucks)", "IUK": "IUK (UK D-Max)", "IRELAND": "Ireland", "PORTUGAL": "Portugal"}

# network reference values
cap25 = cap[(cap.year == 2025) & (cap.line_type == "total")]
net_share25 = float(cap25.actual_qty.sum() / cap25.expected_qty.sum())


def rnd(x, n=4):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


markets = {}
for db, d in sf.groupby("db"):
    b = d[d.y.between(2023, 2025)].groupby("y").net_sales_value.sum()
    if b.get(2025, 0) < 60000:
        continue
    r = {"code": db}
    r["billed"] = {str(int(k)): rnd(v, 0) for k, v in b.items()}
    ja = d[d.m <= 8].groupby("y").net_sales_value.sum()
    r["jan_aug_2025"], r["jan_aug_2026"] = rnd(ja.get(2025), 0), rnd(ja.get(2026), 0)
    seg = d[d.y.isin([2023, 2025])].pivot_table(index="seg", columns="y", values="net_sales_value", aggfunc="sum").fillna(0)
    r["segments"] = {s: {"2023": rnd(seg.loc[s].get(2023, 0), 0), "2025": rnd(seg.loc[s].get(2025, 0), 0)} for s in seg.index}
    fam = d[d.y.isin([2023, 2025])].pivot_table(index="family", columns="y", values="net_sales_value", aggfunc="sum").fillna(0)
    if 2023 in fam and 2025 in fam:
        fam["delta"] = fam[2025] - fam[2023]
        r["family_up"] = [[k, rnd(v, 0)] for k, v in fam.delta.sort_values(ascending=False).head(4).items() if v > 0]
        r["family_down"] = [[k, rnd(v, 0)] for k, v in fam.delta.sort_values().head(4).items() if v < 0]
    a = d[d.y.isin([2023, 2025])].groupby(["pn", "y"]).agg(q=("billed_qty", "sum"), v=("net_sales_value", "sum")).unstack().dropna()
    a = a[(a[("q", 2023)] > 0) & (a[("q", 2025)] > 0)]
    if len(a):
        p23, p25 = a[("v", 2023)] / a[("q", 2023)], a[("v", 2025)] / a[("q", 2025)]
        r["price_effect_23_25"] = rnd(((p25 - p23) * a[("q", 2023)]).sum(), 0)
        r["volume_effect_23_25"] = rnd(((a[("q", 2025)] - a[("q", 2023)]) * p25).sum(), 0)
    y25 = d[d.y == 2025]
    r["pns_2025"] = int(y25.pn.nunique())
    r["bvp_share_2025"] = rnd(y25.net_sales_value[y25.bvp].sum() / y25.net_sales_value.sum())
    r["only_here_share_23_25"] = rnd(d[d.y.between(2023, 2025) & d.only_here].net_sales_value.sum()
                                     / d[d.y.between(2023, 2025)].net_sales_value.sum())
    r["only_here_pns"] = int(d[d.y.between(2023, 2025) & d.only_here].pn.nunique())
    top_only = (d[d.y.between(2023, 2025) & d.only_here].groupby("pn")
                .agg(desc=("description", "first"), eur=("net_sales_value", "sum")).sort_values("eur", ascending=False).head(6))
    r["only_here_examples"] = [str(x)[:28] for x in top_only.desc]
    lv = y25.pn.map(lst25) * y25.billed_qty
    t = y25[lv > 0].assign(lv=lv[lv > 0]).groupby("saty").agg(b=("net_sales_value", "sum"), l=("lv", "sum"))
    r["pays_pct_list"] = {k: rnd(v.b / v.l * 100, 1) for k, v in t.iterrows() if k in ("SOR", "RUSH", "VOR")}
    r["pays_pct_list_all"] = rnd(t.b.sum() / t.l.sum() * 100, 1)
    r["urgent_share"] = rnd(y25.net_sales_value[y25.saty.isin(["VOR", "RUSH"])].sum() / y25.net_sales_value.sum())
    r["avg_line_eur"] = rnd(y25.net_sales_value.sum() / len(y25), 0)
    # fleet
    r["fleet"] = {str(y): rnd(fleet.loc[db, y], 0) for y in (2023, 2024, 2025) if db in fleet.index and y in fleet}
    r["fleet_2026_corrected"] = rnd(f26.get(db), 0)
    r["fleet_status"] = fstatus.get(db)
    # service share
    c = cap[cap.distributor_code == db]
    sh = {}
    for y in (2023, 2024, 2025):
        cy = c[(c.year == y) & (c.line_type == "total")]
        cg = c[(c.year == y) & (c.line_type == "genuine")]
        if len(cy) and cy.expected_qty.sum() > 0:
            sh[str(y)] = {"total": rnd(cy.actual_qty.sum() / cy.expected_qty.sum()),
                          "genuine": rnd(cg.actual_qty.sum() / cy.expected_qty.sum())}
    r["service_share"] = sh
    cc = c[c.line_type == "total"].pivot_table(index="category_label", columns="year", values="capture_rate")
    if 2023 in cc and 2025 in cc:
        cc["chg"] = cc[2025] - cc[2023]
        exp25 = c[(c.year == 2025) & (c.line_type == "total")].set_index("category_label").expected_qty
        cc["exp"] = exp25.reindex(cc.index)
        cc = cc[cc.exp > 20].sort_values("exp", ascending=False)
        r["category_share"] = [[k, rnd(v[2025]), rnd(v.chg)] for k, v in cc.iterrows()]
    # proposal
    bb = base[base.db == db]
    pe = {}
    for s_, gg in bb.groupby("seg"):
        pe[s_] = {"billed": rnd(gg.net_sales_value.sum(), 0), "proposed": rnd(np.average(gg.d, weights=gg.net_sales_value)),
                  "factory": rnd(np.average(gg.c, weights=gg.net_sales_value)), "step": rnd((gg.net_sales_value * gg.d).sum(), 0)}
    r["proposal"] = pe
    if db in resp_map:
        v = resp["four_markets_april_2026"]["by_market"][resp_map[db]]
        u = resp["four_markets_april_2026"]["dealer_units"][resp_map[db]]
        r["dealer_response"] = {"beta": v["beta_dlp"], "se": v["se_dlp"], "units_change": u["change"], "window": u["window"]}
    markets[db] = r

out = {"generated": "2026-09-30", "network_service_share_2025": rnd(net_share25), "total_step": TOT_STEP,
       "total_base": TOT_BASE, "markets": markets}
OUT.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
print("markets:", len(markets), sorted(markets))
print("network service share 2025:", round(net_share25, 3))
for k in ["NORWAY", "MALTA", "IUK"]:
    print(k, json.dumps(markets[k], default=float)[:900])
