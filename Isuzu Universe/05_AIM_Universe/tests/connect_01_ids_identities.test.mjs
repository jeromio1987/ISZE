#!/usr/bin/env node
/* ===========================================================================
   CONNECT-01 acceptance tests: Read IDS evidence through validated identities.

   How to run
     node --test tests/connect_01_ids_identities.test.mjs

   REQUIRED EVIDENCE titles from TASKS_96.txt (verbatim):
     E1  A repeated local question code in different questionnaires does not collide.
     E2  UTI is not included in the 2026 IDS population; no distributor audit score is created.

   Additional brief coverage (synthetic only): validated shows evidence;
   unvalidated shows "identity not validated" with no answers; UMI and UTI
   never merge; an unknown identity stays unknown and does not borrow the
   previous row. Real IDS workbooks are never read.
   =========================================================================== */
import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const require = createRequire(import.meta.url);
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const ids = require(join(ROOT, 'src', 'data', 'ids_evidence.js'));

const SHEET = {
  rows: [
    {
      dealer_id: 'SYN-UMI-01',
      distributor: 'UMI',
      questionnaire_version: 'IDS-2026-UMI',
      local_question_code: 'Q12',
      question_text: 'Synthetic parts handling readiness',
      answer_state: 'answered',
      answer: 'good',
      date_or_round: '2026-R1'
    },
    {
      dealer_id: 'SYN-UMI-01',
      distributor: 'UMI',
      questionnaire_version: 'IDS-2026-PT',
      local_question_code: 'Q12',
      question_text: 'Synthetic workshop capacity (Portugal form)',
      answer_state: 'answered',
      answer: 'fair',
      date_or_round: '2026-R1'
    },
    {
      dealer_id: 'SYN-UMI-01',
      distributor: 'UMI',
      questionnaire_version: 'IDS-2026-UMI',
      local_question_code: 'Q13',
      question_text: 'Synthetic missing answer row',
      answer_state: 'missing',
      answer: null,
      date_or_round: '2026-R1'
    },
    {
      dealer_id: 'SYN-UTI-LOOKALIKE',
      distributor: 'UTI',
      questionnaire_version: 'IDS-2026-FAKE',
      local_question_code: 'Q12',
      question_text: 'Should never surface for UTI in 2026',
      answer_state: 'answered',
      answer: 'should-not-appear',
      date_or_round: '2026-R1'
    },
    {
      dealer_id: 'SYN-UNVAL-01',
      distributor: 'UMI',
      questionnaire_version: 'IDS-2026-UMI',
      local_question_code: 'Q12',
      question_text: 'Hidden until identity is validated',
      answer_state: 'answered',
      answer: 'hidden',
      date_or_round: '2026-R1'
    }
  ]
};

const VALIDATED_UMI = {
  dealer_id: 'SYN-UMI-01',
  distributor: 'UMI',
  display_name: 'Synthetic UMI Dealer',
  validated: true
};

const UNVALIDATED = {
  dealer_id: 'SYN-UNVAL-01',
  distributor: 'UMI',
  display_name: 'Synthetic Unvalidated Dealer',
  validated: false
};

const UTI_DEALER = {
  dealer_id: 'SYN-UTI-LOOKALIKE',
  distributor: 'UTI',
  display_name: 'Synthetic UTI Look-alike',
  validated: true
};

test('CONNECT-01 E1: A repeated local question code in different questionnaires does not collide.', () => {
  const view = ids.readIdsEvidence(VALIDATED_UMI, SHEET);
  assert.equal(view.identity_state, 'validated');
  assert.ok(view.answers.length >= 2, 'validated identity should show its evidence rows');

  const q12 = view.answers.filter((a) => a.local_question_code === 'Q12');
  assert.equal(q12.length, 2, 'both questionnaire rows with local code Q12 should be kept');
  const scoped = q12.map((a) => a.scoped_question_id).sort();
  assert.deepEqual(scoped, ['IDS-2026-PT::Q12', 'IDS-2026-UMI::Q12']);
  assert.notEqual(scoped[0], scoped[1], 'scoped ids must not collide');

  const texts = new Set(q12.map((a) => a.question_text));
  assert.equal(texts.size, 2, 'original question texts must both be retained');

  const missing = view.answers.find((a) => a.local_question_code === 'Q13');
  assert.ok(missing, 'missing answer row should remain');
  assert.equal(missing.answer_state, 'missing');
  assert.equal(missing.answer, null);

  // Brief coverage: validated shows evidence; unvalidated gates; unknown does not borrow.
  const gated = ids.readIdsEvidence(UNVALIDATED, SHEET);
  assert.equal(gated.identity_state, 'not_validated');
  assert.equal(gated.statement, ids.MSG_NOT_VALIDATED);
  assert.deepEqual(gated.answers, []);

  const many = ids.readMany([VALIDATED_UMI, null, UNVALIDATED], SHEET);
  assert.equal(many[0].identity_state, 'validated');
  assert.ok(many[0].answers.length > 0);
  assert.equal(many[1].identity_state, 'unknown');
  assert.equal(many[1].statement, ids.MSG_UNKNOWN);
  assert.deepEqual(many[1].answers, []);
  assert.equal(many[2].identity_state, 'not_validated');
  assert.deepEqual(many[2].answers, []);
  assert.notEqual(many[1].answers, many[0].answers);
});

test('CONNECT-01 E2: UTI is not included in the 2026 IDS population; no distributor audit score is created.', () => {
  const pop = ids.idsPopulation2026([VALIDATED_UMI, UTI_DEALER, UNVALIDATED]);
  assert.equal(pop.year, 2026);
  assert.ok(pop.included.some((d) => d.dealer_id === 'SYN-UMI-01'));
  assert.ok(!pop.included.some((d) => upper(d.distributor) === 'UTI'));
  assert.ok(pop.excluded.some((d) => d.dealer_id === 'SYN-UTI-LOOKALIKE'));
  assert.equal(pop.distributor_audit_scores, null);
  assert.match(pop.statement, /UTI is not included in the 2026 IDS population/);

  const utiView = ids.readIdsEvidence(UTI_DEALER, SHEET);
  assert.equal(utiView.in_ids_population, false);
  assert.equal(utiView.identity_state, 'excluded_from_population');
  assert.deepEqual(utiView.answers, []);
  assert.equal(utiView.distributor_audit_score, null);
  assert.match(utiView.statement, /no distributor audit score is created/);

  const blend = ids.refuseBlend(
    { distributor: 'UMI', dealer_id: 'SYN-UMI-01' },
    { distributor: 'UTI', dealer_id: 'SYN-UTI-LOOKALIKE' }
  );
  assert.equal(blend.ok, false);
  assert.equal(blend.blended, false);
  assert.equal(blend.answers, null);
  assert.equal(blend.distributor_audit_score, null);
  assert.match(blend.statement, /UMI|UTI|separate/);

  const umiOnly = ids.readIdsEvidence(VALIDATED_UMI, SHEET);
  assert.ok(!umiOnly.answers.some((a) => String(a.answer).includes('should-not-appear')));
});

function upper(v) { return String(v || '').toUpperCase(); }
