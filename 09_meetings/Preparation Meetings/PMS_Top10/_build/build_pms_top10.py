#!/usr/bin/env python3
"""Top-10-by-sales (kickback) distributors — PMS cover FY evolution, IML v7 schedule.

Sections 1, 2, 5, 6, 7 from the UTI_PMS_Evolution reference, generalized across the
10 kickback distributors with a customer selector and a clickable PMS-category filter.
Same IML v7 interval schedule reused for all 10 (Jerome's call) — UTI/ITUK are the
calibrated markets; the rest are labelled illustrative in the UI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pms_top10_engine import (  # noqa: E402
    ALL_CATS,
    BRAKE_CATS,
    CLUTCH_CATS,
    FILTER_CATS,
    attach_rates,
    cap_pct,
    compute_dist_fy,
    dist_uio,
    load_sales,
    schedule_table_rows,
    IML_WEAR_FREQ,
    MILEAGE_KM_YR,
)

OUT = Path(__file__).resolve().parent.parent / "PMS_Evolution_Top10.html"
CHARTJS = Path(__file__).resolve().parent.parent / "assets" / "chart.umd.min.js"

NATIVE_FY_YEARS = [2023, 2024, 2025]
FY_YEARS = [fy + 1 for fy in NATIVE_FY_YEARS]  # Jerome's FY label = native + 1

# code -> (display label, calibration note)
DISTRIBUTORS = {
    "ITUK":     ("ITUK (UK, CV)",       "calibrated"),
    "IUK":      ("IUK (UK, LCV)",       "approx"),
    "UTI":      ("UTI (Israel, CV)",    "calibrated"),
    "UMI":      ("UMI (Israel, LCV)",   "approx"),
    "GERMANY":  ("Germany",             "approx"),
    "BELGIUM":  ("Belgium",             "approx"),
    "PORTUGAL": ("Portugal",            "approx"),
    "NORWAY":   ("Norway",              "approx"),
    "IRELAND":  ("Ireland",             "approx"),
    "SWEDEN":   ("Sweden",              "approx"),
}

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


def build_dist_payload(dist: str, sales) -> dict:
    trends: dict = {
        "fy_years": FY_YEARS,
        "uio": [],
        "total": [], "total_true": [],
        "genuine": [], "genuine_true": [],
        "bvp": [], "bvp_true": [],
        "gap_eur": [], "rev_genuine": [], "rev_bvp": [], "bvp_share": [],
        "filters": [], "filters_true": [], "wear": [], "wear_true": [],
        "categories": {},
        "attach": {},
    }
    per_fy_records = {fy: compute_dist_fy(dist, fy, sales) for fy in NATIVE_FY_YEARS}

    for fy in NATIVE_FY_YEARS:
        r = per_fy_records[fy]
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
        trends["attach"][str(fy + 1)] = attach_rates(sales, dist, fy, r["uio"])

    for cat in TREND_CATS:
        cap_s, true_s, gap_s = [], [], []
        for fy in NATIVE_FY_YEARS:
            r = per_fy_records[fy]
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

    snap = per_fy_records[NATIVE_FY_YEARS[-1]]["categories"]
    gaps = []
    for cat in ALL_CATS:
        if cat in snap and snap[cat]["total"]["gap"] > 0:
            gaps.append({
                "cat": CAT_LABELS.get(cat, cat),
                "cat_key": cat,
                "gap": int(snap[cat]["total"]["gap"]),
                "capture": cap_pct(snap[cat]["total"]["capture"])[0],
            })
    gaps.sort(key=lambda x: -x["gap"])
    trends["top_gaps_latest_fy"] = gaps[:8]
    return trends


def schedule_html() -> str:
    rows = schedule_table_rows()
    trs = "".join(
        f"<tr><td>{r['label']}</td><td>{r['freq']}×/yr</td>"
        f"<td>{r['km']:,} km</td></tr>".replace(",", ".")
        for r in rows
    )
    return f"""
<section>
  <h2>0 · IML v7 schedule (network-wide approximation)</h2>
  <p class="sub">100% addressable · {MILEAGE_KM_YR:,} km/yr parc assumption · ISZE FY = Apr–Mar</p>
  <table class="sched">
    <tr><th>Category</th><th>Frequency</th><th>Interval (km)</th></tr>
    {trs}
  </table>
  <p class="sub">Calibrated for UTI/ITUK (UK N75 truck parc). Reused as-is for the other 8 distributors
  — those numbers are illustrative, not market-calibrated (LCV duty cycles differ).</p>
</section>"""


CHART_SCRIPT = r"""
const PAYLOAD = __PAYLOAD__;
const DIST_META = __DIST_META__;
const CAT_KEYS = __CAT_KEYS__;
const distSel = document.getElementById('distSel');
const catChips = document.getElementById('catChips');
let activeCats = new Set(CAT_KEYS);
let charts = {};
const PALETTE = ['#CC0E1E', '#c0552d', '#1a2b4a', '#eda100', '#2a78d6', '#1d9e75', '#7c3aed', '#0891b2'];

function destroyAll() { Object.values(charts).forEach(c => c && c.destroy()); charts = {}; }

function tipFor(withTrue) {
  return { callbacks: { label(ctx) {
    const ds = ctx.dataset; const i = ctx.dataIndex;
    if (withTrue && ds.trueData && ds.trueData[i] != null && ds.trueData[i] > 100.05) {
      return ds.label + ': ' + ctx.parsed.y + '% (true ' + ds.trueData[i] + '%+)';
    }
    return ds.label + ': ' + (ctx.parsed.y == null ? '—' : ctx.parsed.y + '%');
  } } };
}
function lineDs(l, d, t, c) { return { label: l, data: d, trueData: t, borderColor: c, tension: 0.2 }; }

function renderCatChips() {
  catChips.innerHTML = CAT_KEYS.map(k => {
    const on = activeCats.has(k) ? 'chip on' : 'chip';
    return `<button type="button" class="${on}" data-cat="${k}">${PAYLOAD[distSel.value].categories[k].label}</button>`;
  }).join('');
  catChips.querySelectorAll('.chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const k = btn.dataset.cat;
      if (activeCats.has(k)) activeCats.delete(k); else activeCats.add(k);
      if (activeCats.size === 0) activeCats.add(k);
      render();
    });
  });
}

function render() {
  destroyAll();
  const dist = distSel.value;
  const T = PAYLOAD[dist];
  const FY = T.fy_years.map(y => 'FY' + y);

  document.getElementById('distTitle').textContent = DIST_META[dist].label +
    (DIST_META[dist].tier === 'approx' ? ' — illustrative (IML schedule not market-calibrated)' : ' — calibrated (IML v7 native market)');

  charts.cTotal = new Chart(document.getElementById('cTotal'), {
    type: 'line',
    data: { labels: FY, datasets: [lineDs('Total cover', T.total, T.total_true, '#CC0E1E')] },
    options: { responsive: true, plugins: { tooltip: tipFor(true) }, scales: { y: { max: 100, beginAtZero: true } } },
  });
  charts.cGenuine = new Chart(document.getElementById('cGenuine'), {
    type: 'line',
    data: { labels: FY, datasets: [lineDs('Genuine', T.genuine, T.genuine_true, '#CC0E1E')] },
    options: { responsive: true, plugins: { tooltip: tipFor(true) }, scales: { y: { max: 100, beginAtZero: true } } },
  });
  charts.cBvp = new Chart(document.getElementById('cBvp'), {
    type: 'line',
    data: { labels: FY, datasets: [lineDs('BVP', T.bvp, T.bvp_true, '#c0552d')] },
    options: { responsive: true, plugins: { tooltip: tipFor(true) }, scales: { y: { max: 100, beginAtZero: true } } },
  });

  const shownCats = CAT_KEYS.filter(k => activeCats.has(k));
  charts.cCats = new Chart(document.getElementById('cCats'), {
    type: 'line',
    data: {
      labels: FY,
      datasets: shownCats.map((k, i) => lineDs(
        T.categories[k].label, T.categories[k].capture, T.categories[k].capture_true,
        PALETTE[CAT_KEYS.indexOf(k) % PALETTE.length],
      )),
    },
    options: { responsive: true, plugins: { tooltip: tipFor(true), legend: { position: 'bottom' } }, scales: { y: { max: 100 } } },
  });

  const yrs = FY;
  const attach = T.attach || {};
  charts.cAttach = new Chart(document.getElementById('cAttach'), {
    type: 'line',
    data: {
      labels: yrs,
      datasets: [
        { label: 'Oil', data: T.fy_years.map(y => (attach[String(y)] || {}).oil_filter || 0), borderColor: '#CC0E1E' },
        { label: 'Fuel', data: T.fy_years.map(y => (attach[String(y)] || {}).fuel_filter || 0), borderColor: '#c0552d' },
        { label: 'Air', data: T.fy_years.map(y => (attach[String(y)] || {}).air_filter || 0), borderColor: '#1a2b4a' },
        { label: 'Brake pad', data: T.fy_years.map(y => (attach[String(y)] || {}).brake_pad || 0), borderColor: '#eda100' },
      ],
    },
    options: { responsive: true },
  });

  const gapsAll = T.top_gaps_latest_fy;
  const gaps = gapsAll.filter(g => activeCats.has(g.cat_key));
  charts.cTopGap = new Chart(document.getElementById('cTopGap'), {
    type: 'bar',
    data: { labels: gaps.map(g => g.cat), datasets: [{ data: gaps.map(g => g.gap), backgroundColor: '#CC0E1E' }] },
    options: { indexAxis: 'y', responsive: true },
  });

  renderCatChips();
}

distSel.addEventListener('change', render);
render();
"""


def render_html(payload: dict) -> str:
    dist_meta = {code: {"label": lbl, "tier": tier} for code, (lbl, tier) in DISTRIBUTORS.items()}
    options = "".join(f'<option value="{c}">{lbl}</option>' for c, (lbl, _) in DISTRIBUTORS.items())
    script = (
        CHART_SCRIPT
        .replace("__PAYLOAD__", json.dumps(payload))
        .replace("__DIST_META__", json.dumps(dist_meta))
        .replace("__CAT_KEYS__", json.dumps(TREND_CATS))
    )
    chartjs_src = CHARTJS.read_text(encoding="utf-8")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>PMS cover evolution — Top 10 (kickback distributors)</title>
<script>{chartjs_src}</script>
<style>
:root {{ --red:#CC0E1E; --navy:#1a2b4a; --bg:#f5f5f5; --card:#fff; --border:#e0e0e0; --muted:#5a5a5a; }}
body {{ font-family:"Segoe UI",Calibri,sans-serif; margin:0; background:var(--bg); }}
header {{ background:var(--navy); color:#fff; padding:1.2rem 1.5rem; }}
.wrap {{ max-width:1100px; margin:0 auto; padding:1rem 1.25rem 2rem; }}
.controls {{ display:flex; align-items:center; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.75rem; }}
.controls select {{ font-size:0.95rem; padding:0.3rem 0.5rem; }}
#distTitle {{ font-weight:600; color:var(--navy); }}
section {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:1rem 1.2rem; margin-bottom:1rem; }}
section h2 {{ margin:0 0 0.2rem; font-size:1.05rem; color:var(--red); border-bottom:3px solid var(--red); padding-bottom:0.35rem; }}
section .sub {{ margin:0 0 0.75rem; font-size:0.82rem; color:var(--muted); }}
.callout {{ padding:0.65rem 0.9rem; border-left:4px solid var(--red); background:#fff8f8; font-size:0.85rem; margin-bottom:1rem; }}
table.sched {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
table.sched th {{ background:var(--navy); color:#fff; padding:0.4rem 0.5rem; }}
table.sched td {{ padding:0.35rem 0.5rem; border-bottom:1px solid var(--border); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
canvas {{ max-height:280px; }}
#catChips {{ display:flex; flex-wrap:wrap; gap:0.4rem; margin-bottom:0.75rem; }}
.chip {{ border:1px solid var(--border); background:#f0f0f0; color:var(--muted); border-radius:999px; padding:0.25rem 0.7rem; font-size:0.8rem; cursor:pointer; }}
.chip.on {{ background:var(--red); color:#fff; border-color:var(--red); }}
</style>
</head>
<body>
<header>
  <h1>PMS cover evolution — Top 10 distributors (kickback network)</h1>
  <p>IML v7 intervals · 100% addressable · FY2024–FY2026 billing · capped at 100%</p>
</header>
<div class="wrap">
<div class="callout"><strong>ISZE fiscal year</strong> = Apr–Mar (FY2026 = Apr 2025 – Mar 2026).
Cover uses the <strong>IML schedule</strong> calibrated on UTI/ITUK; the other 8 distributors reuse the same
assumptions as an approximation (flagged per market). Hover charts for true % when &gt;100%.</div>
<div class="controls">
  <label>Customer <select id="distSel">{options}</select></label>
  <span id="distTitle"></span>
</div>
{schedule_html()}
<section><h2>1 · Total PMS cover %</h2><canvas id="cTotal"></canvas></section>
<section><h2>2 · Genuine / BVP cover %</h2><div class="grid2"><canvas id="cGenuine"></canvas><canvas id="cBvp"></canvas></div></section>
<section>
  <h2>5 · Category cover (FY trend)</h2>
  <p class="sub">Click a chip to isolate/hide a PMS part type — filters sections 5 and 7 together.</p>
  <div id="catChips"></div>
  <canvas id="cCats"></canvas>
</section>
<section><h2>6 · PMS attach rates (FY)</h2><canvas id="cAttach"></canvas></section>
<section><h2>7 · Top gaps, latest FY</h2><canvas id="cTopGap"></canvas></section>
</div>
<script>
{script}
</script>
</body>
</html>"""


def main() -> None:
    sales = load_sales()
    payload = {code: build_dist_payload(code, sales) for code in DISTRIBUTORS}
    html = render_html(payload)
    OUT.write_text(html, encoding="utf-8")
    print(f"Written: {OUT}")
    for code in DISTRIBUTORS:
        print(f"  {code}: FY{FY_YEARS[-1]} total true {payload[code]['total_true'][-1]}%")


if __name__ == "__main__":
    main()
