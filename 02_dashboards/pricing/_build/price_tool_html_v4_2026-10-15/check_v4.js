const fs = require('fs'); const { makeModel } = require('./model4.js'); const D = require('./payload4.json');
const M = makeModel(D);
const S = {}; D.pad_parts.forEach(p => S['p:' + p] = { ALL: '0' }); D.pad_l3.forEach(i => S['l3:' + i] = { ALL: '0' });
const st = D.l3.findIndex(t => t[1] === 'Steering Unit'); S['l3:' + st] = { ALL: '5' };
const out = {};
for (const [name, mask, target] of [['start_5.3', 32, 0.053], ['start_nomask_5.3', 0, 0.053], ['start_all_5.0', 63, 0.05]]) {
  const r = M.run(S, target, 0.05, mask); let x = 0, held = 0, xs = 0, xf = 0;
  D.lines.forEach(l => { const h = (l[6] & mask) !== 0, e = h ? 0 : l[3] * r.mv[l[2]][l[0]]; x += e; if (h) held += l[3]; if (D.parts[l[0]][4] === st) xs += e; if (l[6] & 32) xf += l[3]; });
  out[name] = { extra: +x.toFixed(2), held: +held.toFixed(2), steer: +xs.toFixed(2), s2: +r.s2.toFixed(6) };
}
console.log(JSON.stringify(out, null, 1)); fs.writeFileSync(__dirname + '/js4.json', JSON.stringify(out));
