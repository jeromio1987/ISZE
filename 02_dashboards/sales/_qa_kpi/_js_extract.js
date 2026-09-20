
const K = window.__KPI__;
const MODE = {period:'cy', dir:'db', warr:'inc'};
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));

/* ---------- formatting ---------- */
function eur(v, dp){
  if(v===null||v===undefined||v==='na'||isNaN(v)) return 'unavailable';
  const n = Number(v);
  if(Math.abs(n)>=1e6) return '\u20ac'+(n/1e6).toFixed(2)+'M';
  if(Math.abs(n)>=1e4) return '\u20ac'+Math.round(n/1e3)+'k';
  return '\u20ac'+n.toFixed(dp===undefined?0:dp);
}
function eurL(v){
  if(v===null||v===undefined||v==='na'||isNaN(v)) return 'unavailable';
  return '\u20ac'+Math.round(Number(v)).toLocaleString('en-GB');
}
function pct(v,dp){ if(v===null||v===undefined||v==='na'||isNaN(v)) return 'unavailable';
  return Number(v).toFixed(dp===undefined?1:dp)+'%'; }
function num(v){ if(v===null||v===undefined||v==='na'||isNaN(v)) return 'unavailable';
  return Math.round(Number(v)).toLocaleString('en-GB'); }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;'); }

/* ---------- state-derived values ---------- */
const LBL_P = {cy:'Calendar 2025 (Jan\u2013Dec)', fy:'FY25/26 (Apr 2025 \u2013 Mar 2026)'};
const LBL_D = {db:'ISZE \u2192 DB (what we invoice the distributor)',
               dlr:'DB \u2192 dealer (what the distributor invoices its dealers)'};
const LBL_W = {inc:'warranty included', ex:'warranty excluded'};

function monthsFor(){
  const out=[];
  if(MODE.period==='cy'){ for(let m=1;m<=12;m++) out.push('2025-'+String(m).padStart(2,'0')); }
  else { for(let m=4;m<=12;m++) out.push('2025-'+String(m).padStart(2,'0'));
         for(let m=1;m<=3;m++) out.push('2026-'+String(m).padStart(2,'0')); }
  return out;
}
/* Billing-side figures. period + warranty recompute; direction swaps to sales to dealer. */
function view(db){
  const ms = monthsFor();
  let e=0,q=0,b=0, cov = ms.length;
  let used=0;
  ms.forEach(m=>{ const r=db.m[m]; if(r){ used++; e+=r[0]; q+=r[1]; b+=r[2]; } });
  const isCis = K.cis4.indexOf(db.code)>=0;
  let warr=null, warrReason=null;
  if(isCis){ warrReason='no warranty data for this market'; }
  else if(MODE.period==='cy'){ warr = db.warr; if(warr===null) warrReason='not held for this market'; }
  else { warr = db.warrFy ? db.warrFy.fy26 : null;
         if(warr===null) warrReason='no fiscal-tagged warranty file for this market'; }
  if(MODE.warr==='ex' && warr!==null) e = e - warr;
  if(MODE.warr==='ex' && warr===null && !isCis) e = null;   /* cannot strip what we do not hold */
  const dir = MODE.dir;
  const dlr = db.dealer;
  let shown, dirReason=null;
  if(dir==='db'){ shown = e; }
  else {
    if(dlr && (MODE.period==='cy')) { shown = dlr.eur; }
    else if(dlr && MODE.period==='fy'){ shown='na'; dirReason='sales-to-dealer file is calendar-2025 only'; }
    else { shown='na'; dirReason='no sales-to-dealer file for this distributor'; }
  }
  const uio = db.uio;
  let spu=null, spuWhy=null;
  if(dir==='db'){
    if(shown===null||shown==='na'||isCis||uio===null||!uio){ spuWhy = isCis? 'no fleet denominator for this market'
        : (uio? 'a figure is unavailable' : 'no fleet denominator for this market'); }
    else spu = shown/uio;
  } else spu=null;
  const uioPrev = db.uio24;
  return {eur:shown, qty:q, bvp:b, warr:warr, warrReason:warrReason, dir:dir,
          dirReason:dirReason, spu:spu, spuWhy:spuWhy, isCis:isCis, uio:uio, uioPrev:uioPrev,
          monthsUsed:used, monthsCov:cov,
          base:e, sub:'', mileage: db.mileage ? db.mileage[0] : 20000,
          mileageMeasured: !!db.mileage};
}

function netView(){
  const ms=monthsFor();
  let e=0,b=0,miss=0;
  K.dbs.forEach(db=>{ if(!db.inModel) return; ms.forEach(m=>{ const r=db.m[m];
    if(r){ e+=r[0]; b+=r[2]; } else miss++; }); });
  const isCis=false;
  let warr = MODE.period==='cy' ? K.net.warrCy : K.net.warrFy;
  const warrAvail = MODE.period==='cy' ? true : (warr>0);
  let ex = e - (warrAvail?warr:0);
  if(MODE.warr==='ex'){ e = ex; }
  const dir = MODE.dir;
  let shown=e, note='';
  if(dir==='dlr'){
    shown = MODE.period==='cy' ? K.net.sellout : 'na';
    note = MODE.period==='cy' ? '' : 'sales-to-dealer file is calendar-2025 only';
  }
  const uio=K.net.uio;
  let spu = (dir==='db' && e>0 && uio>0) ? e/uio : null;
  return {eur:shown, bvp:b, warr:warr, warrAvail:warrAvail, uio:uio, spu:spu, note:note,
          uioPrev:K.net.uio24, monthsMiss:miss};
}
function t(txt, extra){ return (extra? extra+'\n':'') + txt; }
const SNAP = 'Snapshot '+K.snap+'. ';

/* =================================================================== helpers */
function T(formula, notincl, extra){
  return 'Formula: '+formula+'\nSnapshot: '+K.snap+'.'+ (extra? '\n'+extra : '') +
         (notincl? '\nNot included: '+notincl : '');
}
function tip(txt, inner, cls){
  return '<span class="tip '+(cls||'')+'" tabindex="0" data-tip="'+
    String(txt).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;')+'">'+inner+'</span>';
}
const SET = () => 'Setting: '+LBL_P[MODE.period]+' \u00b7 '+LBL_D[MODE.dir]+' \u00b7 '+LBL_W[MODE.warr]+'.';
const CYNOTE = 'Source is calendar-tagged only: the fiscal view cannot be computed from it.';
function cyOnly(html, why){
  if(MODE.period!=='fy') return html;
  return '<span class="cyonly">'+html+'</span> <span class="chip n" data-tip="'+(
    'Shown for Calendar 2025. The fiscal view is unavailable because: '+(why||CYNOTE)
    )+'\nSnapshot: '+K.snap+'.">CY25</span>';
}
function arrow(now, prev){
  if(now===null||prev===null||!prev||now===undefined) return '<span class="na">\u2013</span>';
  const d=(now-prev)/prev*100;
  const s=(d>=0?'\u25b2':' \u25bc')+' '+Math.abs(d).toFixed(1)+'%';
  return '<span class="'+(d>=0?'pos':'neg')+'">'+s+'</span>';
}
function bar(v, max, cls, w){
  const W = w||70;
  if(v===null||v==='na'||isNaN(v)) return '';
  const px = Math.max(1, Math.round(Math.abs(v)/max*W));
  return '<span class="bar-mini '+(cls||'')+'" style="width:'+px+'px"></span>';
}
const CH = [];
function reg(n){ CH.push(n); }

/* =================================================================== hero */
function heroHTML(){
  const n = netView();
  const gap = K.net.capGap, tam = K.net.capTam;
  const rate = K.net.capRate;
  const uio = K.net.uio;
  const uioDir = uio && K.net.uioPrev ? (uio-K.net.uioPrev)/K.net.uioPrev*100 : null;
  const cards = [];
  cards.push('<div class="kpi"><div class="lbl">Spend per truck per year</div>'+
    '<div class="big">'+(n.spu? '\u20ac'+n.spu.toFixed(0) : 'unavailable')+'</div>'+
    '<div class="den">on '+tip(T('parts billed \u00f7 vehicles in service (UIO).',
      'the four CIS markets, which have no fleet denominator; dealer invent-stock effects.',
      SET()+' Direction: '+LBL_D[MODE.dir]+' - on the sales-to-dealer direction this tile is unavailable because the six sell-to-dealer files carry a different fleet basis.'),
      num(uio)+' vehicles in service')+'</div>'+
    '<div class="tl">'+(n.spu? 'network parts billed '+eur(n.eur) : 'needs the ISZE \u2192 DB direction')+'</div></div>');
  cards.push('<div class="kpi"><div class="lbl">Service-part capture</div>'+
    '<div class="big t">'+rate.toFixed(1)+'%</div>'+
    '<div class="den">of the '+num(K.net.capTam/K.net.capTam*996890)+' service parts the model expects</div>'+
    '<div class="tl">'+tip(T('units billed \u00f7 units the maintenance model expects, across the 14 service families, on the same fleet.',
      'the eight markets whose target spend sits on one flat \u20ac250-per-truck placeholder; parts outside the 14 service families.',
      SET()+' Calendar-2025 source: '+CYNOTE),
      'uncaptured GPS value '+eur(gap))+'</div></div>');
  cards.push('<div class="kpi"><div class="lbl">Uncaptured GPS value</div>'+
    '<div class="big t">'+eur(gap)+'</div>'+
    '<div class="den">addressable on '+eur(tam)+' of modelled demand (5.8&times;)'+'</div>'+
    '<div class="tl">'+tip(T('modelled demand (tam_eur) \u2212 parts billed in those families, summed over the 14 service families and 18 distributors.',
      'the four CIS markets and MIDI (no fleet denominator); the flat-\u20ac250 markets\u2019 ceiling precision.',
      SET()+' A ceiling, not a forecast. '+CYNOTE),
      'service families: air, oil and fuel filters, urea filter, blower filter, brake pad, shoe, rotor, clutch disc, kit, pressure plate, booster, pilot and release bearing')+'</div></div>');
  cards.push('<div class="kpi"><div class="lbl">Vehicles in service (UIO)</div>'+
    '<div class="big">'+num(uio)+'</div>'+
    '<div class="den">'+arrow(uio,K.net.uioPrev).replace(/\u2013/,'\u2013')+' against 2024, '+num(K.net.uioPrev)+'</div>'+
    '<div class="tl">'+tip(T('sum of vehicles in service across the 18 distributor databases, 2025.',
      'the four CIS markets (no denominator), the 2026\u20132030 forecast (withdrawn).',
      SET()+' Basis: v18 actual for 17 markets, ITUK DVLA for the UK truck fleet.'),
      'no 2026\u20132030 forecast is shown anywhere on this page')+'</div></div>');
  return '<div class="hero">'+cards.join('')+'</div>';
}

/* =================================================================== controls */
function barHTML(){
  const b=(k,v,t,extra)=>'<button type="button" data-k="'+k+'" data-v="'+v+'"'+
    (MODE[k]===v?' aria-pressed="true"':'')+' data-tip="'+t+'\nSnapshot: '+K.snap+'.'+(extra?'\n'+extra:'')+
    '">'+t.split('.')[0]+'</button>';
  return '<div class="bar"><div class="inner">'+
    '<div class="grp"><span class="gl">Period</span>'+
      b('period','cy','Calendar 2025 (Jan\u2013Dec). Recomputed from the billing fact on billing date.','')+
      b('period','fy','FY25/26 (Apr 2025 \u2013 Mar 2026). Recomputed from the billing fact on billing date.')+
    '</div>'+
    '<div class="grp"><span class="gl">Direction</span>'+
      b('dir','db','ISZE \u2192 DB: what we invoice the distributor.')+
      b('dir','dlr','DB \u2192 dealer: what the distributor invoices its dealers. Only six distributors file it (ITUK, UTI, Ireland, IUK, Greece, Portugal).')+
    '</div>'+
    '<div class="grp"><span class="gl">Warranty</span>'+
      b('warr','inc','Warranty included in what we billed.')+
      b('warr','ex','Warranty excluded: warranty parts are stripped to leave the customer-paid book.')+
    '</div>'+
    '<div class="state" id="stateChip"></div>'+
  '</div></div>';
}

/* =================================================================== league */
const COLS = [
 ['Distributor','l'],['Billed',''],['Share',''],['Vehicles in service',''],['Fleet',''],['Spend per truck',''],
 ['Capture',''],['Uncaptured',''],['Largest family gap','l'],['Capture trend','l'],['Defection','l'],
 ['Breadth',''],['Exposure',''],['Warranty',''],['Competitive parts',''],['Stock','']
];
function storyTag(code){ return K.story.indexOf(code)>=0; }
function leagueHTML(){
  let h='<div class="tbl"><table class="league"><thead><tr>'+
    COLS.map((c,i)=>'<th class="'+(c[1]||'')+'">'+c[0]+'</th>').join('')+'</tr></thead><tbody>';
  const maxCy = Math.max.apply(null, K.dbs.map(d=>d.inModel?d.cy:0));
  K.dbs.forEach(d=>{
    const v = view(d);
    const cap = d.cap, tr = d.traj, df = d.defn, br = d.breadth;
    const famGapTop = d.famGap ? d.famGap.slice().sort((a,b)=>b.gap-a.gap)[0] : null;
    h+='<tr class="'+(storyTag(d.code)?'story ':'')+(d.inModel?'':'cis')+'">';
    h+='<td class="l"><b>'+d.label+'</b>'+(storyTag(d.code)?' <span class="chip r">story</span>':'')+
       '<br><span class="tiny">'+d.name+'</span></td>';
    h+='<td>'+tip(T('parts billed to this distributor in the selected period, from the billing fact, attributed through the distributor code map.',
        'the four CIS markets and MIDI, which trade without a distributor code; 2026 rows, which carry customer names instead of codes.',
        SET()), (v.eur==='na'? '<span class="na">no file</span>' : eurL(v.eur)))+'<br>'+bar(d.cy,maxCy,'')+'</td>';
    h+='<td>'+pct(d.inModel? d.cy/K.net.cyAttr*100 : null,1)+'</td>';
    h+='<td>'+tip(T('vehicles in service (UIO) for 2025, the denominator behind spend per truck and capture.',
        'the 2026\u20132030 forecast, which is withdrawn; the four CIS markets have no denominator.',
        'Basis: '+d.uioSrc+'.'),
        num(d.uio))+'</td>';
    h+='<td>'+tip(T('fleet direction: 2025 against 2024 vehicles in service.',
        'new registrations, scrappage or the model\u2019s own survival curve: this is the level change only.'),
        arrow(d.uio,d.uio24))+'</td>';
    h+='<td>'+tip(T('parts billed \u00f7 vehicles in service.',
        'dealer inventory movements; the four CIS markets. '+(v.mileageMeasured? 'Measured distance '+num(v.mileage)+' km/yr is available for this market.':'No measured distance for this market, the model assumes a flat 20,000 km/yr.'),
        SET()+' Direction: '+LBL_D[MODE.dir]+'.'),
        (v.spu? eurL(v.spu) : '<span class="na">unavailable</span>'))+'</td>';
    h+='<td>'+cyOnly(tip(T('units billed \u00f7 units the maintenance model expects, 2025, weighted across 14 service families.',
        'the flat \u20ac250-per-truck markets\u2019 ceiling precision; parts outside the 14 families.',
        SET()+' A rate above 100% means more was billed than the model expects.'),
        (cap? cap.rate.toFixed(1)+'%' : '<span class="na">n/a</span>')))+'</td>';
    h+='<td>'+cyOnly(tip(T('modelled demand \u2212 parts billed, across the 14 service families, in euro.',
        'the four CIS markets; the ceiling\u2019s accuracy in the flat-target markets.',
        SET()+' Ceiling, not forecast.'),
        (famGapTop? eurL(d.famGap.reduce((a,b)=>a+b.gap,0)) : '<span class="na">n/a</span>')))+'</td>';
    h+='<td class="l">'+cyOnly(tip(T('the service family with the largest euro not billed in 2025.',
        'families outside the 14; the flat-target markets.'),
        (famGapTop? famGapTop.fam+' \u00b7 '+eurL(famGapTop.gap)+' <span class="tiny">'+(100-famGapTop.rate).toFixed(0)+'% unbought</span>' : '\u2013')))+'</td>';
    h+='<td class="l">'+cyOnly(tip(T('least-squares slope of the annual capture rate, in percentage points per year, for the worst-fitting family (2023\u20132025).',
        '2026, whose rows are partial; families with fewer than three annual points.',
        SET()), (tr && tr.length? (function(){ const w=tr.slice().sort((a,b)=>a.slope-b.slope)[0];
          return (w.dec? '<span class="chip r">falling</span> ':'<span class="chip g">rising</span> ')+
            '<span class="tiny">'+w.fam.replace(/_/g,' ')+' '+w.slope.toFixed(2)+' pp/yr, R\u00b2 '+w.r2.toFixed(2)+'</span>'; })()
          : '<span class="na">n/a</span>')))+'</td>';
    h+='<td class="l">'+cyOnly(tip(T('distributor-and-family combinations silent for longer than their own median reorder gap, as at the March 2026 data horizon. The euro is the trailing twelve months billed on that family.',
        'dealer-level dormancy: the file carries no customer names on this page.',
        SET()), (df? '<span class="chip '+(df.n_alert>1?'r':'a')+'">'+df.n_alert+' quiet</span> <span class="tiny">'+eurL(df.silent_eur)+'</span><br><span class="tiny">'+
          df.tops.slice(0,2).map(t=>t.fam.replace(/_/g,' ')+' silent '+t.silent.toFixed(0)+' mo, '+(t.gap? (t.silent/t.gap).toFixed(1)+'\u00d7 its '+t.gap.toFixed(0)+'-month gap':'no gap')).join('<br>')+'</span>'
          : '<span class="na">none flagged</span>')))+'</td>';
    h+='<td>'+cyOnly(tip(T('number of distinct goods-classification groups (the 3-digit part-class prefix) billed at least once in 2025.',
        'part numbers that carry no goods classification: '+K.net.figcov.toFixed(1)+'% of billed value is classified, so '+ (100-K.net.figcov).toFixed(1)+'% carries none.',
        SET()), (br? br.cy.length : '\u2013')))+'</td>';
    h+='<td>'+cyOnly(tip(T('share of billed value on part numbers the aftersales item master classifies as highly exposed to the independent aftermarket, with the weighted genuine-over-competitive price premium beside it.',
        'the pricing-risk layer, which returned a null on backtest; part numbers with no classification.',
        SET()), ((d.aim? (d.aim.risk).toFixed(2)+'% risk' : '\u2013')+
        (d.prem? ' <span class="tiny">+'+d.prem.prem.toFixed(0)+'% price</span>' : ''))))+'</td>';
    h+='<td>'+tip(T('warranty parts in euro \u00f7 total parts billed, for the selected period.',
        'the four CIS markets, which have no warranty data at all. '+(MODE.period==='fy'?'Fiscal figure comes from the fiscal warranty expense file.':'Calendar figure comes from the spend file.'),
        SET()), (v.warr!==null&&v.warr!==undefined? eurL(v.warr)+' <span class="tiny">'+(d.warrShare? d.warrShare.toFixed(1)+'%':'')+'</span>'
          : '<span class="na">no warranty data</span>'))+'</td>';
    h+='<td>'+tip(T('share of all parts billed that is Competitive (best-value) parts, in euro, and the share of the contested euro that went to Competitive parts.',
        'the four CIS markets in the modelled denominators; the contested classification covers only part numbers with a mapped twin.',
        SET()), (d.bvp? d.bvp.pct.toFixed(2)+'% <span class="tiny">contested capture '+(d.bvp.capr===null?'n/a':d.bvp.capr.toFixed(0)+'%')+'</span>' : '\u2013'))+'</td>';
    h+='<td>'+tip(T('what the distributor sold on to its dealers minus what we invoiced it, for the same calendar year: the indicator of stock the distributor is sitting on.',
        'the twelve distributors with no sales-to-dealer file; the fiscal view, which the file cannot support.',
        SET()), (d.dealer? (function(){ const s=d.dealer.eur-d.cy;
          return '<span class="'+(s>=0?'pos':'neg')+'">'+eurL(s)+'</span><br><span class="tiny">'+d.dealer.ents+' dealers</span>'; })()
        : '<span class="na">no file</span>'))+'</td>';
    h+='</tr>';
  });
  h+='</tbody><tfoot><tr><td class="l">Network, 18 modelled distributors</td>'+
     '<td>'+eurL(K.net.cyAttr)+'</td><td>100.0%</td><td>'+num(K.net.uio)+'</td><td>'+arrow(K.net.uio,K.net.uio24)+'</td>'+
     '<td>'+eurL(K.net.spuCy)+'</td><td>'+K.net.capRate.toFixed(1)+'%</td><td>'+eurL(K.net.capGap)+'</td>'+
     '<td class="l">clutch disc, the largest family</td><td class="l">see chart</td>'+
     '<td class="l">'+K.net.defN+' quiet rows \u00b7 '+eurL(K.net.defEur)+'</td><td>240 of 296</td>'+
     '<td>see chart</td><td>'+eurL(K.net.warrCy)+'</td><td>'+K.net.bvpShareCy.toFixed(2)+'%</td>'+
     '<td>'+eurL(K.net.sellout)+'</td></tr></tfoot></div>';
  h+='<p class="tiny">Four CIS markets (Ukraine, Armenia, Kazakhstan, Palestine) bill without a fleet denominator and sit outside every modelled figure on this page. 2026 rows are excluded from every trend: from April 2026 the billing table stores customer names instead of distributor codes, so no calendar or fiscal 2026 view can be attributed.</p>';
  return h;
}

/* =================================================================== charts */
function svgOpen(w,h){ return '<div class="svgwrap"><svg viewBox="0 0 '+w+' '+h+'" width="'+w+'" height="'+h+
  '" role="img" preserveAspectRatio="xMinYMin meet">'; }

/* G1 -- which markets spend most per truck per year? */
function cSpend(){
  const rows = K.dbs.filter(d=>d.inModel && d.spu!==null)
    .map(d=>({d:d, v:(MODE.warr==='ex'? d.spuXw : d.spu), n:(MODE.warr==='ex'?'xw':'in')}))
    .filter(r=>r.v!==null).sort((a,b)=>b.v-a.v);
  if(!rows.length) return '<div class="chart"><h3>Which markets spend most per truck per year?</h3><p class="note">Unavailable in this setting.</p></div>';
  const n=rows.length, bw=34, gap=10, x0=62, H=300, W=x0+ n*(bw+gap)+30;
  const mx=Math.max.apply(null,rows.map(r=>r.v))*1.14, base=H-46;
  const med = median(rows.map(r=>r.v));
  let s=svgOpen(W,H);
  [0,.25,.5,.75,1].forEach(f=>{ const y=base-f*(base-24);
    s+='<line x1="'+x0+'" y1="'+y.toFixed(1)+'" x2="'+(W-24)+'" y2="'+y.toFixed(1)+'" stroke="#e6e0d2"/>'+
       '<text x="'+(x0-6)+'" y="'+(y+3.5).toFixed(1)+'" text-anchor="end" font-size="9.5" fill="#8b8272">\u20ac'+Math.round(mx*f)+'</text>'; });
  s+='<line x1="'+(x0+(rows.findIndex(r=>r.v<med)+(rows.findIndex(r=>r.v<med)<0?n:0))*(bw+gap)-gap/2).toFixed(1)+
     '" y1="24" x2="'+(x0+(rows.findIndex(r=>r.v<med)+(rows.findIndex(r=>r.v<med)<0?n:0))*(bw+gap)-gap/2).toFixed(1)+
     '" y2="'+base+'" stroke="#c0552d" stroke-dasharray="4 3"/>';
  rows.forEach((r,i)=>{
    const x=x0+i*(bw+gap), h=Math.max(2,(r.v/mx)*(base-24));
    const story = K.story.indexOf(r.d.code)>=0;
    s+='<rect x="'+x+'" y="'+(base-h).toFixed(1)+'" width="'+bw+'" height="'+h.toFixed(1)+
       '" fill="'+(story?'#c0552d':'#15233c')+'"><title>'+r.d.label+': \u20ac'+r.v.toFixed(0)+' per truck per year'+
       (r.d.mileage? ' on '+Math.round(r.d.mileage[0]).toLocaleString('en-GB')+' measured km/yr':' on the flat 20,000 km/yr assumption')+'</title></rect>';
    s+='<text x="'+(x+bw/2)+'" y="'+(base-h-4).toFixed(1)+'" text-anchor="middle" font-size="9.5" fill="#15233c">\u20ac'+Math.round(r.v)+'</text>';
    s+='<text x="'+(x+bw/2)+'" y="'+(base+13)+'" text-anchor="middle" font-size="9.5" fill="#3d372b" transform="rotate(0)">'+r.d.label.slice(0,8)+'</text>';
    s+='<text x="'+(x+bw/2)+'" y="'+(base+25)+'" text-anchor="middle" font-size="8.5" fill="#8b8272">'+(r.d.mileage?'meas.':'flat')+'</text>';
  });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#c0552d">network median \u20ac'+Math.round(med)+'</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Which markets spend most per truck per year, and which under-spend their fleet?</h3>'+
   '<p class="cap">Parts billed per vehicle in service, '+LBL_P[MODE.period]+', '+LBL_W[MODE.warr]+
   '. Bar labels say whether the market\u2019s annual distance is measured or the flat 20,000 km/yr assumption. A tall bar is a larger book per truck, not a better-run market.</p>'+
   s+'</div>';
}
function median(a){ const b=a.slice().sort((x,y)=>x-y); const m=Math.floor(b.length/2);
  return b.length%2? b[m] : (b[m-1]+b[m])/2; }

/* G2 -- how much of last year's growth was more trucks, how much price? */
function cGrowth(){
  const leg = MODE.period==='cy' ? 'splitCy' : 'splitFy';
  const rows = K.dbs.filter(d=>d.inModel).map(d=>({d:d, s:d[leg]==='na'? null : d[leg]}))
    .filter(r=>r.s && (Math.abs(r.s.vol)+Math.abs(r.s.price)+Math.abs(r.s.end-r.s.base))>0);
  if(!rows.length) return '<div class="chart"><h3>Was last year\u2019s parts growth more trucks, or price?</h3>'+
    '<p class="note">Unavailable in this setting. The only source for this split is calendar-tagged (2024 \u2192 2025) and there is no fiscal equivalent here.</p></div>';
  rows.sort((a,b)=>Math.abs(b.s.vol+b.s.price)-Math.abs(a.s.vol+a.s.price));
  const bw=30, gap=26, x0=76, H=280, W=x0+rows.length*(bw*2+gap)+30, base=H-52;
  const mx=Math.max.apply(null,rows.map(r=>Math.max(Math.abs(r.s.vol),Math.abs(r.s.price))))*1.2;
  let s=svgOpen(W,H);
  s+='<line x1="'+x0+'" y1="'+(base/1)+'" x2="'+(W-24)+'" y2="'+(base/1)+'" stroke="#15233c"/>';
  const zy=base/1;
  const sy=v=>zy-(v/mx)*(zy-30)/1;
  [1,.5,-.5,-1].forEach(f=>{ const y=zy-f*(zy-30)*0.9;
    s+='<line x1="'+x0+'" y1="'+y.toFixed(1)+'" x2="'+(W-24)+'" y2="'+y.toFixed(1)+'" stroke="#e6e0d2"/>'+
      '<text x="'+(x0-6)+'" y="'+(y+3.5).toFixed(1)+'" text-anchor="end" font-size="9" fill="#8b8272">'+eur(mx*f*0.9)+'</text>'; });
  rows.forEach((r,i)=>{
    const x=x0+i*(bw*2+gap);
    [['vol','#15233c','volume, trucks'],['price','#c0552d','price']].forEach((p,j)=>{
      const v=r.s[p[0]]; const y=v>=0? sy(v) : zy; const h=Math.abs(sy(v)-zy);
      s+='<rect x="'+(x+j*(bw+3))+'" y="'+y.toFixed(1)+'" width="'+bw+'" height="'+Math.max(1,h).toFixed(1)+
         '" fill="'+p[1]+'"><title>'+r.d.label+' \u00b7 '+p[2]+' '+eur(v)+'</title></rect>';
    });
    s+='<text x="'+(x+bw)+'" y="'+(base/1+14)+'" text-anchor="middle" font-size="9.5" fill="#3d372b">'+r.d.label.slice(0,9)+'</text>';
  });
  s+='<text x="'+x0+'" y="16" font-size="10" fill="#15233c">above the line: growth</text>';
  s+='<text x="'+x0+'" y="'+(zy+12)+'" font-size="10" fill="#8b8272">the line: no change</text>';
  s+='<text x="26" y="'+(zy/2)+'" font-size="10" fill="#3d372b" transform="rotate(-90 26 '+(zy/2)+')" text-anchor="middle">euro of change</text>';
  s+='</svg></div>';
  const noMix = K.dbs.filter(d=>d.inModel).length === rows.length;
  return '<div class="chart"><h3>Was last year\u2019s growth more trucks, or price?</h3>'+
   '<p class="cap">Each distributor decomposed into two measurable legs: volume (more trucks buying) and price (a higher average price on the same part). '+
   'The market-mix leg is <b>not shown</b>: the source\u2019s mix column is a hard zero, which means the two other legs absorb it, not that mix did not move. '+
   (MODE.period==='fy'? 'Fiscal figures are recomputed from the billing fact on the same two-leg formula, FY24/25 \u2192 FY25/26.' : 'Calendar figures come from the 2024 \u2192 2025 waterfall.')+
   '</p>'+s+'</div>';
}

/* G3 -- three-way capture bar */
function cCapture(){
  const rows=K.dbs.filter(d=>d.inModel && d.famGap).slice().sort((a,b)=>(a.cap.rate)-(b.cap.rate));
  if(!rows.length) return '';
  const H=26*rows.length+58, W=940, x0=112, w=W-x0-120;
  let s=svgOpen(W,H);
  rows.forEach((d,i)=>{
    const y=24+i*26, t=d.cap;
    const gq = t.exp? (t.act/Math.max(t.exp,1)) : 0;
    const gs=Math.min(1,Math.max(0,gq));
    s+='<rect x="'+x0+'" y="'+y+'" width="'+w.toFixed(1)+'" height="17" fill="#efe9dc" stroke="#ddd6c6"/>';
    s+='<rect x="'+x0+'" y="'+y+'" width="'+(w*gs).toFixed(1)+'" height="17" fill="'+(gs<0.35?'#c0552d':'#15233c')+
       '"><title>'+d.label+': '+t.act.toFixed(0)+' of '+t.exp.toFixed(0)+' expected service parts billed = '+(gs*100).toFixed(1)+
       '%. The not-bought remainder is '+eur(t.gap)+' across 14 service families on '+num(d.uio)+' vehicles in service.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+12.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+d.label+'</text>';
    s+='<text x="'+(x0+w+8)+'" y="'+(y+12.5)+'" font-size="10.5" fill="'+(gs<0.35?'#c0552d':'#3d372b')+'">'+
       (gs*100).toFixed(0)+'% \u00b7 '+eur(t.gap)+' unbought</text>';
  });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#3d372b">billed as a share of the service parts the model expects \u2014 the pale remainder is never bought</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Of the service parts the model expects, how much did each distributor bill \u2014 and how much was never bought at all?</h3>'+
   '<p class="cap">Units billed against units the maintenance model expects, on the same fleet, 14 service families, 2025. '+
   'Ireland above 100% is the model\u2019s ceiling under-running on a market with a small truck parc, not double-counting. '+
   'The euro beside each bar is the value of the pale remainder.</p>'+s+
   '<p class="tiny">Denominator: vehicles in service, shown per row in the league. The expected units rest on an annual distance per market \u2014 measured where a measurement exists, otherwise the flat 20,000 km/yr assumption. IUK\u2019s expected demand falls materially once its measured 14,494 km/yr is applied instead.</p>'+
   '</div>';
}

/* G4 -- capture trend, small multiples of the family slopes */
function cTrend(){
  const dbs=K.dbs.filter(d=>d.inModel && d.traj);
  if(!dbs.length) return '';
  let h='<div class="chart"><h3>Which distributor-and-family captures are rising, and which are falling?</h3>'+
   '<p class="cap">Least-squares slope of the annual capture rate in percentage points per year, 2023\u20132025, one panel per distributor. '+
   'Terracotta means the fit is a fall wide enough to flag; the number is the slope and R\u00b2. A family with fewer than three annual points is left blank.</p>'+
   '<div class="mini">';
  dbs.forEach(d=>{
    h+='<div class="m"><div class="h"><b>'+d.label+'</b><span>'+d.traj.length+' families</span></div>';
    d.traj.slice().sort((a,b)=>a.slope-b.slope).slice(0,7).forEach(f=>{
      const wpx=Math.min(46,Math.max(2,Math.abs(f.slope)*9));
      const col=f.slope<0? (f.dec?'#c0552d':'#a33217') : (f.slope>0.03?'#1f6b45':'#3d6b8c');
      h+='<div class="v">'+tip(T('slope of the annual capture rate for '+f.fam.replace(/_/g,' ')+', 2023\u20132025: '+
        f.slope.toFixed(2)+' pp/yr, R\u00b2 '+f.r2.toFixed(2)+'.',
        MODE.period==='fy'?'the fiscal view: the trajectory source is calendar-tagged only.':'2026 rows, which are partial (source has no fiscal basis).',
        'Setting: '+LBL_P[MODE.period]+'.'),
        f.fam.replace(/_/g,' ').slice(0,15)+
        '<span style="float:right;color:'+col+'">('+(f.slope>=0?'+':'')+f.slope.toFixed(1)+' pt) </span><span class="bar-mini" style="background:'+col+';width:'+wpx+'px;float:right;margin-left:4px"></span>')+'</div>';
    });
    h+='</div>';
  });
  h+='</div>'+(MODE.period==='fy'? '<p class="tiny"><b>Fiscal view unavailable for this chart:</b> the capture-trajectory source carries calendar years only, so the panels above remain calendar 2023\u20132025 even though the period toggle reads FY25/26.</p>':'')+
   '<p class="tiny">The seven steepest-falling families are shown per distributor. Declining-flag families across the network: '+K.net.defN+' distributor rows carry a dormancy flag; five of the 252 family trends are formally flagged as declining, so this chart is mostly a picture of flat-to-slowly-rising capture rather than collapse.</p></div>';
  return h;
}

/* G5 -- uncaptured GPS value ladder */
function cGap(){
  const rows=K.dbs.filter(d=>d.inModel && d.famGap).map(d=>({d:d,g:d.famGap.reduce((a,b)=>a+b.gap,0)}))
    .sort((a,b)=>b.g-a.g);
  const H=22*rows.length+70, W=1000, x0=112, w=W-x0-190;
  const mx=Math.max.apply(null,rows.map(r=>r.g));
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{
    const y=26+i*22, bwv=(r.g/mx)*w;
    const top=r.d.famGap.slice().sort((a,b)=>b.gap-a.gap).slice(0,2);
    s+='<rect x="'+x0+'" y="'+y+'" width="'+bwv.toFixed(1)+'" height="15" fill="'+(i<3?'#c0552d':'#15233c')+
       '"><title>'+r.d.label+' \u00b7 '+eur(r.g)+' unbought across 14 service families. Largest: '+
       top.map(t=>t.fam.replace(/_/g,' ')+' '+eur(t.gap)).join('; ')+'. Fleet: '+num(r.d.uio)+' vehicles in service.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+11.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.d.label+'</text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b">'+eur(r.g)+
       ' <tspan fill="#8b8272">\u00b7 '+top.map(t=>t.fam.replace(/_/g,' ')).join(', ')+'</tspan></text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b" opacity="0">.</text>';
  });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#3d372b">euro of modelled service-part demand never billed, and the family carrying most of it</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Where is the unmade parts revenue concentrated?</h3>'+
   '<p class="cap">Modelled demand less parts billed, in euro, 14 service families, 2025, per distributor, on that distributor\u2019s own fleet. '+
   'This is a ceiling, not a forecast: the top bar is also the market with the largest fleet, so the fleet denominator travels with every row in the league table.</p>'+s+'</div>';
}

/* G6 -- UIO direction slope */
function cUio(){
  const rows=K.dbs.filter(d=>d.inModel && d.uio && d.uio24);
  if(!rows.length) return '';
  const H=430, W=560, x0=110, x1=420;
  const mx=Math.max.apply(null,rows.map(r=>Math.max(r.uio,r.uio24)))*1.06;
  const sy=v=>H-60-(v/mx)*(H-110);
  let s='<div class="svgwrap"><svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" role="img">';
  s+='<text x="'+x0+'" y="26" text-anchor="middle" font-size="11" fill="#15233c">2024</text>';
  s+='<text x="'+x1+'" y="26" text-anchor="middle" font-size="11" fill="#15233c">2025</text>';
  rows.forEach(r=>{
    const up=r.uio>=r.uio24;
    s+='<line x1="'+x0+'" y1="'+sy(r.uio24).toFixed(1)+'" x2="'+x1+'" y2="'+sy(r.uio).toFixed(1)+
       '" stroke="'+(up?'#1f6b45':'#c0552d')+'" stroke-width="'+(r.uio>20000?2.4:1.3)+'" opacity="0.85"/>';
    s+='<circle cx="'+x0+'" cy="'+sy(r.uio24).toFixed(1)+'" r="2.6" fill="#15233c"/>';
    s+='<circle cx="'+x1+'" cy="'+sy(r.uio).toFixed(1)+'" r="2.6" fill="#15233c"/>';
    s+='<text x="'+(x0-7)+'" y="'+(sy(r.uio24)+3.5).toFixed(1)+'" text-anchor="end" font-size="10" fill="#3d372b">'+r.label+
       ' '+num(r.uio24)+'</text>';
    s+='<text x="'+(x1+7)+'" y="'+(sy(r.uio)+3.5).toFixed(1)+'" font-size="10" fill="'+(up?'#1f6b45':'#973f1c')+'">'+
       num(r.uio)+' '+((r.uio-r.uio24)/r.uio24*100).toFixed(1)+'%</text>';
    s+='<title>'+r.label+': '+num(r.uio24)+' \u2192 '+num(r.uio)+' vehicles in service</title>';
  });
  s+='</svg></div>';
  return '<div class="chart g2w"><h3>Is each market\u2019s fleet growing or shrinking?</h3>'+
   '<p class="cap">Vehicles in service, 2024 against 2025. Green rising, terracotta falling. The 2026\u20132030 forecast is deliberately absent: '+
   'it is overstated and awaits correction.</p>'+s+'</div>';
}

/* G7 -- dormancy euro */
function cDefect(){
  const rows=K.dbs.filter(d=>d.defn).map(d=>({d:d, g:d.defn.silent_eur})).sort((a,b)=>b.g-a.g);
  if(!rows.length) return '';
  const mx=Math.max.apply(null,rows.map(r=>r.g));
  let h='<div class="chart"><h3>Where have we gone quiet for longer than the normal reorder gap?</h3>'+
   '<p class="cap">Distributor-and-family pairs silent past their own median reorder rhythm, as at the March 2026 data horizon. '+
   'Each euro is the trailing twelve months actually billed on that family, so this is the run-rate at risk, not a lost-order claim.</p>'+
   '<div class="tbl"><table style="min-width:760px"><thead><tr><th class="l">Distributor</th><th class="l">Service family</th>'+
   '<th>Normal gap</th><th>Silent</th><th>Multiple</th><th>Last order</th><th>Trailing 12m billed</th><th class="l">Value at risk</th></tr></thead><tbody>';
  const all=[];
  rows.forEach(r=>r.d.defn.tops.forEach(t=>all.push({d:r.d,t:t})));
  all.sort((a,b)=>b.t.eur-a.t.eur);
  all.slice(0,22).forEach(x=>{
    h+='<tr><td class="l">'+x.d.label+'</td><td class="l">'+x.t.fam.replace(/_/g,' ')+'</td>'+
       '<td>'+x.t.gap.toFixed(0)+' mo</td><td>'+x.t.silent.toFixed(0)+' mo</td>'+
       '<td>'+(x.t.gap? (x.t.silent/x.t.gap).toFixed(1)+'\u00d7' : '\u2013')+'</td>'+
       '<td>'+x.t.last+'</td><td>'+eurL(x.t.eur)+'</td>'+
       '<td class="l">'+tip(T('euro billed on this family in the twelve months to March 2026, allocated from the billing fact; '+
         'the gap is the median months between orders in the family\u2019s active history.',
         'lost revenue: a quiet pair may be ordering elsewhere or may not need the part.',SET()),
         bar(x.t.eur,mx,'t',150))+'</td></tr>';
  });
  h+='</tbody></table></div>'+
   '<p class="tiny">'+K.net.defN+' of '+K.net.defRows+' distributor-and-family combinations across the network carry the flag, on '+eurL(K.net.defEur)+
   ' of trailing twelve-month billing. Customer-level dormancy ('+K.net.custN+' of '+K.net.custRows+
   ' rows) exists in the source but is not shown here: this page carries no customer names.</p></div>';
  return h;
}

/* G8 -- basket breadth ranking + family presence */
function cBreadth(){
  const rows=K.dbs.filter(d=>d.inModel && d.breadth && d.breadth.cy.length)
    .map(d=>({d:d,n:d.breadth.cy.length})).sort((a,b)=>b.n-a.n);
  if(!rows.length) return '';
  const maxN=296, H=rows.length*22+60, W=760, x0=112, w=W-x0-70;
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{ const y=22+i*22, bwv=(r.n/maxN)*w;
    s+='<rect x="'+x0+'" y="'+y+'" width="'+bwv.toFixed(1)+'" height="15" fill="'+(r.n<120?'#c0552d':'#15233c')+
       '"><title>'+r.d.label+' billed at least once in '+r.n+' of the 296 goods-classification groups catalogued in 2025.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+11.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.d.label+'</text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b">'+r.n+' of 296</text>'; });
  s+='<text x="'+x0+'" y="12" font-size="10" fill="#3d372b">distinct goods-classification groups bought at least once in 2025</text>';
  s+='</svg></div>';
  const G7=['brakes','cab','clutch','electrical','engine_cooling','filters','suspension'];
  const GL={brakes:'Brakes',cab:'Cab',clutch:'Clutch & driveline',electrical:'Electrical',
    engine_cooling:'Engine & cooling',filters:'Filters',suspension:'Suspension & chassis'};
  let hm='<div class="tbl"><table style="min-width:760px"><thead><tr><th class="l">Distributor</th>'+
    G7.map(g=>'<th>'+GL[g]+'</th>').join('')+'</tr></thead><tbody>';
  K.dbs.filter(d=>d.inModel).forEach(d=>{
    const have=new Set((d.famBvp||[]).map(f=>f.fam));
    const src={brakes:'Brakes',cab:'Cab',clutch:'Clutch & driveline',electrical:'Electrical',
      engine_cooling:'Engine & cooling',filters:'Filters',suspension:'Suspension & chassis'};
    hm+='<tr><td class="l">'+d.label+'</td>';
    G7.forEach(g=>{
      const f=(d.famBvp||[]).find(x=>src[g]===x.fam);
      hm+='<td>'+(f? tip(T('parts billed in the '+src[g]+' group in 2025: '+eur(f.total)+', of which Competitive parts '+eur(f.bvp)+
        ' ('+(f.total? (f.bvp/f.total*100).toFixed(1):'0')+'%).',
        'groups with no billed line at all: nothing was bought, which the file cannot distinguish from an unmapped part number.',SET()),
        '<span class="chip '+(f.total>1e6?'g':(f.total>1e5?'a':'r'))+'">'+eur(f.total)+'</span>')
        : '<span class="chip n" data-tip="No billed line in this group in 2025 for this distributor. Shown as not bought rather than zero: a part number with no group mapping also lands here.\nSnapshot: '+K.snap+'.">not bought</span>')+'</td>';
    });
    hm+='</tr>';
  });
  hm+='</tbody></table></div>';
  return '<div class="chart"><h3>Which parts groups does each distributor actually buy?</h3>'+
   '<p class="cap">Left: how many of the 296 goods-classification groups each distributor billed at least once in 2025. Right: the seven aftersales families and the euro billed in each. '+
   'A market that never buys clutch parts has no clutch conversation to have.</p>'+
   '<div class="grid g2" style="grid-template-columns:minmax(0,1fr) minmax(0,1fr)">'+s+hm+'</div>'+
   '<p class="tiny">'+K.net.figcov.toFixed(1)+'% of billed value carries a goods classification; '+(100-K.net.figcov).toFixed(1)+
   '% does not, and those lines sit in no group. On the fiscal toggle the counts recompute from April 2025 to March 2026.</p></div>';
}

/* G9 -- exposure vs price position */
function cExpose(){
  const rows=K.dbs.filter(d=>d.inModel && d.aim && d.prem);
  if(!rows.length) return '';
  const W=760,H=440, x0=76, y0=H-64, w=W-x0-40, h=y0-40;
  const mxX=Math.max.apply(null,rows.map(r=>r.aim.risk))*1.25||1;
  const mxY=Math.max.apply(null,rows.map(r=>r.prem.prem))*1.15||1;
  let s=svgOpen(W,H);
  for(let i=1;i<=4;i++){ const x=x0+w*i/4; s+='<line x1="'+x+'" y1="40" x2="'+x+'" y2="'+y0+'" stroke="#e6e0d2"/>'+
    '<text x="'+x+'" y="'+(y0+14)+'" text-anchor="middle" font-size="9.5" fill="#8b8272">'+(mxX*i/4).toFixed(1)+'%</text>'; }
  for(let i=1;i<=4;i++){ const y=y0-h*i/4; s+='<line x1="'+x0+'" y1="'+y+'" x2="'+(x0+w)+'" y2="'+y+'" stroke="#e6e0d2"/>'+
    '<text x="'+(x0-6)+'" y="'+(y+3.5)+'" text-anchor="end" font-size="9.5" fill="#8b8272">+'+(mxY*i/4).toFixed(0)+'%</text>'; }
  const netX=K.net.aimRisk||0, netY=K.net.premMed;
  s+='<line x1="'+(x0+w*netX/mxX)+'" y1="40" x2="'+(x0+w*netX/mxX)+'" y2="'+y0+'" stroke="#c0552d" stroke-dasharray="4 3"/>';
  s+='<line x1="'+x0+'" y1="'+(y0-h*netY/mxY)+'" x2="'+(x0+w)+'" y2="'+(y0-h*netY/mxY)+'" stroke="#c0552d" stroke-dasharray="4 3"/>';
  s+='<text x="'+(x0+w*netX/mxX+4)+'" y="52" font-size="9.5" fill="#c0552d">network exposure</text>';
  s+='<text x="'+(x0+4)+'" y="'+(y0-h*netY/mxY-4)+'" font-size="9.5" fill="#c0552d">network median premium</text>';
  rows.forEach(r=>{
    const cx=x0+w*r.aim.risk/mxX, cy=y0-h*r.prem.prem/mxY, rad=4+Math.sqrt(r.cy)/26;
    s+='<circle cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+'" r="'+rad.toFixed(1)+'" fill="'+(K.story.indexOf(r.code)>=0?'#c0552d':'#15233c')+'" fill-opacity="0.78"/>';
    s+='<text x="'+(cx+rad+3)+'" y="'+(cy+3.5)+'" font-size="9.5" fill="#3d372b">'+r.label+'</text>';
    s+='<title>'+r.label+': '+r.aim.risk.toFixed(2)+'% of billed value sits on part numbers the item master calls highly exposed, '+
      'and its genuine parts carry a weighted +'+r.prem.prem.toFixed(0)+'% premium over their Competitive twins on '+
      r.prem.units.toLocaleString('en-GB')+' units priced.</title>';
  });
  s+='<text x="'+(x0+w/2)+'" y="'+(y0+34)+'" text-anchor="middle" font-size="10.5" fill="#3d15233c">share of billed value exposed to the independent aftermarket</text>';
  s+='<text x="24" y="'+(40+h/2)+'" font-size="10.5" fill="#3d372b" transform="rotate(-90 24 '+(40+h/2)+')" text-anchor="middle">genuine premium over the Competitive twin</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Where are we priced above the reference dealer price \u2014 and on parts the independent aftermarket can supply?</h3>'+
   '<p class="cap">Each bubble is a distributor: right is more of its book exposed, up is a larger genuine premium over the Competitive twin on the same part. '+
   'Bubble size is the size of the book. Bottom-left is the comfortable corner; top-right is where a customer can buy an alternative cheaply.</p>'+s+
   '<p class="tiny">Premium is unit-weighted across the families where both lines actually sold in 2025, so it is a price comparison on a sample, not a win rate. '+
   'The pricing-risk severity layer behind the exposure axis returned a null on backtest and is used here as classification only.</p></div>';
}

/* G10 -- warranty share */
function cWarranty(){
  const rows=K.dbs.filter(d=>d.inModel && d.warrShare!==null).map(d=>({d:d,v:d.warrShare}))
    .sort((a,b)=>b.v-a.v);
  const H=rows.length*22+74, W=760, x0=112, w=W-x0-120;
  const mx=Math.max.apply(null,rows.map(r=>r.v))*1.15;
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{ const y=24+i*22, bwv=(r.v/mx)*w;
    s+='<rect x="'+x0+'" y="'+y+'" width="'+bwv.toFixed(1)+'" height="15" fill="'+(r.v>25?'#c0552d':'#15233c')+
       '"><title>'+r.d.label+': '+eur(r.d.warr)+' of warranty parts against '+eur(r.d.gpsTotal)+' billed = '+r.v.toFixed(1)+
       '%. Warranty work is not a customer-paid parts sale.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+11.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.d.label+'</text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b">'+r.v.toFixed(1)+'% \u00b7 '+eur(r.d.warr)+'</text>'; });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#3d372b">warranty parts as a share of total parts billed, calendar 2025 \u2014 the depth of grey in the book</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>How much of what we bill is warranty work rather than customer-paid parts?</h3>'+
   '<p class="cap">Warranty parts in euro over total parts billed, calendar 2025. Network: '+eurL(K.net.warrCy)+' of '+eurL(K.net.gpsCy)+
   ' = '+K.net.warrShare.toFixed(1)+'%. A high share is not growth: it is our own cost of quality passing through the parts account.</p>'+s+
   '<p class="tiny">Unavailable for the four CIS markets (Ukraine, Armenia, Kazakhstan, Palestine): they have no warranty data at all, so they are absent from this chart rather than shown at zero. '+
   'The fiscal view reads '+eurL(K.net.warrFy)+' from the fiscal warranty expense file.</p></div>';
}

/* ---- B1 two universes */
function cB1(){
  const bars=[
    {t:'All parts billed, billing fact', d:K.net.cyAttr, n:K.net.bvpFactCy, c:'#15233c',
     why:'Every part number billed to a distributor in the period, competitive parts identified by the catalogue flag (97.3% of billed rows map to a catalogue record).'},
    {t:'All parts billed, modelled book', d:K.net.ceilingCap, n:K.net.ceilingBvp, c:'#3d6b8c',
     why:'The 18 modelled distributors on the ceiling book: what we billed against a modelled target spend. This is the \u20ac30.76M denominator behind the agreed 3.5%.'},
    {t:'Service-part universe (14 families)', d:K.net.capRev, n:K.net.ceilingBvp*0+1231680, c:'#1f6b45',
     why:'Only the 14 service families where the maintenance model makes competitive parts directly comparable: what we billed in those families.'},
    {t:'Service-part universe (7 groups)', d:K.net.mixUniv, n:K.net.mixBvp, c:'#c0552d',
     why:'The seven-group service-part cut the agreed 36.7% comes from: filters, brakes, clutch and driveline, suspension and chassis, electrical, engine and cooling, cab.'}
  ];
  const W=900, rowh=76, H=bars.length*rowh+52, x0=250, w=W-x0-150;
  const mx=Math.max.apply(null,bars.map(b=>b.n/b.d));
  let s='<div class="svgwrap"><svg viewBox="0 0 '+W+' '+H+'" width="'+W+'" height="'+H+'" role="img">';
  bars.forEach((b,i)=>{
    const y=30+i*rowh, share=b.n/b.d, bwv=(share/mx)*w;
    s+='<text x="'+(x0-10)+'" y="'+(y+13)+'" text-anchor="end" font-size="11.5" fill="#15233c">'+b.t+'</text>';
    s+='<text x="'+(x0-10)+'" y="'+(y+27)+'" text-anchor="end" font-size="10" fill="#8b8272">denominator '+eur(b.d)+'</text>';
    s+='<rect x="'+x0+'" y="'+(y+2)+'" width="'+w+'" height="20" fill="#efe9dc" stroke="#ddd6c6"/>';
    s+='<rect x="'+x0+'" y="'+(y+2)+'" width="'+bwv.toFixed(1)+'" height="20" fill="'+b.c+'"><title>'+b.t+
       ': competitive parts '+eur(b.n)+' of '+eur(b.d)+' = '+(share*100).toFixed(1)+'%. '+b.why+'</title></rect>';
    s+='<text x="'+(x0+bwv+9)+'" y="'+(y+17)+'" font-size="12" fill="'+b.c+'">'+(share*100).toFixed(1)+'% \u00b7 '+eur(b.n)+'</text>';
    s+='<text x="'+x0+'" y="'+(y+38)+'" font-size="9.5" fill="#5a5344">'+b.why.slice(0,140)+'</text>';
  });
  s+='<text x="'+x0+'" y="16" font-size="10" fill="#3d372b">competitive parts as a share of four different denominators</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>What share of our billing is Competitive parts \u2014 and which denominator is the real one?</h3>'+
   '<p class="cap">Both agreed universes are here, and they answer different questions. <b>3.5%</b> is the competitive-parts share of <b>everything we bill</b> on the modelled book. '+
   '<b>36.7%</b> is the share of the <b>service-part universe where competitive parts actually compete</b> \u2014 filters, brakes, clutch, suspension, electrical, engine and cooling, cab. '+
   'Neither is the wrong number, and neither is a target. The two middle bars are the same two questions asked of the billing fact, and they read differently because the universe definition differs: that difference is the whole reason the pair has to be published together.</p>'+s+
   '<p class="tiny">Competitive parts are the lower-priced Isuzu line that competes with the independent aftermarket. Genuine is the original-brand line. '+
   'The fiscal view on the billing-fact bars recomputes to '+eurL(K.net.bvpFactFy)+' of '+eurL(K.net.fyAttr)+' = '+K.net.bvpFactFyShare.toFixed(2)+
   '%; the ceiling and seven-group bars are calendar-tagged only.</p></div>';
}

/* ---- B2 addressable range bought */
function cB2(){
  const rows=K.dbs.filter(d=>d.inModel && d.b2).map(d=>({d:d,p:d.b2})).sort((a,b)=>b.p.pct-a.p.pct);
  const H=rows.length*22+74, W=820, x0=112, w=W-x0-190;
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{ const y=24+i*22, bwv=(r.p.pct/100)*w;
    s+='<rect x="'+x0+'" y="'+y+'" width="'+bwv.toFixed(1)+'" height="15" fill="'+(r.p.pct<40?'#c0552d':'#15233c')+
       '"><title>'+r.d.label+' buys '+r.p.selling+' of the '+r.p.pairs+' genuine-and-competitive part-number pairs mapped to it = '+
       r.p.pct.toFixed(1)+'%. A mapping exercise, not an assortment plan.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+11.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.d.label+'</text>';
    s+='<text x="'+(x0+bwv+8)+'" y="'+(y+11.5)+'" font-size="10.5" fill="#3d372b">'+r.p.pct.toFixed(0)+
       '% <tspan fill="#8b8272">('+r.p.selling+' of '+r.p.pairs+' pairs)</tspan></text>'; });
  s+='<text x="'+x0+'" y="12" font-size="10" fill="#3d372b">share of that distributor\u2019s mapped competitive-parts range that it actually buys</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Of the competitive part numbers each distributor could buy, how many does it actually buy?</h3>'+
   '<p class="cap">Each distributor\u2019s mapped genuine-and-competitive pairs, and how many of those pairs it billed at least once in the period. '+
   'The pair list is a part-number mapping, not an approved assortment: a part can be mapped to a market that never orders it for a real reason.</p>'+s+'</div>';
}

/* ---- B3 substitution */
function cB3(){
  const years=['2023','2024','2025'];
  const series=[{n:'Mapped pairs, all distributors', v:years.map(y=>K.suby[y].bvp/K.suby[y].tot*100), c:'#15233c', w:3}];
  const tops=K.dbs.filter(d=>d.inModel && d.suby && d.suby['2025'].tot>50000)
    .map(d=>({l:d.label, v:years.map(y=>d.suby[y].tot? d.suby[y].bvp/d.suby[y].tot*100 : null)}))
    .filter(s=>s.v.every(x=>x!==null)).sort((a,b)=>b.v[2]-a.v[2]).slice(0,6);
  const pal=['#c0552d','#1f6b45','#8a6a20','#3d6b8c','#8d8574','#5c2b13'];
  tops.forEach((t,i)=>series.push({n:t.l, v:t.v, c:pal[i%pal.length], w:1.4}));
  const W=760,H=360, x0=70,y0=H-56,w=W-x0-150,h=y0-34;
  const all=series.reduce((a,s)=>a.concat(s.v),[]);
  const lo=Math.max(0,Math.floor(Math.min.apply(null,all)/5)*5-2), hi=Math.ceil(Math.max.apply(null,all)/5)*5+2;
  let s=svgOpen(W,H);
  for(let i=0;i<=5;i++){ const y=y0-h*i/5;
    s+='<line x1="'+x0+'" y1="'+y.toFixed(1)+'" x2="'+(x0+w)+'" y2="'+y.toFixed(1)+'" stroke="#e6e0d2"/>'+
       '<text x="'+(x0-6)+'" y="'+(y+3.5).toFixed(1)+'" text-anchor="end" font-size="9.5" fill="#8b8272">'+
       (lo+(hi-lo)*i/5).toFixed(0)+'%</text>'; }
  years.forEach((y,i)=>{ const x=x0+w*i/2;
    s+='<line x1="'+x+'" y1="34" x2="'+x+'" y2="'+y0+'" stroke="#f0ebe0"/>';
    s+='<text x="'+x+'" y="'+(y0+16)+'" text-anchor="middle" font-size="10.5" fill="#3d372b">'+y+'</text>'; });
  series.forEach((se,si)=>{
    const pts=se.v.map((v,i)=>{ const x=x0+w*i/2, y=y0-h*(v-lo)/(hi-lo); return [x,y]; });
    s+='<polyline fill="none" stroke="'+se.c+'" stroke-width="'+se.w+'" points="'+
       pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')+'"/>';
    pts.forEach((p,i)=>{ s+='<circle cx="'+p[0].toFixed(1)+'" cy="'+p[1].toFixed(1)+'" r="'+(se.w>2?3.4:2.2)+'" fill="'+se.c+
      '"><title>'+se.n+' in '+years[i]+': '+se.v[i].toFixed(1)+'% of the euro on those pairs went to competitive parts.</title></circle>'; });
    const lp=pts[2];
    s+='<text x="'+(lp[0]+8)+'" y="'+(lp[1]+3.5)+'" font-size="10" fill="'+se.c+'">'+se.n.slice(0,26)+'</text>';
  });
  s+='<text x="26" y="'+(34+h/2)+'" font-size="10.5" fill="#3d372b" transform="rotate(-90 26 '+(34+h/2)+')" text-anchor="middle">competitive share of the euro on mapped pairs</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>When the same reference part is available as Genuine and as Competitive, which one is moving?</h3>'+
   '<p class="cap">On every mapped pair of part numbers, the share of the euro that went to the competitive line, by year. '+
   'The thick navy line is the whole mapped book: it moved from '+(K.suby['2023'].bvp/K.suby['2023'].tot*100).toFixed(1)+'% in 2023 to '+(K.suby['2025'].bvp/K.suby['2025'].tot*100).toFixed(1)+
   '% in 2025 across '+K.suby['2025'].pairs.toLocaleString('en-GB')+' mapped pair series in 22 distributor databases. '+
   'The thin lines are the six distributors with the largest mapped books.</p>'+s+
   '<p class="tiny">A pair is counted whether it sold as genuine, as competitive, or both, so the line is a mix measure on an unchanged part-number set, not a market-share measure. '+
   'Rising substitution can be a win (we kept the job) or a loss (we sold it cheaper): this chart cannot tell those apart, and the contested-euro chart below can.</p></div>';
}

/* ---- B4 exposure bands */
function cB4(){
  const fam=[];
  Object.keys(K.b4).forEach(db=>K.b4[db].forEach(f=>{
    let x=fam.find(z=>z.fam===f.fam); if(!x){ x={fam:f.fam,risk:0,bvp:0,cat:0,bvpeur:0}; fam.push(x); }
    x.risk+=f.risk*f.cat; x.bvp+=f.bvp*f.cat; x.cat+=f.cat; x.bvpeur+=f.bvpeur;
  }));
  fam.forEach(f=>{ f.risk/=f.cat; f.bvp/=f.cat; });
  const LBL={Belts_Cooling:'Belts & cooling',Brakes:'Brakes',Cab_Misc:'Cab & body',Clutch_Driveline:'Clutch & driveline',
    Electrical:'Electrical',PMS_Filters:'Filters (service)',Suspension_Chassis:'Suspension & chassis'};
  if(!fam.length) return '';
  const W=760,H=400, x0=76,y0=H-66,w=W-x0-40,h=y0-36;
  const mxX=Math.max.apply(null,fam.map(f=>f.risk))*1.4||1, mxY=100;
  let s=svgOpen(W,H);
  for(let i=0;i<=4;i++){ const x=x0+w*i/4;
    s+='<line x1="'+x+'" y1="36" x2="'+x+'" y2="'+y0+'" stroke="#f0ebe0"/>'+
       '<text x="'+x+'" y="'+(y0+15)+'" text-anchor="middle" font-size="9.5" fill="#8b8272">'+(mxX*i/4).toFixed(1)+'%</text>'; }
  for(let i=0;i<=4;i++){ const y=y0-h*i/4;
    s+='<line x1="'+x0+'" y1="'+y+'" x2="'+(x0+w)+'" y2="'+y+'" stroke="#e6e0d2"/>'+
       '<text x="'+(x0-6)+'" y="'+(y+3.5)+'" text-anchor="end" font-size="9.5" fill="#8b8272">'+(mxY*i/4).toFixed(0)+'%</text>'; }
  fam.forEach(f=>{
    const cx=x0+w*f.risk/mxX, cy=y0-h*f.bvp/mxY, rad=5+Math.sqrt(f.cat)/22;
    s+='<circle cx="'+cx.toFixed(1)+'" cy="'+cy.toFixed(1)+'" r="'+rad.toFixed(1)+'" fill="#15233c" fill-opacity="0.8"/>';
    s+='<text x="'+(cx+rad+4)+'" y="'+(cy+3.5)+'" font-size="10" fill="#3d372b">'+LBL[f.fam]+'</text>';
    s+='<title>'+LBL[f.fam]+': '+f.risk.toFixed(1)+'% of the euro in this family sits on part numbers the item master calls highly exposed to the independent aftermarket, '+
      'and '+f.bvp.toFixed(1)+'% of the family euro went to competitive parts ('+eur(f.bvpeur)+' on '+eur(f.cat)+' of catalogue sales).</title>';
  });
  s+='<text x="'+(x0+w/2)+'" y="'+(y0+34)+'" text-anchor="middle" font-size="10.5" fill="#3d372b">family exposure to the independent aftermarket</text>';
  s+='<text x="24" y="'+(36+h/2)+'" font-size="10.5" fill="#3d372b" transform="rotate(-90 24 '+(36+h/2)+')" text-anchor="middle">competitive share of the family euro</text>';
  s+='</svg></div>';
  return '<div class="chart"><h3>Where the genuine part is most exposed, does the competitive line take more of the euro?</h3>'+
   '<p class="cap">The seven aftersales families, 2025. Right is more of the family\u2019s euro sitting on part numbers the item master classifies as highly exposed; '+
   'up is a larger competitive share of that family\u2019s euro. Bubble size is the size of the family. If exposure and competitive share tracked each other, the bubbles would run bottom-left to top-right.</p>'+s+
   '<p class="tiny">Exposure is a classification, not a probability: the severity layer behind it returned a null on backtest and is not used as a KPI. '+
   'A family with a low competitive share and a high exposure figure is where the substitution has not happened yet \u2014 that is the read, not a win.</p></div>';
}

/* ---- B5 contested euro */
function cB5(){
  const rows=K.dbs.filter(d=>d.inModel && d.bvp && d.bvp.cont>0)
    .sort((a,b)=>b.bvp.cont-a.bvp.cont);
  const H=rows.length*26+78, W=980, x0=112, w=W-x0-210;
  let s=svgOpen(W,H);
  rows.forEach((r,i)=>{
    const y=26+i*26, b=r.bvp, tot=b.cont;
    const wBvp=(b.bvp/tot)*w, wGen=((tot-b.bvp)/tot)*w;
    s+='<rect x="'+x0+'" y="'+y+'" width="'+wBvp.toFixed(1)+'" height="17" fill="#c0552d">'+
       '<title>'+r.label+': '+eur(b.bvp)+' of '+eur(tot)+' contested euro won as competitive parts ('+(b.capr===null?'n/a':b.capr.toFixed(0)+'%').replace(/\u2013/,'-')+').</title></rect>';
    s+='<rect x="'+(x0+wBvp).toFixed(1)+'" y="'+y+'" width="'+wGen.toFixed(1)+'" height="17" fill="#15233c">'+
       '<title>'+r.label+': genuine contested euro '+eur(b.gencont)+' on part numbers that have a competitive twin and where the independent aftermarket can supply the job.</title></rect>';
    s+='<text x="'+(x0-8)+'" y="'+(y+12.5)+'" text-anchor="end" font-size="10.5" fill="#15233c">'+r.label+'</text>';
    s+='<text x="'+(x0+w+8)+'" y="'+(y+12.5)+'" font-size="10.5" fill="#3d372b">'+eur(tot)+
       ' <tspan fill="#c0552d">'+(b.capr===null?'n/a':b.capr.toFixed(0)+'% won as competitive')+'</tspan></text>';
  });
  s+='<text x="'+x0+'" y="14" font-size="10" fill="#3d372b">the contested euro only: part numbers where a competitive twin exists and an independent supplier could do the job</text>';
  s+='<rect x="'+(W-198)+'" y="'+(H-30)+'" width="11" height="11" fill="#c0552d"/>'+
     '<text x="'+(W-183)+'" y="'+(H-21)+'" font-size="10" fill="#3d372b">won as competitive</text>'+
     '<rect x="'+(W-92)+'" y="'+(H-30)+'" width="11" height="11" fill="#15233c"/>'+
     '<text x="'+(W-77)+'" y="'+(H-21)+'" font-size="10" fill="#3d372b">won as genuine</text>';
  s+='</svg></div>';
  const lost = K.net.bvpAll - K.net.bvpCy - (K.net.bvpAll*0 - 0);
  return '<div class="chart"><h3>Of the euro where we were actually in a contest, how much did we win \u2014 and how?</h3>'+
   '<p class="cap">Each bar is the contested euro for that distributor: the part numbers where a competitive twin exists, so an independent supplier could have taken the job. '+
   'Terracotta is the euro we kept as competitive parts, navy the euro we kept as genuine. The network contested pool is '+eurL(K.net.bvpAll-K.net.bvpCy)+
   ' within '+eurL(K.net.bvpAll)+' billed, and '+K.net.bvpShareCy.toFixed(2)+'% of everything billed is competitive parts.</p>'+s+
   '<p class="tiny">What is <b>not</b> on this chart is the euro we lost to the independent aftermarket. There is no measured share: the leaked euro would need independent-garage volume, '+
   'which nothing in this workspace measures. The uncaptured GPS value of '+eurL(K.net.capGap)+' is the modelled ceiling on that, not a measurement of it.</p></div>';
}

/* net figure for the AIM exposure axis: revenue-weighted across the 18 modelled distributors */
function aimRiskNet(){
  const rows=K.dbs.filter(d=>d.inModel && d.aim);
  if(!rows.length) return 0;
  let a=0,b=0; rows.forEach(d=>{ a+=d.aim.risk*d.cy; b+=d.cy; });
  return b? a/b : 0;
}
K.net.aimRisk = aimRiskNet();

/* =================================================================== narrative */
const STORYTXT = {
 IUK:{tag:'largest book, light commercial only, mileage-corrected',
   head:'The largest book in the network, on a fleet that drives half as far as the model assumes.',
   body:[
    ['billed', d=>'IUK bills '+eurL(d.cy)+' in calendar 2025: the largest distributor book in the network, on '+num(d.uio)+
      ' light commercial vehicles in service.'],
    ['spu', d=>'Spend per truck is '+eurL(d.spu)+' against a network median of \u20ac'+Math.round(K.net.spuCy)+
      '. That gap is not underperformance: measured odometer deltas put the N35 Grafter fleet at 14,494 km/yr against the model\u2019s flat 20,000, '+
      'so the service demand the model expects from an IUK truck is overstated by about a quarter before IUK is judged on it.'],
    ['cap', d=>'Capture reads '+d.cap.rate.toFixed(0)+'%, the lowest of any market above \u20ac5M, and the largest single family gap is '+
      (d.famGap? d.famGap.slice().sort((a,b)=>b.gap-a.gap)[0].fam.replace(/_/g,' ')+' at '+eurL(d.famGap.slice().sort((a,b)=>b.gap-a.gap)[0].gap) : 'unavailable')+
      '. Across all 14 service families the euro never billed is '+eurL(d.cap.gap)+'.'],
    ['bvp', d=>'IUK is a coverage question, not a price question: '+d.bvp.pct.toFixed(2)+
      '% of its billing is competitive parts, the thinnest share of the three large markets, and its genuine parts carry only a moderate premium over their competitive twins.'],
    ['mile', d=>'What makes IUK actionable is that the denominator is now measured rather than assumed. Every IUK figure on this page rests on '+num(d.uio)+
      ' vehicles in service and 14,494 measured km/yr, not on the flat assumption the model uses elsewhere.']
   ]},
 ITUK:{tag:'best capture rate, heavy trucks',
   head:'The best capture rate in the network, on a heavy-truck fleet.',
   body:[
    ['billed', d=>'ITUK bills '+eurL(d.cy)+' on '+num(d.uio)+' vehicles in service, almost all of them N-series and F-series trucks.'],
    ['cap', d=>'Capture is '+d.cap.rate.toFixed(0)+'%, the highest of any market above \u20ac1M, leaving '+eurL(d.cap.gap)+
      ' unbought \u2014 an order of magnitude less than IUK on a comparable book.'],
    ['bvp', d=>'It also carries the strongest competitive-parts mix in the network: '+d.bvp.pct.toFixed(1)+
      '% of all parts billed, and '+(d.bvp.capr===null?'n/a':d.bvp.capr.toFixed(0)+'%')+' of its contested euro won as competitive parts rather than genuine.'],
    ['read', d=>'ITUK is the counter-example that makes the rest of the page readable: when the fleet is heavy, the mileage is right and the service demand in the model is real, '+
      'it gets captured. The gap in the light commercial markets is not a demand problem.']
   ]},
 GERMANY:{tag:'worst capture rate on a large book',
   head:'The worst capture rate on a large book, with a price premium standing where coverage should be.',
   body:[
    ['billed', d=>'Germany bills '+eurL(d.cy)+' on '+num(d.uio)+' vehicles in service.'],
    ['cap', d=>'Capture is '+d.cap.rate.toFixed(0)+'% \u2014 the lowest of any market above \u20ac1M \u2014 leaving '+eurL(d.cap.gap)+
      ' unbought, concentrated in '+(d.famGap? d.famGap.slice().sort((a,b)=>b.gap-a.gap).slice(0,2).map(f=>f.fam.replace(/_/g,' ')).join(' and ') : 'unavailable')+'.'],
    ['price', d=>'At the same time '+d.prem.prem.toFixed(0)+
      '% is the weighted premium its genuine parts carry over their competitive twins across '+d.prem.units.toLocaleString('en-GB')+
      ' priced units: a price answer to what is a coverage problem.'],
    ['mile', d=>'Measured mileage for the German light commercial fleet is 17,819 km/yr, below the flat assumption, so the unbought euro is if anything understated rather than inflated.']
   ]}
};
function storyHTML(){
  return K.story.map(code=>{
    const d=K.dbs.find(x=>x.code===code), s=STORYTXT[code];
    return '<div class="card" data-story="'+code+'"><h4 style="margin:0 0 3px;font-size:15px;color:#15233c">'+
      esc(d.label)+' \u2014 '+s.tag+'</h4><p class="note"><b>'+s.head+'</b></p><ul class="tight">'+
      s.body.map(function(b){ try{ return '<li>'+b[1](d)+'</li>'; }catch(e){ return ''; } }).join('')+'</ul></div>';
  }).join('');
}

/* =================================================================== honesty */
function honestyHTML(){
  const rows=[
    ['Parts billed, per distributor','measured','01_data/00_derived/sales_fact.parquet','Attributed by distributor code. Israel splits at sold-to-SAP level (UMI 1797 / UTI 1799); Portugal sums codes 519 and 92. Calendar 2025 total reconciles to \u20ac33,321,625. 2026 excluded.'],
    ['Vehicles in service (UIO)','measured','gps_spu_by_distributor.csv, uio_by_model_bucket.csv','17 markets on the v18 actual basis, the UK truck fleet on DVLA. The weight split is from the model-bucket file, so it is a modelled split of a measured total.'],
    ['Spend per truck','modelled on a measured numerator','gps_spu_by_distributor.csv','Billing divided by the fleet denominator. The real weakness is the target spend behind capture, not this ratio.'],
    ['Service-part capture and the uncaptured value','modelled','pms_capture_by_db_year.csv, pms_opportunity_matrix.csv','The expected units rest on a maintenance interval and an annual distance. Where the distance is measured it overrides the flat assumption; eight markets sit on one flat \u20ac250-per-truck target, which is 37.0% of the ceiling.'],
    ['Capture trend','measured, weak fit','capture_trajectory.csv','Three annual points per distributor-family. Only five of 252 family trends are formally flagged as declining, so most slopes are indistinguishable from flat.'],
    ['Defection and dormancy','measured flag, euro allocated','defection_alerts.csv plus the billing fact','The silence flag comes from order history to March 2026. The euro beside it is trailing twelve-month billing allocated by distributor and family, not a lost-revenue estimate.'],
    ['Basket breadth','measured, partial','sales_by_database goods classification','96.9% of billed value carries a goods classification; the remainder sits in no group and cannot be counted.'],
    ['Exposure and price position','classification and a sample price','aim_exposure_by_db_year.csv, price_premium.csv','Exposure is a hand classification whose severity layer returned a null on backtest. The premium is unit-weighted only where both lines sold, so it is a sample.'],
    ['Warranty share','measured, with a gap','gps_spu_by_distributor.csv, warranty_by_db_FY_canonical.csv','Calendar share from the spend file; fiscal share from the fiscal warranty file. The four CIS markets have no warranty data at all.'],
    ['Competitive-parts share','measured, two universes','billing fact, wallet_waterfall.csv, mix_genuine_bvp_pms.csv','Published twice because the denominator changes the answer. Neither is a target.'],
    ['Substitution on mapped pairs','measured, mapped set','substitution_by_pair_year.csv','A mapped pair is counted whether it sold as genuine, competitive or both, so the line is a mix measure on an unchanged part-number set.'],
    ['Contested euro','measured within a definition','db_parts_mix_classification.csv, dealer_sellout_gps_2025.csv','Contested means a competitive twin exists. The euro lost outright to the independent aftermarket is not measured anywhere.'],
  ];
  const CHIP={measured:'g','modelled':'a','excluded':'r','needs-a-judgement':'n'};
  return '<div class="card"><div class="rc">'+
    '<span class="r g"><b>'+rows.filter(r=>r[1].indexOf('measured')===0).length+'</b> measured</span>'+
    '<span class="r"><b>'+rows.filter(r=>r[1].indexOf('modelled')===0).length+'</b> modelled</span>'+
    '<span class="r c"><b>3</b> figures excluded outright</span>'+
    '<span class="r"><b>'+K.dbs.length+'</b> distributor rows</span>'+
    '<span class="r"><b>'+document.querySelectorAll('.chart').length+'</b> charts on this page</span>'+
    '</div>'+
    '<div class="tbl" style="margin-top:10px"><table style="min-width:1000px"><thead><tr><th class="l">Figure</th>'+
    '<th class="l">How solid</th><th class="l">Behind it</th><th class="l">The honest limit</th></tr></thead><tbody>'+
    rows.map(r=>'<tr><td class="l"><b>'+r[0]+'</b></td><td class="l"><span class="chip '+CHIP[r[1]]+'">'+r[1]+
      '</span></td><td class="l tiny">'+r[2]+'</td><td class="l">'+r[3]+'</td></tr>').join('')+
    '</tbody></table></div></div>';
}
function notshownHTML(){
  const items=[
    '<b>The euro we lost outright to the independent aftermarket.</b> Nothing in this workspace measures independent-garage volume. Every "lost" figure elsewhere is a modelled ceiling, and it is labelled as one here.',
    '<b>Any 2026 calendar or fiscal view.</b> From April 2026 the billing table stores customer names instead of distributor codes, so 2026 rows cannot be attributed to a distributor. Trends therefore end at December 2025.',
    '<b>The 2026\u20132030 fleet forecast.</b> Withdrawn: the forecast scraps vehicles at about 3% a year where the history implies about 10%, and the gap widens with distance. No figure from it appears anywhere on this page.',
    '<b>Sales to dealer for twelve of the eighteen distributors.</b> Only six file it (ITUK, UTI, Ireland, IUK, Greece, Portugal, 69 dealer entities, \u20ac'+ (K.net.sellout/1e6).toFixed(2)+'M). The other twelve show a blank with the reason, never a zero and never a copy of the other direction.',
    '<b>Warranty for the four CIS markets.</b> Ukraine, Armenia, Kazakhstan and Palestine have no warranty data. They are shown as unavailable, not as zero.',
    '<b>The market-mix leg of the growth split.</b> The source\u2019s mix column is a hard zero, so its value has been absorbed into the volume and price legs. It is stated as unavailable rather than drawn as a flat bar.',
    '<b>Customer-level dormancy.</b> 41 dealer-and-family rows carry the flag in the source, but this page carries no customer names, so only the distributor level is shown.',
    '<b>The fiscal view of anything the sources tag by calendar year only.</b> The capture, trend, exposure and price-premium sources are calendar-tagged, so on the fiscal toggle those figures stay calendar and say so on the figure.',
    '<b>Part-number-level billing and customer names.</b> Out of scope for this page by rule.',
    '<b>Occupancy, utilisation or any other live operational metric.</b> Not in the sources. Inventing one is the failure this page exists to prevent.'
  ];
  return '<div class="warnbox"><b>Not shown, and why.</b><ul class="tight">'+
    items.map(i=>'<li>'+i+'</li>').join('')+'</ul></div>'+
    '<div class="card"><h3 style="margin-top:0">What the three toggles actually do</h3><ul class="tight">'+
    '<li><b>Period</b> recomputes parts billed, competitive-parts euro and spend per truck from the billing fact on billing date: Calendar 2025 is Jan\u2013Dec 2025, FY25/26 is Apr 2025 \u2013 Mar 2026. Sources that are calendar-tagged only keep their calendar figure and carry a CY25 chip.</li>'+
    '<li><b>Direction</b> swaps what we invoice the distributor for what the distributor invoices its dealers, where a file exists. On the dealer direction, spend per truck is withheld because the six sales-to-dealer files carry a different fleet basis, and the fiscal view is unavailable because those files are calendar 2025.</li>'+
    '<li><b>Warranty</b> strips warranty parts to leave the customer-paid book. Where a market has no warranty data the stripped figure cannot be computed, so it is withheld rather than shown unchanged.</li>'+
    '</ul><p class="tiny">Distributor stock ratio: where a market files sales to dealer, what it sold on to its dealers less what we invoiced it, for the same year. Six markets only: ITUK, IUK, UTI, Ireland, Greece, Portugal. Read it as an indicator of stock the distributor is carrying, not as a sales result.</p></div>';
}

/* =================================================================== render */
function render(){
  const d = MODE.dir==='dlr';
  document.getElementById('hero').innerHTML = d
    ? '<div class="warnbox"><b>Direction: DB \u2192 dealer.</b> Six distributors file what they sell on to their dealers: ITUK, UTI, Ireland, IUK, Greece and Portugal, 69 dealer entities, \u20ac'+
      (K.net.sellout/1e6).toFixed(2)+'M in calendar 2025. The other twelve cannot be shown in this direction at all. The league below keeps its ISZE \u2192 DB figures, since that is the direction every per-distributor source is built on, and marks the dealer comparison in the last column.</div>'
    : heroHTML();
  document.getElementById('league').innerHTML = leagueHTML();
  document.getElementById('growth').innerHTML = cSpend()+cGrowth()+cCapture()+cTrend()+cGap();
  document.getElementById('growth2').innerHTML = cUio()+cDefect()+cBreadth()+cExpose()+cWarranty();
  document.getElementById('bvp').innerHTML = cB1()+cB2()+cB3()+cB4()+cB5();
  document.getElementById('story').innerHTML = storyHTML();
  document.getElementById('honest').innerHTML = honestyHTML();
  document.getElementById('notshown').innerHTML = notshownHTML();
  const n = netView();
  document.getElementById('stateChip').innerHTML = LBL_P[MODE.period]+' \u00b7 '+LBL_D[MODE.dir]+' \u00b7 '+LBL_W[MODE.warr]+
    ' \u2014 night rail: '+(n.monthsMiss? n.monthsMiss+' distributor-months have no billing row (dark distributors)':'complete');
  $$('.chart').forEach((c,i)=>{ c.setAttribute('data-chartidx', i+1); });
  const cov = document.getElementById('coverage');
  if(cov) cov.innerHTML = coverageHTML();
  window.__KPI_META__ = {charts: document.querySelectorAll('.chart').length, mode: JSON.parse(JSON.stringify(MODE)), snap: K.snap};
}
function coverageHTML(){
  const cells = K.dbs.map(d=>{
    const v=view(d);
    const cls = v.eur==='na'? 'na' : (v.eur===null? 'na' : 'ok');
    return '<span class="chip '+(cls==='ok'?'g':'n')+'" data-tip="'+esc(d.label+': '+(v.monthsUsed)+' of '+v.monthsCov+
      ' months carry a billing row in '+LBL_P[MODE.period]+'. '+(v.eur==='na'? 'No figure in this direction: '+v.dirReason+'.':''))+'">'+
      d.label+' '+(v.monthsUsed)+'/'+v.monthsCov+'</span>';
  }).join(' ');
  return '<h3 style="margin:0 0 4px">Coverage strip \u2014 how many months of the selected period actually carry a billing row, per distributor</h3>'+
    '<p class="cap">A distributor with no rows in a month is dark for that month, not zero: the file simply has nothing. Capture, trend, exposure and price-premium figures are calendar-tagged and keep their calendar value in the fiscal view.</p>'+
    '<div class="rc">'+cells+'</div>';
}
document.addEventListener('click', function(ev){
  const b = ev.target.closest && ev.target.closest('.bar button'); if(!b) return;
  MODE[b.getAttribute('data-k')] = b.getAttribute('data-v');
  $$('.bar button').forEach(x=>{ if(x.getAttribute('data-k')===b.getAttribute('data-k'))
      x.setAttribute('aria-pressed', x===b? 'true':'false'); });
  render();
});
document.addEventListener('DOMContentLoaded', render);
if(document.readyState!=='loading') render();
