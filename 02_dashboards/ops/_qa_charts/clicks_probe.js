/* Click-and-clear matrix: on every tab, click the first drawn bar or arc, confirm the table
   narrows, then clear and confirm it returns. Reports what was clicked and what changed. */
(async function () {
  var TABS = ['delay', 'parts', 'who', 'recur', 'wait', 'fill', 'bo'];
  var raf = function () { return new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); }); };
  var out = [];
  function txt(id) { var e = document.getElementById(id); return e ? e.textContent.trim() : ''; }
  function rowCounts(panel) {
    var host = document.getElementById(panel);
    var best = null;
    [].forEach.call(host.querySelectorAll('table'), function (t) {
      var n = t.querySelectorAll('tbody tr').length;
      if (!best || n > best.n) best = { n: n, t: t };
    });
    return best ? best.n : 0;
  }
  function state(panel) {
    return { out: txt('out-' + panel), rows: rowCounts(panel), applied: txt('ap-' + panel) };
  }
  for (var i = 0; i < TABS.length; i++) {
    var t = TABS[i];
    var tab = document.querySelector('.tab[data-t="' + t + '"]');
    if (!tab) continue;
    tab.click();
    await raf();
    var panel = document.getElementById('p-' + t);
    var canvas = panel.querySelector('canvas');
    var rec = { tab: t };
    if (!canvas) { out.push(rec); continue; }
    var ch = window.Chart.getChart(canvas);
    if (!ch) { out.push(rec); continue; }
    var before = state('p-' + t);
    var el = null;
    for (var ds = 0; ds < ch.data.datasets.length && !el; ds++) {
      var meta = ch.getDatasetMeta(ds);
      for (var k = 0; k < meta.data.length; k++) {
        var e = meta.data[k];
        if (e && (e.height > 0 || e.width > 0 || e.outerRadius > 0)) { el = e; break; }
      }
    }
    rec = { tab: t, canvas: canvas.id, before: before };
    if (el) {
      var r = canvas.getBoundingClientRect();
      var cx = r.left + (el.x != null ? el.x : 0);
      var cy = r.top + ((el.base != null ? (el.y + el.base) / 2 : (el.y || 0)));
      canvas.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: cx, clientY: cy, view: window }));
      await raf(); await new Promise(function (r2) { setTimeout(r2, 120); });
      rec.after_click = state('p-' + t);
    }
    var clear = document.querySelector('#dr-' + t + ' button[data-clear]');
    if (clear) {
      clear.click();
      await raf(); await new Promise(function (r2) { setTimeout(r2, 120); });
      rec.after_clear = state('p-' + t);
    }
    out.push(rec);
  }
  var payload = JSON.stringify(out, null, 1);
  try { await fetch('/save?f=clicks.json', { method: 'POST', body: payload }); } catch (e) {}
  return payload;
})()
