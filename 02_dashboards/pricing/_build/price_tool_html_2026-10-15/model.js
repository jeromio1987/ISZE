// Model: same maths as the Excel tool (build_price_by_aim_level.py, mode 1 = one target for the whole book).
var K = ['PR00', 'UTI', 'UMI', 'OTH'];
function makeModel(D) {
  var R = D.rows, n = R.length;
  var cp = new Float64Array(n);
  for (var i = 0; i < n; i++) cp[i] = Math.max(0, R[i][9]);
  function parse(v, cpi) {            // -> null (auto) or a fixed move
    if (v === undefined || v === null) return null;
    var s = String(v).trim().toUpperCase().replace(',', '.').replace('%', '');
    if (s === '' || s === 'S' || s === 'AUTO') return null;
    if (s === 'H' || s === 'HOLD') return 0;
    if (s.charAt(0) === 'B') {        // BP = this part's own base price step, BP+2 = plus 2 points
      var rest = s.slice(2).replace('+', '').trim();
      var pts = rest === '' ? 0 : parseFloat(rest);
      return isNaN(pts) ? null : Math.max(0, cpi + pts / 100);
    }
    var x = parseFloat(s);
    return isNaN(x) ? null : x / 100;
  }
  function pick(d, k) {               // list-specific setting beats "all lists"
    if (!d) return undefined;
    if (d[k] !== undefined && d[k] !== '') return d[k];
    if (d.ALL !== undefined && d.ALL !== '') return d.ALL;
    return undefined;
  }
  function run(S, target, ceil) {
    var sc = [], sm = [], mv = [];
    for (var k = 0; k < 4; k++) { sc.push(new Uint8Array(n)); sm.push(new Float64Array(n)); mv.push(new Float64Array(n)); }
    var l2of = D.l3.map(function (t) { return t[0]; });
    var l1of = D.l2.map(function (t) { return t[0]; });
    for (var i = 0; i < n; i++) {
      var r = R[i], a3 = r[4], a2 = r[3], a1 = r[2];
      var chain = [S['p:' + r[0]], S['l3:' + a3], S['l2:' + a2], S['l1:' + a1]];
      for (k = 0; k < 4; k++) {
        var v;
        for (var j = 0; j < 4 && v === undefined; j++) v = pick(chain[j], K[k]);
        var p = parse(v, cp[i]); v = undefined;
        if (p === null) sc[k][i] = 1; else sm[k][i] = p;
      }
    }
    var base = 0, F = 0, B1 = 0;
    for (i = 0; i < n; i++) for (k = 0; k < 4; k++) {
      var b = R[i][5 + k]; base += b;
      if (sc[k][i]) B1 += b * cp[i]; else F += b * sm[k][i];
    }
    var s1 = B1 > 0 ? (target * base - F) / B1 : 0, capeur = 0, unc = B1;
    for (i = 0; i < n; i++) for (k = 0; k < 4; k++) if (sc[k][i] && cp[i] * s1 > cp[i] + ceil) {
      var bb = R[i][5 + k]; capeur += bb * (cp[i] + ceil); unc -= bb * cp[i];
    }
    var s2 = unc > 0 ? (target * base - F - capeur) / unc : 0;
    for (i = 0; i < n; i++) for (k = 0; k < 4; k++)
      mv[k][i] = sc[k][i] ? Math.max(0, Math.min(s2 * cp[i], cp[i] + ceil)) : sm[k][i];
    return { mv: mv, sc: sc, s2: s2, base: base };
  }
  return { run: run, parse: parse, cp: cp, n: n };
}
if (typeof module !== 'undefined') module.exports = { makeModel: makeModel, K: K };
