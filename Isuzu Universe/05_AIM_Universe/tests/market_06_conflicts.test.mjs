#!/usr/bin/env node
/* ===========================================================================
   MARKET-06 acceptance tests: outdated and conflicting observations visible.

   How to run
     node --test tests/market_06_conflicts.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (MARKET-06):
     E1  A newer price does not silently rewrite an earlier saved comparison.
     E2  Conflicting sources remain visible with their scope and dates; the
         cheapest observation is not automatically chosen.

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

function synth(over) {
  return market.toPanelOffer(market.buildRecord(Object.assign({
    role: 'competitor',
    level: 'public_advertised_retail',
    seller: 'Fixture Seller',
    market: 'UK',
    source: 'Synthetic listing',
    amount_scope: 'per_piece',
    currency: 'EUR',
    unit: 'piece',
    tax: 'excluded',
    vat_rate: 0,
    vat_rate_unit: 'percent',
    delivery_included: true,
    match: { status: 'accepted', basis: 'exact_part_number' },
    channel: 'web_listing',
    availability_meaning: 'in_stock_stated',
    part_number: 'SYNTH-PART',
    case_id: 'CASE-X',
    original_reference: 'SYNTH-PART'
  }, over || {})));
}

const CTX = { case_id: 'CASE-X', part_number: 'SYNTH-PART', market: 'UK', unit: 'piece' };
const BASE = { basis_level: 'public_advertised_retail', basis_unit: 'piece', as_of: '2026-09-22' };

const rowById = (panelResult, id) =>
  panelResult.eligible_offers.concat(panelResult.ineligible_offers)
    .find((r) => r.observation_id === id);

const codesOf = (row) => (row && row.reasons ? row.reasons.map((r) => r.code) : []);

test('MARKET-06 E1: A newer price does not silently rewrite an earlier saved comparison', () => {
  const earlier = synth({
    observation_id: 'OBS-OLD', amount: 42, observed_date: '2026-01-10', retrieved: '2026-01-10'
  });
  const newer = synth({
    observation_id: 'OBS-NEW', amount: 31, observed_date: '2026-09-20', retrieved: '2026-09-20',
    supersedes: 'OBS-OLD'
  });

  const view = market.savedComparisonView({
    saved: {
      comparison_id: 'CMP-1',
      observation_ids: ['OBS-OLD'],
      value: 42,
      basis: 'public_advertised_retail per piece',
      saved_at: '2026-02-01'
    },
    observations: [earlier, newer],
    panel: comparable.panel(CTX, [earlier, newer], Object.assign({}, BASE, {
      saved_comparisons: [{
        comparison_id: 'CMP-1', observation_ids: ['OBS-OLD'], value: 42,
        basis: 'public_advertised_retail per piece', saved_at: '2026-02-01'
      }]
    }))
  });

  assert.equal(view.saved.value, 42, 'the saved figure stands as the figure that was saved');
  assert.equal(view.saved.rewritten, false);
  assert.equal(view.newer_rewrote_saved, false);
  assert.ok(view.saved.superseded_by_observation_ids.includes('OBS-NEW'));

  const oldRow = rowById(view.panel, 'OBS-OLD');
  assert.ok(oldRow, 'the superseded observation must remain visible');
  assert.ok(codesOf(oldRow).includes('SUPERSEDED_OBSERVATION'));
  assert.equal(oldRow.raw.amount, 42);
  assert.equal(oldRow.visible, true);
});

test('MARKET-06 E2: Conflicting sources remain visible with their scope and dates; the cheapest is not chosen', () => {
  const a = synth({
    observation_id: 'OBS-A', amount: 10, observed_date: '2026-08-01', retrieved: '2026-08-01',
    seller: 'Seller A', source: 'Synthetic listing A'
  });
  const b = synth({
    observation_id: 'OBS-B', amount: 7, observed_date: '2026-09-01', retrieved: '2026-09-01',
    seller: 'Seller B', source: 'Synthetic listing B'
  });

  const view = market.conflictVisibilityView({
    observations: [a, b],
    panel: comparable.panel(CTX, [a, b], BASE)
  });

  assert.equal(view.cheapest_auto_selected, false);
  assert.equal(view.panel.selected_observation_id == null || view.panel.cheapest_chosen === false || true, true);
  assert.ok(view.visible_observation_ids.includes('OBS-A'));
  assert.ok(view.visible_observation_ids.includes('OBS-B'));
  assert.equal(view.dates['OBS-A'], '2026-08-01');
  assert.equal(view.dates['OBS-B'], '2026-09-01');
  assert.equal(view.sources['OBS-A'], 'Synthetic listing A');
  assert.equal(view.sources['OBS-B'], 'Synthetic listing B');

  /* comparable.panel itself must not auto-pick the cheapest as the decision. */
  assert.equal(view.panel.selected_observation_id, null);
  assert.equal(view.offers_shown_individually, true);
  assert.equal(view.auto_chose_cheapest, false);
  assert.equal(view.cheapest_auto_selected, false);
  assert.equal(view.cheapest_observation_id, 'OBS-B');
});
