#!/usr/bin/env python3
"""UTI PMS cover evolution — IML v7 intervals, fiscal years, capped at 100%."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from uti_iml_fy_engine import (  # noqa: E402
    ALL_CATS,
    BRAKE_CATS,
    CLUTCH_CATS,
    CLUTCH_UIO_RATIO,
    FILTER_CATS,
    IML_WEAR_FREQ,
    IML_FILTER_FREQ,
    IML_WEAR_FREQ,
    MILEAGE_KM_YR,
    cap_pct,
    compute_uti_fy,
    family_cover,
    iml_interval_km,
    load_sales,
    schedule_table_rows,
)

OUT = Path(__file__).resolve().parent.parent / "UTI_PMS_Evolution.html"
DASH_SHOW = OUT.parent / "UTI_Dashboard_Show.html"

# prism's native fiscal_year column already buckets Apr-Mar correctly per data_prep's own
# definition (fiscal_year=2025 == Apr 2025-Mar 2026), which equals Jerome's "FY26" naming
# (FY label = native fiscal_year + 1). NATIVE_FY_YEARS drives the data pull; the payload's
# fy_years list is relabeled to Jerome's convention before it reaches the chart/HTML layer.
NATIVE_FY_YEARS = [2023, 2024, 2025]
FY_YEARS = [fy + 1 for fy in NATIVE_FY_YEARS]  # [2024, 2025, 2026] — display labels

CAT_LABELS = {
    "oil_filter": "Oil filter", "fuel_filter": "Fuel filter", "air_filter": "Air filter",
    "urea_filter": "Urea filter", "brake_pad": "Brake pad", "brake_rotor": "Brake rotor",
    "brake_shoe": "Brake shoe", "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch PP", "clutch_booster": "Clutch booster",
    "clutch_kit": "Clutch kit", "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing",
}
TREND_CATS = [
    "oil_filter", "fuel_filter", "air_filter", "brake_pad", "brake_rotor",
    "clutch_booster", "clutch_disc", "urea_filter",
]
CAPTURE_CEILING = 100.0


def wtd_capture(cats: dict, keys: list[str]) -> float:
    act = sum(cats[k]["total"]["qty"] for k in keys if k in cats)
    exp = sum(cats[k]["total"]["exp"] for k in keys if k in cats)
    return act / exp * 100 if exp else 0.0


def build_fy_payload(sales) -> dict:
    trends: dict = {
        "fy_years": FY_YEARS,
        "uio": [],
        "total": [], "total_true": [],
        "genuine": [], "genuine_true": [],
        "bvp": [], "bvp_true": [],
        "gap_eur": [], "rev_genuine": [], "rev_bvp": [], "bvp_share": [],
        "filters": [], "filters_true": [], "wear": [], "wear_true": [],
        "categories": {},
    }
    for fy in NATIVE_FY_YEARS:
        r = compute_uti_fy(fy, sales)
        c = r["categories"]
        trends["uio"].append(r["uio"])
        for key, lt in [("total", "total"), ("genuine", "genuine"), ("bvp", "bvp")]:
            act = sum(c[k][lt]["qty"] for k in ALL_CATS if k in c)
            exp = sum(c[k]["total"]["exp"] for k in ALL_CATS if k in c)
            true = act / exp * 100 if exp else 0
            trends[key].append(min(true, CAPTURE_CEILING))
            trends[f"{key}_true"].append(round(true, 1))
        gap = sum(c[k]["total"]["gap"] for k in ALL_CATS if k in c)
        rg = sum(c[k]["genuine"]["rev"] for k in ALL_CATS if k in c)
        rb = sum(c[k]["bvp"]["rev"] for k in ALL_CATS if k in c)
        trends["gap_eur"].append(int(gap))
        trends["rev_genuine"].append(int(rg))
        trends["rev_bvp"].append(int(rb))
        trends["bvp_share"].append(round(rb / (rg + rb) * 100, 1) if (rg + rb) else 0)
        ft = wtd_capture(c, FILTER_CATS)
        wt = wtd_capture(c, BRAKE_CATS + CLUTCH_CATS)
        trends["filters"].append(min(ft, CAPTURE_CEILING))
        trends["filters_true"].append(round(ft, 1))
        trends["wear"].append(min(wt, CAPTURE_CEILING))
        trends["wear_true"].append(round(wt, 1))

    for cat in TREND_CATS:
        cap_s, true_s, gap_s = [], [], []
        for fy in NATIVE_FY_YEARS:
            r = compute_uti_fy(fy, sales)
            if cat in r["categories"]:
                t = r["categories"][cat]["total"]["capture"] * 100
                cap_s.append(min(t, CAPTURE_CEILING))
                true_s.append(round(t, 1))
                gap_s.append(int(r["categories"][cat]["total"]["gap"]))
            else:
                cap_s.append(None)
                true_s.append(None)
                gap_s.append(None)
        trends["categories"][cat] = {
            "label": CAT_LABELS.get(cat, cat),
            "capture": cap_s,
            "capture_true": true_s,
            "gap": gap_s,
        }

    snap = compute_uti_fy(NATIVE_FY_YEARS[-1], sales)["categories"]
    gaps = []
    for cat in ALL_CATS:
        if cat in snap and snap[cat]["total"]["gap"] > 0:
            gaps.append({
                "cat": CAT_LABELS.get(cat, cat),
                "gap": int(snap[cat]["total"]["gap"]),
                "capture": cap_pct(snap[cat]["total"]["capture"])[0],
            })
    gaps.sort(key=lambda x: -x["gap"])
    trends["top_gaps_latest_fy"] = gaps[:8]
    return trends


def load_attach_fy() -> dict:
    if not DASH_SHOW.exists():
        return {"fy_years": [], "UTI": {}}
    text = DASH_SHOW.read_text(encoding="utf-8")
    m = re.search(r"const DATA = (\{.*?\});\s*\n", text, re.DOTALL)
    if not m:
        return {"fy_years": [], "UTI": {}}
    data = json.loads(m.group(1))
    dist = data.get("distributors", {}).get("UTI", {})
    out = {"fy_years": data.get("fy_years", []), "UTI": {}}
    for yr, vals in (dist.get("attach_fy") or {}).items():
        out["UTI"][yr] = vals
    return out


def schedule_html() -> str:
    rows = schedule_table_rows()
    trs = "".join(
        f"<tr><td>{r['label']}</td><td>{r['freq']}×/yr</td>"
        f"<td>{r['km']:,} km</td></tr>".replace(",", ".")
        for r in rows
    )
    clutch_km = iml_interval_km(IML_WEAR_FREQ)
    return f"""
<section>
  <h2>0 · IML v7 schedule (UTI)</h2>
  <p class="sub">100% addressable · {MILEAGE_KM_YR:,} km/yr parc assumption · ISZE FY = Apr–Mar</p>
  <table class="sched">
    <tr><th>Category</th><th>Frequency</th><th>Interval (km)</th></tr>
    {trs}
  </table>
  <p class="sub">Clutch uses parc subset ({CLUTCH_UIO_RATIO*100:.0f}% of UIO, IML ratio). Rolled clutch interval ≈ {clutch_km:,} km.</p>
</section>"""


CHART_SCRIPT = """const P = __PAYLOAD__;
const FY = P.trends.fy_years.map(y => 'FY' + y);
const T = P.trends;
const charts = [];
const COL = '#CC0E1E';
const tip = {
  callbacks: {
    label(ctx) {
      const ds = ctx.dataset;
      const i = ctx.dataIndex;
      if (ds.trueData && ds.trueData[i] > 100.05) {
        return ds.label + ': ' + ctx.parsed.y + '% (true ' + ds.trueData[i] + '%+)';
      }
      return ds.label + ': ' + ctx.parsed.y + '%';
    },
  },
};
function lineDs(l, d, t, c) { return { label: l, data: d, trueData: t, borderColor: c, tension: 0.2 }; }
function mk(id, d, t, l) {
  charts.push(new Chart(document.getElementById(id), {
    type: 'line',
    data: { labels: FY, datasets: [lineDs(l, d, t, COL)] },
    options: { responsive: true, plugins: { tooltip: tip }, scales: { y: { max: 100, beginAtZero: true } } },
  }));
}
mk('cTotal', T.total, T.total_true, 'Total cover');
mk('cGenuine', T.genuine, T.genuine_true, 'Genuine');
mk('cBvp', T.bvp, T.bvp_true, 'BVP');
charts.push(new Chart(document.getElementById('cGap'), {
  type: 'bar',
  data: { labels: FY, datasets: [{ label: 'Gap €', data: T.gap_eur, backgroundColor: COL }] },
  options: { responsive: true },
}));
charts.push(new Chart(document.getElementById('cSplit'), {
  type: 'line',
  data: {
    labels: FY,
    datasets: [
      lineDs('Filters', T.filters, T.filters_true, COL),
      lineDs('Wear', T.wear, T.wear_true, '#c0552d'),
    ],
  },
  options: { responsive: true, plugins: { tooltip: tip }, scales: { y: { max: 100 } } },
}));
const catKeys = __CAT_KEYS__;
charts.push(new Chart(document.getElementById('cCats'), {
  type: 'line',
  data: {
    labels: FY,
    datasets: catKeys.map((k, i) => lineDs(
      T.categories[k].label,
      T.categories[k].capture,
      T.categories[k].capture_true,
      ['#CC0E1E', '#c0552d', '#1a2b4a', '#eda100', '#2a78d6', '#1d9e75', '#7c3aed', '#0891b2'][i],
    )),
  },
  options: { responsive: true, plugins: { tooltip: tip, legend: { position: 'bottom' } }, scales: { y: { max: 100 } } },
}));
const gaps = T.top_gaps_latest_fy;
charts.push(new Chart(document.getElementById('cTopGap'), {
  type: 'bar',
  data: { labels: gaps.map(g => g.cat), datasets: [{ data: gaps.map(g => g.gap), backgroundColor: COL }] },
  options: { indexAxis: 'y', responsive: true },
}));
const yrs = (P.attach.fy_years || []).map(String);
const u = P.attach.UTI || {};
charts.push(new Chart(document.getElementById('cAttach'), {
  type: 'line',
  data: {
    labels: yrs,
    datasets: [
      { label: 'Oil', data: yrs.map(y => (u[y] || {}).oil_filter || 0), borderColor: COL },
      { label: 'Fuel', data: yrs.map(y => (u[y] || {}).fuel_filter || 0), borderColor: '#c0552d' },
      { label: 'Air', data: yrs.map(y => (u[y] || {}).air_filter || 0), borderColor: '#1a2b4a' },
      { label: 'Brake pad', data: yrs.map(y => (u[y] || {}).brake_pad || 0), borderColor: '#eda100' },
    ],
  },
  options: { responsive: true },
}));"""


def render_html(trends: dict, attach: dict, sched: str) -> str:
    payload = json.dumps({"trends": trends, "attach": attach})
    script = (
        CHART_SCRIPT.replace("__PAYLOAD__", payload).replace("__CAT_KEYS__", json.dumps(TREND_CATS))
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>UTI PMS — FY evolution (IML)</title>
<script src="assets/chart.umd.min.js"></script>
<style>
:root {{ --red:#CC0E1E; --navy:#1a2b4a; --bg:#f5f5f5; --card:#fff; --border:#e0e0e0; --muted:#5a5a5a; }}
body {{ font-family:"Segoe UI",Calibri,sans-serif; margin:0; background:var(--bg); }}
header {{ background:var(--navy); color:#fff; padding:1.2rem 1.5rem; }}
.wrap {{ max-width:1100px; margin:0 auto; padding:1rem 1.25rem 2rem; }}
section {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; }}
section h2 {{ margin:0 0 0.2rem; font-size:1.05rem; color:var(--red); border-bottom:3px solid var(--red); padding-bottom:0.35rem; }}
section .sub {{ margin:0 0 0.75rem; font-size:0.82rem; color:var(--muted); }}
.callout {{ padding:0.65rem 0.9rem; border-left:4px solid var(--red); background:#fff8f8; font-size:0.85rem; margin-bottom:1rem; }}
table.sched {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
table.sched th {{ background:var(--navy); color:#fff; padding:0.4rem 0.5rem; }}
table.sched td {{ padding:0.35rem 0.5rem; border-bottom:1px solid var(--border); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
canvas {{ max-height:280px; }}
</style>
</head>
<body>
<header>
  <h1>UTI — PMS cover evolution (Fiscal Year)</h1>
  <p>IML v7 intervals · 100% addressable · FY2024–FY2026 billing (FY2026 ended 30 Mar 2026) · capped at 100%</p>
</header>
<div class="wrap">
<div class="callout"><strong>ISZE fiscal year</strong> = Apr–Mar (FY2026 = Apr 2025 – Mar 2026). Cover uses <strong>IML schedule</strong> — not PRISM N75. Hover charts for true % when &gt;100%.</div>
{sched}
<section><h2>1 · Total PMS cover %</h2><canvas id="cTotal"></canvas></section>
<section><h2>2 · Genuine / BVP cover %</h2><div class="grid2"><canvas id="cGenuine"></canvas><canvas id="cBvp"></canvas></div></section>
<section><h2>3 · Residual gap €</h2><canvas id="cGap"></canvas></section>
<section><h2>4 · Filters vs wear cover %</h2><canvas id="cSplit"></canvas></section>
<section><h2>5 · Category cover (FY trend)</h2><canvas id="cCats"></canvas></section>
<section><h2>6 · PMS attach rates (FY)</h2><canvas id="cAttach"></canvas></section>
<section><h2>7 · Top gaps FY2026</h2><canvas id="cTopGap"></canvas></section>
</div>
<script>
{script}
</script>
</body>
</html>"""


def main() -> None:
    sales = load_sales()
    trends = build_fy_payload(sales)
    attach = load_attach_fy()
    html = render_html(trends, attach, schedule_html())
    OUT.write_text(html, encoding="utf-8")
    print(f"Written: {OUT}")
    print(f"  FY{FY_YEARS[-1]} total true: {trends['total_true'][-1]}%")


if __name__ == "__main__":
    main()
