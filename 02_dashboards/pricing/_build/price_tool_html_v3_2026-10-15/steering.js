const { makeModel } = require('./model3.js'); const D = require('./payload2.json');
const M = makeModel(D); const base = {}; D.pad_parts.forEach(p => base['p:' + p] = { ALL: '0' }); D.pad_l3.forEach(i => base['l3:' + i] = { ALL: '0' });
const bill = new Float64Array(D.parts.length); D.lines.forEach(l => bill[l[0]] += l[3]);
const l3 = D.l3.map((t, i) => [i, t[1], D.l2[t[0]][1], D.l1[D.l2[t[0]][0]]]).filter(t => /Steering Unit/i.test(t[1]));
console.log('L3 groups called Steering Unit:', JSON.stringify(l3));
const idx = l3.map(t => t[0]);
const ps = D.parts.map((p, i) => ({ i, pn: p[0], d: p[1], l3: p[4], b: bill[i], c: M.cp[i], bp0: p[6], bp1: p[7] })).filter(p => idx.includes(p.l3)).sort((a, b) => b.b - a.b);
let tb = 0, tx0 = 0, z = 0, zb = 0; const r0 = M.run(base, 0.053, 0.05, 0);
ps.forEach(p => { tb += p.b; let x = 0; M.byPart[p.i].forEach(j => { const l = D.lines[j]; x += l[3] * r0.mv[l[2]][l[0]]; }); tx0 += x; if (p.c === 0) { z++; zb += p.b; } });
console.log('steering unit parts', ps.length, 'billed', Math.round(tb), 'extra at 5.3% now', Math.round(tx0), '= ' + (100 * tx0 / tb).toFixed(2) + '%', '| parts with own step 0%:', z, 'billed', Math.round(zb));
ps.slice(0, 8).forEach(p => console.log('  ', p.pn, p.d, 'billed', Math.round(p.b), 'BP yen', p.bp0, '->', p.bp1, 'own step', (p.c * 100).toFixed(2) + '%'));
for (const setv of ['5', '7']) {
  const S = JSON.parse(JSON.stringify(base)); idx.forEach(i => S['l3:' + i] = { ALL: setv });
  const r = M.run(S, 0.053, 0.05, 0); let x = 0, xs = 0; D.lines.forEach(l => { const e = l[3] * r.mv[l[2]][l[0]]; x += e; if (idx.includes(D.parts[l[0]][4])) xs += e; });
  console.log('steering units fixed at +' + setv + '%: extra on steering units', Math.round(xs), 'whole book', Math.round(x), 'scale for everything else', r.s2.toFixed(4), '(was ' + r0.s2.toFixed(4) + ')');
}
