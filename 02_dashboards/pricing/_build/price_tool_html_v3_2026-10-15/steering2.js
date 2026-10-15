const { makeModel } = require('./model3.js'); const D = require('./payload2.json'); const far = require('./far_flags.json');
const farSet = new Set(far.map(a => a[0] + ':' + a[1]));
D.lines.forEach(l => { if (farSet.has(l[0] + ':' + l[1])) l[6] |= 32; });
const M = makeModel(D);
const base = {}; D.pad_parts.forEach(p => base['p:' + p] = { ALL: '0' }); D.pad_l3.forEach(i => base['l3:' + i] = { ALL: '0' });
const st = D.l3.findIndex(t => t[1] === 'Steering Unit');
const withSteer = JSON.parse(JSON.stringify(base)); withSteer['l3:' + st] = { ALL: '5' };
const farParts = new Set(far.map(a => a[0]));
function show(name, S, mask) {
  const r = M.run(S, 0.053, 0.05, mask); let tot = 0, xs = 0, xf = 0, bf = 0, held = 0;
  D.lines.forEach(l => { const hd = (l[6] & mask) !== 0, e = hd ? 0 : l[3] * r.mv[l[2]][l[0]]; tot += e; if (hd) held += l[3]; if (D.parts[l[0]][4] === st) xs += e; if (farParts.has(l[0])) { xf += e; bf += l[3]; } });
  const rot = D.parts.findIndex(p => p[0] === '8982705240');
  console.log(name.padEnd(46), 'book', Math.round(tot), '| steering units extra', Math.round(xs), '| 20 KS-far parts extra', Math.round(xf), 'of', Math.round(bf), 'billed | held', Math.round(held), '| scale', r.s2.toFixed(4), '| oil filter element', (r.mv[0][rot] * 100).toFixed(2) + '%');
}
show('now (pad kits held only)', base, 0);
show('steering units +5%', withSteer, 0);
show('hold the 20 KS-far parts only', base, 32);
show('steering units +5% and hold the 20 KS-far parts', withSteer, 32);
const names = D.parts.map((p, i) => [p[0], p[1], i]).filter(x => farParts.has(x[2]));
const bill = new Float64Array(D.parts.length); D.lines.forEach(l => bill[l[0]] += l[3]);
names.sort((a, b) => bill[b[2]] - bill[a[2]]).slice(0, 6).forEach(x => console.log('  ', x[0], x[1], Math.round(bill[x[2]])));
