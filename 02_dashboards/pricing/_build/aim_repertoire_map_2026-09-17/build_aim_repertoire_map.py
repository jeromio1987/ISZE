#!/usr/bin/env python3
"""Build ISZE_AIM_Repertoire_Map_2026-09-17.html - the AIM drill page.

One self-contained file: the payload and Chart.js are both inlined, so it opens
from Explorer with no server, no CDN and no internet.

Reads
  02_dashboards/pricing/_build/aim_repertoire_map_2026-09-17/payload.json
  02_dashboards/_ui/chart.umd.min.js

Writes
  02_dashboards/pricing/ISZE_AIM_Repertoire_Map_2026-09-17.html

Nothing under 01_data/00_derived/ is written by this script.
"""
from __future__ import annotations

from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BUILD = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_repertoire_map_2026-09-17"
CHART = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Repertoire_Map_2026-09-17.html"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AIM repertoire map - what the price revision moves, family by family</title>
<style>
:root{
  --navy:#15233c; --navy2:#1d3054; --terra:#c0552d; --paper:#f7f4ee;
  --ink:#22262e; --muted:#6b6459; --line:#d9d3c8; --band:#eef3f9;
  --good:#1e6b4f; --amber:#a8721f; --amberbg:#fdf3e3;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:14px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
h1{font-size:25px;letter-spacing:-.2px}
h2{font-size:18px;margin-bottom:2px}
h3{font-size:14px}
.wrap{max-width:1420px;margin:0 auto;padding:22px 22px 60px}
header.top{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:16px}
.sub{color:var(--muted);font-size:13px;margin-top:6px}
.badge{display:inline-block;background:var(--navy);color:var(--paper);
  font-size:11px;letter-spacing:.6px;text-transform:uppercase;
  padding:3px 9px;border-radius:2px;margin-right:8px}
.badge.t{background:var(--terra)}

.controls{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-end;
  background:#fff;border:1px solid var(--line);border-left:4px solid var(--terra);
  padding:13px 16px;margin-bottom:16px}
.ctrl{display:flex;flex-direction:column;gap:5px}
.ctrl.grow{flex:1 1 260px}
.ctrl label{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted)}
select,input[type=search]{font-size:14px;padding:7px 10px;border:1px solid var(--line);
  background:#fff;color:var(--ink);border-radius:2px;min-width:190px;font-family:inherit}
input[type=search]{width:100%;min-width:0}
select:focus,input:focus{outline:2px solid var(--terra);outline-offset:-1px}
.seg{display:flex;border:1px solid var(--line);border-radius:2px;overflow:hidden}
.seg button{background:#fff;border:0;border-right:1px solid var(--line);
  padding:7px 13px;font-size:13px;cursor:pointer;color:var(--ink);font-family:inherit}
.seg button:last-child{border-right:0}
.seg button.on{background:var(--navy);color:var(--paper)}
.reset{background:#fff;border:1px solid var(--line);padding:7px 13px;font-size:13px;
  cursor:pointer;color:var(--terra);border-radius:2px;font-family:inherit}
.reset:hover{border-color:var(--terra)}
#hits{position:relative}
#hitlist{position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid var(--line);
  border-top:0;max-height:330px;overflow:auto;z-index:70;display:none;
  box-shadow:0 8px 20px rgba(0,0,0,.12)}
#hitlist div{padding:7px 11px;cursor:pointer;font-size:13px;border-bottom:1px solid #f0ece4}
#hitlist div:hover{background:var(--band)}
#hitlist .k{color:var(--muted);font-size:11.5px;display:block}
#hitlist .cd{color:var(--terra)}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(172px,1fr));
  gap:12px;margin-bottom:16px}
.kpi{background:#fff;border:1px solid var(--line);padding:12px 14px;
  border-top:3px solid var(--navy)}
.kpi .lab{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);
  display:flex;align-items:center;gap:5px}
.kpi .val{font-size:23px;font-weight:600;color:var(--navy);margin-top:5px;
  font-variant-numeric:tabular-nums}
.kpi .note{font-size:11.5px;color:var(--muted);margin-top:3px}
.kpi.t{border-top-color:var(--terra)}
.info{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;
  border-radius:50%;background:var(--navy);color:#fff;font-size:9.5px;cursor:help;
  position:relative;flex:0 0 auto;font-family:inherit;letter-spacing:0}
.info .tip{display:none;position:absolute;bottom:22px;left:50%;transform:translateX(-50%);
  width:290px;background:var(--navy);color:var(--paper);font-size:12px;line-height:1.45;
  padding:9px 11px;border-radius:3px;z-index:64;text-transform:none;letter-spacing:0;
  font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25)}
.info .tip b{color:#f0b49a}
.info:hover .tip,.info:focus .tip{display:block}

.grid{display:grid;gap:16px;margin-bottom:16px}
.g2{grid-template-columns:1.45fr 1fr;align-items:start}
.g1{grid-template-columns:1fr}
@media(max-width:1080px){.g2{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);padding:15px 16px 13px;min-width:0}
.card .q{font-size:13.5px;color:var(--muted);margin:3px 0 12px}
.chartbox{position:relative;height:352px}
.chartbox.tall{height:420px}
.chartbox.short{height:270px}

table{border-collapse:collapse;width:100%;font-size:13px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;
  font-weight:600;font-size:11.5px;letter-spacing:.4px;text-transform:uppercase;
  position:sticky;top:0;white-space:nowrap}
th.n,td.n{text-align:right;font-variant-numeric:tabular-nums}
td{padding:6px 9px;border-bottom:1px solid var(--line)}
tbody tr:nth-child(even){background:var(--band)}
tbody tr.clickable{cursor:pointer}
tbody tr.clickable:hover{background:#e3ecf6}
tbody tr.sel{background:#f6e3da!important;box-shadow:inset 3px 0 0 var(--terra)}
.tblwrap{max-height:430px;overflow:auto;border:1px solid var(--line)}
.tblwrap.med{max-height:340px}
.tblwrap.short{max-height:240px}
.muted{color:var(--muted)}
.nowrap{white-space:nowrap}

.warn{background:var(--amberbg);border:1px solid #e6cf9f;border-left:4px solid var(--amber);
  padding:11px 14px;font-size:12.5px;color:#5e4a1c;margin-bottom:16px}
.warn b{color:#4a3a12}
.residbar{background:var(--amberbg);border:1px solid #e6cf9f;border-left:4px solid var(--amber);
  padding:11px 14px;margin-bottom:16px;font-size:12.5px;color:#5e4a1c}
.residbar table{font-size:12.5px;margin-top:8px}
.residbar th{background:transparent;color:#8a6b22;border-bottom:1px solid #e6cf9f;
  position:static;padding:4px 8px;text-transform:none;letter-spacing:0;font-size:12px}
.residbar td{border-bottom:1px solid #f0e3c8;padding:4px 8px;color:#5e4a1c}
.residbar tbody tr:nth-child(even){background:transparent}
.residbar tbody tr.clickable{cursor:pointer}
.residbar tbody tr.clickable:hover{background:#f7ead1}

.crumb{font-size:12.5px;color:var(--muted);margin-bottom:9px;display:flex;flex-wrap:wrap;
  gap:6px;align-items:center}
.crumb span.seg{cursor:pointer;color:var(--terra);text-decoration:underline}
.crumb span.seg:hover{color:var(--navy)}
.crumb b{color:var(--navy)}
.crumb .sep{color:#bdb6a8}
.what{background:#eef3f9;border:1px solid #cfddea;border-left:4px solid var(--navy);
  padding:10px 13px;font-size:13px;margin-bottom:16px;color:#22355a}
.what b{color:var(--navy)}
.foot{font-size:12px;color:var(--muted);border-top:1px solid var(--line);
  padding-top:12px;margin-top:24px}
.foot ul{margin:8px 0 0;padding-left:18px}
.foot li{margin-bottom:5px}
.pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:11px;
  border:1px solid var(--line);background:var(--paper);color:var(--muted)}
.pill.up{border-color:#d9b48c;color:#8a5622}
.pill.low{border-color:#9db4cf;color:#2c4b74}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div><span class="badge">AIM repertoire</span><span class="badge t">Internal</span></div>
  <h1 style="margin-top:9px">The AIM repertoire, drilled to the part number</h1>
  <div class="sub">Click a family and you go one level deeper: category, then group, then part
    type, then the individual part numbers inside it. Parts billed 1 July 2025 to 30 June 2026,
    22 distributors, <span id="sub-pn"></span> part numbers. Opens from Explorer with no server
    and no internet — the data and the charts are inside the file.
    <span id="genline"></span></div>
</header>

<div class="warn" id="errbar" style="display:none"></div>

<div class="what" id="what">
  <b>The tree is bigger than the billing, and that is the point.</b> The AIM tree classifies
  <span id="r-tree"></span> part numbers across <span id="r-l1"></span> top-level categories.
  Only <span id="r-billed"></span> of them were billed in this twelve-month window, so
  <span id="r-silent"></span> classified part numbers carry no quantity, no euro and no price
  move. A count of silent parts is not a finding, so this page draws the
  <span id="r-billed2"></span> that actually moved money, and names the gap rather than hiding it.
</div>

<div class="controls">
  <div class="ctrl">
    <label for="db">Distributor</label>
    <select id="db"></select>
  </div>
  <div class="ctrl">
    <label>Rank and size the bars by</label>
    <div class="seg" id="meas">
      <button data-m="eur" class="on">Parts billed &#8364;</button>
      <button data-m="step">Step &#8364;</button>
      <button data-m="pct">Weighted %</button>
    </div>
  </div>
  <div class="ctrl grow">
    <label for="q">Jump to a family, a part type or a part number</label>
    <div id="hits"><input type="search" id="q" placeholder="e.g. oil filter, brakes, 8982705240"
      autocomplete="off"><div id="hitlist"></div></div>
  </div>
  <div class="ctrl">
    <label>&nbsp;</label>
    <button class="reset" id="reset">Back to all categories</button>
  </div>
</div>

<div class="kpis" id="kpis"></div>

<div class="grid g2">
  <div class="card">
    <h2 id="t-main">Where the money is, by category</h2>
    <div class="crumb" id="crumb"></div>
    <div class="q" id="q-main">Click any bar or row to go one level deeper.</div>
    <div class="chartbox tall"><canvas id="c-main"></canvas></div>
  </div>
  <div class="card">
    <h2 id="t-side">What the biggest category is made of</h2>
    <div class="q" id="q-side"></div>
    <div class="chartbox tall"><canvas id="c-side"></canvas></div>
  </div>
</div>

<div class="grid g2">
  <div class="card">
    <h2 id="t-dist">Which distributor carries the selected slice</h2>
    <div class="q" id="q-dist">Ranked by the selected measure, with the truck fleet beside it, so a
      big euro number in a small market is visible as a rate per truck rather than an absolute.</div>
    <div class="tblwrap med"><table id="dist"><thead></thead><tbody></tbody></table></div>
  </div>
  <div class="card">
    <h2 id="t-move">What moved on this slice</h2>
    <div class="q" id="q-move">Step euro against parts billed euro. A slice that is large but barely
      moved is a different conversation from one that moved hard.</div>
    <div class="chartbox short"><canvas id="c-move"></canvas></div>
  </div>
</div>

<div class="grid g1">
  <div class="card">
    <h2 id="t-tbl">Every row of the selected level</h2>
    <div class="q" id="q-tbl">Click a row with a name to go deeper. The right-hand columns are the
      parts billed euro, the step euro and the weighted move on that slice.</div>
    <div class="tblwrap"><table id="tbl"><thead></thead><tbody></tbody></table></div>
  </div>
</div>

<div class="grid g1">
  <div class="card">
    <h2 id="t-pn">The part numbers inside the selected part type</h2>
    <div class="q" id="q-pn">Drill to a part type above and this fills. Quantity, parts billed euro,
      step euro and the price move, per part, for the selected distributor only.</div>
    <div class="tblwrap"><table id="pntbl"><thead></thead><tbody></tbody></table></div>
  </div>
</div>

<div class="residbar" id="resid" style="display:none"></div>

<div class="foot">
  <b>How to read this page, and what it is not.</b>
  <ul>
    <li>The percentage is a base-price move on the quantity-weighted prior base price. It is not
      a revenue, margin or elasticity outcome, and no demand response is modelled.</li>
    <li>Parts billed euro covers every in-scope line. The percentage covers only lines priced on
      both sides, which is stated on each panel.</li>
    <li>A part number with no catalogue node is labelled UNCLASSIFIED, never dropped, so the
      category rows add up to the shipped revision total.</li>
    <li>The commercial score — contested or captive, per part per market — is a separate axis and
      is not built as columns yet, so this page cannot colour a part as contested. It does not
      guess from the Isuzu figure key.</li>
    <li>Israel is UMI and UTI separately, never blended. Germany trades through two sold-to
      accounts, Portugal through two; those stay together here, as in the price enquiry.</li>
    <li>Fleet counts are 2025 vehicles in service. Four markets have no fleet count and are
      marked, not estimated.</li>
  </ul>
</div>

</div>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script>__CHARTJS__</script>
<script>
(function(){
"use strict";
var P = JSON.parse(document.getElementById('payload').textContent);
var M = P.meta, ROWS = P.rows;
var L1 = M.l1, L2 = M.l2, L3 = M.l3, DB = M.db, PN = M.pn, DESC = M.desc,
    UIO = M.db_uio, CO = M.db_country;
var RESID = M.residual_l1;
var RESID_IX = RESID.map(function(n){ return L1.indexOf(n); });
var NO_L3 = M.no_l3;
function isResidL1(k){ return RESID_IX.indexOf(k) >= 0; }

/* ---------- helpers ---------- */
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function eur(v,d){d=d==null?0:d;
  return '\u20ac'+(v==null?0:v).toLocaleString('en-GB',
    {minimumFractionDigits:d,maximumFractionDigits:d});}
function eurM(v){ return v>=1e6 ? '\u20ac'+(v/1e6).toFixed(2)+'M' : eur(v); }
function num(v,d){d=d==null?0:d;
  return (v==null?0:v).toLocaleString('en-GB',{minimumFractionDigits:d,
    maximumFractionDigits:d});}
function pc(v){ return v==null?'\u2014':(v*100).toFixed(2)+'%'; }
function pct(v){ return v==null?'\u2014':(v>=0?'+':'')+v.toFixed(2)+'%'; }
function tip(t){ return '<span class="info" tabindex="0">i<span class="tip">'+t+'</span></span>'; }

/* ---------- state ---------- */
var state = {
  db:-1,      /* -1 = all 22 distributors */
  meas:'eur', /* eur | step | pct */
  l1:-1, l2:-1, l3:-1,  /* -1 = not chosen */
  jumpTimer:null        /* pending jump-on-typing, so a redraw is not fired per keystroke */
};
var MEASLABEL = {eur:'Parts billed', step:'Step', pct:'Weighted'};

/* ---------- aggregation over the row list ----------
   ROWS: [pn, l1, l2, l3, db, qty, eur, step, prior, new, qtyp, priced]
   Filters applied as a mask, then grouped by the caller's key function.  */
function slice(){
  var out = [];
  for(var i=0;i<ROWS.length;i++){
    var r = ROWS[i];
    if(state.db>=0 && r[4]!==state.db) continue;
    if(state.l1>=0 && r[1]!==state.l1) continue;
    if(state.l2>=0 && r[2]!==state.l2) continue;
    if(state.l3>=0 && r[3]!==state.l3) continue;
    out.push(r);
  }
  return out;
}
/* Totals for a set of rows. pct is null when nothing on the slice was priced,
   so the page prints an explicit dash instead of a fake zero. */
function totals(rows){
  var t={qty:0,qtyp:0,eur:0,step:0,prior:0,new:0,pn:0,npriced:0};
  var seen={};
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    t.qty+=r[5]; t.qtyp+=r[10]; t.eur+=r[6]; t.step+=r[7];
    t.prior+=r[8]; t.new+=r[9];
    if(!seen[r[0]]){seen[r[0]]=1;t.pn++;}
    if(r[11]) t.npriced++;
  }
  t.pct = (t.prior>0 && t.npriced>0) ? 100*(t.new/t.prior-1) : null;
  return t;
}
function groupBy(rows, keyFn){
  var map={}, order=[];
  for(var i=0;i<rows.length;i++){
    var k=keyFn(rows[i]);
    if(map[k]===undefined){map[k]=[];order.push(k);}
    map[k].push(rows[i]);
  }
  var out=order.map(function(k){
    var t=totals(map[k]); t.key=k; return t;
  });
  out.sort(function(a,b){
    var av=a[state.meas], bv=b[state.meas];
    if(state.meas==='pct'){ av=(a.pct==null?-1e9:a.pct); bv=(b.pct==null?-1e9:b.pct); }
    return bv-av;
  });
  return out;
}
function growth(t){ return t.eur>0 ? t.step/t.eur : 0; }

/* ---------- Chart.js set-up ---------- */
var charts={};
if (window.Chart) {
  Chart.defaults.font.family = '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif';
  Chart.defaults.font.size = 12;
  Chart.defaults.color = '#22262e';
}
var TERRA='#c0552d', NAVY='#15233c', AMBER='#a8721f';
function killChart(id){ if(charts[id]){ charts[id].destroy(); delete charts[id]; } }
function barOpts(labels){
  return {
    indexAxis:'y',
    responsive:true, maintainAspectRatio:false,
    layout:{padding:{right:56}},
    plugins:{
      legend:{display:false},
      tooltip:{callbacks:{label:function(c){
        var t=c.chart.$totals[c.dataIndex];
        return [ MEASLABEL[state.meas]+' '+fmtMeas(t), 'Parts billed '+eur(t.eur),
                 'Step '+eur(t.step), 'Weighted '+pct(t.pct),
                 'Part numbers '+num(t.pn) ];
      }}}
    },
    scales:{
      x:{ beginAtZero:true, grid:{color:'#ece7dd'}, ticks:{callback:function(v){
            return state.meas==='pct' ? v+'%' : eurM(v); } } },
      y:{ grid:{display:false}, ticks:{autoSkip:false, callback:function(v,idx){
            var s=labels[idx]; return s.length>34 ? s.slice(0,33)+'\u2026' : s; } } }
    },
    animation:{duration:220}
  };
}
function fmtMeas(t){
  if(state.meas==='pct') return pct(t.pct);
  if(state.meas==='step') return eur(t.step);
  return eur(t.eur);
}
/* value labels at the end of each bar, drawn after layout */
var endLabel = {
  id:'endLabel',
  afterDatasetsDraw:function(chart){
    if(state.meas==='pct') return;
    var ctx=chart.ctx, meta=chart.getDatasetMeta(0);
    ctx.save();
    ctx.font='600 11px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    ctx.fillStyle='#15233c'; ctx.textBaseline='middle';
    meta.data.forEach(function(el,i){
      var t=chart.$totals[i]; if(!t) return;
      var txt = fmtMeas(t) + (t.pct!=null ? '   '+pct(t.pct) : '');
      ctx.fillText(txt, el.x+7, el.y);
    });
    ctx.restore();
  }
};
function drawBar(id, totals, labels){
  killChart(id);
  if(!totals.length){ return; }
  var ctx=document.getElementById(id);
  var colors = totals.map(function(t){ return isResidL1(t.key) ? AMBER : TERRA; });
  var ch=new Chart(ctx,{
    type:'bar',
    data:{ labels:labels, datasets:[{ data:totals.map(function(t){
            return state.meas==='pct' ? (t.pct==null?0:t.pct) : t[state.meas]; }),
          backgroundColor:colors, borderWidth:0, barPercentage:.82, categoryPercentage:.86 }] },
    options:barOpts(labels),
    plugins:[endLabel]
  });
  ch.$totals=totals;
  charts[id]=ch;
}

/* ---------- the main panel ---------- */
function drawMain(){
  var rows=slice();
  var t=totals(rows);
  var level = state.l1<0?1:(state.l2<0?2:(state.l3<0?3:4));
  var lab, q, rowsG;
  if(level===1){
    lab='AIM category (level 1)';
    q='Parts billed in this window per top-level category. The bottom of the list is where the '
      + 'pruning pain sits. Click a category to open its groups.';
    var g1=groupBy(rows,function(r){return r[1];});
    drawBar('c-main',g1,g1.map(function(x){return L1[x.key];}));
    var resid=g1.filter(function(x){return isResidL1(x.key);});
    var real=g1.filter(function(x){return !isResidL1(x.key);});
    var ord=real.concat(resid);
    rowsG=ord;
    var bl=ord.map(function(x){
      return [L1[x.key], eur(x.eur), eur(x.step), pct(x.pct),
              growth(x)>0?eur(growth(x),2):'\u2014', num(x.pn), false]; });
    fillTable('tbl', ['Category','Parts billed','Step','Weighted','Step per \u20ac1 billed',
      'Part numbers'], bl, function(i){ return function(){ pick1(ord[i].key); }; });
  } else if(level===2){
    lab='Group inside '+L1[state.l1];
    q='The groups inside this category, ranked by the selected measure. Click a group to open '
      + 'its part types.';
    var g2=groupBy(rows,function(r){return r[2];});
    drawBar('c-main',g2,g2.map(function(x){return L2[x.key][1];}));
    var bl2=g2.map(function(x){ return [L2[x.key][1], eur(x.eur), eur(x.step), pct(x.pct),
      growth(x), num(x.pn), false]; });
    fillTable('tbl', ['Group','Parts billed','Step','Weighted','Step per \u20ac1 billed',
      'Part numbers'], bl2, function(i){ return function(){ state.l2=g2[i].key; state.l3=-1;
        render(); }; });
    rowsG=g2;
  } else if(level===3){
    lab='Part type inside '+L2[state.l2][1];
    q='The part types inside this group. Two types can look equally large and behave completely '
      + 'differently, so read the weighted column beside the euro.';
    var g3=groupBy(rows,function(r){return r[3];});
    drawBar('c-main',g3,g3.map(function(x){return L3[x.key][2];}));
    var bl3=g3.map(function(x){ return [L3[x.key][2], eur(x.eur), eur(x.step), pct(x.pct),
      growth(x), num(x.pn), false]; });
    fillTable('tbl', ['Part type','Parts billed','Step','Weighted','Step per \u20ac1 billed',
      'Part numbers'], bl3, function(i){ return function(){ state.l3=g3[i].key; render(); }; });
    rowsG=g3;
  } else {
    lab='Individual part numbers inside '+L3[state.l3][2];
    q='Nothing left to expand: this is the leaf. Quantity, parts billed euro, step euro and the '
      + 'price move, per part.';
    var g4=groupBy(rows,function(r){return r[0];});
    drawBar('c-main',g4,g4.map(function(x){return DESC[x.key]||PN[x.key];}));
    var bl4=g4.map(function(x){ return [PN[x.key], DESC[x.key]||'', eur(x.eur), eur(x.step),
      pct(x.pct), num(x.qty), false]; });
    fillTable('tbl', ['Part number','Description','Parts billed','Step','Weighted','Units'],
      bl4, null);
    rowsG=g4;
  }
  document.getElementById('t-main').textContent = lab;
  document.getElementById('q-main').textContent = q;
  drawCrumb();
  drawSide(rows, level, rowsG);
  drawDist(rows);
  drawMove(rows, level);
  drawPn(rows);
  drawResid(level===1 ? rowsG : null);
  updateKpis(t, level);
}
function pick1(i){ state.l1=i; state.l2=-1; state.l3=-1; render(); }

/* ---------- the side panel ---------- */
function drawSide(rows, level, rowsG){
  var head, q, donut;
  if(level===1){
    var fam = firstReal(rowsG);
    var sub = slice().filter(function(r){return r[1]===fam;});
    var g=groupBy(sub,function(r){return r[2];});
    donut=true; head='What '+L1[fam]+' is made of';
    q='This category split into its groups, top three named and the rest combined, so the '
      + 'segments stay readable. Click a category in the panel on the left to move this chart.';
    drawDonut(g.map(function(x){return L2[x.key][1];}), g.map(function(x){return x.eur;}));
  } else if(level===4){
    donut=true; head='This part type across distributors';
    var gd=groupBy(slice(),function(r){return r[4];});
    q='Which markets carry this part type, by billed euro.';
    drawDonut(gd.map(function(x){return DB[x.key];}), gd.map(function(x){return x.eur;}));
  } else {
    donut=true;
    head='What '+L1[state.l1]+' is made of';
    q='The groups inside the selected category, top three named and the rest combined.';
    var g2=groupBy(slice().filter(function(r){return r[1]===state.l1;}),
                   function(r){return r[2];});
    drawDonut(g2.map(function(x){return L2[x.key][1];}), g2.map(function(x){return x.eur;}));
  }
  document.getElementById('t-side').textContent=head;
  document.getElementById('q-side').textContent=q;
}
function biggest(rowsG){ return rowsG.length?rowsG[0].key:0; }
function firstReal(rowsG){
  for(var i=0;i<rowsG.length;i++){ if(RESID.indexOf(rowsG[i].key)<0) return rowsG[i].key; }
  return rowsG.length?rowsG[0].key:0;
}
function drawDonut(labels, vals){
  var pairs=labels.map(function(l,i){return {l:l,v:vals[i]};});
  pairs.sort(function(a,b){return b.v-a.v;});
  var top=pairs.slice(0,3), rest=pairs.slice(3);
  var ls=top.map(function(p){return p.l;}), vs=top.map(function(p){return p.v;});
  if(rest.length){
    ls.push('Other '+rest.length+' groups');
    vs.push(rest.reduce(function(s,p){return s+p.v;},0));
  }
  killChart('c-side');
  var cols=[TERRA,'#1d3054','#7a9cc0','#c9c2b6'];
  charts['c-side']=new Chart(document.getElementById('c-side'),{
    type:'doughnut',
    data:{labels:ls,datasets:[{data:vs,backgroundColor:cols,borderColor:'#fff',borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'52%',
      plugins:{legend:{position:'bottom',labels:{boxWidth:11,boxHeight:11,padding:9}},
        tooltip:{callbacks:{label:function(c){
          var tot=vs.reduce(function(s,v){return s+v;},0);
          return c.label+': '+eur(c.parsed)+'  ('+(100*c.parsed/tot).toFixed(1)+'%)'; }}}}},
    plugins:[{id:'mid',afterDraw:function(ch){
      var ctx=ch.ctx, a=ch.chartArea, x=(a.left+a.right)/2, y=(a.top+a.bottom)/2;
      var tot=vs.reduce(function(s,v){return s+v;},0);
      ctx.save(); ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillStyle='#15233c'; ctx.font='600 15px Georgia,serif';
      ctx.fillText('\u20ac'+(tot/1e6).toFixed(2)+'M',x,y-7);
      ctx.font='11px -apple-system,Segoe UI,Roboto,Arial,sans-serif'; ctx.fillStyle='#6b6459';
      ctx.fillText('billed',x,y+9); ctx.restore(); }}]
  });
}

/* ---------- distributor table ---------- */
function drawDist(rows){
  var g=groupBy(rows,function(r){return r[4];});
  var body=g.map(function(x){
    var u=UIO[x.key];
    return [DB[x.key] + (CO[x.key]? ' <span class="muted">'+esc(CO[x.key])+'</span>':''),
            eur(x.eur), eur(x.step), pct(x.pct),
            u? num(u) : '<span class="muted">none</span>',
            x.npriced? eur(growth(x),2) : '\u2014', false];
  });
  fillTable('dist', ['Distributor','Parts billed','Step','Weighted','Trucks 2025',
    'Billed per truck'], body, null, true);
  var t=totals(rows), uioSum=0;
  for(var i=0;i<g.length;i++){ var u=UIO[g[i].key]; if(u){ uioSum+=u; } }
  document.getElementById('q-dist').innerHTML =
    'Ranked by the selected measure, with the 2025 truck fleet beside it. Network per-truck on '
    + 'this slice: <b>'+eur(t.eur/uioSum,2)+'</b> across the '+num(uioSum)+' trucks in the '
    + 'markets that have a fleet count. Four markets have none and are marked, not estimated.';
}

/* ---------- move chart ---------- */
function drawMove(rows, level){
  var g = (level===1) ? groupBy(slice(),function(r){return r[1];}) : null;
  killChart('c-move');
  if(!g){ document.getElementById('q-move').textContent =
    'Step euro against parts billed euro. A slice that is large but barely moved is a different '
    + 'conversation from one that moved hard.'; return; }
  var pts=g.map(function(x){
    return {x:x.eur,y:x.step,l:L1[x.key],p:x.pct};});
  charts['c-move']=new Chart(document.getElementById('c-move'),{
    type:'scatter',
    data:{datasets:[{data:pts,backgroundColor:TERRA,pointRadius:6,pointHoverRadius:8}]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:function(c){
        var d=c.raw; return [d.l,'Parts billed '+eur(d.x),'Step '+eur(d.y),
          'Weighted '+pct(d.p)];}}}},
      scales:{x:{title:{display:true,text:'Parts billed \u20ac'},grid:{color:'#ece7dd'},
                  ticks:{callback:function(v){return eurM(v);}}},
              y:{title:{display:true,text:'Step \u20ac'},grid:{color:'#ece7dd'},
                  ticks:{callback:function(v){return eurM(v);}}}}},
    plugins:[{id:'ptl',afterDatasetsDraw:function(ch){
      var ctx=ch.ctx; ctx.save(); ctx.font='11px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
      ctx.fillStyle='#15233c';
      ch.getDatasetMeta(0).data.forEach(function(el,i){
        var d=pts[i]; ctx.fillText(d.l.slice(0,16), el.x+8, el.y-6); }); ctx.restore(); }}]
  });
}

/* ---------- part-number table ---------- */
function drawPn(rows){
  var head=document.getElementById('t-pn').parentNode.querySelector('h2');
  var q=document.getElementById('q-pn');
  var tb=document.querySelector('#pntbl tbody');
  var th=document.querySelector('#pntbl thead');
  if(state.l3<0){
    th.innerHTML=''; tb.innerHTML='<tr><td class="muted" style="padding:16px">'
      + 'Drill down to a part type and this table fills: quantity, parts billed euro, step euro '
      + 'and the price move for each part number inside it.</td></tr>';
    head.textContent='The part numbers inside the selected part type';
    return;
  }
  head.textContent='The part numbers inside '+L3[state.l3][2];
  var g=groupBy(rows,function(r){return r[0];});
  th.innerHTML='<tr><th>Part number</th><th>Description</th><th class="n">Units</th>'
    +'<th class="n">Parts billed</th><th class="n">Step</th><th class="n">Weighted</th>'
    +'<th class="n">Step per &#8364;1 billed</th></tr>';
  tb.innerHTML=g.map(function(x){
    return '<tr><td class="nowrap">'+esc(PN[x.key])+'</td>'
      +'<td>'+esc(DESC[x.key]||'\u2014')+'</td>'
      +'<td class="n">'+num(x.qty)+'</td>'
      +'<td class="n">'+eur(x.eur)+'</td>'
      +'<td class="n">'+eur(x.step)+'</td>'
      +'<td class="n">'+pct(x.pct)+'</td>'
      +'<td class="n">'+(x.npriced?eur(growth(x),2):'\u2014')+'</td></tr>'; }).join('');
  document.getElementById('q-pn').innerHTML='Every part number billed inside this part type, for '
    + 'the selected distributor. '+(g.length===1?'One part number.':num(g.length)+' part numbers.')
    + ' If this table is empty while a part type is selected, the filter combination holds no '
    + 'part, which is a real zero rather than missing data.';
  document.getElementById('q-pn').textContent='Drill down to a part type above and this fills: '
    + 'quantity, parts billed euro, step euro and the price move for each part number inside it.';
}

/* ---------- residual strip ---------- */
function drawResid(rows){
  var el=document.getElementById('resid');
  if(!rows){
    var rr=slice().filter(function(r){return isResidL1(r[1]);});
    if(!rr.length){ el.style.display='none'; return; }
    var g=groupBy(rr,function(r){return r[1];}), t=totals(rr);
    el.style.display='block';
    el.innerHTML='<b>Not business families.</b> '+eur(t.eur)+' of the billed euro in the current '
      + 'filter sits outside a real catalogue family: '+eur(t.eur)+' across '
      + num(t.pn)+' part numbers, carrying '+eur(t.step)+' of the step. These rows are shown so '
      + 'the categories above still add up to the shipped revision, but they are placeholders, '
      + 'not families, and they belong in a classification fix rather than a price conversation.';
    return;
  }
  var resid=rows.filter(function(x){return isResidL1(x.key);});
  if(!resid.length){ el.style.display='none'; return; }
  var tot=totals(slice());
  var sumEur=resid.reduce(function(s,x){return s+x.eur;},0);
  var sumStep=resid.reduce(function(s,x){return s+x.step;},0);
  var sumPn=resid.reduce(function(s,x){return s+x.pn;},0);
  el.style.display='block';
  el.innerHTML='<b>Not business families — read these two rows as housekeeping, not as mix.</b> '
    + eur(sumEur)+' of the billed euro and '+eur(sumStep)+' of the step sit outside a real '
    + 'catalogue family, which is '+(100*sumEur/tot.eur).toFixed(2)+'% of the parts billed in '
    + 'the current filter. They are carried so the categories above still add up to the shipped '
    + 'revision. Neither is something you price — they are something you classify.'
    + '<table><thead><tr><th>Placeholder</th><th class="n">Parts billed</th>'
    + '<th class="n">Step</th><th class="n">Weighted</th><th class="n">Part numbers</th>'
    + '</tr></thead><tbody>'
    + resid.map(function(x){
        return '<tr class="clickable" data-k="'+x.key+'"><td>'+esc(L1[x.key])+'</td>'
          +'<td class="n">'+eur(x.eur)+'</td><td class="n">'+eur(x.step)+'</td>'
          +'<td class="n">'+pct(x.pct)+'</td><td class="n">'+num(x.pn)+'</td></tr>'; }).join('')
    + '</tbody></table>';
  Array.prototype.forEach.call(el.querySelectorAll('tr.clickable'),function(tr){
    tr.addEventListener('click',function(){ pick1(parseInt(tr.getAttribute('data-k'),10)); });
  });
}

/* ---------- KPIs ---------- */
function updateKpis(t, level){
  var scope = state.db<0 ? '22 distributors' : DB[state.db];
  var where = state.l1<0 ? 'all categories'
    : (state.l2<0 ? L1[state.l1]
      : (state.l3<0 ? L2[state.l2][1] : L3[state.l3][2]));
  var pricedEur = 0, unpricedEur = 0;
  var rows = slice();
  for(var i=0;i<rows.length;i++){ if(rows[i][11]) pricedEur+=rows[i][6]; else unpricedEur+=rows[i][6]; }
  var html='';
  html+=kpi('Parts billed', eur(t.eur), scope+' \u00b7 '+where, false,
    'Every in-scope line in the current filter, priced or not. This is the size of the slice.');
  html+=kpi('Step at this price revision', eur(t.step), 'on '+pc(t.step/t.eur)+' of the billed euro',
    true, 'The euro the revision adds on this slice, summed over the lines that could be priced.');
  html+=kpi('Weighted move', t.pct==null?'\u2014':pct(t.pct),
    t.npriced? num(t.npriced)+' of '+num(t.pn)+' parts priced' : 'nothing priced on this slice',
    false, 'Quantity-weighted base-price move. Not a revenue or margin outcome, and no demand '
      + 'response is modelled.');
  html+=kpi('Part numbers', num(t.pn),
    num(t.npriced)+' priced \u00b7 '+num(t.pn-t.npriced)+' not',
    false, 'Distinct part numbers inside the current filter.');
  html+=kpi('Cannot move at all', eur(unpricedEur),
    num(t.pn-t.npriced)+' parts with no price on one side',
    false, 'Lines where one side of the comparison has no base price, usually a new or a '
      + 'discontinued part. They carry weight in the billed euro but they cannot move in a '
      + 'price revision, so they are shown instead of being averaged in.');
  document.getElementById('kpis').innerHTML=html;
}
function kpi(lab,val,note,terra,tipText){
  return '<div class="kpi'+(terra?' t':'')+'"><div class="lab">'+esc(lab)+tip(esc(tipText))
    +'</div><div class="val">'+val+'</div><div class="note">'+note+'</div></div>';
}

/* ---------- breadcrumb ---------- */
function drawCrumb(){
  var c='<span class="seg" data-l="0">All categories</span>';
  if(state.l1>=0){
    c+='<span class="sep">\u203a</span><span class="seg" data-l="1">'+esc(L1[state.l1])+'</span>';
    if(state.l2>=0){
      c+='<span class="sep">\u203a</span><span class="seg" data-l="2">'
        + esc(L2[state.l2][1])+'</span>';
      if(state.l3>=0){
        c+='<span class="sep">\u203a</span><b>'+esc(L3[state.l3][2])+'</b>';
      }
    }
  }
  var el=document.getElementById('crumb');
  el.innerHTML=c;
  Array.prototype.forEach.call(el.querySelectorAll('span.seg'),function(s){
    s.addEventListener('click',function(){
      var l=parseInt(s.getAttribute('data-l'),10);
      if(l===0){ state.l1=-1; state.l2=-1; state.l3=-1; }
      else if(l===1){ state.l2=-1; state.l3=-1; }
      else if(l===2){ state.l3=-1; }
      render();
    });
  });
}

/* ---------- generic table ---------- */
function fillTable(id, heads, body, clicker, allowHtml){
  var th=document.querySelector('#'+id+' thead'), tb=document.querySelector('#'+id+' tbody');
  th.innerHTML='<tr>'+heads.map(function(h,i){
    return '<th'+(i>0?' class="n"':'')+'>'+h+'</th>'; }).join('')+'</tr>';
  tb.innerHTML=body.map(function(r,i){
    return '<tr class="'+(clicker?'clickable':'')+'">'+r.map(function(c,j){
      var v = (allowHtml||j===0) ? c : esc(c);
      return '<td'+(j>0?' class="n"':'')+'>'+v+'</td>'; }).join('')+'</tr>'; }).join('');
  if(clicker){
    Array.prototype.forEach.call(tb.querySelectorAll('tr'),function(tr,i){
      tr.addEventListener('click',clicker(i));
    });
  }
}

/* ---------- controls ---------- */
function fillControls(){
  var sel=document.getElementById('db');
  sel.innerHTML='<option value="-1">All 22 distributors</option>'
    + DB.map(function(d,i){ return '<option value="'+i+'">'+esc(d)+'</option>'; }).join('');
  sel.addEventListener('change',function(){ state.db=parseInt(sel.value,10); render(); });
  Array.prototype.forEach.call(document.querySelectorAll('#meas button'),function(b){
    b.addEventListener('click',function(){
      Array.prototype.forEach.call(document.querySelectorAll('#meas button'),
        function(x){x.classList.remove('on');});
      b.classList.add('on'); state.meas=b.getAttribute('data-m'); render();
    });
  });
  document.getElementById('reset').addEventListener('click',function(){
    state.l1=-1; state.l2=-1; state.l3=-1; render(); });
  wireSearch();
}
function wireSearch(){
  var box=document.getElementById('q'), list=document.getElementById('hitlist');
  function show(){
    var s=box.value.trim().toLowerCase();
    if(s.length<2){ list.style.display='none'; list.innerHTML=''; return; }
    var out=[], i;
    for(i=0;i<L1.length;i++){
      if(L1[i].toLowerCase().indexOf(s)>=0)
        out.push({t:L1[i],k:'L1 \u00b7 category',l1:i,l2:-1,l3:-1});
    }
    for(i=0;i<L2.length;i++){
      if(L2[i][1].toLowerCase().indexOf(s)>=0)
        out.push({t:L2[i][1],k:'L2 \u00b7 group \u2014 '+L2[i][0],
          l1:L1.indexOf(L2[i][0]), l2:i, l3:-1});
    }
    for(i=0;i<L3.length;i++){
      if(L3[i][2].toLowerCase().indexOf(s)>=0)
        out.push({t:L3[i][2],k:'L3 \u00b7 part type \u2014 '+L3[i][0]+' \u203a '+L3[i][1],
          l1:L1.indexOf(L3[i][0]),
          l2:L2.findIndex(function(x){return x[0]===L3[i][0] && x[1]===L3[i][1];}),
          l3:i});
    }
    for(i=0;i<PN.length && out.length<40;i++){
      if(PN[i].indexOf(s)>=0)
        out.push({t:PN[i],k:'part number \u2014 '+(DESC[i]||''),pn:i});
    }
    out=out.slice(0,26);
    if(!out.length){ list.innerHTML='<div class="muted">Nothing matches that.</div>';
      list.style.display='block'; return; }
    list.innerHTML=out.map(function(o,i){
      return '<div data-i="'+i+'"><b>'+esc(o.t)+'</b><span class="k">'+esc(o.k)+'</span></div>';
    }).join('');
    list.style.display='block';
    Array.prototype.forEach.call(list.querySelectorAll('div[data-i]'),function(d){
      d.addEventListener('click',function(){ jump(out[parseInt(d.getAttribute('data-i'),10)]); });
    });
  }
  function jump(o){
    list.style.display='none'; box.value=o.t;
    if(o.pn!==undefined){
      /* find the leaf this part number sits in, then open its parent chain */
      var found=null;
      for(var i=0;i<ROWS.length;i++){
        if(ROWS[i][0]===o.pn){ state.l1=ROWS[i][1]; state.l2=ROWS[i][2];
          state.l3=ROWS[i][3]; found=o.pn; break; }
      }
      render();
      if(found===null){ return; }
      var want=PN[o.pn];
      var tb=document.querySelector('#pntbl tbody');
      Array.prototype.forEach.call(tb.querySelectorAll('tr'),function(tr){
        if(tr.firstChild && tr.firstChild.textContent===want){
          tr.classList.add('sel');
          var box2=document.querySelector('#pntbl').parentNode;
          box2.scrollTop = tr.offsetTop - box2.clientHeight/2;
        }
      });
      return;
    }
    if(o.l1!==undefined && o.l1>=0){
      state.l1=o.l1;
      state.l2=(o.l2!==undefined && o.l2>=0)?o.l2:-1;
      state.l3=(o.l3!==undefined && o.l3>=0)?o.l3:-1;
    } else {
      state.l1=-1; state.l2=-1; state.l3=-1;
    }
    render();
  }
  box.addEventListener('input',function(){
    show();
    if(state.jumpTimer){ clearTimeout(state.jumpTimer); }
    var s=box.value.trim().toLowerCase();
    if(s.length>=4 && PN.indexOf(s)>=0){ state.jumpTimer=setTimeout(function(){ if(box.value.trim().toLowerCase()===s){ jump({t:s,k:'',pn:PN.indexOf(s)}); } },50); }
  });
  box.addEventListener('focus',show);
  document.addEventListener('click',function(e){
    if(!document.getElementById('hits').contains(e.target)) list.style.display='none'; });
}

/* ---------- render ---------- */
function render(){
  try{
    drawMain();
    document.getElementById('errbar').style.display='none';
  }catch(err){
    var b=document.getElementById('errbar');
    b.style.display='block';
    b.innerHTML='<b>Something failed while drawing.</b> '+esc(err && err.message ? err.message : err);
  }
}
function boot(){
  var r=M.repertoire;
  document.getElementById('sub-pn').textContent=num(M.checks.part_numbers);
  document.getElementById('r-tree').textContent=num(r.tree_part_numbers);
  document.getElementById('r-l1').textContent=r.tree_l1;
  document.getElementById('r-billed').textContent=num(r.billed_in_tree);
  document.getElementById('r-billed2').textContent=num(r.billed_in_tree);
  document.getElementById('r-silent').textContent=num(r.classified_not_billed);
  document.getElementById('genline').textContent =
    ' Built '+M.built.slice(0,10)+', source '+M.source+'.';
  fillControls();
  render();
}
window.render=render;
window.drillState=state;
window.__aimReady=true;
boot();
})();
</script>
</body>
</html>
"""


def main() -> int:
    payload = (BUILD / "payload.json").read_text(encoding="utf-8")
    chart = CHART.read_text(encoding="utf-8")
    chart = chart.replace("//# sourceMappingURL=chart.umd.min.js.map", "")
    html = HTML.replace("__PAYLOAD__", payload).replace("__CHARTJS__", chart)
    OUT.write_text(html, encoding="utf-8")
    size = OUT.stat().st_size
    print(f"payload  {len(payload)/1024:,.0f} KB")
    print(f"chart.js {len(chart)/1024:,.0f} KB")
    print(f"-> {OUT}  ({size/1024/1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
