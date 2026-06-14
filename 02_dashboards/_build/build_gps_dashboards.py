"""Build ISZE_GPS_Dashboard_v9.html — UIO v18 + car park + study rates."""
import datetime
import io
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
ECHARTS = (ROOT / "echarts.min.js").read_text(encoding="utf-8")
STAMP = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

snap = json.loads((ROOT / "Data" / "_build" / "gps_v9_snapshot.json").read_text(encoding="utf-8"))
BASE25 = snap["base25"]
WARR = snap["warranty"]
UIO26 = snap["uio26"]
BP27 = snap["bp27"]
MAX27 = snap["uio27_max"]
RATES = [snap["rates"][0], snap["rates"][1], snap["rates"][2]]  # N35, N75, FMD
LCV_RATE = 250

ituk = BASE25[0]
ITUK_MAX_25 = ituk[2]
ITUK_SALES = ituk[3]
ITUK_WARR = WARR["ITUK"]
ITUK_GPS_INCL = ITUK_SALES / ITUK_MAX_25
ITUK_GPS_EX = (ITUK_SALES - ITUK_WARR) / ITUK_MAX_25
BP_ITUK_27 = snap["bp_ituk"]["2027"]["isze_eur"]
ITUK_MAX_27 = snap["uio27_max"]["ITUK"]
GPS_NEEDED_ITUK = BP_ITUK_27 / ITUK_MAX_27
PP_GAP_ITUK = GPS_NEEDED_ITUK - ITUK_GPS_EX

cp = json.loads((ROOT / "Data" / "_build" / "uio_v18_gps.json").read_text(encoding="utf-8"))
uio25 = cp["distributors"]["ITUK"]["uio"]["2025"]

HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ISZE GPS Dashboard v9</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#f4f4f5;color:#1a1a1a}
.wrap{max-width:1560px;margin:0 auto;padding:20px 28px 40px}
header{border-left:6px solid #CC0E1E;padding-left:14px;margin-bottom:16px}
header h1{font-size:22px}
header p{font-size:12px;color:#666;margin-top:4px}
.nav{display:flex;gap:8px;margin-bottom:18px;flex-wrap:wrap}
.nav button{padding:8px 16px;border:1px solid #ccc;border-radius:6px;background:#fff;cursor:pointer;font-size:13px;font-weight:600}
.nav button.on{background:#CC0E1E;color:#fff;border-color:#CC0E1E}
.panel{display:none}.panel.on{display:block}
.card{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:16px 18px;margin-bottom:18px}
.card h2{font-size:15px;margin-bottom:10px}
.heroes{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:16px}
.hero{flex:1;min-width:170px;border:1px solid #e0e0e0;border-top:4px solid #CC0E1E;border-radius:8px;padding:12px 14px;background:#fafafa}
.hero .v{font-size:28px;font-weight:700;color:#CC0E1E}
.hero .l{font-size:12px;color:#444;margin-top:4px;line-height:1.4}
.hero .s{font-size:11px;color:#888;margin-top:2px}
.flag{background:#fff7e0;border:1px solid #e6c860;border-radius:8px;padding:10px 14px;font-size:12px;line-height:1.55;margin-bottom:16px}
.note{font-size:11px;color:#777;line-height:1.55;margin-top:8px}
table{border-collapse:collapse;width:100%;font-size:12px}
th{background:#CC0E1E;color:#fff;padding:6px 8px;text-align:right}
th:first-child,td:first-child{text-align:left}
td{padding:5px 8px;text-align:right;border-bottom:1px solid #eee}
tr:nth-child(even) td{background:#f9f9f9}
input[type=number],select{padding:4px 6px;border:1px solid #2962cc;border-radius:4px;color:#0000FF;font-weight:600;font-size:12px}
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:12px;font-size:12px}
.g{color:#0a7d33;font-weight:700}.a{color:#c98a00;font-weight:700}.r{color:#CC0E1E;font-weight:700}
#netChart,#spuChart,#bpChart{height:340px}
.badge{display:inline-block;background:#eee;color:#555;font-size:10px;padding:2px 6px;border-radius:4px;margin-left:6px}
</style>
<script>%%ECHARTS%%</script>
</head><body>
<div class="wrap">
<header>
<h1>ISZE GPS Dashboard <span class="badge">v9</span></h1>
<p>Max spend per unit · UIO v18 + ITUK DVLA car park · rates €296/€739/€887 · %%STAMP%%</p>
</header>
<nav class="nav">
<button type="button" class="on" data-tab="network">Network GPS</button>
<button type="button" data-tab="ituk">ITUK car park</button>
<button type="button" data-tab="bp27">BP FY2027 gap</button>
</nav>

<section id="panel-network" class="panel on">
<div class="flag">CV distributors use <b>study rates</b> (€296 / €739 / €887) — not legacy €1,120 / €1,344. CY2025 UIO from sales-aligned parc; 2026 from UIO v18 growth.</div>
<div class="card">
<div class="controls">
<label>View <select id="viewSel"><option value="2025" selected>CY2025 actual</option><option value="2026">FY2026 projection</option></select></label>
<label>Warranty <select id="warrSel"><option value="incl">incl.</option><option value="ex" selected>ex.</option></select></label>
<label>Uplift (pp) <input type="number" id="uplift" value="1.0" step="0.1" style="width:56px"></label>
<span id="netLine" style="margin-left:auto;font-weight:700"></span>
</div>
<div id="netChart"></div>
</div>
<div class="card"><h2>Distributor detail (GPS % only — no blended €/unit)</h2><table id="netTbl"><thead></thead><tbody></tbody></table></div>
</section>

<section id="panel-ituk" class="panel">
<div class="heroes">
<div class="hero"><div class="v">%%ITUK_GPS_INCL%%</div><div class="l">GPS incl. warranty</div><div class="s">€%%ITUK_SALES_M%%M ÷ €%%ITUK_MAX_M%%M max spend</div></div>
<div class="hero"><div class="v">%%ITUK_GPS_EX%%</div><div class="l">GPS ex. warranty</div><div class="s">Primary CY2025 view</div></div>
<div class="hero"><div class="v">%%ITUK_UIO%%</div><div class="l">DVLA car park CY2025</div><div class="s">N35 %%N35%% · N75+ %%N75%% · F %%F%%</div></div>
</div>
<div class="card"><h2>Max spend per unit — ISZE €/veh/yr (study formula)</h2><div id="spuChart"></div>
<div class="note">£400 / £1,000 / £1,200 retail × GP 34% × FX 1.12. CY2025 UIO: Parts Sales Calculation FY26 (DVLA).</div></div>
</section>

<section id="panel-bp27" class="panel">
<div class="heroes">
<div class="hero"><div class="v">%%GPS_NEEDED_ITUK%%</div><div class="l">GPS needed for ITUK BP FY27</div><div class="s">€7.43M ISZE plan ÷ FY27 max spend</div></div>
<div class="hero"><div class="v">+%%PP_GAP_ITUK%%</div><div class="l">Δ GPS pp vs CY2025 ex-warr</div><div class="s">Genuine share increase required</div></div>
<div class="hero"><div class="v">€%%PP_EUR_ITUK%%</div><div class="l">Value per +1pp ITUK</div><div class="s">On FY27 max spend base</div></div>
</div>
<div class="card"><h2>FY2027 — Δ GPS pp to business plan (ex-warranty basis)</h2><div id="bpChart"></div></div>
<div class="card"><h2>Detail</h2><table id="bpTbl"><thead></thead><tbody></tbody></table>
<p class="note">ITUK: BP ISZE €7.43M. Other DBs: Kosha VP €35.3M allocated by CY2025 sales share (proxy).</p></div>
</section>
</div>

<script>
"use strict";
var BASE25=%%BASE25%%;
var WARR=%%WARR%%;
var UIO26=%%UIO26%%;
var BP27=%%BP27%%;
var MAX27=%%MAX27%%;
var RATES=%%RATES_JSON%%;
var LCV=%%LCV_RATE%%;

document.querySelectorAll('.nav button').forEach(function(btn){
 btn.addEventListener('click',function(){
  document.querySelectorAll('.nav button').forEach(function(b){b.classList.remove('on');});
  document.querySelectorAll('.panel').forEach(function(p){p.classList.remove('on');});
  btn.classList.add('on');
  document.getElementById('panel-'+btn.dataset.tab).classList.add('on');
  if(btn.dataset.tab==='network') netChart.resize();
  if(btn.dataset.tab==='ituk') spuChart.resize();
  if(btn.dataset.tab==='bp27') bpChart.resize();
 });
});

function fmt0(x){return Math.round(x).toLocaleString('en-GB');}
function fmtM(x){return (x/1e6).toFixed(2);}
function gpsClass(g){return g>=0.55?'g':(g>=0.35?'a':'r');}
function warrOf(db){return WARR[db]||0;}

function maxSpend26(db){
 if(db==='ITUK'){
  var u=UIO26.ITUK;
  return u.N35*RATES[0]+u.N75_LD*RATES[1]+u.F_MD*RATES[2];
 }
 var u=UIO26[db];
 return (u.LD||0)*RATES[1]+(u.FMD||0)*RATES[2]+(u.LCV||0)*LCV;
}

function rows2025(ex){
 return BASE25.map(function(b){
  var sales=b[3]-(ex?warrOf(b[0]):0);
  return {db:b[0],max:b[2],sales:sales,gps:sales/b[2]};
 });
}
function rows2026(ex,upl){
 var b25={}; BASE25.forEach(function(b){b25[b[0]]={gps:(b[3]-(ex?warrOf(b[0]):0))/b[2]};});
 return BASE25.map(function(b){
  var db=b[0],max=maxSpend26(db),gBase=b25[db].gps,gps=gBase+upl/100,sales=gps*max;
  return {db:db,max:max,sales:sales,gps:gps};
 });
}
var netChart=echarts.init(document.getElementById('netChart'));
function renderNet(){
 var is26=document.getElementById('viewSel').value==='2026';
 var ex=document.getElementById('warrSel').value==='ex';
 var upl=parseFloat(document.getElementById('uplift').value)||0;
 var rows=is26?rows2026(ex,upl):rows2025(ex);
 rows.sort(function(a,b){return b.gps-a.gps;});
 var totS=0,totM=0; rows.forEach(function(o){totS+=o.sales;totM+=o.max;});
 document.getElementById('netLine').textContent='Network: sales €'+fmtM(totS)+'M · max spend €'+fmtM(totM)+'M · GPS '+(100*totS/totM).toFixed(1)+'%';
 netChart.setOption({
  grid:{left:72,right:50,top:10,bottom:20},
  xAxis:{type:'value',max:115,axisLabel:{formatter:'{value}%'}},
  yAxis:{type:'category',data:rows.map(function(o){return o.db;}).reverse()},
  series:[{type:'bar',barWidth:'58%',data:rows.map(function(o){
   var v=Math.round(1000*o.gps)/10;
   return {value:v,itemStyle:{color:v>=55?'#0a7d33':(v>=35?'#c98a00':'#CC0E1E')},label:{show:true,position:'right',formatter:v+'%'}};
  }).reverse()}]
 },true);
 var thead=document.querySelector('#netTbl thead'),tbody=document.querySelector('#netTbl tbody');
 thead.innerHTML='<tr><th>DB</th><th>Max spend €</th><th>Sales €</th><th>GPS %</th></tr>';
 tbody.innerHTML='';
 rows.forEach(function(o){
  var tr=document.createElement('tr');
  tr.innerHTML='<td><b>'+o.db+'</b></td><td>'+fmt0(o.max)+'</td><td>'+fmt0(o.sales)+'</td><td class="'+gpsClass(o.gps)+'">'+(100*o.gps).toFixed(1)+'%</td>';
  tbody.appendChild(tr);
 });
}
['viewSel','warrSel','uplift'].forEach(function(id){document.getElementById(id).addEventListener('change',renderNet);});
renderNet();

var spuChart=echarts.init(document.getElementById('spuChart'));
spuChart.setOption({
 grid:{left:56,right:24,top:36,bottom:28},
 xAxis:{type:'category',data:['N35','N75/LD','F/MD']},
 yAxis:{type:'value',axisLabel:{formatter:'€{value}'}},
 series:[{name:'Study rate',type:'bar',data:RATES,itemStyle:{color:'#0a7d33'},
  label:{show:true,position:'top',formatter:function(p){return '€'+p.value;}}}]
});

var bpRows=BASE25.map(function(b){
 var db=b[0],max27=MAX27[db]||b[2];
 var salesEx=b[3]-warrOf(db);
 var gps25=salesEx/b[2];
 var target=BP27[db]||0;
 var gpsNeed=target/max27;
 return {db:db,gps25:gps25,gpsNeed:gpsNeed,dpp:gpsNeed-gps25,target:target,max27:max27};
}).sort(function(a,b){return b.dpp-a.dpp;});

var bpChart=echarts.init(document.getElementById('bpChart'));
bpChart.setOption({
 grid:{left:72,right:24,top:10,bottom:20},
 xAxis:{type:'value',axisLabel:{formatter:'{value} pp'}},
 yAxis:{type:'category',data:bpRows.map(function(o){return o.db;}).reverse()},
 series:[{type:'bar',data:bpRows.map(function(o){
  return {value:Math.round(o.dpp*1000)/10,itemStyle:{color:o.dpp>0?'#CC0E1E':'#0a7d33'},
   label:{show:true,position:'right',formatter:function(p){return (p.value>=0?'+':'')+p.value+' pp';}}};
 }).reverse()}]
});
var bthead=document.querySelector('#bpTbl thead'),btbody=document.querySelector('#bpTbl tbody');
bthead.innerHTML='<tr><th>DB</th><th>GPS 2025 ex</th><th>GPS for BP27</th><th>Δ pp</th><th>Plan €</th></tr>';
btbody.innerHTML='';
bpRows.forEach(function(o){
 var tr=document.createElement('tr');
 tr.innerHTML='<td><b>'+o.db+'</b></td><td>'+(100*o.gps25).toFixed(1)+'%</td><td>'+(100*o.gpsNeed).toFixed(1)+'%</td><td class="'+(o.dpp>0?'r':'g')+'">'+(o.dpp>=0?'+':'')+(100*o.dpp).toFixed(1)+' pp</td><td>'+fmt0(o.target)+'</td>';
 btbody.appendChild(tr);
});

window.addEventListener('resize',function(){netChart.resize();spuChart.resize();bpChart.resize();});
</script>
</body></html>
"""

out = ROOT / "Dashboards" / "ISZE_GPS_Dashboard_v9.html"
html = (
    HTML.replace("%%ECHARTS%%", ECHARTS)
    .replace("%%STAMP%%", STAMP)
    .replace("%%BASE25%%", json.dumps(BASE25))
    .replace("%%WARR%%", json.dumps(WARR))
    .replace("%%UIO26%%", json.dumps(UIO26))
    .replace("%%BP27%%", json.dumps(BP27))
    .replace("%%MAX27%%", json.dumps(MAX27))
    .replace("%%RATES_JSON%%", json.dumps(RATES))
    .replace("%%LCV_RATE%%", str(LCV_RATE))
    .replace("%%ITUK_GPS_INCL%%", f"{ITUK_GPS_INCL:.1%}")
    .replace("%%ITUK_GPS_EX%%", f"{ITUK_GPS_EX:.1%}")
    .replace("%%ITUK_SALES_M%%", f"{ITUK_SALES/1e6:.2f}")
    .replace("%%ITUK_MAX_M%%", f"{ITUK_MAX_25/1e6:.2f}")
    .replace("%%ITUK_UIO%%", f"{ituk[1]:,}")
    .replace("%%N35%%", f"{int(uio25['N35']):,}")
    .replace("%%N75%%", f"{int(uio25['N75_LD']):,}")
    .replace("%%F%%", f"{int(uio25['F_MD']):,}")
    .replace("%%GPS_NEEDED_ITUK%%", f"{GPS_NEEDED_ITUK:.1%}")
    .replace("%%PP_GAP_ITUK%%", f"{PP_GAP_ITUK*100:.1f}")
    .replace("%%PP_EUR_ITUK%%", f"{ITUK_MAX_27*0.01:,.0f}")
)
io.open(out, "w", encoding="utf-8").write(html)
print("written", out)
