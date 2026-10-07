/* Whole-space QA harness for ISZE_Backlog_IML_WK41.html.
   Runs inside the page (real browser, locally served) and returns one record per
   (tab, dimension, canvas). Nothing is skipped: every tab, every dropdown option. */
(async function () {
  const TABS = ['delay', 'parts', 'who', 'recur', 'wait', 'fill', 'bo', 'miss'];
  const raf = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  const out = { rows: [], clicks: [], errors: [] };

  function txt(id) {
    const e = document.getElementById(id);
    return e ? e.textContent.trim() : '';
  }

  /* the value axis depends on orientation; a doughnut has none */
  function valueAxis(ch) {
    if (!ch || !ch.scales) return null;
    if (ch.config.type === 'doughnut' || ch.config.type === 'pie') return null;
    if (ch.options && ch.options.indexAxis === 'y') return ch.scales.x || null;
    return ch.scales.y || null;
  }

  function measureCanvas(c) {
    const ch = window.Chart.getChart(c);
    const rec = {
      canvas_id: c.id, type: ch ? ch.config.type : 'none',
      datasets: 0, points: 0, data_max: 0, scale_max: null,
      drawn: 0, css_h: Math.round(c.getBoundingClientRect().height),
      title: (function () { const h = document.getElementById('h-' + c.id); return h ? h.textContent.trim() : ''; })(),
    };
    if (ch) {
      rec.datasets = ch.data.datasets.length;
      ch.data.datasets.forEach((d, i) => {
        rec.points += d.data.length;
        d.data.forEach(v => { const n = Number(v); if (isFinite(n) && n > rec.data_max) rec.data_max = n; });
        const meta = ch.getDatasetMeta(i);
        rec.drawn += meta.data.filter(e => e && (e.height > 0 || e.width > 0 || e.outerRadius > 0)).length;
      });
      const va = valueAxis(ch);
      rec.scale_max = va ? va.max : null;
    }
    return rec;
  }

  function status(rec) {
    if (rec.datasets < 1) return 'FAIL';
    if (rec.points < 1) return 'FAIL';
    if (rec.data_max <= 0) return 'FAIL';
    if (rec.drawn < 1) return 'FAIL';
    if (rec.scale_max != null && rec.scale_max <= 1) return 'FAIL';
    return 'PASS';
  }

  function rowsFor(panel) {
    const o = txt('out-' + panel);
    if (o) return o;
    const h = document.querySelector('#' + panel.replace('p-', 'p-') + ' #t-rows .hint');
    return h ? h.textContent.trim() : '';
  }

  /* two passes: the first pass warms layout so hidden panels have been shown once */
  for (const t of TABS) {
    const tab = document.querySelector('.tab[data-t="' + t + '"]');
    if (!tab) { out.errors.push('no tab ' + t); continue; }
    tab.click();
    await raf();
    const panel = document.getElementById('p-' + t);
    const canvases = panel ? Array.prototype.slice.call(panel.querySelectorAll('canvas')) : [];
    const sel = document.getElementById('sel-p-' + t);
    const dims = sel ? Array.prototype.slice.call(sel.options).map(o => o.value) : ['(none)'];

    for (const d of dims) {
      if (sel) {
        sel.value = d;
        sel.onchange();
        await raf();
        /* force layout so a panel that was hidden has a real size before measuring */
        void panel.offsetHeight;
        if (typeof window.__QA !== 'undefined' && window.__QA && window.__QA.renderAll) {
          try { window.__QA.renderAll(); } catch (e) { out.errors.push('renderAll ' + t + '/' + d + ': ' + e.message); }
          await raf();
        }
      }
      const rows = rowsFor('p-' + t);
      const applied = txt('ap-' + t);
      if (!canvases.length) {
        out.rows.push({
          tab: t, dimension: d, canvas_id: '(no chart)', type: '-', datasets: 0, points: 0,
          data_max: 0, scale_max: null, drawn: 0, css_h: 0, title: '',
          rows: rows, applied: applied, status: 'PASS',
        });
        continue;
      }
      for (const c of canvases) {
        const m = measureCanvas(c);
        out.rows.push(Object.assign({
          tab: t, dimension: d, rows: rows, applied: applied, status: status(m),
        }, m));
      }
    }

    /* click test: click the first drawn bar or arc on this panel, then clear */
    if (canvases.length) {
      const c = canvases[0];
      const ch = window.Chart.getChart(c);
      if (ch) {
        const before = rowsFor('p-' + t);
        const r = c.getBoundingClientRect();
        let el = null;
        for (let ds = 0; ds < ch.data.datasets.length && !el; ds++) {
          const meta = ch.getDatasetMeta(ds);
          for (let i = 0; i < meta.data.length; i++) {
            const e = meta.data[i];
            if (e && (e.height > 0 || e.width > 0 || e.outerRadius > 0)) { el = e; break; }
          }
        }
        let after = before;
        if (el) {
          const cx = r.left + (el.x != null ? el.x : 0);
          const cy = r.top + ((el.base != null ? (el.y + el.base) / 2 : el.y) || 0);
          c.dispatchEvent(new MouseEvent('click', {
            bubbles: true, cancelable: true, clientX: cx, clientY: cy, view: window }));
          await raf();
          after = rowsFor('p-' + t);
        }
        const clear = document.querySelector('#dr-' + t + ' button[data-clear]');
        if (clear) { clear.click(); await raf(); }
        out.clicks.push({
          tab: t, before: before, after_click: after, after_clear: rowsFor('p-' + t),
          applied_after_clear: txt('ap-' + t),
        });
      }
    }
  }

  out.stamp = txt('stamp');
  out.errors = out.errors.slice(0, 20);
  return JSON.stringify(out);
})()
