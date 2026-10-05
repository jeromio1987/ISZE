// EPC decode driver for batch 2 — same read logic as epc_decode_current_ui.js (2026-09-19), with
// one change: every result is POSTed to the local collector the moment it is read, so a reload
// cannot cost the run. The collector appends to a JSONL on disk on each post.
//
// Differences from epc_decode_current_ui.js, both deliberate:
//   1. the part-number input is located RELATIVE TO THE SEARCH BUTTON (the button's right-hand
//      toolbar group, the text input that is not the VIN mask), because the input no longer has
//      the placeholder "FIG, FIGKEY, Part Name or Number" the old driver selects on;
//   2. results are flushed to http://127.0.0.1:8791/append as they land.
//
// Result shape is unchanged, so batch 2 parses with the same code as batch 1:
//   { pn, total, found, editions, families, models }
// plus a nullable `error` when a search did not land.
window.__SINK = 'http://127.0.0.1:8791';
window.__decodeResults = window.__decodeResults || [];
window.__decodeState = window.__decodeState || { running: false, done: 0, total: 0, errors: 0 };

window.__flush = function (rec) {
  try {
    fetch(window.__SINK + '/append', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pn: rec.pn, result: rec }),
      keepalive: true,
    }).catch(function () {});
  } catch (e) { /* the in-page array is still the fallback */ }
};

window.__pnInput = function () {
  var btn = Array.from(document.querySelectorAll('button')).find(function (b) {
    return (b.title || '') === 'Perform search';
  });
  if (!btn) return null;
  var group = btn.closest('.p-toolbar-group-right') || btn.parentElement;
  if (!group) return null;
  var texts = Array.from(group.querySelectorAll('input[type="text"]'));
  return texts.find(function (i) { return !/inputMask/.test(i.className); }) ||
         texts[texts.length - 1] || null;
};

window.__decodeOne = async function (pn, timeoutMs) {
  timeoutMs = timeoutMs || 12000;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const pnInput = window.__pnInput();
  const btn = Array.from(document.querySelectorAll('button')).find(
    (b) => (b.title || '') === 'Perform search'
  );
  if (!pnInput || !btn) return { pn, error: 'no controls' };

  pnInput.focus();
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(pnInput, pn);
  pnInput.dispatchEvent(new InputEvent('input', { bubbles: true, data: pn, inputType: 'insertText' }));
  pnInput.dispatchEvent(new Event('change', { bubbles: true }));
  await sleep(120);

  btn.click();

  // Wait for the header to name THIS part number.
  const t0 = Date.now();
  let total = null;
  let landed = false;
  while (Date.now() - t0 < timeoutMs) {
    const h = document.querySelector('.part-search-header');
    const ht = h ? h.textContent.trim() : '';
    const m = ht.match(/For:\s*(\d{4,15})/);
    if (m && m[1] === pn) {
      document.querySelectorAll('div.right').forEach((e) => {
        const t = (e.textContent || '').trim().match(/^Total Results::?\s*(\d+)$/);
        if (t) total = parseInt(t[1]);
      });
      if (total !== null) { landed = true; break; }
    }
    await sleep(150);
  }
  if (!landed) {
    return { pn, error: 'did not land',
             header: (document.querySelector('.part-search-header') || {}).textContent || null };
  }
  if (total === 0) return { pn, total: 0, found: false, families: [], editions: 0 };

  // Read every row of the first result grid.
  const vps = Array.from(document.querySelectorAll('.ag-body-viewport'))
    .filter((v) => v.getBoundingClientRect().height > 0)
    .sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
  const lv = vps[0];
  if (!lv) return { pn, total, error: 'no viewport' };

  const seen = new Map();
  const families = new Set();
  const scan = () => {
    lv.querySelectorAll('.ag-row').forEach((row) => {
      const text = row.textContent.trim();
      if (/^(TRUCKS|BUSES|PASSENGER VEHICLE|INDUSTRIAL|MARINE|COMPONENT)/.test(text)) {
        families.add(text.split(/\s{2,}/)[0].trim());
        return;
      }
      const m = text.match(/^(\d{4,6})\s*-\s*(.+)/);
      if (m) seen.set(m[1], m[2].trim());
    });
  };
  lv.scrollTop = 0;
  await sleep(90);
  scan();
  const step = Math.max(250, lv.clientHeight - 50);
  for (let pos = 0; pos < lv.scrollHeight + step; pos += step) {
    lv.scrollTop = pos;
    await sleep(45);
    scan();
  }
  lv.scrollTop = 0;

  return {
    pn,
    total,
    found: true,
    editions: seen.size,
    families: Array.from(families),
    models: Array.from(seen.values()).slice(0, 40),
  };
};

window.__decodeBatch = async function (pns, ms) {
  ms = ms || 6000;
  if (window.__decodeState.running) return 'already running';
  window.__decodeState = { running: true, done: 0, total: pns.length, errors: 0, started: Date.now() };
  const sleep = (t) => new Promise((r) => setTimeout(r, t));
  for (let i = 0; i < pns.length; i++) {
    let res;
    try {
      res = await window.__decodeOne(pns[i]);
    } catch (e) {
      res = { pn: pns[i], error: 'exception: ' + String(e).slice(0, 120) };
    }
    if (res && res.error) window.__decodeState.errors++;
    window.__decodeResults.push(res);
    window.__flush(res);
    window.__decodeState.done = i + 1;
    window.__decodeState.lastPN = pns[i];
    if (i < pns.length - 1) await sleep(ms);
  }
  window.__decodeState.running = false;
  window.__decodeState.elapsedMs = Date.now() - window.__decodeState.started;
  try {
    fetch(window.__SINK + '/finalize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meta: window.__decodeState }),
    }).catch(function () {});
  } catch (e) { /* ignore */ }
  return 'finished ' + pns.length;
};

window.__decodeStatus = function () {
  return JSON.stringify(window.__decodeState);
};

window.__decodeDump = function () {
  return JSON.stringify(window.__decodeResults);
};

'batch2 driver ready';
