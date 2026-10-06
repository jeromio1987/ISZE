#!/usr/bin/env node
/* ===========================================================================
   MARKET-08 acceptance tests: ask only for the missing comparison evidence.

   How to run
     node --test tests/market_08_request.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (MARKET-08):
     E1  The request does not ask for full resale-price files, customer
         databases or another distributor's confidential terms.
     E2  Declining the request removes only the unsupported price conclusion;
         the current purchasing task remains available.

   Synthetic figures only. The restricted payload is never read here.
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

test('MARKET-08 E1: Request does not ask for resale-price files, customer databases or confidential terms', () => {
  const dirty = comparable.requestIsClean({
    smallest_missing_detail: 'Please send the full resale price file and the dealer customer list',
    use: 'To build the index', audience: 'the distributor',
    response_offered: 'A comparison'
  });
  assert.equal(dirty.clean, false);
  assert.ok(dirty.hits.includes('resale price'));
  assert.ok(dirty.hits.includes('customer list'));

  const result = comparable.panel(CTX, [
    cleanOffer({ observation_id: 'X', currency: null, tax: null })
  ], BASE);
  const request = comparable.missingEvidenceRequest(result, CTX);
  assert.equal(request.ok, true, request.reason_code || request.error || '');
  assert.equal(request.draft_only, true);
  assert.equal(request.sent, false);
  assert.ok(Array.isArray(request.does_not_ask_for));
  assert.ok(request.does_not_ask_for.some((s) => /resale/i.test(s)));
  assert.ok(request.does_not_ask_for.some((s) => /customer/i.test(s)));
  assert.ok(request.does_not_ask_for.some((s) => /confidential/i.test(s) || /distributor/i.test(s)));

  const cleanCheck = comparable.requestIsClean(request);
  assert.equal(cleanCheck.clean, true, JSON.stringify(cleanCheck.hits || []));

  const bad = comparable.missingEvidenceRequest(result, CTX, { topic: 'everything_you_have' });
  assert.equal(bad.ok, false);
  assert.equal(bad.reason_code, 'UNDECLARED_TOPIC');
});

test('MARKET-08 E2: Declining removes only the unsupported price conclusion; purchasing stays available', () => {
  /* Offer missing tax so the panel has a real smallest ask to decline. */
  const result = comparable.panel(CTX, [
    cleanOffer({ observation_id: 'D1', tax: null, currency: null })
  ], Object.assign({}, BASE, { own_movement: { label: 'recorded periods', periods: [] } }));
  const request = comparable.missingEvidenceRequest(result, CTX);
  assert.equal(request.ok, true, request.reason_code || request.error || '');
  assert.equal(request.draft_only, true);

  const declined = comparable.declineRequest(request, result, {
    unrelated_support: ['the supplier support position on this part']
  });

  assert.equal(declined.declined, true);
  assert.deepEqual(declined.removed_only, ['the competitor price conclusion that this request was for']);
  assert.equal(declined.price_positioning.available, false);
  assert.equal(declined.scenario_link.linked, false);
  assert.ok(declined.still_available.some((s) => /recorded movement/i.test(s)),
    'the purchasing review on this part survives the decline');
  assert.ok(declined.still_available.some((s) => /support/i.test(s)));
  assert.equal(declined.verdict_unchanged, true);
  assert.match(declined.statement, /turned into a zero or an approval/i);
});