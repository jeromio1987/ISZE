(function () {
  var D = JSON.parse(document.getElementById('payload').textContent);
  var M = makeModel(D), P = D.parts, LN = D.lines, np = P.length, nl = LN.length, CEIL = 0.05, byPart = M.byPart, pc = M.partCost;
  var pnIdx = {}; P.forEach(function (r, i) { pnIdx[r[0]] = i; });
  var $ = function (id) { return document.getElementById(id); };
  var NAMES = ['PR00', 'UTI', 'UMI', 'OTH'];
  var LABEL = { ALL: 'All lists', PR00: 'PR00 (EU and UK)', UTI: 'UTI 1799', UMI: 'UMI 1797' };
  var LNAME = ['PR00: EU and UK distributors', 'UTI Israel trucks (1799)', 'UMI Israel D-Max (1797)', 'Other own lists'];
  var DBN = { IUK: 'Isuzu UK (D-Max)', ITUK: 'ITUK (UK trucks)', UTI: 'UTI Israel trucks', UMI: 'UMI Israel D-Max' };
  var COND = [
    { bit: 1, label: 'Service parts held at today\'s price in the markets of the 30 Sep exercise', why: 'service' },
    { bit: 2, label: 'UMI: body and collision parts held (paper of 2 Oct)', why: 'UMI Israel D-Max only' },
    { bit: 4, label: 'UMI: lighting held (paper of 2 Oct)', why: 'UMI Israel D-Max only' },
    { bit: 8, label: 'UTI: lighting held (paper of 2 Oct)', why: 'UTI Israel trucks only' },
    { bit: 16, label: 'Held where the distributor sells under 45% of what its trucks need in that parts category', why: 'measured per market and category' }
  ];
  var st = { target: 0.053, view: 'ALL', db: -1, S: null, mask: 0, open: {}, q: '', pl: 0, valid: '01.01.2026', onlyChg: true, scen: [] };

  function defaults() {
    var S = {};
    D.pad_parts.forEach(function (p) { S['p:' + p] = { ALL: '0' }; });
    D.pad_l3.forEach(function (i) { S['l3:' + i] = { ALL: '0' }; });
    return S;
  }
  st.S = defaults();
  try { var sv = localStorage.getItem('isze_price_sim_v2_scen'); if (sv) st.scen = JSON.parse(sv); } catch (e) { }

  function fp(x, d) { return (x * 100).toFixed(d === undefined ? 1 : d).replace('.', ',') + '%'; }
  function fe(x) { return 'EUR ' + Math.round(x).toLocaleString('nl-NL'); }
  function fm(x) { return 'EUR ' + (x / 1e6).toFixed(2).replace('.', ',') + 'M'; }
  function fn(x) { return (+x).toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;'); }
  function dbName(i) { var c = D.dbs[i]; return DBN[c] || (c.charAt(0) + c.slice(1).toLowerCase()); }
  function viewK() { return st.view === 'ALL' ? -1 : NAMES.indexOf(st.view); }
  function skey() { return st.view; }
  function maskText(m) {
    var t = []; COND.forEach(function (c) { if (m & c.bit) t.push(c.bit === 16 ? 'under 45% capture' : c.bit === 1 ? 'service' : c.bit === 2 ? 'UMI body' : c.bit === 4 ? 'UMI lighting' : 'UTI lighting'); });
    return t.length ? t.join(', ') : 'none';
  }

  // quantity x yen helpers
  var plB = [0, 1, 2].map(function () { return new Float64Array(np); });
  LN.forEach(function (l) { if (l[2] < 3) plB[l[2]][l[0]] += l[3]; });

  var res, A1, A2, A3, DB, PL, T, BK, HB, HBdb;
  function z() { return { p: 0, b: 0, x: 0, qb: 0, qd: 0 }; }
  function z2() { return { b: 0, x: 0, qb: 0, qd: 0, k0: 0, kc: 0, bc: 0, xc: 0, h: 0 }; }
  function add(a, l, mv, held) {
    var r = P[l[0]], b = l[3], x = held ? 0 : b * mv, c0 = l[5];
    a.b += b; a.x += x; a.qb += l[4] * r[6]; a.qd += l[4] * (r[7] - r[6]);
    if (held) a.h += b;
    if (pc[l[0]] > 0) { a.k0 += c0; a.kc += c0 * r[5]; a.bc += b; a.xc += x; }   // a part is costed when it has a known purchase source
  }
  function recalc() {
    res = M.run(st.S, st.target, CEIL, st.mask);
    var vk = viewK(), fd = st.db, mask = st.mask;
    A1 = D.l1.map(z); A2 = D.l2.map(z); A3 = D.l3.map(z);
    DB = D.dbs.map(z2); PL = NAMES.map(z2); T = z2(); BK = { b: 0, x: 0 };
    HB = { 1: 0, 2: 0, 4: 0, 8: 0, 16: 0 }; HBdb = {};
    var seen = new Uint8Array(np);
    for (var j = 0; j < nl; j++) {
      var l = LN[j], pi = l[0], k = l[2], held = (l[6] & mask) !== 0, mv = held ? 0 : res.mv[k][pi];
      BK.b += l[3]; BK.x += l[3] * mv;
      for (var bit = 1; bit <= 16; bit <<= 1) if (l[6] & bit) HB[bit] += l[3];
      if (l[6] & 1) HBdb[l[1]] = 1;
      var inV = vk < 0 || k === vk, inD = fd < 0 || l[1] === fd;
      if (inV) add(DB[l[1]], l, mv, held);
      if (inD) add(PL[k], l, mv, held);
      if (inV && inD) {
        add(T, l, mv, held);
        var r = P[pi], b = l[3], x = held ? 0 : b * mv, q0 = l[4] * r[6], qd = l[4] * (r[7] - r[6]);
        var a = [A1[r[2]], A2[r[3]], A3[r[4]]];
        for (var q = 0; q < 3; q++) { a[q].b += b; a[q].x += x; a[q].qb += q0; a[q].qd += qd; if (!seen[pi]) a[q].p++; }
        seen[pi] = 1;
      }
    }
  }
  function lineMv(l) { return (l[6] & st.mask) ? 0 : res.mv[l[2]][l[0]]; }
  function partAgg(i) {
    var vk = viewK(), a = { b: 0, x: 0, qb: 0, qd: 0 }, r = P[i];
    byPart[i].forEach(function (j) {
      var l = LN[j];
      if ((vk >= 0 && l[2] !== vk) || (st.db >= 0 && l[1] !== st.db)) return;
      a.b += l[3]; a.x += l[3] * lineMv(l); a.qb += l[4] * r[6]; a.qd += l[4] * (r[7] - r[6]);
    });
    return a;
  }
  function settingText(key) { var d = st.S[key]; return d && d[skey()] !== undefined ? d[skey()] : ''; }
  function inherited(key) { var d = st.S[key]; return d && d.ALL !== undefined && skey() !== 'ALL' ? d.ALL : ''; }
  function hasSet(key) { var d = st.S[key]; return !!d && Object.keys(d).some(function (k) { return d[k] !== '' && d[k] !== undefined; }); }
  function costFx(a) { var o = a.k0 * D.fx / D.fx_prior; return o ? (a.k0 + a.kc) / o - 1 : 0; }

  // ---------- KPIs and status
  function kpis() {
    var inc = T.b ? T.x / T.b : 0, bp = T.qb ? T.qd / T.qb : 0, plain = T.k0 ? T.kc / T.k0 : 0, cf = costFx(T);
    var after = T.xc - T.kc, cov = T.b ? T.bc / T.b : 0, h = '', ki = 0, KK = ['inc', 'extra', 'new', 'held', 'bp', 'cost', 'after'];
    function k(cls, lbl, val, note, tip) {
      h += '<div class="kpi ' + cls + '" data-tip="' + esc(tip) + '"><span class="fx" data-x="kpi:' + KK[ki++] + '" title="How is this calculated?">ƒ</span><div class="lbl">' + lbl + '</div><div class="val">' + val + '</div><div class="note">' + note + '</div></div>';
    }
    var scope = (st.db >= 0 ? dbName(st.db) : 'All markets') + ', ' + LABEL[st.view];
    k('', 'Weighted increase', fp(inc, 2), scope, 'Extra billed euro divided by billed euro on last year\'s quantities, for the market and price list in view. The target sets this for the whole book; one market or list can land above or below it.');
    k('', 'Extra billed', fe(T.x), 'on ' + fm(T.b) + ' billed', 'Billed euro times the move, summed over all lines in view. Last 12 months quantities, no volume reaction assumed.');
    k('', 'New billed total', fm(T.b + T.x), 'same quantities', 'Billed euro of July 2025 to June 2026 plus the extra. Not a forecast.');
    k('', 'Held at today\'s price', fe(T.h), fp(T.b ? T.h / T.b : 0, 0) + ' of billed in view', 'Billed euro in markets and parts you hold with the market conditions above. They pay no increase.');
    k('nv', 'BP step in yen', fp(bp, 2), 'purchase side, by quantity', 'Change of the base price (BP) in yen between the prior and new price table, weighted by quantity: the same definition as the 5.96% in the base price comparison (' + fp(D.bp_qty, 4) + ' on the whole book).');
    k('nv', 'Purchase cost in euro', (cf >= 0 ? '+' : '') + fp(cf, 2), 'incl. exchange rate; before FX ' + (plain >= 0 ? '+' : '') + fp(plain, 2), 'Euro purchase cost of the same quantities: BP / JPY per EUR x source discount. Before FX both sides use ' + String(D.fx).replace('.', ',') + '. Including FX the old cost is taken at ' + String(D.fx_prior).replace('.', ',') + ' JPY per EUR (until 30 Sep 2026). Only parts with a known source (Japan or Thailand) are costed.');
    k('nv', 'Extra EUR after purchase step', fe(after), 'on ' + fp(cov, 0) + ' of billed with a known cost', 'Extra billed euro minus the extra purchase cost (BP step at ' + String(D.fx).replace('.', ',') + ' JPY per EUR, before the exchange rate move), for parts whose purchase source is known.');
    $('kpis').innerHTML = h;
    var bk = BK.x / BK.b, gap = bk - st.target, s = $('status');
    if (Math.abs(gap) > 0.0004) {
      s.className = 'status warn';
      s.innerHTML = '<span class="fx" data-x="kpi:scale" title="How is this calculated?">ƒ</span><b>Target not reached.</b> The whole book lands on ' + fp(bk, 2) + ' against your ' + fp(st.target, 2) + '. ' +
        (gap < 0 ? 'Holds and fixed moves leave too little room under the cap of BP step plus 5 points. Release a hold, raise a fixed move, or lower the target.' :
          'Your fixed moves already give more than the target and the automatic parts cannot go below 0%. Lower a fixed move.');
    } else {
      s.className = 'status';
      s.innerHTML = '<span class="fx" data-x="kpi:scale" title="How is this calculated?">ƒ</span><b>On target.</b> The whole book lands on ' + fp(bk, 2) + ' (' + fe(BK.x) + ' extra). Conditions in force: ' + maskText(st.mask) + '. Parts you leave on auto follow their own BP step scaled by ' + res.s2.toFixed(3).replace('.', ',') + ', never below 0% and never more than 5 points above their BP step.' +
        (res.s2 > 1.0005 ? ' The scale is above 1 because the held lines carry nothing and the rest makes it up.' : '');
    }
  }

  // ---------- market conditions
  function cond() {
    var held = Object.keys(HBdb).map(function (i) { return dbName(+i); }).sort().join(', ');
    $('cond').innerHTML = COND.map(function (c) {
      var why = c.bit === 1 ? 'Markets: ' + held : c.why;
      return '<input type="checkbox" data-bit="' + c.bit + '" id="cb' + c.bit + '"' + (st.mask & c.bit ? ' checked' : '') + '>' +
        '<label for="cb' + c.bit + '">' + esc(c.label) + '<div class="why">' + esc(why) + '</div></label><div class="eur">' + fe(HB[c.bit]) + ' billed</div>';
    }).join('');
  }

  // ---------- bars
  function bars() {
    var rows = D.l1.map(function (nm, i) { return { i: i, nm: nm, a: A1[i] }; }).filter(function (r) { return r.a.b > 0; })
      .sort(function (a, b) { return b.a.x - a.a.x; }).slice(0, 12);
    var mx = Math.max.apply(null, rows.map(function (r) { return r.a.x; })) || 1;
    $('bars').innerHTML = rows.map(function (r) {
      return '<div class="brow" data-open="l1:' + r.i + '" data-tip="' + esc(r.nm + ': move ' + fp(r.a.x / r.a.b, 2) + ' on ' + fe(r.a.b) + ' billed. BP step ' + fp(r.a.qd / r.a.qb, 2)) + '">' +
        '<div class="nm">' + esc(r.nm) + '</div><div class="tr"><div class="fl" style="width:' + (100 * r.a.x / mx).toFixed(1) + '%"></div></div>' +
        '<div class="nu">' + fe(r.a.x) + ' &middot; ' + fp(r.a.x / r.a.b, 1) + '</div></div>';
    }).join('') || '<div class="dim">Nothing billed in this view.</div>';
  }

  // ---------- markets table
  function dbtable() {
    var idx = D.dbs.map(function (c, i) { return i; }).filter(function (i) { return DB[i].b > 0; }).sort(function (a, b) { return DB[b].b - DB[a].b; });
    var h = '<thead><tr><th>Market</th><th class="num">Billed EUR</th><th class="num">Held at today\'s price</th><th class="num">Increase</th><th class="num">Extra EUR</th><th class="num" data-tip="Base price step in yen weighted by quantity, on what this market bought.">BP step</th></tr></thead><tbody>';
    var tb = 0, th = 0, tx = 0, tq = 0, td = 0;
    idx.forEach(function (i) {
      var a = DB[i]; tb += a.b; th += a.h; tx += a.x; tq += a.qb; td += a.qd;
      h += '<tr class="dbr' + (st.db === i ? ' foc' : '') + '" data-db="' + i + '"><td>' + esc(dbName(i)) + '</td><td class="num">' + fe(a.b) + '</td><td class="num dim">' + (a.h ? fe(a.h) : '') + '</td><td class="num"><b>' + fp(a.x / a.b, 2) + '</b></td><td class="num">' + fe(a.x) + '</td><td class="num dim">' + fp(a.qb ? a.qd / a.qb : 0, 2) + '</td></tr>';
    });
    h += '<tr class="tot"><td>All markets in view</td><td class="num">' + fe(tb) + '</td><td class="num">' + fe(th) + '</td><td class="num">' + fp(tb ? tx / tb : 0, 2) + '</td><td class="num">' + fe(tx) + '</td><td class="num">' + fp(tq ? td / tq : 0, 2) + '</td></tr></tbody>';
    $('dbt').innerHTML = h;
    var sel = $('dbsel'), o = '<option value="-1">All markets</option>';
    D.dbs.forEach(function (c, i) { o += '<option value="' + i + '"' + (st.db === i ? ' selected' : '') + '>' + esc(dbName(i)) + '</option>'; });
    if (sel.dataset.built !== '1' || sel.value !== String(st.db)) { sel.innerHTML = o; sel.dataset.built = '1'; }
    sel.value = String(st.db);
  }

  // ---------- tree
  function inp(key) {
    var v = settingText(key), ph = inherited(key) !== '' ? 'all: ' + inherited(key) : 'auto';
    var on = String(v) === '0' ? ' on' : '';
    return '<td><input class="in" data-k="' + key + '" value="' + esc(v) + '" placeholder="' + esc(ph) + '"></td>' +
      '<td><button class="hb' + on + '" data-h="' + key + '">Hold</button></td>';
  }
  function row(cls, key, name, parts, a, open, isPart) {
    var mv = a.b ? a.x / a.b : 0, bp = a.qb ? a.qd / a.qb : 0;
    var car = isPart ? '<span class="car"></span>' : '<span class="car">' + (open ? '&#9662;' : '&#9656;') + '</span>';
    var ind = { l1: 0, l2: 18, l3: 36, pt: 54 }[cls];
    return '<tr class="' + cls + (hasSet(key) ? ' set' : '') + '" id="row-' + key.replace(':', '-') + '">' +
      '<td class="nm" ' + (isPart ? '' : 'data-t="' + key + '"') + ' style="padding-left:' + (10 + ind) + 'px">' + car + name + '</td>' +
      '<td class="num">' + parts + '</td><td class="num">' + fe(a.b) + '</td><td class="num dim">' + fp(bp, 1) + '</td>' +
      '<td class="num"><b>' + fp(mv, 1) + '</b></td><td class="num">' + fe(a.x) + '</td>' + inp(key) + '<td><span class="fx" data-x="' + key + '" title="How is this calculated?">ƒ</span></td></tr>';
  }
  function partRow(i) {
    var a = partAgg(i); if (!a.b) return '';
    return row('pt', 'p:' + P[i][0], '<span class="dim">' + P[i][0] + '</span> ' + esc(P[i][1]), '', a, false, true);
  }
  var l3parts = D.l3.map(function () { return []; });
  P.forEach(function (r, i) { l3parts[r[4]].push(i); });
  function tree() {
    var h = '', q = st.q.trim().toUpperCase();
    if (q.length >= 2) {
      var hits = [];
      for (var i = 0; i < np; i++) if ((String(P[i][0]).indexOf(q) >= 0 || P[i][1].toUpperCase().indexOf(q) >= 0) && partAgg(i).b > 0) hits.push(i);
      hits.sort(function (a, b) { return partAgg(b).b - partAgg(a).b; });
      h = hits.slice(0, 60).map(partRow).join('') || '<tr><td colspan="9" class="dim">No part with billed euro in this view matches.</td></tr>';
      if (hits.length > 60) h += '<tr><td colspan="9" class="dim">' + hits.length + ' matches, showing the 60 biggest. Narrow the search.</td></tr>';
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
          if (ps.length > 12) h += '<tr><td colspan="9" class="dim" style="padding-left:64px">' + (ps.length - 12) + ' smaller parts not listed. Use the search box to find one, or set the move on this group.</td></tr>';
        });
      });
    });
    $('tree').innerHTML = h;
  }

  // ---------- price file
  function priceRows(k) {
    var rows = [], un = { n: 0, b: 0 }, tot = 0;
    for (var i = 0; i < np; i++) {
      var b = plB[k][i]; if (b <= 0) continue; tot += b;
      var p0 = P[i][8 + k];
      if (!(p0 > 0)) { un.n++; un.b += b; continue; }
      var mv = res.mv[k][i], n2 = Math.round(p0 * (1 + mv) * 100) / 100;
      rows.push({ i: i, b: b, p0: p0, mv: mv, n2: n2, chg: n2 !== p0 });
    }
    return { rows: rows, un: un, tot: tot };
  }
  var PLN = ['PR00', 'UTI 1799', 'UMI 1797'];
  function pfSkeleton() {
    $('pf').innerHTML = '<div class="tools"><label>Price list <select id="pfl"><option value="0">PR00 (EU and UK distributors)</option><option value="1">UTI Israel trucks (1799)</option><option value="2">UMI Israel D-Max (1797)</option></select></label>' +
      '<label>Valid from <input type="text" id="pfv" value="' + st.valid + '" style="min-width:110px;width:110px"></label>' +
      '<label><input type="checkbox" id="pfc"' + (st.onlyChg ? ' checked' : '') + '> only parts whose price changes</label>' +
      '<button class="btn pri" id="pfd1">Download SAP paste (CSV)</button><button class="btn" id="pfd2">Download full price file (CSV)</button><button class="btn" id="xlb">Download Excel with formulas</button></div><div id="pfs"></div>';
    $('pfl').value = String(st.pl);
  }
  function pf() {
    if (viewK() >= 0 && viewK() < 3) { st.pl = viewK(); $('pfl').value = String(st.pl); }
    var pr = priceRows(st.pl), n = pr.rows.length, chg = pr.rows.filter(function (r) { return r.chg; }).length;
    var pbi = pr.rows.filter(function (r) { return P[r.i][12] !== ''; }).length;
    var bPriced = pr.tot - pr.un.b;
    var topRows = pr.rows.slice().sort(function (a, b) { return b.b - a.b; }).slice(0, 10);
    var h = '<p style="margin:8px 0">' + PLN[st.pl] + ': <b>' + n.toLocaleString('nl-NL') + '</b> parts with a price on file (' + fp(pr.tot ? bPriced / pr.tot : 0, 1) + ' of the euro billed on this list), <b>' + chg.toLocaleString('nl-NL') + '</b> change price. Prices now are the PR00 price table and the Israel price lists as exported on 10 Aug 2026; amounts round to the cent.</p>';
    if (pr.un.n) h += '<div class="amber"><b>' + pr.un.n.toLocaleString('nl-NL') + ' parts (' + fe(pr.un.b) + ' billed, ' + fp(pr.un.b / pr.tot, 1) + ') have no price on this list in the 10 Aug export</b> and cannot be written. They are listed at the end of the full file. Pull a fresh price export before loading.</div>';
    h += '<div class="amber"><b>Newest part number not fully checked.</b> The newest part number from Power BI is on file for ' + pbi + ' of these ' + n.toLocaleString('nl-NL') + ' parts (the ' + D.pbi_n + ' pulled on 15 Oct). Where it differs, the paste file adds a second line with the same amount. For the rest the full file shows what the older price table says as a hint only, because it can lag Power BI. Pull the newest column from Power BI (ISZJ PARTS MASTER) before loading.</div>';
    h += '<div class="scroll" style="max-height:none;margin-top:10px"><table><thead><tr><th>Part number</th><th>Description</th><th class="num">Price now</th><th class="num">Move</th><th class="num">New price</th><th class="num">Billed EUR on list</th><th></th></tr></thead><tbody>' +
      topRows.map(function (r) { return '<tr><td>' + P[r.i][0] + '</td><td>' + esc(P[r.i][1]) + '</td><td class="num">' + fn(r.p0) + '</td><td class="num"><b>' + fp(r.mv, 1) + '</b></td><td class="num">' + fn(r.n2) + '</td><td class="num">' + fe(r.b) + '</td><td><span class="fx" data-x="p:' + P[r.i][0] + '" title="How is this calculated?">ƒ</span></td></tr>'; }).join('') +
      '</tbody></table></div><p class="legend">The ten biggest parts on this list. The files hold all of them.</p>';
    $('pfs').innerHTML = h;
  }
  function q(s) { return '"' + String(s).replace(/"/g, '""') + '"'; }
  function dl(fname, text) {
    var blob = new Blob(['﻿' + text], { type: 'text/csv;charset=utf-8' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = fname; document.body.appendChild(a); a.click(); a.remove();
  }
  function dlJson(fname, obj) {
    var blob = new Blob([JSON.stringify(obj)], { type: 'application/json' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = fname; document.body.appendChild(a); a.click(); a.remove();
  }
  function paste() {
    var pr = priceRows(st.pl), out = ['Material;S;Description;P;Amount;Unit;Per;UoM;C;S;Valid From;Valid To;Role;PBI NEWEST;PBI check'];
    pr.rows.forEach(function (r) {
      if (st.onlyChg && !r.chg) return;
      var p = P[r.i], pn = p[0], nw = p[12], am = String(r.n2.toFixed(2)).replace('.', ',');
      var chk = nw === '' ? 'NOT CHECKED' : 'PBI checked';
      out.push([pn, '', q(p[1]), '', am, 'EUR', 1, 'EA', '', '', st.valid, '31.12.2999', 'ordered', nw, chk].join(';'));
      if (nw !== '' && nw !== pn) out.push([nw, '', q(p[1]), '', am, 'EUR', 1, 'EA', '', '', st.valid, '31.12.2999', 'newest', nw, chk].join(';'));
    });
    dl('ISZE_SAP_paste_' + PLN[st.pl].replace(' ', '_') + '_target_' + (st.target * 100).toFixed(1).replace('.', ',') + 'pct.csv', out.join('\r\n'));
  }
  function full() {
    var pr = priceRows(st.pl), out = ['Part number;Description;AIM L1;AIM L2;AIM L3;Billed EUR on list;Price now;Move;New price;Changes;Newest per older price table (hint only, may lag);Newest per Power BI;Power BI check'];
    pr.rows.slice().sort(function (a, b) { return b.b - a.b; }).forEach(function (r) {
      var p = P[r.i], l3 = D.l3[p[4]], l2 = D.l2[l3[0]];
      out.push([p[0], q(p[1]), q(D.l1[l2[0]]), q(l2[1]), q(l3[1]), String(r.b.toFixed(2)).replace('.', ','), String(r.p0.toFixed(2)).replace('.', ','), (r.mv * 100).toFixed(2).replace('.', ','),
        String(r.n2.toFixed(2)).replace('.', ','), r.chg ? 'yes' : 'no', p[11], p[12], p[12] === '' ? 'NOT CHECKED' : 'PBI checked'].join(';'));
    });
    var seen = {};
    for (var i = 0; i < np; i++) if (plB[st.pl][i] > 0 && !(P[i][8 + st.pl] > 0)) {
      out.push([P[i][0], q(P[i][1]), '', '', '', String(plB[st.pl][i].toFixed(2)).replace('.', ','), 'NO PRICE ON FILE', '', '', '', P[i][11], P[i][12], P[i][12] === '' ? 'NOT CHECKED' : 'PBI checked'].join(';'));
    }
    dl('ISZE_price_file_' + PLN[st.pl].replace(' ', '_') + '_target_' + (st.target * 100).toFixed(1).replace('.', ',') + 'pct.csv', out.join('\r\n'));
  }

  // ---------- list table
  function lists() {
    var ly = D.ly, h = '<thead><tr><th>Price list</th><th class="num">Billed now</th><th class="num">Billed new</th><th class="num">Increase</th><th class="num">BP step (yen)</th><th class="num">Purchase cost EUR incl. FX</th><th class="num">Extra EUR after purchase step</th></tr></thead><tbody>';
    var t = z2();
    PL.forEach(function (p, k) {
      var cf = costFx(p);
      h += '<tr><td>' + LNAME[k] + '</td><td class="num">' + fe(p.b) + '</td><td class="num">' + fe(p.b + p.x) + '</td><td class="num"><b>' + fp(p.b ? p.x / p.b : 0, 2) + '</b></td><td class="num">' + fp(p.qb ? p.qd / p.qb : 0, 2) + '</td><td class="num">' + (p.k0 ? (cf >= 0 ? '+' : '') + fp(cf, 2) : 'n/a') + '</td><td class="num">' + fe(p.xc - p.kc) + '</td></tr>';
      for (var f in t) t[f] += p[f];
    });
    var tcf = costFx(t);
    h += '<tr class="tot"><td>All lists' + (st.db >= 0 ? ', ' + esc(dbName(st.db)) : '') + '</td><td class="num">' + fe(t.b) + '</td><td class="num">' + fe(t.b + t.x) + '</td><td class="num">' + fp(t.b ? t.x / t.b : 0, 2) + '</td><td class="num">' + fp(t.qb ? t.qd / t.qb : 0, 2) + '</td><td class="num">' + (tcf >= 0 ? '+' : '') + fp(tcf, 2) + '</td><td class="num">' + fe(t.xc - t.kc) + '</td></tr>';
    h += '<tr class="ref"><td>2026 simulation file (last year), all lists</td><td class="num">' + fe(ly.turn0) + '</td><td class="num">' + fe(ly.turn1) + '</td><td class="num">' + fp(ly.turn, 2) + '</td><td class="num">' + fp(ly.bp, 2) + '</td><td class="num">+' + fp(ly.fob, 2) + '</td><td class="num">not in that file</td></tr></tbody>';
    $('lists').innerHTML = h;
  }

  // ---------- compare and scenarios
  function book(S, target, mask) {
    var r = M.run(S, target, CEIL, mask), o = { b: 0, x: 0, h: 0, k0: 0, kc: 0, xc: 0 };
    for (var j = 0; j < nl; j++) {
      var l = LN[j], pr = P[l[0]], held = (l[6] & mask) !== 0, x = held ? 0 : l[3] * r.mv[l[2]][l[0]];
      o.b += l[3]; o.x += x; if (held) o.h += l[3];
      if (pc[l[0]] > 0) { o.k0 += l[5]; o.kc += l[5] * pr[5]; o.xc += x; }
    }
    o.cf = costFx(o); o.after = o.xc - o.kc; o.inc = o.x / o.b; o.s2 = r.s2; o.ok = Math.abs(o.inc - target) < 0.0004;
    return o;
  }
  var cmpTimer;
  function cmp() {
    clearTimeout(cmpTimer);
    cmpTimer = setTimeout(function () {
      var cases = [[0.04, '4,0%'], [0.05, '5,0%'], [0.053, '5,3%'], [D.bp_qty, fp(D.bp_qty, 2) + ' (= BP step)']];
      var h = '<thead><tr><th>Your conditions and settings at</th><th class="num">Weighted increase</th><th class="num">Extra EUR</th><th class="num">Held at today\'s price</th><th class="num">Purchase cost incl. FX</th><th class="num">Extra EUR after purchase step</th><th>Target</th></tr></thead><tbody>';
      cases.forEach(function (c) {
        var o = book(st.S, c[0], st.mask), cur = Math.abs(c[0] - st.target) < 1e-4;
        h += '<tr class="' + (cur ? 'cur' : '') + '"><td>' + c[1] + (cur ? ' (current)' : '') + '</td><td class="num">' + fp(o.inc, 2) + '</td><td class="num">' + fe(o.x) + '</td><td class="num">' + fe(o.h) + '</td><td class="num">' + (o.cf >= 0 ? '+' : '') + fp(o.cf, 2) + '</td><td class="num">' + fe(o.after) + '</td><td>' + (o.ok ? 'reached' : 'not reached') + '</td></tr>';
      });
      $('cmp').innerHTML = h + '</tbody>';
    }, 40);
  }
  function scen() {
    var h = '<thead><tr><th>Saved scenario</th><th class="num">Target</th><th>Conditions</th><th class="num">Weighted increase</th><th class="num">Extra EUR</th><th class="num">Extra EUR after purchase step</th><th></th></tr></thead><tbody>';
    if (!st.scen.length) h += '<tr><td colspan="7" class="dim">None saved yet.</td></tr>';
    st.scen.forEach(function (s, i) {
      h += '<tr><td>' + esc(s.name) + '</td><td class="num">' + fp(s.target, 2) + '</td><td>' + esc(maskText(s.mask)) + '</td><td class="num">' + fp(s.tot.inc, 2) + '</td><td class="num">' + fe(s.tot.x) + '</td><td class="num">' + fe(s.tot.after) + '</td><td><button class="hb" data-sl="' + i + '">Load</button> <button class="hb" data-sd="' + i + '">Delete</button></td></tr>';
    });
    $('scen').innerHTML = h + '</tbody>';
  }
  function persist() { try { localStorage.setItem('isze_price_sim_v2_scen', JSON.stringify(st.scen)); } catch (e) { } }

  function foot() {
    $('foot').innerHTML = 'Base: billed to distributors July 2025 to June 2026, EUR 32.595.853 on 15.273 part numbers and 45.581 part and market lines, the same base as the price revision workbook of October 2026 and the AIM level Excel tool of 15 October 2026 (with no market condition ticked this page gives the same extra euro per price list as that tool, to the cent). AIM levels: approved release of 15 Oct 2026, with the 178 parts of the revert list of 15 Oct put back on their 11 Oct labels. BP step from the prior and new base price tables, weighted by quantity as in the base price comparison. Purchase cost = BP / JPY per EUR x source discount (Japan ' + D.disc.J + ', Thailand ' + D.disc.T + '), ' + String(D.fx).replace('.', ',') + ' JPY per EUR from 1 Oct 2026, ' + String(D.fx_prior).replace('.', ',') + ' before. Market conditions are read from the part and market file of the paper of 2 Oct 2026 and from the capture measure per market and category; the extra points for the UK shop price and the stance grid of that paper are not in this page. UMI (1797) and UTI (1799) have their own price lists and are never blended. The 2026 simulation file reference row is read from the Overview sheet of "pricing simulation 2026 5.xlsx" (PR00 + Israel + CIS). No volume reaction is assumed. Nothing here is published.';
  }

  function controls() {
    var bpv = D.bp_qty * 100;
    var pr = [[3, '3%'], [4, '4%'], [5, '5%'], [5.3, '5,3%'], [bpv, 'BP ' + fp(D.bp_qty, 2)]];
    $('presets').innerHTML = pr.map(function (v) {
      return '<button class="chip' + (Math.abs(st.target * 100 - v[0]) < 0.001 ? ' on' : '') + '" data-p="' + v[0] + '">' + v[1] + '</button>';
    }).join('');
    $('views').innerHTML = ['ALL', 'PR00', 'UTI', 'UMI'].map(function (v) {
      return '<button class="chip' + (st.view === v ? ' on' : '') + '" data-v="' + v + '">' + LABEL[v] + '</button>';
    }).join('');
  }
  function renderAll(keepTarget) {
    recalc(); controls(); kpis(); cond(); bars(); dbtable(); tree(); pf(); lists(); cmp(); scen();
    if (!keepTarget) $('tgt').value = (st.target * 100).toFixed(st.target * 100 === Math.round(st.target * 100) || Math.abs(st.target * 100 - D.bp_qty * 100) < 1e-6 ? (Math.abs(st.target * 100 - D.bp_qty * 100) < 1e-6 ? 2 : 1) : 1).replace('.', ',');
    $('rng').value = Math.min(8, st.target * 100);
  }

  // ---------- events
  function setTarget(v, keep) { if (isNaN(v)) return; st.target = Math.max(0, Math.min(0.15, v / 100)); renderAll(keep); }
  $('tgt').addEventListener('input', function () { setTarget(parseFloat(this.value.replace(',', '.')), true); });
  $('tgt').addEventListener('change', function () { renderAll(false); });
  $('rng').addEventListener('input', function () { setTarget(parseFloat(this.value), false); });
  $('dbsel').addEventListener('change', function () { st.db = parseInt(this.value, 10); renderAll(true); });
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-p],[data-v],[data-t],[data-h],[data-open],[data-db],[data-sl],[data-sd]'); if (!t) return;
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
    } else if (t.dataset.db !== undefined) {
      var d = parseInt(t.dataset.db, 10); st.db = st.db === d ? -1 : d; renderAll(true);
      if (st.db >= 0) window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (t.dataset.sl !== undefined) {
      var s = st.scen[parseInt(t.dataset.sl, 10)];
      st.S = JSON.parse(JSON.stringify(s.S)); st.mask = s.mask; st.target = s.target; renderAll(false);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (t.dataset.sd !== undefined) { st.scen.splice(parseInt(t.dataset.sd, 10), 1); persist(); scen(); }
  });
  document.addEventListener('change', function (e) {
    var t = e.target;
    if (t.dataset && t.dataset.bit) { var b = parseInt(t.dataset.bit, 10); if (t.checked) st.mask |= b; else st.mask &= ~b; renderAll(true); return; }
    if (t.id === 'pfl') { st.pl = parseInt(t.value, 10); pf(); return; }
    if (t.id === 'pfv') { st.valid = t.value.trim(); return; }
    if (t.id === 'pfc') { st.onlyChg = t.checked; return; }
    if (t.id === 'sul') {
      var f = t.files[0]; if (!f) return; var rd = new FileReader();
      rd.onload = function () { try { var a = JSON.parse(rd.result); if (Array.isArray(a)) { st.scen = st.scen.concat(a); persist(); scen(); } } catch (err) { alert('That file is not a scenarios file.'); } };
      rd.readAsText(f); t.value = ''; return;
    }
    if (!t.classList.contains('in')) return;
    var key = t.dataset.k; st.S[key] = st.S[key] || {};
    var v = t.value.trim();
    if (v === '') delete st.S[key][skey()]; else st.S[key][skey()] = v;
    renderAll(true);
  });
  document.addEventListener('click', function (e) {
    var id = e.target.id;
    if (id === 'pfd1') paste(); else if (id === 'pfd2') full(); else if (id === 'xlb' || id === 'xlb2') xlsxDownload();
    else if (id === 'ssave') {
      var nm = $('sname').value.trim() || ('Scenario ' + (st.scen.length + 1)), o = book(st.S, st.target, st.mask);
      st.scen.push({ name: nm, target: st.target, mask: st.mask, S: JSON.parse(JSON.stringify(st.S)), tot: { inc: o.inc, x: o.x, after: o.after } });
      $('sname').value = ''; persist(); scen();
    } else if (id === 'sdl') dlJson('ISZE_price_scenarios.json', st.scen);
  });
  $('q').addEventListener('input', function () { st.q = this.value; tree(); });
  $('reset').addEventListener('click', function () { st.S = defaults(); st.target = 0.053; st.mask = 0; st.db = -1; st.view = 'ALL'; st.q = ''; $('q').value = ''; renderAll(false); });
  $('open1').addEventListener('click', function () { D.l1.forEach(function (x, i) { st.open['l1:' + i] = true; }); tree(); });
  $('close1').addEventListener('click', function () { st.open = {}; tree(); });

  // ---------- how is this calculated (formula with the live numbers, and where it sits in the Excel file)
  function xr(s) { return '<div class="xr">In the Excel file: ' + s + '</div>'; }
  function stp(n, title, body, fm, x) {
    return '<div class="st"><div class="sn">' + n + '</div><div class="sb"><b>' + title + '</b>' + (body ? '<p>' + body + '</p>' : '') + (fm ? '<div class="fm">' + fm + '</div>' : '') + (x ? xr(x) : '') + '</div></div>';
  }
  function xnote(t) { return '<p class="xn">' + t + '</p>'; }
  function explain(key) {
    var h = '', title = '', pcnt = function (v) { return fp(v, 2); };
    var scope = (st.db >= 0 ? dbName(st.db) : 'all markets') + ', ' + LABEL[st.view].toLowerCase();
    if (key.indexOf('kpi:') === 0) {
      var w = key.slice(4), tb = T.b, bk = res.base;
      if (w === 'inc') {
        title = 'Weighted increase';
        h += stp(1, 'Extra billed divided by billed', 'Shown for ' + scope + '.', fe(T.x) + ' / ' + fe(T.b) + ' = ' + pcnt(tb ? T.x / tb : 0), 'Settings!B21 (whole book) and By L1 column F (per AIM L1)');
        h += stp(2, 'The target fixes the whole book', 'You set ' + pcnt(st.target) + '. The page scales the moves of parts left on auto until the whole book lands on it. How that scale is found is in the next panel (the line under the tiles).', '', 'Settings!B4 (target), B17 (scale)');
        h += xnote('A single market or price list can land above or below the target. Only the whole book is pinned to it.');
      } else if (w === 'scale') {
        title = 'How the scale is found';
        h += stp(1, 'Billed in the book', 'Free plus held, all price lists.', fe(bk), 'Settings!B11');
        h += stp(2, 'F: euro on fixed moves', 'Parts where you typed a setting. Billed (not held) times the fixed move.', fe(res.F), 'Settings!B12');
        h += stp(3, 'B1: euro on auto parts', 'Parts you left empty. Billed (not held) times the part\'s own BP step.', fe(res.B1), 'Settings!B13');
        h += stp(4, 'First scale s1', '(target x billed - F) / B1', '(' + pcnt(st.target) + ' x ' + fe(bk) + ' - ' + fe(res.F) + ') / ' + fe(res.B1) + ' = ' + res.s1.toFixed(4), 'Settings!B14');
        h += stp(5, 'The ceiling', 'An auto part never moves more than its own step + ' + (CEIL * 100).toFixed(0) + ' points. Parts that would, take the ceiling and are taken out of the scaling.', 'capped euro ' + fe(res.capeur) + ' | auto base left ' + fe(res.unc), 'Settings!B15 and B16');
        h += stp(6, 'Final scale s2', '(target x billed - F - capped) / auto base left', res.s2.toFixed(4), 'Settings!B17');
        h += stp(7, 'Move of an auto part', 'own step x s2, not below 0% and not above own step + ' + (CEIL * 100).toFixed(0) + ' points. Held lines pay today\'s price whatever the move.', '', 'Parts columns AE to AH');
        if (res.s2 > 1.0005) h += xnote('s2 is above 1 because held lines and holds carry nothing and the other parts make it up.');
      } else if (w === 'extra') {
        title = 'Extra billed';
        h += stp(1, 'Per part and list: free billed x move', 'Free = not held by a market condition. Held lines add nothing.', '', 'Parts column AI');
        h += stp(2, 'Added over all parts in view (' + scope + ')', '', fe(T.x), 'Settings!B20 (whole book)');
        h += xnote('Last 12 months quantities, no volume reaction assumed.');
      } else if (w === 'new') {
        title = 'New billed total';
        h += stp(1, 'Billed + extra', 'Same quantities as July 2025 to June 2026. Not a forecast.', fe(T.b) + ' + ' + fe(T.x) + ' = ' + fe(T.b + T.x), 'By L1 column C plus E');
      } else if (w === 'held') {
        title = 'Held at today\'s price';
        h += stp(1, 'Billed euro on lines a ticked condition holds', 'Conditions ticked: ' + maskText(st.mask) + '.', fe(T.h) + ' of ' + fe(T.b) + ' billed in view', 'Settings!B23; Parts columns O to R (plain numbers from the page)');
        h += xnote('The market logic (which part in which market) is not in the Excel file as formulas. The held euro per part is a number taken from the page.');
      } else if (w === 'bp') {
        title = 'BP step in yen';
        h += stp(1, 'Base price change, weighted by quantity', 'Sum of quantity x (BP after - BP before) divided by sum of quantity x BP before. Same definition as the 5.96% in the base price comparison.', 'yen ' + Math.round(T.qd).toLocaleString('nl-NL') + ' / yen ' + Math.round(T.qb).toLocaleString('nl-NL') + ' = ' + pcnt(T.qb ? T.qd / T.qb : 0), 'Settings!B26; Parts columns AR and AS');
      } else if (w === 'cost') {
        var nw = T.k0 + T.kc, od = T.k0 * D.fx / D.fx_prior;
        title = 'Purchase cost in euro';
        h += stp(1, 'Cost of last year\'s quantities', 'quantity x BP / JPY per EUR x source discount (Japan ' + D.disc.J + ', Thailand ' + D.disc.T + '), parts with a known source.', fe(T.k0) + ' at ' + String(D.fx).replace('.', ',') + ' JPY per EUR', 'Settings!B27; Parts column AP');
        h += stp(2, 'Cost step before the exchange rate', 'cost x own BP step, as a share of the cost.', fe(T.kc) + ' / ' + fe(T.k0) + ' = ' + pcnt(T.k0 ? T.kc / T.k0 : 0), 'Settings!B28; Parts column AQ');
        h += stp(3, 'Including the exchange rate', 'The old cost is taken at ' + String(D.fx_prior).replace('.', ',') + ' JPY per EUR (until 30 Sep 2026), the new at ' + String(D.fx).replace('.', ',') + '. A weaker yen lowers the euro cost.', fe(nw) + ' / ' + fe(od) + ' - 1 = ' + pcnt(costFx(T)), 'Settings!B29');
      } else if (w === 'after') {
        title = 'Extra EUR after the purchase step';
        h += stp(1, 'Extra billed on costed parts', 'Parts with a known purchase source only.', fe(T.xc), 'Settings!B30');
        h += stp(2, 'Minus the extra purchase cost', 'cost x own BP step, before the exchange rate move.', fe(T.kc), 'Parts column AQ');
        h += stp(3, 'Result', '', fe(T.xc) + ' - ' + fe(T.kc) + ' = ' + fe(T.xc - T.kc), 'Settings!B30');
      }
    } else if (key.indexOf('p:') === 0) {
      var i = pnIdx[key.slice(2)]; if (i === undefined) return;
      var p = P[i], c = p[5], cpi = M.cp[i], l3 = D.l3[p[4]], l2 = D.l2[l3[0]], rowN = 6 + i;
      title = p[0] + ' ' + p[1];
      h += stp(1, 'Own BP step', 'Base price in yen before and after.', p[6].toLocaleString('nl-NL') + ' to ' + p[7].toLocaleString('nl-NL') + ' = ' + pcnt(c) + (c < 0 ? ' (below 0%, so the part uses 0%)' : ''), 'Parts row ' + rowN + ': G, H, I, J');
      h += '<div class="st"><div class="sn">2</div><div class="sb"><b>Move per price list</b><p>The setting in force, then what it gives.</p>';
      var any = false;
      for (var k = 0; k < 4; k++) {
        var fb = res.bf[k][i], hb = res.hb[k][i]; if (fb + hb <= 0) continue; any = true;
        var inf = M.info(st.S, i, k), fx = M.parse(inf.v, cpi), mv = res.mv[k][i], f1;
        if (fx === null) {
          var raw = res.s2 * cpi, cap = cpi + CEIL;
          f1 = 'auto: ' + res.s2.toFixed(4) + ' x ' + pcnt(cpi) + ' = ' + pcnt(raw) + (raw > cap ? ', above the ceiling ' + pcnt(cap) + ', so ' + pcnt(cap) : '') + ' -> ' + pcnt(mv);
        } else f1 = 'setting ' + esc(String(inf.v)) + ' (' + esc(inf.src) + ') -> fixed ' + pcnt(fx);
        h += '<div class="fm"><b>' + LNAME[k] + '</b><br>' + f1 + '<br>billed ' + fe(fb) + ' free' + (hb ? ' + ' + fe(hb) + ' held at today\'s price' : '') + ' -> extra ' + fe(fb * mv) + '</div>';
      }
      if (!any) h += '<p class="xn">No billing on any list.</p>';
      h += xr('Parts row ' + rowN + ': setting S to V, move AE to AH, extra AI') + '</div></div>';
      for (k = 0; k < 3; k++) {
        var p0 = p[8 + k]; if (!(res.bf[k][i] + res.hb[k][i] > 0)) continue;
        h += stp(3 + k, 'New price, ' + PLN[k], 'Price now x (1 + move), rounded to the cent.', p0 > 0 ? fn(p0) + ' x (1 + ' + pcnt(res.mv[k][i]) + ') = ' + fn(Math.round(p0 * (1 + res.mv[k][i]) * 100) / 100) : 'No price on this list in the 10 Aug export.', 'Parts row ' + rowN + ': AJ to AL, AM to AO');
      }
      h += xnote('AIM group: ' + esc(D.l1[l2[0]]) + ' / ' + esc(l2[1]) + ' / ' + esc(l3[1]) + '. Find it in Excel: Parts sheet, row ' + rowN + ', or filter column A on ' + p[0] + '.');
    } else {
      var lv = key.slice(0, 2), ix = parseInt(key.slice(3), 10);
      var A = lv === 'l1' ? A1[ix] : lv === 'l2' ? A2[ix] : A3[ix];
      var nm = lv === 'l1' ? D.l1[ix] : lv === 'l2' ? D.l2[ix][1] : D.l3[ix][1];
      title = (lv === 'l1' ? 'AIM L1: ' : lv === 'l2' ? 'AIM L2: ' : 'AIM L3: ') + nm;
      var cur = settingText(key), exl = lv === 'l1' ? 'By L1 sheet, the row of ' + esc(nm) : 'Parts sheet, filter column ' + (lv === 'l2' ? 'D' : 'E') + ' on ' + esc(nm) + ', then add up AT (billed) and AI (extra)';
      h += stp(1, 'Billed and extra in view (' + scope + ')', 'Added over every part in the group.', fe(A.b) + ' billed, ' + fe(A.x) + ' extra', exl);
      h += stp(2, 'Move = extra / billed', 'What the distributors in view pay on average, including held lines.', fe(A.x) + ' / ' + fe(A.b) + ' = ' + pcnt(A.b ? A.x / A.b : 0), lv === 'l1' ? 'By L1 column F' : 'Parts: AI / AT');
      h += stp(3, 'BP step in yen, by quantity', 'The purchase side of the same parts.', pcnt(A.qb ? A.qd / A.qb : 0), lv === 'l1' ? 'By L1 column G' : 'Parts: AS / AR');
      h += stp(4, 'Setting on this group', cur !== '' ? 'You typed ' + esc(String(cur)) + ' here. It applies to every part in the group that has no setting of its own or on a lower level.' : 'None. Parts follow their own BP step scaled by s2.', '', lv === 'l1' || cur === '' ? '' : 'Parts columns S to V show the setting in force per part');
    }
    $('xt').textContent = title; $('xb').innerHTML = h; $('xp').classList.add('open');
  }
  document.addEventListener('click', function (e) {
    var f = e.target.closest('.fx'); if (f) { e.stopPropagation(); explain(f.dataset.x); return; }
    if (e.target.id === 'xc') $('xp').classList.remove('open');
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') $('xp').classList.remove('open'); });

  // ---------- Excel with formulas
  function marketsAll() {
    var a = D.dbs.map(function () { return { b: 0, h: 0, x: 0, qb: 0, qd: 0 }; });
    for (var j = 0; j < nl; j++) {
      var l = LN[j], r = P[l[0]], held = (l[6] & st.mask) !== 0, o = a[l[1]];
      o.b += l[3]; if (held) o.h += l[3]; else o.x += l[3] * res.mv[l[2]][l[0]];
      o.qb += l[4] * r[6]; o.qd += l[4] * (r[7] - r[6]);
    }
    return a.map(function (o, i) { return { name: dbName(i), b: o.b, h: o.h, x: o.x, bp: o.qb ? o.qd / o.qb : 0 }; }).sort(function (u, v) { return v.b - u.b; });
  }
  function xlsxDownload() {
    if (typeof CompressionStream === 'undefined') { alert('This needs a current Chrome or Edge to build the Excel file.'); return; }
    var btns = [$('xlb'), $('xlb2')];
    btns.forEach(function (b) { b.disabled = true; b.dataset.t = b.textContent; b.textContent = 'Building Excel...'; });
    var ctx = { D: D, S: st.S, target: st.target, ceil: CEIL, mask: st.mask, res: res, info: function (i, k) { return M.info(st.S, i, k); }, parse: M.parse, maskText: maskText(st.mask), date: new Date().toISOString().slice(0, 10), cp: M.cp, markets: marketsAll() };
    XL.build(ctx).then(function (out) {
      var a = document.createElement('a'); a.href = URL.createObjectURL(out.blob);
      a.download = 'ISZE_Price_Revision_Formulas_target_' + (st.target * 100).toFixed(1).replace('.', ',') + 'pct.xlsx'; document.body.appendChild(a); a.click(); a.remove();
    }).catch(function (err) { alert('Could not build the Excel file: ' + err.message); }).then(function () {
      btns.forEach(function (b) { b.disabled = false; b.textContent = b.dataset.t; });
    });
  }

  foot(); pfSkeleton(); renderAll(false);
  window.__sim = { st: st, res: function () { return res; }, T: function () { return T; }, BK: function () { return BK; }, book: book, priceRows: priceRows };
})();
