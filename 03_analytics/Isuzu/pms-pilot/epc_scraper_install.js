// EPC scraper — paste this into the Chrome console at https://isuzu.snaponepc.com/epc/#/
// after logging in to resume the 222-PN background loop in a future session.
// Then call: window.__bgRun(remainingPNs, 12000) where remainingPNs is the array of PNs left to query.

window.__allResults = window.__allResults || [];

window.__scrapeCurrent = function() {
  const headerEl = document.querySelector('.part-search-header');
  const headerText = headerEl ? headerEl.textContent.trim() : '';
  const hm = headerText.match(/Search Results For:\s*(\d{4,15})/);
  const currentPN = hm ? hm[1] : null;

  let total = null;
  document.querySelectorAll('div.right').forEach(e => {
    const m = (e.textContent || '').trim().match(/^Total Results::?\s*(\d+)$/);
    if (m) total = parseInt(m[1]);
  });

  if (total === 0) return Promise.resolve({pn: currentPN, total: 0, found: false, editions: 0, byFamily: {}});
  if (total === null) return Promise.resolve({pn: currentPN, total: null, found: false, editions: 0, byFamily: {}, partial: 'no_total'});

  const viewports = Array.from(document.querySelectorAll('.ag-body-viewport')).filter(v => {
    const rr = v.getBoundingClientRect();
    return rr.height > 0;
  }).sort((a,b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
  const lv = viewports[0];
  if (!lv) return Promise.resolve({pn: currentPN, total, error: 'no viewport'});

  return new Promise(async (resolve) => {
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    const collected = new Map();
    let currentFamily = '';
    const scan = () => {
      lv.querySelectorAll('.ag-row').forEach(rr => {
        const text = rr.textContent.trim();
        if (/^(TRUCKS|BUSES|PASSENGER VEHICLE|INDUSTRIAL|MARINE|COMPONENT)/.test(text)) {
          currentFamily = text;
        } else {
          const m = text.match(/^(\d{4,6})\s*-\s*(.+)/);
          if (m) collected.set(m[1], {family: currentFamily, text: m[2].trim()});
        }
      });
    };
    lv.scrollTop = 0;
    await sleep(80);
    scan();
    const maxScroll = lv.scrollHeight;
    const step = Math.max(250, lv.clientHeight - 50);
    for (let pos = 0; pos < maxScroll + step; pos += step) {
      lv.scrollTop = pos;
      await sleep(45);
      scan();
    }
    lv.scrollTop = 0;
    const byFamily = {};
    for (const [id, info] of collected) {
      const f = info.family || 'UNKNOWN';
      if (!byFamily[f]) byFamily[f] = [];
      byFamily[f].push({id, text: info.text});
    }
    resolve({
      pn: currentPN, total, found: true, editions: collected.size,
      avgPositions: collected.size ? +(total / collected.size).toFixed(2) : null,
      families: Object.keys(byFamily), byFamily
    });
  });
};

window.__safeScrapeCurrent = window.__scrapeCurrent;  // alias for compatibility

window.__safeSearchAndScrape = async function(pn) {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const pnInput = Array.from(document.querySelectorAll('input.p-dropdown-label')).find(i => {
    const r = i.getBoundingClientRect();
    return r.top < 100 && r.left > 1300;
  });
  const btn = Array.from(document.querySelectorAll('button')).find(b => (b.title || '') === 'Perform search');
  if (!pnInput || !btn) { const e = {pn, error: 'no controls'}; window.__allResults.push(e); return e; }

  pnInput.focus();
  const nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  nativeSet.call(pnInput, pn);
  pnInput.dispatchEvent(new InputEvent('input', {bubbles: true, data: pn, inputType: 'insertText'}));
  pnInput.dispatchEvent(new Event('change', {bubbles: true}));
  await sleep(100);

  const r = btn.getBoundingClientRect();
  const cx = r.left + r.width/2, cy = r.top + r.height/2;
  ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(t => {
    btn.dispatchEvent(new MouseEvent(t, {bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, button: 0}));
  });

  const tPoll = Date.now();
  let headerMatched = false;
  while (Date.now() - tPoll < 10000) {
    const hEl = document.querySelector('.part-search-header');
    const ht = hEl ? hEl.textContent.trim() : '';
    const hm = ht.match(/Search Results For:\s*(\d{4,15})/);
    if (hm && hm[1] === pn) {
      let total = null;
      document.querySelectorAll('div.right').forEach(e => {
        const m = (e.textContent || '').trim().match(/^Total Results::?\s*(\d+)$/);
        if (m) total = parseInt(m[1]);
      });
      if (total !== null) { headerMatched = true; break; }
    }
    await sleep(200);
  }

  if (!headerMatched) {
    const errResult = {pn, error: 'poll timeout', got: document.querySelector('.part-search-header')?.textContent?.trim()};
    window.__allResults.push(errResult);
    return errResult;
  }

  await sleep(200);
  const rr = await window.__scrapeCurrent();
  window.__allResults.push(rr);
  return {ok: true, pn: rr.pn, total: rr.total, ed: rr.editions};
};

window.__bgRun = async function(pns, interPNSleepMs) {
  if (!interPNSleepMs) interPNSleepMs = 12000;
  if (window.__bgState && window.__bgState.running) return 'already running';
  window.__bgState = {total: pns.length, done: 0, errors: 0, running: true, started: Date.now(), interSleep: interPNSleepMs};
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < pns.length; i++) {
    if (window.__bgState.cancelRequested) break;
    const pn = pns[i];
    let r;
    try {
      r = await Promise.race([
        window.__safeSearchAndScrape(pn),
        new Promise(res => setTimeout(() => res({pn, error: 'race timeout'}), 15000))
      ]);
    } catch (e) { r = {pn, error: 'exception: ' + String(e).slice(0,120)}; window.__allResults.push(r); }
    if (r && r.error) window.__bgState.errors++;
    window.__bgState.done = i + 1;
    window.__bgState.lastPN = pn;
    if (i < pns.length - 1) await sleep(interPNSleepMs);
  }
  window.__bgState.running = false;
  window.__bgState.elapsedMs = Date.now() - window.__bgState.started;
};

// Helper: download results as JSON file
window.__downloadResults = function(filename) {
  filename = filename || 'epc_results_partial.json';
  const blob = new Blob([JSON.stringify(window.__allResults, null, 1)], {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
  return 'downloaded ' + filename;
};

console.log('EPC scraper installed. Use window.__bgRun([...pns], 12000) to start.');
