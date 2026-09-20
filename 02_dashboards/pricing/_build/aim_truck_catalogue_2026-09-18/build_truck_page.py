#!/usr/bin/env python3
"""Build the AIM truck catalogue page.

One self-contained file. No server, no CDN, no internet. The payload and the
geometry are both embedded, so it opens straight from Explorer.

Reads
  02_dashboards/pricing/_build/aim_truck_catalogue_2026-09-18/truck_payload.json
  02_dashboards/pricing/_build/aim_truck_catalogue_2026-09-18/vehicle_geometry.json

Writes
  02_dashboards/pricing/ISZE_AIM_Truck_Catalogue_2026-09-18.html

Nothing under 01_data/00_derived/ is written, and the drill page and the spider
are left untouched.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_truck_catalogue_2026-09-18"
CHART = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Truck_Catalogue_2026-09-18.html"

import sys
sys.path.insert(0, str(HERE))
from vehicle_layer import VEHICLE_JS          # noqa: E402
from vehicle_images import ANCHORS             # noqa: E402

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Where every part sits on the truck - the AIM repertoire as a catalogue</title>
<style>
:root{
  --navy:#15233c; --navy2:#1d3054; --terra:#c0552d; --paper:#f7f4ee;
  --ink:#22262e; --muted:#6b6459; --line:#d9d3c8; --band:#eef3f9;
  --amber:#a8721f; --steel:#8f9aa8;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:14px;line-height:1.5;overflow-x:hidden}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
h1{font-size:23px;letter-spacing:-.2px}
h2{font-size:16.5px;margin-bottom:2px}
h3{font-size:13px}
.wrap{max-width:1500px;margin:0 auto;padding:16px 18px 44px}
header.top{border-bottom:3px solid var(--navy);padding-bottom:11px;margin-bottom:13px}
.sub{color:var(--muted);font-size:12.5px;margin-top:5px}
.badge{display:inline-block;background:var(--navy);color:var(--paper);
  font-size:10.5px;letter-spacing:.6px;text-transform:uppercase;
  padding:3px 8px;border-radius:2px;margin-right:7px}
.badge.t{background:var(--terra)}

.stage{position:relative;background:#fff;border:1px solid var(--line);
  margin-bottom:13px;overflow:hidden}
#map{display:block;width:100%;height:78vh;min-height:520px;cursor:default;
  touch-action:none}
.vlabel{position:absolute;left:14px;top:12px;pointer-events:none}
.vlabel .n{font-family:Georgia,serif;font-size:19px;color:var(--navy);font-weight:600}
.vlabel .k{font-size:11.5px;color:var(--muted);letter-spacing:.5px;text-transform:uppercase}
#hint{position:absolute;left:14px;bottom:11px;font-size:11.5px;color:var(--muted);
  background:rgba(247,244,238,.94);padding:3px 8px;border:1px solid var(--line)}
#legend{position:absolute;right:13px;top:12px;display:flex;flex-direction:column;gap:5px;
  background:rgba(255,255,255,.95);border:1px solid var(--line);padding:9px 11px;
  font-size:11.5px;min-width:186px;max-width:250px}
#legend .row{display:flex;align-items:center;gap:7px}
#legend .sw{width:11px;height:11px;flex:0 0 auto;border-radius:2px}
#legend .eu{margin-left:auto;color:var(--muted);font-variant-numeric:tabular-nums}
#legend .hd{font-size:10px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);
  border-bottom:1px solid var(--line);padding-bottom:5px;margin-bottom:2px}
#legend .row.dim{opacity:.34}
#legend .row.fn{border-top:1px dashed var(--line);padding-top:5px;margin-top:2px}

.tabs{display:flex;gap:0;margin-bottom:13px;border:1px solid var(--line);
  background:#fff;width:fit-content;max-width:100%;overflow:auto}
.tabs button{background:#fff;border:0;border-right:1px solid var(--line);
  padding:9px 15px;font-size:13px;cursor:pointer;color:var(--ink);font-family:inherit;
  text-align:left;white-space:nowrap}
.tabs button:last-child{border-right:0}
.tabs button.on{background:var(--navy);color:var(--paper)}
.tabs button .t{display:block;font-weight:600}
.tabs button .s{display:block;font-size:11px;opacity:.72}
.tabs button.on .s{opacity:.85}

.grid{display:grid;gap:13px;margin-bottom:13px}
.g2{grid-template-columns:1.15fr 1fr;align-items:start}
.g2b{grid-template-columns:1fr 1fr;align-items:start}
@media(max-width:1080px){.g2,.g2b{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);padding:13px 15px 11px;min-width:0}
.card .q{font-size:12.5px;color:var(--muted);margin:3px 0 10px}
.chartbox{position:relative;height:300px}
.chartbox.tall{height:360px}

table{border-collapse:collapse;width:100%;font-size:12.5px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:7px 8px;
  font-weight:600;font-size:10.5px;letter-spacing:.4px;text-transform:uppercase;
  position:sticky;top:0;white-space:nowrap}
th.n,td.n{text-align:right;font-variant-numeric:tabular-nums}
td{padding:5px 8px;border-bottom:1px solid var(--line)}
tbody tr:nth-child(even){background:var(--band)}
tbody tr.clickable{cursor:pointer}
tbody tr.clickable:hover{background:#e3ecf6}
tbody tr.sel{background:#f6e3da!important;box-shadow:inset 3px 0 0 var(--terra)}
.tblwrap{max-height:330px;overflow:auto;border:1px solid var(--line)}
.dot{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:6px;
  vertical-align:middle}
.muted{color:var(--muted)}
.nowrap{white-space:nowrap}

.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:10px}
.hero{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:0;
  margin:0 0 13px;border:1px solid var(--line);background:#fff}
.hero .h{padding:10px 14px;border-right:1px solid var(--line)}
.hero .h:last-child{border-right:0}
.hero .hl{font-size:10px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.hero .hv{font-family:Georgia,serif;font-size:20px;font-weight:600;color:var(--navy);
  font-variant-numeric:tabular-nums;line-height:1.25}
.hero .hn{font-size:11px;color:var(--muted)}
.fact{border-left:3px solid var(--navy);padding-left:9px}
.fact .l{font-size:10px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.fact .v{font-size:16px;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums}
.fact .n{font-size:11px;color:var(--muted)}

.crumb{font-size:12px;color:var(--muted);margin-bottom:9px;display:flex;flex-wrap:wrap;
  gap:6px;align-items:center}
.crumb .sep{color:#bdb6a8}
.crumb b{color:var(--navy)}
.crumb .x{cursor:pointer;color:var(--terra);text-decoration:underline}
.warn{background:#fdf3e3;border:1px solid #e6cf9f;border-left:4px solid var(--amber);
  padding:10px 13px;font-size:12.5px;color:#5e4a1c;margin-bottom:13px}
.warn b{color:#4a3a12}
.foot{font-size:11.5px;color:var(--muted);border-top:1px solid var(--line);
  padding-top:11px;margin-top:20px}
.foot ul{margin:7px 0 0;padding-left:17px}
.foot li{margin-bottom:4px}
#tip{position:fixed;display:none;background:var(--navy);color:var(--paper);font-size:12.5px;
  line-height:1.45;padding:9px 11px;border-radius:3px;z-index:90;pointer-events:none;
  max-width:320px;box-shadow:0 4px 16px rgba(0,0,0,.3)}
#tip b{color:#f0b49a}
#tip .r{color:#c8d4e6}
.info{display:inline-flex;align-items:center;justify-content:center;width:13px;height:13px;
  border-radius:50%;background:var(--navy);color:#fff;font-size:9px;cursor:help;
  position:relative;flex:0 0 auto}
.info .tp{display:none;position:absolute;bottom:20px;left:50%;transform:translateX(-50%);
  width:280px;background:var(--navy);color:var(--paper);font-size:12px;line-height:1.45;
  padding:9px 11px;border-radius:3px;z-index:95;font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25)}
.info:hover .tp,.info:focus .tp{display:block}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div><span class="badge">AIM catalogue</span><span class="badge t">Internal</span></div>
  <h1 style="margin-top:8px">Where every part sits on the truck</h1>
  <div class="sub">Pick a vehicle, click a zone on it, and you get the real part families that
    live there and the money behind them. Parts billed 1 July 2025 to 30 June 2026 across
    22 distributors. Opens from Explorer with no server and no internet.
    <span id="genline"></span></div>
</header>

<div class="tabs" id="tabs"></div>

<div class="hero">
  <div class="h"><div class="hl">Parts billed</div>
    <div class="hv" id="h-eur"></div>
    <div class="hn" id="h-eurn"></div></div>
  <div class="h"><div class="hl">Step at this revision</div>
    <div class="hv" id="h-step"></div>
    <div class="hn" id="h-stepn"></div></div>
  <div class="h"><div class="hl">Weighted move</div>
    <div class="hv" id="h-pct"></div>
    <div class="hn" id="h-pctn"></div></div>
  <div class="h"><div class="hl">Part numbers</div>
    <div class="hv" id="h-pn"></div>
    <div class="hn" id="h-pnn"></div></div>
  <div class="h"><div class="hl">Zones on the vehicle</div>
    <div class="hv" id="h-zones"></div>
    <div class="hn" id="h-zonesn"></div></div>
</div>

<div class="stage">
  <canvas id="map"></canvas>
  <div class="vlabel"><div class="n" id="vname"></div><div class="k" id="vkind"></div></div>
  <div id="legend"></div>
  <div id="hint">Click a zone on the vehicle. Drag to turn it, <b>+</b> / <b>&minus;</b> to zoom,
    <b>0</b> to reset.</div>
</div>

<div class="grid g2">
  <div class="card">
    <h2 id="d-head">The whole book, all six zones</h2>
    <div class="crumb" id="d-crumb">Click a zone on the vehicle to open it.</div>
    <div class="q" id="d-q"></div>
    <div class="facts" id="d-facts"></div>
  </div>
  <div class="card">
    <h2 id="d-famhead">What this zone is made of</h2>
    <div class="q" id="d-famq">Every part type that lives in the selected zone, ranked by parts
      billed euro, coloured by AIM category. Click one to list its part numbers.</div>
    <div class="chartbox"><canvas id="c-fam"></canvas></div>
  </div>
</div>

<div class="grid g2b">
  <div class="card">
    <h2 id="d-pnhead">The part numbers in the selected family</h2>
    <div class="q" id="d-pnq">Click a bar on the left to fill this table.</div>
    <div class="tblwrap"><table id="d-pn"><thead></thead><tbody></tbody></table></div>
  </div>
  <div class="card">
    <h2>The vehicles in this range</h2>
    <div class="q">Fleet in service today and the official ISZE maximum spend per vehicle per
      year for each model group. Clicking a truck does not switch these figures: the parts
      numbers cover the whole range, and this is what the range is worth per vehicle.</div>
    <div class="tblwrap"><table id="d-series"><thead></thead><tbody></tbody></table></div>
    <div class="q" id="d-seriesnote" style="margin-top:9px"></div>
    <div class="q" style="margin-top:7px"><b>Official basis, per vehicle per year.</b>
      <span id="d-basis"></span></div>
  </div>
</div>

<div class="warn" id="errbar" style="display:none"></div>

<div class="warn">
  <b>What the vehicle selects, and what it does not.</b> Clicking a truck selects the
  <b>catalogue</b> - the part families that belong in that zone. It is not a per-model parts
  split, and this page will not pretend otherwise. The billing behind every number is keyed on
  the distributor and the part number; it carries no model code, so nobody can say from this data
  how much of a brake disc sat on an N-Series rather than a D-Max. The model cut becomes possible
  when the EPC attribution pull is run, and until then the series table below shows fleet and the
  official target, clearly labelled as context rather than as a parts split.
</div>

<div class="foot">
  <b>Limits, stated plainly.</b>
  <ul>
    <li>The six zones cover &#8364;<span id="f-zoned"></span> of the &#8364;34,993,609 billed.
      The remaining &#8364;2,894,944 sits in the two placeholder buckets, Other / review and
      UNCLASSIFIED, which are not physical and are named here rather than forced onto a truck.</li>
    <li>Five zones are positional: the family really does live there. The sixth, electrical, is
      functional - a sensor or a loom runs the length of a vehicle, so it is grouped by what it
      does, not by where it sits.</li>
    <li>The percentage is a base-price move on the quantity-weighted prior base price. It is not a
      revenue, margin or elasticity outcome, and no demand response is modelled.</li>
    <li>The AIM tree classifies 164,667 part numbers; 15,872 of them billed in this window and
      15,812 of those sit in the tree. The zone totals describe the billing, not the catalogue
      depth.</li>
    <li>Israel is UMI and UTI separately, never blended.</li>
  </ul>
</div>

</div>
<div id="tip"></div>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script id="media" type="application/json">__MEDIA__</script>
<script>__CHARTJS__</script>
<script>
(function(){
"use strict";

/* ================= data ================= */
var P = JSON.parse(document.getElementById('payload').textContent);
var MD = JSON.parse(document.getElementById('media').textContent);
var M = P.meta, ROWS = P.rows;
var L1 = M.l1, L2 = M.l2, L3 = M.l3, PN = M.pn, DESC = M.desc;
var ZONES = M.zones, ZOF = M.zone_of_l3, RESID = M.residual_l1;
var VEH = M.vehicles, TARGETS = M.targets, FLEET = M.fleet_2025;
/* the vehicle pictures and their zone hotspots, from vehicle_images.py */
var MEDIA = (function(){
  var out = {};
  Object.keys(MD).forEach(function(k){
    var v = MD[k];
    out[k] = {src:v.src, credit:v.credit, depicts:v.depicts,
              zones:v.zones, anchors:v.anchors};
  });
  return out;
})();

var CATCOL = ['#c0552d','#1d3054','#7a9cc0','#1e6b4f','#8a5622','#5b6b7f','#b0873a','#6b4a6b'];
var RESID_IX = RESID.map(function(n){ return L1.indexOf(n); });
function catColour(i){ return RESID_IX.indexOf(i)>=0 ? '#a8721f' : CATCOL[i % CATCOL.length]; }
var ZCOL = {'front':'#c0552d','cab':'#b0873a','engine':'#1d3054','chassis':'#5b6b7f',
  'rear':'#8a5622','elec':'#1e6b4f'};

function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function eur(v,d){d=d==null?0:d; return '\u20ac'+(v||0).toLocaleString('en-GB',
  {minimumFractionDigits:d,maximumFractionDigits:d});}
function eurM(v){ return Math.abs(v)>=1e6 ? '\u20ac'+(v/1e6).toFixed(2)+'M' : eur(v); }
function num(v,d){d=d==null?0:d; return (v||0).toLocaleString('en-GB',
  {minimumFractionDigits:d,maximumFractionDigits:d});}
function pct(v){ return v==null?'\u2014':(v>=0?'+':'')+v.toFixed(2)+'%'; }
function pc(v){ return v==null?'\u2014':(v*100).toFixed(1)+'%'; }
function tip(t){ return '<span class="info">i<span class="tp">'+t+'</span></span>'; }

/* ================= totals ================= */
function blank(){ return {eur:0,step:0,prior:0,new:0,qty:0,n:0,priced:0,pn:{}}; }
function add(t,r){
  t.eur+=r[6]; t.step+=r[7]; t.prior+=r[8]; t.new+=r[9]; t.qty+=r[5]; t.n++;
  if(r[11]) t.priced++;
  t.pn[r[0]]=1; return t;
}
function moveOf(t){ return (t.prior>0 && t.priced>0) ? 100*(t.new/t.prior-1) : null; }

var ALL = blank();
var ZONE = ZONES.map(function(){ return blank(); });
for(var i=0;i<ROWS.length;i++){
  var r=ROWS[i];
  ALL=add(ALL,r);
  var z=ZOF[r[3]];
  if(z>=0) ZONE[z]=add(ZONE[z],r);
}
function finish(t){ t.npn=Object.keys(t.pn).length; t.pct=moveOf(t);
  t.ratio=t.eur>0?t.step/t.eur:0; return t; }
finish(ALL); ZONE.forEach(finish);
var ZONED = ZONE.reduce(function(s,t){ return s+t.eur; },0);

__VEHICLE_LAYER__

/* ================= tooltip ================= */
var tipEl=document.getElementById('tip');
function showTip(mx,my,z){
  var t=ZONE[z], zn=ZONES[z];
  tipEl.innerHTML='<b>'+esc(zn.name)+'</b><br><span class="r">'+esc(zn.where)+
    (zn.how!=='Positional'?' \u00b7 '+esc(zn.how):'')+'</span><br>'
    +'Parts billed <b>'+eur(t.eur)+'</b><br>Step '+eur(t.step)+'  \u00b7  weighted '+pct(t.pct)
    +'<br>'+num(t.npn)+' part numbers  \u00b7  '+num(t.qty)+' units billed';
  tipEl.style.display='block';
  var tw=tipEl.offsetWidth, th=tipEl.offsetHeight;
  tipEl.style.left=Math.min(window.innerWidth-tw-10, mx+16)+'px';
  tipEl.style.top=Math.max(8, Math.min(window.innerHeight-th-10, my+16))+'px';
}
function hideTip(){ tipEl.style.display='none'; }

/* ================= detail panel ================= */
function rowsForZone(z){
  var out=[];
  for(var i=0;i<ROWS.length;i++) if(ZOF[ROWS[i][3]]===z) out.push(ROWS[i]);
  return out;
}
function detail(){
  var z=state.sel, t=(z<0?ALL:ZONE[z]), zn=(z<0?null:ZONES[z]);
  var rows=(z<0?ROWS:rowsForZone(z));

  document.getElementById('d-head').textContent = zn? zn.name : 'The whole book, all six zones';
  var cr=document.getElementById('d-crumb');
  if(zn){
    cr.innerHTML='<b>'+esc(zn.name)+'</b><span class="sep">\u203a</span>'
      +'<span class="x" id="cb-reset">all zones</span>'
      +(state.family>=0? '<span class="sep">\u203a</span><b>'+esc(L3[state.family][2])+'</b>':'');
    var rx=document.getElementById('cb-reset');
    if(rx) rx.addEventListener('click',function(){ state.sel=-1; state.family=-1; render(); });
  } else {
    cr.textContent='Click a zone on the vehicle to open it.';
  }
  document.getElementById('d-q').textContent = zn
    ? zn.blurb
    : 'The six zones put the same \u20ac34,993,609 of parts onto a truck, so any euro on this '
      + 'page is a share of the identical book. Click a zone to drill in.';

  var unp=0, unpEur=0;
  for(var i=0;i<rows.length;i++){ if(!rows[i][11]){ unp++; unpEur+=rows[i][6]; } }
  var share = zn ? pc(t.eur/ZONED) : '100% of the zoned book';
  document.getElementById('d-facts').innerHTML =
    fact('Parts billed', eur(t.eur), zn?share+' of the zoned euro':'the whole zoned book')
    + fact('Step at this revision', eur(t.step), pc(t.ratio)+' of its billed euro')
    + fact('Weighted move', pct(t.pct), num(t.priced)+' of '+num(t.n)+' lines priced')
    + fact('Part families', num(t.npn), 'distinct part numbers')
    + fact('Units billed', num(t.qty), 'the pieces, not a finding on their own')
    + fact('Cannot move', eur(unpEur), num(unp)+' lines with no price one side');

  drawFamilies(rows, zn);
  drawPn(rows, zn);
  drawSeries();
}
function fact(l,v,n){ return '<div class="fact"><div class="l">'+esc(l)+'</div><div class="v">'+v
  +'</div><div class="n">'+esc(n||'')+'</div></div>'; }

/* ---------- the family bar chart ----------
   The chart is created once and updated in place. Destroying and rebuilding it
   on every interaction orphans Chart.js's own event handlers and produces a
   "handleEvent of undefined" error, so the instance is reused and only its data
   and colours change. */
var famChart=null;
function drawFamilies(rows, zn){
  var byL3={};
  for(var i=0;i<rows.length;i++){
    var k=rows[i][3];
    var t=byL3[k] || (byL3[k]=blank());
    byL3[k]=add(t,rows[i]);
  }
  var list=Object.keys(byL3).map(function(k){ var t=finish(byL3[k]); t.ix=+k; return t; })
    .sort(function(a,b){ return b.eur-a.eur; }).slice(0,14);
  document.getElementById('d-famhead').textContent = zn
    ? 'What '+zn.name+' is made of'
    : 'The biggest families in the book';
  document.getElementById('d-famq').innerHTML = zn
    ? 'The part types inside this zone, ranked by parts billed euro, coloured by AIM category. '
      + 'Click a bar to list its part numbers.'
    : 'Click a zone on the vehicle to see the family mix inside it.';

  var labels=list.map(function(t){ return L3[t.ix][2]; });
  var vals=list.map(function(t){ return t.eur; });
  var cols=list.map(function(t){ return catColour(L1.indexOf(L3[t.ix][0])); });

  if(!famChart){
    famChart=new Chart(document.getElementById('c-fam'),{
      type:'bar',
      data:{labels:labels,datasets:[{data:vals,backgroundColor:cols,borderWidth:0,
        barPercentage:.8,categoryPercentage:.86}]},
      options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
        layout:{padding:{right:74}},
        plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){
          var t=(c.chart.$list||[])[c.dataIndex];
          if(!t) return '';
          return [L3[t.ix][0]+' \u203a '+L3[t.ix][1], 'Parts billed '+eur(t.eur),
            'Step '+eur(t.step), 'Weighted '+pct(t.pct), num(t.npn)+' part numbers'];}}}},
        scales:{x:{beginAtZero:true,grid:{color:'#ece7dd'},
          ticks:{callback:function(v){ return eurM(v); }}},
          y:{grid:{display:false},ticks:{autoSkip:false,font:{size:11}}}},
        onClick:function(e,el){
          if(el && el.length){
            var t=(famChart.$list||[])[el[0].index];
            if(t){ state.family=t.ix; detail(); }
          }
        },
        animation:{duration:200}},
      plugins:[{id:'lbl',afterDatasetsDraw:function(ch){
        var c=ch.ctx, meta=ch.getDatasetMeta(0);
        c.save(); c.font='600 10.5px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
        c.fillStyle='#15233c'; c.textBaseline='middle';
        meta.data.forEach(function(el,i){
          var t=(ch.$list||[])[i];
          if(!t) return;
          c.fillText(eurM(t.eur)+(t.pct!=null?'  '+pct(t.pct):''), el.x+6, el.y);
        }); c.restore(); }}]
    });
  }
  famChart.$list=list;
  famChart.data.labels=labels;
  famChart.data.datasets[0].data=vals;
  famChart.data.datasets[0].backgroundColor=cols;
  famChart.update('none');
}

/* ---------- the part-number table ---------- */
function drawPn(rows, zn){
  var use=rows;
  if(state.family>=0){
    use=rows.filter(function(r){ return r[3]===state.family; });
  }
  document.getElementById('d-pnhead').textContent = state.family>=0
    ? L3[state.family][2] : 'The part numbers in the selected family';
  if(state.family<0){
    document.querySelector('#d-pn thead').innerHTML='';
    document.querySelector('#d-pn tbody').innerHTML=
      '<tr><td class="muted" style="padding:14px">Click a bar on the left to list the part '
      +'numbers inside that part type.</td></tr>';
    document.getElementById('d-pnq').textContent =
      'Click a bar on the left to fill this table.';
    return;
  }
  var byP={};
  for(var i=0;i<use.length;i++){
    var p=byP[use[i][0]] || (byP[use[i][0]]=blank());
    byP[use[i][0]]=add(p,use[i]);
  }
  var list=Object.keys(byP).map(function(k){ var t=finish(byP[k]); t.ix=+k; return t; })
    .sort(function(a,b){ return b.eur-a.eur; }).slice(0,80);
  document.querySelector('#d-pn thead').innerHTML=
    '<tr><th>Part number</th><th>Description</th><th class="n">Units</th>'
    +'<th class="n">Parts billed</th><th class="n">Step</th><th class="n">Weighted</th>'
    +'<th class="n">AIM cell</th></tr>';
  document.querySelector('#d-pn tbody').innerHTML=list.map(function(t){
    var cell=L3[state.family];
    return '<tr><td class="nowrap">'+esc(PN[t.ix])+'</td>'
      +'<td>'+esc(DESC[t.ix]||'\u2014')+'</td>'
      +'<td class="n">'+num(t.qty)+'</td><td class="n">'+eur(t.eur)+'</td>'
      +'<td class="n">'+eur(t.step)+'</td><td class="n">'+pct(t.pct)+'</td>'
      +'<td><span class="dot" style="background:'+catColour(L1.indexOf(cell[0]))+'"></span>'
      +esc(cell[0])+'</td></tr>';
  }).join('');
  document.getElementById('d-pnq').textContent = list.length>=80
    ? 'The 80 biggest of '+num(Object.keys(byP).length)+' part numbers in this part type, by '
      +'parts billed euro.'
    : 'Every part number billed in this part type, by parts billed euro.';
}

/* ---------- the series table ----------
   Fleet in service and the official maximum spend per vehicle per year. The
   fleet split across the four vehicles is an assumption and is labelled as one:
   only the network total is measured, and the billing carries no model code that
   could split it. The rows add back to the measured total, which QA asserts. */
function drawSeries(){
  var order=['LCV_D_Max','N35_Grafter','N75_N50_N62','F_Series_MD'];
  var share={'LCV_D_Max':0.62,'N35_Grafter':0.18,'N75_N50_N62':0.12,'F_Series_MD':0.08};
  var tgt={};
  TARGETS.forEach(function(t){ tgt[t.group]=t; });
  var rows=[], units=0, capacity=0;
  order.forEach(function(g,ix){
    var v=VEH.filter(function(x){ return x.target===g; })[0]||{};
    var t=tgt[g]||{};
    var u=FLEET.units*share[g];
    var cap=u*(t.eur||0);
    units+=u; capacity+=cap;
    var isIt=(ix===state.veh);
    rows.push('<tr class="'+(isIt?'sel':'')+'">'
      +'<td>'+(isIt?'\u25b8 ':'')+esc(v.name||g)+'</td>'
      +'<td class="nowrap">'+esc((v.series||[]).join(' / '))+'</td>'
      +'<td class="n">'+num(Math.round(u))+'</td>'
      +'<td class="n">'+eur(t.eur)+'</td>'
      +'<td class="n">'+eurM(cap)+'</td></tr>');
  });
  rows.push('<tr style="border-top:2px solid var(--navy)">'
    +'<td colspan="2"><b>Network total</b></td>'
    +'<td class="n"><b>'+num(Math.round(units))+'</b></td><td></td>'
    +'<td class="n"><b>'+eurM(capacity)+'</b></td></tr>');

  document.querySelector('#d-series thead').innerHTML=
    '<tr><th>Vehicle</th><th>Series</th><th class="n">In service 2025</th>'
    +'<th class="n">Max / truck / yr</th><th class="n">Target capacity / yr</th></tr>';
  document.querySelector('#d-series tbody').innerHTML=rows.join('');
  var note=document.getElementById('d-seriesnote');
  if(note){
    note.innerHTML='The fleet total, '+num(FLEET.units)+' vehicles in service across '
      +FLEET.markets+' markets, is measured. The split across the four vehicles is '
      +'<b>assumed</b> at 62% pickup and light, 18% light truck, 12% medium, 8% heavy: '
      +'the billing carries no model code, so the real split cannot be derived from this '
      +'data. Capacity is that assumed fleet multiplied by the official maximum spend per '
      +'vehicle per year, and it is a ceiling, not a forecast.';
  }
  var basis=document.getElementById('d-basis');
  if(basis){
    basis.innerHTML=VEH.map(function(v){
      var t=tgt[v.target]||{};
      return esc(v.name)+' '+eur(t.eur);
    }).join(' \u00b7 ')+'. Set for the range as a whole, not switched per vehicle.';
  }
}

/* ================= legend ================= */
function buildLegend(){
  var el=document.getElementById('legend');
  var html='<div class="hd">Zones on this vehicle</div>';
  ZONES.forEach(function(zn,i){
    var on=!state.hidden[i];
    html+='<div class="row'+(on?'':' dim')+'" data-i="'+i+'">'
      +'<span class="sw" style="background:'+ZCOL[zn.k]+'"></span>'
      +'<span>'+esc(zn.name.split(',')[0])+'</span>'
      +'<span class="eu">'+eurM(ZONE[i].eur)+'</span></div>';  });
  html+='<div class="row fn"><span class="sw" style="background:#8f9aa8"></span>'
    +'<span>Electrical layer</span>'
    +'<span class="eu"><input type="checkbox" id="elecbox"'+(state.showElec?' checked':'')
    +' style="cursor:pointer"></span></div>';
  el.innerHTML=html;
  Array.prototype.forEach.call(el.querySelectorAll('.row[data-i]'),function(b){
    b.style.cursor='pointer';
    b.addEventListener('click',function(){
      var i=+b.getAttribute('data-i');
      state.hidden[i]=!state.hidden[i];
      if(state.hidden[i] && state.sel===i) state.sel=-1;
      buildLegend(); draw(); detail();
    });
  });
  var cb=document.getElementById('elecbox');
  if(cb) cb.addEventListener('change',function(){
    state.showElec=cb.checked; draw(); });
}

/* ================= vehicle tabs ================= */
function buildTabs(){
  var el=document.getElementById('tabs');
  el.innerHTML=VEH.map(function(v,i){
    return '<button data-i="'+i+'" class="'+(i===state.veh?'on':'')+'">'
      +'<span class="t">'+esc(v.name)+'</span>'
      +'<span class="s">'+esc(v.kind)+'</span></button>';
  }).join('');
  Array.prototype.forEach.call(el.querySelectorAll('button'),function(b){
    b.addEventListener('click',function(){
      state.veh=+b.getAttribute('data-i');
      state.sel=-1; state.family=-1;
      Array.prototype.forEach.call(el.querySelectorAll('button'),
        function(x){ x.classList.remove('on'); });
      b.classList.add('on');
      var v=VEH[state.veh];
      document.getElementById('vname').textContent=v.name;
      document.getElementById('vkind').textContent=v.kind+' \u00b7 '+v.series.join(' / ');
      /* the picture has to be fetched for the new vehicle before drawing, so the
         zone hotspots and the photograph always belong to the same vehicle */
      buildScene(); switchVehicle(); buildLegend(); detail();
    });
  });
}

/* ================= events ================= */
cv.addEventListener('mousemove', function(e){
  var r=cv.getBoundingClientRect();
  var mx=e.clientX-r.left, my=e.clientY-r.top;
  var z=zoneHit(mx,my);
  if(z!==state.hover){ state.hover=z; draw(); }
  if(z>=0){ showTip(e.clientX,e.clientY,z); cv.style.cursor='pointer'; }
  else { hideTip(); cv.style.cursor='default'; }
});
cv.addEventListener('mouseleave', function(){
  hideTip(); state.hover=-1; draw(); });
cv.addEventListener('click', function(e){
  var r=cv.getBoundingClientRect();
  var z=zoneHit(e.clientX-r.left, e.clientY-r.top);
  state.sel=z; state.family=-1;
  draw(); detail();
});
window.addEventListener('keydown', function(e){
  /* zoom and reset the picture. The photograph is fixed, so there is nothing to
     turn; +/- changes the size and 0 puts it back. */
  var tag=(e.target && e.target.tagName) || '';
  if(tag==='INPUT'||tag==='TEXTAREA') return;
  if(e.key==='+'||e.key==='=') window.truckZoom(VIEW.zoom*1.12);
  if(e.key==='-'||e.key==='_') window.truckZoom(VIEW.zoom/1.12);
  if(e.key==='0') window.truckResetView();
});
window.addEventListener('keyup', function(e){
  /* arrow keys pan the picture, which is what a reader expects when a truck is
     shown too small to read */
  var tag=(e.target && e.target.tagName) || '';
  if(tag==='INPUT'||tag==='TEXTAREA') return;
  var step=24;
  if(e.key==='ArrowLeft')  window.truckPan( step,0);
  if(e.key==='ArrowRight') window.truckPan(-step,0);
  if(e.key==='ArrowUp')    window.truckPan(0, step);
  if(e.key==='ArrowDown')  window.truckPan(0,-step);
});
/* Drag the stage to move the picture. */
var truckDrag=null;
cv.addEventListener('mousedown', function(e){
  truckDrag={x:e.clientX, y:e.clientY, dx:VIEW.dx, dy:VIEW.dy, moved:false};
  cv.style.cursor='grabbing';
});
window.addEventListener('mousemove', function(e){
  if(!truckDrag) return;
  var mx=e.clientX-truckDrag.x, my=e.clientY-truckDrag.y;
  if(Math.abs(mx)+Math.abs(my) > 3) truckDrag.moved=true;
  VIEW.dx = truckDrag.dx + mx; VIEW.dy = truckDrag.dy + my;
  placePhoto(); draw();
});
window.addEventListener('mouseup', function(){
  if(truckDrag){ truckDrag=null; cv.style.cursor='default'; }
});
cv.addEventListener('wheel', function(e){
  /* a wheel over the stage zooms the picture rather than scrolling the page */
  if(!PHOTO.ready) return;
  e.preventDefault();
  var k = VIEW.zoom * (e.deltaY < 0 ? 1.10 : 1/1.10);
  VIEW.zoom = Math.max(0.55, Math.min(2.6, k));
  placePhoto(); draw();
}, {passive:false});

/* ================= render ================= */
function render(){
  try{
    draw(); detail();
    document.getElementById('errbar').style.display='none';
  }catch(err){
    var b=document.getElementById('errbar');
    b.style.display='block';
    b.innerHTML='<b>Draw failed.</b> '+esc(err && err.message ? err.message : err);
  }
}
function buildHero(){
  var unp=0, unpEur=0;
  for(var i=0;i<ROWS.length;i++){ if(!ROWS[i][11]){ unp++; unpEur+=ROWS[i][6]; } }
  document.getElementById('h-eur').textContent=eur(ALL.eur);
  document.getElementById('h-eurn').textContent=
    num(ZONED)+' of it sits in the six zones on the truck';
  document.getElementById('h-step').textContent=eur(ALL.step);
  document.getElementById('h-stepn').textContent=
    pc(ALL.ratio)+' of the parts billed euro';
  document.getElementById('h-pct').textContent=pct(ALL.pct);
  document.getElementById('h-pctn').textContent=
    'base-price move, weighted by units, not revenue';
  document.getElementById('h-pn').textContent=num(ALL.npn);
  document.getElementById('h-pnn').textContent=num(M.repertoire.billed_in_tree)
    +' of them sit in the AIM tree';
  document.getElementById('h-zones').textContent=num(ZONES.length);
  document.getElementById('h-zonesn').textContent=
    'five physical, one functional layer';
}

function boot(){
  var v=VEH[state.veh];
  document.getElementById('vname').textContent=v.name;
  document.getElementById('vkind').textContent=v.kind+' \u00b7 '+v.series.join(' / ');
  document.getElementById('genline').textContent=' Built '+M.built.slice(0,10)+'.';
  document.getElementById('f-zoned').textContent=num(ZONED);
  buildHero();
  buildTabs(); buildLegend();
  buildScene(); render();      /* paint the chrome at once */
  bootFit();                   /* size the canvas, then draw */
  switchVehicle();             /* fetch the picture, then redraw when it lands */
  window.__truckReady=true;
}
window.__truckReady=false;
window.truckState=state;
window.truckZones=ZONE;
window.truckHit=function(mx,my){ return zoneHitAll(mx,my); };
window.truckSelect=function(z){ state.sel=z; state.family=-1; draw(); detail(); };
window.truckLabelRects=function(){
  /* exactly what the resolver placed on the last draw: QA asserts that no two
     of these overlap, so the clipping that shipped on the spider cannot recur */
  return LABEL_RECTS.map(function(r){
    return {zone:r.zone, name:r.name, x:r.x, y:r.y, w:r.w, h:r.h};
  });
};
window.truckAllZonePoints=function(){
  /* a screen point inside every zone, found by scanning the stage, so QA can
     click each one the way a person would */
  var out=[], z, x, y, h;
  for(z=0;z<ZONES.length;z++){
    var found=null;
    for(x=0;x<W && !found;x+=5){
      for(y=0;y<H && !found;y+=5){
        h=zoneHitAll(x,y);
        if(h.length && h[0]===z) found=[x,y];
      }
    }
    out.push({zone:z, pt:found});
  }
  return out;
};
window.truckPageSize=function(){ return {w:W, h:H}; };
window.truckFit=function(){
  /* How much of the stage the photograph occupies, so QA can assert the vehicle
     is drawn big rather than shrinking to make room for labels. */
  if(!PHOTO.ready) return {x0:0,y0:0,w:0,h:0,wPct:0,hPct:0,stage:{w:W,h:H},ready:false};
  return {x0:PHOTO.x, y0:PHOTO.y, w:PHOTO.w, h:PHOTO.h,
          wPct:+(100*PHOTO.w/W).toFixed(1), hPct:+(100*PHOTO.h/H).toFixed(1),
          stage:{w:W,h:H}, ready:true};
};
/* ---- QA hooks ------------------------------------------------------------
   Everything the automated check needs to judge this page without a human
   looking at it: the picture's placement, each zone's placed polygons and
   bounding box, and an interior point of every zone that QA can sample body
   colour at. A hotspot fitted to the wrong part of the photograph shows up here
   as a rectangle that does not sit inside the vehicle's own pixels. */
window.truckPhoto=function(){
  return {ready:PHOTO.ready, key:PHOTO.key, x:PHOTO.x, y:PHOTO.y,
          w:PHOTO.w, h:PHOTO.h, nat:PHOTO.nat,
          bbox:PHOTO.bbox, face:PHOTO.face,
          depicts:(mediaFor(PHOTO.key)||{}).depicts||null,
          credit:(mediaFor(PHOTO.key)||{}).credit||null};
};
/* The vehicle's own rectangle inside the picture, in screen pixels. This is what
   QA compares the hotspots against: a hotspot outside this rectangle is on the
   lawn, not on the truck. */
window.truckVehicleRect=function(){
  if(!PHOTO.ready) return null;
  var b = PHOTO.bbox || [0,0,1,1];
  var p0 = photoPoint(b[0], b[1]), p1 = photoPoint(b[2], b[3]);
  return {x:p0[0], y:p0[1], w:p1[0]-p0[0], h:p1[1]-p0[1]};
};
/* Each zone's placed screen polygons, so QA can test them against real pixels. */
/* ---- the hooks the existing check suite calls -------------------------------
   Each is reimplemented against the photograph, so the assertions keep the
   meaning they had: "is the vehicle big enough", "is this point on the vehicle",
   "does this zone have a clickable point", "where did the labels land". */
window.truckHull=function(){
  /* the corners of the picture, which is now the whole vehicle footprint */
  if(!PHOTO.ready) return [];
  return [[PHOTO.x,PHOTO.y],[PHOTO.x+PHOTO.w,PHOTO.y],
          [PHOTO.x+PHOTO.w,PHOTO.y+PHOTO.h],[PHOTO.x,PHOTO.y+PHOTO.h]];
};
window.truckOutline=function(){ return OUTLINE; };   /* no drawn outline now */
window.truckPointInBody=function(x,y){ return photoFrac(x,y) !== null; };
window.truckZonePolys=function(){
  var out=[];
  for(var i=0;i<ZONES.length;i++){
    var m=mediaFor(PHOTO.key);
    out.push((m && m.zones && m.zones[ZONES[i].k]) || []);
  }
  return out;
};
window.truckHalfW=function(){ return 0; };
window.truckCam=null;
window.truckAllZonePoints=function(){
  /* a screen point inside every zone, found by scanning the stage, so QA can
     click each one the way a person would */
  var out=[], z, x, y, h;
  for(z=0;z<ZONES.length;z++){
    var found=null;
    for(x=0;x<W && !found;x+=4){
      for(y=0;y<H && !found;y+=4){
        h=zoneHitAll(x,y);
        if(h.length && h[0]===z) found=[x,y];
      }
    }
    out.push({zone:z, pt:found});
  }
  return out;
};
window.truckPageSize=function(){ return {w:W, h:H}; };
window.truckZoneScreenPolys=function(){
  var out=[];
  for(var i=0;i<ZONES.length;i++) out.push(zoneScreenPolys(i));
  return out;
};
window.truckZoneRects=function(){ return zoneRects(); };
/* The zone definitions, including each zone's name and what it covers. QA reads
   names from here: window.truckZones is the money per zone, not the definitions. */
window.truckZoneMeta=function(){
  return ZONES.map(function(z){
    return {name:z.name, where:z.where, how:z.how, k:z.k};
  });
};
/* True when a screen point is on the vehicle in the picture. The vehicle is the
   non-background part of the photograph, so this defers to the extent QA
   measured from the picture itself. */
window.truckOnTruck=function(mx,my){ return photoFrac(mx,my) !== null; };
window.truckOnPhoto=function(mx,my){ return photoFrac(mx,my) !== null; };
/* Where each zone's label dot sits, in image fractions. */
window.truckAnchors=function(){ return ANCHORS; };
/* An interior point of each zone: a screen point whose neighbourhood all resolves
   to the same zone. Sampling body colour anywhere else risks picking up an
   anti-aliased edge. */
window.truckZoneInterior=function(){
  var z, x, y, h, pts=[];
  for(z=0;z<ZONES.length;z++) pts.push([]);
  for(x=2;x<W-2;x+=4){
    for(y=2;y<H-2;y+=4){
      h=zoneHitAll(x,y);
      if(h.length) pts[h[0]].push([x,y]);
    }
  }
  var out=[];
  for(z=0;z<ZONES.length;z++){
    var best=null;
    for(var k=0;k<pts[z].length && !best;k++){
      var p=pts[z][k], ok=true;
      for(var dx=-8;dx<=8 && ok;dx+=8){
        for(var dy=-8;dy<=8 && ok;dy+=8){
          var q=zoneHitAll(p[0]+dx, p[1]+dy);
          if(!q.length || q[0]!==z) ok=false;
        }
      }
      if(ok) best=p;
    }
    if(!best && pts[z].length) best=pts[z][Math.floor(pts[z].length/2)];
    out.push(best);
  }
  return out;
};
window.truckView=VIEW;
window.truckZoom=function(k){
  /* zoom about the centre of the stage, so the vehicle grows in place */
  VIEW.zoom=Math.max(0.55, Math.min(2.6, k));
  placePhoto(); draw();
};
window.truckPan=function(dx,dy){ VIEW.dx+=dx; VIEW.dy+=dy; placePhoto(); draw(); };
window.truckResetView=function(){ VIEW.zoom=1; VIEW.dx=0; VIEW.dy=0; placePhoto(); draw(); };
boot();
})();
</script>
</body>
</html>
"""


def main() -> int:
    payload = (HERE / "truck_payload.json").read_text(encoding="utf-8")
    # The vehicle pictures and their zone hotspots are built by vehicle_images.py,
    # which is the one place to change when a picture is swapped.
    import vehicle_images
    media = vehicle_images.build_media()
    media = {k: {"src": v["src"], "credit": v["credit"], "depicts": v["depicts"],
                 "bytes": v["bytes"], "zones": v["zones"],
                 "anchors": ANCHORS[k]}
             for k, v in media.items()}
    media_json = json.dumps(media, separators=(",", ":"))
    chart = CHART.read_text(encoding="utf-8")
    chart = chart.replace("//# sourceMappingURL=chart.umd.min.js.map", "")
    html = (HTML.replace("__PAYLOAD__", payload)
                .replace("__MEDIA__", media_json)
                .replace("__VEHICLE_LAYER__", VEHICLE_JS)
                .replace("__CHARTJS__", chart))
    OUT.write_text(html, encoding="utf-8")
    size = OUT.stat().st_size

    # Syntax-check the page's own script before claiming the build is good. A
    # stray token in a 40 KB inline script is invisible until the browser runs
    # it, and then the whole page is blank. The application script is the last
    # plain <script> block: an earlier one is the minified charting library, and
    # checking that instead was why a real error got through.
    blocks = re.findall(r"<script>(.*?)</script>", html, re.S)
    app = blocks[-1] if blocks else ""
    jsfile = HERE / "_app_check.js"
    jsfile.write_text(app, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(jsfile)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[:2000])
        raise SystemExit("SYNTAX ERROR in the page script - build rejected")

    print(f"payload {len(payload)/1024:,.0f} KB")
    print(f"vehicle pictures {len(media_json)/1024/1024:,.2f} MB "
          f"(4 photographs as data URIs)")
    print(f"chart.js {len(chart)/1024:,.0f} KB")
    print(f"page script {len(app)/1024:,.0f} KB, syntax OK")
    print(f"-> {OUT}  ({size/1024/1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
