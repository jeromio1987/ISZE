const { makeModel } = require('./model2.js'); const D = require('./payload2.json');
const M = makeModel(D);
const S = {}; D.pad_parts.forEach(p => S['p:' + p] = { ALL: '0' }); D.pad_l3.forEach(i => S['l3:' + i] = { ALL: '0' });
function total(o) {
  let ex = 0, base = 0, held = 0;
  D.lines.forEach(l => { const h = l[6] & o.mask; base += l[3]; if (h) held += l[3]; else ex += l[3] * o.mv[l[2]][l[0]]; });
  return { ex, base, held, inc: ex / base };
}
const out = {};
for (const [name, tgt, mask] of [['noholds_5.3', 0.053, 0], ['allholds_5.3', 0.053, 31], ['service_5.0', 0.05, 1], ['lost_5.0', 0.05, 16]]) {
  const o = M.run(S, tgt, 0.05, mask); const t = total(o);
  out[name] = { extra: +t.ex.toFixed(2), held: +t.held.toFixed(2), inc: +t.inc.toFixed(6), s2: +o.s2.toFixed(6) };
}
console.log(JSON.stringify(out, null, 1));
require('fs').writeFileSync(__dirname + '/js_results.json', JSON.stringify(out));
