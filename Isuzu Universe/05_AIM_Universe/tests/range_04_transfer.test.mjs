#!/usr/bin/env node
/* RANGE-04: transferred business vs new BVP business. */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));
const FIX = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/range_04_transfer.json'), 'utf8'));

test('RANGE-04 E1: a pure one-for-one transfer is not counted as new units or full receiving-line revenue', () => {
  assert.equal(typeof evidence.rangeTransferSplit, 'function',
    'AIMEvidence.rangeTransferSplit is missing');
  const view = evidence.rangeTransferSplit(FIX.pure_transfer);
  assert.equal(view.transferred_units, 40);
  assert.equal(view.new_units, 0);
  assert.equal(view.new_gross_revenue_eur, 0,
    'pure transfer was counted as new gross revenue');
  const receivingFullSales = 40 * FIX.pure_transfer.to_line.price_eur;
  assert.notEqual(view.new_gross_revenue_eur, receivingFullSales);
  assert.equal(view.transfer_revenue_eur, Math.round(receivingFullSales * 100) / 100);
  assert.match(view.statement, /transfer|not new/i);
  assert.equal(/proven|lost sales|factor\s*0\./i.test(view.statement), false);
});

test('RANGE-04 E2: displaced contribution is deducted once after the baseline-versus-proposal basket', () => {
  const view = evidence.rangeTransferSplit(FIX.transfer_plus_new);
  const from = FIX.transfer_plus_new.from_line;
  const unitDisp = from.price_eur - from.cost_eur;
  const expectedOnce = Math.round(40 * unitDisp * 100) / 100;
  assert.equal(view.displaced_contribution_eur, expectedOnce);
  assert.equal(view.displaced_deduction_count, 1,
    'displaced contribution was deducted more than once');
  // Combined contribution change must equal: transfer gain + new gain - displaced (once)
  const to = FIX.transfer_plus_new.to_line;
  const transferGain = Math.round(40 * (to.price_eur - to.cost_eur) * 100) / 100;
  const newGain = Math.round(15 * (to.price_eur - to.cost_eur) * 100) / 100;
  const expectedNet = Math.round((transferGain + newGain - expectedOnce) * 100) / 100;
  assert.equal(view.net_contribution_change_eur, expectedNet);
  // Guard against double-count: if displaced were applied twice, net would be expectedNet - expectedOnce
  assert.notEqual(view.net_contribution_change_eur,
    Math.round((transferGain + newGain - 2 * expectedOnce) * 100) / 100);
  assert.equal(view.new_units, 15);
  assert.equal(view.new_gross_revenue_eur, Math.round(15 * to.price_eur * 100) / 100);
});
