
(function(){
"use strict";
var D = JSON.parse(document.getElementById('pmte-data').textContent);
var NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee', MUTED='#6b6257', RULE='#d8d2c6',
    AMBER='#b7791f', GREEN='#2f6b45', PALE='#eef3f9';
var LANE_TAG={};
Object.keys(D.lane).forEach(function(m){ LANE_TAG[m]=D.lane[m]; });
/* The internal file name of a market's schedule is never printed: the reader gets the schedule
   named by what it is. */
function laneName(m){
  return LANE_TAG[m]==='agreed' ? 'the schedule agreed for that market'
                                : 'the internal service schedule';
}
function eur(v){ if(v===null||v===undefined) return 'n/a';
  return 'EUR ' + Math.round(v).toLocaleString('en-GB'); }
function eurm(v){ if(v===null||v===undefined) return 'n/a';
  return 'EUR ' + (v/1e6).toFixed(2) + 'M'; }
function pct(v,d){ if(v===null||v===undefined) return 'n/a';
  return (100*v).toFixed(d===undefined?1:d) + '%'; }
function num(v){ return (v===null||v===undefined)?'n/a':Math.round(v).toLocaleString('en-GB'); }

/* tooltip */
var tip=document.getElementById('tip');
document.addEventListener('mouseover',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(!t) return; tip.innerHTML=t.getAttribute('data-tip'); tip.style.opacity='1';
});
document.addEventListener('mousemove',function(e){
  if(tip.style.opacity!=='1') return;
  var x=e.clientX+14, y=e.clientY+14;
  if(x+330>window.innerWidth) x=e.clientX-340;
  if(y+120>window.innerHeight) y=e.clientY-130;
  tip.style.left=x+'px'; tip.style.top=y+'px';
});
document.addEventListener('mouseout',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(t) tip.style.opacity='0';
});

Chart.defaults.font.family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif";
Chart.defaults.font.size=12;
Chart.defaults.color='#4a443b';
var charts={};
function mk(id,cfg){ if(charts[id]) charts[id].destroy(); charts[id]=new Chart(document.getElementById(id),cfg); }

/* One flat helper builds every cartesian chart's options, so no chart has to nest five deep. */
function chartOpts(o){
  o=o||{};
  var horiz=!!o.horizontal;
  var out={responsive:true,maintainAspectRatio:false,indexAxis:horiz?'y':'x',
    plugins:{legend:o.legend||{display:false},
      tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10}},
    scales:horiz
      ? {x:{grid:{color:RULE},beginAtZero:true},y:{grid:{display:false}}}
      : {x:{grid:{display:false}},y:{grid:{color:RULE},beginAtZero:true}}};
  if(o.label) out.plugins.tooltip.callbacks={label:o.label};
  if(o.tickX) out.scales.x.ticks=o.tickX;
  return out;
}

function barData(labels,values,colors){
  return {labels:labels,datasets:[{data:values,backgroundColor:colors,borderRadius:3}]};
}

/* ─┬─ every chart that draws more than one series gets a visible key, in words ──
   Chart.js legends are off by default here, so a multi-series chart with no key is unreadable.
   key() writes a legend under the canvas naming each colour; axisLabel() names a single series
   on the axis instead, so a one-series chart is not left bare either. */
/* ─────────── chart keys ─────────── */
function key(id,items){
  var host=document.getElementById(id);
  if(!host) return;
  var html=items.map(function(it){
    var sw=it.line
      ? '<i style="background:'+it.c+';height:3px;border-radius:2px;vertical-align:2px"></i>'
      : '<i style="background:'+it.c+'"></i>';
    return '<span'+(it.tip?' data-tip="'+it.tip+'"':'')+'>'+sw+it.l+'</span>';
  }).join('');
  var box=host.querySelector('.legend');
  if(!box){
    box=document.createElement('div'); box.className='legend';
    if(host.firstChild && host.firstChild.nextSibling){
      host.insertBefore(box, host.firstChild.nextSibling);
    } else { host.appendChild(box); }
  }
  box.innerHTML=html;
}
function axisLabel(id,text){
  var host=document.getElementById(id);
  if(!host) return;
  var box=host.querySelector('.legend.axis');
  if(!box){ box=document.createElement('div'); box.className='legend axis'; host.appendChild(box); }
  box.innerHTML='<span>'+text+'</span>';
}

/* ─────────── controls */
var selM=document.getElementById('selMarket'), selC=document.getElementById('selClock'),
    selY=document.getElementById('selYear'), selF=document.getElementById('selFamily');
D.markets.forEach(function(m){
  var o=document.createElement('option'); o.value=m; o.textContent=m; selM.appendChild(o);
});
selM.value='ITUK';

var CY_YEARS=[2023,2024,2025,2026], FY_YEARS=[2023,2024,2025,2026,2027];

/* What each clock actually covers, in words, printed under the controls and reused in tooltips.
   The ISZE year runs April to March and is named for the year it closes in, so ISZE 2026 is
   April 2025 to March 2026 — the reader should not have to work that out. */
function fySpan(y){ return 'Apr '+(y-1)+' – Mar '+y; }
function clockLabel(clock,year){
  return clock==='FY' ? ('ISZE year '+year+' ('+fySpan(year)+')')
                      : ('calendar year '+year+' (Jan–Dec '+year+')');
}
function clockShort(clock,year){
  return clock==='FY' ? ('ISZE '+year+' (Apr '+(year-1)+'–Mar '+year+')')
                      : ('calendar '+year);
}
function updateClockNote(){
  var clock=selC.value, ys=(clock==='CY'?CY_YEARS:FY_YEARS);
  var y=parseInt(selY.value,10); if(isNaN(y)) y=ys[ys.length-2];
  document.getElementById('clockNote').innerHTML=
    'Reading on the <b>'+clockShort(clock,y)+'</b>. '
    +(clock==='FY'
      ? 'An ISZE year is named for the year it <i>closes</i> in, so ISZE '+y+' covers April '
        +(y-1)+' to March '+y+'. The other option is the calendar year, January to December. '
        +'The billed-sales chart and its KPI follow this control; the fleet, gap and capture panels '
        +'are annual and do not.'
      : 'The other option is the ISZE year, which runs April to March and is named for the year '
        +'it closes in, so ISZE '+y+' is April '+(y-1)+' to March '+y+'. '
        +'The billed-sales chart and its KPI follow this control; the fleet, gap and capture panels '
        +'are annual and do not.');
}

function fillYears(){
  var ys=selC.value==='CY'?CY_YEARS:FY_YEARS;
  var prev=parseInt(selY.value,10);
  selY.innerHTML='';
  ys.forEach(function(y){
    var o=document.createElement('option'); o.value=y;
    o.textContent=(selC.value==='FY'?'ISZE ':'CY ')+y;
    selY.appendChild(o);
  });
  selY.value=ys.indexOf(prev)>=0?prev:(selC.value==='CY'?2025:2026);
  updateClockNote();
}
function fillFamilies(){
  var m=selM.value, cats=Object.keys(D.catLabels)
      .filter(function(c){return D.catGap[m].some(function(r){return r.cat===c;});});
  var prev=selF.value;
  selF.innerHTML='';
  cats.forEach(function(c){
    var o=document.createElement('option'); o.value=c; o.textContent=D.catLabels[c];
    selF.appendChild(o);
  });
  selF.value=cats.indexOf(prev)>=0?prev:cats[0];
}
fillYears(); fillFamilies();

/* ─────────── render */
function render(){
  var m=selM.value, clock=selC.value, year=parseInt(selY.value,10), fam=selF.value;
  var bands=D.fleet[m]||[], cap=D.capture[m]||{}, bl=D.billed[m]||{CY:{},FY:{}};

  /* lane notice */
  var lanes={}; Object.keys(D.lane).forEach(function(k){lanes[D.lane[k]]=1;});
  document.getElementById('laneNotice').innerHTML=
    '<div class="note"><b>'+m+'</b> runs <span class="tag '+LANE_TAG[m]+'">'+laneName(m)
    +'</span>'
    +(LANE_TAG[m]==='agreed'
      ? ' — the schedule agreed with the distributor for this market: filters 1.25 visits a year, '
        +'clutch and brakes 0.5, a 22,389-vehicle fleet.'
      : ' — standard trucks 0.5 visits a year, heavy 0.667, the D-Max pickup 1.0.')
    +' The network carries <b>two</b> interval schedules and they are never averaged or added '
    +'together. A figure from one schedule is not comparable with a figure from the other.'
    +'</div>';

  /* KPIs — every derived number carries its own formula */
  var k=[];
  var yc=cap[year]||cap[2025]||{};
  var totUio=bands.reduce(function(a,b){return a+b.uio;},0);
  var totExp=bands.reduce(function(a,b){return a+b.expected;},0);
  k.push({v:num(totUio),l:'vehicles in service, all bands',
    tip:'Sum of the four tonnage bands for <b>'+m+'</b>: '+bands.map(function(b){
      return b.label+' '+num(b.uio);}).join(', ')+'.<br>This is the 2025 fleet estimate and it is used '
      +'for every year, because mileage is not measured per market. Snapshot '+D.snapshot+'.'});
  k.push({v:num(totExp),l:'service jobs expected a year'
    +(year!==2025?' (2025 fleet)':''),
    tip:'Vehicles in each band x the visits a year implied by the interval schedule for that band, '
      +'summed over the 14 service families.<br>Flat year on year by construction: the fleet is the '
      +'2025 estimate. Actual billing is not split by band.'});
  k.push({v:eur(yc.gap_eur),l:'gap to modelled target spend, '+year+' — '+m,cls:'warn',
    tip:'Modelled target spend minus what was actually billed, at market level, '+year+'.<br>Target spend is the '
      +'fleet x the interval schedule x the category factor. It is a ceiling, not a forecast.<br>'
      +'Same figure on both clocks: the gap is built on the 2025 fleet and annual billing, so it does '
      +'not split by ISZE year. Not observed at tonnage-band level.'});
  k.push({v:pct(yc.capture),l:'share of expected demand bought, '+year,
    tip:'Units actually bought divided by units expected, '+year+', across the 14 service '
      +'families.<br>Above 100% means the customer bought more than its own fleet count implies it '
      +'needs, which usually means it serves vehicles not in that fleet count.<br>'
      +'Same figure on both clocks: it is an annual rate against the 2025 fleet, not an ISZE-year cut.'});
  var bv=bl[clock]&&bl[clock][year];
  k.push({v:eurm(bv),l:'service parts billed, '+clockLabel(clock,year),
    tip:'Net parts billed to '+m+' in '+clockLabel(clock,year)+'.<br>'
      +(clock==='FY'
        ? 'The ISZE year runs April to March and is named for the year it closes in, so ISZE '
          +year+' is April '+(year-1)+' to March '+year+'.'
        : 'The calendar year runs January to December.')
      +'<br>The other clock gives a different split of the same billing. The two are never averaged.'});
  var g25=(D.gps[m]||[]).filter(function(x){return x.year===year;})[0];
  k.push({v:(g25&&g25.spu)?('EUR '+g25.spu.toFixed(0)):'n/a',l:'parts billed per vehicle, '+year,
    tip:'Parts billed divided by vehicles in service, '+year+'.<br>Fleet source for this market: '
      +((g25&&g25.uio_source)||'the band model')+'.'+(g25&&g25.spu_ex_warranty
      ? '<br>Excluding warranty: EUR '+g25.spu_ex_warranty.toFixed(0)+'.' : '')});
  document.getElementById('kpis').innerHTML=k.map(function(x){
    return '<div class="kpi '+(x.cls||'')+'" data-tip="'+x.tip+'"><div class="v">'+x.v
      +'</div><div class="l">'+x.l+'</div></div>';
  }).join('');

  /* fleet mix donut (<=5 segments, one customer). One fixed colour per band, so a band keeps its
     colour from customer to customer instead of taking whatever position it lands in. */
  var BANDCOL={'LCV_D-Max':GREEN,'3.5t_N35':NAVY,'5.5t_N50_N55':AMBER,'7.5t_N50_N62_N75':TERRA,'F_series_MD_heavy':'#7a8ba6'};
  var fl=bands.map(function(b){return {band:b.label,uio:b.uio,col:BANDCOL[b.band]||MUTED};});
  mk('c_fleet',{type:'doughnut',
    data:{labels:fl.map(function(x){return x.band;}),
      datasets:[{data:fl.map(function(x){return x.uio;}),
        backgroundColor:fl.map(function(x){return x.col;}),borderColor:'#fff',borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'58%',
      plugins:{legend:{display:false},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{label:function(c){
            var tot=fl.reduce(function(a,b){return a+b.uio;},0);
            return c.label+': '+num(c.raw)+' vehicles ('+(100*c.raw/tot).toFixed(1)+'% of the fleet)';}}}}}});
  document.getElementById('lg_fleet').innerHTML=fl.map(function(x,i){
    var tot=fl.reduce(function(a,b){return a+b.uio;},0);
    return '<span data-tip="Fleet in this band, from the derived band model.<br>'
      +'Share of this customer total fleet. Snapshot '+D.snapshot+'.">'
      +'<i style="background:'+x.col+'"></i>'+x.band
      +' — '+num(x.uio)+' ('+(100*x.uio/tot).toFixed(0)+'%)</span>';
  }).join('');

  /* expected demand by band */
  mk('c_expected',{type:'bar',data:barData(bands.map(function(b){return b.label;}),
      bands.map(function(b){return b.expected;}),NAVY),
    options:chartOpts({horizontal:true,label:function(c){
      var b=bands[c.dataIndex];
      return [num(b.expected)+' jobs a year in this band',
              num(b.uio)+' vehicles in service, '+b.visits+' visits each',
              'Band rows are modelled. Billing does not split by band.'];}})});
  axisLabel('h_expected','One series: <b>expected / modelled service jobs a year</b> in each tonnage band. '
    +'The horizontal scale is jobs, not euro. Navy bars only — no second series.');
  document.getElementById('n_expected').innerHTML='<b>Expected / modelled by tonnage band.</b> Service jobs per band, from the fleet in '
    +'that band and the interval schedule this market runs. <b>The fleet vintage is 2025 for every '
    +'year</b>, so expected demand is flat over time by construction — only billing and the capture '
    +'rate move. <b>Actual billed at market level</b> — the billing carries no vehicle, so the units '
    +'actually bought cannot be split across bands; the bands carry the expectation, and the market carries the actual.';

  /* gap by band x family — best form: ranked euro bars */
  var gapRows=[];
  D.catGap[m].forEach(function(r){
    gapRows.push({k:D.catLabels[r.cat]||r.cat, gap:r.gap_eur, expected:r.expected, cat:r.cat});
  });
  gapRows.sort(function(a,b){return b.gap-a.gap;});
  gapRows=gapRows.slice(0,12);
  mk('c_gap',{type:'bar',
    data:barData(gapRows.map(function(r){return r.k;}),gapRows.map(function(r){return r.gap;}),
      gapRows.map(function(r){return r.gap<0?GREEN:TERRA;})),
    options:chartOpts({horizontal:true,label:function(c){
      var r=gapRows[c.dataIndex];
      return [eur(r.gap)+' expected-demand share of modelled gap in '+r.k,
              num(r.expected)+' jobs a year expected in this family',
              'Allocated to the family by its share of expected demand — not observed at band.',
              'Market level: the billing carries no vehicle.'];}})});
  key('h_gap',[
    {c:TERRA,l:'modelled opportunity (expected-demand share)',tip:'Market-level modelled gap allocated to this service family by its share of expected demand. '
      +'Not observed billing by tonnage band. The bar length is the euro share of the modelled gap.'},
    {c:GREEN,l:'over-bought against the fleet model',
      tip:'A negative gap: the family billed more than this fleet implies it needs. Usually means the '
      +'customer serves vehicles outside its own fleet count.'}]);
  document.getElementById('n_gap').innerHTML='Ranked by euro, because quantity alone says nothing. '
    +'Each bar is the <b>expected-demand share of the modelled gap</b> in that service family for <b>'+m+'</b> in 2025 — '
    +'allocated by share of expected demand, not observed at tonnage-band level. The euro is the decision currency; the family says '
    +'where modelled opportunity concentrates; the fleet base is in the box above. '
    +'<b>Actual billed at market level</b> — the billing carries no vehicle identification, so a band or '
    +'family column must never be summed against the market actual or it double-counts.';

  /* family table */
  document.getElementById('t_catgap').innerHTML='<table><thead><tr><th>Service family</th>'
    +'<th class="n">Jobs expected</th><th class="n">Units bought</th><th class="n">Modelled gap</th>'
    +'</tr></thead><tbody>'
    +D.catGap[m].slice().sort(function(a,b){return b.gap_eur-a.gap_eur;}).slice(0,8).map(function(r){
      return '<tr><td class="db">'+r.label+'</td><td class="n">'+num(r.expected)+'</td>'
        +'<td class="n">'+num(r.actual)+'</td><td class="n">'+eur(r.gap_eur)+'</td></tr>';
    }).join('')+'</tbody></table>'
    +'<p class="small" style="margin-top:8px">Units bought is the whole market figure for that '
    +'family, repeated on every band row on purpose. It is not band-specific. '
    +'Jobs expected and modelled gap are annual against the 2025 fleet, the same on both clocks; '
    +'only the billed-sales chart and its KPI move with the ISZE-year control.</p>';


  /* family mix donut: one customer, one family, <=4 segments */
  var fm=(D.famMix[m]||{})[fam];
  if(fm){
    mk('c_mix',{type:'doughnut',
      data:{labels:['Genuine Isuzu','Value line'],
        datasets:[{data:[fm.genuine_units,fm.value_units],
          backgroundColor:[NAVY,TERRA],borderColor:'#fff',borderWidth:2}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:'55%',
        plugins:{legend:{display:true,position:'bottom',labels:{boxWidth:11,padding:12}},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{label:function(c){
              var tot=fm.genuine_units+fm.value_units;
              return c.label+': '+num(c.raw)+' units'
                +(tot?' ('+(100*c.raw/tot).toFixed(1)+'%)':'')+', 2025';}}}}}});
    key('h_mix',[
      {c:NAVY,l:'genuine Isuzu line',tip:'Units billed as the OE Isuzu part number for this family in 2025.'},
      {c:TERRA,l:'value line (BVP)',tip:'Units billed as a Best Value Parts alternative for the same family in 2025.'}]);
    document.getElementById('n_mix').innerHTML='Of the <b>'+D.catLabels[fam]+'</b> units bought by '
      +m+' in 2025, '+num(fm.genuine_units)+' were the genuine line and '+num(fm.value_units)
      +' the value line. Two segments only, so a donut is the right form here.';
  }

  /* evolution, both clocks */
  var periods=(clock==='CY'?CY_YEARS:FY_YEARS).filter(function(y){return bl[clock]&&bl[clock][y]!==undefined;});
  mk('c_evo',{type:'bar',
    data:barData(periods.map(function(y){return (clock==='FY'?'ISZE ':'CY ')+y;}),
      periods.map(function(y){return bl[clock][y];}),
      periods.map(function(y){return (clock==='CY'&&y===2026)?AMBER:NAVY;})),
    options:chartOpts({label:function(c){
      var y=periods[c.dataIndex];
      var prev=(clock==='CY'?CY_YEARS:FY_YEARS)[ (clock==='CY'?CY_YEARS:FY_YEARS).indexOf(y)-1 ];
      var pv=bl[clock][prev];
      var s=eur(c.raw)+' billed in '+clockLabel(clock,y);
      if(pv) s+=' ('+((c.raw/pv-1)>=0?'+':'')+(100*(c.raw/pv-1)).toFixed(1)+'% against '+prev+')';
      if(clock==='CY'&&y===2026) s+=' - the calendar year is not complete';
      return s;}})});
  key('h_evo',[
    {c:NAVY,l:'a complete year'},
    {c:AMBER,l:'calendar 2026 — part year, January to the last month with billing',
     tip:'A part year compared against complete years understates 2026. It is shown in amber so it '
       +'cannot be read as a fall.'}]);
  document.getElementById('n_evo').innerHTML=(clock==='FY'
    ? 'The ISZE year runs April to March and is named for the year it closes in, so <b>ISZE 2026 is '
      +'April 2025 to March 2026</b>. '
    : 'The calendar year runs January to December, so <b>calendar 2026 is January 2026 to December '
      +'2026</b> and is not yet complete. ')
    +'<b>Calendar 2026 is shown in amber because it is not a complete year</b> — comparing it with a '
    +'full year understates it. The two clocks are the same underlying billing cut two ways; they '
    +'are shown separately and never averaged.';

  /* AIM level 1 change bars */
  var l1=D.l1[m][clock]||[];
  var byL1={}, pers={};
  l1.forEach(function(r){ (byL1[r.l1]=byL1[r.l1]||{})[r.period]=r.eur;
    pers[r.period]=1; });
  var sortedP=Object.keys(pers).map(Number).sort(function(a,b){return a-b;});
  var latest=sortedP.filter(function(p){return !(clock==='CY'&&p===2026);}).pop();
  var prior=sortedP.filter(function(p){return p<latest;}).pop();
  var l1rows=Object.keys(byL1).map(function(k){
    var a=byL1[k][latest]||0, b=prior!==undefined?(byL1[k][prior]||0):0;
    return {k:k, now:a, before:b, delta:a-b};
  }).filter(function(r){return r.now||r.before;});
  l1rows.sort(function(a,b){return a.delta-b.delta;});
  l1rows=l1rows.slice(0,12);
  mk('c_l1',{type:'bar',
    data:barData(l1rows.map(function(r){return r.k;}),l1rows.map(function(r){return r.delta;}),
      l1rows.map(function(r){return r.delta<0?TERRA:GREEN;})),
    options:chartOpts({horizontal:true,label:function(c){
      var r=l1rows[c.dataIndex];
      return [eur(r.delta)+' change',
              'was '+eur(r.before)+' in '+prior+', now '+eur(r.now)+' in '+latest];}})});

  /* AIM level 2 change bars */
  var l2=(D.l2[m]||[]).filter(function(r){return r.clk===clock;});
  var byL2={}, pers2={};
  l2.forEach(function(r){ var k2=r.l2;
    (byL2[k2]=byL2[k2]||{})[r.period]=(byL2[k2][r.period]||0)+r.eur; pers2[r.period]=1; });
  var sp2=Object.keys(pers2).map(Number).sort(function(a,b){return a-b;});
  var latest2=sp2.filter(function(p){return !(clock==='CY'&&p===2026);}).pop();
  var prior2=sp2.filter(function(p){return p<latest2;}).pop();
  var l2rows=Object.keys(byL2).map(function(k){
    var a=byL2[k][latest2]||0, b=prior2!==undefined?(byL2[k][prior2]||0):0;
    return {k:k, now:a, before:b, delta:a-b};
  }).sort(function(a,b){return a.delta-b.delta;}).slice(0,14);
  mk('c_l2',{type:'bar',
    data:barData(l2rows.map(function(r){return r.k;}),l2rows.map(function(r){return r.delta;}),
      l2rows.map(function(r){return r.delta<0?TERRA:'#7a8ba6';})),
    options:chartOpts({horizontal:true,label:function(c){
      var r=l2rows[c.dataIndex];
      return [eur(r.delta)+' change',
              'was '+eur(r.before)+' in '+prior2+', now '+eur(r.now)+' in '+latest2];}})});
  key('h_l1',[
    {c:TERRA,l:'billed parts fell against the previous year'},
    {c:GREEN,l:'billed parts rose against the previous year'}]);
  key('h_l2',[
    {c:TERRA,l:'billed parts fell against the previous year'},
    {c:'#7a8ba6',l:'billed parts rose against the previous year'}]);
  document.getElementById('n_aim').innerHTML='Both charts compare the latest complete year with the '
    +'year before it on the chosen clock, so a bar pointing left is a fall in billed parts on that product line '
    +'and a bar pointing right is a rise. AIM level 1 is the product group; level 2 is the '
    +'line inside it. Terracotta means a fall. These are observed billed euro, not units or modelled gap.';

  /* network ranked gap */
  var ng=D.markets.map(function(x){
    var c=D.capture[x]&&D.capture[x][2025]; return {m:x, gap:c?c.gap_eur:0, cap:c?c.capture:null};
  }).sort(function(a,b){return b.gap-a.gap;});
  mk('c_netgap',{type:'bar',
    data:barData(ng.map(function(r){return r.m;}),ng.map(function(r){return r.gap;}),
      ng.map(function(r){return r.m===m?TERRA:NAVY;})),
    options:chartOpts({label:function(c){
      var r=ng[c.dataIndex];
      return [eur(r.gap)+' gap to modelled target spend in 2025',
              'share of expected demand bought: '+(r.cap!==null?pct(r.cap):'n/a'),
              'Market-level modelled opportunity — not band-level observed loss.',
              'The customer you have selected is highlighted.'];}})});
  var selRow=ng.filter(function(r){return r.m===m;})[0];
  key('h_netgap',[
    {c:TERRA,l:'the selected customer ('+m+')'
      +(selRow?' — '+eur(selRow.gap)+', '+pct(selRow.cap)+' of expected demand bought':'')},
    {c:NAVY,l:'every other customer'}]);
  document.getElementById('n_netgap').innerHTML='Gap to modelled target spend by customer, 2025, largest first. '
    +'Network modelled opportunity total <b>'+eurm(D.net.gap2025)+'</b> against <b>'+eurm(D.net.actual2025)
    +'</b> actually billed at market level. The selected customer is in terracotta. '
    +'A customer above 100% has bought more than its own fleet implies it needs, which usually means '
    +'it serves vehicles that are not in its own fleet count. '
    +'<b>Scope:</b> the '+D.markets.length+' customers the service model covers. The billing extract '
    +'also carries '+D.scopeNote.markets.join(', ')+', which are outside that scope and are '
    +'<b>'+D.scopeNote.sharePct+'%</b> of total parts billed (EUR '+eurm(D.scopeNote.eur)+' on the '
    +'complete year). They are excluded here rather than added to a network total they do not belong to.';

  /* small multiples of capture by year */
  var palette={2023:'#c9d3e0',2024:'#8fa3c0',2025:NAVY,2026:AMBER};
  /* Four shades and no Chart.js legend, so the key is written here in words. */
  document.getElementById('lg_sm').innerHTML=[2023,2024,2025,2026].map(function(y){
    return '<span><i style="background:'+palette[y]+'"></i>'
      +(y===2026?'calendar 2026 (part year)':'calendar '+y)+'</span>';
  }).join('');

  var smTip='Pieces bought as a share of the pieces the fleet implies it needs. 100% means the '
    +'customer bought exactly what its own fleet implies.<br>Flat across years by construction: the '
    +'fleet is the 2025 estimate. What changes is the billing.<br>Snapshot '+D.snapshot+'.';
  document.getElementById('sm_grid').innerHTML=D.markets.map(function(x){
    var c=D.capture[x]||{};
    var bars=[2023,2024,2025,2026].map(function(y){
      var v=c[y]?c[y].capture:null;
      if(v===null||v===undefined) return '<div style="height:0"></div>';
      var h=Math.max(2,Math.min(100,v*100));
      return '<div title="'+y+': '+pct(v)+'" data-tip="Share of expected demand bought in '+y
        +': <b>'+pct(v)+'</b><br>Expected '+num(c[y].expected)+' jobs, '+num(c[y].actual)
        +' units billed.<br>Snapshot '+D.snapshot+'." style="height:'+h+'px;background:'
        +palette[y]+';border-radius:2px 2px 0 0;flex:1"></div>';
    }).join('');
    return '<div style="cursor:pointer" data-tip="<b>'+x+'</b> &middot; '+laneName(x)+'<br>'
      +smTip+'<br>2023 '+pct(c[2023]&&c[2023].capture)+' &middot; 2024 '+pct(c[2024]&&c[2024].capture)
      +'<br>2025 '+pct(c[2025]&&c[2025].capture)+' &middot; 2026 '+pct(c[2026]&&c[2026].capture)+'">'
      +'<div style="display:flex;align-items:flex-end;gap:2px;height:100px;border-bottom:1px solid '
      +RULE+'">'+bars+'</div>'
      +'<div class="lbl" style="color:'+(x===m?TERRA:NAVY)+'">'+x+'</div></div>';
  }).join('');
  document.getElementById('n_sm').innerHTML='Every customer on one shared scale, so the bars are '
    +'comparable across panels. Three shades for 2023, 2024 and 2025; amber is the incomplete '
    +'calendar 2026. Where a market shows no amber, its 2026 billing is not in the model. '
    +'A short bar means the customer bought a small share of what its own fleet implies it needs.';

  /* GPS spend per vehicle */
  var gs=(D.gps[m]||[]).filter(function(r){return r.spu!==null;});
  mk('c_gps',{type:'bar',
    data:{labels:gs.map(function(r){return r.year;}),
      datasets:[{data:gs.map(function(r){return r.spu;}),backgroundColor:NAVY,borderRadius:3},
        {type:'line',label:'excluding warranty',data:gs.map(function(r){return r.spu_ex_warranty;}),
         borderColor:TERRA,backgroundColor:TERRA,pointRadius:4,fill:false,tension:0,borderWidth:2}]},
    options:chartOpts({legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
      label:function(c){
        var r=gs[c.dataIndex];
        if(c.datasetIndex===1) return 'Excluding warranty: '+eur(r.spu_ex_warranty)+' per vehicle';
        return 'Parts billed per vehicle: '+eur(r.spu)+' on '+num(r.uio)+' vehicles in service';}})});
  key('h_gps',[
    {c:NAVY,l:'parts billed per vehicle in service — all parts',
     tip:'Parts billed in the year divided by the vehicles in service. Includes warranty parts.'},
    {c:TERRA,l:'parts billed per vehicle — excluding warranty',line:true,
     tip:'The same figure with warranty claims removed, because a warranty part is not a customer '
       +'buying a part. Where the warranty split is missing for a year the line breaks.'}]);
  document.getElementById('n_gps').innerHTML='Parts billed to this customer divided by the vehicles '
    +'in service in that year. The terracotta line removes warranty parts, because a warranty claim '
    +'is not a customer buying a part. Where the warranty split is missing for a year the line is '
    +'broken rather than drawn as zero. Fleet figures for this market come from '
    +'<b>'+((gs[0]&&gs[0].uio_source)||'the band model')+'</b>.';

  /* price position, two-sided deviation from the market */
  var po=D.pos[m]||[];
  mk('c_pos',{type:'bar',
    data:barData(po.map(function(r){return r.l1;}),po.map(function(r){return r.idx-1;}),
      po.map(function(r){return r.idx>1?TERRA:'#7a8ba6';})),
    options:chartOpts({horizontal:true,
      tickX:{callback:function(v){return (v>0?'+':'')+v+'x';}},
      label:function(c){var r=po[c.dataIndex];
        return [r.idx.toFixed(2)+' times the competing price',
                r.pns+' part numbers, '+eur(r.billed)+' billed in the latest complete year',
                'Zero means level with the competing price.'];}})});
  key('h_pos',[
    {c:TERRA,l:'above the competing price',tip:'The median of our dealer reference price '
      +'divided by a real competing price is greater than 1.00 in this product group.'},
    {c:'#7a8ba6',l:'at or below it',
     tip:'The same median is 1.00 or lower — level with, or cheaper than, the competing price.'}]);
  document.getElementById('n_pos').innerHTML='Our dealer reference price divided by a real competing '
    +'price, median across the part numbers in each product group. Bars to the right of zero are '
    +'groups where we sit above the independent market. One competing source fanned across markets, '
    +'vintage <b>'+D.compVintage+'</b> — read it as a position, not as a measured transaction price.';

  /* basis table */
  document.getElementById('t_basis').innerHTML='<table><thead><tr><th>Customer</th>'
    +'<th>Interval lane</th><th class="n">3.5 t share of the N-series truck fleet</th>'
    +'<th>Basis</th>'
    +'<th>What the evidence is</th>'
    +'</tr></thead><tbody>'
    +D.basis.map(function(r){
      var unm=r.basis==='unmeasured';
      return '<tr><td class="db">'+r.market+'</td>'
        +'<td><span class="tag '+(LANE_TAG[r.market]==='iml'?'agreed':'internal')+'">'
        +laneName(r.market)+'</span></td>'
        +'<td class="n">'+(unm?'held':(100*r.share).toFixed(1)+'%')+'</td>'
        +'<td>'+(unm?'<span class="tag unm">unmeasured</span>':r.basis)+'</td>'
        +'<td class="small">'+r.note+'</td></tr>';
    }).join('')+'</tbody></table>';

  /* footer */
  document.getElementById('foot').innerHTML='<b>Sources</b> — all read at build time, snapshot '
    +D.snapshot+': the derived service-demand model by tonnage band and service family; the AIM '
    +'evolution model, which carries the billed euro by product group on both clocks; the service '
    +'capture model; the spend-per-vehicle model; the competing-price sample; and the measured band '
    +'shares with their basis. <b>What this page cannot show:</b> the units actually bought are not '
    +'split by tonnage band, because the billing carries no vehicle identification — bands carry the '
    +'expectation and the market carries the actual. The fleet is the 2025 estimate for every year, '
    +'so expected demand is flat over time by construction. Mileage is not measured per market, so '
    +'the interval schedule carries the whole assumption. Tonnage splits for the markets marked '
    +'unmeasured are held, not measured. And the two interval lanes are never combined.';
}

['selMarket','selClock','selYear','selFamily'].forEach(function(id){
  document.getElementById(id).addEventListener('change',function(){
    if(id==='selMarket') fillFamilies();
    render();
  });
});
render();
})();
