#!/usr/bin/env node
/* RANGE-03: multi-part basket with eligibility and partial profit. */
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import fs from 'node:fs';

const require = createRequire(import.meta.url);
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidence = require(path.join(ROOT, 'src/data/evidence.js'));
const FIX = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/range_03_basket.json'), 'utf8'));

test('RANGE-03 E1: the basket result reconciles exactly to its eligible line results', () => {
  assert.equal(typeof evidence.rangeBasket, 'function', 'AIMEvidence.rangeBasket is missing');
  const basket = evidence.rangeBasket(FIX.lines_complete);
  assert.equal(basket.state, 'complete');
  assert.equal(basket.currency, 'EUR');
  assert.equal(basket.eligible_line_count, 2);
  assert.equal(basket.excluded_line_count, 1);

  const eligible = FIX.lines_complete.filter((l) => l.eligible);
  const expectedRevenue = eligible.reduce((s, l) => s + l.quantity * l.price_eur, 0);
  const expectedProfit = eligible.reduce((s, l) => s + l.quantity * (l.price_eur - l.cost_eur), 0);
  assert.equal(basket.revenue_eur, Math.round(expectedRevenue * 100) / 100);
  assert.equal(basket.profit_eur, Math.round(expectedProfit * 100) / 100);

  const lineRev = basket.lines.filter((l) => l.eligible).reduce((s, l) => s + l.revenue_eur, 0);
  const lineProfit = basket.lines.filter((l) => l.eligible).reduce((s, l) => s + l.profit_eur, 0);
  assert.equal(basket.revenue_eur, Math.round(lineRev * 100) / 100);
  assert.equal(basket.profit_eur, Math.round(lineProfit * 100) / 100);
  assert.equal(basket.lines.some((l) => l.original_reference === '899999-SKIP' && l.eligible === false), true);
  assert.equal(/proven|lost sales|factor\s*0\./i.test(basket.statement), false);
});

test('RANGE-03 E2: a missing cost on one material line makes basket profit partial and keeps known line facts', () => {
  const basket = evidence.rangeBasket(FIX.lines_missing_cost);
  assert.equal(basket.profit_state, 'partial');
  assert.equal(basket.profit_eur, null);
  assert.ok(basket.revenue_eur !== null);
  const known = basket.lines.find((l) => l.original_reference === '898240-9990');
  assert.equal(known.cost_eur, 6.1);
  assert.equal(known.revenue_eur, 172);
  assert.equal(known.profit_eur, 111);
  const missing = basket.lines.find((l) => l.original_reference === '898240-BVP1');
  assert.equal(missing.cost_eur, null);
  assert.equal(missing.profit_eur, null);
  assert.match(basket.statement, /partial|missing cost/i);
  assert.equal(/proven|lost sales/i.test(basket.statement), false);
});

test('RANGE-03 E3: basket totals never mix currencies', () => {
  const basket = evidence.rangeBasket(FIX.lines_mixed_currency);
  assert.equal(basket.state, 'currency_mixed');
  assert.equal(basket.revenue_eur, null);
  assert.equal(basket.profit_eur, null);
  assert.match(basket.statement, /currency|not mixed|same currency/i);
  assert.ok(Array.isArray(basket.currencies_seen));
  assert.ok(basket.currencies_seen.includes('EUR') && basket.currencies_seen.includes('GBP'));
  // Per-line facts remain
  assert.equal(basket.lines.length, 2);
  assert.equal(basket.lines[0].revenue_eur, 172);
});
