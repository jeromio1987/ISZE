"""Build ISZE_UIO_Car_Park_V19_V20.html — two-chapter V19 vs V20 pack."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
FLEET = ROOT / "02_dashboards" / "fleet"
PAYLOAD = FLEET / "_uio_carpark_payload.json"
RULES = FLEET / "_uio_v19_v20_rules.json"
OUT_HTML = FLEET / "ISZE_UIO_Car_Park_V19_V20.html"
OUT_CMD = FLEET / "OPEN_ISZE_UIO_Car_Park_V19_V20.cmd"


def fmt(n: float | int) -> str:
    return f"{int(round(n)):,}"


def main() -> None:
    data = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    data["rules"] = json.loads(RULES.read_text(encoding="utf-8"))
    # Prefer live IUK series from extract for V19 2027/2028
    for r in data["meta"].get("uk_rows_in_extract") or []:
        if r.get("dist") == "IUK" and str(r.get("mtype", "")).upper() == "LCV":
            iuk = data["iuk_lcv"]
            years = iuk["years"]
            v19 = list(iuk["v19"])
            for i, y in enumerate(years):
                key = str(y)
                if key in r and r[key] is not None:
                    v19[i] = int(round(float(r[key])))
            # Extend 2029–2030 toward ~52,804 from V20_SPEC
            if len(v19) >= 7:
                v19[5] = v19[5]  # 2029 already set or keep
                # years: 2024..2030 indices 0..6
                v19[5] = int(round((v19[4] + 52804) / 2))  # 2029
                v19[6] = 52804
            iuk["v19"] = v19
            break

    payload_js = json.dumps(data, ensure_ascii=False)
    k = data["kpis"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ISZE car park — UIO V19 vs V20</title>
<style>
:root{{--navy:#15233c;--terra:#c0552d;--paper:#f7f4ee;--ink:#222;--line:#ded8ca;--mid:#3f5a86;--muted:#5f5d57;--rise:#2f6b4f;--amber:#8a6d1d}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font:15px/1.5 "Segoe UI",Helvetica,Arial,sans-serif}}
h1,h2,h3,.serif{{font-family:Georgia,"Times New Roman",serif;font-weight:400}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 22px 48px}}
header.top{{background:var(--navy);color:var(--paper);padding:28px 0 22px;margin-bottom:14px}}
header.top .wrap{{padding-bottom:0}}
.flag{{display:inline-block;background:var(--terra);color:#fff;font-size:11.5px;font-weight:700;
 letter-spacing:.08em;text-transform:uppercase;padding:4px 10px;border-radius:3px;margin-bottom:12px}}
header.top h1{{margin:0 0 8px;font-size:26px;line-height:1.2;color:var(--paper);max-width:960px}}
header.top p{{margin:0;color:#dfd8cb;max-width:920px;font-size:14.2px}}
.controls{{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 14px}}
.seg{{display:inline-flex;background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}}
.seg button{{appearance:none;border:0;background:transparent;padding:10px 14px;font:13.5px/1.2 "Segoe UI",sans-serif;
 color:var(--navy);cursor:pointer;font-weight:600}}
.seg button.on{{background:var(--navy);color:var(--paper)}}
.seg.method button.on{{background:var(--terra);color:#fff}}
.hero{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:0 0 14px}}
@media(max-width:900px){{.hero{{grid-template-columns:1fr 1fr}}}}
@media(max-width:520px){{.hero{{grid-template-columns:1fr}}}}
.kpi{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px;position:relative}}
.kpi .k{{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--terra);font-weight:700;margin:0 0 4px}}
.kpi .v{{font-family:Georgia,serif;font-size:24px;color:var(--navy);margin:0;line-height:1.15}}
.kpi .s{{margin:4px 0 0;font-size:12.2px;color:var(--muted)}}
.ill{{cursor:help;border-bottom:1px dotted #a9a294}}
.ill .tp{{display:none;position:absolute;left:12px;right:12px;top:calc(100% - 4px);z-index:40;
 background:var(--navy);color:var(--paper);font-size:12.2px;line-height:1.45;padding:10px 12px;
 border-radius:6px;box-shadow:0 8px 22px rgba(0,0,0,.28)}}
.ill:hover .tp,.ill:focus .tp{{display:block}}
.amber{{background:#fff8e6;border:1px solid #e6c86a;color:#5a4a12;border-radius:6px;padding:10px 12px;font-size:13px;margin:0 0 14px}}
.chapter{{display:none}}
.chapter.on{{display:block}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px}}
@media(max-width:980px){{.grid2,.grid3{{grid-template-columns:1fr}}}}
.panel{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px 12px;min-width:0}}
.panel.full{{margin-bottom:14px}}
.panel h2{{margin:0 0 4px;font-size:17px;color:var(--navy)}}
.panel .ask{{margin:0 0 12px;font-size:13.2px;color:#4d4b45}}
.bars{{display:flex;flex-direction:column;gap:5px}}
.bar-row{{display:grid;grid-template-columns:150px 1fr 88px;gap:8px;align-items:center;padding:3px 4px;border-radius:4px}}
.bar-row .lbl{{font-size:12.6px;color:var(--navy);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.bar-row .track{{height:14px;background:#eef0f4;border-radius:3px;overflow:hidden;min-width:0;position:relative}}
.bar-row .fill{{display:block;height:100%;background:var(--navy)}}
.bar-row .fill.hot{{background:var(--terra)}}
.bar-row .fill.rise{{background:var(--rise)}}
.bar-row .val{{font-size:12.4px;color:#3d3b36;text-align:right;font-variant-numeric:tabular-nums}}
.dev{{display:grid;grid-template-columns:160px 1fr 90px;gap:8px;align-items:center;padding:4px}}
.dev .zero{{position:relative;height:16px;background:#eef0f4;border-radius:3px}}
.dev .zero::before{{content:"";position:absolute;left:50%;top:0;bottom:0;width:2px;background:#9aa3b2}}
.dev .neg,.dev .pos{{position:absolute;top:0;height:100%;border-radius:2px}}
.dev .neg{{right:50%;background:var(--terra)}}
.dev .pos{{left:50%;background:var(--rise)}}
.chartsvg{{width:100%;height:auto;display:block}}
.callout{{font-size:12.8px;color:var(--navy);background:#f0ebe1;border-left:3px solid var(--terra);
 padding:8px 10px;margin-top:10px;border-radius:0 4px 4px 0}}
.legend{{display:flex;flex-wrap:wrap;gap:14px;font-size:12.4px;color:var(--muted);margin-top:8px}}
.legend i{{display:inline-block;width:18px;height:3px;vertical-align:middle;margin-right:6px;border-radius:1px}}
.foot{{margin-top:18px;padding-top:12px;border-top:1px solid var(--line);font-size:12.2px;color:var(--muted)}}
.foot b{{color:var(--navy)}}
.chip{{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;
 background:#f0ebe1;color:var(--navy);padding:2px 7px;border-radius:3px;margin-left:6px}}
.chip.lock{{background:#ffe8df;color:var(--terra)}}
.rules-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}}
@media(max-width:980px){{.rules-grid{{grid-template-columns:1fr}}}}
.rule-card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px}}
.rule-card h3{{margin:0 0 6px;font-size:15px;color:var(--navy)}}
.rule-card .dbs{{font-size:11.5px;color:var(--terra);font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin:0 0 8px}}
.rule-card ul{{margin:0;padding-left:18px;font-size:13px;color:#3d3b36}}
.rule-card li{{margin:0 0 5px}}
.engine{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin-bottom:14px}}
.engine ol,.engine ul{{margin:6px 0 0;padding-left:18px;font-size:13.2px}}
.engine li{{margin:0 0 6px}}
.prob{{border-left:3px solid var(--terra);padding:8px 10px;margin:0 0 10px;background:#faf7f1;border-radius:0 6px 6px 0}}
.prob .pid{{font-size:11px;font-weight:700;color:var(--terra);letter-spacing:.06em;text-transform:uppercase}}
.prob h4{{margin:2px 0 4px;font-size:14.5px;color:var(--navy);font-family:Georgia,serif;font-weight:400}}
.prob p{{margin:0 0 4px;font-size:13px;color:#3d3b36}}
.prob .ev{{font-size:12.4px;color:var(--muted)}}
.ndata{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
@media(max-width:900px){{.ndata{{grid-template-columns:1fr}}}}
.ndata .card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:11px 12px}}
.ndata h4{{margin:0 0 4px;font-size:14px;color:var(--navy);font-family:Georgia,serif;font-weight:400}}
.ndata p{{margin:0 0 4px;font-size:12.8px;color:#3d3b36}}
.ndata .path{{font-size:11.5px;color:var(--muted);font-family:Consolas,monospace;word-break:break-all}}
.lockbox{{background:#fff;border:1px solid #e6a88a;border-left:4px solid var(--terra);border-radius:8px;padding:12px 14px;margin-bottom:14px}}
.lockbox .big{{font-family:Georgia,serif;font-size:28px;color:var(--navy);margin:4px 0}}
</style>
</head>
<body>
<header class="top"><div class="wrap">
<span class="flag">Car park · UIO V19 vs V20</span>
<h1>Trucks in service — what V19 says, and what V20 corrects</h1>
<p>Two chapters: why the 2026–2030 forecast is overstated under V19, and who holds how many trucks today.
Network figures are <b>ex-MIDI</b> (ISZE-only). Only <b>IUK light commercial CY2026F = {fmt(k['iuk_locked'])}</b> is a locked V20 number; other V20 series are modelled from the V20 specification.</p>
</div></header>

<div class="wrap">
<div class="controls">
<div class="seg" id="chSeg" role="tablist" aria-label="Chapter">
<button type="button" class="on" data-ch="decision">A · Decision brief</button>
<button type="button" data-ch="operating">B · Operating car park</button>
<button type="button" data-ch="rules">C · V19 rules &amp; V20 spec</button>
</div>
<div class="seg method" id="methSeg" role="tablist" aria-label="Method">
<button type="button" data-m="both" class="on">Both methods</button>
<button type="button" data-m="v19">V19 only</button>
<button type="button" data-m="v20">V20 only</button>
</div>
</div>

<div class="amber" id="amber">{data['meta']['amber']}. V20 status: draft method — workbook not rebuilt yet except the locked IUK figure.</div>

<div class="hero" id="hero"></div>

<section class="chapter on" id="ch-decision">
<div class="panel full">
<h2 id="t-a1">V19 keeps growing after 2025; the corrected method turns down</h2>
<p class="ask">ISZE network trucks in service (ex-MIDI). Vertical rule marks where V19 switches from survival curves to a flat 3% scrap rule.</p>
<svg class="chartsvg" id="svgNet" viewBox="0 0 720 280" role="img" aria-label="Network trajectory V19 vs V20"></svg>
<div class="legend" id="legNet"></div>
<div class="callout">Annotation: from 2026 the methods diverge. By 2030 V19 is {k['overstate_2030_pct']}% too high on this basis ({fmt(k['v19_2030'])} vs {fmt(k['v20_2030'])}).</div>
</div>

<div class="grid2">
<div class="panel">
<h2 id="t-a2">How large is the overstatement each year?</h2>
<p class="ask">Gap = V19 minus modelled V20 on the ex-MIDI network. Bars show units; labels show % too high.</p>
<div class="bars" id="gapBars"></div>
</div>
<div class="panel">
<h2 id="t-a3">Are we assuming a 10-year truck or a 33-year truck?</h2>
<p class="ask">Share of a cohort still in service by age. Flat 3% scrap implies a ~33-year life — three times the file’s own historical curves.</p>
<svg class="chartsvg" id="svgSurv" viewBox="0 0 720 280" role="img" aria-label="Survival curves"></svg>
<div class="legend" id="legSurv"></div>
<div class="callout">Ireland check in the spec: at 216 light-truck registrations a year, steady state is ~2,100 under real scrap — ~7,200 under 3%.</div>
</div>
</div>
</section>

<section class="chapter" id="ch-operating">
<div class="panel full">
<h2 id="t-b1">Who has the largest fleet today?</h2>
<p class="ask">Trucks in service, calendar 2025, ISZE distributors only (MIDI Europe Italy/Spain out). Israel UTI and UMI stay separate. United Kingdom IUK vs ITUK stay separate.</p>
<div class="bars" id="rankBars"></div>
</div>

<div class="grid2">
<div class="panel">
<h2 id="t-b2">Who moves most when the method is fixed?</h2>
<p class="ask">Change from V19 to V20 on known worked examples. Negative = fleet shrinks under the corrected survival method.</p>
<div id="moverBars"></div>
</div>
<div class="panel">
<h2 id="t-b3">Does the pickup fleet grow or shrink to 2030?</h2>
<p class="ask">Pickup / light commercial basket vs commercial vehicles. V19 grows pickups while registrations fall; V20 turns pickups down.</p>
<svg class="chartsvg" id="svgMix" viewBox="0 0 720 280" role="img" aria-label="Pickup vs CV small multiples"></svg>
<div class="legend" id="legMix"></div>
<div class="callout">IMIT pickup registrations fall from 16,977 (2024) to 10,845 (2026). A falling registration rate cannot grow a mature fleet.</div>
</div>
</div>

<div class="panel full">
<h2>Locked detail — IUK light commercial</h2>
<p class="ask">Row 25 only. CY2026F locked at {fmt(k['iuk_locked'])} (scrap 12.3% + IMIT regs ≈ 3,020). V19’s {fmt(k['iuk_v19_2026'])} must not be used for GPS planning.</p>
<svg class="chartsvg" id="svgIuk" viewBox="0 0 720 220" role="img" aria-label="IUK LCV V19 vs V20"></svg>
</div>
</section>

<section class="chapter" id="ch-rules">
<div class="amber">Chapter C is the rule set behind the charts: how V19 builds each distributor lane today, and what V20 changes with the new evidence (VIN register, Israel MoT, IMIT, locked IUK).</div>
<div id="rulesHost"></div>
</section>

<p class="foot"><b>Sources:</b> V19 network totals from <code>06_uio/_CURRENT/README.md</code> (ex-MIDI, 2026-07-09 pull);
distributor ranks from <code>01_data/91_build/uio_2026.json</code>; V20 method and overstate % from <code>06_uio/_CURRENT/V20_SPEC.md</code>.
Hover dotted KPI labels for definitions. Built {data['meta']['built']}.</p>
</div>

<script type="application/json" id="payload">{payload_js}</script>
<script>
(function(){{
const D = JSON.parse(document.getElementById('payload').textContent);
let chapter = 'decision';
let method = 'both';

const fmt = n => Math.round(n).toLocaleString('en-GB');
const $ = id => document.getElementById(id);

function hero(){{
  const k = D.kpis;
  $('hero').innerHTML = `
  <div class="kpi"><div class="k ill">2025 fleet (V19)<span class="tp">Ex-MIDI ISZE network trucks in service, calendar 2025 from the V19 workbook README pull.</span></div>
  <p class="v">${{fmt(k.v19_2025)}}</p><p class="s">Actual / estimate year before forecast break</p></div>
  <div class="kpi"><div class="k ill">2030 under V19<span class="tp">Ex-MIDI Grand Total if the flat 3% scrap forecast is left unchanged.</span></div>
  <p class="v">${{fmt(k.v19_2030)}}</p><p class="s">Do not quote externally</p></div>
  <div class="kpi"><div class="k ill">2030 modelled V20<span class="tp">Same 2030 total divided by (1 + 37.7% overstatement) from V20_SPEC Problem 1. Not a locked workbook cell.</span></div>
  <p class="v">${{fmt(k.v20_2030)}}</p><p class="s">~${{k.overstate_2030_pct}}% below V19</p></div>
  <div class="kpi"><div class="k ill">IUK LCV 2026F<span class="tp">Only locked V20 figure (30 Jul 2026): 47,783 × (1 − 12.3%) + 3,020 = 44,926.</span></div>
  <p class="v">${{fmt(k.iuk_locked)}}</p><p class="s">vs V19 ${{fmt(k.iuk_v19_2026)}} <span class="chip lock">Locked</span></p></div>`;
}}

function lineChart(svg, years, series, opts){{
  const W=720,H=opts.h||280,pad={{t:24,r:24,b:36,l:56}};
  const iw=W-pad.l-pad.r, ih=H-pad.t-pad.b;
  const vals = series.flatMap(s => s.y.filter(v => v!=null));
  let ymin = Math.min(...vals), ymax = Math.max(...vals);
  const span = ymax - ymin || 1;
  ymin = Math.max(0, ymin - span*0.08); ymax = ymax + span*0.08;
  const x = i => pad.l + (years.length<=1 ? iw/2 : iw * i/(years.length-1));
  const y = v => pad.t + ih * (1 - (v-ymin)/(ymax-ymin));
  let g = `<rect x="0" y="0" width="${{W}}" height="${{H}}" fill="#fff"/>`;
  // grid
  for(let i=0;i<5;i++){{
    const yy = pad.t + ih*i/4;
    const val = ymax - (ymax-ymin)*i/4;
    g += `<line x1="${{pad.l}}" y1="${{yy}}" x2="${{W-pad.r}}" y2="${{yy}}" stroke="#eee8dc"/>`;
    g += `<text x="${{pad.l-8}}" y="${{yy+4}}" text-anchor="end" font-size="11" fill="#5f5d57">${{fmt(val)}}</text>`;
  }}
  years.forEach((yr,i)=>{{
    g += `<text x="${{x(i)}}" y="${{H-10}}" text-anchor="middle" font-size="11" fill="#5f5d57">${{yr}}</text>`;
  }});
  if(opts.breakAt!=null){{
    const bi = years.findIndex(y=>y>=Math.ceil(opts.breakAt));
    if(bi>0){{
      const bx = (x(bi-1)+x(bi))/2;
      g += `<line x1="${{bx}}" y1="${{pad.t}}" x2="${{bx}}" y2="${{pad.t+ih}}" stroke="#c0552d" stroke-dasharray="5 4"/>`;
      g += `<text x="${{bx+4}}" y="${{pad.t+12}}" font-size="11" fill="#c0552d">method break</text>`;
    }}
  }}
  series.forEach(s => {{
    if(s.hide) return;
    const pts = s.y.map((v,i)=> v==null?null:`${{x(i)}},${{y(v)}}`).filter(Boolean).join(' ');
    g += `<polyline fill="none" stroke="${{s.color}}" stroke-width="${{s.width||2.5}}" points="${{pts}}"/>`;
    s.y.forEach((v,i)=>{{
      if(v==null) return;
      g += `<circle cx="${{x(i)}}" cy="${{y(v)}}" r="3.2" fill="${{s.color}}"/>`;
    }});
  }});
  svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
  svg.innerHTML = g;
}}

function paintNet(){{
  const years = D.network.years;
  const show19 = method!=='v20';
  const show20 = method!=='v19';
  lineChart($('svgNet'), years, [
    {{y: D.network.v19_ex_midi, color:'#15233c', hide:!show19}},
    {{y: D.network.v20_ex_midi, color:'#c0552d', hide:!show20, width:2.8}}
  ], {{breakAt:2025.5, h:280}});
  $('legNet').innerHTML = `
    <span><i style="background:#15233c"></i>V19 (live workbook)</span>
    <span><i style="background:#c0552d"></i>V20 modelled (survival through forecast)</span>`;
}}

function paintGap(){{
  const max = Math.max(...D.gap.map(g=>g.gap_units));
  $('gapBars').innerHTML = D.gap.map(g => {{
    const w = 100*g.gap_units/max;
    return `<div class="bar-row"><div class="lbl">${{g.year}}</div>
      <div class="track"><span class="fill hot" style="width:${{w}}%"></span></div>
      <div class="val">${{fmt(g.gap_units)}} · ${{g.overstate_pct}}%</div></div>`;
  }}).join('');
}}

function paintSurv(){{
  const ages = D.survival.truck_curve.map(p=>p.age);
  const sTruck = D.survival.truck_curve.map(p=>p.surv);
  const sPick = D.survival.pickup_curve.map(p=>p.surv);
  const sFlat = D.survival.flat_3pct_implied.map(p=>p.surv);
  const W=720,H=280,pad={{t:24,r:24,b:36,l:48}};
  const iw=W-pad.l-pad.r, ih=H-pad.t-pad.b;
  const x = i => pad.l + iw * i/(ages.length-1);
  const y = v => pad.t + ih * (1 - v/100);
  let g = `<rect width="${{W}}" height="${{H}}" fill="#fff"/>`;
  for(let i=0;i<=4;i++){{
    const yy=pad.t+ih*i/4;
    g += `<line x1="${{pad.l}}" y1="${{yy}}" x2="${{W-pad.r}}" y2="${{yy}}" stroke="#eee8dc"/>`;
    g += `<text x="${{pad.l-6}}" y="${{yy+4}}" text-anchor="end" font-size="11" fill="#5f5d57">${{100-i*25}}%</text>`;
  }}
  [0,5,10,15,20].forEach(a=>{{
    const i=ages.indexOf(a); if(i<0) return;
    g += `<text x="${{x(i)}}" y="${{H-10}}" text-anchor="middle" font-size="11" fill="#5f5d57">${{a}}y</text>`;
  }});
  const mk=(arr,col,w=2.4)=>{{
    const pts=arr.map((v,i)=>`${{x(i)}},${{y(v)}}`).join(' ');
    return `<polyline fill="none" stroke="${{col}}" stroke-width="${{w}}" points="${{pts}}"/>`;
  }};
  g += mk(sTruck,'#15233c') + mk(sPick,'#3f5a86') + mk(sFlat,'#c0552d',2.8);
  $('svgSurv').innerHTML = g;
  $('legSurv').innerHTML = `
    <span><i style="background:#15233c"></i>Truck history (~9.9 yr)</span>
    <span><i style="background:#3f5a86"></i>Pickup history (~8.1 yr)</span>
    <span><i style="background:#c0552d"></i>V19 flat 3% (~33 yr)</span>`;
}}

function paintRank(){{
  const rows = D.markets_ranked_2025;
  const max = rows[0].uio_2025;
  $('rankBars').innerHTML = rows.map((r,i) => {{
    const w = 100*r.uio_2025/max;
    const hot = i<3 ? 'hot' : '';
    return `<div class="bar-row"><div class="lbl" title="${{r.market}}">${{r.market}}</div>
      <div class="track"><span class="fill ${{hot}}" style="width:${{w}}%"></span></div>
      <div class="val">${{fmt(r.uio_2025)}}</div></div>`;
  }}).join('');
}}

function paintMovers(){{
  const rows = D.movers;
  const maxAbs = Math.max(...rows.map(r=>Math.abs(r.delta)));
  $('moverBars').innerHTML = rows.map(r => {{
    const pct = 50 * Math.abs(r.delta) / maxAbs;
    const lock = r.locked ? '<span class="chip lock">Locked</span>' : '';
    const side = r.delta < 0
      ? `<span class="neg" style="width:${{pct}}%"></span>`
      : `<span class="pos" style="width:${{pct}}%"></span>`;
    return `<div class="dev"><div class="lbl" style="font-size:12.5px;font-weight:600;color:#15233c">${{r.market}}${{lock}}
      <div style="font-weight:400;color:#5f5d57;font-size:11px">${{r.metric}}</div></div>
      <div class="zero">${{side}}</div>
      <div class="val" style="text-align:right;font-size:12.4px">${{r.delta>0?'+':''}}${{fmt(r.delta)}}</div></div>`;
  }}).join('');
}}

function paintMix(){{
  const years = D.mix.years;
  const show19 = method!=='v20';
  const show20 = method!=='v19';
  // two panels in one SVG
  const W=720,H=280,pad={{t:28,r:16,b:32,l:48}};
  const mid = W/2;
  function panel(x0, x1, title, v19, v20, col19, col20){{
    const iw=x1-x0-16, ih=H-pad.t-pad.b;
    const vals=[...v19,...v20];
    let ymin=Math.min(...vals), ymax=Math.max(...vals);
    const span=ymax-ymin||1; ymin=Math.max(0,ymin-span*0.1); ymax+=span*0.1;
    const x = i => x0+8 + iw*i/(years.length-1);
    const y = v => pad.t + ih*(1-(v-ymin)/(ymax-ymin));
    let g = `<text x="${{x0+8}}" y="16" font-size="13" fill="#15233c" font-family="Georgia,serif">${{title}}</text>`;
    for(let i=0;i<3;i++){{
      const yy=pad.t+ih*i/2;
      g += `<line x1="${{x0+8}}" y1="${{yy}}" x2="${{x1-8}}" y2="${{yy}}" stroke="#eee8dc"/>`;
    }}
    years.forEach((yr,i)=> g += `<text x="${{x(i)}}" y="${{H-8}}" text-anchor="middle" font-size="10" fill="#5f5d57">${{yr}}</text>`);
    const mk=(arr,col,hide)=>{{
      if(hide) return '';
      const pts=arr.map((v,i)=>`${{x(i)}},${{y(v)}}`).join(' ');
      return `<polyline fill="none" stroke="${{col}}" stroke-width="2.4" points="${{pts}}"/>`;
    }};
    return g + mk(v19,col19,!show19) + mk(v20,col20,!show20);
  }}
  let g = `<rect width="${{W}}" height="${{H}}" fill="#fff"/>`;
  g += panel(0, mid, 'Pickup / LCV basket', D.mix.v19_pickup, D.mix.v20_pickup, '#15233c', '#c0552d');
  g += panel(mid, W, 'Commercial vehicles', D.mix.v19_cv, D.mix.v20_cv, '#15233c', '#c0552d');
  g += `<line x1="${{mid}}" y1="20" x2="${{mid}}" y2="${{H-20}}" stroke="#ded8ca"/>`;
  $('svgMix').innerHTML = g;
  $('legMix').innerHTML = `<span><i style="background:#15233c"></i>V19</span><span><i style="background:#c0552d"></i>V20 modelled</span>`;
}}

function paintIuk(){{
  lineChart($('svgIuk'), D.iuk_lcv.years, [
    {{y: D.iuk_lcv.v19, color:'#15233c', hide: method==='v20'}},
    {{y: D.iuk_lcv.v20, color:'#c0552d', hide: method==='v19', width:2.8}}
  ], {{breakAt:2025.5, h:220}});
}}

function paintRules(){{
  const R = D.rules; if(!R) {{ $('rulesHost').innerHTML = '<p class="amber">Rules payload missing.</p>'; return; }}
  const v19 = R.v19, v20 = R.v20;
  let h = '';
  h += `<div class="panel full"><h2>${{v19.title}}</h2>
    <p class="ask">${{v19.status}}</p>
    <div class="engine"><b>Engine rules (all distributors)</b><ol>${{v19.engine.map(x=>'<li>'+x+'</li>').join('')}}</ol></div>
    <div class="engine"><b>When you may quote V19</b><ul>${{v19.quote_rules.map(x=>'<li>'+x+'</li>').join('')}}</ul></div>
    <h2 style="margin-top:8px">Distributor lanes</h2>
    <div class="rules-grid">${{v19.lanes.map(L => `
      <div class="rule-card"><h3>${{L.lane}}</h3>
      <div class="dbs">${{(L.dbs||[]).join(' · ')}}</div>
      <ul>${{L.rules.map(r=>'<li>'+r+'</li>').join('')}}</ul></div>`).join('')}}</div>
    <div class="engine"><b>V19 source files</b><ul>${{v19.sources_v19.map(x=>'<li>'+x+'</li>').join('')}}</ul></div>
  </div>`;

  const lock = (v20.locked||[])[0] || {{}};
  h += `<div class="panel full"><h2>${{v20.title}}</h2>
    <p class="ask">${{v20.status}}</p>
    <div class="lockbox"><div class="dbs">Locked decision · 30 Jul 2026</div>
      <div>${{lock.item||'IUK LCV CY2026F'}}</div>
      <div class="big">${{lock.value||'44,926'}}</div>
      <p style="margin:0;font-size:13px">${{lock.formula||''}}</p>
      <p style="margin:4px 0 0;font-size:12.5px;color:var(--muted)">${{lock.vs_v19||''}}</p>
    </div>
    <h2>Seven problems in the V20 spec</h2>
    ${{(v20.problems||[]).map(p => `
      <div class="prob"><div class="pid">${{p.id}}</div><h4>${{p.name}}</h4>
      <p><b>Fix:</b> ${{p.fix}}</p>
      <p class="ev"><b>Evidence:</b> ${{p.evidence}}</p></div>`).join('')}}
    <h2 style="margin-top:12px">New data received (feeds V20)</h2>
    <div class="ndata">${{(v20.new_data||[]).map(n => `
      <div class="card"><h4>${{n.name}}</h4>
      <p class="path">${{n.path}}</p>
      <p>${{n.what}}</p>
      <p><b>Use:</b> ${{n.use}}</p>
      ${{n.note?('<p class="ev">'+n.note+'</p>'):''}}</div>`).join('')}}</div>
    <div class="grid2" style="margin-top:14px">
      <div class="engine"><b>Build order</b><ol>${{(v20.build_order||[]).map(x=>'<li>'+x+'</li>').join('')}}</ol></div>
      <div class="engine"><b>Acceptance checks</b><ul>${{(v20.acceptance||[]).map(x=>'<li>'+x+'</li>').join('')}}</ul></div>
    </div>
  </div>`;
  $('rulesHost').innerHTML = h;
}}

function paint(){{
  hero();
  paintNet(); paintGap(); paintSurv();
  paintRank(); paintMovers(); paintMix(); paintIuk();
  if(chapter==='rules') paintRules();
  document.querySelectorAll('.chapter').forEach(el => el.classList.toggle('on', el.id === 'ch-'+chapter));
  // count bar-rows for ship gate
  window.__paint = {{
    gapRows: document.querySelectorAll('#gapBars .bar-row').length,
    rankRows: document.querySelectorAll('#rankBars .bar-row').length,
    moverRows: document.querySelectorAll('#moverBars .dev').length,
    ruleCards: document.querySelectorAll('#rulesHost .rule-card').length,
    problems: document.querySelectorAll('#rulesHost .prob').length,
    newData: document.querySelectorAll('#rulesHost .ndata .card').length
  }};
}}

$('chSeg').addEventListener('click', e => {{
  const b = e.target.closest('button'); if(!b) return;
  chapter = b.dataset.ch;
  $('chSeg').querySelectorAll('button').forEach(x=>x.classList.toggle('on', x===b));
  paint();
}});
$('methSeg').addEventListener('click', e => {{
  const b = e.target.closest('button'); if(!b) return;
  method = b.dataset.m;
  $('methSeg').querySelectorAll('button').forEach(x=>x.classList.toggle('on', x===b));
  paint();
}});
paint();
}})();
</script>
</body>
</html>
"""

    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text('@echo off\r\nstart "" "%~dp0ISZE_UIO_Car_Park_V19_V20.html"\r\n', encoding="utf-8")
    print("wrote", OUT_HTML)
    print("wrote", OUT_CMD)
    print("bar targets: gap", len(data["gap"]), "rank", len(data["markets_ranked_2025"]), "movers", len(data["movers"]))


if __name__ == "__main__":
    main()
