/* Chart matrix probe. Runs inside the page and returns one row per (tab, dimension, canvas).
   Served from _qa_charts/ so the page context can fetch and eval it. */
(async function () {
  var out = [];
  var tabs = [].map.call(document.querySelectorAll('.tab'), function (t) {
    return t.getAttribute('data-t');
  });
  var canvasesOf = {};
  [].forEach.call(document.querySelectorAll('.panel'), function (p) {
    canvasesOf[p.id] = [].map.call(p.querySelectorAll('canvas'), function (c) { return c.id; });
  });

  function sleep(n) {
    return new Promise(function (r) {
      requestAnimationFrame(function () {
        requestAnimationFrame(function () { setTimeout(r, n || 40); });
      });
    });
  }

  /* rows shown: line count and piece count for the visible panel */
  function rowsInfo(panel) {
    var host = document.getElementById(panel);
    if (!host) return { lines: null, pieces: null, source: 'no panel' };
    /* the counts we print into the drill bar, where a panel has one */
    var cnt = document.getElementById('out-' + panel);
    if (cnt && cnt.textContent.trim()) {
      var m = cnt.textContent.match(/([\d,\.]+)\s+lines,\s*([\d,\.]+)\s*pieces/i);
      if (m) return { lines: +m[1].replace(/[^\d]/g, ''), pieces: +m[2].replace(/[^\d]/g, ''), source: 'drill bar' };
      var m2 = cnt.textContent.match(/([\d,\.]+)\s+lines/i);
      if (m2) return { lines: +m2[1].replace(/[^\d]/g, ''), pieces: null, source: 'drill bar' };
    }
    var hint = document.getElementById('t-rows') ? host.querySelector('.hint') : null;
    if (hint && /lines/.test(hint.textContent)) {
      var h = hint.textContent.match(/([\d,\.]+)\s+lines,\s*([\d,\.]+)\s*pieces/i);
      if (h) return { lines: +h[1].replace(/[^\d]/g, ''), pieces: +h[2].replace(/[^\d]/g, ''), source: 'rows hint' };
    }
    /* fall back: largest tbody in the panel, and its Pieces column if there is one */
    var best = null;
    [].forEach.call(host.querySelectorAll('table'), function (t) {
      var n = t.querySelectorAll('tbody tr').length;
      if (!best || n > best.n) best = { n: n, t: t };
    });
    if (!best) return { lines: 0, pieces: null, source: 'no table' };
    var pieces = null;
    var ths = [].map.call(best.t.querySelectorAll('th'), function (th) { return th.textContent.trim().toLowerCase(); });
    var pi = ths.findIndex(function (x) { return x === 'pieces' || x.indexOf('pieces') === 0; });
    if (pi >= 0) {
      pieces = 0;
      [].forEach.call(best.t.querySelectorAll('tbody tr'), function (tr) {
        var td = tr.querySelectorAll('td')[pi];
        if (td) pieces += Number(String(td.textContent).replace(/[^\d\.-]/g, '')) || 0;
      });
    }
    return { lines: best.n, pieces: pieces, source: 'table' };
  }

  for (var ti = 0; ti < tabs.length; ti++) {
    var t = tabs[ti];
    var tabEl = document.querySelector('.tab[data-t="' + t + '"]');
    if (!tabEl) continue;
    tabEl.click();
    await sleep(60);
    var panel = 'p-' + t;
    var sel = document.getElementById('sel-' + panel);
    var dims = sel ? [].map.call(sel.options, function (o) { return o.value; }) : [null];

    for (var di = 0; di < dims.length; di++) {
      var d = dims[di];
      if (sel && d) { sel.value = d; sel.onchange(); }
      await sleep(120);
      var ri = rowsInfo(panel);
      var applied = document.getElementById('ap-' + panel);
      var appliedText = applied ? applied.textContent.trim() : '';
      var ids = canvasesOf[panel] || [];
      if (!ids.length) {
        out.push({ tab: t, dimension: d || '(none)', canvas: '(no chart)', datasets: 0, points: 0,
                   data_max: 0, scale_max: null, rows_lines: ri.lines, rows_pieces: ri.pieces,
                   applied: appliedText, status: 'PASS' });
        continue;
      }
      for (var ci = 0; ci < ids.length; ci++) {
        var cid = ids[ci];
        var c = document.getElementById(cid);
        var ch = null;
        try { ch = window.Chart.getChart(c); } catch (e) { ch = null; }
        var datasets = ch ? ch.data.datasets.length : 0;
        var points = 0, dataMax = 0, scaleMax = null, arcsDrawn = null, waited = false;
        if (ch) {
          ch.data.datasets.forEach(function (ds) {
            points += ds.data.length;
            ds.data.forEach(function (v) { var n = Math.abs(Number(v) || 0); if (n > dataMax) dataMax = n; });
          });
          if (ch.config.type === 'doughnut') {
            /* a doughnut has no value axis: the equivalent signal is arcs actually drawn */
            arcsDrawn = ch.getDatasetMeta(0).data.filter(function (e) { return e && e.outerRadius > 0; }).length;
            scaleMax = 'n/a (doughnut)';
          } else {
            var v = (ch.options.indexAxis === 'y') ? 'x' : 'y';
            scaleMax = (ch.scales && ch.scales[v]) ? ch.scales[v].max : null;
          }
        }
        var ok;
        if (arcsDrawn !== null) {
          /* a doughnut can be measured one frame before its arcs are laid out. Re-measure once,
             so the harness reports a genuinely blank canvas rather than a timing artefact. */
          if (arcsDrawn < 1 && dataMax > 0) {
            await sleep(220);
            arcsDrawn = ch.getDatasetMeta(0).data.filter(function (e) { return e && e.outerRadius > 0; }).length;
            waited = true;
          }
          ok = datasets >= 1 && points >= 1 && dataMax > 0 && arcsDrawn >= 1;
        } else {
          ok = datasets >= 1 && points >= 1 && dataMax > 0 && scaleMax !== null && scaleMax > 1;
        }
        out.push({
          tab: t, dimension: d || '(none)', canvas: cid,
          datasets: datasets, points: points, data_max: dataMax,
          scale_max: scaleMax === null ? 'null' : scaleMax,
          arcs_drawn: arcsDrawn === null ? '' : arcsDrawn,
          waited_a_frame: waited ? 1 : 0,
          rows_lines: ri.lines, rows_pieces: ri.pieces, applied: appliedText,
          status: ok ? 'PASS' : 'FAIL'
        });
      }
    }
  }
  var payload = JSON.stringify(out, null, 1);
  try {
    await fetch('/save?f=matrix.json', { method: 'POST', body: payload });
  } catch (e) { /* the matrix still comes back in the return value */ }
  return payload;
})()
