
// DATA loaded from isze_data.json
let segments = null;
// ══════════════════════════════════════════════════════════
// STATE
// ══════════════════════════════════════════════════════════
let curSeg = 'all', curMkt = 'uk', curLvl = 'all', curAM = 'iam_r';

// ── Channel chain (FACTS.md §7 — apples-to-apples aftermarket comparison) ──
// Gross genuine up to street as MARKUPS: distributor +40%, then dealer +27.5%.
// PR00 × 1.40 × 1.275 = ×1.785. Do NOT use the margin/divisor form (÷0.60 ÷0.725
// = ×2.299) — that is ISZE's own-EUR convention and overstates street by ~29%.
// Single source for both buildTable() and buildKpis(); they previously diverged.
const CH_DB  = 1.40;             // ASC → DB   : distributor +40%
const CH_DLR = 1.275;            // DB  → DLR  : dealer +27.5%

const IAM_TRADE_FACTOR = 0.65;   // DB gets ~35% off IAM retail
const OEM_TRADE_FACTOR = 0.72;   // DB gets ~28% off OEM-equiv retail
const MKT_DE = 0.92, MKT_FR = 1.05;

function getAm(p) {
  const iam_uk = p.am_uk;
  const iam = !iam_uk ? null : curMkt==='uk' ? iam_uk : curMkt==='de' ? p.am_de : p.am_fr;
  const oem_uk = p.oe_uk || (iam_uk ? iam_uk*1.45 : null);
  const oem = !oem_uk ? null : curMkt==='uk' ? oem_uk : curMkt==='de' ? oem_uk*MKT_DE : oem_uk*MKT_FR;
  if (curAM==='iam_r') return iam;
  if (curAM==='iam_t') return iam ? iam*IAM_TRADE_FACTOR : null;
  if (curAM==='oem_r') return oem;
  if (curAM==='oem_t') return oem ? oem*OEM_TRADE_FACTOR : null;
  return iam;
}

function amColLabel() {
  const m = curMkt.toUpperCase();
  if (curAM==='iam_r') return `IAM retail (${m})`;
  if (curAM==='iam_t') return `IAM→DB trade ×0.65 (${m})`;
  if (curAM==='oem_r') return `OEM-equiv retail (${m})`;
  if (curAM==='oem_t') return `OEM-equiv→DB ×0.72 (${m})`;
}

const AM_DESC = {
  iam_r: { expr:'<span class="fv">ISZE price at level</span> ÷ <span class="fd">IAM retail</span>',
    note:'IAM retail = budget AM brands (Nipparts, Borg&amp;Beck, NK) at consumer price (Autodoc/eBay UK). Most conservative view — retail is higher than what workshops actually pay.' },
  iam_t: { expr:'<span class="fv">ISZE price at level</span> ÷ <span class="fd">IAM trade to DB (retail × 0.65)</span>',
    note:'IAM trade = what a DB/distributor pays to their IAM supplier — approx. 35% off retail list. <strong>This shows the real competitive pressure at distributor buying level.</strong>' },
  oem_r: { expr:'<span class="fv">ISZE price at level</span> ÷ <span class="fd">OEM-equiv retail (Bosch / Valeo / LuK / Brembo)</span>',
    note:'OEM-equivalent = premium OE-supplier brands in aftermarket. Same quality tier as ISZE genuine — a fair "like for like" comparison.' },
  oem_t: { expr:'<span class="fv">ISZE price at level</span> ÷ <span class="fd">OEM-equiv DB trade price (retail × 0.72)</span>',
    note:'OEM-equiv trade = what a DB pays directly to Bosch/Valeo/LuK/Brembo — approx. 28% off their retail. <strong>Most relevant for "other OEM selling to DBs" comparison.</strong>' }
};

function updateFormulaBar() {
  const d = AM_DESC[curAM];
  document.getElementById('formula-expr').innerHTML = d.expr;
  document.getElementById('formula-note').innerHTML = d.note;
  const lbls = {iam_r:'Index = Genuine ÷ IAM retail:', iam_t:'Index = Genuine ÷ IAM→DB trade:', oem_r:'Index = Genuine ÷ OEM-equiv retail:', oem_t:'Index = Genuine ÷ OEM-equiv→DB trade:'};
  document.getElementById('legend-label').textContent = lbls[curAM];
}

function idxClass(v) {
  if (v < 1.0) return 'lt1';
  if (v < 1.2) return 'r1';
  if (v < 1.5) return 'r2';
  if (v < 2.0) return 'r3';
  if (v < 3.0) return 'r4';
  if (v < 4.0) return 'r5';
  return 'r6';
}
function f2(v) { return v.toFixed(2); }
function fIdx(v) { return v.toFixed(2)+'×'; }
function confDots(c) {
  if (c==='high')   return '<span class="ch">●●●</span>';
  if (c==='medium') return '<span class="cm">●●○</span>';
  if (c==='low')    return '<span class="cl">●○○</span>';
  return '<span style="color:#bbb">—</span>';
}

// ── Build one table ──
function buildTable(segKey, containerId) {
  const seg = segments[segKey];
  const container = document.getElementById(containerId);
  let lastGrp = null;

  let html = `<table>
    <thead><tr>
      <th style="width:58px">Group</th>
      <th style="min-width:165px">Part category</th>
      <th class="tr" style="width:74px">PR00 (€)</th>
      <th class="tr" style="width:88px">${amColLabel()}</th>
      <th class="tc col-asc" style="width:86px">ASC idx<br><span style="font-size:10px;opacity:.7;font-weight:400">→DB</span></th>
      <th class="tc col-db"  style="width:86px">DB idx<br><span style="font-size:10px;opacity:.7;font-weight:400">→DLR</span></th>
      <th class="tc col-dlr" style="width:86px">DLR idx<br><span style="font-size:10px;opacity:.7;font-weight:400">fleet</span></th>
      <th class="tc" style="width:48px">Conf.</th>
    </tr></thead><tbody>`;

  seg.parts.forEach(p => {
    if (p.grp !== lastGrp) {
      html += `<tr class="div-row"><td colspan="8">${p.grp}</td></tr>`;
      lastGrp = p.grp;
    }

    if (p.na) {
      html += `<tr>
        <td class="grp">${p.grp}</td>
        <td class="pname" title="${p.note.replace(/"/g,"'")}">${p.name}</td>
        <td class="pr00c" colspan="6" style="color:#aaa;font-style:italic;text-align:left;padding-left:12px">— N/A for this segment</td>
      </tr>`;
      return;
    }

    const am  = getAm(p);
    const db  = p.pr00 * CH_DB;
    const dlr = db * CH_DLR;
    const iA  = p.pr00 / am;
    const iD  = db / am;
    const iL  = dlr / am;

    const ascTd = `<td class="ic ${idxClass(iA)} col-asc">${fIdx(iA)}<span class="ps">€${f2(p.pr00)}</span></td>`;
    const dbTd  = `<td class="ic ${idxClass(iD)} col-db">${fIdx(iD)}<span class="ps">€${f2(db)}</span></td>`;
    const dlrTd = `<td class="ic ${idxClass(iL)} col-dlr">${fIdx(iL)}<span class="ps">€${f2(dlr)}</span></td>`;

    const flagBadge = p.flag === 'pr00_corrected' ? ' <span title="Data corrected 30 Mar 2026 — see Assumptions tab" style="font-size:9px;background:#fff3cd;color:#856404;border:1px solid #ffc107;border-radius:3px;padding:1px 4px;vertical-align:middle;cursor:help">CORR</span>'
                   : p.flag === 'simulation_est' ? ' <span title="PR00 from pricing simulation — no confirmed IE40 PN" style="font-size:9px;background:#ffe4cc;color:#7a3800;border:1px solid #ff9f40;border-radius:3px;padding:1px 4px;vertical-align:middle;cursor:help">SIM</span>'
                   : p.flag === 'mid_of_range'   ? ' <span title="PR00 is mid of IE40 range — see Assumptions tab" style="font-size:9px;background:#e8f0fe;color:#1a3a80;border:1px solid #9ab0f5;border-radius:3px;padding:1px 4px;vertical-align:middle;cursor:help">RANGE</span>'
                   : '';
    html += `<tr>
      <td class="grp">${p.grp}</td>
      <td class="pname" title="${p.note.replace(/"/g,"'")}">${p.name}${flagBadge}</td>
      <td class="pr00c">€${f2(p.pr00)}</td>
      <td class="amc">€${f2(am)}</td>
      ${ascTd}${dbTd}${dlrTd}
      <td class="confc">${confDots(p.conf)}</td>
    </tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
  applyLevelClass(container);
}

// ── Apply level visibility ──
function applyLevelClass(el) {
  el.classList.toggle('hide-asc', curLvl !== 'all' && curLvl !== 'asc');
  el.classList.toggle('hide-db',  curLvl !== 'all' && curLvl !== 'db');
  el.classList.toggle('hide-dlr', curLvl !== 'all' && curLvl !== 'dlr');
}

// ── KPI cards ──
function buildKpis() {
  // Collect all index values at DLR level for current market & visible segs
  let allIdxDlr = [];
  let critCount = 0, exposedCount = 0, okCount = 0;

  const segsToShow = curSeg === 'all' ? ['lcv','mcv','hcv'] : [curSeg];
  segsToShow.forEach(sk => {
    segments[sk].parts.forEach(p => {
      if (p.na || !p.pr00) return;
      const am = getAm(p);
      if (!am) return;
      const dlr = p.pr00 * CH_DB * CH_DLR;
      const idx = dlr / am;
      allIdxDlr.push(idx);
      if (idx >= 3.0) critCount++;
      else if (idx >= 1.5) exposedCount++;
      else okCount++;
    });
  });

  const avg = allIdxDlr.length ? (allIdxDlr.reduce((a,b)=>a+b,0)/allIdxDlr.length) : 0;
  const maxIdx = allIdxDlr.length ? Math.max(...allIdxDlr) : 0;

  const bar = document.getElementById('kpi-bar');
  bar.innerHTML = `
    <div class="kpi">
      <div class="kpi-label">Avg DLR index</div>
      <div class="kpi-val ${avg>3?'kpi-red':avg>2?'kpi-amber':'kpi-green'}">${avg.toFixed(2)}×</div>
      <div class="kpi-sub">vs AM retail at fleet level</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Peak DLR index</div>
      <div class="kpi-val kpi-red">${maxIdx.toFixed(2)}×</div>
      <div class="kpi-sub">worst-exposed category</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Critical (&gt;3×)</div>
      <div class="kpi-val kpi-red">${critCount}</div>
      <div class="kpi-sub">categories at DLR level</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Exposed (1.5–3×)</div>
      <div class="kpi-val kpi-amber">${exposedCount}</div>
      <div class="kpi-sub">categories need attention</div>
    </div>
    <div class="kpi">
      <div class="kpi-label">Competitive (&lt;1.5×)</div>
      <div class="kpi-val kpi-green">${okCount}</div>
      <div class="kpi-sub">categories at/near parity</div>
    </div>
  `;
}

// ── Render everything ──
function renderAll() {
  updateFormulaBar();
  ['lcv','mcv','hcv'].forEach(sk => {
    buildTable(sk, 'tbl-'+sk);
    document.getElementById('foot-'+sk).innerHTML = segments[sk].footHtml;
  });
  buildKpis();
  applySegVisibility();
}

function applySegVisibility() {
  ['lcv','mcv','hcv'].forEach(sk => {
    const show = curSeg === 'all' || curSeg === sk;
    document.getElementById('blk-'+sk).classList.toggle('hidden', !show);
    const div = document.getElementById('div-'+sk);
    if (div) div.classList.toggle('hidden', !show);
  });
}

// ── Controls ──
function setSeg(s) {
  curSeg = s;
  ['all','lcv','mcv','hcv'].forEach(id => {
    document.getElementById('seg-'+id).classList.toggle('active', id===s);
  });
  applySegVisibility();
  buildKpis();
}

function setMkt(m) {
  curMkt = m;
  ['uk','de','fr'].forEach(id => {
    document.getElementById('mkt-'+id).classList.toggle('active', id===m);
  });
  renderAll();
}

function setLvl(l) {
  curLvl = l;
  ['all','asc','db','dlr'].forEach(id => {
    document.getElementById('lvl-'+id).classList.toggle('active', id===l);
  });
  ['lcv','mcv','hcv'].forEach(sk => {
    applyLevelClass(document.getElementById('tbl-'+sk));
  });
}

function setAM(a) {
  curAM = a;
  ['iam_r','iam_t','oem_r','oem_t'].forEach(id => {
    document.getElementById('am-'+id).classList.toggle('active', id===a);
  });
  renderAll();
}

// ── Tab switching ──
function switchTab(t) {
  ['heatmap','scraper','assumptions','sources'].forEach(id => {
    const pg = document.getElementById('page-'+id);
    const tb = document.getElementById('tab-'+id);
    if (pg) pg.classList.toggle('tab-visible', id===t);
    if (tb) tb.classList.toggle('tab-active', id===t);
  });
  if (t === 'scraper') { initScraper(); }
}


// ══════════════════════════════════════════════════════════
// SCRAPER DATA
// ══════════════════════════════════════════════════════════
const ksData = [{"pn": "8983767550", "desc": "ROTOR; DISC BRK,FRT", "pr00": 79.26, "rev": 641264.0, "cat": "Brakes", "am_count": 1, "in_stock": 1, "avg_gbp": 35.0, "avg_eur": 41.3, "idx": 1.92, "gen_gbp": 125.0, "gen_eur": 147.5, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8983767550"}, {"pn": "8982447940", "desc": "PAD KIT; CALIPER,DISC BRK,FRT", "pr00": 89.11, "rev": 287818.0, "cat": "Brakes", "am_count": 1, "in_stock": 0, "avg_gbp": 110.0, "avg_eur": 129.8, "idx": 0.69, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982447940"}, {"pn": "8981596930", "desc": "ELEMENT KIT; FUEL FILTER", "pr00": 13.85, "rev": 234253.0, "cat": "Maintenance Service", "am_count": 2, "in_stock": 2, "avg_gbp": 10.0, "avg_eur": 11.8, "idx": 1.17, "gen_gbp": 25.0, "gen_eur": 29.5, "skus": "|", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981596930"}, {"pn": "8982705240", "desc": "ELEMENT; OIL FILTER", "pr00": 6.8, "rev": 215147.0, "cat": "Maintenance Service", "am_count": 1, "in_stock": 1, "avg_gbp": 10.0, "avg_eur": 11.8, "idx": 0.58, "gen_gbp": 15.0, "gen_eur": 17.7, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982705240"}, {"pn": "8983314120", "desc": "SENSOR; PRESSURE,DPD", "pr00": 196.64, "rev": 118471.0, "cat": "Intake Exhaust Emission", "am_count": 1, "in_stock": 1, "avg_gbp": 295.0, "avg_eur": 348.1, "idx": 0.56, "gen_gbp": 275.0, "gen_eur": 324.5, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8983314120"}, {"pn": "8983300950", "desc": "SENSOR; PM", "pr00": 386.83, "rev": 114941.0, "cat": "Intake Exhaust Emission", "am_count": 1, "in_stock": 1, "avg_gbp": 110.0, "avg_eur": 129.8, "idx": 2.98, "gen_gbp": 545.0, "gen_eur": 643.1, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8983300950"}, {"pn": "8975546610", "desc": "PAD KIT; CALIPER,DISC BRK,FRT", "pr00": 82.25, "rev": 105379.0, "cat": "Brakes", "am_count": 1, "in_stock": 1, "avg_gbp": 15.0, "avg_eur": 17.7, "idx": 4.65, "gen_gbp": 125.0, "gen_eur": 147.5, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8975546610"}, {"pn": "8981919560", "desc": "ROTOR; DISC BRK,RR", "pr00": 162.02, "rev": 81574.0, "cat": "Brakes", "am_count": 1, "in_stock": 1, "avg_gbp": 75.0, "avg_eur": 88.5, "idx": 1.83, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981919560"}, {"pn": "8982074350", "desc": "NOZZLE ASM; INJ", "pr00": 195.62, "rev": 74447.0, "cat": "Fuel System", "am_count": 1, "in_stock": 1, "avg_gbp": 350.0, "avg_eur": 413.0, "idx": 0.47, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982074350"}, {"pn": "8981941190", "desc": "ELEMENT KIT; FUEL FILTER", "pr00": 13.27, "rev": 64022.0, "cat": "Maintenance Service", "am_count": 2, "in_stock": 2, "avg_gbp": 7.5, "avg_eur": 8.85, "idx": 1.5, "gen_gbp": null, "gen_eur": null, "skus": "|", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981941190"}, {"pn": "8983712150", "desc": "SENSOR; SPD,RR WHEEL", "pr00": 196.06, "rev": 59241.0, "cat": "Wheels Hub", "am_count": 1, "in_stock": 0, "avg_gbp": 55.0, "avg_eur": 64.9, "idx": 3.02, "gen_gbp": 85.0, "gen_eur": 100.3, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8983712150"}, {"pn": "8973871590", "desc": "ROTOR; SENSOR", "pr00": 51.32, "rev": 49129.0, "cat": "Electrical", "am_count": 1, "in_stock": 1, "avg_gbp": 90.0, "avg_eur": 106.2, "idx": 0.48, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8973871590"}, {"pn": "1476012190", "desc": "CYLINDER; WHEEL,RR BRK", "pr00": 217.83, "rev": 44224.0, "cat": "Wheels Hub", "am_count": 1, "in_stock": 0, "avg_gbp": 260.0, "avg_eur": 306.8, "idx": 0.71, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=1476012190"}, {"pn": "8975074241", "desc": "TURBOCHARGER ASM", "pr00": 840.91, "rev": 41723.0, "cat": "Intake Exhaust Emission", "am_count": 1, "in_stock": 1, "avg_gbp": 975.0, "avg_eur": 1150.5, "idx": 0.73, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8975074241"}, {"pn": "8983621213", "desc": "BAR; FRT BUMPER", "pr00": 55.06, "rev": 39904.0, "cat": "Body Exterior", "am_count": 1, "in_stock": 1, "avg_gbp": 90.0, "avg_eur": 106.2, "idx": 0.52, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8983621213"}, {"pn": "8981472452", "desc": "SHAFT ASM; FRT DRIVE", "pr00": 342.6, "rev": 39636.0, "cat": "Unknown", "am_count": 1, "in_stock": 1, "avg_gbp": 110.0, "avg_eur": 129.8, "idx": 2.64, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981472452"}, {"pn": "8982054020", "desc": "SENSOR; O2", "pr00": 60.04, "rev": 39449.0, "cat": "Unknown", "am_count": 1, "in_stock": 1, "avg_gbp": 85.0, "avg_eur": 100.3, "idx": 0.6, "gen_gbp": 65.0, "gen_eur": 76.7, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982054020"}, {"pn": "8981394280", "desc": "FILTER; BLOWER UNIT", "pr00": 23.02, "rev": 39306.0, "cat": "Cabin Interior", "am_count": 1, "in_stock": 1, "avg_gbp": 4.0, "avg_eur": 4.72, "idx": 4.88, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981394280"}, {"pn": "8983214130", "desc": "FILTER; ACL", "pr00": 30.73, "rev": 39116.0, "cat": "Maintenance Service", "am_count": 1, "in_stock": 1, "avg_gbp": 45.0, "avg_eur": 53.1, "idx": 0.58, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8983214130"}, {"pn": "8980127530", "desc": "SENSOR; SPEED", "pr00": 173.98, "rev": 36758.0, "cat": "Unknown", "am_count": 1, "in_stock": 1, "avg_gbp": 150.0, "avg_eur": 177.0, "idx": 0.98, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8980127530"}, {"pn": "8982079520", "desc": "ROTOR; SENSOR", "pr00": 62.47, "rev": 36027.0, "cat": "Electrical", "am_count": 1, "in_stock": 0, "avg_gbp": 145.0, "avg_eur": 171.1, "idx": 0.37, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982079520"}, {"pn": "8983929650", "desc": "SHAFT ASM; FRT DRIVE", "pr00": 298.3, "rev": 35693.0, "cat": "Unknown", "am_count": 2, "in_stock": 2, "avg_gbp": 145.0, "avg_eur": 171.1, "idx": 1.74, "gen_gbp": 370.0, "gen_eur": 436.6, "skus": "|", "url": "https://www.ks-international.com/catalogsearch/result/?q=8983929650"}, {"pn": "8976739570", "desc": "FILTER; ACL", "pr00": 30.73, "rev": 33489.0, "cat": "Maintenance Service", "am_count": 1, "in_stock": 1, "avg_gbp": 35.0, "avg_eur": 41.3, "idx": 0.74, "gen_gbp": 50.0, "gen_eur": 59.0, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8976739570"}, {"pn": "8981226950", "desc": "PANEL ASM; FRT", "pr00": 247.82, "rev": 32082.0, "cat": "Body Exterior", "am_count": 1, "in_stock": 1, "avg_gbp": 230.0, "avg_eur": 271.4, "idx": 0.91, "gen_gbp": 340.0, "gen_eur": 401.2, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981226950"}, {"pn": "8974056285", "desc": "BUMPER ASM; FRT", "pr00": 175.09, "rev": 31968.0, "cat": "Body Exterior", "am_count": 1, "in_stock": 1, "avg_gbp": 110.0, "avg_eur": 129.8, "idx": 1.35, "gen_gbp": 145.0, "gen_eur": 171.1, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8974056285"}, {"pn": "8981455011", "desc": "OVERHAUL KIT; SUPPLY PUMP", "pr00": 59.11, "rev": 28417.0, "cat": "Transmission", "am_count": 1, "in_stock": 1, "avg_gbp": 135.0, "avg_eur": 159.3, "idx": 0.37, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981455011"}, {"pn": "8974068144", "desc": "BUMPER ASM; FRT", "pr00": 153.2, "rev": 28266.0, "cat": "Body Exterior", "am_count": 1, "in_stock": 1, "avg_gbp": 120.0, "avg_eur": 141.6, "idx": 1.08, "gen_gbp": 195.0, "gen_eur": 230.1, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8974068144"}, {"pn": "8982410681", "desc": "GRILLE; RAD", "pr00": 185.2, "rev": 26376.0, "cat": "Body Exterior", "am_count": 1, "in_stock": 0, "avg_gbp": 275.0, "avg_eur": 324.5, "idx": 0.57, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982410681"}, {"pn": "8981810290", "desc": "FENDER; FRT", "pr00": 96.64, "rev": 25837.0, "cat": "Body Exterior", "am_count": 2, "in_stock": 0, "avg_gbp": 55.0, "avg_eur": 64.9, "idx": 1.49, "gen_gbp": null, "gen_eur": null, "skus": "|", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981810290"}, {"pn": "8970622940", "desc": "FILTER; AIR CLEANER", "pr00": 31.36, "rev": 25126.0, "cat": "Fluids Chemicals", "am_count": 3, "in_stock": 3, "avg_gbp": 38.33, "avg_eur": 45.23, "idx": 0.69, "gen_gbp": 61.67, "gen_eur": 72.77, "skus": "||", "url": "https://www.ks-international.com/catalogsearch/result/?q=8970622940"}, {"pn": "8981226920", "desc": "PANEL ASM; FRT", "pr00": 166.48, "rev": 24915.0, "cat": "Body Exterior", "am_count": 1, "in_stock": 1, "avg_gbp": 175.0, "avg_eur": 206.5, "idx": 0.81, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981226920"}, {"pn": "8980873901", "desc": "SUPPORT; FRT BUMPER", "pr00": 47.62, "rev": 22109.0, "cat": "Body Exterior", "am_count": 1, "in_stock": 1, "avg_gbp": 45.0, "avg_eur": 53.1, "idx": 0.9, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8980873901"}, {"pn": "8982185991", "desc": "LAMP ASM; FOG", "pr00": 76.72, "rev": 21689.0, "cat": "Electrical", "am_count": 1, "in_stock": 1, "avg_gbp": 120.0, "avg_eur": 141.6, "idx": 0.54, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982185991"}, {"pn": "8983852180", "desc": "GENERATOR ASM", "pr00": 327.52, "rev": 20507.0, "cat": "Electrical", "am_count": 1, "in_stock": 1, "avg_gbp": 155.0, "avg_eur": 182.9, "idx": 1.79, "gen_gbp": 395.0, "gen_eur": 466.1, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8983852180"}, {"pn": "8982201270", "desc": "SENSOR; SPEED", "pr00": 233.21, "rev": 20322.0, "cat": "Unknown", "am_count": 1, "in_stock": 1, "avg_gbp": 250.0, "avg_eur": 295.0, "idx": 0.79, "gen_gbp": 325.0, "gen_eur": 383.5, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982201270"}, {"pn": "8982185981", "desc": "LAMP ASM; FOG", "pr00": 76.72, "rev": 19942.0, "cat": "Electrical", "am_count": 1, "in_stock": 0, "avg_gbp": 120.0, "avg_eur": 141.6, "idx": 0.54, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982185981"}, {"pn": "8981402650", "desc": "FILTER; ACL", "pr00": 25.29, "rev": 19485.0, "cat": "Maintenance Service", "am_count": 2, "in_stock": 2, "avg_gbp": 15.0, "avg_eur": 17.7, "idx": 1.43, "gen_gbp": null, "gen_eur": null, "skus": "|", "url": "https://www.ks-international.com/catalogsearch/result/?q=8981402650"}, {"pn": "8982290711", "desc": "GENERATOR ASM", "pr00": 309.96, "rev": 19469.0, "cat": "Electrical", "am_count": 1, "in_stock": 1, "avg_gbp": 125.0, "avg_eur": 147.5, "idx": 2.1, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982290711"}, {"pn": "8982488970", "desc": "ROTOR; DISC BRK,RR", "pr00": 147.21, "rev": 18724.0, "cat": "Brakes", "am_count": 1, "in_stock": 1, "avg_gbp": 175.0, "avg_eur": 206.5, "idx": 0.71, "gen_gbp": null, "gen_eur": null, "skus": "", "url": "https://www.ks-international.com/catalogsearch/result/?q=8982488970"}];
const autoData = [{"pn": "8981596930", "desc": "ELEMENT KIT; FUEL FILTER", "pr00": 13.85, "rev": 234253.0, "cat": "Maintenance Service", "cls": "V", "count": 125, "avg_gbp": 14.92, "avg_eur": 17.61, "min_gbp": 2.0, "idx": 0.79, "brands": "RIDEX, BOSCH, KAVO PARTS, MAXGEAR, QUINTON HAZELL, FEBI BILSTEIN", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981596930"}, {"pn": "8982705240", "desc": "ELEMENT; OIL FILTER", "pr00": 6.8, "rev": 215147.0, "cat": "Maintenance Service", "cls": "V", "count": 24, "avg_gbp": 11.84, "avg_eur": 13.97, "min_gbp": 2.0, "idx": 0.49, "brands": "KAVO PARTS, PURFLUX, MEAT & DORIA, BORG & BECK, FRAM, COOPERSFIAAM FILTERS, VOLLER FILTERS", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982705240"}, {"pn": "8975554500", "desc": "FILTER; BLOWER UNIT", "pr00": 16.33, "rev": 206830.0, "cat": "Cabin Interior", "cls": "D", "count": 2, "avg_gbp": 8.71, "avg_eur": 10.28, "min_gbp": 2.0, "idx": 1.59, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8975554500"}, {"pn": "8978279610", "desc": "PAD KIT; DISC BRK,W/O SHIM & CLIP", "pr00": 68.55, "rev": 128931.0, "cat": "Brakes", "cls": "V", "count": 9, "avg_gbp": 55.61, "avg_eur": 65.62, "min_gbp": 2.0, "idx": 1.04, "brands": "LPR", "url": "https://www.autodoc.co.uk/spares-search?keyword=8978279610"}, {"pn": "8983314120", "desc": "SENSOR; PRESSURE,DPD", "pr00": 196.64, "rev": 118471.0, "cat": "Intake Exhaust Emission", "cls": "C", "count": 12, "avg_gbp": 86.15, "avg_eur": 101.66, "min_gbp": 2.0, "idx": 1.93, "brands": "NRF, FACET, EPS, HJS, HITACHI, MEAT & DORIA, HOFFER, KW, DINEX", "url": "https://www.autodoc.co.uk/spares-search?keyword=8983314120"}, {"pn": "8975546610", "desc": "PAD KIT; CALIPER,DISC BRK,FRT", "pr00": 82.25, "rev": 105379.0, "cat": "Brakes", "cls": "V", "count": 17, "avg_gbp": 72.81, "avg_eur": 85.92, "min_gbp": 2.0, "idx": 0.96, "brands": "REMSA, LPR", "url": "https://www.autodoc.co.uk/spares-search?keyword=8975546610"}, {"pn": "8974993681", "desc": "SENSOR; TIRE INFLATION", "pr00": 23.36, "rev": 102138.0, "cat": "Unknown", "cls": "C", "count": 8, "avg_gbp": 87.79, "avg_eur": 103.59, "min_gbp": 2.0, "idx": 0.23, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8974993681"}, {"pn": "8976526220", "desc": "PAD KIT; CALIPER,DISC BRK,FRT", "pr00": 62.96, "rev": 95740.0, "cat": "Brakes", "cls": "V", "count": 2, "avg_gbp": 77.86, "avg_eur": 91.87, "min_gbp": 2.0, "idx": 0.69, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8976526220"}, {"pn": "5876150170", "desc": "ELEMENT KIT; FUEL FILTER", "pr00": 9.16, "rev": 94589.0, "cat": "Maintenance Service", "cls": "V", "count": 10, "avg_gbp": 11.6, "avg_eur": 13.69, "min_gbp": 2.0, "idx": 0.67, "brands": "BOSCH, FEBI BILSTEIN, DONALDSON, DT Spare Parts, DENCKERMANN, MOTAQUIP, Castrol filters", "url": "https://www.autodoc.co.uk/spares-search?keyword=5876150170"}, {"pn": "8975554002", "desc": "GLASS; WINDSHIELD", "pr00": 168.62, "rev": 90065.0, "cat": "Body Exterior", "cls": "M", "count": 2, "avg_gbp": 504.2, "avg_eur": 594.96, "min_gbp": 2.0, "idx": 0.28, "brands": "GLAVISTA, PILKINGTON", "url": "https://www.autodoc.co.uk/spares-search?keyword=8975554002"}, {"pn": "1876100934", "desc": "ELEMENT; FUEL FILTER", "pr00": 8.16, "rev": 84379.0, "cat": "Maintenance Service", "cls": "V", "count": 2, "avg_gbp": 21.8, "avg_eur": 25.72, "min_gbp": 2.0, "idx": 0.32, "brands": "DONALDSON, DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=1876100934"}, {"pn": "8981919560", "desc": "ROTOR; DISC BRK,RR", "pr00": 162.02, "rev": 81574.0, "cat": "Brakes", "cls": "C", "count": 2, "avg_gbp": 93.39, "avg_eur": 110.2, "min_gbp": 2.0, "idx": 1.47, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981919560"}, {"pn": "8982488951", "desc": "ROTOR; DISC BRK,FRT", "pr00": 158.83, "rev": 76262.0, "cat": "Brakes", "cls": "C", "count": 4, "avg_gbp": 97.99, "avg_eur": 115.63, "min_gbp": 2.0, "idx": 1.37, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982488951"}, {"pn": "8980618131", "desc": "DRUM; BRK,RR", "pr00": 72.49, "rev": 76047.0, "cat": "Brakes", "cls": "C", "count": 19, "avg_gbp": 109.64, "avg_eur": 129.38, "min_gbp": 2.0, "idx": 0.56, "brands": "KAVO PARTS, DELPHI, A.B.S., ABE, FERODO, TRISCAN, BORG & BECK, IAP QUALITY PARTS", "url": "https://www.autodoc.co.uk/spares-search?keyword=8980618131"}, {"pn": "8983313592", "desc": "TURBOCHARGER ASM", "pr00": 800.47, "rev": 73899.0, "cat": "Intake Exhaust Emission", "cls": "C", "count": 9, "avg_gbp": 577.3, "avg_eur": 681.21, "min_gbp": 2.0, "idx": 1.18, "brands": "BTS TURBO, AJUSA, SIDAT, MEAT & DORIA, BR Turbo, Mitsubishi, FEBI BILSTEIN", "url": "https://www.autodoc.co.uk/spares-search?keyword=8983313592"}, {"pn": "8982169210", "desc": "PAD KIT; CALIPER,DISC BRK,FRT", "pr00": 102.65, "rev": 73840.0, "cat": "Brakes", "cls": "V", "count": 12, "avg_gbp": 86.65, "avg_eur": 102.25, "min_gbp": 2.0, "idx": 1.0, "brands": "DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982169210"}, {"pn": "8981647861", "desc": "VALVE; EGR", "pr00": 234.57, "rev": 71790.0, "cat": "Intake Exhaust Emission", "cls": "C", "count": 2, "avg_gbp": 203.1, "avg_eur": 239.66, "min_gbp": 2.0, "idx": 0.98, "brands": "ELSTOCK, DRI", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981647861"}, {"pn": "8975488420", "desc": "FILTER; BLOWER UNIT", "pr00": 16.33, "rev": 71172.0, "cat": "Cabin Interior", "cls": "D", "count": 7, "avg_gbp": 13.71, "avg_eur": 16.18, "min_gbp": 2.0, "idx": 1.01, "brands": "DENCKERMANN, SIDAT", "url": "https://www.autodoc.co.uk/spares-search?keyword=8975488420"}, {"pn": "8981941190", "desc": "ELEMENT KIT; FUEL FILTER", "pr00": 13.27, "rev": 64022.0, "cat": "Maintenance Service", "cls": "V", "count": 102, "avg_gbp": 16.83, "avg_eur": 19.86, "min_gbp": 2.0, "idx": 0.67, "brands": "RIDEX, BOSCH, KAVO PARTS, QUINTON HAZELL, FEBI BILSTEIN", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981941190"}, {"pn": "8978348260", "desc": "SHOE KIT; BRK,RR", "pr00": 41.49, "rev": 63986.0, "cat": "Brakes", "cls": "V", "count": 8, "avg_gbp": 40.12, "avg_eur": 47.34, "min_gbp": 2.0, "idx": 0.88, "brands": "A.B.S., KAVO PARTS, SAMKO, DELPHI, BREMBO, FEBEST, LPR", "url": "https://www.autodoc.co.uk/spares-search?keyword=8978348260"}, {"pn": "8981772710", "desc": "FILTER; ACL", "pr00": 31.36, "rev": 62780.0, "cat": "Maintenance Service", "cls": "V", "count": 18, "avg_gbp": 36.59, "avg_eur": 43.18, "min_gbp": 2.0, "idx": 0.73, "brands": "ASHIKA, KAVO PARTS, JAPKO, FEBI BILSTEIN, BLUE PRINT, HENGST FILTER, FLEETGUARD, DT Spare Parts, DON", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981772710"}, {"pn": "8981776324", "desc": "DPD ASM", "pr00": 1281.85, "rev": 60198.0, "cat": "Intake Exhaust Emission", "cls": "D", "count": 2, "avg_gbp": 553.0, "avg_eur": 652.54, "min_gbp": 2.0, "idx": 1.96, "brands": "KAMOKA, VEGAZ", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981776324"}, {"pn": "8979488071", "desc": "ROTOR; DISC BRK,FRT", "pr00": 90.47, "rev": 59721.0, "cat": "Brakes", "cls": "C", "count": 21, "avg_gbp": 118.3, "avg_eur": 139.59, "min_gbp": 2.0, "idx": 0.65, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8979488071"}, {"pn": "8982318983", "desc": "INJECTOR ASM; DEF DCM", "pr00": 365.34, "rev": 55454.0, "cat": "Fuel System", "cls": "C", "count": 2, "avg_gbp": 114.25, "avg_eur": 134.81, "min_gbp": 1.01, "idx": 2.71, "brands": "FEBI BILSTEIN, BOSCH", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982318983"}, {"pn": "8980139111", "desc": "VALVE; EGR", "pr00": 156.94, "rev": 54977.0, "cat": "Intake Exhaust Emission", "cls": "C", "count": 6, "avg_gbp": 255.75, "avg_eur": 301.78, "min_gbp": 2.0, "idx": 0.52, "brands": "PartsTec, NTY, ISUZU, SANDO, CASCO", "url": "https://www.autodoc.co.uk/spares-search?keyword=8980139111"}, {"pn": "8982831940", "desc": "PLATE ASM; PRESSURE,CLU", "pr00": 71.55, "rev": 50903.0, "cat": "Chassis Frame", "cls": "V", "count": 4, "avg_gbp": 372.12, "avg_eur": 439.1, "min_gbp": 2.0, "idx": 0.16, "brands": "DT Spare Parts, EXEDY, AISIN", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982831940"}, {"pn": "8982169220", "desc": "PAD KIT; CALIPER,DISC BRK,FRT", "pr00": 81.0, "rev": 47630.0, "cat": "Brakes", "cls": "V", "count": 15, "avg_gbp": 87.76, "avg_eur": 103.56, "min_gbp": 2.0, "idx": 0.78, "brands": "DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982169220"}, {"pn": "8980094180", "desc": "SENSOR; MAP", "pr00": 102.51, "rev": 45031.0, "cat": "Unknown", "cls": "C", "count": 4, "avg_gbp": 41.94, "avg_eur": 49.49, "min_gbp": 2.0, "idx": 2.07, "brands": "NTY, HITACHI, MEAT & DORIA, SIDAT", "url": "https://www.autodoc.co.uk/spares-search?keyword=8980094180"}, {"pn": "5876102200", "desc": "ELEMENT KIT;FUEL FILTER", "pr00": 20.29, "rev": 44874.0, "cat": "Maintenance Service", "cls": "V", "count": 3, "avg_gbp": 24.92, "avg_eur": 29.41, "min_gbp": 2.0, "idx": 0.69, "brands": "BOSCH", "url": "https://www.autodoc.co.uk/spares-search?keyword=5876102200"}, {"pn": "8982473951", "desc": "THROTTLE ASM; INT", "pr00": 165.79, "rev": 42382.0, "cat": "Unknown", "cls": "C", "count": 2, "avg_gbp": 248.99, "avg_eur": 293.81, "min_gbp": 2.0, "idx": 0.56, "brands": "HITACHI", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982473951"}, {"pn": "8981472452", "desc": "SHAFT ASM; FRT DRIVE", "pr00": 342.6, "rev": 39636.0, "cat": "Unknown", "cls": "C", "count": 9, "avg_gbp": 117.72, "avg_eur": 138.91, "min_gbp": 0.88, "idx": 2.47, "brands": "RIDEX, NTY, GSP, RIDEX REMAN, BORG & BECK, POINT GEAR, CEVAM", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981472452"}, {"pn": "8982924331", "desc": "SENSOR; SPD,FRT WHEEL", "pr00": 158.26, "rev": 39340.0, "cat": "Wheels Hub", "cls": "C", "count": 4, "avg_gbp": 22.78, "avg_eur": 26.88, "min_gbp": 2.0, "idx": 5.89, "brands": "TRISCAN, BLUE PRINT, FEBI BILSTEIN, SWAG", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982924331"}, {"pn": "8981394280", "desc": "FILTER; BLOWER UNIT", "pr00": 23.02, "rev": 39306.0, "cat": "Cabin Interior", "cls": "D", "count": 178, "avg_gbp": 18.56, "avg_eur": 21.9, "min_gbp": 2.0, "idx": 1.05, "brands": "RIDEX, STARK, RIDEX PLUS, KAVO PARTS, DACO Germany, KAMOKA", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981394280"}, {"pn": "8980058750", "desc": "JOINT ASM; BALL,LWR CONT ARM", "pr00": 34.55, "rev": 39286.0, "cat": "Unknown", "cls": "F", "count": 45, "avg_gbp": 33.23, "avg_eur": 39.21, "min_gbp": 2.0, "idx": 0.88, "brands": "RIDEX, STARK, GSP, ASHIKA, KAVO PARTS, JAPANPARTS, AISIN, SKF, DELPHI, CORTECO, FEBI BILSTEIN, BLUE ", "url": "https://www.autodoc.co.uk/spares-search?keyword=8980058750"}, {"pn": "8983214130", "desc": "FILTER; ACL", "pr00": 30.73, "rev": 39116.0, "cat": "Maintenance Service", "cls": "V", "count": 2, "avg_gbp": 120.53, "avg_eur": 142.23, "min_gbp": 2.0, "idx": 0.22, "brands": "BLUE PRINT, DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=8983214130"}, {"pn": "8983507161", "desc": "FILTER KIT; PUMP ASM,DEF DCM S", "pr00": 70.53, "rev": 37237.0, "cat": "Maintenance Service", "cls": "C", "count": 4, "avg_gbp": 32.45, "avg_eur": 38.29, "min_gbp": 2.0, "idx": 1.84, "brands": "BOSCH, FEBI BILSTEIN, DT Spare Parts, MEAT & DORIA", "url": "https://www.autodoc.co.uk/spares-search?keyword=8983507161"}, {"pn": "8982924321", "desc": "SENSOR; SPD,FRT WHEEL", "pr00": 158.26, "rev": 36137.0, "cat": "Wheels Hub", "cls": "C", "count": 3, "avg_gbp": 22.78, "avg_eur": 26.88, "min_gbp": 2.0, "idx": 5.89, "brands": "TRISCAN, FEBI BILSTEIN, SWAG", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982924321"}, {"pn": "8975425400", "desc": "ELEMENT; FUEL FILTER", "pr00": 12.56, "rev": 36076.0, "cat": "Maintenance Service", "cls": "V", "count": 5, "avg_gbp": 22.66, "avg_eur": 26.74, "min_gbp": 2.0, "idx": 0.47, "brands": "FEBI BILSTEIN, DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=8975425400"}, {"pn": "8983929650", "desc": "SHAFT ASM; FRT DRIVE", "pr00": 298.3, "rev": 35693.0, "cat": "Unknown", "cls": "C", "count": 2, "avg_gbp": 72.4, "avg_eur": 85.43, "min_gbp": 2.0, "idx": 3.49, "brands": "BORG & BECK, GSP", "url": "https://www.autodoc.co.uk/spares-search?keyword=8983929650"}, {"pn": "8982488930", "desc": "ROTOR; DISC BRK,FRT", "pr00": 165.96, "rev": 35683.0, "cat": "Brakes", "cls": "C", "count": 2, "avg_gbp": 79.66, "avg_eur": 94.0, "min_gbp": 2.0, "idx": 1.77, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982488930"}, {"pn": "8975260081", "desc": "TURBOCHARGER ASM", "pr00": 1084.91, "rev": 34772.0, "cat": "Intake Exhaust Emission", "cls": "C", "count": 2, "avg_gbp": 1253.63, "avg_eur": 1479.28, "min_gbp": 2.0, "idx": 0.73, "brands": "BTS TURBO, IHI, BE TURBO", "url": "https://www.autodoc.co.uk/spares-search?keyword=8975260081"}, {"pn": "5876102500", "desc": "ELEMENT; AIR CLEANER", "pr00": 17.49, "rev": 33609.0, "cat": "Fluids Chemicals", "cls": "V", "count": 2, "avg_gbp": 35.1, "avg_eur": 41.42, "min_gbp": 2.0, "idx": 0.42, "brands": "DT Spare Parts, DONALDSON", "url": "https://www.autodoc.co.uk/spares-search?keyword=5876102500"}, {"pn": "8976739570", "desc": "FILTER; ACL", "pr00": 30.73, "rev": 33489.0, "cat": "Maintenance Service", "cls": "V", "count": 2, "avg_gbp": 29.8, "avg_eur": 35.16, "min_gbp": 2.0, "idx": 0.87, "brands": "FEBI BILSTEIN, BLUE PRINT", "url": "https://www.autodoc.co.uk/spares-search?keyword=8976739570"}, {"pn": "5876101570", "desc": "CARTRIDGE KIT; FUEL FILTER", "pr00": 8.76, "rev": 29548.0, "cat": "Maintenance Service", "cls": "V", "count": 8, "avg_gbp": 16.21, "avg_eur": 19.13, "min_gbp": 2.0, "idx": 0.46, "brands": "BOSCH", "url": "https://www.autodoc.co.uk/spares-search?keyword=5876101570"}, {"pn": "8983303281", "desc": "BUMPER ASM; FRT", "pr00": 129.43, "rev": 29337.0, "cat": "Body Exterior", "cls": "P", "count": 2, "avg_gbp": 117.02, "avg_eur": 138.08, "min_gbp": 2.0, "idx": 0.94, "brands": "KLOKKERHOLM, DIEDERICHS", "url": "https://www.autodoc.co.uk/spares-search?keyword=8983303281"}, {"pn": "8982687932", "desc": "GENERATOR ASM", "pr00": 509.83, "rev": 28780.0, "cat": "Electrical", "cls": "F", "count": 6, "avg_gbp": 257.52, "avg_eur": 303.87, "min_gbp": 1.01, "idx": 1.68, "brands": "AS-PL, BV PSH, AUTOELECTRO", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982687932"}, {"pn": "8982120690", "desc": "DISC; CLUTCH", "pr00": 157.24, "rev": 28770.0, "cat": "Brakes", "cls": "V", "count": 12, "avg_gbp": 238.38, "avg_eur": 281.29, "min_gbp": 1.05, "idx": 0.56, "brands": "DT Spare Parts, LuK, ASHIKA, JAPKO, JAPANPARTS, EXEDY, IAP QUALITY PARTS", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982120690"}, {"pn": "8974863550", "desc": "FLYWHEEL", "pr00": 279.49, "rev": 28717.0, "cat": "Wheels Hub", "cls": "C", "count": 2, "avg_gbp": 177.62, "avg_eur": 209.59, "min_gbp": 2.0, "idx": 1.33, "brands": "AUGER, DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=8974863550"}, {"pn": "8978354480", "desc": "SHOE KIT; BRK,RR", "pr00": 36.33, "rev": 28566.0, "cat": "Brakes", "cls": "V", "count": 4, "avg_gbp": 40.11, "avg_eur": 47.33, "min_gbp": 2.0, "idx": 0.77, "brands": "KAVO PARTS, FEBEST, DELPHI", "url": "https://www.autodoc.co.uk/spares-search?keyword=8978354480"}, {"pn": "8983282070", "desc": "ELEMENT; OIL FILTER", "pr00": 14.45, "rev": 25564.0, "cat": "Maintenance Service", "cls": "V", "count": 6, "avg_gbp": 21.77, "avg_eur": 25.69, "min_gbp": 2.0, "idx": 0.56, "brands": "DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=8983282070"}, {"pn": "8970622940", "desc": "FILTER; AIR CLEANER", "pr00": 31.36, "rev": 25126.0, "cat": "Fluids Chemicals", "cls": "V", "count": 20, "avg_gbp": 38.97, "avg_eur": 45.98, "min_gbp": 2.0, "idx": 0.68, "brands": "ASHIKA, KAVO PARTS, JAPKO, FEBI BILSTEIN, BLUE PRINT, HENGST FILTER, FLEETGUARD, DT Spare Parts, DON", "url": "https://www.autodoc.co.uk/spares-search?keyword=8970622940"}, {"pn": "8982330922", "desc": "LAMP ASM; RR COMB", "pr00": 122.91, "rev": 24864.0, "cat": "Body Exterior", "cls": "F", "count": 3, "avg_gbp": 74.14, "avg_eur": 87.49, "min_gbp": 2.0, "idx": 1.4, "brands": "JOHNS, VAN WEZEL", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982330922"}, {"pn": "8982330912", "desc": "LAMP ASM; RR COMB", "pr00": 133.16, "rev": 24300.0, "cat": "Body Exterior", "cls": "F", "count": 3, "avg_gbp": 81.57, "avg_eur": 96.25, "min_gbp": 2.0, "idx": 1.38, "brands": "JOHNS, VAN WEZEL", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982330912"}, {"pn": "8981506872", "desc": "TURBOCHARGER ASM", "pr00": 588.34, "rev": 24117.0, "cat": "Intake Exhaust Emission", "cls": "C", "count": 19, "avg_gbp": 419.97, "avg_eur": 495.56, "min_gbp": 1.02, "idx": 1.19, "brands": "MEAT & DORIA, EVORON, BTS TURBO, IHI, FEBI BILSTEIN, BE TURBO, ISUZU, SANDO, SIDAT, Henkel Parts, MO", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981506872"}, {"pn": "8975260061", "desc": "TURBOCHARGER ASM", "pr00": 1006.09, "rev": 24009.0, "cat": "Intake Exhaust Emission", "cls": "C", "count": 3, "avg_gbp": 1195.55, "avg_eur": 1410.75, "min_gbp": 2.0, "idx": 0.71, "brands": "BTS TURBO, DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=8975260061"}, {"pn": "5876150021", "desc": "FILTER; ACL", "pr00": 12.93, "rev": 23725.0, "cat": "Maintenance Service", "cls": "V", "count": 2, "avg_gbp": 7.59, "avg_eur": 8.96, "min_gbp": 2.0, "idx": 1.44, "brands": "FEBI BILSTEIN, BLUE PRINT", "url": "https://www.autodoc.co.uk/spares-search?keyword=5876150021"}, {"pn": "8976019670", "desc": "SENSOR;  MANIF", "pr00": 118.21, "rev": 23218.0, "cat": "Unknown", "cls": "C", "count": 27, "avg_gbp": 91.85, "avg_eur": 108.38, "min_gbp": 0.94, "idx": 1.09, "brands": "RIDEX, NTY, ESEN SKV, D2P, AUTLOG, DELPHI, MAGNETI MARELLI, FACET, EPS, HITACHI, NGK, STARK, GH, BRE", "url": "https://www.autodoc.co.uk/spares-search?keyword=8976019670"}, {"pn": "8974914013", "desc": "CONDENSER ASM; A/C", "pr00": 153.48, "rev": 23154.0, "cat": "Unknown", "cls": "D", "count": 2, "avg_gbp": 81.5, "avg_eur": 96.17, "min_gbp": 2.0, "idx": 1.6, "brands": "NRF", "url": "https://www.autodoc.co.uk/spares-search?keyword=8974914013"}, {"pn": "8981402660", "desc": "FILTER; ACL", "pr00": 23.13, "rev": 22427.0, "cat": "Maintenance Service", "cls": "V", "count": 25, "avg_gbp": 13.67, "avg_eur": 16.13, "min_gbp": 2.0, "idx": 1.43, "brands": "RIDEX, KAMOKA, ASHIKA, JAPKO, FEBI BILSTEIN, KAVO PARTS, BLUE PRINT, FILTRON, QUINTON HAZELL, MOTAQU", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981402660"}, {"pn": "5876150000", "desc": "ELEMENT; OIL FILTER", "pr00": 4.8, "rev": 22389.0, "cat": "Maintenance Service", "cls": "V", "count": 13, "avg_gbp": 12.29, "avg_eur": 14.5, "min_gbp": 2.0, "idx": 0.33, "brands": "QUINTON HAZELL, KAVO PARTS, MAGNETI MARELLI, HENGST FILTER, MULLER FILTER, NIPPARTS", "url": "https://www.autodoc.co.uk/spares-search?keyword=5876150000"}, {"pn": "5876101170", "desc": "ELEMENT; OIL FILTER", "pr00": 9.96, "rev": 22086.0, "cat": "Maintenance Service", "cls": "V", "count": 14, "avg_gbp": 23.09, "avg_eur": 27.25, "min_gbp": 2.0, "idx": 0.37, "brands": "HENGST FILTER, DT Spare Parts", "url": "https://www.autodoc.co.uk/spares-search?keyword=5876101170"}, {"pn": "8982399830", "desc": "FILTER ASM; FUEL", "pr00": 55.33, "rev": 21055.0, "cat": "Maintenance Service", "cls": "V", "count": 9, "avg_gbp": 12.19, "avg_eur": 14.38, "min_gbp": 2.0, "idx": 3.85, "brands": "BOSCH, MOTAQUIP", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982399830"}, {"pn": "5876150620", "desc": "SHOE KIT; BRK,RR", "pr00": 30.2, "rev": 20657.0, "cat": "Brakes", "cls": "V", "count": 4, "avg_gbp": 37.22, "avg_eur": 43.92, "min_gbp": 2.0, "idx": 0.69, "brands": "SAMKO, BREMBO, LPR, METELLI", "url": "https://www.autodoc.co.uk/spares-search?keyword=5876150620"}, {"pn": "8982383181", "desc": "NOZZLE ASM; INJ", "pr00": 195.62, "rev": 20584.0, "cat": "Fuel System", "cls": "F", "count": 2, "avg_gbp": 1066.4, "avg_eur": 1258.35, "min_gbp": 2.0, "idx": 0.16, "brands": "DT Spare Parts, DENSO", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982383181"}, {"pn": "8983852180", "desc": "GENERATOR ASM", "pr00": 327.52, "rev": 20507.0, "cat": "Electrical", "cls": "F", "count": 4, "avg_gbp": 183.78, "avg_eur": 216.86, "min_gbp": 0.96, "idx": 1.51, "brands": "AS-PL, AUTOELECTRO", "url": "https://www.autodoc.co.uk/spares-search?keyword=8983852180"}, {"pn": "8980565510", "desc": "ROD END ASM; OUTER", "pr00": 42.91, "rev": 20272.0, "cat": "Unknown", "cls": "C", "count": 40, "avg_gbp": 26.79, "avg_eur": 31.61, "min_gbp": 2.0, "idx": 1.36, "brands": "RIDEX, KAMOKA, GSP, Oyodo, JAPANPARTS, JAPKO, QUINTON HAZELL, KAVO PARTS, YAMATO, BGA, DELPHI, SKF, ", "url": "https://www.autodoc.co.uk/spares-search?keyword=8980565510"}, {"pn": "8981402650", "desc": "FILTER; ACL", "pr00": 25.29, "rev": 19485.0, "cat": "Maintenance Service", "cls": "V", "count": 39, "avg_gbp": 21.22, "avg_eur": 25.04, "min_gbp": 2.0, "idx": 1.01, "brands": "RIDEX, KAMOKA, JAPKO, MAXGEAR, KAVO PARTS, QUINTON HAZELL, JAPANPARTS, DENCKERMANN, MOTAQUIP, HENGST", "url": "https://www.autodoc.co.uk/spares-search?keyword=8981402650"}, {"pn": "8982290711", "desc": "GENERATOR ASM", "pr00": 309.96, "rev": 19469.0, "cat": "Electrical", "cls": "F", "count": 25, "avg_gbp": 180.23, "avg_eur": 212.67, "min_gbp": 0.95, "idx": 1.46, "brands": "AS-PL, AUTOELECTRO, BV PSH, HC-Cargo, IAP QUALITY PARTS", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982290711"}, {"pn": "8982488970", "desc": "ROTOR; DISC BRK,RR", "pr00": 147.21, "rev": 18724.0, "cat": "Brakes", "cls": "C", "count": 6, "avg_gbp": 81.99, "avg_eur": 96.75, "min_gbp": 2.0, "idx": 1.52, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8982488970"}, {"pn": "8980374810", "desc": "CARTRIDGE KIT; FUEL FILTER", "pr00": 15.33, "rev": 18281.0, "cat": "Maintenance Service", "cls": "V", "count": 84, "avg_gbp": 22.94, "avg_eur": 27.07, "min_gbp": 2.0, "idx": 0.57, "brands": "RIDEX", "url": "https://www.autodoc.co.uk/spares-search?keyword=8980374810"}, {"pn": "8978279590", "desc": "PAD KIT; DISC BRK,W/O SHIM & CLIP", "pr00": 68.55, "rev": 17841.0, "cat": "Brakes", "cls": "V", "count": 7, "avg_gbp": 62.55, "avg_eur": 73.81, "min_gbp": 2.0, "idx": 0.93, "brands": "", "url": "https://www.autodoc.co.uk/spares-search?keyword=8978279590"}];

let curScrTab = 'ks';
let curKsCat = 'all', curAutoCat = 'all';
let curKsSort = 'rev', curAutoSort = 'rev';
let ksChartObj = null, autoChartObj = null;

function getScrFiltered(data, cat) {
  return cat === 'all' ? data : data.filter(x => x.cat === cat);
}

function getScrSorted(data, sortBy) {
  return [...data].sort((a, b) => sortBy === 'idx' ? b.idx - a.idx : sortBy === 'pr00' ? b.pr00 - a.pr00 : b.rev - a.rev);
}

function idxColor(idx) {
  if (idx < 1.0) return 'rgba(13,122,64,0.85)';
  if (idx < 1.2) return 'rgba(58,172,98,0.85)';
  if (idx < 1.5) return 'rgba(142,204,90,0.85)';
  if (idx < 2.0) return 'rgba(245,208,64,0.85)';
  if (idx < 3.0) return 'rgba(240,122,40,0.85)';
  if (idx < 4.0) return 'rgba(220,56,32,0.85)';
  return 'rgba(154,16,16,0.85)';
}

function idxLabel(idx) {
  if (idx < 1.0) return 'Cheaper than AM';
  if (idx < 1.2) return 'Near parity';
  if (idx < 1.5) return 'Mild premium';
  if (idx < 2.0) return 'Caution';
  if (idx < 3.0) return 'Exposed';
  if (idx < 4.0) return 'High risk';
  return '⚠ Critical';
}

function buildKsChart(parts) {
  const top = parts.slice(0, 20);
  if (ksChartObj) ksChartObj.destroy();
  const ctx = document.getElementById('ks-chart').getContext('2d');
  ksChartObj = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top.map(x => x.desc.length > 32 ? x.desc.slice(0,32)+'…' : x.desc),
      datasets: [
        {
          label: 'Genuine PR00 (€)',
          data: top.map(x => x.pr00),
          backgroundColor: top.map(x => idxColor(x.idx)),
          borderColor: top.map(x => idxColor(x.idx).replace('0.85','1')),
          borderWidth: 1,
          borderRadius: 4
        },
        {
          label: 'KS AM avg (€)',
          data: top.map(x => x.avg_eur),
          backgroundColor: 'rgba(30,100,180,0.55)',
          borderColor: 'rgba(30,100,180,0.85)',
          borderWidth: 1,
          borderRadius: 4
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { font: { size: 11 }, boxWidth: 14 } },
        tooltip: {
          callbacks: {
            title: (items) => top[items[0].dataIndex].desc,
            afterBody: (items) => {
              const p = top[items[0].dataIndex];
              return [
                'PN: ' + p.pn,
                'PR00: €' + p.pr00.toFixed(2),
                'KS AM avg: €' + p.avg_eur.toFixed(2) + ' (£' + p.avg_gbp.toFixed(2) + ')',
                'Index: ' + p.idx.toFixed(2) + '× — ' + idxLabel(p.idx),
                'AM listings: ' + p.am_count + (p.in_stock ? ' ('+p.in_stock+' in stock)' : ' (none in stock)'),
                'SKUs: ' + (p.skus || 'n/a'),
                'CY2025 rev: €' + (p.rev||0).toLocaleString()
              ];
            }
          },
          displayColors: false,
          backgroundColor: '#0d1a30',
          titleColor: '#fff',
          bodyColor: '#c8d8f0',
          padding: 10,
          bodyFont: { size: 11 }
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Price (EUR)', font: { size: 11 } },
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { font: { size: 10 } }
        },
        y: {
          ticks: { font: { size: 10 }, maxRotation: 0 },
          grid: { display: false }
        }
      }
    }
  });
}

function buildAutoChart(parts) {
  const top = parts.slice(0, 20);
  if (autoChartObj) autoChartObj.destroy();
  const ctx = document.getElementById('auto-chart').getContext('2d');
  autoChartObj = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top.map(x => x.desc.length > 32 ? x.desc.slice(0,32)+'…' : x.desc),
      datasets: [
        {
          label: 'Genuine PR00 (€)',
          data: top.map(x => x.pr00),
          backgroundColor: top.map(x => idxColor(x.idx)),
          borderColor: top.map(x => idxColor(x.idx).replace('0.85','1')),
          borderWidth: 1,
          borderRadius: 4
        },
        {
          label: 'Autodoc AM avg (€)',
          data: top.map(x => x.avg_eur),
          backgroundColor: 'rgba(30,100,180,0.55)',
          borderColor: 'rgba(30,100,180,0.85)',
          borderWidth: 1,
          borderRadius: 4
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { font: { size: 11 }, boxWidth: 14 } },
        tooltip: {
          callbacks: {
            title: (items) => top[items[0].dataIndex].desc,
            afterBody: (items) => {
              const p = top[items[0].dataIndex];
              return [
                'PN: ' + p.pn,
                'PR00: €' + p.pr00.toFixed(2),
                'Autodoc AM avg: €' + p.avg_eur.toFixed(2) + ' (£' + p.avg_gbp.toFixed(2) + ')',
                'Index: ' + p.idx.toFixed(2) + '× — ' + idxLabel(p.idx),
                'Listings found: ' + p.count,
                'AM brands: ' + (p.brands || 'n/a'),
                'CY2025 rev: €' + (p.rev||0).toLocaleString()
              ];
            }
          },
          displayColors: false,
          backgroundColor: '#0d1a30',
          titleColor: '#fff',
          bodyColor: '#c8d8f0',
          padding: 10,
          bodyFont: { size: 11 }
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Price (EUR)', font: { size: 11 } },
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { font: { size: 10 } }
        },
        y: {
          ticks: { font: { size: 10 }, maxRotation: 0 },
          grid: { display: false }
        }
      }
    }
  });
}

function buildKsTable(parts) {
  let html = '<table><thead><tr>' +
    '<th>PN</th><th>Description</th><th style="width:60px">Cat</th>' +
    '<th class="tr" style="width:76px">PR00 (€)</th>' +
    '<th class="tr" style="width:76px">KS AM (€)</th>' +
    '<th class="tc" style="width:76px">Index</th>' +
    '<th style="width:60px">Stock</th>' +
    '<th class="tr" style="width:90px">Rev CY25</th>' +
    '</tr></thead><tbody>';
  parts.forEach(p => {
    const ic = idxClass(p.idx);
    const genNote = p.gen_eur ? ' <small style="color:#0a7a40">(Genuine also: £'+p.gen_gbp+')</small>' : '';
    html += '<tr>' +
      '<td style="font-family:monospace;font-size:11px;color:#334">' + p.pn + '</td>' +
      '<td style="font-size:12px">' + p.desc + genNote + '</td>' +
      '<td style="font-size:10px;color:#5a72a0">' + (p.cat||'') + '</td>' +
      '<td class="pr00c">€' + p.pr00.toFixed(2) + '</td>' +
      '<td class="amc">€' + p.avg_eur.toFixed(2) + '<br><small style="color:#888">£'+p.avg_gbp.toFixed(2)+'</small></td>' +
      '<td><div class="ic ' + ic + '" style="font-size:12px">' + p.idx.toFixed(2) + '×<span class="ps">' + idxLabel(p.idx) + '</span></div></td>' +
      '<td style="font-size:11px;text-align:center">' + (p.in_stock > 0 ? '<span style="color:#0a7a40;font-weight:700">✓ '+p.in_stock+'</span>' : '<span style="color:#aaa">—</span>') + '</td>' +
      '<td class="pr00c" style="font-size:11px">€' + (p.rev||0).toLocaleString() + '</td>' +
      '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('ks-table-wrap').innerHTML = html;
}

function buildAutoTable(parts) {
  let html = '<table><thead><tr>' +
    '<th>PN</th><th>Description</th><th style="width:60px">Cat</th>' +
    '<th class="tr" style="width:76px">PR00 (€)</th>' +
    '<th class="tr" style="width:80px">AM avg (€)</th>' +
    '<th class="tc" style="width:76px">Index</th>' +
    '<th>AM Brands</th>' +
    '<th class="tr" style="width:90px">Rev CY25</th>' +
    '</tr></thead><tbody>';
  parts.forEach(p => {
    const ic = idxClass(p.idx);
    html += '<tr>' +
      '<td style="font-family:monospace;font-size:11px;color:#334">' + p.pn + '</td>' +
      '<td style="font-size:12px">' + p.desc + '</td>' +
      '<td style="font-size:10px;color:#5a72a0">' + (p.cat||'') + '</td>' +
      '<td class="pr00c">€' + p.pr00.toFixed(2) + '</td>' +
      '<td class="amc">€' + p.avg_eur.toFixed(2) + '<br><small style="color:#888">£'+p.avg_gbp.toFixed(2)+'</small></td>' +
      '<td><div class="ic ' + ic + '" style="font-size:12px">' + p.idx.toFixed(2) + '×<span class="ps">' + idxLabel(p.idx) + '</span></div></td>' +
      '<td style="font-size:10.5px;color:#555">' + (p.brands||'').slice(0,60) + '</td>' +
      '<td class="pr00c" style="font-size:11px">€' + (p.rev||0).toLocaleString() + '</td>' +
      '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('auto-table-wrap').innerHTML = html;
}

function buildScrKpis(data, source) {
  const above2 = data.filter(x => x.idx > 2).length;
  const above3 = data.filter(x => x.idx > 3).length;
  const competitive = data.filter(x => x.idx <= 1.5).length;
  const avgIdx = data.length ? (data.reduce((a,b) => a+b.idx, 0) / data.length).toFixed(2) : '—';
  const totalRev = data.reduce((a,b) => a+(b.rev||0), 0);
  document.getElementById('scr-kpi-bar').innerHTML =
    '<div class="kpi"><div class="kpi-label">Parts with ' + source + ' data</div><div class="kpi-val kpi-blue">' + data.length + '</div><div class="kpi-sub">parts found in scrape</div></div>' +
    '<div class="kpi"><div class="kpi-label">Avg competitiveness index</div><div class="kpi-val ' + (parseFloat(avgIdx)>2?'kpi-red':parseFloat(avgIdx)>1.5?'kpi-amber':'kpi-green') + '">' + avgIdx + '×</div><div class="kpi-sub">PR00 ÷ AM avg</div></div>' +
    '<div class="kpi"><div class="kpi-label">Exposed (&gt;2×)</div><div class="kpi-val kpi-amber">' + above2 + '</div><div class="kpi-sub">parts at risk</div></div>' +
    '<div class="kpi"><div class="kpi-label">Critical (&gt;3×)</div><div class="kpi-val kpi-red">' + above3 + '</div><div class="kpi-sub">parts — high detachment risk</div></div>' +
    '<div class="kpi"><div class="kpi-label">Competitive (&le;1.5×)</div><div class="kpi-val kpi-green">' + competitive + '</div><div class="kpi-sub">at or near parity</div></div>' +
    '<div class="kpi"><div class="kpi-label">CY2025 Revenue at stake</div><div class="kpi-val kpi-blue">€' + Math.round(totalRev/1000) + 'K</div><div class="kpi-sub">for parts with scraper data</div></div>';
}

function filterKS(cat) {
  curKsCat = cat;
  document.querySelectorAll('.ks-cat-pill').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
  refreshKS();
}
function sortKS(by) { curKsSort = by; refreshKS(); }
function refreshKS() {
  const filtered = getScrFiltered(ksData, curKsCat);
  const sorted = getScrSorted(filtered, curKsSort);
  buildScrKpis(sorted, 'KS');
  buildKsChart(sorted);
  buildKsTable(sorted);
}

function filterAuto(cat) {
  curAutoCat = cat;
  document.querySelectorAll('.auto-cat-pill').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
  refreshAuto();
}
function sortAuto(by) { curAutoSort = by; refreshAuto(); }
function refreshAuto() {
  const filtered = getScrFiltered(autoData, curAutoCat);
  const sorted = getScrSorted(filtered, curAutoSort);
  buildScrKpis(sorted, 'Autodoc');
  buildAutoChart(sorted);
  buildAutoTable(sorted);
}

function setScrTab(tab) {
  curScrTab = tab;
  document.querySelectorAll('.stab').forEach(b => b.classList.toggle('stab-active', b.id === 'stab-'+tab));
  document.getElementById('scr-ks').style.display = tab === 'ks' ? 'block' : 'none';
  document.getElementById('scr-auto').style.display = tab === 'auto' ? 'block' : 'none';
  if (tab === 'ks') refreshKS();
  else refreshAuto();
}

function initScraper() {
  refreshKS();
}

// Init: called after data fetch (see async loader below)

(async function() {
  try {
    const resp = await __localFetch('../Data/dashboards/isze_data.json');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const j = await resp.json();
    segments = j.competitiveness.segments;
    renderAll();
  } catch(e) {
    document.getElementById('isze-offline-banner').style.display = 'block';
  }
})();
