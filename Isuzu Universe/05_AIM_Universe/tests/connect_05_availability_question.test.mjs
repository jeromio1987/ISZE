#!/usr/bin/env node
/* ===========================================================================
   CONNECT-05 acceptance tests: Create a dated availability question and response.

   How to run
     node --test tests/connect_05_availability_question.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A historical purchase cannot be displayed as current stock availability.
     E2  A response without confirmation is labelled an estimate and retains the
         next-update obligation.

   Synthetic fixtures only. No real stock files, no send, no invented dealer stock.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const mod = require(join(ROOT, 'src', 'data', 'availability_question.js'));

const CASE0 = {
  case_id: 'SYN-CASE-AVAIL-01',
  part_number: 'SYN-PN-AVAIL',
  application: 'Synthetic N75 brake disc',
  availability_questions: []
};

test('CONNECT-05 E1: A historical purchase cannot be displayed as current stock availability.', () => {
  const opened = mod.createAvailabilityQuestion(CASE0, {
    part_number: 'SYN-PN-AVAIL',
    application: 'Synthetic N75 brake disc',
    quantity: 4,
    required_date: '2026-11-01',
    distributor_route: 'Synthetic distributor'
  }, {
    question_id: 'AQ-1',
    asked_at: '2026-10-06T10:00:00Z',
    asked_by: 'synthetic_analyst'
  });
  assert.equal(opened.ok, true);

  const withHistory = mod.recordHistoricalPurchase(opened.case_record, {
    part_number: 'SYN-PN-AVAIL',
    purchased_on: '2025-03-12',
    quantity: 2,
    source: 'synthetic_billing_history',
    observation_time: '2026-10-06T10:05:00Z',
    meaning: 'historical_purchase'
  });
  assert.equal(withHistory.ok, true);

  const view = mod.currentStockAvailability(withHistory.case_record, {
    part_number: 'SYN-PN-AVAIL',
    as_of: '2026-10-06'
  });

  assert.equal(view.ok, true);
  assert.equal(view.shows_as_current_stock, false);
  assert.equal(view.historical_purchase_count, 1);
  assert.ok(
    (view.statement || '').toLowerCase().includes('historical')
      || (view.statement || '').toLowerCase().includes('not current'),
    'statement must refuse to present history as current stock'
  );
  assert.equal(view.available_quantity, null);
  assert.ok(
    !view.rows || view.rows.every(function (r) {
      return r.meaning !== 'historical_purchase' || r.displayed_as_current_stock !== true;
    }),
    'no historical purchase row may be flagged as current stock'
  );
});

test('CONNECT-05 E2: A response without confirmation is labelled an estimate and retains the next-update obligation.', () => {
  const opened = mod.createAvailabilityQuestion(CASE0, {
    part_number: 'SYN-PN-AVAIL',
    application: 'Synthetic N75 brake disc',
    quantity: 4,
    required_date: '2026-11-01',
    distributor_route: 'Synthetic distributor'
  }, {
    question_id: 'AQ-2',
    asked_at: '2026-10-06T11:00:00Z'
  });
  assert.equal(opened.ok, true);

  const answered = mod.recordAvailabilityResponse(opened.case_record, 'AQ-2', {
    source: 'synthetic_distributor_reply',
    observation_time: '2026-10-06T12:00:00Z',
    confirmed: false,
    date_value: '2026-10-20',
    claimed_meaning: 'confirmed_commitment',
    next_update_due: '2026-10-13'
  });

  assert.equal(answered.ok, true);
  const q = answered.question;
  assert.equal(q.response.meaning, 'estimated_date');
  assert.equal(q.response.label, 'estimate');
  assert.equal(q.response.confirmed, false);
  assert.equal(q.response.next_update_due, '2026-10-13');
  assert.equal(q.response.next_update_obligation, true);
  assert.notEqual(q.response.meaning, 'confirmed_commitment');
  assert.ok(
    ['estimated_date', 'confirmed_commitment', 'allocated', 'dispatched', 'delivered']
      .indexOf(q.response.meaning) >= 0
  );
});
