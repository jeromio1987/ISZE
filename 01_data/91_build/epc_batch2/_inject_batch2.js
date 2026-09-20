// Batch-2 decoder, injected into the EPC tab in three parts (A state, B one decode, C loop).
// Same read logic as epc_decode_current_ui.js, with the input located relative to the search
// button because the old placeholder selector no longer matches the Angular search box.

// ── PART A: state and helpers ────────────────────────────────────────────────
window.__BR = [];
window.__slice = function (a, b) { return JSON.stringify(window.__BR.slice(a, b)); };
window.__status = function () {
  return JSON.stringify({ rows: window.__BR.length, errs: window.__BR.filter(function (r) { return r.error; }).length, last: (window.__BR[window.__BR.length - 1] || {}).pn });
};
window.__push = function (pn) { window.__one(pn).catch(function (e) { window.__BR.push({ pn: pn, error: 'exception: ' + String(e).slice(0, 120) }); }); return 'queued'; };
'part A ready';

// ── PART B: one part number ──────────────────────────────────────────────────
window.__one = function (pn, timeoutMs) {
  timeoutMs = timeoutMs || 12000;
  return new Promise(function (resolve) {
    var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
    var out = function (o) { o.pn = pn; window.__BR.push(o); resolve(o); };
    var btn = Array.from(document.querySelectorAll('button')).find(function (b) { return (b.title || '') === 'Perform search'; });
    if (!btn) return out({ error: 'no button' });
    var grp = btn.closest('.p-toolbar-group-right') || btn.parentElement;
    var texts = Array.from(grp.querySelectorAll('input[type=text]'));
    var inp = texts.find(function (i) { return !/inputMask/.test(i.className); }) || texts[texts.length - 1];
    if (!inp) return out({ error: 'no input' });
    var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(inp, pn);
    inp.dispatchEvent(new InputEvent('input', { bubbles: true, data: pn, inputType: 'insertText' }));
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    var t0 = Date.now();
    setTimeout(function () {
      btn.click();
      (function wait() {
        var total = null, landed = false;
        var h = document.querySelector('.part-search-header');
        var ht = h ? h.textContent.trim() : '';
        var m = ht.match(/For:\s*(\d{4,15})/);
        if (m && m[1] === pn) {
          document.querySelectorAll('div.right').forEach(function (e) {
            var t = (e.textContent || '').trim().match(/^Total Results::?\s*(\d+)$/);
            if (t) total = parseInt(t[1]);
          });
          if (total !== null) landed = true;
        }
        if (!landed) {
          if (Date.now() - t0 >= timeoutMs) return out({ error: 'did not land', header: ht });
          return setTimeout(wait, 150);
        }
        if (total === 0) return out({ total: 0, found: false, families: [], editions: 0 });
        try {
          var vps = Array.from(document.querySelectorAll('.ag-body-viewport'))
            .filter(function (v) { return v.getBoundingClientRect().height > 0; })
            .sort(function (a, b) { return a.getBoundingClientRect().left - b.getBoundingClientRect().left; });
          var lv = vps[0];
          if (!lv) return out({ total: total, error: 'no viewport' });
          var seen = {}, fams = {};
          var scan = function () {
            lv.querySelectorAll('.ag-row').forEach(function (row) {
              var text = row.textContent.trim();
              if (/^(TRUCKS|BUSES|PASSENGER VEHICLE|INDUSTRIAL|MARINE|COMPONENT)/.test(text)) { fams[text.split(/\s{2,}/)[0].trim()] = 1; return; }
              var mm = text.match(/^(\d{4,6})\s*-\s*(.+)/);
              if (mm) seen[mm[1]] = mm[2].trim();
            });
          };
          lv.scrollTop = 0;
          setTimeout(function () {
            scan();
            var step = Math.max(250, lv.clientHeight - 50), pos = 0;
            (function next() {
              if (pos > lv.scrollHeight) {
                lv.scrollTop = 0;
                return out({ total: total, found: true, editions: Object.keys(seen).length, families: Object.keys(fams), models: Object.keys(seen).map(function (k) { return seen[k]; }).slice(0, 40) });
              }
              lv.scrollTop = pos; pos += step;
              setTimeout(function () { scan(); next(); }, 45);
            })();
          }, 90);
        } catch (e) { return out({ total: total, error: 'read failed: ' + String(e).slice(0, 120) }); }
      })();
    }, 120);
  });
};
'part B ready';

// ── PART C: sequential loop with a gap, and a completion flag ────────────────
window.__run = function (pns, ms) {
  window.__B2 = { running: true, done: 0, total: pns.length, started: Date.now() };
  (async function () {
    for (var i = 0; i < pns.length; i++) {
      try { await window.__one(pns[i]); } catch (e) { window.__BR.push({ pn: pns[i], error: 'exception: ' + String(e).slice(0, 120) }); }
      window.__B2.done = i + 1;
      if (i < pns.length - 1) await new Promise(function (r) { setTimeout(r, ms); });
    }
    window.__B2.running = false;
    window.__B2.elapsedMs = Date.now() - window.__B2.started;
  })();
  return 'started ' + pns.length;
};
window.__prog = function () { return JSON.stringify(window.__B2 || {}); };
'part C ready';
