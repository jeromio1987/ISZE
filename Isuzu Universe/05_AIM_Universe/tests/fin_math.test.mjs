#!/usr/bin/env node
/* ===========================================================================
   Focused arithmetic tests for the corrected AIM pricing engine.

   Run:  node tests/fin_math.test.mjs
         node tests/fin_math.test.mjs <payload.json>

   Every expected figure below is worked out by hand in the comment above it, so
   the test says what the arithmetic should be and not merely what the code does.
   The synthetic figures are the ones named in the corrective brief. They are not
   ISZE prices.
   =========================================================================== */

import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

/* RE-POINTED 2026-09-22 (duplicate-module correction). This suite loaded
   src/engine/pricing.js, which tools/build.py lists in UNWIRED_MODULES and does
   not assemble; the module the artifact runs is src/engine/engine.js. The two
   were byte-identical at the moment of the repoint (sha256 both 1db7f3fb6fa8f399),
   so no expected figure moved - which is why the repoint is safe here and not
   merely convenient. Counting a green run from the retired copy would have gone
   on reporting on a module nobody receives the first time engine.js changed. */
const engine = require(join(ROOT, 'src', 'engine', 'engine.js'));
const contracts = require(join(ROOT, 'src', 'data', 'contracts.js'));

/* The engine is deliberately payload-free. The restricted business payload is
   loaded only when it is asked for, and it is read for arithmetic - never
   copied into this file. */
const RESTRICTED = join(ROOT, '..', '06_Working', '_aim_pack_20260922', '_payload.json');
const FIXTURE = join(HERE, 'fixtures', 'synthetic_payload.json');
const payloadPath = process.argv[2]
  || (existsSync(RESTRICTED) ? RESTRICTED : FIXTURE);
const payload = JSON.parse(readFileSync(payloadPath, 'utf8'));
engine.setPayload(payload);

const results = [];
function test(id, name, fn) {
  try {
    const evidence = fn();
    results.push({ id, name, status: 'PASS', evidence: evidence === undefined ? null : evidence });
  } catch (e) {
    results.push({ id, name, status: 'FAIL', evidence: e.message });
  }
}
/* A few checks can only run on the restricted business payload: they name its
   cases. When the synthetic fixture is used instead they are reported as
   SKIPPED with the reason, not quietly passed and not failed. */
function restrictedTest(ids, id, name, fn) {
  const missing = ids.filter(x => !(payload.cases || []).some(c => c.id === x));
  if (missing.length) {
    results.push({ id, name, status: 'SKIP',
      evidence: 'needs the restricted payload case ' + missing.join(', ')
        + '; not present in ' + payloadPath.split(/[\\/]/).pop() });
    return;
  }
  test(id, name, fn);
}
const caseOf = id => payload.cases.find(c => c.id === id);
const approx = (observed, expected, tolerance = 1e-8) =>
  assert.ok(Number.isFinite(observed) && Math.abs(observed - expected) <= tolerance,
    `observed ${observed}; expected ${expected}`);
function addDays(iso, days) {
  const d = new Date(iso + 'T00:00:00Z');
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/* The synthetic scenario the brief names: 100 units at 100 EUR, parts cost 60. */
const calc = (extra = {}) => engine.calculate(Object.assign({
  price_before: 100, price_after: 100, quantity_before: 100, quantity_after: null,
  cost_eur: 60, support_eur: 0, scope: 'all', quantity_label: 'manual scenario', pack_size: 1
}, extra));

/* ---------------------------------------------------------------------------
   FIN-02  combined offer margin is reported profit divided by reported revenue
   --------------------------------------------------------------------------- */

/* 100 existing units at 100 EUR plus 20 additional at 80, cost 60:
     revenue  = 100 x 100 + 20 x 80 = 11,600
     cost     = 120 x 60          =  7,200
     profit   = 11,600 - 7,200    =  4,400
     margin   = 4,400 / 11,600    = 37.931034...%
   The unit margin on the discounted units is 1 - 60/80 = 25%, which is a
   different measure and must not be reported as the offer margin. */
test('FIN-02a', 'Combined margin is profit over revenue for the whole offer', () => {
  const r = calc({ scope: 'incremental', price_after: 80, quantity_after: 120 });
  approx(r.revenue_after, 11600);
  approx(r.gp_after, 4400);
  approx(r.margin_after_pct, 37.93103448275862, 1e-9);
  approx(r.margin_after_pct, 100 * r.gp_after / r.revenue_after);
  approx(r.margin_unit_after_pct, 25);
  assert.notEqual(r.margin_after_pct, r.margin_unit_after_pct,
    'the offer margin and the unit margin are the same number');
  return `offer margin ${r.margin_after_pct.toFixed(3)}% vs unit margin ${r.margin_unit_after_pct.toFixed(1)}%`;
});

/* 100 units at 100 EUR, cost 60, 500 EUR support:
     revenue = 10,000; profit = 10,000 - 6,000 - 500 = 3,500; margin = 35%.
   The old engine printed the profit of 3,500 beside a margin of 40%. */
test('FIN-02b', 'The margin follows the profit the engine actually printed after support', () => {
  const r = calc({ support_eur: 500 });
  approx(r.revenue_after, 10000);
  approx(r.gp_after, 3500);
  approx(r.margin_after_pct, 35);
  assert.notEqual(r.margin_after_pct, 40, 'the margin ignored the support it had already deducted');
  return `profit 3,500 on revenue 10,000 -> ${r.margin_after_pct}%`;
});

test('FIN-02c', 'The reported margin always equals profit over revenue', () => {
  const scenarios = [
    calc(), calc({ price_after: 90 }), calc({ price_after: 110 }),
    calc({ price_after: 80, quantity_after: 150 }),
    calc({ scope: 'incremental', price_after: 80, quantity_after: 120, support_eur: 200 }),
    calc({ support_eur: 500 }), calc({ cost_eur: 0 }),
    calc({ scope: 'incremental', quantity_after: 140, price_after: 95.5, support_eur: 37.5 })
  ];
  scenarios.forEach(r => approx(r.margin_after_pct, 100 * r.gp_after / r.revenue_after, 1e-9));
  return `${scenarios.length} scenarios reconcile`;
});

/* ---------------------------------------------------------------------------
   FIN-04  support is counted once and the profit bridge reconciles
   --------------------------------------------------------------------------- */

/* profit after = revenue after - parts cost of the units sold - support, with
   support taken off exactly once. */
test('FIN-04a', 'Profit after equals revenue less cost of units sold less support', () => {
  const scenarios = [calc(), calc({ price_after: 90 }), calc({ price_after: 110 }),
    calc({ scope: 'incremental', price_after: 80, quantity_after: 120, support_eur: 200 }),
    calc({ support_eur: 500 }), calc({ scope: 'incremental', price_after: 80, support_eur: 200 })];
  scenarios.forEach(r => {
    const costOfUnitsSold = r.quantity_after * r.cost;   /* the units actually sold */
    approx(r.gp_after, r.revenue_after - costOfUnitsSold - r.support_eur, 1e-9);
    assert.equal(r.bridge_reconciles, true, 'the bridge did not reconcile');
    assert.ok(!r.flags.some(f => f.code === 'BRIDGE_FAILS'), 'a bridge failure was flagged');
  });
  return `${scenarios.length} scenarios reconcile exactly`;
});

test('FIN-04b', 'Support is deducted once, not twice', () => {
  const without = calc({ price_after: 90, support_eur: 0 });
  const withSupport = calc({ price_after: 90, support_eur: 500 });
  approx(without.gp_after - withSupport.gp_after, 500);
  approx(without.revenue_after, withSupport.revenue_after);
  assert.equal(withSupport.support_counted_once, true);
  return 'one deduction of 500 EUR, revenue unchanged';
});

test('FIN-04c', 'The bridge reports the movement in revenue, cost and support', () => {
  const r = calc({ scope: 'incremental', price_after: 80, quantity_after: 120, support_eur: 200 });
  approx(r.bridge_revenue_change, 1600);           /* 20 extra units at 80 */
  approx(r.bridge_cost_change, 1200);              /* 20 extra units at 60 */
  approx(r.bridge_support_eur, 200);
  approx(r.gp_change, r.bridge_revenue_change - r.bridge_cost_change - r.bridge_support_eur);
  return `revenue +1,600, cost +1,200, support 200 -> profit ${r.gp_change}`;
});

/* ---------------------------------------------------------------------------
   FIN-03  break-even is split by eligibility
   --------------------------------------------------------------------------- */

/* All-volume: a cut to 80 on 100 units at a 60 cost.
     to hold revenue: 10,000 / 80        = 125 units
     to hold profit:  (4,000 + 0) / 20   = 200 units */
test('FIN-03a', 'All-volume break-even is unchanged by the correction', () => {
  const r = calc({ price_after: 80 });
  approx(r.qty_preserve_revenue, 125);
  approx(r.qty_preserve_gp, 200);
  return '125 units to hold revenue, 200 to hold profit';
});

/* Incremental-only: the 100 existing units keep the price of 100, so they
   already hold both their revenue and their contribution. Only additional
   units, earning 80 - 60 = 20 each, have to recover the support.
     support 0:   100 units (nothing extra is needed)
     support 200: 100 + 200/20 = 110 units
   The old engine returned 125, 200 and 210. */
test('FIN-03b', 'Incremental-only holds revenue on the existing units alone', () => {
  const r = calc({ scope: 'incremental', price_after: 80 });
  approx(r.qty_preserve_revenue, 100);
  assert.equal(r.qty_preserve_gp === null, false);
  return '100 units, not 125';
});

test('FIN-03c', 'Incremental-only holds profit on the existing units alone', () => {
  const r = calc({ scope: 'incremental', price_after: 80 });
  approx(r.qty_preserve_gp, 100);
  return '100 units, not 200';
});

test('FIN-03d', 'Incremental-only support is recovered from additional-unit contribution', () => {
  const r = calc({ scope: 'incremental', price_after: 80, support_eur: 200 });
  approx(r.qty_preserve_gp, 110);
  approx(r.extra_qty_to_preserve_gp, 10);
  approx(r.price_after - r.cost, 20);
  return '110 units in total, 10 more than the base, not 210';
});

test('FIN-03e', 'Incremental-only with no support needs no extra volume', () => {
  const r = calc({ scope: 'incremental', price_after: 80, support_eur: 0 });
  approx(r.qty_preserve_gp, 100);
  approx(r.extra_qty_to_preserve_gp, 0);
  return 'no additional unit is required';
});

test('FIN-03f', 'Incremental-only is not attainable when the price is at or below cost', () => {
  const r = calc({ scope: 'incremental', price_after: 60, support_eur: 200 });
  assert.equal(r.qty_preserve_gp, null, 'a quantity was reported although no unit contributes');
  assert.match(r.qty_preserve_gp_label, /not attainable/i);
  return r.qty_preserve_gp_label.slice(0, 90);
});

test('FIN-03g', 'A required orderable quantity is rounded up, not rounded away', () => {
  /* all-volume, price 80, threshold 125 sets of 4: the smallest orderable
     quantity strictly above 125 is 128, not 125.01 rounded back to 125. */
  const r = calc({ price_after: 80, pack_size: 4 });
  const orderable = 100 + r.extra_qty_to_exceed_revenue;
  approx(orderable, 128);
  assert.ok(orderable > r.qty_preserve_revenue, 'the orderable quantity is not above the threshold');
  assert.equal(orderable % 4, 0, 'the orderable quantity is not a whole number of packs');
  return `threshold 125 -> orderable 128 in packs of 4`;
});

test('FIN-03h', 'A threshold already on a pack boundary still needs one more pack', () => {
  /* threshold 125 with packs of 25: "more than 125" is 150, because 125 itself
     only equals the unchanged offer. */
  const r = calc({ price_after: 80, pack_size: 25 });
  const orderable = 100 + r.extra_qty_to_exceed_revenue;
  approx(orderable, 150);
  assert.ok(orderable > r.qty_preserve_revenue);
  return 'threshold 125 -> orderable 150 in packs of 25';
});

test('FIN-03i', 'A required quantity on a pack boundary is not rounded up again', () => {
  const r = calc({ price_after: 80, pack_size: 25 });
  approx(r.extra_qty_to_preserve_revenue, 25);
  approx(r.quantity_before + r.extra_qty_to_preserve_revenue, 125);
  return '125 is already a whole number of packs of 25';
});

test('FIN-03j', 'Pack rounding is upward for any pack size', () => {
  approx(engine.roundToPack(125.0001, 4), 128);
  approx(engine.roundToPack(125, 4), 128);
  approx(engine.roundToPack(124, 4), 124);
  approx(engine.smallestPackAbove(125, 4), 128);
  approx(engine.smallestPackAbove(125, 25), 150);
  approx(engine.smallestPackAbove(100, 50), 150);
  approx(engine.smallestPackAbove(125.5, 1), 126);
  assert.equal(engine.smallestPackAbove(null, 4), null);
  return 'thresholds round up to a real pack';
});

/* ---------------------------------------------------------------------------
   FIN-06  invalid inputs are refused; four separate states
   --------------------------------------------------------------------------- */

/* The old engine validated quantity_before but not quantity_after: negative,
   NaN and infinite proposed quantities came back ok:true, and an invalid
   support string silently became zero. */
test('FIN-06a', 'A negative proposed quantity is refused', () => {
  const r = calc({ quantity_after: -1 });
  assert.equal(r.ok, false);
  assert.ok(r.errors.length > 0);
  return r.errors[0].slice(0, 90);
});

test('FIN-06b', 'A proposed quantity of NaN is refused', () => {
  const r = calc({ quantity_after: NaN });
  assert.equal(r.ok, false);
  return r.errors[0].slice(0, 90);
});

test('FIN-06c', 'An infinite proposed quantity is refused', () => {
  const r = calc({ quantity_after: Infinity });
  assert.equal(r.ok, false);
  return r.errors[0].slice(0, 90);
});

test('FIN-06d', 'A proposed quantity that is not a number is refused', () => {
  ['abc', {}, [], true].forEach(bad => {
    const r = calc({ quantity_after: bad });
    assert.equal(r.ok, false, `accepted ${JSON.stringify(bad)}`);
  });
  return 'text, object, array and boolean are all refused';
});

test('FIN-06e', 'An invalid support amount is refused, not treated as zero', () => {
  const r = calc({ support_eur: 'invalid' });
  assert.equal(r.ok, false);
  assert.ok(r.errors.some(e => /support/i.test(e)));
  return r.errors.find(e => /support/i.test(e)).slice(0, 90);
});

test('FIN-06f', 'A negative support amount is refused', () => {
  assert.equal(calc({ support_eur: -100 }).ok, false);
  return 'negative support refused';
});

test('FIN-06g', 'A proposed quantity of zero is a withdrawal, not a price', () => {
  const r = calc({ quantity_after: 0 });
  assert.equal(r.ok, false);
  assert.match(r.error, /withdrawal/i);
  return r.error.slice(0, 90);
});

test('FIN-06h', 'A negative quantity is a return only when the scenario says so', () => {
  const unlabelled = calc({ quantity_after: -20 });
  assert.equal(unlabelled.ok, false, 'an unlabelled negative quantity was accepted');
  assert.match(unlabelled.error, /return/i);

  const labelled = calc({ quantity_after: -20, quantity_label: 'return of goods' });
  assert.equal(labelled.ok, true, 'a declared return was refused');
  assert.ok(labelled.flags.some(f => f.code === 'NET_NEGATIVE_RETURN'));
  return 'unlabelled refused; declared return reported as its own case';
});

test('FIN-06i', 'Zero, unknown, return and invalid are four different states', () => {
  const zero = engine.validateScenario({ price_before: 100, price_after: 100,
    quantity_before: 100, quantity_after: 0, cost_eur: 60 });
  const unknown = engine.validateScenario({ price_before: 100, price_after: 100,
    quantity_before: 100, quantity_after: null, cost_eur: 60 });
  const returned = engine.validateScenario({ price_before: 100, price_after: 100,
    quantity_before: 100, quantity_after: -20, quantity_label: 'return of goods', cost_eur: 60 });
  const invalid = engine.validateScenario({ price_before: 100, price_after: 100,
    quantity_before: 100, quantity_after: 'x', cost_eur: 60 });
  assert.equal(zero.states.quantity_after, 'zero');
  assert.equal(unknown.states.quantity_after, 'unknown');
  assert.equal(returned.states.quantity_after, 'return');
  assert.equal(invalid.states.quantity_after, 'invalid');
  assert.equal(zero.ok, false);
  assert.equal(unknown.ok, true);
  assert.equal(returned.ok, true);
  assert.equal(invalid.ok, false);
  return 'zero refused, unknown allowed, return reported, invalid refused';
});

test('FIN-06j', 'A missing cost does not suppress a valid revenue result', () => {
  const r = calc({ cost_eur: null, price_after: 90 });
  assert.equal(r.ok, true);
  approx(r.revenue_after, 9000);
  approx(r.revenue_change, -1000);
  assert.equal(r.gp_after, null);
  assert.equal(r.gp_change, null);
  assert.equal(r.margin_after_pct, null);
  assert.equal(r.cost_missing_not_zero, true);
  assert.ok(r.conditional.some(c => /cost/i.test(c)));
  return 'revenue calculated, profit declared unavailable';
});

test('FIN-06k', 'A zero cost is a value, not a missing field', () => {
  const r = calc({ cost_eur: 0 });
  assert.equal(r.ok, true);
  assert.equal(r.cost_is_zero, true);
  assert.equal(r.cost_missing_not_zero, false);
  approx(r.margin_after_pct, 100);
  assert.ok(r.conditional.some(c => /zero/i.test(c)));
  return 'zero cost stated as a condition, margin 100%';
});

test('FIN-06l', 'An incremental-only offer cannot be below the existing volume', () => {
  const r = calc({ scope: 'incremental', price_after: 80, quantity_after: 50 });
  assert.equal(r.ok, false);
  assert.match(r.error, /fewer units than/i);
  return r.error.slice(0, 90);
});

test('FIN-06m', 'Every numeric output is finite or null', () => {
  [calc({ price_after: 90, quantity_after: 125, support_eur: 200 }), calc({ cost_eur: null }),
   calc({ scope: 'incremental', price_after: 80, quantity_after: 120, support_eur: 200, pack_size: 7 })]
    .forEach(r => Object.keys(r).forEach(k => {
      if (typeof r[k] === 'number') assert.ok(Number.isFinite(r[k]), `${k} is not finite`);
    }));
  return 'all numeric outputs finite or null';
});

test('FIN-06n', 'Errors are reported together rather than one at a time', () => {
  const r = engine.validateScenario({ price_before: 0, price_after: -1, quantity_before: 0,
    quantity_after: -5, support_eur: 'x', cost_eur: 'y', pack_size: 0 });
  assert.ok(r.errors.length >= 5, `only ${r.errors.length} reasons returned`);
  return `${r.errors.length} reasons returned in one pass`;
});

/* ---------------------------------------------------------------------------
   FIN-04 date  an unusable effective date is unresolved, not October
   --------------------------------------------------------------------------- */

test('FIN-04d1', 'An invalid effective date is unresolved and says why', () => {
  const r = engine.costForDate(payload, payload.cases[0].pn, 'not-a-date');
  assert.equal(r.ok, false);
  assert.equal(r.resolved, false);
  assert.equal(r.basis_id, null);
  assert.ok(r.error);
  return r.error.slice(0, 96);
});

/* The declared windows in the restricted payload are SEP26 (1 Apr 2026 to
   30 Sep 2026) and OCT26 (1 Oct 2026 to 31 Mar 2027). OCT26's end date is not
   carried as its own field, so it is read from the window that basis declares -
   the basis declaring its own window, not the engine inventing one. Any basis
   whose window cannot be read is reported as having no declared window, and a
   date is never placed in it. */
test('FIN-04d2', 'A date outside every declared window is unresolved', () => {
  const undated = engine.v03bases().filter(b => b.status === 'forward')
    .filter(b => !engine.basisWindow(b).from || !engine.basisWindow(b).to);
  assert.equal(undated.length, 0,
    'these forward bases declare no usable window and were not assumed: '
    + undated.map(b => b.basis_id).join(', '));

  ['1900-01-01', '2035-01-01', '2020-01-01'].forEach(d => {
    const r = engine.costForDate(payload, payload.cases[0].pn, d);
    assert.equal(r.basis_id, null, `${d} silently selected ${r.basis_id}`);
    assert.ok(r.error);
  });
  return 'the bases name their windows; a date outside all of them is unresolved';
});

test('FIN-04d2b', 'A basis window is read from the basis, not assumed open ended', () => {
  const windows = engine.v03bases().filter(b => b.status === 'forward')
    .map(b => ({ id: b.basis_id, w: engine.basisWindow(b) }));
  windows.forEach(x => {
    assert.ok(x.w.from && x.w.to, `${x.id} declares no usable window`);
    assert.ok(x.w.from <= x.w.to, `${x.id} has a window that runs backwards`);
  });
  /* Contiguous windows are correct: a September offer takes September and an
     October offer takes October. The test is that the LAST declared end is a
     real edge: one day after it, nothing is selected. */
  const last = windows.reduce((a, b) => (a.w.to > b.w.to ? a : b));
  const after = engine.costForDate(payload, payload.cases[0].pn, addDays(last.w.to, 1));
  assert.equal(after.basis_id, null,
    `a date one day after ${last.id} ended (${last.w.to}) still selected ${after.basis_id}`);
  assert.ok(after.error);
  /* And the declared end itself is still inside the window. */
  const onEnd = engine.costForDate(payload, payload.cases[0].pn, last.w.to);
  assert.equal(onEnd.basis_id, last.id);
  return windows.map(x => `${x.id} ${x.w.from}..${x.w.to}`).join('; ')
    + `; ${addDays(last.w.to, 1)} draws nothing`;
});

test('FIN-04d3', 'A valid date still discriminates between the named bases', () => {
  const fwd = engine.v03bases().filter(b => b.status === 'forward');
  const w = fwd.map(b => ({ id: b.basis_id, window: engine.basisWindow(b) }))
    .filter(x => x.window.from && x.window.to);
  assert.ok(w.length >= 2, 'fewer than two dated forward bases to discriminate between');
  const a = engine.costForDate(payload, payload.cases[0].pn, w[0].window.from);
  const b = engine.costForDate(payload, payload.cases[0].pn, w[1].window.from);
  assert.equal(a.basis_id, w[0].id);
  assert.equal(b.basis_id, w[1].id);
  assert.notEqual(a.basis_id, b.basis_id);
  assert.notEqual(a.record.cost_eur, b.record.cost_eur);
  return `${a.basis_id} cost ${a.record.cost_eur} vs ${b.basis_id} cost ${b.record.cost_eur}`;
});

test('FIN-04d4', 'A partial date or an impossible date is refused', () => {
  ['2026-9-1', '2026-13-01', '2026-02-30', '', null, undefined].forEach(d => {
    const r = engine.costForDate(payload, payload.cases[0].pn, d);
    assert.equal(r.resolved, false, `accepted ${JSON.stringify(d)}`);
  });
  return 'short, impossible and blank dates are all unresolved';
});

test('FIN-04d5', 'The declared default basis is used only when no date was supplied', () => {
  const noDate = engine.resolveOfferBasis(payload, null);
  assert.equal(noDate.basis_id, payload.meta.defaultForwardBasis);
  assert.match(noDate.source, /default/i);
  const badDate = engine.resolveOfferBasis(payload, 'not-a-date');
  assert.equal(badDate.basis_id, null, 'an unusable date fell back to the default');
  return `no date -> ${noDate.basis_id}; unusable date -> no basis`;
});

restrictedTest(['ITUK-PADS'], 'FIN-04d6',
  'One comparison uses one cost basis for every comparable row', () => {
    const c = caseOf('ITUK-PADS');
    const basis = engine.resolveOfferBasis(payload, c.offer_effective_date || null);
    const rk = engine.rankAlternatives(c, 'revenue', { payload });
    assert.equal(rk.comparison_basis_id, basis.basis_id);
    rk.ranked.forEach(row => {
      if (row.result.cost === null) return;
      assert.equal(row.result.cost_basis_id, rk.comparison_basis_id,
        `${row.alternative.alternative_id} used ${row.result.cost_basis_id}`);
    });
    return `every comparable row priced on ${rk.comparison_basis_id} (${rk.comparison_basis_source})`;
  });

restrictedTest(['ITUK-PADS'], 'FIN-04d7',
  'A differently named cost basis on one row is stated, not applied', () => {
    const c = caseOf('ITUK-PADS');
    const rk = engine.rankAlternatives(c, 'revenue', { payload });
    const differing = rk.ranked.filter(r => r.result.flags.some(f => f.code === 'COST_BASIS_DIFFERENCE'));
    assert.ok(differing.length > 0,
      'an alternative naming a different cost basis was not reported');
    differing.forEach(r => {
      assert.equal(r.result.cost_basis_id, rk.comparison_basis_id,
        'the differently named basis was applied to the numbers');
      assert.ok(r.result.conditional.some(t => /cost basis/i.test(t)));
    });
    return `${differing.length} row(s) name a different basis and it is stated, not applied`;
  });

restrictedTest(['ITUK-PADS'], 'FIN-04d8',
  'A recorded baseline is never rebuilt by rounding a price and called history', () => {
    const c = caseOf('ITUK-PADS');
    const b = engine.baseline(c);
    assert.equal(b.reconciles_to_recorded, false, 'this case was expected not to reconcile');
    assert.equal(b.is_rounded_scenario, true);
    assert.ok(Math.abs(b.revenue - c.baselineDefined.observed_billing_eur) > 0.005);
    assert.match(b.basis_statement, /rounded/i);
    assert.match(b.basis_statement, /does not reproduce/i);
    return `rounded scenario at ${b.price} EUR per unit, not recorded history`;
  });

/* ---------------------------------------------------------------------------
   FIN-07  a Genuine/BVP migration is unresolved until it is a calculation
   --------------------------------------------------------------------------- */

/* The old engine named a move to the Genuine counterpart and then priced the
   original BVP reference unchanged, returning the same zero as no action. */
restrictedTest(['IMOTORS-OIL'], 'FIN-07a',
  'A migration without two product lines is unresolved, not a zero', () => {
    const c = caseOf('IMOTORS-OIL');
    const rk = engine.rankAlternatives(c, 'revenue', { payload });
    const row = rk.ranked.find(r => r.alternative.kind === 'migration');
    assert.ok(row, 'the case carries no migration alternative');
    assert.equal(row.result.migration_status, 'unresolved');
    assert.equal(row.result.revenue_change, null, 'a fabricated revenue change was reported');
    assert.equal(row.result.gp_change, null, 'a fabricated gross profit change was reported');
    assert.equal(row.result.ok, false);
    assert.equal(row.result.resolved, false);
    assert.ok(row.result.flags.some(f => f.code === 'MIGRATION_UNRESOLVED'));
    return 'revenue change null, profit change null, status unresolved';
  });

restrictedTest(['IMOTORS-OIL'], 'FIN-07b',
  'An unresolved migration is never reported as zero benefit', () => {
    const c = caseOf('IMOTORS-OIL');
    const rk = engine.rankAlternatives(c, 'revenue', { payload });
    const row = rk.ranked.find(r => r.alternative.kind === 'migration');
    assert.notEqual(row.result.gp_change, 0);
    assert.notEqual(row.result.revenue_change, 0);
    return 'null is not zero';
  });

restrictedTest(['IMOTORS-OIL'], 'FIN-07c',
  'An unresolved migration still reports the unchanged offer it is measured against', () => {
    const c = caseOf('IMOTORS-OIL');
    const rk = engine.rankAlternatives(c, 'revenue', { payload });
    const row = rk.ranked.find(r => r.alternative.kind === 'migration');
    approx(row.result.revenue_before,
      c.baselineDefined.quantity * engine.round2(c.baselineDefined.observed_unit_price));
    assert.ok(row.result.gp_before !== null);
    return `unchanged offer revenue ${row.result.revenue_before} still reported`;
  });

/* Two product lines with prices, costs and a stated transferred quantity.

   SYNTHETIC FIGURES THROUGHOUT. These are made up for the test and are not any
   real ISZE or supplier price or cost. The service-cost figures below are the
   same round numbers the rest of this file uses (a 60 EUR unit cost at a
   100 EUR price), so no restricted cost table ever enters this file.

     100 units move from a line priced at 100 with a cost of 60
            to a line priced at 130 with a cost of 90.
     revenue change          = 100 x (130 - 100)  =  3,000
     contribution taken up   = 100 x (130 - 90)   =  4,000
     contribution displaced  = 100 x (100 - 60)   =  4,000
     profit change           = 4,000 - 4,000      =      0  (a mix move with
                               equal contribution: the honest answer is that it
                               buys nothing, which is exactly what the old engine
                               claimed without calculating it)

   A second case, where the migration genuinely creates value:
     priced at 130 with a cost of 70 -> contribution 6,000; profit change +2,000. */
test('FIN-07d', 'A fully supplied migration is a two-product calculation', () => {
  const neutral = engine.calculate({
    price_before: 100, price_after: 100, quantity_before: 1224, quantity_after: 1224,
    cost_eur: 60, support_eur: 0, scope: 'all', kind: 'migration',
    migration: { quantity_transferred: 100,
      from: { part_number: 'SYNTH-BVP', price: 100, cost: 60 },
      to: { part_number: 'SYNTH-GENUINE', price: 130, cost: 90 } }
  });
  assert.equal(neutral.migration_status, 'modelled');
  assert.equal(neutral.ok, true);
  approx(neutral.revenue_change, 3000);
  approx(neutral.gp_change, 0);
  assert.equal(neutral.bridge_reconciles, true);
  assert.ok(neutral.flags.some(f => f.code === 'MIGRATION_NOT_NEW_BUSINESS'));
  assert.ok(!neutral.flags.some(f => f.code === 'MIGRATION_UNRESOLVED'));

  const valueCreating = engine.calculate({
    price_before: 100, price_after: 100, quantity_before: 1224, quantity_after: 1224,
    cost_eur: 60, support_eur: 0, scope: 'all', kind: 'migration',
    migration: { quantity_transferred: 100,
      from: { part_number: 'SYNTH-BVP', price: 100, cost: 60 },
      to: { part_number: 'SYNTH-GENUINE', price: 130, cost: 70 } }
  });
  approx(valueCreating.revenue_change, 3000);
  approx(valueCreating.gp_change, 2000);
  assert.equal(valueCreating.bridge_reconciles, true);
  assert.notEqual(valueCreating.gp_change, neutral.gp_change,
    'a migration that creates value returns the same number as one that does not');

  return 'mix move: +3,000 revenue, 0 profit; value-creating move: +3,000 revenue, +2,000 profit';
});

test('FIN-07e', 'A migration missing only the transferred quantity stays unresolved', () => {
  const r = engine.calculate({
    price_before: 100, price_after: 100, quantity_before: 1224, cost_eur: 60,
    scope: 'all', kind: 'migration',
    migration: { from: { price: 100, cost: 60 }, to: { price: 130, cost: 90 } }
  });
  assert.equal(r.migration_status, 'unresolved');
  assert.equal(r.revenue_change, null);
  assert.equal(r.gp_change, null);
  return 'partially supplied inputs stay unresolved';
});

/* ---------------------------------------------------------------------------
   FIN-09  one volume normalisation, one calculation, both entry points
   --------------------------------------------------------------------------- */

/* PADS-VOL states a 25% volume response on a base of 1,400 units, so the
   quantity is 1,750. The old ranking returned 1,750 and the old both-objective
   view returned 1,400. The same check runs generically on any case carrying a
   stated volume assumption. */
restrictedTest(['ITUK-PADS'], 'FIN-09a',
  'Ranking and both-objective agree on the stated volume', () => {
    const c = caseOf('ITUK-PADS');
    const alt = c.alternatives.find(a => a.alternative_id === 'PADS-VOL');
    const ranked = engine.rankAlternatives(c, 'revenue', { payload })
      .ranked.find(x => x.alternative.alternative_id === 'PADS-VOL').result;
    const both = engine.bothObjectives(c, alt, { payload }).result;
    approx(ranked.quantity_after, 1750);
    approx(both.quantity_after, 1750);
    approx(both.quantity_after, ranked.quantity_after);
    return `1,750 units through both entry points, from a 1,400 base and a 25% assumption`;
  });

restrictedTest(['ITUK-PADS'], 'FIN-09b',
  'The same alternative gives the same economics through both entry points', () => {
    const c = caseOf('ITUK-PADS');
    const alt = c.alternatives.find(a => a.alternative_id === 'PADS-VOL');
    const ranked = engine.rankAlternatives(c, 'revenue', { payload })
      .ranked.find(x => x.alternative.alternative_id === 'PADS-VOL').result;
    const both = engine.bothObjectives(c, alt, { payload }).result;
    ['revenue_after', 'gp_after', 'gp_change', 'margin_after_pct', 'qty_preserve_revenue',
     'qty_preserve_gp'].forEach(k => approx(both[k], ranked[k], 1e-9));
    return 'revenue, profit, margin and both break-evens match';
  });

restrictedTest(['ITUK-PADS'], 'FIN-09e',
  'An explicit override still wins over the stated assumption', () => {
    const c = caseOf('ITUK-PADS');
    const alt = c.alternatives.find(a => a.alternative_id === 'PADS-VOL');
    const both = engine.bothObjectives(c, alt, { payload, quantity_after: 2000 }).result;
    approx(both.quantity_after, 2000);
    return 'the replay override is honoured';
  });

test('FIN-09c', 'Every alternative agrees through both entry points', () => {
  let compared = 0;
  payload.cases.forEach(c => {
    const ranked = engine.rankAlternatives(c, 'revenue', { payload }).ranked;
    ranked.forEach(row => {
      const both = engine.bothObjectives(c, row.alternative, { payload }).result;
      if (both.quantity_after === null || row.result.quantity_after === null) return;
      approx(both.quantity_after, row.result.quantity_after);
      compared += 1;
    });
  });
  return `${compared} alternatives across ${payload.cases.length} cases agree on quantity`;
});

test('FIN-09d', 'One calc is created by one function', () => {
  /* calculate and v03run are the same function object, not two paths: the v03
     name is an alias kept so the existing callers keep working. */
  const names = Object.keys(engine);
  const calcNames = names.filter(n => typeof engine[n] === 'function'
    && /^(run|calc|scenario|compute)/i.test(n));
  const distinct = new Set(calcNames.map(n => engine[n]));
  assert.equal(distinct.size, 1,
    `more than one calculation function: ${calcNames.join(', ')}`);
  assert.deepEqual([...distinct], [engine.calculate]);
  assert.equal(engine.v03run, engine.calculate);
  assert.equal(engine.v03rank, engine.rankAlternatives);
  assert.equal(engine.v03both, engine.bothObjectives);
  assert.equal(engine.v03baseline, engine.baseline);
  assert.equal(engine.v03costForDate, engine.costForDate);
  return `${calcNames.join(' and ')} are one function; the other v03 names are aliases`;
});

/* ---------------------------------------------------------------------------
   FIN-08  two objectives, no invented advice
   --------------------------------------------------------------------------- */

test('FIN-08a', 'Changing the objective changes the order, not the baseline or quantity', () => {
  let checked = 0;
  (payload.cases || []).forEach(c => {
    const rev = engine.rankAlternatives(c, 'revenue', { payload });
    const gp = engine.rankAlternatives(c, 'grossProfit', { payload });
    assert.equal(rev.baseline.revenue, gp.baseline.revenue);
    assert.equal(rev.baseline.quantity, gp.baseline.quantity);
    assert.equal(rev.comparison_basis_id, gp.comparison_basis_id);
    const asMap = rows => JSON.stringify(rows
      .map(r => [r.alternative.alternative_id, r.result.quantity_after])
      .sort((a, b) => String(a[0]).localeCompare(String(b[0]))));
    assert.equal(asMap(rev.ranked), asMap(gp.ranked));
    checked += rev.ranked.length;
  });
  return `${checked} rows across ${(payload.cases || []).length} cases share one baseline`;
});

test('FIN-08b', 'The ranking is ordered by the chosen objective and nothing else', () => {
  let checked = 0;
  (payload.cases || []).forEach(c => {
    ['revenue', 'grossProfit'].forEach(obj => {
      const key = obj === 'grossProfit' ? 'gp_change' : 'revenue_change';
      const rk = engine.rankAlternatives(c, obj, { payload });
      const values = rk.ranked.filter(r => r.result.ok).map(r => r.result[key]);
      for (let i = 1; i < values.length; i++) {
        assert.ok(values[i - 1] >= values[i],
          `${c.id} ${obj} is not in descending order`);
      }
      checked += values.length;
    });
  });
  return `${checked} ordered values; each objective orders by its own measure`;
});

test('FIN-08c', 'No invented optimum, elasticity, sacrifice or minimum margin is produced', () => {
  const r = calc({ price_after: 90, quantity_after: 125 });
  const banned = ['score', 'optimum', 'optimal', 'recommended_price', 'elasticity',
    'acceptable_sacrifice', 'minimum_margin', 'min_margin'];
  const keys = Object.keys(r).map(k => k.toLowerCase());
  banned.forEach(b => assert.ok(!keys.includes(b), `the result carries a ${b} field`));
  (payload.cases || []).forEach(c => {
    engine.rankAlternatives(c, 'revenue', { payload }).ranked.forEach(row => {
      assert.ok(!('score' in row.result), 'a composite score was attached to a ranked row');
      assert.ok(!('recommended' in row.result), 'a recommendation was attached to a row');
    });
  });
  return 'revenue and profit stay two separate measures, ranked without a score';
});

test('FIN-08d', 'The engine assumes no elasticity and invents no optimum', () => {
  const r = calc({ price_after: 90 });
  assert.equal(r.ok, true);
  const text = r.conditional.join(' ');
  assert.ok(!/an elasticity of/i.test(text), 'an elasticity figure was stated');
  assert.ok(!/optimal price|price optimum/i.test(text), 'a price optimum was invented');
  return 'no elasticity assumed, calculation not blocked';
});

restrictedTest(['ITUK-PADS'], 'FIN-08e',
  'No factor, code or internal nickname is written into human-facing text', () => {
    const c = caseOf('ITUK-PADS');
    const rk = engine.rankAlternatives(c, 'revenue', { payload });
    const text = rk.ranked.map(r => JSON.stringify([r.result.flags, r.result.conditional,
      r.result.error, r.result.qty_preserve_gp_label, r.result.qty_preserve_revenue_label])).join(' ')
      + rk.objective_label + rk.comparison_basis_source;
    ['factor', 'sell-out', 'sellout', 'street', 'wallet', 'Mode A', 'Mode B'
    ].forEach(word => {
      assert.ok(text.toLowerCase().indexOf(word.toLowerCase()) < 0,
        `the wording contains "${word}"`);
    });
    return 'no factor, no street, no wallet, no audience labels';
  });

/* ---------------------------------------------------------------------------
   Contract and identity
   --------------------------------------------------------------------------- */

test('FIN-00a', 'Every field the engine returns is declared in the shared contract', () => {
  const r = calc({ price_after: 90 });
  const undeclared = Object.keys(r).filter(k => contracts.RESULT_FIELDS.indexOf(k) < 0);
  assert.equal(undeclared.length, 0, `undeclared result fields: ${undeclared.join(', ')}`);
  const missing = contracts.RESULT_FIELDS.filter(k => !(k in r));
  assert.equal(missing.length, 0, `declared fields never returned: ${missing.join(', ')}`);
  return `${Object.keys(r).length} returned fields, all declared, none missing`;
});

test('FIN-00b', 'Every field the input validator reads is declared in the shared contract', () => {
  const scenario = { price_before: 100, price_after: 90, quantity_before: 100,
    quantity_after: 120, quantity_label: 'manual scenario', scope: 'all', pack_size: 1,
    cost_eur: 60, cost_basis_id: 'SEP26', support_eur: 0, evidence_period: 'synthetic',
    offer_effective_date: '2026-10-01' };
  Object.keys(scenario).forEach(k =>
    assert.ok(contracts.SCENARIO_FIELDS.indexOf(k) >= 0, `undeclared scenario field ${k}`));
  const r = engine.calculate(scenario);
  assert.equal(r.cost_basis_id, 'SEP26');
  assert.equal(r.evidence_period, 'synthetic');
  assert.equal(r.offer_effective_date, '2026-10-01');
  return 'declared scenario fields are carried onto the result';
});

test('FIN-00c', 'The exported names the existing callers use are still present', () => {
  ['v03run', 'v03rank', 'v03both', 'v03baseline', 'v03costForDate', 'v03costRecord',
   'v03priceAfter', 'v03quantityAfter', 'v03fmtNum', 'v03fmtPct'].forEach(n =>
    assert.equal(typeof engine[n], 'function', `${n} is missing`));
  assert.equal(typeof engine.PricingEngine, 'undefined');
  return 'ten v03 names kept as aliases';
});

restrictedTest(['ITUK-PADS', 'IMOTORS-CABIN', 'ITUK-TURBO', 'ITUK-DISCS', 'IMOTORS-OIL'],
  'FIN-00d', 'A historical profit is never built on a forward cost', () => {
    let checked = 0;
    payload.cases.forEach(c => {
      const hist = engine.costRecord(payload, c.pn, 'HIST');
      if (!hist) return;                                  /* no named historical basis here */
      const forward = engine.v03bases().filter(b => b.status === 'forward')
        .map(b => engine.costRecord(payload, c.pn, b.basis_id))
        .filter(Boolean);
      assert.equal(hist.status, 'historical');
      assert.ok(forward.length > 0, `${c.id} has a historical cost but no forward one`);
      forward.forEach(f => assert.notEqual(hist.cost_eur, f.cost_eur,
        `${c.id}: the historical cost equals the ${f.basis_id} forward cost`));

      const r = engine.calculate({ price_before: 85.91, price_after: 85.91, quantity_before: 1400,
        quantity_after: 1400, cost_eur: hist.cost_eur, cost_basis_id: 'HIST', support_eur: 0,
        scope: 'all', quantity_label: 'observed history' });
      approx(r.gp_before, 1400 * (85.91 - hist.cost_eur));
      assert.equal(r.cost_basis_id, 'HIST');
      checked += 1;
    });
    assert.ok(checked > 0, 'no case carried a named historical basis');
    return `${checked} cases: HIST used for the historical profit, never a forward cost`;
  });

/* ---------------------------------------------------------------------------
   Report
   --------------------------------------------------------------------------- */

const summary = { pass: results.filter(r => r.status === 'PASS').length,
  fail: results.filter(r => r.status === 'FAIL').length,
  skip: results.filter(r => r.status === 'SKIP').length,
  total: results.length };
for (const r of results) {
  console.log(`${r.status} ${r.id}: ${r.name}`
    + (r.status === 'PASS'
       ? (r.evidence ? '  [' + r.evidence + ']' : '')
       : '  --  ' + r.evidence));
}
console.log('');
console.log('payload: ' + payloadPath);
console.log(JSON.stringify(summary));
process.exitCode = summary.fail ? 1 : 0;
