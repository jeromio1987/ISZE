#!/usr/bin/env node
'use strict';
/* ===========================================================================
   Range engine parity against this component's single-part engine.

   PROVENANCE
   ----------
   Ported from AIM_RANGE_DECISION_PROTOTYPE_2026-09-22
   (tests/engine_parity.test.cjs, sha256
   3c2134593ec274af117fbcb62b0283087a2a6b2c7f62cda4f827fa0aa08dd332), which
   shipped with src/engine/range.js.

   WHAT IT COMPARES
   ----------------
   Only the arithmetic both engines claim to do: an all-volume price and
   quantity move on one product, and a one-for-one move between two products.
   It does NOT establish API compatibility, source provenance, real-offer
   validity, browser behaviour or saved-case agreement. The two APIs are
   deliberately different and neither inherits fields by guessed names.

   WHAT CHANGED IN THE PORT
   ------------------------
   The reference engine is this component's src/engine/engine.js by default,
   because that is the engine the artifact actually assembles. The prototype's
   own file required a path in AIM_REFERENCE_ENGINE instead. An explicit
   override is still honoured when that variable is set, so the comparison can
   be pointed elsewhere deliberately.

   RE-RUN, DO NOT TRUST THE RECORDED NUMBER
   ----------------------------------------
   The prototype's evidence/verification.json records its parity run against an
   engine at sha256 24ae23ee80376a2799f6b8ab8fd8f4317246dd98582076f1daccf63550216176.
   This component's engine.js is not that revision - JOB 1's wording fix alone
   changed it, and the engine this suite is measured against is reported in the
   output below. The prototype's pass count is therefore not evidence about this
   tree and was re-run rather than copied.

   Run:  node --test tests/range_engine_parity.test.cjs
         AIM_REFERENCE_ENGINE=<path> node --test tests/range_engine_parity.test.cjs
   Exit code is non-zero when any comparison fails.
   =========================================================================== */
const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const crypto = require('node:crypto');

const referencePath = process.env.AIM_REFERENCE_ENGINE
  ? path.resolve(process.env.AIM_REFERENCE_ENGINE)
  : path.join(__dirname, '..', 'src', 'engine', 'engine.js');

const previous = require(referencePath);
const range = require('../src/engine/range.js');
const fixtures = require('./fixtures/range_synthetic_scenarios.json');

const digest = crypto.createHash('sha256').update(fs.readFileSync(referencePath)).digest('hex');
console.log('range parity reference engine : ' + referencePath);
console.log('  sha256                      : ' + digest);
console.log('  the prototype recorded      : 24ae23ee80376a2799f6b8ab8fd8f4317246dd98582076f1daccf63550216176');

let count=0;
for(const price of [90,100,110])for(const recovery of [0,100])for(const lost of [0,50])for(const support of [0,100]) {
  test('overlapping all-volume arithmetic '+(++count),()=>{
    const s=structuredClone(fixtures[0]);s.lines=s.lines.slice(0,1);
    Object.assign(s.lines[0],{scenario_net_price_eur:price,recovered_quantity:recovery,lost_quantity:lost});s.support_eur=support;
    const a=range.evaluateRange(s), b=previous.calculate({price_before:100,price_after:price,
      quantity_before:1000,quantity_after:1000+recovery-lost,cost_eur:60,support_eur:support,
      scope:'all',pack_size:10,quantity_label:'explicit synthetic assumption'});
    assert.equal(a.ok,true);assert.equal(b.ok,true,JSON.stringify(b));
    assert.notEqual(b.gp_change,null);assert.notEqual(b.gp_after,null);
    for(const [r,p] of [['revenue_eur','revenue_change'],['gross_profit_eur','gp_change']])
      assert.equal(Math.round(a.change[r]*100),Math.round(b[p]*100));
    assert.equal(Math.round(a.proposal.gross_profit_eur*100),Math.round(b.gp_after*100));
  });
}
test('one-for-one transfer change agrees, while the range retains the BVP starting business',()=>{
  const s=structuredClone(fixtures[0]);s.transfers=structuredClone(fixtures[3].transfers);s.support_eur=100;
  const a=range.evaluateRange(s), b=previous.calculate({kind:'migration',price_before:100,price_after:100,
    quantity_before:1000,quantity_after:1000,cost_eur:60,support_eur:100,scope:'all',pack_size:10,
    migration:{quantity_transferred:200,from:{price:100,cost:60},to:{price:60,cost:35}}});
  assert.equal(a.ok,true);assert.equal(b.ok,true,JSON.stringify(b));
  assert.notEqual(b.gp_change,null);assert.notEqual(b.gp_after,null);
  assert.equal(a.change.revenue_eur,b.revenue_change);assert.equal(a.change.gross_profit_eur,b.gp_change);
  assert.equal(a.baseline.revenue_eur,b.revenue_before+12000);
  assert.equal(a.baseline.gross_profit_eur,b.gp_before+5000);
});
