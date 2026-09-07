// EQ-HIT priority pull — agent-browser robust controls
window.__EQHIT_META = {"8982120690":"clutch_disc","5876100771":"clutch_disc","8982551391":"clutch_disc","8981649171":"clutch_disc","5876100920":"clutch_disc","8978293170":"clutch_disc","8973319320":"brake_shoe","5878320440":"brake_shoe","8982447940":"brake_pad","8982169210":"brake_pad","8982169220":"brake_pad","8982831940":"clutch_pressure_plate","8970388314":"clutch_pressure_plate","5876100910":"clutch_pressure_plate","5876101040":"clutch_pressure_plate","8980400932":"clutch_pressure_plate","8981596930":"fuel_filter","5876150170":"fuel_filter","8981941190":"fuel_filter","8975425400":"fuel_filter","5876101570":"fuel_filter","8980374810":"fuel_filter","1876102860":"fuel_filter","5876150240":"fuel_filter"};
window.__EQHIT_PNS = ["8982120690","5876100771","8982551391","8981649171","5876100920","8978293170","8973319320","5878320440","8982447940","8982169210","8982169220","8982831940","8970388314","5876100910","5876101040","8980400932","8981596930","5876150170","8981941190","8975425400","5876101570","8980374810","1876102860","5876150240"];
window.__allResults = [];

window.__findPnInput = function() {
  const inputs = Array.from(document.querySelectorAll('input'));
  let hit = inputs.find(i => (i.placeholder || '') === 'Part Number');
  if (hit) return hit;
  hit = inputs.find(i => (i.getAttribute('aria-label') || '') === 'Part Number');
  if (hit) return hit;
  hit = inputs.find(i => {
    const r = i.getBoundingClientRect();
    return i.classList.contains('p-dropdown-label') && r.top < 120 && r.width > 80;
  });
  return hit || null;
};

window.__findSearchBtn = function() {
  return Array.from(document.querySelectorAll('button')).find(b => (b.title || '') === 'Perform search') || null;
};

window.__scrapeCurrent = function() {
  const headerEl = document.querySelector('.part-search-header');
  const headerText = headerEl ? headerEl.textContent.trim() : '';
  const hm = headerText.match(/Search Results For:\s*(\d{4,15})/);
  const currentPN = hm ? hm[1] : null;

  let total = null;
  document.querySelectorAll('div.right').forEach(e => {
    const m = (e.textContent || '').trim().match(/^Total Results::?\s*(\d+)$/);
    if (m) total = parseInt(m[1], 10);
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

window.__safeSearchAndScrape = async function(pn) {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const pnInput = window.__findPnInput();
  const btn = window.__findSearchBtn();
  if (!pnInput || !btn) {
    const e = {pn, error: 'no controls', hasInput: !!pnInput, hasBtn: !!btn};
    window.__allResults.push(e);
    return e;
  }

  pnInput.focus();
  const nativeSet = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  nativeSet.call(pnInput, pn);
  pnInput.dispatchEvent(new InputEvent('input', {bubbles: true, data: pn, inputType: 'insertText'}));
  pnInput.dispatchEvent(new Event('change', {bubbles: true}));
  await sleep(120);

  const r = btn.getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(t => {
    btn.dispatchEvent(new MouseEvent(t, {bubbles: true, cancelable: true, view: window, clientX: cx, clientY: cy, button: 0}));
  });

  const tPoll = Date.now();
  let headerMatched = false;
  while (Date.now() - tPoll < 12000) {
    const hEl = document.querySelector('.part-search-header');
    const ht = hEl ? hEl.textContent.trim() : '';
    const hm = ht.match(/Search Results For:\s*(\d{4,15})/);
    if (hm && hm[1] === pn) {
      let total = null;
      document.querySelectorAll('div.right').forEach(e => {
        const m = (e.textContent || '').trim().match(/^Total Results::?\s*(\d+)$/);
        if (m) total = parseInt(m[1], 10);
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

  await sleep(250);
  const rr = await window.__scrapeCurrent();
  window.__allResults.push(rr);
  return {ok: true, pn: rr.pn, total: rr.total, ed: rr.editions, error: rr.error};
};

window.__bgRun = async function(pns, interPNSleepMs) {
  if (!interPNSleepMs) interPNSleepMs = 3500;
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
        new Promise(res => setTimeout(() => res({pn, error: 'race timeout'}), 18000))
      ]);
    } catch (e) {
      r = {pn, error: 'exception: ' + String(e).slice(0,120)};
      window.__allResults.push(r);
    }
    if (r && r.error) window.__bgState.errors++;
    window.__bgState.done = i + 1;
    window.__bgState.lastPN = pn;
    window.__bgState.lastOk = !!(r && r.ok);
    if (i < pns.length - 1) await sleep(interPNSleepMs);
  }
  window.__bgState.running = false;
  window.__bgState.elapsedMs = Date.now() - window.__bgState.started;
  return window.__bgState;
};

'EQHIT_READY:' + window.__EQHIT_PNS.length;
