#!/usr/bin/env node
/* ===========================================================================
   MARKET-07 / MARKET-08 - the comparable-price panel and the missing-evidence
   request.

   Run:  node --test tests/market_evidence.test.mjs

   Every synthetic figure below is invented for the test and is NOT an ISZE
   price. The panel's own payload, when it is read, is read for the shape of its
   records and never copied into this file.

   The suite is written against the panel's declared contract, not against the
   code's current mood: each check says what the panel must do, so a later
   change that quietly drops an exclusion reason fails here.
   =========================================================================== */

import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const comparable = require(join(ROOT, 'src', 'data', 'comparable.js'));
const evidence = require(join(ROOT, 'src', 'data', 'evidence.js'));

const PAYLOAD = join(ROOT, 'payload', 'aim_payload_20260922.json');

/* ----------------------------------------------------------------- helpers -- */

/* A competitor observation that is clean on every axis the panel checks on, so
   each test can spoil exactly one thing and see exactly one exclusion. */
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

const codesOf = (row) => row.reason_codes || [];
const rowById = (panelResult, id) =>
  panelResult.eligible_offers.concat(panelResult.ineligible_offers)
    .find((r) => r.observation_id === id);

/* Every field name anywhere in a value, so "no restricted cost travelled into
   the panel" can be asserted as a property and not as a text search. */
function allKeys(value, into = []) {
  if (value === null || typeof value !== 'object') return into;
  if (Array.isArray(value)) { value.forEach((v) => allKeys(v, into)); return into; }
  for (const k of Object.keys(value)) { into.push(k); allKeys(value[k], into); }
  return into;
}

/* =========================================================================
   MARKET-03 - the pack of four against the single piece
   ========================================================================= */

test('M07 pack of four versus one piece compares correctly when equivalence is accepted', () => {
  const packOfFour = cleanOffer({
    observation_id: 'PACK-4', seller: 'Seller Pack', amount: 40, amount_scope: 'per_pack',
    pack: { contents: [{ part: 'pad', quantity: 4 }], contents_equivalent: true, unit: 'piece' }
  });
  const onePiece = cleanOffer({ observation_id: 'PIECE-1', seller: 'Seller Piece', amount: 12 });

  const result = comparable.panel(CTX, [packOfFour, onePiece], BASE);

  assert.equal(result.ineligible_offers.length, 0,
    'the pack of four and the single piece should both be comparable: '
    + JSON.stringify(result.ineligible_offers.map((r) => [r.observation_id, codesOf(r)])));

  const pack = rowById(result, 'PACK-4');
  const piece = rowById(result, 'PIECE-1');

  /* Both bases are shown: the quoted pack price is kept and the derived unit
     price is stated beside it. */
  assert.equal(pack.per_pack.value, 40, 'the quoted pack price is kept as quoted');
  assert.equal(pack.per_piece.value, 10, '40 for a stated pack of four is 10 per piece');
  assert.equal(piece.per_piece.value, 12);
  assert.deepEqual(pack.bases_shown, ['quoted', 'adjusted', 'per_piece']);
  assert.equal(pack.raw.amount, 40, 'the original unit and its price stay intact');

  /* A summary needs an approved rule. With one, the median is stated and the
     offers it came from are still returned individually. */
  const withRule = comparable.panel(CTX, [packOfFour, onePiece],
    Object.assign({}, BASE, {
      approved_aggregation_rule: { rule_id: 'AGG-1', approved_by: 'role: pricing owner',
        method: 'median', statement: 'median of comparable per-piece prices' }
    }));
  assert.equal(withRule.aggregation.declared, true);
  assert.equal(withRule.aggregation.summary, 11, 'median of 10 and 12 is 11');
  assert.equal(withRule.aggregation.offers_shown_individually, true);
});

test('M03 unknown pack contents block the derived per-piece price and keep the original observation', () => {
  const unknownPack = cleanOffer({
    observation_id: 'PACK-UNKNOWN', amount: 40, amount_scope: 'per_pack',
    pack: { contents: null, kit_contents: null }
  });

  const result = comparable.panel(CTX, [unknownPack], BASE);
  const row = rowById(result, 'PACK-UNKNOWN');

  assert.equal(result.eligible_offers.length, 0,
    'a price per pack with unstated contents cannot be compared per piece');
  assert.ok(codesOf(row).includes('PACK_CONTENTS_UNKNOWN'),
    'expected a named pack-contents reason, saw ' + JSON.stringify(codesOf(row)));

  /* The observation is not discarded: the original quote is still on the row,
     and the money that IS auditable is still stated. Only the derived
     comparison is withheld. */
  assert.equal(row.visible, true);
  assert.equal(row.raw.amount, 40);
  assert.equal(row.adjustment.value, 40,
    'the auditable adjusted amount is kept even though the per-piece figure cannot be derived');
  assert.equal(row.comparable_value.value, null, 'no comparable per-piece figure is stated');
  assert.deepEqual(row.quoted.pack_contents, null);
  assert.match(row.reason, /contents/i);
});

test('M04 a tax rate whose unit is not stated leaves the amount unresolved rather than guessed', () => {
  /* The same digits, two orders of magnitude apart: 0.20 as a fraction and 20 as
     a percentage. Guessing this is a hundred-fold error, so it is not guessed. */
  const ambiguous = cleanOffer({ observation_id: 'AMBIG', amount: 120, tax: 'included',
    vat_rate: 0.2, vat_rate_unit: null });
  const result = comparable.panel(CTX, [ambiguous], BASE);
  const row = rowById(result, 'AMBIG');
  assert.ok(codesOf(row).includes('VAT_RATE_UNIT_NOT_STATED'),
    'an undeclared rate unit must be named, saw ' + JSON.stringify(codesOf(row)));
  assert.equal(row.adjustment.value, null, 'no adjusted figure is stated from a guessed rate unit');

  /* Declared as a fraction, 120 including 20% becomes 100. */
  const asFraction = comparable.panel(CTX, [cleanOffer({ observation_id: 'FRAC', amount: 120,
    tax: 'included', vat_rate: 0.2, vat_rate_unit: 'fraction' })], BASE);
  const f = rowById(asFraction, 'FRAC');
  assert.equal(f.adjustment.value, 100, '120 including 20% differs from 120 excluding by 20');
  assert.equal(f.adjustment.vat_rate_used.passed_to_the_rule, 20,
    'the row declared a fraction, so the rule is given the percentage it asks for');

  /* Declared as a percentage, the same digits mean something else entirely. */
  const asPercent = comparable.panel(CTX, [cleanOffer({ observation_id: 'PCT', amount: 120,
    tax: 'included', vat_rate: 20, vat_rate_unit: 'percent' })], BASE);
  assert.equal(rowById(asPercent, 'PCT').adjustment.value, 100);
});

test('M03 pack contents that are not equivalent are refused even when the price normalises', () => {
  const elementOnly = cleanOffer({
    observation_id: 'HOUSING-V-ELEMENT', amount: 40, amount_scope: 'per_pack',
    pack: { contents: [{ part: 'housing', quantity: 1 }], contents_equivalent: false, unit: 'piece' }
  });
  const result = comparable.panel(CTX, [elementOnly], BASE);
  const row = rowById(result, 'HOUSING-V-ELEMENT');
  assert.ok(codesOf(row).includes('KIT_CONTENTS_NOT_EQUIVALENT'),
    'a housing and an element must not form an accepted price comparison: '
    + JSON.stringify(codesOf(row)));
});

/* =========================================================================
   MARKET-05 - price levels are never mixed
   ========================================================================= */

test('M05 an ISZE-net row against an advertised retail row is excluded without an accepted bridge', () => {
  const ourTerms = cleanOffer({
    observation_id: 'ISZE-NET', role: 'isze_terms', level: 'isze_net_distributor',
    seller: 'ISZE', amount: 85.91
  });
  const retail = cleanOffer({
    observation_id: 'RETAIL-AD', role: 'competitor', level: 'public_advertised_retail',
    seller: 'Some Seller', amount: 76.99
  });

  const noBridge = comparable.panel(CTX, [ourTerms, retail],
    Object.assign({}, BASE, { basis_level: 'isze_net_distributor' }));

  assert.equal(noBridge.eligible_offers.length, 1);
  assert.equal(noBridge.eligible_offers[0].observation_id, 'ISZE-NET');

  const excluded = rowById(noBridge, 'RETAIL-AD');
  assert.ok(codesOf(excluded).includes('NO_ACCEPTED_LEVEL_BRIDGE'),
    'an advertised retail price is not put into a direct index against our own net terms: '
    + JSON.stringify(codesOf(excluded)));
  assert.match(excluded.reason, /not proof that our own net terms are too high/i);
  assert.equal(noBridge.price_positioning.index_allowed, false,
    'the index is not allowed from the one level alone');

  /* An explicitly accepted bridge does allow the comparison. */
  const bridged = comparable.panel(CTX, [ourTerms, retail], Object.assign({}, BASE, {
    basis_level: 'isze_net_distributor',
    level_bridge: { bridge_id: 'BR-1', from_level: 'isze_net_distributor',
      to_level: 'public_advertised_retail', approved_by: 'role: commercial owner',
      statement: 'a documented bridge between our net terms and the advertised level' }
  }));
  assert.equal(bridged.ineligible_offers.length, 0,
    'with an accepted bridge both rows are comparable');
  assert.ok(bridged.eligible_offers.every((r) => r.observation_id));
  assert.equal(bridged.price_positioning.index_allowed, true);
});

test('M05 a bridge that is named but not accepted does not enable the comparison', () => {
  const ourTerms = cleanOffer({ observation_id: 'ISZE-NET', role: 'isze_terms',
    level: 'isze_net_distributor', amount: 90.0 });
  const retail = cleanOffer({ observation_id: 'RETAIL-AD', amount: 80.0 });

  const half = comparable.panel(CTX, [ourTerms, retail], Object.assign({}, BASE, {
    basis_level: 'isze_net_distributor',
    level_bridge: { bridge_id: 'BR-2', from_level: 'isze_net_distributor',
      to_level: 'public_advertised_retail', approved_by: null }
  }));
  assert.equal(half.eligible_offers.length, 1,
    'a bridge with no named approver is not an accepted bridge');
  assert.ok(codesOf(rowById(half, 'RETAIL-AD')).includes('NO_ACCEPTED_LEVEL_BRIDGE'));
});

test('M05 a derived reference valuation is refused as revenue or dealer margin', () => {
  const asRevenue = comparable.assertLevelUse('reference_dealer', 'dealer_revenue');
  assert.equal(asRevenue.ok, false);
  assert.match(asRevenue.statement, /comparison convention, not a transaction/i);

  const asMargin = comparable.assertLevelUse('reference_dealer', 'dealer_margin');
  assert.equal(asMargin.ok, false);

  /* It is allowed for what it is: a competitiveness comparison. */
  const asComparison = comparable.assertLevelUse('reference_dealer', 'competitiveness_comparison');
  assert.equal(asComparison.ok, true);

  /* And a purchasing cost is not a selling price at any level. */
  const cost = comparable.assertLevelUse('supplier_cost', 'competitiveness_comparison');
  assert.equal(cost.ok, false);
  assert.match(cost.statement, /purchase cost/i);
});

test('M05 a row with no declared price level is excluded rather than compared', () => {
  const unlevelled = cleanOffer({ observation_id: 'NO-LEVEL', level: null });
  const result = comparable.panel(CTX, [unlevelled], BASE);
  assert.ok(codesOf(rowById(result, 'NO-LEVEL')).includes('NO_PRICE_LEVEL_DECLARED'));
  assert.match(rowById(result, 'NO-LEVEL').reason, /does not declare which price level/i);
});

/* =========================================================================
   MARKET-04 - missing money facts stay missing
   ========================================================================= */

test('M04 a missing currency or tax basis stays missing and is not inherited from the previous row', () => {
  const complete = cleanOffer({ observation_id: 'FULL-ROW', amount: 10 });
  const missing = cleanOffer({
    observation_id: 'MISSING-ROW', amount: 20, currency: null, tax: null, vat_rate: null,
    delivery_included: true
  });

  const result = comparable.panel(CTX, [complete, missing], BASE);
  const row = rowById(result, 'MISSING-ROW');

  /* The missing row does not borrow the previous row's currency or tax. */
  assert.equal(row.quoted.currency, null, 'a missing currency stays missing');
  assert.equal(row.quoted.tax, null, 'a missing tax basis stays missing');
  assert.notEqual(row.quoted.currency, 'EUR');
  assert.notEqual(row.quoted.tax, 'excluded');

  const codes = codesOf(row);
  assert.ok(codes.includes('CURRENCY_NOT_STATED'), 'expected CURRENCY_NOT_STATED, saw ' + JSON.stringify(codes));
  assert.ok(codes.includes('TAX_BASIS_NOT_STATED'), 'expected TAX_BASIS_NOT_STATED, saw ' + JSON.stringify(codes));
  assert.equal(result.eligible_offers.length, 1,
    'only the complete row is comparable; the incomplete one is not silently completed');

  /* The complete row is untouched by its broken neighbour. */
  const full = rowById(result, 'FULL-ROW');
  assert.equal(full.quoted.currency, 'EUR');
  assert.equal(full.quoted.tax, 'excluded');
});

test('M04 an amount in another currency is unresolved until a dated rate is supplied', () => {
  const foreign = cleanOffer({
    observation_id: 'JPY-ROW', amount: 5000, currency: 'JPY', fx_to_eur: null, fx_date: null
  });
  const noRate = comparable.panel(CTX, [foreign], BASE);
  assert.ok(codesOf(rowById(noRate, 'JPY-ROW')).includes('NO_DATED_RATE_TO_EUR'));
  assert.equal(rowById(noRate, 'JPY-ROW').adjustment.value, null);

  const withRate = comparable.panel(CTX, [cleanOffer({
    observation_id: 'JPY-ROW', amount: 5000, currency: 'JPY', fx_to_eur: 0.0062, fx_date: '2026-09-01'
  })], BASE);
  const row = rowById(withRate, 'JPY-ROW');
  assert.equal(withRate.ineligible_offers.length, 0, JSON.stringify(codesOf(row)));
  assert.ok(row.adjustment.steps.some((s) => s.step === 'convert to EUR'),
    'the conversion is a recorded step');
  assert.equal(row.adjustment.value_before_adjustment, 5000, 'the original quote is retained');
});

test('M04 an unknown tax rate on a tax-inclusive price is unresolved, not assumed', () => {
  const incl = cleanOffer({ observation_id: 'INCL-NO-RATE', tax: 'included', vat_rate: null });
  const result = comparable.panel(CTX, [incl], BASE);
  assert.ok(codesOf(rowById(result, 'INCL-NO-RATE')).includes('TAX_RATE_NOT_STATED'));
  assert.equal(rowById(result, 'INCL-NO-RATE').adjustment.value, null);
});

/* =========================================================================
   MARKET-06 - old and superseded observations stay visible
   ========================================================================= */

test('M06 a newer observation does not rewrite an earlier saved comparison', () => {
  const earlier = cleanOffer({ observation_id: 'OBS-OLD', amount: 42, retrieved: '2026-01-10' });
  const newer = cleanOffer({
    observation_id: 'OBS-NEW', amount: 31, retrieved: '2026-09-20', supersedes: 'OBS-OLD'
  });

  const result = comparable.panel(CTX, [earlier, newer], Object.assign({}, BASE, {
    saved_comparisons: [{ comparison_id: 'CMP-1', observation_ids: ['OBS-OLD'], value: 42,
      basis: 'public_advertised_retail per piece', saved_at: '2026-02-01' }]
  }));

  const saved = result.saved_comparisons[0];
  assert.equal(saved.value, 42, 'the saved figure stands as the figure that was saved');
  assert.equal(saved.rewritten, false);
  assert.deepEqual(saved.superseded_by_observation_ids, ['OBS-NEW']);
  assert.match(saved.statement, /not rewritten/i);

  /* The superseded row is still present and still readable. */
  const oldRow = rowById(result, 'OBS-OLD');
  assert.ok(oldRow, 'the superseded observation must remain visible');
  assert.ok(codesOf(oldRow).includes('SUPERSEDED_OBSERVATION'),
    'expected a named supersession reason, saw ' + JSON.stringify(codesOf(oldRow)));
  assert.equal(oldRow.raw.amount, 42, 'its original amount is retained');
  assert.equal(oldRow.visible, true);
});

test('M06 an old observation is flagged for review because no expiry policy is approved', () => {
  const old = cleanOffer({ observation_id: 'OLD-ROW', retrieved: '2025-01-01' });
  const result = comparable.panel(CTX, [old], BASE);

  assert.equal(result.eligible_offers.length, 1,
    'with no approved expiry policy, age alone does not decide eligibility');
  const row = rowById(result, 'OLD-ROW');
  assert.ok(row.age_days > 180);
  assert.ok(result.flags.some((f) => f.code === 'AGE_BEYOND_REVIEW_POINT' && f.observation_id === 'OLD-ROW'),
    'the old observation is flagged for review');

  /* With a policy that a named owner approved, age does decide. */
  const withPolicy = comparable.panel(CTX, [old], Object.assign({}, BASE, {
    freshness_policy: { policy_id: 'FRESH-1', approved_by: 'role: pricing owner', max_age_days: 180 }
  }));
  assert.ok(codesOf(rowById(withPolicy, 'OLD-ROW')).includes('AGE_BEYOND_DECLARED_POLICY'));
});

test('M06 conflicting observations all stay visible and none is chosen', () => {
  const a = cleanOffer({ observation_id: 'CONF-A', seller: 'Seller A', amount: 10 });
  const b = cleanOffer({ observation_id: 'CONF-B', seller: 'Seller B', amount: 30 });
  const result = comparable.panel(CTX, [a, b], BASE);

  assert.equal(result.eligible_offers.length, 2, 'both conflicting observations stay visible');
  assert.ok(result.flags.some((f) => f.code === 'CONFLICTING_OBSERVATIONS'),
    'the disagreement between the two sources is reported');
});

/* =========================================================================
   MARKET-07 - the panel itself
   ========================================================================= */

test('M07 the cheapest observation is not selected automatically', () => {
  const cheap = cleanOffer({ observation_id: 'CHEAP', amount: 1 });
  const middle = cleanOffer({ observation_id: 'MIDDLE', amount: 50 });
  const dear = cleanOffer({ observation_id: 'DEAR', amount: 900 });

  const result = comparable.panel(CTX, [cheap, middle, dear], BASE);

  assert.equal(result.selected_observation_id, null, 'no observation is chosen for the reader');
  assert.equal(result.aggregation.declared, false, 'no aggregation rule is declared by default');
  assert.equal(result.aggregation.summary, null,
    'without an approved rule no summary figure is invented');
  assert.equal(result.aggregation.offers_shown_individually, true);

  result.eligible_offers.forEach((row) => {
    assert.equal(row.selected_observation_id, null);
    assert.equal(row.selected === false, true,
      'an eligible row must be explicitly marked as not selected');
    assert.match(row.selection, /cheapest is not treated as the right one/i);
  });

  /* The reader cannot read a chosen row out of the panel: no row carries a
     selection, and no summary hides the spread. */
  assert.equal(result.eligible_offers.length, 3);
  assert.equal(new Set(result.eligible_offers.map((r) => r.per_piece.value)).size, 3,
    'all three deliberately different prices stay visible');
});

test('M07 every excluded observation carries a named reason and its raw record', () => {
  const rows = [
    cleanOffer({ observation_id: 'OK-1' }),
    cleanOffer({ observation_id: 'BAD-LEVEL', level: null }),
    cleanOffer({ observation_id: 'BAD-PACK', amount: 40, amount_scope: 'per_pack', pack: { contents: null } }),
    cleanOffer({ observation_id: 'BAD-MATCH', match: { status: 'rejected', basis: 'rejected', reason: 'not the same kit' } }),
    cleanOffer({ observation_id: 'BAD-CURRENCY', currency: null }),
    cleanOffer({ observation_id: 'BAD-ROLE', role: null })
  ];

  const result = comparable.panel(CTX, rows, BASE);

  assert.equal(result.observations_in, 6);
  assert.equal(result.raw_records_retained, 6,
    'an observation is never discarded, only left out of the comparable set');
  assert.equal(result.eligible_offers.length, 1);
  assert.equal(result.ineligible_offers.length, 5);

  /* Each planted defect must be excluded for its own reason, not just any reason. */
  const EXPECTED = {
    'BAD-LEVEL': [['NO_PRICE_LEVEL_DECLARED'], 'excluded'],
    'BAD-PACK': [['PACK_CONTENTS_UNKNOWN'], 'unresolved'],
    'BAD-MATCH': [['PRODUCT_MATCH_REJECTED'], 'excluded'],
    'BAD-CURRENCY': [['CURRENCY_NOT_STATED'], 'unresolved'],
    'BAD-ROLE': [['ROLE_NOT_STATED'], 'excluded']
  };
  assert.deepEqual(result.ineligible_offers.map((r) => r.observation_id).sort(), Object.keys(EXPECTED).sort());
  result.ineligible_offers.forEach((row) => {
    assert.deepEqual(row.reason_codes, EXPECTED[row.observation_id][0],
      row.observation_id + ' was excluded for the wrong reason');
    assert.equal(row.exclusion_kind, EXPECTED[row.observation_id][1], row.observation_id + ' exclusion kind');
    assert.ok(typeof row.reason === 'string' && row.reason.length > 20,
      row.observation_id + ' was excluded without a readable reason');
    (row.reason_codes || []).forEach((code) => {
      assert.ok(comparable.EXCLUSION_CODES[code],
        'reason code ' + code + ' is not declared in the exclusion list');
      assert.equal(comparable.explainExclusion(code).known, true);
    });
    assert.ok(row.raw, row.observation_id + ' lost its raw record');
    assert.equal(row.raw_unchanged, true);
    assert.equal(row.visible, true);
    assert.equal(row.excluded_silently, undefined);
  });

  assert.equal(result.all_exclusion_codes_named, true);
  assert.ok(result.ineligible_offers.every((r) => r.exclusion_kind === 'excluded' || r.exclusion_kind === 'unresolved'));
});

test('M07 removing an ineligible observation does not alter the raw evidence record', () => {
  const keeps = [cleanOffer({ observation_id: 'KEEP-1', amount: 10 }),
    cleanOffer({ observation_id: 'KEEP-2', amount: 20 })];
  const dropped = cleanOffer({ observation_id: 'DROP-1', level: null, amount: 5 });

  const withAll = keeps.concat([dropped]);
  const before = JSON.stringify(withAll);

  const full = comparable.panel(CTX, withAll, BASE);
  const without = comparable.panel(CTX, keeps, BASE);

  /* The caller's array is never written to. */
  assert.equal(JSON.stringify(withAll), before, 'the input array was modified by the panel');
  assert.equal(full.raw_input_unmodified, true);
  assert.equal(without.raw_input_unmodified, true);

  /* The rows that stayed are byte-identical with and without the dropped row. */
  ['KEEP-1', 'KEEP-2'].forEach((id) => {
    assert.equal(JSON.stringify(rowById(full, id).raw), JSON.stringify(rowById(without, id).raw),
      id + ' changed when an unrelated row was removed');
    assert.equal(JSON.stringify(rowById(full, id).adjustment),
      JSON.stringify(rowById(without, id).adjustment));
  });

  /* The dropped row is reported in one panel and simply absent from the other,
     never renumbered or absorbed. */
  assert.equal(full.ineligible_offers.length, 1);
  assert.equal(without.ineligible_offers.length, 0);
});

test('M07 purchasing movement and price positioning are two separate labelled outputs', () => {
  const movement = {
    label: 'January-June 2026 against January-June 2025',
    source_reference: 'the comparison the case already carries',
    periods: [
      { label: '2025', quantity: 1031, unit_price: 87.59 },
      { label: '2026', quantity: 1400, unit_price: 85.91 }
    ]
  };
  const result = comparable.panel(CTX, [cleanOffer({ observation_id: 'OBS-A' })],
    Object.assign({}, BASE, { own_movement: movement }));

  assert.equal(result.purchasing_movement.available, true);
  assert.equal(result.purchasing_movement.is_proof_of_price_positioning, false);
  assert.deepEqual(result.purchasing_movement.periods.map((p) => p.label), ['2025', '2026']);
  assert.ok(result.purchasing_movement.must_not_be_read_as.length >= 3);

  assert.equal(result.price_positioning.available, true);
  assert.equal(result.price_positioning.is_proof_that_our_terms_are_too_high, false);
  assert.notEqual(result.purchasing_movement.evidence_kind, result.price_positioning.evidence_kind,
    'the two outputs must declare different kinds of evidence');

  /* Neither output may be read as the other. */
  assert.match(result.purchasing_movement.statement, /not proof of where our price sits/i);
  assert.match(result.price_positioning.statement, /No index figure is certified/i);
});

test('M07 no price action is certified and the scenario link carries only the supported comparison', () => {
  const good = cleanOffer({ observation_id: 'GOOD' });
  const bad = cleanOffer({ observation_id: 'BAD', level: null });

  const linked = comparable.panel(CTX, [good, bad], BASE);
  assert.equal(linked.price_action_certified, false);
  assert.equal(linked.scenario_link.linked, true);
  assert.deepEqual(linked.scenario_link.eligible_observation_ids, ['GOOD']);
  assert.deepEqual(linked.scenario_link.excluded_observation_ids, ['BAD'],
    'an excluded observation must not travel into the scenario');

  /* With no like-for-like basis named, nothing is linked and the gap is stated. */
  const unlinked = comparable.panel(CTX, [good], { as_of: '2026-09-22' });
  assert.equal(unlinked.selected_basis, null);
  assert.equal(unlinked.scenario_link.linked, false);
  assert.equal(unlinked.scenario_link.reason_code, 'NO_BASIS_NAMED');
  assert.equal(unlinked.price_positioning.available, false);
  assert.equal(unlinked.price_positioning.index_stated, false);
  assert.match(unlinked.price_positioning.statement, /stays missing and is not filled in/i);
  assert.ok(unlinked.flags.some((f) => f.code === 'NO_BASIS_NAMED'));

  /* A named basis with nothing eligible also links nothing. */
  const empty = comparable.panel(CTX, [bad], BASE);
  assert.equal(empty.scenario_link.linked, false);
  assert.equal(empty.scenario_link.reason_code, 'NO_ELIGIBLE_COMPARABLE');
});

test('M07 the panel carries a declared contract and no restricted cost field', () => {
  const result = comparable.panel(CTX, [cleanOffer({})], BASE);

  assert.equal(result.contract.version, 1);
  assert.equal(result.contract.audience, 'internal');
  assert.ok(result.contract.observation.includes('observation_id'));
  assert.ok(result.contract.panel.includes('ineligible_offers'));
  assert.deepEqual(result.contract.declared_roles, ['isze_terms', 'competitor']);
  assert.deepEqual(result.contract.requested_shared_fields, comparable.REQUESTED_SHARED_LEVELS);

  /* A restricted purchasing cost must not travel in a panel. Asserted as
     properties of the returned value, not as a text search. */
  const withoutContract = Object.assign({}, result, { contract: null });
  const keys = allKeys(withoutContract);
  result.contract.excluded_field_names.forEach((banned) => {
    assert.ok(!keys.includes(banned), 'the panel carries a restricted field named ' + banned);
  });
  assert.ok(!keys.includes('cost'), 'the panel carries a cost field');
  assert.ok(!keys.includes('supplier_cost'), 'the panel carries a supplier cost field');
  /* The field-name list is in the contract so a reader can see what is barred,
     and the panel returns none of it. */
  assert.ok(result.contract.excluded_field_names.includes('cost_eur'));
});

test('M07 a partially named aggregation rule produces no summary', () => {
  const rows = [cleanOffer({ observation_id: 'A', amount: 10 }), cleanOffer({ observation_id: 'B', amount: 20 })];
  const undeclared = comparable.panel(CTX, rows, Object.assign({}, BASE, {
    approved_aggregation_rule: { rule_id: 'R1', method: 'median' }
  }));
  assert.equal(undeclared.aggregation.declared, false);
  assert.equal(undeclared.aggregation.summary, null, 'a rule with no approver is not an approved rule');

  const unsupportedMethod = comparable.panel(CTX, rows, Object.assign({}, BASE, {
    approved_aggregation_rule: { rule_id: 'R2', approved_by: 'role: owner', method: 'average',
      statement: 'arithmetic mean' }
  }));
  assert.equal(unsupportedMethod.aggregation.declared, false);
  assert.equal(unsupportedMethod.aggregation.summary, null,
    'a rule the panel cannot compute is not silently replaced with one it can');
  assert.match(unsupportedMethod.aggregation.statement, /would not be the rule that was approved/i);
});

test('M07 the panel reports which price levels are present without choosing one', () => {
  const rows = [
    cleanOffer({ observation_id: 'N1', role: 'isze_terms', level: 'isze_net_distributor', amount: 85 }),
    cleanOffer({ observation_id: 'R1', amount: 76 }),
    cleanOffer({ observation_id: 'B1', amount: 120, level: 'competitor_advertised' })
  ];
  const result = comparable.panel(CTX, rows, { as_of: '2026-09-22' });

  assert.equal(result.selected_basis, null, 'the basis is not picked by the panel');
  const levels = result.candidate_bases.candidates.map((c) => c.level);
  assert.ok(levels.includes('isze_net_distributor'));
  assert.ok(levels.includes('public_advertised_retail'));
  assert.ok(levels.includes('competitor_advertised'));
  assert.match(result.candidate_bases.statement, /has to be named by a reviewer/i);
});

/* =========================================================================
   MARKET-08 - ask only for what is missing
   ========================================================================= */

test('M08 the request asks for the smallest missing detail and nothing else', () => {
  const rows = [
    cleanOffer({ observation_id: 'MISS-1', currency: null, tax: null, amount: 20, amount_scope: 'per_piece' })
  ];
  const result = comparable.panel(CTX, rows, BASE);

  const missing = comparable.missingEvidence(result);
  assert.ok(missing.smallest, 'a gap should be found');
  assert.equal(missing.ordered.length >= 1, true);

  const request = comparable.missingEvidenceRequest(result, CTX);
  assert.equal(request.ok, true);
  assert.equal(request.draft_only, true);
  assert.equal(request.sent, false, 'a draft is never sent automatically');
  assert.equal(request.asks_only_for_one_thing, true);
  assert.equal(request.case_id, 'CASE-X');
  assert.equal(request.part_number, 'SYNTH-PART');
  assert.equal(request.topic, missing.smallest.topic);
  assert.equal(request.observations_affected, missing.smallest.observations);

  /* The four parts of a usable ask are all stated. */
  assert.ok(request.smallest_missing_detail.length > 20);
  assert.ok(request.use.length > 20);
  assert.ok(request.audience.length > 5);
  assert.ok(request.response_offered.length > 20);
  assert.equal(request.kind_of_thing_missing, comparable.REQUEST_TOPICS[request.topic].kind);

  /* The remaining gaps are recorded and are explicitly not asked for. */
  assert.ok(Array.isArray(request.other_gaps_not_asked_for));
  const asked = request.topic;
  request.other_gaps_not_asked_for.forEach((g) => assert.notEqual(g.topic, asked));

  /* It never asks for a full price file, a customer database or anyone's terms. */
  assert.deepEqual(request.does_not_ask_for, [
    'a full resale price file or price list',
    'a customer or dealer database',
    'another distributor\u2019s confidential terms',
    'a restricted purchasing cost table'
  ]);
  assert.equal(comparable.requestIsClean(request).clean, true);
});

test('M08 an ask for prohibited material is refused rather than softened', () => {
  const dirty = comparable.requestIsClean({
    smallest_missing_detail: 'Please send the full resale price file and the dealer customer list',
    use: 'To build the index', audience: 'the distributor',
    response_offered: 'A comparison'
  });
  assert.equal(dirty.clean, false,
    'a request for a full resale price file and a customer list must be refused');
  assert.ok(dirty.hits.includes('resale price'));
  assert.ok(dirty.hits.includes('customer list'));

  /* A sentence that merely says what is NOT asked for is not a request for it. */
  const honest = comparable.requestIsClean({
    smallest_missing_detail: 'State the tax treatment of one advertised price.',
    use: 'So the observation can be placed beside our own terms.',
    audience: 'the seller',
    response_offered: 'The observation is then adjusted and shown on the same basis.'
  });
  assert.equal(honest.clean, true,
    'a request that describes its own boundary must not be read as asking for the thing it excludes');

  /* An undeclared topic is refused, so a request cannot widen itself. */
  const result = comparable.panel(CTX, [cleanOffer({ observation_id: 'X', currency: null, tax: null })], BASE);
  const bad = comparable.missingEvidenceRequest(result, CTX, { topic: 'everything_you_have' });
  assert.equal(bad.ok, false);
  assert.equal(bad.reason_code, 'UNDECLARED_TOPIC');
  assert.ok(bad.declared_topics.includes('tax_basis'));
});

test('M08 only the missing topic is composed, even when more gaps exist', () => {
  const rows = [
    cleanOffer({ observation_id: 'G1', currency: null, tax: null }),
    cleanOffer({ observation_id: 'G2', amount: 40, amount_scope: 'per_pack', pack: { contents: null } })
  ];
  const result = comparable.panel(CTX, rows, BASE);
  const missing = comparable.missingEvidence(result);
  assert.ok(missing.ordered.length > 1, 'this fixture should have more than one gap');

  const request = comparable.missingEvidenceRequest(result, CTX);
  assert.equal(request.topic, missing.smallest.topic);
  assert.equal(request.other_gaps_not_asked_for.length, missing.ordered.length - 1);

  /* Asking for a declared topic other than the smallest is still one thing. */
  const forced = comparable.missingEvidenceRequest(result, CTX, { topic: 'pack_contents' });
  assert.equal(forced.ok, true);
  assert.equal(forced.topic, 'pack_contents');
  assert.match(forced.statement, /One thing is asked for/i);
});

test('M08 an already-held item is not asked for again', () => {
  const result = comparable.panel(CTX, [cleanOffer({ observation_id: 'H1', tax: null })], BASE);
  const request = comparable.missingEvidenceRequest(result, CTX, {
    context_held: ['the part number and the case context', 'our own recorded volumes']
  });
  assert.deepEqual(request.already_held, ['the part number and the case context',
    'our own recorded volumes']);
  assert.match(request.already_held_note, /not asked for again/i);
});

test('M08 declining the request removes only the unsupported price conclusion', () => {
  const result = comparable.panel(CTX, [cleanOffer({ observation_id: 'D1' })],
    Object.assign({}, BASE, { own_movement: { label: 'recorded periods', periods: [] } }));
  const request = comparable.missingEvidenceRequest(result, CTX, { topic: 'tax_basis' });

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
  assert.equal(declined.scenario_link.linked, false);
});

test('M08 nothing is asked for when nothing this panel can ask for is missing', () => {
  const composed = {
    eligible_offers: [{ observation_id: 'OK' }],
    ineligible_offers: [],
    selected_basis: { level: 'public_advertised_retail', unit: 'piece' },
    purchasing_movement: { available: true },
    price_positioning: { available: true }
  };
  const missing = comparable.missingEvidence(composed);
  assert.equal(missing.smallest, null);
  assert.match(missing.statement, /Nothing that this panel can ask for is missing/i);
});

/* =========================================================================
   the real payload - the exclusions the panel actually makes
   ========================================================================= */

test('M07 on the authorised payload, every offer is either comparable or named as excluded', () => {
  if (!existsSync(PAYLOAD)) {
    assert.ok(true, 'payload not present in this environment; the synthetic checks above stand alone');
    return;
  }
  const payload = JSON.parse(readFileSync(PAYLOAD, 'utf8'));

  /* The payload carries ten dated competitor observations in `offers`, and each
     case names the ones that belong to it. */
  const offerIds = Object.keys(payload.offers || {});
  assert.equal(offerIds.length, 10, 'the payload should carry ten offers');

  let totalOffers = 0, totalExcluded = 0, exclusionsWithReasons = 0;
  const codesSeen = {};

  for (const oneCase of payload.cases) {
    const ids = oneCase.offers || [];
    const adapted = ids.map((id) => comparable.observationFromOffer(payload.offers[id], {
      case_id: oneCase.id, unit: oneCase.unit, level: 'public_advertised_retail',
      match_basis: 'cross_reference'
      /* No amount_scope is declared: the payload does not state whether its
         quoted amount is for one piece or for a pack, and the adapter must not
         invent that on its behalf. */
    }));

    const result = comparable.panel(
      { case_id: oneCase.id, part_number: oneCase.pn, market: oneCase.market, unit: oneCase.unit },
      adapted,
      {
        basis_level: 'public_advertised_retail', basis_unit: oneCase.unit, as_of: '2026-09-22',
        own_movement: comparable.movementFromComparison((oneCase.comparisons || {}).half)
      });

    totalOffers += result.observations_in;
    assert.equal(result.raw_records_retained, result.observations_in,
      oneCase.id + ': an observation was dropped rather than retained');
    assert.equal(result.raw_input_unmodified, true, oneCase.id + ': the raw input was written to');
    assert.equal(result.price_action_certified, false);
    assert.equal(result.all_exclusion_codes_named, true);

    result.ineligible_offers.forEach((row) => {
      totalExcluded += 1;
      if ((row.reason_codes || []).length) exclusionsWithReasons += 1;
      (row.reason_codes || []).forEach((c) => { codesSeen[c] = (codesSeen[c] || 0) + 1; });
    });

    /* No restricted cost field travelled out of the payload record. */
    const keys = allKeys(Object.assign({}, result, { contract: null }));
    comparable.CONTRACT.excluded_field_names.forEach((banned) => {
      assert.ok(!keys.includes(banned), oneCase.id + ': restricted field ' + banned + ' reached the panel');
    });
  }

  assert.equal(totalOffers, 10, 'all ten payload offers should reach a case panel');
  assert.equal(totalExcluded, exclusionsWithReasons,
    'every excluded offer must carry a named reason: ' + JSON.stringify({
      excluded: totalExcluded, with_reasons: exclusionsWithReasons, codes: codesSeen }));

  /* The reasons this panel actually gives, on this payload. Named here so a
     later change that stops reporting one of them fails visibly. */
  assert.ok(codesSeen.PRODUCT_MATCH_UNRESOLVED > 0,
    'the payload matches are cross-references and candidates, which are not approved equivalence');
  assert.ok(codesSeen.PACK_CONTENTS_UNKNOWN > 0,
    'the payload does not declare a unit basis for its quoted amounts');
  assert.ok(Object.keys(codesSeen).every((c) => comparable.EXCLUSION_CODES[c]),
    'an undeclared reason code reached a panel: '
    + JSON.stringify(Object.keys(codesSeen).filter((c) => !comparable.EXCLUSION_CODES[c])));
});

test('M04 on the payload, a tax rate whose unit is undeclared is reported rather than guessed', () => {
  if (!existsSync(PAYLOAD)) {
    assert.ok(true, 'payload not present in this environment');
    return;
  }
  const payload = JSON.parse(readFileSync(PAYLOAD, 'utf8'));

  /* WHAT THIS CHECK MEASURES. The payload stores a VAT figure as a fraction while
     evidence.js takes a percentage, and the payload does not say which unit it
     used. Passing the fraction through unconverted removes a fraction of a
     percent of tax instead of the whole rate, which is why this is an exclusion
     and not a rounding.

     HOW IT IS WRITTEN. The amount, the seller and the identifier all come from
     the restricted payload, and none of them is written into this tracked file.
     The rate is supplied by the check as a declared percentage, because the unit
     is what is under test. The expected figure is derived from the row's own
     amount in memory, so the relationship is asserted rather than a literal
     copied out of the payload. */
  const withFractions = payload.cases.map((oneCase) => {
    const adapted = (oneCase.offers || []).map((id) => comparable.observationFromOffer(payload.offers[id], {
      case_id: oneCase.id, unit: oneCase.unit, level: 'public_advertised_retail',
      match_basis: 'cross_reference'
    }));
    return comparable.panel({ case_id: oneCase.id, part_number: oneCase.pn, market: oneCase.market,
      unit: oneCase.unit }, adapted, { basis_level: 'public_advertised_retail',
      basis_unit: oneCase.unit, as_of: '2026-09-22' });
  });
  const undeclaredUnit = withFractions
    .flatMap((r) => r.ineligible_offers)
    .filter((r) => (r.reason_codes || []).includes('VAT_RATE_UNIT_NOT_STATED'));
  assert.ok(undeclaredUnit.length > 0,
    'the payload carries tax-inclusive observations with an undeclared rate unit; the panel must '
    + 'name that rather than convert the fraction as though it were a percentage');

  /* Declaring the unit converts correctly, and the correct figure follows from
     the row's own amount, rate and rate. Where the source row states no rate,
     there is no correction to test, so the first tax-inclusive row is the one
     used and its presence is asserted rather than assumed. */
  const offerIds = Object.keys(payload.offers);
  const inclusiveId = offerIds.find((id) => {
    const o = payload.offers[id];
    return o && o.price !== null && o.price !== undefined
      && String(o.tax || '').toLowerCase().indexOf('includ') >= 0
      && o.vat !== null && o.vat !== undefined && Number(o.vat) > 0;
  });
  assert.ok(inclusiveId, 'the payload carries no tax-inclusive observation with a stated rate');

  const source = payload.offers[inclusiveId];
  const caseFor = payload.cases.find((c) => (c.offers || []).indexOf(inclusiveId) >= 0);
  assert.ok(caseFor, 'the chosen observation belongs to no case in the payload, so no unit basis can '
    + 'be taken from the case');
  const fxRate = 1.17;
  const round2 = (v) => Math.round(v * 100) / 100;
  const expected = round2(source.price / 1.20 * fxRate);
  const asFractionRead = round2(source.price / (1 + Number(source.vat) / 100) * fxRate);
  assert.notEqual(expected, asFractionRead,
    'the chosen row does not distinguish the two readings, so the check would prove nothing');

  const declared = comparable.panel(
    { case_id: caseFor.id, part_number: caseFor.pn, market: caseFor.market, unit: caseFor.unit },
    [comparable.observationFromOffer(source, {
      case_id: caseFor.id, unit: caseFor.unit, level: 'public_advertised_retail',
      amount_scope: 'per_piece', match_basis: 'declared_equivalence', vat_rate_unit: 'fraction',
      equivalence: { declared: true, declared_by: 'role: product owner' }, delivery_included: true,
      fx_rates: { GBP: { rate: fxRate, date: '2026-09-01' } }
    })],
    { basis_level: 'public_advertised_retail', basis_unit: caseFor.unit, as_of: '2026-09-22' });

  assert.equal(declared.ineligible_offers.length, 0,
    'with the VAT unit, the amount basis and the equivalence all declared, nothing should be left '
    + 'out: ' + JSON.stringify(declared.ineligible_offers.map((r) => r.reason_codes)));
  const row = declared.eligible_offers[0];
  assert.ok(row, 'the adapted observation should reach the comparable set');
  assert.equal(row.adjustment.value, expected,
    'a declared rate must be removed at the rate stated, not at a fraction of a percent of it');
  assert.notEqual(row.adjustment.value, asFractionRead,
    'treating the fraction as a percentage rate is the defect this check exists for');
  assert.equal(row.per_piece.value, expected, 'the comparable figure is the corrected one');
  assert.equal(row.adjustment.vat_rate_used.passed_to_the_rule, 20);
});

test('M08 the request composed for a real payload case names the case and one thing', () => {
  if (!existsSync(PAYLOAD)) {
    assert.ok(true, 'payload not present in this environment');
    return;
  }
  const payload = JSON.parse(readFileSync(PAYLOAD, 'utf8'));
  const oneCase = payload.cases.find((c) => c.id === 'ITUK-PADS') || payload.cases[0];
  const adapted = (oneCase.offers || []).map((id) => comparable.observationFromOffer(payload.offers[id], {
    case_id: oneCase.id, unit: oneCase.unit, level: 'public_advertised_retail',
    match_basis: 'cross_reference'
  }));
  const result = comparable.panel(
    { case_id: oneCase.id, part_number: oneCase.pn, market: oneCase.market, unit: oneCase.unit },
    adapted, { basis_level: 'public_advertised_retail', basis_unit: oneCase.unit, as_of: '2026-09-22' });

  const request = comparable.missingEvidenceRequest(result,
    { case_id: oneCase.id, part_number: oneCase.pn, market: oneCase.market });

  assert.equal(request.ok, true, JSON.stringify(request));
  assert.equal(request.case_id, 'ITUK-PADS');
  assert.equal(request.part_number, payload.cases.find((c) => c.id === 'ITUK-PADS').pn);
  assert.equal(request.draft_only, true);
  assert.equal(request.sent, false);
  const held = request.already_held.length;
  assert.ok(request.context_held_optional !== true);
  assert.equal(typeof held, 'number');
  assert.equal(comparable.requestIsClean(request).clean, true);
});

/* =========================================================================
   the shared rules this panel depends on
   ========================================================================= */

test('the panel reuses evidence.js rather than reimplementing the shared rules', () => {
  /* The functions it calls must exist on the shared module. If one is renamed
     the panel must fail loudly here rather than quietly comparing nothing. */
  ['priceLevel', 'assertSamePriceLevel', 'normalisePack', 'perPiecePrice',
    'adjustToComparable', 'productEquivalence', 'observationConflicts']
    .forEach((n) => assert.equal(typeof evidence[n], 'function',
      'evidence.js no longer exposes ' + n + ', which the panel calls'));

  /* And the levels evidence.js already names are answered from there. */
  assert.equal(comparable.levelInfo('list').label, evidence.priceLevel('list').label);
  assert.equal(comparable.levelInfo('competitor_advertised').label,
    evidence.priceLevel('competitor_advertised').label);
  /* The levels evidence.js does not name yet are declared here and reported. */
  assert.equal(comparable.REQUESTED_SHARED_LEVELS.length, 5);
  assert.equal(comparable.levelInfo('isze_net_distributor').named, true);
});
