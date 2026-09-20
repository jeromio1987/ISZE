# -*- coding: utf-8 -*-
"""
Builds the visual version of the pricing policy paper, revision 3 (2026-09-19).

Self-contained HTML: Chart.js inlined, data embedded as JSON, opens from a
double-click with no server. Writes a sibling OPEN_*.cmd with CRLF line endings.

This is a NEW builder. It does not edit build_pricing_policy_paper.py, which
continues to build the revision 2 HTML.

Every chart follows the house chart rule: the title is the business question, the
form is chosen from the relationship, and no gap is shown without context.

Run: python 02_dashboards/pricing/_build/build_pricing_policy_paper_rev3.py
Writes: 02_dashboards/pricing/ISZE_Pricing_Policy_Paper_REV3.html
        02_dashboards/pricing/OPEN_ISZE_Pricing_Policy_Paper_REV3.cmd
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
INBOX = os.path.join(ISZE, "01_data", "90_INBOX")
D = os.path.join(ISZE, "01_data", "00_derived")
BUILD = os.path.join(ISZE, "02_dashboards", "pricing", "_build")
OUT_DIR = os.path.join(ISZE, "02_dashboards", "pricing")
HTML = os.path.join(OUT_DIR, "ISZE_Pricing_Policy_Paper_REV3.html")
CMD = os.path.join(OUT_DIR, "OPEN_ISZE_Pricing_Policy_Paper_REV3.cmd")
PAPER_MD = os.path.join(INBOX, "PRICING_POLICY_PAPER_2026-09-19_REV3.md")


def say(m):
    print(m)
    sys.stdout.flush()


def eur(v):
    return "\u20ac" + format(round(v), ",d")


def money(v):
    return "\u20ac" + f"{v/1e6:.2f}M"


# =============================================================== 1. build data
say("Loading today's research files ...")

fig = json.load(open(os.path.join(INBOX, "pricing_system_figures_2026-09-19.json"),
                     encoding="utf-8"))
lines = pd.read_csv(os.path.join(INBOX, "pricing_system_lines_2026-09-19.csv"),
                    dtype={"part_number": str})
spec = json.load(open(os.path.join(BUILD, "_spec_basis_meta.json"), encoding="utf-8"))
cost = json.load(open(os.path.join(D, "pricing_cost_floor_meta.json"), encoding="utf-8"))
rec = json.load(open(os.path.join(D, "aim_pricing_recalc_2026-09-17.json"), encoding="utf-8"))

# ---- the two-tier system: tiers, lines, revenue, price gain -----------------
TIERS = ["SERVICE BASKET (PMS)", "COMMERCIAL", "CAPTIVE / GATED",
         "CLOSING WINDOW", "BODY / LEGAL", "UNCLASSIFIED"]
TIER_LABEL = {
    "SERVICE BASKET (PMS)": "Service basket (PMS)",
    "COMMERCIAL": "Commercial",
    "CAPTIVE / GATED": "Captive / gated",
    "CLOSING WINDOW": "Closing window",
    "BODY / LEGAL": "Body / legal",
    "UNCLASSIFIED": "Unclassified",
}
tier_lines, tier_rev, tier_gain, tier_names = [], [], [], []
for t in TIERS:
    n = int((lines["tier"] == t).sum())
    if not n:
        continue
    tier_names.append(TIER_LABEL[t])
    tier_lines.append(n)
    tier_rev.append(float(lines.loc[lines["tier"] == t, "l12m_revenue_eur"].sum()))
    tier_gain.append(float(lines.loc[lines["tier"] == t, "price_gain_eur_l12m"].sum()))
say(f"  tiers: {len(tier_names)}; lines {sum(tier_lines):,}; revenue "
    f"{eur(sum(tier_rev))}; gain {eur(sum(tier_gain))}")

# ---- the dial: three levels, four markets -----------------------------------
DIAL = fig["dial_scenarios"]
MARKETS = ["PR00", "UTI", "UMI", "CIS"]

# ---- the movement distribution, and the cap breach --------------------------
m = lines[lines["dial_movement_pct"].notna()].copy()
CAP = 8.0
above = m[m["dial_movement_pct"] > CAP]
dist = m["dial_movement_pct"].round(2).value_counts().sort_index()
HIST = [{"bucket": round(float(k), 2), "lines": int(v)}
        for k, v in dist.items()]
CAP_STATS = {
    "priced_lines": int(len(m)),
    "above": int(len(above)),
    "above_pct": round(100 * len(above) / len(m), 1),
    "worst": round(float(m["dial_movement_pct"].max()), 2),
    "by_tier": {TIER_LABEL[t]: int(v) for t, v in
                above["tier"].value_counts().items()},
}
say(f"  cap: {CAP_STATS['above']:,} of {CAP_STATS['priced_lines']:,} lines above "
    f"+{CAP:.0f}% ({CAP_STATS['above_pct']}%), worst {CAP_STATS['worst']}%")

# ---- lighting: the movement at 0.90 against 0.80 ----------------------------
UTI_LIGHT_NODES = ["Headlamp", "Tail / combination lamp", "Marker / signal lamp",
                   "Fog lamp", "Other lighting", "Lens / reflector"]
K = float(fig["normalisation_k"])
DIAL_DEFAULT = float(fig["dial_default"])
light_now = DIAL_DEFAULT * 0.90 / K * 100.0
light_prop = DIAL_DEFAULT * 0.80 / K * 100.0
breakeven = CAP * K / DIAL_DEFAULT
utl = lines[(lines["market"] == "UTI") & (lines["aim_l3"].isin(UTI_LIGHT_NODES))]
light_stats = {
    "lines": int(len(utl)),
    "with_move": int(utl["dial_movement_pct"].notna().sum()),
    "above": int((utl["dial_movement_pct"] > CAP).sum()),
    "now": round(light_now, 2),
    "prop": round(light_prop, 2),
    "breakeven": round(breakeven, 4),
    "revenue": float(utl["l12m_revenue_eur"].sum()),
    "gain_now": round(float((utl["l12m_revenue_exposed_eur"].fillna(0) *
                            DIAL_DEFAULT * 0.90 / K).sum()), 0),
    "gain_prop": round(float((utl["l12m_revenue_exposed_eur"].fillna(0) *
                              DIAL_DEFAULT * 0.80 / K).sum()), 0),
}
say(f"  lighting: {light_stats['with_move']} of {light_stats['lines']} UTI lines carry "
    f"a move; {light_stats['above']} above the ceiling at 0.90; "
    f"{light_stats['now']}% -> {light_stats['prop']}%")

# ---- lamps and collision, measured on UTI ----------------------------------
lc = pd.read_csv(os.path.join(INBOX, "UTI_LIGHTING_COLLISION_MANAGEMENT_20260919.csv"))
lc = lc[lc["has_list_price_row"] == True]                                      # noqa: E712
lamps = []
for fam, label in [("lighting", "Lighting"), ("collision", "Collision & bodywork")]:
    g = lc[lc["family"] == fam]
    rev = float(g["revenue_eur"].sum())
    lamps.append({
        "label": label,
        "revenue": rev,
        "units": float(g["quantity"].sum()),
        "margin": round(float((g["gross_margin"] * g["revenue_eur"]).sum() / rev) * 100, 1),
        "low_class_share": round(float(
            g.loc[g["price_class"] == "F", "revenue_eur"].sum() / rev) * 100, 1),
    })
lamps[0]["share_of_two"] = round(100 * lamps[0]["revenue"] /
                                 (lamps[0]["revenue"] + lamps[1]["revenue"]), 1)
say(f"  lamps: lighting {eur(lamps[0]['revenue'])} at {lamps[0]['margin']}% margin, "
    f"collision {eur(lamps[1]['revenue'])} at {lamps[1]['margin']}%")

# ---- the collision package: old model against P700 -------------------------
PACKAGE = {
    "labels": ["Old model", "P700"],
    "n75": [679.21, 2144.48],
    "f10": [923.66, 2314.14],
    "n75_pct": 215.7,
    "f10_pct": 150.6,
}
LAMPS_ITEM = {
    "labels": ["Head lamp\n(F/10)", "Rear light\n(N/7.5)", "Turn signal\n(F/10)",
               "Signal\n(N/7.5)"],
    "old": [85.93, 30.42, 30.31, 26.57],
    "new": [370.80, 404.09, 131.37, 131.37],
    "pct": [331.6, 1228.0, 333.4, 394.4],
}

# ---- pickup: measured annual distance and the fleet base -------------------
PICKUP = {
    "labels": ["Israel\n(UMI)", "Ireland", "UK (IUK)", "Portugal\n(Imotors)",
               "Europe\nall markets"],
    "km": [34443, 27998, 24481, 22742, 25600],
    "vins": [13611, 426, 29646, 1596, 76208],
    "fleet": {"labels": ["United Kingdom\n(IUK)", "Israel\n(UMI)",
                         "Portugal\n(Imotors)", "Ireland"],
              "units": [47783, 18542, 4733, 1338]},
    "licence": {
        "labels": ["UK", "Ireland", "Portugal", "Israel"],
        "binding": [0, 0, 0, 0],
        "other_burden": ["towing only", "annual commercial test",
                         "tax classification", "insurance write-off rule"],
    },
}

# ---- launch: the 13 functional SCR parts against class ---------------------
scr = pd.read_csv(os.path.join(INBOX, "p700_2p2l_scr_functional_20260919.csv"))
LAUNCH = {
    "parts": int(len(scr)),
    "class_implied": round(float(scr["sp_class_implied"].sum()), 2),
    "current_list": round(float(scr["sp_eur_2026"].sum()), 2),
    "split": round(float(scr["sp_split"].sum()), 2),
    "warranty_load": round(float(scr["sp_warranty_load"].sum()), 2),
    "new_pns": 1132,
    "carryover": 897,
    "with_base_price": 1072,
    "four_lists": 1048,
    "class_c": 922,
    "class_p": 2,
    "competitor_evidence": 1,
}
LAUNCH["gap_pct"] = round(100 * (LAUNCH["current_list"] / LAUNCH["class_implied"] - 1), 2)
LAUNCH["scenarios"] = {
    "class as issued\n(the price they are listed at)": LAUNCH["class_implied"],
    "split (+25%)": LAUNCH["split"],
    "warranty load (+35%)": LAUNCH["warranty_load"],
}
say(f"  launch: {LAUNCH['parts']} SCR parts, class-implied {eur(LAUNCH['class_implied'])} "
    f"vs list {eur(LAUNCH['current_list'])} ({LAUNCH['gap_pct']:+.2f}%)")

# ---- remanufacturing: the filter in the truck warranty book, by market ------
# Aggregated from the measured lines file: every DPF operation row on the CV truck
# book, summed per market. The line counts and euro reconcile to the research
# document's market table exactly (Israel 436 lines / 696,907 euro; UK 119 / 116,272;
# Spain 62 / 57,007; Italy 46 / 50,604; Portugal 24 / 12,182; France 14 / 13,690).
# The median odometers are the research document's published per-market medians --
# the CSV carries a median per operation row, not one per market.
mea = pd.read_csv(os.path.join(INBOX, "REMAN_DPF_MEASURED_LINES_20260919.csv"),
                  dtype=str)
mea["lines_n"] = pd.to_numeric(mea["lines"], errors="coerce")
mea["eur_n"] = pd.to_numeric(mea["parts_eur"], errors="coerce")
truck = mea[(mea["level"] == "DPF operation x market") &
            (mea["book"].astype(str).str.startswith("CV truck"))]
agg = (truck.groupby("market", as_index=False)
       .agg(lines=("lines_n", "sum"), parts_eur=("eur_n", "sum"))
       .sort_values("parts_eur", ascending=False))
_total_lines = int(agg["lines"].sum())
_total_eur = float(agg["parts_eur"].sum())
# the six markets the written paper's table reports; the tail is small and would
# only crowd the chart
agg = agg.head(6)
REMAN_MEDIAN_ODO = {"ISRAEL": 129200, "UK": 103912, "SPAIN": 135429,
                    "ITALY": 108429, "FRANCE": 71242, "PORTUGAL": 66588}
REMAN_MARKETS = {
    "labels": [str(r["market"]).title() for _, r in agg.iterrows()],
    "eur": [round(float(r["parts_eur"]), 0) for _, r in agg.iterrows()],
    "lines": [int(r["lines"]) for _, r in agg.iterrows()],
    "odo": [REMAN_MEDIAN_ODO.get(str(r["market"]).upper(), 0) for _, r in agg.iterrows()],
}
REMAN_CLAIM = {
    "labels": ["UMI LCV", "IUK LCV", "ITUK truck", "UTI truck"],
    "list": [2162, 2162, 1130, 1130],
    "claim": [3777, 2615, 1473, 1874],
    "ratio": [1.75, 1.21, 1.30, 1.66],
}
say(f"  reman: six main markets shown of {_total_lines:,} truck filter lines, "
    f"{eur(_total_eur)} across {len(truck['market'].unique())} markets; "
    f"Israel {eur(REMAN_MARKETS['eur'][0])} on {REMAN_MARKETS['lines'][0]} lines; "
    f"claim-over-list x{min(REMAN_CLAIM['ratio'])}-x{max(REMAN_CLAIM['ratio'])}")
assert REMAN_MARKETS["labels"][0] == "Israel", REMAN_MARKETS["labels"]
assert REMAN_MARKETS["lines"][0] == 436, REMAN_MARKETS["lines"]

# ---- cost floor: bridge, reach, and the aftermarket against our own cost ----
FLOOR = {
    "bridge_pns": 35,
    "below_any": 26, "testable_any": 33,
    "below_all": 24, "testable_all": 33,
    "median_any": 0.66, "median_all": 0.73,
    "reach": {"visible": 41, "unreachable": 12, "thin": 3, "workable": 26,
              "median_to_match": 52, "median_today": 53},
    "cases": [
        {"pn": "8982924331", "db": "IRELAND", "floor": 147.48, "am": 21.96,
         "brand": "BLUE PRINT", "ratio": 0.15},
        {"pn": "8982924321", "db": "IRELAND", "floor": 145.83, "am": 21.90,
         "brand": "BLUE PRINT", "ratio": 0.15},
        {"pn": "8983034680", "db": "ITUK", "floor": 179.90, "am": 28.34,
         "brand": "FRENKIT", "ratio": 0.16},
        {"pn": "8980094180", "db": "GREECE", "floor": 105.02, "am": 17.17,
         "brand": "NTY", "ratio": 0.16},
    ],
}
MARGIN_BY_CLASS = {
    "labels": ["C", "D", "F", "J", "M", "P", "V", "T"],
    "margins": [53.0, 52.0, 47.5, 44.5, 50.0, 56.0, 45.0, 20.0],
    "book_margin": round(cost["headline"]["weighted_gm_pct"], 2),
}
CHAIN = {"steps": ["Our net price\nto distributor", "Distributor\nprice to dealer",
                   "Dealer price\nto customer"],
         "now": [1.09, 1.53, 1.95],
         "at15": [0.58, 0.86, 1.03],
         "mult": 1.785}
COVER = {"with_benchmark": 16.5, "category_median": 4.8, "no_benchmark": 78.8,
         "no_benchmark_eur": 25672208, "lines_priced": int(spec["lines_priced"]),
         "no_benchmark_lines": int(spec["t5_lines"])}

DATA = {
    "cover": {
        "dial_gain": round(sum(tier_gain), 0),
        "tier_lines": int(sum(tier_lines)),
        "tier_revenue": round(sum(tier_rev), 0),
        "service_cut": round(tier_gain[tier_names.index("Service basket (PMS)")], 0),
        "commercial_gain": round(tier_gain[tier_names.index("Commercial")], 0),
        "captive_gain": round(tier_gain[tier_names.index("Captive / gated")], 0),
        "step_eur": spec["step_eur"],
        "weighted_pct": spec["weighted_pct"] * 100,
        "billed_priced": spec["billed_eur_priced"],
        "gm": cost["headline"]["weighted_gm_pct"],
        "gp": cost["headline"]["gross_profit_eur"],
        "dial": DIAL_DEFAULT,
    },
    "tiers": {"names": tier_names, "lines": tier_lines, "revenue": tier_rev,
              "gain": tier_gain},
    "dial": {"markets": MARKETS,
             "p3": [DIAL[mk]["3pct"] for mk in MARKETS],
             "p5": [DIAL[mk]["5pct"] for mk in MARKETS],
             "p7": [DIAL[mk]["7pct"] for mk in MARKETS],
             "totals": [sum(DIAL[mk][f"{p}pct"] for mk in MARKETS) for p in (3, 5, 7)]},
    "hist": HIST,
    "cap": CAP_STATS,
    "light": light_stats,
    "lamps": lamps,
    "package": PACKAGE,
    "lamps_item": LAMPS_ITEM,
    "pickup": PICKUP,
    "launch": LAUNCH,
    "reman_markets": REMAN_MARKETS,
    "reman_claim": REMAN_CLAIM,
    "floor": FLOOR,
    "margin_by_class": MARGIN_BY_CLASS,
    "chain": CHAIN,
    "coverage": COVER,
    "verdict": {
        "gp": cost["headline"]["gross_profit_eur"],
        "setband": "45% to 56%",
        "proposed_rate_pct": light_stats["prop"],
        "cap_above": CAP_STATS["above"],
    },
}
say(f"  data assembled: {len(json.dumps(DATA)):,} bytes JSON")

# =============================================================== 2. template
CHARTJS = open(os.path.join(ISZE, "02_dashboards", "_ui", "chart.umd.min.js"),
               encoding="utf-8", errors="replace").read()
say(f"  chart.js inlined: {len(CHARTJS):,} bytes")

CSS = """
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--line:#e3ded3;
--muted:#6b6256;--good:#1d9e75;--amber:#c48a16;--pale:#eef3f9;--slate:#4a6b96}
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
.cover{background:var(--navy);color:#eef1f6;padding:0;display:flex;flex-direction:column;
min-height:297mm}
.cover .top{padding:15mm 16mm 0}
.cover .kicker{font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#8fa6c4}
.cover h1{color:#fff;font-size:35px;margin:9px 0 0;max-width:172mm}
.rule{width:58mm;height:3px;background:var(--terra);margin:13px 0 15px}
.cover .thesis{font-size:14.5px;color:#cfd9e8;max-width:152mm;line-height:1.5}
.cover .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;padding:0 16mm;
margin-top:auto}
.stat{background:rgba(255,255,255,.07);border-left:3px solid var(--terra);padding:9px 11px;
position:relative;cursor:default}
.stat .l{font-size:8.5px;color:#9fb0cc;text-transform:uppercase;letter-spacing:.5px;line-height:1.3}
.stat .v{font-family:Georgia,serif;font-size:18px;color:#fff;margin-top:2px}
.stat .s{font-size:9.5px;color:#8fa6c4;margin-top:2px;line-height:1.3}
.stat .tip{display:none;position:absolute;left:0;bottom:calc(100% + 7px);width:255px;
background:var(--paper);color:var(--ink);border-top:3px solid var(--terra);padding:9px 11px;
z-index:30;font-size:11px;line-height:1.45;box-shadow:0 8px 22px rgba(0,0,0,.3)}
.stat:hover .tip{display:block}
.cover .foot{padding:10mm 16mm 12mm;font-size:10px;color:#8fa6c4;
display:flex;justify-content:space-between;border-top:1px solid rgba(255,255,255,.13);
margin-top:11mm}
.dials{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;padding:0 16mm;margin-top:13px}
.dl{background:rgba(255,255,255,.05);border-top:2px solid #4a6b96;padding:8px 10px}
.dl.choice{background:rgba(192,85,45,.16);border-top:2px solid var(--terra)}
.dl .l{font-size:8px;color:#9fb0cc;text-transform:uppercase;letter-spacing:.4px;line-height:1.3}
.dl.choice .l{color:#e7b9a4}
.dl .v{font-family:Georgia,serif;font-size:16px;color:#fff;margin-top:2px}
.dl .s{font-size:9px;color:#8fa6c4;margin-top:2px;line-height:1.3}
.dlnote{padding:8mm 16mm 0;font-size:9.5px;color:#a9bad4;line-height:1.45}
.dlnote b{color:#fff}
.assume{background:var(--pale);border-top:3px solid var(--terra);padding:9px 12px;margin:10px 0 13px}
.assume .h{font-family:Georgia,serif;font-size:12.5px;color:var(--navy);margin-bottom:4px}
.assume table{margin:7px 0 4px}
.defect{background:#fdf1ec;border:1px solid #e8c4b4;border-left:4px solid var(--terra);
padding:11px 14px;margin:11px 0 13px;border-radius:0 4px 4px 0}
.defect .h{font-family:Georgia,serif;font-size:13.5px;color:var(--terra);margin-bottom:5px;
text-transform:uppercase;letter-spacing:.05em}
.two-tier{display:grid;grid-template-columns:1fr 1fr;gap:11px;margin:9px 0 11px}
.tierbox{background:#fff;border:1px solid var(--line);border-left:3px solid var(--navy);padding:9px 11px}
.tierbox.choice{border-left-color:var(--terra);background:#fdf7f4}
.tierbox .t{font-family:Georgia,serif;font-size:12px;color:var(--navy);margin-bottom:4px}
.tierbox .big{font-family:Georgia,serif;font-size:19px;color:var(--terra);margin:2px 0 3px}
.tierbox .s{font-size:10px;color:#444;line-height:1.4}
.verdict{background:var(--paper);border-left:4px solid var(--terra);padding:12px 15px;margin:0 0 14px}
.verdict .t{font-family:Georgia,serif;font-size:15px;color:var(--navy);line-height:1.4}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0 14px}
.kpi{background:var(--pale);border-top:3px solid var(--navy);padding:9px 10px;position:relative;
cursor:default}
.kpi .l{font-size:8.5px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);line-height:1.3}
.kpi .v{font-family:Georgia,serif;font-size:18px;color:var(--navy);margin-top:2px}
.kpi .s{font-size:9.5px;color:var(--muted);margin-top:2px}
.kpi:hover .tip{display:block}
.kpi .tip{display:none;position:absolute;left:0;top:calc(100% + 6px);width:268px;background:var(--navy);
color:var(--paper);border-top:3px solid var(--terra);padding:9px 11px;z-index:30;font-size:11px;
line-height:1.45;box-shadow:0 8px 22px rgba(0,0,0,.28)}
.cb{background:#fff;border:1px solid var(--line);border-radius:5px;padding:11px 13px 9px;
margin:11px 0 13px;page-break-inside:avoid}
.cb .q{font-family:Georgia,serif;font-size:12.5px;color:var(--navy);font-weight:600;margin-bottom:2px}
.cb .sub{font-size:10.5px;color:var(--muted);margin-bottom:9px;line-height:1.4}
.hold{position:relative;height:300px}
.hold.tall{height:360px}
.hold.xtall{height:420px}
.hold.big{height:480px}
.call{border-left:3px solid var(--terra);background:#fff;padding:9px 13px;margin:10px 0;
border-radius:0 4px 4px 0}
.call.good{border-left-color:var(--good);background:#f2faf6}
.call.amber{border-left-color:var(--amber);background:#fdf6e8}
.call.dark{background:var(--navy);color:var(--paper);border-left-color:var(--terra)}
.call.dark b{color:#fff}
.call .h{font-family:Georgia,serif;font-size:13px;color:var(--navy);margin-bottom:3px}
.call.dark .h{color:#fff}
table{width:100%;border-collapse:collapse;font-size:10.5px;margin:8px 0 11px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:6px 8px;font-weight:600;
font-size:9.5px;letter-spacing:.04em;text-transform:uppercase}
td{padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}
tr:nth-child(even) td{background:#faf9f6}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr.hi td{background:#fdf1ec;font-weight:600}
.stack{display:flex;height:34px;border-radius:3px;overflow:hidden;margin:9px 0 5px}
.stack div{display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;
font-weight:600}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:10px;color:var(--muted);margin-bottom:5px}
.legend span{display:flex;align-items:center;gap:5px}
.dot{width:9px;height:9px;border-radius:2px;display:inline-block}
.two{display:grid;grid-template-columns:1fr 1fr;gap:13px}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:11px}
.mini{background:var(--paper);padding:10px 12px;border-left:3px solid var(--navy)}
.mini .v{font-family:Georgia,serif;font-size:19px;color:var(--navy)}
.mini .l{font-size:9.5px;text-transform:uppercase;letter-spacing:.4em;color:var(--muted)}
.mini .s{font-size:10.5px;color:#444;margin-top:4px;line-height:1.4}
ul{margin:4px 0 9px 17px;padding:0}li{margin-bottom:4px}
.grade{display:inline-block;font-size:8px;letter-spacing:.06em;padding:1px 5px;border-radius:2px;
font-weight:700;text-transform:uppercase;vertical-align:1px;border:1px solid transparent}
.g-m{background:#e8f5ef;color:#146b4f;border-color:#bfe3d3}
.g-t{background:#fdf3e2;color:#8a6212;border-color:#e9d3a7}
.g-i{background:#eef3f9;color:#33507a;border-color:#c8d8ea}
.g-n{background:#eceae5;color:#5d5548;border-color:#d5d0c6}
.g-r{background:#fdeee8;color:#9c3a17;border-color:#eec4b3}
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
const axEUR=v=>Math.abs(v)>=1e6?'\\u20AC'+(v/1e6).toFixed(1)+'M':
  (Math.abs(v)>=1e3?'\\u20AC'+Math.round(v/1e3)+'k':'\\u20AC'+v);

/* T1 - what each tier carries, revenue against the movement it takes */
new Chart($('#c-tiers'),{type:'bar',
 data:{labels:D.tiers.names,datasets:[
  {label:'revenue it carries, L12M',data:D.tiers.revenue,backgroundColor:C.navy,
   borderRadius:2,yAxisID:'y',barPercentage:.7},
  {type:'line',label:'price gained at the 5% dial',data:D.tiers.gain,borderColor:C.terra,
   backgroundColor:C.terra,borderWidth:2.4,tension:.2,pointRadius:5,yAxisID:'y1'}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>c.datasetIndex===0
     ? ' carries '+eur(c.parsed.y)+' of revenue, on '+D.tiers.lines[c.dataIndex].toLocaleString()+' lines'
     : ' price gained '+eur(c.parsed.y)}}},
  scales:{x:{ticks:{font:{size:9.5},maxRotation:32,minRotation:32},grid:{display:false}},
   y:{title:{display:true,text:'L12M revenue it carries',font:{size:10.5}},
    ticks:{callback:axEUR,maxTicksLimit:5},grid:{color:'#eceae4'}},
   y1:{position:'right',title:{display:true,text:'price gained at the 5% dial',font:{size:10.5}},
    ticks:{callback:v=>'\\u20AC'+Math.round(v/1000)+'k',maxTicksLimit:5},grid:{display:false}}}}}); 

/* T2 - the dial: three levels across four markets */
new Chart($('#c-dial'),{type:'bar',
 data:{labels:D.dial.markets,datasets:[
  {label:'3% dial',data:D.dial.p3,backgroundColor:C.slate,borderRadius:2,barPercentage:.8},
  {label:'5% dial (placeholder)',data:D.dial.p5,backgroundColor:C.navy,borderRadius:2,
   barPercentage:.8},
  {label:'7% dial',data:D.dial.p7,backgroundColor:C.terra,borderRadius:2,barPercentage:.8}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+eur(c.parsed.y)}}},
  scales:{y:{title:{display:true,text:'price gain, EUR',font:{size:10.5}},
    ticks:{callback:axEUR,maxTicksLimit:5},grid:{color:'#eceae4'}},
   x:{grid:{display:false}}}}}); 

/* T3 - the movement distribution, and where the engine's own ceiling sits */
new Chart($('#c-hist'),{type:'bar',
 data:{labels:D.hist.map(h=>h.bucket.toFixed(2)+'%'),datasets:[
  {label:'priced lines',data:D.hist.map(h=>h.lines),
   backgroundColor:D.hist.map(h=>h.bucket>8?C.terra:C.navy),borderRadius:1,barPercentage:.95}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>' '+c.parsed.y.toLocaleString()+' lines move '+
     D.hist[c.dataIndex].bucket.toFixed(2)+'%'+
     (D.hist[c.dataIndex].bucket>8?' \\u2014 above the engine\\u2019s own +8% ceiling':'')}}},
  scales:{x:{title:{display:true,text:'applied movement on the line, %',font:{size:10.5}},
    ticks:{maxTicksLimit:12,font:{size:9}},grid:{display:false}},
   y:{title:{display:true,text:'priced lines',font:{size:10.5}},
    ticks:{callback:v=>fmtN(v),maxTicksLimit:5},grid:{color:'#eceae4'}}}}}); 

/* T4 - lighting: where 0.90 lands against 0.80, and the ceiling between them */
new Chart($('#c-light'),{type:'bar',
 data:{labels:['Today\\n0.90','Proposed\\n0.80'],datasets:[
  {label:'applied increase on a UTI lighting line at a 5% dial',data:[D.light.now,D.light.prop],
   backgroundColor:[C.terra,C.good],borderRadius:3,barPercentage:.5},
  {type:'line',label:'the +8% per-line ceiling the engine sets',data:[8,8],
   borderColor:C.navy,borderDash:[6,4],borderWidth:1.8,pointRadius:0,fill:false}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>c.datasetIndex===0
     ? ' '+c.parsed.y.toFixed(2)+'% on every lighting line'
     : ' ceiling 8.00%'}}},
  scales:{y:{beginAtZero:true,max:9.2,title:{display:true,text:'applied increase, %',font:{size:10.5}},
    grid:{color:'#eceae4'}},x:{grid:{display:false}}}}}); 

/* T5 - lamps against collision, on UTI */
new Chart($('#c-lamps'),{data:{labels:D.lamps.map(l=>l.label),datasets:[
  {type:'bar',label:'revenue, L12M',data:D.lamps.map(l=>l.revenue),backgroundColor:C.navy,
   borderRadius:2,yAxisID:'y',barPercentage:.55},
  {type:'bar',label:'weighted margin %',data:D.lamps.map(l=>l.margin),backgroundColor:C.slate,
   borderRadius:2,yAxisID:'y1',barPercentage:.55},
  {type:'bar',label:'share of revenue in the lowest-margin class we publish',
   data:D.lamps.map(l=>l.low_class_share),backgroundColor:C.terra,borderRadius:2,
   yAxisID:'y1',barPercentage:.55}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>c.datasetIndex===0
     ? ' '+eur(c.parsed.y)
     : ' '+c.parsed.y.toFixed(1)+'%'}}},
  scales:{y:{title:{display:true,text:'revenue, EUR',font:{size:10.5}},
    ticks:{callback:axEUR,maxTicksLimit:5},grid:{color:'#eceae4'}},
   y1:{position:'right',beginAtZero:true,max:100,
    title:{display:true,text:'%',font:{size:10.5}},grid:{display:false},ticks:{maxTicksLimit:5}},
   x:{grid:{display:false}}}}}); 

/* T6 - the lamp items in UTI's own deck, old model against P700 */
new Chart($('#c-lampitems'),{type:'bar',
 data:{labels:D.lamps_item.labels,datasets:[
  {label:'old model',data:D.lamps_item.old,backgroundColor:C.muted,borderRadius:2,barPercentage:.7},
  {label:'P700',data:D.lamps_item.new,backgroundColor:C.terra,borderRadius:2,barPercentage:.7}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>' '+c.dataset.label+': \\u20AC'+c.parsed.y.toFixed(2)+
     (c.datasetIndex===1?'  (+'+D.lamps_item.pct[c.dataIndex].toFixed(0)+'%)':'')}}},
  scales:{y:{title:{display:true,text:'list price, EUR',font:{size:10.5}},
    grid:{color:'#eceae4'}},x:{grid:{display:false},ticks:{font:{size:9.5}}}}}}); 

/* T7 - the pickup buyer is not licensed anywhere */
new Chart($('#c-pickup'),{data:{labels:D.pickup.fleet.labels,datasets:[
  {type:'bar',label:'pickup / light commercial fleet in service',
   data:D.pickup.fleet.units,backgroundColor:C.navy,borderRadius:2,yAxisID:'y',barPercentage:.55},
  {type:'line',label:'measured annual distance, km',data:D.pickup.km.slice(0,4),
   borderColor:C.terra,backgroundColor:C.terra,borderWidth:2.4,tension:.2,pointRadius:5,
   yAxisID:'y1'}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>c.datasetIndex===0
     ? ' '+fmtN(c.parsed.y)+' vehicles \\u2014 our own estimate, not actual'
     : ' '+fmtN(c.parsed.y)+' km a year, measured'}}},
  scales:{y:{title:{display:true,text:'fleet in service (estimated)',font:{size:10.5}},
    ticks:{callback:v=>fmtN(v),maxTicksLimit:5},grid:{color:'#eceae4'}},
   y1:{position:'right',title:{display:true,text:'measured km a year',font:{size:10.5}},
    ticks:{callback:v=>fmtN(v),maxTicksLimit:5},grid:{display:false}},
   x:{grid:{display:false},ticks:{font:{size:9.5}}}}}}); 

/* T8 - the launch parts are priced at class and no higher */
new Chart($('#c-launch'),{type:'bar',
 data:{labels:Object.keys(D.launch.scenarios),datasets:[
  {label:'price book for the 13 functional SCR / AdBlue parts',
   data:Object.values(D.launch.scenarios),
   backgroundColor:[C.navy,C.slate,C.terra],borderRadius:2,barPercentage:.6}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>{const b=c.parsed.y;const base=D.launch.class_implied;
     return ' '+eur(b)+'  ('+(b===base?'the price they are listed at today':
       '+'+(100*(b/base-1)).toFixed(0)+'% over class-implied')+')';}}}},
  scales:{y:{title:{display:true,text:'sum of unit prices, EUR (not a revenue forecast)',
    font:{size:10.5}},ticks:{callback:axEUR,maxTicksLimit:5},grid:{color:'#eceae4'}},
   x:{grid:{display:false},ticks:{font:{size:9.5}}}}}}); 

/* T9 - the filter in the warranty book, by market */
new Chart($('#c-reman'),{data:{labels:D.reman_markets.labels,datasets:[
  {type:'bar',label:'filter parts cost in the truck warranty book',
   data:D.reman_markets.eur,backgroundColor:C.navy,borderRadius:2,yAxisID:'y',barPercentage:.55},
  {type:'line',label:'median odometer at the claim',data:D.reman_markets.odo,
   borderColor:C.terra,backgroundColor:C.terra,borderWidth:2.4,tension:.2,pointRadius:5,
   yAxisID:'y1'}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>c.datasetIndex===0
     ? ' '+eur(c.parsed.y)+' across '+D.reman_markets.lines[c.dataIndex]+' lines'
     : ' median '+fmtN(c.parsed.y)+' km at the claim'}}},
  scales:{y:{title:{display:true,text:'warranty parts cost, EUR',font:{size:10.5}},
    ticks:{callback:axEUR,maxTicksLimit:5},grid:{color:'#eceae4'}},
   y1:{position:'right',title:{display:true,text:'median odometer, km',font:{size:10.5}},
    ticks:{callback:v=>fmtN(v),maxTicksLimit:5},grid:{display:false}},
   x:{grid:{display:false},ticks:{font:{size:9.5}}}}}}); 

/* T10 - what we pay under warranty against our own list */
new Chart($('#c-claim'),{type:'bar',
 data:{labels:D.reman_claim.labels,datasets:[
  {label:'our own 2026 list price',data:D.reman_claim.list,backgroundColor:C.navy,
   borderRadius:2,barPercentage:.62},
  {label:'what the claim costs per unit',data:D.reman_claim.claim,backgroundColor:C.terra,
   borderRadius:2,barPercentage:.62}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>' '+c.dataset.label+': \\u20AC'+fmtN(c.parsed.y)+
     (c.datasetIndex===1?'  (\\u00d7'+D.reman_claim.ratio[c.dataIndex].toFixed(2)+' list)':'')}}},
  scales:{y:{title:{display:true,text:'EUR per unit',font:{size:10.5}},
    ticks:{callback:v=>'\\u20AC'+fmtN(v),maxTicksLimit:5},grid:{color:'#eceae4'}},
   x:{grid:{display:false},ticks:{font:{size:9.5}}}}}}); 

/* T11 - the aftermarket against our own distributor's cost */
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
         '\\u00d7 our distributor cost';}}}},
  scales:{y:{beginAtZero:true,title:{display:true,text:'EUR per unit',font:{size:10.5}},
    grid:{color:'#eceae4'}},x:{grid:{display:false},ticks:{font:{size:9.5}}}}}}); 

/* T12 - the margin is a lookup, not a decision */
new Chart($('#c-margin'),{type:'bar',
 data:{labels:D.margin_by_class.labels,datasets:[
  {label:'margin the class letter sets',data:D.margin_by_class.margins,
   backgroundColor:D.margin_by_class.labels.map(l=>l==='T'?C.amber:C.navy),
   borderRadius:2,barPercentage:.68}]},
 options:{indexAxis:'y',maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>' class '+c.label+': '+c.parsed.x.toFixed(1)+'% margin'}}},
  scales:{x:{beginAtZero:true,max:62,title:{display:true,text:'gross margin %',font:{size:10.5}},
    grid:{color:'#eceae4'}},y:{grid:{display:false}}}}}); 

/* T13 - what the customer actually faces */
new Chart($('#c-chain'),{type:'bar',
 data:{labels:D.chain.steps,datasets:[
  {label:'today, our margin about 51%',data:D.chain.now,backgroundColor:C.navy,
   borderRadius:3,barPercentage:.6},
  {label:'if we cut our margin to 15%',data:D.chain.at15,backgroundColor:C.terra,
   borderRadius:3,barPercentage:.6}]},
 options:{maintainAspectRatio:false,
  plugins:{legend:{labels:{boxWidth:11,font:{size:10.5}}},
   tooltip:{callbacks:{label:c=>' '+c.dataset.label+': '+c.parsed.y.toFixed(2)+
     '\\u00d7 the competing retail price'}}},
  scales:{y:{beginAtZero:true,max:2.1,
    title:{display:true,text:'\\u00d7 the competing retail price',font:{size:10.5}},
    grid:{color:'#eceae4'}},x:{grid:{display:false}}}}}); 

/* T14 - what the two-tier system moves, at a glance */
new Chart($('#c-moves'),{type:'bar',
 data:{labels:D.tiers.names,datasets:[
  {label:'price gained (positive = increase, negative = cut) at the 5% dial',
   data:D.tiers.gain,
   backgroundColor:D.tiers.gain.map(v=>v<0?C.good:C.terra),borderRadius:2,barPercentage:.6}]},
 options:{indexAxis:'y',maintainAspectRatio:false,
  plugins:{legend:{display:false},
   tooltip:{callbacks:{label:c=>{const i=c.dataIndex;
     return ' '+eur(c.parsed.x)+' on '+D.tiers.lines[i].toLocaleString()+' lines, '+
       eur(D.tiers.revenue[i])+' of revenue'}}}},
  scales:{x:{title:{display:true,text:'movement at the 5% dial, EUR',font:{size:10.5}},
    ticks:{callback:axEUR,maxTicksLimit:5},grid:{color:'#eceae4'}},
   y:{grid:{display:false},ticks:{font:{size:9.5}},afterFit:s=>{s.width=118}}}}});
"""


def html() -> str:
    d = json.dumps(DATA)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE \u2014 A parts pricing policy, revision 3</title>
<style>{CSS}</style></head><body>

<!-- ============================ COVER -->
<section class="page cover">
  <div class="top">
    <div class="kicker">Isuzu Europe \u00b7 Aftersales analytics \u00b7 internal</div>
    <h1>A parts pricing policy<br>for ISZE</h1>
    <div class="rule"></div>
    <div class="thesis">What we should charge, on what basis, what has to be true before we can
    say it &mdash; and what we propose to move. Revision 3 folds today's work on the two-tier
    system, the insurance write-off mechanism, the pickup markets, the launch list and the
    refurbishment trade into one paper.</div>
  </div>
  <div class="stats">
    <div class="stat"><div class="l">Service basket moves down</div>
      <div class="v">{eur(DATA['cover']['service_cut'])}</div>
      <div class="s">816 lines on {eur(3332334)} of revenue</div>
      <div class="tip">The 14 service categories a customer pays for at every service, priced
      competitive and cut. This is the tier where a price move is felt most often, so it is
      defended for turnover rather than for margin. At the 5% placeholder dial.</div></div>
    <div class="stat"><div class="l">Commercial tier carries</div>
      <div class="v">+{eur(DATA['cover']['commercial_gain'])}</div>
      <div class="s">10,698 lines, 53.8% of the book</div>
      <div class="tip">An independent alternative is freely available at a comparable price on
      these lines, so the rate is damped below the average. This tier was called CONTESTED in
      earlier work and was renamed COMMERCIAL on 19 September 2026.</div></div>
    <div class="stat"><div class="l">Available to give away</div>
      <div class="v">1 pt</div>
      <div class="s">median, on the parts we can see</div>
      <div class="tip">On 41 part numbers with an observed competing price, the median margin
      needed to match that price is 52% and the median margin held today is 53%. Our reference
      dealer price sits at 1.64&times; the competing retail price.</div></div>
    <div class="stat"><div class="l">The book we can price</div>
      <div class="v">16.5%</div>
      <div class="s">of the priced euro, on real external evidence</div>
      <div class="tip">880 lines carrying 5,369,216 euro have a same-shop or Eucon benchmark.
      That is 16.5% of the priced book by euro value, and 1.8% of the 47,617 priced lines.</div></div>
  </div>

  <div class="dials">
    <div class="dl"><div class="l">Our book margin</div>
      <div class="v">{DATA['cover']['gm']:.2f}%</div>
      <div class="s">measured, on the priced book</div></div>
    <div class="dl"><div class="l">Billed, in scope</div>
      <div class="v">{money(DATA['cover']['billed_priced'])}</div>
      <div class="s">32,595,853 euro priced on both sides</div></div>
    <div class="dl"><div class="l">The step already filed</div>
      <div class="v">{money(DATA['cover']['step_eur'])}</div>
      <div class="s">at +{DATA['cover']['weighted_pct']:.4f}% weighted</div></div>
    <div class="dl choice"><div class="l">The dial &mdash; a placeholder</div>
      <div class="v">{DATA['cover']['dial']*100:.0f}%</div>
      <div class="s">management sets this. All levels are choices.</div></div>
  </div>
  <div class="dlnote">At the 5% dial the four markets yield <b>{eur(DATA['dial']['totals'][1])}</b>
  &mdash; and the whole system re-derives from that one number. <b>The dial is a placeholder, and
  four of the seven tier multipliers are judgment rather than measurement.</b> The three top dials
  are measured on the priced book. The fourth is a choice, and this paper says so wherever it
  appears. <b>No price has been moved, issued or published.</b></div>

  <div class="foot"><span>Revision 3 &middot; 19 September 2026 &middot; supersedes revision 2 of 17 September</span>
    <span>shared / external</span></div>
</section>

<!-- ============================ 1. VERDICT -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">1 &middot; the verdict</span><span>A parts pricing policy for ISZE</span></div>

  <div class="verdict"><div class="t">We should move from one annual percentage applied to the
  whole book to a priced policy that changes different parts by different amounts &mdash; and that
  policy is now built, measured and costed, not described. It puts a service basket of 816 lines
  down by {eur(DATA['cover']['service_cut'])} and takes {eur(DATA['cover']['commercial_gain'])}
  from a commercial tier of 10,698 lines, at a dial management sets.</div></div>

  <p class="lede">The reason is not that the current method is badly executed. It is that the
  method answers a question we have stopped asking. A single weighted percentage is right if the
  objective is &ldquo;raise the book by X&rdquo;. It is wrong if the objective is &ldquo;charge
  what each part is worth, given who is actually competing for it&rdquo;. Those parts of the book
  behave in opposite directions and one number cannot be right for both.</p>

  <div class="kpis">
    <div class="kpi"><div class="l">Margin is a lookup</div><div class="v">{DATA['cover']['gm']:.2f}%</div>
      <div class="s">on every part, from one letter</div>
      <div class="tip">The list price is built as cost divided by a divisor, and the divisor is
      one minus the intended margin. So the margin is set in advance by the class letter on the
      part. Class C means 53.0%, class V means 45.0%. Nothing about the market or the competitor
      enters it, and 84.3% of the priced book earns inside the one band.</div></div>
    <div class="kpi"><div class="l">Cannot be reached by margin</div><div class="v">12 of 41</div>
      <div class="s">our cost is above their retail</div>
      <div class="tip">On these part numbers our landed cost already exceeds the competing retail
      price, so no margin target reaches it. On 26 of the 33 bridged part numbers the aftermarket
      price is below our own distributor's cost. That is a sourcing question, not a pricing one.</div></div>
    <div class="kpi"><div class="l">Lamps: increase cut to</div>
      <div class="v">{DATA['light']['prop']:.2f}%</div>
      <div class="s">from {DATA['light']['now']:.2f}%, to clear the engine's own ceiling</div>
      <div class="tip">At a 5% dial, lighting's current share puts every lamp line at 8.07%, above
      the +8% per-line ceiling the price engine itself sets. Moving the share from 0.90 to 0.80
      lands at 7.17%. The break-even share is 0.8921. This is the one rate in the system that
      follows from a mechanical constraint rather than a preference.</div></div>
    <div class="kpi"><div class="l">Lines above that ceiling</div>
      <div class="v">{DATA['cap']['above']:,}</div>
      <div class="s">of {DATA['cap']['priced_lines']:,} priced, worst {DATA['cap']['worst']}%</div>
      <div class="tip">The system does not enforce its own +8% per-line ceiling. This is a defect
      in the system as built, stated plainly on page 12 rather than hidden. Whether the system
      should respect the cap or the cap should be revised is a decision for management.</div></div>
  </div>

  <div class="two">
    <div class="cb"><div class="q">What does the two-tier system actually move?</div>
      <div class="sub">Each tier's movement at the 5% dial. Terracotta carries the increase,
      green gives it back.</div>
      <div class="hold tall"><canvas id="c-moves"></canvas></div>
      <div class="small" style="margin-top:6px">The service basket is 16.5% of the revenue and
      comes down. The commercial tier is 53.8% and takes the bulk of the increase. The captive
      tier is 3.3% and carries the steepest rate, because that is the only tier where a customer
      cannot answer a price move by buying something else.</div></div>
    <div class="cb"><div class="q">Is the increase landing inside the engine's own ceiling?</div>
      <div class="sub">Every priced line by the movement it carries. Terracotta is
      <b>above</b> the +8% ceiling the price engine itself sets.</div>
      <div class="hold tall"><canvas id="c-hist"></canvas></div>
      <div class="small" style="margin-top:6px"><b>{DATA['cap']['above']:,} lines
      ({DATA['cap']['above_pct']}%) sit above the ceiling, the worst at
      {DATA['cap']['worst']}%.</b> Most are Body / legal lines at a 0.90 share and Captive /
      gated lines at 1.60, combined with the per-market normalisation. See page 12.</div></div>
  </div>
</div></section>

<!-- ============================ 2. WHAT CHANGED -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">2 &middot; what changed in revision 3</span><span>19 September 2026</span></div>
  <h2><span class="sec-n">section two</span>Five pieces of work, folded into one paper</h2>

  <p class="lede">Revision 3 extends revision 2 rather than replacing it. Where today's work changes
  a conclusion, the change is stated in place on the page that carries it.</p>

  <table>
    <tr><th>Revision 2 said</th><th>Revision 3 says</th><th>Where</th></tr>
    <tr><td>Move from one flat percentage to a policy that changes different parts by different
      amounts &mdash; described as a design intention</td>
      <td>The policy is <b>built and measured</b>: six tiers on a single management dial, carrying
      {eur(DATA['cover']['tier_revenue'])} of last-twelve-months revenue across
      {DATA['cover']['tier_lines']:,} lines</td><td>section 3</td></tr>
    <tr><td>Collision and bodywork parts were one family carrying one rate</td>
      <td><b>Lighting is separated from bodywork and cut from 0.90 to 0.80</b>, because 0.90 puts
      every lighting line above the engine's own ceiling. The Israeli insurance mechanism that
      makes this necessary is set out in full</td><td>section 4</td></tr>
    <tr><td>The pickup sat in the light commercial channel, unexamined as a pricing market</td>
      <td><b>The UK operator's licence does not bind the D-Max buyer</b> &mdash; twice over.
      Ireland, not the UK, carries the real compliance burden. Portugal sells the pickup as a tax
      instrument</td><td>section 6</td></tr>
    <tr><td>New part numbers were a pricing wedge because they had no prior price to compare
      against</td>
      <td><b>That premise was wrong for roughly twelve parts in thirteen.</b> 1,048 of the 1,132
      new numbers carry four consecutive published prices. The wedge is the <b>zero index
      weight</b>, not the absence of a reference price</td><td>section 7</td></tr>
    <tr><td>The competitive set in a wear family was the independent brand</td>
      <td><b>A third price level exists below the independent brands</b> &mdash; remanufactured
      and refurbished units &mdash; and in Israel the law explicitly permits the refurbishment
      trade. The D-Max particulate filter is the most exposed single part in the portfolio</td>
      <td>section 8</td></tr>
    <tr class="hi"><td>The policy described a method</td>
      <td>The policy <b>states the proposed movements</b>, each with its reason, and
      <b>discloses a defect in the system as built</b>: it does not enforce its own +8% per-line
      cap, and {DATA['cap']['above']:,} of {DATA['cap']['priced_lines']:,} priced lines sit above
      it</td><td>sections 10 and 11</td></tr>
  </table>

  <div class="call amber"><div class="h">Two things did not change, and they come first</div>
  The verdict is the same: price by tier rather than by one annual percentage. And the honesty
  requirement is stronger than in revision 2, because this version goes to someone else to check.
  <b>Every factual claim carries a source, every claim carries a grade, and no number is invented
  anywhere.</b> Where a figure is a judgment, the line says so.</div>

  <h3>How to read the grades in this paper</h3>
  <table>
    <tr><th>Grade</th><th>What it means</th></tr>
    <tr><td><span class="grade g-m">measured</span></td><td>Read out of a primary source &mdash;
      legislation, a regulator, a named study, or our own file with a path. It can be checked.</td></tr>
    <tr><td><span class="grade g-t">trade</span></td><td>Trade press, an industry body, or a
      supplier's published commercial material.</td></tr>
    <tr><td><span class="grade g-i">inference</span></td><td>Our reasoning from the facts above,
      not a measurement.</td></tr>
    <tr><td><span class="grade g-n">not found</span></td><td>We looked and could not establish it.
      Carried as a gap, not dropped.</td></tr>
    <tr class="hi"><td><span class="grade g-r">reported &mdash; not verified</span></td>
      <td>Legal or internet research carried from another document that this paper did
      <b>not</b> independently re-open. Reported because it matters to the decision, and labelled
      because it has not been re-checked here.</td></tr>
  </table>
</div></section>

<!-- ============================ 3. THE TWO-TIER SYSTEM -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">3 &middot; the pricing system</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section three</span>One dial, six tiers, and the service basket comes down</h2>

  <p class="lede">There is one dial: the overall increase against today's prices. <b>Management sets
  it.</b> Everything else is a distribution rule that responds to it, so setting it to 3% or 7%
  re-derives every line. The corporate exchange rate is applied, not chosen; it is not a dial.</p>

  <div class="cb"><div class="q">What does each tier carry, and what does it take?</div>
    <div class="sub">Navy bars are the last-twelve-months revenue the tier carries. The terracotta
    line is the price movement it takes at the 5% dial, positive up and negative down.</div>
    <div class="hold xtall"><canvas id="c-tiers"></canvas></div>
    <div class="small" style="margin-top:6px"><b>A flat increase would have put the same
    percentage on an oil filter as on a software-coded control unit.</b> That is what this system
    exists to stop, and the line list shows it is now stopped.</div></div>

  <div class="cb"><div class="q">What does the dial do at 3%, 5% and 7%?</div>
    <div class="sub">The price gain by market at each level. The 5% shown here is a placeholder
    until management sets the real one.</div>
    <div class="hold"><canvas id="c-dial"></canvas></div>
    <div class="small" style="margin-top:6px">The market figures differ from a clean 5% each
    because the mix of tiers differs by market: UTI carries an unusually large filter basket and
    CIS almost none, so the same rule produces a different total in each. <b>UTI and UMI are two
    separate distributors and are never blended</b>, here or anywhere else in this paper.</div></div>

  <div class="two-tier">
    <div class="tierbox"><div class="t">The basket that comes down</div>
      <div class="big">&#8722;{eur(abs(DATA['cover']['service_cut']))}</div>
      <div class="s">816 lines on {eur(3332334)} of revenue &mdash; 16.5% of the book. The 14
      service categories a customer pays for at every service. The four filter categories are cut
      hardest, because that is the most competitive end of the basket and the part a customer
      prices most often.</div></div>
    <div class="tierbox choice"><div class="t">And the tier that pays for it</div>
      <div class="big">+{eur(DATA['cover']['captive_gain'])}</div>
      <div class="s">928 captive lines on {eur(660814)} &mdash; only 3.3% of the revenue, and the
      steepest rate in the book. A control unit has no alternative on any shelf. A brake disc has
      three. <span class="tag t">a choice, not a measurement</span></div></div>
  </div>
</div></section>

<!-- ============================ 3b. THE DIAL IN DETAIL -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">3 &middot; the tiers in detail</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section three, continued</span>Every line is classified, and the totals reconcile</h2>

  <table>
    <tr><th>Tier</th><th class="n">Lines</th><th class="n">L12M revenue</th>
      <th class="n">Share</th><th class="n">Movement at 5%</th><th>Why it is priced this way</th></tr>
    <tr><td>Service basket (PMS)</td><td class="n">816</td><td class="n">{eur(3332334)}</td>
      <td class="n">16.5%</td><td class="n"><b>&#8722;{eur(18664)}</b></td>
      <td>The customer's repeated running cost and the tier felt most often. Defended for
      turnover, not for margin.</td></tr>
    <tr><td>Commercial <span class="tag">renamed from contested</span></td><td class="n">10,698</td>
      <td class="n">{eur(10838823)}</td><td class="n">53.8%</td>
      <td class="n">+{eur(570990)}</td>
      <td>An independent alternative freely available at a comparable price, so the rate is
      damped below the average.</td></tr>
    <tr><td>Captive / gated</td><td class="n">928</td><td class="n">{eur(660814)}</td>
      <td class="n">3.3%</td><td class="n">+{eur(61283)}</td>
      <td>The only tier where a price move cannot be answered by buying something else.
      Steepest rate in the book.</td></tr>
    <tr><td>Closing window</td><td class="n">21</td><td class="n">{eur(137285)}</td>
      <td class="n">0.7%</td><td class="n">+{eur(13906)}</td>
      <td>ADAS and calibration content. Priced now, expected to erode from 23 December 2026
      when the regulation opens it.</td></tr>
    <tr><td>Body / legal</td><td class="n">4,477</td><td class="n">{eur(4252793)}</td>
      <td class="n">21.1%</td><td class="n">+{eur(274178)}</td>
      <td>Crash-driven and legally protected in places. <b>Lighting is separated inside this
      tier</b> &mdash; see the next page.</td></tr>
    <tr><td>Unclassified</td><td class="n">999</td><td class="n">{eur(918854)}</td>
      <td class="n">4.6%</td><td class="n">+{eur(58944)}</td>
      <td>No catalogue node could be assigned. Left out of the family totals rather than guessed,
      and named as a residual.</td></tr>
    <tr class="hi"><td><b>Whole book</b></td><td class="n"><b>{DATA['cover']['tier_lines']:,}</b></td>
      <td class="n"><b>{eur(DATA['cover']['tier_revenue'])}</b></td><td class="n"><b>100%</b></td>
      <td class="n"><b>+{eur(DATA['cover']['dial_gain'])}</b></td>
      <td>The tier movements sum to 960,637 euro; the four markets normalise to 960,503. The
      difference is the per-market normalisation, not a disagreement.</td></tr>
  </table>

  <div class="call amber"><div class="h">A warning on a family average that is really one part number</div>
  Where a family's revenue is concentrated in one part number, the family average describes that
  part and not the family. <b>64 market-by-family leaves carry more than 40% of their revenue in a
  single part number</b>, on at least 25,000 euro of revenue. UTI brake pads: <b>97%</b> of
  {eur(82264)} is one part number. UTI oil filters: 71% of {eur(154475)}. UMI aftertreatment: 90%
  of {eur(146087)}. UMI turbochargers: 73% of {eur(95729)}. UTI clutch kits: 100% of
  {eur(90141)}. PR00 brake discs: 63% of {eur(628493)}.</div>

  <div class="call"><div class="h">What could not be classified, stated as residuals</div>
  <b>999 lines are unclassified</b>, {eur(918854)} of revenue, 4.6% of the book &mdash; mostly the
  catalogue's own &ldquo;review needed&rdquo; residual. <b>709 lines carry no current price</b>
  and cannot be repriced. <b>Cabin and blower filters could not be separated</b>: the catalogue
  puts the blower motor and the cabin filter in one node, so the node sits in the service basket
  and the sheets flag it. And <b>ADAS is effectively absent from the catalogue</b> &mdash; only a
  handful of lines carry a radar or camera description, which is why the closing-window tier is
  21 lines. The regulatory opening has almost nothing listed against it yet.</div>
</div></section>

<!-- ============================ 4. LIGHTING -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">4 &middot; lighting and insurance</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section four</span>A lamp priced too high can cost the whole repair</h2>

  <p class="lede">Collision and bodywork parts carry a risk that mechanical parts do not. In Israel
  a vehicle is declared a total loss at a fixed proportion of its pre-accident value, and the
  repair estimate compared against that value is built from our parts prices. A high enough parts
  line can push a repairable truck over the threshold and lose the entire repair &mdash; which is
  worth considerably more than the margin earned on the parts. <b>Filters, brakes and other
  routine service parts are not affected, because the regime exists for accident repairs, not for
  service.</b></p>

  <div class="two-tier">
    <div class="tierbox"><div class="t">The threshold, in Israel</div>
      <div class="big">60%</div>
      <div class="s">of the vehicle's pre-accident value, at which it is a <b>total loss</b>. The
      insurer may settle as a <b>constructive total loss</b> from 55% at the assessor's
      determination &mdash; or from 50% on the policy wording the pickup work read. The assessor
      decides which parts are used and they appear at their list prices. <b>The assessor does not
      set the market price of the parts.</b></div></div>
    <div class="tierbox choice"><div class="t">What the court recorded</div>
      <div class="s" style="margin-top:6px">&ldquo;The inflated parts prices caused many vehicles
      to be declared a &lsquo;total loss&rsquo; or &lsquo;constructive total loss&rsquo; even
      without need, because the cost of their repair was high relative to their value.&rdquo;
      <div style="margin-top:7px"><span class="grade g-r">reported &mdash; not verified</span>
      carried from the research paper of 19 September 2026, which read the decision directly and
      which the management note did not independently re-open.</div></div></div>
  </div>

  <div class="cb"><div class="q">Which half of collision actually earns &mdash; and which half carries the risk?</div>
    <div class="sub">Measured on UTI, last twelve months. Navy is revenue; the right-hand axis is a
    percentage. The terracotta bar is the point of the chart.</div>
    <div class="hold tall"><canvas id="c-lamps"></canvas></div>
    <div class="small" style="margin-top:6px"><b>Lighting is the smaller and the thinner-margin half,
    and it is already priced defensively:</b> {DATA['lamps'][0]['margin']}% weighted margin against
    collision's {DATA['lamps'][1]['margin']}%, and
    <b>{DATA['lamps'][0]['low_class_share']}% of lighting revenue already sits in the
    lowest-margin class we publish</b>, against {DATA['lamps'][1]['low_class_share']}% of collision
    revenue. Lighting is {DATA['lamps'][0]['share_of_two']}% of the two families together and 3.9%
    of UTI's entire parts book.</div></div>

  <div class="cb"><div class="q">What is UTI actually objecting to? Their own deck, old model against P700</div>
    <div class="sub">The lamp items inside the collision package, at list. These are two model
    generations, and part of the gap may be a different lamp rather than a pure list-price
    increase &mdash; we have not separated the two.</div>
    <div class="hold tall"><canvas id="c-lampitems"></canvas></div>
    <div class="small" style="margin-top:6px">The collision package as a whole moves from
    &euro;679.21 to &euro;2,144.48 on the N/7.5 series (<b>+215%</b>) and from &euro;923.66 to
    &euro;2,314.14 on F/10 (<b>+150%</b>). The lamps inside move far more than the package. And the
    <b>bumper was split from one part at &euro;143.37 into four parts at &euro;320.00</b> &mdash; a
    <b>+123%</b> increase with no material change to the part.</div></div>
</div></section>

<!-- ============================ 4b. LIGHTING MOVEMENT -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">4 &middot; the lighting movement</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section four, continued</span>Lighting moves to 0.80, and it is arithmetic rather than preference</h2>

  <p class="lede">This is the one rate in the whole system that follows from a mechanical
  constraint rather than from a preference. The engine that applies the increase sets its own
  <b>+8% per-line ceiling</b>. At a 5% dial, lighting's current share of <b>0.90 puts every
  lighting line at 8.07% &mdash; above the ceiling the engine itself sets.</b> A share of
  <b>0.80 lands at 7.17%</b>, inside it. The break-even share is <b>0.8921</b>.</p>

  <div class="cb"><div class="q">Does lighting clear the ceiling the engine itself sets?</div>
    <div class="sub">The applied increase on a UTI lighting line at a 5% dial. The dashed line is
    the +8% per-line ceiling.</div>
    <div class="hold"><canvas id="c-light"></canvas></div>
    <div class="small" style="margin-top:6px">Of UTI's {DATA['light']['lines']} lighting lines,
    <b>{DATA['light']['with_move']} carry a movement and {DATA['light']['above']} sit above the
    ceiling today.</b> At 0.80, none do. <b>Lighting still rises</b> &mdash; which is right for the
    thinnest-margin family in collision &mdash; it just no longer rises faster than the engine
    permits. This is a reduction in an <i>increase</i>, not a price cut, and it does not buy back
    the write-off risk, because that risk is not measured.</div></div>

  <div class="two">
    <div class="call amber"><div class="h">The gaps that decide how far this can go</div>
    <b>The threshold for vehicles above 3.5 tonnes is not established.</b> The figures come from the
    policy for vehicles <i>up to</i> 3.5 tonnes, and UTI's 1,700 trucks on repair-and-maintenance
    contracts are all above that &mdash; so <b>our write-off exposure for the fleet in question is
    unverified.</b> There is <b>no measured rate at which a parts line tips a repair</b>, and
    <b>no record anywhere in our files of a repair actually lost.</b> The mechanism is documented
    in principle; it is not observed in our business.
    <span class="grade g-n">not found</span></div>
    <div class="call"><div class="h">The routes to a real answer</div>
    <b>Particle-number testing measures function, not presence</b> &mdash; it is the one test a
    badly cleaned or emptied filter cannot pass, and it is coming in three of our four markets.
    And there is a <b>precedent on the shelf: in 2018 the answer proposed was a funded rebate to
    the insurer, split 50:50 between Isuzu in Japan and ISZE</b>, paid where the insurer used
    genuine parts. That route protects the published price rather than discounting it, it is
    budgetable, and it can be made conditional on genuine-part usage.
    <span class="grade g-r">reported &mdash; not verified</span></div>
  </div>

  <div class="call dark"><div class="h">And the pickup is more exposed to this than the truck</div>
  The thresholds were verified against the policy for vehicles up to 3.5 tonnes, and the
  above-3.5-tonne clause could never be found. <b>The pickup sits squarely inside the policy we
  did verify</b> &mdash; it is registered as a commercial vehicle in Israel, including the double
  cab. So <b>the collision write-off mechanism applies to the pickup more cleanly than it does to
  the trucks</b>, which is the opposite of what a truck-led view would predict.</div>
</div></section>

<!-- ============================ 5. THE DEFECT -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">5 &middot; a defect, stated plainly</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section five</span>The system does not enforce its own ceiling</h2>

  <div class="defect"><div class="h">Stated plainly, because it should not be glossed</div>
  The price engine sets a <b>+8% per-line ceiling</b>. The two-tier system, as built, does not
  enforce it. <b>{DATA['cap']['above']:,} of {DATA['cap']['priced_lines']:,} priced lines sit above
  the ceiling &mdash; {DATA['cap']['above_pct']}% of the book &mdash; and the worst line in the book
  moves {DATA['cap']['worst']}%.</b> This is a defect in the system as built, not a design
  intention.</div>

  <div class="two">
    <div>
      <h3>Where the breach sits</h3>
      <table>
        <tr><th>Tier carrying the breach</th><th class="n">Lines above the ceiling</th></tr>
        {"".join(f'<tr><td>{k}</td><td class="n">{v:,}</td></tr>' for k, v in sorted(DATA["cap"]["by_tier"].items(), key=lambda x: -x[1]))}
        <tr class="hi"><td><b>All tiers</b></td><td class="n"><b>{DATA['cap']['above']:,}</b></td></tr>
      </table>
      <div class="small">The tiers with a multiplier above 1.00, combined with the per-market
      normalisation, put whole tiers above a ceiling the engine applies per line. The worst values
      in the book are Captive / gated lines at {DATA['cap']['worst']}% in one market.</div>
    </div>
    <div>
      <h3>The cap question is a decision, and it has two legitimate answers</h3>
      <div class="call" style="margin-top:4px"><div class="h">Respect the cap</div>
      Scale every tier so that no line breaches 8%, or apply the cap as a hard per-line clamp and
      re-normalise the remaining lines upward. <b>Either changes the euro totals on the previous
      page</b>, so it cannot be done without re-running the build.</div>
      <div class="call" style="margin-top:7px"><div class="h">Revise the cap</div>
      On the argument that a per-line cap set for a flat index is the wrong instrument once tiers
      exist. A captive part with no substitute is precisely the line where a rate above 8% is
      defensible. <span class="tag t">a judgment</span></div>
    </div>
  </div>

  <div class="call amber" style="margin-top:10px"><div class="h">What is not defensible</div>
  <b>Shipping the current state without saying so.</b> A reader who takes the +8% per-line ceiling
  as binding and reads the tier table beside it would draw a false conclusion about what the system
  does. That is why this page exists in a policy paper rather than in a build note.</div>

  <div class="call dark" style="margin-top:10px"><div class="h">And the four other questions that need people, not analysis</div>
  <b>Are the four front pad kits interchangeable?</b> If they are, a 25% price spread across
  networks on a safety-critical wear part is a commercial finding. <b>Does the base price embed a
  premium over transfer cost?</b> If it does, the launch headroom is measured from a non-neutral
  base. <b>What is the write-off threshold above 3.5 tonnes, and what is the loss rate?</b>
  Without them the write-off risk is documented in principle and unmeasured in fact. <b>What does
  a distributor actually do with a cut?</b> A conversation, not a data collection &mdash; and the
  one finding that would reverse this paper.</div>
</div></section>

<!-- ============================ 6. THE PICKUP -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">6 &middot; the pickup market</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section six</span>The compliance regime does not bind the pickup buyer</h2>

  <p class="lede">The framework we set out to research does not govern our main UK customer, and
  that is the finding. The UK Operator's Licence controls goods vehicles above 3.5 tonnes; the
  D-Max is plated at <b>3,100 kg</b>. It is also exempt as a <b>dual-purpose vehicle</b>, at about
  <b>1,985 kg unladen against a 2,040 kg limit</b>. Two independent reasons, and the same
  conclusion. <b>The pickup buyer is not locked into a compliance regime, so roadworthiness risk
  does not make them pay more for a part.</b></p>

  <div class="cb"><div class="q">Which pickup buyer is captive, and how far do they drive?</div>
    <div class="sub">The fleet base in each of the four markets, and the measured annual distance.
    The distance is what decides how often the same part is bought.</div>
    <div class="hold tall"><canvas id="c-pickup"></canvas></div>
    <div class="small" style="margin-top:6px"><b>One correction that must travel with this chart:</b>
    the Israeli distance is <b>UMI alone</b> &mdash; 13,611 vehicles, and the file's own distributor
    label on that row is UMI. <b>UTI is not in that file at all</b>, and the two are never blended.
    <b>The UK fleet figure of 47,783 is flagged as an estimate in our own data, not an actual</b>,
    so any per-vehicle rate built on it inherits that.</div></div>

  <table>
    <tr><th>Market</th><th>Does an operator licence bind the pickup?</th>
      <th>What does bind it</th><th>What it means for price</th></tr>
    <tr><td><b>United Kingdom</b></td>
      <td><b>No, twice over</b> &mdash; 3,100 kg plated against 3,500, and exempt as a dual-purpose
      vehicle</td>
      <td><b>Only towing.</b> A combination is licensed above 3.5 tonnes combined, and the D-Max has
      a 6,000 kg gross train weight</td>
      <td>The tradesman who uses it as a car and a van is not captive. The tradesman who tows plant
      is licensed, keeps records, and has his licence on the line. <b>Two different customers for
      one vehicle, and we cannot tell them apart in our sales data.</b></td></tr>
    <tr class="hi"><td><b>Ireland</b></td>
      <td><b>No</b> &mdash; the licence applies above 3.5 tonnes and the pickup is below it</td>
      <td><b>An annual commercial roadworthiness test plus a statutory maintenance duty.</b> To use
      the goods tax rate the owner must declare the vehicle is never used privately</td>
      <td><b>Ireland is the strictest of the four, not the lightest.</b> A committed commercial
      owner with an annual compliance event &mdash; but still a small operator who can buy the same
      filter from the same factor.</td></tr>
    <tr><td><b>Portugal</b></td>
      <td><b>No</b> &mdash; the European threshold applies above 3.5 tonnes</td>
      <td><b>The tax classification, not a compliance regime.</b> The certificate of conformity
      decides whether the pickup is a goods or a passenger vehicle, and the tax difference between
      the two routes can be 4,000 to 8,000 euro</td>
      <td><b>More than 90% of Portuguese pickups are homologated with three seats</b> to secure the
      business tax treatment, and the three-seat version is about 5,500 euro cheaper at retail.
      That buyer has already chosen the cheaper route once.</td></tr>
    <tr><td><b>Israel</b></td>
      <td><b>No</b> operator licence; registered as a commercial vehicle, including double cabs</td>
      <td><b>The insurance mechanism.</b> The pickup sits inside the up-to-3.5-tonne policy we
      verified</td>
      <td>The write-off exposure applies more cleanly to the pickup than to the trucks. And
      <b>66.4% of the installed base is privately owned</b>, which is the buyer most likely to have
      dropped comprehensive cover and to be paying cash.</td></tr>
  </table>
</div></section>

<!-- ============================ 6b. PICKUP CONSEQUENCES -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">6 &middot; what it means for price</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section six, continued</span>Where we can take more, and where we lose more</h2>

  <div class="two">
    <div class="call good"><div class="h">Where we can take more money</div>
      <ol style="margin:6px 0 0 17px;padding:0">
        <li><b>UK &mdash; the D-Max 2.2L launch, on the strength of the warranty window.</b> The
        largest pickup base of the four, and the longest warranty we offer: five years or 125,000
        miles. A part that cannot be substituted during that window can carry a launch price.</li>
        <li><b>Israel &mdash; service parts on the leasing double cab</b>, inside the two-year
        genuine-part-first window. UMI's measured 34,443 km a year means the same part is bought
        most often here, and a fleet buyer on a maintenance contract buys on uptime.</li>
        <li><b>Ireland &mdash; the most defensible position, on the smallest base.</b> Vertically
        integrated, annual commercial test, statutory maintenance duty &mdash; but only 1,338
        light commercial vehicles. <b>Third on size, first on defensibility.</b></li>
      </ol></div>
    <div class="call amber"><div class="h">Where a rise costs more than it earns</div>
      <ol style="margin:6px 0 0 17px;padding:0">
        <li><b>Israel &mdash; collision and lighting.</b> The write-off mechanism applies to the
        pickup, and the installed base is mostly private. A lamp line that tips a modest pickup into
        a write-off loses the whole repair and every future part on that vehicle.</li>
        <li><b>UK &mdash; the visible service basket, into a market just taxed harder.</b> The
        pickup is exempt from licensing, independent garages advertise warranty-preserving servicing
        at up to 50% less, the parts sit on consumer sites <i>with published price histories</i>,
        and the double-cab tax change landed in April 2025: the market was down 0.7% in 2025 and
        down 61.2% year on year in August 2026.</li>
        <li><b>Portugal &mdash; a tax-driven buyer who has already optimised once</b>, on the
        lowest mileage of the four and the smallest base.</li>
      </ol></div>
  </div>

  <div class="call dark"><div class="h">The three things that contradict the brief as it was set</div>
  <b>One:</b> the operator's licence does not bind the UK pickup customer, twice over. <b>Two:</b>
  the Israeli collision mechanism applies to the pickup more cleanly than to the trucks. <b>Three
  and the one to remember:</b> <b>UTI does not carry the pickup &mdash; UMI does.</b> And in the
  UK the pickup sits with IUK, not ITUK. The split must be respected in both cases.</div>

  <div class="assume"><div class="h">The gaps carried forward from this work</div>
  <b>No buyer-type split for pickups in any of the four markets</b> &mdash; tradesman, farmer,
  fleet and lifestyle are not published anywhere we looked. <b>No pickup leasing penetration figure
  for any market</b>; Ireland's 18.9% is for light commercial vehicles as a whole. <b>No measured
  elasticity for pickup parts.</b> <b>No Portuguese-language primary source on the licensing
  threshold</b> &mdash; that position is an inference from the European framework and is recorded as
  a gap rather than asserted. <b>No pickup-specific servicing-location data</b>, so we cannot say
  what share of D-Max servicing happens outside the dealer network. And the UK unladen weight of
  1,985 kg is a computation, not a weighbridge figure &mdash; which does not change the conclusion,
  because the vehicle also passes on the 3,100 kg gross weight against a 3,500 kg threshold.
  <span class="grade g-n">not found</span></div>
</div></section>

<!-- ============================ 7. THE LAUNCH -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">7 &middot; the launch list</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section seven</span>The wedge is the index weight, not the absence of a price</h2>

  <p class="lede">The first job of this section is to correct a claim in our own earlier work.
  The premise was that the launch book is the pricing wedge because the new part numbers
  &ldquo;carry no old price for a distributor to compare against&rdquo;. <b>On this list that is
  true for roughly one part in thirteen.</b></p>

  <div class="three">
    <div class="mini"><div class="v">1,132</div><div class="l">new part numbers</div>
      <div class="s">Flagged as having no 12-month billing history. <b>It does not mean no old
      price.</b></div></div>
    <div class="mini"><div class="v">1,048</div><div class="l">92.6% carry four lists</div>
      <div class="s">A published price in 2023 <i>and</i> 2024 <i>and</i> 2025 <i>and</i> 2026.
      A distributor can and will compare those lines.</div></div>
    <div class="mini"><div class="v">1</div><div class="l">has a competitor price</div>
      <div class="s">Out of 1,132. So the whole launch book has no benchmark, and therefore no
      permitted positional move.</div></div>
  </div>

  <div class="cb"><div class="q">Are the SCR and AdBlue parts priced at class, or is there a premium in them?</div>
    <div class="sub">The 13 functional parts in the SCR / AdBlue chain &mdash; sensors, pumps,
    control units, catalyst and filter assemblies. The sum of unit prices at each scenario.</div>
    <div class="hold tall"><canvas id="c-launch"></canvas></div>
    <div class="small" style="margin-top:6px"><b>The class-implied price is the current 2026 listed
    price &mdash; within 0.45%, and slightly below it.</b> The rule that captive parts may be priced
    to margin and above class-implied <b>has not been applied to a single one of these 13 parts.
    There is no premium in the launch book today.</b> And the worked example: the upstream NOx
    sensor has been <i>held down</i>, from &euro;272.53 in 2023 to &euro;261.11 today. That is free
    pricing nobody has claimed.</div></div>

  <div class="two-tier">
    <div class="tierbox"><div class="t">What the evidence supports</div>
      <div class="s">These 13 parts have <b>no aftermarket equivalent in any comparator on disk</b>.
      Their current list equals their class-implied price. Their base prices carry a published
      2023&ndash;2026 history. And the precedent: a DPF sensor in this family already realises
      <b>69.3% gross margin</b> against the 56% its class allows. <span class="grade g-m">measured</span>
      <div style="margin-top:6px">On the price book the family can carry <b>+25% to +35%</b> over
      the class-implied price. <b>The binding constraint is the policy ceiling, not the competitive
      position, because there is no competitive benchmark on any of them.</b></div></div></div>
    <div class="tierbox choice"><div class="t">What is assumption, and the dependency</div>
      <div class="s">The scenario totals are driven by behavioural parameters all marked as
      assumptions, and the model's own note says it &ldquo;has no observed elasticity behind it and
      must not be presented as if it does&rdquo;. <span class="grade g-i">inference</span>
      <div style="margin-top:6px"><b>And a genuine dependency: if IML's base price already embeds a
      premium over pure transfer cost, the class-implied price is already above a neutral reference
      and the headroom is smaller. We cannot tell from the files we read, and a launch number
      should not be committed until that question reports.</b>
      <span class="grade g-n">not found</span></div></div></div>
  </div>

  <div class="call amber"><div class="h">And the interval gap, which nobody measures</div>
  The recurring urea filter is <b>carryover, not new</b> &mdash; it has billing history and sits at
  &euro;70.53 against a class-implied &euro;70.21, the same finding as the SCR parts. But the
  <b>D-Max schedule states no AdBlue filter interval at all</b>; the 200,000 km figure comes from
  the P700-era N-series schedule, which is a different vehicle. And <b>nothing on disk measures how
  often a urea filter is actually changed</b>: the measured paid rate implies 1.6 to 2.4 million km
  per vehicle, which is longer than any vehicle will run, because what it actually measures is how
  little of the available paid demand we capture. <b>Both numbers are wrong for the interval
  question, in opposite directions.</b></div>
</div></section>

<!-- ============================ 8. REMAN -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">8 &middot; the third price level</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section eight</span>Refurbishment: the competitor below the independent brands</h2>

  <p class="lede">This section answers a question the earlier paper did not ask: <b>what competes
  with our part when the customer does not have to buy a new one?</b> The answer is a third price
  level, and in one market the law protects it.</p>

  <div class="call dark"><div class="h">One thing to read first</div>
  <b>&ldquo;DPD&rdquo; is DPF.</b> The part numbers in the warranty claims are described in our own
  2026 price list as <b>DPD ASSEMBLY</b>, and the claim file calls it a &ldquo;particulate
  defuser&rdquo;. The industry calls it a diesel particulate filter. <b>There is no separate DPD
  product distinct from the DPF</b>, and the two questions are one question.</div>

  <div class="assume"><div class="h">And the mechanism is regulatory, and it is the opposite of what one would expect</div>
  <b>Israel is not a marginal refurbishment market &mdash; it is a regulated one, and the regulation
  protects refurbishment and only refurbishment.</b> The regulations make it a criminal offence to
  remove a particulate filter <b>unless the removal is intended for cleaning, repair or replacement
  of the filter, or for scrapping the vehicle.</b> In the UK, Ireland, Portugal and Spain the legal
  pressure runs the other way: the filter must be <i>present</i> and <i>untampered</i>, and any
  replacement on a Euro 5 or later vehicle must be type-approved. <b>A cleaned original is the
  only legal path in all four markets. That asymmetry, not a quality difference, is what makes the
  Israeli market different.</b> <span class="grade g-r">reported &mdash; not verified</span> for
  the Israeli regulation; each other market's rule is measured.</div>

  <div class="cb"><div class="q">Where is the filter being paid for, and how far had the truck gone?</div>
    <div class="sub">Filter parts cost in the truck warranty book by market, with the median
    odometer at the claim. Israel is the outlier on both measures.</div>
    <div class="hold tall"><canvas id="c-reman"></canvas></div>
    <div class="small" style="margin-top:6px">Israel is <b>37.0% of the entire truck parts claim
    book by value on 10.2% of its claim lines</b>, and <b>40.4% of Israel's truck parts claim cost
    is the filter alone</b>. Truck-wide the filter is 7.2% of claim lines but <b>20.8% of claim
    cost</b>. And <b>76% of the filter cost we are absorbing is on vehicles our own stated terms
    place outside the 3-year / 100,000 km warranty</b> &mdash; 434 of 719 truck filter lines are
    over 100,000 km.</div></div>
  <div class="cb"><div class="q">What do we pay for the same part under warranty, against our own list?</div>
    <div class="sub">Claim cost per unit divided by our own 2026 list price. Every book pays above
    list, and the pattern is consistent across parts and markets.</div>
    <div class="hold"><canvas id="c-claim"></canvas></div>
    <div class="small" style="margin-top:6px"><b>The filter is a class D part &mdash; our own price
    architecture assigns it the lowest margin band, 48%</b>, because a high-value part is where a
    distributor's margin is most exposed to an undercut. <b>So the part where we earn our thinnest
    percentage is also the part where we are paying out between 1.2 and 1.8 times our own list, on
    the largest single warranty line, in the market with the densest refurbishment trade.</b>
    <b>We have not established the mechanism, and we are flagging it rather than explaining it.</b>
    <span class="grade g-n">not found</span></div></div>
</div></section>

<!-- ============================ 8b. REMAN CONSEQUENCES -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">8 &middot; what it means for price</span><span>new in revision 3</span></div>
  <h2><span class="sec-n">section eight, continued</span>Do not cut the part. Decide when our price stops being a claim price.</h2>

  <div class="two">
    <div class="call amber"><div class="h">Where refurbishment is taking money</div>
      <b>Israel trucks over 100,000 km</b> &mdash; 273 lines, 455,633 euro, median odometer 167,807
      km. Entirely outside our stated terms and entirely inside the window where a cleaned filter is
      a rational purchase. Every one of these is a genuine part we did not sell to a dealer and a
      refurbisher did.
      <div style="margin-top:7px"><b>The D-Max filter, everywhere.</b> UMI's two filter assemblies
      are <b>1.10 million euro of warranty cost</b>; IUK has nine of them at a unit cost of 2,615
      euro against a 2,162 euro list. <b>That is the most exposed single part in the portfolio, and
      it is not close.</b></div></div>
    <div class="call good"><div class="h">Where it cannot</div>
      <b>Anything inside warranty</b> &mdash; no substitute exists there by rule, which is why we
      see so much filter volume in claim and so little anywhere else.
      <div style="margin-top:7px"><b>Anywhere particle-number testing is switched on.</b> A
      particle-number test measures function, not presence &mdash; <b>it is the one test a badly
      cleaned or emptied filter cannot pass.</b> Israel has stated its intent to add one at idle,
      Portugal is regulating a threshold, and the UK is piloting for both light and heavy vehicles
      explicitly to detect removed or damaged filters. <b>This is the single largest structural
      protection available to the genuine part, and it is coming in three of the four markets.</b></div>
      <div style="margin-top:7px"><b>And the UK replacement market</b>, where only a type-approved
      unit may be supplied &mdash; so we compete with a <i>compliant</i> rival there rather than a
      grey one.</div></div>
  </div>

  <div class="call dark" style="margin-top:11px"><div class="h">The finding I did not expect, and the question it raises</div>
  <b>We already run two different answers, and one of them is the market differentiator.</b> In
  North America our own published material describes filters reconditioned to new specification,
  flow-tested and benchmarked, with a 12-month unlimited-mile warranty &mdash; and lists <b>the very
  part number that is our largest Israeli warranty line</b> under it. In the UK, our own
  manufacturer announced in December 2017 that it would supply <b>brand new</b> units at prices
  comparable to remanufactured ones, on a new-in-lieu basis, arguing in its own words that this
  &ldquo;removes the uncertainty of the success of cleaning, or future longevity&rdquo;.
  <div style="margin-top:7px"><b>So the play that beats cleaning already exists inside our own
  manufacturer, argued in our own words, with the cleaning-and-longevity argument ready-made. It is
  not on our radar for Israel.</b> Why does Israel get the reman answer and not the new-in-lieu
  answer? That should be the first question asked.</div>
  <div style="margin-top:7px"><b>And we are the only party in this story without a core loop.</b>
  The entire truck claim book contains 24 core lines totalling 3,646 euro, and every one is an
  evaporator, heater or fuel-cooler core &mdash; zero surcharges, zero exchange lines, zero
  remanufactured. A refurbisher's raw material is our customer's used filter, and today we take it
  back for nothing under a warranty claim and give nothing back for it.</div></div>

  <div class="call amber" style="margin-top:10px"><div class="h">What this work could not establish</div>
  <b>No published Israeli price for truck or commercial filter cleaning</b>, so the Israel truck
  ratio is not established &mdash; passenger-car prices are not a proxy for a truck unit. <b>No
  sales-to-dealer filter series</b>, so we cannot quantify how much refurbishment is taking: the
  mechanism is verified and the size is not. <b>No warranty-versus-paid split on the filter
  specifically.</b> <b>No attribution for the 1.2&ndash;1.8&times; claim-over-list multiple</b>
  &mdash; this is the number that most needs a second opinion, because it changes whether the
  Israeli price is wrong or the claim valuation is. <b>And no causal link</b> between the
  particulate-matter sensor campaign and any filter assembly claim: 941 sensor claim lines at
  253,024 euro in the light commercial book against 43 filter lines is the kind of ratio that means
  either the sensors fail far more often, or the two are the same job billed twice. <b>One of those
  is a price question; the other is a quality question.</b> <span class="grade g-n">not found</span></div>
</div></section>

<!-- ============================ 9. THE FLOOR AND THE CHAIN -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">9 &middot; the cost floor and the chain</span><span>carried from revision 2</span></div>
  <h2><span class="sec-n">section nine</span>On these parts there is no margin left to decide</h2>

  <p class="lede">A price has to clear two tests, not one: it has to be defensible against the
  competing product, and it has to leave enough margin to be worth selling. <b>On the parts where
  we can bridge at all, the competing price is often below our own distributor's cost</b> &mdash;
  and the ratios are not 1.1&times; or 1.3&times;, they are around 0.15&times;.</p>

  <div class="cb"><div class="q">Is the competing price above or below what our distributor paid?</div>
    <div class="sub">Four verified cases. Navy is the net price our distributor paid per unit;
    terracotta is the cheapest aftermarket equivalent online. <b>They are different goods and this
    chart says so.</b></div>
    <div class="hold"><canvas id="c-floor"></canvas></div>
    <div class="small" style="margin-top:6px">On <b>{DATA['floor']['below_any']} of
    {DATA['floor']['testable_any']}</b> bridged part numbers the aftermarket sits below at least
    one of our distributor's own floors, at a median of <b>{DATA['floor']['median_any']:.2f}&times;</b>;
    {DATA['floor']['below_all']} of {DATA['floor']['testable_all']} sit below <i>every</i> floor we
    hold. <b>Caveat that shrinks the finding:</b> this compares an aftermarket part against a
    genuine assembly, so the ratio overstates the gap. Read it as a landing-price fact, not a
    like-for-like comparison. <b>And the coverage limit: the bridge resolves 76 of 15,273 priced
    part numbers &mdash; 0.50%</b> &mdash; assembled from parts we already knew had a competitor, so
    it is optimistic rather than conservative. It is a warrant to look at the rest, not a rate to
    apply to the book.</div></div>

  <div class="two">
    <div class="cb"><div class="q">Is the margin a commercial decision or a lookup?</div>
      <div class="sub">Each bar is one class letter and the margin it sets. The margin is
      <b>identical for every part number in the class</b>, and the eight letters span 45% to 56%.
      84.3% of the priced book earns inside that one band.</div>
      <div class="hold tall"><canvas id="c-margin"></canvas></div></div>
    <div class="cb"><div class="q">Can a margin cut even reach the competitor?</div>
      <div class="sub">Our price and the dealer's, as a multiple of the competing retail price.</div>
      <div class="hold tall"><canvas id="c-chain"></canvas></div>
      <div class="small" style="margin-top:6px">A 34-point give-away on our margin moves the price a
      customer is quoted from 1.83&times; the independent price to 1.03&times; &mdash;
      <b>barely to parity</b>. A reduction in ours is multiplied by
      <b>{DATA['chain']['mult']:.3f}</b> before a customer sees it.</div></div>
  </div>

  <div class="call amber"><div class="h">And the coverage that makes this the whole argument</div>
  <b>83.5% of the priced book by euro has no same-shop and no Eucon benchmark.</b> 880 lines carrying
  5,369,216 euro &mdash; <b>16.5% of the priced euro</b> &mdash; do have a benchmark. Brakes is the
  exception at 82.6% of that family's billed euro, which is why brakes is the pilot. <b>And the
  launch book makes the same point from the other direction: competitor evidence is present on
  1 part in 1,132.</b></div>
</div></section>

<!-- ============================ 10. THE MOVEMENTS -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">10 &middot; the proposed movements</span><span>the brief's central ask</span></div>
  <h2><span class="sec-n">section ten</span>What we propose to move, and why</h2>

  <p class="lede">Each movement carries its one-line reason and its grade.
  <span class="grade g-m">measured</span> means arithmetic on our own files;
  <span class="grade g-i">inference</span> means a judgment. <b>No live price is moved by this
  paper.</b></p>

  <h3>The basket that comes down</h3>
  <table>
    <tr><th>Movement</th><th class="n">Lines</th><th class="n">Effect at 5%</th><th>Reason</th><th>Grade</th></tr>
    <tr><td><b>Service basket held flat, then cut on filters</b></td><td class="n">816</td>
      <td class="n"><b>&#8722;{eur(18664)}</b></td>
      <td>This is the customer's repeated running cost and the tier where a price move is felt most
      often. Defended for turnover, not for margin.</td>
      <td><span class="grade g-m">measured</span> the euro<br><span class="grade g-i">choice</span> the rate</td></tr>
    <tr><td>&mdash; the four filter categories cut hardest (share &#8722;0.20)</td>
      <td class="n">within</td><td class="n">oil filters down in every market</td>
      <td>Filters are the most competitive end of the basket and the part a customer prices most
      often. UTI's oil filter &minus;2,051 and AdBlue filter &minus;3,140.</td>
      <td><span class="grade g-m">measured</span> the euro</td></tr>
    <tr class="hi"><td><b>Lighting share 0.90 &rarr; 0.80</b></td>
      <td class="n">{DATA['light']['lines']} UTI lines</td>
      <td class="n">{DATA['light']['now']}% &rarr; <b>{DATA['light']['prop']}%</b></td>
      <td><b>0.90 breaches the engine's own +8% per-line ceiling; 0.80 does not.</b> It answers the
      distributor's complaint without yielding on the insurance mechanism.
      {DATA['light']['above']} lines come back inside the ceiling.</td>
      <td><span class="grade g-m">measured</span> the arithmetic<br><span class="grade g-i">inference</span> the choice</td></tr>
    <tr><td><b>Collision and bodywork unchanged at 0.90</b></td><td class="n">244 UTI lines</td>
      <td class="n">unchanged</td>
      <td>Crash-driven and legally protected in places. The panel logic is not the problem; the
      lamp logic was.</td><td><span class="grade g-i">inference</span></td></tr>
  </table>

  <h3>The tiers that carry the increase</h3>
  <table>
    <tr><th>Movement</th><th class="n">Lines</th><th class="n">Effect at 5%</th><th>Reason</th><th>Grade</th></tr>
    <tr><td><b>Commercial carries the increase at 0.80</b></td><td class="n">10,698</td>
      <td class="n">+{eur(570990)}</td>
      <td>53.8% of the book by revenue and the tier where a customer can freely buy an alternative,
      so the rate is damped below the average.</td>
      <td><span class="grade g-m">measured</span> the euro<br><span class="grade g-i">choice</span> 0.80</td></tr>
    <tr class="hi"><td><b>Captive / gated takes 1.60 &mdash; the steepest rate in the book</b></td>
      <td class="n">928</td><td class="n">+{eur(61283)}</td>
      <td>The only tier where a price move cannot be answered by buying something else. A control
      unit has no alternative on any shelf; a brake disc has three.
      <b>Anchored only on the 69.3% sensor precedent.</b></td>
      <td><span class="grade g-i">choice</span></td></tr>
    <tr><td><b>Closing window takes 1.40</b></td><td class="n">21</td><td class="n">+{eur(13906)}</td>
      <td>Priced now because the regulatory opening from 23 December 2026 will erode it. Almost
      nothing is listed against it yet, which is itself the finding.</td>
      <td><span class="grade g-i">choice</span></td></tr>
    <tr><td><b>Unclassified takes the neutral rate, 1.00</b></td><td class="n">999</td>
      <td class="n">+{eur(58944)}</td>
      <td>No catalogue node assigned. Left out of the family totals rather than guessed, and named
      as a residual.</td>
      <td><span class="grade g-m">measured</span> the count<br><span class="grade g-i">choice</span> the rate</td></tr>
  </table>

  <div class="assume"><div class="h">And which of the seven multipliers are judgment, said plainly</div>
  <b>Four of the seven are pure judgment and should be read as such.</b> The <b>0.00 on the service
  basket</b> and the <b>&#8722;0.20 on filters</b> are judgment about how much of the basket to
  defend. The <b>1.60 on captive</b> is judgment about how much a customer with no alternative will
  bear, and it is anchored on nothing measured. The <b>1.40 on the closing window</b> is judgment
  about how fast the regulatory opening erodes the position. <b>The remaining three &mdash; 0.90,
  0.80 on lighting, and 1.00 &mdash; are derived</b>: 0.90 is the existing body rate, 0.80 on
  lighting follows from the cap arithmetic, and 1.00 is by definition neutral.
  <div style="margin-top:7px"><b>This system is honest about the shape of the answer and candid
  that the levels are set by judgment, and the judgment should be revisited before any of them is
  used to price a line.</b></div></div>
</div></section>

<!-- ============================ 11. DECISIONS -->
<section class="page"><div class="pad">
  <div class="ph"><span class="pn">11 &middot; decisions</span><span>16 items</span></div>
  <h2><span class="sec-n">section eleven</span>What has to be decided, in the order it matters</h2>

  <table>
    <tr><th class="n">#</th><th>Decision</th><th>Why it comes here</th></tr>
    <tr class="hi"><td class="n">1</td><td><b>Adopt the two-tier system &mdash; and decide the cap
      question with it</b></td>
      <td>The system is built and it does not enforce its own +8% per-line ceiling. Either the
      system respects the cap or the cap is revised, and either answer requires a re-run.
      <b>This is first because it determines every number after it.</b></td></tr>
    <tr class="hi"><td class="n">2</td><td><b>Set the dial</b></td>
      <td>The 5% used throughout is a placeholder. At 3% / 5% / 7% the four markets yield
      {eur(DATA['dial']['totals'][0])} / {eur(DATA['dial']['totals'][1])} /
      {eur(DATA['dial']['totals'][2])}. <b>This is management's number and nothing else
      substitutes for it.</b></td></tr>
    <tr><td class="n">3</td><td><b>Decide whether brakes is the pilot</b></td>
      <td>82.6% evidence coverage, twenty part numbers carrying three-quarters of the family, a live
      complaint case. And the first question is not a price question at all.</td></tr>
    <tr><td class="n">4</td><td><b>Confirm lighting at 0.80, or take 0.85, or explain why 0.90
      stays</b></td>
      <td>The one rate in the system that follows from a mechanical constraint. The break-even share
      is {DATA['light']['breakeven']}. Whatever is decided, record the number with its reason.</td></tr>
    <tr><td class="n">5</td><td><b>Settle the FY2027 ambition on a stated basis</b></td>
      <td>Before or after the distributor support payment. At the 20% figure the specification uses,
      1.00 of headline lands as 0.80, so +4% nets +3.2%. The options are +4% (581k a year), +5%
      (726k), or an open increase on the launch families with the legacy book at +3%.</td></tr>
    <tr><td class="n">6</td><td><b>Decide whether the brakes-low / emissions-high shape is a target
      or a consequence</b></td>
      <td>As computed it adds 540k of gross profit by raising emissions prices 35% to fund a brakes
      cut &mdash; but the evidence says emissions is contested, not captive. <b>The raise funds a
      cut by betting on a captiveness the evidence contradicts.</b></td></tr>
    <tr><td class="n">7</td><td><b>Fund the competitive price index, or accept 16.5% of billed
      euro</b></td>
      <td>Brakes proves dense coverage is achievable at 82.6%. Doing it for two or three more
      families is a resourcing question, not a technical one.</td></tr>
    <tr><td class="n">8</td><td><b>Establish whether we have a voice in class assignment and in the
      base price</b></td>
      <td><b>Class assignment is margin assignment</b> and it fixes the margin for the life of a
      part. The launch work makes it concrete: <b>922 of 1,071 classed new part numbers sit in class
      C and only 2 sit in class P.</b></td></tr>
    <tr><td class="n">9</td><td><b>Aim the margin increase at what is genuinely gated, not at what
      is merely unfamiliar</b></td>
      <td>The gated families are narrow: VIN-paired modules, variant coding, and ADAS calibration
      until December 2026. <b>The closing-window tier is 21 lines on {eur(137285)} &mdash; the whole
      regulatory opening, and almost nothing is listed against it.</b></td></tr>
    <tr><td class="n">10</td><td><b>Decide whether our own second brand is priced as a competitor or
      as a cost</b></td>
      <td>Every one of the seven European truck makers runs a lower-priced own line and we run one
      too &mdash; 356 part numbers cross-referenced to 431 genuine numbers, but only 213 priced part
      numbers, or 7.1% of billed value.</td></tr>
    <tr><td class="n">11</td><td><b>Decide the filter position as terms and timing, not as price</b></td>
      <td>Hold the aftertreatment price flat once each vehicle's own warranty ends. And ask first
      why Israel gets the reman answer and the UK gets the new-in-lieu answer.</td></tr>
    <tr><td class="n">12</td><td><b>Take the top 200 parts by revenue, mapped against criticality
      and competition</b></td>
      <td>The high-criticality / low-competition cluster is where we are most likely under-pricing.
      No new data source needed.</td></tr>
    <tr><td class="n">13</td><td><b>Put currency on every price pack</b></td>
      <td>The rate in use fell the euro price of an unchanged yen base price by 11.7% since 2023 and
      does not move our margin at all. Any comparison without a currency stamp is against a moving
      floor.</td></tr>
    <tr><td class="n">14</td><td><b>Answer the pass-through question with ITUK, as a
      conversation</b></td>
      <td>What actually happens to the dealer price when we reduce ours. No model can answer it and
      no file will either. <b>It is the one finding that would reverse this paper.</b></td></tr>
    <tr><td class="n">15</td><td><b>Confirm the warranty term and mileage cap, market by
      market</b></td>
      <td>The load-then-hold tactic on failure-driven parts pays above roughly three years and costs
      money below it.</td></tr>
    <tr><td class="n">16</td><td><b>Decide the CIS competitor profile</b></td>
      <td>Chinese genuine-equivalent, Chinese independent, or EU re-export. <b>And note the legal
      constraint: parallel trade inside the EEA cannot be closed by agreement</b>, so re-export
      monitoring is a detection tool, not a cure.</td></tr>
  </table>

  <div class="call dark"><div class="h">What this paper does not do</div>
  It changes no price, no list and no published number. No allocation is run. <b>UTI and UMI are two
  distributors and are never blended; IUK and ITUK are two networks and are never blended.</b>
  Leakage euro stays internal. Every figure carries the window it was measured on, because the
  pricing work has four windows in play and they do not agree.
  <div class="small" style="color:#9fb0cc;margin-top:8px">Revision 3 &middot; 19 September 2026
  &middot; prepared for management &middot; shared / external. The full written paper is
  <b>PRICING_POLICY_PAPER_2026-09-19_REV3.md</b>, and it carries every source under every figure.</div></div>
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
_scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
_app = _scripts[-1] if _scripts else ""
_ids = re.findall(r'<canvas id="([^"]+)"', page)
from collections import Counter as _C

_dupes = {k: v for k, v in _C(_ids).items() if v > 1}

with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as _fh:
    _fh.write(_app)
    _tmp = _fh.name
_chk = subprocess.run(["node", "--check", _tmp], capture_output=True, text=True)
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
# forbidden patterns in a shared artifact
_bad = [b for b in ("sell-out", "sellout", "Mode A", "MODE A", "Mode B", "IML v7",
                    "PRISM lane", "class factor", "cdn.jsdelivr", "cdnjs.cloudflare",
                    "https://cdn", "http://cdn") if b.lower() in page.lower()]
say(f"  forbidden strings      : {_bad if _bad else 'none'}")
say(f"  external http refs     : {len(re.findall(r'src=.https?://', page))}")

if (_chk.returncode != 0 or _dupes or page.count("new Chart(") != len(_ids) or _bad
        or page.count("new Chart(") != len(_ids)):
    say("")
    say("GATE_FAIL - not written. Fix the script or the canvas set.")
    sys.exit(1)

with open(HTML, "w", encoding="utf-8") as fh:
    fh.write(page)
size = os.path.getsize(HTML)
say("")
say(f"  {HTML}")
say(f"  {size:,} bytes ({size/1024/1024:.2f} MB)")

with open(CMD, "wb") as fh:
    fh.write(b'@echo off\r\n'
             b'start "" "%~dp0ISZE_Pricing_Policy_Paper_REV3.html"\r\n')
_cmd = open(CMD, "rb").read()
say(f"  {CMD}")
say(f"  launcher bytes        : {_cmd!r}")
assert _cmd.count(b"\r\n") == 2 and _cmd.count(b"\n") == 2 and b"\r\r" not in _cmd, \
    "launcher is not clean CRLF"
say("  launcher CRLF         : verified")
say("BUILD_OK")
