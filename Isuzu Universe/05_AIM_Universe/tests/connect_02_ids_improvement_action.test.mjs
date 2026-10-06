#!/usr/bin/env node
/* ===========================================================================
   CONNECT-02 acceptance tests: Connect an IDS answer to a separate improvement
   action.

   How to run
     node --test tests/connect_02_ids_improvement_action.test.mjs

   One test per REQUIRED EVIDENCE item in TASKS_96.txt (CONNECT-02):
     E1  Closing an improvement leaves the original answer and score unchanged.
     E2  An unresolved IDS link does not disable the purchasing review; new
         action work can remain independent.

   Synthetic dealers and synthetic IDS answers only. No real IDS workbook.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';

const mod = (await import(new URL('../src/data/ids_improvement_action.js', import.meta.url))).default;

const ANSWER = {
  scoped_question_id: 'IDS2026-Q::Q12',
  local_question_code: 'Q12',
  questionnaire_version: 'IDS2026-Q',
  question_text: 'Parts availability at the counter',
  answer_state: 'answered',
  answer: 'Partly met',
  date_or_round: '2026-R1',
  score: 2
};

function seedCase() {
  return {
    case_id: 'SYNTH-CASE-C02',
    customer: 'Synthetic dealer',
    market: 'SYNTH',
    ids_score: 14,
    ids_answers: [Object.assign({}, ANSWER)],
    purchasing_review: { enabled: true, independent: true, basket_eur: 1200 },
    improvement_actions: []
  };
}

test('CONNECT-02 E1: Closing an improvement leaves the original answer and score unchanged.', () => {
  const opened = mod.openFromIdsAnswer(seedCase(), ANSWER, {
    action_id: 'IMP-C02-E1',
    owner: 'dealer',
    support_owed_by: 'isze_support',
    note: 'Agree a counter stock check for the missing references.'
  });
  assert.equal(opened.ok, true, opened.error);
  assert.equal(opened.case_record.ids_score, 14);
  assert.equal(opened.case_record.ids_answers[0].answer, 'Partly met');
  assert.equal(opened.case_record.ids_answers[0].score, 2);

  const closed = mod.closeImprovement(opened.case_record, 'IMP-C02-E1', {
    note: 'Stock check completed on synthetic shelf walk.',
    closed_at: '2026-10-06'
  });
  assert.equal(closed.ok, true, closed.error);
  assert.equal(closed.action.state, 'closed');
  assert.equal(closed.case_record.ids_score, 14, 'closing must not change the IDS score');
  assert.equal(closed.case_record.ids_answers[0].answer, 'Partly met', 'closing must not rewrite the answer');
  assert.equal(closed.case_record.ids_answers[0].score, 2);
  assert.equal(closed.answer_unchanged, true);
  assert.equal(closed.score_unchanged, true);

  // Mutating the closed action evidence must not rewrite the snapshotted answer.
  closed.action.completion_evidence.note = 'tamper';
  assert.equal(closed.case_record.ids_answers[0].answer, 'Partly met');

  const causal = mod.assertNoCausalClaim('The IDS answer caused a historical purchasing movement.');
  assert.equal(causal.ok, false);
  const refused = mod.openFromIdsAnswer(seedCase(), ANSWER, {
    note: 'The IDS answer caused a historical purchasing drop.'
  });
  assert.equal(refused.ok, false);
});

test('CONNECT-02 E2: An unresolved IDS link does not disable the purchasing review; new action work can remain independent.', () => {
  const base = seedCase();
  const unresolved = mod.purchasingReviewWithIdsLink(base, {
    resolved: false,
    open_independent_action: true,
    action_id: 'IMP-IND-1',
    note: 'Independent follow-up while the IDS link stays unresolved.'
  });
  assert.equal(unresolved.ok, true);
  assert.equal(unresolved.ids_link_resolved, false);
  assert.equal(unresolved.purchasing_review.enabled, true,
    'an unresolved IDS link must not switch off the purchasing review');
  assert.equal(unresolved.purchasing_review.disabled_by_ids_link, false);
  assert.equal(unresolved.improvement_actions.length, 1);
  assert.equal(unresolved.improvement_actions[0].independent_of_ids_link, true);
  assert.equal(unresolved.improvement_actions[0].ids_answer_snapshot, null);
  assert.equal(base.purchasing_review.basket_eur, 1200,
    'purchasing figures on the case remain available beside an unresolved link');

  const resolved = mod.purchasingReviewWithIdsLink(base, {
    resolved: true,
    scoped_question_id: ANSWER.scoped_question_id
  });
  assert.equal(resolved.ids_link_resolved, true);
  assert.equal(resolved.purchasing_review.enabled, true);
});
