# -*- coding: utf-8 -*-
"""Render self-contained full sales/order study HTML from study_data.json."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "study_data.json").read_text(encoding="utf-8"))


def eur(x, k=False):
    if x is None:
        return "—"
    v = float(x)
    if k or abs(v) >= 10000:
        return f"€{v/1000:,.0f}K" if abs(v) < 1_000_000 else f"€{v/1_000_000:,.2f}M"
    return f"€{v:,.0f}"


def pct(x, signed=False):
    if x is None:
        return "—"
    v = float(x) * 100 if abs(float(x)) <= 1.5 and not signed else float(x)
    # detect already-percent
    if abs(float(x)) > 1.5:
        v = float(x)
    s = f"{v:+.1f}%" if signed else f"{v:.1f}%"
    return s


imo = next(d for d in DATA["distributors"] if d["key"] == "IMOTORS")
umi = next(d for d in DATA["distributors"] if d["key"] == "UMI")
pbi = DATA["pbi_h1_2026"]
drills = pbi.get("drills", {})
order = pbi.get("order", {})

imo_fy24 = imo["fy_totals"]["2024"]["sales_eur"]
imo_fy25 = imo["fy_totals"]["2025"]["sales_eur"]
umi_fy24 = umi["fy_totals"]["2024"]["sales_eur"]
umi_fy25 = umi["fy_totals"]["2025"]["sales_eur"]

imo_pn25 = [x for x in imo["top_pn"] if x["fiscal_year"] == 2025][:15]
umi_pn25 = [x for x in umi["top_pn"] if x["fiscal_year"] == 2025][:15]
imo_saty25 = [x for x in imo["by_saty"] if x["fiscal_year"] == 2025]
umi_saty25 = [x for x in umi["by_saty"] if x["fiscal_year"] == 2025]
imo_saty24 = [x for x in imo["by_saty"] if x["fiscal_year"] == 2024]
umi_saty24 = [x for x in umi["by_saty"] if x["fiscal_year"] == 2024]

payload_js = json.dumps(
    {
        "imo": {
            "fy": [imo_fy24, imo_fy25],
            "monthly": imo["monthly"],
            "saty24": imo_saty24,
            "saty25": imo_saty25,
            "pn25": imo_pn25,
            "gainers": imo["pn_movers_fy24_to_fy25"]["gainers"][:10],
            "losers": imo["pn_movers_fy24_to_fy25"]["losers"][:10],
            "pms_cats": sorted(imo["pms_categories_total"], key=lambda r: -r["revenue_gap_eur"])[:8],
            "conc": imo["concentration"],
        },
        "umi": {
            "fy": [umi_fy24, umi_fy25],
            "monthly": umi["monthly"],
            "saty24": umi_saty24,
            "saty25": umi_saty25,
            "pn25": umi_pn25,
            "gainers": umi["pn_movers_fy24_to_fy25"]["gainers"][:10],
            "losers": umi["pn_movers_fy24_to_fy25"]["losers"][:10],
            "pms_cats": sorted(umi["pms_categories_total"], key=lambda r: -r["revenue_gap_eur"])[:8],
            "conc": umi["concentration"],
        },
        "pbi": {
            "imo_h1": drills.get("IMOTORS", {}),
            "umi_h1": drills.get("UMI", {}),
            "order": order,
        },
    }
)


def pn_rows(rows):
    html = []
    for r in rows:
        html.append(
            f"<tr><td>{r['rank']}</td><td><code>{r['part_number']}</code></td>"
            f"<td>{r['description']}</td><td class='num'>{eur(r['sales_eur'])}</td>"
            f"<td class='num'>{r['share_pct']:.1f}%</td><td class='num'>{r['qty']:,.0f}</td></tr>"
        )
    return "\n".join(html)


def mover_rows(rows, bad=False):
    html = []
    for r in rows:
        cls = "bad" if bad else "good"
        html.append(
            f"<tr><td><code>{r['part_number']}</code></td><td>{r['description']}</td>"
            f"<td class='num'>{eur(r['fy_a_eur'])}</td><td class='num'>{eur(r['fy_b_eur'])}</td>"
            f"<td class='num {cls}'>{eur(r['delta_eur'])}</td></tr>"
        )
    return "\n".join(html)


html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>I Motors &amp; UMI — Sales &amp; Order study (FY2024–FY2025 + H1 CY2026)</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;font-size:15px;line-height:1.55;background:#f7f4ee}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}}
.wrap{{max-width:1100px;margin:0 auto;padding:0 1.25rem 4rem}}
.cover{{background:linear-gradient(155deg,#15233c 0%,#203759 60%,#2b4a78 100%);color:#eef1f6;padding:3.5rem 2rem 3rem;margin:0 0 2rem}}
.cover h1{{color:#fff;font-size:2.4rem;line-height:1.15}}
.cover .rule{{width:4.5rem;height:3px;background:#c0552d;margin:1.2rem 0 1rem}}
.cover p{{max-width:42rem;opacity:.92}}
.meta{{display:flex;flex-wrap:wrap;gap:.6rem;margin-top:1.4rem}}
.chip{{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2);padding:.25rem .7rem;border-radius:4px;font-size:.8rem}}
.tabs{{display:flex;gap:.5rem;flex-wrap:wrap;margin:0 0 1.2rem;position:sticky;top:0;z-index:5;background:#f7f4ee;padding:.6rem 0;border-bottom:1px solid #d9d3c8}}
.tabs button{{border:1px solid #d9d3c8;background:#fff;padding:.45rem .9rem;cursor:pointer;font-weight:600;color:#1a2b4a}}
.tabs button.active{{background:#1a2b4a;color:#fff;border-color:#1a2b4a}}
.panel{{display:none}}
.panel.active{{display:block}}
h2.sec{{font-size:1.45rem;margin:1.8rem 0 .5rem;padding-bottom:.35rem;border-bottom:2px solid #1a2b4a}}
h2.sec .no{{color:#c0552d}}
h3{{font-size:1.1rem;margin:1.2rem 0 .4rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.8rem;margin:1rem 0}}
.stat{{background:#fff;border:1px solid #d9d3c8;padding:.9rem 1rem}}
.stat .lbl{{font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:#6b6256}}
.stat .val{{font-size:1.35rem;font-weight:700;color:#1a2b4a;margin-top:.15rem}}
.stat .sub{{font-size:.85rem;color:#6b6256}}
.good{{color:#2e7d54!important}}
.bad{{color:#b23b3b!important}}
.callout{{border-left:3px solid #c0552d;background:#fff;padding:.9rem 1rem;margin:1rem 0}}
.callout.warn{{border-left-color:#eda100}}
.chart-box{{position:relative;width:100%;height:340px;background:#fff;border:1px solid #d9d3c8;padding:.6rem;margin:1rem 0}}
.chart-box.tall{{height:480px}}
table{{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.88rem;background:#fff}}
th{{background:#1a2b4a;color:#fff;text-align:left;padding:.55rem .65rem;font-size:.75rem;text-transform:uppercase}}
td{{padding:.5rem .65rem;border-bottom:1px solid #d9d3c8}}
tbody tr:nth-child(even){{background:#faf8f4}}
td.num,.num{{text-align:right;font-variant-numeric:tabular-nums}}
code{{font-family:Consolas,monospace;font-size:.84em}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:1rem}}
@media(max-width:800px){{.two{{grid-template-columns:1fr}}}}
.footer{{margin-top:2.5rem;padding-top:.8rem;border-top:1px solid #d9d3c8;font-size:.78rem;color:#6b6256}}
.muted{{color:#6b6256}}
</style>
</head>
<body>
<div class="cover">
  <div class="wrap" style="padding-top:0;padding-bottom:0">
    <div class="chip">ISZE Parts · Meeting prep</div>
    <h1>I Motors &amp; UMI<br/>Sales &amp; Order study</h1>
    <div class="rule"></div>
    <p>Full hierarchy across the last two complete fiscal years (FY2024 → FY2025), plus Power BI ORDER vs SALES for H1 calendar 2026. Levels: network → customer → SaTy / source / category → part number.</p>
    <div class="meta">
      <span class="chip">FY = Apr–Mar</span>
      <span class="chip">Local billing through {DATA['local_billing_max']}</span>
      <span class="chip">PBI data updated 2026-07-21</span>
      <span class="chip">Generated 2026-07-26</span>
    </div>
  </div>
</div>

<div class="wrap">
  <div class="tabs">
    <button class="active" data-tab="exec">Executive</button>
    <button data-tab="imotors">I Motors</button>
    <button data-tab="umi">UMI</button>
    <button data-tab="order">ORDER vs SALES</button>
    <button data-tab="pn">PN deep dive</button>
  </div>

  <section id="exec" class="panel active">
    <h2 class="sec"><span class="no">01</span> Executive contrast</h2>
    <div class="callout">
      <strong>Two different stories.</strong> I Motors is growing and diversified. UMI is shrinking on the invoice while demand holds — and PMS total capture is weak despite strong oil-filter cover.
    </div>
    <div class="grid">
      <div class="stat"><div class="lbl">I Motors FY2025</div><div class="val">{eur(imo_fy25)}</div><div class="sub good">+{100*(imo_fy25-imo_fy24)/imo_fy24:.1f}% vs FY2024</div></div>
      <div class="stat"><div class="lbl">UMI FY2025</div><div class="val">{eur(umi_fy25)}</div><div class="sub bad">{100*(umi_fy25-umi_fy24)/umi_fy24:.1f}% vs FY2024</div></div>
      <div class="stat"><div class="lbl">I Motors H1 CY2026 sales</div><div class="val">{eur(drills['IMOTORS']['sales_eur'])}</div><div class="sub good">+{drills['IMOTORS']['yoy_pct']:.0f}% vs H1 LY</div></div>
      <div class="stat"><div class="lbl">UMI H1 CY2026 sales</div><div class="val">{eur(drills['UMI']['sales_eur'])}</div><div class="sub bad">{drills['UMI']['yoy_pct']:.0f}% vs H1 LY</div></div>
      <div class="stat"><div class="lbl">UMI H1 demand (ORDER)</div><div class="val">{eur(order['customers']['UMI']['demand_eur'])}</div><div class="sub">−0.4% YoY — almost flat</div></div>
      <div class="stat"><div class="lbl">UMI sales–demand gap H1</div><div class="val bad">{eur(order['sales_vs_demand']['UMI']['gap_eur'])}</div><div class="sub">Demand ahead of billing</div></div>
    </div>
    <div class="chart-box"><canvas id="fyCompare" role="img" aria-label="FY2024 vs FY2025 sales I Motors and UMI"></canvas></div>
    <div class="two">
      <div class="callout">
        <strong>I Motors meeting angle</strong><br/>
        Keep the growth (+19% FY, +15% H1). Dig into emission/engine surge and competitive-parts −27% H1. PMS total capture 41.8% — gaps in brake shoe / clutch / air filter. Fill rate ~87%.
      </div>
      <div class="callout warn">
        <strong>UMI meeting angle</strong><br/>
        Do not blend with UTI. Sales −19% H1 while ORDER demand flat (−0.4%). LOCAL source −55% (Shell channel). PMS total capture only 22.7% / gap €1.11M — oil filter strong (76%), clutch &amp; brakes broken. Top-10 PNs = 40% of FY2025 (Rimula alone ~14%).
      </div>
    </div>
  </section>

  <section id="imotors" class="panel">
    <h2 class="sec"><span class="no">02</span> I Motors — Portugal</h2>
    <p class="muted">SAP sold-to 92 / 519 · legal entity I Motors · PRISM code PORTUGAL</p>
    <div class="grid">
      <div class="stat"><div class="lbl">FY2024 sales</div><div class="val">{eur(imo_fy24)}</div><div class="sub">{imo['fy_totals']['2024']['distinct_pn']:,} PNs</div></div>
      <div class="stat"><div class="lbl">FY2025 sales</div><div class="val">{eur(imo_fy25)}</div><div class="sub">{imo['fy_totals']['2025']['distinct_pn']:,} PNs · {imo['fy_totals']['2025']['lines']:,} lines</div></div>
      <div class="stat"><div class="lbl">GPS CY2025 SPU</div><div class="val">€{imo['gps'][1]['spu']:.0f}</div><div class="sub">GPS capture vs max {100*imo['gps'][1]['gps_capture_vs_max']:.0f}% · green</div></div>
      <div class="stat"><div class="lbl">PMS total capture CY2025</div><div class="val">{100*imo['pms_summary'][0]['capture_rate_total_wtd']:.1f}%</div><div class="sub">Gap {eur(imo['pms_summary'][0]['revenue_gap_eur'])} · genuine capture {100*imo['pms_summary'][0]['capture_rate_genuine_wtd']:.1f}%</div></div>
      <div class="stat"><div class="lbl">Concentration FY2025</div><div class="val">{imo['concentration']['FY2025']['top10_share_pct']:.0f}%</div><div class="sub">Top-10 share · {imo['concentration']['FY2025']['pn_for_80pct']} PNs for 80%</div></div>
      <div class="stat"><div class="lbl">H1 CY2026 fill of growth</div><div class="val good">+15%</div><div class="sub">Sales {eur(drills['IMOTORS']['sales_eur'])} · Demand {eur(order['customers']['IMOTORS']['demand_eur'])}</div></div>
    </div>
    <h3>Monthly sales — FY2024 &amp; FY2025</h3>
    <div class="chart-box"><canvas id="imoMonthly" role="img" aria-label="I Motors monthly sales"></canvas></div>
    <h3>SaTy mix (billing)</h3>
    <div class="chart-box"><canvas id="imoSaty" role="img" aria-label="I Motors SaTy mix"></canvas></div>
    <h3>H1 CY2026 — Power BI category &amp; source</h3>
    <div class="two">
      <div class="chart-box"><canvas id="imoCat" role="img" aria-label="I Motors H1 category"></canvas></div>
      <div class="chart-box"><canvas id="imoSrc" role="img" aria-label="I Motors H1 source"></canvas></div>
    </div>
    <div class="callout">H1 SO mix: SOR 85% · RUSH 11% · VOR 7%. Competitive parts −27% YoY while emission +87% and engine +77% — growth is not “more of the same basket”.</div>
    <h3>PMS category gaps (CY2025, total sales)</h3>
    <div class="chart-box"><canvas id="imoPms" role="img" aria-label="I Motors PMS gaps"></canvas></div>
  </section>

  <section id="umi" class="panel">
    <h2 class="sec"><span class="no">03</span> UMI — Israel LCV</h2>
    <p class="muted">SAP sold-to 1797 · Universal Motors Israel · separate from UTI (1799). IDS Israel = UMI only.</p>
    <div class="grid">
      <div class="stat"><div class="lbl">FY2024 sales</div><div class="val">{eur(umi_fy24)}</div><div class="sub">{umi['fy_totals']['2024']['distinct_pn']:,} PNs</div></div>
      <div class="stat"><div class="lbl">FY2025 sales</div><div class="val">{eur(umi_fy25)}</div><div class="sub bad">−{abs(100*(umi_fy25-umi_fy24)/umi_fy24):.1f}% · {umi['fy_totals']['2025']['distinct_pn']:,} PNs</div></div>
      <div class="stat"><div class="lbl">GPS CY2025 SPU</div><div class="val">€{umi['gps'][1]['spu']:.0f}</div><div class="sub">GPS capture vs max {100*umi['gps'][1]['gps_capture_vs_max']:.0f}% · green headline, Shell-heavy</div></div>
      <div class="stat"><div class="lbl">PMS total capture CY2025</div><div class="val bad">{100*umi['pms_summary'][0]['capture_rate_total_wtd']:.1f}%</div><div class="sub">Gap {eur(umi['pms_summary'][0]['revenue_gap_eur'])} · oil filter {100*umi['pms_summary'][0]['oil_filter_capture']:.0f}%</div></div>
      <div class="stat"><div class="lbl">Concentration FY2025</div><div class="val bad">{umi['concentration']['FY2025']['top10_share_pct']:.0f}%</div><div class="sub">Top-10 · only {umi['concentration']['FY2025']['pn_for_80pct']} PNs for 80%</div></div>
      <div class="stat"><div class="lbl">Rimula 550047337 FY2025</div><div class="val">{eur(umi_pn25[0]['sales_eur'])}</div><div class="sub">{umi_pn25[0]['share_pct']:.1f}% of FY sales</div></div>
    </div>
    <h3>Monthly sales — FY2024 &amp; FY2025</h3>
    <div class="chart-box"><canvas id="umiMonthly" role="img" aria-label="UMI monthly sales"></canvas></div>
    <h3>SaTy mix (billing)</h3>
    <div class="chart-box"><canvas id="umiSaty" role="img" aria-label="UMI SaTy mix"></canvas></div>
    <h3>H1 CY2026 — Power BI category &amp; source</h3>
    <div class="two">
      <div class="chart-box"><canvas id="umiCat" role="img" aria-label="UMI H1 category"></canvas></div>
      <div class="chart-box"><canvas id="umiSrc" role="img" aria-label="UMI H1 source"></canvas></div>
    </div>
    <div class="callout warn">LOCAL source −55% H1 is the Shell / Rimula channel under pressure. TH still 78% of H1 sales. Competitive &amp; emission both −29%. Engine −62%.</div>
    <h3>PMS category gaps (CY2025, total sales)</h3>
    <div class="chart-box tall"><canvas id="umiPms" role="img" aria-label="UMI PMS gaps"></canvas></div>
  </section>

  <section id="order" class="panel">
    <h2 class="sec"><span class="no">04</span> ORDER (demand) vs SALES (billing) — H1 CY2026</h2>
    <p>Power BI <strong>ORDER</strong> page = demand; <strong>SALES</strong> page = invoiced. Same period 1 Jan – 30 Jun 2026.</p>
    <div class="chart-box"><canvas id="orderVsSales" role="img" aria-label="Order versus sales H1"></canvas></div>
    <table>
      <thead><tr><th>Customer</th><th class="num">Sales H1</th><th class="num">YoY</th><th class="num">Demand H1</th><th class="num">YoY</th><th class="num">Gap</th></tr></thead>
      <tbody>
        <tr><td>UMI</td><td class="num">{eur(drills['UMI']['sales_eur'])}</td><td class="num bad">−19%</td><td class="num">{eur(order['customers']['UMI']['demand_eur'])}</td><td class="num">−0.4%</td><td class="num bad">{eur(order['sales_vs_demand']['UMI']['gap_eur'])}</td></tr>
        <tr><td>I Motors</td><td class="num">{eur(drills['IMOTORS']['sales_eur'])}</td><td class="num good">+15%</td><td class="num">{eur(order['customers']['IMOTORS']['demand_eur'])}</td><td class="num good">+14%</td><td class="num">{eur(order['sales_vs_demand']['IMOTORS']['gap_eur'])}</td></tr>
        <tr><td>UTI (context only)</td><td class="num">{eur(pbi['customers']['UTI']['sales_eur'])}</td><td class="num good">+15%</td><td class="num">{eur(order['customers']['UTI']['demand_eur'])}</td><td class="num good">+62%</td><td class="num muted">—</td></tr>
      </tbody>
    </table>
    <div class="callout">
      Israel market demand in PBI is <strong>+26.5%</strong> H1 — other Israel distributors contribute strongly to that market total. UMI’s invoice decline is not “Israel is soft”; it is a UMI-specific sales realisation / mix / Shell story. IDS Israel covers the UMI network only — do not combine other Israel distributors with IDS Israel / PMS / GPS for the UMI discussion.
    </div>
  </section>

  <section id="pn" class="panel">
    <h2 class="sec"><span class="no">05</span> Part-number deep dive — FY2025</h2>
    <div class="two">
      <div>
        <h3>I Motors — top 15 PN</h3>
        <table>
          <thead><tr><th>#</th><th>PN</th><th>Description</th><th class="num">€</th><th class="num">%</th><th class="num">Qty</th></tr></thead>
          <tbody>{pn_rows(imo_pn25)}</tbody>
        </table>
      </div>
      <div>
        <h3>UMI — top 15 PN</h3>
        <table>
          <thead><tr><th>#</th><th>PN</th><th>Description</th><th class="num">€</th><th class="num">%</th><th class="num">Qty</th></tr></thead>
          <tbody>{pn_rows(umi_pn25)}</tbody>
        </table>
      </div>
    </div>
    <h3>Biggest PN movers FY2024 → FY2025</h3>
    <div class="two">
      <div>
        <h3 class="good">I Motors gainers</h3>
        <table><thead><tr><th>PN</th><th>Desc</th><th class="num">FY24</th><th class="num">FY25</th><th class="num">Δ</th></tr></thead>
        <tbody>{mover_rows(imo['pn_movers_fy24_to_fy25']['gainers'][:10])}</tbody></table>
        <h3 class="bad">I Motors losers</h3>
        <table><thead><tr><th>PN</th><th>Desc</th><th class="num">FY24</th><th class="num">FY25</th><th class="num">Δ</th></tr></thead>
        <tbody>{mover_rows(imo['pn_movers_fy24_to_fy25']['losers'][:10], bad=True)}</tbody></table>
      </div>
      <div>
        <h3 class="good">UMI gainers</h3>
        <table><thead><tr><th>PN</th><th>Desc</th><th class="num">FY24</th><th class="num">FY25</th><th class="num">Δ</th></tr></thead>
        <tbody>{mover_rows(umi['pn_movers_fy24_to_fy25']['gainers'][:10])}</tbody></table>
        <h3 class="bad">UMI losers</h3>
        <table><thead><tr><th>PN</th><th>Desc</th><th class="num">FY24</th><th class="num">FY25</th><th class="num">Δ</th></tr></thead>
        <tbody>{mover_rows(umi['pn_movers_fy24_to_fy25']['losers'][:10], bad=True)}</tbody></table>
      </div>
    </div>
    <div class="chart-box tall"><canvas id="pnTopCompare" role="img" aria-label="Top PN share comparison"></canvas></div>
  </section>

  <div class="footer">
    Sources: ISZE billing fact (FY2024–FY2025) · Power BI SALES DATA VP NEW — SALES &amp; ORDER pages, period 1/1/2026–6/30/2026, refreshed 21 Jul 2026 · PRISM GPS/PMS CY2025 (verification green).
    Primary capture lens = total sales / total PMS capture; genuine is a secondary mix lens. UMI ≠ UTI.
  </div>
</div>

<script src="assets/chart.umd.min.js"></script>
<script>
const D = {payload_js};
const ink='#52514e', grid='#e1e0d9';
const navy='#2a78d6', terra='#c0552d', good='#1d9e75', bad='#e24b4a', grey='#888780';

document.querySelectorAll('.tabs button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  }});
}});

new Chart(fyCompare, {{
  type:'bar',
  data:{{
    labels:['FY2024','FY2025'],
    datasets:[
      {{label:'I Motors', data:D.imo.fy, backgroundColor:navy, borderRadius:4, barThickness:36}},
      {{label:'UMI', data:D.umi.fy, backgroundColor:terra, borderRadius:4, barThickness:36}}
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom'}}}},
    scales:{{y:{{ticks:{{callback:v=>'€'+(v/1e6).toFixed(1)+'M', color:ink}}, grid:{{color:grid}}}}, x:{{ticks:{{color:ink}}, grid:{{display:false}}}}}}
  }}
}});

function monthlyChart(id, rows, color) {{
  const fy24 = rows.filter(r => r.fiscal_year===2024);
  const fy25 = rows.filter(r => r.fiscal_year===2025);
  const labels = [...fy24.map(r=>r.ym.slice(5)), ...['|'], ...fy25.map(r=>r.ym.slice(5))];
  const data = [...fy24.map(r=>r.sales_eur), null, ...fy25.map(r=>r.sales_eur)];
  new Chart(document.getElementById(id), {{
    type:'bar',
    data:{{labels, datasets:[{{data, backgroundColor: data.map((v,i)=> i===fy24.length? 'transparent' : color), borderRadius:3, barThickness:10}}]}},
    options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{display:false}},
      title:{{display:true,text:'FY2024 months  |  FY2025 months', color:ink}}}},
      scales:{{y:{{ticks:{{callback:v=>'€'+(v/1000).toFixed(0)+'K', color:ink}}, grid:{{color:grid}}}}, x:{{ticks:{{color:ink, maxRotation:90, font:{{size:9}}}}, grid:{{display:false}}}}}}
    }}
  }});
}}
monthlyChart('imoMonthly', D.imo.monthly, navy);
monthlyChart('umiMonthly', D.umi.monthly, terra);

function satyChart(id, a, b) {{
  const keys = [...new Set([...a.map(x=>x.saty), ...b.map(x=>x.saty)])].filter(k => k && k!=='(blank)');
  new Chart(document.getElementById(id), {{
    type:'bar',
    data:{{
      labels: keys,
      datasets:[
        {{label:'FY2024', data: keys.map(k => (a.find(x=>x.saty===k)||{{}}).share_pct||0), backgroundColor:grey, barThickness:18}},
        {{label:'FY2025', data: keys.map(k => (b.find(x=>x.saty===k)||{{}}).share_pct||0), backgroundColor:navy, barThickness:18}}
      ]
    }},
    options:{{indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{legend:{{position:'bottom'}}}},
      scales:{{x:{{max:100, ticks:{{callback:v=>v+'%', color:ink}}, grid:{{color:grid}}}}, y:{{ticks:{{color:ink}}, grid:{{display:false}}}}}}
    }}
  }});
}}
satyChart('imoSaty', D.imo.saty24, D.imo.saty25);
satyChart('umiSaty', D.umi.saty24, D.umi.saty25);

function catChart(id, rows, color) {{
  const r = (rows||[]).slice().sort((a,b)=>b.eur-a.eur);
  new Chart(document.getElementById(id), {{
    type:'bar',
    data:{{labels:r.map(x=>x.name), datasets:[{{data:r.map(x=>x.eur), backgroundColor:r.map(x=>x.yoy<0?bad:color), borderRadius:4, barThickness:16}}]}},
    options:{{indexAxis:'y', responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}, title:{{display:true, text:'H1 CY2026 category €', color:ink}}}},
      scales:{{x:{{ticks:{{callback:v=>'€'+(v/1000).toFixed(0)+'K', color:ink}}, grid:{{color:grid}}}}, y:{{ticks:{{color:ink}}, grid:{{display:false}}}}}}
    }}
  }});
}}
function srcChart(id, rows) {{
  const r = (rows||[]).filter(x => x.eur>0);
  new Chart(document.getElementById(id), {{
    type:'doughnut',
    data:{{labels:r.map(x=>x.name+' '+x.pct.toFixed(0)+'%'), datasets:[{{data:r.map(x=>x.eur), backgroundColor:[navy, terra, good, grey]}}]}},
    options:{{responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'bottom'}}, title:{{display:true, text:'H1 CY2026 source', color:ink}}}}}}
  }});
}}
catChart('imoCat', D.pbi.imo_h1.category, navy);
catChart('umiCat', D.pbi.umi_h1.category, terra);
srcChart('imoSrc', D.pbi.imo_h1.source);
srcChart('umiSrc', D.pbi.umi_h1.source);

function pmsChart(id, rows) {{
  new Chart(document.getElementById(id), {{
    type:'bar',
    data:{{labels:rows.map(r=>r.category + ' · ' + (r.capture_rate*100).toFixed(0) + '%'), datasets:[
      {{label:'Gap €', data:rows.map(r=>r.revenue_gap_eur), backgroundColor:bad, borderRadius:4, barThickness:18}},
    ]}},
    options:{{indexAxis:'y', responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}}},
      scales:{{x:{{ticks:{{callback:v=>'€'+(v/1000).toFixed(0)+'K', color:ink}}, grid:{{color:grid}}}}, y:{{ticks:{{color:ink}}, grid:{{display:false}}}}}}
    }}
  }});
}}
pmsChart('imoPms', D.imo.pms_cats);
pmsChart('umiPms', D.umi.pms_cats);

new Chart(orderVsSales, {{
  type:'bar',
  data:{{
    labels:['UMI','I Motors'],
    datasets:[
      {{label:'Sales H1', data:[D.pbi.umi_h1.sales_eur, D.pbi.imo_h1.sales_eur], backgroundColor:navy, borderRadius:4, barThickness:28}},
      {{label:'Demand H1', data:[D.pbi.order.customers.UMI.demand_eur, D.pbi.order.customers.IMOTORS.demand_eur], backgroundColor:terra, borderRadius:4, barThickness:28}}
    ]
  }},
  options:{{responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'bottom'}}}},
    scales:{{y:{{ticks:{{callback:v=>'€'+(v/1000).toFixed(0)+'K', color:ink}}, grid:{{color:grid}}}}, x:{{ticks:{{color:ink}}, grid:{{display:false}}}}}}
  }}
}});

new Chart(pnTopCompare, {{
  type:'bar',
  data:{{
    labels:['Top 10 share','Top 25 share','Top 50 share'],
    datasets:[
      {{label:'I Motors FY2025', data:[D.imo.conc.FY2025.top10_share_pct, D.imo.conc.FY2025.top25_share_pct, D.imo.conc.FY2025.top50_share_pct], backgroundColor:navy, barThickness:22}},
      {{label:'UMI FY2025', data:[D.umi.conc.FY2025.top10_share_pct, D.umi.conc.FY2025.top25_share_pct, D.umi.conc.FY2025.top50_share_pct], backgroundColor:terra, barThickness:22}}
    ]
  }},
  options:{{responsive:true, maintainAspectRatio:false, plugins:{{legend:{{position:'bottom'}}, title:{{display:true, text:'Revenue concentration — UMI is far more top-heavy', color:ink}}}},
    scales:{{y:{{max:70, ticks:{{callback:v=>v+'%', color:ink}}, grid:{{color:grid}}}}, x:{{ticks:{{color:ink}}, grid:{{display:false}}}}}}
  }}
}});
</script>
</body>
</html>
"""

(OUT / "FULL_SALES_ORDER_STUDY.html").write_text(html, encoding="utf-8")
print("wrote", OUT / "FULL_SALES_ORDER_STUDY.html")
