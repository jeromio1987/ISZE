#!/usr/bin/env node
'use strict';
/* ===========================================================================
   Range economics - the prototype's own 87 checks, run in this component.

   PROVENANCE
   ----------
   Ported from AIM_RANGE_DECISION_PROTOTYPE_2026-09-22 (tests/range.test.cjs,
   sha256 380a097df43676b6702f0efa4e8f6ea0fc56bf2c2a188af4a50c9414ccd5584d),
   which shipped with src/engine/range.js. The engine is byte-identical to the
   prototype's copy (sha256 f9c9d7466510ef4f1d1e0d93159b354202eb71c93395fed9d0792f6790edbd31,
   re-measured here rather than copied from the prototype's evidence file).

   WHAT CHANGED IN THE PORT
   ------------------------
   Only the fixture path. The prototype required
   ../examples/synthetic_scenarios.json; here the same file lives at
   tests/fixtures/range_synthetic_scenarios.json, because the component keeps
   its fixtures under tests/ and does not grow an examples/ folder for one
   module. No assertion, expectation or tolerance was changed, weakened or
   deleted. Two of the checks carry the prototype's own invariant exercises (400
   deterministic direct-sum cases and 240 bounded break-even cases) inside the
   named tests; those are exercises, not extra tests, and are not counted.

   The fixtures are synthetic and were checked for identifying content before
   being brought across: no payload part number and no seller name appears in
   them. See the restricted-value sweep, not this header, for the evidence.

   Run:  node --test tests/range_engine.test.cjs
   Exit code is non-zero when any check fails.
   =========================================================================== */
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const E = require('../src/engine/range.js');
const scenarios = require('./fixtures/range_synthetic_scenarios.json');
const clone = x => structuredClone(x);
const sample = () => clone(scenarios[0]);
function refused(input, code) {
  const r = E.evaluateRange(input);
  assert.equal(r.ok, false, JSON.stringify(r));
  assert.equal(r.error.code, code);
  assert.equal(r.proposal, null);
  assert.equal(r.change, null);
  return r;
}
const expected = [[0,0],[-10000,-10000],[21000,6000],[1000,-2000],[-250,2750]];
for (let i=0;i<scenarios.length;i++) {
  test('synthetic case '+(i+1)+' direct revenue and profit', () => {
    const r=E.evaluateRange(scenarios[i]); assert.equal(r.ok,true);
    assert.equal(r.baseline.revenue_eur,112000); assert.equal(r.baseline.gross_profit_eur,45000);
    assert.equal(r.change.revenue_eur,expected[i][0]); assert.equal(r.change.gross_profit_eur,expected[i][1]);
    assert.equal(r.proposal.gross_profit_eur,r.proposal.revenue_eur-r.proposal.parts_cost_eur-r.proposal.support_eur);
    assert.equal(r.approval,'not_evaluated'); assert.equal(r.price_causality,'not_established');
  });
  test('synthetic case '+(i+1)+' exact bridges and conserved quantities', () => {
    const r=E.evaluateRange(scenarios[i]);
    for (const [key,target] of [['profit_bridge','gross_profit_eur'],['revenue_bridge','revenue_eur']]) {
      const values=Object.entries(r[key]).filter(([k])=>k.endsWith('_eur')).map(([,v])=>Math.round(v*100));
      assert.equal(values.reduce((a,b)=>a+b,0),Math.round(r.change[target]*100));
      assert.equal(r[key].reconciles_exactly_in_cents,true);
    }
    const q=r.quantity_check; assert.equal(q.scenario-q.baseline,q.assumed_recovered-q.assumed_lost);
    assert.equal(q.transfers_are_new_business,false);
  });
}
test('identical BVP total distinguishes recovery from displacement',()=>{
  const a=E.evaluateRange(scenarios[2]), b=E.evaluateRange(scenarios[3]);
  assert.equal(a.lines[1].scenario_quantity,600); assert.equal(b.lines[1].scenario_quantity,600);
  assert.equal(a.change.gross_profit_eur-b.change.gross_profit_eur,8000);
  assert.equal(b.profit_bridge.internal_transfer_effect_eur,-4000);
});
test('support is counted once at range level and margins reconcile',()=>{
  const x=sample();x.support_eur=123.45;const r=E.evaluateRange(x);
  assert.equal(r.change.gross_profit_eur,-123.45);
  assert.equal(r.profit_bridge.support_effect_eur,-123.45);
  assert.equal(r.proposal.gross_margin_pct,100*r.proposal.gross_profit_eur/r.proposal.revenue_eur);
  assert.equal(r.lines.reduce((a,l)=>a+l.scenario_contribution_before_support_eur,0)-r.proposal.support_eur,r.proposal.gross_profit_eur);
});
test('exact cents do not manufacture a rounding residual',()=>{
  const x=sample();x.lines.forEach(l=>Object.assign(l,{baseline_net_price_eur:0.29,scenario_net_price_eur:0.31,unit_cost_eur:0.11}));
  const r=E.evaluateRange(x);assert.equal(r.ok,true);assert.equal(r.change.gross_profit_eur,24);
});
test('historical fleet rates have a dated non-forecast basis',()=>{
  const r=E.evaluateRange(scenarios[3]);assert.equal(r.historical_fleet_context.scenario_profit_change_per_historical_vehicle_eur,-2);
  assert.equal(r.historical_fleet_context.as_of,'2025-12-31');assert.equal(r.historical_fleet_context.is_scenario_fleet_forecast,false);
});
test('zero cost is known; missing cost is not zero',()=>{
  const x=sample();x.lines[0].unit_cost_eur=0;assert.equal(E.evaluateRange(x).ok,true);
  delete x.lines[0].unit_cost_eur;refused(x,'MISSING_INPUT');
});
test('full withdrawal has zero revenue and no fabricated margin',()=>{
  const x=sample();x.lines.forEach(l=>l.lost_quantity=l.baseline_quantity);
  const r=E.evaluateRange(x);assert.equal(r.ok,true);assert.equal(r.proposal.revenue_eur,0);assert.equal(r.proposal.gross_margin_pct,null);
});
for (const [label,value] of [['null',null],['blank',''],['numeric string','90'],['NaN',NaN],['Infinity',Infinity],
  ['negative',-1],['three decimals',1.001],['boolean',true],['array',[]],['object',{}],['BigInt',2n],['Symbol',Symbol('x')]]) {
  test('refuse invalid money: '+label,()=>{const x=sample();x.lines[0].unit_cost_eur=value;refused(x,'INVALID_MONEY');});
}
for (const [label,value] of [['null',null],['string','100'],['NaN',NaN],['fractional',1.5],['negative',-1],['unsafe',Number.MAX_SAFE_INTEGER+1]]) {
  test('refuse invalid quantity: '+label,()=>{const x=sample();x.lines[0].recovered_quantity=value;refused(x,'INVALID_QUANTITY');});
}
test('scope cannot silently turn an incremental offer into an all-volume cut',()=>{
  const x=sample();x.scope='incremental';refused(x,'UNSUPPORTED_SCOPE');
});
test('unexpected inputs are refused rather than ignored',()=>{
  const x=sample();x.lines[0].recovery_rate=0.2;refused(x,'UNSUPPORTED_INPUT');
});
test('support must be explicit and nonnegative',()=>{
  const x=sample();delete x.support_eur;refused(x,'MISSING_INPUT');x.support_eur=-1;refused(x,'INVALID_MONEY');
});
test('invalid top-level shapes do not produce calculations',()=>{
  for (const x of [null,undefined,[],1,'test']) refused(x,'INVALID_OBJECT');
});
test('unsupported version is refused',()=>{const x=sample();x.schema_version=2;refused(x,'VERSION');});
test('same part number cannot be duplicated',()=>{const x=sample();x.lines[1].id=x.lines[0].id;refused(x,'DUPLICATE_LINE');});
test('one service family does not imply interchangeable kit quantities',()=>{const x=sample();x.lines[1].unit_basis='kit of two';refused(x,'MIXED_UNITS');});
test('whole packs are enforced without silently rounding an assumption',()=>{const x=sample();x.lines[1].recovered_quantity=21;refused(x,'PACK_MISMATCH');});
test('zero pack size is refused',()=>{const x=sample();x.lines[1].pack_size=0;refused(x,'INVALID_QUANTITY');});
test('missing equivalence documentation blocks transfer arithmetic',()=>{
  const x=clone(scenarios[3]);x.transfers[0].equivalence_basis='same_description';refused(x,'EQUIVALENCE_REQUIRED');
  x.transfers[0].equivalence_basis='documented_one_for_one_service_unit';x.transfers[0].equivalence_ref='';refused(x,'INVALID_TEXT');
});
test('transfers cannot refer to unknown or identical lines',()=>{
  const x=clone(scenarios[3]);x.transfers[0].to_line_id='unknown';refused(x,'INVALID_TRANSFER');
  x.transfers[0].to_line_id=x.transfers[0].from_line_id;refused(x,'INVALID_TRANSFER');
});
test('duplicate transfer cannot double-count a movement',()=>{
  const x=clone(scenarios[3]);x.transfers.push(clone(x.transfers[0]));refused(x,'DUPLICATE_TRANSFER');
});
test('losses and transfers share one bounded starting population',()=>{
  const x=clone(scenarios[3]);x.lines[0].lost_quantity=810;refused(x,'SOURCE_VOLUME_EXCEEDED');
});
test('recovered units cannot fund transfers beyond the starting population',()=>{
  const x=clone(scenarios[3]);x.lines[0].recovered_quantity=1000;x.transfers[0].quantity=1100;refused(x,'SOURCE_VOLUME_EXCEEDED');
});
test('transfer cycles are refused',()=>{
  const x=clone(scenarios[3]);x.transfers.push({...x.transfers[0],from_line_id:'SYN-OIL-B',to_line_id:'SYN-OIL-G',quantity:10});refused(x,'TRANSFER_CHAIN');
});
test('branching transfers work and conserve units across three products',()=>{
  const x=clone(scenarios[3]);x.lines.push({...x.lines[1],id:'SYN-OIL-B2',recovered_quantity:0});
  x.transfers.push({...x.transfers[0],to_line_id:'SYN-OIL-B2',quantity:100});
  const r=E.evaluateRange(x);assert.equal(r.ok,true);assert.equal(r.quantity_check.internally_transferred,300);
  assert.equal(r.quantity_check.scenario-r.quantity_check.baseline,200);
});
for (const id of ['UK','United Kingdom','Israel']) test('country is not a distributor: '+id,()=>{
  const x=sample();x.context.distributor_id=id;refused(x,'AMBIGUOUS_DISTRIBUTOR');
});
test('half year cannot be replayed as a whole year',()=>{
  const x=sample();x.context.reference_period={from:'2026-01-01',to:'2026-06-30'};refused(x,'PERIOD_LENGTH_MISMATCH');
});
test('equal-length partial periods are allowed when explicit',()=>{
  const x=sample();x.context.reference_period={from:'2025-01-01',to:'2025-03-31'};
  x.context.scenario_period={from:'2027-01-01',to:'2027-03-31'};assert.equal(E.evaluateRange(x).ok,true);
});
test('impossible and reversed dates are refused',()=>{
  const x=sample();x.context.reference_period.from='2025-02-30';refused(x,'INVALID_DATE');
  x.context.reference_period={from:'2025-03-01',to:'2025-02-01'};refused(x,'INVALID_PERIOD');
});
test('future reference data is not historical',()=>{
  const x=sample();x.context.as_of='2024-12-31';refused(x,'FUTURE_REFERENCE');
});
test('cost windows must cover the entire scenario',()=>{
  const x=sample();x.context.cost_basis.valid_to='2027-03-31';refused(x,'COST_PERIOD_UNCOVERED');
});
test('fleet forecast is not allowed as historical context',()=>{
  const x=sample();x.context.fleet.basis='forecast';refused(x,'FLEET_BASIS');
});
test('retail or another currency is not an ISZE net selling price',()=>{
  const x=sample();x.context.price_basis='dealer_retail';refused(x,'PRICE_BASIS');
});
test('oversized arithmetic is refused, not serialized as null profit',()=>{
  const x=sample();x.lines[0].baseline_quantity=1000000000;x.lines[0].baseline_net_price_eur=1000000000;
  refused(x,'ARITHMETIC_RANGE');
});
test('all baseline quantities zero do not create an observed comparison',()=>{
  const x=sample();x.lines.forEach(l=>l.baseline_quantity=0);refused(x,'NO_BASELINE');
});
test('revenue and profit rankings use different explicit objectives',()=>{
  const rev=E.compareRanges(scenarios,'revenue'), gp=E.compareRanges(scenarios,'gross_profit');
  assert.equal(rev.ok,true);assert.equal(gp.ok,true);
  assert.deepEqual(rev.rows.map(x=>x.scenario_id),['03_bvp_recovery','04_bvp_transfer','01_hold','05_genuine_increase','02_genuine_cut']);
  assert.deepEqual(gp.rows.map(x=>x.scenario_id),['03_bvp_recovery','05_genuine_increase','01_hold','04_bvp_transfer','02_genuine_cut']);
  assert.equal(gp.recommended_scenario_id,null);
});
test('an unselected objective does not become a score',()=>{assert.equal(E.compareRanges(scenarios).error.code,'OBJECTIVE');});
for (const [name,mutate] of [
  ['distributor',x=>x.context.distributor_id='OTHER-DISTRIBUTOR'],
  ['starting quantity',x=>x.lines[0].baseline_quantity+=10],
  ['starting price',x=>x.lines[0].baseline_net_price_eur+=1],
  ['parts cost',x=>x.lines[0].unit_cost_eur+=1],
  ['cost source',x=>x.context.cost_basis.id='ANOTHER-COST-BASIS'],
  ['fleet context',x=>x.context.fleet.vehicles+=1],
]) test('comparison refuses changed '+name,()=>{
  const x=clone(scenarios[1]);mutate(x);const r=E.compareRanges([scenarios[0],x],'gross_profit');
  assert.equal(r.ok,false);assert.equal(r.error.code,'INCOMPARABLE_SCENARIOS');assert.equal(r.rows,undefined);
});
test('row order is not a different economic baseline',()=>{
  const x=clone(scenarios[1]);x.lines.reverse();assert.equal(E.compareRanges([scenarios[0],x],'gross_profit').ok,true);
});
test('duplicate scenario ids are refused',()=>{assert.equal(E.compareRanges([scenarios[0],scenarios[0]],'revenue').error.code,'DUPLICATE_SCENARIO');});
test('a single invalid proposal prevents a partial valid-looking comparison',()=>{
  const x=clone(scenarios[1]);x.lines[0].unit_cost_eur=null;const r=E.compareRanges([scenarios[0],x],'revenue');assert.equal(r.ok,false);assert.equal(r.rows,undefined);
});
test('Genuine cut needs 340 further assumed units in packs of ten',()=>{
  const r=E.recoveryThreshold(scenarios[1],{line_id:'SYN-OIL-G',maximum_additional_quantity:null});
  assert.equal(r.ok,true);assert.equal(r.minimum_additional_quantity,340);assert.equal(r.result_at_minimum.gross_profit_eur,200);
  const x=clone(scenarios[1]);x.lines[0].recovered_quantity=330;assert.equal(E.evaluateRange(x).change.gross_profit_eur,-100);
});
test('BVP displacement needs 100 further recovered units, not 100 more transfers',()=>{
  const r=E.recoveryThreshold(scenarios[3],{line_id:'SYN-OIL-B',maximum_additional_quantity:null});
  assert.equal(r.minimum_additional_quantity,100);assert.equal(r.total_assumed_recovered_quantity_on_line,300);
  assert.equal(r.result_at_minimum.gross_profit_eur,0);assert.equal(r.result_at_minimum.revenue_eur,6500);
});
test('a volume cap below the required break-even blocks it',()=>{
  const r=E.recoveryThreshold(scenarios[1],{line_id:'SYN-OIL-G',maximum_additional_quantity:330});
  assert.equal(r.ok,true);assert.equal(r.status,'not_attainable');assert.equal(r.minimum_additional_quantity,null);
});
test('negative-contribution recovery has a maximum, not an unlimited gain',()=>{
  const x=sample();x.lines[0].unit_cost_eur=110;x.lines[0].scenario_net_price_eur=105;
  const r=E.recoveryThreshold(x,{line_id:'SYN-OIL-G',maximum_additional_quantity:null});
  assert.equal(r.minimum_additional_quantity,0);assert.equal(r.maximum_additional_quantity,1000);
});
test('zero contribution cannot cover additional support',()=>{
  const x=sample();x.lines[0].unit_cost_eur=100;x.support_eur=1;
  const r=E.recoveryThreshold(x,{line_id:'SYN-OIL-G',maximum_additional_quantity:null});assert.equal(r.status,'not_attainable');
});
test('zero contribution with no deficit already preserves the baseline',()=>{
  const x=sample();x.lines[0].unit_cost_eur=100;
  const r=E.recoveryThreshold(x,{line_id:'SYN-OIL-G',maximum_additional_quantity:null});assert.equal(r.minimum_additional_quantity,0);
});
test('caps are not rounded upward into invented available business',()=>{
  const r=E.recoveryThreshold(scenarios[1],{line_id:'SYN-OIL-G',maximum_additional_quantity:345});assert.equal(r.maximum_additional_quantity,340);
});
test('invalid or unknown threshold targets are refused',()=>{
  assert.equal(E.recoveryThreshold(scenarios[0],{line_id:'missing',maximum_additional_quantity:null}).error.code,'UNKNOWN_LINE');
  assert.equal(E.recoveryThreshold(scenarios[0],{line_id:'SYN-OIL-G',maximum_additional_quantity:'100'}).error.code,'INVALID_QUANTITY');
});
test('sensitivity uses only explicitly supplied whole-pack assumptions',()=>{
  const r=E.recoverySensitivity(scenarios[3],{line_id:'SYN-OIL-B',additional_quantities:[0,50,100,200]});
  assert.equal(r.ok,true);assert.deepEqual(r.rows.map(x=>x.change.gross_profit_eur),[-2000,-1000,0,2000]);assert.equal(r.is_demand_forecast,false);
});
test('invalid sensitivity does not return a partly calculated table',()=>{
  for (const quantities of [[0,11],[0,null],[10,10]]) {
    const r=E.recoverySensitivity(scenarios[3],{line_id:'SYN-OIL-B',additional_quantities:quantities});assert.equal(r.ok,false);assert.equal(r.rows,undefined);
  }
});
test('all public calculations leave inputs unchanged',()=>{
  const x=clone(scenarios);const before=JSON.stringify(x);
  E.evaluateRange(x[3]);E.compareRanges(x,'revenue');
  E.recoveryThreshold(x[3],{line_id:'SYN-OIL-B',maximum_additional_quantity:null});
  E.recoverySensitivity(x[3],{line_id:'SYN-OIL-B',additional_quantities:[0,100]});assert.equal(JSON.stringify(x),before);
});
test('browser script publishes its separate API without the existing AIM engine',()=>{
  const sandbox={};vm.createContext(sandbox);vm.runInContext(fs.readFileSync(path.join(__dirname,'../src/engine/range.js'),'utf8'),sandbox);
  assert.equal(typeof sandbox.AIMRangeEngine.evaluateRange,'function');assert.equal(sandbox.AIMEngine,undefined);
});
test('400 deterministic cases reconcile to an independent direct-sum oracle',()=>{
  let seed=228;
  const rand=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
  for(let i=0;i<400;i++) {
    const x=sample();x.lines.forEach(l=>{l.pack_size=1;l.baseline_quantity=10+rand(150);
      l.baseline_net_price_eur=(100+rand(10000))/100;l.scenario_net_price_eur=(100+rand(10000))/100;
      l.unit_cost_eur=rand(10000)/100;l.lost_quantity=rand(l.baseline_quantity+1);l.recovered_quantity=rand(100);});
    x.support_eur=rand(10000)/100;
    const q=rand(x.lines[0].baseline_quantity-x.lines[0].lost_quantity+1);
    if(q)x.transfers=[{...scenarios[3].transfers[0],quantity:q}];
    let beforeR=0,afterR=0,beforeC=0,afterC=0;
    x.lines.forEach((l,j)=>{const after=l.baseline_quantity-l.lost_quantity+l.recovered_quantity+(j===0?-q:q);
      beforeR+=l.baseline_quantity*Math.round(l.baseline_net_price_eur*100);
      afterR+=after*Math.round(l.scenario_net_price_eur*100);
      beforeC+=l.baseline_quantity*Math.round(l.unit_cost_eur*100);afterC+=after*Math.round(l.unit_cost_eur*100);});
    const r=E.evaluateRange(x);assert.equal(r.ok,true,JSON.stringify(r));
    assert.equal(Math.round(r.change.revenue_eur*100),afterR-beforeR);
    assert.equal(Math.round(r.change.gross_profit_eur*100),afterR-afterC-Math.round(x.support_eur*100)-(beforeR-beforeC));
  }
});
test('240 threshold cases equal bounded brute-force search, including negative margins',()=>{
  let checks=0;
  for(const price of [40,60,90,100,105,120])for(const cost of [0,35,60,110])for(const loss of [0,10])for(const support of [0,100,200,300,500]) {
    const x=sample();x.lines[0].pack_size=1;x.lines[0].baseline_quantity=20;x.lines[0].scenario_net_price_eur=price;
    x.lines[0].unit_cost_eur=cost;x.lines[0].lost_quantity=loss;x.support_eur=support;
    const feasible=[];
    for(let q=0;q<=100;q++) {const y=clone(x);y.lines[0].recovered_quantity=q;const r=E.evaluateRange(y);
      assert.equal(r.ok,true);if(r.change.both_nonnegative)feasible.push(q);}
    const t=E.recoveryThreshold(x,{line_id:'SYN-OIL-G',maximum_additional_quantity:100});assert.equal(t.ok,true,JSON.stringify(t));
    if(feasible.length){assert.equal(t.minimum_additional_quantity,feasible[0]);assert.equal(t.maximum_additional_quantity,feasible.at(-1));}
    else assert.equal(t.status,'not_attainable');
    checks++;
  }
  assert.equal(checks,240);
});
