const fs = require('fs'); const { makeModel } = require('./model5.js'); const D = require('./payload5.json');
const M = makeModel(D);
const cats = D.pms.cats, cix = c => cats.indexOf(c);
const base = {}; D.pad_parts.forEach(p => base['p:' + p] = { ALL: '0' }); D.pad_l3.forEach(i => base['l3:' + i] = { ALL: '0' });
const st = D.l3.findIndex(t => t[1] === 'Steering Unit'); base['l3:' + st] = { ALL: '5' };
// scenario "pms": category holds, a cell hold, settings at category, cell and part level
const S2 = JSON.parse(JSON.stringify(base));
S2['c:' + cix('blower_filter')] = { ALL: '3' };
const cellOilT = D.pms.cells.findIndex(c => c[0] === cix('oil_filter') && c[1] === 'T'); S2['f:' + cellOilT] = { ALL: 'BP+1' };
const cellAirJ = D.pms.cells.findIndex(c => c[0] === cix('air_filter') && c[1] === 'J'); S2['f:' + cellAirJ] = { PR00: '2' };
const partX = D.parts.findIndex(p => p[13] === cix('fuel_filter')); S2['p:' + D.parts[partX][0]] = { ALL: '0' };
const ph2 = { cat: {}, cell: {} }; ph2.cat[cix('oil_filter')] = 1; ph2.cat[cix('fuel_filter')] = 1; ph2.cat[cix('air_filter')] = 1;
const dbIUK = D.dbs.indexOf('IUK'); ph2.cell[dbIUK * cats.length + cix('brake_rotor')] = 1;
const scen = { start: [base, 32, 0.053, { cat: {}, cell: {} }], pms: [S2, 32, 0.053, ph2], pms_nomask: [S2, 0, 0.05, ph2] };
const out = {};
for (const [name, [S, mask, target, ph]] of Object.entries(scen)) {
  const r = M.run(S, target, 0.05, mask, ph); let x = 0, held = 0, xp = 0, bp = 0;
  D.lines.forEach(l => { const h = M.isHeld(l, mask, ph), e = h ? 0 : l[3] * r.mv[l[2]][l[0]]; x += e; if (h) held += l[3]; if (D.parts[l[0]][13] >= 0) { xp += e; bp += l[3]; } });
  out[name] = { extra: +x.toFixed(2), held: +held.toFixed(2), pms_extra: +xp.toFixed(2), pms_billed: +bp.toFixed(2), s2: +r.s2.toFixed(6) };
}
console.log(JSON.stringify(out, null, 1)); fs.writeFileSync(__dirname + '/js5.json', JSON.stringify(out));
fs.writeFileSync(__dirname + '/scen5.json', JSON.stringify({ S2: S2, ph2: ph2, base: base }));
