#!/usr/bin/env node
/* ===========================================================================
   MARKET-01 acceptance tests: store dated competitor observations as evidence.

   How to run
     node --test tests/market_01_observation.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (MARKET-01):
     E1  An observation retains source and date through a review and saved case.
     E2  A missing currency or reference remains missing instead of borrowing
         the previous row's values.

   Synthetic fixtures only. The restricted payload is never read here.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const market = require(join(ROOT, 'src', 'data', 'market_observation.js'));
const comparable = require(join(ROOT, 'src', 'data', 'comparable.js'));

test('MARKET-01 E1: An observation retains source and date through a review and saved case', () => {
  const raw = market.buildRecord({
    observation_id: 'OBS-SYNTH-01',
    source: 'Synthetic seller listing (fixture)',
    observed_date: '2026-09-01',
    original_reference: 'SYNTH-PART-01',
    seller: 'Fixture Seller',
    market: 'UK',
    currency: 'EUR',
    tax: 'excluded',
    pack: null,
    channel: 'web_listing',
    availability_meaning: 'in_stock_stated',
    role: 'competitor',
    level: 'public_advertised_retail',
    amount: 12,
    amount_scope: 'per_piece',
    unit: 'piece'
  });

  assert.equal(raw.source, 'Synthetic seller listing (fixture)');
  assert.equal(raw.observed_date, '2026-09-01');
  assert.equal(raw.as_evidence, true);
  assert.equal(raw.as_truth, false);

  const reviewed = market.retainThroughReview(raw, {
    review_id: 'REV-1',
    reviewed_at: '2026-09-15',
    reviewer: 'role: data developer',
    note: 'fixture review only'
  });
  assert.equal(reviewed.source, 'Synthetic seller listing (fixture)',
    'a review must not rewrite the observation source');
  assert.equal(reviewed.observed_date, '2026-09-01',
    'a review must not rewrite the observed date');
  assert.equal(reviewed.source_retained, true);
  assert.equal(reviewed.observed_date_retained, true);
  assert.equal(reviewed.review.review_id, 'REV-1');

  const saved = market.attachToSavedCase(reviewed, {
    case_id: 'CASE-X',
    saved_at: '2026-09-16',
    revision: 1
  });
  assert.equal(saved.source, 'Synthetic seller listing (fixture)',
    'a saved case must keep the same source');
  assert.equal(saved.observed_date, '2026-09-01',
    'a saved case must keep the same observed date');
  assert.equal(saved.saved_case.case_id, 'CASE-X');
  assert.equal(saved.case_id, 'CASE-X');

  /* The panel contract still accepts the mapped offer. */
  const offer = market.toPanelOffer(saved);
  assert.equal(offer.source_reference, saved.source);
  assert.equal(offer.retrieved, saved.observed_date);
  const panel = comparable.panel(
    { case_id: 'CASE-X', part_number: 'SYNTH-PART-01', market: 'UK', unit: 'piece' },
    [offer],
    { basis_level: 'public_advertised_retail', basis_unit: 'piece', as_of: '2026-09-22' }
  );
  assert.ok(panel);
  assert.equal(typeof panel.raw_input_unmodified, 'boolean');
});

test('MARKET-01 E2: A missing currency or reference remains missing instead of borrowing the previous row values', () => {
  const rows = market.buildRecords([
    {
      observation_id: 'FULL-ROW',
      source: 'Fixture A',
      observed_date: '2026-09-01',
      original_reference: 'SYNTH-FULL',
      currency: 'EUR',
      tax: 'excluded',
      seller: 'Seller A',
      market: 'UK',
      channel: 'web_listing',
      availability_meaning: 'in_stock_stated',
      amount: 10
    },
    {
      observation_id: 'SPARSE-ROW',
      source: 'Fixture B',
      observed_date: '2026-09-02',
      original_reference: null,
      currency: null,
      tax: null,
      seller: 'Seller B',
      market: 'UK',
      channel: null,
      availability_meaning: null,
      amount: 20
    }
  ]);

  assert.equal(rows.length, 2);
  assert.equal(rows[0].currency, 'EUR');
  assert.equal(rows[0].original_reference, 'SYNTH-FULL');

  assert.equal(rows[1].currency, null, 'a missing currency stayed missing');
  assert.equal(rows[1].original_reference, null, 'a missing reference stayed missing');
  assert.notEqual(rows[1].currency, rows[0].currency,
    'the sparse row must not borrow EUR from the previous row');
  assert.notEqual(rows[1].original_reference, rows[0].original_reference,
    'the sparse row must not borrow the previous reference');

  assert.ok(rows[1].unknown_fields.includes('currency'));
  assert.ok(rows[1].unknown_fields.includes('original_reference'));
  assert.ok(rows[1].unknown_fields.includes('channel'));
  assert.ok(rows[1].unknown_fields.includes('availability_meaning'));
  assert.equal(rows[1].field_state.currency_known, false);
  assert.equal(rows[1].field_state.original_reference_known, false);

  /* Building the sparse row alone yields the same unknowns: no hidden shared state. */
  const alone = market.buildRecord({
    observation_id: 'SPARSE-ALONE',
    source: 'Fixture B',
    observed_date: '2026-09-02',
    original_reference: null,
    currency: null,
    amount: 20
  });
  assert.equal(alone.currency, null);
  assert.equal(alone.original_reference, null);
});
