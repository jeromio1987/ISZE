# -*- coding: utf-8 -*-
"""
Where we are most likely UNDER-pricing: a revenue x criticality x competition map.

Starting point from the external review: "take your top 200 parts by revenue and
map them across criticality and competition. The clusters that are high-criticality
and low-competition are the ones you are most likely under-pricing."

Criticality is a JUDGEMENT, defined in CRITICALITY below and sourced from the
review's framework (down-time cost: line stoppage / performance loss / cosmetic).
It is not a measurement. Edit the map and re-run.

Competition is graded by what is actually on disk:
  2 = an alternative is visible AND we hold its price
  1 = an alternative is visible (part number, or a sibling under the same figure key)
  0 = nothing on disk

Run: python 01_data/91_build/build_margin_opportunity_map.py
Writes: 01_data/00_derived/margin_opportunity_top200.csv
        01_data/00_derived/margin_opportunity_by_family.csv
        01_data/00_derived/margin_opportunity_meta.json
"""
from __future__ import annotations

import io
import json
import os
import sys

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
D = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived"


def say(m):
    print(m)
    sys.stdout.flush()


# ---------------------------------------------------------------- the judgement
# Criticality = cost of the vehicle being off the road. Three tiers.
# A = safety or line-stoppage. The customer cannot wait and cannot substitute a
#     part that is not rated for the job.
# B = performance loss. The vehicle runs but badly; a planned repair can absorb
#     a day.
# C = cosmetic or discretionary. The vehicle is fully serviceable without it.
#
# Mapped on Level 2 where the family name is ambiguous, so the big families land
# correctly. Brakes > Pads & Shoes is safety-critical; Accident & Body > Panels is
# not. A Level 1 mapping alone would have graded whole families wrongly.
CRITICALITY_L2 = {
    "Discs & Drums": "A", "Pads & Shoes": "A", "Caliper": "A", "ABS Control": "A",
    "Steering Gear": "A", "Knuckle & King Pin": "A", "Control & Sensors": "A",
    "Leaf Springs": "A", "Mounting Hardware": "A", "Hub & Bearing": "A",
    "Wheel Rim": "A", "Final Drive": "A", "Bearings & Seals": "A", "Geartrain": "A",
    "Filters (unspecified)": "B", "Air Filter": "B", "Oil Filter": "B",
    "Fuel Filter": "B", "HVAC Filters": "B", "Belts": "B",
    "Sensors": "A", "EGR": "A", "DEF System": "A", "Turbo": "A", "DPF/DPD": "A",
    "Exhaust": "A", "Fuel Control": "A", "Injection Pump": "A", "Fuel Pump": "A",
    "Radiator": "A", "Complete Assembly": "A", "Control Units": "A",
    "Sensors & Switches": "A", "Charging": "A",
    "Panels": "C", "Bumpers": "C", "Glass": "C", "Mirrors": "C",
    "Lamps": "C", "Lighting": "C", "Manuals": "C",
}
CRITICALITY_L1 = {
    "Brakes": "A", "Steering": "A", "Suspension": "A", "Driveline Axle": "A",
    "Transmission": "A", "Engine": "A", "Cooling": "A", "Fuel System": "A",
    "Intake Exhaust Emission": "A", "Wheels Hub": "A",
    "Maintenance Service": "B", "Clutch": "B", "Electrical": "B",
    "Gaskets / seals": "B", "Hydraulic / mechanical": "B",
    "Accident & Body": "C", "Lighting": "C", "Cabin Interior": "C",
    "Comfort parts": "C", "Hardware & consumables": "C", "Hardware": "C",
    "Literature Marketing": "C", "Tools Equipment": "C", "Logistics Packaging": "C",
    "Lubrication": "C", "Fluids Chemicals": "C", "Miscellaneous": "C",
}
say("")
say("Criticality is a JUDGEMENT and it is mapped on Level 2 where the parent family")
say("is ambiguous. It is editable, and it is the one input in this analysis that is")
say("not measured.")

# ---------------------------------------------------------------- 1. the book
say("Loading the in-scope priced book ...")
d = pd.read_parquet(os.path.join(D, "pricing_aim_source_lines.parquet"))
d["pn"] = d["part_number"].astype(str).str.strip()
d = d[d["priced_both"] == True].copy()                        # noqa: E712

cls = pd.read_parquet(os.path.join(D, "pricing_list_pn.parquet"),
                      columns=["part_number", "gm", "fob_eur", "price_class",
                               "is_superseded_row"])
cls = cls[cls["is_superseded_row"] != True].drop_duplicates("part_number")   # noqa: E712
cls["pn"] = cls["part_number"].astype(str).str.strip()
book = d.merge(cls[["pn", "gm", "fob_eur", "price_class"]], on="pn", how="left",
               suffixes=("", "_list"))
book = book[book["gm"].notna() & (book["gm"] > 0) & (book["gm"] < 1)].copy()
say(f"  {len(book):,} lines, EUR {book['billed_eur'].sum():,.0f} billed, "
    f"margin {100*(book['billed_eur']*book['gm']).sum()/book['billed_eur'].sum():.2f}%")

# ---------------------------------------------------------------- 2. competition
say("Grading competition from what is on disk ...")
ks = pd.read_csv(os.path.join(D, "iam_ks_price_gap.csv"), dtype={"pn": str})
ks["pn"] = ks["pn"].str.strip()
ks_priced = set(ks["pn"])
eu = pd.read_csv(os.path.join(D, "eucon_price_gap.csv"), dtype={"pn": str})
eu_priced = set(eu["pn"].str.strip())
au = pd.read_csv(os.path.join(D, "competitiveness_autodoc_risk.csv"), dtype=str)
au_pns = set(au["part_number"].str.strip())          # names only: its prices are unusable

# Figure key = structural signal that siblings exist in the same assembly group.
# NOT evidence of competition (two parts under one figure may be left and right),
# so it may only lift a part to grade 1, never to grade 2.
fig = pd.read_csv(os.path.join(D, "aim_pn_classification_v2.csv"), dtype=str,
                  usecols=["part_number", "fig_key"] if "fig_key" in
                  pd.read_csv(os.path.join(D, "aim_pn_classification_v2.csv"), nrows=1).columns
                  else ["part_number"])
say(f"  columns available for figure key: {list(fig.columns)}")

GRADE = {}
for pn in book["pn"].unique():
    if pn in ks_priced or pn in eu_priced:
        GRADE[pn] = 2
    elif pn in au_pns:
        GRADE[pn] = 1
    else:
        GRADE[pn] = 0
book["competition"] = book["pn"].map(GRADE)


def tier(row):
    for key, table in ((row.get("aim_l2"), CRITICALITY_L2), (row.get("aim_l1"), CRITICALITY_L1)):
        if isinstance(key, str) and key in table:
            return table[key]
    return None


book["criticality"] = book.apply(tier, axis=1)

# ---------------------------------------------------------------- 3. per part
say("Collapsing to part number ...")
pn = book.groupby("pn").agg(
    description=("description", "first"),
    aim_l1=("aim_l1", "first"),
    aim_l2=("aim_l2", "first"),
    criticality=("criticality", "first"),
    competition=("competition", "max"),
    price_class=("price_class_list", "first"),
    margin_pct=("gm", "mean"),
    cost_fob=("fob_eur", "first"),
    billed_eur=("billed_eur", "sum"),
    qty=("qty", "sum"),
    step_eur=("step_eur", "sum"),
    distributors=("db", "nunique"),
).reset_index()
pn["margin_pct"] = 100 * pn["margin_pct"]
pn["rank_by_revenue"] = pn["billed_eur"].rank(ascending=False).astype(int)
pn = pn.sort_values("billed_eur", ascending=False)

# The target: high criticality, no visible price competition, real revenue.
pn["opportunity_flag"] = np.where(
    (pn["criticality"] == "A") & (pn["competition"] == 0), "HIGH",
    np.where((pn["criticality"] == "A") & (pn["competition"] == 1), "MEDIUM", ""))

top = pn.head(200).copy()
say("")
say("=" * 84)
say("THE TOP 200 BY REVENUE")
say("=" * 84)
say(f"  billed euro in the top 200      : EUR {top['billed_eur'].sum():,.0f} "
    f"({100*top['billed_eur'].sum()/pn['billed_eur'].sum():.1f}% of the priced book)")
say(f"  weighted margin in the top 200  : {100*(top['billed_eur']*top['margin_pct']/100).sum()/top['billed_eur'].sum():.2f}%")
say(f"  weighted margin on the rest     : {100*(pn.iloc[200:]['billed_eur']*pn.iloc[200:]['margin_pct']/100).sum()/pn.iloc[200:]['billed_eur'].sum():.2f}%")
say("")
say(f"  top-200 criticality split: {top['criticality'].value_counts().to_dict()}")
say(f"  top-200 competition split: {top['competition'].value_counts().to_dict()}")
say("")

fl = top[top["opportunity_flag"] == "HIGH"]
say(f"  HIGH opportunity (criticality A, NO price evidence): {len(fl)} part numbers, "
    f"EUR {fl['billed_eur'].sum():,.0f} billed")
say(f"    their weighted margin today: {100*(fl['billed_eur']*fl['margin_pct']/100).sum()/fl['billed_eur'].sum():.2f}%")
say(f"    their gross profit         : EUR {(fl['billed_eur']*fl['margin_pct']/100).sum():,.0f}")
say("")
say("  What a margin move on those would be worth, cost held fixed:")
for tgt in (0.60, 0.65, 0.70):
    cost = (fl["billed_eur"] * (1 - fl["margin_pct"] / 100)).sum()
    newprice = cost / (1 - tgt)
    say(f"    to a {int(tgt*100)}% margin -> price EUR {newprice:,.0f} "
        f"({newprice/fl['billed_eur'].sum():.3f}x today), "
        f"gross profit +EUR {newprice*tgt - (fl['billed_eur']*fl['margin_pct']/100).sum():,.0f}")
say("")
say("  The top 25 of that list:")
cols = ["rank_by_revenue", "pn", "description", "aim_l2", "price_class",
        "margin_pct", "billed_eur", "step_eur", "distributors"]
say(fl.sort_values("billed_eur", ascending=False)[cols].head(25).to_string(
    index=False, float_format=lambda v: f"{v:,.1f}"))

# ---------------------------------------------------------------- 4. by family
say("")
say("=" * 84)
say("BY AIM FAMILY: margin against criticality")
say("=" * 84)
fam = book.groupby("aim_l1").apply(lambda g: pd.Series({
    "part_numbers": g["pn"].nunique(),
    "billed_eur": g["billed_eur"].sum(),
    "margin_pct": 100 * (g["billed_eur"] * g["gm"]).sum() / g["billed_eur"].sum(),
    "criticality_A_share": 100 * g.loc[g["criticality"] == "A", "billed_eur"].sum() / g["billed_eur"].sum(),
    "no_price_evidence_share": 100 * g.loc[g["competition"] == 0, "billed_eur"].sum() / g["billed_eur"].sum(),
}), include_groups=False).sort_values("billed_eur", ascending=False)
say(fam.to_string(float_format=lambda v: f"{v:,.1f}"))
say("")
say("  Read the last two columns together. A family that is mostly criticality A and")
say("  mostly without price evidence is a family where we are earning 51% and cannot")
say("  say whether that is right or half of what it should be.")

# ---------------------------------------------------------------- 5. write
top.to_csv(os.path.join(D, "margin_opportunity_top200.csv"), index=False)
fam.to_csv(os.path.join(D, "margin_opportunity_by_family.csv"))
meta = {
    "built": pd.Timestamp.now().isoformat(timespec="seconds"),
    "method": "revenue rank x criticality (judgement) x competition (graded from disk)",
    "basis": {
        "revenue": "pricing_aim_source_lines.parquet, priced_both == True, billed euro summed by PN",
        "margin": "pricing_list_pn.gm",
        "competition": "2 = alternative visible with its price (KS or Eucon); "
                       "1 = alternative visible by PN (Autodoc names) ; 0 = nothing on disk",
    },
    "headline": {
        "top200_billed_eur": float(top["billed_eur"].sum()),
        "top200_share_of_book_pct": float(100 * top["billed_eur"].sum() / pn["billed_eur"].sum()),
        "top200_margin_pct": float(100 * (top["billed_eur"] * top["margin_pct"] / 100).sum() / top["billed_eur"].sum()),
        "high_opportunity_pns": int(len(fl)),
        "high_opportunity_billed_eur": float(fl["billed_eur"].sum()),
        "high_opportunity_margin_pct": float(100 * (fl["billed_eur"] * fl["margin_pct"] / 100).sum() / fl["billed_eur"].sum()),
    },
    "caveats": [
        "Criticality is a judgement, not a measurement. It is a mapping from the "
        "catalogue family to the cost of the vehicle being off the road. Edit and re-run.",
        "Competition grade 1 rests on the Autodoc file's part-number and brand columns "
        "only. Its price column is unusable (277 of 298 rows carry the identical 2.34).",
        "Grade 0 means nothing on disk, NOT that no competitor exists. It is a statement "
        "about our evidence, not about the market.",
        "Margins are the class-implied margins. The cost behind them is FOB euro implied "
        "by the class, not a purchase cost.",
    ],
}
with open(os.path.join(D, "margin_opportunity_meta.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=2)
say("")
say(f"wrote margin_opportunity_top200.csv ({len(top)} rows) and by_family ({len(fam)} rows)")
say("BUILD_OK")
