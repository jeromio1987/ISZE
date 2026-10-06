#!/usr/bin/env node
/* ===========================================================================
   ACCEPT-01 independent verification (Verification reviewer).

   How to run
     node --test tests/accept_01_independent.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (ACCEPT-01):
     E1  Each applicable v03 defect is closed by reproducible evidence or
         remains explicitly failing/unaccepted.
     E2  No assertion, fixture value or measurement label is weakened merely
         to make a green report.

   Independent arithmetic only. Expected numbers are computed in this file
   (margin as Jerome uses it: 35% margin means sales / 0.65 for the cost side).
   The engine is called for the observed result, never to produce the expected
   figure. Synthetic inputs only. Restricted payload figures are never copied.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const engine = require(join(ROOT, 'src', 'engine', 'engine.js'));

const EPS = 1e-9;

/** Own arithmetic — not an engine helper. */
function expectAllVolume(p0, p1, q0, q1, cost, support) {
  const revenue_before = p0 * q0;
  const revenue_after = p1 * q1;
  const gp_before = revenue_before - cost * q0;
  const gp_after = revenue_after - cost * q1 - support;
  const margin_after_pct = revenue_after === 0 ? null : (100 * gp_after) / revenue_after;
  const margin_unit_after_pct = p1 === 0 ? null : (100 * (p1 - cost)) / p1;
  return {
    revenue_before, revenue_after, gp_before, gp_after,
    margin_after_pct, margin_unit_after_pct,
    revenue_change: revenue_after - revenue_before,
    gp_change: gp_after - gp_before
  };
}

/** Own arithmetic for incremental scope (existing at old price, added at new). */
function expectIncremental(p0, p1, q0, q1, cost, support) {
  const existing = q0;
  const added = q1 - q0;
  const revenue_before = p0 * q0;
  const revenue_after = p0 * existing + p1 * added;
  const gp_before = revenue_before - cost * q0;
  const gp_after = revenue_after - cost * q1 - support;
  const margin_after_pct = revenue_after === 0 ? null : (100 * gp_after) / revenue_after;
  const margin_unit_after_pct = p1 === 0 ? null : (100 * (p1 - cost)) / p1;
  return {
    revenue_before, revenue_after, gp_before, gp_after,
    margin_after_pct, margin_unit_after_pct
  };
}

test('ACCEPT-01 E1: Applicable v03 defects closed by independent arithmetic, or remain explicitly failing', () => {
  /* --- Closed defects, recomputed in this file --- */

  // Unchanged all-volume: price 100, qty 100, cost 60 → rev 10000, gp 4000, margin 40%.
  {
    const exp = expectAllVolume(100, 100, 100, 100, 60, 0);
    const r = engine.calculate({
      price_before: 100, price_after: 100, quantity_before: 100, quantity_after: 100,
      cost_eur: 60, support_eur: 0, scope: 'all', quantity_label: 'manual scenario'
    });
    assert.equal(r.ok, true);
    assert.ok(Math.abs(r.revenue_after - exp.revenue_after) < EPS, 'revenue_after');
    assert.ok(Math.abs(r.gp_after - exp.gp_after) < EPS, 'gp_after');
    assert.ok(Math.abs(r.margin_after_pct - exp.margin_after_pct) < EPS, 'margin_after_pct');
  }

  // Support deducted once → 35% offer margin (gp 3500 / rev 10000).
  // Jerome: 35% margin => factor 0.65 (SP = cost / 0.65; cost side of sales = sales * 0.65).
  {
    const sales = 100 * 100;
    const support = 500;
    const cost = 60;
    const costSide = cost * 100 + support; // 6500
    assert.ok(Math.abs(costSide - sales * 0.65) < EPS, 'cost side = sales * 0.65 at 35% margin');
    assert.ok(Math.abs((cost * 100) / 0.65 - 6000 / 0.65) < EPS, 'SP from cost uses / 0.65');
    const exp = expectAllVolume(100, 100, 100, 100, cost, support);
    assert.ok(Math.abs(exp.margin_after_pct - 35) < EPS, 'expected 35% from own arithmetic');
    assert.ok(Math.abs(exp.gp_after - 3500) < EPS, 'expected gp 3500');
    const r = engine.calculate({
      price_before: 100, price_after: 100, quantity_before: 100, quantity_after: 100,
      cost_eur: cost, support_eur: support, scope: 'all', quantity_label: 'manual scenario'
    });
    assert.ok(Math.abs(r.gp_after - 3500) < EPS, 'engine gp_after vs own 3500');
    assert.ok(Math.abs(r.margin_after_pct - 35) < EPS, 'engine margin vs own 35%');
  }

  // Incremental: combined margin = gp/revenue, not unit margin on the discounted units.
  {
    const exp = expectIncremental(100, 80, 100, 120, 60, 0);
    // Own: rev = 100*100 + 80*20 = 11600; gp = 11600 - 60*120 = 4400; margin = 4400/11600*100
    assert.ok(Math.abs(exp.revenue_after - 11600) < EPS);
    assert.ok(Math.abs(exp.gp_after - 4400) < EPS);
    const r = engine.calculate({
      price_before: 100, price_after: 80, quantity_before: 100, quantity_after: 120,
      cost_eur: 60, support_eur: 0, scope: 'incremental', quantity_label: 'manual scenario'
    });
    assert.ok(Math.abs(r.revenue_after - exp.revenue_after) < EPS, 'incremental revenue');
    assert.ok(Math.abs(r.gp_after - exp.gp_after) < EPS, 'incremental gp');
    assert.ok(Math.abs(r.margin_after_pct - exp.margin_after_pct) < EPS, 'combined margin');
    assert.ok(Math.abs(r.margin_after_pct - r.margin_unit_after_pct) > 1e-6,
      'combined margin must not collapse to unit margin');
  }

  // Missing cost: revenue stated, profit not invented.
  {
    const r = engine.calculate({
      price_before: 100, price_after: 100, quantity_before: 100, quantity_after: 100,
      cost_eur: null, support_eur: 0, scope: 'all', quantity_label: 'manual scenario'
    });
    assert.ok(Math.abs(r.revenue_after - 10000) < EPS);
    assert.equal(r.gp_after, null);
    assert.equal(r.margin_after_pct, null);
  }

  /* --- Explicitly unaccepted: R27 still fails on the authorised payload --- */
  const payloadPath = join(ROOT, 'payload', 'aim_payload_20260922.json');
  assert.ok(fs.existsSync(payloadPath), 'authorised payload missing in worktree');
  const data = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));
  const fields = Object.keys((data.candidateScreen && data.candidateScreen[0]) || {});
  const hasPeriod = fields.some((k) => /^(period|reporting_period|year|date_from|period_start)$/.test(k));
  assert.equal(hasPeriod, false,
    'R27 must remain explicitly failing/unaccepted: candidate rows still lack a period field; '
    + 'fields=' + fields.join(','));
});

test('ACCEPT-01 E2: No assertion, fixture value or measurement label is weakened for a green report', () => {
  /* Measurement label: margin_after_pct is the offer margin (gp / revenue),
     not the unit factor (1 - cost/price). A weakened green would accept the
     unit figure under the offer-margin label. */
  const p0 = 100, p1 = 80, q0 = 100, q1 = 120, cost = 60, support = 1000;
  const exp = expectIncremental(p0, p1, q0, q1, cost, support);
  // Own: rev 11600, gp = 11600 - 7200 - 1000 = 3400, combined margin = 3400/11600*100
  const unitMarginPct = (100 * (p1 - cost)) / p1; // 25
  assert.ok(Math.abs(exp.gp_after - 3400) < EPS, 'own gp');
  assert.ok(Math.abs(exp.margin_after_pct - (100 * 3400) / 11600) < EPS, 'own combined %');
  assert.ok(Math.abs(exp.margin_after_pct - unitMarginPct) > 1, 'own figures distinguish labels');

  const r = engine.calculate({
    price_before: p0, price_after: p1, quantity_before: q0, quantity_after: q1,
    cost_eur: cost, support_eur: support, scope: 'incremental', quantity_label: 'manual scenario'
  });
  assert.ok(Math.abs(r.margin_after_pct - exp.margin_after_pct) < EPS,
    'margin_after_pct must match combined gp/revenue, not a weakened unit figure');
  assert.ok(Math.abs(r.margin_unit_after_pct - unitMarginPct) < EPS,
    'unit margin is labelled separately');
  assert.notEqual(r.margin_after_pct, r.margin_unit_after_pct,
    'labels must not be collapsed to one number to pass');

  /* Fixture values stay absolute constants (not taken from the engine then re-asserted). */
  const FIXED_REV = 11600;
  const FIXED_GP = 3400;
  assert.equal(FIXED_REV, 100 * 100 + 80 * 20);
  assert.equal(FIXED_GP, FIXED_REV - 60 * 120 - 1000);
  assert.ok(Math.abs(r.revenue_after - FIXED_REV) < EPS);
  assert.ok(Math.abs(r.gp_after - FIXED_GP) < EPS);

  /* R27 is not deleted or flipped green: the same undeclared-period fact stands. */
  const payloadPath = join(ROOT, 'payload', 'aim_payload_20260922.json');
  const data = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));
  const row0 = data.candidateScreen[0] || {};
  assert.equal(Object.prototype.hasOwnProperty.call(row0, 'period'), false);
  assert.equal(Object.prototype.hasOwnProperty.call(row0, 'reporting_period'), false);
  assert.equal(Object.prototype.hasOwnProperty.call(row0, 'year'), false);
});
