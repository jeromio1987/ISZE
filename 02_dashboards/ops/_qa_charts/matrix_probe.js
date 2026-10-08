/* Chart matrix probe, v2, for the LIVE page.
   One row per (tab, dimension, canvas) plus, on the plain-load-then-click path, the box height and
   chart height. A sub-100px height is a FAIL even when the data is present: a chart nobody can hit
   is not a working chart. Also records the result of a level-1 and a level-2 click per chart, so a
   chart that promises a drill and changes nothing is caught.

   This deliberately uses the PATH JEROME TAKES: plain load, then click the tab. No dimension change
   and no hash URL. My first harness changed the dimension, which forces a full relayout and hid the
   height fault that his screen showed. */
(async function () {
  var rows = [];
  var tabs = [].map.call(document.querySelectorAll('.tab'), function (t) { return t.getAttribute('data-t'); });
  var canvasesOf = {};
  [].forEach.call(document.querySelectorAll('.panel'), function (p) {
    canvasesOf[p.id] = [].map.call(p.querySelectorAll('canvas'), function (c) { return c.id; });
  });
  function sleep(n) {
    return new Promise(function (r) {
      requestAnimationFrame(function () { requestAnimationFrame(function () { setTimeout(r, n || 60); }); });
    });
  }
  function rowsInfo(panel) {
    var cnt = document.getElementById('out-' + panel);
    if (cnt && cnt.textContent.trim()) {
      var m = cnt.textContent.match(/([\d,\.]+)\s+lines(?:,\s*([\d,\.]+)\s*pieces)?/i);
      if (m) return { lines: +m[1].replace(/[^\d]/g, ''), pieces: m[2] ? +m[2].replace(/[^\d]/g, '') : null };
    }
    var hint = document.querySelector('#p-' + panel + ' .hint');
    if (hint && /lines/.test(hint.textContent)) {
      var h = hint.textContent.match(/([\d,\.]+)\s+lines(?:,\s*([\d,\.]+)\s*pieces)?/i);
      if (h) return { lines: +h[1].replace(/[^\d]/g, ''), pieces: h[2] ? +h[2].replace(/[^\d]/g, '') : null };
    }
    return { lines: null, pieces: null };
  }
  function chartOf(id) { try { return window.Chart.getChart(document.getElementById(id)); } catch (e) { return null; } }
  function describe(id) {
    var c = document.getElementById(id), box = c.closest('.chartbox');
    var ch = chartOf(id);
    var o = {
      box_h: box ? Math.round(box.getBoundingClientRect().height) : null,
      canvas_h: Math.round(c.getBoundingClientRect().height),
      chart_h: ch ? ch.height : null,
      datasets: ch ? ch.data.datasets.length : 0,
      points: 0, data_max: 0, scale_max: null, arcs: null
    };
    if (ch) {
      ch.data.datasets.forEach(function (ds) {
        o.points += ds.data.length;
        ds.data.forEach(function (v) { var n = Math.abs(Number(v) || 0); if (n > o.data_max) o.data_max = n; });
      });
      if (ch.config.type === 'doughnut') {
        o.arcs = ch.getDatasetMeta(0).data.filter(function (e) { return e && e.outerRadius > 0; }).length;
        o.scale_max = 'n/a';
      } else {
        var v = (ch.options.indexAxis === 'y') ? 'x' : 'y';
        o.scale_max = (ch.scales && ch.scales[v]) ? ch.scales[v].max : null;
      }
    }
    return o;
  }
  function pass(d) {
    if (d.canvas_h < 100) return false;                 /* unclickable */
    if (d.datasets < 1 || d.points < 1 || d.data_max <= 0) return false;
    if (d.arcs !== null) return d.arcs >= 1;
    return d.scale_max !== null && d.scale_max > 1;
  }
  /* a click on element 0 of a chart; returns what visibly changed */
  function probeClick(id) {
    var c = document.getElementById(id), ch = chartOf(id);
    if (!ch) return { clicked: false };
    var beforeLine = document.querySelector('#t-rows .hint') ? document.querySelector('#t-rows .hint').textContent : '';
    var beforeDetail = [].map.call(document.querySelectorAll('.hint,.applied'), function (e) { return e.textContent.length; }).join(',');
    var tb = document.querySelectorAll('#' + (document.querySelector('.panel.on').id.replace('p-', 't-')) + ' tbody tr').length;
    var el = ch.getDatasetMeta(0).data[0];
    if (!el || !isFinite(el.x)) return { clicked: false };
    var r = c.getBoundingClientRect();
    var fn = ch.config.type === 'doughnut' ? 'arc' : 'bar';
    var x, y;
    if (fn === 'arc') { x = r.left + el.x; y = r.top + el.y; }
    else { y = r.top + ((isFinite(el.y) ? el.y : 0) + (isFinite(el.base) ? el.base : 0)) / 2; x = r.left + el.x; }
    if (!isFinite(x) || !isFinite(y)) return { clicked: false };
    c.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: x, clientY: y, view: window }));
    var after = document.querySelectorAll('#' + (document.querySelector('.panel.on').id.replace('p-', 't-')) + ' tbody tr').length;
    var afterDetail = [].map.call(document.querySelectorAll('.hint,.applied'), function (e) { return e.textContent.length; }).join(',');
    var line = document.querySelector('#t-rows .hint') ? document.querySelector('#t-rows .hint').textContent : '';
    return {
      clicked: true,
      label: ch.data.labels[0],
      table_changed: after !== tb,
      rows_after: after,
      path_changed: afterDetail !== beforeDetail,
      rows_line_changed: line !== beforeLine
    };
  }

  for (var ti = 0; ti < tabs.length; ti++) {
    var t = tabs[ti];
    var tabEl = document.querySelector('.tab[data-t="' + t + '"]');
    if (!tabEl) continue;
    tabEl.click();                                  /* plain load then click - his path */
    await sleep(120);
    var panel = 'p-' + t;
    var ids = canvasesOf[panel] || [];
    var ri = rowsInfo(panel);
    if (!ids.length) {
      rows.push({ tab: t, dimension: '(none)', canvas: '(no chart)', box_h: null, canvas_h: null,
                  chart_h: null, datasets: 0, points: 0, data_max: 0, scale_max: '',
                  arcs: '', rows_lines: ri.lines, click1: '', click1_changed: '', click2: '', status: 'PASS' });
      continue;
    }
    for (var ci = 0; ci < ids.length; ci++) {
      var id = ids[ci];
      var d = describe(id);
      /* level-1 click on the freshly clicked-tab chart */
      var c1 = probeClick(id);
      await sleep(140);
      var c2 = { clicked: false };
      if (c1.clicked) { c2 = probeClick(id); await sleep(140); }
      rows.push({
        tab: t, dimension: '(default)', canvas: id,
        box_h: d.box_h, canvas_h: d.canvas_h, chart_h: d.chart_h,
        datasets: d.datasets, points: d.points, data_max: d.data_max,
        scale_max: d.scale_max, arcs: d.arcs === null ? '' : d.arcs,
        rows_lines: ri.lines,
        click1: c1.clicked ? String(c1.label).slice(0, 22) : '',
        click1_changed: c1.clicked ? (c1.table_changed || c1.path_changed || c1.rows_line_changed ? 'yes' : 'NO') : '',
        click2: c2.clicked ? String(c2.label).slice(0, 22) : '',
        status: pass(d) ? 'PASS' : 'FAIL'
      });
      /* clear so the next chart starts clean */
      var clr = document.querySelector('.drillbar button[data-clear]');
      if (clr) clr.click();
      var clr2 = document.querySelector('#who-detail button[data-clearsel]');
      if (clr2) clr2.click();
      await sleep(80);
    }
  }
  return JSON.stringify(rows);
})()
