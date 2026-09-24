// EQ-Hit lookup for the IE40 price extract — 2026-09-24
// HOW TO USE
//   1. Open https://isuzu.snaponepc.com/epc/#/ and sign in.
//   2. Press F12, click the Console tab.
//   3. If Chrome says "Warning: Don't paste code...", type:  allow pasting
//   4. Paste this whole file, press Enter. It starts by itself.
//   5. It runs about 199 parts. Watch the progress line.
//   6. At the end it downloads  eq_hits_export_epc_only_20260924.json
//      and also leaves the data in this tab under localStorage key "eqhits_epc_only".
//   Nothing is sent anywhere. Close the tab only after it says DONE.

window.__eqh = window.__eqh || {};
window.__eqh.pns = ["7553266960","7552029255","8975480980","7551810370","8976881050","1884053370","7552928440","8982390621","8981028242","8976725370","7552928450","8978410231","8978410221","5873113800","8972785820","8972785810","8976652600","7552710010","5884023600","8982878091","8970430260","8982409962","8982047290","7552062110","8973613450","8975447350","8972370998","8982330473","8975042471","8983700410","8976773021","8978476607","8980026970","8975120512","8974794347","7552598420","8983753331","1884058000","8981751121","8980422840","8980284213","8973627671","7552126065","5872218030","8975007280","8973325980","5872216470","8960175110","8971349242","8983899750","8980678540","7551940990","8975592990","5876102381","8982811761","8982364242","7553196060","8972718850","7552728890","8981067362","8983699834","8976863171","8980456810","8972721030","8976863181","8978591002","8973723590","8975496190","8980337791","8974210030","1096255760","5872213430","8972111170","8979340574","8983569990","8983943812","8983943851","7552956550","47503000","8974102720","8981347680","8171134000","8980672482","8971078690","8979340584","5872213050","8983945981","7552752950","8980477010","8974779000","8974865102","8979340562","8970125392","8980594581","8983724010","1471310390","8980002652","8943226581","1482191490","8974855450","8104571530","8973574490","8973574500","8973586990","8973305271","1474590132","5872211540","5874122510","7552060320","8971868740","8971868730","8971868700","7552389220","1571810036","8979053430","8983160630","8944409030","5876100263","8983419590","1441290391","8970659740","8981897890","8981896570","8975509830","8975509840","8971133250","8980376041","7552360101","8980440600","5872215520","8982873200","5872211910","8980241230","8971849470","8980905130","1097601191","1822900110","8944383051","8104675460","8970831500","8971746380","8973169834","8980626220","7552974010","8944232863","8971677700","7552060300","8943796470","8983525080","8983525060","8983525050","8976744480","1097071570","8980680830","8973305130","7552347140","8975284780","8974107360","8975089350","8980059740","8975412300","8943633640","8942569590","9091800450","8983160520","8973628520","8971848850","8971848860","8972400560","1097012360","8944476980","8983280180","1095890171","8980626630","8943856640","8972142350","1099841410","5097003500","8981171770","1090300730","8981897360","8981897370","8944607420","8982273810","8981512640","9095714060","8943107300","8978263040","8942205910","1099871410","952350320","8982316080","362104120","9096511120","9091645120","811240250","8982273800","8979239200","5872210810"];
window.__eqh.results = window.__eqh.results || [];
window.__eqh.gapMs = 1800;

window.__eqh.lookup = async function (pn) {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const pnInput = () => {
    const byPh = document.querySelector('input[placeholder="Part Number"]');
    if (byPh) return byPh;
    const btn = [...document.querySelectorAll('button')].find(
      (b) => (b.title || '') === 'Perform search'
    );
    if (!btn) return null;
    const grp = btn.closest('.p-toolbar-group-right') || btn.parentElement;
    const texts = [...(grp ? grp.querySelectorAll('input[type="text"]') : [])];
    return texts.find((i) => !/inputMask/.test(i.className || '')) || texts[texts.length - 1] || null;
  };
  const searchBtn = () =>
    [...document.querySelectorAll('button')].find((b) => (b.title || '') === 'Perform search');
  const getTotal = () => {
    let t = null;
    document.querySelectorAll('div.right').forEach((e) => {
      const m = (e.textContent || '').trim().match(/^Total Results:?\s*(\d+)/);
      if (m) t = +m[1];
    });
    return t;
  };

  const inp = pnInput();
  const btn = searchBtn();
  if (!inp || !btn) return { pn, eq_status: 'ERROR', error: 'no controls' };

  const nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  inp.focus();
  nativeSet.call(inp, pn);
  inp.dispatchEvent(new InputEvent('input', { bubbles: true, data: pn, inputType: 'insertText' }));
  inp.dispatchEvent(new Event('change', { bubbles: true }));
  await sleep(90);
  btn.click();

  const t0 = Date.now();
  let total = null, headerOk = false;
  while (Date.now() - t0 < 15000) {
    const h = (document.querySelector('.part-search-header') || {}).textContent || '';
    if (h.includes(pn)) {
      headerOk = true;
      total = getTotal();
      if (total !== null) break;
    }
    await sleep(180);
  }
  if (!headerOk) return { pn, eq_status: 'ERROR', error: 'header timeout' };
  if (total === 0) return { pn, eq_status: 'NOT_FOUND', eq_total: 0, found: false };

  await sleep(320);
  const rows = [...document.querySelectorAll('.ag-row')].filter((rr) =>
    /\d{3,6}\s*-\s*[A-Z0-9]{2,4}/.test(rr.textContent || '')
  );

  const out = {
    pn,
    eq_status: 'FOUND',
    eq_total: total,
    found: true,
    row_count: rows.length,
    eq_catalog: '',
    eq_fig_key: '',
    eq_fig_name: '',
    eq_part_name: '',
  };

  if (rows.length) {
    const cells = [...rows[0].querySelectorAll('.ag-cell')].map((c) => (c.textContent || '').trim());
    out.eq_catalog = cells.join(' | ').slice(0, 300);
    const fk = cells.find((c) => /^\d{3,6}\s*-\s*[A-Z0-9]{2,4}$/.test(c));
    if (fk) out.eq_fig_key = fk.replace(/\s+/g, '');
    rows[0].click();
    await sleep(900);
  }

  for (let i = 0; i < 25; i++) {
    const txt = document.body.innerText || '';
    const m = txt.match(/FIG Name\s*[\r\n]+Part Name\s*[\r\n]+([^\r\n]+)[\r\n]+([^\r\n]+)/);
    if (m && m[1].trim() && !/^FIG Name/i.test(m[1])) {
      out.eq_fig_name = m[1].trim();
      out.eq_part_name = m[2].trim();
      break;
    }
    await sleep(180);
  }
  return out;
};

window.__eqh.run = async function () {
  if (window.__eqh.running) return 'already running';
  window.__eqh.running = true;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const start = window.__eqh.results.length;
  const total = window.__eqh.pns.length;
  for (let i = 0; i < total; i++) {
    if (window.__eqh.cancel) break;
    let hit;
    try {
      hit = await window.__eqh.lookup(window.__eqh.pns[i]);
    } catch (e) {
      hit = { pn: window.__eqh.pns[i], eq_status: 'ERROR', error: String((e && e.message) || e) };
    }
    window.__eqh.results.push(hit);
    try {
      if (window.__eqh.results.length % 25 === 0) {
        localStorage.setItem('eqhits_epc_only', JSON.stringify(window.__eqh.results));
      }
    } catch (e) {}
    const n = window.__eqh.results.length;
    console.log('EQ ' + n + '/' + total + '  ' + hit.pn + '  ' + (hit.eq_status || '') + '  ' + (hit.eq_fig_name || ''));
    if (i < total - 1) await sleep(window.__eqh.gapMs);
  }
  window.__eqh.running = false;
  try {
    localStorage.setItem('eqhits_epc_only', JSON.stringify(window.__eqh.results));
  } catch (e) {}
  const blob = new Blob([JSON.stringify(window.__eqh.results, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'eq_hits_export_epc_only_20260924.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  console.log('DONE  ' + window.__eqh.results.length + ' results downloaded as eq_hits_export_epc_only_20260924.json');
  return window.__eqh.results.length;
};

window.__eqh.cancel = false;
console.log('EQ-Hit ready: ' + window.__eqh.pns.length + ' part numbers. Starting in 3 seconds. To stop it, run:  __eqh.cancel = true');
setTimeout(() => window.__eqh.run(), 3000);
