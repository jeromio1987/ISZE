const { makeModel } = require('./model3.js'); const D = require('./payload2.json');
const M = makeModel(D); const S = {}; D.pad_parts.forEach(p => S['p:' + p] = { ALL: '0' }); D.pad_l3.forEach(i => S['l3:' + i] = { ALL: '0' });
const rotor = D.parts.findIndex(p => p[0] === '8983767550'), filt = D.parts.findIndex(p => p[0] === '8982705240'), sens = D.parts.findIndex(p => p[0] === '8978808250');
console.log('own steps: rotor', (M.cp[rotor] * 100).toFixed(2), 'oil filter element', (M.cp[filt] * 100).toFixed(2), 'PM sensor', (M.cp[sens] * 100).toFixed(2));
for (const t of [0.04, 0.05, 0.053, 0.0536, 0.0596]) {
  const t0 = process.hrtime.bigint(); const r = M.run(S, t, 0.05, 0); const ms = Number(process.hrtime.bigint() - t0) / 1e6;
  let ex = 0, capped = 0; D.lines.forEach(l => { ex += l[3] * r.mv[l[2]][l[0]]; });
  for (let i = 0; i < D.parts.length; i++) if (r.sc[0][i] && M.cp[i] > 0 && r.s2 * M.cp[i] > M.cp[i] + 0.05) capped++;
  console.log('target', (t * 100).toFixed(2) + '%', 's2', r.s2.toFixed(4), 'extra', Math.round(ex), 'rotor', (r.mv[0][rotor] * 100).toFixed(2) + '%', 'oil filter', (r.mv[0][filt] * 100).toFixed(2) + '%', 'capped PR00 parts', capped, 'model run ms', ms.toFixed(0));
}
