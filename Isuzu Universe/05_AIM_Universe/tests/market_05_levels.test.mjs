#!/usr/bin/env node
/* ===========================================================================
   MARKET-05 acceptance tests: keep different commercial price levels separate.

   How to run
     node --test tests/market_05_levels.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (MARKET-05):
     E1  An ISZE-net-versus-retail fixture is excluded from a direct price index
         unless an accepted bridge is explicitly supplied.
     E2  A reference valuation cannot be displayed as actual downstream revenue
         or dealer margin.

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
    seller: 'Fixture Seller', market: 'UK', source: 'Synthetic listing',
    observed_date: '2026-09-20', amount_scope: 'per_piece', currency: 'EUR',
    unit: 'piece', tax: 'excluded', vat_rate: 0, vat_rate_unit: 'percent',
    delivery_included: true, channel: 'web_listing',
    availability_meaning: 'in_stock_stated', part_number: 'SYNTH-PART',
    case_id: 'CASE-X', original_reference: 'SYNTH-PART',
    match: { status: 'accepted', basis: 'exact_part_number' }
  }, over || {})));
}

const CTX = { case_id: 'CASE-X', part_number: 'SYNTH-PART', market: 'UK', unit: 'piece' };
const rowById = (p, id) => p.eligible_offers.concat(p.ineligible_offers).find((r) => r.observation_id === id);
const codesOf = (row) => (row && row.reasons ? row.reasons.map((r) => r.code) : []);

test('MARKET-05 E1: An ISZE-net-versus-retail fixture is excluded from a direct price index unless an accepted bridge is supplied', () => {
  const ourTerms = synth({
    observation_id: 'ISZE-NET', role: 'isze_terms', level: 'isze_net_distributor',
    seller: 'ISZE', amount: 85.91
  });
  const retail = synth({
    observation_id: 'RETAIL-AD', role: 'competitor', level: 'public_advertised_retail',
    seller: 'Some Seller', amount: 76.99
  });

  const view = market.levelBridgeView({
    our_terms: ourTerms,
    retail,
    panel_without_bridge: comparable.panel(CTX, [ourTerms, retail], {
      basis_level: 'isze_net_distributor', basis_unit: 'piece', as_of: '2026-09-22'
    }),
    panel_with_bridge: comparable.panel(CTX, [ourTerms, retail], {
      basis_level: 'isze_net_distributor', basis_unit: 'piece', as_of: '2026-09-22',
      level_bridge: {
        bridge_id: 'BR-1', from_level: 'isze_net_distributor',
        to_level: 'public_advertised_retail', approved_by: 'role: commercial owner',
        statement: 'a documented bridge between our net terms and the advertised level'
      }
    })
  });

  assert.equal(view.direct_index_allowed_without_bridge, false);
  assert.ok(view.excluded_without_bridge.includes('RETAIL-AD'));
  assert.ok(codesOf(rowById(view.panel_without_bridge, 'RETAIL-AD')).includes('NO_ACCEPTED_LEVEL_BRIDGE'));
  assert.equal(view.direct_index_allowed_with_bridge, true);
  assert.equal(view.panel_with_bridge.ineligible_offers.length, 0);
});

test('MARKET-05 E2: A reference valuation cannot be displayed as actual downstream revenue or dealer margin', () => {
  const view = market.referenceValuationView({});

  assert.equal(view.shown_as_actual_revenue, false);
  assert.equal(view.shown_as_dealer_margin, false);
  assert.ok(view.forbidden_labels.every((l) => !view.display_labels.includes(l)));
  assert.match(view.statement, /comparison convention|not a transaction|cannot be shown as revenue/i);

  /* Direct panel contract stays aligned with the shared assert. */
  const asRevenue = comparable.assertLevelUse('reference_dealer', 'dealer_revenue');
  const asMargin = comparable.assertLevelUse('reference_dealer', 'dealer_margin');
  assert.equal(asRevenue.ok, false);
  assert.equal(asMargin.ok, false);
});
