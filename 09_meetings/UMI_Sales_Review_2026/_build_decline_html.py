"""Build self-contained sales-analysis HTML. Chart.js inlined. No CDN.

Template for other DBs: set DB in _build_decline_payload.py, rebuild payload, then this.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = ISZE / "09_meetings" / "UMI_Sales_Review_2026"
PAYLOAD = HERE / "_decline_payload.json"
CHART = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT = HERE / "ISZE_UMI_Decline_Deep_Study.html"
CMD = HERE / "OPEN_UMI_Decline_Deep_Study.cmd"


def write_open_cmd(html_name: str) -> None:
    """Launch Chrome/Edge. Windows htmlfile still points at iexplore.exe, so start *.html is dead."""
    CMD.write_text(
        "\r\n".join(
            [
                "@echo off",
                "cd /d \"%~dp0\"",
                f'set "HTML=%~dp0{html_name}"',
                'if not exist "%HTML%" (',
                "  echo Missing %HTML%",
                "  pause",
                "  exit /b 1",
                ")",
                'if exist "%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe" (',
                '  start "" "%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe" "%HTML%"',
                "  exit /b 0",
                ")",
                'if exist "%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe" (',
                '  start "" "%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe" "%HTML%"',
                "  exit /b 0",
                ")",
                'if exist "%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe" (',
                '  start "" "%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe" "%HTML%"',
                "  exit /b 0",
                ")",
                'start "" "%HTML%"',
                "",
            ]
        ),
        encoding="ascii",
    )


def main() -> None:
    data = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    # Mode A face: drop internal codes from the embedded payload copy
    data["meta"].pop("sold_to", None)
    data["meta"].pop("not", None)
    data["meta"].pop("uti_rows_in_sales_fact", None)
    data["meta"].pop("umi_rows_sales_fact", None)
    data["meta"].pop("verification", None)
    if isinstance(data.get("pbi"), dict):
        data["pbi"].pop("source", None)
    js = CHART.read_text(encoding="utf-8", errors="ignore")
    js = re.sub(r"//# sourceMappingURL=.*", "", js)
    payload = json.dumps(data, ensure_ascii=False)
    html = TEMPLATE.replace("/*__CHART__*/", js).replace("__PAYLOAD__", payload)
    OUT.write_text(html, encoding="utf-8")
    write_open_cmd(OUT.name)
    https = len(re.findall(r"""(?:src|href)\s*=\s*['"]https://""", html, re.I))
    print("wrote", OUT, "bytes", OUT.stat().st_size, "https_src", https)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>UMI sales analysis</title>
<style>
*{box-sizing:border-box}
html,body{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#f7f4ee;font-size:15px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:#15233c;margin:0}
.cover{background:linear-gradient(155deg,#15233c 0%,#1a2b4a 55%,#2b4a78 100%);color:#f7f4ee;padding:3rem 1.5rem 2.4rem}
.cover .inner{max-width:1040px;margin:0 auto}
.cover h1{color:#fff;font-size:2.2rem;line-height:1.12}
.cover .rule{width:4.2rem;height:3px;background:#c0552d;margin:1rem 0 .9rem}
.chip{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);padding:.18rem .6rem;border-radius:4px;font-size:.76rem;margin:.12rem .2rem 0 0;color:#f7f4ee}
.nav{position:sticky;top:0;z-index:20;background:#15233c;padding:.45rem 1rem;display:flex;flex-wrap:wrap;gap:.3rem}
.nav a{font-size:.72rem;color:#f7f4ee;text-decoration:none;padding:.22rem .45rem;border:1px solid rgba(255,255,255,.2)}
.wrap{max-width:1040px;margin:0 auto;padding:1.6rem 1.3rem}
h2.sec{font-size:1.35rem;margin:1.4rem 0 .55rem;padding-bottom:.3rem;border-bottom:2px solid #15233c}
h2.sec .no{color:#c0552d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:.65rem;margin:.8rem 0}
.stat{background:#fff;border:1px solid #d9d3c8;padding:.75rem .85rem;position:relative}
.stat .lbl{font-size:.68rem;text-transform:uppercase;letter-spacing:.04em;color:#6b6256}
.stat .val{font-size:1.28rem;font-weight:700;color:#15233c;margin-top:.1rem}
.stat .sub{font-size:.8rem;color:#6b6256}
.stat[data-tip],th[data-tip]{cursor:help}
.stat[data-tip]:hover::after,th[data-tip]:hover::after{content:attr(data-tip);position:absolute;left:0;top:100%;z-index:40;width:min(300px,70vw);background:#15233c;color:#f7f4ee;padding:.55rem .7rem;font-size:.78rem;line-height:1.35;border-top:2px solid #c0552d;text-transform:none;letter-spacing:0;font-weight:400;white-space:normal}
th[data-tip]{position:relative}
th[data-tip]:hover::after{right:0;left:auto}
.tblscroll{overflow-x:auto;margin:.55rem 0;background:#fff;border:1px solid #d9d3c8}
#pntable{margin:0;min-width:880px;font-size:.8rem}
#pntable th{text-transform:none;white-space:nowrap;letter-spacing:0;font-size:.72rem;font-weight:600}
#pntable td.num,#pntable td.pn{white-space:nowrap}
#pntable td.pn{font-variant-numeric:tabular-nums}
#pntable tbody tr.spa td,#pntable tbody tr.spa:nth-child(even) td{background:#f3e4dc;color:#222}
#pntable tbody tr.spa td:first-child{box-shadow:inset 3px 0 0 #c0552d}
.spa-mark{display:inline-block;background:#c0552d;color:#f7f4ee;font-size:.62rem;letter-spacing:.03em;padding:.06rem .32rem;margin-left:.35rem;vertical-align:middle}
.submeta{display:block;font-size:.72rem;color:#6b6256;margin-top:.12rem}
.good{color:#2e7d54!important}.bad{color:#b23b3b!important}.amber{color:#a67c00!important}
.callout{border-left:3px solid #c0552d;background:#fff;padding:.8rem .95rem;margin:.85rem 0}
.callout.ok{border-left-color:#1d9e75}.callout.warn{border-left-color:#eda100}
.chart{position:relative;width:100%;height:320px;background:#fff;border:1px solid #d9d3c8;padding:.5rem;margin:.7rem 0}
.chart.tall{height:420px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:860px){.two{grid-template-columns:1fr}}
.btns{display:flex;flex-wrap:wrap;gap:.35rem;margin:.4rem 0 .7rem}
.btns button{background:#fff;border:1px solid #d9d3c8;color:#15233c;padding:.28rem .6rem;font-size:.8rem;cursor:pointer}
.btns button.on{background:#15233c;color:#f7f4ee;border-color:#15233c}
table{width:100%;border-collapse:collapse;font-size:.84rem;background:#fff;margin:.55rem 0}
th{background:#15233c;color:#f7f4ee;text-align:left;padding:.42rem .55rem;font-size:.7rem;text-transform:uppercase}
td{padding:.38rem .55rem;border-bottom:1px solid #d9d3c8;color:#222}
tbody tr:nth-child(even){background:#f7f4ee}
.num{text-align:right;font-variant-numeric:tabular-nums}
.muted{color:#6b6256;font-size:.86rem}
.legend i{display:inline-block;width:.7rem;height:.7rem;margin-right:.25rem;vertical-align:middle}
.foot{max-width:1040px;margin:0 auto;padding:1rem 1.3rem 2.2rem;font-size:.72rem;color:#6b6256}
</style>
</head>
<body>
<div class="cover"><div class="inner">
<span class="chip">UMI · Israel</span>
<span class="chip">Sales analysis</span>
<span class="chip" id="asof"></span>
<h1>UMI sales analysis</h1>
<div class="rule"></div>
<p style="max-width:42rem;opacity:.93">Official sales versus last year. The commercial book has been shrinking for two years while warranty filled the hole. Credit notes are not sales.</p>
</div></div>
<nav class="nav">
<a href="#v">01 Verdict</a><a href="#clocks">02 Families this window</a><a href="#mix">03 Families by quarter</a>
<a href="#pms">04 Above or below</a><a href="#gps">05 GPS</a><a href="#pn">06 Part numbers</a><a href="#gaps">07 Same book</a>
</nav>
<div class="wrap">

<section id="v">
<h2 class="sec"><span class="no">01</span> Verdict</h2>
<div class="grid" id="hero"></div>
<div class="grid" id="heroUnits"></div>
<div class="callout">Official Apr–Jul is <b>€875k vs €1,017k (−14%)</b>. Apr–Jun on that same cut is <b>€644k vs €644k — flat</b>. July is <b>€231k vs €373k (−€142k)</b> — that is the entire miss. This July is not in the billing file, so it cannot be split. Last July was 78% warranty.</div>
<div class="callout warn">Calendar-year totals look stable at ~€3.3m. They are not. The commercial book fell <b>−59% in two years</b> (€2.28m → €1.32m → €0.94m) while warranty grew to 56.5% of the year. That is the study. Credit notes are not sales and are not in these mix figures.</div>
</section>

<section id="clocks">
<h2 class="sec"><span class="no">02</span> Which AIM families moved in this window</h2>
<p class="muted"><b>AIM</b> is the Aftermarket Intelligence Model — the family grouping used for the rest of this page. Pale bar = last year. Terracotta = this year. Shell lubricants stay their own class. <b>Hide warranty</b> strips DPD / warranty PNs out of the family bars — Exhaust is mostly that. Default is hidden so you see the commercial book first.</p>
<div class="btns" id="winbtns"></div>
<div class="btns" id="winwarr"></div>
<div class="grid" id="winstats"></div>
<div class="chart tall"><canvas id="cWin" role="img" aria-label="AIM families this window versus last year"></canvas></div>
<p class="legend muted"><i style="background:#c5c0b5"></i>Last year &nbsp; <i style="background:#c0552d"></i>This year</p>
<div class="two">
  <div>
    <h3>Official months</h3>
    <div class="chart"><canvas id="cPbi" role="img" aria-label="Official monthly sales versus prior year"></canvas></div>
    <p class="muted">Official sales versus the same months last year. The −14% is July — and July cannot be split until it is in the billing file.</p>
    <table id="reconTable"><thead></thead><tbody></tbody></table>
    <p class="muted">Invoice lines are sales. Credit notes are not. May’s €24k credit note is why invoices sit above official; once that note is set aside, May matches official to rounding.</p>
  </div>
  <div>
    <h3>Euro change by AIM family</h3>
    <div class="chart"><canvas id="cAimDelta" role="img" aria-label="AIM family euro change this window"></canvas></div>
    <p class="muted">This year minus last year, same window. Credit notes are not sales — they are out of the family bars.</p>
  </div>
</div>
</section>

<section id="mix">
<h2 class="sec"><span class="no">03</span> AIM families by quarter — Exhaust is the warranty clock</h2>
<p class="muted" id="aimNote"></p>
<div class="btns" id="aimwarr"></div>
<div class="chart tall"><canvas id="cAimQ" role="img" aria-label="AIM families euro by quarter"></canvas></div>
<p class="legend muted" id="aimLegend"></p>
<div class="callout warn" id="aimCallout"></div>
<table id="aimTable"><thead></thead><tbody></tbody></table>
</section>

<section id="pms">
<h2 class="sec"><span class="no">04</span> Service-part capture — above or below the network</h2>
<p class="muted">This is not one race. Each family is its own comparison: <b>UMI total capture</b> versus <b>the rest of the network on that same family</b> (this distributor is not in the network bar). Navy = UMI. Grey = network. The left list is above. The right list is below. Complete calendar 2025 only. Primary capture is total (genuine + BVP), not genuine-only.</p>
<div class="two">
  <div>
    <h3>Above the network</h3>
    <p class="muted">UMI capture is higher than the network on this family.</p>
    <div class="chart" style="height:280px"><canvas id="cPmsAbove" role="img" aria-label="Families above the network"></canvas></div>
    <table id="pmsAbove"><thead></thead><tbody></tbody></table>
  </div>
  <div>
    <h3>Below the network</h3>
    <p class="muted">UMI capture is lower than the network on this family.</p>
    <div class="chart" style="height:280px"><canvas id="cPmsBelow" role="img" aria-label="Families below the network"></canvas></div>
    <table id="pmsBelow"><thead></thead><tbody></tbody></table>
  </div>
</div>
<div class="grid" id="pmsHero"></div>
<p class="muted">Oil filter sits above because BVP units do the work (genuine-only is much lower). Pads, rotors, air and fuel sit below — that is the euro gap. Apr–Jun service-basket billing is up versus last year; the capture hole is structural, not this quarter’s cliff.</p>
</section>

<section id="gps">
<h2 class="sec"><span class="no">05</span> GPS — commercial first</h2>
<div class="grid" id="gpsHero"></div>
<div class="chart" style="height:260px"><canvas id="cGps" role="img" aria-label="GPS percent three fiscal years commercial versus including warranty"></canvas></div>
<p class="muted">Headline is GPS excluding warranty (the commercial book) at 18,349 × €250. The dashed line includes warranty — that is the contractual lens, and with warranty at 56% of the year it mostly tracks warranty. Live FY2027 rate €262.50 is its own chip, not mixed into the three-year trend.</p>
</section>

<section id="pn">
<h2 class="sec"><span class="no">06</span> Part numbers — still selling, lost volume</h2>
<p class="muted">Default is live lines: sold last year and still selling this year, but less. That is the repeat-buy drop, not one-shot turbos and body that did not come back. Terracotta = quantity effect (last year’s unit price × change in units). Navy = price effect (this year’s unit price minus last year’s, × this year’s units). If this year sold zero units, price effect is €0 by definition — those sit under <b>Did not repeat</b>. <b>SPA watch</b> is Special Price Agreement candidates from our billing (wear still moving, units down). UMI still owes the PN / 12-month qty / target prices. Default hides Shell lubricants and warranty.</p>
<div class="btns" id="pnbtns"></div>
<div class="btns" id="pnshell"></div>
<div class="btns" id="pnwarr"></div>
<div class="btns" id="pnfocus"></div>
<div class="chart tall"><canvas id="cPn" role="img" aria-label="Largest euro declines quantity versus price"></canvas></div>
<p class="muted" id="pnnote"></p>
<div class="tblscroll"><table id="pntable"><thead></thead><tbody></tbody></table></div>
</section>

<section id="gaps">
<h2 class="sec"><span class="no">07</span> Same book — and what is still open</h2>
<div class="callout" id="uncodedNote"></div>
<div class="callout">Sales-to-dealer at part level from January 2025 is still with UMI. Without it we see ISZE billing, not what left their warehouse. Fill rate is not on file.</div>
<div class="callout warn">July is the whole official miss and it is not in this billing file. Last July was 78% warranty; this July cannot be split until that month lands.</div>
</section>
</div>
<p class="foot">Sources: official Apr–Jul sales cut (locked 12 Aug 2026); ISZE billing for this distributor only; credit notes are not sales; complete-year service-parts capture versus the rest of the network; GPS on this study’s billed € and 18,349 × €250. Not a customer CSV. Not another Israel distributor.</p>
<script>/*__CHART__*/</script>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
(function(){
var D = JSON.parse(document.getElementById('payload').textContent);
var ink='#52514e', grid='#e1e0d9';
function eur(v){v=Math.round(v||0); var a=Math.abs(v).toLocaleString('en-GB'); return (v<0?'\u2212':'')+'\u20ac'+a;}
function pct(v){return (v==null?'—':(v>0?'+':'')+v.toFixed(1)+'%');}
document.getElementById('asof').textContent = 'Billing through '+D.meta.as_of;
function stat(lbl,val,sub,cls,tip){
  return '<div class="stat"'+(tip?' data-tip="'+tip+'"':'')+'><div class="lbl">'+lbl+'</div><div class="val '+(cls||'')+'">'+val+'</div><div class="sub">'+sub+'</div></div>';
}
var W=D.waterfall_fy_ytd;
document.getElementById('hero').innerHTML = [
  stat('Official YTD','−14%','€875k vs €1,017k · Apr–Jul','bad','Official sales cut. Entire miss is July (−€142k). Apr–Jun is flat €644k vs €644k.'),
  stat('July is the miss',eur(W.pbi_jul_d),'€231k vs €373k last July','bad','This July is not in the billing file, so it cannot be split. Last July was 78% warranty.'),
  stat('Official Apr–Jun','flat','€644k vs €644k','','Official sales. Credit notes are not sales. Do not read invoice lines as a +€25k win.'),
  stat('Commercial book', (W.commercial_two_year_dp||0).toFixed(1)+'%', 'Calendar 2023 → 2025 · warranty share now '+W.warranty_share_cy2025+'%','bad','€2.28m → €1.32m → €0.94m. Totals look flat because warranty grew into the hole.')
].join('');
var h1n=D.windows.cy_h1_2026, h1p=D.windows.cy_h1_2025, amjN=D.windows.amj_2026, amjP=D.windows.amj_2025;
function qdp(a,b){return b?((a-b)/b*100):0;}
document.getElementById('heroUnits').innerHTML = [
  stat('H1 units', qdp(h1n.qty,h1p.qty).toFixed(1)+'%', Math.round(h1n.qty).toLocaleString('en-GB')+' vs '+Math.round(h1p.qty).toLocaleString('en-GB'),'bad','Units fell more than twice as fast as euro. Calendar January–June.'),
  stat('H1 commercial units', qdp(h1n.qty_commercial,h1p.qty_commercial).toFixed(1)+'%', 'Commercial € '+(qdp(h1n.commercial,h1p.commercial)>0?'+':'')+qdp(h1n.commercial,h1p.commercial).toFixed(1)+'%','amber','Euro up on fewer units is a mix effect, not a volume win.'),
  stat('Apr–Jun commercial units', qdp(amjN.qty_commercial,amjP.qty_commercial).toFixed(1)+'%', Math.round(amjP.qty_commercial).toLocaleString('en-GB')+' → '+Math.round(amjN.qty_commercial).toLocaleString('en-GB'),'good','April–June is different from calendar H1: more commercial units, not fewer.')
].join('');

var AIM=D.aim||{groups:[],windows:{},quarterly:[],highlights:{}};
var AIM_IDS=AIM.groups.map(function(g){return g.id;});
function aimSrc(w){
  if(!w) return {shell:0,groups:{},other:0,warranty:0};
  return (hideAimWarr && w.ex_warr) ? w.ex_warr : w;
}
function aimVec(w){
  var s=aimSrc(w);
  var labs=['Shell'].concat(AIM.groups.map(function(g){return g.label;})).concat(['Other']);
  var vals=[s.shell||0].concat(AIM_IDS.map(function(id){return (s.groups&&s.groups[id])||0;})).concat([s.other||0]);
  return {labs:labs,vals:vals};
}
var WIN_KEYS=[
  ['amj_2026','Apr–Jun 2026','amj_2025'],
  ['cy_h1_2026','Calendar H1 2026','cy_h1_2025'],
  ['l12_now','Last 12 months','l12_prior'],
  ['fy2026','FY2026 (Apr–Mar)','fy2025'],
  ['cy2025','Calendar 2025','cy2024']
];
var win=0, hideAimWarr=true, cWin, cAimDelta, cAimQ, cPn, pnMode='amj';
function paintWin(){
  var k=WIN_KEYS[win], totNow=D.windows[k[0]], totPri=D.windows[k[2]];
  var now=AIM.windows[k[0]]||{}, pri=AIM.windows[k[2]]||{};
  var n=aimSrc(now), p=aimSrc(pri);
  var dp=function(a,b){return b?((a-b)/b*100):null};
  var exN=(n.groups&&n.groups.Exhaust)||0, exP=(p.groups&&p.groups.Exhaust)||0;
  var brN=(n.groups&&n.groups['Brake parts'])||0, brP=(p.groups&&p.groups['Brake parts'])||0;
  var wTip=hideAimWarr?'Warranty PNs stripped from family bars. Exhaust without DPD.':'Warranty stays inside the family. Exhaust includes DPD.';
  var totChip = (k[0]==='amj_2026')
    ? stat('This window (official)','flat','€644k vs €644k','','Invoice lines sit higher because a May credit note is not sales.')
    : stat('This window',eur(totNow.total),'vs '+eur(totPri.total)+' prior', dp(totNow.total,totPri.total)<0?'bad':'good');
  document.getElementById('winstats').innerHTML=[
    totChip,
    stat('Warranty',eur((now.warranty||0)-(pri.warranty||0)),eur(now.warranty||0)+' now', (now.warranty||0)<(pri.warranty||0)?'bad':'good', 'Claim-grain + text. Mostly sitting in Exhaust.'),
    stat('Exhaust',eur(exN-exP),eur(exN)+' now'+(hideAimWarr?' · ex-warranty':''), exN<exP?'bad':'good', wTip),
    stat('Brakes',eur(brN-brP),eur(brN)+' now'+(hideAimWarr?' · ex-warranty':''), brN<brP?'bad':'good', 'Pads, shoes, rotors in the AIM brake group.')
  ].join('');
  var a=aimVec(pri), b=aimVec(now);
  var ds=[{label:'Last year',data:a.vals,backgroundColor:'#c5c0b5',barThickness:18},
          {label:'This year',data:b.vals,backgroundColor:'#c0552d',barThickness:18}];
  if(cWin){cWin.data.labels=b.labs; cWin.data.datasets[0].data=ds[0].data; cWin.data.datasets[1].data=ds[1].data; cWin.update();}
  else {
    cWin=new Chart(document.getElementById('cWin'),{type:'bar',data:{labels:b.labs,datasets:ds},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
        scales:{y:{ticks:{color:ink,callback:function(v){return Math.round(v/1000)+'k';}},grid:{color:grid},beginAtZero:true},
                x:{ticks:{color:ink},grid:{display:false}}}}});
  }
  var deltas=b.vals.map(function(v,i){return v-(a.vals[i]||0);});
  var dColors=deltas.map(function(v){return v<0?'#c0552d':'#1d9e75';});
  if(cAimDelta){cAimDelta.data.labels=b.labs; cAimDelta.data.datasets[0].data=deltas; cAimDelta.data.datasets[0].backgroundColor=dColors; cAimDelta.update();}
  else {
    cAimDelta=new Chart(document.getElementById('cAimDelta'),{type:'bar',
      data:{labels:b.labs,datasets:[{data:deltas,backgroundColor:dColors,barThickness:16}]},
      options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
        scales:{x:{ticks:{color:ink,callback:function(v){return Math.round(v/1000)+'k';}},grid:{color:grid}},
                y:{ticks:{color:ink},grid:{display:false}}}}});
  }
}
var box=document.getElementById('winbtns');
WIN_KEYS.forEach(function(k,i){
  var b=document.createElement('button'); b.textContent=k[1]; if(i===0)b.className='on';
  b.onclick=function(){win=i; [].forEach.call(box.children,function(x,j){x.className=j===i?'on':'';}); paintWin();};
  box.appendChild(b);
});

var AIM_COL={Exhaust:'#c0552d','Brake parts':'#15233c','Body parts':'#2a78d6',Lighting:'#c9a227',Filters:'#1d9e75',Steering:'#6b4c9a','Electrical sensors':'#3d6b8a','Engine parts':'#8b5a2b'};
var q=AIM.quarterly||[];
var lineIds=['Exhaust','Brake parts','Engine parts','Filters','Body parts'];
function qAim(r){return aimSrc(r);}
function paintAimQ(){
  document.getElementById('aimNote').textContent=hideAimWarr
    ? 'Warranty hidden. Family lines are commercial euro only — Exhaust without DPD / warranty PNs.'
    : (AIM.note||'');
  var labels=q.map(function(r){return r.label;});
  var sets=lineIds.map(function(id){
    var lab=(AIM.groups.filter(function(g){return g.id===id;})[0]||{}).label||id;
    return {label:lab,data:q.map(function(r){return (qAim(r).groups&&qAim(r).groups[id])||0;}),
      borderColor:AIM_COL[id],backgroundColor:'transparent',tension:.2,pointRadius:4,borderWidth:2};
  }).concat([{label:'Shell lubricants',data:q.map(function(r){return qAim(r).shell||0;}),
    borderColor:'#888780',backgroundColor:'transparent',borderDash:[6,4],tension:.2,pointRadius:4,borderWidth:2}]);
  if(cAimQ){
    cAimQ.data.labels=labels;
    sets.forEach(function(s,i){cAimQ.data.datasets[i].data=s.data;});
    cAimQ.update();
  } else {
    cAimQ=new Chart(document.getElementById('cAimQ'),{type:'line',
      data:{labels:labels,datasets:sets},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
        scales:{y:{beginAtZero:true,ticks:{color:ink,callback:function(v){return Math.round(v/1000)+'k';}},grid:{color:grid}},
                x:{ticks:{color:ink},grid:{display:false}}}}});
  }
  document.getElementById('aimLegend').innerHTML=hideAimWarr
    ? 'Lines are commercial billed euro by AIM family. Dashed grey is Shell. Warranty is off.'
    : 'Lines are billed euro by AIM family. Dashed grey is Shell lubricants. Exhaust includes DPD / warranty until you hide it.';
  function qg(qq,gid){
    var row=q.filter(function(r){return r.q===qq;})[0]||{};
    return (qAim(row).groups&&qAim(row).groups[gid])||0;
  }
  document.getElementById('aimCallout').innerHTML='Exhaust ran '+eur(qg('2025Q2','Exhaust'))+' in Q2 2025, '+eur(qg('2025Q3','Exhaust'))+' in Q3, then '+eur(qg('2025Q4','Exhaust'))+' in Q4'+(hideAimWarr?' with warranty hidden.':' — that is the warranty clock.')+' Brakes ran '+eur(qg('2025Q1','Brake parts'))+' / '+eur(qg('2025Q2','Brake parts'))+' / '+eur(qg('2025Q3','Brake parts'))+' across the same three quarters.';
  var thead=document.querySelector('#aimTable thead');
  var tbody=document.querySelector('#aimTable tbody');
  thead.innerHTML='<tr><th>AIM family</th>'+q.map(function(r){return '<th class="num">'+r.label+'</th>';}).join('')+'</tr>';
  var rows=AIM.groups.concat([{id:'_other',label:'Other families'},{id:'_shell',label:'Shell lubricants'}]);
  tbody.innerHTML=rows.map(function(g){
    return '<tr><td>'+g.label+'</td>'+q.map(function(r){
      var s=qAim(r);
      var v=g.id==='_shell'?s.shell:(g.id==='_other'?s.other:((s.groups&&s.groups[g.id])||0));
      return '<td class="num">'+eur(v)+'</td>';
    }).join('')+'</tr>';
  }).join('');
}
function bindAimWarr(boxId){
  var box=document.getElementById(boxId);
  if(!box) return;
  var ba=document.createElement('button'); ba.textContent='Hide warranty';
  var bb=document.createElement('button'); bb.textContent='Show warranty';
  function apply(hide){
    hideAimWarr=hide;
    document.querySelectorAll('[data-aim-warr]').forEach(function(el){
      var hideBtn=el.children[0], showBtn=el.children[1];
      if(hideBtn) hideBtn.className=hide?'on':'';
      if(showBtn) showBtn.className=hide?'':'on';
    });
    paintWin();
    paintAimQ();
  }
  box.setAttribute('data-aim-warr','1');
  ba.onclick=function(){apply(true);};
  bb.onclick=function(){apply(false);};
  box.appendChild(ba); box.appendChild(bb);
  ba.className=hideAimWarr?'on':'';
  bb.className=hideAimWarr?'':'on';
}
bindAimWarr('winwarr');
bindAimWarr('aimwarr');
paintWin();
paintAimQ();

new Chart(document.getElementById('cPbi'),{type:'bar',
  data:{labels:D.pbi.months,datasets:[
    {label:'Prior year',data:D.pbi.prev_year,backgroundColor:'#c5c0b5',barThickness:22},
    {label:'Official this year',data:D.pbi.sales,backgroundColor:'#c0552d',barThickness:22}
  ]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
    scales:{y:{beginAtZero:true,ticks:{color:ink,callback:function(v){return Math.round(v/1000)+'k';}},grid:{color:grid}},
            x:{ticks:{color:ink},grid:{display:false}}}}});
(function(){
  var rec=D.recon||[];
  var th=document.querySelector('#reconTable thead');
  var tb=document.querySelector('#reconTable tbody');
  if(!th||!tb) return;
  th.innerHTML='<tr><th>Month</th><th class="num">Official</th><th class="num">Invoice lines</th><th class="num">Credit notes</th><th>Note</th></tr>';
  tb.innerHTML=rec.map(function(r){
    var note=r.month==='Jul'&&!r.in_file?'Not in the billing file yet — cannot split.':
      (Math.abs(r.credit_note_eur)>1?'Credit note is not sales. Official matches invoices once it is set aside.':
      (Math.abs(r.gap_invoices_vs_official)<2000?'Same book.':''));
    return '<tr><td>'+r.month+'</td><td class="num">'+eur(r.official)+'</td><td class="num">'+eur(r.invoice_eur)+'</td><td class="num">'+(r.credit_note_eur?eur(r.credit_note_eur):'—')+'</td><td>'+note+'</td></tr>';
  }).join('');
})();

var pms=D.pms.categories.filter(function(c){return c.critical && c.cy2025_pct!=null && !c.skip_best_series;});
var above=pms.filter(function(c){return (c.cy2025_pct||0)>=(c.network_pct||0);}).sort(function(a,b){return (b.cy2025_pct||0)-(a.cy2025_pct||0);});
var below=pms.filter(function(c){return (c.cy2025_pct||0)<(c.network_pct||0);}).sort(function(a,b){return (a.cy2025_pct||0)-(b.cy2025_pct||0);});
function paintPmsSide(canvasId, tableId, rows){
  new Chart(document.getElementById(canvasId),{type:'bar',
    data:{labels:rows.map(function(c){return c.label;}),
      datasets:[
        {label:'UMI',data:rows.map(function(c){return c.cy2025_pct;}),backgroundColor:'#15233c',barThickness:14},
        {label:'Network',data:rows.map(function(c){return c.network_pct;}),backgroundColor:'#c5c0b5',barThickness:14}
      ]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
      scales:{x:{max:100,ticks:{color:ink,callback:function(v){return v+'%';}},grid:{color:grid}},
              y:{ticks:{color:ink},grid:{display:false}}}}});
  var th=document.querySelector('#'+tableId+' thead');
  var tb=document.querySelector('#'+tableId+' tbody');
  th.innerHTML='<tr><th>Family</th><th class="num">UMI</th><th class="num">Network</th><th class="num">Gap</th></tr>';
  tb.innerHTML=rows.map(function(c){
    var gap=(c.cy2025_pct||0)-(c.network_pct||0);
    return '<tr><td>'+c.label+'</td><td class="num">'+c.cy2025_pct.toFixed(1)+'%</td><td class="num">'+(c.network_pct==null?'—':c.network_pct.toFixed(1)+'%')+'</td><td class="num">'+(gap>=0?'+':'')+gap.toFixed(1)+' pt</td></tr>';
  }).join('');
}
paintPmsSide('cPmsAbove','pmsAbove',above);
paintPmsSide('cPmsBelow','pmsBelow',below);
var oil=pms.filter(function(c){return c.id==='oil_filter';})[0]||{};
var pad=pms.filter(function(c){return c.id==='brake_pad';})[0]||{};
document.getElementById('pmsHero').innerHTML=[
  stat('Oil filter is ABOVE', (oil.cy2025_pct||0).toFixed(1)+'%','Network '+(oil.network_pct==null?'—':Number(oil.network_pct).toFixed(1))+'% · genuine-only '+((oil.genuine_cy2025_pct||0).toFixed(1))+'%','good','Total = genuine + BVP units ÷ expected. BVP does most of the oil-filter work.'),
  stat('Brake pads are BELOW', (pad.cy2025_pct||0).toFixed(1)+'%','Network '+(pad.network_pct==null?'—':pad.network_pct.toFixed(1))+'% · largest euro gap among wear items','bad','UMI versus the rest of the network on this family. Not a comparison with oil.'),
  stat('UIO in capture file', (D.pms.uio_units||0).toLocaleString('en-GB'), D.pms.uio_note, '', D.pms.uio_note)
].join('');

var gIncl=D.gps.gps_pct_incl_warr, gEx=D.gps.gps_pct_ex_warr;
var live=(D.gps.gps_pct_incl_warr_live_rate||{}).FY2026;
document.getElementById('gpsHero').innerHTML=[
  stat('GPS commercial FY2024', gEx.FY2024+'%', eur(D.gps.net.FY2024), '', D.gps.formula_ex),
  stat('GPS commercial FY2025', gEx.FY2025+'%', eur(D.gps.net.FY2025), 'bad', D.gps.formula_ex),
  stat('GPS commercial FY2026', gEx.FY2026+'%', eur(D.gps.net.FY2026)+' · the commercial truth', 'bad', D.gps.formula_ex),
  stat('GPS incl. warranty FY2026', gIncl.FY2026+'%', 'Contractual lens · at live €262.50 → '+(live||'—')+'%', '', D.gps.formula_incl)
].join('');
var gpsVals=[gIncl.FY2024,gIncl.FY2025,gIncl.FY2026,gEx.FY2024,gEx.FY2025,gEx.FY2026];
var gpsLo=Math.max(0, Math.floor((Math.min.apply(null,gpsVals)-8)/5)*5);
var gpsHi=Math.min(100, Math.ceil((Math.max.apply(null,gpsVals)+8)/5)*5);
new Chart(document.getElementById('cGps'),{type:'line',
  data:{labels:['FY2024','FY2025','FY2026'],
    datasets:[
      {label:'Commercial (ex-warranty)',data:[gEx.FY2024,gEx.FY2025,gEx.FY2026],
        borderColor:'#c0552d',backgroundColor:'rgba(192,85,45,.12)',fill:true,tension:.25,pointRadius:5},
      {label:'Including warranty',data:[gIncl.FY2024,gIncl.FY2025,gIncl.FY2026],
        borderColor:'#2a78d6',backgroundColor:'transparent',borderDash:[6,4],fill:false,tension:.25,pointRadius:5}
    ]},
  options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:ink}}},
    scales:{y:{min:gpsLo,max:gpsHi,ticks:{color:ink,callback:function(v){return v+'%';}},grid:{color:grid}},
            x:{ticks:{color:ink},grid:{display:false}}}}});

function paintPn(){
  var src=(D.pn[pnMode]||[]).filter(function(r){
    if(hideShell && r.shell) return false;
    if(hideWarr && r.warranty) return false;
    if(pnFocus==='live') return r.still_selling && r.d<0;
    if(pnFocus==='gone') return r.did_not_repeat && r.d<0;
    if(pnFocus==='spa') return r.spa_watch;
    if(pnFocus==='pms') return r.low_pms && r.d<0;
    return r.d<0;
  });
  var rows=src.slice(0,15);
  var labels=rows.map(function(r){
    var d=(r.desc||'').replace(/\s+/g,' ').slice(0,22);
    return (r.pn||'')+'  '+d;
  });
  var cfg={type:'bar',data:{labels:labels,datasets:[
      {label:'Quantity effect',data:rows.map(function(r){return r.qty_effect;}),backgroundColor:'#c0552d',barThickness:16},
      {label:'Price effect',data:rows.map(function(r){return r.price_effect;}),backgroundColor:'#2a78d6',barThickness:16}
    ]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{color:ink}},
        tooltip:{callbacks:{
          label:function(ctx){
            var r=(ctx.chart._pnRows||rows)[ctx.dataIndex]||{};
            if(ctx.datasetIndex===0) return 'Quantity effect: last year unit price × Δ units = '+eur(r.qty_effect);
            return 'Price effect: (this year unit price − last year) × this year units = '+eur(r.price_effect);
          },
          afterBody:function(items){
            var r=(cPn && cPn._pnRows || rows)[(items[0]||{}).dataIndex]||{};
            var extra=['','Quantity = last year unit price × change in units.','Price = (this year unit price − last year) × this year units.'];
            if(!(r.qty_now>0)) extra.push('This year sold zero units, so price effect is €0 by definition.');
            return extra;
          }
        }}},
      scales:{x:{ticks:{color:ink,callback:function(v){return Math.round(v/1000)+'k';}},grid:{color:grid}},
              y:{ticks:{color:ink,font:{size:10}},grid:{display:false}}}}};
  if(cPn){cPn.data.labels=cfg.data.labels; cPn.data.datasets[0].data=cfg.data.datasets[0].data; cPn.data.datasets[1].data=cfg.data.datasets[1].data; cPn._pnRows=rows; cPn.update();}
  else {cPn=new Chart(document.getElementById('cPn'),cfg); cPn._pnRows=rows;}
  var note=document.getElementById('pnnote');
  var bits=[];
  bits.push(hideShell?'Shell lubricants hidden.':'Shell lubricants shown.');
  bits.push(hideWarr?'Warranty hidden.':'Warranty shown.');
  bits.push({
    live:'View is still selling, but less — the live commercial book, not one-shots that did not repeat.',
    gone:'View is sold last year and not this year. That is not a Special Price Agreement list.',
    spa:'View is Special Price Agreement watch: wear still moving, still selling, units down. Candidates from our billing; UMI still owes PN / 12-month qty / target prices.',
    pms:'View is service parts whose total capture sits under 30% (or well under the network). Primary capture is total, not genuine-only.'
  }[pnFocus]||'');
  bits.push(src.length+' part numbers in this cut; table shows the 15 largest euro drops.');
  note.textContent=bits.join(' ');
  var thead=document.querySelector('#pntable thead');
  var tbody=document.querySelector('#pntable tbody');
  thead.innerHTML='<tr>'
    +'<th>PN</th><th>Part</th>'
    +'<th class="num">Last year</th><th class="num">This year</th>'
    +'<th class="num">Units</th><th class="num">€ change</th>'
    +'<th class="num" data-tip="Last year unit price × change in units.">Qty effect</th>'
    +'<th class="num" data-tip="(This year unit price − last year) × this year units. If this year sold zero units, price effect is €0 by definition.">Price effect</th>'
    +'</tr>';
  tbody.innerHTML=rows.map(function(r){
    var meta=[];
    if(r.pms_label) meta.push(r.pms_label);
    if(r.pms_capture_pct!=null) meta.push(r.pms_capture_pct.toFixed(1)+'% capture');
    var sub=meta.length?'<span class="submeta">'+meta.join(' · ')+'</span>':'';
    var mark=r.spa_watch?'<span class="spa-mark">SPA</span>':'';
    var units=Math.round(r.qty_prior||0)+'\u00a0→\u00a0'+Math.round(r.qty_now||0);
    return '<tr'+(r.spa_watch?' class="spa"':'')+'>'
      +'<td class="pn">'+r.pn+mark+'</td>'
      +'<td>'+(r.desc||'')+sub+'</td>'
      +'<td class="num">'+eur(r.eur_prior)+'</td>'
      +'<td class="num">'+eur(r.eur_now)+'</td>'
      +'<td class="num">'+units+'</td>'
      +'<td class="num">'+eur(r.d)+'</td>'
      +'<td class="num">'+eur(r.qty_effect)+'</td>'
      +'<td class="num">'+eur(r.price_effect)+'</td>'
      +'</tr>';
  }).join('');
}
var hideShell=true, hideWarr=true, pnFocus='live';
var pnb=document.getElementById('pnbtns');
[['amj','Apr–Jun'],['cy_h1','Calendar H1'],['l12','Last 12 months']].forEach(function(k,i){
  var b=document.createElement('button'); b.textContent=k[1]; if(i===0)b.className='on';
  b.onclick=function(){pnMode=k[0]; [].forEach.call(pnb.children,function(x,j){x.className=j===i?'on':'';}); paintPn();};
  pnb.appendChild(b);
});
function togglePair(boxId, aLabel, bLabel, setA){
  var box=document.getElementById(boxId);
  var ba=document.createElement('button'); ba.textContent=aLabel; ba.className='on';
  var bb=document.createElement('button'); bb.textContent=bLabel;
  ba.onclick=function(){setA(true); ba.className='on'; bb.className=''; paintPn();};
  bb.onclick=function(){setA(false); bb.className='on'; ba.className=''; paintPn();};
  box.appendChild(ba); box.appendChild(bb);
}
togglePair('pnshell','Hide Shell lubricants','Show Shell lubricants', function(v){hideShell=v;});
togglePair('pnwarr','Hide warranty','Show warranty', function(v){hideWarr=v;});
(function(){
  var box=document.getElementById('pnfocus');
  var opts=[['live','Still selling, lost volume'],['gone','Did not repeat'],['spa','SPA watch'],['pms','Weak capture']];
  opts.forEach(function(k,i){
    var b=document.createElement('button'); b.textContent=k[1]; if(i===0)b.className='on';
    b.onclick=function(){
      pnFocus=k[0];
      [].forEach.call(box.children,function(x,j){x.className=j===i?'on':'';});
      paintPn();
    };
    box.appendChild(b);
  });
})();
paintPn();
var u=D.windows.amj_2026||{};
var un=document.getElementById('uncodedNote');
if(un){
  un.innerHTML='About <b>'+(u.uncoded_share||0)+'%</b> of April–June invoice euros have no order type coded ('+eur(u.uncoded_eur)+', '+(u.uncoded_lines||0)+' lines). Those lines look like real product — they include all Shell in the window. The commercial euro move on that window is therefore not fully checkable on order type. Credit notes are not in this mix.';
}
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
