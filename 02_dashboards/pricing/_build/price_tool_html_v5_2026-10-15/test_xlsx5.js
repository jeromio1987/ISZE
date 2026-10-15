const fs = require('fs'), path = require('path');
const { makeModel } = require('./model5.js'); const XL = require('./xl.js'); const D = require('./payload5.json'); const sc = require('./scen5.json');
const M = makeModel(D); const P = D.parts, PMS = D.pms;
const scen = process.argv[2] || 'pms';
let S = sc.base, ph = { cat: {}, cell: {} }, mask = 32, target = 0.053;
if (scen === 'pms') { S = sc.S2; ph = sc.ph2; }
if (scen === 'pmsall') { S = sc.S2; ph = sc.ph2; mask = 63; target = 0.05; }
const res = M.run(S, target, 0.05, mask, ph);
const dbs = D.dbs.map(() => ({ b: 0, h: 0, x: 0, qb: 0, qd: 0 }));
D.lines.forEach(l => { const r = P[l[0]], held = M.isHeld(l, mask, ph), x = held ? 0 : l[3] * res.mv[l[2]][l[0]], a = dbs[l[1]]; a.b += l[3]; a.x += x; if (held) a.h += l[3]; a.qb += l[4] * r[6]; a.qd += l[4] * (r[7] - r[6]); });
const markets = dbs.map((a, i) => ({ name: D.dbs[i], b: a.b, h: a.h, x: a.x, bp: a.qb ? a.qd / a.qb : 0 })).sort((a, b) => b.b - a.b);
const ctx = { D, S, target, ceil: 0.05, mask, res, info: (i, k) => M.info(S, i, k), parse: M.parse, maskText: 'test ' + scen, date: '2026-10-15', cp: M.cp, markets,
  pms: i => { const r = P[i]; return r[13] >= 0 ? [PMS.labels[r[13]], PMS.src[r[15]], PMS.cells[r[14]][2]] : null; } };
(async () => {
  const out = await XL.build(ctx); const buf = Buffer.from(await out.blob.arrayBuffer());
  const dir = path.join(__dirname, '_xl_test'); fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'wb_' + scen + '.xlsx'), buf); fs.writeFileSync(path.join(dir, 'page_' + scen + '.json'), JSON.stringify(out.page));
  fs.writeFileSync(path.join(dir, 'spots_' + scen + '.json'), JSON.stringify([0, 1, 2, 3, 7, 50, 500, 5000, 15000].map(i => ({ i, row: 6 + i, pn: P[i][0], mv: [0, 1, 2, 3].map(k => res.mv[k][i]) }))));
  const r4 = M.run(S, 0.04, 0.05, mask, ph); let x4 = 0; D.lines.forEach(l => { if (!M.isHeld(l, mask, ph)) x4 += l[3] * r4.mv[l[2]][l[0]]; });
  fs.writeFileSync(path.join(dir, 'alt_' + scen + '.json'), JSON.stringify({ target: 0.04, extra: x4, s2: r4.s2 }));
  console.log(scen, buf.length, JSON.stringify(out.page));
})();
