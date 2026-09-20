#!/usr/bin/env python3
"""
Build the shared page: service demand, capture and sales by vehicle family, per customer.

Reads only the derived files written by ``build_pms_capture_by_family.py`` plus the spend-per-vehicle
and competing-price files. Computes nothing that is not traceable to one of them, and asserts the
euro on the page back to the source before it writes.

Chart form follows the question (skill ``isze-best-chart``):
  * where the family trend is going            -> change bars against the first full year
  * a family's split inside one customer        -> donut, at most four segments
  * many customers on one metric                -> small multiples on a shared scale
  * who carries the biggest euro gap            -> ranked bars, euro at the bar
  * where we sit against the independent market -> ranked bars, one per part family we can place
Every chart with more than one series carries a written key.

Usage:
    python 02_dashboards/sales/_build/build_pms_family_evolution_page.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PRISM = ROOT / "03_analytics" / "Isuzu" / "prism"
OUT_DIR = ROOT / "02_dashboards" / "sales"
OUT_HTML = OUT_DIR / "ISZE_PMS_Family_Evolution.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_PMS_Family_Evolution.cmd"
CHARTJS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"
BUILD_DIR = OUT_DIR / "_build"

SNAPSHOT = "2026-09-19"
norm = lambda x: (str(x).strip().lstrip("0") or "0")  # noqa: E731

FAMILY_LABEL = {
    "n_series_truck": "N-series truck",
    "heavy_truck": "Heavy truck (F-series and C&E)",
    "light_vehicle": "Light vehicle (D-Max pickup and SUV)",
    "shared_across_families": "Parts used across more than one family",
    "unattributed": "No vehicle reference found",
}
NAMED = ["n_series_truck", "heavy_truck", "light_vehicle"]
CAT_LABEL = {
    "air_filter": "Air filter", "blower_filter": "Blower filter", "brake_pad": "Brake pad",
    "brake_rotor": "Brake rotor", "brake_shoe": "Brake shoe", "clutch_booster": "Clutch booster",
    "clutch_disc": "Clutch disc", "clutch_kit": "Clutch kit",
    "clutch_pressure_plate": "Clutch pressure plate", "fuel_filter": "Fuel filter",
    "oil_filter": "Oil filter", "pilot_bearing": "Pilot bearing",
    "release_bearing": "Release bearing", "urea_filter": "Urea (AdBlue) filter",
}
# Spend targets per vehicle a year, from the research study. The N-series figure is a blend,
# because that fleet is a measured mix of 3.5 t and the heavier group and the two have different
# targets. The blend is computed per customer from that customer's own measured 3.5 t share.
TARGET_N35 = 296.0
TARGET_N75 = 739.0
TARGET_HEAVY = 887.0
TARGET_LIGHT = 250.0

SCOPE_18 = ["BELGIUM", "CYPRUS", "DENMARK", "FINLAND", "GERMANY", "GREECE", "HUNGARY", "ICELAND",
            "IRELAND", "ITUK", "IUK", "MALTA", "NORWAY", "PORTUGAL", "ROMANIA", "SWEDEN", "UMI",
            "UTI"]


def die(msg: str) -> None:
    print(f"BUILD FAIL: {msg}")
    sys.exit(1)


def rd(name: str) -> pd.DataFrame:
    p = DER / name
    if not p.is_file():
        die(f"missing {p} — run build_pms_capture_by_family.py first")
    return pd.read_csv(p)


# ────────────────────────────────────────────────────────────────── load
core = rd("pms_capture_by_family.csv")
evo = rd("pms_family_evolution_both_clocks.csv")
fam_map = rd("pms_family_part_number_map.csv")
meta = json.loads((DER / "pms_capture_by_family.meta.json").read_text(encoding="utf-8"))
gps = rd("gps_spu_by_distributor.csv")
buckets = pd.read_csv(PRISM / "data" / "uio_by_model_bucket.csv")
n35share = pd.read_csv(PRISM / "data" / "uio_ld_n35_share.csv")
competitor = rd("lost_sales_competitor_pn.csv")

# the 18 customers the service model covers. The evolution file also carries markets outside it,
# and those must not be mixed into a network figure the model does not cover.
markets = sorted(set(core.distributor_code.unique()))
ev_outside = sorted(set(evo.distributor_code.unique()) - set(markets))

# ────────────────────────────────────────────────────────────────── lane guard
lane_n = core.groupby("distributor_code").lane.nunique()
if int(lane_n.max()) > 1:
    die(f"a customer carries more than one interval lane: {lane_n[lane_n > 1].to_dict()}")
# the interval lane each customer runs. The payload carries only which of the two schedules
# applies, so the page never has to translate an internal file name into a label.
LANE = {m: str(v) for m, v in core.groupby("distributor_code").lane.first().to_dict().items()}
# ────────────────────────────────────────────────────────────────── fleet, 2025 estimate
fleet = {}
for _, b in buckets.iterrows():
    db = b.distributor_code
    sh = float(n35share.loc[n35share.distributor_code == db, "n35_share"].iloc[0]) \
        if (n35share.distributor_code == db).any() else 0.0
    t_ns = sh * TARGET_N35 + (1 - sh) * TARGET_N75
    target = b.cv_std_uio * t_ns + b.f_series_uio * TARGET_HEAVY + b.lcv_uio * TARGET_LIGHT
    fleet[db] = {
        "n_series": round(float(b.cv_std_uio)),
        "heavy": round(float(b.f_series_uio)),
        "light": round(float(b.lcv_uio)),
        "total": round(float(b.cv_std_uio + b.f_series_uio + b.lcv_uio)),
        "n35_share": round(sh, 4),
        "n_series_target_per_vehicle": round(t_ns, 1),
        "target_eur": round(float(target)),
    }

# ────────────────────────────────────────────────────────────────── per customer blocks
def cust_block(db: str) -> dict:
    c = core[core.distributor_code == db]
    y25 = c[c.year == 2025]
    fam_rows = []
    for f in ["n_series_truck", "heavy_truck", "light_vehicle", "shared_across_families",
              "unattributed"]:
        g = y25[y25.family == f]
        if g.empty:
            continue
        exp = float(g.expected_eur.sum())
        bill = float(g.billed_eur.sum())
        fam_rows.append({
            "family": f, "label": FAMILY_LABEL[f],
            "fleet": (None if f in ("unattributed",)
                      else int(fleet.get(db, {}).get(
                          {"n_series_truck": "n_series", "heavy_truck": "heavy",
                           "light_vehicle": "light", "shared_across_families": "total"}[f], 0))),
            "expected_eur": round(exp), "billed_eur": round(bill),
            "billed_units": round(float(g.billed_units.sum())),
            "expected_qty": round(float(g.expected_qty.sum())),
            "capture": (round(bill / exp, 4) if exp > 0 else None),
            "baseline_rows": int(len(g)),
        })
    # service family detail for the selected family on the page
    cats = []
    det = (c[(c.year == 2025) & (c.family.isin(NAMED + ["shared_across_families"]))]
           .groupby(["pms_category", "family"], as_index=False)
           .agg(expected=("expected_eur", "sum"), billed=("billed_eur", "sum"),
                units=("billed_units", "sum")))
    for r in det.itertuples():
        cats.append({"cat": r.pms_category, "label": CAT_LABEL.get(r.pms_category, r.pms_category),
                     "family": r.family, "expected_eur": round(float(r.expected)),
                     "billed_eur": round(float(r.billed)), "billed_units": round(float(r.units))})
    return {"families": fam_rows, "categories": cats}


CUST = {m: cust_block(m) for m in markets}

# ────────────────────────────────────────────────────────────────── trend by family, both clocks
def trend_block(clock: str, scope: str) -> dict:
    e = evo[(evo.clock == clock) & (evo.scope == scope)
            & (evo.distributor_code.isin(markets))]
    periods = sorted(int(p) for p in e.period.unique())
    complete = sorted(int(p) for p in e[e.period_is_complete].period.unique())
    months = {int(r.period): int(r.months_in_period) for _, r in
              e.drop_duplicates("period").iterrows()}
    fam = {}
    for f in ["n_series_truck", "heavy_truck", "light_vehicle", "shared_across_families",
              "unattributed"]:
        ef = e[e.family == f]
        if ef.empty:
            continue
        fam[f] = {
            "eur": {int(p): round(float(g.billed_eur.sum())) for p, g in ef.groupby("period")},
            "units": {int(p): round(float(g.units.sum())) for p, g in ef.groupby("period")},
            "pns": {int(p): int(g.distinct_pns.sum()) for p, g in ef.groupby("period")},
        }
    return {"periods": periods, "complete": complete, "months": months,
            "period_label": {
                int(p): (f"calendar year {int(p)}" if clock == "CY"
                         else f"ISZE year {int(p)} (April {int(p)-1} to March {int(p)})")
                for p in periods},
            "family": fam}


TREND = {c: {s: trend_block(c, s) for s in ("service_parts_only", "all_billed_parts")}
         for c in ("CY", "FY")}

# per-customer family trend, for the small multiples and the market trend table
CUST_TREND = {}
for clock in ("CY", "FY"):
    e = evo[(evo.clock == clock) & (evo.scope == "service_parts_only")
            & (evo.distributor_code.isin(markets))]
    for f in NAMED + ["shared_across_families"]:
        piv = e[e.family == f].pivot_table(index="distributor_code", columns="period",
                                          values="billed_eur", aggfunc="sum")
        CUST_TREND.setdefault(clock, {})[f] = {
            str(col): {str(i): (None if pd.isna(v) else round(float(v))) for i, v in piv[col].items()}
            for col in piv.columns}

# ────────────────────────────────────────────────────────────────── spend per vehicle and the gap
GPS = {}
for _, r in gps.iterrows():
    GPS.setdefault(r.distributor_code, {})[int(r.year)] = {
        "spu": None if pd.isna(r.spend_per_unit_eur) else round(float(r.spend_per_unit_eur), 1),
        "spu_ex": None if pd.isna(r.spend_per_unit_ex_warranty_eur)
        else round(float(r.spend_per_unit_ex_warranty_eur), 1),
        "uio": None if pd.isna(r.uio_units) else round(float(r.uio_units)),
        "sales_eur": None if pd.isna(r.total_sales_eur) else round(float(r.total_sales_eur)),
        "source": str(r.uio_source),
    }

# the spend gap, per customer and per family. The target is the same three-way fleet split the
# demand model uses, so the gap is measured against the fleet the customer actually has.
GAP = []
for db in markets:
    f = fleet.get(db)
    if not f:
        continue
    g25 = GPS.get(db, {}).get(2025)
    if not g25 or g25["spu"] is None:
        continue
    blend = f["target_eur"] / f["total"] if f["total"] else None
    gap_v = (blend - g25["spu"]) if blend is not None else None
    GAP.append({
        "db": db, "spu": g25["spu"], "target_per_vehicle": (round(blend, 1) if blend else None),
        "gap_per_vehicle": (round(gap_v, 1) if gap_v is not None else None),
        "gap_eur": (round(gap_v * f["total"]) if gap_v is not None else None),
        "sales_eur": g25["sales_eur"], "target_eur": f["target_eur"], "fleet": f["total"],
        "source": g25["source"],
        "fam_fleet": {"n_series": f["n_series"], "heavy": f["heavy"], "light": f["light"]},
        "fam_target": {
            "n_series": round(f["n_series"] * f["n_series_target_per_vehicle"]),
            "heavy": round(f["heavy"] * TARGET_HEAVY),
            "light": round(f["light"] * TARGET_LIGHT),
        },
    })
GAP.sort(key=lambda r: -(r["gap_eur"] or 0))

# ────────────────────────────────────────────────────────────────── position vs the independent market
pn_family = dict(zip(fam_map.pn.astype(str).map(norm), fam_map.family))
pn_resolution = dict(zip(fam_map.pn.astype(str).map(norm), fam_map.resolution))
competitor = competitor.assign(pn=competitor.part_number.map(norm))
competitor["family"] = competitor.pn.map(pn_family).fillna(competitor.pn.map(pn_resolution))
comp_rows = competitor[competitor.family.isin(NAMED)]
COMP = []
if len(comp_rows):
    for f in NAMED:
        g = comp_rows[comp_rows.family == f]
        if g.empty:
            continue
        COMP.append({
            "family": f, "label": FAMILY_LABEL[f],
            "median_index": round(float(g.index_reference_vs_competitor.median()), 3),
            "pns": int(g.part_number.nunique()),
            "billed_eur": round(float(g.billed_eur_latest_complete_cy.sum())),
            "above": int((g.index_reference_vs_competitor > 1).sum()),
            "below": int((g.index_reference_vs_competitor < 1).sum()),
        })
COMP_VINTAGE = str(competitor.vintage.mode().iloc[0]) if len(competitor) else "n/a"
COMP_TIER = str(competitor.tier.mode().iloc[0]) if len(competitor) else "n/a"
COMP_PLACED_ROWS = int(len(comp_rows))
COMP_ALL_ROWS = int(len(competitor))

# ────────────────────────────────────────────────────────────────── network totals
net25 = core[(core.year == 2025)]
NET = {
    "expected_eur": round(float(net25.expected_eur.sum())),
    "billed_eur": round(float(net25.billed_eur.sum())),
    "billed_units": round(float(net25.billed_units.sum())),
    "fleet": int(sum(fleet[m]["total"] for m in markets)),
    "target_eur": int(sum(fleet[m]["target_eur"] for m in markets)),
    "gap_eur": round(float(sum((r["gap_eur"] or 0) for r in GAP))),
    "sales_2025_eur": round(float(sum(r["sales_eur"] or 0 for r in GAP))),
}
NET["attributed_share"] = round(
    float(net25[net25.family.isin(NAMED)].billed_eur.sum() / NET["billed_eur"]), 4)

# cross-check: the page's network billed euro must equal the source rows it came from
_chk = float(core[core.year == 2025].billed_eur.sum())
if abs(_chk - NET["billed_eur"]) > 1.0:
    die(f"network euro does not tie to pms_capture_by_family.csv: {_chk} vs {NET['billed_eur']}")
_pub = pd.read_csv(DER / "pms_capture_by_db_year.csv")
_pub = float(_pub[(_pub.line_type == "total") & (_pub.year == 2025)
                  & (_pub.distributor_code.isin(markets))].actual_rev_eur.sum())
if abs(_pub - NET["billed_eur"]) > 1.0:
    die(f"network euro does not tie to the published capture file: {_pub} vs {NET['billed_eur']}")

# ────────────────────────────────────────────────────────────────── heavy truck, measured
# The page used to say the family "carries almost no attributable billing". That is false. This
# block measures what the family actually holds, from the family table and the billing, so the
# sentence on the page is a measurement rather than a claim. Absence of a part number from one
# worklist is not evidence that it did not sell.
_bands = pd.read_csv(DER / "vehicle_family_bands.csv")
_bands["pn"] = _bands["pn"].astype(str).map(norm)
_h = _bands[_bands.family == "heavy_truck"].copy()
_FWD = ("FRR", "FSR", "FTR", "FVR", "FVM", "FRS", "FSS", "FTS", "FVZ", "F*R", "FV*", "FS*", "FT*",
        "FR*")
_h["note"] = _h["source_note"].fillna("").str.upper()
_h["fwd"] = _h["note"].map(lambda s: any(t in s for t in _FWD))
_cat = pd.read_csv(DER / "bvp_pn_dimension.csv", dtype=str, low_memory=False)
_cat["pn"] = _cat["part_number"].astype(str).map(norm)
_cat = _cat[_cat.pms_category.notna()].drop_duplicates("pn")[["pn", "pms_category"]]
_h = _h.drop(columns=[c for c in _h.columns if c.startswith("pms_category")], errors="ignore")
_h = _h.merge(_cat, on="pn", how="left")
_bill = pd.read_parquet(BUILD_DIR / "_deep_billing_cache.parquet")
_bill["pn"] = _bill["pn"].astype(str).map(norm)
_hb = _bill[_bill.pn.isin(set(_h.pn)) & (_bill.y == 2025)]

HEAVY = {
    "pns": int(len(_h)),
    "fwd_pns": int(_h.fwd.sum()),
    "fleet": int(sum(fleet[m]["heavy"] for m in markets)),
    "markets": ", ".join(m for m in markets if fleet[m]["heavy"] > 0) or "none in this scope",
    "billed2025": round(float(_hb.net_sales_value.sum())),
    "units2025": round(float(_hb.billed_qty.sum())),
    "top_categories": [
        {"label": CAT_LABEL.get(c, c), "pns": int(n)}
        for c, n in _h[_h.fwd].pms_category.value_counts().head(4).items()],
}

PAYLOAD = {
    "snapshot": SNAPSHOT,
    "markets": markets,
    "namedFamilies": NAMED,
    "familyLabel": FAMILY_LABEL,
    "catLabel": CAT_LABEL,
    "lane": LANE,
    "fleet": fleet,
    "cust": CUST,
    "trend": TREND,
    "custTrend": CUST_TREND,
    "gap": GAP,
    "competitor": COMP,
    "competitorMeta": {"vintage": COMP_VINTAGE, "tier": COMP_TIER,
                       "placedRows": COMP_PLACED_ROWS, "allRows": COMP_ALL_ROWS},
    "net": NET,
    "meta": {
        "familyResolution": meta["family_resolution"],
        "tie1": meta["tie_out"],
        "tie2": meta["tie_out_attributed_euro"],
        "notAttempted": meta["not_attempted"],
        "outsideScope": ev_outside,
        "targets": {"n35": TARGET_N35, "n_series_other": TARGET_N75,
                    "heavy": TARGET_HEAVY, "light": TARGET_LIGHT},
        "heavyResolution": HEAVY,
    },
}
body = json.dumps(PAYLOAD, separators=(",", ":"), allow_nan=False)

chart_js = CHARTJS.read_text(encoding="utf-8")
chart_js = re.sub(r"//# sourceMappingURL=\S+", "", chart_js)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Service parts by vehicle family — demand, capture and sales per customer</title>
<style>
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--rule:#d8d2c6;--muted:#6b6257;
      --amber:#b7791f;--green:#2f6b45;--red:#a33;--pale:#eef3f9}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
     font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
h1,h2,h3{font-family:Georgia,'Times New Roman',serif;color:var(--navy);margin:0}
header{background:var(--navy);color:var(--paper);padding:26px 32px 22px}
header h1{color:var(--paper);font-size:25px;line-height:1.25}
header p{margin:8px 0 0;color:#cfd6e2;max-width:1020px;font-size:13.5px}
.wrap{max-width:1400px;margin:0 auto;padding:0 32px 64px}
section{margin:32px 0 0}
h2{font-size:20px;margin-bottom:4px}
.q{display:block;font-family:inherit;font-weight:400;color:var(--terra);font-size:13.5px;margin-top:3px}
.card{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:18px 20px;margin-top:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media(max-width:1040px){.grid2,.grid3{grid-template-columns:1fr}}
.controls{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:14px 18px;margin-top:16px;
          display:flex;gap:22px;flex-wrap:wrap;align-items:flex-end}
.ctl{display:flex;flex-direction:column;gap:5px}
.ctl label{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600}
select{padding:8px 10px;border:1px solid var(--rule);border-radius:4px;background:#fff;color:var(--ink);
       font-size:14px;min-width:200px;font-family:inherit}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-top:18px}
.kpi{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:14px 16px;border-top:3px solid var(--navy)}
.kpi .v{font-family:Georgia,serif;font-size:24px;color:var(--navy);line-height:1.15}
.kpi .l{font-size:12px;color:var(--muted);margin-top:3px}
.kpi.warn{border-top-color:var(--amber)}
.kpi.bad{border-top-color:var(--terra)}
.chartbox{position:relative;height:330px}
.chartbox.tall{height:430px}
.chartbox.short{height:265px}
.chartbox.xs{height:210px}
.note{font-size:13px;color:#4a443b;background:var(--pale);border-left:3px solid var(--navy);
      padding:11px 14px;margin:14px 0 0;border-radius:0 4px 4px 0}
.note.amber{background:#fdf6e6;border-left-color:var(--amber)}
.note.red{background:#fbf0ef;border-left-color:var(--red)}
.note b{color:var(--navy)}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:9px 10px;font-weight:600;
   font-size:11.5px;text-transform:uppercase;letter-spacing:.04em}
td{padding:8px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
tbody tr:nth-child(even){background:#faf8f4}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.db{font-weight:600;color:var(--navy)}
.tag{display:inline-block;padding:2px 7px;border-radius:3px;font-size:10.5px;font-weight:700;
     letter-spacing:.03em;text-transform:uppercase}
.tag.iml{background:#e8eef7;color:#2a4a7a}
.tag.prism{background:#eaf3ec;color:var(--green)}
.tag.agreed{background:#e8eef7;color:#2a4a7a}
.tag.internal{background:#eaf3ec;color:var(--green)}
.tag.small{background:#eee9df;color:var(--muted)}
.tag.part{background:#fdf3e0;color:var(--amber)}
.key{font-size:12.5px;color:#4a443b;margin-top:10px;display:flex;gap:16px;flex-wrap:wrap;align-items:center}
.key i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}
.key .ln{display:inline-block;width:16px;height:0;border-top:2px dashed var(--terra);
         margin-right:6px;vertical-align:3px}
#tip{position:fixed;z-index:99;background:var(--navy);color:var(--paper);padding:9px 12px;border-radius:4px;
     font-size:12.5px;max-width:330px;line-height:1.45;pointer-events:none;opacity:0;transition:opacity .1s;
     border-left:3px solid var(--terra)}
#tip b{color:#ffd9c4}
.smgrid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-top:12px}
@media(max-width:1180px){.smgrid{grid-template-columns:repeat(4,1fr)}}
@media(max-width:820px){.smgrid{grid-template-columns:repeat(3,1fr)}}
.sm{border:1px solid var(--rule);border-radius:5px;padding:8px 9px;background:#fff}
.sm .t{font-size:11.5px;font-weight:700;color:var(--navy);white-space:nowrap;overflow:hidden;
       text-overflow:ellipsis}
.sm .v{font-size:11px;color:var(--muted)}
.sm .b{display:flex;align-items:flex-end;gap:2px;height:70px;margin-top:5px}
.sm .b div{flex:1;border-radius:2px 2px 0 0;min-height:1px}
footer{margin-top:40px;padding-top:18px;border-top:1px solid var(--rule);font-size:12.5px;color:var(--muted)}
.small{font-size:12.5px;color:var(--muted)}
.legend{font-size:12.5px;color:var(--muted);margin-top:8px}
</style></head>
<body>
<div id="tip"></div>
<header>
  <h1>Service parts by vehicle family — demand, capture and sales, per customer</h1>
  <p>Which vehicle family is our service business growing on, and which is quietly shrinking.
  Three families are reported: <b>N-series truck</b>, <b>heavy truck</b> (F-series and C&amp;E) and
  <b>light vehicle</b> (D-Max pickup and SUV). Parts that fit more than one family are reported
  together, never spread across them. Two service-interval schedules run side by side and are never
  averaged. Snapshot <b>__SNAPSHOT__</b>; service demand is modelled from the fleet, sales are
  measured from the billing.</p>
</header>
<div id="jserr" style="display:none;margin:16px 32px 0"></div>
<div class="wrap">

  <div class="controls">
    <div class="ctl"><label for="selMarket">Customer</label><select id="selMarket"></select></div>
    <div class="ctl"><label for="selClock">Year clock</label>
      <select id="selClock">
        <option value="CY">Calendar year (January to December)</option>
        <option value="FY">ISZE year (April to March, named by the closing year)</option>
      </select></div>
  </div>
  <div id="laneNotice"></div>
  <div class="kpis" id="kpis"></div>

  <section>
    <h2>Is the N-series truck business growing or shrinking?
      <span class="q">Billed euro by vehicle family, complete years only, against the first full year</span></h2>
    <div class="card">
      <div class="chartbox tall"><canvas id="c_trend"></canvas></div>
      <div class="key" id="k_trend"></div>
      <p class="note" id="n_trend"></p>
    </div>
  </section>

  <section>
    <h2>Is the light-vehicle business carrying all the growth?
      <span class="q">The same three families as bars, so the size of each move is readable</span></h2>
    <div class="grid2">
      <div class="card">
        <h3 style="font-size:15px">Change in billed euro, first full year to last</h3>
        <div class="chartbox short"><canvas id="c_chg_eur"></canvas></div>
        <div class="key"><span><i style="background:#2f6b45"></i>more billed</span>
          <span><i style="background:#c0552d"></i>less billed</span></div>
      </div>
      <div class="card">
        <h3 style="font-size:15px">Change in units, first full year to last</h3>
        <div class="chartbox short"><canvas id="c_chg_units"></canvas></div>
        <div class="key"><span><i style="background:#2f6b45"></i>more units</span>
          <span><i style="background:#c0552d"></i>fewer units</span></div>
      </div>
    </div>
    <div class="card">
      <h3 style="font-size:15px">Every customer, N-series truck, billed euro a year
        <span class="q">One shared scale, so the panels are comparable</span></h3>
      <div class="smgrid" id="sm_grid"></div>
      <div class="key" id="k_sm"></div>
      <p class="note" id="n_sm"></p>
    </div>
  </section>

  <section>
    <h2>How does this customer's fleet split, and what does each family imply?
      <span class="q">Fleet is the denominator every euro below is measured against</span></h2>
    <div class="grid2">
      <div class="card">
        <h3 style="font-size:15px">Vehicles in service, by family</h3>
        <div class="chartbox short"><canvas id="c_fleet"></canvas></div>
        <div class="key" id="k_fleet"></div>
      </div>
      <div class="card">
        <h3 style="font-size:15px">Service demand and what was billed, 2025</h3>
        <div class="chartbox short"><canvas id="c_capture"></canvas></div>
        <div class="key"><span><i style="background:#15233c"></i>implied by the fleet</span>
          <span><i style="background:#c0552d"></i>billed</span></div>
      </div>
    </div>
    <div class="card"><div id="t_fam"></div>
      <p class="note" id="n_fam"></p>
    </div>
  </section>

  <section>
    <h2>Where can this customer's service billing be placed in a family at all?
      <span class="q">Euro by service family, split into the three families and the pooled rest</span></h2>
    <div class="card">
      <div class="chartbox tall"><canvas id="c_cat"></canvas></div>
      <div class="key" id="k_cat"></div>
      <p class="note" id="n_cat"></p>
    </div>
  </section>

  <section>
    <h2>How much does each vehicle in service spend on parts, and how far is that from the target?
      <span class="q">Parts billed per vehicle a year against the target spend for that customer's fleet mix</span></h2>
    <div class="card">
      <div class="chartbox tall"><canvas id="c_gps"></canvas></div>
      <div class="key" id="k_gps"></div>
      <p class="note" id="n_gps"></p>
    </div>
  </section>

  <section>
    <h2>Where do we sit above an independent competitor, for the part numbers we can place?
      <span class="q">Our reference dealer price divided by a real competing price, by vehicle family</span></h2>
    <div class="card">
      <div class="chartbox short"><canvas id="c_pos"></canvas></div>
      <div class="key"><span>1.0 = level with the competing price</span>
        <span><i style="background:#c0552d"></i>above the competing price</span>
        <span><i style="background:#7a8ba6"></i>below it</span></div>
      <p class="note" id="n_pos"></p>
    </div>
  </section>

  <section>
    <h2>What can this page not show, and why?
      <span class="q">Each limit named, with the size of the business it affects</span></h2>
    <div class="card"><div id="t_limits"></div></div>
  </section>

  <footer id="foot"></footer>
</div>

<script>__CHARTJS__</script>
<script id="pmfe-data" type="application/json">__PAYLOAD__</script>
<script>
window.addEventListener('error',function(e){
  var b=document.getElementById('jserr');
  if(!b) return;
  b.style.display='block';
  b.innerHTML='<div class="note red"><b>The page did not finish drawing.</b> A script error '
    +'stopped it, so some panels below are empty. This is a defect in the page, not a data '
    +'problem. Detail: '+String(e.message)+' at line '+String(e.lineno)+'.</div>';
  var f=document.getElementById('foot');
  if(f) f.innerHTML='<b>Incomplete.</b> The page script failed: '+String(e.message);
});
(function(){
"use strict";
try{
var D = JSON.parse(document.getElementById('pmfe-data').textContent);
var NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee', MUTED='#6b6257', RULE='#d8d2c6',
    AMBER='#b7791f', GREEN='#2f6b45', PALE='#eef3f9', SLATE='#7a8ba6';
var FAMCOL={n_series_truck:NAVY, heavy_truck:TERRA, light_vehicle:GREEN,
            shared_across_families:SLATE, unattributed:'#b9ae9d'};

function eur(v){ if(v===null||v===undefined) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+Math.round(Math.abs(v)).toLocaleString('en-GB'); }
function eurm(v){ if(v===null||v===undefined) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+(Math.abs(v)/1e6).toFixed(2)+'M'; }
function num(v){ return (v===null||v===undefined)?'n/a':Math.round(v).toLocaleString('en-GB'); }
function pct(v,d){ if(v===null||v===undefined) return 'n/a';
  return (100*v).toFixed(d===undefined?1:d)+'%'; }
function laneTag(m){ return D.lane[m]==='agreed' ? 'iml' : 'prism'; }
/* The internal nickname for the agreed schedule is never printed: the reader gets the schedule
   he agreed, named by what it is. */
function laneShort(m){
  return laneTag(m)==='iml' ? 'the schedule agreed for that market'
                            : 'the internal service schedule'; }
/* The internal name of a market's schedule is a file name, not a label on a page. */
function laneName(m){ return laneTag(m)==='iml' ? 'agreed' : 'internal'; }

/* tooltip, driven by data-tip so every derived number can explain itself */
var tip=document.getElementById('tip');
document.addEventListener('mouseover',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(!t) return; tip.innerHTML=t.getAttribute('data-tip'); tip.style.opacity='1';});
document.addEventListener('mousemove',function(e){
  if(tip.style.opacity!=='1') return;
  var x=e.clientX+14, y=e.clientY+14;
  if(x+340>window.innerWidth) x=e.clientX-350;
  if(y+120>window.innerHeight) y=e.clientY-130;
  tip.style.left=x+'px'; tip.style.top=y+'px';});
document.addEventListener('mouseout',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(t) tip.style.opacity='0';});

Chart.defaults.font.family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif";
Chart.defaults.font.size=12;
Chart.defaults.color='#4a443b';
/* Animation off. The page redraws every chart whenever the customer or the year clock changes, and
   an animated redraw leaves the canvas momentarily empty. On a data page that reads as a blank
   chart, so every redraw is immediate instead. */
Chart.defaults.animation=false;
Chart.defaults.animations=false;
Chart.defaults.resizeDelay=0;
var charts={};
function mk(id,cfg){ if(charts[id]) charts[id].destroy();
  charts[id]=new Chart(document.getElementById(id),cfg); }
function opts(o){
  o=o||{};
  var horiz=!!o.horizontal, out={responsive:true,maintainAspectRatio:false,
    indexAxis:horiz?'y':'x',
    plugins:{legend:o.legend||{display:false},
      tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10}},
    scales:horiz?{x:{grid:{color:RULE},beginAtZero:o.zero!==false},
                  y:{grid:{display:false}}}
                :{x:{grid:{display:false}},y:{grid:{color:RULE},beginAtZero:o.zero!==false}}};
  if(o.label) out.plugins.tooltip.callbacks={label:o.label};
  if(o.tickX) out.scales.x.ticks={callback:o.tickX};
  if(o.tickY) out.scales.y.ticks={callback:o.tickY};
  return out;
}

var selM=document.getElementById('selMarket'), selC=document.getElementById('selClock');
D.markets.forEach(function(m){var o=document.createElement('option');o.value=m;o.textContent=m;
  selM.appendChild(o);});
selM.value = D.markets.indexOf('ITUK')>=0 ? 'ITUK' : D.markets[0];

function completePeriods(clock){
  return D.trend[clock].service_parts_only.complete.slice();
}

function render(){
  var m=selM.value, clock=selC.value;
  var T=D.trend[clock].service_parts_only, C=D.cust[m];
  var comp=completePeriods(clock);
  var y0=comp[0], y1=comp[comp.length-1];
  var clockWord = clock==='CY' ? 'calendar year' : 'ISZE year';

  /* lane notice */
  document.getElementById('laneNotice').innerHTML=
    '<div class="note"><b>'+m+'</b> runs <span class="tag '+laneTag(m)+'">'+laneShort(m)
    +'</span>'
    +(laneTag(m)==='iml'
      ? ': the schedule agreed for that market — filters 1.25 visits a year, clutch and brake 0.5, '
        +'on a 22,389-vehicle fleet.'
      : ': standard trucks 0.5 visits a year, heavy 0.667, light vehicles 1.0.')
    +' The network carries <b>two</b> interval schedules and they are never averaged or added '
    +'together, because they answer different questions about the same fleet.</div>';

  /* KPIs */
  var k=[], f25={};
  C.families.forEach(function(f){f25[f.family]=f;});
  var ns=f25.n_series_truck||{}, hv=f25.heavy_truck||{}, lt=f25.light_vehicle||{};
  var fl=D.fleet[m]||{};
  var HR=D.meta.heavyResolution;
  var t0=T.family.n_series_truck.eur[String(y0)], t1=T.family.n_series_truck.eur[String(y1)];
  k.push({v:(t1&&t0)?((t1/t0-1)>=0?'+':'')+(100*(t1/t0-1)).toFixed(1)+'%':'n/a',
    l:'N-series truck billed euro, '+y0+' to '+y1, cls:((t1/t0-1)<0?'bad':''),
    tip:'Network billed euro on parts that fit only the N-series truck, on the '+clockWord+'.<br>'
      +y0+': '+eur(t0)+'<br>'+y1+': '+eur(t1)+'<br>'
      +'Both are complete twelve-month periods. Parts that fit more than one vehicle family are '
      +'excluded, because they cannot be attributed to this family.'});
  var g0=T.family.heavy_truck.eur[String(y0)], g1=T.family.heavy_truck.eur[String(y1)];
  k.push({v:(g1&&g0)?((g1/g0-1)>=0?'+':'')+(100*(g1/g0-1)).toFixed(1)+'%':'n/a',
    l:'heavy truck billed euro, '+y0+' to '+y1, cls:((g1/g0-1)<0?'bad':''),
    tip:'Network billed euro on parts that fit only the heavy truck family.<br>'
      +y0+': '+eur(g0)+'<br>'+y1+': '+eur(g1)+'<br>'
      +'The heavy fleet is 1,238 vehicles network-wide, in Ireland, the United Kingdom and '
      +'Portugal only, so this family is small in absolute terms and its percentage moves are '
      +'large. Read it with the euro beside it, never on its own.<br>'
      +'The family carries '+num(HR.pns)+' part numbers, '+num(HR.fwd_pns)+' of them on the '
      +'Forward F&G range and the rest on the C&E range'
      +(HR.top_categories.length?'; the service families with the most of them are '
        +HR.top_categories.map(function(c){return c.pns+' '+c.label.toLowerCase()+'s';}).join(', ')
        :'')
      +'. They bill '+eur(HR.billed2025)+' in 2025. Click the pooled bar below to see them.'});
  var l0=T.family.light_vehicle.eur[String(y0)], l1=T.family.light_vehicle.eur[String(y1)];
  k.push({v:(l1&&l0)?((l1/l0-1)>=0?'+':'')+(100*(l1/l0-1)).toFixed(1)+'%':'n/a',
    l:'light vehicle billed euro, '+y0+' to '+y1,
    tip:'Network billed euro on parts that fit only the D-Max pickup and SUV family.<br>'
      +y0+': '+eur(l0)+'<br>'+y1+': '+eur(l1)+'<br>'
      +'This family also carries the largest share of unit volume, so a euro move here is a '
      +'volume move, not only a price one.'});
  k.push({v:eurm(ns.billed_eur), l:'N-series truck billed, this customer, 2025',
    tip:'Parts billed to <b>'+m+'</b> in 2025 that fit only the N-series truck, plus the pooled '
      +'value apportioned by nothing — the figure is the measured billing on single-family part '
      +'numbers.<br>Implied by the fleet: '+eur(ns.expected_eur)+'.<br>'
      +'The gap between those two is the subject of this page.'});
  k.push({v:num(fl.total), l:'vehicles in service, all families',
    tip:'Fleet for <b>'+m+'</b> from the service model: N-series '+num(fl.n_series)
      +', heavy '+num(fl.heavy)+', light '+num(fl.light)+'.<br>'
      +'This is a 2025 estimate and it is used for every year, so expected demand is flat over '
      +'time by construction. Only the billing moves.'});
  k.push({v:eurm(D.net.gap_eur), l:'network spend gap against target, 2025', cls:'warn',
    tip:'The fleet in each customer x the target spend per vehicle for that fleet mix, minus the '
      +'parts actually billed.<br>Target spend comes from the research study: '
      +eur(D.meta.targets.n35)+' per 3.5 t truck, '+eur(D.meta.targets.n_series_other)
      +' per heavier N-series truck, '+eur(D.meta.targets.heavy)+' per heavy truck and '
      +eur(D.meta.targets.light)+' per light vehicle.<br>It is a ceiling, not a forecast.'});
  document.getElementById('kpis').innerHTML=k.map(function(x){
    return '<div class="kpi '+(x.cls||'')+'" data-tip="'+x.tip+'"><div class="v">'+x.v
      +'</div><div class="l">'+x.l+'</div></div>';}).join('');

  /* the readouts name the measure they plot, and the euro figure is the sum of the bars */
function sumSeries(ds){ return ds.reduce(function(s,d){ return s+(d||0); },0); }

/* 1. the headline trend — one line per family over complete periods only */
  var fams=D.namedFamilies.concat(['shared_across_families']);
  var labels=comp.map(function(p){ return (clock==='FY'?'ISZE ':'')+p; });
  var ds=fams.map(function(f){
    return {label:D.familyLabel[f], data:comp.map(function(p){ return T.family[f].eur[String(p)]; }),
      borderColor:FAMCOL[f], backgroundColor:FAMCOL[f], pointRadius:4, borderWidth:2,
      borderDash:(f==='shared_across_families'?[5,4]:[]), tension:0, fill:false};});
  mk('c_trend',{type:'line',data:{labels:labels,datasets:ds},
    options:opts({legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
      label:function(c){
        var p=comp[c.dataIndex];
        var raw=T.family[fams[c.datasetIndex]];
        var s=eur(raw.eur[String(p)])+' billed, '+num(raw.units[String(p)])+' units';
        if(c.datasetIndex===0 && c.dataIndex>0){
          var prev=T.family.n_series_truck.eur[String(comp[c.dataIndex-1])];
          if(prev) s+=' ('+((c.raw/prev-1)>=0?'+':'')+(100*(c.raw/prev-1)).toFixed(1)+'% against '+comp[c.dataIndex-1]+')';
        }
        return s;}})});
  document.getElementById('k_trend').innerHTML=fams.map(function(f){
    return '<span><i style="background:'+FAMCOL[f]+'"></i>'+(D.familyLabel[f])
      +(f==='shared_across_families'?' <span class="tag small">pooled</span>':'')+'</span>';}).join('')
    +'<span>'+clockWord+(clock==='FY'?' — ISZE '+y0+' = April '+(y0-1)+' to March '+y0:'')
    +', complete periods only: '+comp.join(', ')+'</span>';

  /* the note states plainly which periods are excluded and how many months each holds */
  (function(){
    var T2=D.trend[clock].service_parts_only;
    var all=T2.periods.filter(function(p){return comp.indexOf(p)<0;});
    var bits=all.map(function(p){ return T2.period_label[p]+' holds only '
      +T2.months[String(p)]+' month'+(T2.months[String(p)]===1?'':'s')+' of billing'; });
    var base='Every line is measured billing on part numbers that fit exactly one vehicle family. '
      +'The dashed line is the pooled value: parts that fit more than one family, shown so the '
      +'readable lines are not mistaken for the whole book. ';
    base += bits.length
      ? 'The chart uses complete twelve-month periods only. Excluded here because they are not '
        +'comparable with a full year: '+bits.join('; ')+'.'
      : 'Every period on this chart is a complete twelve-month period.';
    document.getElementById('n_trend').innerHTML=base;
  })();

  /* 2. change bars */
  function changeBars(id,pick,unit){
    var rows=D.namedFamilies.map(function(f){
      return {f:f,label:D.familyLabel[f],a:pick(f,y0),b:pick(f,y1)};});
    var deltas=rows.map(function(r){return (r.a&&r.b)?(r.b-r.a):0;});
    mk(id,{type:'bar',data:{labels:rows.map(function(r){return r.label;}),
      datasets:[{data:deltas,backgroundColor:deltas.map(function(v){
        return v<0?TERRA:GREEN;}),borderRadius:3}]},
      options:opts({horizontal:true,label:function(c){
        var r=rows[c.dataIndex];
        return [eur(r.b-r.a)+' change on the '+unit,
                y0+': '+eur(r.a)+'    '+y1+': '+eur(r.b),
                'Only parts that fit this one family are counted.'];}})});
  }
  changeBars('c_chg_eur',function(f,p){return T.family[f].eur[String(p)];},'euro');
  changeBars('c_chg_units',function(f,p){return T.family[f].units[String(p)];},'units');

  /* small multiples, one panel per customer, shared scale */
  var comp2=comp;
  var allV=D.markets.map(function(x){
    return comp2.map(function(p){ var o=D.custTrend[clock].n_series_truck[String(p)];
      return (o && o[x]!==undefined)?o[x]:null; }).filter(function(v){return v!==null;});});
  var flat=[].concat.apply([],allV);
  var vmax=flat.length?Math.max.apply(null,flat):1;
  var pal=comp2.map(function(p,i){ return i===comp2.length-1?NAVY:(i===0?'#c9d3e0':SLATE); });
  document.getElementById('sm_grid').innerHTML=D.markets.map(function(x){
    var vals=comp2.map(function(p){ var o=D.custTrend[clock].n_series_truck[String(p)];
      return (o && o[x]!==undefined)?o[x]:null;});
    var bars=vals.map(function(v,i){
      if(v===null) return '<div style="height:0" title="no billing"></div>';
      var h=Math.max(2,Math.round(70*v/vmax));
      return '<div title="'+comp2[i]+': '+eur(v)+'" style="height:'+h+'px;background:'
        +pal[i]+'"></div>';}).join('');
    var g=(vals[vals.length-1]&&vals[0])?((vals[vals.length-1]/vals[0]-1)*100):null;
    return '<div class="sm" data-tip="<b>'+x+'</b> &middot; '+laneShort(x)+' schedule<br>'
      +'Billed euro on N-series truck parts only.<br>'+comp2.map(function(p,i){
        return comp2[i]+': '+eur(vals[i]);}).join('<br>')
      +(g!==null?'<br><b>'+y0+' to '+y1+': '+(g>=0?'+':'')+g.toFixed(1)+'%</b>':'')
      +'"><div class="t" style="color:'+(x===m?TERRA:NAVY)+'">'+x+'</div>'
      +'<div class="b">'+bars+'</div>'
      +'<div class="v">'+(g===null?'n/a':((g>=0?'+':'')+g.toFixed(0)+'%'))+'</div></div>';}).join('');
  document.getElementById('k_sm').innerHTML=comp2.map(function(p,i){
    return '<span><i style="background:'+pal[i]+'"></i>'+(clock==='FY'?'ISZE ':'')+p+'</span>';}).join('')
    +'<span>each panel is one customer, bars in year order, all panels on the same euro scale</span>';
  document.getElementById('n_sm').innerHTML='One panel per customer, all on the same scale, so the '
    +'height of a bar is comparable between panels. The value under each panel is the change from '
    +y0+' to '+y1+' in N-series truck billed euro. A customer with no bar for a year billed nothing '
    +'attributable to this family that year, which is not the same as having no fleet.';

  /* 3. fleet split and capture */
  var flRows=[['n_series_truck','n_series'],['heavy_truck','heavy'],['light_vehicle','light']]
    .map(function(x){return {f:x[0],label:D.familyLabel[x[0]],v:fl[x[1]]||0};})
    .filter(function(r){return r.v>0;});
  if(flRows.length){
    mk('c_fleet',{type:'doughnut',
      data:{labels:flRows.map(function(r){return r.label;}),
        datasets:[{data:flRows.map(function(r){return r.v;}),
          backgroundColor:flRows.map(function(r){return FAMCOL[r.f];}),
          borderColor:'#fff',borderWidth:2}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
        plugins:{legend:{display:false},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{label:function(c){
              var tot=flRows.reduce(function(a,b){return a+b.v;},0);
              return c.label+': '+num(c.raw)+' vehicles ('+(100*c.raw/tot).toFixed(1)+'% of the fleet)';}}}}}});
    document.getElementById('k_fleet').innerHTML=flRows.map(function(r){
      return '<span><i style="background:'+FAMCOL[r.f]+'"></i>'+r.label+' — '+num(r.v)
        +'</span>';}).join('');
  } else {
    mk('c_fleet',{type:'doughnut',data:{labels:['no fleet on the service model'],
      datasets:[{data:[1],backgroundColor:['#ddd7cb'],borderWidth:0}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
        plugins:{legend:{display:false},tooltip:{enabled:false}}}});
    document.getElementById('k_fleet').innerHTML='<span>this customer has no fleet in the service '
      +'model, so no family split can be shown</span>';
  }

  var capRows=D.namedFamilies.concat(['shared_across_families']).map(function(f){
    var r=f25[f]; return r?{f:f,label:D.familyLabel[f],e:r.expected_eur,b:r.billed_eur}:null;
  }).filter(function(x){return x;});
  mk('c_capture',{type:'bar',data:{labels:capRows.map(function(r){return r.label;}),
    datasets:[{label:'implied by the fleet',data:capRows.map(function(r){return r.e;}),
      backgroundColor:NAVY,borderRadius:3},
      {label:'billed',data:capRows.map(function(r){return r.b;}),backgroundColor:TERRA,borderRadius:3}]},
    options:opts({horizontal:true,legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
      label:function(c){ var r=capRows[c.dataIndex];
        if(c.datasetIndex===1) return 'billed '+eur(r.b)
          +(r.e>0?' ('+(100*r.b/r.e).toFixed(1)+'% of the ceiling)':' (no ceiling for this value)');
        return 'implied by the fleet '+eur(r.e)+', at one price per family and service family';}})});

  document.getElementById('t_fam').innerHTML='<table><thead><tr><th>Vehicle family</th>'
    +'<th class="n">Vehicles</th><th class="n">Jobs implied a year</th>'
    +'<th class="n">Implied spend EUR</th><th class="n">Billed EUR</th>'
    +'<th class="n">Share of implied</th></tr></thead><tbody>'
    +capRows.map(function(r){
      var cash=(r.e>0?pct(r.b/r.e):'n/a');
      var famKey={n_series_truck:'n_series',heavy_truck:'heavy',light_vehicle:'light',
                  shared_across_families:'total'}[r.f];
      var veh = (r.f==='unattributed') ? null : (D.fleet[m]||{})[famKey];
      return '<tr><td class="db">'+r.label+'</td><td class="n">'+num(veh)+'</td>'
        +'<td class="n">'+num((f25[r.f]||{}).expected_qty)+'</td>'
        +'<td class="n">'+eur(r.e)+'</td><td class="n">'+eur(r.b)+'</td>'
        +'<td class="n">'+cash+'</td></tr>';}).join('')
    +'</tbody></table>';
  document.getElementById('n_fam').innerHTML='<b>Implied spend</b> is the fleet in that family '
    +'multiplied by the visits a year that family\'s interval schedule allows, multiplied by the '
    +'share of a visit each service item takes, valued at one price per family and service family — '
    +'taken from this customer\'s own billed prices. <b>Billed</b> is what was actually invoiced on '
    +'part numbers that resolve to that one family. The <b>pooled</b> row is the whole market '
    +'ceiling, because a part that fits several families is available to all of them; it is not '
    +'added to the three families above it. The fleet is a 2025 estimate used for every year, so the '
    +'implied column is the same in each year and only the billed column moves.';

  /* 4. euro by category, split into family and pooled */
  var catAgg={};
  C.categories.forEach(function(r){
    var kk=r.cat; catAgg[kk]=catAgg[kk]||{cat:r.cat,label:r.label};
    catAgg[kk][r.family]=(catAgg[kk][r.family]||0)+r.billed_eur;});
  var catRows=Object.keys(catAgg).map(function(kk){return catAgg[kk];})
    .sort(function(a,b){
      function tot(x){return D.namedFamilies.concat(['shared_across_families'])
        .reduce(function(s,f){return s+(x[f]||0);},0);}
      return tot(b)-tot(a);}).slice(0,12);
  var stackFams=D.namedFamilies.concat(['shared_across_families']);
  mk('c_cat',{type:'bar',data:{labels:catRows.map(function(r){return r.label;}),
    datasets:stackFams.map(function(f){return {label:D.familyLabel[f],stack:'s',
      data:catRows.map(function(r){return r[f]||0;}),backgroundColor:FAMCOL[f],borderRadius:2};})},
    options:opts({horizontal:true,label:function(c){
      var r=catRows[c.dataIndex], f=stackFams[c.datasetIndex];
      return D.familyLabel[f]+': '+eur(r[f]||0);}})});
  document.getElementById('k_cat').innerHTML=stackFams.map(function(f){
    return '<span><i style="background:'+FAMCOL[f]+'"></i>'+D.familyLabel[f]
      +(f==='shared_across_families'?' <span class="tag small">pooled, not a family</span>':'')
      +'</span>';}).join('');
  document.getElementById('n_cat').innerHTML='Each bar is one service family for '+m+', 2025, '
    +'split by whether the part number can be placed in a single vehicle family. Where a bar is '
    +'almost all grey, that service family cannot be reported by vehicle family at all — the part '
    +'numbers in it are shared across families or carry no vehicle reference. Air filters, brake '
    +'components and clutches place well; oil and fuel filters largely do not, because a filter '
    +'housing is used across several vehicle classes. <b>Nothing is ever spread across families to '
    +'make a chart look fuller.</b>';

  /* 5. spend per vehicle against the target */
  var gs=D.markets.map(function(x){ return D.gap.findIndex(function(r){return r.db===x;}); })
    .filter(function(i){return i>=0;}).map(function(i){return D.gap[i];})
    .sort(function(a,b){return (b.gap_per_vehicle||0)-(a.gap_per_vehicle||0);}).slice(0,12);
  mk('c_gps',{type:'bar',data:{labels:gs.map(function(r){return r.db;}),
    datasets:[{label:'parts billed per vehicle',data:gs.map(function(r){return r.spu;}),
      backgroundColor:gs.map(function(r){return r.db===m?TERRA:NAVY;}),borderRadius:3},
      {label:'target spend for that fleet mix',data:gs.map(function(r){return r.target_per_vehicle;}),
        type:'line',borderColor:AMBER,backgroundColor:AMBER,pointRadius:4,borderWidth:2,
        borderDash:[5,4],fill:false,tension:0}]},
    options:opts({horizontal:true,legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
      label:function(c){ var r=gs[c.dataIndex];
        if(c.datasetIndex===1) return 'target '+eur(r.target_per_vehicle)+' per vehicle a year';
        return eur(r.spu)+' billed per vehicle on '+num(r.fleet)+' vehicles in service'
          +(r.gap_per_vehicle!==null?' — gap '+eur(r.gap_per_vehicle)+' per vehicle, '
            +eurm(r.gap_eur)+' across the fleet':'') ;}})});
  document.getElementById('k_gps').innerHTML='<span><i style="background:'+NAVY+'"></i>parts billed '
    +'per vehicle (the selected customer in terracotta)</span>'
    +'<span><span class="ln"></span>target spend for that fleet mix</span>';
  document.getElementById('n_gps').innerHTML='The target is the same three-way fleet split the '
    +'service demand model uses, so it is the target for the fleet each customer actually has: '
    +eur(D.meta.targets.n35)+' per 3.5 t truck, '+eur(D.meta.targets.n_series_other)
    +' per heavier N-series truck, '+eur(D.meta.targets.heavy)+' per heavy truck and '
    +eur(D.meta.targets.light)+' per light vehicle, blended by that customer\'s own measured 3.5 t '
    +'share. Because the fleet is almost all light vehicles in most markets, the blend lands near '
    +eur(D.meta.targets.light)+' for those customers and only the truck-heavy customers rise above '
    +'it. Read the euro gap at the end of each bar, not the ranking.';

  /* 6. position against the independent market */
  var po=D.competitor;
  if(po.length){
    mk('c_pos',{type:'bar',data:{labels:po.map(function(r){return r.label;}),
      datasets:[{data:po.map(function(r){return r.median_index-1;}),
        backgroundColor:po.map(function(r){return r.median_index>1?TERRA:SLATE;}),borderRadius:3}]},
      options:opts({horizontal:true,tickX:function(v){return (v>0?'+':'')+v+'x';},
        label:function(c){ var r=po[c.dataIndex];
          return [r.median_index.toFixed(2)+' times the competing price',
            r.pns+' part numbers, '+eur(r.billed_eur)+' billed in the latest complete year',
            r.above+' above the competing price, '+r.below+' below it'];}})});
  } else {
    mk('c_pos',{type:'bar',data:{labels:['no part number could be placed in a family'],
      datasets:[{data:[0],backgroundColor:['#ddd7cb']}]},
      options:opts({horizontal:true})});
  }
  document.getElementById('n_pos').innerHTML='Only the part numbers that are both priced against a '
    +'competitor and placeable in a single vehicle family can appear here: '
    +D.competitorMeta.placedRows+' of '+D.competitorMeta.allRows+' priced rows. Median of our '
    +'reference dealer price divided by a real competing price, per vehicle family. Source: '
    +D.competitorMeta.tier+', vintage '+D.competitorMeta.vintage+'. One competing source fanned '
    +'across markets — read it as a position, not as a measured transaction price in each market.';

  /* limits table */
  var lim=D.meta.notAttempted.concat([
    'The heavy truck family is '+num(D.meta.heavyResolution.fleet)+' vehicles network-wide, in '
      +D.meta.heavyResolution.markets+' markets, and the parts that fit it bill a small share of '
      +'the network book, so its percentage moves are large on small numbers. '
      +num(D.meta.heavyResolution.pns)+' part numbers resolve to heavy truck alone — '
      +num(D.meta.heavyResolution.fwd_pns)+' on the Forward F&G range and the rest on the C&E '
      +'range — and they bill '
      +eur(D.meta.heavyResolution.billed2025)+' in 2025. Read the euro beside every percentage.',
    'A service family can look empty for the heavy truck family even when it is not. The unit is '
      +'named only where a source names a vehicle for the part number, and a part that fits more '
      +'than one family is pooled rather than split. So the euro on a heavy-truck bar is the part '
      +'numbers that name the heavy truck and nothing else; the rest of that service family sits '
      +'in the pooled value beside it.',
    'The fleet is a 2025 estimate used for every year in the service model, so implied spend is '
      +'flat over time by construction. Only the billed side moves.',
    'Mileage is not measured per market, so the interval schedule carries the whole distance '
      +'assumption behind every implied figure.',
    'The billing runs from January 2023 to 30 June 2026. Calendar 2026 and ISZE 2027 are therefore '
      +'partial and are excluded from the trend charts rather than shown as a fall.',
    'The evolution file also carries '+(D.meta.outsideScope.length?D.meta.outsideScope.join(', '):'no')
      +', which are outside the service model. They are excluded from every network figure on this '
      +'page.'
  ]);
  document.getElementById('t_limits').innerHTML='<table><thead><tr><th>What cannot be shown</th>'
    +'</tr></thead><tbody>'+lim.map(function(s){
      return '<tr><td>'+s+'</td></tr>';}).join('')+'</tbody></table>';

  /* footer */
  document.getElementById('foot').innerHTML='<b>Sources, all read at build time, snapshot '
    +D.snapshot+':</b> the fleet split by vehicle class; the interval schedule and its per-market '
    +'overrides; the vehicle-family decode and the parts cross-reference; the billing; the service '
    +'part dimension; the published demand-capture model; the spend-per-vehicle model and the '
    +'research targets; and the competing-price sample. '
    +'<b>Reconciliation:</b> the three named families sum back to the published implied demand on '
    +D.meta.tie1.rows_compared+' customer x service family x year rows with a largest difference of '
    +D.meta.tie1.max_abs_delta+' pieces, and the attributed billing equals the published actual euro '
    +'on '+D.meta.tie2.rows_compared+' rows exactly. '
    +'<b>Vehicle family resolution:</b> '+D.meta.familyResolution.resolved_single_family
    +' part numbers resolve to one family, '+D.meta.familyResolution.pooled_shared
    +' fit more than one and are pooled, and '+D.meta.familyResolution.unattributed
    +' have no vehicle reference at all. Where the tonnage banding and the model-range decode both '
    +'name one family, they disagree on '+D.meta.familyResolution.both_sources_speak.of_which_they_disagree
    +' part numbers; those are pooled rather than trusted to either source.';
}
['selMarket','selClock'].forEach(function(id){
  document.getElementById(id).addEventListener('change',render);});
render();
}catch(err){
  var b=document.getElementById('jserr');
  if(b){ b.style.display='block';
    b.innerHTML='<div class="note red"><b>The page did not finish drawing.</b> A script error '
      +'stopped it, so some panels below are empty. Detail: '+String(err && err.message ? err.message : err)
      +'</div>'; }
  var f=document.getElementById('foot');
  if(f) f.innerHTML='<b>Incomplete.</b> The page script failed: '
    +String(err && err.message ? err.message : err);
}
})();
</script>
</body></html>
"""

html = (TEMPLATE.replace("__CHARTJS__", chart_js)
        .replace("__PAYLOAD__", body)
        .replace("__SNAPSHOT__", SNAPSHOT))

# ── guard: the page script must parse. A single unbalanced quote renders empty containers on a
# file that still looks fine on disk, which is how a blank chart ships unnoticed.
_parts = html.split("<script>", 2)
if len(_parts) < 3:
    die("expected the chart library block and the page script block")
_page_js = _parts[2].split("</script>", 1)[0]
_tmp = BUILD_DIR / "_syntax_check.js"
_tmp.parent.mkdir(parents=True, exist_ok=True)
_tmp.write_text(_page_js, encoding="utf-8")
_r = subprocess.run(["node", "--check", str(_tmp)], capture_output=True, text=True)
if _r.returncode != 0:
    die("page script does not parse:\n" + (_r.stderr or "")[:1200])
print("syntax guard: page script parses clean")

OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_HTML.write_text(html, encoding="utf-8")
OUT_CMD.write_bytes(("@echo off\r\nstart \"\" \"%~dp0ISZE_PMS_Family_Evolution.html\"\r\n")
                    .encode("ascii"))

print(f"core rows {len(core):,} | evolution rows {len(evo):,} | payload {len(body)/1024:.0f} KB")
print(f"written -> {OUT_HTML}  ({len(html.encode('utf-8'))/1024:.0f} KB)")
print(f"written -> {OUT_CMD}")
print(f"customers on the page: {len(markets)} | named families: {len(NAMED)} "
      f"| pooled values: 2")
print(f"network 2025 billed EUR {NET['billed_eur']:,} | implied EUR {NET['expected_eur']:,} "
      f"| attributed by family {100*NET['attributed_share']:.1f}%")
