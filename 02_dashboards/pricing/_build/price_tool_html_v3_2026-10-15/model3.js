// Model v2: part x distributor x price list lines. Same maths as the Excel tool (mode 1: one target for the whole book),
// plus market holds: a held line pays today's price (move 0); the rest of the book is scaled to still land on the target.
var K = ['PR00', 'UTI', 'UMI', 'OTH'];
var HOLD_BITS = { service: 1, umiBody: 2, umiLight: 4, utiLight: 8, lost: 16 };
function makeModel(D) {
  var P = D.parts, LN = D.lines, np = P.length, nl = LN.length;
  var cp = new Float64Array(np), partCost = new Float64Array(np);
  // the own BP step is taken from the two yen prices, exactly as the Excel file computes it
  for (var i = 0; i < np; i++) { if (P[i][6] > 0) P[i][5] = P[i][7] / P[i][6] - 1; cp[i] = Math.max(0, P[i][5]); }
  for (var j0 = 0; j0 < nl; j0++) partCost[LN[j0][0]] += LN[j0][5];
  var byPart = [];
  for (i = 0; i < np; i++) byPart.push([]);
  for (var j = 0; j < nl; j++) byPart[LN[j][0]].push(j);

  function parse(v, cpi) {            // -> null (auto) or a fixed move
    if (v === undefined || v === null) return null;
    var s = String(v).trim().toUpperCase().replace(',', '.').replace('%', '');
    if (s === '' || s === 'S' || s === 'AUTO') return null;
    if (s === 'H' || s === 'HOLD') return 0;
    if (s.charAt(0) === 'B') {
      var rest = s.slice(2).replace('+', '').trim();
      var pts = rest === '' ? 0 : parseFloat(rest);
      return isNaN(pts) ? null : Math.max(0, cpi + pts / 100);
    }
    var x = parseFloat(s);
    return isNaN(x) ? null : x / 100;
  }
  function pick(d, k) {
    if (!d) return undefined;
    if (d[k] !== undefined && d[k] !== '') return d[k];
    if (d.ALL !== undefined && d.ALL !== '') return d.ALL;
    return undefined;
  }
  // S: settings, target (share), ceil (share), mask (hold bits on)
  function run(S, target, ceil, mask) {
    var sc = [], sm = [], mv = [], bf = [], hb = [];
    for (var k = 0; k < 4; k++) {
      sc.push(new Uint8Array(np)); sm.push(new Float64Array(np)); mv.push(new Float64Array(np));
      bf.push(new Float64Array(np)); hb.push(new Float64Array(np));
    }
    var base = 0;
    for (j = 0; j < nl; j++) {
      var l = LN[j];
      base += l[3];
      if (l[6] & mask) hb[l[2]][l[0]] += l[3]; else bf[l[2]][l[0]] += l[3];
    }
    var F = 0, B1 = 0;
    for (i = 0; i < np; i++) {
      var r = P[i], chain = [S['p:' + r[0]], S['l3:' + r[4]], S['l2:' + r[3]], S['l1:' + r[2]]];
      for (k = 0; k < 4; k++) {
        var v;
        for (var q = 0; q < 4 && v === undefined; q++) v = pick(chain[q], K[k]);
        var p = parse(v, cp[i]); v = undefined;
        if (p === null) sc[k][i] = 1; else sm[k][i] = p;
        var b = bf[k][i];
        if (sc[k][i]) B1 += b * cp[i]; else F += b * sm[k][i];
      }
    }
    var s1 = B1 > 0 ? (target * base - F) / B1 : 0, capeur = 0, unc = B1;
    for (i = 0; i < np; i++) for (k = 0; k < 4; k++) if (sc[k][i] && cp[i] * s1 > cp[i] + ceil) {
      capeur += bf[k][i] * (cp[i] + ceil); unc -= bf[k][i] * cp[i];
    }
    var s2 = unc > 0 ? (target * base - F - capeur) / unc : 0;
    for (i = 0; i < np; i++) for (k = 0; k < 4; k++)
      mv[k][i] = sc[k][i] ? Math.max(0, Math.min(s2 * cp[i], cp[i] + ceil)) : sm[k][i];
    return { mv: mv, sc: sc, sm: sm, bf: bf, hb: hb, s1: s1, s2: s2, F: F, B1: B1, capeur: capeur, unc: unc, base: base, mask: mask, target: target, ceil: ceil };
  }
  // which setting is in force for a part on a list: raw text and the level it came from
  function info(S, i, k) {
    var r = P[i], chain = [[S['p:' + r[0]], 'part'], [S['l3:' + r[4]], 'L3 ' + D.l3[r[4]][1]], [S['l2:' + r[3]], 'L2 ' + D.l2[r[3]][1]], [S['l1:' + r[2]], 'L1 ' + D.l1[r[2]]]];
    for (var q = 0; q < 4; q++) { var v = pick(chain[q][0], K[k]); if (v !== undefined) return { v: v, src: chain[q][1] }; }
    return { v: undefined, src: '' };
  }
  return { run: run, parse: parse, info: info, cp: cp, partCost: partCost, np: np, nl: nl, byPart: byPart };
}
if (typeof module !== 'undefined') module.exports = { makeModel: makeModel, K: K, HOLD_BITS: HOLD_BITS };
