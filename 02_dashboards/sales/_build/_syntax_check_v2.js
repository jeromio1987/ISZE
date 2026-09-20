
window.addEventListener('error',function(e){
  var b=document.getElementById('errbar');
  if(b){ b.style.display='block';
    b.innerHTML='<b>The page did not finish drawing.</b> A script error stopped it, so some panels '
      +'below are empty. That is a defect in the page, not a data problem. Detail: '
      +String(e.message)+' at line '+String(e.lineno)+'.'; }
});
(function(){
"use strict";
try{
var D = JSON.parse(document.getElementById('pmfe2-data').textContent);
var NAVY='#15233c', TERRA='#c0552d', PAPER='#f7f4ee', MUTED='#6b6459', LINE='#d9d3c8',
    BAND='#eef3f9', GOOD='#1e6b4f', AMBER='#a8721f', GREY='#8a8275', POOLED='#8a6b2f',
    UNC='#b9ae9d', NOTCMP='#ddd7cb', SHAREDDENOM='#cfc7b8', INK='#22262e';
var DEC_COLORS={vol:NAVY, price:TERRA, mix:'#2f6b45', fleet:AMBER};
var FAM_KEYS=D.families.map(function(f){return f.key;});
var BAND_KEYS=D.bands.map(function(b){return b.key;});
var CAT_KEYS=D.cats.map(function(c){return c.key;});

function n0(v){ return v===null||v===undefined?'n/a':Math.round(v).toLocaleString('en-GB'); }
function eur(v){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+Math.round(Math.abs(v)).toLocaleString('en-GB'); }
function eur2(v){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+Math.abs(v).toLocaleString('en-GB',
    {minimumFractionDigits:2,maximumFractionDigits:2}); }
function eurm(v){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  var s=v<0?'-':''; return s+'EUR '+(Math.abs(v)/1e6).toFixed(2)+'M'; }
function pct(v,d){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  return (100*v).toFixed(d===undefined?1:d)+'%'; }
function signpct(v,d){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  return (v>=0?'+':'')+(100*v).toFixed(d===undefined?1:d)+'%'; }
function cls(v){ return v===null||v===undefined||!isFinite(v)?'flat':(v>0?'up':(v<0?'down':'flat')); }
function sign(v,d){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  return (v>=0?'+':'-')+Math.abs(v).toLocaleString('en-GB',
    {minimumFractionDigits:d||0,maximumFractionDigits:d||0}); }
function num(v){ if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  return Math.round(v).toLocaleString('en-GB'); }
function byKey(arr,k){ for(var i=0;i<arr.length;i++) if(arr[i].key===k) return arr[i];
  return {key:k,label:String(k),short:String(k),note:'',color:NAVY}; }

/* ── state ───────────────────────────────────────────────────────────────────────────────────── */
var SEL_MK=new Set();
var S={clock:'CY', metric:'pv', denom:'own', fam:null, band:null, cat:null};

function pairOf(cl){
  var c=D.clocks[cl], cyc=D.cycles[cl];
  /* the cycle INDEX, not the period number: an atom carries an index into D.cycles */
  return {cl:cl, b:c.base, e:c.end, p:c.prior, ok:c.comparable, bl:c.baseLabel, el:c.endLabel,
    pl:c.priorLabel, bm:c.baseMonths, em:c.endMonths, held:c.heldOut, months:c.months,
    periods:c.periods, complete:c.complete,
    pi:cyc.indexOf(c.prior), bi:cyc.indexOf(c.base), ei:cyc.indexOf(c.end)};
}

/* ── the atomic roll-up. Every number on the page is a filter and a sum over these rows. ────── */
function atomsFor(famKey, bandKey, catKey, pnKey, cl){
  var arr=D.atoms[cl||S.clock], out=[], i, r;
  for(i=0;i<arr.length;i++){
    r=arr[i];
    if(SEL_MK.size && !SEL_MK.has(r[1])) continue;
    if(pnKey!==null && pnKey!==undefined){ if(r[0]!==pnKey) continue; }
    else {
      if(famKey!==null && famKey!==undefined && D.pn.fam[r[0]]!==FAM_KEYS.indexOf(famKey)) continue;
      if(bandKey && D.pn.bands[r[0]].indexOf(bandKey)<0) continue;
      if(catKey!==null && catKey!==undefined && D.pn.cat[r[0]]!==CAT_KEYS.indexOf(catKey)) continue;
    }
    out.push(r);
  }
  return out;
}
function totalOf(rows){
  var e=0,u=0,pn=new Set(),mk=new Set(),i;
  for(i=0;i<rows.length;i++){ e+=rows[i][3]; u+=rows[i][4]; pn.add(rows[i][0]); mk.add(rows[i][1]); }
  return {eur:e, units:u, pns:pn.size, dealers:mk.size};
}
function bucketsBy(rows, pr, keyOf){
  var m=new Map(), i, r, k, o;
  for(i=0;i<rows.length;i++){
    r=rows[i]; k=keyOf(r[0]);
    o=m.get(k); if(!o){ o={key:k, eur0:0,eur1:0,eurP:0, units0:0,units1:0, pns:new Set(), mk:new Set()};
      m.set(k,o); }
    o.pns.add(r[0]); o.mk.add(r[1]);
    if(r[2]===pr.pi) o.eurP+=r[3];
    if(r[2]===pr.bi){ o.eur0+=r[3]; o.units0+=r[4]; }
    if(r[2]===pr.ei){ o.eur1+=r[3]; o.units1+=r[4]; }
  }
  return Array.from(m.values());
}
/* the three-way split, exactly as build_price_layer does it: price is weighted across the members
   of the mix axis - the level below this node - which is what keeps the mix term non-zero. */
function splitMove(rows, memberOf, cb, ce){
  var m=new Map(), i, r, k, o;
  for(i=0;i<rows.length;i++){
    r=rows[i]; if(r[2]!==cb && r[2]!==ce) continue;
    k=memberOf(r[0]);
    o=m.get(k); if(!o){ o={q0:0,q1:0,r0:0,r1:0}; m.set(k,o); }
    if(r[2]===cb){ o.q0+=r[4]; o.r0+=r[3]; } else { o.q1+=r[4]; o.r1+=r[3]; }
  }
  var mem=[], Q0=0,Q1=0,R0=0,R1=0;
  m.forEach(function(v,k2){ mem.push({k:k2,o:v}); Q0+=v.q0; Q1+=v.q1; R0+=v.r0; R1+=v.r1; });
  mem.forEach(function(x){ var v=x.o;
    v.p0 = v.q0>0 ? v.r0/v.q0 : null; v.p1 = v.q1>0 ? v.r1/v.q1 : null; });
  var pbar0=0;
  mem.forEach(function(x){ var v=x.o;
    v.p0f = (v.p0!==null? v.p0 : (v.p1||0)); v.p1f = (v.p1!==null? v.p1 : v.p0f);
    pbar0 += (Q0>0? v.q0/Q0 : 0)*v.p0f; });
  var dMix=0, dPrice=0;
  mem.forEach(function(x){ var v=x.o; dMix += v.q1*v.p0f; dPrice += v.q1*(v.p1f-v.p0f); });
  dMix -= Q1*pbar0;
  var dVol=(Q1-Q0)*pbar0, dTot=R1-R0;
  return {R0:R0,R1:R1,Q0:Q0,Q1:Q1,pbar0:pbar0,vol:dVol,price:dPrice,mix:dMix,total:dTot,
          members:mem.length, residual:dTot-dVol-dPrice-dMix};
}
/* a single part number has one member in its own mix axis, so its mix term is zero by definition.
   That is stated rather than faked: mix is a family-level effect and is shown one level up. */
function splitOne(r0,q0,r1,q1){
  var p0 = q0>0? r0/q0 : null, p1 = q1>0? r1/q1 : null;
  var p0f = p0!==null?p0:(p1||0), p1f = p1!==null?p1:p0f;
  return {R0:r0,R1:r1,Q0:q0,Q1:q1,pbar0:p0f,vol:(q1-q0)*p0f,price:q1*(p1f-p0f),mix:0,
          total:r1-r0,members:1,residual:0,p0:p0,p1:p1};
}

/* ── the fleet: each period's own count, or the flat 2025 estimate ──────────────────────────── */
function markets(){ return SEL_MK.size ? Array.from(SEL_MK).map(function(i){return D.markets[i];})
                                       : D.markets; }
function isForwardForecastYear(year){
  if(!year || year<2026) return false;
  var hit=false;
  markets().forEach(function(m){
    var y=(D.fleet[m]||{})[String(year)];
    if(y && y.basis==='forecast') hit=true;
  });
  return hit;
}
function fleetBreakdown(useFlat, year){
  var ns=0,hv=0,lt=0,bases=new Set(),note='',forward=false;
  markets().forEach(function(m){
    if(useFlat){ var f=D.flat[m]||{n_series:0,heavy:0,light:0};
      ns+=f.n_series; hv+=f.heavy; lt+=f.light;
      bases.add('constant 2025 fleet (analytical alternative)'); return; }
    var y=(D.fleet[m]||{})[String(year)];
    if(!y){ bases.add('missing'); return; }
    ns+=y.n_series; hv+=y.heavy; lt+=y.light;
    if(y.basis==='actual') bases.add('measured');
    else if(y.basis==='estimate') bases.add('estimated');
    else if(year>=2026){
      forward=true;
      bases.add('forward figure (not quoted as forecast)');
    } else bases.add('forecast');
    if(y.quality) note=y.quality;
  });
  return {ns:ns, hv:hv, lt:lt, basis:Array.from(bases).join(' / '), note:note,
          forwardForecast:forward};
}
function n35Total(useFlat, year){
  var t=0;
  markets().forEach(function(m){
    var share=(D.n35[m]||{share:0}).share;
    var tot = useFlat ? ((D.flat[m]||{n_series:0}).n_series)
                      : (((D.fleet[m]||{})[String(year)]||{n_series:0}).n_series);
    t += tot*share;
  });
  return t;
}
/* ── fleetFor, carrying the honesty flag the band rows need ─────────────────────────────────── */
var NEVER_BANDED = D.neverbandedFleet||[];
function fleetFor(famKey, bandKey, year, useFlat){
  var fb=fleetBreakdown(useFlat, year);
  var nb=NON_BANDED_FLEET(year);
  if(bandKey){
    var n35=n35Total(useFlat, year);
    /* the never-banded market's N-series leaves every band denominator, so a band rate is
       never applied to a fleet whose own row is not a weight class */
    var netNs=Math.max(0, fb.ns-nb.value);
    var value;
    if(bandKey==='3.5t_N35') value=n35;
    else if(bandKey==='5.5t_N50_N55'||bandKey==='7.5t_N50_N62_N75') value=Math.max(0, netNs-n35);
    else value=netNs;
    return {value:value, basis:fb.basis, ns:fb.ns, hv:fb.hv, lt:fb.lt,
            note:(bandKey==='3.5t_N35'
                  ? 'the measured 3.5 t share of the N-series fleet, per market'
                  : (nb.value>0 ? 'the N-series fleet less the 3.5 t share and less the '
                      +nb.from.join(', ')+' fleet, whose own row is not a weight class'
                    : '')),
            sharedDenom:(bandKey==='5.5t_N50_N55'||bandKey==='7.5t_N50_N62_N75'),
            noWallet:nb.value>0, noWalletFrom:nb.from};
  }
  var value2;
  if(famKey==='n_series_truck') value2=fb.ns;
  else if(famKey==='heavy_truck') value2=fb.hv;
  else if(famKey==='light_vehicle') value2=fb.lt;
  else value2=fb.ns+fb.hv+fb.lt;
  if(famKey==='n_series_truck'){
    return {value:value2, basis:fb.basis, ns:fb.ns, hv:fb.hv, lt:fb.lt, sharedDenom:false,
            note:'the whole N-series fleet; the 3.5 t / 5.5 t / 7.5 t split of it is shown on the '
              +'bands inside',
            noWallet:nb.value>0, noWalletFrom:nb.from};
  }
  return {value:value2, basis:fb.basis, ns:fb.ns, hv:fb.hv, lt:fb.lt, sharedDenom:false,
          note:fb.note, noWallet:false, noWalletFrom:[]};
}
/* The N-series fleet of a market whose fleet row is not a weight class at all - one row for the
   whole N-series at 6.5/7.5 t - comes out of every band denominator. Dividing it by a 3.5 t rate
   would be wrong, and leaving it in the heavier denominators would flatter them. */
function NON_BANDED_FLEET(year){
  var v=0, from=[];
  markets().forEach(function(m){
    if(NEVER_BANDED.indexOf(m)<0) return;
    var tot = S.denom==='flat' ? ((D.flat[m]||{n_series:0}).n_series)
                               : (((D.fleet[m]||{})[String(year)]||{n_series:0}).n_series);
    if(tot>0){ v+=tot; from.push(m); }
  });
  return {value:v, from:from};
}
/* the four terms of the change in euro per vehicle, including the fleet term */
function pvTerms(s, f0, f1, basis, y0, y1){
  if(S.denom!=='flat'){
    if(y0!==undefined && isForwardForecastYear(y0))
      return {ok:false, why:'the '+y0+' fleet row is a forward figure from 2026 onward and is not '
        +'quoted as a forecast; switch to the constant 2025 fleet analytical alternative instead'};
    if(y1!==undefined && isForwardForecastYear(y1))
      return {ok:false, why:'the '+y1+' fleet row is a forward figure from 2026 onward and is not '
        +'quoted as a forecast; switch to the constant 2025 fleet analytical alternative instead'};
  }
  if(f0===null||f0===undefined||f1===null||f1===undefined)
    return {ok:false, why:'the fleet for one of the two periods is not on the page, so this row '
      +'cannot be put on a per-vehicle basis'};
  if(!f0 || !f1)
    return {ok:false, why:'the workbook carries no fleet for this row in one of the two periods '
      +(f0===0? '(it is zero for the earlier period)':'(it is zero for this period)')
      +', so there is nothing to divide by. The euro is shown, and no rate is claimed'};
  var vol=s.vol/f1, price=s.price/f1, mix=s.mix/f1;
  var fleet=s.R0*(f0-f1)/(f0*f1);
  return {ok:true, vol:vol, price:price, mix:mix, fleet:fleet,
          total:vol+price+mix+fleet, rate0:s.R0/f0, rate1:s.R1/f1, f0:f0, f1:f1,
          standStill:s.R0*(f1-f0)/f0,
          check:(s.R1/f1)-(s.R0/f0)-(vol+price+mix+fleet)};
}

/* ── the level being looked at, and the nodes in it ─────────────────────────────────────────── */
function levelNow(){
  if(S.cat) return 'pn';
  if(S.band) return 'cat';
  if(S.fam) return (S.fam==='n_series_truck') ? 'band' : 'cat';
  return 'fam';
}
function nodesNow(cl){
  var pr=pairOf(cl||S.clock), lvl=levelNow(), rows, i;
  if(lvl==='pn'){
    rows=atomsFor(S.fam, S.band, S.cat, null, cl);
    var per=new Map();
    for(i=0;i<rows.length;i++){ var r=rows[i], k=r[0], o=per.get(k);
      if(!o){ o={key:k, eur0:0,eur1:0,eurP:0, units0:0,units1:0, pns:new Set(), mk:new Set()};
        per.set(k,o); }
      o.pns.add(r[0]); o.mk.add(r[1]);
      if(r[2]===pr.pi) o.eurP+=r[3];
      if(r[2]===pr.bi){ o.eur0+=r[3]; o.units0+=r[4]; }
      if(r[2]===pr.ei){ o.eur1+=r[3]; o.units1+=r[4]; } }
    return Array.from(per.values());
  }
  if(lvl==='cat'){ return bucketsBy(atomsFor(S.fam, S.band, null, null, cl),
    pr, function(pn){ return CAT_KEYS[D.pn.cat[pn]]; }); }
  if(lvl==='band'){
    var rows2=atomsFor(S.fam, null, null, null, cl), seen={}, out=[];
    BAND_KEYS.forEach(function(bk){ seen[bk]={key:bk, eur0:0,eur1:0,eurP:0, units0:0,units1:0,
      pns:new Set(), mk:new Set()}; });
    for(i=0;i<rows2.length;i++){ var r2=rows2[i];
      D.pn.bands[r2[0]].forEach(function(bk){ var o=seen[bk]; if(!o) return;
        o.pns.add(r2[0]); o.mk.add(r2[1]);
        if(r2[2]===pr.pi) o.eurP+=r2[3];
        if(r2[2]===pr.bi){ o.eur0+=r2[3]; o.units0+=r2[4]; }
        if(r2[2]===pr.ei){ o.eur1+=r2[3]; o.units1+=r2[4]; } }); }
    BAND_KEYS.forEach(function(bk){ out.push(seen[bk]); });
    return out;
  }
  return bucketsBy(atomsFor(null, null, null, null, cl), pr,
    function(pn){ return FAM_KEYS[D.pn.fam[pn]]; });
}
/* The mix axis is the level BELOW the node, which is what makes the mix term a real effect.
   For a vehicle type that carries weight bands, the interesting basket shift is between bands;
   for the others it is between service families. */
function mixMemberOf(lvl, famKey){
  if(lvl==='fam'){
    if(famKey==='n_series_truck')
      return function(pn){ var b=D.pn.bands[pn]; return b.length? b[0] : '_none'; };
    return function(pn){ return CAT_KEYS[D.pn.cat[pn]]; };
  }
  if(lvl==='band') return function(pn){ return CAT_KEYS[D.pn.cat[pn]]; };
  return function(pn){ return pn; };
}
function nodeLabel(lvl, key){
  if(lvl==='fam') return byKey(D.families, key).label;
  if(lvl==='band') return byKey(D.bands, key).label;
  if(lvl==='cat') return byKey(D.cats, key).label;
  return D.pn.number[key];
}
function nodeShort(lvl, key){
  if(lvl==='fam') return byKey(D.families, key).short;
  if(lvl==='band') return byKey(D.bands, key).short;
  if(lvl==='cat') return byKey(D.cats, key).label;
  return D.pn.number[key];
}

function recFor(node, lvl, cl){
  cl = cl || S.clock;
  var pr=pairOf(cl);
  var fam = lvl==='fam' ? node.key : S.fam;
  var band = lvl==='band' ? node.key : S.band;
  var cat = lvl==='cat' ? node.key : S.cat;
  var rows;
  if(lvl==='fam') rows=atomsFor(node.key, null, null, null, cl);
  else if(lvl==='band') rows=atomsFor(S.fam, node.key, null, null, cl);
  else if(lvl==='cat') rows=atomsFor(S.fam, S.band, node.key, null, cl);
  else rows=atomsFor(S.fam, S.band, S.cat, node.key, cl);
  var s = (lvl==='pn')
    ? splitOne(node.eur0, node.units0, node.eur1, node.units1)
    : splitMove(rows, mixMemberOf(lvl, fam), pr.bi, pr.ei);
  var fA=fleetFor(fam, band, pr.b, S.denom==='flat');
  var fB=fleetFor(fam, band, pr.e, S.denom==='flat');
  var t=pvTerms(s, fA.value, fB.value, null, pr.b, pr.e);
  var tot=totalOf(rows);
  /* comparability: decided from the banding files, not disclaimed */
  var verdict='ok', why='';
  if(lvl==='cat' && S.fam==='n_series_truck' && band){
    var c=(D.comparability[S.clock]||{})[node.key]||{verdict:'ok'};
    verdict=c.verdict||'ok'; why=c.why||'';
  }
  if(lvl==='band' && node.key==='shared_across_bands'){
    verdict='overlap';
    why='these part numbers sit inside more than one band, so this row repeats euro that also '
      +'appears in the band rows above it and must never be added to them';
  }
  var thin=false, thinWhy='', noWalletRow=false;
  if(lvl==='pn'){
    var span=Math.abs(s.R1)+Math.abs(s.R0);
    thin = tot.dealers<2 || span<25000;
    if(thin) thinWhy='a small base: '+tot.dealers+' customer'+(tot.dealers===1?'':'s')+', '
      +eur(span)+' billed across two periods';
  }
  /* a row whose whole vehicle type has no fleet in the workbook cannot carry a rate at all */
  if(fA.value===0 && fB.value===0 && s.R1+s.R0>0) noWalletRow=true;
  /* a period pair that is not like for like is refused outright */
  var pairOk = pr.ok && (pr.bm>=12) && (pr.em>=12);
  return {key:node.key, level:lvl, fam:fam, band:band, cat:cat,
    eur0:s.R0, eur1:s.R1, eurPrior:node.eurP, units0:node.units0, units1:node.units1,
    pns:node.pns.size, dealers:node.mk.size, split:s, pv:t,
    pairOk:pairOk, notComparable:!pairOk, verdict:verdict, why:why,
    thin:thin, thinWhy:thinWhy, sharedDenom:fB.sharedDenom, noWallet:fB.noWallet,
    noWalletRow:noWalletRow,
    f0:fA.value, f1:fB.value, fleetNote:fB.note,
    rate0:t.ok?t.rate0:null, rate1:t.ok?t.rate1:null,
    deltaPct:(s.R0>0? s.R1/s.R0-1 : null),
    deltaUnitsPct:(node.units0>0? node.units1/node.units0-1 : null),
    deltaPriorPct:(node.eurP>0? s.R0/node.eurP-1 : null)};
}

function measureOf(rec){
  if(S.metric==='pv') return rec.pv.ok ? (rec.pv.rate1-rec.pv.rate0) : null;
  if(S.metric==='abs') return rec.split.R1-rec.split.R0;
  return rec.units1-rec.units0;
}
function measureName(){ for(var i=0;i<D.metrics.length;i++) if(D.metrics[i].key===S.metric)
  return D.metrics[i].label; return ''; }

var charts={}, LAST=[], DEC_TIPS=[];
var PANEL_ERR=[], SUPPRESS_ERR=false;
/* ── the chart lifecycle ──────────────────────────────────────────────────────────────────────
   Destroying a chart and building another one on the same canvas leaves a window in which the
   destroyed chart's platform listeners are still attached: the click, mouseup and contextmenu
   listeners live on the canvas, while Chart.js's hover and resize listeners can stay reachable
   after destroy() has already emptied the chart. A pointer that is sitting over the canvas when a
   control re-renders there reaches that stale instance and finds its internals - .legend,
   .tooltip - already taken away, which is the "Cannot read properties of undefined (reading
   'handleEvent')" this page was reported for. So every teardown here does all three things:
   remove the listeners, mark the instance destroyed, and set a flag the callbacks test before they
   touch anything. The click is wired with addEventListener rather than Chart.js's own onClick, so
   there is no framework path left to go stale. */
function teardownCanvas(id){
  var ch=charts[id];
  delete charts[id];
  if(ch){
    try{ ch.destroy(); }catch(e){ /* already gone */ }
    try{ Object.defineProperty(ch,'destroyed',{value:true,configurable:true}); }catch(e){}
  }
  var el=document.getElementById(id);
  if(el){
    var freed=el.__free;
    if(freed){
      try{ el.removeEventListener('click',freed.click); }catch(e){}
      try{ el.removeEventListener('contextmenu',freed.ctx); }catch(e){}
      el.__free=null;
    }
    try{
      if(el.$proxies) Object.keys(el.$proxies).forEach(function(k){ delete el.$proxies[k]; });
    }catch(e){}
    try{ delete el.$chartjs; }catch(e){}
  }
}
function alive(id){ var c=charts[id]; return !!(c && !c.destroyed && c.canvas && c.ctx); }
/* The two controls a breadcrumb click can change - the period and the vehicle type - follow the
   state rather than only setting it, so climbing back leaves the toolbar and the figures saying the
   same thing. */
function syncFleetButtons(pr){
  var block = isForwardForecastYear(pr.b) || isForwardForecastYear(pr.e);
  document.querySelectorAll('#segFleet button').forEach(function(x){
    var own = x.getAttribute('data-d')==='own';
    x.disabled = block && own;
    x.title = block && own
      ? 'Forward fleet figures from 2026 are not quoted as forecasts; use constant 2025 fleet instead'
      : '';
    x.classList.toggle('on', x.getAttribute('data-d')===S.denom);
  });
}
function syncDrillControls(){
  var sf=document.getElementById('selFam');
  if(sf && sf.value!==(S.fam||'')) sf.value=S.fam||'';
  var sc=document.getElementById('selClock');
  if(sc && sc.value!==S.clock) sc.value=S.clock;
}
/* one panel that throws must not take the rest of the page with it: the error is recorded and the
   failure banner counts it, and the next panel is drawn regardless */
function guard(name, fn){
  try{ return fn(); }
  catch(e){
    PANEL_ERR.push(name+': '+String(e&&e.message?e.message:e));
    var b=document.getElementById('panelerrs');
    if(b){
      b.className='on';
      b.innerHTML='<b>'+PANEL_ERR.length+' panel'+(PANEL_ERR.length===1?'':'s')
        +' did not draw.</b> The rest of the page is complete and usable. Detail: '
        +PANEL_ERR.map(function(s){ return '<code>'+s.replace(/</g,'&lt;')+'</code>'; }).join('; ');
    }
    return null;
  }
}
function mk(id,cfg,onClick,onContext){
  teardownCanvas(id);
  var el=document.getElementById(id);
  if(!el) return null;
  var ch;
  try{ ch=new Chart(el,cfg); }
  catch(e){ PANEL_ERR.push(id+': '+String(e&&e.message?e.message:e)); return null; }
  charts[id]=ch;
  var click=function(ev){
    if(!alive(id)) return;
    var els;
    try{ els=ch.getElementsAtEventForMode(ev,'nearest',{intersect:true},false); }
    catch(e){ return; }
    if(els && els.length && onClick) onClick(els[0].index, els[0].datasetIndex);
  };
  var ctx=function(ev){
    if(!alive(id)) return;
    ev.preventDefault();
    if(onContext) onContext(ev);
  };
  el.addEventListener('click',click);
  el.addEventListener('contextmenu',ctx);
  el.__free={click:click, ctx:ctx};
  if(ch.options) { ch.options.onClick=null; ch.options.onHover=null; ch.options.onLeave=null; }
  return ch;
}
/* a control that is opened and then re-renders beneath itself leaves the pointer over a canvas
   that has been replaced. Closing and blurring the open popup before every draw removes that. */
function closePops(){
  ['pickPop','helpPop'].forEach(function(id){
    var p=document.getElementById(id);
    if(p) p.classList.remove('open');
  });
  if(document.activeElement && document.activeElement.blur) document.activeElement.blur();
}
function chartTip(c){
  if(!c||!c.chart) return '';
  var i=c.dataIndex;
  if(i===undefined||i===null) return '';
  if(c.chart.canvas && c.chart.canvas.id==='c_dec') return DEC_TIPS[i]||'';
  return LAST[i] ? tipForRow(LAST[i], LAST[i].level) : '';
}
Chart.defaults.font.family="-apple-system,Segoe UI,Roboto,Arial,sans-serif";
Chart.defaults.font.size=11;
Chart.defaults.color='#4a443b';
Chart.defaults.animation=false;
Chart.defaults.animations=false;
Chart.defaults.resizeDelay=0;

function axisTick(v){ var a=Math.abs(v);
  if(a>=1e6) return (v/1e6).toFixed(1)+'M';
  if(a>=1000) return (v/1000).toFixed(1)+'k';
  return String(Math.round(v)); }
/* Every per-vehicle figure on this page is a fraction of a euro or a small number of euros - a euro
   or two of move, a few cents of price - so the whole-euro formatter above printed every tick on
   those axes as "0". This one gives the unit: cents below a euro, two decimals above it, and never
   a negative zero. The step is read off the tick so that a row of ticks cannot show the same value
   twice - "-7.00" and "-7c" are the same number written two ways. */
function axisCents(v, step){
  if(v===null||v===undefined||!isFinite(v)) return '';
  var a=Math.abs(step===undefined? null : step);
  if(a!==null && a>0 && a<0.1) return (v*100).toFixed(1)+'c';
  v=Math.round(v*1000)/1000;
  if(v===0) return '0';
  if(Math.abs(v)<1) return (Math.round(v*100))+'c';
  return v.toFixed(2);
}
var CENTS_TITLE='euro per vehicle, in cents (1c = EUR 0.01 per vehicle in service)';

function render(){
  closePops();
  syncDrillControls();
  var pr=pairOf(S.clock), lvl=levelNow();
  var recs=nodesNow().map(function(n){ return recFor(n, lvl); });  recs.sort(function(a,b){
    if(a.notComparable!==b.notComparable) return a.notComparable? 1:-1;
    if(a.verdict==='pooled'!==(b.verdict==='pooled')) return a.verdict==='pooled'? 1:-1;
    return Math.abs(b.split.R1)-Math.abs(a.split.R1); });
  if(recs.length>60) recs=recs.slice(0,60);
  LAST=recs;

  /* breadcrumb */
  var bits=['<span class="'+(S.fam?'c':'')+'" data-crumb="0">All vehicle types</span>'];
  if(S.fam) bits.push('<span class="'+(S.band?'c':'')+'" data-crumb="1">'
    +byKey(D.families,S.fam).label+'</span>');
  if(S.band) bits.push('<span class="'+(S.cat?'c':'')+'" data-crumb="2">'
    +byKey(D.bands,S.band).label+'</span>');
  if(S.cat) bits.push('<span><b>'+byKey(D.cats,S.cat).label+'</b></span>');
  else if(S.fam && !S.band && S.fam==='n_series_truck') bits.push('<span>tonnage bands</span>');
  else if(S.fam && !S.band) bits.push('<span>service families</span>');
  else if(S.cat===null && S.band) bits.push('<span>service families</span>');
  if(S.cat) bits.push('<span><b>part numbers</b></span>');
  document.getElementById('crumb').innerHTML='<span>You are looking at:</span> '
    +bits.join(' <span style="color:#c9c2b6">&rsaquo;</span> ')
    +' <span style="margin-left:5px">'+(pr.ok? (pr.el+' against '+pr.bl) : 'not comparable')+'</span>';

  /* KPIs */
  var rowsNow=atomsFor(S.fam, S.band, S.cat, null);
  var R0=0,R1=0,U0=0,U1=0;
  rowsNow.forEach(function(r){ if(r[2]===pr.bi){R0+=r[3];U0+=r[4];}
    if(r[2]===pr.ei){R1+=r[3];U1+=r[4];} });
  var fA=fleetFor(S.fam,S.band,pr.b,S.denom==='flat');
  var fB=fleetFor(S.fam,S.band,pr.e,S.denom==='flat');
  var sAll=splitMove(atomsFor(S.fam,S.band,S.cat,null), mixMemberOf(lvl==='pn'?'cat':lvl, S.fam),
    pr.bi, pr.ei);
  var pvAll=pvTerms(sAll, fA.value, fB.value, null, pr.b, pr.e);
  var fwdOwn = S.denom!=='flat' && (isForwardForecastYear(pr.b) || isForwardForecastYear(pr.e));
  var fw=document.getElementById('fleetWarn');
  if(fw){
    fw.style.display = fwdOwn ? 'block' : 'none';
    fw.innerHTML = fwdOwn
      ? ('<b>Forward fleet figures are not quoted as forecasts.</b> The selected comparison uses a '
         +'year from 2026 onward whose workbook fleet row is marked forward. Per-vehicle rates on '
         +'each period\'s own fleet are blocked. Open <b>More controls</b> and switch to '
         +'<b>Constant 2025 fleet (analytical)</b> for a like-for-like alternative.')
      : '';
  }
  if(fwdOwn && S.denom!=='flat'){
    S.denom='flat';
    document.querySelectorAll('#segFleet button').forEach(function(x){
      x.classList.toggle('on', x.getAttribute('data-d')==='flat');
      x.disabled = (x.getAttribute('data-d')==='own');
    });
    fA=fleetFor(S.fam,S.band,pr.b,true);
    fB=fleetFor(S.fam,S.band,pr.e,true);
    pvAll=pvTerms(sAll, fA.value, fB.value, null, pr.b, pr.e);
  } else {
    syncFleetButtons(pr);
  }
  var book=totalOf(atomsFor(null,null,null,null));
  var sharedEur=0,totEur=0;
  atomsFor(null,null,null,null).forEach(function(r){ if(r[2]!==pr.ei) return; totEur+=r[3];
    var fi=D.pn.fam[r[0]];
    if(FAM_KEYS[fi]==='shared_across_families'||FAM_KEYS[fi]==='unattributed') sharedEur+=r[3]; });
  var k=[];
  k.push({lab:'Billed euro per vehicle, this period', cls:'t',
    val: fB.value? eur2(R1/fB.value):'n/a',
    sub: (fA.value&&fB.value)? ('last period '+eur2(R0/fA.value)+' ('+signpct((R1/fB.value)/(R0/fA.value)-1)+')') : fB.basis,
    tip:'<b>Billed euro per vehicle</b><br>'+eur(R1)+' billed in '+pr.el+' over '+n0(fB.value)
      +' vehicles in service ('+(S.denom==='flat'?'constant 2025 fleet (analytical)':'that period\'s own count')
      +').<br>Last period: '+eur(R0)+' over '+n0(fA.value)+' vehicles.<br>'
      +'This is the measure that does not move just because the fleet moved.'});
  k.push({lab:'Net move per vehicle', cls:'g', val: pvAll.ok? eur2(pvAll.total):'n/a',
    sub: pvAll.ok? ('fleet '+sign(pvAll.fleet,2)+' | price '+sign(pvAll.price,2)+' | volume '
      +sign(pvAll.vol,2)+' | mix '+sign(pvAll.mix,2)) : (pvAll.why||'not comparable'),
    tip:'<b>The change in euro per vehicle, split</b><br>Fleet '+eur2(pvAll.ok?pvAll.fleet:null)
      +': what the fleet change alone took away or handed over.<br>Price '
      +eur2(pvAll.ok?pvAll.price:null)+' on the units actually sold.<br>Volume '
      +eur2(pvAll.ok?pvAll.vol:null)+' at last period\'s price.<br>Mix '
      +eur2(pvAll.ok?pvAll.mix:null)+': a different basket, at last period\'s prices.<br>'
      +'The four add up to the move in euro per vehicle.'});
  k.push({lab:'Fleet denominator', cls:'a', val: n0(fB.value),
    sub: fB.basis+(fA.value? ' | last period '+n0(fA.value):''),
    tip:'<b>The denominator</b><br>'+n0(fB.value)+' vehicles for '+pr.el+'.<br>Basis: '+fB.basis
      +'.<br>'+(fB.note||'')+(S.denom==='flat'
        ? '<br>Constant 2025 fleet is an analytical alternative, not a forward forecast.'
        : '')});
  document.getElementById('kpis').innerHTML=k.map(function(x){
    return '<div class="kpi '+(x.cls||'')+'"><div class="lab">'+x.lab
      +' <span class="info" tabindex="0">i<span class="tip">'+x.tip+'</span></span></div>'
      +'<div class="val">'+x.val+'</div><div class="sub">'+x.sub+'</div></div>';}).join('');

  var lvlName = lvl==='fam'? 'vehicle type' : lvl==='band'? 'tonnage band'
              : lvl==='cat'? 'service family' : 'part number';
  var TITLES = {
    fam: 'Which parts families are moving up or down?',
    band: 'Inside the N-series truck: which tonnage band is moving?',
    cat: 'Which service family is driving the move on this band?',
    pn: 'Which part numbers make up that service family move?'
  };
  document.getElementById('t-main').textContent=TITLES[lvl];
  document.getElementById('q-main').innerHTML='Billed euro per vehicle this period against the same '
    +'months a year earlier. Click a bar to open the family beneath it; right-click to step back. '
    +'Switch chart layout in the toolbar on this card, or open <b>More controls</b> for measure and '
    +'fleet options.';
  document.getElementById('t-table').textContent= (lvl==='pn'
    ? 'The part numbers behind that move, each against the same months a year earlier'
    : 'The numbers behind both charts, by '+lvlName);
  document.getElementById('q-table').innerHTML='Click any row to open the level beneath it. '
    +'<b>volume</b>, <b>price</b>, <b>mix</b> and <b>fleet</b> are in euro per vehicle and add up to '
    +'the move in euro per vehicle.';

  /* ── the main panel: the three chosen forms ───────────────────────────────────────────────────
     One region, three views of the same rows. The decomposition below is unchanged and keeps its
     own canvas, so the four-term split is still drawn beside whichever form is showing. */
  guard('the three forms', function(){ renderForms(recs, lvl, pr); });

  /* ── the decomposition, on the same rows ──────────────────────────────────────────────────────
     The first dataset is the net move: the four components added up for the reader, so the answer
     is visible without adding four bars in the head. The rest are the components. Every value here
     is euro per vehicle, which is a fraction of a euro, so the axis is labelled in cents at two
     decimals - the previous whole-euro formatter printed every tick as "0". */
  DEC_TIPS=[];
  var dSets=[{label:'net move', backgroundColor:'#15233c',
      data: recs.map(function(r){ return (r.notComparable||!r.pv.ok)? null : r.pv.total; })}].concat(
    ['vol','price','mix','fleet'].map(function(key){
      return {label:key, backgroundColor:DEC_COLORS[key],
        data: recs.map(function(r){ return (r.notComparable||!r.pv.ok)? null : r.pv[key]; })}; }));
  recs.forEach(function(r){

    DEC_TIPS.push(r.notComparable? 'not comparable: the period is incomplete'
      : (!r.pv.ok? r.pv.why
      : nodeLabel(lvl, r.key)+'\nnet move '+eur2(r.pv.total)+' per vehicle\n= fleet '
        +eur2(r.pv.fleet)+' + price '+eur2(r.pv.price)+' + volume '+eur2(r.pv.vol)+' + mix '
        +eur2(r.pv.mix)+'\nthe four add up to the move, on '+n0(r.pv.f1)+' vehicles this period '
        +'against '+n0(r.pv.f0)+' a year earlier'));
  });
  guard('the decomposition chart', function(){
    var cfgDec={
      type:'bar',
      data:{labels:recs.map(pointLabel),datasets:dSets},
      options:{
        indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:false,
        plugins:{
          legend:{display:false},
          tooltip:{backgroundColor:NAVY,titleColor:'#f0b49a',bodyColor:PAPER,padding:8,
            titleFont:{size:11.5},bodyFont:{size:11},
            callbacks:{label:function(c){ return c.dataset.label+': '+eur2(c.raw); }}}},
        scales:{
          x:{grid:{color:LINE},
            title:{display:true,text:'euro per vehicle, in cents (EUR per vehicle in service)'},
            ticks:{callback:function(v,i,arr){
              var step=(arr&&arr.length>1)? Math.abs(arr[1].value-arr[0].value) : 0.01;
              return axisCents(v, step); }}},
          y:{grid:{display:false},ticks:{font:{size:10.5}}}}}
    };
    mk('c_dec', cfgDec, function(i){ drill(i); }, function(){ climb(); });
  });
  document.getElementById('l_dec').innerHTML=[['net','the answer: the four terms added up'],
    ['vol','volume','units sold, at last period\'s price'],
    ['price','price','what we charged on the units actually sold'],
    ['mix','mix','a different basket of service families, at last period\'s prices'],
    ['fleet','fleet','the euro needed just to stand still on a bigger fleet']].map(function(x){
      if(x[0]==='net') return '<span><i style="background:'+NAVY+'"></i><b>net move</b> &mdash; '+x[1]
        +' (the four bars beside it)</span>';
      return '<span><i style="background:'+DEC_COLORS[x[0]]+'"></i><b>'+x[1]+'</b> &mdash; '+x[2]
        +'</span>';}).join('');

  var heroEl=document.getElementById('heroDriver');
  if(heroEl){
    var pool=recs.filter(function(r){ return !r.notComparable && r.pv.ok; });
    if(!pool.length){
      heroEl.innerHTML='<b>Main driver:</b> no comparable move on this selection yet.'
        +(pvAll.ok? '' : ' '+String(pvAll.why||''));
    } else {
      pool.sort(function(a,b){ return Math.abs(b.pv.total)-Math.abs(a.pv.total); });
      var top=pool[0];
      var comp=[['fleet',top.pv.fleet],['price',top.pv.price],['volume',top.pv.vol],['mix',top.pv.mix]];
      comp.sort(function(a,b){ return Math.abs(b[1])-Math.abs(a[1]); });
      var word={fleet:'the fleet',price:'price',volume:'volume',mix:'what we sold'}[comp[0][0]];
      heroEl.innerHTML='<b>Main driver:</b> '+nodeLabel(lvl, top.key)+' is '
        +(top.pv.total>=0?'up ':'down ')+eur2(Math.abs(top.pv.total))+' per vehicle against '
        +pr.bl.split(' ')[0]+', mainly '+word+'.';
    }
  }

  /* ── the table, then the band panel, then the panels that do not move with a drill ────────
     Each is wrapped on its own: one bad row in the biggest panel must not take the panels below
     it down with it, and the reader is told which one failed rather than being left with a blank
     page. */
  guard('the table', function(){ renderTable(recs, lvl, pr); });
  guard('the band panel', function(){ renderBandPanel(); });
  guard('the static panels', function(){ renderStatic(pr, lvl); });
}
/* Are we winning or losing on each band, on both clocks? The band answer is always in euro per
   vehicle, so a growing fleet cannot stand in for winning; switch the measure and the fleet
   selector and the panel says so rather than silently changing what it claims. */
function renderTable(recs, lvl, pr){
  var head1 = lvl==='fam'? ['Vehicle type'] : lvl==='band'? ['Tonnage band']
            : lvl==='cat'? ['Service family'] : ['Part number','Service family'];
  document.getElementById('tbl').tHead.innerHTML='<tr>'
    +head1.map(function(h){ return '<th>'+h+'</th>'; }).join('')
    +'<th class="n">Euro '+pr.bl.split(' ')[0]+'</th><th class="n">Euro '+pr.el.split(' ')[0]
    +'</th><th class="n">Move</th><th class="n">%</th><th class="n">Units</th>'
    +'<th class="n">EUR / vehicle</th><th class="n">volume</th><th class="n">price</th>'
    +'<th class="n">mix</th><th class="n">fleet</th><th class="n">Fleet</th>'
    +'<th class="n">vs year before</th><th>Read</th></tr>';
  document.getElementById('tbl').tBodies[0].innerHTML=recs.map(function(r,i){
    var first = lvl==='pn'
      ? '<td><b>'+D.pn.number[r.key]+'</b><div class="caption">'+byKey(D.cats,r.cat).label+' &middot; '
        +(D.pn.fits[r.key]||[]).map(function(f){ return byKey(D.families,f).short; }).join(', ')
        +'</div></td>'
      : '<td><b>'+nodeLabel(lvl,r.key)+'</b></td>';
    var pv=r.pv;
    var cells='<td class="n">'+eur(r.eur0)+'</td><td class="n">'+eur(r.eur1)+'</td>'
      +'<td class="n '+cls(r.notComparable?null:r.eur1-r.eur0)+'">'
        +(r.notComparable? '&mdash;' : sign(r.eur1-r.eur0))+'</td>'
      +'<td class="n '+cls(r.notComparable?null:r.deltaPct)+'">'
        +(r.notComparable? '&mdash;' : signpct(r.deltaPct))+'</td>'
      +'<td class="n">'+num(r.units1)+'<div class="caption">was '+num(r.units0)+' ('
        +signpct(r.deltaUnitsPct)+')</div></td>'
      +'<td class="n">'+(pv.ok? eur2(pv.rate1)+'<div class="caption">was '+eur2(pv.rate0)+'</div>'
        : '&mdash;')
        +(r.sharedDenom? ' <span class="pill pooled" title="no source separates the 5.5 t fleet from '
          +'the 7.5 t fleet, so the denominator here is shared between them">denominator shared</span>':'')
        +'</td>'
      +'<td class="n">'+(r.notComparable||!pv.ok? '&mdash;' : sign(pv.vol,0))+'</td>'
      +'<td class="n">'+(r.notComparable||!pv.ok? '&mdash;' : sign(pv.price,0))+'</td>'
      +'<td class="n">'+(r.notComparable||!pv.ok? '&mdash;' : sign(pv.mix,0))+'</td>'
      +'<td class="n">'+(r.notComparable||!pv.ok? '&mdash;' : sign(pv.fleet,0))+'</td>'
      +'<td class="n">'+num(r.f1)+'</td>'
      +'<td class="n '+cls(r.notComparable?null:r.deltaPriorPct)+'">'
        +(r.eurPrior? signpct(r.deltaPriorPct) : '&mdash;')+'</td>';
    var read;
    if(r.notComparable) read='<span class="pill nc">not comparable</span> the period is incomplete';
    else if(r.noWalletRow) read='<span class="pill nc">no fleet to divide by</span> the workbook '
      +'carries no vehicles for this row in either period, so the euro is shown and no rate is '
      +'claimed';
    else if(r.verdict==='pooled') read='<span class="pill pooled">not comparable by band</span> '+r.why;
    else if(r.verdict==='overlap') read='<span class="pill pooled">overlaps the bands</span> '+r.why;
    else if(r.thin) read='<span class="pill thin">low confidence</span> '+r.thinWhy;
    else if(verdictThin(r)) read='<span class="pill thin">read with care</span> '+r.why;
    else read=readText(r);
    return '<tr class="'+(r.notComparable?'nc':'clickable')+'" data-i="'+i+'">'+first+cells
      +'<td>'+read+'</td></tr>';}).join('');
  document.getElementById('cap-table').innerHTML='Click any row to open the level beneath it. '
    +'<b>volume</b>, <b>price</b>, <b>mix</b> and <b>fleet</b> are in euro per vehicle, and they add '
    +'up to the move in euro per vehicle. The <b>vs year before</b> column puts this period against '
    +'the same months a year earlier, so a part-number row carries its own comparison even though the '
    +'chart above only draws the current pair. '
    +(S.metric==='units'? 'The charts are showing units; the split stays in euro, because a unit '
      +'cannot be split into price and volume.':'')
    +(lvl==='band'? ' <b>The band rows overlap.</b> A part number that fits two bands appears in both, '
      +'so these rows must never be added together: the "fits more than one band" row is the pooled '
      +'figure, counted once.':'')
    +'';

  /* The table already carries its rows and their index in data-i; delegated once for the life of
     the page, so a re-render never has to attach or remove anything. The breadcrumb is rebuilt each
     draw, so its own listeners are attached to the spans as they are written. */
  document.querySelectorAll('#crumb span.c').forEach(function(sp){
    sp.addEventListener('click',function(){
      var n=parseInt(sp.getAttribute('data-crumb'),10);
      if(n===0){ S.fam=null; S.band=null; S.cat=null; }
      if(n===1){ S.band=null; S.cat=null; }
      if(n===2){ S.cat=null; }
      render(); }); });
}

/* Are we winning or losing on each band, on both clocks? The band answer is always in euro per
   vehicle, so a growing fleet cannot stand in for winning; switch the measure and the fleet
   selector and the panel says so rather than silently changing what it claims. */
function renderBandPanel(){
    var cyc=Object.keys(D.clocks), rows=[], head='<tr><th>Clock and pair</th>'
      +'<th class="n">3.5 t, EUR / veh</th><th class="n">5.5 t, EUR / veh</th>'
      +'<th class="n">7.5 t, EUR / veh</th><th class="n">Where the money actually went</th></tr>';
    cyc.forEach(function(cl){
      var pr=pairOf(cl);
      var cells=[], euroCells=[], best=null;
      D.bands.slice(0,3).forEach(function(b){
        var node=null, lv='band';
        /* read the band node on this clock, independently of the clock the page is showing */
        var rows2=atomsFor('n_series_truck', b.key, null, null, cl);
        var e1=0,e0=0;
        rows2.forEach(function(r){ if(r[2]===pr.ei) e1+=r[3]; if(r[2]===pr.bi) e0+=r[3]; });
        var f1=fleetFor('n_series_truck', b.key, pr.e, S.denom==='flat');
        var f0=fleetFor('n_series_truck', b.key, pr.b, S.denom==='flat');
        var rate1=f1.value? e1/f1.value : null, rate0=f0.value? e0/f0.value : null;
        var move=(rate1!==null&&rate0!==null)? rate1-rate0 : null;
        euroCells.push({b:b, e1:e1, e0:e0, move:move, noWallet:f1.noWallet});
        if(move!==null && (best===null||Math.abs(move)>Math.abs(best.move))) best={b:b, move:move};
        cells.push('<td class="n '+cls(move)+'">'+(move===null?'&mdash;':eur2(rate1))
          +'<div class="caption">'+(move===null?'&mdash;':'was '+eur2(rate0)+', '+sign(move,2))+'</div></td>');
      });
      var tot=0; euroCells.forEach(function(x){ tot+=x.e1; });
      var shares=euroCells.map(function(x){ return {b:x.b, p: tot? 100*x.e1/tot : 0,
        e:x.e1, noWallet:x.noWallet}; });
      shares.sort(function(a,b){ return b.p-a.p; });
      var went=shares.map(function(s){ return s.b.short+' '+s.p.toFixed(0)+'% ('+eur(s.e)+')'
        +(s.noWallet?' <span class="pill thin" title="a market on this page carries its N-series as '
          +'one row with no weight class, so that fleet is excluded from the band denominators">one '
          +'market not banded</span>':''); }).join(' &middot; ');
      var held=pr.held&&pr.held.length? '<div class="caption">held out: '+pr.held.map(function(h){
        return h.label+' ('+h.why+')'; }).join('; ')+'</div>' : '';
      rows.push('<tr><td><b>'+cl+'</b> &middot; '+pr.bl+' against '+pr.pl+'</td>'+cells.join('')
        +'<td>'+went+'<div class="caption">'+(best? 'biggest move: '+best.b.short+' '
          +sign(best.move,2)+' per vehicle' : '')+'</div>'+held+'</td></tr>');
    });
    var out='<div class="tblwrap" style="max-height:none"><table id="t_bands"><thead>'+head
      +'</thead><tbody>'+rows.join('')+'</tbody></table></div>'
      +'<div class="caption">'+(S.denom==='flat'
        ? 'This panel is dividing by the constant 2025 fleet analytical alternative, as selected '
          +'above. Switch back to each period\'s own fleet for the like-for-like answer.'
        : "Each period's own fleet, as selected above.")+' '
      +(S.metric!=='pv'? 'The charts above are showing a different measure; this panel is always euro '
        +'per vehicle, because that is the only band answer the fleet cannot hide.' : '')
      +'</div>';
    document.getElementById('bandpanel').innerHTML=out;
    document.getElementById('t-bandpanel').textContent = (levelNow()==='band'
      ? 'The same three bands on the clock, measure and customers you have chosen'
      : 'Which of the three bands is winning, on both clocks at once?');
    document.getElementById('q-bandpanel').innerHTML='A band can win on one clock and lose on the '
      +'other, because the two clocks hold different months. Both are shown side by side rather than '
      +'averaged. This panel is always euro per vehicle, so a growing fleet cannot stand in for '
      +'winning.';
}
function verdictThin(r){ return r.verdict==='thin'; }

function drill(i){
  var r=LAST[i]; if(!r) return;
  if(r.notComparable) return;
  var lvl=r.level;
  if(lvl==='fam'){ S.fam=r.key; S.band=null; S.cat=null; }
  else if(lvl==='band'){ S.band=r.key; S.cat=null; }
  else if(lvl==='cat'){ S.cat=r.key; }
  else return;
  render();
}
/* ── climbing back: right-click on a chart, or Esc / Backspace ──────────────────────────────── */
function climb(){
  if(S.cat) S.cat=null;                 /* part numbers -> the service family */
  else if(S.band) S.band=null;          /* a band -> the bands of the vehicle type */
  else if(S.fam) { S.fam=null; }        /* a vehicle type -> all vehicle types */
  else return false;
  render();
  return true;
}
/* Stepping the period. The clock is on the toolbar; the arrows walk the periods the clock
   knows, skipping the ones an incomplete year holds out, so every confirmed step compares the
   same months on both sides. */
function stepClock(dir){
  var c=D.clocks[S.clock], comp=c.complete||[], i=comp.indexOf(c.end);
  if(i<0) return false;
  var j=i+dir;
  if(j<0||j>=comp.length) return false;
  var base=comp[j-1]!==undefined? comp[j-1] : null;
  if(comp[j]-1!==base) return false;
  c.base=base; c.end=comp[j];
  c.baseLabel=D.clocks[S.clock].spelled[String(base)];
  c.endLabel=D.clocks[S.clock].spelled[String(comp[j])];
  render();
  return true;
}
function readText(r){
  if(!r.pv.ok) return r.pv.why;
  var t=r.pv.total;
  var comp=[['fleet',r.pv.fleet],['price',r.pv.price],['volume',r.pv.vol],['mix',r.pv.mix]];
  comp.sort(function(a,b){ return Math.abs(b[1])-Math.abs(a[1]); });
  var word={fleet:'the fleet',price:'price',volume:'volume',mix:'what we sold'}[comp[0][0]];
  return (t>=0?'better':'worse')+' by '+eur2(Math.abs(t))+' per vehicle, mainly '+word;
}
function tipForRow(r, lvl){
  var out=[nodeLabel(lvl, r.key)];
  out.push('billed '+eur(r.eur1)+' this period, '+eur(r.eur0)+' last period');
  if(r.eurPrior) out.push('a year before that: '+eur(r.eurPrior)+' ('+signpct(r.deltaPriorPct)+')');
  if(r.pv.ok && !r.notComparable){
    out.push('per vehicle '+eur2(r.pv.rate1)+' against '+eur2(r.pv.rate0)+' on '+n0(r.pv.f1)+' and '
      +n0(r.pv.f0)+' vehicles');
    out.push('move '+eur2(r.pv.total)+' = fleet '+eur2(r.pv.fleet)+' + price '+eur2(r.pv.price)
      +' + volume '+eur2(r.pv.vol)+' + mix '+eur2(r.pv.mix));
    out.push('the fleet alone needed '+eur(r.pv.standStill)+' of extra billing to stand still');
  } else if(!r.pv.ok){ out.push('per vehicle: '+r.pv.why); }
  out.push(n0(r.units1)+' units this period against '+n0(r.units0)+' last period');
  out.push(n0(r.pns)+' part numbers, '+n0(r.dealers)+' customers, '+n0(r.f1)+' vehicles in service');
  if(r.notComparable) out.push('NOT COMPARABLE: the period is incomplete');
  if(r.noWalletRow) out.push('NO FLEET TO DIVIDE BY: the workbook names no vehicles here, so no '
    +'per-vehicle rate is claimed');
  if(r.verdict==='pooled') out.push('NOT COMPARABLE by band: '+r.why);
  if(r.verdict==='overlap') out.push('OVERLAPS: '+r.why);
  if(r.thin) out.push('LOW CONFIDENCE: '+r.thinWhy);
  return out;
}

/* ═══ the three chosen forms ═══════════════════════════════════════════════════════════════════
   Forms 2, 8 and 10 from the chart-forms gallery, on this page's real book: the pair with its
   difference, the small multiples on one shared scale, and the ranked table with the bar inside
   the cell. All three draw the same rows of the same level, so the toolbar swaps the view rather
   than stacking three charts - a reader cannot take two answers off one level.

   Percentages are on all three, and there are always two of them side by side:

     * change in billed euro      - how fast a row moved against itself;
     * change in euro per vehicle - how fast it moved against its own fleet.

   The second is the one that cannot mislead while the car park moves, and the pair is printed
   together everywhere because the two can only agree while the fleet stands still:
       (1 + change in euro) / (1 + change in euro per vehicle) = this fleet / last fleet
   The real case that proves it is in D.worked, computed by the build from the same source frames
   and printed on the page beside these forms, so the reader can check the arithmetic.

   The columns follow the measure switch (billed euro, euro per vehicle, units); the two printed
   percentages are always the euro pair, and each form's note says so.
*/
var FONT='-apple-system,Segoe UI,Roboto,Arial,sans-serif';
var PAIR_GUTTER=186;
var SML_CHARTS=[];
var FORM={key:'f2'};
/* the level a form draws, per row: this period, last period, the difference, and the size of the
   bar. A row that the page refuses to compare draws nothing at all rather than a zero. */
function colKey(){ return S.metric; }
function colLabel(){
  if(S.metric==='pv') return 'euro per vehicle';
  if(S.metric==='abs') return 'billed euro';
  return 'units';
}
function colLabelShort(){
  if(S.metric==='pv') return 'EUR / vehicle';
  if(S.metric==='abs') return 'EUR';
  return 'units';
}
function colNow(r){
  if(r.notComparable) return null;
  if(S.metric==='pv') return r.pv.ok? r.pv.rate1 : null;
  if(S.metric==='abs') return r.split.R1;
  return r.units1;
}
function colThen(r){
  if(r.notComparable) return null;
  if(S.metric==='pv') return r.pv.ok? r.pv.rate0 : null;
  if(S.metric==='abs') return r.split.R0;
  return r.units0;
}
/* ── the two percentages. Both are refused rather than guessed when the base is zero, and the
   per-vehicle one is refused when either period carries no fleet, which is the same refusal the
   four-term split makes one panel below. */
function rowPct(r){
  var eurP = (r.notComparable || !(r.eur0>0))? null : (r.eur1/r.eur0-1);
  var rateP = (r.notComparable || !r.pv.ok || !r.pv.rate0)? null : (r.pv.rate1/r.pv.rate0-1);
  return {eurPct:eurP, ratePct:rateP,
    gapPts:(eurP!==null&&rateP!==null)? 100*(rateP-eurP) : null,
    fleetPct:(r.f0&&r.f1)? (r.f1/r.f0-1) : null};
}
function pctTxt(v){ return v===null||v===undefined? 'n/a' : signpct(v); }
/* the one-line form used inside a chart annotation: the difference first, then the two
   percentages in the fixed order euro / per vehicle */
function pairOneLine(r){
  return sign(r.split.R1-r.split.R0)+'  '+pctTxt(rowPct(r).eurPct)
    +' / '+pctTxt(rowPct(r).ratePct);
}
function pairTwoLine(r){
  return [sign(r.split.R1-r.split.R0),
          pctTxt(rowPct(r).eurPct)+' / '+pctTxt(rowPct(r).ratePct)];
}
/* the html form, used in the table and in the small multiples. Both percentages, always, and the
   word before each one, so neither can be read as the other. */
function pctHTML(r, compact){
  var p=rowPct(r);
  if(r.notComparable) return '<span class="flat">not comparable</span>';
  var a=p.eurPct===null? '<span class="flat">n/a</span>'
     : '<span class="'+cls(p.eurPct)+'">'+signpct(p.eurPct)+'</span>';
  var b=p.ratePct===null? '<span class="flat">n/a</span>'
     : '<span class="'+cls(p.ratePct)+'">'+signpct(p.ratePct)+'</span>';
  return '<span class="k">'+(compact?'euro':'euro change')+'</span> '+a
    +'<br><span class="k">'+(compact?'per veh.':'per vehicle')+'</span> '+b;
}
function pointLabel(r){
  if(r.level==='fam') return byKey(D.families,r.key).short;
  if(r.level==='band') return byKey(D.bands,r.key).short;
  if(r.level==='cat') return byKey(D.cats,r.key).label;
  return String(D.pn.number[r.key]);
}
function pointFull(r){
  if(r.level==='fam') return byKey(D.families,r.key).label;
  if(r.level==='band') return byKey(D.bands,r.key).label;
  if(r.level==='cat') return byKey(D.cats,r.key).label;
  return byKey(D.cats,r.cat).label+' - '+D.pn.number[r.key];
}

/* ── form 2: the pair, the difference, and both percentages ──────────────────────────────────── */
function annotatePair(chart, recs){
  /* The annotation gets its own gutter, reserved through the chart's own left padding, so a number
     is never written over a bar. If the full string does not fit the gutter the annotation breaks
     onto two lines; the type size is fixed and never shrinks. */
  var ctx=chart.ctx, a=chart.chartArea;
  var m0=chart.getDatasetMeta(0), m1=chart.getDatasetMeta(1);
  if(!m1 || !m1.data) return;
  var room=a.right-a.left;
  if(room < 260) return;                    /* too narrow to annotate: the table carries them */  ctx.save();
  ctx.textAlign='left';
  m1.data.forEach(function(el,i){
    var r=recs[i];
    if(!r || el.y===null || el.y===undefined) return;
    var y0=m0.data[i]&&m0.data[i].y!==null? m0.data[i].y : el.y;
    var yTop=Math.min(el.y, y0);
    var yBase=Math.max(a.top+11, Math.min(yTop-7, a.bottom-4));
    /* the annotation sits in the gutter to the RIGHT of the plot, whose width is reserved through
       the chart's own right padding. Nothing is written over a bar, at any row. */
    var x=a.right+8;
    if(r.notComparable){
      ctx.font='600 10.5px '+FONT; ctx.fillStyle=MUTED;
      ctx.fillText('not comparable', x, yBase);
      return;
    }
    var p=rowPct(r);
    ctx.font='600 11px '+FONT;
    ctx.fillStyle = (p.eurPct!==null && p.eurPct<0) || (p.gapPts!==null && p.gapPts<-2)
      ? TERRA : INK;
    var one=pairOneLine(r);
    if(ctx.measureText(one).width <= PAIR_GUTTER-14){
      ctx.fillText(one, x, yBase);
    } else {
      var two=pairTwoLine(r);
      ctx.fillText(two[1], x, yBase);
      ctx.fillStyle=INK;
      ctx.fillText(two[0], x, yBase-13);
    }
  });
  ctx.restore();
}
var PAIR_TIPS=[];
function renderForm2(recs, lvl, pr){
  var y0=pr.bl.split(' ')[0], y1=pr.el.split(' ')[0];
  PAIR_TIPS=recs.map(function(r){
    var p=rowPct(r);
    return [pointFull(r),
      'billed '+eur(r.eur1)+' this period against '+eur(r.eur0)+' last period',
      'difference in billed euro '+(r.notComparable?'not comparable':sign(r.eur1-r.eur0)),
      'change in billed euro '+pctTxt(p.eurPct),
      'change in euro per vehicle '+pctTxt(p.ratePct)
        +(r.pv.ok? ' ('+eur2(r.pv.rate1)+' against '+eur2(r.pv.rate0)+')'
                 : ' - no fleet to divide by in one period'),
      'the fleet behind it '+n0(r.f1)+' against '+n0(r.f0)
        +(p.fleetPct===null?'':', '+signpct(p.fleetPct)),
      'the two percentages differ by '+((p.gapPts===null)?'n/a':p.gapPts.toFixed(1)+' points')].join('\n');
  });
  var labels=recs.map(pointLabel);
  guard('form 2, the pair', function(){
    var cfg={
      type:'bar',
      data:{labels:labels,datasets:[
        {label:y0, data:recs.map(colThen), backgroundColor:NAVY, borderWidth:0,
         categoryPercentage:0.7, barPercentage:0.86},
        {label:y1, data:recs.map(colNow), backgroundColor:TERRA, borderWidth:0,
         categoryPercentage:0.7, barPercentage:0.86}]},
      options:{
        indexAxis:'y', responsive:true, maintainAspectRatio:false, animation:false,
        layout:{padding:{right:PAIR_GUTTER, top:22}},
        plugins:{
          legend:{display:true, position:'top', align:'end',
            labels:{boxWidth:10, boxHeight:10, padding:10, color:INK, font:{size:11}}},
          tooltip:{backgroundColor:NAVY, titleColor:'#f0b49a', bodyColor:PAPER, padding:8,
            titleFont:{size:11.5}, bodyFont:{size:11},
            callbacks:{title:function(c){ return PAIR_TIPS[c[0].dataIndex].split('\n')[0]; },
              label:function(c){
                var lines=PAIR_TIPS[c.dataIndex].split('\n');
                return lines[c.datasetIndex+1]; }}}},
        /* indexAxis y: category labels on Y (left), values on X (bottom). Swapping these
           put Light vehicle… on the bottom axis and 0–4 on the left — FAIL. */
        scales:{
          x:{beginAtZero:true, grid:{color:LINE}, border:{display:false},
             title:{display:true, text:colLabel()+', this period against last period'},
             ticks:{color:MUTED, callback:function(v){ return S.metric==='units'? num(v):axisTick(v); }}},
          y:{grid:{display:false}, border:{display:false},
             ticks:{font:{size:10.5}, autoSkip:false, color:NAVY,
               callback:function(v,i){ var l=labels[i]||''; return l.length>28? l.slice(0,27)+'\u2026':l; }}}}},
      plugins:[{id:'pairAnn', afterDatasetsDraw:function(ch){ annotatePair(ch, recs); }}]
    };
    mk('c_main', cfg, function(i){ drill(i); }, function(){ climb(); });
  });
  document.getElementById('l_pair').innerHTML=
    '<span><i style="background:'+NAVY+'"></i><b>'+y0+'</b></span>'
    +'<span><i style="background:'+TERRA+'"></i><b>'+y1+'</b></span>'
    +'<span>printed beside each pair, in this order: <b>the difference in '+colLabel()
    +'</b>, <b>the change in billed euro</b>, <b>the change in euro per vehicle</b></span>'
    +'<span>'+colLabel()+' on the axis &middot; one shared scale for every row</span>';
  document.getElementById('cap-f2').innerHTML='The columns follow the measure switch, which is on '
    +'<b>'+measureName()+'</b>. Both printed percentages are the euro pair and do not change with '
    +'the measure: <b>euro</b> is this period against last period on the same book, <b>per vehicle</b> '
    +'is the same comparison after each period is divided by its own fleet. Where those two disagree, '
    +'the fleet moved - the case worked through beside this panel. Click a bar to open the level '
    +'beneath it, or right-click to come back one level.';
}

/* ── form 8: small multiples on ONE shared euro scale ────────────────────────────────────────── */
function niceMax(v){
  if(!(v>0) || !isFinite(v)) return 1;
  var p=Math.pow(10,Math.floor(Math.log10(v))), m=v/p;
  var s = m<=1?1 : m<=1.5?1.5 : m<=2?2 : m<=2.5?2.5 : m<=3?3 : m<=4?4 : m<=5?5 : m<=7.5?7.5 : 10;
  return s*p;
}
/* The panel's own value line. The plain thousand-formatter rounds a per-vehicle rate to a whole
   euro, so 21.4 and 20.7 both printed as "21" and a row that fell 3% read as "21 was 21". Below a
   hundred, a per-vehicle figure is shown to one decimal. */
function fmtMeasure(v){
  if(v===null||v===undefined||!isFinite(v)) return 'n/a';
  if(S.metric==='units') return num(v);
  if(S.metric==='pv') return Math.abs(v)<100 ? v.toFixed(1) : axisTick(v);
  return axisTick(v);
}
/* the panel's own axis, which can only be a small number when every rate on the level is small */
function fmtPanelTick(v){
  if(v===0) return '0';
  if(S.metric==='pv' && Math.abs(v)<10) return v.toFixed(1);
  return fmtMeasure(v);
}
function renderForm8(recs, lvl, pr){
  SML_CHARTS.forEach(function(c){ try{ c.destroy(); }catch(e){} });
  SML_CHARTS=[];
  var host=document.getElementById('smlGrid');
  var ticks=[];
  recs.forEach(function(r){ [colNow(r),colThen(r)].forEach(function(v){ if(v!==null) ticks.push(v); }); });
  var peak=ticks.length? Math.max.apply(null,ticks) : 1;
  var top=niceMax(peak);
  var step=top/2;
  document.getElementById('smlScale').innerHTML='<span class="leaf">every panel is drawn on the '
    +'same scale, 0 to '+fmtPanelTick(top)+' '+colLabelShort()+', so no vehicle type can be made to '
    +'look dramatic by its own axis</span><span class="leaf">0</span>'
    +'<span class="bar"><i style="left:50%"></i><b style="right:0"></b></span>'
    +'<span class="leaf">'+fmtPanelTick(top)+'</span>';
  var y0=pr.bl.split(' ')[0], y1=pr.el.split(' ')[0];
  if(!recs.length){ host.innerHTML='<div class="formnote">Nothing to draw at this level.</div>'; return; }
  host.innerHTML=recs.map(function(r,i){
    var name='sml_'+i;
    return '<div class="smlPanel" data-i="'+i+'">'
      +'<div class="h" title="'+pointFull(r).replace(/"/g,'')+'">'+pointLabel(r)+'</div>'
      +'<div class="c"><canvas id="'+name+'"></canvas></div>'
      +'<div class="pct">'+pctHTML(r,true)+'</div>'
      +'<div class="pct"><span class="k">'+colLabelShort()+'</span> '
        +(r.notComparable? '<span class="flat">-</span>'
          : '<span class="v">'+fmtMeasure(colNow(r))+'</span>'
            +' <span class="k">was</span> <span class="v">'+fmtMeasure(colThen(r))+'</span>')
      +'</div></div>';
  }).join('');
  recs.forEach(function(r,i){
    var el=document.getElementById('sml_'+i);
    if(!el) return;
    var tip=[pointFull(r),
      'this period '+ (r.notComparable?'not comparable'
        : (S.metric==='units'? num(colNow(r)) : eur2(colNow(r)))),
      'last period '+ (r.notComparable?'not comparable'
        : (S.metric==='units'? num(colThen(r)) : eur2(colThen(r)))),
      'difference '+(r.notComparable?'not comparable':sign(r.eur1-r.eur0)+' billed'),
      'change in billed euro '+pctTxt(rowPct(r).eurPct),
      'change in euro per vehicle '+pctTxt(rowPct(r).ratePct),
      'fleet '+n0(r.f1)+' against '+n0(r.f0)+', so the two percentages part company here']
      .join('\n');
    var c;
    try{
      c=new Chart(el.getContext('2d'), {
        type:'bar',
        data:{labels:[y0,y1], datasets:[{data:[colThen(r),colNow(r)],
          backgroundColor:[NAVY,TERRA], borderWidth:0, categoryPercentage:0.72, barPercentage:0.88}]},
        options:{responsive:true, maintainAspectRatio:false, animation:false,
          layout:{padding:{top:16, right:6}},
          plugins:{legend:{display:false},
            tooltip:{backgroundColor:NAVY, titleColor:'#f0b49a', bodyColor:PAPER, padding:8,
              titleFont:{size:11}, bodyFont:{size:10.5},
              callbacks:{title:function(){ return pointFull(r); },
                label:function(c2){ return (c2.label===y1?'this period ':'last period ')
                  + (S.metric==='units'? num(c2.parsed.y) : eur2(c2.parsed.y)); },
                afterBody:function(){ return [tip.split('\n').slice(4).join('\n')]; }}}},
          scales:{
            x:{grid:{display:false}, border:{display:false},
               ticks:{font:{size:9.5}, color:MUTED, autoSkip:false}},
            y:{beginAtZero:true, max:top, grid:{color:LINE}, border:{display:false},
               ticks:{color:MUTED, font:{size:9}, stepSize:step,
                 callback:function(v){ return fmtPanelTick(v); }}}}},
        plugins:[{id:'smlCap'+i, afterDatasetsDraw:function(ch){
          /* the difference is printed on the panel itself, not left to the tooltip, and so are both
             percentages - this is the panel where the raw percentage would mislead */
          var ctx=ch.ctx, a=ch.chartArea, meta=ch.getDatasetMeta(0);
          ctx.save();
          ctx.font='700 10px '+FONT; ctx.textAlign='left'; ctx.textBaseline='bottom';
          meta.data.forEach(function(bar,bi){
            if(bar.y===null) return;
            var t=fmtMeasure(ch.data.datasets[0].data[bi]);
            if(bar.y-13 < a.top) return;
            ctx.fillStyle=INK;
            ctx.fillText(t, bar.x-ctx.measureText(t).width/2, bar.y-2);
          });
          ctx.restore();
        }}]
      });
      SML_CHARTS.push(c);
    }catch(e){ PANEL_ERR.push('small multiple '+i+': '+String(e&&e.message?e.message:e)); }
  });
  document.getElementById('cap-f8').innerHTML='One panel per row, each with its own two columns, '
    +'its difference in '+colLabel()+', and <b>both percentages printed on the panel itself</b> - not '
    +'in a tooltip, because this is the form where a raw percentage would mislead. Every panel shares '
    +'the same axis ('+fmtPanelTick(top)+' '+colLabelShort()+'), so the heights compare across rows and no '
    +'row can be given a flattering axis of its own. A row the page refuses to compare says so in '
    +'place of its figures rather than drawing a zero. Click a panel to open the level beneath it; '
    +'right-click a panel to come back one level.';
}

/* ── form 10: the ranked table with the bar inside the cell ─────────────────────────────────── */
function renderForm10(recs, lvl, pr){
  var y0=pr.bl.split(' ')[0], y1=pr.el.split(' ')[0];
  var peakEur=0;
  recs.forEach(function(r){ if(!r.notComparable) peakEur=Math.max(peakEur, Math.abs(r.split.R1), Math.abs(r.split.R0)); });
  if(!peakEur) peakEur=1;
  var nameCol = lvl==='pn'? 'Part number' : lvl==='cat'? 'Service family'
              : lvl==='band'? 'Tonnage band' : 'Vehicle type';
  /* This table is the one form that carries both currencies of the book at once, so its columns
     have fixed meanings: the first three are always billed euro, the next two are always the two
     percentage changes, and the three after that are always units. It therefore does not follow
     the measure switch, and its caption says so rather than leaving a header that names one unit
     over cells holding another. */
  var head=['#',nameCol,'Billed EUR this period','Billed EUR last period','EUR difference',
    'Change in billed euro','Change in euro per vehicle','Units this period','Units last period',
    'Unit difference','Fleet this period','Fleet last period','Fleet change','Read'];
  document.getElementById('tbl10').tHead.innerHTML='<tr>'
    +head.map(function(h,i){ return '<th class="'+(i?'n':'')+'">'+h+'</th>'; }).join('')+'</tr>';
  document.getElementById('tbl10').tBodies[0].innerHTML=recs.map(function(r,i){
    var w1=Math.max(2, Math.round(100*Math.abs(r.notComparable?0:r.split.R1)/peakEur));
    var w0=Math.max(2, Math.round(100*Math.abs(r.notComparable?0:r.split.R0)/peakEur));
    var p=rowPct(r);
    var read;    if(r.notComparable) read='<span class="pill nc">not comparable</span> the period is incomplete';
    else if(r.noWalletRow) read='<span class="pill nc">no fleet to divide by</span>';
    else if(r.verdict==='pooled') read='<span class="pill pooled">not comparable by band</span> '+r.why;
    else if(r.verdict==='overlap') read='<span class="pill pooled">overlaps the bands</span> '+r.why;
    else if(r.thin) read='<span class="pill thin">low confidence</span> '+r.thinWhy;
    else if(p.gapPts!==null && Math.abs(p.gapPts)>=2)
      read='<span class="pill thin">the fleet moved</span> euro and per vehicle disagree by '
        +Math.abs(p.gapPts).toFixed(1)+' points, so read the per-vehicle column';
    else read=readText(r);
    return '<tr class="clickable" data-i="'+i+'">'
      +'<td class="n" style="color:#8b93a3">'+(i+1)+'</td>'
      +'<td><b>'+pointFull(r)+'</b></td>'
      +'<td class="n c_now"><div class="cellbar-wrap"><span class="n">'+axisTick(r.notComparable?0:r.split.R1)
        +'</span><span class="cellbar" style="width:'+w1+'%"></span></div></td>'
      +'<td class="n c_then"><div class="cellbar-wrap"><span class="n">'+axisTick(r.notComparable?0:r.split.R0)
        +'</span><span class="cellbar" style="width:'+w0+'%;opacity:.55"></span></div></td>'
      +'<td class="n '+(r.notComparable?'flat':cls(p.eurPct))+' c_diff">'
        +(r.notComparable? '&mdash;' : sign(r.eur1-r.eur0))+'</td>'
      +'<td class="n '+(p.eurPct===null?'flat':cls(p.eurPct))+' c_eurpct">'+pctTxt(p.eurPct)+'</td>'
      +'<td class="n '+(p.ratePct===null?'flat':cls(p.ratePct))+' c_ratepct">'+pctTxt(p.ratePct)
        +(p.gapPts!==null? '<div class="caption">'+p.gapPts.toFixed(1)+' pts from euro</div>':'')+'</td>'
      +'<td class="n">'+num(r.units1)+'</td>'
      +'<td class="n">'+num(r.units0)+'</td>'
      +'<td class="n '+(r.notComparable?'flat':cls(r.units1-r.units0))+'">'
        +(r.notComparable? '&mdash;' : sign(r.units1-r.units0))+'</td>'
      +'<td class="n">'+n0(r.f1)+'</td><td class="n">'+n0(r.f0)+'</td>'
      +'<td class="n '+(p.fleetPct===null?'flat':cls(p.fleetPct))+'">'+pctTxt(p.fleetPct)+'</td>'
      +'<td>'+read+'</td></tr>';
  }).join('');
  document.getElementById('cap-f10').innerHTML='Ranked by billed euro this period, with the bar '
    +'inside each of the first two columns drawn against the largest row in the table ('
    +(peakEur?axisTick(peakEur):'n/a')+'), not against the total, so the rows are comparable to each '
    +'other. <b>These columns do not follow the measure switch above</b>, because this is the only '
    +'one of the three forms that has to carry euro and units in the same row: the first three '
    +'columns are always billed euro, the next two are always the two percentage changes, and the '
    +'three after those are always units. Both percentages are here for that reason: '
    +'<b>change in billed euro</b> and <b>change in euro per vehicle</b>. A unit is an ingredient '
    +'rather than a finding - read it with the service family and the fleet in the next two columns. '
    +'Click a row to open the level beneath it.';
}

/* ── the switcher ─────────────────────────────────────────────────────────────────────────────
   The three buttons are named for the question each view answers, not for the chart type, so the
   control reads as "which of my questions do you want answered" rather than "pick a picture". The
   gallery form each one came from is in the button's own tooltip and in the caption under it. */
var FORM_TITLES={
  f2:'This year against last year, row by row',
  f8:'Every row on one scale at a glance',
  f10:'The ranked detail, euro and units together'
};
var FORM_NAMES={
  f2:'two columns and the difference',
  f8:'small multiples',
  f10:'the ranked table with bars in the cells'
};
function renderForms(recs, lvl, pr){
  guard('form 2', function(){ renderForm2(recs, lvl, pr); });
  guard('form 8', function(){ renderForm8(recs, lvl, pr); });
  guard('form 10', function(){ renderForm10(recs, lvl, pr); });
  applyForm();
}
function applyForm(){
  var key=FORM.key;
  ['f2','f8','f10'].forEach(function(k){
    var v=document.getElementById('view-'+k);
    if(v) v.classList.toggle('on', k===key);
  });
  document.querySelectorAll('#segForm button').forEach(function(b){
    b.classList.toggle('on', b.getAttribute('data-f')===key); });
  var h=document.getElementById('formhint');
  if(h) h.textContent='Showing: '+FORM_TITLES[key]+' ('+FORM_NAMES[key]+'). Opening view: '
    +FORM_TITLES.f2+', because it is the only one of the three that shows both periods as billed '
    +'with the difference and both percentages beside them';
  if(FORM.key!=='f2'){ /* charts in a hidden box have no measurable width; only the visible one is
      left sized by Chart.js's own resize observer, so a swap needs no redraw. */ }
  Object.keys(charts).forEach(function(id){
    var c=charts[id];
    if(c && c.resize) { try{ c.resize(); }catch(e){} }
  });
}
function setForm(k){
  FORM.key=k;
  applyForm();
}

/* ── the worked case, printed beside the forms so the reader can check the arithmetic ────────── */
function renderWorked(){
  var el=document.getElementById('worked');
  if(!el) return;
  var w=D.worked||{}, ex=w.examples||[], trap=w.trap||ex[0];
  if(!ex.length){ el.innerHTML='<div class="formnote">not available on this build</div>'; return; }
  document.getElementById('q-worked').innerHTML='The same book read against two denominators. '
    +'These are the build\'s own figures from the same source files the charts use, so the '
    +'arithmetic can be checked by hand.';
  var rows=ex.map(function(e){
    return '<tr><td><b>'+e.name+'</b><div class="caption">'+e.familyLabel+' &middot; '
      +e.years[0]+' to '+e.years[1]+'</div></td>'
      +'<td class="n">'+eur(e.eur0)+'<div class="caption">'+n0(e.fleet0)+' vehicles</div></td>'
      +'<td class="n">'+eur(e.eur1)+'<div class="caption">'+n0(e.fleet1)+' vehicles</div></td>'
      +'<td class="n '+cls(e.eurPct)+'">'+signpct(e.eurPct)+'</td>'
      +'<td class="n '+cls(e.ratePct)+'">'+signpct(e.ratePct)+'</td>'
      +'<td class="n">'+(e.gapPts>0?'+':'')+e.gapPts.toFixed(1)+' pts</td></tr>';
  }).join('');
  var t=trap;
  el.innerHTML='<table><thead><tr><th>Book</th><th class="n">Billed euro, first year</th>'
    +'<th class="n">Billed euro, second year</th><th class="n">Change in euro</th>'
    +'<th class="n">Change in euro per vehicle</th><th class="n">How far apart</th></tr></thead>'
    +'<tbody>'+rows+'</tbody></table>'
    +'<div class="formnote">The bottom line of each row is the fleet, because that is the whole '
    +'reason the two percentages exist. <b>'+t.name+', '+t.familyLabel+', '+t.years[0]+' to '
    +t.years[1]+':</b> billed euro '+signpct(t.eurPct)+' while the fleet moved '
    +signpct(t.fleetPct)+', so euro per vehicle is '+signpct(t.ratePct)+'. '
    +'Same book, two opposite instructions: '+eur(t.eur0)+' over '+n0(t.fleet0)+' vehicles is '
    +eur2(t.rate0)+' each, and '+eur(t.eur1)+' over '+n0(t.fleet1)+' is '+eur2(t.rate1)+' each. '
    +'The two can only agree while the fleet does not move, because '
    +'<b>'+(w.identity||'')+'</b> &mdash; here '+((1+t.eurPct)/(1+t.ratePct)).toFixed(4)
    +' on the left and '+(t.fleetRatio).toFixed(4)+' on the right. That is why no form on this page '
    +'prints one of the two percentages without the other.</div>';
}

/* ── the static panels ──────────────────────────────────────────────────────────────────────── */
function renderStatic(pr, lvl){
  guard('the worked case', function(){ renderWorked(); });
  /* ── the competitor-price panel ───────────────────────────────────────────────────────────── */
  var cr=D.competitor.rows||[], meta=D.competitor.meta||{rows:0,allRows:0};
  var keep=cr.filter(function(r){
    if(SEL_MK.size && !SEL_MK.has(r[1])) return false;
    if(S.fam && S.fam==='n_series_truck' && S.band && BAND_KEYS[r[2]]!==S.band) return false;
    if(S.fam && S.fam!=='n_series_truck' && FAM_KEYS[D.pn.fam[r[0]]]!==S.fam) return false;
    return true;
  });
  var agg=new Map();
  keep.forEach(function(r){ var k=r[2]<0? '_none' : BAND_KEYS[r[2]];
    var o=agg.get(k); if(!o){ o={k:k, n:0, pos:0, idx:[], euro:0}; agg.set(k,o); }
    o.n++; if(r[4]>1) o.pos++; o.idx.push(r[4]); o.euro+=r[5]; });
  var rows=Array.from(agg.values()).sort(function(a,b){
    var ma=a.idx.reduce(function(s,v){return s+v;},0)/a.n,
        mb=b.idx.reduce(function(s,v){return s+v;},0)/b.n;
    return mb-ma; });
  var plabels=rows.map(function(r){ return r.k==='_none'?'No band on this page'
    : byKey(D.bands,r.k).label; });
  var pvals=rows.map(function(r){
    var m=r.idx.reduce(function(s,v){return s+v;},0)/r.n; return (m-1)*100; });
  var ptips=rows.map(function(r){
    var m=r.idx.reduce(function(s,v){return s+v;},0)/r.n;
    return ['median '+m.toFixed(3)+' times the competing price ('+(100*(m-1)).toFixed(1)+'% above)',
      r.n+' part numbers, '+r.pos+' of them above the competing price',
      eur(r.euro)+' billed on those part numbers in the period this page compares']; });
  guard('the competitor-price panel', function(){
    var cfgPrice={
      type:'bar',
      data:{labels:plabels,datasets:[{
        data:pvals,borderRadius:2,
        backgroundColor:pvals.map(function(v){ return v>0? TERRA : GOOD; })}]},
      options:{
        indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:false,
        plugins:{
          legend:{display:false},
          tooltip:{backgroundColor:NAVY,titleColor:'#f0b49a',bodyColor:PAPER,padding:8,
            titleFont:{size:11.5},bodyFont:{size:11},
            callbacks:{label:function(c){ return ptips[c.dataIndex]; }}}},
        scales:{
          x:{grid:{color:LINE},
            title:{display:true,text:'price index against the competing price (percent, 0 = level)'},
            ticks:{callback:function(v){ return (v>0?'+':'')+v+'%'; }}},
          y:{grid:{display:false},ticks:{font:{size:10.5}}}}}
    };
    mk('c_price', cfgPrice, function(i){
      var k=rows[i].k;
      if(k==='_none') return;
      S.fam='n_series_truck'; S.band=k; S.cat=null; render();
    }, function(){ climb(); });
  });
  document.getElementById('cap-price').innerHTML=(meta.rows||0)+' of '+(meta.allRows||0)
    +' priced part numbers could be placed in a band on this page and '+(SEL_MK.size?
      'in the selected customers':'across all customers')+'. Source: '+(meta.source||'not stated')
    +', vintage '+(meta.vintage||'not stated')+'. '+(meta.note||'')+'. This is a list-price '
    +'comparison on a fixed sample, not a slice of the billing above, and it is the one figure here '
    +'that is not derived from the two charts.';

  /* ── the fleet panel ──────────────────────────────────────────────────────────────────────── */
  var rowsF='', total0=0, total1=0, inBand=false;
  markets().forEach(function(m){
    var y0=(D.fleet[m]||{})[String(pr.b)]||{}, y1=(D.fleet[m]||{})[String(pr.e)]||{};
    var f=D.flat[m]||{};
    var key = S.band? 'n_series' : (S.fam==='n_series_truck'? 'n_series'
      : (S.fam==='heavy_truck'? 'heavy' : (S.fam==='light_vehicle'? 'light' : 'total')));
    if(S.band) inBand=true;
    var v0 = S.band? (y0.n_series||0) : (y0[key]||0);
    var v1 = S.band? (y1.n_series||0) : (y1[key]||0);
    var fv = S.band? (f.n_series||0) : (f[key]||0);
    total0+=v0; total1+=v1;
    rowsF+='<tr><td><b>'+m+'</b></td><td>'+n0(v0)+'</td><td>'+n0(v1)+'</td>'
      +'<td class="'+cls(v1-v0)+'">'+sign(v1-v0)+'</td>'
      +'<td>'+n0(fv)+'</td><td>'+(y1.basis||'n/a')+'</td></tr>';
  });
  document.getElementById('t_fleet').tHead.innerHTML='<tr><th>Customer</th><th class="n">'
    +pr.bl.split(' ')[0]+'</th><th class="n">'+pr.el.split(' ')[0]+'</th><th class="n">change</th>'
    +'<th class="n">const 2025</th><th>basis</th></tr>';
  document.getElementById('t_fleet').tBodies[0].innerHTML=rowsF
    +'<tr style="font-weight:600"><td>All selected</td><td class="n">'+n0(total0)+'</td>'
    +'<td class="n">'+n0(total1)+'</td><td class="n '+cls(total1-total0)+'">'+sign(total1-total0)
    +'</td><td class="n">&mdash;</td><td></td></tr>';
  document.getElementById('cap-fleet').innerHTML='Showing the '
    +(S.band? 'whole N-series fleet of each market, because the weight split of it is the band panel '
        +'above' : (S.fam? byKey(D.families,S.fam).label+' fleet' : 'whole fleet'))
    +'. It is the workbook\'s own count, per market and per year, with each year\'s basis stated: '
    +'<b>measured</b> to 2024, <b>estimated</b> for 2025. From 2026 the workbook carries forward '
    +'figures that are <b>not quoted as forecasts</b> and are blocked for per-vehicle rates unless you '
    +'switch to the constant 2025 fleet analytical alternative. The flat 2025 column is that '
    +'single-vintage estimate, not a forward forecast. The 3.5 t share of the N-series fleet is that '
    +'workbook\'s own measured rate per market, not an assumption, and '
    +(NEVER_BANDED.length? NEVER_BANDED.join(', ')+' carries its N-series as one row with no weight '
      +'class, so that fleet is excluded from the band denominators rather than divided by a rate that '
      +'applies to a weight class it does not have.':'no market on this page is missing a weight class.');

  /* ── what cannot be said: one line each, with the number attached ─────────────────────────── */
  var lim=[];
  var fc=(D.filterEur||0);
  lim.push('<b>Filters cannot be split by tonnage</b> &mdash; one oil filter fits NLR, NMR, NPR and '
    +'NNR, so there is no 3.5 t filter to compare with a 7.5 t filter. The page shows the pooled '
    +'figure; '+eur(fc)+' of N-series filter euro sits on part numbers that fit more than one band.');
  var nv=D.noVehicleRef||{eur:0,pns:0,units:0,dealers:0,topCats:[]};
  lim.push('<b>'+eur(nv.eur)+' has no vehicle reference at all</b> &mdash; '+n0(nv.pns)
    +' part numbers, '+n0(nv.units)+' units, billed to '+nv.dealers+' customers. '
    +(nv.topCats&&nv.topCats.length? 'Largest service families: '+nv.topCats.slice(0,3).map(function(c){
        return c.label.toLowerCase()+'s ('+eur(c.euro)+', '+n0(c.units)+' units)'; }).join(', ')
      +'. ' : '')
    +'No source on disk names a vehicle for these, so they appear as their own row rather than being '
    +'spread across the vehicle types.');
  var we=D.weightEvidence||{};
  lim.push('<b>The tonnage weights come from two sources that agree</b> &mdash; '
    +'the maintenance schedules and the interval table both place NLR at 3.5 t, NMR at 5.5 t and NPR '
    +'and NNR at 7.5 t. '+(we.unresolvedCodesCount? we.unresolvedCodesCount+' chassis codes are not '
      +'weights at all: '+we.unresolvedCodes.slice(0,8).join(', ')
      +(we.unresolvedCodesCount>8?' and others':'')+' are wildcard fragments from the cross-reference, '
      +'not model codes. ':'')
    +(we.noSeriesPns? n0(we.noSeriesPns)+' part numbers carry no series in either source, worth '
      +eur(we.unresolvedEur)+', and are held in a "tonnage not stated" row rather than guessed into a '
      +'band. ':''));
  if(NEVER_BANDED.length){
    lim.push('<b>'+NEVER_BANDED.join(', ')+' cannot be banded</b> &mdash; its fleet row is the whole '
      +'N-series at 6.5/7.5 t, not a weight class, so that fleet comes out of every band denominator '
      +'above instead of being divided by a rate that does not fit it.');
  }
  var held=pr.held||[];
  if(held.length){
    lim.push('<b>'+(held.map(function(h){ return h.label; }).join(', '))+' is incomplete</b> &mdash; it '
      +'holds only '+held[0].months+' months of billing, so it is listed and held out of every '
      +'comparison rather than shown as a fall.');
  }
  lim.push('<b>Mix is a service-family effect</b> &mdash; a single part number has no mix term of its '
    +'own, so at part-number level the move splits into volume and price only and mix is shown one '
    +'level up, where the basket can actually change.');
  lim.push('<b>A unit is an ingredient, not a finding</b> &mdash; every unit figure on this page '
    +'carries the service family it belongs to and the fleet it was sold against, because the same '
    +'number of pieces means opposite things in a large and a small market.');
  lim.push('<b>The two interval lanes are never averaged</b> &mdash; '+(D.lane? (function(){
      var iml=[]; Object.keys(D.lane).forEach(function(m){ if(D.lane[m]==='iml') iml.push(m); });
      return iml.join(', '); })() : 'one market')+' runs the schedule agreed for that market, at 1.25 '
    +'filter visits a year and 0.5 clutch and brake visits, against 0.5 for standard trucks on the '
    +'internal schedule. They answer different questions about the same fleet, so no figure here adds '
    +'them together.');
  document.getElementById('t_limits').innerHTML=lim.map(function(s){ return '<li>'+s+'</li>'; }).join('');
  document.getElementById('cap-limits').innerHTML='Each limit is decided from the published files and '
    +'carries the size of the business it affects, rather than a disclaimer on every panel.';

  /* ── the evidence, in a folded block rather than a page section ───────────────────────────── */
  var ev='';
  ev+='<details class="card" id="evbox"><summary style="cursor:pointer;font-family:Georgia,serif;'
    +'color:#15233c;font-size:15px">Evidence and method &mdash; open only if you need to check the '
    +'working</summary>'
    +'<div style="margin-top:8px">';
  ev+='<h3>Which series carries each band, and on whose word</h3>'
    +'<table style="margin-top:5px"><thead><tr><th>Band</th><th>Series</th><th>Confidence</th>'
    +'<th>Source</th></tr></thead><tbody>'
    +D.bands.slice(0,3).map(function(b){
      var rows=D.weightEvidence.settled.filter(function(s){ return s.band===b.key; });
      if(!rows.length) return '';
      return '<tr><td><b>'+b.label+'</b></td><td>'+rows.map(function(r){ return r.series; }).join(', ')
        +'</td><td>'+rows.map(function(r){ return r.confidence; }).join(', ')
        +'</td><td>'+(D.weightEvidence.sources||[]).slice(0,2).join(' | ')+'</td></tr>';
    }).join('')+'</tbody></table>'
    +'<div class="caption">This is the builder\'s evidence, kept so the banding can be checked. It is '
    +'not a page section, and the confidence column is not a reader-facing judgement: the weights '
    +'above are the only ones any chart on this page uses.</div>';
  if(D.weightEvidence.unresolvedCodes.length){
    ev+='<h3 style="margin-top:10px">Chassis codes that are not weights</h3><p class="caption">'
      +D.weightEvidence.unresolvedCodes.length+' fragments in the cross-reference\'s vehicle field do '
      +'not decode as a tonnage, because they are partial codes rather than model codes: '
      +D.weightEvidence.unresolvedCodes.join(', ')+'. Part numbers whose only series is one of these '
      +'are held in the "tonnage not stated" row and are never guessed into a band.</p>';
  }
  ev+='<h3 style="margin-top:10px">The tie-out on every number on the page</h3><ul class="tight">'
    +'<li>Every euro is derived at part-number grain from the billing published by the project\'s own '
    +'tagging path, and the build asserts it back to the published family totals'
    +(D.meta.ties&&D.meta.ties[0]? ' on '+D.meta.ties[0].rows+' customer x family x year rows, largest '
      +'difference '+eur2(D.meta.ties[0].worst)+', and the whole book of '+eur(D.meta.bookBilled)
      +' both ways':'')+'.</li>'
    +'<li>The volume / price / mix split is the method already in this workspace, with price taken one '
    +'level above the mix axis, so the mix term is a real effect and not an identity. On the build '
    +'date it is non-zero at every level: '
    +Object.keys(D.splitCheck||{}).map(function(k){ var s=D.splitCheck[k];
        return k+' '+eur(s.mix); }).join(', ')+'.</li>'
    +'<li>Vehicle-type resolution: '+(D.meta.familyResolution
      ? ((D.meta.familyResolution.resolved_single_family||'?')+' part numbers resolve to one vehicle '
        +'type, '+(D.meta.familyResolution.pooled_shared||'?')+' fit more than one and are pooled, and '
        +(D.meta.familyResolution.unattributed||'?')+' carry no vehicle reference at all')
      : 'not stated')+'.</li>'
    +'<li>The banding decision per service family is measured, not assumed: a service family is '
    +'refused a band split when no part number in it fits one band only, or when more than half its '
    +'euro sits on shared part numbers'
    +((D.cats||[]).filter(function(c){
        var v=(D.comparability[S.clock]||{})[c.key]||{}; return v.verdict==='pooled'; }).length
      ? ': '+D.cats.filter(function(c){
          var v=(D.comparability[S.clock]||{})[c.key]||{}; return v.verdict==='pooled'; })
        .map(function(c){ return c.label; }).join(', ')+' are refused on the '+S.clock
        +' clock for that reason.'
      : '.')+'</li></ul>';
  ev+='</div></details>';
  document.getElementById('evidence').innerHTML=ev;

  document.getElementById('foot').innerHTML='<b>Snapshot '+D.snapshot+', built '+D.generated
    +'.</b> Opens from Explorer with no server and no internet: the data and the charts are inside '
    +'the file. Sources and the reconciliation behind every figure are in the evidence block above.';
}

/* ── the controls ───────────────────────────────────────────────────────────────────────────── */
function custList(){ return Array.prototype.slice.call(document.getElementById('selCust').options); }
function chosenMarkets(){ return custList().filter(function(o){ return o.selected; })
  .map(function(o){ return o.value; }); }
function syncCust(){
  var sel=new Set(chosenMarkets());
  var meta=document.getElementById('custMeta');
  if(!meta) return;
  var n=sel.size;
  meta.textContent = n===0
    ? ('all '+D.markets.length)
    : (n+' of '+D.markets.length+' selected'
       +(n<=3? ': '+Array.from(sel).join(', ') : ''));
}
function readCust(){
  var v=chosenMarkets();
  SEL_MK.clear();
  v.forEach(function(m){ var i=D.markets.indexOf(m); if(i>=0) SEL_MK.add(i); });
  syncCust();
}
function buildControls(){
  var sc=document.getElementById('selCust');
  sc.innerHTML=D.markets.map(function(m){
    return '<option value="'+m+'">'+m+'</option>'; }).join('');
  /* Ctrl-click gives several, a plain click gives one, and Ctrl-clicking a selected row takes it
     back out. Which of those the browser itself performs differs between platforms - Windows
     toggles on ctrl-click, macOS collapses the list - so the selection in force is captured before
     the click and re-applied once it has settled. That makes the behaviour the same everywhere and
     independent of what the platform does in between. */
  var before=null, target=null;
  sc.addEventListener('mousedown',function(e){
    var o=e.target;
    if(!o||o.tagName!=='OPTION') return;
    before=chosenMarkets();
    target=o;
  }, true);
  sc.addEventListener('mouseup',function(e){
    var o=e.target;
    if(!o||o.tagName!=='OPTION'||before===null||target!==o) return;
    var want;
    if(e.ctrlKey||e.metaKey){
      want=before.slice();
      var at=want.indexOf(o.value);
      if(at>=0) want.splice(at,1); else want.push(o.value);
    } else {
      want=[o.value];
    }
    custList().forEach(function(x){ x.selected=(want.indexOf(x.value)>=0); });
    before=null; target=null;
    readCust(); render();
  });
  sc.addEventListener('change',function(){ readCust(); render(); });
  document.getElementById('btnAll').addEventListener('click',function(){
    custList().forEach(function(o){ o.selected=true; }); readCust(); render(); });
  document.getElementById('btnNone').addEventListener('click',function(){
    custList().forEach(function(o){ o.selected=false; }); readCust(); render(); });
  document.getElementById('btnItuk').addEventListener('click',function(){
    custList().forEach(function(o){ o.selected=(o.value==='ITUK'); }); readCust(); render(); });
  syncCust();

  var sf=document.getElementById('selFam');
  sf.innerHTML='<option value="">All vehicle types</option>'+D.families.map(function(f){
    return '<option value="'+f.key+'">'+f.label+'</option>'; }).join('');
  sf.addEventListener('change',function(){ S.fam=sf.value||null; S.band=null; S.cat=null; render(); });

  var sc=document.getElementById('selClock');
  sc.innerHTML=Object.keys(D.clocks).map(function(c){
    return '<option value="'+c+'">'+D.clocks[c].long+'</option>'; }).join('')
    +heldOptions();
  sc.value='CY';
  sc.addEventListener('change',function(){
    if(!sc.value) { sc.value=S.clock; return; }
    S.clock=sc.value; render(); });
  document.getElementById('tipClock').innerHTML='<b>The two clocks</b><br><b>Calendar year</b>: '
    +'January to December, so CY2025 is compared with CY2024.<br><b>ISZE year</b>: April to March, '
    +'named by the closing year, so FY2026 = April 2025 - March 2026 and is compared with FY2025 = '
    +'April 2024 - March 2025.<br>Both sides of every comparison hold the same months. A period with '
    +'fewer than twelve months is listed but cannot be selected, and is never compared as though it '
    +'were a year.';

  document.getElementById('segMetric').innerHTML=D.metrics.map(function(m){
    return '<button data-m="'+m.key+'"'+(m.key===S.metric?' class="on"':'')+'>'+m.label
      +'</button>'; }).join('');
  document.querySelectorAll('#segMetric button').forEach(function(b){
    b.addEventListener('click',function(){
      S.metric=b.getAttribute('data-m');
      document.querySelectorAll('#segMetric button').forEach(function(x){ x.classList.toggle('on',x===b); });
      render(); }); });

  document.getElementById('segFleet').innerHTML=
    '<button data-d="own" class="on">Each period\'s own fleet</button>'
    +'<button data-d="flat">Constant 2025 fleet (analytical)</button>';
  document.querySelectorAll('#segFleet button').forEach(function(b){
    b.addEventListener('click',function(){
      if(b.disabled) return;
      S.denom=b.getAttribute('data-d');
      document.querySelectorAll('#segFleet button').forEach(function(x){ x.classList.toggle('on',x===b); });
      render(); }); });

  /* the form switcher: swaps which of the three view regions is showing. The view the page opens
     on is the pair, so the toolbar starts there. */
  document.getElementById('segForm').innerHTML=['f2','f8','f10'].map(function(k){
    return '<button data-f="'+k+'">'+FORM_TITLES[k]+'</button>'; }).join('');
  document.querySelectorAll('#segForm button').forEach(function(b){
    b.addEventListener('click',function(){ setForm(b.getAttribute('data-f')); });
  });
  /* a click anywhere in a small-multiple panel, or a row of the ranked table, drills exactly as a
     bar click does - so the two new forms are navigable and not pictures. */
  document.getElementById('smlGrid').addEventListener('click',function(e){
    var p=e.target.closest? e.target.closest('.smlPanel') : null;
    if(p) drill(parseInt(p.getAttribute('data-i'),10)); });
  document.getElementById('smlGrid').addEventListener('contextmenu',function(e){
    e.preventDefault(); climb(); });
  document.getElementById('tbl10').tBodies[0].addEventListener('click',function(e){
    var tr=e.target.closest? e.target.closest('tr[data-i]') : null;
    if(tr) drill(parseInt(tr.getAttribute('data-i'),10)); });
  document.getElementById('tipFleet').innerHTML='<b>Which fleet</b><br><b>Each period\'s own '
    +'fleet</b> divides this period\'s euro by this period\'s vehicles and last period\'s euro by last '
    +'period\'s vehicles. That is the like-for-like answer, and it is the one the page opens on. '
    +'It is disabled when either period year is 2026 or later and the workbook fleet row is a forward '
    +'figure, because those numbers are not quoted as forecasts.<br>'
    +'<b>Constant 2025 fleet (analytical)</b> divides both periods by the same single 2025 estimate. '
    +'It is an analytical alternative, not a forward forecast, and it cannot show a fleet effect '
    +'because the denominator does not move. Both answers stay on the page.';

  document.getElementById('btnReset').addEventListener('click',function(){
    S.fam=null; S.band=null; S.cat=null;
    document.getElementById('selFam').value=''; render(); });

  /* the help popup, opened from the toolbar rather than hidden in the keyboard */
  document.getElementById('helpPop').innerHTML='<h3>Keys and how to read this page</h3>'
    +'<ul><li><span class="keycap">F</span> fullscreen, and <span class="keycap">Esc</span> leaves it</li>'
    +'<li><span class="keycap">1</span> <span class="keycap">2</span> <span class="keycap">3</span> '
    +'pick the measure: EUR per vehicle, billed euro, units</li>'
    +'<li><span class="keycap">Esc</span> or <span class="keycap">Backspace</span> comes back one drill '
    +'level - the same as right-clicking a chart, which is the quickest way back</li>'
    +'<li><span class="keycap">&larr;</span> and <span class="keycap">&rarr;</span> step to the previous '
    +'or next period, skipping any year that is not a full twelve months on both sides</li>'
    +'<li><span class="keycap">/</span> jumps to the customer list, then hold <span class="keycap">Ctrl'
    +'</span> and click to pick several</li>'
    +'<li><span class="keycap">?</span> or <span class="keycap">H</span> opens and closes this box</li></ul>'
    +'<p>The breadcrumb above the figures always names the way back: every level in it can be clicked, '
    +'and a click restores the customers, the period and the vehicle type that were in force at that '
    +'level rather than jumping to the defaults.</p>'
    +'<p>Every level is comparable: euro per vehicle on that period\'s own fleet, the same months on '
    +'both sides, and the move split into volume, price, mix and the fleet, with the net bar beside '
    +'the four.</p>';
  document.getElementById('btnHelp').addEventListener('click',function(e){
    e.stopPropagation();
    closePops();
    document.getElementById('helpPop').classList.toggle('open');
  });
  document.getElementById('btnFull').addEventListener('click',toggleFull);

  /* table rows: one delegated listener for the life of the page */
  document.getElementById('tbl').tBodies[0].addEventListener('click',function(e){
    var tr=e.target.closest?e.target.closest('tr[data-i]'):null;
    if(tr && tr.classList.contains('clickable')) drill(parseInt(tr.getAttribute('data-i'),10));
  });

  buildKeys();
}
function setMetric(k){
  S.metric=k;
  document.querySelectorAll('#segMetric button').forEach(function(x){
    x.classList.toggle('on', x.getAttribute('data-m')===k); });
  render();
}
function toggleFull(){
  var d=document, el=d.documentElement;
  if(d.fullscreenElement||d.webkitFullscreenElement){
    (d.exitFullscreen||d.webkitExitFullscreen||function(){}).call(d);
  } else {
    (el.requestFullscreen||el.webkitRequestFullscreen||function(){}).call(el);
  }
}
function buildKeys(){
  document.addEventListener('keydown',function(e){
    var tag=(e.target&&e.target.tagName)||'';
    if(tag==='SELECT'&&(e.key===' '||e.key==='ArrowUp'||e.key==='ArrowDown')) return;
    var help=document.getElementById('helpPop');
    if(e.key==='Escape'){
      if(document.fullscreenElement||document.webkitFullscreenElement) return;
      if(help&&help.classList.contains('open')){ help.classList.remove('open'); return; }
      if(climb()) e.preventDefault();
      return;
    }
    if(e.key==='Backspace'){ if(climb()) e.preventDefault(); return; }
    if(e.key==='ArrowLeft'||e.key==='ArrowRight'){
      if(stepClock(e.key==='ArrowLeft'? -1 : 1)) e.preventDefault();
      return;
    }
    if(e.key==='/'){
      e.preventDefault();
      var sc=document.getElementById('selCust'); sc.focus();
      if(sc.options.length) sc.options[0].scrollIntoView({block:'nearest'});
      return;
    }
    if(e.key==='?'||e.key==='h'||e.key==='H'){
      e.preventDefault();
      if(help) help.classList.toggle('open');
      return;
    }
    if(e.key==='f'||e.key==='F'){ e.preventDefault(); toggleFull(); return; }
    if(e.key==='1'){ setMetric('pv'); return; }
    if(e.key==='2'){ setMetric('abs'); return; }
    if(e.key==='3'){ setMetric('units'); return; }
  });
  /* closing the help the way every other popup on the page closes */
  document.addEventListener('click',function(e){
    var help=document.getElementById('helpPop');
    var btn=document.getElementById('btnHelp');
    if(!help||!help.classList.contains('open')) return;
    if(help.contains(e.target)||(btn&&btn.contains(e.target))) return;
    help.classList.remove('open');
  });
}
function heldOptions(){
  var out='';
  Object.keys(D.clocks).forEach(function(c){
    (D.clocks[c].heldOut||[]).forEach(function(h){
      out+='<option value="" disabled>'+h.label+' - '+h.why+', not comparable</option>'; });
  });
  return out;
}

/* ── start ──────────────────────────────────────────────────────────────────────────────────── */
S.clock='CY';
buildControls();
render();
/* the view the page opens on: the pair, because it is the only one of the three that shows the two
   columns as billed with the difference beside them. The switcher is on the card itself. */
setForm('f2');

window.__pmfe2={
  state:S,
  pair:function(){ return pairOf(S.clock); },
  recs:function(){ return LAST.map(function(r){ return {key:r.key, level:r.level,
    eur0:r.eur0, eur1:r.eur1, units0:r.units0, units1:r.units1, pns:r.pns, dealers:r.dealers,
    comparable:!r.notComparable, verdict:r.verdict, thin:r.thin, f0:r.f0, f1:r.f1,
    rate0:r.rate0, rate1:r.rate1, noWallet:r.noWallet, sharedDenom:r.sharedDenom,
    total:r.pv.ok? r.pv.total:null, vol:r.pv.ok? r.pv.vol:null, price:r.pv.ok? r.pv.price:null,
    mix:r.pv.ok? r.pv.mix:null, fleet:r.pv.ok? r.pv.fleet:null, check:r.pv.ok? r.pv.check:null}; }); },
  rowCount:function(){ return document.querySelectorAll('#tbl tbody tr').length; },
  drill:function(i){ drill(i); },
  drillKey:function(key){
    for(var i=0;i<LAST.length;i++) if(String(LAST[i].key)===String(key)){ drill(i); return true; }
    return false; },
  clickRow:function(i){ var tr=document.querySelectorAll('#tbl tbody tr.clickable')[i];
    if(!tr) return false; tr.click(); return true; },
  setState:function(patch){ Object.keys(patch).forEach(function(k){ S[k]=patch[k]; }); render(); },
  charts:function(){ return Object.keys(charts); },
  level:function(){ return levelNow(); },
  /* ── for the ship gate. Nothing here draws anything: it reads the page back so the checks can
     assert against the rendered state instead of the source. ─────────────────────────────────── */
  contract:function(){
    var sc=document.getElementById('selCust');
    return {
      controls:{ customers:{present:!!sc, options:sc? sc.options.length:0,
                            multiple:sc? !!sc.multiple:false, selected:chosenMarkets()},
        vehicleType:{present:!!document.getElementById('selFam'),
                     options:document.getElementById('selFam').options.length},
        period:{present:!!document.getElementById('selClock'),
                options:Array.prototype.filter.call(document.getElementById('selClock').options,
                  function(o){ return !o.disabled; }).length,
                spelledOut:Array.prototype.filter.call(document.getElementById('selClock').options,
                  function(o){ return o.textContent.indexOf('January')>=0
                    || o.textContent.indexOf('April')>=0; }).length},
        measure:{present:document.querySelectorAll('#segMetric button').length},
        fleet:{present:document.querySelectorAll('#segFleet button').length},
        clearAll:{present:!!document.getElementById('btnAll')},
        clearNone:{present:!!document.getElementById('btnNone')},
        itukOnly:{present:!!document.getElementById('btnItuk')},
        help:{present:!!document.getElementById('btnHelp')},
        fullscreen:{present:!!document.getElementById('btnFull')}},
      charts:Object.keys(charts),
      panelErrors:PANEL_ERR.slice()
    };
  },
  custOptions:function(){ return custList().map(function(o){ return o.value; }); },
  selectedMarkets:function(){ return chosenMarkets(); },
  syncCust:function(){ syncCust(); },
  /* the mouse path, spelled out: a real control event is dispatched, not a JS value assignment */
  selectCustomer:function(name){
    var o=custList().filter(function(x){ return x.value===name; })[0];
    if(!o) return false;
    custList().forEach(function(x){ x.selected=(x===o); });
    document.getElementById('selCust').dispatchEvent(new Event('change',{bubbles:true}));
    return true;
  },
  clickAll:function(){ document.getElementById('btnAll').click(); return chosenMarkets().length; },
  clickNone:function(){ document.getElementById('btnNone').click(); return chosenMarkets().length; },
  clickItuk:function(){ document.getElementById('btnItuk').click(); return chosenMarkets(); },
  kpis:function(){
    var out=[];
    document.querySelectorAll('#kpis .kpi').forEach(function(k){
      out.push({lab:k.querySelector('.lab').textContent.replace(/\s+/g,' ').trim(),
                val:k.querySelector('.val').textContent.trim(),
                sub:(k.querySelector('.sub')||{textContent:''}).textContent.replace(/\s+/g,' ').trim()});
    });
    return out;
  },
  /* the axis formatter, as the chart actually got it, applied to the values the chart is showing */
  decTicks:function(){
    var ch=charts['c_dec']; if(!ch) return null;
    var cb=ch.options.scales.x.ticks.callback;
    var vals=[];
    ch.data.datasets.forEach(function(d){ d.data.forEach(function(v){ if(v!==null) vals.push(v); }); });
    if(!vals.length) return {title:ch.options.scales.x.title.text, values:[], ticks:[]};
    var lo=Math.min.apply(null,vals), hi=Math.max.apply(null,vals);
    var step=(hi-lo)/4 || 0.01;
    var arr=[0,1,2,3,4].map(function(i){ return {value: lo+step*i}; });
    var ticks=arr.map(function(t){ return cb(t.value, 0, arr); });
    return {title:ch.options.scales.x.title.text, lo:lo, hi:hi, step:step,
            datasets:ch.data.datasets.map(function(d){ return d.label; }), ticks:ticks};
  },
  /* the whole chart inventory, with the listener count each canvas still carries */
  chartState:function(){
    var out={};
    ['c_main','c_dec','c_price'].forEach(function(id){
      var ch=charts[id], el=document.getElementById(id);
      out[id]={exists:!!ch, destroyed:!!(ch&&ch.destroyed),
               hasCanvas:!!(ch&&ch.canvas), hasCtx:!!(ch&&ch.ctx),
               leaves:el? (el.$proxies? Object.keys(el.$proxies).filter(function(k){return el.$proxies[k];}).length
                                 : 0):null,
               own:el&&el.__free? Object.keys(el.__free).length:0};
    });
    SML_CHARTS.forEach(function(c,i){
      out['sml_'+i]={exists:!!c, destroyed:!!(c&&c.destroyed), hasCanvas:!!(c&&c.canvas),
                     hasCtx:!!(c&&c.ctx)};
    });
    return out;
  },
  /* ── the three forms, read back from the DOM that is on screen ─────────────────────────────
     These read the rendered tables, canvases and panels rather than the state they were built
     from, so a check can assert what the reader can actually see. */
  form:function(){ return FORM.key; },
  formVisible:function(){
    var out={};
    ['f2','f8','f10'].forEach(function(k){
      var v=document.getElementById('view-'+k);
      out[k]=!!(v&&v.classList.contains('on'));
    });
    return out;
  },
  setForm:function(k){ setForm(k); return FORM.key; },
  /* every row of every form, with units this period and both percentages, so a check can tie the
     rendered figures back to the payload and to the source frames */
  formRows:function(){
    var out={f2:[], f8:[], f10:[]};
    var cvS=charts['c_main'];
    if(cvS){
      cvS.data.labels.forEach(function(l,i){
        var r=LAST[i];
        out.f2.push({label:l, bar0:cvS.data.datasets[0].data[i], bar1:cvS.data.datasets[1].data[i],
          metric:S.metric,
          measureOk:!!r && !r.notComparable && (S.metric!=='pv' || r.pv.ok),
          eur0:r?r.eur0:null, eur1:r?r.eur1:null, units0:r?r.units0:null, units1:r?r.units1:null,
          rate0:(r&&r.pv.ok)?r.pv.rate0:null, rate1:(r&&r.pv.ok)?r.pv.rate1:null,
          f0:r?r.f0:null, f1:r?r.f1:null,
          eurPct:(r&&r.eur0>0)? r.eur1/r.eur0-1 : null,
          ratePct:(r&&r.pv.ok&&r.pv.rate0)? r.pv.rate1/r.pv.rate0-1 : null,
          pctText:r? pctTxt(rowPct(r).eurPct)+' / '+pctTxt(rowPct(r).ratePct) : null});
      });
    }
    document.querySelectorAll('#smlGrid .smlPanel').forEach(function(p, i){
      var r=LAST[parseInt(p.getAttribute('data-i'),10)];
      var c=SML_CHARTS[i];
      var txt=(p.querySelector('.pct')||{textContent:''}).textContent.replace(/\s+/g,' ').trim();
      var textAll=Array.prototype.map.call(p.querySelectorAll('.pct'),
        function(x){ return x.textContent.replace(/\s+/g,' ').trim(); }).join(' | ');
      var canvas=p.querySelector('canvas');
      var ink=0;
      try{ var ctx=canvas.getContext('2d');
        var d=ctx.getImageData(0,0,canvas.width,canvas.height).data;
        for(var k=3;k<d.length;k+=4){ if(d[k]>8) ink++; }
      }catch(e){}
      out.f8.push({label:(p.querySelector('.h')||{textContent:''}).textContent.trim(),
        bar0:c? c.data.datasets[0].data[0] : null, bar1:c? c.data.datasets[0].data[1] : null,
        yMax:c? c.options.scales.y.max : null, metric:S.metric,
        measureOk:!!r && !r.notComparable && (S.metric!=='pv' || r.pv.ok),
        eur0:r?r.eur0:null, eur1:r?r.eur1:null, rate0:(r&&r.pv.ok)?r.pv.rate0:null,
        rate1:(r&&r.pv.ok)?r.pv.rate1:null, units0:r?r.units0:null, units1:r?r.units1:null,
        eurPct:(r&&r.eur0>0)? r.eur1/r.eur0-1 : null,
        ratePct:(r&&r.pv.ok&&r.pv.rate0)? r.pv.rate1/r.pv.rate0-1 : null,
        pctText:txt, pctTextAll:textAll, inkPixels:ink});
    });
    var ths=Array.prototype.map.call(document.querySelectorAll('#tbl10 thead th'),
      function(t){ return t.textContent.trim(); });
    var rows=Array.prototype.map.call(document.querySelectorAll('#tbl10 tbody tr'), function(tr){
      var tds=Array.prototype.map.call(tr.querySelectorAll('td'),function(td){
        return td.textContent.replace(/\s+/g,' ').trim(); });
      var i=parseInt(tr.getAttribute('data-i'),10), r=LAST[i];
      var bars=Array.prototype.map.call(tr.querySelectorAll('.cellbar'),
        function(b){ return b.style.width; });
      return {i:i, cells:tds, bars:bars,
        eur0:r?r.eur0:null, eur1:r?r.eur1:null, units0:r?r.units0:null, units1:r?r.units1:null,
        f0:r?r.f0:null, f1:r?r.f1:null,
        eurPct:(r&&r.eur0>0)? r.eur1/r.eur0-1 : null,
        ratePct:(r&&r.pv.ok&&r.pv.rate0)? r.pv.rate1/r.pv.rate0-1 : null}; });
    out.f10={headers:ths, rows:rows};
    return out;
  },
  /* the worked case, as it is printed on the page and as the build computed it */
  worked:function(){ return D.worked||null; },
  workedText:function(){
    var el=document.getElementById('worked');
    return el? el.textContent.replace(/\s+/g,' ').trim() : '';
  },
  /* what the page's own browser-side computation says, family by family, for the tie-out */
  pctCheck:function(){
    var out={clock:S.clock, denom:S.denom, byFamily:{}};
    var pr=pairOf(S.clock);
    FAM_KEYS.forEach(function(fk){
      var rows=atomsFor(fk, null, null, null);
      var e0=0,e1=0,u0=0,u1=0;
      rows.forEach(function(r){ if(r[2]===pr.bi){e0+=r[3];u0+=r[4];} if(r[2]===pr.ei){e1+=r[3];u1+=r[4];} });
      var f0=fleetFor(fk,null,pr.b,S.denom==='flat').value,
          f1=fleetFor(fk,null,pr.e,S.denom==='flat').value;
      out.byFamily[fk]={eur0:e0, eur1:e1, units0:u0, units1:u1, f0:f0, f1:f1,
        eurPct:e0>0? e1/e0-1 : null,
        ratePct:(e0>0&&f0>0&&f1>0)? (e1/f1)/(e0/f0)-1 : null,
        fleetPct:(f0>0&&f1>0)? f1/f0-1 : null};
    });
    return out;
  },
  panelErrors:function(){ return PANEL_ERR.slice(); },
  /* a forced failure, used by the ship gate to prove that one broken panel does not blank the page */
  breakChart:function(id){ var ch=charts[id]; if(!ch) return false; delete ch.legend; return true; },
  /* damage a node that one of the guarded panels reads, so that panel really throws on the next
     draw while the others have to carry on */
  damage:function(what){
    var map={table:'tbl', band:'bandpanel', fleet:'t_fleet', kpis:'kpis', crumb:'crumb'};
    var id=map[what];
    if(!id) return false;
    var el=document.getElementById(id);
    if(!el) return false;
    el.innerHTML='';
    if(what==='band') el.parentNode.removeChild(el);
    return true;
  },
  climb:function(){ return climb(); },
  stepClock:function(d){ return stepClock(d); },
  fullscreenAvailable:function(){ return !!(document.documentElement.requestFullscreen
    ||document.documentElement.webkitRequestFullscreen); },
  helpOpen:function(){ return document.getElementById('helpPop').classList.contains('open'); },
  keyHelp:function(){ return document.getElementById('helpPop').textContent.replace(/\s+/g,' ').trim(); }
};

}catch(err){
  var b=document.getElementById('errbar');
  if(b){ b.style.display='block';
    b.innerHTML='<b>The page did not finish drawing.</b> A script error stopped it, so some panels '
      +'below are empty. Detail: '+String(err&&err.message?err.message:err); }
}
})();
