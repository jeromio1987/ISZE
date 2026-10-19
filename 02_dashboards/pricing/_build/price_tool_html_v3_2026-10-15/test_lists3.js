const { makeModel } = require('./model3.js'); const D = require('./payload2.json'); const E = require('./expected_ref.json');
const M = makeModel(D); const S = {}; D.pad_parts.forEach(p => S['p:' + p] = { ALL: '0' }); D.pad_l3.forEach(i => S['l3:' + i] = { ALL: '0' });
const o = M.run(S, 0.053, 0.05, 0); const ex = [0, 0, 0, 0];
D.lines.forEach(l => { ex[l[2]] += l[3] * o.mv[l[2]][l[0]]; });
['PR00', 'UTI', 'UMI', 'OTH'].forEach((k, i) => console.log(k, 'v2', ex[i].toFixed(2), 'excel-tool reference', E.extra[k].toFixed(2), 'diff', (ex[i] - E.extra[k]).toFixed(2)));
