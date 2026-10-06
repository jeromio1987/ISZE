#!/usr/bin/env node
/* ===========================================================================
   MARKET-03 acceptance tests: packs and kit contents only when supported.

   How to run
     node --test tests/market_03_packs.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (MARKET-03):
     E1  A synthetic pack of four and one piece compare correctly when
         equivalence is accepted.
     E2  Unknown pack contents prevent the derived comparable unit price, not
         retention of the original observation.

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
    role: 'competitor', level: 'public_advertised_retail', seller: 'Fixture Seller',
    market: 'UK', source: 'Synthetic listing', observed_date: '2026-09-20',
    amount_scope: 'per_piece', currency: 'EUR', unit: 'piece', tax: 'excluded',
    vat_rate: 0, vat_rate_unit: 'percent', delivery_included: true,
    channel: 'web_listing', availability_meaning: 'in_stock_stated',
    part_number: 'SYNTH-PART', case_id: 'CASE-X', original_reference: 'SYNTH-PART',
    match: { status: 'accepted', basis: 'exact_part_number' }
  }, over || {})));
}

const CTX = { case_id: 'CASE-X', part_number: 'SYNTH-PART', market: 'UK', unit: 'piece' };
const BASE = { basis_level: 'public_advertised_retail', basis_unit: 'piece', as_of: '2026-09-22' };
const rowById = (p, id) => p.eligible_offers.concat(p.ineligible_offers).find((r) => r.observation_id === id);
const codesOf = (row) => (row && row.reasons ? row.reasons.map((r) => r.code) : []);

test('MARKET-03 E1: A synthetic pack of four and one piece compare correctly when equivalence is accepted', () => {
  const packOfFour = synth({
    observation_id: 'PACK-4', amount: 40, amount_scope: 'per_pack',
    pack: {
      contents: [{ part: 'piece', quantity: 4 }],
      contents_equivalent: true,
      pieces_per_pack: 4,
      unit: 'piece'
    }
  });
  const onePiece = synth({
    observation_id: 'PIECE-1', amount: 10, amount_scope: 'per_piece',
    pack: null
  });

  const view = market.packCompareView({
    pack_offer: packOfFour,
    piece_offer: onePiece,
    panel: comparable.panel(CTX, [packOfFour, onePiece], BASE)
  });

  assert.equal(view.equivalence_accepted, true);
  assert.equal(view.pack_unit_price, 10);
  assert.equal(view.piece_unit_price, 10);
  assert.equal(view.comparable, true);
  assert.ok(view.panel.eligible_offers.map((r) => r.observation_id).includes('PACK-4'));
  assert.ok(view.panel.eligible_offers.map((r) => r.observation_id).includes('PIECE-1'));
});

test('MARKET-03 E2: Unknown pack contents prevent the derived comparable unit price, not retention of the original observation', () => {
  const unknown = synth({
    observation_id: 'PACK-UNKNOWN', amount: 40, amount_scope: 'per_pack',
    pack: { contents: null, kit_contents: null }
  });

  const view = market.packUnknownView({
    offer: unknown,
    panel: comparable.panel(CTX, [unknown], BASE)
  });

  assert.equal(view.derived_unit_price, null);
  assert.equal(view.original_amount_retained, true);
  assert.equal(view.original_amount, 40);
  assert.equal(view.panel.eligible_offers.length, 0);
  const row = rowById(view.panel, 'PACK-UNKNOWN');
  assert.ok(codesOf(row).includes('PACK_CONTENTS_UNKNOWN'));
  assert.equal(row.visible, true);
  assert.equal(row.raw.amount, 40);
  assert.equal(row.comparable_value.value, null);
});
