#!/usr/bin/env node
/* ===========================================================================
   MARKET-04 acceptance tests: currency, tax and delivery adjustments auditable.

   How to run
     node --test tests/market_04_adjustments.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (MARKET-04):
     E1  A converted observation can be reproduced from the retained original
         and dated inputs.
     E2  Unknown tax or delivery treatment is not silently assumed equal between
         offers.

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
    amount_scope: 'per_piece', unit: 'piece',
    channel: 'web_listing', availability_meaning: 'in_stock_stated',
    part_number: 'SYNTH-PART', case_id: 'CASE-X', original_reference: 'SYNTH-PART',
    match: { status: 'accepted', basis: 'exact_part_number' }
  }, over || {})));
}

const CTX = { case_id: 'CASE-X', part_number: 'SYNTH-PART', market: 'UK', unit: 'piece' };
const BASE = { basis_level: 'public_advertised_retail', basis_unit: 'piece', as_of: '2026-09-22' };
const rowById = (p, id) => p.eligible_offers.concat(p.ineligible_offers).find((r) => r.observation_id === id);
const codesOf = (row) => (row && row.reasons ? row.reasons.map((r) => r.code) : []);

test('MARKET-04 E1: A converted observation can be reproduced from the retained original and dated inputs', () => {
  const offer = synth({
    observation_id: 'FX-1', amount: 20, currency: 'GBP', tax: 'excluded',
    delivery_included: true, fx_to_eur: 1.15, fx_date: '2026-09-15'
  });

  const view = market.adjustmentAuditView({
    offer,
    panel: comparable.panel(CTX, [offer], BASE)
  });

  assert.equal(view.original.amount, 20);
  assert.equal(view.original.currency, 'GBP');
  assert.ok(view.steps.length >= 1);
  assert.ok(view.steps.every((s) => s.input_date || s.kind));
  assert.equal(view.reproducible, true);
  assert.equal(view.converted_value, 23);
  assert.equal(view.retained_original, true);
});

test('MARKET-04 E2: Unknown tax or delivery treatment is not silently assumed equal between offers', () => {
  const known = synth({
    observation_id: 'TAX-KNOWN', amount: 10, currency: 'EUR', tax: 'excluded',
    delivery_included: true, vat_rate: 0, vat_rate_unit: 'percent'
  });
  const unknownTax = synth({
    observation_id: 'TAX-UNKNOWN', amount: 12, currency: 'EUR', tax: null,
    delivery_included: null, vat_rate: null, vat_rate_unit: null
  });

  const view = market.unknownAdjustmentView({
    known, unknown: unknownTax,
    panel: comparable.panel(CTX, [known, unknownTax], BASE)
  });

  assert.equal(view.assumed_equal, false);
  assert.ok(view.unknown_codes.includes('TAX_BASIS_NOT_STATED')
    || view.unknown_codes.includes('DELIVERY_TREATMENT_UNKNOWN')
    || view.unknown_codes.length > 0);
  const row = rowById(view.panel, 'TAX-UNKNOWN');
  assert.ok(codesOf(row).includes('TAX_BASIS_NOT_STATED')
    || codesOf(row).includes('DELIVERY_TREATMENT_UNKNOWN')
    || codesOf(row).includes('CURRENCY_NOT_STATED')
    || view.panel.eligible_offers.every((r) => r.observation_id !== 'TAX-UNKNOWN'));
  assert.notEqual(row.quoted.tax, 'excluded');
});
