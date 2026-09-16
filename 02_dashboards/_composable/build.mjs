#!/usr/bin/env node
/* ISZE composable cockpit — build
 *
 * Eén bron, twee outputs:
 *   node build.mjs                                  -> dist/isze_cockpit.internal.html
 *   node build.mjs --audience=customer              -> dist/isze_cockpit.customer.html
 *   node build.mjs --audience=customer --focus=ITUK -> idem, met ITUK uitgelicht
 *
 * Kernprincipe: bij een customer build worden gevoelige velden UIT DE DATA GESTRIPT,
 * niet client-side verborgen. Wat niet in het bestand zit, kan niet lekken.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ISZE_ROOT = path.resolve(__dirname, "..", "..");
const MODULES_DIR = path.join(__dirname, "modules");
const DIST_DIR = path.join(__dirname, "dist");

const args = Object.fromEntries(
  process.argv.slice(2).map((a) => {
    const [k, v] = a.replace(/^--/, "").split("=");
    return [k, v ?? true];
  })
);
const audience = args.audience === "customer" ? "customer" : "internal";
const focusDistributor = args.focus || null;

/* Serialise a function for inlining into the page.
 * Object shorthand methods (`onEvent(a,b){}`) stringify to something that is NOT a
 * valid expression, so they get promoted to a named function expression. */
function fnSource(fn) {
  const s = fn.toString().trim();
  if (/^(function\b|async\s+function\b|\()/.test(s)) return s; // fn expression or arrow
  if (/^[A-Za-z_$][\w$]*\s*=>/.test(s)) return s; // single-arg arrow
  return "function " + s; // shorthand method
}

/* ---------- shared distributor dimension ----------
 * The single source of truth for "which DB is this row about". Modules never
 * hardcode a mapping; they declare which field holds their raw label and the
 * shell resolves it to a canonical distributor_code. */

const DIM_PATH = path.join(ISZE_ROOT, "01_data/00_derived/distributor_dimension.csv");

function parseCsv(text) {
  const rows = [];
  const lines = text.replace(/^﻿/, "").trim().split(/\r?\n/);
  const cols = splitCsvLine(lines[0]);
  for (const line of lines.slice(1)) {
    if (!line.trim()) continue;
    const v = splitCsvLine(line);
    const o = {};
    cols.forEach((c, i) => (o[c] = v[i] ?? ""));
    rows.push(o);
  }
  return rows;
}
function splitCsvLine(line) {
  const out = [];
  let cur = "", q = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (q) {
      if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; }
      else if (ch === '"') q = false;
      else cur += ch;
    } else if (ch === '"') q = true;
    else if (ch === ",") { out.push(cur); cur = ""; }
    else cur += ch;
  }
  out.push(cur);
  return out;
}

if (!fs.existsSync(DIM_PATH)) {
  console.error(`  ! distributor dimension missing -> ${DIM_PATH}`);
  console.error(`    rebuild it: python 01_data/91_build/build_distributor_dimension.py`);
  process.exit(1);
}
const dimRows = parseCsv(fs.readFileSync(DIM_PATH, "utf8"));

// label (any casing, from either source) -> canonical distributor_code
const dbAlias = {};
for (const r of dimRows) {
  if (!r.distributor_code) continue;
  for (const label of [r.distributor_code, r.gps_db_label]) {
    if (label) dbAlias[label.trim().toUpperCase()] = r.distributor_code;
  }
}

// canonical DB -> attributes (first sold-to wins for scope/region; they agree by construction)
const dbInfo = {};
for (const r of dimRows) {
  const c = r.distributor_code;
  if (!c || dbInfo[c]) continue;
  dbInfo[c] = { code: c, scope: r.scope || "", region: r.region || "", role: r.network_role };
}
const networkDbs = Object.values(dbInfo)
  .filter((d) => d.role === "network_db")
  .map((d) => d.code)
  .sort();

const PEER_DEFS = {
  network: { label: "Network average", test: () => true },
  cv: { label: "CV customers", test: (d) => d.scope === "CV" },
  mixed: { label: "Mixed (CV + LCV)", test: (d) => d.scope === "MIXED" },
  lcv: { label: "LCV customers", test: (d) => d.scope === "LCV" },
  nordics: { label: "Nordics", test: (d) => d.region === "NORDICS" },
  cis: { label: "CIS countries", test: (d) => d.region === "CIS" },
};
const peerGroups = {};
for (const [k, g] of Object.entries(PEER_DEFS)) {
  const members = networkDbs.filter((c) => g.test(dbInfo[c]));
  peerGroups[k] = { label: g.label, members };
  if (!members.length) peerGroups[k].unavailable = "No distributor in this group";
}

console.log(
  `  dimension: ${networkDbs.length} network DBs · groups ` +
    Object.entries(peerGroups).map(([k, g]) => `${k}=${g.members.length}`).join(" ")
);

/* ---------- module laden + data voorbereiden ---------- */

const moduleFiles = fs.readdirSync(MODULES_DIR).filter((f) => f.endsWith(".mjs"));
const built = [];
const sources = [];

for (const file of moduleFiles) {
  const ns = await import(pathToFileURL(path.join(MODULES_DIR, file)).href);
  const mod = ns.default;

  if (!mod.audience.includes(audience)) {
    console.log(`  - ${mod.id}: overgeslagen (niet zichtbaar voor '${audience}')`);
    continue;
  }

  const srcPath = path.join(ISZE_ROOT, mod.source);
  if (!fs.existsSync(srcPath)) {
    console.error(`  ! ${mod.id}: BRON ONTBREEKT -> ${srcPath}`);
    process.exitCode = 1;
    continue;
  }

  let rows = mod.parse(fs.readFileSync(srcPath, "utf8"));

  // Resolve each row to a canonical distributor_code via the shared dimension.
  // `_db` is what every module and the global picker filter on.
  if (mod.dbField) {
    const unresolved = new Set();
    rows = rows.map((r) => {
      const raw = String(r[mod.dbField] ?? "").trim();
      const code = dbAlias[raw.toUpperCase()] || null;
      if (raw && !code) unresolved.add(raw);
      return { ...r, _db: code };
    });
    // Rows outside the distributor network are dropped from network views.
    const before = rows.length;
    rows = rows.filter((r) => r._db && dbInfo[r._db]?.role === "network_db");
    const dropped = before - rows.length;
    if (unresolved.size) {
      console.warn(
        `  ! ${mod.id}: ${unresolved.size} label(s) not in dimension: ${[...unresolved].join(", ")}`
      );
    }
    if (dropped) console.log(`    ${mod.id}: dropped ${dropped} non-network row(s)`);
  }

  // Veld-niveau redactie voor customer builds.
  let stripped = [];
  if (audience === "customer" && mod.internalOnlyFields?.length) {
    stripped = mod.internalOnlyFields;
    rows = rows.map((r) => {
      const clean = { ...r };
      for (const f of stripped) delete clean[f];
      return clean;
    });
  }

  // Kies de renderer per audience. Bestaat er een audience-specifieke renderer,
  // dan wordt ALLEEN die meegecompileerd — de interne functiebron (met daarin de
  // namen van interne velden) belandt dus nooit in een klantbestand.
  const renderer =
    audience === "customer" && mod.clientRenderCustomer
      ? mod.clientRenderCustomer
      : mod.clientRender;

  if (audience === "customer" && mod.internalOnlyFields?.length && !mod.clientRenderCustomer) {
    console.warn(
      `  ! ${mod.id}: heeft internalOnlyFields maar geen clientRenderCustomer — veldnamen kunnen via de renderbron lekken.`
    );
  }

  sources.push(mod.source);
  built.push({
    id: mod.id,
    title: mod.title,
    grain: mod.grain,
    rows,
    renderSrc: fnSource(renderer),
    initialState: mod.initialState ?? null,
    onEventSrc: mod.onEvent ? fnSource(mod.onEvent) : null,
    // resolvePeerGroups may be a named export or sit on the default object.
    peerGroups: (ns.resolvePeerGroups ?? mod.resolvePeerGroups)?.(rows) ?? null,
  });
  console.log(
    `  + ${mod.id}: ${rows.length} rijen${stripped.length ? ` (gestript: ${stripped.join(", ")})` : ""}${
      renderer === mod.clientRenderCustomer ? " [klant-renderer]" : ""
    }`
  );
}

const MODULE_ORDER = ["wallet_identity", "gps_pure_sales", "db_compare", "mix_quality", "warranty_monthly"];
built.sort((a, b) => {
  const ia = MODULE_ORDER.indexOf(a.id);
  const ib = MODULE_ORDER.indexOf(b.id);
  return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
});

/* ---------- client runtime ---------- */

const RUNTIME = String.raw`
const MONTHS_NL = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function ym(p){ const s=String(p); return { y:+s.slice(0,4), m:+s.slice(4,6) }; }
function fyOf(p){ const {y,m}=ym(p); return m>=4 ? y+1 : y; }
function fqOf(p){ const {m}=ym(p); return Math.floor(((m-4+12)%12)/3)+1; }

function findGaps(periods){
  if(!periods.length || String(periods[0]).length!==6) return [];
  const sorted=[...periods].sort();
  const out=[]; let cur=ym(sorted[0]); const end=ym(sorted[sorted.length-1]);
  const have=new Set(sorted.map(String));
  while(cur.y<end.y || (cur.y===end.y && cur.m<=end.m)){
    const key=String(cur.y)+String(cur.m).padStart(2,'0');
    if(!have.has(key)) out.push(MONTHS_NL[cur.m-1]+' '+String(cur.y).slice(2));
    cur.m++; if(cur.m>12){ cur.m=1; cur.y++; }
  }
  return out;
}

function rollup(rows, period, key){
  if(!rows.length) return [];
  if(String(rows[0][key]).length!==6) return rows.map(r=>({...r,label:String(r[key])}));
  const bucket=new Map();
  for(const r of rows){
    const p=r[key]; let id,label;
    if(period==='month'){ const {y,m}=ym(p); id=String(p); label=MONTHS_NL[m-1]+' '+String(y).slice(2); }
    else if(period==='quarter'){ const fy=fyOf(p); id='FY'+fy+'Q'+fqOf(p); label='FY'+String(fy).slice(2)+' Q'+fqOf(p); }
    else if(period==='cy'){ const {y}=ym(p); id='CY'+y; label='CY'+y; }
    else { const fy=fyOf(p); id='FY'+fy; label='FY'+fy; }
    if(!bucket.has(id)) bucket.set(id,{label,_id:id});
    const b=bucket.get(id);
    for(const [k,v] of Object.entries(r)){
      if(k===key||typeof v!=='number') continue;
      b[k]=(b[k]||0)+v;
    }
  }
  return [...bucket.values()].sort((a,b)=>a._id.localeCompare(b._id));
}

// One locale throughout. Mixing nl-BE and en-GB puts "€107.100" next to "8,443"
// in the same table, which reads as two different magnitudes.
const nf=new Intl.NumberFormat('en-GB',{maximumFractionDigits:0});
// pp delta, with -0.0 normalised to 0.0
function pp(d){
  const v=d*100;
  const s=Math.abs(v)<0.05?0:v;
  return (s>0?'+':'')+s.toFixed(1)+' pp';
}
function median(xs){
  const s=[...xs].sort((a,b)=>a-b); if(!s.length) return 0;
  const m=Math.floor(s.length/2);
  return s.length%2 ? s[m] : (s[m-1]+s[m])/2;
}
// Eerlijke melding bij granulariteits-mismatch: liever "niet beschikbaar"
// dan een maand/kwartaal-detail dat de bron niet heeft.
function grainWarning(ctx, sourceGrain){
  if(ctx.period==='year'||ctx.grain===ctx.period) return '';
  const fine=(ctx.period==='month'||ctx.period==='quarter');
  if(ctx.grain==='year'&&fine){
    return '<p class="warn">This source only has <strong>'+sourceGrain+'</strong> granularity. '+
      'The selected period ('+ctx.periodLabel+') cannot be applied — the full year is shown. '+
      'No month/quarter detail is fabricated.</p>';
  }
  return '';
}
const ctxBase={
  usd:v=>'$'+nf.format(Math.round(v)),
  eur:v=>'€'+nf.format(Math.round(v)),
  pct:v=>(v*100).toFixed(1)+'%',
  rollup, findGaps, median, grainWarning, pp,
};

const PERIOD_LABELS={month:'monthly',quarter:'quarterly (fiscal)',fy:'fiscal year',cy:'calendar year'};

/* ---- global distributor selection, shared by every module ---- */
const SEL = { dbs: [], peer: 'network' };

function renderOne(m){
  const period=document.querySelector('#period').value;
  const el=document.querySelector('#mod-'+m.id);
  const C=window.__COCKPIT__;
  const peer=C.peerGroups[SEL.peer];
  const ctx={...ctxBase,period,periodLabel:PERIOD_LABELS[period],grain:m.grain,
    audience:C.meta.audience,
    focusDistributor:C.meta.focus_distributor,
    state:m.state,
    dim:C.dim.info, networkDbs:C.dim.networkDbs,
    peerGroups:C.peerGroups, peer, peerKey:SEL.peer,
    selectedDbs:SEL.dbs,
    inSelection:code=>!SEL.dbs.length||SEL.dbs.includes(code),
    inPeer:code=>peer.members.includes(code)};
  try{ el.innerHTML=m.render(m.rows,ctx); }
  catch(err){ el.innerHTML='<p class="warn">Module failed: '+err.message+'</p>'; }
}
function mount(){ for(const m of window.__COCKPIT__.modules) renderOne(m); }

function renderPicker(){
  const C=window.__COCKPIT__;
  const groups=Object.entries(C.peerGroups).map(([k,g])=>{
    const dis=g.unavailable||!g.members.length;
    return '<button class="gbtn'+(dis?' dis':'')+'" data-pick="group" data-group="'+k+'"'+
      (dis?' disabled':'')+' title="'+(g.unavailable||('Select '+g.members.length+' DB(s)'))+'">'+
      g.label+' <span class="n">'+g.members.length+'</span></button>';
  }).join('');
  const chips=C.dim.networkDbs.map(code=>{
    const d=C.dim.info[code], on=SEL.dbs.includes(code);
    return '<label class="chip'+(on?' on':'')+'"><input type="checkbox" data-pick="db" data-db="'+
      code+'"'+(on?' checked':'')+'>'+code+'<span class="sc">'+(d.scope||d.region||'')+'</span></label>';
  }).join('');
  const peerOpts=Object.entries(C.peerGroups).map(([k,g])=>
    '<option value="'+k+'"'+(k===SEL.peer?' selected':'')+(g.unavailable?' disabled':'')+'>'+
    g.label+(g.unavailable?' (n/a)':'')+'</option>').join('');
  document.querySelector('#picker').innerHTML=
    '<div class="pickbar"><div class="pick-lbl">Quick select</div><div class="gbtns">'+groups+
    '<button class="gbtn clr" data-pick="clear">Clear</button></div></div>'+
    '<div class="chips">'+chips+'</div>'+
    '<div class="pickbar"><div class="pick-lbl">Benchmark against</div>'+
    '<select data-pick="peer">'+peerOpts+'</select>'+
    '<span class="sel-note">'+(SEL.dbs.length?SEL.dbs.length+' selected':'no filter - all DBs shown')+
    '</span></div>';
}

document.addEventListener('DOMContentLoaded',()=>{
  const C=window.__COCKPIT__;
  try{
    const q=new URLSearchParams(location.search);
    const period=q.get('period');
    if(period && document.querySelector('#period option[value="'+period+'"]')){
      document.querySelector('#period').value=period;
    }
    const fy=q.get('fy');
    if(fy){
      const gps=C.modules.find(m=>m.id==='gps_pure_sales');
      if(gps&&gps.state) gps.state.fy=String(fy);
    }
    const year=q.get('year');
    if(year){
      for (const id of ['wallet_identity','mix_quality']){
        const m=C.modules.find(x=>x.id===id);
        if(m&&m.state) m.state.year=String(year);
      }
    }
    const dbs=(q.get('db')||'').split(',').map(s=>s.trim().toUpperCase()).filter(c=>C.dim.networkDbs.includes(c));
    if(dbs.length) SEL.dbs=dbs;
    const peer=q.get('peer');
    if(peer && C.peerGroups[peer] && !C.peerGroups[peer].unavailable) SEL.peer=peer;
    const mod=q.get('module');
    if(mod){
      const sec=document.querySelector('#sec-'+mod);
      if(sec) sec.classList.add('focus-mod');
      document.querySelectorAll('.modnav a').forEach(a=>{
        if(a.getAttribute('href')==='#sec-'+mod) a.classList.add('on');
      });
    }
    const arrive=document.querySelector('#arrive');
    if(arrive && (mod || dbs.length)){
      const names={wallet_identity:'Wallet ceiling',gps_pure_sales:'Spend · GPS euros',db_compare:'Capture · PMS',mix_quality:'Mix · genuine vs BVP',warranty_monthly:'Warranty'};
      const bits=['From map'];
      if(mod) bits.push(names[mod]||mod);
      if(dbs.length) bits.push(dbs.join(', '));
      arrive.hidden=false;
      arrive.innerHTML='<span>'+bits.join(' · ')+'</span>'+(C.meta.audience==='customer'?'':'<a href="prism_map.html">Back to map</a>');
    }
  }catch(e){ console.warn('desk query parse', e); }
  document.querySelector('#period').addEventListener('change',mount);

  const pick=document.querySelector('#picker');
  if(pick){
    pick.addEventListener('click',e=>{
      const t=e.target.closest('[data-pick]'); if(!t) return;
      if(t.dataset.pick==='group'){ SEL.dbs=[...C.peerGroups[t.dataset.group].members]; }
      else if(t.dataset.pick==='clear'){ SEL.dbs=[]; }
      else return;
      renderPicker(); mount();
    });
    pick.addEventListener('change',e=>{
      const t=e.target.closest('[data-pick]'); if(!t) return;
      if(t.dataset.pick==='db'){
        const db=t.dataset.db;
        SEL.dbs=SEL.dbs.includes(db)?SEL.dbs.filter(x=>x!==db):[...SEL.dbs,db];
      } else if(t.dataset.pick==='peer'){ SEL.peer=t.value; }
      else return;
      renderPicker(); mount();
    });
    renderPicker();
  }

  // Module-local controls (period-independent), delegated once per container.
  for(const m of C.modules){
    if(!m.onEvent) continue;
    const el=document.querySelector('#mod-'+m.id);
    for(const evt of ['change','click']){
      el.addEventListener(evt,e=>{ if(m.onEvent(e,m.state)) renderOne(m); });
    }
  }
  mount();
  try{
    const mod=new URLSearchParams(location.search).get('module');
    if(mod){
      const sec=document.querySelector('#sec-'+mod);
      if(sec) setTimeout(function(){ sec.scrollIntoView({behavior:'smooth',block:'start'}); }, 60);
    }
  }catch(e){ console.warn('desk scroll', e); }
});
`;

/* ---------- HTML samenstellen ---------- */

const meta = {
  generated: new Date().toISOString(),
  audience,
  focus_distributor: focusDistributor,
  sources,
  verification_ok: null, // wordt gezet zodra de build tegen _verification_report.json draait
};

const payload = `window.__COCKPIT__ = {
  meta: ${JSON.stringify(meta, null, 2)},
  dim: { info: ${JSON.stringify(dbInfo)}, networkDbs: ${JSON.stringify(networkDbs)} },
  peerGroups: ${JSON.stringify(peerGroups)},
  modules: [
${built
  .map(
    (m) => `    { id: ${JSON.stringify(m.id)}, title: ${JSON.stringify(m.title)}, grain: ${JSON.stringify(m.grain)},
      rows: ${JSON.stringify(m.rows)},
      peerGroups: ${JSON.stringify(m.peerGroups)},
      state: ${JSON.stringify(m.initialState)},
      onEvent: ${m.onEventSrc ?? "null"},
      render: ${m.renderSrc} }`
  )
  .join(",\n")}
  ]
};`;

// Compile-check the generated bundle before writing it. `new Function` parses without
// executing, so a syntax error fails the build instead of silently shipping a blank page.
for (const [name, src] of [["data payload", payload], ["runtime", RUNTIME]]) {
  try {
    new Function(src);
  } catch (err) {
    console.error(`\n  ! BUILD FAILED — syntax error in ${name}: ${err.message}`);
    process.exit(1);
  }
}

const audienceBadge =
  audience === "customer"
    ? `<span class="badge badge-cust">CUSTOMER BUILD — sensitive fields stripped at build time</span>`
    : `<span class="badge badge-int">INTERNAL</span>`;

const NAV_LABEL = {
  wallet_identity: "Wallet",
  gps_pure_sales: "Spend",
  db_compare: "Capture",
  mix_quality: "Mix",
  warranty_monthly: "Warranty",
};

const html = `<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ISZE Master Dashboard — ${audience === "customer" ? "customer" : "internal"}</title>
<style>
  :root{--navy:#15233c;--navy-2:#1c2f4d;--paper:#f7f4ee;--surface:#fff;--ink:#222;
        --text:#5f6b80;--line:#e7e0d4;--terra:#c0552d;--terra-lit:#e0714a;
        --green:#1d9e75;--muted:#9aa5b8;--revenue:var(--terra);--gp:var(--green);}
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);
       font:15px/1.5 "Segoe UI",Helvetica,Arial,sans-serif}
  h1,h2,h3,.kpi-val{font-family:Georgia,"Times New Roman",serif;font-weight:normal}
  header{position:sticky;top:0;z-index:30;min-height:58px;padding:0 22px;
         display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
         background:var(--navy);color:#f7f4ee;border-bottom:none}
  #wordmark{font-family:Georgia,serif;font-size:22px;letter-spacing:.12em;color:#f7f4ee;margin:8px 0}
  #wordmark b{color:var(--terra-lit);font-weight:normal}
  #wordmark small{display:block;font-family:"Segoe UI",sans-serif;font-size:9.5px;
                  letter-spacing:.24em;color:var(--muted);text-transform:uppercase}
  #modes{display:flex;border:1px solid rgba(154,165,184,.28);border-radius:9px;overflow:hidden;flex-shrink:0}
  #modes a{font:600 11.5px "Segoe UI",sans-serif;letter-spacing:.06em;text-transform:uppercase;
           padding:8px 16px;text-decoration:none;color:var(--muted)}
  #modes a.on{background:var(--terra);color:#fff}
  #modes a:not(.on):hover{color:#f7f4ee}
  .badge{font-size:11px;padding:3px 10px;border-radius:999px;font-weight:600;font-family:"Segoe UI",sans-serif}
  .badge-int{background:rgba(224,113,74,.18);color:var(--terra-lit)}
  .badge-cust{background:rgba(29,158,117,.22);color:#7fe0b8}
  .controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  .controls label{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
  header select{padding:6px 10px;border:1px solid rgba(154,165,184,.28);border-radius:8px;
         background:var(--navy-2);color:#f7f4ee;font-size:13px}
  .modnav{display:flex;gap:6px;flex-wrap:wrap;max-width:1320px;margin:0 auto;padding:16px 32px 0}
  .modnav a{font:600 11px "Segoe UI",sans-serif;letter-spacing:.06em;text-transform:uppercase;
            padding:6px 12px;border-radius:8px;text-decoration:none;color:var(--navy);
            border:1px solid var(--line);background:var(--surface)}
  .modnav a:hover,.modnav a.on{border-color:var(--terra);color:var(--terra)}
  #arrive{max-width:1320px;margin:12px auto 0;padding:10px 18px;background:var(--navy);color:#f7f4ee;
          border-radius:10px;display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:13px}
  #arrive[hidden]{display:none !important}
  #arrive a{color:var(--terra-lit)}
  main{max-width:1320px;margin:0 auto;padding:20px 32px 64px}
  section{margin-bottom:44px}
  section h2{font-size:22px;color:var(--navy);border-bottom:1px solid var(--line);
             padding-bottom:8px;margin:0 0 16px}
  .kpi-row{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}
  .kpi{background:var(--surface);border:1px solid var(--line);border-radius:10px;
       padding:12px 16px;min-width:150px;position:relative}
  .kpi[data-tip]{cursor:help}
  .kpi[data-tip]:hover::after{
    content:attr(data-tip);position:absolute;left:0;bottom:calc(100% + 8px);z-index:40;
    width:min(320px,70vw);padding:10px 12px;background:var(--navy);color:#f7f4ee;
    font:12px/1.45 "Segoe UI",sans-serif;border-radius:8px;border-left:3px solid var(--terra);
    white-space:normal;box-shadow:none}
  .kpi-lbl{display:block;font-size:11px;color:var(--text);text-transform:uppercase;
           letter-spacing:.05em;font-family:"Segoe UI",sans-serif}
  .kpi-val{display:block;font-size:22px;margin-top:2px;color:var(--navy)}
  .bars{display:flex;align-items:flex-end;gap:18px;height:196px;
        border-bottom:1px solid var(--line);padding:8px 4px 0;margin-bottom:28px}
  .bar-col{flex:1;min-width:28px;max-width:88px;height:168px;display:flex;flex-direction:column;
           justify-content:flex-end;align-items:stretch;position:relative}
  .bar{width:100%;background:var(--terra);border-radius:3px 3px 0 0;min-height:4px}
  .stack{width:100%;display:flex;flex-direction:column;justify-content:flex-end;min-height:4px}
  .stack>div{width:100%;min-height:0}
  .bar-lbl{position:absolute;top:100%;left:0;right:0;margin-top:6px;font-size:11px;
           color:var(--text);text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .tbl{width:100%;border-collapse:collapse;font-size:13px}
  .tbl th,.tbl td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left}
  .tbl thead th{background:var(--navy);color:#f7f4ee;font-size:11px;text-transform:uppercase;
                letter-spacing:.05em;font-family:"Segoe UI",sans-serif}
  .tbl td.num,.tbl th.num{text-align:right;font-variant-numeric:tabular-nums}
  .tbl tbody tr:nth-child(even) td{background:#fff}
  .tbl tbody tr:nth-child(odd) td{background:var(--paper)}
  .tbl tr.focus td{background:#f4ebe4;font-weight:600}
  .cats{color:var(--text);font-size:12px}
  .warn{background:#f4efe6;border-left:3px solid var(--terra);color:#4a4436;
        padding:10px 14px;border-radius:0 6px 6px 0;font-size:13px;margin:0 0 14px}
  .warn-fail{background:#f8e8e4;border-left:3px solid var(--terra);color:#7F1D1D;
        padding:10px 14px;border-radius:0 6px 6px 0;font-size:13px;margin:0 0 14px}
  .sub{font-size:13px;color:var(--text);margin:0 0 14px;line-height:1.5}
  .flag{display:inline-block;font-size:10px;padding:1px 6px;margin:1px 2px 0 0;
        border:1px solid var(--line);border-radius:999px;color:var(--text);white-space:nowrap}
  .bar.negbar{background:var(--terra);opacity:.55}
  .kpi-sub{display:block;font-size:10.5px;color:var(--text);margin-top:2px;font-family:"Segoe UI",sans-serif}
  .pickbar{display:flex;align-items:center;gap:12px;margin-bottom:10px;flex-wrap:wrap}
  .pick-lbl{font-size:11px;text-transform:uppercase;letter-spacing:.05em;
            color:var(--text);min-width:120px}
  .gbtns{display:flex;gap:6px;flex-wrap:wrap}
  .gbtn{font:500 12px inherit;padding:5px 11px;border:1px solid var(--line);
        border-radius:999px;background:var(--surface);color:var(--ink);cursor:pointer}
  .gbtn:hover:not(.dis){border-color:var(--terra);color:var(--terra)}
  .gbtn .n{color:var(--text);font-size:10.5px;margin-left:3px}
  .gbtn.dis{opacity:.4;cursor:not-allowed}
  .gbtn.clr{border-style:dashed}
  .chips{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:16px}
  .chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;padding:4px 9px;
        border:1px solid var(--line);border-radius:7px;background:var(--surface);cursor:pointer}
  .chip.on{border-color:var(--terra);background:#f4ebe4;font-weight:600}
  .chip input{margin:0;cursor:pointer}
  .chip .sc{font-size:9.5px;color:var(--text);text-transform:uppercase;letter-spacing:.04em}
  .num.pos{color:var(--green)}
  .num.neg{color:var(--terra)}
  .empty{color:var(--text);text-align:center;padding:20px}
  .note{font-size:11.5px;color:var(--text);margin-top:12px;line-height:1.5}
  .picker-sec{background:var(--surface);border:1px solid var(--line);
              border-radius:12px;padding:18px 20px}
  .picker-sec h2{margin-top:0;font-size:18px}
  .sel-note{font-size:11.5px;color:var(--text)}
  .mixleg{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--text);margin:4px 0 12px}
  .mixleg i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:middle}
  .vizroom{margin:0 0 36px}
  .vizgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}
  .vizgrid a{display:block;padding:14px 16px;background:var(--surface);border:1px solid var(--line);
             border-radius:10px;text-decoration:none;color:var(--navy);font:600 14px Georgia,serif}
  .vizgrid a:hover{border-color:var(--terra)}
  .vizgrid a span{display:block;margin-top:4px;font:12px/1.4 "Segoe UI",sans-serif;color:var(--text);font-weight:400}
  footer{max-width:1320px;margin:0 auto;padding:0 32px 48px;color:var(--text);font-size:12px}
  footer a{color:var(--navy)}
  code{font-size:11.5px}
  section.focus-mod h2{color:var(--terra)}
  select{padding:6px 10px;border:1px solid var(--line);border-radius:8px;
         background:var(--surface);color:var(--ink);font-size:13px}
</style>
</head>
<body>
<header>
  <div id="wordmark">PR<b>I</b>SM<small>Parts revenue intelligence · desk${
    audience === "customer" ? " · customer" : ""
  }</small></div>
  <div class="controls">
${
  audience === "customer"
    ? `    ${audienceBadge}`
    : `    <div id="modes"><a href="prism_map.html">Map</a><a class="on" href="#">Desk</a></div>
    ${audienceBadge}`
}
    <label for="period">Period</label>
    <select id="period">
      <option value="month">Month</option>
      <option value="quarter">Quarter (fiscal)</option>
      <option value="fy" selected>Fiscal year</option>
      <option value="cy">Calendar year</option>
    </select>
  </div>
</header>
<nav class="modnav">${built
  .map(
    (m) =>
      `<a href="#sec-${m.id}">${NAV_LABEL[m.id] || m.title}</a>`
  )
  .join("")}</nav>
<div id="arrive" hidden></div>
<main>
${
  audience === "customer"
    ? ""
    : `  <section class="picker-sec"><h2>Distributors</h2><div id="picker"></div></section>
  <section class="vizroom">
    <h2>Meeting screens</h2>
    <p class="sub">These already look like ISZE. The tables below are the shared picker and spine — they are not a replacement for these screens.</p>
    <div class="vizgrid">
      <a href="../../fleet/ISZE_GPS_Dashboard.html">GPS heatmap<span>Traffic lights · different extract — not a signed GPS%</span></a>
      <a href="../../pricing/ISZE_Pricing_Engine_Readiness_Dashboard.html">Pricing engine<span>Hero KPIs · inline SVG · house style</span></a>
      <a href="../../fleet/ISZE_FY2026_YearEnd_Review.html">FY2026 year-end<span>Plotly review pack</span></a>
      <a href="../../sales/AIM_Dashboard_CY2025.html">AIM CY2025<span>Dealer sell-out</span></a>
      <a href="../../sales/ISZE_Competitiveness_Dashboard.html">Competitiveness<span>Network vs aftermarket</span></a>
      <a href="../../fleet/ISUZU_UIO_Dashboard_2026.html">UIO 2026<span>Parc — unsigned as a GPS denominator</span></a>
    </div>
  </section>`
}
${built.map((m) => `  <section id="sec-${m.id}"><h2>${m.title}</h2><div id="mod-${m.id}"></div></section>`).join("\n")}
</main>
<footer>
  <p><strong>Sources:</strong> ${sources.map((s) => `<code>${s}</code>`).join(" · ")}<br>
  Generated ${meta.generated} · audience=<code>${audience}</code>${focusDistributor ? ` · focus=<code>${focusDistributor}</code>` : ""}</p>
  <p>Self-contained file — no server, no fetch. Works by double-click (file://).${
    audience === "customer"
      ? ""
      : ` Map mode: <a href="prism_map.html">PRISM showcase</a>. File index: <a href="../../hub/MASTER_DASHBOARD.html">MASTER_DASHBOARD</a>.`
  }</p>
</footer>
<script>${payload}</script>
<script>${RUNTIME}</script>
</body>
</html>
`;

fs.mkdirSync(DIST_DIR, { recursive: true });
const outName = `isze_cockpit.${audience}.html`;
const outPath = path.join(DIST_DIR, outName);
fs.writeFileSync(outPath, html, "utf8");

const kb = (fs.statSync(outPath).size / 1024).toFixed(1);
console.log(`\n  -> ${outPath} (${kb} KB, ${built.length} modules, audience=${audience})`);

/* ---------- PRISM map (internal product front door) ----------
 * Authoring copy stays at prism/docs/PRISM_SHOWCASE_v2.html.
 * This emit copies it next to the desk and wires Map ↔ Desk. Customer
 * builds never include the map (roadmap / concept nodes are internal). */

function num(x) {
  const n = Number(x);
  return Number.isFinite(n) ? n : 0;
}
function m1(n) {
  return Math.round((n / 1e6) * 10) / 10;
}

function computePrismSnap() {
  const wf = parseCsv(fs.readFileSync(path.join(ISZE_ROOT, "01_data/00_derived/wallet_waterfall.csv"), "utf8"));
  const y25 = wf.filter((r) => String(r.year).replace(/\.0$/, "") === "2025");
  const wallet = y25.reduce((s, r) => s + num(r.theoretical_wallet_eur), 0);
  const captured = y25.reduce((s, r) => s + num(r.captured_total_eur), 0);
  const genuine = y25.reduce((s, r) => s + num(r.captured_genuine_eur), 0);
  const bvp = y25.reduce((s, r) => s + num(r.captured_bvp_eur), 0);
  const gap = y25.reduce((s, r) => s + num(r.addressable_uncaptured_eur), 0);

  const gpsSrc =
    built.find((m) => m.id === "gps_pure_sales")?.source || "01_data/00_derived/gps_pure_sales_2026-08-13.csv";
  const gpsRows = parseCsv(fs.readFileSync(path.join(ISZE_ROOT, gpsSrc), "utf8"));
  let gpsFy2026 = 0;
  let gpsRowsKept = 0;
  for (const r of gpsRows) {
    if (String(r.fy).replace(/\.0$/, "") !== "2026") continue;
    const code = dbAlias[String(r.db || "").trim().toUpperCase()];
    if (!code || dbInfo[code]?.role !== "network_db") continue;
    gpsFy2026 += num(r.pure_sales_eur);
    gpsRowsKept++;
  }
  gpsFy2026 = Math.round(gpsFy2026 * 100) / 100;

  const runPath = path.join(ISZE_ROOT, "01_data/00_derived/revenue_runway.csv");
  const runwayW = [];
  const runwayC = [];
  let wallet2030 = 0;
  let wallet2024 = 0;
  if (fs.existsSync(runPath)) {
    const run = parseCsv(fs.readFileSync(runPath, "utf8"));
    const wBy = {};
    const cBy = {};
    for (const r of run) {
      const y = Number(r.year);
      wBy[y] = (wBy[y] || 0) + num(r.wallet_eur);
      cBy[y] = (cBy[y] || 0) + num(r.projected_capture_eur);
    }
    for (const y of [2024, 2025, 2026, 2027, 2028, 2029, 2030]) {
      runwayW.push(m1(wBy[y] || 0));
      runwayC.push(m1(cBy[y] || 0));
    }
    wallet2030 = wBy[2030] || 0;
    wallet2024 = wBy[2024] || 0;
  }

  const vs24 =
    wallet2024 > 0 ? "+" + Math.round(((wallet2030 - wallet2024) / wallet2024) * 100) + "% vs 2024" : "";

  return {
    as_of: new Date().toISOString().slice(0, 10),
    n_markets: networkDbs.length,
    wallet,
    captured,
    genuine,
    bvp,
    gap,
    capture_pct: wallet ? ((captured / wallet) * 100).toFixed(0) : "—",
    gps_fy2026: gpsFy2026,
    gps_fy2026_rows: gpsRowsKept,
    gps_source: gpsSrc,
    wallet_2030: wallet2030,
    wallet_2030_vs_2024: vs24,
    runwayW,
    runwayC,
    sources: [
      "01_data/00_derived/wallet_waterfall.csv",
      gpsSrc,
      "01_data/00_derived/revenue_runway.csv",
      "01_data/00_derived/distributor_dimension.csv",
    ],
  };
}

function prismMapGlue(snap) {
  const snapJson = JSON.stringify(snap);
  return `<style>
#modes{display:flex;border:1px solid var(--card-line);border-radius:9px;overflow:hidden;flex-shrink:0;}
#modes span,#modes a{font:600 11.5px "Segoe UI",sans-serif;letter-spacing:.06em;text-transform:uppercase;padding:8px 14px;text-decoration:none;color:var(--muted);}
#modes .on{background:var(--terra);color:#fff;}
#modes a:hover{color:var(--terra-lit);}
#ddesk{display:block;width:100%;margin-top:10px;border:1px solid var(--terra-lit);background:transparent;color:var(--terra-lit);text-decoration:none;text-align:center;font:600 12px "Segoe UI",sans-serif;letter-spacing:.03em;padding:10px 14px;border-radius:9px;}
#ddesk:hover{filter:brightness(1.08);}
#ddesk .g{opacity:.85;font-weight:400;}
#ddesk[hidden]{display:none !important;}
.desktag{display:inline-block;margin-top:8px;margin-left:6px;font:700 8.5px "Segoe UI",sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#4fd0a4;border:1px solid rgba(29,158,117,.45);border-radius:6px;padding:2px 7px;}
</style>
<script>
window.__PRISM_SNAP__=${snapJson};
window.__DESK_HREF__="isze_cockpit.internal.html";
(function(){
  var NODE_DESK={
    c_spend:{module:"gps_pure_sales",period:"fy"},
    der_gps:{module:"gps_pure_sales",period:"fy"},
    suf_fleet:{module:"gps_pure_sales",period:"fy"},
    suf_home:{module:"wallet_identity",year:"2025"},
    c_wallet:{module:"wallet_identity",year:"2025"},
    c_dec:{module:"wallet_identity",year:"2025"},
    der_dec:{module:"wallet_identity",year:"2025"},
    suf_dec:{module:"wallet_identity",year:"2025"},
    src_tgt:{module:"wallet_identity",year:"2025"},
    eng_fact:{module:"gps_pure_sales",period:"fy"},
    c_cap:{module:"db_compare"},
    der_cap:{module:"db_compare"},
    suf_cap:{module:"db_compare"},
    c_mix:{module:"mix_quality",year:"2025"},
    der_mix:{module:"mix_quality",year:"2025"},
    eng_pms:{module:"db_compare"},
    suf_ituk:{module:"db_compare",db:"ITUK"}
  };
  function mEur(n){ return "€"+(Number(n)/1e6).toFixed(1)+"M"; }
  function deskHref(spec){
    spec=spec||{};
    var q=[];
    if(spec.module) q.push("module="+encodeURIComponent(spec.module));
    if(spec.db) q.push("db="+encodeURIComponent(spec.db));
    if(spec.period) q.push("period="+encodeURIComponent(spec.period));
    if(spec.fy) q.push("fy="+encodeURIComponent(spec.fy));
    if(spec.year) q.push("year="+encodeURIComponent(spec.year));
    return window.__DESK_HREF__+(q.length?"?"+q.join("&"):"");
  }
  function liveChip(ch){
    var S=window.__PRISM_SNAP__; if(!S) return ch;
    var l=ch[1]||"";
    if(/wallet ceiling · CY2025/.test(l)) return [mEur(S.wallet), l];
    if(/^captured · CY2025$/.test(l)) return [mEur(S.captured), l];
    if(/^distributor markets$/.test(l)) return [String(S.n_markets), l];
    if(/of ceiling captured/.test(l)) return [S.capture_pct+"%", l];
    if(/genuine captured/.test(l)) return [mEur(S.genuine), l];
    if(/Best Value captured/.test(l)) return [mEur(S.bvp), l];
    if(/addressable gap · CY2025/.test(l)) return [mEur(S.gap), l];
    if(/ceiling by 2030/.test(l)) return [mEur(S.wallet_2030), (S.wallet_2030_vs_2024?"ceiling by 2030 · "+S.wallet_2030_vs_2024:l)];
    return ch;
  }
  var modes=document.createElement("div");
  modes.id="modes";
  modes.innerHTML='<span class="on">Map</span><a id="deskbtn" href="'+deskHref({})+'">Desk</a>';
  var spacer=document.getElementById("spacer");
  if(spacer&&spacer.parentNode) spacer.parentNode.insertBefore(modes, spacer.nextSibling);
  var ddesk=document.createElement("a");
  ddesk.id="ddesk"; ddesk.hidden=true;
  var drawerEl=document.getElementById("drawer");
  if(drawerEl) drawerEl.appendChild(ddesk);
  if(typeof openDrawer==="function"){
    var _open=openDrawer;
    openDrawer=function(n,el){
      _open(n,el);
      var spec=NODE_DESK[n.id];
      if(!spec || n.st==="concept"){ ddesk.hidden=true; ddesk.removeAttribute("href"); return; }
      var label=spec.db ? ("Open desk · "+spec.db) : (spec.module==="gps_pure_sales" ? "Open desk · Spend" : spec.module==="db_compare" ? "Open desk · Capture" : spec.module==="wallet_identity" ? "Open desk · Wallet" : spec.module==="mix_quality" ? "Open desk · Mix" : "Open desk");
      ddesk.hidden=false;
      ddesk.href=deskHref(spec);
      ddesk.innerHTML=label+' <span class="g">· same spine</span>';
    };
  }
  if(typeof setChapter==="function"){
    var _ch=setChapter;
    setChapter=function(i){
      _ch(i);
      var S=window.__PRISM_SNAP__; if(!S||!CHAPTERS) return;
      setTimeout(function(){
        var c=CHAPTERS[state.ch];
        var chips=c.chips.map(liveChip);
        if(state.ch===0 && S.gps_fy2026!=null) chips.push([mEur(S.gps_fy2026),"GPS-eligible parts · FY2026"]);
        document.getElementById("chips").innerHTML=chips.map(function(ch){
          return '<div class="chip"><div class="v">'+ch[0]+'</div><div class="l">'+ch[1]+'</div></div>';
        }).join("");
      }, 240);
    };
  }
  if(typeof runwayW!=="undefined" && window.__PRISM_SNAP__.runwayW && window.__PRISM_SNAP__.runwayW.length){
    runwayW=window.__PRISM_SNAP__.runwayW;
    runwayC=window.__PRISM_SNAP__.runwayC;
  }
  Object.keys(nodeEls||{}).forEach(function(id){
    if(!NODE_DESK[id]) return;
    var rec=nodeEls[id];
    if(rec.n.st==="concept") return;
    if(rec.el.querySelector(".desktag")) return;
    var tag=document.createElement("span");
    tag.className="desktag"; tag.textContent="Desk";
    rec.el.appendChild(tag);
  });
  var foot=document.querySelector("#foot span");
  if(foot && window.__PRISM_SNAP__){
    var S=window.__PRISM_SNAP__;
    foot.textContent="Snapshot "+S.as_of+" · wallet_waterfall CY2025 · "+S.gps_source.split("/").pop()+" FY2026 (network DBs only) · ceiling, not a forecast · Map + Desk share distributor_dimension.csv";
  }
  if(typeof setChapter==="function") setChapter(state.ch||0);
})();
</script>`;
}

function emitPrismMap(snap) {
  const src = path.join(ISZE_ROOT, "03_analytics/Isuzu/prism/docs/PRISM_SHOWCASE_v2.html");
  if (!fs.existsSync(src)) {
    console.warn("  ! PRISM showcase missing — map not emitted:", src);
    return;
  }
  let mapHtml = fs.readFileSync(src, "utf8");
  if (!mapHtml.includes("</body>")) {
    console.warn("  ! PRISM showcase has no </body> — map not emitted");
    return;
  }
  mapHtml = mapHtml.replace("</body>", prismMapGlue(snap) + "\n</body>");
  const mapPath = path.join(DIST_DIR, "prism_map.html");
  fs.writeFileSync(mapPath, mapHtml, "utf8");
  const mkb = (fs.statSync(mapPath).size / 1024).toFixed(1);
  console.log(
    `  -> ${mapPath} (${mkb} KB)  wallet CY2025 ${m1(snap.wallet)}M · captured ${m1(snap.captured)}M · GPS FY2026 ${m1(snap.gps_fy2026)}M · ${snap.n_markets} DBs`
  );
}

emitPrismMap(computePrismSnap());

