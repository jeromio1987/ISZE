#!/usr/bin/env node
/* RANGE-02: exact Genuine/BVP comparison view. */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));

const FIX = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/range_02_exact_pair.json'), 'utf8'));

test('RANGE-02 E1: the comparison always names two distinct actual references or states counterpart unresolved', () => {
  assert.equal(typeof evidence.exactRangeComparison, 'function',
    'AIMEvidence.exactRangeComparison is missing');
  const ok = evidence.exactRangeComparison(FIX.cases[0]);
  assert.equal(ok.state, 'exact');
  assert.ok(ok.reference_a && ok.reference_b);
  assert.notEqual(ok.reference_a, ok.reference_b);
  assert.match(ok.statement, /two distinct|Genuine|BVP/i);

  const unresolved = evidence.exactRangeComparison(FIX.cases[1]);
  assert.equal(unresolved.state, 'counterpart_unresolved');
  assert.equal(unresolved.reference_b, null);
  assert.match(unresolved.statement, /counterpart unresolved|unresolved/i);
});

test('RANGE-02 E2: reference prices, actual prices and application status cannot be confused by labels', () => {
  const view = evidence.exactRangeComparison(FIX.cases[0], { audience: 'internal' });
  assert.ok(view.labels);
  assert.equal(view.labels.reference_price, 'Reference price');
  assert.equal(view.labels.actual_price, 'Actual price');
  assert.equal(view.labels.application_status, 'Application status');
  assert.notEqual(view.labels.reference_price, view.labels.actual_price);
  assert.ok(view.side_a.reference_price_eur !== undefined);
  assert.ok(view.side_a.actual_price_eur !== undefined);
  assert.ok(view.side_a.application_status);
  // cost only internal
  assert.ok(view.side_a.cost_eur !== null && view.side_a.cost_eur !== undefined);
  const external = evidence.exactRangeComparison(FIX.cases[0], { audience: 'external' });
  assert.equal(external.side_a.cost_eur, null);
  assert.match(external.cost_statement, /internal|not shown|cost/i);
  const htmlBits = [view.labels.reference_price, view.labels.actual_price, view.labels.application_status].join(' ');
  assert.equal(/proven|lost sales|factor\s*0\.|×1\.\d+/i.test(htmlBits), false);
});
