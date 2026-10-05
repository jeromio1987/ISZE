var DATA={meta:{snapshot:"",n_dbs:0,nw:{}},dbs:[],groups:[],noprice:[]};
var IUK_ADJ={};
var KM={};
var FAMNET=[];
var NPLIST=[];
var ST={period:"cy",dir:"db",warr:"inc"};
var LOADED=false;
function g(x){return null;}
function q(x){return null;}

function eur(v){ if(v===null||v===undefined||v===''||isNaN(v)) return '\u2014';
  v=+v; var a=Math.abs(v);
  if(a>=1e6) return '\u20AC'+(v/1e6).toFixed(2)+'M';
  if(a>=1e3) return '\u20AC'+Math.round(v/1e3)+'k';
  return '\u20AC'+Math.round(v); }
function eur2(v){ if(v===null||v===undefined||isNaN(v)) return '\u2014';
  v=+v; var a=Math.abs(v);
  if(a>=1e6) return '\u20AC'+(v/1e6).toFixed(2)+'M';
  if(a>=1e3) return '\u20AC'+(v/1e3).toFixed(0)+'k';
  return '\u20AC'+Math.round(v); }
function num(v){ return (v===null||v===undefined||isNaN(v))?'\u2014':Math.round(v).toLocaleString('en-GB'); }
function one(v,s){ return (v===null||v===undefined||isNaN(v))?'\u2014':(+v).toFixed(1)+(s||''); }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function cfg(){ return 'Period '+(ST.period==='cy'?'CY2025 (Jan\u2013Dec)':'FY2025 (Apr\u2013Mar)')
  +' \u00b7 Direction '+(ST.dir==='db'?'ISZE \u2192 DB':'DB \u2192 dealer')
  +' \u00b7 Warranty '+(ST.warr==='inc'?'included':'excluded'); }
function tip(t,f,s,e){ return '<span class="tip"><b>'+t+'</b><span class="tr"><i>Formula</i>'+f
  +'</span><span class="tr"><i>Snapshot &amp; source</i>'+s
  +'</span><span class="tr"><i>Settings that produced this figure</i>'+cfg()
  +'</span><span class="tr warn"><i>Not included</i>'+e+'</span></span>'; }
function g(id){ return document.getElementById(id); }
var $ = g;

// ---------- period/direction aware getters ----------
function demand(r){ if(!r) return null; return r.demand[ST.period]; }
function dealerLeg(r){ if(!r||!r.dealer) return null; return r.dealer[ST.period]; }
function repOf(r){ if(!r||!r.rep) return null; return r.rep[ST.period]; }
function mixOf(r){ if(!r) return null; return r.mix[ST.period]; }
function billOf(r){
  if(!r) return null;
  var k = ST.period+'_'+(ST.warr==='inc'?'inc':'exc');
  var v = r.bill[k];
  return (v===null||v===undefined)?null:v;
}
function billNote(r){
  if(!r) return '';
  var k = ST.period+'_'+(ST.warr==='inc'?'inc':'exc');
  if(r.bill[k]===null||r.bill[k]===undefined){
    if(ST.warr==='exc') return 'no warranty data for this market \u2014 unavailable, not zero';
    return 'no billing extract for this market in this period';
  }
  return '';
}
// the gap column is demand-side when direction is ISZE->DB, dealer-side otherwise
function gapOf(r){
  if(ST.dir==='db'){ var d=demand(r); return d?d.gap:null; }
  var t=dealerLeg(r); return t?t.gap:null;
}
function gapReason(r){
  if(gapOf(r)!==null) return '';
  if(ST.dir==='dealer'){
    if(!r.dealer||!r.dealer.cy) return 'no sales-to-dealer file for this distributor';
    if(ST.period==='fy'&&!r.dealer.fy) return 'dealer file covers only 8 of 11 fiscal months \u2014 excluded, not annualised';
    return 'no sales-to-dealer file for this distributor';
  }
  return 'not in the modelled fleet base (bills parts but has no vehicles-in-service model)';
}
function unboughtOf(r){
  if(ST.dir==='db'){ var d=demand(r); return d?d.nb:null; }
  var t=dealerLeg(r); return t?t.nb:null;
}
function capOf(r){
  if(ST.dir==='db'){ var d=demand(r); return d?d.cap:null; }
  var t=dealerLeg(r); return t?t.cap:null;
}

// ---------- charts ----------
var GROUPC={ 'Filters':'#2b4a78','Brakes':'#c0552d','Clutch & bearings':'#7a8fa8' };
function chart1(){
  var rows=DATA.dbs.filter(function(r){ return demand(r)&&demand(r).gap>0; })
    .sort(function(a,b){ return demand(b).gap-demand(a).gap; });
  if(!rows.length){ g('c1-rows').innerHTML='<p class="small">No demand gap under these settings.</p>'; return; }
  var mx=demand(rows[0]).gap;
  var ticks=''; for(var i=0;i<=4;i++){ ticks+='<span>'+eur2(mx*i/4)+'</span>'; }
  g('c1-axis').innerHTML=ticks;
  var grid=''; for(var i=0;i<=4;i++){ grid+='<i style="left:'+(i*25)+'%"></i>'; }
  var out='<div class="grid">'+grid+'</div>';
  rows.forEach(function(r){
    var d=demand(r), fams=r.fam.slice().sort(function(a,b){ return (b.gap||0)-(a.gap||0); });
    var segs='';
    DATA.groups.forEach(function(gr){
      var v=0;
      fams.forEach(function(f){ if(f.group===gr){ v+=Math.max(0,(ST.period==='fy'?(f.fy_gap||0):(f.gap||0))); } });
      if(v>0){ segs+='<span style="width:'+(v/mx*100)+'%;background:'+GROUPC[gr]+'"></span>'; }
    });
    out+='<div class="brow"><div class="bl">'+esc(r.db)+'</div>'
      +'<div class="track">'+segs+'</div>'
      +'<div class="bv kpi">'+eur2(d.gap)+tip('Uncaptured service value, '+esc(r.db),
        'expected service demand minus quantity bought (genuine or Competitive), valued at the observed average selling price per service family',
        'pms_capture_by_db_year.csv, modelled; fleet '+num(r.uio)+' vehicles in service, '+esc(r.wc)
          + (ST.period==='fy'?'. Fiscal leg derived from the fiscal-to-calendar ratio of service-part billing lines, per distributor and per family':'')
          + (r.db==='IUK'?'. IUK expects '+num(d.exp)+' service-part units against '+num(d.act)+' bought at the flat 20,000 km/yr model distance; the measured distance is 14,494 km/yr':'')
          + (r.db==='IRELAND'?'. Ireland exceeds 100% of modelled expected demand, which is unresolved, not a strength':''),
        'Service families with no agreed interval are outside the model, so this layer is narrower than the parts catalogue. The ceiling itself is modelled, not observed lost orders. Under fiscal the expected-demand ceiling is unchanged because the model has no period dimension.')
      +'</div></div>';
  });
  g('c1-rows').innerHTML=out;
}
function chart2(){
  var rows=DATA.dbs.filter(function(r){ return repOf(r)&&repOf(r).total>0; })
    .sort(function(a,b){ return repOf(b).total-repOf(a).total; });
  if(!rows.length){ g('c2-rows').innerHTML='<p class="small">No distributor-level replenishment evidence under these settings.</p>'; return; }
  var mx=0; rows.forEach(function(r){ mx=Math.max(mx,repOf(r).pull||0,repOf(r).over_low||0,repOf(r).over_none||0); });
  var t=''; for(var i=0;i<=4;i++){ t+='<span>'+eur2(mx*i/4)+'</span>'; } g('c2-axis').innerHTML=t;
  var grid=''; for(var i=0;i<=4;i++){ grid+='<i style="left:'+(i*25)+'%"></i>'; }
  var out='<div class="grid">'+grid+'</div>';
  rows.forEach(function(r){
    var rp=repOf(r), over=(rp.over_low||0)+(rp.over_none||0);
    out+='<div class="brow"><div class="bl">'+esc(r.db)+'</div>'
      +'<div><div class="track plain" title=""><span style="width:'+((rp.pull||0)/mx*100)+'%;background:#2b4a78"></span></div>'
      +'<div class="track plain" style="margin-top:3px"><span style="width:'+(over/mx*100)+'%;background:#c0552d"></span></div></div>'
      +'<div class="bv kpi">'+eur2(rp.total)+tip('Replenishment exceptions, '+esc(r.db),
        'value of exception part numbers billed to the distributor that did not show up proportionally in sales to its dealers, at billed value',
        'replenishment_exceptions_cy2025.csv (calendar 2025) and replenishment_bridge.parquet for fiscal; ranking capped at the top 100 part numbers per signal',
        'Thirteen of eighteen distributors have no sales-to-dealer file and cannot be measured. Under-ordering and overstock are different problems and are not added into one instruction.')
      +'</div></div>';
  });
  g('c2-rows').innerHTML=out;
}
function chart3(){
  var rows=DATA.dbs.filter(function(r){ return mixOf(r)!==null&&r.expo; })
    .sort(function(a,b){ return mixOf(b)-mixOf(a); });
  var mx=Math.max.apply(null,rows.map(function(r){ return mixOf(r); }));
  var t=''; for(var i=0;i<=4;i++){ t+='<span>'+(Math.round(mx*i/4*10)/10)+'%</span>'; } g('c3-axis').innerHTML=t;
  var grid=''; for(var i=0;i<=4;i++){ grid+='<i style="left:'+(i*25)+'%"></i>'; }
  var out='<div class="grid">'+grid+'</div>';
  rows.forEach(function(r){
    var sh=mixOf(r), ex=r.expo.pct;
    out+='<div class="brow"><div class="bl">'+esc(r.db)+'</div>'
      +'<div><div class="track plain"><span style="width:'+(sh/mx*100)+'%;background:#2b4a78"></span></div>'
      +'<div class="track plain" style="margin-top:3px"><span style="width:'+(ex/mx*100)+'%;background:#c0552d;min-width:2px"></span></div></div>'
      +'<div class="bv kpi">'+one(sh,'%')+tip('Competitive-parts share, '+esc(r.db),
        'Competitive-parts euro divided by total service-part euro (genuine plus Competitive), service families only',
        'mix_genuine_bvp_pms.csv, calendar 2025, snapshot '+DATA.meta.snapshot,
        'Part numbers where no alternative is listed, so this is not the whole parts book. Fiscal leg is a period recut. Exposed revenue is '+eur(r.expo.eur)+' of net sales, '+one(ex,'%')+'.')
      +'</div></div>';
  });
  g('c3-rows').innerHTML=out;
}
function chart4(){
  var top=NPLIST.slice(0,10), rest=NPLIST.slice(10);
  var mx=top[0].eur, rows=top.slice();
  var restv=0; rest.forEach(function(x){ restv+=x.eur; });
  if(restv>0) rows=rows.concat([{rank:0,pn:'Other '+(rest.length)+' part numbers',desc:'',eur:restv,lube:false,other:true}]);
  var t=''; for(var i=0;i<=4;i++){ t+='<span>'+eur2(mx*i/4)+'</span>'; } g('c4-axis').innerHTML=t;
  var grid=''; for(var i=0;i<=4;i++){ grid+='<i style="left:'+(i*25)+'%"></i>'; }
  var out='<div class="grid">'+grid+'</div>';
  rows.forEach(function(x){
    var lb=x.other?esc(x.pn):(esc(x.pn)+' <span class="small">'+esc((x.desc||'').slice(0,22))+'</span>');
    out+='<div class="brow"><div class="bl">'+lb+'</div>'
      +'<div class="track plain"><span style="width:'+(x.eur/mx*100)+'%;background:'+(x.lube?'#c0552d':'#2b4a78')+'"></span></div>'
      +'<div class="bv kpi">'+eur2(x.eur)+tip('No usable price, '+(x.other?'grouped remainder':esc(x.pn)),
        'billed value in CY2025 where the price file carries no usable price. '+(x.other?'Sum of '+rest.length+' part numbers below the top ten.':'Cause: '+esc(x.desc?x.desc:'')+'.'),
        'no_pr00_gap_cy2025_ranked.csv (price check 2026-08-11, value from sales_fact.parquet CY2025)',
        'Part numbers closed by the August 2026 SAP price pull return are not in this list. Billed value is not the same as lost margin.')
      +'</div></div>';
  });
  g('c4-rows').innerHTML=out;
}
function chart5(){
  var now=IUK_ADJ.gap_now, adj=IUK_ADJ.gap;
  var mx=Math.max(now,adj);
  var t=''; for(var i=0;i<=4;i++){ t+='<span>'+eur2(mx*i/4)+'</span>'; } g('c5-axis').innerHTML=t;
  var rows=[['Model distance '+num(IUK_ADJ.km_model)+' km/yr',now,'#2b4a78',
             'IUK, the model as it stands, '+num(IUK_ADJ.km_model)+' km/yr flat assumption'],
            ['Measured distance '+num(IUK_ADJ.km)+' km/yr',adj,'#c0552d',
             'IUK, re-baselined to the measured N35 Grafter distance']];
  var out='';
  rows.forEach(function(r){
    out+='<div class="brow"><div class="bl">'+esc(r[0])+'</div>'
      +'<div class="track plain"><span style="width:'+(r[1]/mx*100)+'%;background:'+r[2]+'"></span></div>'
      +'<div class="bv kpi">'+eur2(r[1])+tip(esc(r[3]),
        'expected demand scaled by measured distance divided by model distance ('+IUK_ADJ.scale.toFixed(3)+'), minus actual bought, at the observed average selling price per family',
        'n35 mileages all.xlsx, median of odometer deltas between readings over elapsed time, 18,277 intervals on 5,421 vehicles 2018-2026',
        'Derived from odometer deltas, not the workbook annual mileage column, which divides by a shrinking vehicle age. N35 Grafter only, so the correction is applied to IUK as a whole.')
      +'</div></div>';
  });
  g('c5-rows').innerHTML=out;
  g('c5-note').innerHTML='At '+num(IUK_ADJ.km_model)+' km/yr IUK captures '
    +one(IUK_ADJ.cap_now,'%')+' of expected demand. At the measured '+num(IUK_ADJ.km)+' km/yr it captures '
    +one(IUK_ADJ.cap,'%')+' and the gap falls from '+eur2(IUK_ADJ.gap_now)+' to '+eur2(IUK_ADJ.gap)
    +' \u2014 '+(IUK_ADJ.cut*100).toFixed(0)+'% of the headline was our own assumption. '
    +'Israel is the one market already corrected inside the model, at 51,680 km/yr.';
}
function chart6(){
  var rows=FAMNET.slice().sort(function(a,b){ return (b.gap||0)-(a.gap||0); });
  var mx=rows[0].gap;
  var t=''; for(var i=0;i<=4;i++){ t+='<span>'+eur2(mx*i/4)+'</span>'; } g('c6-axis').innerHTML=t;
  var grid=''; for(var i=0;i<=4;i++){ grid+='<i style="left:'+(i*25)+'%"></i>'; }
  var out='<div class="grid">'+grid+'</div>';
  rows.forEach(function(f){
    out+='<div class="brow"><div class="bl">'+esc(f.label)+'</div>'
      +'<div class="track plain"><span style="width:'+(f.gap/mx*100)+'%;background:'+(GROUPC[f.group]||'#8b8578')+'"></span></div>'
      +'<div class="bv kpi">'+eur2(f.gap)+tip('Uncaptured value, '+esc(f.label),
        'expected demand minus bought, at the observed average selling price for this family',
        'pms_capture_by_db_year.csv, 18 distributors, calendar 2025; snapshot '+DATA.meta.snapshot,
        'This family bought '+one(f.cap,'%')+' of expected demand ('+num(f.act)+' of '+num(f.exp)+' units \u2014 units shown only because the family is named). Modelled, not observed lost orders.')
      +'</div></div>';
  });
  g('c6-rows').innerHTML=out;
}

// ---------- league table ----------
function renderLeague(){
  var tb=g('league-tbody'), out='';
  var mx=0;
  DATA.dbs.forEach(function(x){ var v=gapOf(x); if(v!==null&&v>mx) mx=v; });
  DATA.dbs.forEach(function(r){
    var gv=gapOf(r), nb=unboughtOf(r), bv=billOf(r);
    var pct=(gv!==null&&mx)?Math.min(100,gv/mx*100):0;
    var chips='';
    if(nb!==null&&nb<0) chips+='<span class="chip terra">above 100% \u2014 unresolved</span>';
    if(r.db==='IUK') chips+='<span class="chip">mileage-inflated</span>';
    if(!r.demand.cy) chips+='<span class="chip blue">no fleet model</span>';
    out+='<tr><td><b>'+esc(r.db)+'</b>'+chips+'</td>';
    if(gv===null){
      out+='<td class="null">'+esc(gapReason(r))+'</td><td class="null">'+esc(gapReason(r))+'</td>';
    } else {
      out+='<td class="kpi">'+eur2(gv)+tip((ST.dir==='db'?'Uncaptured service value, ':'Uncaptured service value at the dealer, ')+esc(r.db),
        ST.dir==='db'
          ? 'expected service demand minus quantity the distributor bought from ISZE, valued at the observed average selling price per service family'
          : 'expected service demand minus quantity the distributor sold on to its dealers, valued at the observed average selling price per service family',
        (ST.dir==='db' ? 'pms_capture_by_db_year.csv, modelled' : 'monthly sales-to-dealer file for this distributor')
          + ', fleet '+num(r.uio)+' vehicles in service'
          + (ST.dir==='dealer'&&r.dealer&&r.dealer[ST.period]&&r.dealer[ST.period].proj
             ? '; only '+r.dealer[ST.period].months+' of 12 fiscal months are on file, so the observed run-rate is scaled to twelve and the figure is derived' : ''),
        ST.dir==='db'
          ? 'Service families with no agreed service interval. A modelled ceiling, not observed lost orders. Fiscal leg is a derived recut.'
          : 'Excludes anything the dealer bought elsewhere. Only six of the twenty-two distributors have this file, so the twelve largest blank cells are structural, not zero.')
        +'</td>'
        +'<td class="kpi">'+one(nb,'%')+tip('Not bought, share of expected demand, '+esc(r.db),
          'one minus captured quantity divided by expected quantity',
          'same source as the value column',
          'A negative figure means more was bought than the model expected \u2014 an unresolved reading, not a strength. Ireland reads 102.7% in calendar 2025.')
        +'</td>';
    }
    out+='<td>'+num(r.uio)+'</td><td class="small" style="text-align:left">'+esc(r.wc)
      +(r.n75?('<br><span class="small">'+num(r.n75)+' truck class / '+num(r.lcv||0)+' light</span>'):'')
      +(r.imit?('<br><span class="small">measured '+num(r.imit)+' km/yr</span>'):'')
      +'</td>';
    var rp=repOf(r);
    out+='<td class="kpi">'+(rp?eur2(rp.total):'<span class="null">no sales-to-dealer file</span>')
      +(rp?tip('Replenishment exceptions, '+esc(r.db),
        'value of exception part numbers at billed value, capped at the top 100 part numbers per signal',
        ST.period==='cy'?'replenishment_exceptions_cy2025.csv':'replenishment_bridge.parquet, fiscal months Apr 2025 \u2013 Mar 2026',
        'Only five distributors have a sales-to-dealer file, and under fiscal only four. Not a network figure.'):'')
      +'</td>';
    var mv=mixOf(r);
    out+='<td class="kpi">'+(mv===null?'<span class="null">not measured</span>':one(mv,'%'))
      +(mv===null?'':tip('Competitive-parts share, '+esc(r.db),
        'Competitive-parts euro divided by total service-part euro, service families only',
        'mix_genuine_bvp_pms.csv, calendar 2025'+(ST.period==='fy'?' with a period recut from tagged billing':''),
        'Part numbers with no listed alternative, so this is not the whole parts book.'))
      +'</td>';
    out+='<td class="kpi">'+(r.expo?one(r.expo.pct,'%'):'\u2014')
      +(r.expo?tip('Direct aftermarket exposure, '+esc(r.db),
        'high-risk revenue divided by net sales',
        'aim_exposure_by_db_year.csv, calendar 2025; '+eur(r.expo.eur)+' of net sales',
        'Only part numbers with a matched alternative. A narrow slice, which is why it reads low everywhere.'):'')
      +'</td>';
    out+='<td class="kpi">'+(r.np&&r.np.eur?eur2(r.np.eur):'\u2014')
      +(r.np&&r.np.eur?tip('No usable price, '+esc(r.db),
        'CY2025 billed value of part numbers the price file cannot price',
        'no_pr00_gap_cy2025_ranked.csv with CY2025 value from sales_fact.parquet',
        'Calendar 2025 only \u2014 this file carries no period tag, so it does not move with the period control.'):'')
      +'</td>';
    out+='<td class="kpi">'+(bv===null?'<span class="null">'+esc(billNote(r))+'</span>':eur2(bv))
      +(bv===null?'':tip((ST.dir==='db'?'Billed to ':'Sales to dealer from ')+esc(r.db),
        ST.dir==='db'
          ? 'net parts sales to this distributor, less warranty parts where warranty is excluded'
          : 'value the distributor invoiced on to its dealers',
        ST.dir==='db' ? 'gps_spu_by_distributor.csv (calendar 2025) and sales_fact.parquet (fiscal window); warranty split from the same GPS file'
                      : 'dealer_sellout_gps_2025.csv, calendar 2025 only'
                      + (r.dealer&&r.dealer[ST.period]&&r.dealer[ST.period].proj?'; fiscal value derived at the distributor\u2019s own euro per unit':''),
        ST.warr==='exc'
          ? 'Warranty parts, which are '+(r.bill.warr?eur(r.bill.warr):'n/a')+' at this distributor. Credit notes are already netted out.'
          : 'Nothing excluded. Credit notes are already netted out.'))
      +'</td></tr>';
  });
  tb.innerHTML=out;
  var nwd={gap:0,exp:0,act:0,bill:0,bill_n:0,rep:0,rep_dbs:0,mix_max:null,gv_max:0};
  DATA.dbs.forEach(function(r){
    var v=gapOf(r);
    if(v!==null){ nwd.gap+=v; nwd.exp+=(demand(r)?demand(r).exp:0); nwd.act+=(demand(r)?demand(r).act:0); }
    var b=billOf(r); if(b!==null){ nwd.bill+=b; nwd.bill_n++; }
    var rp=repOf(r); if(rp){ nwd.rep+=rp.total; nwd.rep_dbs++; }
    var mv=mixOf(r); if(mv!==null&&(nwd.mix_max===null||mv>nwd.mix_max)) nwd.mix_max=mv;
    if(r.expo&&r.expo.pct>nwd.gv_max) nwd.gv_max=r.expo.pct;
  });
  var nbn=(ST.dir==='db'&&nwd.exp>0)?one((nwd.exp-nwd.act)/nwd.exp*100,'%'):'\u2014';
  var f='<tr class="tot"><td>Network \u00b7 '+DATA.dbs.length+' distributors</td>'
    +'<td>'+(nwd.gap?eur2(nwd.gap):'\u2014')+'</td><td>'+nbn+'</td>'
    +'<td>'+num(DATA.nw.uio)+'</td><td class="small" style="text-align:left">light and truck class, mixed</td>'
    +'<td>'+(nwd.rep?eur2(nwd.rep)+' <span class="small">('+nwd.rep_dbs+' DBs)</span>':'\u2014')+'</td>'
    +'<td>'+(nwd.mix_max===null?'\u2014':'max '+one(nwd.mix_max,'%'))+'</td>'
    +'<td>'+one(nwd.gv_max,'%')+' max</td>'
    +'<td>'+eur2(DATA.nw.np)+'</td><td>'+(nwd.bill?eur2(nwd.bill):'\u2014')+'</td></tr>';
  g('league-foot').innerHTML=f;
  g('lg-demand').textContent = ST.dir==='db'?'Uncaptured service value':'Uncaptured value at the dealer';
  g('lg-bill').textContent = ST.dir==='db'?'Billed to distributor':'Sales to dealer';
}

// ---------- availability + hero ----------
function renderAvail(){
  var items=[];
  if(ST.dir==='dealer'){
    items.push('<b>Sixteen of the twenty-two distributors have no sales-to-dealer file</b>, so their value columns are blank with the reason, never a zero and never a copy of the other direction. Six have one: IUK, UTI, ITUK, Ireland, Greece and Portugal.');
    var proj=[];
    DATA.dbs.forEach(function(r){ var t=r.dealer&&r.dealer[ST.period];
      if(t&&t.proj) proj.push(r.db+' ('+t.months+' of 11 fiscal months on file)'); });
    if(ST.period==='fy'&&proj.length) items.push('<b>Two dealer files do not cover the fiscal window:</b> '+proj.join(' and ')+'. Their value is the observed run-rate scaled to the window, marked derived, not counted. Greece is absent altogether under fiscal because its file starts in August 2025.');
  }
  if(ST.period==='fy'){
    items.push('<b>Fiscal 2025 is April 2025 to March 2026. No source covers 2026-03</b>, so a complete fiscal window is the eleven months April 2025 to February 2026. March 2026 is in neither the calendar nor the fiscal cut on this page.');
    items.push('<b>The demand gap under fiscal is a derived recut.</b> The demand-capture file on disk carries calendar years only, so the fiscal-to-calendar ratio of service-part billing lines, per distributor and per family, is applied to the published calendar actuals. The expected-demand model has no period dimension, so the ceiling is the same annual figure in both periods &mdash; only the bought quantity moves.');
    items.push('<b>The no-usable-price column stays on calendar 2025</b> under fiscal, because that file carries no period tag.');
    items.push('<b>Greece has no replenishment figure under fiscal</b>, and UTI\'s fiscal replenishment covers ten of the eleven months. Greece is excluded rather than annualised; UTI is shown because it is ten of eleven.');
  }
  if(ST.warr==='exc') items.push('<b>Warranty is priced out of the billing column</b> ('+eur2(DATA.nw.warr)+' network-wide, '+one(DATA.nw.warr_pct,'%')+' of parts billed in CY2025). The four CIS markets \u2014 Ukraine, Armenia, Kazakhstan and Palestine \u2014 have no warranty data and show <i>unavailable, not zero</i>. Other figures do not move with this control: the demand gap covers parts that were never bought, so warranty claims against parts that were bought cannot be netted out of it. The warranty claim extract matches the service-family registry on only seven part numbers, which is why.');
  var el=g('avail');
  if(!items.length){ el.className=''; el.innerHTML=''; return; }
  el.className='show';
  el.innerHTML='<b>What these settings cannot show.</b><ul><li>'+items.join('</li><li>')+'</li></ul>';
}
function renderHero(){
  var billed=0, n=0, nwarr=0;
  DATA.dbs.forEach(function(r){ var b=billOf(r); if(b!==null){ billed+=b; n++; } else if(ST.warr==='exc') nwarr++; });
  g('hero-billed').textContent = eur2(billed);
  g('hero-billed').nextElementSibling.textContent = ST.dir==='dealer'
    ? 'sales to dealer, '+DATA.nw.dealer_dbs+' distributors'
    : 'parts billed, '+(ST.warr==='inc'?'warranty included':'warranty excluded')+', '+n+' of '+DATA.dbs.length+' distributors';
  var gv=0, fc=capOf(DATA.dbs[0]);
  DATA.dbs.forEach(function(r){ var v=gapOf(r); if(v!==null) gv+=v; });
  if(ST.dir==='dealer'){ g('hero-nb').textContent=eur2(gv);
    g('hero-nb').nextElementSibling.textContent='uncaptured service value at the dealer'; }
  else { g('hero-nb').textContent=(ST.period==='fy'?eur2(gv):one(DATA.nw.nb,'%'));
    g('hero-nb').nextElementSibling.textContent=(ST.period==='fy'
      ? 'uncaptured service value, fiscal 2025 (derived recut)'
      : 'of expected service demand never bought'); }
  var cap=0, cn=0;
  DATA.dbs.forEach(function(r){ var c=capOf(r); if(c!==null){ cap+=c; cn++; } });
  $('hero-cap').textContent = cn ? one(cap/cn,'%') : '\u2014';
  $('hero-cap').nextElementSibling.textContent = ST.dir==='dealer'
    ? 'average capture reached dealers'+ (cn<22?' \u2014 '+cn+' of '+DATA.dbs.length+' distributors')
    : 'average capture of expected demand'+ (cn<22?' \u2014 '+cn+' of '+DATA.dbs.length+' distributors');
  var rp=0, dn=0; DATA.dbs.forEach(function(r){ var x=repOf(r); if(x){ rp+=x.total; dn++; } });
  g('hero-rep').textContent = eur2(rp);
  g('hero-rep').nextElementSibling.textContent = dn?('stock sitting with '+dn+' distributors'):'no replenishment evidence under these settings';
}
function renderAll(){ renderAvail(); renderHero(); renderLeague(); chart1(); chart2(); chart3(); chart4(); chart5(); chart6(); }
document.querySelectorAll('.tgl button').forEach(function(b){
  b.addEventListener('click', function(){
    var t=b.getAttribute('data-t'), v=b.getAttribute('data-v');
    document.querySelectorAll('.tgl button[data-t="'+t+'"]').forEach(function(o){ o.classList.remove('on'); o.setAttribute('aria-pressed','false'); });
    b.classList.add('on'); b.setAttribute('aria-pressed','true');
    ST[t]=v; renderAll();
  });
});
document.querySelectorAll('.tgl button').forEach(function(b){ b.setAttribute('aria-pressed', b.classList.contains('on')?'true':'false'); });
renderAll();
