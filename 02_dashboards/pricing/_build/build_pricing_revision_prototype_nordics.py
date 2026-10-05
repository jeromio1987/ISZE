#!/usr/bin/env python3
"""Build the Nordics-customer PROTOTYPE for the AIM price-revision page.

Separate file from the original pack. Primary control is a sold-to customer
dropdown scoped to the Nordics accounts (Sweden, Norway, Finland, BL Iceland),
plus an All-Nordics roll-up. The AIM L1 → L2 → L3 path is a zoom stage
(focus chart + sibling chips), not a photocopy of the original layout.

Run: python 02_dashboards/pricing/_build/build_pricing_revision_prototype_nordics.py
"""
from __future__ import annotations

import json
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BUILD = ISZE / "02_dashboards" / "pricing" / "_build"
DATA = BUILD / "pricing_dashboard_data.json"
CHART = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html"
OPEN = ISZE / "02_dashboards" / "pricing" / "OPEN_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.cmd"

# Nordics sold-tos Jerome named: Sweden, Norway, Finland, Iceland / BL Iceland.
# Matched on distributor label in the cube (not a fake country filter).
NORDICS_DB_LABELS = ("Sverige", "Norway", "Nordic FI", "BL Iceland")
NORDICS_MARKET = {
    "Sverige": "Sweden",
    "Norway": "Norway",
    "Nordic FI": "Finland",
    "BL Iceland": "Iceland",
}

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Price revision — Nordics customers (prototype)</title>
<style>
:root{
  --navy:#15233c; --navy2:#1d3054; --terra:#c0552d; --paper:#f7f4ee;
  --ink:#22262e; --muted:#6b6459; --line:#d9d3c8; --band:#eef3f9;
  --good:#1e6b4f; --amber:#a8721f;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:14px;line-height:1.5}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}
h1{font-size:26px;letter-spacing:-.2px}
h2{font-size:18px;margin-bottom:2px}
.wrap{max-width:1280px;margin:0 auto;padding:22px 22px 60px}
header.top{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:18px}
.sub{color:var(--muted);font-size:13px;margin-top:6px}
.badge{display:inline-block;background:var(--navy);color:var(--paper);
  font-size:11px;letter-spacing:.6px;text-transform:uppercase;
  padding:3px 9px;border-radius:2px;margin-right:8px}
.badge.proto{background:var(--terra)}

.controls{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;
  background:#fff;border:1px solid var(--line);border-left:4px solid var(--terra);
  padding:14px 16px;margin-bottom:18px}
.ctrl{display:flex;flex-direction:column;gap:5px}
.ctrl label{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted)}
select{font-size:14px;padding:7px 10px;border:1px solid var(--line);background:#fff;
  color:var(--ink);border-radius:2px;min-width:280px}
select:focus{outline:2px solid var(--terra);outline-offset:-1px}
.seg{display:flex;border:1px solid var(--line);border-radius:2px;overflow:hidden}
.seg button{background:#fff;border:0;border-right:1px solid var(--line);
  padding:7px 13px;font-size:13px;cursor:pointer;color:var(--ink)}
.seg button:last-child{border-right:0}
.seg button.on{background:var(--navy);color:var(--paper)}
.reset{background:#fff;border:1px solid var(--line);padding:7px 13px;font-size:13px;
  cursor:pointer;color:var(--terra);border-radius:2px}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));
  gap:12px;margin-bottom:18px}
.kpi{background:#fff;border:1px solid var(--line);padding:13px 15px;position:relative;
  border-top:3px solid var(--navy)}
.kpi .lab{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);
  display:flex;align-items:center;gap:5px}
.kpi .val{font-size:22px;font-weight:600;color:var(--navy);margin-top:5px;
  font-variant-numeric:tabular-nums}
.kpi .note{font-size:11.5px;color:var(--muted);margin-top:3px}
.kpi.t{border-top-color:var(--terra)}
.info{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;
  border-radius:50%;background:var(--navy);color:#fff;font-size:9.5px;cursor:help;
  position:relative;flex:0 0 auto}
.info .tip{display:none;position:absolute;bottom:22px;left:50%;transform:translateX(-50%);
  width:260px;background:var(--navy);color:var(--paper);font-size:12px;line-height:1.45;
  padding:9px 11px;border-radius:3px;z-index:60;text-transform:none;letter-spacing:0;
  font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25)}
.info:hover .tip,.info:focus .tip{display:block}

.warn{background:#fdf3e3;border:1px solid #e6cf9f;border-left:4px solid var(--amber);
  padding:11px 14px;font-size:12.5px;color:#5e4a1c;margin-bottom:18px}
.proto-note{background:#fff;border:1px solid var(--line);border-left:4px solid var(--navy);
  padding:11px 14px;font-size:12.5px;margin-bottom:18px}

.zoom{display:grid;grid-template-columns:210px 1fr;gap:16px;margin-bottom:18px}
@media(max-width:900px){.zoom{grid-template-columns:1fr}}
.rail{background:#fff;border:1px solid var(--line);padding:12px}
.rail h3{font-size:12px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);
  font-family:inherit;font-weight:600;margin-bottom:8px}
.chip{display:block;width:100%;text-align:left;border:1px solid var(--line);
  background:var(--paper);padding:8px 10px;margin-bottom:6px;cursor:pointer;
  border-radius:2px;font-size:12.5px;color:var(--ink)}
.chip:hover{border-color:var(--terra)}
.chip.on{background:var(--navy);color:var(--paper);border-color:var(--navy)}
.chip .meta{display:block;font-size:11px;opacity:.8;margin-top:2px}
.stage{background:#fff;border:1px solid var(--line);padding:15px 16px 12px}
.stage .q{font-size:13.5px;color:var(--muted);margin:4px 0 12px}
.chartbox{position:relative;height:420px}
.crumb{font-size:13px;color:var(--muted);margin-bottom:10px}
.crumb span{cursor:pointer;color:var(--terra);text-decoration:underline}
.crumb b{color:var(--navy)}
.depth{display:flex;gap:6px;margin-bottom:10px}
.depth .d{font-size:11px;padding:3px 9px;border:1px solid var(--line);border-radius:10px;
  color:var(--muted);background:var(--paper)}
.depth .d.on{background:var(--terra);color:#fff;border-color:var(--terra)}

.compare{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}
@media(max-width:900px){.compare{grid-template-columns:1fr 1fr}}
.cmini{background:#fff;border:1px solid var(--line);padding:12px;cursor:pointer}
.cmini:hover,.cmini.on{border-color:var(--terra);box-shadow:inset 3px 0 0 var(--terra)}
.cmini .mkt{font-size:11px;letter-spacing:.5px;text-transform:uppercase;color:var(--muted)}
.cmini .name{font-size:13px;color:var(--navy);font-weight:600;margin-top:2px}
.cmini .pct{font-size:20px;font-weight:600;color:var(--terra);margin-top:6px;
  font-variant-numeric:tabular-nums}
.cmini .eur{font-size:12px;color:var(--muted);margin-top:2px}

.card{background:#fff;border:1px solid var(--line);padding:15px 16px 12px;margin-bottom:18px}
.card .q{font-size:13.5px;color:var(--muted);margin:2px 0 12px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;
  font-weight:600;font-size:11.5px;letter-spacing:.4px;text-transform:uppercase;
  position:sticky;top:0}
th.n,td.n{text-align:right;font-variant-numeric:tabular-nums}
td{padding:6px 9px;border-bottom:1px solid var(--line)}
tbody tr:nth-child(even){background:var(--band)}
tbody tr:hover{background:#e3ecf6}
tbody tr.clickable{cursor:pointer}
tbody tr.sel{background:#f6e3da!important;box-shadow:inset 3px 0 0 var(--terra)}
.tblwrap{max-height:380px;overflow:auto;border:1px solid var(--line)}
.muted{color:var(--muted)}
.foot{font-size:12px;color:var(--muted);border-top:1px solid var(--line);
  padding-top:12px;margin-top:24px}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div>
    <span class="badge">Price revision</span>
    <span class="badge proto">Prototype — Nordics customers</span>
    <span class="badge">Internal</span>
  </div>
  <h1 style="margin-top:9px">Nordics accounts — where the revision lands</h1>
  <div class="sub">Pick a Nordics sold-to (or all four together), then zoom AIM level 1 → level 2 →
    level 3. This is a separate prototype from the network pack. Parts billed 1 July 2025 to
    30 June 2026. Opens from Explorer with no server.
    <span id="genline"></span></div>
</header>

<div class="proto-note">
  <b>What is different here.</b> The original pack stays network-first. This page starts from the
  Nordics sold-to accounts (Sweden, Norway, Finland, BL Iceland) and puts the AIM zoom on a large
  stage with a sibling list beside it — so you can step in and out of families without losing
  context. It is not a country filter pretending to be a distributor group.
</div>

<div class="warn">
  <b>What the headline is.</b> The percentage is a base-price move: the euro increase against the
  prior base price, weighted by quantities billed. Not revenue, margin or elasticity.
</div>

<div class="controls">
  <div class="ctrl">
    <label for="cust">Nordics customer (sold-to)</label>
    <select id="cust"></select>
  </div>
  <div class="ctrl">
    <label for="src">Source of supply</label>
    <select id="src"></select>
  </div>
  <div class="ctrl">
    <label>Chart measure</label>
    <div class="seg" id="meas">
      <button data-m="billed" class="on">Parts billed EUR</button>
      <button data-m="step">Step EUR</button>
      <button data-m="pct">Weighted %</button>
    </div>
  </div>
  <div class="ctrl">
    <label>&nbsp;</label>
    <button class="reset" id="reset">Back to all Nordics · L1</button>
  </div>
</div>

<div class="kpis" id="kpis"></div>

<div class="compare" id="compare"></div>

<div class="zoom">
  <aside class="rail">
    <h3 id="rail-title">Siblings at this level</h3>
    <div id="rail"></div>
  </aside>
  <div class="stage">
    <div class="depth" id="depth">
      <span class="d on" data-d="1">Level 1</span>
      <span class="d" data-d="2">Level 2</span>
      <span class="d" data-d="3">Level 3</span>
      <span class="d" data-d="4">Part numbers</span>
    </div>
    <div class="crumb" id="crumb"></div>
    <h2 id="t-zoom">AIM families for this slice</h2>
    <div class="q" id="q-zoom">Click a bar or a sibling chip to zoom one level deeper.</div>
    <div class="chartbox"><canvas id="c-zoom"></canvas></div>
  </div>
</div>

<div class="card">
  <h2 id="t-tbl">Detail at the current zoom</h2>
  <div class="q" id="q-tbl">Same grain as the chart. Click a row to zoom in.</div>
  <div class="tblwrap"><table id="detail"><thead></thead><tbody></tbody></table></div>
</div>

<div class="foot" id="foot"></div>
</div>

<script type="application/json" id="payload">__PAYLOAD__</script>
<script type="application/json" id="nordics-meta">__NORDICS__</script>
<script>__CHARTJS__</script>
<script>
(function(){
"use strict";
var D = JSON.parse(document.getElementById('payload').textContent);
var N = JSON.parse(document.getElementById('nordics-meta').textContent);
var P = D.pool;
var NAVY='#15233c', TERRA='#c0552d', BLUE='#3d6098', SAND='#d9a05b', GREY='#9aa2ad';

function fmtEur(v,dec){
  if(v===null||v===undefined||isNaN(v)) return '—';
  var d = (dec===undefined)?0:dec;
  return '€' + Number(v).toLocaleString('en-GB',{minimumFractionDigits:d,maximumFractionDigits:d});
}
function fmtPct(v,dec){
  if(v===null||v===undefined||isNaN(v)) return '—';
  return Number(v).toFixed((dec===undefined)?2:dec) + '%';
}
function fmtNum(v){ return Number(v).toLocaleString('en-GB'); }
function esc(s){ return String(s).replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

/* state.cust: -1 = all Nordics customers; else one sold-to index */
var state = { cust:-1, src:-1, metric:'billed', l1:-1, l2:null, l3:null, other:null };
var charts = {};
function chart(id, cfg){ if(charts[id]) charts[id].destroy(); charts[id] = new Chart(id, cfg); }

function nordicsSet(){
  var s = {};
  N.customers.forEach(function(c){ s[c.ci] = c; });
  return s;
}
function custMeta(ci){ return nordicsSet()[ci]; }
function custLabel(ci){
  var m = custMeta(ci);
  if(!m) return String(ci);
  return m.name + ' (' + m.code + ')';
}
function sliceLabel(){
  if(state.cust >= 0) return custLabel(state.cust);
  return 'all Nordics customers';
}
function inNordicsCust(ci){
  return !!custMeta(ci);
}
function custMatches(ci){
  if(!inNordicsCust(ci)) return false;
  if(state.cust >= 0) return ci === state.cust;
  return true;
}

function rollupL1(){
  var map = {};
  (D.cust_fam||[]).forEach(function(r){
    if(!custMatches(r[0])) return;
    if(state.src>=0 && r[3]!==state.src) return;
    var o = map[r[2]];
    if(!o) o = map[r[2]] = {l1:r[2], pn:0, billed:0, prior:0, new:0, step:0, all:0};
    o.pn+=r[4]; o.billed+=r[5]; o.prior+=r[6]; o.new+=r[7]; o.step+=r[8];
    o.all += (r[9]!==undefined ? r[9] : r[5]);
  });
  return Object.keys(map).map(function(k){
    var o=map[k]; o.pct=o.prior>0?100*(o.new/o.prior-1):null; return o;
  });
}
function rollupL2(l1){
  var map = {};
  (D.cust_l2||[]).forEach(function(r){
    if(!custMatches(r[0])) return;
    if(state.src>=0 && r[3]!==state.src) return;
    if(r[1]!==l1) return;
    var o = map[r[2]];
    if(!o) o = map[r[2]] = {l1:r[1], l2:r[2], pn:0, rows:0, qty:0, billed:0, prior:0, new:0, step:0, all:0};
    o.pn+=r[4]; o.rows+=r[5]; o.qty+=r[6]; o.billed+=r[7];
    o.prior+=r[8]; o.new+=r[9]; o.step+=r[10]; o.all+=r[11];
  });
  return Object.keys(map).map(function(k){
    var o=map[k]; o.pct=o.prior>0?100*(o.new/o.prior-1):null; return o;
  });
}
function rollupL3(l1, l2){
  var map = {};
  (D.cust_l3||[]).forEach(function(r){
    if(!custMatches(r[0])) return;
    if(state.src>=0 && r[4]!==state.src) return;
    if(r[1]!==l1) return;
    if(l2 === -1){
      if(!state.other || state.other.indexOf(r[2])<0) return;
    } else if(r[2]!==l2) return;
    var o = map[r[3]];
    if(!o) o = map[r[3]] = {l1:r[1], l2:r[2], l3:r[3], pn:0, rows:0, qty:0, billed:0, prior:0, new:0, step:0, all:0};
    o.pn+=r[5]; o.rows+=r[6]; o.qty+=r[7]; o.billed+=r[8];
    o.prior+=r[9]; o.new+=r[10]; o.step+=r[11]; o.all+=r[12];
  });
  return Object.keys(map).map(function(k){
    var o=map[k]; o.pct=o.prior>0?100*(o.new/o.prior-1):null; return o;
  });
}
function rollupPn(){
  var map = {};
  var allowL2 = null;
  if(state.l2 === -1){
    allowL2 = {};
    (state.other||[]).forEach(function(x){ allowL2[x]=true; });
  }
  (D.cust_pn||[]).forEach(function(r){
    if(!custMatches(r[0])) return;
    if(r[1]!==state.l1) return;
    if(state.l2 === -1){ if(!allowL2[r[2]]) return; }
    else if(r[2]!==state.l2) return;
    if(r[3]!==state.l3) return;
    var o = map[r[4]];
    if(!o) o = map[r[4]] = {pn:r[4], qty:0, billed:0, prior:0, new:0, step:0};
    o.qty+=r[5]; o.billed+=r[6]; o.prior+=r[7]; o.new+=r[8]; o.step+=r[9];
  });
  return Object.keys(map).map(function(k){
    var o=map[k]; o.pct=o.prior>0?100*(o.new/o.prior-1):null; return o;
  });
}
function totalsNow(){
  var t = {pn:0,rows:0,qty:0,billed:0,prior:0,new:0,step:0,all:0};
  D.customers.forEach(function(r){
    if(!custMatches(r[0])) return;
    if(state.src>=0 && r[3]!==state.src) return;
    t.pn+=r[4]; t.rows+=r[5]; t.qty+=r[6]; t.billed+=r[7];
    t.prior+=r[8]; t.new+=r[9]; t.step+=r[10]; t.all+=r[11];
  });
  t.pct = t.prior>0 ? 100*(t.new/t.prior-1) : null;
  return t;
}
function metricOf(o){
  return state.metric==='pct' ? o.pct : (state.metric==='step' ? o.step : o.all);
}
function fmtMetric(v){ return state.metric==='pct' ? fmtPct(v) : fmtEur(v); }
function depth(){
  if(state.l1 < 0) return 1;
  if(state.l2 === null || state.l2 === undefined) return 2;
  if(state.l3 === null || state.l3 === undefined) return 3;
  return 4;
}

function kpis(t){
  var scope = sliceLabel() + (state.src<0? '' : ' / ' + P.src[state.src]);
  document.getElementById('kpis').innerHTML =
    '<div class="kpi t"><div class="lab">Weighted increase'
    +'<span class="info" tabindex="0">i<span class="tip">Sum of (units × new base) / sum of (units × prior base) − 1. '
    +'Priced lines only. No elasticity.</span></span></div>'
    +'<div class="val">'+fmtPct(t.pct)+'</div><div class="note">'+esc(scope)+'</div></div>'
    +'<div class="kpi"><div class="lab">Step euro'
    +'<span class="info" tabindex="0">i<span class="tip">Units × (new − prior base), at '
    +D.fx+' JPY per EUR.</span></span></div>'
    +'<div class="val">'+fmtEur(t.step)+'</div>'
    +'<div class="note">'+fmtNum(t.rows)+' in-scope lines</div></div>'
    +'<div class="kpi"><div class="lab">Parts billed (in scope)'
    +'<span class="info" tabindex="0">i<span class="tip">Every in-scope line for this Nordics slice, priced or not.</span></span></div>'
    +'<div class="val">'+fmtEur(t.all)+'</div>'
    +'<div class="note">'+fmtNum(t.pn)+' part numbers</div></div>'
    +'<div class="kpi"><div class="lab">Step per €1m billed'
    +'<span class="info" tabindex="0">i<span class="tip">Step euro ÷ parts billed × 1,000,000.</span></span></div>'
    +'<div class="val">'+(t.all>0?fmtEur(1e6*t.step/t.all):'—')+'</div>'
    +'<div class="note">rise per million billed</div></div>';
}

function drawCompare(){
  var el = document.getElementById('compare');
  el.innerHTML = N.customers.map(function(c){
    var t = {prior:0,new:0,step:0,all:0};
    D.customers.forEach(function(r){
      if(r[0]!==c.ci) return;
      if(state.src>=0 && r[3]!==state.src) return;
      t.prior+=r[8]; t.new+=r[9]; t.step+=r[10]; t.all+=r[11];
    });
    var pct = t.prior>0 ? 100*(t.new/t.prior-1) : null;
    var on = state.cust === c.ci ? ' on' : '';
    return '<div class="cmini'+on+'" data-ci="'+c.ci+'">'
      +'<div class="mkt">'+esc(c.market)+'</div>'
      +'<div class="name">'+esc(c.name)+'</div>'
      +'<div class="pct">'+(pct===null?'—':fmtPct(pct))+'</div>'
      +'<div class="eur">Step '+fmtEur(t.step)+' · billed '+fmtEur(t.all)+'</div></div>';
  }).join('');
  Array.prototype.forEach.call(el.querySelectorAll('.cmini'), function(card){
    card.addEventListener('click', function(){
      var ci = Number(card.getAttribute('data-ci'));
      if(state.cust === ci) setCust(-1);
      else setCust(ci);
    });
  });
}

function currentRows(){
  var d = depth();
  if(d===1){
    return rollupL1().filter(function(r){ return r.all>0; }).sort(function(a,b){
      var ag=/Not on AIM/.test(P.l1[a.l1])?1:0, bg=/Not on AIM/.test(P.l1[b.l1])?1:0;
      if(ag!==bg) return ag-bg;
      return (metricOf(b)||0)-(metricOf(a)||0);
    });
  }
  if(d===2){
    return rollupL2(state.l1).filter(function(r){
      return r.all>0 && !/Not classified at L3/.test(P.l2[r.l2]);
    }).sort(function(a,b){ return (metricOf(b)||0)-(metricOf(a)||0); });
  }
  if(d===3){
    return rollupL3(state.l1, state.l2).filter(function(r){ return r.all>0; })
      .sort(function(a,b){ return (metricOf(b)||0)-(metricOf(a)||0); });
  }
  return rollupPn().sort(function(a,b){ return (b.step||0)-(a.step||0); });
}

function drawRail(rows){
  var d = depth();
  var title = d===1 ? 'AIM level 1' : (d===2 ? 'Level 2 siblings' : (d===3 ? 'Level 3 siblings' : 'Top part numbers'));
  document.getElementById('rail-title').textContent = title;
  var rail = document.getElementById('rail');
  if(d===4){
    rail.innerHTML = rows.slice(0,18).map(function(r){
      return '<button type="button" class="chip" disabled>'
        +'<span>'+esc(P.pn[r.pn])+'</span>'
        +'<span class="meta">'+fmtEur(r.step)+' step · '+fmtPct(r.pct)+'</span></button>';
    }).join('') || '<div class="muted">No part numbers here.</div>';
    return;
  }
  rail.innerHTML = rows.map(function(r, ix){
    var name = d===1 ? P.l1[r.l1] : (d===2 ? P.l2[r.l2] : P.l3[r.l3]);
    var key = d===1 ? r.l1 : (d===2 ? r.l2 : r.l3);
    var on = (d===1 && state.l1===key) || (d===2 && state.l2===key) || (d===3 && state.l3===key);
    return '<button type="button" class="chip'+(on?' on':'')+'" data-ix="'+ix+'">'
      +'<span>'+esc(name)+'</span>'
      +'<span class="meta">'+fmtMetric(metricOf(r))+' · '+fmtEur(r.all)+' billed</span></button>';
  }).join('') || '<div class="muted">No rows for this slice.</div>';
  Array.prototype.forEach.call(rail.querySelectorAll('button.chip[data-ix]'), function(btn){
    btn.addEventListener('click', function(){
      zoomInto(rows[Number(btn.getAttribute('data-ix'))]);
    });
  });
}

function zoomInto(row){
  var d = depth();
  if(d===1){ state.l1 = row.l1; state.l2 = null; state.l3 = null; state.other = null; }
  else if(d===2){ state.l2 = row.l2; state.l3 = null; }
  else if(d===3){ state.l3 = row.l3; }
  render();
}

function drawCrumb(){
  var parts = ['<span data-step="root"><b>'+esc(sliceLabel())+'</b></span>'];
  if(state.l1>=0) parts.push('<span data-step="l1">'+esc(P.l1[state.l1])+'</span>');
  if(state.l1>=0 && state.l2 === -1) parts.push('<span data-step="l2">All other groups</span>');
  else if(state.l1>=0 && typeof state.l2 === 'number' && state.l2 >= 0)
    parts.push('<span data-step="l2">'+esc(P.l2[state.l2])+'</span>');
  if(typeof state.l2 === 'number' && typeof state.l3 === 'number' && state.l3 >= 0)
    parts.push('<span data-step="l3">'+esc(P.l3[state.l3])+'</span>');
  var el = document.getElementById('crumb');
  el.innerHTML = parts.join(' › ');
  Array.prototype.forEach.call(el.querySelectorAll('span[data-step]'), function(sp){
    sp.addEventListener('click', function(){
      var s = sp.getAttribute('data-step');
      if(s==='root'){ state.l1=-1; state.l2=null; state.l3=null; state.other=null; }
      else if(s==='l1'){ state.l2=null; state.l3=null; state.other=null; }
      else if(s==='l2'){ state.l3=null; }
      render();
    });
  });
  var d = depth();
  Array.prototype.forEach.call(document.querySelectorAll('#depth .d'), function(x){
    x.classList.toggle('on', Number(x.getAttribute('data-d')) === d);
  });
}

function drawZoom(rows){
  var d = depth();
  var canvas = document.getElementById('c-zoom');
  if(d===4){
    document.getElementById('t-zoom').textContent =
      'Part numbers inside ' + P.l3[state.l3];
    document.getElementById('q-zoom').textContent =
      'Largest euro steps on this level-3 type for ' + sliceLabel() + '. Use the breadcrumb to zoom out.';
    var top = rows.slice(0, 20);
    chart('c-zoom', {
      type:'bar',
      data:{ labels: top.map(function(r){ return P.pn[r.pn]; }),
        datasets:[{ data: top.map(function(r){ return r.step; }),
          backgroundColor: TERRA, borderRadius:2, borderSkipped:false }] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{display:false},
          tooltip:{callbacks:{label:function(c){ return fmtEur(c.raw); }}} },
        scales:{
          x:{ beginAtZero:true, grid:{color:'#eceae4'},
              ticks:{callback:function(v){ return fmtEur(v); }, font:{size:11}} },
          y:{ grid:{display:false}, ticks:{font:{size:11}, color:NAVY} } },
        animation:{duration:220} }
    });
    return;
  }

  if(d===2){
    /* Donut focus for L2 — prototype zoom language */
    var head = rows.slice(0,3);
    var rest = rows.slice(3);
    var restE = rest.reduce(function(s,r){ return s+r.all; },0);
    var labels = head.map(function(r){ return P.l2[r.l2]; });
    var vals = head.map(function(r){ return r.all; });
    var keys = head.map(function(r){ return r.l2; });
    if(restE>0){
      labels.push('All other groups'); vals.push(restE); keys.push(-1);
      state.other = rest.map(function(r){ return r.l2; });
    } else state.other = [];
    document.getElementById('t-zoom').textContent =
      'Zoomed into ' + P.l1[state.l1] + ' — level 2';
    document.getElementById('q-zoom').textContent =
      'Top three groups named. Click a segment or a sibling chip to open level 3.';
    chart('c-zoom', {
      type:'doughnut',
      data:{ labels:labels, datasets:[{ data:vals,
        backgroundColor:[NAVY,TERRA,SAND,GREY], borderColor:'#fff', borderWidth:2 }] },
      options:{ responsive:true, maintainAspectRatio:false, cutout:'48%',
        onClick:function(evt, els){
          if(!els||!els.length) return;
          var k = keys[els[0].index];
          state.l2 = k; state.l3 = null; render();
        },
        plugins:{ legend:{position:'bottom', labels:{font:{size:12}, boxWidth:12}},
          tooltip:{callbacks:{label:function(c){
            var tot=c.dataset.data.reduce(function(a,b){return a+b;},0);
            return c.label+': '+fmtEur(c.raw)+' ('+fmtPct(100*c.raw/tot,1)+')';
          }}} } },
      plugins:[{ id:'ctr', afterDraw:function(ch){
        var g=ch.ctx; g.save(); g.textAlign='center'; g.textBaseline='middle';
        var x=(ch.chartArea.left+ch.chartArea.right)/2, y=(ch.chartArea.top+ch.chartArea.bottom)/2-6;
        g.fillStyle=NAVY; g.font='600 18px Georgia,serif';
        g.fillText(fmtEur(vals.reduce(function(a,b){return a+b;},0)), x, y);
        g.fillStyle='#6b6459'; g.font='11px sans-serif';
        g.fillText('parts billed', x, y+18); g.restore();
      }}]
    });
    return;
  }

  var labels = rows.map(function(r){
    return d===1 ? P.l1[r.l1] : P.l3[r.l3];
  });
  var vals = rows.map(metricOf);
  var keys = rows.map(function(r){ return d===1 ? r.l1 : r.l3; });
  document.getElementById('t-zoom').textContent =
    d===1
      ? 'Which AIM families move most for ' + sliceLabel() + '?'
      : 'Level 3 inside ' + (state.l2===-1?'All other groups':P.l2[state.l2]);
  document.getElementById('q-zoom').textContent =
    d===1
      ? 'Large focus chart. Click a bar or a sibling on the left to zoom into level 2.'
      : 'Click a bar to list the part numbers for that type.';
  chart('c-zoom', {
    type:'bar',
    data:{ labels:labels, datasets:[{ data:vals,
      backgroundColor: labels.map(function(l,i){
        if(/Not on AIM/.test(l)) return GREY;
        if(d===3 && state.l3===keys[i]) return TERRA;
        return BLUE;
      }),
      borderRadius:2, borderSkipped:false }] },
    options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
      onClick:function(evt, els){
        if(!els||!els.length) return;
        zoomInto(rows[els[0].index]);
      },
      plugins:{ legend:{display:false},
        tooltip:{callbacks:{label:function(c){ return fmtMetric(c.raw); }}} },
      scales:{
        x:{ beginAtZero:true, grid:{color:'#eceae4'},
            ticks:{callback:function(v){ return state.metric==='pct'?v+'%':fmtEur(v); }, font:{size:11}} },
        y:{ grid:{display:false}, ticks:{font:{size:11.5}, color:NAVY} } },
      animation:{duration:220} }
  });
}

function drawTable(rows){
  var d = depth();
  var thead = document.querySelector('#detail thead');
  var tbody = document.querySelector('#detail tbody');
  if(d===4){
    document.getElementById('t-tbl').textContent = 'Part numbers at this zoom';
    document.getElementById('q-tbl').textContent = 'Sorted by euro step. Breadcrumb zooms back out.';
    thead.innerHTML = '<tr><th>Part number</th><th>Description</th><th class="n">Units</th>'
      +'<th class="n">Parts billed</th><th class="n">Step €</th><th class="n">Weighted</th></tr>';
    tbody.innerHTML = rows.length ? rows.map(function(r){
      return '<tr><td>'+esc(P.pn[r.pn])+'</td><td>'+esc(P.desc[r.pn]||'')+'</td>'
        +'<td class="n">'+fmtNum(Math.round(r.qty))+'</td>'
        +'<td class="n">'+fmtEur(r.billed)+'</td>'
        +'<td class="n">'+fmtEur(r.step)+'</td>'
        +'<td class="n">'+fmtPct(r.pct)+'</td></tr>';
    }).join('') : '<tr><td colspan="6" class="muted">No priced part numbers.</td></tr>';
    return;
  }
  var col = d===1 ? 'AIM level 1' : (d===2 ? 'AIM level 2' : 'AIM level 3');
  document.getElementById('t-tbl').textContent = 'Detail — ' + col;
  document.getElementById('q-tbl').textContent = 'Click a row to zoom one level deeper.';
  thead.innerHTML = '<tr><th>'+col+'</th><th class="n">Part numbers</th>'
    +'<th class="n">Parts billed</th><th class="n">Step €</th><th class="n">Weighted</th></tr>';
  tbody.innerHTML = rows.length ? rows.map(function(r, ix){
    var name = d===1 ? P.l1[r.l1] : (d===2 ? P.l2[r.l2] : P.l3[r.l3]);
    return '<tr class="clickable" data-ix="'+ix+'"><td>'+esc(name)+'</td>'
      +'<td class="n">'+fmtNum(r.pn||0)+'</td>'
      +'<td class="n">'+fmtEur(r.all)+'</td>'
      +'<td class="n">'+fmtEur(r.step)+'</td>'
      +'<td class="n">'+fmtPct(r.pct)+'</td></tr>';
  }).join('') : '<tr><td colspan="5" class="muted">No rows.</td></tr>';
  Array.prototype.forEach.call(tbody.querySelectorAll('tr.clickable'), function(tr){
    tr.addEventListener('click', function(){
      zoomInto(rows[Number(tr.getAttribute('data-ix'))]);
    });
  });
}

function render(){
  window.__err = [];
  try{
    var t = totalsNow();
    kpis(t);
    drawCompare();
    drawCrumb();
    var rows = currentRows();
    drawRail(rows);
    drawZoom(rows);
    drawTable(rows);
  }catch(e){ window.__err.push(String(e && e.message ? e.message : e)); }
}

function setCust(ci){
  state.cust = ci;
  state.l1 = -1; state.l2 = null; state.l3 = null; state.other = null;
  var sel = document.getElementById('cust');
  if(sel) sel.value = String(ci);
  render();
}
function setSrc(i){
  state.src = i;
  render();
}

function init(){
  var custSel = document.getElementById('cust');
  custSel.innerHTML = '<option value="-1">All Nordics customers (4 accounts)</option>'
    + N.customers.map(function(c){
      return '<option value="'+c.ci+'">'+esc(c.market)+' — '+esc(c.name)
        +' ('+esc(c.code)+')</option>';
    }).join('');
  custSel.addEventListener('change', function(){ setCust(Number(this.value)); });

  var srcSel = document.getElementById('src');
  srcSel.innerHTML = '<option value="-1">All sources</option>'
    + P.src.map(function(s,i){ return '<option value="'+i+'">'+esc(s)+'</option>'; }).join('');
  srcSel.addEventListener('change', function(){ setSrc(Number(this.value)); });

  Array.prototype.forEach.call(document.querySelectorAll('#meas button'), function(b){
    b.addEventListener('click', function(){
      state.metric = b.getAttribute('data-m');
      Array.prototype.forEach.call(document.querySelectorAll('#meas button'), function(x){
        x.classList.toggle('on', x===b);
      });
      render();
    });
  });
  document.getElementById('reset').addEventListener('click', function(){
    state.cust=-1; state.src=-1; state.metric='billed';
    state.l1=-1; state.l2=null; state.l3=null; state.other=null;
    document.getElementById('cust').value='-1';
    document.getElementById('src').value='-1';
    Array.prototype.forEach.call(document.querySelectorAll('#meas button'), function(x){
      x.classList.toggle('on', x.getAttribute('data-m')==='billed');
    });
    render();
  });

  document.getElementById('genline').textContent =
    ' Built from the same AIM cube as the network pack · ' + (D.generated||'').slice(0,10) + '.';
  document.getElementById('foot').innerHTML =
    '<b>Prototype scope.</b> Nordics sold-tos only: '
    + N.customers.map(function(c){ return c.market+' ('+c.code+')'; }).join(', ')
    + '. Denmark is not in this list. Same basis as the network pack: in-scope lines, '
    + D.fx + ' JPY per EUR, no elasticity modelled.'
    + '<br><br><b>Not the original.</b> The network pack stays at '
    + 'ISZE_Pricing_Revision_AIM_Source.html. Frozen L3PN and FX overlays are untouched.';

  window.__qa = function(){
    return {
      errors: window.__err||[],
      kpi: document.querySelectorAll('#kpis .kpi').length,
      compare: document.querySelectorAll('#compare .cmini').length,
      rail: document.querySelectorAll('#rail .chip').length,
      detail: document.querySelectorAll('#detail tbody tr').length,
      depth: depth(),
      cust: state.cust,
      zoomDrawn: !!(charts['c-zoom'] && charts['c-zoom'].chartArea)
    };
  };
  render();
}
init();
})();
</script>
</body>
</html>
"""


def main() -> int:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    pool = payload["pool"]
    db_labels = pool["db"]
    # Resolve Nordics customers from the live pool (indices can shift if cube rebuilds).
    nordics_db_idx = {lab: i for i, lab in enumerate(db_labels) if lab in NORDICS_DB_LABELS}
    by_cust: dict[int, dict] = {}
    for row in payload["customers"]:
        ci, cni, dbi = int(row[0]), int(row[1]), int(row[2])
        db_lab = db_labels[dbi]
        if db_lab not in nordics_db_idx:
            continue
        if ci not in by_cust:
            by_cust[ci] = {
                "ci": ci,
                "code": pool["cust"][ci],
                "name": pool["cname"][cni],
                "db": db_lab,
                "dbi": dbi,
                "market": NORDICS_MARKET.get(db_lab, db_lab),
                "prior": 0.0,
                "new": 0.0,
            }
        by_cust[ci]["prior"] += float(row[8] or 0)
        by_cust[ci]["new"] += float(row[9] or 0)
    # Stable market order: Sweden, Norway, Finland, Iceland
    order = {"Sweden": 0, "Norway": 1, "Finland": 2, "Iceland": 3}
    customers = sorted(by_cust.values(), key=lambda c: (order.get(c["market"], 9), c["name"]))
    nordics_meta = {
        "db_labels": list(NORDICS_DB_LABELS),
        "customers": [
            {
                "ci": c["ci"],
                "code": c["code"],
                "name": c["name"],
                "db": c["db"],
                "dbi": c["dbi"],
                "market": c["market"],
            }
            for c in customers
        ],
    }
    if len(customers) < 4:
        raise SystemExit(f"expected 4 Nordics customers, found {len(customers)}: {customers}")

    chart = CHART.read_text(encoding="utf-8")
    chart = chart.replace("//# sourceMappingURL=chart.umd.min.js.map", "")
    html = (
        HTML.replace("__PAYLOAD__", json.dumps(payload, separators=(",", ":")))
        .replace("__NORDICS__", json.dumps(nordics_meta, separators=(",", ":")))
        .replace("__CHARTJS__", chart)
    )
    OUT.write_text(html, encoding="utf-8")
    OPEN.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_Pricing_Revision_AIM_Source_PROTOTYPE_NordicsCust.html"\r\n',
        encoding="utf-8",
        newline="",
    )
    print(f"nordics customers: {len(customers)}")
    for c in customers:
        print(f"  {c['market']:8} {c['code']:>6}  {c['name']}")
    print(f"-> {OUT}  ({OUT.stat().st_size/1024/1024:.2f} MB)")
    print(f"-> {OPEN}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
