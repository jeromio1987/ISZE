"""Every number in the AIM deck (charcoal, 11 Oct 2026), computed on one base. Writes aim_numbers.json.

Base: the price revision book, in-scope distributor lines, 1 Jul 2025 - 30 Jun 2026
      01_data/00_derived/price_bp_weighted_compare_pn.csv (in_scope == True).
Old tree: catalog_l1/2/3 (the price-list classification) and AIM labels: approved release 2026-10-07
      01_data/00_derived/_releases/aim_pn_classification_release_2026-10-07.csv.
Fleet: 2025 vehicles in service, 01_data/00_derived/gps_spu_by_distributor.csv.
Competitive price file: 09_meetings/IMotors_FY2027_BPR/_competitive_price_overlap_20261006/pn_competitive_contested_full.csv
What this adds on top of the first build (deck_numbers.py): the split of the base into parts and non-part lines,
the steering unit check, and where the part numbers without a Japan code sit.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
DER = ROOT / "01_data" / "00_derived"
OUT = Path(__file__).with_name("aim_numbers.json")
OVERLAP = ROOT / "09_meetings" / "IMotors_FY2027_BPR" / "_competitive_price_overlap_20261006" / "pn_competitive_contested_full.csv"

book = pd.read_csv(DER / "price_bp_weighted_compare_pn.csv", dtype={"part_number": str}, low_memory=False)
book = book[book.in_scope].copy()
rel = pd.read_csv(DER / "_releases" / "aim_pn_classification_release_2026-10-07.csv", dtype=str, low_memory=False)
rel = rel.drop_duplicates("part_number")
b = book.merge(rel, on="part_number", how="left")
b["eur"] = b.net_sales_value.astype(float)
T = b.eur.sum()


def blank(s):
    s = s.fillna("").str.strip()
    return s.isin(["", "nan"]) | s.str.startswith("Unknown")


res = {"base": {"window": "1 Jul 2025 - 30 Jun 2026", "rows": int(len(b)), "part_numbers": int(b.part_number.nunique()),
                "billed_eur": round(T, 2)}}

# ---- what the base is made of (the book's own reason column)
priced = b.bp_new_jpy.notna() & b.bp_prior_revised.notna() & (b.bp_prior_revised > 0)
reason = b.unpriced_reason.fillna("")
res["composition"] = {
    "priced_both_sides_eur": round(b.eur[priced].sum(), 2), "priced_both_sides_pn": int(b[priced].part_number.nunique()),
    "no_price_one_side_eur": round(b.eur[~priced & (reason == "no_price_on_one_side")].sum(), 2),
    "rebate_transport_eur": round(b.eur[~priced & (reason == "rebate_or_non_part_admin")].sum(), 2),
    "lubricants_eur": round(b.eur[~priced & (reason == "lubricant_no_pr00_in_sap")].sum(), 2)}
c = res["composition"]
c["non_part_eur"] = round(c["rebate_transport_eur"] + c["lubricants_eur"], 2)
c["non_part_pct"] = round(c["non_part_eur"] / T * 100, 2)
c["check_sum"] = round(c["priced_both_sides_eur"] + c["no_price_one_side_eur"] + c["non_part_eur"], 2)
rt = b[~priced & (reason == "rebate_or_non_part_admin")].groupby("billed_description").eur.sum()
res["composition"]["rebate_eur"] = round(float(rt.filter(like="Rebate").sum()), 2)
res["composition"]["transport_eur"] = round(float(rt.filter(like="Transport").sum()), 2)
NONPART_MASK = ~priced & reason.isin(["rebate_or_non_part_admin", "lubricant_no_pr00_in_sap"])

# ---- coverage on AIM
has1 = ~blank(b.aim_l1_fixed)
has3 = ~blank(b.aim_l3_fixed)
res["coverage"] = {
    "eur_with_aim_l1": round(b.eur[has1].sum(), 2), "pct_l1": round(b.eur[has1].sum() / T * 100, 2),
    "pct_l1_parts_only": round(b.eur[has1 & ~NONPART_MASK].sum() / b.eur[~NONPART_MASK].sum() * 100, 2),
    "eur_open": round(b.eur[~has1].sum(), 2), "pn_open": int(b[~has1].part_number.nunique()),
    "eur_open_parts_only": round(b.eur[~has1 & ~NONPART_MASK].sum(), 2),
    "pn_open_parts_only": int(b[~has1 & ~NONPART_MASK].part_number.nunique())}

# ---- old top level vs AIM top level
old = b.groupby(b.catalog_l1.fillna("Not classified")).eur.sum().sort_values(ascending=False)
new = b[has1].groupby("aim_l1_fixed").eur.sum().sort_values(ascending=False)
res["old_l1"] = [{"label": k, "eur": round(v, 2), "pct": round(v / T * 100, 2)} for k, v in old.items()]
res["aim_l1"] = [{"label": k, "eur": round(v, 2), "pct": round(v / T * 100, 2)} for k, v in new.items()]
billed = b[b.eur > 0]
res["levels"] = {
    "old": [int(billed[x].replace("", pd.NA).dropna().nunique()) for x in ["catalog_l1", "catalog_l2", "catalog_l3"]],
    "aim": [int(billed.loc[~blank(billed[x]), x].nunique()) for x in ["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]]}

# ---- what sat inside old "Competitive parts", by AIM part type
oc = b[b.catalog_l1 == "Competitive parts"]
res["old_competitive_top_l3"] = [{"l3": k, "eur": round(v, 2)} for k, v in
                                 oc.groupby("aim_l3_fixed").eur.sum().sort_values(ascending=False).head(8).items()]

# ---- steering units: the part type, its old label, and whether any independent-brand price exists
su = b[b.aim_l3_fixed == "Steering Unit"]
su_pn = su.groupby("part_number").agg(eur=("eur", "sum"), l1=("catalog_l1", "first")).sort_values("eur", ascending=False)
ov = pd.read_csv(OVERLAP, dtype={"pn": str}, low_memory=False)
ov["has_am_price"] = ov.has_am_price.astype(str)
ov_su = ov[ov.aim_l2 == "Steering Gear"]
oc_pn = oc.groupby("part_number").eur.sum()
ov_c = ov[ov.pn.isin(oc_pn.index)]
res["steering"] = {
    "pn": int(su.part_number.nunique()), "eur": round(su.eur.sum(), 2),
    "pn_under_competitive": int((su_pn.l1 == "Competitive parts").sum()),
    "eur_under_competitive": round(su_pn.eur[su_pn.l1 == "Competitive parts"].sum(), 2),
    "top_pn": su_pn.index[0], "top_pn_eur": round(su_pn.eur.iloc[0], 2),
    "top_pn_share_pct": round(su_pn.eur.iloc[0] / su.eur.sum() * 100, 1),
    "price_file_pn": int(ov_su.pn.nunique()), "price_file_pn_with_independent_price": int(ov_su[ov_su.has_am_price == "True"].pn.nunique()),
    "competitive_eur_with_independent_price_pct": round(
        oc_pn[oc_pn.index.isin(ov_c[ov_c.has_am_price == "True"].pn)].sum() / oc_pn.sum() * 100, 1)}

# ---- parts the old rule put in an unrelated family
pats = [
    ("Engine air cleaner elements", r"^FILTER; ?ACL", "Air conditioning"),
    ("King pin kits", r"KING ?PIN", "Hardware > Pin"),
    ("Steering drag links", r"^LINK; ?DRAG", "Linkage (hydraulic / mechanical)"),
    ("Front and rear bumper bars", r"^BAR; ?(?:FRT|RR)? ?BUMPER", "Suspension > Leaf spring"),
    ("Suspension ball joints", r"^JOINT(?: ASM)?; ?BALL", "Linkage (hydraulic / mechanical)"),
]
mis = []
for name, rx, was in pats:
    x = b[b.billed_description.fillna("").str.upper().str.contains(rx, regex=True)]
    top = x.groupby(["aim_l1_fixed", "aim_l2_fixed", "aim_l3_fixed"]).eur.sum().sort_values(ascending=False)
    k = top.index[0]
    mis.append({"name": name, "old": was, "aim": " > ".join(k), "eur": round(x.eur.sum(), 2),
                "pn": int(x.part_number.nunique()), "share_in_top_aim": round(top.iloc[0] / max(x.eur.sum(), 1) * 100, 1)})
res["misfiled"] = mis
res["misfiled_total_eur"] = round(sum(m["eur"] for m in mis), 2)
res["air_cleaner_filter_total_eur"] = round(b[b.aim_l3_fixed == "Air Cleaner Filter"].eur.sum(), 2)

# ---- one path down the three levels
pk = b[b.aim_l3_fixed == "Brake Pad Kit"].groupby(["part_number", "billed_description"]).eur.sum().sort_values(ascending=False)
res["path"] = {"l1": ["Brakes", round(b[b.aim_l1_fixed == "Brakes"].eur.sum(), 2)],
               "l2": ["Pads & Shoes", round(b[b.aim_l2_fixed == "Pads & Shoes"].eur.sum(), 2)],
               "l3": ["Brake Pad Kit", round(b[b.aim_l3_fixed == "Brake Pad Kit"].eur.sum(), 2)],
               "pn": [pk.index[0][0], pk.index[0][1], round(pk.iloc[0], 2)]}

# ---- element versus housing / assembly inside the filter family
fr = b[b.filter_part_role.isin(["element", "assembly"])].groupby("filter_part_role").agg(
    eur=("eur", "sum"), qty=("billed_qty", "sum"), pn=("part_number", "nunique"))
res["filter_roles"] = {k: {"eur": round(r.eur, 2), "qty": float(r.qty), "pn": int(r.pn), "avg": round(r.eur / r.qty, 2)}
                       for k, r in fr.iterrows()}
res["filter_roles_blended_avg"] = round(fr.eur.sum() / fr.qty.sum(), 2)

# ---- factory (IML / IMIT) base-price increase by AIM product group, priced on both sides
pr = b[priced].copy()
pr["new_v"] = pr.billed_qty * pr.bp_new_jpy
pr["old_v"] = pr.billed_qty * pr.bp_prior_revised


def inc(g):
    return pd.Series({"eur": g.eur.sum(), "pct": (g.new_v.sum() / g.old_v.sum() - 1) * 100, "step_eur": g.value_eur_step.sum()})


res["increase_total"] = {"pct": round((pr.new_v.sum() / pr.old_v.sum() - 1) * 100, 2),
                         "step_eur": round(pr.value_eur_step.sum(), 2), "priced_eur": round(pr.eur.sum(), 2)}
l2 = pr[~blank(pr.aim_l2_fixed)].groupby(["aim_l1_fixed", "aim_l2_fixed"]).apply(inc, include_groups=False).reset_index()
l2 = l2[l2.eur >= 500000].sort_values("pct")
res["increase_l2"] = [{"l1": r.aim_l1_fixed, "l2": r.aim_l2_fixed, "eur": round(r.eur, 2), "pct": round(r.pct, 2),
                       "step_eur": round(r.step_eur, 2)} for r in l2.itertuples()]

# ---- Norway against Sweden, euro per vehicle in service
uio = pd.read_csv(DER / "gps_spu_by_distributor.csv")
uio = uio[uio.year == 2025].set_index("distributor_code").uio_units
fleet = {"Norway": int(uio["NORWAY"]), "Sverige": int(uio["SWEDEN"])}
nv = b[b.gps_db_label.isin(fleet)]
tot = nv.groupby("gps_db_label").eur.sum()
res["nordic"] = {"fleet": fleet, "eur": {k: round(v, 2) for k, v in tot.items()},
                 "per_vehicle": {k: round(tot[k] / fleet[k], 1) for k in fleet}}
fam = nv[~blank(nv.aim_l1_fixed)].pivot_table(index="aim_l1_fixed", columns="gps_db_label", values="eur", aggfunc="sum").fillna(0)
fam["gap_pv"] = fam.Norway / fleet["Norway"] - fam.Sverige / fleet["Sverige"]
res["nordic"]["family_gap_pv"] = [{"l1": k, "norway_pv": round(r.Norway / fleet["Norway"], 2),
                                   "sweden_pv": round(r.Sverige / fleet["Sverige"], 2), "gap_pv": round(r.gap_pv, 2)}
                                  for k, r in fam.sort_values("gap_pv", ascending=False).iterrows()]
det = []
for l3 in ["Steering Unit", "Brake Pad Kit"]:
    x = nv[nv.aim_l3_fixed == l3]
    for db in fleet:
        y = x[x.gps_db_label == db]
        det.append({"l3": l3, "db": db, "eur": round(y.eur.sum(), 2), "qty": float(y.billed_qty.sum()),
                    "pn": int(y.part_number.nunique()), "eur_pv": round(y.eur.sum() / fleet[db], 2),
                    "qty_per_100": round(y.billed_qty.sum() / fleet[db] * 100, 2)})
res["nordic"]["detail"] = det

# ---- Japan's catalogue code (ZKK) next to AIM, and what sits in the part without a code
z = b.jp_zkk.fillna("").str.strip()
zt = b[z != ""].groupby(z[z != ""]).eur.sum().sort_values(ascending=False)
top_code = zt.index[0]
tc = b[z == top_code]
nz = b[z == ""]
nz_nonpart = nz.eur[NONPART_MASK[nz.index]].sum()
nz_steer = nz.eur[(nz.aim_l3_fixed == "Steering Unit") & ~NONPART_MASK[nz.index]].sum()
res["zkk"] = {
    "pct_with_code": round(b.eur[z != ""].sum() / T * 100, 2), "eur_without_code": round(nz.eur.sum(), 2),
    "without_code_nonpart_eur": round(nz_nonpart, 2), "without_code_steering_eur": round(nz_steer, 2),
    "without_code_steering_pn": int(nz[nz.aim_l3_fixed == "Steering Unit"].part_number.nunique()),
    "without_code_other_eur": round(nz.eur.sum() - nz_nonpart - nz_steer, 2),
    "pct_with_code_parts_only": round(b.eur[(z != "") & ~NONPART_MASK].sum() / b.eur[~NONPART_MASK].sum() * 100, 2),
    "top_code": top_code, "top_code_eur": round(zt.iloc[0], 2), "top_code_pct": round(zt.iloc[0] / T * 100, 2),
    "top_code_aim_l3_types": int(tc.loc[~blank(tc.aim_l3_fixed) & (tc.eur > 0), "aim_l3_fixed"].nunique()),
    "top_code_by_l1": [{"l1": k, "eur": round(v, 2)} for k, v in
                       tc[~blank(tc.aim_l1_fixed)].groupby("aim_l1_fixed").eur.sum().sort_values(ascending=False).head(8).items()],
    "codes_per_type": {t: int(b[(b.aim_l3_fixed == t) & (z != "") & (b.eur > 0)].jp_zkk.nunique())
                       for t in ["Air Cleaner Filter", "Brake Pad Kit", "Brake Rotor", "Door"]}}

OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
for k in ("base", "composition", "coverage", "steering", "zkk", "increase_total"):
    print(k, json.dumps(res[k], ensure_ascii=False)[:900])
