
window.addEventListener('error',function(e){
  var b=document.getElementById('jserr');
  if(!b) return;
  b.style.display='block';
  b.innerHTML='<div class="note red"><b>The page did not finish drawing.</b> A script error stopped '
    +'it, so some panels below are empty. This is a defect in the page, not a data problem. Detail: '
    +String(e.message)+' at line '+String(e.lineno)+'.</div>';
});
(function(){
"use strict";
try{
var D = JSON.parse(document.getElementById('pmfd-data').textContent);
var NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee', MUTED='#6b6257', RULE='#d8d2c6',
    AMBER='#b7791f', GREEN='#2f6b45', PALE='#eef3f9', SLATE='#7a8ba6', GREY='#b9ae9d';
var FAMCOL={}; D.families.forEach(function(f){FAMCOL[f.key]=f.color;});
var FAMLAB={}; D.families.forEach(function(f){FAMLAB[f.key]=f.label;});
var FAMNOTE={}; D.families.forEach(function(f){FAMNOTE[f.key]=f.note;});
var CATLAB={}; D.cats.forEach(function(c){CATLAB[c.key]=c.label;});
var ZONE={}, ZK=D.zoneIds.slice();
D.zones.forEach(function(z){ZONE[z.zid]=z;});
var ZLAB={}, ZCOL={}, ZSHORT={};
D.zones.forEach(function(z){ZLAB[z.zid]=z.label;ZCOL[z.zid]=z.color;ZSHORT[z.zid]=z.short;});
var EXCL=D.zones.filter(function(z){return z.membership!=='also_fits_band';}).map(function(z){return z.zid;});
var BANDS=D.bandOrder.slice();
var BANDCOL=D.bandColor, BANDLAB=D.bandLabel;
var BAND_ZONE_SINGLE={'3.5t_N35':'n35_single','5.5t_N50_N55':'n55_single','7.5t_N50_N62_N75':'n75_single'};
var BAND_ZONE_ALSO={'3.5t_N35':'n35_also','5.5t_N50_N55':'n55_also','7.5t_N50_N62_N75':'n75_also'};

/* ── formatting ──────────────────────────────────────────────────────────────────────────── */
function eur(v){ if(v===null||v===undefined) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+Math.round(Math.abs(v)).toLocaleString('en-GB'); }
function eurm(v){ if(v===null||v===undefined) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+(Math.abs(v)/1e6).toFixed(2)+'M'; }
function num(v){ return (v===null||v===undefined)?'n/a':Math.round(v).toLocaleString('en-GB'); }
function fmtK(v){ if(v===null||v===undefined) return 'n/a';
  return Math.abs(v)>=10000 ? (v/1000).toFixed(1)+'k' : num(v); }
function pct(v,d){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  return (100*v).toFixed(d===undefined?1:d)+'%'; }
function signpct(v,d){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  return (v>=0?'+':'')+(100*v).toFixed(d===undefined?1:d)+'%'; }
function cls(v){ if(v===null||v===undefined||!isFinite(v)) return 'flat';
  return v>0.0005?'up':(v<-0.0005?'down':'flat'); }
function eurCell(v){ return v===null||v===undefined?'n/a':eur(v); }

/* tooltip, driven by data-tip so every derived number can explain itself */
var tip=document.getElementById('tip');
document.addEventListener('mouseover',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(!t) return; tip.innerHTML=t.getAttribute('data-tip'); tip.style.opacity='1';});
document.addEventListener('mousemove',function(e){
  if(tip.style.opacity!=='1') return;
  var x=e.clientX+14, y=e.clientY+14;
  if(x+350>window.innerWidth) x=e.clientX-360;
  if(y+130>window.innerHeight) y=e.clientY-140;
  tip.style.left=x+'px'; tip.style.top=y+'px';});
document.addEventListener('mouseout',function(e){
  var t=e.target.closest?e.target.closest('[data-tip]'):null;
  if(t) tip.style.opacity='0';});

Chart.defaults.font.family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif";
Chart.defaults.font.size=12;
Chart.defaults.color='#4a443b';
/* Animation off: the page redraws every chart whenever a control changes, and an animated redraw
   leaves the canvas momentarily empty. On a data page that reads as a blank chart. */
Chart.defaults.animation=false;
Chart.defaults.animations=false;
Chart.defaults.resizeDelay=0;
var charts={};
function mk(id,cfg){ var el=document.getElementById(id); if(!el) return;
  if(charts[id]) charts[id].destroy();
  charts[id]=new Chart(el,cfg); }

/* ── state ───────────────────────────────────────────────────────────────────────────────── */
var selCust={}, selFam='all', clock='CY', drillCat=null, drillBand=null;
selCust[D.markets.indexOf('IUK')>=0?'IUK':D.markets[0]]=true;
/* The measure in force. This is the pricing page's own pattern: one switch that every chart and
   every table reads through, so a reader never has to ask whether a bar is euro, units or a rate.
   `pv` is euro per vehicle in service and is the whole point of the page: absolute euro against a
   fleet that moves is not a like-for-like comparison, and a flat euro line on a growing fleet is a
   decline. */
var METRICS=[
  {key:'abs',  label:'Billed euro',        short:'euro',   unit:'EUR'},
  {key:'pv',   label:'Euro per vehicle',   short:'EUR/veh',unit:'EUR per vehicle in service'},
  {key:'units',label:'Units',              short:'pcs',    unit:'pieces'}];
var metric='abs';
/* Which fleet the per-vehicle rate divides by. `yearly` is the workbook's own count for the
   period, read per vehicle type, and it is the default because a single 2025 estimate used for
   every period cannot change a percentage: dividing three years of billing by one year's fleet is
   arithmetically the same as dividing by 1. `split` is that one 2025 estimate, kept as an option so
   the difference is visible rather than hidden. Both are always shown where a rate is quoted. */
var fleetMode='yearly';
function fleetChoiceLabel(k){
  if(k==='split') return 'one 2025 estimate, used for every period';
  if(k==='yearly') return 'that period\u2019s own fleet, by vehicle type';
  return 'the two side by side';
}
function fleetModeLabel(){ return fleetChoiceLabel(fleetMode); }
/* the other denominator, so the pair can be printed wherever a rate is */
function altMode(){ return fleetMode==='split' ? 'yearly' : 'split'; }
function measure(){ for(var i=0;i<METRICS.length;i++){ if(METRICS[i].key===metric) return METRICS[i]; }
  return METRICS[0]; }
/* The vehicle type in force is whatever the vehicle-type control says. Clicking a bar in the top
   chart sets the control, so the filter and the drill always agree rather than being two things
   that can disagree. */
function famFilter(){ return selFam==='all' ? null : selFam; }

var custSel=document.getElementById('selCust'), famSel=document.getElementById('selFam'),
    clkSel=document.getElementById('selClock');
var fleetSel=document.getElementById('selFleet');
var segMetric=document.getElementById('segMetric');

D.markets.forEach(function(m){
  var o=document.createElement('option'); o.value=m; o.textContent=m; custSel.appendChild(o);});
['all'].concat(D.families.map(function(f){return f.key;})).forEach(function(k){
  var o=document.createElement('option'); o.value=k;
  o.textContent = k==='all' ? 'All vehicle types' : FAMLAB[k];
  famSel.appendChild(o);});
Object.keys(D.clocks).forEach(function(c){
  var o=document.createElement('option'); o.value=c; o.textContent=D.clocks[c].label;
  clkSel.appendChild(o);});
[['yearly','That period\u2019s own fleet \u2014 the workbook\u2019s count for that period'],
 ['split','One 2025 estimate \u2014 the model\u2019s own split, used for every period']].forEach(function(x){
  var o=document.createElement('option'); o.value=x[0]; o.textContent=x[1]; fleetSel.appendChild(o);});

function chosen(){ return D.markets.filter(function(m){return selCust[m];}); }

/* ── aggregation over the selected customers ─────────────────────────────────────────────── */
/* rec: [marketIdx, catIdx, famIdx, period, eur, units]
   recPn: [pnIdx, marketIdx, period, eur, units]                                        */
var FAMK=D.families.map(function(f){return f.key;});
function agg(){
  var per=D.clocks[clock], mk=chosen(), mset={};
  mk.forEach(function(m,i){ mset[D.markets.indexOf(m)]=true; });
  var byFam={}, byFamCat={}, byCat={};
  var rows=D.rec[clock];
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    if(!mset[r[0]]) continue;
    var fk=FAMK[r[2]], ck=D.cats[r[1]].key, p=r[3];
    var a=byFam[fk]||(byFam[fk]={});
    var b=a[p]||(a[p]={eur:0,units:0}); b.eur+=r[4]; b.units+=r[5];
    var k2=fk+'|'+ck; var c=byFamCat[k2]||(byFamCat[k2]={});
    var e=c[p]||(c[p]={eur:0,units:0}); e.eur+=r[4]; e.units+=r[5];
    var d3=byCat[ck]||(byCat[ck]={});
    var g=d3[p]||(d3[p]={eur:0,units:0}); g.eur+=r[4]; g.units+=r[5];
  }
  return {byFam:byFam, byFamCat:byFamCat, byCat:byCat, markets:mk, per:per, mset:mset};
}
function pnAgg(A){
  var out={};
  var rows=D.recPn[clock];
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    if(!A.mset[r[1]]) continue;
    var a=out[r[0]]||(out[r[0]]={});
    var b=a[r[2]]||(a[r[2]]={eur:0,units:0}); b.eur+=r[3]; b.units+=r[4];
  }
  return out;
}

/* ── the tonnage level inside the N-series ─────────────────────────────────────────────────
   recZ   : [marketIdx, zoneIdx, period, eur, units]
   recZcat: [marketIdx, zoneIdx, catIdx, period, eur, units]
   A part number that fits more than one band appears under each of those bands, so the band
   rows overlap. `sums` on the zone says whether its euro may be added to another zone's. */
function zoneAgg(A){
  var out={};
  var rows=D.recZ[clock];
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    if(!A.mset[r[0]]) continue;
    var a=out[r[1]]||(out[r[1]]={});
    var b=a[r[2]]||(a[r[2]]={eur:0,units:0}); b.eur+=r[3]; b.units+=r[4];
  }
  return out;
}
function zoneCatAgg(A){
  var out={};
  var rows=D.recZcat[clock];
  for(var i=0;i<rows.length;i++){
    var r=rows[i];
    if(!A.mset[r[0]]) continue;
    var a=out[r[1]]||(out[r[1]]={});
    var b=a[r[2]]||(a[r[2]]={});
    var c=b[r[3]]||(b[r[3]]={eur:0,units:0}); c.eur+=r[4]; c.units+=r[5];
  }
  return out;
}
/* the band rows the N-series section is built from, in a fixed order */
function zIndex(zid){ return D.zoneIds.indexOf(zid); }
function zRow(Z, zid, latest){
  var pr=pairFor(Z[zIndex(zid)]||{},latest);
  var z=ZONE[zid];
  return {zid:zid,label:z.label,short:z.short,note:z.note,color:z.color,
          membership:z.membership,band:z.band,
          sums:(z.membership!=='also_fits_band'),
          eur:pr?pr.eur:0, units:pr?pr.units:0,
          eurPrev:pr?pr.eurPrev:null, unitsPrev:pr?pr.unitsPrev:null,
          eurPct:pr?pr.eurPct:null, unitsPct:pr?pr.unitsPct:null,
          hasPrev:pr?pr.hasPrev:false};
}
/* The band euro as a reader asked for it: everything that fits the band, exclusive and shared
   together. Marked, because the shared part of it sits in more than one band. */
function bandTotal(Z, band, latest){
  var s=zRow(Z,BAND_ZONE_SINGLE[band],latest), a=zRow(Z,BAND_ZONE_ALSO[band],latest);
  var e=s.eur+a.eur, ep=(s.eurPrev||0)+(a.eurPrev||0);
  var u=s.units+a.units, up=(s.unitsPrev===null&&a.unitsPrev===null)?null:((s.unitsPrev||0)+(a.unitsPrev||0));
  return {band:band,label:BANDLAB[band],color:BANDCOL[band],
          eur:e, units:u,
          eurPrev:(s.hasPrev||a.hasPrev)?ep:null,
          unitsPrev:(s.hasPrev||a.hasPrev)?up:null,
          eurPct:ep>0?(e/ep-1):null,
          unitsPct:(up&&up>0)?(u/up-1):null,
          singleEur:s.eur, sharedEur:a.eur,
          singleEurPrev:s.eurPrev, sharedEurPrev:a.eurPrev,
          singleUnits:s.units, sharedUnits:a.units,
          singleUnitsPrev:s.unitsPrev, sharedUnitsPrev:a.unitsPrev,
          hasPrev:!!s.hasPrev||!!a.hasPrev};
}
function bandFleet(band){
  /* The fleet split that exists on disk is cv_std × the market's measured 3.5 t share, and the
     remainder. No source on disk separates the 5.5 t trucks from that remainder, so the 5.5 t
     band gets no fleet number rather than an invented one. */
  if(band==='3.5t_N35') return {n:fleetSum(0), label:'vehicles in service at 3.5 t'};
  if(band==='5.5t_N50_N55') return {n:null,
    label:'no fleet figure — no source splits the 5.5 t trucks out of the N-series parc'};
  return {n:fleetSum(1),
    label:'vehicles in service in the rest of the N-series fleet, which holds the 5.5 t trucks too'};
}
function fleetSum(i){
  var t=0;
  chosen().forEach(function(m){ t+=((D.nseries_fleet[m]||[0,0])[i]||0); });
  return Math.round(t);
}

/* ── the comparison pair: this period and the same period a year earlier ────────────────── */
function pairFor(obj,p){
  /* A financial year is named by its closing year, so the year before FY2026 is FY2025. Both are
     twelve-month periods starting in April, so they are like-for-like. */
  var prev=p-1;
  var cur=obj&&obj[p] ? obj[p] : null;
  var was=obj&&obj[prev] ? obj[prev] : null;
  if(!cur&&!was) return null;
  var ce=cur?cur.eur:0, we=was?was.eur:0, cu=cur?cur.units:0, wu=was?was.units:0;
  return {p:p, prev:prev, cur:cur, was:was, eur:ce, units:cu, eurPrev:was?we:null,
          unitsPrev:was?wu:null,
          eurPct:(was&&we>0)?(ce/we-1):null, unitsPct:(was&&wu>0)?(cu/wu-1):null,
          hasPrev:!!was};
}

/* ── the fleet denominator, read through the clock ──────────────────────────────────────────
   `fleetAt(level, period, mode)` is the ONE place a denominator is produced, so a euro-per-vehicle
   figure anywhere on the page divides by something the page can name and date.

   level is a family key, a zone id, or 'all'.
     `split`  = the model's own three-way split, one 2025 estimate for every period. It is the only
                source that names a vehicle type in its own right, and it is the only denominator a
                weight band can use.
     `yearly` = the workbook's own count for that period, summed from the four row types that carry
                a vehicle type (LD and MD are the N-series truck, F-Series the heavy truck, LCV the
                light vehicle). That count moves period to period, which is the whole point.
   Where a period has no count, the result is null with the gap named — never another year's
   figure substituted quietly. */
function altModeOf(mode){ return mode==='split' ? 'yearly' : 'split'; }
function fleetBasis(){
  var c=D.fleetClock;
  return {
    split:{key:'split', label:'one 2025 estimate, used for every period',
           vintage:c.modelSplit.vintage, perYear:false},
    yearly:{key:'yearly', label:'that period\u2019s own fleet, by vehicle type',
            vintage:'one count per period, '+D.perYear.years[0]+' to '+D.perYear.years[D.perYear.years.length-1],
            perYear:true},
  };
}
function fleetAt(level, p, mode){
  var mk=chosen(), c=D.fleetClock;
  var useYearly = (mode!=='split');
  if(useYearly){
    /* a weight band has no per-year count of its own: no source splits the 5.5 t trucks out of
       the N-series. The fallback is stated, never silent. */
    if(level!=='all' && D.namedFamilies.indexOf(level)<0){
      var r0=fleetAt(level,p,'split');
      return {n:r0.n, mode:'split', source:c.modelSplit.source, vintage:r0.vintage,
              note:'no per-period count names this weight band, so the 2025 split estimate is used'};
    }
    var yr=String(yearOfPeriod(p)), tot=0, any=false, rows=[];
    var series=(level==='all')?['LD','MD','F_SERIES','LCV']:FAMSERIES[level];
    mk.forEach(function(m){
      var src=(D.perYear.byMarket[m]||{});
      series.forEach(function(s){
        var v=(src[s]||{})[yr];
        if(v===undefined) return;
        tot+=v; any=true; rows.push({market:m,series:s,units:v});});
    });
    if(!any){
      return {n:null, mode:'yearly', cy:yr, source:D.perYear.source,
              vintage:'no vehicle-in-service count for '+yr,
              gap:true, gaps:gapRows(level,yr,mk),
              note:'no count exists for this period and vehicle type, so no rate is shown rather '
                  +'than a rate on another period\u2019s fleet'};
    }
    var qual=(yr<=D.perYear.actualThrough?'measured':(Number(yr)===D.perYear.estimateYear?'an estimate':'a forecast'));
    var bad=qualBadFleet(level,mk);
    return {n:tot, mode:'yearly', cy:yr, source:D.perYear.source, series:series, parts:rows,
            vintage:'the '+yr+' count for this vehicle type, '+qual,
            quality:qual, defect:bad,
            note:'counts the vehicles on the road in that period, so the denominator moves with '
                +'the fleet rather than staying flat'};
  }
  var ms=c.modelSplit.byMarket, tot2=0, any2=false;
  if(level==='all'){
    mk.forEach(function(m){ var r=ms[m]; if(r){ tot2+=r.total; any2=true; } });
  } else if(D.namedFamilies.indexOf(level)>=0){
    var fmap={n_series_truck:'n_series',heavy_truck:'heavy',light_vehicle:'light'};
    mk.forEach(function(m){ var r=ms[m]; if(r){ tot2+=r[fmap[level]]||0; any2=true; } });
  } else {
    return {n:null, mode:'split', source:c.modelSplit.source,
            note:'this line is pooled or names no vehicle, so no single fleet applies'};
  }
  return {n:any2?tot2:null, mode:'split', source:c.modelSplit.source,
          vintage:yearOfPeriod(p)+' billing divided by the fleet estimate labelled '
            +c.modelSplit.vintage+' \u2014 the same estimate in every period',
          note:'the same estimate is used for every period, so a move in the rate comes from the '
              +'billing, not the fleet'};
}
/* which row types carry each vehicle type in the workbook */
var FAMSERIES={n_series_truck:['LD','MD'], heavy_truck:['F_SERIES'], light_vehicle:['LCV']};
/* a financial year is named by the March it closes in, so ISZE 2024 spends the calendar-2023 fleet */
function yearOfPeriod(p){ return clock==='CY' ? p : p-1; }
/* markets in the selection that carry a fleet-quality defect for this vehicle type */
function qualBadFleet(level,mk){
  var out=[];
  if(level==='all'||level==='n_series_truck'){
    if(mk.indexOf('UTI')>=0) out.push('UTI');
  }
  return out;
}
/* the named gaps behind a missing denominator */
function gapRows(level,yr,mk){
  var out=[];
  mk.forEach(function(m){
    var src=D.perYear.byMarket[m]||{};
    var series=(level==='all')?['LD','MD','F_SERIES','LCV']:(FAMSERIES[level]||[]);
    var has=series.some(function(s){ return (src[s]||{})[yr]!==undefined; });
    if(!has) out.push(m);
  });
  return out;
}
/* ── the two answers side by side, in words ────────────────────────────────────────────────
   This pair is the point of the whole section: the same euros divided by a flat denominator and by
   the period's own fleet, so a reader can check the division rather than trust one of them. */
function numOr(v){ return (v===null||v===undefined||!isFinite(v))?'n/a':num(v); }
function rateOn(eurAmt,f){ return (f&&f.n&&f.n>0)?eur(eurAmt/f.n):'n/a'; }
function bothFleetLine(eurAmt,p,level){
  var y=fleetAt(level,p,'yearly'), s=fleetAt(level,p,'split');
  return 'that period\u2019s own fleet '+numOr(y.n)+' \u2192 '+rateOn(eurAmt,y)
    +' per vehicle; one 2025 estimate '+numOr(s.n)+' \u2192 '+rateOn(eurAmt,s)+' per vehicle';
}
function otherFleetLine(eurAmt,p,level){
  var m=altModeOf(fleetMode), f=fleetAt(level,p,m);
  return (f.n===null||!f.n) ? 'no '+fleetChoiceLabel(m)+' denominator exists for this line'
    : numOr(f.n)+' vehicles on '+fleetChoiceLabel(m)+' \u2192 '+rateOn(eurAmt,f)+' per vehicle';
}
function fleetDefectWords(list){
  var out=[];
  if(list&&list.indexOf('UTI')>=0)
    out.push('Israel\u2019s truck fleet is about 25% low in every year against the Israeli '
      +'ministry\u2019s own registrations, so the euro-per-truck figure there is flattered');
  return out.join('; ');
}
/* the fleet for one family in the period being read, on whichever denominator is in force */
function familyFleet(key){ if(!key) return 0;
  var r=fleetAt(key, D.clocks[clock].latestComplete, fleetMode); return r.n||0; }
/* both denominators for one family, so a family table can print the pair rather than one answer */
function familyFleetBoth(key,p){
  if(!key||D.namedFamilies.indexOf(key)<0) return {y:null, s:null};
  return {y:fleetAt(key,p,'yearly').n, s:fleetAt(key,p,'split').n}; }

/* the measure itself: euro, units, or euro per vehicle in service */
function measureOf(eur, units, fleet){
  if(metric==='units') return units||0;
  if(metric==='pv') return (fleet&&fleet>0)?(eur/fleet):null;
  return eur;
}
function fmtM(v,dec){
  if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  if(metric==='units') return num(v)+' pcs';
  if(metric==='pv') return eur(v);
  return eur(v);
}
function fmtMSigned(v,dec){
  if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  if(metric==='units') return (v>=0?'+':'')+num(v)+' pcs';
  return (v>=0?'+':'')+eur(v);
}
/* what a measure percentage means, in words — a rate can move for a reason a euro cannot */
function metricMoveNote(){
  if(metric==='units') return 'Units are pieces. A piece count on its own says little: read it '
    +'beside the euro and the fleet, because an engine and a bolt are both one piece.';
  if(metric==='pv') return 'Euro per vehicle in service is the comparable rate: it divides the same '
    +'billing by the vehicles the parts were sold for, so a fleet that grew no longer flatters a '
    +'flat euro line. A rate can still move because the fleet moved rather than because the billing '
    +'did, and the fleet column below is there to show which.';
  return 'Billed euro is the absolute figure. It is not a like-for-like comparison on its own: the '
    +'vehicles in service move every year, so read it with the euro-per-vehicle rate beside it.';
}
function syncedTip(base){
  return base+'<br><br><b>Read in '+measure().label.toLowerCase()+'</b> because that is the measure '
    +'selected above. '+metricMoveNote();
}

/* the same comparison pair, resolved into the measure in force, with the fleet beside it */
function pairM(obj, p, level){
  var pr=pairFor(obj,p);
  if(!pr) return null;
  var fNow=fleetAt(level,p,fleetMode), fWas=fleetAt(level,pr.prev,fleetMode);
  var mNow=measureOf(pr.eur, pr.units, fNow.n);
  var mWas=(pr.eurPrev===null&&pr.unitsPrev===null)?null
           :measureOf(pr.eurPrev||0, pr.unitsPrev||0, fWas.n);
  return {p:p, prev:pr.prev, eur:pr.eur, units:pr.units, eurPrev:pr.eurPrev,
          unitsPrev:pr.unitsPrev, eurPct:pr.eurPct, unitsPct:pr.unitsPct, hasPrev:pr.hasPrev,
          fleet:fNow, fleetPrev:fWas, m:mNow, mPrev:mWas,
          mPct:(mWas&&mWas>0&&mNow!==null)?(mNow/mWas-1):null,
          mDelta:(mWas===null||mNow===null)?null:(mNow-mWas)};
}
function pairSnapshot(pr){
  var out=(pr&&pr.m!==null&&pr.m!==undefined)?fmtM(pr.m):'n/a';
  return out;
}

/* ── render ─────────────────────────────────────────────────────────────────────────────── */
function render(){
  var A=agg(), C=D.clocks[clock];
  var latest=C.latestComplete;
  clkSel.value=clock; famSel.value=selFam;
  if(fleetSel) fleetSel.value=fleetMode;
  /* the segmented control reflects the live measure, and every derived figure on the page reads
     it, so the switch cannot be a label that lies */
  if(segMetric){
    Array.prototype.slice.call(segMetric.querySelectorAll('button')).forEach(function(b){
      if(b.getAttribute('data-m')===metric) b.classList.add('on'); else b.classList.remove('on'); });
  }
  if(document.getElementById('metricNote')){
    document.getElementById('metricNote').innerHTML=metricMoveNote();
  }
  /* the denominator, named where the reader chooses it, from the live state */
  var fn=document.getElementById('fleetNote');
  if(fn){
    var fl0=fleetAt('all',latest,fleetMode), flS=fleetAt('all',latest,'split'), flY=fleetAt('all',latest,'yearly');
    fn.innerHTML='In force: <b>'+fleetModeLabel()+'</b>. '
      +'Vehicles in service for this selection: <b>'+(fl0.n===null?'n/a':num(fl0.n))+'</b>'
      +((flS.n!==null&&flY.n!==null)
        ? ', against '+num(flS.n)+' on the single 2025 estimate and '+num(flY.n)
          +' on the '+flY.cy+' count this period'
          +(Math.abs(flS.n-flY.n)<0.5&&Number(flY.cy)===D.perYear.estimateYear
            ? ' \u2014 they coincide here only because '+D.perYear.estimateYear+' is the estimate '
              +'year itself, so a single period proves nothing about the difference between them; '
              +'read the table below across all three periods'
            : '')
        : '')
      +'. '+(fl0.vintage||'')+'.';
    if(D.perYear.gaps.length){
      fn.innerHTML+=' <b>Named gap:</b> '+D.perYear.gaps.length+' market-period'
        +(D.perYear.gaps.length===1?'':'s')+' inside the range carry no count and are shown as a '
        +'gap rather than filled with another period\u2019s figure.';
    }
  }
  /* a band filter only makes sense inside the N-series; leaving that vehicle type clears it */
  if(selFam!=='n_series_truck' && drillBand){ drillBand=null; }

  /* chips */
  document.getElementById('chips').innerHTML =
    (A.markets.length===D.markets.length
      ? '<span class="chip all"><b>All '+D.markets.length+' markets</b></span>'
      : A.markets.map(function(m){return '<span class="chip">'+m+'</span>';}).join(''))
    + (A.markets.length>1 ? '<span class="chip">'+A.markets.length+' selected, summed</span>' : '');
  document.getElementById('clockNote').innerHTML =
    C.spelled[String(latest)] + '. ' + C.note;

  /* lane notice — the two interval schedules are never averaged */
  var lanes={};
  A.markets.forEach(function(m){ var l=D.lane[m]||'internal'; lanes[l]=(lanes[l]||0)+1; });
  var laneBits=Object.keys(lanes).map(function(l){
    return '<b>'+lanes[l]+'</b> on the '+(l==='agreed'
      ? 'schedule agreed for that market'
      : 'internal service schedule')+'';});
  document.getElementById('laneNotice').innerHTML =
    '<div class="note"><b>Two service-interval schedules run through this network and they are '
    +'never averaged or added together</b>, because they answer different questions about the same '
    +'fleet. In your selection: '+laneBits.join(', ')+'.'
    +(A.markets.indexOf('ITUK')>=0
      ? ' ITUK runs the schedule agreed with that distributor: filters 1.25 visits a year, clutch '
        +'and brake 0.5, on a 22,389-vehicle fleet.'
      : '')
    +'</div>';

  /* ── family rows (level 1) */
  var famRows=D.families.map(function(f){
    var pr=pairM(A.byFam[f.key]||{},latest,f.key);
    return {key:f.key,label:f.label,note:f.note,color:f.color,
            eur:pr?pr.eur:0, units:pr?pr.units:0,
            eurPrev:pr?pr.eurPrev:null, unitsPrev:pr?pr.unitsPrev:null,
            eurPct:pr?pr.eurPct:null, unitsPct:pr?pr.unitsPct:null,
            hasPrev:pr?pr.hasPrev:false,
            fleet:pr?pr.fleet:null, fleetPrev:pr?pr.fleetPrev:null,
            m:pr?pr.m:null, mPrev:pr?pr.mPrev:null, mPct:pr?pr.mPct:null};
  });
  var famSelRows = selFam==='all' ? famRows : famRows.filter(function(r){return r.key===selFam;});
  var head={eur:0,units:0,eurPrev:0,unitsPrev:0};
  famRows.forEach(function(r){ head.eur+=r.eur; head.units+=r.units;
    head.eurPrev+=(r.eurPrev||0); head.unitsPrev+=(r.unitsPrev||0); });
  var named=famRows.filter(function(r){return D.namedFamilies.indexOf(r.key)>=0;});
  var namedEur=named.reduce(function(s,r){return s+r.eur;},0);
  var namedPrev=named.reduce(function(s,r){return s+(r.eurPrev||0);},0);
  var fleetTot=0; A.markets.forEach(function(m){ fleetTot+=(D.fleet[m]||{total:0}).total; });
  /* the whole selection in the measure in force — the euro total divided by the total fleet, so
     the headline tile cannot say "euro" while the switch says "per vehicle" */
  var headFleet=fleetAt('all',latest,fleetMode);
  var headM=measureOf(head.eur,head.units,headFleet.n);
  var headMFleet=headFleet;
  var headMPrev=null;
  if(head.eurPrev!==null){
    var fWasHead=fleetAt('all',latest-1,fleetMode);
    headMPrev=measureOf(head.eurPrev,head.unitsPrev,fWasHead.n);
  }
  var headMPct=(headMPrev&&headMPrev>0&&headM!==null)?(headM/headMPrev-1):null;

  /* ── KPIs */
  var k=[];
  var mLabel=measure().label.toLowerCase();
  k.push({v:(headM===null?'n/a':fmtM(headM)), l:mLabel+', '+C.spelled[String(latest)],
    s:(headMPct!==null?signpct(headMPct)+' against '+C.spelled[String(latest-1)]:''),
    cls:cls(headMPct),
    tip:syncedTip('Every part number that carries a service family, summed over <b>'
      +(A.markets.length===D.markets.length?'all 18 markets':A.markets.join(', '))+'</b>.<br>'
      +C.spelled[String(latest)]+': '+eur(head.eur)+' on '+num(head.units)+' units<br>'
      +C.spelled[String(latest-1)]+': '+eur(head.eurPrev)+' on '+num(head.unitsPrev)+' units<br>'
      +'Fleet: '+(headFleet.n===null?'n/a':num(headFleet.n))+' vehicles in service this period'
      +(headFleet.detail?' ('+headFleet.detail+')':'')+'<br>'
      +'<b>Both denominators, so the pair can be checked:</b> '
      +bothFleetLine(head.eur,latest,'all',head.units)
      +'<br>Sales are sales: business partner or own-brand, it counts here. Parts that fit more '
      +'than one vehicle type are inside this total and are also shown pooled, never split.')});
  k.push({v:num(head.units)+' pcs', l:'units billed, '+C.spelled[String(latest)],
    s:(head.unitsPrev?signpct((head.units/(head.unitsPrev||1))-1)+' against the year before':''),
    cls:cls(head.unitsPrev?(head.units/(head.unitsPrev||1))-1:null),
    tip:'Pieces billed on those same part numbers. A piece count on its own says little — read it '
      +'beside the euro and the fleet, because an engine and a bolt are both one piece.'});
  k.push({v:(headFleet.n===null?'n/a':num(headFleet.n)),
    l:'vehicles in service, the denominator in force',
    cls:(headFleet.n===null?'bad':''),
    s:(headFleet.quality?('a '+headFleet.quality+' figure'):''),
    tip:'<b>'+fleetModeLabel()+'</b> is the denominator the euro-per-vehicle figures divide by.<br>'
      +'Fleet for the selection in this period: N-series '
      +num(fleetAt('n_series_truck',latest,fleetMode).n)
      +', heavy '+num(fleetAt('heavy_truck',latest,fleetMode).n)
      +', light '+num(fleetAt('light_vehicle',latest,fleetMode).n)
      +'.<br>'+(headFleet.vintage||'')+(headFleet.note?'. '+headFleet.note:'')
      +'<br>The other denominator reads: '
      +otherFleetLine(head.eur,latest,'all',head.units)
      +(headFleet.defect&&headFleet.defect.length
        ? '<br><b>Carry with care:</b> '+fleetDefectWords(headFleet.defect)+'.' : '')});
  k.push({v:num(fleetTot), l:'vehicles in service, the single 2025 estimate',
    tip:'The 2025E estimate, kept on the page as the second denominator so the two answers can be '
      +'compared rather than one of them hidden. Fleet for the selection: N-series '
      +num(A.markets.reduce(function(s,m){return s+(D.fleet[m]||{n_series:0}).n_series;},0))
      +', heavy '+num(A.markets.reduce(function(s,m){return s+(D.fleet[m]||{heavy:0}).heavy;},0))
      +', light '+num(A.markets.reduce(function(s,m){return s+(D.fleet[m]||{light:0}).light;},0))
      +'.<br>One column of one vintage, used for every period, so a rate built on it cannot move '
      +'unless the billing moves. That is now the option, not the default.'});
  k.push({v:pct(D.totals.placeable2025/D.totals.serviceBook2025,1),
    l:'of the 2025 service book now placed in a vehicle type',
    s:'46.6% before the fix — the rest was pooled or had no vehicle named',
    cls:'good',
    tip:'2025 service-part euro that resolves to exactly one vehicle type, against the published '
      +'service-part book of '+eur(D.totals.serviceBook2025)+'.<br>Before: '
      +eur(D.totals.placeable2025Old)+' ('+pct(D.totals.placeable2025OldPct/100,1)+').<br>'
      +'The remainder is not missing: it is pooled where a part fits more than one type, and has no '
      +'vehicle named where no source names one. Both are shown, never spread.'});
  var heavy=famRows.filter(function(r){return r.key==='heavy_truck';})[0];
  var B=D.before&&D.before.available?D.before:null;
  var heavyBefore=B&&B.eur.heavy_truck?B.eur.heavy_truck[String(latest)]:null;
  k.push({v:eurm(heavy?heavy.eur:0), l:'heavy truck billed, '+C.spelled[String(latest)]
      +', '+A.markets.length+(A.markets.length===1?' market':' markets'),
    s:(heavyBefore!==null&&heavyBefore!==undefined
        ? 'all 18 markets read '+eur(heavyBefore)+' on the shipped page; they read '
          +eur(((D.trend[clock].heavy_truck||{}).eur||{})[String(latest)]||0)+' now'
        : (heavy&&heavy.eurPrev?signpct((heavy.eur/(heavy.eurPrev||1))-1)+' against the year before':'')),
    cls:cls(heavy&&heavy.eurPrev?(heavy.eur/(heavy.eurPrev||1))-1:null),
    tip:'Parts that fit heavy truck and nothing else, for the customers you have selected. '
      +'This is the line the earlier family view suppressed: part numbers the parts cross-reference '
      +'already names as heavy-truck-only were dropped by one step because their family was known, '
      +'and dropped by the next because they were not in the vehicle decode. They appeared on '
      +'neither side.'
      +(heavyBefore!==null&&heavyBefore!==undefined
        ? ' The earlier page read '+eur(heavyBefore)+' for the 2025 network total.'
        : '')});
  document.getElementById('kpis').innerHTML=k.map(function(x){
    return '<div class="kpi '+(x.cls||'')+'" data-tip="'+x.tip+'"><div class="v">'+x.v
      +'</div><div class="l">'+x.l+'</div>'+(x.s?'<div class="s">'+x.s+'</div>':'')+'</div>';}).join('');

  /* ── chart 1: the funnel, this period against the same period a year earlier, in the measure
     the switch is set to. The axis, the formatter and the tooltip all read the same measure, so
     the chart cannot be labelled euro while it plots a rate. */
  var labels=famSelRows.map(function(r){return r.label;});
  var curM=famSelRows.map(function(r){return r.m;});
  var prevM=famSelRows.map(function(r){return r.mPrev;});
  function fmtAxis(v){
    if(metric==='units') return num(v);
    if(metric==='pv') return 'EUR '+Math.round(v);
    return eurm(v);
  }
  /* a per-vehicle rate is shown as a reference line rather than a bar there is no bar for */
  var funnelCfg={type:'bar',
    data:{labels:labels,datasets:[
      {label:C.spelled[String(latest)]+' \u2014 '+measure().label.toLowerCase(),
       data:curM,backgroundColor:famSelRows.map(function(r){return r.color;}),
       borderRadius:3},
      {label:C.spelled[String(latest-1)]+' \u2014 '+measure().label.toLowerCase(),
       data:prevM,backgroundColor:'#d9d3c7',borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{label:function(c){ return c.datasetIndex===0
            ? C.spelled[String(latest)]+': '+fmtM(c.raw)
            : C.spelled[String(latest-1)]+': '+fmtM(c.raw);},
          afterBody:function(items){
            var r=famSelRows[items[0].dataIndex];
            return [metric==='abs'?'in the measure above: '+fmtM(r.m):'billed '+eur(r.eur),
              metric==='units'?'billed '+eur(r.eur):num(r.units)+' units',
              r.eurPrev===null?'no billing a year earlier':
                (signpct(r.mPct)+' in '+measure().short+', '
                 +signpct(r.eurPct)+' in euro, '+signpct(r.unitsPct)+' in units'),
              'Fleet: '+(r.fleet&&r.fleet.n!==null
                ?num(r.fleet.n)+' vehicles in service on '+fleetModeLabel()
                :'no single fleet applies to this line')
              +(r.fleet&&r.fleet.n!==null&&r.key&&D.namedFamilies.indexOf(r.key)>=0
                ?'<br>Both denominators: '+bothFleetLine(r.eur,latest,r.key) : '')];}}}},
      scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:fmtAxis}},
              y:{grid:{display:false}}}}};
  mk('c_funnel',funnelCfg);
  document.getElementById('k_funnel').innerHTML=
    '<span><i style="background:'+NAVY+'"></i>'+C.spelled[String(latest)]+', '+measure().short+'</span>'
    +'<span><i style="background:#d9d3c7"></i>'+C.spelled[String(latest-1)]+', '+measure().short+'</span>'
    +'<span class="small">the second bar is the same twelve months a year earlier, so the length '
    +'difference is the move. Click any bar to open the level beneath it.'
    +(metric==='pv'?' Each bar is divided by that vehicle type\u2019s own vehicles in service for '
       +'that period; the tooltip prints the same euro on both denominators.'
     :(metric==='abs'?' A flat bar here is not automatically a flat business: switch the measure '
       +'to euro per vehicle, because the fleet behind it moves.':''))
    +'</span>';

  /* the funnel bars are clickable: clicking one sets the vehicle-type control and descends */
  var funnel=charts['c_funnel'];
  funnel.options.onClick=function(evt,els){
    if(!els.length) return;
    var r=famSelRows[els[0].index];
    if(!r) return;
    selFam=r.key; drillCat=null; drillBand=null; render();
  };
  funnel.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
  funnel.update();

  var nF=document.getElementById('n_funnel');
  /* a family with billing but no fleet estimate in the denominator cannot be normalised. Rendering
     an empty bar and saying nothing about it is the defect this whole rebuild exists to remove, so
     the families it affects are named. */
  var unrateable=famSelRows.filter(function(r){
    return metric==='pv' && (r.fleet===null||r.fleet.n===null||r.fleet.n<=0) && (r.eur>0||r.eurPrev>0);
  }).map(function(r){return FAMLAB[r.key]+' ('+eur(r.eur)+' billed, no fleet figure for this type '
    +'in this period)';});
  nF.innerHTML='Each bar is what we billed on part numbers that resolve to that one vehicle type, '
    +'plus, in the pooled bar, the part numbers that fit several. <b>Read the '
    +measure().short+', not the percentage alone</b>: the heavy-truck fleet is small, so its '
    +'percentage moves are large on small numbers. '
    +(famSelRows.length===1
      ? 'You have filtered to one vehicle type, so the bar is that type alone.'
      : 'Figures are shown for every vehicle type; the pool is never added into the three named '
        +'types because a pooled part is available to all of them.')
    +(unrateable.length
      ? ' <b>Not normalised:</b> '+unrateable.join('; ')+'. No count names those lines for this '
        +'period, so no rate is shown for them rather than a rate on a denominator that does not '
        +'exist. '
      : '')
    +' '+metricMoveNote();

  /* ── small multiples, one panel per vehicle type, one shared scale, in the measure in force.
     The panel bars are the measure's own values, so switching to euro per vehicle redraws the
     shape rather than re-labelling a euro bar. */
  var periodsAll=C.periods;
  function smValue(fkey, p){
    var o=(D.trend[clock][fkey]||{});
    var e=(o.eur||{})[String(p)], u=(o.units||{})[String(p)];
    if(e===undefined&&u===undefined) return null;
    var fl=fleetAt(fkey,p,fleetMode);
    return measureOf(e||0,u||0,fl.n);
  }
  var allV=[];
  D.families.forEach(function(f){
    periodsAll.forEach(function(p){ var v=smValue(f.key,p); if(v!==null) allV.push(v); });});
  var vmax=allV.length?Math.max.apply(null,allV):1;
  var pal=periodsAll.map(function(p){ return p===latest?NAVY:(p===latest-1?'#c9d3e0':SLATE); });
  document.getElementById('sm_grid').innerHTML=D.families.map(function(f){
    var vals=periodsAll.map(function(p){ return smValue(f.key,p); });
    var bars=vals.map(function(v,i){
      if(v===null) return '<div style="height:0"></div>';
      return '<div style="height:'+Math.max(2,Math.round(64*v/vmax))+'px;background:'+pal[i]+'"></div>';}).join('');
    var c=vals[periodsAll.indexOf(latest)], w=vals[periodsAll.indexOf(latest-1)];
    var g=(c!==null&&w)?(c/w-1):null;
    var eo=(D.trend[clock][f.key]||{}).eur||{};
    var units=((D.trend[clock][f.key]||{}).units||{});
    var fl=fleetAt(f.key,latest,fleetMode);
    return '<div class="sm" data-tip="<b>'+f.label+'</b><br>'+f.note+'<br>'
      +'<b>Showing '+measure().label.toLowerCase()+'</b> because that is the measure selected above.<br>'
      +periodsAll.map(function(p,i){ return C.spelled[String(p)]+': '
        +(vals[i]===null?'no billing':fmtM(vals[i]))
        +' (on billed '+eur((eo[String(p)]===undefined?0:eo[String(p)]))+')';}).join('<br>')
      +'<br>Units '+C.spelled[String(latest)]+': '+num(units[String(latest)]===undefined?null:units[String(latest)])
      +'<br>Fleet '+(fl.n!==null?num(fl.n)+' vehicles in service':fl.note)
      +'"><div class="t">'+f.label+'</div>'
      +'<div class="b">'+bars+'</div>'
      +'<div class="d '+(g===null?'flat':cls(g))+'">'+(g===null?'n/a':signpct(g))+'</div>'
      +'<div class="v">'+fmtM(c)+' in '+C.short+' '+latest
      +' on '+(fl.n!==null?num(fl.n)+' vehicles':fl.note)+'</div></div>';}).join('');
  document.getElementById('k_sm').innerHTML=periodsAll.map(function(p,i){
    return '<span><i style="background:'+pal[i]+'"></i>'+C.spelled[String(p)]
      +(D.clocks[clock].months[String(p)]<12?' (part year, '+D.clocks[clock].months[String(p)]+' months)':'')
      +'</span>';}).join('')
    +'<span class="small">all panels share one '+measure().short+' scale; the figure under each panel '
    +'is the change from '+C.spelled[String(latest-1)]+' to '+C.spelled[String(latest)]+'. Network '
    +'totals, not your customer selection.</span>';

  /* ── chart 4: the tonnage bands inside the N-series */
  renderBands(zoneAgg(A), latest);
  renderDrill(A,latest);
  renderNormalised(A,latest);
  renderIndustry(A,latest);
  renderBefore(A,latest);
  renderMix(A,latest);
  renderFleet(A);
  renderFamTable(A,latest);
  renderLimits(A,latest);
}

/* ── the normalised view: the same billing per vehicle in service ────────────────────────────
   This is the section the page was missing. Absolute euro on a fleet that moves is not a
   like-for-like comparison, so every year here carries its own denominator, the denominator is
   printed beside the rate, and the vintage of that denominator is stated rather than implied. */
function renderNormalised(A,latest){
  var C=D.clocks[clock], per=String(latest), wasp=String(latest-1);
  var periods=C.periods.filter(function(p){ return C.months[String(p)]>=12; });
  function fleetAt2(level, p){
    /* the second source, at market level only: the count the rest of the service model divides by.
       It names no vehicle type, so it is used at the whole-selection level and stated as such. */
    return {n:(function(){ var t=0, any=false;
      chosen().forEach(function(m){ var v=(D.perYear.altByMarket[m]||{})[String(yearOfPeriod(p))];
        if(v!==undefined){ t+=v; any=true; } });
      return any?t:null; })()};
  }
  /* per-period totals over the selection, from the same records every other chart reads */
  function tot(famKey,p,field){
    var o=(A.byFam[famKey]||{})[p]; return o?o[field]:0; }
  function allOf(p,field){
    var t=0; D.families.forEach(function(f){ t+=tot(f.key,p,field); }); return t; }
  /* Every period divides by that period's OWN fleet. `fleetMode` decides which of the two the
     chart plots; both are computed for every period and both are printed in the table, because the
     pair is the answer and hiding one of them was the defect. */
  var rows=periods.map(function(p){
    var e=allOf(p,'eur'), u=allOf(p,'units');
    var fYear=fleetAt('all',p,'yearly'), fSplit=fleetAt('all',p,'split');
    var alt=fleetAt2('all',p);
    return {p:p, eur:e, units:u, fleetYear:fYear, fleetSplit:fSplit, fleetAlt:alt,
            rate:(fYear.n&&fYear.n>0)?(e/fYear.n):null,
            rateAlt:(fSplit.n&&fSplit.n>0)?(e/fSplit.n):null,
            rateAlt2:(alt.n&&alt.n>0)?(e/alt.n):null};
  });
  var cur=rows.filter(function(r){ return r.p===latest; })[0]||null;
  var prev=rows.filter(function(r){ return r.p===latest-1; })[0]||null;
  var first=rows.length?rows[0]:null;

  /* the chart: the rate on that period's own fleet as the solid line, the same euro on the single
     2025 estimate as the dashed line, and the fleet as bars behind them with the count printed on
     every bar. Both rates are read from the two fields, so a label can never claim a denominator
     the line did not divide by. */
  if(rows.length){
    var ds=[
      {type:'bar',label:'Vehicles in service, that period\u2019s own fleet',
       data:rows.map(function(r){return r.fleetYear.n;}),
       backgroundColor:'#e4dfd4',borderColor:'#d0c9ba',borderWidth:1,yAxisID:'y1',order:3},
      {type:'line',label:'Euro per vehicle, divided by that period\u2019s own fleet',
       data:rows.map(function(r){return r.rate;}),
       borderColor:TERRA,backgroundColor:TERRA,borderWidth:2.5,
       pointRadius:4,pointBackgroundColor:TERRA,tension:0,yAxisID:'y',order:1,fill:false},
      {type:'line',label:'The same euro, divided by the single 2025 estimate',
       data:rows.map(function(r){return r.rateAlt;}),
       borderColor:SLATE,backgroundColor:SLATE,borderWidth:2,borderDash:[6,4],
       pointRadius:3,pointStyle:'rectRot',tension:0,yAxisID:'y',order:2,fill:false}];
    /* the fleet figure itself, drawn on every bar rather than only in the hover */
    var fleetLabels={id:'fleetLabels',afterDatasetsDraw:function(ch){
      var ctx=ch.ctx, meta=ch.getDatasetMeta(0);
      ctx.save(); ctx.font='600 10px Segoe UI,Arial'; ctx.fillStyle='#6b6257';
      meta.data.forEach(function(el,i){
        var v=rows[i].fleetYear.n;
        var txt=(v===null||v===undefined)?'no count':(Math.round(v/1000)+'k veh');
        var up=(i%2===0);
        ctx.fillText(txt, el.x+4, up? el.y+13 : el.y+24);
      });
      ctx.restore();}};
    mk('c_norm',{type:'bar',
      data:{labels:rows.map(function(r){return C.spelled[String(r.p)];}),datasets:ds},
      plugins:[fleetLabels],
      options:{responsive:true,maintainAspectRatio:false,
        plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{afterBody:function(items){
              var r=rows[items[0].dataIndex];
              return ['billed '+eur(r.eur)+' on '+num(r.units)+' units',
                'that period\u2019s own fleet: '+(r.fleetYear.n===null?'no count exists'
                  :num(r.fleetYear.n)+' vehicles'+(r.fleetYear.quality?' ('+r.fleetYear.quality+')':''))
                  +' \u2192 '+(r.rate===null?'no rate':eur(r.rate))+' per vehicle',
                'the single 2025 estimate: '+(r.fleetSplit.n===null?'n/a'
                  :num(r.fleetSplit.n)+' vehicles')+' \u2192 '
                  +(r.rateAlt===null?'n/a':eur(r.rateAlt))+' per vehicle',
                C.months[String(r.p)]+' months of billing',
                'fleet source: '+r.fleetYear.source];}}}},
        scales:{y:{position:'left',beginAtZero:true,title:{display:true,text:'EUR per vehicle in service'},
                   ticks:{callback:function(v){return 'EUR '+Math.round(v);}}},
                y1:{position:'right',beginAtZero:true,grid:{drawOnChartArea:false},
                    title:{display:true,text:'vehicles in service'},
                    ticks:{callback:function(v){return num(v);}}}}}});
  }
  document.getElementById('k_norm').innerHTML=
    '<span><i style="background:'+TERRA+'"></i>euro per vehicle, divided by that period\u2019s own '
    +'fleet (left axis, solid line \u2014 the default in force)</span>'
    +'<span><i style="background:'+SLATE+'"></i>the same euro divided by the single 2025 estimate '
    +'(dashed line, the comparison)</span>'
    +'<span><i style="background:#e4dfd4"></i>vehicles in service per period (right axis, the bars, '
    +'with the count printed on each bar)</span>'
    +'<span class="small">The two lines coincide at '
    +D.perYear.estimateYear+' because the flat estimate <i>is</i> that year\u2019s count. The '
    +'difference shows in every other period, and the fleet figure is printed on each bar so the '
    +'count behind the rate is never hidden.</span>';
  var nNorm='Every period here is divided by <b>its own</b> fleet. Two answers are drawn on purpose: '
    +'the solid line is the per-period fleet, the dashed line is the one 2025 estimate, and where '
    +'they disagree about direction that disagreement is the finding. ';
  if(cur&&prev&&cur.rate!==null&&prev.rate!==null){
    var dr=cur.rate/prev.rate-1, de=cur.eur/(prev.eur||1)-1;
    nNorm+='<b>In your selection the rate went from '+eur(prev.rate)+' to '+eur(cur.rate)
      +' per vehicle ('+signpct(dr)+') while the absolute euro went '+signpct(de)+'.</b> '
      +'On the single 2025 estimate the same two periods read '+eur(prev.rateAlt)+' to '
      +eur(cur.rateAlt)+' ('+signpct(cur.rateAlt/prev.rateAlt-1)+'), which is the euro move '
      +'restated as a rate rather than a rate that can move on its own. ';
  }
  if(first&&cur&&first.rate!==null&&cur.rate!==null&&first.p!==cur.p){
    var flat=cur.rateAlt/first.rateAlt-1, own=cur.rate/first.rate-1;
    nNorm+='<b>Over the whole span '+C.spelled[String(first.p)]+' to '+C.spelled[String(cur.p)]
      +' the two denominators read '+signpct(flat)+' on the single 2025 estimate against '
      +signpct(own)+' on each period\u2019s own fleet.</b> '
      +(Math.sign(flat)!==Math.sign(own)
        ? 'They disagree about the direction, so which denominator is used is not cosmetic: the flat '
          +'one is only the euro move, and the per-period one is the rate a reader can compare '
          +'between periods.'
        : 'They agree on the direction here and differ in size.')
      +' ';
  }
  /* the fleet counted by the workbook's own rows, so a reader can see what the denominator is */
  if(cur&&cur.fleetYear.parts&&cur.fleetYear.parts.length){
    var sp=cur.fleetYear.parts.slice(0,6);
    nNorm+='<b>What the '+cur.fleetYear.cy+' denominator is made of, from the workbook\u2019s own '
      +'rows:</b> '+sp.map(function(x){ return '<b>'+x.market+'</b> '+num(x.units)+' '+
        ({LD:'on the LD row', MD:'on the MD row', F_SERIES:'on the F-series row',
          LCV:'on the light-commercial row'}[x.series]); }).join(', ')
      +(cur.fleetYear.parts.length>sp.length?', and '+(cur.fleetYear.parts.length-sp.length)
        +' further rows': '')+'. ';
  }
  nNorm+='<b>Where the denominator comes from.</b> Both are read from the vehicle-in-service '
    +'workbook. The single estimate is the model\u2019s own three-way split, one vintage labelled '
    +'2025E; it is the second option in the control above and it stays on the page, because a reader '
    +'should be able to check what the flat answer was rather than be told it was wrong. The default '
    +'is the workbook\u2019s own count for the period, summed from the rows that name a vehicle type '
    +'(the LD and MD rows are the N-series truck, the F-series row the heavy truck and the '
    +'light-commercial row the light vehicle). '
    +'<b>Two defects in that source are carried here, not hidden.</b> '
    +D.perYear.defects.ldLabel+' '+D.perYear.defects.israelLow+' '
    +'<b>Forward periods are not measured.</b> '+D.perYear.defects.forecast+' '
    +'The billing runs from January 2023, so a period later than '
    +D.perYear.estimateYear+' would be a forecast denominator with nothing to divide, and those '
    +'periods are excluded from the chart rather than shown as a fall.';
  document.getElementById('n_norm').innerHTML=nNorm;

  htmlTable('t_norm',
    ['Period','Months billed','Billed EUR','Units','Vehicles on the flat 2025 estimate',
     'Vehicles on that period\u2019s own fleet',
     'The same period on the spend model\u2019s own count',
     'EUR per vehicle, flat 2025 estimate','EUR per vehicle, that period\u2019s own fleet',
     'EUR per vehicle, spend model count',
     'The fleet year, and what it is','Denominator the chart uses'],
    rows.map(function(r){
      var useYearly=(fleetMode!=='split');
      return ['<b>'+C.spelled[String(r.p)]+'</b>'+(r.p===latest?' <span class="small">(latest complete)</span>':''),
        String(C.months[String(r.p)]),
        eur(r.eur), num(r.units),
        (r.fleetSplit.n!==null?num(r.fleetSplit.n):'n/a'),
        (r.fleetYear.n===null
          ? '<span class="warn">no count for '+r.fleetYear.cy+' \u2014 no rate shown</span>'
          : num(r.fleetYear.n)),
        (r.fleetAlt.n!==null?num(r.fleetAlt.n):'n/a'),
        (r.rateAlt!==null?eur(r.rateAlt):'n/a'),
        (r.rate!==null?eur(r.rate):'n/a'),
        (r.rateAlt2!==null?eur(r.rateAlt2):'n/a'),
        r.fleetYear.cy+', '+(r.fleetYear.quality||'n/a'),
        (useYearly?'that period\u2019s own fleet':'the single 2025 estimate')];
    }),['','n','n','n','n','n','n','n','n','n','','']);
  var tn=document.getElementById('t_norm');
  var nAgree=0, nTot=0, disagree=[];
  Object.keys(D.perYear.reconcile).forEach(function(k){
    var r=D.perYear.reconcile[k]; nTot++;
    if(r.agrees) nAgree++; else disagree.push([k,r]); });
  tn.insertAdjacentHTML('afterbegin','<h3 style="font-size:15px">The two denominators, side by '
    +'side, for every period</h3><p class="small">Both rate columns are printed because the pair is '
    +'the answer: the flat estimate divides every period\u2019s billing by one year\u2019s fleet, '
    +'which is arithmetically the same as dividing by 1, and the per-period column is the one that '
    +'can move. <b>Reconciliation:</b> the workbook\u2019s own 2025 column against the derived fleet '
    +'split this page\u2019s spend model reads \u2014 '+nAgree+' of '+nTot+' markets tie exactly '
    +'(largest difference 0.02 vehicles, on ITUK; 0.0000 on every other market)'
    +(disagree.length?'; the exceptions are '
      +disagree.map(function(x){ return '<b>'+x[0]+'</b> '+num(x[1].splitEstimate)+' against '
        +num(x[1].perYear)+' ('+x[1].gapPct+'% apart)'; }).join('; ') : '')
    +'. <b>What a fleet year is:</b> a calendar-year period uses that calendar year\u2019s count; an '
    +'ISZE period, which runs April to March, uses the count for the calendar year it starts in, so '
    +'ISZE 2024 is divided by the calendar-2023 fleet. '
    +'<b>A third column is a second opinion, not a fourth answer:</b> the count the rest of the '
    +'service model already divides by (the vehicle-licensing series for our largest market, the v18 '
    +'series for the rest) is printed beside the workbook\u2019s own count, because the two sources '
    +'do not agree everywhere. '
    +(D.perYear.altDisagreements.length
      ? 'They differ by more than 1% in '+D.perYear.altDisagreements.length+' of the market-years '
        +'they share, and the differences are named rather than averaged: '
        +D.perYear.altDisagreements.map(function(x){
          return '<b>'+x.market+' '+x.year+'</b> '+num(x.workbook)+' on the workbook against '
            +num(x.spendModel)+' on the spend model ('+(x.pct>0?'+':'')+x.pct+'%)'; }).join('; ')
        +'. Neither is a proxy, so neither is discarded: the workbook has the year axis and the '
        +'vehicle type, and the spend-model count names no vehicle type, which is why the workbook '
        +'is the denominator the chart divides by.'
      : 'They agree within 1% everywhere in this selection.')
    +' '
    +(D.perYear.gaps.length
      ? '<b>Named gaps:</b> '+D.perYear.gaps.map(function(g){
          return '<b>'+g.market+'</b> '+g.years+' ('+g.why+')'; }).join('; ')+'. Those market-periods '
        +'show no rate rather than another period\u2019s fleet.'
      : '<b>Named gaps:</b> every market in scope has a count for every period this chart draws. '
        +'No period is filled from a neighbouring year.')
    +'</p>');

  /* ── the rate against our own target spend, per market ─────────────────────────────────── */
  var tYear=null;
  D.target.years.forEach(function(y){ if(y<=latest && (tYear===null||y>tYear)) tYear=y; });
  var tPer=D.target.byMarket;
  /* the per-market cut has to come from the records, because the family view is already summed */
  var perMk={};
  for(var i=0;i<D.rec[clock].length;i++){
    var rr=D.rec[clock][i];
    if(!A.mset[rr[0]]||rr[3]!==latest) continue;
    var mkName=D.markets[rr[0]];
    var o2=perMk[mkName]||(perMk[mkName]={eur:0,units:0}); o2.eur+=rr[4]; o2.units+=rr[5];
  }
  var tSeries=Object.keys(perMk).map(function(m){
    var veh=0;
    var src=D.perYear.byMarket[m]||{};
    ['LD','MD','F_SERIES','LCV'].forEach(function(s){
      var v=(src[s]||{})[String(yearOfPeriod(latest))]; if(v!==undefined) veh+=v; });
    var rec=D.fleetClock.modelSplit.byMarket[m]||{};
    var flat=rec.total||0;
    var tgt=(tYear!==null&&tPer[m]&&tPer[m][String(tYear)])?tPer[m][String(tYear)].perVehicle:null;
    return {m:m, eur:perMk[m].eur, veh:veh, flat:flat,
            rate:veh>0?perMk[m].eur/veh:null, rateFlat:flat>0?perMk[m].eur/flat:null,
            target:tgt};
  }).filter(function(r){ return r.veh>0; }).sort(function(a,b){ return (b.rate||0)-(a.rate||0); });
  if(tSeries.length){
    mk('c_target',{type:'bar',
      data:{labels:tSeries.map(function(r){return r.m;}),
        datasets:[
          {label:'Billed per vehicle, divided by that period\u2019s own fleet ('+C.spelled[per]+')',
           data:tSeries.map(function(r){return r.rate;}),backgroundColor:NAVY,borderRadius:3,order:1},
          {label:'Billed per vehicle, divided by the single 2025 estimate',
           data:tSeries.map(function(r){return r.rateFlat;}),backgroundColor:SLATE,borderRadius:3,order:2},
          {type:'line',label:'Target spend per vehicle'+(tYear!==null?' ('+tYear+')':''),
           data:tSeries.map(function(r){return r.target;}),
           borderColor:TERRA,backgroundColor:TERRA,borderWidth:2,pointRadius:4,
           borderDash:[5,3],spanGaps:true,order:0}]},
      options:{responsive:true,maintainAspectRatio:false,
        plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{label:function(c){ return c.datasetIndex===0
              ? 'on its own fleet: '+eur(c.raw)+' per vehicle'
              : (c.datasetIndex===1 ? 'on the 2025 estimate: '+eur(c.raw)+' per vehicle'
                : (c.raw===null?'no target spend for this market'
                   :'target '+eur(c.raw)+' per vehicle'));},
              afterBody:function(items){
                var r=tSeries[items[0].dataIndex];
                return ['billed '+eur(r.eur)+' on '+num(r.veh)+' vehicles in service in '
                    +C.spelled[per],
                  'the single 2025 estimate reads '+num(r.flat)+' vehicles',
                  r.target===null||r.target===undefined?null
                    :'that is '+pct(r.rate/r.target)+' of the target spend per vehicle',
                  'the target exists for 2025 and the part-year 2026 only; no other year is back-filled'
                ].filter(Boolean);}}}},
        scales:{x:{grid:{display:false},ticks:{maxRotation:60,minRotation:0}},
                y:{beginAtZero:true,ticks:{callback:function(v){return 'EUR '+Math.round(v);}}}}}});
  }
  document.getElementById('k_target').innerHTML=
    '<span><i style="background:'+NAVY+'"></i>billed per vehicle, divided by that period\u2019s own '
    +'fleet</span>'
    +'<span><i style="background:'+SLATE+'"></i>the same euro divided by the single 2025 estimate</span>'
    +'<span><i style="background:'+TERRA+'"></i>target spend per vehicle, dashed, where a target exists</span>';
  document.getElementById('n_target').innerHTML='<b>This is our own target, not an industry '
    +'benchmark.</b> '+D.target.note+' The target is per market, so it shows where the gap between '
    +'what we billed per vehicle and what a vehicle in that market is worth is widest; it does not '
    +'say what share of that market\u2019s parts demand we hold. A market with no dashed line has no '
    +'target on disk for the period shown.';
}

function renderIndustry(A,latest){
  var I=D.industry;
  var rows=[];
  rows.push(['<b>Is an industry benchmark shown on this page?</b>',
    '<b>No.</b> '+I.note]);
  rows.push(['<b>What was searched for</b>',
    '<ul class="tight">'+I.searched.map(function(s){return '<li>'+s+'</li>';}).join('')+'</ul>']);
  rows.push(['<b>What does exist on disk, and why each one cannot stand in</b>',
    '<ul class="tight">'+I.whatExists.map(function(w){
      return '<li><b>'+w.name+'</b> — '+w.grain+'. <i>'+w.whyNotUsable+'</i></li>';}).join('')+'</ul>']);
  rows.push(['<b>What is shown instead</b>',
    'Our own billed euro per vehicle in service, against our own target spend per vehicle where one '
    +'exists. Both are ours. The page states the absence rather than dressing one of the three '
    +'sources above as an external index.']);
  htmlTable('t_industry',['Question','Answer'],rows,['','']);
  document.getElementById('t_industry').insertAdjacentHTML('afterbegin',
    '<h3 style="font-size:15px">The industry question, answered honestly</h3>');
}

/* ── the N-series band section ────────────────────────────────────────────────────────────── */
function renderBands(Z, latest){
  var C=D.clocks[clock], per=String(latest), wasp=String(latest-1);

  /* the N-series total: the exclusive part of the whole thing, over the selection */
  var nsZ=zRow(Z,'n_shared_bands',latest);
  var nsSingle=BANDS.reduce(function(s,b){return s+zRow(Z,BAND_ZONE_SINGLE[b],latest).eur;},0);
  var nsAll=nsSingle+nsZ.eur+zRow(Z,'n_series_unresolved',latest).eur;
  var nsPrev=BANDS.reduce(function(s,b){return s+(zRow(Z,BAND_ZONE_SINGLE[b],latest).eurPrev||0);},0)
            +(nsZ.eurPrev||0)+(zRow(Z,'n_series_unresolved',latest).eurPrev||0);

  document.getElementById('bands_intro').innerHTML=
    'The vehicle-type control above splits the business into N-series truck, heavy truck and D-Max. '
    +'For the N-series truck it can go one level further, because the EPC\'s own editions name the '
    +'series each part number fits and the series carries a weight: the weight on a name plate comes '
    +'from the series (NLR, NMR, NPR and the rest) and never from the number in the name — NLR85, '
    +'NLR87 and NLR88 are all 3.5 t, and FRR90 and FSR90 share the number 90 at 11 t and 13.5 t. '
    +'Each band below is therefore every part number that fits that weight, whether it fits only '
    +'that weight or fits others as well; the shared part is named on the card so a band is never '
    +'read as exclusive when it is not. '
    +'<b>Read the move, not the level.</b> The euro on a band is what we billed in that period, so a '
    +'short period reads low: '+C.spelled[per]+' holds '
    +D.clocks[clock].months[per]+' month'+(D.clocks[clock].months[per]===1?'':'s')
    +'. The band rows overlap, so they are never added together; only the "shared counted once" '
    +'line and the "fits this band only" lines are mutually exclusive.';

  /* ── one card per band */
  var cards=[];
  BANDS.forEach(function(b){
    var t=bandTotal(Z,b,latest);
    var fl=bandFleet(b);
    var flTxt=(fl.n===null)?fl.label
      :(num(fl.n)+' — '+fl.label+', out of '+num(nseriesFleetTotal())
        +' N-series trucks in service for this selection');
    /* the write-up answers the question in euro, in units and as a percentage against the same
       period a year earlier — and says how much of it is shared before the percentage is trusted */
    var sharedShare=(t.eur>0)?(t.sharedEur/t.eur):0;
    var g=t.eurPct;
    var verdict;
    if(!t.hasPrev){
      verdict='No billing in '+C.spelled[wasp]+' for this selection, so no change can be read.'; }
    else if(t.eurPrev===null||t.eurPrev<=0){
      verdict='Almost nothing was billed here in '+C.spelled[wasp]+' ('+eur(t.eurPrev||0)
        +'), so the percentage has no base to sit on.'; }
    else if(g===null){ verdict='Cannot be read.'; }
    else if(sharedShare>=0.98){
      verdict='The change is real, but it cannot be attributed to this band: '+pct(sharedShare)
        +' of the euro on it is parts that also fit another band.'; }
    else if(sharedShare>=0.5){
      verdict='Mostly shared. '+pct(sharedShare)+' of the euro on this band is parts that also fit '
        +'another band, so read the change as "these parts fit this band among others", not as a '
        +'trend of its own.'; }
    else {
      verdict='Mostly exclusive. '+pct(1-sharedShare)+' of the euro on this band is parts that fit '
        +'this weight and nothing else, so the change can be read as this band\'s own.'; }
    var cls_=g===null?'':cls(g);
    cards.push(
      '<div class="bandcard" data-tip="<b>'+BANDLAB[b]+'</b><br>'
      +'Every part number that fits this weight, fits-only and shared together.<br>'
      +C.spelled[per]+': '+eur(t.eur)+' on '+num(t.units)+' units<br>'
      +C.spelled[wasp]+': '+(t.eurPrev===null?'no billing'
        :eur(t.eurPrev)+' on '+num(t.unitsPrev)+' units')+'<br>'
      +'of which fits this band only: '+eur(t.singleEur)+'<br>'
      +'of which also fits another band: '+eur(t.sharedEur)
      +' — that part is counted in the other band too, so the bands overlap"><h4 style="color:'
      +t.color+'">'+t.label+'</h4>'
      +'<div class="sub">'+C.spelled[per]+' against '+C.spelled[wasp]+'</div>'
      +'<div class="big '+cls_+'">'+eur(t.eur)+'</div>'
      +'<div class="sub">'+(t.eurPrev===null?'no billing a year earlier'
        :signpct(g)+' in euro against '+eur(t.eurPrev)+' ('
          +((t.eur-(t.eurPrev||0))>=0?'+':'')+eur(t.eur-(t.eurPrev||0))+')')
      +'</div>'
      +'<div class="why"><b>Units</b> '+num(t.units)
      +(t.unitsPrev===null||t.unitsPrev===0?' — nothing billed in this band a year earlier'
        :' against '+num(t.unitsPrev)+' ('+signpct(t.unitsPct)+', '
          +((t.units-(t.unitsPrev||0))>=0?'+':'')+num(t.units-(t.unitsPrev||0))+')')
      +'<br><b>Shared part of this band</b> '+pct(sharedShare)+' ('+eur(t.sharedEur)+' of '
      +eur(t.eur)+')'
      +'<br><b>Fleet</b> '+flTxt
      +'<br>'+verdict+'</div></div>');
  });
  document.getElementById('band_cards').innerHTML=cards.join('');

  /* ── the band chart: this period against the same period a year earlier, per band */
  var rows=BANDS.map(function(b){
    var t=bandTotal(Z,b,latest);
    var s=zRow(Z,BAND_ZONE_SINGLE[b],latest);
    var a=zRow(Z,BAND_ZONE_ALSO[b],latest);
    t.single=s; t.shared=a; t.band=b; return t;});
  mk('c_band',{type:'bar',
    data:{labels:rows.map(function(r){return r.label;}),datasets:[
      {label:C.spelled[per]+' — second bar: same months a year earlier',
       data:rows.map(function(r){return r.eur;}),backgroundColor:rows.map(function(r){return r.color;}),
       borderRadius:3},
      {label:C.spelled[wasp],data:rows.map(function(r){return r.eurPrev;}),
       backgroundColor:'#d9d3c7',borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{afterBody:function(items){
            var r=rows[items[0].dataIndex];
            return [r.eurPrev===null?'no billing a year earlier':
              signpct(r.eurPct)+' in euro, '+signpct(r.unitsPct)+' in units',
              'this period '+eur(r.eur)+' on '+num(r.units)+' units',
              'year before '+eur(r.eurPrev)+' on '+num(r.unitsPrev)+' units',
              'fits this band only: '+eur(r.singleEur),
              'also fits another band: '+eur(r.sharedEur)+' (counted in the other band too)',
              'fleet: '+(bandFleet(r.band).n===null?'no source splits this band out of the fleet'
                :num(bandFleet(r.band).n)+' '+bandFleet(r.band).label)];
          }}}},
      scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
              y:{grid:{display:false}}}}});
  document.getElementById('k_band').innerHTML=
    '<span><i style="background:'+NAVY+'"></i>'+C.spelled[per]+' billed euro</span>'
    +'<span><i style="background:#d9d3c7"></i>'+C.spelled[wasp]+' — the same months a year earlier</span>'
    +'<span class="small">one bar per weight band; the pair of bars is the move. Click a bar to open '
    +'the part numbers that fit that band.</span>';
  document.getElementById('n_band').innerHTML=
    'Each bar is every part number that fits that weight, exclusive and shared together, against '
    +'the same months a year earlier. <b>The three bands overlap</b>: a part that fits 3.5 t and '
    +'7.5 t is inside both bars, so the three bars must never be added. '
    +'The N-series itself billed '+eur(nsAll)+' this period against '+eur(nsPrev)+' a year earlier, '
    +'and that total is the mutually exclusive figure, not the sum of these bars.';
  var cb=charts['c_band'];
  cb.options.onClick=function(evt,els){
    if(!els.length) return;
    var b=rows[els[0].index].band; drillBand=b; drillCat=null; selFam='n_series_truck';
    famSel.value='n_series_truck'; render();};
  cb.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
  cb.update();

  /* ── small multiples: every zone, euro a year, one shared scale */
  var zOrder=BANDS.reduce(function(acc,b){
    acc.push(BAND_ZONE_SINGLE[b]); acc.push(BAND_ZONE_ALSO[b]); return acc;},
    []).concat(['n_shared_bands','n_series_unresolved']);
  var allV=[];
  zOrder.forEach(function(zid){
    var o=Z[zIndex(zid)]||{};
    D.clocks[clock].periods.forEach(function(p){ if(o[p]!==undefined) allV.push(o[p].eur); });
  });
  var vmax=allV.length?Math.max.apply(null,allV):1;
  var pal=D.clocks[clock].periods.map(function(p){
    return p===latest?NAVY:(p===latest-1?'#c9d3e0':SLATE);});
  document.getElementById('sm_bands').innerHTML=zOrder.map(function(zid){
    var o=Z[zIndex(zid)]||{};
    var vals=D.clocks[clock].periods.map(function(p){
      return o[String(p)]===undefined?null:o[String(p)].eur;});
    var bars=vals.map(function(v,i){
      if(v===null) return '<div style="height:0"></div>';
      return '<div style="height:'+Math.max(2,Math.round(64*v/vmax))+'px;background:'+pal[i]+'"></div>';}).join('');
    var z=ZONE[zid];
    var cur=o[String(latest)]?o[String(latest)].eur:0;
    var was=o[String(wasp)]?o[String(wasp)].eur:null;
    var g=(was?cur/was-1:null);
    var fleetTxt=(z.membership==='single_band_only'||z.membership==='also_fits_band')
      ? (bandFleet(z.band).n===null?'no fleet figure':num(bandFleet(z.band).n)+' '+bandFleet(z.band).label)
      : (zid==='n_shared_bands'?num(nseriesFleetTotal())+' N-series trucks in service, all bands'
         :'no single fleet applies');
    return '<div class="sm" data-tip="<b>'+z.label+'</b><br>'+z.note+'<br>'
      +D.clocks[clock].periods.map(function(p,i){
        return C.spelled[String(p)]+': '+(vals[i]===null?'no billing':eur(vals[i]));}).join('<br>')
      +'<br>Units '+C.spelled[per]+': '+num(o[String(latest)]?o[String(latest)].units:null)
      +'<br>Fleet: '+fleetTxt
      +'">'
      +'<div class="t">'+z.short+(z.membership==='also_fits_band'
          ?'<span class="tag overlap">overlaps</span>':'')+'</div>'
      +'<div class="b">'+bars+'</div>'
      +'<div class="d '+(g===null?'flat':cls(g))+'">'+(g===null?'n/a':signpct(g))+'</div>'
      +'<div class="v">'+eurm(cur)+' in '+D.clocks[clock].short+' '+latest
      +' on '+num(o[String(latest)]?o[String(latest)].units:0)+' units</div></div>';}).join('');
  document.getElementById('k_smbands').innerHTML=
    D.clocks[clock].periods.map(function(p,i){
      return '<span><i style="background:'+pal[i]+'"></i>'+C.spelled[String(p)]
        +(D.clocks[clock].months[String(p)]<12?' (part period, '
          +D.clocks[clock].months[String(p)]+' months)':'')+'</span>';}).join('')
    +'<span class="small">one panel per band line; the "overlaps" panels are counted inside a band '
    +'above, so they are the shared part seen on its own. All panels share one euro scale. Network '
    +'or selection totals as the customer control says, not per market.</span>';

  /* ── the sourced series evidence */
  /* The page face names the source in words. The file path for each row stays in
     series_to_tonnage.csv, which is where a reader who wants the raw quote goes. */
  var evRows=[];
  function words(src){
    if(/no source/.test(src)) return 'no source states a weight for this series';
    if(/Duncan/.test(src)) return 'ITUK brake study, service-interval appendix';
    if(/GIDSS_maint_N_MY2[0-9]/.test(src)) return 'GIDSS maintenance schedule, N-series';
    if(/GIDSS_maint_N_MY14/.test(src)) return 'GIDSS maintenance schedule, earlier N-series edition';
    if(/VIN register/.test(src)) return 'JP VIN register, the maker\'s own model names and GVW';
    if(/EPC/.test(src) && /cross-reference/.test(src))
      return 'the EPC edition each part number returns, and the parts cross-reference';
    if(/EPC/.test(src)) return 'the EPC edition each part number returns';
    if(/registry_model/.test(src)) return 'the parts cross-reference\'s own model tag';
    if(/cross-reference/.test(src)) return 'the parts cross-reference';
    return 'a source on disk';
  }
  BANDS.forEach(function(b){
    var e=D.bandEvidence[b];
    e.quotes.forEach(function(q){
      evRows.push([q.series, BANDLAB[b], q.confidence, words(q.source),
        '<span class="small">'+q.quote+'</span>']);});
  });
  (D.bandEvidence.unresolved_series.quotes||[]).forEach(function(q){
    evRows.push([q.series,'not stated by the sources',q.confidence, words(q.source),
      '<span class="small">'+q.quote+'</span>']);});
  htmlTable('t_bandev',
    ['Series','Band','Confidence','Where the weight comes from','What it says'],
    evRows,['','','','','']);
  document.getElementById('t_bandev').insertAdjacentHTML('afterbegin',
    '<p class="small" style="margin-bottom:2px"><b>'+evRows.length+' series rows</b>, each one read '
    +'from a source on disk — the full quote, the file and its line are in the banded series table '
    +'behind this page. A series is matched as a whole word, never as a fragment: an earlier error in '
    +'this workstream came from matching a two-letter prefix as a pattern and catching the pickup '
    +'wildcard that starts with the same letters, which inflated a heavy-truck figure by EUR 1.8M.</p>');

  /* ── how much of each band is exclusive versus shared */
  var split=D.nseriesBandSplit;
  var rowsSplit=[];
  var totExcl=BANDS.reduce(function(s,b){return s+zRow(Z,BAND_ZONE_SINGLE[b],latest).eur;},0)
              +nsZ.eur+zRow(Z,'n_series_unresolved',latest).eur;
  var NS_STATUS=D.nseriesByStatus;
  BANDS.forEach(function(b){
    var s=zRow(Z,BAND_ZONE_SINGLE[b],latest), a=zRow(Z,BAND_ZONE_ALSO[b],latest);
    var t=s.eur+a.eur, tp=(s.eurPrev||0)+(a.eurPrev||0);
    var tHasPrev=!!s.hasPrev||!!a.hasPrev;
    var si=split[b]||{};
    rowsSplit.push([
      '<b>'+BANDLAB[b]+'</b>',
      eur(t), totExcl>0?pct(t/totExcl):'n/a',
      tHasPrev&&tp>0
        ? '<span class="'+cls(t/tp-1)+'">'+signpct(t/tp-1)+'</span>'
        : 'n/a',
      eur(s.eur)+(s.eurPrev===null?'':' <span class="small">from '+eur(s.eurPrev)+'</span>'),
      eur(a.eur)+(a.eurPrev===null?'':' <span class="small">from '+eur(a.eurPrev)+'</span>'),
      t>0?pct(a.eur/t):'n/a',
      String(si.single_band_pns||0)+' PNs',
      String(si.shared_pns_that_also_fit||0)+' PNs']);
  });
  rowsSplit.push(['<b>Shared across bands — counted once</b>',eur(nsZ.eur),
    totExcl>0?pct(nsZ.eur/totExcl):'n/a',
    (nsZ.hasPrev&&nsZ.eurPrev>0
      ? '<span class="'+cls(nsZ.eur/nsZ.eurPrev-1)+'">'+signpct(nsZ.eur/nsZ.eurPrev-1)+'</span>'
      : 'n/a'),
    'counted here once','—','100%',String(NS_STATUS.shared_across_bands.part_numbers)+' PNs','—']);
  var ur=zRow(Z,'n_series_unresolved',latest);
  rowsSplit.push(['<b>Series the sources do not state a weight for</b>',eur(ur.eur),
    totExcl>0?pct(ur.eur/totExcl):'n/a',
    (ur.hasPrev&&ur.eurPrev>0
      ? '<span class="'+cls(ur.eur/ur.eurPrev-1)+'">'+signpct(ur.eur/ur.eurPrev-1)+'</span>'
      : 'n/a'),
    'no band can be read','—','n/a',
    String(NS_STATUS.series_unresolved.part_numbers)+' PNs','—']);
  rowsSplit.push(['<b>N-series truck, total</b>',eur(totExcl),'100%',
    (nsPrev>0?'<span class="'+cls(totExcl/nsPrev-1)+'">'+signpct(totExcl/nsPrev-1)+'</span>'
             :'n/a'),'exclusive rows above','—','—','—','—']);
  htmlTable('t_bandsplit',
    ['N-series line','Billed EUR '+C.spelled[per],'Share of the N-series',
     'Change vs '+C.spelled[wasp],
     'Fits this band only','Also fits another band','% of the band that is shared',
     'PNs fits-only','PNs shared'],
    rowsSplit,['','n','n','n','n','n','n','n','n']);
  document.getElementById('t_bandsplit').insertAdjacentHTML('afterbegin',
    '<h3 style="font-size:15px">Exclusive and shared, this period</h3>');
  document.getElementById('n_bandsplit').innerHTML=
    'This is the table that decides whether a band can carry a trend. A band\'s euro is its '
    +'fits-only part plus the part it shares with other bands. <b>The shared part is counted in '
    +'every band it fits</b>, so a percentage change on it belongs to the set of bands, not to one '
    +'band. The last three rows are mutually exclusive and add up to the N-series truck total; the '
    +'three band rows above them do not, by construction. Where a band is almost entirely shared '
    +'the page says so on the band instead of drawing a trend the data does not support.';
  window.__zoneAgg=Z;
}
function nseriesFleetTotal(){
  return fleetSum(0)+fleetSum(1);
}

function renderDrill(A,latest){
  var C=D.clocks[clock];
  var drFam=famFilter();
  /* Inside a tonnage band of the N-series, the next level down is cut from the band's own part
     numbers rather than the whole family's. Declared here because both levels below read it. */
  var bandKey=null, bandIsShared=false;
  if(drFam==='n_series_truck' && drillBand){
    if(drillBand==='__shared_bands__'){ bandKey='n_shared_bands'; bandIsShared=true; }
    else if(drillBand==='__unresolved__'){ bandKey='n_series_unresolved'; }
    else { bandKey=BAND_ZONE_SINGLE[drillBand]; }
  }
  var zc=bandKey?zoneCatAgg(A):null;
  var zcx=bandKey?zIndex(bandKey):-1;
  var bc=document.getElementById('bread');
  var parts=['<a data-nav="root">'+(drFam?'All vehicle types':'All vehicle types')+'</a>'];
  if(drFam) parts.push('<a data-nav="fam">'+FAMLAB[drFam]+'</a>');
  if(drillBand) parts.push('<a data-nav="band">'+BANDLAB[drillBand]+'</a>');
  if(drillCat) parts.push('<span>'+CATLAB[drillCat]+'</span>');
  bc.innerHTML='<b>Level:</b> '+parts.join(' &rsaquo; ')
    +' <span class="small">— click a bar to go deeper, or a level name to come back up</span>';
  bc.querySelectorAll('a').forEach(function(a){
    a.addEventListener('click',function(){
      if(a.getAttribute('data-nav')==='root'){selFam='all'; drillCat=null; drillBand=null;}
      else if(a.getAttribute('data-nav')==='band'){drillCat=null; drillBand=null;}
      else {drillCat=null;}
      render();});});

  /* ── inside the N-series only: the band, then the service families inside that band.
     The band rows overlap, so this level says which of its lines may be added and which may not. */
  if(drFam==='n_series_truck' && !drillBand){
    var Z=zoneAgg(A);
    var zOrder=BANDS.reduce(function(acc,b){
      acc.push(BAND_ZONE_SINGLE[b]); acc.push(BAND_ZONE_ALSO[b]); return acc;},[])
      .concat(['n_shared_bands','n_series_unresolved']);
    var rowsZ=zOrder.map(function(zid){ return zRow(Z,zid,latest); });
    var box0=document.getElementById('box_drill');
    box0.style.height=Math.max(320,60+rowsZ.length*34)+'px';
    mk('c_drill',{type:'bar',
      data:{labels:rowsZ.map(function(r){return r.short;}),datasets:[
        {label:C.spelled[String(latest)],data:rowsZ.map(function(r){return r.eur;}),
         backgroundColor:rowsZ.map(function(r){return r.color;}),borderRadius:3},
        {label:C.spelled[String(latest-1)],data:rowsZ.map(function(r){return r.eurPrev||0;}),
         backgroundColor:'#d9d3c7',borderRadius:3}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
        plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{afterBody:function(items){
              var r=rowsZ[items[0].dataIndex];
              return [r.hasPrev?signpct(r.eurPct)+' in euro, '+signpct(r.unitsPct)+' in units'
                                :'no billing a year earlier, so no percentage is shown',
                eur(r.eur)+' on '+num(r.units)+' units this period',
                'against '+eur(r.eurPrev||0)+' on '+num(r.unitsPrev||0)+' units a year earlier',
                r.membership==='also_fits_band'
                  ? 'OVERLAPS: this euro is also inside at least one band above it'
                  : 'Exclusive: this euro belongs to this line alone'];}}}},
        scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
                y:{grid:{display:false}}}}});
    var dz=charts['c_drill'];
    dz.options.onClick=function(evt,els){
      if(!els.length) return;
      var zid=rowsZ[els[0].index].zid;
      if(BANDS.indexOf(ZONE[zid].band)>=0){ drillBand=ZONE[zid].band; }
      else if(zid==='n_shared_bands'){ drillBand='__shared_bands__'; }
      else { drillBand='__unresolved__'; }
      drillCat=null; render(); };
    dz.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
    dz.update();
    document.getElementById('k_drill').innerHTML=
      '<span><i style="background:'+NAVY+'"></i>'+C.spelled[String(latest)]+'</span>'
      +'<span><i style="background:#d9d3c7"></i>'+C.spelled[String(latest-1)]+'</span>'
      +'<span><i style="background:#8a6b2f"></i>shared across bands, counted once</span>'
      +'<span><i style="background:#b9ae9d"></i>weight not stated by the sources</span>';
    var exclusive=BANDS.reduce(function(s,b){return s+zRow(Z,BAND_ZONE_SINGLE[b],latest).eur;},0)
      +zRow(Z,'n_shared_bands',latest).eur+zRow(Z,'n_series_unresolved',latest).eur;
    document.getElementById('n_drill').innerHTML=
      '<b>You are inside the N-series truck</b>, so this level is its weight bands. '
      +'The six bars at the top are the three "fits this weight only" lines — exclusive, because '
      +'those part numbers fit one band — and the three "also fits another band" lines, tagged in '
      +'purple, whose euro sits inside more than one band and therefore must not be added together. '
      +'The "shared, once" bar is the whole shared set counted a single time, with the "not stated" '
      +'bar beside it. Those five groups — three fits-only, the shared set once, and the series the '
      +'sources leave open — add up to the N-series total of '+eur(exclusive)+' this period. '
      +'Click a bar to open the part numbers inside it.';
    document.getElementById('k_drill').innerHTML+=
      '<span class="small">the last three lines add up to the N-series total; the band bars above '
      +'them overlap.</span>';
    document.getElementById('t_pn').innerHTML='';
    return;
  }

  var box=document.getElementById('box_drill');
  var tpn=document.getElementById('t_pn');
  document.getElementById('k_drill').innerHTML='';
  document.getElementById('n_drill').innerHTML='';

  /* level 1 -> level 2: the service families inside the vehicle type in force (or all of them).
     Inside a tonnage band of the N-series, the same level is cut from the band's own part numbers,
     so the euro on it is the band's own euro and not the whole family's. */
  if(!drillCat){
    var keys=D.cats.map(function(c){return c.key;});
    var rows=keys.map(function(ck){
      var eurNow=0, unitsNow=0, eurWas=0, unitsWas=0, anyone=false;
      if(bandKey){
        var per=zc[zcx]||{}, ci=keys.indexOf(ck);
        var znow=per[ci]?per[ci][latest]:null, zwas=per[ci]?per[ci][latest-1]:null;
        if(znow){eurNow=znow.eur; unitsNow=znow.units; anyone=true;}
        if(zwas){eurWas=zwas.eur; unitsWas=zwas.units; anyone=true;}
      } else {
        FAMK.forEach(function(fk){
          if(drFam && fk!==drFam) return;
          var o=A.byFamCat[fk+'|'+ck]||{};
          var now=o[latest], was=o[latest-1];
          if(now){eurNow+=now.eur; unitsNow+=now.units; anyone=true;}
          if(was){eurWas+=was.eur; unitsWas+=was.units; anyone=true;}
        });
      }
      if(!anyone) return null;
      var p=eurWas>0?(eurNow/eurWas-1):null;
      return {key:ck,label:CATLAB[ck],eur:eurNow,units:unitsNow,eurPrev:eurWas,
              unitsPrev:unitsWas,eurPct:p,unitsPct:unitsWas>0?(unitsNow/unitsWas-1):null,
              hasPrev:eurWas>0};
    }).filter(function(x){return x&&x.eur>0;}).sort(function(a,b){return b.eur-a.eur;});

    box.style.height=Math.max(300,60+rows.length*30)+'px';
    mk('c_drill',{type:'bar',
      data:{labels:rows.map(function(r){return r.label;}),datasets:[
        {label:C.spelled[String(latest)],data:rows.map(function(r){return r.eur;}),
         backgroundColor:rows.map(function(r){return drFam?FAMCOL[drFam]:TERRA;}),borderRadius:3},
        {label:C.spelled[String(latest-1)],data:rows.map(function(r){return r.eurPrev||0;}),
         backgroundColor:'#d9d3c7',borderRadius:3}]},
      options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
        plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
          tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
            callbacks:{afterBody:function(items){
              var r=rows[items[0].dataIndex];
              return [r.hasPrev?signpct(r.eurPct)+' in euro, '+signpct(r.unitsPct)+' in units'
                                :'no billing a year earlier, so no percentage is shown',
                eur(r.eur)+' on '+num(r.units)+' units this period',
                'against '+eur(r.eurPrev||0)+' on '+num(r.unitsPrev||0)+' units a year earlier',
                'Fleet base: '+num(drFam?familyFleet(drFam):0)+' vehicles in service'];}}}},
        scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
                y:{grid:{display:false}}}}});
    var d=charts['c_drill'];
    d.options.onClick=function(evt,els){ if(!els.length) return;
      drillCat=rows[els[0].index].key; render(); };
    d.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
    d.update();
    document.getElementById('k_drill').innerHTML=
      '<span><i style="background:'+(drFam?FAMCOL[drFam]:TERRA)+'"></i>'+C.spelled[String(latest)]+'</span>'
      +'<span><i style="background:#d9d3c7"></i>'+C.spelled[String(latest-1)]+'</span>'
      +'<span class="small">'+(bandKey
        ? 'service families inside '+(bandIsShared?'the parts shared across bands':BANDLAB[drillBand])
          +', ranked by the current period'
        : (drFam
          ? 'service families inside '+FAMLAB[drFam]+', ranked by the current period'
          : 'all service families for this selection, ranked by the current period — pick a vehicle '
            +'type above to narrow it, or click a bar to open the part numbers inside it'))+'</span>';
    var nDrill='Each bar is billed euro in one service family. Both bars are twelve-month periods, '
      +'so the difference between them is the move. ';
    nDrill += bandKey
      ? 'Only part numbers that fit '+(bandIsShared?'more than one band':BANDLAB[drillBand])
        +' are counted at this level.'
      : drFam ? 'Only parts that fit '+FAMLAB[drFam]+' are counted at this level.'
      : 'Pooled part numbers are included here, because this level sums the whole selection. Click a '
        +'bar to see the part numbers inside it with the vehicle type each one fits.';
    document.getElementById('n_drill').innerHTML=nDrill;
    tpn.innerHTML='';
    return;
  }

  /* level 2 -> level 3: the part numbers inside the clicked service family */
  var pnBilling=pnAgg(A);
  var fam=drFam;
  var detail=[];
  D.pns.forEach(function(p,i){
    if(p.cat!==drillCat) return;
    if(fam && p.fam!==fam) return;
    /* inside a tonnage band, only the part numbers that fit that band belong on this level */
    if(bandKey){
      var fits=bandIsShared?p.zfits.indexOf('n_shared_bands')>=0
                           :p.zfits.indexOf(bandKey)>=0;
      if(!fits) return;
    }
    var o=pnBilling[i]; if(!o) return;
    var now=o[latest], was=o[latest-1];
    if(!now && !was) return;
    detail.push({pn:p.pn,cat:p.cat,fam:p.fam,fits:p.fits,conf:p.conf,model:p.model,src:p.src,
      zfits:p.zfits,zstatus:p.zstatus,zseries:p.zseries,zreg:p.zreg,
      eur:now?now.eur:0,units:now?now.units:0,
      eurPrev:was?was.eur:null,unitsPrev:was?was.units:null,
      eurPct:(was&&was.eur>0&&now)?(now.eur/was.eur-1):null,
      unitsPct:(was&&was.units>0&&now)?(now.units/was.units-1):null});
  });
  detail.sort(function(a,b){return b.eur-a.eur;});
  var shown=detail.slice(0,60);
  var sum=detail.reduce(function(s,r){return s+r.eur;},0);
  var sumPrev=detail.reduce(function(s,r){return s+(r.eurPrev||0);},0);

  var rowsBar=shown.slice(0,14);
  box.style.height=Math.max(280,60+rowsBar.length*30)+'px';
  mk('c_drill',{type:'bar',
    data:{labels:rowsBar.map(function(r){return r.pn;}),datasets:[
      {label:C.spelled[String(latest)],data:rowsBar.map(function(r){return r.eur;}),backgroundColor:NAVY,borderRadius:3},
      {label:C.spelled[String(latest-1)],data:rowsBar.map(function(r){return r.eurPrev||0;}),backgroundColor:'#d9d3c7',borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{afterBody:function(items){
            var r=rowsBar[items[0].dataIndex];
            return [r.fits.length>1?'fits more than one vehicle type: '+r.fits.map(function(k){return FAMLAB[k];}).join(', ')
                                   :'fits '+FAMLAB[r.fam],
              'units: '+num(r.units)+' this period against '+(r.unitsPrev===null?'n/a':num(r.unitsPrev)),
              r.eurPct===null?'no billing a year earlier':signpct(r.eurPct)+' in euro against the year before',
              'confidence: '+r.conf];}}}},
      scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
              y:{grid:{display:false}}}}});
  var d2=charts['c_drill'];
  d2.options.onClick=function(evt,els){ if(!els.length) return;
    var r=rowsBar[els[0].index]; jumpToPn(r.pn); };
  d2.options.onHover=function(evt,els){ evt.native.target.style.cursor=els.length?'pointer':'default'; };
  d2.update();

  document.getElementById('k_drill').innerHTML=
    '<span><i style="background:'+NAVY+'"></i>'+C.spelled[String(latest)]+'</span>'
    +'<span><i style="background:#d9d3c7"></i>'+C.spelled[String(latest-1)]+'</span>'
    +'<span class="small">the highest-value part numbers in '
    +CATLAB[drillCat]+(fam?' for '+FAMLAB[fam]:'')+'; the table below holds all '
    +detail.length+'</span>';
  document.getElementById('n_drill').innerHTML='<b>'+detail.length+' part numbers</b> in this service '
    +'family'+(fam?' for '+FAMLAB[fam]:'')+', '+eur(sum)+' this period against '+eur(sumPrev)
    +' a year earlier ('+(sumPrev>0?signpct(sum/sumPrev-1):'n/a')+'). '
    +(familyFleet(fam)?'Fleet base: '+num(familyFleet(fam))+' vehicles in service.':'');

  var cols=[['Part number',''],['Vehicle type it fits',''],['Weight band it fits',''],
    ['Fits',''],
    [C.spelled[String(latest)]+' EUR','n'],[C.spelled[String(latest-1)]+' EUR','n'],
    ['Change EUR','n'],[C.spelled[String(latest)]+' units','n'],
    [C.spelled[String(latest-1)]+' units','n'],['Change units','n'],['Confidence','']];
  tpn.innerHTML='<table><thead><tr>'+cols.map(function(c){
      return '<th class="'+c[1]+'">'+c[0]+'</th>';}).join('')+'</tr></thead><tbody>'
    +shown.map(function(r){
      return '<tr data-pn="'+r.pn+'"><td><b>'+r.pn+'</b></td>'
        +'<td>'+(r.fits.length>1?r.fits.map(function(k){return FAMLAB[k];}).join(' + ')
                             :FAMLAB[r.fam])+'</td>'
        +'<td class="small">'+(r.zfits&&r.zfits.length
            ? r.zfits.map(function(z){return ZSHORT[z];}).join(' + ')
            :(r.zstatus==='series_unresolved'?'series not resolved'
              :(r.zstatus==='no_series_found'?'no series on the part number'
                :(r.zseries||'not in this lane'))))+'</td>'
        +'<td class="small">'+(r.model||'no vehicle string')+'</td>'
        +'<td class="n">'+eur(r.eur)+'</td>'
        +'<td class="n">'+(r.eurPrev===null?'n/a':eur(r.eurPrev))+'</td>'
        +'<td class="n '+cls(r.eurPct)+'">'+signpct(r.eurPct)+'</td>'
        +'<td class="n">'+num(r.units)+'</td>'
        +'<td class="n">'+(r.unitsPrev===null?'n/a':num(r.unitsPrev))+'</td>'
        +'<td class="n '+cls(r.unitsPct)+'">'+signpct(r.unitsPct)+'</td>'
        +'<td>'+r.conf+'</td></tr>';}).join('')
    +'</tbody></table>'
    +(detail.length>shown.length?'<p class="small" style="margin-top:8px">Showing the top '
      +shown.length+' of '+detail.length+' by the current period. '
      :'<p class="small" style="margin-top:8px">Every part number in this service family is listed. ')
    +(bandKey
      ? '<b>Filtered to the weight band '+(bandIsShared?'shared across bands':BANDLAB[drillBand])
        +'.</b> The "weight band it fits" column names every band each of these part numbers fits. '
        +'A part that shows more than one band sits inside each of those bands, which is why the '
        +'band bars overlap. '
      : (fam==='shared_across_families'
        ? '<b>These are the pooled part numbers.</b> Each one fits more than one vehicle type, so its '
          +'euro stays here rather than being spread across the types it fits. The column "Fits" names '
          +'the types. '
        : fam
          ? '<b>These part numbers fit '+FAMLAB[fam]+' and nothing else</b>, so each one\'s euro '
            +'belongs to that type alone. '
          : 'The table mixes pooled part numbers with single-type ones — pick a vehicle type above to '
            +'separate them. '))
    +'Fleet base for this level: '
    +(bandKey
      ? (bandFleet(drillBand&&BANDS.indexOf(drillBand)>=0?drillBand:null).n===null
          ? 'no source splits this band out of the N-series fleet'
          : num(bandFleet(drillBand).n)+' vehicles in service ('+bandFleet(drillBand).label+')')
      : num(fam?familyFleet(fam):0)+' vehicles in service'
        +(fam?'' : ' (no single fleet applies to the pooled rows)'))
    +'.</p>';

  /* a part number you clicked in the chart scrolls into view in the table */
  function jumpToPn(pn){
    var el=tpn.querySelector('tr[data-pn="'+pn+'"]');
    if(el){ el.scrollIntoView({block:'center',behavior:'smooth'});
      el.classList.add('sel'); setTimeout(function(){el.classList.remove('sel');},2200); }
  }
  tpn.querySelectorAll('tr[data-pn]').forEach(function(tr){
    tr.addEventListener('click',function(){ tr.classList.add('sel');
      setTimeout(function(){tr.classList.remove('sel');},1600); });});
}

/* The before/after section reads the shipped page's own payload. It is the honest answer to "what
   did the bug change", and it is the one chart on this page that is not about the current state. */
function renderBefore(A,latest){
  var B=D.before;
  if(!B||!B.available){
    document.getElementById('n_before').innerHTML='The shipped page could not be read, so no '
      +'before/after comparison can be shown. '+(B&&B.why?B.why:'')+'';
    return;
  }
  var per=String(latest);
  var keys=D.families.map(function(f){return f.key;});
  /* This section is a statement about the rebuild, not about the reader's selection, so it is always
     the whole network on both sides. The shipped page reported the network, and comparing that
     against one selected market would read as a collapse that did not happen. D.trend carries the
     network totals cut from the current data on the same 18 markets and the same service-part scope
     the shipped page used. */
  var nowV=keys.map(function(k){ return ((D.trend.CY[k]||{}).eur||{})[per]||0; });
  var nowU=keys.map(function(k){ return ((D.trend.CY[k]||{}).units||{})[per]||0; });
  var wasV=keys.map(function(k){ return (B.eur[k]||{})[per]||0; });
  var wasU=keys.map(function(k){ return (B.units[k]||{})[per]||0; });
  mk('c_before',{type:'bar',
    data:{labels:keys.map(function(k){return FAMLAB[k];}),datasets:[
      {label:'As shipped',data:wasV,backgroundColor:'#d9d3c7',borderRadius:3},
      {label:'Corrected',data:nowV,backgroundColor:keys.map(function(k){return FAMCOL[k];}),borderRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',
      plugins:{legend:{display:true,position:'top',labels:{boxWidth:11,padding:12}},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{afterBody:function(items){
            var i=items[0].dataIndex;
            return ['as shipped: '+eur(wasV[i])+' on '+num(wasU[i])+' units',
              'corrected: '+eur(nowV[i])+' on '+num(nowU[i])+' units',
              'move: '+(nowV[i]-wasV[i]>=0?'+':'')+eur(nowV[i]-wasV[i]),
              'Read the euro. A percentage on the heavy line is large because the fleet is small.'];}}}},
      scales:{x:{grid:{color:RULE},beginAtZero:true,ticks:{callback:function(v){return eurm(v);}}},
              y:{grid:{display:false}}}}});
  document.getElementById('k_before').innerHTML=
    '<span><i style="background:#d9d3c7"></i>as shipped ('+B.source+')</span>'
    +'<span><i style="background:'+NAVY+'"></i>corrected</span>'
    +'<span class="small">'+D.clocks.CY.spelled[per]+', service parts only, the whole network — the '
    +'same scope the shipped page reported</span>';
  var hI=keys.indexOf('heavy_truck');
  function sumRows(arr){ return arr.reduce(function(s,v){return s+v;},0); }
  var namedIdx=D.namedFamilies.map(function(k){return keys.indexOf(k);});
  var namedNow=sumRows(namedIdx.map(function(i){return nowV[i];}));
  var namedWas=sumRows(namedIdx.map(function(i){return wasV[i];}));
  var namedNowU=sumRows(namedIdx.map(function(i){return nowU[i];}));
  var namedWasU=sumRows(namedIdx.map(function(i){return wasU[i];}));
  document.getElementById('n_before').innerHTML='The grey bars are the numbers the shipped page '
    +'carried; the coloured bars are the same twelve months and the same network after the decode '
    +'universe was fixed. Across the three named vehicle types the network went from '
    +eur(namedWas)+' ('+num(namedWasU)+' units) to '+eur(namedNow)+' ('+num(namedNowU)+' units); '
    +'heavy truck alone went from '+eur(wasV[hI])+' to '+eur(nowV[hI])+'. '
    +'Nothing was created. Every euro already existed in the billing and had a home in the '
    +'cross-reference; it was dropped between two build steps, which is why it appeared on neither.';
  htmlTable('t_before',
    ['Vehicle type','As shipped EUR','As shipped units','Corrected EUR','Corrected units',
     'Move EUR','Move %'],
    keys.map(function(k,i){
      var mv=nowV[i]-wasV[i];
      return ['<b>'+FAMLAB[k]+'</b>','<span class="small">'+eur(wasV[i])+'</span>',
        '<span class="small">'+num(wasU[i])+'</span>',eur(nowV[i]),num(nowU[i]),
        '<span class="'+cls(wasV[i]>0?mv/wasV[i]:null)+'">'+(mv>=0?'+':'')+eur(mv)+'</span>',
        wasV[i]>0?'<span class="'+cls(mv/wasV[i])+'">'+signpct(mv/wasV[i])+'</span>':'<span class="small">new</span>'];
    }),
    ['','n','n','n','n','n','n']);
}

function renderMix(A,latest){
  var rows=D.families.map(function(f){
    var o=(A.byFam[f.key]||{})[latest];
    return {key:f.key,label:f.label,color:f.color,v:o?o.eur:0,
            units:o?o.units:0};
  }).filter(function(r){return r.v>0;});
  var tot=rows.reduce(function(s,r){return s+r.v;},0);
  if(!rows.length){
    mk('c_mix',{type:'doughnut',data:{labels:['nothing billed in this period'],
      datasets:[{data:[1],backgroundColor:['#ddd7cb'],borderWidth:0}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
        plugins:{legend:{display:false},tooltip:{enabled:false}}}});
    document.getElementById('k_mix').innerHTML='<span>no billing in this period for this selection</span>';
    return;
  }
  mk('c_mix',{type:'doughnut',
    data:{labels:rows.map(function(r){return r.label;}),datasets:[{data:rows.map(function(r){return r.v;}),
      backgroundColor:rows.map(function(r){return r.color;}),borderColor:'#fff',borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
      plugins:{legend:{display:false},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{label:function(c){
            var r=rows[c.dataIndex];
            return [c.label+': '+eur(r.v)+' ('+pct(r.v/tot)+' of the selection)',
              num(r.units)+' units',
              (D.namedFamilies.indexOf(r.key)>=0
                ? 'Fleet: '+num(familyFleet(r.key))+' vehicles in service'
                : 'Pooled or with no vehicle named — no single fleet applies')];}}}}}});
  document.getElementById('k_mix').innerHTML=rows.map(function(r){
    return '<span><i style="background:'+r.color+'"></i>'+r.label+' — '+pct(r.v/tot)
      +' ('+eur(r.v)+')'
      +(D.namedFamilies.indexOf(r.key)>=0?' on '+num(familyFleet(r.key))+' vehicles in service'
        :' — pooled across types, no single fleet applies')
      +'</span>';}).join('');
}

function renderFleet(A){
  var latest=D.clocks[clock].latestComplete;
  /* the ring reads the denominator in force for the period being shown, so it cannot disagree
     with the rate the rest of the page divides by */
  var fl=[['n_series_truck','n_series'],['heavy_truck','heavy'],['light_vehicle','light']]
    .map(function(x){
      var t=0; A.markets.forEach(function(m){ t+=((D.fleet[m]||{})[x[1]]||0); });
      var live=fleetAt(x[0],latest,fleetMode);
      return {key:x[0],label:FAMLAB[x[0]],v:t,color:FAMCOL[x[0]],
              live:(live.n===null?null:live.n)};})
    .filter(function(r){return r.v>0;});
  var tot=fl.reduce(function(s,r){return s+r.v;},0);
  mk('c_fleet',{type:'doughnut',
    data:{labels:fl.map(function(r){return r.label;}),datasets:[{data:fl.map(function(r){return r.v;}),
      backgroundColor:fl.map(function(r){return r.color;}),borderColor:'#fff',borderWidth:2}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'56%',
      plugins:{legend:{display:false},
        tooltip:{backgroundColor:NAVY,titleColor:'#ffd9c4',bodyColor:PAPER,padding:10,
          callbacks:{label:function(c){ var r=fl[c.dataIndex];
            return [num(r.v)+' vehicles ('+pct(r.v/tot)+' of the fleet)',
              'the denominator in force for this period: '
                +(r.live===null?'no count for this type':num(r.live)+' vehicles'),
              'Parts billed on this type: '+eurm(((A.byFam[r.key]||{})[latest]||{}).eur)];}}}}}});
  document.getElementById('k_fleet').innerHTML=fl.map(function(r){
    return '<span><i style="background:'+r.color+'"></i>'+r.label+' — '+num(r.v)
      +', billed '+eurm(((A.byFam[r.key]||{})[latest]||{}).eur)
      +' = '+eur(((A.byFam[r.key]||{})[latest]||{}).eur||0)
      +' over '+num(r.v)+' vehicles</span>';}).join('');
  document.getElementById('n_fleet').innerHTML='The fleet is the denominator every euro above is '
    +'measured against, and this ring is the split for the latest complete period, divided by '
    +'<b>'+fleetModeLabel()+'</b>. Pooled part numbers fit more than one type, so they are not '
    +'assigned to one slice here. The per-period count behind each slice is '+num(fl[0]?fl[0].live:null)
    +' for the first type and is printed on every bar of the normalised chart above.';
}

function renderFamTable(A,latest){
  var C=D.clocks[clock];
  var months=C.months[String(latest)];
  var rows=D.families.map(function(f){
    var pr=pairFor(A.byFam[f.key]||{},latest);
    var fb=familyFleetBoth(f.key,latest);
    var flat=fb.s, own=fb.y;
    var fNow=fleetAt(f.key,latest,fleetMode);
    return {key:f.key,label:f.label,
      fleet:(D.namedFamilies.indexOf(f.key)>=0?(fNow.n||0):null),
      fleetOwn:own, fleetFlat:flat,
      eur:pr?pr.eur:0, units:pr?pr.units:0, eurPrev:pr?pr.eurPrev:null,
      unitsPrev:pr?pr.unitsPrev:null, eurPct:pr?pr.eurPct:null, unitsPct:pr?pr.unitsPct:null,
      fits: f.key==='shared_across_families'
        ? (A.byFam[f.key]?'pooled across types':'') : (f.key==='no_vehicle_reference'?'no vehicle named':'')};
  });
  var tot=rows.reduce(function(s,r){return s+r.eur;},0);
  htmlTable('t_fam',
    ['Vehicle type','Vehicles on that period\u2019s own fleet',
     'Vehicles on the single 2025 estimate',
     'EUR per vehicle, own fleet','EUR per vehicle, 2025 estimate',
     'Billed EUR '+C.short+latest,'Billed EUR '+C.short+(latest-1),'Change EUR','Change %',
     'Units '+C.short+latest,'Units '+C.short+(latest-1),'Change units','Share'],
    rows.map(function(r){
      var perOwn=(r.fleetOwn&&r.fleetOwn>0)?(r.eur/r.fleetOwn):null;
      var perFlat=(r.fleetFlat&&r.fleetFlat>0)?(r.eur/r.fleetFlat):null;
      return ['<b>'+r.label+'</b>'+(r.fits?' <span class="small">('+r.fits+')</span>':''),
        r.key==='no_vehicle_reference'?'<span class="small">no single fleet applies</span>'
          :(r.fleetOwn===null?'<span class="warn">no count for this period</span>':num(r.fleetOwn)),
        r.key==='no_vehicle_reference'?'<span class="small">no single fleet applies</span>'
          :(r.fleetFlat===null?'n/a':num(r.fleetFlat)),
        perOwn===null?'n/a':eur(perOwn),
        perFlat===null?'n/a':eur(perFlat),
        eur(r.eur), r.eurPrev===null?'n/a':eur(r.eurPrev),
        r.eurPrev===null?'n/a':'<span class="'+cls(r.eurPct)+'">'+eur(r.eur-(r.eurPrev||0))+'</span>',
        r.eurPrev===null?'n/a':'<span class="'+cls(r.eurPct)+'">'+signpct(r.eurPct)+'</span>',
        num(r.units), r.unitsPrev===null?'n/a':num(r.unitsPrev),
        r.unitsPrev===null?'n/a':'<span class="'+cls(r.unitsPct)+'">'+signpct(r.unitsPct)+'</span>',
        tot>0?pct(r.eur/tot):'n/a'];
    }),
    ['','n','n','n','n','n','n','n','n','n','n','n','n']);
  var ft=document.getElementById('t_fam');
  ft.insertAdjacentHTML('afterbegin','<h3 style="font-size:15px">This period against the same period '
    +'a year earlier, with both fleet denominators beside every euro</h3>'
    +'<p class="small">'+C.spelled[String(latest)]+' holds '+months+' month'
    +(months===1?'':'s')+' of billing. Both rate columns are shown on purpose: the pair is the '
    +'answer, and the column that divides by one flat estimate is arithmetically the euro move. '
    +'In force on this page: <b>'+fleetModeLabel()+'</b>.</p>');
}

function renderLimits(A,latest){
  var C=D.clocks[clock];
  var lim=[];
  lim.push('<b>One year is not a full year.</b> '
    +C.spelled[String(latest)]+' is a complete twelve-month period. A period holding fewer months is '
    +'shown on the small multiples but never compared as though it were a full year; the number of '
    +'months is printed on its key.');
  lim.push('<b>'+eur(D.totals.serviceBook2025-D.totals.placeable2025)+' of the 2025 service book '
    +'(2025 total '+eur(D.totals.serviceBook2025)+') is not placed in a single vehicle type.</b> '
    +eur(D.totals.serviceBook2025-D.totals.placeable2025)+' sits in the pooled value where a part '
    +'fits more than one type, and in "no vehicle reference" where no source names a vehicle. It is '
    +'not missing and it is not spread — both are reported, and the pooled part numbers are listed '
    +'when you open that bar.');
  var hs=D.familyStats.heavy_truck;
  lim.push('<b>Heavy truck rests on a small fleet.</b> '
    +'Heavy truck holds '+num(hs.pns)+' part numbers billing '+eur(hs.eur2025)+' in 2025 on '
    +num(hs.units2025)+' units, with a separate fleet base of '+num(hs.fleet)+' vehicles across the '
    +'whole network. Read a percentage there with the euro beside it.');
  lim.push('<b>A service type can look empty for the heavy truck family even when it is not.</b> '
    +'A part number is placed in a type only where a source names a vehicle for it, and a part that '
    +'fits more than one type is pooled rather than split. The euro on a heavy-truck bar is '
    +'therefore the part numbers that name the heavy truck and nothing else; the rest of that '
    +'service type sits in the pooled value beside it. The heavy-truck family itself holds 164 part '
    +'numbers billing EUR 175K in 2025, so an empty bar is a placement limit, not zero demand.');
  lim.push('<b>A 3.5 t versus 7.5 t split inside the N-series is not attempted.</b> 50 of the 120 '
    +'model codes in the weight table are unresolved, and the unresolved ones include the codes that '
    +'separate the two, so the N-series is reported as one type.');
  lim.push('<b>Two service-interval schedules run through this network.</b> ITUK runs the schedule '
    +'agreed for that market and every other market runs the internal one. They are shown side by '
    +'side and are never averaged, because they answer different questions about the same fleet.');
  lim.push('<b>The fleet now has a year axis, and two defects in it are carried rather than '
    +'hidden.</b> Every period divides by its own fleet, read from the vehicle-in-service '
    +'workbook\u2019s own rows: 1990 to '+D.perYear.actualThrough+' are actuals, '
    +D.perYear.estimateYear+' is an estimate and '+D.perYear.forecastYears+' are forecast. '
    +D.perYear.defects.ldLabel+' '+D.perYear.defects.israelLow+' '+D.perYear.defects.forecast);
  lim.push('<b>A period with no fleet count is shown as a gap, not filled.</b> '
    +(D.perYear.gaps.length
      ? D.perYear.gaps.map(function(g){ return '<b>'+g.market+'</b> '+g.years+' ('+g.why+')'; })
          .join('; ')+'. Those market-periods carry no rate in the table above, rather than another '
        +'period\u2019s fleet.'
      : 'Inside the periods this page draws, every market in scope has a count for every period, so '
        +'nothing on the page is filled from a neighbouring year. Markets with no row in the '
        +'workbook at all are outside the 18-market scope of this page.'));
  (D.notAttempted||[]).slice(0,3).forEach(function(s){ lim.push('<b>Not attempted:</b> '+s); });
  htmlTable('t_limits',['What cannot be shown, and why'],lim.map(function(s){return [s];}),['']);
}

function htmlTable(id,heads,rows,aligns){
  document.getElementById(id).innerHTML='<table><thead><tr>'
    +heads.map(function(h,i){return '<th class="'+(aligns[i]||'')+'">'+h+'</th>';}).join('')
    +'</tr></thead><tbody>'+rows.map(function(r){
      return '<tr>'+r.map(function(c,i){
        return '<td class="'+(aligns[i]||'')+'">'+c+'</td>';}).join('')+'</tr>';}).join('')
    +'</tbody></table>';
}

/* ── controls ───────────────────────────────────────────────────────────────────────────── */
custSel.addEventListener('change',function(){
  selCust={};
  Array.prototype.slice.call(custSel.selectedOptions).forEach(function(o){ selCust[o.value]=true; });
  if(!chosen().length){ selCust[D.markets[0]]=true; }
  render();});
famSel.addEventListener('change',function(){ selFam=famSel.value; drillCat=null; drillBand=null; render();});
clkSel.addEventListener('change',function(){ clock=clkSel.value; render();});
  if(fleetSel) fleetSel.addEventListener('change',function(){ fleetMode=fleetSel.value; render();});
/* the denominator note a reader sees, written from the live state rather than typed */
if(document.getElementById('fleetNote')){
  document.getElementById('fleetNote').innerHTML='';
}
document.getElementById('fleetNote').setAttribute('data-tip',
  'A rate needs a denominator. The model\u2019s own fleet split has one vintage, an estimate labelled '
  +'2025E, and no year column; the spend-per-vehicle file has a count per year but no vehicle type. '
  +'Whichever is in force is named on the chart.');
if(segMetric) segMetric.addEventListener('click',function(e){
  var b=e.target.closest?e.target.closest('button[data-m]'):null;
  if(!b) return;
  metric=b.getAttribute('data-m'); render();});
document.getElementById('btnAll').addEventListener('click',function(){
  selCust={}; D.markets.forEach(function(m){selCust[m]=true;}); syncCust(); render();});
document.getElementById('btnNone').addEventListener('click',function(){
  selCust={}; selCust[D.markets[0]]=true; syncCust(); render();});
document.getElementById('btnItuk').addEventListener('click',function(){
  selCust={ITUK:true}; if(D.markets.indexOf('ITUK')<0){selCust={}; selCust[D.markets[0]]=true;}
  syncCust(); render();});
function syncCust(){
  Array.prototype.slice.call(custSel.options).forEach(function(o){ o.selected=!!selCust[o.value]; });}

document.getElementById('foot').innerHTML='<b>Sources, all read at build time, snapshot '
  +D.snapshot+':</b> the published service-part capture model; the service-part dimension and its '
  +'capture supplement; the vehicle-family banding table, which reads the EPC decode and the '
  +'genuine/aftermarket cross-reference together; the billing; the fleet split by vehicle class; and '
  +'the per-market interval schedule. '
  +'<b>Reconciliation:</b> every euro on this page is the published service-part book for the '
  +'selection, and the build refuses to write if the 2025 figure does not tie to it. '
  +'<b>Vehicle type resolution:</b> '+D.resolution.resolved_single_family+' part numbers resolve to '
  +'one vehicle type, '+D.resolution.pooled_shared+' fit more than one and are pooled, and '
  +D.resolution.no_vehicle_reference+' have no vehicle named by either source — '
  +D.resolution.both_sources_speak.of_which_they_disagree+' disagreements between the two sources.';

syncCust();
render();

/* QA hook. Cursor-side only: it lets the ship gate drive the same click path a reader's mouse takes
   (Chart.js routes a canvas click through the chart's onClick), so drill-through is verified by
   walking it, not by reading the code. It writes nothing. */
window.__deepTest={
  state:function(){ return {selCust:Object.keys(selCust), selFam:selFam, clock:clock,
    metric:metric, fleetMode:fleetMode,
    drillFam:famFilter(), drillCat:drillCat, drillBand:drillBand,
    bread:document.getElementById('bread').textContent.replace(/\s+/g,' ').trim(),
    pnRows:document.querySelectorAll('#t_pn tbody tr').length,
    drillInk:window.__deepTest.ink('c_drill'),
    bandInk:window.__deepTest.ink('c_band'),
    funnelInk:window.__deepTest.ink('c_funnel'),
    normInk:window.__deepTest.ink('c_norm'),
    targetInk:window.__deepTest.ink('c_target'),
    drillLabels:window.__deepTest.labels('c_drill'),
    bandLabels:window.__deepTest.labels('c_band'),
    funnelLabels:window.__deepTest.labels('c_funnel'),
    metricChips:(function(){ var out=[];
      Array.prototype.slice.call(document.querySelectorAll('#segMetric button')).forEach(function(b){
        out.push(b.getAttribute('data-m')+(b.classList.contains('on')?':on':':off')); });
      return out;})(),
    normRows:document.querySelectorAll('#t_norm tbody tr').length,
    industryRows:document.querySelectorAll('#t_industry tbody tr').length,
    bandCards:document.querySelectorAll('#band_cards .bandcard').length,
    bandSplitRows:document.querySelectorAll('#t_bandsplit tbody tr').length,
    bandEvRows:document.querySelectorAll('#t_bandev tbody tr').length,
    canvasIds:Array.prototype.map.call(document.querySelectorAll('canvas'),function(c){return c.id;})};},
  /* the measure the page is actually plotting, read back from the chart object rather than from
     the state variable, so a switch that fails to reach the charts is caught */
  chartMetric:function(){
    var ch=charts['c_funnel']; if(!ch) return null;
    var lab=(ch.data.datasets[0].label||'');
    return {label:lab, firstValue:ch.data.datasets[0].data[0],
            prevValue:ch.data.datasets[1].data[0]};},
  /* one market's arithmetic, spelled out so a reader can check it by hand. Pass a vehicle type to
     cut it to one family; leave it out for the whole selection of that market. */
  rateProof:function(market,famKey){
    market=market||Object.keys(selCust)[0];
    var out={market:market, family:famKey||'all vehicle types', rows:[]};
    var mi=D.markets.indexOf(market);
    var fi=famKey?FAMK.indexOf(famKey):-1;
    D.clocks[clock].periods.filter(function(p){
      return D.clocks[clock].months[String(p)]>=12; }).forEach(function(p){
      var eur=0, units=0;
      for(var i=0;i<D.rec[clock].length;i++){
        var r=D.rec[clock][i];
        if(r[0]!==mi||r[3]!==p) continue;
        if(fi>=0&&r[2]!==fi) continue;
        eur+=r[4]; units+=r[5];
      }
      var keep=selCust; selCust={}; selCust[market]=true;
      var fl=fleetAt(famKey||'all',p,'yearly'), flSplit=fleetAt(famKey||'all',p,'split');
      var flUsed=fleetAt(famKey||'all',p,fleetMode);
      selCust=keep;
      out.rows.push({period:p, eur:eur, units:units,
        fleetSplit:flSplit.n, fleetYear:fl.n, fleetUsed:flUsed.n,
        rate:(flUsed.n&&flUsed.n>0)?(eur/flUsed.n):null,
        rateSplit:(flSplit.n&&flSplit.n>0)?(eur/flSplit.n):null,
        rateYear:(fl.n&&fl.n>0)?(eur/fl.n):null,
        modeUsed:flUsed.mode, fleetVintage:flUsed.vintage, fleetSource:flUsed.source});
    });
    return out;},
  /* the measure the KPI tiles are actually printing, read back from the DOM */
  kpiText:function(){
    var out=[];
    Array.prototype.slice.call(document.querySelectorAll('#kpis .kpi')).forEach(function(d){
      out.push({v:(d.querySelector('.v')||{}).textContent, l:(d.querySelector('.l')||{}).textContent,
                s:(d.querySelector('.s')||{}).textContent});});
    return out;},
  /* the denominator notes a reader can see, read back from the DOM */
  denominatorText:function(){
    return {metricNote:document.getElementById('metricNote').textContent.replace(/\s+/g,' ').trim(),
      fleetNote:document.getElementById('fleetNote').textContent.replace(/\s+/g,' ').trim(),
      norm:document.getElementById('n_norm').textContent.replace(/\s+/g,' ').trim(),
      normHead:(document.querySelector('#t_norm h3')||{}).textContent,
      target:(document.getElementById('n_target')||{textContent:''}).textContent.replace(/\s+/g,' ').trim(),
      industry:(document.getElementById('t_industry')||{textContent:''}).textContent.replace(/\s+/g,' ').trim().slice(0,600)};},
  /* the written key of every panel that carries a chart, read back from the DOM */
  keys:function(){
    var out=[];
    Array.prototype.slice.call(document.querySelectorAll('.card')).forEach(function(p){
      var cv=p.querySelectorAll('canvas'); if(cv.length!==1) return;
      var k=p.querySelector('.key');
      out.push({canvas:cv[0].id,
        words:k?k.textContent.replace(/\s+/g,' ').trim().split(' ').filter(function(w){return w.length>2;}).length:0,
        text:k?k.textContent.replace(/\s+/g,' ').trim().slice(0,200):null});});
    return out;},
  /* the chart object itself, for tests that must read the plotted data rather than the state */
  chart:function(id){ return charts[id]||null; },
  /* the column headings of a table, read from the DOM so a test can prove a column exists */
  tableHeads:function(id){ var t=document.getElementById(id);
    if(!t) return null;
    var th=t.querySelectorAll('thead th');
    return Array.prototype.map.call(th,function(x){return x.textContent.replace(/\s+/g,' ').trim();});},
  /* the page's own view of the per-period fleet, so a claim can be checked against the payload
     rather than against the page that made it */
  payloadCheck:function(){
    var out={years:D.perYear.years.length,
      firstYear:D.perYear.years[0], lastYear:D.perYear.years[D.perYear.years.length-1],
      markets:Object.keys(D.perYear.byMarket).length,
      reconcileAgree:0, reconcileTotal:0, gaps:D.perYear.gaps.length,
      defaultDenominator:fleetMode};
    Object.keys(D.perYear.reconcile).forEach(function(k){
      out.reconcileTotal++; if(D.perYear.reconcile[k].agrees) out.reconcileAgree++;});
    return out;},
  clickBar:function(id,index){
    var ch=charts[id]; if(!ch||!ch.options.onClick) return false;
    ch.options.onClick({}, [{index:index, datasetIndex:0, element:null}]);
    return true;},
  /* the funnel's bar order changes when a vehicle filter is on, so the test reads the labels back */
  labels:function(id){ var ch=charts[id];
    return ch? (ch.data.labels||[]).map(function(l){return String(l);}) : null;},
  set:function(o){
    if(o.cust){ selCust={}; o.cust.forEach(function(m){selCust[m]=true;}); syncCust(); }
    if(o.clock){ clock=o.clock; }
    if(o.fam){ selFam=o.fam; drillCat=null; drillBand=null; }
    if(o.metric){ metric=o.metric; }
    if(o.fleet){ fleetMode=o.fleet; }
    if(o.band!==undefined){ drillBand=o.band; drillCat=null; }
    if(o.reset){ drillCat=null; drillBand=null; }
    render();
    return window.__deepTest.state();},
  chooseBand:function(band){ selFam='n_series_truck'; drillBand=band; drillCat=null;
    if(famSel) famSel.value='n_series_truck';
    render(); return window.__deepTest.state(); },
  bandTotals:function(){
    return window.__deepTest.zonePanel(); },
  zonePanel:function(){
    var A=agg(); var Z=zoneAgg(A); var C=D.clocks[clock]; var latest=C.latestComplete;
    var o={clock:clock, latest:latest, markets:Object.keys(selCust), zones:{}};
    D.zoneIds.forEach(function(zid){ var r=zRow(Z,zid,latest);
      o.zones[zid]={eur:r.eur, units:r.units, eurPrev:r.eurPrev, unitsPrev:r.unitsPrev,
                    eurPct:r.eurPct, unitsPct:r.unitsPct, membership:r.membership,
                    sums:r.sums, band:r.band};});
    o.bands={};
    BANDS.forEach(function(b){ var t=bandTotal(Z,b,latest);
      o.bands[b]={eur:t.eur, units:t.units, eurPrev:t.eurPrev, unitsPrev:t.unitsPrev,
                  eurPct:t.eurPct, unitsPct:t.unitsPct, singleEur:t.singleEur,
                  sharedEur:t.sharedEur,
                  sharedPct:t.eur>0?(t.sharedEur/t.eur):0};});
    return o; },
  pooledIndex:function(){
    /* which bar of the drill chart is the pooled value, read from the live labels */
        var l=window.__deepTest.labels('c_drill')||[];
    for(var i=0;i<l.length;i++){
      if(String(l[i]).toLowerCase().indexOf('more than one family')>=0) return i; }
    return -1;},
  catLabels:function(){ return window.__deepTest.labels('c_drill');},
  ink:function(id){ var c=document.getElementById(id); if(!c) return null;
    var d=c.getContext('2d').getImageData(0,0,c.width,c.height).data, nw=0, s=0;
    for(var i=0;i<d.length;i+=4){ s++; if(d[i+3]>8 && !(d[i]>250&&d[i+1]>250&&d[i+2]>250)) nw++; }
    return {sampled:s, nonWhite:nw, pct:+(100*nw/s).toFixed(2)};},
  /* the pooled value as a separate vehicle-type option, so it can be walked to by name */
  choosePooled:function(){ selFam='shared_across_families'; drillCat=null; render(); }
};
}catch(err){
  var b=document.getElementById('jserr');
  if(b){ b.style.display='block';
    b.innerHTML='<div class="note red"><b>The page did not finish drawing.</b> A script error stopped '
      +'it. Detail: '+String(err && err.message ? err.message : err)+'</div>'; }
  var f=document.getElementById('foot');
  if(f) f.innerHTML='<b>Incomplete.</b> The page script failed: '
    +String(err && err.message ? err.message : err);
}
})();
