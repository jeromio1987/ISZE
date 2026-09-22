'use strict';

/* Positive control for the continuation patch (AIM-CONTINUATION-20260922-01).
 *
 * WHY THIS FILE EXISTS
 *
 * The patch hardened input handling by making invalid inputs travel to the
 * calculation boundary as invalid instead of being quietly replaced with a
 * default. That is tested through rankAlternatives() and bothObjectives() - the
 * two helpers the assembled page actually calls. Every one of those new checks
 * asserts a REFUSAL.
 *
 * A suite made only of refusals cannot tell "refuse the bad input" apart from
 * "refuse everything". If the hardening had swallowed a legitimate value - a
 * real volume assumption, a real proposed quantity, a real pack size - every
 * refusal assertion would still pass and the defect would ship unseen.
 *
 * This file is the other half: it proves that clean input through the same two
 * helpers still produces the expected quantity. It asserts values, not refusals.
 * It adds no new engine behaviour and changes no source file.
 *
 * Run:  node --test tests/continuation_positive_control.test.cjs
 *
 * Synthetic fixture only. No restricted payload, part number, price or
 * supplier cost is opened or quoted here.
 */

const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');

const E = require(process.env.AIM_ENGINE_UNDER_TEST || '../src/engine/engine.js');
const fixture = require('./fixtures/synthetic_payload.json');

/* The fixture's baseline: 100 units observed, at 6.00 EUR, billing 600.00.
   Read from the fixture rather than hard-coded, so a fixture change is a loud
   failure here instead of a silently different expectation. */
const CASE = fixture.cases[0];
const BASE_QTY = CASE.baselineDefined.quantity;

/* The one alternative that carries a stated volume assumption (+25%), and the
   one whose assumption is a plain zero. Both are legitimate clean inputs. */
const ALT_VOLUME = CASE.alternatives.find((a) => a.alternative_id === 'SYNTH-INC');
const ALT_ZERO = CASE.alternatives.find((a) => a.alternative_id === 'SYNTH-NONE');

/* The options shape src/ui/app.js builds for its ranking views. */
const pageOpts = (extra) => Object.assign(
  { payload: fixture, pack_size: 1, offer_effective_date: null },
  extra || {});

function rowFor(ranked, id) {
  const row = ranked.find((r) => r.alternative.alternative_id === id);
  assert.ok(row, 'the clean alternative ' + id + ' must still be ranked');
  return row;
}

/* A refusal looks a specific way. Asserting the absence of that shape is what
   separates "kept its volume" from "was refused and reported null". */
function isUsable(result) {
  assert.equal(result.ok, true, 'a clean input must not be refused: ' + (result.error || ''));
  assert.equal(result.resolved, true);
  return result;
}

test('P01 a clean alternative keeps its stated volume assumption through the page ranking helper', () => {
  assert.equal(BASE_QTY, 100, 'fixture baseline quantity moved');
  assert.equal(ALT_VOLUME.volume_assumption, 25, 'fixture volume assumption moved');

  const ranked = E.rankAlternatives(CASE, 'grossProfit', pageOpts()).ranked;
  const result = isUsable(rowFor(ranked, 'SYNTH-INC').result);

  /* 100 units plus a stated 25% is 125. Legacy quantities stay fractional. */
  assert.equal(result.quantity_after, 125);
  assert.equal(result.extra_quantity, 25);
});

test('P02 the same clean input through bothObjectives returns the same quantity', () => {
  const result = isUsable(E.bothObjectives(CASE, ALT_VOLUME, pageOpts()).result);
  assert.equal(result.quantity_after, 125);
  assert.equal(result.extra_quantity, 25);
});

test('P03 a clean zero volume assumption means unchanged volume, not a refusal', () => {
  /* Zero here is a stated assumption of no change. The patch must not confuse it
     with an explicit proposed quantity of zero, which is a withdrawal. */
  const ranked = E.rankAlternatives(CASE, 'grossProfit', pageOpts()).ranked;
  const result = isUsable(rowFor(ranked, 'SYNTH-NONE').result);
  assert.equal(result.quantity_after, BASE_QTY);
  assert.equal(result.extra_quantity, 0);
});

test('P04 a stated pack size of five is applied and does not trip the zero-pack refusal', () => {
  /* pack_size 0 is now refused. A real pack size must still pass through and
     still reach the rounding, or the refusal took the working path with it. */
  const ranked = E.rankAlternatives(CASE, 'grossProfit', pageOpts({ pack_size: 5 })).ranked;
  const result = isUsable(rowFor(ranked, 'SYNTH-INC').result);
  assert.equal(result.pack_size, 5);

  /* 125 units in whole packs of 5 is 25 orderable packs above the 100 base,
     which is still 125 - so the quantity itself is unchanged and the pack is
     carried as its own stated assumption. */
  assert.equal(result.quantity_after, 125);
  assert.equal(result.extra_qty_to_preserve_gp % 5, 0,
    'a required quantity must land on a whole pack of the stated size');
});

test('P05 a valid numeric quantity string still becomes a number', () => {
  /* Numeric text is a legitimate operator entry and must survive the hardening.
     The patch refuses symbols, objects and BigInts at the same boundary. */
  const result = isUsable(E.bothObjectives(CASE, ALT_VOLUME, pageOpts({ quantity_after: '120' })).result);
  assert.equal(result.quantity_after, 120);
});

test('P06 a blank proposed quantity still means unchanged rather than refused', () => {
  /* Blank is the documented meaning of "the quantity does not change". The
     patch states that invalid input must not become blank; it must not have
     turned blank into invalid in the other direction. */
  const result = isUsable(E.bothObjectives(CASE, ALT_VOLUME, pageOpts({ quantity_after: null })).result);
  assert.equal(result.quantity_after, 125, 'a blank override must fall back to the stated volume');

  const blankish = isUsable(E.bothObjectives(CASE, ALT_VOLUME, pageOpts({ quantity_after: '   ' })).result);
  assert.equal(blankish.quantity_after, 125);
});

test('P07 a clean price move still reaches the arithmetic rather than a refusal', () => {
  /* The price path shares the same hardening. A real reduction must still price
     at two decimals and still produce a usable result. */
  const result = isUsable(E.bothObjectives(CASE, ALT_VOLUME, pageOpts()).result);
  assert.equal(result.price_before, 6);
  assert.ok(result.price_after < result.price_before, 'the fixture reduces the price');
  assert.equal(result.price_after, 5.7, 'a -5% move on 6.00 is 5.70');
  assert.notEqual(result.gp_after, null, 'a held cost must still produce gross profit');
});

test('P08 every clean alternative in the fixture still ranks, and only the unmodelled one is refused', () => {
  /* Guards against the hardening refusing a whole population. Four alternatives
     exist; three are single-part price offers and one is a migration with no
     supplied product lines, which is genuinely not calculable. */
  const ranked = E.rankAlternatives(CASE, 'grossProfit', pageOpts()).ranked;
  assert.equal(ranked.length, CASE.alternatives.length, 'every alternative must still be ranked');

  const refused = ranked.filter((r) => r.result.ok === false)
    .map((r) => r.alternative.alternative_id);
  assert.deepEqual(refused, ['SYNTH-MIG'],
    'only the migration without supplied product lines may be refused');
});
