#!/usr/bin/env node
/* ===========================================================================
   MARKET-02 acceptance tests: product equivalence separate from lexical similarity.

   How to run
     node --test tests/market_02_equivalence.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (MARKET-02):
     E1  A housing and element, or incomplete kit and full kit, do not form an
         accepted price comparison.
     E2  Rejected and unresolved evidence stays traceable and is excluded from
         the eligible comparison.

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
    observed_date: '2026-09-20',
    amount_scope: 'per_piece',
    currency: 'EUR',
    unit: 'piece',
    tax: 'excluded',
    vat_rate: 0,
    vat_rate_unit: 'percent',
    delivery_included: true,
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

test('MARKET-02 E1: A housing and element, or incomplete kit and full kit, do not form an accepted price comparison', () => {
  const housingVsElement = market.productMatchGate(synth({
    observation_id: 'HOUSING-V-ELEMENT',
    amount: 40,
    amount_scope: 'per_pack',
    pack: { contents: [{ part: 'housing', quantity: 1 }], contents_equivalent: false, unit: 'piece' },
    match: { status: 'unresolved', basis: 'lexical_family_only' }
  }));
  assert.equal(housingVsElement.accepted_price_comparison, false);
  assert.ok(
    housingVsElement.reason_codes.includes('KIT_CONTENTS_NOT_EQUIVALENT')
    || housingVsElement.reason_codes.includes('PRODUCT_MATCH_UNRESOLVED'),
    'housing vs element must not be an accepted comparison: ' + JSON.stringify(housingVsElement)
  );

  const incompleteKit = market.productMatchGate(synth({
    observation_id: 'INCOMPLETE-KIT',
    amount: 55,
    amount_scope: 'per_pack',
    pack: {
      contents: [{ part: 'pad', quantity: 2 }],
      declared_complete_kit: false,
      contents_equivalent: false,
      unit: 'piece'
    },
    match: { status: 'documented_candidate', basis: 'seller_cross_ref' }
  }));
  assert.equal(incompleteKit.accepted_price_comparison, false);

  const panel = comparable.panel(CTX, [
    synth({
      observation_id: 'HOUSING-V-ELEMENT',
      amount: 40,
      amount_scope: 'per_pack',
      pack: { contents: [{ part: 'housing', quantity: 1 }], contents_equivalent: false, unit: 'piece' },
      match: { status: 'unresolved', basis: 'lexical_family_only' }
    })
  ], BASE);
  const row = rowById(panel, 'HOUSING-V-ELEMENT');
  assert.equal(panel.eligible_offers.length, 0);
  assert.ok(
    codesOf(row).includes('KIT_CONTENTS_NOT_EQUIVALENT')
    || codesOf(row).includes('PRODUCT_MATCH_UNRESOLVED'),
    'panel must exclude housing/element: ' + JSON.stringify(codesOf(row))
  );
});

test('MARKET-02 E2: Rejected and unresolved evidence stays traceable and is excluded from the eligible comparison', () => {
  const rejected = synth({
    observation_id: 'REJ-1',
    amount: 9,
    match: { status: 'rejected', basis: 'reviewer_rejected', reviewer: 'role: source owner' }
  });
  const unresolved = synth({
    observation_id: 'UNRES-1',
    amount: 11,
    match: { status: 'unresolved', basis: 'seller_cross_ref' }
  });
  const accepted = synth({
    observation_id: 'OK-1',
    amount: 12,
    match: { status: 'accepted', basis: 'exact_part_number' }
  });

  const view = market.matchTraceView({
    observations: [rejected, unresolved, accepted],
    panel: comparable.panel(CTX, [rejected, unresolved, accepted], BASE)
  });

  assert.ok(view.traceable_ids.includes('REJ-1'));
  assert.ok(view.traceable_ids.includes('UNRES-1'));
  assert.ok(view.excluded_ids.includes('REJ-1'));
  assert.ok(view.excluded_ids.includes('UNRES-1'));
  assert.ok(view.eligible_ids.includes('OK-1'));
  assert.ok(!view.eligible_ids.includes('REJ-1'));
  assert.ok(!view.eligible_ids.includes('UNRES-1'));

  const rej = rowById(view.panel, 'REJ-1');
  const un = rowById(view.panel, 'UNRES-1');
  assert.equal(rej.visible, true);
  assert.equal(un.visible, true);
  assert.ok(codesOf(rej).length > 0 || rej.reason);
  assert.ok(codesOf(un).includes('PRODUCT_MATCH_UNRESOLVED') || /unresolved/i.test(un.reason || ''));
});
