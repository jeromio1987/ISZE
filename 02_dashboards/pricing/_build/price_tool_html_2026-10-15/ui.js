(function () {
  var D = JSON.parse(document.getElementById('payload').textContent);
  var M = makeModel(D), R = D.rows, n = R.length, CEIL = 0.05;
  var $ = function (id) { return document.getElementById(id); };
  var NAMES = ['PR00', 'UTI', 'UMI', 'OTH'];
  var LABEL = { ALL: 'All lists', PR00: 'PR00 (EU and UK)', UTI: 'UTI 1799', UMI: 'UMI 1797' };
  var LNAME = ['PR00: EU and UK distributors', 'UTI Israel trucks (1799)', 'UMI Israel D-Max (1797)', 'Other own lists'];
  var st = { target: 0.053, view: 'ALL', S: null, open: {}, q: '' };

  function defaults() {
    var S = {};
    D.pad_parts.forEach(function (p) { S['p:' + p] = { ALL: '0' }; });
    D.pad_l3.forEach(function (i) { S['l3:' + i] = { ALL: '0' }; });
    return S;
  }
  st.S = defaults();

  function fp(x, d) { return (x * 100).toFixed(d === undefined ? 1 : d).replace('.', ',') + '%'; }
  function fe(x) { return 'EUR ' + Math.round(x).toLocaleString('nl-NL'); }
  function fm(x) { return 'EUR ' + (x / 1e6).toFixed(2).replace('.', ',') + 'M'; }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); }
  function vks() { return st.view === 'ALL' ? [0, 1, 2, 3] : [NAMES.indexOf(st.view)]; }
  function skey() { return st.view; }

  var l3parts = D.l3.map(function () { return []; });
  for (var i = 0; i < n; i++) l3parts[R[i][4]].push(i);

  var res, A1, A2, A3, T, PL;
  function recalc() {
    res = M.run(st.S, st.target, CEIL);
    var ks = vks();
    A1 = D.l1.map(z); A2 = D.l2.map(z); A3 = D.l3.map(z);
    function z() { return { p: 0, b: 0, x: 0, w: 0 }; }
    PL = NAMES.map(function () { return { b: 0, x: 0, w: 0, k0: 0, kc: 0, bc: 0, xc: 0 }; });
    for (var i = 0; i < n; i++) {
      var r = R[i], c = r[9];
      for (var k = 0; k < 4; k++) {
        var b = r[5 + k]; if (!b) continue;
        var x = b * res.mv[k][i], p = PL[k];
        p.b += b; p.x += x; p.w += b * c;
        var kc = r[10 + k];
        if (kc > 0) { p.k0 += kc; p.kc += kc * c; p.bc += b; p.xc += x; }
      }
      var sb = 0, sx = 0;
      for (var q = 0; q < ks.length; q++) { var kk = ks[q]; var bb = r[5 + kk]; sb += bb; sx += bb * res.mv[kk][i]; }
      if (sb > 0) {
        var a = [A1[r[2]], A2[r[3]], A3[r[4]]];
        for (var j = 0; j < 3; j++) { a[j].p++; a[j].b += sb; a[j].x += sx; a[j].w += sb * c; }
      }
    }
    T = { b: 0, x: 0, w: 0, k0: 0, kc: 0, bc: 0, xc: 0 };
    ks.forEach(function (k) { for (var f in T) T[f] += PL[k][f]; });
  }

  function partAgg(i) {
    var ks = vks(), r = R[i], b = 0, x = 0;
    ks.forEach(function (k) { b += r[5 + k]; x += r[5 + k] * res.mv[k][i]; });
    return { b: b, x: x };
  }
  function settingText(key) { var d = st.S[key]; return d && d[skey()] !== undefined ? d[skey()] : ''; }
  function inherited(key) { var d = st.S[key]; return d && d.ALL !== undefined && skey() !== 'ALL' ? d.ALL : ''; }
  function hasSet(key) { var d = st.S[key]; return !!d && Object.keys(d).some(function (k) { return d[k] !== '' && d[k] !== undefined; }); }

  // ---------- KPIs
  function kpis() {
    var inc = T.b ? T.x / T.b : 0, bp = T.b ? T.w / T.b : 0;
    var costPlain = T.k0 ? T.kc / T.k0 : 0;
    var newCost = T.k0 + T.kc, oldCostFx = T.k0 * D.fx / D.fx_prior;
    var costFx = oldCostFx ? newCost / oldCostFx - 1 : 0;
    var after = T.xc - T.kc, cov = T.b ? T.bc / T.b : 0;
    var h = '';
    function k(cls, lbl, val, note, tip) {
      h += '<div class="kpi ' + cls + '" data-tip="' + esc(tip) + '"><div class="lbl">' + lbl + '</div><div class="val">' + val + '</div><div class="note">' + note + '</div></div>';
    }
    k('', 'Weighted increase', fp(inc, 2), LABEL[st.view] + ', last 12 months', 'Extra billed euro divided by billed euro, on last year\'s quantities. This is the number the target sets for the whole book; a single price list can land above or below it.');
    k('', 'Extra billed', fe(T.x), 'on ' + fm(T.b) + ' billed', 'Sum over all parts of billed euro times the move. Last 12 months quantities, no volume reaction assumed.');
    k('', 'New billed total', fm(T.b + T.x), 'same quantities', 'Billed euro of July 2025 to June 2026 plus the extra. Not a forecast.');
    k('nv', 'BP step in yen', fp(bp, 2), 'purchase side, weighted by billed EUR', 'Change of the base price (BP) in yen between the prior and the new price table, weighted by billed euros. Independent of what you set on the selling side.');
    k('nv', 'Purchase cost in euro', (costFx >= 0 ? '+' : '') + fp(costFx, 2), 'incl. exchange rate; before FX ' + (costPlain >= 0 ? '+' : '') + fp(costPlain, 2), 'Euro purchase cost of the same quantities. BP / JPY per EUR x the source discount. Before FX uses ' + String(D.fx).replace('.', ',') + ' on both sides; including FX the old cost is taken at ' + String(D.fx_prior).replace('.', ',') + ' JPY per EUR (until 30 Sep 2026). Only parts with a known source (Japan or Thailand) are costed.');
    k('nv', 'Extra EUR after purchase step', fe(after), 'on ' + fp(cov, 0) + ' of billed with a known cost', 'Extra billed euro minus the extra purchase cost (BP step at ' + String(D.fx).replace('.', ',') + ' JPY per EUR, before the exchange rate move), for parts where the purchase source is known.');
    $('kpis').innerHTML = h;
    // status
    var base = 0, ext = 0; PL.forEach(function (p) { base += p.b; ext += p.x; });
    var bk = ext / base, gap = bk - st.target, s = $('status');
    if (Math.abs(gap) > 0.0004) {
      s.className = 'status warn';
      s.innerHTML = '<b>Target not reached.</b> The whole book lands on ' + fp(bk, 2) + ' against your ' + fp(st.target, 2) + '. ' +
        (gap < 0 ? 'Your holds and fixed moves leave too little room under the cap of BP step plus 5 points. Raise a fixed move or open a hold.' :
          'Your fixed moves already give more than the target and the automatic parts cannot go below 0%. Lower a fixed move.');
    } else {
      s.className = 'status';
      s.innerHTML = '<b>On target.</b> The whole book lands on ' + fp(bk, 2) + ' (' + fe(ext) + ' extra). Automatic parts follow their own BP step scaled by ' + res.s2.toFixed(3).replace('.', ',') + ', never below 0% and never more than 5 points above their BP step.';
    }
  }

  // ---------- bars
  function bars() {
    var rows = D.l1.map(function (nm, i) { return { i: i, nm: nm, a: A1[i] }; }).filter(function (r) { return r.a.b > 0; })
      .sort(function (a, b) { return b.a.x - a.a.x; }).slice(0, 12);
    var mx = Math.max.apply(null, rows.map(function (r) { return r.a.x; })) || 1;
    $('bars').innerHTML = rows.map(function (r) {
      return '<div class="brow" data-open="l1:' + r.i + '" data-tip="' + esc(r.nm + ': move ' + fp(r.a.x / r.a.b, 2) + ' on ' + fe(r.a.b) + ' billed. BP step ' + fp(r.a.w / r.a.b, 2)) + '">' +
        '<div class="nm">' + esc(r.nm) + '</div><div class="tr"><div class="fl" style="width:' + (100 * r.a.x / mx).toFixed(1) + '%"></div></div>' +
        '<div class="nu">' + fe(r.a.x) + ' &middot; ' + fp(r.a.x / r.a.b, 1) + '</div></div>';
    }).join('');
  }

  // ---------- tree
  function inp(key) {
    var v = settingText(key), ph = inherited(key) !== '' ? 'all: ' + inherited(key) : 'auto';
    var on = String(v) === '0' ? ' on' : '';
    return '<td><input class="in" data-k="' + key + '" value="' + esc(v) + '" placeholder="' + esc(ph) + '"></td>' +
      '<td><button class="hb' + on + '" data-h="' + key + '">Hold</button></td>';
  }
  function row(cls, key, name, parts, a, open, isPart) {
    var mv = a.b ? a.x / a.b : 0, bp = a.b ? a.w / a.b : 0;
    var car = isPart ? '<span class="car"></span>' : '<span class="car">' + (open ? '&#9662;' : '&#9656;') + '</span>';
    var ind = { l1: 0, l2: 18, l3: 36, pt: 54 }[cls];
    return '<tr class="' + cls + (hasSet(key) ? ' set' : '') + '" id="row-' + key.replace(':', '-') + '">' +
      '<td class="nm" ' + (isPart ? '' : 'data-t="' + key + '"') + ' style="padding-left:' + (10 + ind) + 'px">' + car + name + '</td>' +
      '<td class="num">' + parts + '</td><td class="num">' + fe(a.b) + '</td><td class="num dim">' + fp(bp, 1) + '</td>' +
      '<td class="num"><b>' + fp(mv, 1) + '</b></td><td class="num">' + fe(a.x) + '</td>' + inp(key) + '</tr>';
  }
  function partRow(i) {
    var r = R[i], a = partAgg(i); if (!a.b) return '';
    a.w = a.b * r[9];
    return row('pt', 'p:' + r[0], '<span class="dim">' + r[0] + '</span> ' + esc(r[1]), '', a, false, true);
  }
  function tree() {
    var h = '', q = st.q.trim().toUpperCase();
    if (q.length >= 2) {
      var hits = [];
      for (var i = 0; i < n; i++) if ((String(R[i][0]).indexOf(q) >= 0 || R[i][1].toUpperCase().indexOf(q) >= 0) && partAgg(i).b > 0) hits.push(i);
      hits.sort(function (a, b) { return partAgg(b).b - partAgg(a).b; });
      h = hits.slice(0, 60).map(partRow).join('') || '<tr><td colspan="8" class="dim">No part with billed euro on this price list matches.</td></tr>';
      if (hits.length > 60) h += '<tr><td colspan="8" class="dim">' + hits.length + ' matches, showing the 60 biggest. Narrow the search.</td></tr>';
      $('tree').innerHTML = h; return;
    }
    var l1 = D.l1.map(function (nm, i) { return i; }).filter(function (i) { return A1[i].b > 0; }).sort(function (a, b) { return A1[b].b - A1[a].b; });
    l1.forEach(function (i1) {
      var k1 = 'l1:' + i1, o1 = st.open[k1];
      h += row('l1', k1, esc(D.l1[i1]), A1[i1].p, A1[i1], o1, false);
      if (!o1) return;
      var l2 = []; D.l2.forEach(function (t, i2) { if (t[0] === i1 && A2[i2].b > 0) l2.push(i2); });
      l2.sort(function (a, b) { return A2[b].b - A2[a].b; });
      l2.forEach(function (i2) {
        var k2 = 'l2:' + i2, o2 = st.open[k2];
        h += row('l2', k2, esc(D.l2[i2][1]), A2[i2].p, A2[i2], o2, false);
        if (!o2) return;
        var l3 = []; D.l3.forEach(function (t, i3) { if (t[0] === i2 && A3[i3].b > 0) l3.push(i3); });
        l3.sort(function (a, b) { return A3[b].b - A3[a].b; });
        l3.forEach(function (i3) {
          var k3 = 'l3:' + i3, o3 = st.open[k3];
          h += row('l3', k3, esc(D.l3[i3][1]), A3[i3].p, A3[i3], o3, false);
          if (!o3) return;
          var ps = l3parts[i3].filter(function (i) { return partAgg(i).b > 0; }).sort(function (a, b) { return partAgg(b).b - partAgg(a).b; });
          h += ps.slice(0, 12).map(partRow).join('');
          if (ps.length > 12) h += '<tr><td colspan="8" class="dim" style="padding-left:64px">' + (ps.length - 12) + ' smaller parts not listed. Use the search box to find one, or set the move on this group.</td></tr>';
        });
      });
    });
    $('tree').innerHTML = h;
  }

  // ---------- list table
  function lists() {
    var ly = D.ly, h = '<thead><tr><th>Price list</th><th class="num">Billed now</th><th class="num">Billed new</th><th class="num">Increase</th><th class="num">BP step (yen)</th><th class="num">Purchase cost EUR incl. FX</th><th class="num">Extra EUR after purchase step</th></tr></thead><tbody>';
    var tb = 0, tx = 0, tw = 0, tk0 = 0, tkc = 0, tax = 0;
    PL.forEach(function (p, k) {
      var cf = p.k0 ? (p.k0 + p.kc) / (p.k0 * D.fx / D.fx_prior) - 1 : 0;
      h += '<tr><td>' + LNAME[k] + '</td><td class="num">' + fe(p.b) + '</td><td class="num">' + fe(p.b + p.x) + '</td><td class="num"><b>' + fp(p.b ? p.x / p.b : 0, 2) + '</b></td><td class="num">' + fp(p.b ? p.w / p.b : 0, 2) + '</td><td class="num">' + (p.k0 ? (cf >= 0 ? '+' : '') + fp(cf, 2) : 'n/a') + '</td><td class="num">' + fe(p.xc - p.kc) + '</td></tr>';
      tb += p.b; tx += p.x; tw += p.w; tk0 += p.k0; tkc += p.kc; tax += p.xc - p.kc;
    });
    var tcf = tk0 ? (tk0 + tkc) / (tk0 * D.fx / D.fx_prior) - 1 : 0;
    h += '<tr class="tot"><td>All lists</td><td class="num">' + fe(tb) + '</td><td class="num">' + fe(tb + tx) + '</td><td class="num">' + fp(tx / tb, 2) + '</td><td class="num">' + fp(tw / tb, 2) + '</td><td class="num">' + (tcf >= 0 ? '+' : '') + fp(tcf, 2) + '</td><td class="num">' + fe(tax) + '</td></tr>';
    h += '<tr class="ref"><td>2026 simulation file (last year), all lists</td><td class="num">' + fe(ly.turn0) + '</td><td class="num">' + fe(ly.turn1) + '</td><td class="num">' + fp(ly.turn, 2) + '</td><td class="num">' + fp(ly.bp, 2) + '</td><td class="num">+' + fp(ly.fob, 2) + '</td><td class="num">not in that file</td></tr></tbody>';
    $('lists').innerHTML = h;
  }

  function foot() {
    $('foot').innerHTML = 'Base: billed to distributors July 2025 to June 2026, EUR 32.595.853 on 15.273 part numbers, the same base as the price revision workbook of October 2026 and the AIM level Excel tool of 15 October 2026 (with the same settings this page matches its figures to within a few euro). AIM levels from the release of 11 Oct 2026. BP step from the prior and new base price tables. Purchase cost = BP / JPY per EUR x source discount (Japan ' + D.disc.J + ', Thailand ' + D.disc.T + '), ' + String(D.fx).replace('.', ',') + ' JPY per EUR from 1 Oct 2026, ' + String(D.fx_prior).replace('.', ',') + ' before. UMI (1797) and UTI (1799) have their own price lists and are never blended. The 2026 simulation file reference row is read from the Overview sheet of "pricing simulation 2026 5.xlsx" (PR00 + Israel + CIS). No volume reaction is assumed. Nothing here is published.';
  }

  function controls() {
    $('presets').innerHTML = [3, 4, 5, 5.3, 6].map(function (v) {
      return '<button class="chip' + (Math.abs(st.target * 100 - v) < 0.001 ? ' on' : '') + '" data-p="' + v + '">' + String(v).replace('.', ',') + '%</button>';
    }).join('');
    $('views').innerHTML = ['ALL', 'PR00', 'UTI', 'UMI'].map(function (v) {
      return '<button class="chip' + (st.view === v ? ' on' : '') + '" data-v="' + v + '">' + LABEL[v] + '</button>';
    }).join('');
  }
  function renderAll(keepTarget) {
    recalc(); controls(); kpis(); bars(); tree(); lists();
    if (!keepTarget) { $('tgt').value = (st.target * 100).toFixed(1).replace('.', ','); }
    $('rng').value = Math.min(8, st.target * 100);
  }

  // ---------- events
  function setTarget(v, keep) { if (isNaN(v)) return; st.target = Math.max(0, Math.min(0.15, v / 100)); renderAll(keep); }
  $('tgt').addEventListener('input', function () { setTarget(parseFloat(this.value.replace(',', '.')), true); });
  $('tgt').addEventListener('change', function () { renderAll(false); });
  $('rng').addEventListener('input', function () { setTarget(parseFloat(this.value), false); });
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-p],[data-v],[data-t],[data-h],[data-open]'); if (!t) return;
    if (t.dataset.p) setTarget(parseFloat(t.dataset.p), false);
    else if (t.dataset.v) { st.view = t.dataset.v; renderAll(true); }
    else if (t.dataset.t) { st.open[t.dataset.t] = !st.open[t.dataset.t]; recalc(); tree(); }
    else if (t.dataset.h) {
      var key = t.dataset.h; st.S[key] = st.S[key] || {};
      var cur = st.S[key][skey()];
      if (String(cur) === '0') delete st.S[key][skey()]; else st.S[key][skey()] = '0';
      renderAll(true);
    } else if (t.dataset.open) {
      var k = t.dataset.open, i1 = parseInt(k.split(':')[1], 10);
      st.q = ''; $('q').value = ''; st.open[k] = true; tree();
      var el = $('row-l1-' + i1); if (el) el.scrollIntoView({ block: 'start', behavior: 'smooth' });
    }
  });
  document.addEventListener('change', function (e) {
    var t = e.target; if (!t.classList.contains('in')) return;
    var key = t.dataset.k; st.S[key] = st.S[key] || {};
    var v = t.value.trim();
    if (v === '') delete st.S[key][skey()]; else st.S[key][skey()] = v;
    renderAll(true);
  });
  $('q').addEventListener('input', function () { st.q = this.value; tree(); });
  $('reset').addEventListener('click', function () { st.S = defaults(); st.target = 0.053; st.q = ''; $('q').value = ''; renderAll(false); });
  $('open1').addEventListener('click', function () { D.l1.forEach(function (x, i) { st.open['l1:' + i] = true; }); tree(); });
  $('close1').addEventListener('click', function () { st.open = {}; tree(); });
  $('exp').addEventListener('click', function () {
    var L = ['PR00', 'UTI', 'UMI', 'Other lists'], out = ['Part number;Description;AIM L1;AIM L2;AIM L3;Billed EUR;Move PR00;Move UTI 1799;Move UMI 1797;Move other lists'];
    function f(x) { return (x * 100).toFixed(2).replace('.', ','); }
    for (var i = 0; i < n; i++) {
      var r = R[i], tot = r[5] + r[6] + r[7] + r[8], l3 = D.l3[r[4]], l2 = D.l2[l3[0]];
      var cells = [0, 1, 2, 3].map(function (k) { return r[5 + k] > 0 ? f(res.mv[k][i]) : ''; });
      out.push([r[0], '"' + r[1].replace(/"/g, '""') + '"', '"' + D.l1[l2[0]] + '"', '"' + l2[1] + '"', '"' + l3[1] + '"', tot].concat(cells).join(';'));
    }
    var blob = new Blob(['﻿' + out.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = 'ISZE_price_moves_target_' + (st.target * 100).toFixed(1).replace('.', ',') + 'pct.csv'; document.body.appendChild(a); a.click(); a.remove();
  });

  foot(); renderAll(false);
  window.__sim = { st: st, res: function () { return res; }, T: function () { return T; }, PL: function () { return PL; } };
})();
