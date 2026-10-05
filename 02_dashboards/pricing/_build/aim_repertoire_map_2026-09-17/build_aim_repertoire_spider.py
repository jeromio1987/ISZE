#!/usr/bin/env python3
"""Build ISZE_AIM_Repertoire_Spider_2026-09-17.html - the radial AIM map.

Nothing new is computed here. It reads the payload the drill page already uses:

  02_dashboards/pricing/_build/aim_repertoire_map_2026-09-17/payload.json

and draws the same numbers as a radial map: the book at the centre, the three AIM
levels as rings out from it, the 22 distributors on the outer ring, and links
between a part type and the markets that bill it.

Read-only. Nothing under 01_data/00_derived/ is touched, and the drill page is
left exactly as built.
"""
from __future__ import annotations

from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BUILD = ISZE / "02_dashboards" / "pricing" / "_build" / "aim_repertoire_map_2026-09-17"
OUT = ISZE / "02_dashboards" / "pricing" / "ISZE_AIM_Repertoire_Spider_2026-09-17.html"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All the connections - the AIM repertoire as one map</title>
<style>
:root{
  --navy:#15233c; --navy2:#1d3054; --terra:#c0552d; --paper:#f7f4ee;
  --ink:#22262e; --muted:#6b6459; --line:#d9d3c8; --band:#eef3f9;
  --amber:#a8721f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:14px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
h1{font-size:24px;letter-spacing:-.2px}
h2{font-size:17px;margin-bottom:2px}
h3{font-size:13px}
.wrap{max-width:1600px;margin:0 auto;padding:18px 20px 50px}
header.top{border-bottom:3px solid var(--navy);padding-bottom:12px;margin-bottom:14px}
.sub{color:var(--muted);font-size:13px;margin-top:6px}
.badge{display:inline-block;background:var(--navy);color:var(--paper);
  font-size:11px;letter-spacing:.6px;text-transform:uppercase;
  padding:3px 9px;border-radius:2px;margin-right:8px}
.badge.t{background:var(--terra)}

.controls{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-end;
  background:#fff;border:1px solid var(--line);border-left:4px solid var(--terra);
  padding:12px 15px;margin-bottom:14px}
.ctrl{display:flex;flex-direction:column;gap:5px}
.ctrl.grow{flex:1 1 230px}
.ctrl label{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted)}
select,input[type=search]{font-size:14px;padding:7px 10px;border:1px solid var(--line);
  background:#fff;color:var(--ink);border-radius:2px;min-width:170px;font-family:inherit}
input[type=search]{width:100%;min-width:0}
select:focus,input:focus{outline:2px solid var(--terra);outline-offset:-1px}
.seg{display:flex;border:1px solid var(--line);border-radius:2px;overflow:hidden;flex-wrap:wrap}
.seg button{background:#fff;border:0;border-right:1px solid var(--line);
  padding:7px 12px;font-size:13px;cursor:pointer;color:var(--ink);font-family:inherit}
.seg button:last-child{border-right:0}
.seg button.on{background:var(--navy);color:var(--paper)}
.reset{background:#fff;border:1px solid var(--line);padding:7px 13px;font-size:13px;
  cursor:pointer;color:var(--terra);border-radius:2px;font-family:inherit}
.reset:hover{border-color:var(--terra)}
#hits{position:relative}
#hitlist{position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid var(--line);
  border-top:0;max-height:300px;overflow:auto;z-index:70;display:none;
  box-shadow:0 8px 20px rgba(0,0,0,.12)}
#hitlist div{padding:7px 11px;cursor:pointer;font-size:13px;border-bottom:1px solid #f0ece4}
#hitlist div:hover{background:var(--band)}
#hitlist .k{color:var(--muted);font-size:11.5px;display:block}

.stage{position:relative;background:#fff;border:1px solid var(--line)}
#map{display:block;width:100%;height:840px;cursor:crosshair}
#hint{position:absolute;left:12px;bottom:10px;font-size:11.5px;color:var(--muted);
  background:rgba(247,244,238,.92);padding:3px 8px;border:1px solid var(--line)}
#tip{position:fixed;display:none;background:var(--navy);color:var(--paper);font-size:12.5px;
  line-height:1.45;padding:9px 11px;border-radius:3px;z-index:90;pointer-events:none;
  max-width:330px;box-shadow:0 4px 16px rgba(0,0,0,.3)}
#tip b{color:#f0b49a}
#tip .r{color:#c8d4e6}

.legend{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0 16px}
.lg{display:flex;align-items:center;gap:6px;font-size:12px;background:#fff;
  border:1px solid var(--line);padding:4px 9px;border-radius:2px;cursor:pointer}
.lg.off{opacity:.32}
.sw{width:11px;height:11px;border-radius:2px;flex:0 0 auto}
.lg .n{color:var(--muted)}

.grid{display:grid;gap:14px;margin-bottom:14px}
.g2{grid-template-columns:1fr 1fr;align-items:start}
.g3{grid-template-columns:1fr 1fr 1fr;align-items:start}
@media(max-width:1100px){.g2,.g3{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);padding:14px 15px 12px;min-width:0}
.card .q{font-size:13px;color:var(--muted);margin:3px 0 11px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:7px 9px;
  font-weight:600;font-size:11.5px;letter-spacing:.4px;text-transform:uppercase;
  position:sticky;top:0;white-space:nowrap}
th.n,td.n{text-align:right;font-variant-numeric:tabular-nums}
td{padding:6px 9px;border-bottom:1px solid var(--line)}
tbody tr:nth-child(even){background:var(--band)}
.tblwrap{max-height:330px;overflow:auto;border:1px solid var(--line)}
.muted{color:var(--muted)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:11px}
.fact{border-left:3px solid var(--navy);padding-left:10px}
.fact .l{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.fact .v{font-size:17px;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums}
.fact .n{font-size:11.5px;color:var(--muted)}
.crumb{font-size:12.5px;color:var(--muted);margin-bottom:10px}
.crumb b{color:var(--navy)}
.warn{background:#fdf3e3;border:1px solid #e6cf9f;border-left:4px solid var(--amber);
  padding:10px 13px;font-size:12.5px;color:#5e4a1c;margin-bottom:14px}
.foot{font-size:12px;color:var(--muted);border-top:1px solid var(--line);
  padding-top:12px;margin-top:22px}
.foot ul{margin:8px 0 0;padding-left:18px}
.foot li{margin-bottom:5px}
.info{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;
  border-radius:50%;background:var(--navy);color:#fff;font-size:9.5px;cursor:help;
  position:relative;flex:0 0 auto}
.info .tp{display:none;position:absolute;bottom:22px;left:50%;transform:translateX(-50%);
  width:280px;background:var(--navy);color:var(--paper);font-size:12px;line-height:1.45;
  padding:9px 11px;border-radius:3px;z-index:95;font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25)}
.info:hover .tp,.info:focus .tp{display:block}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div><span class="badge">AIM map</span><span class="badge t">Internal</span></div>
  <h1 style="margin-top:9px">The whole repertoire on one map, and every connection on it</h1>
  <div class="sub">The book sits in the middle. Each ring out from it is one AIM level:
    the eight categories, then their groups, then the part types. The outer ring is the
    22 distributors. A ribbon between a part type and a distributor means that market
    actually bills that part type, and the ribbon is as thick as the euro. Parts billed
    1 July 2025 to 30 June 2026. Opens from Explorer with no server and no internet.
    <span id="genline"></span></div>
</header>

<div class="controls">
  <div class="ctrl">
    <label>Colour the leaves by</label>
    <div class="seg" id="mode">
      <button data-m="cat" class="on">AIM category</button>
      <button data-m="step">Share of the step</button>
      <button data-m="pct">Weighted move</button>
    </div>
  </div>
  <div class="ctrl">
    <label>Market ribbons</label>
    <div class="seg" id="links">
      <button data-l="all" class="on">All connections</button>
      <button data-l="sel">On the selected part type</button>
      <button data-l="off">None</button>
    </div>
  </div>
  <div class="ctrl">
    <label for="db">Distributor</label>
    <select id="db"></select>
  </div>
  <div class="ctrl grow">
    <label for="q">Jump to a part type or a part number</label>
    <div id="hits"><input type="search" id="q" placeholder="e.g. oil filter, brake parts, 8982705240"
      autocomplete="off"><div id="hitlist"></div></div>
  </div>
  <div class="ctrl">
    <label>&nbsp;</label>
    <button class="reset" id="reset">Clear the selection</button>
  </div>
</div>

<div class="legend" id="legend"></div>

<div class="stage">
  <canvas id="map"></canvas>
  <div id="hint">Hover to read a node &middot; click to pin it &middot; <b>+</b> / <b>&minus;</b> to zoom,
    drag to pan, <b>0</b> to reset the view</div>
</div>

<div class="grid g2" style="margin-top:14px">
  <div class="card">
    <h2 id="d-head">Nothing selected</h2>
    <div class="crumb" id="d-crumb">Hover the map. Click a wedge to pin it and fill this panel.</div>
    <div class="q" id="d-q"></div>
    <div class="facts" id="d-facts"></div>
  </div>
  <div class="card">
    <h2>Where the selected slice is billed</h2>
    <div class="q" id="d-distq">The markets that carry the selected node, by parts billed euro.</div>
    <div class="tblwrap"><table id="d-dist"><thead></thead><tbody></tbody></table></div>
  </div>
</div>

<div class="grid g2">
  <div class="card">
    <h2>The part numbers inside the selected slice</h2>
    <div class="q" id="d-pnq">The biggest lines in the selection, by parts billed euro. A part
      number on its own is a quantity, so the description and the move sit beside it.</div>
    <div class="tblwrap"><table id="d-pn"><thead></thead><tbody></tbody></table></div>
  </div>
  <div class="card">
    <h2>How the four rings divide the book</h2>
    <div class="q">Read top to bottom: the categories, then the largest groups, then the largest
      part types, then the markets. Each row is a share of the same &#8364;34,993,609, so the
      numbers are comparable down the table.</div>
    <div class="tblwrap"><table id="d-share"><thead></thead><tbody></tbody></table></div>
  </div>
</div>

<div class="warn">
  <b>What the middle of the map is, and what it is not.</b> The centre is the
  &#8364;34,993,609 of parts billed in this window — the slice of the repertoire that actually
  moved money. The AIM tree classifies <span id="w-tree"></span> part numbers; only
  <span id="w-billed"></span> of them billed here, so <span id="w-silent"></span> classified part
  numbers are not on this map at all. They carry no quantity, no euro and no price move, and a
  count of parts with no revenue is not a finding. The map shows what moved, and names the gap
  rather than drawing the silent 90% as if it were business.
</div>

<div class="foot">
  <b>How to read it, and the limits.</b>
  <ul>
    <li>A wedge is as wide as its share of parts billed euro. The geometry never moves when you
      change the colour, so the map stays comparable while you look at different measures.</li>
    <li>The weighted percentage is a base-price move on the quantity-weighted prior base price.
      It is not a revenue, margin or elasticity outcome, and no demand response is modelled.</li>
    <li>Ribbons are drawn from a part type to the markets that bill it. A market with no ribbon on
      a leaf genuinely does not bill that part type — that is a real zero, not a missing figure.</li>
    <li>A part number with no catalogue node is labelled UNCLASSIFIED and carried, so the
      category arcs add up to the shipped revision total.</li>
    <li>The commercial score — contested or captive, per part per market — is a separate axis and
      is not built as columns yet, so this map cannot show it. It does not guess from the Isuzu
      figure key.</li>
    <li>Israel is UMI and UTI separately, never blended. Source of supply (Japan through IML
      against Thailand through IMIT) is not on this map yet.</li>
  </ul>
</div>

</div>
<div id="tip"></div>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
(function(){
"use strict";

/* ================= data ================= */
var P = JSON.parse(document.getElementById('payload').textContent);
var M = P.meta, ROWS = P.rows;
var L1N = M.l1, L2N = M.l2, L3N = M.l3, DBN = M.db, PN = M.pn, DESC = M.desc;
var RESID_IX = M.residual_l1.map(function(n){ return L1N.indexOf(n); });

function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function eur(v,d){d=d==null?0:d; return '\u20ac'+(v||0).toLocaleString('en-GB',
  {minimumFractionDigits:d,maximumFractionDigits:d});}
function eurM(v){ return Math.abs(v)>=1e6 ? '\u20ac'+(v/1e6).toFixed(2)+'M' : eur(v); }
function num(v,d){d=d==null?0:d; return (v||0).toLocaleString('en-GB',
  {minimumFractionDigits:d,maximumFractionDigits:d});}
function pct(v){ return v==null?'\u2014':(v>=0?'+':'')+v.toFixed(2)+'%'; }
function pc(v){ return v==null?'\u2014':(v*100).toFixed(1)+'%'; }

/* ================= tree ================= */
/* Each node: {lv, ix, key, name, euro, step, prior, new, qty, pn, priced, prev}
   lv 1/2/3 are the AIM levels; lv 4 is a distributor. */
var byL1 = {}, byL2 = {}, byL3 = {}, byDB = {};

function tot(r){  /* per-row totals accumulator */
  return {euro:r[6], step:r[7], prior:r[8], new:r[9], qty:r[5], qtyp:r[10],
          priced:r[11]?1:0, n:1};
}
function add(a,b){
  a.euro+=b.euro; a.step+=b.step; a.prior+=b.prior; a.new+=b.new;
  a.qty+=b.qty; a.qtyp+=b.qtyp; a.priced+=b.priced; a.n+=b.n; return a;
}
function zero(){ return {euro:0,step:0,prior:0,new:0,qty:0,qtyp:0,priced:0,n:0,
  pn:{}, dbs:{}, pns:{}}; }

var ALL = zero();
var N1 = [], N2 = [], N3 = [], ND = [];
var i;
for(i=0;i<L1N.length;i++){ N1.push(zero()); N1[i].lv=1; N1[i].ix=i; N1[i].name=L1N[i]; }
for(i=0;i<L2N.length;i++){ N2.push(zero()); N2[i].lv=2; N2[i].ix=i; N2[i].name=L2N[i][1];
  N2[i].p=L1N.indexOf(L2N[i][0]); }
for(i=0;i<L3N.length;i++){ N3.push(zero()); N3[i].lv=3; N3[i].ix=i; N3[i].name=L3N[i][2];
  N3[i].p=L2N.findIndex(function(x){return x[0]===L3N[i][0] && x[1]===L3N[i][1];}); }
for(i=0;i<DBN.length;i++){ ND.push(zero()); ND[i].lv=4; ND[i].ix=i; ND[i].name=DBN[i]; }

for(i=0;i<ROWS.length;i++){
  var r=ROWS[i], t=tot(r);
  add(N1[r[1]],t); add(N2[r[2]],t); add(N3[r[3]],t); add(ND[r[4]],t);
  ALL.euro+=r[6]; ALL.step+=r[7]; ALL.prior+=r[8]; ALL.new+=r[9];
  ALL.qty+=r[5]; ALL.qtyp+=r[10]; ALL.priced+=r[11]?1:0; ALL.n++;
  N1[r[1]].pn[r[0]]=1; N2[r[2]].pn[r[0]]=1; N3[r[3]].pn[r[0]]=1; ND[r[4]].pn[r[0]]=1;
  /* the connection table: leaf -> distributor euro */
  var k=r[3]+'_'+r[4];
  byL3[k]=(byL3[k]||0)+r[6];
  if(!N3[r[3]].dbs[r[4]]) N3[r[3]].dbs[r[4]]={euro:0,step:0,prior:0,new:0,qty:0,priced:0};
  var d=N3[r[3]].dbs[r[4]];
  d.euro+=r[6]; d.step+=r[7]; d.prior+=r[8]; d.new+=r[9]; d.qty+=r[5];
  d.priced+=r[11]?1:0;
  var pk=r[3]+'_'+r[0];
  N3[r[3]].pns[r[0]]=(N3[r[3]].pns[r[0]]||0)+r[6];
}
N1.forEach(function(n){ n.npn=Object.keys(n.pn).length; });
N2.forEach(function(n){ n.npn=Object.keys(n.pn).length; });
N3.forEach(function(n){ n.npn=Object.keys(n.pn).length; });
ND.forEach(function(n){ n.npn=Object.keys(n.pn).length; });

function movePct(n){ return (n.prior>0 && n.priced>0) ? 100*(n.new/n.prior-1) : null; }
function stepRatio(n){ return n.euro>0 ? n.step/n.euro : 0; }
[N1,N2,N3,ND].forEach(function(arr){ arr.forEach(function(n){
  n.pct=movePct(n); n.ratio=stepRatio(n); n.share=n.euro/ALL.euro; }); });
ALL.pct=movePct(ALL);

/* ================= colours ================= */
var CAT = ['#c0552d','#1d3054','#7a9cc0','#1e6b4f','#8a5622','#5b6b7f','#b0873a','#6b4a6b'];
function catColour(ix){ return RESID_IX.indexOf(ix)>=0 ? '#a8721f' : CAT[ix % CAT.length]; }
/* heat ramps for the two analytical colour modes */
function rampStep(v, max){   /* 0 .. 1 -> pale to deep terracotta */
  var t=Math.max(0,Math.min(1, max>0?v/max:0));
  var r=Math.round(247+(176-247)*t), g=Math.round(232+(85-232)*t), b=Math.round(214+(45-214)*t);
  return 'rgb('+r+','+g+','+b+')';
}
function rampMove(v){        /* diverging: soft blue -> grey -> terracotta, centred on the network */
  if(v==null) return '#ded8cc';
  var lo=0, hi=14, mid=ALL.pct;
  if(v<=mid){ var t=(mid-v)/Math.max(0.01,mid-lo); t=Math.max(0,Math.min(1,t));
    var r=Math.round(217+(157-217)*t), g=Math.round(216+(196-216)*t), b=Math.round(208+(214-208)*t);
    return 'rgb('+r+','+g+','+b+')'; }
  var t2=(v-mid)/Math.max(0.01,hi-mid); t2=Math.max(0,Math.min(1,t2));
  var r2=Math.round(217+(192-217)*t2), g2=Math.round(216+(85-216)*t2), b2=Math.round(208+(45-208)*t2);
  return 'rgb('+r2+','+g2+','+b2+')';
}
var maxStepShare = 0;
N3.forEach(function(n){ maxStepShare=Math.max(maxStepShare, n.step/ALL.step); });

/* ================= layout ================= */
var PAD1=0.014, PAD2=0.0045, PAD3=0.0016;
function layout(){
  /* order children by euro desc so the biggest sits first from the top, clockwise */
  var order1 = N1.map(function(n){return n.ix;})
    .sort(function(a,b){ return N1[b].euro-N1[a].euro; });
  var a=-Math.PI/2, out={};
  order1.forEach(function(i){
    var span=2*Math.PI*(N1[i].euro/ALL.euro);
    var a0=a+PAD1/2, a1=a+span-PAD1/2;
    if(a1<a0) a1=a0+0.001;
    N1[i].a0=a0; N1[i].a1=a1;
    var kids=N2.map(function(n,j){return j;})
      .filter(function(j){return N2[j].p===i;})
      .sort(function(x,y){ return N2[y].euro-N2[x].euro; });
    var b=a0;
    kids.forEach(function(j){
      var s=(a1-a0)*(N2[j].euro/N1[i].euro);
      var b0=b+PAD2/2, b1=b+s-PAD2/2;
      if(b1<b0) b1=b0+0.0008;
      N2[j].a0=b0; N2[j].a1=b1;
      var ks=N3.map(function(n,k){return k;})
        .filter(function(k){return N3[k].p===j;})
        .sort(function(x,y){ return N3[y].euro-N3[x].euro; });
      var c=b0;
      ks.forEach(function(k){
        var s3=(b1-b0)*(N3[k].euro/N2[j].euro);
        var c0=c+PAD3/2, c1=c+s3-PAD3/2;
        if(c1<c0) c1=c0+0.0004;
        N3[k].a0=c0; N3[k].a1=c1;
        c+=s3;
      });
      b+=s;
    });
    a+=span;
  });
  /* distributors: equal angles, biggest first, so the ring reads as a league table */
  var dOrder=ND.map(function(n){return n.ix;})
    .sort(function(x,y){ return ND[y].euro-ND[x].euro; });
  var da=-Math.PI/2, dspan=2*Math.PI/ND.length;
  dOrder.forEach(function(x){
    ND[x].a0=da+dspan*0.06; ND[x].a1=da+dspan*0.94; da+=dspan;
  });
  return out;
}
layout();

var RING = {  /* fractions of the base radius */
  c:      [0.00, 0.155],
  l1:     [0.195, 0.360],
  l2:     [0.400, 0.555],
  l3:     [0.595, 0.775],
  db:     [0.845, 0.985]
};

/* ================= canvas ================= */
var cv=document.getElementById('map'), ctx=cv.getContext('2d');
var W=0,H=0,DPR=1,R=1;
var view={s:1, tx:0, ty:0};
var state={mode:'cat', links:'all', db:-1, sel:null, hover:null, hidden:{}};

function resize(){
  DPR=Math.min(2, window.devicePixelRatio||1);
  W=cv.clientWidth; H=cv.clientHeight;
  cv.width=Math.round(W*DPR); cv.height=Math.round(H*DPR);
  R=Math.min(W,H)/2-26;
  draw();
}
window.addEventListener('resize', resize);

function arc(r0,r1,a0,a1){
  ctx.beginPath();
  if(a1-a0 < 0.0009){ ctx.moveTo(0,0); return; }
  ctx.arc(0,0,r1,a0,a1);
  ctx.arc(0,0,r0,a1,a0,true);
  ctx.closePath();
}
function nodeColour(n, lv){
  if(lv===1){ if(state.hidden[n.ix]) return '#cfc9bd'; return catColour(n.ix); }
  if(lv===2){ if(state.hidden[N2[n.ix].p] || state.hidden[n.p]) return '#d8d2c6';
    return shade(catColour(n.p), 0.14); }
  if(state.mode==='cat'){
    return state.hidden[n.p>=0?N2[n.p].p:0] ? '#dcd6ca' : shade(catColour(N2[n.p].p), -0.06);
  }
  if(state.mode==='step') return rampStep(n.step/ALL.step, maxStepShare);
  return rampMove(n.pct);
}
function shade(hex, amt){  /* amt>0 lightens, <0 darkens */
  var c=hex.replace('#',''); var r=parseInt(c.slice(0,2),16), g=parseInt(c.slice(2,4),16),
      b=parseInt(c.slice(4,6),16);
  if(amt>0){ r=r+(255-r)*amt; g=g+(255-g)*amt; b=b+(255-b)*amt; }
  else { r=r*(1+amt); g=g*(1+amt); b=b*(1+amt); }
  return 'rgb('+Math.round(r)+','+Math.round(g)+','+Math.round(b)+')';
}

function dim(arr, lv){  /* a node is dimmed when it is not on the selected branch */
  if(!state.sel) return false;
  var s=state.sel;
  if(s.lv===lv && s.ix===arr) return false;
  if(lv===3){ if(s.lv===3) return arr!==s.ix;
    if(s.lv===2) return N3[arr].p!==s.ix;
    if(s.lv===1) return N2[N3[arr].p].p!==s.ix; }
  if(lv===2){ if(s.lv===3) return N3[s.ix].p!==arr;
    if(s.lv===2) return arr!==s.ix;
    if(s.lv===1) return N2[arr].p!==s.ix; }
  if(lv===1){ if(s.lv===3) return N2[N3[s.ix].p].p!==arr;
    if(s.lv===2) return N2[s.ix].p!==arr;
    if(s.lv===1) return arr!==s.ix; }
  if(lv===4){ return !leafHasDB(state.sel, arr); }
  return false;
}
function leafHasDB(sel, dbIx){
  var leaf = sel.lv===3 ? sel.ix : null;
  if(leaf==null) return true;   /* a category spans everything */
  return !!N3[leaf].dbs[dbIx];
}

function draw(){
  ctx.setTransform(DPR,0,0,DPR,0,0);
  ctx.clearRect(0,0,W,H);
  ctx.save();
  ctx.translate(W/2+view.tx, H/2+view.ty);
  ctx.scale(view.s, view.s);

  /* ---- ribbons, behind the rings */
  if(state.links!=='off') drawLinks();

  /* ---- rings */
  ctx.lineWidth=0.6; ctx.strokeStyle='rgba(255,255,255,.85)';
  var r1=RING.l1.map(function(f){return f*R;}), r2=RING.l2.map(function(f){return f*R;});
  var r3=RING.l3.map(function(f){return f*R;}), r4=RING.db.map(function(f){return f*R;});

  N1.forEach(function(n){
    ctx.fillStyle=dim(n.ix,1)?'#d9d3c8':nodeColour(n,1);
    arc(r1[0],r1[1],n.a0,n.a1); ctx.fill(); ctx.stroke();
  });
  N2.forEach(function(n){
    ctx.fillStyle=dim(n.ix,2)?'#ded8cc':nodeColour(n,2);
    arc(r2[0],r2[1],n.a0,n.a1); ctx.fill(); ctx.stroke();
  });
  N3.forEach(function(n){
    if(state.hidden[N2[n.p].p]) { ctx.fillStyle='#eee9e0'; }
    else ctx.fillStyle=dim(n.ix,3)?'#e2ddd3':nodeColour(n,3);
    arc(r3[0],r3[1],n.a0,n.a1); ctx.fill(); ctx.stroke();
  });
  ND.forEach(function(n){
    ctx.fillStyle=(state.db>=0 && state.db!==n.ix) ? '#dcd6ca'
      : (dim(n.ix,4)?'#dcd6ca':'#1d3054');
    arc(r4[0],r4[1],n.a0,n.a1); ctx.fill(); ctx.stroke();
  });

  /* ---- centre disc */
  var bookSel = state.sel && state.sel.lv===0;
  ctx.beginPath(); ctx.arc(0,0,RING.c[1]*R,0,2*Math.PI);
  ctx.fillStyle=(state.sel && !bookSel)?'#f2ece2':'#15233c'; ctx.fill();
  ctx.fillStyle=(state.sel && !bookSel)?'#15233c':'#f7f4ee';
  ctx.textAlign='center';
  var cLab = (state.sel && !bookSel) ? nameOf(state.sel) : 'The book';
  var cPct = (state.sel && state.sel.lv!==4 && !bookSel) ? state.sel.pct : ALL.pct;
  ctx.font='600 15px Georgia,serif';
  var cl = cLab.length>22 ? cLab.slice(0,21)+'\u2026' : cLab;
  ctx.fillText(cl,0,-6);
  ctx.font='600 17px Georgia,serif';
  ctx.fillText((state.sel && !bookSel)? eurM(state.sel.euro) : eurM(ALL.euro), 0, 13);
  ctx.font='11px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
  ctx.fillStyle=(state.sel && !bookSel)?'#6b6459':'#c8d4e6';
  ctx.fillText(cPct!=null ? pct(cPct)+' weighted' : 'parts billed', 0, 27);

  /* ---- labels */
  N1.forEach(function(n){
    if(n.a1-n.a0 < 0.05) return;
    var m=(n.a0+n.a1)/2, rr=(r1[0]+r1[1])/2;
    var x=Math.cos(m)*rr, y=Math.sin(m)*rr;
    var flip = Math.cos(m)<0;
    ctx.save(); ctx.translate(x,y); ctx.rotate(m+(flip?Math.PI/2:-Math.PI/2));
    ctx.fillStyle='#f7f4ee'; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.font='600 12px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    var nm=n.name.length>20 ? n.name.slice(0,19)+'\u2026' : n.name;
    ctx.fillText(nm,0,0);
    ctx.restore();
  });
  ND.forEach(function(n){
    var m=(n.a0+n.a1)/2, rr=(r4[0]+r4[1])/2;
    var x=Math.cos(m)*rr, y=Math.sin(m)*rr;
    var flip=Math.cos(m)<0;
    ctx.save(); ctx.translate(x,y); ctx.rotate(m+(flip?Math.PI/2:-Math.PI/2));
    ctx.fillStyle=(state.db>=0 && state.db!==n.ix)?'#9a9284':'#f7f4ee';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.font='600 10.5px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    ctx.fillText(n.name,0,0);
    ctx.restore();
  });
  /* group labels only where there is room; otherwise they appear on hover */
  N2.forEach(function(n){
    var span=n.a1-n.a0;
    if(span < 0.20 || view.s<1.35) return;
    var m=(n.a0+n.a1)/2, rr=(r2[0]+r2[1])/2;
    var x=Math.cos(m)*rr, y=Math.sin(m)*rr, flip=Math.cos(m)<0;
    ctx.save(); ctx.translate(x,y); ctx.rotate(m+(flip?Math.PI/2:-Math.PI/2));
    ctx.fillStyle='#f7f4ee'; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.font='600 10px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    ctx.fillText(n.name,0,0); ctx.restore();
  });
  if(state.sel && state.sel.lv>=2){
    var s=state.sel, rr3=(r3[0]+r3[1])/2, m3=(s.a0+s.a1)/2;
    var x3=Math.cos(m3)*(rr3+RING.l3[1]*R*0.06), y3=Math.sin(m3)*(rr3+0);
    ctx.font='600 12px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
    ctx.textAlign='center'; ctx.textBaseline='middle';
    var tx=Math.cos(m3)*(r3[1]+16), ty=Math.sin(m3)*(r3[1]+16);
    var w=ctx.measureText(s.name).width;
    ctx.fillStyle='rgba(21,35,60,.92)';
    ctx.fillRect(tx-w/2-6, ty-9, w+12, 18);
    ctx.fillStyle='#f7f4ee'; ctx.fillText(s.name, tx, ty);
  }
  ctx.restore();
}

function nameOf(sel){
  if(!sel || sel.lv===0) return 'The book';
  if(sel.lv===1) return L1N[sel.ix];
  if(sel.lv===2) return L2N[sel.ix][1];
  if(sel.lv===3) return L3N[sel.ix][2];
  return DBN[sel.ix];
}
function pathOf(sel){
  if(!sel || sel.lv===0) return 'All categories \u00b7 all 22 distributors';
  if(sel.lv===1) return L1N[sel.ix];
  if(sel.lv===2) return L1N[N2[sel.ix].p]+' \u203a '+L2N[sel.ix][1];
  if(sel.lv===3){ var p=N3[sel.ix].p;
    return L1N[N2[p].p]+' \u203a '+L2N[p][1]+' \u203a '+L3N[sel.ix][2]; }
  return DBN[sel.ix];
}
function nodeOf(sel){
  if(!sel || sel.lv===0) return ALL;
  if(sel.lv===1) return N1[sel.ix];
  if(sel.lv===2) return N2[sel.ix];
  if(sel.lv===3) return N3[sel.ix];
  return ND[sel.ix];
}

/* ---------- ribbons ---------- */
function drawLinks(){
  var r3o=RING.l3[1]*R, r4i=RING.db[0]*R;
  var maxW=0, list=[];
  if(state.links==='all'){
    N3.forEach(function(n){
      if(state.hidden[N2[n.p].p]) return;
      if(state.db>=0 && !n.dbs[state.db]) return;
      for(var d in n.dbs){ if(state.db>=0 && +d!==state.db) continue;
        var v=n.dbs[d].euro; list.push([n.a0,n.a1,+d,v]); if(v>maxW) maxW=v; }
    });
  } else if(state.sel && state.sel.lv===3){
    var n=N3[state.sel.ix];
    for(var d2 in n.dbs){ if(state.db>=0 && +d2!==state.db) continue;
      var v2=n.dbs[d2].euro; list.push([n.a0,n.a1,+d2,v2]); if(v2>maxW) maxW=v2; }
  } else if(state.sel && state.sel.lv===2){
    N3.forEach(function(n){ if(n.p!==state.sel.ix) return;
      for(var d3 in n.dbs){ if(state.db>=0 && +d3!==state.db) continue;
        var v3=n.dbs[d3].euro; list.push([n.a0,n.a1,+d3,v3]); if(v3>maxW) maxW=v3; }
    });
  } else if(state.sel && state.sel.lv===1){
    N3.forEach(function(n){ if(N2[n.p].p!==state.sel.ix) return;
      for(var d4 in n.dbs){ if(state.db>=0 && +d4!==state.db) continue;
        var v4=n.dbs[d4].euro; list.push([n.a0,n.a1,+d4,v4]); if(v4>maxW) maxW=v4; }
    });
  } else {
    return;
  }
  var alpha = state.links==='all' ? 0.10 : 0.42;
  list.sort(function(a,b){ return a[3]-b[3]; });
  ctx.save();
  for(var i=0;i<list.length;i++){
    var o=list[i], a0=o[0], a1=o[1], dnode=ND[o[2]], v=o[3];
    var x0=Math.cos(a0)*r3o, y0=Math.sin(a0)*r3o;
    var x1=Math.cos(a1)*r3o, y1=Math.sin(a1)*r3o;
    var b0=dnode.a0, b1=dnode.a1;
    var x2=Math.cos(b0)*r4i, y2=Math.sin(b0)*r4i;
    var x3=Math.cos(b1)*r4i, y3=Math.sin(b1)*r4i;
    var cm0=(a0+b0)/2, cm1=(a1+b1)/2, rr=(r3o+r4i)/2*0.86;
    var c0x=Math.cos(cm0)*rr, c0y=Math.sin(cm0)*rr;
    var c1x=Math.cos(cm1)*rr, c1y=Math.sin(cm1)*rr;
    ctx.beginPath();
    ctx.moveTo(x0,y0); ctx.lineTo(x1,y1);
    ctx.quadraticCurveTo(c1x,c1y,x3,y3);
    ctx.lineTo(x2,y2);
    ctx.quadraticCurveTo(c0x,c0y,x0,y0);
    ctx.closePath();
    var w = maxW>0 ? v/maxW : 0.5;
    ctx.fillStyle='rgba(192,85,45,'+(alpha*(0.30+0.70*w)).toFixed(3)+')';
    ctx.fill();
  }
  ctx.restore();
}

/* ================= hit testing ================= */
function polar(mx,my){
  var x=(mx-W/2-view.tx)/view.s, y=(my-H/2-view.ty)/view.s;
  var r=Math.sqrt(x*x+y*y);
  var a=Math.atan2(y,x);
  if(a<-Math.PI/2) a+=2*Math.PI;
  return {r:r, a:a, x:x, y:y};
}
function findArc(a, arr, lo, hi){
  for(var i=0;i<arr.length;i++){
    var n=arr[i];
    if(n.a0==null) continue;
    if(a>=n.a0 && a<=n.a1) return n;
  }
  return null;
}
function findDB(a){
  for(var i=0;i<ND.length;i++){ if(a>=ND[i].a0 && a<=ND[i].a1) return ND[i]; }
  return null;
}
function hit(mx,my){
  var p=polar(mx,my), f=p.r/R;
  if(f<=RING.c[1])   return {lv:0, ix:-1};
  if(f>=RING.l1[0] && f<=RING.l1[1] && !state.hiddenAll){
    return wrapNode(findArc(p.a, N1), 1); }
  if(f>=RING.l2[0] && f<=RING.l2[1]) return wrapNode(findArc(p.a, N2), 2);
  if(f>=RING.l3[0] && f<=RING.l3[1]) return wrapNode(findArc(p.a, N3), 3);
  if(f>=RING.db[0] && f<=RING.db[1]) return wrapNode(findDB(p.a), 4);
  return null;
}
function wrapNode(n, lv){ if(!n) return null; return {lv:lv, ix:n.ix}; }

/* ================= tooltip ================= */
var tip=document.getElementById('tip');
function showTip(mx,my,sel){
  var n=nodeOf(sel);
  var rows=[];
  rows.push('<b>'+esc(nameOf(sel))+'</b>');
  if(sel.lv!==1) rows.push('<span class="r">'+esc(pathOf(sel))+'</span>');
  rows.push('Parts billed <b>'+eur(n.euro)+'</b>');
  rows.push('Step at this revision '+eur(n.step));
  rows.push('Weighted move '+pct(n.pct)+'  ('+num(n.priced)+' of '+num(n.n)+' lines priced)');
  if(sel.lv!==4) rows.push('Part numbers '+num(n.npn)+'  \u00b7  units '+num(n.qty));
  if(sel.lv===3){
    var dbs=Object.keys(n.dbs).length;
    rows.push('Billed in '+dbs+' of '+ND.length+' markets');
  }
  if(sel.lv===0) rows.push('Whole in-scope book, all 22 distributors');
  tip.innerHTML=rows.join('<br>');
  tip.style.display='block';
  var tw=tip.offsetWidth, th=tip.offsetHeight;
  tip.style.left=Math.min(window.innerWidth-tw-10, mx+16)+'px';
  tip.style.top=Math.max(8, Math.min(window.innerHeight-th-10, my+16))+'px';
}
function hideTip(){ tip.style.display='none'; }

/* ================= detail panel ================= */
function rowsFor(sel){
  var out=[], i;
  if(!sel){ for(i=0;i<ROWS.length;i++) out.push(ROWS[i]); return out; }
  if(sel.lv===1){ for(i=0;i<ROWS.length;i++) if(ROWS[i][1]===sel.ix) out.push(ROWS[i]); }
  else if(sel.lv===2){ for(i=0;i<ROWS.length;i++) if(ROWS[i][2]===sel.ix) out.push(ROWS[i]); }
  else if(sel.lv===3){ for(i=0;i<ROWS.length;i++) if(ROWS[i][3]===sel.ix) out.push(ROWS[i]); }
  else { for(i=0;i<ROWS.length;i++) if(ROWS[i][4]===sel.ix) out.push(ROWS[i]); }
  return out;
}
function detail(sel){
  var n=nodeOf(sel), rs=rowsFor(sel);
  var isBook = !sel || sel.lv===0;
  document.getElementById('d-head').textContent = isBook ? 'The whole book' : nameOf(sel);
  document.getElementById('d-crumb').innerHTML = esc(pathOf(sel))+' &middot; '+num(n.npn)
    +' part numbers';
  var unp=0, unpEur=0, priced=0;
  for(var i=0;i<rs.length;i++){ if(rs[i][11]) priced++; else { unp++; unpEur+=rs[i][6]; } }
  var q = isBook
    ? 'Everything billed in the window across all 22 distributors. Click any wedge to narrow it.'
    : (sel.lv===4
      ? 'One market. The euro here is what this distributor was billed in the window.'
      : 'A category spans everything under it, so this is the whole branch, not a single leaf.');
  document.getElementById('d-q').textContent=q;
  var parentShare = '';
  if(!isBook){
    if(sel.lv===1) parentShare='100% of the book';
    else if(sel.lv===2) parentShare=pc(n.euro/N1[N2[sel.ix].p].euro)+' of '+L1N[N2[sel.ix].p];
    else if(sel.lv===3) parentShare=pc(n.euro/N2[N3[sel.ix].p].euro)+' of '+L2N[N3[sel.ix].p][1];
    else parentShare='100% of the book';
  }
  document.getElementById('d-facts').innerHTML =
    fact('Parts billed', eur(n.euro), isBook?'the whole in-scope book':parentShare)
    + fact('Step at this revision', eur(n.step), pc(n.ratio)+' of its billed euro')
    + fact('Weighted move', pct(n.pct), num(n.priced)+' of '+num(n.n)+' lines priced')
    + fact('Part numbers', num(n.npn), pc(n.euro/ALL.euro)+' of the book by euro')
    + fact('Units billed', num(n.qty), 'the pieces, not a finding on their own')
    + fact('Cannot move', eur(unpEur), num(unp)+' lines with no price one side');
  /* distributors */
  var byD={};
  for(i=0;i<rs.length;i++){
    var d=byD[rs[i][4]] || (byD[rs[i][4]]={euro:0,step:0,prior:0,new:0,qty:0,priced:0,n:0,pn:{}});
    d.euro+=rs[i][6]; d.step+=rs[i][7]; d.prior+=rs[i][8]; d.new+=rs[i][9];
    d.qty+=rs[i][5]; d.priced+=rs[i][11]?1:0; d.n++; d.pn[rs[i][0]]=1;
  }
  var dl=Object.keys(byD).map(function(k){ var v=byD[k]; v.ix=+k;
    v.pct=v.prior>0&&v.priced>0?100*(v.new/v.prior-1):null; return v; })
    .sort(function(a,b){ return (sel&&sel.lv===4)? b.euro-a.euro : b.euro-a.euro; });
  document.querySelector('#d-dist thead').innerHTML =
    '<tr><th>Distributor</th><th class="n">Parts billed</th><th class="n">Share</th>'
    +'<th class="n">Step</th><th class="n">Weighted</th><th class="n">Part numbers</th></tr>';
  document.querySelector('#d-dist tbody').innerHTML = dl.length ? dl.map(function(v){
    return '<tr><td>'+esc(DBN[v.ix])+'</td><td class="n">'+eur(v.euro)+'</td>'
      +'<td class="n">'+pc(v.euro/n.euro)+'</td><td class="n">'+eur(v.step)+'</td>'
      +'<td class="n">'+pct(v.pct)+'</td><td class="n">'+num(Object.keys(v.pn).length)
      +'</td></tr>'; }).join('')
    : '<tr><td class="muted" colspan="6">No rows for this selection.</td></tr>';
  document.getElementById('d-distq').textContent = sel && sel.lv===3
    ? 'The markets that bill this part type. A market missing from this list genuinely does not bill it.'
    : 'The markets that carry the selected node, by parts billed euro.';
  /* part numbers */
  var byP={};
  for(i=0;i<rs.length;i++){
    var p=byP[rs[i][0]] || (byP[rs[i][0]]={euro:0,step:0,prior:0,new:0,qty:0,priced:0});
    p.euro+=rs[i][6]; p.step+=rs[i][7]; p.prior+=rs[i][8]; p.new+=rs[i][9];
    p.qty+=rs[i][5]; p.priced+=rs[i][11]?1:0;
  }
  var pl=Object.keys(byP).map(function(k){ var v=byP[k]; v.pn=+k;
    v.pct=v.prior>0&&v.priced>0?100*(v.new/v.prior-1):null; return v; })
    .sort(function(a,b){ return b.euro-a.euro; }).slice(0,60);
  document.querySelector('#d-pn thead').innerHTML =
    '<tr><th>Part number</th><th>Description</th><th class="n">Units</th>'
    +'<th class="n">Parts billed</th><th class="n">Step</th><th class="n">Weighted</th></tr>';
  document.querySelector('#d-pn tbody').innerHTML = pl.length ? pl.map(function(v){
    return '<tr><td>'+esc(PN[v.pn])+'</td><td>'+esc(DESC[v.pn]||'\u2014')+'</td>'
      +'<td class="n">'+num(v.qty)+'</td><td class="n">'+eur(v.euro)+'</td>'
      +'<td class="n">'+eur(v.step)+'</td><td class="n">'+pct(v.pct)+'</td></tr>'; }).join('')
    : '<tr><td class="muted" colspan="6">No part numbers in this selection.</td></tr>';
  document.getElementById('d-pnq').textContent = pl.length>60
    ? 'The 60 biggest of '+num(Object.keys(byP).length)+' part numbers in the selection, by parts billed euro.'
    : 'The biggest lines in the selection, by parts billed euro. A part number on its own is a '
      + 'quantity, so the description and the move sit beside it.';
  drawShare();
}
function fact(l,v,n){ return '<div class="fact"><div class="l">'+esc(l)+'</div><div class="v">'
  +v+'</div><div class="n">'+esc(n||'')+'</div></div>'; }

function drawShare(){
  var html='';
  function row(lab, v, cls){
    return '<tr><td class="'+cls+'">'+lab+'</td><td class="n">'+eur(v.euro)+'</td>'
      +'<td class="n">'+pc(v.euro/ALL.euro)+'</td><td class="n">'+pct(v.pct)+'</td>'
      +'<td class="n">'+num(v.npn)+'</td></tr>';
  }
  html+='<tr><td colspan="5" style="background:#eef3f9;font-weight:600">AIM category</td></tr>';
  N1.slice().sort(function(a,b){return b.euro-a.euro;}).forEach(function(n){
    html+=row(esc(n.name), n, ''); });
  html+='<tr><td colspan="5" style="background:#eef3f9;font-weight:600">The ten biggest groups</td></tr>';
  N2.slice().sort(function(a,b){return b.euro-a.euro;}).slice(0,10).forEach(function(n){
    html+=row('&nbsp;&nbsp;'+esc(L1N[n.p])+' \u203a '+esc(n.name), n, ''); });
  html+='<tr><td colspan="5" style="background:#eef3f9;font-weight:600">The ten biggest part types</td></tr>';
  N3.slice().sort(function(a,b){return b.euro-a.euro;}).slice(0,10).forEach(function(n){
    html+=row('&nbsp;&nbsp;'+esc(N2[n.p].name)+' \u203a '+esc(n.name), n, ''); });
  html+='<tr><td colspan="5" style="background:#eef3f9;font-weight:600">The markets</td></tr>';
  ND.slice().sort(function(a,b){return b.euro-a.euro;}).forEach(function(n){
    html+=row('&nbsp;&nbsp;'+esc(n.name), n, ''); });
  document.querySelector('#d-share thead').innerHTML =
    '<tr><th>Ring</th><th class="n">Parts billed</th><th class="n">Share of the book</th>'
    +'<th class="n">Weighted</th><th class="n">Part numbers</th></tr>';
  document.querySelector('#d-share tbody').innerHTML=html;
}

/* ================= legend ================= */
function buildLegend(){
  var el=document.getElementById('legend');
  el.innerHTML = N1.map(function(n){
    return '<span class="lg'+(state.hidden[n.ix]?' off':'')+'" data-i="'+n.ix+'">'
      +'<span class="sw" style="background:'+catColour(n.ix)+'"></span>'+esc(n.name)
      +'<span class="n">'+eurM(n.euro)+'</span></span>'; }).join('')
    + '<span class="lg" style="cursor:default;border-style:dashed">Click a colour to hide that '
    + 'category from the map</span>';
  Array.prototype.forEach.call(el.querySelectorAll('.lg[data-i]'),function(b){
    b.addEventListener('click',function(){
      var i=+b.getAttribute('data-i');
      state.hidden[i]=!state.hidden[i];
      if(state.sel && state.sel.lv!==4){
        /* keep the selection honest: clear it if its category was just hidden */
        var cat = state.sel.lv===1?state.sel.ix
          : state.sel.lv===2?N2[state.sel.ix].p : N2[N3[state.sel.ix].p].p;
        if(state.hidden[cat]){ state.sel=null; detail(null); }
      }
      buildLegend(); draw();
    });
  });
}

/* ================= controls ================= */
function fillControls(){
  var sel=document.getElementById('db');
  sel.innerHTML='<option value="-1">All 22 distributors</option>'
    + DBN.map(function(d,i){ return '<option value="'+i+'">'+esc(d)+'</option>'; }).join('');
  sel.addEventListener('change',function(){ state.db=parseInt(sel.value,10); draw(); });
  Array.prototype.forEach.call(document.querySelectorAll('#mode button'),function(b){
    b.addEventListener('click',function(){
      Array.prototype.forEach.call(document.querySelectorAll('#mode button'),
        function(x){x.classList.remove('on');});
      b.classList.add('on'); state.mode=b.getAttribute('data-m'); draw(); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('#links button'),function(b){
    b.addEventListener('click',function(){
      Array.prototype.forEach.call(document.querySelectorAll('#links button'),
        function(x){x.classList.remove('on');});
      b.classList.add('on'); state.links=b.getAttribute('data-l'); draw(); });
  });
  document.getElementById('reset').addEventListener('click',function(){
    state.sel=null; state.hidden={}; view={s:1,tx:0,ty:0};
    buildLegend(); detail(null); draw(); });
  wireSearch();
}

/* ---------- search ---------- */
function wireSearch(){
  var box=document.getElementById('q'), list=document.getElementById('hitlist');
  function show(){
    var s=box.value.trim().toLowerCase();
    if(s.length<2){ list.style.display='none'; list.innerHTML=''; return; }
    var out=[], i;
    for(i=0;i<N1.length;i++) if(N1[i].name.toLowerCase().indexOf(s)>=0)
      out.push({t:N1[i].name,k:'category \u00b7 '+eurM(N1[i].euro),lv:1,ix:i});
    for(i=0;i<N2.length;i++) if(N2[i].name.toLowerCase().indexOf(s)>=0)
      out.push({t:N2[i].name,k:'group \u2014 '+L1N[N2[i].p]+' \u00b7 '+eurM(N2[i].euro),lv:2,ix:i});
    for(i=0;i<N3.length;i++) if(N3[i].name.toLowerCase().indexOf(s)>=0)
      out.push({t:N3[i].name,k:'part type \u2014 '+N2[N3[i].p].name+' \u00b7 '+eurM(N3[i].euro),
        lv:3,ix:i});
    for(i=0;i<DBN.length;i++) if(DBN[i].toLowerCase().indexOf(s)>=0)
      out.push({t:DBN[i],k:'distributor \u00b7 '+eurM(ND[i].euro),lv:4,ix:i});
    if(out.length<8){
      var hits=0;
      for(i=0;i<PN.length && hits<10;i++){
        if(PN[i].indexOf(s)>=0){
          var leaf=null, j;
          for(j=0;j<ROWS.length;j++) if(ROWS[j][0]===i){ leaf=ROWS[j][3]; break; }
          if(leaf!=null) out.push({t:PN[i],k:'part number \u2014 '+(DESC[i]||''),lv:3,ix:leaf,pn:i});
          hits++;
        }
      }
    }
    out=out.slice(0,24);
    if(!out.length){ list.innerHTML='<div class="muted">Nothing matches that.</div>';
      list.style.display='block'; return; }
    list.innerHTML=out.map(function(o,i){
      return '<div data-i="'+i+'"><b>'+esc(o.t)+'</b><span class="k">'+esc(o.k)+'</span></div>'; })
      .join('');
    list.style.display='block';
    Array.prototype.forEach.call(list.querySelectorAll('div[data-i]'),function(d){
      d.addEventListener('click',function(){ jump(out[+d.getAttribute('data-i')]); }); });
  }
  function jump(o){
    list.style.display='none'; box.value=o.t;
    state.hidden={};
    state.sel={lv:o.lv, ix:o.ix};
    buildLegend(); detail(state.sel); draw();
    if(o.pn!=null){ highlightPn(o.pn); }
  }
  function highlightPn(pnIx){
    var rows=document.querySelectorAll('#d-pn tbody tr');
    Array.prototype.forEach.call(rows,function(tr){
      if(tr.firstChild && tr.firstChild.textContent===PN[pnIx]){
        tr.style.background='#f6e3da';
        var w=document.querySelector('#d-pn').parentNode;
        w.scrollTop=tr.offsetTop-w.clientHeight/2;
      }
    });
  }
  box.addEventListener('input',show);
  box.addEventListener('focus',show);
  document.addEventListener('click',function(e){
    if(!document.getElementById('hits').contains(e.target)) list.style.display='none'; });
}

/* ---------- mouse ---------- */
cv.addEventListener('mousemove', function(e){
  var mx=e.clientX-cv.getBoundingClientRect().left;
  var my=e.clientY-cv.getBoundingClientRect().top;
  var h=hit(mx,my);
  if(h && h.lv>0){
    state.hover=h; showTip(e.clientX,e.clientY,h); cv.style.cursor='pointer';
  } else if(h && h.lv===0){
    state.hover={lv:0,ix:-1}; showTip(e.clientX,e.clientY,{lv:0,ix:-1}); cv.style.cursor='pointer';
  } else { state.hover=null; hideTip(); cv.style.cursor='crosshair'; }
});
cv.addEventListener('mouseleave', function(){ hideTip(); state.hover=null; });
cv.addEventListener('click', function(e){
  var mx=e.clientX-cv.getBoundingClientRect().left;
  var my=e.clientY-cv.getBoundingClientRect().top;
  var h=hit(mx,my);
  if(!h){ state.sel=null; } else if(h.lv===0){ state.sel=null; }
  else { state.sel=h; }
  detail(state.sel); draw();
});
var drag=null;
cv.addEventListener('mousedown', function(e){
  drag={x:e.clientX, y:e.clientY, tx:view.tx, ty:view.ty, moved:false};
});
window.addEventListener('mousemove', function(e){
  if(!drag) return;
  var dx=e.clientX-drag.x, dy=e.clientY-drag.y;
  if(Math.abs(dx)+Math.abs(dy)>3) drag.moved=true;
  view.tx=drag.tx+dx; view.ty=drag.ty+dy; draw();
});
window.addEventListener('mouseup', function(){ drag=null; });
cv.addEventListener('wheel', function(e){
  e.preventDefault();
  var f = e.deltaY<0 ? 1.12 : 1/1.12;
  view.s=Math.max(0.55, Math.min(4.5, view.s*f));
  draw();
}, {passive:false});
cv.addEventListener('dblclick', function(){ view={s:1,tx:0,ty:0}; draw(); });
window.addEventListener('keydown', function(e){
  if(e.key==='+'||e.key==='='){ view.s=Math.min(4.5, view.s*1.15); draw(); }
  if(e.key==='-'||e.key==='_'){ view.s=Math.max(0.55, view.s/1.15); draw(); }
  if(e.key==='0'){ view={s:1,tx:0,ty:0}; draw(); }
});

/* ================= boot ================= */
function boot(){
  var rep=M.repertoire;
  document.getElementById('w-tree').textContent=num(rep.tree_part_numbers);
  document.getElementById('w-billed').textContent=num(rep.billed_in_tree);
  document.getElementById('w-silent').textContent=num(rep.classified_not_billed);
  document.getElementById('genline').textContent=' Built '+M.built.slice(0,10)+'.';
  fillControls();
  buildLegend();
  detail(null);
  resize();
}
window.__spiderReady=false;
window.spiderState=state;
window.spiderNodes={N1:N1,N2:N2,N3:N3,ND:ND,ALL:ALL};
window.spiderHit=hit;
window.spiderDetail=detail;
boot();
window.__spiderReady=true;
})();
</script>
</body>
</html>
"""


def main() -> int:
    payload = (BUILD / "payload.json").read_text(encoding="utf-8")
    html = HTML.replace("__PAYLOAD__", payload)
    OUT.write_text(html, encoding="utf-8")
    size = OUT.stat().st_size
    print(f"payload  {len(payload)/1024:,.0f} KB")
    print(f"-> {OUT}  ({size/1024/1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
