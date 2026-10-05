#!/usr/bin/env python3
"""Build the shared PMS / tonnage / AIM evolution page — self-contained HTML.

Answers, for one customer at a time and for the network:
  * how the fleet and the expected service demand split across tonnage bands
  * where modelled service demand concentrates, and the modelled gap by service family
  * how billed euro evolves, on the calendar year AND on the ISZE April-March year
  * which product lines gained or fell in billed parts at AIM level 1 and level 2
  * how GPS spend per vehicle and our price position vs the independent market move

Reads only derived files. Computes nothing that is not traceable to one of them.

Two interval lanes exist and are never blended:
  ITUK     -> IML v7 schedule
  everyone -> the PRISM lane
The build FAILS if any market ever carries two lanes in the band file.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
PD = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"
OUT_DIR = ROOT / "02_dashboards" / "sales"
OUT_HTML = OUT_DIR / "ISZE_PMS_Tonnage_Evolution.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_PMS_Tonnage_Evolution.cmd"
CHARTJS = ROOT / "02_dashboards" / "_ui" / "chart.umd.min.js"

BAND_ORDER = ["LCV_D-Max", "3.5t_N35", "5.5t_N50_N55", "7.5t_N50_N62_N75", "F_series_MD_heavy"]
BAND_SHORT = {
    "LCV_D-Max": "LCV / D-Max",
    "3.5t_N35": "3.5 t (N35 Grafter)",
    "5.5t_N50_N55": "5.5 t (N50 / N55)",
    "7.5t_N50_N62_N75": "7.5 t (N75 / N50 / N62)",
    "F_series_MD_heavy": "F-series / MD (heavy)",
}
CAT_LABEL = {
    "air_filter": "Air filter", "blower_filter": "Blower filter", "brake_pad": "Brake pad",
    "brake_rotor": "Brake rotor", "brake_shoe": "Brake shoe", "clutch_booster": "Clutch booster",
    "clutch_disc": "Clutch disc", "clutch_kit": "Clutch kit",
    "clutch_pressure_plate": "Clutch pressure plate", "fuel_filter": "Fuel filter",
    "oil_filter": "Oil filter", "pilot_bearing": "Pilot bearing",
    "release_bearing": "Release bearing", "urea_filter": "Urea (AdBlue) filter",
}
# The snapshot and the "billed through" date are read from the billing of record at build time.
# Until 2026-09-23 both were typed in ("2026-09-18", "30 June 2026") and went stale while the
# billing underneath had already moved to August.
_BILLED_THROUGH = pd.to_datetime(pd.read_parquet(DER / "sales_fact.parquet",
                                                 columns=["billing_date"]).billing_date).max()
SNAPSHOT = _BILLED_THROUGH.strftime("%Y-%m-%d")
BILLED_THROUGH_TEXT = f"{_BILLED_THROUGH.day} {_BILLED_THROUGH:%B %Y}"


def die(msg: str) -> None:
    print(f"BUILD FAIL: {msg}")
    sys.exit(1)


# ────────────────────────────────────────────────────────────── load
band = pd.read_csv(DER / "pms_tonnage_model.csv")
aim = pd.read_csv(DER / "aim_evolution_model.csv")
cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
gps = pd.read_csv(DER / "gps_spu_by_distributor.csv")
comp = pd.read_csv(DER / "lost_sales_competitor_pn.csv")
shares = pd.read_csv(PD / "uio_ld_n35_share.csv")
summary = pd.read_csv(DER / "pms_summary_by_db.csv")

markets = sorted(band.distributor_code.unique())

# ────────────────────────────────────────────────────────────── guard: one lane per market
lane_map = band.groupby("distributor_code").lane.nunique()
bad = lane_map[lane_map > 1]
if len(bad):
    die(f"a market carries more than one interval lane and must never be averaged: {bad.to_dict()}")
# the interval schedule each market runs. The payload carries which of the two applies, never the
# internal file name for it.
LANE = {m: ("agreed" if "IML" in str(v) else "internal")
        for m, v in band.groupby("distributor_code").lane.first().to_dict().items()}

# the PRISM lane's own categories are the 14 service categories; the IML lane differs and is
# never compared with it in the same aggregate.
assert band.actual_is_market_level.all(), "every actual must be flagged market-level"

# ────────────────────────────────────────────────────────────── per-market blocks
fleet, exp, gap_band, cat_gap, basis_rows = {}, {}, {}, {}, []
for m in markets:
    g = band[band.distributor_code == m]
    bs = []
    for b in BAND_ORDER:
        gb = g[g.band == b]
        if gb.empty:
            continue
        bs.append({
            "band": b, "label": BAND_SHORT[b],
            "uio": round(float(gb.uio_units.max())),
            "visits": round(float(gb.visits_per_year.max()), 3),
            "expected": round(float(gb[gb.year == 2025].expected_qty_per_year.sum())),
            "gap_eur": round(float(gb[gb.year == 2025].gap_eur_band_share.sum())),
        })
    fleet[m] = bs
    exp[m] = bs  # same records; the page reads what it needs

    # service-family attributed gap, 2025 (market level, allocated by expected share)
    g25 = g[g.year == 2025].groupby("pms_category").agg(
        expected=("expected_qty_per_year", "sum"),
        gap=("gap_eur_band_share", "sum"),
        actual=("market_actual_qty", "first"),
    ).reset_index()
    cat_gap[m] = [
        {"cat": r.pms_category, "label": CAT_LABEL.get(r.pms_category, r.pms_category),
         "expected": round(float(r.expected)), "gap_eur": round(float(r.gap)),
         "actual": round(float(r.actual))}
        for r in g25.itertuples()
    ]

# band measurement basis, straight off the share file. The source file's evidence note is written
# for an internal reader and carries two words that must not reach a page: the internal name of the
# agreed service schedule, and "wallet" where it means what the dealer billed. Both are rewritten
# here once, so the note is never printed raw.
def reader_note(s: str) -> str:
    s = str(s)
    s = s.replace("IML v7", "the schedule agreed for that market")
    s = s.replace("the wallet", "what the dealer bills").replace("wallet", "what the dealer bills")
    return s


for _, r in shares.iterrows():
    basis_rows.append({
        "market": r.distributor_code, "share": float(r.n35_share),
        "basis": str(r.basis), "units": (float(r.units_2025e) if pd.notna(r.units_2025e) else None),
        "note": reader_note(r.evidence_note),
    })

# ────────────────────────────────────────────────────────────── billed euro, both clocks
evo = aim.groupby(["distributor_code", "clock", "period"]).billed_eur.sum().reset_index()
billed = {}
for m in markets:
    for cl in ("CY", "FY"):
        s = evo[(evo.distributor_code == m) & (evo.clock == cl)]
        billed.setdefault(m, {})[cl] = {int(r.period): round(float(r.billed_eur))
                                       for r in s.itertuples()}

# ────────────────────────────────────────────────────────────── AIM level 1 and 2
aim_l1 = aim.groupby(["distributor_code", "clock", "period", "aim_l1"]).billed_eur.sum().reset_index()
L1 = {}
for m in markets:
    L1[m] = {}
    for cl in ("CY", "FY"):
        s = aim_l1[(aim_l1.distributor_code == m) & (aim_l1.clock == cl)]
        L1[m][cl] = [
            {"period": int(r.period), "l1": r.aim_l1, "eur": round(float(r.billed_eur))}
            for r in s.itertuples()
        ]

# AIM level 2 — keep the lines that matter, drop the tail so the page stays a sane size
aim_l2 = aim.groupby(["distributor_code", "clock", "period", "aim_l1", "aim_l2"]).agg(
    eur=("billed_eur", "sum"), pns=("distinct_pns", "max")).reset_index()
L2 = {}
for m in markets:
    s = aim_l2[aim_l2.distributor_code == m]
    top = s.groupby("aim_l2").eur.sum().nlargest(30).index
    s = s[s.aim_l2.isin(top)]
    L2[m] = [
        {"period": int(r.period), "clk": r.clock, "l1": r.aim_l1, "l2": r.aim_l2,
         "eur": round(float(r.eur)), "pns": int(r.pns)}
        for r in s.itertuples()
    ]

# ────────────────────────────────────────────────────────────── capture by market and year
CAP = {}
for m in markets:
    s = cap[(cap.distributor_code == m) & (cap.line_type == "total")]
    CAP[m] = {}
    for y, gy in s.groupby("year"):
        exp_q = float(gy.expected_qty.sum())
        act_q = float(gy.actual_qty.sum())
        CAP[m][int(y)] = {
            "expected": round(exp_q), "actual": round(act_q),
            "capture": (round(act_q / exp_q, 4) if exp_q else None),
            "gap_eur": round(float(gy.revenue_gap_eur.sum())),
            "actual_eur": round(float(gy.actual_rev_eur.sum())),
            "avg_sp": round(float(gy.avg_sp_eur.mean()), 2),
        }

# service-family capture mix for the donut, one market, one family, <=4 segments
FAMMIX = {}
for m in markets:
    s = cap[(cap.distributor_code == m) & (cap.year == 2025)]
    for cat, gc in s.groupby("pms_category"):
        tot = gc[gc.line_type == "total"]
        gen = gc[gc.line_type == "genuine"]
        val = gc[gc.line_type == "bvp"]
        if tot.empty:
            continue
        FAMMIX.setdefault(m, {})[cat] = {
            "total_units": round(float(tot.actual_qty.sum())),
            "total_eur": round(float(tot.actual_rev_eur.sum())),
            "genuine_units": round(float(gen.actual_qty.sum())) if not gen.empty else 0,
            "value_units": round(float(val.actual_qty.sum())) if not val.empty else 0,
        }

# ────────────────────────────────────────────────────────────── GPS and the market layer
GPSU = {}
for m in markets:
    s = gps[gps.distributor_code == m]
    GPSU[m] = [
        {"year": int(r.year), "spu": (round(float(r.spend_per_unit_eur), 1)
                                      if pd.notna(r.spend_per_unit_eur) else None),
         "spu_ex_warranty": (round(float(r.spend_per_unit_ex_warranty_eur), 1)
                             if pd.notna(r.spend_per_unit_ex_warranty_eur) else None),
         "uio": (round(float(r.uio_units)) if pd.notna(r.uio_units) else None),
         "uio_source": str(r.uio_source), "light": str(r.traffic_light),
         "sales_eur": (round(float(r.total_sales_eur)) if pd.notna(r.total_sales_eur) else None)}
        for r in s.itertuples()
    ]

# price position vs the independent market, median index per AIM level 1
POS = {}
for m in markets:
    s = comp[comp.db == m]
    if s.empty:
        continue
    agg = s.groupby("aim_l1").agg(
        idx=("index_reference_vs_competitor", "median"),
        pns=("part_number", "nunique"),
        billed=("billed_eur_latest_complete_cy", "sum"),
        vintage=("vintage", "first"),
    ).reset_index()
    POS[m] = [
        {"l1": r.aim_l1, "idx": round(float(r.idx), 2), "pns": int(r.pns),
         "billed": round(float(r.billed or 0)), "vintage": str(r.vintage)}
        for r in agg.sort_values("idx", ascending=False).itertuples()
    ]

COMP_VINTAGE = str(comp.vintage.mode().iloc[0]) if len(comp) else "n/a"
# Summed from the unrounded source, then rounded once: adding the per-market rounded figures left
# the network total EUR 1 off the source on both lines (fixed 2026-09-23).
_c25 = cap[(cap.line_type == "total") & (cap.year == 2025) & cap.distributor_code.isin(markets)]
NET_GAP_2025 = round(float(_c25.revenue_gap_eur.sum()))
NET_ACT_2025 = round(float(_c25.actual_rev_eur.sum()))

# Scope disclosure: the billing extract carries markets the service model does not cover.
BASE = set(markets)
OUT_MARKETS = sorted(set(aim.distributor_code.unique()) - BASE)
_cy_complete = int(aim[(aim.clock == "CY")].period.max()) - 1  # exclude the incomplete calendar year
_tot = float(aim[(aim.clock == "CY") & (aim.period == _cy_complete)].billed_eur.sum())
_out = float(aim[(aim.clock == "CY") & (aim.period == _cy_complete)
                 & (~aim.distributor_code.isin(BASE))].billed_eur.sum())
SCOPE_NOTE = {
    "markets": OUT_MARKETS,
    "eur": round(_out),
    "sharePct": round(100 * _out / _tot, 1) if _tot else None,
    "completeYear": _cy_complete,
}

PAYLOAD = {
    "snapshot": SNAPSHOT,
    "markets": markets,
    "bands": BAND_ORDER,
    "bandLabels": BAND_SHORT,
    "catLabels": CAT_LABEL,
    "lane": LANE,
    "fleet": fleet,
    "catGap": cat_gap,
    "basis": basis_rows,
    "billed": billed,
    "l1": L1,
    "l2": L2,
    "capture": CAP,
    "famMix": FAMMIX,
    "gps": GPSU,
    "pos": POS,
    "compVintage": COMP_VINTAGE,
    "scopeNote": SCOPE_NOTE,
    "net": {"gap2025": NET_GAP_2025, "actual2025": NET_ACT_2025},
}
body = json.dumps(PAYLOAD, separators=(",", ":"), allow_nan=False)

chart_js = CHARTJS.read_text(encoding="utf-8")
chart_js = re.sub(r"//# sourceMappingURL=\S+", "", chart_js)

HTML = TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Service demand and parts billed evolution by tonnage band</title>
<style>
:root{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--rule:#d8d2c6;--muted:#6b6257;
      --amber:#b7791f;--green:#2f6b45;--red:#a33;--pale:#eef3f9}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
     font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
h1,h2,h3{font-family:Georgia,'Times New Roman',serif;color:var(--navy);margin:0}
header{background:var(--navy);color:var(--paper);padding:26px 32px 22px}
header h1{color:var(--paper);font-size:26px;line-height:1.25}
header p{margin:8px 0 0;color:#cfd6e2;max-width:1000px;font-size:13.5px}
.wrap{max-width:1400px;margin:0 auto;padding:0 32px 64px}
section{margin:30px 0 0}
h2{font-size:20px;margin-bottom:4px}
.q{display:block;font-family:inherit;font-weight:400;color:var(--terra);font-size:13.5px;
   letter-spacing:.02em;margin-top:3px}
.card{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:18px 20px;margin-top:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
@media(max-width:1000px){.grid2,.grid3{grid-template-columns:1fr}}
.controls{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:14px 18px;
          margin-top:16px;display:flex;gap:22px;flex-wrap:wrap;align-items:flex-end}
.ctl{display:flex;flex-direction:column;gap:5px}
.ctl label{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
           font-weight:600}
select{padding:8px 10px;border:1px solid var(--rule);border-radius:4px;background:#fff;
       color:var(--ink);font-size:14px;min-width:190px;font-family:inherit}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-top:18px}
.kpi{background:#fff;border:1px solid var(--rule);border-radius:6px;padding:14px 16px;
     border-top:3px solid var(--navy)}
.kpi .v{font-family:Georgia,serif;font-size:25px;color:var(--navy);line-height:1.15}
.kpi .l{font-size:12px;color:var(--muted);margin-top:3px}
.kpi.warn{border-top-color:var(--amber)}
.chartbox{position:relative;height:330px}
.chartbox.tall{height:420px}
.chartbox.short{height:270px}
.note{font-size:13px;color:#4a443b;background:var(--pale);border-left:3px solid var(--navy);
      padding:11px 14px;margin:14px 0 0;border-radius:0 4px 4px 0}
.note.amber{background:#fdf6e6;border-left-color:var(--amber)}
.note.red{background:#fbf0ef;border-left-color:var(--red)}
.basis-strip{background:#fff;border:1px solid var(--rule);border-left:4px solid var(--navy);
             border-radius:6px;padding:14px 18px;margin-top:16px;font-size:13px;line-height:1.65}
.basis-strip b{color:var(--navy);font-size:11px;text-transform:uppercase;letter-spacing:.05em}
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
.tag.unm{background:#fdf3e0;color:var(--amber)}
.tag.ok{background:#eaf3ec;color:var(--green)}
.chip{display:inline-block;background:var(--pale);border:1px solid var(--rule);border-radius:12px;
      padding:3px 10px;font-size:12px;margin:2px 4px 2px 0;cursor:help;position:relative}
[data-tip]{cursor:help}
.legend{font-size:12.5px;color:var(--muted);margin-top:10px;display:flex;gap:18px;flex-wrap:wrap;
        align-items:center}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;
          vertical-align:-1px}
.legend.axis{font-style:italic}
.legend span{cursor:help}
#tip{position:fixed;z-index:99;background:var(--navy);color:var(--paper);padding:9px 12px;
     border-radius:4px;font-size:12.5px;max-width:320px;line-height:1.45;pointer-events:none;
     opacity:0;transition:opacity .1s;border-left:3px solid var(--terra)}
#tip b{color:#ffd9c4}
footer{margin-top:40px;padding-top:18px;border-top:1px solid var(--rule);font-size:12.5px;
       color:var(--muted)}
.small{font-size:12.5px;color:var(--muted)}
.rankrow{display:grid;grid-template-columns:150px 1fr 96px;gap:10px;align-items:center;
         margin:5px 0;font-size:13px}
.rankrow .bar{height:19px;background:var(--navy);border-radius:2px;min-width:2px}
.rankrow .bar.neg{background:var(--terra)}
.rankrow .val{text-align:right;font-variant-numeric:tabular-nums;font-weight:600}
.smgrid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-top:12px}
.smgrid .lbl{font-size:10.5px;font-weight:600;margin-top:4px;text-align:center;
             white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media(max-width:1180px){.smgrid{grid-template-columns:repeat(4,1fr)}}
@media(max-width:820px){.smgrid{grid-template-columns:repeat(3,1fr)}}
</style></head>
<body>
<div id="tip"></div>
<header>
  <h1>Service demand, capture and parts billed evolution — by tonnage band</h1>
  <p>Primary question: where does expected service demand concentrate across tonnage bands? One
  customer at a time, or the whole network. Tonnage band is the first axis, then service family,
  then time on two clocks: the calendar year, and the ISZE year that runs April to March and is
  named for the year it closes in (the 2026 ISZE year is April 2025 to March 2026).
  Snapshot <b>__SNAPSHOT__</b>. Built from the derived service-demand model, never from live billing.</p>
</header>
<div class="wrap">

  <div class="basis-strip">
    <div><b>Observed</b> — Parts billed through __BILLED_THROUGH__ (market level only)</div>
    <div><b>Modelled</b> — Target spend / service demand by tonnage band (allocated by expected-demand
    shares; not observed at band)</div>
    <div><b>Fleet</b> — Historical fleet basis only; no forward forecast quoted</div>
  </div>

  <div class="controls">
    <div class="ctl"><label for="selMarket">Customer</label><select id="selMarket"></select></div>
    <div class="ctl" style="flex:1;min-width:260px"><label for="selClock">Year clock</label>
      <select id="selClock">
        <option value="CY">Calendar year (Jan–Dec)</option>
        <option value="FY">ISZE year (Apr–Mar) — ISZE 2026 = Apr 2025 – Mar 2026</option>
      </select></div>
    <div class="ctl"><label for="selYear">Year</label><select id="selYear"></select></div>
    <div class="ctl"><label for="selFamily">Service family</label><select id="selFamily"></select></div>
  </div>
  <p class="small" id="clockNote" style="margin:8px 0 0"></p>

  <div id="laneNotice"></div>

  <div class="kpis" id="kpis"></div>

  <section>
    <h2>How does this customer's fleet split across tonnage bands?
      <span class="q">Fleet is the denominator everything else is measured against</span></h2>
    <div class="grid2">
      <div class="card"><div id="h_fleet"><div class="chartbox short"><canvas id="c_fleet"></canvas></div>
        <div class="legend" id="lg_fleet"></div></div></div>
      <div class="card"><div id="h_expected"><div class="chartbox short"><canvas id="c_expected"></canvas></div></div>
        <p class="note" id="n_expected"></p></div>
    </div>
  </section>

  <section>
    <h2>Where is modelled service demand concentrated by tonnage band and service family?
      <span class="q">Expected / modelled by tonnage band — actual billed at market level only</span></h2>
    <div class="card">
      <div id="h_gap"><div class="chartbox tall"><canvas id="c_gap"></canvas></div></div>
      <p class="note amber" id="n_gap"></p>
    </div>
    <div class="grid2">
      <div class="card">
        <h3 style="font-size:15px">Largest modelled gaps by service family</h3>
        <div id="t_catgap"></div>
      </div>
      <div class="card">
        <h3 style="font-size:15px">Units bought in 2025, genuine line versus value line</h3>
        <div id="h_mix"><div class="chartbox short" style="height:250px"><canvas id="c_mix"></canvas></div></div>
        <p class="note" id="n_mix"></p>
      </div>
    </div>
  </section>

  <section>
    <h2>Is this customer growing or falling in billed parts, on both clocks?
      <span class="q">Service parts billed to this customer, per year — observed at market level</span></h2>
    <div class="card">
      <div id="h_evo"><div class="chartbox"><canvas id="c_evo"></canvas></div></div>
      <p class="note" id="n_evo"></p>
    </div>
  </section>

  <section>
    <h2>Which product lines saw the largest year-on-year change in billed parts?
      <span class="q">Change in billed euro against the previous comparable year — observed billing</span></h2>
    <div class="grid2">
      <div class="card">
        <h3 style="font-size:15px">AIM level 1 — the product groups</h3>
        <div id="h_l1"><div class="chartbox tall"><canvas id="c_l1"></canvas></div></div>
      </div>
      <div class="card">
        <h3 style="font-size:15px">AIM level 2 — the lines inside them</h3>
        <div id="h_l2"><div class="chartbox tall"><canvas id="c_l2"></canvas></div></div>
      </div>
    </div>
    <p class="note" id="n_aim"></p>
  </section>

  <section>
    <h2>Across all customers, who has the largest gap to modelled target spend?
      <span class="q">2025, market-level modelled opportunity — not band-level observed loss</span></h2>
    <div class="card">
      <div id="h_netgap"><div class="chartbox tall"><canvas id="c_netgap"></canvas></div></div>
      <p class="note" id="n_netgap"></p>
    </div>
    <div class="card">
      <h3 style="font-size:15px">Capture rate by customer and year — small multiples, one shared scale
        <span class="q">Below 100% means the customer bought less than the fleet implies it needs</span></h3>
      <div id="sm_grid" class="smgrid"></div>
      <div class="legend" id="lg_sm"></div>
      <p class="note" id="n_sm"></p>
    </div>
  </section>

  <section>
    <h2>How much does each vehicle in service spend on parts, and is that rising?
      <span class="q">Parts billed per vehicle in service, per year</span></h2>
    <div class="card">
      <div id="h_gps"><div class="chartbox tall"><canvas id="c_gps"></canvas></div></div>
      <p class="note" id="n_gps"></p>
    </div>
  </section>

  <section>
    <h2>How does our dealer reference price sit against the independent market?
      <span class="q">Median of our dealer reference price divided by a real competing price, by product group</span></h2>
    <div class="card">
      <div id="h_pos"><div class="chartbox tall"><canvas id="c_pos"></canvas></div></div>
      <p class="note" id="n_pos"></p>
    </div>
  </section>

  <section>
    <h2>How solid is each market's tonnage split?
      <span class="q">The measured basis behind every band share, and where none exists</span></h2>
    <div class="card"><div id="t_basis"></div>
      <p class="note amber">Where the basis reads <b>unmeasured</b>, the service rate was deliberately
      held at its previous value instead of being inferred from a handful of shipment records. Those
      markets are named below rather than being presented as if the split were measured.</p>
    </div>
  </section>

  <footer id="foot"></footer>
</div>

<script>__CHARTJS__</script>
<script id="pmte-data" type="application/json">__PAYLOAD__</script>
<script>
(function(){
"use strict";
var D = JSON.parse(document.getElementById('pmte-data').textContent);
var NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee', MUTED='#6b6257', RULE='#d8d2c6',
    AMBER='#b7791f', GREEN='#2f6b45', PALE='#eef3f9';
var LANE_TAG={};
Object.keys(D.lane).forEach(function(m){ LANE_TAG[m]=D.lane[m]; });
/* The internal file name of a market's schedule is never printed: the reader gets the schedule
   named by what it is. */
function laneName(m){
  return LANE_TAG[m]==='agreed' ? 'the schedule agreed for that market'
                                : 'the internal service schedule';
}
function eur(v){ if(v===null||v===undefined) return 'n/a';
  return 'EUR ' + Math.round(v).toLocaleString('en-GB'); }
function eurm(v){ if(v===null||v===undefined) return 'n/a';
  return 'EUR ' + (v/1e6).toFixed(2) + 'M'; }
function pct(v,d){ if(v===null||v===undefined) return 'n/a';
  return (100*v).toFixed(d===undefined?1:d) + '%'; }
function num(v){ return (v===null||v===undefined)?'n/a':Math.round(v).toLocaleString('en-GB'); }

/* tooltip */
var tip=document.getElementById('tip');
document.addEventListener('mouseover',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(!t) return; tip.innerHTML=t.getAttribute('data-tip'); tip.style.opacity='1';
});
document.addEventListener('mousemove',function(e){
  if(tip.style.opacity!=='1') return;
  var x=e.clientX+14, y=e.clientY+14;
  if(x+330>window.innerWidth) x=e.clientX-340;
  if(y+120>window.innerHeight) y=e.clientY-130;
  tip.style.left=x+'px'; tip.style.top=y+'px';
});
document.addEventListener('mouseout',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(t) tip.style.opacity='0';
});

Chart.defaults.font.family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif";
Chart.defaults.font.size=12;
Chart.defaults.color='#4a443b';
var charts={};
function mk(id,cfg){ if(charts[id]) charts[id].destroy(); charts[id]=new Chart(document.getElementById(id),cfg); }

/* One flat helper builds every cartesian chart's options, so no chart has to nest five deep. */
function chartOpts(o){
  o=o||{};
  var horiz=!!o.horizontal;
  var out={responsive:true,maintainAspectRatio:false,indexAxis:horiz?'y':'x',
    plugins:{legend:o.legend||{display:false},
      tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10}},
    scales:horiz
      ? {x:{grid:{color:RULE},beginAtZero:true},y:{grid:{display:false}}}
      : {x:{grid:{display:false}},y:{grid:{color:RULE},beginAtZero:true}}};
  if(o.label) out.plugins.tooltip.callbacks={label:o.label};
  if(o.tickX) out.scales.x.ticks=o.tickX;
  return out;
}

function barData(labels,values,colors){
  return {labels:labels,datasets:[{data:values,backgroundColor:colors,borderRadius:3}]};
}

/* ─┬─ every chart that draws more than one series gets a visible key, in words ──
   Chart.js legends are off by default here, so a multi-series chart with no key is unreadable.
   key() writes a legend under the canvas naming each colour; axisLabel() names a single series
   on the axis instead, so a one-series chart is not left bare either. */
/* ─────────── chart keys ─────────── */
function key(id,items){
  var host=document.getElementById(id);
  if(!host) return;
  var html=items.map(function(it){
    var sw=it.line
      ? '<i style="background:'+it.c+';height:3px;border-radius:2px;vertical-align:2px"></i>'
      : '<i style="background:'+it.c+'"></i>';
    return '<span'+(it.tip?' data-tip="'+it.tip+'"':'')+'>'+sw+it.l+'</span>';
  }).join('');
  var box=host.querySelector('.legend');
  if(!box){
    box=document.createElement('div'); box.className='legend';
    if(host.firstChild && host.firstChild.nextSibling){
      host.insertBefore(box, host.firstChild.nextSibling);
    } else { host.appendChild(box); }
  }
  box.innerHTML=html;
}
function axisLabel(id,text){
  var host=document.getElementById(id);
  if(!host) return;
  var box=host.querySelector('.legend.axis');
  if(!box){ box=document.createElement('div'); box.className='legend axis'; host.appendChild(box); }
  box.innerHTML='<span>'+text+'</span>';
}

/* ─────────── controls */
var selM=document.getElementById('selMarket'), selC=document.getElementById('selClock'),
    selY=document.getElementById('selYear'), selF=document.getElementById('selFamily');
D.markets.forEach(function(m){
  var o=document.createElement('option'); o.value=m; o.textContent=m; selM.appendChild(o);
});
selM.value='ITUK';

var CY_YEARS=[2023,2024,2025,2026], FY_YEARS=[2023,2024,2025,2026,2027];

/* What each clock actually covers, in words, printed under the controls and reused in tooltips.
   The ISZE year runs April to March and is named for the year it closes in, so ISZE 2026 is
   April 2025 to March 2026 — the reader should not have to work that out. */
function fySpan(y){ return 'Apr '+(y-1)+' – Mar '+y; }
function clockLabel(clock,year){
  return clock==='FY' ? ('ISZE year '+year+' ('+fySpan(year)+')')
                      : ('calendar year '+year+' (Jan–Dec '+year+')');
}
function clockShort(clock,year){
  return clock==='FY' ? ('ISZE '+year+' (Apr '+(year-1)+'–Mar '+year+')')
                      : ('calendar '+year);
}
function updateClockNote(){
  var clock=selC.value, ys=(clock==='CY'?CY_YEARS:FY_YEARS);
  var y=parseInt(selY.value,10); if(isNaN(y)) y=ys[ys.length-2];
  document.getElementById('clockNote').innerHTML=
    'Reading on the <b>'+clockShort(clock,y)+'</b>. '
    +(clock==='FY'
      ? 'An ISZE year is named for the year it <i>closes</i> in, so ISZE '+y+' covers April '
        +(y-1)+' to March '+y+'. The other option is the calendar year, January to December. '
        +'The billed-sales chart and its KPI follow this control; the fleet, gap and capture panels '
        +'are annual and do not.'
      : 'The other option is the ISZE year, which runs April to March and is named for the year '
        +'it closes in, so ISZE '+y+' is April '+(y-1)+' to March '+y+'. '
        +'The billed-sales chart and its KPI follow this control; the fleet, gap and capture panels '
        +'are annual and do not.');
}

function fillYears(){
  var ys=selC.value==='CY'?CY_YEARS:FY_YEARS;
  var prev=parseInt(selY.value,10);
  selY.innerHTML='';
  ys.forEach(function(y){
    var o=document.createElement('option'); o.value=y;
    o.textContent=(selC.value==='FY'?'ISZE ':'CY ')+y;
    selY.appendChild(o);
  });
  selY.value=ys.indexOf(prev)>=0?prev:(selC.value==='CY'?2025:2026);
  updateClockNote();
}
function fillFamilies(){
  var m=selM.value, cats=Object.keys(D.catLabels)
      .filter(function(c){return D.catGap[m].some(function(r){return r.cat===c;});});
  var prev=selF.value;
  selF.innerHTML='';
  cats.forEach(function(c){
    var o=document.createElement('option'); o.value=c; o.textContent=D.catLabels[c];
    selF.appendChild(o);
  });
  selF.value=cats.indexOf(prev)>=0?prev:cats[0];
}
fillYears(); fillFamilies();

/* ─────────── render */
function render(){
  var m=selM.value, clock=selC.value, year=parseInt(selY.value,10), fam=selF.value;
  var bands=D.fleet[m]||[], cap=D.capture[m]||{}, bl=D.billed[m]||{CY:{},FY:{}};

  /* lane notice */
  var lanes={}; Object.keys(D.lane).forEach(function(k){lanes[D.lane[k]]=1;});
  document.getElementById('laneNotice').innerHTML=
    '<div class="note"><b>'+m+'</b> runs <span class="tag '+LANE_TAG[m]+'">'+laneName(m)
    +'</span>'
    +(LANE_TAG[m]==='agreed'
      ? ' — the schedule agreed with the distributor for this market: filters 1.25 visits a year, '
        +'clutch and brakes 0.5, a 22,389-vehicle fleet.'
      : ' — standard trucks 0.5 visits a year, heavy 0.667, the D-Max pickup 1.0.')
    +' The network carries <b>two</b> interval schedules and they are never averaged or added '
    +'together. A figure from one schedule is not comparable with a figure from the other.'
    +'</div>';

  /* KPIs — every derived number carries its own formula */
  var k=[];
  var yc=cap[year]||cap[2025]||{};
  var totUio=bands.reduce(function(a,b){return a+b.uio;},0);
  var totExp=bands.reduce(function(a,b){return a+b.expected;},0);
  k.push({v:num(totUio),l:'vehicles in service, all bands',
    tip:'Sum of the four tonnage bands for <b>'+m+'</b>: '+bands.map(function(b){
      return b.label+' '+num(b.uio);}).join(', ')+'.<br>This is the 2025 fleet estimate and it is used '
      +'for every year, because mileage is not measured per market. Snapshot '+D.snapshot+'.'});
  k.push({v:num(totExp),l:'service jobs expected a year'
    +(year!==2025?' (2025 fleet)':''),
    tip:'Vehicles in each band x the visits a year implied by the interval schedule for that band, '
      +'summed over the 14 service families.<br>Flat year on year by construction: the fleet is the '
      +'2025 estimate. Actual billing is not split by band.'});
  k.push({v:eur(yc.gap_eur),l:'gap to modelled target spend, '+year+' — '+m,cls:'warn',
    tip:'Modelled target spend minus what was actually billed, at market level, '+year+'.<br>Target spend is the '
      +'fleet x the interval schedule x the category factor. It is a ceiling, not a forecast.<br>'
      +'Same figure on both clocks: the gap is built on the 2025 fleet and annual billing, so it does '
      +'not split by ISZE year. Not observed at tonnage-band level.'});
  k.push({v:pct(yc.capture),l:'share of expected demand bought, '+year,
    tip:'Units actually bought divided by units expected, '+year+', across the 14 service '
      +'families.<br>Above 100% means the customer bought more than its own fleet count implies it '
      +'needs, which usually means it serves vehicles not in that fleet count.<br>'
      +'Same figure on both clocks: it is an annual rate against the 2025 fleet, not an ISZE-year cut.'});
  var bv=bl[clock]&&bl[clock][year];
  k.push({v:eurm(bv),l:'service parts billed, '+clockLabel(clock,year),
    tip:'Net parts billed to '+m+' in '+clockLabel(clock,year)+'.<br>'
      +(clock==='FY'
        ? 'The ISZE year runs April to March and is named for the year it closes in, so ISZE '
          +year+' is April '+(year-1)+' to March '+year+'.'
        : 'The calendar year runs January to December.')
      +'<br>The other clock gives a different split of the same billing. The two are never averaged.'});
  var g25=(D.gps[m]||[]).filter(function(x){return x.year===year;})[0];
  k.push({v:(g25&&g25.spu)?('EUR '+g25.spu.toFixed(0)):'n/a',l:'parts billed per vehicle, '+year,
    tip:'Parts billed divided by vehicles in service, '+year+'.<br>Fleet source for this market: '
      +((g25&&g25.uio_source)||'the band model')+'.'+(g25&&g25.spu_ex_warranty
      ? '<br>Excluding warranty: EUR '+g25.spu_ex_warranty.toFixed(0)+'.' : '')});
  document.getElementById('kpis').innerHTML=k.map(function(x){
    return '<div class="kpi '+(x.cls||'')+'" data-tip="'+x.tip+'"><div class="v">'+x.v
      +'</div><div class="l">'+x.l+'</div></div>';
  }).join('');

  /* fleet mix donut (<=5 segments, one customer). One fixed colour per band, so a band keeps its
     colour from customer to customer instead of taking whatever position it lands in. */
  var BANDCOL={'LCV_D-Max':GREEN,'3.5t_N35':NAVY,'5.5t_N50_N55':AMBER,'7.5t_N50_N62_N75':TERRA,'F_series_MD_heavy':'#7a8ba6'};
  var fl=bands.map(function(b){return {band:b.label,uio:b.uio,col:BANDCOL[b.band]||MUTED};});
  mk('c_fleet',{type:'doughnut',
    data:{labels:fl.map(function(x){return x.band;}),
      datasets:[{data:fl.map(function(x){return x.uio;}),
        backgroundColor:fl.map(function(x){return x.col;}),borderColor:'#fff',borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'58%',
      plugins:{legend:{display:false},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{label:function(c){
            var tot=fl.reduce(function(a,b){return a+b.uio;},0);
            return c.label+': '+num(c.raw)+' vehicles ('+(100*c.raw/tot).toFixed(1)+'% of the fleet)';}}}}}});
  document.getElementById('lg_fleet').innerHTML=fl.map(function(x,i){
    var tot=fl.reduce(function(a,b){return a+b.uio;},0);
    return '<span data-tip="Fleet in this band, from the derived band model.<br>'
      +'Share of this customer total fleet. Snapshot '+D.snapshot+'.">'
      +'<i style="background:'+x.col+'"></i>'+x.band
      +' — '+num(x.uio)+' ('+(100*x.uio/tot).toFixed(0)+'%)</span>';
  }).join('');

  /* expected demand by band */
  mk('c_expected',{type:'bar',data:barData(bands.map(function(b){return b.label;}),
      bands.map(function(b){return b.expected;}),NAVY),
    options:chartOpts({horizontal:true,label:function(c){
      var b=bands[c.dataIndex];
      return [num(b.expected)+' jobs a year in this band',
              num(b.uio)+' vehicles in service, '+b.visits+' visits each',
              'Band rows are modelled. Billing does not split by band.'];}})});
  axisLabel('h_expected','One series: <b>expected / modelled service jobs a year</b> in each tonnage band. '
    +'The horizontal scale is jobs, not euro. Navy bars only — no second series.');
  document.getElementById('n_expected').innerHTML='<b>Expected / modelled by tonnage band.</b> Service jobs per band, from the fleet in '
    +'that band and the interval schedule this market runs. <b>The fleet vintage is 2025 for every '
    +'year</b>, so expected demand is flat over time by construction — only billing and the capture '
    +'rate move. <b>Actual billed at market level</b> — the billing carries no vehicle, so the units '
    +'actually bought cannot be split across bands; the bands carry the expectation, and the market carries the actual.';

  /* gap by band x family — best form: ranked euro bars */
  var gapRows=[];
  D.catGap[m].forEach(function(r){
    gapRows.push({k:D.catLabels[r.cat]||r.cat, gap:r.gap_eur, expected:r.expected, cat:r.cat});
  });
  gapRows.sort(function(a,b){return b.gap-a.gap;});
  gapRows=gapRows.slice(0,12);
  mk('c_gap',{type:'bar',
    data:barData(gapRows.map(function(r){return r.k;}),gapRows.map(function(r){return r.gap;}),
      gapRows.map(function(r){return r.gap<0?GREEN:TERRA;})),
    options:chartOpts({horizontal:true,label:function(c){
      var r=gapRows[c.dataIndex];
      return [eur(r.gap)+' expected-demand share of modelled gap in '+r.k,
              num(r.expected)+' jobs a year expected in this family',
              'Allocated to the family by its share of expected demand — not observed at band.',
              'Market level: the billing carries no vehicle.'];}})});
  key('h_gap',[
    {c:TERRA,l:'modelled opportunity (expected-demand share)',tip:'Market-level modelled gap allocated to this service family by its share of expected demand. '
      +'Not observed billing by tonnage band. The bar length is the euro share of the modelled gap.'},
    {c:GREEN,l:'over-bought against the fleet model',
      tip:'A negative gap: the family billed more than this fleet implies it needs. Usually means the '
      +'customer serves vehicles outside its own fleet count.'}]);
  document.getElementById('n_gap').innerHTML='Ranked by euro, because quantity alone says nothing. '
    +'Each bar is the <b>expected-demand share of the modelled gap</b> in that service family for <b>'+m+'</b> in 2025 — '
    +'allocated by share of expected demand, not observed at tonnage-band level. The euro is the decision currency; the family says '
    +'where modelled opportunity concentrates; the fleet base is in the box above. '
    +'<b>Actual billed at market level</b> — the billing carries no vehicle identification, so a band or '
    +'family column must never be summed against the market actual or it double-counts.';

  /* family table */
  document.getElementById('t_catgap').innerHTML='<table><thead><tr><th>Service family</th>'
    +'<th class="n">Jobs expected</th><th class="n">Units bought</th><th class="n">Modelled gap</th>'
    +'</tr></thead><tbody>'
    +D.catGap[m].slice().sort(function(a,b){return b.gap_eur-a.gap_eur;}).slice(0,8).map(function(r){
      return '<tr><td class="db">'+r.label+'</td><td class="n">'+num(r.expected)+'</td>'
        +'<td class="n">'+num(r.actual)+'</td><td class="n">'+eur(r.gap_eur)+'</td></tr>';
    }).join('')+'</tbody></table>'
    +'<p class="small" style="margin-top:8px">Units bought is the whole market figure for that '
    +'family, repeated on every band row on purpose. It is not band-specific. '
    +'Jobs expected and modelled gap are annual against the 2025 fleet, the same on both clocks; '
    +'only the billed-sales chart and its KPI move with the ISZE-year control.</p>';


  /* family mix donut: one customer, one family, <=4 segments */
  var fm=(D.famMix[m]||{})[fam];
  if(fm){
    mk('c_mix',{type:'doughnut',
      data:{labels:['Genuine Isuzu','Value line'],
        datasets:[{data:[fm.genuine_units,fm.value_units],
          backgroundColor:[NAVY,TERRA],borderColor:'#fff',borderWidth:2}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:'55%',
        plugins:{legend:{display:true,position:'bottom',labels:{boxWidth:11,padding:12}},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{label:function(c){
              var tot=fm.genuine_units+fm.value_units;
              return c.label+': '+num(c.raw)+' units'
                +(tot?' ('+(100*c.raw/tot).toFixed(1)+'%)':'')+', 2025';}}}}}});
    key('h_mix',[
      {c:NAVY,l:'genuine Isuzu line',tip:'Units billed as the OE Isuzu part number for this family in 2025.'},
      {c:TERRA,l:'value line (BVP)',tip:'Units billed as a Best Value Parts alternative for the same family in 2025.'}]);
    document.getElementById('n_mix').innerHTML='Of the <b>'+D.catLabels[fam]+'</b> units bought by '
      +m+' in 2025, '+num(fm.genuine_units)+' were the genuine line and '+num(fm.value_units)
      +' the value line. Two segments only, so a donut is the right form here.';
  }

  /* evolution, both clocks */
  var periods=(clock==='CY'?CY_YEARS:FY_YEARS).filter(function(y){return bl[clock]&&bl[clock][y]!==undefined;});
  mk('c_evo',{type:'bar',
    data:barData(periods.map(function(y){return (clock==='FY'?'ISZE ':'CY ')+y;}),
      periods.map(function(y){return bl[clock][y];}),
      periods.map(function(y){return (clock==='CY'&&y===2026)?AMBER:NAVY;})),
    options:chartOpts({label:function(c){
      var y=periods[c.dataIndex];
      var prev=(clock==='CY'?CY_YEARS:FY_YEARS)[ (clock==='CY'?CY_YEARS:FY_YEARS).indexOf(y)-1 ];
      var pv=bl[clock][prev];
      var s=eur(c.raw)+' billed in '+clockLabel(clock,y);
      if(pv) s+=' ('+((c.raw/pv-1)>=0?'+':'')+(100*(c.raw/pv-1)).toFixed(1)+'% against '+prev+')';
      if(clock==='CY'&&y===2026) s+=' - the calendar year is not complete';
      return s;}})});
  key('h_evo',[
    {c:NAVY,l:'a complete year'},
    {c:AMBER,l:'calendar 2026 — part year, January to the last month with billing',
     tip:'A part year compared against complete years understates 2026. It is shown in amber so it '
       +'cannot be read as a fall.'}]);
  document.getElementById('n_evo').innerHTML=(clock==='FY'
    ? 'The ISZE year runs April to March and is named for the year it closes in, so <b>ISZE 2026 is '
      +'April 2025 to March 2026</b>. '
    : 'The calendar year runs January to December, so <b>calendar 2026 is January 2026 to December '
      +'2026</b> and is not yet complete. ')
    +'<b>Calendar 2026 is shown in amber because it is not a complete year</b> — comparing it with a '
    +'full year understates it. The two clocks are the same underlying billing cut two ways; they '
    +'are shown separately and never averaged.';

  /* AIM level 1 change bars */
  var l1=D.l1[m][clock]||[];
  var byL1={}, pers={};
  l1.forEach(function(r){ (byL1[r.l1]=byL1[r.l1]||{})[r.period]=r.eur;
    pers[r.period]=1; });
  var sortedP=Object.keys(pers).map(Number).sort(function(a,b){return a-b;});
  var latest=sortedP.filter(function(p){return !(clock==='CY'&&p===2026);}).pop();
  var prior=sortedP.filter(function(p){return p<latest;}).pop();
  var l1rows=Object.keys(byL1).map(function(k){
    var a=byL1[k][latest]||0, b=prior!==undefined?(byL1[k][prior]||0):0;
    return {k:k, now:a, before:b, delta:a-b};
  }).filter(function(r){return r.now||r.before;});
  l1rows.sort(function(a,b){return a.delta-b.delta;});
  l1rows=l1rows.slice(0,12);
  mk('c_l1',{type:'bar',
    data:barData(l1rows.map(function(r){return r.k;}),l1rows.map(function(r){return r.delta;}),
      l1rows.map(function(r){return r.delta<0?TERRA:GREEN;})),
    options:chartOpts({horizontal:true,label:function(c){
      var r=l1rows[c.dataIndex];
      return [eur(r.delta)+' change',
              'was '+eur(r.before)+' in '+prior+', now '+eur(r.now)+' in '+latest];}})});

  /* AIM level 2 change bars */
  var l2=(D.l2[m]||[]).filter(function(r){return r.clk===clock;});
  var byL2={}, pers2={};
  l2.forEach(function(r){ var k2=r.l2;
    (byL2[k2]=byL2[k2]||{})[r.period]=(byL2[k2][r.period]||0)+r.eur; pers2[r.period]=1; });
  var sp2=Object.keys(pers2).map(Number).sort(function(a,b){return a-b;});
  var latest2=sp2.filter(function(p){return !(clock==='CY'&&p===2026);}).pop();
  var prior2=sp2.filter(function(p){return p<latest2;}).pop();
  var l2rows=Object.keys(byL2).map(function(k){
    var a=byL2[k][latest2]||0, b=prior2!==undefined?(byL2[k][prior2]||0):0;
    return {k:k, now:a, before:b, delta:a-b};
  }).sort(function(a,b){return a.delta-b.delta;}).slice(0,14);
  mk('c_l2',{type:'bar',
    data:barData(l2rows.map(function(r){return r.k;}),l2rows.map(function(r){return r.delta;}),
      l2rows.map(function(r){return r.delta<0?TERRA:'#7a8ba6';})),
    options:chartOpts({horizontal:true,label:function(c){
      var r=l2rows[c.dataIndex];
      return [eur(r.delta)+' change',
              'was '+eur(r.before)+' in '+prior2+', now '+eur(r.now)+' in '+latest2];}})});
  key('h_l1',[
    {c:TERRA,l:'billed parts fell against the previous year'},
    {c:GREEN,l:'billed parts rose against the previous year'}]);
  key('h_l2',[
    {c:TERRA,l:'billed parts fell against the previous year'},
    {c:'#7a8ba6',l:'billed parts rose against the previous year'}]);
  document.getElementById('n_aim').innerHTML='Both charts compare the latest complete year with the '
    +'year before it on the chosen clock, so a bar pointing left is a fall in billed parts on that product line '
    +'and a bar pointing right is a rise. AIM level 1 is the product group; level 2 is the '
    +'line inside it. Terracotta means a fall. These are observed billed euro, not units or modelled gap.';

  /* network ranked gap */
  var ng=D.markets.map(function(x){
    var c=D.capture[x]&&D.capture[x][2025]; return {m:x, gap:c?c.gap_eur:0, cap:c?c.capture:null};
  }).sort(function(a,b){return b.gap-a.gap;});
  mk('c_netgap',{type:'bar',
    data:barData(ng.map(function(r){return r.m;}),ng.map(function(r){return r.gap;}),
      ng.map(function(r){return r.m===m?TERRA:NAVY;})),
    options:chartOpts({label:function(c){
      var r=ng[c.dataIndex];
      return [eur(r.gap)+' gap to modelled target spend in 2025',
              'share of expected demand bought: '+(r.cap!==null?pct(r.cap):'n/a'),
              'Market-level modelled opportunity — not band-level observed loss.',
              'The customer you have selected is highlighted.'];}})});
  var selRow=ng.filter(function(r){return r.m===m;})[0];
  key('h_netgap',[
    {c:TERRA,l:'the selected customer ('+m+')'
      +(selRow?' — '+eur(selRow.gap)+', '+pct(selRow.cap)+' of expected demand bought':'')},
    {c:NAVY,l:'every other customer'}]);
  document.getElementById('n_netgap').innerHTML='Gap to modelled target spend by customer, 2025, largest first. '
    +'Network modelled opportunity total <b>'+eurm(D.net.gap2025)+'</b> against <b>'+eurm(D.net.actual2025)
    +'</b> actually billed at market level. The selected customer is in terracotta. '
    +'A customer above 100% has bought more than its own fleet implies it needs, which usually means '
    +'it serves vehicles that are not in its own fleet count. '
    +'<b>Scope:</b> the '+D.markets.length+' customers the service model covers. The billing extract '
    +'also carries '+D.scopeNote.markets.join(', ')+', which are outside that scope and are '
    +'<b>'+D.scopeNote.sharePct+'%</b> of total parts billed (EUR '+eurm(D.scopeNote.eur)+' on the '
    +'complete year). They are excluded here rather than added to a network total they do not belong to.';

  /* small multiples of capture by year */
  var palette={2023:'#c9d3e0',2024:'#8fa3c0',2025:NAVY,2026:AMBER};
  /* Four shades and no Chart.js legend, so the key is written here in words. */
  document.getElementById('lg_sm').innerHTML=[2023,2024,2025,2026].map(function(y){
    return '<span><i style="background:'+palette[y]+'"></i>'
      +(y===2026?'calendar 2026 (part year)':'calendar '+y)+'</span>';
  }).join('');

  var smTip='Pieces bought as a share of the pieces the fleet implies it needs. 100% means the '
    +'customer bought exactly what its own fleet implies.<br>Flat across years by construction: the '
    +'fleet is the 2025 estimate. What changes is the billing.<br>Snapshot '+D.snapshot+'.';
  document.getElementById('sm_grid').innerHTML=D.markets.map(function(x){
    var c=D.capture[x]||{};
    var bars=[2023,2024,2025,2026].map(function(y){
      var v=c[y]?c[y].capture:null;
      if(v===null||v===undefined) return '<div style="height:0"></div>';
      var h=Math.max(2,Math.min(100,v*100));
      return '<div title="'+y+': '+pct(v)+'" data-tip="Share of expected demand bought in '+y
        +': <b>'+pct(v)+'</b><br>Expected '+num(c[y].expected)+' jobs, '+num(c[y].actual)
        +' units billed.<br>Snapshot '+D.snapshot+'." style="height:'+h+'px;background:'
        +palette[y]+';border-radius:2px 2px 0 0;flex:1"></div>';
    }).join('');
    return '<div style="cursor:pointer" data-tip="<b>'+x+'</b> &middot; '+laneName(x)+'<br>'
      +smTip+'<br>2023 '+pct(c[2023]&&c[2023].capture)+' &middot; 2024 '+pct(c[2024]&&c[2024].capture)
      +'<br>2025 '+pct(c[2025]&&c[2025].capture)+' &middot; 2026 '+pct(c[2026]&&c[2026].capture)+'">'
      +'<div style="display:flex;align-items:flex-end;gap:2px;height:100px;border-bottom:1px solid '
      +RULE+'">'+bars+'</div>'
      +'<div class="lbl" style="color:'+(x===m?TERRA:NAVY)+'">'+x+'</div></div>';
  }).join('');
  document.getElementById('n_sm').innerHTML='Every customer on one shared scale, so the bars are '
    +'comparable across panels. Three shades for 2023, 2024 and 2025; amber is the incomplete '
    +'calendar 2026. Where a market shows no amber, its 2026 billing is not in the model. '
    +'A short bar means the customer bought a small share of what its own fleet implies it needs.';

  /* GPS spend per vehicle */
  var gs=(D.gps[m]||[]).filter(function(r){return r.spu!==null;});
  mk('c_gps',{type:'bar',
    data:{labels:gs.map(function(r){return r.year;}),
      datasets:[{data:gs.map(function(r){return r.spu;}),backgroundColor:NAVY,borderRadius:3},
        {type:'line',label:'excluding warranty',data:gs.map(function(r){return r.spu_ex_warranty;}),
         borderColor:TERRA,backgroundColor:TERRA,pointRadius:4,fill:false,tension:0,borderWidth:2}]},
    options:chartOpts({legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
      label:function(c){
        var r=gs[c.dataIndex];
        if(c.datasetIndex===1) return 'Excluding warranty: '+eur(r.spu_ex_warranty)+' per vehicle';
        return 'Parts billed per vehicle: '+eur(r.spu)+' on '+num(r.uio)+' vehicles in service';}})});
  key('h_gps',[
    {c:NAVY,l:'parts billed per vehicle in service — all parts',
     tip:'Parts billed in the year divided by the vehicles in service. Includes warranty parts.'},
    {c:TERRA,l:'parts billed per vehicle — excluding warranty',line:true,
     tip:'The same figure with warranty claims removed, because a warranty part is not a customer '
       +'buying a part. Where the warranty split is missing for a year the line breaks.'}]);
  document.getElementById('n_gps').innerHTML='Parts billed to this customer divided by the vehicles '
    +'in service in that year. The terracotta line removes warranty parts, because a warranty claim '
    +'is not a customer buying a part. Where the warranty split is missing for a year the line is '
    +'broken rather than drawn as zero. Fleet figures for this market come from '
    +'<b>'+((gs[0]&&gs[0].uio_source)||'the band model')+'</b>.';

  /* price position, two-sided deviation from the market */
  var po=D.pos[m]||[];
  mk('c_pos',{type:'bar',
    data:barData(po.map(function(r){return r.l1;}),po.map(function(r){return r.idx-1;}),
      po.map(function(r){return r.idx>1?TERRA:'#7a8ba6';})),
    options:chartOpts({horizontal:true,
      tickX:{callback:function(v){return (v>0?'+':'')+v+'x';}},
      label:function(c){var r=po[c.dataIndex];
        return [r.idx.toFixed(2)+' times the competing price',
                r.pns+' part numbers, '+eur(r.billed)+' billed in the latest complete year',
                'Zero means level with the competing price.'];}})});
  key('h_pos',[
    {c:TERRA,l:'above the competing price',tip:'The median of our dealer reference price '
      +'divided by a real competing price is greater than 1.00 in this product group.'},
    {c:'#7a8ba6',l:'at or below it',
     tip:'The same median is 1.00 or lower — level with, or cheaper than, the competing price.'}]);
  document.getElementById('n_pos').innerHTML='Our dealer reference price divided by a real competing '
    +'price, median across the part numbers in each product group. Bars to the right of zero are '
    +'groups where we sit above the independent market. One competing source fanned across markets, '
    +'vintage <b>'+D.compVintage+'</b> — read it as a position, not as a measured transaction price.';

  /* basis table */
  document.getElementById('t_basis').innerHTML='<table><thead><tr><th>Customer</th>'
    +'<th>Interval lane</th><th class="n">3.5 t share of the N-series truck fleet</th>'
    +'<th>Basis</th>'
    +'<th>What the evidence is</th>'
    +'</tr></thead><tbody>'
    +D.basis.map(function(r){
      var unm=r.basis==='unmeasured';
      return '<tr><td class="db">'+r.market+'</td>'
        +'<td><span class="tag '+(LANE_TAG[r.market]==='iml'?'agreed':'internal')+'">'
        +laneName(r.market)+'</span></td>'
        +'<td class="n">'+(unm?'held':(100*r.share).toFixed(1)+'%')+'</td>'
        +'<td>'+(unm?'<span class="tag unm">unmeasured</span>':r.basis)+'</td>'
        +'<td class="small">'+r.note+'</td></tr>';
    }).join('')+'</tbody></table>';

  /* footer */
  document.getElementById('foot').innerHTML='<b>Sources</b> — all read at build time, snapshot '
    +D.snapshot+': the derived service-demand model by tonnage band and service family; the AIM '
    +'evolution model, which carries the billed euro by product group on both clocks; the service '
    +'capture model; the spend-per-vehicle model; the competing-price sample; and the measured band '
    +'shares with their basis. <b>What this page cannot show:</b> the units actually bought are not '
    +'split by tonnage band, because the billing carries no vehicle identification — bands carry the '
    +'expectation and the market carries the actual. The fleet is the 2025 estimate for every year, '
    +'so expected demand is flat over time by construction. Mileage is not measured per market, so '
    +'the interval schedule carries the whole assumption. Tonnage splits for the markets marked '
    +'unmeasured are held, not measured. And the two interval lanes are never combined.';
}

['selMarket','selClock','selYear','selFamily'].forEach(function(id){
  document.getElementById(id).addEventListener('change',function(){
    if(id==='selMarket') fillFamilies();
    render();
  });
});
render();
})();
</script>
</body></html>
"""

html = (TEMPLATE.replace("__CHARTJS__", chart_js)
                .replace("__PAYLOAD__", body)
                .replace("__SNAPSHOT__", SNAPSHOT)
                .replace("__BILLED_THROUGH__", BILLED_THROUGH_TEXT))

# ── guard: the inline script must parse. A single unbalanced quote kills the whole page
# silently — the containers render empty and the file still looks fine on disk.
_parts = html.split("<script>", 2)
if len(_parts) < 3:
    die("expected the chart library block and the page script block")
_page_js = _parts[2].split("</script>", 1)[0]
for _bad, _why in [("\\\\'", "an escaped backslash before a quote closes the string early"),
                   ("\\'", "a stray backslash before a quote")]:
    if _bad in _page_js:
        die(f"page script contains {_why}")
_tmp_js = OUT_DIR / "_build" / "_syntax_check.js"
_tmp_js.write_text(_page_js, encoding="utf-8")
_r = subprocess.run(["node", "--check", str(_tmp_js)], capture_output=True, text=True)
if _r.returncode != 0:
    die("page script does not parse:\n" + (_r.stderr or "")[:800])
print("syntax guard: page script parses clean")

OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_HTML.write_text(html, encoding="utf-8")
OUT_CMD.write_bytes(("@echo off\r\nstart \"\" \"%~dp0ISZE_PMS_Tonnage_Evolution.html\"\r\n")
                    .encode("ascii"))

kb = len(html.encode("utf-8")) / 1024
print(f"rows  band={len(band)}  aim={len(aim)}  payload={len(body)/1024:.0f} KB")
print(f"written -> {OUT_HTML}  ({kb:.0f} KB)")
print(f"written -> {OUT_CMD}")
print(f"lanes: " + ", ".join(f"{k}={v}" for k, v in sorted(LANE.items())))
print(f"network gap 2025 = EUR {NET_GAP_2025:,}")
