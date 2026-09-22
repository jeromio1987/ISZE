'use strict';
// Synthetic boundary checks. No ISZE transaction, part, price or supplier cost.
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const E = require(process.env.AIM_ENGINE_UNDER_TEST || '../src/engine/engine.js');
const fixture = require('./fixtures/synthetic_payload.json');
const base = {price_before:100, price_after:100, quantity_before:100,
  quantity_after:100, cost_eur:60, support_eur:0, scope:'all'};
const calc = x => E.calculate({...base,...x});
const migrate = (extra={}, migration={}) => calc({kind:'migration',...extra,
  migration:{quantity_transferred:20,from:{price:100,cost:60},
    to:{price:120,cost:65},...migration}});
const approx = (got,want,tol=1e-8) => assert.ok(Number.isFinite(got) && Math.abs(got-want)<=tol,
  `got ${got}; expected ${want}`);
const refused = result => {
  assert.equal(result.ok,false,'unsupported inputs must be refused');
  assert.equal(result.resolved,false);
  assert.equal(result.gp_after,null,'no unsupported profit total');
  assert.ok(result.errors.length>0,'state the reason');
};
function both(c,opts={}) { return E.bothObjectives(c,c.alternatives[0],{payload:fixture,...opts}).result; }
function rank(c,opts={}) { return E.rankAlternatives(c,'grossProfit',{payload:fixture,...opts}).ranked; }
function variant(field,value) {
  const c=structuredClone(fixture.cases[0]);
  c.alternatives=c.alternatives.slice(0,1);
  c.alternatives[0][field]=value;
  return c;
}

for (const [label,bad] of [['text','invalid'],['NaN',NaN],['infinity',Infinity],
  ['boolean',true],['array',[]],['object',{}],['symbol',Symbol('invalid')]]) {
  test(`F01 invalid quantity ${label} is refused by both ranking entry points`,()=>{
    for (const row of rank(fixture.cases[0],{quantity_after:bad})) refused(row.result);
    refused(both(fixture.cases[0],{quantity_after:bad}));
  });
}
test('F01 valid numeric quantity string remains usable',()=>{
  const r=both(fixture.cases[0],{quantity_after:'120'});
  assert.equal(r.ok,true); approx(r.quantity_after,120);
});
for (const [label,bad] of [['text','invalid'],['boolean',true],['NaN',NaN]]) {
  test(`F01 invalid volume assumption ${label} cannot silently become unchanged volume`,()=>{
    const c=variant('volume_assumption',bad);
    rank(c).forEach(row=>refused(row.result)); refused(both(c));
  });
  test(`F01 invalid price move ${label} cannot silently become unchanged price`,()=>{
    const c=variant('price_delta_pct',bad);
    rank(c).forEach(row=>refused(row.result)); refused(both(c));
  });
}
test('F01 invalid alternative support is not defaulted to zero',()=>{
  const c=variant('support_eur',NaN);
  rank(c).forEach(row=>refused(row.result)); refused(both(c));
});
test('F01 explicit zero pack size is not defaulted to one',()=>{
  rank(fixture.cases[0],{pack_size:0}).forEach(row=>refused(row.result));
  refused(both(fixture.cases[0],{pack_size:0}));
});
test('F01 symbol and bigint numeric inputs return a refusal rather than throwing or coercing',()=>{
  refused(calc({price_after:Symbol('bad')})); refused(calc({quantity_after:123n}));
});

test('F02 incremental price rise uses the incremental profit threshold for tolerable loss',()=>{
  const r=calc({scope:'incremental',price_after:110,quantity_after:120,support_eur:500});
  // Existing contribution 4,000. Recover 500 from new units at 50: need 110 total.
  // From 120 total, lose at most 10/120 = 8.333... percent, not 25 percent.
  approx(r.qty_preserve_gp,110); approx(r.tolerable_loss_gp_pct,8.33);
  approx(r.tolerable_volume_loss_pct,8.33);
  approx(calc({scope:'incremental',price_after:110,quantity_after:110,support_eur:500}).gp_change,0);
});
test('F02 loss thresholds agree with forward calculations across 240 synthetic scenarios',()=>{
  let checked=0;
  for(const scope of ['all','incremental']) for(const p of [101,110,125,150])
    for(const support of [0,100,500,1200,3000]) for(const qty of [100,120,180,300,500,1000]) {
      const r=calc({scope,price_after:p,quantity_after:qty,support_eur:support});
      approx(r.tolerable_loss_gp_pct,E.round2(100*(1-r.qty_preserve_gp/qty)));
      const at=calc({scope,price_after:p,quantity_after:r.qty_preserve_gp,support_eur:support});
      approx(at.gp_change,0,1e-7); checked++;
    }
  assert.equal(checked,240);
});

test('F03 missing baseline cost never becomes a zero-cost migration baseline',()=>{
  refused(migrate({cost_eur:null}));
});
test('F03 transferred quantity cannot exceed the source population',()=>{
  refused(migrate({}, {quantity_transferred:101}));
});
for (const [label,change] of [
  ['negative source price',{from:{price:-100,cost:60}}],
  ['negative source cost',{from:{price:100,cost:-60}}],
  ['zero target price',{to:{price:0,cost:65}}],
  ['negative target price',{to:{price:-120,cost:65}}],
  ['negative target cost',{to:{price:120,cost:-65}}],
  ['source price differs from baseline',{from:{price:90,cost:60}}],
  ['source cost differs from baseline',{from:{price:100,cost:55}}]
]) test(`F03 migration refuses ${label}`,()=>refused(migrate({},change)));
test('F03 migration is not also an incremental-volume scenario',()=>{
  refused(migrate({scope:'incremental'})); refused(migrate({quantity_after:120}));
});
test('F03 valid one-for-one migration keeps all unchanged units and deducts support once',()=>{
  const r=migrate({support_eur:100}); assert.equal(r.ok,true);
  approx(r.revenue_before,10000); approx(r.revenue_after,10400);
  approx(r.gp_before,4000); approx(r.gp_after,4200); approx(r.gp_change,200);
  approx(r.quantity_after,100); approx(r.extra_quantity,0);
  assert.equal(r.bridge_reconciles,true);
});
test('F03 a documented zero source cost remains a value',()=>{
  const r=migrate({cost_eur:0},{from:{price:100,cost:0}});
  assert.equal(r.ok,true); approx(r.gp_after,9100);
});

function assertFiniteTree(o) {
  if(typeof o==='number') assert.ok(Number.isFinite(o),'a non-finite number escaped');
  else if(o && typeof o==='object') for(const v of Object.values(o)) assertFiniteTree(v);
}
test('F04 finite inputs whose products overflow do not return an accepted result',()=>{
  const r=calc({price_after:1e308,quantity_after:1e308}); refused(r); assertFiniteTree(r);
  assert.match(r.error,/finite|range|overflow/i);
});
test('F04 migration arithmetic also rejects numeric overflow',()=>{
  const r=migrate({}, {to:{price:1e308,cost:65}}); refused(r); assertFiniteTree(r);
});
test('F04 missing migration data cannot expose an overflowing baseline',()=>{
  const r=calc({price_before:1e308,quantity_before:1e308,kind:'migration'});
  refused(r); assertFiniteTree(r);
});
test('F05 overlapping forward cost windows remain unresolved in either source order',()=>{
  const p=structuredClone(fixture);
  const copy=structuredClone(p.meta.costBases.find(b=>b.basis_id==='FWD_B'));
  copy.basis_id='OVERLAP'; p.meta.costBases.push(copy);
  for(const bases of [p.meta.costBases,[...p.meta.costBases].reverse()]){
    const r=E.basisForDate({...p,meta:{...p.meta,costBases:bases}},'2025-10-15');
    assert.equal(r.ok,false); assert.equal(r.basis_id,null); assert.match(r.error,/overlap|ambiguous|multiple/i);
  }
});
test('F05 a single supported cost window still resolves',()=>{
  const r=E.basisForDate(fixture,'2025-10-15'); assert.equal(r.ok,true); assert.equal(r.basis_id,'FWD_B');
});
