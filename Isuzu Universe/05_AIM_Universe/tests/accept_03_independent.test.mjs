#!/usr/bin/env node
/* ===========================================================================
   ACCEPT-03 independent verification (Verification reviewer).

   How to run
     node --test tests/accept_03_independent.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (ACCEPT-03):
     E1  Half-year, national/dealer, annual/monthly and shared-applicability
         fixtures cannot inflate or mislabel results.
     E2  Identical re-import, declared replacement and two genuine same-value
         transactions behave differently and correctly.

   Synthetic figures only. Different numbers from accept_03_conservation.cjs
   fixtures so a blind spot in that suite is not silently reused. Expected
   counts are computed in this file, not read back from the store first.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const cand = require(join(ROOT, 'src', 'data', 'candidates.js'));
const evidence = require(join(ROOT, 'src', 'data', 'evidence.js'));

/* Independent fixtures — not the U11 horizon / two-purchase files. */
const HALF = { period: 'H1-2027', sales_stage: 'billed to distributor', unit: 'each', entity: 'ITUK', quantity: 7, price: 9 };
const ANNUAL = { period: 'CY-2026', sales_stage: 'billed to distributor', unit: 'each', entity: 'ITUK', quantity: 7, price: 9 };
const MONTHLY = { period: '2027-03', sales_stage: 'billed to distributor', unit: 'each', entity: 'ITUK', quantity: 7, price: 9 };
const NATIONAL = { period: 'H1-2027', sales_stage: 'billed to distributor', unit: 'each', entity: 'ITUK', quantity: 7, price: 9 };
const DEALER = { period: 'H1-2027', sales_stage: 'sold to dealer', unit: 'each', entity: 'ITUK-DEALER-9', quantity: 7, price: 9 };
const SHARE_A = { distributor: 'SYNTH-X', part_number: 'SYNTH-U16-SHARE', billed_qty: 3, observed_billing_eur: 27, applicability: 'N75 cabin filter' };
const SHARE_B = { distributor: 'SYNTH-Y', part_number: 'SYNTH-U16-SHARE', billed_qty: 5, observed_billing_eur: 45, applicability: 'N75 cabin filter' };

test('ACCEPT-03 E1: Half-year, national/dealer, annual/monthly and shared-applicability cannot inflate or mislabel', () => {
  const halfVsAnnual = evidence.comparability(HALF, ANNUAL);
  assert.equal(halfVsAnnual.ok, false, 'half-year vs annual must not align');
  assert.match(halfVsAnnual.statement || halfVsAnnual.findings?.join(' ') || JSON.stringify(halfVsAnnual), /different periods/i);

  const annualVsMonthly = evidence.comparability(ANNUAL, MONTHLY);
  assert.equal(annualVsMonthly.ok, false, 'annual vs monthly must not align');
  assert.match(String(annualVsMonthly.statement || (annualVsMonthly.findings || []).join(' ')), /different periods/i);

  const nationalVsDealer = evidence.comparability(NATIONAL, DEALER);
  assert.equal(nationalVsDealer.ok, false, 'billed to distributor vs sales to dealer must not align');
  const ndText = String(nationalVsDealer.statement || (nationalVsDealer.findings || []).join(' '));
  assert.match(ndText, /sales stage|dealer|distributor/i);

  /* Own expected totals for shared applicability: 3+5 units, 27+45 euro — two rows. */
  const EXPECT_UNITS = 3 + 5;
  const EXPECT_EUR = 27 + 45;
  const ds = cand.makeDataset('synthetic-u16-e1', {});
  ds.upsert('alpha', [SHARE_A, SHARE_B], {});
  const held = ds.all();
  assert.equal(held.length, 2, 'shared applicability across two distributors stays two rows');
  const units = held.reduce((s, r) => s + Number(r.record.billed_qty), 0);
  const euro = held.reduce((s, r) => s + Number(r.record.observed_billing_eur), 0);
  assert.equal(units, EXPECT_UNITS, 'units must not inflate beyond 3+5');
  assert.equal(euro, EXPECT_EUR, 'euro must not inflate beyond 27+45');

  /* Period labels stay as declared — no relabel of H1 into a calendar year. */
  assert.equal(evidence.describePeriod(HALF).value, 'H1-2027');
  assert.equal(evidence.describePeriod(ANNUAL).value, 'CY-2026');
  assert.equal(evidence.describePeriod(MONTHLY).value, '2027-03');
});

test('ACCEPT-03 E2: Identical re-import, declared replacement, and two genuine same-value purchases differ correctly', () => {
  const same = { distributor: 'SYNTH-Z', part_number: 'SYNTH-U16-P', billed_qty: 7, observed_billing_eur: 49 };

  /* Identical re-import of the same section folds — expected independently: 1 row. */
  const dsRepeat = cand.makeDataset('synthetic-u16-e2a', {});
  const first = dsRepeat.upsert('alpha', [same], {});
  const repeat = dsRepeat.upsert('alpha', [same], {});
  assert.equal(dsRepeat.all().length, 1, 'rows after identical re-import');
  assert.equal(first.counts.added, 1);
  assert.equal(repeat.counts.unchanged, 1);
  assert.equal(repeat.counts.added, 0);

  /* Declared replacement keeps one row at the corrected quantity (own expectation: 5). */
  const dsReplace = cand.makeDataset('synthetic-u16-e2b', {});
  dsReplace.upsert('alpha', [same], {});
  const key = dsReplace.all()[0].key;
  const declared = dsReplace.correct('alpha', key,
    Object.assign({}, same, { billed_qty: 5, observed_billing_eur: 35 }),
    { corrects_revision: 1, reason: 'U16 independent declared replacement of a mistyped quantity' });
  assert.equal(declared.ok, true, 'declared replacement accepted');
  assert.equal(dsReplace.all().length, 1, 'declared replacement still one row');
  assert.equal(dsReplace.all()[0].record.billed_qty, 5, 'held quantity is the replacement');
  assert.equal(dsReplace.all()[0].record.observed_billing_eur, 35);

  /* Two genuine same-value purchases on different invoice sections: own expectation 2 rows / 14 units. */
  const buy1 = Object.assign({}, same, { purchase_id: 'U16-INV-1' });
  const buy2 = Object.assign({}, same, { purchase_id: 'U16-INV-2' });
  const EXPECT_ROWS = 2;
  const EXPECT_QTY = 7 + 7;
  const dsTwo = cand.makeDataset('synthetic-u16-e2c', {});
  const a = dsTwo.upsert('invoice-1', [buy1], {});
  const b = dsTwo.upsert('invoice-2', [buy2], {});
  const held = dsTwo.all().length;
  const qty = dsTwo.all().reduce((s, r) => s + Number(r.record.billed_qty), 0);
  assert.equal(held, EXPECT_ROWS,
    'two genuine same-value purchases must stay two rows; held=' + held
    + ' added1=' + a.counts.added + ' added2=' + b.counts.added
    + ' replaced2=' + b.counts.replaced);
  assert.equal(qty, EXPECT_QTY, 'qty must be 7+7=14, not collapsed');
});
