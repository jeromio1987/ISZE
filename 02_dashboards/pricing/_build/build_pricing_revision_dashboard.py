#!/usr/bin/env python3
"""Build the dynamic pricing-revision HTML.

One self-contained page: the data pack and Chart.js are both inlined, so it opens
straight from Explorer with no server and no CDN.

What it does
  - AIM family drill first (L1 -> L2 -> L3 -> part numbers) on All-network or one DB
  - sold-to customer is an optional further cut, not required to start
  - distributor dropdown (All network + the 22 trading entities); blank/unset = all DBs
  - source of supply filter: all / Japan (IML) / Thailand (IMIT) / not held
  - charts chosen for the question, not a fixed bar form:
      * league of distributors              -> ranked bars, network reference line
      * where the euro sits in one family   -> donut, <= 4 segments
      * Japan against Thailand              -> paired bars on the same families
      * the biggest individual part numbers -> ranked bars
  - KPI chips carry hover tooltips with the formula and what is excluded

Run: python 02_dashboards/pricing/_build/build_pricing_revision_dashboard.py
"""
from __future__ import annotations

import json
from pathlib import Path

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
BUILD = ISZE / "02_dashboards" / "pricing" / "_build"
DATA = BUILD / "pricing_dashboard_data.json"
CHART = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"
OUT = ISZE / "02_dashboards" / "pricing" / "ISZE_Pricing_Revision_AIM_Source.html"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Price revision - distributor, family and source of supply</title>
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
h2{font-size:19px;margin-bottom:2px}
h3{font-size:15px}
.wrap{max-width:1360px;margin:0 auto;padding:22px 22px 60px}
header.top{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:18px}
.sub{color:var(--muted);font-size:13px;margin-top:6px}
.badge{display:inline-block;background:var(--navy);color:var(--paper);
  font-size:11px;letter-spacing:.6px;text-transform:uppercase;
  padding:3px 9px;border-radius:2px;margin-right:8px}

.controls{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;
  background:#fff;border:1px solid var(--line);border-left:4px solid var(--terra);
  padding:14px 16px;margin-bottom:18px}
.ctrl{display:flex;flex-direction:column;gap:5px}
.ctrl label{font-size:11px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted)}
select{font-size:14px;padding:7px 10px;border:1px solid var(--line);background:#fff;
  color:var(--ink);border-radius:2px;min-width:190px}
select:focus{outline:2px solid var(--terra);outline-offset:-1px}
.seg{display:flex;border:1px solid var(--line);border-radius:2px;overflow:hidden}
.seg button{background:#fff;border:0;border-right:1px solid var(--line);
  padding:7px 13px;font-size:13px;cursor:pointer;color:var(--ink)}
.seg button:last-child{border-right:0}
.seg button.on{background:var(--navy);color:var(--paper)}
.reset{background:#fff;border:1px solid var(--line);padding:7px 13px;font-size:13px;
  cursor:pointer;color:var(--terra);border-radius:2px}

.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));
  gap:12px;margin-bottom:20px}
.kpi{background:#fff;border:1px solid var(--line);padding:13px 15px;position:relative;
  border-top:3px solid var(--navy)}
.kpi .lab{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);
  display:flex;align-items:center;gap:5px}
.kpi .val{font-size:24px;font-weight:600;color:var(--navy);margin-top:5px;
  font-variant-numeric:tabular-nums}
.kpi .note{font-size:11.5px;color:var(--muted);margin-top:3px}
.kpi.t{border-top-color:var(--terra)}
.info{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;
  border-radius:50%;background:var(--navy);color:#fff;font-size:9.5px;cursor:help;
  position:relative;flex:0 0 auto}
.info .tip{display:none;position:absolute;bottom:22px;left:50%;transform:translateX(-50%);
  width:268px;background:var(--navy);color:var(--paper);font-size:12px;line-height:1.45;
  padding:9px 11px;border-radius:3px;z-index:60;text-transform:none;letter-spacing:0;
  font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25)}
.info .tip b{color:#f0b49a}
.info:hover .tip,.info:focus .tip{display:block}

.grid{display:grid;gap:16px;margin-bottom:18px}
.g2{grid-template-columns:1fr 1fr}
.g1{grid-template-columns:1fr}
@media(max-width:980px){.g2{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid var(--line);padding:15px 16px 12px}
.card .q{font-size:14px;color:var(--muted);margin:2px 0 12px}
.chartbox{position:relative;height:340px}
.chartbox.tall{height:410px}
.chartbox.short{height:250px}

table{border-collapse:collapse;width:100%;font-size:13px}
th{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;
  font-weight:600;font-size:11.5px;letter-spacing:.4px;text-transform:uppercase;
  position:sticky;top:0;white-space:nowrap}
#cust-pn th,#brake-pn th{cursor:pointer;user-select:none}
#cust-pn th .sortmark,#brake-pn th .sortmark{opacity:.45;font-size:10px;margin-left:4px;font-weight:400}
#cust-pn th.on .sortmark,#brake-pn th.on .sortmark{opacity:1;color:#f0b49a}
th.n,td.n{text-align:right;font-variant-numeric:tabular-nums}
td{padding:6px 9px;border-bottom:1px solid var(--line)}
tbody tr:nth-child(even){background:var(--band)}
tbody tr:hover{background:#e3ecf6}
tbody tr.clickable{cursor:pointer}
tbody tr.sel{background:#f6e3da!important;box-shadow:inset 3px 0 0 var(--terra)}
.tblwrap{max-height:430px;overflow:auto;border:1px solid var(--line)}
.pill{display:inline-block;padding:1px 7px;border-radius:9px;font-size:11px;
  border:1px solid var(--line);background:var(--paper);color:var(--muted)}
.pill.jp{border-color:#9db4cf;color:#2c4b74}
.pill.th{border-color:#d9b48c;color:#8a5622}
.pill.na{border-color:#c9c2b6;color:#8a8275}
.muted{color:var(--muted)}
.warn{background:#fdf3e3;border:1px solid #e6cf9f;border-left:4px solid var(--amber);
  padding:11px 14px;font-size:12.5px;color:#5e4a1c;margin-bottom:18px}
.foot{font-size:12px;color:var(--muted);border-top:1px solid var(--line);
  padding-top:12px;margin-top:24px}
.crumb{font-size:12.5px;color:var(--muted);margin-bottom:9px}
.crumb b{color:var(--navy)}
.crumb span{cursor:pointer;color:var(--terra);text-decoration:underline}

/* the few-figures band used by the brake and concentration sections */
.figs{display:flex;flex-wrap:wrap;gap:22px;margin:2px 0 14px}
.fig{min-width:186px}
.fig .fv{font-size:21px;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums;
  display:flex;align-items:center;gap:5px}
.fig.t .fv{color:var(--terra)}
.fig .fl{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);margin-top:2px}
.fig .fn{font-size:12px;color:var(--muted);margin-top:2px}
</style>
</head>
<body>
<div class="wrap">

<header class="top">
  <div><span class="badge">Price revision</span><span class="badge" style="background:var(--terra)">Internal</span></div>
  <h1 style="margin-top:9px">Where the parts price revision lands</h1>
  <div class="sub">By distributor, by AIM family at all three levels, and by source of supply:
    Japan through IML or Thailand through IMIT. Parts billed 1 July 2025 to 30 June 2026.
    Opens from Explorer with no server and no internet — the data and charts are inside the file.
    <span id="genline"></span></div>
</header>

<div class="warn" id="errbar" style="display:none"></div>

<div class="warn">
  <b>What the headline is.</b> The percentage is a base-price move: the euro increase measured against
  the prior base price, weighted by the quantities actually billed. It is not a revenue, margin or
  elasticity outcome, and no demand response is modelled. Parts billed euro covers every in-scope line;
  the weighted percentage covers only lines priced on both sides, which is stated on every panel.
</div>

<div class="controls">
  <div class="ctrl">
    <label for="db">Distributor</label>
    <select id="db"></select>
  </div>
  <div class="ctrl">
    <label for="cust">Customer (sold-to, optional)</label>
    <select id="cust" style="min-width:320px"></select>
  </div>
  <div class="ctrl">
    <label for="src">Source of supply</label>
    <select id="src"></select>
  </div>
  <div class="ctrl">
    <label for="concscope">Concentration view</label>
    <select id="concscope">
      <option value="all">All families</option>
      <option value="brake">Brakes only</option>
    </select>
  </div>
  <div class="ctrl">
    <label>Include</label>
    <div class="seg" id="meas">
      <button data-m="pct" class="on">Weighted %</button>
      <button data-m="step">Step EUR</button>
      <button data-m="billed">Parts billed EUR</button>
    </div>
  </div>
  <div class="ctrl">
    <label>&nbsp;</label>
    <button class="reset" id="reset">Reset to network</button>
  </div>
</div>

<div class="kpis" id="kpis"></div>

<div class="grid g2" id="cust-drill">
  <div class="card">
    <h2 id="t-cust-mix">Which AIM families move most?</h2>
    <div class="q" id="q-cust-mix">Level 1 for the current slice (all distributors, or one). Click a bar to
      open level 2. A sold-to customer is optional and narrows the same path.</div>
    <div class="chartbox tall"><canvas id="c-cust-mix"></canvas></div>
  </div>
  <div class="card">
    <h2 id="t-cust-pn">Drill table — level 1 → level 2 → level 3</h2>
    <div class="crumb" id="cust-crumb">Network — AIM level 1. Click a row to go deeper.</div>
    <div class="q" id="q-cust-pn">Click a row to go deeper. On the part-number list, click a column header to re-sort.</div>
    <div class="tblwrap" style="max-height:410px"><table id="cust-pn"><thead></thead><tbody></tbody></table></div>
  </div>
</div>

<div class="grid g2">
  <div class="card">
    <h2 id="t-league">Which distributor carries the biggest price step?</h2>
    <div class="q" id="q-league"></div>
    <div class="chartbox"><canvas id="c-league"></canvas></div>
  </div>
  <div class="card">
    <h2 id="t-l1">Where the revision sits across the AIM families</h2>
    <div class="q" id="q-l1"></div>
    <div class="chartbox"><canvas id="c-l1"></canvas></div>
  </div>
</div>

<div class="grid g2">
  <div class="card">
    <h2 id="t-mix">Which level 2 family carries the most of it?</h2>
    <div class="q" id="q-mix"></div>
    <div class="chartbox tall"><canvas id="c-mix"></canvas></div>
  </div>
  <div class="card">
    <h2 id="t-src">Japan against Thailand, on the same families</h2>
    <div class="q" id="q-src"></div>
    <div class="chartbox tall"><canvas id="c-src"></canvas></div>
  </div>
</div>

<div class="grid g1">
  <div class="card">
    <h2>The drill: level 1 → level 2 → level 3 → part numbers</h2>
    <div class="crumb" id="crumb"></div>
    <div class="q">Click a row to go one level deeper. At level 3, the next click lists the part
      numbers. The euro and the weighted percentage are the selected distributor and source only.</div>
    <div class="tblwrap"><table id="drill"><thead></thead><tbody></tbody></table></div>
  </div>
</div>

<div class="grid g1">
  <div class="card">
    <h2>The biggest individual part numbers</h2>
    <div class="q">Read with the family and the source beside them. A part number on its own is a
      quantity, not a finding.</div>
    <div class="tblwrap" style="max-height:340px"><table id="movers"><thead></thead><tbody></tbody></table></div>
  </div>
</div>

<div class="grid g1">
  <div class="card">
    <h2 id="t-conc">How few part numbers carry the increase?</h2>
    <div class="q" id="q-conc"></div>
    <div class="figs" id="conc-figs"></div>
    <div class="chartbox short"><canvas id="c-conc"></canvas></div>
  </div>
</div>

<div class="grid g1">
  <div class="card">
    <h2 id="t-brake">Inside brakes: which sub-group and which part number?</h2>
    <div class="q" id="q-brake"></div>
    <div class="figs" id="brake-figs"></div>
    <div class="chartbox short"><canvas id="c-brake"></canvas></div>
    <div class="tblwrap" style="max-height:300px" id="brake-l2wrap">
      <table id="brake-l2"><thead></thead><tbody></tbody></table>
    </div>
    <div class="crumb" id="brake-crumb" style="margin-top:12px"></div>
    <div class="tblwrap" style="max-height:340px"><table id="brake-pn"><thead></thead><tbody></tbody></table></div>
  </div>
</div>

<div class="foot" id="foot"></div>
</div>

<script type="application/json" id="payload">__PAYLOAD__</script>
<script>__CHARTJS__</script>
<script>
(function(){
"use strict";
var D = JSON.parse(document.getElementById('payload').textContent);
window.D = D;
var P = D.pool;
var NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee', LINE='#d9d3c8',
    BLUE='#3d6098', SAND='#d9a05b', GREY='#9aa2ad', GREEN='#1e6b4f';

function fmtEur(v,dec){
  if(v===null||v===undefined||isNaN(v)) return '—';
  var d = (dec===undefined)?0:dec;
  return '€' + Number(v).toLocaleString('en-GB',{minimumFractionDigits:d,maximumFractionDigits:d});
}
function fmtPct(v,dec){
  if(v===null||v===undefined||isNaN(v)) return '—';
  var d = (dec===undefined)?2:dec;
  return Number(v).toFixed(d) + '%';
}
function fmtNum(v){ return Number(v).toLocaleString('en-GB'); }
function esc(s){ return String(s).replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

/* ---------- state ---------- */
var state = { db:-1, src:-1, metric:'pct', l1:-1, l2:-1, l3:-1, cust:-1, custL1:-1, custL2:null, custL3:null, custOther:null,
  custPnSort:{ key:'step', dir:-1 }, drillPnSort:{ key:'step', dir:-1 },
  brakeL2:null, brakePnSort:{ key:'step', dir:-1 } };
window.state = state;

var srcPill = function(i){
  var v = P.src[i];
  var cls = /Japan/.test(v)?'jp':(/Thailand/.test(v)?'th':'na');
  return '<span class="pill '+cls+'">'+esc(v)+'</span>';
};

/* ---------- roll the groups up to any grain ---------- */
function rollup(keys, opts){
  opts = opts || {};
  var map = {};
  var rows = D.groups;
  for(var i=0;i<rows.length;i++){
    var r = rows[i];
    if(state.db>=0 && r[0]!==state.db) continue;
    if(state.src>=0 && r[4]!==state.src) continue;
    if(opts.l1!==undefined && r[1]!==opts.l1) continue;
    if(opts.l2!==undefined && opts.l2>=0 && r[2]!==opts.l2) continue;
    var k = keys.map(function(x){return r[x];}).join('|');
    var o = map[k];
    if(!o){ o = {key:k, kk:keys.map(function(x){return r[x];}),
      pn:0, rows:0, qty:0, billed:0, prior:0, new:0, step:0, all:0}; map[k]=o; }
    o.pn += r[5]; o.rows += r[6]; o.qty += r[7]; o.billed += r[8];
    o.prior += r[9]; o.new += r[10]; o.step += r[11]; o.all += r[12];
  }
  var out = [];
  for(var k2 in map){ var o2 = map[k2]; o2.pct = o2.prior>0 ? 100*(o2.new/o2.prior-1) : null; out.push(o2); }
  return out;
}

/* the same, driven by the account table, so a customer view is consistent */
function rollupCustomers(keys){
  var map = {};
  for(var i=0;i<D.customers.length;i++){
    var r = D.customers[i];
    if(state.db>=0 && r[2]!==state.db) continue;
    if(state.src>=0 && r[3]!==state.src) continue;
    var k = keys.map(function(x){return r[x];}).join('|');
    var o = map[k];
    if(!o){ o={key:k,kk:keys.map(function(x){return r[x];}), pn:0,rows:0,qty:0,
      billed:0,prior:0,new:0,step:0,all:0,unpriced:0,unpricedN:0}; map[k]=o; }
    o.pn+=r[4]; o.rows+=r[5]; o.qty+=r[6]; o.billed+=r[7]; o.prior+=r[8];
    o.new+=r[9]; o.step+=r[10]; o.all+=r[11]; o.unpriced+=r[12]; o.unpricedN+=r[13];
  }
  var out=[]; for(var k2 in map){ var o2=map[k2]; o2.pct=o2.prior>0?100*(o2.new/o2.prior-1):null; out.push(o2); }
  return out;
}

function sumMetricRows(rows){
  var t = {pn:0,rows:0,qty:0,billed:0,prior:0,new:0,step:0,all:0};
  for(var i=0;i<rows.length;i++){
    var r = rows[i];
    t.pn += r.pn||0; t.rows += r.rows||0; t.qty += r.qty||0;
    t.billed += r.billed||0; t.prior += r.prior||0; t.new += r.new||0;
    t.step += r.step||0; t.all += r.all||0;
  }
  t.pct = t.prior>0 ? 100*(t.new/t.prior-1) : null;
  return t;
}
function aimDrillActive(){
  return state.custL1 >= 0;
}
function totalsAimDrill(){
  /* KPIs must follow the Network → L1 → L2 → L3 zoom, not stay on the network total. */
  if(typeof state.custL3 === 'number' && state.custL3 >= 0){
    return sumMetricRows(rollupCustL3({l1: state.custL1, l2: state.custL2}).filter(function(r){
      return r.l3 === state.custL3;
    }));
  }
  if(state.custL2 !== null && state.custL2 !== undefined){
    return sumMetricRows(rollupCustL3({l1: state.custL1, l2: state.custL2}));
  }
  return sumMetricRows(rollupCustL1().filter(function(r){ return r.l1 === state.custL1; }));
}
function totalsNow(){
  /* AIM family zoom wins over the network chips once a level-1 family is open. */
  if(aimDrillActive()) return totalsAimDrill();
  /* When a sold-to is in focus, KPIs follow that account (and source filter). */
  if(state.cust >= 0){
    var map = {};
    for(var i=0;i<D.customers.length;i++){
      var r = D.customers[i];
      if(r[0] !== state.cust) continue;
      if(state.src>=0 && r[3]!==state.src) continue;
      var o = map.x;
      if(!o){ o={pn:0,rows:0,qty:0,billed:0,prior:0,new:0,step:0,all:0}; map.x=o; }
      o.pn+=r[4]; o.rows+=r[5]; o.qty+=r[6]; o.billed+=r[7]; o.prior+=r[8];
      o.new+=r[9]; o.step+=r[10]; o.all+=r[11];
    }
    var t = map.x || {pn:0,rows:0,qty:0,billed:0,prior:0,new:0,step:0,all:0};
    t.pct = t.prior>0 ? 100*(t.new/t.prior-1) : null;
    return t;
  }
  var m = rollup([0], {});       /* one bucket = the current selection */
  var t2 = {pn:0,rows:0,qty:0,billed:0,prior:0,new:0,step:0,all:0};
  for(var j=0;j<m.length;j++){ for(var k in t2) t2[k]+=m[j][k]; }
  t2.pct = t2.prior>0 ? 100*(t2.new/t2.prior-1) : null;
  return t2;
}

function custName(ci){
  for(var i=0;i<D.customers.length;i++){
    if(D.customers[i][0]===ci) return P.cname[D.customers[i][1]];
  }
  return P.cust[ci] || '';
}
function custLabel(ci){
  var name = custName(ci);
  var code = String(P.cust[ci] || '');
  if(!code) return name;
  if(name && name.indexOf('('+code+')') >= 0) return name;
  return name + ' (' + code + ')';
}
function custDb(ci){
  for(var i=0;i<D.customers.length;i++){
    if(D.customers[i][0]===ci) return D.customers[i][2];
  }
  return -1;
}

function scopeSliceLabel(){
  if(state.cust >= 0) return custLabel(state.cust);
  if(state.db >= 0) return P.db[state.db];
  return 'the network';
}
function custInDb(ci){
  if(state.db < 0) return true;
  return custDb(ci) === state.db;
}

/* Customer drill depth: L1 → L2 → L3 → part numbers.
   With no sold-to selected, the same path runs on the current distributor
   slice (All network when distributor is blank / All). */
function rollupCustL1(){
  var map = {};
  if(state.cust < 0){
    /* Network / DB grain from groups — unique PN counts stay honest. */
    var g = rollup([1], {});
    return g.map(function(r){
      return {l1:r.kk[0], pn:r.pn, billed:r.billed, prior:r.prior, new:r.new,
        step:r.step, all:r.all, pct:r.pct, rows:r.rows, qty:r.qty};
    });
  }
  var rows = D.cust_fam || [];
  for(var i=0;i<rows.length;i++){
    var r = rows[i];
    if(r[0]!==state.cust) continue;
    if(state.src>=0 && r[3]!==state.src) continue;
    var o = map[r[2]];
    if(!o){ o={l1:r[2], pn:0, billed:0, prior:0, new:0, step:0, all:0}; map[r[2]]=o; }
    o.pn += r[4]; o.billed += r[5]; o.prior += r[6]; o.new += r[7];
    o.step += r[8]; o.all += (r[9]!==undefined ? r[9] : r[5]);
  }
  var out=[];
  for(var k in map){ var o2=map[k]; o2.pct=o2.prior>0?100*(o2.new/o2.prior-1):null; out.push(o2); }
  return out;
}
function rollupCustL2(opts){
  opts = opts || {};
  if(state.cust < 0){
    var g2 = rollup([1,2], {l1: opts.l1});
    return g2.filter(function(r){
      if(opts.l2!==undefined && opts.l2>=0 && r.kk[1]!==opts.l2) return false;
      return true;
    }).map(function(r){
      return {l1:r.kk[0], l2:r.kk[1], pn:r.pn, rows:r.rows, qty:r.qty,
        billed:r.billed, prior:r.prior, new:r.new, step:r.step, all:r.all, pct:r.pct};
    });
  }
  var map = {};
  var rows = D.cust_l2 || [];
  for(var i=0;i<rows.length;i++){
    var r = rows[i];
    if(r[0]!==state.cust) continue;
    if(state.src>=0 && r[3]!==state.src) continue;
    if(opts.l1!==undefined && r[1]!==opts.l1) continue;
    if(opts.l2!==undefined && opts.l2>=0 && r[2]!==opts.l2) continue;
    var k = r[1]+'|'+r[2];
    var o = map[k];
    if(!o){ o={l1:r[1],l2:r[2], pn:0,rows:0,qty:0,billed:0,prior:0,new:0,step:0,all:0}; map[k]=o; }
    o.pn+=r[4]; o.rows+=r[5]; o.qty+=r[6]; o.billed+=r[7];
    o.prior+=r[8]; o.new+=r[9]; o.step+=r[10]; o.all+=r[11];
  }
  var out=[];
  for(var k2 in map){ var o2=map[k2]; o2.pct=o2.prior>0?100*(o2.new/o2.prior-1):null; out.push(o2); }
  return out;
}
function rollupCustL3(opts){
  opts = opts || {};
  if(state.cust < 0){
    var filt = {l1: opts.l1};
    if(opts.l2!==undefined && opts.l2>=0) filt.l2 = opts.l2;
    var g3 = rollup([1,2,3], filt);
    return g3.filter(function(r){
      if(opts.l2 === -1){
        if(!state.custOther || !state.custOther.some(function(x){ return x===r.kk[1]; })) return false;
      }
      return true;
    }).map(function(r){
      return {l1:r.kk[0], l2:r.kk[1], l3:r.kk[2], pn:r.pn, rows:r.rows, qty:r.qty,
        billed:r.billed, prior:r.prior, new:r.new, step:r.step, all:r.all, pct:r.pct};
    });
  }
  var map = {};
  var rows = D.cust_l3 || [];
  for(var i=0;i<rows.length;i++){
    var r = rows[i];
    if(r[0]!==state.cust) continue;
    if(state.src>=0 && r[4]!==state.src) continue;
    if(opts.l1!==undefined && r[1]!==opts.l1) continue;
    if(opts.l2 === -1){
      if(!state.custOther || !state.custOther.some(function(x){ return x===r[2]; })) continue;
    } else if(opts.l2!==undefined && opts.l2>=0 && r[2]!==opts.l2) continue;
    var k = r[1]+'|'+r[2]+'|'+r[3];
    var o = map[k];
    if(!o){ o={l1:r[1],l2:r[2],l3:r[3], pn:0,rows:0,qty:0,billed:0,prior:0,new:0,step:0,all:0}; map[k]=o; }
    o.pn+=r[5]; o.rows+=r[6]; o.qty+=r[7]; o.billed+=r[8];
    o.prior+=r[9]; o.new+=r[10]; o.step+=r[11]; o.all+=r[12];
  }
  var out=[];
  for(var k2 in map){ var o2=map[k2]; o2.pct=o2.prior>0?100*(o2.new/o2.prior-1):null; out.push(o2); }
  return out;
}

function setCustL1(i){
  state.custL1 = i; state.custL2 = null; state.custL3 = null; state.custOther = null;
  state.brakeL2 = null;
  render();
}
function setCustL2(i){
  state.custL2 = i; state.custL3 = null;
  render();
}
function setCustL3(i){
  state.custL3 = i;
  render();
}
function custCrumbHtml(){
  var root = state.cust >= 0 ? custLabel(state.cust)
    : (state.db >= 0 ? P.db[state.db] : 'Network');
  var parts = ['<span data-cstep="root">'+esc(root)+'</span>'];
  if(state.custL1>=0) parts.push('<span data-cstep="l1">'+esc(P.l1[state.custL1])+'</span>');
  if(state.custL2 === -1) parts.push('<span data-cstep="l2">All other groups</span>');
  else if(typeof state.custL2 === 'number' && state.custL2 >= 0)
    parts.push('<span data-cstep="l2">'+esc(P.l2[state.custL2])+'</span>');
  if(typeof state.custL3 === 'number' && state.custL3 >= 0)
    parts.push('<span data-cstep="l3">'+esc(P.l3[state.custL3])+'</span>');
  return parts.join(' › ');
}
function wireCustCrumb(){
  var el = document.getElementById('cust-crumb');
  Array.prototype.forEach.call(el.querySelectorAll('span[data-cstep]'), function(sp){
    sp.style.cursor = 'pointer';
    sp.style.color = 'var(--terra)';
    sp.style.textDecoration = 'underline';
    sp.addEventListener('click', function(){
      var step = sp.getAttribute('data-cstep');
      if(step==='root'){ state.custL1=-1; state.custL2=null; state.custL3=null; state.custOther=null; }
      else if(step==='l1'){ state.custL2=null; state.custL3=null; state.custOther=null; }
      else if(step==='l2'){ state.custL3=null; }
      render();
    });
  });
}

function drawCustMix(){
  var canvas = document.getElementById('c-cust-mix');
  var slice = scopeSliceLabel();

  /* ---- Level 1 bars ---- */
  if(state.custL1 < 0){
    var l1rows = rollupCustL1().filter(function(r){ return r.all > 0; });
    l1rows.sort(function(a,b){
      var ag = /Not on AIM/.test(P.l1[a.l1]) ? 1 : 0;
      var bg = /Not on AIM/.test(P.l1[b.l1]) ? 1 : 0;
      if(ag !== bg) return ag - bg;
      return b.all - a.all;
    });
    var labels = l1rows.map(function(r){ return P.l1[r.l1]; });
    var vals = l1rows.map(function(r){ return r.all; });
    var keys = l1rows.map(function(r){ return r.l1; });
    document.getElementById('t-cust-mix').textContent =
      'Which AIM families carry the revision for ' + slice + '?';
    document.getElementById('q-cust-mix').textContent =
      'Level 1 for ' + slice + '. Bars are parts billed euro for each family. Click a bar to open level 2.'
      + (state.cust < 0 ? ' Sold-to remains optional if you want one account only.' : '');
    chart('c-cust-mix', {
      type:'bar',
      data:{ labels:labels, datasets:[{ data:vals,
        backgroundColor:labels.map(function(l){ return /Not on AIM/.test(l)? GREY : BLUE; }),
        borderRadius:2, borderSkipped:false }] },
      options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
        onClick:function(evt, els){
          if(!els || !els.length) return;
          setCustL1(keys[els[0].index]);
        },
        plugins:{ legend:{display:false},
          tooltip:{callbacks:{ label:function(c){ return 'Parts billed ' + fmtEur(c.raw); }}} },
        scales:{
          x:{ beginAtZero:true, grid:{color:'#eceae4'},
              title:{display:true, text:'Parts billed euro', font:{size:11}, color:'#6b6459'},
              ticks:{callback:function(v){ return fmtEur(v); },font:{size:11}} },
          y:{ grid:{display:false}, ticks:{font:{size:11.5},color:NAVY} } },
        animation:{duration:250} }
    });
    return;
  }

  /* ---- Level 2 donut ---- */
  if(state.custL2 === null || state.custL2 === undefined){
    var fam = rollupCustL2({l1: state.custL1}).filter(function(r){
      return r.all > 0 && !/Not classified at L3/.test(P.l2[r.l2]);
    });
    fam.sort(function(a,b){ return b.all-a.all; });
    var head = fam.slice(0,3);
    var rest = fam.slice(3);
    var restE = rest.reduce(function(s,r){ return s+r.all; },0);
    var labels2 = head.map(function(r){ return P.l2[r.l2]; });
    var vals2 = head.map(function(r){ return r.all; });
    var keys2 = head.map(function(r){ return r.l2; });
    if(restE>0){
      labels2.push('All other groups');
      vals2.push(restE);
      keys2.push(-1);
      state.custOther = rest.map(function(r){ return r.l2; });
    } else {
      state.custOther = [];
    }
    if(!vals2.length){ labels2=['No data for this selection']; vals2=[1]; keys2=[-2]; }
    document.getElementById('t-cust-mix').textContent =
      'Level 2 inside ' + P.l1[state.custL1] + ' for ' + slice;
    document.getElementById('q-cust-mix').textContent =
      'Top three groups named; the rest combined. Click a segment to open level 3.';
    chart('c-cust-mix', {
      type:'doughnut',
      data:{ labels:labels2, datasets:[{ data:vals2,
        backgroundColor:[NAVY,TERRA,SAND,GREY], borderColor:'#fff', borderWidth:2 }] },
      options:{ responsive:true, maintainAspectRatio:false, cutout:'52%',
        onClick:function(evt, els){
          if(!els || !els.length) return;
          var l2 = keys2[els[0].index];
          if(l2 === -2) return;
          setCustL2(l2);
        },
        plugins:{ legend:{position:'bottom',labels:{font:{size:12},boxWidth:12,padding:12}},
          tooltip:{callbacks:{ label:function(c){
            var tot = c.dataset.data.reduce(function(a,b){return a+b;},0);
            return c.label + ': ' + fmtEur(c.raw) + ' (' + fmtPct(100*c.raw/tot,1) + ')'; }}} } },
      plugins:[{ id:'centreCust', afterDraw:function(ch){
        var g=ch.ctx; g.save(); g.textAlign='center'; g.textBaseline='middle';
        var x=(ch.chartArea.left+ch.chartArea.right)/2, y=(ch.chartArea.top+ch.chartArea.bottom)/2-6;
        g.fillStyle=NAVY; g.font='600 17px Georgia, serif';
        g.fillText(fmtEur(vals2.reduce(function(a,b){return a+b;},0)), x, y);
        g.fillStyle='#6b6459'; g.font='11px sans-serif';
        g.fillText('parts billed', x, y+17); g.restore();
      }}]
    });
    return;
  }

  /* ---- Level 3 bars ---- */
  var l3rows = rollupCustL3({l1: state.custL1, l2: state.custL2}).filter(function(r){ return r.all > 0; });
  l3rows.sort(function(a,b){ return b.all - a.all; });
  var labels3 = l3rows.map(function(r){ return P.l3[r.l3]; });
  /* Bars are always this slice's parts billed — never the network step KPI. */
  var vals3 = l3rows.map(function(r){ return r.all; });
  var keys3 = l3rows.map(function(r){ return r.l3; });
  var l2name = state.custL2 === -1 ? 'All other groups' : P.l2[state.custL2];
  var sliceStep = l3rows.reduce(function(s,r){ return s+(r.step||0); },0);
  var sliceAll = l3rows.reduce(function(s,r){ return s+(r.all||0); },0);
  document.getElementById('t-cust-mix').textContent =
    'Level 3 inside ' + l2name + ' for ' + slice;
  document.getElementById('q-cust-mix').textContent =
    (typeof state.custL3 === 'number' && state.custL3 >= 0)
      ? ('Level 3 selected. Bars show parts billed for this slice ('
        + fmtEur(sliceAll) + '), not the network step. Slice step is ' + fmtEur(sliceStep)
        + '. The table lists the part numbers. Click the breadcrumb to step back.')
      : ('Bars show parts billed euro for each type inside this family. Slice step is '
        + fmtEur(sliceStep) + '. Click a bar to list the part numbers.');
  chart('c-cust-mix', {
    type:'bar',
    data:{ labels:labels3, datasets:[{ data:vals3,
      backgroundColor:labels3.map(function(l,i){
        return (typeof state.custL3 === 'number' && state.custL3===keys3[i]) ? TERRA : BLUE;
      }),
      borderRadius:2, borderSkipped:false }] },
    options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
      onClick:function(evt, els){
        if(!els || !els.length) return;
        setCustL3(keys3[els[0].index]);
      },
      plugins:{ legend:{display:false},
        tooltip:{callbacks:{ label:function(c){
          var row = l3rows[c.dataIndex];
          return 'Parts billed ' + fmtEur(c.raw)
            + (row ? ' · step ' + fmtEur(row.step||0) : '');
        }}} },
      scales:{
        x:{ beginAtZero:true, grid:{color:'#eceae4'},
            title:{display:true, text:'Parts billed euro (this slice)', font:{size:11}, color:'#6b6459'},
            ticks:{callback:function(v){ return fmtEur(v); },font:{size:11}} },
        y:{ grid:{display:false}, ticks:{font:{size:11},color:NAVY} } },
      animation:{duration:250} }
  });
}

function custPnVal(r, key){
  /* cust_pn: [cust,l1,l2,l3,pn,qty,billed,prior,new,step] */
  if(key==='pn') return P.pn[r[4]] || '';
  if(key==='desc') return P.desc[r[4]] || '';
  if(key==='l2') return P.l2[r[2]] || '';
  if(key==='l3') return P.l3[r[3]] || '';
  if(key==='units') return r[5];
  if(key==='billed') return r[6];
  if(key==='prior') return r[7];
  if(key==='new') return r[8];
  if(key==='step') return r[9];
  if(key==='pct') return r[7]>0 ? 100*(r[8]/r[7]-1) : null;
  return r[9];
}
function custPnSortLabel(){
  var k = state.custPnSort.key;
  var hi = state.custPnSort.dir < 0;
  if(k==='pct') return hi
    ? 'Sorted by weighted % — highest increase first. Click Weighted again to flip.'
    : 'Sorted by weighted % — lowest first. Click Weighted again to flip.';
  if(k==='step') return hi
    ? 'Sorted by the euro step — largest cash move first. Click any header to change.'
    : 'Sorted by the euro step — smallest first. Click any header to change.';
  if(k==='billed') return 'Sorted by parts billed euro. Click any header to change.';
  if(k==='units') return 'Sorted by units. Click any header to change.';
  if(k==='prior' || k==='new') return 'Sorted by base euro. Click any header to change.';
  return 'Sorted alphabetically. Click any header to change.';
}

function drawCustPn(){
  var thead = document.querySelector('#cust-pn thead');
  var tbody = document.querySelector('#cust-pn tbody');
  document.getElementById('cust-crumb').innerHTML = custCrumbHtml();
  wireCustCrumb();
  var slice = scopeSliceLabel();

  function metricRow(label, o, onClick){
    var pct = o.pct===null||o.pct===undefined ? '—' : fmtPct(o.pct);
    return '<tr class="clickable"'+(onClick?' data-act="1"':'')+'>'
      +'<td>'+esc(label)+'</td>'
      +'<td class="n">'+fmtNum(o.pn||0)+'</td>'
      +'<td class="n">'+fmtEur(o.all||o.billed||0)+'</td>'
      +'<td class="n">'+fmtEur(o.step||0)+'</td>'
      +'<td class="n">'+pct+'</td></tr>';
  }

  /* L1 table */
  if(state.custL1 < 0){
    document.getElementById('t-cust-pn').textContent =
      'AIM level 1 for ' + slice;
    document.getElementById('q-cust-pn').textContent =
      'Click a family to open level 2.';
    var rows1 = rollupCustL1().filter(function(r){ return r.all > 0; });
    rows1.sort(function(a,b){
      var ag = /Not on AIM/.test(P.l1[a.l1]) ? 1 : 0;
      var bg = /Not on AIM/.test(P.l1[b.l1]) ? 1 : 0;
      if(ag !== bg) return ag - bg;
      return b.all - a.all;
    });
    thead.innerHTML = '<tr><th>AIM level 1</th><th class="n">Part numbers</th>'
      +'<th class="n">Parts billed</th><th class="n">Step €</th><th class="n">Weighted</th></tr>';
    if(!rows1.length){
      tbody.innerHTML = '<tr><td colspan="5" class="muted">No families for this selection.</td></tr>';
      return;
    }
    tbody.innerHTML = rows1.map(function(r){
      return metricRow(P.l1[r.l1], r, true);
    }).join('');
    Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function(tr, ix){
      tr.addEventListener('click', function(){ setCustL1(rows1[ix].l1); });
    });
    return;
  }

  /* L2 table */
  if(state.custL2 === null || state.custL2 === undefined){
    document.getElementById('t-cust-pn').textContent =
      'AIM level 2 inside ' + P.l1[state.custL1];
    document.getElementById('q-cust-pn').textContent =
      'Click a group to open level 3.';
    var rows2 = rollupCustL2({l1: state.custL1}).filter(function(r){ return r.all > 0; });
    rows2.sort(function(a,b){ return b.all-a.all; });
    thead.innerHTML = '<tr><th>AIM level 2</th><th class="n">Part numbers</th>'
      +'<th class="n">Parts billed</th><th class="n">Step €</th><th class="n">Weighted</th></tr>';
    if(!rows2.length){
      tbody.innerHTML = '<tr><td colspan="5" class="muted">No level-2 groups here.</td></tr>';
      return;
    }
    tbody.innerHTML = rows2.map(function(r){
      return metricRow(P.l2[r.l2], r, true);
    }).join('');
    Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function(tr, ix){
      tr.addEventListener('click', function(){ setCustL2(rows2[ix].l2); });
    });
    return;
  }

  /* L3 table */
  if(state.custL3 === null || state.custL3 === undefined){
    var l2title = state.custL2 === -1 ? 'All other groups' : P.l2[state.custL2];
    document.getElementById('t-cust-pn').textContent =
      'AIM level 3 inside ' + l2title;
    document.getElementById('q-cust-pn').textContent =
      'Click a type to list the part numbers.';
    var rows3 = rollupCustL3({l1: state.custL1, l2: state.custL2}).filter(function(r){ return r.all > 0; });
    rows3.sort(function(a,b){ return b.all-a.all; });
    thead.innerHTML = '<tr><th>AIM level 3</th><th class="n">Part numbers</th>'
      +'<th class="n">Parts billed</th><th class="n">Step €</th><th class="n">Weighted</th></tr>';
    if(!rows3.length){
      tbody.innerHTML = '<tr><td colspan="5" class="muted">No level-3 types here.</td></tr>';
      return;
    }
    tbody.innerHTML = rows3.map(function(r){
      return metricRow(P.l3[r.l3], r, true);
    }).join('');
    Array.prototype.forEach.call(tbody.querySelectorAll('tr'), function(tr, ix){
      tr.addEventListener('click', function(){ setCustL3(rows3[ix].l3); });
    });
    return;
  }

  /* Part-number table */
  document.getElementById('t-cust-pn').textContent =
    'Which part numbers move most inside ' + P.l3[state.custL3] + '?';
  var allowL2 = null;
  if(state.custL2 === -1){
    allowL2 = {};
    (state.custOther||[]).forEach(function(x){ allowL2[x]=true; });
  }
  var rows = [];
  if(state.cust < 0){
    /* Network / DB PN grain — reuse db_pn with temporary L scope. */
    var saved = {l1:state.l1, l2:state.l2, l3:state.l3};
    state.l1 = state.custL1;
    state.l2 = state.custL2 === -1 ? -1 : state.custL2;
    state.l3 = state.custL3;
    var netPn = rollupDbPn();
    if(state.custL2 === -1 && allowL2){
      /* rollupDbPn uses exact l2; for "other groups" scan db_pn manually. */
      netPn = [];
      var mapPn = {};
      var srcDb = D.db_pn || [];
      for(var di=0; di<srcDb.length; di++){
        var dr = srcDb[di];
        if(state.db>=0 && dr[0]!==state.db) continue;
        if(state.src>=0 && dr[4]!==state.src) continue;
        if(dr[1]!==state.custL1) continue;
        if(!allowL2[dr[2]]) continue;
        if(dr[3]!==state.custL3) continue;
        var pni = dr[5];
        var oo = mapPn[pni];
        if(!oo){ oo={pn:pni, qty:0, billed:0, prior:0, new:0, step:0}; mapPn[pni]=oo; }
        oo.qty+=dr[6]; oo.billed+=dr[7]; oo.prior+=dr[8]; oo.new+=dr[9]; oo.step+=dr[10];
      }
      for(var pk in mapPn){
        var o3 = mapPn[pk];
        o3.pct = o3.prior>0 ? 100*(o3.new/o3.prior-1) : null;
        netPn.push(o3);
      }
    }
    state.l1 = saved.l1; state.l2 = saved.l2; state.l3 = saved.l3;
    /* Adapt to cust_pn row shape for sorting helpers: [cust,l1,l2,l3,pn,qty,billed,prior,new,step] */
    rows = netPn.map(function(r){
      return [-1, state.custL1,
        state.custL2 === -1 ? -1 : state.custL2,
        state.custL3, r.pn, r.qty, r.billed, r.prior, r.new, r.step];
    });
  } else {
    var src = D.cust_pn || [];
    for(var i=0;i<src.length;i++){
      var r = src[i];
      if(r[0]!==state.cust) continue;
      if(r[1]!==state.custL1) continue;
      if(state.custL2 === -1){ if(!allowL2[r[2]]) continue; }
      else if(r[2]!==state.custL2) continue;
      if(r[3]!==state.custL3) continue;
      rows.push(r);
    }
  }
  var sk = state.custPnSort.key, sd = state.custPnSort.dir;
  rows.sort(function(a,b){
    var av = custPnVal(a, sk), bv = custPnVal(b, sk);
    if(av===null || av===undefined) av = (typeof bv==='string' ? '' : -1e99);
    if(bv===null || bv===undefined) bv = (typeof av==='string' ? '' : -1e99);
    if(typeof av==='string'){
      var cmp = String(av).localeCompare(String(bv), undefined, {sensitivity:'base'});
      return sd < 0 ? -cmp : cmp;
    }
    if(av===bv) return b[9]-a[9];
    return sd < 0 ? (bv-av) : (av-bv);
  });
  document.getElementById('q-cust-pn').textContent = custPnSortLabel();
  thead.innerHTML = '<tr>' + [
    ['pn','Part number',false],['desc','Description as billed',false],['l3','AIM level 3',false],
    ['units','Units',true],['billed','Parts billed',true],['prior','Prior base',true],
    ['new','New base',true],['step','Step €',true],['pct','Weighted',true]
  ].map(function(c){
    var key=c[0], label=c[1], num=c[2];
    var on = sk===key;
    var cls = [];
    if(num) cls.push('n');
    if(on) cls.push('on');
    var mark = on ? (sd<0 ? ' ↓' : ' ↑') : '';
    return '<th'+(cls.length?' class="'+cls.join(' ')+'"':'')+' data-sort="'+key+'">'
      +label+'<span class="sortmark">'+mark+'</span></th>';
  }).join('') + '</tr>';

  Array.prototype.forEach.call(thead.querySelectorAll('th[data-sort]'), function(el){
    el.addEventListener('click', function(){
      var key = el.getAttribute('data-sort');
      if(state.custPnSort.key === key){
        state.custPnSort.dir *= -1;
      } else {
        state.custPnSort.key = key;
        state.custPnSort.dir = (key==='pn'||key==='desc'||key==='l3') ? 1 : -1;
      }
      drawCustPn();
    });
  });

  if(!rows.length){
    tbody.innerHTML = '<tr><td colspan="9" class="muted">No priced part numbers for this selection.</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(function(r){
    var pct = r[7]>0 ? 100*(r[8]/r[7]-1) : null;
    return '<tr><td>'+esc(P.pn[r[4]])+'</td><td>'+esc(P.desc[r[4]]||'')+'</td>'
      +'<td>'+esc(P.l3[r[3]])+'</td>'
      +'<td class="n">'+fmtNum(Math.round(r[5]))+'</td>'
      +'<td class="n">'+fmtEur(r[6])+'</td>'
      +'<td class="n">'+fmtEur(r[7])+'</td>'
      +'<td class="n">'+fmtEur(r[8])+'</td>'
      +'<td class="n">'+fmtEur(r[9])+'</td>'
      +'<td class="n">'+fmtPct(pct)+'</td></tr>';
  }).join('');
}

/* ---------- brake deep dive ---------- */
var BRAKE = 'Brakes', BRAKE_L1 = -1;
function brakeL1Index(){
  if(BRAKE_L1 < 0) BRAKE_L1 = P.l1.indexOf(BRAKE);
  return BRAKE_L1;
}
function brakeConc(){
  var c = D.conc_brake || {};
  var key = state.db < 0 ? '__net__' : P.db[state.db];
  return c[key] || null;
}
/* Sum the level 2 groups for the current distributor and source, from groups. */
function brakeL2Rows(){
  var l1 = brakeL1Index();
  if(l1 < 0) return [];
  return rollup([1,2], {l1:l1}).map(function(r){
    return {l2:r.kk[1], pn:r.pn, rows:r.rows, qty:r.qty, billed:r.billed,
      prior:r.prior, new:r.new, step:r.step, all:r.all, pct:r.pct};
  });
}
function brakeTotals(){ return sumMetricRows(brakeL2Rows()); }
/* brake_pn: [db,src,l2,pn,prior_jpy,new_jpy,qty,billed,step] */
function brakePnRows(){
  var l1 = brakeL1Index();
  if(l1 < 0) return [];
  var rows = D.brake_pn || [], out = [];
  for(var i=0;i<rows.length;i++){
    var r = rows[i];
    if(state.db>=0 && r[0]!==state.db) continue;
    if(state.src>=0 && r[1]!==state.src) continue;
    if(state.brakeL2!==null && state.brakeL2!==undefined && r[2]!==state.brakeL2) continue;
    out.push(r);
  }
  return out;
}
function brakeSliceLabel(){
  var s = (state.db<0 ? 'the network' : P.db[state.db]);
  if(state.src>=0) s += ' / ' + P.src[state.src];
  if(state.brakeL2!==null && state.brakeL2!==undefined) s += ' · ' + P.l2[state.brakeL2];
  return s;
}
function drawBrake(){
  var l1 = brakeL1Index();
  if(l1 < 0) return;
  var slice = brakeSliceLabel();
  var rows = brakeL2Rows();
  var t = sumMetricRows(rows);
  var conc = brakeConc();
  var ituk = (state.db>=0 && P.db[state.db]==='ITUK');

  document.getElementById('t-brake').textContent = 'Inside brakes: which sub-group and which part number?'
    + (ituk ? ' (ITUK)' : '');
  document.getElementById('q-brake').textContent =
    'Brakes is one bar in the family league, so it is opened here: the level 2 groups first, then the '
    + 'part numbers behind the biggest moves. Scope is ' + slice + '. The euro step and the weighted '
    + 'move are both on the level 2 lines, so a sub-group that adds a lot of cash and one that moves a '
    + 'small base by a large percentage cannot be confused.';

  var figs = '';
  figs += '<div class="fig t"><div class="fv">'+fmtPct(t.pct)
    +'<span class="info" tabindex="0">i<span class="tip">Sum of units x new base divided by sum of '
    +'units x prior base, minus one, across every priced brake line in this scope. Only lines carrying '
    +'a price on both sides.</span></span></div>'
    +'<div class="fl">Brake family, weighted move</div>'
    +'<div class="fn">'+esc(slice)+'</div></div>';
  figs += '<div class="fig"><div class="fv">'+fmtEur(t.step)
    +'<span class="info" tabindex="0">i<span class="tip">Units x (new base - prior base) at '
    +D.fx+' JPY per EUR, summed over the brake family for this scope.</span></span></div>'
    +'<div class="fl">Brake step euro</div>'
    +'<div class="fn">'+fmtNum(t.rows)+' priced lines · '+fmtNum(t.pn)+' part numbers</div></div>';
  figs += '<div class="fig"><div class="fv">'+fmtEur(t.prior)
    +'</div><div class="fl">Prior base</div>'
    +'<div class="fn">the base the move is measured against</div></div>';
  figs += '<div class="fig"><div class="fv">'+fmtEur(t.all)
    +'<span class="info" tabindex="0">i<span class="tip">Every brake line in scope, priced or not. '
    +'The weighted move uses only lines priced on both sides.</span></span></div>'
    +'<div class="fl">Brake parts billed</div>'
    +'<div class="fn">all in scope, priced or not</div></div>';
  if(conc && conc.half){
    figs += '<div class="fig t"><div class="fv">'+fmtNum(conc.half)
      +'<span class="info" tabindex="0">i<span class="tip">Brake part numbers counted from the largest '
      +'step down until half of the brake step euro is reached. Part numbers that did not move are '
      +'left out of the count.</span></span></div>'
      +'<div class="fl">Carry half the brake step</div>'
      +'<div class="fn">of '+fmtNum(conc.n)+' brake part numbers</div></div>';
  }
  document.getElementById('brake-figs').innerHTML = figs;
  drawBrakeL2(rows, t);
  drawBrakePn();
  drawBrakeChart(rows);
}
function drawBrakeL2(rows, t){
  rows.sort(function(a,b){ return b.step-a.step; });
  document.querySelector('#brake-l2 thead').innerHTML =
    '<tr><th>AIM level 2 inside Brakes</th><th class="n">Part numbers</th>'
    +'<th class="n">Lines</th><th class="n">Parts billed</th><th class="n">Prior base</th>'
    +'<th class="n">New base</th><th class="n">Step €</th><th class="n">Weighted</th>'
    +'<th class="n">Share of brake step</th></tr>';
  var tb = document.querySelector('#brake-l2 tbody');
  if(!rows.length){
    tb.innerHTML = '<tr><td colspan="9" class="muted">No priced brake lines for this selection.</td></tr>';
    return;
  }  tb.innerHTML = rows.map(function(r){
    var sel = (state.brakeL2===r.l2);
    var share = t.step>0 ? 100*r.step/t.step : null;
    return '<tr class="clickable'+(sel?' sel':'')+'" data-l2="'+r.l2+'">'
      +'<td>'+esc(P.l2[r.l2] || '')+'</td>'
      +'<td class="n">'+fmtNum(r.pn)+'</td>'
      +'<td class="n">'+fmtNum(r.rows)+'</td>'
      +'<td class="n">'+fmtEur(r.all)+'</td>'
      +'<td class="n">'+fmtEur(r.prior)+'</td>'
      +'<td class="n">'+fmtEur(r.new)+'</td>'
      +'<td class="n">'+fmtEur(r.step)+'</td>'
      +'<td class="n">'+fmtPct(r.pct)+'</td>'
      +'<td class="n">'+fmtPct(share,1)+'</td></tr>';
  }).join('');
  Array.prototype.forEach.call(tb.querySelectorAll('tr'), function(tr){
    tr.addEventListener('click', function(){
      var l2 = Number(tr.getAttribute('data-l2'));
      state.brakeL2 = (state.brakeL2 === l2) ? null : l2;
      render();
    });
  });
}
/* Part numbers behind the biggest brake moves: those of the level 2 group
   selected in the table above, or the whole brake family when none is selected. */
function drawBrakePn(){
  document.getElementById('brake-crumb').innerHTML =
    '<b>Part numbers: ' + ((state.brakeL2===null||state.brakeL2===undefined)
      ? 'all brake groups'
      : '<span id="brake-back">'+esc(P.l2[state.brakeL2])
        +' — click to go back to all groups</span>')
    + '</b>';
  var backEl = document.getElementById('brake-back');
  if(backEl) backEl.addEventListener('click', function(){ state.brakeL2 = null; render(); });
  var pns = brakePnRows();
  /* One row per part number for the scope, not one per distributor: the same pad
     kit is billed in thirteen markets and must not appear thirteen times in a
     ranking. Base prices sit on the part number, so they are taken as-is; units,
     euro and step are added up across the distributors that carry it. */
  var byPn = {}, order = [];
  for(var i=0;i<pns.length;i++){
    var r = pns[i];
    var o = byPn[r[3]];
    if(!o){
      o = {pn:r[3], l2:r[2], prior:r[4], new:r[5], qty:0, billed:0, step:0,
           dbs:{}, dbN:0};
      byPn[r[3]] = o; order.push(o);
    }
    o.qty += r[6]; o.billed += r[7]; o.step += r[8];
    if(!o.dbs[r[0]]){ o.dbs[r[0]] = 1; o.dbN += 1; }
  }
  pns = order;
  var sk = state.brakePnSort.key, sd = state.brakePnSort.dir;
  function val(r, key){
    if(key==='pn') return P.pn[r.pn] || '';
    if(key==='desc') return P.desc[r.pn] || '';
    if(key==='l2') return P.l2[r.l2] || '';
    if(key==='units') return r.qty;
    if(key==='billed') return r.billed;
    if(key==='prior') return r.prior;
    if(key==='new') return r.new;
    if(key==='dbs') return r.dbN;
    if(key==='pct') return r.prior>0 ? 100*(r.new/r.prior-1) : null;
    return r.step;
  }
  pns.sort(function(a,b){
    var av = val(a,sk), bv = val(b,sk);
    if(av===null||av===undefined) av = (typeof bv==='string' ? '' : -1e99);
    if(bv===null||bv===undefined) bv = (typeof av==='string' ? '' : -1e99);
    if(typeof av==='string'){
      var cmp = String(av).localeCompare(String(bv), undefined, {sensitivity:'base'});
      return sd<0 ? -cmp : cmp;
    }
    if(av===bv) return b.step-a.step;
    return sd<0 ? (bv-av) : (av-bv);
  });
  drawBrakePnHead(sk, sd);
  Array.prototype.forEach.call(
    document.querySelectorAll('#brake-pn thead th[data-sort]'), function(el){
    el.addEventListener('click', function(){
      var key = el.getAttribute('data-sort');
      if(state.brakePnSort.key===key) state.brakePnSort.dir *= -1;
      else {
        state.brakePnSort.key = key;
        state.brakePnSort.dir = (key==='pn'||key==='desc'||key==='l2') ? 1 : -1;
      }
      drawBrakePn();
    });
  });
  document.querySelector('#brake-pn tbody').innerHTML = pns.length ? pns.map(function(r){
    var pct = r.prior>0 ? 100*(r.new/r.prior-1) : null;
    return '<tr><td>'+esc(P.pn[r.pn])+'</td><td>'+esc(P.desc[r.pn]||'')+'</td>'
      +'<td>'+esc(P.l2[r.l2]||'')+'</td>'
      +'<td class="n">'+fmtNum(Math.round(r.qty))+'</td>'
      +'<td class="n">'+fmtEur(r.billed)+'</td>'
      +'<td class="n">'+fmtNum(r.prior)+'</td>'
      +'<td class="n">'+fmtNum(r.new)+'</td>'
      +'<td class="n">'+fmtEur(r.step)+'</td>'
      +'<td class="n">'+fmtPct(pct)+'</td>'
      +'<td class="n">'+fmtNum(r.dbN)+'</td></tr>';
  }).join('') : '<tr><td colspan="10" class="muted">No priced brake part numbers for this selection.</td></tr>';
}
function drawBrakePnHead(sk, sd){
  document.querySelector('#brake-pn thead').innerHTML = '<tr>' + [
    ['pn','Part number',false],['desc','Description as billed',false],['l2','AIM level 2',false],
    ['units','Units',true],['billed','Parts billed',true],['prior','Prior base JPY',true],
    ['new','New base JPY',true],['step','Step €',true],['pct','Weighted',true],
    ['dbs','Distributors',true]
  ].map(function(c){
    var key=c[0], label=c[1], num=c[2];
    var on = sk===key, cls = [];
    if(num) cls.push('n');
    if(on) cls.push('on');
    var mark = on ? (sd<0 ? ' ↓' : ' ↑') : '';
    return '<th'+(cls.length?' class="'+cls.join(' ')+'"':'')+' data-sort="'+key+'">'
      +label+'<span class="sortmark">'+mark+'</span></th>';
  }).join('') + '</tr>';
}
function drawBrakeChart(rows){
  /* Part-to-whole of the brake step across the level 2 groups. Three named groups
     plus a combined remainder stays inside the four-segment limit; the ranking is
     left to the table above, which carries all eight groups. */
  var named = rows.slice(0,3);
  var restE = rows.slice(3).reduce(function(s,r){ return s+r.step; },0);
  var labels = named.map(function(r){ return P.l2[r.l2]; });
  var vals = named.map(function(r){ return r.step; });
  if(restE>0){ labels.push('All other groups'); vals.push(restE); }
  if(!vals.length){ labels = ['No priced brake lines']; vals = [1]; }
  var tot = vals.reduce(function(a,b){ return a+b; },0);
  chart('c-brake', {
    type:'doughnut',
    data:{ labels:labels, datasets:[{ data:vals,
      backgroundColor:[NAVY,TERRA,SAND,GREY], borderColor:'#fff', borderWidth:2 }] },
    options:{ responsive:true, maintainAspectRatio:false, cutout:'52%',
      plugins:{ legend:{position:'bottom',labels:{font:{size:12},boxWidth:12,padding:12}},
        tooltip:{callbacks:{ label:function(c){
          return c.label + ': ' + fmtEur(c.raw) + ' (' + fmtPct(100*c.raw/tot,1)
            + ' of the brake step)'; }}} } },
    plugins:[{ id:'brakeCentre', afterDraw:function(ch){
      var g=ch.ctx; g.save(); g.textAlign='center'; g.textBaseline='middle';
      var x=(ch.chartArea.left+ch.chartArea.right)/2, y=(ch.chartArea.top+ch.chartArea.bottom)/2-6;
      g.fillStyle=NAVY; g.font='600 17px Georgia, serif';
      g.fillText(fmtEur(tot), x, y);
      g.fillStyle='#6b6459'; g.font='11px sans-serif';
      g.fillText('brake step', x, y+17); g.restore();
    }}]
  });
}
/* ---------- step concentration ---------- */
var concScope = 'all';
function concNow(){
  var set = (/brake/.test(concScope) ? (D.conc_brake||{}) : (D.conc_all||{}));
  var key = state.db < 0 ? '__net__' : P.db[state.db];
  return { c: set[key] || null, key: key };
}
function drawConc(){
  var got = concNow(), c = got.c;
  var isBrake = /brake/.test(concScope);
  var named = (got.key === '__net__') ? 'the network' : got.key;
  document.getElementById('t-conc').textContent = isBrake
    ? 'How few brake part numbers carry the increase?'
    : 'How few part numbers carry the increase?';
  document.getElementById('q-conc').textContent =
    'Every priced part number for ' + named + (isBrake ? ', brake family only,' : '')
    + ' ranked by its euro step and added up from the largest down. The curve is the share of the '
    + 'total step the biggest part numbers carry; the two figures are where half and eighty per cent '
    + 'of the step is reached. Part numbers that did not move carry no step and are left out of the '
    + 'count, so they do not pad it.';

  var figs = '';
  if(!c || !c.n){
    figs = '<div class="fig"><div class="fv">—</div>'
      +'<div class="fl">No priced step for this selection</div></div>';
    document.getElementById('conc-figs').innerHTML = figs;
    return;
  }
  figs += '<div class="fig t"><div class="fv">'+fmtNum(c.half)
    +'<span class="info" tabindex="0">i<span class="tip">Counted from the largest step down until '
    +'half of the total step euro is reached. Part numbers that did not move are not counted.</span>'
    +'</span></div>'
    +'<div class="fl">Part numbers carry half of the step</div>'
    +'<div class="fn">half of '+fmtEur(c.total)+'</div></div>';
  figs += '<div class="fig t"><div class="fv">'+fmtNum(c.eighty)
    +'<span class="info" tabindex="0">i<span class="tip">Counted from the largest step down until '
    +'eighty per cent of the total step euro is reached.</span></span></div>'
    +'<div class="fl">Part numbers carry eighty per cent</div>'
    +'<div class="fn">of '+fmtEur(c.total)+'</div></div>';
  figs += '<div class="fig"><div class="fv">'+fmtNum(c.positive)
    +'</div><div class="fl">Part numbers moved up</div>'
    +'<div class="fn">of '+fmtNum(c.n)+' carrying a step</div></div>';
  figs += '<div class="fig"><div class="fv">'+fmtEur(c.total)
    +'</div><div class="fl">Total step</div>'
    +'<div class="fn">'+esc(named)+(isBrake?' · brakes':' · all families')+'</div></div>';
  document.getElementById('conc-figs').innerHTML = figs;

  var pts = c.curve || [];
  var labels = pts.map(function(p){ return p[0]; });
  var vals = pts.map(function(p){ return p[1]; });
  chart('c-conc', {
    type:'line',
    data:{ labels:labels, datasets:[
      { label:'Share of the total step carried', data:vals, borderColor:TERRA,
        backgroundColor:'rgba(192,85,45,.16)', fill:true, tension:.25,
        pointRadius:pts.map(function(p){ return p[0]<=12 ? 3 : 0; }),
        pointBackgroundColor:TERRA, borderWidth:2, pointHoverRadius:4 },
      { label:'Half of the step', data:labels.map(function(){ return 50; }),
        borderColor:NAVY, borderDash:[6,4], borderWidth:1.5, pointRadius:0, fill:false },
      { label:'Eighty per cent', data:labels.map(function(){ return 80; }),
        borderColor:GREY, borderDash:[3,3], borderWidth:1.5, pointRadius:0, fill:false }
    ] },
    options:{ responsive:true, maintainAspectRatio:false,
      interaction:{mode:'index', intersect:false},
      plugins:{ legend:{position:'bottom',labels:{font:{size:12},boxWidth:12}},
        tooltip:{callbacks:{
          title:function(items){ return fmtNum(items[0].label) + ' part numbers in'; },
          label:function(ctx){
            if(ctx.datasetIndex===0) return fmtPct(ctx.raw,1) + ' of the total step';
            return ctx.dataset.label;
          }}}},
      scales:{
        x:{ grid:{display:false},
            title:{display:true, text:'Part numbers, largest step first',
              font:{size:11}, color:'#6b6459'},
            ticks:{font:{size:11}, maxRotation:0, autoSkip:true, maxTicksLimit:14} },
        y:{ beginAtZero:true, suggestedMax:100, grid:{color:'#eceae4'},
            title:{display:true, text:'Cumulative share of the step',
              font:{size:11}, color:'#6b6459'},
            ticks:{callback:function(v){ return v+'%'; },font:{size:11}} } },
      animation:{duration:250} }
  });
}
/* ---------- KPI chips ---------- */
function kpis(t){
  var scope;
  if(state.cust >= 0){
    scope = custLabel(state.cust)
      + (state.src<0? '' : ' / ' + P.src[state.src]);
  } else {
    scope = (state.db<0? 'the network' : P.db[state.db]) +
            (state.src<0? '' : ' / ' + P.src[state.src]);
  }
  if(aimDrillActive()){
    scope += ' · ' + P.l1[state.custL1];
    if(state.custL2 === -1) scope += ' · All other groups';
    else if(typeof state.custL2 === 'number' && state.custL2 >= 0) scope += ' · ' + P.l2[state.custL2];
    if(typeof state.custL3 === 'number' && state.custL3 >= 0) scope += ' · ' + P.l3[state.custL3];
  }
  var l3share = D.coverage.l3_pct;
  var el = document.getElementById('kpis');
  el.innerHTML =
  '<div class="kpi t"><div class="lab">Weighted increase'
   +'<span class="info" tabindex="0">i<span class="tip">Sum of (units x new base price) divided by '
   +'sum of (units x prior base price), minus one. Only lines carrying a price on both sides. '
   +'No elasticity, no revenue effect.</span></span></div>'
   +'<div class="val">'+fmtPct(t.pct)+'</div>'
   +'<div class="note">'+esc(scope)+'</div></div>'
  +'<div class="kpi"><div class="lab">Step euro'
   +'<span class="info" tabindex="0">i<span class="tip">Units x (new base price - prior base price), '
   +'valued at '+D.fx+' JPY per EUR. This is the cash on the price move, not extra revenue.</span></span></div>'
   +'<div class="val">'+fmtEur(t.step)+'</div>'
   +'<div class="note">'+fmtNum(t.rows)+' in-scope lines</div></div>'
  +'<div class="kpi"><div class="lab">Parts billed (all in scope)'
   +'<span class="info" tabindex="0">i<span class="tip">Every in-scope line for this selection, priced or not. '
   +'Network book is '+fmtEur(D.totals.billed||D.in_scope.billed)+'; the priced-only book used for '
   +'weighted % is '+fmtEur(D.totals.priced_billed||D.in_scope.priced_billed)+'. This chip is the full book.</span></span></div>'
   +'<div class="val">'+fmtEur(t.all)+'</div>'
   +'<div class="note">'+fmtNum(t.pn)+' part numbers · not priced-only</div></div>'
  +'<div class="kpi"><div class="lab">Step per €1m billed'
   +'<span class="info" tabindex="0">i<span class="tip">Step euro divided by in-scope parts billed euro, x 1,000,000. '
   +'Normalises the move so a small market and a large one can be compared on the same axis.</span></span></div>'
   +'<div class="val">'+ (t.all>0 ? fmtEur(1000000*t.step/t.all) : '—') +'</div>'
   +'<div class="note">rise per million of parts billed</div></div>'
  +'<div class="kpi"><div class="lab">Source of supply held'
   +'<span class="info" tabindex="0">i<span class="tip">Share of in-scope parts billed euro where the '
   +'supplying entity (Japan through IML, Thailand through IMIT) is recorded. The rest is kept in every '
   +'total and shown as not held. Network figure — does not change with the selection.</span></span></div>'
   +'<div class="val">'+fmtPct(D.coverage.source_pct,1)+'</div>'
   +'<div class="note">of network parts billed euro</div></div>'
  +'<div class="kpi"><div class="lab">AIM level 3 filled'
   +'<span class="info" tabindex="0">i<span class="tip">Share of in-scope parts billed euro carrying a '
   +'level 3 type. The remainder is shown as its own row, never hidden. Network figure.</span></span></div>'
   +'<div class="val">'+fmtPct(l3share,1)+'</div>'
   +'<div class="note">of network parts billed euro</div></div>';
}

/* ---------- charts ---------- */
var charts = {};
window.charts = charts;
function chart(id, cfg){ if(charts[id]) charts[id].destroy(); charts[id] = new Chart(id, cfg); }

function metricOf(o){
  /* Parts billed metric = in-scope euro (o.all), not priced-only o.billed. */
  return state.metric==='pct' ? o.pct : (state.metric==='step'? o.step : o.all);
}
function metricLabel(){ return state.metric==='pct' ? 'Weighted increase'
  : (state.metric==='step' ? 'Step euro' : 'Parts billed euro (in scope)'); }
function fmtMetric(v){ if(state.metric==='pct') return fmtPct(v); return fmtEur(v); }

function drawLeague(){
  /* Group by distributor index (customer row field 2). */
  var rows = rollupCustomers([2]);
  rows.sort(function(a,b){ return metricOf(b)-metricOf(a); });
  /* Network benchmark on the same metric (keep source filter, clear DB + customer). */
  var savedDb = state.db, savedCust = state.cust;
  state.db = -1; state.cust = -1;
  var net = totalsNow();
  state.db = savedDb; state.cust = savedCust;
  var ref = metricOf(net);
  var labels = rows.map(function(r){ return P.db[r.kk[0]]; });
  var vals = rows.map(metricOf);
  /* One distributor alone: show it next to Network as a second bar. */
  if(labels.length === 1){
    labels = [labels[0], 'Network'];
    vals = [vals[0], ref];
  }
  var max = Math.max.apply(null, vals.concat([ref, 0.0001]));
  document.getElementById('q-league').textContent =
    metricLabel() + ' per distributor' + (state.src<0? '' : ', ' + P.src[state.src]) +
    '. The dashed line is the network figure'
    + (labels.indexOf('Network')>=0 ? '; with one distributor selected, Network is also a bar.' : '.');
  chart('c-league', {
    type:'bar',
    data:{ labels:labels, datasets:[{ data:vals,
      backgroundColor:labels.map(function(l){ return l==='Network' ? NAVY : TERRA; }),
      borderRadius:2, borderSkipped:false }] },
    options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false},
        tooltip:{callbacks:{ label:function(c){ return fmtMetric(c.raw); }}} },
      scales:{
        x:{ beginAtZero:true, suggestedMax:max*1.08, grid:{color:'#eceae4'},
            ticks:{callback:function(v){ return state.metric==='pct'? v+'%' : fmtEur(v); },font:{size:11}},
            title:{display:true,text:metricLabel(),font:{size:11},color:'#6b6459'} },
        y:{ grid:{display:false}, ticks:{font:{size:11.5},color:NAVY} } },
      animation:{duration:250}
    },
    plugins:[{
      id:'netRefLine',
      afterDraw:function(ch){
        if(ref===null || ref===undefined || isNaN(ref)) return;
        var x = ch.scales.x.getPixelForValue(ref);
        var top = ch.chartArea.top, bot = ch.chartArea.bottom;
        if(x < ch.chartArea.left || x > ch.chartArea.right) return;
        var g = ch.ctx;
        g.save();
        g.beginPath();
        g.setLineDash([6,4]);
        g.strokeStyle = NAVY;
        g.lineWidth = 1.5;
        g.moveTo(x, top);
        g.lineTo(x, bot);
        g.stroke();
        g.restore();
      }
    }]
  });
}

function drawL1(){
  var rows = rollup([1]);
  rows.sort(function(a,b){ return metricOf(b)-metricOf(a); });
  var labels = rows.map(function(r){ return P.l1[r.kk[0]]; });
  var vals = rows.map(metricOf);
  var colors = labels.map(function(l){ return /Not on AIM/.test(l)? GREY : BLUE; });
  document.getElementById('q-l1').textContent =
    metricLabel() + ' by AIM level 1 for the current selection. Grey is the part of the book '
    + 'that does not sit on the AIM spine.';
  chart('c-l1', {
    type:'bar',
    data:{ labels:labels, datasets:[{ data:vals, backgroundColor:colors, borderRadius:2,
      borderSkipped:false }] },
    options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false},
        tooltip:{callbacks:{ label:function(c){ return fmtMetric(c.raw); }}} },
      scales:{ x:{ beginAtZero:true, grid:{color:'#eceae4'},
          ticks:{callback:function(v){ return state.metric==='pct'? v+'%' : fmtEur(v); },font:{size:11}} },
        y:{ grid:{display:false}, ticks:{font:{size:11.5},color:NAVY} } },
      animation:{duration:250} }
  });
}

function drawMix(){
  /* Part-to-whole inside the selected level 1: a donut, capped at four named
     segments. Until a family is actually chosen, chart the biggest real family but
     do NOT write it into the state - the drill must stay at level 1 and the
     breadcrumb must keep saying Network. */
  var scopeL1 = state.l1;
  if(scopeL1 < 0){
    var cand = rollup([1]).filter(function(r){
      return !/Not on AIM/.test(P.l1[r.kk[0]]);
    });
    cand.sort(function(a,b){ return b.all-a.all; });
    if(cand.length){ scopeL1 = cand[0].kk[0]; }
  }
  var fam = rollup([2], {l1: scopeL1}).filter(function(r){
    return r.all > 0 && !/Not classified at L3/.test(P.l2[r.kk[0]]);
  });
  fam.sort(function(a,b){ return b.all-a.all; });
  var head = fam.slice(0,3);
  var restE = fam.slice(3).reduce(function(s,r){ return s+r.all; },0);
  var labels = head.map(function(r){ return P.l2[r.kk[0]]; });
  var vals = head.map(function(r){ return r.all; });
  if(restE>0){ labels.push('All other groups'); vals.push(restE); }
  if(!vals.length){ labels = ['No data for this selection']; vals = [1]; }
  var famName = scopeL1 >= 0 ? P.l1[scopeL1] : 'the network';
  var chosen = state.l1 >= 0;
  document.getElementById('t-mix').textContent =
    (chosen ? 'Where the parts billed euro sits inside ' : 'The biggest family: ') + famName;
  document.getElementById('q-mix').textContent =
    'Split by level 2 group, for the current distributor and source. Top three groups named, the rest '
    + 'combined, so the segments stay readable.'
    + (chosen ? '' : ' Click a family in the drill below to move this chart onto it.');
  chart('c-mix', {
    type:'doughnut',
    data:{ labels:labels, datasets:[{ data:vals,
      backgroundColor:[NAVY,TERRA,SAND,GREY], borderColor:'#fff', borderWidth:2 }] },
    options:{ responsive:true, maintainAspectRatio:false, cutout:'52%',
      plugins:{ legend:{position:'bottom',labels:{font:{size:12},boxWidth:12,padding:12}},
        tooltip:{callbacks:{ label:function(c){
          var tot = c.dataset.data.reduce(function(a,b){return a+b;},0);
          return c.label + ': ' + fmtEur(c.raw) + ' (' + fmtPct(100*c.raw/tot,1) + ')'; }}} } },
    plugins:[{ id:'centre', afterDraw:function(ch){
      var g=ch.ctx; g.save(); g.textAlign='center'; g.textBaseline='middle';
      var x=(ch.chartArea.left+ch.chartArea.right)/2, y=(ch.chartArea.top+ch.chartArea.bottom)/2-6;
      g.fillStyle=NAVY; g.font='600 17px Georgia, serif';
      g.fillText(fmtEur(vals.reduce(function(a,b){return a+b;},0)), x, y);
      g.fillStyle='#6b6459'; g.font='11px sans-serif';
      g.fillText('parts billed', x, y+17); g.restore();
    }}]
  });
}

function drawSrc(){
  /* same families, two supply routes: paired bars, not two pies */
  var rows = rollup([1,4]);
  var byFam = {};
  rows.forEach(function(r){
    var f = r.kk[0], s = r.kk[1];
    byFam[f] = byFam[f] || {};
    byFam[f][s] = r;
  });
  var fams = Object.keys(byFam).map(Number);
  fams.sort(function(a,b){
    var sa = 0, sb = 0;
    for(var k in byFam[a]) sa += byFam[a][k].step;
    for(var k2 in byFam[b]) sb += byFam[b][k2].step;
    return sb-sa; });
  fams = fams.slice(0,10);
  var jp = [], th = [];
  fams.forEach(function(f){
    var j = null, t = null;
    for(var k in byFam[f]){ if(/Japan/.test(P.src[k])) j = byFam[f][k]; if(/Thailand/.test(P.src[k])) t = byFam[f][k]; }
    jp.push(j ? metricOf(j) : null);
    th.push(t ? metricOf(t) : null);
  });
  document.getElementById('q-src').textContent =
    metricLabel() + ' on the ten biggest AIM families, Japan (supplied through IML) against '
    + 'Thailand (through IMIT). A family with no bar on one side is not supplied by that route.';
  chart('c-src', {
    type:'bar',
    data:{ labels:fams.map(function(f){ return P.l1[f]; }),
      datasets:[
        { label:'JP - Japan (IML)', data:jp, backgroundColor:BLUE, borderRadius:2, borderSkipped:false },
        { label:'TH - Thailand (IMIT)', data:th, backgroundColor:SAND, borderRadius:2, borderSkipped:false }
      ] },
    options:{ indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{position:'bottom',labels:{font:{size:12},boxWidth:12}},
        tooltip:{callbacks:{ label:function(c){
          return c.dataset.label + ': ' + (state.metric==='pct'? fmtPct(c.raw) : fmtEur(c.raw)); }}} },
      scales:{ x:{ beginAtZero:true, grid:{color:'#eceae4'},
          ticks:{callback:function(v){ return state.metric==='pct'? v+'%' : fmtEur(v); },font:{size:11}} },
        y:{ grid:{display:false}, ticks:{font:{size:11},color:NAVY} } },
      animation:{duration:250} }
  });
}

/* ---------- drill table ---------- */
function rollupDbPn(){
  /* db_pn: [db,l1,l2,l3,src,pn,qty,billed,prior,new,step] — network L3 → PN. */
  var map = {};
  var rows = D.db_pn || [];
  for(var i=0;i<rows.length;i++){
    var r = rows[i];
    if(state.db>=0 && r[0]!==state.db) continue;
    if(state.src>=0 && r[4]!==state.src) continue;
    if(state.l1>=0 && r[1]!==state.l1) continue;
    if(state.l2>=0 && r[2]!==state.l2) continue;
    if(state.l3>=0 && r[3]!==state.l3) continue;
    var pn = r[5];
    var o = map[pn];
    if(!o){ o={pn:pn, qty:0, billed:0, prior:0, new:0, step:0}; map[pn]=o; }
    o.qty += r[6]; o.billed += r[7]; o.prior += r[8]; o.new += r[9]; o.step += r[10];
  }
  var out = [];
  for(var k in map){
    var o2 = map[k];
    o2.pct = o2.prior>0 ? 100*(o2.new/o2.prior-1) : null;
    out.push(o2);
  }
  return out;
}

function drawDrill(){
  /* Clicking a row sets the scope. Level 4 = part numbers inside the chosen L3 type. */
  var level = state.l1<0 ? 1 : (state.l2<0 ? 2 : (state.l3<0 ? 3 : 4));
  var tb = document.querySelector('#drill tbody');
  var thead = document.querySelector('#drill thead');

  if(level===4){
    var pnRows = rollupDbPn();
    var sk = state.drillPnSort.key, sd = state.drillPnSort.dir;
    pnRows.sort(function(a,b){
      var av = sk==='pn' ? String(P.pn[a.pn]||'') : (sk==='desc' ? String(P.desc[a.pn]||'') : a[sk]);
      var bv = sk==='pn' ? String(P.pn[b.pn]||'') : (sk==='desc' ? String(P.desc[b.pn]||'') : b[sk]);
      if(av===bv) return 0;
      if(av===null||av===undefined) return 1;
      if(bv===null||bv===undefined) return -1;
      if(av<bv) return -1*sd;
      return 1*sd;
    });
    var mark = function(key){
      return state.drillPnSort.key===key ? (state.drillPnSort.dir<0?' ▼':' ▲') : '';
    };
    thead.innerHTML =
      '<tr><th class="sortable" data-k="pn">Part number'+mark('pn')+'</th>'
      +'<th class="sortable" data-k="desc">Description as billed'+mark('desc')+'</th>'
      +'<th class="n sortable" data-k="qty">Units'+mark('qty')+'</th>'
      +'<th class="n sortable" data-k="billed">Parts billed'+mark('billed')+'</th>'
      +'<th class="n sortable" data-k="prior">Prior base'+mark('prior')+'</th>'
      +'<th class="n sortable" data-k="new">New base'+mark('new')+'</th>'
      +'<th class="n sortable" data-k="step">Step €'+mark('step')+'</th>'
      +'<th class="n sortable" data-k="pct">Weighted'+mark('pct')+'</th></tr>';
    tb.innerHTML = pnRows.length ? pnRows.map(function(r){
      return '<tr><td>'+esc(P.pn[r.pn])+'</td><td>'+esc(P.desc[r.pn]||'')+'</td>'
        +'<td class="n">'+fmtNum(Math.round(r.qty))+'</td>'
        +'<td class="n">'+fmtEur(r.billed)+'</td>'
        +'<td class="n">'+fmtEur(r.prior)+'</td>'
        +'<td class="n">'+fmtEur(r.new)+'</td>'
        +'<td class="n">'+fmtEur(r.step)+'</td>'
        +'<td class="n">'+fmtPct(r.pct)+'</td></tr>';
    }).join('') : '<tr><td colspan="8" class="muted">No priced part numbers in this type for the selection.</td></tr>';
    Array.prototype.forEach.call(thead.querySelectorAll('th.sortable'), function(th){
      th.style.cursor = 'pointer';
      th.addEventListener('click', function(){
        var key = th.getAttribute('data-k');
        if(state.drillPnSort.key===key) state.drillPnSort.dir *= -1;
        else {
          state.drillPnSort.key = key;
          state.drillPnSort.dir = (key==='pn'||key==='desc') ? 1 : -1;
        }
        drawDrill();
      });
    });
  } else {
    var rows;
    if(level===1){
      rows = rollup([1]);
      rows.sort(function(a,b){
        var na = /Not on AIM/.test(P.l1[a.kk[0]]) ? 1 : 0;
        var nb = /Not on AIM/.test(P.l1[b.kk[0]]) ? 1 : 0;
        if(na!==nb) return na-nb;
        return metricOf(b)-metricOf(a);
      });
    }
    else if(level===2) rows = rollup([1,2], {l1: state.l1});
    else rows = rollup([1,2,3], {l1: state.l1, l2: state.l2});
    if(level>1) rows.sort(function(a,b){ return metricOf(b)-metricOf(a); });

    var head = level===1 ? 'AIM level 1' : (level===2 ? 'AIM level 2 inside ' + esc(P.l1[state.l1])
      : 'AIM level 3 inside ' + esc(P.l2[state.l2]));
    thead.innerHTML =
      '<tr><th>'+head+'</th><th class="n">Part numbers</th><th class="n">Lines</th>'
      +'<th class="n">Units</th><th class="n">Parts billed</th><th class="n">Prior base</th>'
      +'<th class="n">New base</th><th class="n">Step €</th><th class="n">Weighted</th>'
      +'<th class="n">Step / €1m</th></tr>';

    tb.innerHTML = rows.map(function(r){
      var name = level===1 ? P.l1[r.kk[0]] : (level===2 ? P.l2[r.kk[1]] : P.l3[r.kk[2]]);
      var cls = /Not on AIM|Not classified/.test(name) ? ' class="muted"' : '';
      return '<tr class="clickable" data-key="'+r.kk.join(',')+'" data-level="'+level+'"'+cls+'>'
        +'<td>'+esc(name)+'</td>'
        +'<td class="n">'+fmtNum(r.pn)+'</td>'
        +'<td class="n">'+fmtNum(r.rows)+'</td>'
        +'<td class="n">'+fmtNum(Math.round(r.qty))+'</td>'
        +'<td class="n">'+fmtEur(r.all)+'</td>'
        +'<td class="n">'+fmtEur(r.prior)+'</td>'
        +'<td class="n">'+fmtEur(r.new)+'</td>'
        +'<td class="n">'+fmtEur(r.step)+'</td>'
        +'<td class="n">'+fmtPct(r.pct)+'</td>'
        +'<td class="n">'+fmtEur(r.all>0?1000000*r.step/r.all:0)+'</td></tr>';
    }).join('');

    Array.prototype.forEach.call(document.querySelectorAll('#drill tbody tr'), function(tr){
      tr.addEventListener('click', function(){
        var kk = tr.getAttribute('data-key').split(',').map(Number);
        var lv = Number(tr.getAttribute('data-level'));
        if(lv===1){ setL1(kk[0]); }
        else if(lv===2){ state.l2 = kk[1]; state.l3 = -1; render(); }
        else if(lv===3){ state.l3 = kk[2]; state.drillPnSort = { key:'step', dir:-1 }; render(); }
      });
    });
  }

  var crumb = '<b id="cb-net" style="cursor:pointer">Network</b>';
  if(state.db>=0) crumb += ' › <span id="cb-db">'+esc(P.db[state.db])+'</span>';
  if(state.l1>=0) crumb += ' › <span id="cb-l1">'+esc(P.l1[state.l1])+'</span>';
  if(state.l2>=0) crumb += ' › <span id="cb-l2">'+esc(P.l2[state.l2])+'</span>';
  if(state.l3>=0) crumb += ' › <span id="cb-l3">'+esc(P.l3[state.l3])+'</span>';
  document.getElementById('crumb').innerHTML = crumb;
  var netEl = document.getElementById('cb-net');
  if(netEl) netEl.addEventListener('click', function(){
    state.l1 = -1; state.l2 = -1; state.l3 = -1; render();
  });
  var dbEl = document.getElementById('cb-db');
  if(dbEl) dbEl.addEventListener('click', function(){
    state.l1 = -1; state.l2 = -1; state.l3 = -1; render();
  });
  var l1El = document.getElementById('cb-l1');
  if(l1El) l1El.addEventListener('click', function(){
    state.l2 = -1; state.l3 = -1; render();
  });
  var l2El = document.getElementById('cb-l2');
  if(l2El) l2El.addEventListener('click', function(){
    state.l3 = -1; render();
  });
}

/* ---------- movers ---------- */
function drawMovers(){
  var rows = D.movers.filter(function(m){
    if(state.db>=0 && m[6]!==state.db) return false;
    if(state.src>=0 && m[5]!==state.src) return false;
    if(state.l1>=0 && m[2]!==state.l1) return false;
    if(state.l2>=0 && m[3]!==state.l2) return false;
    if(state.l3>=0 && m[4]!==state.l3) return false;
    return true;
  }).slice(0,60);
  document.querySelector('#movers thead').innerHTML =
    '<tr><th>Part number</th><th>Description as billed</th><th>AIM level 1</th><th>AIM level 2</th>'
    +'<th>Source</th><th>Distributor</th><th class="n">Units</th><th class="n">Parts billed</th>'
    +'<th class="n">Step €</th><th class="n">Weighted</th></tr>';
  document.querySelector('#movers tbody').innerHTML = rows.length ? rows.map(function(m){
    var pct = m[9]>0 ? 100*(m[10]/m[9]-1) : null;
    return '<tr><td>'+esc(m[0])+'</td><td>'+esc(m[1])+'</td><td>'+esc(P.l1[m[2]])+'</td>'
      +'<td>'+esc(P.l2[m[3]])+'</td><td>'+srcPill(m[5])+'</td><td>'+esc(P.db[m[6]])+'</td>'
      +'<td class="n">'+fmtNum(Math.round(m[7]))+'</td><td class="n">'+fmtEur(m[8])+'</td>'
      +'<td class="n">'+fmtEur(m[11])+'</td><td class="n">'+fmtPct(pct)+'</td></tr>';
  }).join('') : '<tr><td colspan="10" class="muted">No part number above the cut for this selection.</td></tr>';
}

/* ---------- page ---------- */
function render(){
  try{
    var t = totalsNow();
    kpis(t);
  }catch(e){ window.__err.push('kpis: '+e.message); }
  [drawCustMix, drawCustPn, drawLeague, drawL1, drawMix, drawSrc, drawDrill, drawMovers,
   drawConc, drawBrake].forEach(function(fn){
    try{ fn(); }catch(e){ window.__err.push(fn.name + ': ' + e.message); }
  });
  document.getElementById('errbar').style.display = window.__err.length ? 'block' : 'none';
  document.getElementById('errbar').textContent = window.__err.length
    ? 'Render problem: ' + window.__err.join(' | ') : '';
}
window.render = render;

/* One place that moves the distributor, so the control, the state and the drill
   can never disagree. */
function coerceIdx(v){
  if(v === '' || v === null || v === undefined) return -1;
  var n = Number(v);
  return (isNaN(n) || n < -1) ? -1 : n;
}
function setCust(i){
  state.cust = coerceIdx(i);
  state.custL1 = -1;
  state.custL2 = null;
  state.custL3 = null;
  state.custOther = null;
  state.brakeL2 = null;
  if(state.cust >= 0){
    var dbi = custDb(state.cust);
    if(dbi >= 0){ state.db = dbi; state.l1 = -1; state.l2 = -1; state.l3 = -1; }
  }
  var sel = document.getElementById('cust');
  if(sel && sel.value !== String(state.cust)) sel.value = String(state.cust);
  var dbSel = document.getElementById('db');
  if(dbSel && state.db >= 0 && dbSel.value !== String(state.db)) dbSel.value = String(state.db);
  render();
}
function setDb(i){
  state.db = coerceIdx(i);
  state.l1 = -1; state.l2 = -1; state.l3 = -1;
  state.brakeL2 = null;
  state.custL1 = -1; state.custL2 = null; state.custL3 = null; state.custOther = null;
  /* Clearing the distributor also clears a customer focus that belonged to another DB. */
  if(state.cust >= 0 && state.db >= 0 && custDb(state.cust) !== state.db){
    state.cust = -1;
    var csel = document.getElementById('cust');
    if(csel) csel.value = '-1';
  }
  var sel = document.getElementById('db');
  if(sel && sel.value !== String(state.db)) sel.value = String(state.db);
  refreshCustOptions();
  render();
}
function setSrc(i){
  state.src = coerceIdx(i);
  var sel = document.getElementById('src');
  if(sel && sel.value !== String(state.src)) sel.value = String(state.src);
  render();
}
function setL1(i){ state.l1 = i; state.l2 = -1; state.l3 = -1; render(); }
function setMetric(m){
  state.metric = m;
  Array.prototype.forEach.call(document.querySelectorAll('#meas button'), function(x){
    x.classList.toggle('on', x.getAttribute('data-m') === m); });
  render();
}

function refreshCustOptions(){
  var byCust = {};
  for(var i=0;i<D.customers.length;i++){
    var r = D.customers[i];
    if(state.db >= 0 && r[2] !== state.db) continue;
    var o = byCust[r[0]];
    if(!o){ o={ci:r[0], ni:r[1], dbi:r[2], prior:0, new:0, step:0, all:0}; byCust[r[0]]=o; }
    o.prior+=r[8]; o.new+=r[9]; o.step+=r[10]; o.all+=r[11];
  }
  var custOpts = [];
  for(var k in byCust){
    var c = byCust[k];
    c.pct = c.prior>0 ? 100*(c.new/c.prior-1) : null;
    custOpts.push(c);
  }
  custOpts.sort(function(a,b){
    var ap = a.pct===null?-1e9:a.pct, bp = b.pct===null?-1e9:b.pct;
    return bp-ap;
  });
  var custSel = document.getElementById('cust');
  var keep = state.cust;
  custSel.innerHTML = '<option value="-1">All customers (optional cut)</option>' +
    custOpts.map(function(c){
      var lab = esc(custLabel(c.ci)) + ' — '
        + (c.pct===null?'n/a':fmtPct(c.pct)) + ' · ' + esc(P.db[c.dbi]);
      return '<option value="'+c.ci+'">'+lab+'</option>';
    }).join('');
  if(keep >= 0 && byCust[keep] !== undefined) custSel.value = String(keep);
  else { state.cust = -1; custSel.value = '-1'; }
}

function init(){
  refreshCustOptions();
  var custSel = document.getElementById('cust');
  custSel.addEventListener('change', function(){ setCust(coerceIdx(this.value)); });

  var dbSel = document.getElementById('db');
  dbSel.innerHTML = '<option value="-1">All network (22 distributors)</option>' +
    P.db.map(function(d,i){ return '<option value="'+i+'">'+esc(d)+'</option>'; }).join('');
  var srcSel = document.getElementById('src');
  srcSel.innerHTML = '<option value="-1">All sources</option>' +
    P.src.map(function(s,i){ return '<option value="'+i+'">'+esc(s)+'</option>'; }).join('');

  dbSel.addEventListener('change', function(){ setDb(coerceIdx(this.value)); });
  srcSel.addEventListener('change', function(){ setSrc(coerceIdx(this.value)); });
  var concSel = document.getElementById('concscope');
  concSel.addEventListener('change', function(){
    concScope = (/brake/.test(this.value) ? 'brake' : 'all');
    drawConc();
  });
  Array.prototype.forEach.call(document.querySelectorAll('#meas button'), function(b){
    b.addEventListener('click', function(){
      setMetric(b.getAttribute('data-m'));
      document.getElementById('t-src').textContent = state.metric==='billed'
        ? 'Japan against Thailand, on the parts billed euro that sits in each family'
        : 'Japan against Thailand, on the same families';
    });
  });
  document.getElementById('reset').addEventListener('click', function(){
    state.db=-1; state.src=-1; state.l1=-1; state.l2=-1; state.l3=-1; state.metric='pct';
    state.cust=-1; state.custL1=-1; state.custL2=null; state.custL3=null; state.custOther=null;
    state.custPnSort = { key:'step', dir:-1 };
    state.brakeL2 = null; state.brakePnSort = { key:'step', dir:-1 };
    concScope = 'all';
    var cs = document.getElementById('concscope');
    if(cs) cs.value = 'all';
    document.getElementById('db').value='-1';
    document.getElementById('src').value='-1';
    Array.prototype.forEach.call(document.querySelectorAll('#meas button'), function(x){
      x.classList.toggle('on', x.getAttribute('data-m')==='pct'); });
    refreshCustOptions();
    render();
  });

  // Exposed so the QA pass can prove the tables filled and the render finished
  // without throwing, rather than guessing from a screenshot.
  window.__err = [];
  window.__qa = function(){
    return {
      errors: window.__err,
      kpi: document.querySelectorAll('#kpis .kpi').length,
      kpiVals: Array.prototype.map.call(document.querySelectorAll('#kpis .val'),
        function(e){ return e.textContent; }),
      drill: document.querySelectorAll('#drill tbody tr').length,
      movers: document.querySelectorAll('#movers tbody tr').length,
      brakeL2: document.querySelectorAll('#brake-l2 tbody tr').length,
      brakePn: document.querySelectorAll('#brake-pn tbody tr').length,
      brakeL2Sel: state.brakeL2,
      brakeFigs: Array.prototype.map.call(document.querySelectorAll('#brake-figs .fv'),
        function(e){ return e.textContent; }),
      concFigs: Array.prototype.map.call(document.querySelectorAll('#conc-figs .fv'),
        function(e){ return e.textContent; }),
      concScope: concScope,
      accounts: document.getElementById('custs') === null ? 'removed' : 'present',
      custPn: document.querySelectorAll('#cust-pn tbody tr').length,
      custPnSort: state.custPnSort,
      cust: state.cust,
      custL1: state.custL1,
      custL2: state.custL2,
      custL3: state.custL3,
      crumb: document.getElementById('crumb').textContent,
      custCrumb: document.getElementById('cust-crumb').textContent,
      charts: ['c-cust-mix','c-league','c-l1','c-mix','c-src','c-brake','c-conc'].map(function(id){
        var el = document.getElementById(id);
        var ch = el && window.Chart.getChart(el);
        return { id:id, type: ch? ch.config.type : null,
                 points: ch? ch.data.datasets.reduce(function(n,d){return n+(d.data?d.data.length:0);},0) : 0,
                 drawn: !!(ch && ch.chartArea && ch.chartArea.width>10) };
      })
    };
  };
  window.__qaDrillSpine = function(){
    var l1 = P.l1.indexOf('Not on AIM spine');
    if(l1 < 0) return {ok:false, err:'no spine l1'};
    state.cust = -1; state.db = -1; state.src = -1;
    state.custL1 = l1; state.custL2 = null; state.custL3 = null; state.custOther = null;
    render();
    var l2rows = rollupCustL2({l1: l1}).filter(function(r){ return r.all > 0; });
    if(l2rows.length){ state.custL2 = l2rows[0].l2; state.custL3 = null; render(); }
    var l3rows = rollupCustL3({l1: state.custL1, l2: state.custL2}).filter(function(r){ return r.all > 0; });
    if(l3rows.length){ state.custL3 = l3rows[0].l3; render(); }
    var t = totalsNow();
    var el = document.getElementById('c-cust-mix');
    var ch = el && window.Chart.getChart(el);
    var chartVals = ch && ch.data && ch.data.datasets[0] ? ch.data.datasets[0].data : [];
    return {
      ok: true,
      step: t.step,
      all: t.all,
      rows: t.rows,
      kpiVals: Array.prototype.map.call(document.querySelectorAll('#kpis .val'),
        function(e){ return e.textContent; }),
      chartVals: chartVals,
      custCrumb: document.getElementById('cust-crumb').textContent,
      qMix: document.getElementById('q-cust-mix').textContent
    };
  };

  var gen = new Date(D.generated);
  document.getElementById('genline').textContent =
    'Built ' + gen.toISOString().slice(0,10) + '. Network tie-out: step ' + fmtEur(D.published.step)
    + ', weighted ' + fmtPct(D.published.pct) + ', both checked against the published revision.';
  document.getElementById('foot').innerHTML =
    '<b>Basis.</b> Price revision comparison, network customers in scope, window 1 Jul 2025 to 30 Jun 2026. '
    + fmtNum(D.in_scope.rows) + ' in-scope lines carrying ' + fmtEur(D.in_scope.billed)
    + ' of parts billed; ' + fmtNum(D.in_scope.priced_rows) + ' of those carry a price on both sides. '
    + 'Euro values use ' + D.fx + ' JPY per EUR. '
    + '<br><br><b>What is shown rather than hidden.</b> AIM level 1 covers '
    + fmtPct(D.coverage.spine_pct,1) + ' of in-scope parts billed euro; AIM level 3 is filled on '
    + fmtPct(D.coverage.l3_pct,1) + '; source of supply is held on ' + fmtPct(D.coverage.source_pct,1)
    + '. The remainder appears as its own row or its own filter value and stays inside every euro total. '
    + 'Israel is UMI and UTI as two separate distributors, never one blended figure. Price classes '
    + '(C, D, F, J, M, P, T, V) are IML-owned and are not a lever here. '
    + '<br><br><b>Brakes and the concentration curves.</b> Families follow the corrected AIM taxonomy, '
    + 'the same one used in every other panel on this page. The brake view and the concentration curves '
    + 'count part numbers that moved up; part numbers that did not move carry no step and are left out, '
    + 'so the counts are not padded with rows that add nothing. '
    + '<br><br><b>Not modelled.</b> No elasticity, no revenue, margin or customer-behaviour response. '
    + 'The weighted percentage is a base-price move on prior billing quantities.';

  render();
}
init();
})();
</script>
</body>
</html>
"""


def main() -> int:
    payload = DATA.read_text(encoding="utf-8")
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
