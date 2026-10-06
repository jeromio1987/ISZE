#!/usr/bin/env node
/* RANGE-06: price-up and price-down investigations with arithmetic thresholds. */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));
const FIX = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/range_06_price_direction.json'), 'utf8'));

test('RANGE-06 E1: a price increase can improve unit profit while total profit falls under the stated quantity scenario', () => {
  assert.equal(typeof evidence.rangePriceDirection, 'function',
    'AIMEvidence.rangePriceDirection is missing');
  const view = evidence.rangePriceDirection(FIX.price_up_with_volume_loss);
  assert.equal(view.direction, 'price_up');
  assert.ok(view.unit_profit_after_eur > view.unit_profit_before_eur,
    'unit profit did not rise after the price increase');
  assert.ok(view.total_profit_after_eur < view.total_profit_before_eur,
    'total profit did not fall under the stated quantity loss');
  assert.ok(view.tolerable_quantity_loss_units !== null);
  assert.ok(view.required_extra_volume_units !== null);
  assert.match(view.statement, /unit profit|total profit|quantity/i);
  assert.equal(/proven|lost sales|factor\s*0\./i.test(view.statement), false);
});

test('RANGE-06 E2: no unsupported part is labelled underpriced merely to populate a price-up example', () => {
  const view = evidence.rangePriceDirection(FIX.no_underpriced_evidence);
  assert.equal(view.labelled_underpriced, false);
  assert.notEqual(view.price_action_count, 5);
  assert.ok(view.price_action_count <= 2);
  assert.match(view.statement, /not labelled underpriced|no evidence|underpriced/i);
});
