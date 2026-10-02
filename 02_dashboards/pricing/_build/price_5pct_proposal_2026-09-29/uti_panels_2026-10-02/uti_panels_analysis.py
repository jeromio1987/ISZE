"""UTI (Israel trucks, sold-to 1799) body / panel parts: is lost volume price or availability?

Read-only on every source. Writes CSVs + _numbers.json beside this file.
Run: python uti_panels_analysis.py
Sources:
  billing      01_data/00_derived/sales_fact.parquet (2023-01-03 .. 2026-08-31)
  categories   APPROVED AIM release via 04_tools/_shared/classification_paths.approved_release()
  markets      01_data/00_derived/distributor_dimension.csv
  lists        pricing_pr00_ie40_{2023,2024,2025}.parquet + pricing_pr00_ie40.parquet (via response_lib.load_lists)
  proposal     price_bp_weighted_compare_pn.csv (Jul 25-Jun 26 base) x Proposal sheet 'Proposed move'
               (same method as market_facts.py)
  backorder    01_data/08_Distributor/BO OVERVIEW - UNIVERSAL TRUCKS ISRAEL LTD 01-07-2026 (1).xlsx
  sell-out     dealer_sellout_long_UTI_CY2025.csv / _CY2026YTD.csv (UTI's own part sales)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import openpyxl

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
D = ROOT / "01_data" / "00_derived"
HERE = Path(__file__).parent
PROP_DIR = HERE.parent
sys.path.insert(0, str(ROOT / "04_tools" / "_shared"))
sys.path.insert(0, str(PROP_DIR))
import classification_paths as cp  # noqa: E402
from response_lib import load_lists  # noqa: E402

z = lambda s: s.astype(str).str.replace(r"\.0$", "", regex=True).str.strip().str.zfill(10)
N = {}

# ------------------------------------------------------------------ categories (approved release)
rel_path, rel = cp.approved_release()
N["release"] = {"id": rel["release_id"], "status": rel["status"], "file": str(rel_path)}
R = pd.read_csv(rel_path, dtype=str, usecols=["part_number", "aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"])
R["pn"] = z(R.part_number)
R = R.drop_duplicates("pn").set_index("pn")


def group(pn):
    l1 = R.aim_l1_fixed.reindex(pn).fillna("Unclassified").values
    l2 = R.aim_l2_fixed.reindex(pn).fillna("").values
    l3 = R.aim_l3_fixed.reindex(pn).fillna("").values
    g = np.where(l1 == "Lighting", "Lighting",
        np.where(l1 != "Accident & Body", "Not body",
        np.where(l2 == "Panels", "Panels", "Other body (" + pd.Series(l2).replace("", "blank").values + ")")))
    return l1, l2, l3, g


# ------------------------------------------------------------------ billing
dd = pd.read_csv(D / "distributor_dimension.csv", dtype=str)
code_of = dict(zip(dd.sold_to_sap, dd.distributor_code))
sf = pd.read_parquet(D / "sales_fact.parquet",
                     columns=["billing_date", "sold_to_sap", "part_number", "description", "billed_qty",
                              "net_sales_value", "saty"])
sf["db"] = sf.sold_to_sap.astype("Int64").astype(str).map(code_of)
sf["pn"] = z(sf.part_number)
sf = sf[sf.db.notna() & ~sf.db.isin(["GERMANY_SERVICE", "MIDI"]) & (sf.billed_qty > 0) & (sf.net_sales_value > 0)]
lub = sf.pn.str.startswith("05") & sf.description.fillna("").str.upper().str.contains("RIM|TELLUS|SHELL|HELIX|SPIRAX")
sf = sf[~lub & sf.pn.str.fullmatch(r"\d{10}")].copy()
sf["l1"], sf["l2"], sf["l3"], sf["grp"] = group(sf.pn)
sf["y"] = sf.billing_date.dt.year
sf["q"] = sf.billing_date.dt.to_period("Q").astype(str)
sf["m"] = sf.billing_date.dt.month
N["billing_range"] = [str(sf.billing_date.min().date()), str(sf.billing_date.max().date())]


def periods(df):
    """year 2023/2024/2025 + Jan-Aug of each year (2026 billing ends 31 Aug)."""
    out = []
    for y in (2023, 2024, 2025):
        out.append(df[df.y == y].assign(period=str(y)))
    for y in (2023, 2024, 2025, 2026):
        out.append(df[(df.y == y) & (df.m <= 8)].assign(period=f"Jan-Aug {y}"))
    return pd.concat(out)


u = sf[sf.db == "UTI"].copy()
up = periods(u)

# T1 UTI by period x group
t1 = up.groupby(["period", "grp"]).agg(eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"),
                                         lines=("pn", "size"), parts=("pn", "nunique")).reset_index()
t1.to_csv(HERE / "t1_uti_by_period_group.csv", index=False)

# T1b UTI Panels by L3
t1b = up[up.grp == "Panels"].groupby(["period", "l3"]).agg(eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"),
                                                           lines=("pn", "size"), parts=("pn", "nunique")).reset_index()
t1b.to_csv(HERE / "t1b_uti_panels_by_l3.csv", index=False)

# T2 UTI by quarter
t2 = u.groupby(["q", "grp"]).agg(eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"),
                                 lines=("pn", "size")).reset_index()
t2.to_csv(HERE / "t2_uti_by_quarter_group.csv", index=False)

# T3 all markets: Panels + total, Jan-Aug 2025 vs 2026, and 2023 vs 2025
ap = periods(sf)
piv = ap.assign(is_pan=ap.grp.eq("Panels")).groupby(["db", "period", "is_pan"]).net_sales_value.sum().unstack(["period", "is_pan"])
rows = []
for db in piv.index:
    g = lambda p, pan: float(piv.loc[db].get((p, pan), 0) or 0)
    tot = lambda p: g(p, True) + g(p, False)
    rows.append({"market": db,
                 "panels_2023": g("2023", True), "panels_2025": g("2025", True),
                 "panels_janaug_2025": g("Jan-Aug 2025", True), "panels_janaug_2026": g("Jan-Aug 2026", True),
                 "total_2023": tot("2023"), "total_2025": tot("2025"),
                 "total_janaug_2025": tot("Jan-Aug 2025"), "total_janaug_2026": tot("Jan-Aug 2026"),
                 "nonpanel_janaug_2025": g("Jan-Aug 2025", False), "nonpanel_janaug_2026": g("Jan-Aug 2026", False)})
t3 = pd.DataFrame(rows)
for a, b, c in (("panels_janaug_2025", "panels_janaug_2026", "panels_yoy"),
                ("nonpanel_janaug_2025", "nonpanel_janaug_2026", "nonpanel_yoy"),
                ("panels_2023", "panels_2025", "panels_23_25"), ("total_2023", "total_2025", "total_23_25")):
    t3[c] = np.where(t3[a] > 0, t3[b] / t3[a] - 1, np.nan)
t3 = t3.sort_values("panels_janaug_2025", ascending=False)
t3.to_csv(HERE / "t3_markets_panels_vs_rest.csv", index=False)

# T4 order type mix (SaTy) by half-year, UTI panels vs UTI non-body
u["h"] = u.y.astype(str) + np.where(u.m <= 6, "-H1", "-H2")
u["seg"] = np.where(u.grp == "Panels", "Panels", np.where(u.grp == "Lighting", "Lighting",
                    np.where(u.grp.str.startswith("Other body"), "Other body", "Not body")))
t4 = u.groupby(["seg", "h", "saty"]).agg(eur=("net_sales_value", "sum"), lines=("pn", "size")).reset_index()
tot4 = t4.groupby(["seg", "h"])[["eur", "lines"]].transform("sum")
t4["eur_share"], t4["line_share"] = t4.eur / tot4.eur, t4.lines / tot4.lines
t4.to_csv(HERE / "t4_uti_order_type_by_half.csv", index=False)

# T5 price: list moves on the panels UTI buys + what UTI pays vs list
lists, superseded, origin = load_lists()
pan_pns = u[u.grp == "Panels"].groupby("pn").net_sales_value.sum()
lst = pd.DataFrame({y: lists[y] for y in (2023, 2024, 2025, 2026)})
rows = []
for a, b, lab in ((2023, 2024, "Jan 2024 change"), (2024, 2025, "Jan 2025 change"), (2025, 2026, "2026 list (valid 13 Mar 2026)")):
    for seg, pns in (("UTI panels", pan_pns), ("UTI all parts", u.groupby("pn").net_sales_value.sum())):
        j = lst.loc[lst.index.intersection(pns.index), [a, b]].dropna()
        j = j[(j[a] > 0) & (j[b] > 0)]
        ch = j[b] / j[a] - 1
        w = pns.reindex(j.index)
        rows.append({"event": lab, "segment": seg, "parts": len(j), "median_change": float(ch.median()),
                     "billed_weighted_change": float((ch * w).sum() / w.sum())})
t5 = pd.DataFrame(rows)
t5.to_csv(HERE / "t5_list_moves_uti_panels.csv", index=False)

# T5b paid vs list (list of the same year; 2026 uses current list)
rows = []
for y in (2023, 2024, 2025, 2026):
    x = u[(u.y == y)].copy()
    x["list"] = x.pn.map(lists[y])
    x = x[x.list > 0]
    for seg in ("Panels", "Not body", "Lighting"):
        s = x[x.seg == seg]
        for st in ("SOR", "ALL"):
            ss = s if st == "ALL" else s[s.saty == st]
            if len(ss):
                rows.append({"year": y, "segment": seg, "order_type": st, "lines": len(ss),
                             "paid_pct_of_list": float(ss.net_sales_value.sum() / (ss.list * ss.billed_qty).sum() * 100)})
t5b = pd.DataFrame(rows)
t5b.to_csv(HERE / "t5b_uti_paid_vs_list.csv", index=False)

# T5c volume response around the 2026 list (same calendar months before/after, units per panel part)
pre = u[(u.billing_date >= "2025-04-01") & (u.billing_date <= "2025-08-31") & (u.grp == "Panels")].groupby("pn").billed_qty.sum()
post = u[(u.billing_date >= "2026-04-01") & (u.billing_date <= "2026-08-31") & (u.grp == "Panels")].groupby("pn").billed_qty.sum()
j = pd.DataFrame({"pre": pre, "post": post}).fillna(0)
j["list_change"] = (lists[2026] / lists[2025] - 1).reindex(j.index)
j = j.dropna()
j["band"] = pd.cut(j.list_change, [-1, 0.0001, 0.05, 0.10, 10], labels=["<=0%", "0-5%", "5-10%", ">10%"])
t5c = j.groupby("band", observed=False).agg(parts=("pre", "size"), units_pre=("pre", "sum"), units_post=("post", "sum")).reset_index()
t5c["units_change"] = t5c.units_post / t5c.units_pre - 1
t5c.to_csv(HERE / "t5c_uti_panels_units_by_list_move.csv", index=False)
N["t5c_rank_corr_listchange_vs_unitgrowth"] = float(
    j[(j.pre + j.post) >= 3].assign(g=lambda d: np.log((d.post + 0.5) / (d.pre + 0.5)))[["list_change", "g"]]
    .corr(method="spearman").iloc[0, 1])
N["t5c_parts_used"] = int(((j.pre + j.post) >= 3).sum())

# T6 backorder overview 1 Jul 2026
bo_path = ROOT / "01_data" / "08_Distributor" / "BO OVERVIEW - UNIVERSAL TRUCKS ISRAEL LTD 01-07-2026 (1).xlsx"
ws = openpyxl.load_workbook(bo_path, data_only=True, read_only=True)["DATA"]
vals = list(ws.iter_rows(values_only=True))
hdr = list(vals[3])
bo = pd.DataFrame([r for r in vals[4:] if r[4]], columns=["sold_to", "customer", "doc", "ref", "material", "desc",
                                                          "saty", "req_date", "open_qty", "transit_qty", "eta",
                                                          "priority", "next_eta_supplier", "tentative_eta_isze", "confirmed_qty"])
bo["pn"] = z(bo.material)
bo["l1"], bo["l2"], bo["l3"], bo["grp"] = group(bo.pn)
bo["req_date"] = pd.to_datetime(bo.req_date, errors="coerce")
bo["days_open_at_1jul"] = (pd.Timestamp("2026-07-01") - bo.req_date).dt.days
lp = lists[2026]
bo["list_eur"] = bo.pn.map(lp)
bo["open_value_at_list"] = bo.open_qty.astype(float) * bo.list_eur
bo["seg"] = np.where(bo.grp == "Panels", "Panels", np.where(bo.grp == "Lighting", "Lighting",
                     np.where(bo.grp.str.startswith("Other body"), "Other body", "Not body")))
bo.drop(columns=["customer"]).to_csv(HERE / "t6_uti_backorder_lines_2026-07-01.csv", index=False)
t6 = bo.groupby("seg").agg(lines=("pn", "size"), parts=("pn", "nunique"), units=("open_qty", "sum"),
                           value_at_list=("open_value_at_list", "sum"),
                           median_days_open=("days_open_at_1jul", "median"),
                           max_days_open=("days_open_at_1jul", "max"),
                           vor_rush_lines=("saty", lambda s: int(s.isin(["VOR", "RUSH"]).sum()))).reset_index()
t6.to_csv(HERE / "t6b_uti_backorder_summary.csv", index=False)
N["backorder_header"] = [str(h) for h in hdr]
N["backorder_lines"] = int(len(bo))

# T7 UTI sell-out (their own part sales), panels share of units
so = []
for f in ("dealer_sellout_long_UTI_CY2025.csv", "dealer_sellout_long_UTI_CY2026YTD.csv"):
    x = pd.read_csv(D / f, dtype=str)
    so.append(x)
so = pd.concat(so)
so = so[~so.source_file.eq("UTIPartSales_2026-07.xlsx")]          # byte-for-byte duplicate of the June file
so = so[~((so.period == "2025-12") & so.source_file.str.contains("YTD"))]  # same YTD file re-labelled as Dec
so["qty"] = pd.to_numeric(so.qty, errors="coerce")
so["pn"] = z(so.part_number)
so["l1"], so["l2"], so["l3"], so["grp"] = group(so.pn)
so["seg"] = np.where(so.grp == "Panels", "Panels", np.where(so.grp == "Lighting", "Lighting",
                     np.where(so.grp.str.startswith("Other body"), "Other body", "Not body")))
so["bucket"] = np.where(so.period == "2025", "CY2025 (YTD file)", np.where(so.period.str.startswith("2026"), "2026 Jan-Jun files", "2025 monthly files"))
t7 = so.groupby(["bucket", "seg"]).agg(units=("qty", "sum"), parts=("pn", "nunique")).reset_index()
t7["unit_share"] = t7.units / t7.groupby("bucket").units.transform("sum")
t7.to_csv(HERE / "t7_uti_sellout_units_by_segment.csv", index=False)
t7m = so[so.period != "2025"].groupby(["period", "seg"]).qty.sum().unstack(fill_value=0)
t7m.to_csv(HERE / "t7b_uti_sellout_units_by_month.csv")
# purchases from ISZE in the same buckets (units)
pur = {"CY2025": u[u.y == 2025], "2026 Jan-Jun": u[(u.y == 2026) & (u.m <= 6)]}
N["purchase_units"] = {k: v.groupby("seg").billed_qty.sum().to_dict() for k, v in pur.items()}

# T8 EUR at stake in the proposal (market_facts method)
aim_master = pd.read_csv(D / "aim_master_v2.csv", dtype=str, usecols=["part_number", "aim_l1"])
aim_master["pn"] = z(aim_master.part_number)
am = aim_master.drop_duplicates("pn").set_index("pn").aim_l1
base = pd.read_csv(D / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str, "customer_code": str})
base = base[(base.in_scope == True) & base.bp_new_jpy.notna() & base.bp_prior_revised.notna()].copy()  # noqa: E712
base["db"] = base.customer_code.astype(str).str.replace(r"\.0$", "", regex=True).map(code_of)
base["pn"] = z(base.part_number)
prop = pd.read_excel(ROOT / "01_data" / "01_Pricing" / "Price_Increase_5pct_Proposal_2026-09-29.xlsx",
                     sheet_name="Proposal", dtype={"Part number": str})
prop["pn"] = z(prop["Part number"])
pm = prop.drop_duplicates("pn").set_index("pn")
base["d"] = base.pn.map(pm["Proposed move"])
base["c"] = base.pn.map(pm["Factory move"])
b = base[base.db == "UTI"].copy()
b["step"] = b.net_sales_value * b.d
b["master_body"] = b.pn.map(am).eq("Accident & Body")
b["l1"], b["l2"], b["l3"], b["grp"] = group(b.pn)
N["uti_body_step_master_method"] = float(b.loc[b.master_body, "step"].sum())
N["uti_body_billed_master_method"] = float(b.loc[b.master_body, "net_sales_value"].sum())
t8 = b.groupby(["grp", "l3"]).agg(billed_jul25_jun26=("net_sales_value", "sum"), step_eur=("step", "sum"),
                                  parts=("pn", "nunique")).reset_index()
t8["avg_move"] = t8.step_eur / t8.billed_jul25_jun26
t8.to_csv(HERE / "t8_uti_proposal_step_by_category.csv", index=False)
t8b = b.groupby(["master_body", "grp"]).agg(billed=("net_sales_value", "sum"), step=("step", "sum")).reset_index()
t8b.to_csv(HERE / "t8b_uti_step_master_vs_release.csv", index=False)

# T9 backorder: body parts by description that the release does not file under body (never billed / unclassified)
body_words = r"PANEL|BUMPER|LID;|DOOR|GRILLE|FENDER|HOOD|ROOF|COWL|STEP|MEMBER; CAB"
bo["body_by_description_only"] = bo.seg.eq("Not body") & bo.desc.str.upper().str.contains(body_words, regex=True)
bo[bo.seg.ne("Not body") | bo.body_by_description_only].drop(columns=["customer"]).to_csv(
    HERE / "t6c_uti_backorder_body_lines.csv", index=False)
N["backorder_body_by_description_only"] = bo[bo.body_by_description_only][["pn", "desc", "saty", "days_open_at_1jul"]] \
    .astype(str).values.tolist()
N["backorder_saty_counts"] = bo.saty.value_counts().to_dict()

# T10 same-part unit price paid, panels, Jan-Aug 2025 vs Jan-Aug 2026 (parts bought in both windows)
def asp(df):
    g = df.groupby("pn")[["net_sales_value", "billed_qty"]].sum()
    return g.net_sales_value / g.billed_qty, g.net_sales_value
a25 = u[(u.y == 2025) & (u.m <= 8) & (u.grp == "Panels")]
a26 = u[(u.y == 2026) & (u.m <= 8) & (u.grp == "Panels")]
p25, v25 = asp(a25)
p26, v26 = asp(a26)
j = pd.DataFrame({"p25": p25, "p26": p26, "v25": v25}).dropna()
r = j.p26 / j.p25
N["panels_same_part_price_change_janaug_25_26"] = {
    "parts_both_windows": int(len(j)), "median": float(r.median()) - 1,
    "eur25_weighted": float((r * j.v25).sum() / j.v25.sum()) - 1,
    "list_change_same_parts_median": float((lists[2026] / lists[2025]).reindex(j.index).median()) - 1}
# EUR bridge Jan-Aug 2025 -> 2026 for panels: parts in both / only 2025 / only 2026
both = j.index
N["panels_eur_bridge_janaug"] = {
    "eur_2025": float(a25.net_sales_value.sum()), "eur_2026": float(a26.net_sales_value.sum()),
    "parts_2025": int(a25.pn.nunique()), "parts_2026": int(a26.pn.nunique()), "parts_both": int(len(both)),
    "eur_2025_parts_not_bought_2026": float(a25[~a25.pn.isin(both)].net_sales_value.sum()),
    "eur_2026_parts_not_bought_2025": float(a26[~a26.pn.isin(both)].net_sales_value.sum()),
    "eur_both_2025": float(a25[a25.pn.isin(both)].net_sales_value.sum()),
    "eur_both_2026": float(a26[a26.pn.isin(both)].net_sales_value.sum()),
    "units_both_2025": float(a25[a25.pn.isin(both)].billed_qty.sum()),
    "units_both_2026": float(a26[a26.pn.isin(both)].billed_qty.sum())}
top = pd.concat([a25.assign(w="JanAug2025"), a26.assign(w="JanAug2026")]).groupby(["pn", "w"]).agg(
    eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"), desc=("description", "first")).unstack("w")
top.columns = [f"{a}_{b}" for a, b in top.columns]
top["l3"] = R.aim_l3_fixed.reindex(top.index)
top["eur_change"] = top.get("eur_JanAug2026", 0).fillna(0) - top.get("eur_JanAug2025", 0).fillna(0)
top.sort_values("eur_change").to_csv(HERE / "t10_uti_panels_by_part_janaug.csv")

(HERE / "_numbers.json").write_text(json.dumps(N, indent=1, default=str), encoding="utf-8")
pd.set_option("display.width", 250, "display.max_columns", 30, "display.max_rows", 300)
for nm, t in (("t1", t1), ("t1b", t1b), ("t3", t3), ("t5", t5), ("t5b", t5b), ("t5c", t5c), ("t6", t6),
              ("t7", t7), ("t8", t8), ("t8b", t8b)):
    print("=====", nm); print(t.to_string())
print(json.dumps(N, indent=1, default=str))
