#!/usr/bin/env node
/* ===========================================================================
   MARKET-07 acceptance tests: comparable-price panel with clear exclusions.

   How to run
     node --test tests/market_07_panel.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (MARKET-07):
     E1  Removing an ineligible pack/market/price-level observation does not
         alter the raw evidence record.
     E2  No price action is certified from an index alone; missing like-for-like
         evidence remains explicit.

   Synthetic figures only. The restricted payload is never read here.
   Pattern: tests/market_evidence.test.mjs (same panel contract).
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');
const comparable = require(join(ROOT, 'src', 'data', 'comparable.js'));

function cleanOffer(over) {
  return Object.assign({
    observation_id: 'OBS-A',
    role: 'competitor',
    level: 'public_advertised_retail',
    seller: 'Seller A',
    market: 'UK',
    retrieved: '2026-09-20',
    source_reference: 'synthetic listing',
    part_number: 'SYNTH-PART',
    case_id: 'CASE-X',
    amount: 12,
    amount_scope: 'per_piece',
    currency: 'EUR',
    unit: 'piece',
    pack: null,
    tax: 'excluded',
    vat_rate: 0,
    vat_rate_unit: 'percent',
    delivery_included: true,
    delivery_cost_eur: null,
    fx_to_eur: null,
    fx_date: null,
    match: { status: 'accepted', basis: 'exact_part_number' },
    equivalence: null,
    supersedes: null,
    saved_comparison_id: null
  }, over || {});
}

const CTX = { case_id: 'CASE-X', part_number: 'SYNTH-PART', market: 'UK', unit: 'piece' };
const BASE = { basis_level: 'public_advertised_retail', basis_unit: 'piece', as_of: '2026-09-22' };

const rowById = (panelResult, id) =>
  panelResult.eligible_offers.concat(panelResult.ineligible_offers)
    .find((r) => r.observation_id === id);

test('MARKET-07 E1: Removing an ineligible observation does not alter the raw evidence record', () => {
  const keeps = [
    cleanOffer({ observation_id: 'KEEP-1', amount: 10 }),
    cleanOffer({ observation_id: 'KEEP-2', amount: 20 })
  ];
  const dropped = cleanOffer({ observation_id: 'DROP-1', level: null, amount: 5 });
  const withAll = keeps.concat([dropped]);
  const before = JSON.stringify(withAll);

  const full = comparable.panel(CTX, withAll, BASE);
  const without = comparable.panel(CTX, keeps, BASE);

  assert.equal(JSON.stringify(withAll), before, 'the input array was modified by the panel');
  assert.equal(full.raw_input_unmodified, true);
  assert.equal(without.raw_input_unmodified, true);

  ['KEEP-1', 'KEEP-2'].forEach((id) => {
    assert.equal(JSON.stringify(rowById(full, id).raw), JSON.stringify(rowById(without, id).raw),
      id + ' changed when an unrelated row was removed');
  });

  assert.equal(full.ineligible_offers.length, 1);
  assert.equal(without.ineligible_offers.length, 0);
});

test('MARKET-07 E2: No price action is certified from an index alone; missing like-for-like stays explicit', () => {
  const good = cleanOffer({ observation_id: 'GOOD' });
  const bad = cleanOffer({ observation_id: 'BAD', level: null });

  const linked = comparable.panel(CTX, [good, bad], BASE);
  assert.equal(linked.price_action_certified, false);
  assert.equal(linked.scenario_link.linked, true);
  assert.deepEqual(linked.scenario_link.eligible_observation_ids, ['GOOD']);
  assert.deepEqual(linked.scenario_link.excluded_observation_ids, ['BAD']);

  const unlinked = comparable.panel(CTX, [good], { as_of: '2026-09-22' });
  assert.equal(unlinked.selected_basis, null);
  assert.equal(unlinked.scenario_link.linked, false);
  assert.equal(unlinked.scenario_link.reason_code, 'NO_BASIS_NAMED');
  assert.equal(unlinked.price_positioning.available, false);
  assert.equal(unlinked.price_positioning.index_stated, false);
  assert.match(unlinked.price_positioning.statement, /stays missing and is not filled in/i);
  assert.equal(unlinked.price_action_certified, false);

  const empty = comparable.panel(CTX, [bad], BASE);
  assert.equal(empty.scenario_link.linked, false);
  assert.equal(empty.scenario_link.reason_code, 'NO_ELIGIBLE_COMPARABLE');
  assert.equal(empty.price_action_certified, false);
});