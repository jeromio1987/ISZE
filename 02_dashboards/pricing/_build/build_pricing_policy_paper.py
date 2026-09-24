# -*- coding: utf-8 -*-
"""
Builds the visual pricing paper: a self-contained HTML with embedded data and an
inlined Chart.js (no CDN, opens from file://).

Every chart follows the house chart rule: the title is the business question, the
form is chosen from the relationship, and no gap is shown without context.

Run: python 02_dashboards/pricing/_build/build_pricing_policy_paper.py
Writes: 02_dashboards/pricing/ISZE_Pricing_Policy_Paper.html
        02_dashboards/pricing/OPEN_ISZE_Pricing_Policy_Paper.cmd
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
D = os.path.join(ISZE, "01_data", "00_derived")
OUT_DIR = os.path.join(ISZE, "02_dashboards", "pricing")
HTML = os.path.join(OUT_DIR, "ISZE_Pricing_Policy_Paper.html")
CMD = os.path.join(OUT_DIR, "OPEN_ISZE_Pricing_Policy_Paper.cmd")


def say(m):
    print(m)
    sys.stdout.flush()


def eur(v):
    return "\u20ac" + format(round(v), ",d")


def money(v):
    return "\u20ac" + f"{v/1e6:.2f}M"


# =============================================================== 1. build data
say("Loading derived files ...")

spec = json.load(open(os.path.join(OUT_DIR, "_build", "_spec_basis_meta.json"), encoding="utf-8"))
cost = json.load(open(os.path.join(D, "pricing_cost_floor_meta.json"), encoding="utf-8"))
fx = json.load(open(os.path.join(D, "pricing_chain_and_fx_meta.json"), encoding="utf-8"))
rec = json.load(open(os.path.join(D, "aim_pricing_recalc_2026-09-17.json"), encoding="utf-8"))
wl_meta = json.load(open(os.path.join(D, "price_collection_worklist_meta.json"), encoding="utf-8"))

fam = pd.read_csv(os.path.join(D, "pricing_cost_floor_by_family.csv"))
reach = pd.read_csv(os.path.join(D, "pricing_cost_floor_reach.csv"))
chain = pd.read_csv(os.path.join(D, "pricing_chain_and_fx.csv"))
top200 = pd.read_csv(os.path.join(D, "margin_opportunity_top200.csv"), dtype={"pn": str})
work = pd.read_csv(os.path.join(D, "price_collection_worklist.csv"), dtype={"pn": str})
resp = pd.read_csv(os.path.join(D, "ituk_price_volume_response.csv"))

# --- the step by family, spine basis
fam_step = pd.DataFrame(rec["aim_l1"])[["aim_l1", "billed_eur", "step_eur", "pn"]]
spine_billed = fam_step["billed_eur"].sum()
spine_step = fam_step["step_eur"].sum()
fam_step["step_share"] = 100 * fam_step["step_eur"] / spine_step
fam_step = fam_step.sort_values("step_eur", ascending=False).head(15)

# --- the level test: family price move against family volume move
aim = pd.read_csv(os.path.join(D, "aim_pn_classification_20260920.csv"), dtype=str,
                  usecols=["part_number", "catalog_l1"])
aim["pn"] = aim["part_number"].astype(str).str.strip().str.zfill(10)
aim = aim.drop_duplicates("pn")
p = pd.read_csv(os.path.join(D, "price_bp_weighted_compare_pn.csv"), dtype={"part_number": str})
p = p[p["in_scope"] == True]                                                  # noqa: E712
p = p[p["bp_new_jpy"].notna() & p["bp_prior_revised"].notna()].copy()
p["pn"] = p["part_number"].str.strip().str.zfill(10)
p = p.merge(aim, on="pn", how="left")
price_by_fam = p.groupby("catalog_l1").apply(lambda x: pd.Series({
    "billed": x["net_sales_value"].sum(),
    "wt_move": 100 * ((x["billed_qty"] * x["bp_new_jpy"]).sum() /
                      (x["billed_qty"] * x["bp_prior_revised"]).sum() - 1),
}), include_groups=False)

rows = {}
for yr, f, gr in [(2023, "dealer_sellout_long_ITUK_CY2023.csv", "network_pn"),
                  (2025, "dealer_sellout_long_ITUK_CY2025.csv", "dealer_pn")]:
    x = pd.read_csv(os.path.join(D, f))
    x = x[x["grain"] == gr]
    x["pn"] = x["part_number"].astype(str).str.strip().str.zfill(10)
    x["qty"] = pd.to_numeric(x["qty"], errors="coerce")
    rows["y" + str(yr)] = x.groupby("pn")["qty"].sum()
q = pd.DataFrame(rows).fillna(0.0).reset_index().rename(columns={"index": "pn"})
q = q.merge(aim, on="pn", how="left")
vol_by_fam = q.groupby("catalog_l1")[["y2023", "y2025"]].sum()
vol_by_fam["vol_move"] = 100 * (vol_by_fam["y2025"] / vol_by_fam["y2023"] - 1)
level = price_by_fam.join(vol_by_fam, how="inner")
level = level[level["billed"] > 1000].reset_index()
r_level = float(level["wt_move"].corr(level["vol_move"]))

# --- brakes concentration
br = pd.read_parquet(os.path.join(D, "pricing_aim_source_lines.parquet"))
br["pn"] = br["part_number"].astype(str).str.strip()
br = br[(br["priced_both"] == True) & (br["aim_l1"] == "Brakes")]             # noqa: E712
brpn = br.groupby("pn").agg(description=("description", "first"),
                            billed=("billed_eur", "sum")).sort_values("billed", ascending=False)
br_top = brpn.head(20).reset_index().rename(columns={"index": "pn"})
cum = np.cumsum(br_top["billed"].to_numpy()) / brpn["billed"].sum() * 100

# --- the four pad kits
KITS = ["8975056801", "8975546610", "8982169210", "8982447940"]
pl = pd.read_parquet(os.path.join(D, "pricing_list_pn.parquet"),
                     columns=["part_number", "sp_eur", "bp_jpy", "is_superseded_row"])
pl = pl[pl["is_superseded_row"] != True]                                      # noqa: E712
pl["pn"] = pl["part_number"].astype(str).str.strip()
kits = []
for k in KITS:
    r = pl[pl["pn"] == k]
    b = br[br["pn"] == k]
    if len(r):
        kits.append({"pn": k, "list": round(float(r.iloc[0]["sp_eur"]), 2),
                     "bp": float(r.iloc[0]["bp_jpy"]),
                     "billed": round(float(b["billed_eur"].sum()), 0),
                     "distributors": int(b["db"].nunique()) if len(b) else 0})
kits = sorted(kits, key=lambda d: d["list"])

# --- worklist brands
brand = (work.dropna(subset=["competing_brand"])
         .groupby("competing_brand")["billed_eur"].agg(["count", "sum"])
         .sort_values("sum", ascending=False).head(10).reset_index())

# --- the cost floor: what our own distributor paid, against the aftermarket price.
# floor = bill_eur / bill_qty, per distributor per part number, on positive quantities.
# No distributor is blended into another and no price tier is mixed with another:
# this compares an AFTERMARKET part against a GENUINE assembly, and says so.
brd = pd.read_parquet(os.path.join(D, "replenishment_bridge.parquet"))
brd["pn"] = brd["part_number"].astype(str).str.strip()
for _c in ("bill_eur", "bill_qty"):
    brd[_c] = pd.to_numeric(brd[_c], errors="coerce")
_ok = brd[(brd["bill_qty"] > 0) & brd["bill_eur"].notna()]
_floors = (_ok.groupby(["distributor_code", "pn"])
           .agg(be=("bill_eur", "sum"), bq=("bill_qty", "sum")).reset_index())
_floors = _floors[_floors["bq"] > 0]
_floors["floor"] = _floors["be"] / _floors["bq"]

_bc = pd.read_csv(os.path.join(D, "oe_bridge_coverage.csv"), dtype={"pn": str})
_bc["pn"] = _bc["pn"].str.strip()
UOM = {"8980252486", "8982127181"}          # flagged unit/spec mismatches in the source file
_bc_clean = _bc[~_bc["pn"].isin(UOM)]

_j = _bc.merge(_floors, on="pn", how="inner")
_j["ratio"] = _j["min_price_eur"] / _j["floor"]
_lo = _j.groupby("pn")["floor"].min()
_hi = _j.groupby("pn")["floor"].max()
_r_any = (_bc_clean.set_index("pn")["min_price_eur"] / _hi).dropna()      # vs best floor
_r_all = (_bc_clean.set_index("pn")["min_price_eur"] / _lo).dropna()      # vs lowest floor
_rank = _r_all.sort_values()

CASES = [("8982924331", "IRELAND"), ("8982924321", "IRELAND"),
         ("8983034680", "ITUK"), ("8980094180", "GREECE")]
cases = []
for _pn, _db in CASES:
    _c = _bc[_bc["pn"] == _pn].iloc[0]
    _f = _floors[(_floors["pn"] == _pn) & (_floors["distributor_code"] == _db)]
    if len(_f) and len(_c):
        _floor = float(_f.iloc[0]["floor"])
        cases.append({"pn": _pn, "db": _db, "floor": round(_floor, 2),
                      "am": round(float(_c["min_price_eur"]), 2),
                      "brand": str(_c["cheapest_brand"]),
                      "ratio": round(float(_c["min_price_eur"]) / _floor, 3)})

# --- the two bridge sources are of different sizes; union them for the coverage figure
_eu = pd.read_csv(os.path.join(ISZE, "02_dashboards", "Data", "01_Pricing", "_raw",
                               "eucon_crossref_iam_20260329.csv"), dtype=str)
_eu["pn"] = (_eu["isze_pn"].astype(str).str.strip()
             .str.replace(r"\.0$", "", regex=True).str.zfill(10))
_book = pd.read_parquet(os.path.join(D, "pricing_aim_source_lines.parquet"))
_book["pn"] = _book["part_number"].astype(str).str.strip()
_cat = set(_book.loc[_book["priced_both"] == True, "pn"])                 # noqa: E712
_union = (set(_bc["pn"]) & _cat) | (set(_eu["pn"]) & _cat)

# --- Israeli shop lines against the floor, using the prices recorded in
# 01_data/90_INBOX/scrape_targets/israel.md (2026-09-18 sweep), net of VAT at €0.28715/ILS
SHOP = [("8980139111", 366.24), ("8973728510", 163.53), ("8972546810", 175.21),
        ("8981265720", 99.53), ("8972559050", 228.75), ("8971188600", 13.38),
        ("8981610620", 14.11), ("8981610610", 13.38), ("8981587290", 83.22),
        ("8981587300", 83.22), ("8981587310", 85.66), ("8981587320", 83.22),
        ("8983284490", 132.95), ("8980476610", 112.28), ("8974742480", 167.70),
        ("8974742510", 171.72), ("8981019465", 85.57), ("8980595332", 198.88),
        ("8981560020", 205.87), ("5876150170", 80.55)]
shop = []
for _pn, _net in SHOP:
    _f = _floors[_floors["pn"] == _pn]
    if len(_f):
        _r = _f.loc[_f["floor"].idxmin()]
        shop.append({"pn": _pn, "net": round(_net, 2),
                     "db": str(_r["distributor_code"]), "floor": round(float(_r["floor"]), 2),
                     "ratio": round(_net / float(_r["floor"]), 2)})
shop.sort(key=lambda x: x["ratio"])
say(f"  cost floor: {len(_bc)} bridged PNs, {len(_j)} part x distributor observations, "
    f"{int((_r_any < 1).sum())} below a floor (of {len(_r_any)})")
say(f"  Israel: {len(shop)} of {len(SHOP)} shop lines have a floor, "
    f"{sum(1 for s in shop if s['ratio'] < 1)} below it")

DATA = {
    "cover": {
        "step_eur": spec["step_eur"],
        "weighted_pct": spec["weighted_pct"] * 100,
        "billed_in_scope": 34993609.39,
        "billed_priced": spec["billed_eur_priced"],
        "gp": cost["headline"]["gross_profit_eur"],
        "gm": cost["headline"]["weighted_gm_pct"],
        "lines_priced": spec["lines_priced"],
        "part_numbers": 15872,
    },
    "margin_by_class": {
        "labels": ["C", "D", "F", "J", "M", "P", "V", "T"],
        "margins": [53.0, 52.0, 47.5, 44.5, 50.0, 56.0, 45.0, 20.0],
        "billed": [14511753, 3909756, 3501479, 91804, 908874, 2166634, 4552178, 0],
        "book_margin": cost["headline"]["weighted_gm_pct"],
    },
    "reach": {
        "labels": ["15%", "20%", "30%", "40%", "50%"],
        "multiple": [0.57, 0.60, 0.69, 0.80, 0.96],
        "median_to_match": cost["reach"]["median_gm_to_match_pct"],
        "median_today": cost["reach"]["median_gm_today_pct"],
        "visible": cost["reach"]["part_numbers_visible"],
        "unreachable": cost["reach"]["cost_above_competing_retail"],
        "thin": cost["reach"]["reachable_under_20pct_margin"],
        "workable": cost["reach"]["reachable_at_20pct_or_better"],
    },
    "chain": {
        "steps": ["Our net price\nto distributor", "Distributor\nprice to dealer",
                  "Dealer price\nto customer"],
        "now": [1.09, 1.53, 1.95],
        "at15": [0.58, 0.86, 1.03],
    },
    "coverage": {
        # Every share in this block is a share of the PRICED BOOK BY EURO VALUE, not of lines.
        # Two line-count measures sit beside it and are deliberately kept separate:
        #   no_benchmark_lines  = T5, lines with no benchmark price on file
        #   no_service_category_lines = lines with no service category on the captured-demand
        #                               measure, which is a different gate entirely
        "real_evidence_pct": 16.5,
        "category_median_pct": 4.8,
        "no_benchmark_pct": 78.8,
        "no_benchmark_eur": 25672208,
        "real_evidence_eur": 5369216,
        "basis": "share of the priced book by euro value",
        "lines_priced": int(spec["lines_priced"]),
        "no_benchmark_lines": int(spec["t5_lines"]),
        "no_benchmark_lines_pct": round(100 * spec["t5_lines"] / spec["lines_priced"], 1),
        "no_service_category_lines": int(spec["no_service_category_lines"]),
        # 83.5% is T4 + T5 BY EURO: no same-shop and no Eucon benchmark. The 4.8-point gap to
        # 78.8% is exactly the category-median tier, not a snapshot difference.
        "no_same_shop_or_eucon_pct": round(
            100 * (spec["tier_eur"]["T4"] + spec["tier_eur"]["T5"]) / spec["billed_eur_priced"], 1),
    },
    "level": {
        "points": [{"x": round(float(r.wt_move), 2), "y": round(float(r.vol_move), 1),
                    "label": str(r.catalog_l1), "billed": round(float(r.billed), 0)}
                   for r in level.itertuples()],
        "r": round(r_level, 2),
    },
    "fam_step": {
        "labels": fam_step["aim_l1"].tolist(),
        "step": [round(v, 0) for v in fam_step["step_eur"]],
        "billed": [round(v, 0) for v in fam_step["billed_eur"]],
        "share": [round(v, 1) for v in fam_step["step_share"]],
        "spine_billed": round(spine_billed, 0),
        "spine_step": round(spine_step, 0),
    },
    "brakes": {
        "labels": br_top["pn"].tolist(),
        "billed": [round(v, 0) for v in br_top["billed"]],
        "cum": [round(v, 1) for v in cum],
        "family_billed": round(float(brpn["billed"].sum()), 0),
        "top20_share": round(float(cum[-1]), 0),
        "kits": kits,
    },
    "top200": {
        "billed": float(top200["billed_eur"].sum()),
        "share_of_book": round(100 * top200["billed_eur"].sum() / spec["billed_eur_priced"], 1),
        "margin": 50.81,
        "with_price": int((top200["competition"] == 2).sum()),
        "with_price_eur": float(top200.loc[top200["competition"] == 2, "billed_eur"].sum()),
        "rival_named_eur": float(top200.loc[top200["competition"] == 1, "billed_eur"].sum()),
        "rival_named_pns": int((top200["competition"] == 1).sum()),
        "nothing": int((top200["competition"] == 0).sum()),
        "nothing_eur": float(top200.loc[top200["competition"] == 0, "billed_eur"].sum()),
        "crit_a": int((top200["criticality"] == "A").sum()),
    },
    "worklist": {
        "pns": wl_meta["counts"]["part_numbers"],
        "eur": wl_meta["counts"]["billed_eur"],
        "brand_named": wl_meta["counts"]["brand_named"],
        "brand_named_eur": wl_meta["counts"]["brand_named_billed_eur"],
        "crit_a": wl_meta["counts"]["criticality_A"],
        "brands": brand.to_dict("records"),
    },
    "fx": {
        "labels": ["Oct 2023", "Oct 2024", "Oct 2025\nin use", "stress\n175", "stress\n150"],
        "rates": [146.6, 159.4, 163.7, 175.0, 150.0],
        "index": [111.7, 102.7, 100.0, 93.5, 109.1],
        "in_use": 163.7,
    },
    "assumptions": {
        "db": 1.40,                 # markup on the distributor's cost -> 28.6% margin on price
        "dlr": 1.275,               # markup on the dealer's cost
        "chain": round(1.40 * 1.275, 3),
        "db_margin": 28.6,          # 1 - 1/1.40
        "dlr_margin": 21.6,         # 1 - 1/1.275
        "assumed_dist_margin": 35.0,  # STATED ASSUMPTION, not a measurement
        "book_margin": round(cost["headline"]["weighted_gm_pct"], 2),
    },
    "floor": {
        "bridge_pns": int(len(_bc)),
        "observations": int(len(_j)),
        "below_any": int((_r_any < 1).sum()),
        "testable_any": int(len(_r_any)),
        "below_all": int((_r_all < 1).sum()),
        "testable_all": int(len(_r_all)),
        "median_any": round(float(_r_any.median()), 3),
        "median_all": round(float(_r_all.median()), 3),
        "median_below": round(float(_j.loc[_j["ratio"] < 1, "ratio"].median()), 3),
        "min_ratio": round(float(_r_all.min()), 3),
        "cases": cases,
        "union": int(len(_union)),
        "catalogue": int(len(_cat)),
        "union_pct": round(100 * len(_union) / len(_cat), 2),
        "eucon": int(len(set(_eu["pn"]) & _cat)),
        "cards": int(len(set(_bc["pn"]) & _cat)),
        "uom_excluded": len(UOM),
        "above_every": int((_r_all >= 1).sum()),
    },
    "israel": {
        "lines": len(shop),
        "of_lines": len(SHOP),
        "below": int(sum(1 for s in shop if s["ratio"] < 1)),
        "below_2x": int(sum(1 for s in shop if s["ratio"] < 2)),
        "min": round(min(s["ratio"] for s in shop), 2),
        "median": round(float(np.median([s["ratio"] for s in shop])), 2),
        "max": round(max(s["ratio"] for s in shop), 2),
        "rows": shop,
        "uti_pns": 2201,
        "uti_share": 14.4,
    },
}
say(f"  data assembled: {len(json.dumps(DATA)):,} bytes JSON")

# =============================================================== 2. template
CHARTJS = open(os.path.join(ISZE, "02_dashboards", "_ui", "chart.umd.min.js"),
               encoding="utf-8", errors="replace").read()
say(f"  chart.js inlined: {len(CHARTJS):,} bytes")

CSS = """
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--line:#e3ded3;
--muted:#6b6256;--good:#1d9e75;--amber:#c48a16;--pale:#eef3f9}
*{box-sizing:border-box}
body{margin:0;background:#e8e5de;color:var(--ink);
font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
font-size:13px;line-height:1.5}
.page{width:210mm;min-height:297mm;margin:0 auto 8mm;background:#fff;position:relative;
box-shadow:0 2px 14px rgba(0,0,0,.13);padding:0}
.pad{padding:14mm 16mm}
.ph{display:flex;justify-content:space-between;align-items:baseline;font-size:9.5px;
letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.pn{letter-spacing:.08em}
h1{font-family:Georgia,serif;font-size:31px;line-height:1.12;margin:0 0 10px;color:var(--navy)}
h2{font-family:Georgia,serif;font-size:20px;line-height:1.2;margin:0 0 12px;color:var(--navy);
padding-bottom:7px;border-bottom:2px solid var(--navy)}
h3{font-family:Georgia,serif;font-size:14.5px;margin:16px 0 7px;color:var(--navy)}
h4{font-family:Georgia,serif;font-size:12.5px;margin:12px 0 5px;color:var(--navy)}
p{margin:0 0 9px}
.lede{font-size:14px;color:#3a3a3a}
.small{font-size:11px;color:var(--muted)}
.sec-n{font-family:Georgia,serif;color:var(--terra);font-size:13px;letter-spacing:.16em;
text-transform:uppercase;display:block;margin-bottom:3px}
/* cover */
.cover{background:var(--navy);color:#eef1f6;padding:0;display:flex;flex-direction:column;
min-height:297mm}
.cover .top{padding:16mm 16mm 0}
.cover .kicker{font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#8fa6c4}
.cover h1{color:#fff;font-size:36px;margin:9px 0 0;max-width:170mm}
.rule{width:58mm;height:3px;background:var(--terra);margin:13px 0 15px}
.cover .thesis{font-size:15px;color:#cfd9e8;max-width:150mm;line-height:1.5}
.cover .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;padding:0 16mm;
margin-top:auto}
.stat{background:rgba(255,255,255,.07);border-left:3px solid var(--terra);padding:9px 11px;
position:relative;cursor:default}
.stat .l{font-size:8.5px;color:#9fb0cc;text-transform:uppercase;letter-spacing:.5px;line-height:1.3}
.stat .v{font-family:Georgia,serif;font-size:19px;color:#fff;margin-top:2px}
.stat .s{font-size:9.5px;color:#8fa6c4;margin-top:2px;line-height:1.3}
.stat .tip{display:none;position:absolute;left:0;bottom:calc(100% + 7px);width:250px;
background:var(--paper);color:var(--ink);border-top:3px solid var(--terra);padding:9px 11px;
z-index:30;font-size:11px;line-height:1.45;box-shadow:0 8px 22px rgba(0,0,0,.3)}
.stat:hover .tip{display:block}
.cover .foot{padding:12mm 16mm 12mm;font-size:10px;color:#8fa6c4;
display:flex;justify-content:space-between;border-top:1px solid rgba(255,255,255,.13);
margin-top:12mm}
/* the dials strip - measured values and stated assumptions, kept visually apart */
.dials{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;padding:0 16mm;margin-top:14px}
.dl{background:rgba(255,255,255,.05);border-top:2px solid #4a6b96;padding:8px 10px}
.dl.assumed{background:rgba(192,85,45,.16);border-top:2px solid var(--terra)}
.dl .l{font-size:8px;color:#9fb0cc;text-transform:uppercase;letter-spacing:.4px;line-height:1.3}
.dl.assumed .l{color:#e7b9a4}
.dl .v{font-family:Georgia,serif;font-size:17px;color:#fff;margin-top:2px}
.dl .s{font-size:9px;color:#8fa6c4;margin-top:2px;line-height:1.3}
.dlnote{padding:8px 16mm 0;font-size:9.5px;color:#a9bad4;line-height:1.45}
.dlnote b{color:#fff}
/* assumption banner on a white page */
.assume{background:var(--pale);border-top:3px solid var(--terra);padding:9px 12px;margin:10px 0 13px}
.assume .h{font-family:Georgia,serif;font-size:12.5px;color:var(--navy);margin-bottom:4px}
.assume table{margin:7px 0 4px}
.tier{font-size:8.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.two-tier{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin:9px 0 11px}
.tierbox{background:#fff;border:1px solid var(--line);border-left:3px solid var(--navy);padding:9px 11px}
.tierbox.assumed{border-left-color:var(--terra);background:#fdf7f4}
.tierbox .t{font-family:Georgia,serif;font-size:12px;color:var(--navy);margin-bottom:4px}
.tierbox .big{font-family:Georgia,serif;font-size:19px;color:var(--terra);margin:2px 0 3px}
.tierbox .s{font-size:10px;color:#444;line-height:1.4}
/* verdict strip */
.verdict{background:var(--paper);border-left:4px solid var(--terra);padding:12px 15px;margin:0 0 14px}
.verdict .t{font-family:Georgia,serif;font-size:15px;color:var(--navy);line-height:1.4}
.verdict .t:first-letter{font-size:20px}
/* kpi row on white */
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0 14px}
.kpi{background:var(--pale);border-top:3px solid var(--navy);padding:9px 10px;position:relative;cursor:default}
.kpi .l{font-size:8.5px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);line-height:1.3}
.kpi .v{font-family:Georgia,serif;font-size:18px;color:var(--navy);margin-top:2px}
.kpi .s{font-size:9.5px;color:var(--muted);margin-top:2px}
.kpi:hover .tip{display:block}
.kpi .tip{display:none;position:absolute;left:0;top:calc(100% + 6px);width:262px;background:var(--navy);
color:var(--paper);border-top:3px solid var(--terra);padding:9px 11px;z-index:30;font-size:11px;
line-height:1.45;box-shadow:0 8px 22px rgba(0,0,0,.28)}
/* chart block */
.cb{background:#fff;border:1px solid var(--line);border-radius:5px;padding:11px 13px 9px;margin:11px 0 13px;
page-break-inside:avoid}
.cb .q{font-family:Georgia,serif;font-size:12.5px;color:var(--navy);font-weight:600;margin-bottom:2px}
.cb .sub{font-size:10.5px;color:var(--muted);margin-bottom:9px;line-height:1.4}
.hold{position:relative;height:300px}
.hold.tall{height:380px}
.hold.xtall{height:440px}
.hold.big{height:520px}
/* callouts */
.call{border-left:3px solid var(--terra);background:#fff;padding:9px 13px;margin:10px 0;border-radius:0 4px 4px 0}
.call.good{border-left-color:var(--good);background:#f2faf6}
.call.amber{border-left-color:var(--amber);background:#fdf6e8}
.call.dark{background:var(--navy);color:var(--paper);border-left-color:var(--terra)}
.call.dark b{color:#fff}
.call .h{font-family:Georgia,serif;font-size:13px;color:var(--navy);margin-bottom:3px}
.call.dark .h{color:#fff}
/* table */
table{width:100%;border-collapse:collapse;font-size:10.5px;margin:8px 0 11px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:6px 8px;font-weight:600;
font-size:9.5px;letter-spacing:.04em;text-transform:uppercase}
td{padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}
tr:nth-child(even) td{background:#faf9f6}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr.hi td{background:#fdf1ec;font-weight:600}
/* stacked bar */
.stack{display:flex;height:34px;border-radius:3px;overflow:hidden;margin:9px 0 5px}
.stack div{display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;font-weight:600}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:10px;color:var(--muted);margin-bottom:5px}
.legend span{display:flex;align-items:center;gap:5px}
.dot{width:9px;height:9px;border-radius:2px;display:inline-block}
/* two col */
.two{display:grid;grid-template-columns:1fr 1fr;gap:13px}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:11px}
.mini{background:var(--paper);padding:10px 12px;border-left:3px solid var(--navy)}
.mini .v{font-family:Georgia,serif;font-size:20px;color:var(--navy)}
.mini .l{font-size:9.5px;text-transform:uppercase;letter-spacing:.4em;color:var(--muted)}
.mini .s{font-size:10.5px;color:#444;margin-top:4px;line-height:1.4}
ul{margin:4px 0 9px 17px;padding:0}li{margin-bottom:4px}
.tag{display:inline-block;background:var(--navy);color:var(--paper);font-size:8.5px;
letter-spacing:.09em;padding:1px 6px;border-radius:2px;font-weight:700;text-transform:uppercase;
vertical-align:1px}
.tag.t{background:var(--terra)}.tag.g{background:var(--good)}.tag.a{background:var(--amber)}
@media print{body{background:#fff}.page{margin:0;box-shadow:none;page-break-after:always}
.cb{break-inside:avoid}}
"""

JS = """
const $=s=>document.querySelector(s);
const C={navy:'#15233c',terra:'#c0552d',paper:'#f7f4ee',muted:'#6b6256',
good:'#1d9e75',amber:'#c48a16',pale:'#eef3f9',line:'#e3ded3',slate:'#4a6b96'};
Chart.defaults.font.family='-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif';
Chart.defaults.font.size=11;
Chart.defaults.color=C.navy;
const fmtN=v=>v.toLocaleString('en-GB',{maximumFractionDigits:0});
const eur=v=>'\\u20AC'+fmtN(v);
const money=v=>'\\u20AC'+(v/1e6).toFixed(2)+'M';
/* compact axis ticks so labels never collide */
const axEUR=v=>Math.abs(v)>=1e6?'\\u20AC'+(v/1e6).toFixed(1)+'M':(Math.abs(v)>=1e3?'\\u20AC'+Math.round(v/1e3)+'k':'\\u20AC'+v);

/* 2. Margin by class - a point per class, not a range */
new Chart($('#c-margin'),{type:'bar',
 data:{labels:D.margin_by_class.labels,datasets:[
  {label:'margin the class sets',data:D.margin_by_class.margins,
   backgroundColor:D.margin_by_class.labels.map(l=>l==='T'?C.amber:C.navy),borderRadius:2,barPercentage:.68}]},
 options:{indexAxis:'y',maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>' class '+c.label+': '+c.parsed.x.toFixed(1)+'% margin'}},
   annotation:true},
  scales:{x:{beginAtZero:true,max:62,title:{display:true,text:'gross margin %',font:{size:10.5}},
    grid:{color:'#eceae4'}},
   y:{grid:{display:false}}}}}); 

/* 3. Reach - curve with parity reference */
new Chart($('#c-reach'),{type:'line',
 data:{labels:D.reach.labels,datasets:[
  {label:'our net price as a multiple of the competing price',data:D.reach.multiple,
   borderColor:C.terra,backgroundColor:'rgba(192,85,45,.12)',fill:true,tension:.32,
   pointBackgroundColor:C.terra,pointRadius:4,borderWidth:2.5},
  {label:'parity with the competing price',data:[1,1,1,1,1],borderColor:C.muted,
   borderDash:[5,4],borderWidth:1.4,pointRadius:0,fill:false}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>c.datasetIndex===0?
     ' at '+D.reach.labels[c.dataIndex]+' margin our price is '+c.parsed.y.toFixed(2)+'x the competitor':' parity'}}},
  scales:{y:{beginAtZero:true,max:1.1,title:{display:true,text:'x the competing price',font:{size:10.5}},
    grid:{color:'#eceae4'}},x:{title:{display:true,text:'margin we target on the part',font:{size:10.5}},
    grid:{display:false}}}}}); 

/* 4. Chain ladder */
new Chart($('#c-chain'),{type:'bar',
 data:{labels:D.chain.steps,datasets:[
  {label:'today, our margin ~51%',data:D.chain.now,backgroundColor:C.navy,borderRadius:3,barPercentage:.6},
  {label:'if we cut our margin to 15%',data:D.chain.at15,backgroundColor:C.terra,borderRadius:3,barPercentage:.6}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+c.parsed.y.toFixed(2)+'x the competing price'}}},
  scales:{y:{beginAtZero:true,max:2.1,title:{display:true,text:'x the competing retail price',font:{size:10.5}},
    grid:{color:'#eceae4'}},x:{grid:{display:false}}}}}); 

/* 5. Level test - does our price move volume? */
new Chart($('#c-level'),{type:'scatter',
 data:{datasets:[{label:'one commercial family',
   data:D.level.points.map(p=>({x:p.x,y:p.y,label:p.label,billed:p.billed})),
   backgroundColor:C.terra,pointRadius:7,pointHoverRadius:10}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>' '+c.raw.label+': price +'+c.raw.x.toFixed(1)+'%, volume '+
     (c.raw.y>0?'+':'')+c.raw.y.toFixed(1)+'%'}}},
  scales:{x:{title:{display:true,text:'list price move on the family, %',font:{size:10.5}},
    grid:{color:'#eceae4'}},
   y:{title:{display:true,text:'ITUK dealer sell-out volume move, %',font:{size:10.5}},
    grid:{color:'#eceae4'}}}}}); 

/* 6. Step by family */
new Chart($('#c-fam'),{type:'bar',
 data:{labels:D.fam_step.labels,datasets:[
  {label:'step euro',data:D.fam_step.step,backgroundColor:C.navy,borderRadius:2,yAxisID:'y'}]},
 options:{indexAxis:'y',maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>' step '+eur(c.parsed.x)+' ('+D.fam_step.share[c.dataIndex]+'% of the spine step)'}}},
  scales:{x:{title:{display:true,text:'step euro',font:{size:10.5}},ticks:{callback:axEUR,maxTicksLimit:5},
    grid:{color:'#eceae4'}},
   y:{grid:{display:false},ticks:{font:{size:9.5}},afterFit:s=>{s.width=124}}}}}); 

/* 7. Brakes concentration - Pareto */
new Chart($('#c-brakes'),{data:{labels:D.brakes.labels,datasets:[
  {type:'bar',label:'billed euro',data:D.brakes.billed,backgroundColor:C.navy,borderRadius:2,yAxisID:'y'},
  {type:'line',label:'cumulative share of the family',data:D.brakes.cum,borderColor:C.terra,
   backgroundColor:C.terra,borderWidth:2.2,tension:.25,pointRadius:3,yAxisID:'y1'}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>c.datasetIndex===0?' '+eur(c.parsed.y):
     ' top '+(c.dataIndex+1)+' = '+c.parsed.y.toFixed(0)+'% of the family'}}},
  scales:{x:{ticks:{maxRotation:70,minRotation:70,font:{size:9}},grid:{display:false}},
   y:{title:{display:true,text:'billed euro per part number',font:{size:10.5}},
    ticks:{callback:axEUR,maxTicksLimit:5},grid:{color:'#eceae4'}},
   y1:{position:'right',beginAtZero:true,max:100,title:{display:true,text:'cumulative %',font:{size:10.5}},
    grid:{display:false},ticks:{maxTicksLimit:5}}}}}); 

/* 8. Pad kits */
new Chart($('#c-kits'),{type:'bar',
 data:{labels:D.brakes.kits.map(k=>k.pn),datasets:[
  {label:'official list price',data:D.brakes.kits.map(k=>k.list),
   backgroundColor:D.brakes.kits.map((k,i)=>i===0?C.muted:C.navy),borderRadius:3,barPercentage:.55}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>{const k=D.brakes.kits[c.dataIndex];
     return [' list \\u20AC'+k.list.toFixed(2),' billed '+eur(k.billed),
             ' bought by '+k.distributors+' distributors'];}}}},
  scales:{y:{beginAtZero:true,max:118,
    title:{display:true,text:'official list price, EUR',font:{size:10.5}},grid:{color:'#eceae4'}},
   x:{grid:{display:false}}}}});

/* 9. FX */
new Chart($('#c-fx'),{type:'line',
 data:{labels:D.fx.labels,datasets:[
  {label:'EUR price index of an unchanged yen base price',data:D.fx.index,borderColor:C.navy,
   backgroundColor:'rgba(21,35,60,.10)',fill:true,tension:.3,pointRadius:4,borderWidth:2.4}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>' JPY/EUR '+D.fx.rates[c.dataIndex]+' \\u2192 index '+
     c.parsed.y.toFixed(1)+' (margin unchanged)'}}},
  scales:{y:{beginAtZero:false,min:88,max:118,
    title:{display:true,text:'index, Oct 2025 rate = 100',font:{size:10.5}},grid:{color:'#eceae4'}},
   x:{grid:{display:false}}}}}); 

/* 10. Worklist brands */
new Chart($('#c-work'),{type:'bar',
 data:{labels:D.worklist.brands.map(b=>b.competing_brand),datasets:[
  {label:'our revenue where this brand competes and we hold no price',
   data:D.worklist.brands.map(b=>b.sum),backgroundColor:C.navy,borderRadius:2,barPercentage:.72}]},
 options:{indexAxis:'y',maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>' '+eur(c.parsed.x)+' across '+
     D.worklist.brands[c.dataIndex].count+' part numbers'}}},
  scales:{x:{title:{display:true,text:'our annual revenue, EUR',font:{size:10.5}},
    ticks:{callback:axEUR,maxTicksLimit:4,autoSkip:true},grid:{color:'#eceae4'}},
   y:{grid:{display:false},ticks:{font:{size:9.5}}}}}});

/* 11. The cost floor - aftermarket price against what our own distributor paid */
new Chart($('#c-floor'),{type:'bar',
 data:{labels:D.floor.cases.map(c=>c.pn),datasets:[
  {label:'our distributor paid us, per unit',data:D.floor.cases.map(c=>c.floor),
   backgroundColor:C.navy,borderRadius:3,barPercentage:.62},
  {label:'cheapest aftermarket equivalent, online',data:D.floor.cases.map(c=>c.am),
   backgroundColor:C.terra,borderRadius:3,barPercentage:.62}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>{const k=D.floor.cases[c.dataIndex];
     return c.datasetIndex===0
       ? ' '+k.db+' paid \\u20AC'+k.floor.toFixed(2)+' per unit'
       : ' '+k.brand+' at \\u20AC'+k.am.toFixed(2)+' \\u2192 '+k.ratio.toFixed(2)+
         'x our distributor cost';}}}},
  scales:{y:{beginAtZero:true,
    title:{display:true,text:'EUR per unit',font:{size:10.5}},grid:{color:'#eceae4'}},
   x:{grid:{display:false},ticks:{font:{size:9.5}}}}}});

/* 12. Israel - shop price against the floor */
new Chart($('#c-israel'),{type:'bar',
 data:{labels:D.israel.rows.map(r=>r.pn),datasets:[
  {label:'Israeli shop net price, as a multiple of our distributor floor',
   data:D.israel.rows.map(r=>r.ratio),backgroundColor:C.navy,borderRadius:2,barPercentage:.74},
  {label:'parity with the floor',data:D.israel.rows.map(()=>1),borderColor:C.terra,
   borderDash:[5,4],borderWidth:1.6,type:'line',pointRadius:0,fill:false}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>{const k=D.israel.rows[c.dataIndex];
     return c.datasetIndex===0
       ? ' shop \\u20AC'+k.net.toFixed(2)+' vs '+k.db+' floor \\u20AC'+k.floor.toFixed(2)
       : ' parity';}}}},
  scales:{y:{beginAtZero:true,max:13.5,
    title:{display:true,text:'x the floor',font:{size:10.5}},grid:{color:'#eceae4'}},
   x:{grid:{display:false},ticks:{maxRotation:70,minRotation:70,font:{size:9}}}}}});
"""


def html() -> str:
    d = json.dumps(DATA)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE \u2014 A parts pricing policy</title>
<style>{CSS}</style></head><body>

<!-- ============================ COVER -->
<section class="page cover">
  <div class="top">
    <div class="kicker">Isuzu Europe \u00b7 Aftersales analytics \u00b7 internal</div>
    <h1>A parts pricing policy<br>for ISZE</h1>
    <div class="rule"></div>
    <div class="thesis">What we should charge, on what basis, and what has to be true
    before we can say it. Built on the FY2027 revision as filed, the parts
    classification, and the one panel in the workspace that can measure a
    volume response \u2014 which it cannot.</div>
  </div>
  <div class="stats">
    <div class="stat"><div class="l">Base price move</div>
      <div class="v">{DATA['cover']['weighted_pct']:.4f}%</div>
      <div class="s">weighted on last twelve months</div>
      <div class="tip">Quantity-weighted base price move on the in-scope revision base,
      window 1 Jul 2025 to 30 Jun 2026. Ties to the published figure to the cent.</div></div>
    <div class="stat"><div class="l">Value of the step</div>
      <div class="v">{money(DATA['cover']['step_eur'])}</div>
      <div class="s">on {eur(DATA['cover']['billed_priced'])} priced</div>
      <div class="tip">The euro value of that base price change on the volume actually
      billed in the window. It is not a revenue, margin or volume outcome.</div></div>
    <div class="stat"><div class="l">Gross profit at stake</div>
      <div class="v">{money(DATA['cover']['gp'])}</div>
      <div class="s">at {DATA['cover']['gm']:.2f}% margin</div>
      <div class="tip">On the 45,816 priced lines that carry a usable margin. The margin
      is set by the class letter, not by a commercial decision per part.</div></div>
    <div class="stat"><div class="l">Of the book we can price</div>
      <div class="v">16.5%</div>
      <div class="s">of the priced euro, on real external evidence</div>
      <div class="tip">880 lines carrying 5,369,216 euro have a same-shop or Eucon
      benchmark. That is 16.5% of the priced book by euro value, and 1.8% of the
      47,617 priced lines. The rest cannot be priced against a named alternative.</div></div>
  </div>

  <div class="dials">
    <div class="dl"><div class="l">Our book margin</div><div class="v">{DATA['assumptions']['book_margin']:.2f}%</div>
      <div class="s">measured, on the priced book</div></div>
    <div class="dl"><div class="l">Distributor markup</div><div class="v">{DATA['assumptions']['db']:.2f}&times;</div>
      <div class="s">= a {DATA['assumptions']['db_margin']:.1f}% margin on price</div></div>
    <div class="dl"><div class="l">Dealer markup</div><div class="v">{DATA['assumptions']['dlr']:.3f}&times;</div>
      <div class="s">= a {DATA['assumptions']['dlr_margin']:.1f}% margin on price</div></div>
    <div class="dl assumed"><div class="l">Distributor margin &mdash; assumption</div>
      <div class="v">{DATA['assumptions']['assumed_dist_margin']:.0f}%</div>
      <div class="s">stated, not measured. No dealer purchase price exists on disk.</div></div>
  </div>
  <div class="dlnote">The first three are the stack and the book as they are. The fourth is a
  <b>stated assumption</b>: ISZE does not hold dealer purchase prices and will not get them, and no
  distributor will share what it charges its dealers. A 1.40 markup on cost is a 28.6% margin on
  price, which is <b>not</b> the same thing as a 35% margin on price &mdash; the paper keeps the two
  in separate columns and never converts one into the other.</div>

  <div class="foot"><span>Working paper, revision 2 &middot; corrected 18 September 2026</span>
    <span>17 September 2026</span></div>
</section>

<!-- ============================ 1. VERDICT -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">1 \u00b7 the verdict</span><span>A parts pricing policy for ISZE</span></div>

  <div class="verdict"><div class="t">We should move from one annual percentage applied
  to the whole book to a priced policy that changes different parts by different
  amounts \u2014 and the first thing that has to change is not the price, it is the
  number of parts we can see a competitor's price for.</div></div>

  <p class="lede">The reason is not that the current method is badly executed. It is
  that the method answers a question we have stopped asking. A single weighted
  percentage is right if the objective is &ldquo;raise the book by X&rdquo;. It is wrong if
  the objective is &ldquo;charge what each part is worth, given who is actually
  competing for it&rdquo;. Those parts of the book behave in opposite directions and one
  number cannot be right for both.</p>

  <div class="kpis">
    <div class="kpi"><div class="l">Margin is a lookup</div><div class="v">51.09%</div>
      <div class="s">on every part, from one letter</div>
      <div class="tip">The list price is built as cost divided by a divisor, and the
      divisor is one minus the intended margin. So the margin is set in advance by the
      class letter on the part. Class C means 53.0%, class V means 45.0%. Nothing about
      the market or the competitor enters it.</div></div>
    <div class="kpi"><div class="l">Margin available to give</div><div class="v">1 pt</div>
      <div class="s">median, on the parts we can see</div>
      <div class="tip">On 41 part numbers with an observed competing price, the median
      margin needed to match that price is 52% and the median margin held today is 53%.
      Our reference dealer price sits at 1.64x the competing retail price.</div></div>
    <div class="kpi"><div class="l">Cannot be reached by margin</div><div class="v">12 of 41</div>
      <div class="s">our cost is above their retail</div>
      <div class="tip">On these part numbers our landed cost already exceeds the
      competing retail price, so no margin target reaches it. That is a sourcing
      question, not a pricing one.</div></div>
    <div class="kpi"><div class="l">Top-200 with a rival, unpriced</div><div class="v">66.6%</div>
      <div class="s">of our largest revenue</div>
      <div class="tip">139 of our 200 largest part numbers, worth 10,353,141 euro, have a
      competing brand identified and no price on file. We charge 51.3% margin on them,
      against 49.9% on the 47 where we can see the rival. Statistically the same number.</div></div>
  </div>

  <div class="two">
    <div class="cb"><div class="q">Does our price move volume at all?</div>
      <div class="sub">Each dot is one commercial family. Price move on the horizontal,
      ITUK dealer sell-out volume move on the vertical. 2023 to 2025.</div>
      <div class="hold tall"><canvas id="c-level"></canvas></div>
      <div class="small" style="margin-top:6px">Correlation across the seven families:
      <b>r = {DATA['level']['r']}</b>. No relationship. The family that took the largest
      increase lost volume, and so did the family that took the smallest.</div></div>
    <div class="cb"><div class="q">Can a margin cut even reach the competitor?</div>
      <div class="sub">Our net price as a multiple of the competing price, at each
      margin we could target. The dashed line is parity.</div>
      <div class="hold tall"><canvas id="c-reach"></canvas></div>
      <div class="small" style="margin-top:6px">At a 15% margin our price is still
      0.57x the competitor \u2014 cheaper than them, with the margin given away.</div></div>
  </div>

  <div class="call dark"><div class="h">The one sentence</div>
  We do not have a pricing problem on our largest revenue. We have a
  <b>missing-number</b> problem: two thirds of our top-200 revenue sits on parts where
  we can name the competing brand and cannot name its price.</div>
</div></section>

<!-- ============================ 2. MARGIN -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">2 \u00b7 where the margin comes from</span><span>revision 2</span></div>
  <h2><span class="sec-n">section two</span>The margin is not a decision. It is a letter.</h2>

  <p>The list price is built as <b>cost in yen, converted at the rate, divided by a
  divisor</b> &mdash; and that divisor is one minus the intended margin. So the margin is
  fixed before anyone looks at the part's market: it is set by the class letter.</p>

  <div class="cb"><div class="q">Is the margin a commercial decision or a lookup?</div>
    <div class="sub">Each bar is one class letter and the margin it sets. The vertical
    rule is the book's weighted margin.</div>
    <div class="hold tall"><canvas id="c-margin"></canvas></div>
    <div class="small" style="margin-top:6px">Within each of these classes the margin is
    identical to a few hundredths of a point for <b>every part number in the
    catalogue</b>. The eight letters span 45% to 56%, and <b>84.3% of the priced book
    earns inside that band</b>. There is no high-margin set of parts and no low-margin
    set.</div></div>

  <div class="three">
    <div class="mini"><div class="l">Letters</div><div class="v">8</div>
      <div class="s">C D F J M P T V. Each one sets one margin for every part carrying it.</div></div>
    <div class="mini"><div class="l">Margin band</div><div class="v">11 pts</div>
      <div class="s">45% to 56%. The policy we argue about annually is a five-point band around 51%.</div></div>
    <div class="mini"><div class="l">Under-earned by rule</div><div class="v">69.3%</div>
      <div class="s">One sensor already earns this, against the 56% our most aggressive letter allows.</div></div>
  </div>
</div></section>

<!-- ============================ 3. COST FLOOR -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">3 \u00b7 the cost floor</span><span>revision 2</span></div>
  <h2><span class="sec-n">section three</span>A price has to clear two tests, not one</h2>

  <p class="lede">Revision 1 asked only whether a price was defensible against the
  competitor. A price also has to leave enough margin to be worth selling, and it has to
  be visible at the counter. Both of those constrain the margin idea hard.</p>

  <div class="call amber"><div class="h">One thing the floor does not need, and will not get</div>
  <b>ISZE does not hold a dealer purchase price and will not get one.</b> A distributor's
  resale price to its dealers is commercially confidential and no distributor will share it.
  Every dealer-level figure in this paper is therefore <b>built</b>, not observed &mdash;
  official list &times; 1.40 &times; 1.275 at a stated distributor margin &mdash; and it is
  labelled as a construction wherever it appears. What the floor <i>does</i> use is our own
  cost and our own billed price, per part number, which is what the next page measures.</div>

  <div class="two">
    <div>
      <div class="call"><div class="h">A price has to clear cost, not just the competitor</div>
      On the 41 part numbers where we can see a competing price: <b>12</b> already have our
      cost above their retail price, so no margin target reaches them at all; 3 are reachable
      only inside the dealer's own margin; 26 are reachable at 20% margin or better. Median
      margin needed to match: <b>{DATA['reach']['median_to_match']:.0f}%</b>. Median held
      today: <b>{DATA['reach']['median_today']:.0f}%</b>.</div>
      <table>
        <tr><th>Reach on the 41 observed parts</th><th class="n">Count</th></tr>
        <tr><td>Cost already above their retail</td><td class="n">{DATA['reach']['unreachable']}</td></tr>
        <tr><td>Reachable only under 20% margin</td><td class="n">{DATA['reach']['thin']}</td></tr>
        <tr class="hi"><td>Reachable at 20% margin or better</td><td class="n">{DATA['reach']['workable']}</td></tr>
      </table>
    </div>
    <div class="cb"><div class="q">What a uniform margin target would imply</div>
      <div class="sub">Our net price as a multiple of the competing price, at each margin we
      could target. Parity is 1.00.</div>
      <table style="margin-top:9px">
        <tr><th>Margin we target</th><th class="n">Our net price vs the competitor</th></tr>
        <tr class="hi"><td>15%</td><td class="n">0.57&times;</td></tr>
        <tr><td>20%</td><td class="n">0.60&times;</td></tr>
        <tr><td>30%</td><td class="n">0.69&times;</td></tr>
        <tr><td>40%</td><td class="n">0.80&times;</td></tr>
        <tr><td>50%</td><td class="n">0.96&times;</td></tr>
      </table>
      <div class="small">Read the top row. At a 15% margin our net price is still 57% of the
      competing price &mdash; below them, with the margin given away, and the dealer then adds
      their own margin on top of a cost we have just destroyed.</div></div>
  </div>

  <div class="call dark"><div class="h">The marquee case is not a margin problem</div>
  Part number <b>8975546610</b>, a front brake pad kit, class V, 45% margin. Our list is
  82.25 euro, our implied cost 45.24, and the cheapest observed same-shop listing is
  <b>17.55 euro</b>. <b>Our cost is 2.6 times their retail price.</b> Moving our margin
  from 45% to 15% does not change that ratio by a cent. The lever on that part is
  sourcing, not price.</div>
</div></section>

<!-- ============================ 3b. THE AFTERMARKET BELOW OUR COST -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">3 \u00b7 the cost floor, continued</span><span>added 18 September 2026</span></div>
  <h2><span class="sec-n">section three, continued</span>On these parts the rival is below our distributor's cost</h2>

  <p class="lede">The cost floor above compares us to a competing price. This compares the
  competing price to what our own distributor <b>paid us</b>, on the same part number, per
  distributor. On <b>{DATA['floor']['below_any']} of {DATA['floor']['testable_any']}</b> bridged
  part numbers the aftermarket equivalent sits below at least one of our distributor's own
  floors, at a median of <b>{DATA['floor']['median_any']:.2f}&times;</b>.</p>

  <div class="cb"><div class="q">Is the competing price above or below what our distributor paid?</div>
    <div class="sub">Four verified cases. Navy is the net price our distributor paid per unit
    in CY2025; terracotta is the cheapest aftermarket equivalent online. They are different
    goods and the chart says so.</div>
    <div class="hold"><canvas id="c-floor"></canvas></div>
    <table>
      <tr><th>Part number</th><th>Part</th><th>Distributor floor</th><th class="n">Floor EUR</th><th class="n">Aftermarket EUR</th><th class="n">Ratio</th><th>Cheapest brand</th></tr>
      <tr><td>8982924331</td><td>SENSOR; SPD,FRT WHEEL</td><td>IRELAND</td><td class="n">147.48</td><td class="n">21.96</td><td class="n"><b>0.15&times;</b></td><td>BLUE PRINT</td></tr>
      <tr><td>8982924321</td><td>front wheel speed sensor</td><td>IRELAND</td><td class="n">145.83</td><td class="n">21.90</td><td class="n"><b>0.15&times;</b></td><td>BLUE PRINT</td></tr>
      <tr><td>8983034680</td><td>CALIPER; RR DISC BRK</td><td>ITUK</td><td class="n">179.90</td><td class="n">28.34</td><td class="n"><b>0.16&times;</b></td><td>FRENKIT</td></tr>
      <tr class="hi"><td>8980094180</td><td>SENSOR; MAP</td><td>GREECE</td><td class="n">105.02</td><td class="n">17.17</td><td class="n"><b>0.16&times;</b></td><td>NTY</td></tr>
    </table>
    <div class="small">Floor = billed euro &divide; billed quantity per distributor per part
    number, CY2025. Each row names the one distributor it is measured against; no distributor
    is blended with another. <b>{DATA['floor']['below_all']} of {DATA['floor']['testable_all']}</b>
    part numbers sit below <i>every</i> floor we hold. Median against the lowest floor:
    <b>{DATA['floor']['median_all']:.2f}&times;</b>.</div></div>

  <div class="assume" style="margin-top:9px"><div class="h">The caveat that shrinks this finding</div>
  <b>This compares an aftermarket part against a genuine assembly.</b> They may not be the same
  article at the same specification, so the ratio <b>overstates the gap</b>. Read it as a
  landing-price fact &mdash; what a buyer can pay for an equivalent &mdash; not as a
  like-for-like comparison. Two rows in the source file (two EGR coolers, priced at several times
  our own list) are a unit-of-measure fault and are excluded from every figure here; excluding
  them changes nothing, still 26 of 33.</div>
</div></section>

<!-- ============================ 3b-ii. WHAT THE FLOOR CHANGES -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">3 \u00b7 what the floor changes</span><span>added 18 September 2026</span></div>
  <h2><span class="sec-n">section three, continued</span>The price lever comes off these parts</h2>

  <p class="lede">Section 3.2 ended on the 12 part numbers where our cost is already above the
  competing retail price: a sourcing problem, not a pricing problem. The bridge does not merely
  repeat that conclusion. It makes the same point larger and sharper &mdash; and this is the
  section's conclusion, revised.</p>

  <div class="two-tier">
    <div class="tierbox assumed"><div class="tier">what it means for the decision</div>
      <div class="t">There is no cost-to-price gap here to decide</div>
      <div class="s">On the bridged parts the competing price is often below our
      <b>distributor's cost</b>, not merely below our price, and the ratios are not 1.1&times; or
      1.3&times; &mdash; they are around <b>0.15&times;</b>. There is no margin target, at any
      level above zero, that reaches a price sitting at roughly one seventh of what the
      distributor paid. Cutting margin at any level cannot move a relationship between two
      numbers that are both already below our price.</div></div>
    <div class="tierbox"><div class="tier">where that leaves the question</div>
      <div class="t">What is in the box, and what does it cost us</div>
      <div class="s">The floor does not merely constrain the margin idea. On this subset it
      removes the price lever entirely, and it moves the question from <i>what should we
      charge</i> to <i>what is actually in the box, and what does it cost us to put one
      there</i>. That is the sourcing route the external review ranks third, and our own data now
      argues for it from two directions.</div></div>
  </div>

  <div class="assume" style="margin-top:11px"><div class="h">Coverage limit, stated with the finding</div>
  The bridge resolves <b>{DATA['floor']['union']} of {DATA['floor']['catalogue']:,}</b> priced part
  numbers &mdash; <b>{DATA['floor']['union_pct']:.2f}%</b> &mdash; as the union of two sources that
  share no part numbers between them: a licensed cross-reference of {DATA['floor']['eucon']}
  priced part numbers and a third-party multi-brand lookup of {DATA['floor']['cards']}. Both were
  assembled from parts we already knew had a named competitor, so
  <b>{DATA['floor']['union_pct']:.2f}% is optimistic, not conservative</b> as a rate across the
  catalogue.
  <div class="two" style="margin-top:9px">
    <div class="mini" style="background:#fff;border-left-color:var(--terra)">
      <div class="v">{DATA['floor']['testable_any']}</div>
      <div class="l">part numbers, and it must say so</div>
      <div class="s">A conclusion from {DATA['floor']['testable_any']} part numbers must say it is
      {DATA['floor']['testable_any']}. The finding is a warrant to go and look at the rest of the
      book, not a rate to apply to it.</div></div>
    <div class="mini" style="background:#fff;border-left-color:var(--terra)">
      <div class="v">{DATA['floor']['above_every']}</div>
      <div class="l">behave the other way</div>
      <div class="s">{DATA['floor']['above_every']} of the {DATA['floor']['testable_all']} sit
      <i>above</i> every floor we hold, at ratios up to 4.9&times;. The bridge is a spread and not
      a uniform story, and the two ends of it call for different decisions.</div></div>
  </div></div>
</div></section>

<!-- ============================ 3c. THE CHAIN -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">3 \u00b7 the chain</span><span>corrected 18 September 2026</span></div>
  <h2><span class="sec-n">section three, continued</span>What the customer faces, and what is assumption</h2>

  <p class="lede">Three margins are stacked on a part: ours, the distributor's, the dealer's.
  Two of those three are <b>stated assumptions</b>, not measurements, and the two
  distributor numbers in circulation are not the same quantity.</p>

  <div class="assume" style="margin-top:6px"><div class="h">What is measured here, and what is assumed</div>
  <div class="two-tier" style="margin-top:6px">
    <div class="tierbox"><div class="tier">measured, ours</div>
      <div class="t">Our book margin</div><div class="big">{DATA['assumptions']['book_margin']:.2f}%</div>
      <div class="s">Read off the priced book. The reference dealer price is built from it
      (official list &times; 1.40 &times; 1.275).</div></div>
    <div class="tierbox assumed"><div class="tier">stated assumption</div>
      <div class="t">Distributor margin</div><div class="big">{DATA['assumptions']['assumed_dist_margin']:.0f}%</div>
      <div class="s">A dial, not a measurement. No dealer purchase price exists for us to hold.</div></div>
  </div>
  <table style="margin-top:6px">
    <tr><th>Step in the chain</th><th class="n">Markup</th><th>Basis</th><th class="n">Margin on their selling price</th></tr>
    <tr><td>Distributor, the stack in use</td><td class="n">1.40&times;</td><td>markup on <b>cost</b></td><td class="n">{DATA['assumptions']['db_margin']:.1f}%</td></tr>
    <tr><td>Dealer, the stack in use</td><td class="n">1.275&times;</td><td>markup on <b>cost</b></td><td class="n">{DATA['assumptions']['dlr_margin']:.1f}%</td></tr>
    <tr class="hi"><td>Distributor, working assumption</td><td class="n">&mdash;</td><td>margin on <b>price</b> (stated)</td><td class="n">{DATA['assumptions']['assumed_dist_margin']:.1f}%</td></tr>
  </table>
  <div class="small" style="margin-top:4px"><b>The 1.40 and the 35% are not two roundings of one
  number.</b> A 1.40 markup on cost is a <b>28.6% margin on price</b>; the 35% is a margin on
  price. They differ by about six points, and the difference is the difference between the stack
  we have been modelling and the margin we are now told to assume. This page uses 1.40 for the
  chain arithmetic, because that is what builds the reference dealer price in use
  (&times;{DATA['assumptions']['chain']:.3f} with the dealer), and states 35% as the working
  assumption wherever the distributor's own economics matter. Never both in one column, and never
  one converted into the other and quoted as measured.</div></div>

  <div class="cb" style="margin-top:9px"><div class="q">What the customer actually faces</div>
    <div class="sub">Our price, then the distributor's, then the dealer's &mdash; each as a
    multiple of the competing retail price, at the stack in use.</div>
    <div class="hold" style="height:262px"><canvas id="c-chain"></canvas></div>

  <div class="call" style="margin-top:8px"><div class="h">A 34-point give-away moves the dealer price by a third</div>
  A cut in our margin is multiplied by <b>{DATA['assumptions']['chain']:.3f}</b> before a
  customer sees it &mdash; and a cut that protects our position against the independent channel
  while destroying the dealer's margin <b>converts the dealer into a competitor</b>, invisibly for
  one to three years. <b>And the dealer price itself is a construction.</b> Whether a distributor
  passes a cut through at all is unknown and cannot be read out of any file we hold.</div></div>
</div></section>

<!-- ============================ 3d. CURRENCY -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">3 \u00b7 the currency lever</span><span>revision 2</span></div>
  <h2><span class="sec-n">section three, continued</span>Currency moves the price and the profit, and never moves the margin</h2>

  <p class="lede">This is the second thing revision 1 did not have, and it may be the
  largest single influence on our competitive position. The price is set in yen and converted.
  Because the margin is fixed by the letter and applied <i>after</i> the conversion, FX moves
  the euro price and the euro gross profit, and never moves the margin percentage at all.</p>

  <div class="cb"><div class="q">Has the yen rate been doing the pricing for us?</div>
    <div class="sub">The euro price of a yen base price left unchanged, indexed to the
    rate now in use.</div>
    <div class="hold tall"><canvas id="c-fx"></canvas></div>
    <div class="small" style="margin-top:6px">From the rate in use in 2023 to the rate in
    use today, the euro price and the euro gross profit of an unchanged yen price fell
    <b>11.7%</b>. The margin percentage did not move at all. Our position against the
    competing price moved from <b>0.98x to 1.09x</b> with no decision taken and no line
    in any pack. A 7% currency move is larger than the gap between the ambition options
    we spend months debating.</div></div>

  <div class="call amber"><div class="h">Every competitive comparison we hold is FX-stamped, and none of them says so</div>
  The index in the AIM dashboard, the reference dealer price, the ratios in this paper &mdash;
  all of them move with a rate that was set on 1 October 2025. The yen base price and the class
  letter are IML's, and the rate is IML's, so the two largest inputs to our competitive position
  are both outside our control and neither appears in any ISZE pricing discussion. That is not a
  criticism of IML. It is an argument that ISZE should carry an FX sensitivity on every price
  pack it publishes, because otherwise we will keep explaining a currency move as a pricing
  outcome.</div>
</div></section>

<!-- ============================ 4. EVIDENCE -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">4 \u00b7 what we can actually price</span><span>revision 2</span></div>
  <h2><span class="sec-n">section four</span>Four fifths of the book has no competitor's price in it</h2>

  <div class="legend">
    <span><i class="dot" style="background:#15233c"></i> observed at the same shop, or Eucon</span>
    <span><i class="dot" style="background:#4a6b96"></i> category median</span>
    <span><i class="dot" style="background:#c0552d"></i> no benchmark on file</span>
  </div>
  <div class="stack">
    <div style="width:16.5%;background:#15233c">16.5% of euro</div>
    <div style="width:4.8%;background:#4a6b96">4.8% of euro</div>
    <div style="width:78.8%;background:#c0552d">78.8% of euro &mdash; no benchmark price</div>
  </div>
  <div class="small" style="margin-bottom:9px">Share of the {eur(DATA['cover']['billed_priced'])}
  priced book <b>by euro value</b>, and by the quality of the evidence behind the price. Two counts
  sit beside the shares and are not the same measure: <b>46,276 lines</b>
  ({DATA['coverage']['no_benchmark_lines_pct']:.1f}% of the {DATA['coverage']['lines_priced']:,} priced
  lines) have no benchmark <i>price</i> at all, and <b>46,893 lines</b> have no <i>service category</i>
  on the captured-demand measure, which is the first gate rather than the price gate. Counting the
  category-median tier as no benchmark takes the share to
  <b>{DATA['coverage']['no_same_shop_or_eucon_pct']:.1f}% of the priced euro</b>. A competitor exists
  for most of this book; what is missing is their price.</div>

  <h3 style="margin-top:12px">Our largest revenue looks contested and is priced as if captive</h3>
  <div class="cb"><div class="q">Does our largest revenue look contested or captive to us?</div>
    <div class="sub">Our top 200 part numbers by revenue, split by what we actually know
    about the competing price.</div>
    <div class="stack" style="height:40px;margin-bottom:7px">
      <div style="width:30.0%;background:#15233c">30.0% &mdash; we hold the rival price</div>
      <div style="width:66.6%;background:#c0552d">66.6% &mdash; rival named, no price</div>
      <div style="width:3.4%;background:#6b6256">3.4%</div>
    </div>
    <table>
      <tr><th>What we know about the rival</th><th class="n">Part numbers</th><th class="n">Revenue</th><th class="n">Our margin</th></tr>
      <tr><td>We hold the competing price</td><td class="n">{DATA['top200']['with_price']}</td><td class="n">{eur(DATA['top200']['with_price_eur'])}</td><td class="n">49.9%</td></tr>
      <tr class="hi"><td>A brand is named, the price is not held</td><td class="n">{DATA['top200']['rival_named_pns']}</td><td class="n">{eur(DATA['top200']['rival_named_eur'])}</td><td class="n">51.3%</td></tr>
      <tr><td>Nothing on file</td><td class="n">{DATA['top200']['nothing']}</td><td class="n">{eur(DATA['top200']['nothing_eur'])}</td><td class="n">49.4%</td></tr>
    </table>
    <div class="small">The margin we charge on revenue where a rival is named and unpriced
    is <b>51.3%</b>, against <b>49.9%</b> where we can see the rival's price. We are
    pricing our most contested revenue exactly as though it were captive, and we have no
    way to tell the difference.</div></div>

  <div class="call good"><div class="h">The bounded move that fixes it</div>
  <b>{DATA['worklist']['pns']} part numbers</b>, worth {eur(DATA['worklist']['eur'])}, carry a
  competing brand we can already name. <b>{DATA['worklist']['brand_named']} of them</b>
  ({eur(DATA['worklist']['brand_named_eur'])}) have the brand recorded &mdash; catalogue
  brands with published catalogues, so a lookup rather than a research programme. If half
  of those yield a price, evidence coverage on the top 200 goes from 30% to about 63% of
  revenue and those lines become priceable.
  <div class="small" style="margin-top:5px">Worklist:
  01_data/00_derived/price_collection_worklist.xlsx</div></div>
</div></section>

<!-- ============================ 4b. ISRAEL IS NOT A DISCOUNT CHANNEL -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">4 \u00b7 Israel, a separate question</span><span>added 18 September 2026</span></div>
  <h2><span class="sec-n">section four, continued</span>Israel is not a discount channel</h2>

  <p class="lede">On the {DATA['israel']['of_lines']} Israeli shop lines we could record,
  <b>{DATA['israel']['lines']}</b> have any official purchase floor in our data to test against
  &mdash; five distributors' floors, and <b>no Israeli one among them</b>. <b>Nothing is below
  the floor. Not one line.</b> The cheapest sits at <b>{DATA['israel']['min']:.2f}&times;</b> its
  floor, the median at <b>{DATA['israel']['median']:.2f}&times;</b>, the highest at
  <b>{DATA['israel']['max']:.2f}&times;</b>, and <b>not a single line is even as low as
  2&times;</b>.</p>

  <div class="cb"><div class="q">Are Israeli shops undercutting what our distributor pays?</div>
    <div class="sub">Each bar is one shop line: the shop's net price as a multiple of the
    lowest official floor on that part number. The dashed line is parity with the floor.</div>
    <div class="hold xtall"><canvas id="c-israel"></canvas></div>
    <div class="small" style="margin-top:6px">Read the levels, not the multiples. Every line is
    at or above <b>{DATA['israel']['min']:.2f}&times;</b> the floor, and
    <b>{DATA['israel']['below_2x']} of {DATA['israel']['lines']}</b> are below 2&times;. A shop
    price above a floor is not evidence about where it buys from &mdash; and here not one is
    below, so a discount channel is not what we are looking at.</div></div>

  <div class="two-tier">
    <div class="tierbox"><div class="tier">why the join was empty</div>
      <div class="t">Not a numbering problem</div>
      <div class="s">The shops list our own Isuzu numbers &mdash; the join was not missing a
      translation step. It came back empty for two other reasons: the bridge holds
      <b>zero UMI purchase rows</b>, and UTI prices only <b>{DATA['israel']['uti_pns']:,} part
      numbers &mdash; {DATA['israel']['uti_share']:.1f}% of the catalogue</b> &mdash; which
      intersects those shop lines <b>zero times</b>. A bigger cross-reference would not have
      fixed either.</div></div>
    <div class="tierbox assumed"><div class="tier">the lawful position, stated in full</div>
      <div class="t">Closed as a no-finding</div>
      <div class="s">This compares a shop's <b>retail</b> price against a distributor's
      <b>purchase</b> price &mdash; two tiers, deliberately, because a retail price that cannot
      reach a purchase price is not a discount channel. It is not a like-for-like comparison and
      is not presented as one. <b>Buying genuine parts trade-to-trade is lawful and protected by
      the motor vehicle block exemption, and no evidence of an unlawful route was found.</b> The
      only Israeli rows that cross any floor are a dismantler's <b>used</b> parts, tagged as
      such. The question of how these shops buy is therefore <b>closed as a no-finding</b> &mdash;
      the honest result, and not a clean bill of health.</div></div>
  </div>
  <div class="small" style="margin-top:5px">Floor = billed euro &divide; billed quantity per
  distributor per part number, CY2025 &mdash; an invoice average, with freight and rebates already
  inside it. Seven of the twenty lines have no floor at all, and five have neither a floor nor a
  translation, so the test runs on {DATA['israel']['lines']}. Shop prices: the 2026-09-18 sweep in
  <b>01_data/90_INBOX/scrape_targets/israel.md</b>, net of VAT at &euro;0.28715 per shekel. UMI and
  UTI are never blended.</div>
</div></section>

<!-- ============================ 5. THE VOLUME QUESTION -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">5 \u00b7 the volume question</span><span>revision 2</span></div>
  <h2><span class="sec-n">section five</span>We tried to measure it, and the method makes it unmeasurable</h2>

  <p class="lede">Revision 1 said no volume response was quotable. We then found a panel
  that could answer it &mdash; ITUK dealer sell-out, 2023 against 2025, with the list
  price on both sides, {len(resp):,} part numbers. The result is more useful than a
  coefficient.</p>

  <div class="two">
    <div class="call amber"><div class="h">The number, and why it is not identified</div>
      A naive reading gives an elasticity of <b>&minus;0.69</b>: a 3.3% list increase
      associated with a 1.9% volume fall. It does not survive contact with the price
      variation. The interquartile range of the price change is <b>0.69 percentage
      points</b>, and <b>70.6% of the book moved within one point of the median</b>.
      Inside that band the elasticity standard deviation is 22. The 226 parts that did
      move differently have a <b>median elasticity of exactly zero</b>.</div>
    <div class="call"><div class="h">Our method destroys the variation we would need</div>
      We change almost every part by almost the same amount &mdash; we have to, to solve a
      single weighted target with per-line caps. So the variation needed to measure a
      response is destroyed by the act of raising prices. And it cannot be read off the
      exception lines either, because those are the lines that moved for reasons other
      than the policy.</div>
  </div>

  <div class="cb"><div class="q">Does where we sit against the competition predict anything?</div>
    <div class="sub">29 ITUK part numbers with both an observed price index and 2023
    volume, grouped by how we sit against the independent price.</div>
    <table>
      <tr><th>Where we sit against the competing price</th><th class="n">Parts</th><th class="n">Volume 2023</th><th class="n">Volume 2025</th><th class="n">Change</th></tr>
      <tr><td>Cheaper than them (under 1.0x)</td><td class="n">7</td><td class="n">5,008</td><td class="n">6,566</td><td class="n">+31.1%</td></tr>
      <tr><td>1.0 to 1.5x</td><td class="n">10</td><td class="n">9,488</td><td class="n">14,730</td><td class="n">+55.2%</td></tr>
      <tr><td>1.5 to 2.5x</td><td class="n">8</td><td class="n">3,952</td><td class="n">4,962</td><td class="n">+25.6%</td></tr>
      <tr class="hi"><td>Far above them (over 2.5x)</td><td class="n">4</td><td class="n">14,576</td><td class="n">21,204</td><td class="n">+45.5%</td></tr>
    </table>
    <div class="small">The parts where we sit <b>furthest above</b> the independent price
    grew <b>fastest</b>. Across the whole family cross-section the correlation between the
    price move and the volume move is <b>{DATA['level']['r']}</b>.</div></div>

  <div class="call dark"><div class="h">The conclusion is stronger than &ldquo;we cannot
  measure it&rdquo;</div>
  The dealer's choice of genuine or independent is usually taken <b>before</b> anyone
  quotes a price &mdash; in the supplier relationship, in whose van calls at the door, in
  whether the part is on the shelf tonight. If that is where the decision is made, a price
  move at our level is not competing for a sale. It is competing with a decision already
  taken. <b>At this level in the chain there may be very little elasticity to
  measure.</b> The customers who stay are not comparing, and the ones who leave do not
  announce it. A price move here changes margin, not volume &mdash; which is exactly why
  the margin work matters more than any elasticity estimate would.</div>
</div></section>

<!-- ============================ 6. WHERE THE STEP LANDS -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">6 \u00b7 where the step lands</span><span>revision 2</span></div>
  <h2><span class="sec-n">section six</span>Which families carry the increase, and who chose</h2>

  <div class="cb"><div class="q">Which families are being repriced hardest, and who decided?</div>
    <div class="sub">Step euro by family on the AIM spine. The spine carries
    {money(DATA['fam_step']['spine_step'])} of the network's
    {money(DATA['cover']['step_eur'])} step, on
    {eur(DATA['fam_step']['spine_billed'])} of billed value.</div>
    <div class="hold big"><canvas id="c-fam"></canvas></div>
    <div class="small" style="margin-top:6px"><b>Brakes earn their step and Maintenance
    Service does not.</b> Brakes are the fourth-largest family by billed euro and the
    third-largest by step euro, on 347 part numbers, at 15.6% of the spine step.
    Maintenance Service is slightly larger by billed euro and carries 8.0%. That is not an
    accident of this revision &mdash; it reflects a decision taken somewhere that
    service-interval parts should move gently. The current method cannot express it,
    because it does not rank by family at all.</div></div>

  <div class="call amber"><div class="h">One euro in six is not on the spine at all</div>
  <b>6,883,708 euro</b> of in-scope billed value, <b>16.6% of the network step</b>, sits
  on part numbers that no category covers. A policy that prices by family cannot price
  that block, and it should not be distributed across the families above as though it
  had one.</div>
</div></section>

<!-- ============================ 6b. ISRAEL vs UK, CV vs LCV -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">7 \u00b7 Israel against the UK, CV against LCV</span><span>revision 2</span></div>
  <h2><span class="sec-n">section seven</span>I tried to answer this, and the evidence cannot</h2>

  <p class="lede">The question was whether Israel prices differently from the UK, and
  whether commercial vehicles differ from light commercial. I built the panel to answer
  both. <b>The file cannot support either answer, and the reason is worth knowing.</b></p>

  <div class="call dark"><div class="h">The governing finding</div>
  <b>All 43 part numbers carry exactly the same price index in every market they appear
  in.</b> Not similar &mdash; identical. Our list price is global, and the observed
  competitor price is a single national listing, so the same part has one index wherever
  you look. <b>Every market comparison in this file is a composition effect</b> &mdash;
  which parts that market happens to see &mdash; and not a statement about the market.
  <div class="small" style="color:#9fb0cc;margin-top:7px">Part numbers whose index
  differs by market: <b>0</b>. Part numbers whose competitor price differs by market:
  <b>0</b>. The index is a property of the part, not of the market.</div></div>

  <div class="two">
    <div>
      <h3>What the market averages actually are</h3>
      <table>
        <tr><th>Market</th><th class="n">Parts seen</th><th class="n">Median index</th></tr>
        <tr><td>Iceland</td><td class="n">11</td><td class="n">4.03x</td></tr>
        <tr><td>Finland</td><td class="n">17</td><td class="n">4.03x</td></tr>
        <tr><td>Sweden</td><td class="n">17</td><td class="n">3.78x</td></tr>
        <tr class="hi"><td><b>IUK</b> (LCV)</td><td class="n">19</td><td class="n">3.64x</td></tr>
        <tr class="hi"><td><b>UMI</b> (LCV)</td><td class="n">7</td><td class="n">3.64x</td></tr>
        <tr><td>Norway</td><td class="n">16</td><td class="n">3.47x</td></tr>
        <tr><td>Germany</td><td class="n">35</td><td class="n">1.95x</td></tr>
        <tr class="hi"><td><b>ITUK</b> (CV)</td><td class="n">28</td><td class="n">1.38x</td></tr>
        <tr class="hi"><td><b>UTI</b> (CV)</td><td class="n">15</td><td class="n">1.02x</td></tr>
      </table>
      <div class="small">Read down the parts-seen column, not the index column. Each
      market's median is simply the median of whichever parts it happens to check.</div>
    </div>
    <div>
      <h3>And the CV / LCV test, which is decisive</h3>
      <p>Six part numbers appear in <b>both</b> a CV market and an LCV market. If CV
      really priced differently, these would differ.</p>
      <table>
        <tr><th>Part number</th><th class="n">CV index</th><th class="n">LCV index</th></tr>
        <tr><td>8970622940</td><td class="n">1.59</td><td class="n">1.59</td></tr>
        <tr><td>8981596930</td><td class="n">4.23</td><td class="n">4.23</td></tr>
        <tr><td>8982054020</td><td class="n">1.08</td><td class="n">1.08</td></tr>
        <tr><td>8982705240</td><td class="n">1.04</td><td class="n">1.04</td></tr>
        <tr><td>8983214130</td><td class="n">1.56</td><td class="n">1.56</td></tr>
        <tr><td>8983314120</td><td class="n">1.02</td><td class="n">1.02</td></tr>
      </table>
      <div class="call amber" style="margin-top:8px"><b>Identical in every case.</b> The
      same part number carries the same index whichever vehicle it goes on. The apparent
      CV / LCV gap in the market averages is composition &mdash; CV markets check
      different parts from LCV markets.</div>
    </div>
  </div>

  <h3>What would actually answer the question</h3>
  <div class="three">
    <div class="mini"><div class="l">Ask for</div><div class="v">Per-market prices</div>
      <div class="s">A competitor price <b>per market</b> for the same part number. Today
      one listing value is applied to all 18 markets, so no market comparison exists at
      all.</div></div>
    <div class="mini"><div class="l">Ask for</div><div class="v">Vehicle application</div>
      <div class="s">The vehicle each part number fits, so a part can be attributed to CV
      or LCV rather than inferred from which distributor happens to stock it.</div></div>
    <div class="mini"><div class="l">Ask for</div><div class="v">More listings</div>
      <div class="s"><b>83% of the evidence rests on a single price</b> and the median
      number of competing brands found is exactly 1. One listing is not a market.</div></div>
  </div>
</div></section>

<!-- ============================ 7. BRAKES -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">7 \u00b7 brakes, end to end</span><span>revision 2</span></div>
  <h2><span class="sec-n">section seven</span>Twenty part numbers carry three quarters of the family</h2>

  <p class="lede">Brakes are the only family where this can be done properly: <b>82.6% of
  the family has a competitor reference</b>, against 16.5% of the book by euro. So it is the
  pilot, and it is a conversation about twenty part numbers rather than 334.</p>

  <div class="cb"><div class="q">Is the brakes family one decision or twenty?</div>
    <div class="sub">The largest 20 part numbers by billed euro, and the share of the
    family they accumulate to.</div>
    <div class="hold tall"><canvas id="c-brakes"></canvas></div>
    <div class="small" style="margin-top:6px">The bend in the curve is the finding:
    <b>twenty part numbers carry {DATA['brakes']['top20_share']:.0f}% of the money</b>, and
    the largest single one carries 22.4% on its own.</div></div>

  <div class="three">
    <div class="mini"><div class="l">Family billed</div><div class="v">{money(DATA['brakes']['family_billed'])}</div>
      <div class="s">334 part numbers, 1,267 lines on the revision base.</div></div>
    <div class="mini"><div class="l">Step on the family</div><div class="v">7.36%</div>
      <div class="s">against 5.96% for the network. Brakes are being repriced harder than the book, without anyone having decided that.</div></div>
    <div class="mini"><div class="l">Friction's share of the step</div><div class="v">52.8%</div>
      <div class="s">on 37.5% of the family's money. Pads and shoes are taking nearly one and a half times the move that discs and drums take.</div></div>
  </div>

  <div class="call"><div class="h">Why brakes is the pilot and not another family</div>
  <b>82.6% of the brakes family has a competitor reference</b> &mdash; 311 of 334 part
  numbers, 2,596,458 euro &mdash; against 16.5% of the book by euro (82.6% and 16.5% are
  both shares of billed euro, not line counts). That is the difference
  between a pilot that can produce a priced answer and one that cannot. It also has the
  loudest live complaint, which is on the next page.</div>
</div></section>

<!-- ============================ 8b. THE FOUR KITS -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">8 \u00b7 brakes, the live complaint</span><span>revision 2</span></div>
  <h2><span class="sec-n">section eight, continued</span>Four live pad kits, one function, a 25% spread</h2>

  <div class="cb"><div class="q">Why are four identical pad kits priced 82 to 103 euro, to different networks?</div>
    <div class="sub">Four front pad kits with the same description, each live and none
    superseded, with the official list price and the distributors who buy each.</div>
    <div class="hold tall"><canvas id="c-kits"></canvas></div>
    <table>
      <tr><th>Part number</th><th class="n">List EUR</th><th class="n">Base JPY</th><th class="n">Billed EUR</th><th class="n">Dist.</th><th>The network that buys it</th></tr>
      <tr><td>8975056801</td><td class="n">82.25</td><td class="n">12,120</td><td class="n">233,750</td><td class="n">13</td><td>IUK, ISD, Sverige, IBX, Norway, RSA, UMI, 6 more</td></tr>
      <tr><td>8975546610</td><td class="n">82.25</td><td class="n">12,120</td><td class="n">86,139</td><td class="n">8</td><td>Norway, IBX, Ireland, ISD, 4 more</td></tr>
      <tr class="hi"><td>8982447940</td><td class="n">89.11</td><td class="n">12,940</td><td class="n">342,394</td><td class="n">13</td><td><b>ITUK 228,730 &middot; UTI 65,234</b> &middot; Imotors, Ireland, 6 more</td></tr>
      <tr><td>8982169210</td><td class="n">102.65</td><td class="n">14,906</td><td class="n">79,679</td><td class="n">6</td><td>ITUK 74,146 &middot; Imotors &middot; Ireland</td></tr>
    </table>
    <div class="small">All four point to themselves as their newest part number and none
    is marked superseded, so this is <b>not</b> a supersession chain. What is here is
    stranger: the same function supplied under four part numbers at prices spanning
    <b>82.25 to 102.65 euro &mdash; a 25% spread</b> &mdash; with largely disjoint
    distributor bases. IUK buys only the cheapest; <b>ITUK and UTI are locked into the two
    most expensive</b>, and the part carrying the family's largest step, at +24.9%, is the
    one they are locked into.</div></div>

  <div class="call dark"><div class="h">The first question in the pilot is not a price question</div>
  It is whether those four part numbers are <b>interchangeable</b>. Different numbers for
  one function usually mean different model applications, GVW or brake systems, and the
  description is identical on all four so it does not settle it. <b>That is what the
  manufacturer's electronic parts catalogue answers.</b> If they are interchangeable, a
  25% price spread across the network on a safety-critical wear part is a commercial
  finding in its own right. If they are not, the +24.9% stands and gets the four-way
  split: source it, price it, hold it, or explain it.</div>

  <div class="call amber" style="margin-top:11px"><div class="h">And the larger part number is not a margin problem</div>
  On <b>8975546610</b>, a front pad kit at 45% margin, our list is 82.25 euro against an
  observed competing listing of <b>17.55</b>, with our landed cost at 45.24.
  <b>Our cost is 2.6 times their retail price.</b> No margin target reaches that. It is a
  sourcing question, and it is the clearest single example of the cost floor in the whole
  family.</div>
</div></section>

<!-- ============================ 8. DECISIONS -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">8 \u00b7 what it needs</span><span>revision 2</span></div>
  <h2><span class="sec-n">section eight</span>What to do next</h2>

  <h3>Start now, without anyone's permission</h3>
  <div class="call good"><div class="h">The price-collection worklist is built</div>
  <b>{DATA['worklist']['pns']} part numbers</b>, {eur(DATA['worklist']['eur'])}, ranked, with
  our list price and reference dealer price on each and the competing brand where we
  already know it. <b>{DATA['worklist']['brand_named']} of them have the brand
  recorded.</b> The sheet carries empty columns for their price, the brand actually found,
  the source, the evidence tier and the date. <b>{DATA['worklist']['crit_a']} of the
  {DATA['worklist']['pns']} are criticality A</b>, worth 6,682,029 euro.
  <div class="small" style="margin-top:6px">File:
  01_data/00_derived/price_collection_worklist.xlsx</div></div>

  <div class="cb"><div class="q">Which brands are standing in front of our largest parts?</div>
    <div class="sub">Our revenue on the worklist, by the competing brand already
    identified. These are the names to go and price, and the top five carry 29% of the
    list's revenue.</div>
    <div class="hold tall"><canvas id="c-work"></canvas></div>
    <div class="small">Catalogue brands with published catalogues, not marketplace
    listings. The one bulk source we had has been blocked since May and cannot be relied
    on, so this is a person with the sheet, one part number at a time.</div></div>
</div></section>

<!-- ============================ 9. TWO WORKSTREAMS -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">9 \u00b7 two workstreams</span><span>revision 2</span></div>
  <h2><span class="sec-n">section nine</span>Run these two alongside each other</h2>

  <div class="two">
    <div class="call"><div class="h">The brakes pilot, starting with identity</div>
      Brakes are the only family where this can be done properly: <b>82.6% of the family
      has a competitor reference</b>, against 16.5% of the book by euro, and twenty part numbers
      carry 76% of the money.
      <ul style="margin-top:7px">
        <li><b>First, the EPC check</b> on the four pad kits &mdash; are they
        interchangeable? That answers whether a 25% price spread exists on a
        safety-critical wear part.</li>
        <li><b>Then the four-way split</b> on whatever survives: source it, price it, hold
        it, or explain it.</li>
        <li><b>Then the sourcing list</b> &mdash; the parts where our cost already sits
        above their retail price. That is a buying question, not a pricing one.</li>
      </ul>
      <div class="small" style="margin-top:6px">One family done completely beats ten
      sketched.</div></div>
    <div class="call"><div class="h">The top-200 map, extended</div>
      The same method on revenue 200 to 500. No new inputs, no new judgement needed &mdash;
      the criticality map and the competition grading are already written and
      rerunnable.
      <div class="mini" style="margin-top:9px;border-left-color:var(--terra)">
        <div class="l">Prize, today</div><div class="v">{money(DATA['worklist']['eur'])}</div>
        <div class="s">Revenue where a rival competes and we hold no price.</div></div>
      <div class="mini" style="margin-top:7px;border-left-color:var(--terra)">
        <div class="l">Prize, extended</div><div class="v">~ &euro;20M</div>
        <div class="s">Estimated on the same density from revenue 200 to 500.</div></div>
      <div class="small" style="margin-top:7px">Builder:
      01_data/91_build/build_margin_opportunity_map.py</div></div>
  </div>

  <h3>And the same two written down as a sequence</h3>
  <table>
    <tr><th class="n">#</th><th>Step</th><th>Who</th><th>What it unblocks</th></tr>
    <tr><td class="n">1</td><td>Price the {DATA['worklist']['brand_named']} part numbers that already have a brand named</td>
      <td>a person with the sheet</td><td>Evidence coverage on the top 200 from 30% to about 63% of revenue</td></tr>
    <tr><td class="n">2</td><td>EPC check on the four pad kits</td><td>us</td>
      <td>Whether the 25% spread is real, and whether the +24.9% is a price decision at all</td></tr>
    <tr><td class="n">3</td><td>Extend the map to revenue 200&ndash;500</td><td>us</td>
      <td>Doubles the size of the prize on the same method</td></tr>
    <tr><td class="n">4</td><td>Brakes pilot, four-way split</td><td>us, with ITUK</td>
      <td>A priced answer on the family with the most evidence and the loudest complaint</td></tr>
    <tr class="hi"><td class="n">5</td><td>The four questions that need people, not analysis</td>
      <td>Jerome</td><td>See the next page</td></tr>
  </table>
</div></section>

<!-- ============================ 10. OPEN DECISIONS -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">10 \u00b7 not mine to answer</span><span>revision 2</span></div>
  <h2><span class="sec-n">section ten</span>Four questions no analysis can settle</h2>

  <p class="lede">Each of these moves the whole paper, and each needs a person rather than
  a model. They are listed smallest-first so the first can be taken today. <b>They are all
  questions for people.</b> Two of the four used to read as data requests, and neither can be
  answered from a file: a dealer purchase price does not exist for us to pull, and a
  pass-through is behaviour.</p>

  <table>
    <tr><th>Question</th><th>Why it cannot come from the data</th><th class="n">What it moves</th></tr>
    <tr><td><b>Do we have a voice in class assignment?</b></td>
      <td>The class letter <i>is</i> the margin, so whoever assigns the class assigns the
      price &mdash; and it fixes that margin for the life of the part. Asked in August and
      still open. If the answer is no, the margin discussion is an observation rather than
      a lever.</td>
      <td class="n">the whole margin</td></tr>
    <tr><td><b>What does the distributor do with a cut?</b></td>
      <td>Whether a distributor reduces the dealer price when we reduce ours, or widens
      their own margin instead. No model can answer it, and no file will either &mdash; a
      distributor's resale price is not something we hold or will obtain. If they hold
      absolute margin, the case for cutting reverses &mdash; it is the one finding that would
      overturn this paper. See section 4.</td>
      <td class="n">21 points of price</td></tr>
    <tr><td><b>Is the target before or after the support payment?</b></td>
      <td>At the 20% figure the specification uses, one euro of headline increase lands as
      0.80. So a headline of +4% nets +3.2%, and to net +4% the headline must be +5.0%.
      The 20% itself is not a signed term.</td>
      <td class="n">&times;1.25 on every euro</td></tr>
    <tr><td><b>How much is the landed-cost basis understating the headroom?</b></td>
      <td>The cost floor rests on the cost implied by the margin. Where that margin is
      generous the headroom is overstated. <b>This one does not need anybody's permission or
      anybody's price list:</b> the method in section 3.3 already holds our own billed cost per
      unit against a competing price, part number by part number, and extending that sample is
      the direct route. It is analysis we can run, not a question for a person.</td>
      <td class="n">the 26 reachable</td></tr>
  </table>

  <div class="call dark" style="margin-top:12px"><div class="h">What this paper does not do</div>
  It changes no price, no list and no published number. No allocation is run. Israel is
  kept as two distributors throughout and the two are never blended. Leakage euro stays
  internal. Every figure carries the window it was measured on, because the pricing work
  has three windows in play and they do not agree.
  <div class="small" style="color:#9fb0cc;margin-top:8px">Internal working paper, revision 2
  &middot; 17 September 2026 &middot; prepared for Jerome Van der Pluym. Not a shared pack.</div></div>
</div></section>

<!-- ============================ 11. CLOSE -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">11 \u00b7 the papers behind this</span><span>revision 2</span></div>
  <h2><span class="sec-n">section eleven</span>What this rests on, and what it must not claim</h2>

  <div class="two">
    <div>
      <h4>The written work</h4>
      <table>
        <tr><th>Document</th><th>What it carries</th></tr>
        <tr><td><b>The policy paper, revision 2</b></td>
          <td>The full argument, 786 lines. Supersedes revision 1, which is kept on disk so the two can be compared. Corrected and added to on 18 September 2026.</td></tr>
        <tr><td><b>Revision 1</b></td>
          <td>The first cut. Retained because revision 2 corrects two of its claims, and both should stay visible.</td></tr>
        <tr><td><b>The external review</b></td>
          <td>795 lines on how other operators price, every figure graded by evidence quality, with an internal source list so any number can be verified.</td></tr>
        <tr><td><b>The classification paper</b></td>
          <td>The product tree, and the audit that found the misfiled families.</td></tr>
      </table>
      <div class="small">Files under 01_data/90_INBOX/ and 02_dashboards/sales/.</div>
    </div>
    <div>
      <h4>The data behind every figure</h4>
      <table>
        <tr><th>Derived file</th><th>What it holds</th></tr>
        <tr><td>price_bp_weighted_compare_pn</td><td>The revision, line by line</td></tr>
        <tr><td>pricing_aim_source_lines</td><td>The book on the AIM spine</td></tr>
        <tr><td>pricing_cost_floor_reach</td><td>Can a margin reach the competitor</td></tr>
        <tr><td>pricing_chain_and_fx</td><td>The channel chain and the rate</td></tr>
        <tr><td>ituk_price_volume_response</td><td>The volume panel, 3,662 parts</td></tr>
        <tr><td>margin_opportunity_top200</td><td>The top 200, graded on competition</td></tr>
        <tr><td>price_collection_worklist</td><td>The 139 to go and price</td></tr>
        <tr><td>oe_bridge_coverage + replenishment_bridge</td><td>The aftermarket price against our own distributor's cost</td></tr>
        <tr><td>eucon_crossref_iam</td><td>The licensed half of the bridge</td></tr>
      </table>
      <div class="small">All under 01_data/00_derived/ except the Eucon cross-reference, which
      sits under 02_dashboards/Data/01_Pricing/_raw/.</div>
    </div>
  </div>

  <h3>What this paper must not claim, and why</h3>
  <div class="two">
    <div class="call amber"><div class="h">Do not claim a volume response to a price change</div>
      There is one serious empirical study of automotive parts demand in the literature,
      and its elasticity table is not obtainable from any accessible copy. Our own panel
      fails for a different reason, shown on page five. The evidence base does not support
      the claim, and two published price cuts that are cited as proof published no outcome
      data at all.</div>
    <div class="call amber"><div class="h">Do not transplant cars into trucks, or quote one margin figure</div>
      The manufacturer holds more of the truck independent channel than the car one, and
      the truck aftermarket is more consolidated. And the genuine-parts margin is a band of
      30% to 50%, from consultancy commentary without a disclosed sample &mdash; a single
      number would be false precision.</div>
  </div>

  <div class="call dark" style="margin-top:12px"><div class="h">What this paper does not do</div>
  It changes no price, no list and no published number. No allocation is run. Israel is
  kept as two distributors throughout and the two are never blended. Leakage euro stays
  internal. Every figure carries the window it was measured on, because the pricing work
  has three windows in play and they do not agree.
  <div class="small" style="color:#9fb0cc;margin-top:8px">Internal working paper, revision 2
  &middot; 17 September 2026 &middot; prepared for Jerome Van der Pluym. Not a shared pack.</div></div>
</div></section>

<script type="application/json" id="payload">{d}</script>
<script>{CHARTJS}</script>
<script>const D=JSON.parse(document.getElementById('payload').textContent);{JS}</script>
</body></html>
"""


say("Writing HTML ...")
os.makedirs(OUT_DIR, exist_ok=True)
page = html()

# ---- hard gate: the page's own script must parse, and every canvas must be unique.
# This is the check that was missing when nine charts shipped blank.
import re as _re
import subprocess as _sp
import tempfile as _tf

_scripts = _re.findall(r"<script>(.*?)</script>", page, _re.S)
_app = _scripts[-1] if _scripts else ""
_ids = _re.findall(r'<canvas id="([^"]+)"', page)
from collections import Counter as _C
_dupes = {k: v for k, v in _C(_ids).items() if v > 1}

with _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as _fh:
    _fh.write(_app)
    _tmp = _fh.name
_chk = _sp.run(["node", "--check", _tmp], capture_output=True, text=True)
os.unlink(_tmp)

say("")
say("PRE-SHIP GATE")
say(f"  app script parses      : {'YES' if _chk.returncode == 0 else 'NO'}")
if _chk.returncode != 0:
    say(_chk.stderr[:900])
say(f"  canvases defined       : {len(_ids)}")
say(f"  charts constructed     : {page.count('new Chart(')}")
say(f"  duplicate canvas ids   : {_dupes if _dupes else 'none'}")
say(f"  'new Chart' vs canvases: {'match' if page.count('new Chart(') == len(_ids) else 'MISMATCH'}")

if _chk.returncode != 0 or _dupes or page.count("new Chart(") != len(_ids):
    say("")
    say("GATE_FAIL - not written. Fix the script or the canvas set.")
    sys.exit(1)

with open(HTML, "w", encoding="utf-8") as fh:
    fh.write(page)
size = os.path.getsize(HTML)
say("")
say(f"  {HTML}")
say(f"  {size:,} bytes ({size/1024/1024:.2f} MB)")

with open(CMD, "w", encoding="ascii", newline="\r\n") as fh:
    fh.write('@echo off\r\nstart "" "%~dp0ISZE_Pricing_Policy_Paper.html"\r\n')
say(f"  {CMD}")
say("BUILD_OK")
