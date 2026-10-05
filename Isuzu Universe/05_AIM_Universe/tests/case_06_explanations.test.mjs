#!/usr/bin/env node
/* ===========================================================================
   CASE-06 acceptance tests: explanations and corrections kept as separate
   evidence.

   How to run
     node --test tests/case_06_explanations.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (CASE-06):
     E1  Adding a reported availability reason does not allocate the entire
         family decline to supply.
     E2  A corrected source can be compared with the original saved evidence
         and identifies affected decisions.

   The case service is loaded the way tests/case_store.test.mjs loads it, on the
   memory adapter. Every value is invented; no real part, customer or price.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';

const schema = (await import(new URL('../src/case/schema.js', import.meta.url))).default;
const store = (await import(new URL('../src/case/store.js', import.meta.url))).default;

const FIXED_NOW = '2026-09-22T10:00:00.000Z';

function newService() {
  return store.makeCaseService({
    adapter: store.makeMemoryAdapter(),
    now: () => FIXED_NOW,
    caller: 'test-runner',
    identityMode: 'development-only'
  });
}

const seed = (id) => ({
  case_id: id,
  customer: 'Synthetic customer',
  market: 'SYNTH',
  part_number: 'SYNTH-PART-A',
  description: 'Synthetic part A',
  owner_role: 'case_owner',
  scope_note: 'Synthetic. No real part, customer or price appears in this test.',
  by: 'test-runner'
});

const explanation = (extra = {}) => Object.assign({
  kind: 'explanation',
  words: 'We could not get the part for about six weeks in spring.',
  scope: 'family: synthetic brake family',
  reported_period: 'H1 2026',
  source: 'dealer call note, synthetic',
  audience: 'internal',
  factors: ['availability'],
  no_action: false
}, extra);

test('CASE-06 E1: a reported availability reason does not allocate the entire family decline to supply', () => {
  const service = newService();
  const id = 'CASE-06-E1';
  assert.equal(service.create(seed(id)).ok, true);
  const before = service.get(id);

  const added = service.recordExplanation(id, explanation(), { role: 'dealer', by: 'dealer-1' });
  assert.equal(added.ok, true, added.error);
  const rec = service.get(id);
  assert.equal(rec.state, before.state, 'recording an explanation moved the case');
  assert.equal(rec.explanations.length, 1);
  const stored = rec.explanations[0];
  assert.equal(stored.words, explanation().words, 'the contributor\'s words were not kept as given');
  assert.equal(stored.scope, explanation().scope);
  assert.equal(stored.reported_period, 'H1 2026');
  assert.equal(stored.recorded_date, FIXED_NOW.slice(0, 10));
  assert.equal(stored.source, explanation().source);
  assert.equal(stored.audience, 'internal');
  assert.deepEqual(stored.factors, ['availability']);

  const decline = { family: 'synthetic brake family', amount_eur: -1000 };
  const one = schema.declineAttribution(rec, decline);
  assert.deepEqual(one.factors_reported, ['availability']);
  assert.equal(one.allocated_eur.availability, null,
    'a reported availability reason was given a euro share of the decline');
  assert.equal(one.unallocated_eur, -1000, 'part of the decline was allocated without a measurement');
  assert.equal(one.allocation_state, 'not allocated');

  /* Several factors, an unknown, and "no action" are all allowed, and still
     nothing is allocated. */
  const more = service.recordExplanation(id, explanation({
    words: 'Price went up too, and some of it we just do not know.',
    factors: ['availability', 'price', 'unknown'], no_action: true
  }), { role: 'dealer', by: 'dealer-1' });
  assert.equal(more.ok, true, more.error);
  const two = schema.declineAttribution(service.get(id), decline);
  assert.deepEqual(two.factors_reported.slice().sort(), ['availability', 'price', 'unknown']);
  Object.keys(two.allocated_eur).forEach((f) => {
    assert.equal(two.allocated_eur[f], null, f + ' received an allocation');
  });
  assert.equal(two.unallocated_eur, -1000);
  assert.equal(service.get(id).explanations[1].no_action, true);

  /* An explanation that names no factor is refused rather than defaulted. */
  const none = service.recordExplanation(id, explanation({ factors: [] }), { role: 'dealer' });
  assert.equal(none.ok, false);
});

test('CASE-06 E2: a corrected source is compared with the original saved evidence and names the affected decisions', () => {
  const service = newService();
  const id = 'CASE-06-E2';
  assert.equal(service.create(seed(id)).ok, true);

  const first = service.recordExplanation(id, explanation({ source: 'dealer stock report, version 1' }),
    { role: 'dealer', by: 'dealer-1' });
  assert.equal(first.ok, true, first.error);
  const originalId = service.get(id).explanations[0].explanation_id;

  /* Two decisions taken while the original evidence stood. */
  const submitted = service.transition(id, {
    action: 'submit', role: 'case_owner', next_action: 'Reviewer to take the case',
    next_update_due: '2026-10-01', note: 'Submitted on the dealer explanation'
  });
  assert.equal(submitted.ok, true, submitted.error);
  const assessing = service.transition(id, {
    action: 'begin_assessment', role: 'reviewer', next_action: 'Assess the explanation',
    next_update_due: '2026-10-05'
  });
  assert.equal(assessing.ok, true, assessing.error);
  const decisionSeqs = service.get(id).history
    .filter((h) => h.kind === 'transition').map((h) => h.seq);
  assert.equal(decisionSeqs.length, 2);

  /* A correction that names no original is refused. */
  const orphan = service.recordExplanation(id, explanation({ kind: 'source_correction', corrects: 'EXP-NOPE' }),
    { role: 'dealer' });
  assert.equal(orphan.ok, false);

  const corrected = service.recordExplanation(id, explanation({
    kind: 'source_correction', corrects: originalId,
    source: 'dealer stock report, version 2',
    words: 'The stock report was wrong: the part was out for two weeks, not six.',
    reported_period: 'April 2026'
  }), { role: 'dealer', by: 'dealer-1' });
  assert.equal(corrected.ok, true, corrected.error);
  const rec = service.get(id);
  assert.equal(rec.explanations.length, 2, 'the correction replaced the original instead of sitting beside it');
  assert.equal(rec.explanations[0].source, 'dealer stock report, version 1', 'the original evidence was rewritten');
  const correctionId = rec.explanations[1].explanation_id;

  const cmp = schema.compareCorrection(rec, correctionId);
  assert.equal(cmp.ok, true, cmp.error);
  assert.equal(cmp.kind, 'source_correction');
  assert.equal(cmp.original.source, 'dealer stock report, version 1');
  assert.equal(cmp.corrected.source, 'dealer stock report, version 2');
  ['source', 'words', 'reported_period'].forEach((f) => {
    assert.ok(cmp.changed_fields.includes(f), f + ' is not reported as changed');
  });
  assert.ok(!cmp.changed_fields.includes('scope'), 'an unchanged field was reported as changed');
  assert.deepEqual(cmp.affected_decisions.map((d) => d.seq), decisionSeqs,
    'the decisions taken on the original evidence were not identified');

  /* The three kinds of later evidence stay distinct. */
  const recollection = service.recordExplanation(id, explanation({ kind: 'later_recollection',
    corrects: originalId, words: 'Thinking back, it was closer to a month.' }), { role: 'dealer' });
  assert.equal(recollection.ok, true, recollection.error);
  const disagreement = service.recordExplanation(id, explanation({ kind: 'interpretation_disagreement',
    corrects: originalId, words: 'We do not agree the shortage explains the fall.' }), { role: 'reviewer' });
  assert.equal(disagreement.ok, true, disagreement.error);
  const kinds = service.get(id).explanations.map((e) => e.kind);
  assert.deepEqual(kinds, ['explanation', 'source_correction', 'later_recollection', 'interpretation_disagreement']);
});