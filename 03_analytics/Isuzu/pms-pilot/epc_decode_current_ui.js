// EPC decode driver — matched to the CURRENT UI (2026-09-19).
//
// The older scraper_install.js targets an input.p-dropdown-label control that no longer exists.
// On the live page the part-number search box is an <input> with placeholder
// "FIG, FIGKEY, Part Name or Number", next to a button titled "Perform search", and the results
// header reads "Search Results For: <pn>". This driver uses those.
//
// Exposes:
//   __decodeOne(pn)              -> one part number, returns the family list
//   __decodeBatch([...pns], ms)  -> sequential loop, results accumulate in window.__decodeResults
//   __decodeStatus()             -> progress
//   __decodeDump()               -> rows as JSON text (read it out via CDP)
//
// The loop is deliberately defensive: it never throws, it records a per-PN error rather than
// aborting the run, and it reports honestly when a search did not land.

window.__decodeResults = window.__decodeResults || [];
window.__decodeState = window.__decodeState || { running: false, done: 0, total: 0, errors: 0 };

window.__decodeOne = async function (pn, timeoutMs) {
  timeoutMs = timeoutMs || 12000;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const pnInput =
    document.querySelector('input[placeholder="FIG, FIGKEY, Part Name or Number"]') ||
    Array.from(document.querySelectorAll('input')).find((i) =>
      /FIG, FIGKEY, Part Name or Number/i.test(i.placeholder || '')
    );
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

  const r = btn.getBoundingClientRect();
  const cx = r.left + r.width / 2;
  const cy = r.top + r.height / 2;
  ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach((t) =>
    btn.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, button: 0 }))
  );

  // Wait for the header to name THIS part number.
  const t0 = Date.now();
  let total = null;
  let landed = false;
  while (Date.now() - t0 < timeoutMs) {
    const h = document.querySelector('.part-search-header');
    const ht = h ? h.textContent.trim() : '';
    const m = ht.match(/Search Results For:\s*(\d{4,15})/);
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
    return { pn, error: 'did not land', header: (document.querySelector('.part-search-header') || {}).textContent || null };
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
    window.__decodeState.done = i + 1;
    window.__decodeState.lastPN = pns[i];
    if (i < pns.length - 1) await sleep(ms);
  }
  window.__decodeState.running = false;
  window.__decodeState.elapsedMs = Date.now() - window.__decodeState.started;
  return 'finished ' + pns.length;
};

window.__decodeStatus = function () {
  return JSON.stringify(window.__decodeState);
};

window.__decodeDump = function () {
  return JSON.stringify(window.__decodeResults);
};

'decoder ready';
