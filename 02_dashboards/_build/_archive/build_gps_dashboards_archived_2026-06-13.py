import json, datetime, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ECHARTS = open(r"C:\Users\jerom\Desktop\claude\ISZE\echarts.min.js", encoding="utf-8").read()
HIST = [r for r in json.load(open(r"C:\Users\jerom\Desktop\claude\ISZE\Data\_build\gps_results.json", encoding="utf-8-sig"))
        if r["db"] != "Distributor" and isinstance(r["year"], int) and r["year"] <= 2024]
STAMP = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# v8 2025 baseline (GPS Calculator v8 / v7 GPS_ex_Warranty)
BASE25 = [
    ["ITUK", 23989, 27270432, 5769867.82], ["IUK", 47783, 11945750, 6221920.41],
    ["UMI", 18542, 4635500, 3388801.28], ["UTI", 10336, 12534368, 3402116.94],
    ["GERMANY", 13780, 4089680, 2577765.90], ["BELGIUM", 9594, 2497904, 2143951.90],
    ["IRELAND", 2161, 1276868, 1213660.33], ["NORWAY", 7929, 1982250, 1438472.63],
    ["SWEDEN", 8443, 2110750, 1289481.04], ["DENMARK", 851, 212500, 150218.49],
    ["FINLAND", 1204, 301000, 285912.53], ["ICELAND", 406, 101500, 87259.89],
    ["CYPRUS", 2308, 753610, 429512.03], ["GREECE", 3742, 967690, 528390.82],
    ["MALTA", 1040, 471410, 206502.27], ["ROMANIA", 1071, 267750, 177276.35],
    ["HUNGARY", 3734, 933500, 330030.58], ["PORTUGAL", 7208, 4015506, 1712790.96],
]
WARR = {"ITUK": 374426.05, "UTI": 255967.77, "GERMANY": 5593.33, "GREECE": 1450.36,
        "MALTA": 1469.68, "CYPRUS": 406.22}
UIO26 = {"ITUK": [23210, 963, 0], "IUK": [0, 0, 44923], "UMI": [0, 0, 17016], "UTI": [5887, 4583, 0],
         "GERMANY": [784, 0, 12338], "BELGIUM": [145, 0, 9338], "IRELAND": [1332, 131, 2145],
         "NORWAY": [0, 0, 7419], "SWEDEN": [0, 0, 8778], "DENMARK": [1, 0, 902], "FINLAND": [0, 0, 1194],
         "ICELAND": [0, 0, 419], "CYPRUS": [227, 5, 2328], "GREECE": [56, 5, 4106], "MALTA": [260, 0, 788],
         "ROMANIA": [0, 0, 1159], "HUNGARY": [0, 0, 3643], "PORTUGAL": [2963, 371, 5762]}
RATES = {"ITUK": [1120, 1344, 0], "IUK": [0, 0, 250], "UMI": [0, 0, 250], "UTI": [1120, 1344, 0],
         "BELGIUM": [1120, 1344, 250], "GERMANY": [1120, 1344, 250], "PORTUGAL": [1120, 1344, 250],
         "IRELAND": [1120, 1344, 250], "NORWAY": [0, 0, 250], "SWEDEN": [0, 0, 250], "DENMARK": [0, 0, 250],
         "FINLAND": [0, 0, 250], "ICELAND": [0, 0, 250], "MALTA": [1120, 1344, 250], "CYPRUS": [1120, 1344, 250],
         "GREECE": [1120, 1344, 250], "HUNGARY": [0, 0, 250], "ROMANIA": [0, 0, 250]}

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Arial,sans-serif;background:#fff;color:#1a1a1a;padding:24px 32px;max-width:1560px;margin:0 auto}
h1{font-size:22px;color:#1a1a1a;border-left:6px solid #CC0E1E;padding-left:12px;margin-bottom:4px}
.sub{color:#666;font-size:12px;margin-bottom:18px;padding-left:18px}
.heroes{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:22px}
.hero{flex:1;min-width:200px;border:1px solid #e0e0e0;border-top:4px solid #CC0E1E;border-radius:6px;padding:14px 16px;background:#fafafa}
.hero .v{font-size:30px;font-weight:700;color:#CC0E1E}
.hero .l{font-size:12px;color:#444;margin-top:4px;line-height:1.4}
.hero .s{font-size:11px;color:#888;margin-top:2px}
.card{border:1px solid #e0e0e0;border-radius:6px;padding:16px 18px;margin-bottom:22px;background:#fff}
.card h2{font-size:15px;margin-bottom:10px;color:#1a1a1a}
.note{font-size:11px;color:#777;line-height:1.55;margin-top:8px}
table{border-collapse:collapse;width:100%;font-size:12px}
th{background:#CC0E1E;color:#fff;padding:6px 8px;text-align:right;font-weight:600;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
td{padding:5px 8px;text-align:right;border-bottom:1px solid #eee;white-space:nowrap}
tr:nth-child(even) td{background:#f7f7f7}
input[type=number]{width:70px;padding:3px 4px;border:1px solid #2962cc;border-radius:3px;color:#0000FF;font-weight:600;text-align:right;font-size:12px}
select,button{padding:5px 10px;border:1px solid #ccc;border-radius:4px;background:#fff;font-size:12px;cursor:pointer}
button{background:#CC0E1E;color:#fff;border:none;font-weight:600}
.controls{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-bottom:12px;font-size:12px}
.controls label{display:flex;gap:6px;align-items:center}
.g{color:#0a7d33;font-weight:700}.a{color:#c98a00;font-weight:700}.r{color:#CC0E1E;font-weight:700}
.flag{background:#fff7e0;border:1px solid #e6c860;border-radius:6px;padding:10px 14px;font-size:12px;line-height:1.55;margin-bottom:22px}
.bp{display:flex;gap:16px;flex-wrap:wrap}
.bp div{flex:1;min-width:170px;border:1px solid #e0e0e0;border-radius:6px;padding:10px 12px}
.bp b{font-size:17px;color:#CC0E1E;display:block;margin-top:3px}
"""

D1 = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>ISZE — ITUK Target Study vs GPS Reconciliation</title>
<style>%%CSS%%
.spuPanel{display:flex;gap:26px;flex-wrap:wrap;align-items:flex-start}
.spuInputs{min-width:300px}
.spuInputs label{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px;font-size:12px}
.out{font-size:13px;line-height:2}
.out b{font-size:18px;color:#CC0E1E}
</style>
<script>%%ECHARTS%%</script>
</head><body>
<h1>ITUK Parts Sales Target Study vs ISZE GPS — Reconciliation</h1>
<div class="sub">Why ITUK's DB→DLR-level file says ~79% and our GPS says ~21% for the same business · Sources: ITUK Parts Sales Target Study.xlsx (CY2025), ISZE_GPS_Calculator_v8.xlsx · Generated %%STAMP%%</div>

<div class="heroes">
<div class="hero"><div class="v">78.6%</div><div class="l">ITUK file — retail (DB→DLR) share</div><div class="s">£12.87M ITUK sell-out ÷ £16.38M potential (their spend/unit, retail GBP)</div></div>
<div class="hero"><div class="v">55.0%</div><div class="l">ITUK file — ISZE billing level</div><div class="s">€6.66M ISZE→ITUK ÷ €12.11M potential (same study spend/unit at ISZE cost level)</div></div>
<div class="hero"><div class="v">21.2%</div><div class="l">ISZE GPS Calculator v8</div><div class="s">€5.77M ISZE net sales ÷ €27.27M max wallet (UIO 23,989; 19.8% ex-warranty)</div></div>
</div>

<div class="flag"><b>⚠ Open item:</b> the study's CY2025 "actual" ISZE→ITUK is <b>€6.66M</b>; our ERP net-sales cut is <b>€5.77M</b> — a <b>€0.89M scope gap</b>. Verified: ERP billing has <b>no separate warranty document type</b> (SaTy = SOR/VOR/RUSH/PRD only), so warranty does <b>not</b> explain this gap — it must be line scope, timing or price basis. Needs one check with ITUK/SAP before external use.</div>

<div class="card"><h2>The bridge: 78.6% → 21.2% in three steps</h2>
<div id="bridge" style="height:320px"></div>
<div class="note">Step 1 — move from ITUK retail (incl. 34% GP and locally sourced parts) to ISZE billing: ITUK only buys ~52% of its retail parts value from ISZE. Step 2 — replace the study's actual with our ERP net-sales cut (−€0.89M, unreconciled). Step 3 — replace the study's spend/unit with the ISZE max wallet: denominator more than doubles (€12.1M → €27.3M, incl. updated UIO 23,989).</div>
</div>

<div class="card"><h2>The real driver: spend-per-unit assumptions (ISZE-net €/unit/yr)</h2>
<div id="spuChart" style="height:300px"></div>
<div class="note">Study (ITUK retail GBP): N35 £400 · N75 £1,000 · F/MD £1,200 → at ITUK cost (GP 34%) × 1.12 GBP/EUR = €296 / €739 / €887 ISZE-net. ISZE standard wallet applies €1,120 to <b>all</b> N-series. N35 alone is ~11,400 units (~half of ITUK UIO): study values it at €3.4M, our wallet at €12.8M — that one assumption is ~70% of the denominator gap. Neither number is validated against actual UK workshop spend.</div>
</div>

<div class="card"><h2>Adjustable ITUK spend/unit — what GPS would be</h2>
<div class="spuPanel">
<div class="spuInputs">
<label>N35 spend/unit (€ ISZE-net/yr) <input type="number" id="spuN35" value="1120" step="10"></label>
<label>N75 spend/unit (€ ISZE-net/yr) <input type="number" id="spuN75" value="1120" step="10"></label>
<label>F-series / MD spend/unit (€/yr) <input type="number" id="spuFMD" value="1344" step="10"></label>
<label>Numerator
<select id="numBase"><option value="5769867.82">ERP cut €5.77M (GPS calc)</option><option value="5395441.77">ERP ex-warranty €5.40M</option><option value="6658172.06">Study actual €6.66M</option></select></label>
<button id="btnStd">Standard wallet</button> <button id="btnStudy">Study values</button>
<div class="note">Defaults = ISZE standard wallet. "Study values" = €296/€739/€887. UIO fixed at study CY2025: N35 11,444 · N75 10,747 · F/MD 877.</div>
</div>
<div class="out">
Wallet: <b id="outWallet">—</b><br>
GPS: <b id="outGps">—</b><br>
Value of +1pp GPS: <b id="outPp">—</b> /yr additional ISZE sales
</div>
</div>
</div>

<script>
"use strict";
var UIO_N35=11444, UIO_N75=10747, UIO_FMD=877;
var fmtM=function(x){return "€"+(x/1e6).toFixed(2)+"M";};
var fmtK=function(x){return "€"+Math.round(x/1000)+"K";};

var bridge=echarts.init(document.getElementById("bridge"));
bridge.setOption({
 grid:{left:60,right:30,top:30,bottom:60},
 xAxis:{type:"category",data:["ITUK file\\nretail (DB→DLR) share","Measure at ISZE\\nbilling level","Use ERP\\nnumerator (−€0.89M)","Use ISZE\\nmax wallet"],axisLabel:{interval:0,fontSize:11}},
 yAxis:{type:"value",max:90,axisLabel:{formatter:"{value}%"}},
 series:[{type:"bar",barWidth:"52%",
  data:[{value:78.6,itemStyle:{color:"#888"}},{value:55.0,itemStyle:{color:"#b06a00"}},{value:47.7,itemStyle:{color:"#b06a00"}},{value:21.2,itemStyle:{color:"#CC0E1E"}}],
  label:{show:true,position:"top",formatter:"{c}%",fontWeight:"bold"}}],
 tooltip:{trigger:"axis"}
});

var spuChart=echarts.init(document.getElementById("spuChart"));
spuChart.setOption({
 grid:{left:60,right:30,top:40,bottom:30},
 legend:{top:0},
 xAxis:{type:"category",data:["N35","N75","F-series / MD"]},
 yAxis:{type:"value",axisLabel:{formatter:"€{value}"}},
 series:[
  {name:"Target Study (ISZE-net equiv.)",type:"bar",data:[295.68,739.20,887.04],itemStyle:{color:"#888"},label:{show:true,position:"top",formatter:function(p){return "€"+Math.round(p.value);}}},
  {name:"ISZE standard wallet",type:"bar",data:[1120,1120,1344],itemStyle:{color:"#CC0E1E"},label:{show:true,position:"top",formatter:function(p){return "€"+Math.round(p.value);}}}
 ],
 tooltip:{trigger:"axis"}
});

function recompute(){
 var sN35=parseFloat(document.getElementById("spuN35").value)||0;
 var sN75=parseFloat(document.getElementById("spuN75").value)||0;
 var sFMD=parseFloat(document.getElementById("spuFMD").value)||0;
 var num=parseFloat(document.getElementById("numBase").value);
 var wallet=UIO_N35*sN35+UIO_N75*sN75+UIO_FMD*sFMD;
 document.getElementById("outWallet").textContent=fmtM(wallet);
 document.getElementById("outGps").textContent=wallet>0?(100*num/wallet).toFixed(1)+"%":"—";
 document.getElementById("outPp").textContent=fmtK(wallet*0.01);
}
["spuN35","spuN75","spuFMD","numBase"].forEach(function(id){document.getElementById(id).addEventListener("input",recompute);});
document.getElementById("btnStd").addEventListener("click",function(){
 document.getElementById("spuN35").value=1120;document.getElementById("spuN75").value=1120;document.getElementById("spuFMD").value=1344;recompute();});
document.getElementById("btnStudy").addEventListener("click",function(){
 document.getElementById("spuN35").value=295.68;document.getElementById("spuN75").value=739.20;document.getElementById("spuFMD").value=887.04;recompute();});
recompute();
window.addEventListener("resize",function(){bridge.resize();spuChart.resize();});
</script>
</body></html>
"""

D2 = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>ISZE — Network GPS, warranty view & FY2026 projection</title>
<style>%%CSS%%
#gpsChart{height:380px}
td.in{padding:2px 4px}
#bpCard{display:none}
</style>
<script>%%ECHARTS%%</script>
</head><body>
<h1>Network GPS — all distributors, warranty view &amp; FY2026 projection</h1>
<div class="sub">Basis: ISZE_GPS_Calculator_v8.xlsx (2025 baseline + Rate Table) · UIO FY2026: ISUZU_UIO_Overview_2026_v17.xlsx · Warranty: Warranty_CV_2025.xlsx (CV only) · Generated %%STAMP%%</div>

<div class="card">
<div class="controls">
<label>View <select id="viewSel">
 <option value="2022">2022 actual</option><option value="2023">2023 actual</option><option value="2024">2024 actual</option>
 <option value="2025">2025 actual</option><option value="2026" selected>FY2026 projection</option></select></label>
<label>Warranty <select id="warrSel"><option value="incl" selected>incl. warranty</option><option value="ex">ex. warranty</option></select></label>
<label>GPS uplift vs 2025 (pp) <input type="number" id="uplift" value="1.0" step="0.1" style="width:56px"></label>
<button id="btnReset">Reset rates &amp; uplift</button>
<span id="netLine" style="margin-left:auto;font-weight:700"></span>
</div>
<div id="gpsChart"></div>
</div>

<div class="card" id="bpCard"><h2>ITUK — FY2026 landing vs Business Plan</h2>
<div class="bp">
<div>BP FY2026 retail (£)<b>£13.13M</b></div>
<div>BP-implied ISZE→ITUK (€)<b>€6.97M</b></div>
<div>Projected ISZE→ITUK @ uplift<b id="bpProj">—</b></div>
<div>Gap to BP<b id="bpGap">—</b></div>
<div>GPS needed for BP<b id="bpNeed">—</b></div>
</div>
<div class="note">BP source: ITUK BUSINESSPLAN.xlsx (FY26 £13,129,200); ISZE-level plan €6,974,170 per Target Study. GPS needed = BP-implied sales ÷ FY26 wallet. ITUK 2025 baseline GPS 21.2% incl. warranty / 19.8% ex. — hitting BP means ~+4.4pp in one year; the +1pp uplift lands ~€0.9M short.</div>
</div>

<div class="card"><h2 id="tblTitle">Distributor detail</h2>
<table id="tbl"><thead id="thead"></thead><tbody id="tbody"></tbody></table>
<div class="note" id="footNote"></div>
</div>

<script>
"use strict";
var HIST=%%HIST%%;
var BASE25=%%BASE25%%;
var WARR=%%WARR%%;
var UIO26=%%UIO26%%;
var RATEDEF=%%RATES%%;
var BP={retailGBP:13129200,iszeEUR:6974170.05};
var rateState={};
var fmt0=function(x){return x.toLocaleString("en-GB",{maximumFractionDigits:0});};
var fmtM=function(x){return "€"+(x/1e6).toFixed(2)+"M";};
function rateOf(db){if(!rateState[db]){rateState[db]=RATEDEF[db].slice();}return rateState[db];}
function gpsClass(g){return g>=0.55?"g":(g>=0.35?"a":"r");}
function warrOf(db){return WARR[db]||0;}

var chart=echarts.init(document.getElementById("gpsChart"));

function rows2025(ex){
 return BASE25.map(function(b){
  var sales=b[3]-(ex?warrOf(b[0]):0);
  return {db:b[0],uio:b[1],wallet:b[2],sales:sales,gps:sales/b[2]};
 });
}
function rowsHist(year){
 return HIST.filter(function(r){return r.year===year;}).map(function(r){
  return {db:r.db,uio:r.uio_total,wallet:r.wallet,sales:r.sales,gps:r.gps};
 });
}
function rows2026(ex,upl){
 var b25={};
 BASE25.forEach(function(b){b25[b[0]]={wallet:b[2],sales:b[3]-(ex?warrOf(b[0]):0)};});
 return BASE25.map(function(b){
  var db=b[0],u=UIO26[db],rt=rateOf(db);
  var wallet=u[0]*rt[0]+u[1]*rt[1]+u[2]*rt[2];
  var gBase=b25[db].sales/b25[db].wallet;
  var gProj=gBase+upl/100;
  var sales=gProj*wallet;
  return {db:db,uio:u[0]+u[1]+u[2],u:u,rt:rt,wallet:wallet,gBase:gBase,gps:gProj,sales:sales,delta:sales-b25[db].sales,pp:wallet*0.01};
 });
}

function render(){
 var view=document.getElementById("viewSel").value;
 var ex=document.getElementById("warrSel").value==="ex";
 var upl=parseFloat(document.getElementById("uplift").value)||0;
 var warrSel=document.getElementById("warrSel");
 var isProj=view==="2026";
 var isHist=view==="2022"||view==="2023"||view==="2024";
 warrSel.disabled=isHist;
 if(isHist&&ex){ex=false;}
 document.getElementById("bpCard").style.display=isProj?"block":"none";

 var rows = isProj?rows2026(ex,upl):(view==="2025"?rows2025(ex):rowsHist(parseInt(view,10)));
 rows.sort(function(x,y){return y.gps-x.gps;});

 var thead=document.getElementById("thead"), tbody=document.getElementById("tbody");
 var totS=0,totW=0,totD=0;
 if(isProj){
  thead.innerHTML="<tr><th>Distributor</th><th>UIO CV 26</th><th>UIO F/MD 26</th><th>UIO LCV 26</th>"
   +"<th>Rate CV €</th><th>Rate F/MD €</th><th>Rate LCV €</th><th>Wallet FY26 €</th>"
   +"<th>GPS 2025</th><th>GPS FY26 proj</th><th>Proj. sales €</th><th>Δ vs 2025 €</th><th>+1pp = €</th></tr>";
  tbody.innerHTML="";
  rows.forEach(function(o){
   totS+=o.sales;totW+=o.wallet;totD+=o.delta;
   var tr=document.createElement("tr");
   tr.innerHTML="<td><b>"+o.db+"</b></td><td>"+fmt0(o.u[0])+"</td><td>"+fmt0(o.u[1])+"</td><td>"+fmt0(o.u[2])+"</td>"
    +'<td class="in"><input type="number" step="10" data-db="'+o.db+'" data-k="0" value="'+o.rt[0]+'"></td>'
    +'<td class="in"><input type="number" step="10" data-db="'+o.db+'" data-k="1" value="'+o.rt[1]+'"></td>'
    +'<td class="in"><input type="number" step="10" data-db="'+o.db+'" data-k="2" value="'+o.rt[2]+'"></td>'
    +"<td>"+fmt0(o.wallet)+"</td><td>"+(100*o.gBase).toFixed(1)+"%</td>"
    +'<td class="'+gpsClass(o.gps)+'">'+(100*o.gps).toFixed(1)+"%</td>"
    +"<td>"+fmt0(o.sales)+"</td><td>"+fmt0(o.delta)+"</td><td>"+fmt0(o.pp)+"</td>";
   tbody.appendChild(tr);
  });
  tbody.querySelectorAll("input").forEach(function(inp){
   inp.addEventListener("change",function(){
    rateOf(inp.dataset.db)[parseInt(inp.dataset.k,10)]=parseFloat(inp.value)||0;
    render();
   });
  });
  document.getElementById("tblTitle").textContent="FY2026 projection — rates and uplift adjustable (blue)";
  document.getElementById("footNote").innerHTML="• Projection = (GPS 2025 "+(ex?"ex":"incl.")+" warranty + uplift) × FY26 wallet (UIO 2026F × rate). Defaults: standard Rate Table, +1.0pp.<br>• UMI sales include Shell products. IUK/UMI warranty not split (LCV file has no distributor column) — ex-warranty view unchanged for them.<br>• ITUK FY26 UIO: LD 23,210 / F+MD 963 from UIO v17 projection.";
  var bpProj=rows.filter(function(o){return o.db==="ITUK";})[0];
  document.getElementById("bpProj").textContent=fmtM(bpProj.sales);
  var gap=bpProj.sales-BP.iszeEUR;
  document.getElementById("bpGap").textContent=(gap<0?"−":"+")+fmtM(Math.abs(gap)).slice(1);
  document.getElementById("bpGap").className=gap<0?"r":"g";
  document.getElementById("bpNeed").textContent=(100*BP.iszeEUR/bpProj.wallet).toFixed(1)+"% (+"+((100*BP.iszeEUR/bpProj.wallet)-100*bpProj.gBase).toFixed(1)+"pp)";
 } else {
  thead.innerHTML="<tr><th>Distributor</th><th>Total UIO</th><th>Wallet €</th><th>Sales €"+(ex?" (ex. warr)":"")+"</th><th>€/unit</th><th>GPS %</th><th>+1pp = €</th></tr>";
  tbody.innerHTML="";
  rows.forEach(function(o){
   totS+=o.sales;totW+=o.wallet;
   var tr=document.createElement("tr");
   tr.innerHTML="<td><b>"+o.db+"</b></td><td>"+fmt0(o.uio)+"</td><td>"+fmt0(o.wallet)+"</td><td>"+fmt0(o.sales)+"</td>"
    +"<td>"+fmt0(o.sales/o.uio)+"</td>"
    +'<td class="'+gpsClass(o.gps)+'">'+(100*o.gps).toFixed(1)+"%</td><td>"+fmt0(o.wallet*0.01)+"</td>";
   tbody.appendChild(tr);
  });
  document.getElementById("tblTitle").textContent=view+" actuals"+(view==="2025"?" — v8 baseline":" — history (warranty split n/a)");
  document.getElementById("footNote").innerHTML="• 2022–2024 from GPS history (incl. warranty; no warranty split available). 2025 = v8 baseline (updated UIO cut).<br>• CV warranty CY2025 (€): ITUK 374K · UTI 256K · Germany 5.6K · Greece 1.5K · Malta 1.5K · Cyprus 0.4K. IUK/UMI (D-Max) not splittable.";
 }
 var netGps=totW>0?100*totS/totW:0;
 document.getElementById("netLine").textContent=(isProj?"Network FY26: ":"Network "+view+": ")+"sales €"+(totS/1e6).toFixed(1)+"M · wallet €"+(totW/1e6).toFixed(1)+"M · GPS "+netGps.toFixed(1)+"%"+(isProj?" · Δ vs 2025 +€"+(totD/1e6).toFixed(2)+"M":"");

 chart.setOption({
  grid:{left:80,right:55,top:10,bottom:25},
  xAxis:{type:"value",max:115,axisLabel:{formatter:"{value}%"}},
  yAxis:{type:"category",data:rows.map(function(o){return o.db;}).reverse(),axisLabel:{fontSize:11}},
  series:[{type:"bar",data:rows.map(function(o){
    var v=Math.round(1000*o.gps)/10;
    var col=v>=55?"#0a7d33":(v>=35?"#c98a00":"#CC0E1E");
    return {value:v,itemStyle:{color:col}};
   }).reverse(),
   label:{show:true,position:"right",formatter:"{c}%"},barWidth:"60%"}],
  tooltip:{trigger:"axis",axisPointer:{type:"shadow"}}
 },true);
}
["viewSel","warrSel","uplift"].forEach(function(id){document.getElementById(id).addEventListener("change",render);});
document.getElementById("btnReset").addEventListener("click",function(){rateState={};document.getElementById("uplift").value=1.0;render();});
render();
window.addEventListener("resize",function(){chart.resize();});
</script>
</body></html>
"""

out1 = r"C:\Users\jerom\Desktop\claude\ISZE\Dashboards\ISZE_GPS_TargetStudy_Reconciliation_Dashboard.html"
out2 = r"C:\Users\jerom\Desktop\claude\ISZE\Dashboards\ISZE_GPS_Network_SPU_Dashboard.html"

h1 = D1.replace("%%CSS%%", BASE_CSS).replace("%%STAMP%%", STAMP).replace("%%ECHARTS%%", ECHARTS)
h2 = (D2.replace("%%CSS%%", BASE_CSS).replace("%%STAMP%%", STAMP)
        .replace("%%HIST%%", json.dumps(HIST)).replace("%%BASE25%%", json.dumps(BASE25))
        .replace("%%WARR%%", json.dumps(WARR)).replace("%%UIO26%%", json.dumps(UIO26))
        .replace("%%RATES%%", json.dumps(RATES)).replace("%%ECHARTS%%", ECHARTS))

io.open(out1, "w", encoding="utf-8").write(h1)
io.open(out2, "w", encoding="utf-8").write(h2)
print("written", out1)
print("written", out2)
