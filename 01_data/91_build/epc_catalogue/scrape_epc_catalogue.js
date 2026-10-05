// EPC catalogue bulk scraper -- in-page controller (ISZE, 2026-09-19)
//
// WHY THIS SHAPE
// The EPC service endpoints (/epc-services/datasets/...) reject any request that does not
// carry a per-request signed header (SBSEQHITEPCCS) that only the running app can produce.
// Verified 2026-09-19: /datasets, /navigations/..., /pages/parts/... all return
// 401 NOT AUTHORIZED without it, and a captured token replayed 60s later also 401s.
// So the page must make every call. This controller drives the app's own navigation and
// reads the JSON the app itself fetches.
//
// READ-ONLY. It only clicks navigation nodes and reads XHR responses. It never touches
// picklists, estimates, quicklists, exports or settings.
//
// BULK SHAPE (measured 2026-09-19)
//   TRUCKS > {family}          -> ONE call returns every edition under that family
//                                 (N = 556 editions in a single 212,577-byte payload)
//   edition                    -> ONE call returns the 10 systems
//   system                     -> ONE call returns that system's subsections
//   subsection (= one FIG page)-> ONE call returns every part row:
//                                 {pageId, imageId, partItems:[{partNumber, calloutLabel,
//                                  description, quantity, position, remarks, ...}], ...}
//
// So the unit of work is one FIG page, and each FIG page is one request. There is no
// endpoint that returns parts for a whole edition in one shot.

(function () {
  if (window.__cat && window.__cat.installed) return 'already installed';

  var S = {
    installed: true,
    running: false,
    phase: 'idle',
    started: null,
    editions: [],      // editions queued
    edIndex: 0,
    log: [],
    errors: [],
    rows: [],          // {part_number, figkey, part_name, ...}
    stats: { editions: 0, figs: 0, rows: 0, emptyFigs: 0 },
    lastError: null,
  };
  window.__cat = S;

  // ---- response capture -------------------------------------------------------
  if (!window.__catCapture) {
    window.__catCapture = { ring: [] };
    var oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (m, u) { this.__u = String(u); return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function () {
      var x = this;
      x.addEventListener('load', function () {
        try {
          var t = x.responseText;
          if (!t || t.length < 40) return;
          var ring = window.__catCapture.ring;
          ring.push({ u: x.__u, body: t, at: Date.now() });
          if (ring.length > 40) ring.shift();
        } catch (e) { /* ignore */ }
      });
      return os.apply(this, arguments);
    };
  }

  var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };

  function nav() { return document.querySelector('.navigationContent'); }

  function leaves() {
    var n = nav();
    if (!n) return [];
    var out = [], seen = {};
    var all = n.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
      var e = all[i];
      if (e.children.length !== 0) continue;
      var t = (e.textContent || '').trim();
      if (!t) continue;
      if (seen[t]) continue;
      seen[t] = 1;
      out.push(t);
    }
    return out;
  }

  function clickLeaf(txt) {
    var n = nav();
    if (!n) return false;
    var all = n.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
      var e = all[i];
      if (e.children.length === 0 && (e.textContent || '').trim() === txt) { e.click(); return true; }
    }
    return false;
  }

  function since(ms) {
    var ring = window.__catCapture.ring;
    var out = [];
    for (var i = ring.length - 1; i >= 0; i--) {
      if (ring[i].at < ms) break;
      out.unshift(ring[i]);
    }
    return out;
  }

  function newest(recs, re) {
    for (var i = recs.length - 1; i >= 0; i--) { if (re.test(recs[i].u)) return recs[i]; }
    return null;
  }

  // Click something and return the payload the app fetched as a result.
  async function clickAndWait(txt, urlRe, timeoutMs) {
    var t0 = Date.now();
    if (!clickLeaf(txt)) return { error: 'node not found: ' + txt };
    while (Date.now() - t0 < (timeoutMs || 20000)) {
      await sleep(250);
      var hit = newest(since(t0), urlRe);
      if (hit) return { payload: hit.body, url: hit.u, ms: Date.now() - t0 };
    }
    return { error: 'timeout waiting for ' + urlRe + ' after ' + txt, ms: Date.now() - t0 };
  }

  function fmtPN(f) {
    // EPC returns both a raw and a formatted number, e.g. "8-97601-967-0"
    return f ? String(f).replace(/[^0-9A-Za-z]/g, '') : null;
  }

  function parseParts(jsonText, ctx) {
    var j;
    try { j = JSON.parse(jsonText); } catch (e) { return { error: 'bad json: ' + e.message }; }
    var items = j.partItems || [];
    var out = [];
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      out.push({
        part_number: fmtPN(it.formattedPartNumber || it.partNumber),
        part_number_formatted: it.formattedPartNumber || it.partNumber,
        figkey: it.calloutLabel != null ? String(it.calloutLabel) : null,
        part_name: it.description || null,
        quantity: it.quantity != null ? it.quantity : null,
        position: it.position != null ? String(it.position) : null,
        remarks: it.remarks || null,
        l_r: it.lR != null ? it.lR : (it.leftRight != null ? it.leftRight : null),
        page_id: j.pageId != null ? String(j.pageId) : null,
        image_id: j.imageId != null ? String(j.imageId) : null,
        catalogue_family: ctx.catalogue_family || null,
        edition_id: ctx.edition_id || null,
        edition_text: ctx.edition_text || null,
        systems_path: ctx.systems_path || null,
        asm_page: !!j.asmPage,
        accessories_page: !!j.accessoriesPage,
        page_limit_exceeded: !!j.pageLimitExceeded,
      });
    }
    return { rows: out, pageId: j.pageId, imageId: j.imageId, pageImages: (j.pageImages || []).length };
  }

  // ---- run -------------------------------------------------------------------
  // editions: array of edition texts, already in the order to process
  window.__catRun = async function (editions, family, opts) {
    if (S.running) return 'already running';
    opts = opts || {};
    var settle = opts.settleMs || 700;   // pause between requests (shared production system)
    S.running = true; S.started = Date.now(); S.phase = 'starting';
    S.editions = editions.slice(); S.edIndex = 0;

    for (var ei = 0; ei < editions.length; ei++) {
      S.edIndex = ei;
      var ed = editions[ei];
      S.phase = 'edition: ' + ed;

      var r = await clickAndWait(ed, /\/navigations\//, 20000);
      if (r.error) { S.errors.push({ edition: ed, where: 'edition', error: r.error }); continue; }
      await sleep(settle);

      var systems = leaves().filter(function (t) { return /^\d+ - /.test(t); });
      if (!systems.length) { S.errors.push({ edition: ed, where: 'systems', error: 'none listed' }); continue; }

      for (var si = 0; si < systems.length; si++) {
        var sys = systems[si];
        var r2 = await clickAndWait(sys, /\/navigations\//, 20000);
        if (r2.error) { S.errors.push({ edition: ed, system: sys, error: r2.error }); continue; }
        await sleep(settle);

        var subs = leaves().filter(function (t) { return /^\d+-\d+ - /.test(t); });
        for (var fi = 0; fi < subs.length; fi++) {
          var sub = subs[fi];
          var r3 = await clickAndWait(sub, /\/pages\/parts\//, 25000);
          if (r3.error) { S.errors.push({ edition: ed, system: sys, fig: sub, error: r3.error }); continue; }
          var parsed = parseParts(r3.payload, {
            catalogue_family: family, edition_id: ed.split(' - ')[0], edition_text: ed,
            systems_path: sys + ' > ' + sub,
          });
          if (parsed.error) { S.errors.push({ edition: ed, fig: sub, error: parsed.error }); continue; }
          S.stats.figs++;
          if (!parsed.rows.length) S.stats.emptyFigs++;
          S.stats.rows += parsed.rows.length;
          for (var k = 0; k < parsed.rows.length; k++) S.rows.push(parsed.rows[k]);
          // keep a compact progress trail
          S.log.push({ phase: 'fig', fig: sub, rows: parsed.rows.length });
          if (S.log.length > 400) S.log.shift();
          await sleep(settle);

          // re-read subsection list each time (the tree can re-render)
          subs = leaves().filter(function (t) { return /^\d+-\d+ - /.test(t); });
        }
        S.stats.editions = ei + 1;
      }
    }

    S.phase = 'done';
    S.running = false;
    S.elapsedMs = Date.now() - S.started;
    return 'finished';
  };

  window.__catStatus = function () {
    return JSON.stringify({
      running: S.running, phase: S.phase, edIndex: S.edIndex, editions: S.editions.length,
      stats: S.stats, elapsedMs: S.elapsedMs || (S.started ? Date.now() - S.started : 0),
      errors: S.errors.length, lastError: S.errors.length ? S.errors[S.errors.length - 1] : null,
      lastLog: S.log.slice(-5),
      bufferBytes: JSON.stringify(S.rows).length,
      sample: S.rows.slice(0, 3),
    });
  };

  window.__catTake = function () { return JSON.stringify(S.rows); };
  window.__catDrain = function () { var r = S.rows; S.rows = []; return JSON.stringify(r); };
  window.__catReset = function () {
    S.rows = []; S.errors = []; S.log = []; S.stats = { editions: 0, figs: 0, rows: 0, emptyFigs: 0 };
    S.phase = 'idle'; S.running = false; return 'reset';
  };

  return 'catalogue controller installed';
})();
