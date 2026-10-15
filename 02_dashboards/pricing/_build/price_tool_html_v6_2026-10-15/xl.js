// Minimal xlsx writer (zip + deflate through the browser's CompressionStream) and the workbook of the price simulator.
// No library, no network. Runs in the browser and in Node 20+ (used for the test).
var XL = (function () {
  var enc = new TextEncoder();
  var crcT = (function () { var t = new Uint32Array(256); for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(u) { var c = 0xFFFFFFFF; for (var i = 0; i < u.length; i++) c = crcT[(c ^ u[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  async function deflate(u) {
    var s = new Blob([u]).stream().pipeThrough(new CompressionStream('deflate-raw'));
    return new Uint8Array(await new Response(s).arrayBuffer());
  }
  async function zip(files) {
    var chunks = [], central = [], off = 0;
    for (var f of files) {
      var u = enc.encode(f.data), c = await deflate(u), crc = crc32(u), nm = enc.encode(f.name);
      var h = new DataView(new ArrayBuffer(30));
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0, true); h.setUint16(8, 8, true);
      h.setUint16(10, 0, true); h.setUint16(12, 0x21, true); h.setUint32(14, crc, true); h.setUint32(18, c.length, true);
      h.setUint32(22, u.length, true); h.setUint16(26, nm.length, true); h.setUint16(28, 0, true);
      chunks.push(new Uint8Array(h.buffer), nm, c);
      var d = new DataView(new ArrayBuffer(46));
      d.setUint32(0, 0x02014b50, true); d.setUint16(4, 20, true); d.setUint16(6, 20, true); d.setUint16(8, 0, true); d.setUint16(10, 8, true);
      d.setUint16(12, 0, true); d.setUint16(14, 0x21, true); d.setUint32(16, crc, true); d.setUint32(20, c.length, true);
      d.setUint32(24, u.length, true); d.setUint16(28, nm.length, true); d.setUint32(42, off, true);
      central.push(new Uint8Array(d.buffer), nm);
      off += 30 + nm.length + c.length;
    }
    var csize = 0; central.forEach(function (x) { csize += x.length; });
    var e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true);
    e.setUint32(12, csize, true); e.setUint32(16, off, true);
    return new Blob(chunks.concat(central, [new Uint8Array(e.buffer)]), { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  }
  function L(n) { var s = ''; while (n > 0) { var m = (n - 1) % 26; s = String.fromCharCode(65 + m) + s; n = Math.floor((n - 1) / 26); } return s; }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
  function sv(s) { return String(s).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, ''); }
  // style ids (see styles())
  var ST = { def: 0, head: 1, pct1: 2, int: 3, dec2: 4, inpct: 5, bold: 6, wrap: 7, pct3: 8, note: 9, dec4: 10, title: 11, pale: 12, note2: 13, indate: 14, date: 15, indec: 16 };
  function n(r, v, s) { return '<c r="' + r + '"' + (s ? ' s="' + s + '"' : '') + '><v>' + (isFinite(v) ? +(+v).toPrecision(15) : 0) + '</v></c>'; }
  function t(r, v, s) { return '<c r="' + r + '" t="inlineStr"' + (s ? ' s="' + s + '"' : '') + '><is><t xml:space="preserve">' + esc(sv(v)) + '</t></is></c>'; }
  function f(r, fm, cached, s) {
    var isStr = typeof cached === 'string';
    return '<c r="' + r + '"' + (s ? ' s="' + s + '"' : '') + (isStr ? ' t="str"' : '') + '><f>' + esc(fm) + '</f>' +
      (cached === undefined || cached === null ? '' : '<v>' + (isStr ? esc(cached) : (isFinite(cached) ? +(+cached).toPrecision(15) : 0)) + '</v>') + '</c>';
  }
  function row(r, cells, ht) { return '<row r="' + r + '"' + (ht ? ' ht="' + ht + '" customHeight="1"' : '') + '>' + cells.join('') + '</row>'; }
  function sheet(o) {
    var x = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">';
    x += '<sheetPr>' + (o.tab ? '<tabColor rgb="FF' + o.tab + '"/>' : '') + '</sheetPr>';
    x += '<sheetViews><sheetView workbookViewId="0" showGridLines="' + (o.grid === false ? 0 : 1) + '"' + (o.sel ? ' tabSelected="1"' : '') + '>';
    if (o.freeze) x += '<pane' + (o.freeze.x ? ' xSplit="' + o.freeze.x + '"' : '') + ' ySplit="' + o.freeze.y + '" topLeftCell="' + L(o.freeze.x + 1) + (o.freeze.y + 1) + '" activePane="' + (o.freeze.x ? 'bottomRight' : 'bottomLeft') + '" state="frozen"/>';
    x += '</sheetView></sheetViews><sheetFormatPr defaultRowHeight="15"/>';
    x += '<cols>' + o.widths.map(function (w, i) { return '<col min="' + (i + 1) + '" max="' + (i + 1) + '" width="' + w + '" customWidth="1"/>'; }).join('') + '</cols>';
    x += '<sheetData>' + o.rows.join('') + '</sheetData>';
    if (o.filter) x += '<autoFilter ref="' + o.filter + '"/>';
    return x + '</worksheet>';
  }
  function styles() {
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
      '<numFmts count="6"><numFmt numFmtId="164" formatCode="0.0%"/><numFmt numFmtId="165" formatCode="#,##0"/><numFmt numFmtId="166" formatCode="#,##0.00"/><numFmt numFmtId="167" formatCode="0.000%"/><numFmt numFmtId="168" formatCode="0.0000"/><numFmt numFmtId="169" formatCode="dd.mm.yyyy"/></numFmts>' +
      '<fonts count="6"><font><sz val="10"/><name val="Arial"/></font><font><b/><sz val="10"/><color rgb="FFF7F4EE"/><name val="Arial"/></font><font><b/><sz val="10"/><name val="Arial"/></font><font><sz val="10"/><color rgb="FF1A3B8A"/><name val="Arial"/></font><font><i/><sz val="9"/><color rgb="FF6B6459"/><name val="Arial"/></font><font><b/><sz val="14"/><color rgb="FF15233C"/><name val="Arial"/></font></fonts>' +
      '<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF15233C"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFEEF3F9"/></patternFill></fill></fills>' +
      '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>' +
      '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>' +
      '<cellXfs count="17">' +
      '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>' +
      '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>' +
      '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +
      '<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +
      '<xf numFmtId="166" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +
      '<xf numFmtId="164" fontId="3" fillId="3" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1"/>' +
      '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>' +
      '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>' +
      '<xf numFmtId="167" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +
      '<xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>' +
      '<xf numFmtId="168" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +
      '<xf numFmtId="0" fontId="5" fillId="0" borderId="0" xfId="0" applyFont="1"/>' +
      '<xf numFmtId="0" fontId="2" fillId="4" borderId="0" xfId="0" applyFont="1" applyFill="1"/>' +
      '<xf numFmtId="0" fontId="4" fillId="0" borderId="0" xfId="0" applyFont="1"/>' +
      '<xf numFmtId="169" fontId="3" fillId="3" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1"/>' +
      '<xf numFmtId="169" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +
      '<xf numFmtId="168" fontId="3" fillId="3" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1"/>' +
      '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>';
  }

  // ctx: { D, S, target, ceil, mask, res, info(i,k), maskText, date, partCost, cp, markets }
  async function build(ctx) {
    var D = ctx.D, P = D.parts, LN = D.lines, np = P.length, res = ctx.res, ST_ = ST;
    var R0 = 6, RL = R0 + np - 1;       // first and last data row on Parts
    var K4 = ['PR00', 'UTI', 'UMI', 'OTH'];
    // part-level sums from the lines
    var qty = new Float64Array(np), cost = new Float64Array(np);
    LN.forEach(function (l) { qty[l[0]] += l[4]; cost[l[0]] += l[5]; });
    // column map on Parts
    var C = { pn: 1, desc: 2, l1: 3, l2: 4, l3: 5, qty: 6, bp0: 7, bp1: 8, step: 9, cp: 10, fr: 11, hd: 15, st: 19, au: 23, fx: 27, mv: 31, ex: 35, pr: 36, np: 39, cost: 42, cstep: 43, yb: 44, ys: 45, bt: 46, ht: 47, src: 48 };
    function colRange(c, k) { return 'Parts!$' + L(c + (k || 0)) + '$' + R0 + ':$' + L(c + (k || 0)) + '$' + RL; }
    function sp(fn) { var s = []; for (var k = 0; k < 4; k++) s.push(fn(k)); return s.join('+'); }
    var cpR = colRange(C.cp);
    var files = [];
    // ---------------- Parts
    var heads = ['Part number', 'Description', 'AIM L1', 'AIM L2', 'AIM L3', 'Quantity, last 12 months', 'Base price before (yen)', 'Base price after (yen)', 'Own BP step', 'Own step, never below 0%',
      'Billed EUR, free: PR00', 'Billed EUR, free: UTI 1799', 'Billed EUR, free: UMI 1797', 'Billed EUR, free: other lists',
      'Billed EUR, held at today\'s price: PR00', 'Billed EUR, held: UTI 1799', 'Billed EUR, held: UMI 1797', 'Billed EUR, held: other lists',
      'SETTING PR00 (blank = auto)', 'SETTING UTI 1799', 'SETTING UMI 1797', 'SETTING other lists',
      'Auto? PR00', 'Auto? UTI', 'Auto? UMI', 'Auto? other', 'Fixed move PR00', 'Fixed move UTI', 'Fixed move UMI', 'Fixed move other',
      'MOVE PR00', 'MOVE UTI 1799', 'MOVE UMI 1797', 'MOVE other lists', 'Extra EUR (free billed x move)',
      'Price now PR00', 'Price now UTI 1799', 'Price now UMI 1797', 'NEW PRICE PR00', 'NEW PRICE UTI 1799', 'NEW PRICE UMI 1797',
      'Purchase cost EUR (quantity x FOB)', 'Purchase cost step EUR', 'Yen base (qty x BP before)', 'Yen step (qty x BP change)', 'Billed EUR total', 'Held EUR total', 'Where the setting comes from', 'PMS category', 'Made in', 'Weight band', 'Extra EUR after dealer reaction'];
    var rows = [], RE_E = ctx.react ? ctx.react.e : 0, xaTot = 0;
    rows.push(row(1, [t('A1', 'Parts: one row per part number, its setting, its move and its new price', ST_.title)]));
    rows.push(row(2, [t('A2', 'Yellow = a setting you can type on this part and list (a fraction: 0 = hold today\'s price, 0.04 = +4%; blank = auto). Everything to the right recalculates. The held euro columns are plain numbers taken from the simulator page, with these market conditions ticked: ' + ctx.maskText + '.', ST_.note2)]));
    rows.push(row(3, [t('A3', 'Own BP step = base price after / before - 1. A move is the setting if there is one, otherwise the own step scaled by Settings!B17 and capped at own step + the ceiling in Settings!B5, never below 0%.', ST_.note2)]));
    var hc = heads.map(function (h, i) { return t(L(i + 1) + '5', h, ST_.head); });
    rows.push(row(5, hc, 60));
    var pr = res.mv;
    for (var i = 0; i < np; i++) {
      var r = R0 + i, p = P[i], cells = [];
      var cpv = ctx.cp[i], stepv = p[5];
      cells.push(t('A' + r, p[0]), t('B' + r, p[1]), t('C' + r, D.l1[D.l2[D.l3[p[4]][0]][0]]), t('D' + r, D.l2[D.l3[p[4]][0]][1]), t('E' + r, D.l3[p[4]][1]));
      cells.push(n('F' + r, qty[i], ST_.int), n('G' + r, p[6], ST_.int), n('H' + r, p[7], ST_.int));
      cells.push(f('I' + r, 'IF(G' + r + '>0,H' + r + '/G' + r + '-1,0)', stepv, ST_.pct3), f('J' + r, 'MAX(0,I' + r + ')', cpv, ST_.pct3));
      var srcs = [];
      for (var k = 0; k < 4; k++) cells.push(n(L(C.fr + k) + r, res.bf[k][i], ST_.dec2));
      for (k = 0; k < 4; k++) cells.push(n(L(C.hd + k) + r, res.hb[k][i], ST_.dec2));
      var autoV = [], fxV = [];
      for (k = 0; k < 4; k++) {
        var inf = ctx.info(i, k), a = ctx.parse(inf.v, cpv), cell = L(C.st + k) + r;
        if (a === null) { cells.push('<c r="' + cell + '" s="' + ST_.inpct + '"/>'); autoV.push(1); fxV.push(0); }
        else { cells.push(n(cell, a, ST_.inpct)); autoV.push(0); fxV.push(a); srcs.push(K4[k] + ': ' + inf.src + ' = ' + inf.v); }
      }
      for (k = 0; k < 4; k++) cells.push(f(L(C.au + k) + r, 'IF(' + L(C.st + k) + r + '="",1,0)', autoV[k]));
      for (k = 0; k < 4; k++) cells.push(f(L(C.fx + k) + r, 'IF(' + L(C.st + k) + r + '="",0,' + L(C.st + k) + r + ')', fxV[k], ST_.pct3));
      for (k = 0; k < 4; k++) cells.push(f(L(C.mv + k) + r, 'IF(' + L(C.au + k) + r + '=1,MAX(0,MIN(Settings!$B$17*$J' + r + ',$J' + r + '+Settings!$B$5)),' + L(C.fx + k) + r + ')', pr[k][i], ST_.pct3));
      var ex = 0; for (k = 0; k < 4; k++) ex += res.bf[k][i] * pr[k][i];
      cells.push(f('AI' + r, sp(function (k) { return L(C.fr + k) + r + '*' + L(C.mv + k) + r; }), ex, ST_.dec2));
      for (k = 0; k < 3; k++) { var pv = p[8 + k]; cells.push(pv > 0 ? n(L(C.pr + k) + r, pv, ST_.dec2) : '<c r="' + L(C.pr + k) + r + '"/>'); }
      for (k = 0; k < 3; k++) {
        var pv2 = p[8 + k];
        cells.push(f(L(C.np + k) + r, 'IF(' + L(C.pr + k) + r + '="","",ROUND(' + L(C.pr + k) + r + '*(1+' + L(C.mv + k) + r + '),2))', pv2 > 0 ? Math.round(pv2 * (1 + pr[k][i]) * 100) / 100 : '', ST_.dec2));
      }
      cells.push(n('AP' + r, cost[i], ST_.dec2), f('AQ' + r, 'AP' + r + '*I' + r, cost[i] * stepv, ST_.dec2));
      cells.push(f('AR' + r, 'F' + r + '*G' + r, qty[i] * p[6], ST_.int), f('AS' + r, 'F' + r + '*(H' + r + '-G' + r + ')', qty[i] * (p[7] - p[6]), ST_.int));
      var bt = 0, ht = 0; for (k = 0; k < 4; k++) { bt += res.bf[k][i] + res.hb[k][i]; ht += res.hb[k][i]; }
      cells.push(f('AT' + r, 'SUM(K' + r + ':R' + r + ')', bt, ST_.dec2), f('AU' + r, 'SUM(O' + r + ':R' + r + ')', ht, ST_.dec2));
      cells.push(t('AV' + r, srcs.join('; ')));
      var pmi = ctx.pms ? ctx.pms(i) : null; if (pmi) cells.push(t('AW' + r, pmi[0]), t('AX' + r, pmi[1]), t('AY' + r, pmi[2]));
      var xaP = 0; for (k = 0; k < 4; k++) xaP += res.bf[k][i] * ((1 + pr[k][i]) * (1 + RE_E * pr[k][i]) - 1);
      xaTot += xaP;
      cells.push(f('AZ' + r, sp(function (k) { return L(C.fr + k) + r + '*((1+' + L(C.mv + k) + r + ')*(1+Settings!$B$33*' + L(C.mv + k) + r + ')-1)'; }), xaP, ST_.dec2));
      rows.push(row(r, cells));
    }
    // column letters of the extra columns used above are fixed: AI extra, AP cost, AQ cost step, AR yen base, AS yen step, AT billed, AU held
    var wP = [14, 34, 24, 22, 22, 12, 12, 12, 10, 10, 13, 13, 13, 13, 13, 13, 13, 13, 12, 12, 12, 12, 7, 7, 7, 7, 10, 10, 10, 10, 10, 10, 10, 10, 13, 11, 11, 11, 11, 11, 11, 14, 12, 14, 14, 13, 13, 46, 24, 18, 28, 16];
    files.push({ name: 'xl/worksheets/sheet3.xml', data: sheet({ widths: wP, rows: rows, freeze: { x: 2, y: 5 }, filter: 'A5:AZ' + RL, tab: 'C0552D' }) });
    var EX = 'AI', BT = 'AT', HT = 'AU', YB = 'AR', YS = 'AS', CO = 'AP', CS = 'AQ';
    function rng(col) { return 'Parts!$' + col + '$' + R0 + ':$' + col + '$' + RL; }

    // ---------------- numbers the page shows, computed from the same model (cached values and the Checks sheet)
    var tot = { b: 0, h: 0, x: 0, xc: 0, kc: 0, k0: 0, qd: 0, qb: 0 }, pmsAgg = {}, pmsx = 0, pmsb = 0, pmsh = 0, pmsn = 0, pmsys = 0, pmsyb = 0;
    for (i = 0; i < np; i++) {
      var xi = 0, bi = 0, hi = 0;
      for (k = 0; k < 4; k++) { xi += res.bf[k][i] * pr[k][i]; bi += res.bf[k][i] + res.hb[k][i]; hi += res.hb[k][i]; tot.h += res.hb[k][i]; }
      tot.b += bi; tot.x += xi;
      var pmj = ctx.pms ? ctx.pms(i) : null;
      if (pmj) {
        var pa = pmsAgg[pmj[0]] = pmsAgg[pmj[0]] || { n: 0, b: 0, h: 0, x: 0, ys: 0, yb: 0 };
        pa.n++; pa.b += bi; pa.h += hi; pa.x += xi; pa.ys += qty[i] * (P[i][7] - P[i][6]); pa.yb += qty[i] * P[i][6];
        pmsx += xi; pmsb += bi; pmsh += hi; pmsn++; pmsys += qty[i] * (P[i][7] - P[i][6]); pmsyb += qty[i] * P[i][6];
      }
      tot.qb += qty[i] * P[i][6]; tot.qd += qty[i] * (P[i][7] - P[i][6]);
      if (cost[i] > 0) { tot.k0 += cost[i]; tot.kc += cost[i] * P[i][5]; tot.xc += xi; }
    }
    var fxr = D.fx / D.fx_prior;
    var costFx = tot.k0 ? (tot.k0 + tot.kc) / (tot.k0 * fxr) - 1 : 0;
    var page = { b: tot.b, x: tot.x, inc: tot.x / tot.b, h: tot.h, s2: res.s2, bp: tot.qd / tot.qb, costFx: costFx, after: tot.xc - tot.kc, pmsx: pmsx, xa: xaTot };

    // ---------------- Settings
    var S2 = [];
    var fr = function (k) { return rng(L(C.fr + k)); };
    S2.push(row(1, [t('A1', 'Settings: the target and how the scaling is worked out', ST_.title)]));
    S2.push(row(2, [t('A2', 'Change a yellow cell and everything recalculates. Built from the simulator page on ' + ctx.date + '. A proposal on paper: nothing is published and no price list is changed.', ST_.note)], 28));
    S2.push(row(4, [t('A4', 'Target: weighted increase on last 12 months billed', ST_.bold), n('B4', ctx.target, ST_.inpct)]));
    S2.push(row(5, [t('A5', 'Ceiling above a part\'s own BP step (points)', ST_.bold), n('B5', ctx.ceil, ST_.inpct), t('C5', 'decided 30 Sep and 2 Oct 2026', ST_.note)]));
    S2.push(row(7, [t('A7', 'JPY per EUR now (from 1 Oct 2026)', ST_.bold), n('B7', D.fx, ST_.dec2)]));
    S2.push(row(8, [t('A8', 'JPY per EUR before (until 30 Sep 2026)', ST_.bold), n('B8', D.fx_prior, ST_.dec2)]));
    S2.push(row(10, [t('A10', 'How the scale is worked out', ST_.title)]));
    S2.push(row(11, [t('A11', 'Billed EUR in the book (free plus held)'), f('B11', 'SUM(' + rng('K') + ',' + rng('L') + ',' + rng('M') + ',' + rng('N') + ',' + rng('O') + ',' + rng('P') + ',' + rng('Q') + ',' + rng('R') + ')', tot.b, ST_.dec2), t('C11', 'Parts!K to R', ST_.note)]));
    S2.push(row(12, [t('A12', 'F: euro on fixed moves = billed x the fixed move'), f('B12', sp(function (k) { return 'SUMPRODUCT(' + fr(k) + ',' + rng(L(C.fx + k)) + ')'; }), res.F, ST_.dec2), t('C12', 'only free (not held) billed counts', ST_.note)]));
    S2.push(row(13, [t('A13', 'B1: euro on auto parts = billed x own step'), f('B13', sp(function (k) { return 'SUMPRODUCT(' + fr(k) + ',' + rng(L(C.au + k)) + ',' + cpR + ')'; }), res.B1, ST_.dec2)]));
    S2.push(row(14, [t('A14', 'First scale s1 = (target x billed - F) / B1'), f('B14', 'IF(B13>0,(B4*B11-B12)/B13,0)', res.s1, ST_.dec4)]));
    S2.push(row(15, [t('A15', 'Capped euro: auto parts whose scaled move would pass the ceiling'), f('B15', sp(function (k) { return 'SUMPRODUCT(' + fr(k) + '*' + rng(L(C.au + k)) + '*(' + cpR + '*$B$14>' + cpR + '+$B$5)*(' + cpR + '+$B$5))'; }), res.capeur, ST_.dec2), t('C15', 'these take own step + ceiling', ST_.note)]));
    S2.push(row(16, [t('A16', 'Auto base left to scale (not capped)'), f('B16', 'B13-(' + sp(function (k) { return 'SUMPRODUCT(' + fr(k) + '*' + rng(L(C.au + k)) + '*(' + cpR + '*$B$14>' + cpR + '+$B$5)*' + cpR + ')'; }) + ')', res.unc, ST_.dec2)]));
    S2.push(row(17, [t('A17', 'Scale s2 = (target x billed - F - capped) / auto base left'), f('B17', 'IF(B16>0,(B4*B11-B12-B15)/B16,0)', res.s2, ST_.dec4), t('C17', 'every auto part: move = s2 x own step, within 0% and own step + ceiling', ST_.note)]));
    S2.push(row(19, [t('A19', 'Result', ST_.title)]));
    S2.push(row(20, [t('A20', 'Extra billed EUR'), f('B20', 'SUM(' + rng(EX) + ')', tot.x, ST_.dec2)]));
    S2.push(row(21, [t('A21', 'Weighted increase'), f('B21', 'B20/B11', page.inc, ST_.pct3)]));
    S2.push(row(22, [t('A22', 'Status'), f('B22', 'IF(ABS(B21-B4)<0.0004,"On target","Target not reached")', Math.abs(page.inc - ctx.target) < 0.0004 ? 'On target' : 'Target not reached')]));
    S2.push(row(23, [t('A23', 'Held at today\'s price, EUR'), f('B23', 'SUM(' + rng(HT) + ')', tot.h, ST_.dec2), t('C23', 'market conditions ticked on the page: ' + ctx.maskText, ST_.note)]));
    S2.push(row(25, [t('A25', 'Purchase side', ST_.title)]));
    S2.push(row(26, [t('A26', 'BP step in yen, weighted by quantity'), f('B26', 'SUM(' + rng(YS) + ')/SUM(' + rng(YB) + ')', page.bp, ST_.pct3), t('C26', 'sum of quantity x BP change / sum of quantity x BP before', ST_.note)]));
    S2.push(row(27, [t('A27', 'Purchase cost EUR on last year\'s quantities'), f('B27', 'SUM(' + rng(CO) + ')', tot.k0, ST_.dec2), t('C27', 'BP / JPY per EUR x source discount, parts with a known source only', ST_.note)]));
    S2.push(row(28, [t('A28', 'Purchase cost step before the exchange rate'), f('B28', 'IF(B27>0,SUM(' + rng(CS) + ')/B27,0)', tot.k0 ? tot.kc / tot.k0 : 0, ST_.pct3)]));
    S2.push(row(29, [t('A29', 'Purchase cost step including the exchange rate'), f('B29', 'IF(B27>0,(B27+SUM(' + rng(CS) + '))/(B27*B7/B8)-1,0)', costFx, ST_.pct3), t('C29', 'old cost taken at the previous JPY per EUR rate', ST_.note)]));
    S2.push(row(32, [t('A32', 'Dealer reaction', ST_.title)]));
    S2.push(row(33, [t('A33', 'Response per +1% price (volume change for 1% on our price)', ST_.bold), n('B33', RE_E, ST_.indec), t('C33', ctx.react ? ctx.react.label + ': ' + ctx.react.src : '', ST_.note)]));
    S2.push(row(34, [t('A34', 'Extra billed EUR after the volume effect'), f('B34', 'SUM(' + rng('AZ') + ')', xaTot, ST_.dec2), t('C34', 'billed x (1 + move) x (1 + response x move) minus billed, as in the revision workbook', ST_.note)]));
    S2.push(row(35, [t('A35', 'Volume change'), f('B35', 'B33*B21', RE_E * (tot.x / tot.b), ST_.pct3)]));
    S2.push(row(36, [t('A36', 'Given up to the reaction EUR'), f('B36', 'B20-B34', tot.x - xaTot, ST_.dec2)]));
    S2.push(row(30, [t('A30', 'Extra EUR after the purchase step'), f('B30', 'SUMIF(' + rng(CO) + ',">0",' + rng(EX) + ')-SUM(' + rng(CS) + ')', page.after, ST_.dec2), t('C30', 'extra billed on costed parts minus the extra purchase cost', ST_.note)]));
    files.push({ name: 'xl/worksheets/sheet2.xml', data: sheet({ widths: [62, 18, 60], rows: S2.slice().sort(function (u, v) { return +u.match(/^<row r="(\d+)"/)[1] - +v.match(/^<row r="(\d+)"/)[1]; }), tab: '15233C', grid: false }) });

    // ---------------- By L1 (formulas)
    var l1rows = D.l1.map(function (nm, i) { return { nm: nm, b: 0 }; });
    for (i = 0; i < np; i++) { var q1 = D.l2[D.l3[P[i][4]][0]][0]; for (k = 0; k < 4; k++) l1rows[q1].b += res.bf[k][i] + res.hb[k][i]; }
    l1rows.sort(function (a, b) { return b.b - a.b; });
    var B1r = [];
    B1r.push(row(1, [t('A1', 'By L1: billed, extra and move per AIM L1 group', ST_.title)]));
    B1r.push(row(3, ['Parts', 'AIM L1', 'Billed EUR', 'Held EUR', 'Extra EUR', 'Move (extra / billed)', 'BP step (yen, by quantity)'].map(function (h, i) { return t(L(i + 1) + '3', h, ST_.head); }), 32));
    var rr = 4;
    l1rows.forEach(function (o) {
      if (!o.b) return;
      var ss = function (col) { return 'SUMIF(' + rng('C') + ',$B' + rr + ',' + rng(col) + ')'; };
      var ex1 = 0, ys = 0, yb = 0, ht1 = 0, cnt = 0;
      for (var j = 0; j < np; j++) if (D.l1[D.l2[D.l3[P[j][4]][0]][0]] === o.nm) { cnt++; for (var k2 = 0; k2 < 4; k2++) { ex1 += res.bf[k2][j] * pr[k2][j]; ht1 += res.hb[k2][j]; } ys += qty[j] * (P[j][7] - P[j][6]); yb += qty[j] * P[j][6]; }
      B1r.push(row(rr, [f('A' + rr, 'COUNTIF(' + rng('C') + ',$B' + rr + ')', cnt, ST_.int), t('B' + rr, o.nm), f('C' + rr, ss(BT), o.b, ST_.int), f('D' + rr, ss(HT), ht1, ST_.int), f('E' + rr, ss(EX), ex1, ST_.int), f('F' + rr, 'IF(C' + rr + '>0,E' + rr + '/C' + rr + ',0)', o.b ? ex1 / o.b : 0, ST_.pct1), f('G' + rr, 'IF(' + ss(YB) + '>0,' + ss(YS) + '/' + ss(YB) + ',0)', yb ? ys / yb : 0, ST_.pct1)]));
      rr++;
    });
    B1r.push(row(rr, [f('A' + rr, 'SUM(A4:A' + (rr - 1) + ')', np, ST_.int), t('B' + rr, 'All groups', ST_.pale), f('C' + rr, 'SUM(C4:C' + (rr - 1) + ')', tot.b, ST_.int), f('D' + rr, 'SUM(D4:D' + (rr - 1) + ')', tot.h, ST_.int), f('E' + rr, 'SUM(E4:E' + (rr - 1) + ')', tot.x, ST_.int), f('F' + rr, 'E' + rr + '/C' + rr, page.inc, ST_.pct1), f('G' + rr, 'Settings!B26', page.bp, ST_.pct1)]));
    files.push({ name: 'xl/worksheets/sheet4.xml', data: sheet({ widths: [9, 30, 15, 15, 15, 14, 14], rows: B1r, freeze: { x: 0, y: 3 } }) });

    // ---------------- By PMS category (formulas on Parts columns AW)
    var pmsL = Object.keys(pmsAgg).sort(function (a, b) { return pmsAgg[b].b - pmsAgg[a].b; }), PM = [];
    PM.push(row(1, [t('A1', 'By PMS category: the PMS part numbers, billed, extra and move', ST_.title)]));
    PM.push(row(2, [t('A2', 'PMS parts are the part numbers of this base that sit in a PMS category of the vehicle family file. Every figure is a formula on the Parts sheet (column AW is the category).', ST_.note2)]));
    PM.push(row(3, ['Parts', 'PMS category', 'Billed EUR', 'Held EUR', 'Extra EUR', 'Move (extra / billed)', 'BP step (yen, by quantity)'].map(function (h, ii) { return t(L(ii + 1) + '3', h, ST_.head); }), 32));
    var pr2 = 4;
    pmsL.forEach(function (lab) {
      var a = pmsAgg[lab], ss = function (col) { return 'SUMIF(' + rng('AW') + ',$B' + pr2 + ',' + rng(col) + ')'; };
      PM.push(row(pr2, [f('A' + pr2, 'COUNTIF(' + rng('AW') + ',$B' + pr2 + ')', a.n, ST_.int), t('B' + pr2, lab), f('C' + pr2, ss(BT), a.b, ST_.int), f('D' + pr2, ss(HT), a.h, ST_.int), f('E' + pr2, ss(EX), a.x, ST_.int), f('F' + pr2, 'IF(C' + pr2 + '>0,E' + pr2 + '/C' + pr2 + ',0)', a.b ? a.x / a.b : 0, ST_.pct1), f('G' + pr2, 'IF(' + ss(YB) + '>0,' + ss(YS) + '/' + ss(YB) + ',0)', a.yb ? a.ys / a.yb : 0, ST_.pct1)]));
      pr2++;
    });
    var pmsLast = pr2 - 1, pt = pr2, po = pr2 + 1;
    PM.push(row(pt, [f('A' + pt, 'SUM(A4:A' + pmsLast + ')', pmsn, ST_.int), t('B' + pt, 'All PMS parts', ST_.pale), f('C' + pt, 'SUM(C4:C' + pmsLast + ')', pmsb, ST_.int), f('D' + pt, 'SUM(D4:D' + pmsLast + ')', pmsh, ST_.int), f('E' + pt, 'SUM(E4:E' + pmsLast + ')', pmsx, ST_.int), f('F' + pt, 'IF(C' + pt + '>0,E' + pt + '/C' + pt + ',0)', pmsb ? pmsx / pmsb : 0, ST_.pct1), f('G' + pt, 'IF(SUMIF(' + rng('AW') + ',"<>",' + rng(YB) + ')>0,SUMIF(' + rng('AW') + ',"<>",' + rng(YS) + ')/SUMIF(' + rng('AW') + ',"<>",' + rng(YB) + '),0)', pmsyb ? pmsys / pmsyb : 0, ST_.pct1)]));
    PM.push(row(po, [f('A' + po, COUNTA_PARTS(np) + '-A' + pt, np - pmsn, ST_.int), t('B' + po, 'All other parts', ST_.pale), f('C' + po, 'Settings!B11-C' + pt, tot.b - pmsb, ST_.int), f('D' + po, 'Settings!B23-D' + pt, tot.h - pmsh, ST_.int), f('E' + po, 'Settings!B20-E' + pt, tot.x - pmsx, ST_.int), f('F' + po, 'IF(C' + po + '>0,E' + po + '/C' + po + ',0)', (tot.b - pmsb) ? (tot.x - pmsx) / (tot.b - pmsb) : 0, ST_.pct1), f('G' + po, 'IF((SUM(' + rng(YB) + ')-SUMIF(' + rng('AW') + ',"<>",' + rng(YB) + '))>0,(SUM(' + rng(YS) + ')-SUMIF(' + rng('AW') + ',"<>",' + rng(YS) + '))/(SUM(' + rng(YB) + ')-SUMIF(' + rng('AW') + ',"<>",' + rng(YB) + ')),0)', (tot.qb - pmsyb) ? (tot.qd - pmsys) / (tot.qb - pmsyb) : 0, ST_.pct1)]));
    files.push({ name: 'xl/worksheets/sheet5.xml', data: sheet({ widths: [9, 30, 15, 15, 15, 14, 14], rows: PM, freeze: { x: 0, y: 3 } }) });
    function COUNTA_PARTS(n) { return 'COUNTA(' + rng('A') + ')'; }

    // ---------------- By market (values from the page)
    var mk = ctx.markets, M4 = [];
    M4.push(row(1, [t('A1', 'By market: values from the simulator page', ST_.title)]));
    M4.push(row(2, [t('A2', 'Market is not a column on the Parts sheet (one price list serves several markets), so these are numbers from the page with the conditions ticked, not formulas. They add up to the book on the Settings sheet.', ST_.note)], 30));
    M4.push(row(4, ['Market', 'Billed EUR', 'Held at today\'s price EUR', 'Extra EUR', 'Increase', 'BP step (yen, by quantity)'].map(function (h, i) { return t(L(i + 1) + '4', h, ST_.head); }), 32));
    mk.forEach(function (m, i) {
      var r2 = 5 + i;
      M4.push(row(r2, [t('A' + r2, m.name), n('B' + r2, m.b, ST_.int), n('C' + r2, m.h, ST_.int), n('D' + r2, m.x, ST_.int), f('E' + r2, 'IF(B' + r2 + '>0,D' + r2 + '/B' + r2 + ',0)', m.b ? m.x / m.b : 0, ST_.pct1), n('F' + r2, m.bp, ST_.pct1)]));
    });
    var mlast = 4 + mk.length, mt = mlast + 1;
    M4.push(row(mt, [t('A' + mt, 'All markets', ST_.pale), f('B' + mt, 'SUM(B5:B' + mlast + ')', tot.b, ST_.int), f('C' + mt, 'SUM(C5:C' + mlast + ')', tot.h, ST_.int), f('D' + mt, 'SUM(D5:D' + mlast + ')', tot.x, ST_.int), f('E' + mt, 'D' + mt + '/B' + mt, page.inc, ST_.pct1)]));
    files.push({ name: 'xl/worksheets/sheet6.xml', data: sheet({ widths: [28, 15, 16, 15, 11, 14], rows: M4 }) });

    // ---------------- Fiscal year (formulas on the per-market extra and the monthly billing shares from the page)
    var fyM = ctx.fy ? ctx.fy.markets : [], fyN = fyM.length, FR0 = 9, FRL = FR0 + fyN - 1, FYr = [];
    var serial = function (iso) { return Math.round(Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) / 86400000) + 25569; };
    var y0 = +ctx.fy.iso.slice(0, 4), m0 = +ctx.fy.iso.slice(5, 7) - 1, d0 = +ctx.fy.iso.slice(8, 10), mR0 = FRL + 4, mRL = mR0 + 35, cm = [];
    for (var q = 0; q < 36; q++) {
      var dt = new Date(Date.UTC(y0, m0 + q, 1)), mn = dt.getUTCMonth() + 1, yr = dt.getUTCFullYear(), dim = new Date(Date.UTC(yr, mn, 0)).getUTCDate(), ww = q === 0 ? (dim - d0 + 1) / dim : 1, vv = 0;
      fyM.forEach(function (mk2) { vv += mk2.x * mk2.cal[mn - 1]; });
      cm.push({ ser: serial(dt.toISOString().slice(0, 10)), w: ww, fy: mn >= 4 ? yr + 1 : yr, v: vv * ww });
    }
    FYr.push(row(1, [t('A1', 'Fiscal year: what the extra is worth from an effective date', ST_.title)]));
    FYr.push(row(2, [t('A2', 'The extra per market and the monthly billing pattern of July 2025 to June 2026 are values from the simulator page. The dates and sums are formulas: change the yellow date. Every invoice from the date carries the new price; no early buying before it is assumed. FY2027 is 1 April 2026 to 31 March 2027. The page also shows the figures after the dealer reaction.', ST_.note2)]));
    FYr.push(row(4, [t('A4', 'Effective date', ST_.bold), n('B4', serial(ctx.fy.iso), ST_.indate), t('C4', ctx.fy.illus ? 'An example date: none is set on the page.' : 'As set on the page.', ST_.note)]));
    FYr.push(row(5, [t('A5', 'Extra EUR in FY2027 at today\'s volumes'), f('B5', 'SUMIF($C$' + mR0 + ':$C$' + mRL + ',2027,$D$' + mR0 + ':$D$' + mRL + ')', ctx.fy.vals.FY2027 || 0, ST_.dec2)]));
    FYr.push(row(6, [t('A6', 'Extra EUR in FY2028'), f('B6', 'SUMIF($C$' + mR0 + ':$C$' + mRL + ',2028,$D$' + mR0 + ':$D$' + mRL + ')', ctx.fy.vals.FY2028 || 0, ST_.dec2)]));
    FYr.push(row(7, [t('A7', 'Full year (run rate)'), f('B7', 'SUM($B$' + FR0 + ':$B$' + FRL + ')', fyM.reduce(function (s, m) { return s + m.x; }, 0), ST_.dec2)]));
    var mh = ['Market', 'Extra EUR (value from page)', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    FYr.push(row(8, mh.map(function (h, ii) { return t(L(ii + 1) + '8', h, ST_.head); }), 30));
    fyM.forEach(function (m, ii) { var r4 = FR0 + ii, cs = [t('A' + r4, m.name), n('B' + r4, m.x, ST_.int)]; m.cal.forEach(function (s, jj) { cs.push(n(L(3 + jj) + r4, s, ST_.pct1)); }); FYr.push(row(r4, cs)); });
    FYr.push(row(mR0 - 1, ['Month start', 'Share of the month counted', 'Fiscal year', 'Extra EUR'].map(function (h, ii) { return t(L(ii + 1) + (mR0 - 1), h, ST_.head); }), 30));
    cm.forEach(function (c, ii) {
      var r5 = mR0 + ii;
      FYr.push(row(r5, [f('A' + r5, 'EDATE(DATE(YEAR($B$4),MONTH($B$4),1),' + ii + ')', c.ser, ST_.date),
        ii === 0 ? f('B' + r5, '(EOMONTH($B$4,0)-$B$4+1)/DAY(EOMONTH($B$4,0))', c.w, ST_.pct1) : n('B' + r5, 1, ST_.pct1),
        f('C' + r5, 'IF(MONTH(A' + r5 + ')>=4,YEAR(A' + r5 + ')+1,YEAR(A' + r5 + '))', c.fy), f('D' + r5, 'B' + r5 + '*SUMPRODUCT($B$' + FR0 + ':$B$' + FRL + ',INDEX($C$' + FR0 + ':$N$' + FRL + ',0,MONTH(A' + r5 + ')))', c.v, ST_.dec2)]));
    });
    files.push({ name: 'xl/worksheets/sheet7.xml', data: sheet({ widths: [44, 22, 11, 11, 11, 9, 9, 9, 9, 9, 9, 9, 9, 9], rows: FYr }) });

    // ---------------- Checks
    var CK = [];
    CK.push(row(1, [t('A1', 'Checks: the simulator page against this workbook', ST_.title)]));
    CK.push(row(2, [t('A2', 'Column B is the number the page showed when this file was made. Column C is calculated here by the formulas. Every line should read OK.', ST_.note)], 28));
    CK.push(row(3, ['Figure', 'Page', 'This workbook', 'Difference', 'Result'].map(function (h, i) { return t(L(i + 1) + '3', h, ST_.head); })));
    var items = [['Billed EUR in the book', page.b, 'Settings!B11', 1, ST_.dec2], ['Extra billed EUR', page.x, 'Settings!B20', 1, ST_.dec2], ['Weighted increase', page.inc, 'Settings!B21', 0.00002, ST_.pct3],
      ['Held at today\'s price, EUR', page.h, 'Settings!B23', 1, ST_.dec2], ['Scale s2', page.s2, 'Settings!B17', 0.0001, ST_.dec4], ['BP step in yen, by quantity', page.bp, 'Settings!B26', 0.000002, ST_.pct3],
      ['Purchase cost step incl. exchange rate', page.costFx, 'Settings!B29', 0.000002, ST_.pct3], ['Extra EUR after the purchase step', page.after, 'Settings!B30', 1, ST_.dec2]];
    items.push(['Extra EUR on PMS parts', page.pmsx, '\'By PMS category\'!E' + pt, 1, ST_.dec2]);
    items.push(['Extra EUR after the dealer reaction', page.xa, 'Settings!B34', 1, ST_.dec2]);
    items.push(['Extra EUR in FY2027 from the date on the Fiscal year sheet', ctx.fy.vals.FY2027 || 0, '\'Fiscal year\'!B5', 1, ST_.dec2]);
    items.forEach(function (it, j) {
      var r3 = 4 + j;
      CK.push(row(r3, [t('A' + r3, it[0]), n('B' + r3, it[1], it[4]), f('C' + r3, it[2], it[1], it[4]), f('D' + r3, 'C' + r3 + '-B' + r3, 0, it[4]), f('E' + r3, 'IF(ABS(D' + r3 + ')<=' + it[3] + ',"OK","CHECK")', 'OK')]));
    });
    files.push({ name: 'xl/worksheets/sheet8.xml', data: sheet({ widths: [52, 18, 18, 14, 10], rows: CK, tab: '2F6B3F' }) });

    // ---------------- Read me
    var RM = [
      ['Price revision: the formulas behind the simulator page', ST_.title],
      ['Built from the simulator page on ' + ctx.date + ', with the settings you had on screen. A proposal on paper: nothing is published and no price list or SAP price is changed.', ST_.wrap],
      ['', 0],
      ['What is in it', ST_.bold],
      ['Settings: the target, the ceiling and the steps that work out the scale. Change the yellow cells.', ST_.wrap],
      ['Parts: one row per part number (' + np.toLocaleString('en') + '). Own BP step, your setting, the move, the extra euro and the new price, all as formulas you can click into.', ST_.wrap],
      ['By L1: billed, extra and move per AIM L1 group, calculated from the Parts sheet.', ST_.wrap],
      ['By market: values from the page (a price list serves several markets, so market is not a column on Parts).', ST_.wrap],
      ['By PMS category: the 484 PMS part numbers (brake pads, shoes and rotors, clutch parts, five filter types) by category, calculated from the Parts sheet, with the rest of the book underneath.', ST_.wrap],
      ['Fiscal year: what the extra is worth from an effective date, counted by month in each market (formulas; change the yellow date). Settings rows 32 to 36 hold the dealer reaction.', ST_.wrap],
      ['Checks: the page\'s numbers next to this workbook\'s. Every line should read OK.', ST_.wrap],
      ['', 0],
      ['How a move is set', ST_.bold],
      ['1. Own BP step = base price after / before - 1 in yen (the purchase side), never below 0%.', ST_.wrap],
      ['2. If you typed a setting on the part, its group or a group above it, that is the move (the part beats its PMS group, that beats its PMS category, that beats AIM L3; L3 beats L2, L2 beats L1; a price list beats all lists). 0 = hold today\'s price.', ST_.wrap],
      ['3. Otherwise the part is on auto: its own step times one scale s2, within 0% and own step + ' + (ctx.ceil * 100).toFixed(0) + ' points. s2 is worked out on Settings so the whole book lands on the target.', ST_.wrap],
      ['4. Held lines pay today\'s price. They are the market conditions ticked on the page (' + ctx.maskText + '); the euro held is a plain number on Parts, columns O to R, because the market logic is not in this workbook.', ST_.wrap],
      ['5. New price = price now x (1 + move), rounded to the cent. Price now is the PR00 price table and the Israel price lists as exported on 10 Aug 2026.', ST_.wrap],
      ['', 0],
      ['Base', ST_.bold],
      ['Billed to distributors July 2025 to June 2026, EUR ' + Math.round(tot.b).toLocaleString('en') + ' on ' + np.toLocaleString('en') + ' part numbers. Purchase cost = BP / JPY per EUR x source discount (Japan ' + D.disc.J + ', Thailand ' + D.disc.T + '). No volume reaction is assumed.', ST_.wrap]
    ];
    var rm = RM.map(function (x, i) { return row(i + 1, x[0] === '' ? [] : [t('A' + (i + 1), x[0], x[1])], x[1] === ST_.wrap ? 30 : 0); });
    files.push({ name: 'xl/worksheets/sheet1.xml', data: sheet({ widths: [130], rows: rm, grid: false, sel: true, tab: 'C0552D' }) });

    // ---------------- package parts
    var names = ['Read me', 'Settings', 'Parts', 'By L1', 'By PMS category', 'By market', 'Fiscal year', 'Checks'];
    files.push({ name: '[Content_Types].xml', data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' + [1, 2, 3, 4, 5, 6, 7, 8].map(function (i) { return '<Override PartName="/xl/worksheets/sheet' + i + '.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'; }).join('') + '</Types>' });
    files.push({ name: '_rels/.rels', data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>' });
    files.push({ name: 'xl/workbook.xml', data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><bookViews><workbookView activeTab="0"/></bookViews><sheets>' + names.map(function (nm, i) { return '<sheet name="' + nm + '" sheetId="' + (i + 1) + '" r:id="rId' + (i + 1) + '"/>'; }).join('') + '</sheets><definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="2" hidden="1">Parts!$A$5:$AZ$' + RL + '</definedName></definedNames><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>' });
    files.push({ name: 'xl/_rels/workbook.xml.rels', data: '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + [1, 2, 3, 4, 5, 6, 7, 8].map(function (i) { return '<Relationship Id="rId' + i + '" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet' + i + '.xml"/>'; }).join('') + '<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>' });
    files.push({ name: 'xl/styles.xml', data: styles() });
    var order = ['[Content_Types].xml', '_rels/.rels', 'xl/workbook.xml', 'xl/_rels/workbook.xml.rels', 'xl/styles.xml', 'xl/worksheets/sheet1.xml', 'xl/worksheets/sheet2.xml', 'xl/worksheets/sheet3.xml', 'xl/worksheets/sheet4.xml', 'xl/worksheets/sheet5.xml', 'xl/worksheets/sheet6.xml', 'xl/worksheets/sheet7.xml', 'xl/worksheets/sheet8.xml'];
    files.sort(function (a, b) { return order.indexOf(a.name) - order.indexOf(b.name); });
    var blob = await zip(files);
    return { blob: blob, page: page };
  }
  return { build: build, zip: zip };
})();
if (typeof module !== 'undefined') module.exports = XL;
