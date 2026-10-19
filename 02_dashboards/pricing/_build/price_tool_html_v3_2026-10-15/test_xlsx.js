// Node test: build the workbook for a scenario with the same model the page uses, write it to disk, save the page numbers.
const fs = require('fs'), path = require('path');
const { makeModel } = require('./model3.js'); const XL = require('./xl.js'); const D = require('./payload2.json');
const M = makeModel(D);
const scen = process.argv[2] || 'holds';
const S = {}; D.pad_parts.forEach(p => S['p:' + p] = { ALL: '0' }); D.pad_l3.forEach(i => S['l3:' + i] = { ALL: '0' });
let mask = 0, target = 0.053;
if (scen === 'holds') { mask = 31; }
if (scen === 'edits') {   // settings at several levels and a list-specific one
  mask = 17; target = 0.05;
  S['l1:' + D.l1.indexOf('Brakes')] = { ALL: '2' };
  S['l2:' + 0] = { UTI: '0' };
  const i0 = 3; S['p:' + D.parts[i0][0]] = { ALL: 'BP+2', PR00: '9' };
  S['p:' + D.parts[7][0]] = { UMI: 'hold' };
}
const res = M.run(S, target, 0.05, mask);
const dbs = D.dbs.map(() => ({ b: 0, h: 0, x: 0, qb: 0, qd: 0 }));
D.lines.forEach(l => { const r = D.parts[l[0]], held = (l[6] & mask) !== 0, x = held ? 0 : l[3] * res.mv[l[2]][l[0]], a = dbs[l[1]]; a.b += l[3]; a.x += x; if (held) a.h += l[3]; a.qb += l[4] * r[6]; a.qd += l[4] * (r[7] - r[6]); });
const markets = dbs.map((a, i) => ({ name: D.dbs[i], b: a.b, h: a.h, x: a.x, bp: a.qb ? a.qd / a.qb : 0 })).sort((a, b) => b.b - a.b);
const ctx = { D, S, target, ceil: 0.05, mask, res, info: (i, k) => M.info(S, i, k), parse: M.parse, maskText: 'test ' + scen, date: '2026-10-15', cp: M.cp, markets };
(async () => {
  const t0 = Date.now();
  const out = await XL.build(ctx);
  const buf = Buffer.from(await out.blob.arrayBuffer());
  const dir = path.join(__dirname, '_xl_test'); fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'wb_' + scen + '.xlsx'), buf);
  fs.writeFileSync(path.join(dir, 'page_' + scen + '.json'), JSON.stringify(out.page));
  // spot parts for the Excel comparison: biggest, one with a list-specific setting, one with BP setting
  const spots = [0, 1, 2, 3, 7, 50, 500, 5000, 15000].map(i => ({ i, row: 6 + i, pn: D.parts[i][0], mv: [0, 1, 2, 3].map(k => res.mv[k][i]) }));
  fs.writeFileSync(path.join(dir, 'spots_' + scen + '.json'), JSON.stringify(spots));
  // what the page would show if the target were changed to 4% with the same settings: Excel must follow when B4 is typed over
  const r4 = M.run(S, 0.04, 0.05, mask); let x4 = 0; D.lines.forEach(l => { if (!(l[6] & mask)) x4 += l[3] * r4.mv[l[2]][l[0]]; });
  fs.writeFileSync(path.join(dir, 'alt_' + scen + '.json'), JSON.stringify({ target: 0.04, extra: x4, s2: r4.s2 }));
  console.log(scen, 'bytes', buf.length, 'ms', Date.now() - t0, JSON.stringify(out.page));
})();
